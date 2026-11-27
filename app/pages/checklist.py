import copy

import streamlit as st
import yaml

import ui
from core.config import RULE_TYPES, reset_checklist, save_checklist
from core.detector import EXTINGUISHER

c = ui.cfg()
ui.sidebar_status(c)
det = ui.detector(c)

ui.header("Bảng kiểm", "Tiêu chí, ngưỡng, lớp đối tượng và mức độ — cấu hình không cần sửa code")
st.caption("Mọi thay đổi lưu vào `app/checklist.yaml` và áp dụng ngay cho ảnh, video và trang đánh giá. "
           "Bấm **💾 Lưu bảng kiểm** ở thanh bên khi sửa xong.")

deleted = st.session_state.setdefault("ck_deleted", set())
new = copy.deepcopy(c)
class_opts = sorted(set(det.coco_names) | set(c["detector"].get("world_classes") or []) | {EXTINGUISHER}
                    | set(det.custom_names))
groups, sevs, ztypes = list(c["groups"]), list(c["severity"]), list(c["zone_types"])


def K(*parts):
    return "ck_" + "_".join(str(p) for p in parts)


def _reset_widgets():
    for k in [k for k in st.session_state if k.startswith("ck_")]:
        del st.session_state[k]


tab1, tab2, tab3, tab4, tab5 = st.tabs(["Tiêu chí", "Nhóm · mức độ · loại vùng", "Bộ phát hiện",
                                        "Video · cảnh báo · riêng tư", "YAML"])

