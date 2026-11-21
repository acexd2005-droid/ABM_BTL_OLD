# GD10 – A/B/C, độ nhạy, độ vững (sinh tự động từ `reports/stage10/*.csv`)

Mọi số là kết quả MÔ HÌNH (chạy lại từ cấu hình + seed cố định); không phải dự báo, không phải tác động chính sách thực tế. B−A, C−A nhiễu lẫn với mức A và xác suất tuân thủ. Quý sau chính sách = 15–18 (Q4/2026–Q3/2027).

## 1. A/B/C, 60 lần, theo cấu hình (`abc_summary_stage10.csv`)

| Cấu hình | LS cho vay A | B | C | B−A TB | C−A TB | C−B TB | B−A cuối kỳ (Q3/2027) | C−A cuối kỳ | LS huy động A | B−A hh | tuân thủ B | tuân thủ C | nim A | nim B |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hieu_chinh_GD9b (chinh) | 7.9781 | 7.5847 | 7.5834 | -0.3933 | -0.3947 | -0.0014 | -0.5031 | -0.5061 | 5.6618 | 0.0006 | 0.8178 | 0.8178 | 3.376 | 2.982 |
| goc_scenarios | 9.9342 | 9.5232 | 9.5013 | -0.4110 | -0.4329 | -0.0219 | -0.5058 | -0.5548 | 6.8091 | 0.0006 | 0.9393 | 0.9409 | 4.489 | 4.075 |
| macro_GD8 | 9.3448 | 8.9270 | 8.9029 | -0.4178 | -0.4420 | -0.0242 | -0.5186 | -0.5696 | 5.8999 | 0.0005 | 0.9433 | 0.9452 | 4.558 | 4.140 |
| hieu_chinh_GD9 | 8.4903 | 8.0887 | 8.0752 | -0.4016 | -0.4151 | -0.0135 | -0.5018 | -0.5301 | 5.7696 | 0.0006 | 0.8768 | 0.8790 | 3.788 | 3.385 |

Phân bố qua seed của B−A (P5–P95, TB sau chính sách):

| Cấu hình | B−A P5 | B−A P95 | C−A P5 | C−A P95 | C−B CI95 nửa rộng | tỷ lệ seed B−A<0 |
|---|---:|---:|---:|---:|---:|---:|
| hieu_chinh_GD9b (chinh) | -0.4571 | -0.3361 | -0.4585 | -0.3375 | 0.00000 | 1.000 |
| goc_scenarios | -0.4343 | -0.3778 | -0.4538 | -0.4011 | 0.00168 | 1.000 |
| macro_GD8 | -0.4368 | -0.3876 | -0.4607 | -0.4115 | 0.00037 | 1.000 |
| hieu_chinh_GD9 | -0.4407 | -0.3598 | -0.4533 | -0.3725 | 0.00122 | 1.000 |

## 2. Độ nhạy, 30 lần mỗi biến thể (`sensitivity_stage10.csv`, `robustness_stage10.csv`)

