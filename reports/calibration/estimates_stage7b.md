# Giai đoạn 7b: ước lượng phương trình lãi suất huy động (sinh tự động)

> Không sửa mô hình, không sửa `configs/`. Ước lượng trong mẫu, chỉ để đối chiếu; không phải tác động chính sách thực tế.

## Quy tắc hiện tại và dạng ước lượng

`Bank.step` (src/agents/bank.py): `Δr^D_t = base_deposit_rate_step + deposit_competition · clip(LDR − 0.82, ±0.5)` với `base_deposit_rate_step = 0.018` (điểm %/quý), `deposit_competition = 0.07`. `LDR = loans/deposits` đo **đầu quý t** (= cuối quý t−1, vì ngân hàng chạy trước khối người gửi/người vay trong `step()`), nên trong panel dùng `LDR_{t-1}`. Cơ sở `term`: `r^D = deposit_rate_pct/(1−casa)`. Kịch bản C nhân thêm `deposit_cap_factor` sau chính sách (ngoài mẫu).

- **PT5:** `Δr^D_t = a + δ·LDR_{t-1}`; mô hình ngụ ý `a = 0.018 − 0.07·0.82 = −0.0394`, `δ = 0.07`; `base_step_implied = a + 0.82δ` so với 0.018.
- **PT5z:** như PT5 nhưng dùng đúng biến `clip(LDR_{t-1} − 0.82, ±0.5)` (11/112 quan sát LDR_{t-1} nằm ngoài miền tuyến tính [0.32; 1.32]); khi đó hằng số = `base_step` trực tiếp.
- **PT5-ON:** `Δr^D_t = α_i + δ·LDR_{t-1} + φ·(ON_{t-k} − r^D_{t-1})`, k = 1, 2, 3, FE ngân hàng; φ = tốc độ điều chỉnh về phía lãi suất qua đêm bình quân đơn giản của quý; cân bằng ngụ ý `r* − ON = Δr̄/φ + trung bình(r^D_{t-1} − ON_{t-k})`. Ở biến thể (c) ON bị FE quý hấp thụ nên φ = −hệ số của `r^D_{t-1}`.
- Biến thể: (a) OLS gộp; (b) FE ngân hàng; (c) FE ngân hàng + quý; (d) FE ngân hàng + số hạng ON. SE cụm CR1 theo ngân hàng, **8 cụm** (t với 7 bậc tự do, 2.3646).
- Mẫu: N = 112 (k = 1), 104 (k = 2), 96 (k = 3); mẫu chung nhỏ nhất N = 96 để so sánh các độ trễ.
- Hạn chế cũ vẫn áp dụng (Giai đoạn 7): SE cụm theo ngân hàng không xử lý cú sốc chung theo quý nên t/CI của (a), (b), (d) bị đánh giá quá hẹp; thiên lệch Nickell với T = 14 cho hệ số của biến trễ r^D_{t-1} (φ ở (d) bị lệch lên); cột `se_cluster` của hằng số FE là độ phân tán giữa ngân hàng, không phải SE chuẩn; lợi suất sổ sách.

### PT5, mẫu N112

| parameter | bien_the | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | se_ols | r2 | n | yaml_value |
|---|---|---|---|---|---|---|---|---|---|---|
| delta | a | 1.0971 | 0.3669 | 2.9901 | 0.2295 | 1.9647 | 0.3563 | 0.0794 | 112 | 0.0700 |
| a_const | a | -1.2254 | 0.3868 | -3.1681 | -2.1399 | -0.3108 | 0.4015 | 0.0794 | 112 | -0.0394 |
| base_step_implied | a | -0.3258 | 0.0957 | -3.4053 | -0.5520 | -0.0996 |  | 0.0794 | 112 | 0.0180 |
| delta | b | 5.2894 | 0.6276 | 8.4281 | 3.8054 | 6.7734 | 0.6577 | 0.3858 | 112 | 0.0700 |
| a_const | b | -5.9102 | 0.2575 | -22.9536 | -6.5190 | -5.3013 |  | 0.3858 | 112 | -0.0394 |
| base_step_implied | b | -1.5729 | 0.5754 | -2.7333 | -2.9336 | -0.2122 |  | 0.3858 | 112 | 0.0180 |
| delta | c | 1.1872 | 0.3077 | 3.8583 | 0.4596 | 1.9148 | 0.5744 | 0.0453 | 112 | 0.0700 |

### PT5z (biến đã chặn), mẫu N112

