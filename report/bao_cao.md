# Phản ứng của ngân hàng thương mại trước chỉ đạo giảm lãi suất cho vay: mô hình dựa trên tác nhân cho 8 ngân hàng Việt Nam

*Dự thảo báo cáo nghiên cứu – GD12 (21/11/2026). Nhóm: Huy (TV1), Minh (TV2), Vũ (TV3).*

> Mọi con số trong báo cáo truy được tới file kết quả; đường dẫn ghi trong comment HTML `<!-- nguồn: ... -->` hoặc trong chú thích bảng. Số liệu được đọc trực tiếp từ CSV, không chép từ văn bản báo cáo giai đoạn.

> ### ⚠️ Những điều KHÔNG được diễn giải
> 1. **Chênh lệch giữa kịch bản A/B/C không phải tác động chính sách thực tế.** Đó là chênh lệch giữa các quy tắc bên trong mô hình, nhiễu lẫn với mức lãi suất của A và xác suất tuân thủ.
> 2. **Không so sánh trực tiếp B−A với mức giảm 1.5–2%/năm trong CV 9608:** chỉ đạo nhắm vào lĩnh vực sản xuất kinh doanh, ưu tiên, còn mô hình trừ `policy_step` vào toàn bộ lãi suất cho vay. Với giả định step 0.14–0.50, B−A cuối kỳ của mô hình là −0.26 đến −0.89 điểm %.
> 3. **Tỷ lệ chạm trần LDR bằng 0% không phải bằng chứng về cơ chế.** Nó là hệ quả của việc bù tăng trưởng (Q7); bỏ bù (chẩn đoán, khởi đầu 2023Q1, quý 1–18, kịch bản A) thì tỷ lệ chạm trần là 18.1%.
> 4. **λ (`pass_through`), biên tổng và `deposit_competition` không phải ước lượng.** Chúng là nghiệm của lưới hiệu chỉnh (nghiệm biên) hoặc giá trị độ nhạy, không có khoảng tin cậy thống kê.
> 5. **RMSE ngoài mẫu không phải dự báo.** Ở giai đoạn 2025Q3–2026Q3 mô hình được cấp lãi suất qua đêm (ON) thực tế, tức có lợi thế thông tin.

<!-- nguồn ý 2: reports/stage10/sensitivity_stage10.csv, cột BmA_cuoi_ky_q18: policy_step_0.14 = -0.2587, policy_step_0.5 = -0.8857; quyết định D11 (Huy, 21/11/2026) -->
<!-- nguồn ý 3: reports/calibration/stage9b/diag_gd9b.csv, phần bo_bu (18.1%); confounding_stage9b.csv (0%) -->

## 1. Giới thiệu và câu hỏi nghiên cứu

Trong giai đoạn 2023–2026, Ngân hàng Nhà nước Việt Nam (NHNN) và Chính phủ nhiều lần yêu cầu các tổ chức tín dụng giảm lãi suất cho vay, có lúc kèm mục tiêu định lượng (vd. Công văn 6385/NHNN-CSTT tháng 8/2023: giảm 1.5–2%/năm; Công văn 4462/NHNN-CSTT tháng 5/2024: giảm 1–2%/năm). Tháng 10/2026, Công văn 9608/NHNN-CSTT và 9736/NHNN-CSTT yêu cầu giảm tối thiểu 0.5%/năm lãi suất huy động kỳ hạn từ 6 tháng và giảm lãi suất cho vay nói chung, với mức giảm 1.5–2%/năm tập trung cho sản xuất kinh doanh/lĩnh vực ưu tiên (xem mục 3.4 và 6.3). Đây là công cụ "chỉ đạo mềm": hiệu quả phụ thuộc vào việc từng ngân hàng có tuân thủ hay không, và vào việc chi phí vốn có giảm theo hay không.

Nghiên cứu xây dựng một mô hình dựa trên tác nhân (agent-based model, ABM) cho 8 ngân hàng thương mại Việt Nam (Vietcombank, VietinBank, BIDV, Techcombank, VPBank, MB Bank, ACB, HDBank) nhằm trả lời ba câu hỏi:

1. **Trong cấu trúc mô hình**, khi bổ sung một quy tắc chỉ đạo giảm lãi suất cho vay (kịch bản B) so với không can thiệp (A), lãi suất cho vay mô phỏng thay đổi theo chiều nào và độ lớn phụ thuộc vào giả định nào?
2. Bổ sung hạn chế cạnh tranh huy động (kịch bản C) có tạo khác biệt phân biệt được so với B không?
3. Sau khi hiệu chỉnh trên dữ liệu panel 2023Q1–2026Q3, mô hình tái tạo được đến đâu diễn biến lãi suất cho vay và huy động quan sát, và những kết luận nào vững trước thay đổi tham số?

Mô hình chạy theo quý: khởi tạo Q1/2023, 18 bước (Q2/2023 → Q3/2027), chính sách kích hoạt từ bước 15 (Q4/2026). Mục tiêu là phân tích **cơ chế** trong một khung giả định minh bạch, không phải ước lượng tác động nhân quả hay dự báo lãi suất.

Cấu trúc báo cáo: mục 2 tổng quan tài liệu; mục 3 dữ liệu; mục 4 mô hình; mục 5 ước lượng và hiệu chỉnh; mục 6 kết quả kịch bản, độ vững, giả định và hạn chế; mục 7 hướng mở rộng; mục 8 nội dung cần hoàn thiện.

<!-- nguồn mục tiêu định lượng các văn bản: data/raw/chi_dao_lai_suat_2023_2026.csv, cột muc_tieu_dinh_luong -->

## 2. Tổng quan tài liệu

### 2.1. Mô hình dựa trên tác nhân trong kinh tế và ngân hàng

ABM mô phỏng một hệ thống từ dưới lên: các tác nhân dị biệt hành động theo quy tắc đơn giản, và hành vi tổng thể của hệ thống (giá, lãi suất, phân phối) nổi lên từ tương tác giữa chúng, thay vì được áp đặt bằng một phương trình cân bằng. Santa Fe Institute (SFI) là một trong những trung tâm phát triển hướng tiếp cận này trong kinh tế học; SFI có bài tổng quan về phương pháp "Agent-Based Modeling: Worlds Within Worlds" [5].

Ví dụ kinh điển là Santa Fe Artificial Stock Market của W. Brian Arthur, John H. Holland, Blake LeBaron, Richard Palmer và Paul Tayler. Các nhà đầu tư nhân tạo liên tục thử và loại bỏ các mô hình kỳ vọng; khi tốc độ khám phá thấp, thị trường hội tụ về cân bằng kỳ vọng hợp lý, còn khi tốc độ khám phá cao, xuất hiện giao dịch kỹ thuật, bong bóng và sụp đổ tạm thời, cùng các đặc trưng thống kê giống dữ liệu thực (như hành vi GARCH) [1]–[3]. Farmer và Foley (2009) [4] lập luận rằng kinh tế học cần dùng mô hình dựa trên tác nhân. Bài học phương pháp cho nghiên cứu này: (i) quy tắc hành vi đơn giản, minh bạch; (ii) so sánh kết quả mô phỏng với đặc trưng của dữ liệu thực thay vì chỉ kiểm tra tính nội nhất quán.

Trong lĩnh vực ngân hàng, Chan-Lau (2017) [6] xây dựng ABBA, mô hình ABM của hệ thống ngân hàng với ngân hàng là tác nhân dị biệt, thích nghi, đặt lãi suất cho vay bằng markup. Papadopoulos (2020) [7] nhận xét rằng quy tắc đặt lãi suất cho vay trong các ABM thường mang tính ad-hoc và thử nhận diện quy tắc này từ dữ liệu; đây là vấn đề gần với phương trình lãi suất cho vay của nghiên cứu này. Mô hình ở đây dùng thư viện Mesa 3.3.1 cho Python [8].

