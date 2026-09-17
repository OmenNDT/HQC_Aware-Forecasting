# Code review — pha 01 P29202A tầng A/C (10/09/2026)

## Phạm vi
- Mới: `scripts/New/34_ingest_p29202a.py` (87 dòng), `scripts/New/35_tier_a_c_p29202a.py` (123 dòng)
- Sửa: `17_tier_a_direct_projection.py` (`daily_direct`, `project` nhận tham số), `18_tier_b_slow_scale_and_tier_c.py` (`weekly_signature`, `true_restarts` nhận tham số)
- Cách kiểm: đọc mã + chạy lại các hàm trong bộ nhớ (không ghi tệp), pandas 2.1.4, bắt mọi warning.

## Đã xác minh (không phải lỗi)
- Tệp Direct: dòng dữ liệu ĐẦU TIÊN là ô datetime, các dòng sau là số ngày Excel → đường parse kép ở 34:32-33 là bắt buộc và đúng; 61.057 dòng, bước 10 phút đều, không trùng, hai tệp cùng lưới.
- Cột lọc đúng: 4 kênh bơm Direct/1X Amp/Phase; 2052A/2053A "Configure" → NaN 100 % và không dùng.
- Không có dòng nào có đúng 3 kênh Direct hợp lệ (99 dòng toàn NaN = "Not Connect" → "chưa biết", không phải "dừng"); pha 0,0° chỉ xuất hiện ở dòng máy dừng, sau cổng chạy = 0 dòng lọt vào kho.
- Hồi quy A: `daily_direct()`/`project()` mặc định == `Dataclean_new/tier_a_daily.parquet` (1.848 dòng, `DataFrame.equals` True); `weekly_signature`/`true_restarts` mặc định == `tier_c_weekly.parquet` (35 tuần) và `restarts_true` trong lock2. Thứ tự tham số vị trí khớp mọi caller (20, 21, 27).
- Kết quả lưu trong `Dataclean_new/p29202a/` tái lập đúng khi chạy lại hàm.
- Cổng `min_ch=3` cho cả "known" lẫn "running" là tương đương đúng của 6/8: cùng 75 %, và `stopped = known & ~running` giữ nguyên ngữ nghĩa. Lưu ý duy nhất: với 4 kênh, nếu 1 kênh Direct chết vĩnh viễn thì mọi giờ phụ thuộc cả 3 kênh còn lại > 3 µm (A chịu được 2 kênh thấp). Hiện Direct NaN 0,2 % nên không sao.

## Phát hiện (theo mức)

### Trung bình
1. **34:78 — `assert dd.index.equals(dx.index)` quá cứng.** Hai tệp xuất PI thường lệch nhau 1 dòng cuối (23:50 vs 00:00) hoặc thiếu vài dòng; khi đó toàn bộ ingest chết dù Direct đã đủ làm cổng. Sửa: `dx = dx.reindex(dd.index)` (Direct là chủ lưới), cảnh báo nếu số dòng lệch > 0,1 %. `assert` cũng bị bỏ khi chạy `python -O` → dùng `raise ValueError`.
2. **34:25,31 — hàng tiêu đề cứng `HEADER_ROW=11`, không kiểm.** Nếu mẫu xuất thêm/bớt một dòng đầu, `keep` rỗng và lỗi nổ ở 34:41 dạng `KeyError: '29VT-2017AX Direct (um)'` khó hiểu. Sửa: sau khi đọc, `if hdr[0] != "Thoi diem": raise ValueError(...)` và kiểm đủ 4 cột mong đợi ngay trong `read_datalink`.
3. **35:66-86 — `restart_checks` chép lại logic script 19** thay vì gọi lại như pha 01 ghi ("gọi lại hàm của script 17/18/19"). Hai bản đã lệch: 19 có guard `fs.index.min() >= t_stop - 14d`, 35 dựa vào `len(before) < 200`. Thêm nữa `19:47` vẫn cứng `< 6` — bản sao thứ ba của cổng chạy bên cạnh `true_restarts(min_run_ch)`. Đề nghị: tách `restart_windows(fs, restarts)` + `summarize(g, ch)` trong 19 nhận `ch`, rồi 35 gọi; hoặc ghi rõ trong docstring 35 là cố ý chép để 19 giữ nguyên.
4. **35:118 — `summary.json["locked_from"] = "locked_params.json"` sai nguồn.** Ngưỡng A lấy từ `phase01_config.py`, luật C từ `locked_params_phase02.json` (35:54); `locked_params.json` (LOCK_FILE) là khóa chọn mô hình pha 01, không dùng ở đây. Sửa: `"locked_from": ["phase01_config.py", "locked_params_phase02.json"]` (+ `inputs_sha256` của lock2 nếu muốn truy vết).

