# Bước 8a: cơ sở lãi suất huy động `total` so với `term` (sinh tự động)

> 60 lần chạy mỗi kịch bản, seed = base_seed + run_id (cùng seed cho hai cơ sở), dữ liệu 8 ngân hàng thật, khởi tạo 2023Q1, 18 quý, chính sách từ bước 15 (Q4/2026). Mặc định của dự án vẫn là `total`; đổi sang `term` là quyết định của trưởng nhóm. RMSE là đối chiếu trong mẫu, không phải dự báo ngoài mẫu; chênh lệch A/B/C không phải tác động chính sách thực tế. Kịch bản A không dùng số ngẫu nhiên nên các lần chạy của A giống hệt nhau (sd RMSE = 0); số lần chạy chỉ có tác dụng với B và C (xác suất tuân thủ).

`deposit_rate_total_basis` gia quyền theo tiền gửi, cùng cơ sở với dữ liệu (chi phí lãi sổ sách trên tổng tiền gửi): ở `total` bằng chính `deposit_rate` của mô hình; ở `term` bằng `deposit_rate × (1 − casa)` (cột `deposit_rate` gốc ở `term` là lãi suất kỳ hạn nên cao hơn).

## Trạng thái khởi tạo

| basis | mean_funding_cost | mean_deposit_rate_model | learning_nim_threshold |
|---|---|---|---|
| total | 4.2188 | 5.0537 | 5.5875 |
| term | 5.2037 | 6.3498 | 4.6331 |

## Độ khớp với chuỗi thực 2023Q2–2026Q3 (kịch bản A; 14 quý; trước chính sách A = B = C)

| basis | bien | so_quy | RMSE_tb_cac_lan | RMSE_sd | RMSE_duong_trung_binh | MAE_tb | sai_so_trung_binh(mo_hinh-thuc) |
|---|---|---|---|---|---|---|---|
| total | loan_rate | 14 | 1.1776 | 0.0000 | 1.1776 | 1.0308 | 0.8790 |
| total | deposit_rate_total_basis | 14 | 1.7047 | 0.0000 | 1.7047 | 1.5611 | 1.5301 |
| term | loan_rate | 14 | 1.9681 | 0.0000 | 1.9681 | 1.7729 | 1.7532 |
| term | deposit_rate_total_basis | 14 | 1.6086 | 0.0000 | 1.6086 | 1.4655 | 1.4329 |

Lưu ý: `RMSE_sd` = 0 vì kịch bản A không dùng số ngẫu nhiên (các lần chạy giống hệt nhau), không phải do sai số được ước lượng chính xác. Hai cơ sở khởi tạo `deposit_rate` của mô hình ở mức khác nhau (`term` = dữ liệu/(1 − casa)); sau khi quy đổi về cơ sở dữ liệu, huy động của `term` xấp xỉ `total` (term nhỉnh hơn chút). Chênh lệch lớn nằm ở chi phí vốn và lãi suất cho vay, vì `total` trừ CASA hai lần ở `funding_cost`.

## Tác động chính sách (B−A, C−A; chênh theo cặp cùng seed, điểm %/năm)

| basis | thoi_diem | bien | so_sanh | tb | sd_giua_cac_lan_chay | min | max |
|---|---|---|---|---|---|---|---|
| term | cuoi_ky | loan_rate | B-A | -0.5058 | 0.0299 | -0.5360 | -0.3758 |
| term | cuoi_ky | loan_rate | C-A | -0.5548 | 0.0243 | -0.5793 | -0.4939 |
| term | cuoi_ky | deposit_rate_total_basis | B-A | 0.0013 | 0.0001 | 0.0009 | 0.0013 |
| term | cuoi_ky | deposit_rate_total_basis | C-A | -0.0755 | 0.0000 | -0.0756 | -0.0755 |
| term | tb_sau_chinh_sach | loan_rate | B-A | -0.4110 | 0.0199 | -0.4343 | -0.3529 |
| term | tb_sau_chinh_sach | loan_rate | C-A | -0.4329 | 0.0186 | -0.4538 | -0.3753 |
| term | tb_sau_chinh_sach | deposit_rate_total_basis | B-A | 0.0005 | 0.0000 | 0.0004 | 0.0005 |
| term | tb_sau_chinh_sach | deposit_rate_total_basis | C-A | -0.0482 | 0.0000 | -0.0483 | -0.0482 |
| total | cuoi_ky | loan_rate | B-A | -0.5033 | 0.0314 | -0.5336 | -0.3706 |
| total | cuoi_ky | loan_rate | C-A | -0.5574 | 0.0247 | -0.5818 | -0.4938 |
| total | cuoi_ky | deposit_rate_total_basis | B-A | 0.0014 | 0.0001 | 0.0009 | 0.0014 |
| total | cuoi_ky | deposit_rate_total_basis | C-A | -0.1070 | 0.0000 | -0.1071 | -0.1070 |
| total | tb_sau_chinh_sach | loan_rate | B-A | -0.4094 | 0.0206 | -0.4329 | -0.3515 |
| total | tb_sau_chinh_sach | loan_rate | C-A | -0.4336 | 0.0191 | -0.4547 | -0.3733 |
| total | tb_sau_chinh_sach | deposit_rate_total_basis | B-A | 0.0005 | 0.0000 | 0.0004 | 0.0006 |
| total | tb_sau_chinh_sach | deposit_rate_total_basis | C-A | -0.0678 | 0.0000 | -0.0679 | -0.0678 |

