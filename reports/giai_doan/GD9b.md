# GD9b – Hiệu chỉnh lại GD9 theo quyết định D9 (Q6, Q7)

**Trạng thái:** HOÀN THÀNH (nghiệm chạm biên lưới, xem mục 3.2 và 6) · **Ngày:** 2026-11-21 · **Commit:** xem TRANG_THAI.md (đăng ký trước đã commit 1ab8201)

## 1. Mục tiêu và phạm vi
Hiệu chỉnh lại GD9 với hai thay đổi (D9), mọi thứ khác giữ nguyên (cửa sổ 2023Q2–2025Q2, ngoài mẫu 2025Q3–2026Q3, J = 0.5·RMSE_cho_vay + 0.5·RMSE_huy_động, nền `scenarios_macro.yaml`):
- **Q7:** bù một lần độ lệch tăng trưởng tổng (dữ liệu − mô hình A tại nghiệm GD9) vào `depositor_base_growth`, `borrower_base_growth`.
- **Q6:** lưới ràng buộc λ ∈ {0.15…0.40} (6), biên tổng ∈ {3.4…4.8} (8), `base_deposit_rate_step` (4), `deposit_competition` (4), ngưỡng LDR (2) = 1536 bộ.
KHÔNG làm: không chạm `src/agents/`, `src/core/`; không đổi σ, ε, `policy_pressure`, `policy_step` (D6); không sửa `scenarios.yaml`, `scenarios_macro.yaml`; không sửa nội dung đã đăng ký; không mở rộng lưới.

## 2. Đã làm
- `reports/calibration/stage9b/DANG_KY_TRUOC_GD9b.md`: đã commit 1ab8201 trước khi chạy lưới; sau lưới chỉ thêm mục 7 (phụ lục chẩn đoán, ghi rõ thêm sau), mục 1–6 giữ nguyên.
- `src/calibration/calibrate_stage9b.py` (mới): tái dùng hàm của `calibrate_stage9` (không đổi phương pháp GD9). Chạy: `python -m src.calibration.calibrate_stage9b`. Tất định; chạy lại vào thư mục khác cho file giống hệt từng byte (đã kiểm: mọi file trong `reports/calibration/stage9b/` trùng).
  - Giá trị bù tính lại bằng đúng công thức và khớp giá trị dự kiến của đăng ký trong 1e-9 (script tự DỪNG nếu lệch).
  - Nhiễu lẫn tuân thủ tổng quát hóa từ `confounding_stage9.py` (dùng lại `summarize`, `start_2026q3`; 3 cấu hình: macro GĐ8, GD9, GD9b; 10 seed; quý 15–18).
- `configs/scenarios_calibrated_gd9.yaml` (mới): sao nguyên bản GD9 trước khi ghi đè, thêm 2 dòng comment đầu file.
- `configs/scenarios_calibrated.yaml`: ghi đè bằng nghiệm GD9b, 36 khóa tường minh, comment nguồn từng giá trị, ghi giá trị bù Q7 và chạm biên.
- `src/calibration/calibrate_stage9.py`: chỉ đổi đường ghi YAML (`CALIBRATED_CFG` → `scenarios_calibrated_gd9.yaml`, thêm comment đầu file giống bản đã sao) để chạy lại GD9 không ghi đè nghiệm GD9b. `src/calibration/confounding_stage9.py`: cấu hình GD9 trỏ tới file `_gd9`. Phương pháp và đầu ra stage9 không đổi: 22 file trong `reports/calibration/stage9/` trùng md5 trước/sau.
- `tests/test_calibration_stage9.py`: 4 đường dẫn `scenarios_calibrated.yaml` → `scenarios_calibrated_gd9.yaml` (các test này kiểm bản GD9; không nới lỏng gì). `tests/test_calibration_stage9b.py` (mới, 8 test): lưới đúng đăng ký, bản GD9 giữ, quy tắc bù + giá trị dự kiến + dừng khi lệch, YAML khớp nghiệm và bù, argmin/hòa, tái mô phỏng 3 điểm lưới, mục 6, A tất định, `calibrate_stage9` không ghi đè nghiệm GD9b.
- Vòng sửa 2 (chẩn đoán, không đổi nghiệm/YAML/lưới): `src/calibration/diag_gd9b.py` (mới) → `diag_gd9b.csv`, `diag_gd9b.md` (cũng nhúng vào `summary_stage9b.md`); `tests/test_diag_gd9b.py` (mới, 1 test: tái lập byte, không đổi YAML, các quan hệ định tính). Ghi vào đăng ký mục 7 là phụ lục thêm SAU khi chạy lưới; mục 1–6 không đổi. Mọi số trong 3.4–3.6 mới thêm dưới đây truy được tới `diag_gd9b.csv`.
- `README.md`: cây `configs/` và mục hiệu chỉnh GD9b.
- `python -m src.analysis.kiem_dinh_ngoai_mau`: chạy lại với cấu hình mới, báo "Chưa có dữ liệu ngoài mẫu: panel kết thúc ở 2026Q3"; `reports/stage11/` không đổi (git không thấy khác biệt).

