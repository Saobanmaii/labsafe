"""Fine-tune YOLO phát hiện bình chữa cháy trên dataset công khai (Fire-ART, đã qua prep_fireart.py).

    python src/train_extinguisher.py --data D:/Study/datasets/extinguisher_yolo/data.yaml
"""
import argparse
import json
import shutil
from pathlib import Path

from ultralytics import YOLO

from common import MODELS, OUT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="đường dẫn data.yaml của dataset")
    ap.add_argument("--model", default="yolo11n.pt")  # bản nhỏ nhất, vừa GPU 2 GB (MX350)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()

    model = YOLO(args.model)
    model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch, workers=args.workers,
                project=str(OUT / "train"), name="extinguisher", exist_ok=True, patience=10)

    best = Path(model.trainer.best)
    MODELS.mkdir(parents=True, exist_ok=True)
    shutil.copy(best, MODELS / "extinguisher_best.pt")

    metrics = YOLO(best).val(data=args.data, split="val", workers=args.workers)
    summary = {
        "base_model": args.model, "epochs": args.epochs, "imgsz": args.imgsz,
        "mAP50": float(metrics.box.map50), "mAP50_95": float(metrics.box.map),
        "precision": float(metrics.box.mp), "recall": float(metrics.box.mr),
    }
    (OUT / "train_metrics.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"Đã lưu model: {MODELS / 'extinguisher_best.pt'}")


if __name__ == "__main__":  # bắt buộc trên Windows khi dataloader dùng nhiều tiến trình
    main()
