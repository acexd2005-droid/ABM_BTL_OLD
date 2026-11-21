# Giai đoạn 9 – Hiệu chỉnh bằng mô phỏng và kiểm định ngoài mẫu lịch sử (sinh tự động)

> Sinh bởi `python -m src.calibration.calibrate_stage9`. Phương pháp chốt trước: `DANG_KY_TRUOC.md`. Cửa sổ hiệu chỉnh 2023Q2–2025Q2 (month 1–9), ngoài mẫu 2025Q3–2026Q3 (month 10–14). Kịch bản A, tất định (hai seed cho kết quả trùng: có). Mô hình được cấp ON THỰC ngoài mẫu (lợi thế thông tin). Không phải dự báo, không phải tác động chính sách thực tế.

## Bước 1 – Tăng trưởng (quy tắc, không tối ưu)
| bien_the | bat_doi_xung | loai_bat_thuong | depositor_base_growth | borrower_base_growth | borrower_growth_min | borrower_growth_max | depositor_min_growth | depositor_max_growth | n_obs | dep_p025 | dep_p975 | loan_p025 | loan_p975 | dep_mean_bank_quarter | loan_mean_bank_quarter | ldr_binh_quan_cua_so |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| batdoixung_daydu | True | False | 0.0398 | 0.0448 | 0.0012 | 0.1395 | -0.0142 | 0.1732 | 72 | -0.0142 | 0.1732 | 0.0012 | 0.1395 | 0.0475 | 0.0512 | 1.0900 |
| doixung_daydu | False | False | 0.0398 | 0.0448 | 0.0012 | 0.1395 |  | 0.1732 | 72 | -0.0142 | 0.1732 | 0.0012 | 0.1395 | 0.0475 | 0.0512 | 1.0900 |
| batdoixung_loaibatthuong | True | True | 0.0371 | 0.0438 | 0.0029 | 0.1371 | -0.0143 | 0.1193 | 69 | -0.0143 | 0.1193 | 0.0029 | 0.1371 | 0.0414 | 0.0500 | 1.0900 |
| doixung_loaibatthuong | False | True | 0.0371 | 0.0438 | 0.0029 | 0.1371 |  | 0.1193 | 69 | -0.0143 | 0.1193 | 0.0029 | 0.1371 | 0.0414 | 0.0500 | 1.0900 |

## Bước 2 – Bộ tốt nhất theo biến thể Bước 1 (trong mẫu)
| bien_the | pass_through | total_margin | base_deposit_rate_step | deposit_competition | ldr_choice | target_margin | deposit_ldr_target | J | RMSE_L_cal | RMSE_D_cal |
|---|---|---|---|---|---|---|---|---|---|---|
| batdoixung_daydu | 0.4500 | 3.8000 | 0.0000 | 0.0700 | ldr_mean | 2.4500 | 1.0900 | 0.4548 | 0.4620 | 0.4477 |
| doixung_daydu | 0.4500 | 3.8000 | 0.0000 | 0.0700 | ldr_mean | 2.4500 | 1.0900 | 0.4550 | 0.4620 | 0.4480 |
| batdoixung_loaibatthuong | 0.4500 | 3.8000 | 0.0000 | 0.0700 | ldr_mean | 2.4500 | 1.0900 | 0.4558 | 0.4626 | 0.4489 |
| doixung_loaibatthuong | 0.4500 | 3.8000 | 0.0000 | 0.0700 | ldr_mean | 2.4500 | 1.0900 | 0.4561 | 0.4627 | 0.4496 |

λ tốt nhất (biến thể chính) = 0.45; CI GĐ7 (c) [0.158; 0.395]: NGOÀI CI. LDR bình quân cửa sổ = 1.0900. 1536 bộ/biến thể.

