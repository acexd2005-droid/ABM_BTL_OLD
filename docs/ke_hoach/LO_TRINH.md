# Lộ trình hoàn thành dự án ABM_BTL (đã được trưởng nhóm Huy duyệt ngày 21/11/2026)

Dùng bởi `/dieu-phoi` và subagent `thuc-thi-giai-doan`. Mỗi giai đoạn tự chứa: người thực thi chỉ cần đọc mục này + CLAUDE.md + báo cáo tiên quyết.

## Nhánh làm việc
`hieu-chinh-tham-so`. Push chỉ lên remote `fork`. Không sửa `main`.

## Bối cảnh đã chốt (tóm tắt các giai đoạn trước)
- Panel: `data/clean/abm_panel_8nganhang_2023Q1_2026Q3.csv` (8 NH × 15 quý). `deposit_rate_pct` và `loan_rate_pct` là **lợi suất sổ sách**; `deposit_rate_pct` tính trên TỔNG tiền gửi (gồm CASA). Ánh xạ: r^D_mô_hình = deposit_rate_pct/(1−casa); chi phí vốn = deposit_rate_pct + 0.15.
- `deposit_rate_basis: term` là mặc định (GĐ8a). Golden hiện hành là bản `term`; `tests/golden_total/` lưu bản cũ.
- Dữ liệu vĩ mô: `data/raw/sbv_lnh_qua_dem_theo_quy.csv` (ON bình quân quý, cột `bq_gian_don`), `data/raw/sbv_lai_suat_dieu_hanh_quy.csv`, `data/raw/chi_dao_lai_suat_2023_2026.csv` (24 văn bản/sự kiện, có nguồn; danh mục có thể chưa đầy đủ).
- GĐ7 (`reports/calibration/estimates_stage7.md`): λ (c) = 0.274, CI bootstrap [0.158; 0.395]; (d1) 0.315 [0.224; 0.449]. **λ = 0.48 trong configs nằm ngoài CI.** b+γ=1 không bị bác ở (a)(b)(c). σ, ε không nhận diện được. Tăng trưởng nền dữ liệu ~0.045 (TG) và ~0.05 (DN)/quý so với 0.004/0.006 trong mô hình; 42% g^D và 59% g^L vượt ngưỡng chặn. Mùa vụ mạnh ở Q4.
- GĐ7b (`estimates_stage7b.md`): quy tắc huy động hiện hành không mô tả được dữ liệu; φ = 0.177 (neo về ON_{t−1} + 1.2723).
- GĐ8 (`reports/stage8/summary_stage8.md`): `macro_driver: exogenous` giảm RMSE khử mức của LS cho vay 0.894 → 0.505; sai số mức còn +0.97 điểm %; biên độ chữ V 0.45 lần thực.
- **Chỉ đạo thực tế tháng 10/2026** (CV 9608, 9736): giảm ≥0.5%/năm LS huy động kỳ hạn ≥6 tháng; giảm 1.5–2%/năm LS cho vay SXKD. Trùng thời điểm và nội dung với kịch bản C (chính sách từ Q4/2026).

## Quyết định đã duyệt sẵn (người thực thi áp dụng, không hỏi lại)
D1. `macro_lending_on_coef = 0` (không dùng số hạng ON trong cho vay).
D2. Cấu hình chuẩn cho mọi giai đoạn sau: `configs/scenarios_macro.yaml` = `scenarios.yaml` + `macro_driver: exogenous`, `deposit_rate_basis: term`. `scenarios.yaml` giữ `macro_driver: none` để golden không đổi.
D3. `macro_dep_spread = 1.2723`; ON sau 2026Q3 giữ 3.946 cho mọi kịch bản. ON thực tế Q4/2026 CHỈ dùng cho kiểm định ngoài mẫu (GD11), không đưa vào kịch bản.
D4. Thước đo độ khớp báo cáo: chính = RMSE khử mức + tỷ lệ biên độ chữ V + quý đáy; phụ = RMSE thô, sai số trung bình. Hàm mục tiêu hiệu chỉnh xem GD9.
D5. Không sửa `configs/scenarios.yaml` ngoài việc thêm khóa mới (với giá trị = hành vi hiện tại). Bộ tham số hiệu chỉnh ghi vào file mới `configs/scenarios_calibrated.yaml`.
D6. `policy_pressure`, `policy_step` là giả định kịch bản; chỉ phân tích độ nhạy (GD10), không hiệu chỉnh, trừ khi GD7c chứng minh nhận diện được – khi đó vẫn chỉ BÁO CÁO, không đổi giá trị.
D7. Q1, Q2 trong TRANG_THAI.md: dùng mặc định đã ghi ở đó.
D8. Được phép thay golden **chỉ** ở GD9a nếu và chỉ nếu kết quả bitwise thay đổi do lỗi số học không thể tránh — mặc định là golden PHẢI giữ nguyên.

