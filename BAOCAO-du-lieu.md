# HQC — BÁO CÁO DỮ LIỆU

> Kiểm kê thực tế trên đĩa, ngày 25/08/2026. Trả lời hai câu: **dữ liệu có những gì** và
> **đang dùng những gì**. Mọi con số trong báo cáo này đã xác minh bằng cách đọc file, không
> lấy từ tài liệu mô tả.

═══════════════════════════════════════════════════════════════════
# PHẦN I — DỮ LIỆU CÓ NHỮNG GÌ

## 1. Tổng quan 4 thư mục

| Thư mục | Số file | Dung lượng | Vai trò |
|---|---|---|---|
| `Dataraw/` | 14 | ~321 MB | Bản xuất gốc từ PI / System 1 — **không sửa** |
| `Dataclean/` | 13 | ~7,8 MB | Bản làm sạch trung gian + kết quả M1 |
| `Data/` | 7 | ~0,64 MB | **Bộ chính thức dùng train + eval** |
| `papers/` | 27 | ~15,9 MB | PDF/text paper trụ + 3 paper neural-operator |

## 2. Chín nguồn dữ liệu gốc trong `Dataraw/`

| # | File | MB | Nội dung | Khoảng | Bước | Trạng thái |
|---|---|---|---|---|---|---|
| A | `P29201A-5y-2026.csv` | 5,5 | **23 điểm đo** (10 rung VT + 11 nhiệt TE + 3 vị trí XT), attribute `Direct` | 27/07/2021 – 21/07/2026 (**5 năm**) | không đều (~8,2h) | ✅ dùng được |
| B | `PI Data.xlsx` | 48,0 | Workbook PI Datalink 15 sheet — có `33_Aligned` (11 biến quá trình), `51_Vib180d` (**1X Amp + Phase, 8 đầu, 180 ngày**), `52_RunHours`, `60_P29201B`, `70_MayTrongCum`, `99_BaoCao` | 08/2025 – 08/2026 | 10m / 1h / 1 ngày | ✅ **nguồn chính hiện tại** |
| C | `PI Data rev02.xlsx` | 49,8 | Workbook 11 sheet — `34_Vibration` (2 máy MP, bước **10 phút**, 304 ngày), 3 sheet danh mục tag | 01/10/2025 – 01/08/2026 | 10m | 🔶 xem mục 4 |
| D | `P29201A-HP BFW Pumps.xml` | 130,0 | SpreadsheetML, cảm biến CBM **chỉ có `Trigger\|Current percent` = 0 hằng số** | 30/05 – 29/06/2026 | 1h | ❌ **không dùng được** |
| E | `...-1M-process.csv` | 20,1 | 83 tag; **chỉ biến quá trình có giá trị thật**, CBM rung/nhiệt = trigger 0 | 30/05 – 02/06/2026 | 1m | 🔶 chỉ biến quá trình |
| F | `...-7D.csv` | 0,05 | **Export lỗi** — 314 dòng, mỗi tag 1 điểm, timestamp tới 20/10/2026 (tương lai) | — | — | ❌ **bỏ** |
| G | `...-8h-9pm28-7-5am-29-7.csv` | 32,6 | **34 chuỗi CBM giá trị thật**: 8 đầu rung × (Direct + 1X Amp + 1X Phase) + nhiệt | 28/07 21:09 – 29/07 13:13 (~16h) | **3 giây** | ✅ **giàu nhất** |
| H | `...-8h-4am29-7-12am-29-7.csv` | 34,3 | khối 8h ban ngày, cùng loại nguồn G | 29/07/2026 | 3 giây | ✅ dùng được |
| I | `sep-ware-29VT-2001/2003/2005/2007.csv` | 0,15 mỗi | **Waveform thô** 2048 điểm/bản ghi, 5 bản ghi mỗi file | 3 mốc: 27/04/2023, 27/08/2023, 25/07/2026 | 16.949 Hz | ✅ nhưng **rất thưa** |

