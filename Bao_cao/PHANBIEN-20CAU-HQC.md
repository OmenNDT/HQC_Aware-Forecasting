# BỘ CÂU HỎI PHẢN BIỆN — Đồ án HQC_Aware-Forecasting

> Vai: giáo sư phản biện hội đồng. 20 câu, xếp từ dễ đến khó.
> Mỗi câu có **đáp án**, và ở các câu khó có thêm **bẫy** (chỗ trả lời sai thường gặp).
> Số liệu trong đáp án đã kiểm lại từ dữ liệu thật, không lấy theo trí nhớ.

---

## PHẦN A — Nền tảng (câu 1–5)

### Câu 1. Đề tài giải bài toán gì, và tại sao không dùng ngưỡng cảnh báo có sẵn của nhà máy?

**Đáp án.** Bài toán: phát hiện sớm trạng thái bất thường có khả năng dẫn tới hư hỏng trên máy
quay, trước khi giá trị đo chạm ngưỡng cảnh báo.

Không dùng ngưỡng nhà máy vì ba lý do:
1. **Phát hiện muộn** — ngưỡng đặt đủ cao để tránh báo động giả, nên khi chạm ngưỡng thì hư hỏng
   đã tiến triển.
2. Ngưỡng chỉ xét **từng cảm biến riêng lẻ**, không thấy được thay đổi trong **quan hệ giữa các
   cảm biến** — thứ thường xuất hiện sớm hơn.
3. Kiểm dữ liệu thật cho thấy ngưỡng trong hệ được **sinh tự động theo quy luật** (giá trị nền
   cộng một hằng số), không phải ngưỡng kỹ thuật đặt theo tiêu chuẩn — nên đối chiếu với nó ít
   có ý nghĩa.

### Câu 2. Dữ liệu đầu vào là gì? Vì sao chọn biên độ và pha thành phần 1X mà không dùng tín hiệu rung thô?

**Đáp án.** Đầu vào: **8 biên độ 1X + 8 pha 1X** của 8 đầu đo dịch chuyển (4 ổ đỡ × 2 hướng
lệch nhau 90°), lấy mẫu 1 giờ, cùng 11 biến quá trình dùng làm cổng lọc trạng thái.

Không dùng tín hiệu thô vì **mật độ dữ liệu**: hệ giám sát chỉ lưu tín hiệu thô ở vài mốc thời
điểm (khi có sự kiện), quá thưa để huấn luyện. Trong khi biên độ và pha 1X — vốn **đã là kết quả
phép biến đổi phổ do hệ tự làm** — được lưu liên tục. Với mục tiêu theo dõi xu thế dài hạn, dữ
liệu dày quan trọng hơn độ chi tiết của từng lát.

### Câu 3. Vì sao phải tách pha thành cặp sin–cos thay vì dùng trực tiếp giá trị độ?

**Đáp án.** Vì pha là **đại lượng vòng tròn**: 359° và 1° chỉ cách nhau 2° về vật lý nhưng cách
nhau 358 đơn vị nếu để nguyên số. Mô hình tuyến tính sẽ hiểu sai hoàn toàn.

Cặp (sin, cos) đưa góc lên đường tròn đơn vị, nơi khoảng cách hình học khớp khoảng cách thật.
Hệ quả: 8 kênh pha thành 16 cột, tổng đầu vào **24 chiều**.

**Lưu ý bổ sung** — cùng lý do đó, mọi thống kê trên pha (trung bình, độ lệch chuẩn) phải dùng
công thức vòng tròn. Dùng công thức thông thường sinh ra sai số nghiêm trọng: trong dữ liệu này,
trung bình thông thường của một kênh pha cho lệch **119°** giữa hai giai đoạn, nhưng công thức
vòng tròn cho thấy lệch thật chỉ **7°** — phần còn lại là artefact quấn vòng.

### Câu 4. "Học không giám sát" ở đây nghĩa là gì? Nếu không có nhãn thì đánh giá bằng gì?

