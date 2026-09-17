#!/usr/bin/env python3
"""48_figure_three_tier_logic_diagram.py — Sơ đồ logic ba tầng A / B / C chạy song song: đầu vào → cách tính → luật → cờ báo.

Ba hàng, mỗi hàng một tầng, cùng bốn cột (đầu vào · cách tính · quy tắc báo · cờ). Tham số đọc từ phase01_config, locked_params_phase02
(τ₁₄, τ₄₅, số ngày liên tiếp, luật C) để chữ trên hình luôn khớp mã. Nội dung theo Bảng 2.4 của báo cáo. Ra: Bao_cao/hinh-logic-ba-tang.png
"""
import json, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
OUT = f"{ROOT}/Bao_cao/hinh-logic-ba-tang.png"
BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
plt.rcParams.update({"figure.facecolor": BG, "text.color": INK, "font.family": "DejaVu Sans", "font.size": 9})


def box(ax, x, y, w, h, title, lines, color, tsize=10, bsize=8.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc="#191922", ec=color, lw=1.3))
    ax.text(x + w / 2, y + h - .17, title, ha="center", va="top", color=color, fontsize=tsize, fontweight="bold")
    ax.text(x + .12, y + h - (.50 if title else .22), "\n".join(lines), ha="left", va="top", color=INK2, fontsize=bsize, linespacing=1.4)


def arrow(ax, x0, y, x1, color=INK2):
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", color=color, lw=1.3, mutation_scale=12))


