"""Đánh giá trên bộ 62 ảnh có nhãn 3 người chấm, với bảng kiểm HIỆN TẠI.

Detection được cache theo cấu hình bộ phát hiện, nên đổi ngưỡng/luật rồi đánh giá lại chỉ mất ~1 giây.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, f1_score

from .config import CACHE_DIR, LABELS_DIR, active_criteria, camera_for_image, dataset_images, detector_key
from .detector import postprocess
from .render import load_image
from .rules_engine import evaluate, zones_to_px


def majority_labels() -> pd.DataFrame | None:
    files = sorted(LABELS_DIR.glob("rater*.csv"))
    if not files:
        return None
    frames = [pd.read_csv(f, encoding="utf-8-sig").set_index("image") for f in files]
    crit = [c for c in frames[0].columns if c.startswith("C") and c[1:].isdigit()]
    stack = np.stack([f.loc[frames[0].index, crit].to_numpy() for f in frames])
    maj = (stack.sum(0) * 2 > len(frames)).astype(int)
    return pd.DataFrame(maj, index=frames[0].index, columns=crit)


def det_cache_file(cfg: dict) -> Path:
    return CACHE_DIR / f"dets_{detector_key(cfg)}.json"


def load_det_cache(cfg: dict) -> dict:
    f = det_cache_file(cfg)
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def detect_dataset(cfg: dict, detector, progress=None) -> dict:
    """{image_name: {"dets": [...], "w": W, "h": H}} — chạy YOLO cho ảnh chưa có trong cache."""
    cache = load_det_cache(cfg)
    imgs = dataset_images()
    todo = [p for p in imgs if p.name not in cache]
    for k, p in enumerate(todo):
        img = load_image(p)
        dets, ms = detector.detect(img)
        cache[p.name] = {"dets": [dict(d, xyxy=list(d["xyxy"])) for d in dets],
                         "w": img.shape[1], "h": img.shape[0], "ms": round(ms, 1)}
        if progress:
            progress((k + 1) / len(todo), p.name)
    if todo:
        det_cache_file(cfg).write_text(json.dumps(cache), encoding="utf-8")
    return cache


def predict_dataset(cfg: dict, cache: dict, zones: dict) -> pd.DataFrame:
    crit = active_criteria(cfg)
    zone_names = {k: v["name"] for k, v in cfg["zone_types"].items()}
    rows = []
    for name, item in sorted(cache.items()):
        cam = camera_for_image(name, zones)
        dets, _ = postprocess([dict(d, xyxy=tuple(d["xyxy"])) for d in item["dets"]], cfg["detector"])
        res = evaluate(crit, dets, zones_to_px(zones.get(cam, {}), item["w"], item["h"]) if cam else {}, zone_names)
        rows.append({"image": name, "camera": cam, **{r.id: r.status for r in res}})
    return pd.DataFrame(rows).set_index("image")


def metrics(pred: pd.DataFrame, gold: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c in [c for c in pred.columns if c in gold.columns]:
        both = pred[[c]].join(gold[[c]], lsuffix="_p", rsuffix="_g").dropna()
        p, g = both[f"{c}_p"].astype(int), both[f"{c}_g"].astype(int)
        tp, fp = int(((p == 1) & (g == 1)).sum()), int(((p == 1) & (g == 0)).sum())
        fn, tn = int(((p == 0) & (g == 1)).sum()), int(((p == 0) & (g == 0)).sum())
        rows.append({"Tiêu chí": c, "n": len(both), "Khớp": round((p == g).mean(), 3),
                     "κ": round(cohen_kappa_score(g, p), 3) if len(set(g) | set(p)) > 1 else np.nan,
                     "F1 (vi phạm)": round(f1_score(g, p, zero_division=0), 3),
                     "TP": tp, "FP": fp, "FN": fn, "TN": tn})
    return pd.DataFrame(rows)
