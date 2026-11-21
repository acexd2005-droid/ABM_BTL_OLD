# CLAUDE.md – Hướng dẫn làm việc cho Claude trong dự án ABM_BTL

Trả lời và viết tài liệu bằng **tiếng Việt**. Comment trong code có thể tiếng Việt hoặc tiếng Anh, giữ nhất quán với file đang sửa.

## 1. Dự án là gì

Mô hình mô phỏng dựa trên tác nhân (ABM) bằng **Python + Mesa 3.3.1**, phân tích phản ứng của **8 ngân hàng thương mại Việt Nam** trước chỉ đạo giảm lãi suất cho vay của NHNN.

- 1 bước = **1 quý**. Khởi tạo Q1/2023, chạy 18 bước (Q2/2023 → Q3/2027).
- Chính sách kích hoạt khi `model.month >= policy_month` (mặc định `policy_month: 14` → bước 15 = **Q4/2026**).
- Kịch bản: **A** không can thiệp · **B** chỉ đạo giảm lãi suất cho vay · **C** = B + hạn chế cạnh tranh huy động.
- Lãi suất có đơn vị **%/năm**; tăng trưởng tiền gửi/dư nợ tính **mỗi quý**.
- Tên biến `month`, `n_months`, `policy_month`, `finish_month` giữ lại để tương thích, nhưng **nghĩa là quý**. Không đổi tên các biến này.

Nhóm: **Huy (TV1)** – quy tắc hành vi & tham số · **Minh (TV2)** – dữ liệu · **Vũ (TV3)** – code & chạy mô phỏng.

## 2. Cấu trúc mã nguồn

| Đường dẫn | Vai trò |
|---|---|
| `main.py` | Chạy toàn bộ: `experiments` rồi `advanced_analysis` |
| `configs/scenarios.yaml` | **Nơi duy nhất** để chỉnh tham số |
| `src/agents/bank.py` | Ngân hàng: lãi suất huy động, lãi suất cho vay (truyền dẫn chi phí vốn trễ), tuân thủ chỉ đạo |
| `src/agents/regulator.py` | NHNN: bật chính sách, xác suất tuân thủ dạng logistic |
| `src/agents/depositors.py` | Khối người gửi tiền gộp |
| `src/agents/borrowers.py` | Khối người vay gộp |
| `src/core/model.py` | `ABMModel`: trình tự 1 quý, ràng buộc, ghi lịch sử |
| `src/analysis/experiments.py` | Chạy A/B/C nhiều lần, độ nhạy, biểu đồ → `outputs/*_KichBan/` |
| `src/analysis/advanced_analysis.py` | Phân tích nhóm, truyền dẫn, độ nhạy, đối chiếu lịch sử, độ trễ → `outputs/*_PhanTichABC/` |
| `src/analysis/sensitivity_grid.py` | Tạo dải độ nhạy ±`sensitivity_relative_width` |
| `src/analysis/validation.py` | Kiểm tra logic mô hình |
| `tests/test_model.py` | Test tự động (pytest) |
| `data/clean/` | Dữ liệu khởi tạo 2023Q1, 2026Q3 và panel 2023Q1–2026Q3 |
| `docs/`, `report/` | Tài liệu bàn giao và dự thảo báo cáo |

Trình tự trong `ABMModel.step()`: tính `market_rate` → Regulator → Bank → DepositorBlock → BorrowerBlock → `finish_month()` + kiểm tra ràng buộc → ghi lịch sử. **Không đổi thứ tự này** khi chưa được duyệt.

## 3. Lệnh thường dùng (macOS, đã kích hoạt `.venv`)

```bash
source .venv/bin/activate
python -m pytest -v
python -m src.analysis.validation --banks data/clean/abm_initial_8nganhang_2023Q1.csv
python main.py                                   # chạy đầy đủ (vài phút)
python main.py --runs 5 --sensitivity-runs 2     # chạy nhanh để thử
```

Khi chỉ cần kiểm tra code có chạy không, dùng bản chạy nhanh. Chỉ chạy `python main.py` đầy đủ khi cần kết quả cuối.

## 4. Quy tắc bắt buộc

