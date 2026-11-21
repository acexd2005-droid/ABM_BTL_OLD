# GD9 – Hiệu chỉnh bằng mô phỏng và kiểm định ngoài mẫu lịch sử

**Trạng thái:** HOÀN THÀNH · **Ngày:** 2026-11-21 · **Commit:** (điều phối viên điền)

## 1. Mục tiêu và phạm vi
Hiệu chỉnh mô hình bằng mô phỏng kịch bản A. Cấu hình nền là `scenarios.yaml` + `scenarios_macro.yaml` (D2), dữ liệu 8 NH, khởi tạo 2023Q1. Cửa sổ hiệu chỉnh là 2023Q2–2025Q2; phần ngoài mẫu 2025Q3–2026Q3 không dùng để chọn tham số. Các bước:
- Bước 1: tăng trưởng nền và ngưỡng chặn tính theo quy tắc, không tối ưu.
- Bước 2: lưới 1536 bộ (λ × biên tổng × base_step × δ × ngưỡng LDR).
- Bước 3: kiểm định ngoài mẫu, so với cấu hình GĐ8 và hai mốc ngây thơ.
- Bước 4: ghi `configs/scenarios_calibrated.yaml` và kiểm tra mục 6.

Ngoài lộ trình, làm thêm 5 việc điều phối viên chuyển từ phản biện GD9a.

KHÔNG làm:
- không hiệu chỉnh σ, ε (GĐ7: không nhận diện được);
- không hiệu chỉnh `policy_pressure`, `policy_step` (D6);
- không đổi giá trị nào trong `scenarios.yaml` (D5), không đổi golden;
- không chạy A/B/C 60 lần và không phân tích độ nhạy (thuộc GD10).

## 2. Đã làm
- **Việc 1 (làm đầu tiên):** sửa hai script ước lượng để đọc hằng số từ `cfg["parameters"]`, mặc định giữ nguyên.
  - `src/calibration/estimate_equations.py`: thêm hàm `_read_param(key, default)`. `FUNDING_CONST`, `TARGET_MARGIN`, `DEPOSITOR_BASE` đọc từ `funding_cost_add`, `target_margin`, `depositor_base_growth`. Bỏ các comment sai "KHÔNG nằm trong YAML".
  - `src/calibration/estimate_deposit_equation.py`: `PIVOT`, `CLIP` đọc từ `deposit_ldr_target`, `demand_pressure_cap`; `FUNDING_CONST` nhập từ `estimate_equations`.
  - Kiểm tra: chạy lại GĐ7, 7b, 7c vào thư mục tạm. Cả 17 file trùng **từng byte** với `reports/calibration/` (12 file GĐ7/7b, 5 file GĐ7c).
- **Khóa tùy chọn mới `depositor_min_growth`** (Q4, việc 3), là sàn riêng của tăng trưởng tiền gửi.
  - `configs/scenarios.yaml` để `null`, nghĩa là sàn = `−depositor_max_growth` như hành vi cũ.
  - `src/core/model.py` đọc khóa bằng `p.get("depositor_min_growth", None)` và báo lỗi nếu min > max.
  - `src/agents/depositors.py` thêm tham số `min_growth=None`, sàn tính bằng `-max_growth if min_growth is None else min_growth`.
  - Công thức không đổi khi để `null`: golden `term` và `golden_total` vẫn qua bitwise (`tests/test_constants_yaml.py`). Có thêm test mới so bản có khóa với bản bỏ khóa: trùng chính xác cho A/B/C.
- **`src/calibration/calibrate_stage9.py` (mới):** chạy Bước 1–4 và sinh mọi file trong `reports/calibration/stage9/`, gồm cả `summary_stage9.md`. Script tự ghi `configs/scenarios_calibrated.yaml`.
  - Một lần chạy kịch bản A mất khoảng 1.5 ms. Cả 4 × 1536 bộ lưới, lưới chẩn đoán và mục 6 chạy hết trong khoảng 10 giây, nên không cần chạy song song (việc 5).
  - Kịch bản A không dùng RNG (đã kiểm: hai seed cho kết quả trùng), nên mỗi bộ tham số chỉ chạy 1 lần.
- **Đăng ký trước:** `reports/calibration/stage9/DANG_KY_TRUOC.md` viết trước khi chạy lưới. Tài liệu ghi hàm mục tiêu, quy tắc Bước 1, các biến thể và tiêu chí chọn bản chính.
  - Phụ lục (ghi rõ là thêm SAU khi thấy kết quả lưới chính) có 2 chẩn đoán CHỈ để báo cáo: bộ tốt nhất với λ trong CI GĐ7, và lưới mở rộng.
- **`configs/scenarios_calibrated.yaml` (mới, sinh tự động, việc 2):** ghi **tường minh** 36 khóa, gồm đủ 13 khóa GD9a, `depositor_min_growth`, các khóa macro (D1–D3), `loan_spread_add` 1.35 (D7), σ, ε, `policy_*`. Mỗi khóa có comment ghi nguồn giá trị.
- **`tests/test_calibration_stage9.py` (mới, 15 test; 2 test thêm ở vòng sửa 2):**
  - script ước lượng đọc YAML và không còn bản sao cứng;
  - `depositor_min_growth`: mặc định giữ hành vi cũ, sàn bất đối xứng hoạt động đúng, giá trị không hợp lệ bị từ chối;
  - quy tắc Bước 1 khớp phép tính độc lập; loại đúng 3 quan sát bất thường;
  - lưới có 1536 điểm và ánh xạ biên tổng → `target_margin` đúng;
  - hàm mục tiêu: chỉ tính month 1–9, bằng 0 khi khớp hoàn toàn; kịch bản A tất định;
  - công thức mốc ngây thơ ON đúng;
  - YAML hiệu chỉnh có đủ khóa, khớp bộ tốt nhất, giữ nguyên σ, ε, policy;
  - cấu hình hiệu chỉnh đạt mục 6; bộ tốt nhất đúng là argmin J.
