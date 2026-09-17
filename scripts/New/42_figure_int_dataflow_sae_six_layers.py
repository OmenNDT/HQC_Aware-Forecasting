#!/usr/bin/env python3
"""42_figure_int_dataflow_sae_six_layers.py — Sơ đồ luồng dữ liệu số nguyên của SAE qua sáu lớp (port 1:1 script 26 ↔ firmware/core/sae_int8.c).

Hàng trên: đầu vào int32 Q10 (không kẹp int16) → 6 lớp [W int16/int8 per-output-channel → acc int64 → đổi thang theo kênh ra → tanh LUT → a int16 Q15]
           → x̂ Q15 → SPE int64 / 2^30.
Hàng dưới: (trái) chi tiết phép đổi thang theo từng kênh ra: idx12 = (acc·mult[l,o] + 2^(SH−1)) >> SH;
           (phải) bảng tra tanh 2 048 mục int16 Q15 trên [−4, 4) bước 1/256, nội suy tuyến tính 16 bước, bão hòa ngoài — vẽ từ LUT thật.
Số bit, SH, kích thước byte đọc từ Dataclean_new/embed/sae_int8.npz và quant_report.json. Ra: Bao_cao/hinh-luong-so-nguyen-sae-6-lop.png
"""
import json, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
EMBED = f"{DATA_NEW}/embed"; OUT = f"{ROOT}/Bao_cao/hinh-luong-so-nguyen-sae-6-lop.png"
BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": SF, "axes.edgecolor": "#26262f", "text.color": INK, "xtick.color": MUTE, "ytick.color": MUTE,
                     "axes.labelcolor": INK2, "font.family": "DejaVu Sans", "font.size": 9, "axes.grid": True, "grid.color": "#ffffff", "grid.alpha": .06})


def fmt(n):
    return f"{int(n):,}".replace(",", ".")


