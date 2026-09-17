# MẪU BÁO CÁO TUẦN — ĐỒ ÁN HQC_Aware-Forecasting

**Đề tài:** Nghiên cứu và xây dựng hệ thống cảnh báo sớm bất thường thiết bị quay
ứng dụng học sâu tái tạo, triển khai trên máy tính nhúng
**GVHD:** ThS. Phan Đình Duy
**Thời gian thực hiện:** 03/08/2026 – 06/09/2026

**Thành viên thực hiện:**

| STT | Họ và tên | MSSV | Vai trò |
|---|---|---|---|
| 1 | Trương Ngọc Sơn | 25210183 | Điều phối, Tài liệu, Dữ liệu & Gán nhãn |
| 2 | Trần Tín Nghĩa | 25210147 | Huấn luyện & Tối ưu mô hình |
| 3 | Hồ Thị Mỹ Phương | 25210170 | Đánh giá, Kiểm thử, Triển khai thời gian thực & IoT |

---

# BÁO CÁO TUẦN 1 — Khởi động & Nghiên cứu
**Thời gian:** 03/08/2026 – 09/08/2026

## 1. Nội dung công việc trong tuần

Chốt yêu cầu và phạm vi đề tài; nghiên cứu cơ sở lý thuyết gồm học sâu tái tạo cho phát hiện bất
thường, thống kê điều khiển quá trình đa biến và cơ sở chẩn đoán rung động máy quay; khảo sát
nguồn dữ liệu giám sát tình trạng của nhà máy và chọn tập dữ liệu; chọn nền tảng phần cứng cho
phần triển khai nhúng; hoàn thiện đề cương chi tiết.

## 2. Phân công thực hiện

**Trương Ngọc Sơn:**
- Khảo sát nguồn dữ liệu của nhà máy: liệt kê các điểm đo có sẵn trên máy P29201A, xác định độ
  sâu lưu trữ từng điểm đo.
- Xác định đúng thuộc tính giá trị đo cần kéo (hệ có thuộc tính khác biểu diễn phần trăm tiệm cận
  ngưỡng cảnh báo, không phải giá trị thật).
- Trích xuất mẫu dữ liệu thử để kiểm định dạng và chu kỳ lấy mẫu thật.
- Viết đề cương chi tiết; tổng hợp báo cáo tuần.

**Trần Tín Nghĩa:**
- Đọc và tóm tắt công trình tham chiếu về giám sát sức khỏe thiết bị bằng học sâu tái tạo (lấy từ
  bản gốc của nhà xuất bản).
- Nghiên cứu lý thuyết thống kê điều khiển quá trình đa biến: thống kê sai số dự đoán bình phương,
  khoảng cách Mahalanobis và cách tính giới hạn kiểm soát.
- Dựng khung mã huấn luyện; chuẩn bị các kiến trúc sẽ so sánh.

**Hồ Thị Mỹ Phương:**
- Nghiên cứu cơ sở chẩn đoán rung động máy quay: quan hệ giữa phân bố năng lượng theo bậc vòng
  quay và dạng hư hỏng cơ khí.
- Khảo sát cách đọc dữ liệu từ hệ giám sát của nhà máy và phương án kết nối.
- Chọn nền tảng phần cứng nhúng; vẽ sơ đồ khối hệ thống.

## 3. Báo cáo quá trình thực hiện

### 3.1. Đánh giá mức độ hoàn thành

