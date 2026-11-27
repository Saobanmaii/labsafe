"""BƯỚC 4 — So sánh TRƯỚC / SAU khi thêm mô hình LabSafe-6, trên 62 ảnh kiểm tra (nhãn 3 người chấm).

Cấu hình "Sau" được chọn TRƯỚC khi xem kết quả (để không "học tủ" bộ kiểm tra):
  + mô hình LabSafe-6, bỏ lớp bình chữa cháy của nó (đã có mô hình bình chuyên dụng)
  + C2 thêm áo khoác, mũ, ví · C3 thêm áo khoác làm vật che · C4 thêm đồ uống, đồ ăn
Các dòng "Phân tích" chỉ để hiểu phần nào giúp / phần nào hại — KHÔNG dùng để chọn cấu hình trên 62 ảnh.

    python app/train/compare.py --model models/labsafe6_v2.pt
Kết quả: outputs/compare_labsafe6.csv + app/checklist.labsafe6.yaml (bảng kiểm "Sau")
"""
import argparse
import copy
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from core.config import ROOT, load_checklist, load_zones  # noqa: E402
from core.detector import Detector  # noqa: E402
from core.evaluation import detect_dataset, majority_labels, metrics, predict_dataset  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="models/labsafe6_v2.pt")
args = ap.parse_args()
if not (ROOT / args.model).exists():
    sys.exit(f"Chưa có {args.model}. Chạy app/train/train.py trước.")


def add(cfg, cid, key, items):
    c = next((x for x in cfg["criteria"] if x["id"] == cid), None)
    if c:
        c[key] = list(dict.fromkeys(list(c.get(key, [])) + items))


def make(base, c2=True, c3=True, c4=True, conf=None, skip_ext=True):
    cfg = copy.deepcopy(base)
    d = cfg["detector"]
    d["custom_model"] = args.model
    d["custom_skip"] = ["fire extinguisher"] if skip_ext else []
    if conf:
        d["custom_conf"] = conf
    sup = d.setdefault("suppress_on_extinguisher", {"enabled": True, "classes": [], "overlap": 0.5})
    sup["classes"] = list(dict.fromkeys(sup.get("classes", []) + ["drink"]))
    if c2:
        add(cfg, "C2", "classes", ["jacket", "hat", "wallet"])
    if c3:
        add(cfg, "C3", "classes", ["jacket"])
    if c4:
        add(cfg, "C4", "classes", ["drink", "food"])
    return cfg


before = load_checklist()
after = make(before)
variants = [
    ("Trước", before),
    ("Sau (LabSafe-6)", after),
    ("Phân tích: chỉ thêm C2", make(before, c3=False, c4=False)),
    ("Phân tích: chỉ thêm C3", make(before, c2=False, c4=False)),
    ("Phân tích: chỉ thêm C4", make(before, c2=False, c3=False)),
    ("Phân tích: ngưỡng 0,5", make(before, conf=0.5)),
    ("Phân tích: giữ bình của LabSafe-6", make(before, skip_ext=False)),
]

zones, gold = load_zones(), majority_labels()
cache = None
rows = []
for tag, cfg in variants:
    if cache is None or tag in ("Trước", "Sau (LabSafe-6)"):
        print(f"== {tag}: chạy phát hiện (có cache)...")
        cache = detect_dataset(cfg, Detector(cfg["detector"]),
                               progress=lambda f, n: print(f"\r   {f:.0%} {n}     ", end=""))
        print()
    m = metrics(predict_dataset(cfg, cache, zones), gold)
    m.insert(0, "Cấu hình", tag)
    rows.append(m)

res = pd.concat(rows)
wide = res.pivot(index="Cấu hình", columns="Tiêu chí", values="κ").reindex([t for t, _ in variants])
print("\nCohen's κ so với nhãn đa số của 3 người chấm (62 ảnh)\n" + wide.round(3).to_string())
print("\nChi tiết Trước / Sau:\n" + res[res["Cấu hình"].isin(["Trước", "Sau (LabSafe-6)"])].to_string(index=False))

(ROOT / "outputs").mkdir(exist_ok=True)
res.to_csv(ROOT / "outputs" / "compare_labsafe6.csv", index=False, encoding="utf-8-sig")
(APP / "checklist.labsafe6.yaml").write_text(yaml.safe_dump(after, allow_unicode=True, sort_keys=False, width=110),
                                             encoding="utf-8")
print("\nĐã lưu outputs/compare_labsafe6.csv và app/checklist.labsafe6.yaml")
