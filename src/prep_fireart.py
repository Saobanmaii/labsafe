"""Chuyển Fire-ART (Wen et al., 2025; CC BY 4.0) thành bộ dữ liệu YOLO một lớp "fire extinguisher".

Fire-ART gán nhãn đa giác dạng YOLO (class x1 y1 ... xn yn, chuẩn hoá). Script:
  - tự tìm id lớp bình chữa cháy từ file tên lớp (classes.txt / *.yaml), hoặc nhận --class-id
  - đổi đa giác -> hộp bao, bỏ các lớp khác
  - giữ toàn bộ ảnh có bình + một phần ảnh không có bình (ảnh âm, giảm báo động giả)
  - chia train/val ngẫu nhiên (seed cố định) và ghi data.yaml

    python src/prep_fireart.py --src D:/Study/datasets/Fire-ART --dst D:/Study/datasets/extinguisher_yolo
"""
import argparse
import os
import random
import re
import shutil
from pathlib import Path

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

ap = argparse.ArgumentParser()
ap.add_argument("--src", required=True)
ap.add_argument("--dst", required=True)
ap.add_argument("--class-id", type=int, default=None, help="id lớp bình chữa cháy nếu không tự dò được")
ap.add_argument("--neg-ratio", type=float, default=0.3, help="số ảnh âm = tỷ lệ này x số ảnh dương")
ap.add_argument("--val", type=float, default=0.2)
args = ap.parse_args()
src, dst = Path(args.src), Path(args.dst)


def find_class_id():
    if args.class_id is not None:
        return args.class_id
    for f in list(src.rglob("classes.txt")) + list(src.rglob("*.yaml")) + list(src.rglob("*.yml")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        if f.suffix == ".txt":
            names = [l.strip() for l in text.splitlines() if l.strip()]
        else:  # names: [a, b] | names:\n  0: a | names:\n  - a
            m = re.search(r"names\s*:\s*\[(.*?)\]", text, re.S)
            if m:
                names = [n.strip().strip("'\"") for n in m.group(1).split(",")]
            else:
                block = text.split("names:", 1)[-1]
                names = [re.sub(r"^\s*(-|\d+\s*:)\s*", "", l).strip().strip("'\"")
                         for l in block.splitlines()[1:] if re.match(r"^\s*(-|\d+\s*:)", l)]
        for i, n in enumerate(names):
            if "extinguish" in n.lower():
                print(f"Lớp bình chữa cháy: id={i} '{n}' (từ {f.relative_to(src)})")
                return i
    raise SystemExit("Không tự dò được id lớp bình chữa cháy -> chạy lại với --class-id N")


cid = find_class_id()
images = {}
for p in src.rglob("*"):
    if p.suffix.lower() in IMG_EXTS:
        images.setdefault(p.stem, p)

pos, neg = [], []
for lab in src.rglob("*.txt"):
    if lab.name == "classes.txt" or lab.stem not in images:
        continue
    boxes = []
    for line in lab.read_text(encoding="utf-8", errors="ignore").splitlines():
        t = line.split()
        if len(t) < 5 or int(float(t[0])) != cid:
            continue
        v = list(map(float, t[1:]))
        if len(v) == 4:  # đã là hộp bao xc yc w h
            boxes.append(v)
        else:            # đa giác -> hộp bao
            xs, ys = v[0::2], v[1::2]
            x1, x2, y1, y2 = max(0, min(xs)), min(1, max(xs)), max(0, min(ys)), min(1, max(ys))
            if x2 > x1 and y2 > y1:
                boxes.append([(x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1])
    (pos if boxes else neg).append((images[lab.stem], boxes))

rng = random.Random(0)
rng.shuffle(neg)
items = pos + neg[: int(len(pos) * args.neg_ratio)]
rng.shuffle(items)
n_val = int(len(items) * args.val)

if dst.exists():
    shutil.rmtree(dst)
for split, chunk in (("val", items[:n_val]), ("train", items[n_val:])):
    (dst / "images" / split).mkdir(parents=True)
    (dst / "labels" / split).mkdir(parents=True)
    for i, (img, boxes) in enumerate(chunk):
        name = f"{split}_{i:05d}{img.suffix.lower()}"
        try:
            os.link(img, dst / "images" / split / name)  # liên kết cứng, không tốn thêm dung lượng
        except OSError:
            shutil.copy(img, dst / "images" / split / name)
        (dst / "labels" / split / f"{Path(name).stem}.txt").write_text(
            "".join(f"0 {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n" for xc, yc, w, h in boxes))

(dst / "data.yaml").write_text(f"path: {dst.as_posix()}\ntrain: images/train\nval: images/val\nnames:\n  0: fire extinguisher\n")
n_boxes = sum(len(b) for _, b in pos)
print(f"Ảnh có bình: {len(pos)} ({n_boxes} hộp) · ảnh âm dùng: {len(items) - len(pos)} / {len(neg)}")
print(f"train: {len(items) - n_val} · val: {n_val} -> {dst / 'data.yaml'}")