### Top 10 (biến thể chính)
| grid_index | pass_through | total_margin | base_deposit_rate_step | deposit_competition | ldr_choice | target_margin | deposit_ldr_target | J | RMSE_L_cal | RMSE_D_cal |
|---|---|---|---|---|---|---|---|---|---|---|
| 1345 | 0.4500 | 3.8000 | 0.0000 | 0.0700 | ldr_mean | 2.4500 | 1.0900 | 0.4548 | 0.4620 | 0.4477 |
| 1353 | 0.4500 | 3.8000 | 0.0060 | 0.0700 | ldr_mean | 2.4500 | 1.0900 | 0.4674 | 0.4722 | 0.4625 |
| 1153 | 0.4000 | 3.8000 | 0.0000 | 0.0700 | ldr_mean | 2.4500 | 1.0900 | 0.4731 | 0.4991 | 0.4471 |
| 1361 | 0.4500 | 3.8000 | 0.0120 | 0.0700 | ldr_mean | 2.4500 | 1.0900 | 0.4800 | 0.4825 | 0.4775 |
| 1161 | 0.4000 | 3.8000 | 0.0060 | 0.0700 | ldr_mean | 2.4500 | 1.0900 | 0.4856 | 0.5092 | 0.4620 |
| 1369 | 0.4500 | 3.8000 | 0.0180 | 0.0700 | ldr_mean | 2.4500 | 1.0900 | 0.4927 | 0.4929 | 0.4926 |
| 1344 | 0.4500 | 3.8000 | 0.0000 | 0.0700 | 0.82 | 2.4500 | 0.8200 | 0.4938 | 0.4940 | 0.4936 |
| 1347 | 0.4500 | 3.8000 | 0.0000 | 0.3000 | ldr_mean | 2.4500 | 1.0900 | 0.4979 | 0.4862 | 0.5095 |
| 1169 | 0.4000 | 3.8000 | 0.0120 | 0.0700 | ldr_mean | 2.4500 | 1.0900 | 0.4982 | 0.5194 | 0.4770 |
| 961 | 0.3500 | 3.8000 | 0.0000 | 0.0700 | ldr_mean | 2.4500 | 1.0900 | 0.4994 | 0.5523 | 0.4465 |

### Hồ sơ hàm mục tiêu (min J theo từng giá trị; biên độ nhỏ = phẳng = khó nhận diện)
| tham_so | gia_tri | J_min | bien_do_J_min |
|---|---|---|---|
| pass_through | 0.1000 | 0.8203 | 0.3655 |
| pass_through | 0.1500 | 0.7218 | 0.3655 |
| pass_through | 0.2000 | 0.6439 | 0.3655 |
| pass_through | 0.2500 | 0.5827 | 0.3655 |
| pass_through | 0.3000 | 0.5353 | 0.3655 |
| pass_through | 0.3500 | 0.4994 | 0.3655 |
| pass_through | 0.4000 | 0.4731 | 0.3655 |
| pass_through | 0.4500 | 0.4548 | 0.3655 |
| total_margin | 3.8000 | 0.4548 | 0.3884 |
| total_margin | 4.0000 | 0.5221 | 0.3884 |
| total_margin | 4.2000 | 0.5978 | 0.3884 |
| total_margin | 4.4000 | 0.6776 | 0.3884 |
| total_margin | 4.6000 | 0.7597 | 0.3884 |
| total_margin | 4.8000 | 0.8432 | 0.3884 |
| base_deposit_rate_step | 0.0000 | 0.4548 | 0.0379 |
| base_deposit_rate_step | 0.0060 | 0.4674 | 0.0379 |
| base_deposit_rate_step | 0.0120 | 0.4800 | 0.0379 |
| base_deposit_rate_step | 0.0180 | 0.4927 | 0.0379 |
| deposit_competition | 0.0700 | 0.4548 | 0.2124 |
| deposit_competition | 0.3000 | 0.4979 | 0.2124 |
| deposit_competition | 0.7000 | 0.5735 | 0.2124 |
| deposit_competition | 1.2000 | 0.6672 | 0.2124 |
| ldr_choice | 0.82 | 0.4938 | 0.0390 |
| ldr_choice | ldr_mean | 0.4548 | 0.0390 |

Biên độ min J theo tham số:
| tham_so | bien_do_J_min |
|---|---|
| base_deposit_rate_step | 0.0379 |
| deposit_competition | 0.2124 |
| ldr_choice | 0.0390 |
| pass_through | 0.3655 |
| total_margin | 0.3884 |