| Nhiệm vụ tuần 1 | Mức hoàn thành | Ghi chú |
|---|---|---|
| Chốt yêu cầu và phạm vi đề tài | **100%** | Mục tiêu, đối tượng, phạm vi (kèm phần ngoài phạm vi) đã viết trong đề cương |
| Nghiên cứu cơ sở lý thuyết | **100%** | Đã đọc sâu công trình tham chiếu từ bản gốc nhà xuất bản; đã nghiên cứu thống kê điều khiển quá trình đa biến và cơ sở chẩn đoán rung động |
| Khảo sát nguồn dữ liệu, chọn tập dữ liệu | **100%** | Đã khảo sát 10 nguồn, xác định được ràng buộc lưu trữ của hệ và chọn được ba nguồn dùng được |
| Chọn nền tảng phần cứng | **100%** | Chọn máy tính nhúng Raspberry Pi, có lý do kỹ thuật (tích hợp mạng, không phải do năng lực tính toán) |
| Viết đề cương chi tiết | **100%** | Đủ 7 phần theo mẫu đăng ký |
| Vẽ sơ đồ khối hệ thống | **70%** | Đã mô tả bằng văn bản trong báo cáo; còn phải vẽ thành hình chuẩn |
| **Tổng thể tuần 1** | **≈ 95%** | Hoàn thành mục tiêu tuần; chỉ còn sơ đồ khối chưa vẽ thành hình |

### 3.2. Đã hoàn thành

**Về nghiên cứu lý thuyết:**
- Xác định được **công trình tham chiếu chính**: bài báo về giám sát sức khỏe máy nén bằng học sâu
  tái tạo (tạp chí *Entropy*, 2021), lấy được **bản gốc PDF của nhà xuất bản** để bảo đảm tính
  chính xác khi trích dẫn.
- Rút được từ công trình đó bốn nội dung dùng trực tiếp: công thức sai số tái tạo, cách so sánh
  các kiến trúc tái tạo, kỹ thuật quy đổi điểm bất thường về thang 0–100, và kỹ thuật đóng góp
  từng cảm biến để giải thích cảnh báo.
- Ghi nhận một **cảnh báo quan trọng** từ phần thảo luận của công trình: tối ưu siêu tham số quá
  mạnh khiến mô hình học sao chép đầu vào sang đầu ra, tái tạo tốt cả dữ liệu lỗi và mất hẳn tín
  hiệu phát hiện. Cảnh báo này quyết định tiêu chí chọn mô hình ở tuần 3.
- Nghiên cứu lý thuyết thống kê điều khiển quá trình đa biến và bảng quy tắc chẩn đoán rung động
  máy quay theo tiêu chuẩn ngành.

**Về khảo sát dữ liệu:**
- Khảo sát nguồn dữ liệu giám sát tình trạng của máy P29201A; xác định được **ràng buộc quan trọng
  của hệ**: các cảm biến giám sát tình trạng chỉ lưu giá trị thật ở độ phân giải cao trong khoảng
  ngắn gần đây, còn lịch sử dài chỉ giữ thuộc tính phần trăm tiệm cận ngưỡng cảnh báo — không phải
  giá trị đo. Phát hiện này định hình lại phạm vi dữ liệu của đề tài.
- Chọn được ba nguồn dùng được: chuỗi rung (biên độ và pha thành phần 1X) độ sâu 180 ngày, chuỗi
  biến quá trình độ sâu 1 năm, và các khối dữ liệu độ phân giải cao dùng cho phân tích chẩn đoán.

**Về phần cứng:**
- Chọn **máy tính nhúng Raspberry Pi** đặt trong tủ điện cạnh thiết bị. Lý do là **tích hợp**, không
  phải năng lực tính toán: nền tảng này có ngăn xếp mạng đầy đủ để đọc dữ liệu từ hệ giám sát và
  lưu đệm được khi mất kết nối.

**Về tài liệu:**
- Hoàn thành **đề cương chi tiết** gồm 7 phần: tổng quan, mục tiêu, đối tượng, phạm vi, phương pháp
  thực hiện, kết quả mong đợi, kế hoạch và phân công.
- Dựng **khung báo cáo đồ án** theo đúng khung 5 chương của mẫu môn học, đánh dấu rõ các mục còn
  chờ dữ liệu kèm điều kiện hoàn thành.

### 3.3. Kết quả cụ thể

