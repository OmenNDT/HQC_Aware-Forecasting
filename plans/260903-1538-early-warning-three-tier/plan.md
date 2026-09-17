# Cảnh báo sớm 3 tầng cho P29201A — kế hoạch

**Ngày:** 03/09/2026 · **Cập nhật:** 03/09/2026 20:40 · **Trạng thái:** phase 01 chờ duyệt · **Chế độ:** fast

## Bối cảnh đã chốt với người dùng

- **Nhà máy:** ngưỡng cứng Direct **65 µm**, áp cả 8 kênh. Hai lần dừng (04–14/01 và 29/05–01/06 + 11–13/06/2026) là **dừng tháo kiểm tra**, không phát hiện gì, Run Hours không reset. Nhà máy coi hiện tại là bình thường.
- **Tiên đề hệ 8 kênh:** "ổn định" là ổn định của cả hệ 8 cảm biến, không phải của riêng 2001. Mọi thước chọn nền, chữ ký, giải thích đều tính trên 8 kênh.
- **Ổ 2001:** hai chu kỳ leo (20 → 43 µm tới 29/05; 13 → 27 trong 10 ngày sau 01/06), pha 1X quay đều −4°/tháng suốt 10 tháng; **từ 19/07 leo lại +2 µm/tháng và pha đổi chiều** (+7,5°/tháng). Sau mỗi lần tháo lắp vector không quay về nền.
- **Tham chiếu pha tua-bin xoay 148°** tại lần dừng 1 (giữa 04/01 và 15/01), chỉ ở 2005/2007, biên độ và hiệu X−Y không đổi. Không phải do mẫu kéo: mẫu mới và `51_Vib180d` khớp từng giờ trên cả pha. Từ 15/01/2026 mọi dữ liệu cùng một tham chiếu.
- **Archive 1X sâu ≥ 340 ngày**, không phải 270 như tài liệu cũ.

## Ba tầng (chốt)

| Tầng | Câu hỏi | Cách tính | Dữ liệu | Trạng thái |
|---|---|---|---|---|
| A. Dự phóng tới ngưỡng | bao lâu nữa chạm 65 µm | hồi quy Direct 14 ngày chạy, ngoại suy tới 65, khoảng tin cậy 90%; báo khi còn < 30 ngày; bỏ 2 ngày đầu sau khởi động | Direct 8 kênh, file 5 năm | phase 02 |
| B. Lệch nền gốc | có còn giống lúc khỏe không | **trạng thái** = SPE so nền gốc 9b (mô hình chọn ở phase 01); **báo động** = tốc độ tăng log SPE trên 14 ngày; vượt giới hạn 99% liên tục ≥ 6 h mới tính | 1X Amp/Phase 8 kênh, 10 phút | phase 01 |
| C. Chữ ký hệ | cũ hay mới | hình dạng thay đổi của cả 8 kênh (Δamp, chiều và tốc độ quay pha, phần 1X/Direct). **Đề xuất nâng:** báo mức thấp khi chiều quay pha đổi hoặc hình dạng khác đợt đã biết (đợt 19/07 là ví dụ). Chưa có 2X | 1X pha + Direct | phase 02, chờ người dùng quyết mức báo |

## Quyết định đã chốt

| Điểm | Quyết định |
|---|---|
| Nền gốc | **9b, 20/02–22/03/2026, toàn bộ file 10 phút** `Doan9b_20.02.26-22.03.26.xlsx`. Lý do: ổn định nhất theo thước hệ (dốc 2,0 %/th, pha 4,4 °/th), sạch nhất (2001 = 17,5 µm), cùng tham chiếu pha với vận hành. Không đổi theo chu kỳ. Hình: `Bao_cao/hinh-chon-nen-goc-9b.png` |
| Vì sao không phải 9a | 9a (15/01–05/02) sạch hơn 37% nhưng cả hệ đang lắng sau tháo lắp: 2003 giảm 6–8 µm/th, pha 2001 xoay 33° trong 5 ngày. Là **thử âm mạnh**, không phải nền |
| Mẫu kéo | mẫu mới 10 phút, 16 cột, timestamp serial Excel; đọc bằng `scripts/11_profile_1x_episode_pull.py::load_pull` |
| Đoạn 7, 8 | thử âm; cộng **+148°** vào pha 2005/2007 trước khi dùng |
| Tầng B khi máy khác nền lâu dài | mức = trạng thái, tốc độ = báo động (một nền, không nền chu kỳ) |
| Tầng A | cửa sổ 14 ngày, báo khi < 30 ngày, 65 µm cho cả 8 kênh |
| Bước lấy mẫu | 10 phút là đủ; mịn hơn không thêm thông tin (nhiễu 10 phút = nhiễu 1 giờ, tự tương quan 6 h). Muốn nhiều mẫu hơn phải **dài hơn** |

