# Nâng cấp: ngân hàng học thích nghi

> Trạng thái: **tùy chọn, mặc định TẮT** (`adaptive_learning: false`). Mọi tham số học là **giá trị khởi điểm, chưa hiệu chỉnh, chờ Huy duyệt**. Kết quả dưới đây là so sánh trong mẫu của mô hình minh họa, không phải ước lượng tác động chính sách thực tế.

## 1. Cơ chế

Trong mô hình gốc, biên `target_margin` $m_i=3.2$ là hằng số: lãi suất cho vay mục tiêu là $r^*_{i,t}=c_{i,t-1}+m_i+\delta$ với $c$ là chi phí vốn trễ và $\delta=$ `loan_spread_add`. Khi bật học, cuối mỗi quý (trong `Bank.finish_month`) ngân hàng $i$ chỉnh $m_i$ cho quý kế tiếp.

Ký hiệu: $s_{i,t}=L_{i,t}/\sum_j L_{j,t}$ là thị phần dư nợ, $g_{i,t}=L_{i,t}/L_{i,t-1}-1$ là tăng trưởng dư nợ quý, $\text{nim}_{i,t}$ là `nim_proxy` cuối quý.

$$
\Delta_{i,t}=
\begin{cases}
-d & \text{nếu } s_{i,t}<s_{i,t-1}\\[2pt]
+u & \text{nếu } s_{i,t}\ge s_{i,t-1}\ \wedge\ g_{i,t}\ge g^*\ \wedge\ \text{nim}_{i,t}\ge n^*\\[2pt]
0 & \text{còn lại}
\end{cases}
$$

$$
m_{i,t+1}=\min\!\big(m_{\max},\ \max(m_{\min},\ m_{i,t}+\Delta_{i,t})\big)
$$

Khi cả hai điều kiện cùng xảy ra thì chỉ giảm. Giá trị khởi điểm: $u=0.05$, $d=0.10$ (điểm %/quý), $g^*=0.006$ (bằng tăng trưởng cơ sở), $n^*=5.5875$ điểm %/năm, $[m_{\min},m_{\max}]=[2.2,4.2]$. $n^*$ là `nim_proxy` bình quân gia quyền theo dư nợ của 8 ngân hàng tại t=0, tính một lần từ `abm_initial_8nganhang_2023Q1.csv` và ghi cố định trong YAML. Cột `target_margin` mới ở cuối `bank_history` ghi biên đã cập nhật, áp dụng cho quý kế tiếp. Hàm học không dùng số ngẫu nhiên, nên không làm lệch chuỗi RNG.

## 2. Lý do kinh tế

- **Dùng thị phần dư nợ, không dùng thị phần tiền gửi.** `target_margin` chỉ tác động lên lãi suất cho vay và qua đó lên dư nợ; nó không tác động lên tiền gửi (lãi suất huy động và tiền gửi được xác định bởi kênh khác). Dùng thị phần tiền gửi làm tín hiệu sẽ gắn phần thưởng/phạt vào một biến mà quyết định được chỉnh không điều khiển được.
- Mất thị phần cho vay là dấu hiệu giá cho vay kém cạnh tranh, nên giảm biên (bước giảm lớn hơn bước tăng: phản ứng bất đối xứng, mất khách đau hơn).
- Chỉ nới biên khi cùng lúc tăng trưởng tốt và `nim_proxy` cao, tức ngân hàng có dư địa. Bước tăng nhỏ để hành vi thận trọng.
- Biên bị chặn để không trôi ra ngoài miền hợp lý.

## 3. Liên hệ với học thích nghi (Santa Fe Institute)

Cơ chế thuộc họ mô hình *tác nhân thích nghi bị giới hạn lý trí* của kinh tế học tính toán/phức hệ thích nghi (W. B. Arthur, J. Holland, J. Epstein–R. Axtell...): tác nhân không tối ưu hóa mà điều chỉnh quy tắc theo phản hồi từ kết quả gần nhất, và hành vi tổng thể nổi lên từ tương tác. Nó gần nhất với học tăng cường đơn giản/học theo kết quả (win-stay/lose-shift, mô hình Roth–Erev). Khác biệt: mô hình này chỉ có một tham số học trực tiếp, không có quần thể quy tắc cạnh tranh hay tiến hóa như hệ phân loại của Holland, nên là phiên bản rất sơ đẳng. *Đây là liên hệ khái niệm, chưa được kiểm chứng bằng đối chiếu tài liệu trong repo; nhóm cần tự xác nhận trích dẫn trước khi đưa vào báo cáo.*

## 4. Bảng so sánh (10 lần chạy, `--sensitivity-runs 2`, seed gốc 202611)

Lệnh: `python main.py --runs 10 --sensitivity-runs 2` (TẮT) và `python main.py --config configs/scenarios_adaptive.yaml --runs 10 --sensitivity-runs 2` (BẬT). Đơn vị %/năm.

**loan_rate trung bình (gia quyền theo dư nợ)**

