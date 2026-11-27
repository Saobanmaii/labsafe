# Báo cáo tiến độ đề tài CVFP26BCPPRJC025

**Đánh giá điều kiện gọn gàng, vệ sinh và an toàn trong phòng thí nghiệm**
Môn: Thị giác máy tính · Nhóm: Trần Tuấn Kiệt (B23DCPT176), Lành Diệu Hương, Lê Quốc Dũng · Cập nhật: 13/10/2026

---

## 1. Tóm tắt

Nhóm đã hoàn thành **luồng xử lý từ ảnh đến kết quả chấm điểm**, gồm một mô hình tự huấn luyện, một bộ luật theo vùng, bộ dữ liệu thử nghiệm tự thu thập có gán nhãn và một đánh giá so sánh đầy đủ với người chấm. Phần còn thiếu chủ yếu là **lớp sản phẩm**: giao diện demo/dashboard, xử lý video, bảng kiểm cấu hình được và nhật ký sự kiện.

| Mức yêu cầu | Tình trạng |
|---|---|
| Baseline: demo cơ bản, có thể dùng API, sản phẩm hệ thống | **Gần xong.** Hệ thống chạy bằng dòng lệnh, có dùng API Gemini. Chưa có giao diện demo. |
| Extended 1: customized model, dữ liệu đầy đủ, đánh giá so sánh | **Đạt phần lõi.** Có mô hình tự huấn luyện, 62 ảnh gán nhãn bởi 3 người, đánh giá so sánh 2 hướng. Thiếu demo hoàn chỉnh. |
| Extended 2: full flow, demo thực tế | **Một phần.** Ảnh thực tế chụp tại phòng thí nghiệm. Chưa chạy trên video/camera. |
| Extended 3: bảng kiểm cấu hình, cảnh báo theo vùng, sự kiện kèm ảnh ẩn danh, đánh giá từng nhóm tiêu chí | **Một phần.** Đã có cảnh báo theo vùng và đánh giá riêng từng tiêu chí. Chưa có bảng kiểm cấu hình được và nhật ký sự kiện. |

---

## 2. Phạm vi bài toán

Đầu vào là một ảnh chụp phòng thí nghiệm. Đầu ra là kết quả **Đạt (0) / Vi phạm (1)** cho 4 tiêu chí, kèm ảnh minh hoạ khung đối tượng và vùng làm bằng chứng.

| Mã | Tiêu chí | Vi phạm khi |
|---|---|---|
| C1 | Vật cản lối đi | Có vật cỡ từ balo trở lên đặt trên sàn trong vùng lối đi |
| C2 | Đồ cá nhân trên bàn | Từ 3 đồ cá nhân trở lên trên mặt bàn thí nghiệm |
| C3 | Bình chữa cháy bị che | Bình bị che từ 1/3 trở lên, bị chắn phía trước, hoặc không còn ở vị trí |
| C4 | Đồ ăn, đồ uống | Có bất kỳ đồ ăn uống nào (dụng cụ, chai dung dịch kỹ thuật không tính) |

Định nghĩa đầy đủ: `RUBRIC.md`.

---

## 3. Kiến trúc hệ thống

Hệ thống có hai hướng chấm điểm chạy song song trên cùng một ảnh, cùng được so với người chấm:

```
                         ┌──────────────────────────────────────────────┐
                         │  Hướng A: YOLO + bộ luật (có huấn luyện)     │
                         │  ┌───────────────┐                           │
                         │  │ YOLO11s COCO  │ ghế, balo, cốc, chai,     │
                         │  │ (có sẵn)      │ điện thoại, laptop, sách  │
                         │  ├───────────────┤                           │
  Ảnh ──► Tiền xử lý ──► │  │ YOLO11n bình  │ bình chữa cháy            │──► Bộ luật  ──► C1..C4
  (xoay EXIF, đọc góc)   │  │ (TỰ HUẤN LUYỆN)│                          │   theo vùng    + ảnh bằng chứng
                         │  ├───────────────┤                           │      ▲
                         │  │ YOLO-World    │ thùng carton              │      │
                         │  └───────────────┘                           │  zones.json
                         └──────────────────────────────────────────────┘  (lối đi, bàn, bình)
                         ┌──────────────────────────────────────────────┐
                ────────►│  Hướng B: Gemini 3.5 Flash (không huấn luyện) │──► C1..C4 + lý do
                         │  3 biến thể prompt, đầu ra JSON               │
                         └──────────────────────────────────────────────┘
                                                   │
                         Người chấm (3 người, nhãn đa số) ──► So sánh: κ, F1, CI 95%
```

