# ĐỀ CƯƠNG CHI TIẾT — NỘI DUNG ĐỀ TÀI

**Tên đề tài:** Nghiên cứu và xây dựng hệ thống cảnh báo sớm bất thường thiết bị quay
ứng dụng học sâu tái tạo, triển khai trên máy tính nhúng

**Tên tiếng Anh:** Research and Development of an Early-Warning System for Rotating Machinery
Anomalies using Reconstruction-based Deep Learning with Embedded Deployment

**Cán bộ hướng dẫn:** ThS. Phan Đình Duy

---

## 1. TỔNG QUAN ĐỀ TÀI

Thiết bị quay — bơm, máy nén, tua-bin — là nhóm tài sản có tần suất hư hỏng cao và hậu quả
dừng máy lớn nhất trong nhà máy hóa chất và lọc hóa dầu. Các nhà máy hiện đại đều đã lắp hệ
giám sát rung và nhiệt liên tục, sinh ra khối lượng dữ liệu rất lớn. Tuy nhiên dữ liệu này
phần lớn chỉ được dùng theo cách đơn giản nhất: **so sánh với một ngưỡng cảnh báo cố định**.

Cách làm đó có ba hạn chế thực tế. **Thứ nhất, phát hiện muộn** — ngưỡng được đặt đủ cao để
tránh báo động giả, nên khi giá trị chạm ngưỡng thì hư hỏng đã tiến triển đáng kể. **Thứ hai,
không có dữ liệu hỏng có nhãn** — thiết bị được bảo trì phòng ngừa nên rất ít khi chạy tới
hỏng thật, khiến các phương pháp học có giám sát không áp dụng được. **Thứ ba, thay đổi do
tải bị lẫn với thay đổi do suy giảm** — biên độ rung phụ thuộc tải, và một hệ không phân biệt
được hai nguyên nhân này sẽ báo động mỗi khi máy đổi chế độ, dẫn tới việc người vận hành tắt
báo động.

Đề tài đặt vấn đề theo hướng khác: thay vì hỏi *"giá trị đã vượt ngưỡng chưa?"*, hỏi *"hành vi
hiện tại có còn giống hành vi lúc thiết bị khỏe không?"*. Câu hỏi thứ hai phát hiện được
**thay đổi trong tương quan giữa các cảm biến** — thường xuất hiện sớm hơn việc một con số
đơn lẻ vượt ngưỡng.

Hướng tiếp cận là **học không giám sát dựa trên tái tạo**: mô hình chỉ học đặc trưng của giai
đoạn thiết bị vận hành bình thường, sau đó sai số tái tạo trở thành chỉ số bất thường. Vì chỉ
cần dữ liệu bình thường để huấn luyện, hướng này giải được đúng vấn đề thứ hai ở trên.

Đề tài được thực hiện trên dữ liệu thật của máy bơm cấp nước cao áp **P29201A** (tổ tua-bin
hơi dẫn động + bơm) tại một nhà máy đạm, trích xuất từ hệ lưu trữ dữ liệu quá trình của nhà
máy. Đồng thời, mô hình sau khi huấn luyện được nén và triển khai lên **máy tính nhúng** đặt
cạnh thiết bị — đáp ứng đầy đủ quy trình thiết kế trí tuệ nhân tạo cho hệ thống nhúng.

---

## 2. MỤC TIÊU

### 2.1. Mục tiêu tổng quát

Xây dựng thành công một hệ thống phát hiện sớm trạng thái bất thường có khả năng dẫn tới hư
hỏng trên thiết bị quay, với hai đặc tính cốt lõi: **huấn luyện không cần dữ liệu hỏng có
nhãn**, và **đủ gọn để suy luận ngay trên thiết bị nhúng đặt cạnh máy** thay vì phụ thuộc máy
chủ trung tâm.

### 2.2. Mục tiêu cụ thể

1. **Xây dựng quy trình thu thập và làm sạch dữ liệu** giám sát tình trạng từ hệ lưu trữ dữ
   liệu quá trình của nhà máy: hợp nhất dữ liệu rung và biến quá trình về một trục thời gian
   chung, xử lý các dạng dữ liệu rác đặc thù của hệ công nghiệp, và nhận biết trạng thái vận
   hành để loại giai đoạn thiết bị dừng.

2. **Huấn luyện mô hình tái tạo chỉ trên giai đoạn thiết bị vận hành bình thường**, so sánh
   các kiến trúc từ tuyến tính (phân tích thành phần chính) tới phi tuyến (autoencoder,
   autoencoder biến phân), và chọn kích thước mô hình bằng bằng chứng thực nghiệm.

3. **Thay ngưỡng cảnh báo chỉnh tay bằng giới hạn kiểm soát thống kê** có mức tin cậy xác
   định trước, theo lý thuyết điều khiển quá trình đa biến.

