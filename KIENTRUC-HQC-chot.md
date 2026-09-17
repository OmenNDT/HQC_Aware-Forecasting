# HQC_Aware-Forecasting — KIẾN TRÚC CHỐT (trước khi train)

> Chốt ngày 04/08/2026, sau khi khảo sát `PI Data.xlsx` (15 sheet, 10 nguồn) và đọc sâu
> paper trụ từ PDF gốc. Tài liệu này là mốc tham chiếu — mọi thay đổi sau phải ghi changelog.

## 0. Bài toán và mục tiêu
**Mục tiêu:** dự đoán sớm trạng thái bất thường có khả năng dẫn đến hư hỏng trên máy quay
(early-warning), máy **P29201A** (tổ tua-bin hơi + bơm cấp nước HP), 4 ổ đỡ × 2 hướng.

**Paper trụ:** *Health Monitoring of Air Compressors Using Reconstruction-Based Deep Learning
for Anomaly Detection with Increased Transparency*, Entropy 2021, 23, 83. DOI 10.3390/e23010083.
Học **không giám sát** — train chỉ trên dữ liệu bình thường.

## 1. Dữ liệu

| Bộ | File | Nội dung |
|---|---|---|
| **Train** | `Data/HQC_train_healthy.csv` | 1.307 giờ, 05/02–31/03/2026, KHÔNG nhãn |
| **Đánh giá** | `Data/HQC_eval_expert.csv` | 350 mẫu (150 bình thường + 200 bất thường), 01/04–31/07/2026, chuyên gia PDM xác nhận |

Nguồn: sheet `51_Vib180d` (rung) ghép `33_Aligned` (tải) trên lưới **1 giờ**.
Tập đánh giá **không chứa giờ nào đã dùng train** (chống rò rỉ).

## 2. QUYẾT ĐỊNH LỚN: tải là CỔNG LỌC, không phải biến đầu vào

**Đã sửa so với đề xuất ban đầu.** Lượt đầu tôi kết luận "tải biến thiên rộng → dùng
condition-aware (tải → dự đoán rung khỏe)". Sau khi làm sạch rác, số liệu nói ngược:

| Đo được (45.598 giờ chạy, dữ liệu sạch) | Kết luận |
|---|---|
| 90,9% thời gian tốc độ trong dải hẹp 4.750–4.830 rpm | tải gần như **một điểm vận hành** |
| 90,2% lưu lượng trong 27.000–29.500 | |
| CV thật: tốc độ 4,9% · áp 2,6% · nhiệt 6,9% | đều hẹp |
| Chỉ 9,1% ngoài dải — phần lớn là khởi động/dừng dần | không phải nhiều mức tải |

→ Không đủ đa dạng để học ánh xạ tải→rung. Thêm nữa tải phủ ngắn hơn cảm biến
(1 năm vs 3,3 năm) nên đưa vào sẽ **thu hẹp** khoảng dùng được.

**Tải dùng làm cổng lọc:** `lưu lượng 29FI2005 ≥ 20.000` **và** `≥6/8 kênh 1X Amp > 3 µm`
(ngưỡng máy-dừng từ báo cáo dữ liệu). Loại thêm vùng chuyển tiếp 28/05–13/06/2026.
Đúng nguyên tắc: lúc máy dừng không có gì để học.

Cách này cũng khớp paper trụ — họ đưa 14 cảm biến vào, không tách riêng tải.

## 3. Đầu vào: 16 cột cảm biến (chốt)
- 8 × `1X Amp` (biên độ, µm)
- 8 × `1X Phase` (pha, độ)

**Chuẩn hóa:**
- Amp → z-score theo trung bình/độ lệch chuẩn của **nền khỏe**
- Phase → **sin/cos** (pha là góc: 359° và 1° gần nhau, không được đưa số độ thô vào)
  → 8 pha thành 16 cột số ⇒ tổng **24 cột số** đầu vào