| parameter | bien_the | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | se_ols | r2 | n | yaml_value |
|---|---|---|---|---|---|---|---|---|---|---|
| delta | a | 1.2395 | 0.4722 | 2.6252 | 0.1230 | 2.3559 | 0.4254 | 0.0717 | 112 | 0.0700 |
| base_step_implied | a | -0.3555 | 0.1252 | -2.8392 | -0.6516 | -0.0594 | 0.1327 | 0.0717 | 112 | 0.0180 |
| delta | b | 6.2512 | 0.9055 | 6.9034 | 4.1100 | 8.3924 | 0.8122 | 0.3652 | 112 | 0.0700 |
| base_step_implied | b | -1.7954 | 0.2575 | -6.9731 | -2.4043 | -1.1866 |  | 0.3652 | 112 | 0.0180 |
| delta | c | 1.1750 | 0.4999 | 2.3504 | -0.0071 | 2.3571 | 0.6718 | 0.0329 | 112 | 0.0700 |

### PT5-ON, mẫu N112

| parameter | bien_the | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | se_ols | r2 | n | yaml_value |
|---|---|---|---|---|---|---|---|---|---|---|
| delta | c | 1.3016 | 0.3269 | 3.9813 | 0.5285 | 2.0746 | 0.5119 | 0.2517 | 112 | 0.0700 |
| phi | c | 0.4013 | 0.0530 | 7.5758 | 0.2760 | 0.5265 | 0.0810 | 0.2517 | 112 |  |
| delta | d(k=1) | 2.0139 | 0.3141 | 6.4106 | 1.2710 | 2.7567 | 0.5748 | 0.6881 | 112 | 0.0700 |
| phi | d(k=1) | 0.1771 | 0.0085 | 20.8156 | 0.1570 | 0.1973 | 0.0178 | 0.6881 | 112 |  |
| alpha_mean | d(k=1) | -2.0251 | 0.0949 | -21.3368 | -2.2495 | -1.8006 |  | 0.6881 | 112 |  |
| speed_per_quarter | d(k=1) | 0.1771 | 0.0085 | 20.8156 | 0.1570 | 0.1973 | 0.0178 | 0.6881 | 112 |  |
| half_life_quarters | d(k=1) | 3.5550 |  |  |  |  |  | 0.6881 | 112 |  |
| spread_actual_mean | d(k=1) | 1.2689 |  |  |  |  |  | 0.6881 | 112 |  |
| spread_equilibrium | d(k=1) | 1.2723 |  |  |  |  |  | 0.6881 | 112 |  |

### PT5, mẫu N104

| parameter | bien_the | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | se_ols | r2 | n | yaml_value |
|---|---|---|---|---|---|---|---|---|---|---|
| delta | a | 1.1617 | 0.4062 | 2.8596 | 0.2011 | 2.1223 | 0.3709 | 0.0877 | 104 | 0.0700 |
| a_const | a | -1.3294 | 0.4299 | -3.0922 | -2.3459 | -0.3128 | 0.4184 | 0.0877 | 104 | -0.0394 |
| base_step_implied | a | -0.3768 | 0.1060 | -3.5548 | -0.6274 | -0.1262 |  | 0.0877 | 104 | 0.0180 |
| delta | b | 5.7083 | 0.8070 | 7.0733 | 3.8000 | 7.6166 | 0.6885 | 0.4198 | 104 | 0.0700 |
| a_const | b | -6.4152 | 0.2779 | -23.0880 | -7.0722 | -5.7582 |  | 0.4198 | 104 | -0.0394 |
| base_step_implied | b | -1.7344 | 0.7177 | -2.4165 | -3.4315 | -0.0372 |  | 0.4198 | 104 | 0.0180 |
| delta | c | 0.5112 | 0.2893 | 1.7669 | -0.1729 | 1.1954 | 0.6733 | 0.0069 | 104 | 0.0700 |

### PT5z (biến đã chặn), mẫu N104

| parameter | bien_the | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | se_ols | r2 | n | yaml_value |
|---|---|---|---|---|---|---|---|---|---|---|
| delta | a | 1.3179 | 0.5216 | 2.5268 | 0.0846 | 2.5512 | 0.4437 | 0.0796 | 104 | 0.0700 |
| base_step_implied | a | -0.4100 | 0.1398 | -2.9324 | -0.7406 | -0.0794 | 0.1389 | 0.0796 | 104 | 0.0180 |
| delta | b | 7.1124 | 0.9151 | 7.7723 | 4.9485 | 9.2762 | 0.8692 | 0.4134 | 104 | 0.0700 |
| base_step_implied | b | -2.0812 | 0.2937 | -7.0854 | -2.7757 | -1.3866 |  | 0.4134 | 104 | 0.0180 |
| delta | c | 0.1286 | 0.3193 | 0.4028 | -0.6264 | 0.8836 | 0.8381 | 0.0003 | 104 | 0.0700 |