*Kèm `INDEX.md` (125 nghìn ký tự) — mục lục chi tiết do người dùng lập.*

### ⚠ Một sai lệch trong `INDEX.md` cần sửa
`INDEX.md` ghi file 5 năm chứa *"duy nhất điểm đo 29VT-2007Y"*. Kiểm thực tế: file có **24 block
`Machine Name`, 23 điểm đo duy nhất** (một block `29VT-2007Y` bị trùng). Đây đúng là cái bẫy tôi
từng mắc — đọc block header đầu rồi tưởng cả file một cảm biến.

## 3. Ba loại dữ liệu rung — khác nhau về bản chất

| Loại | Là gì | Mật độ | Dùng cho |
|---|---|---|---|
| **`Direct`** | biên độ rung tổng (một số) | dày, 5 năm | phát hiện "rung to/nhỏ" |
| **`1X Amp` + `1X Phase`** | biên độ + pha thành phần một-lần-mỗi-vòng (**vector**) | 180 ngày @1h, hoặc 16h @3s | **chữ ký chẩn đoán** — phân biệt kiểu hỏng |
| **Waveform** | tín hiệu dịch chuyển theo thời gian, 2048 điểm | **chỉ 3 mốc ngày** | phân tích phổ đầy đủ (tính được mọi bậc) |

`1X Amp/Phase` chính là **kết quả FFT của waveform, rút gọn còn thành phần 1X** — nên dày hơn
waveform nhưng chỉ có một bậc.

## 4. Đánh giá `PI Data rev02.xlsx` — tiến bộ và thiếu sót

**✅ Tiến bộ lớn nhất: bước 10 phút đã xác nhận có.** `34_Vibration` 43.777 hàng, 304 ngày,
chất lượng rất tốt (khuyết 4,01%, **0 rác `6,4e-17`, 0 sentinel `−32768`**).

**❌ Ba thiếu sót:**

| Thiếu | Chi tiết |
|---|---|
| **Không có `1X Amp`/`1X Phase`** | Kiểm cả 3 sheet danh mục: xuất hiện **0 lần**. Chỉ có `Direct` → mất chữ ký vector |
| **Thiếu hai máy quan trọng nhất** | Không có dữ liệu rung/nhiệt của **P29201A** (máy đã có toàn bộ phân tích) và **P29201B** (có 2 mốc reset) |
| **Máy 202B đứng yên** | Chỉ **77/43.777 điểm (0,2%)** vượt ngưỡng máy-chạy 3 µm; rung ổn định 1,0–1,5 µm suốt 304 ngày → **không train được** |

→ Thực tế rev02 chỉ thêm **1 máy dùng được** (202A), không phải 3.

## 5. Kiểm kê cụm máy (từ sheet `70_MayTrongCum`)

| Máy | Hệ con | Run Hours hiện tại | Mốc reset (nhãn lead-time) |
|---|---|---|---|
| **P29201A** | HP BFWP + **Turbine** | 491,24 h | **1** — 31/05/2025 (trước đó chạy 162,27 h) |
| **P29201B** | Gear + HP BFWP + Motor | 2.684,35 h | **2** — 07/09/2024 (9.377 h), 21/05/2025 (5.951 h) |
| P29202A-MP | HP BFWP + Motor | 1.394,84 h | 0 (tăng đơn điệu) |
| P29202B-MP | HP BFWP + Motor | 1.593,63 h | 0 (dừng từ ~180 ngày) |
| B29101 (quạt gió) | B29101 + MB29101 | 3.273,08 h | 0 |

**Tổng 3 mốc reset từ 2 máy** — paper trụ chỉ có 1 case và tự nhận là hạn chế.

## 6. Độ sâu archive theo attribute (ràng buộc cứng)