| Biến thể | tham số | B−A TB | B−A cuối kỳ | tỷ số / chính | giữ dấu | giữ độ lớn | C−A TB | tỷ số / chính | giữ dấu | giữ độ lớn | C−B TB | C phân biệt B | tuân thủ B | A sau CS |
|---|---|---:|---:|---:|:--:|:--:|---:|---:|:--:|:--:|---:|:--:|---:|---:|
| co_so_30 | cấu hình chính, 30 lần (cùng seed 0..29) | -0.4004 | -0.5113 | 1.018 | có | có | -0.4018 | 1.018 | có | có | -0.0014 | KHÔNG | 0.8176 | 7.9781 |
| policy_pressure_x0.7 | policy_pressure = 0.4550 (×0.7) | -0.3639 | -0.4715 | 0.925 | có | có | -0.3649 | 0.925 | có | có | -0.0011 | KHÔNG | 0.7371 | 7.9781 |
| policy_pressure_x1.3 | policy_pressure = 0.8450 (×1.3) | -0.4262 | -0.5493 | 1.084 | có | có | -0.4275 | 1.083 | có | có | -0.0014 | KHÔNG | 0.8782 | 7.9781 |
| policy_step_0.14 | policy_step = 0.14 điểm %/năm (ánh xạ giả định ở báo cáo) | -0.2015 | -0.2587 | 0.512 | có | có | -0.2028 | 0.514 | có | có | -0.0013 | KHÔNG | 0.8305 | 7.9781 |
| policy_step_0.28 | policy_step = 0.28 điểm %/năm (= giá trị YAML) | -0.4004 | -0.5113 | 1.018 | có | có | -0.4018 | 1.018 | có | có | -0.0014 | KHÔNG | 0.8176 | 7.9781 |
| policy_step_0.42 | policy_step = 0.42 điểm %/năm (ánh xạ giả định ở báo cáo) | -0.5950 | -0.7537 | 1.513 | có | KHÔNG | -0.5969 | 1.512 | có | KHÔNG | -0.0019 | KHÔNG | 0.8038 | 7.9781 |
| policy_step_0.5 | policy_step = 0.5 điểm %/năm (ánh xạ giả định ở báo cáo) | -0.7001 | -0.8857 | 1.780 | có | KHÔNG | -0.7020 | 1.779 | có | KHÔNG | -0.0019 | KHÔNG | 0.7958 | 7.9781 |
| pass_through_0.158 | λ = 0.158 (CI_duoi) | -0.4886 | -0.7152 | 1.242 | có | có | -0.4866 | 1.233 | có | có | 0.0021 | KHÔNG | 0.7924 | 7.8339 |
| pass_through_0.35 | λ = 0.35 (trong_CI_Q9) | -0.4182 | -0.5504 | 1.063 | có | có | -0.4204 | 1.065 | có | có | -0.0022 | KHÔNG | 0.8095 | 7.9429 |
| pass_through_0.395 | λ = 0.395 (CI_tren) | -0.4022 | -0.5144 | 1.023 | có | có | -0.4035 | 1.022 | có | có | -0.0013 | KHÔNG | 0.8168 | 7.9749 |
| macro_dep_spread_1.08 | macro_dep_spread = 1.08 (mẫu N = 104, GĐ8) | -0.4004 | -0.5113 | 1.018 | có | có | -0.4026 | 1.020 | có | có | -0.0022 | KHÔNG | 0.8182 | 7.8425 |
| depositor_sensitivity_x0.5 | σ = 0.0175 (×0.5) | -0.4002 | -0.5105 | 1.018 | có | có | -0.4007 | 1.015 | có | có | -0.0005 | KHÔNG | 0.8175 | 7.9652 |
| depositor_sensitivity_x1.5 | σ = 0.0525 (×1.5) | -0.4004 | -0.5113 | 1.018 | có | có | -0.4027 | 1.020 | có | có | -0.0023 | KHÔNG | 0.8177 | 7.9898 |
| borrower_elasticity_x0.5 | ε = 0.0060 (×0.5) | -0.4006 | -0.5118 | 1.019 | có | có | -0.3971 | 1.006 | có | có | 0.0035 | KHÔNG | 0.8188 | 7.9686 |
| borrower_elasticity_x1.5 | ε = 0.0180 (×1.5) | -0.3989 | -0.5082 | 1.014 | có | có | -0.4055 | 1.028 | có | có | -0.0066 | KHÔNG | 0.8162 | 7.9954 |
| GD9_lambda_0.45 | nghiệm GD9 không ràng buộc λ (λ 0.45, biên tổng 3.8, chưa bù Q7) | -0.4047 | -0.5061 | 1.029 | có | có | -0.4191 | 1.062 | có | có | -0.0144 | KHÔNG | 0.8767 | 8.4903 |
| hoc_relative | learning_rule relative, θ 0.005, bước 0.05, simple; margin_min/max theo YAML (2.2–4.2) | -0.4075 | -0.5170 | 1.036 | có | có | -0.4078 | 1.033 | có | có | -0.0004 | KHÔNG | 0.8488 | 8.1643 |
| hoc_relative_cua_so_doi | như trên nhưng margin_min/max dời -1.15 để giữ ±1.0 quanh target_margin hiệu chỉnh | -0.4012 | -0.5147 | 1.020 | có | có | -0.4023 | 1.019 | có | có | -0.0011 | KHÔNG | 0.8046 | 7.9799 |
| GD9_hoc_relative | nghiệm GD9 + học relative (margin_min/max 2.2–4.2 vẫn bao quanh target_margin 2.45) | -0.4022 | -0.5021 | 1.023 | có | có | -0.4163 | 1.055 | có | có | -0.0141 | KHÔNG | 0.8733 | 8.4788 |
| hoc_relative_60 | như biến thể 30 lần tương ứng, 60 lần | -0.4008 | -0.5097 | 1.019 | có | có | -0.4013 | 1.017 | có | có | -0.0005 | KHÔNG | 0.8490 | 8.1643 |
| hoc_relative_cua_so_doi_60 | như biến thể 30 lần tương ứng, 60 lần | -0.3942 | -0.5062 | 1.002 | có | có | -0.3951 | 1.001 | có | có | -0.0009 | KHÔNG | 0.8047 | 7.9799 |