**Đáp án.** Cần tách hai việc thường bị gộp:
- **Huấn luyện: không cần nhãn.** Mô hình chỉ học đặc trưng giai đoạn thiết bị vận hành bình
  thường. Tập huấn luyện **không có cột nhãn**.
- **Đánh giá: cần nhãn.** Muốn báo cáo một con số độ chính xác thì phải có nhãn để đối chiếu.

Nhãn dùng để **chấm điểm**, không dùng để huấn luyện. Đây cũng là cách công trình tham chiếu làm:
họ huấn luyện trên dữ liệu bình thường, nhưng bảng độ chính xác của họ dựa trên nhãn do chuyên gia
gán.

### Câu 5. Mô hình tái tạo hoạt động thế nào? Vì sao sai số tái tạo lại phát hiện được bất thường?

**Đáp án.** Chuỗi: 24 số → chuẩn hóa → **nén xuống 6 chiều** → **dựng lại về 24 chiều** → tính
chênh lệch.

Cơ chế nằm ở chỗ mô hình **bị buộc phải bỏ thông tin**: giữ 6 chiều trong không gian 24 chiều
nghĩa là nó chỉ giữ được các **mẫu quan hệ đã học từ giai đoạn khỏe**. Hệ quả:
- Giờ nào **giống nếp khỏe** → dựng lại gần giống bản gốc → sai số nhỏ.
- Giờ nào có **quan hệ lạ** → mô hình không có "chỗ chứa" cho kiểu quan hệ đó → dựng lại sai
  nhiều → sai số lớn.

---

## PHẦN B — Phương pháp (câu 6–12)

### Câu 6. Vì sao chọn mô hình tuyến tính mà không dùng mạng nơ-ron sâu, khi công trình tham chiếu kết luận mạng sâu tốt nhất?

**Đáp án.** Vì **khối lượng dữ liệu khác nhau**, và quyết định dựa trên bằng chứng thực nghiệm
chứ không theo kết luận của người khác.

Chạy đường cong học (giữ cố định 25% giờ khỏe cuối làm kiểm định, huấn luyện trên lượng tăng dần):

| Mô hình | Số trọng số | Sai số kiểm định | Chênh kiểm định − huấn luyện |
|---|---|---|---|
| Tuyến tính (6 thành phần) | ~144 | **0,542** | **+0,223** |
| Autoencoder 8-4-8 | 492 | 0,679 | +0,283 |
| Autoencoder 16-8-4-8-16 | 1.164 | 0,684 | +0,329 |

Hai autoencoder **đều thua** dù nhiều trọng số hơn 3–8 lần, và khoảng chênh lớn hơn — dấu hiệu
quá khớp. Cả hai còn **tệ đi** khi thêm dữ liệu, điều chỉ xảy ra khi mô hình quá lớn so với mẫu.

**Bẫy:** trả lời "vì mô hình nhỏ dễ nhúng" là **sai thứ tự lập luận** — sẽ bị hỏi ngay "vậy nếu
mạng sâu tốt hơn thì sao?". Đúng thứ tự: mô hình được chọn vì **bằng chứng đường cong học**;
việc nó dễ nhúng là **hệ quả may mắn**, không phải tiêu chí chọn.

### Câu 7. Tại sao sai số tái tạo nhỏ nhất không phải tiêu chí chọn mô hình?

**Đáp án.** Đây là cảnh báo trong phần thảo luận của công trình tham chiếu: nếu tối ưu quá mạnh,
mô hình học **sao chép đầu vào sang đầu ra**. Khi đó nó tái tạo tốt **cả** dữ liệu bình thường
**lẫn** dữ liệu lỗi — sai số nhỏ ở mọi nơi, và **tín hiệu phát hiện biến mất**.

Đề tài gặp đúng bẫy này trên dữ liệu thật: một cấu hình cho sai số tái tạo **tốt nhất** nhưng
tỉ số (sai số nhóm bất thường / nhóm bình thường) chỉ **0,95×** — tức nó tái tạo dữ liệu bất
thường còn tốt hơn dữ liệu bình thường, mất hoàn toàn khả năng phát hiện.

