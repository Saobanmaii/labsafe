"""Kiểm thử bộ luật bằng hộp bao tự tạo — gồm đúng ví dụ tính tay ở mục 4.2 đề cương.

    python src/test_rules.py
"""
from rules import PARAMS, evaluate_rules


def cell_box(c1, r1, c2, r2):
    """Ô (cột, hàng) đánh số từ 1 trên lưới 10x10, mỗi ô 1 đơn vị -> hộp bao bao trọn các ô."""
    return (c1 - 1, r1 - 1, c2, r2)


def rect(x1, y1, x2, y2):
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


full_box = dict(PARAMS, footprint_frac=1.0)  # ví dụ trong đề cương dùng cả hộp bao

# Lối đi: ô (3,1)–(7,10) = 5 x 10 = 50 ô
aisle = rect(*cell_box(3, 1, 7, 10))
zones = {"aisle": [aisle]}

# Ví dụ 1 (đề cương): vật cản ô (4,2)–(6,4) = 9 ô, nằm trọn trong lối đi -> R = 9/50 = 18%
r = evaluate_rules([{"cls": "chair", "conf": 0.9, "xyxy": cell_box(4, 2, 6, 4)}], zones, dict(full_box, tau_aisle=0.15))
assert abs(r["R_aisle"] - 0.18) < 1e-9 and r["C1"] == 1, r
print(f"Ví dụ 1 — vật cản nằm trọn trong lối đi: R = {r['R_aisle']:.0%} >= 15% -> Vi phạm ✓")

# Ví dụ 2: vật cản nhỏ ô (4,2)–(5,3) = 4 ô -> R = 8% < 15% -> Đạt
r = evaluate_rules([{"cls": "backpack", "conf": 0.9, "xyxy": cell_box(4, 2, 5, 3)}], zones, dict(full_box, tau_aisle=0.15))
assert abs(r["R_aisle"] - 0.08) < 1e-9 and r["C1"] == 0, r
print(f"Ví dụ 2 — vật cản nhỏ:                    R = {r['R_aisle']:.0%} <  15% -> Đạt ✓")

# Ví dụ 3: vật cản nằm một phần trong lối đi ô (1,5)–(4,8): 16 ô, chỉ cột 3–4 (8 ô) trong lối đi -> R = 16%
r = evaluate_rules([{"cls": "suitcase", "conf": 0.9, "xyxy": cell_box(1, 5, 4, 8)}], zones, dict(full_box, tau_aisle=0.15))
assert abs(r["R_aisle"] - 0.16) < 1e-9 and r["C1"] == 1, r
print(f"Ví dụ 3 — vật cản nằm một phần:           R = {r['R_aisle']:.0%} >= 15% -> Vi phạm ✓")

# Hai vật chồng lên nhau không bị tính trùng diện tích (dùng hợp ∪)
r = evaluate_rules([{"cls": "chair", "conf": 0.9, "xyxy": cell_box(4, 2, 6, 4)},
                    {"cls": "chair", "conf": 0.9, "xyxy": cell_box(4, 2, 6, 4)}], zones, full_box)
assert abs(r["R_aisle"] - 0.18) < 1e-9, r
print("Hai hộp trùng nhau không bị cộng đôi ✓")

# C2: 3 vật cá nhân trên bàn -> vi phạm; vật ngoài bàn không tính
bench = rect(0, 0, 10, 3)
dets = [{"cls": "cell phone", "conf": .8, "xyxy": (1, 1, 2, 2)},
        {"cls": "book", "conf": .8, "xyxy": (3, 1, 4, 2)},
        {"cls": "laptop", "conf": .8, "xyxy": (5, 0, 7, 2)},
        {"cls": "handbag", "conf": .8, "xyxy": (5, 6, 7, 8)}]
r = evaluate_rules(dets, {"bench": [bench]})
assert r["n_personal"] == 3 and r["C2"] == 1, r
print("C2 — 3 vật cá nhân trên bàn -> Vi phạm ✓")

# C3: bình nhìn rõ -> Đạt; bị thùng che một nửa -> Vi phạm; không thấy bình -> Vi phạm
ext_zone = {"extinguisher": [rect(0, 0, 2, 4)]}
ext = {"cls": "fire extinguisher", "conf": .9, "xyxy": (0, 0, 2, 4)}
assert evaluate_rules([ext], ext_zone)["C3"] == 0
assert evaluate_rules([ext, {"cls": "cardboard box", "conf": .9, "xyxy": (0, 2, 3, 5)}], ext_zone)["C3"] == 1
assert evaluate_rules([{"cls": "fire extinguisher", "conf": .9, "xyxy": (0, 0, 2, 1.5)}], ext_zone)["C3"] == 1
assert evaluate_rules([], ext_zone)["C3"] == 1
print("C3 — nhìn rõ: Đạt; bị che 1/2: Vi phạm; chỉ thấy phần trên: Vi phạm; mất bình: Vi phạm ✓")

# C4
assert evaluate_rules([{"cls": "cup", "conf": .7, "xyxy": (0, 0, 1, 1)}], {})["C4"] == 1
assert evaluate_rules([], {})["C4"] == 0
print("C4 — có cốc: Vi phạm; không có gì: Đạt ✓")

# Thiếu vùng -> None (không kết luận)
assert evaluate_rules([], {})["C1"] is None
print("\nTất cả kiểm thử đều đạt.")