**Bộ luật (rule engine)** tính trên hình học đa giác:

- **C1:** tỷ lệ chiếm dụng lối đi `R = |(∪ phần đáy hộp bao vật cản) ∩ vùng lối đi| / |vùng lối đi|`; vi phạm khi R ≥ 5%.
- **C2:** đếm đồ cá nhân có tâm nằm trong vùng bàn; vi phạm khi ≥ 3.
- **C3:** tỷ lệ nhìn thấy V và tỷ lệ bị che O của vị trí bình; vi phạm khi không thấy bình, V < 0,5 hoặc O ≥ 1/3.
- **C4:** vi phạm khi có ít nhất 1 đối tượng đồ ăn uống.

Vùng chức năng được vẽ **một lần cho mỗi góc camera**, giống cách cấu hình vùng của camera giám sát thực tế.

---

## 4. Công nghệ đã sử dụng

### 4.1 Đối chiếu với tech stack gợi ý

| Gợi ý của đề | Nhóm đã dùng | Ghi chú |
|---|---|---|
| YOLOv8 | **YOLO11** (s và n) + **YOLOv8s-World v2** | YOLO11 là bản kế tiếp của YOLOv8, cùng thư viện Ultralytics |
| PPE / object detection | **Object detection** (COCO + mô hình bình chữa cháy) | Không dùng PPE vì 4 tiêu chí nói về trạng thái căn phòng, không về đồ bảo hộ của người |
| Semantic segmentation | **Chưa dùng.** Thay bằng vùng đa giác vẽ tay | Có thể bổ sung để tự tách vùng sàn/mặt bàn |
| Multi-label classifier | **Gemini** đóng vai bộ phân loại 4 nhãn (zero-shot) | Chưa huấn luyện bộ phân loại riêng |
| Rule engine | **Đã có**: luật hình học trên đa giác (Shapely) | `src/rules.py`, có bộ kiểm thử |
| Python | **Python 3.12** | Toàn bộ mã nguồn |
| Dashboard | **Chưa có** | Kế hoạch ở mục 9 |

### 4.2 Danh sách công nghệ

| Nhóm | Công nghệ | Dùng để |
|---|---|---|
| Phát hiện đối tượng | Ultralytics 8.4, YOLO11s (COCO), YOLO11n (tinh chỉnh), YOLOv8s-World v2 | Nhận diện đồ vật, bình chữa cháy, thùng carton |
| Huấn luyện | PyTorch 2.x + CUDA 12.6, GPU NVIDIA MX350 2 GB | Tinh chỉnh YOLO11n |
| Mô hình ngôn ngữ–thị giác | Google Gemini API (`google-genai`), model `gemini-3.5-flash` | Hướng chấm điểm thứ hai, không huấn luyện |
| Hình học / luật | Shapely | Tính giao, hợp đa giác cho C1–C3 |
| Xử lý ảnh | OpenCV, Pillow | Đọc ảnh (xoay EXIF), vẽ ảnh bằng chứng, làm mờ người |
| Đánh giá | scikit-learn, NumPy, pandas | Cohen's κ, Fleiss' κ (tự cài đặt), F1, bootstrap CI 95% |
| Trực quan hoá | Matplotlib | Biểu đồ κ theo tiêu chí |
| Công cụ gán vùng | HTML + JavaScript (`tools/zone_tool.html`) | Vẽ đa giác vùng trên ảnh, xuất `zones.json` |
| Thu nhãn người chấm | openpyxl (Excel có ô chọn 0/1) | Phiếu chấm và nhập nhãn tự động |
| Báo cáo | LaTeX IEEEtran (XeLaTeX, Overleaf) | Bài báo khoa học kèm theo |

---

## 5. Dữ liệu

| Bộ dữ liệu | Quy mô | Nguồn | Vị trí |
|---|---|---|---|
| Huấn luyện bình chữa cháy | 358 ảnh (179 có bình, 207 đối tượng; 179 ảnh âm), chia 287 / 71 | Fire-ART (CC BY 4.0), chỉ giữ lớp bình chữa cháy | `D:\Study\datasets\extinguisher_yolo` |
| Thử nghiệm | 62 ảnh, 1 phòng thí nghiệm điện tử, 6 góc chụp (5–13 ảnh/góc) | Nhóm tự chụp, dàn dựng theo kịch bản | `data/images/` |
| Nhãn người chấm | 3 người × 62 ảnh × 4 tiêu chí | 3 người ngoài nhóm, không tham gia dàn dựng | `data/labels/` |
| Vùng chức năng | 6 góc + 6 ảnh lệch khung vẽ riêng | Vẽ bằng công cụ của nhóm | `data/zones.json` |