Tiêu chí đúng có **hai vế**: tái tạo tốt trạng thái bình thường **và** sai số phải tăng khi
trạng thái lệch.

### Câu 8. Cửa sổ nền được chọn thế nào? Vì sao không lấy đoạn đầu chuỗi dữ liệu?

**Đáp án.** Phương pháp: **quét mọi cửa sổ 30 ngày với bước 5 ngày**, chạy hồi quy tuyến tính
từng kênh trên mỗi cửa sổ, chọn cửa sổ có độ dốc nhỏ nhất. Kiểm bắt buộc: độ dốc **và mức ý
nghĩa thống kê** của từng kênh, không chỉ so đầu–cuối.

Không lấy đoạn đầu vì một cửa sổ "trông hợp lý" vẫn có thể đang chứa đợt suy giảm. Thực tế đã
gặp: cửa sổ đầu tiên trông ổn nhưng hồi quy phát hiện một kênh tăng **+2,60 µm/tháng** với mức
ý nghĩa rất cao, trong khi 6 kênh khác chỉ tăng 0,9–5,5%.

**Vì sao nghiêm trọng:** nếu huấn luyện trên nền bị nhiễm, mô hình **học luôn hướng bất thường**
và mất khả năng phát hiện chính hiện tượng đó. Đổi cửa sổ nền cải thiện tỉ số tách từ 0,95× lên
**1,81×** — nhiều hơn bất kỳ khác biệt giữa các kiến trúc mô hình.

**Đây là điểm công trình tham chiếu không kiểm**, và là một trong bốn đóng góp của đề tài.

### Câu 9. Giới hạn cảnh báo tính thế nào? "Mức tin cậy 99%" là kết quả hay đầu vào?

**Đáp án.** **99% là ĐẦU VÀO** — con số người thiết kế chọn, tương đương câu "tôi chấp nhận báo
động giả khoảng 1%". Không phải kết quả mô hình đạt được.

Dòng chảy đúng:
```
CHỌN: chấp nhận báo động giả 1%        (đầu vào)
   ↓ công thức khớp mô-men
TÍNH RA: giới hạn = 17,658             (kết quả tính)
   ↓ áp lên 743 giờ nền
ĐO ĐƯỢC: báo động giả 1,08% (8/743)    (kết quả thực nghiệm — thứ để nghiệm thu)
```

**Bẫy:** nói "mô hình đạt độ tin cậy 99%" là **sai bản chất** và sẽ bị truy ngay.

### Câu 10. Vì sao không dùng công thức "trung bình + 3 độ lệch chuẩn" cho đơn giản?

**Đáp án.** Vì công thức đó chỉ đúng với phân bố **hình chuông đối xứng**, còn phân bố sai số
tái tạo **lệch mạnh** (độ lệch 16,1; trong khi đối xứng = 0).

Kiểm bằng số trên 743 giờ nền:

| Cách tính | Giới hạn | Báo động giả thực đo |
|---|---|---|
| Khớp mô-men | 17,66 | **1,08%** (đúng thiết kế 1%) |
| Gauss (trung bình + 2,326 × độ lệch chuẩn) | 42,78 | 0,40% |

Ngưỡng Gauss **cao gấp 2,4 lần** cần thiết → bỏ sót bất thường thật.

Nguyên nhân: 5 giá trị lớn nhất là `23,9 · 31,7 · 189,8 · 197,7 · 319,5`. Chỉ ba giá trị cực
trị làm độ lệch chuẩn phồng từ 3,28 lên **15,40**. Công thức khớp mô-men **không đọc dữ liệu
đo** — nó tính từ trị riêng của mô hình — nên miễn nhiễm với đuôi này.

### Câu 11. Công thức khớp mô-men dùng dữ liệu gì làm đầu vào? Vì sao không dùng chính các giá trị sai số đã đo?

**Đáp án.** Đầu vào là **18 trị riêng bị loại** của mô hình (giữ 6, loại 18 trong 24 chiều), qua
ba mô-men:

