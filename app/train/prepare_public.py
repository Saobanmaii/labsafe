"""BƯỚC 1 — Tải dữ liệu công khai từ Open Images (phần validation + test) cho các lớp LabSafe.

Chỉ tải ảnh có chứa lớp cần (áo khoác, mũ, đồ uống, đồ ăn), bỏ ảnh vẽ/minh hoạ và hộp "nhóm nhiều vật",
thu nhỏ ảnh về cạnh dài 1024 px, ghi nhãn YOLO.

    python app/train/prepare_public.py --per-class 600
Kết quả: D:/Study/datasets/labsafe_public/{images,labels}/  (+ sources.csv ghi nguồn từng ảnh)
"""
import argparse
import csv
import io
import random
import sys
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classes import CLASSES, OPEN_IMAGES_MAP  # noqa: E402

RAW = Path("D:/Study/datasets/openimages_raw")
OUT = Path("D:/Study/datasets/labsafe_public")
BASE = "https://storage.googleapis.com/openimages"
CSVS = {"classes.csv": f"{BASE}/v7/oidv7-class-descriptions-boxable.csv",
        "validation-bbox.csv": f"{BASE}/v5/validation-annotations-bbox.csv",
        "test-bbox.csv": f"{BASE}/v5/test-annotations-bbox.csv"}
IMG_URL = "https://open-images-dataset.s3.amazonaws.com/{split}/{id}.jpg"

ap = argparse.ArgumentParser()
ap.add_argument("--per-class", type=int, default=600, help="số ảnh tối đa cho mỗi lớp LabSafe")
ap.add_argument("--workers", type=int, default=16)
ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()

RAW.mkdir(parents=True, exist_ok=True)
for name, url in CSVS.items():
    if not (RAW / name).exists():
        print("tải", url)
        urllib.request.urlretrieve(url, RAW / name)

cls = pd.read_csv(RAW / "classes.csv", header=None, names=["mid", "name"])
mid2lab = {r.mid: OPEN_IMAGES_MAP[r.name] for r in cls.itertuples() if r.name in OPEN_IMAGES_MAP}
missing = set(OPEN_IMAGES_MAP) - set(cls["name"])
if missing:
    print("[!] không có trong Open Images:", missing)

frames = []
for split in ("validation", "test"):
    df = pd.read_csv(RAW / f"{split}-bbox.csv", usecols=["ImageID", "LabelName", "XMin", "XMax", "YMin", "YMax",
                                                         "IsGroupOf", "IsDepiction"])
    df = df[df["LabelName"].isin(mid2lab)].copy()
    df["split"] = split
    frames.append(df)
boxes = pd.concat(frames)
# bỏ ảnh có hộp "nhóm" hoặc hình vẽ của lớp cần, để nhãn nhất quán
bad = set(boxes.loc[(boxes.IsGroupOf == 1) | (boxes.IsDepiction == 1), "ImageID"])
boxes = boxes[~boxes.ImageID.isin(bad)]
boxes["lab"] = boxes.LabelName.map(mid2lab)

# chọn ảnh: tối đa --per-class ảnh cho mỗi lớp LabSafe (ưu tiên lớp hiếm trước)
rng = random.Random(args.seed)
by_lab = defaultdict(set)
for r in boxes[["ImageID", "lab"]].drop_duplicates().itertuples():
    by_lab[r.lab].add(r.ImageID)
chosen = set()
for lab in sorted(by_lab, key=lambda k: len(by_lab[k])):
    ids = sorted(by_lab[lab])
    rng.shuffle(ids)
    have = sum(1 for i in ids if i in chosen)
    for i in ids:
        if have >= args.per_class:
            break
        if i not in chosen:
            chosen.add(i)
            have += 1
print("ảnh sẵn có / lớp:", {k: len(v) for k, v in by_lab.items()})
sel = boxes[boxes.ImageID.isin(chosen)]
split_of = sel.groupby("ImageID")["split"].first().to_dict()
print(f"chọn {len(chosen)} ảnh, {len(sel)} hộp")

(OUT / "images").mkdir(parents=True, exist_ok=True)
(OUT / "labels").mkdir(parents=True, exist_ok=True)


def fetch(img_id):
    dst = OUT / "images" / f"oi_{img_id}.jpg"
    if dst.exists():
        return img_id, True
    try:
        data = urllib.request.urlopen(IMG_URL.format(split=split_of[img_id], id=img_id), timeout=30).read()
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.thumbnail((1024, 1024))
        im.save(dst, quality=90)
        return img_id, True
    except Exception as e:  # noqa: BLE001
        print("  lỗi", img_id, e)
        return img_id, False


ok = set()
with ThreadPoolExecutor(args.workers) as ex:
    futs = [ex.submit(fetch, i) for i in sorted(chosen)]
    for k, f in enumerate(as_completed(futs), 1):
        i, good = f.result()
        if good:
            ok.add(i)
        if k % 200 == 0:
            print(f"  {k}/{len(futs)}")

counts = defaultdict(int)
for img_id, g in sel[sel.ImageID.isin(ok)].groupby("ImageID"):
    lines = []
    for r in g.itertuples():
        cx, cy = (r.XMin + r.XMax) / 2, (r.YMin + r.YMax) / 2
        w, h = r.XMax - r.XMin, r.YMax - r.YMin
        lines.append(f"{CLASSES.index(r.lab)} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        counts[r.lab] += 1
    (OUT / "labels" / f"oi_{img_id}.txt").write_text("\n".join(lines) + "\n")

with open(OUT / "sources.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["file", "source", "split", "license"])
    for i in sorted(ok):
        w.writerow([f"oi_{i}.jpg", "Open Images V7", split_of[i], "CC BY 2.0 (ảnh) / CC BY 4.0 (nhãn)"])
print(f"\nXong: {len(ok)} ảnh -> {OUT}\nSố hộp theo lớp: {dict(counts)}")
