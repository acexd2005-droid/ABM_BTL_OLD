# GD9a – Đưa hằng số cứng còn lại ra YAML (thay đổi hành vi = 0)

**Trạng thái:** HOÀN THÀNH · **Ngày:** 2026-11-21 · **Commit:** (điều phối viên điền)

## 1. Mục tiêu và phạm vi
Đưa các hằng số hành vi còn cứng trong `src/agents/` ra `configs/scenarios.yaml` với giá trị mặc định = giá trị hiện tại (có comment, đơn vị, cập nhật README): ngưỡng LDR 0.82 và chặn ±0.5 của `demand_pressure` (`bank.py`), `base_growth` 0.004 và `max_growth` 0.04 (`depositors.py`), chặn −0.04/0.035 (`borrowers.py`), rà soát mọi hằng số hành vi còn lại trong `src/agents/` và `src/core/`. Chỉ chạm agent để **đọc tham số**, không đổi công thức, không đổi trình tự `step()`.
KHÔNG làm: không đổi giá trị nào, không hiệu chỉnh (thuộc GD9), không đổi golden.

## 2. Đã làm
- `configs/scenarios.yaml`: thêm 13 khóa (mục "Giai doan 9a"), giá trị = giá trị cũ: `target_margin` 3.2, `funding_cost_add` 0.15, `deposit_ldr_target` 0.82, `demand_pressure_cap` 0.5, `depositor_base_growth` 0.004, `depositor_max_growth` 0.04, `borrower_growth_min` −0.04, `borrower_growth_max` 0.035, `compliance_pressure_coef` 2.5, `compliance_pressure_center` 0.5, `compliance_margin_coef` 1.1, `compliance_prob_min` 0.02, `compliance_prob_max` 0.98. Không sửa khóa cũ nào (D5).
- `src/core/model.py`: đọc các khóa bằng `p.get(khóa, mặc định = YAML)`, truyền vào agent; `target_margin` gán bằng `setdefault` khi dữ liệu không có cột `target_margin` (dữ liệu có cột thì dữ liệu được ưu tiên – đúng như hành vi cũ, vì trước đây cột dữ liệu đè mặc định 3.2 của `Bank`). Thêm kiểm tra giá trị không hợp lệ (`demand_pressure_cap < 0`, `depositor_max_growth < 0`, `borrower_growth_min > borrower_growth_max`, xác suất ngoài `0 ≤ min ≤ max ≤ 1`) – chỉ báo lỗi, không ảnh hưởng mặc định.
- `src/agents/bank.py`: `funding_cost` dùng `model.funding_cost_add`; `demand_pressure` dùng `model.deposit_ldr_target`, `model.demand_pressure_cap`. Biểu thức giữ nguyên thứ tự phép tính.
- `src/agents/depositors.py`: chỉ sửa docstring (giá trị đã là thuộc tính; nay `ABMModel` truyền từ YAML).
- `src/agents/borrowers.py`: thêm tham số `growth_min`, `growth_max` (mặc định −0.04, 0.035).
- `src/agents/regulator.py`: thêm `pressure_coef`, `pressure_center`, `margin_coef`, `prob_min`, `prob_max` (mặc định 2.5, 0.5, 1.1, 0.02, 0.98).
- `src/analysis/compare_macro_driver.py`: hàm `drift_table` đọc `deposit_ldr_target`, `demand_pressure_cap` từ cấu hình (mặc định 0.82, 0.5) thay vì lặp lại hằng số.
- `src/analysis/check_stage9a.py` (mới): sinh `reports/stage9a/check_stage9a.json` và `.md`.
- `tests/test_constants_yaml.py` (mới, 36 test): mặc định code = YAML cho **mọi** khóa `parameters` (phân tích AST các lời gọi `p.get`, so cả kiểu); mặc định hàm khởi tạo agent = YAML; bỏ các khóa mới khỏi tham số cho kết quả trùng **chính xác** (dữ liệu thật và bộ giả lập, A/B/C); golden `term` và `golden_total` khớp với `check_exact=True` (18 + 18 cặp file); các literal cũ không còn trong công thức agent; mỗi khóa mới có tác dụng; giá trị không hợp lệ bị từ chối.
- `README.md`: bảng tham số, đoạn YAML mẫu, mục 3.5 (hằng số còn cố định).

