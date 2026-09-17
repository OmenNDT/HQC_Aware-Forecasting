#!/usr/bin/env python3
"""21_figures_three_tiers.py — Một hình ba tầng trên cùng trục thời gian 9/2025 → 9/2026.

Tầng A: Direct 2001AX, 2003AX + ngưỡng 65 µm + ngày báo. Tầng B: SPE SAE (log) + giới hạn + ngày báo 14 ngày (đỏ) và 45 ngày (vàng).
Tầng C: tốc độ quay pha 2001X (°/tuần) + tuần cờ/báo. Hai lần dừng tháo kiểm tra. Ra: Bao_cao/hinh-ba-tang-toan-chuoi.png
"""
import json, os, pickle, sys, importlib.util
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.dates as mdates

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from alarm_utils import alarm_days, load_script                           # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__))
cv13, s18 = load_script("cv13", "13_blocked_cv_train_compare.py", HERE), load_script("s18", "18_tier_b_slow_scale_and_tier_c.py", HERE)
BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": SF, "axes.edgecolor": "#26262f", "axes.labelcolor": INK2, "xtick.color": MUTE,
                     "ytick.color": MUTE, "text.color": INK, "font.family": "DejaVu Sans", "font.size": 9.5, "axes.grid": True, "grid.color": "#ffffff",
                     "grid.alpha": .06, "axes.spines.top": False, "axes.spines.right": False})


def main():
    lock2 = json.load(open(f"{DATA_NEW}/locked_params_phase02.json")); tau14, tau45, model = lock2["tau14"], lock2["tau45"], lock2["model"]
    res = pd.read_csv(CV_RESULTS).set_index("model")
    fs = pd.read_parquet(FEATURE_STORE); fs10 = fs[fs.cadence_min == 10]
    d = pd.read_parquet(f"{DATA_NEW}/tier_b45_daily.parquet"); obj = pickle.load(open(f"{MODEL_DIR}/{model}.pkl", "rb"))
    blind = fs10[fs10.role == "blind"]; spe_b = cv13.score_segments(obj["model"], obj["scaler"], blind)
    db = pd.DataFrame({"spe": spe_b, "role": "blind", "episode": "ep11"})
    db["slope14"] = cv13.slope_series(db.spe).reindex(db.index.floor("1D")).values; db["slope45"] = s18.slope_slow(db.spe).reindex(db.index.floor("1D")).values
    allb = pd.concat([d, db]).sort_index(); nr = allb[allb.role != "report"]
    b14 = alarm_days(nr.slope14.resample("1D").first().dropna(), tau14, CONSEC); b45 = alarm_days(nr.slope45.resample("1D").first().dropna(), tau45, lock2["slow_consec"])
    ta = pd.read_parquet(f"{DATA_NEW}/tier_a_daily.parquet"); a_al = alarm_days(ta.groupby("day").flag.any().astype(int), 0.5, TIERA_CONSEC)
    lev = ta.pivot_table(index="day", columns="ch", values="level")
    wC = s18.weekly_signature(fs10, lock2["rule_c"], [pd.Timestamp(r) for r in lock2["restarts_true"]])
    fig, axs = plt.subplots(3, 1, figsize=(15, 10.5), dpi=130, sharex=True, gridspec_kw={"height_ratios": [1.1, 1.2, .9], "hspace": .12})
    for ax in axs:
        for a0, b0, lab in [("2026-01-04", "2026-01-14", "dừng 1"), ("2026-05-29", "2026-06-13", "dừng 2")]:
            ax.axvspan(pd.Timestamp(a0), pd.Timestamp(b0), color="#ffffff", alpha=.08, lw=0)
        ax.axvspan(pd.Timestamp("2026-02-20"), pd.Timestamp("2026-03-22"), color=TEAL, alpha=.18, lw=0)
        ax.axvspan(pd.Timestamp("2026-06-14"), pd.Timestamp("2026-09-02"), color=ROSE, alpha=.10, lw=0)
    # A
    ax = axs[0]; ax.plot(lev.index, lev["2001AX"], color=TEAL, lw=1.6, label="Direct 2001AX"); ax.plot(lev.index, lev["2003AX"], color=AMB, lw=1.2, alpha=.8, label="Direct 2003AX")
    ax.axhline(PLANT_LIMIT_UM, color=BAD, ls="--", lw=1.2, label="ngưỡng nhà máy 65 µm p-p")
    ax.scatter(a_al, [68] * len(a_al), s=22, color=BAD, marker="v", label=f"tầng A báo (còn < {TIERA_HORIZON_DAYS} ngày, leo so chính nó)")
    ax.set_ylim(0, 72); ax.set_ylabel("Direct (µm p-p)"); ax.legend(loc="upper left", frameon=False, fontsize=8.5, ncol=4)
    ax.set_title("Ba tầng cảnh báo trên toàn chuỗi 9/2025 → 9/2026 · nền 9b (xanh) · kiểm mù đoạn 11 (hồng) · hai lần dừng tháo kiểm tra (xám)", loc="left", fontsize=12, fontweight="bold", pad=10)
    # B
    ax = axs[1]; day = allb.spe.resample("1D").median().dropna(); ax.plot(day.index, day.values, color=TEAL, lw=1.6, label=f"SPE {model} (trung vị ngày)")
    ax.axhline(res.loc[model, "limit99_6h"], color=AMB, ls="--", lw=1.1, label="giới hạn 99% ngoài mẫu")
    ax.scatter(b14, day.reindex(b14).values, s=26, color=BAD, zorder=5, label=f"báo 14 ngày (τ₁₄ = {tau14})")
    ax.scatter(b45, day.reindex(b45).values * 1.6, s=22, color=AMB, marker="s", zorder=5, label=f"báo 45 ngày (τ₄₅ = {tau45})")
    ax.set_yscale("log"); ax.set_ylabel("SPE (log)"); ax.legend(loc="lower right", frameon=False, fontsize=8.5, ncol=2)
    # C
    ax = axs[2]; r = wC["rot_2001X_deg_wk"]; ax.bar(r.index, r.values, width=6, color=[BAD if v < 0 else BLUE for v in r.fillna(0)], alpha=.85)
    ax.axhline(0, color=INK2, lw=.8)
    fl = pd.DatetimeIndex(wC.week_end[wC.c_flag.values]); al = pd.DatetimeIndex(wC.week_end[wC.c_alarm.values])   # gắn vào cuối tuần (nhân quả)
    ax.scatter(fl, [np.nanmax(r) + 2] * len(fl), s=20, color=AMB, marker="D", label="luật C: dấu quay đổi (cờ tuần)")
    ax.scatter(al, [np.nanmax(r) + 2] * len(al), s=40, color=BAD, marker="D", label="luật C: báo 'cần xem' (2 tuần liên tiếp)")
    ax.set_ylabel("quay pha 2001X (°/tuần)"); ax.legend(loc="upper left", frameon=False, fontsize=8.5, ncol=2)
    ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
    out = f"{ROOT}/Bao_cao/hinh-ba-tang-toan-chuoi.png"; fig.savefig(out, bbox_inches="tight", facecolor=BG); print("saved", out)


if __name__ == "__main__":
    main()
