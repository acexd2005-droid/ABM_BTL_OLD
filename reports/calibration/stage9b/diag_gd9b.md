# Chẩn đoán GD9b (vòng sửa 2; phụ lục đăng ký mục 7, thêm SAU khi chạy lưới; `diag_gd9b.csv`)

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
