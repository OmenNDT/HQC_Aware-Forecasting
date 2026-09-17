# BÁO CÁO ĐỒ ÁN MÔN HỌC

**Tên đồ án:** Nghiên cứu và xây dựng hệ thống cảnh báo sớm bất thường thiết bị quay
ứng dụng học sâu tái tạo trên dữ liệu giám sát tình trạng công nghiệp

**Tên tiếng Anh:** Early Warning of Rotating Machinery Anomalies using
Reconstruction-based Deep Learning on Industrial Condition-Monitoring Data

**GVHD:** ThS. Phan Đình Duy · **Trường:** ĐH Công nghệ Thông tin – ĐHQG TP.HCM,
Trung tâm Phát triển CNTT

> **Trạng thái tài liệu:** bản thảo v0.1 — Chương 1–3 đã viết theo dữ liệu đã kiểm chứng;
> Chương 4 mới có kết quả tiền đề (M1) và bộ dữ liệu; Chương 5 chờ kết quả.
> Các mục còn thiếu được đánh dấu **[CHỜ]** kèm điều kiện để hoàn thành.

---

# TÓM TẮT ĐỒ ÁN

Đồ án xây dựng một hệ thống **cảnh báo sớm bất thường** cho thiết bị quay công nghiệp,
áp dụng trên máy bơm cấp nước cao áp P29201A (tổ tua-bin hơi + bơm) tại một nhà máy
đạm. Bài toán đặt ra: phát hiện trạng thái bất thường có khả năng dẫn tới hư hỏng
**trước khi** thiết bị phải dừng sửa, trong điều kiện thực tế của nhà máy là **không có
dữ liệu hỏng được gán nhãn** và **rất ít ca chạy-đến-hỏng**.

Hướng tiếp cận là **học không giám sát dựa trên tái tạo** (reconstruction-based): mô hình
chỉ học đặc trưng của giai đoạn thiết bị vận hành bình thường, sau đó sai số tái tạo
(residual) đóng vai trò chỉ số bất thường. Hướng này bám theo công trình tham chiếu của
Kaspersen và cộng sự trên máy nén khí (Entropy 2021), đồng thời mở rộng ở ba điểm mà dữ
liệu của đồ án cho phép: (i) dùng **rung vector** (biên độ và pha thành phần 1X) thay vì
chỉ đại lượng vô hướng; (ii) thay ngưỡng chỉnh tay bằng **giới hạn kiểm soát thống kê**
theo lý thuyết điều khiển quá trình đa biến; (iii) lượng tử hóa mô hình về số nguyên 8 bit và triển
khai suy luận trên máy tính nhúng Raspberry Pi đặt cạnh thiết bị.

Dữ liệu gồm **8 đầu đo rung** (4 ổ đỡ × 2 hướng) và **11 biến quá trình**, trích từ hệ
PI Data Archive của nhà máy qua PI DataLink, hợp nhất trên lưới 1 giờ, tổng **4.237 giờ**
vận hành, sau làm sạch và lọc trạng thái còn **3.801 giờ** dùng được.

**[CHỜ] Kết quả chính** — điền sau khi hoàn thành huấn luyện và nghiệm thu chuyên gia.

---

# MỞ ĐẦU

Trong nhà máy hóa chất và lọc hóa dầu, thiết bị quay (bơm, máy nén, tua-bin) là nhóm
tài sản có tần suất hư hỏng cao và hậu quả dừng máy lớn nhất. Thực tế vận hành hiện nay
chủ yếu dựa trên **bảo trì theo ngưỡng**: hệ giám sát đặt một mức cảnh báo cố định, khi
biên độ rung vượt mức đó thì báo động. Cách này có hai hạn chế: báo động thường xuất
hiện khi hư hỏng đã tiến triển đáng kể, và ngưỡng cố định không phân biệt được thay đổi
do tải với thay đổi do suy giảm tình trạng.

Đồ án này đặt vấn đề theo hướng khác: thay vì hỏi *"giá trị đã vượt ngưỡng chưa?"*, hỏi
*"hành vi hiện tại có còn giống hành vi lúc thiết bị khỏe không?"*. Câu hỏi thứ hai
phát hiện được **thay đổi tương quan giữa các cảm biến** — thường xuất hiện sớm hơn
việc một con số đơn lẻ vượt ngưỡng.

---

# Chương 1. TỔNG QUAN VỀ ĐỀ TÀI

## 1.1. Đặt vấn đề và tính cấp thiết

Thiết bị quay trong nhà máy được giám sát liên tục bằng hệ đo rung và nhiệt, nhưng phần lớn
dữ liệu chỉ được dùng để so sánh với một ngưỡng cảnh báo cố định. Cách này gặp ba hạn chế:

1. **Phát hiện muộn** — ngưỡng phải đặt đủ cao để tránh báo động giả, nên khi chạm ngưỡng thì
   hư hỏng đã tiến triển. Nhà máy cần tín hiệu ở giai đoạn *chớm*, khi còn thời gian lên kế
   hoạch sửa chữa.
2. **Không có dữ liệu hỏng gán nhãn** — thiết bị được bảo trì phòng ngừa nên rất ít khi chạy
   tới hỏng thật, khiến các phương pháp học có giám sát không áp dụng được.
3. **Tải lẫn với hư hỏng** — biên độ rung phụ thuộc tải và tốc độ; hệ không tính tới điều này
   sẽ báo động mỗi khi máy đổi chế độ, và hệ quả là người vận hành tắt báo động.

Cả ba cùng chỉ về một hướng giải: **học không giám sát trên dữ liệu bình thường** — hướng đang
được quan tâm trong lĩnh vực quản lý sức khỏe thiết bị (Prognostics and Health Management).

Hình TỔNG QUAN VỀ ĐỀ TÀI.1: Tên hình 1

Bảng TỔNG QUAN VỀ ĐỀ TÀI.1: Tên bảng 1

## 1.2. Mục tiêu nghiên cứu

**Mục tiêu tổng quát:** xây dựng hệ thống phát hiện sớm trạng thái bất thường có khả năng
dẫn tới hư hỏng trên thiết bị quay, huấn luyện **không cần dữ liệu hỏng có nhãn**, và
đủ gọn để triển khai trên thiết bị biên đặt cạnh máy.

**Mục tiêu cụ thể:**

1. Xây dựng quy trình thu thập và làm sạch dữ liệu giám sát tình trạng từ hệ PI Data
   Archive của nhà máy, hợp nhất rung và biến quá trình về một trục thời gian chung.
2. Huấn luyện mô hình tái tạo (PCA, Autoencoder, Variational Autoencoder) **chỉ trên
   giai đoạn thiết bị vận hành bình thường**, sinh chỉ số bất thường từ sai số tái tạo.
3. Thay ngưỡng chỉnh tay bằng **giới hạn kiểm soát thống kê** (SPE/Q và T² Hotelling)
   có mức tin cậy xác định trước.
4. Xây dựng lớp **giải thích được**: chỉ ra đầu đo nào đóng góp nhiều nhất vào chỉ số
   bất thường, từ đó khoanh vùng bộ phận nghi có vấn đề.
5. Lượng tử hóa mô hình sang số nguyên 8 bit, triển khai suy luận trên **máy tính nhúng
   Raspberry Pi** đặt cạnh máy, và đo tài nguyên thực tế (độ trễ, bộ nhớ, điện năng).
6. Nghiệm thu bằng tập đánh giá **do chuyên gia bảo trì dự đoán xác nhận nhãn**.

## 1.3. Đối tượng và phạm vi nghiên cứu

**Đối tượng nghiên cứu:**
- Thiết bị: bơm cấp nước cao áp **P29201A** (tổ tua-bin hơi dẫn động + bơm), 4 ổ đỡ,
  8 đầu đo rung dịch chuyển kiểu tiệm cận (proximity probe) bố trí X–Y trên mỗi ổ.
- Dữ liệu: hệ **PI Data Archive** (OSIsoft/AVEVA) truy xuất qua PI DataLink; hệ giám sát
  rung **System 1** (Bently Nevada).
- Phương pháp: mô hình tái tạo (PCA, AE, VAE), thống kê điều khiển quá trình đa biến
  (MSPC), và kỹ thuật nén mô hình cho thiết bị biên.

**Phạm vi nghiên cứu:**
- *Thiết bị:* tập trung một máy (P29201A). Cụm Steam Generation có 5 máy quay
  (bảng 1.1) — các máy còn lại chỉ dùng để đối chứng, không huấn luyện riêng.
- *Thời gian:* dữ liệu rung 180 ngày (05/02/2026 – 04/08/2026) bước 1 giờ; dữ liệu quá
  trình 1 năm (01/08/2025 – 01/08/2026) bước 10 phút.
- *Đại lượng:* biên độ và pha thành phần **1X** (một lần mỗi vòng quay). Không xét các
  bậc khác (2X, dưới đồng bộ) vì hệ chỉ trích sẵn thành phần 1X.
- *Loại hư hỏng:* giới hạn ở các dạng thể hiện qua thành phần 1X, chủ yếu **mất cân bằng**.
- *Triển khai:* mô hình đã lượng tử hóa chạy suy luận trên **Raspberry Pi** với dữ liệu
  lấy từ hệ giám sát; đo tài nguyên thực tế. Chưa lắp đặt vận hành lâu dài tại hiện trường.

**Bảng 1.1: Các máy quay trong cụm Steam Generation**

| Máy | Loại | Hệ con | Số mốc bảo trì tìm được |
|---|---|---|---|
| P29201A – HP BFW Pumps | Bơm cấp nước cao áp | HP BFWP, Turbine | 1 (31/05/2025) |
| P29201B – HP BFW Pumps | Bơm cấp nước cao áp | Gear, HP BFWP, Motor | 2 (07/09/2024; 21/05/2025) |
| P29202A – MP BFW Pumps | Bơm cấp nước trung áp | HP BFWP, Motor | 0 |
| P29202B – MP BFW Pumps | Bơm cấp nước trung áp | HP BFWP, Motor | 0 |
| B29101 – Force Draft Fan | Quạt gió cưỡng bức | B29101, MB29101 | 0 |

*Nguồn: liệt kê từ PI Asset Framework, database CBM, đường dẫn `Utility\Steam Generation`.*

## 1.4. Phương pháp thực hiện

**Nghiên cứu tài liệu.** Đọc sâu công trình tham chiếu từ bản gốc của nhà xuất bản; nghiên cứu
lý thuyết điều khiển quá trình đa biến, cơ sở chẩn đoán rung động máy quay theo tiêu chuẩn
ngành, và kỹ thuật nén mô hình cho thiết bị biên. Nguyên tắc áp dụng xuyên suốt: **mọi thành
phần đưa vào hệ thống — kể cả các đường cơ sở đơn giản — phải truy được nguồn gốc phương pháp.**

**Xử lý dữ liệu.** Trích xuất từ hệ lưu trữ của nhà máy, làm sạch các dạng dữ liệu rác đặc thù
của hệ công nghiệp, xử lý riêng đại lượng góc bằng công thức thống kê vòng tròn, và áp cổng lọc
trạng thái để chỉ giữ giai đoạn thiết bị chạy có tải.

**Xác định cửa sổ nền.** Quét mọi cửa sổ 30 ngày với bước 5 ngày, hồi quy tuyến tính từng kênh
trên mỗi cửa sổ, chọn cửa sổ có độ dốc nhỏ nhất. Bước này có ảnh hưởng lớn nhất tới kết quả:
nếu huấn luyện trên nền đang chứa một đợt suy giảm, mô hình sẽ học luôn hướng bất thường và
mất khả năng phát hiện chính hiện tượng đó.

**Thực nghiệm mô hình.** Huấn luyện không giám sát trên cửa sổ nền; chia dữ liệu theo khối thời
gian (không xáo trộn, tránh rò rỉ thông tin từ tương lai); chọn kích thước mô hình bằng đường
cong học. Tiêu chí chọn có **hai vế**: tái tạo tốt trạng thái bình thường **và** sai số phải
tăng khi trạng thái lệch — vế thứ hai là bẫy mà công trình tham chiếu cảnh báo.