| Attribute | Độ sâu | Với tới mốc reset A (cách 430 ngày)? |
|---|---|---|
| `1X Amp`, `1X Phase` | **~270 ngày** | ❌ **không** |
| `Direct`, `Gap`, `Temperature` | ~1.150 ngày | ✅ có |

→ Đây là lý do **không thể đo lead-time bằng 1X**; phải dùng `Direct` + nhiệt cho khoảng cũ.

═══════════════════════════════════════════════════════════════════
# PHẦN II — ĐANG DÙNG NHỮNG GÌ

## 7. Bốn file trong `Data/` — bộ chính thức

| File | Hàng × Cột | Khoảng | Vai trò |
|---|---|---|---|
| `HQC_train_healthy.csv` | 1.307 × 28 | 05/02 – 31/03/2026 (54 ngày) | nền train **bản đầu — ĐÃ THAY** |
| **`HQC_train_healthy_flat.csv`** | **743 × 28** | **20/02 – 22/03/2026 (30 ngày)** | **nền train ĐANG DÙNG** |
| **`HQC_eval_expert.csv`** | **350 × 38** | **01/04 – 31/07/2026** | **tập đánh giá — chờ chuyên gia PDM** |
| `HQC_eval_scored_flat.csv` | 350 × 15 | 01/04 – 31/07/2026 | kết quả chấm điểm (score + contribution) |

**Nguồn:** sheet `51_Vib180d` (rung 1X Amp/Phase) ghép `33_Aligned` (biến quá trình) của
`PI Data.xlsx` — **KHÔNG dùng rev02** (vì rev02 thiếu 1X và thiếu máy A).

## 8. Đặc trưng đầu vào mô hình đang dùng

| Nhóm | Số cột | Xử lý |
|---|---|---|
| `1X Amp` × 8 đầu rung | 8 | z-score theo nền khỏe |
| `1X Phase` × 8 đầu rung | 8 → **16** | chuyển **sin/cos** (pha là góc: 359° và 1° gần nhau) |
| **Tổng đầu vào** | **24 cột số** | |
| Biến quá trình (11 biến) | 0 | **chỉ làm CỔNG LỌC**, không vào mô hình |

**Vì sao tải không vào mô hình:** đo được 90,9% thời gian tốc độ nằm trong dải hẹp
4.750–4.830 rpm → tải gần như một điểm vận hành, không đủ đa dạng để học ánh xạ tải→rung.

**Cổng lọc:** `lưu lượng 29FI2005 ≥ 20.000` **và** `≥6/8 kênh 1X Amp > 3 µm`, loại vùng chuyển
tiếp 28/05–13/06/2026.

## 9. Mô hình đang dùng

**PCA k=6 trên 24 đặc trưng** — 216 tham số (864 byte float32).

Chọn bằng learning curve + tiêu chí paper trụ ("residual phải TĂNG khi có lỗi"):

| Mô hình | val MAE | tỉ số tách | AUC |
|---|---|---|---|
| PCA k=3 | 0,645 | 1,53× | 0,823 |
| PCA k=4 | 0,571 | 1,71× | 0,827 |
| **PCA k=6** | **0,462** | **1,88×** | **0,834** |
| AE 8-4-8 (492 tham số) | 0,579 | 1,71× | 0,842 |
| AE 16-8-4-8-16 (1.164) | 0,577 | 1,71× | 0,830 |

Lượng tử hóa Int8 per-channel: **864 B → 264 B**, AUC 0,8337 → 0,8339 (không mất gì).
Mã C đã biên dịch, khớp Python sai lệch < 1e-5. Dấu chân: 384 B Flash + 216 B RAM + 1.149 B mã.

## 10. Đang KHÔNG dùng gì, và vì sao