## 3. Kết quả chính
Mọi số lấy từ `reports/calibration/stage9b/summary_stage9b.md` và các CSV cùng thư mục. Đối chiếu trong mẫu và ngoài mẫu lịch sử (mô hình và mốc ON cùng được cấp ON thực: lợi thế thông tin), không phải dự báo, không phải tác động chính sách thực tế.

### 3.1 Bù Q7 (`bu_tang_truong_stage9b.csv`, một lần tại nghiệm GD9)
| | dữ liệu | mô hình A (GD9) | Δ | base mới |
|---|---:|---:|---:|---:|
| tiền gửi | 0.03976093 | 0.02975501 | +0.01000592 | 0.04976685 |
| dư nợ | 0.04475110 | 0.06018453 | −0.01543342 | 0.02931768 |
Khớp giá trị dự kiến trong đăng ký (0.0497668532; 0.02931768308).

### 3.2 Nghiệm (`best_by_variant_stage9b.csv`, `boundary_stage9b.csv`)
Cả 3 biến thể (bất đối xứng đủ dữ liệu = chính; đối xứng; loại bất thường) cùng chọn: **λ = 0.40, biên tổng = 3.4 (`target_margin` = 2.05), `base_deposit_rate_step` = 0, `deposit_competition` = 0.07, ngưỡng LDR = bình quân cửa sổ 1.0900**; J = 0.3733 (RMSE_L 0.3164, RMSE_D 0.4303). GD9: J = 0.4548 (λ = 0.45, biên tổng 3.8).
- **Chạm biên:** λ = 0.40 là biên trên lưới ràng buộc và **NGOÀI CI GĐ7 [0.158; 0.395]** (hơn 0.005); biên tổng = 3.4 là **cận dưới lưới**; `base_deposit_rate_step` = 0 và `deposit_competition` = 0.07 là cận dưới lưới (như GD9). Giữ nguyên, không mở rộng (D9).
- Hồ sơ J nhỏ nhất theo giá trị (`profile_stage9b.csv`): λ từ 0.15 đến 0.40: 0.5837, 0.4977, 0.4384, 0.4006, 0.3788, 0.3733 (đơn điệu giảm; biên độ 0.2104). Biên tổng 3.4 → 4.8: 0.3733 … 0.7733 (đơn điệu tăng; biên độ 0.4000), tức hàm mục tiêu chưa có cực tiểu bên trong theo hai tham số này. `base_step` biên độ 0.0293, `deposit_competition` 0.0167, ngưỡng LDR 0.0307 (phẳng hơn).
- Top 10: toàn bộ có biên tổng 3.4, λ ∈ {0.35, 0.40}, LDR bình quân (`top10_stage9b.csv`). Tương quan top 50: λ–biên tổng +0.390, biên tổng–base_step −0.244 (`corr_top50_stage9b.csv`).
- Chẩn đoán (không đổi bộ chính): bộ tốt nhất với λ trong CI GĐ7 là λ = 0.35 (biên tổng 3.4, cùng các tham số khác), J = 0.3788 (hơn nghiệm chính 0.0055).

### 3.3 Trong mẫu và ngoài mẫu so GD9, GĐ8, mốc ngây thơ (`oos_stage9b.csv`)
| Cấu hình | Chuỗi | RMSE thô trong mẫu | RMSE thô ngoài mẫu | RMSE khử mức ngoài mẫu | sai số TB ngoài mẫu | biên độ ngoài mẫu mô hình / thực |
|---|---|---:|---:|---:|---:|---:|
| GD9b | cho vay | 0.3164 | 0.5921 | 0.4861 | −0.3380 | 0.4428 / 1.7147 |
| GD9 | cho vay | 0.4620 | 0.4767 | 0.4609 | +0.1217 | 0.5149 / 1.7147 |
| GĐ8 | cho vay | 1.0879 | 1.0930 | 0.4569 | +0.9930 | 0.5265 / 1.7147 |
| giữ 2025Q2 | cho vay | – | 1.0447 | 0.6449 | −0.8219 | 0 / 1.7147 |
| ON (0.45) | cho vay | – | 0.6429 | 0.3896 | −0.5114 | 0.9923 / 1.7147 |
| GD9b | huy động | 0.4303 | 0.5421 | 0.2888 | +0.4588 | 0.8081 / 1.4567 |
| GD9 | huy động | 0.4477 | 0.5855 | 0.2801 | +0.5142 | 0.8358 / 1.4567 |
| GĐ8 | huy động | 0.5325 | 0.6908 | 0.2826 | +0.6303 | 0.8285 / 1.4567 |
| giữ 2025Q2 | huy động | – | 0.8318 | 0.5747 | −0.6014 | 0 / 1.4567 |
| ON (0.45) | huy động | – | 0.4478 | 0.3404 | −0.2909 | 0.9922 / 1.4567 |
Quý đáy ngoài mẫu: mô hình và thực đều 2025Q3 (cả hai chuỗi, mọi cấu hình mô hình). Toàn chuỗi, tỷ lệ giảm/hồi phục V (mô hình ÷ thực), cho vay: GD9b 0.7025/0.3025, GD9 0.6173/0.3837; huy động: GD9b 0.7289/0.8199, GD9 0.7235/0.8533.
- **Trung thực:** ngoài mẫu, LS cho vay của GD9b **kém GD9** (RMSE thô 0.5921 so 0.4767; khử mức 0.4861 so 0.4609), vì mô hình hạ thấp mức: sai số TB −0.338 (GD9 +0.122). LS huy động thô tốt hơn GD9 (0.5421 so 0.5855) nhưng khử mức hơi kém (0.2888 so 0.2801). So mốc ON, GD9b tốt hơn cho vay (0.5921 so 0.6429) nhưng kém huy động (0.5421 so 0.4478). Trong mẫu GD9b tốt hơn GD9 cả hai chuỗi (đúng kỳ vọng vì tối ưu trong mẫu).
- Chẩn đoán nghiệm GD9b không bù Q7: cho vay ngoài mẫu 0.5516, huy động 0.5922 (`chan_doan_GD9b_nghiem_khong_bu`).

