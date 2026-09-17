# Kế hoạch: chạy suy luận ba tầng trên dữ liệu P29201B (29/05–07/09/2026)

Trạng thái: ĐỀ XUẤT, chờ duyệt · Ngày: 08/09/2026 · Dữ liệu: `Dataraw/1X_P29201B_29.5_07.09.26.xlsx`, `Dataraw/Direct_P29201B_29.5_07.09.26.xlsx`

## 1. Kết quả khảo sát

| Mục | P29201B | So với P29201A |
|---|---|---|
| Định dạng tệp | Cùng mẫu xuất PI DataLink (khối "GIA DINH", hàng 12 = tên cột, dữ liệu từ hàng 13, "Bad" khi mất tín hiệu) | Giống hệt, chỉ nhiều cột hơn → dùng lại bộ đọc của script 11/12 với danh sách kênh mới |
| Khoảng thời gian, bước | 29/05 00:00 → 07/09 00:00, 10 phút, 14.545 dòng, không thiếu dòng | Cùng bước |
| Điểm đo | 12: bơm 2001X/Y, 2003X/Y · hộp số 2022X/Y, 2024X/Y · động cơ 2050X/Y, 2051X/Y | A có 8: bơm 2001/2003 + tua-bin 2005/2007. **B là máy khác cấu trúc (động cơ + hộp số)** |
| Thời gian máy chạy | **7,7 %** (1.118 mẫu ≈ 186 giờ ≈ 7,8 ngày), 4 lần chạy: 29/05 10:10–01/06 15:50 (3,2 ngày) · 11/06 16:40–13/06 14:30 (1,9 ngày) · 25/06 09:40–13:30 (4 giờ) · 04/09 13:50–07/09 (2,6 ngày, chưa kết thúc) | A chạy gần liên tục. **B là bơm dự phòng**: 3 lần chạy đầu trùng đúng các lần dừng của A (29/05, 11–13/06) |
| Direct khi chạy (trung vị ngày) | 2001: 18 / 16 µm · 2003: 22–28 µm · động cơ 2050X tới 37 µm | Xa ngưỡng 65 µm; 2003 của B cao hơn 2001, ngược với A |
| 1X khi chạy | Biên độ 2003 ≈ 18 µm (đỉnh 30), 2001 ≈ 8–9 µm; pha 2001X ổn định 154–180° | Cùng chất lượng, dùng được cho tầng C |
| Lỗi dữ liệu | (1) **2022BY 1X: "Bad" 99,9 % ngay khi máy chạy** (tag chết); (2) **tệp 1X bị cắt cột**: thiếu pha 2051BX và toàn bộ 2051BY (cột 22–24 trống) | Cần xuất lại 1X hoặc chấp nhận 11 kênh |

**Kết luận khảo sát:** dữ liệu sạch và đúng định dạng, nhưng máy chỉ chạy 12 ngày rời rạc. Ba tầng như đã khóa cho A không thể cho ra cảnh báo trên B với dữ liệu này, cụ thể:

- Tầng A cần ≥ 8 ngày chạy trong cùng một đoạn (cửa sổ 14 ngày) và 90 ngày tham chiếu ≥ 30 ngày quan sát. Đoạn chạy dài nhất của B là 3,2 ngày → chỉ ra được dòng ngày, không tính được dốc.
- Tầng B đo khoảng cách tới nền gốc **của chính máy đó** (SAE học trên 9b của A). Đem SAE của A chấm B chỉ đo "B khác A", không đo B đang xấu đi. B chưa có nền gốc: cần một đoạn chạy ổn định dài (A dùng 31 ngày), B mới có 7,8 ngày cộng dồn. Dốc 14/45 ngày cũng vô nghĩa với máy chạy vài ngày một lần.
- Tầng C cần 8 tuần chữ ký pha; B có dữ liệu ở 4 tuần rải trong 15 tuần → không đủ.

## 2. Đề xuất: ba mức, làm mức 1 ngay

