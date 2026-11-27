# LabSafe — Hướng dẫn chạy và demo sản phẩm

Sản phẩm cho đề tài **CVFP26BCPPRJC025 — Đánh giá điều kiện gọn gàng, vệ sinh và an toàn trong phòng thí nghiệm**.

## 1. Chạy

Nháy đúp **`run_demo.bat`**, trình duyệt tự mở `http://localhost:8501`.

Hoặc chạy bằng dòng lệnh:

```
D:\Study\venv-nckh\Scripts\python.exe -m streamlit run app\main.py
```

Cài trên máy khác: `pip install -r requirements.txt streamlit streamlit-image-coordinates`, rồi chép các file trọng số `yolo11s.pt`, `yolov8s-worldv2.pt` và `models/extinguisher_best.pt`.

Gemini (không bắt buộc): khai báo `GEMINI_API_KEY=...` trong `.env`, có thể thêm `_2`, `_3`, `_4`. Khi key này hết hạn mức, hệ thống tự chuyển sang key kế tiếp.
Telegram (không bắt buộc): khai báo `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID` trong `.env`, rồi bật mục này ở trang «Bảng kiểm».

## 2. Các trang

| Trang | Chức năng |
|---|---|
| Tổng quan | Sơ đồ hệ thống, bảng kiểm đang áp dụng, đối chiếu với từng mức yêu cầu của đề |
| Phân tích ảnh | Lấy ảnh mẫu, ảnh tải lên (một hoặc nhiều ảnh) hoặc ảnh chụp từ webcam. Có 3 chế độ: YOLO + luật, Gemini, Kết hợp. Kết quả gồm điểm tổng, điểm theo nhóm, thẻ từng tiêu chí có lý do và vùng bằng chứng. Với ảnh trong bộ dữ liệu, trang hiện thêm nhãn của người chấm để so sánh |
| Video & camera | Nhận tệp video, webcam hoặc camera IP/điện thoại. Hệ thống lấy mẫu khung hình định kỳ và lọc theo thời gian: vi phạm phải kéo dài N khung liên tiếp mới được ghi thành sự kiện. Khi có sự kiện, hệ thống cảnh báo bằng âm thanh, thông báo trên màn hình và Telegram |
| Nhật ký sự kiện | Dữ liệu lưu trong SQLite, mỗi sự kiện kèm ảnh bằng chứng đã **làm mờ người**. Có bộ lọc, biểu đồ, nút xác nhận đã xử lý kèm ghi chú và xuất CSV |
| Bảng kiểm | Bật/tắt tiêu chí, sửa ngưỡng, chọn lớp đối tượng, nhóm, mức độ. Có thể thêm tiêu chí mới theo 3 loại luật hoặc sửa thẳng YAML. Nội dung lưu tại `app/checklist.yaml` |
| Vùng camera | Nhấp chuột lên ảnh để vẽ vùng lối đi, mặt bàn, vị trí bình chữa cháy. Có thể tạo camera mới từ ảnh tải lên hoặc từ webcam |
| Đánh giá mô hình | Chạy lại κ, F1 trên 62 ảnh với bảng kiểm hiện tại, xem κ theo nhóm, κ của chế độ Kết hợp, xem từng ảnh bị chấm sai, và kết quả huấn luyện YOLO11n |

## 3. Kịch bản demo (~7 phút)

1. **Tổng quan** (30 giây): giới thiệu sơ đồ và bảng đối chiếu yêu cầu.
2. **Phân tích ảnh** với ảnh `v2c_05.jpg`: điểm 50/100, C1 vi phạm vì ghế trong lối đi chiếm 24,6%, C2 vi phạm vì có laptop và 2 quyển sách trên bàn. Ảnh có nhãn người chấm, khớp 4/4 tiêu chí. Bấm ▶ để xem ảnh tiếp theo.
3. Chuyển sang chế độ **Kết hợp** với ảnh `v2b_06.jpg`: Gemini khoanh balo và bình chữa cháy, đưa ra lý do bằng tiếng Việt. Kết quả này đã được lưu đệm nên không tốn hạn mức API.
4. **Bảng kiểm**: đổi C2 thành «≥ 2 đồ», lưu, quay lại ảnh cũ để thấy kết luận thay đổi. Sau đó vào **Đánh giá mô hình**, chạy lại để xem κ thay đổi theo. Nhớ khôi phục mặc định sau khi demo xong.
5. **Video & camera**: chọn `demo_v2c.mp4`, tốc độ 2x, bấm Bắt đầu. Quan sát phần «chờ xác nhận 1/3 → 2/3 → đang vi phạm», nghe tiếng cảnh báo, và xem sự kiện tự đóng khi hết vi phạm.
6. **Nhật ký sự kiện**: chọn một dòng để xem ảnh đã làm mờ người, bấm «Xác nhận đã xử lý», rồi xuất CSV.
7. *(Demo thực tế)* Vào **Vùng camera**, tạo camera mới từ webcam và vẽ lối đi. Sau đó ở **Video & camera**, chọn Webcam và đặt balo vào vùng lối đi.

