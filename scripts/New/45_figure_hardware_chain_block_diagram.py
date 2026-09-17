#!/usr/bin/env python3
"""45_figure_hardware_chain_block_diagram.py — Sơ đồ khối kết nối phần cứng: đầu đo → System 1 → PI Data Archive → PC → USB → ESP32-S3.

Ba khối bên trái là hạ tầng nhà máy (đo, trích 1X/Direct, lưu trữ), ba khối bên phải là phần đồ án (PC phát lại, cổng USB, bo ESP32-S3).
Ranh giới nhà máy / đồ án là file xuất PI DataLink. Mũi tên ngược từ ESP32-S3 về PC là JSON kết quả mỗi ngày/tuần cho trang trình diễn.
Thông số cổng nối tiếp lấy đúng firmware/esp32s3/main/main.c và scripts/New/28_replay_to_esp32_serial.py. Ra: Bao_cao/hinh-so-do-khoi-phan-cung.png
"""
import os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
OUT = f"{ROOT}/Bao_cao/hinh-so-do-khoi-phan-cung.png"
BG, SF, INK, INK2, MUTE = "#0e0e14", "#14141c", "#d6d6de", "#9a9aac", "#5c5c70"
TEAL, AMB, BLUE, ROSE, BAD = "#63a898", "#c9a35c", "#7d9ad0", "#c47c9a", "#c0705a"
plt.rcParams.update({"figure.facecolor": BG, "text.color": INK, "font.family": "DejaVu Sans", "font.size": 9})

BLOCKS = [  # (tiêu đề, dòng phụ, thân, màu)
    ("ĐẦU ĐO", "8 đầu đo tiệm cận · 4 ổ đỡ", ["Bently Nevada, dòng xoáy", "mỗi ổ 2 đầu đo X/Y lệch 90°", "29VT-2001…2007 (A X/Y)",
                                            "Keyphasor 29KT-2014A", "→ tín hiệu rung tương tự"], TEAL),
    ("SYSTEM 1", "Bently Nevada · giám sát rung", ["sóng thô đồng bộ tốc độ quay", "trích 1X biên + pha, 8 kênh", "Direct p-p (8 kênh), tốc độ",
                                                 "dạng sóng 256 mẫu/vòng khi cần", "→ giá trị đã trích, 10 phút"], TEAL),
    ("PI DATA ARCHIVE", "OSIsoft/AVEVA · lưu trữ", ["tag theo kênh: 1X Amp,", "1X Phase, Direct; nhiều năm", "xuất qua PI DataLink (Excel)",
                                                  "44.358 dòng 10 phút kéo về", "(28/09/2025 → 02/09/2026)"], TEAL),
    ("PC", "Python · phát lại", ["lọc máy chạy → 42.064 mẫu", "kho đặc trưng 24 chiều", "(biên, sin, cos của 8 kênh)", "replay_stream.txt (script 27):",
                                 "S = 24 đặc trưng, D = Direct", "script 28: gửi dòng, gom JSON"], AMB),
    ("USB", "USB-Serial-JTAG gốc của chip", ["115200 baud, 8N1", "không bắt tay phần cứng", "gói 8 dòng ≈ 2,5 KB, chờ ping", "→ không tràn đệm RX 4 KB",
                                             "DTR/RTS giữ tắt khi mở cổng", "(tránh reset chip)"], BLUE),
    ("ESP32-S3", "DevKitC · ESP-IDF v5.3.2", ["SAE số nguyên int16/int8 + LUT", "ba tầng A / B₁₄ / B₄₅ / C, C99", "JSON khi đóng ngày / tuần",
                                             "646 µs/mẫu, tối đa 4,9 ms", "42.064 mẫu phát lại: 106 s"], ROSE),
]
LINKS = ["tín hiệu\ntương tự", "1X, Direct\n10 phút", "PI DataLink\nfile Excel", "dòng S / D\nvăn bản", "byte\n115200"]


