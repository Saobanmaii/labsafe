"""Nhật ký sự kiện (SQLite) kèm ảnh bằng chứng đã ẩn danh, bộ lọc thời gian cho video, kênh cảnh báo."""
from __future__ import annotations

import json
import os
import sqlite3
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

from .config import DB_FILE, EVENT_DIR, ROOT, load_env
from .render import save_jpg

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    camera        TEXT,
    source        TEXT,      -- image | video | webcam | stream
    source_name   TEXT,
    criterion     TEXT,
    criterion_name TEXT,
    grp           TEXT,
    grp_name      TEXT,
    severity      TEXT,
    zone          TEXT,
    engine        TEXT,
    explanation   TEXT,
    metrics       TEXT,
    started_at    TEXT,
    ended_at      TEXT,
    status        TEXT,      -- open | closed
    ack           INTEGER DEFAULT 0,
    note          TEXT DEFAULT '',
    image_path    TEXT,      -- ảnh bằng chứng đã làm mờ người (tương đối với thư mục đề tài)
    people_blurred INTEGER DEFAULT 0,
    video_t0      REAL,      -- giây trong video lúc bắt đầu / kết thúc vi phạm (nguồn tệp video)
    video_t1      REAL
);
"""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class EventStore:
    def __init__(self, path: Path = DB_FILE):
        self.path = path
        with self._conn() as c:
            c.executescript(SCHEMA)
            cols = {r[1] for r in c.execute("PRAGMA table_info(events)")}
            for col in ("video_t0", "video_t1"):
                if col not in cols:
                    c.execute(f"ALTER TABLE events ADD COLUMN {col} REAL")

    def _conn(self):
        return sqlite3.connect(self.path, timeout=10)

    def save_image(self, img, prefix: str) -> str:
        day = datetime.now().strftime("%Y%m%d")
        p = EVENT_DIR / day / f"{prefix}_{datetime.now():%H%M%S}_{uuid.uuid4().hex[:6]}.jpg"
        save_jpg(p, img)
        return str(p.relative_to(ROOT)).replace("\\", "/")

    def open(self, *, camera, source, source_name, r, cfg, image_path, people_blurred, closed=False,
             t_video: float | None = None) -> int:
        now = _now()
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO events (camera, source, source_name, criterion, criterion_name, grp, grp_name, severity,"
                " zone, engine, explanation, metrics, started_at, ended_at, status, image_path, people_blurred, video_t0)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (camera, source, source_name, r.id, r.name, r.group, cfg["groups"].get(r.group, r.group),
                 r.severity, cfg["zone_types"].get(r.zone, {}).get("name", r.zone) if r.zone else "Toàn ảnh",
                 r.engine, r.explanation if r.engine == "rules" else (r.vlm_reason or r.explanation),
                 json.dumps(r.metrics, ensure_ascii=False), now, now if closed else None,
                 "closed" if closed else "open", image_path, people_blurred, t_video))
            return cur.lastrowid

    def close(self, event_id: int, t_video: float | None = None) -> None:
        with self._conn() as c:
            c.execute("UPDATE events SET status='closed', ended_at=?, video_t1=? WHERE id=?",
                      (_now(), t_video, event_id))

    def close_all_open(self) -> None:
        with self._conn() as c:
            c.execute("UPDATE events SET status='closed', ended_at=? WHERE status='open'", (_now(),))

    def ack(self, ids: list[int], note: str = "") -> None:
        with self._conn() as c:
            c.executemany("UPDATE events SET ack=1, note=? WHERE id=?", [(note, i) for i in ids])

    def delete_all(self) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM events")
        for p in EVENT_DIR.rglob("*.jpg"):
            p.unlink()

    def df(self) -> pd.DataFrame:
        with self._conn() as c:
            d = pd.read_sql_query("SELECT * FROM events ORDER BY id DESC", c)
        for col in ("started_at", "ended_at"):
            d[col] = pd.to_datetime(d[col], errors="coerce")
        d["duration_s"] = (d["ended_at"] - d["started_at"]).dt.total_seconds()
        for col in ("video_t0", "video_t1"):
            d[col] = pd.to_numeric(d[col], errors="coerce")
        vdur = d["video_t1"] - d["video_t0"]
        d["duration_s"] = vdur.where(vdur.notna(), d["duration_s"])
        return d


class TemporalFilter:
    """Chống báo động giả trên video: vi phạm phải kéo dài `confirm` khung liên tiếp mới mở sự kiện,
    và phải hết vi phạm `clear` khung liên tiếp mới đóng sự kiện."""

    def __init__(self, confirm: int = 3, clear: int = 3):
        self.confirm, self.clear = max(1, confirm), max(1, clear)
        self.state: dict[str, dict] = {}

    def update(self, statuses: dict[str, int | None]) -> tuple[list[str], list[str]]:
        opened, closed = [], []
        for cid, st in statuses.items():
            s = self.state.setdefault(cid, {"active": False, "pos": 0, "neg": 0, "event": None})
            if st is None:
                continue
            if st == 1:
                s["pos"] += 1
                s["neg"] = 0
                if not s["active"] and s["pos"] >= self.confirm:
                    s["active"] = True
                    opened.append(cid)
            else:
                s["neg"] += 1
                s["pos"] = 0
                if s["active"] and s["neg"] >= self.clear:
                    s["active"] = False
                    closed.append(cid)
        return opened, closed

    def progress(self, cid: str) -> str:
        s = self.state.get(cid)
        if not s:
            return ""
        if s["active"]:
            return "đang vi phạm"
        if s["pos"]:
            return f"chờ xác nhận {s['pos']}/{self.confirm}"
        return ""


def send_telegram(text: str, image_file: Path | None = None) -> str | None:
    """Gửi cảnh báo qua Telegram nếu có TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID. Trả về lỗi (nếu có)."""
    load_env()
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return "Chưa cấu hình TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID trong .env"
    try:
        if image_file and image_file.exists():
            boundary = uuid.uuid4().hex
            body = b""
            for k, v in (("chat_id", chat), ("caption", text[:1000])):
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
            body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"e.jpg\"\r\n"
                     "Content-Type: image/jpeg\r\n\r\n").encode() + image_file.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
            req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendPhoto", data=body,
                                         headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        else:
            data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
            req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
        urllib.request.urlopen(req, timeout=10).read()
        return None
    except Exception as e:  # noqa: BLE001
        return f"Gửi Telegram lỗi: {e}"
