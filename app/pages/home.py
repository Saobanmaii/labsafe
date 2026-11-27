import pandas as pd
import streamlit as st

import ui

c = ui.cfg()
ui.sidebar_status(c)

ui.header("Tổng quan", "Đánh giá điều kiện gọn gàng, vệ sinh và an toàn trong phòng thí nghiệm")
st.caption("Đề tài CVFP26BCPPRJC025 · Môn Thị giác máy tính · Nhóm: Trần Tuấn Kiệt, Lành Diệu Hương, Lê Quốc Dũng")

# ---------------------------------------------------------------- số liệu nhanh
df = ui.store().df()
today = df[df["started_at"].dt.date == pd.Timestamp.now().date()] if len(df) else df
k = st.columns(4)
k[0].metric("Sự kiện vi phạm hôm nay", len(today))
k[1].metric("Đang mở (chưa hết vi phạm)", int((df["status"] == "open").sum()) if len(df) else 0)
k[2].metric("Chưa xác nhận xử lý", int((df["ack"] == 0).sum()) if len(df) else 0)
k[3].metric("Tổng sự kiện đã ghi", len(df))

st.divider()
left, right = st.columns([3, 2])
with left:
    ui.section("Hệ thống hoạt động thế nào")
    st.graphviz_chart("""
digraph G {
  rankdir=LR; bgcolor="transparent";
  node [shape=box, style="rounded,filled", fillcolor="#f2f4f8", color="#9aa4b2", fontname="Arial", fontsize=11];
  edge [color="#7a8594", fontname="Arial", fontsize=9];
  src [label="Ảnh / Video /\\nWebcam / Camera IP", fillcolor="#e8f1ff"];
  subgraph cluster_det { label="Phát hiện đối tượng"; fontname="Arial"; fontsize=10; color="#c9d2de"; style=rounded;
    coco [label="YOLO11s (COCO)\\nghế, balo, cốc, chai..."];
    ext  [label="YOLO11n tự huấn luyện\\nbình chữa cháy", fillcolor="#fff3d6"];
    wld  [label="YOLO-World\\nlớp từ vựng mở"];
  }
  pp   [label="Hậu xử lý\\n(lọc chai trùng bình)"];
  zone [label="Vùng camera\\nlối đi · bàn · bình", fillcolor="#eaf7ea"];
  rule [label="Bộ luật theo vùng\\n(bảng kiểm YAML)", fillcolor="#eaf7ea"];
  vlm  [label="Gemini (tuỳ chọn)\\nchấm + khoanh bằng chứng"];
  out  [label="Kết luận từng tiêu chí\\nđiểm theo nhóm\\nảnh bằng chứng", fillcolor="#ffe9e9"];
  tf   [label="Lọc theo thời gian\\n(video)"];
  ev   [label="Nhật ký sự kiện\\nảnh đã làm mờ người\\ncảnh báo", fillcolor="#ffe9e9"];
  src -> coco; src -> ext; src -> wld; coco -> pp; ext -> pp; wld -> pp; pp -> rule; zone -> rule;
  src -> vlm [style=dashed]; rule -> out; vlm -> out [style=dashed]; out -> tf -> ev;
}
""", width="stretch")
with right:
    ui.section("Bảng kiểm đang áp dụng")
    sev = {k: v["name"] for k, v in c["severity"].items()}
    st.dataframe(pd.DataFrame([{
        "Mã": x["id"], "Tiêu chí": x["name"], "Nhóm": c["groups"][x["group"]],
        "Mức độ": sev[x["severity"]], "Bật": "✅" if x.get("enabled", True) else "—"} for x in c["criteria"]]),
        hide_index=True, width="stretch")
    st.page_link("pages/checklist.py", label="Chỉnh bảng kiểm", icon="✅")

st.divider()
ui.section("Đối chiếu với yêu cầu đề tài")
st.dataframe(pd.DataFrame([
    ("Baseline", "Demo cơ bản, có thể dùng API", "Trang «Phân tích ảnh»: chế độ YOLO + luật, Gemini API, hoặc kết hợp"),
    ("Extended 1", "Customized model", "YOLO11n tự huấn luyện phát hiện bình chữa cháy (mAP@0,5 = 0,80)"),
    ("Extended 1", "Dữ liệu đầy đủ, đánh giá so sánh", "62 ảnh thực tế × 3 người chấm; trang «Đánh giá mô hình»: κ, F1 cho từng hướng"),
    ("Extended 2", "Sản phẩm full flow, demo thực tế", "Ảnh/video/webcam/camera IP → phát hiện → luật → sự kiện → cảnh báo → nhật ký"),
    ("Extended 3", "Bảng kiểm cấu hình được", "Trang «Bảng kiểm»: bật/tắt, sửa ngưỡng, lớp đối tượng, thêm tiêu chí mới (YAML)"),
    ("Extended 3", "Cảnh báo theo vùng nguy cơ", "Trang «Vùng camera»: vẽ vùng; vi phạm khoanh đỏ đúng vùng, cảnh báo âm thanh/Telegram"),
    ("Extended 3", "Ghi nhận sự kiện kèm ảnh ẩn danh", "Trang «Nhật ký sự kiện»: SQLite + ảnh bằng chứng đã làm mờ người"),
    ("Extended 3", "Đánh giá riêng từng nhóm tiêu chí", "Điểm theo nhóm Bố trí / Vệ sinh / An toàn; κ riêng từng tiêu chí"),
], columns=["Mức", "Yêu cầu", "Đáp ứng trong sản phẩm"]), hide_index=True, width="stretch")

ui.section("Kịch bản demo gợi ý")
st.markdown("""
1. **Phân tích ảnh** → chọn ảnh mẫu `v2c_…`, xem điểm, vùng bằng chứng, so với nhãn người chấm; bật chế độ *Kết hợp* để Gemini chấm cùng.
2. **Bảng kiểm** → hạ ngưỡng C2 từ 3 xuống 2 đồ cá nhân, lưu → quay lại ảnh cũ thấy kết luận đổi.
3. **Vùng camera** → tạo camera mới từ webcam, vẽ lối đi / bàn / vị trí bình.
4. **Video & camera** → chạy video mẫu hoặc webcam; sự kiện chỉ ghi khi vi phạm kéo dài nhiều khung, có cảnh báo.
5. **Nhật ký sự kiện** → lọc, xem ảnh đã làm mờ người, xác nhận đã xử lý, xuất CSV.
6. **Đánh giá mô hình** → κ so với người chấm, chạy lại đánh giá với bảng kiểm vừa sửa.
""")
