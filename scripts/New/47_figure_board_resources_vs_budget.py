#!/usr/bin/env python3
"""47_figure_board_resources_vs_budget.py — Tài nguyên trên bo ESP32-S3 dạng thanh ngang so với ngân sách (Bảng 3.7 + embed_measurements.json).

Bốn thanh: flash app (ảnh firmware 294 KB / phân vùng 1 MB), hằng số mô hình (đọc từ STAT trên bo / 1 MB), RAM tĩnh + trạng thái ba tầng
(8,3 KB / 334 KB DIRAM; toàn firmware 68 KB), thời gian suy luận mỗi mẫu (trung bình và lớn nhất, đọc từ STAT / ngân sách 1 s của thiết kế,
vẽ thang log vì cách nhau ba bậc). Ra: Bao_cao/hinh-tai-nguyen-tren-bo.png
"""
import json, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
EMBED = f"{DATA_NEW}/embed"; OUT = f"{ROOT}/Bao_cao/hinh-tai-nguyen-tren-bo.png"
BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": SF, "axes.edgecolor": "#26262f", "axes.labelcolor": INK2, "xtick.color": MUTE,
                     "ytick.color": INK, "text.color": INK, "font.family": "DejaVu Sans", "font.size": 10, "axes.grid": True, "grid.color": "#ffffff",
                     "grid.alpha": .06, "axes.spines.top": False, "axes.spines.right": False})
# Số đo bo (Bảng 3.7, đo 06/09/2026) — những gì có trong STAT thì đọc từ file
FLASH_APP_KB, FLASH_PART_KB = 294, 1024
RAM_TIERS_KB, RAM_FW_KB, RAM_DIRAM_KB = 8.3, 68, 334
BUDGET_US = 1_000_000                                                       # chỉ tiêu thiết kế: < 1 s mỗi mẫu 10 phút (Bảng 3.4)


def hbar(ax, y, used, total, color, label_used, label_total, log=False):
    ax.barh(y, total, height=.5, color="#26262f", lw=0)
    ax.barh(y, used, height=.5, color=color, lw=0)
    ax.text(total * (1.02 if not log else 1.15), y, label_total, va="center", ha="left", fontsize=9, color=INK2)
    ax.text(used * (1.03 if not log else 1.25) if (used / total > .0 and used > 0) else 0, y, label_used, va="center", ha="left", fontsize=9.5, color=INK, fontweight="bold")