- **Vòng sửa 2:**
  - `src/calibration/confounding_stage9.py` (mới, được `calibrate_stage9` gọi cuối `main`, chạy riêng được): tự tính nhiễu lẫn tuân thủ cho macro GĐ8 và hiệu chỉnh GD9 (10 seed, quý 15–18). Xuất `confounding_stage9.csv/.md`, `ldr_cap_stage9.csv`, `ldr_cap_2026q3_stage9.csv` và nhúng bảng vào `summary_stage9.md`. Không chạy lại lưới, không đổi tham số hay nghiệm.
  - `src/core/model.py`: nếu `depositor_min_growth > 0` thì phát `UserWarning` (vẫn cho phép; sàn thường ≤ 0). Mặc định `null` không đổi, golden bitwise vẫn qua. Ghi chú dấu trong `configs/scenarios.yaml`. Thêm test.
- `README.md`: thêm dòng `depositor_min_growth` vào bảng tham số và đoạn YAML mẫu, thêm mục "Hiệu chỉnh bằng mô phỏng (Giai đoạn 9)" và cây thư mục `configs/`.
- `docs/ke_hoach/TRANG_THAI.md`: thêm Q4b, Q6, Q7 vào bảng "Quyết định đang mở".

## 3. Kết quả chính
Mọi số trong mục này lấy từ `reports/calibration/stage9/summary_stage9.md` và các file CSV cùng thư mục.

### Bước 1 – Tăng trưởng (theo quy tắc, trong mẫu 2023Q2–2025Q2) – `growth_rules_stage9.csv`
| Biến thể | TG nền | DN nền | Sàn / trần TG | Sàn / trần DN | N |
|---|---:|---:|---|---|---:|
| **bất đối xứng, đủ dữ liệu (chính)** | 0.0398 | 0.0448 | −0.0142 / 0.1732 | 0.0012 / 0.1395 | 72 |
| đối xứng, đủ dữ liệu | 0.0398 | 0.0448 | ±0.1732 | 0.0012 / 0.1395 | 72 |
| bất đối xứng, loại bất thường | 0.0371 | 0.0438 | −0.0143 / 0.1193 | 0.0029 / 0.1371 | 69 |
| đối xứng, loại bất thường | 0.0371 | 0.0438 | ±0.1193 | 0.0029 / 0.1371 | 69 |

- Ba quan sát bất thường bị loại là HDBank 2023Q2, MB Bank 2023Q4 và MB Bank 2024Q4. MB Bank 2025Q4 nằm ngoài cửa sổ nên không thuộc diện loại.
- LDR bình quân theo ngân hàng-quý trong cửa sổ là 1.0900; đây là ứng viên ngưỡng LDR thứ hai của lưới.
- Phân vị tiền gửi lệch hẳn về một phía (−0.0142 so với 0.1732). Một khóa đối xứng 0.04 như cũ thì gần bằng chính mức nền 0.0398, nên chặn sẽ mất tác dụng.

### Bước 2 – Lưới (kịch bản A, trong mẫu) – `best_by_variant_stage9.csv`, `profile_stage9.csv`, `corr_top50_stage9.csv`
- **Bộ tốt nhất (biến thể chính):** λ = 0.45, biên tổng = 3.8 (`target_margin` 2.45), base_step = 0, δ = 0.07, ngưỡng LDR = 1.0900. Kết quả J = 0.4548, với RMSE_L = 0.4620 và RMSE_D = 0.4477.
  - Cả 4 biến thể Bước 1 cho **cùng một bộ tham số**, J nằm trong khoảng 0.4548–0.4561. Lựa chọn đối xứng hay bất đối xứng hầu như không ảnh hưởng kết quả.
  - Để so sánh, cấu hình GĐ8 có RMSE thô trong mẫu là 1.0879 (cho vay) và 0.5325 (huy động).
- **Nghiệm nằm ở biên lưới với 4/5 tham số:** λ ở cận trên 0.45; biên tổng, base_step và δ đều ở cận dưới.
- **λ = 0.45 nằm NGOÀI CI GĐ7 [0.158; 0.395].** Bộ tốt nhất có λ trong CI là λ = 0.35, cho J = 0.4994.
- **Hồ sơ hàm mục tiêu** (biên độ của min J theo từng tham số):

  | Tham số | Biên độ min J | Nhận xét |
  |---|---:|---|
  | biên tổng | 0.3884 | nhận diện rõ |
  | λ | 0.3655 | nhận diện rõ |
  | δ | 0.2124 | nhận diện vừa |
  | ngưỡng LDR | 0.0390 | gần phẳng |
  | base_step | 0.0379 | gần phẳng |

  Hai tham số gần phẳng là những tham số khó nhận diện từ dữ liệu.
- **Tương quan trong top 50 đều yếu:** λ–biên tổng 0.293, δ–LDR 0.351.
- **Chẩn đoán lưới mở rộng** (`diagnostics_stage9.csv`, `grid_ext_stage9.csv`; chỉ báo cáo):
  - Với λ 0.10–1.00, biên tổng 3.0–3.8, δ 0–0.07, nghiệm là λ = 0.25 (nằm trong CI), biên tổng 3.0 (**lại ở biên**), δ = 0, với J = 0.3649.
  - Trên lưới này, J gần như phẳng theo λ trong khoảng 0.25–0.40 (0.3649–0.3729). Như vậy λ và biên tổng bù trừ cho nhau.
  - Biên tổng mà mô hình ưa (3.0–3.8) thấp hơn biên dữ liệu μ = 4.59 (GĐ7, PT2). Lý do: LS huy động của mô hình cao hơn thực trung bình +0.33 điểm % trong mẫu, làm chi phí vốn cao lên, nên biên phải thấp xuống để bù.
  - Bộ của lưới mở rộng khớp kém hơn ở ngoài mẫu (xem Bước 3), là dấu hiệu quá khớp.

