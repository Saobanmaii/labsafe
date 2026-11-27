import re

import cv2
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates

import ui
from core.config import CAMERA_DIR, camera_reference_image, save_zones
from core.render import draw_zones_only, load_image, save_jpg, to_rgb

c = ui.cfg()
ui.sidebar_status(c)
Z = ui.zones()
ZT = c["zone_types"]

ui.header("Vùng camera", "Vẽ lối đi, mặt bàn, vị trí bình chữa cháy cho từng góc camera")
st.caption("Mỗi góc camera vẽ vùng **một lần** (lối đi, mặt bàn, vị trí bình chữa cháy...), giống cấu hình vùng của "
           "camera giám sát. Bộ luật dùng các vùng này để biết vật nằm ở đâu và cảnh báo theo vùng nguy cơ.")

# ---------------------------------------------------------------- chọn / tạo camera
left, right = st.columns([2, 3])
with left:
    cams = list(Z.keys())
    cam = st.selectbox("Camera", cams, format_func=ui.camera_label, key="zone_cam")
with right, st.expander("➕ Tạo camera mới"):
    name = st.text_input("Tên camera (chữ, số, gạch dưới)", placeholder="lab_dien_tu_goc1")
    how = st.radio("Ảnh nền", ["Tải ảnh lên", "Chụp từ webcam"], horizontal=True)
    shot = (st.file_uploader("Ảnh góc camera", type=["jpg", "jpeg", "png"]) if how == "Tải ảnh lên"
            else st.camera_input("Chụp khung hình"))
    if st.button("Tạo camera", disabled=not (name and shot)):
        if not re.fullmatch(r"[A-Za-z0-9_]+", name):
            st.error("Tên chỉ gồm chữ không dấu, số, gạch dưới")
        elif name in Z:
            st.error("Tên đã tồn tại")
        else:
            save_jpg(CAMERA_DIR / f"{name}.jpg", load_image(shot.getvalue()), quality=92)
            Z[name] = {}
            save_zones(Z)
            st.session_state.zone_cam = name
            st.rerun()

ref = camera_reference_image(cam)
if ref is None:
    st.warning("Camera này chưa có ảnh nền. Tải ảnh mới cho camera bên dưới.")
    up = st.file_uploader("Ảnh nền", type=["jpg", "jpeg", "png"], key="ref_up")
    if up:
        save_jpg(CAMERA_DIR / f"{cam}.jpg", load_image(up.getvalue()), quality=92)
        st.rerun()
    st.stop()

# ---------------------------------------------------------------- trình vẽ
pend_key = f"pending_{cam}"
pending = st.session_state.setdefault(pend_key, [])
cz = Z.setdefault(cam, {})

tool, canvas = st.columns([1, 3])
with tool:
    zt = st.radio("Loại vùng đang vẽ", list(ZT), format_func=lambda z: ZT[z]["name"])
    st.caption("Nhấp lên ảnh để đặt từng đỉnh đa giác, rồi bấm **Hoàn tất vùng**. Một loại vùng có thể gồm nhiều đa giác.")
    st.markdown(f"Đỉnh đang vẽ: **{len(pending)}**")
    if st.button("✔ Hoàn tất vùng", type="primary", disabled=len(pending) < 3, width="stretch"):
        cz.setdefault(zt, []).append([[round(x, 4), round(y, 4)] for x, y in pending])
        save_zones(Z)
        st.session_state[pend_key] = []
        st.rerun()
    if st.button("↶ Xoá đỉnh cuối", disabled=not pending, width="stretch"):
        pending.pop()
        st.rerun()
    if st.button("✖ Huỷ đa giác đang vẽ", disabled=not pending, width="stretch"):
        st.session_state[pend_key] = []
        st.rerun()
    st.divider()
    st.markdown("**Vùng đã lưu**")
    for z in list(cz):
        n = len(cz[z])
        a, b = st.columns([3, 1])
        a.write(f"{ZT.get(z, {}).get('name', z)}: {n} đa giác")
        with b.popover("🗑️", help="Xoá các đa giác của loại vùng này"):
            st.write(f"Xoá {n} đa giác «{ZT.get(z, {}).get('name', z)}» của camera {cam}?")
            if st.button("Xoá", key=f"delz_{cam}_{z}", type="primary"):
                del cz[z]
                save_zones(Z)
                st.rerun()
    missing = [ZT[z]["name"] for z in ZT if z not in cz]
    if missing:
        st.info("Chưa vẽ: " + ", ".join(missing) + ". Tiêu chí dùng vùng này sẽ «không đánh giá được».")
    with st.popover("Xoá camera", width="stretch"):
        if st.button(f"Xoá «{cam}»", type="primary"):
            del Z[cam]
            save_zones(Z)
            del st.session_state["zone_cam"]
            st.rerun()

with canvas:
    img = load_image(ref)
    h, w = img.shape[:2]
    disp_w = 1000
    scale = disp_w / w
    small = cv2.resize(img, (disp_w, int(h * scale)), interpolation=cv2.INTER_AREA)
    view = draw_zones_only(small, cz, c, pending,
                           pending_color=tuple(ZT[zt]["color"]))
    click = streamlit_image_coordinates(to_rgb(view), key=f"canvas_{cam}", width=disp_w)
    if click and click != st.session_state.get(f"last_click_{cam}"):
        st.session_state[f"last_click_{cam}"] = click
        cw, ch = click.get("width") or disp_w, click.get("height") or small.shape[0]
        pending.append((click["x"] / cw, click["y"] / ch))
        st.rerun()
    st.caption(f"Ảnh nền: {ref.name} · vùng lưu trong app_data/zones.json (toạ độ chuẩn hoá 0..1, dùng được cho mọi độ phân giải)")
