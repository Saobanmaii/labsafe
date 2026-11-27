# Brief làm slide — Báo cáo đề tài NCKH (thuyết trình 07/10/2026)

> **Cách dùng:** sang tài khoản Claude khác, đính kèm file này (cùng các file ở mục "Tài liệu đính kèm" nếu có), rồi dán đoạn PROMPT bên dưới vào khung chat.

---

## PROMPT (copy nguyên đoạn này)

```
Hãy làm cho tôi một bộ slide thuyết trình bằng tiếng Việt, 16:9, 12 trang, cho buổi "báo cáo đề tài" môn Phương pháp nghiên cứu khoa học (người nghe: giảng viên và các bạn cùng lớp, thời lượng khoảng 10 phút).

Toàn bộ nội dung từng trang, phần lời nói (speaker notes), bảng màu và font nằm trong file SLIDES_BRIEF.md đính kèm. Hãy làm đúng theo nội dung đó:
- Giữ nguyên số liệu và trích dẫn [1]–[13]. KHÔNG tự bịa thêm số liệu.
- Các ô [__] là số liệu chưa có (sẽ điền sau ngày 06/10): giữ nguyên dạng [__], đừng tự điền.
- Mỗi trang một ý chính, ít chữ; ưu tiên thẻ (card), bảng, số lớn thay cho gạch đầu dòng dài.
- Đặt phần "Lời nói" của mỗi trang vào speaker notes.
- Font: Lora (tiêu đề) + Be Vietnam Pro (nội dung), cả hai đều hỗ trợ đầy đủ dấu tiếng Việt.
- Bảng màu: xanh đậm #14213D, nền sáng #F7F6F2, cam nhấn #E08A3C (chữ cam trên nền sáng dùng #B8560F), chữ phụ #4A5568. Trang bìa, trang 4 và trang cuối dùng nền xanh đậm; các trang còn lại nền sáng.
- Đánh số trang ở góc dưới trái.
Làm xong cho tôi tải về dạng PowerPoint (.pptx).
```

---

## Thông tin chung

- **Đề tài:** Chấm điểm an toàn phòng thí nghiệm từ ảnh: so sánh hệ thống dựa trên luật và mô hình ngôn ngữ–thị giác với đánh giá của con người
- **Nhóm:** Trần Tuấn Kiệt (B23DCPT176) · Lành Diệu Hương · Lê Quốc Dũng
- **Trường:** Học viện Công nghệ Bưu chính Viễn thông
- **Ngày:** 07/10/2026
- **Ý tưởng chính:** cùng một bộ ảnh phòng thí nghiệm được chấm độc lập bởi 3 nguồn: (1) người chấm, dùng làm đáp án chuẩn; (2) hệ thống YOLO do nhóm tự huấn luyện + bộ luật không gian; (3) VLM Gemini không huấn luyện. Sau đó so sánh từng tiêu chí bằng hệ số kappa.

---

## Nội dung từng trang

### Trang 1 — Bìa (nền xanh đậm)
- Dòng nhỏ: BÁO CÁO ĐỀ TÀI · PHƯƠNG PHÁP NGHIÊN CỨU KHOA HỌC
- Tiêu đề: **Chấm điểm an toàn phòng thí nghiệm từ ảnh**
- Phụ đề: So sánh hệ thống dựa trên luật và mô hình ngôn ngữ–thị giác với đánh giá của con người
- Nhóm, trường, ngày (như trên)
- *Lời nói:* Chào thầy và các bạn. Nhóm em xin trình bày đề tài chấm điểm an toàn phòng thí nghiệm từ ảnh, so sánh hai cách chấm tự động với đánh giá của con người. Đây là báo cáo đề tài kèm kết quả sơ bộ.

