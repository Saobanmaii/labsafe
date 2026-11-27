# Ôn tập trước khi gặp thầy

> Mục tiêu: **tự giải thích được bằng lời của mình** từng phần dưới đây, không cần thuộc code.
> Thời gian đọc: khoảng 1–2 tiếng. Phần nào có ghi "Mở file" thì nên mở ra xem tận mắt.

---

## 1. Hệ thống chạy thế nào (phải nói được trong 1 phút)

```
Ảnh ──┬──► YOLO tìm đồ vật ──► Bộ luật + vùng vẽ sẵn ──► C1..C4 (0/1) + ảnh bằng chứng
      │
      └──► Gemini đọc ảnh + prompt ──► C1..C4 (0/1) + lý do
                                                    │
               3 người chấm (lấy đa số) ──► so sánh bằng κ
```

Hai hướng chạy **độc lập** trên cùng 62 ảnh, rồi cùng được so với đáp án của người.

---

## 2. YOLO và COCO

**YOLO** là mô hình **phát hiện vật thể**. Nó nhận một ảnh và trả về danh sách: *tên vật, độ tin cậy, khung chữ nhật (toạ độ)*.

**COCO** là bộ dữ liệu 80 lớp vật thể phổ biến (người, ghế, cốc, chai, điện thoại, laptop…). YOLO "có sẵn" nghĩa là đã được người ta huấn luyện trên COCO, tải về là dùng được.

Hệ thống dùng **3 mô hình**:

| Mô hình | Tìm gì | Vì sao cần |
|---|---|---|
| YOLO11s (COCO, có sẵn) | ghế, balo, cốc, chai, điện thoại, sách… | Phần lớn đồ vật cần tìm |
| YOLO11n **nhóm tự huấn luyện** | bình chữa cháy | COCO **không có** lớp bình chữa cháy |
| YOLO-World | thùng carton | Gõ tên vật bằng chữ là tìm được, không cần huấn luyện |

Ngưỡng tin cậy 0,30: vật nào YOLO chắc dưới 30% thì bỏ.

### Huấn luyện mô hình bình chữa cháy
- Dữ liệu: bộ **Fire-ART**, chỉ giữ lớp bình chữa cháy, thêm ảnh không có bình. Tổng 358 ảnh, chia 287 huấn luyện / 71 kiểm tra.
- Cách làm: lấy YOLO11n đã học COCO, **huấn luyện tiếp** (fine-tune) trên dữ liệu bình. Đây gọi là học chuyển giao (transfer learning).
- Kết quả: **mAP@0,5 = 0,80**.

**mAP@0,5 là gì?** Đo mô hình tìm vật đúng đến đâu. Một khung được tính là đúng nếu chồng lên khung thật từ 50% trở lên (IoU ≥ 0,5). mAP gần 1 là tốt. 0,80 là ổn với lượng dữ liệu ít.

**Precision 0,88 / Recall 0,67:** khi mô hình báo "có bình" thì đúng 88% (ít báo nhầm). Nhưng nó chỉ tìm ra 67% số bình thật (còn bỏ sót).

---

## 3. Vùng chức năng (zones)

YOLO chỉ biết "có cái ghế ở toạ độ này", **không biết** ghế đó nằm trên lối đi hay sát bàn. Vì vậy nhóm **vẽ tay đa giác** cho từng góc chụp:
- **lối đi** (aisle)
- **mặt bàn** (bench)
- **chỗ đặt bình** (extinguisher)

Mỗi góc camera chỉ vẽ một lần, giống camera giám sát thật được cấu hình vùng một lần. Toạ độ lưu dạng tỉ lệ 0–1 trong `data/zones.json`.

> Thầy có thể hỏi: *"Sao không tự tìm vùng bằng segmentation?"*
> Trả lời: "Vẽ tay đơn giản và chính xác vì camera cố định. Tự tách vùng bằng semantic segmentation là hướng cải tiến của nhóm."

---

## 4. Bộ luật (rule engine). Mở file `src/rules.py`

Đây là phần **dễ hiểu nhất và quan trọng nhất**, nên đọc kỹ. Toàn bộ là tính diện tích giao nhau giữa khung vật và vùng (dùng thư viện Shapely).

