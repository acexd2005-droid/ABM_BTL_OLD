# Trạng thái các giai đoạn (điều phối viên cập nhật)

Trạng thái: CHUA_LAM · DANG_LAM · XONG · XONG_CHO_DUYET · BI_CHAN · DUNG

| Giai đoạn | Tên | Phụ thuộc | Trạng thái | Commit | Báo cáo | Ghi chú |
|---|---|---|---|---|---|---|
| GD7c | Quyết định GĐ8 + chỉ đạo LS và biên cho vay | – | XONG | ff20d53 | reports/calibration/estimates_stage7c.md | Làm thủ công trước khi cài điều phối; không có bằng chứng chỉ đạo làm hẹp biên → giữ D6 |
| GD9a | Đưa hằng số cứng còn lại ra YAML | – | XONG_CHO_DUYET | 9e806f4 | reports/giai_doan/GD9a.md | 13 khóa mới, hành vi bitwise không đổi; reviewer ĐẠT vòng 1; 2 việc NHỎ chuyển sang đầu GD9 |
| GD9 | Hiệu chỉnh bằng mô phỏng + kiểm định ngoài mẫu lịch sử | GD7c, GD9a | XONG_CHO_DUYET | 464c86d | reports/giai_doan/GD9.md | Reviewer ĐẠT CÓ ĐIỀU KIỆN sau 2 vòng; nghiệm ở biên lưới (λ 0.45 ngoài CI), chờ Huy: Q4b, Q6, Q7 |
| GD9b | Hiệu chỉnh lại GD9 theo D9 (Q7 bù tăng trưởng; Q6 lưới λ ∈ CI, biên tổng 3.4–4.8) | GD9 | XONG_CHO_DUYET | 0b8ec53 | reports/giai_doan/GD9b.md | Reviewer ĐẠT CÓ ĐIỀU KIỆN sau 2 vòng; nghiệm góc λ 0.40 (ngoài CI 0.005), biên tổng 3.4; bù Q7 làm hết chạm trần LDR nhưng C không phân biệt được với B; ngoài mẫu LS cho vay kém GD9. Chờ Huy: Q9–Q11 |
| GD10 | Chạy lại A/B/C, độ nhạy, độ vững | GD9b | XONG_CHO_DUYET | 05712bb | reports/giai_doan/GD10.md | Reviewer ĐẠT CÓ ĐIỀU KIỆN sau 2 vòng; dấu B−A, C−A giữ ở mọi biến thể, độ lớn ≈ −1.4×policy_step (giả định); B và C không phân biệt được; chờ Huy: Q12, Q13 (và Q9–Q11) |
| GD11 | Khung kiểm định ngoài mẫu Q4/2026 | GD9b | XONG_CHO_DUYET | f8658cc | reports/giai_doan/GD11.md | Reviewer ĐẠT CÓ ĐIỀU KIỆN sau 2 vòng; chưa có kết quả ngoài mẫu thực (panel dừng ở 2026Q3); đã tải ON Q4/2026 đến 19/11; chạy lại script khi YAML đổi ở GD9b; Q8 đã đóng (D9) |
| GD10b | Độ nhạy `deposit_competition` ∈ {0.07, 0.3, 0.7, 1.2} và `policy_step` 0.375 trên GD9b (30 lần; không đổi YAML) | GD10 | XONG | ab6d156 | reports/giai_doan/GD10b.md | Theo D10 (Q10); quy tắc đọc đặt trước: báo cả 4 giá trị, không chọn. Gồm xuất sai lệch mức GD9b (Q14) |
| GD12 | Hoàn thiện báo cáo nghiên cứu | GD10, GD10b, GD11 | XONG_CHO_DUYET | 01f250c | reports/giai_doan/GD12.md | Reviewer ĐẠT sau 2 vòng; hộp 5 ý, B−A theo dải `policy_step` (TB ≈ −1.4×step, cuối kỳ ≈ −1.8×step), bảng GD9b/GD9/λ 0.35, hạn chế (a) +0.312, (b), (c). Hộp ý (ii) và ánh xạ step↔1.5–2 điểm % đã đóng theo D11 (không còn chờ Huy). Câu hỏi cho Minh: ngày/thứ tự CV 9608–9736, định nghĩa biên PT2 |
| GD13 | Tổng hợp cho trưởng nhóm | tất cả | CHUA_LAM | | reports/giai_doan/TONG_HOP.md | Gồm cập nhật CLAUDE.md mục 4.2 (Q3, được phép) |