| Sản phẩm | Nội dung |
|---|---|
| Đề cương chi tiết | 7 phần theo mẫu đăng ký, kèm bảng tiến độ 5 tuần và phân công 3 thành viên |
| Bản thảo báo cáo đồ án | 5 chương theo mẫu, các mục chờ dữ liệu đã đánh dấu kèm điều kiện hoàn thành |
| Ghi chú công trình tham chiếu | Rút các công thức và kỹ thuật dùng được, kèm cảnh báo về tối ưu quá mức |
| Bản gốc PDF công trình tham chiếu | Bản chính thức của nhà xuất bản, dùng làm nguồn trích dẫn |
| Danh sách dữ liệu cần kéo | Phân tầng theo ưu tiên, ghi rõ các bẫy khi trích xuất |

### 3.4. Vướng mắc và cách xử lý

| Vướng mắc | Cách xử lý |
|---|---|
| Không tải được bản gốc PDF công trình tham chiếu từ môi trường làm việc (trang nhà xuất bản chặn truy cập tự động) | Tải trực tiếp từ máy cá nhân. Bản do công cụ tự trích xuất **không dùng** làm nguồn trích dẫn vì không bảo đảm nguyên văn |
| Hệ lưu trữ không giữ giá trị thật của cảm biến rung trong lịch sử dài — thử trích xuất nhiều lần với nhiều khoảng thời gian đều chỉ nhận được thuộc tính phần trăm tiệm cận ngưỡng | Xác nhận đây là **ràng buộc của hệ**, không phải lỗi thao tác. Điều chỉnh thiết kế theo thực tế: dùng chuỗi rung 180 ngày cho trục early-warning, biến quá trình làm cổng lọc trạng thái, và các khối độ phân giải cao cho phân tích chẩn đoán |
| Một tệp trích xuất bị lỗi (mỗi điểm đo chỉ có một giá trị, có mốc thời gian trong tương lai) | Loại bỏ, không dùng; trích xuất lại với khoảng thời gian và bước lấy mẫu khác |
| Chưa có nhật ký bảo trì để làm mốc đối chiếu | Tìm được phương án thay thế: hệ lưu số giờ chạy kể từ lần bảo trì gần nhất, mỗi lần giá trị này về không tương ứng một lần can thiệp — dùng làm mốc nghiệm thu. Đã đưa vào danh sách dữ liệu cần kéo ở mức ưu tiên cao nhất |

## 4. Dự kiến công việc tuần tiếp theo

Trích xuất và làm sạch dữ liệu; xác định cửa sổ nền bằng phương pháp quét độ dốc; hợp nhất dữ
liệu rung và biến quá trình về lưới thời gian chung; xây tập huấn luyện và tập đánh giá; viết
hướng dẫn gán nhãn và chuyển chuyên gia bảo trì dự đoán.

**Việc chuyển tiếp từ tuần 1:** vẽ sơ đồ khối hệ thống thành hình chuẩn (Phương).

**Cần chốt trước khi sang tuần 2:** định dạng bộ dữ liệu giữa Sơn và Nghĩa — thứ tự cột đặc trưng,
cách mã hóa pha thành cặp sin–cos, đơn vị, quy ước ô khuyết.

---

# BÁO CÁO TUẦN 2 — Dữ liệu & Đặc trưng
**Thời gian:** 10/08/2026 – 16/08/2026

## 1. Nội dung công việc trong tuần

Trích xuất dữ liệu từ hệ lưu trữ của nhà máy; xây quy trình làm sạch và cổng lọc trạng thái vận
hành; xác định cửa sổ nền; hợp nhất dữ liệu rung và biến quá trình về một lưới thời gian chung;
xây tập huấn luyện (không nhãn) và tập đánh giá; viết hướng dẫn gán nhãn và chuyển chuyên gia.

## 2. Phân công thực hiện

