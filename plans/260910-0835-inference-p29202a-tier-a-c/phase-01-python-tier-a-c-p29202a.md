# Pha 01 — Tầng A và C trên P29202A bằng Python (ngưỡng khóa của P29201A)

Ưu tiên: cao · Trạng thái: HOÀN THÀNH 10/09/2026 10:30 (tester DONE, reviewer DONE_WITH_CONCERNS đã xử lý) · Kết quả: `reports/tier-a-c-p29202a-python.md`

## Bối cảnh
- Khảo sát: `plans/reports/survey-260910-0835-p29202a-1x-data-suitability.md`
- Luật tầng A: `scripts/New/17_tier_a_direct_projection.py`, hằng số `scripts/New/phase01_config.py` (PLANT_LIMIT_UM, TIERA_*)
- Luật tầng C và kiểm tra khởi động: `scripts/New/18_tier_b_slow_scale_and_tier_c.py` (`weekly_signature`), `scripts/New/19_restart_check.py`, ngưỡng trong `Dataclean_new/locked_params_phase02.json`

## Yêu cầu
- Không đổi bất kỳ ngưỡng nào đã khóa. Chỉ đổi: danh sách kênh (4 kênh bơm), cổng chạy ≥ 3/4 kênh > 3 µm, kênh tầng C = 2017X.
- Kết quả tách riêng thư mục `Dataclean_new/p29202a/`, không ghi đè sản phẩm của A.

## Tệp
- Tạo `scripts/New/34_ingest_p29202a.py`: đọc hai tệp (thời gian Direct là số ngày Excel → chuyển; "Bad"/"Not Connect"/"Configure" → NaN; lọc cột theo hậu tố "(um)"/"(do)"), cổng chạy, bảng đoạn chạy/dừng, ra `direct_long.parquet` (dạng dài như `DIRECT_LONG`) và `feature_store_1x.parquet` (amp, sin, cos cho 2017X/Y, 2019Y; 2019X NaN).
- Tạo `scripts/New/35_tier_a_c_p29202a.py`: gọi lại hàm của script 17/18/19 với tham số kênh (tách hàm `daily_direct`/`project` nhận `CH`, `run_min_ch`; `weekly_signature` nhận tên kênh) — sửa script 17/18 tối thiểu để nhận tham số, mặc định giữ hành vi A (chạy lại script 20 để xác nhận kết quả A không đổi).
- Hình: `Bao_cao/hinh-p29202a-tang-a-c.png` (Direct ngày 4 kênh + cờ, chữ ký pha tuần 2017X + tốc độ), tái dùng `21_figures_three_tiers.py`.
- Biên bản: `plans/260910-0835-inference-p29202a-tier-a-c/reports/tier-a-c-p29202a-python.md`.

## Bước
1. Bộ đọc + bảng đoạn chạy; đối chiếu số ngày chạy (395) và hai lần dừng 2025 với khảo sát.
2. Tầng A toàn kỳ: bảng ngày (level, dốc, t, D_low, tham chiếu 90 ngày, cờ), số ngày báo, ngày bỏ sau khởi động.
3. Tầng C toàn kỳ: chữ ký tuần 2017X, tốc độ 4 tuần, cờ/báo, cờ 21 ngày sau khởi động; kiểm tra khởi động cho các lần dừng 29/08 và 22/09/2025.
4. Chạy lại script 20 cho A → kết quả phải giống run 3 (B₁₄ 06/04, B₄₅ 11/04, A 29/04, C 0).
5. Hình + biên bản; tester chạy lại từ đầu; code-reviewer soát thay đổi ở script 17/18.

## Tiêu chí xong
- Bảng ngày tầng A và bảng tuần tầng C cho 14 tháng; số ngày/tuần báo (kỳ vọng 0) và lý do từng cờ lẻ nếu có.
- Kết quả A không đổi sau khi tham số hóa.

## Rủi ro
- 2019Y 1X thiếu nửa đầu kỳ → chỉ ảnh hưởng hình, không ảnh hưởng A/C.
- Nếu ánh xạ ổ 2001 ↔ 2017 sai, chạy lại tầng C với 2019X là không thể (1X 2019X chết) → cần xác nhận trước.
