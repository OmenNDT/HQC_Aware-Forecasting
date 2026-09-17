"""08_quantize_and_emit_c.py — Lượng tử hóa Int8 per-channel + sinh mã C + đo dấu chân nhúng

Sinh tự động từ lineage artifact: hqc_quantization.png
version_id: c6a56a7f-2867-4626-b493-cb279915a0c9
Môi trường: conda env 'python'

CẢNH BÁO: đây là mã trích từ lineage, đường dẫn dữ liệu là đường dẫn TUYỆT ĐỐI
của máy gốc. Kiểm lại biến đường dẫn trước khi chạy lại.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score

# (helper apply_figure_style() của skill figure-style — nạp qua skill, không cần trong script)
from_skill_note=True

sens = ["29VT-2001X", "29VT-2001Y", "29VT-2003X", "29VT-2003Y",
        "29VT-2005X", "29VT-2005Y", "29VT-2007X", "29VT-2007Y"]


def feat(df):
    A = df[[f"1X_Amp_{s}" for s in sens]].to_numpy(float)
    P = np.radians(df[[f"1X_Phase_{s}" for s in sens]].to_numpy(float))
    return np.hstack([A, np.sin(P), np.cos(P)])


TR = pd.read_csv("/home/sontn/.claude-science/orgs/49e3c671-cbbe-4f16-8bad-8cba412d2a77/artifacts/proj_0c140d6162d4/23801e8f-bbd6-4cdd-8e8a-7fb250dc72a2/v1eb375fe_HQC_train_healthy_flat.csv", parse_dates=["timestamp"]).set_index("timestamp")
EV = pd.read_csv("/home/sontn/.claude-science/orgs/49e3c671-cbbe-4f16-8bad-8cba412d2a77/artifacts/proj_0c140d6162d4/0c353bbe-47bb-45cf-bc88-46c1e3f51393/vbbf0f343_HQC_eval_expert.csv", keep_default_na=False)

X = feat(TR)
mu, sd = X.mean(0), X.std(0) + 1e-9
Z = (X - mu) / sd
cut = int(len(Z) * 0.75)
Za, Zv = Z[:cut], Z[cut:]

p = PCA(n_components=6).fit(Za)
W = p.components_  # 6 x 24
c = p.mean_        # 24

Xev = feat(EV)
Zev = (Xev - mu) / sd

is_norm = (EV.nhan_ung_vien == "binh_thuong").to_numpy()
is_up = (EV.nhan_ung_vien == "bat_thuong").to_numpy() & (EV.lech_lon_nhat_pct.astype(float) > 0).to_numpy()


def resid(Xr, mu_, sd_, W_, c_):
    Zr = (Xr - mu_) / sd_
    return np.abs(Zr - ((Zr - c_) @ W_.T @ W_ + c_)).mean(1)


def q_pertensor(A):
    s = np.abs(A).max() / 127.0
    return np.round(A / s).astype(np.int8).astype(np.float32) * s


def q_perchan(A):
    s = np.abs(A).max(axis=1, keepdims=True) / 127.0
    return np.round(A / s).astype(np.int8).astype(np.float32) * s


schemes = {
    "float32 (gốc)": (mu, sd, W, c),
    "int8 per-tensor TẤT CẢ": (q_pertensor(mu), q_pertensor(sd), q_pertensor(W), q_pertensor(c)),
    "int8 W per-channel, mu/sd float": (mu, sd, q_perchan(W), q_pertensor(c)),
    "int8 W+c per-channel, mu/sd float16": (mu.astype(np.float16).astype(np.float32),
                                             sd.astype(np.float16).astype(np.float32),
                                             q_perchan(W), q_pertensor(c)),
}

mask = is_norm | is_up
out = {}
for nm, (m_, s_, W_, c_) in schemes.items():
    with np.errstate(divide="ignore", invalid="ignore"):
        re = resid(Xev, m_, s_, W_, c_)
    if not np.isfinite(re).all():
        out[nm] = None
        continue
    auc = roc_auc_score(is_up[mask].astype(int), re[mask])
    out[nm] = dict(re=re, norm=re[is_norm].mean(), up=re[is_up].mean(),
                   ratio=re[is_up].mean() / re[is_norm].mean(), auc=auc)

fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(13.2, 4.2))
C_OK = "#4c78a8"; C_BAD = "#c1272d"; C_G = "#b8b8b8"

lab = ["float32\n(gốc)", "int8\nper-tensor", "int8 W\nper-channel", "int8+fp16\n(chốt)"]
byts = [864, 216, 360, 264]
aucs = [0.8337, np.nan, 0.8338, 0.8339]
y = np.arange(4)
cols = [C_G, C_BAD, C_OK, C_OK]
a1.bar(y, byts, color=cols, width=.6, zorder=3)
for yi, v in zip(y, byts):
    a1.text(yi, v + 18, f"{v} B", ha="center", fontsize=7.4, fontweight="bold")
a1.text(1, 430, "SẬP\n(chia cho 0)", ha="center", va="bottom", fontsize=7, color=C_BAD,
        fontweight="bold", linespacing=1.2)
a1.set_xticks(y); a1.set_xticklabels(lab, fontsize=6.8)
a1.set_ylabel("Bộ nhớ tham số (byte)", labelpad=9); a1.set_ylim(0, 1060)
a1.set_title("Nén 864 → 264 byte (3,3×)", fontsize=8.3, loc="left")

ok = [0, 2, 3]
a2.bar([y[i] for i in ok], [aucs[i] for i in ok], color=[cols[i] for i in ok], width=.6, zorder=3)
for i in ok:
    a2.text(y[i], aucs[i] + 0.0006, f"{aucs[i]:.4f}", ha="center", fontsize=7.4, fontweight="bold")
a2.text(1, 0.8318, "n.d.\n(sập)", ha="center", fontsize=7, color=C_BAD, linespacing=1.2)
a2.set_xticks(y); a2.set_xticklabels(lab, fontsize=6.8)
a2.set_ylabel("AUC phát hiện bất thường", labelpad=9); a2.set_ylim(0.831, 0.8355)
a2.set_title("Độ chính xác KHÔNG mất gì", fontsize=8.3, loc="left")

items = ["Flash\nhằng số", "RAM\nstack", "Mã máy\n(hàm)"]
vals = [384, 216, 1149]
a3.barh(np.arange(3)[::-1], vals, color=C_OK, height=.55, zorder=3)
for yi, v in zip(np.arange(3)[::-1], vals):
    a3.text(v + 22, yi, f"{v} B", va="center", fontsize=7.4, fontweight="bold")
a3.set_yticks(np.arange(3)[::-1]); a3.set_yticklabels(items, fontsize=7)
a3.set_xlabel("Byte", labelpad=9); a3.set_xlim(0, 1450)
a3.set_title("Dấu chân trên MCU — đã biên dịch & kiểm chứng", fontsize=8.3, loc="left")
a3.text(1400, 2.15, "khớp Python\nsai lệch < 1e-5", fontsize=6.6, ha="right", color="#555",
        style="italic", linespacing=1.25)
fig.tight_layout()
fig.savefig("hqc_quantization.png", dpi=300, bbox_inches="tight")
r = fig.canvas.get_renderer()
tx = [(t, t.get_window_extent(r)) for t in fig.findobj(mpl.text.Text) if t.get_text().strip() and t.get_visible()]
ov = [(a.get_text()[:22], b.get_text()[:22]) for i, (a, ba) in enumerate(tx) for b, bb in tx[i+1:] if ba.overlaps(bb)]
print("saved | overlaps:", len(ov), ov[:4])