| | A | B | C |
|---|---|---|---|
| TẮT, trung bình 18 quý | 8.835 | 8.746 | 8.740 |
| BẬT, trung bình 18 quý | 8.482 | 8.396 | 8.391 |
| TẮT, trung bình Q4/2026–Q3/2027 | 9.038 | 8.637 | 8.611 |
| BẬT, trung bình Q4/2026–Q3/2027 | 8.429 | 8.045 | 8.018 |

**Chênh lệch sau Q4/2026 (điểm %)**

| Quý | B−A (TẮT) | C−A (TẮT) | B−A (BẬT) | C−A (BẬT) |
|---|---|---|---|---|
| Q4/2026 | −0.261 | −0.261 | −0.251 | −0.251 |
| Q1/2027 | −0.391 | −0.402 | −0.373 | −0.389 |
| Q2/2027 | −0.454 | −0.489 | −0.438 | −0.473 |
| Q3/2027 | −0.496 | −0.555 | −0.477 | −0.532 |
| Trung bình | −0.401 | −0.427 | −0.385 | −0.411 |

**loan_rate theo nhóm, trung bình Q4/2026–Q3/2027**

| Kịch bản | Nhóm | TẮT | BẬT |
|---|---|---|---|
| A | quốc doanh | 8.802 | 8.135 |
| A | cổ phần lớn | 8.924 | 8.382 |
| A | cổ phần nhỏ | 10.170 | 9.341 |
| B | quốc doanh | 8.404 | 7.748 |
| B | cổ phần lớn | 8.507 | 7.980 |
| B | cổ phần nhỏ | 9.754 | 8.988 |
| C | quốc doanh | 8.373 | 7.716 |
| C | cổ phần lớn | 8.487 | 7.959 |
| C | cổ phần nhỏ | 9.747 | 8.973 |

Chênh giữa nhóm cao nhất và thấp nhất tại Q3/2027: TẮT A/B/C = 1.329 / 1.323 / 1.378; BẬT = 1.217 / 1.260 / 1.295 (trước chính sách, Q3/2026: TẮT 1.428, BẬT 1.186). Tác động B−A theo nhóm (trung bình Q4/2026–Q3/2027): TẮT −0.417 / −0.398 / −0.416 (cổ phần lớn / quốc doanh / cổ phần nhỏ); BẬT −0.402 / −0.387 / −0.353.

**Biên và tuân thủ (BẬT)**

| Chỉ tiêu | TẮT | BẬT |
|---|---|---|
| `target_margin` trung bình Q3/2027 (lớn / nhỏ / quốc doanh) | 3.2 / 3.2 / 3.2 | 2.42 / 2.35 / 2.43 |
| Tỷ lệ ngân hàng-lần chạy chạm sàn 2.2, Q3/2027 | 0 | 37.5% (3/8 ngân hàng) |
| Chạm trần 4.2 | 0 | 0 |
| Xác suất tuân thủ trung bình (B / C) | 0.939 / 0.941 | 0.878 / 0.882 |
| Tỷ lệ tuân thủ thực tế (B / C) | 0.938 / 0.944 | 0.878 / 0.884 |
| `nim_proxy` trung bình Q4/2026–Q3/2027 (A) | 4.49 | 3.82 |

Kiểm tra mục 6 CLAUDE.md khi BẬT: B và C không cao hơn A ở mọi lần chạy sau Q4/2026; A/B/C trùng nhau ở mọi quý trước chính sách; lãi suất cho vay 7.89–9.10, huy động 4.82–5.78; LDR tối đa 1.23 ≤ 1.60. Không vi phạm.

## 5. Hạn chế

- Mặt bằng lãi suất cho vay giảm ~0.6 điểm % ở A khi bật học; đây là hệ quả của cơ chế, không phải tác động chính sách. Thị phần dư nợ có tổng bằng 1 nên luôn có ngân hàng mất thị phần (tín hiệu giảm kích hoạt thường xuyên), trong khi tín hiệu tăng đòi hỏi `nim_proxy` ≥ n\*; khi lãi suất hội tụ về mức cân bằng (~4.5) `nim_proxy` thấp hơn n\*=5.59 nên bước tăng gần như tắt. Hệ thống có xu hướng trôi về sàn.
- Biên chạm sàn ở 3/8 ngân hàng vào Q3/2027 và tỷ lệ này tăng dần; kết quả phụ thuộc vào sàn 2.2.
- Tất cả tham số học là khởi điểm, chưa hiệu chỉnh theo dữ liệu panel; không có kiểm định ngoài mẫu.
- Một số ít ngân hàng (8) và 10 lần chạy; kịch bản A không có ngẫu nhiên nên các lần chạy giống nhau.
- `nim_proxy` tại t=0 (n\*) phụ thuộc cách định nghĩa chi phí vốn xấp xỉ của mô hình.
- Học làm thay đổi xác suất tuân thủ chỉ đạo (vì xác suất phụ thuộc `nim_proxy`), nên khó tách riêng tác động của chỉ đạo với tác động của học.
- Học chỉ chỉnh biên cho vay; tiền gửi và lãi suất huy động không học.