**Nén mô hình — thực nghiệm so sánh nhiều phương án.** Không chọn một phương án lượng tử hóa
rồi báo cáo, mà **thử tám phương án và so sánh** trên cùng bộ chỉ số: số nguyên 8 bit và 4 bit,
một hệ số tỉ lệ cho cả mảng so với một hệ số cho từng hàng, số thực 16 bit, và các biến thể xử
lý riêng tham số ở mẫu số. Bộ chỉ số gồm ba mặt — **bộ nhớ**, **khả năng xếp hạng** (diện tích
dưới đường ROC) và **sai lệch giá trị tuyệt đối** của phần dư. Ba mặt cần đo cùng nhau vì một
phương án có thể giữ nguyên khả năng xếp hạng nhưng làm méo hoàn toàn giá trị tuyệt đối — khi
đó giới hạn kiểm soát và điểm sức khỏe đều sai (chi tiết mục 3.5.4).

**Triển khai nhúng.** Sinh mã C thuần rồi kiểm chứng bằng cách so kết quả với bản gốc trên cùng
dữ liệu vào (biên dịch được chưa chứng minh chạy đúng); đo tài nguyên trên thiết bị.

**Kiểm thử và đánh giá.** Ba cách nghiệm thu bổ sung nhau: (i) tập đánh giá 350 mẫu có nhãn do
chuyên gia bảo trì dự đoán xác nhận — nhãn ứng viên sinh từ thống kê mô tả trên dữ liệu thô,
tuyệt đối không từ sai số của mô hình cần chấm điểm; (ii) kiểm xem lớp giải thích có tự chỉ
đúng bộ phận mà phân tích độc lập cho thấy đang thay đổi; (iii) đo thời gian cảnh báo trước
so với mốc bảo trì thật.

## 1.5. Kết quả mong đợi

### 1.5.1. Về sản phẩm phần mềm

| Sản phẩm | Nội dung |
|---|---|
| Bộ dữ liệu chuẩn hóa | Tập huấn luyện (giờ vận hành ở trạng thái nền, không nhãn) và tập đánh giá 350 mẫu có nhãn chuyên gia xác nhận, kèm tài liệu quy tắc làm sạch và quy tắc sinh nhãn |
| Chương trình xử lý dữ liệu | Trích xuất, làm sạch, hợp nhất rung và biến quá trình về lưới thời gian chung, áp cổng lọc trạng thái vận hành |
| Chương trình huấn luyện và đánh giá | Huấn luyện mô hình trên cửa sổ nền, tính giới hạn kiểm soát, chấm điểm trên tập đánh giá |
| Mã suy luận cho thiết bị nhúng | Mã C thuần, không phụ thuộc thư viện ngoài, đã kiểm chứng khớp với bản gốc |
| Chương trình giám sát trên máy tính nhúng | Đọc dữ liệu theo chu kỳ, suy luận tại chỗ, xuất điểm sức khỏe và danh sách đầu đo đóng góp |

Yêu cầu chung với phần mềm: chạy lại được từ dữ liệu thô tới kết quả cuối bằng một chuỗi bước
có tài liệu, không phụ thuộc thao tác thủ công không ghi lại.

### 1.5.2. Về mô hình và tối ưu

**Mô hình.** Một mô hình tái tạo học được đặc trưng của thiết bị ở trạng thái bình thường, kèm
giới hạn kiểm soát thống kê ở mức tin cậy 99% thay cho ngưỡng chỉnh tay. Mô hình phải đạt hai
tính chất **cùng lúc** — tái tạo tốt trạng thái bình thường **và** sai số tăng khi trạng thái
lệch; tính chất thứ hai là điều kiện then chốt, vì một mô hình tối ưu quá mức sẽ tái tạo tốt cả
dữ liệu bất thường và mất hẳn khả năng phát hiện.

**Tối ưu kích thước.** Kích thước mô hình được chọn bằng **bằng chứng thực nghiệm** (đường cong
học), không theo quy tắc kinh nghiệm. Kết quả mong đợi là một kết luận có căn cứ về việc mô
hình nào phù hợp với khối lượng dữ liệu hiện có — kể cả khi kết luận đó là "mô hình tuyến tính
đủ tốt, mạng nơ-ron sâu bị quá khớp", vì đây là kết luận có giá trị chứ không phải thất bại.

**Tối ưu cho thiết bị nhúng.** Thử **nhiều phương án lượng tử hóa** (số nguyên 8 bit và 4 bit,
một hệ số tỉ lệ cho cả mảng so với từng hàng, số thực 16 bit) và so sánh trên bộ ba chỉ số —
bộ nhớ, khả năng xếp hạng, và sai lệch giá trị tuyệt đối của phần dư. Kết quả mong đợi không
chỉ là "nén được", mà là **hiểu được phương án nào phù hợp và vì sao**.

**Bảng 1.2: Chỉ tiêu kỹ thuật mong đợi**

| Chỉ tiêu | Mức mong đợi |
|---|---|
| Tỉ lệ báo động giả trên giai đoạn nền | ≤ 1% (theo thiết kế giới hạn kiểm soát 99%) |
| Khả năng tách bất thường | sai số tái tạo nhóm bất thường cao hơn rõ rệt nhóm bình thường |
| Dung lượng mô hình sau nén | dưới 1 KB |
| Sai lệch do nén | phần dư lệch không quá 5% so bản chưa nén |
| Độ trễ suy luận trên thiết bị nhúng | dưới 1 giây (chu kỳ dữ liệu 1 giờ nên rất dư) |
| Lớp giải thích | mọi cảnh báo kèm danh sách đầu đo đóng góp, chỉ đúng bộ phận có vấn đề |

### 1.5.3. Về tài liệu

| Tài liệu | Nội dung |
|---|---|
| Báo cáo đồ án | Theo khung 5 chương của mẫu môn học, tài liệu tham khảo chuẩn IEEE |
| Báo cáo tuần | Theo mẫu, ghi tiến độ và vướng mắc từng tuần |
| Slide báo cáo | Theo mẫu |
| Tài liệu dữ liệu | Quy tắc làm sạch, dải nền, quy tắc sinh nhãn ứng viên |
| Hướng dẫn gán nhãn cho chuyên gia | Viết bằng ngôn ngữ chẩn đoán rung động, kèm ví dụ mẫu đã điền |
| Báo cáo kỹ thuật từng bước | Chọn mô hình, lượng tử hóa và nhúng, ghi chú công trình tham chiếu |

Yêu cầu về nội dung tài liệu, gắn với **bốn đóng góp phương pháp** mà báo cáo phải trình bày rõ
so với công trình tham chiếu: dùng rung **vector** (biên độ và pha) thay đại lượng vô hướng nên
kết quả diễn giải trực tiếp thành dạng hư hỏng; **giới hạn kiểm soát thống kê** thay ngưỡng
chỉnh tay — điểm công trình tham chiếu tự nhận là hạn chế; **phương pháp xác định cửa sổ nền có
nguyên tắc** — điểm công trình đó không kiểm; và **triển khai nhúng** — công trình đó xếp hai
kiến trúc mạng sâu là tốt nhất nhưng không làm phần này, mà cả hai đều rất khó nhúng.

Đồng thời, tài liệu phải **nêu rõ giới hạn** — tính trung thực về ranh giới được coi là một phần
của kết quả, không phải điều cần che: phương pháp phát hiện **thay đổi** chứ không phát hiện
**mức tuyệt đối xấu** có sẵn từ đầu; chưa phân biệt mất cân bằng với lệch trục do dữ liệu chỉ
có thành phần 1X; kết quả trên **một thiết bị** nên tính tổng quát cần kiểm thêm; và chưa đo
được thời gian cảnh báo trước do độ sâu lưu trữ của dữ liệu rung không phủ tới mốc bảo trì gần
nhất.

## 1.6. Cấu trúc báo cáo

Chương 1 đã trình bày mục tiêu (1.2), đối tượng và phạm vi (1.3), phương pháp thực hiện (1.4)
và kết quả mong đợi trên ba mặt — sản phẩm phần mềm, mô hình và tối ưu, tài liệu (1.5). Bốn
chương sau triển khai chi tiết.

**Chương 2** trình bày cơ sở lý thuyết: tổng quan nghiên cứu trong và ngoài nước về phát
hiện bất thường trên chuỗi thời gian công nghiệp, lý thuyết mô hình tái tạo, thống kê
điều khiển quá trình đa biến, cơ sở chẩn đoán rung động máy quay, và lý do triển khai
suy luận tại thiết bị biên.

**Chương 3** trình bày phân tích và thiết kế hệ thống: kiến trúc tổng thể từ cảm biến
tới ứng dụng, thiết kế luồng dữ liệu và làm sạch, thiết kế mô hình và cơ chế huấn luyện,
thiết kế lớp giải thích, và thiết kế lượng tử hóa cùng triển khai trên Raspberry Pi.

**Chương 4** trình bày kết quả thực nghiệm: đặc trưng bộ dữ liệu, kết quả mô hình tiền đề,
so sánh các kiến trúc, kết quả nghiệm thu với chuyên gia, kết quả nén mô hình và đo tài nguyên trên Raspberry Pi.

**Chương 5** kết luận và hướng phát triển.

---

# Chương 2. CƠ SỞ LÝ THUYẾT

## 2.1. Tổng quan các nghiên cứu liên quan

### 2.1.1. Tổng quan ngoài nước

**Công trình tham chiếu chính.** Kaspersen và cộng sự (Entropy, 2021) [1] nghiên cứu giám
sát sức khỏe máy nén khí hàng hải bằng học sâu tái tạo. Bài toán của họ đặt ra đúng hoàn
cảnh công nghiệp thực tế: rất ít dữ liệu có nhãn và rất ít ca chạy-đến-hỏng, khiến việc
xây dựng hệ PHM tin cậy trở nên khó. Cách giải: huấn luyện mô hình **chỉ trên dữ liệu
bình thường**, rồi dùng sai số tái tạo làm chỉ số bất thường. Điểm quan trọng về bản chất
bài toán mà công trình này nêu rõ: bất thường trên hệ thống công nghiệp **không phải điểm
đột biến** mà là **độ lệch tăng dần** khi các bộ phận suy giảm.

Công trình so sánh sáu kiến trúc tái tạo trên cùng tập dữ liệu (bảng 2.1) và đề xuất hai
kỹ thuật mà đồ án này áp dụng lại: chuyển sai số tái tạo thô thành **điểm bất thường
thang 0–100** chia ba vùng, và tính **đóng góp của từng cảm biến** vào sai số để tăng
tính giải thích được.

**Bảng 2.1: Độ chính xác các kiến trúc tái tạo trong công trình tham chiếu**

| Kiến trúc | Độ chính xác (350 mẫu) |
|---|---|
| Variational Autoencoder (VAE) | 1,000 |
| Encoder–Decoder LSTM | 1,000 |
| Encoder–Decoder CNN | 0,963 |
| Autoencoder (AE) | 0,797 |
| Deep Belief Network (DBN) | 0,794 |
| Sparse Autoencoder (SAE) | 0,783 |

*Nguồn: [1], Bảng 9. Hai kiến trúc tốt nhất đều dùng cửa sổ thời gian.*

Một nhận xét về phương pháp trong công trình này cần được ghi lại vì nó định hướng thiết
kế của đồ án: nếu tối ưu siêu tham số quá mạnh, mô hình tái tạo có thể học cách "sao chép"
đầu vào sang đầu ra, khi đó nó tái tạo tốt **cả** dữ liệu bình thường **lẫn** dữ liệu lỗi
và mất hẳn tín hiệu residual. Tiêu chí chọn kiến trúc do đó không phải "sai số tái tạo nhỏ
nhất" mà là "tái tạo tốt trạng thái bình thường **và** residual tăng dần khi lỗi tiến triển".

