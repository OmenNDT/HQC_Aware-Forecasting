#!/usr/bin/env python3
"""34_ingest_p29202a.py — Đọc cặp tệp PI DataLink của P29202A (Direct + 1X, 13/07/2025–10/09/2026) thành
dạng dữ liệu mà script 17/18 dùng cho P29201A, không đổi luật nào.

Ra (Dataclean_new/p29202a/):
  direct_long.parquet      : sensor ("29VT-2017AX"…), ts, val, running — cùng dạng DIRECT_LONG của A
  feature_store_1x.parquet : index ts 10 phút, amp_/sin_/cos_ cho 2017X 2017Y 2019X 2019Y, episode, role,
                             cadence_min, phase_ref_corrected — cùng dạng FEATURE_STORE của A
  run_segments.csv         : đoạn chạy/dừng ≥ 1 giờ theo cổng Direct

Cổng máy chạy: ≥ 3/4 kênh Direct ổ bơm > 3 µm (A: ≥ 6/8, cùng tỷ lệ 75 %). Dòng 1X chỉ giữ khi máy chạy
(gate bằng Direct cùng thời điểm, vì 1X chỉ có 2 kênh tin cậy); điền khuyết ≤ 6 dòng như script 12.
"""
import os
import numpy as np
import pandas as pd

ROOT = "/home/sontn/Projects/HQC_Aware-Forecasting"
RAW_1X = f"{ROOT}/Dataraw/P29202A_1X_13.07.25-10.09.26.xlsx"
RAW_DIRECT = f"{ROOT}/Dataraw/P29202A_Direct_13.07.25-10.09.26.xlsx"
OUT = f"{ROOT}/Dataclean_new/p29202a"
CH = ["2017X", "2017Y", "2019X", "2019Y"]           # tên kênh trong kho đặc trưng (khớp quy ước CH của A)
TAG = {c: f"29VT-{c[:4]}A{c[4]}" for c in CH}        # 2017X → 29VT-2017AX (tên cảm biến trong DIRECT_LONG)
RUN_UM, RUN_MIN_CH, FFILL_MAX = 3.0, 3, 6
HEADER_ROW, FIRST_DATA_ROW = 11, 12                  # hàng 12 (0-based 11) = tên cột; dữ liệu từ hàng 13


def read_datalink(path):
    """Đọc mẫu xuất PI DataLink: cột 0 thời gian (datetime hoặc số ngày Excel), ô chữ (Bad/Not Connect/Configure) → NaN."""
    df = pd.read_excel(path, header=None)
    hdr = df.iloc[HEADER_ROW].tolist()
    if str(hdr[0]).strip() != "Thoi diem":                                 # mẫu xuất đổi bố cục → báo rõ thay vì KeyError mờ
        raise ValueError(f"{os.path.basename(path)}: hàng {HEADER_ROW + 1} không phải hàng tên cột ('Thoi diem'), thấy {hdr[0]!r}")
    d = df.iloc[FIRST_DATA_ROW:].copy(); d.columns = ["ts"] + hdr[1:]
    ts = pd.to_datetime(pd.to_numeric(d["ts"], errors="coerce"), unit="D", origin="1899-12-30")
    d["ts"] = ts.fillna(pd.to_datetime(d["ts"], errors="coerce")).dt.round("min"); d = d.dropna(subset=["ts"]).set_index("ts")
    keep = [c for c in d.columns if isinstance(c, str) and c.startswith("29VT") and ("(um)" in c or "(do)" in c)]
    return d[keep].apply(pd.to_numeric, errors="coerce")