### 2.2. Truyền dẫn lãi suất ở Việt Nam

Truyền dẫn lãi suất là mức độ và tốc độ lãi suất bán lẻ (huy động, cho vay) phản ứng với thay đổi của lãi suất điều hành và lãi suất thị trường liên ngân hàng. Trong mô hình, kênh này được biểu diễn bằng hai phương trình: lãi suất huy động neo về ON quý trước (tốc độ φ), và lãi suất cho vay điều chỉnh từng phần (hệ số λ) về chi phí vốn trễ cộng biên. Ở Việt Nam, ngoài công cụ lãi suất điều hành, NHNN còn dùng chỉ đạo hành chính (công văn, chỉ thị, họp với các tổ chức tín dụng) để tác động lãi suất; danh mục 24 sự kiện 2023–2026 của nhóm ở mục 3.4.

Các nghiên cứu thực nghiệm về Việt Nam cho thấy: truyền dẫn từ lãi suất chính sách sang lãi suất bán lẻ chưa hoàn toàn (hệ số dài hạn khoảng 0.7–0.93 trong mẫu 07/2004–06/2014), điều chỉnh về cân bằng mất khoảng 3–6 tháng, và lãi suất huy động truyền dẫn mạnh hơn lãi suất cho vay [9]. Truyền dẫn diễn ra theo hai giai đoạn (lãi suất chính sách → lãi suất thị trường → lãi suất bán lẻ) và có tính bất đối xứng; lãi suất thị trường phản ứng nhanh, lãi suất bán lẻ chưa hoàn toàn [10]. Với sáu ngân hàng thương mại giai đoạn 2009–2012, ràng buộc về vốn và thanh khoản là nguyên nhân của bất đối xứng, và truyền dẫn từ lãi suất chính sách sang lãi suất cho vay không rõ ràng [11]. Đây là kết quả của các nghiên cứu nêu trên, không phải kết quả của mô hình này; mẫu và phương pháp của chúng khác dữ liệu quý 2023–2026 ở đây nên chỉ dùng làm bối cảnh.

Khoảng trống mà nghiên cứu hướng tới: phần lớn phân tích truyền dẫn dùng hồi quy trên chuỗi tổng hợp, ít chú ý đến **tính dị biệt của quyết định tuân thủ** giữa các ngân hàng. ABM cho phép mô tả tường minh xác suất tuân thủ phụ thuộc biên lợi nhuận của từng ngân hàng, và tách được (trong mô hình) phần thay đổi lãi suất do quy tắc chỉ đạo với phần do chi phí vốn.

## 3. Dữ liệu

### 3.1. Panel 8 ngân hàng
<!-- nguồn: data/clean/abm_panel_8nganhang_2023Q1_2026Q3.csv; mô tả cách xây dựng: data/clean/README.md -->

Panel gồm 8 ngân hàng × 15 quý (2023Q1–2026Q3), 120 quan sát, với các biến: tiền gửi, dư nợ, tỷ lệ CASA, nợ xấu, giấy tờ có giá, vay liên ngân hàng, NIM, `loan_rate_pct`, `deposit_rate_pct`. Ba nhóm ngân hàng chỉ mang tính tương đối trong mẫu, không phải phân loại chính thức: quốc doanh (Vietcombank, VietinBank, BIDV), cổ phần lớn (Techcombank, VPBank, MB Bank), cổ phần nhỏ (ACB, HDBank). Dữ liệu khởi tạo mô hình lấy từ quý 2023Q1 (`data/clean/abm_initial_8nganhang_2023Q1.csv`); file 2026Q3 (`abm_initial_8nganhang_2026Q3.csv`) chỉ dùng để kiểm tra trần LDR (xem 6.4).

| Biến (120 quan sát) | TB | Nhỏ nhất | Lớn nhất |
|---|---:|---:|---:|
| `loan_rate_pct` (%/năm) | 8.740 | 5.472 | 14.041 |
| `deposit_rate_pct` (%/năm) | 3.944 | 2.031 | 7.877 |
| `casa_ratio` | 0.235 | 0.070 | 0.390 |

### 3.2. Định nghĩa lợi suất sổ sách và ánh xạ CASA

`loan_rate_pct` và `deposit_rate_pct` là **lợi suất sổ sách** tính từ báo cáo tài chính (thu nhập/chi phí lãi chia số dư bình quân, quy năm), không phải lãi suất niêm yết hay lãi suất khoản vay mới. Vì vậy chúng phản ánh lãi suất bình quân danh mục và thay đổi chậm hơn lãi suất chào mới (giả định Q2: r^L của mô hình được hiểu là lãi suất bình quân danh mục).

`deposit_rate_pct` tính trên **tổng** tiền gửi, gồm cả CASA gần như không trả lãi. Trong mô hình, lãi suất huy động của ngân hàng là lãi suất **có kỳ hạn** (`deposit_rate_basis: term`), nên khi đối chiếu dùng ánh xạ

  r^D_mô_hình = `deposit_rate_pct` / (1 − CASA),   chi phí vốn = r^D · (1 − CASA) + 0.15 = `deposit_rate_pct` + 0.15.

Số 0.15 điểm % (`funding_cost_add`) là chi phí vốn ngoài lãi tiền gửi, giả định giữ nguyên.

### 3.3. Lãi suất liên ngân hàng qua đêm (ON)
<!-- nguồn: data/raw/sbv_lnh_qua_dem_theo_quy.csv (cột bq_gian_don); data/raw/README_sbv.md -->

Nguồn: NHNN, trang "Lãi suất thị trường liên ngân hàng" trên sbv.gov.vn, lấy qua API của trang ngày 21/11/2026 (970 phiên, 12/2022–10/2026; script `src/data/fetch_sbv_interbank.py`). Chuỗi dùng trong mô hình là bình quân giản đơn theo quý. ON biến động mạnh trong mẫu: 4.817 (2023Q1) → 0.227 (2023Q3) → 5.812 (2026Q1) → 3.946 (2026Q3). Sau 2026Q3, mọi kịch bản giữ ON = 3.946 (D3). ON thực tế Q4/2026 (bình quân 4.074 trên 36 phiên đến 19/11/2026, quý chưa kết thúc; `data/raw/sbv_lnh_qua_dem_ngoai_mau.csv`) chỉ dùng cho kiểm định ngoài mẫu, không đưa vào kịch bản. Lãi suất điều hành (tái cấp vốn, tái chiết khấu) ở `data/raw/sbv_lai_suat_dieu_hanh_quy.csv`.

### 3.4. Danh mục chỉ đạo lãi suất 2023–2026
<!-- nguồn: data/raw/chi_dao_lai_suat_2023_2026.csv (24 dòng, cột nguon) -->

Nhóm lập danh mục 24 văn bản/sự kiện của NHNN, Chính phủ và Thủ tướng, mỗi dòng có đường dẫn nguồn. Phân loại: yêu cầu giảm lãi suất cho vay (7); thay đổi lãi suất điều hành (4); ổn định huy động, giảm cho vay (4); yêu cầu giảm cả huy động và cho vay (3); công bố lãi suất cho vay (2); kiểm tra thực hiện (2); yêu cầu giảm huy động để giảm cho vay (1); ổn định lãi suất (1). Chỉ một số văn bản có mục tiêu định lượng (6385/2023: giảm 1.5–2%/năm; 4462/2024: giảm 1–2%/năm; 9608/2026: huy động kỳ hạn ≥ 6 tháng giảm tối thiểu 0.5%/năm; giảm lãi suất cho vay nói chung, mức 1.5–2%/năm tập trung cho sản xuất kinh doanh/lĩnh vực ưu tiên). Danh mục **có thể chưa đầy đủ**. Ngày và nội dung CV 9608 được xác nhận qua chính văn bản CV 9736, văn bản này dẫn "công văn số 9608/NHNN-CSTT ngày 18/10/2026" [12], [13]. Các văn bản khác trong danh mục chưa được xác minh lại trong GD12; nguồn của từng văn bản là đường dẫn ghi trong cột `nguon`.

