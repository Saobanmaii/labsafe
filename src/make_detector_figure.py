"""Hình so sánh định tính: cùng một ảnh, 3 bộ phát hiện (COCO, YOLO-World, YOLO tự huấn luyện).

    python src/make_detector_figure.py --image <ảnh> --out outputs/fig_detector_compare.png
Ảnh mẫu lấy từ tập kiểm định Fire-ART (CC BY 4.0) — ghi nguồn khi dùng.
"""
import argparse

import cv2
import numpy as np
from ultralytics import YOLO, YOLOWorld

from common import MODELS, OUT, load_image_bgr

ap = argparse.ArgumentParser()
ap.add_argument("--image", required=True)
ap.add_argument("--out", default=str(OUT / "fig_detector_compare.png"))
ap.add_argument("--conf", type=float, default=0.30)
args = ap.parse_args()

img = load_image_bgr(args.image)
scale = 900 / img.shape[0]
img = cv2.resize(img, None, fx=scale, fy=scale)

world = YOLOWorld("yolov8s-worldv2.pt")
world.set_classes(["fire extinguisher"])
panels = [
    ("YOLO11s (COCO, có sẵn)", YOLO("yolo11s.pt")),
    ("YOLO-World (từ vựng mở)", world),
    ("YOLO11n tự huấn luyện", YOLO(MODELS / "extinguisher_best.pt")),
]

tiles = []
for title, model in panels:
    r = model.predict(img, conf=args.conf, verbose=False)[0]
    tile = img.copy()
    for xyxy, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist()):
        x1, y1, x2, y2 = map(int, xyxy)
        label = f"{r.names[int(c)]} {s:.2f}"
        cv2.rectangle(tile, (x1, y1), (x2, y2), (0, 200, 255), 4)
        cv2.rectangle(tile, (x1, y1 - 34), (x1 + 16 * len(label), y1), (0, 200, 255), -1)
        cv2.putText(tile, label, (x1 + 4, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
    if len(r.boxes) == 0:
        cv2.putText(tile, "khong phat hien", (20, tile.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 255), 3)
    print(f"{title}: " + (", ".join(f"{r.names[int(c)]} {s:.2f}" for c, s in zip(r.boxes.cls.tolist(), r.boxes.conf.tolist())) or "không phát hiện"))
    tiles.append(tile)

gap = np.full((img.shape[0], 16, 3), 255, np.uint8)
row = np.hstack([tiles[0], gap, tiles[1], gap, tiles[2]])
ok, buf = cv2.imencode(".png", row)
buf.tofile(args.out)
print(f"Đã lưu {args.out}")
