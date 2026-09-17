# Khảo sát công trình trong nước tương tự đồ án (2026-09-10)

Đồ án: cảnh báo sớm bất thường bơm P29201A (Đạm Cà Mau), học sâu tái tạo (AE/VAE/ED-LSTM) chỉ trên dữ liệu bình thường, 8 kênh proximity probe từ System 1, thang 0-100, đóng góp từng cảm biến.

## Gần nhất về phương pháp

| # | Công trình | Đơn vị / năm | Thiết bị & dữ liệu | Phương pháp | Khác đồ án ở đâu |
|---|---|---|---|---|---|
| 1 | LATS Trần Ngọc Trung, *Nâng cao hiệu quả xử lý khí tự nhiên tại mỏ Hải Thạch* | ĐH Mỏ-Địa chất, 2023 | Giếng khai thác + máy nén khí cao áp (Export Gas Compressor), dữ liệu quá trình Biển Đông POC | Improved LSTM-AE, ngưỡng theo MAE tái tạo, chọn ngưỡng theo F-score; F=0,571, TPR 0,667, FPR 0,0003 | Dữ liệu quá trình (áp suất/lưu lượng), không phải rung; không có đóng góp cảm biến, không thang 0-100, không có "tốc độ dịch chuyển" |
| 2 | EPS (Nguyễn Duy Khánh & cs), *ML phát hiện bất thường máy điện quay* | NMNĐ Vĩnh Tân 2, triển khai 2024 | Quạt khói, dữ liệu PI System | Hồi quy đa biến + Elastic Net, dự đoán nhiệt gối đỡ, so lệch dự đoán/thực | Hồi quy có giám sát 1 biến đích, không phải tái tạo đa kênh; phát hiện trước ngưỡng Alarm tương tự mục tiêu đồ án |
| 3 | Nguyễn Hồ Sĩ Hùng & cs, *Dự đoán RUL máy điện quay dựa trên học sâu* | ĐHBK Đà Nẵng, JST-HAUI 7/2024 | Cảm biến rung gắn máy điện | CNN-LSTM hồi quy RUL | Bài toán RUL có nhãn run-to-failure, không phải phát hiện bất thường không giám sát |

## Cùng lĩnh vực rung động máy quay, khác cách tiếp cận

| # | Công trình | Đơn vị / năm | Ghi chú |
|---|---|---|---|
| 4 | HUST bearing dataset (Nguyễn Đức Thuận, Hoàng Sĩ Hồng) | ĐHBK Hà Nội, BMC Res Notes 2023 | Testbench ổ lăn 6204-6208, 6 loại lỗi, 51,2 kHz; học có giám sát phân loại lỗi |
| 5 | Sáng chế *Quy trình chẩn đoán lỗi ổ trục đa ổ trục bằng tín hiệu rung* (Hoàng Sĩ Hồng) | ĐHBK Hà Nội, 2025 | Hilbert-Huang → ảnh phổ → MobileNet V3 + pruning; có giám sát |
| 6 | Bộ kit thí nghiệm AI chẩn đoán lỗi vòng bi máy điện quay | ĐHBK Hà Nội | Phần cứng + phần mềm đào tạo, dữ liệu gây lỗi chủ động |
| 7 | LVThS *Xây dựng bộ dữ liệu lớn & học sâu chẩn đoán lỗi vòng bi động cơ 3 pha* | (slideshare, đã gỡ) | Testbench, rung + âm thanh, có giám sát |
| 8 | LATS Lại Huy Thiện, *Giám sát rung động động cơ diesel tàu biển* | ĐH Hàng hải, 2020 | Xử lý tín hiệu cổ điển, ngưỡng giới hạn dao động; không dùng ML |
| 9 | ĐHBK TP.HCM, BM Quản lý & Kỹ thuật Bảo trì | — | FFT/Wavelet/Cepstrum/RMS/Kurtosis, hướng CBM truyền thống |

## Nhận định
- Chưa thấy công trình VN công khai nào kết hợp đủ 4 yếu tố của đồ án: (a) học sâu tái tạo chỉ trên dữ liệu bình thường, (b) dữ liệu rung proximity probe đa kênh từ nhà máy thật (System 1), (c) chỉ số 0-100 + đóng góp từng cảm biến, (d) theo dõi tốc độ dịch chuyển.
- Gần nhất là LATS Trần Ngọc Trung (LSTM-AE, dầu khí, dữ liệu thật) — nên trích dẫn ở mục "tình hình trong nước" và đối chiếu.
- EPS/Vĩnh Tân 2 chứng minh nhu cầu "phát hiện trước Alarm" ở nhà máy VN bằng ML trên dữ liệu historian; là bằng chứng thực tiễn hữu ích.
- Đa số nghiên cứu VN về rung động máy quay đi theo hướng phân loại lỗi có giám sát trên testbench (HUST), khác bối cảnh "không có nhãn hỏng" của đồ án.

## Nguồn
- https://humg.edu.vn/content/tintuc/Lists/News/Attachments/8486/ (tóm tắt LATS Trần Ngọc Trung)
- https://dienvadoisong.vn/d/vi-VN/news/Giai-phap-ap-dung-cac-thuat-toan-Machine-learning-nham-phat-hien-cac-bat-thuong-cho-may-dien-quay-60-3569-511377
- https://jst-haui.vn/media/31/uffile-upload-no-title31606.pdf
- https://link.springer.com/article/10.1186/s13104-023-06400-4
- https://hust.edu.vn/vi/nghien-cuu/van-bang-so-huu-tri-tue/quy-trinh-chan-doan-loi-o-truc-cho-da-o-truc-bang-tin-hieu-rung-650272.html
- https://hust.edu.vn/vi/nghien-cuu/khoa-hoc-cong-nghe/bo-kit-thi-nghiem-dao-tao-ve-ung-ai-trong-phan-tich-va-chan-doan-loi-vong-bi-may-dien-quay-650387.html
- http://sdh.vimaru.edu.vn/sites/sdh.vimaru.edu.vn/files/NOI_DUNG_LATS_-_LAI_HUY_THIEN.pdf
- https://fme.hcmut.edu.vn/quan-ly-va-ky-thuat-bao-tri

## Câu hỏi chưa giải quyết
- Chưa truy cập được toàn văn LATS Trần Ngọc Trung (chỉ có tóm tắt); cần xác nhận kiến trúc LSTM-AE và số kênh đầu vào.
- Nhiều khoá luận tốt nghiệp ĐH không công bố online, có thể tồn tại đề tài tương tự chưa lập chỉ mục.
