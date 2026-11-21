# Giai đoạn 7c: chỉ đạo lãi suất có làm biên cho vay hẹp lại không? (sinh tự động)

> Không sửa mô hình, không sửa `configs/`. Kết quả chỉ là **tương quan** trong mẫu, không phải tác động nhân quả của chỉ đạo và không phải tác động chính sách thực tế. Không đề xuất giá trị tham số.

## Biến và quy tắc

- Dữ liệu: `data/raw/chi_dao_lai_suat_2023_2026.csv` (24 sự kiện). Hai sự kiện 2026Q4 (Công văn 9608/9736) nằm ngoài panel (kết thúc 2026Q3) nên không dùng, để dành cho kiểm định ngoài mẫu.
- **I_q:** 0 = không có văn bản; 1 = có văn bản yêu cầu giảm/ổn định lãi suất (mọi loại trừ `thay_doi_LS_dieu_hanh` và `cong_bo_LS_cho_vay`; kể cả `kiem_tra_thuc_hien`); 2 = có mục tiêu định lượng cho lãi suất cho vay (cột `muc_tieu_dinh_luong` khác rỗng và loại `yeu_cau_giam_LS_cho_vay` hoặc nội dung mục tiêu có chữ "cho vay"). Nhiều văn bản trong quý: lấy giá trị lớn nhất.
- **Dời quý (mặc định):** văn bản có ngày đầy đủ ban hành **sau ngày 15 của tháng cuối quý** (3, 6, 9, 12) tính sang quý sau; ngày chỉ có tháng không dời. Chạy thêm bản **không dời** (`khong_dich`) để kiểm tra độ nhạy. Quy tắc này chỉ dời 2 sự kiện: Thông báo ổn định lãi suất 30/3/2026 (2026Q1 → 2026Q2) và QĐ thay đổi lãi suất điều hành 19/6/2023 (2023Q2 → 2023Q3).
- **DH_q:** số quyết định thay đổi lãi suất điều hành (`thay_doi_LS_dieu_hanh`) trong quý (cùng quy tắc dời); đưa vào như biến kiểm soát riêng.
- **Biên thực** `m_{i,t} = loan_rate_pct_t − (deposit_rate_pct_{t−1} + 0.15)` (cơ sở `term`). Mẫu: 8 ngân hàng × 14 quý (2023Q2-2026Q3), N = 112.
- Mô hình: FE ngân hàng (**không** FE quý vì sẽ hấp thụ I_q), kiểm soát `ON_{t−1}`; SE CR1 theo ngân hàng (8 cụm, t với 7 bậc tự do) và wild-cluster bootstrap Webb (B = 9999) cho hệ số `I_t`.

## Bảng cường độ I_q theo quý

| t | quy | I_dich_quy | n_van_ban_dich | DH_dich | I_khong_dich | n_van_ban_khong_dich | DH_khong_dich |
|---|---|---|---|---|---|---|---|
| 1 | 2023Q1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 2023Q2 | 0 | 0 | 2 | 0 | 0 | 3 |
| 3 | 2023Q3 | 2 | 2 | 1 | 2 | 2 | 0 |
| 4 | 2023Q4 | 1 | 1 | 0 | 1 | 1 | 0 |
| 5 | 2024Q1 | 1 | 2 | 0 | 1 | 2 | 0 |
| 6 | 2024Q2 | 2 | 1 | 0 | 2 | 1 | 0 |
| 7 | 2024Q3 | 0 | 0 | 0 | 0 | 0 | 0 |
| 8 | 2024Q4 | 1 | 2 | 0 | 1 | 2 | 0 |
| 9 | 2025Q1 | 1 | 2 | 0 | 1 | 2 | 0 |
| 10 | 2025Q2 | 0 | 0 | 0 | 0 | 0 | 0 |
| 11 | 2025Q3 | 1 | 1 | 0 | 1 | 1 | 0 |
| 12 | 2025Q4 | 0 | 0 | 0 | 0 | 0 | 0 |
| 13 | 2026Q1 | 0 | 0 | 0 | 1 | 1 | 0 |
| 14 | 2026Q2 | 1 | 4 | 0 | 1 | 3 | 0 |
| 15 | 2026Q3 | 0 | 0 | 0 | 0 | 0 | 0 |

