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
