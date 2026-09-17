# HQC_Aware-Forecasting — Mục báo cáo M1: Chứng minh cơ chế

> **Máy P29201A** (tổ tua-bin hơi + bơm), giám sát tình trạng đa cảm biến.
> **Mục tiêu M1:** chứng minh CƠ CHẾ residual-based anomaly detection đứng vững trên dữ liệu thật,
> làm nền cho các mức M2 (lead-time thật) và M3 (tổng quát hóa) khi bổ sung dữ liệu.
> **Phương pháp M1:** cổ điển, có kỷ luật học thuật — KHÔNG phải mô hình lượng tử (đó là đích cuối).

---

## 0. Vì sao M1 cố tình đơn giản

Trước khi dựng operator lượng tử (phức tạp, tốn), M1 kiểm một giả định rẻ:
*"mô hình học hành vi máy KHỎE → residual tăng khi máy lệch khỏi khỏe"*. Nếu một mô hình cổ điển
tầm thường đã không phân biệt nổi khỏe/bất thường, thì operator lượng tử cũng vô ích. M1 = "cắm thử
bóng đèn vào ổ điện thường trước khi xây nhà máy điện".

---

## 1. Dữ liệu (đã làm sạch)

23 cảm biến trên máy P29201A, trải 5 năm (2021-07 → 2026-07), cadence gốc ~8.2h (≈3 lần/ngày).
Sau làm sạch (khử sentinel −32768, giới hạn vật lý theo loại, cờ running cho rung): **110.408/110.422
giá trị hợp lệ (100%)** — dữ liệu gốc chất lượng cao.

![Tổng quan dữ liệu sạch]({{artifact:art_d5b63079-9771-490c-912b-68b117ec17e7}})

**Tín hiệu bất thường thật (đã kiểm chứng running-corrected):** nhiệt độ ổ đỡ trôi đơn điệu
(29TE-2005A: 39 → 64 °C), rung ổ 2003 cao lên giai đoạn 2025-26. Giai đoạn nền khỏe rõ: 2022-2023.

---

## 2. Cơ chế & huấn luyện

- **Chia theo THỜI GIAN (không ngẫu nhiên):** train CHỈ giai đoạn khỏe 2022-2023; 2024 = chuyển tiếp
  (không train/không chấm); test = giai đoạn trôi 2025-2026.
- **Chuẩn hóa z-score** theo mean/std giai đoạn khỏe → "bình thường" ≈ 0, độ trôi hiện thành độ lệch.
- **Unsupervised:** nhãn healthy/drift CHỈ dùng lúc chấm điểm, KHÔNG dùng lúc học.
- **Cảnh báo = residual** (‖thực tế − tái tạo‖), theo dõi liên tục.

**Lựa chọn đặc trưng (phương pháp có tên):** availability filter (23 → 14, loại rung running-sparse
+ cảm biến lắp muộn) → variance filter → correlation filter (|r|>0.95, bỏ 6 nhiệt trùng) → **10 đặc
trưng cuối** (4 nhiệt đại diện + 3 vị trí trục + các cảm biến độc lập).

**Kích thước model — chọn bằng bằng chứng, không quy tắc ngón tay:** xem §5 (learning curve).
Số thành phần PCA chọn theo tiêu chí "≥90% phương sai" = 4 (Kaiser=3, 95%=5; kết luận không nhạy 3-5).

---

## 3. Độ đo (chuẩn Multivariate Statistical Process Control)

| Độ đo | Bắt loại bất thường | Loại suy | Giới hạn kiểm soát |
|---|---|---|---|
| **SPE / Q-statistic** | "vỡ cấu trúc tương quan" (dàn nhạc lạc điệu) | quan hệ cảm biến lệch | Jackson–Mudholkar 99% (moment-matching χ²) |
| **T² Hotelling** | "biến động quá lớn đúng hướng" (dàn nhạc chơi to gấp ba) | biên độ vượt mức quen | phân phối F 99% |

Hai độ đo bổ sung nhau: SPE bắt lỗi kiểu-mới, T² bắt lỗi kiểu-cũ-nhưng-to.

---

## 4. Kết quả

![Biểu đồ kiểm soát SPE/T²]({{artifact:art_2ac3c112-a778-4605-b25d-ca4f94afe53d}})

