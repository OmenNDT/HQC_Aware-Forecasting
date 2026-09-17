# HQC — YÊU CẦU DỮ LIỆU v5

> Lập sau khi kiểm `PI Data rev02.xlsx` (49,8 MB, 11 sheet).
> **v5 = v4 (plan 4 máy) trừ đi phần rev02 đã có, cộng thêm 3 mục mới phát hiện khi kiểm.**

## PHẦN A — REV02 ĐÃ CÓ GÌ (ghi nhận, không cần kéo lại)

| Nội dung | Chi tiết | Đánh giá |
|---|---|---|
| **Bước 10 phút** | sheet `34_Vibration`, 43.777 hàng, 01/10/2025 → 01/08/2026 (304 ngày) | ✅ **Đây là tiến bộ lớn nhất** — đòn bẩy quan trọng nhất của plan đã xác nhận có |
| Chất lượng | khuyết 4,01%, **0 rác 6,4e-17, 0 sentinel −32768** | ✅ rất tốt |
| Rung 202A | 4 kênh `Direct` (29VT-2017AX/AY, 2019AX/AY), median 7,9–13,5 µm | ✅ dùng được |
| Rung 202B | 4 kênh `Direct`, median 1,0–1,5 µm | ⚠ xem mục A.1 |
| Nhiệt | 16 tag `Temperature` (8 mỗi máy 202A/202B) | ✅ dùng được |
| Biến quá trình | `33_Aligned` 11 biến cụm HP, cùng khoảng, bước 10m | ✅ nhưng thiếu cụm MP |
| Danh mục tag | 3 sheet `P29201A_tag`, `P29202A_tag`, `P29202B_tag` | ✅ hữu ích — có cột "Kết luận" (OK / Configure / not found) |

### A.1 ⚠ Phát hiện: máy 202B là máy DỰ PHÒNG ĐỨNG YÊN

| Máy | Số điểm rung > 3 µm | Tỉ lệ | Kết luận |
|---|---|---|---|
| 202A | 43.682 / 43.777 | **99,8%** | đang chạy, dữ liệu dùng được |
| **202B** | **77 / 43.777** | **0,2%** | **dừng suốt 304 ngày — KHÔNG train được** |

Rung 202B ổn định 1,0–1,5 µm, dưới ngưỡng máy-dừng 3 µm.
→ **Thực tế rev02 chỉ thêm được 1 máy dùng được (202A), không phải 3.**

### A.2 ⚠ Phát hiện quan trọng hơn: rev02 CHỈ CÓ `Direct`, KHÔNG có `1X Amp` / `1X Phase`

Kiểm cả 3 sheet danh mục tag: `1X Amp` xuất hiện **0 lần**, `1X Phase` **0 lần**.
Sheet `34_Vibration` cũng chỉ có tag rung dạng `Direct` (biên độ tổng).

**Hệ quả — mất phần vượt paper mạnh nhất:**

| | Có 1X Amp/Phase | Chỉ có Direct |
|---|---|---|
| Đặc trưng mỗi đầu rung | 4 (Direct + 1X Amp + sin/cos pha) | **1** |
| Chữ ký chẩn đoán | ✅ phân biệt được kiểu hỏng | ❌ chỉ biết "rung to/nhỏ" |
| Theo dõi pha trôi (điểm nặng di chuyển) | ✅ | ❌ |
| Điểm vượt paper trụ ("vector vs vô hướng") | ✅ | ❌ **mất** |

→ **Đây là mục ưu tiên cao nhất của v5** (mục B.1).

## PHẦN B — CÒN THIẾU, THEO ƯU TIÊN

### ⭐⭐ B.1 — `1X Amp` + `1X Phase` cho MỌI đầu rung (quan trọng nhất)

