# HQC — BÁO CÁO YÊU CẦU DỮ LIỆU

> Lập ngày 04/08/2026, sau khi train thử trên dữ liệu hiện có và phát hiện **vấn đề gốc**.
> Tài liệu này trả lời ba câu: **cần dữ liệu gì · khoảng thời gian nào · tại sao**.

## PHẦN 1 — VẤN ĐỀ GỐC: không có "nếp khỏe" trong dữ liệu hiện có

Phương pháp của đề tài (reconstruction-based, theo paper trụ Entropy 2021) đòi **một đoạn dữ
liệu máy khỏe** để mô hình học "bình thường trông thế nào". Kiểm tra cho thấy **toàn bộ 180
ngày dữ liệu rung hiện có KHÔNG chứa đoạn khỏe nào của ổ 29VT-2001**:

| Đoạn | Median 1X Amp ổ 2001X | Xu hướng |
|---|---|---|
| 05–11/02/2026 (đầu dữ liệu, 132 giờ) | 11,60 µm | **+3,23 µm/tháng** (p = 1,3e-09) — ĐANG LEO |
| 11–19/02/2026 | 12,2 → 17,0 µm | leo nhanh **+50% trong 8 ngày** |
| 20/02–22/03/2026 | 17,46 µm | +0,21 µm/tháng — phẳng |
| 04–27/05/2026 | 28,10 µm | leo tiếp |
| 01/07–04/08/2026 | 21,17 µm | sau khởi động lại |

**Dữ liệu bắt đầu khi máy đã trong quá trình suy giảm.** Đoạn "phẳng" 20/02–22/03 là một
**bình nguyên GIỮA hai đợt leo**, cao hơn mức đầu dữ liệu 51% — không phải trạng thái bình
thường của thiết bị.

**Hệ quả nếu dùng nền này:** mô hình coi 17,5 µm là bình thường → chỉ bắt được đợt leo **thứ
hai** (tháng 5), bỏ hoàn toàn đợt **thứ nhất** (tháng 2) — vốn sớm hơn và đúng là thứ
early-warning cần bắt. Mức "khỏe thật" của ổ 2001 **không xác định được** từ dữ liệu hiện có.

Bằng chứng đây là hiện tượng thật, không phải do vận hành:
- Tải **hoàn toàn không đổi** suốt tháng 2 (4.815 rpm, lưu lượng 28,3–29,0 nghìn)
- Chỉ ổ 2001X/Y nhảy (+41,6% / +37,7%); **6 đầu đo khác trong ±2,6%** → sự kiện khu trú

---

## PHẦN 2 — DỮ LIỆU CẦN, THEO ƯU TIÊN

### ⭐ ƯU TIÊN 1 — Lùi 1X Amp/Phase thêm 91 ngày (giải vấn đề gốc)

| Nội dung | Chi tiết |
|---|---|
| **Tag** | `29VT-2001X/Y, 2003X/Y, 2005X/Y, 2007X/Y` × (`\|1X Amp`, `\|1X Phase`) — 16 chuỗi |
| **Khoảng** | **07/11/2025 → 05/02/2026** (91 ngày) |
| **Bước** | 1 giờ |
| **Tại sao** | Archive 1X Amp/Phase sâu ~270 ngày; dữ liệu hiện có chỉ dùng 179 ngày → **còn 91 ngày chưa khai thác**. Đây là đoạn duy nhất còn khả năng chứa nền khỏe thật của ổ 2001. |
| **Kết quả kỳ vọng** | (a) nếu 2001 phẳng ở mức thấp (~11 µm hoặc thấp hơn) → **có nền khỏe, giải quyết trọn vẹn**; (b) nếu đã leo từ trước → biết đợt suy giảm bắt đầu từ khi nào, và phải chuyển sang khung "tốc độ thay đổi" |

