# Trạng thái các giai đoạn (điều phối viên cập nhật)

Trạng thái: CHUA_LAM · DANG_LAM · XONG · XONG_CHO_DUYET · BI_CHAN · DUNG

| Giai đoạn | Tên | Phụ thuộc | Trạng thái | Commit | Báo cáo | Ghi chú |
|---|---|---|---|---|---|---|
| GD7c | Quyết định GĐ8 + chỉ đạo LS và biên cho vay | – | XONG | ff20d53 | reports/calibration/estimates_stage7c.md | Làm thủ công trước khi cài điều phối; không có bằng chứng chỉ đạo làm hẹp biên → giữ D6 |
| GD9a | Đưa hằng số cứng còn lại ra YAML | – | XONG_CHO_DUYET | 9e806f4 | reports/giai_doan/GD9a.md | 13 khóa mới, hành vi bitwise không đổi; reviewer ĐẠT vòng 1; 2 việc NHỎ chuyển sang đầu GD9 |
| GD9 | Hiệu chỉnh bằng mô phỏng + kiểm định ngoài mẫu lịch sử | GD7c, GD9a | XONG_CHO_DUYET | 464c86d | reports/giai_doan/GD9.md | Reviewer ĐẠT CÓ ĐIỀU KIỆN sau 2 vòng; nghiệm ở biên lưới (λ 0.45 ngoài CI), chờ Huy: Q4b, Q6, Q7 |
| GD9b | Hiệu chỉnh lại GD9 theo D9 (Q7 bù tăng trưởng; Q6 lưới λ ∈ CI, biên tổng 3.4–4.8) | GD9 | XONG_CHO_DUYET | 0b8ec53 | reports/giai_doan/GD9b.md | Reviewer ĐẠT CÓ ĐIỀU KIỆN sau 2 vòng; nghiệm góc λ 0.40 (ngoài CI 0.005), biên tổng 3.4; bù Q7 làm hết chạm trần LDR nhưng C không phân biệt được với B; ngoài mẫu LS cho vay kém GD9. Chờ Huy: Q9–Q11 |
| GD10 | Chạy lại A/B/C, độ nhạy, độ vững | GD9b | XONG_CHO_DUYET | HASH10 | reports/giai_doan/GD10.md | Reviewer ĐẠT CÓ ĐIỀU KIỆN sau 2 vòng; dấu B−A, C−A giữ ở mọi biến thể, độ lớn ≈ −1.4×policy_step (giả định); B và C không phân biệt được; chờ Huy: Q12, Q13 (và Q9–Q11) |
| GD11 | Khung kiểm định ngoài mẫu Q4/2026 | GD9b | XONG_CHO_DUYET | f8658cc | reports/giai_doan/GD11.md | Reviewer ĐẠT CÓ ĐIỀU KIỆN sau 2 vòng; chưa có kết quả ngoài mẫu thực (panel dừng ở 2026Q3); đã tải ON Q4/2026 đến 19/11; chạy lại script khi YAML đổi ở GD9b; Q8 đã đóng (D9) |
| GD12 | Hoàn thiện báo cáo nghiên cứu | GD10, GD11 | CHUA_LAM | | reports/giai_doan/GD12.md | |
| GD13 | Tổng hợp cho trưởng nhóm | tất cả | CHUA_LAM | | reports/giai_doan/TONG_HOP.md | Gồm cập nhật CLAUDE.md mục 4.2 (Q3, được phép) |