### PT5-ON, mẫu N104

| parameter | bien_the | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | se_ols | r2 | n | yaml_value |
|---|---|---|---|---|---|---|---|---|---|---|
| delta | c | 0.8056 | 0.4025 | 2.0016 | -0.1461 | 1.7573 | 0.6082 | 0.2084 | 104 | 0.0700 |
| phi | c | 0.3930 | 0.0677 | 5.8077 | 0.2330 | 0.5529 | 0.0860 | 0.2084 | 104 |  |
| delta | d(k=1) | 1.9767 | 0.6430 | 3.0743 | 0.4563 | 3.4971 | 0.5926 | 0.7304 | 104 | 0.0700 |
| phi | d(k=1) | 0.1797 | 0.0149 | 12.0805 | 0.1445 | 0.2149 | 0.0173 | 0.7304 | 104 |  |
| alpha_mean | d(k=1) | -2.0167 | 0.0918 | -21.9763 | -2.2337 | -1.7997 |  | 0.7304 | 104 |  |
| speed_per_quarter | d(k=1) | 0.1797 | 0.0149 | 12.0805 | 0.1445 | 0.2149 | 0.0173 | 0.7304 | 104 |  |
| half_life_quarters | d(k=1) | 3.4989 |  |  |  |  |  | 0.7304 | 104 |  |
| spread_actual_mean | d(k=1) | 1.2486 |  |  |  |  |  | 0.7304 | 104 |  |
| spread_equilibrium | d(k=1) | 1.0821 |  |  |  |  |  | 0.7304 | 104 |  |
| delta | d(k=2) | 2.8521 | 0.6752 | 4.2244 | 1.2556 | 4.4486 | 0.6200 | 0.6716 | 104 | 0.0700 |
| phi | d(k=2) | 0.1923 | 0.0255 | 7.5470 | 0.1320 | 0.2525 | 0.0226 | 0.6716 | 104 |  |
| alpha_mean | d(k=2) | -2.9661 | 0.1330 | -22.3083 | -3.2805 | -2.6517 |  | 0.6716 | 104 |  |
| speed_per_quarter | d(k=2) | 0.1923 | 0.0255 | 7.5470 | 0.1320 | 0.2525 | 0.0226 | 0.6716 | 104 |  |
| half_life_quarters | d(k=2) | 3.2464 |  |  |  |  |  | 0.6716 | 104 |  |
| spread_actual_mean | d(k=2) | 1.3216 |  |  |  |  |  | 0.6716 | 104 |  |
| spread_equilibrium | d(k=2) | 1.1661 |  |  |  |  |  | 0.6716 | 104 |  |

### PT5, mẫu N96

| parameter | bien_the | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | se_ols | r2 | n | yaml_value |
|---|---|---|---|---|---|---|---|---|---|---|
| delta | a | 1.2271 | 0.4535 | 2.7055 | 0.1546 | 2.2995 | 0.3773 | 0.1011 | 96 | 0.0700 |
| a_const | a | -1.3691 | 0.4696 | -2.9154 | -2.4795 | -0.2587 | 0.4274 | 0.1011 | 96 | -0.0394 |
| base_step_implied | a | -0.3629 | 0.1040 | -3.4897 | -0.6088 | -0.1170 |  | 0.1011 | 96 | 0.0180 |
| delta | b | 5.7954 | 0.7656 | 7.5699 | 3.9851 | 7.6057 | 0.7053 | 0.4370 | 96 | 0.0700 |
| a_const | b | -6.5014 | 0.2801 | -23.2108 | -7.1637 | -5.8390 |  | 0.4370 | 96 | -0.0394 |
| base_step_implied | b | -1.7491 | 0.6874 | -2.5444 | -3.3746 | -0.1236 |  | 0.4370 | 96 | 0.0180 |
| delta | c | 0.7872 | 0.4107 | 1.9167 | -0.1840 | 1.7583 | 0.6252 | 0.0204 | 96 | 0.0700 |

### PT5z (biến đã chặn), mẫu N96

