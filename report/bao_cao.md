## 6. Giả định, hạn chế và lưu ý diễn giải kết quả

### 6.1. Các giả định của mô hình

Nghiên cứu xây dựng mô hình mô phỏng dựa trên tác nhân (Agent-Based Model – ABM) nhằm phân tích phản ứng của các ngân hàng thương mại trước chính sách chỉ đạo giảm lãi suất cho vay. Mô hình sử dụng dữ liệu khởi tạo của 8 ngân hàng thương mại Việt Nam, được phân thành ba nhóm tương đối trong phạm vi mẫu nghiên cứu, bao gồm ngân hàng quốc doanh, ngân hàng thương mại cổ phần lớn và ngân hàng thương mại cổ phần nhỏ.

Mô hình được triển khai theo tần suất quý, trong đó Q1/2023 là kỳ khởi tạo và mỗi bước mô phỏng tương ứng một quý. Tổng thời gian mô phỏng gồm 18 bước, từ Q2/2023 đến Q3/2027. Chính sách được giả định bắt đầu tác động từ bước 15, tương ứng Q4/2026. Do sử dụng tần suất quý, mô hình gộp các mốc chỉ đạo trong tháng 8 và tháng 10/2026 vào một thời điểm can thiệp giả định, chưa phân biệt riêng tác động của từng sự kiện.

Hệ thống bao gồm các tác nhân ngân hàng, cơ quan quản lý và hai khối hành vi tổng hợp đại diện cho người gửi tiền và người vay. Trong đó, người gửi tiền điều chỉnh lượng tiền gửi dựa trên chênh lệch lãi suất huy động của ngân hàng so với mặt bằng thị trường; người vay điều chỉnh nhu cầu tín dụng theo lãi suất cho vay. Ngân hàng xác định lãi suất cho vay dựa trên chi phí vốn có độ trễ và biên lợi nhuận mục tiêu, đồng thời có thể thực hiện điều chỉnh giảm lãi suất khi tuân thủ chỉ đạo của cơ quan quản lý.

Nghiên cứu xem xét ba kịch bản: A – không có chính sách can thiệp bổ sung; B – chỉ đạo giảm lãi suất cho vay; và C – kết hợp chỉ đạo giảm lãi suất cho vay với hạn chế cạnh tranh tăng lãi suất huy động. Các kịch bản được mô phỏng lặp lại với hạt giống ngẫu nhiên được xác định trước nhằm đánh giá sự khác biệt về kết quả và mức độ phân tán giữa các lần chạy.

Các quy tắc hành vi trong mô hình mang tính đơn giản hóa. Một số tham số như hệ số truyền dẫn chi phí vốn, độ nhạy người gửi tiền, độ co giãn nhu cầu tín dụng và áp lực chính sách hiện được thiết lập theo giả định, chưa được hiệu chỉnh đầy đủ bằng kết quả ước lượng thực nghiệm. Đồng thời, các hệ số tăng trưởng cơ sở được áp dụng cho từng quý nhưng chưa được chuyển đổi hoặc kiểm chứng từ dữ liệu hành vi theo tháng. Vì vậy, kết quả cần được diễn giải trong phạm vi cấu trúc và giả định của mô hình.

### 6.2. Kết quả kiểm tra và đối chiếu thực tế

Để đánh giá tính nhất quán của mô hình, nghiên cứu thực hiện các kiểm tra về thời điểm kích hoạt chính sách, chiều phản ứng lãi suất giữa các kịch bản, giới hạn kỹ thuật của các biến trạng thái và khả năng tái lập kết quả khi sử dụng cùng hạt giống ngẫu nhiên.

Bên cạnh đó, cơ chế độ trễ truyền dẫn chi phí vốn được kiểm tra riêng thông qua một cú sốc giả định đối với lãi suất huy động. Kết quả kiểm tra cho thấy lãi suất cho vay không phản ứng ngay tại bước đầu mà thay đổi ở bước tiếp theo, phù hợp với quy tắc sử dụng chi phí vốn trễ được lập trình trong mô hình. Tuy nhiên, kết quả này mới xác nhận tính nhất quán của cơ chế mô phỏng, chưa chứng minh độ trễ truyền dẫn trong thực tế của hệ thống ngân hàng Việt Nam.

Nghiên cứu đồng thời đối chiếu lãi suất cho vay mô phỏng với chuỗi lãi suất bình quân gia quyền theo dư nợ được xây dựng từ dữ liệu của 8 ngân hàng giai đoạn Q2/2023–Q3/2026. Việc đánh giá được thực hiện thông qua biểu đồ so sánh diễn biến lãi suất, chỉ tiêu sai số tuyệt đối trung bình (MAE), căn bậc hai sai số bình phương trung bình (RMSE) và phân tích sai lệch theo từng quý.

