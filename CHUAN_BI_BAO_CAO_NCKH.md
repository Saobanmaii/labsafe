# Chuẩn bị báo cáo NCKH

**Đề tài:** Chấm điểm an toàn phòng thí nghiệm từ ảnh: so sánh hệ thống dựa trên luật và mô hình ngôn ngữ–thị giác với đánh giá của con người
**Nhóm:** Trần Tuấn Kiệt · Lành Diệu Hương · Lê Quốc Dũng

**Cách dùng file này:**
- **Cả 3 người** đọc kỹ **Phần 0** (chung). Ai cũng phải trả lời được các câu hỏi ở Phần 0.
- Mỗi người đọc **phần của mình** (Phần 1, 2 hoặc 3) thật kỹ, tập nói theo "Nói gì", biết "Show gì" và chuẩn bị câu hỏi.
- Đọc lướt phần của 2 người kia để đỡ lời khi cần.
- Phân công dưới đây là gợi ý; nhóm đổi người cho hợp thì cứ đổi.

## Khung trình bày theo hướng dẫn của thầy

Thầy gợi ý trình bày theo 4 bước: **① ý tưởng, đặt vấn đề → ② giải quyết vấn đề gì → ③ thuật toán → ④ hướng giải quyết**. Vai trò vẫn giữ như cũ, chỉ sắp lại thứ tự nói:

| Bước | Người nói | Nội dung | Show trong bài báo | Thời gian |
|---|---|---|---|---|
| **① Ý tưởng, đặt vấn đề** | **Kiệt** | Kiểm tra an toàn đang làm thủ công, 3 hạn chế; nghiên cứu trước chỉ nhìn người, chưa nhìn căn phòng | Trang 1, mục I | 1,5 phút |
| **② Giải quyết vấn đề gì** | **Kiệt** | Mục tiêu: máy chấm từ ảnh có giống người không; 3 câu hỏi RQ1–RQ3; thiết kế 3 cột; 4 tiêu chí | Mục I (RQ), Hình 1, Bảng I | 2 phút |
| **③ Thuật toán (a): YOLO + bộ luật** | **Hương** | 3 bộ phát hiện, mô hình bình tự huấn luyện, vùng, **thuật toán luật C1–C4** (mã giả), dữ liệu | Mục III.C, Hình 2, công thức R, V, O, mục IV.A | 4 phút |
| **③ Thuật toán (b): Gemini + cách đánh giá** | **Dũng** | Cách gọi Gemini, 3 prompt; người chấm, nhãn đa số, cách tính κ | Mục III.D, III.E | 1,5 phút |
| **④ Hướng giải quyết: kết quả** | **Dũng** | Giải quyết được đến đâu: bảng kết quả, đổi prompt, phân tích lỗi | Bảng II, III, IV, Hình 3, 4 | 3,5 phút |
| **④ Hướng giải quyết: kết luận, đi tiếp** | **Kiệt** | Trả lời RQ1–RQ3, đề xuất hệ thống lai, hạn chế, việc làm tiếp | Mục V | 1,5 phút |

Thứ tự lên nói: **Kiệt (① ②) → Hương (③a) → Dũng (③b, ④ kết quả) → Kiệt (④ kết luận)**.

**Lưu ý:** "hướng giải quyết" ở đây hiểu là *đã giải quyết thế nào, được đến đâu, và đi tiếp ra sao*. Nếu thầy hiểu là *cách tiếp cận* thì phần đó đã có ở ③; Kiệt nói thêm một câu tổng kết "nhóm giải quyết bằng hai hướng: luật và VLM" là đủ.

---

# PHẦN 0. CHUNG CHO CẢ NHÓM

## 0.1 Đề tài trong 30 giây (ai cũng phải nói được)

> Hiện nay kiểm tra an toàn phòng thí nghiệm phải có người đi xem tận nơi. Nhóm thử cho máy tự chấm từ một tấm ảnh, theo 4 tiêu chí: vật cản lối đi, đồ cá nhân trên bàn, bình chữa cháy bị che, và đồ ăn uống. Nhóm làm hai cách: một là **YOLO kết hợp bộ luật**, hai là **hỏi thẳng AI Gemini**. Cả hai được so với **3 người chấm thật** trên **62 ảnh** nhóm tự chụp. Kết quả: hai cách **giỏi ở hai chỗ khác nhau**. Luật giỏi các tiêu chí về **vị trí**, Gemini giỏi các tiêu chí về **nhận biết đồ vật**, nên kết hợp cả hai là tốt nhất.

## 0.2 Các con số phải thuộc

| Thứ | Số |
|---|---|
| Số ảnh thử nghiệm | **62 ảnh**, 1 phòng thí nghiệm **điện tử**, 6 góc chụp |
| Số người chấm | **3 người**, không tham gia dàn dựng ảnh, lấy **đa số** làm đáp án |
| Mô hình tự huấn luyện | Phát hiện **bình chữa cháy**, YOLO11n, **mAP@0,5 = 0,80** |
| Dữ liệu huấn luyện | **358 ảnh** từ bộ công khai **Fire-ART** (179 có bình, 179 không) |
| Gemini | Phiên bản **gemini-3.5-flash**, **3 prompt** (P1, P2, P3) |

