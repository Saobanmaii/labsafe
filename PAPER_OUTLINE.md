# DÀN Ý BÀI BÁO (khuôn IEEE hai cột, 4–6 trang)

> Bám theo cấu trúc bài mẫu: *Yadav et al., "CLAHE Based Enhancement For Real Time Video System", ICACCI 2014*.
> Soạn bằng LaTeX `IEEEtran` trên Overleaf, chọn compiler **XeLaTeX** để gõ tiếng Việt.

**Tên bài (đề xuất):** Chấm điểm an toàn phòng thí nghiệm từ ảnh: so sánh hệ thống dựa trên luật và mô hình ngôn ngữ–thị giác với đánh giá của con người

| Mục | Độ dài | Nội dung | Nguồn |
|---|---|---|---|
| **Abstract + Keywords** | ~150 chữ | Vấn đề → phương pháp (YOLO + luật, VLM, người chấm) → dữ liệu (N ảnh, 4 tiêu chí) → kết quả chính (κ của từng cách) → kết luận | Viết sau cùng |
| **I. Giới thiệu** | 0,5 trang | Kiểm tra thủ công tốn công, thiếu nhất quán, không lưu bằng chứng; camera có sẵn; câu hỏi nghiên cứu; đóng góp (3 gạch đầu dòng) | Đề cương mục 1, 3 |
| **II. Các nghiên cứu liên quan và cơ sở lý thuyết** | 1 trang | A. Phát hiện đồ bảo hộ bằng YOLO [1–3] · B. VLM trong đánh giá an toàn và độ nhạy với prompt [9–12] · C. Cơ sở: YOLO [7], hệ số kappa [13], **có công thức** Cohen's κ, Fleiss' κ | Đề cương mục 2 |
| **III. Phương pháp đề xuất** | 1,5 trang | A. Bảng tiêu chí (bảng 4 tiêu chí) · B. Hệ thống luật: **lưu đồ** (giống Fig. 4 bài mẫu), **công thức tỷ lệ chiếm dụng R**, tỷ lệ che bình, **các bước Step 1…n** (giống bài mẫu) · C. **Ví dụ tính tay** trên lưới 10×10 (từ đề cương 4.2) · D. VLM: model, 3 biến thể prompt, temperature, định dạng JSON · E. Người chấm: số người, quy trình, gộp nhãn đa số | Đề cương mục 4 + RUBRIC |
| **IV. Thực nghiệm và kết quả** | 1,5 trang | A. Dữ liệu: dataset train (Roboflow + COCO), bộ test tự chụp (N ảnh, 4 góc, 9 kịch bản) · B. Chỉ số đánh giá · C. **Bảng chính:** tỷ lệ khớp, κ [CI 95%] theo tiêu chí × {luật, VLM-P1, P2, P3} + đồng thuận giữa người chấm · D. **Bảng độ ổn định prompt** · E. **Hình:** ảnh minh họa (vùng + hộp bao), biểu đồ κ · F. Phân tích ca lỗi (3–4 ca, có ảnh) · G. Tốc độ/chi phí | Script đánh giá |
| **V. Kết luận và hướng phát triển** | 0,3 trang | Trả lời 3 câu hỏi nghiên cứu; hạn chế (ảnh dàn dựng, mẫu nhỏ, 2D/phối cảnh, COCO gộp chai); hướng phát triển (thêm tiêu chí hóa chất và dây điện, dữ liệu camera thật, kết hợp luật + VLM) | |
| **Tài liệu tham khảo** | | Giữ [1]–[3], [7], [9]–[13] từ đề cương. **Bỏ [4], [5], [6], [8]** nếu không dùng (CLAHE, SLIC, fire detection), hoặc trích [5] nếu có tiền xử lý ánh sáng. Bổ sung tên tác giả cho [2], [3]. Thêm trích dẫn COCO, Ultralytics YOLO, Fleiss 1971, dataset Roboflow | |

## Bảng và hình dự kiến

| Ký hiệu | Nội dung |
|---|---|
| Bảng I | Bảng tiêu chí: 4 tiêu chí, định nghĩa Vi phạm, luật máy tương ứng |
| Bảng II | Thống kê dữ liệu: số ảnh, số ca vi phạm mỗi tiêu chí (theo nhãn người) |
| **Bảng III** | **Kết quả chính:** độ khớp và κ theo tiêu chí × phương pháp |
| Bảng IV | Độ ổn định prompt của VLM |
| Hình 1 | Lưu đồ tổng thể (3 cột đánh giá) |
| Hình 2 | Lưu đồ hệ thống luật |
| Hình 3 | Ví dụ tính tỷ lệ chiếm dụng trên lưới 10×10 |
| Hình 4 | Ảnh mẫu: vùng + hộp bao YOLO + kết luận từng tiêu chí |
| Hình 5 | Biểu đồ cột κ theo tiêu chí và phương pháp |
| Hình 6 | Ca lỗi tiêu biểu (ví dụ: chai hóa chất bị nhận nhầm là đồ uống) |

## Công thức sẽ dùng

- Tỷ lệ chiếm dụng lối đi: $R = \dfrac{\left|\left(\bigcup_i B_i^{\text{đáy}}\right) \cap A\right|}{|A|}$
- Tỷ lệ che bình chữa cháy: $O = \dfrac{\left|E \cap \bigcup_j B_j\right|}{|E|}$
- Cohen's kappa: $\kappa = \dfrac{p_o - p_e}{1 - p_e}$
- Fleiss' kappa: $\kappa_F = \dfrac{\bar{P} - \bar{P}_e}{1 - \bar{P}_e}$
- Khoảng tin cậy 95%: bootstrap 2000 lần lấy mẫu lại trên tập ảnh

## Giả thuyết cần kiểm chứng (từ đề cương)

- Tiêu chí có đối tượng rõ ràng, đếm được (C3, C4) → cả hai cách chấm đều khớp tốt với người.
- Tiêu chí mang tính chủ quan hoặc phụ thuộc vùng (C1, C2) → độ khớp thấp hơn, kể cả giữa các người chấm với nhau.
- VLM dao động theo prompt rõ hơn ở các tiêu chí chủ quan.