Đây là điểm vượt paper: paper chỉ có cảm biến **vô hướng** (áp, nhiệt, dòng, dầu);
ta có **vector rung** nên chữ ký mang nghĩa vật lý trực tiếp.

## 4. Mô hình: PCA + AE + VAE, chọn kích thước bằng learning curve (chốt)

| Mô hình | Vai trò | Trọng số (ước) | Đối chiếu paper |
|---|---|---|---|
| **PCA** | baseline (đã có từ M1) | ~64 | — |
| **AE** | tái tạo phi tuyến | ~600 | paper: acc 0,797 |
| **VAE** | tái tạo sinh | ~700 | paper: acc **1,00** (tốt nhất) |

**KHÔNG dùng ED-LSTM / ED-CNN / DBN** dù paper xếp ED-LSTM tốt nhất — chúng cần hàng nghìn
trọng số, vượt ngân sách với 1.307 mẫu. Paper có nhiều chuỗi hơn nên chạy được.
→ **Kích thước chọn bằng learning curve** (time-blocked, giữ 25% tuần khỏe cuối làm
validation), không bê nguyên kiến trúc paper. Nếu một kích thước overfit thì báo cáo nói rõ —
đó là kết quả có giá trị, paper không kiểm điều này.

### Bài học tuning từ paper (Discussion, phải tuân)
Nếu tối ưu hyperparameter quá mạnh, mô hình học "copy input→output" → tái tạo hoàn hảo
**cả** dữ liệu bình thường **lẫn** lỗi → **mất hẳn tín hiệu residual**.
→ Tiêu chí chọn KHÔNG phải "sai số tái tạo nhỏ nhất" mà là **"tái tạo tốt normal nhưng
residual TĂNG DẦN khi lỗi tiến triển"**.

## 5. Độ đo và đầu ra

| Tầng | Công thức | Nguồn |
|---|---|---|
| Residual | `RE = (1/N)·Σ\|xᵢ − x̂ᵢ\|` (MAE) | paper Eq.1 |
| Giới hạn kiểm soát | **SPE/Q** (Jackson-Mudholkar) + **T² Hotelling**, mức 99% | vượt paper (paper chỉnh ngưỡng tay) |
| Điểm sức khỏe | **0–100**: min-max → sigmoid → thang 100. Normal 0-40 · Warning 40-60 · Danger 60-100 | mượn paper §6.3 |
| Minh bạch | **contribution_j = 100·\|xⱼ−x̂ⱼ\| / RE** | paper Eq.3 |

**Bước dịch cuối** (contribution → chẩn đoán) do **tri thức cơ học rotor** làm, KHÔNG phải nhãn:

| Đặc trưng lệch | Suy luận | Việc sửa |
|---|---|---|
| 1X tăng, pha giữ | mất cân bằng | cân bằng lại rotor |
| 1X tăng, **pha quay dần** | điểm nặng di chuyển (nứt trục, mòn cánh) | dừng máy kiểm ngay |
| 2X trội | lệch trục | căn tâm khớp nối |

*(2X chưa có trong dữ liệu — hệ chỉ trích sẵn bậc 1X. Cần kiểm PI có tag `2X Amp` không.)*

## 6. ĐẶC TÍNH phải nêu rõ khi báo cáo (không phải lỗi)

Ổ **29VT-2003 ĐÃ mất cân bằng ngay trong cửa sổ nền** (1X Amp median 47,7 µm; xác nhận bởi
4 nguồn độc lập: 1X chiếm 97,9–98,5% năng lượng phổ, 2X/1X = 0,04–0,11, nhóm đối chứng 2005
cho phổ khác hoàn toàn, hai thuật toán FFT độc lập trùng khớp).

→ Mô hình coi mức đó là "bình thường của máy này" và **KHÔNG báo động ổ 2003**.
Nó chỉ báo cái **lệch khỏi nền** — thực tế là ổ **2001**.

