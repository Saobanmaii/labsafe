"""BƯỚC 3 — Huấn luyện mô hình LabSafe-6 (học chuyển giao từ YOLO11 đã học trên COCO).

    python app/train/train.py                       # YOLO11n, 40 epoch (GPU MX350: vài giờ)
    python app/train/train.py --model yolo11s.pt --epochs 60
Kết quả: models/labsafe6_best.pt  +  outputs/train_labsafe6.json  +  runs/labsafe6/<lần chạy>/ (biểu đồ)
"""
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path("D:/Study/datasets/labsafe_6cls/data.yaml")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="yolo11n.pt", help="trọng số khởi đầu (COCO)")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=8, help="GPU 2 GB: 8 với yolo11n, 4 với yolo11s")
    ap.add_argument("--patience", type=int, default=10, help="dừng sớm nếu kiểm định không cải thiện")
    ap.add_argument("--name", default="run")
    ap.add_argument("--data", default=str(DATA), help="đường dẫn data.yaml")
    ap.add_argument("--out", default="labsafe6_best.pt", help="tên file trọng số lưu vào models/")
    args = ap.parse_args()

    import torch
    from ultralytics import YOLO

    start = ROOT / args.model if (ROOT / args.model).exists() else args.model
    model = YOLO(str(start))
    model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch, patience=args.patience,
                device=0 if torch.cuda.is_available() else "cpu", workers=2, seed=0,
                project=str(ROOT / "runs" / "labsafe6"), name=args.name, exist_ok=True, plots=True)

    run_dir = ROOT / "runs" / "labsafe6" / args.name
    best = run_dir / "weights" / "best.pt"
    (ROOT / "models").mkdir(exist_ok=True)
    shutil.copy(best, ROOT / "models" / args.out)

    m = YOLO(str(best)).val(data=args.data, imgsz=args.imgsz, batch=args.batch, plots=False, verbose=False)
    names = m.names
    per_class = {names[int(c)]: round(float(ap50), 3) for c, ap50 in zip(m.box.ap_class_index, m.box.ap50)}
    out = {"base_model": args.model, "epochs": args.epochs, "imgsz": args.imgsz,
           "mAP50": round(float(m.box.map50), 3), "mAP50_95": round(float(m.box.map), 3),
           "precision": round(float(m.box.mp), 3), "recall": round(float(m.box.mr), 3),
           "AP50_per_class": per_class, "run_dir": str(run_dir)}
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / f"train_{Path(args.out).stem}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nĐã lưu models/{args.out}. Bước tiếp: python app/train/compare.py --model models/{args.out}")


if __name__ == "__main__":  # bắt buộc trên Windows khi workers > 0
    main()