Giá trị chính (60 lần, GD9b): B−A = -0.3933, C−A = -0.3947, C−B = -0.0014.

## 3. Kết luận nào giữ được qua mọi biến thể (bảng tóm tắt)

| Kết luận | số biến thể giữ / tổng | biến thể KHÔNG giữ |
|---|---:|---|
| B−A < 0 (giữ dấu) | 20/20 | (không có) |
| C−A < 0 (giữ dấu) | 20/20 | (không có) |
| B−A cùng bậc độ lớn (tỷ số 0.5–1.5) | 18/20 | policy_step_0.42, policy_step_0.5 |
| C−A cùng bậc độ lớn (tỷ số 0.5–1.5) | 18/20 | policy_step_0.42, policy_step_0.5 |
| C−B khác 0 theo CI 95% ghép cặp | 17/20 | pass_through_0.158, pass_through_0.35, hoc_relative_60 |
| abs(C−B) >= 10% abs(B−A) (đáng kể) | 0/20 | tất cả |
| C phân biệt được với B (cả hai điều kiện trên) | 0/20 | tất cả |

Tổng gồm các biến thể độ nhạy (nền GD9b, 30 lần), học thích nghi 60 lần, nghiệm GD9, và 3 cấu hình so sánh (gốc, GĐ8, GD9; 60 lần). Không tính: co_so_30, policy_step_0.28 (trùng cấu hình chính), hai bản học 30 lần (đã có bản 60 lần).

Lưu ý: 20 KHÔNG phải số biến thể độc lập. Bảng chứa các bản gần trùng (hieu_chinh_GD9 60 lần và GD9_lambda_0.45 30 lần là cùng một cấu hình; hoc_relative, hoc_relative_60, hoc_relative_cua_so_doi, hoc_relative_cua_so_doi_60 và GD9_hoc_relative cùng nền học) và 3 cấu hình nền đổi nhiều tham số cùng lúc. Tỷ lệ x/n chỉ để tóm tắt bảng, không phải tần suất kiểm định. Hai biến thể policy_step >= 0.42 là biến thể duy nhất đổi độ lớn: độ lớn B−A, C−A lệ thuộc giả định policy_step.

C−B < 0 (C thấp hơn B) ở 18/20 biến thể; dương ở: pass_through_0.158, borrower_elasticity_x0.5.

## 4. Tuân thủ, nim_proxy và thí nghiệm tuân thủ cố định (`confounding_stage10.csv`)

