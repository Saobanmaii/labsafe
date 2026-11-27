import hashlib
from pathlib import Path

import pandas as pd
import streamlit as st

import ui
from core import vlm
from core.config import camera_for_image, dataset_images
from core.evaluation import majority_labels
from core.pipeline import MODES, analyze
from core.render import load_image, to_rgb

c = ui.cfg()
Z = ui.zones()
ui.sidebar_status(c)
det = ui.detector(c)

ui.header("Phân tích ảnh", "Kiểm tra một hoặc nhiều ảnh theo bảng kiểm, kèm vùng bằng chứng")

# ---------------------------------------------------------------- đầu vào
src = st.segmented_control("Nguồn ảnh", ["Ảnh mẫu (bộ dữ liệu)", "Tải ảnh lên", "Chụp từ camera"],
                           default="Ảnh mẫu (bộ dữ liệu)")
items: list[tuple[str, bytes | Path]] = []   # (tên, nguồn)
if src == "Ảnh mẫu (bộ dữ liệu)":
    imgs = dataset_images()
    if not imgs:
        st.warning("Không tìm thấy data/images.")
        st.stop()
    names = [p.name for p in imgs]
    if "sample_idx" not in st.session_state:
        st.session_state.sample_idx = names.index("v2c_05.jpg") if "v2c_05.jpg" in names else 0
    a, b, cc = st.columns([1, 6, 1])
    if a.button("◀", width="stretch"):
        st.session_state.sample_idx = (st.session_state.sample_idx - 1) % len(names)
    if cc.button("▶", width="stretch"):
        st.session_state.sample_idx = (st.session_state.sample_idx + 1) % len(names)
    pick = b.selectbox("Ảnh", names, index=st.session_state.sample_idx, label_visibility="collapsed")
    st.session_state.sample_idx = names.index(pick)
    items = [(pick, imgs[names.index(pick)])]
elif src == "Tải ảnh lên":
    ups = st.file_uploader("Chọn một hoặc nhiều ảnh", type=["jpg", "jpeg", "png", "bmp", "webp"],
                           accept_multiple_files=True)
    items = [(u.name, u.getvalue()) for u in ups or []]
else:
    shot = st.camera_input("Chụp ảnh phòng thí nghiệm")
    if shot:
        items = [("camera.jpg", shot.getvalue())]
if not items:
    st.info("Chọn hoặc tải ảnh lên để bắt đầu.")
    st.stop()

# ---------------------------------------------------------------- tuỳ chọn
cams = list(Z.keys())
NO_ZONE = "(không dùng vùng)"
auto_cam = camera_for_image(items[0][0], Z)
o1, o2 = st.columns([1, 2])
cam_opts = [NO_ZONE] + cams
cam = o1.selectbox("Camera / bộ vùng", cam_opts, format_func=lambda x: x if x == NO_ZONE else ui.camera_label(x),
                   index=cam_opts.index(auto_cam) if auto_cam else 0,
                   help="Ảnh mẫu tự chọn đúng camera theo tên file. Ảnh mới: chọn camera có cùng góc chụp "
                        "hoặc tạo camera mới ở trang «Vùng camera».")
cam = None if cam == NO_ZONE else cam
gem = vlm.available()
mode = o2.radio("Chế độ chấm", list(MODES), format_func=MODES.get, horizontal=False,
                disabled=not gem, help=None if gem else "Thêm GEMINI_API_KEY vào file .env để bật Gemini")
with st.expander("Hiển thị & nhật ký", expanded=False):
    t1, t2, t3, t4 = st.columns(4)
    show_zones = t1.toggle("Hiện vùng", True)
    show_all = t2.toggle("Hiện mọi đối tượng", True, help="Tắt: chỉ hiện vật làm bằng chứng")
    blur = t3.toggle("Làm mờ người", c.get("privacy", {}).get("blur_in_display", False))
    auto_log = t4.toggle("Tự ghi sự kiện khi vi phạm", False)
if cam is None:
    st.warning("Chưa chọn bộ vùng: các tiêu chí cần vùng (lối đi, mặt bàn, vị trí bình) sẽ **không đánh giá được**.")

gold_df = majority_labels()


def run_one(name, source, need_click: bool):
    img = load_image(source)
    key = hashlib.sha1((name + str(img.shape) + str(img[::50, ::50].sum())).encode()).hexdigest()[:12]
    if need_click and st.session_state.get(f"vlm_ok_{key}_{mode}") is None:
        return img, key, None
    return img, key, analyze(img, cam, Z, c, det, mode=mode)