### Bước 3 – Ngoài mẫu 2025Q3–2026Q3 (5 quý) – `oos_stage9.csv`
Mô hình và mốc (iii) đều được cấp **ON thực** trong giai đoạn ngoài mẫu. Đây là lợi thế thông tin, nên kết quả không phải dự báo thật.

| Cấu hình | Cho vay: RMSE thô / khử mức / sai số TB | Huy động: RMSE thô / khử mức / sai số TB | Biên độ cho vay (thực 1.7147) |
|---|---|---|---:|
| **Hiệu chỉnh (chính)** | 0.4767 / 0.4609 / +0.1217 | 0.5855 / 0.2801 / +0.5142 | 0.5149 |
| GĐ8 chưa hiệu chỉnh | 1.0930 / 0.4569 / +0.9930 | 0.6908 / 0.2826 / +0.6303 | 0.5265 |
| Ngây thơ: giữ 2025Q2 | 1.0447 / 0.6449 / −0.8219 | 0.8318 / 0.5747 / −0.6014 | 0 |
| Ngây thơ: ON | 0.6429 / 0.3896 / −0.5114 | 0.4478 / 0.3404 / −0.2909 | 0.9923 |
| (chẩn đoán) λ trong CI, 0.35 | 0.5000 / 0.4923 / +0.0871 | 0.5824 / 0.2804 / +0.5105 | 0.4253 |
| (chẩn đoán) lưới mở rộng | 0.8960 / 0.5648 / −0.6956 | 0.5354 / 0.2896 / +0.4503 | 0.2242 |

- Hiệu chỉnh chủ yếu sửa **mức** của LS cho vay. Sai số trung bình ngoài mẫu giảm từ +0.99 xuống +0.12. RMSE khử mức gần như không đổi so với GĐ8 (0.461 so với 0.457), nghĩa là hình dạng đường đi không tốt hơn.
- Mô hình chỉ tái tạo được khoảng 30% biên độ tăng của LS cho vay ngoài mẫu (0.51 so với 1.71).
- Mốc ngây thơ ON thắng mô hình ở RMSE thô của LS huy động (0.448 so với 0.586) và ở RMSE khử mức của LS cho vay (0.390 so với 0.461). Mô hình hiệu chỉnh thắng ở RMSE thô của LS cho vay (0.477 so với 0.643).
- Trên toàn chuỗi 2023Q2–2026Q3, tỷ lệ biên độ giảm của chữ V (LS cho vay) tăng từ 0.4458 (GĐ8) lên 0.6173. Quý đáy của mô hình là 2024Q4, thực là 2025Q1. Với LS huy động, quý đáy trùng thực (2024Q2).
- So với `summary_stage8.md`, cấu hình GĐ8 ở đây cho RMSE khử mức toàn chuỗi 0.5049 và tỷ lệ V 0.4458. Hai số này khớp số đã báo ở GĐ8 (0.505 và 0.45).

### Bước 4 – Ngưỡng có thực sự đạt tới không (việc 4) – `thresholds_stage9.csv`, `growth_ldr_stage9.csv`
- **`deposit_ldr_target` = 1.0900: có đạt tới và có bị vượt qua.** Xét month 1–14, LDR đầu quý nằm trong [0.916; 1.600]. 83.0% số ngân hàng-quý ở trên ngưỡng, 6/8 ngân hàng có quan sát ở cả hai phía ngưỡng, 2.7% chạm chặn ±0.5. Ngược lại, với 0.82 (GĐ8), 100% quan sát ở trên ngưỡng và không ngân hàng nào xuống dưới, tức áp lực huy động luôn dương.
- **Biên mục tiêu 3.8: có đạt tới.**
  - Biên thực (`loan_rate − lagged_funding_cost`) trung bình 3.9990 trong month 1–14, và 50.9% số ngân hàng-quý có biên thực ≥ mục tiêu.
  - Chênh tuyệt đối trung bình giữa biên thực và mục tiêu là 0.2383 ở quý 14 và 0.0317 ở quý 18, tức biên thực hội tụ về mục tiêu.
- **Chạm biên:**
  - chặn tăng trưởng tiền gửi: chạm trần 0%, chạm sàn 0.9%;
  - chặn tăng trưởng dư nợ mong muốn: 0%;
  - **trần LDR 1.60: chạm ở 3.6% số ngân hàng-quý trong month 1–14 và 9.7% trong month 1–18**, so với 0% ở GĐ8. Vietcombank chạm từ month 11 (2025Q4); Techcombank và MB Bank chạm từ month 16. LDR thực của Vietcombank chỉ khoảng 0.98–1.02.
  - Nguyên nhân: tăng trưởng tổng của mô hình lệch khỏi dữ liệu. Trong mẫu, tiền gửi tăng 0.0298/quý so với thực 0.0398, dư nợ tăng 0.0602/quý so với thực 0.0448.
  - Cơ chế: tăng trưởng nền được đặt bằng trung bình của tổng, nhưng còn cộng thêm các số hạng σ(r_i − r̄) và −ε(r^L_i − 9.5). Các ngân hàng lớn có LS thấp, nên tổng lệch đi.
  - Chẩn đoán (`diag_growth_stage9.csv`, không đổi bộ chính): bù một lần phần lệch vào base_growth thì tăng trưởng tổng khớp (0.0395 / 0.0449), LDR lớn nhất ở quý 14 còn 1.238, không còn chạm trần, J giảm từ 0.4548 xuống 0.4407. Đây là Q7.