### Tương quan giữa tham số trong top 50 (biến thể chính; ô trống = tham số hằng trong top 50)
| tham_so | pass_through | total_margin | base_deposit_rate_step | deposit_competition | ldr_is_mean |
|---|---|---|---|---|---|
| pass_through | 1.000 | 0.293 | 0.111 | 0.058 | -0.058 |
| total_margin | 0.293 | 1.000 | -0.162 | -0.182 | 0.182 |
| base_deposit_rate_step | 0.111 | -0.162 | 1.000 | -0.057 | 0.057 |
| deposit_competition | 0.058 | -0.182 | -0.057 | 1.000 | 0.351 |
| ldr_is_mean | -0.058 | 0.182 | 0.057 | 0.351 | 1.000 |

### Chẩn đoán (phụ lục DANG_KY_TRUOC.md, CHỈ báo cáo, không đổi bộ chính)
| chan_doan | pass_through | total_margin | base_deposit_rate_step | deposit_competition | ldr_choice | target_margin | J | RMSE_L_cal | RMSE_D_cal |
|---|---|---|---|---|---|---|---|---|---|
| luoi_chinh_tot_nhat | 0.4500 | 3.8000 | 0.0000 | 0.0700 | ldr_mean | 2.4500 | 0.4548 | 0.4620 | 0.4477 |
| lambda_trong_CI_GD7 | 0.3500 | 3.8000 | 0.0000 | 0.0700 | ldr_mean | 2.4500 | 0.4994 | 0.5523 | 0.4465 |
| luoi_mo_rong_tot_nhat | 0.2500 | 3.0000 | 0.0000 | 0.0000 | ldr_mean | 1.6500 | 0.3649 | 0.3009 | 0.4289 |

Hồ sơ min J trên lưới mở rộng (λ 0.10–1.00, biên tổng 3.0–3.8, δ 0–0.07, base_step 0, LDR bình quân):
| tham_so | gia_tri | J_min | bien_do_J_min |
|---|---|---|---|
| pass_through | 0.1000 | 0.6518 | 0.2869 |
| pass_through | 0.1500 | 0.5092 | 0.2869 |
| pass_through | 0.2000 | 0.4119 | 0.2869 |
| pass_through | 0.2500 | 0.3649 | 0.2869 |
| pass_through | 0.3000 | 0.3675 | 0.2869 |
| pass_through | 0.3500 | 0.3679 | 0.2869 |
| pass_through | 0.4000 | 0.3729 | 0.2869 |
| pass_through | 0.4500 | 0.3790 | 0.2869 |
| pass_through | 0.5000 | 0.3896 | 0.2869 |
| pass_through | 0.5500 | 0.3926 | 0.2869 |
| pass_through | 0.6000 | 0.3991 | 0.2869 |
| pass_through | 0.6500 | 0.4076 | 0.2869 |
| pass_through | 0.7000 | 0.4171 | 0.2869 |
| pass_through | 0.7500 | 0.4249 | 0.2869 |
| pass_through | 0.8000 | 0.4293 | 0.2869 |
| pass_through | 0.8500 | 0.4343 | 0.2869 |
| pass_through | 0.9000 | 0.4395 | 0.2869 |
| pass_through | 0.9500 | 0.4449 | 0.2869 |
| pass_through | 1.0000 | 0.4503 | 0.2869 |
| total_margin | 3.0000 | 0.3649 | 0.0545 |
| total_margin | 3.2000 | 0.3675 | 0.0545 |
| total_margin | 3.4000 | 0.3729 | 0.0545 |
| total_margin | 3.6000 | 0.3896 | 0.0545 |
| total_margin | 3.8000 | 0.4194 | 0.0545 |
| base_deposit_rate_step | 0.0000 | 0.3649 | 0.0000 |
| deposit_competition | 0.0000 | 0.3649 | 0.0109 |
| deposit_competition | 0.0350 | 0.3703 | 0.0109 |
| deposit_competition | 0.0700 | 0.3758 | 0.0109 |
| ldr_choice | ldr_mean | 0.3649 | 0.0000 |

