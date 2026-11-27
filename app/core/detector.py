"""Bộ phát hiện đối tượng: 3 mô hình YOLO chạy trên cùng một ảnh rồi gộp kết quả.

  1. YOLO11s (COCO)       : ghế, balo, cốc, chai, điện thoại, laptop, sách, người...
  2. YOLO11n tự huấn luyện: bình chữa cháy (COCO không có lớp này)
  3. YOLO-World (từ vựng mở): lớp ngoài COCO khai báo trong bảng kiểm (mặc định: thùng carton)

Một detection là dict {"cls", "conf", "xyxy": (x1, y1, x2, y2), "src"} theo pixel ảnh gốc.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from .config import ROOT

EXTINGUISHER = "fire extinguisher"
PERSON = "person"
# tên lớp của mô hình LabSafe-6 (app/train/classes.py) -> tên lớp bộ luật dùng
CUSTOM_RENAME = {"binh_chua_chay": EXTINGUISHER, "ao_khoac": "jacket", "mu": "hat", "vi": "wallet",
                 "do_uong": "drink", "do_an": "food"}


def _resolve(path: str) -> str:
    p = Path(path)
    if not p.is_absolute() and (ROOT / p).exists():
        return str(ROOT / p)
    return str(p)


class Detector:
    def __init__(self, det_cfg: dict):
        import torch
        from ultralytics import YOLO

        self.cfg = det_cfg
        self.device = 0 if torch.cuda.is_available() else "cpu"
        self.device_name = torch.cuda.get_device_name(0) if self.device == 0 else "CPU"
        self.conf = float(det_cfg.get("conf", 0.30))

        self.coco = YOLO(_resolve(det_cfg["coco_model"]))
        ext_path = _resolve(det_cfg.get("ext_model") or "")
        self.ext = YOLO(ext_path) if ext_path and Path(ext_path).exists() else None

        # Mô hình nâng cấp LabSafe-6 (tuỳ chọn): áo khoác, mũ, ví, đồ uống, đồ ăn, bình chữa cháy
        self.custom = None
        cpath = _resolve(det_cfg.get("custom_model") or "")
        if det_cfg.get("custom_model") and Path(cpath).exists():
            self.custom = YOLO(cpath)
        self.custom_names = sorted(set(CUSTOM_RENAME.values())) if self.custom else []

        world_classes = list(det_cfg.get("world_classes") or [])
        if self.ext is None:  # chưa có mô hình tự huấn luyện -> YOLO-World tìm bình chữa cháy
            world_classes.append(EXTINGUISHER)
        self.world = None
        if world_classes and det_cfg.get("world_model"):
            from ultralytics import YOLOWorld
            self.world = YOLOWorld(_resolve(det_cfg["world_model"]))
            self.world.set_classes(world_classes)
        self.world_classes = world_classes

    @property
    def coco_names(self) -> list[str]:
        return list(self.coco.names.values())

    def _run(self, model, img, rename=None) -> list[dict]:
        r = model.predict(img, conf=self.conf, device=self.device, verbose=False)[0]
        out = []
        for xyxy, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist()):
            name = r.names[int(c)]
            out.append({"cls": rename(name) if rename else name, "conf": round(float(s), 3),
                        "xyxy": tuple(round(v, 1) for v in xyxy)})
        return out

    def detect(self, img_bgr: np.ndarray) -> tuple[list[dict], float]:
        """Trả về (detections thô, thời gian ms). Hậu xử lý làm riêng ở postprocess()."""
        t0 = time.perf_counter()
        dets = [dict(d, src="coco") for d in self._run(self.coco, img_bgr)]
        if self.ext is not None:
            ren = lambda n: EXTINGUISHER if "extinguish" in n.lower() else n  # noqa: E731
            dets += [dict(d, src="ext") for d in self._run(self.ext, img_bgr, ren) if d["cls"] == EXTINGUISHER]
        if self.custom is not None:
            dets += [dict(d, src="custom") for d in self._run(self.custom, img_bgr, lambda n: CUSTOM_RENAME.get(n, n))]
        if self.world is not None:
            dets += [dict(d, src="world") for d in self._run(self.world, img_bgr)]
        return dets, (time.perf_counter() - t0) * 1000


def _area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _inter(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0.0, w) * max(0.0, h)


def postprocess(dets: list[dict], det_cfg: dict) -> tuple[list[dict], list[dict]]:
    """Bỏ khung 'bottle'/'cup' của COCO nằm chồng lên bình chữa cháy.

    Trả về (detections giữ lại, detections bị loại kèm lý do) để giao diện hiển thị minh bạch.
    """
    # Mô hình LabSafe-6: bỏ các lớp không dùng (vd. bình chữa cháy — đã có mô hình bình riêng) và ngưỡng tin cậy riêng
    skip = set(det_cfg.get("custom_skip") or [])
    cconf = float(det_cfg.get("custom_conf") or 0)
    dropped = [dict(d, reason="lớp/ngưỡng của mô hình LabSafe-6") for d in dets
               if d["src"] == "custom" and (d["cls"] in skip or d["conf"] < cconf)]
    dets = [d for d in dets if not (d["src"] == "custom" and (d["cls"] in skip or d["conf"] < cconf))]
    rule = det_cfg.get("suppress_on_extinguisher") or {}
    if not rule.get("enabled"):
        return dets, dropped
    classes = set(rule.get("classes", []))
    thr = float(rule.get("overlap", 0.5))
    exts = [d["xyxy"] for d in dets if d["cls"] == EXTINGUISHER]
    keep = []
    for d in dets:
        if d["cls"] in classes and d["src"] != "ext" and d["cls"] != EXTINGUISHER and exts:
            a = _area(d["xyxy"]) or 1.0
            ov = max(_inter(d["xyxy"], e) / a for e in exts)
            if ov >= thr:
                dropped.append(dict(d, reason=f"nằm trên bình chữa cháy ({ov:.0%})"))
                continue
        keep.append(d)
    return keep, dropped
