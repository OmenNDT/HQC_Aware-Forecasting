#!/usr/bin/env python3
"""16_figures_model_comparison.py — Hình cho phase 01 (bản đầu: PCA).

Hình 1: SPE trung vị ngày (trục log) của mô hình chọn trên toàn chuỗi 9/2025–9/2026, tô vai trò
từng đoạn, giới hạn 99% ngoài mẫu, ngày báo theo tốc độ (τ chung), hai lần dừng.
Hình 2: bảng so sánh k của PCA: FA fold max, tỉ số tách, ngày báo đầu trên 9c.

Chạy: python scripts/New/16_figures_model_comparison.py --model PCA_k6 --tau 0.06
Ra : Bao_cao/hinh-tang-b-<model>-spe.png, Bao_cao/hinh-so-sanh-pca-k.png
"""
import argparse, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.dates as mdates

ROOT = "/home/sontn/Projects/HQC_Aware-Forecasting"
BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
ROLE_FILL = {"train": (TEAL, .30), "config_pos": (AMB, .16), "precheck_pos": (AMB, .28),
             "neg": (BAD, .14), "blind": (ROSE, .16), "report": ("#ffffff", .05)}
ROLE_LABEL = {"train": "nền 9b (train)", "config_pos": "9c chỉnh", "precheck_pos": "9c kiểm trước",
              "neg": "thử âm", "blind": "kiểm mù", "report": "chỉ báo cáo"}
STOPS = [("2026-01-05", "2026-01-13", "dừng 1"), ("2026-05-30", "2026-06-01", "dừng 2"), ("2026-06-12", "2026-06-13", "")]
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": SF, "axes.edgecolor": "#26262f", "axes.labelcolor": INK2,
                     "xtick.color": MUTE, "ytick.color": MUTE, "text.color": INK, "font.family": "DejaVu Sans",
                     "font.size": 10, "axes.grid": True, "grid.color": "#ffffff", "grid.alpha": .06,
                     "axes.spines.top": False, "axes.spines.right": False})


def alarm_days(slope_daily, tau, n=3):
    hit = (slope_daily > tau).astype(int).rolling(n).sum()
    return hit[hit >= n].index


def fig_spe(model, tau):
    d = pd.read_parquet(f"{ROOT}/Dataclean_new/spe/{model}.parquet")
    res = pd.read_csv(f"{ROOT}/Dataclean_new/cv_results.csv").set_index("model").loc[model]
    day = d.spe.resample("1D").median().dropna()
    fig, ax = plt.subplots(figsize=(15, 6.2), dpi=130)
    # dải vai trò theo đoạn liên tục
    for (ep, role), g in d.groupby(["episode", "role"]):
        c, a = ROLE_FILL[role]; ax.axvspan(g.index.min(), g.index.max(), color=c, alpha=a, lw=0)
    for a0, b0, lab in STOPS:
        ax.axvspan(pd.Timestamp(a0), pd.Timestamp(b0) + pd.Timedelta(days=1), color="#ffffff", alpha=.10, lw=0)
        if lab: ax.text(pd.Timestamp(a0), day.max() * .6, lab, fontsize=8.5, color=INK2, ha="center")
    ax.plot(day.index, day.values, color=TEAL, lw=1.8, label=f"SPE trung vị ngày · {model}")
    ax.axhline(res.limit99_6h, color=AMB, ls="--", lw=1.2, label=f"giới hạn 99% ngoài mẫu = {res.limit99_6h:.2f}")
    # ngày báo theo tốc độ
    for ep, g in d[d.role != "report"].groupby("episode"):
        s = g.slope14.resample("1D").first().dropna(); al = alarm_days(s, tau)
        if len(al): ax.scatter(al, day.reindex(al).values, s=26, color=BAD, zorder=5, label="_")
    ax.scatter([], [], s=26, color=BAD, label=f"ngày báo theo tốc độ (dốc log SPE 14 ngày > {tau}, ≥3 ngày)")
    ax.set_yscale("log"); ax.set_ylabel("SPE (thang log)")
    ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
    handles = [plt.Rectangle((0, 0), 1, 1, color=ROLE_FILL[r][0], alpha=max(ROLE_FILL[r][1] * 2, .3)) for r in ROLE_LABEL]
    leg1 = ax.legend(handles, list(ROLE_LABEL.values()), loc="upper left", frameon=False, fontsize=8.5, ncol=6, bbox_to_anchor=(0, 1.10))
    ax.add_artist(leg1); ax.legend(loc="lower right", frameon=False, fontsize=8.5)
    ax.set_title(f"Tầng B · {model} · nền gốc 9b · 9/2025 → 9/2026", loc="left", fontsize=13, fontweight="bold", pad=46)
    out = f"{ROOT}/Bao_cao/hinh-tang-b-{model}-spe.png"; fig.savefig(out, bbox_inches="tight", facecolor=BG); print("saved", out)


