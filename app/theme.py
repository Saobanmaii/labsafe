"""Giao diện LabSafe: sidebar đỏ, khung nội dung xám nhạt bo góc, thẻ trắng, nút viền đỏ.

apply()        — gọi một lần mỗi lượt chạy (main.py)
page_header()  — tiêu đề trang + chuông cảnh báo + người dùng
section()      — tiêu đề mục có vạch đỏ bên trái
"""
from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

RED = "#C0171E"
RED_DARK = "#8E0F14"
PINK = "#FBE1E3"
ASSETS = Path(__file__).resolve().parent / "assets"

CSS = f"""
<style>
/* ---------- khung tổng ---------- */
[data-testid="stAppViewContainer"] {{ background: {RED}; }}
[data-testid="stMain"] {{
  background: #F3F4F6; border-top-left-radius: 34px; border-bottom-left-radius: 34px;
  min-height: 100vh;
}}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stMainBlockContainer"] {{ padding-top: 1.6rem; max-width: 1500px; }}

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {{ background: {RED}; overflow: hidden; }}
section[data-testid="stSidebar"]::before {{
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 58%; pointer-events: none; z-index: 0;
  background:
    radial-gradient(circle at -55% 125%, {RED_DARK} 0 40%, transparent 40.4%),
    radial-gradient(circle at -48% 118%, #F2B8BC 0 50%, transparent 50.4%),
    radial-gradient(circle at -40% 110%, #D2343B 0 61%, transparent 61.4%);
  opacity: .95;
}}
section[data-testid="stSidebar"] > div {{ position: relative; z-index: 1; }}
[data-testid="stSidebarHeader"] {{ padding: 1.2rem 1.2rem .6rem; }}
img[data-testid="stSidebarLogo"] {{ height: 3.3rem !important; max-height: none !important; width: auto !important; max-width: 100% !important; }}
[data-testid="stLogoLink"] {{ height: auto !important; }}
[data-testid="stNavSectionHeader"] {{
  color: rgba(255,255,255,.72) !important; text-transform: uppercase; letter-spacing: .06em;
  font-size: .72rem !important; font-weight: 600; margin-top: .6rem;
}}
[data-testid="stSidebarNavLink"] {{
  border-radius: 10px; padding: .55rem .8rem !important; margin: .12rem .2rem;
}}
[data-testid="stSidebarNavLink"] span {{ color: #fff !important; font-weight: 600; font-size: 1rem; }}
[data-testid="stSidebarNavLink"]:hover {{ background: rgba(255,255,255,.14) !important; }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{ background: {PINK} !important; }}
[data-testid="stSidebarNavLink"][aria-current="page"] span {{ color: {RED} !important; }}
section[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.25); }}
.ls-side-status {{ background: rgba(0,0,0,.14); border-radius: 12px; padding: .8rem .9rem; font-size: .85rem; line-height: 1.7; }}
.ls-side-status b {{ font-weight: 700; }}

/* ---------- tiêu đề trang ---------- */
.ls-header {{
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  border-bottom: 1px solid #E3E5E9; padding: .2rem 0 1.1rem; margin-bottom: 1.4rem;
}}
.ls-header h1 {{ font-size: 1.9rem; font-weight: 700; margin: 0; padding: 0; color: #1F2430; line-height: 1.25; }}
.ls-header .sub {{ color: #6B7280; font-size: .92rem; margin-top: .25rem; }}
.ls-user {{ display: flex; align-items: center; gap: 1.2rem; flex-shrink: 0; }}
.ls-bell {{ position: relative; width: 26px; height: 26px; }}
.ls-bell i {{
  position: absolute; inset: 0; background: #374151;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27black%27 stroke-width=%271.9%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27%3E%3Cpath d=%27M6 8a6 6 0 1 1 12 0c0 7 3 8 3 8H3s3-1 3-8%27/%3E%3Cpath d=%27M10.3 21a1.94 1.94 0 0 0 3.4 0%27/%3E%3C/svg%3E") center / contain no-repeat;
          mask: url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27black%27 stroke-width=%271.9%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27%3E%3Cpath d=%27M6 8a6 6 0 1 1 12 0c0 7 3 8 3 8H3s3-1 3-8%27/%3E%3Cpath d=%27M10.3 21a1.94 1.94 0 0 0 3.4 0%27/%3E%3C/svg%3E") center / contain no-repeat;
}}
.ls-bell .badge {{
  position: absolute; top: -9px; right: -12px; background: {RED}; color: #fff; border-radius: 999px;
  font-size: .68rem; font-weight: 700; padding: 1px 6px; border: 2px solid #F3F4F6;
}}
.ls-avatar {{
  width: 38px; height: 38px; border-radius: 50%; background: {PINK}; color: {RED}; display: grid; place-items: center;
  font-weight: 700; font-size: .95rem;
}}
.ls-who {{ line-height: 1.25; }}
.ls-who .n {{ font-weight: 600; color: #1F2430; }}
.ls-who .r {{ color: #6B7280; font-size: .82rem; }}

/* ---------- tiêu đề mục ---------- */
.ls-section {{
  font-size: 1.18rem; font-weight: 600; color: #1F2430; margin: 1.2rem 0 .7rem;
  padding-left: .85rem; border-left: 3px solid {RED}; line-height: 1.2;
}}

/* ---------- thẻ, bảng, chỉ số ---------- */
[data-testid="stMetric"] {{
  background: #fff; border: 1px solid #ECEEF1; border-radius: 14px; padding: .9rem 1.1rem;
  box-shadow: 0 1px 2px rgba(16,24,40,.04);
}}
[data-testid="stMetricLabel"] p {{ color: #6B7280; font-weight: 500; }}
[data-testid="stDataFrame"], [data-testid="stTable"] {{
  background: #fff; border-radius: 14px; border: 1px solid #ECEEF1; overflow: hidden;
  box-shadow: 0 1px 2px rgba(16,24,40,.04);
}}
[data-testid="stExpander"] details {{ background: #fff; border-radius: 12px; border-color: #ECEEF1; }}
[data-testid="stImage"] img {{ border-radius: 12px; }}
[data-testid="stTabs"] [data-baseweb="tab-list"] {{ gap: 1.2rem; }}
[data-testid="stTabs"] button p {{ font-weight: 600; }}

/* nút phụ: viền đỏ như "Chỉnh sửa" */
button[data-testid="stBaseButton-secondary"], [data-testid="stDownloadButton"] button,
[data-testid="stPopover"] > div > button {{
  background: #fff; border: 1px solid {RED}; color: {RED};
}}
button[data-testid="stBaseButton-secondary"]:hover, [data-testid="stDownloadButton"] button:hover {{
  background: #FDECEC; border-color: {RED}; color: {RED};
}}
button[data-testid="stBaseButton-primary"] {{ font-weight: 600; }}

/* nút trong sidebar: trắng trên nền đỏ */
section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
section[data-testid="stSidebar"] [data-testid="stPopover"] button {{
  background: rgba(255,255,255,.1); border-color: rgba(255,255,255,.6); color: #fff;
}}
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {{ background: #fff; color: {RED}; }}

/* ô nhập dạng viên thuốc như ô tìm kiếm mẫu */
[data-testid="stTextInput"] input {{ border-radius: 999px; }}
</style>
"""

BELL = ('<svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 1 1 12 0c0 7 3 8 3 8H3s3-1 3-8"/>'
        '<path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>')


def apply() -> None:
    st.html(CSS)
    logo = ASSETS / "logo.svg"
    if logo.exists():
        st.logo(str(logo), size="large", icon_image=str(ASSETS / "icon.svg"))


def page_header(title: str, subtitle: str = "", alerts: int | None = None) -> None:
    badge = f'<span class="badge">{alerts}</span>' if alerts else ""
    sub = f'<div class="sub">{html.escape(subtitle)}</div>' if subtitle else ""
    st.html(f"""
<div class="ls-header">
  <div><h1>{html.escape(title)}</h1>{sub}</div>
  <div class="ls-user">
    <div class="ls-bell" title="Sự kiện vi phạm chưa xác nhận"><i></i>{badge}</div>
    <div class="ls-avatar">QT</div>
    <div class="ls-who"><div class="n">Quản trị viên</div><div class="r">Phụ trách phòng thí nghiệm</div></div>
  </div>
</div>""")


def section(title: str) -> None:
    st.html(f'<div class="ls-section">{html.escape(title)}</div>')