### Trang 2 — Đặt vấn đề
- Tiêu đề: **Kiểm tra an toàn phòng thí nghiệm vẫn làm bằng tay**
- 3 thẻ:
  - **Tốn nhân lực:** cán bộ đi từng phòng đối chiếu bảng kiểm, không thể làm thường xuyên.
  - **Thiếu nhất quán:** kết quả phụ thuộc người đánh giá và từng lần kiểm tra.
  - **Không lưu bằng chứng:** không theo dõi được mức độ cải thiện theo thời gian.
- Câu nhấn: Camera giám sát đã có sẵn. **Ảnh có thể tự động hoá một phần việc chấm điểm không, và tin cậy đến đâu?**
- *Lời nói:* Hiện nay việc kiểm tra an toàn phòng thí nghiệm chủ yếu là thủ công, có ba hạn chế: tốn người, không nhất quán, không lưu bằng chứng. Camera đã có sẵn, nên câu hỏi là có tận dụng ảnh để chấm tự động được không, và tin cậy đến đâu.

### Trang 3 — Tổng quan tài liệu
- Tiêu đề: **Nghiên cứu tập trung vào con người, chưa vào căn phòng**
- Cột trái **"Đã nhiều: phát hiện đồ bảo hộ"**:
  - YOLOv5/v7 tại phòng thí nghiệm giáo dục, mAP 77,4% [1]
  - YOLOv4–v6 phòng thực hành chế tạo, mAP 0,757 [2]
  - YOLOv7 cải tiến cho đồ bảo hộ phòng thí nghiệm [3]
- Cột phải **"Hướng mới: VLM chấm trực tiếp"**:
  - **37–58%** phán đoán an toàn sai dù nhận đúng hành động [12]
  - **85–100%** dự đoán dồn vào một lớp [9]
  - **32 điểm %** chênh lệch chỉ do đổi cách viết prompt [9]
- Câu nhấn: **Khoảng trống:** chưa có nghiên cứu so sánh hệ thống luật, VLM và người chấm trên điều kiện gọn gàng – vệ sinh – an toàn ở mức toàn cảnh.
- *Lời nói:* Các nghiên cứu hiện có chủ yếu phát hiện đồ bảo hộ trên người. Hướng mới là dùng VLM chấm trực tiếp, nhưng các bộ chuẩn gần đây cho thấy nó còn sai nhiều và nhạy với cách viết prompt. Chưa ai so sánh hai hướng này với người chấm cho bài toán toàn cảnh căn phòng.

### Trang 4 — Câu hỏi nghiên cứu (nền xanh đậm)
- Tiêu đề: **Ba câu hỏi nhóm cần trả lời**
- 01 · Máy chấm khớp với người chấm đến đâu, **xét riêng từng tiêu chí**?
- 02 · Hệ thống luật hay VLM gần với người hơn, và **với tiêu chí nào**?
- 03 · VLM có **ổn định** khi đổi cách diễn đạt prompt không?
- *Lời nói:* Nghiên cứu trả lời ba câu hỏi: máy khớp với người đến đâu theo từng tiêu chí; giữa luật và VLM cách nào tốt hơn với tiêu chí nào; và VLM có ổn định khi đổi cách hỏi không.

### Trang 5 — Thiết kế nghiên cứu (sơ đồ)
- Tiêu đề: **Cùng một bộ ảnh, ba nguồn chấm độc lập**
- Sơ đồ: [36 ảnh tự chụp] → 3 nhánh → [So sánh từng tiêu chí bằng hệ số κ]
  1. **Người chấm — đáp án chuẩn:** 2–3 người chấm độc lập, lấy nhãn đa số
  2. **YOLO nhóm tự huấn luyện + bộ luật:** phát hiện đối tượng, áp luật quan hệ không gian theo vùng
  3. **VLM (Gemini) — không huấn luyện:** đưa ảnh và bảng tiêu chí, yêu cầu chấm, 3 cách viết prompt
- *Lời nói:* Thiết kế ba cột: cùng một bộ ảnh được chấm độc lập bởi ba nguồn. Người chấm là đáp án chuẩn; cột hai là hệ thống nhóm tự xây dựng; cột ba là Gemini không huấn luyện. Sau đó so sánh từng tiêu chí bằng hệ số kappa.