### 3.4 Tăng trưởng tổng sau bù (kịch bản A, `growth_ldr_stage9b.csv`; không bù lần hai)
| | Trong mẫu 1–9: tiền gửi / dư nợ | Ngoài mẫu 10–14: tiền gửi / dư nợ |
|---|---:|---:|
| dữ liệu | 0.0398 / 0.0448 | 0.0334 / 0.0434 |
| GD9b | 0.0395 / 0.0482 | 0.0560 / 0.0537 |
| GD9 | 0.0298 / 0.0602 | 0.0463 / 0.0604 |
Độ lệch còn lại sau bù: tiền gửi −0.0002, dư nợ +0.0035 (tăng trưởng mô hình phụ thuộc lãi suất nên đổi theo nghiệm lưới; bù chỉ tính tại nghiệm GD9). Ngoài mẫu mô hình tăng nhanh hơn dữ liệu (tiền gửi +0.0225, dư nợ +0.0103 mỗi quý; `diag_gd9b.csv`, phần `tang_truong`).

**Đánh giá mức quan trọng (không bù lần hai, đúng đăng ký).** Bù khớp **tại điểm tham chiếu GD9** (Δ tính tại nghiệm GD9: trong mẫu GD9 lệch tiền gửi −0.0100, dư nợ +0.0154 trước bù), **không khớp tại điểm nghiệm GD9b** vì tăng trưởng phụ thuộc lãi suất:
| Khoảng cách mô hình − dữ liệu (mỗi quý) | GD9 | GD9b | tỷ số mô hình/dữ liệu GD9b |
|---|---:|---:|---:|
| tiền gửi, trong mẫu 1–9 | −0.0100 | −0.0002 | 0.994 |
| dư nợ, trong mẫu 1–9 | +0.0154 | +0.0035 | 1.077 (lệch ~7.7% tương đối) |
| tiền gửi, ngoài mẫu 10–14 | +0.0128 | +0.0225 | **1.674** |
| dư nợ, ngoài mẫu 10–14 | +0.0170 | +0.0103 | 1.236 |
Trong mẫu GD9b khớp tốt hơn GD9 (còn dư nợ +7.7% tương đối). Ngoài mẫu, tăng trưởng tiền gửi lệch **xa hơn GD9** (khoảng cách 0.0225 so 0.0128; mô hình gấp 1,67 lần dữ liệu), dư nợ lệch ít hơn GD9. Hệ quả cần nhớ cho GD10 trở đi: kết quả ngoài mẫu của GD9b chịu độ lệch tăng trưởng tiền gửi lớn; bù Q7 chỉ đảm bảo khớp trung bình trong cửa sổ tại nghiệm GD9, không phải tại nghiệm GD9b.

### 3.5 Trần LDR 1.60 và ngưỡng (nguyên nhân: bù Q7) (`confounding_stage9b.csv`, `ldr_cap_stage9b.csv`, `ldr_cap_2026q3_stage9b.csv`, `thresholds_stage9b.csv`)
| Tỷ lệ ngân hàng-quý chạm trần LDR (A) | GD9b | GD9 |
|---|---:|---:|
| month 1–10 | 0.000 | 0.000 |
| month 11–15 | 0.000 | 0.125 |
| month 16–18 | 0.000 | 0.375 |
| khởi đầu 2026Q3, quý cuối | 0.000 | 0.875 |
**Không chạm trần LDR 1.60 là hệ quả của bù Q7, không phải đặc tính của cơ chế hay của biên tổng 3.4.** Cùng nghiệm GD9b, chỉ khác bù Q7 (bỏ bù = cộng ngược Δ_D = +0.0100, Δ_L = −0.0154; chỉ chẩn đoán, không ghi YAML; `diag_gd9b.csv`, phần `bo_bu`; kịch bản A):
| | có bù (nghiệm GD9b) | bỏ bù (chẩn đoán) |
|---|---:|---:|
| tỷ lệ chạm trần LDR, month 1–18 | 0.0% | 18.1% |
| tỷ lệ chạm trần LDR, month 15–18 | 0.0% | 59.4% |
| LDR max | 1.337 | 1.600 |
| tăng trưởng dư nợ TB, month 1–18 | 0.0496 | 0.0592 |
| tăng trưởng tiền gửi TB, month 1–18 | 0.0456 | 0.0359 |
Bù tăng tiền gửi và giảm dư nợ nên LDR không đạt trần. Vì vậy 0% ở bảng trên không nên đọc là kết quả tích cực của cơ chế; nó phụ thuộc quyết định Q7.

