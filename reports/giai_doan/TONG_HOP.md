# Tổng hợp cho trưởng nhóm – GD7c đến GD13

**Ngày:** 2026-11-21 · **Nhánh:** `hieu-chinh-tham-so` (push lên remote `fork`; chưa push `origin`, chưa tạo PR) · **Người duyệt sau cùng:** Huy

Thay cho bản tổng hợp tạm thời trước đó (khi GD10, GD12, GD13 còn bị chặn bởi Q6/Q7). Mọi số dưới đây lấy từ các CSV trong `reports/`; tên file ghi trong báo cáo từng giai đoạn.

## 1. Tóm tắt toàn dự án (1 trang)

**Làm gì.** ABM 8 ngân hàng Việt Nam (Mesa 3.3.1), 1 bước = 1 quý, chính sách kích hoạt từ Q4/2026, ba kịch bản A (không can thiệp), B (chỉ đạo giảm lãi suất cho vay), C (B + hạn chế cạnh tranh huy động). Lượt công việc này đưa mô hình từ "tham số giả định" sang "hiệu chỉnh theo quy tắc đăng ký trước, kèm độ nhạy và báo cáo nghiên cứu".

**Đã có.**
- Ước lượng một bước (GĐ7, 7b, 7c): λ (truyền dẫn cho vay) 0.27–0.31, CI bootstrap [0.158; 0.395]; φ (huy động neo ON) 0.177; không có bằng chứng chỉ đạo làm hẹp biên cho vay → `policy_pressure`, `policy_step` giữ là giả định kịch bản.
- 13 hằng số hành vi đã ra YAML, hành vi không đổi (golden bitwise) – GD9a.
- Hiệu chỉnh bằng mô phỏng (GD9, GD9b) và cấu hình chính **GD9b**: λ 0.40, biên tổng 3.4, bù tăng trưởng Q7. Đây là **nghiệm biên** (λ chạm cận trên lưới, biên tổng chạm cận dưới; J đơn điệu theo cả hai).
- Trong mẫu 2023Q2–2025Q2: RMSE thô LS cho vay 0.3164, LS huy động 0.4303. Ngoài mẫu lịch sử 2025Q3–2026Q3 (mô hình được cấp ON thực, không phải dự báo): LS cho vay 0.5921, **kém GD9** (0.4767) vì mô hình hạ thấp mức (sai số TB −0.338).
- Kịch bản (60 lần, TB quý 15–18, `policy_step` = 0.28): B−A −0.3933, C−A −0.3947, C−B −0.0014. Theo dải `policy_step` 0.14–0.50: B−A TB từ −0.20 đến −0.70, cuối kỳ từ −0.26 đến −0.89 (≈ −1.4 × step và ≈ −1.8 × step). Dấu âm của B−A, C−A giữ ở 20/20 biến thể; **độ lớn tỷ lệ với giả định step**; **B và C không phân biệt được** (|C−B| ≤ 1.44% |B−A| ở 4 giá trị `deposit_competition`).
- Khung kiểm định ngoài mẫu Q4/2026 (GD11) và báo cáo nghiên cứu `report/bao_cao.md` (GD12) đã xong; hộp "Những điều không được diễn giải" nằm đầu báo cáo.

**Chưa có / hạn chế chính.**
- Chưa có kết quả ngoài mẫu sau chính sách: panel dừng ở 2026Q3.
- Sai lệch mức LS huy động trong mẫu GD9b là +0.312 điểm % (`mean_error_insample_stage9b.csv`; Q14); biên tổng hiệu chỉnh 3.4–3.8 thấp hơn biên quan sát 4.59 (định nghĩa chưa xác nhận – xem mục 6).
- 0% chạm trần LDR ở GD9b là hệ quả bù Q7 (bỏ bù: 18.1%), không phải bằng chứng cơ chế.
- A/B/C là kết quả của mô hình, **không phải tác động chính sách thực**; không so sánh trực tiếp B−A với mức giảm 1.5–2%/năm trong CV 9608 (D11).
- Một số trích dẫn trong báo cáo còn `[CẦN XÁC MINH]`.

## 2. Bảng giai đoạn

