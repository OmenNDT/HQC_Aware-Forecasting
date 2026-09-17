# DEMO mô hình đã train — không cần thiết bị nhúng

## Ba mức demo, chọn theo mục đích

| Mức | Là gì | Cần gì | Thuyết phục ai |
|---|---|---|---|
| **1. Phát lại (đã dựng)** | đọc dữ liệu lịch sử như thể realtime, in điểm + vùng + cảm biến nghi ngờ | chỉ Python | hội đồng, người vận hành |
| 2. Web dashboard | biểu đồ điểm theo thời gian, click ra contribution | + Flask/Streamlit | trình diễn trực quan |
| 3. Nối PI thật | thay hàm đọc file bằng đọc PI, chạy liên tục | quyền đọc PI | chứng minh dùng được thật |

**Mức 1 đủ cho mọi mục đích học thuật** — nó chứng minh mô hình chạy, không chứng minh phần cứng.

## Dùng

```
python demo_monitor.py                              # 20 giờ gần nhất
python demo_monitor.py --from 2026-03-01 --hours 8  # nền khỏe
python demo_monitor.py --from 2026-05-14 --hours 8  # suy giảm rõ
python demo_monitor.py --speed 0.3                  # giãn nhịp cho dễ xem
```

## Kết quả thật (đã chạy)

| Giai đoạn | Điểm median | Vùng |
|---|---|---|
| Nền khỏe 01/03 | **23,7** | BÌNH THƯỜNG |
| Tháng 4 (chớm) | **77,9** | BẤT THƯỜNG |
| Tháng 5 (rõ) | **87,4** | BẤT THƯỜNG |
| Tháng 6 | 81,5 | BẤT THƯỜNG |
| Tháng 8 | 84,4 | BẤT THƯỜNG |

Cảm biến nghi ngờ: nền khỏe chỉ vào **2003** (ổ mất cân bằng sẵn có, mô hình coi là nếp bình
thường); từ tháng 4 chuyển sang **2001** (ổ đang suy giảm) — đúng như phân tích độc lập.

## Thang điểm — nối tuyến trên trục log qua 3 mốc

| Mốc | SPE | Điểm |
|---|---|---|
| median nền khỏe | 5,53 | 20 |
| ngưỡng kiểm soát | 17,66 | 70 |
| p99 toàn chuỗi | 8.617 | 95 |

Kiểm trên 743 giờ nền khỏe: **82,5% BÌNH THƯỜNG · 16,4% CẦN XEM · 1,1% BẤT THƯỜNG**
(1,1% khớp thiết kế false-alarm 1%).

**Vì sao 3 mốc, không phải sigmoid đơn giản:** SPE thật trải từ 5 tới **49.692** — gấp 2.814
lần ngưỡng. Thang 2 mốc làm mọi giai đoạn sau tháng 3 đều bão hòa 100 điểm, không phân biệt
được tháng 4 với tháng 5.

## File

| File | Nội dung |
|---|---|
| `demo_monitor.py` | chương trình demo, Python thuần + pandas/numpy |
| `model_pca_k6.json` | tham số mô hình đã train (W 6×24, mean, mu, sd, mốc thang điểm) — **không train lại** |

Mô hình train trên `HQC_train_healthy_flat.csv` (743 giờ, 20/02–22/03/2026).

## Giới hạn phải nêu khi demo

1. **Không chứng minh phần cứng** — mức này chỉ chứng minh logic mô hình. Phần nhúng đã kiểm
   riêng bằng `hqc_detector.c` (mã C khớp Python sai lệch < 1e-5).
2. **Bộ dò bão hòa sau tháng 3** — 92,9% giờ vượt ngưỡng. Vùng "BẤT THƯỜNG" đúng nhưng không
   còn phân biệt mức trong vùng đó bằng vạch đóng/mở; phải đọc **điểm số**.
3. **Ổ 2003 không được báo** — nó đã mất cân bằng ngay trong nền khỏe nên mô hình coi là bình
   thường. Muốn bắt cần thêm tầng ngưỡng tuyệt đối theo ISO 20816.
