# Pha 01 — Tầng A và C trên P29202A bằng Python, ngưỡng khóa của P29201A (10/09/2026)

## Cách làm
- Dữ liệu: `Dataraw/P29202A_Direct_13.07.25-10.09.26.xlsx` + `P29202A_1X_13.07.25-10.09.26.xlsx`, 13/07/2025 → 10/09/2026, 10 phút, 61.057 dòng.
- Bộ đọc `scripts/New/34_ingest_p29202a.py` → `Dataclean_new/p29202a/` (direct_long, feature_store_1x, run_segments). Cổng chạy ≥ 3/4 kênh Direct ổ bơm > 3 µm (A: 6/8, cùng 75 %). 1X chỉ giữ dòng máy chạy; 2019X 1X chết (Bad 99,8 %) bị loại khỏi tầng C và kiểm tra khởi động.
- `scripts/New/35_tier_a_c_p29202a.py` gọi đúng hàm của script 17 (tầng A) và 18 (tầng C) sau khi tham số hóa kênh; mọi ngưỡng lấy từ `phase01_config.py` và `locked_params_phase02.json`. Kênh chữ ký tầng C = 2017X (ánh xạ ổ 2001 ↔ 2017).
- Kiểm tra hồi quy P29201A: chạy lại 17 và 18 với mặc định → `tier_a_daily`, `tier_c_weekly`, `tier_b45_daily` giống hệt bản trước khi sửa.

## Kết quả
| Mục | P29202A |
|---|---|
| Máy chạy | 92,0 % thời gian; 383 ngày chạy dùng được, 6 đoạn, bỏ 12 ngày sau khởi động; 349 ngày có dòng tầng A |
| Dừng thật (khoảng trống > 12 h có ngày Direct dừng) | 04/08 → 29/08/2025 (24,7 ngày), 15/09 → 22/09/2025 (7,2 ngày) |
| **Tầng A** | **0 ngày cờ, 0 ngày báo.** D_low nhỏ nhất: 2017X 1.355, 2017Y 1.501, 2019X 597, 2019Y 632 ngày (chân trời 30). Kênh 2019Y có 46 ngày "leo so với chính nó" (mức > 1,10 × trung vị 90 ngày, từ 7,6 lên 10,8 µm trong đầu 2026) nhưng dốc quá nhỏ nên không tới điều kiện D_low |
| **Tầng C** | **59 tuần, 0 tuần cờ, 0 tuần báo.** \|tốc độ\| quay pha 2017X: trung vị 0,23°/tuần, lớn nhất 1,75 (tuần sau khởi động 10/2025); sd tuần trung vị 0,78°; 6 tuần nằm trong 21 ngày sau khởi động |
| Kiểm tra khởi động (14 ngày trước dừng so ngày 10–14 sau) | 29/08/2025: 2017X biên độ +5,2 %, pha −2,7°; 2017Y +3,9 %, −1,1°. 22/09/2025: 2017X −3,6 %, +1,7°; 2017Y +0,4 %, −6,1°. Không có bước pha lớn kiểu +39° như P29201A 15/01/2026 |

Hình: `Bao_cao/hinh-p29202a-tang-a-c.png` (Direct ngày 4 kênh, D_low nhỏ nhất thang log, tốc độ quay pha 2017X với vùng 21 ngày sau khởi động).

## Đọc kết quả
- Luật A và C với ngưỡng của P29201A **không báo giả trong 14 tháng** trên máy thứ hai, kể cả qua hai lần khởi động. Đây là kết quả âm tính đúng kỳ vọng: máy vận hành ổn định, mức Direct 8–14 µm.
- Tốc độ quay pha vượt 1°/tuần ba lần (10/2025, 12/2025, 02/2026) nhưng không đổi dấu so 8 tuần trước, nên luật C không cờ. Hai lần đầu nằm trong vùng sau khởi động.
- 2019Y leo 40 % trong nửa đầu 2026 rồi đứng: luật A ghi nhận "leo so với chính nó" nhưng đúng là không đáng báo vì cách 65 µm quá xa.

## Sản phẩm
`Dataclean_new/p29202a/{direct_long.parquet, feature_store_1x.parquet, run_segments.csv, tier_a_daily.parquet, tier_c_weekly.parquet, restart_checks.csv, summary.json}`, `Bao_cao/hinh-p29202a-tang-a-c.png`, script 34/35, script 17/18 tham số hóa (mặc định giữ nguyên A).

## Kiểm thử và rà soát
- Tester: `plans/reports/tester-260910-1010-phase01-p29202a-tier-a-c.md`
- Code review: `plans/reports/code-reviewer-260910-1010-phase01-p29202a-tier-a-c.md`
- Tester (10/09 10:11): 44/44 kiểm tra đạt; tính lại độc lập từ Excel khớp (máy chạy 92,0 %, hai lần dừng, lưới thời gian Direct = 1X); ba bảng A và `restart_checks.csv` giống hệt bản trước; script 20 chạy lại cho lead-time không đổi (B₁₄ 06/04, B₄₅ 11/04, A 29/04, C không); tệp khóa không đổi tham số. Trạng thái DONE.
- Code review (10/09 10:20): đúng luật, không trôi ngưỡng, 17/18 mặc định tái tạo A từng byte; DONE_WITH_CONCERNS với 4 điểm vừa. **Đã sửa:** kiểm tra hàng tiêu đề "Thoi diem" và cột Direct bắt buộc; lưới 1X lệch Direct thì đưa về lưới Direct (lỗi nếu lệch > 0,1 %) thay cho assert; nguồn ngưỡng trong summary.json ghi đúng (phase01_config + locked_params_phase02); D_low vô cực → null; `assert SIG in good`; đóng tệp bằng `with`; bỏ `groupby.apply` sắp bị bỏ; hình đổi tên theo quy ước `Bao_cao/hinh-*.png`. **Chấp nhận, chưa sửa:** kiểm tra khởi động trong script 35 là bản rút gọn của script 19 (script 19 gắn với nền gốc 9b và phép sửa pha tua-bin của A, không tách hàm được nếu không sửa sâu); 2019Y vào bảng tuần nhờ ngưỡng 50 % dữ liệu hợp lệ (56,7 %), không ảnh hưởng cờ.

## Ghi chú kỹ thuật cho pha 02 (từ rà soát)
- `daily_direct` đưa Direct về lưới 1 giờ bằng "giá trị gần nhất trong ±4 h": với dữ liệu 10 phút đều, chỉ mẫu đúng giờ được dùng (1/6 số mẫu). Firmware tầng A cũng lấy một mẫu mỗi giờ nên luồng phát lại dòng D phải gửi đúng các mẫu đúng giờ, không gửi cả 6 mẫu.
- Lần dừng 15,5 giờ 25–26/09/2025 là khoảng trống > 12 h nhưng không có ngày Direct dừng theo trung vị ngày: tầng C không gắn cờ 21 ngày, tầng A vẫn cắt đoạn và bỏ 2 ngày. Đúng định nghĩa từng tầng như đã khóa trên A.
- Số ngày: khảo sát đếm 395 ngày có mẫu chạy; tầng A dùng 383 ngày (bỏ 12 ngày sau khởi động) và có dòng ở 349 ngày (cần ≥ 8 ngày cùng đoạn trong cửa sổ 14 ngày và ≥ 30 ngày tham chiếu).

## Câu hỏi chưa giải
1. P29202A có sự kiện kiểm tra/sửa chữa nào 07/2025–09/2026 không? Lần dừng 04–29/08/2025 là gì?
2. 2019Y leo 40 % đầu 2026: có thay đổi vận hành nào tương ứng không?
