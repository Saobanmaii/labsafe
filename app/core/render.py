"""Vẽ ảnh bằng chứng (vùng + khung đối tượng + kết luận), cắt vùng bằng chứng, làm mờ người."""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

from .detector import PERSON

RED = (40, 40, 230)       # BGR
GREEN = (60, 180, 60)
GREY = (200, 200, 200)
MAGENTA = (200, 60, 200)
_FONT_CACHE: dict[int, ImageFont.FreeTypeFont] = {}


def font(size: int):
    size = max(10, int(size))
    if size not in _FONT_CACHE:
        for name in ("arial.ttf", "C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf"):
            try:
                _FONT_CACHE[size] = ImageFont.truetype(name, size)
                break
            except OSError:
                continue
        else:
            _FONT_CACHE[size] = ImageFont.load_default()
    return _FONT_CACHE[size]


# ------------------------------------------------------------------ đọc / ghi ảnh
def load_image(src) -> np.ndarray:
    """Đọc ảnh (đường dẫn, bytes hoặc file upload), xoay theo EXIF, trả về BGR."""
    if isinstance(src, (str, Path)):
        img = Image.open(src)
    else:
        data = src if isinstance(src, (bytes, bytearray)) else src.getvalue()
        img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img).convert("RGB")
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def save_jpg(path: Path, img: np.ndarray, quality: int = 88) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    assert ok
    buf.tofile(str(path))


def jpeg_bytes(img: np.ndarray, long_edge: int = 1568, quality: int = 90) -> bytes:
    h, w = img.shape[:2]
    s = min(1.0, long_edge / max(h, w))
    if s < 1:
        img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes()