Ngưỡng (GD9b, month 1–14): LDR đầu quý nằm trên ngưỡng 1.0900 ở 61.6% ngân hàng-quý; 5 ngân hàng có LDR ở cả hai phía ngưỡng (nên nhánh áp lực huy động có kích hoạt cả hai chiều); LDR đầu quý trong [0.870; 1.399]; áp lực chạm chặn 0%. Định nghĩa biên: biên thực = `loan_rate` − chi phí vốn trễ (`lagged_funding_cost`), cùng định nghĩa với biên mục tiêu của mô hình (biên tổng 3.4); TB 3.696 so mục tiêu 3.40, vượt mục tiêu ở 58.9% ngân hàng-quý, tức "đạt tới mục tiêu" chỉ theo định nghĩa này. Theo định nghĩa khác, `loan_rate` − `deposit_rate`, biên TB là 2.806 (GD9: 3.096; `diag_gd9b.csv`, phần `bien`); không so sánh trực tiếp với 3.40. Chạm trần tăng trưởng tiền gửi 0%, chạm sàn dư nợ mong muốn 1.8%, chạm trần LDR (tại cuối quý) 0%. LDR cuối 2026Q3 (A) lệch thực: ví dụ Vietcombank 1.305 so 1.019, VPBank 1.096 so 1.528, ACB 0.923 so 1.284.

### 3.6 Nhiễu lẫn tuân thủ (10 seed, quý 15–18; trung bình theo seed rồi theo quý)
| Chỉ tiêu | macro GĐ8 | GD9 | GD9b |
|---|---:|---:|---:|
| xác suất tuân thủ TB, B | 0.9434 | 0.8771 | 0.8184 |
| xác suất tuân thủ TB, C | 0.9454 | 0.8794 | 0.8184 |
| nim_proxy A / B / C | 4.558 / 4.147 / 4.183 | 3.788 / 3.390 / 3.412 | 3.376 / 2.986 / 2.989 |
| LS cho vay A sau chính sách | 9.3448 | 8.4903 | 7.9781 |
| B−A (TB) | −0.4101 | −0.3964 | −0.3891 |
| C−A (TB) | −0.4340 | −0.4090 | −0.3904 |
| C−B (TB) | −0.0239 | −0.0126 | −0.0014 |
Tại GD9b, C gần như trùng B (C−B ≈ −0.001): **kịch bản C không phân biệt được với B**. Nguyên nhân truy được (`diag_gd9b.csv`, phần `canh_tranh_huy_dong`; cùng `deposit_competition` = 0.07, ngưỡng LDR 1.09, 10 seed, quý 15–18): nhánh áp lực huy động mà C làm khác B hầu như không được kích hoạt sau bù Q7.
| Sau chính sách | GD9 | GD9b |
|---|---:|---:|
| LDR đầu quý TB của A | 1.461 | 1.092 |
| tỷ lệ ngân hàng-quý trên ngưỡng 1.09 | 100% | 68.8% |
| lãi suất huy động C−B | −0.0401 | −0.0006 |
| `nim_proxy` C−B | +0.0218 | +0.0027 |
(Số tự tính dùng LDR đầu quý = LDR cuối quý trước; hơi khác số reviewer nêu 1.479/65.6%/−0.0007/−0.0002; dùng số tự tính. `nim_proxy` C−B khớp `confounding_stage9b.csv`: 2.9889 − 2.9862.) Nghĩa là các so sánh B vs C ở GD10 trở đi dưới GD9b gần như không mang thông tin về "hạn chế cạnh tranh huy động"; chỉ nên nói "không phân biệt được", không diễn giải thành tác động chính sách. Xác suất tuân thủ thấp hơn GD9 (0.8184 so 0.8771) là hệ quả tham số GD9b (biên tổng thấp hơn); chưa tách riêng. Mức A thấp hơn GD9 0.51 điểm %. Đây là số của mô hình, nhiễu lẫn với mức A và xác suất tuân thủ, không phải tác động chính sách thực tế.

