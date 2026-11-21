# GD9b – Hiệu chỉnh lại GD9 theo D9 (Q6, Q7): sinh tự động

> Sinh bởi `python -m src.calibration.calibrate_stage9b`. Phương pháp chốt trước: `DANG_KY_TRUOC_GD9b.md` (commit 1ab8201). Cửa sổ hiệu chỉnh 2023Q2–2025Q2 (month 1–9), ngoài mẫu 2025Q3–2026Q3 (month 10–14). Kịch bản A, tất định (hai seed cho kết quả trùng: có). Mô hình và mốc ON cùng được cấp ON THỰC ngoài mẫu (lợi thế thông tin). Không phải dự báo, không phải tác động chính sách thực tế.

## Q7 – Bù tăng trưởng (một lần, tại nghiệm GD9; `bu_tang_truong_stage9b.csv`)
| chi_tieu | du_lieu | mo_hinh_A_GD9 | delta | base_GD9 | base_moi |
|---|---|---|---|---|---|
| tien_gui (depositor_base_growth) | 0.0397609337 | 0.0297550142 | 0.0100059195 | 0.0397609337 | 0.0497668532 |
| du_no (borrower_base_growth) | 0.0447511050 | 0.0601845269 | -0.0154334219 | 0.0447511050 | 0.0293176831 |

## Bước 1 – Tăng trưởng sau bù và ngưỡng chặn (giữ GD9)
| bien_the | bat_doi_xung | loai_bat_thuong | depositor_base_growth | depositor_min_growth | depositor_max_growth | borrower_base_growth | borrower_growth_min | borrower_growth_max | depositor_base_growth_buoc1 | borrower_base_growth_buoc1 | n_obs | dep_p025 | dep_p975 | loan_p025 | loan_p975 | dep_mean_bank_quarter | loan_mean_bank_quarter | ldr_binh_quan_cua_so |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| batdoixung_daydu | True | False | 0.049767 | -0.014160 | 0.173223 | 0.029318 | 0.001179 | 0.139510 | 0.039761 | 0.044751 | 72 | -0.014160 | 0.173223 | 0.001179 | 0.139510 | 0.047497 | 0.051228 | 1.089962 |
| doixung_daydu | False | False | 0.049767 |  | 0.173223 | 0.029318 | 0.001179 | 0.139510 | 0.039761 | 0.044751 | 72 | -0.014160 | 0.173223 | 0.001179 | 0.139510 | 0.047497 | 0.051228 | 1.089962 |
| batdoixung_loaibatthuong | True | True | 0.047064 | -0.014274 | 0.119269 | 0.028410 | 0.002897 | 0.137079 | 0.037058 | 0.043843 | 69 | -0.014274 | 0.119269 | 0.002897 | 0.137079 | 0.041438 | 0.049953 | 1.089962 |

## Bước 2 – Bộ tốt nhất theo biến thể (trong mẫu)
| bien_the | pass_through | total_margin | base_deposit_rate_step | deposit_competition | ldr_choice | target_margin | deposit_ldr_target | J | RMSE_L_cal | RMSE_D_cal |
|---|---|---|---|---|---|---|---|---|---|---|
| batdoixung_daydu | 0.4000 | 3.4000 | 0.0000 | 0.0700 | ldr_mean | 2.0500 | 1.0900 | 0.3733 | 0.3164 | 0.4303 |
| doixung_daydu | 0.4000 | 3.4000 | 0.0000 | 0.0700 | ldr_mean | 2.0500 | 1.0900 | 0.3733 | 0.3164 | 0.4303 |
| batdoixung_loaibatthuong | 0.4000 | 3.4000 | 0.0000 | 0.0700 | ldr_mean | 2.0500 | 1.0900 | 0.3741 | 0.3164 | 0.4318 |

λ tốt nhất (biến thể chính) = 0.4; CI GĐ7 (c) [0.158; 0.395]: NGOÀI CI. LDR bình quân cửa sổ = 1.0900. 1536 bộ/biến thể.