def to_rgb(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def downscale(img: np.ndarray, long_edge: int) -> tuple[np.ndarray, float]:
    h, w = img.shape[:2]
    s = min(1.0, long_edge / max(h, w))
    if s < 1:
        img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return img.copy(), s


# ------------------------------------------------------------------ ẩn danh
def blur_people(img: np.ndarray, dets: list[dict], scale: float = 1.0, pad: float = 0.15) -> tuple[np.ndarray, int]:
    """Làm mờ mạnh toàn bộ vùng người (lớp 'person' của COCO). Trả về (ảnh, số người)."""
    h, w = img.shape[:2]
    n = 0
    for d in dets:
        if d["cls"] != PERSON:
            continue
        x1, y1, x2, y2 = (v * scale for v in d["xyxy"])
        dx, dy = (x2 - x1) * pad, (y2 - y1) * pad
        x1, y1 = int(max(0, x1 - dx)), int(max(0, y1 - dy))
        x2, y2 = int(min(w, x2 + dx)), int(min(h, y2 + dy))
        if x2 - x1 < 2 or y2 - y1 < 2:
            continue
        roi = img[y1:y2, x1:x2]
        small = cv2.resize(roi, (max(1, (x2 - x1) // 16), max(1, (y2 - y1) // 16)), interpolation=cv2.INTER_LINEAR)
        img[y1:y2, x1:x2] = cv2.GaussianBlur(cv2.resize(small, (x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST),
                                             (0, 0), 3)
        n += 1
    return img, n


# ------------------------------------------------------------------ vẽ
def _poly_px(poly, w, h):
    return np.array([[x * w, y * h] for x, y in poly], dtype=np.int32)


def render(img_bgr: np.ndarray, cam_zones: dict, dets: list[dict], results: list, cfg: dict, *,
           long_edge: int = 1600, show_zones: bool = True, show_all: bool = True,
           blur: bool = False, banner: str | None = None) -> np.ndarray:
    """Ảnh bằng chứng: vùng vi phạm viền đỏ, vật gây vi phạm khung đỏ có nhãn mã tiêu chí."""
    img, s = downscale(img_bgr, long_edge)
    if blur:
        blur_people(img, dets, s)
    h, w = img.shape[:2]
    t = max(2, w // 500)
    ztypes = cfg["zone_types"]

    violated_zones = {r.zone for r in results if r.status == 1 and r.zone}
    if show_zones:
        overlay = img.copy()
        for zt, polys in cam_zones.items():
            color = tuple(ztypes.get(zt, {}).get("color", GREY))
            for poly in polys:
                cv2.fillPoly(overlay, [_poly_px(poly, w, h)], color)
        cv2.addWeighted(overlay, 0.22, img, 0.78, 0, dst=img)
        for zt, polys in cam_zones.items():
            bad = zt in violated_zones
            color = RED if bad else tuple(ztypes.get(zt, {}).get("color", GREY))
            for poly in polys:
                cv2.polylines(img, [_poly_px(poly, w, h)], True, color, t * (2 if bad else 1), cv2.LINE_AA)

    # bằng chứng: chỉ số detection -> các tiêu chí liên quan
    ev: dict[int, list] = {}
    for r in results:
        if r.engine == "rules" or r.vlm_status is None:
            for i in r.evidence:
                ev.setdefault(i, []).append(r)
    labels = []
    for i, d in enumerate(dets):
        if d["cls"] == PERSON and blur:
            continue
        rs = ev.get(i, [])
        if not rs and not show_all:
            continue
        bad = any(r.status == 1 for r in rs)
        color = RED if bad else (GREEN if rs else (0, 215, 255))
        x1, y1, x2, y2 = (int(v * s) for v in d["xyxy"])
        cv2.rectangle(img, (x1, y1), (x2, y2), color, t * (2 if bad else 1), cv2.LINE_AA)
        tag = (",".join(r.id for r in rs) + " ") if rs else ""
        labels.append(((x1, y1), f"{tag}{d['cls']} {d['conf']:.2f}", color, bad))
    # bằng chứng do Gemini khoanh
    for r in results:
        if r.engine != "vlm":
            continue
        for b in r.vlm_boxes:
            x1, y1, x2, y2 = (int(b["box"][0] * w), int(b["box"][1] * h), int(b["box"][2] * w), int(b["box"][3] * h))
            color = RED if r.status == 1 else MAGENTA
            cv2.rectangle(img, (x1, y1), (x2, y2), color, t * 2, cv2.LINE_AA)
            labels.append(((x1, y1), f"{r.id} Gemini: {b.get('label', '')}", color, r.status == 1))

    # chữ (PIL để có tiếng Việt)
    pil = Image.fromarray(to_rgb(img))
    dr = ImageDraw.Draw(pil)
    f = font(max(14, w // 75))
    placed: list[tuple[int, int, int, int]] = []
    if show_zones:  # nhãn vùng vẽ trước, nhãn đối tượng sẽ tránh chúng
        fz = font(max(13, w // 85))
        for zt, polys in cam_zones.items():
            name = ztypes.get(zt, {}).get("name", zt)
            bad = zt in violated_zones
            for poly in polys[:1]:
                px = _poly_px(poly, w, h)
                cx, cy = int(px[:, 0].mean()), int(px[:, 1].mean())
                txt = name + (" — VI PHẠM" if bad else "")
                bb = dr.textbbox((cx, cy), txt, font=fz, anchor="mm")
                dr.rectangle([bb[0] - 4, bb[1] - 3, bb[2] + 4, bb[3] + 3],
                             fill=(230, 40, 40) if bad else (30, 30, 30))
                dr.text((cx, cy), txt, font=fz, fill=(255, 255, 255), anchor="mm")
                placed.append((bb[0] - 4, bb[1] - 3, bb[2] + 4, bb[3] + 3))
    # nhãn vi phạm vẽ sau cùng để nằm trên; nhãn chồng nhau thì đẩy xuống dưới
    for (x, y), text, color, _ in sorted(labels, key=lambda l: l[3]):
        rgb = color[::-1]
        bb = dr.textbbox((0, 0), text, font=f)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        y0 = max(0, y - th - 8)
        x = min(max(0, x), max(0, w - tw - 8))
        for _ in range(20):
            hit = next((p for p in placed if x < p[2] and x + tw + 8 > p[0] and y0 < p[3] and y0 + th + 8 > p[1]), None)
            if hit is None:
                break
            y0 = hit[3] + 1
        placed.append((x, y0, x + tw + 8, y0 + th + 8))
        dr.rectangle([x, y0, x + tw + 8, y0 + th + 8], fill=rgb)
        dr.text((x + 4, y0 + 2), text, font=f, fill=(255, 255, 255))

    if banner is not None:
        pil = _add_banner(pil, banner, results)
    return cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR)


def _add_banner(pil: Image.Image, title: str, results) -> Image.Image:
    w, h = pil.size
    f1, f2 = font(max(16, w // 55)), font(max(14, w // 70))
    bad = [r for r in results if r.status == 1]
    lines = [f"{title}  ·  {datetime.now():%d/%m/%Y %H:%M:%S}",
             ("VI PHẠM: " + "; ".join(f"{r.id} {r.name}" for r in bad)) if bad else "ĐẠT tất cả tiêu chí"]
    bh = int(f1.size * 1.4 + f2.size * 1.5 + 16)
    out = Image.new("RGB", (w, h + bh), (25, 25, 30))
    out.paste(pil, (0, bh))
    dr = ImageDraw.Draw(out)
    dr.text((12, 8), lines[0], font=f1, fill=(255, 255, 255))
    dr.text((12, 8 + int(f1.size * 1.4)), lines[1], font=f2, fill=(255, 90, 90) if bad else (120, 220, 120))
    return out


def evidence_crop(img_bgr: np.ndarray, cam_zones: dict, dets: list[dict], r, pad: float = 0.08) -> np.ndarray | None:
    """Cắt vùng bằng chứng của một tiêu chí: vùng chức năng + các vật liên quan."""
    h, w = img_bgr.shape[:2]
    xs, ys = [], []
    for poly in cam_zones.get(r.zone, []) if r.zone else []:
        xs += [x * w for x, _ in poly]
        ys += [y * h for _, y in poly]
    for i in r.evidence:
        x1, y1, x2, y2 = dets[i]["xyxy"]
        xs += [x1, x2]
        ys += [y1, y2]
    for b in r.vlm_boxes:
        xs += [b["box"][0] * w, b["box"][2] * w]
        ys += [b["box"][1] * h, b["box"][3] * h]
    if not xs:
        return None
    x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
    px, py = (x2 - x1) * pad + 20, (y2 - y1) * pad + 20
    x1, y1 = int(max(0, x1 - px)), int(max(0, y1 - py))
    x2, y2 = int(min(w, x2 + px)), int(min(h, y2 + py))
    if x2 - x1 < 10 or y2 - y1 < 10:
        return None
    return img_bgr[y1:y2, x1:x2]


def draw_zones_only(img_bgr: np.ndarray, cam_zones: dict, cfg: dict, pending: list | None = None,
                    pending_color=(0, 255, 255)) -> np.ndarray:
    """Ảnh nền cho trình vẽ vùng: các vùng đã lưu + đa giác đang vẽ dở."""
    img = img_bgr.copy()
    h, w = img.shape[:2]
    t = max(2, w // 400)
    overlay = img.copy()
    for zt, polys in cam_zones.items():
        color = tuple(cfg["zone_types"].get(zt, {}).get("color", GREY))
        for poly in polys:
            cv2.fillPoly(overlay, [_poly_px(poly, w, h)], color)
            cv2.polylines(img, [_poly_px(poly, w, h)], True, color, t, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.3, img, 0.7, 0, dst=img)
    if pending:
        pts = _poly_px(pending, w, h)
        if len(pts) > 1:
            cv2.polylines(img, [pts], False, pending_color, t, cv2.LINE_AA)
        for p in pts:
            cv2.circle(img, tuple(int(v) for v in p), t * 3, pending_color, -1, cv2.LINE_AA)
    return img
