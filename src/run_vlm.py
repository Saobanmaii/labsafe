"""Cột 3 — Mô hình ngôn ngữ–thị giác (VLM), không huấn luyện, 3 biến thể prompt -> results_vlm.csv

    # Gemini (cần biến môi trường GEMINI_API_KEY)
    python src/run_vlm.py --backend gemini --model gemini-2.5-flash
    # Claude (cần ANTHROPIC_API_KEY; gói Claude Pro KHÔNG dùng được cho API)
    python src/run_vlm.py --backend claude --model claude-haiku-4-5

Chạy lại sẽ bỏ qua những (ảnh, prompt, lần chạy) đã có -> bị ngắt giữa chừng thì cứ chạy lại.
"""
import argparse
import base64
import csv
import json
import os
import re
import time
from pathlib import Path

from common import CRITERIA, OUT, ROOT, jpeg_bytes_resized, list_images

# Đọc API key từ file .env ở thư mục gốc (dòng dạng GEMINI_API_KEY=...), nếu có
if (ROOT / ".env").exists():
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            if v.strip():
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

# ---- 3 biến thể prompt: chi tiết / rút gọn / chi tiết nhưng đảo thứ tự tiêu chí ----
CRIT_TEXT = {
    "C1": "C1 - Obstruction in walkway: VIOLATED if at least one object of backpack size or larger "
          "(chair, backpack, box, bag, bucket, ...) is placed on the floor within the walkway, narrowing "
          "or blocking it. Ignore people and objects fully under benches.",
    "C2": "C2 - Personal items on lab bench: VIOLATED if 3 or more personal items (phone, personal laptop, "
          "backpack, handbag, wallet, books or notebooks, jacket, hat) are on the lab bench surfaces. Lab "
          "equipment, tools, fixed lab computers and instruction sheets do not count.",
    "C3": "C3 - Fire extinguisher obstructed: VIOLATED if the fire extinguisher is covered by about one "
          "third or more, an object in front makes it hard to reach, or its spot is empty. PASSES if it is "
          "clearly visible and freely accessible.",
    "C4": "C4 - Food or drink: VIOLATED if any food or drink is visible (cups, mugs, drinking bottles, cans, "
          "lunch boxes, snacks, fruit), even partly consumed. Chemical bottles, reagent containers, lab "
          "glassware and beakers do NOT count.",
}
HEADER = ("You are a laboratory safety inspector. Assess the photo of a university laboratory against the "
          "criteria below. For each criterion output 1 if it is VIOLATED and 0 if it PASSES. Judge only "
          "from what is visible in the photo.\n\n")
FOOTER = ('\n\nReturn only JSON: {"C1": 0 or 1, "C2": 0 or 1, "C3": 0 or 1, "C4": 0 or 1, '
          '"reason": "one short sentence per criterion"}')
PROMPTS = {
    "P1": HEADER + "\n".join(CRIT_TEXT[c] for c in ["C1", "C2", "C3", "C4"]) + FOOTER,
    "P2": ("Lab safety check of this photo. Answer 1 = violation, 0 = OK.\n"
           "C1: an object (backpack-size or larger) on the floor in the walkway.\n"
           "C2: 3 or more personal items on lab benches.\n"
           "C3: fire extinguisher blocked, covered by 1/3 or more, or missing.\n"
           "C4: any food or drink visible (lab glassware and chemical bottles do not count).") + FOOTER,
    "P3": HEADER + "\n".join(CRIT_TEXT[c] for c in ["C4", "C3", "C2", "C1"]) + FOOTER,
}
SCHEMA = {
    "type": "object",
    "properties": {**{c: {"type": "integer", "enum": [0, 1]} for c in CRITERIA}, "reason": {"type": "string"}},
    "required": [*CRITERIA, "reason"],
    "additionalProperties": False,
}


class AllKeysExhausted(Exception):
    pass