## Chia train / val / test (chốt, chi tiết ở phase 01 mục 2 và 5)

| Tập | Dữ liệu | Vai trò |
|---|---|---|
| Train / val / test trong nền | 9b, 5 khối × ~6 ngày, trống 1 ngày; fold i: test = Kᵢ, val = Kᵢ₋₁, train = 3 khối còn lại | trọng số · dừng sớm · SPE ngoài mẫu → giới hạn |
| Cấu hình dương | 9c 23/03–29/05 | chọn dung lượng, ngưỡng tốc độ, lead-time tới dừng 2 |
| Cấu hình âm | đoạn 8 (02/12–01/01), đoạn 7, 9a | báo động phải = 0 |
| Chỉ báo cáo | 05/02–19/02 (leo vào nền, 1 giờ), 9c 02–10/06 (quá độ) | không chọn tham số |
| Kiểm mù | đoạn 11, 14/06–02/09 | chạy một lần |
| Nghiệm thu mẫu | 350 mẫu chuyên gia, **tách hai cột**: trong 9c (210 mẫu) và trong đoạn 11 (140) | chấm, không chọn |

## Dữ liệu 1X đã có (mẫu mới, 10 phút; parsed trong `Dataclean/P29201A_1X_*.parquet`)

| Đoạn | File | Dòng | Ghi chú |
|---|---|---|---|
| 7 · 28/09–04/11/2025 | `28.9.25-4.11.25.xlsx` | 5.329 | giảm −5,5 µm/th; pha 2005/2007 +148° |
| 8 · 07/11/2025–04/01/2026 | `Doan8_7.11.25-4.01.26.xlsx` | 8.353 | bình nguyên 21; 2007X NaN 29%; +148° |
| 9a · 15/01–05/02/2026 | `Doan-9a.15.01.26–05.02.26.xlsx` | 3.025 | 2001 = 11 µm; đang lắng; 2007X NaN 8% |
| **9b · 20/02–22/03/2026** | `Doan9b_20.02.26-22.03.26.xlsx` | 4.321 | **nền gốc**, khớp `51_Vib180d` Δ = 0 |
| 9c · 23/03–13/06/2026 | `Doan9c_23.03.26-13.06.26.xlsx` | 11.809 | leo 17 → 32; NaN = lúc dừng; khớp `51_Vib180d` |
| 11 · 14/06–02/09/2026 | `Doan11_14.06.26-2.09.26.xlsx` | 11.521 | kiểm mù; leo lại từ 19/07 |

## Phase

| Phase | File | Trạng thái |
|---|---|---|
| 01 | [phase-01-train-six-models-blocked-cv.md](phase-01-train-six-models-blocked-cv.md) — 7 mô hình trên nền 9b, 5 khối ba vai, chọn mô hình tầng B | **xong kỹ thuật (04/09 00:05)**, chờ 3 quyết định người dùng để khép |
| 02 | [phase-02-tier-a-tier-c-restart-check-backtest.md](phase-02-tier-a-tier-c-restart-check-backtest.md) — tầng A (Direct → 65 µm p-p), tầng B thêm thang 45 ngày, tầng C báo mức thấp, kiểm tra sau khởi động (gồm kiểm tham chiếu pha), backtest ba tầng, lead-time hai lần dừng (2b gộp vào 2) | **đã duyệt 04/09 12:00**, đang làm ngày 1 |
| 03 | Demo phát lại ba tầng theo ngày (HTML tự chứa, số liệu nhúng từ phase 02) + quay video câm 6 phút bằng ffmpeg x11grab, Computer Use thao tác theo kịch bản 5 cảnh; đối tượng: giảng viên "AI trong hệ thống nhúng" → [phase-03](phase-03-demo-replay-dashboard-and-screen-recording.md) | **HOÀN THÀNH 04/09 16:40** (video 6:02, 8 khung, báo cáo 3.8) |
| 04 | Lượng tử hóa SAE int8 (mã C viết tay, bảng tra tanh) + nhúng ba tầng lên **ESP32-S3 DevKitC**, phát lại qua UART, đối chiếu 100 % ngày báo với backtest; 3 ngày đầu không cần bo (tham chiếu, lượng tử, C trên x86, ESP-IDF build) → [phase-04](phase-04-quantize-sae-int8-embed-esp32s3.md) | **HOÀN THÀNH 06/09** (trên bo: trùng từng dòng, 646 µs/mẫu, heap còn 354 KB) |

## Ràng buộc

