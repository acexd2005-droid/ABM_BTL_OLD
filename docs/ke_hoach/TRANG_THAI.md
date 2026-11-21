# Trạng thái các giai đoạn (điều phối viên cập nhật)

Trạng thái: CHUA_LAM · DANG_LAM · XONG · XONG_CHO_DUYET · BI_CHAN · DUNG

| Giai đoạn | Tên | Phụ thuộc | Trạng thái | Commit | Báo cáo | Ghi chú |
|---|---|---|---|---|---|---|
| GD7c | Quyết định GĐ8 + chỉ đạo LS và biên cho vay | – | CHUA_LAM | | reports/giai_doan/GD7c.md | |
| GD9a | Đưa hằng số cứng còn lại ra YAML | – | CHUA_LAM | | reports/giai_doan/GD9a.md | |
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