| Không dùng | Lý do |
|---|---|
| File 5 năm (nguồn A) | Lấy mẫu **không đều** (~8,2h), không join được lưới 10 phút; chỉ có `Direct` |
| `PI Data rev02.xlsx` | Thiếu `1X Amp/Phase`, thiếu máy P29201A/B, 202B đứng yên |
| XML tháng (nguồn D) | Cảm biến CBM chỉ có `Trigger\|Current percent` = 0 hằng số |
| File 7D (nguồn F) | Export lỗi |
| Waveform (nguồn I) | Chỉ **3 mốc ngày** — quá thưa để train; dùng làm **bằng chứng chẩn đoán** ổ 2003 |
| Khối 3 giây (nguồn G, H) | Chỉ ~16h + 8h; **cả hai cùng tải ~4.765 rpm** nên chưa dựng được thư viện chữ ký đa điều kiện |
| Biến quá trình trong mô hình | Chỉ làm cổng lọc (xem mục 8) |

═══════════════════════════════════════════════════════════════════
# PHẦN III — VẤN ĐỀ CÒN TREO

## 11. Vấn đề gốc: không có nền khỏe thật

Hồi quy trên chính cửa sổ nền cho thấy **toàn bộ 180 ngày không chứa đoạn khỏe nào của ổ 2001**:

| Đoạn | Median 1X Amp 2001X | Xu hướng |
|---|---|---|
| 05–11/02/2026 (đầu dữ liệu) | 11,60 µm | **+3,23 µm/tháng** (p = 1,3e-09) — **đã đang leo** |
| 11–19/02/2026 | 12,2 → 17,0 µm | leo **+50% trong 8 ngày** |
| 20/02–22/03/2026 (nền đang dùng) | 17,46 µm | +0,21 µm/tháng — phẳng |
| 04–27/05/2026 | 28,10 µm | leo tiếp |

→ Nền đang dùng là **bình nguyên GIỮA hai đợt leo**, cao hơn mức đầu dữ liệu **51%**.
Mô hình sẽ bỏ đợt leo thứ nhất (tháng 2) — vốn sớm hơn và đúng là thứ early-warning cần bắt.

**Bằng chứng đây là hiện tượng thật:** tải hoàn toàn không đổi suốt tháng 2 (4.815 rpm, lưu lượng
28,3–29,0 nghìn); chỉ 2001X/Y nhảy (+41,6%/+37,7%), 6 đầu đo khác trong ±2,6%.

## 12. Ba chỗ dữ liệu chặn tiến độ

| # | Vấn đề | Cần gì để gỡ |
|---|---|---|
| 1 | Không có nền khỏe | `1X Amp/Phase` lùi thêm **91 ngày** (07/11/2025 – 05/02/2026) — archive còn cho phép |
| 2 | Không đo được lead-time | `Direct` + nhiệt phủ **01/03 – 31/07/2025** (mốc reset 31/05/2025) |
| 3 | Mô hình quá nhỏ để lượng tử hóa có ý nghĩa | `1X Amp/Phase` cho 4 máy, bước 10 phút → 76 đặc trưng thay 24 |

*Chi tiết yêu cầu: xem `YEUCAU-du-lieu-v5.md`.*

## 13. Bằng chứng đã có (không cần thêm dữ liệu)

| Kết luận | Bằng chứng |
|---|---|
| **Ổ 29VT-2003 mất cân bằng** | 4 nguồn độc lập: 1X chiếm 97,9–98,5% năng lượng phổ; 2X/1X = 0,04–0,11 (loại trừ lệch trục); không có họ harmonics bậc cao; nhóm đối chứng 2005 cho phổ hoàn toàn khác (1X chỉ 56,6%) |
| **Ổ 29VT-2001 đang tiến triển** | +68% (Feb→May), tải không đổi; contribution của mô hình chỉ vào 2001 ở **192/193 mẫu** |
| **Ổ 29VT-2005 nghi lệch trục** | 2X/1X = 0,740 — cần điều tra riêng |
| Cơ chế reconstruction đứng vững | Tỉ số tách 1,88×, false-alarm kiểm soát, contribution chỉ đúng ổ mà 4 nguồn độc lập đã xác nhận |