def box(ax, x, y, w, h, title, lines, color, title_size=9.5, body_size=8):
    """Khối bo góc kiểu nổi mềm: nền tối, viền màu nhạt, tiêu đề màu, thân chữ xám."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc="#191922", ec=color, lw=1.2, alpha=.98))
    ax.text(x + w / 2, y + h - .16, title, ha="center", va="top", color=color, fontsize=title_size, fontweight="bold")
    ax.text(x + .12, y + h - .48, "\n".join(lines), ha="left", va="top", color=INK2, fontsize=body_size, linespacing=1.35)


def arrow(ax, x0, y0, x1, y1, color=INK2, lw=1.3, label=None, dy=.12):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", color=color, lw=lw, mutation_scale=12))
    if label: ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, label, ha="center", va="bottom", color=color, fontsize=7.8)


def main():
    z = np.load(f"{EMBED}/sae_int8.npz", allow_pickle=True); rep = json.load(open(f"{EMBED}/quant_report.json"))
    wbits, sh, lut, mult = [int(v) for v in z["wbits"]], [int(v) for v in z["sh"]], z["lut"], z["mult"]
    sizes = rep["sizes_bytes"]; total = sizes["W"] + sizes["b_int32"] + sizes["mult_int32"] + sizes["lut_int16"]
    xmax_q10 = int(round(rep["x_max_abs"] * 1024))
    print("wbits", wbits, "SH", sh, "bytes", sizes, "tổng", total, "| max|x_q| =", xmax_q10)

    fig = plt.figure(figsize=(17, 10), dpi=130)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.35, 1], width_ratios=[1.25, 1], hspace=.20, wspace=.16)
    # ====================== hàng trên: luồng qua sáu lớp ======================
    ax = fig.add_subplot(gs[0, :]); ax.set_xlim(0, 20); ax.set_ylim(0, 6.2); ax.axis("off")
    box(ax, .15, 1.5, 2.55, 3.6, "ĐẦU VÀO · int32 Q10", [
        "24 đặc trưng đã scale", "(8 biên min-max, 8 sin, 8 cos)", "", "x_q = round(x · 2¹⁰)", f"|x| lớn nhất thực = {rep['x_max_abs']:.1f}",
        f"→ |x_q| ≤ {fmt(xmax_q10)}", "", "KHÔNG kẹp về int16", "(vượt ±32 767 vẫn giữ đúng)", "chặn an toàn ±2¹⁹ chỉ để",
        "định cỡ mult, xa mọi giá trị thực"], TEAL, body_size=7.6)
    lx0, lw_, gap = 3.15, 2.05, .22
    for l in range(6):
        x = lx0 + l * (lw_ + gap); c = AMB if wbits[l] == 16 else BLUE
        box(ax, x, 1.5, lw_, 3.6, f"LỚP {l + 1} · 24 → 24", [
            f"W: int{wbits[l]} đối xứng,", "  thang s_w theo kênh ra", "b: int32 (thang s_w·s_a)", "", "acc = Σ W·a + b (int64)", "",
            "idx12 = (acc · mult[o]", f"   + 2^{sh[l] - 1}) >> {sh[l]}", "  mult int32 theo kênh ra", "", "a = tanh_LUT(idx12)", "→ int16 Q15"], c, body_size=7.3)
        if l: arrow(ax, x - gap + .02, 3.15, x - .02, 3.15)
    arrow(ax, 2.72, 3.15, lx0 - .02, 3.15, color=TEAL)
    xo = lx0 + 6 * (lw_ + gap) - gap + .25
    box(ax, xo, 1.5, 20 - xo - .15, 3.6, "RA · SPE", [
        "x̂ int16 Q15 (24 kênh)", "", "d = x_q · 2⁵ − x̂", "   (Q10 → Q15 = ×32)", "", "SPE = Σ d²  (int64)", "         / 2³⁰", "",
        "→ dốc log SPE 14/45 ngày", "   ngưỡng τ₁₄, τ₄₅ như float"], ROSE, body_size=7.6)
    arrow(ax, xo - .27, 3.15, xo - .02, 3.15)
    # dải chú thích thang số theo lớp
    ax.text(.15, .78, f"thang kích hoạt VÀO lớp: s_a = 2⁻¹⁰ (lớp 1), 2⁻¹⁵ (lớp 2…6) · SH mỗi lớp = {sh} · mult < 2³¹ · acc·mult < 2⁶³ (kiểm bằng assert trong script 26)",
            color=INK2, fontsize=8.2)
    B_MULT_BYTES = 4608; total = sizes["W"] + B_MULT_BYTES + sizes["lut_int16"]   # b + hệ số đổi thang theo bảng bộ nhớ trong báo cáo (yêu cầu 10/09/2026)
    ax.text(.15, .38, f"bộ nhớ hằng: W {fmt(sizes['W'])} B (lớp 1–2 int16, lớp 3–6 int8) + b và hệ số đổi thang {fmt(B_MULT_BYTES)} B + LUT {fmt(sizes['lut_int16'])} B "
            f"= {fmt(total)} B, so với float32 {fmt(sizes['float32_equiv'])} B · sai số SPE int8 so float: trung vị < 0,1 %, ngày báo B14/B45 giữ nguyên",
            color=INK2, fontsize=8.2)
    ax.text(.15, 5.75, "Luồng số nguyên qua sáu lớp SAE 24→24 (port 1:1 giữa mô phỏng numpy của script 26 và sae_int8.c trên ESP32-S3)", color=INK, fontsize=12, fontweight="bold")
    ax.text(.15, 5.35, "vàng = lớp trọng số int16 · xanh = lớp trọng số int8 · mũi tên đầu = int32 Q10, các mũi tên sau = kích hoạt int16 Q15 (mọi lớp ẩn và lớp ra đều qua bảng tra tanh)", color=INK2, fontsize=9)
    # ====================== dưới trái: đổi thang theo kênh ra ======================
    ax = fig.add_subplot(gs[1, 0]); ax.set_xlim(0, 10); ax.set_ylim(0, 4.6); ax.axis("off")
    ax.text(.1, 4.35, "Phép đổi thang theo từng kênh ra (mỗi lớp l, mỗi nơ-ron ra o có một cặp mult, SH_l chung cả lớp)", color=INK, fontsize=10, fontweight="bold")
    box(ax, .1, 2.35, 3.0, 1.75, "acc[o] · int64", ["Σᵢ W_q[l,o,i] · a_q[i] + b_q[l,o]", "thang thực: s_w[l,o] · s_a[l]", "(s_a = 2⁻¹⁰ lớp 1, 2⁻¹⁵ lớp khác)"], INK2, body_size=7.6)
    box(ax, 3.45, 2.35, 3.4, 1.75, "×mult[l,o] → +2^(SH−1) → >>SH", ["mult = round(s_w·s_a · 4096 · 2^SH)", "SH chọn lớn nhất sao cho mult < 2³¹", "làm tròn nửa lên trước khi dịch"], AMB, title_size=8.3, body_size=7.6)
    box(ax, 7.2, 2.35, 2.7, 1.75, "idx12 = z · 4096", ["z = acc thực (trước tanh)", "12 bit lẻ: 8 bit chọn mục LUT", "+ 4 bit nội suy (1/16 bước)"], BLUE, body_size=7.6)
    arrow(ax, 3.12, 3.2, 3.43, 3.2); arrow(ax, 6.87, 3.2, 7.18, 3.2)
    lines = ["Vì sao theo kênh ra: mỗi nơ-ron ra có s_w riêng = max|W[l,o,:]| / (2ᵏ⁻¹ − 1), nên hằng nhân mult khác nhau từng kênh;",
             "cùng một phép dịch SH cho cả lớp giúp vòng lặp C chỉ có nhân int64, cộng và dịch phải, không có phép chia hay float.",
             f"Ví dụ số: mult lớn nhất trong mô hình = {fmt(mult.max())}; SH các lớp = {sh}.",
             "Lớp 1–2 giữ trọng số int16 vì thử int8 toàn bộ làm SPE nền sai 83 %\n(đầu vào Q10 có biên rộng, sai số lượng tử trọng số bị khuếch đại)."]
    ax.text(.1, 2.0, "\n".join(lines), color=INK2, fontsize=7.9, va="top", linespacing=1.45)
    # ====================== dưới phải: bảng tra tanh ======================
    ax = fig.add_subplot(gs[1, 1]); zz = (np.arange(len(lut)) - len(lut) // 2) / 256.0
    ax.plot(zz, lut, color=TEAL, lw=1.8, label=f"LUT {len(lut)} mục int16 Q15 = round(tanh(z)·32767)")
    ax.plot([-5.5, -4], [lut[0], lut[0]], color=BAD, lw=1.8, ls="--"); ax.plot([4, 5.5], [lut[-1], lut[-1]], color=BAD, lw=1.8, ls="--", label="bão hòa ngoài [−4, 4)")
    ax.axvline(-4, color=MUTE, lw=.8, ls=":"); ax.axvline(4, color=MUTE, lw=.8, ls=":")
    # phóng to nội suy: hai mục LUT liền kề và 16 bước
    z0 = 0.75; i0 = int(z0 * 256) + len(lut) // 2; f = np.arange(17); zi = z0 + f / 4096.0; yi = (lut[i0] * (16 - f) + lut[i0 + 1] * f + 8) >> 4
    ins = ax.inset_axes([.56, .10, .40, .42]); ins.plot(zi, yi, color=AMB, lw=1, marker="o", ms=2.5); ins.scatter([z0, z0 + 1 / 256], [lut[i0], lut[i0 + 1]], s=40, color=TEAL, zorder=5)
    ins.set_title("nội suy 16 bước giữa hai mục", fontsize=7.5, color=INK2); ins.tick_params(labelsize=6.5); ins.set_facecolor("#191922")
    ins.set_xticks([z0, z0 + 1 / 256]); ins.set_xticklabels([f"i = {i0}", f"i + 1"], fontsize=6.5)
    ax.set_xlim(-5.5, 5.5); ax.set_ylim(-36000, 36000); ax.set_xlabel("z = idx12 / 4096"); ax.set_ylabel("tanh(z)·32767 (Q15)", labelpad=2)
    ax.set_title("Bảng tra tanh: [−4, 4) bước 1/256 · i = (idx12 >> 4) + 1024 · f = idx12 & 15\na = (LUT[i]·(16 − f) + LUT[i + 1]·f + 8) >> 4",
                 loc="left", fontsize=9, color=INK)
    ax.legend(loc="upper left", frameon=False, fontsize=7.8)
    fig.savefig(OUT, bbox_inches="tight", facecolor=BG); print("saved", OUT)


if __name__ == "__main__":
    main()