### Chạm biên lưới (nghiệm chính; giữ, không mở rộng lưới – D9)
| tham_so | gia_tri | can_duoi_luoi | can_tren_luoi | cham_can_duoi | cham_can_tren |
|---|---|---|---|---|---|
| pass_through | 0.4000 | 0.1500 | 0.4000 | False | True |
| total_margin | 3.4000 | 3.4000 | 4.8000 | True | False |
| base_deposit_rate_step | 0.0000 | 0.0000 | 0.0180 | True | False |
| deposit_competition | 0.0700 | 0.0700 | 1.2000 | True | False |

### Top 10 (biến thể chính)
| grid_index | pass_through | total_margin | base_deposit_rate_step | deposit_competition | ldr_choice | target_margin | deposit_ldr_target | J | RMSE_L_cal | RMSE_D_cal |
|---|---|---|---|---|---|---|---|---|---|---|
| 1281 | 0.4000 | 3.4000 | 0.0000 | 0.0700 | ldr_mean | 2.0500 | 1.0900 | 0.3733 | 0.3164 | 0.4303 |
| 1283 | 0.4000 | 3.4000 | 0.0000 | 0.3000 | ldr_mean | 2.0500 | 1.0900 | 0.3759 | 0.3158 | 0.4361 |
| 1025 | 0.3500 | 3.4000 | 0.0000 | 0.0700 | ldr_mean | 2.0500 | 1.0900 | 0.3788 | 0.3279 | 0.4296 |
| 1027 | 0.3500 | 3.4000 | 0.0000 | 0.3000 | ldr_mean | 2.0500 | 1.0900 | 0.3794 | 0.3256 | 0.4332 |
| 1289 | 0.4000 | 3.4000 | 0.0060 | 0.0700 | ldr_mean | 2.0500 | 1.0900 | 0.3829 | 0.3206 | 0.4452 |
| 1285 | 0.4000 | 3.4000 | 0.0000 | 0.7000 | ldr_mean | 2.0500 | 1.0900 | 0.3830 | 0.3156 | 0.4504 |
| 1029 | 0.3500 | 3.4000 | 0.0000 | 0.7000 | ldr_mean | 2.0500 | 1.0900 | 0.3830 | 0.3225 | 0.4436 |
| 1291 | 0.4000 | 3.4000 | 0.0060 | 0.3000 | ldr_mean | 2.0500 | 1.0900 | 0.3851 | 0.3198 | 0.4504 |
| 1033 | 0.3500 | 3.4000 | 0.0060 | 0.0700 | ldr_mean | 2.0500 | 1.0900 | 0.3893 | 0.3340 | 0.4445 |
| 1035 | 0.3500 | 3.4000 | 0.0060 | 0.3000 | ldr_mean | 2.0500 | 1.0900 | 0.3895 | 0.3315 | 0.4475 |

### Hồ sơ hàm mục tiêu (min J theo từng giá trị; biên độ nhỏ = phẳng = khó nhận diện)
| tham_so | gia_tri | J_min | bien_do_J_min |
|---|---|---|---|
| pass_through | 0.1500 | 0.5837 | 0.2104 |
| pass_through | 0.2000 | 0.4977 | 0.2104 |
| pass_through | 0.2500 | 0.4384 | 0.2104 |
| pass_through | 0.3000 | 0.4006 | 0.2104 |
| pass_through | 0.3500 | 0.3788 | 0.2104 |
| pass_through | 0.4000 | 0.3733 | 0.2104 |
| total_margin | 3.4000 | 0.3733 | 0.4000 |
| total_margin | 3.6000 | 0.4018 | 0.4000 |
| total_margin | 3.8000 | 0.4505 | 0.4000 |
| total_margin | 4.0000 | 0.5064 | 0.4000 |
| total_margin | 4.2000 | 0.5689 | 0.4000 |
| total_margin | 4.4000 | 0.6349 | 0.4000 |
| total_margin | 4.6000 | 0.7034 | 0.4000 |
| total_margin | 4.8000 | 0.7733 | 0.4000 |
| base_deposit_rate_step | 0.0000 | 0.3733 | 0.0293 |
| base_deposit_rate_step | 0.0060 | 0.3829 | 0.0293 |
| base_deposit_rate_step | 0.0120 | 0.3926 | 0.0293 |
| base_deposit_rate_step | 0.0180 | 0.4026 | 0.0293 |
| deposit_competition | 0.0700 | 0.3733 | 0.0167 |
| deposit_competition | 0.3000 | 0.3759 | 0.0167 |
| deposit_competition | 0.7000 | 0.3830 | 0.0167 |
| deposit_competition | 1.2000 | 0.3901 | 0.0167 |
| ldr_choice | 0.82 | 0.4040 | 0.0307 |
| ldr_choice | ldr_mean | 0.3733 | 0.0307 |