4. **Xây dựng lớp giải thích được**: quy đổi sai số tái tạo thành điểm sức khỏe thang 0–100
   dễ đọc cho người vận hành, và chỉ ra đầu đo nào đóng góp nhiều nhất vào chỉ số bất thường
   để khoanh vùng bộ phận nghi có vấn đề.

5. **Nén mô hình về số nguyên 8 bit, sinh mã C và triển khai lên máy tính nhúng**, đo tài
   nguyên thực tế: bộ nhớ chiếm dụng, độ trễ suy luận và điện năng tiêu thụ.

6. **Nghiệm thu bằng tập đánh giá do chuyên gia bảo trì dự đoán xác nhận nhãn**, kèm chỉ số
   minh bạch về tỉ lệ chuyên gia sửa nhãn ứng viên.

---

## 3. ĐỐI TƯỢNG NGHIÊN CỨU

### 3.1. Đối tượng vật lý

Máy bơm cấp nước cao áp **P29201A**, gồm hai hệ con: tua-bin hơi dẫn động và bơm. Thiết bị có
**4 ổ đỡ**, mỗi ổ gắn hai đầu đo dịch chuyển kiểu tiệm cận lệch nhau 90° (ký hiệu hướng X và
hướng Y), tổng **8 kênh đo rung**. Ngoài ra có các đầu đo nhiệt độ ổ đỡ và đầu đo vị trí dọc
trục.

Thiết bị này nằm trong một cụm gồm 5 máy quay, trong đó có **2 cặp máy song song cùng loại** —
điều kiện thuận lợi cho việc đối chứng ở giai đoạn mở rộng.

### 3.2. Đối tượng dữ liệu

- **Hệ lưu trữ dữ liệu quá trình của nhà máy**, truy xuất qua công cụ bảng tính chuyên dụng.
- **Hệ giám sát rung chuyên dụng**, cung cấp sẵn biên độ và pha của thành phần tần số quay
  cơ bản (thành phần 1X) — tức hệ đã thực hiện phép biến đổi phổ, không cần xử lý tín hiệu thô.
- Các đại lượng sử dụng: **biên độ 1X** và **pha 1X** của 8 đầu đo (đầu vào mô hình), cùng
  **11 biến quá trình** (tốc độ, lưu lượng, áp suất, mức, nhiệt độ quá trình — dùng làm cổng
  lọc trạng thái).

### 3.3. Đối tượng phương pháp

- **Mô hình tái tạo**: phân tích thành phần chính, autoencoder, autoencoder biến phân.
- **Thống kê điều khiển quá trình đa biến**: thống kê sai số dự đoán bình phương với giới hạn
  kiểm soát theo phương pháp khớp mô-men, và thống kê khoảng cách Mahalanobis.
- **Cơ sở chẩn đoán rung động máy quay**: quan hệ giữa phân bố năng lượng theo bậc vòng quay
  và dạng hư hỏng cơ khí, theo tiêu chuẩn ngành.
- **Kỹ thuật nén mô hình cho thiết bị biên**: lượng tử hóa số nguyên 8 bit.

### 3.4. Đối tượng phần cứng triển khai

Máy tính nhúng **Raspberry Pi** đặt trong tủ điện cạnh thiết bị, đọc dữ liệu từ hệ giám sát
qua mạng nhà máy và chạy suy luận tại chỗ.

---

## 4. PHẠM VI NGHIÊN CỨU

### 4.1. Phạm vi thiết bị

Tập trung vào **một máy** (P29201A). Bốn máy còn lại trong cụm chỉ dùng để đối chứng và xác
định mốc bảo trì, không huấn luyện mô hình riêng.

### 4.2. Phạm vi thời gian dữ liệu

| Loại dữ liệu | Khoảng thời gian | Bước lấy mẫu |
|---|---|---|
| Rung (biên độ + pha 1X) | 180 ngày (05/02/2026 – 04/08/2026) | 1 giờ |
| Biến quá trình | 1 năm (01/08/2025 – 01/08/2026) | 10 phút |

Sau khi hợp nhất về lưới 1 giờ và áp cổng lọc trạng thái vận hành, khối lượng dữ liệu dùng
được là **3.801 giờ**.

### 4.3. Phạm vi đại lượng đo

Giới hạn ở **thành phần 1X** (một lần mỗi vòng quay). Hệ giám sát của nhà máy chỉ trích sẵn
thành phần này; các bậc khác (2X, dưới đồng bộ) không có trong dữ liệu. Hệ quả về phạm vi
chẩn đoán: phân biệt được **mất cân bằng** — dạng hư hỏng thể hiện qua thành phần 1X — nhưng
chưa phân biệt được với **lệch trục** (cần thành phần 2X để so sánh tỉ lệ).

### 4.4. Phạm vi bài toán

- **Có trong phạm vi:** phát hiện *thay đổi* so với trạng thái nền của thiết bị; khoanh vùng
  đầu đo/ổ đỡ có bất thường; quy đổi thành điểm sức khỏe và phiếu việc bảo trì.