def main():
    lock2 = json.load(open(f"{DATA_NEW}/locked_params_phase02.json")); rc = lock2["rule_c"]; tau14, tau45 = lock2["tau14"], lock2["tau45"]
    fig, ax = plt.subplots(figsize=(17, 9.6), dpi=130); ax.set_xlim(0, 20); ax.set_ylim(0, 10.5); ax.axis("off")
    cols_x = [.3, 4.3, 8.9, 14.2]; cols_w = [3.6, 4.2, 4.9, 3.0]; hdr = ["ĐẦU VÀO (mỗi mẫu 10 phút)", "CÁCH TÍNH", "QUY TẮC BÁO", "CỜ BÁO"]
    for x, w, t in zip(cols_x, cols_w, hdr): ax.text(x + w / 2, 9.42, t, ha="center", va="center", color=INK, fontsize=10.5, fontweight="bold")
    rows = [
        (TEAL, "TẦNG A · ngoại suy tới ngưỡng", 6.35,
         ["Direct (rung tổng p-p, µm)", "8 kênh · giờ máy chạy", "+ lịch dừng/khởi động thật"],
         ["trung vị ngày trên giờ máy chạy", f"hồi quy tuyến tính {TIERA_WINDOW_RUN_DAYS} ngày CHẠY", "(không vắt qua lần dừng)",
          f"ngoại suy tới {PLANT_LIMIT_UM:.0f} µm, cùng mức 8 kênh", "cận dưới số ngày còn lại từ", f"khoảng tin cậy 90 % của dốc (z = {TIERA_Z90})"],
         [f"mức > {1 + TIERA_RISE_MIN:.2f} × trung vị {TIERA_REF_DAYS} ngày trước", "(đang leo so với chính nó)", f"dốc có ý nghĩa: t > {TIERA_Z90}",
          f"cận dưới còn < {TIERA_HORIZON_DAYS} ngày", f"giữ ≥ {TIERA_CONSEC} ngày liên tiếp", f"bỏ {TIERA_STARTUP_SKIP} ngày đầu sau khởi động"],
         ["A", "mức cao", "ngưỡng nhà máy đang dùng", "kênh nào leo → ổ đó"]),
        (AMB, "TẦNG B · tốc độ lệch khỏi đoạn nền ổn định", 3.45,
         ["24 đặc trưng 1X đã scale", "(8 biên min-max, 8 sin, 8 cos)", "SAE 6 lớp 24→24 số nguyên", "→ SPE = Σ(x − x̂)²"],
         ["nền cố định 9b; SPE so nền = trạng thái", "dốc log-SPE trung vị ngày:", f"  thang {SLOPE_DAYS} ngày (≥ {SLOPE_MIN_OBS} ngày quan sát)",
          f"  thang {lock2['slow_days']} ngày (≥ {lock2['slow_min_obs']} ngày quan sát)", "đóng góp kênh r²biên+r²sin+r²cos", "→ chỉ ổ đỡ đang lệch"],
         [f"B₁₄: dốc 14 ngày > τ₁₄ = {tau14}", f"      giữ ≥ {CONSEC} ngày liên tiếp", f"B₄₅: dốc 45 ngày > τ₄₅ = {tau45}",
          f"      giữ ≥ {lock2['slow_consec']} ngày liên tiếp", "B₄₅ giữ báo khi B₁₄ đã ngừng", "(log SPE bão hòa khi SPE lớn)"],
         ["B₁₄ / B₄₅", "mức cao", "ngưỡng tương đối, sớm hơn A", "kèm ổ đóng góp lớn nhất"]),
        (ROSE, "TẦNG C · cơ chế hư hỏng", .55,
         ["1X Phase 8 kênh (°)", "+ biên độ 1X", "+ lịch khởi động thật"],
         ["chữ ký tuần của cả hệ 8 kênh:", "trung bình tròn và sd tròn của pha", "tốc độ quay pha (°/tuần):", "  hồi quy 4 tuần trên pha đã unwrap",
          "tham chiếu: tốc độ 8 tuần trước", f"  (lịch, ±{rc['lookback_tol_days']} ngày)"],
         ["kênh chữ ký 2001X:", f"dấu tốc độ đổi so {rc['lookback_days'] // 7} tuần trước", f"|tốc độ| > {rc['min_rate_deg_wk']:.0f}°/tuần cả hai phía",
          f"sd tuần < {rc['sd_max_deg']:.0f}°", f"giữ {rc['hold_weeks']} tuần liên tiếp", "ngày báo = ngày cuối tuần", f"tách riêng cửa sổ {rc['post_restart_days']} ngày sau khởi động"],
         ["C", "mức thấp \"cần xem\"", "đọc cơ chế: điểm nặng di chuyển,", "chưa tự báo mức cao"]),
    ]
    h = 2.55
    for c, name, y, inp, calc, rule, flag in rows:
        ax.add_patch(FancyBboxPatch((.12, y - .12), 19.76, h + .55, boxstyle="round,pad=0.02,rounding_size=0.15", fc=c, ec="none", alpha=.045))
        ax.text(.3, y + h + .22, name, ha="left", va="center", color=c, fontsize=11, fontweight="bold")
        box(ax, cols_x[0], y, cols_w[0], h, "", inp, c); box(ax, cols_x[1], y, cols_w[1], h, "", calc, c); box(ax, cols_x[2], y, cols_w[2], h, "", rule, c)
        # cờ: khối đậm hơn
        x, w = cols_x[3], cols_w[3]
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=c, ec=c, lw=1.3, alpha=.22))
        ax.text(x + w / 2, y + h - .45, flag[0], ha="center", va="center", color=c, fontsize=17, fontweight="bold")
        ax.text(x + w / 2, y + h - 1.0, flag[1], ha="center", va="center", color=INK, fontsize=10)
        ax.text(x + w / 2, y + .55, "\n".join(flag[2:]), ha="center", va="center", color=INK2, fontsize=8.2, linespacing=1.4)
        for i in range(3): arrow(ax, cols_x[i] + cols_w[i] + .03, y + h / 2, cols_x[i + 1] - .03, color=c)
    # nhánh song song: một nguồn dữ liệu, ba tầng độc lập, gộp về màn hình / đèn
    ax.text(.3, 10.2, "Sơ đồ logic ba tầng cảnh báo A / B / C chạy song song: mỗi tầng một trục dữ liệu, một câu hỏi, một quy tắc báo riêng",
            ha="left", va="center", color=INK, fontsize=13, fontweight="bold")
    ax.text(.3, 9.87, "A trả lời \"còn bao lâu tới ngưỡng\", B trả lời \"đang rời xa nền nhanh cỡ nào\", C trả lời \"cơ chế gì\" · cờ nào cũng chỉ ra ổ đỡ · ba cờ hiển thị cùng lúc (đèn A/B₁₄/B₄₅/C trên bo, trang trình diễn)",
            ha="left", va="center", color=INK2, fontsize=9)
    fig.savefig(OUT, bbox_inches="tight", facecolor=BG); print("saved", OUT)


if __name__ == "__main__":
    main()
