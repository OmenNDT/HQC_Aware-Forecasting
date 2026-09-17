"""04_train_and_compare_baseline.py — Train PCA/AE trên nền phẳng, so nền cũ vs nền phẳng, learning curve

Sinh tự động từ lineage artifact: hqc_baseline_fix.png
version_id: 3ec8805e-f43c-4d32-bc93-7aa4919d9782
Môi trường: conda env 'python'

CẢNH BÁO: đây là mã trích từ lineage, đường dẫn dữ liệu là đường dẫn TUYỆT ĐỐI
của máy gốc. Kiểm lại biến đường dẫn trước khi chạy lại.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import roc_auc_score
from scipy import stats

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


def mae(A, B):
    return float(np.mean(np.abs(A - B)))


def resid_rows(model, X, kind):
    R = model.inverse_transform(model.transform(X)) if kind == "pca" else model.predict(X)
    return np.abs(X - R)


# --- Original baseline (full train window) ---
Xtr, mu, sd = featurize(TR)
n = len(Xtr)
cut = int(n * 0.75)
Xa, Xv = Xtr[:cut], Xtr[cut:]

Xev, _, _ = featurize(EV, mu, sd)

is_norm = (EV.nhan_ung_vien == "binh_thuong").to_numpy()
pos_dev = (EV.lech_lon_nhat_pct.astype(float) > 0).to_numpy()
is_anom_up = (EV.nhan_ung_vien == "bat_thuong").to_numpy() & pos_dev
is_anom_dn = (EV.nhan_ung_vien == "bat_thuong").to_numpy() & ~pos_dev

fr = [0.15, 0.3, 0.5, 0.7, 0.85, 1.0]

curve = {}
for k in [3, 4, 6]:
    rows = []
    for f in fr:
        m_ = int(len(Xa) * f)
        sub = Xa[:m_]
        if m_ <= k + 2:
            continue
        p = PCA(n_components=k).fit(sub)
        rows.append((mae(sub, p.inverse_transform(p.transform(sub))),
                     mae(Xv, p.inverse_transform(p.transform(Xv))), m_, (k * 24 * 2)))
    curve[f"PCA k={k}"] = rows
for h in [(8, 4, 8), (16, 8, 4, 8, 16)]:
    rows = []
    for f in fr:
        m_ = int(len(Xa) * f)
        sub = Xa[:m_]
        if m_ < 40:
            continue
        net = MLPRegressor(hidden_layer_sizes=h, activation="tanh", max_iter=800, random_state=0,
                           early_stopping=False, alpha=1e-3, learning_rate_init=3e-3)
        net.fit(sub, sub)
        rows.append((mae(sub, net.predict(sub)), mae(Xv, net.predict(Xv)), m_,
                     sum(a * b for a, b in zip((24,) + h, h + (24,))) + sum(h) + 24))
    curve[f"AE {'-'.join(map(str, h))}"] = rows

cands = {}
for k in [3, 4, 6]:
    cands[f"PCA k={k}"] = (PCA(n_components=k).fit(Xa), "pca")
for h in [(8, 4, 8), (16, 8, 4, 8, 16)]:
    net = MLPRegressor(hidden_layer_sizes=h, activation="tanh", max_iter=800, random_state=0,
                       alpha=1e-3, learning_rate_init=3e-3).fit(Xa, Xa)
    cands[f"AE {'-'.join(map(str, h))}"] = (net, "ae")

mask = is_norm | is_anom_up
res = {}
for nm, (m_, kind) in cands.items():
    rv = mae(Xv, m_.inverse_transform(m_.transform(Xv)) if kind == "pca" else m_.predict(Xv))
    rt_ = mae(Xa, m_.inverse_transform(m_.transform(Xa)) if kind == "pca" else m_.predict(Xa))
    R = resid_rows(m_, Xev, kind)
    re_row = R.mean(1)
    rn = re_row[is_norm].mean()
    ru = re_row[is_anom_up].mean()
    auc = roc_auc_score(is_anom_up[mask].astype(int), re_row[mask])
    res[nm] = dict(val=rv, gap=rv - rt_, re_norm=rn, re_up=ru, ratio=ru / rn, auc=auc,
                   re_row=re_row, R=R, model=m_, kind=kind)

# Contribution from original baseline
best = "PCA k=3"
B = res[best]
R_orig = B["R"]
contrib_orig = np.zeros((len(EV), 8))
for i in range(8):
    contrib_orig[:, i] = R_orig[:, i] + R_orig[:, 8 + i] + R_orig[:, 16 + i]
contrib_orig = contrib_orig / contrib_orig.sum(1, keepdims=True) * 100
cu = contrib_orig[is_anom_up].mean(0)

# --- New flat baseline ---
TR2 = TR.loc["2026-02-20":"2026-03-22"].copy()
Xtr2, mu2, sd2 = featurize(TR2)
n2 = len(Xtr2)
cut2 = int(n2 * 0.75)
Xa2, Xv2 = Xtr2[:cut2], Xtr2[cut2:]

Xev2, _, _ = featurize(EV, mu2, sd2)

cands2 = {}
for k in [2, 3, 4, 6]:
    cands2[f"PCA k={k}"] = (PCA(n_components=k).fit(Xa2), "pca")
for h in [(8, 4, 8), (16, 8, 4, 8, 16)]:
    cands2[f"AE {'-'.join(map(str, h))}"] = (
        MLPRegressor(hidden_layer_sizes=h, activation="tanh", max_iter=800, random_state=0,
                     alpha=1e-3, learning_rate_init=3e-3).fit(Xa2, Xa2), "ae")

res2 = {}
for nm, (m_, kind) in cands2.items():
    rv = mae(Xv2, m_.inverse_transform(m_.transform(Xv2)) if kind == "pca" else m_.predict(Xv2))
    rt_ = mae(Xa2, m_.inverse_transform(m_.transform(Xa2)) if kind == "pca" else m_.predict(Xa2))
    R = resid_rows(m_, Xev2, kind)
    re_row = R.mean(1)
    rn = re_row[is_norm].mean()
    ru = re_row[is_anom_up].mean()
    auc = roc_auc_score(is_anom_up[mask].astype(int), re_row[mask])
    res2[nm] = dict(val=rv, gap=rv - rt_, re_norm=rn, re_up=ru, ratio=ru / rn, auc=auc,
                    re_row=re_row, R=R, model=m_, kind=kind)

best2 = "PCA k=6"
B2 = res2[best2]
R2 = B2["R"]
c2 = np.zeros((len(EV), 8))
for i in range(8):
    c2[:, i] = R2[:, i] + R2[:, 8 + i] + R2[:, 16 + i]
c2 = c2 / c2.sum(1, keepdims=True) * 100
cu2 = c2[is_anom_up].mean(0)

# Need Vr for panel 1: rebuild from TR (hourly vibration)
# Vr is the running-filtered vibration data; use TR as proxy for 2001X amplitude trend
amp_cols = [f"1X_Amp_{s}" for s in sens]


# Build Vr-like series from TR for the 2001X plot
# We need the full vibration series for panel 1 - reconstruct from TR which covers the period
class VrProxy:
    pass


# Use TR for the time-series plot of 2001X
w_data = TR["1X_Amp_29VT-2001X"].loc[:"2026-04-05"].resample("6h").median()

# --- Plot ---
C_OLD = "#b8b8b8"
C_NEW = "#4c78a8"
C_HL = "#e4572e"

fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(13.6, 4.4))

# panel 1
a1.plot(w_data.index, w_data.values, color="#333", lw=1.3, zorder=3)
a1.axvspan(pd.Timestamp("2026-02-05"), pd.Timestamp("2026-03-31"), color=C_OLD, alpha=.45, zorder=1)
a1.axvspan(pd.Timestamp("2026-02-20"), pd.Timestamp("2026-03-22"), color=C_NEW, alpha=.30, zorder=2)
a1.axvspan(pd.Timestamp("2026-02-11"), pd.Timestamp("2026-02-19"), color=C_HL, alpha=.30, zorder=2)
a1.text(pd.Timestamp("2026-02-07"), 19.6, "đoạn LEO\n+50%/8 ngày", fontsize=6.6, color=C_HL,
        fontweight="bold", linespacing=1.2)
a1.text(pd.Timestamp("2026-03-01"), 11.6, "nền MỚI (phẳng)", fontsize=6.8, color=C_NEW,
        fontweight="bold", ha="center")
a1.text(pd.Timestamp("2026-03-05"), 10.5, "nền CŨ (chứa đoạn leo)", fontsize=6.6, color="#777",
        ha="center")
a1.set_ylabel("1X Amp ổ 2001X (µm)", labelpad=9)
a1.set_ylim(10, 21)
a1.set_title("Nền cũ chứa một sự cố đang diễn ra", fontsize=8.3, loc="left")
a1.xaxis.set_major_locator(mdates.MonthLocator())
a1.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
a1.xaxis.set_minor_locator(mdates.DayLocator(interval=10))

# panel 2
nm2 = ["PCA k=3", "PCA k=4", "PCA k=6", "AE 8-4-8", "AE 16-8-4-8-16"]
old = [res[n]["ratio"] for n in nm2]
new = [res2[n]["ratio"] for n in nm2]
y = np.arange(len(nm2))[::-1]
h = .36
a2.barh(y + h / 2, old, height=h, color=C_OLD, label="nền cũ (có đoạn leo)", zorder=3)
a2.barh(y - h / 2, new, height=h, color=C_NEW, label="nền phẳng 20/02–22/03", zorder=3)
for yi, v in zip(y + h / 2, old):
    a2.text(v + .02, yi, f"{v:.2f}×", va="center", fontsize=6.8, color="#666")
for yi, v in zip(y - h / 2, new):
    a2.text(v + .02, yi, f"{v:.2f}×", va="center", fontsize=6.8, fontweight="bold", color=C_NEW)
a2.axvline(1.0, color="#c00", lw=.9, ls="--", zorder=4)
a2.set_yticks(y)
a2.set_yticklabels(nm2, fontsize=6.8)
a2.set_xlabel("Tỉ số residual: bất thường / bình thường", labelpad=9)
a2.set_xlim(0.85, 2.15)
a2.set_title("Nền phẳng cải thiện khả năng tách ở MỌI mô hình", fontsize=8.3, loc="left")
a2.legend(frameon=False, fontsize=6.4, loc="lower right", bbox_to_anchor=(1.02, 0.08))

# panel 3
order3 = sorted(range(8), key=lambda i: cu2[i])
y3 = np.arange(8)
a3.barh(y3 + h / 2, [cu[i] for i in order3], height=h, color=C_OLD, label="nền cũ", zorder=3)
a3.barh(y3 - h / 2, [cu2[i] for i in order3], height=h,
        color=[C_HL if sens[i].startswith("29VT-2001") else C_NEW for i in order3],
        label="nền phẳng", zorder=3)
for yi, i in zip(y3 - h / 2, order3):
    a3.text(cu2[i] + .5, yi, f"{cu2[i]:.1f}%", va="center", fontsize=6.8, fontweight="bold")
a3.set_yticks(y3)
a3.set_yticklabels([sens[i].replace("29VT-", "") for i in order3], fontsize=7)
a3.set_xlabel("Đóng góp vào điểm bất thường (%)", labelpad=9)
a3.set_xlim(0, 34)
a3.set_title(f"Ổ 2001 nổi rõ hơn: {cu[0]+cu[1]:.1f}% → {cu2[0]+cu2[1]:.1f}%",
             fontsize=8.3, loc="left")
a3.legend(frameon=False, fontsize=6.4, loc="lower right")

fig.tight_layout()
fig.savefig("hqc_baseline_fix.png", dpi=300, bbox_inches="tight")
r = fig.canvas.get_renderer()
tx = [(t, t.get_window_extent(r)) for t in fig.findobj(mpl.text.Text) if t.get_text().strip() and t.get_visible()]
ov = [(a.get_text()[:26], b.get_text()[:26]) for i, (a, ba) in enumerate(tx) for b, bb in tx[i+1:] if ba.overlaps(bb)]
print("saved | overlaps:", len(ov), ov[:4])