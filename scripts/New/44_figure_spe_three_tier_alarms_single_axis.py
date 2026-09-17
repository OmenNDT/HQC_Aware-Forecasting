#!/usr/bin/env python3
"""44_figure_spe_three_tier_alarms_single_axis.py — Một trục thời gian 9/2025 → 9/2026: log-SPE (SAE, trung vị ngày) và ba tầng cảnh báo.

Đánh dấu ngày báo đầu tiên của B₁₄ (06/04), B₄₅ (11/04), A (29/04) — đọc từ dữ liệu, không gõ tay; hai vạch dừng máy 04/01 và 29/05;
tô vùng kiểm mù từ 19/07 (đợt lệch chậm không tầng nào báo). Số liệu nạp bằng load_all() của script 38 (giống hình ba tầng).
Ra: Bao_cao/hinh-spe-ba-tang-mot-truc.png
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.dates as mdates

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from alarm_utils import load_script                                       # noqa: E402
s38 = load_script("s38", "38_figure_three_tiers_with_slope_lines.py", os.path.dirname(os.path.abspath(__file__)))
OUT = f"{ROOT}/Bao_cao/hinh-spe-ba-tang-mot-truc.png"
BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": SF, "axes.edgecolor": "#26262f", "axes.labelcolor": INK2, "xtick.color": MUTE,
                     "ytick.color": MUTE, "text.color": INK, "font.family": "DejaVu Sans", "font.size": 10, "axes.grid": True, "grid.color": "#ffffff",
                     "grid.alpha": .06, "axes.spines.top": False, "axes.spines.right": False})


def main():
    lock2, res, allb, s14, s45, b14, b45, lev, a_al, wC = s38.load_all(); model = lock2["model"]
    day = allb.spe.resample("1D").median().dropna(); limit = res.loc[model, "limit99_6h"]
    first = {"B14": b14.min(), "B45": b45.min(), "A": a_al.min()}; print("ngày báo đầu:", {k: f"{v:%d/%m/%Y}" for k, v in first.items()})
    stop1, stop2 = STOP1, STOP2.floor("1D"); print("dừng:", stop1.date(), stop2.date(), "| lead-time:", {k: (stop2 - v).days for k, v in first.items()})
    fig, ax = plt.subplots(figsize=(16, 6.4), dpi=130)
    ax.axvspan(pd.Timestamp("2026-02-20"), pd.Timestamp("2026-03-22"), color=TEAL, alpha=.16, lw=0)
    ax.axvspan(BLIND_CLIMB_FROM, day.index.max(), color=ROSE, alpha=.14, lw=0)
    ax.axvspan(pd.Timestamp("2026-06-14"), BLIND_CLIMB_FROM, color=ROSE, alpha=.05, lw=0)
    ax.plot(day.index, day.values, color=TEAL, lw=1.7, label=f"log-SPE {model} (trung vị ngày)")
    ax.axhline(limit, color=AMB, ls="--", lw=1.1, label=f"giới hạn 99 % ngoài mẫu = {limit:.2f}")
    ax.set_yscale("log"); ax.set_ylim(5e-3, 3e4); ax.set_ylabel("SPE (thang log)")
    # ngày báo đầu tiên của ba tầng
    marks = [("B14", BAD, "o", pd.Timestamp("2026-02-24"), 4.0, f"B₁₄ báo {first['B14']:%d/%m}\n({(stop2 - first['B14']).days} ngày trước dừng 2)"),
             ("B45", AMB, "s", pd.Timestamp("2026-05-12"), 0.05, f"B₄₅ báo {first['B45']:%d/%m}\n({(stop2 - first['B45']).days} ngày trước dừng 2)"),
             ("A", BLUE, "v", pd.Timestamp("2026-04-03"), 2500, f"A báo {first['A']:%d/%m} ({(stop2 - first['A']).days} ngày)\nDirect 2003 ngoại suy chạm 65 µm\ntrong < {TIERA_HORIZON_DAYS} ngày")]
    for key, c, m, tx, ty, lab in marks:
        t = first[key]; y = day.reindex([t], method="nearest").iloc[0]
        ax.scatter([t], [y], s=110, color=c, marker=m, zorder=6, edgecolor=BG, lw=1.2)
        ax.annotate(lab, (t, y), (tx, ty), color=c, fontsize=9.5, ha="center", va="center", arrowprops=dict(arrowstyle="-", color=c, lw=.9, alpha=.8, shrinkB=6))
    # hai lần dừng máy
    for t, lab, dx in [(stop1, f"dừng 1 · {stop1:%d/%m}\ntháo kiểm tra", 1), (stop2, f"dừng 2 · {stop2:%d/%m}\ntháo kiểm tra", -1)]:
        ax.axvline(t, color=INK, lw=1.3, ls="-", alpha=.7)
        ax.text(t + pd.Timedelta(days=3 * dx), 1.6e4, lab, color=INK, fontsize=9.5, ha="left" if dx > 0 else "right", va="top")
    ax.text(pd.Timestamp("2026-03-06"), 1.6e4, "đoạn nền ổn định 9b\n(huấn luyện)", color=TEAL, fontsize=9.5, ha="center", va="top")
    ax.text(pd.Timestamp("2026-06-17"), 1.6e4, f"kiểm mù đoạn 11 · đợt lệch chậm từ {BLIND_CLIMB_FROM:%d/%m} (hồng đậm)\nSPE tăng 1,6–2,4 lần, dốc tối đa 0,045 < τ₁₄ = {lock2['tau14']}\n→ không tầng nào báo tới 02/09",
            color=ROSE, fontsize=9.5, ha="left", va="top")
    ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y")); ax.set_xlim(day.index.min() - pd.Timedelta(days=5), day.index.max() + pd.Timedelta(days=5))
    h, l = ax.get_legend_handles_labels()
    h += [plt.Line2D([], [], marker="o", ls="", color=BAD, ms=8), plt.Line2D([], [], marker="s", ls="", color=AMB, ms=8), plt.Line2D([], [], marker="v", ls="", color=BLUE, ms=8)]
    l += ["B₁₄: dốc log-SPE 14 ngày > τ₁₄, 3 ngày liên tiếp", "B₄₅: dốc 45 ngày > τ₄₅, 5 ngày liên tiếp", "A: Direct ngoại suy chạm 65 µm"]
    ax.legend(h, l, loc="upper left", frameon=False, fontsize=9, ncol=1)
    ax.set_title("Sai số tái tạo SPE và ba tầng cảnh báo trên toàn chuỗi 9/2025 → 9/2026 · ngày báo đầu tiên của mỗi tầng · hai lần dừng máy · vùng kiểm mù (hồng)",
                 loc="left", fontsize=12, fontweight="bold", pad=10)
    fig.savefig(OUT, bbox_inches="tight", facecolor=BG); print("saved", OUT)


if __name__ == "__main__":
    main()
