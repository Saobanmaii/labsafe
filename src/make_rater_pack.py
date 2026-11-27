"""Đóng gói bộ chấm cho từng người chấm -> share/cham_diem_raterX.zip

Mỗi gói gồm: HUONG_DAN_CHAM.html, phieu_cham_raterX.xlsx (ô chọn 0/1, bấm tên ảnh để mở ảnh),
images/ (ảnh thu nhỏ), anh_tham_khao/ (vị trí bình chữa cháy của từng góc chụp).
KHÔNG đưa photo_map.csv / raw_photos vào gói.

    python src/make_rater_pack.py
"""
import shutil
import zipfile
from pathlib import Path

import cv2
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from PIL import Image, ImageOps

from common import CRITERIA, IMAGES, LABELS, MODELS, ROOT, list_images, load_image_bgr, save_image_bgr, view_of

SHARE = ROOT / "share"
BUILD = SHARE / "_build_rater"
GUIDE = Path(__file__).with_name("rater_guide.html")
MAX_SIDE = 1800
VIEW_NAMES = {"v1": "Góc 1", "v2a": "Góc 2 (cao)", "v2b": "Góc 2 (ngang)", "v2c": "Góc 2 (thấp)",
              "v3a": "Góc 3 (cao)", "v3b": "Góc 3 (thấp)"}
HEAD = {"C1": "C1 Vật cản lối đi", "C2": "C2 Đồ cá nhân trên bàn (≥3)",
        "C3": "C3 Bình chữa cháy bị che", "C4": "C4 Đồ ăn / uống"}


def build_images(dst):
    dst.mkdir(parents=True, exist_ok=True)
    for p in list_images():
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        im.thumbnail((MAX_SIDE, MAX_SIDE))
        im.save(dst / (p.stem + ".jpg"), quality=88)


def build_reference(dst):
    """Mỗi góc chụp: lấy ảnh có bình chữa cháy được phát hiện chắc nhất, khoanh đỏ vị trí bình."""
    from ultralytics import YOLO
    model = YOLO(str(MODELS / "extinguisher_best.pt"))
    dst.mkdir(parents=True, exist_ok=True)
    best = {}
    for p in list_images():
        r = model.predict(load_image_bgr(p), conf=0.4, verbose=False)[0]
        for xyxy, s in zip(r.boxes.xyxy.tolist(), r.boxes.conf.tolist()):
            v = view_of(p.name)
            if s > best.get(v, (0,))[0]:
                best[v] = (s, p, xyxy)
    for v, (s, p, (x1, y1, x2, y2)) in sorted(best.items()):
        img = load_image_bgr(p)
        h, w = img.shape[:2]
        t = max(4, w // 250)
        pad = int(0.15 * max(x2 - x1, y2 - y1))
        cv2.rectangle(img, (int(x1) - pad, int(y1) - pad), (int(x2) + pad, int(y2) + pad), (0, 0, 255), t)
        f = h / 1100
        cv2.putText(img, "BINH CHUA CHAY", (int(x1) - pad, max(30, int(y1) - pad - 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, f, (0, 0, 255), max(2, t // 2))
        s_ = MAX_SIDE / max(h, w)
        img = cv2.resize(img, (int(w * s_), int(h * s_)), interpolation=cv2.INTER_AREA)
        save_image_bgr(dst / f"{v}.jpg", img)
        print(f"  tham khảo {v}: {p.name} (conf {s:.2f})")
    missing = sorted({view_of(p.name) for p in list_images()} - set(best))
    if missing:
        print(f"[!] Không tìm được bình ở góc: {missing} -> kiểm tra tay")
    return missing


def build_sheet(rater_csv, dst):
    order = pd.read_csv(rater_csv, encoding="utf-8-sig")["image"].tolist()
    wb = Workbook()
    ws = wb.active
    ws.title = "Phieu cham"
    ws.append(["STT", "Ảnh (bấm để mở)"] + [HEAD[c] for c in CRITERIA] + ["Ghi chú (nếu phân vân)"])
    for i, name in enumerate(order, 1):
        ws.append([i, Path(name).stem + ".jpg", None, None, None, None, None])
        cell = ws.cell(row=i + 1, column=2)
        cell.hyperlink = f"images/{Path(name).stem}.jpg"
        cell.font = Font(color="0563C1", underline="single")
    dv = DataValidation(type="list", formula1='"0,1"', allow_blank=True, showErrorMessage=True,
                        errorTitle="Chỉ nhập 0 hoặc 1", error="0 = Đạt, 1 = Vi phạm")
    ws.add_data_validation(dv)
    dv.add(f"C2:F{len(order) + 1}")
    head_fill = PatternFill("solid", fgColor="DDEBF7")
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = head_fill
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    for col, wd in zip("ABCDEFG", [6, 16, 14, 16, 16, 14, 45]):
        ws.column_dimensions[col].width = wd
    for row in ws.iter_rows(min_row=2, min_col=3, max_col=6):
        for c in row:
            c.alignment = Alignment(horizontal="center")
    ws.row_dimensions[1].height = 36
    ws.freeze_panes = "C2"
    wb.save(dst)


def main():
    if BUILD.exists():
        shutil.rmtree(BUILD)
    common = BUILD / "common"
    print("Thu nhỏ ảnh...")
    build_images(common / "images")
    print("Tạo ảnh tham khảo vị trí bình chữa cháy...")
    build_reference(common / "anh_tham_khao")
    for rater_csv in sorted(LABELS.glob("rater*.csv")):
        r = rater_csv.stem
        sheet = BUILD / f"phieu_cham_{r}.xlsx"
        build_sheet(rater_csv, sheet)
        out = SHARE / f"cham_diem_{r}.zip"
        root = f"cham_diem_{r}"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(GUIDE, f"{root}/HUONG_DAN_CHAM.html")
            z.write(sheet, f"{root}/phieu_cham_{r}.xlsx")
            for f in sorted(common.rglob("*.jpg")):
                z.write(f, f"{root}/{f.relative_to(common).as_posix()}")
        print(f"-> {out} ({out.stat().st_size / 1e6:.1f} MB)")
    shutil.rmtree(BUILD)


if __name__ == "__main__":
    main()
