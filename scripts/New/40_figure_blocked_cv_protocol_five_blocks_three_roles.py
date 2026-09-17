#!/usr/bin/env python3
"""40_figure_blocked_cv_protocol_five_blocks_three_roles.py — Sơ đồ giao thức kiểm định chéo "năm khối ba vai" trên đoạn nền ổn định 9b.

Trên: trục thời gian nền 9b (20/02–22/03/2026) chia năm khối bằng nhau theo thời gian (make_blocks của script 13),
      đệm 12 giờ hai bên mỗi ranh giới trong (bỏ khỏi mọi vai để cửa sổ/lọc trượt không vắt qua).
Dưới: năm vòng xoay: vòng i lấy khối i làm KIỂM (đo SPE ngoài mẫu), khối i−1 (vòng tròn) làm CHỈNH (dừng sớm / chọn epoch),
      ba khối còn lại làm HUẤN LUYỆN. Số dòng mỗi khối và mốc ngày lấy thẳng từ kho đặc trưng.
Ra: Bao_cao/hinh-giao-thuc-nam-khoi-ba-vai.png
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.dates as mdates
from matplotlib.patches import Rectangle, FancyArrowPatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from alarm_utils import load_script                                       # noqa: E402
cv13 = load_script("cv13", "13_blocked_cv_train_compare.py", os.path.dirname(os.path.abspath(__file__)))
OUT = f"{ROOT}/Bao_cao/hinh-giao-thuc-nam-khoi-ba-vai.png"
BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
ROLE = {"train": (TEAL, "huấn luyện"), "val": (AMB, "chỉnh (dừng sớm)"), "test": (BAD, "kiểm (SPE ngoài mẫu)")}
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": SF, "axes.edgecolor": "#26262f", "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "text.color": INK, "font.family": "DejaVu Sans", "font.size": 10, "axes.grid": False})


def block_edges(idx):
    """Mốc chia năm khối và vùng đệm, y hệt make_blocks (script 13)."""
    edges = pd.date_range(idx.min(), idx.max(), periods=N_BLOCKS + 1); blk, keep = cv13.make_blocks(idx)
    return edges, blk, keep


def main():
    fs = pd.read_parquet(FEATURE_STORE); tr = fs[(fs.role == "train") & (fs.cadence_min == 10)]
    edges, blk, keep = block_edges(tr.index); n_blk = [int(((blk == i) & keep).sum()) for i in range(N_BLOCKS)]
    print("mốc khối:", [f"{e:%d/%m %H:%M}" for e in edges]); print("dòng dùng được mỗi khối:", n_blk, "| bỏ vì đệm:", int((~keep).sum()))
    fig = plt.figure(figsize=(14, 8.4), dpi=130); gs = fig.add_gridspec(2, 1, height_ratios=[1.15, 2.6], hspace=.32)
    # ---------- trên: trục thời gian nền 9b ----------
    ax = fig.add_subplot(gs[0]); ax.set_xlim(edges[0] - pd.Timedelta(hours=18), edges[-1] + pd.Timedelta(hours=18)); ax.set_ylim(0, 1)
    for i in range(N_BLOCKS):
        a, b = edges[i], edges[i + 1]
        ax.add_patch(Rectangle((a, .30), b - a, .42, color=BLUE, alpha=.22 + .06 * (i % 2), lw=0))
        ax.text(a + (b - a) / 2, .51, f"khối {i + 1}\n{n_blk[i]} dòng", ha="center", va="center", color=INK, fontsize=10, fontweight="bold")
        ax.text(a, .20, f"{a:%d/%m}", ha="center", va="top", color=INK2, fontsize=9)
    ax.text(edges[-1], .20, f"{edges[-1]:%d/%m}", ha="center", va="top", color=INK2, fontsize=9)
    for e in edges[1:-1]:   # đệm 12 giờ hai bên ranh giới trong
        ax.add_patch(Rectangle((e - pd.Timedelta(hours=PURGE_H), .26), pd.Timedelta(hours=2 * PURGE_H), .50, color=BG, lw=0))
        ax.add_patch(Rectangle((e - pd.Timedelta(hours=PURGE_H), .26), pd.Timedelta(hours=2 * PURGE_H), .50, fill=False, ec=ROSE, lw=1.1, ls="--"))
        ax.plot([e, e], [.26, .76], color=ROSE, lw=.8)
    e1 = edges[2]; ax.annotate(f"đệm ±{PURGE_H} h quanh mỗi ranh giới trong (bỏ khỏi mọi vai, tổng {int((~keep).sum())} dòng)", (e1 + pd.Timedelta(hours=PURGE_H), .28),
                               (e1 + pd.Timedelta(hours=14), .04), color=ROSE, fontsize=9, va="center", ha="left", arrowprops=dict(arrowstyle="-", color=ROSE, lw=.8))
    ax.text(edges[0], 1.10, f"đoạn nền ổn định 9b · {tr.index.min():%d/%m/%Y} → {tr.index.max():%d/%m/%Y} · {len(tr)} dòng 10 phút · 5 khối bằng nhau theo thời gian (≈ {(edges[1] - edges[0]).days} ngày/khối)",
            ha="left", va="center", color=INK, fontsize=10.5)
    ax.set_yticks([]); ax.set_xticks([])
    ax.spines[["left", "right", "top", "bottom"]].set_visible(False)
    # ---------- dưới: năm vòng xoay vai trò ----------
    ax = fig.add_subplot(gs[1]); ax.set_xlim(-1.6, N_BLOCKS + 3.1); ax.set_ylim(-1.0, N_BLOCKS + .1); ax.axis("off")
    for f in range(N_BLOCKS):
        y = N_BLOCKS - 1 - f; te, va = f, (f - 1) % N_BLOCKS
        ax.text(-.15, y + .5, f"vòng {f + 1}", ha="right", va="center", color=INK, fontsize=10.5, fontweight="bold")
        for i in range(N_BLOCKS):
            role = "test" if i == te else ("val" if i == va else "train"); c, lab = ROLE[role]
            ax.add_patch(Rectangle((i + .06, y + .12), .88, .76, color=c, alpha=.92 if role != "train" else .55, lw=0))
            ax.text(i + .5, y + .5, "K" if role == "test" else ("C" if role == "val" else "H"), ha="center", va="center", color=BG if role != "train" else INK, fontsize=12, fontweight="bold")
            if i and i < N_BLOCKS: ax.plot([i, i], [y + .10, y + .90], color=BG, lw=3)   # khe đệm giữa các khối
        ax.text(N_BLOCKS + .25, y + .5, f"kiểm = khối {te + 1}, chỉnh = khối {va + 1}, huấn luyện = 3 khối còn lại → SPE ngoài mẫu cho khối {te + 1}",
                ha="left", va="center", color=INK2, fontsize=9)
    for i in range(N_BLOCKS): ax.text(i + .5, N_BLOCKS + .05, f"khối {i + 1}", ha="center", va="bottom", color=INK2, fontsize=9.5)
    # mũi tên xoay vai: vai chỉnh đi trước vai kiểm một khối, vòng tròn
    ax.add_patch(FancyArrowPatch((N_BLOCKS - .5, .05), (.6, -.30), connectionstyle="arc3,rad=-.08", arrowstyle="-|>", color=AMB, lw=1.2, mutation_scale=12))
    ax.text(N_BLOCKS / 2, -.72, "vai chỉnh luôn là khối liền trước khối kiểm (vòng 1 lấy khối 5); mỗi khối đúng một lần làm kiểm, một lần làm chỉnh",
            ha="center", va="top", color=AMB, fontsize=9)
    handles = [Rectangle((0, 0), 1, 1, color=ROLE[r][0], alpha=.92 if r != "train" else .55) for r in ("train", "val", "test")]
    ax.legend(handles, [f"H · {ROLE['train'][1]}", f"C · {ROLE['val'][1]}", f"K · {ROLE['test'][1]}"], loc="upper right", bbox_to_anchor=(1.0, 1.12), frameon=False, fontsize=9.5, ncol=3)
    fig.text(.06, .035, f"Sau 5 vòng: ghép SPE ngoài mẫu của 5 khối kiểm → mẫu 6 giờ → giới hạn 99%; FA từng vòng đo bằng giới hạn tính từ 4 vòng còn lại "
             f"(tiêu chí: trung bình ≤ {FA_FOLD_MEAN_MAX}, lớn nhất ≤ {FA_FOLD_MAX_MAX}). Mô hình cuối fit lại trên cả 9b với số epoch trung bình 5 vòng.",
             ha="left", va="bottom", color=INK2, fontsize=8.8)
    fig.suptitle("Quy trình năm khối ba vai (kiểm định chéo theo khối thời gian có đệm) trên đoạn nền ổn định 9b", x=.06, y=.975, ha="left", fontsize=13, fontweight="bold", color=INK)
    fig.savefig(OUT, bbox_inches="tight", facecolor=BG); print("saved", OUT)


if __name__ == "__main__":
    main()
