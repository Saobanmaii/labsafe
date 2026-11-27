# KỊCH BẢN CHỤP ẢNH ĐỂ TRAIN + QUAY VIDEO DEMO

> **Mục tiêu buổi chụp**
> 1. **Khoảng 200 ảnh** để train mô hình nhận diện những vật mà mô hình có sẵn đang nhận sai hoặc không nhận được.
> 2. **3 video** quay cố định để demo thực tế.
>
> Thời gian: khoảng **2 giờ** · 3 người.

---

## 0. Vì sao chụp những thứ này

Mô hình có sẵn đang mắc 3 lỗi chính ở phòng thí nghiệm của nhóm:

| Lỗi hiện tại | Hậu quả |
|---|---|
| Bình chữa cháy màu đỏ bị nhận là **chai nước** | C4 báo vi phạm nhầm |
| **Không nhận ra áo khoác, ví, mũ** | C2 đếm thiếu đồ cá nhân, C3 không biết bình bị áo che |
| Áo vắt trên ghế bị nhận là **người** | C1 bỏ sót ghế trong lối đi |

Mô hình mới sẽ được dạy **6 lớp** sau. Đây là những vật cần chụp thật nhiều:

| Lớp | Gồm những gì |
|---|---|
| `binh_chua_chay` | Bình chữa cháy |
| `ao_khoac` | Áo khoác, áo hoodie, áo mưa |
| `mu` | Mũ lưỡi trai, mũ bảo hiểm |
| `vi` | Ví, túi đựng thẻ |
| `do_uong` | Chai nước uống, bình giữ nhiệt, cốc, lon, ly trà sữa |
| `do_an` | Hộp cơm, bánh, bánh mì, trái cây, gói snack |

Ghế, balo, laptop, điện thoại, sách thì mô hình có sẵn đã nhận tốt. Không cần chụp riêng, nhưng **cứ để chúng xuất hiện tự nhiên** trong ảnh.

**Vật "bẫy"** là những vật **có xuất hiện trong ảnh nhưng KHÔNG gán nhãn**, để mô hình học được rằng chúng không phải đồ uống: chai cồn, lọ dung dịch vệ sinh mạch, hộp linh kiện, dụng cụ, máy đo của phòng.

---

## 1. Đồ mang theo

- [ ] **Áo khoác: 3–4 cái, màu khác nhau** (đen, trắng, màu sáng, áo đồng phục...)
- [ ] Mũ lưỡi trai: 2 · mũ bảo hiểm: 1
- [ ] Ví: 2–3 cái
- [ ] Đồ uống: 2–3 chai nước khác nhãn, 1 bình giữ nhiệt, 1 cốc, 1–2 lon, 1 ly trà sữa hoặc cà phê
- [ ] Đồ ăn: 1 hộp cơm, bánh mì hoặc bánh ngọt, 1–2 quả trái cây, 1 gói snack
- [ ] Bẫy: 1–2 chai cồn hoặc lọ dung dịch (nếu phòng có sẵn thì dùng luôn)
- [ ] 2 balo, 1 thùng carton, laptop, điện thoại, vở
- [ ] **Giá đỡ điện thoại hoặc chân máy** (bắt buộc cho phần video), sạc dự phòng
- [ ] Điện thoại: **chụp ngang**, zoom 1x, **tắt** chế độ chân dung, làm đẹp, bộ lọc

---

## 2. Quy tắc chụp

Quy tắc ở đây **khác** buổi chụp trước. Buổi trước cần đứng cố định, còn buổi này cần **đa dạng**.

1. **Mỗi ảnh đổi ít nhất một thứ**: vị trí đứng, góc máy, hoặc cách bày đồ. Không chụp liên tiếp hai ảnh gần giống nhau.
2. **Khoảng cách**:
   - khoảng **1/2 số ảnh chụp toàn cảnh** từ góc cao như camera giám sát (giơ máy cao hoặc đứng lên ghế), vì hệ thống thật nhìn phòng theo kiểu này và vật sẽ nhỏ;
   - 1/4 ảnh ở tầm trung (2–3 m);
   - 1/4 ảnh chụp gần (1 m).
