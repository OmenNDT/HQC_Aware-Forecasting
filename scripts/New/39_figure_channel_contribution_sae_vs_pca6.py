#!/usr/bin/env python3
"""39_figure_channel_contribution_sae_vs_pca6.py — Đóng góp của 8 kênh vào SPE trong đợt lệch 16–30/04/2026.

Hai khung song song: mô hình được chọn (SAE, theo locked_params_phase02) và PCA sáu thành phần, cùng dữ liệu 9c (role config_pos),
cùng công thức đóng góp r²amp + r²sin + r²cos của mỗi kênh chia tổng SPE (ReconstructionModel.contribution).
Cột = phần trăm đóng góp của tổng SPE cửa sổ; ghi thêm tổng theo ổ đỡ (X + Y). Ra: Bao_cao/hinh-dong-gop-kenh-sae-vs-pca6.png
"""
import json, os, pickle, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from models.reconstruction_base import to_matrix                          # noqa: E402
OUT = f"{ROOT}/Bao_cao/hinh-dong-gop-kenh-sae-vs-pca6.png"
CH = ["2001X", "2001Y", "2003X", "2003Y", "2005X", "2005Y", "2007X", "2007Y"]
BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
BEARING_COLOR = {"2001": BAD, "2003": AMB, "2005": BLUE, "2007": TEAL}
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": SF, "axes.edgecolor": "#26262f", "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": MUTE, "text.color": INK, "font.family": "DejaVu Sans", "font.size": 10, "axes.grid": True, "grid.color": "#ffffff",
                     "grid.alpha": .06, "axes.spines.top": False, "axes.spines.right": False})


def contribution_pct(tag, X):
    """% đóng góp từng kênh trên tổng SPE cửa sổ (tổng r² theo kênh / tổng r² toàn cửa sổ) và trung bình phần theo dòng."""
    obj = pickle.load(open(f"{MODEL_DIR}/{tag}.pkl", "rb")); m, sc = obj["model"], obj["scaler"]
    Z = sc.transform(X); r2 = m.residual(Z) ** 2; per = r2[:, 0:8] + r2[:, 8:16] + r2[:, 16:24]
    per = per[~np.isnan(per).any(axis=1)]
    share_sum = per.sum(0) / per.sum(); share_row = m.contribution(Z); share_row = np.nanmean(share_row, axis=0)
    return 100 * share_sum, 100 * share_row, float(np.nansum(per, axis=1).mean())


def draw(ax, pct, tag, spe_mean, ylabel=True):
    cols = [BEARING_COLOR[c[:4]] for c in CH]; bars = ax.bar(range(8), pct, color=cols, alpha=.9, lw=0, width=.72)
    for b, v in zip(bars, pct): ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.1f}%", ha="center", va="bottom", fontsize=9, color=INK)
    for i in range(0, 8, 2):   # tổng theo ổ đỡ
        tot = pct[i] + pct[i + 1]; ax.text(i + .5, 96, f"ổ {CH[i][:4]}\n{tot:.0f}%", ha="center", va="top", fontsize=9.5, color=cols[i], fontweight="bold")
        if i: ax.axvline(i - .5, color="#ffffff", alpha=.12, lw=.8)
    ax.set_xticks(range(8)); ax.set_xticklabels(CH); ax.set_ylim(0, 100)
    if ylabel: ax.set_ylabel("% đóng góp vào SPE (trung bình theo dòng, 16–30/04)")
    ax.set_title(f"{tag} · SPE trung bình cửa sổ {spe_mean:.1f}", loc="left", fontsize=11, color=INK)


def main():
    lock2 = json.load(open(f"{DATA_NEW}/locked_params_phase02.json")); chosen = lock2["model"]
    fs = pd.read_parquet(FEATURE_STORE); w = fs[(fs.cadence_min == 10) & (fs.role == "config_pos")].loc[SEP_WINDOW[0]:SEP_WINDOW[1]]
    X = to_matrix(w); print(f"cửa sổ {SEP_WINDOW[0]:%d/%m} → {SEP_WINDOW[1]:%d/%m/%Y}: {len(w)} dòng 10 phút")
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.6), dpi=130, sharey=True, gridspec_kw={"wspace": .08})
    for i, (ax, tag) in enumerate(zip(axs, [chosen, "PCA_k6"])):
        p_sum, p_row, spe_mean = contribution_pct(tag, X); draw(ax, p_row, tag, spe_mean, ylabel=(i == 0))   # vẽ theo trung bình phần theo dòng (= contribution(), số 97% / 60% trong báo cáo)
        print(f"{tag}: theo tổng r² " + " ".join(f"{c}={v:.1f}" for c, v in zip(CH, p_sum)) + f" | ổ 2001 = {p_sum[0] + p_sum[1]:.1f}%")
        print(f"{tag}: trung bình phần theo dòng ổ 2001 = {p_row[0] + p_row[1]:.1f}%")
    fig.suptitle("Đóng góp của 8 kênh vào sai số tái tạo trong đợt lệch 16–30/04/2026 (9c) · trái: mô hình chọn · phải: PCA k = 6\n"
                 "màu theo ổ đỡ; đóng góp kênh = r²biên + r²sin + r²cos, tính trên cùng kho đặc trưng và cùng nền 9b",
                 x=.01, y=1.04, ha="left", fontsize=11.5, color=INK)
    fig.savefig(OUT, bbox_inches="tight", facecolor=BG); print("saved", OUT)


if __name__ == "__main__":
    main()