Biên độ min J theo tham số:
| tham_so | bien_do_J_min |
|---|---|
| base_deposit_rate_step | 0.0293 |
| deposit_competition | 0.0167 |
| ldr_choice | 0.0307 |
| pass_through | 0.2104 |
| total_margin | 0.4000 |

### Tương quan giữa tham số trong top 50 (ô trống = tham số hằng trong top 50)
| tham_so | pass_through | total_margin | base_deposit_rate_step | deposit_competition | ldr_is_mean |
|---|---|---|---|---|---|
| pass_through | 1.000 | 0.390 | 0.095 | -0.058 | -0.112 |
| total_margin | 0.390 | 1.000 | -0.244 | 0.043 | 0.110 |
| base_deposit_rate_step | 0.095 | -0.244 | 1.000 | -0.005 | 0.182 |
| deposit_competition | -0.058 | 0.043 | -0.005 | 1.000 | 0.270 |
| ldr_is_mean | -0.112 | 0.110 | 0.182 | 0.270 | 1.000 |

### Chẩn đoán (CHỈ báo cáo, không đổi bộ chính)
| chan_doan | pass_through | total_margin | base_deposit_rate_step | deposit_competition | ldr_choice | target_margin | deposit_ldr_target | J | RMSE_L_cal | RMSE_D_cal |
|---|---|---|---|---|---|---|---|---|---|---|
| luoi_chinh_tot_nhat | 0.4000 | 3.4000 | 0.0000 | 0.0700 | ldr_mean | 2.0500 | 1.0900 | 0.3733 | 0.3164 | 0.4303 |
| lambda_trong_CI_GD7_tot_nhat | 0.3500 | 3.4000 | 0.0000 | 0.0700 | ldr_mean | 2.0500 | 1.0900 | 0.3788 | 0.3279 | 0.4296 |

## Ngoài mẫu 2025Q3–2026Q3 (so GD9, GĐ8, mốc ngây thơ)
| cau_hinh | chuoi | RMSE_tho_ngoai_mau | RMSE_khu_muc_ngoai_mau | sai_so_tb_ngoai_mau | bien_do_ngoai_mau_mo_hinh | bien_do_ngoai_mau_thuc | quy_day_ngoai_mau_mo_hinh | quy_day_ngoai_mau_thuc |
|---|---|---|---|---|---|---|---|---|
| hieu_chinh_GD9b_batdoixung_daydu | cho_vay | 0.5921 | 0.4861 | -0.3380 | 0.4428 | 1.7147 | 2025Q3 | 2025Q3 |
| hieu_chinh_GD9b_batdoixung_daydu | huy_dong | 0.5421 | 0.2888 | 0.4588 | 0.8081 | 1.4567 | 2025Q3 | 2025Q3 |
| hieu_chinh_GD9b_doixung_daydu | cho_vay | 0.5921 | 0.4861 | -0.3380 | 0.4428 | 1.7147 | 2025Q3 | 2025Q3 |
| hieu_chinh_GD9b_doixung_daydu | huy_dong | 0.5421 | 0.2888 | 0.4588 | 0.8081 | 1.4567 | 2025Q3 | 2025Q3 |
| hieu_chinh_GD9b_batdoixung_loaibatthuong | cho_vay | 0.5897 | 0.4854 | -0.3348 | 0.4447 | 1.7147 | 2025Q3 | 2025Q3 |
| hieu_chinh_GD9b_batdoixung_loaibatthuong | huy_dong | 0.5455 | 0.2881 | 0.4632 | 0.8103 | 1.4567 | 2025Q3 | 2025Q3 |
| chan_doan_GD9b_lambda_trong_CI | cho_vay | 0.6137 | 0.5047 | -0.3492 | 0.3893 | 1.7147 | 2025Q3 | 2025Q3 |
| chan_doan_GD9b_lambda_trong_CI | huy_dong | 0.5405 | 0.2889 | 0.4568 | 0.8074 | 1.4567 | 2025Q3 | 2025Q3 |
| chan_doan_GD9b_nghiem_khong_bu | cho_vay | 0.5516 | 0.4721 | -0.2853 | 0.4841 | 1.7147 | 2025Q3 | 2025Q3 |
| chan_doan_GD9b_nghiem_khong_bu | huy_dong | 0.5922 | 0.2786 | 0.5226 | 0.8405 | 1.4567 | 2025Q3 | 2025Q3 |
| GD9_nghiem | cho_vay | 0.4767 | 0.4609 | 0.1217 | 0.5149 | 1.7147 | 2025Q3 | 2025Q3 |
| GD9_nghiem | huy_dong | 0.5855 | 0.2801 | 0.5142 | 0.8358 | 1.4567 | 2025Q3 | 2025Q3 |
| GD8_chua_hieu_chinh | cho_vay | 1.0930 | 0.4569 | 0.9930 | 0.5265 | 1.7147 | 2025Q3 | 2025Q3 |
| GD8_chua_hieu_chinh | huy_dong | 0.6908 | 0.2826 | 0.6303 | 0.8285 | 1.4567 | 2025Q3 | 2025Q3 |
| ngay_tho_giu_2025Q2 | cho_vay | 1.0447 | 0.6449 | -0.8219 | 0.0000 | 1.7147 | 2025Q3 | 2025Q3 |
| ngay_tho_giu_2025Q2 | huy_dong | 0.8318 | 0.5747 | -0.6014 | 0.0000 | 1.4567 | 2025Q3 | 2025Q3 |
| ngay_tho_ON | cho_vay | 0.6429 | 0.3896 | -0.5114 | 0.9923 | 1.7147 | 2025Q3 | 2025Q3 |
| ngay_tho_ON | huy_dong | 0.4478 | 0.3404 | -0.2909 | 0.9922 | 1.4567 | 2025Q3 | 2025Q3 |