**Chỉ số sức khỏe khi ít ca hỏng và điều kiện vận hành thay đổi.** Một nhánh nghiên cứu
liên quan xây dựng chỉ số sức khỏe và dự báo tuổi thọ còn lại cho hệ thống có **ít ca hỏng**
và **điều kiện vận hành biến động**, dùng autoencoder kiểu LSTM [2]. Nhánh này đặt đúng
vấn đề *điều kiện vận hành* — thứ mà công trình [1] không xét.

**[CHỜ] Cần bổ sung:** một bài tổng quan (survey) về phát hiện bất thường chuỗi thời gian
đa biến bằng phương pháp tái tạo, để định vị đồ án trong bức tranh chung của lĩnh vực.

### 2.1.2. Tổng quan trong nước

**[CHỜ]** Phần này cần tra cứu các nghiên cứu, luận văn và sản phẩm trong nước về giám sát
tình trạng thiết bị quay và bảo trì dự đoán. Định hướng tìm kiếm: các đề tài của các trường
kỹ thuật về chẩn đoán rung động; các giải pháp bảo trì dự đoán do đơn vị trong nước triển
khai tại nhà máy điện, hóa chất, lọc dầu; các bài báo trong nước về ứng dụng học máy cho
dữ liệu cảm biến công nghiệp.

## 2.2. Cơ sở chẩn đoán rung động máy quay

### 2.2.1. Phân tích theo bậc vòng quay

Rung của trục quay không phải một đại lượng đơn lẻ mà là tổng của nhiều thành phần ứng với
các bội số của tần số quay. Tần số quay cơ bản được gọi là **1X**. Phân bố năng lượng giữa
các bậc mang thông tin chẩn đoán:

**Bảng 2.2: Quan hệ giữa thành phần phổ và dạng hư hỏng**

| Thành phần trội | Nguyên nhân cơ học | Biện pháp xử lý |
|---|---|---|
| 1X | Khối lượng lệch tâm quay cùng trục — **mất cân bằng** | Cân bằng lại rotor |
| 2X | Hai nửa khớp nối lệch tâm — **lệch trục** | Căn tâm lại khớp nối |
| Dưới đồng bộ (≈0,4–0,5X) | Màng dầu bôi trơn mất ổn định — **xoáy dầu** | Kiểm tra khe hở, dầu |
| Phổ rộng nhiều bậc | Khe hở, va đập — **lỏng cơ khí**, hỏng vòng bi | Kiểm tra bulông, vòng bi |

Bảng này là **tri thức cơ học có sẵn từ chuẩn ngành**, không phải quy luật học từ dữ liệu.
Đây là điểm quan trọng về phương pháp: nó cho phép hệ thống diễn giải bất thường thành
chẩn đoán **mà không cần bất kỳ mẫu hỏng có nhãn nào**.

### 2.2.2. Biên độ và pha — đại lượng vector

Mỗi thành phần bậc có hai đại lượng: **biên độ** (mức độ nặng) và **pha** (hướng của điểm
nặng trên vòng tròn quay). Hai đại lượng hợp thành một vector, và theo dõi vector này biến
đổi theo thời gian là kỹ thuật chuẩn trong chẩn đoán máy quay:

- Biên độ 1X tăng, pha **giữ nguyên** → mất cân bằng nặng dần *cùng một vị trí*.
- Biên độ 1X tăng, pha **quay dần** → điểm nặng **di chuyển**, dấu hiệu nghiêm trọng hơn.
- 2X tăng trong khi 1X đứng → khớp nối đang lệch dần.

Vì pha là đại lượng **góc**, mọi phép thống kê trên pha phải dùng công thức vòng tròn.
Dùng độ lệch chuẩn thông thường cho pha sẽ sinh sai số nghiêm trọng khi dữ liệu tập trung
quanh 0°/360° — chi tiết ở mục 3.2.3.

### 2.2.3. Cấu hình đo trên thiết bị nghiên cứu

Máy P29201A có 4 ổ đỡ, mỗi ổ gắn hai đầu đo tiệm cận lệch nhau 90° (ký hiệu X và Y), tổng
8 kênh. Hai đầu đo vuông góc trên cùng ổ cho phép dựng quỹ đạo tâm trục (orbit). Ngoài ra
có các đầu đo nhiệt ổ đỡ và đầu đo vị trí dọc trục.

## 2.3. Mô hình tái tạo cho phát hiện bất thường

### 2.3.1. Nguyên lý chung

Mô hình tái tạo nén dữ liệu đầu vào qua một "cổ chai" có số chiều nhỏ hơn, rồi dựng lại từ
biểu diễn nén đó. Khi chỉ được huấn luyện trên dữ liệu bình thường, mô hình học được cấu
trúc tương quan đặc trưng của trạng thái bình thường. Với dữ liệu vẫn theo cấu trúc đó, nó
dựng lại chính xác; với dữ liệu lệch khỏi cấu trúc, sai số tái tạo tăng.

Sai số tái tạo, theo công thức của công trình tham chiếu [1], là sai số tuyệt đối trung
bình giữa đầu vào và bản tái tạo:

$$RE = \frac{1}{N}\sum_{i=1}^{N}\left|x_i - \hat{x}_i\right|$$

### 2.3.2. Phân tích thành phần chính (PCA)

PCA là dạng tái tạo **tuyến tính**: nó tìm một không gian con tuyến tính giữ phần lớn
phương sai của dữ liệu, chiếu điểm dữ liệu lên đó rồi dựng lại. Khoảng cách vuông góc từ
điểm thật tới hình chiếu chính là phần dư tái tạo.

Cần phân biệt hai đại lượng dễ lẫn: **phương sai dọc theo trục** thành phần chính (đại
lượng mà tỉ lệ phần trăm phương sai giải thích đo) và **khoảng cách vuông góc** từ điểm
tới không gian con (phần dư). Hai đại lượng này vuông góc với nhau.

### 2.3.3. Autoencoder và Variational Autoencoder

Autoencoder (AE) là dạng tổng quát **phi tuyến** của PCA: thay phép chiếu tuyến tính bằng
mạng nơ-ron có hàm kích hoạt phi tuyến, nên biểu diễn được các quan hệ cong giữa các biến.
Variational Autoencoder (VAE) khác AE ở chỗ mã hóa đầu vào thành một **phân phối** thay vì
một điểm, giúp không gian nén trơn hơn và ít bị nhớ thuộc dữ liệu huấn luyện.

### 2.3.4. Ràng buộc dung lượng mô hình

Số tham số của mô hình phải cân xứng với số mẫu huấn luyện. Đây không phải một định lý mà
là nguyên tắc thực nghiệm, và cách kiểm chặt chẽ là **đường cong học** (learning curve):
huấn luyện trên lượng dữ liệu tăng dần với phần kiểm định giữ riêng, rồi so sai số huấn
luyện với sai số kiểm định. Mô hình có khoảng cách giữa hai đường lớn và sai số kiểm định
không giảm là mô hình quá lớn so với dữ liệu.

Đồ án chọn kích thước mô hình bằng bằng chứng từ đường cong học, không bằng quy tắc kinh
nghiệm và không bê nguyên kiến trúc của công trình tham chiếu — vì lượng dữ liệu khác nhau.

## 2.4. Thống kê điều khiển quá trình đa biến

Thay vì đặt ngưỡng cho từng cảm biến bằng tay, lý thuyết điều khiển quá trình đa biến
(Multivariate Statistical Process Control – MSPC) cung cấp hai thống kê có **giới hạn kiểm
soát suy ra từ phân phối của giai đoạn bình thường**, với mức tin cậy chọn trước:

- **SPE (Squared Prediction Error), còn gọi Q-statistic:** bình phương chuẩn của phần dư —
  đo mức độ điểm dữ liệu **rời khỏi** không gian con của trạng thái bình thường. Giới hạn
  kiểm soát tính theo phương pháp khớp mô-men của Jackson và Mudholkar [3].
- **T² Hotelling:** khoảng cách Mahalanobis **trong** không gian con — đo mức độ điểm dữ
  liệu đi tới vùng bất thường của chính không gian đó. Giới hạn theo phân phối F.

Hai thống kê bổ sung nhau: SPE bắt kiểu bất thường "cấu trúc tương quan bị vỡ", T² bắt
kiểu "vẫn theo cấu trúc nhưng đi quá xa".

Việc dùng giới hạn kiểm soát thống kê là một cải tiến có chủ ý so với công trình tham
chiếu [1] — công trình đó tự nhận rằng ngưỡng và tham số biến đổi của họ **phải chỉnh tay**
và nhạy với thay đổi.

## 2.5. Suy luận tại thiết bị biên

Triển khai mô hình suy luận trên thiết bị đặt cạnh máy (edge device) thay vì gửi dữ liệu
lên máy chủ trung tâm có bốn lý do trong bối cảnh nhà máy:

1. **Độ trễ.** Cảnh báo rung cần phản hồi nhanh; vòng gửi–xử lý–trả về qua mạng nhà máy
   thêm độ trễ không cần thiết cho một phép tính rất nhẹ.
2. **Bảo mật và cách ly mạng.** Mạng điều khiển công nghiệp thường được cách ly khỏi mạng
   văn phòng và Internet. Suy luận tại chỗ không đòi mở kết nối ra ngoài.
3. **Băng thông.** Dữ liệu rung tần số cao nếu truyền thô sẽ chiếm băng thông đáng kể;
   truyền kết quả suy luận thì rất nhỏ.
4. **Hoạt động khi mất kết nối.** Thiết bị biên vẫn cảnh báo được khi mạng hoặc máy chủ
   gặp sự cố.

Để mô hình chạy được trên thiết bị tài nguyên hạn chế, hai kỹ thuật nén thường dùng là
**lượng tử hóa** (quantization — chuyển tham số từ số thực 32 bit sang số nguyên 8 bit) và
**tỉa** (pruning — loại bỏ các tham số ít ảnh hưởng). Mô hình tái tạo dạng PCA hoặc
autoencoder nhỏ đặc biệt phù hợp vì phép suy luận chỉ gồm vài phép nhân ma trận.

Đồ án áp dụng lượng tử hóa; **không** áp dụng tỉa, vì mô hình đã ở mức vài trăm tham số —
tỉa thêm không còn ý nghĩa. Chi tiết quy trình và vai trò thực của bước nén ở mục 3.5.

---

# Chương 3. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG

## 3.1. Thiết kế kiến trúc tổng thể

### 3.1.1. Sơ đồ khối hệ thống

```
[8 đầu đo rung tiệm cận]  [đầu đo nhiệt ổ đỡ]  [đầu đo biến quá trình]
   trên 4 ổ đỡ (X,Y)                              tốc độ, lưu lượng, áp, mức
          │                      │                      │
          ▼                      ▼                      ▼
   ┌──────────────────────┐              ┌────────────────────────┐
   │ System 1 (Bently)    │              │  DCS / hệ điều khiển   │
   │ trích sẵn 1X Amp/Pha │              │                        │
   └──────────┬───────────┘              └───────────┬────────────┘
              └──────────────┬───────────────────────┘
                             ▼
                  ┌────────────────────────┐
                  │  PI Data Archive       │  ← lưu trữ lịch sử
                  └───────────┬────────────┘
                              │ PI DataLink
                              ▼
   ┌───────────────────────────────────────────────────────┐
   │  TẦNG XỬ LÝ DỮ LIỆU (mục 3.2)                         │
   │  làm sạch → cổng lọc trạng thái → hợp nhất lưới 1 giờ │
   └───────────────────────┬───────────────────────────────┘
                           ▼
   ┌───────────────────────────────────────────────────────┐
   │  TẦNG MÔ HÌNH (mục 3.3) — huấn luyện ngoại tuyến      │
   │  PCA · AE · VAE, train CHỈ trên giai đoạn bình thường │
   └───────────────────────┬───────────────────────────────┘
                           ▼
   ┌───────────────────────────────────────────────────────┐
   │  TẦNG PHÁT HIỆN & GIẢI THÍCH (mục 3.4)                │
   │  residual → SPE/T² + giới hạn kiểm soát 99%           │
   │           → điểm bất thường 0–100 (3 vùng)            │
   │           → đóng góp từng đầu đo                      │
   └───────────────────────┬───────────────────────────────┘
                           ▼
   ┌─────────────────────────┐     ┌─────────────────────────┐
   │ THIẾT BỊ BIÊN (mục 3.5) │     │ GIAO DIỆN GIÁM SÁT      │
   │ mô hình đã lượng tử hóa │     │ biểu đồ kiểm soát,      │
   │ suy luận tại chỗ        │     │ phiếu việc bảo trì      │
   └─────────────────────────┘     └─────────────────────────┘
```