| Cấu hình | loại | xs tuân thủ B | xs tuân thủ C | nim A | nim B | nim C | A sau CS | B−A | C−A | C−B |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hieu_chinh_GD9b (chinh) | tuan_thu_noi_sinh_60 | 0.8178 | 0.8178 | 3.376 | 2.982 | 2.985 | 7.9781 | -0.3933 | -0.3947 | -0.0014 |
| goc_scenarios | tuan_thu_noi_sinh_60 | 0.9393 | 0.9409 | 4.489 | 4.075 | 4.107 | 9.9342 | -0.4110 | -0.4329 | -0.0219 |
| macro_GD8 | tuan_thu_noi_sinh_60 | 0.9433 | 0.9452 | 4.558 | 4.140 | 4.175 | 9.3448 | -0.4178 | -0.4420 | -0.0242 |
| hieu_chinh_GD9 | tuan_thu_noi_sinh_60 | 0.8768 | 0.8790 | 3.788 | 3.385 | 3.406 | 8.4903 | -0.4016 | -0.4151 | -0.0135 |
| co_so_30 | tuan_thu_noi_sinh_30 | 0.8176 | 0.8176 | 3.376 | 2.975 | 2.977 | 7.9781 | -0.4004 | -0.4018 | -0.0014 |
| policy_pressure_x0.7 | tuan_thu_noi_sinh_30 | 0.7371 | 0.7371 | 3.376 | 3.011 | 3.014 | 7.9781 | -0.3639 | -0.3649 | -0.0011 |
| policy_pressure_x1.3 | tuan_thu_noi_sinh_30 | 0.8782 | 0.8782 | 3.376 | 2.949 | 2.952 | 7.9781 | -0.4262 | -0.4275 | -0.0014 |
| policy_step_0.14 | tuan_thu_noi_sinh_30 | 0.8305 | 0.8304 | 3.376 | 3.174 | 3.176 | 7.9781 | -0.2015 | -0.2028 | -0.0013 |
| policy_step_0.28 | tuan_thu_noi_sinh_30 | 0.8176 | 0.8176 | 3.376 | 2.975 | 2.977 | 7.9781 | -0.4004 | -0.4018 | -0.0014 |
| policy_step_0.42 | tuan_thu_noi_sinh_30 | 0.8038 | 0.8037 | 3.376 | 2.780 | 2.782 | 7.9781 | -0.5950 | -0.5969 | -0.0019 |
| policy_step_0.5 | tuan_thu_noi_sinh_30 | 0.7958 | 0.7957 | 3.376 | 2.675 | 2.677 | 7.9781 | -0.7001 | -0.7020 | -0.0019 |
| pass_through_0.158 | tuan_thu_noi_sinh_30 | 0.7924 | 0.7912 | 3.250 | 2.761 | 2.761 | 7.8339 | -0.4886 | -0.4866 | 0.0021 |
| pass_through_0.35 | tuan_thu_noi_sinh_30 | 0.8095 | 0.8093 | 3.343 | 2.924 | 2.925 | 7.9429 | -0.4182 | -0.4204 | -0.0022 |
| pass_through_0.395 | tuan_thu_noi_sinh_30 | 0.8168 | 0.8168 | 3.373 | 2.970 | 2.973 | 7.9749 | -0.4022 | -0.4035 | -0.0013 |
| macro_dep_spread_1.08 | tuan_thu_noi_sinh_30 | 0.8182 | 0.8184 | 3.379 | 2.978 | 2.982 | 7.8425 | -0.4004 | -0.4026 | -0.0022 |
| depositor_sensitivity_x0.5 | tuan_thu_noi_sinh_30 | 0.8175 | 0.8173 | 3.375 | 2.975 | 2.975 | 7.9652 | -0.4002 | -0.4007 | -0.0005 |
| depositor_sensitivity_x1.5 | tuan_thu_noi_sinh_30 | 0.8177 | 0.8178 | 3.376 | 2.975 | 2.980 | 7.9898 | -0.4004 | -0.4027 | -0.0023 |
| borrower_elasticity_x0.5 | tuan_thu_noi_sinh_30 | 0.8188 | 0.8175 | 3.384 | 2.983 | 2.977 | 7.9686 | -0.4006 | -0.3971 | 0.0035 |
| borrower_elasticity_x1.5 | tuan_thu_noi_sinh_30 | 0.8162 | 0.8176 | 3.366 | 2.965 | 2.978 | 7.9954 | -0.3989 | -0.4055 | -0.0066 |
| GD9_lambda_0.45 | tuan_thu_noi_sinh_30 | 0.8767 | 0.8789 | 3.788 | 3.381 | 3.401 | 8.4903 | -0.4047 | -0.4191 | -0.0144 |
| hoc_relative | tuan_thu_noi_sinh_30 | 0.8488 | 0.8486 | 3.566 | 3.158 | 3.159 | 8.1643 | -0.4075 | -0.4078 | -0.0004 |
| hoc_relative_cua_so_doi | tuan_thu_noi_sinh_30 | 0.8046 | 0.8047 | 3.372 | 2.971 | 2.974 | 7.9799 | -0.4012 | -0.4023 | -0.0011 |
| GD9_hoc_relative | tuan_thu_noi_sinh_30 | 0.8733 | 0.8756 | 3.773 | 3.369 | 3.390 | 8.4788 | -0.4022 | -0.4163 | -0.0141 |
| hoc_relative_60 | tuan_thu_noi_sinh_60 | 0.8490 | 0.8488 | 3.566 | 3.164 | 3.166 | 8.1643 | -0.4008 | -0.4013 | -0.0005 |
| hoc_relative_cua_so_doi_60 | tuan_thu_noi_sinh_60 | 0.8047 | 0.8048 | 3.372 | 2.978 | 2.981 | 7.9799 | -0.3942 | -0.3951 | -0.0009 |
| tuan_thu_co_dinh_hieu_chinh_GD9b (chinh) | tuan_thu_co_dinh | 0.8178 | 0.8178 | 3.376 | 2.975 | 2.978 | 7.9781 | -0.4003 | -0.4017 | -0.0014 |
| tuan_thu_co_dinh_goc_scenarios | tuan_thu_co_dinh | 0.8178 | 0.8178 | 4.489 | 4.117 | 4.151 | 9.9342 | -0.3695 | -0.3891 | -0.0195 |
| tuan_thu_co_dinh_macro_GD8 | tuan_thu_co_dinh | 0.8178 | 0.8178 | 4.558 | 4.187 | 4.222 | 9.3448 | -0.3709 | -0.3948 | -0.0239 |
| tuan_thu_co_dinh_hieu_chinh_GD9 | tuan_thu_co_dinh | 0.8178 | 0.8178 | 3.788 | 3.406 | 3.428 | 8.4903 | -0.3801 | -0.3927 | -0.0126 |