Trong mẫu và toàn chuỗi (chỉ cấu hình mô hình; tỷ lệ V = biên độ giảm/hồi phục mô hình ÷ thực):
| cau_hinh | chuoi | RMSE_tho_trong_mau | RMSE_khu_muc_trong_mau | RMSE_tho_toan_chuoi | RMSE_khu_muc_toan_chuoi | ty_le_giam_V_toan_chuoi | ty_le_hoi_phuc_V_toan_chuoi | quy_day_toan_chuoi_mo_hinh | quy_day_toan_chuoi_thuc |
|---|---|---|---|---|---|---|---|---|---|
| hieu_chinh_GD9b_batdoixung_daydu | cho_vay | 0.3164 | 0.3153 | 0.4354 | 0.4132 | 0.7025 | 0.3025 | 2025Q1 | 2025Q1 |
| hieu_chinh_GD9b_batdoixung_daydu | huy_dong | 0.4303 | 0.2964 | 0.4733 | 0.3020 | 0.7289 | 0.8199 | 2024Q2 | 2024Q2 |
| hieu_chinh_GD9b_doixung_daydu | cho_vay | 0.3164 | 0.3153 | 0.4354 | 0.4132 | 0.7025 | 0.3025 | 2025Q1 | 2025Q1 |
| hieu_chinh_GD9b_doixung_daydu | huy_dong | 0.4303 | 0.2964 | 0.4733 | 0.3020 | 0.7289 | 0.8199 | 2024Q2 | 2024Q2 |
| hieu_chinh_GD9b_batdoixung_loaibatthuong | cho_vay | 0.3164 | 0.3155 | 0.4342 | 0.4125 | 0.7023 | 0.3041 | 2025Q1 | 2025Q1 |
| hieu_chinh_GD9b_batdoixung_loaibatthuong | huy_dong | 0.4318 | 0.2972 | 0.4755 | 0.3027 | 0.7285 | 0.8225 | 2024Q2 | 2024Q2 |
| chan_doan_GD9b_lambda_trong_CI | cho_vay | 0.3279 | 0.3230 | 0.4513 | 0.4426 | 0.7013 | 0.2453 | 2025Q1 | 2025Q1 |
| chan_doan_GD9b_lambda_trong_CI | huy_dong | 0.4296 | 0.2959 | 0.4722 | 0.3016 | 0.7291 | 0.8187 | 2024Q2 | 2024Q2 |
| chan_doan_GD9b_nghiem_khong_bu | cho_vay | 0.3206 | 0.3201 | 0.4180 | 0.4023 | 0.6959 | 0.3335 | 2025Q1 | 2025Q1 |
| chan_doan_GD9b_nghiem_khong_bu | huy_dong | 0.4499 | 0.3084 | 0.5053 | 0.3124 | 0.7230 | 0.8589 | 2024Q2 | 2024Q2 |
| GD9_nghiem | cho_vay | 0.4620 | 0.3824 | 0.4673 | 0.4174 | 0.6173 | 0.3837 | 2024Q4 | 2025Q1 |
| GD9_nghiem | huy_dong | 0.4477 | 0.3070 | 0.5013 | 0.3111 | 0.7235 | 0.8533 | 2024Q2 | 2024Q2 |
| GD8_chua_hieu_chinh | cho_vay | 1.0879 | 0.5291 | 1.0897 | 0.5049 | 0.4458 | 0.4252 | 2024Q4 | 2025Q1 |
| GD8_chua_hieu_chinh | huy_dong | 0.5325 | 0.3358 | 0.5939 | 0.3344 | 0.6909 | 0.8620 | 2024Q2 | 2024Q2 |

