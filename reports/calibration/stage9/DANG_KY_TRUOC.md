# Giai đoạn 9 – Đăng ký trước (viết TRƯỚC khi chạy lưới, không sửa sau khi có kết quả)

Ngày 2026-11-21. Thực hiện bởi `src/calibration/calibrate_stage9.py`. Tài liệu này chỉ ghi phương pháp, không có kết quả số.

## Dữ liệu và cửa sổ
- Cấu hình nền: `configs/scenarios.yaml` + ghi đè `configs/scenarios_macro.yaml` (D2). Dữ liệu khởi tạo `data/clean/abm_initial_8nganhang_2023Q1.csv`, chuỗi thực từ `data/clean/abm_panel_8nganhang_2023Q1_2026Q3.csv`.
- Cửa sổ hiệu chỉnh: 2023Q2–2025Q2 (`month` 1–9). Ngoài mẫu: 2025Q3–2026Q3 (`month` 10–14), KHÔNG dùng để chọn tham số.
- Kịch bản A không dùng số ngẫu nhiên (chỉ B/C rút xác suất tuân thủ) nên mỗi bộ tham số chạy 1 lần (seed = `base_seed`); script kiểm tra lại điều này bằng một seed khác.

## Bước 1 – Tăng trưởng (quy tắc đặt trước, không tối ưu)
- `depositor_base_growth`, `borrower_base_growth` = trung bình (9 quý trong cửa sổ) của tăng trưởng quý của TỔNG tiền gửi / TỔNG dư nợ 8 NH (`sum_t / sum_{t-1} − 1`), cùng cách mô hình tổng hợp `deposit_growth`, `credit_growth`.
- Ngưỡng chặn = phân vị 2.5% và 97.5% (numpy, nội suy tuyến tính mặc định) của tăng trưởng quý **theo ngân hàng-quý** trong cửa sổ (8 × 9 = 72 quan sát), vì chặn áp dụng cho từng ngân hàng.
  - Dư nợ: `borrower_growth_min` = P2.5, `borrower_growth_max` = P97.5 (đã có hai khóa).
  - Tiền gửi (Q4 TRANG_THAI.md): hai cách hợp lý, chạy cả hai:
    - **(chính)** bất đối xứng: `depositor_min_growth` = P2.5 (khóa tùy chọn mới, mặc định null = hành vi cũ), `depositor_max_growth` = P97.5. Tiêu chí chọn làm chính: áp dụng **nguyên văn** quy tắc LO_TRINH (sàn = P2.5, trần = P97.5).
    - (phụ) đối xứng, không cần khóa mới: `depositor_max_growth` = max(|P2.5|, |P97.5|).
- Quan sát bất thường đã biết trong cửa sổ (`reports/calibration/outliers_stage7.csv`): HDBank 2023Q2, MB Bank 2023Q4, MB Bank 2024Q4 (MB Bank 2025Q4 nằm ngoài cửa sổ). Bản phụ: loại các ngân hàng-quý này khỏi cả trung bình (tổng của các NH còn lại trong quý đó) lẫn phân vị. Bản chính dùng đủ dữ liệu.
- `deposit_ldr_target` ứng viên thứ hai = bình quân đơn giản LDR (loans/deposits) theo ngân hàng-quý trong cửa sổ (72 quan sát; ngưỡng áp cho từng NH). Bản loại bất thường dùng cùng giá trị với bản đủ dữ liệu cho LDR (LDR không phải tăng trưởng).

## Bước 2 – Lưới (kịch bản A)
- `pass_through` ∈ {0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45}
- biên tổng ∈ {3.8, 4.0, 4.2, 4.4, 4.6, 4.8} qua `target_margin` = biên tổng − `loan_spread_add` (1.35 giữ nguyên)
- `base_deposit_rate_step` ∈ {0, 0.006, 0.012, 0.018}; `deposit_competition` ∈ {0.07, 0.3, 0.7, 1.2}; `deposit_ldr_target` ∈ {0.82, LDR bình quân}
- 1536 bộ cho mỗi biến thể Bước 1. Các tham số khác giữ giá trị `scenarios_macro.yaml` (σ, ε, policy_pressure, policy_step KHÔNG hiệu chỉnh).

## Hàm mục tiêu (chốt trước khi chạy)
J = 0.5 · RMSE_L + 0.5 · RMSE_D trên `month` 1–9, với
- RMSE_L = sqrt(mean_t (r^L_mô_hình,t − r^L_thực,t)²), r^L_mô_hình = `loan_rate` của `history` (gia quyền dư nợ), r^L_thực = `loan_rate_pct` gia quyền dư nợ (`prepare_actual_from_panel`).
- RMSE_D tương tự với r^D cơ sở dữ liệu: mô hình = Σ deposit_rate_i(1−casa_i)·deposits_i / Σ deposits_i (từ `bank_history`); thực = Σ deposit_rate_pct·deposits / Σ deposits.
- Bộ tốt nhất = argmin J; hòa thì lấy bộ đứng trước theo thứ tự lưới (λ, biên, base_step, δ, LDR tăng dần).
- Bộ chính ghi vào `configs/scenarios_calibrated.yaml` = argmin J của biến thể Bước 1 chính (bất đối xứng, đủ dữ liệu). Các biến thể khác chỉ báo cáo.

## Bước 3 – Ngoài mẫu (month 10–14)
RMSE thô, RMSE khử mức (độ lệch chuẩn của sai số, ddof = 0), sai số trung bình; biên độ (max − min) và quý đáy trong cửa sổ ngoài mẫu; tỷ lệ biên độ chữ V và quý đáy trên toàn chuỗi 2023Q2–2026Q3 cho các cấu hình mô hình. So: (i) cấu hình GĐ8 chưa hiệu chỉnh (`scenarios_macro.yaml`), (ii) giữ giá trị 2025Q2, (iii) r_t = r_2025Q2 + 0.45·(ON_{t−1} − ON_2025Q1) (áp cho cả hai chuỗi). Ghi rõ mô hình (và mốc (iii)) được cấp ON thực ngoài mẫu.

## Bước 4
Mục 6 CLAUDE.md, A/B/C 10 lần chạy với `scenarios_calibrated.yaml`; kiểm tra ngưỡng `deposit_ldr_target` và biên mục tiêu có thực sự đạt tới trong mô phỏng; tỷ lệ ngân hàng-quý chạm các ngưỡng chặn tăng trưởng và trần LDR. Vi phạm mục 6 → DỪNG.

## Phụ lục (thêm SAU khi chạy lưới chính – chỉ chẩn đoán, không đổi bộ chính)
Lưới chính cho nghiệm ở biên lưới (λ = 0.45 cận trên; biên tổng 3.8, base_step 0, δ 0.07 cận dưới). Thêm hai phân tích CHỈ ĐỂ BÁO CÁO, không thay bộ ghi vào `scenarios_calibrated.yaml`:
1. Bộ tốt nhất với λ trong CI GĐ7 [0.158; 0.395] (tức λ ∈ {0.20, 0.25, 0.30, 0.35} của lưới), cùng biến thể Bước 1 chính; báo J và ngoài mẫu.
2. Lưới mở rộng chẩn đoán (biến thể Bước 1 chính): λ ∈ {0.10, 0.15, …, 1.00}, biên tổng ∈ {3.0, 3.2, 3.4, 3.6, 3.8}, base_step ∈ {0}, δ ∈ {0, 0.035, 0.07}, ngưỡng LDR = LDR bình quân. Mục đích: cho biết cực tiểu có nằm ngoài lưới đã duyệt không.
