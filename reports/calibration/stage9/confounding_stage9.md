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
