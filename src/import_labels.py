"""Đọc phiếu chấm Excel người chấm gửi lại -> data/labels/raterX.csv (định dạng evaluate.py dùng)

    python src/import_labels.py
Báo các ô trống / giá trị lạ để hỏi lại người chấm.
"""
import pandas as pd

from common import CRITERIA, LABELS

ok = True
for xlsx in sorted(LABELS.glob("phieu_cham_rater*.xlsx")):
    r = xlsx.stem.replace("phieu_cham_", "")
    df = pd.read_excel(xlsx)
    df = df.rename(columns={df.columns[1]: "image", df.columns[-1]: "ghi_chu"})
    df.columns = ["STT", "image", *CRITERIA, "ghi_chu"]
    df = df.dropna(subset=["image"])
    order = pd.read_csv(LABELS / f"{r}.csv", encoding="utf-8-sig")["image"]
    # Tên ảnh trong phiếu luôn là .jpg (ảnh đã thu nhỏ); khôi phục tên gốc (vd v2b_11.png)
    stem2orig = {n.rsplit(".", 1)[0]: n for n in order}
    df["image"] = df["image"].astype(str).str.rsplit(".", n=1).str[0].map(stem2orig)
    problems = []
    if df["image"].isna().any() or len(df) != len(order):
        problems.append(f"số ảnh {len(df)} / {len(order)} hoặc tên ảnh lạ")
    for c in CRITERIA:
        v = pd.to_numeric(df[c], errors="coerce")
        bad = df.loc[~v.isin([0, 1]), "image"].tolist()
        if bad:
            problems.append(f"{c}: {len(bad)} ô trống/sai ({', '.join(bad[:5])}{'…' if len(bad) > 5 else ''})")
        df[c] = v.astype("Int64")
    out = df[["image", *CRITERIA, "ghi_chu"]]
    out.to_csv(LABELS / f"{r}.csv", index=False, encoding="utf-8-sig")
    n_note = out["ghi_chu"].notna().sum()
    print(f"{r}: {len(out)} ảnh, {n_note} ghi chú" + (" | LỖI: " + "; ".join(problems) if problems else " | đủ, hợp lệ"))
    print("   tỷ lệ vi phạm:", {c: int(out[c].sum()) for c in CRITERIA})
    ok &= not problems
print("OK" if ok else "Có lỗi, xem ở trên")