## Quyết định đang mở (chờ Huy)
| # | Giai đoạn | Câu hỏi | Mặc định đã áp dụng | Giai đoạn bị ảnh hưởng |
|---|---|---|---|---|
| Q1 | (trước) | Nguồn gốc `loan_spread_add = 1.35` | Giữ 1.35; biên tổng hiệu chỉnh qua `target_margin` ở GD9 | GD9 |
| Q2 | (trước) | r^L trong mô hình là LS chào khoản vay mới hay LS bình quân danh mục | Coi là bình quân danh mục (vì đối chiếu với lợi suất sổ sách) | GD9, GD12 |
| Q4 | GD9a | Chặn `demand_pressure` ±0.5 và tăng trưởng tiền gửi: 1 khóa đối xứng hay 2 khóa sàn/trần | 1 khóa đối xứng (`demand_pressure_cap`, `depositor_max_growth`) | GD9 (dạng tham số có thể hiệu chỉnh; Bước 1 GD9 dùng phân vị 2.5/97.5 – nếu bất đối xứng sẽ cần tách khóa) |
| Q5 | GD9a | Đưa miền hợp lệ 0–20/0–14 và sàn 0.01 ra YAML? | Giữ cứng (trùng assert mục 6) | Không |

## Quyết định đã đóng (Huy, 21/11/2026 – D9 và D10 trong LO_TRINH.md; D11 ghi tại đây và GD12.md)
| # | Giai đoạn | Quyết định | Áp dụng ở |
|---|---|---|---|
| Q3 | GD9a | ĐÃ ĐÓNG – Cho phép cập nhật CLAUDE.md mục 4.2 trong GD13 (chỉ tài liệu) | GD13 |
| Q4b | GD9 | ĐÃ ĐÓNG – Duyệt (a): giữ khóa `depositor_min_growth`, chặn bất đối xứng | GD9b, GD10 |
| Q6 | GD9 | ĐÃ ĐÓNG – Bản chính ràng buộc λ ∈ {0.15…0.40}, biên tổng {3.4…4.8}; nghiệm chạm cận dưới biên tổng thì giữ, không mở rộng; λ = 0.45 chỉ vào độ nhạy GD10 | GD9b, GD10 |
| Q7 | GD9 | ĐÃ ĐÓNG – (b) Bù độ lệch tăng trưởng tổng vào `base_growth` để khớp trung bình dữ liệu trong cửa sổ | GD9b |
| Q8 | GD11 | ĐÃ ĐÓNG – Đồng ý mặc định: không đặt ngưỡng, chỉ báo tín hiệu/nhiễu | GD12 |
| Q9 | GD9b | ĐÃ ĐÓNG (D10) – GD9b là cấu hình chính, ghi "nghiệm biên"; không mở rộng lưới; λ 0.35 và GD9 vào bảng đối chiếu | GD10, GD12 |
| Q10 | GD9b | ĐÃ ĐÓNG (D10) – không đổi `deposit_competition`/ngưỡng LDR; thêm GD10b (độ nhạy {0.07, 0.3, 0.7, 1.2}, báo cả 4) | GD10b, GD12 |
| Q11 | GD9b | ĐÃ ĐÓNG (D10) – không chọn theo ngoài mẫu; GD9 song song trong GD12 | GD12 |
| Q12 | GD10 | ĐÃ ĐÓNG (D10) – giữ YAML; báo cả hai bản học | GD12 |
| Q13 | GD10 | ĐÃ ĐÓNG (D10) – giữ ngưỡng; B−A báo theo dải `policy_step` | GD12 |
| Q14 | GD10 | MỚI, ĐÃ ĐÓNG (D10) – sai lệch mức LS huy động là hạn chế; xuất sai lệch mức trong mẫu GD9b ra CSV trước GD12 | GD12 |
| D11-a | GD12 | ĐÃ ĐÓNG (D11) – ý (ii) của hộp "Những điều không được diễn giải" thay bằng: không so sánh trực tiếp B−A với mức giảm 1,5–2%/năm trong CV 9608 (chỉ đạo nhắm SXKD/ưu tiên, `policy_step` trừ vào toàn bộ lãi suất cho vay); step 0.14–0.50 cho B−A cuối kỳ −0.26 đến −0.89 điểm % | GD12, GD13 |
| D11-b | GD12 | ĐÃ ĐÓNG (D11) – ánh xạ step 0.375–0.50 ≈ 1,5–2 điểm %/năm: chỉ giữ một câu ở thiết kế kịch bản (mục 4.4), ghi "giả định" và nêu khác phạm vi; xóa khỏi phần kết quả và kết luận | GD12, GD13 |
