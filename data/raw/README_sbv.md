# Dữ liệu lãi suất NHNN

- `sbv_lnh_qua_dem_theo_quy.csv`, `sbv_lnh_qua_dem_theo_thang.csv`: lãi suất bình quân liên ngân hàng VND kỳ hạn qua đêm, tính từ 970 phiên (12/2022–10/2026) lấy ngày 21/11/2026 từ API của trang "Lãi suất thị trường liên ngân hàng" trên sbv.gov.vn (content structure 3450260). Ngày phiên = "ngày áp dụng" theo giờ VN; bỏ 14 bản ghi lặp ngày nghỉ; ngày có nhiều bản ghi giữ bản mới nhất.
- Đối chiếu: 2023Q1–Q2 khớp số công bố (~4,8 / 3,6); bình quân năm 2024 = 3,40 (công bố 3,4); 2026Q2–Q3 lệch ≤ 0,06 so với Tạp chí Doanh Nhân VN.
- `sbv_lai_suat_dieu_hanh_quy.csv`: tái cấp vốn / tái chiết khấu bình quân theo ngày và cuối quý, tính từ các quyết định 313, 576, 950, 1123/QĐ-NHNN năm 2023; giữ nguyên 4,5% / 3,0% từ 19/6/2023.
- Tái tạo: `python src/data/fetch_sbv_interbank.py --outdir data/raw`. Máy chủ NHNN có thể chặn client không phải trình duyệt (lỗi 403 "No server") sau vài lượt gọi; script có cache theo tháng để chạy tiếp.