### Trang 6 — Bảng tiêu chí
- Tiêu đề: **Bốn tiêu chí, chấm Đạt hoặc Vi phạm**
- Bảng 3 cột:

| Tiêu chí | Vi phạm khi | Luật máy |
|---|---|---|
| C1 · Lối đi | Có vật cỡ từ balo trở lên trên sàn lối đi | Tỷ lệ chiếm dụng R ≥ 5% |
| C2 · Đồ cá nhân | Từ 3 vật dụng cá nhân trên bàn thí nghiệm | Đếm vật có tâm trong vùng bàn ≥ 3 |
| C3 · Bình chữa cháy | Bị che từ 1/3, khó tiếp cận hoặc không còn ở vị trí | Không thấy bình, nhìn thấy < 50% hoặc bị che ≥ 1/3 |
| C4 · Đồ ăn uống | Có bất kỳ đồ ăn, đồ uống (không tính dụng cụ thí nghiệm) | Có ít nhất 1 đối tượng đồ ăn uống |

- Ghi chú nhỏ: Thu hẹp từ 6 tiêu chí, thang 3 mức trong đề cương: bỏ "hóa chất ngoài tủ" và "dây điện" (khó phát hiện từ ảnh), chuyển sang nhị phân để giảm tính chủ quan.
- *Lời nói:* So với đề cương, nhóm thu hẹp từ sáu tiêu chí ba mức xuống bốn tiêu chí đạt hoặc vi phạm, để người chấm ít chủ quan hơn và bỏ hai tiêu chí khó phát hiện từ ảnh.

### Trang 7 — Thuật toán nền (có hình lưới)
- Tiêu đề: **Thuật toán nền: tỷ lệ chiếm dụng lối đi**
- Công thức lớn: **R = |(∪ đáy hộp vật cản) ∩ A| / |A|**
- Ví dụ tính tay:
  - Lưới 10×10, lối đi A từ ô (3,1) đến (7,10): **50 ô**
  - Vật cản ô (4,2)–(6,4): **9 ô**, nằm trọn trong lối đi
  - **R = 9 / 50 = 18% ≥ 15% → Vi phạm**