```
θ₁ = Σλ  = 6,974      ← chính là sai số tái tạo KỲ VỌNG
θ₂ = Σλ² = 5,815      ← độ rộng
θ₃ = Σλ³ = 5,413      ← độ lệch
h₀ = 1 − 2·θ₁·θ₃/(3·θ₂²) = 0,2557   ← hệ số hiệu chỉnh độ lệch
```

Không dùng dữ liệu đo vì dữ liệu đo **bị giá trị cực trị làm méo**. Trong khi sai số tái tạo,
về bản chất, chính là **phần phương sai mô hình không giữ được** — nên phân bố lý thuyết của nó
được xác định bởi đúng các trị riêng bị loại.

**Bằng chứng lý thuyết khớp thực tế:** θ₁ = 6,974 (tính từ trị riêng) so với trung bình đo được
6,9645 — chênh **0,1%**. Hai con số đến từ hai đường hoàn toàn khác nhau mà trùng nhau.

**Đọc h₀:** bằng 1 nghĩa là phân bố đối xứng (công thức thu về dạng Gauss). Ở đây 0,26 nên số
mũ thành 1/0,26 = 3,91 — nó bẻ cong thang đo cho khớp phân bố lệch.

### Câu 12. Vì sao cần hai thống kê phát hiện? Một cái không đủ sao?

**Đáp án.** Vì chúng đo **hai hướng lệch vuông góc nhau**, và một cái không thay được cái kia.

| | Sai số dự đoán bình phương | Khoảng cách Mahalanobis |
|---|---|---|
| **Đo gì** | Lệch **vuông góc** khỏi mô hình | Xa tâm **dọc theo** mô hình |
| **Bắt loại nào** | Quan hệ giữa các cảm biến **lạ** | Quan hệ **quen** nhưng mức cực trị |
| **Loại suy** | Người lạ vào khu phố | Người quen nhưng đi lúc 3 giờ sáng |
| **Giới hạn** | Khớp mô-men trên trị riêng bị loại | Phân phối F |

**Bằng chứng số trên 743 giờ nền** — chia thành bốn vùng:

| Vùng | Số giờ |
|---|---|
| Dưới cả hai giới hạn | 725 |
| Vượt **chỉ** khoảng cách Mahalanobis | **10** |
| Vượt **chỉ** sai số dự đoán bình phương | **4** |
| Vượt cả hai | 4 |

Nếu chỉ dùng một thống kê thì bỏ sót 10 giờ hoặc 4 giờ tương ứng. Hai vùng này **không trống**
→ hai thống kê thật sự độc lập, không đo cùng một thứ.

**Ý nghĩa vật lý của trường hợp thứ hai:** một máy suy giảm mà **giữ đúng quan hệ giữa các cảm
biến** — tất cả cùng tăng — sẽ trượt dọc theo mô hình. Sai số tái tạo nhìn không thấy gì.

---

## PHẦN C — Kết quả và phần nhúng (câu 13–16)

### Câu 13. Lớp giải thích hoạt động thế nào? Làm sao mô hình biết ổ đỡ nào có vấn đề khi không ai dạy nó?

**Đáp án.** Sai số tổng được tách theo từng cột, rồi gộp ba cột của cùng một đầu đo (biên độ,
sin pha, cos pha) để xếp hạng đóng góp.

Điểm quan trọng: mô hình **không được dạy** ổ nào có vấn đề — nó chỉ học nếp khỏe. Nhưng lớp
đóng góp tự chỉ vào **ổ 2001** (đóng góp cao nhất, và là đầu đo dẫn đầu trong phần lớn mẫu bất
thường) — đúng ổ mà phân tích xu hướng **độc lập** cho thấy đang thay đổi.

Đây là nghiệm thu bằng bằng chứng vật lý, **không cần nhãn nào**.