**[CHỜ]** Sơ đồ này sẽ được vẽ lại thành hình chuẩn (Hình 3.1) thay cho khối văn bản.

### 3.1.2. Yêu cầu chức năng

| Mã | Yêu cầu |
|---|---|
| CN-1 | Thu thập dữ liệu rung và biến quá trình từ PI Data Archive theo khoảng thời gian và bước lấy mẫu chỉ định |
| CN-2 | Làm sạch dữ liệu: loại giá trị rác, giá trị sentinel, bản ghi trùng |
| CN-3 | Nhận biết và loại giai đoạn thiết bị dừng hoặc tải thấp |
| CN-4 | Huấn luyện mô hình tái tạo trên giai đoạn bình thường, không cần nhãn |
| CN-5 | Sinh chỉ số bất thường có giới hạn kiểm soát ở mức tin cậy đặt trước |
| CN-6 | Quy đổi chỉ số về thang 0–100 với ba vùng Bình thường / Cảnh báo / Nguy hiểm |
| CN-7 | Chỉ ra đầu đo đóng góp nhiều nhất vào chỉ số bất thường |
| CN-8 | Lượng tử hóa mô hình sang số nguyên 8 bit và suy luận trên Raspberry Pi, không dùng thư viện học sâu |

### 3.1.3. Yêu cầu phi chức năng

| Mã | Yêu cầu | Chỉ tiêu |
|---|---|---|
| PCN-1 | Tỉ lệ báo động giả trên giai đoạn bình thường | ≤ 1% (theo mức tin cậy 99% của giới hạn kiểm soát) |
| PCN-2 | Dung lượng mô hình cân xứng dữ liệu | xác minh bằng đường cong học |
| PCN-3 | Tính giải thích được | mọi cảnh báo kèm danh sách đầu đo đóng góp |
| PCN-4 | Độ trễ suy luận trên Raspberry Pi | dưới 1 giây (chu kỳ dữ liệu là 1 giờ nên rất dư) |
| PCN-5 | Dung lượng mô hình sau lượng tử hóa | dưới 1 KB (đạt: 312 byte) |
| PCN-6 | Sai lệch do lượng tử hóa | phần dư lệch ≤ 5% so bản gốc (đạt: 0,2%) |

## 3.2. Thiết kế luồng dữ liệu

### 3.2.1. Nguồn dữ liệu và cách truy xuất

Dữ liệu được truy xuất từ PI Data Archive qua PI DataLink. Có một điểm kỹ thuật quan trọng
về cách chọn thẻ dữ liệu (PI Point): các cảm biến giám sát tình trạng có nhiều thuộc tính,
trong đó thuộc tính giá trị thật kết thúc ở `|Direct`, `|1X Amp`, `|1X Phase`, `|Temperature`.
Có một thuộc tính khác biểu diễn **phần trăm tiệm cận ngưỡng cảnh báo**, không phải giá trị
đo. Lấy nhầm thuộc tính này cho kết quả bằng không trên toàn khoảng — đây là lỗi đã gặp
trong quá trình thu thập và đã được ghi nhận để tránh.

Một ràng buộc của hệ thống cần nêu: độ sâu lưu trữ **khác nhau theo từng thẻ**. Biên độ và
pha 1X lưu khoảng 270 ngày, trong khi biên độ tổng và khe hở lưu trên 1.150 ngày. Ràng
buộc này giới hạn khoảng thời gian nghiên cứu có đủ cả hai vế dữ liệu.

### 3.2.2. Quy trình làm sạch

**Bảng 3.1: Các quy tắc làm sạch và khối lượng dữ liệu bị loại**

| Bước | Quy tắc | Khối lượng loại |
|---|---|---|
| Giá trị rác dạng số cực nhỏ | `|v| < 10⁻¹⁰` → khuyết | 568 ô (lưu lượng 1), 2.664 ô (lưu lượng 2) |
| Giá trị rác dạng không | thẻ tốc độ phụ `= 0` khi máy đang quay | 8.836 ô (16,8%) |
| Bản ghi trùng | lọc theo tên điểm đo | 1 khối cảm biến |
| Giá trị sentinel | `−32768` (giá trị nhỏ nhất của số nguyên 16 bit) | 13 ô |

Ảnh hưởng của việc làm sạch không nhỏ: với thẻ tốc độ phụ, nếu giữ 8.836 ô rác thì độ lệch
chuẩn tính được sai **−53,6%** so với giá trị thật. Điều này cho thấy một điểm về phương
pháp: kiểm tra chất lượng trên cửa sổ thời gian ngắn gần nhất **không phát hiện được** rác
nằm ở dữ liệu cũ — phải quét toàn khoảng.

### 3.2.3. Thống kê trên đại lượng góc

Pha là đại lượng góc, nên độ lệch chuẩn phải tính theo công thức vòng tròn. Ví dụ cụ thể
từ dữ liệu của đồ án: một kênh có độ lệch chuẩn thông thường **155,7°** — con số này gợi ý
pha rất bất ổn. Nhưng 95,4% điểm của kênh này nằm gần 0°/360°, và độ lệch chuẩn vòng tròn
chỉ **15,4°**. Nếu dùng số 155,7° thì kết luận về tình trạng thiết bị sẽ sai hoàn toàn.

Công thức dùng: với tập góc $\theta_i$, đặt $\bar{C}=\overline{\cos\theta}$,
$\bar{S}=\overline{\sin\theta}$, $R=\sqrt{\bar{C}^2+\bar{S}^2}$, khi đó độ lệch chuẩn vòng
tròn là $\sigma_{circ}=\sqrt{-2\ln R}$ (đổi sang độ).

### 3.2.4. Cổng lọc trạng thái vận hành

Dữ liệu chỉ có ý nghĩa chẩn đoán khi thiết bị đang chạy có tải — giai đoạn dừng chỉ phản
ánh nền môi trường. Hai điều kiện được áp:

- **Máy đang chạy:** cần ít nhất 6 trong 8 kênh có biên độ 1X vượt 3 µm. Ngưỡng 3 µm được
  xác định từ dữ liệu: giai đoạn máy dừng cho biên độ khoảng 0,7–2,4 µm.
- **Đang mang tải:** lưu lượng ≥ 20.000 (đơn vị hệ đo), loại các giai đoạn chạy ở tải tối
  thiểu.

### 3.2.5. Hợp nhất trục thời gian

Hai vế dữ liệu có bước lấy mẫu khác nhau (rung 1 giờ, biến quá trình 10 phút). Biến quá
trình được lấy trung vị theo giờ rồi ghép với dữ liệu rung trên **lưới 1 giờ**.

**Bảng 3.2: Khối lượng dữ liệu qua các bước xử lý**

| Bước | Số giờ |
|---|---|
| Hợp nhất được hai vế | 4.237 |
| Sau cổng lọc trạng thái và tính hợp lệ | 4.032 |
| Sau loại giai đoạn chuyển tiếp vận hành | **3.801** |

## 3.3. Thiết kế mô hình và cơ chế huấn luyện

### 3.3.1. Đặc trưng đầu vào

Đầu vào gồm **16 đại lượng**: biên độ 1X và pha 1X của 8 đầu đo. Biến quá trình **không**
tham gia vector đầu vào mà chỉ dùng làm cổng lọc trạng thái (mục 3.2.4).

Lý do của lựa chọn này là kết quả đo trên chính dữ liệu: thiết bị vận hành gần như tại một
điểm làm việc duy nhất — **90,9%** thời gian chạy có tốc độ nằm trong dải hẹp 4.750–4.830
vòng/phút, và 90,2% thời gian lưu lượng nằm trong một dải hẹp tương ứng. Với biến thiên
tải hẹp như vậy, việc đưa tải vào làm biến điều kiện để mô hình học ánh xạ tải→rung không
có đủ thông tin, đồng thời làm tăng số chiều đầu vào một cách vô ích. Cách xử lý này cũng
trùng với công trình tham chiếu [1] — họ đưa các cảm biến vào cùng một vector, không tách
riêng biến tải.

Pha được chuyển thành cặp $(\sin\theta, \cos\theta)$ trước khi vào mô hình, vì pha là đại
lượng góc: giá trị 359° và 1° gần nhau về mặt vật lý nhưng cách xa nhau nếu dùng trực tiếp
làm số thực. Sau bước này vector đầu vào có **24 chiều số**.

Biên độ được chuẩn hóa về điểm z theo trung bình và độ lệch chuẩn của **giai đoạn nền**.

### 3.3.2. Bộ mô hình

| Mô hình | Vai trò | Số tham số (ước lượng) |
|---|---|---|
| PCA | Đường cơ sở tuyến tính, đối chiếu | ~100 |
| Autoencoder nhỏ | Bản phi tuyến, theo [1] | ~600 |
| Variational Autoencoder | Kiến trúc tốt nhất của [1] | ~700 |

Các kiến trúc dùng cửa sổ thời gian của công trình [1] (Encoder–Decoder LSTM và CNN) có số
tham số ở mức hàng nghìn. Với 1.307 mẫu huấn luyện, đây là mức vượt ngân sách dữ liệu, nên
đồ án **không** đưa vào bộ chính. Quyết định này sẽ được kiểm chứng bằng đường cong học
(mục 2.3.4) chứ không dựa trên phỏng đoán.

### 3.3.3. Cơ chế huấn luyện

- **Dữ liệu huấn luyện:** 1.307 giờ giai đoạn nền (05/02/2026 – 31/03/2026), **không có
  cột nhãn**. Đây là điểm cốt lõi của học không giám sát: mô hình chỉ được cho xem trạng
  thái bình thường, không bao giờ được dạy khái niệm "hư hỏng".
- **Chia dữ liệu theo khối thời gian**, không xáo trộn ngẫu nhiên — vì đây là chuỗi thời
  gian, xáo trộn sẽ làm rò rỉ thông tin từ tương lai vào tập huấn luyện.
- **Tiêu chí chọn siêu tham số:** không phải sai số tái tạo nhỏ nhất, mà là "tái tạo tốt
  trạng thái bình thường và residual tăng khi trạng thái lệch" (theo nhận xét phương pháp
  của [1], mục 2.1.1).

### 3.3.4. Một đặc tính của phương pháp phải nêu rõ

Ổ đỡ số 2 của máy P29201A **đã ở trạng thái mất cân bằng ngay trong giai đoạn nền** (biên
độ 1X trung vị ≈ 47,7 µm, cao nhất trong 8 kênh). Hệ quả: mô hình học giai đoạn nền này sẽ
coi mức đó là "bình thường của máy này" và **không báo động ổ đỡ đó**.

Đây không phải lỗi thiết kế mà là đặc tính của phương pháp tái tạo: nó phát hiện **thay
đổi**, không phát hiện **mức tuyệt đối xấu**. Muốn phát hiện cả trạng thái xấu có sẵn thì
cần thêm một tầng đối chiếu ngưỡng tuyệt đối theo tiêu chuẩn ngành. Việc nêu rõ ranh giới
này là một phần của tính trung thực phương pháp.

## 3.4. Thiết kế lớp phát hiện và giải thích

### 3.4.1. Từ residual tới quyết định

Chuỗi xử lý gồm ba bước, mỗi bước trả lời một câu hỏi khác nhau:

| Bước | Đại lượng | Trả lời câu hỏi |
|---|---|---|
| 1 | SPE/Q và T² với giới hạn kiểm soát 99% | **Có** bất thường không, **từ khi nào**? |
| 2 | Điểm bất thường 0–100, ba vùng | **Mức độ** bao nhiêu — để người vận hành đọc nhanh |
| 3 | Đóng góp từng đầu đo | Bất thường **ở đâu** — đầu đo/ổ đỡ nào |

