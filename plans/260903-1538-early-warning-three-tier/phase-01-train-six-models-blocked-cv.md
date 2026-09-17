# Phase 01 — Kế hoạch train: 6 mô hình paper + PCA, nền 9b, kiểm định chéo 5 khối ba vai

**Ngày lập:** 03/09/2026 · **Cập nhật:** 03/09/2026 20:55 · **Trạng thái:** **đã duyệt, đang làm ngày 1** · **Phụ thuộc:** plan.md

## 1. Mục tiêu

Train và so sánh **7 mô hình tái tạo** (8 cấu hình) trên cùng nền gốc, cùng 24 đặc trưng, cùng giao thức: PCA, AE hai cỡ, SAE, VAE, DBN, ED-LSTM, ED-CNN. Đầu ra: mô hình cho **tầng B** (trạng thái SPE + báo động theo tốc độ) và bảng so sánh theo tiêu chí hai vế của paper: *tái tạo tốt nền* **và** *residual tăng khi hệ lệch*. Tầng A, C sang phase 02.

## 2. Dữ liệu và tập chia (chốt)

Mọi file 10 phút, cùng tham chiếu pha từ 15/01/2026; đoạn 7, 8 cộng +148° vào pha 2005/2007. Mẫu độc lập ≈ 4/ngày (tự tương quan 6 h).

| Tập | Dữ liệu | Dòng · độc lập | Vai trò | Được dùng để | Cấm |
|---|---|---|---|---|---|
| Train | 9b, 3/5 khối | ≈2.250 · ≈60 | fit | trọng số, chuẩn hóa | — |
| Val | 9b, 1 khối đứng trước khối test | ≈750 · ≈21 | dừng sớm | số epoch, tốc độ học, đường cong k của PCA | giới hạn, dung lượng |
| Test trong nền | 9b, 1 khối, xoay 5 fold phủ hết 20/02–22/03 | ≈750 · ≈21 | SPE ngoài mẫu | giới hạn 99% (mẫu 6 h), mốc thang điểm | dừng sớm |
| Cấu hình dương | 9c 23/03–29/05 (`…Doan9c_23.03.26-13.06.26.parquet`, khớp `51_Vib180d` Δ = 0) | ≈9.600 · ≈270 | đợt leo tới dừng 2 | chọn dung lượng (tỉ số tách), ngưỡng tốc độ, lead-time | trọng số |
| Cấu hình âm | đoạn 8 cửa sổ 02/12–01/01; đoạn 7; 9a 15/01–05/02 | 4.464 + 5.329 + 3.025 · ≈180 | không được báo | ngưỡng tốc độ | trọng số |
| Chỉ báo cáo | 05/02–19/02 (leo vào nền, chỉ 1 giờ ở `51_Vib180d`); 9c 02–10/06 (quá độ sau dừng 2, pha 2001 ở 63° rồi nhảy về 92°) | | mô tả | hình, nhận xét | chọn bất kỳ tham số nào |
| Kiểm mù | đoạn 11 14/06–02/09 (`…Doan11_14.06.26-2.09.26.parquet`) | 11.521 · ≈320 | chạy một lần | báo cáo | mọi việc trên |
| Nghiệm thu mẫu | `Data/HQC_eval_expert.csv` 350 mẫu | 350 | accuracy kiểu Bảng 9 | chấm, **tách hai cột**: 210 mẫu trong 9c (bộ cấu hình) và 140 trong đoạn 11 (mù) | chọn |

Khoảng trống 1 ngày ở mọi ranh giới khối và ở ranh giới 9b–9c. Khuyết (2007X: 8% ở 9a, 29% ở đoạn 8; các kênh lúc máy dừng ở 9c): điền tiến ≤ 6 dòng, dài hơn bỏ dòng.

## 3. Quy trình chung (không mô hình nào được lệch)

