# Phase 03 — Demo phát lại ba tầng cảnh báo + quay video bằng Computer Use

**Trạng thái:** HOÀN THÀNH 04/09 16:40 (duyệt 13:10, chú thích tiếng Việt) · **Ưu tiên:** cao · **Thời lượng:** 2 ngày làm việc
**Phụ thuộc:** phase 02 đóng (lần chạy 3, `Dataclean_new/backtest_three_tiers.json`, `locked_params_phase02.json`)

## 1. Bối cảnh và quyết định đã chốt (04/09 13:00)

| Câu hỏi | Quyết định |
|---|---|
| Đối tượng xem | Giảng viên môn **"AI trong hệ thống nhúng"** → demo phải nói được: mô hình gì, bao nhiêu tham số, chạy trên dữ liệu gì mỗi ngày, và bước nhúng (phase 04) sẽ mang cái gì lên thiết bị |
| Phạm vi thời gian | **Tua liên tục toàn chuỗi** 28/09/2025 → 02/09/2026, gồm cả khoảng dừng máy (đèn xám) |
| Âm thanh | **Video câm, chú thích trên màn hình** (hộp chú thích đổi nội dung theo ngày, không TTS) |
| Tầng A ngày 29/04 do 2003Y | Trình bày là **"báo hợp lệ theo luật"**: kênh 2003Y leo 20% so với chính nó, ngoại suy chạm 65 trong 23–27 ngày |
| Hình thức | **Một file HTML tự chứa** (số liệu nhúng JSON), Dark Neumorphism, không server, không port |
| Quay video | **ffmpeg x11grab** quay màn hình thật DISPLAY :0 1920×1080; **Computer Use (desktop-x11)** mở trình duyệt và thao tác theo kịch bản; chụp ảnh xác minh mỗi bước |

Nguyên tắc nhân quả: tại ngày D, giao diện chỉ vẽ dữ liệu ≤ D và chỉ bật đèn từ các báo động đã có ở D (đúng bảng backtest lần 3, không tính lại gì).

## 2. Đầu vào (chỉ đọc, không tính lại)

| Nguồn | Dùng cho |
|---|---|
| `Dataclean_new/tier_b45_daily.parquet` (spe, slope14, slope45 theo 10 phút) → gộp trung vị ngày | đồ thị SPE, đèn B₁₄ / B₄₅ |
| `Dataclean_new/tier_a_daily.parquet` (ngày × 8 kênh: level, days_left_low, ref90, flag) | đồ thị Direct, đèn A, bảng "còn bao nhiêu ngày tới 65" |
| `Dataclean_new/tier_c_weekly.parquet` (week_end, pha/biên 8 kênh, flag, post_restart) | đèn C, la bàn pha 2001 |
| `Dataclean_new/backtest_three_tiers.json` | danh sách ngày báo chính thức từng tầng (đèn bật theo đây) |
| `Dataclean_new/feature_store_1x.parquet` (amp 8 kênh, gộp trung vị ngày) | đồ thị 8 kênh 1X |
| `Dataclean_new/restart_checks.csv` | vạch dừng thật, chú thích "tháo kiểm tra, không phát hiện gì" |
| `Dataclean_new/locked_params*.json` | hộp "thông số đã khóa" (τ₁₄ 0,135; τ₄₅ 0,035; chân trời 30; 65 µm p-p) |

Script xuất: `scripts/New/22_export_demo_data.py` → `Bao_cao/demo/demo_data.json` (≈ 340 ngày × vài chục số, < 300 KB). Kèm hash các file đầu vào ghi trong JSON để chứng minh không sửa số.

## 3. Giao diện demo (`Bao_cao/demo/demo-ba-tang.html`)

Bố cục một màn 1920×1080, không cuộn (để quay video sạch):

```
┌ Tiêu đề: P29201A · Cảnh báo sớm ba tầng · ngày đang xem D ── ba đèn A / B₁₄ / B₄₅ / C ──┐
│ [Đồ thị 1] Direct 8 kênh (µm p-p), vạch 65, vạch dừng thật, cắt tại D     │ Hộp chú thích │
│ [Đồ thị 2] log SPE SAE + dốc 14/45 ngày, ngưỡng τ, tô vùng đang báo         │ (đổi theo D) │
│ [Đồ thị 3] biên độ 1X 8 kênh · [La bàn] pha 2001X/Y theo tuần               │ Hộp mô hình:  │
│ Thanh trượt ngày 28/09/2025 → 02/09/2026 · ▶ phát · ⏸ · tốc độ ×1 ×3 ×10  │ SAE 24→..→24 │
└──────────────────────────────────────────────────────────────────────────────┘ tham số, τ, 65 │
```