Kết quả đối chiếu ban đầu cho thấy mô hình phản ánh được một số chiều hướng biến động, nhưng chưa tái tạo đầy đủ biên độ thay đổi của lãi suất quan sát. Đặc biệt, dữ liệu lịch sử ghi nhận giai đoạn giảm lãi suất tương đối mạnh trong năm 2023–2024 và đầu năm 2025, sau đó phục hồi vào năm 2026, trong khi đường lãi suất mô phỏng biến động trong phạm vi hẹp hơn.

Sự khác biệt này có thể xuất phát từ việc mô hình chưa phản ánh đầy đủ các cú sốc kinh tế vĩ mô, sự thay đổi mặt bằng lãi suất thị trường và các yếu tố điều hành chính sách trong từng giai đoạn. Ngoài ra, các tham số hành vi chưa được hiệu chỉnh thực nghiệm cũng có thể ảnh hưởng đến tốc độ và biên độ phản ứng của lãi suất mô phỏng.

Do đó, kết quả đối chiếu lịch sử chỉ được sử dụng để nhận diện mức độ phù hợp ban đầu và những hạn chế của mô hình, không được xem là bằng chứng xác nhận khả năng dự báo ngoài mẫu.

### 6.3. Hạn chế của mô hình

Thứ nhất, **hạn chế về dữ liệu và tính đại diện của mẫu**. Mô hình sử dụng dữ liệu của 8 ngân hàng thương mại Việt Nam, chưa bao quát toàn bộ hệ thống ngân hàng. Việc phân chia thành ba nhóm chỉ mang tính tương đối trong phạm vi mẫu và không phải hệ thống phân loại chính thức.

Thứ hai, **hạn chế về cấu trúc hành vi tác nhân**. Người gửi tiền và người vay được mô phỏng thông qua các khối hành vi tổng hợp, chưa phản ánh sự khác biệt giữa từng khách hàng về mức độ nhạy cảm với lãi suất, khả năng tiếp cận tín dụng và lựa chọn ngân hàng. Các quy tắc hình thành lãi suất cũng được đơn giản hóa so với thực tế.

Thứ ba, **hạn chế về tham số và hiệu chỉnh mô hình**. Các tham số hiện tại chủ yếu dựa trên giả định và chưa được xác định đầy đủ bằng phương pháp ước lượng từ dữ liệu quan sát. Vì vậy, mức độ phản ứng của các tác nhân và kết quả mô phỏng có thể thay đổi khi sử dụng bộ tham số khác.

Thứ tư, **hạn chế về tần suất và thời điểm chính sách**. Mô hình sử dụng bước thời gian theo quý nên không phản ánh riêng các sự kiện diễn ra trong từng tháng. Việc gộp các mốc chính sách vào một thời điểm kích hoạt có thể làm mất thông tin về sự khác biệt trong thời điểm và tốc độ phản ứng của các ngân hàng.

Thứ năm, **hạn chế về khả năng kiểm chứng thực nghiệm**. Dữ liệu quan sát hiện mới kéo dài đến Q3/2026, trong khi thời điểm can thiệp được giả định từ Q4/2026. Vì vậy, chưa có cơ sở để kiểm chứng tác động chính sách sau thời điểm kích hoạt trong mô hình. Ngoài ra, nghiên cứu chưa thực hiện quy trình hiệu chỉnh và đánh giá ngoài mẫu hoàn chỉnh.

Thứ sáu, **hạn chế về các chỉ tiêu tài chính**. Biến `nim_proxy` chỉ phản ánh chênh lệch giữa lãi suất cho vay và chi phí vốn đại diện trong mô hình, không đồng nhất với tỷ lệ thu nhập lãi cận biên (NIM) được xác định từ báo cáo tài chính. Tương tự, giới hạn dư nợ trên tiền gửi được sử dụng trong mô hình là ràng buộc kỹ thuật, không phải tỷ lệ LDR được xác định theo quy định pháp lý.

### 6.4. Lưu ý khi diễn giải kết quả

Các kết quả từ mô hình cần được diễn giải là phản ứng của hệ thống ngân hàng trong những điều kiện và giả định đã thiết lập, không mặc nhiên phản ánh diễn biến thực tế hoặc tác động nhân quả của chính sách điều hành.

Chênh lệch lãi suất giữa các kịch bản A, B và C thể hiện tác động của việc thay đổi quy tắc chính sách bên trong mô hình. Những kết quả này không đủ để kết luận rằng chính sách thực tế của cơ quan quản lý đã làm thay đổi lãi suất cho vay với mức độ tương ứng.

Khoảng phân vị 5%–95% phản ánh sự phân tán của kết quả giữa các lần chạy mô phỏng, không mặc nhiên là khoảng tin cậy thống kê của lãi suất toàn hệ thống ngân hàng.