## 4. Kiểm tra
| Hạng mục | Kết quả |
|---|---|
| pytest | 206 passed, 1 xfailed |
| validation | 7/7 ĐẠT (`python -m src.analysis.validation --banks data/clean/abm_initial_8nganhang_2023Q1.csv`) |
| Mục 6 CLAUDE.md (GD9b, 10 lần A/B/C; `section6_stage9b.csv`) | max(B−A) sau chính sách = −0.1495, max(C−A) = −0.1495 (≤ 0); trước chính sách A/B/C trùng (sai khác 0); loan_rate ∈ [6.491; 12.218] (0–20); deposit_rate ∈ [3.681; 6.974] (0–14); max(loans − 1.6·deposits) = −9.96e7 (≤ 0); lag: sai số theo chi phí vốn trễ = 0, theo chi phí vốn hiện tại 0.0684 (> 0): ĐẠT |
| Golden | không đổi (không chạm `src/agents/`, `src/core/`); golden term/golden_total vẫn qua trong pytest |
| Tái lập | chạy lại `calibrate_stage9b` vào thư mục khác cho file giống hệt từng byte: có; `reports/calibration/stage9/` trùng md5 trước/sau: có (22 file) |
| Chẩn đoán vòng sửa 2 | `python -m src.calibration.diag_gd9b` → `diag_gd9b.csv` (md5 ổn định giữa 2 lần chạy; `tests/test_diag_gd9b.py` kiểm byte và YAML không đổi) |
| `kiem_dinh_ngoai_mau` | chạy được, báo chưa có dữ liệu 2026Q4; `reports/stage11/` không đổi |

## 5. Quyết định mặc định đã áp dụng
| # | Câu hỏi | Mặc định đã dùng | Căn cứ | Hệ quả nếu Huy chọn khác |
|---|---|---|---|---|
| 1 | Biến thể phụ (ii) loại bất thường: Δ cộng vào base riêng của Bước 1 biến thể (0.0371/0.0438) hay base chính | cộng vào base riêng của biến thể | Đăng ký mục 4 "cộng cùng Δ"; ghi ở phụ lục mục 7 | Chỉ ảnh hưởng biến thể phụ (không ghi vào YAML); cả 3 biến thể cùng chọn một nghiệm |
| 2 | `calibrate_stage9` ghi vào đâu sau GD9b | `configs/scenarios_calibrated_gd9.yaml` (không phải file chính) | tránh chạy lại GD9 ghi đè nghiệm GD9b; đầu ra stage9 không đổi | Có thể trả đường ghi cũ nhưng có nguy cơ ghi đè |
| 3 | Test GD9 cũ trỏ file YAML nào | trỏ `scenarios_calibrated_gd9.yaml` (kiểm cùng nội dung như trước) | bản GD9 vẫn được giữ; không nới test | – |

## 6. CẦN HUY QUYẾT ĐỊNH
Q6/Q7 đã đóng bởi D9. Điểm mới:
1. **Nghiệm góc.** λ = 0.40 (biên trên lưới; ngoài CI GĐ7 0.005) và biên tổng = 3.4 (cận dưới lưới) đều chạm biên; J đơn điệu theo hai tham số này, nên đây là nghiệm biên do lưới giới hạn, không phải cực tiểu bên trong. Mặc định đã áp dụng: giữ nguyên và ghi lại (D9). Phương án: (a) giữ; (b) dùng bộ trong CI (λ = 0.35, J + 0.0055) làm cấu hình chính hoặc biến thể độ nhạy GD10; (c) mở rộng lưới (D9 không cho phép). Đề xuất: giữ (a) và đưa λ = 0.35 vào độ nhạy GD10.
2. **Ngoài mẫu cho vay kém GD9.** RMSE thô 0.5921 so 0.4767 do mô hình hạ thấp mức LS cho vay (sai số TB −0.338). Biên tổng 3.4 thấp hơn biên GĐ8/GD9 và hàm mục tiêu chỉ đo trong mẫu. Mặc định: GD9b vẫn là cấu hình chính theo D9; GD9 giữ làm biến thể độ nhạy GD10. Huy cân nhắc có chọn cấu hình chính theo ngoài mẫu hay không (khác tiêu chí đã đăng ký, nên không tự làm).
3. **Tăng trưởng ngoài mẫu.** Sau bù, mô hình tăng trưởng nhanh hơn dữ liệu ngoài mẫu (tiền gửi 0.0560 so 0.0334). Theo đăng ký không bù lần hai; chỉ báo cáo. Bù khớp tại điểm GD9, không khớp tại điểm GD9b (xem 3.4); khoảng cách tiền gửi ngoài mẫu rộng hơn GD9 (0.0225 so 0.0128).
4. **C không phân biệt được với B dưới GD9b.** C−B = −0.0014 vì sau bù Q7 chỉ 68.8% ngân hàng-quý trên ngưỡng LDR (GD9: 100%) nên nhánh áp lực huy động gần như không khác giữa B và C (3.6). Mặc định: giữ GD9b theo D9; GD10 báo B vs C chỉ ở mức "không phân biệt được". Phương án cho Huy: dùng GD9 làm biến thể độ nhạy cho so sánh B vs C, hoặc xem lại `deposit_competition`/ngưỡng LDR (ngoài phạm vi D9).
5. **Không chạm trần LDR là do bù Q7** (3.5), không phải đặc tính cơ chế; không dùng làm bằng chứng cơ chế đúng.