## 4. Kiểm tra
| Hạng mục | Kết quả |
|---|---|
| pytest | 186 passed, 1 xfailed (trước: 171 passed, 1 xfailed; +15 test mới; ca xfail cũ `test_relative_drift_small_scenario_a[path3-total]`) |
| validation | 7/7 ĐẠT, kết quả tổng hợp True |
| Mục 6 CLAUDE.md – `scenarios_calibrated.yaml`, 10 lần chạy A/B/C (`section6_stage9.csv`) | ĐẠT, chi tiết ở 5 dòng dưới |
| – B, C không cao hơn A sau CS | max(B−A) = −0.1529, max(C−A) = −0.1528 (≤ 0; đây là max theo quý và seed, KHÔNG phải mức trung bình, xem mục 7). TB LS cho vay sau CS A/B/C = 8.4903 / 8.0939 / 8.0813 |
| – A/B/C trùng nhau trước CS | lệch tối đa 0 |
| – Miền lãi suất | cho vay [6.8475; 12.1699], huy động [3.6953; 6.9743] |
| – Ràng buộc LDR | max(loans − 1.60·deposits) = 0: chặt ở trần, không vượt |
| – Phản ứng trễ | sai số khi dùng `lagged_funding_cost` = 0; khi dùng chi phí vốn cuối quý = 0.0769 |
| Mục 6 – `scenarios_macro.yaml` (GĐ8, để đối chiếu) | ĐẠT: −0.1499 / −0.1499; lệch trước CS 0; trễ 0 / 0.0796 |
| Golden | không đổi: `term` và `golden_total` qua bitwise (`test_constants_yaml.py`, `test_golden.py`) |
| Tái lập | có: chạy `calibrate_stage9` hai lần, MD5 của 18 file trong `stage9/` và `scenarios_calibrated.yaml` trùng nhau. Đọc lại YAML cho đường đi lệch 0 so với bộ tốt nhất trong bộ nhớ (`meta_stage9.json`) |
| Kết quả GĐ7/7b/7c sau việc 1 | 17/17 file trùng từng byte |
| Chạy nhanh `main.py --runs 2 --sensitivity-runs 1` | chạy hết, mã thoát 0, cả với `--config configs/scenarios_calibrated.yaml` lẫn mặc định |

## 5. Quyết định mặc định đã áp dụng
| # | Câu hỏi | Mặc định đã dùng | Căn cứ (mục 8 CLAUDE.md / LO_TRINH) | Hệ quả nếu Huy chọn khác |
|---|---|---|---|---|
| 1 | Chặn tiền gửi bất đối xứng (Q4) | Thêm khóa tùy chọn `depositor_min_growth` (mặc định `null` = hành vi cũ, golden không đổi). Bản chính dùng bất đối xứng P2.5/P97.5; bản đối xứng max(\|P2.5\|, \|P97.5\|) cũng chạy và báo cáo | Chỉ đạo của điều phối viên; mục 8.2. Tiêu chí chọn bản chính ghi trước: theo nguyên văn quy tắc LO_TRINH | Chọn bản đối xứng: cùng bộ tham số, J 0.4550 thay vì 0.4548; chỉ đổi 2 dòng YAML |
| 2 | Phân vị tính trên quan sát nào | Theo ngân hàng-quý (72 quan sát), vì chặn áp cho từng ngân hàng. Tăng trưởng nền tính trên tổng 8 NH | LO_TRINH: "gộp 8 NH, cùng trọng số với cách mô hình tổng hợp" | Nếu tính phân vị trên chuỗi tổng (9 điểm) thì khoảng chặn hẹp hơn nhiều |
| 3 | "LDR bình quân dữ liệu" | Bình quân đơn giản theo ngân hàng-quý trong cửa sổ = 1.0900 | Ngưỡng áp cho từng ngân hàng | LDR gộp (tổng dư nợ/tổng tiền gửi) thấp hơn (khoảng 1.03–1.10) |
| 4 | Loại bất thường | Loại 3 ngân hàng-quý trong cửa sổ (MB Bank 2025Q4 ngoài cửa sổ). Bản chính dùng đủ dữ liệu | LO_TRINH: "chạy thêm bản loại chúng" | Cùng bộ tham số, J 0.4558 |
| 5 | Mốc ngây thơ (iii) cho LS huy động | Áp cùng công thức r_2025Q2 + 0.45·(ON_{t−1} − ON_2025Q1) cho cả hai chuỗi | LO_TRINH ghi "r_t" chung | Hệ số 0.45 vốn lấy từ phương trình cho vay; với LS huy động chỉ dùng làm mốc so sánh |
| 6 | Nghiệm ở biên lưới, λ ngoài CI | Giữ argmin của lưới đã duyệt trong YAML. Hai chẩn đoán (λ trong CI, lưới mở rộng) chỉ báo cáo, ghi trong phụ lục đăng ký trước | Mục 8.2: không đổi tiêu chí sau khi có kết quả | Xem mục 6 (Q6) |
| 7 | Lệch tăng trưởng tổng / chạm trần LDR | Giữ quy tắc Bước 1 đã duyệt; bản bù độ lệch chỉ chẩn đoán | LO_TRINH Bước 1 "quy tắc đặt trước, không tối ưu" | Xem mục 6 (Q7) |
| 8 | Tham số không thuộc lưới (`macro_dep_speed`, `macro_dep_spread`, `funding_cost_add`, `demand_pressure_cap`, `deposit_cap_factor`, hệ số tuân thủ, `borrower_reference_rate`) | Giữ giá trị hiện tại, ghi tường minh trong YAML hiệu chỉnh | D2, D3, D5, D6 | – |

## 6. CẦN HUY QUYẾT ĐỊNH
- **Q4b – Dạng chặn tăng trưởng tiền gửi.**
  - Phương án (a), đang dùng: bất đối xứng qua khóa mới `depositor_min_growth`. Đúng quy tắc LO_TRINH. Đổi lại phải thêm 1 khóa và chạm `depositors.py`, tuy mặc định vẫn giữ hành vi cũ.
  - Phương án (b): đối xứng ±0.1732, không cần khóa mới; sàn −0.17 không có căn cứ dữ liệu.
  - Hai phương án cho kết quả gần như trùng nhau. Đề xuất: giữ (a).
