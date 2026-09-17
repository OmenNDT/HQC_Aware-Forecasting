#!/usr/bin/env python3
"""35_tier_a_c_p29202a.py — Tầng A và tầng C trên P29202A với LUẬT VÀ NGƯỠNG ĐÃ KHÓA của P29201A.

Chỉ đổi: danh sách kênh (4 kênh ổ bơm), cổng chạy ≥ 3/4, kênh chữ ký tầng C = 2017X (ánh xạ ổ 2001 ↔ 2017,
quyết định 10/09/2026). Không huấn luyện, không đụng tầng B.

Vào: Dataclean_new/p29202a/{direct_long,feature_store_1x}.parquet (script 34)
Ra : Dataclean_new/p29202a/{tier_a_daily.parquet, tier_c_weekly.parquet, restart_checks.csv, summary.json}
     Bao_cao/p29202a-tang-a-c.png
"""
import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/home/sontn/Projects/HQC_Aware-Forecasting"
sys.path.insert(0, f"{ROOT}/scripts/New")
from alarm_utils import alarm_days                                          # noqa: E402
from phase01_config import TIERA_CONSEC, DATA_NEW                          # noqa: E402

IN = f"{ROOT}/Dataclean_new/p29202a"
CH = ["2017X", "2017Y", "2019X", "2019Y"]
CH_DIRECT = ["2017AX", "2017AY", "2019AX", "2019AY"]       # tên trong direct_long ("29VT-" + tên)
SIG = "2017X"                                              # kênh chữ ký tầng C (ứng với 2001X của A)
RUN_MIN_CH = 3


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


s17 = load("s17", f"{ROOT}/scripts/New/17_tier_a_direct_projection.py")
s18 = load("s18", f"{ROOT}/scripts/New/18_tier_b_slow_scale_and_tier_c.py")


def tier_a():
    w, skipped = s17.daily_direct(f"{IN}/direct_long.parquet", CH_DIRECT, RUN_MIN_CH)
    df = s17.project(w, CH_DIRECT)
    day = df.groupby("day")["flag"].any().astype(int); al = alarm_days(day, 0.5, TIERA_CONSEC)
    print(f"Tầng A — ngày chạy dùng: {len(w)} | đoạn chạy: {w.seg.nunique()} | ngày bỏ sau khởi động: {len(skipped)} | ngày có dòng: {df.day.nunique()}")
    print(f"  ngày cờ (1 ngày): {int(day.sum())} | ngày báo (≥ 2 ngày liên tiếp): {len(al)} → {[a.strftime('%d/%m/%Y') for a in al]}")
    print("  mức/dốc/D_low theo kênh (trung vị toàn kỳ):")
    print(df.groupby("ch")[["level", "ref90_median", "slope_um_day", "t_stat", "days_left_low"]].median().round(3).to_string())
    print("  D_low nhỏ nhất theo kênh:", df.groupby("ch").days_left_low.min().round(0).to_dict())
    print("  số ngày rising (mức > 1,10 × trung vị 90 ngày) theo kênh:", (df.level > 1.1 * df.ref90_median).groupby(df.ch).sum().astype(int).to_dict())
    return w, df, al