## 7. Hạn chế và rủi ro
- Hiệu chỉnh trong mẫu 9 quý, 2 chuỗi LS; nghiệm biên và nhiều tham số phẳng (`base_step`, δ, ngưỡng LDR biên độ ≤ 0.031) nên khó nhận diện; không diễn giải từng tham số.
- Mô hình và mốc ON được cấp ON thực ngoài mẫu: RMSE ngoài mẫu là đối chiếu, không phải dự báo.
- B−A, C−A (3.6) là số của mô hình; mức A và xác suất tuân thủ khác nhau giữa cấu hình nên không so sánh trực tiếp như tác động chính sách.
- Bù Q7 tính tại nghiệm GD9 (đã đăng ký); tại nghiệm GD9b độ lệch dư nợ còn +0.0035 trong mẫu (~7.7% tương đối), tiền gửi ngoài mẫu gấp 1,67 lần dữ liệu (3.4).
- 0% chạm trần LDR là hệ quả của bù Q7 (bỏ bù: 18.1%; 3.5), không phải bằng chứng cơ chế.
- C ≈ B (C−B = −0.0014) do nhánh áp lực huy động gần như không kích hoạt sau bù (3.6); kết luận B vs C ở GD10+ chỉ ở mức "không phân biệt được".
- "Biên đạt mục tiêu" chỉ theo định nghĩa `loan_rate` − chi phí vốn trễ (3.696 so 3.40); theo `loan_rate` − `deposit_rate` là 2.806.

## 8. Phản biện (điều phối viên điền nguyên văn báo cáo cuối của reviewer-abm, số vòng)

**Số vòng: 2.** Vòng 1: reviewer ĐẠT CÓ ĐIỀU KIỆN (3 TRUNG BÌNH, 2 NHỎ). Vòng sửa 2 chỉ bổ sung chẩn đoán và giải thích (script `src/calibration/diag_gd9b.py`, `reports/calibration/stage9b/diag_gd9b.*`): trần LDR không chạm là hệ quả của bù Q7; C−B ≈ 0 do nhánh áp lực huy động không được kích hoạt sau bù; độ lệch tăng trưởng còn lại sau bù; định nghĩa biên. Không đổi tham số, nghiệm hay YAML. Số tự tính của vòng 2 khác số reviewer ở vài ô nhỏ (LDR đầu quý, nim_proxy C−B); báo cáo dùng số tự tính và đã ghi rõ.

Nguyên văn báo cáo cuối của reviewer-abm (vòng 1):

