# Phase 02 — Tầng A, tầng C mức thấp, kiểm tra sau khởi động, thang tốc độ 45 ngày, backtest 2025–2026

**Ngày lập:** 04/09/2026 · **Trạng thái:** **đã duyệt 04/09 12:00, đang làm ngày 1** · **Phụ thuộc:** phase 01 đã khép (tầng B = SAE β = 10⁻³, τ₁₄ = 0,135, hash trong `Dataclean_new/locked_params.json`)

**Quyết định người dùng 04/09 12:00:** ngưỡng 65 µm là **peak-to-peak**, cùng quy ước với thẻ `Direct` (µm pp) → so trực tiếp, không đổi hệ số.

## 1. Mục tiêu

Hoàn thiện hệ **ba tầng** đã chốt (plan.md) để trả lời cả ba câu của nhà máy, và đo lead-time của từng tầng trên hai lần dừng năm 2026. Phase 01 cho thấy tầng B một mình có hai điểm mù: báo động tắt trong tháng 5 khi log SPE bão hòa, và không thấy đợt leo chậm từ 19/07. Phase 02 lấp đúng hai điểm đó.

## 2. Quyết định đã có (không mở lại)

| Điểm | Quyết định |
|---|---|
| Tầng A | Direct 8 kênh, hồi quy 14 ngày chạy, ngoại suy tới 65 µm, báo khi còn < 30 ngày, bỏ 2 ngày đầu sau khởi động, không báo trên đoạn 7 và 2003AX |
| Tầng B | SAE (đã train, `models/SAE_b0.001_s0.pkl`), τ₁₄ = 0,135 giữ nguyên; **thêm thang 45 ngày** τ₄₅ chỉnh mới |
| Tầng C | báo mức thấp "cần xem" khi chiều quay pha 2001 đổi dấu và giữ ≥ 14 ngày, sd pha tuần < 5°; kèm câu giải thích hình dạng 8 kênh |
| Luật xếp hạng | lead-time cắt cụt xếp sau lead-time đo được thật |
| Lead-time | tính tới **quyết định dừng của nhà máy** (29/05/2026 và, nếu có, mốc tương lai), không phải tới hư hỏng |

## 3. Thiết kế từng tầng

### 3.1. Tầng A — ngoại suy Direct tới 65 µm
- Đầu vào: `Dataclean_old/P29201A_clean_long.parquet` (Direct 8 kênh, ~8 h) 2025–2026; sau này là kéo 10 phút.
- Mỗi ngày chạy t, mỗi kênh: hồi quy tuyến tính Direct trung vị ngày trên **14 ngày chạy** gần nhất (đếm ngày máy chạy, bỏ 2 ngày đầu sau mỗi lần dừng); độ dốc b, sai số chuẩn s_b.
- Ngày còn lại D = (65 − mức hiện tại)/b nếu b > 0, vô cực nếu b ≤ 0. Khoảng tin cậy 90% từ b ± 1,645·s_b.
- **Báo** khi cận dưới của D < 30 ngày ở bất kỳ kênh nào, giữ ≥ 2 ngày liên tiếp.
- Đầu ra: bảng ngày × kênh (mức, dốc, D, D_dưới, báo). Kiểm âm: đoạn 7 (dốc âm) và 2003AX (55 µm, phẳng) phải im.

### 3.2. Tầng B — thêm thang tốc độ 45 ngày
- Giữ nguyên SPE của SAE và luật 14 ngày (τ₁₄ = 0,135, ≥ 3 ngày liên tiếp).
- Thêm dốc log SPE trên **45 ngày lịch** (≥ 30 ngày quan sát); báo mức thấp khi > τ₄₅ trong ≥ 5 ngày liên tiếp.
- **Chỉnh τ₄₅ trên đúng bộ cấu hình phase 01** (9c 23/03–30/04 + đoạn 7, 8, 9a): τ₄₅ nhỏ nhất sao cho 0 báo trên đoạn âm. **Không** nhìn đoạn 11 khi chỉnh; đoạn 11 vẫn là kiểm mù cho thang 45 ngày (đây là lý do phase 01 không chỉnh lại τ trên đoạn 11).
- Kỳ vọng ghi trước: đợt leo 19/07→02/09 có dốc 0,035–0,045/ngày ở thang 14 ngày; nếu thang 45 ngày cho dốc ổn định cỡ đó và τ₄₅ chỉnh được dưới mức ấy, tầng B sẽ thấy đợt leo chậm; nếu không, ghi nhận là giới hạn.

