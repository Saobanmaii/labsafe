"""Đường dẫn, đọc/ghi bảng kiểm (YAML) và cấu hình vùng camera (JSON)."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
from pathlib import Path

import yaml

APP = Path(__file__).resolve().parent.parent          # .../app
ROOT = APP.parent                                      # thư mục đề tài
DATA = ROOT / "data"
DATASET_IMAGES = DATA / "images"
LABELS_DIR = DATA / "labels"
PAPER_OUT = ROOT / "outputs"

STORE = ROOT / "app_data"                              # dữ liệu sinh ra khi chạy sản phẩm
EVENT_DIR = STORE / "events"
CAMERA_DIR = STORE / "cameras"
CACHE_DIR = STORE / "cache"
DB_FILE = STORE / "events.db"

CHECKLIST = APP / "checklist.yaml"
CHECKLIST_DEFAULT = APP / "checklist.default.yaml"
ZONES = STORE / "zones.json"
ZONES_SEED = DATA / "zones.json"                       # vùng đã vẽ cho 62 ảnh của bài báo

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
RULE_TYPES = {
    "zone_occupancy": "Chiếm dụng vùng",
    "count_in_zone": "Đếm vật trong vùng",
    "zone_visibility": "Vật bắt buộc phải nhìn thấy",
}

for d in (STORE, EVENT_DIR, CAMERA_DIR, CACHE_DIR):
    d.mkdir(parents=True, exist_ok=True)


def load_env() -> None:
    """Đọc .env ở thư mục gốc (GEMINI_API_KEY..., TELEGRAM_...)."""
    f = ROOT / ".env"
    if not f.exists():
        return
    for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            if v.strip():
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))


# ---------------------------------------------------------------- bảng kiểm
def load_checklist() -> dict:
    if not CHECKLIST.exists():
        shutil.copy(CHECKLIST_DEFAULT, CHECKLIST)
    with open(CHECKLIST, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    validate_checklist(cfg)
    return cfg


def save_checklist(cfg: dict) -> None:
    validate_checklist(cfg)
    if CHECKLIST.exists():
        shutil.copy(CHECKLIST, STORE / "checklist.backup.yaml")
    with open(CHECKLIST, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False, width=110)


def reset_checklist() -> dict:
    shutil.copy(CHECKLIST_DEFAULT, CHECKLIST)
    return load_checklist()


def validate_checklist(cfg: dict) -> None:
    """Báo lỗi rõ ràng thay vì để luật chạy sai âm thầm."""
    for key in ("groups", "severity", "zone_types", "criteria", "detector"):
        if key not in cfg:
            raise ValueError(f"Bảng kiểm thiếu mục '{key}'")
    ids = set()
    for c in cfg["criteria"]:
        cid = c.get("id")
        if not cid or cid in ids:
            raise ValueError(f"Mã tiêu chí trống hoặc bị trùng: {cid!r}")
        ids.add(cid)
        if c.get("type") not in RULE_TYPES:
            raise ValueError(f"{cid}: loại luật không hợp lệ {c.get('type')!r}")
        if c.get("group") not in cfg["groups"]:
            raise ValueError(f"{cid}: nhóm {c.get('group')!r} chưa khai báo trong 'groups'")
        if c.get("severity") not in cfg["severity"]:
            raise ValueError(f"{cid}: mức độ {c.get('severity')!r} chưa khai báo trong 'severity'")
        z = c.get("zone")
        if z is not None and z not in cfg["zone_types"]:
            raise ValueError(f"{cid}: loại vùng {z!r} chưa khai báo trong 'zone_types'")
        if c["type"] in ("zone_occupancy", "zone_visibility") and z is None:
            raise ValueError(f"{cid}: luật {c['type']} bắt buộc phải có vùng")
        if c["type"] == "zone_visibility" and not c.get("target"):
            raise ValueError(f"{cid}: luật zone_visibility cần 'target'")


def active_criteria(cfg: dict) -> list[dict]:
    return [c for c in cfg["criteria"] if c.get("enabled", True)]


def detector_key(cfg: dict) -> str:
    """Băm phần cấu hình ảnh hưởng tới kết quả phát hiện (để cache)."""
    d = copy.deepcopy(cfg["detector"])
    for k in ("suppress_on_extinguisher", "custom_skip", "custom_conf"):  # hậu xử lý, không cần chạy lại YOLO
        d.pop(k, None)
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()[:10]


# ---------------------------------------------------------------- vùng camera
def load_zones() -> dict:
    """{camera: {zone_type: [[[x, y], ...], ...]}}, toạ độ chuẩn hoá 0..1."""
    if not ZONES.exists():
        shutil.copy(ZONES_SEED, ZONES)
    with open(ZONES, encoding="utf-8") as f:
        return json.load(f)


def save_zones(zones: dict) -> None:
    if ZONES.exists():  # giữ bản trước để khôi phục nếu xoá nhầm
        shutil.copy(ZONES, STORE / "zones.backup.json")
    with open(ZONES, "w", encoding="utf-8") as f:
        json.dump(zones, f, ensure_ascii=False, indent=1)


def view_of(name: str) -> str:
    """'v2b_07.jpg' -> 'v2b'."""
    return Path(name).stem.split("_")[0]


def camera_for_image(name: str, zones: dict) -> str | None:
    """Vùng vẽ riêng cho ảnh (khung lệch) ưu tiên hơn vùng của góc camera."""
    stem = Path(name).stem
    if stem in zones:
        return stem
    v = view_of(name)
    return v if v in zones else None


def camera_reference_image(camera: str) -> Path | None:
    """Ảnh nền để vẽ vùng cho một camera."""
    for ext in (".jpg", ".png"):
        p = CAMERA_DIR / f"{camera}{ext}"
        if p.exists():
            return p
    for p in dataset_images():
        if p.stem == camera:
            return p
    for p in dataset_images():
        if view_of(p.name) == camera:
            return p
    return None


def dataset_images() -> list[Path]:
    if not DATASET_IMAGES.exists():
        return []
    return sorted(p for p in DATASET_IMAGES.iterdir() if p.suffix.lower() in IMG_EXTS)