## 4. Mô hình

<!-- nguồn phương trình: src/agents/bank.py, regulator.py, depositors.py, borrowers.py; src/core/model.py (step) -->
<!-- nguồn giá trị tham số: configs/scenarios_calibrated.yaml (cấu hình chính GD9b) -->

### 4.1. Tác nhân

| Tác nhân | Số lượng | Vai trò |
|---|---:|---|
| Ngân hàng (`Bank`) | 8 | Đặt lãi suất huy động r^D và cho vay r^L; quyết định có tuân thủ chỉ đạo hay không |
| NHNN (`Regulator`) | 1 | Bật chỉ đạo ở kịch bản B, C từ bước chính sách; xác định xác suất tuân thủ |
| Khối người gửi tiền (`DepositorBlock`) | 1 (gộp) | Tăng trưởng tiền gửi của từng ngân hàng theo chênh lệch lãi suất |
| Khối người vay (`BorrowerBlock`) | 1 (gộp) | Tăng trưởng dư nợ mong muốn theo lãi suất cho vay, bị chặn bởi trần LDR |

### 4.2. Phương trình (chỉ số i: ngân hàng; t: quý; lãi suất %/năm, tăng trưởng mỗi quý)

**Lãi suất huy động.** Với LDR_i = L_i / D_i đầu quý:

  r^D_{i,t} = clip_[0;14]( r^D_{i,t−1} + κ_t · [s₀ + δ · clip_±0.5(LDR_i − LDR*)] + φ · (ON_{t−1} + spread − r^D_{i,t−1}) )

trong đó s₀ = `base_deposit_rate_step`, δ = `deposit_competition`, LDR* = `deposit_ldr_target`; κ_t = `deposit_cap_factor` (0.25) ở kịch bản C sau khi chính sách bật, bằng 1 trong các trường hợp khác. Số hạng neo ON (φ = `macro_dep_speed` = 0.177, spread = `macro_dep_spread` = 1.2723) chỉ có khi `macro_driver: exogenous` và **không** bị nhân với κ: chỉ đạo chỉ hạn chế phần cạnh tranh huy động, không hạn chế lãi suất thị trường.

**Chi phí vốn.** FC_{i,t} = r^D_{i,t} · (1 − CASA_i) + 0.15; chi phí vốn trễ FC^lag được cập nhật cuối mỗi quý.

**Lãi suất cho vay (điều chỉnh từng phần về mục tiêu).**

  r^L_{i,t} = r^L_{i,t−1} + λ · (FC^lag_{i} + m_i + 1.35 − r^L_{i,t−1})

với λ = `pass_through`, m_i = `target_margin`; biên tổng = m_i + `loan_spread_add` (1.35). Vì dùng FC^lag, lãi suất cho vay phản ứng **trễ một quý** với cú sốc chi phí vốn.

**Tuân thủ chỉ đạo (B, C sau khi chính sách bật).** Với nim_i = r^L_i − FC_i (`nim_proxy`, không phải NIM kế toán):

  p_i = clip_[0.02; 0.98]( 1 / (1 + exp(−[2.5 · (P − 0.5) + 1.1 · (nim_i − 2.2)])) ),

P = `policy_pressure` (0.65). Ngân hàng tuân thủ với xác suất p_i (bốc thăm qua `model.random`); nếu tuân thủ, **r^L_i giảm trực tiếp `policy_step`** điểm % trong quý đó. Do điều chỉnh từng phần, mức giảm tích lũy dần qua các quý tuân thủ liên tiếp.

**Tiền gửi.** g^D_i = clip_[g^D_min; g^D_max]( g^D_0 + σ · (r^D_i − r̄^D) ), với r̄^D là bình quân giản đơn lãi suất huy động đầu quý của 8 ngân hàng, σ = `depositor_sensitivity` (0.035).

**Dư nợ.** g^L_i = clip_[g^L_min; g^L_max]( g^L_0 − ε · (r^L_i − 9.5) ), ε = `borrower_elasticity` (0.012); L_i = min( L_i·(1 + g^L_i), 1.60 · D_i ) (trần LDR kỹ thuật `max_loan_to_deposit`, không phải tỷ lệ pháp lý).

### 4.3. Trình tự một quý

`ABMModel.step()`: (1) tính r̄^D từ lãi suất huy động đầu quý; (2) NHNN xác định chính sách có hiệu lực; (3) mỗi ngân hàng cập nhật r^D, r^L và quyết định tuân thủ; (4) khối người gửi tiền cập nhật tiền gửi; (5) khối người vay cập nhật dư nợ (có trần LDR); (6) `finish_month()`: cập nhật chi phí vốn trễ (và biên nếu bật học thích nghi), kiểm tra ràng buộc (0 ≤ r^L ≤ 20, 0 ≤ r^D ≤ 14, L ≤ 1.60·D); (7) ghi lịch sử.

### 4.4. Kịch bản

| Kịch bản | Nội dung trong mô hình |
|---|---|
| A | Không chỉ đạo |
| B | Từ bước 15 (Q4/2026): ngân hàng tuân thủ với xác suất p_i giảm r^L thêm `policy_step` |
| C | B + nhân phần cạnh tranh huy động với `deposit_cap_factor` = 0.25 |

`policy_step` là **giả định** kịch bản (YAML: 0.28). Phần phân tích độ nhạy thử dải 0.14–0.50; đầu trên của dải (0.375–0.50) được chọn để gần với quy đổi thô của mức giảm 1.5–2%/năm trong chỉ đạo, trải trong 4 quý, nhưng phạm vi khác nhau: chỉ đạo nhắm vào sản xuất kinh doanh và lĩnh vực ưu tiên, còn `policy_step` trừ vào toàn bộ lãi suất cho vay của ngân hàng tuân thủ (`src/agents/bank.py`).

Trước bước chính sách, A/B/C trùng nhau với cùng seed. Kịch bản A là tất định (không có bốc thăm), nên khoảng phân vị giữa các lần chạy chỉ phản ánh bốc thăm tuân thủ ở B, C.

### 4.5. Tùy chọn mở rộng

- **`macro_driver: exogenous`** (từ GĐ8, bật trong cấu hình chuẩn): đưa số hạng neo ON vào phương trình huy động. `macro_lending_on_coef` = 0 (không có số hạng ON trực tiếp trong cho vay; D1).
- **Học thích nghi `relative`** (mặc định TẮT): cuối mỗi quý, ngân hàng so tăng trưởng dư nợ của mình với bình quân hệ thống; thấp hơn quá ngưỡng θ thì giảm biên một bước, cao hơn quá θ (và nim không thấp hơn bình quân) thì tăng biên; biên bị chặn trong [`margin_min`; `margin_max`]. Không dùng số ngẫu nhiên. Chỉ dùng trong phân tích độ vững (6.2).
- **`deposit_rate_basis: term`** (mặc định): r^D là lãi suất có kỳ hạn, ánh xạ CASA như 3.2.

## 5. Ước lượng và hiệu chỉnh

Quy trình gồm hai lớp: (i) **ước lượng một bước** trên panel (GĐ7, 7b, 7c) để có khoảng tham chiếu cho tham số và kiểm tra giả thuyết; (ii) **hiệu chỉnh bằng mô phỏng** (GD9, GD9b) – chọn tham số trên lưới đặt trước để tối thiểu sai số đường đi mô phỏng so với dữ liệu, với phương pháp đăng ký trước khi chạy lưới. Mọi kết quả là đối chiếu trong mẫu; không có kiểm định dự báo thật.