### 3.3. Tầng C — chữ ký hệ 8 kênh, báo mức thấp
- Mỗi tuần (giờ máy chạy): trung bình vòng tròn và sd pha 1X từng kênh; tốc độ quay pha (°/tuần) bằng hồi quy trên pha đã unwrap 4 tuần; biên độ trung vị; phần 1X/Direct khi có Direct.
- **Luật báo "cần xem":** dấu của tốc độ quay pha 2001X đổi so với 8 tuần trước và giữ ≥ 14 ngày, với sd pha tuần < 5°. Kèm câu mô tả tự sinh: "2001 tăng/giảm x%, pha quay ±y°/tuần; 2003 …; 2005 …; 2007 …".
- Ghi lịch sử chữ ký: đoạn 7 (giảm, pha −13°), 9c (leo, pha −21°, 2003/2007 quay theo), đoạn 11 (leo chậm, pha **+**). Đợt 19/07 là ca kiểm đầu tiên của luật này.

### 3.4. Kiểm tra sau khởi động
- Kích hoạt khi có khoảng trống máy dừng > 12 h rồi chạy lại. Lấy ngày 10–14 sau khởi động, so với 14 ngày trước dừng và với nền gốc 9b:
  - biên độ 1X từng kênh hồi bao nhiêu % (ổ 2001 tháng 6: −48% so đỉnh, +21% so nền);
  - pha 1X có quay về nền không (2001: 85° so 105°);
  - **kiểm tham chiếu pha tua-bin:** hiệu pha 2005/2007 so nền; lệch > 60° đồng loạt cả 4 kênh với biên độ không đổi → cảnh báo "xoay tham chiếu, cần cộng bù trước khi chấm" (đã xảy ra 148° tại dừng 1).
- Đầu ra: một bảng 8 dòng cho mỗi lần khởi động, in ra cùng đợt báo.

### 3.5. Backtest và lead-time
- Chạy A, B (14 + 45 ngày), C trên toàn chuỗi 9/2025–9/2026 đúng thứ tự thời gian (nhân quả).
- Bảng lead-time: mỗi tầng × hai sự kiện (dừng 1 ngày 04/01/2026; dừng 2 ngày 29/05/2026, đã gộp 2b), kèm cờ cắt cụt và số ngày báo giả trên đoạn âm.
- Kiểm mù cho phần mới (τ₄₅, luật C): đoạn 11, chạy một lần sau khóa, cùng cơ chế hash như phase 01.

## 4. Sản phẩm

| File | Nội dung | Dòng |
|---|---|---|
| `scripts/New/17_tier_a_direct_projection.py` | tầng A; xuất `Dataclean_new/tier_a_daily.parquet` | ≤ 150 |
| `scripts/New/18_tier_b_slow_scale_and_tier_c.py` | dốc 45 ngày trên SPE của SAE; chỉnh τ₄₅ trên bộ cấu hình; chữ ký tuần và luật C; khóa `locked_params_phase02.json` | ≤ 180 |
| `scripts/New/19_restart_check.py` | kiểm tra sau khởi động, gồm kiểm tham chiếu pha | ≤ 120 |
| `scripts/New/20_backtest_three_tiers.py` | chạy ba tầng nhân quả, bảng lead-time, kiểm mù đoạn 11 cho τ₄₅ và luật C (từ chối nếu chưa khóa / đã chạy) | ≤ 150 |
| `scripts/New/21_figures_three_tiers.py` | hình: ba tầng trên một trục thời gian với hai lần dừng và vạch 65 µm | ≤ 120 |
| Báo cáo | mục 3.7 "Ba tầng trên toàn chuỗi" + cập nhật 3.6 đối chiếu chỉ tiêu | |

## 5. Lịch

