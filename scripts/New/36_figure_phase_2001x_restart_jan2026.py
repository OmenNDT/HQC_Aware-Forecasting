#!/usr/bin/env python3
"""36_figure_phase_2001x_restart_jan2026.py — Pha 1X kênh 2001X quanh lần dừng 1 (04/01) và khởi động lại 15/01/2026.

Trên: pha 10 phút (chấm mờ) + trung bình tròn theo ngày (đường), khoảng dừng tháo kiểm tra, bước nhảy +39°
      (102° trước dừng → 141° sau tháo lắp) và đợt xoay 33° ngày 26–30/01 (141° → 108°).
Dưới: tốc độ quay pha tuần (°/tuần, hồi quy 4 tuần) từ luật C, so với tham chiếu 8 tuần trước và sd tuần —
      giải thích vì sao tầng C có dấu hiệu ở tuần 18–24/01 rồi mất dấu khi sd vượt 5°.
Ra: Bao_cao/hinh-pha-2001X-khoi-dong-lai-15-01.png
"""
import os, sys, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.dates as mdates

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from alarm_utils import load_script                                       # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__))
s18 = load_script("s18", "18_tier_b_slow_scale_and_tier_c.py", HERE)
OUT = f"{ROOT}/Bao_cao/hinh-pha-2001X-khoi-dong-lai-15-01.png"

BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": SF, "axes.edgecolor": "#26262f", "axes.labelcolor": INK2, "xtick.color": MUTE,
                     "ytick.color": MUTE, "text.color": INK, "font.family": "DejaVu Sans", "font.size": 9.5, "axes.grid": True, "grid.color": "#ffffff",
                     "grid.alpha": .06, "axes.spines.top": False, "axes.spines.right": False})

T0, T1 = pd.Timestamp("2025-12-01"), pd.Timestamp("2026-02-06")
STOP_A, STOP_B = pd.Timestamp("2026-01-04 03:00"), pd.Timestamp("2026-01-15")   # dòng cuối 04/01 → khởi động lại 15/01
ROT_A, ROT_B = pd.Timestamp("2026-01-26"), pd.Timestamp("2026-01-30 23:59")      # đợt xoay 33°


def phase_deg(df, ch="2001X"):
    return np.rad2deg(np.arctan2(df[f"sin_{ch}"], df[f"cos_{ch}"])) % 360


def daily_circ_mean(ph):
    """Trung bình tròn theo ngày (°), bỏ ngày < 10 mẫu."""
    rows = {t: s18.circ_mean_sd(g.values)[0] for t, g in ph.resample("1D")}
    return pd.Series(rows).dropna().asfreq("1D")   # ngày thiếu → NaN để đường vẽ đứt qua khoảng dừng


