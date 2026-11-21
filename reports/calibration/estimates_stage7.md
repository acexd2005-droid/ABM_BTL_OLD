# Giai đoạn 7: ước lượng phương trình hành vi từ panel (sinh tự động)

> Chỉ để đối chiếu với giá trị giả định trong `configs/scenarios.yaml`; **không** sửa configs. Kết quả là ước lượng trong mẫu, không phải tác động chính sách thực tế.

## Phương pháp và hạn chế

- Panel 8 ngân hàng x 15 quý; sau lấy trễ 1 quý còn N = 112 (N = 104 khi cần lãi suất qua đêm trễ 2 quý).
- Ánh xạ: `r^D = deposit_rate_pct/(1-casa)`, nên `c = deposit_rate_pct + 0.15` (kết quả chính). Phụ lục dùng công thức cũ (trừ CASA hai lần).
- Biến thể: (a) OLS gộp; (b) FE ngân hàng; (c) FE ngân hàng + quý; (d) FE ngân hàng + lãi suất qua đêm `bq_gian_don` trễ 0/1/2 quý (tâm hoá, nên hằng số tính tại ON trung bình).
- SE cụm CR1 theo ngân hàng, **chỉ 8 cụm**: SE cụm thường bị đánh thấp, nên dùng t với 7 bậc tự do (giá trị tới hạn 2.3646). Kèm SE thường để so sánh.
- R²: gộp = R² thường; FE = R² within (nền riêng của từng biến thể).
- **Hạn chế quan trọng nhất:** SE cụm theo ngân hàng KHÔNG xử lý được phụ thuộc chéo giữa các ngân hàng trong cùng một quý. Quý FE một mình giải thích khoảng 71% phương sai within của Δr^L (xem mục hấp thụ), tức cú sốc chung rất lớn, nên t-stat và khoảng tin cậy của (a), (b), (d) bị đánh giá QUÁ CAO (với (d) thông tin hiệu dụng của lãi suất qua đêm chỉ cỡ 14 điểm theo quý). Chỉ (c) kiểm soát được cú sốc cộng chung, nhưng vẫn chỉ 8 cụm và vẫn có thể thấp SE. Không nên dùng chữ "có ý nghĩa" cho (a), (b), (d). Wild-cluster bootstrap (Webb, B = 9999) đã làm cho PT1 ở mục riêng bên dưới; Driscoll-Kraay không làm vì T = 14 quá ngắn.
- Nickell (PT1, T = 14): FE ngân hàng làm lệch XUỐNG hệ số của biến trễ r^L_{t-1} (= 1-λ), nên λ của (b), (c), (d) có xu hướng bị lệch LÊN. Ngược lại λ của (a) bị kéo xuống vì hiệu ứng ngân hàng bị bỏ sót (biên khác nhau giữa các NH tương quan với mức r^L_{t-1}). Khoảng λ = 0.11 đến 0.53 là khoảng giữa hai cực thiên lệch, KHÔNG phải khoảng tin cậy.
- Biến thể (d) thêm lãi suất qua đêm, vốn không có trong mô hình; kiểm định b+γ=1 bị bác ở (d0) và (d1), nên (d) không còn là PT1 của mô hình. Hằng số của (d) tính tại ON trung bình.
- Kiểm định ràng buộc b+γ=1 không bị bác ở (a), (b), (c) và ổn định ở N=104: dữ liệu ủng hộ dạng điều chỉnh từng phần của PT1 (không bác bỏ; với 8 cụm kiểm định có thể thiếu lực).
- λ đo tốc độ điều chỉnh của lợi suất bình quân danh mục (sổ sách). Nếu r^L trong mô hình là lãi suất chào cho khoản vay mới, λ sổ sách có thể thấp hơn λ của lãi suất chào. Cần chốt khái niệm r^L trước Giai đoạn 9.
- Hằng số/đại lượng suy ra trong biến thể FE (`margin_const`, `a_D`, `base_growth_L`, `mu_margin`) là trung bình hằng số FE theo ngân hàng; cột `se_cluster` của các hàng đó là **độ phân tán giữa NH sd/√8, không phải SE chuẩn** (bỏ qua sai số ước lượng hằng số từng NH và hiệp phương sai với độ dốc). Biến thể (c) không nhận diện được mức.
- PT3/PT4 là cân bằng cung-cầu đồng thời, OLS không cho nhân quả. Hệ số PT4 gộp có dấu ngược (β > 0): xu hướng chung 2023-2026 (lãi suất giảm, tăng trưởng cao), không phải độ co giãn. Dấu dương của ε trong (b), (d1) KHÔNG bền: ở mẫu N = 104 các biến thể (b), (c), (d2) đều có khoảng tin cậy chứa 0 (xem bảng ổn định).
- Cả `deposit_rate_pct` và `loan_rate_pct` là lợi suất sổ sách, trễ so với lãi suất cận biên.
- Mô hình chặn g^D trong ±0.04 và g^L trong [-0.04, 0.035], nhưng 42% quan sát g^D và 59% g^L nằm ngoài; OLS ước lượng phần tuyến tính toàn mẫu. Hằng số ước lượng a_D ≈ 0.045 và base_growth_L ≈ 0.05 cao gấp 8-11 lần giá trị mô hình (0.004, 0.006): đây là **khoảng cách mô hình - dữ liệu** (tăng trưởng nền của dữ liệu lớn hơn cả trần chặn), không phải kết quả ước lượng độ nhạy lãi suất.
- `target_margin` (3.2) và `loan_spread_add` (1.35) chỉ nhận diện được **tổng**. Ước lượng μ ≈ 4.59 **nhất quán với 4.55 (chưa phải kiểm định độc lập; nguồn gốc loan_spread_add=1.35 đang được xác minh)**. Ngoài ra r^L - c_{t-1} chưa ở trạng thái dừng (c giảm mạnh giai đoạn 2023-2024, r^L điều chỉnh chậm).