## Ngưỡng có đạt tới không, chạm biên (kịch bản A)
| cau_hinh | pham_vi | n_ngan_hang_quy | deposit_ldr_target | ldr_dau_quy_min | ldr_dau_quy_max | ty_le_ldr_tren_nguong | so_ngan_hang_co_ca_hai_phia_nguong | ty_le_ap_luc_cham_chan | bien_muc_tieu | bien_thuc_tb | bien_thuc_min | bien_thuc_max | chenh_bien_thuc_muc_tieu_tb | chenh_bien_tuyet_doi_tb_quy_cuoi | ty_le_bien_thuc_vuot_muc_tieu | ty_le_tg_cham_tran | ty_le_tg_cham_san | ty_le_dn_mong_muon_cham_tran | ty_le_dn_mong_muon_cham_san | ty_le_cham_tran_ldr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hieu_chinh_GD9b | month_1_14 | 112 | 1.0900 | 0.8701 | 1.3994 | 0.6161 | 5 | 0.0000 | 3.4000 | 3.6964 | 3.1075 | 6.1351 | 0.2964 | 0.2635 | 0.5893 | 0.0000 | 0.0000 | 0.0000 | 0.0179 | 0.0000 |
| hieu_chinh_GD9b | month_1_18 | 144 | 1.0900 | 0.8401 | 1.3994 | 0.6319 | 6 | 0.0000 | 3.4000 | 3.6107 | 3.1010 | 6.1351 | 0.2107 | 0.0323 | 0.5208 | 0.0000 | 0.0000 | 0.0000 | 0.0139 | 0.0000 |
| hieu_chinh_GD9 | month_1_14 | 112 | 1.0900 | 0.9162 | 1.6000 | 0.8304 | 6 | 0.0268 | 3.8000 | 3.9990 | 3.5076 | 6.0871 | 0.1990 | 0.2383 | 0.5089 | 0.0000 | 0.0089 | 0.0000 | 0.0000 | 0.0357 |
| hieu_chinh_GD9 | month_1_18 | 144 | 1.0900 | 0.9162 | 1.6000 | 0.8681 | 6 | 0.0833 | 3.8000 | 3.9386 | 3.5076 | 6.0871 | 0.1386 | 0.0317 | 0.4722 | 0.0000 | 0.0069 | 0.0000 | 0.0000 | 0.0972 |
| GD8_chua_hieu_chinh | month_1_14 | 112 | 0.8200 | 0.9162 | 1.4662 | 1.0000 | 0 | 0.0982 | 4.5500 | 4.6577 | 3.8836 | 6.3224 | 0.1077 | 0.2170 | 0.4375 | 0.0000 | 0.0089 | 0.0000 | 0.0000 | 0.0000 |
| GD8_chua_hieu_chinh | month_1_18 | 144 | 0.8200 | 0.9162 | 1.5380 | 1.0000 | 0 | 0.1528 | 4.5500 | 4.6211 | 3.8836 | 6.3224 | 0.0711 | 0.0381 | 0.4444 | 0.0000 | 0.0069 | 0.0000 | 0.0000 | 0.0000 |

