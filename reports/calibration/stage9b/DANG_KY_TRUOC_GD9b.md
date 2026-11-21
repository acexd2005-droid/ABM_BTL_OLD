# GD9b – Đăng ký trước (viết TRƯỚC khi chạy lưới GD9b; không sửa sau khi có kết quả)

Ngày 2026-11-21. Căn cứ: `docs/ke_hoach/LO_TRINH.md` (mục GD9b và D9: Q3, Q4b, Q6, Q7, Q8 do Huy duyệt). Tài liệu này chỉ ghi phương pháp; không chứa kết quả số nào của lưới GD9b. Các con số trích từ kết quả GD9 đã có (`reports/calibration/stage9/`) được nêu rõ nguồn. Đây là hiệu chỉnh tham số trong YAML; KHÔNG đổi công thức hành vi, KHÔNG chạm `src/agents/`, `src/core/`.

## 1. Dữ liệu, cửa sổ, hàm mục tiêu (giữ nguyên GD9)
- Cấu hình nền: `configs/scenarios.yaml` + ghi đè `configs/scenarios_macro.yaml`. Khởi tạo `data/clean/abm_initial_8nganhang_2023Q1.csv`; chuỗi thực `data/clean/abm_panel_8nganhang_2023Q1_2026Q3.csv`. Công cụ: tái sử dụng `src/calibration/calibrate_stage9.py` (khái quát hóa lưới/đầu ra sang thư mục `reports/calibration/stage9b/`, không đổi phương pháp).
- Cửa sổ hiệu chỉnh 2023Q2–2025Q2 (`month` 1–9). Ngoài mẫu 2025Q3–2026Q3 (`month` 10–14) KHÔNG dùng để chọn tham số (chỉ báo cáo).
- Hàm mục tiêu: **J = 0.5·RMSE_cho_vay + 0.5·RMSE_huy_động** trên `month` 1–9.
  - RMSE_cho_vay: `loan_rate` mô hình (gia quyền dư nợ, `history`) so `loan_rate_pct` thực gia quyền dư nợ.
  - RMSE_huy_động: Σ deposit_rate_i·(1−casa_i)·deposits_i / Σ deposits_i (mô hình, từ `bank_history`) so Σ deposit_rate_pct·deposits / Σ deposits (thực).
  - Giống hệt định nghĩa GD9 (`objective`).
- Kịch bản A không dùng số ngẫu nhiên nên mỗi bộ tham số chạy 1 lần với `seed = base_seed`; script kiểm tra tất định bằng seed thứ hai (`base_seed` + 7). "10 seed cho A" trong LO_TRINH thực chất là 1 chạy tất định (10 seed cho kết quả trùng nhau); các phép B/C (mục 6, nhiễu lẫn tuân thủ) dùng 10 seed `base_seed + i`, i = 0..9.

## 2. Quy tắc bù tăng trưởng Q7 (một lần, xác định trước, không tối ưu J)
Mục tiêu: tăng trưởng tổng của mô hình trong cửa sổ khớp tăng trưởng tổng của dữ liệu.

- Thước đo dữ liệu (như GD9 `growth_ldr_table`, dòng `thuc_te`, `trong_mau_1_9`): trung bình 9 quý (`month` 1–9) của `sum_t/sum_{t-1} − 1` trên TỔNG tiền gửi / TỔNG dư nợ 8 NH = **0.0397609337** (tiền gửi), **0.04475110499** (dư nợ).
- Thước đo mô hình: trung bình `month` 1–9 của `deposit_growth`, `credit_growth` (`history`, cùng cách gộp) của kịch bản A.
- Phép bù: `Δ_D = g_D(dữ liệu) − g_D(mô hình A)`; `Δ_L = g_L(dữ liệu) − g_L(mô hình A)`; 
  `depositor_base_growth_mới = depositor_base_growth_GD9 + Δ_D`; `borrower_base_growth_mới = borrower_base_growth_GD9 + Δ_L` (cộng, một bước, đúng như `growth_offset_diagnostic` của GD9). `depositor_base_growth_GD9` = 0.03976093370475935 và `borrower_base_growth_GD9` = 0.044751104985969604 (trung bình tăng trưởng tổng dữ liệu, quy tắc Bước 1 GD9).