Phân bố I (bản dời quý) trên 15 quý: I = 0: 6 quý, I = 1: 7 quý, I = 2: 2 quý. **Khác với kỳ vọng ban đầu "I_q gần như luôn ≥ 1"**: có 6 quý không có văn bản (I = 0) và chỉ 2 quý có mục tiêu định lượng (I = 2: 2023Q3, 2024Q2). Nhận diện vì thế đến từ cả chênh lệch 0 so với ≥ 1 lẫn 1 so với 2, nhưng mức "I = 2" chỉ dựa trên hai quý.

### Mô tả: biên thực theo mức I

| I | so_quy | bien_tb | dr_L_tb | ON_tb |
|---|---|---|---|---|
| 0.0000 | 6.0000 | 4.1384 | 0.0804 | 4.8357 |
| 1.0000 | 6.0000 | 3.9632 | -0.1840 | 3.1418 |
| 2.0000 | 2.0000 | 4.0851 | -0.3308 | 2.2905 |

Tương quan theo quý (T = 14): corr(I_t, ON_{t−1}) = -0.55; corr(I_t, biên thực) = -0.15. Chỉ đạo tập trung vào các quý lãi suất liên ngân hàng thấp (2023Q3-2025Q1), nên I_t và ON_{t−1} cộng tuyến đáng kể.

### Mô tả theo quý

| t | quy | I | DH | ON_t-1 | bien_thuc_gia_quyen | dr_L_tb |
|---|---|---|---|---|---|---|
| 2 | 2023Q2 | 0 | 2 | 4.817 | 4.711 | 0.029 |
| 3 | 2023Q3 | 2 | 1 | 3.573 | 4.063 | -0.344 |
| 4 | 2023Q4 | 1 | 0 | 0.227 | 3.943 | -0.631 |
| 5 | 2024Q1 | 1 | 0 | 0.680 | 3.750 | -0.943 |
| 6 | 2024Q2 | 2 | 0 | 1.008 | 4.108 | -0.318 |
| 7 | 2024Q3 | 0 | 0 | 4.072 | 4.102 | -0.274 |
| 8 | 2024Q4 | 1 | 0 | 4.400 | 4.108 | -0.069 |
| 9 | 2025Q1 | 1 | 0 | 4.125 | 3.768 | -0.307 |
| 10 | 2025Q2 | 0 | 0 | 4.349 | 3.677 | -0.097 |
| 11 | 2025Q3 | 1 | 0 | 3.607 | 3.705 | 0.111 |
| 12 | 2025Q4 | 0 | 0 | 4.557 | 3.929 | 0.211 |
| 13 | 2026Q1 | 0 | 0 | 5.452 | 4.079 | 0.124 |
| 14 | 2026Q2 | 1 | 0 | 5.812 | 4.506 | 0.735 |
| 15 | 2026Q3 | 0 | 0 | 5.767 | 4.333 | 0.488 |

## Hệ số: dạng tuyến tính (I_t, I_{t−1}), bản dời quý, có kiểm soát DH

### Biên thực (mức)

| I_def | kiem_soat_DH | parameter | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | r2 | n |
|---|---|---|---|---|---|---|---|---|---|
| dich_quy | True | I_t | 0.2169 | 0.0515 | 4.2090 | 0.0951 | 0.3388 | 0.2726 | 112 |
| dich_quy | True | I_t-1 | 0.2296 | 0.0595 | 3.8578 | 0.0889 | 0.3703 | 0.2726 | 112 |
| dich_quy | True | ON_t-1 | 0.0864 | 0.0253 | 3.4084 | 0.0264 | 0.1463 | 0.2726 | 112 |
| dich_quy | True | DH_t | 0.3886 | 0.0965 | 4.0266 | 0.1604 | 0.6169 | 0.2726 | 112 |
| dich_quy | True | I_sum | 0.4465 | 0.1077 | 4.1467 | 0.1919 | 0.7011 | 0.2726 | 112 |