## Bước 3 – Ngoài mẫu 2025Q3–2026Q3
| cau_hinh | chuoi | RMSE_tho_ngoai_mau | RMSE_khu_muc_ngoai_mau | sai_so_tb_ngoai_mau | bien_do_ngoai_mau_mo_hinh | bien_do_ngoai_mau_thuc | quy_day_ngoai_mau_mo_hinh | quy_day_ngoai_mau_thuc |
|---|---|---|---|---|---|---|---|---|
| hieu_chinh_batdoixung_daydu | cho_vay | 0.4767 | 0.4609 | 0.1217 | 0.5149 | 1.7147 | 2025Q3 | 2025Q3 |
| hieu_chinh_batdoixung_daydu | huy_dong | 0.5855 | 0.2801 | 0.5142 | 0.8358 | 1.4567 | 2025Q3 | 2025Q3 |
| hieu_chinh_doixung_daydu | cho_vay | 0.4768 | 0.4609 | 0.1220 | 0.5151 | 1.7147 | 2025Q3 | 2025Q3 |
| hieu_chinh_doixung_daydu | huy_dong | 0.5859 | 0.2802 | 0.5145 | 0.8357 | 1.4567 | 2025Q3 | 2025Q3 |
| hieu_chinh_batdoixung_loaibatthuong | cho_vay | 0.4768 | 0.4597 | 0.1267 | 0.5191 | 1.7147 | 2025Q3 | 2025Q3 |
| hieu_chinh_batdoixung_loaibatthuong | huy_dong | 0.5892 | 0.2795 | 0.5187 | 0.8379 | 1.4567 | 2025Q3 | 2025Q3 |
| hieu_chinh_doixung_loaibatthuong | cho_vay | 0.4771 | 0.4597 | 0.1275 | 0.5190 | 1.7147 | 2025Q3 | 2025Q3 |
| hieu_chinh_doixung_loaibatthuong | huy_dong | 0.5898 | 0.2795 | 0.5194 | 0.8378 | 1.4567 | 2025Q3 | 2025Q3 |
| chan_doan_lambda_trong_CI | cho_vay | 0.5000 | 0.4923 | 0.0871 | 0.4253 | 1.7147 | 2025Q3 | 2025Q3 |
| chan_doan_lambda_trong_CI | huy_dong | 0.5824 | 0.2804 | 0.5105 | 0.8347 | 1.4567 | 2025Q3 | 2025Q3 |
| chan_doan_luoi_mo_rong | cho_vay | 0.8960 | 0.5648 | -0.6956 | 0.2242 | 1.7147 | 2025Q4 | 2025Q3 |
| chan_doan_luoi_mo_rong | huy_dong | 0.5354 | 0.2896 | 0.4503 | 0.8050 | 1.4567 | 2025Q3 | 2025Q3 |
| GD8_chua_hieu_chinh | cho_vay | 1.0930 | 0.4569 | 0.9930 | 0.5265 | 1.7147 | 2025Q3 | 2025Q3 |
| GD8_chua_hieu_chinh | huy_dong | 0.6908 | 0.2826 | 0.6303 | 0.8285 | 1.4567 | 2025Q3 | 2025Q3 |
| GD8_chi_buoc1_tang_truong | cho_vay | 1.0974 | 0.4561 | 0.9981 | 0.5288 | 1.7147 | 2025Q3 | 2025Q3 |
| GD8_chi_buoc1_tang_truong | huy_dong | 0.6956 | 0.2818 | 0.6360 | 0.8310 | 1.4567 | 2025Q3 | 2025Q3 |
| ngay_tho_giu_2025Q2 | cho_vay | 1.0447 | 0.6449 | -0.8219 | 0.0000 | 1.7147 | 2025Q3 | 2025Q3 |
| ngay_tho_giu_2025Q2 | huy_dong | 0.8318 | 0.5747 | -0.6014 | 0.0000 | 1.4567 | 2025Q3 | 2025Q3 |
| ngay_tho_ON | cho_vay | 0.6429 | 0.3896 | -0.5114 | 0.9923 | 1.7147 | 2025Q3 | 2025Q3 |
| ngay_tho_ON | huy_dong | 0.4478 | 0.3404 | -0.2909 | 0.9922 | 1.4567 | 2025Q3 | 2025Q3 |