## Bảng chính (mẫu N = 112; c = deposit_rate_pct + 0.15)

| equation | parameter | bien_the | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | se_ols | R2 | n | yaml_value |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PT1 | lambda | a | 0.1104 | 0.0383 | 2.8791 | 0.0197 | 0.2010 | 0.0308 | 0.1043 | 112 | 0.4800 |
| PT1 | margin_const | a | 3.8494 | 0.5018 | 7.6710 | 2.6628 | 5.0359 |  | 0.1043 | 112 | 4.5500 |
| PT1 | lambda | b | 0.5275 | 0.0568 | 9.2794 | 0.3931 | 0.6619 | 0.0604 | 0.4251 | 112 | 0.4800 |
| PT1 | margin_const | b | 4.5061 | 0.6823 | 6.6042 | 2.8927 | 6.1195 |  | 0.4251 | 112 | 4.5500 |
| PT1 | lambda | c | 0.2740 | 0.0450 | 6.0836 | 0.1675 | 0.3804 | 0.0742 | 0.1317 | 112 | 0.4800 |
| PT1 | lambda | d(lag0) | 0.3639 | 0.0619 | 5.8829 | 0.2177 | 0.5102 | 0.0650 | 0.5286 | 112 | 0.4800 |
| PT1 | margin_const | d(lag0) | 4.4280 | 0.8880 | 4.9864 | 2.3282 | 6.5278 |  | 0.5286 | 112 | 4.5500 |
| PT1 | lambda | d(lag1) | 0.3145 | 0.0438 | 7.1751 | 0.2109 | 0.4182 | 0.0585 | 0.6116 | 112 | 0.4800 |
| PT1 | margin_const | d(lag1) | 4.3884 | 0.7696 | 5.7020 | 2.5686 | 6.2083 |  | 0.6116 | 112 | 4.5500 |
| PT1b | b+gamma-1 | a | 0.0057 | 0.0272 | 0.2085 | -0.0587 | 0.0700 |  | 0.9495 | 112 | 0.0000 |
| PT1b | b+gamma-1 | b | 0.0180 | 0.0370 | 0.4857 | -0.0695 | 0.1054 |  | 0.8559 | 112 | 0.0000 |
| PT1b | b+gamma-1 | c | -0.1944 | 0.1943 | -1.0005 | -0.6538 | 0.2650 |  | 0.4219 | 112 | 0.0000 |
| PT1b | b+gamma-1 | d(lag0) | 0.2608 | 0.0475 | 5.4854 | 0.1484 | 0.3732 |  | 0.9067 | 112 | 0.0000 |
| PT1b | b+gamma-1 | d(lag1) | 0.0399 | 0.0124 | 3.2248 | 0.0107 | 0.0692 |  | 0.9035 | 112 | 0.0000 |
| PT2 | mu_margin | a | 4.5882 | 0.4881 | 9.4001 | 3.4340 | 5.7424 | 0.1306 | 0.0000 | 112 | 4.5500 |
| PT2 | mu_margin | b | 4.5882 | 0.4881 | 9.4001 | 3.4340 | 5.7424 | 0.1306 | 0.0000 | 112 | 4.5500 |
| PT2 | mu_margin | d(lag0) | 4.5882 | 0.4881 | 9.4001 | 3.4340 | 5.7424 |  | 0.0016 | 112 | 4.5500 |
| PT2 | mu_margin | d(lag1) | 4.5882 | 0.4881 | 9.4001 | 3.4340 | 5.7424 |  | 0.0046 | 112 | 4.5500 |
| PT3 | sigma | a | 0.0182 | 0.0084 | 2.1691 | -0.0016 | 0.0381 | 0.0053 | 0.0985 | 112 | 0.0350 |
| PT3 | a_D | a | 0.0447 | 0.0044 | 10.1581 | 0.0343 | 0.0551 | 0.0042 | 0.0985 | 112 | 0.0040 |
| PT3 | sigma | b | 0.0071 | 0.0095 | 0.7478 | -0.0154 | 0.0297 | 0.0072 | 0.0095 | 112 | 0.0350 |
| PT3 | a_D | b | 0.0447 | 0.0060 | 7.4109 | 0.0304 | 0.0590 |  | 0.0095 | 112 | 0.0040 |
| PT3 | sigma | c | 0.0177 | 0.0110 | 1.6104 | -0.0083 | 0.0436 | 0.0133 | 0.0193 | 112 | 0.0350 |
| PT3 | sigma | d(lag0) | 0.0207 | 0.0110 | 1.8792 | -0.0053 | 0.0467 | 0.0102 | 0.0420 | 112 | 0.0350 |
| PT3 | a_D | d(lag0) | 0.0447 | 0.0041 | 10.8741 | 0.0350 | 0.0544 |  | 0.0420 | 112 | 0.0040 |
| PT3 | sigma | d(lag1) | 0.0212 | 0.0104 | 2.0402 | -0.0034 | 0.0457 | 0.0118 | 0.0306 | 112 | 0.0350 |
| PT3 | a_D | d(lag1) | 0.0447 | 0.0041 | 10.9981 | 0.0351 | 0.0543 |  | 0.0306 | 112 | 0.0040 |
| PT4 | epsilon | a | -0.0050 | 0.0005 | -10.4157 | -0.0061 | -0.0038 | 0.0016 | 0.0768 | 112 | 0.0120 |
| PT4 | base_growth_L | a | 0.0553 | 0.0036 | 15.2973 | 0.0467 | 0.0638 |  | 0.0768 | 112 | 0.0060 |
| PT4 | epsilon | b | 0.0049 | 0.0018 | 2.7415 | 0.0007 | 0.0091 | 0.0033 | 0.0207 | 112 | 0.0120 |
| PT4 | base_growth_L | b | 0.0465 | 0.0194 | 2.4034 | 0.0008 | 0.0923 |  | 0.0207 | 112 | 0.0060 |
| PT4 | epsilon | c | 0.0070 | 0.0082 | 0.8615 | -0.0123 | 0.0263 | 0.0085 | 0.0076 | 112 | 0.0120 |
| PT4 | epsilon | d(lag0) | 0.0069 | 0.0031 | 2.2202 | -0.0004 | 0.0142 | 0.0039 | 0.0292 | 112 | 0.0120 |
| PT4 | base_growth_L | d(lag0) | 0.0447 | 0.0314 | 1.4243 | -0.0295 | 0.1190 |  | 0.0292 | 112 | 0.0060 |
| PT4 | epsilon | d(lag1) | 0.0056 | 0.0021 | 2.5891 | 0.0005 | 0.0106 | 0.0033 | 0.0613 | 112 | 0.0120 |
| PT4 | base_growth_L | d(lag1) | 0.0459 | 0.0226 | 2.0309 | -0.0075 | 0.0994 |  | 0.0613 | 112 | 0.0060 |


