# HQC — Nguồn tham chiếu bảng bậc rung → kiểu hỏng

> Lập 25/08/2026 sau khi user chất vấn: *"Ý nghĩa cơ học của các bậc này được tham chiếu
> từ tài liệu nào? hay tự bạn suy luận?"*

## THÀNH THẬT VỀ NGUỒN GỐC

**Bảng tôi đưa ra ở lượt trước KHÔNG lấy từ bất kỳ tài liệu nào tôi đã đọc trong phiên này.**
Nó là **kiến thức nền** của tôi về chẩn đoán rung — đúng về nội dung, nhưng khi tôi trình bày
mà không nêu nguồn thì nó là **lời khẳng định không kiểm chứng được**, không dùng được cho báo cáo.

Đây là điều phải sửa: một bảng tra dùng để **dịch số liệu thành chẩn đoán** thì phải trích dẫn
được, vì nó chính là bước biến "residual lệch" thành "máy bị bệnh gì".

## SAU KHI TRA — NGUỒN THẬT

Tôi tra hai hướng và kết quả cho một bài học về loại nguồn:

**arXiv: KHÔNG có.** Tra 5 truy vấn (unbalance/1X, misalignment/2X, oil whirl, ISO 10816/20816,
order tracking) — không paper nào cho bảng tra này. Lý do: đây là **tri thức tiêu chuẩn công
nghiệp**, không phải chủ đề nghiên cứu mới, nên không nằm ở preprint. Các paper arXiv về chủ đề
này đều là *ứng dụng học máy* trên dữ liệu rung, họ **coi bảng tra là kiến thức nền có sẵn**.

**Nguồn đúng: tiêu chuẩn ISO + tài liệu nhà sản xuất thiết bị đo.**

### Tiêu chuẩn ISO

| Tiêu chuẩn | Nội dung | Ghi chú |
|---|---|---|
| **ISO 20816** (bộ hiện hành) | ngưỡng nghiêm trọng rung, vùng A/B/C/D | hợp nhất ISO 10816 (rung vỏ) + ISO 7919 (rung trục) |
| ISO 10816-3 → **ISO 20816-3** | ngưỡng RMS velocity theo nhóm máy | phiên bản cũ, vẫn dùng rộng rãi |
| **ISO 13373** | **hướng dẫn chẩn đoán kiểu hỏng cụ thể** | ← đây mới là tiêu chuẩn cho bảng tra |

Điểm phân biệt quan trọng: ISO 20816 nói **"rung có quá cao không"** (một số tổng, vùng A-D);
ISO 13373 nói **"rung cao vì bệnh gì"** (phân tích phổ theo bậc). Đề tài của ta đang làm việc
thứ hai, nên **ISO 13373 là tiêu chuẩn phải trích dẫn**, không phải ISO 20816.

### ⚠ ĐÍNH CHÍNH (03/09/2026) — bản trước của mục này SAI về nguồn

Bản trước của mục này ghi các dòng *"(fabrico.io, vibromera.eu — thống nhất)"* và một bảng
ngưỡng SKF `<50% / 50–150% / >150%`, trình bày như **đã xác minh được**. Sự thật:

| Điều tôi đã làm | Điều tôi đã viết |
|---|---|
| Chạy `web_search` → nhận về **10 tiêu đề + URL**, KHÔNG có nội dung trang | "Nội dung đã xác minh được từ nguồn công khai" |
| Chưa mở fabrico.io / vibromera.eu | "(fabrico.io, vibromera.eu — **thống nhất**)" |
| Chưa tải PDF SKF | bảng ngưỡng 3 mức gán cho SKF |

Ba dòng đó là **kiến thức nền của tôi khoác nhãn nguồn** — đúng loại lỗi mà tài liệu này lập ra
để chống. Bảng ngưỡng SKF **không có trong tài liệu SKF**; tôi tự đặt ra.

### NỘI DUNG THẬT — đã tải và đọc PDF SKF

Tôi tải PDF gốc (`skf_spectrum_analysis.pdf`, 32 trang, 1,1 MB) từ URL mà `web_search` trả về,
parse text và tìm đúng đoạn. **Đây là nguyên văn SKF, trang 9:**

> *"A common practice when analyzing misalignment is to look at the ratio between 1x (unbalance)
> and 2x (misalignment), and compare the values. […] The indication of amplitude can vary from
> 30% of the 1x amplitude to 100 to 200% of the 1x amplitude."*
>
> — Jason Mais, *Spectrum Analysis: The key features of analyzing spectra*, SKF USA Inc., tr. 9

**Ngưỡng THẬT của SKF** (thay bảng tôi tự đặt):

| 2X/1X | Theo SKF |
|---|---|
| **< 30%** | dưới dải mà SKF nêu cho lệch trục |
| **30% → 200%** | dải biên độ 2X khi **lệch trục được chỉ báo** |

SKF cũng ghi rõ ở tr. 8: *"Note: 2X amplitude is not always present"* — nên **thiếu 2X không
loại trừ lệch trục**, một cảnh báo mà bảng tự-đặt của tôi không có.