---

## GD7c – Ghi quyết định GĐ8 + chỉ đạo lãi suất và biên cho vay (KHÔNG sửa mô hình)
Tiên quyết: không. Kết quả: `reports/calibration/*_stage7c.*`.
1. Tạo `configs/scenarios_macro.yaml` theo D2 (test: tải được, khác `scenarios.yaml` đúng ở các khóa đã nêu). Ghi các quyết định D1–D3 vào mục "Quyết định" của `reports/stage8/summary_stage8.md` (sửa trong script sinh md nếu md sinh tự động).
2. Biến cường độ chỉ đạo theo quý I_q từ `data/raw/chi_dao_lai_suat_2023_2026.csv`: 0 = không văn bản; 1 = có văn bản yêu cầu giảm/ổn định LS (mọi `loai` trừ `thay_doi_LS_dieu_hanh`, `cong_bo_LS_cho_vay`); 2 = có `muc_tieu_dinh_luong` cho LS cho vay. Biến riêng cho `thay_doi_LS_dieu_hanh`. Văn bản sau ngày 15 của tháng cuối quý tính sang quý sau; chạy thêm bản không dời.
3. Biên thực m_{i,t} = loan_rate_pct − (deposit_rate_pct + 0.15)_{t−1}. Hồi quy m và Δr^L lên I_q, I_{q−1}, FE ngân hàng, kiểm soát ON_{t−1}; không FE quý. Biến thể: phần dư PT1 (d1) của GĐ7 hồi quy lên I_q.
4. CR1 theo ngân hàng + wild-cluster bootstrap Webb (B=9999, seed cố định) cho hệ số I_q chính. Ghi rõ: ~14 quý; I_q gần như luôn ≥ 1 nên nhận diện chủ yếu từ 1 vs 2; chỉ đạo có thể nội sinh → tương quan, không nhân quả.
5. Kết luận: có đủ căn cứ nhận diện `policy_pressure`/`policy_step` từ dữ liệu không. KHÔNG đề xuất giá trị.

## GD9a – Đưa hằng số cứng còn lại ra YAML (thay đổi hành vi = 0)
Tiên quyết: không. **Được trưởng nhóm duyệt sẵn việc chạm `src/agents/`** chỉ để đọc tham số, không đổi công thức.
- Đưa ra YAML (giá trị mặc định = giá trị hiện tại, có comment, đơn vị, cập nhật README): ngưỡng LDR 0.82 và biên chặn ±0.5 của demand_pressure (`bank.py`); `base_growth` 0.004 và `max_growth` 0.04 (`depositors.py`); biên chặn −0.04 / 0.035 (`borrowers.py`); kiểm tra lại mọi hằng số hành vi còn trong `src/agents/` và `src/core/`.
- Test: golden `term` và `golden_total` qua **bitwise**; test mới đối chiếu mặc định code = YAML.

