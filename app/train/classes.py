"""Danh sách lớp của mô hình nâng cấp "LabSafe-6" — dùng chung cho mọi script train và cho ứng dụng.

Tên tiếng Việt (không dấu) là tên dùng khi GÁN NHÃN trên Roboflow.
Tên tiếng Anh là tên bộ luật trong checklist.yaml dùng (ứng dụng tự đổi tên khi chạy).
"""

CLASSES = ["binh_chua_chay", "ao_khoac", "mu", "vi", "do_uong", "do_an"]

TO_RULE_NAME = {
    "binh_chua_chay": "fire extinguisher",
    "ao_khoac": "jacket",
    "mu": "hat",
    "vi": "wallet",
    "do_uong": "drink",
    "do_an": "food",
}

# Lớp Open Images (tên đúng như oidv7-class-descriptions-boxable.csv) -> lớp LabSafe
OPEN_IMAGES_MAP = {
    "Jacket": "ao_khoac", "Coat": "ao_khoac",
    "Hat": "mu", "Sun hat": "mu", "Cowboy hat": "mu", "Helmet": "mu", "Bicycle helmet": "mu",
    "Bottle": "do_uong", "Mug": "do_uong", "Coffee cup": "do_uong", "Tin can": "do_uong", "Drink": "do_uong",
    "Snack": "do_an", "Cookie": "do_an", "Doughnut": "do_an", "Bread": "do_an", "Sandwich": "do_an",
    "Banana": "do_an", "Apple": "do_an", "Orange (fruit)": "do_an", "Fast food": "do_an",
}
# Open Images không có lớp ví và bình chữa cháy:
#   ví             -> chỉ có từ ảnh nhóm tự chụp (Roboflow)
#   bình chữa cháy -> bộ Fire-ART đã dùng cho mô hình bình (D:/Study/datasets/extinguisher_yolo)
