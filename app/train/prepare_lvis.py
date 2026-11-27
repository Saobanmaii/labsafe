"""BƯỚC 1b — Lấy thêm dữ liệu từ LVIS v1 (nhãn chi tiết 1.203 lớp trên ảnh COCO, nhiều cảnh trong nhà).

LVIS bù chỗ Open Images thiếu: có VÍ (wallet) và BÌNH CHỮA CHÁY. Đọc JSON kiểu dòng chảy (ijson) nên không
cần nhiều RAM. LVIS gán nhãn "liên hợp": nếu một lớp được đánh dấu "chưa gán đủ" trong ảnh thì ảnh đó bị bỏ,
để mô hình không học nhầm vật thật thành nền.

    python app/train/prepare_lvis.py --per-class 500
Kết quả: D:/Study/datasets/labsafe_lvis/{images,labels}/ + sources.csv
"""
import argparse
import csv
import random
import sys
import urllib.request
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import ijson

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classes import CLASSES  # noqa: E402

RAW = Path("D:/Study/datasets/lvis_raw")
OUT = Path("D:/Study/datasets/labsafe_lvis")
URLS = {"lvis_v1_val.json.zip": "https://dl.fbaipublicfiles.com/LVIS/lvis_v1_val.json.zip",
        "lvis_v1_train.json.zip": "https://dl.fbaipublicfiles.com/LVIS/lvis_v1_train.json.zip"}

LVIS_MAP = {
    "fire_extinguisher": "binh_chua_chay",
    "jacket": "ao_khoac", "coat": "ao_khoac", "ski_parka": "ao_khoac", "parka": "ao_khoac", "raincoat": "ao_khoac",
    "trench_coat": "ao_khoac", "sweatshirt": "ao_khoac",
    "hat": "mu", "baseball_cap": "mu", "cowboy_hat": "mu", "sunhat": "mu", "dress_hat": "mu", "bowler_hat": "mu",
    "helmet": "mu",
    "wallet": "vi",
    "water_bottle": "do_uong", "bottle": "do_uong", "cup": "do_uong", "mug": "do_uong", "can": "do_uong",
    "pop_(soda)": "do_uong", "Dixie_cup": "do_uong", "teacup": "do_uong", "thermos_bottle": "do_uong",
    "beer_can": "do_uong",
    "apple": "do_an", "banana": "do_an", "bread": "do_an", "cookie": "do_an", "doughnut": "do_an",
    "pastry": "do_an", "sandwich": "do_an", "cupcake": "do_an", "cake": "do_an",
}
PRIORITY = ["vi", "binh_chua_chay", "ao_khoac", "mu", "do_uong", "do_an"]  # lớp hiếm chọn trước

ap = argparse.ArgumentParser()
ap.add_argument("--per-class", type=int, default=500)
ap.add_argument("--workers", type=int, default=16)
args = ap.parse_args()

RAW.mkdir(parents=True, exist_ok=True)
for name, url in URLS.items():
    if not (RAW / name).exists():
        print("tải", url)
        urllib.request.urlretrieve(url, RAW / name)

images, anns, cat2lab = {}, defaultdict(list), {}
for name in URLS:
    with zipfile.ZipFile(RAW / name) as z, z.open(z.namelist()[0]) as f:
        for c in ijson.items(f, "categories.item"):
            if c["name"] in LVIS_MAP:
                cat2lab[c["id"]] = LVIS_MAP[c["name"]]
    with zipfile.ZipFile(RAW / name) as z, z.open(z.namelist()[0]) as f:
        for im in ijson.items(f, "images.item"):
            images[im["id"]] = (im["coco_url"], int(im["width"]), int(im["height"]),
                                set(im.get("not_exhaustive_category_ids", [])))
    with zipfile.ZipFile(RAW / name) as z, z.open(z.namelist()[0]) as f:
        for a in ijson.items(f, "annotations.item"):
            if a["category_id"] in cat2lab:
                anns[a["image_id"]].append((a["category_id"], [float(v) for v in a["bbox"]]))
    print(f"{name}: {len(images)} ảnh, {sum(len(v) for v in anns.values())} hộp liên quan")

# bỏ ảnh có lớp liên quan bị đánh dấu "chưa gán đủ"
target_cats = set(cat2lab)
usable = {i: v for i, v in anns.items() if not (images[i][3] & target_cats)}
by_lab = defaultdict(set)
for i, v in usable.items():
    for c, _ in v:
        by_lab[cat2lab[c]].add(i)
print("ảnh dùng được / lớp:", {k: len(by_lab[k]) for k in PRIORITY})

rng = random.Random(0)
chosen = set()
for lab in PRIORITY:
    ids = sorted(by_lab[lab])
    rng.shuffle(ids)
    have = sum(1 for i in ids if i in chosen)
    for i in ids:
        if have >= args.per_class:
            break
        if i not in chosen:
            chosen.add(i)
            have += 1
print("chọn", len(chosen), "ảnh")

(OUT / "images").mkdir(parents=True, exist_ok=True)
(OUT / "labels").mkdir(parents=True, exist_ok=True)


def fetch(i):
    dst = OUT / "images" / f"lvis_{i}.jpg"
    if dst.exists():
        return i, True
    try:
        dst.write_bytes(urllib.request.urlopen(images[i][0], timeout=30).read())
        return i, True
    except Exception as e:  # noqa: BLE001
        print("  lỗi", i, e)
        return i, False


ok = set()
with ThreadPoolExecutor(args.workers) as ex:
    futs = [ex.submit(fetch, i) for i in sorted(chosen)]
    for k, fu in enumerate(as_completed(futs), 1):
        i, good = fu.result()
        if good:
            ok.add(i)
        if k % 300 == 0:
            print(f"  {k}/{len(futs)}")

counts = defaultdict(int)
for i in sorted(ok):
    _, W, H, _ = images[i]
    lines = []
    for c, (x, y, w, h) in usable[i]:
        if w < 2 or h < 2:
            continue
        lab = cat2lab[c]
        lines.append(f"{CLASSES.index(lab)} {(x + w / 2) / W:.6f} {(y + h / 2) / H:.6f} {w / W:.6f} {h / H:.6f}")
        counts[lab] += 1
    (OUT / "labels" / f"lvis_{i}.txt").write_text("\n".join(lines) + "\n")
with open(OUT / "sources.csv", "w", newline="", encoding="utf-8") as f:
    wr = csv.writer(f)
    wr.writerow(["file", "source", "url", "license"])
    for i in sorted(ok):
        wr.writerow([f"lvis_{i}.jpg", "LVIS v1 / COCO 2017", images[i][0], "COCO images: Flickr (CC); LVIS labels: CC BY 4.0"])
print(f"\nXong: {len(ok)} ảnh -> {OUT}\nSố hộp theo lớp: {dict(counts)}")
