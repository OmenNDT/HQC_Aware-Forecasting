#!/usr/bin/env python3
"""46_figure_contribution_int_vs_float_on_board.py — Đóng góp 8 kênh vào SPE trong đợt lệch 16–30/04/2026: bản số nguyên (trên bo) so bản Python (float).

Bản float: mô hình SAE đã khóa (pkl), contribution() = (r²biên + r²sin + r²cos) / SPE từng dòng, trung bình theo dòng (như hình 39).
Bản số nguyên: cùng dữ liệu, chạy forward_int của script 26 với trọng số/LUT trong embed/sae_int8.npz (đúng bảng hằng nạp lên ESP32-S3),
phần dư d = x_q·2⁵ − x̂ (Q15) → r² theo kênh → cùng công thức. Cột đôi từng kênh, ghi tổng theo ổ đỡ và chênh lệch lớn nhất.
Ra: Bao_cao/hinh-dong-gop-kenh-int-vs-float.png
"""
import json, os, pickle, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from models.reconstruction_base import to_matrix                          # noqa: E402
from alarm_utils import load_script                                       # noqa: E402
q26 = load_script("q26", "26_quantize_sae_int8.py", os.path.dirname(os.path.abspath(__file__)))
EMBED = f"{DATA_NEW}/embed"; OUT = f"{ROOT}/Bao_cao/hinh-dong-gop-kenh-int-vs-float.png"
CH = ["2001X", "2001Y", "2003X", "2003Y", "2005X", "2005Y", "2007X", "2007Y"]
BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": SF, "axes.edgecolor": "#26262f", "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": MUTE, "text.color": INK, "font.family": "DejaVu Sans", "font.size": 10, "axes.grid": True, "grid.color": "#ffffff",
                     "grid.alpha": .06, "axes.spines.top": False, "axes.spines.right": False})


def share_from_residual(r):
    """(n, 24) phần dư → % đóng góp từng kênh, trung bình theo dòng (cùng định nghĩa ReconstructionModel.contribution)."""
    r2 = r ** 2; per = r2[:, 0:8] + r2[:, 8:16] + r2[:, 16:24]; tot = per.sum(1, keepdims=True); tot[tot == 0] = 1
    return 100 * (per / tot).mean(0)


def forward_int_residual(Xq, Wq, bq, mult, sh, lut):
    """Chạy lại forward_int của script 26 nhưng trả phần dư Q15 theo kênh (không chỉ SPE)."""
    xhat, _ = q26.forward_int(Xq, Wq, bq, mult, sh, lut)
    return (Xq.astype(np.int64) * (1 << (15 - q26.X_Q)) - xhat.astype(np.int64)).astype(float)


def main():
    lock2 = json.load(open(f"{DATA_NEW}/locked_params_phase02.json")); model = lock2["model"]
    z = np.load(f"{EMBED}/sae_int8.npz", allow_pickle=True); zf = np.load(f"{EMBED}/sae_float.npz", allow_pickle=True)
    fs = pd.read_parquet(FEATURE_STORE); w = fs[(fs.cadence_min == 10) & (fs.role == "config_pos")].loc[SEP_WINDOW[0]:SEP_WINDOW[1]]
    X = to_matrix(w)
    # float: mô hình đã khóa + scaler của nó
    obj = pickle.load(open(f"{MODEL_DIR}/{model}.pkl", "rb")); Zf = obj["scaler"].transform(X); r_f = obj["model"].residual(Zf); p_f = share_from_residual(r_f)
    # số nguyên: cùng scale như script 26 (amp min-max theo scaler_a/b, sin/cos giữ nguyên) → Q10 → forward_int
    Xs = X.copy(); Xs[:, :8] = (Xs[:, :8] - zf["scaler_a"]) / zf["scaler_b"]
    Xq = np.clip(np.round(Xs * 2 ** q26.X_Q), -q26.X_MAX, q26.X_MAX).astype(np.int64)
    r_i = forward_int_residual(Xq, z["Wq"], z["bq"], z["mult"], z["sh"], z["lut"]); p_i = share_from_residual(r_i)
    d = p_i - p_f; print(f"cửa sổ {SEP_WINDOW[0]:%d/%m}–{SEP_WINDOW[1]:%d/%m/%Y}: {len(w)} dòng")
    for c, a, b in zip(CH, p_f, p_i): print(f"  {c}: float {a:5.2f} %  int {b:5.2f} %  Δ {b - a:+.2f}")
    print(f"ổ 2001: float {p_f[0] + p_f[1]:.1f} %, int {p_i[0] + p_i[1]:.1f} % | |Δ| lớn nhất theo kênh {np.abs(d).max():.2f} điểm %")

    fig, ax = plt.subplots(figsize=(13.5, 6.2), dpi=130); x = np.arange(8); bw = .36
    b1 = ax.bar(x - bw / 2, p_f, bw, color=TEAL, alpha=.9, label="bản Python · float32 (mô hình đã khóa)")
    b2 = ax.bar(x + bw / 2, p_i, bw, color=AMB, alpha=.9, label="bản trên bo · số nguyên int16/int8 + LUT (cùng bảng hằng nạp ESP32-S3)")
    for bars, vals, c in [(b1, p_f, TEAL), (b2, p_i, AMB)]:
        for b, v in zip(bars, vals): ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.1f}", ha="center", va="bottom", fontsize=8.5, color=c)
    for i in range(0, 8, 2):
        ax.text(i + .5, 90, f"ổ {CH[i][:4]}\nfloat {p_f[i] + p_f[i + 1]:.1f} % · int {p_i[i] + p_i[i + 1]:.1f} %", ha="center", va="top", fontsize=9, color=INK,
                bbox=dict(boxstyle="round,pad=.3", fc="#191922", ec=BAD if i == 0 else "#2a2a36", lw=1))
        if i: ax.axvline(i - .5, color="#ffffff", alpha=.12, lw=.8)
    ax.set_xticks(x); ax.set_xticklabels(CH); ax.set_ylim(0, 100); ax.set_ylabel("% đóng góp vào SPE (trung bình theo dòng, 16–30/04/2026)")
    ax.legend(loc="upper right", bbox_to_anchor=(1, .80), frameon=False, fontsize=9.5)
    ax.text(.985, .56, f"chênh lệch lớn nhất theo kênh: {np.abs(d).max():.2f} điểm %\nổ 2001 giữ {p_i[0] + p_i[1]:.0f} % sau nén\n{len(w)} dòng 10 phút, cùng đầu vào",
            transform=ax.transAxes, ha="right", va="top", fontsize=9.5, color=INK2)
    ax.set_title("Đóng góp kênh trong đợt lệch 16–30/04/2026: bản số nguyên trên bo so với bản Python · con số 97 % đúng ổ 2001 giữ nguyên sau nén",
                 loc="left", fontsize=11.5, fontweight="bold", pad=10)
    fig.savefig(OUT, bbox_inches="tight", facecolor=BG); print("saved", OUT)


if __name__ == "__main__":
    main()
