import altair as alt
import pandas as pd
import streamlit as st

import ui
from core.config import ROOT

c = ui.cfg()
ui.sidebar_status(c)
store = ui.store()

ui.header("Nhật ký sự kiện", "Vi phạm đã ghi nhận, ảnh bằng chứng đã làm mờ người")
st.caption("Mỗi vi phạm được ghi một dòng (thời gian, camera, tiêu chí, vùng, lý do) kèm ảnh bằng chứng "
           "**đã làm mờ người**. Lưu trong SQLite: `app_data/events.db`.")

df = store.df()
if not df.empty:
    df["severity"] = df["severity"].map(lambda k: c["severity"].get(k, {}).get("name", k))
if df.empty:
    st.info("Chưa có sự kiện. Chạy «Video & camera» hoặc bấm «Ghi vi phạm vào nhật ký» ở trang «Phân tích ảnh».")
    st.stop()

# ---------------------------------------------------------------- bộ lọc
f1, f2, f3, f4, f5 = st.columns(5)
cams = f1.multiselect("Camera", sorted(df["camera"].dropna().unique()))
crits = f2.multiselect("Tiêu chí", sorted(df["criterion"].unique()))
grps = f3.multiselect("Nhóm", sorted(df["grp_name"].dropna().unique()))
stt = f4.selectbox("Trạng thái", ["Tất cả", "Chưa xác nhận", "Đã xác nhận", "Đang mở"])
dmin, dmax = df["started_at"].min().date(), df["started_at"].max().date()
rng = f5.date_input("Khoảng ngày", (dmin, dmax), min_value=dmin, max_value=dmax)
v = df
if cams:
    v = v[v["camera"].isin(cams)]
if crits:
    v = v[v["criterion"].isin(crits)]
if grps:
    v = v[v["grp_name"].isin(grps)]
if stt == "Chưa xác nhận":
    v = v[v["ack"] == 0]
elif stt == "Đã xác nhận":
    v = v[v["ack"] == 1]
elif stt == "Đang mở":
    v = v[v["status"] == "open"]
if isinstance(rng, tuple) and len(rng) == 2:
    v = v[(v["started_at"].dt.date >= rng[0]) & (v["started_at"].dt.date <= rng[1])]

# ---------------------------------------------------------------- thống kê
k = st.columns(4)
k[0].metric("Sự kiện (đã lọc)", len(v))
k[1].metric("Mức độ cao", int((v["severity"] == c["severity"].get("cao", {}).get("name", "cao")).sum()))
k[2].metric("Chưa xác nhận", int((v["ack"] == 0).sum()))
dur = v["duration_s"].dropna()
k[3].metric("Thời lượng vi phạm TB (video)", f"{dur[dur > 0].mean():.0f} s" if (dur > 0).any() else "—")

g1, g2 = st.columns(2)
with g1:
    ui.section("Theo tiêu chí và nhóm")
    cnt = v.groupby(["criterion", "criterion_name", "grp_name"]).size().reset_index(name="Số sự kiện")
    cnt["Tiêu chí"] = cnt["criterion"] + " " + cnt["criterion_name"]
    st.altair_chart(alt.Chart(cnt).mark_bar().encode(
        x="Số sự kiện:Q", y=alt.Y("Tiêu chí:N", sort="-x"), color=alt.Color("grp_name:N", title="Nhóm"),
        tooltip=["Tiêu chí", "grp_name", "Số sự kiện"]), width="stretch")
with g2:
    ui.section("Theo thời gian")
    t = v.assign(gio=v["started_at"].dt.floor("h")).groupby(["gio", "criterion"]).size().reset_index(name="n")
    st.altair_chart(alt.Chart(t).mark_bar().encode(
        x=alt.X("gio:T", title="Giờ"), y=alt.Y("n:Q", title="Số sự kiện"), color=alt.Color("criterion:N", title="Tiêu chí"),
        tooltip=["gio:T", "criterion", "n"]), width="stretch")

# ---------------------------------------------------------------- bảng + chi tiết
ui.section("Danh sách sự kiện")
st.caption("Chọn dòng để xem ảnh bằng chứng và xác nhận đã xử lý")
show = v[["id", "started_at", "ended_at", "camera", "criterion", "criterion_name", "grp_name", "severity", "zone",
          "engine", "source", "source_name", "video_t0", "video_t1", "status", "ack", "explanation", "note",
          "image_path"]].copy()
sel = st.dataframe(
    show, hide_index=True, width="stretch", on_select="rerun", selection_mode="multi-row", height=320,
    column_config={
        "id": st.column_config.NumberColumn("ID", width="small"),
        "started_at": st.column_config.DatetimeColumn("Bắt đầu", format="DD/MM HH:mm:ss"),
        "ended_at": st.column_config.DatetimeColumn("Kết thúc", format="DD/MM HH:mm:ss"),
        "camera": "Camera", "criterion": "Mã", "criterion_name": "Tiêu chí", "grp_name": "Nhóm",
        "severity": "Mức độ", "zone": "Vùng", "engine": "Bộ chấm", "source": "Nguồn", "source_name": "Tệp / luồng",
        "video_t0": st.column_config.NumberColumn("Từ giây", format="%.0f s"),
        "video_t1": st.column_config.NumberColumn("Đến giây", format="%.0f s"),
        "status": "Trạng thái",
        "ack": st.column_config.CheckboxColumn("Đã xử lý"), "explanation": "Lý do", "note": "Ghi chú",
        "image_path": None,
    })
rows = sel.selection.rows if sel else []
if rows:
    chosen = show.iloc[rows]
    a, b = st.columns([3, 2])
    with a:
        for _, r in chosen.head(4).iterrows():
            p = ROOT / str(r["image_path"])
            if p.exists():
                st.image(str(p), width="stretch",
                         caption=f"#{r['id']} · {r['criterion']} {r['criterion_name']} · {r['started_at']:%d/%m %H:%M:%S}")
    with b:
        for _, r in chosen.head(4).iterrows():
            with st.container(border=True):
                st.markdown(f"**#{r['id']} · {r['criterion']} {r['criterion_name']}** "
                            f"{':green-badge[Đã xử lý]' if r['ack'] else ':orange-badge[Chưa xử lý]'}")
                st.caption(f"Camera {r['camera']} · vùng {r['zone']} · {r['source']} · bộ chấm {r['engine']}")
                st.write(r["explanation"])
        note = st.text_input("Ghi chú xử lý", placeholder="vd: đã nhắc sinh viên dọn balo khỏi lối đi")
        if st.button(f"✔ Xác nhận đã xử lý {len(chosen)} sự kiện", type="primary"):
            store.ack([int(i) for i in chosen["id"]], note)
            st.rerun()

st.divider()
e1, e2, e3 = st.columns(3)
e1.download_button("⬇️ Xuất CSV (đã lọc)", v.drop(columns=["duration_s"]).to_csv(index=False).encode("utf-8-sig"),
                   "nhat_ky_su_kien.csv", "text/csv")
with e3.popover("🗑️ Xoá toàn bộ nhật ký"):
    st.write("Xoá mọi sự kiện và ảnh bằng chứng. Không hoàn tác được.")
    if st.button("Xoá hết", type="primary"):
        store.delete_all()
        st.rerun()