# ================================================================ tiêu chí
with tab1:
    out = []
    for x in c["criteria"]:
        cid = x["id"]
        if cid in deleted:
            continue
        y = copy.deepcopy(x)
        on = x.get("enabled", True)
        with st.expander(f"{'🟢' if on else '⚪'} **{cid} · {x['name']}** — {RULE_TYPES[x['type']]}", expanded=False):
            a, b, cc, d = st.columns([1, 3, 2, 2])
            y["enabled"] = a.toggle("Bật", on, key=K(cid, "on"))
            y["name"] = b.text_input("Tên tiêu chí", x["name"], key=K(cid, "name"))
            y["group"] = cc.selectbox("Nhóm", groups, groups.index(x["group"]), format_func=c["groups"].get,
                                      key=K(cid, "grp"))
            y["severity"] = d.selectbox("Mức độ", sevs, sevs.index(x["severity"]),
                                        format_func=lambda s: c["severity"][s]["name"], key=K(cid, "sev"))
            p = dict(x.get("params", {}))
            a, b = st.columns([1, 3])
            if x["type"] == "count_in_zone":
                zopts = [None] + ztypes
                y["zone"] = a.selectbox("Vùng", zopts, zopts.index(x.get("zone")),
                                        format_func=lambda z: "Toàn ảnh" if z is None else c["zone_types"][z]["name"],
                                        key=K(cid, "zone"))
            else:
                y["zone"] = a.selectbox("Vùng", ztypes, ztypes.index(x["zone"]),
                                        format_func=lambda z: c["zone_types"][z]["name"], key=K(cid, "zone"))
            lab = {"zone_occupancy": "Lớp đối tượng tính là vật cản", "count_in_zone": "Lớp đối tượng được đếm",
                   "zone_visibility": "Lớp đối tượng tính là vật che"}[x["type"]]
            y["classes"] = b.multiselect(lab, class_opts, [k for k in x.get("classes", []) if k in class_opts],
                                         key=K(cid, "cls"))
            a, b, cc = st.columns(3)
            if x["type"] == "zone_occupancy":
                p["threshold"] = a.slider("Ngưỡng chiếm dụng vùng (%)", 1, 50, int(round(p.get("threshold", .05) * 100)),
                                          key=K(cid, "thr")) / 100
                p["footprint_frac"] = b.slider("Phần đáy hộp bao coi là chân vật", 0.05, 1.0,
                                               float(p.get("footprint_frac", .25)), 0.05, key=K(cid, "foot"))
                cc.caption("Vi phạm khi diện tích phần chân vật cản nằm trong vùng ≥ ngưỡng × diện tích vùng.")
            elif x["type"] == "count_in_zone":
                p["min_count"] = a.number_input("Vi phạm khi số vật ≥", 1, 50, int(p.get("min_count", 1)),
                                                key=K(cid, "min"))
                cc.caption("Đếm vật có tâm khung nằm trong vùng (hoặc toàn ảnh).")
            else:
                y["target"] = a.selectbox("Vật bắt buộc nhìn thấy", class_opts,
                                          class_opts.index(x["target"]) if x["target"] in class_opts else 0,
                                          key=K(cid, "tgt"))
                p["min_visible"] = b.slider("Tỷ lệ nhìn thấy tối thiểu", 0.0, 1.0, float(p.get("min_visible", .5)),
                                            0.05, key=K(cid, "vis"))
                p["max_occlusion"] = round(cc.slider("Tỷ lệ bị che tối đa", 0.05, 1.0,
                                                     float(p.get("max_occlusion", 1 / 3)), 0.05, key=K(cid, "occ")), 4)
            y["params"] = p
            a, b = st.columns([1, 3])
            y["hybrid_engine"] = a.radio("Chế độ Kết hợp dùng", ["rules", "vlm"],
                                         ["rules", "vlm"].index(x.get("hybrid_engine", "rules")),
                                         format_func={"rules": "Bộ luật", "vlm": "Gemini"}.get, key=K(cid, "hyb"))
            y["vlm_description"] = b.text_area("Mô tả cho Gemini (tiếng Anh)", x.get("vlm_description", ""),
                                               height=90, key=K(cid, "vlm"))
            if st.button("🗑️ Xoá tiêu chí này", key=K(cid, "del")):
                deleted.add(cid)
                st.rerun()
        out.append(y)
    new["criteria"] = out

    ui.section("Thêm tiêu chí mới")
    with st.form("add_crit", clear_on_submit=True):
        a, b, cc = st.columns([1, 3, 2])
        nid = a.text_input("Mã", placeholder="C5")
        nname = b.text_input("Tên", placeholder="Thùng carton chắn lối thoát hiểm")
        ntype = cc.selectbox("Loại luật", list(RULE_TYPES), format_func=RULE_TYPES.get)
        a, b, cc, d = st.columns(4)
        nzone = a.selectbox("Vùng", [None] + ztypes,
                            format_func=lambda z: "Toàn ảnh (chỉ cho luật đếm)" if z is None else c["zone_types"][z]["name"])
        ngrp = b.selectbox("Nhóm", groups, format_func=c["groups"].get)
        nsev = cc.selectbox("Mức độ", sevs, format_func=lambda s: c["severity"][s]["name"])
        ntgt = d.selectbox("Vật bắt buộc (luật nhìn thấy)", class_opts, class_opts.index(EXTINGUISHER))
        ncls = st.multiselect("Lớp đối tượng", class_opts)
        ndesc = st.text_input("Mô tả cho Gemini (tiếng Anh)", placeholder="Cardboard boxes: VIOLATED if ...")
        if st.form_submit_button("Thêm và lưu"):
            item = {"id": nid.strip(), "name": nname.strip() or nid.strip(), "group": ngrp, "severity": nsev,
                    "enabled": True, "type": ntype, "zone": nzone, "classes": ncls,
                    "params": {"zone_occupancy": {"footprint_frac": 0.25, "threshold": 0.05},
                               "count_in_zone": {"min_count": 1},
                               "zone_visibility": {"min_visible": 0.5, "max_occlusion": 0.3333}}[ntype],
                    "hybrid_engine": "rules", "vlm_description": ndesc or f"{nname}: VIOLATED if present."}
            if ntype == "zone_visibility":
                item["target"] = ntgt
            try:
                new["criteria"].append(item)
                save_checklist(new)
                deleted.clear()
                _reset_widgets()
                st.success(f"Đã thêm {nid}")
                st.rerun()
            except ValueError as e:
                new["criteria"].pop()
                st.error(str(e))

