# BÀN GIAO VÀ ĐỐI CHIẾU HỢP ĐỒNG GIAO DIỆN

## 1. Tổng quan phần công việc TV3 – Vũ đã thực hiện

TV3 – Vũ phụ trách xây dựng và hoàn thiện các thành phần kỹ thuật hỗ trợ mô hình mô phỏng dựa trên tác nhân (Agent-Based Model – ABM), bao gồm lập trình hành vi người gửi tiền và người vay, tích hợp mô hình, triển khai các kịch bản mô phỏng, phân tích độ nhạy, kiểm thử và trực quan hóa kết quả.

Phiên bản hiện tại được xây dựng bằng Python, sử dụng thư viện Mesa và tổ chức mã nguồn theo cấu trúc lập trình hướng đối tượng (OOP).

Mô hình sử dụng dữ liệu khởi tạo của 8 ngân hàng thương mại Việt Nam, với kỳ khởi tạo Q1/2023. Một bước mô phỏng tương ứng với một quý. Mô hình thực hiện 18 bước, từ Q2/2023 đến Q3/2027, với thời điểm bắt đầu can thiệp chính sách trong mô phỏng là Q4/2026.

Các nội dung TV3 đã triển khai gồm:

- Xây dựng các quy tắc hành vi của người gửi tiền và người vay.
- Tích hợp các tác nhân ngân hàng, cơ quan quản lý, người gửi tiền và người vay vào mô hình ABM.
- Thiết lập hệ thống chạy lặp các kịch bản chính sách A, B và C.
- Triển khai phân tích kết quả theo nhóm ngân hàng, truyền dẫn chính sách và độ nhạy tham số.
- Xây dựng công cụ đối chiếu lãi suất mô phỏng với dữ liệu quan sát.
- Kiểm tra cơ chế độ trễ truyền dẫn chi phí vốn và các đặc điểm định tính của mô hình.
- Bổ sung kiểm thử logic, điều kiện giới hạn và khả năng tái lập kết quả.
- Tổ chức hệ thống biểu đồ, bảng dữ liệu, cấu hình và hướng dẫn chạy chương trình.

## 2. Các file mã nguồn và chức năng

### 2.1. Nhóm tác nhân – `src/agents/`

**`bank.py` – Tác nhân ngân hàng**

Mô tả hành vi điều chỉnh lãi suất huy động và lãi suất cho vay của từng ngân hàng.

Các chức năng chính:

- Xác định mức điều chỉnh lãi suất huy động dựa trên cạnh tranh huy động vốn và áp lực dư nợ/tiền gửi.
- Xác định lãi suất cho vay mục tiêu dựa trên chi phí vốn có độ trễ và biên lợi nhuận mục tiêu.
- Điều chỉnh lãi suất cho vay theo hệ số truyền dẫn chi phí vốn (`pass_through`).
- Thực hiện điều chỉnh giảm lãi suất khi ngân hàng tuân thủ chính sách.
- Theo dõi dư nợ, tiền gửi, chi phí vốn và chỉ tiêu `nim_proxy`.

`nim_proxy` là chỉ tiêu chênh lệch lãi suất đại diện trong mô hình, không đồng nhất với NIM tính từ báo cáo tài chính.

**`regulator.py` – Tác nhân cơ quan quản lý**

Mô phỏng việc kích hoạt và thực thi chính sách điều hành lãi suất.

Các chức năng chính:

- Xác định thời điểm chính sách bắt đầu có hiệu lực.
- Tính xác suất ngân hàng tuân thủ chỉ đạo dựa trên các giả định của mô hình.
- Kết hợp với tác nhân ngân hàng để mô phỏng phản ứng trước áp lực chính sách.

**`depositors.py` – Khối người gửi tiền**

Mô phỏng phản ứng tổng hợp của tiền gửi trước thay đổi lãi suất huy động.

Các chức năng chính:

- Xác định tăng trưởng tiền gửi cơ sở trong một quý.
- Điều chỉnh tăng trưởng tiền gửi theo chênh lệch lãi suất huy động giữa ngân hàng và thị trường.
- Áp dụng giới hạn biến động tiền gửi nhằm tránh những phản ứng cực đoan.