### Rà soát hằng số còn lại trong `src/agents/`, `src/core/` (giữ cứng, có lý do)
| Hằng số | Vị trí | Lý do giữ |
|---|---|---|
| 0–20 (cho vay), 0–14 (huy động) %/năm | `bank.py` (clip), `model.py` (assert) | Miền hợp lệ của mục 6 CLAUDE.md, trùng assert; đưa ra YAML có thể làm clip và assert lệch nhau |
| 0.01 | sàn số dư tiền gửi/dư nợ (`depositors.py`, `borrowers.py`) | Chặn số học (tránh số dư ≤ 0), không phải tham số hành vi |
| bình quân đơn giản của lãi suất huy động đầu quý | `market_rate`, `model.py` | Định nghĩa cấu trúc, không phải hằng số; đổi là đổi công thức |
| `casa_ratio` 0.20, `npl_ratio` 0.02, `capital_ratio` 0.10, `lagged_funding_cost` 4.5 | mặc định `Bank`, `model.py` | Chỉ dùng khi dữ liệu thiếu cột (dữ liệu 8 NH có đủ `casa_ratio`, `npl_ratio`); `capital_ratio`, `npl_ratio` không vào công thức nào; `lagged_funding_cost` bị ghi đè ngay khi khởi tạo |
| các số của bộ ngân hàng giả lập (1000, 140, 0.82, 5.0, 9.2, …) | `_make_banks` | Chỉ dùng khi không nạp dữ liệu (demo/test), không phải tham số hành vi |

## 3. Kết quả chính
Nguồn: `reports/stage9a/check_stage9a.md` / `.json` (sinh bởi `python -m src.analysis.check_stage9a`; trong mẫu, không phải dự báo).

| Hạng mục | Kết quả |
|---|---|
| 13 khóa mới: YAML = mặc định code = giá trị cũ | 13/13 khớp |
| Mọi khóa `parameters` của `scenarios.yaml` có mặc định code trùng YAML | có (46 khóa) |
| Golden `term` khớp bitwise | 18/18 file, sai lệch lớn nhất 0 |
| Golden `total` khớp bitwise | 18/18 file, sai lệch lớn nhất 0 |

Ngoài ra (kiểm tra thủ công trong scratchpad, không lưu vào repo): băm SHA-256 của `history` + `bank_history` cho 144 tổ hợp (6 file cấu hình `scenarios*.yaml` × A/B/C × 4 seed × có/không dữ liệu) trước và sau thay đổi trùng nhau hoàn toàn. Điều này thể hiện thay đổi hành vi = 0, kể cả với các cấu hình học thích nghi và `macro`.

## 4. Kiểm tra
| Hạng mục | Kết quả |
|---|---|
| pytest | 171 passed, 1 xfailed (trước: 135 passed, 1 xfailed; +36 test mới) |
| validation | 7/7 ĐẠT |
| Mục 6 CLAUDE.md | Không có cấu hình mới tạo kết quả A/B/C; kết quả không đổi bitwise. Vẫn kiểm tra lại, 10 seed (`check_stage9a.md`). `scenarios.yaml`: max(B−A) sau CS = −0.1553, max(C−A) = −0.1551 (≤ 0); trước CS lệch 0; LS cho vay [8.131; 12.405], huy động [4.939; 7.435]; max(loans − LDR·deposits) = 0 (ràng buộc chặt ở biên, không vượt); trễ: sai số công thức dùng `lagged_funding_cost` = 0, dùng chi phí vốn cuối quý = 0.0220 → ĐẠT. `scenarios_macro.yaml`: −0.1499 / −0.1499; lệch trước CS 0; cho vay [7.655; 12.405], huy động [3.819; 7.011]; −9.521e+05; trễ 0 / 0.0796 → ĐẠT |
| Golden | không đổi (D8 không cần dùng) |
| Tái lập | có: chạy `check_stage9a` hai lần cho file giống hệt (MD5 json 85fc318e…, md 22c60b0e…) |
| Chạy nhanh `main.py --runs 2 --sensitivity-runs 1` | chạy hết, mã thoát 0 |