| parameter | bien_the | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | se_ols | r2 | n | yaml_value |
|---|---|---|---|---|---|---|---|---|---|---|
| delta | a | 1.4504 | 0.5611 | 2.5848 | 0.1236 | 2.7771 | 0.4557 | 0.0973 | 96 | 0.0700 |
| base_step_implied | a | -0.4146 | 0.1383 | -2.9975 | -0.7417 | -0.0876 | 0.1442 | 0.0973 | 96 | 0.0180 |
| delta | b | 7.1444 | 1.0315 | 6.9264 | 4.7054 | 9.5835 | 0.9001 | 0.4200 | 96 | 0.0700 |
| base_step_implied | b | -2.0797 | 0.2868 | -7.2512 | -2.7578 | -1.4015 |  | 0.4200 | 96 | 0.0180 |
| delta | c | 0.2581 | 0.2663 | 0.9693 | -0.3715 | 0.8877 | 0.7798 | 0.0014 | 96 | 0.0700 |

### PT5-ON, mẫu N96

| parameter | bien_the | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | se_ols | r2 | n | yaml_value |
|---|---|---|---|---|---|---|---|---|---|---|
| delta | c | 1.1018 | 0.4664 | 2.3625 | -0.0010 | 2.2046 | 0.5177 | 0.3438 | 96 | 0.0700 |
| phi | c | 0.4452 | 0.0672 | 6.6260 | 0.2863 | 0.6041 | 0.0732 | 0.3438 | 96 |  |
| delta | d(k=1) | 2.1738 | 0.6111 | 3.5573 | 0.7288 | 3.6187 | 0.5723 | 0.7602 | 96 | 0.0700 |
| phi | d(k=1) | 0.1764 | 0.0196 | 9.0146 | 0.1302 | 0.2227 | 0.0164 | 0.7602 | 96 |  |
| alpha_mean | d(k=1) | -2.2407 | 0.0961 | -23.3044 | -2.4680 | -2.0133 |  | 0.7602 | 96 |  |
| speed_per_quarter | d(k=1) | 0.1764 | 0.0196 | 9.0146 | 0.1302 | 0.2227 | 0.0164 | 0.7602 | 96 |  |
| half_life_quarters | d(k=1) | 3.5708 |  |  |  |  |  | 0.7602 | 96 |  |
| spread_actual_mean | d(k=1) | 1.0881 |  |  |  |  |  | 0.7602 | 96 |  |
| spread_equilibrium | d(k=1) | 1.1417 |  |  |  |  |  | 0.7602 | 96 |  |
| delta | d(k=2) | 2.8021 | 0.5668 | 4.9434 | 1.4617 | 4.1424 | 0.6104 | 0.7083 | 96 | 0.0700 |
| phi | d(k=2) | 0.1907 | 0.0271 | 7.0280 | 0.1265 | 0.2549 | 0.0213 | 0.7083 | 96 |  |
| alpha_mean | d(k=2) | -2.8961 | 0.1262 | -22.9515 | -3.1945 | -2.5977 |  | 0.7083 | 96 |  |
| speed_per_quarter | d(k=2) | 0.1907 | 0.0271 | 7.0280 | 0.1265 | 0.2549 | 0.0213 | 0.7083 | 96 |  |
| half_life_quarters | d(k=2) | 3.2756 |  |  |  |  |  | 0.7083 | 96 |  |
| spread_actual_mean | d(k=2) | 1.2709 |  |  |  |  |  | 0.7083 | 96 |  |
| spread_equilibrium | d(k=2) | 1.3206 |  |  |  |  |  | 0.7083 | 96 |  |
| delta | d(k=3) | 5.3143 | 0.7197 | 7.3845 | 3.6126 | 7.0160 | 0.7532 | 0.4552 | 96 | 0.0700 |
| phi | d(k=3) | 0.0578 | 0.0332 | 1.7388 | -0.0208 | 0.1364 | 0.0341 | 0.4552 | 96 |  |
| alpha_mean | d(k=3) | -5.8826 | 0.2535 | -23.2086 | -6.4820 | -5.2833 |  | 0.4552 | 96 |  |
| speed_per_quarter | d(k=3) | 0.0578 | 0.0332 | 1.7388 | -0.0208 | 0.1364 | 0.0341 | 0.4552 | 96 |  |
| half_life_quarters | d(k=3) | 11.6421 |  |  |  |  |  | 0.4552 | 96 |  |
| spread_actual_mean | d(k=3) | 1.3538 |  |  |  |  |  | 0.4552 | 96 |  |
| spread_equilibrium | d(k=3) | 1.5176 |  |  |  |  |  | 0.4552 | 96 |  |

