"""Tạo file chấm nhãn cho từng người chấm, thứ tự ảnh xáo trộn khác nhau.

    python src/make_label_sheets.py --raters 3
"""
import argparse
import csv
import random

from common import CRITERIA, LABELS, list_images

ap = argparse.ArgumentParser()
ap.add_argument("--raters", type=int, default=3)
ap.add_argument("--force", action="store_true", help="ghi đè file đã có")
args = ap.parse_args()

names = [p.name for p in list_images()]
LABELS.mkdir(parents=True, exist_ok=True)
for k in range(1, args.raters + 1):
    path = LABELS / f"rater{k}.csv"
    if path.exists() and not args.force:
        print(f"Bỏ qua {path.name} (đã có, dùng --force để ghi đè)")
        continue
    order = names[:]
    random.Random(k).shuffle(order)
    # utf-8-sig để Excel mở đúng tiếng Việt
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["image", *CRITERIA, "ghi_chu"])
        for n in order:
            w.writerow([n, *[""] * len(CRITERIA), ""])
    print(f"Đã tạo {path} ({len(order)} ảnh)")
