# Tổng hợp điều phối – lượt chạy ngày 21/11/2026

Nhánh `hieu-chinh-tham-so`, push lên remote `fork`. Bản tổng hợp tạm thời: GD10, GD12, GD13 chưa chạy vì chờ Huy quyết Q6/Q7.

## Bảng giai đoạn
| Giai đoạn | Trạng thái | Commit | Kết quả | Báo cáo |
|---|---|---|---|---|
| GD7c | XONG | ff20d53 | Không có bằng chứng chỉ đạo làm hẹp biên cho vay; giữ D6 (làm trước khi cài điều phối) | `reports/calibration/estimates_stage7c.md` |
| GD9a | XONG_CHO_DUYET | 9e806f4 | 13 hằng số hành vi ra YAML; hành vi không đổi (golden bitwise, 162 tổ hợp trùng HEAD); reviewer ĐẠT vòng 1 | [GD9a.md](GD9a.md) |
| GD9 | XONG_CHO_DUYET | 464c86d | Lưới 1536 bộ trên 2023Q2–2025Q2 → `configs/scenarios_calibrated.yaml`. Bộ tốt nhất λ 0.45, biên tổng 3.8, nằm ở biên lưới, λ ngoài CI GĐ7. Ngoài mẫu: RMSE thô LS cho vay 0.477 (GĐ8: 1.093), nhưng RMSE khử mức không tốt hơn (0.461 so với 0.457), mốc ON thắng ở LS huy động, mô hình chỉ tái tạo ~30% biên độ. Reviewer ĐẠT CÓ ĐIỀU KIỆN (2 vòng) | [GD9.md](GD9.md) |
| GD10 | BI_CHAN | – | Chờ Q6/Q7 | – |
| GD11 | XONG_CHO_DUYET | f8658cc | Script `src/analysis/kiem_dinh_ngoai_mau.py` chạy được trên dữ liệu giả lập (có nhãn); chưa có kết quả ngoài mẫu thực vì panel dừng ở 2026Q3. Đã tải ON thực Q4/2026 đến 19/11 (bình quân giản đơn 4.074, cao hơn giả định 3.946). Reviewer ĐẠT CÓ ĐIỀU KIỆN (2 vòng) | [GD11.md](GD11.md) |
| GD12 | BI_CHAN | – | Phụ thuộc GD10 | – |
| GD13 | BI_CHAN | – | Phụ thuộc GD10, GD12 | – |

Kiểm tra cuối lượt: `pytest` 197 passed, 1 xfailed; validation 7/7 ĐẠT; golden term và golden_total khớp bitwise.

## Quyết định đang mở (chờ Huy)

**Q6 – Nghiệm lưới ở biên, λ ngoài CI (chặn GD10, GD12, GD13).**
- Câu hỏi: giữ nghiệm của lưới đã duyệt (λ 0.45, biên tổng 3.8), hay ràng buộc λ trong CI GĐ7, hay mở rộng lưới?
- Đã áp dụng: giữ nghiệm của lưới đã duyệt.
- Nếu Huy chọn khác: λ = 0.35 trong CI có J 0.4994 (so với 0.4548). Lưới mở rộng cho nghiệm lại nằm ở biên (λ 0.25, biên tổng 3.0) và ngoài mẫu xấu hơn (RMSE thô 0.896), dấu hiệu quá khớp. Biên thấp chủ yếu bù LS huy động của mô hình cao hơn thực khoảng +0.33 trong mẫu.
- Ảnh hưởng: GD10 (mức và độ lớn B−A, C−A), GD12.

