# ROADMAP — Bài báo NCKH: Chấm điểm an toàn phòng thí nghiệm

> **Câu hỏi trung tâm:** Máy chấm điểm an toàn phòng thí nghiệm từ ảnh khớp với người chấm đến đâu,
> và cách chấm nào (YOLO + bộ luật hay VLM) phù hợp với loại tiêu chí nào?

- **Hạn gần nhất:** **Thứ Tư 7/10: báo cáo đề tài, có kết quả sơ bộ** (đã xác nhận với thầy)
- **Sản phẩm:** bài báo 4–6 trang theo khuôn IEEE hai cột (giống bài mẫu CLAHE – ICACCI 2014)
- **Cuối kỳ:** phát triển bài báo thành báo cáo cuối kỳ (theo lịch thi)

---

## 0. Thiết kế nghiên cứu (đã chốt)

```
 Dataset công khai ──► fine-tune YOLO (bình chữa cháy)
 YOLO COCO có sẵn ──┐
                    ├─► Hệ thống LUẬT (vùng + quan hệ không gian) ─┐
 Ảnh tự chụp ───────┤                                               │
 (30–40 ảnh, chỉ    ├─► VLM (3 biến thể prompt, không train) ──────┼─► So sánh từng tiêu chí
  dùng để TEST)     │                                               │   (tỷ lệ khớp, kappa, CI)
                    └─► 2–3 NGƯỜI chấm độc lập ─► nhãn đa số ──────┘   + phân tích ca lỗi
                                                 (đáp án chuẩn)
```

- **Không train trên ảnh tự chụp.** Ảnh tự chụp chỉ dùng để test, tức là đánh giá khác miền dữ liệu (cross-domain).
- **4 tiêu chí nhị phân (Đạt / Vi phạm):** xem [RUBRIC.md](RUBRIC.md)
  - C1 Vật cản trên lối đi · C2 Vật dụng cá nhân trên bàn · C3 Bình chữa cháy bị che · C4 Đồ ăn/uống
  - Hai tiêu chí "hóa chất ngoài tủ" và "dây điện" chuyển sang **hướng phát triển** (khó phát hiện, không có dataset)

---

## 1. Lịch làm việc

> Ảnh chỉ có vào **chiều 6/10**. Vì vậy mọi thứ không cần ảnh phải xong **trước** đó: code, train YOLO, phần I–III của bài, khung slide.

### Hôm nay — Thứ Hai 5/10

| # | Việc | Ai làm | Trạng thái |
|---|---|---|---|
| 1.1 | Code: vẽ vùng, hệ thống luật, VLM, đánh giá, notebook Colab | **Claude** | ✅ Xong, đã kiểm thử bộ luật và phần đánh giá |
| 1.2 | Lấy API key VLM (xem mục 3) | **Bạn** | |
| 1.3 | Roboflow: tìm dataset bình chữa cháy, export **YOLOv8** | **Bạn** | |
| 1.4 | Upload thư mục lên Drive (`MyDrive/ChuyenDe`), chạy ô 0 và ô Demo của notebook | **Bạn** | |
| 1.5 | Train YOLO bình chữa cháy (ô 1 notebook, ~30–60 phút, chạy nền) | **Bạn** bấm chạy | |
| 1.6 | Bản nháp bài báo phần I–III (LaTeX) + khung slide | **Claude** | |

### Ngày mai — Thứ Ba 6/10

| Giờ (gợi ý) | Việc | Ai làm |
|---|---|---|
| Sáng | Đọc và sửa bản nháp I–III; chạy thử VLM trên 1–2 ảnh bất kỳ để chắc API key dùng được | **Bạn** |
| 13:00–14:30 | Chụp 36 ảnh theo [PHOTO_GUIDE.md](PHOTO_GUIDE.md) | **Người chụp** |
| 14:30–14:45 | Copy ảnh vào `data/images/` → vẽ vùng bằng `tools/zone_tool.html` → chạy ô 2, 3 | **Bạn** |
| 14:45–15:30 | **Song song:** người chấm chấm nhãn (RUBRIC + ảnh xem trước vùng) ‖ chạy ô 4 (luật) và ô 5 (VLM) | **Người chấm** ‖ **Bạn** |
| 15:30 | Chạy ô 6 (đánh giá) → gửi Claude thư mục `outputs/` | **Bạn** |
| Tối | Viết phần IV–V và Abstract, hoàn thiện slide | **Claude** nháp, **Bạn** sửa |

> **Người chụp ≠ người chấm.** Người đã dàn dựng ảnh thì không được chấm.

### Thứ Tư 7/10 — Thuyết trình (kết quả sơ bộ)

### Phương án dự phòng nếu bị trễ
- Train YOLO lỗi hoặc không tìm được dataset → **bỏ C3**, chỉ dùng YOLO COCO có sẵn cho C1, C2, C4.
- Không có API key → **bỏ cột VLM**, bài thành "hệ thống luật vs người chấm" (câu hỏi 2 và 3 chuyển sang hướng phát triển).
- Thiếu người chấm → tối thiểu **2 người**, dùng Cohen's kappa thay cho Fleiss' kappa.
- Thiếu ảnh → tối thiểu **20 ảnh**, ghi rõ là nghiên cứu thử nghiệm (pilot study).