Tăng trưởng tổng (TB/quý) kịch bản A so với dữ liệu:
| cau_hinh | pham_vi | tang_truong_tien_gui_tb | tang_truong_du_no_tb |
|---|---|---|---|
| thuc_te | trong_mau_1_9 | 0.0398 | 0.0448 |
| thuc_te | ngoai_mau_10_14 | 0.0334 | 0.0434 |
| hieu_chinh_GD9b | trong_mau_1_9 | 0.0395 | 0.0482 |
| hieu_chinh_GD9b | ngoai_mau_10_14 | 0.0560 | 0.0537 |
| hieu_chinh_GD9 | trong_mau_1_9 | 0.0298 | 0.0602 |
| hieu_chinh_GD9 | ngoai_mau_10_14 | 0.0463 | 0.0604 |
| GD8_chua_hieu_chinh | trong_mau_1_9 | -0.0052 | 0.0131 |
| GD8_chua_hieu_chinh | ngoai_mau_10_14 | 0.0104 | 0.0144 |

LDR theo ngân hàng cuối 2025Q2 / 2026Q3 (kịch bản A so với thực):
| bank_id | GD8_chua_hieu_chinh|LDR_2025Q2 | GD8_chua_hieu_chinh|LDR_2026Q3 | hieu_chinh_GD9|LDR_2025Q2 | hieu_chinh_GD9|LDR_2026Q3 | hieu_chinh_GD9b|LDR_2025Q2 | hieu_chinh_GD9b|LDR_2026Q3 | thuc_te|LDR_2025Q2 | thuc_te|LDR_2026Q3 |
|---|---|---|---|---|---|---|---|---|
| ACB | 1.029 | 1.045 | 1.136 | 1.231 | 0.937 | 0.923 | 1.117 | 1.284 |
| BIDV | 1.241 | 1.244 | 1.370 | 1.465 | 1.139 | 1.110 | 1.051 | 1.085 |
| HDBank | 1.001 | 0.965 | 1.112 | 1.147 | 0.914 | 0.856 | 1.062 | 1.015 |
| MB Bank | 1.244 | 1.305 | 1.364 | 1.521 | 1.125 | 1.143 | 1.123 | 1.296 |
| Techcombank | 1.299 | 1.333 | 1.430 | 1.561 | 1.184 | 1.177 | 1.303 | 1.313 |
| VPBank | 1.280 | 1.241 | 1.413 | 1.462 | 1.162 | 1.096 | 1.380 | 1.528 |
| Vietcombank | 1.380 | 1.475 | 1.519 | 1.600 | 1.264 | 1.305 | 0.981 | 1.019 |
| VietinBank | 1.229 | 1.240 | 1.355 | 1.458 | 1.125 | 1.103 | 1.104 | 1.101 |

## Mục 6 CLAUDE.md (10 lần chạy A/B/C)
| cau_hinh | runs | max_B_minus_A_after | max_C_minus_A_after | mean_loan_after_A | mean_loan_after_B | mean_loan_after_C | max_abs_diff_before | loan_min | loan_max | dep_min | dep_max | max_loans_minus_limit | lag_err_lagged | lag_err_current | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| scenarios_calibrated.yaml (GD9b) | 10 | -0.1495 | -0.1495 | 7.9781 | 7.5890 | 7.5876 | 0.0000 | 6.4908 | 12.2178 | 3.6813 | 6.9743 | -99564282.3920 | 0.0000 | 0.0684 | True |
| scenarios_calibrated_gd9.yaml (GD9) | 10 | -0.1529 | -0.1528 | 8.4903 | 8.0939 | 8.0813 | 0.0000 | 6.8475 | 12.1699 | 3.6953 | 6.9743 | 0.0000 | 0.0000 | 0.0769 | True |
| scenarios_macro.yaml (GĐ8) | 10 | -0.1499 | -0.1499 | 9.3448 | 8.9347 | 8.9108 | 0.0000 | 7.6546 | 12.4051 | 3.8187 | 7.0112 | -952092.1201 | 0.0000 | 0.0796 | True |

