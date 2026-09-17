# Khảo sát dữ liệu 1X P29202A (tệp `Dataraw/P29202A_1X_13.07.25-10.09.26.xlsx`) — 10/09/2026

## Sự thật về tệp
- Cùng mẫu xuất PI DataLink như A/B (hàng 12 tên cột, dữ liệu từ hàng 13, "Bad"/"Not Connect"/"Configure" khi không có số).
- **Khoảng thời gian thật: 13/07/2025 → 10/09/2026** (14 tháng, 61.057 dòng, bước 10 phút, không thiếu dòng). Tên tệp ghi 13.07.26 nhưng tiêu đề và dữ liệu là 2025.
- 6 điểm đo: bơm 2017X/Y, 2019X/Y; động cơ 2052A, 2053A (một kênh, không X/Y).
- Không có tệp Direct kèm theo.

## Chất lượng từng kênh
| Kênh | Tình trạng | Dùng được? |
|---|---|---|
| 2017AX, 2017AY | Bad 7,7 % (đúng các lần dừng); biên độ 10,8–11,3 / 7,3–7,7 µm, pha 44–55° / 141–151°, cực ổn định | **Có**, toàn kỳ |
| 2019AY | Bad 49 %; có số chủ yếu từ 01/2026; biên độ 5,5 → 3,7 → 6,9 µm; pha nhảy 191° → 141° → 222–229° qua các lần dừng 2025 | Một phần (từ 25/01/2026) |
| 2019AX | Bad 99,8 %, "Not Connect" 99 dòng | **Không** (tag chết) |
| 2052A, 2053A | "Configure" 100 % (thuộc tính chưa cấu hình trong AF) | **Không** |

## Máy chạy
- Chạy 92 % thời gian (390 ngày). Dừng dài: 05/08–29/08/2025 (25 ngày), 15–22/09/2025 (7 ngày); vài lần dừng ngắn tháng 9–11/2025.
- **Chạy liên tục 06/11/2025 → 11/08/2026 (278 ngày)** rồi 11/08 → 10/09/2026 (30 ngày; khoảng trống 20 phút ở 11/08 08:30, không phải dừng thật).

## Phù hợp với ba tầng
- **Tầng A:** không có Direct → chưa chạy được. Cần xuất thêm `Direct_P29202A` cùng kỳ.
- **Tầng B:** mô hình đã khóa cần 8 kênh (24 đầu vào); máy này chỉ có 2 kênh tin cậy (+1 kênh nửa kỳ). Không đem SAE của A sang được. Nhưng có **278 ngày chạy liên tục** → đủ để lập nền gốc riêng và mô hình nhỏ (6–9 đầu vào: amp, sin, cos của 2017X/Y ± 2019Y) theo đúng quy trình khối đã dùng cho A.
- **Tầng C:** dùng được ngay với 2017X (thay vai 2001X của A): 14 tháng tuần, pha ổn định, trôi +8° cả năm (< 1°/tuần) → kỳ vọng không báo; các lần dừng 2025 cho kiểm tra bước pha khi khởi động (2019Y đổi tham chiếu rõ rệt qua mỗi lần dừng).
- Không có sự kiện xấu nào được biết trong kỳ → dữ liệu này là **kiểm âm tính 14 tháng trên máy thứ hai** (tỷ lệ báo giả), không đo được lead-time.

## Câu hỏi chưa giải
1. Xuất được Direct P29202A cùng kỳ không (tầng A)?
2. P29202A có sự kiện hỏng/kiểm tra nào 07/2025–09/2026 không? Lần dừng 05–29/08/2025 là gì?
3. 2019AX chết và 2052A/2053A "Configure" là lỗi tag/AF hay lỗi xuất? Có tag động cơ X/Y nào khác không?
4. Chấp nhận mô hình 2 kênh (2017X/Y) cho tầng B, hay chờ sửa 2019/2052/2053?