### 3.4.2. Điểm bất thường thang 0–100

Sai số tái tạo thô có thang đo khó đọc với người vận hành. Theo [1], nó được quy đổi qua
ba bước: chuẩn hóa cực tiểu–cực đại theo giai đoạn nền, đưa qua hàm sigmoid, rồi nhân
thang 100. Ba vùng: **Bình thường 0–40**, **Cảnh báo 40–60**, **Nguy hiểm 60–100**.

### 3.4.3. Đóng góp của từng đầu đo

Theo [1], đóng góp của đầu đo thứ $j$ vào sai số tái tạo được tính bằng tỉ lệ phần trăm
sai số của đầu đo đó trên tổng sai số:

$$C_j = 100 \times \frac{\left|x_j - \hat{x}_j\right|}{\sum_k \left|x_k - \hat{x}_k\right|}$$

Công trình [1] cho thấy mỗi dạng lỗi tạo ra một "vân tay" đóng góp riêng giữa các cảm biến,
nhờ đó nhận dạng được dạng lỗi mà không cần mẫu hỏng lịch sử.

Với đồ án này, lớp đóng góp còn mạnh hơn: vì đầu đo là **rung vector** có ý nghĩa vật lý
xác định (bảng 2.2), nên đóng góp của kênh biên độ và kênh pha dịch trực tiếp thành nhận
định về dạng hư hỏng, đối chiếu được với chuẩn ngành. Công trình [1] chỉ có cảm biến vô
hướng (áp suất, nhiệt độ, dòng điện) nên đóng góp của họ dừng ở mức "cảm biến số mấy lệch
nhiều nhất".

### 3.4.4. Ranh giới giữa quan sát và suy luận

Một quy tắc trình bày được áp dụng xuyên suốt: **đại lượng đo được là quan sát; dạng hư
hỏng là suy luận**. Ví dụ, "thành phần 1X chiếm 98% năng lượng phổ" là quan sát; "mất cân
bằng" là suy luận dựa trên tri thức cơ học rotor (bảng 2.2). Cái nối quan sát với suy luận
là tri thức vật lý từ **ngoài** dữ liệu, không phải quy luật học được từ dữ liệu. Báo cáo
không gộp hai thứ này thành một.

## 3.5. Thiết kế triển khai trên thiết bị biên

### 3.5.1. Nền tảng phần cứng

Đích triển khai là **máy tính nhúng Raspberry Pi** đặt trong tủ điện cạnh máy P29201A.
Lý do chọn nền tảng này thay vì vi điều khiển thuần:

| Tiêu chí | Raspberry Pi | Vi điều khiển (ESP32/STM32) |
|---|---|---|
| Đọc dữ liệu từ hệ PI / System 1 | có ngăn xếp mạng đầy đủ, thư viện sẵn | phải tự viết giao thức |
| Chạy mã Python đã phát triển | trực tiếp | phải viết lại bằng C |
| Lưu đệm khi mất kết nối | thẻ nhớ, hệ tập tin | bộ nhớ hạn chế |
| Tài nguyên so với mô hình | rất dư | vẫn dư (mô hình chỉ 312 byte) |

Điểm cần nói rõ: mô hình của đồ án **nhỏ tới mức cả hai nền tảng đều dư sức chạy**. Lựa
chọn Raspberry Pi không xuất phát từ giới hạn tính toán mà từ **yêu cầu tích hợp** — thiết
bị phải nói được giao thức của hệ giám sát nhà máy để lấy dữ liệu đầu vào.

**Sơ đồ nối ghép:**

```
   ┌─────────────────────┐         ┌──────────────────────────────┐
   │  Hệ PI / System 1   │────────▶│  Raspberry Pi (thiết bị biên) │
   │  (mạng nhà máy)     │  đọc    │  ┌────────────────────────┐  │
   └─────────────────────┘  chu kỳ │  │ 1. Lấy 16 đại lượng    │  │
                            1 giờ  │  │ 2. Cổng lọc trạng thái │  │
                                   │  │ 3. Chuẩn hóa + sin/cos │  │
                                   │  │ 4. Suy luận int8       │  │
                                   │  │ 5. SPE/T² → điểm 0-100 │  │
                                   │  │ 6. Đóng góp từng đầu đo│  │
                                   │  └───────────┬────────────┘  │
                                   │              ▼               │
                                   │   cảnh báo + phiếu việc      │
                                   └──────────┬───────────────────┘
                                              ▼
                                   giao diện giám sát / email / đèn báo
```

### 3.5.2. Quy trình lượng tử hóa

Lượng tử hóa chuyển tham số mô hình từ số thực 32 bit sang **số nguyên 8 bit**. Với mỗi
ma trận tham số $W$, phép lượng tử hóa đối xứng dùng một hệ số tỉ lệ:

$$s = \frac{\max_{i,j}\left|W_{ij}\right|}{127}, \qquad
W^{q}_{ij} = \mathrm{round}\!\left(\frac{W_{ij}}{s}\right), \qquad
\hat{W}_{ij} = s \cdot W^{q}_{ij}$$

Suy luận thực hiện bằng số nguyên, chỉ nhân lại hệ số tỉ lệ ở bước cuối. Sai số lượng tử hóa
được kiểm bằng cách so phần dư của mô hình gốc với mô hình đã nén trên cùng tập dữ liệu —
**tiêu chí chấp nhận: chỉ số đánh giá (diện tích dưới đường ROC) không giảm**.

Điểm cần lưu ý ngay ở bước thiết kế: phép lượng tử hóa trên **không** áp được đồng loạt cho
mọi mảng tham số. Mục 3.5.3 trình bày một thất bại cụ thể và nguyên nhân của nó.

**Bảng 3.3: Cấu trúc mô hình đã chọn về mặt nhúng (PCA k=6, đầu vào 24 chiều)**

| Thành phần | Kích thước | Vai trò |
|---|---|---|
| Ma trận thành phần chính | 6 × 24 = 144 số | phép chiếu |
| Vector tâm | 24 số | tâm không gian mô hình |
| Vector trung bình, độ lệch chuẩn | 24 + 24 = 48 số | chuẩn hóa điểm z |
| **Tổng** | **216 tham số = 864 byte (float32)** | |

**Bảng 3.4: Khối lượng tính toán mỗi lần suy luận**

| Phép toán | Số lượng |
|---|---|
| Nhân–cộng khi chiếu (24→6) | 144 |
| Nhân–cộng khi dựng lại (6→24) | 144 |
| Cộng/trừ/trị tuyệt đối khi tính phần dư | 96 |
| **Tổng** | **≈ 384 phép toán số học** |

Điểm quyết định cho khả năng nhúng: **không có hàm siêu việt** — không có hàm mũ, hàm
tang hyperbolic, căn bậc hai hay hàm chuẩn hóa xác suất. Toàn bộ suy luận là hai phép nhân
ma trận nhỏ. So sánh: một autoencoder cần hàm tang hyperbolic (phải dùng bảng tra hoặc xấp
xỉ đa thức trên vi điều khiển); kiến trúc Encoder–Decoder LSTM của công trình tham chiếu cần
hàm sigmoid và tang hyperbolic ở nhiều cổng, nhân với nhiều bước thời gian.

### 3.5.3. Lượng tử hóa mù thất bại — và bài học phương pháp

Lần thử đầu tiên áp lượng tử hóa số nguyên 8 bit **theo một hệ số tỉ lệ chung cho toàn bộ
từng mảng** (per-tensor). Kết quả: mô hình trả về giá trị không xác định (`NaN`) — sập hoàn
toàn. Nguyên nhân đã truy được và đáng ghi lại:

**Bảng 3.5: Dải động của các mảng tham số**

| Mảng | Dải giá trị | Tỉ số lớn nhất / nhỏ nhất |
|---|---|---|
| Vector trung bình | −0,92 … 47,57 | 343× |
| Vector độ lệch chuẩn | 0,0051 … 2,01 | **396×** |
| Ma trận thành phần chính | −0,495 … 0,651 | 180× |

Với vector độ lệch chuẩn, hệ số tỉ lệ tính được là 2,01/127 ≈ 0,0159. Mọi phần tử nhỏ hơn
một nửa hệ số này bị làm tròn về **không** — cụ thể **3 trong 24 phần tử** (các giá trị
0,0051 · 0,0053 · 0,0066). Vì vector này nằm ở **mẫu số** của phép chuẩn hóa điểm z, việc
làm tròn về không dẫn tới phép chia cho không.

**Bài học:** lượng tử hóa không phải một thao tác cơ học áp đồng loạt lên mọi tham số. Hai
loại tham số phải xử lý riêng: tham số nằm ở **mẫu số** của một phép chia, và tham số có
**dải động rộng**.

### 3.5.4. Thực nghiệm so sánh tám phương án lượng tử hóa

Thay vì chọn một phương án rồi báo cáo, đồ án thử **tám phương án** và so sánh trên cùng bộ chỉ
số. Điểm quan trọng về phương pháp đánh giá: cần **ba chỉ số**, không phải một.

**Bảng 3.6: So sánh tám phương án lượng tử hóa**

| # | Phương án | Bộ nhớ | Diện tích dưới ROC | Sai lệch phần dư | Số cảnh báo |
|---|---|---|---|---|---|
| 0 | float32 (bản gốc) | 864 B | 0,8304 | — | 285 |
| 1 | int8, **một hệ số cho cả mảng, mọi tham số** | 232 B | **sập** | — | — |
| 2 | int8 ma trận **theo hàng** + còn lại float32 | 456 B | 0,8303 | 0,1% | 284 |
| 3 | int8 ma trận **theo hàng** + còn lại float16 | 312 B | 0,8303 | 0,2% | 284 |
| 4 | int8 ma trận **một hệ số** + còn lại float16 | 292 B | 0,8306 | 0,2% | 284 |
| 5 | float16 toàn bộ (không dùng số nguyên) | 432 B | 0,8304 | <0,1% | 284 |
| 6 | **int4** ma trận theo hàng + còn lại float16 | **240 B** | 0,8324 | 2,5% | 277 |
| 7 | int8 mọi tham số, **chỉ** độ lệch chuẩn float16 | 252 B | 0,8211 | **171,6%** | 253 |

*Số cảnh báo: số mẫu trong 350 mẫu đánh giá vượt giới hạn kiểm soát của cùng mô hình.*

![So sánh các phương án lượng tử hóa]({{artifact:art_2baf2746-3c83-474a-9e1d-14354ea03c32}})

**Hình 3.2:** Bộ nhớ và sai lệch giá trị tuyệt đối của tám phương án. Cột màu xanh lá là các
phương án đạt; cột vàng là phương án nén sâu nhưng bắt đầu lệch; cột đỏ là phương án giữ được
khả năng xếp hạng nhưng méo giá trị tuyệt đối; cột xám là phương án sập.

**Ba điều thực nghiệm này cho thấy:**

**(a) Diện tích dưới ROC một mình gây nhầm.** Phương án 7 có chỉ số 0,8211 — chỉ giảm 1% so bản
gốc, nhìn qua thì chấp nhận được. Nhưng sai lệch giá trị tuyệt đối của phần dư là **171,6%**:
phần dư trung bình đi từ 3,01 lên 8,19. Nguyên nhân là chỉ số ROC chỉ đo **thứ tự xếp hạng** —
nếu mọi giá trị bị nhân lên cùng một hệ số thì thứ tự không đổi và chỉ số không thay đổi. Nhưng
**giới hạn kiểm soát và điểm sức khỏe 0–100 dựa trên giá trị tuyệt đối**, nên chúng sai hoàn
toàn. Số cảnh báo tụt từ 285 xuống 253 chính là hệ quả đó.

**(b) Thủ phạm là tham số ở mẫu số, không phải ma trận.** So phương án 3 với 4: ma trận lượng
tử hóa theo từng hàng (6 hệ số) và theo một hệ số duy nhất cho kết quả **gần như y nhau**
(0,8303 so 0,8306). Nghĩa là ma trận thành phần chính **chịu được** lượng tử hóa thô. Điều làm
mô hình sập ở phương án 1 và méo ở phương án 7 là **vector độ lệch chuẩn** — nó nằm ở mẫu số
của phép chuẩn hóa và có dải động 396× (bảng 3.5). Đây là một đính chính so với nhận định ban
đầu: không phải "mọi tham số đều cần lượng tử hóa theo hàng", mà là "tham số ở mẫu số phải giữ
độ chính xác".