- **Q6 – Nghiệm ở biên lưới; λ = 0.45 nằm ngoài CI GĐ7.**
  - Phương án (a), đang dùng: giữ argmin của lưới đã duyệt. Đúng quy trình đã chốt. Nhược điểm: λ ngoài CI và biên tổng ở cận dưới, tức cực tiểu thực có thể nằm ngoài lưới.
  - Phương án (b): ràng buộc λ trong CI (λ = 0.35, cùng biên 3.8). J tăng 0.4548 → 0.4994, ngoài mẫu tương đương (RMSE thô cho vay 0.500 so với 0.477).
  - Phương án (c): mở rộng lưới biên tổng xuống dưới 3.8. Chẩn đoán cho λ = 0.25 (trong CI) nhưng biên tổng lại dừng ở cận 3.0 và ngoài mẫu xấu hơn rõ (RMSE thô cho vay 0.896, sai số TB −0.70), là dấu hiệu quá khớp. Biên thấp ở đây chủ yếu bù cho LS huy động của mô hình cao hơn thực (+0.33 trong mẫu), không phải biên thật thấp.
  - Đề xuất: (a) làm chính cho GD10, kèm độ nhạy theo λ trong CI và biên tổng (mục 7: B−A bị nhiễu lẫn tuân thủ). Đưa λ = 0.35 (hai đầu CI đã có trong kế hoạch GD10) vào độ nhạy. Sửa sai lệch mức của phương trình huy động (vd. `macro_dep_spread`) trước khi xét lại biên. Mọi thay đổi theo hướng này cần Huy duyệt.
- **Q7 – Tăng trưởng nền không tái tạo được tăng trưởng tổng; trần LDR bị chạm.**
  - Phương án (a), đang dùng: giữ quy tắc đã duyệt. Hệ quả: Vietcombank chạm trần 1.60 từ 2025Q4, trong khi thực tế khoảng 1.0.
  - Phương án (b): đổi quy tắc, chọn base_growth sao cho tăng trưởng tổng của mô hình khớp dữ liệu. Chẩn đoán: J 0.4407, không còn chạm trần.
  - Phương án (c): xem lại `borrower_reference_rate` 9.5 hoặc ε. Cách này chạm tham số GĐ7 coi là không nhận diện được.
  - Ảnh hưởng tới LS nhỏ, vì δ = 0.07 và LS cho vay không phụ thuộc dư nợ. Tuy vậy chạm trần LDR làm sai lượng tín dụng và tỷ lệ LDR trong GD10.
  - Số liệu mới (mục 7): 87.5% ngân hàng chạm trần khi khởi đầu từ 2026Q3, và 31–34% ngân hàng-quý sau CS ở chạy từ 2023Q1; B−A bị nhiễu lẫn. Đề xuất: Huy chọn (a) hoặc (b) trước GD10. Nếu chọn (b), cần chạy lại lưới.
- (Nhắc lại, không mới) Q3: CLAUDE.md mục 4.2 vẫn lỗi thời. Danh sách hằng số cứng nay thêm `depositor_min_growth`.

## 7. Hạn chế và rủi ro
- Cửa sổ hiệu chỉnh chỉ có 9 quý, một đường đi duy nhất, với 5 tham số lãi suất. J phẳng theo base_step và ngưỡng LDR, nên hai tham số này gần như không nhận diện được.
- "Ngoài mẫu" chỉ có 5 quý và mô hình được cấp ON thực; đây không phải dự báo. Mốc ngây thơ ON tốt hơn mô hình ở 2/4 thước đo chính.
- Chọn bằng mô phỏng (đường đi nhiều bước) cho λ = 0.45, khác λ ước lượng một bước của GĐ7 (0.274). Hai cách đo thứ khác nhau, và λ của mô hình còn hấp thụ sai lệch mức của phương trình huy động.
- Biên tổng hiệu chỉnh (3.8) thấp hơn biên dữ liệu (μ = 4.59) và ở cận dưới lưới. Biên thấp làm `nim_proxy` thấp, kéo theo xác suất tuân thủ trong B/C thấp hơn, nên B−A, C−A, C−B của hai cấu hình bị nhiễu lẫn.
- **Nhiễu lẫn tuân thủ và độ tin cậy B−A / C−A** (tự tính, `confounding_stage9.csv`; 10 seed, trung bình theo seed rồi theo quý 15–18; số tự tính trùng số reviewer vòng 1 đến 3 chữ số, riêng `nim_proxy` B sau CS tự tính là 3.3899 so với 3.40 của reviewer):
  - **"max(B−A) = −0.1529" ở mục 4 là max theo quý và seed, không phải mức trung bình.** Mức trung bình B−A là −0.3964 (macro GĐ8: −0.4101; max của GĐ8 là −0.1499). Hai cấu hình khác nhau ở max (−0.1529 so với −0.1499) vì so max, không so trung bình.

  | Chỉ tiêu sau CS | macro GĐ8 | hiệu chỉnh GD9 |
  |---|---:|---:|
  | B−A (TB) | −0.4101 | −0.3964 |
  | C−A (TB) | −0.4340 | −0.4090 |
  | C−B (TB) | −0.0239 | −0.0126 |
  | độ lệch chuẩn B−A theo seed | 0.0232 | 0.0300 |
  | LS cho vay A | 9.3448 | 8.4903 |
  | `nim_proxy` A / B / C | 4.5579 / 4.1473 / 4.1828 | 3.7885 / 3.3899 / 3.4117 |
  | xác suất tuân thủ TB, B / C | 0.9434 / 0.9454 | 0.8771 / 0.8794 |
  | tỷ lệ ngân hàng-quý chạm trần LDR 1.60, sau CS: A / B / C | 0 / 0 / 0 | 0.3125 / 0.3438 / 0.3438 |
  | chạm trần LDR của A: month 1–10 / 11–15 / 16–18 | 0 / 0 / 0 | 0 / 0.125 / 0.375 |

  - Mức A sau CS giảm 0.8546 (9.3448 → 8.4903). Phần lớn thay đổi của cả ba kịch bản giữa hai cấu hình là **hiệu ứng mức**. Chênh B−A giữa hai cấu hình (0.014) nhỏ so với độ lệch chuẩn theo seed (0.023–0.030), nên khác biệt này không phân biệt được với nhiễu mô phỏng.
  - Xác suất tuân thủ giảm 0.943 → 0.877 (B) và C−B co từ −0.024 xuống −0.013 (gần một nửa): tác động của "hạn chế cạnh tranh huy động" bị nhiễu lẫn bởi mức tuân thủ.
  - Trần LDR 1.60 bị chạm 31–34% số ngân hàng-quý sau CS (macro GĐ8: 0), nên một phần B−A là do ràng buộc dư nợ, không phải do cơ chế lãi suất.
  - **Khởi đầu từ `abm_initial_8nganhang_2026Q3.csv` (A, 18 quý): 87.5% ngân hàng chạm trần LDR ở quý cuối (macro GĐ8: 12.5%; `ldr_cap_2026q3_stage9.csv`). Cấu hình hiệu chỉnh KHÔNG dùng được cho chạy khởi đầu từ 2026Q3.**
  - Gợi ý cho GD10 (chưa làm ở GD9): chạy độ nhạy theo λ trong CI GĐ7 (vd. 0.158, 0.274, 0.395) và biên tổng, báo cáo B−A, C−A, C−B kèm xác suất tuân thủ; không đổi tham số ở GD9.