Đây là đặc tính của phương pháp reconstruction: phát hiện **THAY ĐỔI**, không phát hiện
**MỨC TUYỆT ĐỐI xấu**. Muốn bắt cả 2003 cần thêm tầng đối chiếu ngưỡng tuyệt đối
(ISO 10816 / API 610). Nói rõ điều này là **điểm mạnh phương pháp luận**, không phải điểm yếu.

## 7. Nghiệm thu (3 cách, không phải 1)

| Cách | Cần gì | Trạng thái |
|---|---|---|
| **1. Bảng accuracy 350 mẫu** (như paper Bảng 9) | nhãn chuyên gia PDM | 🔶 đang gán |
| **2. Chỉ đúng ổ bất thường** — contribution có chỉ vào 2001 không? | bằng chứng vật lý | ✅ có ngay |
| **3. Lead-time trước mốc bảo trì** | dữ liệu phủ tới trước 31/05/2025 | ❌ phải kéo thêm |

**Về tính độc lập của nhãn:** nhãn ứng viên sinh từ **thống kê mô tả trên dữ liệu thô**
(dải p1–p99 của nền), **KHÔNG** từ residual mô hình — nếu không thì lập luận vòng tròn.
Sau khi chuyên gia điền, **ghi lại tỉ lệ chuyên gia sửa** như chỉ số minh bạch bắt buộc.

## 8. Sáu điểm vượt paper (lợi thế dữ liệu)

1. **Vector rung** 1X Amp + Phase — paper chỉ vô hướng
2. **Giới hạn kiểm soát thống kê** thay ngưỡng chỉnh tay (điểm paper **tự nhận** yếu)
3. **Nhiều máy**: 5 máy trong cụm, **2 cặp song song** (P29201A/B, P29202A/B) — paper 1 loại máy
4. **3 mốc run-to-failure** (P29201A 31/05/2025; P29201B 07/09/2024 + 21/05/2025) — paper 1 case, tự nhận hạn chế
5. **Cấu trúc cây theo hệ con** (tua-bin / bơm / 4 ổ đỡ) — paper **đề xuất làm tương lai**
6. **Triển khai nhúng** Int8 + MCU — paper không làm, khung môn học lại đòi

## 9. Ánh xạ vào 6 bước Embedded AI (khung môn học)

| Bước | Nội dung | Trạng thái |
|---|---|---|
| 1. Định nghĩa bài toán + chọn phần cứng | early-warning trên máy quay; MCU cạnh máy | ✅ |
| 2. Thu thập cảm biến + trích đặc trưng | 8 đầu rung → 1X Amp/Phase; cổng lọc bằng tải | ✅ |
| 3. Thiết kế + train mô hình (GPU/cloud) | PCA + AE + VAE, learning curve | 🔶 **bước tiếp** |
| 4. Nén mô hình (quantize/prune) | Int8 bộ dò nhẹ | ⬜ |
| 5. Triển khai C-array lên MCU | | ⬜ |
| 6. Kiểm latency/RAM/điện trên thiết bị | | ⬜ |

**Chia vai:** quantum (nếu quay lại) train trên GPU = nghiên cứu; bộ dò nhẹ deploy MCU = sản phẩm.
Hiện **quantum đang gác** — tập trung dự báo chuỗi thời gian / cảnh báo sớm.

## 10. Việc tiếp theo (theo thứ tự)
1. Train PCA + AE + VAE trên `HQC_train_healthy.csv`, learning curve chọn kích thước
2. Tính anomaly score 0–100 + contribution trên tập đánh giá
3. Nghiệm thu cách 2 (contribution có chỉ đúng ổ 2001?)
4. Khi chuyên gia trả file → nghiệm thu cách 1 + tính tỉ lệ chuyên gia sửa
5. Song song: kéo dữ liệu dài (Direct + nhiệt, 500+ ngày) để mở khóa lead-time