## Độ trễ 2 quý (mẫu N = 104, cùng mẫu cho a, b, c, d2)

| equation | parameter | bien_the | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | se_ols | R2 | n | yaml_value |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PT1 | lambda | a | 0.1207 | 0.0457 | 2.6405 | 0.0126 | 0.2288 | 0.0329 | 0.1165 | 104 | 0.4800 |
| PT1 | margin_const | a | 3.7921 | 0.5270 | 7.1962 | 2.5460 | 5.0381 |  | 0.1165 | 104 | 4.5500 |
| PT1 | lambda | b | 0.6249 | 0.0754 | 8.2845 | 0.4465 | 0.8033 | 0.0592 | 0.5397 | 104 | 0.4800 |
| PT1 | margin_const | b | 4.4668 | 0.7246 | 6.1647 | 2.7535 | 6.1801 |  | 0.5397 | 104 | 4.5500 |
| PT1 | lambda | c | 0.3209 | 0.0554 | 5.7957 | 0.1900 | 0.4518 | 0.0754 | 0.1791 | 104 | 0.4800 |
| PT1 | lambda | d(lag2) | 0.5035 | 0.0761 | 6.6191 | 0.3236 | 0.6833 | 0.0692 | 0.5815 | 104 | 0.4800 |
| PT1 | margin_const | d(lag2) | 4.4278 | 0.8241 | 5.3729 | 2.4791 | 6.3765 |  | 0.5815 | 104 | 4.5500 |
| PT1b | b+gamma-1 | a | -0.0129 | 0.0325 | -0.3966 | -0.0897 | 0.0639 |  | 0.9438 | 104 | 0.0000 |
| PT1b | b+gamma-1 | b | -0.0474 | 0.0414 | -1.1442 | -0.1453 | 0.0505 |  | 0.8360 | 104 | 0.0000 |
| PT1b | b+gamma-1 | c | -0.1924 | 0.1987 | -0.9682 | -0.6624 | 0.2775 |  | 0.4234 | 104 | 0.0000 |
| PT1b | b+gamma-1 | d(lag2) | -0.1032 | 0.0322 | -3.2105 | -0.1792 | -0.0272 |  | 0.8569 | 104 | 0.0000 |
| PT2 | mu_margin | a | 4.5274 | 0.4885 | 9.2681 | 3.3723 | 5.6825 | 0.1336 | 0.0000 | 104 | 4.5500 |
| PT2 | mu_margin | b | 4.5274 | 0.4885 | 9.2681 | 3.3723 | 5.6825 | 0.1336 | 0.0000 | 104 | 4.5500 |
| PT2 | mu_margin | d(lag2) | 4.5274 | 0.4885 | 9.2681 | 3.3723 | 5.6825 |  | 0.0110 | 104 | 4.5500 |
| PT3 | sigma | a | 0.0129 | 0.0060 | 2.1445 | -0.0013 | 0.0271 | 0.0051 | 0.0593 | 104 | 0.0350 |
| PT3 | a_D | a | 0.0431 | 0.0042 | 10.3242 | 0.0332 | 0.0530 | 0.0040 | 0.0593 | 104 | 0.0040 |
| PT3 | sigma | b | 0.0030 | 0.0061 | 0.4895 | -0.0115 | 0.0175 | 0.0069 | 0.0020 | 104 | 0.0350 |
| PT3 | a_D | b | 0.0428 | 0.0055 | 7.8011 | 0.0298 | 0.0558 |  | 0.0020 | 104 | 0.0040 |
| PT3 | sigma | c | 0.0101 | 0.0104 | 0.9728 | -0.0145 | 0.0348 | 0.0123 | 0.0081 | 104 | 0.0350 |
| PT3 | sigma | d(lag2) | -0.0046 | 0.0064 | -0.7172 | -0.0197 | 0.0105 | 0.0082 | 0.0307 | 104 | 0.0350 |
| PT3 | a_D | d(lag2) | 0.0426 | 0.0068 | 6.2755 | 0.0265 | 0.0586 |  | 0.0307 | 104 | 0.0040 |
| PT4 | epsilon | a | -0.0063 | 0.0005 | -11.6091 | -0.0076 | -0.0050 | 0.0017 | 0.1159 | 104 | 0.0120 |
| PT4 | base_growth_L | a | 0.0592 | 0.0033 | 17.8657 | 0.0514 | 0.0670 |  | 0.1159 | 104 | 0.0060 |
| PT4 | epsilon | b | 0.0023 | 0.0011 | 2.0487 | -0.0004 | 0.0049 | 0.0041 | 0.0033 | 104 | 0.0120 |
| PT4 | base_growth_L | b | 0.0502 | 0.0131 | 3.8234 | 0.0192 | 0.0813 |  | 0.0033 | 104 | 0.0060 |
| PT4 | epsilon | c | 0.0097 | 0.0051 | 1.8789 | -0.0025 | 0.0218 | 0.0090 | 0.0136 | 104 | 0.0120 |
| PT4 | epsilon | d(lag2) | 0.0026 | 0.0014 | 1.8456 | -0.0007 | 0.0060 | 0.0041 | 0.0070 | 104 | 0.0120 |
| PT4 | base_growth_L | d(lag2) | 0.0499 | 0.0158 | 3.1477 | 0.0124 | 0.0873 |  | 0.0070 | 104 | 0.0060 |