# ---------------------------------------------------------------- nhiều ảnh: bảng tổng hợp
if len(items) > 1:
    if mode != "rules" and not st.button(f"Gửi {len(items)} ảnh cho Gemini", type="primary"):
        st.info("Chế độ có Gemini tốn hạn mức API (~20 ảnh/ngày/key) — bấm nút để chạy.")
        st.stop()
    rows, bar = [], st.progress(0.0)
    for k, (name, source) in enumerate(items):
        img, _, a = run_one(name, source, False)
        rows.append({"Ảnh": name, "Điểm": a.score["overall"],
                     **{r.id: {1: "❌", 0: "✅", None: "—"}[r.status] for r in a.results},
                     "Vi phạm": "; ".join(r.name for r in a.violations)})
        with st.expander(f"{name} — điểm {a.score['overall']}, {len(a.violations)} vi phạm"):
            st.image(to_rgb(ui.evidence_image(a, img, c, show_zones=show_zones, show_all=show_all, blur=blur)),
                     width="stretch")
        if auto_log:
            ui.log_violations(a, img, c, camera=cam or "?", source="image", source_name=name)
        bar.progress((k + 1) / len(items))
    out = pd.DataFrame(rows)
    st.dataframe(out, hide_index=True, width="stretch")
    st.download_button("Tải bảng kết quả (CSV)", out.to_csv(index=False).encode("utf-8-sig"),
                       "ket_qua_phan_tich.csv", "text/csv")
    st.stop()

# ---------------------------------------------------------------- một ảnh
name, source = items[0]
img, key, a = run_one(name, source, need_click=mode != "rules")
if a is None:
    st.image(to_rgb(img), width="stretch")
    if st.button("🤖 Gửi ảnh cho Gemini chấm", type="primary"):
        st.session_state[f"vlm_ok_{key}_{mode}"] = True
        st.rerun()
    st.caption("Ảnh được làm mờ người trước khi gửi. Kết quả được lưu đệm: chấm lại cùng ảnh không tốn hạn mức.")
    st.stop()

if a.vlm_error:
    st.error(f"Gemini lỗi, đang dùng kết quả bộ luật: {a.vlm_error}")
elif a.vlm_info:
    st.caption(f"Gemini {a.vlm_info.get('model')}: "
               + ("kết quả lưu đệm" if a.vlm_info.get("cached") else f"{a.vlm_info.get('latency_s')} giây"))

gold = None
if gold_df is not None and name in gold_df.index:
    gold = gold_df.loc[name].to_dict()

ui.score_panel(a, c)
if a.violations:
    st.error("**Phát hiện vi phạm:** " + " · ".join(f"{r.id} {r.name}" for r in a.violations), icon="🚨")
else:
    st.success("Không phát hiện vi phạm nào trong các tiêu chí đánh giá được.", icon="✅")

left, right = st.columns([3, 2])
with left:
    ev = ui.evidence_image(a, img, c, show_zones=show_zones, show_all=show_all, blur=blur)
    st.image(to_rgb(ev), width="stretch",
             caption=f"{name} · camera {cam or '—'} · phát hiện {a.det_ms:.0f} ms · tổng {a.total_ms:.0f} ms · "
                     f"{det.device_name}")
    b1, b2 = st.columns(2)
    if b1.button("📋 Ghi vi phạm vào nhật ký", disabled=not a.violations, width="stretch"):
        ids = ui.log_violations(a, img, c, camera=cam or "?", source="image", source_name=name)
        st.toast(f"Đã ghi {len(ids)} sự kiện (ảnh đã làm mờ người)", icon="📋")
    log_key = f"logged_{key}_{mode}"
    if auto_log and a.violations and not st.session_state.get(log_key):
        st.session_state[log_key] = ui.log_violations(a, img, c, camera=cam or "?", source="image", source_name=name)
        ui.alert(a, c, f"Camera {cam or '?'}")
    ok, buf = __import__("cv2").imencode(".jpg", ev)
    b2.download_button("⬇️ Tải ảnh bằng chứng", buf.tobytes(), f"bang_chung_{Path(name).stem}.jpg",
                       "image/jpeg", width="stretch")
with right:
    if gold is not None:
        agree = sum(1 for r in a.results if r.id in gold and r.status == gold[r.id])
        st.info(f"Ảnh có nhãn của 3 người chấm (đa số): hệ thống khớp **{agree}/{len(gold)}** tiêu chí.", icon="🧑‍⚖️")
    ui.criteria_cards(a, img, c, gold=gold, ncols=1)

with st.expander(f"Chi tiết {len(a.dets)} đối tượng phát hiện"):
    used = {i: [r.id for r in a.results if i in r.evidence] for i in range(len(a.dets))}
    src_name = {"coco": "YOLO11s COCO", "ext": "YOLO11n tự huấn luyện", "world": "YOLO-World"}
    st.dataframe(pd.DataFrame([{"Lớp": d["cls"], "Độ tin cậy": d["conf"], "Mô hình": src_name.get(d["src"], d["src"]),
                                "Bằng chứng cho": ", ".join(used[i]),
                                "Hộp bao (x1,y1,x2,y2)": tuple(int(v) for v in d["xyxy"])}
                               for i, d in enumerate(a.dets)]), hide_index=True, width="stretch")
    if a.suppressed:
        st.caption("Đã loại bỏ (hậu xử lý): " + "; ".join(f"{d['cls']} {d['conf']:.2f} — {d['reason']}"
                                                          for d in a.suppressed))