### 5.1. GĐ7 – Phương trình lãi suất cho vay và biên
<!-- nguồn: reports/calibration/estimates_stage7.csv, bootstrap_stage7.csv -->

Hồi quy panel (N = 112, 8 cụm ngân hàng, SE CR1 theo ngân hàng, wild-cluster bootstrap B = 9999) của phương trình điều chỉnh từng phần lãi suất cho vay:

| Đặc tả | λ | CI 95% CR1 | CI 95% bootstrap |
|---|---:|---|---|
| PT1 (c) | 0.274 | [0.167; 0.380] | [0.158; 0.395] |
| PT1 (d1), có ON_{t−1} | 0.315 | [0.211; 0.418] | [0.224; 0.449] |

Biên trung bình quan sát μ (PT2) = 4.588, CI [3.434; 5.742]. Giá trị trong cấu hình gốc trước hiệu chỉnh: λ = 0.48 (nằm ngoài CI), biên 4.55. Độ nhạy người gửi tiền σ và độ co giãn nhu cầu tín dụng ε **không nhận diện được** từ dữ liệu; giữ giá trị giả định (0.035; 0.012).

### 5.2. GĐ7b – Phương trình lãi suất huy động
<!-- nguồn: reports/calibration/estimates_stage7b.csv, bootstrap_stage7b.csv -->

Quy tắc huy động gốc (điều chỉnh theo áp lực LDR) không mô tả được dữ liệu. Đặc tả neo về ON quý trước (PT5-ON, d) cho tốc độ hội tụ φ = 0.177 (CI bootstrap [0.156; 0.196], N = 112) và chênh lệch cân bằng 1.2723 điểm % trên ON. Hai giá trị này được đưa vào cấu hình (`macro_dep_speed`, `macro_dep_spread`). Trên mẫu N = 104 chênh lệch cân bằng là 1.082, được dùng làm biến thể độ nhạy (6.2).

### 5.3. GĐ7c – Chỉ đạo lãi suất và biên cho vay
<!-- nguồn: reports/calibration/estimates_stage7c.csv (equation margin/dRL, parameter I_sum, c_def main) -->

Mã hóa cường độ chỉ đạo I_q ∈ {0, 1, 2} theo quý từ danh mục 3.4 và hồi quy biên thực, Δ lãi suất cho vay lên I_t, I_{t−1}, có FE ngân hàng và kiểm soát ON_{t−1}. **Không có bằng chứng "chỉ đạo làm biên hẹp lại"**: tác động tích lũy I_t + I_{t−1} lên biên thực là +0.446 (CI [0.192; 0.701]); lên Δ lãi suất cho vay là +0.081 (CI [−0.179; 0.340]). Chỉ khi không kiểm soát ON, hệ số lên Δ lãi suất cho vay mới âm – tức trùng với thời kỳ ON giảm. Kết luận: dữ liệu **không đủ** để hiệu chỉnh `policy_pressure`, `policy_step`; hai tham số này là **giả định kịch bản** (D6), chỉ phân tích độ nhạy. Các hệ số trên là tương quan, không phải tác động nhân quả.

### 5.4. GD9 và GD9b – Hiệu chỉnh bằng mô phỏng
<!-- nguồn: reports/calibration/stage9/best_by_variant_stage9.csv; reports/calibration/stage9b/best_by_variant_stage9b.csv, profile_stage9b.csv, boundary_stage9b.csv, bu_tang_truong_stage9b.csv; đăng ký: reports/calibration/stage9b/DANG_KY_TRUOC_GD9b.md -->

**Thiết kế (đăng ký trước).** Kịch bản A, cấu hình nền `configs/scenarios_macro.yaml`. Cửa sổ hiệu chỉnh 2023Q2–2025Q2 (9 quý), ngoài mẫu lịch sử 2025Q3–2026Q3 (5 quý). Hàm mục tiêu J = 0.5·RMSE(LS cho vay) + 0.5·RMSE(LS huy động), so với chuỗi lợi suất sổ sách gộp của 8 ngân hàng. Lưới: λ, biên tổng, `base_deposit_rate_step`, `deposit_competition`, ngưỡng LDR. Ngưỡng chặn tăng trưởng lấy từ phân vị 2.5%/97.5% của dữ liệu.

**GD9.** Nghiệm: λ = 0.45, biên tổng 3.8, J = 0.4548 (RMSE_L 0.4620, RMSE_D 0.4477). λ = 0.45 nằm ngoài CI GĐ7.

**GD9b (cấu hình chính, quyết định D9).** Hai thay đổi so với GD9:
1. *Bù tăng trưởng (Q7)*, một lần, không tối ưu J: tại nghiệm GD9, tăng trưởng tổng mô hình lệch dữ liệu (tiền gửi 0.0298 so 0.0398; dư nợ 0.0602 so 0.0448 mỗi quý); cộng phần lệch vào tăng trưởng nền: `depositor_base_growth` = 0.0398 + 0.0100 = 0.0498, `borrower_base_growth` = 0.0448 − 0.0154 = 0.0293.
2. *Lưới ràng buộc (Q6)*: λ ∈ {0.15, …, 0.40} (trong CI GĐ7), biên tổng ∈ {3.4, …, 4.8}.

Nghiệm GD9b: **λ = 0.40, biên tổng = 3.4** (`target_margin` 2.05), `base_deposit_rate_step` = 0, `deposit_competition` = 0.07, ngưỡng LDR = 1.090 (LDR bình quân cửa sổ); J = 0.3733 (RMSE_L 0.3164, RMSE_D 0.4303). Cả ba biến thể ngưỡng tăng trưởng chọn cùng bộ.

**Đây là nghiệm biên** (Q9): λ ở biên trên lưới (và vượt cận trên CI bootstrap 0.395 khoảng 0.005), biên tổng, `base_deposit_rate_step`, `deposit_competition` ở cận dưới lưới. Hồ sơ J theo λ giảm đơn điệu (0.5837 ở 0.15 → 0.3733 ở 0.40) và theo biên tổng tăng đơn điệu (0.3733 ở 3.4 → 0.7733 ở 4.8), nên hàm mục tiêu không có cực tiểu bên trong lưới theo hai tham số này. Theo D9, nghiệm được giữ nguyên, lưới không mở rộng. Bộ tốt nhất có λ trong CI là λ = 0.35 (cùng các tham số khác), J = 0.3788.

**Hạn chế của hiệu chỉnh.** Chỉ 9 quý và một đường đi; `base_deposit_rate_step`, `deposit_competition`, ngưỡng LDR có hồ sơ J gần phẳng (biên độ ≤ 0.031), tức khó nhận diện. λ hiệu chỉnh (đường đi nhiều bước) và λ ước lượng một bước (GĐ7) đo hai thứ khác nhau; λ của mô hình còn hấp thụ sai lệch mức của phương trình huy động. Biên tổng hiệu chỉnh (3.4) thấp hơn biên quan sát (4.59), xem 6.4.

## 6. Kết quả, giả định, hạn chế và lưu ý diễn giải

Tất cả kết quả dưới đây là kết quả **của mô hình**. Không đọc chênh lệch giữa kịch bản là tác động chính sách thực tế (hộp "Những điều KHÔNG được diễn giải" ở đầu báo cáo).

### 6.1. Độ khớp lịch sử: GD9b (chính), GD9 và λ = 0.35 song song
<!-- nguồn: reports/calibration/stage9b/oos_stage9b.csv (dòng hieu_chinh_GD9b_batdoixung_daydu, GD9_nghiem, chan_doan_GD9b_lambda_trong_CI, GD8_chua_hieu_chinh, ngay_tho_*) -->
<!-- B−A, C−A, C−B: reports/stage10/abc_summary_stage10.csv (GD9b, GD9; 60 lần), reports/stage10/sensitivity_stage10.csv dòng pass_through_0.35 (30 lần); TB quý 15–18 -->