**Đây là mục rẻ nhất và giá trị cao nhất.** 16 chuỗi × 91 ngày × 1 giờ ≈ 35 nghìn giá trị.

### ⭐ ƯU TIÊN 2 — Lùi biến quá trình cho khớp

| Nội dung | Chi tiết |
|---|---|
| **Tag** | 11 biến của sheet `33_Aligned` (`29SIC2001`, `29SIC2001A`, `29FI2005/2006`, `29PI2011/2012`, `29PDI2007A`, `29LI2002A`, `29TI2030/2031/2026A`) |
| **Khoảng** | **07/11/2025 → 01/08/2025** — tức lùi từ 01/08/2025 về 07/11/2025 (thực tế đã có 01/08/2025 trở đi, cần **thêm phần trước 01/08/2025** nếu làm ưu tiên 3) |
| **Bước** | 10 phút (như hiện tại) |
| **Tại sao** | Tải dùng làm **cổng lọc** (loại giờ máy dừng / tải thấp). Không có tải cùng kỳ thì không lọc được đoạn 91 ngày mới. |

*Ghi chú: `29SIC2001A` chỉ có ~180 ngày archive → có thể không phủ được; nếu thiếu thì bỏ biến này.*

### ⭐ ƯU TIÊN 3 — Direct + nhiệt ổ đỡ phủ mốc bảo trì (mở khóa lead-time)

| Nội dung | Chi tiết |
|---|---|
| **Tag** | 8 × `29VT-....\|Direct`, 3 × `29XT-....\|Direct` + `\|Gap`, 10 × `29TE-....\|Temperature` |
| **Khoảng** | **01/03/2025 → 31/07/2025** (5 tháng, phủ trước-sau mốc reset 31/05/2025) |
| **Bước** | 1 giờ |
| **Tại sao** | **1X Amp/Phase KHÔNG với tới mốc reset**: archive 270 ngày, mốc cách 430 ngày. Nhưng **Direct/Gap/Temperature sâu ~1150 ngày** → phủ được. Đây là cách duy nhất đo **lead-time thật** (hệ báo động trước mốc bảo trì bao lâu). |
| **Kèm** | biến quá trình cùng kỳ, bước 10 phút, để làm cổng lọc |

### ƯU TIÊN 4 — Máy song song P29201B (nền đối chứng + 2 case nữa)

| Nội dung | Chi tiết |
|---|---|
| **Tag** | 4 đầu rung của B × (`Direct`, `1X Amp`, `1X Phase`) + nhiệt ổ đỡ + biến quá trình |
| **Khoảng** | **01/08/2024 → 30/09/2024** và **01/04/2025 → 30/06/2025** (phủ 2 mốc reset 07/09/2024 và 21/05/2025) |
| **Bước** | 1 giờ |
| **Tại sao** | (a) thêm **2 case run-to-failure** — paper trụ chỉ có 1 case và tự nhận là hạn chế; (b) máy cùng loại, cùng điều kiện nhà máy → nền đối chứng. **Lưu ý:** B chỉ có 4 đầu rung (không có tua-bin), nên chỉ so được phần bơm. |

### ƯU TIÊN 5 — Khối 3 giây ở điều kiện tải KHÁC (chữ ký đa điều kiện)

| Nội dung | Chi tiết |
|---|---|
| **Nội dung** | 2–3 khối 8 giờ, cadence 3 giây, 8 đầu rung × (Direct + 1X Amp + 1X Phase) |
| **Điều kiện** | **mỗi khối ở một mức tải khác nhau** — hiện có 2 khối nhưng **cả hai đều ~4.765 rpm** |
| **Tại sao** | Để dựng thư viện "chữ ký khỏe ở từng mức tải" — cần cho phần chẩn đoán. Hiện chưa làm được vì thiếu đa dạng tải. |