1. Nạp bằng `scripts/11_profile_1x_episode_pull.py::load_pull`; cổng máy chạy ≥ 6/8 kênh > 3 µm.
2. Sửa tham chiếu pha đoạn 7, 8: pha 2005X/Y, 2007X/Y += 148° (mod 360); cờ `phase_ref_corrected`. Hằng số 148° ước lượng từ đoạn 8 và 9b, là hằng tiền xử lý, ghi README.
3. Đặc trưng 24 chiều: 8 Amp, 8 sin(pha), 8 cos(pha); thứ tự `2001X,2001Y,2003X,2003Y,2005X,2005Y,2007X,2007Y`. Một mẫu = một hình dạng của hệ tại một thời điểm; đích tái tạo = chính nó; không tải, không thời gian, không Direct.
4. Chuẩn hóa fit trên train của từng fold: PCA z-score; mạng nơ-ron min-max [−1, 1] theo p1–p99 train, sin/cos giữ nguyên.
5. Residual: SPE = Σ(x − x̂)²; giữ MAE để đối chiếu paper. Đóng góp kênh j = (r²amp + r²sin + r²cos)_j / SPE, in đủ 8 kênh.
6. Cửa sổ nhân quả 20 bước cho LSTM, CNN; trượt từng dòng khi train; không vắt qua ranh giới khối. Đếm dung lượng theo ≈120 mẫu độc lập, không theo 4.302 cửa sổ.
7. 3 hạt giống cho mô hình ngẫu nhiên; báo trung bình ± độ lệch.

## 4. Bảy mô hình — kiến trúc quy đổi từ paper (14 → 24 đầu vào)

| Mô hình | Kiến trúc | Tối ưu | Tham số (ước) | Ghi chú paper |
|---|---|---|---|---|
| PCA | k ∈ {2,3,4,5,6,8} | — | 24k + 72 | đường cơ sở |
| AE | 24-28-12-6-12-28-24, tanh | RMSProp 1e-4 | ≈ 2.100 | 14-17-8-4-8-17-14, lớp đầu rộng hơn đầu vào |
| AE nhỏ | 24-12-6-12-24 | RMSProp 1e-4 | ≈ 600 | so với ngân sách ≈120 mẫu |
| SAE | 24-24-24-24-24-24, phạt L1 kích hoạt β ∈ {1e-4, 1e-3, 1e-2} | RMSProp 1e-4 | ≈ 3.000 | mọi lớp = 14 |
| VAE | 24-28-14 → z=8 → 14-28-24; MSE + KL | mini-batch SGD 1e-3 | ≈ 2.300 | 16,8,6,8,16; chấm bằng trung bình 16 lần lấy mẫu |
| DBN | 3 RBM: 24→28→22→18, CD-k k=10, batch 25 | lr 3e-3 | ≈ 1.700 | 16,13,11; residual lọc trung bình trượt 50 |
| ED-LSTM | cửa sổ 20×24 → LSTM 16-10-16 → 24, tanh | SGD 1e-3, batch 100 | ≈ 4.000 | 10,7,10 |
| ED-CNN | ảnh 24×20 → Conv16 8×8 → pool → Conv8 3×3 → pool → Conv8 → up(2,1) → Conv16 → up → Conv1 8×8 tanh | Adam 1e-3 | ≈ 4.000 | Bảng 7, padding same |

Epoch tối đa 300, dừng sớm kiên nhẫn 20 trên khối val. PyTorch, CPU đủ; GPU RTX 3090 chỉ để lặp seed.

## 5. Giao thức kiểm định chéo: 5 khối ba vai trong 9b

```
9b (31 ngày) = |K1|gap|K2|gap|K3|gap|K4|gap|K5|   mỗi khối ~5,2 ngày sau khi trừ 1 ngày trống
fold i:  test  = Ki             → SPE ngoài mẫu (giới hạn, mốc thang điểm)
         val   = K(i−1)         → dừng sớm, tốc độ học (xoay vòng, K0 = K5)
         train = 3 khối còn lại → trọng số + chuẩn hóa (~15 ngày, ~60 mẫu độc lập)
5 fold → SPE ngoài mẫu phủ toàn bộ 9b; không khối nào vừa val vừa test trong cùng fold
```