| Tiêu chí | Luật | Ghi nhớ |
|---|---|---|
| **C1 Lối đi** | Lấy **25% phần đáy** khung của vật cản (coi như chân vật chạm sàn). Tính `R = diện tích bị chiếm / diện tích lối đi`. **R ≥ 5% → vi phạm** | Lấy phần đáy vì cái ghế ở xa trông như "nằm trong" lối đi trên ảnh 2D, nhưng chân nó mới cho biết nó thật sự đứng ở đâu |
| **C2 Đồ cá nhân** | Đếm đồ cá nhân (điện thoại, laptop, balo, túi, sách) có **tâm khung nằm trong vùng bàn**. **≥ 3 → vi phạm** | |
| **C3 Bình chữa cháy** | Trong vùng chỗ đặt bình: **không thấy bình**, hoặc thấy **< 50%**, hoặc bị vật khác **phủ ≥ 1/3 → vi phạm** | |
| **C4 Đồ ăn uống** | Có **ít nhất 1** cốc, chai, đồ ăn ở bất kỳ đâu → vi phạm | Không cần vùng |

Các ngưỡng (5%, 3, 50%, 1/3) **được đặt trước khi xem kết quả**, không chỉnh để đẹp số. Nếu thầy hỏi, nhấn mạnh điểm này.

---

## 5. Gemini (VLM). Mở file `src/run_vlm.py`, dòng 30–57

**VLM** (Vision-Language Model) là mô hình vừa nhìn ảnh vừa hiểu chữ. Gửi ảnh kèm câu hỏi, nó trả lời bằng chữ. Nhóm dùng **gemini-3.5-flash** qua API.

- **Zero-shot:** không huấn luyện gì, chỉ mô tả tiêu chí bằng lời trong prompt.
- Bắt trả về **JSON**: `{"C1": 0/1, "C2": ..., "reason": "..."}` để máy đọc được.
- `temperature = 0`: để câu trả lời ít ngẫu nhiên nhất.

**3 prompt:**

| Prompt | Khác nhau ở đâu | Mục đích |
|---|---|---|
| P1 | Mô tả chi tiết, thứ tự C1→C4 | Bản chính |
| P2 | Rút gọn, mỗi tiêu chí 1 dòng | Xem bớt mô tả thì kết quả có tụt không |
| P3 | Chi tiết như P1 nhưng **đảo thứ tự** C4→C1 | Xem thứ tự có ảnh hưởng không |

Kết luận: P2 tụt mạnh ở C1, C2, tức **mô tả chi tiết quan trọng**. P3 gần P1, tức thứ tự ảnh hưởng ít hơn.

P2, P3 mới chạy khoảng 33 ảnh vì gói Gemini miễn phí chỉ cho khoảng 20 lượt/ngày/tài khoản.

---

## 6. Đánh giá: các chỉ số. Mở file `outputs/table_main.csv`

### Đáp án
3 người chấm độc lập. Ô nào **2/3 người** nói vi phạm thì đáp án là vi phạm (bỏ phiếu đa số).

### Độ khớp (accuracy)
Tỉ lệ ảnh máy chấm giống đáp án. **Nhược điểm:** C2 có 51/62 ảnh "Đạt". Một máy lúc nào cũng nói "Đạt" vẫn khớp 82%, dù chẳng làm gì. Vì vậy cần κ.

### Cohen's κ (kappa): chỉ số chính
Đo mức khớp **sau khi trừ phần khớp do may rủi**.
- 1: khớp hoàn toàn. 0: như đoán bừa. Âm: tệ hơn đoán bừa.
- Thang tham khảo: < 0,4 yếu, 0,4–0,6 trung bình, 0,6–0,8 khá, > 0,8 rất tốt.
- Cohen's κ dùng để so **2 bên** (máy với đáp án).

### Fleiss κ
Giống Cohen's κ nhưng cho **nhiều người** (3 người chấm với nhau). Cho biết tiêu chí rõ ràng đến đâu: người còn lệch nhau thì máy khó khớp cao.

| | C1 | C2 | C3 | C4 |
|---|---|---|---|---|
| Fleiss κ (người với người) | 0,89 | **0,69** | 0,98 | 0,96 |

C2 thấp nhất vì người chấm hay phân vân "cái này có phải đồ cá nhân không".

### Khoảng tin cậy 95% (bootstrap): thanh lỗi trên biểu đồ
Bốc ngẫu nhiên có hoàn lại 62 ảnh, tính κ, lặp lại hàng nghìn lần. 95% số kết quả nằm trong khoảng nào thì đó là khoảng tin cậy.
- **Khoảng rộng = kết quả chưa chắc chắn**, do ít ảnh.
- Hai phương pháp có khoảng chồng lên nhau thì **chưa khẳng định được** cái nào hơn.

