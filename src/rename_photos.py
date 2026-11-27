"""Đổi tên ảnh chụp sang tên trung tính (người chấm không đoán được kịch bản từ tên file).

Ảnh gốc ở data/raw_photos/<Góc>/[<độ cao>/]*.jpg -> data/images/<view>_<NN>.<ext>
Bảng đối chiếu ghi vào data/photo_map.csv (tên gốc chứa ý định dàn dựng — KHÔNG gửi cho người chấm).

    python src/rename_photos.py
"""
import csv
import re
import shutil

from common import DATA, IMAGES, IMG_EXTS

RAW = DATA / "raw_photos"
# thư mục góc/độ cao -> mã góc camera (không có dấu "_" vì view_of tách theo "_")
VIEWS = {
    ("góc 1",): "v1",
    ("góc 2", "cao"): "v2a", ("góc 2", "trung"): "v2b", ("góc 2", "dưới"): "v2c",
    ("góc 3", "cao"): "v3a", ("góc 3", "thấp"): "v3b",
}


def natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s.lower())]


IMAGES.mkdir(parents=True, exist_ok=True)
rows = []
for key, view in VIEWS.items():
    # tên thư mục có thể viết hoa (Cao/Thấp): tìm không phân biệt hoa thường
    folder = RAW
    for part in key:
        match = [d for d in folder.iterdir() if d.is_dir() and d.name.lower() == part]
        if not match:
            folder = None
            break
        folder = match[0]
    if folder is None:
        print(f"[!] Không thấy thư mục {'/'.join(key)}")
        continue
    files = sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS), key=lambda p: natural(p.name))
    for i, p in enumerate(files, 1):
        new = f"{view}_{i:02d}{p.suffix.lower()}"
        shutil.copy2(p, IMAGES / new)
        m = re.match(r"\s*s(\d+)", p.stem, re.I)
        intended = f"s{int(m.group(1)):02d}" if m else ("s01" if "gọn" in p.stem.lower() else "")
        rows.append({"image": new, "view": view, "original": str(p.relative_to(RAW)), "intended_scenario": intended})
    print(f"{view}: {len(files)} ảnh  ({folder.relative_to(RAW)})")

with open(DATA / "photo_map.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["image", "view", "original", "intended_scenario"])
    w.writeheader()
    w.writerows(rows)
print(f"Tổng {len(rows)} ảnh -> {IMAGES}. Bảng đối chiếu: {DATA / 'photo_map.csv'}")