def fig_k_table():
    res = pd.read_csv(f"{ROOT}/Dataclean_new/cv_results.csv"); res = res[res.model.str.startswith("PCA")]
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2), dpi=130)
    k = res.model.str.extract(r"k(\d+)")[0].astype(int)
    for ax, col, lab in zip(axs, ["fa_fold_max", "sep_ratio_16-30apr", "n_params"],
                            ["FA lớn nhất giữa các fold", "tỉ số tách 16–30/04 (log)", "số tham số"]):
        cols = [TEAL if kk == 6 else "#4a4a5c" for kk in k]
        ax.bar(k.astype(str), res[col], color=cols); ax.set_title(lab, loc="left", fontsize=10.5, color=INK2)
        if "sep" in col: ax.set_yscale("log")
        for x, v in zip(k.astype(str), res[col]): ax.text(x, v, f"{v:.2f}" if v < 10 else f"{v:.0f}", ha="center", va="bottom", fontsize=8.5, color=INK2)
    fig.suptitle("PCA theo k · nền 9b · 5 fold ba vai · k = 6 tô xanh", x=.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    out = f"{ROOT}/Bao_cao/hinh-so-sanh-pca-k.png"; fig.savefig(out, bbox_inches="tight", facecolor=BG); print("saved", out)


def fig_all_models():
    """So sánh 7 họ mô hình sau khi khóa τ (đọc locked_params.json): lead-time, FA fold max, tỉ số tách, tham số.
    Mô hình ngẫu nhiên gộp theo họ: trung bình ± độ lệch trên các hạt giống."""
    import json, os
    lock_path = f"{ROOT}/Dataclean_new/locked_params.json"
    if not os.path.exists(lock_path):
        print("chưa có locked_params.json — bỏ qua hình 7 mô hình"); return
    lock = json.load(open(lock_path)); r = pd.DataFrame(lock["ranking"])
    r["family"] = r.model.str.replace(r"_s\d+$", "", regex=True)
    g = r.groupby("family").agg(lead=("lead_days", "mean"), lead_sd=("lead_days", "std"), fa=("fa_fold_max", "mean"),
                                sep=("sep_ratio_16-30apr", "mean"), params=("n_params", "first"), passed=("pass", "mean")).reset_index()
    g = g.sort_values("params")
    fig, axs = plt.subplots(1, 4, figsize=(17, 4.6), dpi=130)
    cols = [TEAL if lock["chosen_model"].startswith(f) else ("#4a4a5c" if p >= 1 else BAD) for f, p in zip(g.family, g.passed)]
    for ax, col, lab, err in zip(axs, ["lead", "fa", "sep", "params"],
                                 [f"lead-time (ngày) tới 29/05 · τ = {lock['tau_common']}", "FA lớn nhất giữa các fold", "tỉ số tách 16–30/04 (log)", "số tham số (log)"],
                                 ["lead_sd", None, None, None]):
        ax.bar(g.family, g[col].fillna(0), color=cols, yerr=g[err] if err else None, ecolor=INK2, capsize=3)
        ax.set_title(lab, loc="left", fontsize=10.5, color=INK2); ax.tick_params(axis="x", rotation=40, labelsize=8.5)
        if col in ("sep", "params"): ax.set_yscale("log")
        for x, v in zip(g.family, g[col].fillna(0)): ax.text(x, v, f"{v:.0f}" if v >= 10 else f"{v:.2f}", ha="center", va="bottom", fontsize=8, color=INK2)
    fig.suptitle(f"Bảy họ mô hình · nền 9b · 5 fold ba vai · xanh = mô hình chọn ({lock['chosen_model']}), đỏ = không đạt tiêu chí", x=.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    out = f"{ROOT}/Bao_cao/hinh-so-sanh-7-mo-hinh.png"; fig.savefig(out, bbox_inches="tight", facecolor=BG); print("saved", out)


if __name__ == "__main__":
    import json, os
    ap = argparse.ArgumentParser(); ap.add_argument("--model", default=None); ap.add_argument("--tau", type=float, default=None)
    a = ap.parse_args()
    lock_path = f"{ROOT}/Dataclean_new/locked_params.json"
    lock = json.load(open(lock_path)) if os.path.exists(lock_path) else {}
    model = a.model or lock.get("chosen_model", "PCA_k6"); tau = a.tau if a.tau is not None else lock.get("tau_common", 0.06)
    fig_spe(model, tau); fig_k_table(); fig_all_models()
