#!/usr/bin/env python3
"""41_figure_seven_families_four_panels.py — Bốn khung so sánh bảy họ mô hình trên đoạn nền ổn định 9b (dạng ngang, theo thứ tự Bảng 3.5).

Khung 1: lead-time (ngày) tới 29/05 tại τ chung; PCA k = 8 gạch chéo = bị giới hạn bởi ngày sớm nhất có thể báo (25/03).
Khung 2: tỉ lệ báo giả lớn nhất giữa các khối (fold) với vạch tiêu chí 0,10.  Khung 3: tỉ số tách 16–30/04 (log).  Khung 4: số tham số (log).
Mô hình ngẫu nhiên (3 hạt giống): thanh = trung bình, chấm = từng hạt giống. Màu: xanh = mô hình chọn (locked_params_phase02),
xám = đạt tiêu chí, đỏ = không đạt (theo cờ pass của locked_params.json). Ra: Bao_cao/hinh-bay-ho-bon-khung.png
"""
import json, os, sys, re
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
OUT = f"{ROOT}/Bao_cao/hinh-bay-ho-bon-khung.png"
BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
GREY = "#4a4a5c"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": SF, "axes.edgecolor": "#26262f", "axes.labelcolor": INK2, "xtick.color": MUTE,
                     "ytick.color": INK, "text.color": INK, "font.family": "DejaVu Sans", "font.size": 9.5, "axes.grid": True, "grid.color": "#ffffff",
                     "grid.alpha": .06, "axes.spines.top": False, "axes.spines.right": False})
# Thứ tự hàng theo Bảng 3.5 (trên → dưới), nhãn hiển thị và tiền tố cấu hình trong ranking
ROWS = [("PCA k = 8", "PCA_k8"), ("SAE β = 10⁻³", "SAE_b0.001"), ("PCA k = 3", "PCA_k3"), ("PCA k = 2", "PCA_k2"), ("AE nhỏ 24-12-6", "AEsmall"),
        ("AE 24-28-12-6", "AE"), ("VAE z = 8", "VAE_z8"), ("ED-LSTM", "EDLSTM"), ("ED-CNN", "EDCNN"), ("DBN", "DBN"),
        ("PCA k = 4", "PCA_k4"), ("PCA k = 5", "PCA_k5"), ("PCA k = 6", "PCA_k6")]


def family_of(model):
    return re.sub(r"_s\d+$", "", model)