| | |
|---|---|
| **Tag** | mọi đầu `29VT-*` của **4 máy** × (`\|1X Amp`, `\|1X Phase`) |
| **Khoảng** | **01/10/2025 → 01/08/2026** (khớp `34_Vibration` để ghép được ngay) |
| **Bước** | **10 phút** |
| **Tại sao** | Không có 1X thì mất chữ ký vector — mất cả phần chẩn đoán kiểu hỏng lẫn điểm vượt paper trụ. `Direct` chỉ là biên độ tổng, không tách được thành phần theo bậc vòng quay. |
| **Kiểm trước** | Máy P29201A **đã từng kéo được** 1X Amp/Phase (sheet `51_Vib180d` của bản trước, 180 ngày bước 1h) → attribute này **tồn tại** trên AF. Cần kiểm 3 máy còn lại có không. |

### ⭐⭐ B.2 — Rung + nhiệt của **P29201A** và **P29201B** (hai máy quan trọng nhất, rev02 thiếu hoàn toàn)

| | |
|---|---|
| **P29201A** | 8 đầu `29VT-2001X/Y, 2003X/Y, 2005X/Y, 2007X/Y` × (`Direct`, `1X Amp`, `1X Phase`) + 11 tag `29TE-*\|Temperature` + 3 tag `29XT-*` × (`Direct`, `Gap`) |
| **P29201B** | 4 đầu rung × 3 attribute + nhiệt ổ đỡ + vị trí trục (theo cấu trúc Gear + HP BFWP + Motor) |
| **Khoảng** | **01/10/2025 → 01/08/2026**, bước **10 phút** |
| **Tại sao** | **A** là máy đã có toàn bộ phân tích của đề tài (chẩn đoán ổ 2003 mất cân bằng bằng 4 nguồn độc lập; phát hiện ổ 2001 leo +68%). **B** có **2 mốc reset bảo trì** (07/09/2024, 21/05/2025) — nguồn nhãn lead-time. Thiếu hai máy này thì rev02 không nối được với công việc đã làm. |

### ⭐ B.3 — Vị trí trục `29XT-*` (rev02 có 0/9)

| | |
|---|---|
| **Tag** | `29XT-2012, 2012A, 2013, 2013A, 2026, 2026A` (đã liệt kê trong sheet `P29201A_tag`) × (`Direct`, `Gap`) |
| **Khoảng / bước** | như B.2 |
| **Tại sao** | `Gap` (khe hở) là chỉ báo **trục dịch vị trí** — một kiểu hỏng khác với mất cân bằng. Sheet tag đã có đường dẫn AF, chỉ chưa kéo dữ liệu. |

### ⭐ B.4 — Run Hours 4 máy (nhãn nghiệm thu — rev02 không có)

| | |
|---|---|
| **Tag** | `<máy>\|Running Time\|Run Hours - Since Last Service` và `<máy>\|Status` × 4 máy |
| **Khoảng** | **04/08/2024 → 05/08/2026** (2 năm) |
| **Bước** | 1 ngày |
| **Tại sao** | Mỗi lần biến này **reset về 0** = một mốc bảo trì → nhãn để đo **lead-time thật**. Đã biết 3 mốc (A: 31/05/2025; B: 07/09/2024 + 21/05/2025); 2 máy MP chưa có reset trong tầm 365 ngày → kéo 2 năm xem có thêm. **Đây là nhãn nghiệm thu duy nhất, và tuyệt đối không đưa vào đầu vào mô hình.** |

### B.5 — Biến quá trình cụm MP (cổng lọc cho 202A/202B)

| | |
|---|---|
| **Tag** | các biến tương ứng của cụm MP: `29FI` (lưu lượng), `29PI`/`29PDI` (áp), `29SIC` (tốc độ), `29LI` (mức), `29TI` (nhiệt process) của P29202A/B |
| **Khoảng / bước** | 01/10/2025 → 01/08/2026, **10 phút** |
| **Tại sao** | `33_Aligned` chỉ có 11 biến **cụm HP**. Bốn máy có lịch chạy khác nhau (202B đứng yên là ví dụ) → **không dùng chung cổng lọc được**, mỗi máy cần biến vận hành riêng. |