**Số ca vi phạm theo nhãn đa số (trên 62 ảnh):** C1: 32 · C2: 11 · C3: 32 · C4: 26.

**Ẩn danh:** ảnh thử nghiệm không có người. Nhóm đã viết sẵn bước làm mờ người (`src/blur_people.py`); khi chạy thử, bước này phát hiện nhầm áo khoác thành người nên ảnh gốc được giữ nguyên.

---

## 6. Kết quả đã đạt

### 6.1 Mô hình tự huấn luyện (bình chữa cháy)

YOLO11n tinh chỉnh từ trọng số COCO, ảnh 640, batch 8, dừng sớm ở epoch 46 (tốt nhất: epoch 36).

| mAP@0,5 | mAP@0,5:0,95 | Precision | Recall |
|---|---|---|---|
| 0,797 | 0,514 | 0,876 | 0,672 |

Trên ảnh phòng thí nghiệm thực tế, mô hình COCO có sẵn và YOLO-World đều **không** phát hiện được bình chữa cháy, còn mô hình tự huấn luyện phát hiện được với độ tin cậy 0,94 (`outputs/fig_detector_compare.png`).

### 6.2 Đánh giá so sánh với người chấm (Cohen's κ, 62 ảnh)

| | C1 Lối đi | C2 Đồ cá nhân | C3 Bình chữa cháy | C4 Ăn uống |
|---|---|---|---|---|
| Người với người (Fleiss κ) | 0,89 | 0,69 | 0,98 | 0,96 |
| YOLO + luật | **0,74** | 0,58 | **0,90** | 0,78 |
| Gemini 3.5 Flash (prompt P1) | 0,44 | **0,88** | 0,78 | **0,97** |

- **YOLO + luật** tốt hơn ở tiêu chí phụ thuộc **vị trí** (C1, C3) nhờ có vùng chức năng.
- **Gemini** tốt hơn ở tiêu chí phụ thuộc **loại đồ vật** (C2, C4) nhờ nhận biết được vật ngoài 80 lớp COCO.
- **Tốc độ:** YOLO + luật khoảng 0,13 giây/ảnh trên laptop, chạy offline. Gemini khoảng 10 giây/ảnh, cần mạng, gói miễn phí giới hạn khoảng 20 ảnh/ngày/tài khoản.

### 6.3 Phân tích lỗi chính

- Mô hình COCO nhận **chính bình chữa cháy thành "bottle"**, gây 6/7 ca báo nhầm C4.
- **Áo khoác** không có trong COCO: áo trùm bình không được tính là vật che (bỏ sót C3), ghế có áo vắt lên bị nhận là người (bỏ sót C1).
- Gemini **không biết vị trí lối đi** nên báo nhầm C1 nhiều (16 ca), và đôi khi coi "không thấy bình" là đạt (bỏ sót C3).

Bảng và hình đầy đủ: `outputs/paper/`. Bài báo chi tiết: `paper/main.tex`.

---

## 7. Đối chiếu chi tiết với yêu cầu

### 7.1 Yêu cầu công việc