def tier_c():
    fs = pd.read_parquet(f"{IN}/feature_store_1x.parquet").sort_index()
    with open(f"{DATA_NEW}/locked_params_phase02.json") as f: rule = json.load(f)["rule_c"]
    restarts = s18.true_restarts(fs, f"{IN}/direct_long.parquet", RUN_MIN_CH)
    good = [c for c in CH if fs[f"amp_{c}"].notna().mean() > 0.5]                 # bỏ kênh 1X chết (2019X)
    assert SIG in good, f"kênh chữ ký {SIG} không đủ dữ liệu 1X"
    w = s18.weekly_signature(fs, rule, restarts, ch=good, sig=SIG)
    flags, alarms = w[w.c_flag], w[w.c_alarm]
    print(f"\nTầng C — tuần có chữ ký: {len(w)} | chạy lại sau dừng thật: {[r.strftime('%d/%m/%Y %H:%M') for r in restarts]}")
    print(f"  tuần cờ: {len(flags)} | tuần báo (2 tuần liên tiếp): {len(alarms)} | tuần trong 21 ngày sau khởi động: {int(w.post_restart.sum())}")
    print(f"  |tốc độ| tuần {SIG}: trung vị {w[f'rot_{SIG}_deg_wk'].abs().median():.2f}°/tuần, lớn nhất {w[f'rot_{SIG}_deg_wk'].abs().max():.2f} | sd trung vị {w[f'sd_{SIG}'].median():.2f}°")
    if len(flags): print(flags[["week_end", f"ph_{SIG}", f"sd_{SIG}", f"rot_{SIG}_deg_wk", "rot_prev8w", "post_restart"]].round(2).to_string())
    return w, restarts, rule


def restart_checks(fs, restarts):
    """Bước pha / biên độ sau mỗi lần chạy lại: 14 ngày trước dừng so với ngày 10–14 sau khởi động (như script 19, không có nền gốc)."""
    rows = []
    good = [c for c in CH if fs[f"amp_{c}"].notna().mean() > 0.5]
    for k, t_restart in enumerate(restarts):
        t_stop = fs.index[fs.index < t_restart].max()
        next_stop = fs.index[fs.index < restarts[k + 1]].max() if k + 1 < len(restarts) else fs.index.max()
        before = fs.loc[t_stop - pd.Timedelta(days=14): t_stop]
        a0, a1 = t_restart + pd.Timedelta(days=10), min(t_restart + pd.Timedelta(days=14), next_stop); incomplete = (a1 - a0) < pd.Timedelta(days=3)
        if a1 <= a0 + pd.Timedelta(hours=12): a0, a1 = max(t_restart, next_stop - pd.Timedelta(days=2)), next_stop; incomplete = True
        after = fs.loc[a0:a1]
        if len(before) < 200 or len(after) < 50: continue
        r = {"stop": t_stop, "restart": t_restart, "stop_days": round((t_restart - t_stop).total_seconds() / 86400, 1), "after_window": f"{a0:%d/%m %H:%M}–{a1:%d/%m %H:%M}", "incomplete": incomplete}
        for c in good:
            if before[f"amp_{c}"].notna().sum() < 50 or after[f"amp_{c}"].notna().sum() < 20: continue
            ph = lambda g: np.rad2deg(np.arctan2(np.nanmean(g[f"sin_{c}"]), np.nanmean(g[f"cos_{c}"]))) % 360
            r[f"{c}_amp_vs_before_pct"] = round((after[f"amp_{c}"].median() / before[f"amp_{c}"].median() - 1) * 100, 1)
            r[f"{c}_phase_vs_before_deg"] = round(((ph(after) - ph(before) + 180) % 360) - 180, 1)
        rows.append(r)
    out = pd.DataFrame(rows); print("\nKiểm tra khởi động (so 14 ngày trước dừng):"); print(out.to_string(index=False) if len(out) else "  không có lần dừng đủ dữ liệu")
    return out


