# BẢNG TIÊU CHÍ CHẤM ĐIỂM — Hướng dẫn cho người chấm

> Bạn sẽ xem từng ảnh phòng thí nghiệm và chấm **4 tiêu chí**. Mỗi tiêu chí ghi **0 = Đạt** hoặc **1 = Vi phạm**.
> Cả **người chấm**, **hệ thống luật** và **VLM** đều dùng chung bảng tiêu chí này.

## Quy tắc chung

1. **Chấm độc lập.** Không bàn với người chấm khác, không xem kết quả của người khác.
2. **Chỉ dựa vào những gì nhìn thấy trong ảnh.** Không suy đoán phần bị khuất ngoài khung hình.
3. **Phân vân thì chọn theo cảm nhận thực tế:** "Nếu là cán bộ kiểm tra phòng, mình có nhắc nhở không?" Ghi lý do vào cột `ghi_chu`.
4. Chấm lần lượt theo thứ tự trong file, **không quay lại sửa** các ảnh đã chấm.
5. Người **đã tham gia dàn dựng ảnh** thì **không làm người chấm**, vì đã biết trước đáp án.

---

## C1. Vật cản trên lối đi

| | Mô tả |
|---|---|
| **Vi phạm (1)** | Có ít nhất một vật **đặt trên sàn trong vùng lối đi**, cỡ từ **balo trở lên** (ghế, balo, thùng, túi, hộp, xô…), làm hẹp hoặc chắn lối đi |
| **Đạt (0)** | Lối đi trống, hoặc chỉ có vật rất nhỏ (cỡ cây bút, mẩu giấy) |
| Không tính | Người đang đứng hoặc đi lại; đồ vật nằm hẳn dưới gầm bàn, không lấn ra lối đi |

*Vùng lối đi của mỗi góc chụp được khoanh trên ảnh mẫu `data/zones_preview/`. Xem ảnh mẫu trước khi chấm.*

## C2. Vật dụng cá nhân trên bàn thí nghiệm

| | Mô tả |
|---|---|
| **Vi phạm (1)** | Trên **mặt bàn thí nghiệm** có **từ 3 vật dụng cá nhân trở lên** |
| **Đạt (0)** | Có 0–2 vật dụng cá nhân |
| Tính là vật dụng cá nhân | Điện thoại, laptop xách tay, balo, túi xách, ví, sách/vở, áo khoác, mũ |
| Không tính | Thiết bị thí nghiệm (máy hiện sóng, nguồn, đồng hồ đo, mỏ hàn, bo mạch…), dụng cụ, máy tính cố định của phòng, giấy hướng dẫn thí nghiệm |

## C3. Bình chữa cháy bị che khuất

| | Mô tả |
|---|---|
| **Vi phạm (1)** | Bình chữa cháy **bị che từ khoảng 1/3 trở lên**, **hoặc** có vật chắn trước làm khó lấy bình, **hoặc** vị trí đặt bình trống (bình không còn ở đó) |
| **Đạt (0)** | Bình nhìn thấy rõ, phía trước thông thoáng, lấy được ngay |

*Vị trí quy định của bình chữa cháy ở mỗi góc chụp cũng được đánh dấu trong ảnh mẫu.*

## C4. Đồ ăn, đồ uống trong khu vực thí nghiệm

| | Mô tả |
|---|---|
| **Vi phạm (1)** | Có **bất kỳ** đồ ăn hoặc đồ uống nào nhìn thấy được: cốc, ly, chai nước uống, lon nước, hộp cơm, bánh, trái cây… (kể cả đã uống/ăn dở) |
| **Đạt (0)** | Không có đồ ăn, đồ uống |
| Không tính | **Chai lọ hóa chất, chai cồn / dung dịch vệ sinh mạch, bình thí nghiệm, cốc đong thủy tinh**: đây là dụng cụ, không phải đồ uống |

---

## Cách điền file nhãn

Mỗi người chấm nhận một file `raterX.csv` (X = 1, 2, 3) có sẵn cột `image`. Bạn chỉ cần điền 4 cột C1–C4 và cột ghi chú nếu cần:

```csv
image,C1,C2,C3,C4,ghi_chu
v2_s07.jpg,0,1,1,0,"C3: bị thùng che khoảng một nửa"
v1_s03.jpg,0,0,0,0,
...
```

- Thứ tự ảnh trong file **đã được xáo trộn**, cứ chấm theo đúng thứ tự đó.
- Thời gian ước tính: **khoảng 1 phút/ảnh**, tức 30–40 phút cho cả bộ.

---

## Ánh xạ tiêu chí sang luật máy (dành cho nhóm nghiên cứu)

| Tiêu chí | Đối tượng YOLO | Luật |
|---|---|---|
| C1 | COCO: chair, backpack, suitcase, handbag, bench, … | Tỷ lệ chiếm dụng R = diện tích(∪ phần đáy hộp bao ∩ vùng lối đi) / diện tích(vùng lối đi). **Vi phạm nếu R ≥ τ₁** (τ₁ hiệu chỉnh, mặc định 5%) |
| C2 | COCO: cell phone, laptop, backpack, handbag, book | Đếm số vật có tâm hộp bao nằm trong vùng bàn. **Vi phạm nếu ≥ 3** |
| C3 | Model fine-tune: fire extinguisher | Tại vùng vị trí bình: **Vi phạm nếu không phát hiện được bình**, hoặc tỷ lệ bị che (phần hộp bao bình bị hộp vật khác phủ lên) **≥ 1/3** |
| C4 | COCO: cup, bottle, wine glass, bowl, banana, apple, sandwich, orange, pizza, donut, cake | **Vi phạm nếu có ít nhất 1 đối tượng** (độ tin cậy ≥ ngưỡng) |

> **Nguồn lỗi dự kiến (đưa vào phần thảo luận):** COCO gộp chai nước và chai hóa chất chung một lớp `bottle`, nên C4 sẽ báo động giả ở các ảnh có chai hóa chất. Chụp ảnh nên có chủ đích đưa các tình huống này vào (xem PHOTO_GUIDE).