Theo Q11, cấu hình chính **không** được chọn theo kết quả ngoài mẫu; GD9b là cấu hình chính theo quy tắc đã đăng ký, GD9 và biến thể λ = 0.35 (λ trong CI GĐ7, các tham số khác như GD9b) báo song song với cùng chỉ tiêu.

| Chỉ tiêu (kịch bản A; mô hình − thực) | GD9b (chính) | GD9 | λ = 0.35 |
|---|---:|---:|---:|
| λ / biên tổng | 0.40 / 3.4 | 0.45 / 3.8 | 0.35 / 3.4 |
| **Trong mẫu 2023Q2–2025Q2** – LS cho vay: RMSE thô / khử mức | 0.3164 / 0.3153 | 0.4620 / 0.3824 | 0.3279 / 0.3230 |
| Trong mẫu – LS huy động: RMSE thô / khử mức | 0.4303 / 0.2964 | 0.4477 / 0.3070 | 0.4296 / 0.2959 |
| **Ngoài mẫu 2025Q3–2026Q3** – LS cho vay: RMSE thô / khử mức / sai số TB | 0.5921 / 0.4861 / −0.3380 | 0.4767 / 0.4609 / +0.1217 | 0.6137 / 0.5047 / −0.3492 |
| Ngoài mẫu – LS huy động: RMSE thô / khử mức / sai số TB | 0.5421 / 0.2888 / +0.4588 | 0.5855 / 0.2801 / +0.5142 | 0.5405 / 0.2889 / +0.4568 |
| Biên độ ngoài mẫu LS cho vay, mô hình / thực | 0.4428 / 1.7147 | 0.5149 / 1.7147 | 0.3893 / 1.7147 |
| Tỷ lệ biên độ chữ V toàn chuỗi (LS cho vay): giảm / hồi phục | 0.7025 / 0.3025 | 0.6173 / 0.3837 | 0.7013 / 0.2453 |
| Quý đáy toàn chuỗi LS cho vay, mô hình (thực 2025Q1) | 2025Q1 | 2024Q4 | 2025Q1 |
| B−A (TB quý 15–18; `policy_step` = 0.28) | −0.3933 | −0.4016 | −0.4182 |
| C−A | −0.3947 | −0.4151 | −0.4204 |
| C−B | −0.0014 | −0.0135 | −0.0022 |

*Chú thích số lần chạy:* B−A, C−A, C−B của GD9b và GD9 lấy từ bản 60 lần; của λ = 0.35 lấy từ bản 30 lần. Nếu so cùng 30 lần, B−A lần lượt là −0.4004 (GD9b), −0.4047 (GD9) và −0.4182 (λ = 0.35) <!-- nguồn: sensitivity_stage10.csv dòng co_so_30, GD9_lambda_0.45, pass_through_0.35 -->. Riêng các chỉ tiêu độ khớp lịch sử của kịch bản A là tất định, không phụ thuộc số lần chạy.

Mốc đối chiếu ngoài mẫu (cùng cửa sổ): cấu hình GĐ8 chưa hiệu chỉnh – LS cho vay RMSE thô 1.0930, khử mức 0.4569; giữ nguyên mức 2025Q2 – 1.0447 / 0.6449; mốc ngây thơ theo ON – LS cho vay 0.6429 / 0.3896, LS huy động 0.4478 / 0.3404.

Đọc bảng:
- Trong mẫu, GD9b khớp tốt hơn GD9 ở cả hai chuỗi (đúng kỳ vọng vì tối ưu trên cửa sổ này). Ngoài mẫu, LS cho vay của GD9b **kém** GD9 (RMSE thô 0.5921 so 0.4767) do mô hình hạ thấp mức (sai số TB −0.338); LS huy động thô tốt hơn GD9 nhưng khử mức gần như bằng nhau.
- Ở cả ba cấu hình, mô hình chỉ tái tạo khoảng 23–30% biên độ tăng ngoài mẫu của LS cho vay (0.39–0.51 so 1.71).
- Mốc ngây thơ ON thắng cả ba cấu hình ở RMSE khử mức LS cho vay và RMSE thô LS huy động.
- B−A và C−A cùng dấu, cùng bậc độ lớn ở ba cấu hình; C−B nhỏ ở cả ba. Khác biệt B−A giữa các cấu hình đi kèm khác biệt xác suất tuân thủ (6.2), không phải bằng chứng chính sách tác động khác nhau.

### 6.2. Kết quả kịch bản A/B/C và độ vững
<!-- nguồn: reports/stage10/abc_summary_stage10.csv; sensitivity_stage10.csv; sensitivity_gd10b_stage10.csv; robustness_stage10.csv; confounding_stage10.csv -->

**Cấu hình chính (GD9b, 60 lần chạy, TB quý 15–18 = Q4/2026–Q3/2027).** LS cho vay A = 7.978; ở `policy_step` = 0.28 (giá trị YAML, một giả định; độ lớn theo dải step ở bảng dưới), B−A = −0.3933 (P5–P95 theo seed: −0.4571 đến −0.3361; 100% seed âm); C−A = −0.3947; C−B = −0.0014. Xác suất tuân thủ TB ở B và C đều là 0.818. Cuối kỳ (quý 18), B−A = −0.5031 vì mức giảm tích lũy qua các quý tuân thủ.

**Độ lớn B−A phụ thuộc giả định `policy_step`.** Chính sách trừ trực tiếp `policy_step` khỏi LS cho vay của ngân hàng tuân thủ (`src/agents/bank.py`), nên B−A gần như tỷ lệ thuận với step. Kết quả được báo theo **dải step**, không nêu một con số:

| `policy_step` (giả định) | B−A TB quý 15–18 | B−A cuối kỳ (q18) | B−A TB / step | C−B TB | nguồn |
|---:|---:|---:|---:|---:|---|
| 0.14 | −0.2015 | −0.2587 | −1.44 | −0.0013 | sensitivity_stage10.csv |
| 0.28 (YAML) | −0.4004 | −0.5113 | −1.43 | −0.0014 | sensitivity_stage10.csv |
| 0.375 | −0.5342 | −0.6793 | −1.42 | −0.0014 | sensitivity_gd10b_stage10.csv |
| 0.42 | −0.5950 | −0.7537 | −1.42 | −0.0019 | sensitivity_stage10.csv |
| 0.50 | −0.7001 | −0.8857 | −1.40 | −0.0019 | sensitivity_stage10.csv |

(30 lần chạy mỗi dòng.) Với step trong dải 0.14–0.50 có hai hệ số, đo hai thứ khác nhau:
- **B−A trung bình sau chính sách (TB quý 15–18) ≈ −1.4 × step** (từ −1.40 đến −1.44): nằm trong khoảng −0.20 đến −0.70 điểm %.
- **B−A cuối kỳ (quý 18) ≈ −1.8 × step** (từ −1.77 đến −1.85): nằm trong khoảng −0.26 đến −0.89 điểm %. Hệ số cuối kỳ lớn hơn vì mức giảm tích lũy qua các quý tuân thủ.

Độ lớn B−A là hệ quả của giả định `policy_step` (mục 4.4), không phải kết quả nhận diện từ dữ liệu; không so sánh trực tiếp với mức giảm trong CV 9608 (xem hộp ý 2 ở đầu báo cáo).

