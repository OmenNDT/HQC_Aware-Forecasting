#!/usr/bin/env python3
"""11_profile_1x_episode_pull.py — Hồ sơ một lần kéo 1X Amp/Phase (8 kênh) từ PI DataLink.

Dùng cho các file dạng `Dataraw/28.9.25-4.11.25.xlsx`, `Dataraw/Doan8_7.11.25-4.01.26.xlsx`:
sheet đầu, hàng tiêu đề bắt đầu bằng "Thoi diem", 16 cột (8 Amp + 8 Phase), timestamp có thể
là số serial Excel.

In ra: khoảng, bước, khuyết, cổng máy chạy, trung vị/độ dốc từng kênh so với nền 9b, pha
vòng tròn, bảng tuần, quét cửa sổ 30 ngày phẳng nhất (ứng viên nền gốc), nhiễu trong ngày.
Lưu: Dataclean/P29201A_1X_<tên>.parquet (10 phút, 16 cột).

Chạy: python scripts/11_profile_1x_episode_pull.py "Dataraw/Doan8_7.11.25-4.01.26.xlsx"
"""
import sys
from datetime import datetime
import numpy as np
import pandas as pd
import openpyxl
from scipy import stats

ROOT = "/home/sontn/Projects/HQC_Aware-Forecasting"
CH = ["2001X", "2001Y", "2003X", "2003Y", "2005X", "2005Y", "2007X", "2007Y"]
RUN_UM, RUN_MIN_CH = 3.0, 6          # cổng máy chạy: ≥6/8 kênh có 1X Amp > 3 µm
WIN_DAYS, STEP_DAYS = 30, 5          # quét cửa sổ nền


def load_pull(path):
    """Đọc sheet đầu → DataFrame index thời gian, cột <kênh>_amp / <kênh>_ph."""
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0]
    rows, hdr = [], None
    for r in ws.iter_rows(values_only=True):
        if hdr is None and r[0] == "Thoi diem":
            hdr = [str(c) for c in r[:17]]
            continue
        if hdr:
            rows.append(r[:17])
    df = pd.DataFrame(rows, columns=hdr)
    ts = [x if isinstance(x, datetime)
          else (pd.to_datetime(float(x), unit="D", origin="1899-12-30") if x is not None else pd.NaT)
          for x in df["Thoi diem"]]
    df.index = pd.DatetimeIndex(ts).round("min")
    df = df.drop(columns=["Thoi diem"]).apply(pd.to_numeric, errors="coerce")
    df.columns = [c.split(" ")[0] + ("_amp" if "Amp" in c else "_ph") for c in df.columns]
    return df[~df.index.isna()].sort_index()


def circ(a):
    """Trung bình và độ lệch chuẩn vòng tròn (độ)."""
    a = np.deg2rad(pd.Series(a).dropna())
    if len(a) == 0:
        return np.nan, np.nan
    C, S = np.cos(a).mean(), np.sin(a).mean()
    R = max(np.hypot(C, S), 1e-9)
    return round(np.rad2deg(np.arctan2(S, C)) % 360, 1), round(np.rad2deg(np.sqrt(-2 * np.log(R))), 1)


def phase_drift_per_month(ts, ph_deg):
    """Độ trôi pha (°/tháng): unwrap quanh trung bình vòng tròn rồi hồi quy tuyến tính."""
    ph = pd.Series(ph_deg).values.astype(float)
    ok = ~np.isnan(ph)
    if ok.sum() < 10:
        return np.nan
    m = circ(ph[ok])[0]
    dev = ((ph - m + 180) % 360) - 180
    x = (ts - ts[0]).total_seconds().values / 86400
    return stats.linregress(x[ok], dev[ok]).slope * 30


def slope_per_month(x_days, y):
    m = ~np.isnan(y)
    if m.sum() < 10:
        return np.nan, np.nan
    lr = stats.linregress(x_days[m], y[m])
    return lr.slope * 30, lr.pvalue


