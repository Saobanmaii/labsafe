"""Bộ luật quan hệ không gian: từ danh sách đối tượng phát hiện + vùng -> Đạt (0) / Vi phạm (1).

Hàm ở đây không phụ thuộc YOLO, nên kiểm thử được bằng hộp bao tự tạo (xem test_rules.py).
Một detection là dict: {"cls": str, "conf": float, "xyxy": (x1, y1, x2, y2), "src": str}.
"""
import cv2
import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

# ---- Lớp đối tượng cho từng tiêu chí (tên lớp COCO + lớp từ vựng mở) ----
C1_OBSTACLES = {"chair", "backpack", "suitcase", "handbag", "bench", "cardboard box"}
C2_PERSONAL = {"cell phone", "laptop", "backpack", "handbag", "book"}
C4_FOOD_DRINK = {"cup", "bottle", "wine glass", "bowl", "banana", "apple", "sandwich",
                 "orange", "pizza", "donut", "cake", "hot dog", "broccoli", "carrot"}
EXTINGUISHER = "fire extinguisher"
C3_OCCLUDERS = (C1_OBSTACLES | C2_PERSONAL | {"umbrella", "tie"}) - {"bench"}

# ---- Ngưỡng (cố định TRƯỚC khi xem kết quả; nếu hiệu chỉnh phải ghi rõ trong bài) ----
PARAMS = {
    "footprint_frac": 0.25,  # phần đáy hộp bao coi là "chân" vật chạm sàn
    "tau_aisle": 0.05,       # C1: vi phạm nếu tỷ lệ chiếm dụng lối đi R >= 5%
    "min_personal": 3,       # C2: vi phạm nếu >= 3 vật dụng cá nhân trên bàn
    "tau_visible": 0.5,      # C3: vi phạm nếu phần bình nhìn thấy < 50% vùng bình
    "tau_occlusion": 1 / 3,  # C3: vi phạm nếu vật khác phủ >= 1/3 vùng bình
    "min_food": 1,           # C4: vi phạm nếu có >= 1 đồ ăn/uống
}


def _union_polys(polys):
    shapes = [Polygon(p).buffer(0) for p in polys if len(p) >= 3]
    return unary_union(shapes) if shapes else None


def _center(xyxy):
    x1, y1, x2, y2 = xyxy
    return (x1 + x2) / 2, (y1 + y2) / 2


def evaluate_rules(dets: list[dict], zones_px: dict, params: dict = PARAMS) -> dict:
    """Trả về dict gồm kết luận C1..C4 (0/1, hoặc None nếu thiếu vùng) và các đại lượng trung gian."""
    out = {}

    # C1 — tỷ lệ chiếm dụng lối đi: R = |(∪ đáy hộp) ∩ A| / |A|
    aisle = _union_polys(zones_px.get("aisle", []))
    if aisle is None or aisle.area == 0:
        out.update(C1=None, R_aisle=None)
    else:
        feet = []
        for d in dets:
            if d["cls"] in C1_OBSTACLES:
                x1, y1, x2, y2 = d["xyxy"]
                feet.append(box(x1, y2 - params["footprint_frac"] * (y2 - y1), x2, y2))
        occupied = unary_union(feet).intersection(aisle).area if feet else 0.0
        r = occupied / aisle.area
        out.update(C1=int(r >= params["tau_aisle"]), R_aisle=round(r, 4))

    # C2 — đếm vật dụng cá nhân có tâm nằm trên bàn
    bench = _union_polys(zones_px.get("bench", []))
    if bench is None:
        out.update(C2=None, n_personal=None)
    else:
        n = sum(1 for d in dets if d["cls"] in C2_PERSONAL and bench.contains(Point(_center(d["xyxy"]))))
        out.update(C2=int(n >= params["min_personal"]), n_personal=n)

    # C3 — bình chữa cháy: phần nhìn thấy trong vùng bình và phần bị vật khác phủ
    zone = _union_polys(zones_px.get("extinguisher", []))
    if zone is None or zone.area == 0:
        out.update(C3=None, ext_visible=None, ext_occluded=None)
    else:
        ext_boxes = [box(*d["xyxy"]) for d in dets if d["cls"] == EXTINGUISHER]
        ext_boxes = [b for b in ext_boxes if b.intersects(zone)]
        visible = unary_union(ext_boxes).intersection(zone).area / zone.area if ext_boxes else 0.0
        occ_boxes = [box(*d["xyxy"]) for d in dets if d["cls"] in C3_OCCLUDERS]
        occluded = unary_union(occ_boxes).intersection(zone).area / zone.area if occ_boxes else 0.0
        violated = (not ext_boxes) or visible < params["tau_visible"] or occluded >= params["tau_occlusion"]
        out.update(C3=int(violated), ext_visible=round(min(visible, 1.0), 4), ext_occluded=round(occluded, 4))

    # C4 — có đồ ăn/uống ở bất kỳ đâu trong ảnh
    food = [d["cls"] for d in dets if d["cls"] in C4_FOOD_DRINK]
    out.update(C4=int(len(food) >= params["min_food"]), n_food=len(food), food_labels="|".join(sorted(food)))
    return out


# ---- Vẽ minh hoạ (dùng cho hình trong bài báo) ----
ZONE_COLORS = {"aisle": (80, 200, 80), "bench": (230, 150, 40), "extinguisher": (60, 60, 230)}


def _thick(img):
    return max(2, img.shape[1] // 600)


def draw_zones(img: np.ndarray, view_zones_norm: dict, alpha: float = 0.25) -> np.ndarray:
    h, w = img.shape[:2]
    overlay = img.copy()
    for ztype, polys in view_zones_norm.items():
        color = ZONE_COLORS.get(ztype, (200, 200, 200))
        for poly in polys:
            pts = np.array([[x * w, y * h] for x, y in poly], dtype=np.int32)
            cv2.fillPoly(overlay, [pts], color)
            cv2.polylines(img, [pts], True, color, _thick(img))
            cv2.putText(img, ztype, tuple(pts[0]), cv2.FONT_HERSHEY_SIMPLEX, _thick(img) * 0.5, color, _thick(img))
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, dst=img)
    return img


def draw_result(img: np.ndarray, view_zones_norm: dict, dets: list[dict], res: dict) -> np.ndarray:
    draw_zones(img, view_zones_norm)
    t = _thick(img)
    for d in dets:
        x1, y1, x2, y2 = map(int, d["xyxy"])
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 255), t)
        cv2.putText(img, f'{d["cls"]} {d["conf"]:.2f}', (x1, max(0, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, t * 0.4, (0, 255, 255), max(1, t // 2))
    def v(c):
        return "N/A" if res[c] is None else ("VIOLATION" if res[c] else "OK")

    lines = [
        f"C1 aisle   : {v('C1')}  R={res.get('R_aisle')}",
        f"C2 personal: {v('C2')}  n={res.get('n_personal')}",
        f"C3 extingu.: {v('C3')}  vis={res.get('ext_visible')} occ={res.get('ext_occluded')}",
        f"C4 food    : {v('C4')}  n={res.get('n_food')}",
    ]
    y = 30 * t
    for line in lines:
        cv2.putText(img, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, t * 0.5, (0, 0, 0), t * 3)
        cv2.putText(img, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, t * 0.5, (255, 255, 255), t)
        y += 18 * t
    return img