def direct_long(dd):
    """Bảng dài như DIRECT_LONG của A + cột running theo cổng ≥ 3/4 kênh > 3 µm."""
    cols = {c: f"{TAG[c]} Direct (um)" for c in CH}
    w = dd[[cols[c] for c in CH]].copy(); w.columns = CH
    run = (w > RUN_UM).sum(axis=1) >= RUN_MIN_CH
    rows = [pd.DataFrame({"sensor": TAG[c], "ts": w.index, "raw_val": w[c].values, "kind": "vibration", "val": w[c].values,
                          "running": run.astype(float).values}) for c in CH]
    return pd.concat(rows, ignore_index=True).dropna(subset=["val"]), run


def feature_store(dx, run):
    """amp/sin/cos 10 phút khi máy chạy; kênh không có 1X (2019X chết) để NaN."""
    out = pd.DataFrame(index=dx.index)
    for c in CH:
        a, p = f"{TAG[c]} 1X Amp (um)", f"{TAG[c]} 1X Phase (do)"
        amp = dx[a] if a in dx else pd.Series(np.nan, index=dx.index); ph = np.deg2rad(dx[p]) if p in dx else pd.Series(np.nan, index=dx.index)
        out[f"amp_{c}"] = amp
        out[f"sin_{c}"] = np.sin(ph); out[f"cos_{c}"] = np.cos(ph)
    r = run.reindex(out.index).fillna(False).astype(bool)
    out = out[r]
    # điền khuyết ≤ 6 dòng trong cùng đoạn liên tục (như script 12), chỉ trên kênh có dữ liệu
    has = [c for c in CH if out[f"amp_{c}"].notna().any()]
    cols = [f"{k}_{c}" for c in has for k in ("amp", "sin", "cos")]
    seg = (out.index.to_series().diff() > pd.Timedelta(minutes=10)).cumsum()
    out[cols] = out.groupby(seg)[cols].ffill(limit=FFILL_MAX)
    out = out.dropna(subset=[f"amp_{c}" for c in has], how="all")
    out["episode"], out["role"], out["cadence_min"], out["phase_ref_corrected"] = "p29202a", "report", 10, False
    return out


def run_segments(run):
    seg = (run != run.shift()).cumsum()
    t = pd.DataFrame({"run": run, "seg": seg}).groupby("seg").agg(start=("run", lambda s: s.index.min()), end=("run", lambda s: s.index.max()),
                                                                 running=("run", "first"), n=("run", "size"))
    t["days"] = (t.n / 144).round(2); return t[t.n >= 6].reset_index(drop=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    dd, dx = read_datalink(RAW_DIRECT), read_datalink(RAW_1X)
    missing = [f"{TAG[c]} Direct (um)" for c in CH if f"{TAG[c]} Direct (um)" not in dd]
    if missing: raise ValueError(f"tệp Direct thiếu cột {missing}")
    if not dd.index.equals(dx.index):                                       # Direct là chủ lưới; 1X lệch vài dòng thì đưa về lưới Direct
        lost = len(dx.index.difference(dd.index)); print(f"CẢNH BÁO: lưới 1X khác Direct, {lost} dòng 1X ngoài lưới bị bỏ"); dx = dx.reindex(dd.index)
        if lost > 0.001 * len(dd): raise ValueError("lưới 1X lệch Direct quá 0,1 %, kiểm tra lại hai tệp xuất")
    dl, run = direct_long(dd); fs = feature_store(dx, run); segs = run_segments(run)
    dl.to_parquet(f"{OUT}/direct_long.parquet"); fs.to_parquet(f"{OUT}/feature_store_1x.parquet"); segs.to_csv(f"{OUT}/run_segments.csv", index=False)
    print(f"Direct: {dd.index.min()} → {dd.index.max()}, {len(dd)} dòng 10 phút | máy chạy {run.mean()*100:.1f} % | dòng dài {len(dl)}")
    print(f"Kho 1X khi chạy: {len(fs)} dòng; kênh có 1X: {[c for c in CH if fs[f'amp_{c}'].notna().any()]}")
    print("Đoạn chạy/dừng ≥ 1 giờ:"); print(segs.to_string(index=False))


if __name__ == "__main__":
    main()