**Trương Ngọc Sơn:**
- Trích xuất dữ liệu; lập tài liệu ghi rõ điểm đo, khoảng thời gian và bước lấy mẫu.
- Xây quy trình làm sạch: loại giá trị đặc biệt biểu thị lỗi cảm biến, loại giá trị rác dạng số
  cực nhỏ, lọc bản ghi trùng, áp giới hạn vật lý theo từng loại cảm biến.
- Xử lý đại lượng góc bằng công thức thống kê vòng tròn; chuyển pha thành cặp sin–cos.
- Áp cổng lọc trạng thái vận hành; hợp nhất về lưới thời gian chung.
- Xác định cửa sổ nền bằng quét độ dốc; kiểm độ dốc và mức ý nghĩa thống kê từng kênh.
- Xây tập huấn luyện và tập đánh giá; sinh nhãn ứng viên bằng thống kê mô tả trên dữ liệu thô.
- Viết hướng dẫn gán nhãn bằng ngôn ngữ chẩn đoán rung; điền ví dụ mẫu; chuyển chuyên gia.

**Trần Tín Nghĩa:**
- Nhận bộ dữ liệu theo định dạng đã chốt; kiểm tính hợp lệ trước khi huấn luyện.
- Huấn luyện các kiến trúc tái tạo trên cửa sổ nền, chia dữ liệu theo khối thời gian.
- Chạy đường cong học chọn kích thước mô hình; kiểm cửa sổ kiểm định vẫn thuần khỏe.
- Tính giới hạn kiểm soát thống kê mức tin cậy 99%.

**Hồ Thị Mỹ Phương:**
- Hỗ trợ trích xuất dữ liệu từ hệ giám sát.
- Thiết kế lược đồ cơ sở dữ liệu lưu chuỗi thời gian, kết quả suy luận và lịch sử cảnh báo.
- Chuẩn bị môi trường trên máy tính nhúng.

## 3. Báo cáo quá trình thực hiện

### 3.1. Đánh giá mức độ hoàn thành

| Nhiệm vụ trong tuần | Mức hoàn thành | Ghi chú |
|---|---|---|
| … | …% | … |
| … | …% | … |
| **Tổng thể tuần** | **…%** | … |

### 3.2. Đã hoàn thành

*(Nêu theo nhóm việc — mỗi việc ghi rõ đã làm được đến đâu, không viết chung chung)*
- …

### 3.3. Kết quả cụ thể

| Sản phẩm | Nội dung |
|---|---|
| … | … |

### 3.4. Vướng mắc và cách xử lý

| Vướng mắc | Cách xử lý |
|---|---|
| … | … |

## 4. Dự kiến công việc tuần tiếp theo

Hoàn thiện lớp phát hiện và lớp giải thích; thực nghiệm các phương án lượng tử hóa và chốt phương
án; bắt đầu sinh mã C cho thiết bị nhúng.

**Cần chốt trước khi sang tuần 3:** định dạng tham số mô hình giữa Nghĩa và Phương — thứ tự các
mảng, kiểu số của từng mảng, cách lưu hệ số tỉ lệ. Và định dạng nhãn chuyên gia giữa Sơn với hai
thành viên còn lại — tên cột, mã giá trị nhãn, cách xử lý dòng chuyên gia để trống.

---

# BÁO CÁO TUẦN 3 — Huấn luyện & Tối ưu mô hình
**Thời gian:** 17/08/2026 – 23/08/2026

## 1. Nội dung công việc trong tuần

Hoàn thiện lớp phát hiện (hai thống kê kiểm soát) và lớp giải thích (điểm sức khỏe, đóng góp từng
đầu đo); thực nghiệm nhiều phương án lượng tử hóa và so sánh trên bộ ba chỉ số; sinh mã C thuần và
kiểm chứng tính đúng đắn; bắt đầu triển khai lên máy tính nhúng.

## 2. Phân công thực hiện