**(c) Nén sâu hơn có giá nhưng chưa đắt.** Phương án 6 dùng số nguyên **4 bit** cho ma trận, nén
tới 240 byte — nhỏ nhất trong các phương án chạy được — với sai lệch 2,5%, vẫn dưới ngưỡng chấp
nhận 5%. Chỉ số ROC thậm chí nhích lên 0,8324, nhưng đây là biến động ngẫu nhiên chứ không phải
cải thiện thật.

### 3.5.5. Phương án được chọn và lý do

Chọn **phương án 3**: ma trận thành phần chính lượng tử hóa số nguyên 8 bit theo từng hàng,
vector trung bình và độ lệch chuẩn giữ float16 — **312 byte**, sai lệch 0,2%.

Không chọn hai phương án nhỏ hơn, dù chúng cũng đạt:

| Phương án nhỏ hơn | Vì sao không chọn |
|---|---|
| #6 int4 (240 B) | sai lệch 2,5% — cao hơn phương án 3 mười lần, đổi lấy 72 byte không cần thiết khi thiết bị đích có dư bộ nhớ |
| #4 int8 một hệ số (292 B) | tương đương phương án 3 trên dữ liệu này, nhưng lượng tử hóa theo hàng bền hơn nếu dải động của ma trận thay đổi khi huấn luyện lại |

Nguyên tắc rút ra: **chọn phương án nén nhỏ nhất trong nhóm có sai lệch không đáng kể, không
phải phương án nhỏ nhất tuyệt đối.** Khi thiết bị đích còn dư tài nguyên, đánh đổi độ chính xác
để lấy thêm vài chục byte là đổi sai chiều.

### 3.5.6. Về quy mô của bài toán

Cần đặt các con số trên vào đúng bối cảnh: mô hình 312 byte và chu kỳ dữ liệu 1 giờ nghĩa là
bài toán **không bị giới hạn bởi tài nguyên tính toán**. Giá trị của nhánh triển khai nhúng
do đó không nằm ở việc vượt qua giới hạn phần cứng, mà nằm ở ba điểm:

1. **Đi trọn quy trình thiết kế AI cho hệ thống nhúng** — huấn luyện, nén, xuất tham số,
   suy luận trên thiết bị, đo tài nguyên.
2. **Một thất bại lượng tử hóa thật để phân tích** (mục 3.5.3) — có giá trị phương pháp cao
   hơn một kết quả "nén xong, chạy tốt" không gặp trở ngại nào.
3. **Chứng minh mô hình đúng kích thước triển khai được ở mọi nơi.** Mô hình được chọn nhỏ
   vì bằng chứng từ đường cong học, không phải vì mục đích dễ nhúng; nhưng chính vì nhỏ mà
   nó chạy được trên vi điều khiển 2 KB RAM. Công trình tham chiếu xếp Encoder–Decoder LSTM
   và VAE là tốt nhất nhưng **không làm phần nhúng** — và hai kiến trúc đó rất khó nhúng.

### 3.5.7. Sinh mã C và kiểm chứng tính đúng đắn

Mô hình sau lượng tử hóa được sinh thành tệp mã C thuần (`hqc_detector.c`) — không dùng thư
viện ngoài, không cấp phát bộ nhớ động, chỉ cần một tệp khai báo kiểu số nguyên tiêu chuẩn.
Toàn bộ hàm suy luận gồm: chuẩn hóa đầu vào, nhân ma trận số nguyên hai lần, tính bình phương
chuẩn phần dư.

**Bảng 3.7: Dấu chân bộ nhớ của mã nhúng**

| Thành phần | Kích thước | Nội dung |
|---|---|---|
| Bộ nhớ chương trình (hằng số) | 384 B | ma trận lượng tử hóa 144 + hệ số tỉ lệ 24 + tâm 24 + trung bình/độ lệch chuẩn 192 |
| Bộ nhớ làm việc (ngăn xếp) | 216 B | ba mảng tạm 24 + 6 + 24 phần tử |
| Mã máy của hàm | 1.149 B | biên dịch với mức tối ưu O2 |

**Kiểm chứng tính đúng đắn.** Việc mã biên dịch được chưa chứng minh nó chạy đúng. Kết quả
của bản C được so trực tiếp với bản Python trên cùng dữ liệu vào:

**Bảng 3.8: Đối chiếu kết quả bản C với bản Python**

| Mẫu | Bản C | Bản Python | Sai lệch |
|---|---|---|---|
| 0 | 0,668439 | 0,668437 | 1,9 × 10⁻⁶ |
| 1 | 7,013474 | 7,013483 | 9,5 × 10⁻⁶ |
| 2 | 0,499448 | 0,499447 | 1,6 × 10⁻⁶ |
| 3 | 3,909388 | 3,909396 | 8,6 × 10⁻⁶ |
| 4 | 5,836287 | 5,836296 | 9,1 × 10⁻⁶ |
| 5 | 3,478087 | 3,478093 | 6,0 × 10⁻⁶ |

Toàn bộ sai lệch dưới 10⁻⁵, nguyên nhân là thứ tự cộng dồn số thực khác nhau giữa hai bản —
không phải sai lệch thuật toán.

**Bảng 3.9: Khả năng vừa với các vi điều khiển phổ thông**

| Vi điều khiển | Bộ nhớ chương trình | Bộ nhớ làm việc | Kết quả |
|---|---|---|---|
| ATmega328 (Arduino Uno) | 32 KB | 2 KB | vừa — dùng 1,2% và 11% |
| ATtiny1614 | 16 KB | 2 KB | vừa |
| STM32F103 (Cortex-M3) | 64 KB | 20 KB | dư nhiều |
| ESP32 | 4 MB | 520 KB | dư rất nhiều |

Ghi chú về tính chính xác của số đo: các con số bộ nhớ chương trình và mã máy ở bảng 3.7 được
đo khi biên dịch trên kiến trúc x86-64. Để có số chính xác cho kiến trúc ARM cần biên dịch
chéo — đây là việc còn lại của nhánh nhúng.

### 3.5.8. Chu kỳ hoạt động

Bước lấy mẫu của dữ liệu là **1 giờ**, nên thiết bị biên chỉ cần suy luận một lần mỗi giờ.
Đây là điểm khiến bài toán rất nhẹ về mặt thời gian thực: một lần suy luận ước 15–50 µs trên
vi điều khiển Cortex-M4, so với chu kỳ 1 giờ thì tỉ lệ chiếm dụng vi xử lý dưới 10⁻⁸. Thiết bị dành phần lớn
thời gian ở trạng thái chờ, phù hợp với cấu hình tiết kiệm điện.

## 3.6. Thiết kế cơ sở dữ liệu

**[CHỜ]** Lược đồ lưu chuỗi thời gian đã làm sạch, kết quả suy luận theo mốc thời gian, và
lịch sử cảnh báo kèm phản hồi của người vận hành.

---

# Chương 4. KẾT QUẢ THỰC NGHIỆM

## 4.1. Môi trường và công cụ triển khai

| Thành phần | Công cụ |
|---|---|
| Truy xuất dữ liệu | PI DataLink (add-in Excel) trên PI Data Archive |
| Xử lý dữ liệu | Python, pandas, NumPy |
| Mô hình | scikit-learn (PCA), **[CHỜ]** thư viện học sâu cho AE/VAE |
| Thống kê | SciPy |
| Trực quan hóa | Matplotlib |
| **[CHỜ]** Thiết bị biên | chờ chọn nền tảng |

## 4.2. Đặc trưng bộ dữ liệu

### 4.2.1. Hai bộ dữ liệu đã xây dựng

**Bảng 4.1: Hai bộ dữ liệu**

| Bộ | Số bản ghi | Khoảng thời gian | Nhãn |
|---|---|---|---|
| Huấn luyện | 1.307 giờ | 05/02/2026 – 31/03/2026 | **không có** (học không giám sát) |
| Đánh giá | 350 mẫu (150 + 200) | 01/04/2026 – 31/07/2026 | nhãn ứng viên + chuyên gia xác nhận |

Tập đánh giá được thiết kế **theo đúng cấu trúc tập đánh giá của công trình tham chiếu**
[1] — 150 mẫu bình thường và 200 mẫu bất thường — để so sánh được. Tập này **không chứa
giờ nào đã dùng huấn luyện**, và các mẫu được rải đều theo thời gian.

### 4.2.2. Nguồn gốc của nhãn ứng viên

Nhãn ứng viên trong tập đánh giá được sinh từ **thống kê mô tả trên dữ liệu thô** — dải
phân vị 1–99% của từng đầu đo trong giai đoạn nền — **không** từ residual của bất kỳ mô
hình nào. Đây là yêu cầu bắt buộc về tính độc lập: nếu nhãn sinh từ chính mô hình cần chấm
điểm thì lập luận trở thành vòng tròn và kết quả không có giá trị.

**Bảng 4.2: Dải nền dùng làm tiêu chí sinh nhãn ứng viên**

| Đầu đo | Dải phân vị 1–99% của biên độ 1X (µm) |
|---|---|
| Ổ 1 – hướng X | 11,3 – 18,3 |
| Ổ 1 – hướng Y | 10,9 – 17,2 |
| Ổ 2 – hướng X | 43,1 – 52,6 |
| Ổ 2 – hướng Y | 28,8 – 34,9 |
| Ổ 3 – hướng X | 9,4 – 10,6 |
| Ổ 3 – hướng Y | 8,1 – 9,0 |
| Ổ 4 – hướng X | 5,7 – 7,2 |
| Ổ 4 – hướng Y | 10,8 – 14,2 |

Luật sinh nhãn được công bố rõ: lệch từ 25% trở lên ngoài dải nền → *bất thường*; lệch
10–25% → *cần xem*; trong dải → *bình thường*.

### 4.2.3. Chất lượng dữ liệu sau làm sạch

![Tổng quan chất lượng dữ liệu sau làm sạch]({{artifact:art_d5b63079-9771-490c-912b-68b117ec17e7}})

**Hình 4.1:** Tổng quan bộ dữ liệu sau làm sạch — phân bố theo nhóm cảm biến và độ phủ
thời gian của từng kênh.

## 4.3. Kết quả phân tích tình trạng thiết bị

### 4.3.1. Chữ ký rung ở độ phân giải cao

![Chữ ký rung của bốn ổ đỡ]({{artifact:art_bc87cc32-f44e-46aa-a486-ebf306c0dff8}})

**Hình 4.2:** Chữ ký rung bốn ổ đỡ từ khối dữ liệu độ phân giải cao (bước 3 giây). Ổ số 2
có đồng thời biên độ tổng cao nhất và tỉ lệ thành phần 1X cao nhất.

### 4.3.2. Diễn biến biên độ 1X trên 180 ngày

![Xu hướng biên độ 1X trên 180 ngày]({{artifact:art_7d5bb82f-7869-4c60-824d-d57d50722801}})

**Hình 4.3:** Diễn biến biên độ 1X của 8 kênh trên 180 ngày (chỉ giai đoạn máy chạy có
tải). Ổ số 2 có biên độ cao nhất nhưng **không có xu hướng**; ổ số 1 có biên độ thấp hơn
nhưng **tăng 68%** rồi giảm một phần sau đợt khởi động lại.

Đây là phát hiện đáng chú ý về mặt bài toán: hai ổ đỡ ở **hai trạng thái khác nhau về
bản chất**.

**Bảng 4.3: Diễn biến biên độ 1X theo giai đoạn (trung vị, µm)**