- B−A, C−A là kết quả của mô hình, không phải tác động chính sách thực tế.
- RMSE trong mẫu không phải dự báo.
- `depositor_min_growth` là khóa mới chạm `src/agents/depositors.py`, theo chỉ đạo của điều phối viên (việc 3). LO_TRINH GD9 không ghi rõ việc chạm agent; cần reviewer xác nhận phạm vi này.

## 8. Phản biện (điều phối viên điền nguyên văn báo cáo cuối của reviewer-abm, số vòng)

**Số vòng: 2.** Vòng 1: reviewer ĐẠT CÓ ĐIỀU KIỆN (2 vấn đề TRUNG BÌNH, 3 NHỎ). Vòng sửa 2: bổ sung định lượng nhiễu lẫn tuân thủ và trần LDR (vấn đề 1, script `src/calibration/confounding_stage9.py`), thêm cảnh báo dấu cho `depositor_min_growth` (vấn đề 4), commit nguyên trạng `DANG_KY_TRUOC.md` (vấn đề 3). Vấn đề 2 (trần LDR bị chạm tăng dần) thuộc quyết định Q7 của Huy nên KHÔNG tự sửa. Vòng sửa 2 chỉ đổi báo cáo/số liệu bổ sung và một cảnh báo; không đổi tham số hay nghiệm hiệu chỉnh; pytest 186 passed, 1 xfailed, golden bitwise.

Nguyên văn báo cáo cuối của reviewer-abm (vòng 1):

