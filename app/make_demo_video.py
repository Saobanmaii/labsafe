"""Tạo video mẫu giả lập camera cố định từ các ảnh cùng một góc chụp (dùng khi chưa quay video thật).

Mỗi ảnh giữ N giây, chuyển cảnh mờ dần — giống cảnh phòng thay đổi theo thời gian (có người để balo ra lối đi,
đặt cốc nước lên bàn...). Ảnh có vùng vẽ riêng (khung lệch) được bỏ qua để vùng của camera khớp mọi khung.

    python app/make_demo_video.py                 # mặc định góc v2c và v2b
    python app/make_demo_video.py --views v1 v3a --hold 4
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from core.config import STORE, dataset_images, load_zones, view_of  # noqa: E402
from core.render import load_image  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--views", nargs="+", default=["v2c", "v2b"])
ap.add_argument("--hold", type=float, default=5.0, help="số giây giữ mỗi ảnh")
ap.add_argument("--fade", type=float, default=0.6)
ap.add_argument("--fps", type=int, default=10)
ap.add_argument("--width", type=int, default=1280)
args = ap.parse_args()

zones = load_zones()
for v in args.views:
    imgs = [p for p in dataset_images() if view_of(p.name) == v and p.stem not in zones]
    if not imgs:
        print(f"[!] không có ảnh cho góc {v}")
        continue
    frames = []
    for p in imgs:
        im = load_image(p)
        h, w = im.shape[:2]
        frames.append(cv2.resize(im, (args.width, int(h * args.width / w)), interpolation=cv2.INTER_AREA))
    H = min(f.shape[0] for f in frames)
    frames = [f[:H] for f in frames]
    out = STORE / f"demo_{v}.mp4"
    vw = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (args.width, H))
    nh, nf = int(args.hold * args.fps), int(args.fade * args.fps)
    for k, f in enumerate(frames):
        for _ in range(nh):
            vw.write(f)
        if k + 1 < len(frames):
            for j in range(1, nf + 1):
                a = j / (nf + 1)
                vw.write(cv2.addWeighted(f, 1 - a, frames[k + 1], a, 0))
    vw.release()
    print(f"{out}  ({len(frames)} ảnh: {', '.join(p.stem for p in imgs)}, ~{len(frames) * (args.hold + args.fade):.0f} s)")