### Δ lãi suất cho vay

| I_def | kiem_soat_DH | parameter | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | r2 | n |
|---|---|---|---|---|---|---|---|---|---|
| dich_quy | True | I_t | 0.0818 | 0.0690 | 1.1860 | -0.0813 | 0.2449 | 0.5220 | 112 |
| dich_quy | True | I_t-1 | -0.0012 | 0.0571 | -0.0207 | -0.1361 | 0.1337 | 0.5220 | 112 |
| dich_quy | True | ON_t-1 | 0.2210 | 0.0185 | 11.9390 | 0.1772 | 0.2647 | 0.5220 | 112 |
| dich_quy | True | DH_t | -0.0997 | 0.0416 | -2.3990 | -0.1980 | -0.0014 | 0.5220 | 112 |
| dich_quy | True | I_sum | 0.0806 | 0.1096 | 0.7354 | -0.1786 | 0.3398 | 0.5220 | 112 |

### Phần dư PT1 (d1), hai bước

| I_def | kiem_soat_DH | parameter | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | r2 | n |
|---|---|---|---|---|---|---|---|---|---|
| dich_quy | True | I_t | 0.0575 | 0.0528 | 1.0885 | -0.0674 | 0.1825 | 0.0279 | 112 |
| dich_quy | True | I_t-1 | 0.0103 | 0.0388 | 0.2669 | -0.0813 | 0.1020 | 0.0279 | 112 |
| dich_quy | True | DH_t | 0.0632 | 0.0495 | 1.2765 | -0.0539 | 0.1804 | 0.0279 | 112 |
| dich_quy | True | I_sum | 0.0679 | 0.0770 | 0.8812 | -0.1142 | 0.2500 | 0.0279 | 112 |

### PT1 (d1) thêm I_t, I_{t−1}, một bước

| I_def | kiem_soat_DH | parameter | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | r2 | n |
|---|---|---|---|---|---|---|---|---|---|
| dich_quy | True | lambda | 0.3769 | 0.0502 | 7.5063 | 0.2582 | 0.4957 | 0.6307 | 112 |
| dich_quy | True | ON_t-1c | 0.1702 | 0.0166 | 10.2773 | 0.1311 | 0.2094 | 0.6307 | 112 |
| dich_quy | True | I_t | 0.1327 | 0.0621 | 2.1371 | -0.0141 | 0.2796 | 0.6307 | 112 |
| dich_quy | True | I_t-1 | 0.0858 | 0.0574 | 1.4953 | -0.0499 | 0.2215 | 0.6307 | 112 |
| dich_quy | True | DH_t | 0.0844 | 0.0571 | 1.4776 | -0.0506 | 0.2194 | 0.6307 | 112 |
| dich_quy | True | I_sum | 0.2185 | 0.1103 | 1.9818 | -0.0422 | 0.4793 | 0.6307 | 112 |

## Hệ số: dạng biến giả (I = 1, I = 2 so với I = 0); biên độ ngụ ý I = 2 so với I = 1

### Biên thực (mức)

| I_def | kiem_soat_DH | parameter | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | r2 | n |
|---|---|---|---|---|---|---|---|---|---|
| dich_quy | True | I1_t | 0.0070 | 0.0698 | 0.0997 | -0.1581 | 0.1721 | 0.2308 | 112 |
| dich_quy | True | I2_t | 0.1268 | 0.0719 | 1.7620 | -0.0434 | 0.2969 | 0.2308 | 112 |
| dich_quy | True | ON_t-1 | 0.0099 | 0.0296 | 0.3346 | -0.0602 | 0.0800 | 0.2308 | 112 |
| dich_quy | True | I2_minus_I1 | 0.1198 | 0.1228 | 0.9755 | -0.1706 | 0.4102 | 0.2308 | 112 |