## GD9 – Hiệu chỉnh bằng mô phỏng và kiểm định ngoài mẫu lịch sử
Tiên quyết: GD7c, GD9a. Kết quả: `reports/calibration/stage9/`, `configs/scenarios_calibrated.yaml`.
Cấu hình nền: `configs/scenarios_macro.yaml`, dữ liệu 8 NH, khởi tạo 2023Q1. Cửa sổ hiệu chỉnh: **2023Q2–2025Q2**; kiểm định ngoài mẫu: **2025Q3–2026Q3** (không dùng để chọn tham số).
Bước 1 – Tăng trưởng (quy tắc đặt trước, không tối ưu):
- `base_growth` tiền gửi và dư nợ = trung bình tăng trưởng quý của dữ liệu trong cửa sổ hiệu chỉnh (gộp 8 NH, cùng trọng số với cách mô hình tổng hợp). Ngưỡng chặn = phân vị 2.5% và 97.5% của tăng trưởng dữ liệu trong cửa sổ. Báo các quan sát bất thường đã biết (HDBank 2023Q2, MB Bank các Q4) và chạy thêm bản loại chúng.
Bước 2 – Lưới tham số lãi suất (kịch bản A; nếu A dùng RNG thì trung bình 10 seed):
- `pass_through` λ ∈ {0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45}.
- Biên tổng (target_margin + loan_spread_add) ∈ {3.8, 4.0, 4.2, 4.4, 4.6, 4.8}, điều chỉnh qua `target_margin`, giữ `loan_spread_add` = 1.35 (D7/Q1).
- `base_deposit_rate_step` ∈ {0, 0.006, 0.012, 0.018}; `deposit_competition` ∈ {0.07, 0.3, 0.7, 1.2}; ngưỡng LDR ∈ {0.82, giá trị bình quân LDR dữ liệu trong cửa sổ}.
- Hàm mục tiêu: RMSE thô LS cho vay (bình quân hệ thống, cùng trọng số với chuỗi thực) + RMSE thô LS huy động (cơ sở dữ liệu: deposit_rate×(1−casa)), trọng số bằng nhau, trên cửa sổ hiệu chỉnh. Ghi hàm mục tiêu trước khi chạy lưới.
- Báo: top 10 bộ tham số; hồ sơ hàm mục tiêu theo từng tham số (tham số nào "phẳng" = không nhận diện); tương quan giữa tham số trong top 50; λ chọn được có nằm trong CI GĐ7 không.
Bước 3 – Ngoài mẫu (2025Q3–2026Q3): RMSE thô, RMSE khử mức, biên độ/đáy V của bộ tốt nhất so với (i) cấu hình GĐ8 chưa hiệu chỉnh, (ii) mốc ngây thơ "giữ giá trị 2025Q2", (iii) mốc ngây thơ dùng ON: r_t = r_{2025Q2} + 0.45·(ON_{t−1} − ON_{2025Q1}). Ghi rõ mô hình được cấp ON thực ngoài mẫu (lợi thế thông tin).
Bước 4 – Ghi `configs/scenarios_calibrated.yaml` (bộ tốt nhất; comment nguồn từng giá trị). Mục 6 CLAUDE.md với A/B/C 10 lần chạy. Nếu bộ tốt nhất vi phạm mục 6 → DỪNG.
KHÔNG hiệu chỉnh σ, ε (không nhận diện, GĐ7) – giữ giá trị hiện tại, ghi là giả định; policy_pressure/policy_step theo D6.

## GD10 – Chạy lại A/B/C, độ nhạy, độ vững
Tiên quyết: GD9. Kết quả: `reports/stage10/`.
1. A/B/C 60 lần với `scenarios_calibrated.yaml`: LS cho vay/huy động theo quý (TB, P5–P95), B−A, C−A cuối kỳ và TB sau chính sách, tuân thủ. So với cấu hình gốc (`scenarios.yaml`) và cấu hình GĐ8.
2. Độ nhạy (mỗi lần đổi 1 tham số, 30 lần chạy): policy_pressure ±30%; policy_step ∈ {0.14, 0.28, 0.42, 0.50} (0.375–0.50 ≈ giảm 1.5–2 điểm %/năm trải trong 4 quý theo CV 9608 – ghi rõ đây là ánh xạ giả định); λ ở hai đầu CI GĐ7; macro_dep_spread = 1.08; σ, ε ±50%.
3. Độ vững học thích nghi: `learning_rule: relative` (θ=0.005, bước 0.05, simple) trên cấu hình hiệu chỉnh; so B−A, C−A với khi TẮT.
4. Bảng tóm tắt: kết luận chính sách nào giữ được dấu và độ lớn qua mọi biến thể.
5. Tách hiệu ứng tuân thủ: báo tuân thủ theo biến thể và nêu nhiễu lẫn với mức `nim_proxy`.

