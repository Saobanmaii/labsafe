"""Ẩn danh ảnh: phát hiện người bằng YOLO (COCO, lớp person) và làm mờ toàn bộ vùng người.

Chạy trên data/images (bản sao); ảnh gốc vẫn ở data/raw_photos. Danh sách ảnh đã làm mờ -> data/blur_log.csv

    python src/blur_people.py
"""
import argparse
import csv

import cv2
from ultralytics import YOLO

from common import DATA, list_images, load_image_bgr, save_image_bgr

ap = argparse.ArgumentParser()
ap.add_argument("--conf", type=float, default=0.25)
ap.add_argument("--pad", type=float, default=0.15, help="nới rộng hộp bao thêm tỷ lệ này mỗi phía")
args = ap.parse_args()

model = YOLO("yolo11s.pt")
log = []
for p in list_images():
    img = load_image_bgr(p)
    h, w = img.shape[:2]
    r = model.predict(img, conf=args.conf, classes=[0], verbose=False)[0]
    boxes = r.boxes.xyxy.tolist()
    for x1, y1, x2, y2 in boxes:
        dx, dy = (x2 - x1) * args.pad, (y2 - y1) * args.pad
        x1, y1 = int(max(0, x1 - dx)), int(max(0, y1 - dy))
        x2, y2 = int(min(w, x2 + dx)), int(min(h, y2 + dy))
        k = max(31, (min(x2 - x1, y2 - y1) // 3) | 1)  # kích thước lõi lẻ, đủ lớn để không nhận ra
        img[y1:y2, x1:x2] = cv2.GaussianBlur(img[y1:y2, x1:x2], (k, k), 0)
    if boxes:
        # ghi lại dưới dạng JPEG cùng tên (ảnh đã được xoay đúng chiều theo EXIF)
        save_image_bgr(p.with_suffix(".jpg"), img, quality=92)
        if p.suffix.lower() != ".jpg":
            p.unlink()
        log.append({"image": p.with_suffix(".jpg").name, "people": len(boxes),
                    "conf": "|".join(f"{c:.2f}" for c in r.boxes.conf.tolist())})
        print(f"{p.name}: làm mờ {len(boxes)} người")

with open(DATA / "blur_log.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["image", "people", "conf"])
    w.writeheader()
    w.writerows(log)
print(f"Xong: {len(log)} ảnh có người đã được làm mờ.")