## FE quý hấp thụ bao nhiêu, lãi suất qua đêm thay thế được bao nhiêu

Các `share_*` là tỷ lệ phương sai within-ngân-hàng của biến phụ thuộc được giải thích (nền chung = tổng bình phương sau khi trừ trung bình ngân hàng). `ratio_ON_vs_quarterFE` = (share_X_bank_ON - share_X_bank_FE) / (share_X_bank_quarter_FE - share_X_bank_FE), chưa hiệu chỉnh bậc tự do (13 biến giả quý luôn cộng thêm R² giả nhiều hơn 1 biến ON, nên tỷ lệ này có thể thấp hơn thực tế); `ratio_adj_df` là bản hiệu chỉnh. `R2_common_on_ON` = R² khi hồi quy thành phần chung theo quý (trung bình các NH của biến sau khi trừ trung bình NH) lên lãi suất qua đêm trễ k, **chỉ trên 14 hoặc 13 điểm** và bị chi phối bởi cú sốc 2023 (ON giảm 4.8 -> 3.6 -> 0.2). `approx_share_explained_by_ON_via_common` = R2_common_on_ON x share_quarter_FE_only: phần phương sai within của biến phụ thuộc mà ON giải thích qua thành phần chung (ví dụ Δr^L, trễ 1: khoảng 0.5, không phải 0.71). Lưu ý: ở PT1 trễ 1, `share_quarter_FE_only` (0.708105) và `R2_common_on_ON` (0.708102) trùng đến 5 chữ số **do ngẫu nhiên**; chúng là hai đại lượng khác nhau.

