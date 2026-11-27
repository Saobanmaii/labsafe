"""Thành phần giao diện dùng chung cho các trang Streamlit."""
from __future__ import annotations

import io
import json
import wave

import numpy as np
import streamlit as st

import theme

from core import vlm
from core.config import load_checklist, load_zones
from core.detector import Detector
from core.events import EventStore, send_telegram
from core.config import ROOT
from core.render import evidence_crop, render, to_rgb

STATUS_BADGE = {1: ":red-badge[VI PHẠM]", 0: ":green-badge[ĐẠT]", None: ":gray-badge[KHÔNG ĐÁNH GIÁ]"}
ENGINE_NAME = {"rules": "YOLO + luật", "vlm": "Gemini"}


def cfg() -> dict:
    try:
        return load_checklist()
    except Exception as e:  # noqa: BLE001
        st.error(f"Bảng kiểm lỗi: {e}. Vào trang «Bảng kiểm» để sửa hoặc khôi phục mặc định.")
        st.stop()


def zones() -> dict:
    return load_zones()


@st.cache_resource(show_spinner="Đang nạp các mô hình YOLO (lần đầu ~20 giây)...")
def _detector(det_json: str) -> Detector:
    return Detector(json.loads(det_json))


def detector(c: dict) -> Detector:
    d = dict(c["detector"])
    for k in ("suppress_on_extinguisher", "custom_skip", "custom_conf"):
        d.pop(k, None)
    return _detector(json.dumps(d, sort_keys=True))


@st.cache_resource
def store() -> EventStore:
    return EventStore()


def camera_label(cam: str) -> str:
    return f"{cam} (vùng riêng cho ảnh này)" if "_" in cam else cam


@st.cache_data
def beep_wav(freq: int = 880, dur: float = 0.6) -> bytes:
    sr = 16000
    t = np.linspace(0, dur, int(sr * dur), False)
    tone = (np.sin(2 * np.pi * freq * t) * (t * 8 % 1 < 0.6) * 0.5 * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(tone.tobytes())
    return buf.getvalue()


def alert(analysis, c: dict, where: str, image_file=None, slot=None) -> None:
    """Cảnh báo khi có vi phạm: thông báo trên màn hình, âm thanh, Telegram (nếu bật)."""
    bad = analysis.violations if hasattr(analysis, "violations") else analysis
    if not bad:
        return
    text = f"⚠️ {where}: " + "; ".join(f"{r.id} {r.name}" for r in bad)
    a = c.get("alerts", {})
    if a.get("on_screen", True):
        st.toast(text, icon="🚨")
    if a.get("sound", True):
        # Streamlit cấm 2 phần tử audio giống hệt nhau trong một lần chạy -> đổi tần số rất nhẹ mỗi lần
        n = st.session_state.get("_beep_n", 0) + 1
        st.session_state["_beep_n"] = n
        (slot or st).audio(beep_wav(880 + n % 300), format="audio/wav", autoplay=True)
    if a.get("telegram"):
        err = send_telegram("Cảnh báo an toàn phòng thí nghiệm\n" + text,
                            ROOT / image_file if image_file else None)
        if err:
            st.caption(err)


def score_panel(a, c: dict) -> None:
    s = a.score
    cols = st.columns(1 + len(s["groups"]))
    ov = s["overall"]
    cols[0].metric("Điểm an toàn", "—" if ov is None else f"{ov}/100",
                   f"{s['violations']} vi phạm / {s['evaluated']} tiêu chí",
                   delta_color="red" if s["violations"] else "green", delta_arrow="off")
    for col, g in zip(cols[1:], s["groups"].values()):
        col.metric(g["name"], "—" if g["score"] is None else f"{g['score']}/100",
                   f"{g['violations']} vi phạm" if g["violations"] else "đạt",
                   delta_color="red" if g["violations"] else "green", delta_arrow="off")


def criteria_cards(a, img, c: dict, gold: dict | None = None, ncols: int = 2) -> None:
    sev = {k: v["name"] for k, v in c["severity"].items()}
    cols = st.columns(ncols)
    for k, r in enumerate(a.results):
        with cols[k % ncols].container(border=True):
            head = f"**{r.id} · {r.name}** {STATUS_BADGE[r.status]}"
            if gold is not None and r.id in gold:
                ok = r.status == gold[r.id]
                head += f" :{'green' if ok else 'orange'}-badge[Người chấm: {'VI PHẠM' if gold[r.id] else 'ĐẠT'}]"
            st.markdown(head)
            st.caption(f"Nhóm: {c['groups'].get(r.group, r.group)} · Mức độ: {sev.get(r.severity, r.severity)} · "
                       f"Quyết định bởi: {ENGINE_NAME[r.engine]}")
            st.write(r.explanation)
            if r.vlm_status is not None:
                st.markdown(f"🤖 *Gemini:* {STATUS_BADGE[r.vlm_status]} {r.vlm_reason}")
                if r.rule_status is not None and r.rule_status != r.vlm_status:
                    st.caption(f"Bộ luật kết luận khác: {'VI PHẠM' if r.rule_status else 'ĐẠT'}")
            crop = evidence_crop(img, a.cam_zones, a.dets, r)
            if crop is not None and r.status == 1:
                st.image(to_rgb(crop), caption="Vùng bằng chứng", width="stretch")


def evidence_image(a, img, c: dict, *, show_zones=True, show_all=True, blur=False, banner=None):
    return render(img, a.cam_zones, a.dets, a.results, c, show_zones=show_zones, show_all=show_all,
                  blur=blur, banner=banner)


def log_violations(a, img, c: dict, *, camera: str, source: str, source_name: str) -> list[int]:
    """Ghi mỗi tiêu chí vi phạm thành một sự kiện, ảnh bằng chứng luôn làm mờ người."""
    if not a.violations:
        return []
    ev = render(img, a.cam_zones, a.dets, a.results, c, show_all=False,
                blur=c.get("privacy", {}).get("blur_people", True), banner=f"Camera {camera}")
    n_people = sum(1 for d in a.dets if d["cls"] == "person")
    path = store().save_image(ev, f"{camera}_{source}")
    ids = [store().open(camera=camera, source=source, source_name=source_name, r=r, cfg=c,
                        image_path=path, people_blurred=n_people, closed=True) for r in a.violations]
    return ids


def sidebar_status(c: dict) -> None:
    gem = vlm.available()
    on = sum(1 for x in c["criteria"] if x.get("enabled", True))
    with st.sidebar:
        st.html(f"""<div class="ls-side-status">
<div style="opacity:.75;font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;margin-bottom:.2rem">Trạng thái hệ thống</div>
<div>Gemini API: <b>{"đã có key" if gem else "chưa cấu hình"}</b></div>
<div>Tiêu chí đang bật: <b>{on}/{len(c["criteria"])}</b></div>
<div>Camera đã vẽ vùng: <b>{len(zones())}</b></div></div>""")


def header(title: str, subtitle: str = "") -> None:
    """Tiêu đề trang theo giao diện LabSafe; chuông hiện số sự kiện chưa xác nhận."""
    try:
        df = store().df()
        n = int((df["ack"] == 0).sum()) if len(df) else 0
    except Exception:  # noqa: BLE001
        n = 0
    theme.page_header(title, subtitle, alerts=n)


def section(title: str) -> None:
    theme.section(title)
