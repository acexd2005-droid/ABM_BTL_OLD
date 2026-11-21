# Golden files (cơ sở `term`, mặc định từ Bước A)

Kết quả `history` và `bank_history` của kịch bản A/B/C với seed 202611, 202612, 202613, tham số từ
`configs/scenarios.yaml` (`deposit_rate_basis: term`, `learning_nim_threshold: 4.6331`), dữ liệu
`data/clean/abm_initial_8nganhang_2023Q1.csv`. Gồm mọi cột hiện có, kể cả `target_margin`.

- **Tạo bằng:** code tại commit `a3da8fa` cộng thay đổi của chính commit Bước A (đổi mặc định sang `term`); commit Bước A = `6a5f219`.
- **Lý do tạo lại:** trưởng nhóm duyệt rõ ràng (Bước A) đổi mặc định `deposit_rate_basis` từ `total` sang `term` để sửa lỗi CASA bị trừ hai lần trong `funding_cost`.
  Cơ sở `total` khớp lãi suất cho vay thực tốt hơn (RMSE 1.18 so với 1.97) chỉ vì hai lỗi bù nhau; giữ lại là chỉnh cho đẹp. Báo cáo: `reports/stage8a/summary_stage8a.md`.
- **Không chỉ là hiệu ứng mức:** phép chia `1 − casa` khác nhau theo ngân hàng (hệ số từ khoảng 1.08 đến 1.49) nên thứ hạng lãi suất huy động tương đối giữa các ngân hàng thay đổi, và khối người gửi phản ứng với lãi suất tương đối. Vì vậy tiền gửi/dư nợ từng ngân hàng lệch đáng kể so với golden cũ (tiền gửi lệch tối đa 2.9% ở quý 1 và 58.5% ở quý 18; dư nợ lệch tối đa 18.7%, theo reviewer-abm). Không so trực tiếp thị phần/tiền gửi theo ngân hàng giữa `golden_total/` và `golden/`.
- **Golden cũ:** chuyển nguyên vẹn sang `tests/golden_total/` (tạo từ code gốc 0117fb6). `tests/test_golden.py::test_golden_total` vẫn chạy cơ sở `total` so với đó để đối chiếu lịch sử.
- Không tạo lại các file này để làm test qua. Chỉ tạo lại khi có quyết định đổi mô hình có chủ đích của nhóm.
