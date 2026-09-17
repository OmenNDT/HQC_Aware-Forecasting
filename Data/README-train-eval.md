# HQC — Hai bộ dữ liệu: TRAIN và ĐÁNH GIÁ

Nguồn: `PI Data.xlsx` sheet `51_Vib180d` (rung, 8 đầu × 1X Amp + 1X Phase) ghép
`33_Aligned` (11 biến quá trình) trên lưới **1 giờ**. Tổng ghép được 4.237 giờ
(05/02/2026 → 01/08/2026).

## Làm sạch và cổng lọc đã áp
| Bước | Quy tắc | Loại bỏ |
|---|---|---|
| Rác 6,4e-17 | `\|v\|<1e-10` → khuyết | 29FI2005 568 ô, 29FI2006 2.664 ô |
| Rác 29SIC2001A | giá trị `=0` → khuyết | 8.836 ô (16,8%) |
| Máy dừng | cần ≥6/8 kênh 1X Amp > 3 µm | 116 giờ |
| Tải thấp | cần lưu lượng 29FI2005 ≥ 20.000 | 122 giờ |
| Vùng chuyển tiếp | 28/05–13/06/2026 (máy về tải tối thiểu rồi khởi động lại) | 408 giờ — **loại khỏi train**, giữ trong eval |

## FILE 1 — `HQC_train_healthy.csv` (KHÔNG có nhãn)
- **1.307 giờ**, 05/02/2026 → 31/03/2026. 27 cột: 8 × 1X Amp + 8 × 1X Phase + 11 biến tải.
- Dùng cho **huấn luyện không giám sát**: mô hình học tái tạo nếp bình thường.
- **KHÔNG có cột nhãn** — đúng bản chất unsupervised.

### ⚠ Điều phải nêu rõ khi báo cáo
Ổ **29VT-2003 ĐÃ mất cân bằng ngay trong cửa sổ nền** (1X Amp ≈ 47,7 µm). Nghĩa là
mô hình sẽ coi mức đó là "bình thường của máy này" và **KHÔNG báo động ổ 2003**.
Nó chỉ báo cái **lệch khỏi nền** — thực tế là ổ **2001**.
→ Đây không phải lỗi, mà là đặc tính của phương pháp: nó phát hiện **thay đổi**, không phát hiện **mức tuyệt đối xấu**.
Muốn bắt cả 2003 thì cần thêm một tầng đối chiếu ngưỡng tuyệt đối (ISO 10816/API 610).

## FILE 2 — `HQC_eval_expert.csv` (có nhãn ứng viên + cột cho chuyên gia)
- **350 mẫu**: 150 "bình thường" + 200 "bất thường" — mirror đúng cấu trúc tập đánh giá của paper trụ.
- Khoảng 01/04/2026 → 31/07/2026. **Không chứa giờ nào đã dùng train** (chống rò rỉ).
- Rải đều theo thời gian (chia khối, lấy 1 mẫu ngẫu nhiên mỗi khối, seed 42).

### Nhãn ứng viên sinh từ đâu — QUAN TRỌNG
Nhãn ứng viên **KHÔNG** sinh từ residual của bất kỳ mô hình nào (nếu vậy sẽ là lập
luận vòng tròn). Nó sinh từ **thống kê mô tả trên dữ liệu thô**: dải p1–p99 của
từng cảm biến trong cửa sổ nền.

| Nhãn | Luật |
|---|---|
| `bat_thuong` | lệch ≥ 25% ngoài dải nền p1–p99 |
| `can_xem` | lệch 10–25% |
| `binh_thuong` | trong dải nền |
| `loai_bo_...` | máy dừng hoặc tải thấp |

Dải nền p1–p99 (µm): 2001X 11.3–18.3, 2001Y 10.9–17.2, 2003X 43.1–52.6, 2003Y 28.8–34.9, 2005X 9.4–10.6, 2005Y 8.1–9.0, 2007X 5.7–7.2, 2007Y 10.8–14.2

### Ba cột chuyên gia điền
| Cột | Điền gì |
|---|---|
| `CHUYEN_GIA_xac_nhan` | `Đúng` / `Sai` — nhãn ứng viên có đúng không |
| `CHUYEN_GIA_nhan_dung` | nếu Sai: nhãn đúng là gì (`binh_thuong` / `bat_thuong`) |
| `CHUYEN_GIA_ghi_chu` | căn cứ (lịch sử bảo trì, mở máy thấy gì, kinh nghiệm) |

**Yêu cầu về tính độc lập:** chuyên gia phải có quyền **bác** nhãn ứng viên. Sau khi
điền, ta **ghi lại tỉ lệ chuyên gia sửa** — đó là chỉ số minh bạch bắt buộc báo cáo.
Nếu tỉ lệ sửa ≈ 0% thì nhãn thực chất là của luật thống kê, không phải của chuyên gia.

### Cột hỗ trợ đọc
`lech_lon_nhat_pct` (lệch lớn nhất so dải nền), `cam_bien_lech_nhat`,
`so_cam_bien_ngoai_dai`, `may_chay`, `co_tai` — để chuyên gia không phải tự tính.

## Lưu ý phương pháp về pha
Độ lệch chuẩn pha phải tính bằng **công thức vòng tròn**, không dùng std thường:
29VT-2001Y std thường 155,7° nhưng std vòng tròn chỉ **15,4°** (95,4% điểm nằm gần 0/360°).
Tương tự 2005X: 27,3° → thật **3,8°**.