| Ngày | Việc | Kiểm được |
|---|---|---|
| 1 | Tầng A + backtest riêng tầng A | im trên đoạn 7 và 2003AX; ngày báo đầu trên 9c; D vào 28/05 ≈ 46 ngày như tính tay |
| 2 | Thang 45 ngày: chỉnh τ₄₅ trên bộ cấu hình, khóa; tầng C và lịch sử chữ ký | 0 báo trên đoạn âm; luật C không nổ trên 9c1 (pha quay một chiều) |
| 3 | Kiểm tra sau khởi động cho dừng 1, 2, 2b; backtest ba tầng; kiểm mù đoạn 11 một lần | bảng lead-time; kết quả τ₄₅ và luật C trên đợt 19/07 |
| 4 | Hình; tester + code-reviewer; báo cáo mục 3.7; cập nhật plan | |

## 6. Rủi ro

| Rủi ro | Xử lý |
|---|---|
| Direct chỉ ~8 h/mẫu, 14 ngày chạy = ~40 điểm | khoảng tin cậy sẽ rộng; báo theo cận dưới D, ghi rõ; sau này dùng Direct 10 phút |
| τ₄₅ chỉnh trên một đợt leo nhanh vẫn có thể mù với đợt chậm | đó là kết quả kiểm mù; không chỉnh lại trên đoạn 11 |
| Luật C nổ giả do pha 2007X nhiễu (biên độ nhỏ) | luật chỉ áp cho 2001, kèm điều kiện sd < 5° |
| Tham chiếu pha xoay lần nữa ở lần dừng tới | kiểm tra sau khởi động phát hiện; không tự cộng bù, chỉ cảnh báo |

## 6b. Kết quả ngày 1 — tầng A (04/09/2026 12:15), cần một quyết định

`scripts/New/17_tier_a_direct_projection.py` → `Dataclean_new/tier_a_daily.parquet`. 269 ngày chạy dùng được, 42 ngày bỏ do chặn khởi động.

| Luật | Ngày báo | Kiểm âm đoạn 7 | Cờ trên 2003AX | Báo trước dừng 2 | Kênh gây báo |
|---|---|---|---|---|---|
| Đặc tả: D_low < 30 | 129 | **14 ngày báo — hỏng** | 151 ngày | 05/02 (do 2003AX) | 2003AX, 2003AY |
| + dốc có ý nghĩa (t > 1,645) | 15 | 0 | 22 ngày | 07/02 (do 2003AX) | 2003AX, 2003AY |
| + dốc có ý nghĩa, D điểm < 30 | 7 | 0 | 14 ngày | — | 2003AX, 2003AY |

Ba điều đọc ra:
1. **Luật đặc tả hỏng kiểm âm** vì cận dưới D_low trên kênh phẳng gần ngưỡng bị chi phối bởi sai số dốc. Thêm điều kiện dốc có ý nghĩa thống kê (t > 1,645) là sửa đúng tinh thần "khoảng tin cậy" của đặc tả, đã cài làm mặc định, giữ cột `flag_spec` để đối chiếu.
2. **2003AX vẫn bật cờ 14–22 ngày** dù đã sửa: kênh này ở 54 µm p-p, cách ngưỡng 11 µm, nhiễu ngày 2 µm; mọi lần trôi lên nhỏ đều ngoại suy chạm 65 trong vòng một tháng. Về vật lý, cờ này **không sai**: 2003AX thật sự gần ngưỡng. "Không báo trên 2003AX" là **thói quen chấp nhận của nhà máy**, không phải tính chất của dữ liệu. → Quyết định người dùng: (a) miễn trừ 2003 theo danh sách nhà máy; (b) đổi luật thành "so với mức 90 ngày của chính kênh": chỉ báo khi mức hiện tại cao hơn trung vị 90 ngày ≥ 10% **và** D < 30; (c) giữ cờ 2003AX như một cảnh báo mức thấp riêng ("gần ngưỡng, phẳng").
3. **Tầng A không báo trước dừng 2 cho ổ 2001.** Ngày 28/05, mức 39 µm, dốc 0,46 µm/ngày → còn **57 ngày** tới 65. Nhà máy dừng khi dự phóng còn khoảng hai tháng, tức hành động theo chân trời ~60 ngày, không phải 30. Với chân trời 30 ngày, tầng A là thước "mức tuyệt đối" cho người vận hành, không phải cảnh báo sớm cho đợt này; với chân trời 120 ngày nó báo từ 19/02 nhưng ngoại suy 4 tháng từ 14 ngày dốc là suy đoán. Ghi nhận, không đổi chân trời sau khi nhìn kết quả.

