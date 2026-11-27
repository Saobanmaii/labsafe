import json

import pandas as pd
import streamlit as st
from sklearn.metrics import cohen_kappa_score, f1_score

import ui
from core.config import PAPER_OUT, ROOT, camera_for_image, dataset_images
from core.evaluation import detect_dataset, majority_labels, metrics, predict_dataset
from core.render import load_image, to_rgb
from core.pipeline import analyze

c = ui.cfg()
Z = ui.zones()
ui.sidebar_status(c)

ui.header("Đánh giá mô hình", "So sánh kết quả hệ thống với 3 người chấm độc lập")
st.caption("Bộ thử nghiệm: 62 ảnh chụp tại phòng thí nghiệm điện tử, 6 góc camera, mỗi ảnh được 3 người ngoài nhóm "
           "chấm độc lập; nhãn chuẩn = nhãn đa số. Độ đo chính: Cohen's κ so với nhãn đa số.")

tab1, tab2, tab3 = st.tabs(["Đánh giá trực tiếp (bảng kiểm hiện tại)", "Kết quả trong báo cáo", "Mô hình tự huấn luyện"])

# ================================================================ trực tiếp
with tab1:
    gold = majority_labels()
    if gold is None:
        st.warning("Không tìm thấy data/labels/rater*.csv")
        st.stop()
    st.markdown("Chạy toàn bộ hệ thống YOLO + bộ luật với **bảng kiểm đang lưu**. Kết quả phát hiện được lưu đệm, "
                "nên sau khi đổi ngưỡng ở trang «Bảng kiểm» chỉ mất khoảng 1 giây để đánh giá lại.")
    if st.button("▶ Chạy đánh giá trên 62 ảnh", type="primary") or st.session_state.get("eval_done"):
        st.session_state.eval_done = True
        bar = st.progress(0.0, "Đang phát hiện đối tượng...")
        cache = detect_dataset(c, ui.detector(c), progress=lambda f, n: bar.progress(f, f"Phát hiện: {n}"))
        bar.empty()
        pred = predict_dataset(c, cache, Z)
        m = metrics(pred, gold)
        names = {x["id"]: x["name"] for x in c["criteria"]}
        grp = {x["id"]: c["groups"][x["group"]] for x in c["criteria"]}
        m.insert(1, "Tên", m["Tiêu chí"].map(names))
        m.insert(2, "Nhóm", m["Tiêu chí"].map(grp))

        paper = PAPER_OUT / "table_main.csv"
        if paper.exists():
            pm = pd.read_csv(paper, encoding="utf-8-sig")
            rule_p = pm[pm["Phương pháp"].str.startswith("Luật")].set_index("Tiêu chí")["κ"]
            vlm_p = pm[pm["Phương pháp"].str.contains("P1")].set_index("Tiêu chí")["κ"]
            m["κ bài báo (luật)"] = m["Tiêu chí"].map(rule_p)
            m["κ Gemini P1"] = m["Tiêu chí"].map(vlm_p)
        st.dataframe(m, hide_index=True, width="stretch",
                     column_config={"κ": st.column_config.ProgressColumn("κ (hiện tại)", min_value=0, max_value=1,
                                                                         format="%.2f")})
        inter = PAPER_OUT / "table_interrater.csv"
        if inter.exists():
            ir = pd.read_csv(inter, encoding="utf-8-sig")
            st.caption("Tham chiếu — độ đồng thuận giữa 3 người chấm (Fleiss κ): "
                       + " · ".join(f"{r['Tiêu chí'].split()[0]} {r['Fleiss κ']:.2f}" for _, r in ir.iterrows()))

        # theo nhóm tiêu chí
        st.markdown("**Theo nhóm tiêu chí** (gộp mọi quyết định đạt/vi phạm trong nhóm)")
        rows = []
        for gid, gname in c["groups"].items():
            ids = [x["id"] for x in c["criteria"] if x["group"] == gid and x["id"] in pred.columns and x["id"] in gold.columns]
            if not ids:
                continue
            pp = pd.DataFrame({"p": pd.concat([pred[i] for i in ids]).values,
                               "g": pd.concat([gold.loc[pred.index, i] for i in ids]).values}).dropna()
            rows.append({"Nhóm": gname, "Tiêu chí": ", ".join(ids), "Số quyết định": len(pp),
                         "Khớp": round((pp.p == pp.g).mean(), 3),
                         "κ": round(cohen_kappa_score(pp.g.astype(int), pp.p.astype(int)), 3),
                         "F1 (vi phạm)": round(f1_score(pp.g.astype(int), pp.p.astype(int)), 3)})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

        # chế độ kết hợp, dùng kết quả Gemini đã chạy cho bài báo (không tốn API)
        vf = PAPER_OUT / "results_vlm.csv"
        if vf.exists():
            vr = pd.read_csv(vf, encoding="utf-8-sig")
            vr = vr[(vr["prompt"] == "P1") & (vr["error"].isna() | (vr["error"] == ""))].drop_duplicates("image")
            vr = vr.set_index("image")
            hyb = pred.copy()
            for x in c["criteria"]:
                if x.get("hybrid_engine") == "vlm" and x["id"] in vr.columns:
                    hyb[x["id"]] = vr.reindex(hyb.index)[x["id"]]
            st.markdown("**Chế độ Kết hợp** — luật cho tiêu chí có `hybrid_engine: rules`, Gemini cho tiêu chí "
                        "`hybrid_engine: vlm` (dùng lại kết quả Gemini P1 đã chạy cho báo cáo, không tốn API)")
            hm = metrics(hyb, gold)
            hm.insert(1, "Dùng", hm["Tiêu chí"].map({x["id"]: "Gemini" if x.get("hybrid_engine") == "vlm" else "Luật"
                                                       for x in c["criteria"]}))
            st.dataframe(hm, hide_index=True, width="stretch")

        # ảnh sai
        ui.section("Các ảnh hệ thống chấm khác người chấm")
        crit_ids = [i for i in pred.columns if i in gold.columns]
        wrong = []
        for img_name in pred.index:
            for i in crit_ids:
                pv, gv = pred.loc[img_name, i], gold.loc[img_name, i]
                if pd.notna(pv) and int(pv) != int(gv):
                    wrong.append({"Ảnh": img_name, "Tiêu chí": i, "Hệ thống": "VI PHẠM" if pv else "ĐẠT",
                                  "Người chấm": "VI PHẠM" if gv else "ĐẠT",
                                  "Loại lỗi": "Báo nhầm (FP)" if pv else "Bỏ sót (FN)"})
        wdf = pd.DataFrame(wrong)
        if wdf.empty:
            st.success("Không có ảnh sai!")
        else:
            a, b = st.columns([2, 3])
            with a:
                sel = st.dataframe(wdf, hide_index=True, width="stretch", on_select="rerun",
                                   selection_mode="single-row", height=420)
            with b:
                r = sel.selection.rows if sel else []
                if r:
                    name = wdf.iloc[r[0]]["Ảnh"]
                    path = next(p for p in dataset_images() if p.name == name)
                    img = load_image(path)
                    item = cache[name]
                    an = analyze(img, camera_for_image(name, Z), Z, c, ui.detector(c),
                                 dets=[dict(d, xyxy=tuple(d["xyxy"])) for d in item["dets"]])
                    st.image(to_rgb(ui.evidence_image(an, img, c)), width="stretch", caption=name)
                    for res in an.results:
                        if res.id == wdf.iloc[r[0]]["Tiêu chí"]:
                            st.write(f"**{res.id}:** {res.explanation}")
                else:
                    st.info("Chọn một dòng để xem ảnh bằng chứng.")
        st.download_button("⬇️ Tải dự đoán (CSV)", pred.to_csv().encode("utf-8-sig"), "du_doan_62_anh.csv")

