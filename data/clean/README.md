# Dữ liệu thực tế do Minh chuyển giao

Không có dữ liệu ngân hàng thực trong bản giao này. Mô hình dùng 9 ngân hàng hư cấu khi chưa truyền `--banks`.

Định dạng WIDE cho `--banks`: `bank_id,group,deposits,loans,deposit_rate,loan_rate,casa_ratio`.
Các cột có thể thêm: `target_margin,capital_ratio,npl_ratio`.

CSV LONG nhóm đã thống nhất gồm `ngan_hang,ky,chi_tieu,gia_tri,don_vi,nguon,ngay_truy_cap`.
Cần pivot thành 1 dòng/ngân hàng cho kỳ khởi tạo; thống nhất cách đổi đơn vị và tần suất với Minh.

Chuỗi thực tế cho `--actual`: `month,loan_rate`; month=1..24 cùng kỳ mô phỏng. Chỉ dùng số liệu có nguồn, không tự điền số giả để so với thực tế.