Trong mẫu và toàn chuỗi (chỉ cấu hình mô hình; tỷ lệ V = biên độ giảm/hồi phục mô hình ÷ thực):
| cau_hinh | chuoi | RMSE_tho_trong_mau | RMSE_khu_muc_trong_mau | RMSE_tho_toan_chuoi | RMSE_khu_muc_toan_chuoi | ty_le_giam_V_toan_chuoi | ty_le_hoi_phuc_V_toan_chuoi | quy_day_toan_chuoi_mo_hinh | quy_day_toan_chuoi_thuc |
|---|---|---|---|---|---|---|---|---|---|
| hieu_chinh_batdoixung_daydu | cho_vay | 0.4620 | 0.3824 | 0.4673 | 0.4174 | 0.6173 | 0.3837 | 2024Q4 | 2025Q1 |
| hieu_chinh_batdoixung_daydu | huy_dong | 0.4477 | 0.3070 | 0.5013 | 0.3111 | 0.7235 | 0.8533 | 2024Q2 | 2024Q2 |
| hieu_chinh_doixung_daydu | cho_vay | 0.4620 | 0.3825 | 0.4673 | 0.4174 | 0.6173 | 0.3838 | 2024Q4 | 2025Q1 |
| hieu_chinh_doixung_daydu | huy_dong | 0.4480 | 0.3071 | 0.5016 | 0.3112 | 0.7233 | 0.8533 | 2024Q2 | 2024Q2 |
| hieu_chinh_batdoixung_loaibatthuong | cho_vay | 0.4626 | 0.3828 | 0.4677 | 0.4168 | 0.6170 | 0.3868 | 2024Q4 | 2025Q1 |
| hieu_chinh_batdoixung_loaibatthuong | huy_dong | 0.4489 | 0.3078 | 0.5035 | 0.3119 | 0.7232 | 0.8562 | 2024Q2 | 2024Q2 |
| hieu_chinh_doixung_loaibatthuong | cho_vay | 0.4627 | 0.3829 | 0.4679 | 0.4168 | 0.6169 | 0.3871 | 2024Q4 | 2025Q1 |
| hieu_chinh_doixung_loaibatthuong | huy_dong | 0.4496 | 0.3081 | 0.5042 | 0.3121 | 0.7229 | 0.8561 | 2024Q2 | 2024Q2 |
| chan_doan_lambda_trong_CI | cho_vay | 0.5523 | 0.3993 | 0.5342 | 0.4571 | 0.6047 | 0.2748 | 2025Q1 | 2025Q1 |
| chan_doan_lambda_trong_CI | huy_dong | 0.4465 | 0.3062 | 0.4993 | 0.3103 | 0.7238 | 0.8513 | 2024Q2 | 2024Q2 |
| chan_doan_luoi_mo_rong | cho_vay | 0.3009 | 0.3008 | 0.5873 | 0.5340 | 0.7869 | 0.1236 | 2025Q4 | 2025Q1 |
| chan_doan_luoi_mo_rong | huy_dong | 0.4289 | 0.2940 | 0.4697 | 0.2998 | 0.7287 | 0.8132 | 2024Q2 | 2024Q2 |
| GD8_chua_hieu_chinh | cho_vay | 1.0879 | 0.5291 | 1.0897 | 0.5049 | 0.4458 | 0.4252 | 2024Q4 | 2025Q1 |
| GD8_chua_hieu_chinh | huy_dong | 0.5325 | 0.3358 | 0.5939 | 0.3344 | 0.6909 | 0.8620 | 2024Q2 | 2024Q2 |
| GD8_chi_buoc1_tang_truong | cho_vay | 1.0897 | 0.5297 | 1.0925 | 0.5051 | 0.4452 | 0.4274 | 2024Q4 | 2025Q1 |
| GD8_chi_buoc1_tang_truong | huy_dong | 0.5348 | 0.3372 | 0.5972 | 0.3356 | 0.6898 | 0.8649 | 2024Q2 | 2024Q2 |

