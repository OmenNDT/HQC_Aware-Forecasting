# HQC_Aware-Forecasting — DANH SÁCH DỮ LIỆU CẦN KÉO (PI Datalink) — v2

> Nguồn: PI Data Archive qua PI Datalink. Máy gốc: P29201A-HP BFW Pumps (server \\SRV-PI-AF01),
> nhưng **mở rộng ra nhiều máy quay trong cụm** — đó là lợi thế lớn nhất so với paper tham chiếu.
>
> **v2 thay đổi gì:** đưa `Run Hours - Since Last Service` (đa máy) lên **Tầng 0** — nó là chìa khóa
> định vị chuỗi chạy-đến-hỏng (run-to-failure) mà không cần xin nhật ký bảo trì.

## QUY TẮC KÉO — đọc trước khi làm
- Lấy **PI Point GIÁ TRỊ GỐC**: tag kết thúc ở `|Direct`, `|1X Amp`, `|1X Phase`, `|Temperature`, `|Gap`.
- **TUYỆT ĐỐI KHÔNG** lấy đuôi `|Trigger|Current percent` — đó là % tiệm cận ngưỡng cảnh báo, = 0 hằng số.
  Chính cái bẫy này đã làm 3 bản export dài trước đó vô dụng.
- **PISampDat** (interval cố định) → tốt cho ma trận căn thời gian. **PICompDat** (raw) → biết cadence thật.
- Xuất mỗi nhóm 1 sheet: cột = tag, hàng = timestamp. **Giữ nguyên tên tag đầy đủ** (để tôi parse đúng).

═══════════════════════════════════════════════════════════════════
# TẦNG 0 — HAI VIỆC SONG SONG (bắt buộc, làm trước hết)

## 0A. ⭐ Run Hours ĐA MÁY — tìm chuỗi chạy-đến-hỏng
**Đây là mục quan trọng nhất của cả danh sách.**

| Tag | Máy | Interval | Khoảng |
|---|---|---|---|
| `...\<TÊN MÁY>\|Running Time\|Run Hours - Since Last Service` | **CÀNG NHIỀU máy quay càng tốt** (mọi bơm/máy nén/tua-bin trong cụm Steam Generation & lân cận) | 1h | DÀI NHẤT có (>=3-5 năm) |
| `...\<TÊN MÁY>\|Status` | cùng các máy trên | 1h | như trên |

**Cách dùng (vì sao quý):** mỗi lần `Run Hours` **RESET về 0** = một lần can thiệp bảo trì.
→ Đoạn dữ liệu **NGAY TRƯỚC mốc reset** chính là chuỗi suy giảm dẫn tới sửa chữa = "run-to-failure".
→ Đây là thứ paper tham chiếu (Entropy 2021) phải nhờ công ty đối tác cung cấp; anh **suy ra được từ PI**.

**Kết quả cần:** một bảng "máy nào — reset lúc nào" → từ đó chọn máy + khoảng thời gian cho mục 0B.

## 0B. Trục chính cảm biến — máy P29201A (và các máy có mốc reset tìm được ở 0A)

| Nhóm | Tag (giá trị THẬT) | Interval | Khoảng |
|---|---|---|---|
| Rung Direct (8) | `29VT-2001X/Y, 2003X/Y, 2005X/Y, 2007X/Y \| Direct` | 1h (và 10m nếu được) | DÀI NHẤT có |
| Rung 1X Amp (8) | `...VT... \| 1X Amp` | như trên | như trên |
| Rung 1X Phase (8) | `...VT... \| 1X Phase` | như trên | như trên |
| Nhiệt ổ đỡ (10) | `29TE-2003,2004,2005,2035,2036,2037,2038,2039,2055,2056 \| Temperature` | như trên | như trên |
| Vị trí trục (3) | `29XT-2012,2013,2026 \| Direct` + `\| Gap` | như trên | như trên |

→ Câu hỏi 0B trả lời: PI Archive có giữ **giá trị thật** rung/nhiệt dài hạn không (khác bản CBM export)?