### 4.1. Tính toàn vẹn nghiên cứu
- **Không thay đổi công thức hành vi** trong `src/agents/` hoặc trình tự trong `model.py` nếu người dùng chưa yêu cầu rõ ràng. Nếu nâng cấp cần đổi hành vi, thêm dưới dạng **tùy chọn bật/tắt trong YAML, mặc định TẮT**, để kết quả cũ tái lập được.
- **Không chọn hay chỉnh tham số để có kết quả "đẹp"** hoặc khớp giả thuyết. Hiệu chỉnh phải theo tiêu chí rõ ràng (vd. tối thiểu RMSE trên dữ liệu panel) và ghi lại phương pháp.
- **Không tự điền số liệu giả** vào `data/clean/`. Không sửa file dữ liệu gốc; nếu cần biến đổi, tạo file mới và ghi rõ cách tạo.
- Không diễn giải kết quả A/B/C là tác động chính sách thực tế; MAE/RMSE hiện là đối chiếu trong mẫu, không phải dự báo ngoài mẫu.

### 4.2. Tham số
- Tham số chỉnh trong `configs/scenarios.yaml`, không hard-code giá trị mới trong Python.
- Khi thêm tham số mới: thêm vào YAML (có comment ý nghĩa + đơn vị), đọc trong `ABMModel.__init__` bằng `p.get(...)` với giá trị mặc định **trùng với YAML**, và cập nhật bảng tham số trong `README.md`.
- Mặc định trong `model.py` (`p.get(...)`) và mặc định trong hàm khởi tạo các agent **phải trùng** `configs/scenarios.yaml` cho mọi khóa; `tests/test_constants_yaml.py` kiểm điều này (GD9a). Ghi chú cũ "`max_loan_to_deposit=1.15`, `policy_month=12` khác YAML" đã lỗi thời. Dù vậy, vẫn nên truyền tham số từ YAML, không dựa vào mặc định trong code.
- Các hằng số hành vi trước đây cứng trong code (`0.018` → `base_deposit_rate_step`, `1.35` → `loan_spread_add`, `reference_rate=9.5` → `borrower_reference_rate`, `margin_floor=2.2`, hệ số logistic tuân thủ, `target_margin`, `funding_cost_add`, ngưỡng LDR, các chặn tăng trưởng, `depositor_min_growth`, ...) nay đã ở YAML; danh sách đầy đủ và kiểm tra "không còn hằng số cũ trong agent" nằm ở `tests/test_constants_yaml.py`. Còn cứng trong code (giữ, trùng ràng buộc mục 6): miền hợp lệ lãi suất 0–20 / 0–14 và sàn 0.01 (Q5). Không đổi giá trị mà không được duyệt.
- Cấu hình chuẩn cho kết quả hiện hành: `configs/scenarios_macro.yaml` (`macro_driver: exogenous`) và bộ hiệu chỉnh `configs/scenarios_calibrated.yaml` (GD9b); `scenarios.yaml` giữ nguyên để golden không đổi.

### 4.3. Code
- Giữ tương thích **Mesa 3.3.1** (agent khởi tạo bằng `super().__init__(model)`, gọi qua `agents_by_type[...]`). Không nâng cấp phiên bản thư viện trong `requirements.txt` nếu không được yêu cầu.
- Giữ nguyên tên cột CSV đầu ra (`month`, `quarter`, `scenario`, `loan_rate`, ...) vì các script phân tích phụ thuộc vào chúng.
- Mọi kết quả ngẫu nhiên phải đi qua `model.random` và seed để tái lập được.
- Không commit `outputs/`, `.venv/` (đã có trong `.gitignore`).

## 5. Quy trình cho mỗi thay đổi

1. Đọc các file liên quan trước, rồi **trình bày kế hoạch ngắn** và chờ người dùng duyệt nếu thay đổi chạm tới `src/agents/`, `src/core/` hoặc dữ liệu.
2. Làm trên nhánh riêng (`git checkout -b <ten-nhanh>`), không sửa trực tiếp `main`.
3. Thêm hoặc cập nhật test trong `tests/` cho hành vi mới.
4. Chạy `python -m pytest -v` và `validation`; tất cả phải qua. Không xóa hay nới lỏng test có sẵn để cho qua.
5. Nếu thay đổi ảnh hưởng kết quả: chạy bản nhanh, so sánh với trước khi sửa (vd. `loan_rate` trung bình A/B/C, chênh lệch B−A), báo lại con số.
6. Cập nhật `README.md` hoặc `docs/` cho phần đã đổi.
7. Commit với message tiếng Việt mô tả rõ thay đổi. **Không push** khi người dùng chưa yêu cầu.