def block(ax, x, y, w, h, title, sub, lines, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.14", fc="#191922", ec=color, lw=1.4))
    ax.add_patch(FancyBboxPatch((x, y + h - .62), w, .62, boxstyle="round,pad=0.02,rounding_size=0.14", fc=color, ec=color, lw=0, alpha=.18))
    ax.text(x + w / 2, y + h - .20, title, ha="center", va="center", color=color, fontsize=11.5, fontweight="bold")
    ax.text(x + w / 2, y + h - .47, sub, ha="center", va="center", color=INK, fontsize=8.6)
    ax.text(x + .13, y + h - .85, "\n".join(lines), ha="left", va="top", color=INK2, fontsize=7.8, linespacing=1.45)


def main():
    fig, ax = plt.subplots(figsize=(17, 6.2), dpi=130); ax.set_xlim(0, 20); ax.set_ylim(0, 6); ax.axis("off")
    w, h, y0, gap = 2.72, 3.0, 1.55, .58; x0 = .25
    for i, (t, s, ls, c) in enumerate(BLOCKS):
        x = x0 + i * (w + gap); block(ax, x, y0, w, h, t, s, ls, c)
        if i < 5:
            ax.add_patch(FancyArrowPatch((x + w + .03, y0 + h / 2), (x + w + gap - .03, y0 + h / 2), arrowstyle="-|>", color=INK2, lw=1.5, mutation_scale=14))
            ax.text(x + w + gap / 2, y0 + h + .08, LINKS[i], ha="center", va="bottom", color=INK2, fontsize=7.6, bbox=dict(fc=BG, ec="none", pad=1.5))
    # mũi tên ngược: JSON kết quả ESP32-S3 → PC → trang trình diễn
    xe = x0 + 5 * (w + gap); xp = x0 + 3 * (w + gap)
    ax.add_patch(FancyArrowPatch((xe + .4, y0 - .05), (xp + w - .4, y0 - .05), connectionstyle="arc3,rad=.28", arrowstyle="-|>", color=ROSE, lw=1.3, mutation_scale=13, ls="--"))
    ax.text((xe + xp + w) / 2, y0 - .70, "JSON kết quả mỗi ngày / tuần (đèn A, B₁₄, B₄₅, C, SPE, thống kê thời gian, bộ nhớ) → esp32_replay_log.jsonl → demo-esp32-live.html",
            ha="center", va="top", color=ROSE, fontsize=8.4, bbox=dict(fc=BG, ec="none", pad=1.5))
    # dải nhóm: nhà máy / đồ án, ranh giới là file xuất
    xb = x0 + 3 * (w + gap) - gap / 2
    ax.plot([xb, xb], [.45, 5.55], color=AMB, lw=1.2, ls=":")
    ax.text(x0 + 1.5 * w + gap, 5.35, "HẠ TẦNG NHÀ MÁY (Đạm Cà Mau) · đo, trích đặc trưng, lưu trữ", ha="center", va="center", color=TEAL, fontsize=10, fontweight="bold")
    ax.text(x0 + 4.5 * w + 4 * gap, 5.35, "PHẦN ĐỒ ÁN · phát lại toàn chuỗi và thiết bị biên", ha="center", va="center", color=ROSE, fontsize=10, fontweight="bold")
    ax.text(xb, .22, "ranh giới: dữ liệu đã trích được xuất thành file, đồ án không chạm vào hệ đo và System 1", ha="center", va="center", color=AMB, fontsize=8.4)
    ax.text(.25, 5.85, "Sơ đồ khối kết nối phần cứng: đầu đo → System 1 → PI Data Archive → PC → USB → ESP32-S3", ha="left", va="center", color=INK, fontsize=13, fontweight="bold")
    fig.savefig(OUT, bbox_inches="tight", facecolor=BG); print("saved", OUT)


if __name__ == "__main__":
    main()