**Chi tiết đáng nêu:** ổ 2003 có biên độ **cao nhất tuyệt đối** nhưng đóng góp chỉ trung bình —
vì mức cao của nó đã nằm trong nền. Điều này minh hoạ đúng đặc tính phương pháp: nó phát hiện
**thay đổi**, không phát hiện **mức xấu có sẵn**.

### Câu 14. Lượng tử hóa làm thế nào? Có phải chỉ đổi số thực sang số nguyên?

**Đáp án.** Không — áp đồng loạt thì **mô hình sập**. Đây là kết quả thực nghiệm, không phải
giả thiết.

Thử tám phương án, so trên **bộ ba chỉ số**:

| Phương án | Bộ nhớ | Khả năng xếp hạng | Sai lệch giá trị tuyệt đối |
|---|---|---|---|
| Gốc (số thực 32 bit) | 864 B | 0,8304 | — |
| Số nguyên 8 bit, **một hệ số cho mọi tham số** | 232 B | **sập** | — |
| **8 bit theo hàng + 16 bit cho phần còn lại** | **312 B** | 0,8303 | **0,2%** |
| Số nguyên 4 bit theo hàng | 240 B | 0,8324 | 2,5% |
| 8 bit mọi tham số, chỉ cứu một mảng | 252 B | 0,8211 | **171,6%** |

Nguyên nhân sập: vector độ lệch chuẩn có dải động **396×** và nằm ở **mẫu số** của phép chuẩn
hóa. Hệ số tỉ lệ chung làm 3/24 phần tử bị làm tròn về không → chia cho không.

**Bài học:** tham số ở **mẫu số** và tham số có **dải động rộng** phải xử lý riêng.

### Câu 15. Vì sao phải đo ba chỉ số khi so sánh các phương án nén? Một chỉ số độ chính xác không đủ sao?

**Đáp án.** Không đủ — và đây là điểm phương pháp quan trọng nhất của bước nén.

Xem phương án cuối bảng ở câu 14: khả năng xếp hạng **0,8211**, chỉ giảm 1% so bản gốc — nhìn
qua thì đạt. Nhưng sai lệch giá trị tuyệt đối là **171,6%**: sai số tái tạo trung bình đi từ
3,01 lên 8,19.

Lý do chỉ số xếp hạng không phát hiện được: nó chỉ đo **thứ tự**. Nếu mọi giá trị bị nhân lên
cùng một hệ số thì thứ tự không đổi và chỉ số không đổi.

Nhưng **giới hạn kiểm soát và điểm sức khỏe 0–100 dựa trên giá trị tuyệt đối** — nên cả hai đều
sai. Bằng chứng: số cảnh báo trên tập đánh giá tụt từ 285 xuống 253.

### Câu 16. Mô hình sau nén chỉ 312 byte. Vậy nén để làm gì khi thiết bị có hàng trăm megabyte?

**Đáp án.** Câu hỏi đúng, và phải trả lời thẳng: **nén không phải để mô hình vừa bộ nhớ** — nó
đã vừa từ trước.

Giá trị của bước này ở ba chỗ:
1. **Đi trọn quy trình thiết kế** — huấn luyện, nén, xuất tham số, suy luận trên thiết bị, đo
   tài nguyên.
2. **Một thất bại thật để phân tích** (câu 14) — có giá trị phương pháp cao hơn một kết quả
   "nén xong chạy tốt" không gặp trở ngại nào.
3. **Chứng minh mô hình đúng kích thước triển khai được ở mọi nơi** — 312 byte chạy được trên vi
   điều khiển 2 KB RAM. Công trình tham chiếu xếp hai kiến trúc mạng sâu là tốt nhất nhưng
   **không làm phần nhúng**, mà cả hai đều rất khó nhúng (cần hàng nghìn tham số và các hàm phi
   tuyến phức tạp).

**Bẫy:** trả lời "để tiết kiệm bộ nhớ" là tự đưa mình vào bẫy — hội đồng sẽ chỉ ra ngay rằng
2 KB cũng chạy được.

---

## PHẦN D — Câu hỏi khó (câu 17–20)