**Quyết định người dùng 04/09 12:30 và kết quả chốt tầng A:** (1) chỉ báo khi kênh **leo so với chính nó** (mức > 1,10 × trung vị 90 ngày của kênh) và dốc có ý nghĩa và D_low < 30; (2) **giữ chân trời 30 ngày**. Kết quả luật chốt: 2 ngày báo trên toàn chuỗi (17–18/06/2026, ổ 2003 hồi sau khởi động), 0 trên đoạn 7, 2003AX 1 ngày cờ, **không báo trước dừng 1 và dừng 2** (28/05: 2001AX còn 57 ngày). Tầng A giữ vai trò thước mức tuyệt đối; cảnh báo sớm thuộc tầng B và C. Ngày 1 **xong**.

## 6d. Code review phase 02 và lần chạy 3 (04/09/2026 13:40) — SỐ LIỆU CHÍNH THỨC

`plans/reports/code-reviewer-260904-1300-phase02-scripts.md` (DONE_WITH_CONCERNS) và `tester-260904-1300-phase02-pipeline.md` (DONE, 7/7 trên lần 1). Lỗi đã sửa: C1 dốc 45 tính riêng episode → toàn chuỗi liên tục; C2 ngày báo tầng C gắn đầu tuần → cuối tuần; C3 bỏ `--force`, chạy lại chỉ khi khóa lại (ghi `reruns`), hash gồm tier_a + feature store, luật C lấy từ khóa; H1 tầng A gate theo giờ trên lưới 1 h (±4 h), cửa sổ không vắt qua dừng, bỏ 2 ngày chỉ sau dừng thật, tham chiếu 90 ngày không gồm ngày hiện tại; H2 tham chiếu 8 tuần theo lịch, |rate| > 1 hai phía; H3 cột `post_restart` (21 ngày); H4 cửa sổ sau khởi động cắt tại dừng kế tiếp, kiểm tham chiếu trên pha thô; H6 cờ cắt cụt; gom hàm chung vào `alarm_utils.py`. Lần 1, 2 lưu `backtest_three_tiers_run1/2.json`.

| Tầng | Dừng 1 | Dừng 2 | Âm 7/8/9a | Mù đoạn 11 |
|---|---|---|---|---|
| A | — | **29/04, 30 ngày** (do 2003Y 35→42 µm; 2001 ngày 28/05 còn 39–58 ngày) | 0/0/0 | 0 / 0 |
| B₁₄ (τ 0,135) | — | **06/04, 53 ngày** | 0/0/0 | 0 / 0 |
| B₄₅ (τ 0,035) | — | **11/04, 48 ngày**, giữ 25/29 ngày tháng 5 | 0/0/— | 0 / 0 (dốc 0,029) |
| C | — | không (một tuần cờ 24–29/05) | 0/0/1 (18–24/01, sau khởi động) | 0 / cờ đơn 28/06, 30/08 |

Kiểm tra sau khởi động: 4 lần dừng thật; lần 29/05 "chưa đủ 3 ngày" (dừng 2b tới sớm). Ngày 2–3 **xong**; còn: tester chạy lại lần 3 (tùy chọn), báo cáo 3.6 đã thay số.

## 6c. Kết quả ngày 2–3, lần chạy 1 (04/09/2026 12:50) — ĐÃ THAY BẰNG 6d, giữ để đối chiếu