# ================================================================ nhóm, mức độ, vùng
with tab2:
    a, b = st.columns(2)
    with a:
        st.markdown("**Nhóm tiêu chí** (điểm được tính riêng cho từng nhóm)")
        for g in groups:
            new["groups"][g] = st.text_input(g, c["groups"][g], key=K("g", g))
        st.markdown("**Mức độ nghiêm trọng → trọng số điểm**")
        for s in sevs:
            x1, x2 = st.columns([2, 1])
            new["severity"][s]["name"] = x1.text_input(s, c["severity"][s]["name"], key=K("s", s))
            new["severity"][s]["weight"] = x2.number_input("trọng số", 1, 10, int(c["severity"][s]["weight"]),
                                                           key=K("sw", s))
    with b:
        st.markdown("**Loại vùng** (vẽ ở trang «Vùng camera»)")
        for z in ztypes:
            x1, x2, x3 = st.columns([3, 1, 2])
            zt = c["zone_types"][z]
            new["zone_types"][z]["name"] = x1.text_input(z, zt["name"], key=K("z", z))
            bgr = zt.get("color", [200, 200, 200])
            hexv = x2.color_picker("màu", "#%02x%02x%02x" % (bgr[2], bgr[1], bgr[0]), key=K("zc", z))
            new["zone_types"][z]["color"] = [int(hexv[5:7], 16), int(hexv[3:5], 16), int(hexv[1:3], 16)]
            new["zone_types"][z]["risk"] = x3.selectbox("nguy cơ", sevs, sevs.index(zt.get("risk", sevs[0])),
                                                         format_func=lambda s: c["severity"][s]["name"], key=K("zr", z))
        with st.form("add_zone", clear_on_submit=True):
            x1, x2 = st.columns(2)
            zid = x1.text_input("Mã loại vùng mới", placeholder="exit")
            zname = x2.text_input("Tên", placeholder="Cửa thoát hiểm")
            if st.form_submit_button("Thêm loại vùng") and zid.strip():
                new["zone_types"][zid.strip()] = {"name": zname or zid, "color": [0, 165, 255], "risk": "cao"}
                save_checklist(new)
                _reset_widgets()
                st.rerun()

# ================================================================ bộ phát hiện
with tab3:
    d = new["detector"]
    a, b = st.columns(2)
    d["conf"] = a.slider("Ngưỡng tin cậy phát hiện", 0.05, 0.9, float(c["detector"]["conf"]), 0.05, key=K("conf"),
                         help="Thấp hơn: bắt được nhiều vật hơn nhưng nhiều nhầm hơn. Bài báo dùng 0,30.")
    wc = b.text_input("Lớp từ vựng mở cho YOLO-World (phân cách bằng dấu phẩy)",
                      ", ".join(c["detector"].get("world_classes") or []), key=K("world"),
                      help="Ví dụ thêm «jacket» để nhận áo khoác (COCO không có lớp này).")
    d["world_classes"] = [s.strip() for s in wc.split(",") if s.strip()]
    st.markdown("**Hậu xử lý: bỏ khung chai/cốc nằm trên bình chữa cháy**")
    st.caption("Lỗi chính trong bài báo: YOLO COCO nhận bình chữa cháy màu đỏ là «bottle» → báo nhầm C4. "
               "Bật bước này nâng κ của C4 trên 62 ảnh từ 0,78 lên 0,90.")
    s = d["suppress_on_extinguisher"]
    a, b, cc = st.columns([1, 2, 1])
    s["enabled"] = a.toggle("Bật", bool(s.get("enabled")), key=K("sup_on"))
    s["classes"] = b.multiselect("Lớp bị lọc", class_opts, [k for k in s.get("classes", []) if k in class_opts],
                                 key=K("sup_cls"))
    s["overlap"] = cc.slider("Tỷ lệ chồng lấn", 0.1, 1.0, float(s.get("overlap", .5)), 0.05, key=K("sup_ov"))
    st.caption(f"Mô hình: `{c['detector']['coco_model']}` · `{c['detector']['ext_model']}` · "
               f"`{c['detector']['world_model']}` · thiết bị: {det.device_name}")
    new["vlm"]["model"] = st.text_input("Model Gemini", c["vlm"]["model"], key=K("vlm_model"))