## Tuân thủ chỉ đạo (các quý có chính sách, theo ngân hàng-quý)

| basis | scenario | ty_le_tuan_thu_tb | ty_le_tuan_thu_sd | xac_suat_tuan_thu_tb |
|---|---|---|---|---|
| term | B | 0.9474 | 0.0352 | 0.9393 |
| term | C | 0.9521 | 0.0323 | 0.9409 |
| total | B | 0.9469 | 0.0356 | 0.9387 |
| total | C | 0.9521 | 0.0323 | 0.9407 |

## Kiểm tra hợp lý kinh tế (mục 6 CLAUDE.md)

| basis | chenh_lech_toi_da_A_B_C_truoc_chinh_sach | so_vi_pham_B_cao_hon_A_sau_chinh_sach | so_vi_pham_C_cao_hon_A_sau_chinh_sach | loan_rate_min | loan_rate_max | deposit_rate_min | deposit_rate_max | ldr_toi_da | so_quan_sat_chan_tran_huy_dong_14 |
|---|---|---|---|---|---|---|---|---|---|
| total | 0.000000 | 0 | 0 | 7.132463 | 12.020678 | 3.527209 | 6.883766 | 1.600000 | 0 |
| term | 0.000000 | 0 | 0 | 8.131275 | 12.405120 | 4.939109 | 7.435213 | 1.600000 | 0 |

## Chuỗi theo quý — cơ sở `total` (trung bình 60 lần chạy)

| month | quarter | actual_loan_rate | loan_rate_A | loan_rate_B | loan_rate_C | actual_deposit_rate | deposit_rate_total_basis_A | deposit_rate_total_basis_B | deposit_rate_total_basis_C | deposit_rate_model_basis_A |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2023Q2 | 9.692 | 9.095 | 9.095 | 9.095 | 5.036 | 4.819 | 4.819 | 4.819 | 4.819 |
| 2 | 2023Q3 | 9.289 | 8.841 | 8.841 | 8.841 | 4.622 | 4.873 | 4.873 | 4.873 | 4.873 |
| 3 | 2023Q4 | 8.735 | 8.718 | 8.718 | 8.718 | 3.922 | 4.929 | 4.929 | 4.929 | 4.929 |
| 4 | 2024Q1 | 7.850 | 8.664 | 8.664 | 8.664 | 3.246 | 4.986 | 4.986 | 4.986 | 4.986 |
| 5 | 2024Q2 | 7.511 | 8.645 | 8.645 | 8.645 | 2.962 | 5.043 | 5.043 | 5.043 | 5.043 |
| 6 | 2024Q3 | 7.220 | 8.645 | 8.645 | 8.645 | 3.011 | 5.102 | 5.102 | 5.102 | 5.102 |
| 7 | 2024Q4 | 7.286 | 8.656 | 8.656 | 8.656 | 3.023 | 5.160 | 5.160 | 5.160 | 5.160 |
| 8 | 2025Q1 | 6.972 | 8.676 | 8.676 | 8.676 | 3.138 | 5.218 | 5.218 | 5.218 | 5.218 |
| 9 | 2025Q2 | 6.985 | 8.715 | 8.715 | 8.715 | 3.202 | 5.274 | 5.274 | 5.274 | 5.274 |
| 10 | 2025Q3 | 7.071 | 8.758 | 8.758 | 8.758 | 3.230 | 5.330 | 5.330 | 5.330 | 5.330 |
| 11 | 2025Q4 | 7.338 | 8.801 | 8.801 | 8.801 | 3.239 | 5.386 | 5.386 | 5.386 | 5.386 |
| 12 | 2026Q1 | 7.510 | 8.845 | 8.845 | 8.845 | 3.620 | 5.440 | 5.440 | 5.440 | 5.440 |
| 13 | 2026Q2 | 8.328 | 8.889 | 8.889 | 8.889 | 4.239 | 5.493 | 5.493 | 5.493 | 5.493 |
| 14 | 2026Q3 | 8.785 | 8.932 | 8.932 | 8.932 | 4.687 | 5.546 | 5.546 | 5.546 | 5.546 |
| 15 | 2026Q4 |  | 8.975 | 8.709 | 8.709 |  | 5.597 | 5.597 | 5.570 | 5.597 |
| 16 | 2027Q1 |  | 9.017 | 8.619 | 8.606 |  | 5.648 | 5.648 | 5.593 | 5.648 |
| 17 | 2027Q2 |  | 9.059 | 8.588 | 8.558 |  | 5.697 | 5.698 | 5.616 | 5.697 |
| 18 | 2027Q3 |  | 9.100 | 8.597 | 8.542 |  | 5.746 | 5.747 | 5.639 | 5.746 |