**Q7 – Quy tắc tăng trưởng nền không tái tạo tăng trưởng tổng (chặn GD10, GD12, GD13).**
- Câu hỏi: giữ quy tắc đã duyệt hay bù độ lệch?
- Đã áp dụng: giữ quy tắc đã duyệt.
- Hệ quả: tăng trưởng tiền gửi mô hình 0.030 so với 0.040, dư nợ 0.060 so với 0.045 mỗi quý. Trần LDR 1.60 bị chạm dần (kịch bản A: 0% đến Q10, 12.5% từ month 11, 37.5% từ month 16; B/C sau chính sách 34% ngân hàng-quý). Khởi đầu từ 2026Q3 thì 87.5% ngân hàng chạm trần, nên cấu hình hiệu chỉnh không dùng được cho chạy từ 2026Q3.
- Nếu Huy chọn bù độ lệch: chẩn đoán cho J 0.4407 và hết chạm trần LDR, nhưng phải chạy lại lưới GD9.
- Nhiễu lẫn tuân thủ (cần biết khi đọc B−A, C−A): xác suất tuân thủ TB của B giảm 0.943 → 0.877, C−B thu hẹp từ −0.024 xuống −0.013; mức A sau chính sách giảm 0.85 điểm so với bản macro, nên phần lớn thay đổi là hiệu ứng mức.

**Q4b – Dạng chặn tăng trưởng tiền gửi.** Đã áp dụng: bất đối xứng qua khóa tùy chọn `depositor_min_growth` (null = hành vi cũ); LO_TRINH GD9 không ghi rõ việc chạm `src/agents/depositors.py`, cần Huy xác nhận. Nếu chọn đối xứng ±0.1732: cùng bộ tham số, J lệch 0.0002. Ảnh hưởng: GD10 (chỉ hình thức).

**Q8 – Ngưỡng kinh tế coi hướng hiệu ứng là "đủ lớn" (GD11).** Đã áp dụng: không có ngưỡng, chỉ báo tín hiệu/nhiễu. Ảnh hưởng: GD12.

**Q3 – CLAUDE.md mục 4.2 lỗi thời** (danh sách hằng số cứng; câu "model.py 1.15/12 khác YAML"). Đã áp dụng: không sửa CLAUDE.md. Không ảnh hưởng giai đoạn nào.

**Q4 / Q5 (GD9a).** Q4: chặn demand_pressure và tăng trưởng tiền gửi dùng 1 khóa đối xứng (đã áp dụng; Q4b là phần tiếp). Q5: miền hợp lệ 0–20/0–14 và sàn 0.01 giữ cứng, trùng assert mục 6. Không ảnh hưởng kết quả.

**Q1 / Q2 (từ trước).** Q1: `loan_spread_add = 1.35` giữ nguyên, biên tổng hiệu chỉnh qua `target_margin`. Q2: r^L coi là LS bình quân danh mục. Ảnh hưởng GD9, GD12.

## Việc cần làm khi có dữ liệu Q4/2026
- Minh bổ sung 2026Q4, 2027Q1 vào panel theo `docs/ke_hoach/yeu_cau_du_lieu_Minh.md` (bỏ cả quý nếu thiếu một ngân hàng, không để ô trống; số cũ giữ nguyên, script kiểm tra bằng `--panel-cu`).
- Tải lại ON sau 31/12/2026 (hiện chỉ đến 19/11); chênh 4.074 so với giả định 3.946 mới được ghi nhận, chưa đánh giá.
- Chạy `python -m src.analysis.kiem_dinh_ngoai_mau`. Thực tế Q4/2026 có chỉ đạo (CV 9608, 9736) nên tương ứng nhánh B/C, A là phản thực tế; không diễn giải là tác động chính sách. Ở 1–2 quý, B và C gần như không phân biệt được về LS cho vay.

## Đề xuất tiếp theo
1. Huy quyết Q6, Q7 (và xác nhận Q4b).
2. Nếu đổi Q7 hoặc Q6: chạy lại lưới GD9, rồi `/dieu-phoi tu GD10`. Nếu giữ mặc định: chạy `/dieu-phoi tu GD10` ngay (GD11 chỉ cần chạy lại script nếu YAML đổi).
3. PR: nhánh `hieu-chinh-tham-so` → `main` (chưa tạo), gộp theo thứ tự GD7c → GD9a → GD9 → GD11, sau khi GD10–GD13 xong.

## Câu hỏi cho Minh
- Có bổ sung được panel 2026Q4, 2027Q1 đủ 8 ngân hàng, đúng định dạng và số cũ không đổi không? Khi nào có?
- Danh mục chỉ đạo lãi suất (`chi_dao_lai_suat_2023_2026.csv`, 24 văn bản) đã đầy đủ chưa?