**Độ nhạy các tham số khác** (30 lần, mỗi lần đổi một tham số; `sensitivity_stage10.csv`): `policy_pressure` ×0.7 / ×1.3 cho B−A −0.3639 / −0.4262 (chỉ qua xác suất tuân thủ 0.737 / 0.878; mức A không đổi); λ = 0.158 (đầu dưới CI) cho −0.4886, λ = 0.395 cho −0.4022; `macro_dep_spread` 1.08 cho −0.4004; σ, ε ±50% cho −0.3989 đến −0.4006; nghiệm GD9 (λ 0.45) cho −0.4047. Trong 20 dòng tóm tắt của `robustness_stage10.csv` (không phải 20 biến thể độc lập): B−A < 0 và C−A < 0 ở 20/20; cùng bậc độ lớn (tỷ số 0.5–1.5 so cấu hình chính) ở 18/20, hai trường hợp không giữ là step 0.42 và 0.50; **C phân biệt được B ở 0/20** (|C−B| < 10% |B−A| ở mọi dòng). Độ nhạy một-tham-số-một-lần không bắt được tương tác giữa tham số.

**Nhiễu lẫn tuân thủ** (`confounding_stage10.csv`). Khi cố định xác suất tuân thủ p* = 0.8178 cho mọi cấu hình nền (30 lần), B−A là −0.4003 (GD9b), −0.3801 (GD9), −0.3709 (GĐ8), −0.3695 (cấu hình gốc) – thứ tự đảo so với khi tuân thủ nội sinh (−0.3933, −0.4016, −0.4178, −0.4110). Phần chênh B−A giữa các cấu hình nền chủ yếu do xác suất tuân thủ khác nhau (0.82 so 0.94), vốn phụ thuộc `nim_proxy` và do đó phụ thuộc biên hiệu chỉnh.

**Học thích nghi `relative`** – báo cả hai bản (Q12), 60 lần, nền GD9b (`sensitivity_stage10.csv`):

| Bản | LS cho vay A | B−A | C−A | C−B | xs tuân thủ B |
|---|---:|---:|---:|---:|---:|
| Học TẮT (chính) | 7.9781 | −0.3933 | −0.3947 | −0.0014 | 0.8178 |
| Học BẬT, cửa sổ biên theo YAML (`margin_min`/`margin_max`) | 8.1643 | −0.4008 | −0.4013 | −0.0005 | 0.8490 |
| Học BẬT, cửa sổ biên dời −1.15 | 7.9799 | −0.3942 | −0.3951 | −0.0009 | 0.8047 |

Cửa sổ biên trong YAML được đặt quanh biên gốc; với biên hiệu chỉnh (`target_margin` 2.05 < `margin_min` 2.2), biên bị đẩy lên ngay quý đầu, nên bản YAML mang một hiệu ứng mức (A tăng 0.19 điểm) không do quy tắc học. Bản dời cửa sổ cô lập quy tắc học: mức A gần như không đổi. Ở cả hai bản, B−A và C−A thay đổi dưới 2%.

**`deposit_competition` (GD10b, 30 lần, nền GD9b; báo cả 4 giá trị, không giá trị nào là bản chính, không đổi YAML)** – `sensitivity_gd10b_stage10.csv`:

| `deposit_competition` | LS cho vay A | B−A | C−A | C−B | C−B / |B−A| | LS huy động C−B | chạm trần LDR |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.07 (= YAML) | 7.9781 | −0.4004 | −0.4018 | −0.0014 | 0.34% | −0.0046 | 0 |
| 0.3 | 8.0148 | −0.4006 | −0.4047 | −0.0041 | 1.03% | −0.0161 | 0 |
| 0.7 | 8.0646 | −0.4001 | −0.4059 | −0.0058 | 1.44% | −0.0209 | 0 |
| 1.2 | 8.0983 | −0.4016 | −0.4001 | +0.0015 | 0.37% | −0.0019 | 0 |

B−A gần như không đổi theo `deposit_competition`; C−B đổi theo `deposit_competition` nhưng không đơn điệu. C−B **khác 0 về thống kê** (nửa rộng CI 95% ghép cặp: ±0.0008 ở 0.3, ±0.0020 ở 0.7, ±0.0010 ở 1.2; `CmB_ci95_nua_rong`) nhưng **nhỏ về độ lớn**: |C−B| ≤ 1.44% |B−A|, dưới ngưỡng 10% đã đặt trước ở GD10. CI ghép cặp rất hẹp vì B và C dùng chung dãy bốc thăm, nên "khác 0 về thống kê" không mang ý nghĩa kinh tế. Vì vậy **kết luận về B so với C chỉ ở mức "không phân biệt được"** trong mô hình, không phải kết luận về hiệu quả của hạn chế cạnh tranh huy động.

**Tóm lại các kết luận vững (trong mô hình):** (i) B và C cho LS cho vay thấp hơn A ở mọi biến thể đã thử. Dấu âm phần lớn do cấu trúc (chính sách chỉ trừ `policy_step` khỏi lãi suất cho vay); điều vững đáng chú ý là các phản hồi qua huy động và tăng trưởng không đảo được dấu này. (ii) độ lớn vững với λ, σ, ε, spread, `policy_pressure`, học thích nghi và cấu hình nền, nhưng **tỷ lệ với giả định `policy_step`**; (iii) B và C không phân biệt được.

### 6.3. Bối cảnh chỉ đạo thực tế tháng 10/2026 và kiểm định ngoài mẫu sau chính sách
<!-- nguồn: data/raw/chi_dao_lai_suat_2023_2026.csv (dòng 2026-10-18, 2026-10-21); data/raw/sbv_lnh_qua_dem_ngoai_mau.csv; reports/stage11/trang_thai_stage11.md -->

Ngày 18/10/2026, trước cuộc họp của Thống đốc ngày 19/10/2026, NHNN ban hành CV 9608/NHNN-CSTT [12]: giảm tối thiểu 0.5%/năm lãi suất huy động kỳ hạn từ 6 tháng; giảm lãi suất cho vay nói chung, với mức 1.5–2%/năm tập trung cho sản xuất kinh doanh/lĩnh vực ưu tiên (không cùng phạm vi với `policy_step`, vốn áp lên toàn bộ dư nợ trong mô hình; xem hộp ý 2 ở đầu báo cáo). Ngày 21/10/2026, sau cuộc họp ngày 19/10/2026, CV 9736/NHNN-CSTT quán triệt giảm tối thiểu 0.5%/năm lãi suất huy động bình quân của các giao dịch phát sinh mới kỳ hạn từ 6 tháng so với kỳ báo cáo 11–20/10/2026 [13]. Thời điểm và nội dung trùng với kịch bản C (chỉ đạo từ Q4/2026, cả cho vay và huy động). Thực tế Q4/2026 vì vậy tương ứng nhánh B/C; kịch bản A là phản thực tế, không quan sát được.

Kiểm định ngoài mẫu sau chính sách (GD11) **chưa có kết quả**: panel kết thúc 2026Q3, lợi suất sổ sách Q4/2026 chưa công bố. Khung kiểm định đã sẵn sàng (`src/analysis/kiem_dinh_ngoai_mau.py`). ON thực tế Q4/2026 đến 19/11/2026 bình quân 4.074, cao hơn 3.946 giả định trong kịch bản; ý nghĩa của chênh lệch này chưa được đánh giá. Khi có dữ liệu, kết quả chỉ là đối chiếu mô tả trên 1–2 quý, không phải ước lượng tác động chính sách.

### 6.4. Giả định và hạn chế

**Giả định chính.** Bước thời gian theo quý: các mốc chỉ đạo trong quý được gộp vào một thời điểm kích hoạt (Q4/2026). Người gửi tiền và người vay là khối gộp. `policy_pressure`, `policy_step`, `deposit_cap_factor` là giả định kịch bản (D6). σ, ε không nhận diện được và giữ giá trị giả định. ON sau 2026Q3 giữ 3.946 cho mọi kịch bản (D3). LS cho vay của mô hình được hiểu là lãi suất bình quân danh mục (Q2).

