"""Tự đề xuất vùng camera bằng phân đoạn ngữ nghĩa (semantic segmentation).

Mô hình SegFormer-B2 đã học trên ADE20K (150 lớp cảnh trong nhà/ngoài trời) gán nhãn cho TỪNG ĐIỂM ẢNH.
Từ ảnh phòng SẠCH của một camera:
  - Lối đi            = các điểm ảnh "sàn" (floor, rug) nhìn thấy được
  - Mặt bàn thí nghiệm = các điểm ảnh "bàn" (table, desk, counter, countertop)
  - Vị trí bình        = khung bình chữa cháy do mô hình nhóm tự huấn luyện phát hiện, nới rộng một chút
Mặt nạ được làm sạch (đóng/mở hình thái học, bỏ mảng nhỏ) rồi đổi thành đa giác, toạ độ chuẩn hoá 0..1.

Phải dùng ảnh phòng SẠCH: nếu có balo giữa lối đi, chỗ đó là "balo" chứ không phải "sàn", và vùng lối đi
sẽ thủng đúng chỗ cần kiểm tra. Người dùng xem lại và sửa đề xuất trên trang «Vùng camera».
"""
from __future__ import annotations

import cv2
import numpy as np

MODEL = "nvidia/segformer-b5-finetuned-ade-640-640"  # B5 nhận bàn tốt hơn B2 trên ảnh phòng lab
FLOOR = {"floor", "rug"}
TABLE = {"table", "desk", "counter", "countertop"}


class Segmenter:
    def __init__(self, name: str = MODEL):
        import torch
        from transformers import AutoImageProcessor, SegformerForSemanticSegmentation

        self.torch = torch
        self.proc = AutoImageProcessor.from_pretrained(name)
        self.model = SegformerForSemanticSegmentation.from_pretrained(name).eval()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.id2label = {int(k): v for k, v in self.model.config.id2label.items()}

    def labels(self, img_bgr: np.ndarray, long_edge: int = 1024) -> tuple[np.ndarray, float]:
        """Bản đồ nhãn (H', W') ở ảnh thu nhỏ, và hệ số thu nhỏ."""
        h, w = img_bgr.shape[:2]
        s = min(1.0, long_edge / max(h, w))
        small = cv2.resize(img_bgr, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA) if s < 1 else img_bgr
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        with self.torch.no_grad():
            out = self.model(**self.proc(images=rgb, return_tensors="pt").to(self.device))
            logits = self.torch.nn.functional.interpolate(out.logits, size=rgb.shape[:2], mode="bilinear",
                                                          align_corners=False)
            return logits.argmax(1)[0].cpu().numpy().astype(np.int32), s

    def mask(self, seg: np.ndarray, names: set[str]) -> np.ndarray:
        ids = [i for i, n in self.id2label.items() if n in names]
        return np.isin(seg, ids).astype(np.uint8)


def _clean(mask: np.ndarray, min_frac: float = 0.01) -> np.ndarray:
    h, w = mask.shape
    k = max(3, int(min(h, w) * 0.015)) | 1
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    m = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, ker)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, ker)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= min_frac * h * w:
            keep[lab == i] = 1
    return keep


def mask_to_polys(mask: np.ndarray, eps: float = 0.004, max_polys: int = 4) -> list[list[list[float]]]:
    """Mặt nạ nhị phân -> đa giác chuẩn hoá (giữ tối đa max_polys mảng lớn nhất)."""
    h, w = mask.shape
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cs = sorted(cs, key=cv2.contourArea, reverse=True)[:max_polys]
    out = []
    for c in cs:
        a = cv2.approxPolyDP(c, eps * cv2.arcLength(c, True), True)
        if len(a) >= 3:
            out.append([[round(float(x) / w, 4), round(float(y) / h, 4)] for x, y in a[:, 0, :]])
    return out


def _under(table: np.ndarray, depth: float = 0.25) -> np.ndarray:
    """Dải ngay bên dưới mặt bàn (gầm bàn): theo từng cột, từ mép dưới của bàn xuống thêm depth × chiều cao ảnh."""
    h, w = table.shape
    out = np.zeros_like(table)
    rows = np.arange(h)[:, None]
    has = table.any(0)
    if not has.any():
        return out
    bottom = np.where(has, h - 1 - np.argmax(table[::-1], 0), -1)
    band = (rows > bottom[None, :]) & (rows <= bottom[None, :] + int(depth * h)) & has[None, :]
    out[band] = 1
    return out


def propose_zones(img_bgr: np.ndarray, seg: Segmenter, detector=None, ext_pad: float = 0.15,
                  exclude_under_table: bool = True) -> dict:
    """Đề xuất {aisle, bench, extinguisher} cho một camera từ ảnh phòng sạch."""
    lab, _ = seg.labels(img_bgr)
    zones = {}
    table = _clean(seg.mask(lab, TABLE))
    floor = seg.mask(lab, FLOOR)
    if exclude_under_table:  # sàn dưới gầm bàn không phải lối đi
        floor = floor & (1 - _under(table))
    floor = _clean(floor)
    if floor.any():
        zones["aisle"] = mask_to_polys(floor)
    if table.any():
        zones["bench"] = mask_to_polys(table)
    if detector is not None:
        from .detector import EXTINGUISHER
        dets, _ = detector.detect(img_bgr)
        ext = sorted((d for d in dets if d["cls"] == EXTINGUISHER), key=lambda d: -d["conf"])
        if ext:
            H, W = img_bgr.shape[:2]
            x1, y1, x2, y2 = ext[0]["xyxy"]
            dx, dy = (x2 - x1) * ext_pad, (y2 - y1) * ext_pad
            x1, y1, x2, y2 = max(0, x1 - dx), max(0, y1 - dy), min(W, x2 + dx), min(H, y2 + dy)
            zones["extinguisher"] = [[[round(x1 / W, 4), round(y1 / H, 4)], [round(x2 / W, 4), round(y1 / H, 4)],
                                      [round(x2 / W, 4), round(y2 / H, 4)], [round(x1 / W, 4), round(y2 / H, 4)]]]
    return zones


def zones_iou(a: dict, b: dict, ztype: str, size: tuple[int, int] = (400, 300)) -> float | None:
    """IoU giữa hai bộ vùng (cùng loại) bằng cách tô lên lưới điểm ảnh."""
    w, h = size

    def raster(z):
        m = np.zeros((h, w), np.uint8)
        for poly in z.get(ztype, []):
            cv2.fillPoly(m, [np.array([[x * w, y * h] for x, y in poly], np.int32)], 1)
        return m

    ma, mb = raster(a), raster(b)
    union = (ma | mb).sum()
    return None if union == 0 else float((ma & mb).sum() / union)