YAML hiệu chỉnh khớp bộ tốt nhất: có; sai lệch lớn nhất đường đi khi đọc lại từ YAML = 0.

### Nhiễu lẫn tuân thủ và độ tin cậy của B−A / C−A (`confounding_stage9b.csv`, `ldr_cap_stage9b.csv`, `ldr_cap_2026q3_stage9b.csv`)

10 seed (base_seed + 0..9), trung bình theo seed rồi theo quý 15-18; phương pháp giữ nguyên `confounding_stage9.py`. `max(B−A)` là max theo quý và seed, KHÔNG phải mức trung bình. Số của mô hình, không phải tác động chính sách thực tế.

| Chỉ tiêu (sau CS) | macro_GD8 | hieu_chinh_GD9 | hieu_chinh_GD9b |
|---|---:|---:|---:|
| B−A (TB) | -0.4101 | -0.3964 | -0.3891 |
| C−A (TB) | -0.4340 | -0.4090 | -0.3904 |
| C−B (TB) | -0.0239 | -0.0126 | -0.0014 |
| độ lệch chuẩn B−A theo seed | 0.0232 | 0.0300 | 0.0376 |
| max(B−A) theo quý và seed | -0.1499 | -0.1529 | -0.1495 |
| max(C−A) theo quý và seed | -0.1499 | -0.1528 | -0.1495 |
| LS cho vay A | 9.3448 | 8.4903 | 7.9781 |
| LS cho vay B | 8.9347 | 8.0939 | 7.5890 |
| LS cho vay C | 8.9108 | 8.0813 | 7.5876 |
| nim_proxy A | 4.5579 | 3.7885 | 3.3757 |
| nim_proxy B | 4.1473 | 3.3899 | 2.9862 |
| nim_proxy C | 4.1828 | 3.4117 | 2.9889 |
| xác suất tuân thủ TB, B | 0.9434 | 0.8771 | 0.8184 |
| xác suất tuân thủ TB, C | 0.9454 | 0.8794 | 0.8184 |
| tỷ lệ ngân hàng-quý chạm trần LDR, A (quý 15–18) | 0.0000 | 0.3125 | 0.0000 |
| tỷ lệ chạm trần LDR, B (quý 15–18) | 0.0000 | 0.3438 | 0.0000 |
| tỷ lệ chạm trần LDR, C (quý 15–18) | 0.0000 | 0.3438 | 0.0000 |
| tỷ lệ chạm trần LDR, A, month 1–10 | 0.0000 | 0.0000 | 0.0000 |
| tỷ lệ chạm trần LDR, A, month 11–15 | 0.0000 | 0.1250 | 0.0000 |
| tỷ lệ chạm trần LDR, A, month 16–18 | 0.0000 | 0.3750 | 0.0000 |

Tỷ lệ ngân hàng-quý chạm trần LDR 1.60, kịch bản A, theo month (trung bình 10 seed):

| month | macro_GD8 | hieu_chinh_GD9 | hieu_chinh_GD9b |
|---|---:|---:|---:|
| 1 | 0.0000 | 0.0000 | 0.0000 |
| 2 | 0.0000 | 0.0000 | 0.0000 |
| 3 | 0.0000 | 0.0000 | 0.0000 |
| 4 | 0.0000 | 0.0000 | 0.0000 |
| 5 | 0.0000 | 0.0000 | 0.0000 |
| 6 | 0.0000 | 0.0000 | 0.0000 |
| 7 | 0.0000 | 0.0000 | 0.0000 |
| 8 | 0.0000 | 0.0000 | 0.0000 |
| 9 | 0.0000 | 0.0000 | 0.0000 |
| 10 | 0.0000 | 0.0000 | 0.0000 |
| 11 | 0.0000 | 0.1250 | 0.0000 |
| 12 | 0.0000 | 0.1250 | 0.0000 |
| 13 | 0.0000 | 0.1250 | 0.0000 |
| 14 | 0.0000 | 0.1250 | 0.0000 |
| 15 | 0.0000 | 0.1250 | 0.0000 |
| 16 | 0.0000 | 0.3750 | 0.0000 |
| 17 | 0.0000 | 0.3750 | 0.0000 |
| 18 | 0.0000 | 0.3750 | 0.0000 |