- **Ngoài phạm vi:** dự báo *thời điểm hỏng* cụ thể (cần nhiều ca chạy-đến-hỏng); phát hiện
  *mức tuyệt đối xấu* có sẵn từ đầu (cần tầng đối chiếu tiêu chuẩn ngành, xem mục 5.6).

### 4.5. Phạm vi triển khai

Dừng ở mức chứng minh khả thi: mô hình đã nén, mã suy luận đã kiểm chứng, tài nguyên đã đo.
**Không** bao gồm lắp đặt vận hành lâu dài tại hiện trường và theo dõi hiệu quả thực tế.

---

## 5. PHƯƠNG PHÁP THỰC HIỆN

### 5.1. Phương pháp nghiên cứu tài liệu

Tìm hiểu và đọc sâu công trình tham chiếu về giám sát sức khỏe thiết bị bằng học sâu tái tạo,
lấy từ bản gốc của nhà xuất bản để đảm bảo tính chính xác khi trích dẫn. Nghiên cứu lý thuyết
điều khiển quá trình đa biến, cơ sở chẩn đoán rung động máy quay theo tiêu chuẩn ngành, và
tài liệu về nén mô hình cho thiết bị biên.

**Nguyên tắc áp dụng xuyên suốt:** mọi thành phần đưa vào hệ thống — kể cả các đường cơ sở
đơn giản — đều phải truy được nguồn gốc phương pháp, không tự đặt ra.

### 5.2. Phương pháp xử lý dữ liệu

Truy xuất dữ liệu từ hệ lưu trữ của nhà máy, lưu ý chọn đúng thuộc tính giá trị đo (hệ có
thuộc tính khác biểu diễn phần trăm tiệm cận ngưỡng cảnh báo, không phải giá trị thật).

Quy trình làm sạch gồm: loại giá trị rác dạng số cực nhỏ và dạng không, loại giá trị đặc biệt
biểu thị lỗi cảm biến, lọc bản ghi trùng. Việc kiểm tra chất lượng phải quét **toàn khoảng
thời gian** — kiểm trên cửa sổ gần nhất không phát hiện được rác ở dữ liệu cũ.

Xử lý riêng cho **đại lượng góc**: pha phải dùng công thức thống kê vòng tròn, và khi đưa vào
mô hình phải chuyển thành cặp sin–cos vì 359° và 1° gần nhau về vật lý.

**Cổng lọc trạng thái vận hành:** chỉ giữ các giờ thiết bị đang chạy có tải, xác định bằng
ngưỡng biên độ rung tối thiểu và ngưỡng lưu lượng.

### 5.3. Phương pháp xác định cửa sổ nền

Đây là bước có ảnh hưởng lớn nhất tới kết quả, và cần phương pháp có nguyên tắc thay vì lấy
"đoạn đầu chuỗi": **quét mọi cửa sổ 30 ngày với bước 5 ngày, chạy hồi quy tuyến tính từng
kênh trên mỗi cửa sổ, chọn cửa sổ có độ dốc nhỏ nhất**. Kiểm bắt buộc trước khi gọi một cửa
sổ là nền: độ dốc và mức ý nghĩa thống kê của từng kênh, không chỉ so đầu–cuối.

Lý do bước này quan trọng: một cửa sổ "trông hợp lý" vẫn có thể đang chứa một đợt suy giảm
đang diễn ra. Nếu huấn luyện trên nền bị nhiễm, mô hình sẽ học luôn hướng bất thường và mất
khả năng phát hiện chính hiện tượng đó.

### 5.4. Phương pháp huấn luyện và chọn mô hình

**Huấn luyện không giám sát** trên cửa sổ nền, không có cột nhãn. Chia dữ liệu **theo khối
thời gian**, không xáo trộn ngẫu nhiên — vì đây là chuỗi thời gian, xáo trộn sẽ làm rò rỉ
thông tin.

Chọn kích thước mô hình bằng **đường cong học**: huấn luyện trên lượng dữ liệu tăng dần với
phần kiểm định giữ riêng, so sai số huấn luyện với sai số kiểm định. Đây là bằng chứng thực
nghiệm, thay cho quy tắc kinh nghiệm về tỉ lệ mẫu trên tham số.

**Tiêu chí chọn mô hình có hai vế, không phải một.** Sai số tái tạo nhỏ nhất **không** phải
tiêu chí duy nhất — công trình tham chiếu cảnh báo rằng tối ưu quá mạnh khiến mô hình học
"sao chép" đầu vào sang đầu ra, khi đó nó tái tạo tốt cả dữ liệu bình thường lẫn dữ liệu lỗi
và mất hẳn tín hiệu. Tiêu chí đúng: **tái tạo tốt trạng thái bình thường VÀ sai số phải tăng
khi trạng thái lệch**.

### 5.5. Phương pháp phát hiện và giải thích

Chuỗi ba bước, mỗi bước trả lời một câu hỏi:

| Bước | Đại lượng | Trả lời |
|---|---|---|
| 1 | Thống kê sai số dự đoán bình phương và khoảng cách Mahalanobis, kèm giới hạn kiểm soát 99% | Có bất thường không, từ khi nào |
| 2 | Điểm sức khỏe thang 0–100, ba vùng | Mức độ bao nhiêu |
| 3 | Đóng góp của từng đầu đo vào sai số | Bất thường ở đâu |

Điểm sức khỏe phải hiệu chỉnh trên **thang logarit** của sai số ở giai đoạn kiểm định khỏe —
thang tuyến tính bị bão hòa, làm mọi mẫu tràn lên đầu thang và mất khả năng phân biệt.

**Ranh giới quan sát – suy luận.** Đại lượng đo được là *quan sát*; dạng hư hỏng là *suy luận*
dựa trên tri thức cơ học rotor từ ngoài dữ liệu. Ví dụ: "thành phần 1X chiếm 98% năng lượng
phổ" là quan sát, "mất cân bằng" là suy luận. Hai thứ này không được gộp làm một khi trình bày.

### 5.6. Phương pháp nén và triển khai nhúng

Lượng tử hóa tham số từ số thực 32 bit sang **số nguyên 8 bit**, nhưng **không áp đồng loạt**:
tham số nằm ở mẫu số của phép chia và tham số có dải động rộng phải xử lý riêng, nếu không mô
hình sẽ mất tính hợp lệ số học.

Sinh **mã C thuần** không phụ thuộc thư viện ngoài, rồi **kiểm chứng tính đúng đắn** bằng cách
so kết quả bản C với bản gốc trên cùng dữ liệu vào — việc mã biên dịch được chưa chứng minh nó
chạy đúng.

Đo tài nguyên trên thiết bị: bộ nhớ chương trình, bộ nhớ làm việc, độ trễ suy luận, điện năng.

### 5.7. Phương pháp nghiệm thu

Ba cách nghiệm thu bổ sung nhau, mỗi cách có điều kiện riêng:

**Cách 1 — Tập đánh giá có nhãn chuyên gia.** Xây tập 350 mẫu theo đúng cấu trúc tập đánh giá
của công trình tham chiếu (150 bình thường + 200 bất thường), không chứa giờ nào đã dùng huấn
luyện. Nhãn ứng viên sinh từ **thống kê mô tả trên dữ liệu thô**, tuyệt đối **không** từ sai
số của mô hình cần chấm điểm — nếu ngược lại thì lập luận trở thành vòng tròn và kết quả vô
giá trị. Chuyên gia bảo trì dự đoán xác nhận hoặc **bác** từng nhãn; **tỉ lệ chuyên gia sửa
nhãn** được báo cáo như một chỉ số minh bạch.

**Cách 2 — Bằng chứng vật lý độc lập.** Kiểm xem lớp giải thích có tự chỉ đúng vào ổ đỡ mà
phân tích độc lập cho thấy đang thay đổi hay không, dù mô hình không được dạy ổ nào có vấn đề.

**Cách 3 — Thời gian cảnh báo trước.** Hệ lưu trữ ghi số giờ chạy kể từ lần bảo trì gần nhất;
mỗi lần đại lượng này về không tương ứng một lần can thiệp. Đo khoảng thời gian từ lúc hệ
báo động tới lúc thiết bị thật sự phải sửa. Cách này cần dữ liệu phủ tới trước mốc bảo trì —
là hướng mở rộng.

---

## 6. KẾT QUẢ MONG ĐỢI

### 6.1. Về sản phẩm phần mềm

- **Bộ dữ liệu chuẩn hóa:** tập huấn luyện gồm các giờ vận hành ở trạng thái nền (không nhãn)
  và tập đánh giá 350 mẫu có nhãn chuyên gia xác nhận, kèm tài liệu quy tắc làm sạch và quy tắc
  sinh nhãn.
- **Chương trình xử lý dữ liệu:** trích xuất, làm sạch, hợp nhất rung và biến quá trình về lưới
  thời gian chung, áp cổng lọc trạng thái vận hành.
- **Chương trình huấn luyện và đánh giá:** huấn luyện trên cửa sổ nền, tính giới hạn kiểm soát,
  chấm điểm trên tập đánh giá.
- **Mã suy luận cho thiết bị nhúng:** mã C thuần, không phụ thuộc thư viện ngoài, đã kiểm chứng
  khớp với bản gốc.
- **Chương trình giám sát trên máy tính nhúng:** đọc dữ liệu theo chu kỳ, suy luận tại chỗ, xuất
  điểm sức khỏe và danh sách đầu đo đóng góp.

Yêu cầu chung: chạy lại được từ dữ liệu thô tới kết quả cuối bằng một chuỗi bước có tài liệu,
không phụ thuộc thao tác thủ công không ghi lại.

### 6.2. Về mô hình và tối ưu

