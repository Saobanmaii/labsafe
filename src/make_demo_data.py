"""Sinh dữ liệu GIẢ để chạy thử evaluate.py trước khi có ảnh thật. KHÔNG dùng số liệu này trong bài.

    python src/make_demo_data.py
    python src/evaluate.py --labels data/demo/labels --rule data/demo/results_rule.csv --vlm data/demo/results_vlm.csv --out outputs/demo
"""
import numpy as np
import pandas as pd

from common import CRITERIA, DATA

rng = np.random.default_rng(42)
demo = DATA / "demo"
(demo / "labels").mkdir(parents=True, exist_ok=True)

# 4 góc x 9 kịch bản theo PHOTO_GUIDE
SCEN = {1: [], 2: ["C1"], 3: ["C2"], 4: ["C3"], 5: ["C4"], 6: ["C1", "C2"], 7: ["C3", "C4"],
        8: ["C1", "C3", "C4"], 9: CRITERIA}
images, truth = [], []
for v in range(1, 5):
    for s, viol in SCEN.items():
        images.append(f"v{v}_s{s:02d}.jpg")
        truth.append([int(c in viol) for c in CRITERIA])
truth = np.array(truth)


def noisy(flip):
    """flip: xác suất lật nhãn cho từng tiêu chí."""
    return np.where(rng.random(truth.shape) < np.array(flip), 1 - truth, truth)


for k in range(1, 4):  # người chấm: C1, C2 chủ quan hơn
    df = pd.DataFrame(noisy([0.12, 0.15, 0.05, 0.03]), columns=CRITERIA)
    df.insert(0, "image", images)
    df["ghi_chu"] = ""
    df.sample(frac=1, random_state=k).to_csv(demo / "labels" / f"rater{k}.csv", index=False, encoding="utf-8-sig")

rule = pd.DataFrame(noisy([0.2, 0.25, 0.15, 0.2]), columns=CRITERIA)
rule.insert(0, "image", images)
rule.to_csv(demo / "results_rule.csv", index=False, encoding="utf-8-sig")

rows = []
for p, flip in {"P1": [0.15, 0.2, 0.2, 0.08], "P2": [0.25, 0.3, 0.25, 0.1], "P3": [0.18, 0.2, 0.22, 0.08]}.items():
    pred = noisy(flip)
    for img, r in zip(images, pred):
        rows.append({"image": img, "backend": "demo", "model": "demo-vlm", "prompt": p, "run": 0,
                     **dict(zip(CRITERIA, r)), "reason": "demo", "error": ""})
pd.DataFrame(rows).to_csv(demo / "results_vlm.csv", index=False, encoding="utf-8-sig")
print(f"Đã tạo dữ liệu giả trong {demo}")