## Bước 4 – Ngưỡng có đạt tới không, chạm biên (kịch bản A)
| cau_hinh | pham_vi | n_ngan_hang_quy | deposit_ldr_target | ldr_dau_quy_min | ldr_dau_quy_max | ty_le_ldr_tren_nguong | so_ngan_hang_co_ca_hai_phia_nguong | ty_le_ap_luc_cham_chan | bien_muc_tieu | bien_thuc_tb | bien_thuc_min | bien_thuc_max | chenh_bien_thuc_muc_tieu_tb | chenh_bien_tuyet_doi_tb_quy_cuoi | ty_le_bien_thuc_vuot_muc_tieu | ty_le_tg_cham_tran | ty_le_tg_cham_san | ty_le_dn_mong_muon_cham_tran | ty_le_dn_mong_muon_cham_san | ty_le_cham_tran_ldr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hieu_chinh_batdoixung_daydu | month_1_14 | 112 | 1.0900 | 0.9162 | 1.6000 | 0.8304 | 6 | 0.0268 | 3.8000 | 3.9990 | 3.5076 | 6.0871 | 0.1990 | 0.2383 | 0.5089 | 0.0000 | 0.0089 | 0.0000 | 0.0000 | 0.0357 |
| hieu_chinh_batdoixung_daydu | month_1_18 | 144 | 1.0900 | 0.9162 | 1.6000 | 0.8681 | 6 | 0.0833 | 3.8000 | 3.9386 | 3.5076 | 6.0871 | 0.1386 | 0.0317 | 0.4722 | 0.0000 | 0.0069 | 0.0000 | 0.0000 | 0.0972 |
| GD8_chua_hieu_chinh | month_1_14 | 112 | 0.8200 | 0.9162 | 1.4662 | 1.0000 | 0 | 0.0982 | 4.5500 | 4.6577 | 3.8836 | 6.3224 | 0.1077 | 0.2170 | 0.4375 | 0.0000 | 0.0089 | 0.0000 | 0.0000 | 0.0000 |
| GD8_chua_hieu_chinh | month_1_18 | 144 | 0.8200 | 0.9162 | 1.5380 | 1.0000 | 0 | 0.1528 | 4.5500 | 4.6211 | 3.8836 | 6.3224 | 0.0711 | 0.0381 | 0.4444 | 0.0000 | 0.0069 | 0.0000 | 0.0000 | 0.0000 |

Tăng trưởng tổng (TB/quý) và LDR theo ngân hàng (kịch bản A so với thực):
| cau_hinh | pham_vi | tang_truong_tien_gui_tb | tang_truong_du_no_tb |
|---|---|---|---|
| thuc_te | trong_mau_1_9 | 0.0398 | 0.0448 |
| thuc_te | ngoai_mau_10_14 | 0.0334 | 0.0434 |
| hieu_chinh_batdoixung_daydu | trong_mau_1_9 | 0.0298 | 0.0602 |
| hieu_chinh_batdoixung_daydu | ngoai_mau_10_14 | 0.0463 | 0.0604 |
| GD8_chua_hieu_chinh | trong_mau_1_9 | -0.0052 | 0.0131 |
| GD8_chua_hieu_chinh | ngoai_mau_10_14 | 0.0104 | 0.0144 |

| bank_id | GD8_chua_hieu_chinh|LDR_2025Q2 | GD8_chua_hieu_chinh|LDR_2026Q3 | hieu_chinh_batdoixung_daydu|LDR_2025Q2 | hieu_chinh_batdoixung_daydu|LDR_2026Q3 | thuc_te|LDR_2025Q2 | thuc_te|LDR_2026Q3 |
|---|---|---|---|---|---|---|
| ACB | 1.029 | 1.045 | 1.136 | 1.231 | 1.117 | 1.284 |
| BIDV | 1.241 | 1.244 | 1.370 | 1.465 | 1.051 | 1.085 |
| HDBank | 1.001 | 0.965 | 1.112 | 1.147 | 1.062 | 1.015 |
| MB Bank | 1.244 | 1.305 | 1.364 | 1.521 | 1.123 | 1.296 |
| Techcombank | 1.299 | 1.333 | 1.430 | 1.561 | 1.303 | 1.313 |
| VPBank | 1.280 | 1.241 | 1.413 | 1.462 | 1.380 | 1.528 |
| Vietcombank | 1.380 | 1.475 | 1.519 | 1.600 | 0.981 | 1.019 |
| VietinBank | 1.229 | 1.240 | 1.355 | 1.458 | 1.104 | 1.101 |

