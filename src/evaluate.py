"""Đối chiếu 3 cột: người chấm (đáp án chuẩn) vs hệ thống luật vs VLM -> bảng + hình cho bài báo.

    python src/evaluate.py
    python src/evaluate.py --labels data/demo/labels --rule data/demo/results_rule.csv --vlm data/demo/results_vlm.csv --out outputs/demo

Đầu ra (thư mục --out):
    table_interrater.csv/.tex   độ đồng thuận giữa người chấm (Fleiss' kappa, tỷ lệ khớp)
    table_main.csv/.tex         độ khớp, Cohen's kappa [CI 95%], F1 của từng phương pháp so với nhãn đa số
    table_prompt.csv/.tex       độ ổn định của VLM khi đổi prompt
    table_data.csv              số ca vi phạm mỗi tiêu chí (theo nhãn đa số)
    errors.csv                  mọi ca máy chấm khác người -> chọn ca để phân tích
    fig_kappa.png/.pdf          biểu đồ kappa theo tiêu chí
"""
import argparse
from itertools import combinations
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, f1_score

from common import CRITERIA, CRITERIA_NAMES, LABELS, OUT

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--labels", default=str(LABELS))
ap.add_argument("--rule", default=str(OUT / "results_rule.csv"))
ap.add_argument("--vlm", default=str(OUT / "results_vlm.csv"))
ap.add_argument("--out", default=str(OUT))
ap.add_argument("--boot", type=int, default=2000)
args = ap.parse_args()
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(0)


# ---------------------------------------------------------------- thống kê
def fleiss_kappa(mat: np.ndarray) -> float:
    """mat: (số ảnh, số người chấm) nhãn 0/1. Fleiss (1971)."""
    n_items, n_raters = mat.shape
    counts = np.stack([(mat == k).sum(1) for k in (0, 1)], axis=1)
    p_i = ((counts ** 2).sum(1) - n_raters) / (n_raters * (n_raters - 1))
    p_bar = p_i.mean()
    p_j = counts.sum(0) / (n_items * n_raters)
    p_e = (p_j ** 2).sum()
    return float("nan") if p_e == 1 else float((p_bar - p_e) / (1 - p_e))


def kappa(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    if len(set(a) | set(b)) < 2:
        return float("nan")  # cả hai đều hằng và trùng nhau -> kappa không xác định
    return float(cohen_kappa_score(a, b))


def boot_ci(a, b, fn=kappa):
    a, b = np.asarray(a), np.asarray(b)
    vals = []
    for _ in range(args.boot):
        idx = rng.integers(0, len(a), len(a))
        v = fn(a[idx], b[idx])
        if not np.isnan(v):
            vals.append(v)
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) if vals else (np.nan, np.nan)


def fmt(x, nd=2):
    return "–" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


def to_latex(df: pd.DataFrame, path: Path, caption: str):
    cols = list(df.columns)
    lines = [r"\begin{table}[t]", r"\centering", rf"\caption{{{caption}}}", r"\footnotesize",
             r"\begin{tabular}{" + "l" * len(cols) + "}", r"\hline",
             " & ".join(cols) + r" \\", r"\hline"]
    lines += [" & ".join(str(v) for v in row) + r" \\" for row in df.itertuples(index=False)]
    lines += [r"\hline", r"\end{tabular}", r"\end{table}"]
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------- người chấm
rater_files = sorted(Path(args.labels).glob("rater*.csv"))
assert len(rater_files) >= 2, f"Cần ít nhất 2 file rater*.csv trong {args.labels}"
raters = {}
for f in rater_files:
    d = pd.read_csv(f, sep=None, engine="python", encoding="utf-8-sig", dtype={"image": str})
    d.columns = [c.strip() for c in d.columns]
    missing = d[CRITERIA].isna().any(axis=1)
    if missing.any():
        print(f"[!] {f.name}: {missing.sum()} ảnh chưa chấm đủ -> bỏ qua các ảnh đó")
    d = d[~missing]
    raters[f.stem] = d.set_index("image")[CRITERIA].astype(int)
common_imgs = sorted(set.intersection(*(set(r.index) for r in raters.values())))
R = {k: v.loc[common_imgs] for k, v in raters.items()}
print(f"{len(R)} người chấm, {len(common_imgs)} ảnh chung")

# nhãn đa số; số người chẵn mà hoà -> bỏ ảnh đó khỏi so sánh với máy
gt = {}
for c in CRITERIA:
    m = np.mean([R[k][c].values for k in R], axis=0)
    gt[c] = pd.Series(np.where(m > 0.5, 1, np.where(m < 0.5, 0, -1)), index=common_imgs)