Khối người gửi tiền là quy tắc hành vi gộp, chưa mô phỏng từng khách hàng riêng biệt.

**`borrowers.py` – Khối người vay**

Mô phỏng phản ứng của nhu cầu tín dụng trước thay đổi lãi suất cho vay.

Các chức năng chính:

- Xác định tăng trưởng nhu cầu tín dụng cơ sở trong một quý.
- Điều chỉnh nhu cầu tín dụng theo mức lãi suất cho vay.
- Giới hạn tăng trưởng dư nợ theo điều kiện kỹ thuật của mô hình.

Khối người vay cũng được mô phỏng ở cấp độ tổng hợp, không phải từng khách hàng độc lập.

### 2.2. Mô hình trung tâm – `src/core/`

**`model.py` – Tích hợp mô hình ABM**

Đây là file điều phối hoạt động của toàn bộ các tác nhân.

Các chức năng chính:

- Khởi tạo ngân hàng từ dữ liệu CSV.
- Thiết lập tham số, kịch bản và hạt giống ngẫu nhiên (`seed`).
- Kết nối tác nhân ngân hàng với cơ quan quản lý, người gửi tiền và người vay.
- Thực hiện các bước mô phỏng theo quý.
- Thu thập dữ liệu tổng hợp toàn hệ thống và dữ liệu của từng ngân hàng.
- Cung cấp dữ liệu cho các chương trình phân tích và kiểm thử.

Một bước mô phỏng đại diện cho một quý, mặc dù một số tên biến kỹ thuật như `month` và `n_months` được giữ lại để tương thích với các thành phần đã xây dựng.

### 2.3. Nhóm chạy kịch bản và phân tích – `src/analysis/`

**`experiments.py` – Chạy các kịch bản mô phỏng**

Chương trình thực hiện các lần chạy lặp để đánh giá phản ứng của hệ thống ngân hàng dưới ba kịch bản:

- **Kịch bản A:** Không có chính sách can thiệp bổ sung.
- **Kịch bản B:** Cơ quan quản lý chỉ đạo giảm lãi suất cho vay.
- **Kịch bản C:** Kết hợp chỉ đạo giảm lãi suất cho vay và hạn chế cạnh tranh tăng lãi suất huy động.

Chức năng chính:

- Chạy nhiều lần mô phỏng với các hạt giống ngẫu nhiên được xác định trước.
- Tổng hợp kết quả theo từng kịch bản.
- Tính giá trị trung bình và khoảng phân vị 5%–95%.
- Xuất bảng kết quả, dữ liệu các lần chạy và biểu đồ so sánh.
- Hỗ trợ phân tích độ nhạy tham số.

**`advanced_analysis.py` – Phân tích nâng cao A/B/C/D**

Chương trình mở rộng việc phân tích kết quả theo bốn nhóm nội dung.

**A – Phân tích sự khác biệt giữa các nhóm ngân hàng**

- Phân nhóm ngân hàng quốc doanh, ngân hàng cổ phần lớn và ngân hàng cổ phần nhỏ trong phạm vi mẫu.
- Tính các chỉ tiêu tổng hợp theo từng nhóm.
- So sánh diễn biến lãi suất cho vay giữa các nhóm ngân hàng trong kịch bản B.

**B – Phân tích truyền dẫn chính sách**

- Tính chênh lệch lãi suất cho vay giữa các kịch bản B−A, C−A và C−B.
- Theo dõi sự thay đổi của chênh lệch trước và sau khi chính sách được kích hoạt.
- Tổng hợp tỷ lệ tuân thủ và mức giảm lãi suất trực tiếp.

**C – Phân tích độ nhạy và đối chiếu dữ liệu thực tế**

- Đánh giá mức độ nhạy của kết quả trước thay đổi các tham số chính.
- Sử dụng dữ liệu panel để xây dựng chuỗi lãi suất cho vay bình quân gia quyền theo dư nợ.
- Đối chiếu kết quả mô phỏng với chuỗi lãi suất quan sát.
- Tính các chỉ tiêu sai số MAE và RMSE.