Khởi đầu từ `abm_initial_8nganhang_2026Q3.csv`, kịch bản A, 18 quý: tỷ lệ ngân hàng chạm trần LDR ở quý cuối = 0.125 (macro_GD8); 0.875 (hieu_chinh_GD9); 0.000 (hieu_chinh_GD9b).

<!-- diag_gd9b:begin -->
## Phụ lục chẩn đoán (thêm sau khi chạy lưới, vòng sửa 2)

Số của mô hình, không phải tác động chính sách thực tế. Thí nghiệm "bỏ bù" chỉ để chẩn đoán, không ghi vào YAML, không đổi nghiệm. Δ_D = +0.010006, Δ_L = -0.015433 (`bu_tang_truong_stage9b.csv`).

### 1. Nghiệm GD9b có bù và bỏ bù Q7 (kịch bản A)

| chỉ tiêu | GD9b_bo_bu_CHAN_DOAN | GD9b_co_bu |
|---|---:|---:|
| ldr_max_month_1_18 | 1.6000 | 1.3366 |
| ldr_tb_month_15_18 | 1.5248 | 1.0931 |
| tang_truong_du_no_tb_10_14 | 0.0627 | 0.0537 |
| tang_truong_du_no_tb_1_18 | 0.0592 | 0.0496 |
| tang_truong_du_no_tb_1_9 | 0.0635 | 0.0482 |
| tang_truong_tien_gui_tb_10_14 | 0.0464 | 0.0560 |
| tang_truong_tien_gui_tb_1_18 | 0.0359 | 0.0456 |
| tang_truong_tien_gui_tb_1_9 | 0.0298 | 0.0395 |
| ty_le_cham_tran_LDR_month_15_18 | 0.5938 | 0.0000 |
| ty_le_cham_tran_LDR_month_1_18 | 0.1806 | 0.0000 |

### 2. Áp lực huy động và C−B (deposit_competition như nhau; 10 seed, quý 15–18)

| chỉ tiêu | GD9 | GD9b |
|---|---:|---:|
| deposit_competition | 0.0700 | 0.0700 |
| deposit_rate_C_tru_B_sau_CS | -0.0401 | -0.0006 |
| ldr_dau_quy_A_tb_sau_CS | 1.4614 | 1.0920 |
| ngưỡng_LDR | 1.0900 | 1.0900 |
| nim_proxy_C_tru_B_sau_CS | 0.0218 | 0.0027 |
| ty_le_ldr_tren_nguong_A_sau_CS | 1.0000 | 0.6875 |

### 3a. Hai định nghĩa biên (A, month 1–14)

| chỉ tiêu | GD9 | GD9b |
|---|---:|---:|
| bien_loan_rate_tru_chi_phi_von_tre_tb | 3.9990 | 3.6964 |
| bien_loan_rate_tru_deposit_rate_tb | 3.0955 | 2.8055 |
| muc_tieu_bien_tong | 3.8000 | 3.4000 |

### 3b. Khoảng cách tăng trưởng mô hình − dữ liệu và tỷ số

| chỉ tiêu | hieu_chinh_GD9 | hieu_chinh_GD9b |
|---|---:|---:|
| khoang_cach_du_no_ngoai_mau_10_14 | 0.0170 | 0.0103 |
| khoang_cach_du_no_trong_mau_1_9 | 0.0154 | 0.0035 |
| khoang_cach_tien_gui_ngoai_mau_10_14 | 0.0128 | 0.0225 |
| khoang_cach_tien_gui_trong_mau_1_9 | -0.0100 | -0.0002 |
| ty_so_mo_hinh_tren_thuc_du_no_ngoai_mau_10_14 | 1.3922 | 1.2361 |
| ty_so_mo_hinh_tren_thuc_du_no_trong_mau_1_9 | 1.3449 | 1.0772 |
| ty_so_mo_hinh_tren_thuc_tien_gui_ngoai_mau_10_14 | 1.3839 | 1.6735 |
| ty_so_mo_hinh_tren_thuc_tien_gui_trong_mau_1_9 | 0.7483 | 0.9942 |

<!-- diag_gd9b:end -->
