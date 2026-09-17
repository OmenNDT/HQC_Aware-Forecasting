# HQC — PLAN YÊU CẦU DỮ LIỆU MỞ RỘNG (4 máy bơm)

> Lập 05/08/2026. Mục tiêu: mở rộng từ 1 máy / 24 đặc trưng lên **4 máy / 126 đặc trưng**,
> để mô hình đủ lớn cho việc lượng tử hóa **có ý nghĩa** (thay vì nén 864 byte — quá nhỏ để
> làm bài tập môn nhúng).

## 1. Vì sao phải mở rộng — nói bằng số

| | Hiện tại | Sau mở rộng |
|---|---|---|
| Máy | 1 (P29201A) | **4** (P29201A/B, P29202A/B) |
| Cảm biến vật lý | 21 | **57** |
| Chuỗi dữ liệu | 27 | **128** (106 rung/nhiệt + 22 quá trình) |
| Đặc trưng đầu vào mô hình | 24 | **126** |
| Mô hình | PCA k=6, **216 tham số, 864 byte** | AE/VAE, **18–31 nghìn tham số, 73–123 KB** |
| Nén Int8 | 864 B → 264 B (**vô nghĩa**) | 123 KB → **31 KB** (có ý nghĩa thật) |

**Vấn đề của mô hình hiện tại:** 216 tham số vừa cả ATtiny 2 KB RAM — nên bước "nén để nhúng"
không có nội dung để phân tích. Cần mô hình đủ lớn để việc nén **thật sự cần thiết**.

## 2. Kiểm kê 4 máy (từ sheet `70_MayTrongCum`)

| Máy | Hệ con | Đầu rung VT | Nhiệt TE | Vị trí XT | Chuỗi |
|---|---|---|---|---|---|
| **P29201A** | HP BFWP + **Turbine** | 8 | 10 | 3 | 40 |
| **P29201B** | Gear + HP BFWP + Motor | 4 | 6 | 2 | 22 |
| **P29202A-MP** | HP BFWP + Motor | 4 | 6 | 2 | 22 |
| **P29202B-MP** | HP BFWP + Motor | 4 | 6 | 2 | 22 |
| **TỔNG** | | **20** | **28** | **9** | **106** |

*(Số TE/XT của B và 2 máy MP là ước từ cấu trúc hệ con — cần xác nhận khi kéo.)*

## 3. ⚠ MỘT PHÁT HIỆN QUAN TRỌNG VỀ NGÂN SÁCH MẪU

**Gộp 4 máy thành 126 cột KHÔNG tự động cho phép mô hình lớn hơn.**

Lý do: 4 máy × 270 ngày = **vẫn chỉ 270 ngày lịch**. Gộp cột tăng số **cột** (24 → 126) mà
**không tăng số hàng**. Về ngân sách trọng số thì đây là **tệ hơn**, không tốt hơn.

| Kiến trúc trên 126 cột | Tham số | Cần mẫu (3:1) | = số ngày (bước 1h) | Khả thi? |
|---|---|---|---|---|
| PCA k=6 | 1.134 | 3.402 | 142 ngày | ✅ |
| PCA k=12 | 1.890 | 5.670 | 236 ngày | ✅ |
| PCA k=20 | 2.898 | 8.694 | 362 ngày | 🔶 sát (archive 270d) |
| AE 126-64-16-64-126 | 18.698 | 56.094 | **2.337 ngày** | ❌ |
| VAE tương đương | 19.738 | 59.214 | **2.467 ngày** | ❌ |

→ **Với bước 1 giờ, không đủ mẫu cho autoencoder trên 126 cột.**

### Hai đòn bẩy giải quyết

**Đòn bẩy 1 — Bước lấy mẫu (mạnh nhất):**

| Bước | Mẫu (4 máy × 270 ngày) | Tham số cho phép | Kiến trúc lớn nhất |
|---|---|---|---|
| 1 giờ | 25.920 | 8.640 | PCA k≤20, AE nhỏ |
| **10 phút** | **155.520** | **51.840** | **AE sâu, VAE, ED-LSTM** |
| 1 phút | 1.555.200 | 518.400 | mọi kiến trúc |

→ Kéo bước **10 phút** thay 1 giờ là đủ cho **cả 6 kiến trúc của paper trụ**.
**CÂU PHẢI HỎI:** archive CBM có lưu bước 10 phút không? (dữ liệu hiện có kéo ở 1h — chưa biết bước gốc)