**D – Kiểm tra hiện tượng đặc trưng và sai lệch lịch sử**

- Kiểm tra riêng cơ chế độ trễ truyền dẫn chi phí vốn.
- Đánh giá phản ứng của lãi suất cho vay sau một cú sốc giả định đối với lãi suất huy động.
- Phân tích sai lệch mô phỏng so với thực tế theo từng quý.
- Xác định độ lớn, chiều sai lệch và đặc điểm biến động mà mô hình chưa tái tạo đầy đủ.

**`sensitivity_grid.py` – Tạo các mức phân tích độ nhạy**

Đây là file dùng chung để tạo dải giá trị tham số cho các chương trình phân tích.

Các mức phân tích độ nhạy được tính tự động quanh giá trị cơ sở trong `configs/scenarios.yaml`, thay vì sử dụng những mức cố định độc lập với cấu hình.

Ví dụ, nếu `pass_through = 0.60` và phạm vi độ nhạy là ±30%, chương trình tạo các mức 0.42, 0.60 và 0.78.

Nhờ đó, khi TV1 – Huy điều chỉnh tham số cơ sở, chương trình phân tích độ nhạy tự động sử dụng các giá trị mới.

**`validation.py` – Kiểm tra tính hợp lệ của mô hình**

Thực hiện các kiểm tra bao gồm:

- Số ngân hàng và số bước mô phỏng.
- Thời điểm kích hoạt chính sách.
- Không xuất hiện tác động chính sách trước thời điểm kích hoạt.
- Chiều phản ứng lãi suất giữa các kịch bản.
- Giới hạn kỹ thuật về dư nợ và tiền gửi.
- Khả năng tái lập kết quả với cùng `seed`.

Các kiểm tra này nhằm xác nhận tính nhất quán của chương trình, không thay thế cho kiểm chứng thực nghiệm.

### 2.4. Nhóm tiện ích và kiểm thử

**`src/utils/output_utils.py`**

Quản lý việc tạo thư mục lưu kết quả theo thời điểm chạy, giúp các lần mô phỏng có thư mục riêng và hạn chế ghi đè dữ liệu.

**`tests/test_model.py`**

Chứa các bài kiểm thử tự động đối với các thành phần của mô hình, bao gồm hành vi tác nhân, điều kiện giới hạn, cơ chế chính sách và tính tái lập.

**`main.py`**

Là chương trình điều phối chính, cho phép thực hiện toàn bộ quy trình bằng một lệnh duy nhất.

Chương trình lần lượt:

1. Chạy các kịch bản A/B/C bằng `experiments.py`.
2. Chạy phân tích nâng cao A/B/C/D bằng `advanced_analysis.py`.
3. Xuất bảng dữ liệu và biểu đồ vào các thư mục kết quả tương ứng.

## 3. Các file cấu hình và dữ liệu

### 3.1. `configs/scenarios.yaml`

Chứa cấu hình chính của mô hình, bao gồm:

- Số bước mô phỏng.
- Số lần chạy lặp.
- Hạt giống ngẫu nhiên.
- Thời điểm kích hoạt chính sách.
- Các tham số hành vi và chính sách.
- Phạm vi phân tích độ nhạy.

Đây là file mà TV1 – Huy sử dụng để điều chỉnh các tham số chính sau khi thống nhất kết quả hiệu chỉnh.

### 3.2. `data/clean/abm_initial_8nganhang_2023Q1.csv`

Chứa dữ liệu trạng thái khởi tạo của 8 ngân hàng trong Q1/2023.

Các thông tin được sử dụng để xác định trạng thái ban đầu của tác nhân ngân hàng, như tiền gửi, dư nợ, lãi suất và tỷ lệ CASA.

### 3.3. `data/clean/abm_initial_8nganhang_2026Q3.csv`

Chứa trạng thái ngân hàng tại Q3/2026.

File này phục vụ đối chiếu hoặc thiết lập một trạng thái khởi tạo thay thế khi cần nghiên cứu giai đoạn khác. Đây không phải file khởi tạo mặc định của chương trình `main.py` hiện tại.