## Quyết định đang mở (chờ Huy)
| # | Giai đoạn | Câu hỏi | Mặc định đã áp dụng | Giai đoạn bị ảnh hưởng |
|---|---|---|---|---|
| Q1 | (trước) | Nguồn gốc `loan_spread_add = 1.35` | Giữ 1.35; biên tổng hiệu chỉnh qua `target_margin` ở GD9 | GD9 |
| Q2 | (trước) | r^L trong mô hình là LS chào khoản vay mới hay LS bình quân danh mục | Coi là bình quân danh mục (vì đối chiếu với lợi suất sổ sách) | GD9, GD12 |
| Q4 | GD9a | Chặn `demand_pressure` ±0.5 và tăng trưởng tiền gửi: 1 khóa đối xứng hay 2 khóa sàn/trần | 1 khóa đối xứng (`demand_pressure_cap`, `depositor_max_growth`) | GD9 (dạng tham số có thể hiệu chỉnh; Bước 1 GD9 dùng phân vị 2.5/97.5 – nếu bất đối xứng sẽ cần tách khóa) |
| Q5 | GD9a | Đưa miền hợp lệ 0–20/0–14 và sàn 0.01 ra YAML? | Giữ cứng (trùng assert mục 6) | Không |
| Q9 | GD9b | Nghiệm GD9b chạm góc lưới (λ = 0.40 ngoài CI GĐ7 0.005; biên tổng 3.4 cận dưới; J đơn điệu) – giữ làm cấu hình chính? | Giữ theo D9 (không mở rộng lưới); λ = 0.35 (trong CI, J +0.0055) và nghiệm GD9 đưa vào độ nhạy GD10 | GD10, GD12 |
| Q10 | GD9b | Bù Q7 làm nhánh áp lực huy động gần như không kích hoạt (LDR TB của A sau chính sách 1.46 → 1.09), nên C−B ≈ 0 (−0.0014) và C không phân biệt được với B; xem lại `deposit_competition`/ngưỡng LDR (ngoài phạm vi D9)? | Giữ GD9b; GD10 báo B vs C ở mức "không phân biệt được" và so thêm biến thể GD9 (`scenarios_calibrated_gd9.yaml`) cho B vs C | GD10, GD12 |
| Q11 | GD9b | Ngoài mẫu LS cho vay GD9b kém GD9 (RMSE thô 0.592 so 0.477; sai số TB −0.338 so +0.122); tăng trưởng tiền gửi ngoài mẫu gấp 1.67 lần dữ liệu. Chọn cấu hình chính theo ngoài mẫu / bù lần hai? | Không: tiêu chí đã đăng ký là J trong mẫu; không bù lần hai | GD10, GD12 |
| Q12 | GD10 | Khi bật học thích nghi, `margin_min` 2.2 / `margin_max` 4.2 trong YAML chính > `target_margin` hiệu chỉnh 2.05: biên bị đẩy lên ngay quý đầu (A 7.978 → 8.164; tuân thủ 0.818 → 0.849). Dời cửa sổ theo `target_margin`? | Giữ YAML làm bản chính; chạy song song bản dời cửa sổ −1.15, B−A/C−A như nhau ở cả hai | GD12 (phần độ vững học thích nghi) |
| Q13 | GD10 | Tiêu chí "giữ dấu / giữ độ lớn (tỷ số 0.5–1.5) / C phân biệt B (|C−B| ≥ 10% |B−A| và CI ghép cặp loại 0)" do người thực thi đặt trước vì LO_TRINH không có ngưỡng; báo B−A theo dải policy_step (không nêu một số) | Giữ tiêu chí đã đặt trước; báo độ nhạy ngưỡng 5%, 1%; báo dải theo step | GD12 |

## Quyết định đã đóng (Huy, 21/11/2026 – D9 trong LO_TRINH.md)
| # | Giai đoạn | Quyết định | Áp dụng ở |
|---|---|---|---|
| Q3 | GD9a | ĐÃ ĐÓNG – Cho phép cập nhật CLAUDE.md mục 4.2 trong GD13 (chỉ tài liệu) | GD13 |
| Q4b | GD9 | ĐÃ ĐÓNG – Duyệt (a): giữ khóa `depositor_min_growth`, chặn bất đối xứng | GD9b, GD10 |
| Q6 | GD9 | ĐÃ ĐÓNG – Bản chính ràng buộc λ ∈ {0.15…0.40}, biên tổng {3.4…4.8}; nghiệm chạm cận dưới biên tổng thì giữ, không mở rộng; λ = 0.45 chỉ vào độ nhạy GD10 | GD9b, GD10 |
| Q7 | GD9 | ĐÃ ĐÓNG – (b) Bù độ lệch tăng trưởng tổng vào `base_growth` để khớp trung bình dữ liệu trong cửa sổ | GD9b |
| Q8 | GD11 | ĐÃ ĐÓNG – Đồng ý mặc định: không đặt ngưỡng, chỉ báo tín hiệu/nhiễu | GD12 |
