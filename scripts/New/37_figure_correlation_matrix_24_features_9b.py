#!/usr/bin/env python3
"""37_figure_correlation_matrix_24_features_9b.py — Ma trận tương quan Pearson 24 × 24 của kho đặc trưng trên đoạn nền ổn định 9b.

Cột xếp theo ổ đỡ (2001 → 2003 → 2005 → 2007), trong mỗi ổ theo kênh X rồi Y, trong mỗi kênh amp / sin / cos,
để khối tương quan trong từng cặp X/Y hiện rõ. Khung đậm = ổ đỡ (6 × 6), khung mảnh = kênh (3 × 3).
Ra: Bao_cao/hinh-ma-tran-tuong-quan-24-nen-9b.png
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
OUT = f"{ROOT}/Bao_cao/hinh-ma-tran-tuong-quan-24-nen-9b.png"
BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": SF, "axes.edgecolor": "#26262f", "text.color": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "font.family": "DejaVu Sans", "font.size": 9})
BEARINGS = ["2001", "2003", "2005", "2007"]
FEATS = ["amp", "sin", "cos"]
ORDER = [f"{f}_{b}{d}" for b in BEARINGS for d in "XY" for f in FEATS]           # 24 cột, nhóm theo ổ → kênh → đặc trưng
CMAP = LinearSegmentedColormap.from_list("dark_div", [BLUE, "#1d1d27", BAD])     # âm = xanh, 0 = nền, dương = đỏ gạch


def main():
    fs = pd.read_parquet(FEATURE_STORE); tr = fs[(fs.role == "train") & (fs.cadence_min == 10)]
    C = tr[ORDER].corr().values; n = len(ORDER)
    print(f"nền 9b: {len(tr)} dòng 10 phút, {tr.index.min():%d/%m/%Y} → {tr.index.max():%d/%m/%Y}")
    for b in BEARINGS:   # tương quan amp X–Y, sin X–Y trong từng ổ (in để đối chiếu báo cáo)
        i = ORDER.index(f"amp_{b}X"); j = ORDER.index(f"amp_{b}Y"); k, l = ORDER.index(f"sin_{b}X"), ORDER.index(f"sin_{b}Y")
        print(f"  ổ {b}: r(amp X, amp Y) = {C[i, j]:+.2f}   r(sin X, sin Y) = {C[k, l]:+.2f}")
    fig, ax = plt.subplots(figsize=(11.5, 10.5), dpi=130)
    im = ax.imshow(C, cmap=CMAP, vmin=-1, vmax=1)
    for i in range(n):
        for j in range(n):
            v = C[i, j]
            if i != j and abs(v) >= .5:
                ax.text(j, i, f"{v:+.1f}".replace("+0.", "+.").replace("-0.", "−."), ha="center", va="center", fontsize=6.3, color=INK if abs(v) > .7 else INK2)
    for k in range(0, n, 3):   # khung kênh 3 × 3
        ax.add_patch(plt.Rectangle((k - .5, k - .5), 3, 3, fill=False, ec="#ffffff", lw=.6, alpha=.35))
    for k in range(0, n, 6):   # khung ổ đỡ 6 × 6
        ax.add_patch(plt.Rectangle((k - .5, k - .5), 6, 6, fill=False, ec=AMB, lw=1.8))
        ax.text(k + 2.5, -1.4, f"ổ {BEARINGS[k // 6]}", ha="center", va="bottom", color=AMB, fontsize=10.5, fontweight="bold")
        ax.text(-1.6, k + 2.5, f"ổ {BEARINGS[k // 6]}", ha="right", va="center", color=AMB, fontsize=10.5, fontweight="bold", rotation=90)
    lab = [f"{o.split('_')[1][-1]} {o.split('_')[0].replace('amp', 'biên')}" for o in ORDER]   # "X biên", "X sin", ... "Y cos"
    ax.set_xticks(range(n)); ax.set_yticks(range(n)); ax.set_xticklabels(lab, rotation=90, fontsize=7.5); ax.set_yticklabels(lab, fontsize=7.5)
    ax.tick_params(length=0); ax.set_xticks(np.arange(-.5, n, 1), minor=True); ax.set_yticks(np.arange(-.5, n, 1), minor=True)
    ax.grid(which="minor", color=BG, lw=.6); ax.grid(which="major", visible=False)
    for s in ax.spines.values(): s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=.035, pad=.02); cb.set_label("hệ số tương quan Pearson", color=INK2); cb.outline.set_visible(False)
    ax.set_title(f"Ma trận tương quan 24 × 24 kho đặc trưng 1X · đoạn nền ổn định 9b (20/02–22/03/2026, {len(tr)} dòng 10 phút)\n"
                 "khung vàng = ổ đỡ (biên/sin/cos của X rồi Y) · khung trắng = kênh · in số khi |r| ≥ 0,5",
                 loc="left", fontsize=11, pad=48, color=INK)
    fig.savefig(OUT, bbox_inches="tight", facecolor=BG); print("saved", OUT)


if __name__ == "__main__":
    main()