### Mục hỏi thêm (không phải chuỗi dữ liệu)
1. **Hệ có tag `2X Amp` không?** Hiện chỉ có 1X. Không có 2X thì **không phân biệt được mất cân bằng với lệch trục** — hạn chế phần chẩn đoán.
2. **Ngưỡng cảnh báo do ai đặt, theo tiêu chuẩn nào** (ISO 10816? API 610?). Báo cáo dữ liệu ghi ngưỡng hiện tại **sinh tự động** theo quy luật (Based ± hằng số) → đối chiếu mất ý nghĩa.
3. **Lịch sử can thiệp ổ 2001** — có sửa/cân bằng/thay bi gì trong 11/2025–02/2026 không? Đây là câu giải thích trực tiếp đợt leo tháng 2.
4. **Quy ước biên độ 1X Amp của PI**: 0-peak, peak-to-peak hay RMS? (sai hệ số 2 nếu nhầm)

---

## PHẦN 3 — BẢNG TÓM TẮT

| # | Dữ liệu | Khoảng | Bước | Mở khóa được gì |
|---|---|---|---|---|
| 1 | 1X Amp + Phase, 8 đầu | 07/11/2025 – 05/02/2026 | 1h | **Nền khỏe thật** (vấn đề gốc) |
| 2 | 11 biến quá trình | cùng kỳ mục 1 | 10m | Cổng lọc cho mục 1 |
| 3 | Direct + Gap + nhiệt ổ đỡ | 01/03 – 31/07/2025 | 1h | **Lead-time thật** (nghiệm thu mạnh nhất) |
| 4 | Bộ đầy đủ máy P29201B | 08–09/2024 và 04–06/2025 | 1h | 2 case run-to-failure + nền đối chứng |
| 5 | Khối 8h cadence 3s | tải khác nhau | 3s | Chữ ký chẩn đoán đa điều kiện |

## PHẦN 4 — NẾU KHÔNG KÉO ĐƯỢC THÌ SAO

Đề tài **vẫn làm được** nhưng phải đổi khung, và phải nói rõ giới hạn:

| Thiếu | Hệ quả | Cách đi vòng |
|---|---|---|
| Mục 1 (nền khỏe) | Không có "bình thường" để so | Chuyển sang phát hiện **tốc độ thay đổi** (đạo hàm) thay vì lệch khỏi nền — bài toán khác, phải tra literature lại |
| Mục 3 (lead-time) | Không đo được "báo trước bao lâu" | Nghiệm thu bằng **bằng chứng vật lý** (contribution có chỉ đúng ổ 2001 không) — đã làm được, kết quả 192/193 mẫu |
| Mục 4 (máy B) | Chỉ 1 máy | Giữ nguyên phạm vi 1 máy, nêu là hạn chế (giống paper trụ) |
| Mục 5 (đa tải) | Không dựng được thư viện chữ ký | Chẩn đoán ở một điều kiện tải, nêu giới hạn |

## PHẦN 5 — QUY TẮC KÉO (nhắc lại, tránh bẫy cũ)
- Lấy **PI Point giá trị gốc**: tag kết thúc ở `\|Direct`, `\|1X Amp`, `\|1X Phase`, `\|Temperature`, `\|Gap`
- **TUYỆT ĐỐI KHÔNG** lấy đuôi `\|Trigger\|Current percent` — là % tiệm cận ngưỡng, = 0 hằng số (bẫy đã làm 3 bản export dài trước vô dụng)
- Cú pháp đường dẫn AF: attribute của **cảm biến** dùng gạch chéo trước hệ con
  (`...\P29201A-HP BFW Pumps\HP BFWP|29VT-2003X|1X Amp`); attribute của **máy** dùng `|` ngay sau tên element
- Dùng **mốc tuyệt đối dạng text** (`07-Nov-2025 00:00:00`), không dùng `*-270d` (mỗi tag lệch 0–152 giây)
- Đặt mỗi nhóm trên **sheet riêng**, không có gì bên dưới hàng tiêu đề (tránh `#SPILL!`)
