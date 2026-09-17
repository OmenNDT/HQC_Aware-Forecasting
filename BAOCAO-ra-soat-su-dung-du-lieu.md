# HQC — RÀ SOÁT MỨC SỬ DỤNG DỮ LIỆU

> Trả lời câu: **kết quả mới nhất có dùng hết dữ liệu đang có chưa?**
> **KHÔNG. Đang dùng khoảng 0,2% tổng bản ghi, và 25,3% của nguồn chính.**
> Mọi con số đã xác minh bằng cách đọc file.

## 1. Kết quả mới nhất dùng những gì

| | |
|---|---|
| Nguồn | sheet `51_Vib180d` (rung 1X) + `33_Aligned` (tải) của `PI Data.xlsx` |
| Train | **743 giờ**, 20/02 – 22/03/2026 (30 ngày) |
| Eval | **350 mẫu**, 01/04 – 31/07/2026 |
| Cảm biến | **8** đầu rung (2001X/Y, 2003X/Y, 2005X/Y, 2007X/Y) |
| Đặc trưng | 8 `1X Amp` + 8 `1X Phase` → 16 sin/cos = **24 cột** |
| Mô hình | PCA k=6, 216 tham số |

## 2. Bảng mức sử dụng từng nguồn

| Nguồn | Bản ghi | Bước | Đã dùng | Tỉ lệ |
|---|---|---|---|---|
| A. Direct 5 năm (23 cảm biến) | 114.392 | ~8,2h | **0** | **0%** |
| **B. `51_Vib180d` (1X Amp+Phase, 8 đầu)** | **4.319** | 1h | **1.093** | **25,3%** |
| C. `rev02 34_Vibration` (202A/B, Direct) | 43.777 | 10 phút | **0** | **0%** |
| D. `33_Aligned` (11 biến quá trình) | 52.561 | 10 phút | chỉ cổng lọc | — |
| E. Khối 3 giây đêm (~16h) | 244.160 | 3 giây | **0** | **0%** |
| F. Khối 3 giây ngày (~8h) | 247.030 | 3 giây | **0** | **0%** |
| G. Waveform 4 file | 20 bản ghi | 16.949 Hz | **0** | **0%** |
| **TỔNG** | **~702.000** | | **1.093** | **~0,2%** |

*Ghi chú: E/F/G có được dùng làm **bằng chứng chẩn đoán** (phổ ổ 2003), chỉ là chưa dùng để train.*

## 3. Ba cơ hội chưa khai thác, xếp theo giá trị

### ⭐⭐⭐ Cơ hội 1 — Chấm điểm TOÀN BỘ chuỗi thay vì 350 mẫu lẻ

| | |
|---|---|
| Giờ sau nền khỏe (23/03 – 04/08/2026) | **3.230** |
| Đã chấm (tập eval) | 350 (**10,8%**) |
| **Chưa chấm** | **2.880 (89,2%)** |

**Đang mất gì:** không có **đường cong residual liên tục** — chỉ có 350 điểm rời rạc.
Hệ quả cụ thể: biểu đồ kiểm soát hiện tại (`hqc_M1_control_chart.png`) đang vẽ trên **dữ liệu
nhiệt 5 năm của mô hình M1 cũ**, chưa có bản nào trên dữ liệu 1X của mô hình hiện tại.

**Chi phí:** gần như bằng 0 — mô hình đã train xong, chỉ cần chạy suy luận trên 2.880 giờ còn lại.
**Được gì:** biểu đồ kiểm soát liên tục 5 tháng, thấy được residual leo theo thời gian, và
**có thể phát hiện đợt bất thường mà 350 mẫu lấy mẫu thưa đã bỏ sót.**

### ⭐⭐⭐ Cơ hội 2 — Khối 3 giây CÓ `1X Amp` + `1X Phase` (cùng đặc trưng đang dùng)

Xác minh bằng cách quét toàn file:

| | Khối đêm | Khối ngày |
|---|---|---|
| Data-source không phải `Trigger` | 218 | 217 |
| Chuỗi `1X Amp` | **32** | **32** |
| Chuỗi `1X Phase` | **16** | **16** |
| Điểm đo mỗi chuỗi | **3.600** | ~3.600 |
| Tổng điểm 1X | **57.457** | tương đương |

**Đây là dữ liệu CÙNG LOẠI đặc trưng mô hình đang dùng, mật độ gấp ~1.200× (3 giây vs 1 giờ),
và chưa dùng để train một chút nào.**

**Được gì:**
- **Ngân sách mẫu**: 3.600 mẫu/chuỗi × 2 khối = ~7.200 mẫu ở độ phân giải giây — cho phép mô hình
  lớn hơn nhiều so với 743 mẫu hiện tại
- **Chữ ký ổn định trong ngày**: xem 1X Amp/Phase có dao động trong 16 giờ không (hiện chỉ biết
  ở độ phân giải giờ)
- **Đo được nhiễu nền thật** — cần cho việc đặt ngưỡng kiểm soát chính xác

**Giới hạn phải nói rõ:** hai khối chỉ cách nhau 1 ngày và **cùng mức tải ~4.765 rpm**, nên không
dựng được thư viện chữ ký đa điều kiện. Chúng dùng để nghiên cứu **độ phân giải**, không phải **độ dài**.

### ⭐ Cơ hội 3 — `Direct` 5 năm làm trục dài bổ trợ

114.392 bản ghi, 23 cảm biến, 5 năm — **hoàn toàn chưa dùng** trong kết quả mới nhất.

**Vì sao chưa dùng:** lấy mẫu không đều (~8,2h), không join được lưới 1 giờ của 1X; và chỉ có
`Direct` (vô hướng), không có pha.

**Nhưng có giá trị riêng:** đây là nguồn **duy nhất phủ tới mốc reset 31/05/2025** (1X chỉ sâu
270 ngày, không với tới). Dùng được cho **một mô hình thứ hai** trên trục nhiệt/Direct để đo
lead-time — độc lập với mô hình 1X.

## 4. Ba việc đề xuất, theo thứ tự

| # | Việc | Chi phí | Được gì |
|---|---|---|---|
| **1** | Chấm điểm 3.230 giờ → biểu đồ kiểm soát liên tục trên dữ liệu 1X | rất thấp (mô hình đã có) | Đường cong residual 5 tháng; có thể lộ đợt bất thường bị bỏ sót |
| **2** | Nạp khối 3 giây, train mô hình ở độ phân giải giây | trung bình (phải parse 2 file 34 MB) | Ngân sách mẫu ~7.200; đo nhiễu nền; kiểm chữ ký ổn định trong ngày |
| **3** | Mô hình thứ hai trên `Direct` + nhiệt 5 năm, phủ mốc reset | cao (làm sạch + nền khỏe riêng) | **Lead-time thật** — thứ duy nhất hiện chưa chứng minh được |

## 5. Nói thẳng về mức độ

Việc chỉ dùng 25,3% nguồn chính **không phải lỗi** — nó là hệ quả của cách chia
train/eval theo đúng khung paper trụ (nền khỏe để train, mẫu lấy thưa để chuyên gia gán nhãn).
Nhưng có hai chỗ đúng là **bỏ sót thật**:

1. **Không chấm điểm toàn chuỗi** — chỉ 350/3.230 giờ. Đây là bỏ sót rõ nhất, và sửa gần như
   không tốn gì.
2. **Không dùng khối 3 giây dù nó chứa đúng đặc trưng đang cần** — 57.457 điểm 1X nằm không,
   trong khi mô hình đang bị giới hạn kích thước vì thiếu mẫu.

Cả hai đều làm được **ngay với dữ liệu hiện có**, không cần chờ anh kéo thêm.