def figure(w_a, df_a, w_c, out_png):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    bg, fg, grid = "#0f0f14", "#d8d8e0", "#26262f"
    fig, ax = plt.subplots(3, 1, figsize=(13, 9.5), facecolor=bg, sharex=True)
    for a in ax: a.set_facecolor(bg); a.tick_params(colors=fg); a.grid(color=grid, lw=.6); [s.set_color(grid) for s in a.spines.values()]
    for c, col in zip(CH_DIRECT, ["#e8c46a", "#8fd3a8", "#7fb2e8", "#e08b8b"]): ax[0].plot(w_a.index, w_a[c], lw=1, color=col, label=c)
    ax[0].axhline(65, color="#e05b5b", ls="--", lw=1); ax[0].text(w_a.index[0], 66, "ngưỡng nhà máy 65 µm", color="#e05b5b", fontsize=8)
    ax[0].set_ylabel("Direct trung vị ngày (µm)", color=fg); ax[0].legend(ncol=4, fontsize=8, facecolor=bg, labelcolor=fg, edgecolor=grid); ax[0].set_ylim(0, 70)
    dl = df_a.groupby("day").days_left_low.min().clip(upper=1e5)                # ∞ (dốc âm) cắt ở 100.000 ngày
    ax[1].plot(dl.index, dl.values, lw=1, color="#e8c46a"); ax[1].axhline(30, color="#e05b5b", ls="--", lw=1); ax[1].set_yscale("log")
    ax[1].set_ylabel("D_low nhỏ nhất (ngày, thang log)", color=fg); ax[1].text(dl.index[0], 36, "chân trời 30 ngày", color="#e05b5b", fontsize=8)
    ax[2].plot(w_c.index, w_c[f"rot_{SIG}_deg_wk"], lw=1.2, color="#8fd3a8", label=f"tốc độ quay pha {SIG} (°/tuần)")
    ax[2].axhline(1, color="#e05b5b", ls="--", lw=.8); ax[2].axhline(-1, color="#e05b5b", ls="--", lw=.8)
    for t in w_c.index[w_c.post_restart]: ax[2].axvspan(t, t + pd.Timedelta(days=7), color="#5a5a3a", alpha=.35, lw=0)
    ax[2].set_ylabel("Tầng C", color=fg); ax[2].legend(fontsize=8, facecolor=bg, labelcolor=fg, edgecolor=grid)
    fig.suptitle("P29202A · tầng A và C với ngưỡng khóa của P29201A · 13/07/2025–10/09/2026 (vùng xám = 21 ngày sau khởi động)", color=fg, fontsize=11)
    fig.tight_layout(); fig.savefig(out_png, dpi=130, facecolor=bg); print("hình:", out_png)


def main():
    pd.set_option("display.width", 220)
    w_a, df_a, al_a = tier_a(); w_c, restarts, rule = tier_c()
    fs = pd.read_parquet(f"{IN}/feature_store_1x.parquet").sort_index(); rc = restart_checks(fs, restarts)
    df_a.to_parquet(f"{IN}/tier_a_daily.parquet"); w_c.to_parquet(f"{IN}/tier_c_weekly.parquet"); rc.to_csv(f"{IN}/restart_checks.csv", index=False)
    figure(w_a, df_a, w_c, f"{ROOT}/Bao_cao/hinh-p29202a-tang-a-c.png")
    summ = {"data_period": [str(w_a.index.min().date()), str(w_a.index.max().date())], "tier_a_row_period": [str(df_a.day.min().date()), str(df_a.day.max().date())], "tier_a": {"run_days": int(len(w_a)), "segments": int(w_a.seg.nunique()), "row_days": int(df_a.day.nunique()),
            "flag_days": int(df_a.groupby("day").flag.any().sum()), "alarm_days": [str(a.date()) for a in al_a], "min_days_left_low": {c: (None if np.isinf(v) else round(float(v), 1)) for c, v in df_a.groupby("ch").days_left_low.min().items()}},
            "tier_c": {"weeks": int(len(w_c)), "flag_weeks": int(w_c.c_flag.sum()), "alarm_weeks": int(w_c.c_alarm.sum()), "post_restart_weeks": int(w_c.post_restart.sum()),
                       "restarts": [str(r) for r in restarts], "sig": SIG, "rule": rule, "abs_rate_max": float(w_c[f"rot_{SIG}_deg_wk"].abs().max())},
            "thresholds_from": ["scripts/New/phase01_config.py (tầng A)", "Dataclean_new/locked_params_phase02.json (rule_c)"]}
    with open(f"{IN}/summary.json", "w") as f: json.dump(summ, f, indent=1, ensure_ascii=False); print("\nsummary:", json.dumps({k: summ[k] for k in ["tier_a", "tier_c"]}, ensure_ascii=False, default=str)[:600])


if __name__ == "__main__":
    main()
