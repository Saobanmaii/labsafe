"""Bộ luật cấu hình được: chạy các tiêu chí trong bảng kiểm trên danh sách detection + vùng.

Mỗi tiêu chí trả về một CriterionResult gồm kết luận, đại lượng đo được, ngưỡng, lời giải thích
và CHỈ SỐ các detection làm bằng chứng — để giao diện khoanh đúng vật gây vi phạm.
Với cấu hình mặc định, kết quả trùng với src/rules.py dùng trong bài báo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union


@dataclass
class CriterionResult:
    id: str
    name: str
    group: str
    severity: str
    status: int | None                 # 1 = vi phạm, 0 = đạt, None = không đánh giá được
    engine: str = "rules"              # rules | vlm
    explanation: str = ""
    metrics: dict = field(default_factory=dict)
    evidence: list[int] = field(default_factory=list)       # chỉ số trong danh sách detection
    zone: str | None = None
    vlm_boxes: list[dict] = field(default_factory=list)     # bằng chứng do Gemini khoanh
    rule_status: int | None = None
    vlm_status: int | None = None
    vlm_reason: str = ""


def _union(polys):
    shapes = [Polygon(p).buffer(0) for p in polys if len(p) >= 3]
    return unary_union(shapes) if shapes else None


def _center(xyxy):
    x1, y1, x2, y2 = xyxy
    return (x1 + x2) / 2, (y1 + y2) / 2


def zones_to_px(cam_zones: dict, w: int, h: int) -> dict:
    return {zt: [[(x * w, y * h) for x, y in poly] for poly in polys] for zt, polys in cam_zones.items()}


def evaluate(criteria: list[dict], dets: list[dict], zones_px: dict, zone_names: dict) -> list[CriterionResult]:
    out = []
    for c in criteria:
        r = CriterionResult(id=c["id"], name=c["name"], group=c["group"], severity=c["severity"],
                            status=None, zone=c.get("zone"))
        fn = {"zone_occupancy": _occupancy, "count_in_zone": _count, "zone_visibility": _visibility}[c["type"]]
        zname = zone_names.get(c.get("zone"), c.get("zone"))
        fn(c, dets, zones_px, r, zname)
        r.rule_status = r.status
        out.append(r)
    return out


def _missing_zone(r: CriterionResult, zname: str):
    r.status = None
    r.explanation = f"Camera này chưa vẽ vùng «{zname}» nên không đánh giá được."


def _occupancy(c, dets, zones_px, r, zname):
    zone = _union(zones_px.get(c["zone"], []))
    if zone is None or zone.area == 0:
        return _missing_zone(r, zname)
    p = c.get("params", {})
    frac, thr = float(p.get("footprint_frac", 0.25)), float(p.get("threshold", 0.05))
    classes = set(c.get("classes", []))
    feet = []
    for i, d in enumerate(dets):
        if d["cls"] in classes:
            x1, y1, x2, y2 = d["xyxy"]
            f = box(x1, y2 - frac * (y2 - y1), x2, y2)
            if f.intersects(zone) and f.intersection(zone).area > 0:
                r.evidence.append(i)
            feet.append(f)
    occ = unary_union(feet).intersection(zone).area / zone.area if feet else 0.0
    r.status = int(occ >= thr)
    r.metrics = {"tỷ lệ chiếm dụng": round(occ, 4), "ngưỡng": thr}
    names = ", ".join(sorted({dets[i]["cls"] for i in r.evidence})) or "không có"
    r.explanation = (f"Vật cản chiếm {occ:.1%} diện tích «{zname}» "
                     f"({'≥' if r.status else '<'} ngưỡng {thr:.0%}). Vật trong vùng: {names}.")


def _count(c, dets, zones_px, r, zname):
    p = c.get("params", {})
    k = int(p.get("min_count", 1))
    classes = set(c.get("classes", []))
    if c.get("zone"):
        zone = _union(zones_px.get(c["zone"], []))
        if zone is None:
            return _missing_zone(r, zname)
        r.evidence = [i for i, d in enumerate(dets)
                      if d["cls"] in classes and zone.contains(Point(_center(d["xyxy"])))]
        where = f"trong «{zname}»"
    else:
        r.evidence = [i for i, d in enumerate(dets) if d["cls"] in classes]
        where = "trong ảnh"
    n = len(r.evidence)
    r.status = int(n >= k)
    r.metrics = {"số lượng": n, "ngưỡng": k}
    labels = sorted(dets[i]["cls"] for i in r.evidence)
    detail = (": " + ", ".join(labels)) if labels else ""
    r.explanation = f"Phát hiện {n} vật {where}{detail} ({'≥' if r.status else '<'} ngưỡng {k})."


def _visibility(c, dets, zones_px, r, zname):
    zone = _union(zones_px.get(c["zone"], []))
    if zone is None or zone.area == 0:
        return _missing_zone(r, zname)
    p = c.get("params", {})
    vmin, omax = float(p.get("min_visible", 0.5)), float(p.get("max_occlusion", 1 / 3))
    target = c["target"]
    occluders = set(c.get("classes", []))
    tgt = [(i, box(*d["xyxy"])) for i, d in enumerate(dets) if d["cls"] == target]
    tgt = [(i, b) for i, b in tgt if b.intersects(zone)]
    vis = unary_union([b for _, b in tgt]).intersection(zone).area / zone.area if tgt else 0.0
    occ_list = [(i, box(*d["xyxy"])) for i, d in enumerate(dets) if d["cls"] in occluders]
    occ_in = [(i, b) for i, b in occ_list if b.intersection(zone).area > 0]
    occ = unary_union([b for _, b in occ_list]).intersection(zone).area / zone.area if occ_list else 0.0
    vis = min(vis, 1.0)
    r.status = int((not tgt) or vis < vmin or occ >= omax)
    r.evidence = [i for i, _ in tgt] + [i for i, _ in occ_in]
    r.metrics = {"tỷ lệ nhìn thấy": round(vis, 4), "tỷ lệ bị che": round(occ, 4),
                 "ngưỡng thấy": vmin, "ngưỡng che": round(omax, 4)}
    if not tgt:
        r.explanation = f"Không thấy «{target}» trong «{zname}» (bị che hoàn toàn hoặc không ở vị trí)."
    elif occ >= omax:
        by = ", ".join(sorted({dets[i]["cls"] for i, _ in occ_in}))
        r.explanation = f"«{zname}» bị che {occ:.0%} (≥ {omax:.0%}) bởi: {by}."
    elif vis < vmin:
        r.explanation = f"Chỉ nhìn thấy {vis:.0%} «{target}» trong vùng (< {vmin:.0%})."
    else:
        r.explanation = f"Nhìn thấy {vis:.0%} «{target}», bị che {occ:.0%} — thông thoáng."


def scores(results: list[CriterionResult], cfg: dict) -> dict:
    """Điểm an toàn (0–100) có trọng số theo mức độ, tổng và theo từng nhóm tiêu chí."""
    w = {k: v.get("weight", 1) for k, v in cfg["severity"].items()}

    def pct(rs):
        rs = [r for r in rs if r.status is not None]
        tot = sum(w.get(r.severity, 1) for r in rs)
        if not tot:
            return None
        return round(100 * sum(w.get(r.severity, 1) for r in rs if r.status == 0) / tot)

    groups = {}
    for gid, gname in cfg["groups"].items():
        rs = [r for r in results if r.group == gid]
        if rs:
            groups[gid] = {"name": gname, "score": pct(rs),
                           "violations": sum(1 for r in rs if r.status == 1), "total": len(rs)}
    return {"overall": pct(results), "groups": groups,
            "violations": sum(1 for r in results if r.status == 1),
            "evaluated": sum(1 for r in results if r.status is not None)}
