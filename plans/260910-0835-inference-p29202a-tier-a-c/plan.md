# Kế hoạch: suy luận tầng A và C trên P29202A (13/07/2025–10/09/2026), Python rồi ESP32-S3

Trạng thái: ĐANG LÀM (pha 01 hoàn thành 10/09 10:30, pha 02 chờ) · duyệt 10/09/2026 · Dữ liệu: `Dataraw/P29202A_1X_13.07.25-10.09.26.xlsx`, `Dataraw/P29202A_Direct_13.07.25-10.09.26.xlsx` · Khảo sát: `plans/reports/survey-260910-0835-p29202a-1x-data-suitability.md`

## Mục tiêu
Kiểm tra **luật và ngưỡng đã khóa trên P29201A** (tầng A: 1,10 × trung vị 90 ngày, t > 1,645, D_low < 30, 2 ngày; tầng C: đổi dấu so 8 tuần trước, |tốc độ| > 1°/tuần, sd < 5°, 2 tuần, cờ 21 ngày sau khởi động) khi áp nguyên vẹn lên máy thứ hai. Không huấn luyện gì mới, không đụng tầng B. Kỳ vọng: 14 tháng không báo giả; hai lần dừng 2025 cho kiểm tra khởi động.

## Nguyên tắc chuyển máy (đã chốt với người dùng 10/09)
- Chuyển **luật + ngưỡng**, không chuyển dữ liệu. Tầng C không có mô hình học; "chữ ký 2001X" là phép tính trên pha 1X của ổ bơm thứ nhất theo hướng X. Trên P29202A, cảm biến tương ứng là **2017X** (ánh xạ 2001 ↔ 2017, 2003 ↔ 2019). **Quyết định 10/09 09:40:** giữ cách ánh xạ theo ổ; khi triển khai máy mới được phép xem lịch sử dữ liệu để chọn kênh chữ ký. Phương án "mọi kênh" đã cân nhắc và không chọn.
- Cổng máy chạy là luật tính sẵn có của dữ liệu, không phải tham số mô hình: A có 8 kênh, đòi ≥ 6 kênh > 3 µm (75 %); P29202A có 4 kênh → giữ cùng tỷ lệ 75 % = ≥ 3/4. Số 3 µm giữ nguyên.
- Khe kênh trên bo: 2017X→0, 2017Y→1, 2019X→2, 2019Y→3, khe 4–7 = NaN; tầng A bỏ qua kênh NaN sẵn, tầng C đọc khe 0.

## Các pha
| Pha | Nội dung | Ước tính | Trạng thái |
|---|---|---|---|
| [01](phase-01-python-tier-a-c-p29202a.md) | Bộ đọc cặp tệp P29202A, tầng A + C bằng Python với ngưỡng khóa, hình, biên bản | 0,5 ngày | **HOÀN THÀNH** — 0 báo A, 0 báo C trong 14 tháng; [biên bản](reports/tier-a-c-p29202a-python.md) |
| [02](phase-02-esp32-replay-p29202a.md) | Tham số hóa số kênh/cổng chạy trong firmware, tắt tầng B lúc biên dịch, luồng phát lại P29202A, host_sim = Python, chạy trên bo, trang demo A/C, video | 1 ngày | chờ duyệt |

## Phụ thuộc, rủi ro
- Không có sự kiện xấu → chỉ đo báo giả và ổn định; không có lead-time.
- Firmware: cổng chạy `running >= 6` và 3,0 µm đang cứng trong `tier_a_direct.c:59-61` → đưa vào `hqc_params.h` (sinh bởi script 26). Tầng B trên bo với trọng số của A sẽ ra số vô nghĩa → thêm cờ biên dịch `HQC_TIER_B=0`.

## Câu hỏi chưa giải
1. P29202A có sự kiện/kiểm tra nào 07/2025–09/2026 không (để đối chiếu kết quả "không báo")?
