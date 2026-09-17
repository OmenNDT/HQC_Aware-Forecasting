#!/usr/bin/env python3
"""43_figure_raw_waveform_spectrum_2001x_2003x.py — Phổ tần của 2001AX và 2003AX tính từ dạng sóng thô (Dataraw/sep-ware-29VT-200{1,3}.csv).

Bản ghi dùng: 25/07/2026 13:40:10, 4 762 vòng/phút, "Disp Wf(256X/8revs)": 256 mẫu/vòng × 8 vòng = 2 048 điểm, lấy mẫu đồng bộ theo vòng quay
→ phổ tính theo bậc (order): vạch k ↔ k/8 bậc, thành phần 1X rơi đúng vạch k = 8, không rò rỉ, không cần cửa sổ.
Tỉ lệ năng lượng 1X = |X[8]|² / Σ_{k≥1} |X[k]|² (bỏ thành phần DC). Trái: dạng sóng 8 vòng (µm); phải: phổ biên độ 0–10 bậc, đánh dấu 1X, 2X, 3X.
Ra: Bao_cao/hinh-pho-tan-2001x-2003x-dang-song-tho.png
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
OUT = f"{ROOT}/Bao_cao/hinh-pho-tan-2001x-2003x-dang-song-tho.png"
FILES = {"2001AX": f"{ROOT}/Dataraw/sep-ware-29VT-2001.csv", "2003AX": f"{ROOT}/Dataraw/sep-ware-29VT-2003.csv"}
BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": SF, "axes.edgecolor": "#26262f", "axes.labelcolor": INK2, "xtick.color": MUTE,
                     "ytick.color": MUTE, "text.color": INK, "font.family": "DejaVu Sans", "font.size": 9.5, "axes.grid": True, "grid.color": "#ffffff",
                     "grid.alpha": .06, "axes.spines.top": False, "axes.spines.right": False})


def read_first_record(path):
    """Đọc bản ghi đầu tiên (2001AX / 2003AX, 256X/8revs): header dict + t (ms) + y (µm)."""
    lines = open(path, encoding="utf-8-sig").read().splitlines()
    hdr = {l.split(",")[0]: ",".join(l.split(",")[1:]).strip() for l in lines[:10]}
    t, y = [], []
    for l in lines[11:]:
        if l.startswith("Machine Name"): break
        p = l.split(",")
        if len(p) == 2 and p[0] and p[1]: t.append(float(p[0])); y.append(float(p[1]))
    return hdr, np.array(t), np.array(y)


def order_spectrum(y, revs):
    """Phổ biên độ đơn biên theo bậc: y đã trừ trung bình, N mẫu đồng bộ; trả (bậc, biên độ đỉnh µm, năng lượng từng vạch)."""
    n = len(y); X = np.fft.rfft(y - y.mean()); amp = 2 * np.abs(X) / n; amp[0] = 0
    orders = np.arange(len(X)) / revs; energy = np.abs(X) ** 2; energy[0] = 0
    return orders, amp, energy


def main():
    fig, axs = plt.subplots(2, 2, figsize=(16, 8.4), dpi=130, gridspec_kw={"width_ratios": [1, 1.6], "hspace": .45, "wspace": .16})
    for row, (ch, path) in enumerate(FILES.items()):
        hdr, t, y = read_first_record(path); revs = int(hdr["Number of Revs"]); rpm = float(hdr["Sample Speed"].replace("rpm", ""))
        n = len(y); spr = n // revs; fs = spr * rpm / 60; f1 = rpm / 60
        orders, amp, energy = order_spectrum(y, revs); k1 = revs
        share1 = energy[k1] / energy.sum(); share_1to3 = energy[[k1, 2 * k1, 3 * k1]].sum() / energy.sum()
        pp = y.max() - y.min(); rank = np.argsort(energy)[::-1][:4]
        print(f"{ch}: {hdr['Timestamp']} · {rpm:.0f} rpm · {n} mẫu = {spr}/vòng × {revs} vòng · fs = {fs:,.0f} Hz · 1X = {f1:.1f} Hz")
        print(f"   p-p thô {pp:.1f} µm (Wf Amp ghi {hdr['Wf Amp']}) · 1X đỉnh {amp[k1]:.2f} µm (p-p {2 * amp[k1]:.1f}) · năng lượng 1X {100 * share1:.1f} % · 1X+2X+3X {100 * share_1to3:.1f} %")
        print("   4 vạch mạnh nhất (bậc, %):", [(round(orders[k], 3), round(100 * energy[k] / energy.sum(), 2)) for k in rank])
        col = TEAL if ch == "2001AX" else AMB
        # --- trái: dạng sóng ---
        ax = axs[row, 0]; ax.plot(t, y, color=col, lw=1.0)
        for r in range(1, revs): ax.axvline(t[r * spr], color=MUTE, lw=.6, ls=":")
        ax.set_xlim(t[0], t[-1]); ax.set_xlabel("thời gian (ms) · vạch chấm = mốc mỗi vòng quay"); ax.set_ylabel("dịch chuyển (µm)")
        ts = pd.Timestamp(hdr["Timestamp"]).strftime("%d/%m/%Y %H:%M")
        ax.set_title(f"{ch} · dạng sóng thô {n} điểm = {spr} mẫu/vòng × {revs} vòng\n{ts} · {rpm:.0f} vòng/phút · fs ≈ {fs / 1000:.1f} kHz · p-p = {pp:.1f} µm",
                     loc="left", fontsize=9.5, color=INK)
        # --- phải: phổ theo bậc ---
        ax = axs[row, 1]; m = orders <= 10.05
        ax.vlines(orders[m], 0, amp[m], color=col, lw=1.6, alpha=.9); ax.scatter(orders[m], amp[m], s=8, color=col)
        ymax = amp[m].max() * 1.32; ax.set_ylim(0, ymax); ax.set_xlim(0, 10.05)
        for q, lab in [(1, "1X"), (2, "2X"), (3, "3X")]:
            k = q * k1; ax.axvline(q, color=BAD if q == 1 else MUTE, lw=.9, ls="--", alpha=.8)
            ax.text(q, amp[k] + ymax * .03, f"{lab}\n{amp[k]:.1f} µm\n{100 * energy[k] / energy.sum():.1f} %", ha="center", va="bottom", fontsize=8.5,
                    color=BAD if q == 1 else INK2, fontweight="bold" if q == 1 else "normal")
        ax.text(.98, .95, f"thành phần 1X = {f1:.1f} Hz (vạch k = {k1} của {n} điểm)\nnăng lượng 1X / tổng năng lượng xoay chiều = {100 * share1:.1f} %\n1X + 2X + 3X = {100 * share_1to3:.1f} %",
                transform=ax.transAxes, ha="right", va="top", fontsize=9, color=INK, bbox=dict(boxstyle="round,pad=.4", fc="#191922", ec=col, lw=1))
        ax.set_xlabel("bậc (× tần số quay) · phổ đơn biên, biên độ đỉnh"); ax.set_ylabel("biên độ (µm)")
        ax.set_title(f"{ch} · phổ biên độ theo bậc 0–10\nlấy mẫu đồng bộ 256X nên 1X rơi đúng vạch, không cần cửa sổ, không rò rỉ", loc="left", fontsize=9.5, color=INK)
    fig.suptitle("Phổ tần từ dạng sóng thô: ổ 2001 và 2003 hướng X, cùng thời điểm đo · 1X trội tuyệt đối, xác nhận độc lập cho đặc trưng 1X biên độ + pha của mô hình",
                 x=.01, y=.995, ha="left", fontsize=12, fontweight="bold", color=INK)
    fig.savefig(OUT, bbox_inches="tight", facecolor=BG); print("saved", OUT)


if __name__ == "__main__":
    main()