# ================================================================ video, cảnh báo, riêng tư
with tab4:
    a, b, cc = st.columns(3)
    vv = new.setdefault("video", {})
    vv["sample_every_s"] = a.number_input("Lấy mẫu mỗi (giây)", 0.2, 10.0, float(vv.get("sample_every_s", 1.0)), 0.2,
                                          key=K("v_every"))
    vv["confirm_frames"] = b.number_input("Vi phạm kéo dài ≥ N khung mới ghi", 1, 30, int(vv.get("confirm_frames", 3)),
                                          key=K("v_conf"))
    vv["clear_frames"] = cc.number_input("Hết vi phạm ≥ N khung mới đóng", 1, 30, int(vv.get("clear_frames", 3)),
                                         key=K("v_clear"))
    st.divider()
    al, pr = new.setdefault("alerts", {}), new.setdefault("privacy", {})
    a, b, cc = st.columns(3)
    al["on_screen"] = a.toggle("Thông báo trên màn hình", al.get("on_screen", True), key=K("al_scr"))
    al["sound"] = b.toggle("Âm thanh cảnh báo", al.get("sound", True), key=K("al_snd"))
    al["telegram"] = cc.toggle("Gửi Telegram", al.get("telegram", False), key=K("al_tg"),
                               help="Cần TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID trong file .env")
    if cc.button("Gửi thử Telegram"):
        from core.events import send_telegram
        err = send_telegram("LabSafe: tin nhắn thử")
        st.error(err) if err else st.success("Đã gửi")
    st.divider()
    a, b, cc = st.columns(3)
    pr["blur_people"] = a.toggle("Làm mờ người trong ảnh nhật ký", pr.get("blur_people", True), key=K("pr_blur"))
    pr["blur_in_display"] = b.toggle("Làm mờ người trên màn hình", pr.get("blur_in_display", False), key=K("pr_disp"))
    new["vlm"]["blur_people_before_send"] = cc.toggle("Làm mờ người trước khi gửi Gemini",
                                                      c["vlm"].get("blur_people_before_send", True), key=K("pr_vlm"))

# ================================================================ YAML
with tab5:
    st.caption("Sửa trực tiếp toàn bộ bảng kiểm. Hệ thống kiểm tra hợp lệ trước khi lưu.")
    txt = st.text_area("checklist.yaml", yaml.safe_dump(c, allow_unicode=True, sort_keys=False, width=110),
                       height=500, key=K("yaml"))
    if st.button("Áp dụng YAML"):
        try:
            save_checklist(yaml.safe_load(txt))
            deleted.clear()
            _reset_widgets()
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"YAML không hợp lệ: {e}")

# ================================================================ lưu
changed = new != c
with st.sidebar:
    st.divider()
    if changed:
        st.warning("Có thay đổi chưa lưu")
    if st.button("💾 Lưu bảng kiểm", type="primary", disabled=not changed, width="stretch"):
        try:
            save_checklist(new)
            deleted.clear()
            _reset_widgets()
            st.toast("Đã lưu bảng kiểm", icon="✅")
            st.rerun()
        except ValueError as e:
            st.error(str(e))
    if st.button("↩️ Bỏ thay đổi", disabled=not changed, width="stretch"):
        deleted.clear()
        _reset_widgets()
        st.rerun()
    with st.popover("Khôi phục mặc định", width="stretch"):
        st.write("Ghi đè bảng kiểm bằng `checklist.default.yaml` (cấu hình dùng trong bài báo + lọc chai trên bình).")
        if st.button("Khôi phục"):
            reset_checklist()
            deleted.clear()
            _reset_widgets()
            st.rerun()