- Đèn: xám = máy dừng/thiếu dữ liệu, xanh trầm = bình thường, hổ phách = cờ đơn (chưa đủ ngày liên tiếp), đỏ trầm = **báo**. Đèn A ghi kênh gây báo (vd "A · 2003Y · còn 24 ngày").
- Hộp chú thích: bảng mốc → nội dung, khớp §3.6 báo cáo. Mốc bắt buộc: 28/09 (nền chưa có, chỉ quan sát), 04/11 (dừng, chạy lại 07/11), 04/01 (dừng 1 tháo kiểm tra, không phát hiện gì), 15/01 (pha 2001 xoay 33°, C cờ sau khởi động), 20/02–22/03 (nền gốc 9b, huấn luyện), 06/04 (B₁₄ báo, 53 ngày trước dừng), 11/04 (B₄₅ báo), 29/04 (A báo, 2003Y, hợp lệ theo luật), 15/05 (B₁₄ tắt, B₄₅ giữ), 29/05 (dừng 2), 14/06 (đoạn 11 kiểm mù), 19/07 (leo chậm, chưa tầng nào báo), 30/08 (C cờ đơn, cần thêm một tuần).
- Hộp mô hình (cho giảng viên nhúng): kiến trúc SAE, số tham số, kích thước float32/int8 ước tính, số phép nhân-cộng một lần suy luận, nhịp suy luận 10 phút, RAM cần cho cửa sổ 45 ngày; ghi "phase 04 sẽ đo trên thiết bị".
- Kỹ thuật: Plotly (CDN cdnjs, pin phiên bản) hoặc SVG thuần nếu Plotly nặng khi tua ×10; thử trước, chọn cái mượt ≥ 20 khung/giây. Phím tắt: mũi tên ±1 ngày, Space phát/dừng, phím 1–9 nhảy tới mốc. Phím tắt là để Computer Use điều khiển bằng `key` thay vì click tọa độ.

## 4. Quay video

### 4.1 Công cụ
- `scripts/New/23_record_demo_screen.sh`: `ffmpeg -f x11grab -framerate 30 -video_size 1920x1080 -i :0.0 -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p Bao_cao/demo/demo-ba-tang.mp4`; nền, ghi PID để dừng bằng SIGINT.
- Computer Use theo kịch bản `scripts/New/24_demo_director_steps.md` (danh sách bước: hành động, phím, thời gian chờ, ảnh xác minh mong đợi). Tôi thực hiện từng bước qua MCP `desktop-x11`; không dùng `type_text` (IME), chỉ `key` và `paste_text`.

### 4.2 Kịch bản 5 cảnh (≈ 6 phút)

| Cảnh | Thời gian | Thao tác | Nội dung chú thích |
|---|---|---|---|
| 0 Mở | 0:00–0:20 | mở Chrome kiosk `file://…/demo-ba-tang.html`, chờ 3 s, chụp ảnh | tiêu đề, ba tầng, hộp mô hình |
| 1 Trước nền | 0:20–1:20 | phát ×10 từ 28/09/2025 → 19/02/2026, dừng tại 04/01 và 15/01 (phím mốc) | đoạn 7 giảm, dừng 1, xoay pha, C cờ sau khởi động |
| 2 Nền và tháng 4 | 1:20–3:00 | ×3 qua 9b, ×1 từ 01/04 → 30/04, dừng 06/04, 11/04, 29/04 | B₁₄, B₄₅, A bật; bảng đóng góp |
| 3 Tháng 5 → dừng 2 | 3:00–4:00 | ×1 tới 29/05 | B₁₄ tắt, B₄₅ giữ, dừng 2 tháo kiểm tra |
| 4 Kiểm mù đoạn 11 | 4:00–5:30 | ×3 tới 02/09, dừng 19/07, 30/08 | bình nguyên sạch, leo chậm chưa báo, C cờ đơn |
| 5 Kết | 5:30–6:00 | phím mốc "tổng kết" | bảng lead-time lần 3 + hộp nhúng phase 04 |

### 4.3 Nghiệm thu video
- Xem lại toàn bộ MP4 (tôi kiểm bằng ffprobe thời lượng + trích 6 khung tại mốc, đọc ảnh) : không màn hình trống, không hộp thoại lạ, không lộ cửa sổ khác.
- Ảnh chụp từng mốc lưu `Bao_cao/demo/khung/` để đưa vào báo cáo mục 3.8.

## 5. Việc theo ngày

- **Ngày 1:** script 22 xuất JSON (kiểm hash, số ngày, ngày báo khớp backtest); HTML demo; chạy thử tay, đo khung/giây khi tua ×10.
- **Ngày 2:** kịch bản 24, quay thử 1 phút (kiểm ffmpeg + Computer Use + IME), quay thật; trích khung; báo cáo mục 3.8 "Trình diễn" (≤ 1 trang, 6 ảnh); code-reviewer + tester cho script 22 (đối chiếu số trong JSON với parquet/backtest).

