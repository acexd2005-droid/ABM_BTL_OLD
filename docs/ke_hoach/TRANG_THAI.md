# Trạng thái các giai đoạn (điều phối viên cập nhật)

Trạng thái: CHUA_LAM · DANG_LAM · XONG · XONG_CHO_DUYET · BI_CHAN · DUNG

| Giai đoạn | Tên | Phụ thuộc | Trạng thái | Commit | Báo cáo | Ghi chú |
|---|---|---|---|---|---|---|
| GD7c | Quyết định GĐ8 + chỉ đạo LS và biên cho vay | – | XONG | ff20d53 | reports/calibration/estimates_stage7c.md | Làm thủ công trước khi cài điều phối; không có bằng chứng chỉ đạo làm hẹp biên → giữ D6 |
| GD9a | Đưa hằng số cứng còn lại ra YAML | – | XONG_CHO_DUYET | 9e806f4 | reports/giai_doan/GD9a.md | 13 khóa mới, hành vi bitwise không đổi; reviewer ĐẠT vòng 1; 2 việc NHỎ chuyển sang đầu GD9 |
| GD9 | Hiệu chỉnh bằng mô phỏng + kiểm định ngoài mẫu lịch sử | GD7c, GD9a | XONG_CHO_DUYET | 464c86d | reports/giai_doan/GD9.md | Reviewer ĐẠT CÓ ĐIỀU KIỆN sau 2 vòng; nghiệm ở biên lưới (λ 0.45 ngoài CI), chờ Huy: Q4b, Q6, Q7 |
| GD10 | Chạy lại A/B/C, độ nhạy, độ vững | GD9 | BI_CHAN | | reports/giai_doan/GD10.md | Chờ Huy quyết Q6/Q7 (đổi λ, biên tổng, quy tắc tăng trưởng thì đổi mức/độ lớn B−A, C−A; phải quyết trước, nếu đổi phải chạy lại lưới GD9) |
| GD11 | Khung kiểm định ngoài mẫu Q4/2026 | GD9 | XONG_CHO_DUYET | f8658cc | reports/giai_doan/GD11.md | Reviewer ĐẠT CÓ ĐIỀU KIỆN sau 2 vòng; chưa có kết quả ngoài mẫu thực (panel dừng ở 2026Q3); đã tải ON Q4/2026 đến 19/11; chờ Huy: Q8 |
| GD12 | Hoàn thiện báo cáo nghiên cứu | GD10, GD11 | BI_CHAN | | reports/giai_doan/GD12.md | Phụ thuộc GD10 (bị chặn bởi Q6/Q7) |
| GD13 | Tổng hợp cho trưởng nhóm | tất cả | BI_CHAN | | reports/giai_doan/TONG_HOP.md | Phụ thuộc GD10, GD12. Bản TONG_HOP tạm thời đã viết cho lượt chạy này |

## Quyết định đang mở (chờ Huy)
| # | Giai đoạn | Câu hỏi | Mặc định đã áp dụng | Giai đoạn bị ảnh hưởng |
|---|---|---|---|---|
| Q1 | (trước) | Nguồn gốc `loan_spread_add = 1.35` | Giữ 1.35; biên tổng hiệu chỉnh qua `target_margin` ở GD9 | GD9 |
| Q2 | (trước) | r^L trong mô hình là LS chào khoản vay mới hay LS bình quân danh mục | Coi là bình quân danh mục (vì đối chiếu với lợi suất sổ sách) | GD9, GD12 |
| Q3 | GD9a | CLAUDE.md mục 4.2 lỗi thời (danh sách hằng số cứng; câu "1.15/12 khác YAML") – cập nhật? | Không sửa CLAUDE.md (việc của Huy) | Không (chỉ tài liệu) |
| Q4 | GD9a | Chặn `demand_pressure` ±0.5 và tăng trưởng tiền gửi: 1 khóa đối xứng hay 2 khóa sàn/trần | 1 khóa đối xứng (`demand_pressure_cap`, `depositor_max_growth`) | GD9 (dạng tham số có thể hiệu chỉnh; Bước 1 GD9 dùng phân vị 2.5/97.5 – nếu bất đối xứng sẽ cần tách khóa) |
| Q5 | GD9a | Đưa miền hợp lệ 0–20/0–14 và sàn 0.01 ra YAML? | Giữ cứng (trùng assert mục 6) | Không |
| Q4b | GD9 | (tiếp Q4) Tiền gửi: chặn bất đối xứng (P2.5 = −0.0142 / P97.5 = 0.1732) qua khóa tùy chọn mới `depositor_min_growth` (null = hành vi cũ) hay đối xứng max(|P2.5|, |P97.5|) | Bản chính bất đối xứng (đúng nguyên văn quy tắc LO_TRINH, ghi trước khi chạy); đối xứng chạy song song: cùng bộ tham số tốt nhất, J lệch 0.0002 | GD10 (chỉ hình thức tham số; kết quả gần như không đổi) |
| Q6 | GD9 | Nghiệm lưới nằm ở biên lưới đã duyệt (λ = 0.45 cận trên, NGOÀI CI GĐ7 [0.158; 0.395]; biên tổng 3.8 cận dưới; base_step 0; δ 0.07 cận dưới). Lưới mở rộng chẩn đoán cho λ = 0.25, biên tổng 3.0 (lại ở biên), ngoài mẫu xấu hơn. Giữ bộ của lưới đã duyệt hay mở rộng lưới / ràng buộc λ trong CI? | Giữ argmin của lưới đã duyệt (λ 0.45, biên 3.8) trong `scenarios_calibrated.yaml`; chẩn đoán chỉ báo cáo | GD10 (λ, biên tổng là tham số chính của B−A) |
| Q7 | GD9 | Quy tắc tăng trưởng Bước 1 (base_growth = TB tăng trưởng tổng) KHÔNG tái tạo tăng trưởng tổng trong mô hình (TG 0.030 so với 0.040; DN 0.060 so với 0.045/quý) do số hạng lệch giữa các NH; Vietcombank chạm trần LDR 1.60 từ 2025Q4 (thực ~1.0). Giữ quy tắc đã duyệt hay bù độ lệch (chẩn đoán: bù một lần làm J 0.455 → 0.441, hết chạm trần LDR)? | Giữ quy tắc đã duyệt | GD10 (LDR, áp lực huy động; ít ảnh hưởng LS vì δ = 0.07) |
| Q8 | GD11 | Ngưỡng kinh tế để coi hướng hiệu ứng B−A/C−A (so với thực tế ngoài mẫu) là "đủ lớn" để diễn giải | Không có ngưỡng; chỉ báo signal_to_noise và độ lớn tuyệt đối; hướng chỉ diễn giải chính cho LS cho vay | GD12 |