Các chỉ tiêu MAE và RMSE được tính từ việc đối chiếu dữ liệu lịch sử với kết quả mô phỏng, chưa phải kết quả kiểm định dự báo ngoài mẫu. Đồng thời, chỉ tiêu lãi suất được xây dựng từ báo cáo tài chính có thể khác với lãi suất cho vay niêm yết hoặc lãi suất áp dụng cho từng khoản vay cụ thể.

Việc điều chỉnh tham số cần dựa trên dữ liệu, căn cứ kinh tế và phương pháp hiệu chỉnh được thống nhất. Không thay đổi tham số chỉ nhằm làm cho kết quả phù hợp với giả thuyết nghiên cứu.

## 7. Hướng mở rộng nghiên cứu

Trên cơ sở những hạn chế đã xác định, nghiên cứu có thể được phát triển theo các hướng sau:

**Thứ nhất, hiệu chỉnh tham số từ dữ liệu thực nghiệm.** Các nghiên cứu tiếp theo có thể sử dụng dữ liệu ngân hàng và phương pháp ước lượng phù hợp để xác định hệ số truyền dẫn chi phí vốn, độ nhạy của người gửi tiền và mức phản ứng của nhu cầu tín dụng đối với lãi suất. Việc hiệu chỉnh cần kết hợp phân chia dữ liệu theo giai đoạn để đánh giá khả năng tái tạo và dự báo ngoài mẫu.

**Thứ hai, bổ sung các yếu tố kinh tế vĩ mô và thị trường tiền tệ.** Mô hình có thể đưa thêm các biến phản ánh lãi suất điều hành, lạm phát, tăng trưởng kinh tế, thanh khoản thị trường và các cú sốc bên ngoài nhằm cải thiện khả năng tái tạo diễn biến lãi suất theo thời gian.

**Thứ ba, mở rộng tính không đồng nhất giữa các tác nhân.** Có thể bổ sung những đặc điểm khác biệt của ngân hàng như quy mô vốn, khả năng thanh khoản, cấu trúc huy động và mức độ cạnh tranh. Khi có dữ liệu vi mô phù hợp, các khối người gửi tiền và người vay có thể được thay thế hoặc mở rộng thành những tác nhân riêng biệt với hành vi khác nhau.

**Thứ tư, hoàn thiện cơ chế mô phỏng chính sách.** Nghiên cứu có thể phân tách những thời điểm can thiệp theo tháng, kiểm tra các độ trễ phản ứng khác nhau và bổ sung cơ chế chính sách điều chỉnh theo trạng thái của hệ thống ngân hàng.

**Thứ năm, mở rộng phân tích độ nhạy và kiểm chứng mô hình.** Ngoài phương pháp thay đổi từng tham số, các nghiên cứu tiếp theo có thể xem xét tương tác đồng thời giữa nhiều tham số, thực hiện kiểm chứng bằng dữ liệu ngoài mẫu và so sánh kết quả mô phỏng giữa các giai đoạn kinh tế khác nhau.

Những hướng mở rộng này nhằm nâng cao tính thực nghiệm và khả năng giải thích của mô hình. Việc triển khai cần căn cứ vào mức độ sẵn có của dữ liệu, thời gian nghiên cứu và sự thống nhất của nhóm.

## 8. Những nội dung cần hoàn thiện trước khi nghiệm thu nghiên cứu

Mặc dù phần kỹ thuật mô phỏng, phân tích kịch bản và đối chiếu lịch sử đã được triển khai, nghiên cứu vẫn cần hoàn thiện một số nội dung trước khi đưa ra kết luận thực nghiệm cuối cùng.

**Đối với TV1 – Huy:** Rà soát và xác nhận các quy tắc hành vi ngân hàng, cơ quan quản lý, thời điểm chính sách và bộ tham số sử dụng. Đồng thời, thống nhất phương pháp hiệu chỉnh và phạm vi kết luận của nghiên cứu.

**Đối với TV2 – Minh:** Xác nhận nguồn gốc và phương pháp xây dựng dữ liệu khởi tạo, chuỗi lãi suất lịch sử và các biến sử dụng trong mô hình; cung cấp kết quả ước lượng tham số và căn cứ lựa chọn giá trị hiệu chỉnh.

**Đối với TV3 – Vũ:** Phối hợp cập nhật cấu hình sau khi bộ tham số được phê duyệt, chạy lại hệ thống mô phỏng A/B/C/D, thực hiện các kiểm tra cần thiết và lưu trữ kết quả cùng cấu hình tương ứng.

Việc nghiệm thu thực nghiệm cuối cùng chỉ nên được thực hiện sau khi bộ tham số, quy tắc hành vi, dữ liệu và kết quả kiểm tra được các thành viên thống nhất.