### Δ lãi suất cho vay

| I_def | kiem_soat_DH | parameter | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | r2 | n |
|---|---|---|---|---|---|---|---|---|---|
| dich_quy | True | I1_t | 0.0762 | 0.0784 | 0.9727 | -0.1091 | 0.2615 | 0.5221 | 112 |
| dich_quy | True | I2_t | 0.1687 | 0.1362 | 1.2390 | -0.1532 | 0.4907 | 0.5221 | 112 |
| dich_quy | True | ON_t-1 | 0.2212 | 0.0135 | 16.3799 | 0.1892 | 0.2531 | 0.5221 | 112 |
| dich_quy | True | I2_minus_I1 | 0.0925 | 0.1412 | 0.6550 | -0.2413 | 0.4263 | 0.5221 | 112 |

### Phần dư PT1 (d1), hai bước

| I_def | kiem_soat_DH | parameter | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | r2 | n |
|---|---|---|---|---|---|---|---|---|---|
| dich_quy | True | I1_t | 0.0343 | 0.0669 | 0.5136 | -0.1237 | 0.1924 | 0.0288 | 112 |
| dich_quy | True | I2_t | 0.1226 | 0.1228 | 0.9976 | -0.1679 | 0.4130 | 0.0288 | 112 |
| dich_quy | True | I2_minus_I1 | 0.0882 | 0.1385 | 0.6371 | -0.2392 | 0.4156 | 0.0288 | 112 |

## Độ nhạy theo đặc tả kiểm soát: hệ số của I_t (FE ngân hàng, N = 112)

Ở bản dời quý, hệ số dương và lớn (≥ 0.2) của I_t lên biên thực chỉ xuất hiện khi kiểm soát đồng thời `ON_{t−1}` và `I_{t−1}`; không có ON thì gần 0 (I_t và ON_{t−1} tương quan −0.55 và ON_{t−1} có hệ số dương lên biên). Bản không dời quý cho hệ số dương ở nhiều đặc tả hơn. Vì vậy hệ số dương KHÔNG đọc được như tác động của biến chỉ đạo thô. Với Δ lãi suất cho vay, hệ số ÂM khi không kiểm soát ON là kết quả đáng lưu ý (phù hợp với giả thuyết chỉ đạo kéo lãi suất xuống), chỉ là không tách được khỏi chu kỳ lãi suất chung.

| outcome | dac_ta | coef_I_t | se_cluster | ci95_lo | ci95_hi | r2 |
|---|---|---|---|---|---|---|
| margin | I_t | 0.0276 | 0.0534 | -0.0985 | 0.1538 | 0.0017 |
| margin | I_t, I_t-1 | 0.0433 | 0.0692 | -0.1203 | 0.2068 | 0.0079 |
| margin | I_t, ON | 0.0752 | 0.0251 | 0.0159 | 0.1346 | 0.0132 |
| margin | I_t, I_t-1, ON | 0.2588 | 0.0545 | 0.1300 | 0.3876 | 0.0686 |
| margin | I_t, ON, DH | 0.0516 | 0.0245 | -0.0064 | 0.1095 | 0.2281 |
| margin | I_t, I_t-1, ON, DH (cơ sở) | 0.2169 | 0.0515 | 0.0951 | 0.3388 | 0.2726 |
| margin | I_t, I_t-1, DH (không ON) | 0.0594 | 0.0688 | -0.1033 | 0.2220 | 0.2405 |
| dRL | I_t | -0.2203 | 0.0523 | -0.3440 | -0.0966 | 0.0971 |
| dRL | I_t, I_t-1 | -0.3196 | 0.0522 | -0.4430 | -0.1963 | 0.3271 |
| dRL | I_t, ON | 0.0767 | 0.0587 | -0.0622 | 0.2156 | 0.5097 |
| dRL | I_t, I_t-1, ON | 0.0711 | 0.0705 | -0.0957 | 0.2378 | 0.5097 |
| dRL | I_t, ON, DH | 0.0827 | 0.0594 | -0.0578 | 0.2231 | 0.5220 |
| dRL | I_t, I_t-1, ON, DH (cơ sở) | 0.0818 | 0.0690 | -0.0813 | 0.2449 | 0.5220 |
| dRL | I_t, I_t-1, DH (không ON) | -0.3213 | 0.0527 | -0.4460 | -0.1967 | 0.3294 |