### Câu 17. Tỉ lệ báo động giả 1,08% đo trên chính giai đoạn dùng để huấn luyện. Đó không phải đánh giá trên dữ liệu độc lập — con số này có ý nghĩa gì?

**Đáp án.** Đúng, và phải thừa nhận rõ: **1,08% là kiểm tra tính đúng đắn của công thức, không
phải đánh giá năng lực tổng quát hóa.**

Nó trả lời câu "công thức thống kê có cho ra đúng mức báo động giả đã thiết kế hay không" — và
câu trả lời là có. Nó **không** trả lời câu "trên dữ liệu mới thì báo động giả bao nhiêu".

Muốn trả lời câu thứ hai cần một giai đoạn khỏe **thứ hai** không dùng huấn luyện. Dữ liệu hiện
có chưa cho phép: giai đoạn sau cửa sổ nền đã bắt đầu có thay đổi.

**Đây là giới hạn thật của đề tài**, cần nêu trong báo cáo thay vì trình bày 1,08% như một kết
quả tổng quát.

### Câu 18. Trên tập đánh giá, 93% mẫu được gán nhãn "bình thường" cũng vượt giới hạn cảnh báo. Vậy mô hình có phân biệt được gì không?

**Đáp án.** Đây là câu hỏi sắc nhất, và câu trả lời trung thực: **mô hình đang quá nhạy khi áp
ra ngoài cửa sổ nền** — không phải vì cơ chế sai, mà vì cửa sổ nền **quá hẹp**.

Số liệu:

| | Sai số tái tạo trung bình |
|---|---|
| Giai đoạn nền (743 giờ) | 6,96 |
| Tập đánh giá — nhãn "bình thường" | 687 |
| Tập đánh giá — nhãn "bất thường" | 1.123 |

Truy nguyên nhân — độ tán **pha** trên cửa sổ nền cực nhỏ:

| Kênh pha | Độ tán trên nền | Độ tán trên tập đánh giá | Tỉ số |
|---|---|---|---|
| 2001X | 1,44° | 16,35° | **11,3×** |
| 2001Y | 1,22° | 18,79° | **15,4×** |

Cửa sổ nền tình cờ là giai đoạn pha **rất ổn định** (độ tán 1–3°). Phép chuẩn hóa chia cho độ
lệch chuẩn nhỏ đó, nên một lệch pha **1°** ở kênh hẹp nhất đã thành **3,4 đơn vị chuẩn hóa**.
Kết quả: mọi dao động pha bình thường về sau đều bị phóng đại thành bất thường.

**Điều mô hình VẪN làm được:** phân biệt theo **thứ tự** vẫn hợp lệ — nhóm bất thường có sai số
cao hơn nhóm bình thường 1,81 lần, khả năng xếp hạng 0,83. Nghĩa là **thứ hạng dùng được, mức
tuyệt đối thì không**.

**Ba cách xử lý, phải nêu trong báo cáo:**
1. Mở rộng cửa sổ nền để bao nhiều chế độ vận hành hơn — cách đúng nhất, cần thêm dữ liệu.
2. Đặt sàn cho độ lệch chuẩn khi chuẩn hóa, tránh chia cho số quá nhỏ.
3. Hiệu chỉnh lại giới hạn trên một giai đoạn khỏe thứ hai.

Nêu thẳng vấn đề này **mạnh hơn** là im lặng — vì hội đồng sẽ tự tính ra.

### Câu 19. Nhãn trên tập đánh giá do ai gán? Nếu sinh từ chính mô hình thì lập luận có vòng tròn không?

**Đáp án.** Có — và đó chính là lý do đề tài **tuyệt đối không** sinh nhãn từ sai số của mô hình.

Quy trình đúng, hai lớp:
1. **Nhãn ứng viên** sinh từ **thống kê mô tả trên dữ liệu thô** — so từng cảm biến với dải nền.
   Tiêu chí này **độc lập với mô hình cần chấm điểm**.
2. **Chuyên gia bảo trì dự đoán phán quyết** — xác nhận hoặc **bác** từng nhãn.