- Ghi chú: Phép hợp ∪ để vật chồng nhau không bị tính hai lần. Cả 3 ví dụ trong đề cương đều nằm trong bộ kiểm thử tự động.
- **Hình minh hoạ:** lưới 10×10 ô; cột 3–7 tô xanh nhạt (lối đi A, viền xanh #1F6F78); khối 3×3 ô ở cột 4–6, hàng 2–4 tô cam (vật cản). Chú thích: "Xanh: lối đi A · Cam: vật cản".
- *Lời nói:* Thuật toán nền là tỷ lệ chiếm dụng lối đi: phần đáy hộp bao vật cản giao với vùng lối đi, chia cho diện tích lối đi. Ví dụ: lối đi 50 ô, vật cản 9 ô, R bằng 18%, vượt ngưỡng 15% nên vi phạm. Hệ thống thật dùng ngưỡng 5%, chọn trước khi thu dữ liệu.

### Trang 8 — Ba bộ phát hiện
- Tiêu đề: **Tự huấn luyện phần COCO không có: bình chữa cháy**
- 3 thẻ (thẻ giữa viền cam, nổi bật):
  - **YOLO11 – COCO:** có sẵn: ghế, balo, túi, cốc, chai, đồ ăn, điện thoại, laptop, sách
  - **YOLO11n tự huấn luyện:** bình chữa cháy, trên bộ Fire-ART (ISPRS 2025, CC BY 4.0)
  - **YOLO-World:** từ vựng mở, không huấn luyện: thùng carton
- 3 số lớn: **179** ảnh có bình (207 đối tượng) · **287 / 71** ảnh huấn luyện / kiểm định · **0,80** mAP@0,5 trên tập kiểm định (precision 0,88 · recall 0,67)
- *Lời nói:* YOLO COCO nhận được phần lớn đồ vật nhưng không có lớp bình chữa cháy, nên nhóm tự huấn luyện YOLO11n trên bộ dữ liệu công khai Fire-ART, đạt mAP@0,5 bằng 0,80 trên tập kiểm định.

### Trang 9 — VLM
- Tiêu đề: **Gemini 2.5 Flash, hỏi theo ba cách**
- 3 thẻ: **P1 Chi tiết:** định nghĩa đầy đủ từng tiêu chí như bảng chấm của người · **P2 Rút gọn:** mỗi tiêu chí một dòng · **P3 Đảo thứ tự:** như P1 nhưng tiêu chí theo thứ tự C4 → C1
- Câu nhấn: Không huấn luyện, không ví dụ mẫu · nhiệt độ 0 · đầu ra JSON · ảnh thu về cạnh 1568 px. Ba prompt cùng nghĩa → đo được độ ổn định (câu hỏi 3).
- *Lời nói:* Cột ba là Gemini 2.5 Flash, chọn vì ổn định nhất khi thử; các bản mới hơn thường bị quá tải. Mỗi ảnh được hỏi theo ba cách cùng nghĩa để đo xem kết quả có thay đổi theo cách hỏi không.

### Trang 10 — Dữ liệu thử nghiệm
- Tiêu đề: **4 góc camera × 9 kịch bản = 36 ảnh**
- Bảng (VP = dàn dựng vi phạm, – = không):

| Kịch bản | s01 | s02 | s03 | s04 | s05 | s06 | s07 | s08 | s09 |
|---|---|---|---|---|---|---|---|---|---|
| C1 Lối đi | – | VP | – | – | – | VP | – | VP | VP |
| C2 Đồ cá nhân | – | – | VP | – | – | VP | – | – | VP |
| C3 Bình CC | – | – | – | VP | – | – | VP | VP | VP |
| C4 Đồ ăn uống | – | – | – | – | VP | – | VP | VP | VP |

- Ghi chú: VP = dàn dựng vi phạm (khoảng 40% ảnh mỗi tiêu chí). s01 và s03 có chai hóa chất làm "bẫy" cho C4. Đáp án chuẩn là **nhãn đa số của 2–3 người chấm** không tham gia dàn dựng, chấm độc lập, thứ tự ảnh xáo trộn.
- *Lời nói:* 36 ảnh, 4 góc camera cố định, mỗi góc 9 kịch bản sao cho mỗi tiêu chí vi phạm khoảng 40%. Có tình huống bẫy là chai hóa chất. Kịch bản chỉ là ý định dàn dựng; đáp án chuẩn là nhãn đa số của người chấm.

### Trang 11 — Kết quả sơ bộ (BẢN DÙNG CHO 07/10, thay cho bảng trống bên dưới)
- Tiêu đề: **Mô hình tự huấn luyện phát hiện được thứ các mô hình có sẵn bỏ sót**
- Hình lớn: `fig_detector_compare.png` (3 ảnh cạnh nhau). Đặt nhãn trên từng ảnh: **YOLO11s – COCO: không phát hiện** · **YOLO-World: không phát hiện** · **YOLO11n nhóm tự huấn luyện: 0,94**. Chú thích nhỏ: "Ảnh: tập kiểm định Fire-ART (CC BY 4.0)".
- Hàng số liệu dưới hình: **mAP@0,5 = 0,80** · **Precision = 0,88** · **Recall = 0,67** (71 ảnh kiểm định)
- Ô trạng thái nhỏ: ✅ Hệ thống luật, Gemini và script đánh giá đã chạy thông · ⏳ Bộ 36 ảnh phòng thí nghiệm + người chấm: đang chờ mượn phòng
- *Lời nói:* Kết quả sơ bộ hiện có là mô hình phát hiện bình chữa cháy nhóm tự huấn luyện. Trên cùng một ảnh, YOLO huấn luyện sẵn trên COCO và YOLO-World đều không phát hiện được bình, còn mô hình của nhóm phát hiện đúng với độ tin cậy 0,94. Trên tập kiểm định, mô hình đạt mAP 0,80, precision 0,88, recall 0,67; recall còn thấp, nghĩa là vẫn bỏ sót khoảng một phần ba số bình, nhóm sẽ cải thiện bằng cách bổ sung dữ liệu. Toàn bộ hệ thống đã chạy thông; phần so sánh với người chấm đang chờ nhóm mượn được phòng thí nghiệm để chụp ảnh, sẽ hoàn thành trong báo cáo cuối kỳ.

### (Để dành, dùng khi có ảnh phòng thí nghiệm) Trang kết quả so sánh
- Tiêu đề: **[Câu kết luận chính — điền sau khi có số liệu]**
- Bảng:

| Tiêu chí | Người (Fleiss κ) | Luật (κ) | VLM P1 (κ) | VLM P1–P3 |
|---|---|---|---|---|
| C1 Lối đi | [__] | [__] | [__] | [__] |
| C2 Đồ cá nhân | [__] | [__] | [__] | [__] |
| C3 Bình chữa cháy | [__] | [__] | [__] | [__] |
| C4 Đồ ăn uống | [__] | [__] | [__] | [__] |

- Ghi chú: κ diễn giải theo Landis & Koch: 0,41–0,60 trung bình · 0,61–0,80 đáng kể · > 0,80 gần như hoàn hảo. Cột cuối: biên độ độ khớp giữa 3 prompt.
- Chừa chỗ cho 1 biểu đồ cột (hình `fig_kappa.png`, sẽ gửi sau).
- *Lời nói:* [Điền sau khi có kết quả ngày 06/10.]

### Trang 12 — Hạn chế và kế hoạch (nền xanh đậm)
- Tiêu đề: **Từ kết quả sơ bộ đến báo cáo cuối kỳ**
- Cột **Hạn chế:** ảnh dàn dựng, chưa phải camera giám sát thực tế · 36 ảnh, 2–3 người chấm: khoảng tin cậy của κ còn rộng · luật tính trên ảnh 2D, chưa hiệu chỉnh phối cảnh
- Cột **Đến cuối kỳ:** mở rộng bộ ảnh, thêm phòng và góc camera · bổ sung tiêu chí hóa chất ngoài tủ và dây điện · thử kết hợp luật cho tiêu chí đếm được, VLM cho tiêu chí cần ngữ cảnh
- Dòng cuối: **Nhóm em xin cảm ơn và mong nhận góp ý của thầy.**
- *Lời nói:* Hạn chế chính là ảnh dàn dựng, quy mô nhỏ và luật tính trên ảnh 2D. Đến cuối kỳ nhóm sẽ mở rộng dữ liệu, bổ sung hai tiêu chí còn lại và thử kết hợp hai hướng. Nhóm em xin cảm ơn và mong nhận góp ý của thầy.

---

## Tài liệu tham khảo dùng trong slide

[1] L. Ali và cs., Sensors 22(22):8820, 2022 · [2] A. S. Ludwika, A. P. Rifai, Safety 10(1):26, 2024 · [3] H. Luo và cs., Heliyon 10(16):e36264, 2024 · [9] A. Goyal và cs., arXiv:2606.21861 · [12] S. R. Yarrabothula và cs., SteelBench, arXiv:2607.05264 · Fire-ART: Y. Wen và cs., ISPRS J. Photogramm. Remote Sens. 231:679–703, 2025 · Landis & Koch, Biometrics 33(1):159–174, 1977

## Tài liệu đính kèm (tuỳ chọn)

- `De-cuong-NCKH-Tran-Tuan-Kiet.pdf`: đề cương gốc, để Claude bên kia hiểu bối cảnh
- `fig_detector_compare.png` (trong thư mục `outputs/`): **đính kèm ngay**, dùng cho trang 11
- `fig_kappa.png`: biểu đồ so sánh với người chấm, gửi sau khi có ảnh phòng thí nghiệm