**Mô hình.** Một mô hình tái tạo học được đặc trưng của thiết bị ở trạng thái bình thường, kèm
giới hạn kiểm soát thống kê mức tin cậy 99% thay ngưỡng chỉnh tay. Mô hình phải đạt hai tính
chất **cùng lúc**: tái tạo tốt trạng thái bình thường **và** sai số tăng khi trạng thái lệch.
Tính chất thứ hai là điều kiện then chốt — một mô hình tối ưu quá mức sẽ tái tạo tốt cả dữ liệu
bất thường và mất hẳn khả năng phát hiện.

**Tối ưu kích thước.** Chọn kích thước bằng bằng chứng thực nghiệm (đường cong học), không theo
quy tắc kinh nghiệm. Kết quả mong đợi là một kết luận có căn cứ về mô hình nào phù hợp với khối
lượng dữ liệu hiện có — kể cả khi kết luận là "mô hình tuyến tính đủ tốt, mạng nơ-ron sâu bị quá
khớp", vì đó là kết luận có giá trị chứ không phải thất bại.

**Tối ưu cho thiết bị nhúng.** Thử nhiều phương án lượng tử hóa (số nguyên 8 bit và 4 bit, một
hệ số tỉ lệ cho cả mảng so với từng hàng, số thực 16 bit) và so sánh trên bộ ba chỉ số: bộ nhớ,
khả năng xếp hạng, sai lệch giá trị tuyệt đối của phần dư. Kết quả mong đợi không chỉ là "nén
được", mà là **hiểu được phương án nào phù hợp và vì sao**.

**Chỉ tiêu kỹ thuật:**

| Chỉ tiêu | Mức mong đợi |
|---|---|
| Tỉ lệ báo động giả trên giai đoạn nền | ≤ 1% (theo thiết kế giới hạn kiểm soát 99%) |
| Khả năng tách bất thường | sai số tái tạo nhóm bất thường cao hơn rõ rệt nhóm bình thường |
| Dung lượng mô hình sau nén | dưới 1 KB |
| Sai lệch do nén | phần dư lệch không quá 5% so bản chưa nén |
| Độ trễ suy luận trên thiết bị nhúng | dưới 1 giây (chu kỳ dữ liệu 1 giờ nên rất dư) |
| Lớp giải thích | mọi cảnh báo kèm danh sách đầu đo đóng góp, chỉ đúng bộ phận có vấn đề |

### 6.3. Về tài liệu

- **Báo cáo đồ án** theo khung 5 chương của mẫu, tài liệu tham khảo chuẩn IEEE.
- **Báo cáo tuần** theo mẫu; **slide báo cáo** theo mẫu.
- **Tài liệu dữ liệu:** quy tắc làm sạch, dải nền, quy tắc sinh nhãn ứng viên.
- **Hướng dẫn gán nhãn cho chuyên gia:** viết bằng ngôn ngữ chẩn đoán rung động, kèm ví dụ mẫu.
- **Báo cáo kỹ thuật từng bước:** chọn mô hình, lượng tử hóa và nhúng, ghi chú công trình tham chiếu.

Về nội dung, tài liệu phải trình bày rõ **bốn đóng góp phương pháp** so với công trình tham
chiếu: dùng rung **vector** (biên độ và pha) thay đại lượng vô hướng nên kết quả diễn giải trực
tiếp thành dạng hư hỏng; **giới hạn kiểm soát thống kê** thay ngưỡng chỉnh tay — điểm công trình
tham chiếu tự nhận là hạn chế; **phương pháp xác định cửa sổ nền có nguyên tắc** — điểm công
trình đó không kiểm; và **triển khai nhúng** — công trình đó xếp hai kiến trúc mạng sâu là tốt
nhất nhưng không làm phần này, mà cả hai đều rất khó nhúng.

Đồng thời phải **nêu rõ giới hạn** — tính trung thực về ranh giới là một phần của kết quả:
phương pháp phát hiện **thay đổi** chứ không phát hiện **mức tuyệt đối xấu** có sẵn từ đầu; chưa
phân biệt mất cân bằng với lệch trục do dữ liệu chỉ có thành phần 1X; kết quả trên **một thiết
bị** nên tính tổng quát cần kiểm thêm; chưa đo được thời gian cảnh báo trước do độ sâu lưu trữ
của dữ liệu rung không phủ tới mốc bảo trì gần nhất.

---

## 7. KẾ HOẠCH THỰC HIỆN VÀ PHÂN CÔNG

**Thời gian thực hiện:** từ ngày **03/08/2026** đến ngày **06/09/2026** (5 tuần).
**Nhóm thực hiện:** 3 thành viên.

| STT | Họ và tên | MSSV | Vai trò |
|---|---|---|---|
| 1 | Trương Ngọc Sơn | 25210183 | Điều phối, Tài liệu, Dữ liệu & Gán nhãn |
| 2 | Trần Tín Nghĩa | 25210147 | Huấn luyện & Tối ưu mô hình |
| 3 | Hồ Thị Mỹ Phương | 25210170 | Đánh giá, Kiểm thử, Triển khai thời gian thực & IoT |

### 7.1. Bảng tiến độ thực hiện dự kiến

