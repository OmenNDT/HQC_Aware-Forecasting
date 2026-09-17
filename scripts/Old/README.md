# HQC — PIPELINE SCRIPT

## Trả lời câu "script lưu ở đâu"

**Trước hôm nay: KHÔNG có file script nào trong project.** Toàn bộ phân tích chạy trong
**kernel Python phiên làm việc** (Claude Science), nên mã tồn tại ở hai chỗ:

| Nơi lưu | Nội dung | Truy cập |
|---|---|---|
| **Hệ lineage của artifact store** | mã tái lập đầy đủ, gắn với từng artifact + snapshot môi trường conda | `host.lineage[version_id]["code"]` |
| **Transcript phiên làm việc** | mã + ngữ cảnh trao đổi | tìm trong lịch sử hội thoại |

Thư mục `scripts/` này là **bản trích ra thành file** để đề tài có mã nguồn cầm tay được —
đọc được, phiên bản hóa được, đưa vào phụ lục báo cáo được.

## Bảy script — theo thứ tự chạy

| Script | Làm gì | Vào | Ra |
|---|---|---|---|
| `01_clean_direct_5y.py` | Làm sạch file 5 năm: tách 24 block header → 23 cảm biến, khử sentinel `−32768`, luật vật lý theo loại, cờ running | `Dataraw/P29201A-5y-2026.csv` | `Dataclean/P29201A_clean_long.*`, `quality_manifest.csv` |
| `02_build_train_flat_baseline.py` | Dựng nền train **phẳng 20/02–22/03/2026** (743 giờ). Ghép `51_Vib180d` (1X Amp/Phase) với `33_Aligned` (tải) trên lưới 1 giờ, áp cổng lọc | `PI Data.xlsx` | `Data/HQC_train_healthy_flat.csv` |
| `03_build_eval_set.py` | Dựng tập đánh giá 350 mẫu: nhãn ứng viên từ percentile nền + 3 ví dụ mẫu + cột trống cho chuyên gia | `PI Data.xlsx` | `Data/HQC_eval_expert.csv`, `HUONGDAN-gan-nhan-PDM.md` |
| `04_train_and_compare_baseline.py` | Train PCA k∈{2,3,4,6} + AE 2 cỡ. Learning curve time-blocked. So nền cũ (nhiễm) vs nền phẳng | `Data/HQC_train_healthy_flat.csv` | `hqc_baseline_fix.png` |
| `05_score_and_contribution.py` | Anomaly score 0–100 (hiệu chỉnh trên residual val khỏe, thang log) + contribution từng cảm biến | mô hình + eval | `Data/HQC_eval_scored_flat.csv` |
| `06_figure_model_selection.py` | Figure 3 panel: learning curve · tỉ số tách · contribution | kết quả bước 4-5 | `hqc_model_selection.png` |
| `07_figure_control_chart.py` | Biểu đồ kiểm soát SPE/Q + T² Hotelling với giới hạn kiểm soát | mô hình | `hqc_M1_control_chart.png` |
| `08_quantize_and_emit_c.py` | Lượng tử hóa Int8 per-channel, sinh `hqc_detector.c`, đo dấu chân nhúng | mô hình | `hqc_quantization.png`, `hqc_detector.c` |

## Mã nhúng (không phải script phân tích)

| File | Nội dung |
|---|---|
| `hqc_detector.c` | Bộ dò residual, C thuần, 384 B Flash + 216 B RAM, không `malloc`, không hàm siêu việt |
| `test_detector.c` | Harness kiểm chứng — so 6 mẫu với Python, sai lệch < 1e-5 |

Biên dịch: `gcc -O2 -std=c99 test_detector.c -o test_detector -lm && ./test_detector`

## ⚠ Ba lưu ý khi chạy lại

1. **Đường dẫn tuyệt đối.** Script trích từ lineage giữ đường dẫn của máy gốc
   (`/home/sontn/Projects/HQC_Aware-Forecasting/...`). Sửa biến đường dẫn ở đầu file trước khi chạy.
2. **Helper `apply_figure_style()`** thuộc skill `figure-style`, không có trong script. Các script
   figure cần nạp skill đó, hoặc thay bằng cấu hình matplotlib riêng.
3. **Thứ tự bắt buộc.** Bước 4 cần đầu ra bước 2; bước 5 cần mô hình bước 4; bước 6–8 cần bước 5.
   Không chạy lẻ được vì mỗi script vốn là một cell trong kernel liên tục.

## Môi trường

conda env `python` — `pandas`, `numpy`, `scikit-learn`, `scipy`, `matplotlib`, `pyarrow`.
Snapshot môi trường đầy đủ nằm trong lineage của từng artifact (`host.lineage[vid]["env"]`).
