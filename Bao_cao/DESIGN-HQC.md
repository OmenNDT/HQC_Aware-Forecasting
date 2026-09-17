# HQC_Aware-Forecasting — Bản thiết kế v2 (theo khung Embedded AI 6 bước)

> Máy P29201A (tổ tua-bin hơi + bơm HP BFW), giám sát tình trạng đa cảm biến.
> Mục tiêu: DỰ ĐOÁN SỚM trạng thái bất thường có khả năng dẫn đến hư hỏng (early-warning).
> KIẾN TRÚC CHỐT — CHIA VAI: quantum operator TRAIN trên GPU (nghiên cứu, bước 3);
>   bộ dò residual NHẸ DEPLOY lên MCU cạnh máy (nhúng, bước 4-6).

## Vì sao chia vai (dung hòa quantum voi nhúng)
Khung môn học là Embedded AI: bước 4-6 đòi Int8 + C-array + chạy trên vi điều khiển — NGƯỢC với
quantum (mạch lượng tử không quantize/deploy lên MCU). Giải: tách 2 nhánh cùng tồn tại.
- Quantum = "phòng thí nghiệm" (train, cloud/GPU) — điểm nghiên cứu độc đáo.
- Model nhẹ (PCA/SPE 40 trọng số) = "sản phẩm cắm vào máy" (deploy MCU) — đúng embedded.
Cùng một CƠ CHẾ residual; chỉ khác lõi (quantum operator vs PCA tuyến tính).

---

## Bước 1 — Định nghĩa bài toán & chọn phần cứng
- **Bài toán:** phát hiện/dự đoán sớm bất thường (anomaly prediction) — học nếp KHỎE, cảnh báo khi
  residual vượt ngưỡng. KHÔNG dự báo giá trị tuyệt đối.
- **Cảm biến:** 8 đầu rung 29VT (proximity X-Y, 4 ổ đỡ) + 10 nhiệt ổ đỡ 29TE + process (lưu lượng
  29FI, tốc độ 29SIC, áp, mức) + Performance P1/P2.
- **Phần cứng đích (deploy):** MCU biên (vd ARM Cortex-M / ESP32 cạnh tủ giám sát) — CHỐT ở bước 5.

## Bước 2 — Thu thập & tiền xử lý + trích đặc trưng
- **Đã làm sạch** 5 nguồn: 5-năm cadence 8h (nhiệt+Direct dài hạn); khối 8-16h cadence 3s (vector
  rung Direct+1X Amp/Phase — CHÍNH LÀ đặc trưng FFT); process 2 tháng.
- **Đặc trưng:** 1X Amp/Phase = thành phần FFT bậc 1 (trích sẵn bởi hệ). Waveform (3 mốc) cho phổ
  đầy đủ điểm. Ràng buộc: rung/nhiệt-ổ-đỡ CHỈ lưu ngắn hạn độ phân giải cao (hệ PI).
- **Chuẩn hóa:** z-score theo giai đoạn khỏe.

## Bước 3 — Thiết kế & huấn luyện (GPU/Cloud) — NHÁNH NGHIÊN CỨU (quantum)
- **M1 (đã xong, cổ điển):** PCA + SPE/T² — CHỨNG MINH cơ chế residual (false-alarm 1%, detect 100%).
  Learning curve chứng minh PCA 40 trọng số là kích thước đúng với dữ liệu hiện có.
- **Nâng cấp (nghiên cứu):** condition-aware Neural Operator — input = điều kiện vận hành (process),
  output = trường rung khỏe kỳ vọng (8 ổ × Direct/1X Amp/Phase); residual có điều kiện.
  Quantum vào lớp phổ (QFNO-style: FFT → mạch biến phân vài mode → IFFT). Train trên GPU.
- **Baseline bắt buộc:** mean+3σ, PCA, FNO cổ điển (không quantum) — KHÔNG hứa "quantum thắng",
  đóng khung "đạt tương đương với ít tham số / bền nhiễu".

## Bước 4 — Tối ưu model (Quantization Int8 + Pruning) — NHÁNH NHÚNG
- Đối tượng deploy KHÔNG phải quantum operator (không nhúng được) mà là **bộ dò residual nhẹ**:
  ma trận PCA (10×4) + ngưỡng SPE. ~40 tham số.
- Quantize Int8: phép chiếu PCA = nhân ma trận → Int8 dễ, sai số nhỏ. Pruning gần như không cần
  (model đã cực nhỏ).

## Bước 5 — Triển khai (C-array, biên dịch cho MCU)
- Xuất ma trận PCA + ngưỡng thành **C-array**; vòng lặp suy luận = nhân ma trận + tính SPE + so ngưỡng.
- Biên dịch cho MCU đích. Bộ nhớ: ~vài KB (ma trận nhỏ). Không cần accelerator.

## Bước 6 — Kiểm thử thực tế (độ trễ, điện năng)
- Đo trên MCU: latency mỗi lần suy luận (kỳ vọng < 1ms — chỉ nhân ma trận nhỏ), RAM, điện năng.
- So chế độ cảnh báo tại-biên (MCU) vs gửi-về-cloud (quantum): minh họa vì sao edge detector nhẹ
  đáng giá (cảnh báo tức thì, không phụ thuộc mạng).

---

## Độ đo (3 tầng, đã chốt)
- Operator/nén (điều kiện cần): RMSE/MAE tái tạo trên tập khỏe.
- Phát hiện (chính): SPE/Q + T² Hotelling, giới hạn kiểm soát 99% (Jackson-Mudholkar); ROC/PR-AUC.
- Vận hành + nhúng: lead time (cần nhật ký bảo trì — M2) + latency/RAM/power on-device (bước 6).

## Giới hạn nói thẳng
- 1 máy, 1 đợt trôi → chứng minh trên máy này, chưa tổng quát (cần máy 2 = M3).
- Lead-time thật cần nhật ký bảo trì (mốc hỏng) — chưa có.
- Quantum chạy simulator (PennyLane), không phải máy lượng tử thật → "nghiên cứu khả năng biểu diễn".
- Rung/nhiệt-ổ-đỡ chỉ có chuỗi ngắn hạn (ràng buộc hệ PI) → operator điều kiện dùng nhiều khối 8h.