| Tuần | Giai đoạn | Nhiệm vụ cụ thể | Người phụ trách | Kết quả cần đạt |
|---|---|---|---|---|
| **1**<br>03–09/08 | Khởi động & Nghiên cứu | Chốt yêu cầu và phạm vi; tìm hiểu lý thuyết học sâu tái tạo, điều khiển quá trình đa biến, cơ sở chẩn đoán rung động máy quay; khảo sát nguồn dữ liệu nhà máy và chọn tập dữ liệu; chọn nền tảng phần cứng nhúng. | Cả nhóm | Đề cương chi tiết; chốt nguồn dữ liệu và nền tảng phần cứng; sơ đồ khối hệ thống. |
| **2**<br>10–16/08 | Dữ liệu & Đặc trưng *(bước 1–2)* | Trích xuất dữ liệu; làm sạch (loại giá trị rác, xử lý đại lượng góc, cổng lọc trạng thái vận hành); xác định cửa sổ nền bằng quét độ dốc; hợp nhất rung và biến quá trình về lưới thời gian chung; xây tập huấn luyện và tập đánh giá; viết hướng dẫn gán nhãn và chuyển chuyên gia. | Sơn *(Phương hỗ trợ)* | Bộ dữ liệu chuẩn hóa; tài liệu quy tắc làm sạch và sinh nhãn; hướng dẫn gán nhãn đã gửi chuyên gia. |
| **3**<br>17–23/08 | Huấn luyện & Tối ưu mô hình *(bước 3–4)* | Xây và huấn luyện các kiến trúc tái tạo; đường cong học chọn kích thước; giới hạn kiểm soát 99%; điểm sức khỏe 0–100 và lớp đóng góp từng đầu đo; thực nghiệm nhiều phương án lượng tử hóa và chốt phương án. | Nghĩa | Mô hình đã huấn luyện kèm giới hạn kiểm soát; báo cáo chọn mô hình; bảng so sánh phương án lượng tử hóa; mô hình đã nén. |
| **4**<br>24–30/08 | Triển khai & Kiểm thử *(bước 5–6)* | Sinh mã C thuần và kiểm chứng khớp bản gốc; thêm tầng ngưỡng để hệ ra quyết định báo động; chương trình đọc dữ liệu và suy luận theo chu kỳ trên máy tính nhúng; biên dịch chéo; đo độ trễ, bộ nhớ, điện năng. | Phương *(Nghĩa hỗ trợ)* | Hệ chạy thật trên thiết bị nhúng; mã C đã kiểm chứng; bảng đo tài nguyên. |
| **5**<br>31/08–06/09 | Đánh giá & Hoàn thiện | Nhận tập đánh giá từ chuyên gia, tính tỉ lệ chuyên gia sửa nhãn; tính lại chỉ số theo nhãn chuyên gia; phân tích trường hợp mô hình và chuyên gia bất đồng; hoàn thiện báo cáo và tài liệu tham khảo; chuẩn bị slide. | Cả nhóm | Bảng chỉ số đánh giá cuối; báo cáo đồ án hoàn chỉnh; slide. **Nộp 06/09.** |

**Ngày nộp báo cáo tuần:** 09/08 · 16/08 · 23/08 · 30/08 · 06/09.

### 7.2. Phân công công việc dự kiến

Chia theo **trục kỹ năng** — mỗi sinh viên phụ trách một chặng liên tiếp của quy trình, có sản
phẩm đầu ra riêng kiểm tra được.

#### Trương Ngọc Sơn — Điều phối, Tài liệu, Dữ liệu & Gán nhãn

*Phụ trách bước 1–2 của quy trình: định nghĩa bài toán, thu thập và tiền xử lý dữ liệu cảm biến,
trích đặc trưng.*

**Nhiệm vụ dữ liệu:**
1. Khảo sát nguồn dữ liệu của nhà máy: xác định các điểm đo có sẵn, độ sâu lưu trữ từng điểm đo,
   và **chọn đúng thuộc tính giá trị đo** (hệ có thuộc tính khác biểu diễn phần trăm tiệm cận
   ngưỡng cảnh báo, không phải giá trị thật).
2. Trích xuất dữ liệu qua công cụ bảng tính chuyên dụng; lập tài liệu ghi rõ tag đã kéo, khoảng
   thời gian và bước lấy mẫu.
3. Xây quy trình làm sạch: loại giá trị đặc biệt biểu thị lỗi cảm biến, loại giá trị rác dạng số
   cực nhỏ, lọc bản ghi trùng, áp giới hạn vật lý theo từng loại cảm biến.
4. Xử lý **đại lượng góc** (pha) bằng công thức thống kê vòng tròn, và chuyển thành cặp sin–cos
   khi đưa vào mô hình.