def main():
    m = json.load(open(f"{EMBED}/embed_measurements.json")); st = m["final_stat"]
    us_mean, us_max, weights_b, engine_b, heap = st["infer_us_mean"], st["infer_us_max"], st["weights_bytes"], st["engine_bytes"], st["heap_free"]
    print(f"STAT bo: {us_mean:.0f} µs TB, {us_max} µs max, hằng số {weights_b} B, trạng thái {engine_b} B, heap trống {heap / 1000:.0f} KB")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.2), dpi=130, gridspec_kw={"width_ratios": [1.25, 1], "wspace": .30})
    # ---- trái: bộ nhớ (%) ----
    rows = [("Flash · ảnh firmware / phân vùng app", FLASH_APP_KB, FLASH_PART_KB, BLUE, f"{FLASH_APP_KB} KB ({100 * FLASH_APP_KB / FLASH_PART_KB:.0f} %)", f"{FLASH_PART_KB // 1024} MB phân vùng"),
            ("Flash · hằng số mô hình SAE (W, b, mult, LUT)", weights_b / 1024, FLASH_PART_KB, AMB, f"{weights_b / 1024:.1f} KB ({100 * weights_b / 1024 / FLASH_PART_KB:.1f} %)", "trong ảnh firmware"),
            ("RAM · toàn firmware / DIRAM", RAM_FW_KB, RAM_DIRAM_KB, BLUE, f"{RAM_FW_KB} KB ({100 * RAM_FW_KB / RAM_DIRAM_KB:.0f} %)", f"{RAM_DIRAM_KB} KB DIRAM"),
            ("RAM · trạng thái ba tầng (đệm 45 ngày SPE, 90 ngày Direct, 12 tuần pha)", engine_b / 1024, RAM_DIRAM_KB, AMB, f"{engine_b / 1024:.1f} KB ({100 * engine_b / 1024 / RAM_DIRAM_KB:.1f} %)", f"heap còn trống {heap / 1000:.0f} KB")]
    ys = np.arange(len(rows))[::-1]
    for y, (lab, used, total, c, lu, lt) in zip(ys, rows):
        ax1.barh(y, 100, height=.52, color="#26262f", lw=0); ax1.barh(y, 100 * used / total, height=.52, color=c, lw=0)
        ax1.text(max(100 * used / total, 0) + 1.2, y, lu, va="center", ha="left", fontsize=9.5, color=INK, fontweight="bold")
        ax1.text(99, y - .36, lt, va="center", ha="right", fontsize=8.3, color=INK2)
    ax1.set_yticks(ys); ax1.set_yticklabels([r[0] for r in rows], fontsize=9); ax1.set_xlim(0, 100); ax1.set_xlabel("% ngân sách"); ax1.tick_params(axis="y", length=0); ax1.grid(axis="y", visible=False)
    ax1.set_title("Bộ nhớ trên bo ESP32-S3 DevKitC (đo 06/09/2026)\n", loc="left", fontsize=11, color=INK)
    # ---- phải: thời gian suy luận (log) ----
    rows2 = [("ngân sách thiết kế\n< 1 s mỗi mẫu 10 phút", BUDGET_US, "#26262f", "1 000 000 µs"), ("lớn nhất trên 42.064 mẫu", us_max, ROSE, f"{us_max:,} µs".replace(",", ".")),
             ("trung bình (bo 1)", us_mean, TEAL, f"{us_mean:.0f} µs"), ("trung bình (bo 2, cùng firmware)", 656, TEAL, "656 µs")]
    ys2 = np.arange(len(rows2))[::-1]
    for y, (lab, v, c, txt) in zip(ys2, rows2):
        ax2.barh(y, v, height=.52, color=c, lw=0); ax2.text(v * 1.2, y, txt, va="center", ha="left", fontsize=9.5, color=INK, fontweight="bold")
    ax2.set_xscale("log"); ax2.set_xlim(100, 2e7); ax2.set_yticks(ys2); ax2.set_yticklabels([r[0] for r in rows2], fontsize=9); ax2.tick_params(axis="y", length=0); ax2.grid(axis="y", visible=False)
    ax2.axvline(BUDGET_US, color=AMB, ls=":", lw=1.2); ax2.set_xlabel("µs mỗi mẫu 10 phút (thang log)")
    ax2.set_ylim(-1.0, 3.6); ax2.text(BUDGET_US * .9, -.75, f"nhanh hơn ngân sách {BUDGET_US / us_mean:,.0f} lần (trung bình), {BUDGET_US / us_max:,.0f} lần (lớn nhất)".replace(",", "."), ha="right", va="center", fontsize=9, color=AMB)
    ax2.set_title("Thời gian mỗi mẫu so với ngân sách\n(gồm đọc dòng, phân tích 24 số, suy luận SAE, luật ba tầng)", loc="left", fontsize=11, color=INK)
    fig.suptitle("Tài nguyên trên bo: flash, RAM và thời gian suy luận so với ngân sách · firmware ESP-IDF v5.3.2, phát lại 42.064 mẫu qua USB trong 106 s",
                 x=.01, y=.98, ha="left", fontsize=12, fontweight="bold", color=INK)
    fig.subplots_adjust(top=.78)
    fig.savefig(OUT, bbox_inches="tight", facecolor=BG); print("saved", OUT)


if __name__ == "__main__":
    main()
