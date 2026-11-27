"""Đánh giá vùng TỰ ĐỘNG (phân đoạn ngữ nghĩa) so với vùng VẼ TAY trên 6 góc camera.

1. Mỗi góc camera: lấy ảnh <góc>_01 (cảnh "phòng gọn gàng" theo kịch bản chụp) làm ảnh phòng sạch,
   đề xuất vùng tự động, so với vùng vẽ tay bằng IoU.
2. Chấm lại 62 ảnh với bộ luật hiện tại khi CHỈ dùng vùng tự động, so κ với vùng vẽ tay.

    python app/eval_auto_zones.py
Kết quả: outputs/auto_zones/<góc>.jpg (vẽ tay | tự động), outputs/auto_zones_eval.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from core.config import DATASET_IMAGES, PAPER_OUT, load_checklist, load_zones  # noqa: E402
from core.detector import Detector  # noqa: E402
from core.evaluation import detect_dataset, majority_labels, metrics, predict_dataset  # noqa: E402
from core.render import draw_zones_only, load_image, save_jpg  # noqa: E402
from core.segment import Segmenter, propose_zones, zones_iou  # noqa: E402


def label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 46), (30, 30, 30), -1)
    cv2.putText(out, text, (14, 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    return out


cfg = load_checklist()
manual = load_zones()
views = sorted(k for k in manual if "_" not in k)
seg = Segmenter()
det = Detector(cfg["detector"])
out_dir = PAPER_OUT / "auto_zones"
out_dir.mkdir(parents=True, exist_ok=True)

auto, auto_nogam, rows = {}, {}, []
for v in views:
    ref = DATASET_IMAGES / f"{v}_01.jpg"
    img = load_image(ref)
    auto[v] = propose_zones(img, seg, det)
    auto_plain = propose_zones(img, seg, det, exclude_under_table=False)
    auto_nogam[v] = auto_plain
    r = {"Góc": v, "Ảnh nền": ref.name}
    for zt in ("aisle", "bench", "extinguisher"):
        iou = zones_iou(manual[v], auto[v], zt)
        r[f"IoU {zt}"] = None if iou is None else round(iou, 2)
    rows.append(r)
    small = cv2.resize(img, (960, int(img.shape[0] * 960 / img.shape[1])))
    both = np.hstack([label(draw_zones_only(small, manual[v], cfg), f"{v}: VE TAY"),
                      label(draw_zones_only(small, auto[v], cfg), f"{v}: TU DONG (SegFormer)")])
    save_jpg(out_dir / f"{v}.jpg", both, quality=85)
    print(r)

iou_df = pd.DataFrame(rows)
print("\nIoU trung bình:", iou_df[[c for c in iou_df if c.startswith("IoU")]].mean().round(2).to_dict())

# ---- κ trên 62 ảnh: vẽ tay (có vùng riêng cho ảnh lệch khung) / vẽ tay chỉ theo góc / tự động
gold = majority_labels()
cache = detect_dataset(cfg, det)
manual_view_only = {k: v for k, v in manual.items() if "_" not in k}
res = []
for tag, zs in (("Vẽ tay (có vùng riêng ảnh lệch khung)", manual),
                ("Vẽ tay, chỉ theo góc camera", manual_view_only),
                ("Tự động, không loại gầm bàn", auto_nogam),
                ("Tự động (SegFormer-B5 + mô hình bình, loại gầm bàn)", auto)):
    m = metrics(predict_dataset(cfg, cache, zs), gold)
    m.insert(0, "Vùng", tag)
    res.append(m)
res = pd.concat(res)
print("\n" + res.pivot(index="Vùng", columns="Tiêu chí", values="κ").round(3).to_string())
with open(PAPER_OUT / "auto_zones_eval.csv", "w", encoding="utf-8-sig", newline="") as f:
    iou_df.to_csv(f, index=False)
    f.write("\n")
    res.to_csv(f, index=False)
print(f"\nĐã lưu {out_dir} và outputs/auto_zones_eval.csv")