### B.6 — Direct + nhiệt phủ mốc bảo trì (lead-time, khoảng CŨ hơn)

| | |
|---|---|
| **Tag** | 20 đầu `\|Direct` + nhiệt `\|Temperature` + `\|Gap` — **không cần 1X** |
| **Khoảng** | **01/08/2024 → 30/09/2025** (nối liền trước `34_Vibration`) |
| **Bước** | 1 giờ (chấp nhận thô hơn để đổi độ dài) |
| **Tại sao** | `1X Amp/Phase` chỉ sâu ~270 ngày, **không với tới mốc reset** (cách 430–700 ngày). `Direct`/`Temperature`/`Gap` sâu ~1.150 ngày → phủ được. Đây là cách **duy nhất** đo lead-time. |

### ⭐⭐ B.7 — Khối cadence 3 giây LÚC MÁY KHỎE (hiệu chỉnh ngưỡng kiểm soát)

**Đây là mục MỚI, và là mục duy nhất gỡ được một hạn chế đã xác định của mô hình hiện tại.**

| | |
|---|---|
| **Nội dung** | 2–3 khối 8 giờ, cadence 3 giây, 8 đầu rung × (`Direct`, `1X Amp`, `1X Phase`) |
| **Điều kiện BẮT BUỘC** | phải nằm **TRONG giai đoạn máy khỏe** — với P29201A là **20/02 – 22/03/2026** |
| **Bước** | 3 giây |

**Vấn đề đã đo được:** ngưỡng kiểm soát hiện tại (SPE = 17,658, mức 99%) tính từ nền lấy mẫu
**bước 1 giờ**, mà bước 1 giờ là **trung vị của ~1.200 điểm** — trung vị làm giảm phân tán rất
mạnh. Nhiễu nền thật đo ở cadence 3 giây là **0,432 µm** so với **0,028 µm** mà bước 1 giờ thấy
được (**gấp 15,5×**). Ngưỡng đang đặt trên tín hiệu mượt hơn thực tế → khi chạy trên dữ liệu độ
phân giải cao, tỉ lệ báo động giả sẽ **nhiều hơn 1%** như thiết kế.

**Vì sao 2 khối 3 giây hiện có KHÔNG dùng được cho việc này:**

| | |
|---|---|
| Khối 3 giây hiện có | 28–29/07/2026 |
| Nền khỏe tính ngưỡng | 20/02 – 22/03/2026 |
| Cách nhau | **127 ngày**, số điểm chồng lấp = **0** |
| Trạng thái máy | ổ 2001X median **22,19 µm** (tháng 7) vs **17,46 µm** (nền khỏe) = **+27%** |

→ Khối hiện có là bản đo chi tiết của máy **đã suy giảm**, không dùng để đặt lại vạch "thế nào
là khỏe" được.

**Ba đường ra, theo thứ tự nên thử:**

| # | Cách | Điều kiện |
|---|---|---|
| 1 | Kiểm hệ có **lưu khối 3 giây lịch sử** trong 02–03/2026 không | nếu có → giải xong trọn vẹn |
| 2 | Đo khối 3 giây trên **máy P29202A** (đang chạy, chưa thấy suy giảm) | dùng làm chuẩn nhiễu tham chiếu; phải nêu rõ là máy khác |
| 3 | Chấp nhận và **nêu rõ trong báo cáo** rằng ngưỡng tính từ bước 1 giờ | kèm ước lượng ảnh hưởng — không cần dữ liệu mới |

**Giả thuyết chưa kiểm được (cần nhiều khối ở nhiều mức suy giảm):** nhiễu tương đối đo được
dao động **0,64–4,46%** biên độ, và **hai ổ có nhiễu tương đối cao nhất chính là ổ 2003** đã
chẩn đoán mất cân bằng (2003X 4,03%, 2003Y 4,46%). Có thể **nhiễu tăng theo mức độ hỏng** — nếu
đúng thì bản thân nhiễu là một đặc trưng chẩn đoán mới. Chưa kết luận được.