### F1, TP, FP, FN
- **TP:** vi phạm thật, máy báo vi phạm (đúng).
- **FP:** không vi phạm, máy báo vi phạm (**báo nhầm**).
- **FN:** vi phạm thật, máy nói đạt (**bỏ sót**).
- **F1:** điểm cân bằng giữa báo nhầm và bỏ sót, tính riêng cho lớp "vi phạm".

---

## 7. Kết quả. Phải thuộc mấy con số này

| κ | C1 Lối đi | C2 Đồ cá nhân | C3 Bình | C4 Ăn uống |
|---|---|---|---|---|
| Người với người | 0,89 | 0,69 | 0,98 | 0,96 |
| **YOLO + luật** | **0,74** | 0,58 | **0,90** | 0,78 |
| **Gemini P1** | 0,44 | **0,88** | 0,78 | **0,97** |

**Một câu tóm tắt:** *Luật giỏi tiêu chí về **vị trí** (C1, C3), Gemini giỏi tiêu chí về **loại đồ vật** (C2, C4).*

### Vì sao? (phân tích lỗi, xem `outputs/errors.csv`)

| Lỗi | Nguyên nhân | Ảnh hưởng |
|---|---|---|
| Luật báo nhầm C4 (7 ca) | YOLO COCO nhận **bình chữa cháy màu đỏ thành "bottle"** | 6/7 ca báo nhầm C4 |
| Luật bỏ sót C2 (6 ca) | COCO **không có lớp áo khoác** | Áo khoác trên bàn không được đếm |
| Gemini báo nhầm C1 (16 ca) | Gemini **không biết vùng lối đi** ở đâu, thấy ghế là báo | κ C1 chỉ 0,44 |
| Gemini bỏ sót C3 (7 ca) | Đôi khi không thấy bình lại cho là "đạt" | |

---

## 8. Câu hỏi thầy có thể hỏi và gợi ý trả lời

**"Sao C2 Gemini (0,88) lại khớp hơn cả người với nhau (0,69)?"**
> Gemini được so với **nhãn đa số** của 3 người, nhãn này đã lọc bớt chỗ từng người chấm lệch. Còn 0,69 là mức các người chấm **riêng lẻ** đồng ý với nhau. Hai con số đo hai thứ khác nhau nên không mâu thuẫn.

**"62 ảnh có ít quá không?"**
> Có, đó là hạn chế chính. Khoảng tin cậy còn rộng, và mới có 1 phòng thí nghiệm. Hướng tiếp là chụp thêm phòng khác.

**"Phần nào nhóm tự huấn luyện?"**
> Mô hình bình chữa cháy (fine-tune YOLO11n trên Fire-ART, mAP 0,80). Các phần khác dùng mô hình có sẵn.

**"Ngưỡng 5%, 1/3 lấy từ đâu?"**
> Nhóm đặt dựa trên định nghĩa tiêu chí trong bảng chấm (ví dụ "che khoảng 1/3"), **cố định trước khi chạy**, không chỉnh theo kết quả.

**"Sao không dùng accuracy?"**
> Dữ liệu lệch, ví dụ C2 có 51/62 ảnh đạt. Đoán bừa "đạt" hết vẫn được 82%. κ trừ phần may rủi nên công bằng hơn.

**"Sao chọn Gemini mà không phải mô hình khác?"**
> Có API miễn phí, nhận ảnh được. Code đã viết sẵn để chạy cả Claude. Thử thêm mô hình là hướng mở rộng.

**"Kết hợp hai hướng được không?"**
> Được, và đó là kế hoạch: dùng luật cho C1, C3 và Gemini cho C2, C4. Nhìn bảng κ thì cách ghép này cho mỗi tiêu chí phương pháp tốt nhất.

**"Hệ thống chạy nhanh không?"**
> YOLO + luật khoảng 0,13 giây/ảnh trên laptop, chạy offline. Gemini khoảng 10 giây/ảnh và cần mạng.

**Câu hỏi về chi tiết code mà chưa nắm:**
> "Phần này em chưa đọc kỹ, em sẽ xem lại và báo thầy." Nói thật vẫn tốt hơn trả lời bừa.

---

## 9. Thứ tự đọc nếu ít thời gian

1. Mục 7 (kết quả + phân tích lỗi): **bắt buộc**
2. Mục 4 (bộ luật): **bắt buộc**
3. Mục 6 (κ, khoảng tin cậy): **bắt buộc**
4. Mục 8 (câu hỏi)
5. Mục 2, 3, 5