> KẾT LUẬN: ĐẠT CÓ ĐIỀU KIỆN
> (Điều kiện: Huy xác nhận phạm vi chạm src/agents/depositors.py + model.py cho khóa depositor_min_growth (Q4b), và quyết định Q6/Q7 trước GD10. Về kỹ thuật và quy trình, tôi không thấy lỗi chặn.)
>
> KỸ THUẬT
> - pytest: đạt. 184 passed, 1 xfailed (xfail cũ). validation: 7/7 ĐẠT.
> - Không có test cũ bị xóa hay nới. `git diff HEAD --stat -- tests` rỗng; chỉ có file mới tests/test_calibration_stage9.py. Golden không bị đổi (không có thay đổi nào trong tests/golden*). data/clean/ không bị sửa (git status sạch ở data/).
> - configs/scenarios.yaml chỉ thêm đúng khóa `depositor_min_growth: null` kèm comment (D5 đạt).
> - Mặc định khi TẮT = hành vi cũ. Trong depositors.py, `floor = -max_growth if min_growth is None else min_growth`, nên công thức cũ giữ nguyên. Mặc định trong code (`p.get(..., None)`) trùng YAML (null), README đã cập nhật. Test golden term/golden_total bitwise đều qua trong lần chạy pytest của tôi. Có kiểm lỗi khi min > max. Chưa có kiểm tra dấu của min (nhỏ).
> - Tái lập: tôi chạy lại `python -m src.calibration.calibrate_stage9 --outdir <scratchpad> --no-yaml`. 17/17 file kết quả trùng từng byte với reports/calibration/stage9/. Repo và `scenarios_calibrated.yaml` không bị đổi (md5 trước/sau trùng). Script báo `yaml_matches_best: true`.
> - Hai việc chuyển từ GD9a (câu 9): đạt. Hai script ước lượng đọc từ YAML. Lời báo "17 file GĐ7/7b/7c trùng byte" là của người thực thi; tôi không chạy lại. Diff của hai file rất nhỏ và hợp lý, có test. `scenarios_calibrated.yaml` ghi tường minh 36 khóa, gồm đủ 13 khóa GD9a, mỗi khóa có comment nguồn.
> - (1) Phạm vi chạm agents/core: chấp nhận được, kèm điều kiện.
>   - CLAUDE.md 4.1 cho phép nâng cấp hành vi dưới dạng tùy chọn bật/tắt trong YAML, mặc định TẮT. Mục 8.2 cho chọn phương án bảo thủ cho lựa chọn chưa duyệt. Khóa này đúng tinh thần đó, và đã ghi vào Q4b.
>   - Tuy vậy LO_TRINH GD9 không ghi việc chạm src/agents/ (chỉ GD9a có phép), nên mục 8.1 "chỉ đúng phạm vi LO_TRINH ghi" chưa phủ trực tiếp.
>   - Báo cáo GD9.md đã nêu rõ điều này (mục 7) và đề xuất Huy duyệt. Có thể chuyển Q4b thành "đã duyệt" hoặc quay về phương án đối xứng (J 0.4550 so với 0.4548, cùng bộ tham số).
> - (2) Trung thực quy trình:
>   - Đạt về mặt nội dung. DANG_KY_TRUOC.md ghi J, lưới, quy tắc Bước 1, tiêu chí chọn bản chính (bất đối xứng, đủ dữ liệu) và quy tắc hòa. Phụ lục chẩn đoán được ghi rõ là "thêm SAU khi chạy lưới chính, chỉ chẩn đoán, không đổi bộ chính" và tách bạch khỏi YAML.
>   - Bộ tham số chọn là argmin J của biến thể chính. Tôi kiểm lại trên grid_stage9.csv: 1536 bộ, top-1 là λ 0.45 / biên 3.8 / J 0.454823, bộ thứ hai J 0.46737.
>   - Không rò ngoài mẫu: hàm mục tiêu chỉ lấy month 1–9. Tôi tính độc lập: RMSE trong mẫu 0.46199, ngoài mẫu thô 0.47672, khử mức 0.46094, sai số TB +0.1217. Tất cả trùng báo cáo. Với GĐ8: 1.0879 / 1.0930 / 0.4569 / +0.993, cũng trùng.
>   - Giới hạn bằng chứng: các file chưa được git track. Dấu thời gian của DANG_KY là 16:28:14, script 16:29:46, kết quả 16:30:11, nên phù hợp với việc viết trước, nhưng không chứng minh được (phụ lục đã có trong file có thể do chạy lưới nhiều lần). Cần commit DANG_KY nguyên trạng.
> - (3) Bước 1: đạt. Tôi tính độc lập từ abm_panel_8nganhang_2023Q1_2026Q3.csv trong cửa sổ 2023Q2–2025Q2. TB tăng trưởng tổng tiền gửi/dư nợ là 0.039761 / 0.044751. P2.5 / P97.5 theo ngân hàng-quý (N = 72) là tiền gửi −0.014160 / 0.173223 và dư nợ 0.001179 / 0.139510. LDR bình quân là 1.089962. Cả 6 số trùng YAML. Ba quan sát bất thường (HDBank 2023Q2, MB Bank 2023Q4, MB Bank 2024Q4) được báo và có bản loại riêng, MB Bank 2025Q4 nằm ngoài cửa sổ.
>
> KINH TẾ (chạy 10 seed A/B/C với scenarios_calibrated.yaml so với scenarios_macro.yaml)
> 1. Mục 6: ĐẠT.
>    - Max(B−A) sau CS là −0.1529, max(C−A) là −0.1528 (là max theo quý và seed, không phải trung bình). Trước CS lệch 0.
>    - Miền cho vay [6.85; 12.17], huy động [3.70; 6.97].
>    - max(loans − 1.6·deposits) = 0, tức bị chặn ở trần và không vượt.
>    - Sai số dùng `lagged_funding_cost` = 0, dùng chi phí vốn cuối quý = 0.077.
>    - Không ngân hàng nào chạm mốc 20% hay 0/14%.
> 2. Trôi hệ thống ở A: không phát hiện trôi do cơ chế mới. Đường A (trung bình 10 seed) đi từ 9.22 xuống đáy 7.54 (Q3/2024) rồi lên 8.5. Đây là hình chữ V do ON ngoại sinh, cùng dạng với bản macro (9.55 → 8.34 → 9.37) nhưng thấp hơn khoảng 0.85 điểm. Đó là hiệu ứng mức.
> 3. Chạm biên:
>    - Sàn/trần tăng trưởng tiền gửi: 0% trần, 0.9% sàn (báo cáo). Dư nợ: 0%.
>    - Trần LDR 1.60: tôi xác nhận ở seed 0, A: 0% đến Q10, 12.5% (Vietcombank) từ month 11, 37.5% (thêm Techcombank và MB Bank) từ month 16. Tỷ lệ tăng dần theo thời gian là dấu hiệu bất khớp cơ chế, không phải nhiễu. Báo cáo nêu 3.6% (month 1–14) và 9.7% (month 1–18); phù hợp.
>    - Với B/C sau CS: 34% ngân hàng-quý chạm trần.
> 4. Tín hiệu tổng không đổi: không có cơ chế mới. Khóa mới chỉ là sàn tăng trưởng, không đổi tín hiệu. Không áp dụng.
> 5. Ngưỡng đạt được:
>    - LDR 1.0900: LDR nằm trong [0.916; 1.60]; 83% ở trên ngưỡng, 6/8 ngân hàng có quan sát ở cả hai phía. Ngưỡng cũ 0.82 thì 100% ở trên, nên ngưỡng mới có thông tin hơn.
>    - Biên 3.8: biên thực TB 3.999, 50.9% ngân hàng-quý ≥ mục tiêu, hội tụ về mục tiêu. Đạt.
> 6. Vòng khép kín: tín hiệu LDR → áp lực huy động → LS huy động → chi phí vốn → LS cho vay. LDR bị chính dư nợ tác động (vòng có sẵn của mô hình), nay với ngưỡng 1.09 hoạt động mạnh hơn. Ảnh hưởng tới LS nhỏ (δ = 0.07). Trần LDR cắt vòng này ở ngân hàng chạm trần.
> 7. Tác động chính sách (tôi tính, trung bình theo seed, quý 15–18):
>    - Bản macro: B−A −0.410, C−A −0.434, C−B −0.024.
>    - Bản hiệu chỉnh: B−A −0.396 (nhỏ hơn 3%), C−A −0.409 (nhỏ hơn 6%), C−B −0.013 (giảm một nửa).
>    - Mức A sau CS giảm từ 9.34 xuống 8.49 (−0.85), nên phần lớn thay đổi cả 3 kịch bản là hiệu ứng mức, không phải hiệu ứng chính sách.
>    - GD9.md chỉ đối chiếu max(B−A) (−0.1529 so với −0.1499), chưa đưa số trung bình này; mục 7 của báo cáo chỉ nói sơ về nhiễu lẫn.
> 8. Nhiễu lẫn tuân thủ: CÓ và đáng kể. `nim_proxy` sau CS của B giảm từ 4.15 xuống 3.40 (biên tổng 3.8 so với 4.6). Xác suất tuân thủ TB của B giảm từ 0.943 xuống 0.877, của C từ 0.945 xuống 0.879. Điều này giải thích vì sao C−B thu hẹp một nửa và gây khó tách tác động chính sách.
> 9. Phụ thuộc dữ liệu:
>    - Với ngân hàng mặc định (không dùng dữ liệu thật): không chạm trần LDR (0%) và đường A có hình chữ V tương tự. Với 2026Q3 làm điểm khởi đầu: chạm trần LDR 88% ngân hàng ở cuối chuỗi, so với 12% của bản macro.
>    - Kết luận: chạm trần là hiện tượng phụ thuộc điểm khởi đầu và tăng trưởng nền. Cấu hình hiệu chỉnh này không dùng được cho chạy khởi đầu 2026Q3.
> - Nghiệm ở biên, λ ngoài CI: báo cáo nêu đủ, không che giấu (câu 5 của yêu cầu). GD9.md nêu rõ λ = 0.45 ngoài CI [0.158; 0.395], 4/5 tham số ở biên lưới, J gần như phẳng theo base_step (0.038) và ngưỡng LDR (0.039), λ và biên tổng bù trừ, lưới mở rộng lại cho nghiệm ở biên (biên tổng 3.0) và ngoài mẫu xấu hơn (RMSE thô 0.896). Báo cáo không diễn giải các tham số phẳng như được nhận diện.
> - (4) Kết luận ngoài mẫu: trung thực, không diễn giải quá mức. Tôi kiểm các số sau, đều khớp:
>   - RMSE khử mức cho vay 0.461 so với 0.457 của GĐ8, tức không tốt hơn về hình dạng.
>   - Mô hình tái tạo ~30% biên độ (0.51/1.71).
>   - Mốc ON thắng ở LS huy động (0.448 so với 0.586) và ở RMSE khử mức cho vay (0.390 so với 0.461).
>   - Có nêu lợi thế thông tin (mô hình và mốc ON được cấp ON thực). So sánh gồm đủ (i) GĐ8, (ii) giữ 2025Q2, (iii) ON.
> - (5) Báo cáo nêu đúng mức độ (xem trên).
> - (7) YAML: ghi tường minh; σ = 0.035, ε = 0.012 ghi rõ là "GIẢ ĐỊNH, không hiệu chỉnh"; policy_pressure 0.65 / policy_step 0.28 giữ nguyên (D6); scenarios.yaml chỉ thêm 1 khóa (D5). Đạt.
> - (8) Số liệu GD9.md và summary_stage9.md khớp CSV/JSON ở các số tôi kiểm: top-1, J, RMSE trong/ngoài mẫu, tăng trưởng, và số mục 6.
>
> VẤN ĐỀ CẦN SỬA (theo mức độ)
> 1. [TRUNG BÌNH] Nhiễu lẫn tuân thủ và độ tin cậy của B−A/C−A chưa được định lượng. Xác suất tuân thủ giảm 0.943 → 0.877, C−B giảm từ −0.024 xuống −0.013; trần LDR bị chạm ở 34% ngân hàng-quý sau CS. Báo cáo chỉ nêu "B−A −0.1529 so với −0.1499" (đó là max, không phải mức trung bình). Hướng sửa: bổ sung các con số trên vào mục 7 của GD9.md và cho GD10 chạy độ nhạy theo λ trong CI và biên tổng. Không đổi tham số.
> 2. [TRUNG BÌNH] Trần LDR 1.60 bị chạm tăng dần (12.5% → 37.5% ngân hàng của kịch bản A theo thời gian; Vietcombank từ 2025Q4 trong khi LDR thực khoảng 1.0). Cấu hình này không nên dùng cho chạy khởi đầu 2026Q3 (88% chạm trần). Báo cáo đã nêu Q7 và chẩn đoán bù tăng trưởng (J 0.4407, hết chạm trần). Vấn đề là tăng trưởng nền theo quy tắc cố định không tái tạo được tăng trưởng tổng. Chỉ giải quyết được bằng cách đổi quy tắc hoặc tham số, nên thuộc mục quyết định.
> 3. [NHỎ] DANG_KY_TRUOC.md và các file stage9 chưa được git track, nên "ghi trước khi chạy" chỉ dựa vào mtime. Hướng sửa: commit DANG_KY_TRUOC.md nguyên trạng trong commit GD9.
> 4. [NHỎ] `depositor_min_growth` chưa có kiểm tra dấu (nếu đặt dương thì sàn dương). Hướng sửa: thêm cảnh báo hoặc ghi chú trong YAML.
> 5. [NHỎ] GD9.md mục 8 (phản biện) còn trống; điều phối viên điền báo cáo này sau khi nhận.
>
> CẦN NGƯỜI DÙNG/NHÓM QUYẾT ĐỊNH
> - Q4b: Duyệt việc chạm src/agents/depositors.py và model.py cho khóa `depositor_min_growth` (hoặc quay về chặn đối xứng ±0.1732).
> - Q6: Giữ nghiệm biên (λ 0.45, ngoài CI GĐ7), hay ràng buộc λ trong CI (λ 0.35, J 0.4994), hay mở rộng lưới. Quyết định này ảnh hưởng mức A/B/C trực tiếp.
> - Q7: Giữ quy tắc tăng trưởng nền hay bù độ lệch. Cần quyết trước GD10, vì nếu đổi phải chạy lại lưới.
> - Sai lệch mức LS huy động của mô hình (+0.33 trong mẫu) làm kéo biên tổng xuống 3.8, thấp hơn biên dữ liệu 4.59. Việc xử lý (vd. `macro_dep_spread`) là lựa chọn kinh tế/tham số, cần Huy duyệt.
