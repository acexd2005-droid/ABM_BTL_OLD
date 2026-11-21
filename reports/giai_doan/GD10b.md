# GD10b – Độ nhạy `deposit_competition` và `policy_step` 0.375; sai lệch mức trong mẫu GD9b

**Trạng thái:** HOÀN THÀNH · **Ngày:** 2026-11-21 · **Commit:** ab6d156

## 1. Mục tiêu và phạm vi
Theo LO_TRINH.md (GD10b, D10, Q10, Q14): (1) trên cấu hình GD9b, 30 lần chạy, mỗi lần đổi một tham số: `deposit_competition` ∈ {0.07, 0.3, 0.7, 1.2} và `policy_step` = 0.375; (2) quy tắc đọc đặt trước: báo cả 4 giá trị (B−A, C−A, C−B, tỷ lệ chạm trần LDR), KHÔNG chọn giá trị nào làm bản chính, không dùng kết quả để sửa YAML; (3) ghi rõ đây là độ nhạy, không phải ước lượng; (4) xuất sai lệch mức trong mẫu (2023Q2–2025Q2) của GD9b và GD9 ra CSV.
KHÔNG làm: không đổi YAML, không chạm `src/agents/`, `src/core/`, không hiệu chỉnh lại, không chọn bản chính.

## 2. Đã làm
- `src/analysis/sensitivity_gd10b.py` (mới; tái dùng hàm của `robustness_stage10.py`). Chạy `python -m src.analysis.sensitivity_gd10b` (~2 giây). Biến thể đổi trong bộ nhớ; seed `base_seed + i`, cùng seed cho A/B/C.
- `src/calibration/mean_error_insample_stage9b.py` (mới, chỉ đọc). Chạy `python -m src.calibration.mean_error_insample_stage9b`. Dùng đúng `c9.simulate` và `actual_series` của GD9.
- Kết quả: `reports/stage10/sensitivity_gd10b_stage10.csv`, `reports/stage10/sensitivity_gd10b_section6_stage10.csv`, `reports/stage10/summary_gd10b_stage10.md`, `reports/calibration/stage9b/mean_error_insample_stage9b.csv`.
- Test mới `tests/test_gd10b.py` (5 test): tái lập từng byte (cả hai script), md5 mọi YAML không đổi, đủ 4 giá trị `deposit_competition` + `policy_step` 0.375 và mỗi biến thể đổi ≤ 1 tham số, khớp `oos_stage9b.csv` (RMSE thô, khử mức; √(thô² − khử mức²) = |sai số TB|), mục 6 đạt, khớp cấu hình chính 30 lần của GD10.

## 3. Kết quả chính
### 3.1 Độ nhạy 30 lần (`reports/stage10/sensitivity_gd10b_stage10.csv`; đây là ĐỘ NHẠY, không phải ước lượng; mô hình, không phải tác động chính sách thực tế)
| Cấu hình | LS cho vay A sau CS | B−A TB | C−A TB | C−B TB | B−A cuối kỳ | C−A cuối kỳ | LS huy động C−B | tuân thủ B | tỷ lệ chạm trần LDR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| co_so_30 (GD9b, đối chiếu) | 7.9781 | −0.4004 | −0.4018 | −0.0014 | −0.5113 | −0.5143 | −0.0046 | 0.8176 | 0 |
| deposit_competition 0.07 (= YAML) | 7.9781 | −0.4004 | −0.4018 | −0.0014 | −0.5113 | −0.5143 | −0.0046 | 0.8176 | 0 |
| deposit_competition 0.3 | 8.0148 | −0.4006 | −0.4047 | −0.0041 | −0.5103 | −0.5206 | −0.0161 | 0.8180 | 0 |
| deposit_competition 0.7 | 8.0646 | −0.4001 | −0.4059 | −0.0058 | −0.5088 | −0.5232 | −0.0209 | 0.8187 | 0 |
| deposit_competition 1.2 | 8.0983 | −0.4016 | −0.4001 | +0.0015 | −0.5119 | −0.5104 | −0.0019 | 0.8193 | 0 |
| policy_step 0.375 | 7.9781 | −0.5342 | −0.5356 | −0.0014 | −0.6793 | −0.6824 | −0.0047 | 0.8083 | 0 |
- Cả 4 giá trị `deposit_competition` được báo cáo ngang hàng; không giá trị nào là bản chính. Đổi `deposit_competition` làm mức A tăng nhẹ (7.978 → 8.098) nhưng B−A gần như không đổi (−0.4001 đến −0.4016); C−A và C−B đổi trong khoảng nhỏ (C−B từ −0.0058 đến +0.0015, tức ≤ 1.5% |B−A|), dấu C−B không đơn điệu theo giá trị. Tỷ lệ chạm trần LDR bằng 0 ở cả 4 giá trị (không phải bằng chứng về cơ chế).
- `policy_step` 0.375: B−A TB −0.5342 (≈ 1.42 × step, khớp quan hệ B−A ≈ −1.4 × step của GD10), cuối kỳ −0.6793, nằm giữa kết quả step 0.28 (−0.4004) và 0.42/0.50 của GD10 (`sensitivity_stage10.csv`). Mô hình vẫn không tái tạo mức giảm 1.5–2 điểm %; ánh xạ step ↔ chỉ đạo thực là giả định.
- Mục 6 đạt ở cả 6 cấu hình (`sensitivity_gd10b_section6_stage10.csv`).

