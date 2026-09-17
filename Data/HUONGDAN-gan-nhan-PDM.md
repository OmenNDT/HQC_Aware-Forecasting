# HƯỚNG DẪN GÁN NHÃN — dành cho chuyên gia PDM

Máy: **P29201A** (tổ tua-bin hơi + bơm cấp nước HP), 4 ổ đỡ × 2 hướng = 8 đầu đo rung.
File: `HQC_eval_expert.csv` — **350 dòng**, mỗi dòng là **một giờ vận hành**.
**3 dòng đầu đã điền sẵn làm ví dụ.** 347 dòng còn lại cần anh/chị điền.

## Việc cần làm — chỉ 2 cột bắt buộc

| Cột | Điền gì |
|---|---|
| `CHUYEN_GIA_xac_nhan` | `Đúng` hoặc `Sai` — cột `nhan_ung_vien` có đúng không |
| `CHUYEN_GIA_nhan_dung` | Nếu điền `Sai`: nhãn đúng là gì (`binh_thuong` hoặc `bat_thuong`) |
| `CHUYEN_GIA_ghi_chu` | (không bắt buộc) căn cứ — càng ghi càng tốt |

**Cột `nhan_ung_vien` là máy tự gắn bằng một luật thống kê thô.** Nó KHÔNG phải chẩn đoán.
Việc của anh/chị là **xác nhận hoặc bác nó** bằng chuyên môn.

> **Rất mong anh/chị BÁC những dòng luật gắn sai.** Nếu tất cả 347 dòng đều `Đúng` thì
> nghĩa là nhãn vẫn là của cái luật thống kê, không phải của chuyên gia — và phần đánh giá
> của nghiên cứu mất giá trị. Ví dụ mẫu số 3 là một dòng luật gắn SAI.

## Đọc dòng dữ liệu thế nào

**Cột quan trọng nhất — `1X_Amp_29VT-xxxx`**: biên độ thành phần 1X (µm) của 8 đầu đo.
So với **dải nền** (máy chạy bình thường giai đoạn 05/02–31/03/2026):

| Đầu đo | Dải nền (µm) | Ghi chú |
|---|---|---|
| 29VT-2001X | 11,3 – 18,3 | |
| 29VT-2001Y | 10,9 – 17,2 | |
| **29VT-2003X** | **43,1 – 52,6** | ổ này đã mất cân bằng từ trước — mức cao này là "nền" của nó |
| 29VT-2003Y | 28,8 – 34,9 | |
| 29VT-2005X | 9,4 – 10,6 | |
| 29VT-2005Y | 8,1 – 9,0 | |
| 29VT-2007X | 5,7 – 7,2 | |
| 29VT-2007Y | 10,8 – 14,2 | |

**Cột `1X_Phase_29VT-xxxx`**: pha 1X (độ). Pha nền: 2001X ≈ 106° · 2001Y ≈ 14° ·
2003X ≈ 218° · 2003Y ≈ 125° · 2005X ≈ 8° · 2005Y ≈ 293° · 2007X ≈ 153° · 2007Y ≈ 71°.
*Pha lệch nhiều = điểm nặng đổi hướng — dấu hiệu nghiêm trọng hơn là chỉ biên độ tăng.*

**Cột hỗ trợ (máy tính sẵn, khỏi phải tính tay):**
- `lech_lon_nhat_pct` — lệch lớn nhất so dải nền (%). **Dấu + = cao hơn nền, dấu − = thấp hơn nền.**
- `cam_bien_lech_nhat` — đầu đo nào lệch nhiều nhất
- `so_cam_bien_ngoai_dai` — mấy đầu đo ra ngoài dải
- `may_chay`, `co_tai` — 1 = máy đang chạy có tải
- `29SIC2001` tốc độ (rpm) · `29FI2005` lưu lượng — để xét bối cảnh vận hành

## Bối cảnh vận hành cần biết
- **29–31/05/2026:** máy về tải tối thiểu (3.910 rpm, lưu lượng ~1.100) rồi khởi động lại 01/06.
  Sau khởi động lại, rung ổ 2001 **thấp hơn** trước khi dừng.
- **11–13/06/2026:** một đợt tải thấp ngắn nữa.
- Ngoài hai đợt đó, máy chạy khá ổn định ~4.765–4.820 rpm.

## Nguyên tắc phân biệt (gợi ý, anh/chị quyết)

| Tình huống | Thường là |
|---|---|
| Mọi đầu đo trong dải nền | `binh_thuong` |
| Một/vài đầu đo **CAO hơn** nền rõ rệt, các đầu khác không | `bat_thuong` |
| Biên độ tăng **kèm pha dịch** nhiều | `bat_thuong` (nặng hơn) |
| **THẤP hơn** nền (dấu −) | thường **`binh_thuong`** — rung giảm không phải hư hỏng |
| Mọi đầu đo cùng tăng/giảm đồng loạt | xét tải trước — có thể do vận hành |
| 2003X ở mức 43–53 µm | `binh_thuong` với máy này (đó là nền của nó) |

## Ba ví dụ mẫu trong file
1. **01/04 00:00** — mọi kênh trong dải, pha ổn định → luật gắn `binh_thuong`, **Đúng**.
2. **28/05 13:00** — 2001X 35,4 µm (gấp đôi nền), pha dịch 23° → luật gắn `bat_thuong`, **Đúng**.
3. **03/06 09:00** — lệch −31,8% nhưng **xuống thấp** (2001X chỉ 7,9 µm), 3 ngày sau khởi động
   lại → luật gắn `bat_thuong` là **SAI**, nhãn đúng `binh_thuong`. **Đây là dạng dòng cần bác.**

## Nếu không chắc
Ghi `Sai` + để trống `CHUYEN_GIA_nhan_dung` + ghi chú "không chắc, cần xem waveform/lịch sử".
Chúng tôi sẽ loại dòng đó khỏi tập đánh giá — **tốt hơn là đoán**.