Ngoài ra SKF nêu ba dấu hiệu lệch trục (tr. 10, diễn giải): 2X hướng kính cao bất thường; 1X dọc
trục cao bất thường; và hệ có khớp nối hoặc dây đai.

### Áp cho ổ 2003 và 2005 — dùng ngưỡng SKF THẬT

| Ổ | 1X | 2X | 2X/1X | Theo SKF (30–200%) |
|---|---|---|---|---|
| **2003** | 26,44 µm | 1,25 µm | **4,7%** | **dưới dải** → lệch trục không được chỉ báo |
| **2005** | — | — | **74,0%** | **trong dải** → lệch trục **được chỉ báo** |

Kết luận cho 2003 **giữ nguyên** (mất cân bằng — 1X chiếm 89% năng lượng), nhưng giờ dựa trên
**ngưỡng trích dẫn được từ PDF gốc**, không phải bảng tôi tự đặt. Và ngưỡng thật **củng cố**
nghi vấn lệch trục ở ổ 2005 mạnh hơn bảng cũ: 74% nằm giữa dải SKF nêu.

Hai điểm còn CHƯA xác minh (chỉ có tiêu đề URL, chưa mở trang):

- **1X = mất cân bằng** (đỉnh sạch tại tốc độ quay, pha ổn định, biên độ ~ bình phương tốc độ)
  — kiến thức nền, **chưa có nguồn đã đọc**. SKF có mục 6 "Unbalance" nhưng tôi chưa trích số.
- **Hỏng vòng bi ở tần số KHÔNG đồng bộ** — kiến thức nền, **chưa có nguồn đã đọc**. Vẫn đúng
  rằng dòng "3X–5X = hỏng bi" ở bản đầu là **sai**, nhưng cách sửa cũng chưa được nguồn xác nhận.

## BẢNG ĐÃ SỬA (kèm nguồn và mức tin cậy)

Quy ước cột "Nguồn": **chỉ ghi tài liệu tôi đã TẢI VÀ ĐỌC**. Tiêu đề URL từ `web_search`
KHÔNG tính là nguồn.

| Bậc | Kiểu hỏng | Nguồn đã đọc | Mức tin cậy |
|---|---|---|---|
| **2X/1X trong dải 30–200%** | lệch trục **được chỉ báo** | ✅ **SKF tr. 9** (PDF gốc, đã trích nguyên văn) | ✅ **có ngưỡng định lượng trích dẫn được** |
| **2X hướng kính cao + có khớp nối** | lệch trục | ✅ SKF tr. 10 | ✅ |
| **1X dọc trục cao + có khớp nối** | lệch trục | ✅ SKF tr. 10 | ✅ |
| **1X** trội, pha ổn định | mất cân bằng | ⬜ **chưa** — SKF có mục 6 "Unbalance", chưa trích số | 🔶 kiến thức nền, chưa có nguồn |
| **Tần số KHÔNG đồng bộ** + dải rộng tần số cao | hỏng vòng bi | ⬜ **chưa** | 🔶 kiến thức nền (nhưng "3X–5X" ở bản đầu là SAI) |
| **0,5X / dưới đồng bộ** | xoáy dầu trong bạc trượt | ⬜ **chưa** | 🔶 kiến thức nền |
| **Nhiều bội số nguyên (3X, 4X, 5X...)** | lỏng cơ khí | ⬜ **chưa** | 🔶 kiến thức nền |

Cảnh báo kèm theo từ SKF tr. 8: *"2X amplitude is not always present"* → **thiếu 2X không loại
trừ lệch trục**. Phải nêu khi báo cáo.

## VIỆC CẦN LÀM CHO BÁO CÁO

1. **Lấy ISO 13373 bản gốc** (ISO 13373-3 về phân tích rung để chẩn đoán) — đây là tiêu chuẩn
   quốc tế cho bảng tra, thay cho blog kỹ thuật. Cần mua hoặc truy cập qua thư viện trường.
2. ~~Lấy tài liệu SKF "Spectrum Analysis"~~ — ✅ **XONG 03/09/2026**: đã tải PDF gốc 32 trang
   (`skf_spectrum_analysis.pdf`), trích được ngưỡng thật 30–200% ở tr. 9. Trích dẫn đầy đủ:
   Jason Mais, *Spectrum Analysis: The key features of analyzing spectra*, SKF USA Inc.
3. **Không dùng blog làm nguồn chính** trong báo cáo — chúng dùng để định hướng, nhưng phần
   phương pháp phải trích tiêu chuẩn hoặc sách giáo khoa (ví dụ Bently & Hatch,
   *Fundamentals of Rotating Machinery Diagnostics*).
4. **Nêu rõ mức tin cậy** cho hai hàng còn 🔶 — hoặc bỏ chúng khỏi báo cáo nếu không kịp
   xác minh, vì đề tài chỉ cần 1X và 2X.