## Trôi bình quân: dữ liệu so với quy tắc hiện hành

`base_step_implied` ở LDR = 0.82 là ngoại suy ra ngoài miền dữ liệu (LDR_{t-1} quan sát được từ khoảng 0.85, trung bình khoảng 1.1), nên so sánh thực chất là trôi bình quân tại LDR thực:

| mau | dr_D_tb_thuc | dr_D_sd_thuc | LDR_lag_tb | LDR_lag_min | LDR_lag_max | dr_D_ngu_y_quy_tac_hien_hanh_tai_LDR_thuc |
|---|---|---|---|---|---|---|
| N112 | 0.0006 | 0.5653 | 1.1175 | 0.8537 | 1.5847 | 0.0381 |

## FE quý hấp thụ bao nhiêu, ON thay thế bao nhiêu

Cách đọc giống Giai đoạn 7: `share_*` là tỷ lệ phương sai within-ngân-hàng của Δr^D được giải thích; `ratio_ON_vs_quarterFE` = (share_LDR_ON − share_LDR) / (share_LDR_bank_quarter_FE − share_LDR); `ratio_adj_df` đã hiệu chỉnh bậc tự do; `R2_common_on_ON` là R² trên **13-14 điểm theo quý** (thành phần chung theo quý hồi quy lên trung bình các ngân hàng của ON_{t-k} − r^D_{t-1}), `approx_share_explained_by_ON_via_common` = R2_common × share_quarter_FE_only.

| lag_on | sample | n | share_LDR_bank_FE | share_quarter_FE_only | share_LDR_bank_quarter_FE | share_LDR_ON_bank_FE | ratio_ON_vs_quarterFE | ratio_adj_df | R2_common_on_ON | approx_share_explained_by_ON_via_common |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | N112 | 112 | 0.3858 | 0.8094 | 0.8180 | 0.6881 | 0.6994 | 0.7371 | 0.7671 | 0.6209 |
| 1 | N104 | 104 | 0.4198 | 0.8174 | 0.8186 | 0.7304 | 0.7788 | 0.8259 | 0.8201 | 0.6703 |
| 1 | N96 | 96 | 0.4370 | 0.8490 | 0.8521 | 0.7602 | 0.7786 | 0.8139 | 0.8079 | 0.6859 |
| 2 | N104 | 104 | 0.4198 | 0.8174 | 0.8186 | 0.6716 | 0.6313 | 0.6664 | 0.6937 | 0.5670 |
| 2 | N96 | 96 | 0.4370 | 0.8490 | 0.8521 | 0.7083 | 0.6537 | 0.6806 | 0.7064 | 0.5997 |
| 3 | N96 | 96 | 0.4370 | 0.8490 | 0.8521 | 0.4552 | 0.0439 | 0.0302 | 0.1348 | 0.1144 |

## Độ trễ tốt nhất và wild-cluster bootstrap cho φ

Tiêu chí chọn (đặt trước): độ trễ có phần phương sai within giải thích lớn nhất trên mẫu chung N = 96. Kết quả: k = 1: 0.7602, k = 2: 0.7083, k = 3: 0.4552 ⇒ **k = 1**. Bootstrap WCR-t, trọng số Webb 6 điểm, B = 9999, seed = 20261121; vẫn chỉ 8 cụm, ON là biến chung theo quý nên thông tin hiệu dụng của φ cỡ 13-14 điểm.

| lag_on | sample | coef | se_cr1 | t_cr1 | ci_cr1_lo | ci_cr1_hi | p_boot | ci_boot_lo | ci_boot_hi |
|---|---|---|---|---|---|---|---|---|---|
| 1 | N96 | 0.1764 | 0.0196 | 9.0146 | 0.1302 | 0.2227 | 0.0025 | 0.1465 | 0.2282 |
| 1 | tu_nhien_N112 | 0.1771 | 0.0085 | 20.8156 | 0.1570 | 0.1973 | 0.0000 | 0.1561 | 0.1961 |

## Mô phỏng offline (không đưa vào mô hình; trong mẫu)

