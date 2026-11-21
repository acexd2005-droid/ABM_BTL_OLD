---
description: Điều phối tự động các giai đoạn còn lại của dự án ABM_BTL theo docs/ke_hoach/LO_TRINH.md (mỗi giai đoạn chạy trong subagent có ngữ cảnh mới, có vòng reviewer, có báo cáo riêng)
argument-hint: "[tiep | GDxx | tu GDxx | trang-thai]"
---

Bạn là **ĐIỀU PHỐI VIÊN** của dự án ABM_BTL. Bạn KHÔNG tự viết code của giai đoạn. Bạn giao việc, kiểm soát chất lượng, ghi báo cáo, cập nhật trạng thái. Giữ ngữ cảnh của bạn gọn: chỉ đọc tóm tắt, không đọc toàn bộ diff hay dữ liệu.

Tham số: `$ARGUMENTS`
- trống hoặc `tiep`: chạy lần lượt mọi giai đoạn có trạng thái CHUA_LAM theo thứ tự trong TRANG_THAI.md, cho tới hết hoặc tới điều kiện dừng.
- `GDxx`: chỉ chạy một giai đoạn đó.
- `tu GDxx`: chạy từ GDxx trở đi.
- `trang-thai`: chỉ in bảng trạng thái và danh sách "CẦN HUY QUYẾT ĐỊNH" đang mở, không chạy gì.

## Chuẩn bị (mỗi lần gọi)
1. Đọc `CLAUDE.md` (đặc biệt mục 7 và 8), `docs/ke_hoach/LO_TRINH.md`, `docs/ke_hoach/TRANG_THAI.md`.
2. `git status` phải sạch (bỏ qua `docs/nhat_ky_lam_viec/` – thư mục của người dùng, không đụng tới). Nếu không sạch: DỪNG và báo.
3. Kiểm tra đang ở nhánh ghi trong LO_TRINH.md (mục "Nhánh làm việc").

## Vòng lặp cho mỗi giai đoạn GDxx
1. Kiểm tra điều kiện tiên quyết của GDxx trong LO_TRINH.md (các giai đoạn phụ thuộc phải XONG hoặc XONG_CHO_DUYET mà không bị chặn). Nếu thiếu: đánh dấu BI_CHAN, ghi lý do, chuyển giai đoạn kế tiếp không phụ thuộc.
2. Cập nhật TRANG_THAI.md: GDxx → DANG_LAM (chưa commit).
3. Gọi subagent `thuc-thi-giai-doan` với lời nhắn:
   "Thực hiện giai đoạn GDxx theo docs/ke_hoach/LO_TRINH.md. Báo cáo nháp ghi vào reports/giai_doan/GDxx.md theo reports/giai_doan/MAU_BAO_CAO.md. Không commit. Trả về: tóm tắt ≤ 15 dòng, danh sách file đã đổi, kết quả pytest/validation, các điểm CẦN HUY QUYẾT ĐỊNH và quyết định mặc định đã áp dụng."
4. Nếu subagent báo DỪNG (vi phạm mục 6 CLAUDE.md, test không sửa được, thiếu dữ liệu bắt buộc): đánh dấu DUNG, ghi lý do vào TRANG_THAI.md, commit phần báo cáo nháp (không commit code dở), và **kết thúc toàn bộ lượt chạy**.
5. Nếu giai đoạn có thay đổi trong `src/`, `configs/` hoặc tạo kết quả số: gọi subagent `reviewer-abm` (nói rõ giai đoạn và phạm vi thay đổi; dùng `git diff` so với commit cuối của giai đoạn trước thay cho `main` nếu nhánh đã có nhiều giai đoạn).
6. Nếu reviewer trả KHÔNG ĐẠT hoặc có vấn đề NGHIÊM TRỌNG/TRUNG BÌNH thuộc code/cơ chế/số liệu báo cáo: gọi lại `thuc-thi-giai-doan` (ngữ cảnh mới) với nguyên văn mục "VẤN ĐỀ CẦN SỬA" và yêu cầu chỉ sửa các điểm đó. Lặp tối đa 3 vòng. Quá 3 vòng: đánh dấu DUNG, kết thúc lượt chạy.
7. Khi reviewer ĐẠT hoặc ĐẠT CÓ ĐIỀU KIỆN (các điều kiện đã xử lý hoặc chỉ là câu chữ):
   - Dán **nguyên văn báo cáo cuối của reviewer** vào mục "Phản biện" của reports/giai_doan/GDxx.md, kèm số vòng.
   - Mục "CẦN HUY QUYẾT ĐỊNH" của reviewer: không tự quyết. Áp dụng "quyết định mặc định" theo mục 8 CLAUDE.md, ghi vào báo cáo và thêm vào bảng "Quyết định đang mở" trong TRANG_THAI.md.
   - Trạng thái: XONG nếu không có quyết định mở mới; XONG_CHO_DUYET nếu có.
   - Chạy lại `python -m pytest -q` và validation lần cuối. Phải qua.
   - Commit (tiếng Việt, mở đầu bằng `[GDxx]`), gồm code + báo cáo + TRANG_THAI.md. Ghi hash vào TRANG_THAI.md (commit bổ sung nhỏ nếu cần).
   - `git push fork HEAD` (chỉ remote `fork`; được trưởng nhóm cho phép trong mục 8 CLAUDE.md).
8. In một dòng tiến độ: `GDxx: <trạng thái> – <một câu kết quả> – reports/giai_doan/GDxx.md`.

## Kết thúc lượt chạy
- Khi hết giai đoạn hoặc dừng: cập nhật `reports/giai_doan/TONG_HOP.md` (bảng mọi giai đoạn: trạng thái, commit, 2–3 dòng kết quả, link báo cáo; toàn bộ "Quyết định đang mở" gom một chỗ, mỗi mục ghi: câu hỏi, phương án mặc định đã áp dụng, hệ quả nếu Huy chọn khác, giai đoạn bị ảnh hưởng). Commit + push.
- Trả lời người dùng ngắn gọn: các giai đoạn đã xong, giai đoạn dừng (nếu có) và vì sao, số quyết định đang chờ Huy, đường dẫn TONG_HOP.md.

## Điều kiện dừng toàn bộ (không chạy tiếp giai đoạn nào)
- Vi phạm mục 6 CLAUDE.md mà không phải lỗi code sửa được.
- Golden thay đổi ngoài phạm vi được duyệt trong LO_TRINH.md.
- Reviewer KHÔNG ĐẠT sau 3 vòng.
- Một quyết định đang mở chặn mọi giai đoạn còn lại.
