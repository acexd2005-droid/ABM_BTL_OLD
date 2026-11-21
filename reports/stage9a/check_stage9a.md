# Giai đoạn 9a – kiểm tra hằng số đưa ra YAML (sinh tự động bởi `src/analysis/check_stage9a.py`)

## 1. Khóa mới (giá trị YAML = mặc định code = giá trị cũ cứng trong agent)

| Khóa | Vị trí cũ | Giá trị cũ | YAML | Mặc định code | Khớp |
|---|---|---:|---:|---:|---|
| `target_margin` | bank.py: Bank(target_margin=3.2) | 3.2 | 3.2 | 3.2 | có |
| `funding_cost_add` | bank.py: funding_cost + 0.15 | 0.15 | 0.15 | 0.15 | có |
| `deposit_ldr_target` | bank.py: ldr - 0.82 | 0.82 | 0.82 | 0.82 | có |
| `demand_pressure_cap` | bank.py: max(-0.5, min(0.5, .)) | 0.5 | 0.5 | 0.5 | có |
| `depositor_base_growth` | depositors.py: base_growth=0.004 | 0.004 | 0.004 | 0.004 | có |
| `depositor_max_growth` | depositors.py: max_growth=0.04 | 0.04 | 0.04 | 0.04 | có |
| `borrower_growth_min` | borrowers.py: max(-0.04, .) | -0.04 | -0.04 | -0.04 | có |
| `borrower_growth_max` | borrowers.py: min(0.035, .) | 0.035 | 0.035 | 0.035 | có |
| `compliance_pressure_coef` | regulator.py: 2.5 * (pressure - .) | 2.5 | 2.5 | 2.5 | có |
| `compliance_pressure_center` | regulator.py: (pressure - 0.5) | 0.5 | 0.5 | 0.5 | có |
| `compliance_margin_coef` | regulator.py: 1.1 * (margin - .) | 1.1 | 1.1 | 1.1 | có |
| `compliance_prob_min` | regulator.py: max(0.02, .) | 0.02 | 0.02 | 0.02 | có |
| `compliance_prob_max` | regulator.py: min(0.98, .) | 0.98 | 0.98 | 0.98 | có |

Mọi 46 khóa trong `parameters` của `configs/scenarios.yaml` có mặc định code trùng YAML: có.

## 2. Golden (so khớp chính xác từng bit)

| Cơ sở | Số file | Khớp bitwise | Sai lệch tuyệt đối lớn nhất |
|---|---:|---:|---:|
| term | 18 | 18 | 0 |
| total | 18 | 18 | 0 |

## 3. Mục 6 CLAUDE.md (10 seed từ base_seed, dữ liệu 8 NH 2023Q1)

| Cấu hình | max(B−A) sau CS | max(C−A) sau CS | TB LS cho vay sau CS A / B / C | max lệch trước CS | LS cho vay [min; max] | LS huy động [min; max] | max(loans − LDR·deposits) | trễ: sai số dùng lagged / dùng hiện tại | ĐẠT |
|---|---:|---:|---|---:|---|---|---:|---|---|
| `scenarios.yaml` | -0.1553 | -0.1551 | 9.9342 / 9.5321 / 9.5086 | 0 | [8.131; 12.405] | [4.939; 7.435] | 0 | 0 / 0.0220 | có |
| `scenarios_macro.yaml` | -0.1499 | -0.1499 | 9.3448 / 8.9347 / 8.9108 | 0 | [7.655; 12.405] | [3.819; 7.011] | -9.521e+05 | 0 / 0.0796 | có |

Ghi chú: “sau CS” = các quý có `month` ≥ policy_month + 1 (từ 2026Q4). Kiểm tra trễ: ở quý đầu, `loan_rate` khớp công thức dùng `lagged_funding_cost` đầu kỳ (sai số ~0) và lệch nếu dùng chi phí vốn cuối quý.