| equation | lag_on | n | share_X_bank_FE | share_quarter_FE_only | share_X_bank_quarter_FE | share_X_bank_ON | ratio_ON_vs_quarterFE | ratio_adj_df | R2_common_on_ON | slope_common_on_ON | approx_share_explained_by_ON_via_common |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PT1 | 0 | 112 | 0.4251 | 0.7081 | 0.7465 | 0.5286 | 0.3221 | 0.3472 | 0.5417 | 0.1763 | 0.3836 |
| PT1 | 1 | 112 | 0.4251 | 0.7081 | 0.7465 | 0.6116 | 0.5802 | 0.6414 | 0.7081 | 0.1989 | 0.5014 |
| PT1 | 2 | 104 | 0.5397 | 0.7203 | 0.7704 | 0.5815 | 0.1811 | 0.1890 | 0.4804 | 0.1722 | 0.3460 |
| PT2 | 0 | 112 | 0.0000 | 0.4286 | 0.4286 | 0.0016 | 0.0037 | -0.0233 | 0.0037 | -0.0109 | 0.0016 |
| PT2 | 1 | 112 | 0.0000 | 0.4286 | 0.4286 | 0.0046 | 0.0107 | -0.0147 | 0.0107 | 0.0182 | 0.0046 |
| PT2 | 2 | 104 | 0.0000 | 0.3067 | 0.3067 | 0.0110 | 0.0359 | 0.0029 | 0.0359 | -0.0249 | 0.0110 |
| PT3 | 0 | 112 | 0.0095 | 0.3067 | 0.3201 | 0.0420 | 0.1047 | 0.1089 | 0.0104 | -0.0014 | 0.0032 |
| PT3 | 1 | 112 | 0.0095 | 0.3067 | 0.3201 | 0.0306 | 0.0680 | 0.0547 | 0.0004 | -0.0003 | 0.0001 |
| PT3 | 2 | 104 | 0.0020 | 0.3528 | 0.3580 | 0.0307 | 0.0807 | 0.0700 | 0.0779 | 0.0037 | 0.0275 |
| PT4 | 0 | 112 | 0.0207 | 0.3967 | 0.4013 | 0.0292 | 0.0225 | -0.0032 | 0.0000 | -0.0000 | 0.0000 |
| PT4 | 1 | 112 | 0.0207 | 0.3967 | 0.4013 | 0.0613 | 0.1067 | 0.1068 | 0.0878 | -0.0036 | 0.0348 |
| PT4 | 2 | 104 | 0.0033 | 0.3920 | 0.4003 | 0.0070 | 0.0093 | -0.0222 | 0.0067 | 0.0010 | 0.0026 |


## Wild-cluster bootstrap cho PT1 (λ và hệ số lãi suất qua đêm trễ 1 quý)

WCR-t (áp đặt H0), trọng số Webb 6 điểm, B = 9999, seed = 20261121 (cố định), chỉ numpy; p-value đối xứng của H0: hệ số = 0; khoảng tin cậy boot = đảo kiểm định trên lưới. Cạnh đó là CR1 (t với 7 bậc tự do). Bootstrap chạy trên dữ liệu đã biến đổi within và vẫn chỉ có 8 cụm; với (d1), ON là biến chung theo quý nên thông tin hiệu dụng của hệ số ON chỉ cỡ 14 điểm: bootstrap theo ngân hàng không khắc phục được hạn chế này. Không làm Driscoll-Kraay (T = 14 quá ngắn).

| variant | parameter | coef | se_cr1 | t_cr1 | ci_cr1_lo | ci_cr1_hi | p_boot | ci_boot_lo | ci_boot_hi |
|---|---|---|---|---|---|---|---|---|---|
| c | lambda | 0.2740 | 0.0450 | 6.0836 | 0.1675 | 0.3804 | 0.0030 | 0.1584 | 0.3952 |
| d1 | lambda | 0.3145 | 0.0438 | 7.1751 | 0.2109 | 0.4182 | 0.0021 | 0.2237 | 0.4489 |
| d1 | ON_lag1 | 0.1420 | 0.0214 | 6.6382 | 0.0914 | 0.1926 | 0.0059 | 0.0891 | 0.1872 |


Tác động dài hạn của ON trong (d1): 0.142/0.315 ≈ 0.45 (ON +1 điểm % lâu dài → r^L +0.45 điểm %). Dùng làm mốc kiểm tra độ lớn cho Giai đoạn 8. Lưu ý (d1) bác b+γ=1 (0.040, t=3.2).


## Ổn định giữa N = 112 và N = 104 (bỏ 2023Q2), biến thể a, b, c

`CI..._chua_0` = True nghĩa là khoảng tin cậy 95% (cụm, t7) chứa 0. Cảnh báo: với (a), (b) khoảng tin cậy bị đánh giá quá hẹp do cú sốc chung theo quý.

| equation | parameter | variant | coef_N112 | coef_N104 | CI112_chua_0 | CI104_chua_0 | doi_dau |
|---|---|---|---|---|---|---|---|
| PT1 | lambda | a | 0.1104 | 0.1207 | False | False | False |
| PT1 | lambda | b | 0.5275 | 0.6249 | False | False | False |
| PT1 | lambda | c | 0.2740 | 0.3209 | False | False | False |
| PT1 | margin_const | a | 3.8494 | 3.7921 | False | False | False |
| PT1 | margin_const | b | 4.5061 | 4.4668 | False | False | False |
| PT1b | b+gamma-1 | a | 0.0057 | -0.0129 | True | True | True |
| PT1b | b+gamma-1 | b | 0.0180 | -0.0474 | True | True | True |
| PT1b | b+gamma-1 | c | -0.1944 | -0.1924 | True | True | False |
| PT2 | mu_margin | a | 4.5882 | 4.5274 | False | False | False |
| PT2 | mu_margin | b | 4.5882 | 4.5274 | False | False | False |
| PT3 | a_D | a | 0.0447 | 0.0431 | False | False | False |
| PT3 | a_D | b | 0.0447 | 0.0428 | False | False | False |
| PT3 | sigma | a | 0.0182 | 0.0129 | True | True | False |
| PT3 | sigma | b | 0.0071 | 0.0030 | True | True | False |
| PT3 | sigma | c | 0.0177 | 0.0101 | True | True | False |
| PT4 | base_growth_L | a | 0.0553 | 0.0592 | False | False | False |
| PT4 | base_growth_L | b | 0.0465 | 0.0502 | False | False | False |
| PT4 | epsilon | a | -0.0050 | -0.0063 | False | False | False |
| PT4 | epsilon | b | 0.0049 | 0.0023 | False | True | False |
| PT4 | epsilon | c | 0.0070 | 0.0097 | True | True | False |