| Kênh | Tháng 2 | Tháng 5 (trước đợt dừng) | Tháng 8 (sau khởi động lại) | Nhận xét |
|---|---|---|---|---|
| Ổ 1 – X | 16,5 | 27,8 (+68%) | 22,5 (+36% so tháng 2) | **đang thay đổi** |
| Ổ 1 – Y | 15,6 | 26,0 (+67%) | 24,1 (+47%) | **đang thay đổi** |
| Ổ 2 – X | 47,6 | 52,2 | 48,4 | cao nhưng **ổn định** |
| 5 kênh còn lại | — | — | — | phẳng trong ±10% |

Tải gần như không đổi trong cùng kỳ (tốc độ giảm 1%), nên diễn biến của ổ số 1 **không
giải thích được bằng thay đổi vận hành**.

Ý nghĩa với bài toán cảnh báo sớm: một hệ chỉ xét "ổ nào rung to nhất" sẽ luôn chỉ vào ổ
số 2 và **bỏ sót hoàn toàn** ổ số 1 — nơi đang có thay đổi. Đây chính là lý do phương pháp
dựa trên thay đổi so với trạng thái nền có giá trị.

### 4.3.3. Kết quả mô hình tiền đề

Trước khi xây dựng bộ mô hình chính, một mô hình tuyến tính tiền đề được dựng trên dữ liệu
nhiệt và vị trí trục 5 năm để kiểm chứng cơ chế residual.

![Biểu đồ kiểm soát SPE và T²]({{artifact:art_2ac3c112-a778-4605-b25d-ca4f94afe53d}})

**Hình 4.4:** Biểu đồ kiểm soát của mô hình tiền đề. Thống kê SPE với giới hạn kiểm soát
99% cho tỉ lệ báo động giả khoảng 1% trên giai đoạn nền — khớp mức thiết kế.

![Đường cong học]({{artifact:art_7c293b5a-b572-4ab9-99a1-880d540357ee}})

**Hình 4.5:** Đường cong học so sánh mô hình tuyến tính với hai kích thước autoencoder.
Mô hình tuyến tính có sai số kiểm định thấp nhất và khoảng cách huấn luyện–kiểm định nhỏ
nhất; hai autoencoder đều quá khớp. Đây là căn cứ bằng chứng cho việc chọn kích thước mô
hình, thay cho quy tắc kinh nghiệm.

Kết luận từ mô hình tiền đề: **cơ chế residual đứng vững** — mô hình học tương quan giữa
các cảm biến phát hiện thay đổi sớm hơn mô hình chỉ xét mức tuyệt đối, và giới hạn kiểm
soát thống kê cho tỉ lệ báo động giả đúng như thiết kế.

## 4.4. So sánh các kiến trúc mô hình

**[CHỜ]** Huấn luyện PCA, AE, VAE trên 1.307 giờ; so sánh bằng đường cong học; báo cáo
điểm bất thường 0–100 và đóng góp từng đầu đo.

## 4.5. Nghiệm thu với chuyên gia

**[CHỜ]** Tập đánh giá 350 mẫu đã được chuyển cho chuyên gia bảo trì dự đoán xác nhận.
Khi có kết quả, báo cáo hai chỉ số: (i) độ chính xác của từng mô hình trên nhãn đã được
chuyên gia xác nhận; (ii) **tỉ lệ chuyên gia sửa nhãn ứng viên** — chỉ số minh bạch cho
thấy nhãn cuối cùng là phán quyết của chuyên gia, không phải của luật thống kê.

## 4.6. Kết quả nén mô hình và triển khai nhúng

### 4.6.1. Kết quả nén — so sánh tám phương án

Mô hình được chọn (PCA k=6, 216 tham số) nén từ **864 byte** xuống **312 byte** — hệ số **2,8×**
— theo phương án ma trận lượng tử hóa số nguyên 8 bit theo từng hàng, vector trung bình và độ
lệch chuẩn giữ float16. Tám phương án đã thử và bộ ba chỉ số so sánh trình bày ở bảng 3.6 và
hình 3.2.

Ba kết quả có giá trị phương pháp:

**Phương án nhỏ nhất không phải phương án tốt nhất.** Lượng tử hóa số nguyên 4 bit đạt 240 byte
— nhỏ hơn 23% — nhưng sai lệch phần dư 2,5% so với 0,2%. Khi thiết bị đích còn dư tài nguyên,
đánh đổi độ chính xác lấy vài chục byte là đổi sai chiều.

**Chỉ số xếp hạng một mình gây nhầm.** Phương án lượng tử hóa mọi tham số (chỉ giữ độ lệch chuẩn
ở float16) có diện tích dưới ROC 0,8211 — chỉ giảm 1%, nhìn qua thì đạt. Nhưng phần dư trung bình
đi từ 3,01 lên 8,19 (**lệch 171,6%**), và số cảnh báo trên tập đánh giá tụt từ 285 xuống 253.
Nguyên nhân: chỉ số ROC chỉ đo thứ tự xếp hạng, còn giới hạn kiểm soát và điểm sức khỏe 0–100
dựa trên **giá trị tuyệt đối**. Đây là lý do phải đo cả ba chỉ số.

**Thủ phạm là tham số ở mẫu số.** Ma trận thành phần chính chịu được lượng tử hóa thô — lượng tử
hóa theo hàng và theo một hệ số duy nhất cho kết quả gần như y nhau. Điều làm mô hình sập là
vector độ lệch chuẩn với dải động 396×, nằm ở mẫu số của phép chuẩn hóa.

### 4.6.2. Kết quả kiểm chứng mã nhúng

Mã C sinh ra được biên dịch và **kiểm chứng khớp với bản Python** trên 6 mẫu, sai lệch toàn
bộ dưới 10⁻⁵ (bảng 3.8). Dấu chân bộ nhớ: **384 byte** bộ nhớ chương trình + **216 byte** bộ
nhớ làm việc + **1.149 byte** mã máy (bảng 3.7), vừa với cả vi điều khiển 32 KB / 2 KB.

### 4.6.3. Đánh giá thời gian và điện năng

| Chỉ tiêu | Giá trị | Nguồn |
|---|---|---|
| Số phép toán mỗi lần suy luận | ≈ 384 | tính từ cấu trúc mô hình |
| Thời gian đo trên x86-64 | 30 µs/mẫu | đo thực (có phần chi phí thư viện) |
| Thời gian ước lượng trên Cortex-M4 @80 MHz | 15–50 µs | suy từ số phép toán |
| Chu kỳ dữ liệu | 1 giờ | đặc tính hệ giám sát |
| Tỉ lệ chiếm dụng vi xử lý | dưới 10⁻⁸ | tính từ hai dòng trên |
| Điện năng tiêu thụ | **[CHỜ]** | cần đo trên board thật |

Tỉ lệ chiếm dụng vi xử lý cực thấp có một hệ quả thực tế: thiết bị có thể ở trạng thái ngủ
gần như toàn bộ thời gian và chỉ thức dậy mỗi giờ một lần. Điều này quan trọng nếu thiết bị
chạy pin hoặc lắp ở nơi khó cấp nguồn.

### 4.6.4. Việc còn lại của nhánh nhúng

| Việc | Lý do cần |
|---|---|
| Biên dịch chéo cho kiến trúc ARM | số bộ nhớ hiện tại đo trên x86-64, cần số ARM thật |
| Đo điện năng trên board | hoàn thành bước cuối của quy trình thiết kế nhúng |
| Thêm tầng ngưỡng kiểm soát vào mã C | hiện mã trả về giá trị phần dư, chưa ra **quyết định** báo động |
| Xét số học điểm cố định | nếu triển khai lên vi điều khiển không có đơn vị tính toán số thực |

---

# Chương 5. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

## 5.1. Kết luận

**[CHỜ]** Đối chiếu kết quả thực tế với các mục tiêu cụ thể ở mục 1.2 và các chỉ tiêu
mong đợi ở bảng 1.2.

Những phần đã hoàn thành ở thời điểm hiện tại:
- Quy trình thu thập và làm sạch dữ liệu (mục tiêu 1) — đã xây dựng, có tài liệu.
- Cơ chế residual với giới hạn kiểm soát thống kê (mục tiêu 3) — đã kiểm chứng trên mô
  hình tiền đề.
- Bộ dữ liệu huấn luyện và đánh giá — đã xây dựng, tập đánh giá đang chờ chuyên gia.

## 5.2. Hướng phát triển

Bốn hướng mở rộng đã xác định được từ chính dữ liệu:

1. **Đo thời gian cảnh báo trước.** Hệ PI ghi lại số giờ chạy kể từ lần bảo trì gần nhất;
   mỗi lần đại lượng này về không tương ứng một lần can thiệp bảo trì. Đã tìm được 3 mốc
   như vậy trên 2 máy. Nếu truy xuất được dữ liệu cảm biến phủ tới trước các mốc đó, có
   thể đo được **hệ báo động trước bao lâu so với lúc máy thật sự phải sửa** — đại lượng
   có giá trị vận hành cao nhất, và là đại lượng công trình tham chiếu [1] không đo.

2. **Mở rộng ra nhiều máy.** Cụm có 5 máy quay, trong đó **2 cặp máy song song cùng loại**.
   Hai máy cùng loại chạy cùng điều kiện là thiết kế đối chứng mạnh nhất. Công trình [1]
   chỉ có một loại máy và tự nhận đây là hạn chế.

3. **Bổ sung các bậc phổ khác.** Hệ hiện chỉ trích sẵn thành phần 1X, nên chưa phân biệt
   được mất cân bằng với lệch trục. Nếu truy xuất được thành phần 2X, khả năng chẩn đoán
   mở rộng đáng kể mà không cần thay đổi kiến trúc.

4. **Cấu trúc chẩn đoán theo hệ con.** Máy gồm nhiều hệ con (tua-bin, bơm, hộp số). Tổ
   chức lớp đóng góp theo cây hệ con sẽ chỉ ra hệ con nào có vấn đề trước, rồi mới xuống
   từng đầu đo. Đây là hướng công trình [1] đề xuất cho nghiên cứu tương lai nhưng chưa
   thực hiện vì thiết bị của họ có ít cảm biến.

---

# TÀI LIỆU THAM KHẢO

*(chuẩn IEEE)*

[1] C. J. Kaspersen, "Health Monitoring of Air Compressors Using Reconstruction-Based Deep
Learning for Anomaly Detection with Increased Transparency," *Entropy*, vol. 23, no. 1,
p. 83, Jan. 2021, doi: 10.3390/e23010083.

[2] "Developing health indicators and RUL prognostics for systems with few failure
instances and varying operating conditions using a LSTM autoencoder," *Engineering
Applications of Artificial Intelligence*, 2023, doi: 10.1016/j.engappai.2022.105582.

[3] J. E. Jackson and G. S. Mudholkar, "Control Procedures for Residuals Associated with
Principal Component Analysis," *Technometrics*, vol. 21, no. 3, pp. 341–349, 1979.

**[CHỜ]** Bổ sung: tiêu chuẩn ISO 10816 / API 610 về mức rung cho phép; tài liệu tham chiếu
về lượng tử hóa số nguyên 8 bit cho suy luận (mục 3.5.2); các tài liệu tổng quan trong nước
(mục 2.1.2).

---

# PHỤ LỤC A — KẾ HOẠCH THỰC HIỆN

**Thời gian:** 03/08/2026 – 06/09/2026 (**5 tuần**).

Bảng tiến độ ở mục A.2 trình bày **toàn bộ dự án từ đầu**, theo đúng năm giai đoạn của quy trình
thiết kế trí tuệ nhân tạo cho hệ thống nhúng. Mục A.1 ghi nhận riêng phần đã có sẵn trước mốc
bắt đầu — đây là lý do khung 5 tuần khả thi dù mẫu môn học đặt 10 tuần cộng 2 tuần cải tiến.

## A.1. Phần đã có sẵn trước mốc bắt đầu

Một phần công việc thuộc giai đoạn dữ liệu và mô hình đã được thực hiện trong quá trình khảo sát
tính khả thi trước khi đăng ký đề tài. Bảng dưới ghi rõ để phân biệt cái đã có với cái sẽ làm
trong 5 tuần; các sinh viên phụ trách vẫn thực hiện lại và kiểm chứng phần này ở tuần tương ứng.