3. **Hạn chế đứng đúng 6 vị trí của bộ 62 ảnh cũ.** Bộ cũ là bộ kiểm tra, ảnh train không nên giống nó.
4. **Không để mặt người trong ảnh.** Người bày đồ phải ra khỏi khung trước khi bấm chụp.
5. **Đổi ánh sáng** ở một phần ảnh: tắt bớt đèn, kéo hoặc mở rèm.
6. Chụp xong mỗi cảnh, **xem nhanh lại**, ảnh nhoè thì chụp lại.

---

## 3. Năm cảnh chụp (tổng ~195 ảnh)

### Cảnh A — Bình chữa cháy · 35 ảnh · thư mục `A_binh`

| Số ảnh | Cách bày |
|---|---|
| 10 | Bình **không bị che**, chụp từ nhiều góc và khoảng cách |
| 10 | Bình **bị che một phần** (1/3, 1/2) bởi áo khoác, balo, thùng, ghế |
| 8 | Bình **đứng cạnh chai nước, lon, cốc** (mô hình phải phân biệt bình với chai) |
| 7 | Toàn cảnh có bình ở xa, nhìn thấy nhỏ |

### Cảnh B — Áo khoác · 40 ảnh · thư mục `B_ao`

| Số ảnh | Cách bày |
|---|---|
| 10 | **Áo vắt lưng ghế**, lần lượt từng màu (đây là lỗi bị nhận nhầm thành người) |
| 10 | Áo trên bàn: gấp gọn, vứt bừa, cuộn lại |
| 8 | Áo **trùm hoặc che bình chữa cháy** |
| 7 | Áo trên sàn, trên balo, treo móc |
| 5 | Toàn cảnh có 2–3 áo ở nhiều chỗ |

### Cảnh C — Đồ ăn, đồ uống · 40 ảnh · thư mục `C_anuong`

| Số ảnh | Cách bày |
|---|---|
| 15 | Đồ uống trên bàn thí nghiệm: 1–3 món, đổi loại và vị trí |
| 10 | Đồ ăn trên bàn: hộp cơm, bánh, trái cây, có thể kèm đồ uống |
| 10 | Đồ uống, đồ ăn **đặt cạnh chai cồn, lọ dung dịch, dụng cụ** (bẫy) |
| 5 | Đồ ăn uống trên ghế, trên sàn, trên kệ |

### Cảnh D — Đồ cá nhân trên bàn · 40 ảnh · thư mục `D_canhan`

| Số ảnh | Cách bày |
|---|---|
| 15 | 1–2 món (ví, mũ, điện thoại, vở) để giữa thiết bị của phòng |
| 15 | 3–5 món cá nhân trên bàn (ví + mũ + điện thoại + laptop + vở...) |
| 10 | Mũ bảo hiểm và mũ lưỡi trai ở nhiều chỗ: bàn, ghế, sàn |

### Cảnh E — Cảnh tổng hợp · 40 ảnh · thư mục `E_tonghop`

| Số ảnh | Cách bày |
|---|---|
| 25 | **Bừa bộn tự nhiên**: trộn đồ của các cảnh trên, chụp toàn cảnh từ nhiều vị trí |
| 15 | **Phòng sạch** (dọn hết đồ mang theo), chụp toàn cảnh: để mô hình học rằng đồ của phòng không phải vi phạm |

> Một ảnh có thể chứa nhiều lớp, như vậy càng tốt. Mục tiêu là **mỗi lớp xuất hiện khoảng 100 lần** trên tổng số ảnh.

---

## 4. Ba video demo (~30 phút)

**Trước mỗi video:** đặt điện thoại lên giá, **chụp 1 ảnh phòng sạch từ đúng vị trí đó** (dùng làm ảnh nền để vẽ vùng), rồi bấm quay. **Không chạm vào điện thoại cho đến khi quay xong.**

Mỗi góc quay phải nhìn thấy **lối đi, bàn thí nghiệm và bình chữa cháy**. Mỗi vi phạm phải **giữ ít nhất 15 giây**, vì hệ thống cần 3 giây liên tiếp mới xác nhận.