> Video mẫu được ghép từ ảnh cùng một góc chụp: `python app/make_demo_video.py`. Nên quay thêm video thật tại phòng thí nghiệm bằng điện thoại, giữ máy cố định, rồi vẽ vùng cho góc quay đó.

## 4. Số liệu (62 ảnh, so với nhãn đa số của 3 người chấm)

| Cohen's κ | C1 Lối đi | C2 Đồ cá nhân | C3 Bình chữa cháy | C4 Ăn uống |
|---|---|---|---|---|
| Người với người (Fleiss κ) | 0,89 | 0,69 | 0,98 | 0,96 |
| YOLO + luật, đúng cấu hình bài báo | 0,74 | 0,58 | 0,90 | 0,78 |
| **Sản phẩm: YOLO + luật + lọc chai trên bình** | 0,74 | 0,58 | 0,90 | **0,90** |
| Gemini 3.5 Flash (P1) | 0,44 | 0,88 | 0,78 | 0,97 |
| **Sản phẩm: chế độ Kết hợp** (luật C1, C3; Gemini C2, C4) | **0,74** | **0,88** | **0,90** | **0,97** |

Kiểm tra lại không cần giao diện:

- `python app/batch.py --paper`: kết quả khớp 100% với `outputs/results_rule.csv` của bài báo.
- `python app/batch.py`: chạy với bảng kiểm hiện tại.

## 5. Cấu trúc mã sản phẩm

```
app/
  main.py                 điểm vào Streamlit (điều hướng các trang)
  checklist.default.yaml  bảng kiểm mặc định (checklist.yaml = bản đang dùng)
  core/
    config.py             đường dẫn, đọc/ghi và kiểm tra bảng kiểm, vùng camera
    detector.py           3 mô hình YOLO + hậu xử lý lọc chai trên bình
    rules_engine.py       3 loại luật cấu hình được, bằng chứng từng tiêu chí, điểm theo nhóm
    vlm.py                Gemini: prompt sinh từ bảng kiểm, khung bằng chứng, cache, xoay vòng key
    pipeline.py           luồng ảnh → phát hiện → luật → (Gemini) → kết luận
    render.py             vẽ ảnh bằng chứng (tiếng Việt), cắt vùng bằng chứng, làm mờ người
    events.py             nhật ký SQLite, bộ lọc theo thời gian cho video, Telegram
    evaluation.py         κ / F1 so với người chấm, cache kết quả phát hiện
  pages/                  7 trang giao diện
  theme.py, assets/       giao diện: sidebar đỏ, logo, thanh tiêu đề, thẻ, nút (CSS)
  batch.py                đánh giá bằng dòng lệnh
  make_demo_video.py      tạo video mẫu
  train/                  nâng cấp mô hình LabSafe-6 (xem mục 6)
app_data/                 dữ liệu sinh ra khi chạy: events.db, ảnh sự kiện, zones.json (+ zones.backup.json), cache, video mẫu
.streamlit/config.toml    màu, phông chữ (Be Vietnam Pro), bo góc của giao diện
```

Mã của bài báo trong `src/` được giữ nguyên.

## 6. Nâng cấp mô hình LabSafe-6

Mô hình bổ sung nhận 6 lớp mà mô hình COCO thiếu hoặc nhầm: `binh_chua_chay`, `ao_khoac`, `mu`, `vi`, `do_uong`, `do_an`.

```
python app/train/prepare_public.py     # 1. Open Images: áo khoác, mũ, đồ uống, đồ ăn (~2.300 ảnh)
python app/train/prepare_lvis.py       # 1b. LVIS (ảnh COCO): thêm ví, bình chữa cháy (~2.000 ảnh)
python app/train/build_dataset.py --out D:/Study/datasets/labsafe_6cls_v2
                                       # 2. gộp + Fire-ART + ảnh nhóm tự chụp (data/train_labeled/), tự loại ảnh trùng bộ kiểm tra
python app/train/train.py --data D:/Study/datasets/labsafe_6cls_v2/data.yaml --out labsafe6_v2.pt --name v2
                                       # 3. train (GPU MX350: ~6 phút/epoch). TẮT app khi train để không tranh bộ nhớ GPU
python app/train/compare.py --model models/labsafe6_v2.pt
                                       # 4. κ trước/sau trên 62 ảnh + phân tích từng phần
```

Bật mô hình trong ứng dụng: thêm `custom_model: models/labsafe6_v2.pt` và `custom_skip: [fire extinguisher]` vào mục `detector` của bảng kiểm (hoặc dán `app/checklist.labsafe6.yaml` vào tab YAML của trang Bảng kiểm), rồi thêm các lớp `jacket`, `hat`, `wallet`, `drink`, `food` vào tiêu chí tương ứng.