Bắt đầu từ t = 4 (2023Q4), khởi tạo bằng dữ liệu thực của quý đó (r^D_term, r^L theo từng ngân hàng, casa cố định như mô hình), chạy tới 2026Q3 (t = 15, 11 quý so sánh). LDR thực (trễ 1 quý) và ON thực là biến ngoại sinh. Chi phí vốn `c = r^D_term(1−casa)+0.15`; lãi suất cho vay theo PT1 hiện hành `r^L_t = r^L_{t-1} + λ(c_{t-1} + 4.55 − r^L_{t-1})` với λ = GĐ7 biến thể (c) hoặc 0.48 (YAML); trọng số = dư nợ thực. Hàng đầu là chuỗi thực. Thang đo: lãi suất cho vay %/năm; RMSE trên 11 quý t = 5..15; chỉ số chữ V tính trên t ≥ 4. Hàng "huy động thực" dùng lãi suất huy động thực trong PT1, tức giới hạn trên của những gì chi phí vốn giải thích được. `RMSE_khu_muc` = độ lệch chuẩn của sai số (RMSE sau khi bỏ sai số trung bình) để so hình dạng chuỗi tách khỏi chênh lệch mức. Cột `deposit_rate_total_basis` trong simulation_paths_stage7b.csv dùng casa cố định ở quý T0 như mô hình nên không so trực tiếp với chuỗi huy động thực.

| lambda_set | chuoi | RMSE | RMSE_khu_muc | MAE | sai_so_tb | tuong_quan | tho_thap_nhat | quy_thap_nhat_t | giam_tu_dau_den_day | hoi_phuc_tu_day_den_cuoi |
|---|---|---|---|---|---|---|---|---|---|---|
| - | THỰC (cho vay) | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 6.9720 | 9 | 1.7627 | 1.8134 |
| lambda_GD7_c | huy động thực (chỉ PT1) | 0.8263 | 0.4981 | 0.7785 | 0.6593 | 0.4249 | 7.9739 | 11 | 0.7538 | 0.3808 |
| lambda_GD7_c | quy tắc huy động hiện hành | 1.3497 | 0.5028 | 1.2526 | 1.2526 | 0.7191 | 8.7082 | 7 | 0.0196 | 0.2126 |
| lambda_GD7_c | PT5 ước lượng (FE ngân hàng, không ON) | 1.0628 | 0.5187 | 0.9721 | 0.9276 | 0.3467 | 8.2866 | 12 | 0.4411 | 0.2540 |
| lambda_GD7_c | PT5-ON ước lượng (k = 1) | 0.9186 | 0.4343 | 0.8456 | 0.8095 | 0.7155 | 8.1568 | 10 | 0.5709 | 0.4300 |
| lambda_YAML_0.48 | huy động thực (chỉ PT1) | 0.6840 | 0.3813 | 0.6374 | 0.5679 | 0.7536 | 7.8235 | 9 | 0.8822 | 0.7453 |
| lambda_YAML_0.48 | quy tắc huy động hiện hành | 1.3521 | 0.4965 | 1.2576 | 1.2576 | 0.6613 | 8.6894 | 6 | 0.0163 | 0.2647 |
| lambda_YAML_0.48 | PT5 ước lượng (FE ngân hàng, không ON) | 0.9811 | 0.4478 | 0.8965 | 0.8729 | 0.7038 | 8.1992 | 11 | 0.5065 | 0.4565 |
| lambda_YAML_0.48 | PT5-ON ước lượng (k = 1) | 0.8239 | 0.3341 | 0.7551 | 0.7531 | 0.8898 | 7.9793 | 8 | 0.7264 | 0.7949 |


### Biên thực r^L − c_{t-1} theo quý (gia quyền theo dư nợ) so với 4.55 giả định

| t | quy | bien_thuc_rL_tru_c_lag | bien_gia_dinh_mo_hinh |
|---|---|---|---|
| 2 | 2023Q2 | 4.711 | 4.550 |
| 3 | 2023Q3 | 4.063 | 4.550 |
| 4 | 2023Q4 | 3.943 | 4.550 |
| 5 | 2024Q1 | 3.750 | 4.550 |
| 6 | 2024Q2 | 4.108 | 4.550 |
| 7 | 2024Q3 | 4.102 | 4.550 |
| 8 | 2024Q4 | 4.108 | 4.550 |
| 9 | 2025Q1 | 3.768 | 4.550 |
| 10 | 2025Q2 | 3.677 | 4.550 |
| 11 | 2025Q3 | 3.705 | 4.550 |
| 12 | 2025Q4 | 3.929 | 4.550 |
| 13 | 2026Q1 | 4.079 | 4.550 |
| 14 | 2026Q2 | 4.506 | 4.550 |
| 15 | 2026Q3 | 4.333 | 4.550 |


