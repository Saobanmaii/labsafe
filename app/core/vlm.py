"""Hướng chấm điểm thứ hai: Gemini (mô hình ngôn ngữ–thị giác), không huấn luyện.

Prompt được sinh tự động từ bảng kiểm (vlm_description của từng tiêu chí), nên thêm tiêu chí mới
trên dashboard là Gemini chấm luôn. Gemini còn trả về khung bằng chứng (box_2d) cho mỗi vi phạm.
Kết quả được cache theo (ảnh, model, prompt) để không tốn hạn mức khi demo lại cùng một ảnh.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time

from .config import CACHE_DIR, load_env

CACHE_FILE = CACHE_DIR / "vlm_cache.json"


class VLMError(Exception):
    pass


def build_prompt(criteria: list[dict]) -> str:
    ids = [c["id"] for c in criteria]
    lines = "\n".join(f"{c['id']} - {' '.join(c['vlm_description'].split())}" for c in criteria)
    example = ", ".join(f'"{i}": 0 or 1' for i in ids)
    return (
        "You are a laboratory safety inspector. Assess the photo of a university laboratory against the "
        "criteria below. For each criterion output 1 if it is VIOLATED and 0 if it PASSES. Judge only "
        "from what is visible in the photo.\n\n" + lines + "\n\n"
        "Return only JSON with this structure:\n"
        "{" + example + ', "reasons": {' + ", ".join(f'"{i}": "one short sentence"' for i in ids) + "}, "
        '"evidence": [{"criterion": "<id>", "label": "<object>", "box_2d": [ymin, xmin, ymax, xmax]}]}\n'
        "In 'evidence' give a bounding box (coordinates normalized to 0-1000) for each object that causes a "
        "violation, and for the fire extinguisher if one is visible. Write reasons in Vietnamese."
    )


def available() -> bool:
    load_env()
    return any(k.startswith("GEMINI_API_KEY") and os.environ[k].strip() for k in os.environ)


def _cache_load() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _cache_save(c: dict) -> None:
    CACHE_FILE.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")


def _call_gemini(model: str, jpeg: bytes, prompt: str) -> str:
    from google import genai
    from google.genai import types

    load_env()
    names = sorted(k for k in os.environ if k.startswith("GEMINI_API_KEY") and os.environ[k].strip())
    if not names:
        raise VLMError("Chưa có GEMINI_API_KEY trong file .env")
    last = None
    for name in names:  # key nào hết hạn mức thì chuyển key sau
        try:
            # tối đa ~60 s mỗi key, không để thư viện tự thử lại lâu -> giao diện không bị treo
            client = genai.Client(api_key=os.environ[name], http_options=types.HttpOptions(
                timeout=60_000, retry_options=types.HttpRetryOptions(attempts=1)))
            r = client.models.generate_content(
                model=model,
                contents=[types.Part.from_bytes(data=jpeg, mime_type="image/jpeg"), prompt],
                config=types.GenerateContentConfig(temperature=0.0, response_mime_type="application/json"),
            )
            return r.text
        except Exception as e:  # noqa: BLE001
            last = e
            msg = str(e)
            if "RESOURCE_EXHAUSTED" in msg or "429" in msg or "503" in msg or "UNAVAILABLE" in msg:
                continue
            raise VLMError(f"{type(e).__name__}: {msg[:300]}") from e
    raise VLMError(f"Tất cả {len(names)} key Gemini đều hết hạn mức hoặc máy chủ bận. ({str(last)[:200]})")


def _parse(text: str, ids: list[str]) -> dict:
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise VLMError(f"Gemini trả về không phải JSON: {text[:200]}")
        obj = json.loads(m.group(0))
    if isinstance(obj, list) and obj:
        obj = obj[0]
    verdicts = {}
    for i in ids:
        v = obj.get(i)
        if isinstance(v, dict):
            v = v.get("violated", v.get("value"))
        verdicts[i] = None if v is None else int(v)
    reasons = obj.get("reasons") or {}
    if isinstance(reasons, str):
        reasons = {i: reasons for i in ids}
    boxes = []
    for e in obj.get("evidence") or []:
        try:
            ymin, xmin, ymax, xmax = (float(v) / 1000 for v in e["box_2d"])
            boxes.append({"criterion": str(e.get("criterion", "")), "label": str(e.get("label", "")),
                          "box": [max(0, xmin), max(0, ymin), min(1, xmax), min(1, ymax)]})
        except (KeyError, TypeError, ValueError):
            continue
    return {"verdicts": verdicts, "reasons": {i: str(reasons.get(i, "")) for i in ids}, "evidence": boxes}


def analyze(jpeg: bytes, criteria: list[dict], model: str, use_cache: bool = True) -> dict:
    prompt = build_prompt(criteria)
    ids = [c["id"] for c in criteria]
    key = hashlib.sha1(jpeg + model.encode() + prompt.encode()).hexdigest()
    cache = _cache_load()
    if use_cache and key in cache:
        return dict(cache[key], cached=True)
    t0 = time.perf_counter()
    text = _call_gemini(model, jpeg, prompt)
    out = _parse(text, ids)
    out.update(model=model, latency_s=round(time.perf_counter() - t0, 2), cached=False)
    cache[key] = out
    _cache_save(cache)
    return out