| Yêu cầu | Trạng thái | Bằng chứng |
|---|---|---|
| Phân tích **ảnh** để phát hiện dấu hiệu liên quan bố trí, vệ sinh, an toàn | Xong | `src/run_rules.py`, `src/run_vlm.py` |
| Phân tích **video** | Chưa | — |
| Kết quả gắn với tiêu chí và **vùng bằng chứng** cụ thể | Xong | Ảnh bằng chứng có khung đối tượng, vùng và kết luận từng tiêu chí: `outputs/annotated/` |
| Demo cơ bản, có thể dùng API | Một phần | Chạy dòng lệnh; dùng API Gemini. Chưa có giao diện |
| Customized model | Xong | `models/extinguisher_best.pt`, mAP@0,5 = 0,80 |
| Dữ liệu đầy đủ | Xong | 358 ảnh huấn luyện, 62 ảnh thử nghiệm có nhãn 3 người |
| Đánh giá so sánh | Xong | 2 hướng × 4 tiêu chí × người chấm, κ + CI 95% + F1 + phân tích lỗi |
| Sản phẩm hệ thống full flow | Một phần | Ảnh → kết quả + ảnh bằng chứng đã thông suốt. Chưa có lưu trữ, giao diện, cảnh báo |
| Demo thực tế | Một phần | Ảnh chụp thật tại phòng thí nghiệm. Chưa chạy trực tiếp từ camera |
| Bảng kiểm cấu hình được | Một phần | Ngưỡng luật nằm trong `PARAMS` (`src/rules.py`), vùng trong `zones.json`. Chưa tách thành file cấu hình hoặc giao diện |
| Cảnh báo theo vùng nguy cơ | Một phần | Luật đã tính theo vùng, ảnh đánh dấu VIOLATION. Chưa có cơ chế cảnh báo (thông báo, âm thanh) |
| Ghi nhận sự kiện kèm ảnh đã ẩn danh | Chưa | Có sẵn bước làm mờ người; chưa có nhật ký sự kiện |
| Đánh giá riêng từng nhóm tiêu chí | Xong | κ, F1, CI riêng cho C1–C4 |

### 7.2 Yêu cầu báo cáo

| Yêu cầu | Trạng thái |
|---|---|
| Log tiến trình, báo cáo tiến độ thường kỳ | Có: báo cáo sơ bộ 07/10, báo cáo này, nhật ký ở mục 8 |
| Cuối kỳ: báo cáo kỹ thuật | Bản nháp đầy đủ dạng bài báo IEEE (`paper/main.tex`) |
| Cuối kỳ: source code | Có: thư mục `src/`, `tools/` |
| Cuối kỳ: dataset | Có ảnh, nhãn, vùng; cần đóng gói và viết mô tả |
| Cuối kỳ: demo | Chưa |

---

## 8. Nhật ký tiến trình

| Ngày | Công việc |
|---|---|
| 09/10 | Hoàn thành chấm điểm bằng Gemini (prompt P1 đủ 62 ảnh), đánh giá so sánh, viết phần kết quả bài báo |
| 08/10 | Vẽ vùng, chạy YOLO + luật trên 62 ảnh, gửi và thu 3 phiếu người chấm, bắt đầu chạy Gemini |
| 07–08/10 | Chụp 62 ảnh tại phòng thí nghiệm điện tử, đặt tên, kiểm tra ẩn danh |
| 07/10 | Báo cáo đề tài với kết quả sơ bộ (mAP 0,80, so sánh định tính 3 bộ phát hiện) |
| 04–05/10 | Chốt đề tài và 4 tiêu chí, thiết kế đánh giá 3 cột, viết bộ luật và kiểm thử, cài môi trường GPU, huấn luyện mô hình bình chữa cháy trên Fire-ART |

---

## 9. Việc còn lại và kế hoạch

Ưu tiên theo mức độ đề yêu cầu:

1. **Dashboard demo** (Streamlit hoặc Gradio): tải ảnh lên → hiện ảnh bằng chứng, kết quả 4 tiêu chí của cả hai hướng.
2. **Bảng kiểm cấu hình được:** tách tiêu chí, ngưỡng và danh sách lớp đối tượng ra file YAML, chỉnh được trên dashboard.
3. **Nhật ký sự kiện + ảnh ẩn danh:** mỗi lần phát hiện vi phạm ghi một dòng (thời gian, góc, tiêu chí, ảnh đã làm mờ người) vào CSV/SQLite, hiển thị trên dashboard.
4. **Xử lý video:** lấy mẫu khung hình theo chu kỳ, chạy hướng YOLO + luật, chỉ ghi sự kiện khi vi phạm kéo dài nhiều khung liên tiếp.
5. **Cải thiện mô hình:**
    - bỏ các khung "bottle" trùng với khung bình chữa cháy;
    - bổ sung lớp áo khoác;
    - thử phân đoạn ngữ nghĩa (semantic segmentation) để tự tìm vùng sàn và mặt bàn;
    - thử kết hợp: luật cho C1, C3 và Gemini cho C2, C4.
6. **Đóng gói nộp cuối kỳ:** dataset kèm mô tả, README chạy mã nguồn, video demo.

**Câu hỏi cần thầy xác nhận:** mức yêu cầu tối thiểu của nhóm (Baseline hay Extended), và demo có bắt buộc chạy trên video/camera hay chạy trên ảnh là đủ.
