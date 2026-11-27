"""Vẽ vùng lên ảnh đầu tiên của mỗi góc chụp -> data/zones_preview/ (cho người chấm xem và để kiểm tra vùng)."""
from collections import OrderedDict

from common import DATA, list_images, load_image_bgr, load_zones, save_image_bgr, view_of
from rules import draw_zones

zones = load_zones()
first_of_view = OrderedDict()
for p in list_images():
    first_of_view.setdefault(view_of(p.name), p)

for view, p in first_of_view.items():
    if view not in zones:
        print(f"[!] Góc {view} chưa có vùng trong zones.json")
        continue
    img = load_image_bgr(p)
    draw_zones(img, zones[view])
    save_image_bgr(DATA / "zones_preview" / f"{view}.jpg", img)
    print(f"{view}: {p.name}")