| Giai đoạn | Trạng thái | Commit | Kết quả | Báo cáo |
|---|---|---|---|---|
| GD7c | XONG | ff20d53 | Không có bằng chứng chỉ đạo làm hẹp biên cho vay; giữ D6 | `reports/calibration/estimates_stage7c.md` |
| GD9a | XONG_CHO_DUYET | 9e806f4 | 13 hằng số ra YAML, hành vi không đổi; reviewer ĐẠT | [GD9a.md](GD9a.md) |
| GD9 | XONG_CHO_DUYET | 464c86d | λ 0.45, biên tổng 3.8 (biên lưới, λ ngoài CI); giữ làm bản đối chiếu (`scenarios_calibrated_gd9.yaml`) | [GD9.md](GD9.md) |
| GD9b | XONG_CHO_DUYET | 0b8ec53 | Cấu hình chính: λ 0.40, biên tổng 3.4, bù Q7; nghiệm biên; ngoài mẫu LS cho vay kém GD9 | [GD9b.md](GD9b.md) |
| GD10 | XONG_CHO_DUYET | 05712bb | A/B/C 60 lần, độ nhạy, độ vững; B−A, C−A < 0 ở 20/20; B và C không phân biệt được | [GD10.md](GD10.md) |
| GD10b | XONG | ab6d156 | Độ nhạy `deposit_competition` {0.07, 0.3, 0.7, 1.2} và `policy_step` 0.375; sai lệch mức trong mẫu (Q14) | [GD10b.md](GD10b.md) |
| GD11 | XONG_CHO_DUYET | f8658cc | Khung kiểm định ngoài mẫu; chờ panel Q4/2026; đã tải ON Q4/2026 đến 19/11 (bình quân 4.074 so với 3.946 giả định) | [GD11.md](GD11.md) |
| GD12 | XONG_CHO_DUYET | 01f250c, 4914bf5 | `report/bao_cao.md`; reviewer ĐẠT sau 2 vòng; áp dụng D11 | [GD12.md](GD12.md) |
| GD13 | XONG_CHO_DUYET | 671054d | CLAUDE.md mục 4.2 cập nhật; tổng hợp này; hai sửa lời văn báo cáo theo yêu cầu của Huy (xem mục 7) | – |

Kiểm tra cuối GD13: `pytest -q` 216 passed, 1 xfailed; validation 7/7 ĐẠT; `configs/scenarios.yaml` và `configs/scenarios_calibrated.yaml` không đổi (md5 `36daf800…`, `5292f5b2…`). GD13 không chạm `src/`, `configs/`, `data/`, `tests/`.

## 3. Quyết định đã đóng (để Huy rà lại)

**D9 (sau GD9):** Q3 cho phép sửa CLAUDE.md mục 4.2 (đã làm ở GD13); Q4b giữ `depositor_min_growth` (chặn bất đối xứng); Q6 lưới ràng buộc λ ∈ {0.15…0.40}, biên tổng {3.4…4.8}, nghiệm chạm cận thì giữ, không mở rộng; Q7 bù tăng trưởng một lần vào `base_growth`; Q8 không đặt ngưỡng kinh tế, chỉ báo tín hiệu/nhiễu.

**D10 (sau GD10):**
- Q9: GD9b là cấu hình chính, ghi rõ "nghiệm biên"; không mở rộng lưới; λ = 0.35 và GD9 vào bảng đối chiếu.
- Q10: không đổi `deposit_competition` và ngưỡng LDR trong YAML chính; thêm GD10b, báo cả 4 giá trị, không chọn.
- Q11: không chọn cấu hình theo kết quả ngoài mẫu; chạy song song GD9 trong GD12.
- Q12: giữ YAML; báo cả hai bản học thích nghi (YAML và dời cửa sổ −1.15).
- Q13: giữ ngưỡng đã đặt trước; B−A báo theo dải `policy_step`, không nêu một số.
- **Q14:** sai lệch mức LS huy động là hạn chế của mô hình; xuất sai lệch mức trong mẫu GD9b ra CSV trước GD12 (đã làm; GD9b: LS huy động +0.312, LS cho vay −0.026; GD9: +0.326 và +0.259).

**D11 (sau GD12):**
- D11-a: ý (ii) của hộp "Những điều không được diễn giải" = không so sánh trực tiếp B−A với mức giảm 1.5–2%/năm của CV 9608 (chỉ đạo nhắm SXKD/ưu tiên, `policy_step` trừ vào toàn bộ lãi suất cho vay); step 0.14–0.50 cho B−A cuối kỳ −0.26 đến −0.89 điểm %.
- D11-b: ánh xạ step 0.375–0.50 ≈ 1.5–2 điểm %/năm chỉ giữ một câu ở mục 4.4 của báo cáo (giả định, khác phạm vi); xóa khỏi phần kết quả và kết luận.