### B.8 — Khối cadence 3 giây ĐA TẢI (chữ ký chẩn đoán nhiều điều kiện)

| | |
|---|---|
| **Nội dung** | 3–4 khối 8 giờ, cadence 3 giây, đủ đầu rung × (`Direct`, `1X Amp`, `1X Phase`) |
| **Điều kiện** | **mỗi khối một mức tải khác nhau** — hiện 2 khối đều ~4.765 rpm |
| **Tại sao** | Thư viện "chữ ký khỏe ở từng mức tải". Chưa làm được vì thiếu đa dạng tải. |

*Phân biệt B.7 với B.8: B.7 cần **cùng một tải, lúc máy khỏe** (để đo nhiễu nền chuẩn);
B.8 cần **nhiều tải khác nhau** (để dựng thư viện chữ ký). Hai mục đích khác nhau, không thay
thế nhau được.*

### 🔗 Ghi nhận: chữ ký đã KIỂM XONG với dữ liệu hiện có

Một phần của việc này **không cần dữ liệu mới** và đã làm xong: kiểm chữ ký có ổn định ở thang
giây không. Kết quả trên 2.256 mẫu đủ 8 cảm biến — tỉ lệ năng lượng 1X giữa các đầu đo có độ
lệch chuẩn **đều dưới 0,85%** (2003X 0,847% là lớn nhất; 2005Y chỉ 0,088%).

→ **Chữ ký không dao động ở thang giây**, nên việc lấy trung vị theo giờ **không làm mất thông
tin chữ ký** — nó chỉ làm mất nhiễu nền. Đây là bằng chứng biện minh lựa chọn bước 1 giờ.
*(Figure: `hqc_signature_and_limit.png`)*

## PHẦN C — NĂM CÂU HỎI CẦN TRẢ LỜI (không phải chuỗi dữ liệu)

| # | Câu hỏi | Vì sao quan trọng |
|---|---|---|
| **C.0** | **Hệ có lưu dữ liệu cadence 3 giây trong QUÁ KHỨ không, hay chỉ giữ gần đây?** Cụ thể: thử kéo `29VT-2001X\|1X Amp` bước 3 giây cho **8 giờ bất kỳ trong 20/02 – 22/03/2026** | **Quyết định B.7 làm được hay không.** Nếu archive giữ được thì hiệu chỉnh ngưỡng xong ngay; nếu không thì phải đi đường 2 hoặc 3 của B.7. **Đây là câu hỏi rẻ nhất và quyết định nhiều nhất trong v5.** |
| C.1 | **4 tag `29VT-2052/2053` bị bỏ với ghi chú "Configure — chưa cấu hình phía PI" đo gì?** | Nếu là đầu rung thật thì cần cấu hình phía PI mới kéo được; nếu là tag dự phòng không dùng thì bỏ là đúng. |
| C.2 | **Hệ có `2X Amp` không?** (sheet `P29202A_tag` có 1 lần chữ "2X") | Có 2X thì **phân biệt được mất cân bằng vs lệch trục**. Không có thì phần chẩn đoán chỉ dừng ở "1X trội hay không". |
| C.3 | **202B dừng từ bao giờ, và có kế hoạch chạy lại không?** | Quyết định có nên chờ 202B hay bỏ nó khỏi phạm vi. Nếu nó luân phiên với 202A thì có thể có đoạn chạy trong quá khứ. |
| C.4 | **Quy ước biên độ của PI: 0-peak, peak-to-peak hay RMS?** | Sai hệ số 2 nếu nhầm — ảnh hưởng mọi so sánh với ngưỡng ISO/API. |

## PHẦN D — BẢNG TỔNG HỢP