**SPE/Q với giới hạn 99%: false-alarm 1.0% trên nếp khỏe, phát hiện 100% giai đoạn suy giảm.**
Ổn định qua mọi lựa chọn số thành phần (3/4/5 đều detect 100%).

![Timeline residual]({{artifact:art_2ae1c137-1b67-4c8d-b0d4-4afe81c40230}})

Residual (nhất là PCA — học tương quan) trôi lên dần suốt 2024-2025, vượt ngưỡng *trước* khi bất
thường lộ rõ bằng mắt thường. Đây là bằng chứng cho **early-warning về mặt cơ chế**.

---

## 5. Kích thước model đúng — bằng learning curve

![Learning curve]({{artifact:art_7c293b5a-b572-4ab9-99a1-880d540357ee}})

Time-blocked: giữ cố định 25% tuần khỏe cuối (26 tuần) làm validation, train tăng dần 31→79 tuần.

| Model | Trọng số | val-RMSE (đủ data) | Khoảng cách train↔val |
|---|---|---|---|
| **PCA n=4** | 40 | **0.77** | nhỏ |
| AE 10→4→2→4→10 | ~116 | 1.93 | rất lớn (overfit) |
| AE 10→8→4→8→10 | ~254 | 1.13 | lớn (overfit) |

→ Ở quy mô 105 tuần, **PCA (40 trọng số) là kích thước ĐÚNG**; deep model overfit. Đây là lập luận
vững trả lời hội đồng "vì sao chưa dùng deep learning": *bằng chứng nói dữ liệu chưa đủ*, không phải
không biết. Đường validation chưa phẳng → thêm dữ liệu sẽ giúp → deep/quantum chỉ đáng khi có thêm data.

---

## 6. Bốn trụ nền tảng (đều có bằng chứng)

1. **Dữ liệu sạch, hiểu đúng** — 23 cảm biến, 100% hợp lệ, tín hiệu bất thường thật đã kiểm chứng.
2. **Cơ chế residual chạy** — SPE/T² phát hiện được, false-alarm kiểm soát 1%.
3. **Phương pháp chọn model có kỷ luật** — feature filter, tiêu chí thành phần, learning curve; mọi
   lựa chọn truy nguồn được.
4. **Ranh giới trung thực đã vẽ rõ** — biết chính xác cái gì cần dữ liệu bổ sung.

---

## 7. Ranh giới — cái M1 CHƯA chứng minh (trung thực khoa học)

- **Lead-time thật (báo trước hư hỏng N tuần):** CHƯA. Không có nhật ký bảo trì → "mốc hỏng" tự định
  nghĩa (ngưỡng nhiệt) → lead-time nhảy +70 đến −78 tuần tùy độ hạt. **Rút lại con số "16 tháng".**
- **Nhãn "drift 2025-2026" là giả định** (dựa nhiệt tăng), chưa phải hư hỏng xác nhận.
- **ROC/PR-AUC ~1.00 KHÔNG dùng làm điểm mạnh** — bài toán "khỏe vs trôi-rõ" quá dễ (baseline cũng ~0.98).
- **Chỉ 1 máy, 1 đợt trôi** → chưa tổng quát.
- **Cổ điển, chưa quantum** — nhưng đã chứng minh cơ chế đúng hướng để nâng cấp có cơ sở.

---

## 8. Điều kiện mở khóa các bước tiếp

| Bước tiếp | Điều kiện (từ M1) |
|---|---|
| Đo lead-time thật (M2) | Nhật ký bảo trì — mốc hỏng thật |
| Autoencoder phi tuyến | Thêm dữ liệu (learning curve chưa bão hòa) |
| Quantum operator (QFNO) | Sau khi AE có chỗ đứng + đủ mẫu |
| Tổng quát hóa (M3) | Máy thứ 2 / ca hỏng thật |

**Khẳng định:** cơ chế cốt lõi (residual-based anomaly trên học tương quan đa cảm biến) đã đứng vững —
đủ làm nền đi tiếp. Cái đang chờ KHÔNG phải chứng minh nguyên lý (đã xong), mà là DỮ LIỆU để nâng
"chứng minh cơ chế trên 1 máy" lên "phương pháp đo được lead-time thật".