> KẾT LUẬN: ĐẠT CÓ ĐIỀU KIỆN
>
> Số liệu, lưới, nghiệm, tính tái lập và mục 6 CLAUDE.md đều khớp. Quy trình trung thực. Có ba điểm cần ghi rõ trong báo cáo hoặc để Huy quyết: (a) nghiệm góc, (b) hiệu ứng phụ của bù Q7, (c) B và C không còn phân biệt được.
>
> KỸ THUẬT
> - pytest: 205 passed, 1 xfailed. Validation: 7/7 ĐẠT.
> - (1) Quy trình: `git diff HEAD` của DANG_KY_TRUOC_GD9b.md chỉ thêm mục 7, ghi rõ "THÊM SAU". Mục 1–6 giống hệt bản commit 1ab8201. Tôi dùng `git diff HEAD` chứ không so `git show 1ab8201` với working tree; kết quả như nhau vì HEAD chính là 1ab8201.
>   - Tôi đọc lại `grid_stage9b.csv`. Mỗi biến thể có 1536 điểm, đúng 6×8×4×4×2.
>   - Argmin J của cả 3 biến thể là λ=0.40, biên tổng 3.4, base_step 0, δ 0.07, ldr_mean. Chỉ có 1 điểm đạt min, nên không có hòa. J = 0.373347.
>   - Nghiệm chọn theo J trong mẫu, không theo ngoài mẫu.
>   - Hồ sơ J theo λ: 0.5837, 0.4977, 0.4384, 0.4006, 0.3788, 0.3733. Theo biên tổng 3.4→4.8: 0.3733 … 0.7733. Khớp báo cáo.
> - (9) Không chạm `src/agents/`, `src/core/`, `tests/golden`, `configs/scenarios.yaml`, `configs/scenarios_macro.yaml`, `data/`, `reports/calibration/stage9/`. Kiểm bằng `git diff HEAD`.
>   - Test GD9 cũ chỉ đổi 4 đường dẫn sang `_gd9`, không nới ngưỡng. Golden vẫn qua trong pytest.
>   - `calibrate_stage9.py` chỉ đổi đường ghi YAML và thêm 2 dòng comment đầu file.
> - (8) YAML mới: `policy_pressure` 0.65, `policy_step` 0.28, σ (`depositor_sensitivity` 0.035) và ε (`borrower_elasticity` 0.012) giữ nguyên, `policy_month` 14, `max_loan_to_deposit` 1.6. Bản `scenarios_calibrated_gd9.yaml` cùng giá trị với `git show HEAD:configs/scenarios_calibrated.yaml` (so sau khi bỏ dòng comment, không có khác biệt).
> - (10) Chạy lại `calibrate_stage9b --outdir <scratchpad>/rep --no-yaml`: cả 21 file trùng byte với repo. Phần ghi chú tính tái lập trong GD9b.md đúng.
> - Số trong GD9b.md khớp những gì tôi tự tính lại (xem phần kinh tế). Tôi không đối chiếu từng ô các CSV khác ngoài `grid_stage9b.csv`.
> - `reports/stage11/` không đổi. Không có giá trị mới hard-code trong Python.
>
> KINH TẾ (10 seed, tự chạy lại bằng `ABMModel`; script tại scratchpad rv.py, rv2.py, rv3.py)
> 1. Mục 6 CLAUDE.md: ĐẠT.
>    - Trước chính sách, A/B/C chênh 0.0.
>    - B−A sau chính sách TB −0.389, max theo quý −0.224. C−A TB −0.390, max −0.224.
>    - `loan_rate` ∈ [6.49; 12.22], `deposit_rate` ∈ [3.68; 6.97].
>    - LDR max 1.370 ≤ 1.6, 0 vi phạm.
>    - Phản ứng trễ qua `lagged_funding_cost` do `section6_stage9b.csv` báo (sai số 0 với chi phí vốn trễ, 0.0684 với chi phí vốn hiện tại). Tôi không tự kiểm lại mục này.
> 2. Trôi hệ thống: không có xu hướng tự sinh ở A. `target_margin` hằng 2.05 mọi quý. Đường `loan_rate` A của GD9b (9.10 → 7.19 ở quý 8 → 8.0 ở quý 16–18) cùng hình dạng với GĐ8 và GD9, theo biến vĩ mô. Khác biệt chỉ là dịch mức: A sau chính sách 7.978 so GD9 8.490 và GĐ8 9.345. Đây là hiệu ứng mức, không phải trôi.
> 3. Chạm biên: ở A, chạm trần/sàn tăng trưởng tiền gửi và dư nợ 0% mọi quý; chạm trần LDR 0% mọi quý; `loan_rate` không chạm miền 0–20. Không có xu hướng tăng dần.
> 4. Tín hiệu có tổng không đổi: không áp dụng. Cơ chế mới chỉ đổi giá trị tham số, không thêm cơ chế.
> 5. Ngưỡng đạt được: ngưỡng LDR 1.09 có đạt, 61.6% ngân hàng-quý trên ngưỡng. Sau chính sách ở A, 65.6% trên ngưỡng, so GD9 là 100%. Biên mục tiêu 3.40 không phải ràng buộc cứng, và biên thực TB vượt mục tiêu.
> 6. Vòng khép kín: không áp dụng, không có cơ chế mới.
> 7. Tác động chính sách. Dịch mức: A giảm 0.51 điểm % so GD9, và B−A, C−A đổi nhẹ.
>
>    | Chênh lệch | GĐ8 | GD9 | GD9b |
>    |---|---:|---:|---:|
>    | B−A | −0.410 | −0.396 | −0.389 |
>    | C−A | −0.434 | −0.409 | −0.390 |
>    | C−B | −0.0239 | −0.0126 | −0.0014 |
>
>    Đây chủ yếu là dịch mức. C−B gần như bằng 0 là mất phân biệt B/C, xem vấn đề 2.
> 8. Nhiễu lẫn tuân thủ: xác suất tuân thủ B/C = 0.8184/0.8184 (GD9 0.8771/0.8794, GĐ8 0.9434/0.9454). `nim_proxy` sau chính sách: B 2.9996, C 2.9994. Cơ chế làm xác suất tuân thủ giảm là biên thấp hơn, qua `nim_proxy`. Điều này làm khó tách tác động chính sách. Báo cáo đã nêu mức, nhưng ghi "chưa phân tích nguyên nhân". Tôi đã tìm ra nguyên nhân, xem vấn đề 2.
> 9. Phụ thuộc dữ liệu:
>    - Khởi đầu từ 2026Q3: trần LDR 0% mọi quý, LDR max 1.466 (GD9 là 87.5% ở quý cuối).
>    - Tôi không chạy ngân hàng giả lập mặc định. Phần này đưa ra để người đọc biết, không kết luận được.
>    - Hiệu ứng "trần LDR không chạm" lặp lại trên cả hai bộ dữ liệu tôi chạy (2023Q1 và 2026Q3). Hiệu ứng do bù Q7, không do dữ liệu.
>
>    Ngoài mẫu, tôi tự tính RMSE LS cho vay: 0.5921 cho GD9b so 0.4767 cho GD9 và 1.0930 cho GĐ8. Trong mẫu: 0.3164 (GD9b), 0.4620 (GD9), 1.0879 (GĐ8). Sai số TB ngoài mẫu: −0.338 (GD9b), +0.122 (GD9), +0.993 (GĐ8). Khớp báo cáo. Báo cáo trung thực khi nói LS cho vay GD9b kém GD9 ngoài mẫu.
>
> VẤN ĐỀ CẦN SỬA (xếp theo mức độ)
> 1. [TRUNG BÌNH] Không chạm trần LDR 1.60 là hệ quả của bù Q7, không phải đặc tính cơ chế. Báo cáo GD9b.md mục 3.5 trình bày 0% như một kết quả tích cực nhưng không nêu rõ nguyên nhân (hạng mục đặc biệt (5) hỏi đúng điều này).
>    - Bằng chứng: tôi chạy nghiệm GD9b nhưng bỏ bù (cộng ngược Δ_D = 0.0100 và Δ_L = −0.0154) cho kết quả sau.
>
>      | Chỉ tiêu | Có bù (GD9b) | Bỏ bù |
>      |---|---:|---:|
>      | Tỷ lệ chạm trần LDR | 0% | 18.1% |
>      | LDR max | 1.34 | 1.60 |
>      | Tăng trưởng dư nợ TB | 0.0496 | 0.0592 |
>      | Tăng trưởng tiền gửi TB | 0.0456 | 0.0359 |
>
>    - Biên tổng 3.4 không phải nguyên nhân chính.
>    - Hướng sửa: thêm vào GD9b.md một câu nói rõ trần LDR không chạm là do bù Q7, kèm bảng trên. Không phải đổi tham số.
> 2. [TRUNG BÌNH] C−B ≈ 0 (−0.0014) làm kịch bản C không phân biệt được với B; nguyên nhân tôi truy được nhưng báo cáo chưa nêu.
>    - Với `deposit_competition` = 0.07 như GD9, sau chính sách LDR TB của A giảm từ 1.479 (GD9, 100% ngân hàng trên ngưỡng 1.09) xuống 1.093 (GD9b, 65.6% trên ngưỡng).
>    - Chênh lệch lãi suất huy động giữa C và B sau chính sách giảm từ −0.040 (GD9) xuống −0.0007. `nim_proxy` C−B từ +0.0193 xuống −0.0002.
>    - Tức là, theo kiểm tra của tôi, nhánh áp lực huy động mà C làm khác B hầu như không được kích hoạt sau bù.
>    - Ý nghĩa: các kết luận B vs C ở GD10 trở đi gần như không mang thông tin về "hạn chế cạnh tranh huy động".
>    - Hướng sửa: GD9b.md mục 3.6 và mục 7 nên ghi nguyên nhân này, không nên để "chưa phân tích nguyên nhân". Đây là phần giải thích, không phải sửa tham số.
> 3. [TRUNG BÌNH] Độ lệch tăng trưởng còn lại sau bù. Báo cáo có nêu số, nhưng đánh giá mức quan trọng còn thiếu.
>    - Trong mẫu: dư nợ +0.0034/quý, tương đương khoảng 7.6% tương đối so với tăng trưởng thực 0.0448. Tiền gửi −0.0003.
>    - Ngoài mẫu: tiền gửi 0.0560 so 0.0334 (gấp 1.68 lần; khoảng cách 0.0226, rộng hơn GD9 là 0.0129). Dư nợ 0.0537 so 0.0434 (khoảng cách 0.0103, hẹp hơn GD9 là 0.0170).
>    - Bù tại nghiệm GD9 cố định (đúng như đăng ký) khớp ý định Q7(b) chỉ ở trung bình trong cửa sổ và chỉ ở GD9, không ở GD9b.
>    - Hướng sửa: nêu rõ "bù khớp tại điểm tham chiếu GD9, không khớp tại điểm nghiệm GD9b; tăng trưởng tiền gửi ngoài mẫu lệch xa hơn GD9". Không bù lần hai đúng như đăng ký.
> 4. [NHỎ] Báo cáo GD9b.md mục 8 (phản biện) còn trống ("điều phối viên điền"). Trường "Commit" cũng chưa điền. Không phải lỗi của người thực thi.
> 5. [NHỎ] Số liệu "Biên thực TB 3.696 vs mục tiêu 3.40" (biên = `loan_rate` − chi phí vốn trễ): tôi chưa tái tính từ đầu. Biên cách khác (`loan_rate` − `deposit_rate`) cho 2.71. Báo cáo cần nói rõ định nghĩa biên khi viết "đạt tới mục tiêu".
>
> CẦN NGƯỜI DÙNG/NHÓM QUYẾT ĐỊNH
> - Nghiệm góc: λ = 0.40 (ngoài CI GĐ7 [0.158; 0.395] 0.005) và biên tổng = 3.4 (cận dưới lưới), J đơn điệu theo cả hai. Báo cáo nêu đủ và quy tắc "giữ, không mở rộng" đã thực hiện đúng. Hai tham số này không được nhận diện, nên không diễn giải như ước lượng. Quyết định giữ nghiệm này làm cấu hình chính hay đưa λ = 0.35 (J +0.0055, trong CI) làm cấu hình chính hoặc làm độ nhạy GD10 là của Huy.
> - Có chọn cấu hình chính theo ngoài mẫu hay không (GD9b kém GD9 về LS cho vay ngoài mẫu, tốt hơn thô về huy động). Tiêu chí đã đăng ký là J trong mẫu, nên không đổi.
> - Chấp nhận hay không việc bù Q7 làm mất phân biệt B/C (vấn đề 2) và làm trần LDR không còn ràng buộc (vấn đề 1). Nếu GD10 cần C khác B thì phải đổi quy tắc bù hoặc giả định kinh tế, ngoài quyền của người thực thi.
> - Có bù lần hai tại nghiệm GD9b hay không (độ lệch dư nợ 0.0034 trong mẫu; tiền gửi ngoài mẫu lệch 0.0226). Hiện đúng như đăng ký, chỉ báo cáo.