| # | Nội dung | Khoảng | Bước | Mở khóa |
|---|---|---|---|---|
| **B.1** | `1X Amp` + `1X Phase` mọi đầu rung, 4 máy | 01/10/2025 – 01/08/2026 | 10m | **Chữ ký vector — điểm vượt paper** |
| **B.2** | Rung + nhiệt P29201A và P29201B | 01/10/2025 – 01/08/2026 | 10m | **Nối rev02 với công việc đã làm** |
| B.3 | Vị trí trục `29XT-*` (Direct + Gap) | như B.2 | 10m | Kiểu hỏng "trục dịch vị trí" |
| B.4 | Run Hours + Status, 4 máy | 04/08/2024 – 05/08/2026 | 1 ngày | **Nhãn lead-time** |
| B.5 | Biến quá trình cụm MP | 01/10/2025 – 01/08/2026 | 10m | Cổng lọc riêng từng máy |
| B.6 | Direct + nhiệt khoảng cũ | 01/08/2024 – 30/09/2025 | 1h | Lead-time (phủ mốc reset) |
| **B.7** | Khối 8h cadence 3s **LÚC MÁY KHỎE** | **20/02 – 22/03/2026** | 3s | **Hiệu chỉnh ngưỡng kiểm soát** (nhiễu nền lệch 15,5×) |
| B.8 | Khối 8h cadence 3s **đa tải** | — | 3s | Chữ ký đa điều kiện |

## PHẦN E — NGÂN SÁCH MẪU SAU KHI CÓ B.1 + B.2

Với bước 10 phút, 304 ngày, **2 máy đang chạy** (P29201A + P29202A):

| Đầu vào | Số đặc trưng | Mẫu khả dụng | Tham số cho phép (3:1) | Kiến trúc lớn nhất |
|---|---|---|---|---|
| Chỉ Direct (rev02 hiện tại) | 8 + 16 nhiệt = 24 | 43.777 | ~14.600 | AE trung bình |
| **+ 1X Amp/Phase (B.1)** | 12×4 + 16 + 6×2 = **76** | 43.777 | ~14.600 | **AE 76-48-16-48-76 (~9.000 tham số)** |
| **+ per-machine gộp mẫu** | 38/máy | **87.554** | ~29.000 | **AE sâu / VAE** |

→ Có B.1 + B.2 là **đủ cho autoencoder/VAE**, tức tái hiện được kiến trúc paper trụ xếp tốt nhất,
và mô hình đủ lớn (30–120 KB) để **lượng tử hóa có ý nghĩa thật** (không còn "nhỏ như cái kẹo").

## PHẦN F — QUY TẮC KÉO (nhắc lại)
- **PI Point giá trị gốc**: đuôi `\|Direct`, `\|1X Amp`, `\|1X Phase`, `\|Temperature`, `\|Gap`
- **TUYỆT ĐỐI KHÔNG** `\|Trigger\|Current percent` (= 0 hằng số — bẫy đã làm 3 export vô dụng)
- Đường dẫn AF: attribute **cảm biến** dùng gạch chéo trước hệ con
  (`...\P29202A-MP BFW Pumps\HP BFWP|29VT-2017X|1X Amp`); attribute **máy** dùng `|` ngay sau tên element
- **Tên máy MP**: hậu tố `-MP BFW Pumps`, KHÔNG phải `-HP BFW Pumps`
- **Attribute bỏ hậu tố A/B**: sheet tag cho thấy nhãn `29VT-2017AX` nhưng attribute là `29VT-2017X` — giữ đúng quy ước này
- Mốc **tuyệt đối dạng text** (`01-Oct-2025 00:00:00`), không `*-304d`
- Mỗi nhóm **một sheet riêng**, không có gì dưới hàng tiêu đề (tránh `#SPILL!`)
- **Giới hạn Excel**: B.1 (4 máy × 40 chuỗi × 43.777 điểm ≈ 7 triệu giá trị) vượt 1.048.576 hàng/sheet → chia mỗi máy một sheet, hoặc xuất CSV
