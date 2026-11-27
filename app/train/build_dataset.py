"""BƯỚC 2 — Gộp các nguồn thành một bộ dữ liệu YOLO duy nhất cho mô hình LabSafe-6.

Nguồn:
  1. Open Images (bước 1)          D:/Study/datasets/labsafe_public
     LVIS (bước 1b)                 D:/Study/datasets/labsafe_lvis
  2. Fire-ART (bình chữa cháy)     D:/Study/datasets/extinguisher_yolo
  3. Ảnh nhóm tự chụp, xuất từ Roboflow dạng YOLOv8, giải nén vào data/train_labeled/<tên bất kỳ>/
     (có thể nhiều thư mục, mỗi người một thư mục)

An toàn: tự kiểm tra và LOẠI mọi ảnh trùng/gần trùng với 62 ảnh kiểm tra (data/images),
vì ảnh kiểm tra tuyệt đối không được dùng để train.

    python app/train/build_dataset.py
Kết quả: D:/Study/datasets/labsafe_6cls/  (images/{train,val}, labels/{train,val}, data.yaml, summary.csv)
"""
import argparse
import hashlib
import shutil
import sys
from collections import Counter
from pathlib import Path

import yaml
from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classes import CLASSES  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = [(Path("D:/Study/datasets/labsafe_public"), "openimages"), (Path("D:/Study/datasets/labsafe_lvis"), "lvis")]
FIREART = Path("D:/Study/datasets/extinguisher_yolo")
ROBOFLOW = ROOT / "data" / "train_labeled"
TEST_IMAGES = ROOT / "data" / "images"
OUT = Path("D:/Study/datasets/labsafe_6cls")
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

ap = argparse.ArgumentParser()
ap.add_argument("--val", type=float, default=0.15, help="tỷ lệ ảnh kiểm định")
ap.add_argument("--no-public", action="store_true")
ap.add_argument("--no-fireart", action="store_true")
ap.add_argument("--out", default=str(OUT), help="thư mục kết quả (đổi tên khi đang có lần train khác dùng thư mục cũ)")
args = ap.parse_args()
OUT = Path(args.out)


def ahash(path, n=16):
    im = ImageOps.exif_transpose(Image.open(path)).convert("L").resize((n, n))
    px = list(im.get_flattened_data()) if hasattr(im, "get_flattened_data") else list(im.getdata())
    avg = sum(px) / len(px)
    return int("".join("1" if p > avg else "0" for p in px), 2)


def near_dup(h, pool, thr=12):
    return any(bin(h ^ t).count("1") <= thr for t in pool)


def label_for(img: Path) -> Path:
    # .../images/<split>/x.jpg -> .../labels/<split>/x.txt ; .../images/x.jpg -> .../labels/x.txt
    parts = list(img.parts)
    i = len(parts) - 1 - parts[::-1].index("images")
    parts[i] = "labels"
    return Path(*parts).with_suffix(".txt")


items = []  # (ảnh, dòng nhãn đã đổi sang id LabSafe, nguồn)

for pdir, pname in ([] if args.no_public else PUBLIC):
    if not pdir.exists():
        continue
    for img in sorted((pdir / "images").glob("*.jpg")):
        lb = pdir / "labels" / (img.stem + ".txt")
        if lb.exists():
            items.append((img, lb.read_text().split("\n"), pname))

if not args.no_fireart and FIREART.exists():
    for img in sorted((FIREART / "images").rglob("*")):
        if img.suffix.lower() in IMG_EXTS:
            lb = label_for(img)
            lines = lb.read_text().split("\n") if lb.exists() else []   # ảnh âm (không có bình) vẫn giữ
            lines = [f"{CLASSES.index('binh_chua_chay')} " + l.split(maxsplit=1)[1] for l in lines if l.strip()]
            items.append((img, lines, "fireart"))

rf_names = Counter()
if ROBOFLOW.exists():
    for dy in sorted(ROBOFLOW.rglob("data.yaml")):
        names = yaml.safe_load(dy.read_text(encoding="utf-8"))["names"]
        names = list(names.values()) if isinstance(names, dict) else list(names)
        remap = {}
        for k, n in enumerate(names):
            key = str(n).strip().lower().replace(" ", "_")
            if key in CLASSES:
                remap[k] = CLASSES.index(key)
            else:
                print(f"[!] {dy.parent.name}: lớp '{n}' không thuộc {CLASSES} -> bỏ qua hộp của lớp này")
        for img in sorted(dy.parent.rglob("*")):
            if img.suffix.lower() not in IMG_EXTS or "images" not in img.parts:
                continue
            lb = label_for(img)
            out = []
            for l in (lb.read_text().split("\n") if lb.exists() else []):
                p = l.split()
                if len(p) == 5 and int(p[0]) in remap:
                    out.append(" ".join([str(remap[int(p[0])])] + p[1:]))
                    rf_names[CLASSES[remap[int(p[0])]]] += 1
            items.append((img, out, f"roboflow:{dy.parent.name}"))

# ---- chặn rò rỉ ảnh kiểm tra
test_hashes = [ahash(p) for p in TEST_IMAGES.iterdir() if p.suffix.lower() in IMG_EXTS]
kept, leaked = [], []
for it in items:
    if it[2].startswith("roboflow") and near_dup(ahash(it[0]), test_hashes):
        leaked.append(it[0])
    else:
        kept.append(it)
if leaked:
    print(f"[!] LOẠI {len(leaked)} ảnh trùng với bộ 62 ảnh kiểm tra:", *[p.name for p in leaked[:10]])

# ---- chia train/val ổn định theo tên file (chạy lại cho cùng kết quả)
if OUT.exists():
    shutil.rmtree(OUT)
summary = Counter()
for img, lines, src in kept:
    h = int(hashlib.md5(f"{src}/{img.name}".encode()).hexdigest(), 16) % 1000
    split = "val" if h < args.val * 1000 else "train"
    stem = f"{src.split(':')[0]}_{hashlib.md5(str(img).encode()).hexdigest()[:8]}_{img.stem}"[:120]
    (OUT / "images" / split).mkdir(parents=True, exist_ok=True)
    (OUT / "labels" / split).mkdir(parents=True, exist_ok=True)
    shutil.copy(img, OUT / "images" / split / (stem + img.suffix.lower()))
    lines = [l for l in lines if l.strip()]
    (OUT / "labels" / split / (stem + ".txt")).write_text("\n".join(lines) + ("\n" if lines else ""))
    summary[(split, src.split(":")[0], "ảnh")] += 1
    for l in lines:
        summary[(split, CLASSES[int(l.split()[0])], "hộp")] += 1

(OUT / "data.yaml").write_text(yaml.safe_dump({"path": str(OUT).replace("\\", "/"), "train": "images/train",
                                               "val": "images/val", "names": dict(enumerate(CLASSES))},
                                              allow_unicode=True, sort_keys=False), encoding="utf-8")
with open(OUT / "summary.csv", "w", encoding="utf-8") as f:
    f.write("split,muc,loai,so_luong\n")
    for (a, b, c), n in sorted(summary.items()):
        f.write(f"{a},{b},{c},{n}\n")
print(f"\nBộ dữ liệu: {OUT}")
for (a, b, c), n in sorted(summary.items()):
    print(f"  {a:5s} {b:15s} {c:4s} {n}")
if rf_names:
    print("Hộp từ ảnh nhóm tự chụp:", dict(rf_names))
else:
    print("Chưa có ảnh nhóm tự chụp (data/train_labeled trống) -> chỉ dùng dữ liệu công khai.")