### 3.4. `data/clean/abm_panel_8nganhang_2023Q1_2026Q3.csv`

Chứa chuỗi dữ liệu theo quý của 8 ngân hàng từ Q1/2023 đến Q3/2026.

Dữ liệu được dùng để tính lãi suất cho vay bình quân gia quyền theo dư nợ và thực hiện đối chiếu với kết quả mô phỏng.

Các chỉ tiêu lãi suất được xây dựng từ dữ liệu tài chính cần được nhận diện đúng là chỉ tiêu thay thế, không mặc nhiên đồng nhất với lãi suất niêm yết hoặc lãi suất áp dụng cho từng khoản vay.

## 4. Các biểu đồ đã xây dựng và ý nghĩa

### 4.1. Biểu đồ tổng hợp ba kịch bản

**File: `fig_scenarios.png`**

Biểu đồ thể hiện diễn biến lãi suất cho vay bình quân của hệ thống ngân hàng trong ba kịch bản A, B và C theo từng quý mô phỏng.

Ý nghĩa:

- So sánh đường diễn biến lãi suất trong điều kiện không can thiệp và có can thiệp chính sách.
- Đánh giá sự khác biệt giữa chính sách chỉ đạo giảm lãi suất và chính sách kết hợp.
- Minh họa mức độ phân tán của kết quả qua khoảng phân vị 5%–95%.
- Quan sát diễn biến trước và sau mốc chính sách.

Biểu đồ giúp đánh giá sự thay đổi của lãi suất trong các kịch bản giả định, không được hiểu là bằng chứng nhân quả thực nghiệm từ dữ liệu lịch sử.

### 4.2. Biểu đồ A – Sự khác biệt giữa các nhóm ngân hàng

**File: `A_loan_rate_nhom.png`**

Biểu đồ mô tả lãi suất cho vay bình quân của ba nhóm ngân hàng trong kịch bản B.

Ba nhóm được sử dụng trong nghiên cứu gồm ngân hàng quốc doanh, ngân hàng cổ phần lớn và ngân hàng cổ phần nhỏ theo cách phân loại trong mẫu.

Ý nghĩa:

- Quan sát sự khác biệt về mặt bằng lãi suất giữa các nhóm.
- Đánh giá diễn biến lãi suất theo thời gian của từng nhóm.
- Xem xét tính không đồng nhất giữa các tác nhân ngân hàng trong mô hình.

Biểu đồ phản ánh mức lãi suất của từng nhóm, chưa trực tiếp đo lường tác động chính sách riêng của từng nhóm. Để đánh giá tác động chính sách theo nhóm cần đối chiếu kịch bản có và không có can thiệp.

### 4.3. Biểu đồ B – Truyền dẫn chính sách

**File: `B_chuyen_dan_chinh_sach.png`**

Biểu đồ mô tả chênh lệch lãi suất cho vay giữa ba cặp kịch bản:

- B−A: Chỉ đạo giảm lãi suất so với không can thiệp.
- C−A: Chính sách kết hợp so với không can thiệp.
- C−B: Chính sách kết hợp so với chỉ đạo giảm lãi suất đơn thuần.

Ý nghĩa:

- Xác định mức thay đổi lãi suất do các quy tắc can thiệp trong mô hình tạo ra.
- Phân biệt kết quả của từng phương án chính sách.
- Theo dõi tốc độ hình thành và tích lũy chênh lệch lãi suất sau thời điểm can thiệp.

Chênh lệch âm cho biết lãi suất ở kịch bản đứng trước thấp hơn kịch bản đối chứng.

### 4.4. Biểu đồ C1 – Phân tích độ nhạy tham số

**File: `C_do_nhay.png`**

Biểu đồ thể hiện sự thay đổi của lãi suất cho vay cuối kỳ khi lần lượt điều chỉnh ba tham số:

- `pass_through`: Hệ số điều chỉnh lãi suất theo chi phí vốn.
- `depositor_sensitivity`: Độ nhạy của tiền gửi trước chênh lệch lãi suất huy động.
- `policy_pressure`: Mức áp lực chính sách ảnh hưởng đến xác suất tuân thủ.

Ý nghĩa:

