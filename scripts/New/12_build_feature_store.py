#!/usr/bin/env python3
"""12_build_feature_store.py — Gộp 6 lần kéo 1X (10 phút) thành một kho đặc trưng 24 chiều.

Quy trình chung phase 01 (mục 3): cổng máy chạy, sửa tham chiếu pha +148° cho đoạn 7/8,
điền khuyết ≤ 6 dòng, đặc trưng thô (amp, sin, cos) — KHÔNG chuẩn hóa ở đây (scaler fit theo fold).

Vai trò (role) theo mục 2 phase 01:
  train        9b 20/02–22/03/2026
  config_pos   9c 23/03–30/04   (chỉnh dung lượng + ngưỡng tốc độ)
  precheck_pos 9c 01/05–29/05   (kiểm trước, không sửa gì)
  neg          đoạn 7; đoạn 8 cửa sổ 02/12–01/01; 9a 15/01–05/02
  report       đoạn 8 ngoài cửa sổ; 9c 02–10/06 (quá độ); 05/02–19/02 (1 giờ, từ 51_Vib180d)
  blind        đoạn 11 14/06–02/09

Ra: Dataclean_new/feature_store_1x.parquet  (index ts; cột episode, role, cadence_min,
    phase_ref_corrected, amp_<ch>×8, sin_<ch>×8, cos_<ch>×8)
"""
import numpy as np
import pandas as pd
import openpyxl
from datetime import datetime

ROOT = "/home/sontn/Projects/HQC_Aware-Forecasting"
CH = ["2001X", "2001Y", "2003X", "2003Y", "2005X", "2005Y", "2007X", "2007Y"]
TURBINE = ["2005X", "2005Y", "2007X", "2007Y"]
PHASE_SHIFT_DEG = 148.0        # xoay tham chiếu tua-bin tại lần dừng 1 (ước lượng đoạn 8 vs 9b)
RUN_UM, RUN_MIN_CH, FFILL_MAX = 3.0, 6, 6

# (file parquet đã parse bởi scripts/Old/11 (Dataclean_old), episode, sửa pha?, danh sách (từ, đến, role))
SOURCES = [
    ("P29201A_1X_ep7_28sep-04nov2025", "ep7", True, [("2025-09-28", "2025-11-05", "neg")]),
    ("P29201A_1X_Doan8_7.11.25-4.01.26", "ep8", True, [("2025-11-07", "2025-12-01 23:59", "report"),
                                                        ("2025-12-02", "2026-01-01 23:59", "neg"),
                                                        ("2026-01-02", "2026-01-05", "report")]),
    ("P29201A_1X_Doan-9a.15.01.26–05.02.26", "9a", False, [("2026-01-15", "2026-02-06", "neg")]),
    ("P29201A_1X_Doan9b_20.02.26-22.03.26", "9b", False, [("2026-02-20", "2026-03-23", "train")]),
    ("P29201A_1X_Doan9c_23.03.26-13.06.26", "9c", False, [("2026-03-23", "2026-04-30 23:59", "config_pos"),
                                                          ("2026-05-01", "2026-05-29 23:59", "precheck_pos"),
                                                          ("2026-06-02", "2026-06-10 23:59", "report")]),
    ("P29201A_1X_Doan11_14.06.26-2.09.26", "ep11", False, [("2026-06-14", "2026-09-03", "blind")]),
]


def prepare(df, correct_phase):
    """Cổng máy chạy → điền khuyết ngắn → bỏ dòng còn NaN → sửa pha tua-bin nếu cần."""
    amp = [f"{c}_amp" for c in CH]
    run = (df[amp] > RUN_UM).sum(axis=1) >= RUN_MIN_CH
    d = df[run].copy()
    d = d.ffill(limit=FFILL_MAX).dropna()
    if correct_phase:
        for c in TURBINE:
            d[f"{c}_ph"] = (d[f"{c}_ph"] + PHASE_SHIFT_DEG) % 360.0
    return d


def featurize(d):
    """24 cột thô: amp (µm), sin(pha), cos(pha) theo thứ tự CH."""
    out = pd.DataFrame(index=d.index)
    for c in CH:
        out[f"amp_{c}"] = d[f"{c}_amp"].astype(float)
    ph = {c: np.deg2rad(d[f"{c}_ph"].astype(float)) for c in CH}
    for c in CH:
        out[f"sin_{c}"] = np.sin(ph[c])
    for c in CH:
        out[f"cos_{c}"] = np.cos(ph[c])
    return out


def load_hourly_report_segment():
    """05/02–19/02/2026 chỉ có 1 giờ trong 51_Vib180d — vai trò report (leo vào nền)."""
    ws = openpyxl.load_workbook(f"{ROOT}/Dataraw/PI Data.xlsx", read_only=True, data_only=True)["51_Vib180d"]
    rows, seen = [], False
    for r in ws.iter_rows(values_only=True):
        if not seen and r[0] == "Timestamp":
            seen = True
            continue
        if seen and isinstance(r[0], datetime):
            rows.append((r[0],) + tuple(r[1:17]))
    cols = ["ts"] + [f"{c}_amp" for c in CH] + [f"{c}_ph" for c in CH]
    h = pd.DataFrame(rows, columns=cols).set_index("ts").apply(pd.to_numeric, errors="coerce")
    h.index = h.index.round("10min")
    return h.loc["2026-02-05":"2026-02-19 23:59"]


def main():
    parts = []
    for fname, ep, corr, roles in SOURCES:
        d = prepare(pd.read_parquet(f"{ROOT}/Dataclean_old/{fname}.parquet"), corr)
        f = featurize(d)
        f["episode"], f["cadence_min"], f["phase_ref_corrected"], f["role"] = ep, 10, corr, None
        for a, b, role in roles:
            f.loc[a:b, "role"] = role
        f = f.dropna(subset=["role"])
        parts.append(f)
        print(f"{ep:5s} {len(d):6d} dòng sau cổng/khuyết → {f['role'].value_counts().to_dict()}")
    h = featurize(prepare(load_hourly_report_segment(), False))
    h["episode"], h["cadence_min"], h["phase_ref_corrected"], h["role"] = "9a_climb", 60, False, "report"
    parts.append(h)
    print(f"9a_climb (1 giờ) {len(h)} dòng → report")

    fs = pd.concat(parts).sort_index()
    fs.index.name = "ts"
    out = f"{ROOT}/Dataclean_new/feature_store_1x.parquet"
    fs.to_parquet(out)
    print("\nTổng theo role:\n" + fs.groupby("role").size().to_string())
    print(f"\nsaved {out}  ({len(fs)} dòng, {fs.shape[1]} cột)")


if __name__ == "__main__":
    main()