**Trương Ngọc Sơn:**
- Theo dõi tiến trình gán nhãn của chuyên gia.
- Viết mục tổng quan nghiên cứu trong nước.
- Rà soát tính nhất quán số liệu giữa các chương của báo cáo.

**Trần Tín Nghĩa:**
- Xây điểm sức khỏe 0–100, hiệu chỉnh trên thang logarit của sai số ở giai đoạn kiểm định khỏe.
- Xây lớp đóng góp từng đầu đo.
- Kiểm độ nhạy kết quả theo số thành phần của mô hình.
- Thực nghiệm các phương án lượng tử hóa: số nguyên 8 bit và 4 bit, một hệ số tỉ lệ cho cả mảng
  so với từng hàng, số thực 16 bit; so sánh trên bộ ba chỉ số (bộ nhớ, khả năng xếp hạng, sai lệch
  giá trị tuyệt đối); xử lý riêng tham số ở mẫu số và tham số có dải động rộng.
- Chốt phương án và giao định dạng tham số cho Phương.

**Hồ Thị Mỹ Phương:**
- Sinh mã C thuần từ tham số mô hình đã nén; kiểm chứng khớp với bản gốc trên cùng dữ liệu vào.
- Thêm tầng ngưỡng kiểm soát vào mã để hệ ra quyết định báo động, không chỉ trả về con số.
- Viết chương trình đọc dữ liệu và suy luận theo chu kỳ trên máy tính nhúng.
- Biên dịch chéo cho kiến trúc đích.

## 3. Báo cáo quá trình thực hiện

### 3.1. Đánh giá mức độ hoàn thành

| Nhiệm vụ trong tuần | Mức hoàn thành | Ghi chú |
|---|---|---|
| … | …% | … |
| … | …% | … |
| **Tổng thể tuần** | **…%** | … |

### 3.2. Đã hoàn thành

*(Nêu theo nhóm việc — mỗi việc ghi rõ đã làm được đến đâu, không viết chung chung)*
- …

### 3.3. Kết quả cụ thể

| Sản phẩm | Nội dung |
|---|---|
| … | … |

### 3.4. Vướng mắc và cách xử lý

| Vướng mắc | Cách xử lý |
|---|---|
| … | … |

## 4. Dự kiến công việc tuần tiếp theo

Đo tài nguyên trên thiết bị (bộ nhớ, độ trễ, điện năng); kiểm tra hoạt động liên tục và xử lý tình
huống lỗi; nhận tập đánh giá từ chuyên gia và tính các chỉ số theo nhãn chuyên gia.

**Cần chốt trước khi sang tuần 4:** giá trị giới hạn kiểm soát và biên ba vùng của điểm sức khỏe,
giữa Nghĩa và Phương.

---

# BÁO CÁO TUẦN 4 — Triển khai & Kiểm thử
**Thời gian:** 24/08/2026 – 30/08/2026

## 1. Nội dung công việc trong tuần

Đo tài nguyên trên thiết bị nhúng; kiểm tra hoạt động liên tục và các tình huống lỗi; nhận tập
đánh giá từ chuyên gia và tính lại các chỉ số theo nhãn chuyên gia; kiểm tra và sửa lỗi toàn hệ.

## 2. Phân công thực hiện

**Trương Ngọc Sơn:**
- Nhận tập đánh giá đã xác nhận từ chuyên gia bảo trì dự đoán.
- Tính tỉ lệ chuyên gia sửa nhãn ứng viên — chỉ số minh bạch bắt buộc báo cáo.
- Đối chiếu các trường hợp chuyên gia bác nhãn để rút nhận xét về điểm yếu của luật sinh nhãn.

**Trần Tín Nghĩa:**
- Tính lại các chỉ số đánh giá theo nhãn chuyên gia (thay nhãn ứng viên).
- Phân tích các trường hợp mô hình và chuyên gia bất đồng.
- Viết mục kết quả về so sánh kiến trúc và lượng tử hóa.