- Đánh giá kết quả mô hình có nhạy cảm với các giả định đầu vào hay không.
- Xác định tham số nào làm kết quả thay đổi nhiều hơn trong phạm vi khảo sát.
- Hỗ trợ lựa chọn và kiểm tra tính hợp lý của bộ tham số sau hiệu chỉnh.

Các mức độ nhạy được tạo tự động quanh giá trị cơ sở trong file YAML. Việc phân tích độ nhạy không đồng nghĩa với ước lượng tham số từ dữ liệu thực tế.

### 4.5. Biểu đồ C2 – Đối chiếu lãi suất thực tế và mô phỏng

**File: `C_thuc_te_vs_mo_phong.png`**

Biểu đồ so sánh lãi suất cho vay bình quân quan sát với lãi suất mô phỏng theo kịch bản A trong giai đoạn lịch sử có dữ liệu.

Ý nghĩa:

- Đánh giá mức độ phù hợp của kết quả mô phỏng với diễn biến lịch sử.
- Quan sát sự khác biệt về xu hướng và biên độ thay đổi.
- Làm cơ sở tính MAE, RMSE và xác định những hạn chế của cấu trúc mô hình.

Kết quả đối chiếu cho thấy mô hình chưa tái tạo đầy đủ những biến động lớn của lãi suất thực tế. Vì vậy, không thể chỉ dựa vào biểu đồ này để kết luận mô hình có khả năng dự báo thực nghiệm tốt.

### 4.6. Biểu đồ D1 – Kiểm tra độ trễ truyền dẫn chi phí vốn

**File: `D1_kiem_tra_do_tre.png`**

Biểu đồ minh họa phản ứng của lãi suất cho vay khi lãi suất huy động chịu một cú sốc giả định, so với trường hợp đối chứng không có cú sốc.

Ý nghĩa:

- Kiểm tra xem cơ chế sử dụng chi phí vốn trễ có hoạt động như thiết kế hay không.
- Quan sát thời điểm lãi suất cho vay bắt đầu phản ứng.
- Làm rõ rằng chi phí vốn huy động không nhất thiết được truyền ngay vào lãi suất cho vay trong cùng một bước mô phỏng.

Đây là kiểm tra cơ chế lập trình. Kết quả không chứng minh rằng độ trễ quan sát được trong thực tế nhất thiết bằng một quý.

### 4.7. Biểu đồ D2 – Sai lệch lịch sử theo quý

**File: `D2_sai_lech_lich_su_theo_quy.png`**

Biểu đồ thể hiện sai lệch giữa lãi suất mô phỏng và lãi suất quan sát trong từng quý.

Sai lệch được xác định theo công thức:

Sai lệch = Lãi suất mô phỏng − Lãi suất thực tế.

Ý nghĩa:

- Sai lệch dương: lãi suất mô phỏng cao hơn thực tế.
- Sai lệch âm: lãi suất mô phỏng thấp hơn thực tế.
- Sai lệch tuyệt đối lớn: mô hình tái tạo chưa tốt mức lãi suất ở quý tương ứng.
- Sai lệch có tính hệ thống: gợi ý khả năng mô hình đang đánh giá cao hoặc thấp mặt bằng lãi suất trong một giai đoạn.

Biểu đồ hỗ trợ nhận diện những thời kỳ mà mô hình chưa phản ánh tốt biến động lịch sử, từ đó làm cơ sở thảo luận về điều kiện hiệu chỉnh và giới hạn nghiên cứu.

## 5. Các bảng dữ liệu kết quả đã xuất

### 5.1. Thư mục `_KichBan`

| File | Nội dung |
|---|---|
| `bang_ket_qua.csv` | Bảng thống kê kết quả cuối kỳ theo kịch bản |
| `runs_A.csv` | Dữ liệu các lần chạy kịch bản A |
| `runs_B.csv` | Dữ liệu các lần chạy kịch bản B |
| `runs_C.csv` | Dữ liệu các lần chạy kịch bản C |
| `sensitivity.csv` | Kết quả phân tích độ nhạy ở chương trình kịch bản |
| `run_metadata.json` | Thông tin về cấu hình và lần chạy |