- **Phụ thuộc bộ tham số và cách xử lý vòng phụ thuộc:** tăng trưởng mô hình phụ thuộc lãi suất, nên phụ thuộc bộ tham số lưới. Để tránh vòng (bù → lưới → bù…), Δ_D và Δ_L được tính **MỘT LẦN** tại cấu hình tham chiếu cố định, xác định trước, KHÔNG phụ thuộc J của GD9b: **bộ nghiệm GD9** (`configs/scenarios_calibrated.yaml` hiện tại, sẽ được sao thành `configs/scenarios_calibrated_gd9.yaml`: λ = 0.45, target_margin = 2.45, base_step = 0, δ = 0.07, ngưỡng LDR 1.0899618858566973, tăng trưởng GD9, ngưỡng chặn bất đối xứng). Giá trị bù này CỐ ĐỊNH rồi áp dụng nguyên cho MỌI điểm của lưới GD9b. Không lặp lại, không tính lại tại nghiệm GD9b để tối ưu J.
- Giá trị dự kiến (đã có trong `reports/calibration/stage9/diag_growth_stage9.csv`, dòng `bu_tang_truong`, sinh từ GD9, trước GD9b): `depositor_base_growth` = 0.0497668532 (Δ_D ≈ +0.0100059), `borrower_base_growth` = 0.02931768308 (Δ_L ≈ −0.0154334). Script GD9b phải tính lại bằng đúng công thức trên và báo giá trị; nếu khác các số này quá 1e-9 thì ghi lại và DỪNG để điều phối viên xử lý (không tự đổi quy tắc).
- Phần dư sau bù không xử lý lặp: báo cáo tăng trưởng tổng mô hình so dữ liệu tại nghiệm GD9b (trong mẫu và ngoài mẫu) như một kiểm tra, không dùng để bù lần hai.
- **Ngưỡng chặn giữ như GD9** (phân vị theo ngân hàng-quý, 72 quan sát, `np.percentile` nội suy tuyến tính, dữ liệu đủ):
  - tiền gửi: `depositor_min_growth` = P2.5 = −0.014160053263038454; `depositor_max_growth` = P97.5 = 0.17322255795489236;
  - dư nợ: `borrower_growth_min` = P2.5 = 0.0011790118598663808; `borrower_growth_max` = P97.5 = 0.13950953337717706.

## 3. Lưới (kịch bản A)
- `pass_through` λ ∈ {0.15, 0.20, 0.25, 0.30, 0.35, 0.40} (6 giá trị; D9/Q6, nằm trong CI GĐ7 [0.158; 0.395] trừ hai đầu 0.15 và 0.40 mà Huy đã chọn; ghi lại λ nào nằm trong CI).
- Biên tổng ∈ {3.4, 3.6, 3.8, 4.0, 4.2, 4.4, 4.6, 4.8} (8 giá trị) qua `target_margin` = biên tổng − `loan_spread_add`, `loan_spread_add` giữ 1.35.
- `base_deposit_rate_step` ∈ {0, 0.006, 0.012, 0.018} (4); `deposit_competition` ∈ {0.07, 0.3, 0.7, 1.2} (4).
- `deposit_ldr_target` ∈ {0.82, bình quân LDR ngân hàng-quý trong cửa sổ = 1.0899618858566973} (2).
- Kích thước: 6 × 8 × 4 × 4 × 2 = **1536** bộ (1536 lần chạy A). Các tham số khác giữ giá trị `scenarios_macro.yaml` (σ, ε, policy_pressure, policy_step KHÔNG hiệu chỉnh).

## 4. Biến thể, tiêu chí chọn, quy tắc hòa
- **Bản chính:** ngưỡng tiền gửi bất đối xứng qua `depositor_min_growth` (Q4b đã duyệt), dữ liệu đủ (không loại quan sát bất thường), có bù Q7 như mục 2.
- Biến thể phụ (chỉ báo cáo, không ghi vào YAML): (i) đối xứng `depositor_max_growth = max(|P2.5|,|P97.5|)`, không `depositor_min_growth`, đủ dữ liệu; (ii) bất đối xứng, loại ba quan sát bất thường (HDBank 2023Q2, MB Bank 2023Q4, MB Bank 2024Q4; xử lý như GD9). Với hai biến thể phụ, bù Q7 theo cùng quy tắc (cộng cùng Δ_D, Δ_L của mục 2). Tiêu chí chọn bản chính: áp dụng nguyên văn quy tắc LO_TRINH/D9 (bất đối xứng, đủ dữ liệu), chốt trước, không theo kết quả.
- Bộ chính ghi vào `configs/scenarios_calibrated.yaml` = argmin J của biến thể chính. Hòa (sai khác < 1e-12) lấy bộ đứng trước theo thứ tự lưới (λ, biên tổng, base_step, δ, ngưỡng LDR tăng dần; ngưỡng LDR: 0.82 trước).
- Nghiệm chạm cận dưới biên tổng 3.4 (hoặc biên khác của lưới, kể cả λ = 0.15/0.40): GIỮ nguyên nghiệm, ghi lại, KHÔNG mở rộng lưới (D9).
- Giữ bản cũ: trước khi ghi đè, sao `configs/scenarios_calibrated.yaml` hiện tại thành `configs/scenarios_calibrated_gd9.yaml` với comment đầu file nêu đây là bản GD9 giữ để đối chiếu; sau đó ghi đè `configs/scenarios_calibrated.yaml` bằng nghiệm GD9b, đủ khóa tường minh, comment nguồn từng giá trị.