rows = []
for c in CRITERIA:
    mat = np.stack([R[k][c].values for k in R], axis=1)
    pair_agree = np.mean([np.mean(R[a][c].values == R[b][c].values) for a, b in combinations(R, 2)])
    pair_kappa = np.nanmean([kappa(R[a][c], R[b][c]) for a, b in combinations(R, 2)])
    rows.append({"Tiêu chí": f"{c} {CRITERIA_NAMES[c]}", "Fleiss κ": fmt(fleiss_kappa(mat)),
                 "Cohen κ TB cặp": fmt(pair_kappa), "Khớp TB cặp": fmt(pair_agree),
                 "Khớp cả nhóm": fmt(np.mean((mat == mat[:, :1]).all(1))),
                 "_fleiss": fleiss_kappa(mat)})
inter = pd.DataFrame(rows)
inter.drop(columns="_fleiss").to_csv(out / "table_interrater.csv", index=False, encoding="utf-8-sig")
to_latex(inter.drop(columns="_fleiss"), out / "table_interrater.tex", "Độ đồng thuận giữa những người chấm")

data_rows = [{"Tiêu chí": f"{c} {CRITERIA_NAMES[c]}", "Vi phạm": int((gt[c] == 1).sum()),
              "Đạt": int((gt[c] == 0).sum()), "Hoà (bỏ)": int((gt[c] == -1).sum())} for c in CRITERIA]