### 5.2. Thư mục `_PhanTichABC`

| File | Nội dung |
|---|---|
| `A_du_lieu_tung_ngan_hang.csv` | Dữ liệu mô phỏng của từng ngân hàng theo quý và lần chạy |
| `A_nhom_ngan_hang.csv` | Các chỉ tiêu tổng hợp theo nhóm ngân hàng |
| `B_chuyen_dan_tung_lan_chay.csv` | Chênh lệch chính sách của từng lần chạy |
| `B_chuyen_dan_trung_binh.csv` | Chênh lệch chính sách bình quân |
| `B_tuan_thu_chinh_sach.csv` | Tỷ lệ và xác suất tuân thủ chính sách |
| `C_bang_do_nhay.csv` | Kết quả phân tích độ nhạy tham số |
| `C_lai_suat_thuc_te_tu_panel.csv` | Chuỗi lãi suất quan sát tính từ dữ liệu panel |
| `C_so_sanh_thuc_te.csv` | Giá trị thực tế, mô phỏng và sai lệch từng quý |
| `C_sai_so.csv` | Chỉ tiêu MAE và RMSE |
| `D_kiem_tra_nhiem_vu_4_4.json` | Kết quả kiểm tra độ trễ và đánh giá đặc điểm mô hình |
| `D_chi_tiet_sai_lech_lich_su.csv` | Chẩn đoán sai lệch lịch sử theo từng quý |

## 6. Những nội dung TV1 – Huy cần xác nhận

TV1 – Huy chịu trách nhiệm thống nhất kiến trúc, giả định và các quy tắc kinh tế của mô hình.

Các nội dung cần xác nhận gồm:

1. **Quy tắc hành vi ngân hàng và cơ quan quản lý:** Rà soát `bank.py` và `regulator.py`, đặc biệt là quy tắc hình thành lãi suất mục tiêu, xác suất tuân thủ chính sách và mức giảm lãi suất.
2. **Đơn vị đo lường:** Lãi suất được biểu diễn bằng %/năm; tỷ lệ như CASA được biểu diễn dưới dạng thập phân từ 0 đến 1; mỗi bước mô phỏng hiện tương ứng một quý.
3. **Chỉ tiêu `nim_proxy`:** Thống nhất đây là chỉ tiêu chênh lệch lãi suất đại diện, không phải NIM BCTC.
4. **Bộ tham số:** Rà soát và cập nhật các tham số cơ sở trong `configs/scenarios.yaml`, dựa trên kết quả ước lượng và các giả định được nhóm chấp thuận.
5. **Mốc chính sách:** Xác nhận việc quy đổi các mốc chỉ đạo chính sách từ kế hoạch theo tháng sang mô hình theo quý. Mốc Q4/2026 hiện là lựa chọn mô phỏng và cần được phân biệt với thời điểm ban hành văn bản thực tế.
6. **Giới hạn mô hình:** Xác nhận những tham số và quy tắc đang mang tính giả định trước khi nhóm đưa ra kết luận nghiên cứu.

## 7. Những nội dung TV2 – Minh cần xác nhận và bàn giao

TV2 – Minh phụ trách dữ liệu, đối chiếu nguồn và hỗ trợ hiệu chỉnh tham số.

Các nội dung cần xác nhận gồm:

1. Kiểm tra nguồn gốc, thời điểm và đơn vị của dữ liệu khởi tạo 8 ngân hàng tại Q1/2023.
2. Xác nhận dữ liệu panel 8 ngân hàng giai đoạn Q1/2023–Q3/2026.
3. Làm rõ phương pháp xây dựng chỉ tiêu lãi suất cho vay và lãi suất huy động từ dữ liệu tài chính.
4. Cung cấp tài liệu gốc và bảng mô tả các biến.
5. Bàn giao các tham số đã ước lượng, phương pháp ước lượng và phạm vi giá trị hợp lý.
6. Phối hợp với Huy kiểm tra mức độ phù hợp của mô hình đối với chuỗi lãi suất lịch sử.

## 8. Kết quả kiểm tra và giới hạn nghiệm thu