## Mùa vụ theo quý trong năm (chỉ là gợi ý, chưa kiểm định; số quan sát theo quý không cân bằng nên lẫn xu hướng thời gian)

| bien | quy_trong_nam | tb_tho | tb_tru_TB_NH | n |
|---|---|---|---|---|
| g^D | 1 | 0.0174 | -0.0273 | 24 |
| g^D | 2 | 0.0558 | 0.0111 | 32 |
| g^D | 3 | 0.0308 | -0.0139 | 32 |
| g^D | 4 | 0.0757 | 0.0310 | 24 |
| g^L | 1 | 0.0373 | -0.0136 | 24 |
| g^L | 2 | 0.0598 | 0.0089 | 32 |
| g^L | 3 | 0.0354 | -0.0154 | 32 |
| g^L | 4 | 0.0731 | 0.0222 | 24 |
| Δr^L | 1 | -0.3754 | -0.2837 | 24 |
| Δr^L | 2 | 0.0875 | 0.1791 | 32 |
| Δr^L | 3 | -0.0046 | 0.0871 | 32 |
| Δr^L | 4 | -0.1629 | -0.0713 | 24 |


## Quan sát bất thường để Minh kiểm tra

`z_robust` = (x - trung vị)/(1.4826 MAD) trên toàn mẫu 112 quan sát.

| bien | bank_id | period | gia_tri | z_robust | ly_do |
|---|---|---|---|---|---|
| g^D | HDBank | 2023Q2 | 0.2396 | 6.0320 | z robust lớn nhất |
| g^D | MB Bank | 2023Q4 | 0.1830 | 4.3794 | z robust lớn nhất |
| g^D | VPBank | 2023Q2 | 0.1704 | 4.0099 | z robust lớn nhất |
| g^D | MB Bank | 2025Q4 | 0.1692 | 3.9756 | z robust lớn nhất |
| g^D | HDBank | 2025Q4 | 0.1493 | 3.3946 | z robust lớn nhất |
| g^D | MB Bank | 2024Q4 | 0.1380 | 3.0627 | z robust lớn nhất |
| g^L | HDBank | 2023Q4 | 0.1772 | 3.7855 | z robust lớn nhất |
| g^L | MB Bank | 2025Q4 | 0.1637 | 3.3943 | z robust lớn nhất |
| g^L | HDBank | 2025Q2 | 0.1400 | 2.7030 | z robust lớn nhất |
| g^L | MB Bank | 2023Q4 | 0.1394 | 2.6856 | z robust lớn nhất |
| g^L | VPBank | 2025Q2 | 0.1358 | 2.5827 | z robust lớn nhất |
| g^L | HDBank | 2025Q3 | -0.0392 | -2.5108 | z robust lớn nhất |
| Δr^L | MB Bank | 2026Q2 | 1.3721 | 3.0412 | z robust lớn nhất |
| Δr^L | HDBank | 2024Q1 | -1.2918 | -2.7498 | z robust lớn nhất |
| Δr^L | VPBank | 2024Q1 | -1.1546 | -2.4516 | z robust lớn nhất |
| Δr^L | ACB | 2023Q4 | -1.0894 | -2.3099 | z robust lớn nhất |
| Δr^L | BIDV | 2024Q1 | -1.0627 | -2.2519 | z robust lớn nhất |
| Δr^L | ACB | 2026Q2 | 0.9307 | 2.0816 | z robust lớn nhất |
| g^D | HDBank | 2023Q2 | 0.2396 | 6.0320 | HDBank 2023Q2 / MB Bank quý 4 (yêu cầu kiểm tra) |
| g^L | HDBank | 2023Q2 | -0.0041 | -1.4876 | HDBank 2023Q2 / MB Bank quý 4 (yêu cầu kiểm tra) |
| Δr^L | HDBank | 2023Q2 | 0.3468 | 0.8124 | HDBank 2023Q2 / MB Bank quý 4 (yêu cầu kiểm tra) |
| g^D | MB Bank | 2023Q4 | 0.1830 | 4.3794 | HDBank 2023Q2 / MB Bank quý 4 (yêu cầu kiểm tra) |
| g^L | MB Bank | 2023Q4 | 0.1394 | 2.6856 | HDBank 2023Q2 / MB Bank quý 4 (yêu cầu kiểm tra) |
| Δr^L | MB Bank | 2023Q4 | -0.9678 | -2.0456 | HDBank 2023Q2 / MB Bank quý 4 (yêu cầu kiểm tra) |
| g^D | MB Bank | 2024Q4 | 0.1380 | 3.0627 | HDBank 2023Q2 / MB Bank quý 4 (yêu cầu kiểm tra) |
| g^L | MB Bank | 2024Q4 | 0.1063 | 1.7239 | HDBank 2023Q2 / MB Bank quý 4 (yêu cầu kiểm tra) |
| Δr^L | MB Bank | 2024Q4 | 0.0440 | 0.1541 | HDBank 2023Q2 / MB Bank quý 4 (yêu cầu kiểm tra) |
| g^D | MB Bank | 2025Q4 | 0.1692 | 3.9756 | HDBank 2023Q2 / MB Bank quý 4 (yêu cầu kiểm tra) |
| g^L | MB Bank | 2025Q4 | 0.1637 | 3.3943 | HDBank 2023Q2 / MB Bank quý 4 (yêu cầu kiểm tra) |
| Δr^L | MB Bank | 2025Q4 | 0.2810 | 0.6693 | HDBank 2023Q2 / MB Bank quý 4 (yêu cầu kiểm tra) |