## Chuỗi theo quý — cơ sở `term` (trung bình 60 lần chạy)

| month | quarter | actual_loan_rate | loan_rate_A | loan_rate_B | loan_rate_C | actual_deposit_rate | deposit_rate_total_basis_A | deposit_rate_total_basis_B | deposit_rate_total_basis_C | deposit_rate_model_basis_A |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2023Q2 | 9.692 | 9.554 | 9.554 | 9.554 | 5.036 | 4.808 | 4.808 | 4.808 | 6.060 |
| 2 | 2023Q3 | 9.289 | 9.540 | 9.540 | 9.540 | 4.622 | 4.851 | 4.851 | 4.851 | 6.109 |
| 3 | 2023Q4 | 8.735 | 9.543 | 9.543 | 9.543 | 3.922 | 4.894 | 4.894 | 4.894 | 6.159 |
| 4 | 2024Q1 | 7.850 | 9.556 | 9.556 | 9.556 | 3.246 | 4.938 | 4.938 | 4.938 | 6.210 |
| 5 | 2024Q2 | 7.511 | 9.573 | 9.573 | 9.573 | 2.962 | 4.982 | 4.982 | 4.982 | 6.261 |
| 6 | 2024Q3 | 7.220 | 9.592 | 9.592 | 9.592 | 3.011 | 5.026 | 5.026 | 5.026 | 6.312 |
| 7 | 2024Q4 | 7.286 | 9.613 | 9.613 | 9.613 | 3.023 | 5.070 | 5.070 | 5.070 | 6.364 |
| 8 | 2025Q1 | 6.972 | 9.635 | 9.635 | 9.635 | 3.138 | 5.114 | 5.114 | 5.114 | 6.415 |
| 9 | 2025Q2 | 6.985 | 9.657 | 9.657 | 9.657 | 3.202 | 5.157 | 5.157 | 5.157 | 6.465 |
| 10 | 2025Q3 | 7.071 | 9.695 | 9.695 | 9.695 | 3.230 | 5.199 | 5.199 | 5.199 | 6.515 |
| 11 | 2025Q4 | 7.338 | 9.733 | 9.733 | 9.733 | 3.239 | 5.240 | 5.240 | 5.240 | 6.563 |
| 12 | 2026Q1 | 7.510 | 9.771 | 9.771 | 9.771 | 3.620 | 5.281 | 5.281 | 5.281 | 6.610 |
| 13 | 2026Q2 | 8.328 | 9.809 | 9.809 | 9.809 | 4.239 | 5.320 | 5.320 | 5.320 | 6.657 |
| 14 | 2026Q3 | 8.785 | 9.846 | 9.846 | 9.846 | 4.687 | 5.359 | 5.359 | 5.359 | 6.702 |
| 15 | 2026Q4 |  | 9.882 | 9.616 | 9.616 |  | 5.396 | 5.396 | 5.376 | 6.746 |
| 16 | 2027Q1 |  | 9.917 | 9.518 | 9.507 |  | 5.432 | 5.433 | 5.393 | 6.789 |
| 17 | 2027Q2 |  | 9.952 | 9.480 | 9.452 |  | 5.468 | 5.468 | 5.410 | 6.831 |
| 18 | 2027Q3 |  | 9.986 | 9.480 | 9.431 |  | 5.502 | 5.503 | 5.426 | 6.871 |

File dữ liệu: quarterly_stage8a.csv, effects_stage8a.csv, compliance_stage8a.csv, fit_vs_actual_stage8a.csv, checks_stage8a.csv, initial_state_stage8a.csv, C_lai_suat_thuc_te_tu_panel.csv.