Bản không dời quý:

| outcome | dac_ta | coef_I_t | se_cluster | ci95_lo | ci95_hi | r2 |
|---|---|---|---|---|---|---|
| margin | I_t | 0.0077 | 0.0481 | -0.1060 | 0.1215 | 0.0001 |
| margin | I_t, I_t-1 | 0.0442 | 0.0671 | -0.1146 | 0.2030 | 0.0140 |
| margin | I_t, ON | 0.0382 | 0.0201 | -0.0095 | 0.0858 | 0.0069 |
| margin | I_t, I_t-1, ON | 0.1973 | 0.0357 | 0.1129 | 0.2817 | 0.0566 |
| margin | I_t, ON, DH | 0.1523 | 0.0290 | 0.0837 | 0.2210 | 0.2485 |
| margin | I_t, I_t-1, ON, DH (cơ sở) | 0.3479 | 0.0437 | 0.2446 | 0.4512 | 0.3190 |
| margin | I_t, I_t-1, DH (không ON) | 0.1779 | 0.0640 | 0.0266 | 0.3293 | 0.2681 |
| dRL | I_t | -0.2036 | 0.0494 | -0.3204 | -0.0868 | 0.0769 |
| dRL | I_t, I_t-1 | -0.3158 | 0.0494 | -0.4327 | -0.1990 | 0.1974 |
| dRL | I_t, ON | 0.0493 | 0.0507 | -0.0707 | 0.1692 | 0.5049 |
| dRL | I_t, I_t-1, ON | 0.1206 | 0.0549 | -0.0092 | 0.2504 | 0.5141 |
| dRL | I_t, ON, DH | 0.0402 | 0.0471 | -0.0712 | 0.1517 | 0.5063 |
| dRL | I_t, I_t-1, ON, DH (cơ sở) | 0.1116 | 0.0550 | -0.0186 | 0.2418 | 0.5149 |
| dRL | I_t, I_t-1, DH (không ON) | -0.3299 | 0.0478 | -0.4429 | -0.2169 | 0.2000 |

## Độ nhạy: không dời quý

### Biên thực (mức), tuyến tính, không dời quý

| I_def | kiem_soat_DH | parameter | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | r2 | n |
|---|---|---|---|---|---|---|---|---|---|
| khong_dich | True | I_t | 0.3479 | 0.0437 | 7.9615 | 0.2446 | 0.4512 | 0.3190 | 112 |
| khong_dich | True | I_t-1 | 0.2817 | 0.0403 | 6.9960 | 0.1865 | 0.3769 | 0.3190 | 112 |
| khong_dich | True | ON_t-1 | 0.0895 | 0.0334 | 2.6841 | 0.0107 | 0.1684 | 0.3190 | 112 |
| khong_dich | True | I_sum | 0.6296 | 0.0786 | 8.0075 | 0.4437 | 0.8155 | 0.3190 | 112 |

### Δ lãi suất cho vay, tuyến tính, không dời quý

