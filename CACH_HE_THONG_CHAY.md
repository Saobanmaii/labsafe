# Hệ thống chạy thế nào (môn Thị giác máy tính)

Tài liệu này đi theo đúng thứ tự hệ thống chạy: **chuẩn bị một lần**, rồi **mỗi ảnh đi qua 5 bước**, cuối cùng là **đánh giá**. Mỗi bước ghi rõ file nào làm, viết bằng gì, làm thế nào.

Toàn bộ viết bằng **Python 3.12**, mã nằm trong thư mục `src/`. Môi trường chạy: `D:\Study\venv-nckh` (có PyTorch dùng GPU).

---

## Sơ đồ tổng thể

```
 CHUẨN BỊ (làm 1 lần)                       CHẠY (mỗi ảnh)                          ĐÁNH GIÁ
 ─────────────────────                      ───────────────                         ────────
 A. Huấn luyện mô hình bình    ──┐
    prep_fireart.py                │
    train_extinguisher.py          │      ┌─► 1. Đọc ảnh, xác định góc chụp
    → models/extinguisher_best.pt  │      │      common.py
                                   ├──────┤
 B. Vẽ vùng cho mỗi góc            │      ├─► 2. YOLO tìm đồ vật (3 mô hình)
    tools/zone_tool.html           │      │      run_rules.py
    → data/zones.json            ──┘      │
                                          ├─► 3. Nạp vùng của góc đó
 C. Định nghĩa tiêu chí + ngưỡng          │      common.py
    RUBRIC.md, rules.py (PARAMS)  ────────┤
                                          ├─► 4. Bộ luật → C1..C4                    evaluate.py
                                          │      rules.py                     ──►  so với người chấm
                                          │                                         → bảng κ, biểu đồ,
                                          └─► 5. Vẽ ảnh bằng chứng + ghi CSV          danh sách ca sai
                                                 rules.py, run_rules.py
                                                 → outputs/results_rule.csv
                                                 → outputs/annotated/*.jpg

                     (song song)  Gemini chấm trực tiếp: run_vlm.py → outputs/results_vlm.csv
```

---

## PHẦN A. Chuẩn bị (chỉ làm một lần)

### A1. Huấn luyện mô hình bình chữa cháy (phần "customized model")

**Vì sao:** YOLO có sẵn học trên bộ COCO 80 lớp, không có lớp "bình chữa cháy". Phải tự dạy.

| Bước | File | Làm gì |
|---|---|---|
| Chuẩn bị dữ liệu | `src/prep_fireart.py` | Đọc bộ ảnh Fire-ART (15 loại thiết bị phòng cháy). Chỉ giữ lớp bình chữa cháy. Nhãn gốc là đa giác, đổi thành hộp chữ nhật (định dạng YOLO). Thêm ảnh không có bình làm ảnh âm. Chia 287 ảnh huấn luyện / 71 ảnh kiểm tra. |
| Huấn luyện | `src/train_extinguisher.py` | Lấy YOLO11n đã học COCO, huấn luyện tiếp trên dữ liệu trên. Ảnh 640 px, batch 8, tự dừng khi 10 epoch liền không tiến bộ. |
| Kết quả | `models/extinguisher_best.pt` | File mô hình. mAP@0,5 = 0,80 (`outputs/train_metrics.json`) |

**Viết thế nào:** dùng thư viện **Ultralytics**. Phần huấn luyện thực chất chỉ là:

```python
model = YOLO("yolo11n.pt")                        # mô hình gốc đã học COCO
model.train(data="data.yaml", imgsz=640, batch=8, patience=10, device=0)
```

### A2. Vẽ vùng chức năng (thay cho semantic segmentation)

**Vì sao:** YOLO chỉ nói "có cái ghế ở toạ độ này", không biết ghế đó nằm trên lối đi hay sát bàn. Cần cho máy biết vùng nào là gì.

| File | Làm gì |
|---|---|
| `tools/zone_tool.html` | Trang web chạy trong Chrome. Mở ảnh, click các góc để vẽ đa giác: **lối đi** (xanh lá), **mặt bàn** (xanh dương), **chỗ đặt bình** (đỏ). Vẽ 1 lần cho mỗi góc camera; ảnh nào lệch khung thì tick "vẽ riêng". |
| `data/zones.json` | Kết quả. Toạ độ lưu dạng tỉ lệ 0–1 nên dùng được cho ảnh mọi kích thước. |

Ví dụ một dòng trong `zones.json`:
```json
"v1": { "aisle": [[[0.01,0.80],[0.25,0.75],...]], "bench": [...], "extinguisher": [...] }
```

**Viết thế nào:** HTML + JavaScript thuần, vẽ trên `<canvas>`, không cần cài gì.

### A3. Định nghĩa tiêu chí và ngưỡng (phần "bảng kiểm")