## Quyết định của trưởng nhóm sau phản biện (vòng reviewer 2)

1. **Không cập nhật tham số nào trong `configs/` cho tới Giai đoạn 9.** λ = 0.48 trong configs nằm NGOÀI khoảng tin cậy bootstrap của cả (c) [0.158; 0.395] và (d1) [0.224; 0.449]. Nickell làm λ của các biến thể có FE ngân hàng lệch lên (ước lượng thô ~+0.1 với T=14), nên λ thực có thể còn thấp hơn 0.27. Lưới tìm kiếm Giai đoạn 9: 0.10–0.45, dày quanh 0.15–0.35. σ và ε chỉ là tương quan mô tả, không dùng làm tham số nhân quả.
2. **Biến thể chuẩn cho tham số hành vi: (c)** FE ngân hàng + quý. **Đặc tả macro cho Giai đoạn 8: (d) với lãi suất qua đêm trễ 1 quý**, tác động vào phương trình lãi suất cho vay (PT1).
3. Wild-cluster bootstrap đã làm cho λ và hệ số ON trễ 1 (bảng trên); không làm Driscoll-Kraay.
4. μ ≈ 4.59 **nhất quán với 4.55 (chưa phải kiểm định độc lập; nguồn gốc loan_spread_add=1.35 đang được xác minh)**.
5. **Khoảng cách tăng trưởng nền và ngưỡng chặn là vấn đề cấu trúc, chuyển sang Giai đoạn 9**: `base_growth` (tiền gửi 0.004, dư nợ 0.006) và các ngưỡng chặn (±0.04 cho tiền gửi; [-0.04, 0.035] cho dư nợ) sẽ nằm trong danh sách tham số hiệu chỉnh. Dữ liệu cho a_D ≈ 0.045 và base_growth_L ≈ 0.05; 42% quan sát g^D và 59% g^L vượt ngưỡng chặn hiện tại.


## Phụ lục: công thức chi phí vốn cũ (trừ CASA hai lần)

