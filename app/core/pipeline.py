"""Luồng xử lý một khung hình: phát hiện -> bộ luật theo vùng -> (Gemini) -> kết luận + điểm + bằng chứng."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from . import vlm
from .config import active_criteria
from .detector import Detector, postprocess
from .render import blur_people, downscale, jpeg_bytes
from .rules_engine import CriterionResult, evaluate, scores, zones_to_px

MODES = {
    "rules": "YOLO + bộ luật (offline, nhanh)",
    "vlm": "Gemini (cần mạng, ~10 giây/ảnh)",
    "hybrid": "Kết hợp: luật cho tiêu chí vị trí, Gemini cho tiêu chí loại đồ vật",
}


@dataclass
class Analysis:
    camera: str | None
    cam_zones: dict
    dets: list[dict]
    suppressed: list[dict]
    results: list[CriterionResult]
    score: dict
    mode: str
    det_ms: float = 0.0
    total_ms: float = 0.0
    vlm_info: dict = field(default_factory=dict)
    vlm_error: str | None = None

    @property
    def statuses(self) -> dict:
        return {r.id: r.status for r in self.results}

    @property
    def violations(self) -> list[CriterionResult]:
        return [r for r in self.results if r.status == 1]


def analyze(img: np.ndarray, camera: str | None, zones: dict, cfg: dict, detector: Detector,
            mode: str = "rules", dets: list[dict] | None = None, use_vlm_cache: bool = True) -> Analysis:
    t0 = time.perf_counter()
    crit = active_criteria(cfg)
    cam_zones = zones.get(camera, {}) if camera else {}
    det_ms = 0.0
    if dets is None:
        dets, det_ms = detector.detect(img)
    dets, suppressed = postprocess(dets, cfg["detector"])
    h, w = img.shape[:2]
    zone_names = {k: v["name"] for k, v in cfg["zone_types"].items()}
    results = evaluate(crit, dets, zones_to_px(cam_zones, w, h), zone_names)

    info, err = {}, None
    if mode in ("vlm", "hybrid"):
        try:
            small, s = downscale(img, 1568)
            if cfg.get("vlm", {}).get("blur_people_before_send", True):
                blur_people(small, dets, s)
            info = vlm.analyze(jpeg_bytes(small), crit, cfg["vlm"]["model"], use_cache=use_vlm_cache)
        except Exception as e:  # noqa: BLE001  — mất mạng / hết hạn mức: quay về bộ luật
            err = str(e)
        if info:
            for r, c in zip(results, crit):
                v = info["verdicts"].get(r.id)
                r.vlm_status = v
                r.vlm_reason = info["reasons"].get(r.id, "")
                r.vlm_boxes = [b for b in info["evidence"] if b["criterion"] == r.id]
                use_vlm = mode == "vlm" or c.get("hybrid_engine", "rules") == "vlm"
                if use_vlm and v is not None:
                    r.status = v
                    r.engine = "vlm"
    return Analysis(camera=camera, cam_zones=cam_zones, dets=dets, suppressed=suppressed, results=results,
                    score=scores(results, cfg), mode=mode, det_ms=det_ms,
                    total_ms=(time.perf_counter() - t0) * 1000, vlm_info=info, vlm_error=err)