**Hạn chế (a) – Sai lệch mức lãi suất huy động.** <!-- nguồn: reports/calibration/stage9b/mean_error_insample_stage9b.csv --> Trong mẫu 2023Q2–2025Q2 (kịch bản A, mô hình − thực), cấu hình chính GD9b có sai số trung bình có dấu của LS huy động là **+0.312** điểm % (RMSE thô 0.4303, khử mức 0.2964), trong khi LS cho vay gần như không lệch mức (−0.026). Như vậy phần lớn sai số RMSE của LS huy động là sai lệch mức: phương trình huy động của mô hình đặt LS huy động cao hơn dữ liệu một cách hệ thống. (Kiểm tra nội nhất quán: √(0.4303² − 0.2964²) = 0.312.) Sai lệch này làm chi phí vốn mô phỏng cao hơn thực và là một lý do khiến hiệu chỉnh ưa biên thấp (hạn chế b). Ngoài mẫu, sai số TB của LS huy động GD9b là +0.459. Đây là hạn chế của mô hình (Q14), chưa được sửa.

**Hạn chế (b) – Biên tổng hiệu chỉnh thấp hơn biên quan sát.** Biên tổng hiệu chỉnh nằm trong khoảng 3.4 (GD9b, λ = 0.35) đến 3.8 (GD9), thấp hơn biên trung bình quan sát μ = 4.59 (GĐ7, PT2; CI [3.43; 5.74]). Biên thấp làm `nim_proxy` thấp, kéo xác suất tuân thủ xuống (0.818 ở GD9b so 0.877 ở GD9 và 0.943 ở GĐ8), nên B−A, C−A nhiễu lẫn với lựa chọn biên. Biên tổng 3.4 không nên đọc là ước lượng biên thực của ngân hàng. Lưu ý thêm: biên tổng hiệu chỉnh là **tham số mục tiêu**, còn μ = 4.59 là biên **quan sát**, và hai đại lượng có thể không cùng định nghĩa. Biên thực hiện của mô hình GD9b (TB quý 1–14) là 3.696 nếu tính bằng `loan_rate` − chi phí vốn trễ, và 2.806 nếu tính bằng `loan_rate` − `deposit_rate` (GD9: 3.999 và 3.095) <!-- nguồn: reports/calibration/stage9b/diag_gd9b.csv phần bien -->. Định nghĩa biên của PT2 (GĐ7) chưa được đối chiếu để so cùng cơ sở; việc này là câu hỏi cho Minh (TONG_HOP.md).

**Hạn chế (c) – Nghiệm GD9b là nghiệm biên.** λ = 0.40 ở biên trên lưới ràng buộc, biên tổng 3.4 ở cận dưới lưới, và hàm mục tiêu đơn điệu theo cả hai tham số trong lưới (5.4). Cực tiểu thực có thể nằm ngoài lưới; theo D9 lưới không được mở rộng. λ = 0.40 còn vượt cận trên CI bootstrap GĐ7 (0.395) khoảng 0.005. Các tham số `base_deposit_rate_step`, `deposit_competition`, ngưỡng LDR có hồ sơ J gần phẳng, nên không nhận diện được.

**Các hạn chế khác.**
- *Cơ sở đo của chỉ đạo.* CV 9736 đo trên lãi suất bình quân của các giao dịch phát sinh mới (dòng) [13], còn mô hình và dữ liệu dùng lợi suất sổ sách trên toàn bộ số dư (tồn); lợi suất sổ sách phản ánh chỉ đạo chậm hơn, nên so sánh với diễn biến Q4/2026 cần tính đến khác biệt cơ sở này.
- *Tăng trưởng.* Bù Q7 được tính tại nghiệm GD9, không tại nghiệm GD9b. Trong mẫu, tăng trưởng tổng GD9b khớp gần (tiền gửi 0.0395 so 0.0398; dư nợ 0.0482 so 0.0448 mỗi quý), nhưng ngoài mẫu mô hình tăng nhanh hơn dữ liệu (tiền gửi 0.0560 so 0.0334; dư nợ 0.0537 so 0.0434) <!-- nguồn: reports/calibration/stage9b/growth_ldr_stage9b.csv, diag_gd9b.csv phần bo_bu -->.
- *Trần LDR.* Ở GD9b không ngân hàng-quý nào chạm trần LDR 1.60, cả khi khởi đầu từ 2023Q1 lẫn khi khởi đầu từ 2026Q3 (GD9: 87.5% ngân hàng chạm trần ở quý cuối khi khởi đầu từ 2026Q3). **Cả hai con số 0% này là hệ quả của bù tăng trưởng Q7, không phải bằng chứng về cơ chế** (GD9b.md, mục 3.5): bù làm tăng trưởng tiền gửi cao lên và dư nợ thấp xuống, nên LDR không chạm trần. Chẩn đoán bỏ bù (cùng nghiệm GD9b, khởi đầu 2023Q1, kịch bản A) cho tỷ lệ chạm trần 18.1% (quý 1–18) và 59.4% (quý 15–18); chẩn đoán bỏ bù chưa được chạy riêng cho khởi đầu 2026Q3. <!-- nguồn: reports/calibration/stage9b/diag_gd9b.csv phần bo_bu; ldr_cap_2026q3_stage9b.csv (month 18); reports/giai_doan/GD9b.md mục 3.5 -->
- *Dữ liệu.* 8 ngân hàng, không đại diện toàn hệ thống; lợi suất sổ sách khác lãi suất niêm yết và lãi suất khoản vay mới; danh mục chỉ đạo có thể chưa đầy đủ.
- *Cửa sổ ngắn.* Hiệu chỉnh trên 9 quý, ngoài mẫu lịch sử 5 quý; không đủ cho suy luận thống kê về tham số.
- *Bất định.* Kịch bản A tất định; khoảng P5–P95 chỉ phản ánh bốc thăm tuân thủ, không phản ánh bất định tham số hay cấu trúc mô hình.
- *Chỉ tiêu.* `nim_proxy` không phải NIM kế toán; trần LDR 1.60 là ràng buộc kỹ thuật, không phải tỷ lệ pháp lý.

### 6.5. Lưu ý khi diễn giải kết quả

- Chênh lệch A/B/C thể hiện tác động của việc thay quy tắc **trong mô hình**; không đủ để kết luận chỉ đạo thực tế làm thay đổi lãi suất với mức tương ứng. Độ lớn B−A tỷ lệ với giả định `policy_step`.
- Khoảng P5–P95 là độ phân tán giữa các lần chạy, không phải khoảng tin cậy của lãi suất toàn hệ thống.
- RMSE trong mẫu là độ khớp trên cửa sổ đã dùng để hiệu chỉnh; RMSE "ngoài mẫu" 2025Q3–2026Q3 dùng ON thực, nên là đối chiếu có lợi thế thông tin, không phải dự báo.
- Không chọn cấu hình theo kết quả ngoài mẫu (Q11) và không chỉnh tham số để kết quả khớp giả thuyết.
- Kịch bản khởi tạo từ 2023Q1 theo thiết kế; file khởi tạo 2026Q3 chỉ dùng để kiểm tra trần LDR.

## 7. Hướng mở rộng nghiên cứu

