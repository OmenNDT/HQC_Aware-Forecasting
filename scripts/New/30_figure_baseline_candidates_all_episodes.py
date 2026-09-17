#!/usr/bin/env python3
"""30_figure_baseline_candidates_all_episodes.py — Hình 2.2: các đoạn chạy 7, 8, 9a, 9b, 9c, 11 trên chuỗi 1X trung vị ngày,
ghi chú đầy đủ từng đoạn và thước hệ 8 kênh của bốn ứng viên nền (số từ Bảng 2.2 / script 11_profile_1x_episode_pull.py)."""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402

BG, PANEL, INK, DIM, GRID = "#0e0e14", "#161620", "#d6d7de", "#8a8c9a", "#2a2b38"
C2001, C2001Y, C2003, C2005, CSEL, CAMB = "#5fbfa0", "#5fbfa0", "#b08a4a", "#5f7fc0", "#5fbfa0", "#c9963a"
STOPS = [("2025-11-04", "2025-11-07", "dừng\n(khoảng trống)"), ("2026-01-04", "2026-01-15", "dừng 1\ntháo kiểm tra"), ("2026-05-29", "2026-06-02", "dừng 2\ntháo kiểm tra"), ("2026-06-11", "2026-06-14", "")]
# (nhãn, từ, đến, màu nền, dòng chú thích) — số dốc/pha/mức lấy từ Bảng 2.2
EPIS = [("Đoạn 7", "2025-09-28", "2025-11-03", "#3a3020", "thử âm\ndốc 8,7 %/th · pha 7,7 °/th\n2001X 22,8 µm, đang giảm"),
        ("Đoạn 8", "2025-11-07", "2026-01-03", "#20283a", "thử âm (cửa sổ 02/12–01/01)\ndốc 2,3 %/th · pha 5,1 °/th\n2001X 21,2 µm, bình nguyên"),
        ("Đoạn 9a", "2026-01-15", "2026-02-05", "#2a2036", "thử âm mạnh\nhệ đang lắng sau tháo lắp\n2001 = 11 µm, pha nhảy +39°"),
        ("05–19/02", "2026-02-05", "2026-02-19", "#262630", "chỉ mô tả\n(bước 1 giờ,\nleo vào nền)"),
        ("Đoạn 9b", "2026-02-20", "2026-03-22", "#1b3a32", "ĐOẠN NỀN ỔN ĐỊNH\nhuấn luyện 5 khối chéo\ndốc 2,0 %/th · pha 4,4 °/th\n2001X 17,5 µm, thấp nhất"),
        ("Đoạn 9c", "2026-03-23", "2026-05-29", "#3a2a20", "9c1 23/03–15/05: chỉnh ngưỡng (→ 30/04),\nkiểm trước (01–29/05) · 9c2 16/05–29/05: tăng tốc\nleo 17 → 43 µm tới dừng 2"),
        ("Đoạn 10", "2026-06-02", "2026-06-10", "#262630", "chỉ mô tả\n(quá độ\nsau dừng 2)"),
        ("Đoạn 11", "2026-06-14", "2026-09-02", "#33203a", "kiểm mù\n11a 14/06–18/07: bình nguyên (dốc 3,2 · pha 2,1)\n11b từ 19/07: leo chậm, pha đổi chiều")]
SUBDIV = [("2026-05-16", "9c1 | 9c2"), ("2026-07-19", "11a | 11b")]      # vạch chia cửa sổ con
CAND = [("Đoạn 7", 8.7, 7.7, 22.8), ("Đoạn 8\n(cửa sổ 02/12–01/01)", 2.3, 5.1, 21.2), ("Đoạn 9b\n(chọn)", 2.0, 4.4, 17.5), ("Đoạn 11a\n(bình nguyên 14/06–18/07)", 3.2, 2.1, 21.0)]