- Nền gốc cố định ở 9b; không dời theo chu kỳ.
- Không trộn dữ liệu trước 15/01/2026 với sau đó ở pha 2005/2007 nếu chưa cộng 148°.
- Tầng A: bộ chặn khởi động 2 ngày; không được báo trên đoạn 7 (đang giảm) và 2003AX (cao, phẳng).
- Không mock dữ liệu; mọi số in ra đọc từ file.
- Mọi mô hình dưới 200 dòng/file; scaler fit trên train của fold.

## Todo

- [x] Kế hoạch; chốt 3 tầng; chốt nền gốc 9b; hình chọn nền
- [x] Hồ sơ 6 lần kéo 1X (script 11), xác nhận tham chiếu pha, đoạn 9c/9a/11
- [x] Kế hoạch train phase 01 (+ artifact)
- [x] Người dùng duyệt phase 01 (20:55): đủ 5 fold; tách 9c hai nửa (chỉnh 23/03–30/04, kiểm trước 01–29/05); một ngưỡng tốc độ chung; tầng C báo mức thấp
- [x] Phase 01 ngày 1 (21:30): `scripts/New/12_build_feature_store.py` → `Dataclean_new/feature_store_1x.parquet` (42.412 dòng); `scripts/New/13_blocked_cv_train_compare.py` + `scripts/New/models/` → `Dataclean_new/cv_results.csv`, `Dataclean_new/spe/PCA_k*.parquet`. Người dùng đã tách thư mục: mã cũ `scripts/Old/`, dữ liệu cũ `Dataclean_old/`, mới `scripts/New/`, `Dataclean_new/`
- [x] Soi k=6 vs k=4 (21:40): k=4 ổn định giới hạn hơn (FA fold max 4,5% vs 23%) và báo sớm hơn 3 ngày; k=6 giải thích đúng ổ 2001 (60% đóng góp đợt leo, k=4 chia cho 2003X/2007Y). Cắt 6 ngày đầu 9b làm tệ hơn. **Chọn k=6 theo yêu cầu người dùng + tiêu chí "chỉ đúng ổ"**, giữ k=4 so sánh. τ chung sơ bộ 0,06 → lead-time 43 ngày (16/04 → 29/05), 0 báo giả trên 7/8/9a
- [x] `scripts/New/16_figures_model_comparison.py` (bản PCA) → `Bao_cao/hinh-tang-b-PCA_k6-spe.png`, `hinh-so-sanh-pca-k.png`
- [x] Cập nhật báo cáo `Bao_cao/Bao-cao-do-an-final.md`: Bảng 3.1b (6 lần kéo), sửa archive 270→≥340, mục 3.5 mới (giai đoạn 2), 3.6 đối chiếu chỉ tiêu hai giai đoạn
- [x] Phase 01 ngày 2–4 (22:10): 27 cấu hình xong (`cv_results.csv`); script 14 khóa **τ = 0,135** (luật: nhiều mô hình đạt nhất → 26/27), chọn **SAE_b0.001_s0** (lead 56 ngày, 03/04); PCA k=6 chỉ 29 ngày ở τ chung (43 ở τ=0,06). Kiểm mù đoạn 11: 0 báo giả bình nguyên, **không mô hình nào báo đợt leo chậm 19/07→** (dốc 0,02–0,04 < τ); báo động tắt trong tháng 5 dù máy leo tiếp (log SPE bão hòa). Hình: `hinh-so-sanh-7-mo-hinh.png`, `hinh-tang-b-SAE_b0.001_s0-spe.png`. Báo cáo: mục 3.5.6–3.5.7
- [x] Tester (`plans/reports/tester-260903-2200-phase01-pipeline.md`): 7 bước đạt, pipeline tái lập, purge/scaler/hash đúng
- [x] Code-reviewer (`plans/reports/code-reviewer-260903-2200-phase01-scripts.md`): DONE_WITH_CONCERNS — C1 blind bị chấm trước khóa; C2 khóa lệch hash; C3 fit lại bỏ qua epoch fold; H1 tiêu chí 1 bị vô hiệu (`or True`); H2 τ dùng cả nửa kiểm trước; H3 τ do mô hình nhiễu nhất quyết; H4 lead-time SAE bị cắt cụt (03/04 = ngày sớm nhất luật có thể nổ); H5 6h median≠sample; H6 cửa sổ vắt qua khoảng trống trong ep8; H7 đua ghi CSV; ED-CNN interpolate, VAE reseed RNG, DBN 49 hàng đầu thô
- [x] **Sửa toàn bộ (23:05)**: `phase01_config.py` hằng số chung; script 13 không chấm blind, lưu mô hình `.pkl`, refit theo epoch TB fold, đoạn liên tục cắt theo trống >1h, giới hạn trên mẫu 6h, dốc trên chuỗi liên tục 9b→9c theo ngày lịch, ghi `cv_rows/*.json`, từ chối khi đã khóa; script 14 gộp rows, tiêu chí 1 thật (FA fold mean ≤3%, max ≤10%), τ chỉ trên mô hình đủ 1–2 và nửa cấu hình, cờ "cắt cụt"; script 15 tự chấm blind từ `.pkl`, từ chối nếu đã có kết quả; ED-CNN up(2,4), VAE generator riêng, DBN NaN 49 hàng đầu; script 16 đọc τ từ khóa. **Kết quả lần 1 chuyển vào `Dataclean_new/run1_provisional/` — chỉ tham khảo**
- [x] **Lần chạy 2 xong (04/09 00:05)**: 27 cấu hình; tiêu chí 1 thật loại 11 (DBN, PCA k=4/5/6, AE s0/s1, AEsmall s1, EDCNN s0/s2); τ chung = 0,135 (do PCA k=2/3 trên 9a); **PCA_k8 đứng đầu theo luật nhưng lead 65 ngày bị cắt cụt** (SPE tăng ×3 ngay 21–22/03 cuối nền); **SAE đứng đầu không cắt cụt: 06/04, 53 ngày**; blind: 0 báo giả, không mô hình nào báo đợt leo chậm (dốc 0,035–0,045 < τ). Báo cáo mục 3.5.6 đã thay bằng lần 2. Hình `hinh-so-sanh-7-mo-hinh.png`, `hinh-tang-b-PCA_k8-spe.png`
- [x] Sửa tiêu đề cột Bảng 3.11 theo yêu cầu (04/09 00:30)