### 3.2 Sai lệch mức trong mẫu 2023Q2–2025Q2, kịch bản A (`reports/calibration/stage9b/mean_error_insample_stage9b.csv`; TRONG MẪU, mô hình − thực)
| Cấu hình | Chuỗi | Sai số TB có dấu | RMSE thô | RMSE khử mức |
|---|---|---:|---:|---:|
| GD9b | LS cho vay | −0.0257 | 0.3164 | 0.3153 |
| GD9b | LS huy động | +0.3120 | 0.4303 | 0.2964 |
| GD9 | LS cho vay | +0.2592 | 0.4620 | 0.3824 |
| GD9 | LS huy động | +0.3258 | 0.4477 | 0.3070 |
- Sai lệch mức của LS huy động trong mẫu: GD9b +0.312 (GD9 +0.326). Đây là số GD12 trích cho hạn chế (a). Khớp `oos_stage9b.csv` (cột `*_trong_mau`).

## 4. Kiểm tra
| Hạng mục | Kết quả |
|---|---|
| pytest | 216 passed, 1 xfailed |
| validation | 7/7 ĐẠT |
| Mục 6 CLAUDE.md | đạt cả 6 cấu hình: B,C ≤ A sau CS; trước CS trùng (0); LS trong miền; loans ≤ cap·deposits; trễ (lag_err_tre = 0) |
| Golden | không đổi |
| YAML chính | không đổi (test md5 trước/sau chạy; `git diff` configs rỗng) |
| Tái lập | chạy lại cho file giống hệt từng byte: có (test) |

## 5. Quyết định mặc định đã áp dụng
| # | Câu hỏi | Mặc định đã dùng | Căn cứ | Hệ quả nếu Huy chọn khác |
|---|---|---|---|---|
| 1 | `policy_step` 0.375 chạy riêng (không tổ hợp với `deposit_competition`) | mỗi lần đổi đúng một tham số | LO_TRINH GD10b mục 1 | Có thể chạy thêm lưới giao nhau nếu cần |
| 2 | Giá trị 0.07 = YAML nên trùng cấu hình chính | giữ làm một trong 4 giá trị, kèm `co_so_30` đối chiếu | quy tắc "báo cả 4 giá trị" | không |

## 6. CẦN HUY QUYẾT ĐỊNH
Không có điểm mới.

## 7. Hạn chế và rủi ro
- Độ nhạy 30 lần; sai khác do số lần chạy cỡ ~2% (GD10). Chênh C−B giữa các `deposit_competition` (≤ 0.006) nhỏ so với nhiễu mô phỏng nên không đọc thành xu hướng.
- Sai lệch mức huy động +0.31 trong mẫu là hạn chế của mô hình (Q14).

## 8. Phản biện (điều phối viên điền nguyên văn báo cáo cuối của reviewer-abm, số vòng)

Reviewer-abm: **ĐẠT** sau 1 vòng.

> KẾT LUẬN: ĐẠT
>
> KỸ THUẬT: pytest 216 passed, 1 xfailed (lần đầu lỗi collection do chưa kích hoạt .venv, không phải lỗi code); validation True; `git diff HEAD -- configs data src/agents src/core tests/golden` rỗng, md5 8 file YAML không đổi (scenarios.yaml 36daf800…c27); chỉ có 2 script mới, 1 test mới, file kết quả, báo cáo; hằng số chỉ `DC_VALUES = (0.07, 0.3, 0.7, 1.2)` và `STEP_VALUE = 0.375` theo LO_TRINH; tái lập từng byte (cmp 4 file); bảng đủ 4 giá trị `deposit_competition`, `policy_step` 0.375 và dòng `co_so_30`; không chọn bản chính; số báo cáo khớp CSV; sai lệch mức khớp `oos_stage9b.csv` (GD9b cho vay √(0.31638²−0.31533²)=0.0258=|−0.0257|; huy động √(0.43031²−0.29638²)=0.312).
>
> KINH TẾ: mục 6 đạt ở cả 6 cấu hình; B−A −0.400…−0.534, C−A −0.400…−0.536; tỷ lệ chạm trần LDR = 0 ở mọi cấu hình (không phải bằng chứng cơ chế); B−A gần như không đổi theo `deposit_competition`; C−B từ −0.0058 đến +0.0015, đổi dấu không đơn điệu (nhiễu); `policy_step` 0.375 → B−A −0.534 (≈1.9×step), ánh xạ là giả định; tuân thủ B 0.808–0.819. Không diễn giải A/B/C là tác động thực.
>
> VẤN ĐỀ CẦN SỬA: (1) [NHỎ] mục 8 và ô Commit chưa điền – điều phối viên điền. (2) [NHỎ] `CmB_ci95_nua_rong` rất nhỏ do cùng seed A/B/C, không đọc là độ chắc chắn ước lượng. (3) [NHỎ] tỷ lệ chạm trần LDR = 0 nên cột không phân biệt các giá trị `deposit_competition`.
>
> CẦN NGƯỜI DÙNG/NHÓM QUYẾT ĐỊNH: không có điểm mới. Việc chọn `deposit_competition` làm bản chính vẫn để mở theo Q10 và không nên chọn theo bảng này (C−B nhỏ hơn nhiễu mô phỏng); ánh xạ `policy_step` sang mức chỉ đạo thực là giả định của nhóm.

Ghi chú điều phối viên: 1.9 là lỗi tính; đúng là 0.5342/0.375 = 1.42.
