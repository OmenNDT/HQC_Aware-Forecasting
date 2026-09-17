#!/usr/bin/env python3
"""29_figure_system_architecture.py — Hình 2.1: kiến trúc tổng thể (5 tầng) cho báo cáo, cùng tông tối với các hình khác."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BG, PANEL, INK, DIM, ACC, ACC2, EDGE = "#0e0e14", "#161620", "#d6d7de", "#8a8c9a", "#e8a06a", "#7fb3d5", "#2a2b38"
fig, ax = plt.subplots(figsize=(13, 9.2), dpi=170); fig.patch.set_facecolor(BG); ax.set_facecolor(BG); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 100)

def box(x, y, w, h, title, lines, color=ACC2, tw=13):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.6", fc=PANEL, ec=EDGE, lw=1.2))
    ax.plot([x + 0.6, x + w * 0.55], [y + h - 0.15, y + h - 0.15], color="white", alpha=.18, lw=1)
    ax.text(x + 1.8, y + h - 2.3, title, color=color, fontsize=tw, weight="bold", va="top", ha="left")
    for i, l in enumerate(lines):
        ax.text(x + 1.8, y + h - 5.6 - i * 3.0, l, color=INK, fontsize=9.6, va="top", ha="left")

def arrow(x, y0, y1, label=None):
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=18, color=ACC, lw=1.8))
    if label: ax.text(x + 1.2, (y0 + y1) / 2, label, color=DIM, fontsize=9.5, va="center", ha="left")

ax.text(50, 98.5, "Kiến trúc tổng thể hệ cảnh báo sớm P29201A", color="#eeeef3", fontsize=15, weight="bold", ha="center", va="top")
# nguồn
box(4, 84, 44, 10.5, "NGUỒN ĐO · System 1 (Bently Nevada)", ["8 đầu đo tiệm cận trên 4 ổ đỡ → 1X Amp + 1X Phase", "Direct 8 kênh (peak-to-peak) · ngưỡng nhà máy 65 µm"], color=ACC2)
box(51, 84, 45, 10.5, "LƯU TRỮ · PI Data Archive", ["Truy xuất qua PI DataLink", "1X mỗi 10 phút (28/09/2025 → 02/09/2026) · Direct mỗi 1 giờ"], color=ACC2)
arrow(25.5, 83.6, 79.2); arrow(74.5, 83.6, 79.2)
# tầng dữ liệu
box(4, 66, 92, 12.5, "TẦNG DỮ LIỆU", ["Cổng lọc máy chạy (≥ 6/8 kênh > 3 µm) → thống nhất tham chiếu pha (+148° trước 15/01/2026)",
    "Kho đặc trưng 24 chiều (8 biên độ chuẩn hóa theo nền, 8 sin, 8 cos) → vai trò từng đoạn: nền, chỉnh, kiểm trước, âm, mù"])
arrow(50, 65.6, 60.6)
# tầng mô hình
box(4, 48.5, 92, 11.5, "TẦNG MÔ HÌNH", ["Nền gốc 9b (20/02–22/03/2026) → 5 khối chéo có đệm 12 h → bảy họ tái tạo (PCA, AE, SAE, VAE, DBN, ED-LSTM, ED-CNN)",
    "Bốn tiêu chí đo được → chọn SAE 3.600 tham số · SPE = Σ(x − x̂)² so với nền gốc · đóng góp từng kênh"])
arrow(50, 48.1, 43.1)
# ba tầng
ax.add_patch(FancyBboxPatch((4, 24), 92, 18.5, boxstyle="round,pad=0.4,rounding_size=1.6", fc=PANEL, ec=EDGE, lw=1.2))
ax.text(5.8, 40.3, "BA TẦNG CẢNH BÁO (chạy song song, mỗi tầng một trục dữ liệu)", color=ACC, fontsize=13, weight="bold", va="top")
for i, (t, l1, l2) in enumerate([("A · Ngoại suy tới ngưỡng", "Direct → hồi quy 14 ngày chạy", "→ cận dưới ngày còn lại tới 65 µm < 30"),
                                 ("B · Tốc độ lệch khỏi nền", "SPE so nền gốc → dốc log SPE", "14 ngày (τ₁₄), 45 ngày (τ₄₅), ngưỡng khóa"),
                                 ("C · Chữ ký hình dạng hệ", "Pha 1X 8 kênh theo tuần", "→ đổi chiều quay ổ 2001 → \"cần xem\"")]):
    x = 5.5 + i * 30.2
    ax.add_patch(FancyBboxPatch((x, 26), 29, 10.5, boxstyle="round,pad=0.3,rounding_size=1.2", fc="#1c1c28", ec=EDGE, lw=1))
    ax.text(x + 1.2, 35.2, t, color="#f2d7a3", fontsize=10.5, weight="bold", va="top"); ax.text(x + 1.2, 32.0, l1, color=INK, fontsize=8.9, va="top"); ax.text(x + 1.2, 29.3, l2, color=INK, fontsize=8.9, va="top")
arrow(50, 23.6, 18.6, "lead-time = ngày báo đầu → ngày nhà máy dừng")
# thiết bị biên
box(4, 5, 92, 13, "THIẾT BỊ BIÊN · ESP32-S3", ["SAE lượng tử hóa hỗn hợp (lớp 0–1 int16, lớp 2–5 int8) + ba tầng bằng C99, hằng số sinh từ file khóa kèm hash",
    "Suy luận mỗi mẫu 10 phút · cùng ngày báo với bản Python trên toàn chuỗi · trạng thái 8,3 KB RAM, hằng số 9,9 KB flash"], color=ACC)
fig.savefig("Bao_cao/hinh-kien-truc-tong-the.png", facecolor=BG, bbox_inches="tight", pad_inches=0.25); print("saved Bao_cao/hinh-kien-truc-tong-the.png")