| I_def | kiem_soat_DH | parameter | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | r2 | n |
|---|---|---|---|---|---|---|---|---|---|
| khong_dich | True | I_t | 0.1116 | 0.0550 | 2.0275 | -0.0186 | 0.2418 | 0.5149 | 112 |
| khong_dich | True | I_t-1 | 0.1028 | 0.0404 | 2.5458 | 0.0073 | 0.1983 | 0.5149 | 112 |
| khong_dich | True | ON_t-1 | 0.2326 | 0.0161 | 14.4167 | 0.1945 | 0.2708 | 0.5149 | 112 |
| khong_dich | True | I_sum | 0.2144 | 0.0832 | 2.5761 | 0.0176 | 0.4112 | 0.5149 | 112 |

## Wild-cluster bootstrap Webb cho hệ số I_t (có kiểm soát DH)

WCR-t, trọng số Webb 6 điểm, B = 9999, seed = 20261121. Với 8 cụm nhưng I_q là biến chung theo quý, **thông tin hiệu dụng cỡ 14 điểm**: bootstrap theo ngân hàng không khắc phục được điều này. `p_boot = 0.0000` nghĩa là p < 1/9999.

| equation | I_def | coef | se_cr1 | ci_cr1_lo | ci_cr1_hi | p_boot | ci_boot_lo | ci_boot_hi |
|---|---|---|---|---|---|---|---|---|
| margin | dich_quy | 0.2169 | 0.0515 | 0.0951 | 0.3388 | 0.0012 | 0.0856 | 0.3449 |
| dRL | dich_quy | 0.0818 | 0.0690 | -0.0813 | 0.2449 | 0.2651 | -0.0781 | 0.2537 |
| pt1_resid_2step | dich_quy | 0.0575 | 0.0528 | -0.0674 | 0.1825 | 0.3273 | -0.0654 | 0.1848 |
| pt1_onestep | dich_quy | 0.1327 | 0.0621 | -0.0141 | 0.2796 | 0.0851 | -0.0255 | 0.2878 |
| margin | khong_dich | 0.3479 | 0.0437 | 0.2446 | 0.4512 | 0.0012 | 0.2462 | 0.4488 |
| dRL | khong_dich | 0.1116 | 0.0550 | -0.0186 | 0.2418 | 0.0966 | -0.0131 | 0.2423 |
| pt1_resid_2step | khong_dich | 0.0994 | 0.0462 | -0.0097 | 0.2085 | 0.0773 | -0.0143 | 0.2164 |
| pt1_onestep | khong_dich | 0.2100 | 0.0457 | 0.1019 | 0.3181 | 0.0025 | 0.1127 | 0.3196 |

## Kiểm tra chuỗi thời gian (biên bình quân gia quyền theo quý, T = 14, OLS, SE thường)

| parameter | coef | se_ols | t | T | R2 | I_def |
|---|---|---|---|---|---|---|
| const | 3.3596 | 0.4608 | 7.2907 | 14 | 0.5088 | dich_quy |
| I_t | 0.1379 | 0.1621 | 0.8503 | 14 | 0.5088 | dich_quy |
| I_t-1 | 0.1467 | 0.1566 | 0.9370 | 14 | 0.5088 | dich_quy |
| ON_t-1 | 0.1135 | 0.0693 | 1.6370 | 14 | 0.5088 | dich_quy |
| DH_t | 0.2675 | 0.1237 | 2.1616 | 14 | 0.5088 | dich_quy |
| const | 3.0123 | 0.3209 | 9.3855 | 14 | 0.7183 | khong_dich |
| I_t | 0.3013 | 0.1206 | 2.4981 | 14 | 0.7183 | khong_dich |
| I_t-1 | 0.2718 | 0.1155 | 2.3529 | 14 | 0.7183 | khong_dich |
| ON_t-1 | 0.1387 | 0.0432 | 3.2103 | 14 | 0.7183 | khong_dich |
| DH_t | 0.2528 | 0.0708 | 3.5714 | 14 | 0.7183 | khong_dich |


## Diễn giải (viết tay sau khi xem kết quả; các con số lấy từ các bảng ở trên)

