import tempfile
import time
from pathlib import Path

import altair as alt
import cv2
import pandas as pd
import streamlit as st

import ui
from core.config import STORE
from core.events import TemporalFilter
from core.pipeline import analyze
from core.render import to_rgb

c = ui.cfg()
Z = ui.zones()
ui.sidebar_status(c)
det = ui.detector(c)
vc = c.get("video", {})

ui.header("Video & camera", "Giám sát liên tục từ tệp video, webcam hoặc camera điện thoại")
st.caption("Lấy mẫu khung hình theo chu kỳ, chạy YOLO + bộ luật. Một vi phạm chỉ thành **sự kiện** khi kéo dài "
           "nhiều khung liên tiếp (tránh báo động giả khi có người đi ngang), và tự đóng khi hết vi phạm.")

# ---------------------------------------------------------------- nguồn
kind = st.segmented_control("Nguồn", ["Tệp video", "Webcam", "Camera IP / điện thoại"], default="Tệp video")
source, source_name = None, ""
if kind == "Tệp video":
    demo_videos = sorted(STORE.glob("demo_*.mp4"))
    up = st.file_uploader("Tải video lên (mp4, avi, mov)", type=["mp4", "avi", "mov", "mkv"])
    if up:
        tmp = Path(tempfile.gettempdir()) / f"labsafe_{up.name}"
        tmp.write_bytes(up.getvalue())
        source, source_name = str(tmp), up.name
    elif demo_videos:
        pick = st.selectbox("…hoặc dùng video mẫu", demo_videos, format_func=lambda p: p.name)
        source, source_name = str(pick), pick.name
    else:
        st.info("Chưa có video mẫu. Tạo bằng: `python app/make_demo_video.py`")
elif kind == "Webcam":
    idx = st.number_input("Chỉ số webcam", 0, 5, 0, help="0 = webcam tích hợp của laptop")
    source, source_name = int(idx), f"webcam{idx}"
else:
    url = st.text_input("Địa chỉ luồng", placeholder="http://192.168.1.5:8080/video  hoặc  rtsp://...",
                        help="Điện thoại Android: cài app «IP Webcam», bấm Start server, dùng địa chỉ hiện trên màn hình + /video")
    if url:
        source, source_name = url, url

# ---------------------------------------------------------------- tuỳ chọn
cams = list(Z.keys())
default_cam = "v2c" if "v2c" in cams else cams[0]
if isinstance(source_name, str) and source_name.startswith("demo_"):
    guess = source_name.removeprefix("demo_").removesuffix(".mp4")
    default_cam = guess if guess in cams else default_cam
s1, s2, s3, s4 = st.columns(4)
cam = s1.selectbox("Camera / bộ vùng", cams, index=cams.index(default_cam), format_func=ui.camera_label,
                   help="Bộ vùng phải vẽ cho đúng góc nhìn của camera này (trang «Vùng camera»).")
every = s2.number_input("Lấy mẫu mỗi (giây)", 0.2, 10.0, float(vc.get("sample_every_s", 1.0)), 0.2)
confirm = s3.number_input("Xác nhận sau (khung)", 1, 20, int(vc.get("confirm_frames", 3)))
clear = s4.number_input("Đóng sau (khung)", 1, 20, int(vc.get("clear_frames", 3)))
o1, o2, o3 = st.columns(3)
speed = o1.select_slider("Tốc độ phát (tệp video)", ["1x", "2x", "4x", "tối đa"], value="2x")
blur = o2.toggle("Làm mờ người trên màn hình", c.get("privacy", {}).get("blur_in_display", False))
log_events = o3.toggle("Ghi sự kiện vào nhật ký", True)

start = st.button("▶ Bắt đầu giám sát", type="primary", disabled=source is None)


def show_timeline(timeline, title):
    tl = pd.DataFrame(timeline)
    if len(tl):
        ui.section("{title}")
        long = tl.melt(id_vars=["t"], var_name="Tiêu chí", value_name="Vi phạm").dropna()
        long["Trạng thái"] = long["Vi phạm"].map({1: "Vi phạm", 0: "Đạt"})
        long["t2"] = long["t"] + every
        st.altair_chart(alt.Chart(long).mark_rect().encode(
            x=alt.X("t:Q", title="Thời gian (giây)"), x2="t2:Q",
            y=alt.Y("Tiêu chí:N"),
            color=alt.Color("Trạng thái:N", scale=alt.Scale(domain=["Đạt", "Vi phạm"], range=["#59b36b", "#e04848"]))),
            width="stretch")
        st.page_link("pages/events.py", label="Xem sự kiện đã ghi", icon="📋")