| equation | parameter | bien_the | coef | se_cluster | t_cluster | ci95_lo | ci95_hi | se_ols | R2 | n | yaml_value |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PT1 | lambda | a | 0.1078 | 0.0329 | 3.2797 | 0.0301 | 0.1856 | 0.0305 | 0.1022 | 112 | 0.4800 |
| PT1 | margin_const | a | 4.6689 | 0.5351 | 8.7249 | 3.4035 | 5.9342 |  | 0.1022 | 112 | 4.5500 |
| PT1 | lambda | b | 0.4758 | 0.0334 | 14.2648 | 0.3969 | 0.5547 | 0.0580 | 0.3953 | 112 | 0.4800 |
| PT1 | margin_const | b | 5.3262 | 0.6088 | 8.7482 | 3.8865 | 6.7658 |  | 0.3953 | 112 | 4.5500 |
| PT1 | lambda | c | 0.2702 | 0.0465 | 5.8174 | 0.1604 | 0.3801 | 0.0725 | 0.1336 | 112 | 0.4800 |
| PT1 | lambda | d(lag0) | 0.3007 | 0.0748 | 4.0212 | 0.1239 | 0.4775 | 0.0689 | 0.4805 | 112 | 0.4800 |
| PT1 | margin_const | d(lag0) | 5.2140 | 1.3797 | 3.7790 | 1.9515 | 8.4764 |  | 0.4805 | 112 | 4.5500 |
| PT1 | lambda | d(lag1) | 0.2727 | 0.0358 | 7.6084 | 0.1880 | 0.3575 | 0.0554 | 0.5971 | 112 | 0.4800 |
| PT1 | margin_const | d(lag1) | 5.1827 | 0.8271 | 6.2663 | 3.2270 | 7.1384 |  | 0.5971 | 112 | 4.5500 |
| PT1b | b+gamma-1 | a | -0.0039 | 0.0241 | -0.1620 | -0.0608 | 0.0530 |  | 0.9494 | 112 | 0.0000 |
| PT1b | b+gamma-1 | b | 0.0909 | 0.0667 | 1.3635 | -0.0668 | 0.2486 |  | 0.8519 | 112 | 0.0000 |
| PT1b | b+gamma-1 | c | -0.1925 | 0.2015 | -0.9555 | -0.6689 | 0.2839 |  | 0.4233 | 112 | 0.0000 |
| PT1b | b+gamma-1 | d(lag0) | 0.3250 | 0.0589 | 5.5178 | 0.1857 | 0.4643 |  | 0.9011 | 112 | 0.0000 |
| PT1b | b+gamma-1 | d(lag1) | 0.0905 | 0.0196 | 4.6154 | 0.0442 | 0.1369 |  | 0.9025 | 112 | 0.0000 |
| PT2 | mu_margin | a | 5.4271 | 0.4898 | 11.0803 | 4.2690 | 6.5853 | 0.1324 | 0.0000 | 112 | 4.5500 |
| PT2 | mu_margin | b | 5.4271 | 0.4898 | 11.0803 | 4.2690 | 6.5853 | 0.1324 | 0.0000 | 112 | 4.5500 |
| PT2 | mu_margin | d(lag0) | 5.4271 | 0.4898 | 11.0803 | 4.2690 | 6.5853 |  | 0.0374 | 112 | 4.5500 |
| PT2 | mu_margin | d(lag1) | 5.4271 | 0.4898 | 11.0803 | 4.2690 | 6.5853 |  | 0.0009 | 112 | 4.5500 |
| PT3 | sigma | a | 0.0182 | 0.0084 | 2.1691 | -0.0016 | 0.0381 | 0.0053 | 0.0985 | 112 | 0.0350 |
| PT3 | a_D | a | 0.0447 | 0.0044 | 10.1581 | 0.0343 | 0.0551 | 0.0042 | 0.0985 | 112 | 0.0040 |
| PT3 | sigma | b | 0.0071 | 0.0095 | 0.7478 | -0.0154 | 0.0297 | 0.0072 | 0.0095 | 112 | 0.0350 |
| PT3 | a_D | b | 0.0447 | 0.0060 | 7.4109 | 0.0304 | 0.0590 |  | 0.0095 | 112 | 0.0040 |
| PT3 | sigma | c | 0.0177 | 0.0110 | 1.6104 | -0.0083 | 0.0436 | 0.0133 | 0.0193 | 112 | 0.0350 |
| PT3 | sigma | d(lag0) | 0.0207 | 0.0110 | 1.8792 | -0.0053 | 0.0467 | 0.0102 | 0.0420 | 112 | 0.0350 |
| PT3 | a_D | d(lag0) | 0.0447 | 0.0041 | 10.8741 | 0.0350 | 0.0544 |  | 0.0420 | 112 | 0.0040 |
| PT3 | sigma | d(lag1) | 0.0212 | 0.0104 | 2.0402 | -0.0034 | 0.0457 | 0.0118 | 0.0306 | 112 | 0.0350 |
| PT3 | a_D | d(lag1) | 0.0447 | 0.0041 | 10.9981 | 0.0351 | 0.0543 |  | 0.0306 | 112 | 0.0040 |
| PT4 | epsilon | a | -0.0050 | 0.0005 | -10.4157 | -0.0061 | -0.0038 | 0.0016 | 0.0768 | 112 | 0.0120 |
| PT4 | base_growth_L | a | 0.0553 | 0.0036 | 15.2973 | 0.0467 | 0.0638 |  | 0.0768 | 112 | 0.0060 |
| PT4 | epsilon | b | 0.0049 | 0.0018 | 2.7415 | 0.0007 | 0.0091 | 0.0033 | 0.0207 | 112 | 0.0120 |
| PT4 | base_growth_L | b | 0.0465 | 0.0194 | 2.4034 | 0.0008 | 0.0923 |  | 0.0207 | 112 | 0.0060 |
| PT4 | epsilon | c | 0.0070 | 0.0082 | 0.8615 | -0.0123 | 0.0263 | 0.0085 | 0.0076 | 112 | 0.0120 |
| PT4 | epsilon | d(lag0) | 0.0069 | 0.0031 | 2.2202 | -0.0004 | 0.0142 | 0.0039 | 0.0292 | 112 | 0.0120 |
| PT4 | base_growth_L | d(lag0) | 0.0447 | 0.0314 | 1.4243 | -0.0295 | 0.1190 |  | 0.0292 | 112 | 0.0060 |
| PT4 | epsilon | d(lag1) | 0.0056 | 0.0021 | 2.5891 | 0.0005 | 0.0106 | 0.0033 | 0.0613 | 112 | 0.0120 |
| PT4 | base_growth_L | d(lag1) | 0.0459 | 0.0226 | 2.0309 | -0.0075 | 0.0994 |  | 0.0613 | 112 | 0.0060 |


Toàn bộ hàng (mọi hệ số, hằng số, SE thường, R² chung nền): `estimates_stage7.csv`; hấp thụ: `absorption_stage7.csv`; bất thường: `outliers_stage7.csv`; bootstrap: `bootstrap_stage7.csv`.