**Đòn bẩy 2 — Mô hình dùng chung trọng số cho các máy cùng loại ("per-pump"):**
Ba máy B/202A/202B cấu trúc giống nhau (bơm + motor, 4 đầu rung). Thay vì gộp 126 cột,
huấn luyện **một mô hình 26 cột dùng chung**, mỗi máy góp mẫu riêng:
- Mẫu = **4 máy × 270 ngày × 24 = 25.920 giờ** (gấp 4 lần)
- AE 26-32-8-32-26 (2.326 tham số) → cần 73 ngày × 4 máy ✅
- AE 26-48-16-4-16-48-26 (4.370 tham số) → cần 137 ngày × 4 máy ✅

*Ưu điểm phụ: mô hình học "bơm khỏe trông thế nào" nói chung → phát hiện được máy nào lệch khỏi
đồng đội, không cần nền khỏe riêng từng máy. Đây cũng là đường gỡ cho vấn đề "không có nền khỏe".*

## 4. DANH SÁCH KÉO — theo ưu tiên

### ⭐ ƯU TIÊN 0 — Trả lời 3 câu trước khi kéo hàng loạt (rẻ, quyết định mọi thứ)

| # | Câu hỏi | Cách kiểm | Vì sao quyết định |
|---|---|---|---|
| 0.1 | Archive CBM lưu bước bao nhiêu? | Kéo `29VT-2001X\|1X Amp` **1 ngày** ở bước **10 phút** và **1 phút**, xem có giá trị khác nhau hay lặp | Quyết định được dùng AE/VAE hay chỉ PCA |
| 0.2 | 3 máy mới có đủ tag rung không? | `PIAFSearch` liệt kê attribute của P29201B, P29202A, P29202B | Nếu thiếu 1X Phase thì đặc trưng giảm |
| 0.3 | Độ sâu archive của 3 máy mới? | Kéo `\|1X Amp` ở `*-270d`, `*-365d`, `*-547d` xem tới đâu | Quyết định khoảng thời gian chung |

**Làm mục 0 trước — 3 truy vấn nhỏ, tiết kiệm hàng giờ kéo sai.**

### ⭐ ƯU TIÊN 1 — Bộ chính 4 máy

| Nội dung | Chi tiết |
|---|---|
| **Rung** | 20 đầu VT × (`\|Direct`, `\|1X Amp`, `\|1X Phase`) = **60 chuỗi** |
| **Nhiệt ổ đỡ** | ~28 tag `29TE-...\|Temperature` = **28 chuỗi** |
| **Vị trí trục** | 9 đầu XT × (`\|Direct`, `\|Gap`) = **18 chuỗi** |
| **Khoảng** | **07/11/2025 → 05/08/2026** (270 ngày = độ sâu archive 1X) |
| **Bước** | **10 phút** nếu mục 0.1 xác nhận có; nếu không thì 1 giờ |
| **Tại sao** | Bộ dữ liệu chính. 270 ngày là tối đa archive 1X Amp/Phase cho phép. |

### ⭐ ƯU TIÊN 2 — Biến quá trình 2 cụm

| Nội dung | Chi tiết |
|---|---|
| **Tag** | 11 biến cụm HP (đã có danh sách) + ~11 biến tương ứng cụm MP (`29FI`, `29PI`, `29SIC`, `29LI`, `29TI` của 202A/B) |
| **Khoảng** | cùng kỳ ưu tiên 1 |
| **Bước** | 10 phút |
| **Tại sao** | Cổng lọc (loại giờ máy dừng/tải thấp) cho **từng máy riêng** — 4 máy có lịch chạy khác nhau, không dùng chung cổng được. |

### ƯU TIÊN 3 — Run Hours 4 máy (nhãn nghiệm thu)

| Nội dung | Chi tiết |
|---|---|
| **Tag** | `<máy>\|Running Time\|Run Hours - Since Last Service` + `Status` × 4 máy |
| **Khoảng** | **04/08/2024 → 05/08/2026** (2 năm, tối đa) |
| **Bước** | 1 ngày |
| **Tại sao** | Tìm mốc reset = nhãn lead-time. Đã biết 3 mốc (A: 31/05/2025; B: 07/09/2024 + 21/05/2025); 2 máy MP chưa có reset trong tầm 365 ngày → kéo 2 năm xem có thêm. |

### ƯU TIÊN 4 — Direct + nhiệt phủ mốc bảo trì (lead-time)

| Nội dung | Chi tiết |
|---|---|
| **Tag** | 20 × `\|Direct` + 28 × `\|Temperature` + 9 × `\|Gap` (KHÔNG cần 1X — archive không với tới) |
| **Khoảng** | **01/08/2024 → 31/07/2025** (phủ cả 3 mốc reset đã biết) |
| **Bước** | 1 giờ |
| **Tại sao** | `1X Amp/Phase` chỉ sâu 270 ngày, **không với tới mốc reset** (cách 430–700 ngày). Nhưng `Direct`/`Temperature`/`Gap` sâu ~1.150 ngày → phủ được. Đây là cách duy nhất đo lead-time thật. |