**Không có bằng chứng ủng hộ giả thuyết “chỉ đạo làm biên cho vay hẹp lại”: hệ số của I_t lên biên thực ≥ 0 ở mọi đặc tả; lên Δ lãi suất cho vay, hệ số chỉ âm khi KHÔNG kiểm soát ON và đổi dấu (không có ý nghĩa) khi kiểm soát ON_{t−1}.**
- Biên thực (mức), bản dời quý, FE ngân hàng, kiểm soát ON_{t−1} và DH_t: β(I_t) = +0.217 (CR1 [0.095; 0.339]; bootstrap Webb p = 0.0012, CI [0.086; 0.345]), β(I_{t−1}) = +0.230, tổng +0.447. **Ở bản dời quý, hệ số lớn (≥ 0.2) chỉ có khi kiểm soát đồng thời ON_{t−1} và I_{t−1}**: không có ON thì gần 0 (0.028 khi chỉ có I_t; 0.043 khi có I_t, I_{t−1}), và chỉ I_t + ON cho 0.075 (xem bảng độ nhạy theo đặc tả). Bản không dời quý cho hệ số dương ở nhiều đặc tả hơn (kể cả không ON: 0.178 với I_t, I_{t−1}, DH). Trung bình thô theo mức I cũng không đơn điệu: biên 4.14 (I = 0), 3.96 (I = 1), 4.09 (I = 2). Nên kết luận là **không có bằng chứng biên hẹp hơn**, không phải “biên rộng hơn do chỉ đạo”.
- Δ lãi suất cho vay: β(I_t) = +0.082, không có ý nghĩa (bootstrap p = 0.265, CI [−0.078; 0.254]) khi kiểm soát ON_{t−1}. **Khi không kiểm soát ON, hệ số là ÂM và rõ: −0.22 (chỉ I_t; CR1 [−0.34; −0.10]) và −0.32 (thêm I_{t−1})**: lãi suất cho vay giảm nhiều hơn ở các quý có chỉ đạo, nhưng đó cũng là các quý lãi suất liên ngân hàng thấp (corr(I_t, ON_{t−1}) = −0.55) nên không tách được tác động của chỉ đạo khỏi chu kỳ lãi suất chung; dấu âm biến mất ngay khi thêm ON_{t−1}. Phần dư PT1 (d1): hai bước +0.058 (p = 0.327), một bước +0.133 (p = 0.085, CI [−0.026; 0.288]). Nếu chỉ đạo kéo lãi suất cho vay xuống ngoài phần chi phí vốn giải thích thì các hệ số này phải âm.
- Dạng biến giả: I = 1 so với 0: +0.007; I = 2 so với 0: +0.127. **Biên độ ngụ ý của I = 2 so với I = 1 là +0.12 điểm % (CR1 [−0.17; 0.41])**, tức không phải biên giảm; chỉ dựa trên 2 quý có I = 2 (2023Q3, 2024Q2).