---

## 2. Cấu trúc thư mục

```
Chuyên đề/
├── ROADMAP.md · RUBRIC.md · PHOTO_GUIDE.md · PAPER_OUTLINE.md
├── requirements.txt
├── tools/zone_tool.html        ← mở bằng Chrome để vẽ vùng → zones.json
├── notebooks/pipeline.ipynb    ← chạy toàn bộ trên Colab (ô 0 → 6)
├── src/
│   ├── common.py               ← đường dẫn, tên tiêu chí, đọc ảnh
│   ├── rules.py                ← BỘ LUẬT (C1–C4) + vẽ minh hoạ
│   ├── test_rules.py           ← kiểm thử luật, gồm ví dụ tính tay 10×10 của đề cương
│   ├── train_extinguisher.py   ← fine-tune YOLO bình chữa cháy
│   ├── preview_zones.py        ← ảnh xem trước vùng cho người chấm
│   ├── make_label_sheets.py    ← tạo rater1..3.csv (thứ tự xáo trộn)
│   ├── run_rules.py            ← Cột 2: YOLO + luật → outputs/results_rule.csv
│   ├── run_vlm.py              ← Cột 3: VLM × 3 prompt → outputs/results_vlm.csv
│   ├── evaluate.py             ← so sánh với người → bảng .csv/.tex + hình
│   └── make_demo_data.py       ← dữ liệu GIẢ để chạy thử
├── data/
│   ├── images/                 ← ảnh tự chụp: v1_s01.jpg …
│   ├── zones.json              ← vùng mỗi góc chụp
│   ├── zones_preview/          ← ảnh có vẽ vùng (gửi người chấm)
│   └── labels/                 ← rater1.csv, rater2.csv, rater3.csv
├── models/extinguisher_best.pt ← sau khi train
├── outputs/                    ← kết quả, bảng, hình, ảnh minh hoạ
└── paper/                      ← LaTeX (Overleaf)
```

**Hệ thống luật dùng 3 bộ phát hiện:**
1. **YOLO11 (COCO, có sẵn):** ghế, balo, túi, cốc, chai, điện thoại, laptop, sách…
2. **YOLO fine-tune (Roboflow):** bình chữa cháy. Đây là phần "train AI".
3. **YOLO-World (từ vựng mở, không train):** "cardboard box", vì COCO không có lớp thùng carton. Nếu train bình chữa cháy thất bại, YOLO-World cũng thay luôn cho lớp bình chữa cháy.

---

## 3. API key cho VLM

| Lựa chọn | Chi phí ước tính (40 ảnh × 3 prompt = 120 lần gọi) | Ghi chú |
|---|---|---|
| **Gemini** (aistudio.google.com → Get API key) | **Miễn phí** (gói free có giới hạn số request/phút, script sẽ tự chờ) | Nhanh nhất để bắt đầu |
| **Claude API** (console.anthropic.com, nạp tối thiểu vài USD) | Haiku 4.5: ~0,5 USD · Sonnet 5.5: ~1 USD · Opus 5.5: ~2 USD | **Gói Claude Pro không dùng được cho API**, phải nạp riêng |

> Nếu có cả hai, bài báo có thể so sánh **2 VLM**. Đây là điểm cộng nhưng không bắt buộc.

---

## 4. Câu hỏi gửi thầy (ưu tiên câu 1, 2, 4, 6)

1. Buổi báo cáo đề tài 7/10 và 14/10 là hai buổi chia nhóm trình bày phải không ạ? Nhóm em thuộc buổi nào ạ?
2. Ở buổi báo cáo đề tài, em cần nộp bài báo có kết quả thực nghiệm đầy đủ, hay kết quả sơ bộ kèm slide là được ạ?
3. Mỗi nhóm trình bày khoảng bao nhiêu phút ạ?
4. Bài báo có bắt buộc theo mẫu IEEE hai cột như bài mẫu không ạ? Viết bằng tiếng Việt hay tiếng Anh ạ?
5. Báo cáo cuối kỳ "phát triển từ bài báo" khác bài báo ở điểm nào ạ: dài hơn, thêm chương, hay thêm thí nghiệm ạ?
6. Yêu cầu là nhóm 2–3 sinh viên, em có được làm cá nhân không ạ?
7. Đề tài có dùng mô hình phát hiện có sẵn (YOLO) và dataset công khai, còn ảnh thử nghiệm do nhóm tự chụp. Như vậy có được chấp nhận không ạ?

---

## 5. Theo dõi tiến độ

- [x] Đã hỏi thầy: 7/10, kết quả sơ bộ, khuôn IEEE
- [x] Code xong và chạy thử OK (bộ luật + đánh giá trên dữ liệu giả)
- [ ] Có API key
- [ ] Có dataset bình chữa cháy (YOLOv8 format)
- [ ] Đã chụp xong ảnh (≥ 30)
- [ ] Train xong YOLO bình chữa cháy
- [ ] Người chấm 1 xong · [ ] Người chấm 2 xong · [ ] Người chấm 3 xong
- [ ] Đã vẽ vùng (`zones.json`)
- [ ] Đã chạy hệ thống luật · [ ] Đã chạy VLM
- [ ] Đã có bảng kết quả
- [ ] Bản nháp bài báo · [ ] Slide