D11 hiện chỉ ghi ở `docs/ke_hoach/TRANG_THAI.md` và `GD12.md`; **chưa có trong `LO_TRINH.md`**. Nếu muốn nhất quán với D9, D10, nên bổ sung một mục D11 vào LO_TRINH.md (chỉ tài liệu).

## 4. Quyết định đang mở (mặc định đã dùng, hệ quả nếu đổi)

| # | Câu hỏi | Mặc định đã dùng | Hệ quả nếu Huy chọn khác |
|---|---|---|---|
| Q1 | Nguồn gốc `loan_spread_add = 1.35` | Giữ 1.35; biên tổng hiệu chỉnh qua `target_margin` | Mục tiêu cho vay chỉ phụ thuộc tổng `target_margin + loan_spread_add` (`bank.py`), nên đổi 1.35 mà giữ biên tổng thì kết quả không đổi; chỉ đổi cách đọc `target_margin` (hiện 2.05 = 3.4 − 1.35) và `margin_min`/`margin_max` của học thích nghi |
| Q2 | r^L trong mô hình là LS chào khoản vay mới hay LS bình quân danh mục | Coi là LS bình quân danh mục (vì đối chiếu với lợi suất sổ sách) | Nếu là LS chào mới: không đối chiếu được với `loan_rate_pct` sổ sách; cần dữ liệu lãi suất khoản vay mới, hiệu chỉnh lại (λ, biên) và viết lại phần dữ liệu, 6.1 của báo cáo |
| Q4 | Chặn `demand_pressure` ±0.5 và tăng trưởng tiền gửi: 1 khóa đối xứng hay 2 khóa sàn/trần | 1 khóa đối xứng cho `demand_pressure_cap`; tăng trưởng tiền gửi đã tách sàn/trần theo Q4b | Tách `demand_pressure` thành sàn/trần: thêm khóa mới (mặc định tắt) và chạm `src/agents/bank.py`; ở GD9b áp lực huy động chạm chặn ±0.5 ở 0% ngân hàng-quý (GD9b.md mục 3.5) nên ít khả năng đổi kết quả, chưa kiểm |
| Q5 | Đưa miền hợp lệ 0–20/0–14 và sàn 0.01 ra YAML? | Giữ cứng (trùng assert mục 6 CLAUDE.md) | Không ảnh hưởng kết quả; chỉ thêm khóa và test |

Hai điểm ở GD12.md mục 6 (hộp ý (ii), ánh xạ step) đã đóng bằng D11, không còn mở.

## 5. Việc cần làm khi có dữ liệu Q4/2026

1. **Minh** bổ sung 2026Q4 (và 2027Q1 nếu có) vào panel theo `docs/ke_hoach/yeu_cau_du_lieu_Minh.md`: đủ 8 ngân hàng, bỏ cả quý nếu thiếu một ngân hàng, số cũ giữ nguyên (script kiểm bằng `--panel-cu`), cùng định nghĩa quy năm của lợi suất sổ sách.
2. Tải lại ON sau 31/12/2026 (hiện chỉ đến 19/11; quý chưa kết thúc) rồi ghi đè `data/raw/sbv_lnh_qua_dem_ngoai_mau.csv`. Chênh 4.074 so với giả định 3.946 mới chỉ được ghi nhận, chưa đánh giá.
3. Chạy `python -m src.analysis.kiem_dinh_ngoai_mau --config configs/scenarios_calibrated.yaml`. Thực tế Q4/2026 có chỉ đạo nên tương ứng nhánh B/C; A là phản thực tế. Ở 1–2 quý, đây chỉ là đối chiếu mô tả, không phải tác động chính sách; B và C gần như không phân biệt được.
4. Cập nhật mục 6.3 của `report/bao_cao.md` và các câu "chưa có kết quả ngoài mẫu sau chính sách"; xác minh các mục `[CẦN XÁC MINH]` trước khi nộp.

## 6. Đề xuất PR

