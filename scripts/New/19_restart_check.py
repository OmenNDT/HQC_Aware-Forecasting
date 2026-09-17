#!/usr/bin/env python3
"""19_restart_check.py — Kiểm tra sau khởi động (phase 02 mục 3.4), bản sửa theo code review 04/09 13:10.

Với mỗi lần dừng THẬT (khoảng trống > 12 h có ngày Direct không chạy): so ngày 10–14 sau khởi động — cắt ngắn nếu
gặp lần dừng kế tiếp, đánh dấu 'incomplete' nếu < 3 ngày — với 14 ngày trước dừng và với nền 9b:
  - biên độ 1X từng kênh: % so trước dừng, % so nền; pha 1X: lệch so trước dừng và so nền;
  - kiểm tham chiếu pha tua-bin trên PHA THÔ (hoàn lại +148° cho các dòng đã sửa): 4 kênh 2005/2007 cùng lệch > 60°,
    biên độ đổi < 15% → 'xoay tham chiếu'.
Ra: Dataclean_new/restart_checks.csv
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402

CH = ["2001X", "2001Y", "2003X", "2003Y", "2005X", "2005Y", "2007X", "2007Y"]
TURB = ["2005X", "2005Y", "2007X", "2007Y"]
PHASE_SHIFT_DEG = 148.0


def raw_phase(g, c):
    """Pha thô (°): hoàn lại phép cộng 148° ở các dòng có phase_ref_corrected."""
    ph = np.rad2deg(np.arctan2(g[f"sin_{c}"], g[f"cos_{c}"])) % 360
    if c in TURB:
        ph = np.where(g["phase_ref_corrected"].values, (ph - PHASE_SHIFT_DEG) % 360, ph)
    return ph


def circ_mean(a):
    a = np.deg2rad(np.asarray(a, float)); return np.rad2deg(np.arctan2(np.nanmean(np.sin(a)), np.nanmean(np.cos(a)))) % 360


def summarize(g):
    return {c: (g[f"amp_{c}"].median(), circ_mean(raw_phase(g, c))) for c in CH}


def dphi(a, b):
    return ((a - b + 180) % 360) - 180


def stopped_days():
    c5 = pd.read_parquet(DIRECT_LONG); vt = [s for s in c5.sensor.unique() if s.startswith("29VT")]
    d = c5[c5.sensor.isin(vt)].copy(); d["day"] = d.ts.dt.floor("1D")
    w = d.pivot_table(index="day", columns="sensor", values="val", aggfunc="median")
    return set(w.index[(w > 3.0).sum(axis=1) < 6])


def main():
    fs_all = pd.read_parquet(FEATURE_STORE).sort_index(); fs = fs_all[fs_all.cadence_min == 10]
    base = summarize(fs[fs.role == "train"]); stop_days = stopped_days()
    gaps = fs_all.index.to_series().diff() > pd.Timedelta(hours=12)
    restarts = [t for t in fs_all.index[gaps.values]
                if any(dd in stop_days for dd in pd.date_range(fs_all.index[fs_all.index < t].max().floor("1D"), t.floor("1D")))]
    rows = []
    for k, t_restart in enumerate(restarts):
        t_stop = fs_all.index[fs_all.index < t_restart].max()
        if fs.index.min() >= t_stop - pd.Timedelta(days=14): continue
        next_stop = fs_all.index[fs_all.index < restarts[k + 1]].max() if k + 1 < len(restarts) else fs.index.max()
        before = fs.loc[t_stop - pd.Timedelta(days=14): t_stop]
        a0, a1 = t_restart + pd.Timedelta(days=10), min(t_restart + pd.Timedelta(days=14), next_stop)
        incomplete = (a1 - a0) < pd.Timedelta(days=3)
        if a1 <= a0 + pd.Timedelta(hours=12):                              # lần dừng kế tiếp tới sớm hơn ngày 10: lấy 2 ngày cuối của đoạn chạy, ghi 'chưa đủ'
            a0, a1 = max(t_restart, next_stop - pd.Timedelta(days=2)), next_stop; incomplete = True
        after = fs.loc[a0:a1]
        if len(before) < 200 or len(after) < 50: continue
        b, a = summarize(before), summarize(after)
        turb_shift = [abs(dphi(a[c][1], b[c][1])) for c in TURB]; turb_amp = [abs(a[c][0] / b[c][0] - 1) for c in TURB]
        ref_rot = all(s > 60 for s in turb_shift) and all(x < 0.15 for x in turb_amp)
        r = {"stop": t_stop, "restart": t_restart, "stop_days": round((t_restart - t_stop).total_seconds() / 86400, 1),
             "after_window": f"{a0:%d/%m %H:%M}–{a1:%d/%m %H:%M}", "incomplete": incomplete, "ref_rotation_turbine": ref_rot}
        for c in CH:
            r[f"{c}_amp_vs_before_pct"] = round((a[c][0] / b[c][0] - 1) * 100, 1); r[f"{c}_amp_vs_base_pct"] = round((a[c][0] / base[c][0] - 1) * 100, 1)
            r[f"{c}_phase_vs_before_deg"] = round(dphi(a[c][1], b[c][1]), 1); r[f"{c}_phase_vs_base_deg"] = round(dphi(a[c][1], base[c][1]), 1)
        rows.append(r)
        print(f"\n=== Dừng {t_stop:%d/%m/%Y %H:%M} → chạy lại {t_restart:%d/%m/%Y %H:%M} ({r['stop_days']} ngày) · cửa sổ sau: {r['after_window']}"
              f"{' · CHƯA ĐỦ 3 NGÀY' if incomplete else ''}{'  ⚠ XOAY THAM CHIẾU PHA TUA-BIN' if ref_rot else ''}")
        print(pd.DataFrame({"amp vs trước %": [r[f"{c}_amp_vs_before_pct"] for c in CH], "amp vs nền %": [r[f"{c}_amp_vs_base_pct"] for c in CH],
                            "pha vs trước °": [r[f"{c}_phase_vs_before_deg"] for c in CH], "pha vs nền °": [r[f"{c}_phase_vs_base_deg"] for c in CH]}, index=CH).to_string())
    out = pd.DataFrame(rows); out.to_csv(f"{DATA_NEW}/restart_checks.csv", index=False); print(f"\nsaved {DATA_NEW}/restart_checks.csv ({len(out)} lần)")


if __name__ == "__main__":
    main()