def main():
    lock = json.load(open(LOCK_FILE)); lock2 = json.load(open(f"{DATA_NEW}/locked_params_phase02.json")); chosen = lock2["model"]
    r = pd.DataFrame(lock["ranking"]); r["family"] = r.model.map(family_of)
    rows = []
    for lab, fam in ROWS:
        g = r[r.family == fam]
        rows.append({"label": lab, "family": fam, "n": len(g), "lead": g.lead_days.mean(), "lead_pts": g.lead_days.tolist(), "censored": bool(g.censored.any()),
                     "fa": g.fa_fold_max.max(), "fa_pts": g.fa_fold_max.tolist(), "sep": g["sep_ratio_16-30apr"].mean(), "sep_pts": g["sep_ratio_16-30apr"].tolist(),
                     "params": g.n_params.iloc[0], "passed": g["pass"].mean(), "n_pass": int(g["pass"].sum())})
    t = pd.DataFrame(rows); y = np.arange(len(t))[::-1]
    cols = [TEAL if family_of(chosen) == f else (GREY if p == 1 else BAD) for f, p in zip(t.family, t.passed)]
    print(t[["label", "n", "lead", "censored", "fa", "sep", "params", "n_pass"]].round(3).to_string())

    fig, axs = plt.subplots(1, 4, figsize=(18, 7.6), dpi=130, sharey=True, gridspec_kw={"wspace": .12, "width_ratios": [1.2, 1.05, 1, .9]})
    # --- 1. lead-time ---
    ax = axs[0]; ax.barh(y, t.lead, color=cols, height=.66, hatch=["///" if c else "" for c in t.censored], edgecolor=BG, lw=.6)
    for yi, pts, v, c in zip(y, t.lead_pts, t.lead, t.censored):
        if len(pts) > 1: ax.scatter(pts, [yi] * len(pts), s=14, color=INK, zorder=4, alpha=.8)
        ax.text(max(pts) + 1.5, yi, f"{v:.0f}" + (" · bị giới hạn (báo 25/03)" if c else ""), va="center", fontsize=8.5, color=INK2)
    ax.axvline(30, color=AMB, ls=":", lw=1, label="mốc thiết kế 30 ngày"); ax.set_xlim(0, 108)
    ax.set_title(f"① lead-time tới 29/05 (ngày)\nτ chung = {lock['tau_common']}, ≥ {lock['consecutive_days']} ngày liên tiếp", loc="left", fontsize=10, color=INK2)
    ax.legend(loc="lower right", frameon=False, fontsize=8.5)
    # --- 2. FA lớn nhất giữa các khối ---
    ax = axs[1]; ax.barh(y, t.fa, color=cols, height=.66, edgecolor=BG, lw=.6)
    for yi, pts in zip(y, t.fa_pts):
        if len(pts) > 1: ax.scatter(pts, [yi] * len(pts), s=14, color=INK, zorder=4, alpha=.8)
    for yi, v, n, npass in zip(y, t.fa, t.n, t.n_pass):
        ax.text(v + .025, yi, f"{v:.2f}" + (f" ({npass}/{n})" if n > 1 else ""), va="center", fontsize=8.5, color=INK2)
    ax.axvline(FA_FOLD_MAX_MAX, color=AMB, ls=":", lw=1, label=f"tiêu chí ≤ {FA_FOLD_MAX_MAX} · (x/3) = số hạt giống đạt"); ax.set_xlim(0, 1.3)
    ax.set_title("② tỉ lệ báo giả lớn nhất giữa 5 khối\n(mẫu 6 giờ, giới hạn từ 4 khối còn lại)", loc="left", fontsize=10, color=INK2); ax.legend(loc="lower right", frameon=False, fontsize=8.5)
    # --- 3. tỉ số tách (log) ---
    ax = axs[2]; ax.barh(y, t.sep, color=cols, height=.66, edgecolor=BG, lw=.6); ax.set_xscale("log")
    for yi, pts in zip(y, t.sep_pts):
        if len(pts) > 1: ax.scatter(pts, [yi] * len(pts), s=14, color=INK, zorder=4, alpha=.8)
    for yi, pts, v in zip(y, t.sep_pts, t.sep): ax.text(max(pts) * 1.2, yi, f"{v:.0f}", va="center", fontsize=8.5, color=INK2)
    ax.axvline(SEP_MIN, color=AMB, ls=":", lw=1, label=f"tiêu chí ≥ {SEP_MIN}"); ax.set_xlim(1, 4000)
    ax.set_title("③ tỉ số tách 16–30/04 (thang log)\nSPE trung vị đợt lệch / SPE trung vị nền", loc="left", fontsize=10, color=INK2); ax.legend(loc="lower right", frameon=False, fontsize=8.5)
    # --- 4. số tham số (log) ---
    ax = axs[3]; ax.barh(y, t.params, color=cols, height=.66, edgecolor=BG, lw=.6); ax.set_xscale("log")
    for yi, v in zip(y, t.params): ax.text(v * 1.15, yi, f"{v:,}".replace(",", "."), va="center", fontsize=8.5, color=INK2)
    ax.set_xlim(60, 30000); ax.set_title("④ số tham số (thang log)\n", loc="left", fontsize=10, color=INK2)
    axs[0].set_yticks(y); axs[0].set_yticklabels(t.label, fontsize=9.5)
    for ax in axs: ax.tick_params(axis="y", length=0); ax.grid(axis="y", visible=False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (TEAL, GREY, BAD)] + [plt.Rectangle((0, 0), 1, 1, facecolor=GREY, hatch="///", edgecolor=BG)]
    fig.legend(handles, [f"mô hình chọn ({chosen})", "đạt tiêu chí 1 (mọi hạt giống)", "không đạt tiêu chí 1 (ít nhất một hạt giống)", "lead-time bị giới hạn"],
               loc="upper left", bbox_to_anchor=(.005, .955), frameon=False, fontsize=9, ncol=4)
    fig.suptitle("Bảy họ mô hình trên đoạn nền ổn định 9b · năm khối ba vai · thanh = trung bình 3 hạt giống, chấm trắng = từng hạt giống · thứ tự theo Bảng 3.5",
                 x=.005, y=.995, ha="left", fontsize=12, fontweight="bold", color=INK)
    fig.subplots_adjust(top=.86)
    fig.savefig(OUT, bbox_inches="tight", facecolor=BG); print("saved", OUT)


if __name__ == "__main__":
    main()