## 6. Kiểm tra hợp lý kinh tế sau mỗi thay đổi

- Kịch bản B và C phải có `loan_rate` **không cao hơn** A sau Q4/2026.
- Trước bước kích hoạt chính sách, A/B/C phải **trùng nhau** với cùng seed.
- Lãi suất trong miền hợp lệ: cho vay 0–20%, huy động 0–14%.
- `loans <= deposits * max_loan_to_deposit`.
- Lãi suất cho vay phản ứng **trễ** với cú sốc chi phí vốn (qua `lagged_funding_cost`).

Nếu kết quả vi phạm các điểm trên, dừng lại và báo cho người dùng thay vì tự chỉnh tham số.
## 7. Vòng kiểm tra tự động với reviewer-abm

Sau mỗi giai đoạn có thay đổi trong `src/agents/`, `src/core/` hoặc `configs/`:

1. Chạy test. Nếu qua, gọi subagent `reviewer-abm` để kiểm tra (không tự đánh giá thay reviewer).
2. Nếu reviewer trả về **KHÔNG ĐẠT** hoặc có vấn đề NGHIÊM TRỌNG/TRUNG BÌNH thuộc về **code hoặc cơ chế**: tự sửa rồi gọi lại reviewer.
3. Tối đa **3 vòng** sửa cho mỗi giai đoạn. Sau 3 vòng vẫn chưa đạt thì dừng, báo cáo cho người dùng.
4. Vấn đề nằm trong mục "CẦN NGƯỜI DÙNG/NHÓM QUYẾT ĐỊNH" (giá trị tham số, giả định kinh tế): **không tự sửa**, dừng lại và hỏi người dùng.
5. Chỉ commit giai đoạn khi reviewer trả về ĐẠT hoặc ĐẠT CÓ ĐIỀU KIỆN. Đưa nguyên văn báo cáo cuối của reviewer vào báo cáo gửi người dùng.

## 8. Chế độ điều phối (`/dieu-phoi`) – trưởng nhóm Huy duyệt ngày 21/11/2026

Khi chạy qua `/dieu-phoi` và subagent `thuc-thi-giai-doan`, trưởng nhóm cho phép chạy không cần hỏi giữa chừng, với các quy tắc sau (ưu tiên hơn mục 5.1, 5.7 và 7.4 trong chế độ này):

1. **Kế hoạch đã duyệt sẵn:** nội dung từng giai đoạn trong `docs/ke_hoach/LO_TRINH.md` coi như kế hoạch đã được duyệt (mục 5.1). Việc chạm `src/agents/`, `src/core/` chỉ được phép đúng phạm vi LO_TRINH.md ghi.
2. **Quyết định mặc định khi gặp lựa chọn kinh tế/tham số chưa có trong "Quyết định đã duyệt sẵn":**
   - Chọn phương án **bảo thủ**: không đổi giá trị trong `configs/scenarios.yaml`; cơ chế mới là tùy chọn mặc định TẮT; khi có nhiều cách hợp lý, chạy và báo cáo **cả hai**, chọn một làm chính theo tiêu chí đã ghi trước (không theo kết quả nào "đẹp" hơn).
   - Ghi vào mục "CẦN HUY QUYẾT ĐỊNH" của báo cáo giai đoạn và bảng "Quyết định đang mở" trong `docs/ke_hoach/TRANG_THAI.md`.
   - Chỉ chạy tiếp các giai đoạn không phụ thuộc vào quyết định đó theo cách làm thay đổi kết luận; nếu mọi giai đoạn còn lại đều phụ thuộc → dừng.
3. **Commit và push:** commit sau mỗi giai đoạn đạt; được phép `git push fork <nhánh>` (chỉ remote `fork`). Không push `origin`, không sửa `main`, không tạo PR.
4. **Vẫn dừng như cũ** khi: vi phạm mục 6; golden thay đổi ngoài phép của LO_TRINH.md; reviewer KHÔNG ĐẠT sau 3 vòng; cần dữ liệu không có.
5. Không đụng thư mục `docs/nhat_ky_lam_viec/` (của người dùng).
6. Mọi báo cáo giai đoạn nằm ở `reports/giai_doan/`; trưởng nhóm duyệt sau cùng qua `reports/giai_doan/TONG_HOP.md`.
