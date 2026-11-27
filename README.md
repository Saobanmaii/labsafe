# LabSafe — Đánh giá điều kiện gọn gàng, vệ sinh và an toàn trong phòng thí nghiệm

Đề tài **CVFP26BCPPRJC025** · Môn Thị giác máy tính · Nhóm: Trần Tuấn Kiệt, Lành Diệu Hương, Lê Quốc Dũng

Hệ thống nhận ảnh hoặc video phòng thí nghiệm, phát hiện 4 loại vi phạm (vật cản lối đi, đồ cá nhân trên bàn,
bình chữa cháy bị che, đồ ăn uống), khoanh vùng bằng chứng, chấm điểm an toàn 0–100, cảnh báo và ghi nhật ký
kèm ảnh đã làm mờ người.

```
Ảnh / video ─► YOLO nhận diện đồ vật ─► Bộ luật so vị trí với vùng (lối đi, bàn, bình) ─► Điểm + ảnh bằng chứng ─► Sự kiện, cảnh báo
```

## Đọc gì trước

| File | Nội dung |
|---|---|
| **`BAO_CAO_SAN_PHAM_LabSafe.docx`** | Tài liệu chính để ôn vấn đáp: luồng, nguyên lý, thuật toán, kết quả, hướng cải thiện, **11 câu hỏi thầy có thể hỏi** |
| `HUONG_DAN_DEMO.md` | Cách chạy, kịch bản demo 7 phút, cấu trúc mã |
| `HUONG_DAN_THU_THAP_DU_LIEU.docx` | Hướng dẫn chụp ảnh, gán nhãn Roboflow, quay video phòng 602 |
| `RUBRIC.md` | Định nghĩa đầy đủ 4 tiêu chí |

## Cài đặt

Cần Python 3.12. Có GPU NVIDIA thì cài PyTorch bản CUDA trước (https://pytorch.org/get-started/locally/).

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Lần chạy đầu, thư viện tự tải các trọng số `yolo11s.pt`, `yolov8s-worldv2.pt` và CLIP (khoảng 400 MB).
Mô hình nhóm tự huấn luyện đã có sẵn trong `models/`.

**Gemini (không bắt buộc):** tạo file `.env` ở thư mục gốc, ghi `GEMINI_API_KEY=...`.
File `.env` **không được đưa lên git**.

## Chạy

```bash
streamlit run app/main.py      # hoặc nháy đúp run_demo.bat
```

Trình duyệt mở `http://localhost:8501`.

Kiểm tra lại số liệu bằng dòng lệnh (không cần giao diện):

```bash
python app/batch.py --paper    # phải khớp 100% số liệu bài báo
python app/batch.py            # với bảng kiểm hiện tại
```

## Cấu trúc

```
app/            sản phẩm (Streamlit): core/ = lõi xử lý, pages/ = 7 trang, train/ = nâng cấp mô hình LabSafe-6
src/            mã thí nghiệm của bài báo NCKH
data/images/    62 ảnh kiểm tra (6 góc camera) — CHỈ để đánh giá, không dùng để train
data/labels/    nhãn của 3 người chấm
data/zones.json vùng lối đi / bàn / vị trí bình đã vẽ cho từng góc camera
models/         mô hình nhóm tự huấn luyện
outputs/        bảng, hình kết quả
paper/          bài báo (LaTeX)
```

## Kết quả chính (62 ảnh, Cohen's κ so với nhãn đa số của 3 người chấm)

| | C1 Lối đi | C2 Đồ cá nhân | C3 Bình chữa cháy | C4 Ăn uống |
|---|---|---|---|---|
| Người với người (Fleiss κ) | 0,89 | 0,69 | 0,98 | 0,96 |
| YOLO + luật (sản phẩm) | 0,74 | 0,58 | 0,90 | 0,90 |
| Gemini 3.5 Flash | 0,44 | 0,88 | 0,78 | 0,97 |
| Kết hợp (luật C1, C3 + Gemini C2, C4) | 0,74 | 0,88 | 0,90 | 0,97 |

**Tự đề xuất vùng bằng phân đoạn ngữ nghĩa** (trang «Vùng camera», `app/core/segment.py`, đánh giá: `python app/eval_auto_zones.py`):
SegFormer-B5 (ADE20K) tìm sàn và mặt bàn trên ảnh phòng sạch, mô hình bình tìm vị trí bình. Khi chỉ dùng vùng tự động:
C3 = 0,87 và C2 = 0,55 (gần vẽ tay), nhưng C1 = 0,34 (vẽ tay 0,71) vì sàn chưa chắc là lối đi → dùng làm trợ lý, người sửa lại.

**Thử nghiệm LabSafe-6** (`app/train/`, `models/labsafe6_v2.pt`): YOLO11n 6 lớp (bình, áo khoác, mũ, ví, đồ uống, đồ ăn)
train trên ~4.700 ảnh công khai (Open Images, LVIS, Fire-ART), mAP@0,5 = 0,454 trên tập kiểm định. Trên 62 ảnh phòng lab
**không cải thiện κ** vì ảnh công khai khác bối cảnh (áo đang mặc, chụp cận) → bước tiếp theo: ảnh tự chụp đồ cá nhân trên bàn
(`HUONG_DAN_THU_THAP_DU_LIEU.docx`). Chi tiết: `outputs/train_labsafe6_v2.json`, `outputs/compare_labsafe6.csv`.