def main():
    lock2 = json.load(open(f"{DATA_NEW}/locked_params_phase02.json"))
    fs = pd.read_parquet(FEATURE_STORE); fs10 = fs[fs.cadence_min == 10]
    ph = phase_deg(fs10); win = ph[T0:T1]; day = daily_circ_mean(win)
    w = s18.weekly_signature(fs10, lock2["rule_c"], [pd.Timestamp(r) for r in lock2["restarts_true"]])
    before = w.loc["2025-12-28", "ph_2001X"]                                   # chữ ký tuần cuối trước dừng (28/12–03/01)
    after = w.loc["2026-01-11", "ph_2001X"]                                    # chữ ký tuần đầu sau khởi động (15–17/01)
    rot_from, rot_to = after, s18.circ_mean_sd(ph["2026-01-30":"2026-01-31"].values)[0]   # bình nguyên sau khởi động → mức cuối đợt xoay
    jump, rot = after - before, rot_from - rot_to
    ww = w[(w.index >= T0 - pd.Timedelta(days=7)) & (w.index <= T1)]
    print(f"trước dừng {before:.0f}°, sau khởi động {after:.0f}°, bước nhảy {jump:+.0f}°; xoay 26–30/01: {rot_from:.0f}° → {rot_to:.0f}° = {rot:.0f}°")
    print(ww[["week_end", "ph_2001X", "sd_2001X", "rot_2001X_deg_wk", "rot_prev8w", "c_flag", "c_alarm", "post_restart"]].round(1).to_string())

    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(14, 8.2), dpi=130, sharex=True, gridspec_kw={"height_ratios": [2.2, 1], "hspace": .10})
    for a in (ax, ax2):
        a.axvspan(STOP_A, STOP_B, color="#ffffff", alpha=.08, lw=0)
        a.axvspan(ROT_A, ROT_B, color=ROSE, alpha=.10, lw=0)
    # --- trên: pha ---
    ax.scatter(win.index, win.values, s=3, color=BLUE, alpha=.18, lw=0, rasterized=True, label="pha 10 phút")
    ax.plot(day.index, day.values, color=INK, lw=1.8, label="trung bình tròn theo ngày")
    ax.hlines(before, pd.Timestamp("2025-12-29"), STOP_B, color=TEAL, lw=1.4, ls="--"); ax.hlines(after, STOP_A, pd.Timestamp("2026-01-21"), color=AMB, lw=1.4, ls="--")
    xm = pd.Timestamp("2026-01-09 12:00")
    ax.annotate("", (xm, after), (xm, before), arrowprops=dict(arrowstyle="-|>", color=AMB, lw=1.8))
    ax.text(xm + pd.Timedelta(hours=14), (before + after) / 2, f"bước nhảy {jump:+.0f}°\n{before:.0f}° → {after:.0f}°\nngay lúc khởi động lại 15/01", color=AMB, fontsize=9.5, va="center")
    ax.text(STOP_A + pd.Timedelta(days=.4), 150, "dừng 1\ntháo kiểm tra\n04→15/01", color=INK2, fontsize=8.5, va="top")
    ax.annotate("", (ROT_B, rot_to), (pd.Timestamp("2026-01-25 12:00"), rot_from), arrowprops=dict(arrowstyle="-|>", color=ROSE, lw=1.8, connectionstyle="arc3,rad=-.25"))
    ax.text(ROT_B + pd.Timedelta(days=.6), (rot_from + rot_to) / 2 + 6, f"đợt xoay {rot:.0f}° ngày 26–30/01\n{rot_from:.0f}° → {rot_to:.0f}°, về gần mức trước dừng\n(sd tuần lên 10,7°, luật C mất dấu)", color=ROSE, fontsize=9.5, va="center")
    ax.set_ylim(92, 156); ax.set_ylabel("pha 1X kênh 2001X (°)"); ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    ax.set_title("Pha 1X ổ 2001 hướng X quanh lần dừng tháo kiểm tra 04/01 và khởi động lại 15/01/2026 (P29201A, 10 phút)", color=INK, fontsize=11, loc="left")
    # --- dưới: tốc độ quay pha tuần theo luật C ---
    r = ww.rot_2001X_deg_wk; cols = [BAD if f else (BLUE if not np.isnan(v) else MUTE) for f, v in zip(ww.c_flag, r)]
    ax2.bar(ww.week_end, r.fillna(0), width=5, color=cols, alpha=.85, lw=0, label="tốc độ quay pha (°/tuần, hồi quy 4 tuần)")
    ax2.plot(ww.week_end, ww.rot_prev8w, color=TEAL, lw=1.2, ls="--", marker="o", ms=3.5, label="tham chiếu 8 tuần trước")
    ax2.axhline(0, color=INK2, lw=.8)
    for t, v, sd, f in zip(ww.week_end, r, ww.sd_2001X, ww.c_flag):
        if np.isnan(v): continue
        ax2.text(t, v + (.6 if v >= 0 else -.6), f"{v:+.0f}°\nsd {sd:.1f}°", ha="center", va="bottom" if v >= 0 else "top", fontsize=8, color=BAD if f else INK2)
    ax2.set_ylim(-17.5, 16); ax2.set_ylabel("°/tuần"); ax2.legend(loc="upper left", frameon=False, fontsize=8.5)
    ax2.text(pd.Timestamp("2025-12-02"), -16.3, "đỏ = tuần có dấu hiệu luật C (đổi dấu so 8 tuần trước, |tốc độ| > 1°/tuần, sd < 5°); hai tuần liền 18–24/01 → báo, nằm trong 21 ngày sau khởi động", fontsize=8, color=INK2)
    ax2.xaxis.set_major_locator(mdates.DayLocator(interval=7)); ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax2.set_xlim(T0, T1 + pd.Timedelta(days=1))
    fig.savefig(OUT, bbox_inches="tight", facecolor=BG); print("saved", OUT)


if __name__ == "__main__":
    main()