## 5. Đầu ra sẽ báo (so GD9)
Tất cả sinh từ script vào `reports/calibration/stage9b/`:
1. Trong mẫu và ngoài mẫu: RMSE thô, RMSE khử mức, sai số trung bình, biên độ/đáy chữ V; so GĐ8 (`scenarios_macro.yaml`), mốc giữ 2025Q2, mốc ON (hệ số 0.45; nêu rõ mô hình và mốc ON cùng được cấp ON thực ngoài mẫu), và so GD9.
2. Top 10 bộ J nhỏ nhất; hồ sơ hàm mục tiêu theo từng tham số (J nhỏ nhất theo mỗi giá trị); tương quan trong top 50.
3. λ nghiệm có nằm trong CI GĐ7 [0.158; 0.395] không.
4. Tỷ lệ ngân hàng-quý chạm trần LDR 1.60 (kịch bản A) theo thời gian và khi khởi đầu từ 2026Q3 (so GD9: 0% đến month 10, 12.5% từ month 11, 37.5% từ month 16; khởi đầu 2026Q3 87.5%); tăng trưởng tổng mô hình so dữ liệu sau bù; tỷ lệ chạm ngưỡng chặn tăng trưởng.
5. Nhiễu lẫn tuân thủ (tổng quát hóa `src/calibration/confounding_stage9.py`, không đổi phương pháp): xác suất tuân thủ TB của B/C, `nim_proxy`, mức A sau chính sách, B−A, C−A, C−B, trung bình theo seed, quý 15–18, 10 seed, so GD9.
6. Mục 6 CLAUDE.md với A/B/C 10 lần chạy trên cấu hình mới. Vi phạm → DỪNG.
7. Chạy lại `src/analysis/kiem_dinh_ngoai_mau.py` với cấu hình mới và cập nhật `reports/stage11/` nếu thay đổi.

## 6. Phụ lục
Phụ lục chẩn đoán (nếu có) sẽ được thêm SAU khi chạy lưới chính, chỉ chẩn đoán, không đổi bộ chính.

## 7. Phụ lục chẩn đoán (THÊM SAU khi chạy lưới chính; chỉ chẩn đoán, không đổi bộ chính, không đổi mục 1–6 ở trên)
Sinh bởi `src/calibration/calibrate_stage9b.py` vào `reports/calibration/stage9b/` (xem `diagnostics_stage9b.csv`, `oos_stage9b.csv`, `boundary_stage9b.csv`):
- Bộ J nhỏ nhất với λ nằm trong CI GĐ7 [0.158; 0.395] (dòng `lambda_trong_CI_GD7_tot_nhat`), và đường đi ngoài mẫu của bộ này (`chan_doan_GD9b_lambda_trong_CI`).
- Đường đi của nghiệm GD9b nhưng KHÔNG bù Q7 (cộng ngược Δ; `chan_doan_GD9b_nghiem_khong_bu`), để tách tác động của bù tăng trưởng.
- Bảng chạm biên lưới của nghiệm chính (`boundary_stage9b.csv`).
- Đối với biến thể (i), (ii) ở mục 4: bù Δ_D, Δ_L cộng vào base_growth của chính Bước 1 của biến thể đó (biến thể (ii) có base riêng 0.0371/0.0438 từ Bước 1 GD9); mục 2 chỉ nêu "cộng cùng Δ", đây là cách hiểu đã áp dụng.
- (Vòng sửa 2, thêm SAU khi chạy lưới; chỉ chẩn đoán, không đổi mục 1–6, không đổi nghiệm, không chạy lại lưới) `src/calibration/diag_gd9b.py` → `diag_gd9b.csv`/`diag_gd9b.md`: (a) nghiệm GD9b bỏ bù Q7 (cộng ngược Δ) chỉ để chẩn đoán, không ghi YAML, so tỷ lệ chạm trần LDR, LDR max, tăng trưởng; (b) GD9 so GD9b về áp lực huy động (LDR đầu quý của A sau chính sách, tỷ lệ trên ngưỡng) và C−B lãi suất huy động, `nim_proxy`; (c) hai định nghĩa biên và khoảng cách tăng trưởng mô hình − dữ liệu.