### Mức 1 — Chạy đường ống đầu-cuối trên B, không hứa cảnh báo (1 ngày)
Mục đích: chứng minh mã dùng lại được cho máy khác và lập hồ sơ nền cho B.
1. `scripts/New/34_ingest_p29201b.py`: đọc hai tệp, cổng máy chạy theo Direct bơm (> 3 µm ở ≥ 3/4 kênh bơm; A dùng ≥ 6/8), bảng đoạn chạy/dừng, kho đặc trưng `Dataclean_new/p29201b/feature_store_1x.parquet` (amp, sin, cos) cho 8 kênh chọn: **2001X/Y, 2003X/Y, 2024X/Y, 2050X/Y** (bỏ 2022BY chết và 2051 thiếu cột; hộp số 2024 + động cơ 2050 thay vai tua-bin 2005/2007 của A).
2. Tầng A trên B: chạy lại luật script 17 với 4 kênh bơm + 4 kênh còn lại → bảng ngày, ghi rõ "chưa đủ hàng" và mức Direct từng lần chạy (để so lần chạy sau).
3. Kiểm tra khởi động (script 19) cho từng lần B chạy: bước pha 1X so với lần chạy trước — đây là phép kiểm duy nhất của bộ ba dùng được ngay cho bơm dự phòng.
4. Thí nghiệm chéo máy: chấm SPE của B bằng SAE_b0.001_s0 (nền 9b của A). Kỳ vọng SPE rất lớn; ghi thành bằng chứng "mô hình phải học theo từng máy", không dùng để cảnh báo.
5. Phát lại B qua `host_sim` và bo ESP32-S3 (định dạng luồng S/D/R/E không đổi) để chứng minh firmware không phụ thuộc máy; đối chiếu bo với Python như đã làm cho A.
6. Hình + báo cáo ngắn `plans/260908-1100-inference-p29201b/reports/`.

### Mức 2 — Nền gốc riêng cho B và "tầng B-khởi động" (khi có thêm dữ liệu)
- **Xin thêm dữ liệu B các thời kỳ A dừng dài**, đặc biệt 04/01–15/01/2026 (A dừng lần 1, B nhiều khả năng chạy ~11 ngày) và các đợt trước 2026. Đó là ứng viên nền gốc.
- Với bơm dự phòng, luật dốc 14/45 ngày không hợp. Đề xuất biến thể **so sánh khi khởi động**: mỗi lần B chạy, sau 2 ngày ổn định, tính trung vị SPE 6 giờ so với giới hạn 99 % của nền gốc riêng; báo khi vượt trong 6 giờ liên tiếp. Ngưỡng và nền khóa theo cùng quy trình khối như A (khối = từng lần chạy).
- Huấn luyện SAE cho B với đúng kiến trúc và siêu tham số đã khóa, chỉ đổi dữ liệu; giữ PCA_k8 làm mốc so sánh.

### Mức 3 — Nhúng cho B (0,5 ngày, sau mức 2)
- Tham số hóa script 25/26 theo mã bơm (thư mục ra, tệp khóa) → sinh `sae_weights.h`/`hqc_params.h` riêng cho B; firmware giữ nguyên, chỉ đổi hằng số lúc biên dịch.

## 3. Rủi ro và điểm cần chốt
- Chọn 8 kênh cho B (đề xuất 2001, 2003, 2024, 2050) ảnh hưởng mọi bước sau; nếu xuất lại được 1X đầy đủ thì cân nhắc 2051 thay 2050.
- Luật máy chạy trên B chỉ dựa 4 kênh bơm; cần kiểm lại với các lần chạy 4 giờ (25/06) để không tạo đoạn giả.
- Tệp Direct có thêm hai cột rác ở cuối (`29VT-2051BX`, `29VT-2051X`); bộ đọc phải lọc theo hậu tố "(um)".

## 4. Câu hỏi chưa giải
1. B chạy từ 04/09 13:50 có nghĩa là A dừng lần thứ ba ngày 04/09/2026? Nếu đúng, đây là mốc mới cho A (dữ liệu A hiện dừng ở 02/09).
2. Có xuất được B cho 01/01–20/01/2026 và các năm trước không? Không có đoạn chạy dài thì không lập được nền gốc.
3. 2022BY 1X chết là lỗi tag hay lỗi xuất? 2051 thiếu cột là do xuất cắt ngang?
4. B có lịch sử kiểm tra/sửa chữa nào trong 29/05–07/09 không (để gán nhãn giống A)?