### Video 1 — từng lỗi một (~2 phút)

| Thời điểm | Hành động |
|---|---|
| 0:00 | Phòng sạch, chưa có gì |
| 0:15 | Đặt **balo vào lối đi**, ra khỏi khung, chờ 20 giây, rồi lấy balo đi |
| 0:45 | **Một người đi nhanh ngang lối đi** (2–3 giây, quay lưng lại máy). Hệ thống **không được** báo vi phạm |
| 0:55 | Đặt **cốc và chai nước lên bàn**, chờ 20 giây, rồi lấy đi |
| 1:25 | **Trùm áo khoác lên bình chữa cháy**, chờ 20 giây, rồi gỡ ra |
| 1:55 | Phòng sạch thêm 15 giây, sau đó dừng quay |

### Video 2 — nhiều lỗi cùng lúc (~1,5 phút), góc khác video 1

| Thời điểm | Hành động |
|---|---|
| 0:00 | Phòng sạch |
| 0:15 | Lần lượt đặt lên bàn **ví, mũ, điện thoại, laptop** (C2) |
| 0:35 | Thêm **ghế vào lối đi** và **lon nước** trên bàn (C1 + C4) |
| 1:00 | Dọn từng món một |
| 1:20 | Phòng sạch 15 giây, sau đó dừng quay |

### Video 3 — góc cao như camera giám sát (~1,5 phút)

Đặt điện thoại **trên tủ hoặc kệ cao**, chĩa xuống phòng. Diễn lại tự do các tình huống của video 1 và 2.

---

## 5. Phân công

| Người | Việc |
|---|---|
| Người 1 | Chụp ảnh |
| Người 2 | Bày và dọn đồ theo kịch bản, **đánh dấu số ảnh đã chụp** cho từng cảnh |
| Người 3 | Xem lại ảnh nhoè, ghi giờ; đến phần video thì đặt máy và bấm giờ |

Thứ tự gợi ý: **quay video trước** (lúc phòng còn gọn), sau đó chụp các cảnh A → E, cuối cùng dọn phòng.

---

## 6. Lưu file

```
data/train_raw/A_binh/       ← ảnh cảnh A (tên file để nguyên như điện thoại đặt cũng được)
data/train_raw/B_ao/
data/train_raw/C_anuong/
data/train_raw/D_canhan/
data/train_raw/E_tonghop/
data/videos/video1.mp4  +  video1_ref.jpg   ← ảnh phòng sạch chụp trước video
data/videos/video2.mp4  +  video2_ref.jpg
data/videos/video3.mp4  +  video3_ref.jpg
```

⚠️ **Không chép ảnh mới vào `data/images/`.** Thư mục đó là bộ 62 ảnh kiểm tra, phải giữ nguyên.

Gửi điện thoại sang máy tính bằng cáp hoặc Google Drive **ở chế độ ảnh gốc** (Zalo hoặc Messenger sẽ nén mất chất lượng).

---

## 7. Kiểm tra trước khi rời phòng

- [ ] Đủ khoảng 40 ảnh cho mỗi cảnh A–E, không ảnh nào nhoè
- [ ] Mỗi lớp (bình, áo, mũ, ví, đồ uống, đồ ăn) đã xuất hiện nhiều lần ở **nhiều góc và khoảng cách**
- [ ] Có ảnh toàn cảnh từ góc cao
- [ ] 3 video, mỗi video có kèm **ảnh phòng sạch** chụp từ đúng vị trí đặt máy
- [ ] Không có mặt người
- [ ] Trả phòng về nguyên trạng, mang hết đồ ăn uống ra ngoài

---

## Sau buổi chụp

1. **Gán nhãn**: khoanh khung 6 lớp trên Roboflow, khoảng 3–4 giờ chia cho 3 người. Quy tắc quan trọng: **trong mỗi ảnh, vật nào thuộc 6 lớp đều phải khoanh**, sót một vật thì mô hình sẽ học sai.
2. Train YOLO trên ảnh mới, rồi **chấm lại 62 ảnh cũ** để so sánh κ trước và sau.
3. Vẽ vùng cho 3 góc video, chạy demo trên trang «Video & camera».