- **Thang 45 ngày:** τ₄₅ = 0,04 (τ nhỏ nhất để đoạn 7 và 8 im; 9a chỉ 21 ngày nên không kiểm được ở thang này; ep8 dốc max 0,042 ngay sát τ). Báo đầu trên 9c: **25/04 (34 ngày)**, và **giữ báo suốt 25/29 ngày tháng 5** → lấp điểm mù "tắt trước khi dừng" của thang 14 ngày.
- **Kiểm mù đoạn 11 cho thang 45:** dốc max đợt leo 0,029 < 0,04 → **vẫn không báo**; bình nguyên 0 báo. Kết luận: cả hai thang tốc độ đều mù với đợt leo chậm; τ được chỉnh trên một sự kiện nhanh không chuyển sang sự kiện chậm gấp ba.
- **Luật C:** nổ 2 tuần trên phần không mù: **18/01 (9a, đợt xoay pha 33° sau tháo lắp)** và **24/05 (9c, 5 ngày trước dừng 2)**. Trên đoạn 11: cờ đơn 28/06 và **30/08** (tốc độ quay đổi dấu sang +1,7°/tuần hai tuần liền, khớp "pha đổi chiều" đã thấy tay), chưa đủ 2 tuần liên tiếp tại ngày cuối dữ liệu → **chưa báo, có thể báo tuần 06/09**. Lần nổ 18/01 là hệ 8 kênh đổi hình dạng thật sau tháo lắp; ghi là "cần xem" đúng nghĩa, không tính báo giả.
- **Kiểm tra sau khởi động:** 4 lần dừng thật (04/11/2025; 04/01, 29/05, 10/06/2026) sau khi lọc bằng Direct; khoảng trống 05/02–20/02 và 22/03 chỉ là thiếu dữ liệu kéo, không phải dừng. Dừng 1: 2001 −49% biên độ, pha +25° so trước dừng; dừng 2: 2001 −25%, sau 10/06 lại +106% (hồi về bình nguyên). **Lưu ý:** kiểm tham chiếu pha chạy trên kho đặc trưng đã cộng 148°, nên không "tái phát hiện" được lần xoay tháng 1; trong vận hành phải chạy trên pha thô.
- **Bảng lead-time (backtest_three_tiers.json):** dừng 1: không tầng nào báo (đúng kỳ vọng ghi trước). Dừng 2: **B14 = 53 ngày (06/04), B45 = 34 ngày (25/04), C = 5 ngày (24/05), A = không báo** (28/05 còn 57 ngày). Đoạn âm: B14 và B45 = 0; C = 1 (18/01, xem trên).
- Kiểm mù đoạn 11 tổng hợp: A báo 2 ngày trên bình nguyên (17–18/06, ổ 2003 hồi sau khởi động, tính là báo giả của A); B14, B45, C: 0 báo giả, 0 báo đợt leo tới 02/09.

## 7. Tiêu chí hoàn thành

- [ ] Tầng A: 0 báo trên đoạn 7 và 2003AX; báo trên 9c trước 29/05 với ngày cụ thể.
- [ ] τ₄₅ khóa với hash; 0 báo trên đoạn âm; kết quả trên đoạn 11 ghi một lần.
- [ ] Luật C: ngày báo "cần xem" đầu tiên trên đoạn 11 (kỳ vọng đầu tháng 8) và 0 báo trên 9c1.
- [ ] Ba bảng kiểm tra sau khởi động (dừng 1, 2, 2b), gồm cờ xoay tham chiếu 148° ở dừng 1.
- [ ] Bảng lead-time ba tầng × hai sự kiện; hình ba tầng; tester và code-reviewer xong; báo cáo 3.7.

## Quyết định người dùng (04/09/2026 12:00)

- **Dừng 2b (11–13/06) gộp với dừng 2 (29/05–01/06)** thành một sự kiện "dừng tháo kiểm tra lần 2"; lead-time đo tới 29/05 10:40. Bảng lead-time có hai sự kiện: dừng 1 (04/01/2026) và dừng 2 (29/05/2026). Với dừng 1, dữ liệu trước đó (đoạn 8) là bình nguyên nên kỳ vọng ghi trước: các tầng **không báo**, lead-time = không có; đây là kết quả hợp lệ (nhà máy dừng không kèm dấu hiệu trong dữ liệu), không phải lỗi.

## Câu hỏi còn mở

- Không còn. (65 µm = peak-to-peak, đã xác nhận 04/09 12:00.)
