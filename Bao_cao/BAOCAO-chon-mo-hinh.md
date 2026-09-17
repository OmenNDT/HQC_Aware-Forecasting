# HQC — Chọn mô hình + Điểm bất thường + Minh bạch cảm biến

## 1. Learning curve chọn kích thước (time-blocked, 25% giờ khỏe cuối làm validation)

Train 980 giờ · validation 327 giờ (18/03–31/03/2026). **Đã kiểm cửa sổ validation vẫn thuần
khỏe** (mọi kênh lệch <3,5% so phần train) → sai số validation là thước đo tổng quát hóa hợp lệ.

| Mô hình | Trọng số | val MAE | gap (val−train) |
|---|---|---|---|
| PCA k=3 | ~72 | 0,723 | +0,250 |
| PCA k=4 | ~96 | 0,662 | +0,249 |
| **PCA k=6** | ~144 | **0,542** | **+0,223** |
| AE 8-4-8 | 492 | 0,679 | +0,283 |
| AE 16-8-4-8-16 | 1.164 | 0,684 | +0,329 |

**Hai autoencoder đều KHÔNG thắng PCA** dù nhiều trọng số hơn 3–16 lần, và gap lớn hơn —
dấu hiệu overfit đúng như ngân sách trọng số dự đoán với 1.307 mẫu. Cả hai còn **tệ đi ở
điểm dữ liệu đầy đủ nhất** (n=980: AE 8-4-8 0,636→0,679).

→ Xác nhận nguyên tắc "số trọng số phải cân với số mẫu" bằng thực nghiệm, không bằng quy tắc ngón tay.

## 2. NHƯNG: sai số tái tạo nhỏ nhất KHÔNG phải tiêu chí chọn

Đây là điểm paper trụ cảnh báo (Discussion): tối ưu quá mạnh → mô hình copy input→output →
tái tạo hoàn hảo **cả** normal **lẫn** lỗi → mất tín hiệu. Tiêu chí đúng: **residual phải TĂNG
khi có lỗi**.

| Mô hình | val MAE | RE bình thường | RE bất thường | **tỉ số** | AUC |
|---|---|---|---|---|---|
| **PCA k=3** | 0,723 | 2,220 | 2,942 | **1,33×** | **0,811** |
| PCA k=4 | 0,662 | 1,984 | 1,945 | 0,98× | 0,671 |
| PCA k=6 | **0,542** | 1,491 | 1,409 | **0,95×** | 0,702 |
| AE 8-4-8 | 0,679 | 2,084 | 2,532 | 1,22× | 0,779 |
| AE 16-8-4-8-16 | 0,684 | 1,959 | 2,442 | 1,25× | 0,783 |

**PCA k=6 có sai số tái tạo TỐT NHẤT nhưng tỉ số 0,95× — nghĩa là nó tái tạo dữ liệu bất
thường CŨNG TỐT như dữ liệu bình thường, mất hẳn khả năng phát hiện.** Đúng y cái bẫy paper nêu.

→ **CHỌN PCA k=3** (tỉ số 1,33×, AUC 0,811) — kích thước nhỏ nhất, tách tốt nhất.
Đây là ví dụ cụ thể cho báo cáo: *sai số tái tạo và khả năng phát hiện là hai thứ khác nhau.*

## 3. Điểm sức khỏe 0–100 (paper §6.3)

Hiệu chỉnh trên **thang log** của residual validation khỏe (p5–p95×3), vì thang tuyến tính
gốc bị bão hòa (mọi mẫu eval tràn lên 98–100).

| Nhóm | Điểm median |
|---|---|
| Nền train | 16,1 |
| Validation khỏe | 27,6 |
| Eval "bình thường" (nhãn ứng viên) | **57,5** |
| Eval "bất thường" lệch LÊN | **84,3** |

Phân bố 3 vùng: bất thường → 198 Danger + 2 Warning · bình thường → 59 Danger + 82 Warning + 9 Normal.

### ⚠ Phát hiện: nhóm "bình thường" của tập eval KHÔNG cùng phân bố với nền
Nhóm này có điểm median 57,5 (vùng Warning), không phải Normal. Kiểm ra: 1X Amp của nó cao
hơn nền **4,8–4,9%** ở ổ 2001 và 2,4% ở 2003 — **cả cụm cùng dịch nhẹ**.

→ **Luật gán nhãn ứng viên có điểm yếu hệ thống:** nó kiểm từng cảm biến riêng lẻ so dải nền,
nên bỏ qua dịch chuyển đồng loạt nhỏ. Mô hình bắt được vì nó học **tương quan** giữa các cảm biến.
→ Đây là lý do **nhãn chuyên gia là bắt buộc**, không thể dùng nhãn luật làm sự thật nền.

## 4. Minh bạch: đóng góp từng cảm biến (paper Eq.3)

Gộp 3 cột (Amp, sin, cos) về từng đầu đo:

| Đầu đo | Đóng góp |
|---|---|
| **29VT-2001Y** | **23,0%** |
| **29VT-2001X** | **15,8%** |
| 29VT-2003X | 14,6% |
| 29VT-2003Y | 14,4% |
| 29VT-2005Y | 10,6% |
| 29VT-2007Y | 8,0% |
| 29VT-2005X | 7,1% |
| 29VT-2007X | 6,4% |

Đếm "đầu đo đóng góp nhất" trong 193 mẫu bất thường: **2001Y 138 lần**, 2003X 38, 2003Y 16, 2001X 1.

**NGHIỆM THU CÁCH 2 — ĐẠT.** Mô hình học nếp khỏe, **không được dạy** khái niệm mất cân bằng
hay biết ổ nào có vấn đề, nhưng tự chỉ vào **ổ 2001** — đúng ổ mà phân tích xu hướng 180 ngày
độc lập cho thấy đang thay đổi (+68% Feb→May). Ổ 2003 đóng góp trung bình (14,6%) vì mức cao
của nó đã nằm trong nền — đúng như đặc tính đã nêu ở kiến trúc.

## 5. Đính chính con số tôi nói sai
Lượt trước tôi nói "trong 200 mẫu bất thường có 67 dòng lệch dấu âm". **Sai** — có **7 dòng
lệch âm**; 67 là số dòng có |lệch| < 32%.

## 6. Giới hạn phải nêu
- AUC 0,811 chấm theo **nhãn ứng viên** (luật thống kê), **chưa** phải nhãn chuyên gia. Con số
  cuối phải tính lại sau khi chuyên gia PDM trả file.
- Chưa có SPE/T² với giới hạn kiểm soát 99% cho bộ đặc trưng mới (đã làm ở M1 với bộ nhiệt/vị trí).
- Chưa đo lead-time (cần dữ liệu phủ tới trước mốc reset 31/05/2025).