## 5. Quyết định mặc định đã áp dụng
| # | Câu hỏi | Mặc định đã dùng | Căn cứ (mục 8 CLAUDE.md / LO_TRINH) | Hệ quả nếu Huy chọn khác |
|---|---|---|---|---|
| 1 | Chặn `demand_pressure` ±0.5 dùng 1 hay 2 khóa | 1 khóa đối xứng `demand_pressure_cap` (LO_TRINH ghi "±0.5"); tương tự `depositor_max_growth` vốn đã đối xứng trong code | Bảo thủ, giữ đúng dạng công thức | Tách 2 khóa: sửa nhỏ, không đổi kết quả |
| 2 | Ngoài danh sách LO_TRINH, có đưa ra YAML `target_margin` 3.2, `funding_cost_add` 0.15 và 5 hệ số logistic tuân thủ không | Có, giá trị giữ nguyên (thuộc "rà soát mọi hằng số hành vi"). `target_margin` cần cho lưới biên tổng của GD9 | LO_TRINH GD9a gạch đầu dòng 1; D5 | Không ảnh hưởng kết quả; chỉ là tham số lộ ra |
| 3 | Đưa miền hợp lệ 0–20/0–14 và sàn 0.01 ra YAML không | Không (giữ cứng, lý do ở mục 2) | Bảo thủ; miền hợp lệ là kiểm tra của mục 6 | Nếu đưa ra phải đồng bộ với assert trong `model.py` |
| 4 | Dữ liệu có cột `target_margin` thì sao | Dữ liệu được ưu tiên (giữ đúng hành vi cũ) | Hành vi = 0 | Ngược lại sẽ đổi kết quả với dữ liệu có cột này (hiện không có) |

## 6. CẦN HUY QUYẾT ĐỊNH
- **Cập nhật CLAUDE.md mục 4.2** (người thực thi không được sửa CLAUDE.md): danh sách "Các hằng số cứng hiện có: `0.018` và `1.35` (`bank.py`), `reference_rate=9.5`, `base_growth`, `margin_floor=2.2`" và câu "mặc định trong `model.py` (`max_loan_to_deposit=1.15`, `policy_month=12`) đang khác YAML" đã lỗi thời: code hiện dùng 1.60 và 14, và mọi hằng số hành vi đã ở YAML. Đề xuất: Huy sửa mục 4.2 cho khớp (có thể trỏ tới `tests/test_constants_yaml.py`). Không ảnh hưởng các giai đoạn sau, nên không chặn GD9.
- Không có lựa chọn kinh tế/tham số mới nào: mọi giá trị giữ nguyên.

## 7. Hạn chế và rủi ro
- Các khóa mới cho phép GD9 đổi `deposit_ldr_target`, `depositor_base_growth`, `borrower_base_growth`, chặn tăng trưởng và `target_margin`. Từ đây, đổi các giá trị này **sẽ** đổi kết quả và golden. Golden chỉ khớp với giá trị mặc định trong `scenarios.yaml`; cấu hình hiệu chỉnh phải nằm ở `configs/scenarios_calibrated.yaml` (D5).
- Test AST `p.get("khóa", hằng)` chỉ bắt được mặc định dạng literal trong `model.py`. Mặc định mới viết dạng biểu thức sẽ không được test này kiểm tra (test sẽ báo khóa YAML thiếu trong danh sách mặc định, nên vẫn bị phát hiện).
- Mặc định trong chữ ký hàm khởi tạo agent (vd. `Bank(target_margin=3.2)`) vẫn còn, để agent dùng được độc lập. Test kiểm tra các mặc định này trùng YAML.