**Kết quả rất mong manh, nên không diễn giải như một tác động.**
- *Nhạy với quy tắc dời quý của đúng một sự kiện:* bản không dời quý cho β(I_t) = +0.348 thay vì +0.217 (và PT1 một bước +0.210 với p = 0.0025 thay vì +0.133). Quy tắc dời chỉ đổi quý của hai sự kiện (Thông báo ổn định lãi suất 30/3/2026 và QĐ lãi suất điều hành 19/6/2023).
- *SE cụm theo ngân hàng không hợp lệ cho biến chung theo quý:* I_q chỉ có 14 giá trị khác nhau (mọi ngân hàng cùng giá trị trong một quý), nên thông tin hiệu dụng cỡ 14 điểm, không phải 112. Kiểm tra chuỗi thời gian (biên bình quân theo quý, T = 14, OLS, SE thường, vẫn lạc quan vì bỏ qua tự tương quan): β(I_t) = +0.138 (SE 0.162, t = 0.85) ở bản dời quý, +0.301 (t = 2.5) ở bản không dời. Các p-value rất nhỏ của bootstrap theo ngân hàng (0.0012) vì vậy **không nên đọc là có ý nghĩa**.
- *Cộng tuyến với ON:* corr(I_t, ON_{t−1}) = −0.55: chỉ đạo tập trung vào các quý lãi suất liên ngân hàng thấp. Dù đã kiểm soát ON_{t−1} tuyến tính, tách tác động của chỉ đạo khỏi chu kỳ lãi suất chung từ 14 điểm là không khả thi.
- *Nội sinh:* chỉ đạo có thể được ban hành khi lãi suất cho vay đang cao hoặc được kỳ vọng giảm; khi đó quan hệ ngược chiều (lãi suất/biên ảnh hưởng tới việc ban hành) có thể cho hệ số dương. Dữ liệu hiện có không phân biệt được các cách giải thích này. Kết quả là **tương quan**.
- *Phân bố I khác kỳ vọng ban đầu:* I_q không "gần như luôn ≥ 1": có 6 trong 14 quý ước lượng không có văn bản (I = 0), 6 quý I = 1 và chỉ 2 quý I = 2. Nhận diện đến từ cả chênh lệch 0 so với ≥ 1 lẫn 1 so với 2, nhưng mức I = 2 chỉ dựa trên hai quý.

**Dữ liệu cũng không đủ sức để bác bỏ một tác động của chỉ đạo** (thiếu đối chứng, nội sinh, 14 điểm): “không có bằng chứng” không phải “không có tác động”.

**Có đủ căn cứ để hiệu chỉnh `policy_pressure`, `policy_step` từ dữ liệu này không? Không.** (i) dấu của hệ số lên Δ lãi suất cho vay phụ thuộc vào việc kiểm soát ON (âm và rõ khi không kiểm soát, đúng dấu kỳ vọng của mô hình; dương/không có ý nghĩa khi kiểm soát), còn hệ số lên biên thực ≥ 0 ở mọi đặc tả: không nhất quán, và việc coi ON là biến kiểm soát chu kỳ chung hay là biến bị chính chỉ đạo tác động ngược là giả định kinh tế không quyết được bằng dữ liệu này; (ii) chỉ 14 quý, I_q là biến chung theo quý, mức I = 2 chỉ có 2 quý; (iii) kết quả đổi cỡ 60% khi dời quý một sự kiện; (iv) cộng tuyến với chu kỳ lãi suất và nội sinh; (v) chế độ trong dữ liệu (chỉ đạo gần như liên tục, 2023-2026) không có đối chứng "không can thiệp" tương ứng với kịch bản A của mô hình, và mô hình kích hoạt chính sách một lần từ Q4/2026. Báo cáo này không đề xuất giá trị tham số nào. Hai văn bản 2026Q4 (Công văn 9608/9736) nằm ngoài mẫu và có thể dùng cho kiểm định ngoài mẫu.

**Hệ số DH_t** (+0.39 trong mô hình biên thực) chỉ dương ở ba quý đầu (2023Q1-Q3), trùng giai đoạn biên cao nhất (4.7), nên chủ yếu bắt xu hướng thời gian; không đọc như tác động của lãi suất điều hành.

**Hạn chế.** Biên thực `r^L − c_{t−1}` bao gồm cả chi phí vốn trễ và mức cho vay danh mục sổ sách (lợi suất sổ sách, trễ so với lãi suất cận biên); mã hóa cường độ I_q (0/1/2) là một thang thứ tự gán tay, không phải đo lường độ mạnh thực của chỉ đạo; `kiem_tra_thuc_hien` được tính là I = 1 theo quy tắc đã nêu; phần dư PT1 hai bước không hiệu chỉnh sai số của bước một.


File: estimates_stage7c.csv, bootstrap_stage7c.csv, policy_intensity_stage7c.csv, spec_sensitivity_stage7c.csv.