## 6. Tiêu chí hoàn thành
1. Mọi số hiển thị trong demo truy ngược được về parquet/JSON phase 02 (tester đối chiếu 20 mẫu ngẫu nhiên + 4 ngày báo).
2. Đèn bật đúng ngày backtest lần 3: B₁₄ 06/04, B₄₅ 11/04, A 29/04 (2003Y), C không trước 29/05; không đèn nào bật trước 04/01; đoạn 11 không đỏ.
3. MP4 ≥ 5 phút, 1080p30, xem trọn không cần cắt; 13 mốc chú thích đều xuất hiện.
4. Không tạo port, không server; file HTML chạy offline (Plotly từ CDN là ngoại lệ duy nhất, ghi rõ; nếu cần offline tuyệt đối thì nhúng thư viện).

## 7. Rủi ro
| Rủi ro | Xử lý |
|---|---|
| Computer Use bấm lệch tọa độ khi cửa sổ không kiosk | mở Chrome `--kiosk`, điều khiển bằng phím tắt, chụp xác minh trước mỗi cảnh |
| Tua ×10 giật khi Plotly vẽ lại | vẽ trước toàn chuỗi, chỉ đổi `xaxis.range` + lớp che (shape) thay vì vẽ lại dữ liệu |
| ffmpeg x11grab rớt khung | `-framerate 30 -probesize 50M`, kiểm quay thử 1 phút |
| Màn hình thật của ngài đang dùng | hẹn giờ quay, thông báo trước, không chạm cửa sổ khác |

## 8. Câu hỏi còn treo
- Trình duyệt: máy có `google-chrome` và `firefox`; dùng **google-chrome --kiosk** (đã kiểm 04/09).
- Có cần bản tiếng Anh cho chú thích không (giảng viên chỉ tiếng Việt thì không).

## 9. Nhật ký

- **Ngày 1 (04/09 13:15–13:45) XONG:** `scripts/New/22_export_demo_data.py` (xuất JSON 55 KB, tự đối chiếu ngày báo với backtest: KHỚP; dựng `Bao_cao/demo/demo-ba-tang.html` 82 KB tự chứa từ `scripts/New/demo/` gồm template, CSS neumorphism, `demo-charts-canvas.js` (canvas thuần, không CDN), `demo-replay-app.js`, `demo-annotations-vi.js` 13 mốc). Mở tại ngày bất kỳ bằng `#YYYY-MM-DD`. Ảnh chụp headless 1920×1080 tại 4 ngày: bố cục đủ một màn, không cuộn. Phát hiện khi làm: **Direct chỉ kéo tới 21/07/2026** → tầng A chưa kiểm được đợt leo 19/07 (đã sửa báo cáo 3.6 và chú thích); số trong chú thích lấy từ JSON (2001X Direct 24 → 43 µm tới 28/05; ngày 06/04 B₁₄ báo khi 2001X còn 25 µm, SPE 0,1 < 0,26).
- Tester script 22 (13:33): 8/8 đạt, `plans/reports/tester-260904-1330-phase03-demo-export.md`, không concern.
- Ngày 2 chuẩn bị xong: `23_record_demo_screen.sh` (start/stop/frames), `24_demo_director_steps.md` (16 bước, ≈ 6 phút). **Chờ ngài cho phép chiếm màn hình ≈ 7 phút** để quay.
- **Ngày 2 (04/09 15:55–16:40) XONG:** ba lần quay. Lần 1 (437 s): phát ×10 vượt mốc 14/06; phát hiện `tier_c_weekly.parquet` không có tuần đoạn 11 → script 22 bổ sung từ `backtest_three_tiers.json.C_weekly_blind` (47 tuần). Lần 2 (372 s): bảng tổng kết tự bật trong cảnh tháng 5 (không tái hiện được bằng từng phím; nghi phím lạc) → đổi phím sang **F9/Esc**. Lần 3 (368 s): đạt; cửa sổ VS Code lộ 0:55–1:00 (mất tiêu điểm 5 s, 3/5 phím → bị nuốt) → cắt 5,5 s bằng ffmpeg select → **`Bao_cao/demo/demo-ba-tang.mp4` 362 s, 1080p30, 10 MB**. Khung: `Bao_cao/demo/khung/01…08`. Báo cáo mục 3.8. Đã tắt banner GNOME khi quay và bật lại; Chrome kiosk profile riêng trong scratchpad, thẻ `notranslate`.
- Tiêu chí §6: (1) tester 8/8; (2) đèn đúng ngày (ảnh xác minh 06/04, 11/04, 29/04, 29/05, 02/09); (3) video 6:02 ≥ 5 phút, 13 mốc; (4) không port, không server, không CDN.