Hai điều kiện bắt buộc:
- Chuyên gia phải có **quyền bác thật**. Nếu họ chỉ bấm đồng ý hàng loạt thì nhãn thuộc về luật
  thống kê, không thuộc về chuyên gia.
- **Tỉ lệ chuyên gia sửa nhãn** phải báo cáo như một chỉ số minh bạch.

Vì chuyên gia rành máy nhưng không rành thao tác gán nhãn dữ liệu, đề tài đã điền sẵn **ba ví
dụ mẫu** — trong đó một ví dụ là trường hợp **luật thống kê gán SAI** (lệch xuống dưới dải nền
không phải hư hỏng), để chuyên gia thấy mình được phép bác.

**Ghi chú trung thực:** con số 0,83 hiện tại chấm theo **nhãn ứng viên**, chưa phải nhãn chuyên
gia. Con số cuối phải tính lại sau khi chuyên gia trả kết quả.

### Câu 20. Đề tài nói "cảnh báo sớm", nhưng sớm bao nhiêu? Con số đó ở đâu?

**Đáp án.** Chưa có, và **không thể có** với dữ liệu hiện tại. Phải trả lời thẳng vì đây là câu
truy đến tận gốc.

Muốn đo thời gian cảnh báo trước cần một **mốc bảo trì thật** để đối chiếu — thời điểm thiết bị
thực sự phải sửa. Dữ liệu hiện có không phủ tới mốc nào như vậy:

```
2025-05-31        2025-08-01         2026-02-05        2026-08-04
   ▲ mốc bảo trì      ▲ biến quá trình    ▲ dữ liệu rung    ▲ hết dữ liệu
     (nằm NGOÀI)         bắt đầu             bắt đầu
```

Mốc bảo trì gần nhất nằm **trước** cả hai chuỗi dữ liệu.

**Một lần thử đã bị rút lại:** đề tài từng tính ra con số "cảnh báo trước 16 tháng", nhưng phát
hiện nó **không bền** — mốc "bất thường trở nên rõ" do chính nhóm tự định nghĩa, và nó dịch đi
hàng tháng chỉ vì đổi độ hạt thời gian. Con số đó đã bị loại bỏ.

**Điều đề tài chứng minh được:** cơ chế phát hiện hoạt động, phát hiện đúng bộ phận, giới hạn
thống kê cho mức báo động giả đúng thiết kế.
**Điều chưa chứng minh được:** cảnh báo trước bao lâu so với hư hỏng thật.

**Đường ra:** hệ lưu số giờ chạy kể từ lần bảo trì gần nhất — mỗi lần giá trị này về không tương
ứng một lần can thiệp. Kéo dữ liệu phủ tới trước một mốc như vậy trên nhiều máy sẽ cho phép đo.
Đã đưa vào danh sách dữ liệu cần kéo ở mức ưu tiên cao nhất.

---

## Ba nguyên tắc trả lời phản biện

1. **Phân biệt "chọn" với "đạt".** Mức tin cậy, số thành phần, cửa sổ nền là **lựa chọn có tiêu
   chí**; báo động giả, khả năng xếp hạng, thời gian cảnh báo là **kết quả đo**. Lẫn hai loại
   này là chỗ bị truy nhiều nhất.

2. **Nêu giới hạn trước khi bị hỏi.** Ba giới hạn phải chủ động nêu: báo động giả đo trên chính
   giai đoạn huấn luyện (câu 17), cửa sổ nền quá hẹp làm mô hình quá nhạy (câu 18), chưa đo được
   thời gian cảnh báo trước (câu 20). Nêu trước thì thành "hiểu rõ phương pháp"; bị hỏi mới nói
   thì thành "che".

3. **Phân biệt quan sát với suy luận.** "Thành phần 1X chiếm 98% năng lượng phổ" là **quan sát**;
   "mất cân bằng" là **suy luận** từ tri thức cơ học rotor bên ngoài dữ liệu. Gộp hai thứ này là
   chỗ dễ bị bắt lỗi overclaim nhất.