## Diễn giải (viết tay sau khi xem kết quả; các con số lấy từ bảng ở trên, mẫu N = 112 nếu không nói khác)

**Quy tắc huy động hiện hành không mô tả được dữ liệu.**
- Hệ số theo LDR: δ ước lượng là 1.10 (a, gộp), 5.29 (b, FE ngân hàng), 1.19 (c, FE ngân hàng + quý), 2.01 (d, k = 1) so với `deposit_competition = 0.07`, tức gấp khoảng 15 đến 75 lần. Khoảng tin cậy CR1 của (c) là [0.46; 1.91] (N = 112), [-0.17; 1.20] (N = 104) và [-0.18; 1.76] (N = 96): chỉ một phần chứa 0.07. Các khoảng này bị đánh giá quá hẹp (cú sốc chung theo quý, 8 cụm).
- Trôi bình quân: dữ liệu có Δr^D_term trung bình 0.0006 điểm %/quý (độ lệch chuẩn 0.565) trong khi quy tắc hiện hành ngụ ý khoảng +0.038 điểm %/quý tại LDR thực (trung bình 1.12). `base_step_implied` ở LDR = 0.82 là ngoại suy ngoài miền dữ liệu, không nên đọc như ước lượng của 0.018.
- Dạng đúng của mô hình (PT5z, biến đã chặn) cho cùng kết luận.

**Phần lớn biến động của Δr^D là cú sốc chung theo quý, và lãi suất qua đêm giải thích phần lớn cú sốc đó.**
- FE quý một mình giải thích 81% (N = 112), 82% (N = 104), 85% (N = 96) phương sai within-ngân-hàng của Δr^D.
- ON trễ 1 quý: tỷ lệ thay thế FE quý là 0.70 (chưa hiệu chỉnh) và 0.74 (hiệu chỉnh) ở N = 112; R² của thành phần chung theo quý là 0.77, nhưng chỉ trên 13-14 điểm theo quý. Phần phương sai within của Δr^D mà ON giải thích qua thành phần chung khoảng 0.62. ON trễ 2: 0.63-0.65; ON trễ 3: gần 0 (0.04). Độ trễ tốt nhất theo tiêu chí đặt trước: k = 1.
- Với PT5-ON (d, k = 1): tốc độ điều chỉnh φ = 0.177 mỗi quý (N = 112; nửa vòng khoảng 3.6 quý). Bootstrap WCR-t Webb (B = 9999): CI 95% [0.147; 0.228] trên N = 96 và [0.156; 0.196] trên N = 112; `p_boot = 0.0000` nghĩa là không lần lặp nào cực đoan hơn (p < 1/9999). Ở (c) (ON bị FE quý hấp thụ), φ = 0.40 [0.28; 0.53] (CR1): hai con số không cùng mô hình, và φ ở các biến thể FE có xu hướng bị lệch lên do thiên lệch Nickell.
- Mức cân bằng ngụ ý của r^D so với ON (khoảng 1.1 đến 1.3 điểm %) gần như bằng spread thực trung bình trong mẫu; vì Δr̄ ≈ 0 nên đây gần như là định nghĩa, không phải ước lượng độc lập (không có SE).

