#!/usr/bin/env python3
"""17_tier_a_direct_projection.py — Tầng A: ngoại suy Direct (peak-to-peak) tới ngưỡng nhà máy 65 µm.

Luật chốt (phase 02, quyết định 04/09 12:30): báo khi (1) kênh LEO SO VỚI CHÍNH NÓ: mức > 1,10 × trung vị 90 ngày
trước đó (không tính ngày hiện tại); (2) dốc 14 ngày chạy có ý nghĩa (t > 1,645); (3) cận dưới số ngày còn lại tới
65 µm < 30; giữ ≥ 2 ngày liên tiếp.
Sửa theo code review 04/09 13:10: cổng máy chạy áp ở MỨC DÒNG trước khi lấy trung vị ngày (loại nửa ngày dừng);
cửa sổ hồi quy không vắt qua lần dừng (chỉ lấy ngày trong cùng đoạn chạy); bỏ 2 ngày đầu chỉ sau lần dừng THẬT
(có dòng thô không chạy trong khoảng trống), không bỏ sau khoảng trống chỉ do thiếu dữ liệu.

Ra: Dataclean_new/tier_a_daily.parquet (ngày × kênh) + bảng backtest.
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from alarm_utils import alarm_days, first_before                           # noqa: E402

CH = ["2001AX", "2001AY", "2003AX", "2003AY", "2005X", "2005Y", "2007X", "2007Y"]
NEG_EP7 = (pd.Timestamp("2025-09-28"), pd.Timestamp("2025-11-04"))


RUN_UM, RUN_MIN_CH = 3.0, 6                                              # cổng máy chạy: ≥ 6/8 kênh > 3 µm (75 % số kênh)


def daily_direct(direct_long=DIRECT_LONG, ch=CH, min_ch=RUN_MIN_CH):
    """Trung vị ngày của các DÒNG máy chạy; trả (bảng ngày, nhãn đoạn chạy, ngày bị bỏ sau khởi động).
    Tham số hóa 10/09/2026 để chạy máy khác (P29202A: 4 kênh, min_ch = 3); mặc định giữ nguyên hành vi P29201A."""
    c5 = pd.read_parquet(direct_long)
    d = c5[c5.sensor.isin([f"29VT-{c}" for c in ch])].copy()
    # 8 kênh quét lệch nhau (~8 h/kênh): đưa về lưới 1 giờ bằng giá trị gần nhất trong ±4 h, rồi gate theo GIỜ
    grid = pd.date_range(d.ts.min().floor("1D"), d.ts.max().ceil("1D"), freq="1h"); cols = {}
    for c in ch:
        s = d[d.sensor == f"29VT-{c}"].set_index("ts").val.sort_index()
        s = s.groupby(level=0).median()                                  # 29VT-2007Y có khối trùng trong file gốc
        cols[c] = s.reindex(grid, method="nearest", tolerance=pd.Timedelta(hours=4))
    wide = pd.DataFrame(cols, index=grid)
    known = wide.notna().sum(axis=1) >= min_ch                            # giờ có đủ thông tin để phán xét
    running_h = known & ((wide[ch] > RUN_UM).sum(axis=1) >= min_ch)
    stopped_h = known & ~running_h
    stopped_days = set(stopped_h[stopped_h].index.floor("1D"))           # ngày có ít nhất một giờ máy DỪNG thật
    w = wide[running_h].resample("1D").median().dropna(how="any")        # trung vị ngày chỉ trên giờ máy chạy
    # đoạn chạy: cắt khi có ngày dừng THẬT giữa hai ngày chạy liên tiếp của bảng
    seg = np.zeros(len(w), int); skip = np.zeros(len(w), bool); s = 0
    for i in range(1, len(w)):
        between = pd.date_range(w.index[i - 1] + pd.Timedelta(days=1), w.index[i] - pd.Timedelta(days=1))
        if any(dd in stopped_days for dd in between) or (w.index[i] in stopped_days):
            s += 1; skip[i:i + TIERA_STARTUP_SKIP] = True
        seg[i] = s
    w["seg"] = seg
    return w[~skip], w.index[skip]


def project(w, ch=CH):
    rows = []
    for i in range(len(w)):
        t = w.index[i]
        same = w.iloc[max(0, i - TIERA_WINDOW_RUN_DAYS + 1): i + 1]
        win = same[same.seg == w.seg.iloc[i]]                                # không vắt qua lần dừng
        if len(win) < 8:
            continue
        x = (win.index - win.index[0]).days.values.astype(float)
        ref = w.loc[t - pd.Timedelta(days=TIERA_REF_DAYS): t - pd.Timedelta(days=1)]   # 90 ngày TRƯỚC, không gồm t
        for c in ch:
            y = win[c].values; b, a = np.polyfit(x, y, 1)
            resid = y - (a + b * x); se = np.sqrt(np.sum(resid ** 2) / max(len(x) - 2, 1) / np.sum((x - x.mean()) ** 2))
            level = a + b * x[-1]; t_stat = b / se if se > 0 else np.inf
            dl = (PLANT_LIMIT_UM - level) / b if b > 0 else np.inf
            b_hi = b + TIERA_Z90 * se; dl_low = (PLANT_LIMIT_UM - level) / b_hi if b_hi > 0 else np.inf
            ref_med = ref[c].median() if len(ref) >= TIERA_REF_MIN_OBS else np.nan
            rising = (not np.isnan(ref_med)) and level > (1 + TIERA_RISE_MIN) * ref_med
            rows.append({"day": t, "ch": c, "level": level, "slope_um_day": b, "slope_se": se, "t_stat": t_stat,
                         "days_left": dl, "days_left_low": dl_low, "ref90_median": ref_med, "n_win": len(win),
                         "flag_spec": dl_low < TIERA_HORIZON_DAYS,
                         "flag_sig": (t_stat > TIERA_Z90) and (dl_low < TIERA_HORIZON_DAYS),
                         "flag": rising and (t_stat > TIERA_Z90) and (dl_low < TIERA_HORIZON_DAYS)})
    return pd.DataFrame(rows)


def alarms(df, col="flag"):
    day = df.groupby("day")[col].any().astype(int)
    return alarm_days(day, 0.5, TIERA_CONSEC)


def main():
    w, skipped = daily_direct(); df = project(w)
    os.makedirs(DATA_NEW, exist_ok=True); df.to_parquet(f"{DATA_NEW}/tier_a_daily.parquet")
    pd.set_option("display.width", 220)
    print(f"Ngày chạy dùng: {len(w)} | đoạn chạy: {w.seg.nunique()} | ngày bỏ sau khởi động thật: {len(skipped)}")
    for col, label in [("flag_spec", "luật đặc tả: D_low<30"), ("flag_sig", "+ dốc có ý nghĩa"), ("flag", "+ leo so với chính nó — LUẬT CHỐT")]:
        al = alarms(df, col); ep7 = [a for a in al if NEG_EP7[0] <= a <= NEG_EP7[1]]; byc = df[df[col]].groupby("ch").size().to_dict()
        print(f"  [{label}] ngày báo {len(al)} | đoạn 7: {len(ep7)} | 2003AX cờ: {byc.get('2003AX', 0)} | kênh: {byc}")
    al = alarms(df)
    for name, stop in EVENTS.items():
        f, lt = first_before(al, stop)
        print(f"Sự kiện {name} ({stop.date()}): {'báo đầu ' + str(f.date()) + f' → lead-time {lt} ngày' if f else 'không báo'}")
    key = df[(df.ch == "2001AX") & df.day.isin(pd.to_datetime(["2026-04-15", "2026-05-15", "2026-05-22", "2026-05-28"]))]
    print("\n2001AX tại các mốc:\n" + key[["day", "level", "ref90_median", "slope_um_day", "days_left", "days_left_low", "n_win", "flag"]].round(2).to_string(index=False))
    a11 = [a for a in al if a >= pd.Timestamp("2026-06-14")]
    print("Đoạn 11 (14/06→): ngày báo =", [a.strftime("%d/%m") for a in a11])


if __name__ == "__main__":
    main()