def make_gemini(model):
    from google import genai
    from google.genai import types
    # Nhiều key (GEMINI_API_KEY, GEMINI_API_KEY_2, ...): key nào hết hạn mức trong ngày thì chuyển key sau
    names = sorted(k for k in os.environ if k.startswith("GEMINI_API_KEY") and os.environ[k].strip())
    clients = [genai.Client(api_key=os.environ[k]) for k in names]
    state = {"i": 0}
    print(f"Gemini: {len(clients)} key ({', '.join(names)})")

    def call(jpeg, prompt):
        while True:
            try:
                r = clients[state["i"]].models.generate_content(
                    model=model,
                    contents=[types.Part.from_bytes(data=jpeg, mime_type="image/jpeg"), prompt],
                    config=types.GenerateContentConfig(temperature=0.0, response_mime_type="application/json"),
                )
                break
            except Exception as e:
                msg = str(e)
                if "RESOURCE_EXHAUSTED" in msg and "PerDay" in msg:
                    print(f"[!] {names[state['i']]} hết hạn mức ngày")
                    state["i"] += 1
                    if state["i"] >= len(clients):
                        raise AllKeysExhausted("tất cả key đã hết hạn mức ngày") from e
                    continue
                raise
        u = r.usage_metadata
        return r.text, getattr(u, "prompt_token_count", None), getattr(u, "candidates_token_count", None)
    return call


def make_claude(model):
    import anthropic
    client = anthropic.Anthropic()
    output_config = {"format": {"type": "json_schema", "schema": SCHEMA}}
    if "haiku" not in model:  # effort không áp dụng cho Haiku 4.5
        output_config["effort"] = "low"

    def call(jpeg, prompt):
        # Không bật fallback sang model khác: mỗi cột kết quả phải đến từ đúng một model.
        r = client.messages.create(
            model=model, max_tokens=4000, output_config=output_config,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                             "data": base64.standard_b64encode(jpeg).decode()}},
                {"type": "text", "text": prompt},
            ]}],
        )
        if r.stop_reason == "refusal":
            raise RuntimeError("refusal")
        text = next((b.text for b in r.content if b.type == "text"), "")
        return text, r.usage.input_tokens, r.usage.output_tokens
    return call


def parse(text):
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        obj = json.loads(m.group(0))
    return {c: int(obj[c]) for c in CRITERIA}, str(obj.get("reason", ""))


ap = argparse.ArgumentParser()
ap.add_argument("--backend", choices=["gemini", "claude"], default="gemini")
ap.add_argument("--model", default="gemini-2.5-flash")
ap.add_argument("--prompts", default="P1,P2,P3")
ap.add_argument("--runs", type=int, default=1, help="số lần lặp mỗi (ảnh, prompt) để đo tính ngẫu nhiên")
ap.add_argument("--sleep", type=float, default=4.0, help="giây nghỉ giữa các lần gọi (gói miễn phí Gemini)")
ap.add_argument("--limit", type=int, default=0, help="chỉ chạy N ảnh đầu (thử nghiệm)")
ap.add_argument("--images", default=None, help="thư mục ảnh (mặc định data/images)")
ap.add_argument("--out", default=str(OUT / "results_vlm.csv"))
args = ap.parse_args()

call = make_gemini(args.model) if args.backend == "gemini" else make_claude(args.model)
fields = ["image", "backend", "model", "prompt", "run", *CRITERIA, "reason", "latency_s", "in_tokens", "out_tokens", "error"]

done = set()
if os.path.exists(args.out):
    with open(args.out, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if not r["error"]:
                done.add((r["image"], r["model"], r["prompt"], r["run"]))

OUT.mkdir(parents=True, exist_ok=True)
new_file = not os.path.exists(args.out)
images = (list_images(Path(args.images)) if args.images else list_images())[: args.limit or None]
with open(args.out, "a", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    if new_file:
        w.writeheader()
    for p in images:
        jpeg = jpeg_bytes_resized(p)
        for pid in args.prompts.split(","):
            for run in range(args.runs):
                if (p.name, args.model, pid, str(run)) in done:
                    continue
                row = {"image": p.name, "backend": args.backend, "model": args.model, "prompt": pid, "run": run}
                for attempt in range(5):
                    try:
                        t0 = time.perf_counter()
                        text, tin, tout = call(jpeg, PROMPTS[pid])
                        verdict, reason = parse(text)
                        row.update(verdict, reason=reason, latency_s=round(time.perf_counter() - t0, 2),
                                   in_tokens=tin, out_tokens=tout, error="")
                        break
                    except AllKeysExhausted as e:
                        print(f"\n[!] Dừng: {e}. Chạy lại lệnh sau khi hạn mức reset hoặc thêm key; phần đã xong được giữ.")
                        raise SystemExit(1)
                    except Exception as e:
                        row["error"] = f"{type(e).__name__}: {e}"[:300]
                        time.sleep(min(60, 5 * 2 ** attempt))
                w.writerow(row)
                f.flush()
                print(f"{p.name} {pid} run{run}: " + (row["error"] or " ".join(f"{c}={row[c]}" for c in CRITERIA)))
                time.sleep(args.sleep)
print(f"\nĐã lưu {args.out}")