**Bảng A.1: Phần đã có sẵn**

| Công việc | Sản phẩm |
|---|---|
| Đọc sâu công trình tham chiếu từ bản gốc | Ghi chú tham chiếu |
| Khảo sát nguồn dữ liệu nhà máy (15 bảng, 10 nguồn) | Báo cáo tình trạng dữ liệu |
| Quy trình làm sạch + cổng lọc trạng thái | Tài liệu quy tắc làm sạch |
| Xác định cửa sổ nền bằng quét độ dốc | Tập huấn luyện 743 giờ nền phẳng |
| Bộ đánh giá 350 mẫu + hướng dẫn cho chuyên gia | Tập đánh giá, đã chuyển chuyên gia |
| Đường cong học, chọn kích thước mô hình | Báo cáo chọn mô hình |
| Điểm sức khỏe 0–100 + đóng góp từng đầu đo | Tập đánh giá đã tính điểm |
| Lượng tử hóa + sinh mã C + kiểm chứng | Mã nhúng, báo cáo lượng tử hóa |
| Kiến trúc chốt, đề cương, bản thảo báo cáo | Ba tài liệu |

## A.2. Bảng tiến độ thực hiện dự kiến

**Bảng A.2: Tiến độ thực hiện**

| Tuần | Giai đoạn | Nhiệm vụ cụ thể | Người phụ trách | Kết quả cần đạt |
|---|---|---|---|---|
| **1**<br>03–09/08 | Khởi động & Nghiên cứu | Chốt yêu cầu và phạm vi; tìm hiểu lý thuyết học sâu tái tạo, điều khiển quá trình đa biến và cơ sở chẩn đoán rung động máy quay; khảo sát nguồn dữ liệu của nhà máy và chọn tập dữ liệu; chọn nền tảng phần cứng nhúng. | Cả nhóm | Đề cương chi tiết; chốt được nguồn dữ liệu và nền tảng phần cứng; sơ đồ khối hệ thống. |
| **2**<br>10–16/08 | Dữ liệu & Đặc trưng<br>*(bước 1–2)* | Trích xuất dữ liệu qua công cụ bảng tính chuyên dụng; làm sạch (loại giá trị rác, xử lý đại lượng góc, cổng lọc trạng thái vận hành); xác định cửa sổ nền bằng quét độ dốc; hợp nhất rung và biến quá trình về lưới thời gian chung; xây tập huấn luyện và tập đánh giá; viết hướng dẫn gán nhãn và chuyển chuyên gia. | Sơn<br>*(Phương hỗ trợ đọc dữ liệu)* | Bộ dữ liệu chuẩn hóa (tập huấn luyện không nhãn + tập đánh giá); tài liệu quy tắc làm sạch và sinh nhãn; hướng dẫn gán nhãn đã gửi chuyên gia. |
| **3**<br>17–23/08 | Huấn luyện & Tối ưu mô hình<br>*(bước 3–4)* | Xây và huấn luyện các kiến trúc tái tạo; chạy đường cong học chọn kích thước; tính giới hạn kiểm soát thống kê 99%; xây điểm sức khỏe 0–100 và lớp đóng góp từng đầu đo; thực nghiệm nhiều phương án lượng tử hóa và chốt phương án. | Nghĩa | Mô hình đã huấn luyện kèm giới hạn kiểm soát; báo cáo chọn mô hình có căn cứ; bảng so sánh các phương án lượng tử hóa; mô hình đã nén. |
| **4**<br>24–30/08 | Triển khai & Kiểm thử<br>*(bước 5–6)* | Sinh mã C thuần và kiểm chứng khớp bản gốc; thêm tầng ngưỡng để hệ ra quyết định báo động; viết chương trình đọc dữ liệu và suy luận theo chu kỳ trên máy tính nhúng; biên dịch chéo cho kiến trúc đích; đo độ trễ, bộ nhớ, điện năng. | Phương<br>*(Nghĩa hỗ trợ kiểm chứng)* | Hệ chạy thật trên thiết bị nhúng; mã C đã kiểm chứng; bảng đo tài nguyên (độ trễ, bộ nhớ, điện năng). |
| **5**<br>31/08–06/09 | Đánh giá & Hoàn thiện | Nhận tập đánh giá từ chuyên gia, tính tỉ lệ chuyên gia sửa nhãn; tính lại các chỉ số theo nhãn chuyên gia; phân tích trường hợp mô hình và chuyên gia bất đồng; hoàn thiện báo cáo và tài liệu tham khảo; chuẩn bị slide và bản trình diễn. | Cả nhóm | Bảng chỉ số đánh giá cuối theo nhãn chuyên gia; báo cáo đồ án hoàn chỉnh; slide báo cáo. **Nộp 06/09.** |

**Ngày nộp báo cáo tuần:** 09/08 · 16/08 · 23/08 · 30/08 · 06/09.

**Ghi chú về nén tiến độ.** Mẫu kế hoạch của môn học đặt khung 10 tuần cộng 2 tuần cải tiến. Bảng
trên nén còn 5 tuần bằng cách **gộp mỗi giai đoạn vào một tuần** và cho ba sinh viên chạy song
song ở các tuần giữa (tuần 3 Nghĩa huấn luyện trong khi Phương dựng môi trường nhúng
với tham số giả). Điều kiện để song song hóa được là các **giao diện dữ liệu phải chốt trước**
(bảng A.5).

## A.3. Đường tới hạn và phương án dự phòng

Hai việc trong kế hoạch **không hoàn toàn nằm trong tầm kiểm soát**, nên mỗi việc có phương án
dự phòng để tiến độ không bị chặn:

**Bảng A.3: Rủi ro tiến độ và phương án dự phòng**

| Việc | Rủi ro | Phương án dự phòng |
|---|---|---|
| Nghiệm thu chuyên gia (tuần 4) | Chuyên gia trả tập đánh giá muộn hoặc không kịp | Báo cáo kết quả theo **nhãn ứng viên** kèm ghi rõ đây là nhãn từ luật thống kê, chưa phải nhãn chuyên gia; đồng thời trình bày nghiệm thu bằng bằng chứng vật lý — lớp giải thích tự chỉ đúng ổ đỡ đang thay đổi (đã đạt) |
| Triển khai trên thiết bị thật (tuần 3–4) | Không có board đúng hạn | Báo cáo dấu chân bộ nhớ và kết quả kiểm chứng mã C **đã đo** (bảng 3.7, 3.8), ước lượng độ trễ từ số phép toán, và nêu rõ phần điện năng chưa đo được |

Vì hai việc này song song và không phụ thuộc nhau, chậm một việc không kéo theo việc kia. Tuần
5 chỉ dành cho viết báo cáo nên có thể hấp thu một phần trượt tiến độ từ tuần 4.

## A.4. Sản phẩm nộp

| Sản phẩm | Mốc |
|---|---|
| Báo cáo tuần (theo mẫu) | mỗi tuần, ngày ghi ở bảng A.2 |
| Báo cáo đồ án hoàn chỉnh | 06/09/2026 |
| Slide báo cáo | 06/09/2026 |
| Mã nguồn, bộ dữ liệu, mã nhúng | kèm báo cáo |

## A.5. Phân công công việc dự kiến

**Thành viên thực hiện**

| STT | Họ và tên | MSSV | Vai trò |
|---|---|---|---|
| 1 | Trương Ngọc Sơn | 25210183 | Điều phối, Tài liệu, Dữ liệu & Gán nhãn |
| 2 | Trần Tín Nghĩa | 25210147 | Huấn luyện & Tối ưu mô hình |
| 3 | Hồ Thị Mỹ Phương | 25210170 | Đánh giá, Kiểm thử, Triển khai thời gian thực & IoT |


Nhóm 3 sinh viên, chia theo **trục kỹ năng**: mỗi người phụ trách một chặng liên tiếp trong quy
trình thiết kế trí tuệ nhân tạo cho hệ thống nhúng, từ bước đầu tới bước cuối. Nguyên tắc chia:
mỗi người có **sản phẩm đầu ra riêng kiểm tra được**, và các chặng nối nhau qua **giao diện dữ
liệu đã thống nhất trước** để không ai phải chờ người khác xong mới bắt đầu được.

### Trương Ngọc Sơn — Điều phối, Tài liệu, Dữ liệu & Gán nhãn

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
1. Chủ trì họp nhóm đầu mỗi tuần; theo dõi tiến độ theo bảng ở bảng A.2.
2. Tổng hợp **báo cáo tuần** theo mẫu và **báo cáo đồ án** hoàn chỉnh.
3. Rà soát tính nhất quán số liệu giữa các chương — mỗi con số phải truy được về sản phẩm của
   người tạo ra nó.
4. Viết các mục thuộc phần đặt vấn đề, tổng quan và dữ liệu.

### Trần Tín Nghĩa — Huấn luyện & Tối ưu mô hình

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

### Hồ Thị Mỹ Phương — Đánh giá, Kiểm thử, Triển khai thời gian thực & IoT

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

**Bảng A.4: Phân chia mục báo cáo**

| Thành viên | Mục phụ trách viết |
|---|---|
| Sơn | 1.1 · 1.3 · Chương 2 · 3.1–3.3 · 4.2–4.3 |
| Nghĩa | 3.4 · 3.5.2–3.5.6 · 4.4 |
| Phương | 3.5.1 · 3.5.7–3.5.8 · 3.6 · 4.1 · 4.5–4.6 |

**Việc chung cả nhóm.** Báo cáo tuần theo mẫu, nộp vào các ngày ở bảng A.2; họp nhóm đầu mỗi
tuần để chốt việc; rà soát chéo số liệu — mỗi con số trong báo cáo phải truy được về sản phẩm
của người tạo ra nó.

**Bảng A.5: Điểm giao thoa cần thống nhất trước khi làm**

| Giao diện | Giữa | Cần chốt trước | Chốt ở tuần |
|---|---|---|---|
| Định dạng bộ dữ liệu | Sơn → Nghĩa | Thứ tự cột đặc trưng, cách mã hóa pha thành cặp sin–cos, đơn vị, quy ước ô khuyết | 1 |
| Định dạng tham số mô hình | Nghĩa → Phương | Thứ tự các mảng, kiểu số của từng mảng, cách lưu hệ số tỉ lệ | 2 |
| Nhãn chuyên gia | Sơn → Nghĩa, Phương | Tên cột, mã giá trị nhãn, cách xử lý dòng chuyên gia để trống | 2 |
| Ngưỡng và vùng cảnh báo | Nghĩa → Phương | Giá trị giới hạn kiểm soát, biên ba vùng của điểm sức khỏe | 3 |

Ba giao diện đầu được chốt **trước khi** phần tương ứng bắt đầu, nên hai người có thể làm song
song: Phương dựng được chương trình suy luận với tham số giả trước khi có mô hình thật, và
Nghĩa huấn luyện được trên bộ dữ liệu đầu tiên trong khi Sơn vẫn đang mở rộng dữ
liệu.

---

# PHỤ LỤC B — Tài liệu kèm theo

| Tài liệu | Nội dung |
|---|---|
| `Data/HQC_train_healthy.csv` | Bộ huấn luyện 1.307 giờ, 27 cột, không nhãn |
| `Data/HQC_eval_expert.csv` | Bộ đánh giá 350 mẫu, có 3 ví dụ mẫu đã điền |
| `Data/README-train-eval.md` | Tài liệu hai bộ dữ liệu: cổng lọc, luật sinh nhãn |
| `Data/HUONGDAN-gan-nhan-PDM.md` | Hướng dẫn gán nhãn cho chuyên gia |
| `hqc_detector.c` | Mã suy luận C thuần cho thiết bị nhúng |
| `test_detector.c` | Chương trình kiểm chứng mã C khớp bản Python |
| `BAOCAO-luong-tu-hoa-nhung.md` | Báo cáo chi tiết bước lượng tử hóa và nhúng |
| `BAOCAO-chon-mo-hinh.md` | Báo cáo chi tiết quá trình chọn mô hình |
| `papers/2507.08746.pdf`, `...` | Các công trình đã đọc |
