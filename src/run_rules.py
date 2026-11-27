"""Cột 2 — Hệ thống dựa trên luật: YOLO (COCO + bình chữa cháy + từ vựng mở) -> bộ luật -> results_rule.csv

    python src/run_rules.py
    python src/run_rules.py --no-world        # tắt YOLO-World (nếu không cài được CLIP)
"""
import argparse
import json
import time
from pathlib import Path

import pandas as pd
import torch
from ultralytics import YOLO

from common import MODELS, OUT, list_images, load_image_bgr, load_zones, save_image_bgr, view_of, zones_to_px
from rules import EXTINGUISHER, PARAMS, draw_result, evaluate_rules

ap = argparse.ArgumentParser()
ap.add_argument("--coco-model", default="yolo11s.pt")
ap.add_argument("--ext-model", default=str(MODELS / "extinguisher_best.pt"))
ap.add_argument("--world-model", default="yolov8s-worldv2.pt")
ap.add_argument("--no-world", action="store_true")
ap.add_argument("--conf", type=float, default=0.30)
ap.add_argument("--images", default=None, help="thư mục ảnh (mặc định data/images)")
ap.add_argument("--zones", default=None, help="file vùng (mặc định data/zones.json)")
ap.add_argument("--out", default=str(OUT / "results_rule.csv"))
args = ap.parse_args()

device = 0 if torch.cuda.is_available() else "cpu"
zones = load_zones(Path(args.zones)) if args.zones else load_zones()
annotated_dir = Path(args.out).parent / "annotated"


def run(model, img, rename=None):
    r = model.predict(img, conf=args.conf, device=device, verbose=False)[0]
    dets = []
    for xyxy, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist()):
        name = r.names[int(c)]
        dets.append({"cls": rename(name) if rename else name, "conf": float(s), "xyxy": tuple(xyxy)})
    return dets


# 1) YOLO COCO có sẵn: ghế, balo, cốc, chai, điện thoại, laptop...
coco = YOLO(args.coco_model)

# 2) Bình chữa cháy: model fine-tune; mọi tên lớp chứa "extinguish" quy về một tên chung
ext = None
if Path(args.ext_model).exists():
    ext = YOLO(args.ext_model)
else:  # chưa train xong -> dùng YOLO-World thay thế
    print(f"[!] Chưa có {args.ext_model}. Sẽ dùng YOLO-World cho lớp bình chữa cháy.")

# 3) YOLO-World (từ vựng mở): "cardboard box" (COCO không có thùng carton) + dự phòng bình chữa cháy
world = None
if not args.no_world:
    from ultralytics import YOLOWorld
    world = YOLOWorld(args.world_model)
    world_classes = ["cardboard box"] + ([] if ext else [EXTINGUISHER])
    world.set_classes(world_classes)

rows = []
for p in (list_images(Path(args.images)) if args.images else list_images()):
    view = view_of(p.name)
    zkey = p.stem if p.stem in zones else view  # vùng vẽ riêng cho ảnh (khung lệch) ưu tiên hơn vùng của góc
    if zkey not in zones:
        print(f"[!] {p.name}: góc {view} chưa có vùng -> bỏ qua")
        continue
    img = load_image_bgr(p)
    h, w = img.shape[:2]

    t0 = time.perf_counter()
    dets = [dict(d, src="coco") for d in run(coco, img)]
    if ext:
        dets += [dict(d, src="ext") for d in run(ext, img, rename=lambda n: EXTINGUISHER if "extinguish" in n.lower() else n)
                 if d["cls"] == EXTINGUISHER]
    if world:
        dets += [dict(d, src="world") for d in run(world, img)]
    res = evaluate_rules(dets, zones_to_px(zones[zkey], w, h))
    ms = (time.perf_counter() - t0) * 1000

    rows.append({"image": p.name, "view": view, "zones": zkey, **res, "time_ms": round(ms, 1),
                 "detections": json.dumps([{k: (round(v, 3) if isinstance(v, float) else v) for k, v in d.items() if k != "xyxy"} for d in dets])})
    save_image_bgr(annotated_dir / p.name, draw_result(img, zones[zkey], dets, res))
    print(f"{p.name}: C1={res['C1']} C2={res['C2']} C3={res['C3']} C4={res['C4']}  ({ms:.0f} ms)")

df = pd.DataFrame(rows)
Path(args.out).parent.mkdir(parents=True, exist_ok=True)
df.to_csv(args.out, index=False, encoding="utf-8-sig")
meta = {"coco_model": args.coco_model, "ext_model": args.ext_model if ext else None,
        "world_model": args.world_model if world else None, "conf": args.conf, "params": PARAMS,
        "device": torch.cuda.get_device_name(0) if device == 0 else "cpu",
        "mean_time_ms": float(df["time_ms"].mean()) if len(df) else None}
(Path(args.out).parent / "results_rule_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nĐã lưu {args.out} ({len(df)} ảnh). Ảnh minh hoạ: {annotated_dir}")
