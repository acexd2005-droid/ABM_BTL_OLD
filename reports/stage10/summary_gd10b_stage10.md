# GD10b – Độ nhạy `deposit_competition` và `policy_step` 0.375 (sinh tự động)

Sinh bởi `python -m src.analysis.sensitivity_gd10b`. Cấu hình nền: `configs/scenarios_calibrated.yaml` (GD9b), 30 lần chạy, mỗi lần đổi một tham số trong bộ nhớ. **Đây là độ nhạy, không phải ước lượng**; không giá trị nào được chọn làm bản chính; YAML chính không đổi. Số là kết quả mô hình, không phải tác động chính sách thực tế.

| Cấu hình | LS cho vay A sau CS | B−A TB | C−A TB | C−B TB | B−A cuối kỳ | C−A cuối kỳ | LS huy động C−B | tuân thủ B | nim_proxy A | tỷ lệ chạm trần LDR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| co_so_30 | 7.9781 | -0.4004 | -0.4018 | -0.0014 | -0.5113 | -0.5143 | -0.0046 | 0.8176 | 3.376 | 0.0000 |
| deposit_competition_0.07 | 7.9781 | -0.4004 | -0.4018 | -0.0014 | -0.5113 | -0.5143 | -0.0046 | 0.8176 | 3.376 | 0.0000 |
| deposit_competition_0.3 | 8.0148 | -0.4006 | -0.4047 | -0.0041 | -0.5103 | -0.5206 | -0.0161 | 0.8180 | 3.377 | 0.0000 |
| deposit_competition_0.7 | 8.0646 | -0.4001 | -0.4059 | -0.0058 | -0.5088 | -0.5232 | -0.0209 | 0.8187 | 3.391 | 0.0000 |
| deposit_competition_1.2 | 8.0983 | -0.4016 | -0.4001 | 0.0015 | -0.5119 | -0.5104 | -0.0019 | 0.8193 | 3.422 | 0.0000 |
| policy_step_0.375 | 7.9781 | -0.5342 | -0.5356 | -0.0014 | -0.6793 | -0.6824 | -0.0047 | 0.8083 | 3.376 | 0.0000 |

Quý sau chính sách = 15–18 (Q4/2026–Q3/2027). `co_so_30` là cấu hình GD9b (deposit_competition 0.07, policy_step 0.28) chạy 30 lần để đối chiếu cùng số lần.