def main(path):
    pd.set_option("display.width", 230)
    df = load_pull(path)
    amp = [f"{c}_amp" for c in CH]
    ph = [f"{c}_ph" for c in CH]
    step = df.index.to_series().diff().dt.total_seconds().div(60).value_counts().head(3).to_dict()
    print(f"File: {path}\nrows={len(df)}  range {df.index.min()} -> {df.index.max()}  step(min)={step}")
    print("NaN per column:", {c: int(v) for c, v in df.isna().sum().items() if v})

    run = (df[amp] > RUN_UM).sum(axis=1) >= RUN_MIN_CH
    d = df[run]
    print(f"running gate: {run.sum()}/{len(run)} ({run.mean() * 100:.1f}%)")

    base = pd.read_csv(f"{ROOT}/Data/HQC_train_healthy_flat.csv")
    b_amp = [c for c in base.columns if c.startswith("1X_Amp")]
    b_ph = [c for c in base.columns if c.startswith("1X_Phase")]
    x = (d.index - d.index[0]).total_seconds().values / 86400
    rows = []
    for k, a, p, ba, bp in zip(CH, amp, ph, b_amp, b_ph):
        sl, pv = slope_per_month(x, d[a].values)
        rows.append({"kênh": k, "median": d[a].median(), "p10": d[a].quantile(.1), "p90": d[a].quantile(.9),
                     "9b_median": base[ba].median(), "slope_um/th": sl, "p": pv,
                     "pha": circ(d[p])[0], "sd_pha": circ(d[p])[1], "pha_9b": circ(base[bp])[0]})
    print("\n=== Từng kênh (giờ máy chạy) so với nền 9b:")
    print(pd.DataFrame(rows).round(2).to_string(index=False))

    print("\n=== Theo tuần: ổ 2001 amp + pha:")
    wk = []
    for t0, s in d.resample("7D"):
        if len(s) < 100:
            continue
        wk.append({"tuần": t0.date(), "n": len(s), "2001X": s["2001X_amp"].median(), "2001Y": s["2001Y_amp"].median(),
                   "phX": circ(s["2001X_ph"])[0], "sdX": circ(s["2001X_ph"])[1],
                   "phY": circ(s["2001Y_ph"])[0], "sdY": circ(s["2001Y_ph"])[1],
                   "2003X": s["2003X_amp"].median(), "2005X": s["2005X_amp"].median()})
    print(pd.DataFrame(wk).round(1).to_string(index=False))

    # Quét cửa sổ nền theo THƯỚC HỆ 8 KÊNH: độ dốc biên độ (%/tháng so trung vị) và độ trôi pha
    # (°/tháng, hồi quy trên pha đã unwrap quanh trung bình vòng tròn). Xếp hạng theo tổng chuẩn hóa.
    print(f"\n=== Quét cửa sổ {WIN_DAYS} ngày, bước {STEP_DAYS} ngày — thước hệ 8 kênh (ổn định nhất trước):")
    out = []
    t = d.index.min()
    while t + pd.Timedelta(days=WIN_DAYS) <= d.index.max():
        w = d.loc[t:t + pd.Timedelta(days=WIN_DAYS)]
        xw = (w.index - w.index[0]).total_seconds().values / 86400
        sl = [abs(slope_per_month(xw, w[a].values)[0]) / w[a].median() * 100 for a in amp]
        pdr = [abs(phase_drift_per_month(w.index, w[p].values)) for p in ph]
        out.append({"từ": t.date(), "đến": (t + pd.Timedelta(days=WIN_DAYS)).date(), "n": len(w),
                    "dốc_TB": np.nanmean(sl), "dốc_max": np.nanmax(sl), "kênh_dốc": CH[int(np.nanargmax(sl))],
                    "pha_TB": np.nanmean(pdr), "pha_max": np.nanmax(pdr), "kênh_pha": CH[int(np.nanargmax(pdr))]})
        t += pd.Timedelta(days=STEP_DAYS)
    o = pd.DataFrame(out)
    if len(o):
        o["xếp_hạng"] = o["dốc_TB"] / o["dốc_TB"].median() + o["pha_TB"] / o["pha_TB"].median()
        print(o.round(2).sort_values("xếp_hạng").head(8).to_string(index=False))
    else:
        print(f"  (file ngắn hơn {WIN_DAYS} ngày, bỏ qua quét cửa sổ)")

    res = d[amp] - d[amp].resample("1D").transform("median")
    print("\n=== Nhiễu trong ngày (std sau khử trung vị ngày, trung vị qua các ngày):")
    print(res.groupby(res.index.floor("1D")).std().median().round(2).to_string())

    name = path.split("/")[-1].rsplit(".", 1)[0].replace(" ", "_")
    outp = f"{ROOT}/Dataclean/P29201A_1X_{name}.parquet"
    df.to_parquet(outp)
    print(f"\nsaved {outp}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else f"{ROOT}/Dataraw/Doan8_7.11.25-4.01.26.xlsx")