**Hồ Thị Mỹ Phương:**
- Đo tài nguyên trên thiết bị: bộ nhớ chương trình, bộ nhớ làm việc, độ trễ suy luận, điện năng.
- Kiểm tra hoạt động liên tục và xử lý tình huống lỗi: mất kết nối, dữ liệu khuyết, thiết bị dừng;
  kiểm phương án lưu đệm khi mất kết nối.
- Kiểm tra và sửa lỗi chương trình giám sát.

## 3. Báo cáo quá trình thực hiện

### 3.1. Đánh giá mức độ hoàn thành

| Nhiệm vụ trong tuần | Mức hoàn thành | Ghi chú |
|---|---|---|
| … | …% | … |
| … | …% | … |
| **Tổng thể tuần** | **…%** | … |

### 3.2. Đã hoàn thành

*(Nêu theo nhóm việc — mỗi việc ghi rõ đã làm được đến đâu, không viết chung chung)*
- …

### 3.3. Kết quả cụ thể

| Sản phẩm | Nội dung |
|---|---|
| … | … |

### 3.4. Vướng mắc và cách xử lý

| Vướng mắc | Cách xử lý |
|---|---|
| … | … |

## 4. Dự kiến công việc tuần tiếp theo

Hoàn thiện báo cáo đồ án (danh mục hình, bảng, từ viết tắt, tài liệu tham khảo chuẩn IEEE); viết
mục kết luận và đối chiếu kết quả với mục tiêu; chuẩn bị slide và bản trình diễn chạy thật.

---

# BÁO CÁO TUẦN 5 — Đánh giá & Hoàn thiện
**Thời gian:** 31/08/2026 – 06/09/2026 · **Nộp 06/09/2026**

## 1. Nội dung công việc trong tuần

Hoàn thiện báo cáo đồ án; viết mục kết luận và đối chiếu kết quả với mục tiêu và chỉ tiêu đề ra;
rà soát toàn bộ số liệu; chuẩn bị slide báo cáo và bản trình diễn chạy thật trên thiết bị.

## 2. Phân công thực hiện

**Trương Ngọc Sơn:**
- Hoàn thiện báo cáo: danh mục hình, danh mục bảng, danh mục từ viết tắt, tóm tắt đồ án, mở đầu.
- Chuẩn hóa tài liệu tham khảo theo chuẩn IEEE.
- Rà soát lần cuối tính nhất quán giữa các chương.

**Trần Tín Nghĩa:**
- Viết mục kết luận phần mô hình và tối ưu.
- Rà lại mọi con số ở các chương thiết kế và kết quả, đối chiếu với sản phẩm gốc.

**Hồ Thị Mỹ Phương:**
- Viết mục kết luận phần triển khai và kiểm thử.
- Chuẩn bị slide báo cáo theo mẫu.
- Chuẩn bị bản trình diễn chạy thật trên thiết bị nhúng cho buổi báo cáo.

## 3. Báo cáo quá trình thực hiện

### 3.1. Đánh giá mức độ hoàn thành

| Nhiệm vụ trong tuần | Mức hoàn thành | Ghi chú |
|---|---|---|
| … | …% | … |
| … | …% | … |
| **Tổng thể tuần** | **…%** | … |

### 3.2. Đã hoàn thành

*(Nêu theo nhóm việc — mỗi việc ghi rõ đã làm được đến đâu, không viết chung chung)*
- …

### 3.3. Kết quả cụ thể

| Sản phẩm | Nội dung |
|---|---|
| … | … |

### 3.4. Vướng mắc và cách xử lý

| Vướng mắc | Cách xử lý |
|---|---|
| … | … |

## 4. Dự kiến công việc tuần tiếp theo

Bảo vệ đồ án. Nếu còn thời gian cải tiến: đo điện năng đầy đủ trên board thật; mở rộng sang máy
thứ hai trong cụm để kiểm tính tổng quát của phương pháp.