### Thấp
5. **35:56,69 — ngưỡng kênh hợp lệ `> 0.5` sát biên**: 2019Y = 0,567. Thêm vài tuần Bad là 2019Y rớt khỏi bảng tuần/khởi động → cột đầu ra đổi giữa hai lần chạy. Không ảnh hưởng cờ (chỉ `sig` quyết định). Sửa: đặt hằng `MIN_VALID_FRAC`, in danh sách kênh vào summary (đã có `good` nhưng chưa ghi), và `assert SIG in good` để lỗi rõ thay vì KeyError trong 18:58.
6. **Tương thích pandas ≥ 2.2**: 35:48 `groupby("ch").apply(lambda …)` → DeprecationWarning (cột nhóm bị gộp; pandas 3 đổi hành vi — lambda không dùng `ch` nên kết quả không đổi, nhưng đổi sang `groupby("ch")[["level","ref90_median"]].apply` hoặc tính vector `(df.level > 1.1*df.ref90_median).groupby(df.ch).sum()`); 18:74 `flip.shift(1).fillna(False)` → FutureWarning downcast (có sẵn, không thuộc diff; sửa `flip & flip.shift(1, fill_value=False)`); 35:54,119 `json.load(open(…))`/`json.dump(…, open(…,"w"))` → ResourceWarning, dùng `with`.
7. **35:115 — `float(days_left_low.min())` có thể là `inf`** khi mọi cửa sổ của kênh có dốc ≤ 0 → `json.dump` ghi `Infinity` (JSON không chuẩn; trang demo JS/`jq` từ chối). Sửa: `None if np.isinf(v) else float(v)`.
8. **Đường dẫn hình lệch kế hoạch**: pha 01 ghi `Bao_cao/hinh/p29202a-tang-a-c.png`; script ghi `Bao_cao/p29202a-tang-a-c.png`; quy ước hiện có là `Bao_cao/hinh-*.png`. Chọn một và cập nhật plan/biên bản.
9. **35:114 `summary["period"]`** là kỳ có dòng tầng A (từ 20/07) chứ không phải kỳ dữ liệu (13/07) — đổi tên `tier_a_row_period` hoặc lấy từ `w_a`. Bước 1 của pha 01 yêu cầu đối chiếu "395 ngày" với khảo sát (390) — biên bản nêu 383/349 nhưng chưa giải thích chênh lệch (12 ngày bỏ sau khởi động + ngày thiếu dữ liệu).
10. **18:55 `g[amp_2019Y].median()` trên tuần toàn NaN** → `RuntimeWarning: Mean of empty slice` (vô hại, trả NaN). Không cần sửa; nếu muốn sạch log: `g[col].median() if g[col].notna().any() else np.nan`.
11. **Ghi chú tài liệu (không sửa mã)**: (a) `daily_direct` lấy mẫu "gần nhất trên lưới 1 giờ" → với Direct 10 phút, trung vị ngày chỉ dùng mẫu đúng giờ (1/6 dữ liệu). Đúng luật A, không đổi, nhưng nên ghi vào docstring 34/35 để pha 02 (firmware) tái lập cùng cách. (b) Lần dừng 15,5 h 25–26/09/2025 là khoảng trống > 12 h nhưng trung vị ngày không "dừng" → C không coi là khởi động (không có cờ 21 ngày), A thì cắt đoạn + bỏ 2 ngày. Đúng định nghĩa của từng tầng như trên A; ghi vào biên bản.

## Điểm tốt
- Parse thời gian kép (số ngày Excel / datetime) xử lý đúng tệp thật lẫn lộn ngay từ dòng 1.
- `ffill` cắt theo đoạn liên tục (34:61-62) chặt hơn script 12 (không tràn qua lúc dừng).
- Tham số hóa 17/18 tối thiểu, mặc định giữ nguyên byte-identical; docstring ghi ngày quyết định.
- Cổng chạy bằng Direct cho kho 1X (thay vì 1X amp như A) được nêu rõ lý do trong docstring 34.
- Mọi tệp < 200 dòng; bình luận tiếng Việt cùng giọng với script 12/17/18.

## Hành động đề nghị (theo thứ tự)
1. 34: reindex 1X theo lưới Direct + kiểm tiêu đề, thay `assert` bằng `raise` (mục 1, 2).
2. 35: sửa `locked_from`, `inf` → `None`, `assert SIG in good`, `with open` (mục 4, 5, 7, 6).
3. Chọn đường dẫn hình, bổ sung đối chiếu 383/390 vào biên bản (mục 8, 9).
4. Cân nhắc gom `restart_checks` về script 19 trước pha 02 nếu firmware cần cùng cửa sổ (mục 3).

## Câu hỏi chưa giải
1. Ngưỡng 3 µm cho cổng chạy đã kiểm với mức dừng thực của P29202A chưa? Direct lúc dừng ≈ 0,8–1,5 µm nên hiện an toàn, chỉ cần xác nhận.
2. Có muốn 2019Y nằm trong bảng tuần/khởi động không (nửa đầu kỳ Bad)? Nếu không, loại tường minh thay vì dựa vào ngưỡng 0,5.

**Status:** DONE_WITH_CONCERNS
**Summary:** Ingest và luật A/C áp lên P29202A đúng, không trôi ngưỡng, mặc định 17/18 tái lập A byte-identical. Còn 4 điểm trung bình (assert lưới cứng, tiêu đề không kiểm, chép logic script 19, nguồn khóa ghi sai trong summary.json) và vài điểm thấp về tương thích pandas/JSON; không có lỗi chặn.