if not start:
    if st.session_state.get("video_timeline"):
        show_timeline(st.session_state.video_timeline, "Diễn biến lần chạy trước")
    st.stop()

# ---------------------------------------------------------------- vòng giám sát
cap = cv2.VideoCapture(source)
if not cap.isOpened():
    st.error(f"Không mở được nguồn: {source_name}")
    st.stop()
is_file = kind == "Tệp video"
fps = cap.get(cv2.CAP_PROP_FPS) or 25
n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if is_file else 0
step = max(1, int(round(fps * every)))
mult = {"1x": 1, "2x": 2, "4x": 4, "tối đa": 0}[speed]

st.button("⏹ Dừng", help="Dừng giám sát; các sự kiện đang mở sẽ được đóng")
prog = st.progress(0.0) if is_file and n_frames else None
left, right = st.columns([3, 2])
frame_slot = left.empty()
info_slot = left.empty()
status_slot = right.empty()
alert_slot = right.empty()
feed_slot = right.empty()

tf = TemporalFilter(confirm, clear)
open_ids: dict[str, int] = {}
feed: list[str] = []
timeline: list[dict] = []
store = ui.store()
t_wall0 = time.perf_counter()
fidx = 0
try:
    while True:
        if is_file:
            ok = cap.grab()
            if not ok:
                break
            if fidx % step:
                fidx += 1
                continue
            ok, frame = cap.retrieve()
            t_video = fidx / fps
            fidx += 1
        else:
            t_loop = time.perf_counter()
            ok, frame = cap.read()
            t_video = time.perf_counter() - t_wall0
        if not ok or frame is None:
            break

        a = analyze(frame, cam, Z, c, det, mode="rules")
        opened, closed = tf.update(a.statuses)
        timeline.append({"t": round(t_video, 1), **a.statuses})

        ev = ui.evidence_image(a, frame, c, show_all=False, blur=blur)
        frame_slot.image(to_rgb(ev), width="stretch")
        info_slot.caption(f"{source_name} · t = {t_video:6.1f} s · {a.det_ms:.0f} ms/khung · {det.device_name}")

        lines = []
        for r in a.results:
            badge = ui.STATUS_BADGE[r.status]
            extra = tf.progress(r.id)
            lines.append(f"**{r.id}** {r.name} {badge}" + (f" · *{extra}*" if extra else ""))
        status_slot.markdown("#### Trạng thái hiện tại\n" + "\n\n".join(lines) +
                             f"\n\n**Điểm an toàn:** {a.score['overall']}/100")

        now = time.strftime("%H:%M:%S")
        if opened:
            bad = [r for r in a.results if r.id in opened]
            path = None
            if log_events:
                img = ui.evidence_image(a, frame, c, show_all=False,
                                        blur=c.get("privacy", {}).get("blur_people", True), banner=f"Camera {cam}")
                path = store.save_image(img, f"{cam}_video")
                n_people = sum(1 for d in a.dets if d["cls"] == "person")
                for r in bad:
                    open_ids[r.id] = store.open(camera=cam, source="video" if is_file else "stream",
                                                source_name=source_name, r=r, cfg=c, image_path=path,
                                                people_blurred=n_people, t_video=round(t_video, 1))
            for r in bad:
                feed.insert(0, f"🔴 `{now}` t={t_video:.0f}s **{r.id} {r.name}** — {r.explanation}")
            ui.alert(bad, c, f"Camera {cam}", image_file=path, slot=alert_slot)
        for cid in closed:
            if cid in open_ids:
                store.close(open_ids.pop(cid), t_video=round(t_video, 1))
            feed.insert(0, f"🟢 `{now}` t={t_video:.0f}s **{cid}** hết vi phạm — đóng sự kiện")
        feed_slot.markdown("#### Sự kiện\n" + ("\n\n".join(feed[:12]) if feed else "_chưa có_"))

        if prog:
            prog.progress(min(1.0, fidx / n_frames))
        if is_file and mult:
            target = t_video / mult
            lag = target - (time.perf_counter() - t_wall0)
            if lag > 0:
                time.sleep(lag)
        elif not is_file:
            time.sleep(max(0.0, every - (time.perf_counter() - t_loop)))
finally:
    cap.release()
    for eid in open_ids.values():
        store.close(eid, t_video=round(timeline[-1]["t"], 1) if timeline else None)
    st.session_state.video_timeline = timeline

st.success(f"Đã xử lý {len(timeline)} khung hình. Sự kiện đã ghi: {sum(1 for f in feed if f.startswith('🔴'))}.")
show_timeline(timeline, "Diễn biến theo thời gian")
