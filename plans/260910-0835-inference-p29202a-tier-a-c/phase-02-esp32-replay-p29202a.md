# Pha 02 — Phát lại P29202A trên ESP32-S3, chỉ tầng A và C

Ưu tiên: trung bình · Trạng thái: chờ pha 01 · Ước tính: 1 ngày

## Bối cảnh
- Firmware: `firmware/core/` (tier_a_direct.c, tier_c_phase.c, hqc_engine.c), `firmware/esp32s3/main/main.c`, hằng số sinh `firmware/core/hqc_params.h` (script 26)
- Luồng và đối chiếu: `scripts/New/27_replay_feature_store_to_uart.py`, `28_replay_to_esp32_serial.py`, `host_sim`
- Trang demo: `scripts/New/32_build_esp32_live_demo.py` → `Bao_cao/demo/demo-esp32-live.html`; cầu nối `33_serial_ws_bridge.py`; quay màn hình `23_record_demo_screen.sh` (bài học 07/09: cắt video theo đoạn `-ss/-t`, không dùng bộ lọc gộp)

## Thay đổi firmware (nhỏ, tương thích ngược với A)
1. `hqc_params.h`: thêm `TA_RUN_MIN_CH` (A = 6, P29202A = 3) và `TA_RUN_UM` (3,0); `tier_a_direct.c:59-61` dùng hằng số này thay số cứng.
2. Cờ biên dịch `HQC_TIER_B` (mặc định 1): khi 0, engine không gọi SAE/tầng B, không phát dòng B; trang demo ẩn hai ô B₁₄/B₄₅ và đồ thị SPE.
3. Khe kênh: script 27 nhận ánh xạ kênh → khe (2017X→0, 2017Y→1, 2019X→2, 2019Y→3, còn lại NaN); dòng S/D vẫn 8 khe, NaN ghi `nan` (kiểm tra `strtof` trên ESP-IDF đọc được `nan`).
4. Script 26 nhận mã máy để sinh `hqc_params.h` riêng (`--pump P29202A`), giữ hash khóa của A không đổi.

## Bước
1. Sửa firmware + host_sim; `make -B` host_sim; phát lại luồng P29202A trên host_sim → dòng A/C phải trùng 100 % kết quả pha 01.
2. Phát lại luồng A qua host_sim với `TA_RUN_MIN_CH=6` → 652/652 dòng như cũ (không hồi quy).
3. Biên dịch ESP-IDF với `-DHQC_TIER_B=0`, nạp bo x99 (giữ BOOT+RST/RST như ghi chú phase 04), phát lại qua script 28 (chunk 8 dòng), đối chiếu bo = host_sim.
4. Trang demo A/C cho P29202A (tên máy, kênh, kỳ vọng Python), chạy qua cầu nối, quay video ~6 phút với script 23; cắt theo đoạn; khung hình.
5. Nhật ký + số đo (µs/mẫu, heap) vào biên bản pha 02; tester và code-reviewer.

## Tiêu chí xong
- Bo cho ra dòng A/C trùng Python trên 14 tháng P29202A; kết quả A không đổi; video và khung hình lưu trong `Bao_cao/demo/`.

## Rủi ro
- Luồng 14 tháng ≈ 61 k dòng S + 10 k dòng D → ~8 phút phát lại ở tốc độ hiện tại; chấp nhận, hoặc phát lại từ 06/11/2025.
- Tầng C trên bo tính tuần từ nửa đêm ngày đầu luồng; phải bắt đầu luồng đúng 13/07/2025 00:00 để trùng Python.