pd.DataFrame(data_rows).to_csv(out / "table_data.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- các phương pháp máy
systems = {}  # tên -> DataFrame index=image, cột C1..C4
rule_df = None
if Path(args.rule).exists():
    rule_df = pd.read_csv(args.rule, encoding="utf-8-sig").set_index("image")
    systems["Luật (YOLO)"] = rule_df[CRITERIA]
vlm_df = None
if Path(args.vlm).exists():
    vlm_df = pd.read_csv(args.vlm, encoding="utf-8-sig", dtype={"error": str})
    vlm_df = vlm_df[vlm_df["error"].isna() | (vlm_df["error"] == "")]
    vlm_df = vlm_df.drop_duplicates(["image", "model", "prompt", "run"], keep="last")
    for (model, prompt), g in vlm_df.groupby(["model", "prompt"]):
        # nhiều lần chạy -> lấy đa số
        agg = g.groupby("image")[CRITERIA].mean().round().astype(int)
        systems[f"VLM {prompt} ({model})"] = agg

main_rows, err_rows, plot = [], [], {}
for name, S in systems.items():
    for c in CRITERIA:
        y = gt[c][gt[c] >= 0]
        s = S[c].dropna() if c in S else pd.Series(dtype=float)
        imgs = sorted(set(y.index) & set(s.index))
        if not imgs:
            continue
        a, b = y.loc[imgs].values, s.loc[imgs].astype(int).values
        k, (lo, hi) = kappa(a, b), boot_ci(a, b)
        main_rows.append({"Phương pháp": name, "Tiêu chí": c, "n": len(imgs), "Khớp": fmt(np.mean(a == b)),
                          "κ": fmt(k), "CI 95%": f"[{fmt(lo)}, {fmt(hi)}]",
                          "F1 (vi phạm)": fmt(f1_score(a, b, zero_division=0)),
                          "TP": int(((a == 1) & (b == 1)).sum()), "FP": int(((a == 0) & (b == 1)).sum()),
                          "FN": int(((a == 1) & (b == 0)).sum()), "TN": int(((a == 0) & (b == 0)).sum())})
        plot[(name, c)] = (k, lo, hi)
        for img, ai, bi in zip(imgs, a, b):
            if ai != bi:
                err_rows.append({"image": img, "Tiêu chí": c, "Phương pháp": name, "Người (đa số)": int(ai),
                                 "Máy": int(bi), "Loại lỗi": "FP (báo động giả)" if bi else "FN (bỏ sót)"})

main = pd.DataFrame(main_rows)
main.to_csv(out / "table_main.csv", index=False, encoding="utf-8-sig")
if len(main):
    wide = main.assign(cell=main["Khớp"] + " / " + main["κ"]).pivot(index="Phương pháp", columns="Tiêu chí", values="cell")
    to_latex(wide.reset_index(), out / "table_main.tex", r"Độ khớp / Cohen's $\kappa$ so với nhãn đa số của người chấm")

errors = pd.DataFrame(err_rows)
if len(errors) and rule_df is not None:
    diag = [c for c in ["R_aisle", "n_personal", "ext_visible", "ext_occluded", "food_labels"] if c in rule_df]
    errors = errors.merge(rule_df[diag], left_on="image", right_index=True, how="left")
if len(errors) and vlm_df is not None:
    reasons = vlm_df[vlm_df["prompt"] == "P1"].drop_duplicates("image").set_index("image")["reason"]
    errors["Lý do VLM (P1)"] = errors["image"].map(reasons)
errors.to_csv(out / "errors.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- độ ổn định theo prompt
if vlm_df is not None and len(vlm_df):
    prow = []
    for model, g in vlm_df[vlm_df["run"] == 0].groupby("model"):
        piv = {c: g.pivot_table(index="image", columns="prompt", values=c) for c in CRITERIA}
        for c in CRITERIA:
            m = piv[c].dropna()
            if m.shape[1] < 2:
                continue
            accs = [np.mean(m[p].values == gt[c].reindex(m.index).values) for p in m.columns]
            prow.append({"Model": model, "Tiêu chí": c, "Số prompt": m.shape[1],
                         "Ảnh 3 prompt đồng nhất": fmt(np.mean((m.values == m.values[:, :1]).all(1))),
                         "Fleiss κ giữa prompt": fmt(fleiss_kappa(m.values.astype(int))),
                         "Độ khớp min–max": f"{fmt(min(accs))}–{fmt(max(accs))}",
                         "Biên độ": fmt(max(accs) - min(accs))})
    ptab = pd.DataFrame(prow)
    ptab.to_csv(out / "table_prompt.csv", index=False, encoding="utf-8-sig")
    if len(ptab):
        to_latex(ptab, out / "table_prompt.tex", "Độ ổn định của VLM khi thay đổi prompt")

# ---------------------------------------------------------------- hình: kappa theo tiêu chí
# Màu phân loại theo thứ tự cố định + hoa văn để đọc được khi in đen trắng.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
HATCH = ["", "//", "\\\\", "xx", "..", "--", "++", "oo"]
names = list(systems)
if names:
    fig, ax = plt.subplots(figsize=(3.5, 2.6), dpi=300)  # vừa một cột IEEE
    x = np.arange(len(CRITERIA))
    width = 0.8 / len(names)
    for i, name in enumerate(names):
        ks = [plot.get((name, c), (np.nan,) * 3) for c in CRITERIA]
        k = np.array([v[0] for v in ks], dtype=float)
        err = np.array([[v[0] - v[1], v[2] - v[0]] for v in ks], dtype=float).T
        pos = x - 0.4 + width * (i + 0.5)
        ax.bar(pos, np.nan_to_num(k), width * 0.9, color=PALETTE[i % 8], hatch=HATCH[i % 8],
               edgecolor="white", linewidth=0.4, label=name, zorder=2)
        ax.errorbar(pos, np.nan_to_num(k), yerr=np.nan_to_num(err), fmt="none", ecolor="#52514e",
                    elinewidth=0.6, capsize=1.5, zorder=3)
    ax.scatter(x, inter["_fleiss"].values, marker="D", s=14, color="#0b0b0b", zorder=4,
               label="Đồng thuận người chấm (Fleiss κ)")
    short = {"C1": "Lối đi", "C2": "Đồ cá nhân", "C3": "Bình chữa cháy", "C4": "Đồ ăn/uống"}
    ax.set_xticks(x, [f"{c}\n{short[c]}" for c in CRITERIA], fontsize=5.5)
    ax.set_ylabel("Cohen's κ so với người", fontsize=6.5)
    ax.set_ylim(min(-0.2, ax.get_ylim()[0]), 1.0)
    ax.axhline(0, color="#52514e", linewidth=0.5)
    ax.tick_params(axis="y", labelsize=6)
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.4, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(fontsize=4.8, frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.28))
    fig.tight_layout()
    fig.savefig(out / "fig_kappa.png", bbox_inches="tight")
    fig.savefig(out / "fig_kappa.pdf", bbox_inches="tight")

# ---------------------------------------------------------------- tóm tắt
print("\n=== Đồng thuận giữa người chấm ===")
print(inter.drop(columns="_fleiss").to_string(index=False))
print("\n=== Số ca theo nhãn đa số ===")
print(pd.DataFrame(data_rows).to_string(index=False))
if len(main):
    print("\n=== Kết quả chính ===")
    print(main[["Phương pháp", "Tiêu chí", "n", "Khớp", "κ", "CI 95%", "F1 (vi phạm)"]].to_string(index=False))
print(f"\nĐã ghi bảng và hình vào {out}")