## 8. Phản biện (điều phối viên điền nguyên văn báo cáo cuối của reviewer-abm, số vòng)

**Số vòng: 1.** Reviewer kết luận ĐẠT; chỉ có 2 vấn đề NHỎ, nằm ngoài `src/agents/` và `src/core/`. Hai vấn đề này không sửa ở GD9a mà giao làm việc đầu tiên của GD9, vì chính GD9 sẽ đổi các tham số liên quan.

Nguyên văn báo cáo cuối của reviewer-abm:

> KẾT LUẬN: ĐẠT
>
> GD9a không làm đổi kết quả mô hình ở bất kỳ bit nào. Tôi đã kiểm tra độc lập với HEAD e4c1493 trên 162 tổ hợp, không lệch tổ hợp nào. Mục 6 CLAUDE.md đạt trên cả 3 bộ dữ liệu. Hai vấn đề còn lại đều NHỎ, nằm ngoài `src/agents/` và `src/core/`, không chặn commit.
>
> Tóm tắt thay đổi:
> - 13 hằng số trước đây viết cứng trong `bank.py`, `borrowers.py` và `regulator.py` (ngưỡng LDR 0.82, chặn ±0.5, chặn tăng trưởng dư nợ −0.04/0.035, `funding_cost_add` 0.15, `target_margin` 3.2, 5 hệ số logistic tuân thủ) nay được đọc từ YAML. Với `depositors.py`, `depositor_base_growth` 0.004 và `depositor_max_growth` 0.04 vốn đã là tham số khởi tạo của agent; GD9a chỉ cho `ABMModel` truyền giá trị từ YAML và sửa docstring.
> - Giá trị và công thức giữ nguyên, chỉ thay chữ số bằng biến.
> - `target_margin` được gán bằng `setdefault`, nên cột `target_margin` trong dữ liệu (nếu có) vẫn được ưu tiên như cũ.
> - Có thêm kiểm tra báo lỗi khi giá trị không hợp lệ. Thứ tự trong `step()` không đổi.
>
> KỸ THUẬT:
> - **pytest: đạt.** 171 passed, 1 xfailed. Ca xfail là `test_relative_drift_small_scenario_a[path3-total]`, đã có từ trước. Không có thay đổi nào với file đã track trong `tests/`; chỉ thêm file mới `tests/test_constants_yaml.py`. `tests/golden/` và `tests/golden_total/` không bị tạo lại.
> - **validation: đạt.** 7/7 mục ĐẠT, kết quả tổng hợp True.
> - **Hành vi = 0: đạt.** Tôi tự chạy bản HEAD (git worktree tạm trong scratchpad, đã xóa) và bản mới, so bằng `assert_frame_equal(check_exact=True)` cả `history` lẫn `bank_history`. Phạm vi: 6 file `configs/scenarios*.yaml` (gồm adaptive, relative, nonim, macro, total) × 3 bộ dữ liệu (2023Q1, 2026Q3, giả lập) × A/B/C × 3 seed = 162 tổ hợp, 0 lệch. Golden term và golden_total khớp bitwise (test mới dùng `check_exact=True`; `test_golden.py` cũ dùng atol=1e-9 và vẫn qua). Đọc diff: biểu thức giữ nguyên dạng, ví dụ `-model.demand_pressure_cap` so với `-0.5`, và `+ self.model.funding_cost_add` đúng vị trí cũ.
> - **Mặc định code trùng YAML: đạt.** Test AST xác nhận cả 46 khóa `parameters` có `p.get` với mặc định trùng YAML. Mặc định trong chữ ký hàm khởi tạo của Bank, DepositorBlock, BorrowerBlock và Regulator cũng trùng YAML. Tôi đã đọc lại diff `model.py` để đối chiếu.
> - **Hằng số bị bỏ sót: đạt.** Tôi grep các số còn lại trong `src/agents/` và `src/core/`. Chỉ còn miền 0–20 và 0–14, sàn 0.01, các mặc định của Bank khi dữ liệu thiếu cột (casa 0.20, npl, capital, `lagged_funding_cost` bị ghi đè ngay khi khởi tạo) và các số của bộ ngân hàng giả lập. Bảng rà soát trong GD9a.md đã nêu đủ và có lý do; tôi không thấy hằng số hành vi nào bị sót. `sensitivity_grid` dùng danh sách tham số cố định, nên 13 khóa mới không lọt vào phân tích độ nhạy.
> - **Ưu tiên cột `target_margin` từ dữ liệu: đạt.** `d.setdefault("target_margin", ...)` chỉ điền khi thiếu cột. Hai file 2023Q1 và 2026Q3 đều không có cột này, nên dùng 3.2 như cũ.
> - **`data/clean/`: đạt**, không bị sửa.
> - **README: đạt.** Đã cập nhật bảng tham số, đoạn YAML mẫu và mục hằng số cố định.
> - **Số liệu báo cáo: đạt.** Tôi chạy lại `python -m src.analysis.check_stage9a` trên một bản sao trong scratchpad (để không ghi đè repo). MD5 của json (85fc318e…) và md (22c60b0e…) trùng file trong `reports/stage9a/`. Tôi tính lại độc lập với 10 seed, dữ liệu 2023Q1, `scenarios.yaml`: max(B−A) = −0.1553, max(C−A) = −0.1551, TB lãi suất cho vay sau chính sách A/B/C = 9.9342 / 9.5321 / 9.5086, cho vay trong [8.131; 12.405], huy động trong [4.939; 7.435]. Mọi số trùng GD9a.md.
>
> KINH TẾ:
> 1. **Mục 6: đạt** trên cả 3 bộ dữ liệu (10 seed, `scenarios.yaml`). Trước chính sách, A/B/C lệch nhau 0. LDR không vượt trần 1.60.
>
>    | Dữ liệu | max(B−A) | max(C−A) | Cho vay | Huy động | LDR max |
>    |---|---:|---:|---|---|---:|
>    | 2023Q1 | −0.1553 | −0.1551 | [8.131; 12.405] | [4.939; 7.435] | 1.600 |
>    | 2026Q3 | −0.1702 | −0.1700 | [7.872; 11.448] | [5.214; 7.559] | 1.600 |
>    | giả lập | −0.2061 | −0.2061 | [8.072; 9.295] | [5.018; 5.628] | 1.122 |
>
>    Với `scenarios_macro.yaml` (theo check_stage9a): −0.1499 / −0.1499. Kiểm tra trễ `lagged_funding_cost`: sai số 0 (cách tính thay thế lệch 0.0220), đạt.
> 2. **Trôi hệ thống: không áp dụng.** Không có cơ chế mới; kết quả trùng bitwise với HEAD.
> 3. **Chạm biên: không áp dụng** (không đổi so với trước). Ghi nhận từ trước: LDR chạm trần 1.60 ở 6.2% quan sát ngân hàng-quý với dữ liệu 2023Q1 và 8.1% với 2026Q3.
> 4. **Tín hiệu có tổng không đổi: không áp dụng.**
> 5. **Ngưỡng có đạt được không: không áp dụng** (giá trị không đổi). Lưu ý cho GD9: từ nay `deposit_ldr_target` và `target_margin` đổi được, nên bất kỳ giá trị nào được chọn ở GD9 đều phải kiểm tra lại câu này.
> 6. **Vòng khép kín: không áp dụng.**
> 7. **Tác động chính sách: không đổi.** B−A và C−A trùng bitwise với HEAD.
> 8. **Nhiễu lẫn tuân thủ: không đổi.** Các hệ số logistic tuân thủ chỉ được đưa ra YAML, giá trị giữ nguyên.
> 9. **Phụ thuộc dữ liệu hay cơ chế:** đã chạy cả 3 bộ dữ liệu (xem câu 1), không có hiện tượng bất thường mới.
>
> VẤN ĐỀ CẦN SỬA (xếp theo mức độ nghiêm trọng):
> 1. [NHỎ] Các script hiệu chỉnh vẫn giữ bản sao cứng của các hằng số vừa đưa ra YAML, và một số comment đã lỗi thời.
>    - Bằng chứng: `src/calibration/estimate_equations.py` dòng 40, 47, 51 có `FUNDING_CONST = 0.15`, `TARGET_MARGIN = 3.2`, `DEPOSITOR_BASE = 0.004`, kèm comment "KHÔNG nằm trong YAML" (nay đã sai). `src/calibration/estimate_deposit_equation.py` dòng 39 và 49 có `PIVOT = 0.82`, `FUNDING_CONST = 0.15`.
>    - Không ảnh hưởng mô hình. Rủi ro: GD9 sẽ thử các giá trị khác cho ngưỡng LDR và `target_margin`; nếu dùng lại các script này mà không đọc YAML thì sẽ lệch khỏi mô hình mà không ai biết.
>    - Hướng sửa: đọc từ `cfg["parameters"]` với cùng mặc định, ở GD9a hoặc đầu GD9.
> 2. [NHỎ] Các file cấu hình biến thể (`scenarios_macro.yaml`, `scenarios_adaptive*.yaml`, `scenarios_total.yaml`) không có 13 khóa mới mà dựa vào mặc định trong code.
>    - Hiện đúng, vì mặc định trùng YAML và đã có test bảo vệ.
>    - GD9 lấy `scenarios_macro.yaml` làm cấu hình nền. Khi tạo `scenarios_calibrated.yaml` cần ghi rõ các khóa này, để không bị phụ thuộc ngầm vào mặc định trong code.
>
> CẦN NGƯỜI DÙNG/NHÓM QUYẾT ĐỊNH:
> - Mục 4.2 CLAUDE.md đã lỗi thời (danh sách "hằng số cứng hiện có"; câu "mặc định model.py 1.15/12 khác YAML", trong khi code nay dùng 1.60/14 trùng YAML). Đây là việc của Huy, người thực thi đã ghi đúng vào mục "CẦN HUY QUYẾT ĐỊNH".
> - Chọn một khóa đối xứng (`demand_pressure_cap`) hay hai khóa sàn/trần riêng cho chặn `demand_pressure` và chặn tăng trưởng tiền gửi. Lựa chọn này không đổi kết quả hiện tại, nhưng quyết định dạng tham số mà GD9 có thể hiệu chỉnh.
> - Có đưa miền hợp lệ 0–20 / 0–14 và sàn 0.01 ra YAML hay không. Tôi đồng ý giữ cứng như mặc định đã chọn, nhưng việc này cần Huy xác nhận.
>
> Tôi không sửa hay commit file nào trong repo. Worktree tạm trong scratchpad đã được xóa, `git worktree list` chỉ còn repo chính.

### Quyết định đang mở từ phản biện (đã thêm vào TRANG_THAI.md)
- Q3: Cập nhật CLAUDE.md mục 4.2. Mặc định: giữ nguyên CLAUDE.md, Huy tự sửa.
- Q4: Chặn `demand_pressure` và tăng trưởng tiền gửi dùng một khóa đối xứng hay tách sàn/trần. Mặc định: một khóa đối xứng.
- Q5: Có đưa miền 0–20 / 0–14 và sàn 0.01 ra YAML không. Mặc định: giữ cứng.