def main():
    fs = pd.read_parquet(FEATURE_STORE); d = fs[[f"amp_{c}" for c in ["2001X", "2001Y", "2003X", "2005X"]]].resample("1D").median()
    fig = plt.figure(figsize=(23, 12), dpi=140); fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0.06, 0.40, 0.92, 0.53]); ax2 = fig.add_axes([0.06, 0.06, 0.92, 0.24])
    for a in (ax, ax2): a.set_facecolor(PANEL); [s.set_color(GRID) for s in a.spines.values()]; a.tick_params(colors=DIM); a.grid(color=GRID, alpha=.5, lw=.6)
    for lab, a0, b0, col, note in EPIS:
        ax.axvspan(pd.Timestamp(a0), pd.Timestamp(b0) + pd.Timedelta(days=1), color=col, alpha=.55, lw=0)
        mid = pd.Timestamp(a0) + (pd.Timestamp(b0) - pd.Timestamp(a0)) / 2
        small = (pd.Timestamp(b0) - pd.Timestamp(a0)).days < 25           # đoạn ngắn: nhãn đặt ở dải thấp hơn để không chồng
        yt, yn = (37.5, 35.3) if small else (46.5, 44.2)
        if lab == "05–19/02": yt, yn = (30.0, 27.8)                          # dải thứ ba cho khoảng chỉ mô tả kẹp giữa 9a và 9b
        ax.text(mid, yt, lab, color=CSEL if "9b" in lab else INK, fontsize=9.5 if small else 11.5, weight="bold", ha="center", va="top")
        ax.text(mid, yn, note, color=DIM, fontsize=7.6 if small else 8.4, ha="center", va="top", linespacing=1.25)
    for x0, lab in SUBDIV:
        ax.axvline(pd.Timestamp(x0), color=INK, ls="--", lw=.8, alpha=.5); ax.text(pd.Timestamp(x0), 38.5, lab, color=INK, fontsize=8.5, ha="center", va="bottom", alpha=.8)
    for a0, b0, lab in STOPS:
        ax.axvspan(pd.Timestamp(a0), pd.Timestamp(b0), color="#6a6a7a", alpha=.35, lw=0)
        if lab: ax.text(pd.Timestamp(a0) + (pd.Timestamp(b0) - pd.Timestamp(a0)) / 2, 2.5, lab, color=INK, fontsize=8.5, ha="center", va="bottom")
    ax.axvline(pd.Timestamp("2026-01-15"), color="#e07a5f", ls=":", lw=1.2); ax.text(pd.Timestamp("2026-01-16"), 24, "tham chiếu pha\ntua-bin xoay 148°", color="#e07a5f", fontsize=8.5, va="bottom")
    ax.axvspan(pd.Timestamp("2026-02-20"), pd.Timestamp("2026-03-23"), fill=False, ec=CSEL, lw=2)
    ax.annotate("CHỌN\nĐOẠN NỀN ỔN ĐỊNH", xy=(pd.Timestamp("2026-03-07"), 18.5), xytext=(pd.Timestamp("2026-03-07"), 27.5), color=CSEL, fontsize=11, weight="bold", ha="center", arrowprops=dict(arrowstyle="-|>", color=CSEL))
    ax.plot(d.index, d["amp_2003X"] / 2, color=C2003, lw=1, alpha=.85, label="2003X ÷ 2 (đối chứng)")
    ax.plot(d.index, d["amp_2005X"], color=C2005, lw=1, alpha=.85, label="2005X (đối chứng)")
    ax.plot(d.index, d["amp_2001Y"], color=C2001Y, lw=1.4, ls="--", alpha=.9, label="2001Y")
    ax.plot(d.index, d["amp_2001X"], color=C2001, lw=2.2, label="2001X")
    ax.set_ylim(0, 48); ax.set_xlim(pd.Timestamp("2025-09-24"), pd.Timestamp("2026-09-06"))
    ax.set_ylabel("1X Amp (µm), trung vị ngày, giờ máy chạy", color=INK); ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
    ax.legend(loc="lower right", ncol=4, facecolor=PANEL, edgecolor=GRID, labelcolor=INK, fontsize=9.5)
    ax.set_title("Các đoạn chạy của P29201A trên chuỗi 1X 9/2025 → 9/2026 và lựa chọn đoạn nền ổn định 9b", color="#eeeef3", fontsize=14, weight="bold", pad=10)
    # thước hệ 8 kênh
    x = range(len(CAND)); w = .26
    for i, (lab, sl, ph, lv) in enumerate(CAND):
        sel = "9b" in lab; col = CSEL if sel else "#4a4c5c"
        b1 = ax2.bar(i - w, sl, w, color=col, alpha=.95); b2 = ax2.bar(i, ph, w, color=col, alpha=.6); b3 = ax2.bar(i + w, (lv / 17.5 - 1) * 100, w, color=CAMB, alpha=.9)
        for b, v in [(b1, sl), (b2, ph), (b3, (lv / 17.5 - 1) * 100)]:
            ax2.text(b[0].get_x() + w / 2, v + .6, f"{v:.1f}", color=INK, fontsize=9, ha="center", va="bottom")
    ax2.set_xticks(list(x)); ax2.set_xticklabels([c[0] for c in CAND], color=INK, fontsize=10); ax2.set_ylim(0, 36)
    ax2.legend(handles=[plt.Rectangle((0, 0), 1, 1, color="#4a4c5c"), plt.Rectangle((0, 0), 1, 1, color="#4a4c5c", alpha=.6), plt.Rectangle((0, 0), 1, 1, color=CAMB)],
               labels=["dốc biên độ TB 8 kênh (%/tháng)", "trôi pha TB 8 kênh (°/tháng)", "mức 2001X cao hơn 9b (%)"], loc="upper right", ncol=3, facecolor=PANEL, edgecolor=GRID, labelcolor=INK, fontsize=9.5)
    ax2.set_title("Thước hệ 8 kênh của bốn ứng viên nền: càng thấp càng ổn định · 9b thấp nhất ở dốc biên độ, thứ hai ở trôi pha, mức 2001 thấp nhất", color=DIM, fontsize=11, loc="left")
    fig.text(0.06, 0.012, "Nguồn: kho đặc trưng 1X (6 file kéo 10 phút, 28/09/2025 → 02/09/2026). Dốc và trôi pha là trung bình trị tuyệt đối trên 8 kênh trong cửa sổ; 9a không làm ứng viên vì hệ đang lắng sau tháo lắp; 9c là đợt leo; 05–19/02 và đoạn 10 chỉ mô tả.", color=DIM, fontsize=8.5)
    out = f"{ROOT}/Bao_cao/hinh-chon-nen-goc-9b.png"; fig.savefig(out, facecolor=BG, bbox_inches="tight", pad_inches=0.2); print("saved", out)


if __name__ == "__main__":
    main()