5. Áp **cổng lọc trạng thái vận hành**: chỉ giữ các giờ thiết bị đang chạy có tải.
6. Hợp nhất dữ liệu rung và biến quá trình về **một lưới thời gian chung**.
7. Xác định **cửa sổ nền** bằng phương pháp quét độ dốc: quét mọi cửa sổ 30 ngày với bước 5 ngày,
   hồi quy tuyến tính từng kênh, chọn cửa sổ có độ dốc nhỏ nhất; kiểm độ dốc và mức ý nghĩa thống
   kê của từng kênh trước khi kết luận.

**Nhiệm vụ gán nhãn:**
1. Xây **tập huấn luyện** (các giờ trong cửa sổ nền, không có cột nhãn) và **tập đánh giá** (350
   mẫu, không chứa giờ nào đã dùng huấn luyện).
2. Sinh **nhãn ứng viên** bằng thống kê mô tả trên dữ liệu thô — không được dùng sai số của mô
   hình, vì như vậy lập luận đánh giá trở thành vòng tròn.
3. Điền **ví dụ mẫu** vào tập đánh giá, chọn các trường hợp dạy được nhiều nhất, gồm cả trường
   hợp mà luật thống kê gán nhãn **sai** để chuyên gia thấy mình có quyền bác.
4. Viết **hướng dẫn gán nhãn** bằng ngôn ngữ chẩn đoán rung động (biên độ, pha, dải nền), không
   dùng thuật ngữ máy học; kèm bối cảnh vận hành và lối thoát cho dòng không chắc chắn.
5. Làm việc với chuyên gia bảo trì dự đoán; ghi lại **tỉ lệ chuyên gia sửa nhãn** như một chỉ số
   minh bạch.

**Nhiệm vụ điều phối và tài liệu:**
1. Chủ trì họp nhóm đầu mỗi tuần; theo dõi tiến độ theo bảng ở mục 7.1.
2. Tổng hợp **báo cáo tuần** theo mẫu và **báo cáo đồ án** hoàn chỉnh.
3. Rà soát tính nhất quán số liệu giữa các chương — mỗi con số phải truy được về sản phẩm của
   người tạo ra nó.
4. Viết các mục thuộc phần đặt vấn đề, tổng quan và dữ liệu.

#### Trần Tín Nghĩa — Huấn luyện & Tối ưu mô hình

*Phụ trách bước 3–4 của quy trình: thiết kế và huấn luyện mô hình, nén mô hình.*

**Nhiệm vụ huấn luyện:**
1. Xây dựng các kiến trúc tái tạo để so sánh: phân tích thành phần chính, autoencoder,
   autoencoder biến phân.
2. Huấn luyện **không giám sát** trên cửa sổ nền; chia dữ liệu **theo khối thời gian** (không xáo
   trộn ngẫu nhiên, vì đây là chuỗi thời gian và xáo trộn sẽ làm rò rỉ thông tin).
3. Chạy **đường cong học** để chọn kích thước mô hình bằng bằng chứng thực nghiệm thay vì quy tắc
   kinh nghiệm; kiểm cửa sổ kiểm định vẫn thuần khỏe trước khi đọc kết quả.
4. Áp **tiêu chí chọn mô hình hai vế**: tái tạo tốt trạng thái bình thường **và** sai số tăng khi
   trạng thái lệch — không chọn theo sai số tái tạo nhỏ nhất.

**Nhiệm vụ lớp phát hiện và giải thích:**
1. Tính **thống kê sai số dự đoán bình phương** với giới hạn kiểm soát theo phương pháp khớp
   mô-men, và **khoảng cách Mahalanobis** với giới hạn theo phân phối F, ở mức tin cậy 99%.
2. Kiểm **độ nhạy theo số thành phần**: báo cáo kết quả ở nhiều lựa chọn để chứng minh kết luận
   không phụ thuộc một con số tùy chọn.
3. Xây **điểm sức khỏe 0–100**, hiệu chỉnh trên thang logarit của sai số ở giai đoạn kiểm định
   khỏe (thang tuyến tính bị bão hòa).
4. Xây **lớp đóng góp từng đầu đo** để chỉ ra bộ phận nghi có vấn đề.

**Nhiệm vụ tối ưu cho thiết bị nhúng:**
1. Thực nghiệm **nhiều phương án lượng tử hóa**: số nguyên 8 bit và 4 bit, một hệ số tỉ lệ cho cả
   mảng so với một hệ số cho từng hàng, số thực 16 bit.
2. So sánh trên **bộ ba chỉ số**: bộ nhớ, khả năng xếp hạng, và sai lệch giá trị tuyệt đối của
   sai số tái tạo — vì một phương án có thể giữ khả năng xếp hạng nhưng làm méo giá trị tuyệt
   đối, khi đó giới hạn kiểm soát và điểm sức khỏe đều sai.
3. Xử lý riêng tham số nằm ở **mẫu số** của phép chia và tham số có **dải động rộng**.
4. Chốt phương án và giao **định dạng tham số** cho Phương.

#### Hồ Thị Mỹ Phương — Đánh giá, Kiểm thử, Triển khai thời gian thực & IoT

*Phụ trách bước 5–6 của quy trình: triển khai lên thiết bị, kiểm thử tại thiết bị.*