═══════════════════════════════════════════════════════════════════
# TẦNG 1 — BỐI CẢNH VẬN HÀNH (điều kiện cho condition-aware)
Cùng khoảng thời gian Tầng 0. Đây là thứ **paper tham chiếu KHÔNG có** → điểm vượt lên của đề tài.

| Biến | Tag | Interval |
|---|---|---|
| Tốc độ | `29SIC2001`, `29SIC2001A` | 10m |
| Lưu lượng | `29FI2005`, `29FI2006` | 10m |
| Áp suất | `29PI2011`, `29PI2012`, `29PDI2007A` | 10m |
| Mức | `29LI2002A` | 10m |
| Nhiệt process | `29TI2030`, `29TI2031`, `29TI2026A` | 10m |
| Hiệu suất | `Performance Efficiency \| P1, P2, T1, T2` | 10m |
| Trạng thái chạy | `Steady Running State` | 1h |

═══════════════════════════════════════════════════════════════════
# TẦNG 2 — NHIỀU MÁY (tổng quát hóa — paper chỉ có 1 loại máy nén)

- **Máy song song cùng loại** (P29201**B** nếu có): kéo ĐÚNG bộ Tầng 0B + Tầng 1, cùng khoảng thời gian.
  Hai máy cùng điều kiện = chứng âm/chứng dương mạnh nhất.
- **Các máy có mốc reset Run Hours** (từ 0A): kéo bộ Tầng 0B + 1 phủ **trước và sau** mốc.
  → mỗi máy là một "case" → đề tài từ 1 case lên **phương pháp nhiều máy** (paper tự nhận là hạn chế).

═══════════════════════════════════════════════════════════════════
# TẦNG 3 — ĐỘ PHÂN GIẢI CAO (chữ ký chẩn đoán)
- **Vài khối 8h cadence 3s** (Direct + 1X Amp + 1X Phase, 8 đầu VT) ở **CÁC ĐIỀU KIỆN KHÁC NHAU**:
  1 khối tải cao, 1 khối tải thấp, 1 khối tốc độ khác → thấy chữ ký rung đổi theo điều kiện.
- **Waveform** (nếu xuất được): `29VT-2003X` (ổ nghi mất cân bằng) tại 2-3 thời điểm.

═══════════════════════════════════════════════════════════════════
# METADATA (1 lần, không cần chuỗi)
- Nameplate: công suất, tốc độ định mức (rpm), số/kiểu ổ đỡ.
- Ngưỡng cảnh báo hệ đặt cho mỗi cảm biến (Alarm/Trip) — đối chiếu với ngưỡng thống kê ta tự tính.
- Sơ đồ vị trí cảm biến: ổ nào trên tua-bin, ổ nào trên bơm (cần cho cấu trúc CÂY theo hệ con).
- Danh sách máy quay trong cụm + tên tag PI của chúng (để làm 0A).

═══════════════════════════════════════════════════════════════════
# THỨ TỰ ƯU TIÊN
1. **0A — Run Hours đa máy** → định vị máy nào từng hỏng, hỏng lúc nào. Mở khóa lead-time thật (M2)
   và tập run-to-failure. **Làm trước tiên, rẻ nhất, giá trị cao nhất.**
2. **0B — Trục chính P29201A dài nhất có thể** → xác nhận PI giữ giá trị rung/nhiệt thật dài hạn.
3. **Tầng 1** → mở khóa condition-aware (điểm paper không có).
4. **Tầng 2** → nhiều máy, nâng tầm đề tài.

## Ghi chú định vị so với paper tham chiếu (Entropy 2021, DOI 10.3390/e23010083)
Paper học **KHÔNG GIÁM SÁT** (train chỉ trên dữ liệu bình thường, không cần nhãn) → ta tái hiện được
ngay với dữ liệu hiện có. Sáu chỗ dữ liệu của anh cho phép **vượt lên**: nhiều máy · vector rung
1X Amp/Phase (paper chỉ vô hướng) · condition-aware theo tải/tốc độ · giới hạn kiểm soát thống kê
thay ngưỡng chỉnh tay (điểm paper tự nhận yếu) · cấu trúc cây theo hệ con (paper đề xuất làm tương
lai) · triển khai nhúng Int8/MCU (paper không làm).