# ================================================================ báo cáo
with tab2:
    tm = PAPER_OUT / "table_main.csv"
    if tm.exists():
        st.markdown("**So sánh YOLO + luật và Gemini với người chấm** (từ `outputs/table_main.csv`)")
        st.dataframe(pd.read_csv(tm, encoding="utf-8-sig"), hide_index=True, width="stretch")
    a, b = st.columns(2)
    if (PAPER_OUT / "fig_kappa.png").exists():
        a.image(str(PAPER_OUT / "fig_kappa.png"), caption="κ theo tiêu chí", width="stretch")
    if (PAPER_OUT / "fig_detector_compare.png").exists():
        b.image(str(PAPER_OUT / "fig_detector_compare.png"),
                caption="COCO và YOLO-World không thấy bình chữa cháy; mô hình tự huấn luyện thấy (0,94)", width="stretch")
    st.markdown("""
**Nhận xét chính**
- **YOLO + luật** tốt hơn ở tiêu chí phụ thuộc **vị trí** (C1 lối đi, C3 bình chữa cháy) nhờ có vùng chức năng.
- **Gemini** tốt hơn ở tiêu chí phụ thuộc **loại đồ vật** (C2, C4) vì nhận biết được vật ngoài 80 lớp COCO.
- → Sản phẩm có chế độ **Kết hợp** lấy phần mạnh của mỗi hướng, và bước **lọc chai trên bình** sửa lỗi lớn nhất của C4.
- Tốc độ: YOLO + luật ~0,13 s/ảnh offline (GPU MX350); Gemini ~10 s/ảnh, cần mạng, có hạn mức.
""")

# ================================================================ mô hình tự huấn luyện
with tab3:
    tmf = PAPER_OUT / "train_metrics.json"
    if tmf.exists():
        t = json.loads(tmf.read_text())
        k = st.columns(4)
        k[0].metric("mAP@0,5", f"{t['mAP50']:.3f}")
        k[1].metric("mAP@0,5:0,95", f"{t['mAP50_95']:.3f}")
        k[2].metric("Precision", f"{t['precision']:.3f}")
        k[3].metric("Recall", f"{t['recall']:.3f}")
        st.caption(f"YOLO11n tinh chỉnh từ {t['base_model']}, ảnh {t['imgsz']}, dữ liệu Fire-ART (358 ảnh, "
                   "chỉ lớp bình chữa cháy), GPU NVIDIA MX350 2 GB.")
    val = ROOT / "runs" / "detect" / "val"
    figs = [("BoxPR_curve.png", "Đường Precision–Recall"), ("confusion_matrix_normalized.png", "Ma trận nhầm lẫn"),
            ("BoxF1_curve.png", "F1 theo ngưỡng"), ("val_batch0_pred.jpg", "Dự đoán trên tập kiểm định")]
    cols = st.columns(2)
    for k, (f, cap) in enumerate(figs):
        if (val / f).exists():
            cols[k % 2].image(str(val / f), caption=cap, width="stretch")
