# HQC — YÊU CẦU DỮ LIỆU v6

## Đang có gì

| Nguồn | Tên thiết bị | Cảm biến | Khoảng | Bước |
|---|---|---|---|---|
| `51_Vib180d` — **đang dùng train** | **P29201A-HP BFW Pumps** | 8 rung (1X Amp + Phase) | 05/02–04/08/2026 (180 ngày) | 1 giờ |
| `33_Aligned` — cổng lọc | cụm HP (dùng chung A/B) | 11 biến quá trình | 01/08/2025–01/08/2026 | 10 phút |
| File 5 năm — chưa dùng | **P29201A-HP BFW Pumps** | 23 (Direct + nhiệt + XT) | 27/07/2021–21/07/2026 (1.820 ngày) | ~8,2 giờ |
| `rev02 34_Vibration` — chưa dùng | **P29202A-MP** + **P29202B-MP** | 24 (Direct + nhiệt) | 01/10/2025–01/08/2026 | 10 phút |
| 2 khối 3 giây — chưa train | **P29201A-HP BFW Pumps** | 21 (rung + nhiệt + XT) | 28–29/07/2026 (16h + 8h) | 3 giây |

**Tổng 57 cảm biến / 3 thiết bị:** P29201A-HP 33 · P29202A-MP 12 · P29202B-MP 12.
Chỉ 8 vào mô hình (14%), **cả 8 đều thuộc P29201A**.

Hai máy của cụm **chưa có dữ liệu**: `P29201B-HP BFW Pumps` (có 2 mốc reset — nguồn nhãn
lead-time) và `B29101 - Force Draft Fan`. Máy `P29202B-MP` có dữ liệu nhưng **đứng yên**
(0,2% điểm vượt ngưỡng máy-chạy) nên không train được.

## Cần kéo — 4 mục

### ⭐ 1a. `1X Amp` + `1X Phase` cho **P29201A** — lùi thêm 60 ngày
- **Khoảng:** **07/12/2025 → 05/02/2026** (60 ngày) · **bước 10 phút**
- **Dùng để làm gì — 3 việc cụ thể:**

| Việc | Vì sao cần đúng khoảng này |
|---|---|
| **Tìm nền khỏe thật** | Nền đang dùng (20/02–22/03/2026) là **bình nguyên giữa hai đợt leo**, cao hơn mức đầu dữ liệu 51%. Đoạn 60 ngày này là **phần archive duy nhất còn chưa khai thác** — nếu ổ 2001 phẳng ở mức thấp thì có nền khỏe thật. |
| **Biết đợt suy giảm bắt đầu từ khi nào** | Dữ liệu hiện có bắt đầu 05/02/2026 khi ổ 2001 **đã đang leo** (+3,23 µm/tháng, p=1,3e-09). Lùi 60 ngày để thấy điểm khởi phát. |
| **Nâng mật độ mẫu 6×** | Hiện 1X ở bước 1 giờ (4.205 mẫu/180 ngày). Bước 10 phút cho 6× mẫu → cho phép mô hình lớn hơn, và **đo được nhiễu nền** mà bước 1 giờ làm mượt mất. |

- **⚠ Giới hạn cứng:** archive 1X sâu **~270 ngày** → tính từ hôm nay chỉ với tới **07/12/2025**.
  Yêu cầu lùi xa hơn (v6 bản trước ghi 01/10/2025) là **67 ngày ngoài archive** — kéo sẽ ra rỗng.

### ⭐ 1b. `1X Amp` + `1X Phase` cho **P29201B** — kiểm trước, kéo sau
- **Việc cần làm trước:** kiểm xem hệ có **lưu 1X của B trong archive** khi B còn chạy không.
- **Vì sao phải kiểm:** B **hiện đang dừng** (`Steady Running = False`, `Direct` chỉ 0,68–0,92 µm,
  dưới ngưỡng máy-chạy 3 µm) nên `1X Amp` hiện trả **`Bad`** — đúng về vật lý: máy không quay thì
  không có "một lần mỗi vòng" để đo. B đã chạy 2.684 giờ nên **từng** có 1X; câu hỏi là archive
  có giữ hay không.
