"""Cấu hình và hàm dùng chung cho toàn bộ pipeline."""
import io
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IMAGES = DATA / "images"
LABELS = DATA / "labels"
ZONES_FILE = DATA / "zones.json"
OUT = ROOT / "outputs"
MODELS = ROOT / "models"

CRITERIA = ["C1", "C2", "C3", "C4"]
CRITERIA_NAMES = {
    "C1": "Vật cản lối đi",
    "C2": "Đồ cá nhân trên bàn",
    "C3": "Bình chữa cháy bị che",
    "C4": "Đồ ăn/uống",
}
ZONE_TYPES = ["aisle", "bench", "extinguisher"]
IMG_EXTS = {".jpg", ".jpeg", ".png"}


def list_images(folder: Path = IMAGES) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMG_EXTS)


def view_of(name: str) -> str:
    """'v2_s07.jpg' -> 'v2'."""
    return Path(name).stem.split("_")[0]


def load_image_bgr(path: Path) -> np.ndarray:
    """Đọc ảnh, xoay theo EXIF (ảnh điện thoại), an toàn với đường dẫn tiếng Việt."""
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def save_image_bgr(path: Path, img: np.ndarray, quality: int = 90) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    assert ok
    buf.tofile(str(path))


def jpeg_bytes_resized(path: Path, long_edge: int = 1568, quality: int = 90) -> bytes:
    """Ảnh gửi cho VLM: xoay theo EXIF, thu về cạnh dài 1568 px (cùng đầu vào cho mọi model)."""
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    img.thumbnail((long_edge, long_edge))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def load_zones(path: Path = ZONES_FILE) -> dict:
    """zones.json: {view: {zone_type: [[[x, y], ...], ...]}} với toạ độ chuẩn hoá 0..1."""
    if not path.exists():
        raise FileNotFoundError(f"Chưa có {path}. Dùng tools/zone_tool.html để vẽ vùng.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def zones_to_px(view_zones: dict, w: int, h: int) -> dict:
    return {
        ztype: [[(x * w, y * h) for x, y in poly] for poly in polys]
        for ztype, polys in view_zones.items()
    }
