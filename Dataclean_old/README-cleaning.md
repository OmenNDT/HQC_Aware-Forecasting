# HQC_Aware-Forecasting — Báo cáo làm sạch dữ liệu (Direct 5 năm)

Nguồn: `Dataraw/P29201A-5y-2026.csv` (máy quay P29201A — tổ tua-bin hơi + bơm).

## Cấu trúc gốc
- File gồm 24 block header nối tiếp (`Machine Name, / Point Name, / Y-Axis Unit,` ... rồi bảng
  `X-Axis Value, Y-Axis Value`). Phải tách theo dòng bắt đầu `Machine Name,` — đọc cả file bằng
  một header là SAI.
- 23 cảm biến duy nhất (block `29VT-2007Y` lặp 2 lần y hệt -> bỏ 1).

## Nhóm cảm biến
| Nhóm | Số | Đơn vị | Cảm biến |
|---|---|---|---|
| Rung (VT) | 8 | µm pp | 2001AX/AY, 2003AX/AY, 2005X/Y, 2007X/Y (cặp X-Y ở 4 ổ đỡ) |
| Vị trí dọc trục (XT) | 3 | mm | 2012A, 2013A, 2026 |
| Nhiệt độ (TE/TI) | 12 | °C | 2003A...2057, 2030 |

## Luật làm sạch đã áp
1. Sentinel -32768 (int16 min = lỗi cảm biến) -> NaN. Có 13 điểm.
2. Giới hạn vật lý theo loại: rung [0,2000] µm; nhiệt [-50,900] °C; vị trí [-5,5] mm. Chỉ 1 điểm nhiệt bị loại.
3. Cờ `running` (chỉ cho rung): biên độ >=5 µm pp = máy đang quay. Lúc dừng (~0) KHÔNG mang thông tin hư hỏng -> loại khỏi ma trận wide.
4. Bỏ block trùng byte-identical.

-> Sau làm sạch: 110.408 / 110.422 giá trị hợp lệ (100%) — dữ liệu gốc chất lượng rất cao.

## Độ phủ thời gian
- Toàn dải: 2021-07-27 -> 2026-07-21 (~5 năm), cadence gốc ~8h (~3 lần/ngày, theo ca kíp).
- Hai cảm biến lắp muộn: 29TI2030 từ 2022-07, 29TE-2057 từ 2025-09 (lưu ý khi căn ma trận).

## Tín hiệu bất thường thật (đã kiểm chứng running-corrected)
- Nhiệt độ tăng đơn điệu 12/12 TE: 29TE-2005A 39 -> 64 °C (nền n=21, gần đây n=294). Tín hiệu SẠCH — ứng viên chính cho anomaly-prediction.
- Rung ổ đỡ 2003 cao 2025-26 (29VT-2003AX median ~53 µm) nhưng NHIỄU, không đơn điệu.
- Giai đoạn nền khỏe rõ: 2022-2023.

## File xuất ra
| File | Nội dung |
|---|---|
| P29201A_clean_long.parquet / .csv | long-form sạch (ts, sensor, kind, unit, val, running) — 110.408 dòng |
| P29201A_wide_8h.parquet | ma trận 23 cảm biến × lưới 8h (rung = running-only, dừng->NaN) |
| P29201A_wide_weekly.parquet | ma trận tuần (261 tuần) — dùng cho cửa sổ anomaly |
| quality_manifest.csv | tóm tắt mỗi cảm biến: n, dải thời gian, median |
