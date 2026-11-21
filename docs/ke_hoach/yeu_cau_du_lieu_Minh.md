# Yêu cầu dữ liệu gửi Minh (TV2) – kiểm định ngoài mẫu sau chính sách (GD11)

Mục đích: khi có số liệu quý sau chính sách (CV 9608/9736, 10/2026), script `src/analysis/kiem_dinh_ngoai_mau.py` so dự báo A/B/C (cấu hình hiệu chỉnh) với thực tế. Cần **2026Q4** và, khi có, **2027Q1** (tối đa 2027Q3 vì mô hình chạy 18 quý).

## Định dạng: GIỮ NGUYÊN panel hiện tại
File mới (không sửa file cũ): `data/clean/abm_panel_8nganhang_2023Q1_<quý cuối>.csv`, ví dụ `abm_panel_8nganhang_2023Q1_2027Q1.csv`. Mã hóa UTF-8 (có/không BOM đều được). Một dòng cho mỗi cặp (ngân hàng, quý), **đủ 8 ngân hàng** cho mọi quý, các quý liên tục (không bỏ quý), gồm toàn bộ 2023Q1–2026Q3 như file cũ (số cũ giữ nguyên: script tự đối chiếu với panel cũ qua `--panel-cu`, mặc định `data/clean/abm_panel_8nganhang_2023Q1_2026Q3.csv`, và báo lỗi nếu bất kỳ giá trị nào của 2023Q1–2026Q3 khác) cộng quý mới.

| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| `bank_id` | mã ngân hàng, đúng 8 mã như file cũ | |
| `period` | `YYYYQn`, ví dụ `2026Q4` | |
| `nim_pct` | NIM | % |
| `deposits`, `loans` | tiền gửi, dư nợ cuối quý | cùng đơn vị với file cũ (triệu VND) |
| `npl_amount`, `npl_ratio` | nợ xấu (số tiền; tỷ lệ dạng số thập phân, vd 0.0167) | |
| `casa_ratio` | tỷ lệ CASA dạng thập phân | |
| `issued_papers`, `interbank_borrowing` | giấy tờ có giá phát hành; vay liên ngân hàng | như file cũ |
| `loan_rate_pct` | lợi suất cho vay sổ sách = thu nhập lãi cho vay / dư nợ BQ, **annualize** | %/năm |
| `deposit_rate_pct` | chi phí huy động sổ sách trên TỔNG tiền gửi, annualize | %/năm |

Yêu cầu: cùng định nghĩa và cách annualize với các quý cũ; không điền số giả; nếu một ngân hàng chưa công bố thì **bỏ cả quý đó khỏi file** (không có dòng nào của quý đó), **không để ô trống** và không để thiếu một ngân hàng nào trong quý (script từ chối ô trống và quý thiếu ngân hàng). Ghi nguồn và ngày truy cập vào `data/clean/README.md`. Lưu ý các quan sát lệch đã biết (HDBank 2023Q2, MB Bank các Q4): nếu số Q4/2026 có điều chỉnh bất thường, ghi chú riêng.

Lãi suất liên ngân hàng qua đêm ngoài mẫu (không cần Minh): `data/raw/sbv_lnh_qua_dem_ngoai_mau.csv` (tải từ API NHNN; xem `data/raw/README_sbv.md`).

## Cách chạy khi có file
```
python -m src.analysis.kiem_dinh_ngoai_mau --panel data/clean/abm_panel_8nganhang_2023Q1_2027Q1.csv
```
File thật phải nằm trong `data/clean/` và tên không chứa "gia_lap"; nếu không script từ chối (trừ khi dùng `--gia-lap`, khi đó kết quả bị gắn GIA_LAP).

Khi panel chưa có quý sau 2026Q3, script dừng với thông báo và KHÔNG ghi bảng kết quả.