- Val chỉ quyết **khi nào dừng** cho một kiến trúc; **kiến trúc nào** do bộ cấu hình quyết (tránh bẫy "sao chép").
- Tiêu chí val: AE/SAE/LSTM/CNN = MSE; VAE = ELBO; DBN = sai số tái tạo một lượt xuống, từng RBM; PCA = đường cong theo k.
- Giới hạn kiểm soát 99% trên SPE ngoài mẫu lấy mẫu 6 h (≈120 điểm); báo cáo FA ở cả 6 h và 10 phút.
- Luật báo: vượt giới hạn liên tục ≥ 6 h.
- Mô hình cuối fit lại trên toàn bộ 9b, epoch = trung bình fold; giới hạn giữ từ CV. **Thiên lệch đã biết:** mô hình cuối thấy 31 ngày nên SPE nền hơi thấp hơn → FA thật hơi < 1%, giới hạn hơi rộng; chấp nhận, ghi báo cáo, không hạ tay.
- Fold có test trước train về thời gian: hợp lệ vì nền coi là dừng. **Chờ người dùng:** giữ đủ 5 fold hay chỉ fold xuôi chiều (mất phủ hai khối đầu).

## 6. Tiêu chí chọn mô hình (khóa trước khi chạy, đúng thứ tự)

1. FA trên 9b ngoài mẫu ≤ 1,5% (đếm 6 h).
2. Tỉ số tách = median SPE(9c 16–29/05) / median SPE(9b ngoài mẫu) ≥ 1,3; dưới là mô hình sao chép, loại.
3. Số lần báo theo tốc độ trên đoạn 7, 8, 9a = 0.
4. Ngày báo đầu tiên trên 9c so với 29/05 (lead-time), chỉ xét sau khi qua 1–3.
5. Hòa → ít tham số hơn thắng.

**Báo động theo tốc độ:** độ dốc log SPE (trung vị ngày) trên 14 ngày; một ngưỡng chung cho mọi mô hình, chỉnh một lần trên bộ cấu hình. Ngưỡng này chỉnh trên **một** sự kiện dương (9c); đợt leo 19/07 trong đoạn 11 là lần kiểm đầu tiên. **Tùy chọn chờ người dùng:** tách 9c làm hai nửa (chỉnh 23/03–30/04, kiểm trước 01–29/05) để chắc hơn, đổi lại lead-time đo được ngắn hơn.

**Mốc thang điểm 0–100:** median và p99 SPE ngoài mẫu 9b + p99 của 9c. Không dùng max toàn chuỗi (đang rò ở `model_pca_k6.json`).

## 7. Sản phẩm

| File | Nội dung | Dòng |
|---|---|---|
| `scripts/12_build_feature_store.py` | nạp 6 file 10 phút (+ `51_Vib180d` chỉ cho 05/02–19/02), sửa pha 148°, cổng, khuyết, 24 đặc trưng → `Dataclean/feature_store_1x.parquet` (cột `episode`, `role`, `phase_ref_corrected`) | ≤ 150 |
| `scripts/models/reconstruction_base.py` | fit / score / contribution, scaler theo fold | ≤ 120 |
| `scripts/models/pca_model.py`, `ae_sae_vae_models.py`, `dbn_rbm_model.py`, `ed_lstm_model.py`, `ed_cnn_model.py` | mỗi mô hình một file | ≤ 200 |
| `scripts/13_blocked_cv_train_compare.py` | 5 khối × mô hình × seed; `Dataclean/cv_results.csv`, SPE ngoài mẫu | ≤ 180 |
| `scripts/14_configure_rate_alarm_and_score.py` | ngưỡng tốc độ + mốc thang điểm trên bộ cấu hình; lead-time 9c; kiểm âm; ghi `Dataclean/locked_params.json` kèm hash | ≤ 150 |
| `scripts/15_blind_test_episode11.py` | chạy một lần; từ chối chạy nếu chưa có hash khóa | ≤ 100 |
| `scripts/16_figures_model_comparison.py` | SPE ngoài mẫu theo mô hình, tỉ số tách, lead-time, bảng kiểu Bảng 9 hai cột | ≤ 150 |

## 8. Lịch

| Ngày | Việc | Kết quả kiểm được |
|---|---|---|
| 1 | Feature store; PCA qua CV; ngưỡng tốc độ v0 | `feature_store_1x.parquet`; dòng PCA trong `cv_results.csv`; FA 9b ≈ 1% |
| 2 | AE, AE nhỏ, SAE, VAE | 4 dòng × 3 seed |
| 3 | DBN (tự viết RBM), ED-LSTM, ED-CNN | 3 dòng; kiểm cửa sổ nhân quả |
| 4 | Chỉnh tốc độ, mốc điểm; kiểm âm; lead-time 9c; **khóa** | bảng chọn theo mục 6 |
| 5 | Kiểm mù đoạn 11 một lần; hình; tester + code-reviewer; cập nhật plan | báo cáo phase |