## GD11 – Khung kiểm định ngoài mẫu sau chính sách (Q4/2026 trở đi)
Tiên quyết: GD9. Kết quả: `src/analysis/kiem_dinh_ngoai_mau.py`, `reports/stage11/`.
1. Script đọc panel mở rộng (khi Minh bổ sung 2026Q4, 2027Q1 theo đúng định dạng panel hiện tại; viết đặc tả định dạng vào `docs/ke_hoach/yeu_cau_du_lieu_Minh.md`) và so dự báo A/B/C (cấu hình hiệu chỉnh) với thực tế: sai số từng kịch bản, kịch bản nào gần thực tế nhất, kiểm tra hướng (C−A dự báo so với thay đổi thực).
2. Chạy thử với dữ liệu giả lập ĐƯỢC ĐÁNH DẤU RÕ là giả lập trong test (không ghi vào data/), để chứng minh script chạy. Không tạo kết quả "thực" khi chưa có dữ liệu.
3. Thử tải ON thực Q4/2026 bằng `src/data/fetch_sbv_interbank.py` (có thể bị chặn 403 – nếu vậy ghi lại, không coi là lỗi). Nếu có, lưu riêng `data/raw/sbv_lnh_qua_dem_ngoai_mau.csv`, KHÔNG đổi file ON dùng cho kịch bản (D3).
4. Ghi rõ cách đọc: thực tế Q4/2026 có chỉ đạo (CV 9608/9736) nên tương ứng nhánh B/C; A là phản thực tế.

## GD12 – Hoàn thiện báo cáo nghiên cứu `report/bao_cao.md`
Tiên quyết: GD10, GD11.
1. Viết mục 1–5 còn thiếu: (1) Giới thiệu và câu hỏi nghiên cứu; (2) Tổng quan tài liệu (ABM trong kinh tế/ngân hàng; truyền dẫn lãi suất ở Việt Nam); (3) Dữ liệu (panel, định nghĩa lợi suất sổ sách và ánh xạ CASA, dữ liệu ON từ API NHNN, danh mục chỉ đạo); (4) Mô hình (tác nhân, phương trình, trình tự, kịch bản, tùy chọn macro và học thích nghi); (5) Ước lượng và hiệu chỉnh (GĐ7, 7b, 7c, 9 – phương pháp, kết quả, hạn chế).
2. Cập nhật mục 6–8 theo kết quả GD9–GD11 (bỏ các câu đã lỗi thời, vd. "tham số chưa hiệu chỉnh"); thêm phần độ vững (học thích nghi, độ nhạy) và bối cảnh chỉ đạo thực tế 10/2026.
3. Trích dẫn: chỉ dùng nguồn đã kiểm chứng được bằng WebSearch/WebFetch; nguồn chưa xác minh ghi `[CẦN XÁC MINH]`, tuyệt đối không bịa thông tin xuất bản. Bao gồm: bài SFI "Agent-Based Modeling: Worlds Within Worlds"; Santa Fe Artificial Stock Market (Arthur, Holland, LeBaron, Palmer); các văn bản NHNN trong danh mục chỉ đạo; NHNN là nguồn dữ liệu ON.
4. Mọi con số trong báo cáo phải truy được tới file kết quả (ghi đường dẫn trong comment HTML hoặc chú thích).
Reviewer kiểm tra: số liệu khớp, không diễn giải A/B/C là tác động thực, nêu đủ hạn chế.

## GD13 – Tổng hợp cho trưởng nhóm
Tiên quyết: tất cả. Viết `reports/giai_doan/TONG_HOP.md`: tóm tắt 1 trang toàn dự án; bảng giai đoạn; **mọi quyết định đang mở** với phương án mặc định đã dùng và hệ quả nếu đổi; việc cần làm khi có dữ liệu Q4/2026; đề xuất PR (nhánh nào, gộp theo thứ tự nào); danh sách câu hỏi cho Minh. Không cần reviewer.
