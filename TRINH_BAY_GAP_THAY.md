# Trình bày tiến độ với thầy

Đề tài: **Đánh giá điều kiện gọn gàng, vệ sinh và an toàn trong phòng thí nghiệm**
Nhóm: Trần Tuấn Kiệt, Lành Diệu Hương, Lê Quốc Dũng

> File gồm 2 phần: **Phần 1** liệt kê việc nhóm đã làm (để tự rà lại, sửa chỗ nào chưa đúng). **Phần 2** là kịch bản nói 5–7 phút.

---

## PHẦN 1. Những việc nhóm đã làm

### 1.1 Nhóm tự làm (phần phải nói được rõ ràng)

| Việc | Cụ thể |
|---|---|
| Chốt bài toán | Chọn 4 tiêu chí đo được bằng ảnh: C1 vật cản lối đi, C2 đồ cá nhân trên bàn, C3 bình chữa cháy bị che, C4 đồ ăn uống |
| Viết bảng tiêu chí | `RUBRIC.md`: định nghĩa thế nào là vi phạm, cái gì không tính (ví dụ chai hoá chất không phải đồ uống). Người chấm, luật và Gemini đều dùng chung bảng này |
| Thu thập dữ liệu | Chụp **62 ảnh** tại phòng thí nghiệm điện tử, **6 góc chụp**, dàn dựng có chủ đích các tình huống vi phạm / không vi phạm |
| Tổ chức người chấm | Mời **3 người ngoài nhóm** chấm độc lập 62 ảnh × 4 tiêu chí. Lấy nhãn đa số (2/3) làm đáp án |
| Vẽ vùng chức năng | Vẽ đa giác lối đi, mặt bàn, chỗ đặt bình cho từng góc chụp (6 góc + 6 ảnh lệch khung vẽ riêng) |
| Huấn luyện mô hình bình chữa cháy | Lọc bộ Fire-ART còn 358 ảnh, huấn luyện YOLO11n trên GPU laptop. Kết quả mAP@0,5 = 0,80 |
| Chạy thí nghiệm | Chạy YOLO + luật trên 62 ảnh. Chạy Gemini với 3 prompt (xoay vòng nhiều API key vì gói miễn phí giới hạn) |
| Đọc kết quả, phân tích lỗi | Xem từng ca máy chấm sai (`outputs/errors.csv`), tìm ra nguyên nhân: bình chữa cháy bị nhận thành "bottle", áo khoác không có trong COCO, Gemini không biết đâu là lối đi |

### 1.2 Dùng AI hỗ trợ

| Việc | Ghi chú |
|---|---|
| Viết code Python | Pipeline chạy YOLO, bộ luật hình học, script gọi Gemini, script đánh giá |
| Gợi ý phương pháp đánh giá | Cohen's κ, Fleiss κ, khoảng tin cậy bootstrap |
| Hỗ trợ viết bản nháp bài báo LaTeX | Nhóm cung cấp số liệu và nhận xét |

> **Cách nói với thầy:** "Nhóm dùng AI để dựng nhanh bản đầu tiên của hệ thống, chủ yếu là phần code. Thiết kế bài toán, dữ liệu, nhãn và phân tích kết quả là nhóm làm. Giờ có kết quả rồi, nhóm đang đọc kỹ từng phần để hiểu sâu và cải tiến."

### 1.3 Chưa làm

- Giao diện demo / dashboard
- Chạy trên video hoặc camera
- Bảng kiểm cấu hình được (file YAML, chỉnh trên giao diện)
- Nhật ký sự kiện kèm ảnh ẩn danh
- Prompt P2, P3 mới chạy được khoảng 33/62 ảnh

---

## PHẦN 2. Kịch bản trình bày 5–7 phút

### Phút 0–1: Bài toán

> "Đề tài của nhóm em là tự động chấm an toàn phòng thí nghiệm từ ảnh chụp. Đầu vào là một ảnh, đầu ra là **Đạt hoặc Vi phạm** cho 4 tiêu chí: vật cản lối đi, đồ cá nhân trên bàn, bình chữa cháy bị che, và đồ ăn uống. Ngoài kết luận, hệ thống còn vẽ khung và vùng lên ảnh để làm bằng chứng."

