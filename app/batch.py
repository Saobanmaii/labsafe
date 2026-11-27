"""Chạy hệ thống trên bộ 62 ảnh có nhãn và in κ so với nhãn đa số của 3 người chấm (không cần giao diện).

    python app/batch.py                 # bảng kiểm hiện tại (app/checklist.yaml)
    python app/batch.py --paper         # tắt bước lọc "bottle" trên bình -> phải khớp số liệu bài báo
"""
import argparse
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402

from core.config import PAPER_OUT, load_checklist, load_zones  # noqa: E402
from core.detector import Detector  # noqa: E402
from core.evaluation import detect_dataset, majority_labels, metrics, predict_dataset  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--paper", action="store_true", help="cấu hình giống bài báo (không lọc bottle trên bình)")
args = ap.parse_args()

cfg = load_checklist()
if args.paper:
    cfg = copy.deepcopy(cfg)
    cfg["detector"]["suppress_on_extinguisher"]["enabled"] = False

zones = load_zones()
cache = detect_dataset(cfg, Detector(cfg["detector"]),
                       progress=lambda f, n: print(f"\r  phát hiện {f:.0%} {n}   ", end=""))
print()
pred = predict_dataset(cfg, cache, zones)
print(metrics(pred, majority_labels()).to_string(index=False))

paper = PAPER_OUT / "results_rule.csv"
if args.paper and paper.exists():
    old = pd.read_csv(paper, encoding="utf-8-sig").set_index("image")[["C1", "C2", "C3", "C4"]]
    diff = (pred[["C1", "C2", "C3", "C4"]] != old.loc[pred.index]).sum()
    print("\nSố ảnh khác với outputs/results_rule.csv của bài báo:", dict(diff))