| File | Làm gì |
|---|---|
| `RUBRIC.md` | Định nghĩa bằng lời 4 tiêu chí (dùng chung cho người chấm, luật, Gemini). |
| `src/rules.py`, phần đầu | Bảng kiểm dạng code: lớp nào tính là vật cản, đồ cá nhân, đồ ăn uống; các ngưỡng. |

```python
C1_OBSTACLES  = {"chair", "backpack", "suitcase", "handbag", "bench", "cardboard box"}
C2_PERSONAL   = {"cell phone", "laptop", "backpack", "handbag", "book"}
C4_FOOD_DRINK = {"cup", "bottle", "wine glass", "bowl", "banana", "apple", ...}
PARAMS = {
    "tau_aisle": 0.05,       # C1: chiếm >= 5% lối đi là vi phạm
    "min_personal": 3,       # C2: >= 3 đồ cá nhân trên bàn
    "tau_visible": 0.5,      # C3: thấy < 50% bình là vi phạm
    "tau_occlusion": 1/3,    # C3: bị che >= 1/3 là vi phạm
    "min_food": 1,           # C4: >= 1 đồ ăn uống
}
```

Đổi tiêu chí thì sửa ở đây. Đề yêu cầu "bảng kiểm cấu hình được" ở mức cao hơn: tách phần này ra file YAML và chỉnh trên giao diện (chưa làm).

---

## PHẦN B. Chạy hệ thống trên ảnh

**Lệnh chạy:**
```
D:\Study\venv-nckh\Scripts\python.exe src\run_rules.py
```
File chính: **`src/run_rules.py`**. Nó lặp qua từng ảnh trong `data/images/` và làm 5 bước:

### Bước 1. Đọc ảnh, xác định góc chụp — `src/common.py`

- `load_image_bgr()`: đọc ảnh bằng Pillow, **xoay đúng chiều theo EXIF** (ảnh điện thoại hay bị xoay), đổi sang định dạng OpenCV.
- `view_of()`: lấy góc chụp từ tên file, ví dụ `v2b_07.jpg` → góc `v2b`.

### Bước 2. YOLO tìm đồ vật — `src/run_rules.py`

Chạy **3 mô hình** trên cùng một ảnh, gộp kết quả lại:

| Mô hình | Nguồn | Tìm gì |
|---|---|---|
| `yolo11s.pt` | Có sẵn (COCO) | ghế, balo, túi, cốc, chai, điện thoại, laptop, sách… |
| `models/extinguisher_best.pt` | **Nhóm tự huấn luyện** | bình chữa cháy |
| `yolov8s-worldv2.pt` (YOLO-World) | Có sẵn, gõ tên lớp bằng chữ | "cardboard box" (thùng carton, COCO không có) |

Mỗi vật tìm được là một dòng: `{tên lớp, độ tin cậy, toạ độ khung}`. Ngưỡng tin cậy 0,30.

### Bước 3. Nạp vùng của góc đó — `src/common.py`

- `load_zones()`: đọc `data/zones.json`.
- Ưu tiên vùng vẽ riêng của ảnh (nếu có), không thì dùng vùng của góc.
- `zones_to_px()`: đổi toạ độ tỉ lệ 0–1 thành toạ độ điểm ảnh.

### Bước 4. Bộ luật quyết định Đạt/Vi phạm — `src/rules.py`, hàm `evaluate_rules()`

Đây là phần **rule engine**. Dùng thư viện **Shapely** để tính giao, hợp các đa giác:

| Tiêu chí | Cách tính |
|---|---|
| **C1** | Lấy phần đáy (25%) của khung mỗi vật cản (coi như chân chạm sàn). Tính tỉ lệ diện tích lối đi bị chiếm: `R = (hợp các đáy ∩ lối đi) / lối đi`. **R ≥ 5% → vi phạm.** |
| **C2** | Đếm đồ cá nhân có **tâm khung nằm trong vùng bàn**. **≥ 3 → vi phạm.** |
| **C3** | Trong vùng đặt bình: tính phần bình nhìn thấy (V) và phần bị vật khác phủ (O). **Không thấy bình, V < 50% hoặc O ≥ 1/3 → vi phạm.** |
| **C4** | **Có ít nhất 1** cốc, chai, đồ ăn → vi phạm. |

Hàm trả về kết luận C1–C4 kèm các con số trung gian (R, số đồ cá nhân, V, O…) để giải thích được vì sao.

### Bước 5. Vẽ ảnh bằng chứng và ghi kết quả — `rules.py` (`draw_result`), `run_rules.py`

- Vẽ lên ảnh: các vùng (tô màu mờ), khung từng vật kèm tên và độ tin cậy, 4 dòng kết luận ở góc trên. Đây là phần **"kết quả gắn với vùng bằng chứng cụ thể"** của đề.
- Ghi ra:

| File đầu ra | Nội dung |
|---|---|
| `outputs/annotated/*.jpg` | Ảnh bằng chứng, 1 ảnh cho mỗi ảnh đầu vào |
| `outputs/results_rule.csv` | Mỗi ảnh 1 dòng: C1–C4, R, số đồ cá nhân, V, O, tên đồ ăn, thời gian xử lý, danh sách vật tìm được |
| `outputs/results_rule_meta.json` | Cấu hình đã dùng (mô hình, ngưỡng, GPU, thời gian trung bình) |

Tốc độ: khoảng **0,13 giây/ảnh** trên GPU laptop MX350.

---

## PHẦN C. Hướng thứ hai: Gemini chấm trực tiếp — `src/run_vlm.py`

**Lệnh:** `python src\run_vlm.py --model gemini-3.5-flash`

1. Thu nhỏ ảnh về cạnh dài 1568 px (`jpeg_bytes_resized()` trong `common.py`).
2. Gửi ảnh + câu hỏi (prompt) mô tả 4 tiêu chí qua **API Gemini** (thư viện `google-genai`). API key đọc từ file `.env`.
3. Bắt Gemini trả lời dạng JSON: `{"C1": 0/1, ..., "reason": "lý do"}`.
4. Có 3 kiểu câu hỏi (P1 chi tiết, P2 rút gọn, P3 đảo thứ tự) để xem kết quả có ổn định không.
5. Ghi ra `outputs/results_vlm.csv`. Hết lượt miễn phí thì tự đổi sang key khác; chạy lại thì tự bỏ qua ảnh đã xong.

Phần này đáp ứng ý "có thể sử dụng API" của mức Baseline, và đóng vai **multi-label classifier** (một ảnh → 4 nhãn) mà không cần huấn luyện.

---

## PHẦN D. Đánh giá so sánh — `src/evaluate.py`

**Lệnh:** `python src\evaluate.py`

1. Đọc nhãn 3 người chấm (`data/labels/rater1-3.csv`). Ô nào 2/3 người nói vi phạm thì đáp án là vi phạm.
2. Đo người với người đồng ý đến đâu (Fleiss' κ).
3. So từng hướng máy với đáp án: độ khớp, Cohen's κ, khoảng tin cậy 95% (bootstrap), F1, số ca báo nhầm/bỏ sót. **Tính riêng từng tiêu chí** (đúng ý "đánh giá riêng từng nhóm tiêu chí" của mức 3).
4. Ghi ra `outputs/`: bảng `table_*.csv` / `.tex`, biểu đồ `fig_kappa.png`, danh sách ca sai `errors.csv`.

Thư viện: scikit-learn (κ, F1), pandas, NumPy, Matplotlib.

---

## Các file phụ trợ

| File | Làm gì |
|---|---|
| `src/common.py` | Hàm dùng chung: đường dẫn thư mục, đọc/ghi ảnh (an toàn với tên thư mục tiếng Việt), đọc vùng |
| `src/test_rules.py` | Kiểm thử bộ luật bằng các ví dụ tính tay (18%, 8%, 16%) |
| `src/rename_photos.py` | Đổi tên ảnh chụp thành `v1_01.jpg`, `v2a_03.jpg`… |
| `src/blur_people.py` | Làm mờ người trong ảnh (ẩn danh) bằng YOLO lớp "person" |
| `src/preview_zones.py` | Vẽ vùng lên ảnh để kiểm tra vùng vẽ đúng chưa |
| `src/make_rater_pack.py`, `src/import_labels.py` | Đóng gói phiếu chấm Excel, đọc phiếu nhận về |
| `src/make_detector_figure.py` | Hình so sánh 3 bộ phát hiện bình chữa cháy |
| `requirements.txt` | Danh sách thư viện cần cài |

---

## Đối chiếu nhanh với đề

| Đề yêu cầu | Phần nào trong hệ thống |
|---|---|
| Phân tích ảnh phát hiện dấu hiệu bố trí, vệ sinh, an toàn | Phần B (YOLO + luật), Phần C (Gemini) |
| Kết quả gắn với tiêu chí và vùng bằng chứng | Bước 5: `outputs/annotated/` |
| YOLOv8 / object detection | Bước 2: YOLO11, YOLO-World (YOLOv8) |
| Semantic segmentation | Chưa; thay bằng vùng vẽ tay (A2) |
| Multi-label classifier | Gemini (Phần C) |
| Rule engine | Bước 4: `rules.py` |
| Customized model | A1: mô hình bình chữa cháy |
| Đánh giá so sánh, đánh giá riêng từng tiêu chí | Phần D |
| Có thể dùng API | Phần C: API Gemini |
| Bảng kiểm cấu hình được | Một phần: `PARAMS` trong `rules.py`, `zones.json`. Chưa có file YAML/giao diện |
| Cảnh báo theo vùng nguy cơ | Một phần: luật tính theo vùng, ảnh ghi VIOLATION. Chưa có cảnh báo thật |
| Ghi nhận sự kiện kèm ảnh ẩn danh | Chưa (có sẵn `blur_people.py`) |
| Video | Chưa |
| Dashboard / demo | Chưa |