*Có thể mở 1 ảnh trong `outputs/annotated/` cho thầy xem.*

### Phút 1–2: Dữ liệu

> "Nhóm tự chụp 62 ảnh ở phòng thí nghiệm điện tử, 6 góc máy, có dàn dựng các tình huống vi phạm. Để có đáp án, nhóm nhờ 3 người ngoài nhóm chấm độc lập theo một bảng tiêu chí chung, rồi lấy kết quả đa số. Ba người này đồng ý với nhau khá cao, trừ tiêu chí đồ cá nhân là hay lệch nhau hơn."

### Phút 2–4: Hai hướng giải quyết

> "Nhóm so sánh hai hướng.
>
> **Hướng 1 là YOLO cộng luật.** YOLO tìm đồ vật trong ảnh như ghế, balo, cốc, điện thoại. YOLO có sẵn không nhận được bình chữa cháy nên nhóm tự huấn luyện thêm một mô hình riêng cho bình, đạt mAP 0,80. Sau đó, bộ luật dựa vào **vùng đã vẽ sẵn** để kết luận. Ví dụ C1: nếu vật cản chiếm từ 5% diện tích lối đi trở lên thì là vi phạm.
>
> **Hướng 2 là Gemini**, một mô hình nhìn được ảnh. Nhóm gửi ảnh kèm mô tả 4 tiêu chí, Gemini trả lời luôn 0 hay 1, không cần huấn luyện. Nhóm thử 3 cách viết prompt để xem kết quả có ổn định không."

### Phút 4–6: Kết quả (mở biểu đồ κ)

> "Nhóm đo mức khớp với người chấm bằng hệ số kappa. Kappa bằng 1 là khớp hoàn toàn, bằng 0 là như đoán bừa.
>
> - **YOLO + luật tốt hơn ở tiêu chí về vị trí:** lối đi đạt 0,74, bình chữa cháy đạt 0,90. Lý do là có vùng vẽ sẵn nên máy biết vật nằm ở đâu.
> - **Gemini tốt hơn ở tiêu chí về loại đồ vật:** đồ cá nhân đạt 0,88, đồ ăn uống đạt 0,97. Gemini nhận ra được những thứ YOLO không có lớp, như áo khoác.
> - Prompt ảnh hưởng nhiều: prompt rút gọn P2 cho kết quả kém hẳn ở C1 và C2."

**Ba phát hiện nên kể (thầy thường thích phần này):**
1. YOLO nhận **chính bình chữa cháy thành "bottle"**, nên báo nhầm có đồ uống (6 trên 7 ca báo nhầm C4).
2. Áo khoác không có trong COCO nên YOLO bỏ sót, vì thế luật yếu ở C2.
3. Gemini không biết đâu là lối đi nên hay báo nhầm C1 (16 ca).

### Phút 6–7: Hạn chế, kế hoạch, câu hỏi

> "Hạn chế: dữ liệu còn ít, chỉ 1 phòng, nên khoảng tin cậy còn rộng.
>
> Kế hoạch tiếp: làm demo giao diện; kết hợp hai hướng (luật cho C1, C3 và Gemini cho C2, C4); sửa lỗi bottle và áo khoác; sau đó mở rộng sang video.
>
> Em muốn hỏi thầy hai điều: nhóm cần đạt mức yêu cầu nào, và demo chạy trên ảnh có đủ không hay bắt buộc phải có video/camera?"

---

## Chuẩn bị mang theo

- [ ] Biểu đồ κ (`outputs/fig_kappa.png`)
- [ ] 2–3 ảnh bằng chứng trong `outputs/annotated/`: 1 ảnh chấm đúng, 1 ảnh bị lỗi "bottle"
- [ ] Hình so sánh 3 bộ phát hiện bình chữa cháy (`outputs/fig_detector_compare.png`)
- [ ] Đã đọc xong file `ON_TAP_TRUOC_KHI_GAP_THAY.md`
