# Trạng thái các giai đoạn (điều phối viên cập nhật)

Trạng thái: CHUA_LAM · DANG_LAM · XONG · XONG_CHO_DUYET · BI_CHAN · DUNG

| Giai đoạn | Tên | Phụ thuộc | Trạng thái | Commit | Báo cáo | Ghi chú |
|---|---|---|---|---|---|---|
| GD7c | Quyết định GĐ8 + chỉ đạo LS và biên cho vay | – | XONG | ff20d53 | reports/calibration/estimates_stage7c.md | Làm thủ công trước khi cài điều phối; không có bằng chứng chỉ đạo làm hẹp biên → giữ D6 |
| GD9a | Đưa hằng số cứng còn lại ra YAML | – | XONG_CHO_DUYET | | reports/giai_doan/GD9a.md | 13 khóa mới, hành vi bitwise không đổi; reviewer ĐẠT vòng 1; 2 việc NHỎ chuyển sang đầu GD9 |
| GD9 | Hiệu chỉnh bằng mô phỏng + kiểm định ngoài mẫu lịch sử | GD7c, GD9a | CHUA_LAM | | reports/giai_doan/GD9.md | |
| GD10 | Chạy lại A/B/C, độ nhạy, độ vững | GD9 | CHUA_LAM | | reports/giai_doan/GD10.md | |
| GD11 | Khung kiểm định ngoài mẫu Q4/2026 | GD9 | CHUA_LAM | | reports/giai_doan/GD11.md | |
| GD12 | Hoàn thiện báo cáo nghiên cứu | GD10, GD11 | CHUA_LAM | | reports/giai_doan/GD12.md | |
| GD13 | Tổng hợp cho trưởng nhóm | tất cả | CHUA_LAM | | reports/giai_doan/TONG_HOP.md | |

## Quyết định đang mở (chờ Huy)
| # | Giai đoạn | Câu hỏi | Mặc định đã áp dụng | Giai đoạn bị ảnh hưởng |
|---|---|---|---|---|
| Q1 | (trước) | Nguồn gốc `loan_spread_add = 1.35` | Giữ 1.35; biên tổng hiệu chỉnh qua `target_margin` ở GD9 | GD9 |
| Q2 | (trước) | r^L trong mô hình là LS chào khoản vay mới hay LS bình quân danh mục | Coi là bình quân danh mục (vì đối chiếu với lợi suất sổ sách) | GD9, GD12 |
| Q3 | GD9a | CLAUDE.md mục 4.2 lỗi thời (danh sách hằng số cứng; câu "1.15/12 khác YAML") – cập nhật? | Không sửa CLAUDE.md (việc của Huy) | Không (chỉ tài liệu) |
| Q4 | GD9a | Chặn `demand_pressure` ±0.5 và tăng trưởng tiền gửi: 1 khóa đối xứng hay 2 khóa sàn/trần | 1 khóa đối xứng (`demand_pressure_cap`, `depositor_max_growth`) | GD9 (dạng tham số có thể hiệu chỉnh; Bước 1 GD9 dùng phân vị 2.5/97.5 – nếu bất đối xứng sẽ cần tách khóa) |
| Q5 | GD9a | Đưa miền hợp lệ 0–20/0–14 và sàn 0.01 ra YAML? | Giữ cứng (trùng assert mục 6) | Không |