## 9. Danh sách kiểm rò rỉ (chạy trước khi khóa)

- Không dòng val/test nào trong train cùng fold, kể cả qua cửa sổ.
- Chuẩn hóa fit trên train fold; mốc thang điểm chỉ từ 9b ngoài mẫu và 9c.
- 350 mẫu chuyên gia không tham gia chọn k, kiến trúc, ngưỡng.
- Đoạn 11 chưa từng được đọc bởi script 13, 14.
- Hằng 148° ghi README, không học.

## 10. Rủi ro

| Rủi ro | Xử lý |
|---|---|
| Deep model quá khớp với ≈60 mẫu độc lập mỗi fold | đó là kết quả; báo đường cong train–val, không thu hẹp khối kiểm định |
| DBN không có thư viện chuẩn | RBM Gauss-nhị phân ~120 dòng; kiểm trên dữ liệu tổng hợp trước |
| Ngưỡng tốc độ chỉnh trên một sự kiện | ghi rõ; tùy chọn tách 9c hai nửa; đoạn 11 là kiểm đầu tiên |
| Giới hạn từ CV hơi rộng so với mô hình cuối | ghi chiều thiên lệch, không sửa tay |
| Chọn mô hình "nhìn trộm" đoạn 11 | script 15 yêu cầu hash khóa |
| Pha 2001Y quanh 0°/360° | sin/cos; thống kê báo cáo dùng công thức vòng tròn |
| Ổ 2005/2007 xoay tham chiếu sau lần dừng kế tiếp | kiểm tra sau khởi động ở phase 02; README cảnh báo |

## 11. Tiêu chí hoàn thành phase

- [x] `cv_results.csv` đủ 27 cấu hình (8 họ × hạt giống): tham số, FA 9b (6 h và 10 phút), FA fold mean/max, tỉ số tách, dốc max đoạn âm, dốc max 9c — lần chạy 2, 04/09 00:05.
- [x] Mô hình chọn theo luật đã khóa: PCA_k8 (lead cắt cụt); đứng đầu không cắt cụt: SAE_b0.001_s0. `locked_params.json` có hash, τ = 0,135.
- [x] Kiểm mù đoạn 11 chạy một lần: 0 ngày báo trên bình nguyên (16/16 cấu hình đạt), không cấu hình nào báo đợt leo từ 19/07 (dốc 0,035–0,045 < τ).
- [x] Tester lần 1 đạt 7/7; code-reviewer DONE_WITH_CONCERNS → đã sửa toàn bộ C1–C3, H1–H7 và chạy lại. Tester lần 2: tùy chọn.
- [x] Hình so sánh 7 họ, hình SPE mô hình chọn. [ ] Bảng kiểu Bảng 9 hai cột: chờ 350 nhãn chuyên gia.

## Quyết định người dùng (03/09/2026 20:55) — phase 01 ĐÃ DUYỆT

1. **Giữ đủ 5 fold**, kể cả fold có test đứng trước train.
2. **Tách 9c làm hai nửa:** chỉnh dung lượng và ngưỡng tốc độ trên **23/03–30/04** (+ ba đoạn âm); **kiểm trước** trên **01–29/05** không sửa gì. Lead-time báo cáo là ngày báo đầu tiên trên toàn 9c, ghi rõ nửa đầu đã dùng để chỉnh. Tỉ số tách ở mục 6.2 đổi thành median SPE(16–30/04) / median SPE(9b ngoài mẫu).
3. **Một ngưỡng tốc độ chung** cho mọi mô hình.
4. **Tầng C báo mức thấp** (phase 02): luật "chiều quay pha 2001 đổi dấu và giữ ≥ 14 ngày, sd pha tuần < 5°" → cảnh báo hạng "cần xem", kèm câu giải thích hình dạng 8 kênh.

## Câu hỏi còn mở

- Chuyên gia trả 350 nhãn khi nào?