- **Và một giới hạn nữa:** B chỉ có **4/8 đầu rung** (`29VT-2001X/Y`, `2003X/Y`); bốn đầu
  `2005X/Y`, `2007X/Y` báo `Attribute not found` (B dùng Motor + Gear thay tua-bin).
- **⚠ Hai mốc reset của B nằm NGOÀI archive 1X:** 07/09/2024 cách **726 ngày**, 21/05/2025 cách
  **470 ngày** — cả hai vượt 270 ngày. → **Không đo lead-time bằng 1X của B được**; việc đó thuộc
  mục 4 (`Direct` + nhiệt, archive 1.150 ngày).

### ⭐ 2. Khối 3 giây **lúc máy khỏe**
- **Khoảng bắt buộc:** trong **20/02 – 22/03/2026** · 2–3 khối 8 giờ · 8 đầu rung
- **Vì sao:** ngưỡng kiểm soát hiện tại tính từ nhiễu bước 1 giờ (0,028 µm), nhiễu thật ở 3 giây là 0,432 µm — **gấp 15,5×**. 2 khối đang có ở tháng 7, cách nền khỏe 127 ngày, máy đã +27% → không dùng được.

### 3. Run Hours + Status, 4 máy
- **Khoảng:** 04/08/2024 → 05/08/2026 · **bước 1 ngày**
- **Vì sao:** biến này reset về 0 mỗi lần bảo trì = **nhãn duy nhất** để đo lead-time.

### 4. `Direct` + nhiệt + `Gap` phủ mốc bảo trì
- **Khoảng:** 01/08/2024 → 30/09/2025 · **bước 1 giờ**
- **Vì sao:** 1X chỉ sâu 270 ngày, không với tới mốc reset 31/05/2025 (cách 430 ngày). Direct/nhiệt sâu 1.150 ngày → phủ được.

## Cần trả lời — 3 câu

1. **Hệ có lưu 3 giây trong quá khứ không?** Thử kéo `29VT-2001X|1X Amp` bước 3 giây, 8 giờ bất kỳ trong 20/02–22/03/2026. → quyết định mục 2 làm được hay không. **Rẻ nhất, quyết định nhiều nhất.**
2. **Hệ có `2X Amp` không?** → có thì phân biệt được mất cân bằng vs lệch trục liên tục (hiện chỉ làm được ở 3 mốc có waveform).
3. **Biên độ PI là 0-peak, peak-to-peak hay RMS?** → sai hệ số 2 nếu nhầm.

## Quy tắc kéo
- Tag phải kết thúc ở `|Direct`, `|1X Amp`, `|1X Phase`, `|Temperature`, `|Gap`
- **KHÔNG** lấy `|Trigger|Current percent` — bằng 0 hằng số, đã làm 3 bản export vô dụng
- Nhãn tag có hậu tố máy (`29VT-2017AX`) nhưng **attribute bỏ hậu tố** (`29VT-2017X`)
- Máy MP có hậu tố `-MP BFW Pumps`, không phải `-HP`
- Mốc tuyệt đối dạng text (`01-Oct-2025 00:00:00`), không dùng `*-270d`
- Mục 1a nhỏ: 16 chuỗi × 8.640 điểm = **138.240 giá trị**, dạng wide chỉ 8.640 hàng × 17 cột → **một sheet là đủ**, không lo `#SPILL!`

## Không cần kéo cho việc này
- **Chữ ký ổn định:** đã kiểm xong, std tỉ lệ < 0,85% → bước 1 giờ không làm mất chữ ký
- **Khối 3 giây đa tải:** hoãn — chỉ cần khi làm thư viện chữ ký nhiều điều kiện, không phải bây giờ
