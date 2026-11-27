"""LabSafe — Đánh giá điều kiện gọn gàng, vệ sinh và an toàn trong phòng thí nghiệm.

    streamlit run app/main.py        (hoặc nháy đúp run_demo.bat)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402

import theme  # noqa: E402

st.set_page_config(page_title="LabSafe — An toàn phòng thí nghiệm", page_icon=str(theme.ASSETS / "icon.svg"),
                   layout="wide")
theme.apply()

P = Path(__file__).resolve().parent / "pages"
nav = st.navigation({
    "Giám sát": [
        st.Page(P / "home.py", title="Tổng quan", icon=":material/grid_view:", default=True),
        st.Page(P / "analyze.py", title="Phân tích ảnh", icon=":material/image_search:"),
        st.Page(P / "video.py", title="Video & camera", icon=":material/videocam:"),
        st.Page(P / "events.py", title="Nhật ký sự kiện", icon=":material/notifications_active:"),
    ],
    "Cấu hình": [
        st.Page(P / "checklist.py", title="Bảng kiểm", icon=":material/fact_check:"),
        st.Page(P / "zones.py", title="Vùng camera", icon=":material/polyline:"),
    ],
    "Báo cáo": [
        st.Page(P / "evaluation.py", title="Đánh giá mô hình", icon=":material/monitoring:"),
    ],
})
nav.run()