- **Nhánh nguồn → đích:** `hieu-chinh-tham-so` → `main` của `origin` (hiện `main` ở `312bdd4`, nhánh nguồn hơn 44 commit, 208 file; phần lớn là kết quả CSV/báo cáo dưới `reports/`, `data/raw`, `tests/golden*`).
- **Gộp:** một PR duy nhất, vì nhánh là chuỗi tuyến tính và các giai đoạn sau phụ thuộc trước; tách PR đòi hỏi rebase. Nên đọc theo thứ tự commit: GĐ5–8 (tùy chọn mặc định TẮT, `macro_driver`) → GD7c (ff20d53) → GD9a (9e806f4) → GD9 (464c86d) → GD9b (0b8ec53) → GD10 (05712bb) → GD10b (ab6d156) → GD11 (f8658cc) → GD12 (01f250c, 4914bf5) → GD13. Điểm kiểm trước khi merge: pytest 216 passed; golden `term` và `golden_total` khớp bitwise; `configs/scenarios.yaml` không đổi giá trị hành vi.
- Chưa tạo PR và chưa push `origin`: Huy quyết định thời điểm và người tạo.

## 7. Câu hỏi cho Minh

1. **Biên 4.59 (GĐ7, PT2, μ_margin = 4.588, CI [3.43; 5.74]) có cùng định nghĩa với biên của mô hình không?** Biên mô hình là `loan_rate` − chi phí vốn trễ (3.696 ở GD9b, 3.999 ở GD9) và, nếu tính theo `loan_rate` − `deposit_rate`, là 2.806 (GD9b), 3.095 (GD9) (`reports/calibration/stage9b/diag_gd9b.csv`, phần `bien`). Biên mục tiêu hiệu chỉnh là 3.4 (GD9b) hoặc 3.8 (GD9). Câu trả lời quyết định hạn chế (b) của báo cáo có phải chênh lệch thật hay chênh lệch định nghĩa.
2. **Ngày và thứ tự CV 9608–9736** trong `data/raw/chi_dao_lai_suat_2023_2026.csv`: dòng ngày `2026-10-18` ghi "CV 9608 (sau họp Thống đốc 19/10)", mâu thuẫn với ngày văn bản; theo báo chí, CV 9736 (21/10) mới quán triệt theo cuộc họp 19/10 và CV 9608 (18/10). Đề nghị xác minh ngày ban hành CV 9608 và sửa mô tả (tạo file mới hoặc ghi rõ cách sửa; không sửa trực tiếp dữ liệu gốc). Báo cáo đang gắn `[CẦN XÁC MINH]` cho ngày 18/10/2026.
3. **Phạm vi mức giảm 1.5–2%/năm của CV 9608:** cột `tom_tat` đã ghi "SXKD và lĩnh vực ưu tiên"; đề nghị bổ sung phạm vi cho cột `muc_tieu_dinh_luong` khi đối chiếu toàn văn.
4. Panel 2026Q4, 2027Q1: có bổ sung được đủ 8 ngân hàng, đúng định dạng, số cũ không đổi không? Khi nào có?
5. Danh mục chỉ đạo (24 văn bản) đã đầy đủ chưa? Các văn bản ngoài CV 9608/9736 chưa được kiểm lại nguồn trong GD12.
6. Xác minh nguồn còn `[CẦN XÁC MINH]` trong báo cáo: tài liệu ABM trong ngân hàng, tài liệu truyền dẫn lãi suất ở Việt Nam, nơi in 1997 của bài Santa Fe, bài SFI "Worlds Within Worlds", toàn văn CV 9608.

## 8. Thay đổi ở GD13

- `CLAUDE.md` mục 4.2 (Q3, được phép): bỏ câu "mặc định trong `model.py` (1.15, 12) khác YAML" (đã lỗi thời: nay là 1.60 và 14, trùng YAML); trỏ tới `tests/test_constants_yaml.py`; cập nhật danh sách hằng số (nay ở YAML, còn cứng: miền hợp lệ và sàn 0.01 – Q5); ghi cấu hình chuẩn hiện hành.
- `report/bao_cao.md` (chỉ lời văn, theo yêu cầu của Huy): (1) mục 6.2, sau ý (i) của "Tóm lại các kết luận vững", thêm câu rằng dấu âm phần lớn do cấu trúc (chính sách chỉ trừ `policy_step` khỏi lãi suất cho vay) và các phản hồi qua huy động và tăng trưởng không đảo được dấu này; (2) mục 2.1, bỏ câu khẳng định không nguồn về ABM trong ngân hàng, giữ `[CẦN XÁC MINH: tài liệu ABM trong ngân hàng]`.
- Không cần reviewer (theo LO_TRINH GD13; thay đổi chỉ là tài liệu).