### ƯU TIÊN 5 — Khối cadence 3 giây, đa tải (chữ ký chẩn đoán)

| Nội dung | Chi tiết |
|---|---|
| **Nội dung** | 3–4 khối 8 giờ, cadence 3 giây, đủ 20 đầu rung × (Direct + 1X Amp + 1X Phase) |
| **Điều kiện** | **mỗi khối một mức tải khác** — hiện 2 khối đều ~4.765 rpm |
| **Tại sao** | Thư viện "chữ ký khỏe ở từng mức tải". Cũng là dữ liệu cho nhánh **1 phút / 3 giây** nếu muốn mô hình rất lớn. |

## 5. Ước lượng khối lượng

| Ưu tiên | Chuỗi | Điểm mỗi chuỗi | Tổng giá trị |
|---|---|---|---|
| 1 (bước 10 phút, 270 ngày) | 106 | 38.880 | **~4,1 triệu** |
| 1 (bước 1 giờ, 270 ngày) | 106 | 6.480 | ~690 nghìn |
| 2 (quá trình, 10 phút) | 22 | 38.880 | ~855 nghìn |
| 3 (Run Hours, 1 ngày) | 8 | 730 | ~6 nghìn |
| 4 (Direct+nhiệt, 1 giờ, 365 ngày) | 57 | 8.760 | ~500 nghìn |

**Lưu ý Excel:** 4,1 triệu giá trị vượt giới hạn 1.048.576 hàng của một sheet.
→ Chia **mỗi máy một sheet** (hoặc mỗi nhóm cảm biến một sheet), hoặc xuất CSV trực tiếp.

## 6. Mô hình sau mở rộng — biên độ nén thật

| Kiến trúc | fp32 | int8 | ATmega328 2KB | STM32F103 20KB | ESP32 520KB |
|---|---|---|---|---|---|
| PCA k=6 hiện tại (24 cột) | 0,8 KB | 0,2 KB | ✅ | ✅ | ✅ |
| PCA k=12 (126 cột) | 7,4 KB | 1,8 KB | ❌ | ✅ | ✅ |
| AE 26-48-16-4-16-48-26 | 17,1 KB | 4,3 KB | ❌ | ✅ | ✅ |
| **AE 126-64-16-64-126** | **73,0 KB** | **18,3 KB** | ❌ | ❌ | ✅ |
| **VAE 126-64-16-64-126** | **77,1 KB** | **19,3 KB** | ❌ | ❌ | ✅ |
| **AE 126-96-32-8-32-96-126** | **123,0 KB** | **30,8 KB** | ❌ | ❌ | ✅ |

→ Với AE/VAE trên 126 cột, **nén Int8 trở thành bắt buộc** để vừa ESP32, và **vẫn không vừa
STM32F103** — tức có ràng buộc thật để phân tích. Đây đúng là "biên độ nén" cần cho môn học:
phải bàn đánh đổi kích thước ↔ độ chính xác ↔ phần cứng, không phải nén cho có.

## 7. Việc mở rộng này còn giải được vấn đề khác

| Vấn đề đang treo | Mở rộng 4 máy giúp thế nào |
|---|---|
| **Không có nền khỏe** (ổ 2001 leo suốt 180 ngày) | 3 máy khác làm **nền đối chứng chéo** — mô hình per-pump học "bơm khỏe nói chung" |
| **Chỉ 1 case run-to-failure** | 4 máy → tối đa 6+ mốc reset (paper trụ chỉ có 1 và tự nhận hạn chế) |
| **Không phân biệt được kiểu hỏng** | Nhiều máy → nhiều kiểu hỏng khác nhau (ổ 2005 nghi lệch trục 2X/1X=0,74) |
| **Mô hình quá nhỏ để nhúng có ý nghĩa** | 126 cột → 18–31 nghìn tham số |

## 8. Quy tắc kéo (nhắc lại)
- **PI Point giá trị gốc**: đuôi `\|Direct`, `\|1X Amp`, `\|1X Phase`, `\|Temperature`, `\|Gap`
- **TUYỆT ĐỐI KHÔNG** `\|Trigger\|Current percent` (=0 hằng số — bẫy đã làm 3 export vô dụng)
- Đường dẫn AF: attribute **cảm biến** dùng gạch chéo trước hệ con
  (`...\P29202A-MP BFW Pumps\HP BFWP|29VT-xxxx|1X Amp`); attribute **máy** dùng `|` ngay sau tên element
- **Lưu ý tên máy MP**: hậu tố là `-MP BFW Pumps`, KHÔNG phải `-HP BFW Pumps`
- Mốc **tuyệt đối dạng text** (`07-Nov-2025 00:00:00`), không `*-270d`
- Mỗi nhóm **một sheet riêng**, không có gì dưới hàng tiêu đề (tránh `#SPILL!`)