## Việc tiếp theo (theo thứ tự)

1. ~~[Người dùng] Ba quyết định~~ **ĐÃ QUYẾT 04/09 11:40:** (a) tầng B vận hành = **SAE** (β = 10⁻³; `Dataclean_new/models/SAE_b0.001_s0.pkl`, lock giữ PCA_k8 theo luật cũ, quyết định nhóm ghi ở đây và báo cáo 3.5.6); (b) phase 02: lead-time cắt cụt xếp sau mô hình đo được thật; (c) thêm thang tốc độ 45 ngày. Phase 01 **KHÉP**
2. ~~Lập phase 02~~ **ĐÃ DUYỆT 12:00, ngày 1–3 XONG 13:00**: scripts/New/17 (tầng A, luật chốt: leo so chính nó + dốc có ý nghĩa + D_low<30), 18 (τ₄₅ = 0,04 lần 1 → 0,035 lần 3; tầng C chữ ký tuần), 19 (4 lần dừng thật), 20 (backtest + kiểm mù phase 02, chạy 1 lần), 21 (hình `Bao_cao/hinh-ba-tang-toan-chuoi.png`). **Sau code review (13:40, lần chạy 3, có log):** lead-time dừng 2: B14 53 ngày, B45 48 (τ₄₅ 0,035), A 30 (do 2003Y), C không; dừng 1: không tầng nào (đúng kỳ vọng); đoạn âm 0 (C: 1 tuần sau khởi động tháng 1); đợt leo 19/07 chưa tầng nào báo, C cờ đơn 30/08. Tester lần 1: 7/7; code-reviewer: 3 C + 6 H, đã sửa hết (phase-02 §6d). Báo cáo mục 3.6 và 3.7 đã thay số. Phase 3 (demo) **xong 04/09 16:40** (`Bao_cao/demo/demo-ba-tang.{html,mp4}`, tester 8/8, ba lần quay có nhật ký); phase 4 (nhúng) chưa lập
3. ~~Cập nhật artifact phase 01~~ **XONG** (04/09 11:45): mục 0 "Kết quả" + trạng thái HOÀN THÀNH. Tester chạy lại lần 2: tùy chọn, chưa làm
4. **[Chờ ngoài]** Chuyên gia trả 350 nhãn → Bảng 9 hai cột (210 mẫu trong 9c, 140 trong đoạn 11)
5. ~~Sửa lời "không bảo trì"~~ **XONG** (04/09 11:50): hai artifact ổ 2001 và 8 kênh đổi thành "dừng tháo kiểm tra, không phát hiện gì", thêm vạch 65 µm (trục Direct tới 70); PNG trong Bao_cao tạo lại; báo cáo đã sạch từ trước

## Tiêu chí đạt toàn dự án

- Tầng A: trên 9c số ngày còn lại giảm dần và < 30 trước 29/05; không báo giả ở đoạn 7, 8, 11 và 2003AX.
- Tầng B: FA trên nền ≈ 1% (đếm 6 h); tốc độ = 0 báo trên đoạn 7, 8, 9a; báo trong tháng 4/2026 trên 9c; đoạn 11 im trên bình nguyên và bắt được đợt leo 19/07.
- Bảng lead-time cho hai lần dừng, ghi rõ là lead-time trước **quyết định của nhà máy**, không phải trước hư hỏng.