Chẩn đoán (KHÔNG đổi bộ chính): bù một lần phần lệch tăng trưởng tổng trong mẫu vào base_growth:
| chan_doan | depositor_base_growth | borrower_base_growth | J | RMSE_L_cal | RMSE_D_cal | tang_truong_tien_gui_tb_1_9 | tang_truong_du_no_tb_1_9 | ldr_max_month_14 | ty_le_cham_tran_ldr_1_14 |
|---|---|---|---|---|---|---|---|---|---|
| bo_chinh | 0.0398 | 0.0448 | 0.4548 | 0.4620 | 0.4477 | 0.0298 | 0.0602 | 1.6000 | 0.0357 |
| bu_tang_truong | 0.0498 | 0.0293 | 0.4407 | 0.4530 | 0.4283 | 0.0395 | 0.0449 | 1.2379 | 0.0000 |

## Mục 6 CLAUDE.md (10 lần chạy A/B/C)
| cau_hinh | runs | max_B_minus_A_after | max_C_minus_A_after | mean_loan_after_A | mean_loan_after_B | mean_loan_after_C | max_abs_diff_before | loan_min | loan_max | dep_min | dep_max | max_loans_minus_limit | lag_err_lagged | lag_err_current | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| scenarios_calibrated.yaml | 10 | -0.1529 | -0.1528 | 8.4903 | 8.0939 | 8.0813 | 0.0000 | 6.8475 | 12.1699 | 3.6953 | 6.9743 | 0.0000 | 0.0000 | 0.0769 | True |
| scenarios_macro.yaml (GĐ8) | 10 | -0.1499 | -0.1499 | 9.3448 | 8.9347 | 8.9108 | 0.0000 | 7.6546 | 12.4051 | 3.8187 | 7.0112 | -952092.1201 | 0.0000 | 0.0796 | True |

YAML hiệu chỉnh khớp bộ tốt nhất: có; sai lệch lớn nhất đường đi khi đọc lại từ YAML = 0.

<!-- confounding:begin -->
### Nhiễu lẫn tuân thủ và độ tin cậy của B−A / C−A (vòng sửa 2; `confounding_stage9.csv`, `ldr_cap_stage9.csv`, `ldr_cap_2026q3_stage9.csv`)

10 seed (base_seed + 0..9), trung bình theo seed rồi theo quý 15-18. `max(B−A)` ở mục 6 là max theo quý và seed, KHÔNG phải mức trung bình. Chênh lệch phần lớn là hiệu ứng mức và nhiễu lẫn tuân thủ; đây là số của mô hình, không phải tác động chính sách thực tế.

| Chỉ tiêu (sau CS) | macro GĐ8 | hiệu chỉnh GD9 |
|---|---:|---:|
| B−A (TB) | -0.4101 | -0.3964 |
| C−A (TB) | -0.4340 | -0.4090 |
| C−B (TB) | -0.0239 | -0.0126 |
| độ lệch chuẩn B−A theo seed | 0.0232 | 0.0300 |
| max(B−A) theo quý và seed | -0.1499 | -0.1529 |
| max(C−A) theo quý và seed | -0.1499 | -0.1528 |
| LS cho vay A | 9.3448 | 8.4903 |
| LS cho vay B | 8.9347 | 8.0939 |
| LS cho vay C | 8.9108 | 8.0813 |
| nim_proxy A | 4.5579 | 3.7885 |
| nim_proxy B | 4.1473 | 3.3899 |
| nim_proxy C | 4.1828 | 3.4117 |
| xác suất tuân thủ TB, B | 0.9434 | 0.8771 |
| xác suất tuân thủ TB, C | 0.9454 | 0.8794 |
| tỷ lệ ngân hàng-quý chạm trần LDR, A | 0.0000 | 0.3125 |
| tỷ lệ chạm trần LDR, B | 0.0000 | 0.3438 |
| tỷ lệ chạm trần LDR, C | 0.0000 | 0.3438 |
| tỷ lệ chạm trần LDR, A, month 1–10 | 0.0000 | 0.0000 |
| tỷ lệ chạm trần LDR, A, month 11–15 | 0.0000 | 0.1250 |
| tỷ lệ chạm trần LDR, A, month 16–18 | 0.0000 | 0.3750 |

Khởi đầu từ `abm_initial_8nganhang_2026Q3.csv`, kịch bản A, 18 quý: tỷ lệ ngân hàng chạm trần LDR ở quý cuối = 0.125 (macro GĐ8) và 0.875 (hiệu chỉnh GD9).
<!-- confounding:end -->