1. **Sửa sai lệch mức của phương trình huy động** (hạn chế a) trước khi xét lại biên: vd. kiểm tra ánh xạ CASA theo thời gian, hoặc chênh lệch neo ON theo nhóm ngân hàng. Mọi thay đổi phải là tùy chọn mặc định TẮT và hiệu chỉnh lại theo quy trình đăng ký trước.
2. **Hiệu chỉnh đồng thời theo hướng không bị nghiệm biên**: lưới được thiết kế trước rộng hơn hoặc phương pháp tối ưu liên tục, kèm tiêu chí dừng đặt trước; báo cáo hồ sơ hàm mục tiêu và mức nhận diện của từng tham số.
3. **Kiểm định ngoài mẫu sau chính sách** khi có lợi suất sổ sách Q4/2026 và Q1/2027 (khung GD11 đã sẵn sàng), đồng thời tải lại ON Q4/2026 sau khi quý kết thúc.
4. **Nhận diện `policy_step`, `policy_pressure`**: cần dữ liệu tần suất cao hơn (lãi suất khoản vay mới theo tháng, theo lĩnh vực) để tách tác động chỉ đạo khỏi biến động ON; hiện chỉ có thể phân tích độ nhạy.
5. **Tính dị biệt và tần suất**: tách khối người gửi tiền/người vay theo nhóm khách hàng; mô phỏng theo tháng để phân biệt các mốc chỉ đạo trong quý.
6. **Độ nhạy nhiều chiều**: thay đổi đồng thời nhiều tham số (vd. thiết kế Latin hypercube) để bắt tương tác, nhất là giữa λ, biên tổng và `policy_step`.
7. **Kịch bản C có nội dung kinh tế rõ hơn**: hiện cơ chế hạn chế cạnh tranh huy động hầu như không tạo khác biệt; cần xem lại giả định của C (do nhóm quyết định), không chỉnh tham số để C "khác" B.

## 8. Những nội dung cần hoàn thiện trước khi nghiệm thu

Phần kỹ thuật (mô hình, hiệu chỉnh GD9/GD9b, chạy A/B/C, độ nhạy, độ vững, khung kiểm định ngoài mẫu) đã hoàn tất trên nhánh `hieu-chinh-tham-so`. Còn lại:

- **TV1 – Huy:** duyệt báo cáo này, đặc biệt hộp "Những điều KHÔNG được diễn giải", cách báo B−A theo dải `policy_step` và các hạn chế (a)–(c); quyết định có xem lại giả định kinh tế của kịch bản C hay không.
- **TV2 – Minh:** xác nhận phương pháp tính lợi suất sổ sách và ánh xạ CASA; cung cấp lợi suất sổ sách Q4/2026 khi có báo cáo tài chính (cùng định nghĩa quy năm như các quý trước) để chạy GD11; rà soát danh mục chỉ đạo (đầy đủ, nguồn).
- **TV3 – Vũ:** chạy lại GD11 khi có dữ liệu Q4/2026; tải lại ON Q4/2026 sau 31/12/2026; cập nhật CLAUDE.md mục 4.2 (GD13).
- **Chung:** kiểm lại trên bản in số báo và năm của tài liệu [11], và đối chiếu toàn văn CV 9608 trên cổng NHNN nếu có, trước khi nộp.

## Tài liệu tham khảo

Các mục [1]–[13] lấy từ `docs/tai_lieu_tham_khao_da_xac_minh.md` (đã mở trực tiếp trang nhà xuất bản, RePEc/IDEAS, DOI, thư viện hoặc văn bản gốc, 22/11/2026); [14]–[15] là nguồn dữ liệu của dự án.

**ABM trong kinh tế và ngân hàng**

[1] Arthur, W. B., Holland, J. H., LeBaron, B., Palmer, R., & Tayler, P. (1997). Asset pricing under endogenous expectations in an artificial stock market. In W. B. Arthur, S. N. Durlauf, & D. A. Lane (Eds.), *The economy as an evolving complex system II* (Santa Fe Institute Studies in the Sciences of Complexity, Proceedings Vol. 27). Addison-Wesley. Bản working paper: SFI Working Paper 96-12-093 (12/12/1996), https://sites.santafe.edu/~wbarthur/Papers/Artif_Mkt.pdf

[2] Palmer, R. G., Arthur, W. B., Holland, J. H., LeBaron, B., & Tayler, P. (1994). Artificial economic life: A simple model of a stockmarket. *Physica D: Nonlinear Phenomena, 75*(1–3), 264–274. https://doi.org/10.1016/0167-2789(94)90287-9

[3] LeBaron, B., Arthur, W. B., & Palmer, R. (1999). Time series properties of an artificial stock market. *Journal of Economic Dynamics and Control, 23*(9–10), 1487–1516. https://doi.org/10.1016/S0165-1889(98)00081-5

[4] Farmer, J. D., & Foley, D. (2009). The economy needs agent-based modelling. *Nature, 460*(7256), 685–686. https://doi.org/10.1038/460685a

[5] Ostmann, J. (2026). *Agent-based modeling: Worlds within worlds* [Interactive story]. Santa Fe Institute. https://santafe.edu/features/agent-based-modeling-worlds-within-worlds (truy cập 22/11/2026)

[6] Chan-Lau, J. A. (2017). *ABBA: An agent-based model of the banking system* (IMF Working Paper No. 17/136). International Monetary Fund. https://doi.org/10.5089/9781484300688.001

[7] Papadopoulos, G. (2020). *Probing the mechanism: Lending rate setting in a data-driven agent-based model* (MPRA Paper No. 102749). University Library of Munich. https://mpra.ub.uni-muenchen.de/102749/

**Phần mềm**

[8] ter Hoeven, E., Kwakkel, J., Hess, V., Pike, T., Wang, B., rht, & Kazil, J. (2025). Mesa 3: Agent-based modeling with Python in 2025. *Journal of Open Source Software, 10*(107), 7668. https://doi.org/10.21105/joss.07668

**Truyền dẫn lãi suất ở Việt Nam**

[9] Le Phan Thi Dieu Thao, & Nguyen Thi Thu Trang. (2015). Interest rate pass-through estimates from error correction models ECM. *Ho Chi Minh City Open University Journal of Science – Economics and Business Administration, 5*(1), 3–11. https://doi.org/10.46223/HCMCOUJS.econ.en.5.1.906.2015

[10] Ngo, T. H., Ariyoshi, A., & Tran, T. X. A. (2021). Interest rate pass-through and exogenous factors: Evidence from Vietnam. *International Journal of Finance & Economics, 26*(1), 1299–1317. https://doi.org/10.1002/ijfe.1850

[11] Nguyễn, K. Q. B., & Nguyễn, H. H. N. (2013). Empirical evidence of asymmetric interest rate pass-through in Vietnam. *Tạp chí Phát triển Kinh tế* (Journal of Economic Development), (218), 78–93. https://vjol.info.vn/index.php/ed/article/view/34259 (năm theo số báo 218; trang VJOL ghi đăng tải 2018, chưa kiểm trên bản in)

**Văn bản chỉ đạo của NHNN**

[12] Ngân hàng Nhà nước Việt Nam. (2026, 18 tháng 10). *Công văn số 9608/NHNN-CSTT về triển khai các giải pháp hoạt động của tổ chức tín dụng*. Ngày ban hành theo CV 9736 [13] (dẫn lại trên thuvienphapluat.vn, luatvietnam.vn).

[13] Ngân hàng Nhà nước Việt Nam. (2026, 21 tháng 10). *Công văn số 9736/NHNN-CSTT về giảm mặt bằng lãi suất*. https://thuvienphapluat.vn/documents/law.aspx?id=A%3DpJNU9EazTn

**Nguồn dữ liệu của dự án**

[14] Ngân hàng Nhà nước Việt Nam. (2026). *Lãi suất thị trường liên ngân hàng* [Dữ liệu ON]. https://sbv.gov.vn/vi/lãi-suất-thị-trường-liên-ngân-hàng (lấy dữ liệu qua API của trang ngày 21/11/2026; xem `data/raw/README_sbv.md`)

[15] Nhóm nghiên cứu. (2026). Danh mục 24 văn bản chỉ đạo lãi suất 2023–2026 (CV 6385/NHNN-CSTT năm 2023, CV 4462/NHNN-CSTT năm 2024, Chỉ thị 01/CT-NHNN năm 2024, các công điện của Thủ tướng, …) [Dữ liệu]. `data/raw/chi_dao_lai_suat_2023_2026.csv` (nguồn từng văn bản ở cột `nguon`; chưa kiểm tra lại trong GD12).
