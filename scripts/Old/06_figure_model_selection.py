"""06_figure_model_selection.py — Figure chọn mô hình: learning curve + tỉ số tách + contribution

Sinh tự động từ lineage artifact: hqc_model_selection.png
version_id: f5585977-7837-4edb-abf4-73c725e8ef13
Môi trường: conda env 'python'

CẢNH BÁO: đây là mã trích từ lineage, đường dẫn dữ liệu là đường dẫn TUYỆT ĐỐI
của máy gốc. Kiểm lại biến đường dẫn trước khi chạy lại.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPRegressor

# (helper apply_figure_style() của skill figure-style — nạp qua skill, không cần trong script)
from_skill_note=True

TR = pd.read_csv("/home/sontn/.claude-science/orgs/49e3c671-cbbe-4f16-8bad-8cba412d2a77/artifacts/proj_0c140d6162d4/0dce3195-b9a4-49d3-a288-1b43c39f7940/v40969419_HQC_train_healthy.csv", parse_dates=["timestamp"]).set_index("timestamp")
EV = pd.read_csv("/home/sontn/.claude-science/orgs/49e3c671-cbbe-4f16-8bad-8cba412d2a77/artifacts/proj_0c140d6162d4/0c353bbe-47bb-45cf-bc88-46c1e3f51393/vf282060f_HQC_eval_expert.csv", parse_dates=["timestamp"], keep_default_na=False)

sens = ["29VT-2001X", "29VT-2001Y", "29VT-2003X", "29VT-2003Y",
        "29VT-2005X", "29VT-2005Y", "29VT-2007X", "29VT-2007Y"]


def featurize(df, ref_mu=None, ref_sd=None):
    A = df[[f"1X_Amp_{s}" for s in sens]].to_numpy(float)
    P = np.radians(df[[f"1X_Phase_{s}" for s in sens]].to_numpy(float))
    X = np.hstack([A, np.sin(P), np.cos(P)])
    if ref_mu is None:
        ref_mu, ref_sd = X.mean(0), X.std(0) + 1e-9
    return (X - ref_mu) / ref_sd, ref_mu, ref_sd


Xtr, mu, sd = featurize(TR)

n = len(Xtr)
cut = int(n * 0.75)
Xa, Xv = Xtr[:cut], Xtr[cut:]

def mae(A, B):
    return float(np.mean(np.abs(A - B)))

def pca_curve(k, Xa, Xv, frac):
    m = int(len(Xa) * frac)
    sub = Xa[:m]
    if m <= k + 2:
        return None
    p = PCA(n_components=k).fit(sub)
    return mae(sub, p.inverse_transform(p.transform(sub))), mae(Xv, p.inverse_transform(p.transform(Xv))), m

def ae_curve(h, Xa, Xv, frac, seed=0):
    m = int(len(Xa) * frac)
    sub = Xa[:m]
    if m < 40:
        return None
    net = MLPRegressor(hidden_layer_sizes=h, activation="tanh", max_iter=800, random_state=seed,
                       early_stopping=False, alpha=1e-3, learning_rate_init=3e-3)
    net.fit(sub, sub)
    return mae(sub, net.predict(sub)), mae(Xv, net.predict(Xv)), m, sum(a * b for a, b in zip((24,) + h, h + (24,))) + sum(h) + 24

fr = [0.15, 0.3, 0.5, 0.7, 0.85, 1.0]
curve = {}
for k in [3, 4, 6]:
    rows = [pca_curve(k, Xa, Xv, f) for f in fr]
    curve[f"PCA k={k}"] = [r for r in rows if r]
for h in [(8, 4, 8), (16, 8, 4, 8, 16)]:
    rows = [ae_curve(h, Xa, Xv, f) for f in fr]
    curve[f"AE {'-'.join(map(str, h))}"] = [r for r in rows if r]

Xev, _, _ = featurize(EV, mu, sd)
is_norm = (EV.nhan_ung_vien == "binh_thuong").to_numpy()
pos_dev = (EV.lech_lon_nhat_pct.astype(float) > 0).to_numpy()
is_anom_up = (EV.nhan_ung_vien == "bat_thuong").to_numpy() & pos_dev

def resid_rows(model, X, kind):
    R = model.inverse_transform(model.transform(X)) if kind == "pca" else model.predict(X)
    return np.abs(X - R)

cands = {}
for k in [3, 4, 6]:
    cands[f"PCA k={k}"] = (PCA(n_components=k).fit(Xa), "pca")
for h in [(8, 4, 8), (16, 8, 4, 8, 16)]:
    net = MLPRegressor(hidden_layer_sizes=h, activation="tanh", max_iter=800, random_state=0,
                       alpha=1e-3, learning_rate_init=3e-3).fit(Xa, Xa)
    cands[f"AE {'-'.join(map(str, h))}"] = (net, "ae")

from sklearn.metrics import roc_auc_score
res = {}
for nm, (m, kind) in cands.items():
    rv = mae(Xv, m.inverse_transform(m.transform(Xv)) if kind == "pca" else m.predict(Xv))
    Rev = resid_rows(m, Xev, kind)
    re_row = Rev.mean(1)
    rn = re_row[is_norm].mean()
    ru = re_row[is_anom_up].mean()
    mask = is_norm | is_anom_up
    auc = roc_auc_score(is_anom_up[mask].astype(int), re_row[mask])
    res[nm] = dict(val=rv, re_norm=rn, re_up=ru, ratio=ru / rn, auc=auc, re_row=re_row, R=Rev, model=m, kind=kind)

best = "PCA k=3"
B = res[best]
m, kind = B["model"], B["kind"]

# contribution for the best model
R = B["R"]
contrib = np.zeros((len(EV), 8))
for i in range(8):
    contrib[:, i] = R[:, i] + R[:, 8 + i] + R[:, 16 + i]
contrib = contrib / contrib.sum(1, keepdims=True) * 100
cu = contrib[is_anom_up].mean(0)

# Plot
cmap = {"PCA k=3": "#4c78a8", "PCA k=4": "#7fa8cd", "PCA k=6": "#b8b8b8",
        "AE 8-4-8": "#e4572e", "AE 16-8-4-8-16": "#f3a58c"}

fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(13.6, 4.3))

for nm, rows in curve.items():
    ns = [r[2] for r in rows]
    a1.plot(ns, [r[1] for r in rows], "-o", color=cmap[nm], ms=3.2, lw=1.5, label=nm, zorder=3)
    a1.plot(ns, [r[0] for r in rows], "--", color=cmap[nm], lw=0.9, alpha=.65, zorder=2)
a1.set_xlabel("Số giờ dùng huấn luyện", labelpad=9)
a1.set_ylabel("Sai số tái tạo (MAE)", labelpad=9)
a1.set_title("Nét liền = validation khỏe, nét đứt = train", fontsize=8.3, loc="left")
a1.legend(frameon=False, fontsize=6.3, loc="upper right")

nms = list(res)
rt = [res[n]["ratio"] for n in nms]
yy = np.arange(len(nms))[::-1]

a2.barh(yy, rt, color=[cmap[n] for n in nms], height=.6, zorder=3)
a2.axvline(1.0, color="#c00", lw=1.0, ls="--", zorder=4)
for yi, v in zip(yy, rt):
    a2.text(v + .012, yi, f"{v:.2f}×", va="center", fontsize=7.2, fontweight="bold")
a2.set_yticks(yy)
a2.set_yticklabels(nms, fontsize=6.8)
a2.set_xlabel("Tỉ số residual: bất thường / bình thường", labelpad=9)
a2.set_xlim(0.85, 1.45)
a2.set_title("Tiêu chí paper: residual phải TĂNG khi có lỗi", fontsize=8.3, loc="left")
a2.text(1.005, 0.5, "1.0 = không tách được", fontsize=6.4, color="#c00", ha="left", va="center")

cc = [(s.replace("29VT-", ""), cu[i]) for i, s in enumerate(sens)]
cc.sort(key=lambda x: x[1])
y3 = np.arange(len(cc))
col = ["#e4572e" if n.startswith("2001") else "#b8b8b8" for n, _ in cc]
a3.barh(y3, [c[1] for c in cc], color=col, height=.62, zorder=3)
for yi, (n, v) in zip(y3, cc):
    a3.text(v + .35, yi, f"{v:.1f}%", va="center", fontsize=7.2,
            fontweight="bold" if n.startswith("2001") else "normal")
a3.set_yticks(y3)
a3.set_yticklabels([c[0] for c in cc], fontsize=7)
a3.set_xlabel("Đóng góp vào điểm bất thường (%)", labelpad=9)
a3.set_xlim(0, 29)
a3.set_title("Mô hình tự chỉ vào ổ 2001 — không được dạy trước", fontsize=8.3, loc="left")

fig.tight_layout()
fig.savefig("hqc_model_selection.png", dpi=300, bbox_inches="tight")