**Bảng kết quả chính (Cohen's κ so với người chấm):**

| | C1 Lối đi | C2 Đồ cá nhân | C3 Bình chữa cháy | C4 Ăn uống |
|---|---|---|---|---|
| Người với người (Fleiss κ) | 0,89 | 0,69 | 0,98 | 0,96 |
| YOLO + luật | **0,74** | 0,58 | **0,90** | 0,78 |
| Gemini (P1) | 0,44 | **0,88** | 0,78 | **0,97** |

Cách nhớ: **luật thắng C1, C3 (vị trí) — Gemini thắng C2, C4 (đồ vật).**

## 0.3 Hệ thống chạy thế nào (sơ đồ cả nhóm phải vẽ lại được)

```
                     ┌─► Cột 1: 3 người chấm ──► nhãn đa số (đáp án)
                     │
 Ảnh phòng TN ───────┼─► Cột 2: YOLO tìm đồ vật ──► bộ luật theo vùng ──► C1..C4
                     │        (3 mô hình)           (lối đi, bàn, bình)
                     │
                     └─► Cột 3: Gemini + prompt ─────────────────────────► C1..C4

                     So sánh cột 2 và cột 3 với cột 1, riêng từng tiêu chí (κ)
```

Ba "cột" độc lập: không cột nào thấy kết quả của cột khác. Ảnh thử nghiệm **không** dùng để huấn luyện mô hình nào.

## 0.4 Bốn tiêu chí

Mỗi tiêu chí chỉ có 2 đáp án: **0 = Đạt**, **1 = Vi phạm** (chấm nhị phân).

| Mã | Tiêu chí | Vi phạm khi |
|---|---|---|
| C1 | Vật cản lối đi | Có vật cỡ từ balo trở lên (ghế, balo, thùng…) đặt trên sàn ở lối đi |
| C2 | Đồ cá nhân trên bàn | Từ **3** đồ cá nhân trở lên trên mặt bàn (điện thoại, laptop, balo, ví, sách vở, áo khoác, mũ). Thiết bị đo, mỏ hàn, máy tính của phòng không tính |
| C3 | Bình chữa cháy bị che | Bị che từ **1/3** trở lên, có vật chắn phía trước, hoặc không còn ở chỗ cũ |
| C4 | Đồ ăn, đồ uống | Có **bất kỳ** đồ ăn uống nào. Chai cồn, dung dịch vệ sinh mạch không tính |

Vì sao chỉ 4 tiêu chí nhị phân (đề cương ban đầu có 6 tiêu chí, thang 3 mức)? **Để giảm chủ quan khi chấm**, và bỏ 2 tiêu chí khó thấy trong ảnh (hoá chất ngoài tủ, dây điện cắt ngang lối đi).

## 0.5 Từ vựng ai cũng phải hiểu

| Từ | Nghĩa dễ hiểu |
|---|---|
| **YOLO** | Mô hình phát hiện đối tượng: nhìn ảnh, vẽ **khung** quanh mỗi vật, kèm **tên lớp** và **độ tin cậy** (0–1). "You Only Look Once": nhìn ảnh một lần là ra hết. |
| **COCO** | Bộ dữ liệu 80 loại đồ vật phổ biến. YOLO "có sẵn" đã học trên bộ này. **Không có** bình chữa cháy, áo khoác, thùng carton. |
| **Huấn luyện / tinh chỉnh (fine-tune)** | Lấy mô hình đã học COCO, cho học tiếp trên ảnh mới để biết thêm lớp mới (bình chữa cháy). Nhanh hơn học từ đầu. |
| **Bộ luật (rule engine)** | Các quy tắc "nếu… thì…" viết bằng code, ví dụ "có ghế chiếm ≥ 5% lối đi thì vi phạm". |
| **Vùng (zone)** | Đa giác vẽ tay trên ảnh, cho máy biết đâu là lối đi, mặt bàn, chỗ đặt bình. Vẽ **1 lần cho mỗi góc camera**. |
| **VLM** | Vision-Language Model, mô hình ngôn ngữ–thị giác: AI vừa nhìn ảnh vừa hiểu chữ. Gemini là một VLM. |
| **Prompt** | Câu hỏi/hướng dẫn gửi kèm ảnh cho Gemini. |
| **Zero-shot** | Dùng mô hình **không huấn luyện thêm**, không cho ví dụ mẫu, chỉ mô tả bằng lời. |
| **Nhãn đa số** | Đáp án mỗi ô = ý kiến của ít nhất 2/3 người chấm. |
| **κ (kappa)** | Độ khớp **đã trừ phần ăn may**. 0 = như đoán bừa, 1 = khớp hoàn toàn. Xem 0.6. |
| **FP / FN** | FP = báo động giả (máy nói vi phạm, thật ra đạt). FN = bỏ sót (máy nói đạt, thật ra vi phạm). |

## 0.6 Kappa: phải giải thích được vì sao dùng κ chứ không dùng %

**Vì sao không dùng % khớp?** Vì bị "ăn may". C2 chỉ có 11/62 ảnh vi phạm. Một máy "lười", ảnh nào cũng nói Đạt, vẫn khớp 51/62 = **82%**, nhưng κ = **0**.

**Công thức Cohen's κ** (2 nguồn chấm):

```
κ = (p_o − p_e) / (1 − p_e)
  p_o = tỉ lệ khớp thật
  p_e = tỉ lệ khớp nếu cả hai đoán bừa (theo tỉ lệ vi phạm của mỗi bên)
```

**Ví dụ tính tay** (luật, tiêu chí C3, 62 ảnh):

```
Máy VP & Người VP : 31     Máy VP & Người Đạt: 2  (báo động giả)
Máy Đạt & Người VP:  1     Máy Đạt & Người Đạt: 28
p_o = (31+28)/62 = 0,952
p_e = (33/62)(32/62) + (29/62)(30/62) = 0,503
κ = (0,952 − 0,503)/(1 − 0,503) = 0,90
```

**Fleiss' κ**: giống Cohen nhưng cho **3 người trở lên** chấm cùng lúc. Dùng để đo người với người.

**Thang đọc κ** (Landis & Koch 1977):

| < 0,20 | 0,21–0,40 | 0,41–0,60 | 0,61–0,80 | > 0,80 |
|---|---|---|---|---|
| kém | khá | trung bình | đáng kể | gần như hoàn hảo |

**Khoảng tin cậy 95% (CI)**: vì chỉ có 62 ảnh, κ dao động. Nhóm lấy mẫu lại ngẫu nhiên 2.000 lần (bootstrap) để ước lượng khoảng giá trị thật có thể nằm trong. Ví dụ C1 luật: 0,74 [0,56; 0,90].

## 0.7 Cách show bài báo

Mở PDF trên Overleaf, **phóng to 125–150%**, cuộn đến đúng chỗ khi người nói nhắc tới. Một người (gợi ý: người **không** đang nói) cầm máy cuộn.

| Khi nói về | Cuộn tới |
|---|---|
| Đề tài, nhóm | Trang 1: tiêu đề, tác giả, tóm tắt |
| Câu hỏi nghiên cứu | Mục I, danh sách RQ1–RQ3 |
| Thiết kế 3 cột | **Hình 1** |
| 4 tiêu chí | **Bảng I** |
| Hệ thống luật | **Hình 2** (lưu đồ) + công thức R |
| Người chấm đồng ý | **Bảng II** |
| Kết quả chính | **Bảng III** + **Hình 3** (biểu đồ κ) |
| Đổi prompt | **Bảng IV** |
| Ca lỗi | **Hình 4** |
| Kết luận | Mục V |

**Nên chuẩn bị thêm (mở sẵn tab):** thư mục `outputs/annotated/`, mở 2 ảnh `v1_05.jpg` (bình bị nhận thành chai) và `v3a_08.jpg` (ghế có áo bị nhận là người). Thầy hỏi "máy thấy gì" thì mở cho xem.

## 0.8 Câu hỏi chung, ai cũng phải trả lời được

**Đề tài mới ở chỗ nào?**
Các nghiên cứu trước chủ yếu phát hiện **đồ bảo hộ trên người** (mũ, kính, áo blouse). Nhóm đánh giá **trạng thái căn phòng** (lối đi, mặt bàn, bình chữa cháy). Và chưa thấy nghiên cứu nào so sánh trực tiếp **luật, VLM và người chấm** trong bối cảnh này.

**Phần nào nhóm tự làm, phần nào dùng có sẵn?**
Tự làm: huấn luyện mô hình bình chữa cháy, bộ luật không gian, công cụ vẽ vùng, bộ 62 ảnh + nhãn 3 người, toàn bộ đánh giá. Dùng có sẵn: YOLO COCO, YOLO-World, Gemini.

**Vì sao phòng điện tử, không phải phòng hoá?**
Học viện không có phòng thí nghiệm hoá. 4 tiêu chí vẫn áp dụng được; nhóm điều chỉnh định nghĩa cho phù hợp (thiết bị đo, chai dung dịch vệ sinh mạch không tính là đồ cá nhân/đồ uống).

**Vì sao chỉ 62 ảnh, 1 phòng?**
Bị giới hạn thời gian và quyền vào phòng. Đã ghi rõ trong mục Hạn chế. Bù lại, ảnh được dàn dựng có chủ đích để mỗi tiêu chí có đủ ca vi phạm và ca đạt (C1: 32, C3: 32, C4: 26 vi phạm trên 62; riêng C2 chỉ 11).

**Ảnh dàn dựng thì có thật không?**
Là hạn chế (i) trong bài. Dàn dựng giúp kiểm soát được tình huống, kể cả **ảnh bẫy** để thử máy. Hướng phát triển là dùng ảnh từ camera giám sát thực tế.

**Nhóm có dùng AI để làm không?** *(trả lời thật)*
Có dùng trợ lý AI hỗ trợ viết code và soạn bài. Nhóm hiểu thiết kế, tự chụp ảnh, tổ chức người chấm, và đã kiểm tra lại số liệu. *(Mỗi người phải nắm chắc phần mình nói để chứng minh điều này.)*

**Kết luận một câu?**
Không cách nào thắng hết. Luật tốt cho tiêu chí cần biết **vị trí** (C1, C3), Gemini tốt cho tiêu chí cần **nhận ra đồ vật** (C2, C4), nên hệ thống thực tế nên **kết hợp**.

---

# PHẦN 1. KIỆT — ① Đặt vấn đề, ② Giải quyết vấn đề gì, ④ Kết luận

**Mục bài báo:** Tóm tắt, I (Giới thiệu), II (Nghiên cứu liên quan), III.A (Thiết kế), III.B (Bảng tiêu chí), V (Kết luận).

## 1.1 Nói gì

### ① Ý tưởng, đặt vấn đề (khoảng 1,5 phút)

1. **Chào, giới thiệu** đề tài và nhóm. *(Show: trang 1)*
2. **Ý tưởng xuất phát:** kiểm tra an toàn phòng thí nghiệm hiện làm thủ công, có 3 hạn chế: tốn người nên không làm thường xuyên được; mỗi người chấm một kiểu, thiếu nhất quán; không lưu bằng chứng để theo dõi. Trong khi camera đã có sẵn ở nhiều nơi → **liệu có cho máy chấm từ ảnh được không?**
3. **Khoảng trống (chỉ 1–2 câu, không đọc từng bài):** nghiên cứu trước chủ yếu phát hiện **đồ bảo hộ trên người**, ít ai đánh giá **trạng thái căn phòng**. VLM như Gemini chấm được mà không cần huấn luyện, nhưng nhiều nghiên cứu cho thấy nó **chưa ổn định**. Bảng nghiên cứu liên quan ở 1.2 chỉ để trả lời khi thầy hỏi.

### ② Giải quyết vấn đề gì (khoảng 2 phút)

4. **Mục tiêu:** đo xem máy chấm từ ảnh **khớp với người đến đâu**, và **cách nào tốt hơn**. Cụ thể là 3 câu hỏi *(Show: danh sách RQ ở mục I)*:
    - RQ1: Máy chấm khớp với người ở mức nào, từng tiêu chí?
    - RQ2: Luật hay VLM gần người hơn, ở tiêu chí nào?
    - RQ3: VLM có ổn định khi đổi cách hỏi không?
5. **Thiết kế 3 cột** *(Show: Hình 1)*: cùng bộ ảnh, 3 nguồn chấm độc lập, so cột 2 và 3 với cột 1.
6. **4 tiêu chí** *(Show: Bảng I)*: đọc nhanh 4 dòng. Giải thích vì sao chọn **nhị phân** và **4 tiêu chí** (0.4).
7. Chuyển lời: *"Tiếp theo là phần thuật toán. Hương trình bày hướng thứ nhất: YOLO kết hợp bộ luật."*

### ④ Hướng giải quyết: kết luận và đi tiếp (cuối buổi, khoảng 1,5 phút)

*(Show: mục V)*
- RQ1: cả hai cách đều từ mức trung bình trở lên (κ ≥ 0,44); ở tiêu chí tốt nhất thì gần bằng người với người.
- RQ2: luật thắng C1, C3; Gemini thắng C2, C4.
- RQ3: Gemini ổn định ở C3, C4, dao động ở C1, C2.
- Đề xuất: **hệ thống lai**, luật cho C1, C3 và Gemini cho C2, C4.
- Hạn chế: 1 phòng, ảnh dàn dựng, 62 ảnh, C2 ít ca vi phạm, P2/P3 chỉ 33 ảnh, luật tính trên ảnh 2D.
- Hướng phát triển: nói theo **Phần 4** (chọn 3–4 ý chính ở 4.1, nếu thầy hỏi thêm thì mới nói chi tiết).

## 1.2 Kiến thức cần nắm kỹ

**Nghiên cứu liên quan (mục II), nhớ mỗi bài một ý:**

| Bài | Làm gì | Ý chính để nhắc |
|---|---|---|
| Ali và cộng sự 2022 | YOLOv5, YOLOv7 giám sát an toàn phòng TN giáo dục, 481 ảnh | mAP cao nhất 77,4% — nhưng phát hiện **người**, không phải căn phòng |
| PPE 2024 | So sánh YOLOv4/5/6 phát hiện đồ bảo hộ ở xưởng | mAP 0,757 |
| YOLOv7-PPE 2024 | Cải tiến YOLOv7 cho bài toán tương tự | — |
| iSafetyBench 2025 | 1.100 video công nghiệp, 8 mô hình video–ngôn ngữ | VLM zero-shot **gặp khó** nhận diện hoạt động nguy hiểm |
| SteelBench 2026 | Đánh giá an toàn ngành thép | Nhận dạng đúng hành động vẫn phán đoán an toàn sai **37–58%** |
| Goyal và cộng sự 2026 | VLM chấm điểm zero-shot | **Sụp đổ lớp** (85–100% dự đoán rơi vào 1 mức), đổi prompt lệch tới **32 điểm %** |
| Weng và cộng sự 2026 | Độ nhạy của VLM với prompt | Prompt cùng nghĩa vẫn cho kết quả khác nhau |

**Ba đóng góp của bài (mục I):**
1. Bảng tiêu chí nhị phân có định nghĩa định lượng cho 4 tiêu chí.
2. Hệ thống luật không gian, mô hình huấn luyện trên dữ liệu công khai, thử trên ảnh thực tế khác miền (khác loại ảnh với lúc huấn luyện).
3. Thiết kế đánh giá 3 cột + phân tích ca lỗi.

**Vì sao người chấm là "đáp án"?** Không có đáp án tuyệt đối cho "gọn gàng". Người là chuẩn thực tế mà hệ thống muốn thay thế. Fleiss κ giữa người được coi là **trần tham chiếu**: máy khó vượt mức người đồng ý với nhau.

## 1.3 Câu hỏi có thể gặp

**Sao không dùng thang 3 mức như đề cương?**
Thang 3 mức (tốt/trung bình/kém) chủ quan hơn, người chấm dễ lệch nhau. Nhị phân có định nghĩa định lượng (≥ 3 vật, ≥ 1/3) nên đồng thuận cao hơn.

**Ứng dụng thực tế thế nào?**
Gắn vào camera có sẵn, chụp định kỳ, chấm tự động, báo cho cán bộ phụ trách khi vi phạm. Vùng chỉ cần vẽ 1 lần cho mỗi camera.

**Đề tài khác gì so với dùng YOLO bình thường?**
YOLO chỉ nói "có cái ghế". Đề tài thêm **luật không gian** để biết ghế có chắn lối đi không, và **so sánh có hệ thống** với VLM và người.

---

# PHẦN 2. HƯƠNG — ③ Thuật toán (a): YOLO + bộ luật

**Mục bài báo:** III.C (Hệ thống dựa trên luật), IV.A (Dữ liệu).

## 2.1 Nói gì (khoảng 4 phút)

Thầy nhấn mạnh **thuật toán**, nên trọng tâm là bước 3–4 (lưu đồ và luật từng tiêu chí). Nắm thật chắc **mã giả ở 2.2**: thầy hỏi "thuật toán chạy thế nào" thì nói theo mã giả đó.

1. **Ba bộ phát hiện** *(Show: danh sách đầu mục III.C)*:
    - YOLO11 **có sẵn** (học trên COCO): ghế, balo, túi, cốc, chai, điện thoại, laptop, sách.
    - YOLO11 **nhóm tự tinh chỉnh** để phát hiện **bình chữa cháy**, vì COCO không có lớp này.
    - **YOLO-World**: gõ tên lớp bằng chữ ("cardboard box") để tìm thùng carton, COCO cũng không có.
2. **Vùng chức năng:** mỗi góc camera khoanh 3 vùng một lần: lối đi A, mặt bàn B, chỗ đặt bình Z. Giống cách cài vùng của camera giám sát thật.
3. **Lưu đồ 5 bước** *(Show: Hình 2)*: đọc ảnh → phát hiện → nạp vùng → tính các đại lượng → so ngưỡng ra C1–C4.
4. **Luật từng tiêu chí** *(Show: công thức R và V, O)*:
    - C1: tính tỉ lệ lối đi bị chiếm R. Chỉ lấy **phần đáy 25%** của khung vật, coi như chân vật chạm sàn. **R ≥ 5% là vi phạm.** Phép hợp để chỗ chồng nhau không bị tính 2 lần.
    - C2: đếm đồ cá nhân có **tâm khung** nằm trong vùng bàn. **≥ 3 là vi phạm.**
    - C3: trong vùng đặt bình, tính phần bình **nhìn thấy V** và phần bị **che O**. **Không thấy bình, hoặc V < 0,5, hoặc O ≥ 1/3 là vi phạm.**
    - C4: có **≥ 1** đồ ăn uống là vi phạm.
5. **Ví dụ tính tay** *(Show: 3 gạch đầu dòng ví dụ lưới 10×10)*: giải thích 1 ví dụ (xem 2.2).
6. **Mô hình bình chữa cháy** *(Show: IV.A đoạn "Dữ liệu huấn luyện")*: Fire-ART, 358 ảnh, YOLO11n, GPU laptop MX350, **mAP@0,5 = 0,80**, precision 0,88, recall 0,67.
7. **Dữ liệu thử nghiệm** *(Show: IV.A đoạn "Dữ liệu thử nghiệm")*: 62 ảnh, phòng điện tử, 3 vị trí × nhiều độ cao = 6 góc, có ảnh bẫy, không có người. Số ca vi phạm C1–C4: 32, 11, 32, 26.
8. Chuyển lời: *"Dũng sẽ trình bày hướng thứ hai là Gemini, cách đánh giá và kết quả."*

## 2.2 Kiến thức cần nắm kỹ

**Thuật toán chấm một ảnh (mã giả, nắm chắc nhất):**

```
Đầu vào : ảnh I, vùng của góc camera {A: lối đi, B: mặt bàn, Z: chỗ đặt bình}
Đầu ra  : C1, C2, C3, C4 ∈ {0 = Đạt, 1 = Vi phạm} + ảnh bằng chứng

1. D ← YOLO_COCO(I) ∪ YOLO_bình(I) ∪ YOLO_World(I, "cardboard box")
       (mỗi phần tử: tên lớp, độ tin cậy ≥ 0,30, khung chữ nhật)

2. C1 – Lối đi:
       với mỗi vật cản d ∈ D (ghế, balo, túi, vali, thùng):
           đáy(d) ← 25% phía dưới khung d
       R ← diện tích( hợp các đáy(d) ∩ A ) / diện tích(A)
       C1 ← 1 nếu R ≥ 0,05, ngược lại 0

3. C2 – Đồ cá nhân:
       n ← số vật d ∈ D thuộc {điện thoại, laptop, balo, túi, sách}
            có tâm khung nằm trong B
       C2 ← 1 nếu n ≥ 3, ngược lại 0

4. C3 – Bình chữa cháy:
       E ← hợp các khung bình chữa cháy giao với Z
       Q ← hợp các khung vật có thể che (balo, túi, ghế, thùng…)
       V ← diện tích(E ∩ Z) / diện tích(Z)      (phần bình nhìn thấy)
       O ← diện tích(Q ∩ Z) / diện tích(Z)      (phần bị che)
       C3 ← 1 nếu (không có bình) hoặc V < 0,5 hoặc O ≥ 1/3, ngược lại 0

5. C4 – Đồ ăn uống:
       C4 ← 1 nếu có ít nhất 1 vật thuộc {cốc, chai, ly, bát, trái cây, bánh…}, ngược lại 0

6. Vẽ vùng + khung + kết luận lên ảnh → ảnh bằng chứng
```

Ý chính để nói: **YOLO chỉ trả lời "có gì, ở đâu"; bộ luật dùng phép giao/hợp đa giác giữa khung đồ vật và vùng để trả lời "có vi phạm không"**. Phần hình học dùng thư viện Shapely.

**YOLO cơ bản:**
- Đầu vào: ảnh. Đầu ra: danh sách `(tên lớp, độ tin cậy, khung x1 y1 x2 y2)`.
- Nhóm dùng **ngưỡng tin cậy 0,30**: vật nào máy chắc < 30% thì bỏ.
- **YOLO11s**: bản "small", chính xác hơn, dùng cho COCO. **YOLO11n**: bản "nano", nhẹ nhất, hợp GPU 2 GB, dùng để huấn luyện bình.
- **YOLO-World**: YOLO "từ vựng mở", kết hợp với mô hình hiểu chữ (CLIP) nên tìm được vật theo tên gõ vào, không cần huấn luyện lại.

**Huấn luyện mô hình bình chữa cháy:**

| Thông số | Giá trị | Nghĩa |
|---|---|---|
| Dữ liệu | Fire-ART, giấy phép CC BY 4.0 | Bộ ảnh công khai về thiết bị phòng cháy, 15 lớp. Nhóm chỉ giữ lớp bình chữa cháy |
| Số ảnh | 179 có bình (207 bình) + 179 ảnh âm (không có bình) | Ảnh âm giúp mô hình bớt báo nhầm |
| Chia | 287 huấn luyện / 71 kiểm định | Kiểm định = ảnh mô hình chưa thấy, để chấm điểm |
| Nhãn | Đa giác → khung chữ nhật | YOLO cần khung chữ nhật |
| Khởi tạo | Trọng số COCO | Học chuyển giao, đỡ tốn dữ liệu |
| Ảnh, batch | 640 px, batch 8 | Batch nhỏ vì GPU chỉ 2 GB |
| Dừng sớm | Sau 10 epoch không tiến bộ | Dừng ở epoch 46, tốt nhất epoch 36 |
| Kết quả | mAP@0,5 = 0,797 · mAP@0,5:0,95 = 0,514 · P = 0,876 · R = 0,672 | Xem giải thích bên dưới |

- **Epoch**: một lượt học hết toàn bộ ảnh huấn luyện.
- **IoU**: độ trùng giữa khung máy vẽ và khung đúng, từ 0 đến 1.
- **Precision (P)**: trong các bình máy báo, bao nhiêu % là bình thật (0,88: ít báo nhầm).
- **Recall (R)**: trong các bình thật, máy tìm được bao nhiêu % (0,67: còn sót khoảng 1/3).
- **mAP@0,5**: điểm tổng hợp của P và R, tính khung đúng khi IoU ≥ 0,5. **0,80 là khá tốt.**
- **mAP@0,5:0,95**: giống trên nhưng đòi khung khít hơn (IoU 0,5 đến 0,95). Luôn thấp hơn.

**Bằng chứng mô hình tự huấn luyện có ích:** trên ảnh phòng thật, YOLO COCO và YOLO-World đều **không** tìm thấy bình, mô hình của nhóm tìm thấy với độ tin cậy **0,94** (`outputs/fig_detector_compare.png`). Trong kết quả cuối, C3 đạt **κ = 0,90**, cao nhất của luật.

**Ví dụ tính tay C1** (trong bài, dùng cả khung và ngưỡng 15% để dễ minh hoạ):
- Lối đi 5 × 10 = 50 ô. Vật chiếm 3 × 3 = 9 ô nằm trọn trong lối đi → R = 9/50 = **18% ≥ 15% → vi phạm**.
- Vật nhỏ 2 × 2 = 4 ô → R = 4/50 = **8% → đạt**.
- Vật 16 ô nhưng chỉ 8 ô nằm trong lối đi → R = 8/50 = **16% → vi phạm**. Phần ngoài lối đi không tính.
- Cả 3 ví dụ là **bộ kiểm thử tự động** (`src/test_rules.py`), chạy đều đạt.

**Vì sao ngưỡng 5%?** Chọn **trước khi thu thập dữ liệu**, tương ứng 1 vật cỡ balo trên lối đi điển hình. Không chỉnh theo kết quả, để tránh "học tủ".

**Các file liên quan** (nếu thầy hỏi code ở đâu):
`src/rules.py` (bộ luật) · `src/run_rules.py` (chạy cả hệ thống) · `src/train_extinguisher.py` (huấn luyện) · `src/prep_fireart.py` (chuẩn bị dữ liệu) · `tools/zone_tool.html` (vẽ vùng) · `data/zones.json` (vùng đã vẽ).

## 2.3 Câu hỏi có thể gặp

**Sao không dùng phân đoạn ảnh (segmentation) để tự tìm lối đi?**
Camera giám sát đứng yên nên vẽ vùng 1 lần là dùng mãi, đơn giản và chính xác. Segmentation là hướng phát triển khi camera di chuyển hoặc cần tự động hoàn toàn.

**Sao lấy phần đáy 25% của khung?**
Khung bao cả chiều cao vật. Cái ghế cao che lên lối đi trong ảnh nhưng chỉ chân ghế mới thật sự chạm sàn. Lấy phần đáy để gần với diện tích chiếm sàn thật.

**Recall 0,67 thấp, có ảnh hưởng không?**
Trên bộ kiểm định Fire-ART (ảnh đa dạng) thì sót 1/3. Trên ảnh phòng của nhóm (bình to, rõ) thì C3 vẫn đạt κ = 0,90. Nếu không thấy bình, luật coi là vi phạm (nghiêng về an toàn).

**Luật có nhược điểm gì?**
Tính trên ảnh 2D, chưa tính phối cảnh xa gần; khung chữ nhật to hơn vật thật; chỉ biết các lớp mà YOLO biết (không biết áo khoác). Dũng sẽ nói rõ ở phần lỗi.

**Tốc độ?**
Khoảng 0,13 giây/ảnh trên GPU laptop, chạy offline, không cần mạng.

---

# PHẦN 3. DŨNG — ③ Thuật toán (b): Gemini + cách đánh giá, ④ Kết quả

**Mục bài báo:** III.D (VLM), III.E (Người chấm), IV.B–F (Kết quả).

## 3.1 Nói gì (khoảng 5 phút)

### ③ Thuật toán (b): Gemini và cách đánh giá (khoảng 1,5 phút)

Quy trình hướng thứ hai, nói ngắn theo 3 bước: **ảnh → gửi Gemini kèm prompt → nhận JSON {C1..C4, lý do}**. Cách đánh giá: **lấy nhãn đa số của 3 người làm đáp án → so từng tiêu chí bằng κ**.

1. **Cách dùng Gemini** *(Show: III.D)*: gửi ảnh (thu nhỏ cạnh dài 1568 px) + prompt tiếng Anh mô tả 4 tiêu chí, model **gemini-3.5-flash**, **nhiệt độ 0** (trả lời ổn định nhất), bắt trả về **JSON**. **Không huấn luyện, không cho ví dụ** (zero-shot). 3 prompt: **P1 chi tiết**, **P2 rút gọn**, **P3 như P1 nhưng đảo thứ tự tiêu chí**.
2. **Người chấm** *(Show: III.E)*: 3 người không tham gia dàn dựng, chấm độc lập, có hướng dẫn và ảnh tham khảo vị trí bình. Phiếu Excel chỉ nhập được 0/1, **thứ tự ảnh xáo trộn khác nhau** cho mỗi người. Đáp án = **nhãn đa số**; độ khớp đo bằng **κ** (giải thích ở 0.6).

### ④ Hướng giải quyết: giải quyết được đến đâu (khoảng 3,5 phút)

3. **Người có đồng ý với nhau?** *(Show: Bảng II)*: rất cao, Fleiss κ 0,89 / 0,69 / 0,98 / 0,96. C2 thấp nhất vì khó xác định "có phải đồ cá nhân không". → Đáp án đa số đáng tin.
4. **Kết quả chính** *(Show: Bảng III, rồi Hình 3)*: đọc bảng 0.2. Chỉ vào biểu đồ: **cột xanh (luật) cao hơn ở C1, C3; cột cam (Gemini) cao hơn ở C2, C4**; điểm đen là mức người đồng ý với nhau.
5. **Giải thích vì sao:**
    - Luật có **vùng vẽ sẵn** nên biết chính xác lối đi, chỗ bình → thắng C1, C3.
    - Gemini **nhận ra được đồ vật** ngoài 80 lớp COCO (áo khoác, ví), phân biệt chai nước với vật giống chai → thắng C2, C4.
6. **Đổi prompt** *(Show: Bảng IV)*: C3, C4 gần như không đổi; C1, C2 đổi đáng kể. P2 rút gọn tệ nhất ở C2 vì đếm cả chai nước, gói bánh là đồ cá nhân. → **Định nghĩa rõ trong prompt quan trọng hơn thứ tự.**
7. **Ca lỗi** *(Show: Hình 4)*: (a) YOLO COCO nhận **chính bình chữa cháy thành "chai"** → báo nhầm có đồ uống; (b) **áo khoác trùm bình** không được tính là vật che. Gemini thì quá khắt khe ở lối đi và hay nói "không thấy bình nên đạt".
8. **Tốc độ:** luật 0,13 s/ảnh offline; Gemini khoảng 10 s/ảnh, cần mạng, miễn phí chỉ khoảng 20 ảnh/ngày/tài khoản.
9. Chuyển lời: *"Kiệt sẽ tổng kết và nói hướng đi tiếp."*

## 3.2 Kiến thức cần nắm kỹ

**Bảng III đầy đủ** (thuộc các ý chính, không cần thuộc hết):

| | Tiêu chí | Khớp | κ [CI 95%] | F1 | FP/FN |
|---|---|---|---|---|---|
| Luật | C1 | 87% | **0,74** [0,56; 0,90] | 0,88 | 6/2 |
| | C2 | 90% | 0,58 [0,22; 0,85] | 0,62 | 0/6 |
| | C3 | 95% | **0,90** [0,77; 1,00] | 0,95 | 2/1 |
| | C4 | 89% | 0,78 [0,61; 0,90] | 0,88 | 7/0 |
| Gemini P1 | C1 | 73% | 0,44 [0,25; 0,65] | 0,78 | 16/1 |
| | C2 | 97% | **0,88** [0,68; 1,00] | 0,90 | 0/2 |
| | C3 | 89% | 0,78 [0,61; 0,90] | 0,88 | 0/7 |
| | C4 | 98% | **0,97** [0,90; 1,00] | 0,98 | 1/0 |

Đọc FP/FN để thấy "tính cách" của mỗi máy:
- Luật ở C2: **0 báo nhầm, 6 bỏ sót** → không nhận ra áo, ví nên đếm thiếu.
- Luật ở C4: **7 báo nhầm, 0 bỏ sót** → thấy "chai" ở khắp nơi (do nhầm bình thành chai).
- Gemini ở C1: **16 báo nhầm** → quá khắt khe vì không biết lối đi ở đâu.
- Gemini ở C3: **7 bỏ sót** → không biết bình phải ở đâu, không thấy bình thì cho là đạt.

**F1**: điểm 0–1 cân bằng giữa "báo đúng" (precision) và "không bỏ sót" (recall) cho các ca vi phạm.

**Bảng IV (33 ảnh chung):**

| Tiêu chí | 3 prompt cùng kết luận | Fleiss κ giữa prompt | Khớp người |
|---|---|---|---|
| C1 | 70% | 0,49 | 64–82% |
| C2 | 76% | 0,46 | 73–97% |
| C3 | 97% | 0,96 | 88–91% |
| C4 | 100% | 1,00 | 100% |

**Ca lỗi, có số liệu:**
- **Bình → chai:** 6/7 ca báo nhầm C4 của luật. Khung "bottle" trùng khung bình (IoU 0,50–0,95). Mô hình có sẵn không có lớp bình chữa cháy nên gán vào lớp giống hình dạng nhất. **Đây cũng là lý do phải tự huấn luyện mô hình bình.**
- **Áo khoác:** COCO không có lớp này → áo trùm bình không tính là che (C3), áo trên bàn không đếm (6 ca bỏ sót C2), ghế có áo vắt lên bị nhận là "người" và bị bỏ qua (C1).
- **Gemini C1:** coi ghế, balo cạnh bàn, loa sát tường là vật cản, trong khi người chấm thấy chúng không nằm trên lối đi.
- **Gemini C3:** 4/7 ca bỏ sót có lý do "không thấy bình chữa cháy nên không vi phạm", trong khi không thấy bình ở chỗ quy định chính là vi phạm.

**Chuyện model Gemini và hạn mức:**
- Ban đầu định dùng gemini-2.5-flash; tài khoản mới không dùng được, bản 3.8 hay quá tải, nên **chốt gemini-3.5-flash cho toàn bộ**, chạy 8–9/10/2026.
- Miễn phí khoảng 20 lần/ngày/tài khoản → dùng 4 key, chạy 2 ngày. **P1 đủ 62 ảnh; P2, P3 chỉ 33 ảnh.** Đã ghi rõ trong bài.

**Các file liên quan:** `src/run_vlm.py` (gọi Gemini) · `outputs/results_vlm.csv` (kết quả + lý do Gemini) · `src/evaluate.py` (tính κ, CI, vẽ biểu đồ) · `data/labels/` (phiếu người chấm) · `outputs/errors.csv` (các ca sai).

## 3.3 Câu hỏi có thể gặp

**Sao không đưa Gemini thông tin vùng cho công bằng?**
Câu hỏi nghiên cứu là so sánh hai hướng **như cách người ta thường dùng**: VLM thì chỉ cần ảnh + mô tả, không cấu hình gì. Đưa vùng cho Gemini là một hướng cải tiến hay, có thể làm tiếp.

**Khoảng tin cậy chồng nhau, vậy chênh lệch có ý nghĩa không?**
Với 62 ảnh, nhiều chỗ còn chồng lấn nên bài viết dè dặt: cần dữ liệu lớn hơn để khẳng định. Chênh lệch rõ nhất ở **C1** (luật 0,74 so với 0,44) và **C4** (Gemini 0,97 so với 0,78).

**P2/P3 chỉ 33 ảnh có làm sai kết luận không?**
Phần so sánh chính (RQ1, RQ2) dùng **P1 đủ 62 ảnh**. Phần độ ổn định (RQ3) so 3 prompt trên **cùng 33 ảnh** nên vẫn công bằng giữa các prompt. Đã ghi vào hạn chế.

**Biết luật nhầm bình thành chai, sao không sửa luôn?**
Sửa luật sau khi nhìn kết quả trên chính bộ ảnh thử nghiệm là "học tủ", số liệu sẽ đẹp giả tạo. Đúng quy trình là ghi nhận lỗi, đề xuất cách sửa (bỏ khung "chai" trùng khung bình), rồi thử trên bộ ảnh mới.

**Nhiệt độ 0 là gì?**
Tham số độ "ngẫu nhiên" khi AI trả lời. 0 = luôn chọn câu trả lời chắc nhất, kết quả lặp lại được.

**Người chấm là ai, có thiên vị không?**
3 người ngoài nhóm, không dàn dựng ảnh, không biết kịch bản, chấm độc lập, thứ tự ảnh xáo trộn. Người đồng ý với nhau rất cao (κ 0,69–0,98).

---

# PHẦN 4. HƯỚNG PHÁT TRIỂN TIẾP THEO (cả nhóm nắm, Kiệt trình bày)

## 4.1 Tóm tắt 30 giây (Kiệt nói ở cuối phần kết luận)

> "Nếu có thêm thời gian, nhóm dự định làm 4 việc để bài báo tốt hơn. **Thứ nhất**, chạy đủ 3 prompt trên toàn bộ 62 ảnh. **Thứ hai**, thu thêm ảnh ở 2–3 phòng khác, nhất là ảnh vi phạm tiêu chí đồ cá nhân, để kết luận chắc chắn hơn. **Thứ ba**, xây dựng hệ thống lai: dùng luật cho lối đi và bình chữa cháy, dùng Gemini cho đồ cá nhân và đồ ăn uống, rồi đánh giá trên dữ liệu mới. **Thứ tư**, sửa hai lỗi đã phát hiện, là nhận nhầm bình chữa cháy thành chai và không nhận ra áo khoác, rồi kiểm tra lại."

Mỗi việc lấp một điểm yếu của bài hiện tại:

| Ưu tiên | Điểm yếu hiện tại | Việc làm | Bài tốt hơn ở chỗ |
|---|---|---|---|
| 1 | P2, P3 mới chạy 33/62 ảnh | Chạy đủ 3 prompt trên 62 ảnh | Dễ nhất; RQ3 đầy đủ |
| 2 | 1 phòng, 62 ảnh, C2 chỉ 11 ca vi phạm | Thêm 2–3 phòng, thêm ảnh vi phạm C2 | Khoảng tin cậy hẹp lại, nói được hệ thống chạy ở phòng khác |
| 3 | Mới gợi ý kết hợp, chưa thử | Làm hệ thống lai, đo trên ảnh mới | Gợi ý thành kết quả thật; đóng góp mạnh nhất |
| 4 | Biết lỗi bình → chai, áo khoác nhưng chưa sửa | Sửa 2 lỗi, đo lại trên ảnh mới | Chứng minh phân tích lỗi có ích |

Dashboard, video, nhật ký sự kiện (hướng 5 bên dưới) là việc làm **sản phẩm** cho môn Thị giác máy tính, **không** nói như việc để bài báo tốt hơn.

## 4.2 Chi tiết từng hướng

### Hướng 1. Sửa lỗi đã phát hiện (ngắn hạn, làm ngay được)

| Lỗi | Cách sửa dự kiến |
|---|---|
| YOLO COCO nhận **bình chữa cháy thành "chai"** (6/7 ca báo nhầm C4) | Bỏ các khung "bottle" trùng nhiều với khung bình chữa cháy do mô hình tự huấn luyện tìm ra |
| **Áo khoác** không có trong COCO (bỏ sót C1, C2, C3) | Bổ sung lớp áo khoác: dùng YOLO-World gõ "jacket", hoặc gán nhãn thêm ảnh để huấn luyện |
| Ghế có áo vắt lên bị nhận là **"người"** | Chỉ bỏ qua "người" khi khung đủ lớn và có dáng đứng; còn lại coi là vật cản |
| Gemini **không biết lối đi** ở đâu (16 ca báo nhầm C1) | Vẽ vùng lên ảnh trước khi gửi, hoặc mô tả vùng trong prompt |
| Gemini **không biết vị trí bình** (bỏ sót C3) | Gửi kèm ảnh mẫu vị trí bình, nói rõ "không thấy bình ở vị trí này là vi phạm" |

**Quan trọng:** các cách sửa phải được thử trên **bộ ảnh mới**, không chỉnh rồi đo lại trên chính 62 ảnh cũ (tránh "học tủ").

### Hướng 2. Hệ thống lai (đóng góp chính của bước tiếp theo)

- Dùng **luật cho C1, C3** (cần biết vị trí) và **Gemini cho C2, C4** (cần nhận ra đồ vật).
- Nếu chỉ lấy con số hiện có, hệ thống lai sẽ đạt κ khoảng 0,74 / 0,88 / 0,90 / 0,97. Nhưng con số này là **chọn sau khi xem kết quả**, nên cần kiểm chứng lại trên dữ liệu mới.
- Thử thêm cách khác: luật chạy trước (nhanh, offline), chỉ gửi Gemini **những ảnh luật nghi ngờ** → tiết kiệm lượt API.

### Hướng 3. Mở rộng dữ liệu và đánh giá

- **Nhiều phòng hơn:** ít nhất 2–3 phòng thí nghiệm khác, để xem hệ thống có chạy được ở phòng chưa thấy bao giờ không.
- **Ảnh từ camera giám sát thật** thay vì ảnh dàn dựng chụp bằng điện thoại.
- **Thêm ca vi phạm C2** (hiện chỉ 11/62) để khoảng tin cậy hẹp lại.
- **Chạy đủ P2, P3 trên toàn bộ ảnh** (hiện chỉ 33 ảnh do hết lượt miễn phí).
- **Thêm người chấm** hoặc cho chấm lại sau một thời gian, để đo độ ổn định của chính người chấm.
- Thử **thêm VLM khác** (GPT, Claude, hoặc mô hình mã nguồn mở chạy trên máy như Qwen-VL) để xem kết quả có phụ thuộc vào Gemini không.

### Hướng 4. Cải tiến phương pháp

- **Bổ sung 2 tiêu chí** đã bỏ: hoá chất để ngoài tủ, dây điện cắt ngang lối đi.
- **Phân đoạn ảnh (segmentation)** để máy tự tìm lối đi, mặt bàn, khỏi phải vẽ tay.
- **Hiệu chỉnh phối cảnh:** quy diện tích trên ảnh về diện tích sàn thật, vật ở xa không bị tính nhỏ hơn thực tế.
- **Tối ưu ngưỡng** (5%, 1/3, ≥ 3 vật) trên một bộ dữ liệu riêng, rồi kiểm tra trên bộ khác.

### Hướng 5. Thành sản phẩm (gắn với môn Thị giác máy tính)

- **Dashboard:** tải ảnh lên, xem kết quả 4 tiêu chí và ảnh bằng chứng.
- **Chạy trên video / camera:** lấy khung hình định kỳ, chỉ báo khi vi phạm kéo dài nhiều khung liên tiếp.
- **Nhật ký sự kiện:** mỗi vi phạm ghi lại thời gian, góc camera, tiêu chí, ảnh đã làm mờ người.
- **Bảng kiểm cấu hình được:** chỉnh tiêu chí, ngưỡng mà không cần sửa code.

## 4.3 Lộ trình dự kiến

| Giai đoạn | Việc chính | Kết quả mong đợi |
|---|---|---|
| 1–2 tuần tới | Sửa lỗi (hướng 1), chạy đủ P2/P3, viết thử hệ thống lai | Có phiên bản hệ thống mới |
| Tiếp theo | Thu thêm ảnh ở 2–3 phòng khác, mời người chấm, đánh giá lại trên dữ liệu mới | Kiểm chứng hệ thống lai trên dữ liệu chưa thấy |
| Cuối kỳ | Dashboard, xử lý video, nhật ký sự kiện | Demo hoàn chỉnh cho môn Thị giác máy tính |

*(Thời gian là gợi ý, nhóm chỉnh theo lịch thật trước khi nói.)*

## 4.4 Câu hỏi có thể gặp

**Hướng nào quan trọng nhất?**
Hệ thống lai và kiểm chứng trên dữ liệu mới. Đây là câu trả lời trực tiếp cho kết luận của bài: hai cách bù trừ nhau thì kết hợp có tốt hơn thật không.

**Sao không làm luôn hệ thống lai trong bài này?**
Vì muốn đánh giá công bằng thì phải thử trên dữ liệu khác với dữ liệu dùng để chọn cách kết hợp. Hiện chỉ có 62 ảnh nên chưa tách ra được.

**Có dùng được ngoài phòng thí nghiệm không?**
Có thể, với văn phòng, nhà xưởng, kho: chỉ cần đổi bảng tiêu chí, danh sách đồ vật và vẽ lại vùng. Bộ luật không gian dùng lại được.

---

# Checklist trước giờ báo cáo

- [ ] Cả nhóm đọc Phần 0, tự nói được đề tài trong 30 giây và bảng kết quả chính
- [ ] Mỗi người tập nói phần mình 1–2 lần, bấm giờ
- [ ] PDF bài báo mở sẵn trên Overleaf (đã biên dịch XeLaTeX, không lỗi), phóng to 125–150%
- [ ] Mở sẵn 2 ảnh `outputs/annotated/v1_05.jpg` và `v3a_08.jpg`
- [ ] Thống nhất ai cầm máy cuộn bài báo
- [ ] Kiểm tra tên, email 3 người trên trang 1 bài báo
- [ ] Mang theo / mở sẵn file này để tra nhanh khi bị hỏi