**Nhiệm vụ thiết kế hệ thống:**
1. Chọn nền tảng phần cứng; vẽ **sơ đồ khối hệ thống** và sơ đồ nối ghép với hệ giám sát của
   nhà máy.
2. Thiết kế **lược đồ cơ sở dữ liệu** lưu chuỗi thời gian, kết quả suy luận và lịch sử cảnh báo.
3. Khảo sát cách đọc dữ liệu từ hệ giám sát và phương án lưu đệm khi mất kết nối.

**Nhiệm vụ triển khai:**
1. **Sinh mã C thuần** từ tham số mô hình đã nén — không dùng thư viện ngoài, không cấp phát bộ
   nhớ động.
2. **Kiểm chứng tính đúng đắn**: so kết quả bản C với bản gốc trên cùng dữ liệu vào; việc mã biên
   dịch được chưa chứng minh nó chạy đúng.
3. Thêm **tầng ngưỡng kiểm soát** vào mã để hệ ra **quyết định** báo động, không chỉ trả về con số
   sai số.
4. Viết **chương trình giám sát** chạy trên máy tính nhúng: đọc dữ liệu theo chu kỳ, suy luận tại
   chỗ, xuất điểm sức khỏe và danh sách đầu đo đóng góp, ghi vào cơ sở dữ liệu.
5. **Biên dịch chéo** cho kiến trúc đích.

**Nhiệm vụ kiểm thử và đánh giá:**
1. Đo **tài nguyên trên thiết bị**: bộ nhớ chương trình, bộ nhớ làm việc, độ trễ suy luận, điện
   năng tiêu thụ.
2. Kiểm tra hoạt động liên tục và xử lý tình huống lỗi: mất kết nối, dữ liệu khuyết, thiết bị dừng.
3. Tính **các chỉ số đánh giá cuối** theo nhãn chuyên gia sau khi nhận tập đánh giá.
4. Chuẩn bị **bản trình diễn** chạy thật trên thiết bị cho buổi báo cáo.

**Việc chung cả nhóm.** Báo cáo tuần theo mẫu; họp nhóm đầu mỗi tuần để chốt việc; rà soát chéo
số liệu — mỗi con số trong báo cáo phải truy được về sản phẩm của người tạo ra nó.

**Bảng phân chia mục báo cáo:**

| Thành viên | Mục phụ trách viết |
|---|---|
| Sơn | Đặt vấn đề · Đối tượng và phạm vi · Chương tổng quan · Các mục về dữ liệu và làm sạch · Kết quả về dữ liệu |
| Nghĩa | Thiết kế mô hình · Quy trình và thực nghiệm lượng tử hóa · Kết quả so sánh kiến trúc |
| Phương | Nền tảng phần cứng · Sinh mã và kiểm chứng · Thiết kế cơ sở dữ liệu · Môi trường triển khai · Nghiệm thu và đo tài nguyên |

### 7.3. Điểm giao thoa cần thống nhất trước

| Giao diện | Giữa | Cần chốt trước | Tuần |
|---|---|---|---|
| Định dạng bộ dữ liệu | Sơn → Nghĩa | Thứ tự cột đặc trưng, cách mã hóa pha thành cặp sin–cos, đơn vị, quy ước ô khuyết | 1 |
| Định dạng tham số mô hình | Nghĩa → Phương | Thứ tự các mảng, kiểu số từng mảng, cách lưu hệ số tỉ lệ | 2 |
| Nhãn chuyên gia | Sơn → Nghĩa, Phương | Tên cột, mã giá trị nhãn, cách xử lý dòng chuyên gia để trống | 2 |
| Ngưỡng và vùng cảnh báo | Nghĩa → Phương | Giá trị giới hạn kiểm soát, biên ba vùng của điểm sức khỏe | 3 |

Chốt giao diện trước cho phép hai người làm song song: Phương dựng chương trình suy luận với tham
số giả trước khi có mô hình thật, Nghĩa huấn luyện trên bộ dữ liệu đầu tiên trong khi Sơn vẫn đang
mở rộng dữ liệu. Đây là điều kiện để nén khung 10 tuần của mẫu xuống 5 tuần.

### 7.4. Phương án dự phòng

| Việc | Rủi ro | Phương án |
|---|---|---|
| Nghiệm thu chuyên gia (tuần 5) | Chuyên gia trả kết quả muộn | Báo cáo theo nhãn ứng viên, ghi rõ chưa phải nhãn chuyên gia; nghiệm thu bằng bằng chứng vật lý — lớp giải thích tự chỉ đúng ổ đỡ đang thay đổi |
| Triển khai trên thiết bị thật (tuần 4) | Không có board đúng hạn | Báo cáo dấu chân bộ nhớ và kết quả kiểm chứng mã C; ước lượng độ trễ từ số phép toán; nêu rõ phần điện năng chưa đo |

Hai việc này thuộc hai tuần khác nhau và do hai người khác nhau phụ trách nên không kéo theo nhau.