Phiên bản hiện tại đã có mã nguồn, cấu hình, dữ liệu sạch, các kịch bản mô phỏng, biểu đồ A/B/C/D và bộ kiểm tra logic.

Các kết quả đã lưu cho thấy:

- Mô hình đã chạy với 8 ngân hàng.
- Có kết quả mô phỏng 60 lần cho mỗi kịch bản A/B/C.
- Bộ kiểm tra `validation.py` đã ghi nhận 7/7 điều kiện đạt.
- Phần D đã có kết quả kiểm tra độ trễ và chẩn đoán sai lệch lịch sử.
- Đã tạo được biểu đồ so sánh lãi suất quan sát với mô phỏng, cùng các chỉ số MAE và RMSE.

Tuy nhiên, những kết quả này chủ yếu xác nhận chương trình vận hành theo các quy tắc đã thiết kế.

Các nội dung chưa thể coi là nghiệm thu thực nghiệm hoàn chỉnh gồm:

- Chưa xác nhận toàn bộ tham số đã được hiệu chỉnh từ dữ liệu thực tế.
- Chưa có kết quả đánh giá ngoài mẫu được xác nhận.
- Chưa chứng minh mô hình tái tạo tốt toàn bộ biên độ biến động lãi suất lịch sử.
- Chưa kiểm chứng thực nghiệm tác động chính sách đối với giai đoạn sau Q3/2026.
- Các giả định kinh tế và kết luận chính sách cuối cùng vẫn cần Huy và Minh thống nhất.

Vì vậy, phần triển khai kỹ thuật của TV3 có thể được bàn giao để nhóm tiếp tục hiệu chỉnh và hoàn thiện nghiên cứu; không nên đồng nhất việc chương trình chạy đúng với việc mô hình đã được kiểm chứng thực nghiệm thành công.

## 9. Hướng dẫn chạy và bàn giao

### 9.1. Cài đặt môi trường

Sử dụng Python và cài đặt các thư viện được liệt kê trong `requirements.txt` sau khi file này được bổ sung và kiểm tra.

```powershell
python -m pip install -r requirements.txt
```

### 9.2. Chạy kiểm thử tự động

```powershell
python -m pytest -v
```

### 9.3. Chạy kiểm tra logic mô hình

```powershell
python -m src.analysis.validation --banks data/clean/abm_initial_8nganhang_2023Q1.csv
```

### 9.4. Chạy toàn bộ mô phỏng và phân tích

```powershell
python main.py
```

Chương trình lần lượt thực hiện các kịch bản A/B/C và phân tích nâng cao A/B/C/D.

Các kết quả được lưu trong thư mục `outputs/`, theo từng lần chạy. Các thư mục kết quả gồm:

- `_KichBan`: Kết quả mô phỏng và thống kê kịch bản.
- `_PhanTichABC`: Kết quả phân tích nhóm ngân hàng, chính sách, độ nhạy, đối chiếu lịch sử và kiểm tra 4.4.

## 10. Kết luận bàn giao

TV3 – Vũ đã xây dựng và tích hợp hệ thống kỹ thuật phục vụ mô phỏng ABM, triển khai các kịch bản chính sách A/B/C, phân tích nâng cao A/B/C/D, kiểm thử logic, phân tích độ nhạy và đối chiếu dữ liệu lịch sử.

Sản phẩm bàn giao gồm mã nguồn Python có cấu trúc OOP, cấu hình YAML, dữ liệu CSV, các chương trình kiểm thử, hệ thống bảng kết quả, 7 biểu đồ trực quan hóa và tài liệu hướng dẫn.

Hệ thống cho phép TV1 – Huy điều chỉnh các tham số chính trong YAML và chạy lại toàn bộ chương trình mà không cần trực tiếp thay đổi các mức phân tích độ nhạy trong nhiều file khác nhau.

Phần triển khai kỹ thuật đã sẵn sàng phục vụ bước hiệu chỉnh và đánh giá tiếp theo. Việc xác nhận tính hợp lý của tham số, kết quả thực nghiệm và các kết luận chính sách thuộc quá trình phối hợp cuối cùng giữa các thành viên trong nhóm.