Tuân thủ cố định: xác suất tuân thủ ép = 0.817807 (xác suất TB của B, cấu hình chính 60 lần) ở mọi cấu hình; khác biệt B−A còn lại giữa các cấu hình chỉ do mức LS và biên, không do xác suất tuân thủ. Lưu ý: bản tuân thủ cố định chạy 30 lần còn bản nội sinh cùng bảng chạy 60 lần; sai khác do số lần chạy cỡ ~2% (≈0.008), nhỏ hơn mức chênh 0.02–0.05 giữa nội sinh và cố định nên kết luận đứng.

Tương quan giữa các biến thể (độ nhạy + cấu hình): corr(B−A, xs tuân thủ B) = 0.184; corr(B−A, nim_proxy A) = 0.116; corr(B−A, LS cho vay A) = 0.100 (n = 17, đã loại co_so_30 và policy_step_0.28 trùng cấu hình chính; các bản học còn trong mẫu và mang hiệu ứng mức); đây là mô tả, không phải nhân quả.

## 5. Mục 6 CLAUDE.md (`section6_stage10.csv`)

| Cấu hình | max(B−A) sau CS | max(C−A) sau CS | trước CS khác nhau | loan_rate [min; max] | deposit_rate [min; max] | max(loans − 1.6·deposits) | trễ (sai số trễ / hiện tại) | ĐẠT |
|---|---:|---:|---:|---|---|---:|---|:--:|
| hieu_chinh_GD9b (chinh) | -0.1495 | -0.1495 | 0.0e+00 | [6.491; 12.218] | [3.681; 6.974] | -9.96e+07 | 0.0e+00 / 0.0684 | ĐẠT |
| goc_scenarios | -0.1553 | -0.1551 | 0.0e+00 | [8.131; 12.405] | [4.939; 7.435] | 0 | 0.0e+00 / 0.0220 | ĐẠT |
| macro_GD8 | -0.1499 | -0.1499 | 0.0e+00 | [7.655; 12.405] | [3.819; 7.011] | -9.52e+05 | 0.0e+00 / 0.0796 | ĐẠT |
| hieu_chinh_GD9 | -0.1529 | -0.1528 | 0.0e+00 | [6.847; 12.170] | [3.695; 6.974] | 0 | 0.0e+00 / 0.0769 | ĐẠT |
| co_so_30 | -0.1495 | -0.1495 | 0.0e+00 | [6.491; 12.218] | [3.681; 6.974] | -9.96e+07 | 0.0e+00 / 0.0684 | ĐẠT |
| policy_pressure_x0.7 | -0.1495 | -0.1495 | 0.0e+00 | [6.491; 12.218] | [3.681; 6.974] | -9.96e+07 | 0.0e+00 / 0.0684 | ĐẠT |
| policy_pressure_x1.3 | -0.1495 | -0.1495 | 0.0e+00 | [6.491; 12.218] | [3.681; 6.974] | -9.96e+07 | 0.0e+00 / 0.0684 | ĐẠT |
| policy_step_0.14 | -0.0747 | -0.0747 | 0.0e+00 | [6.491; 12.218] | [3.681; 6.974] | -9.96e+07 | 0.0e+00 / 0.0684 | ĐẠT |
| policy_step_0.28 | -0.1495 | -0.1495 | 0.0e+00 | [6.491; 12.218] | [3.681; 6.974] | -9.96e+07 | 0.0e+00 / 0.0684 | ĐẠT |
| policy_step_0.42 | -0.2244 | -0.2244 | 0.0e+00 | [6.428; 12.218] | [3.681; 6.974] | -9.96e+07 | 0.0e+00 / 0.0684 | ĐẠT |
| policy_step_0.5 | -0.2672 | -0.2672 | 0.0e+00 | [6.254; 12.218] | [3.681; 6.974] | -9.96e+07 | 0.0e+00 / 0.0684 | ĐẠT |
| pass_through_0.158 | -0.1444 | -0.1444 | 0.0e+00 | [6.466; 13.321] | [3.679; 6.974] | -9.96e+07 | 0.0e+00 / 0.0270 | ĐẠT |
| pass_through_0.35 | -0.1489 | -0.1489 | 0.0e+00 | [6.555; 12.446] | [3.681; 6.974] | -9.96e+07 | 0.0e+00 / 0.0598 | ĐẠT |
| pass_through_0.395 | -0.1494 | -0.1494 | 0.0e+00 | [6.496; 12.241] | [3.681; 6.974] | -9.96e+07 | 0.0e+00 / 0.0675 | ĐẠT |
| macro_dep_spread_1.08 | -0.1495 | -0.1495 | 0.0e+00 | [6.414; 12.218] | [3.562; 6.940] | -9.89e+07 | 0.0e+00 / 0.0810 | ĐẠT |
| depositor_sensitivity_x0.5 | -0.1494 | -0.1494 | 0.0e+00 | [6.482; 12.218] | [3.667; 6.974] | -9.59e+07 | 0.0e+00 / 0.0684 | ĐẠT |
| depositor_sensitivity_x1.5 | -0.1496 | -0.1496 | 0.0e+00 | [6.498; 12.218] | [3.693; 6.974] | -1.03e+08 | 0.0e+00 / 0.0684 | ĐẠT |
| borrower_elasticity_x0.5 | -0.1522 | -0.1522 | 0.0e+00 | [6.486; 12.218] | [3.674; 6.974] | -9.41e+07 | 0.0e+00 / 0.0684 | ĐẠT |
| borrower_elasticity_x1.5 | -0.1471 | -0.1471 | 0.0e+00 | [6.496; 12.218] | [3.688; 6.974] | 0 | 0.0e+00 / 0.0684 | ĐẠT |
| GD9_lambda_0.45 | -0.1529 | -0.1528 | 0.0e+00 | [6.847; 12.170] | [3.695; 6.974] | 0 | 0.0e+00 / 0.0769 | ĐẠT |
| hoc_relative | -0.1491 | -0.1491 | 0.0e+00 | [6.634; 12.218] | [3.681; 6.974] | -9.96e+07 | 0.0e+00 / 0.0684 | ĐẠT |
| hoc_relative_cua_so_doi | -0.1499 | -0.1499 | 0.0e+00 | [6.491; 12.218] | [3.681; 6.974] | -9.96e+07 | 0.0e+00 / 0.0684 | ĐẠT |
| GD9_hoc_relative | -0.1531 | -0.1530 | 0.0e+00 | [6.847; 12.170] | [3.695; 6.974] | 0 | 0.0e+00 / 0.0769 | ĐẠT |