**Mô phỏng offline (trong mẫu; LDR thực và ON thực là ngoại sinh, khởi tạo bằng dữ liệu thực 2023Q4, so sánh 11 quý 2024Q1-2026Q3).**
- Chuỗi thực của lãi suất cho vay gia quyền là chữ V: đáy 6.97% ở 2025Q1 (t = 9), giảm 1.76 điểm % từ 2023Q4 xuống đáy rồi hồi phục 1.81 điểm % tới 2026Q3.
- Quy tắc huy động hiện hành + PT1 cho đường gần như đi lên đơn điệu (giảm chỉ 0.02 điểm %): **không** tạo chữ V; RMSE 1.35 cho cả hai λ.
- PT5-ON + PT1 tạo chữ V đúng hướng, đáy lệch không quá 1 quý (t = 10 với λ = 0.274; t = 8 với λ = 0.48), nhưng **biên độ chỉ bằng khoảng 0.24 đến 0.44 lần biên độ thực**: giảm 0.57 và hồi phục 0.43 điểm % (λ = 0.274), giảm 0.73 và hồi phục 0.80 (λ = 0.48). RMSE 0.92 và 0.82 (so với 1.35 của quy tắc hiện hành); tương quan đường 0.72 và 0.89.
- PT5 không ON (FE ngân hàng): RMSE 1.06 (λ = 0.274) và 0.98 (λ = 0.48); biên độ giảm 0.44 và 0.51.
- **Ngay cả khi đưa lãi suất huy động thực vào PT1**, biên độ cũng chỉ giảm 0.75-0.88 và hồi phục 0.38-0.75 điểm % (RMSE 0.83 và 0.68). Quan sát mô tả (không phải nguyên nhân đã xác định): biên thực đã thực hiện `r^L − c_{t-1}` giảm từ 4.71 (2023Q2) xuống khoảng 3.68 (2025Q2) rồi tăng lên 4.51 (2026Q2), tức dao động khoảng 1 điểm %. 4.55 là biên MỤC TIÊU của PT1 (`target_margin` + `loan_spread_add`) mà `r^L` tiến tới với tốc độ λ, nên không so trực tiếp với biên thực; tuy vậy theo PT1 khi chi phí vốn giảm và `r^L` điều chỉnh trễ thì biên thực lẽ ra MỞ RỘNG, trong khi dữ liệu cho thấy biên thực HẸP lại, nghĩa là `r^L` giảm nhanh hơn chi phí vốn trễ. Phương trình huy động không bù được phần này; có kênh khác ngoài chi phí vốn trễ (chính sách, cạnh tranh, cơ cấu danh mục…) mà dữ liệu hiện có không phân biệt được. Kết quả mô phỏng này là kiểm tra trong mẫu (hệ số ước lượng trên cùng dữ liệu), không phải dự báo ngoài mẫu.
- RMSE/tương quan giữa các hàng chỉ dùng để so sánh tương đối; đường lai (huy động ước lượng + biên cố định) có thể tốt hơn đường dùng huy động thực ở một số chỉ số (ví dụ tương quan 0.89 so với 0.75 ở λ = 0.48), có thể do hai sai số bù nhau (chưa kiểm chứng); không nên diễn giải như bằng chứng cơ chế.
- **Sai số mức chi phối RMSE.** Sai số trung bình (mô hình − thực) là 0.57-1.26 điểm %, phần lớn của RMSE thô. Sau khi bỏ sai số trung bình (cột `RMSE_khu_muc`): PT5-ON 0.43 (λ = 0.274) và 0.33 (λ = 0.48); quy tắc huy động hiện hành 0.50 và 0.50; huy động thực 0.50 và 0.38; PT5 không ON 0.52 và 0.45. Về hình dạng, cải thiện của PT5-ON so với quy tắc hiện hành có thật nhưng khiêm tốn hơn con số RMSE thô; chênh lệch mức (mô hình cao hơn thực khoảng 0.57 đến 1.26 điểm %, tùy quy tắc huy động) chỉ một phần do phương trình huy động: ngay cả khi đưa lãi suất huy động thực vào PT1 mô hình vẫn lệch +0.57 đến +0.66 điểm %. Phần còn lại chưa được đo riêng (có thể liên quan biên mục tiêu 4.55 cao hơn biên thực trung bình khoảng 4.1); không kết luận nguyên nhân ở đây.

**Hạn chế và việc chờ nhóm quyết định.** LDR là biến nội sinh (LDR cao khi huy động khan, huy động tăng giá khi LDR cao); δ ở (b) lớn có thể phản ánh tương quan chung hơn là độ nhạy cơ chế. δ dao động 1.1 đến 5.3 tùy cách kiểm soát cú sốc chung nên không số nào là "tham số đúng". Mô phỏng offline dùng LDR thực làm ngoại sinh; trong ABM đầy đủ LDR là nội sinh nên kết quả có thể khác. Hệ số ON (φ) ở (d) chủ yếu được xác định bởi chuỗi ON theo thời gian (13-14 điểm), không phải bởi khác biệt giữa ngân hàng. PT5 và PT5-ON có hằng số riêng từng ngân hàng ước lượng trên chính mẫu này (trong mẫu), còn quy tắc hiện hành thì không, nên so sánh không đều về số tham số. Hằng số FE (alpha_mean) đi cùng δ·LDR_trung bình nên không đọc riêng. `bank.py` và `scenarios.yaml` KHÔNG được sửa ở Giai đoạn 7b; mọi thay đổi (thêm số hạng ON vào quy tắc huy động, biên cho vay biến thiên theo thời gian) là quyết định cho Giai đoạn 8-9 của trưởng nhóm.


File: estimates_stage7b.csv, absorption_stage7b.csv, bootstrap_stage7b.csv, simulation_paths_stage7b.csv, simulation_summary_stage7b.csv.
