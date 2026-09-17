"""05_score_and_contribution.py — Tính anomaly score 0-100 + sensor contribution trên tập đánh giá

Sinh tự động từ lineage artifact: HQC_eval_scored_flat.csv
version_id: 76b3c78a-0139-4b34-9691-0b76fffd9aeb
Môi trường: conda env 'python'

CẢNH BÁO: đây là mã trích từ lineage, đường dẫn dữ liệu là đường dẫn TUYỆT ĐỐI
của máy gốc. Kiểm lại biến đường dẫn trước khi chạy lại.
"""

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import roc_auc_score

# (helper apply_figure_style() của skill figure-style — nạp qua skill, không cần trong script)
from_skill_note=True

p = "/home/sontn/Projects/HQC_Aware-Forecasting/Dataraw/PI Data.xlsx"

# Load vibration sheet
Vfull = pd.read_excel(p, sheet_name="51_Vib180d", header=None, skiprows=7)
sens = ["29VT-2001X", "29VT-2001Y", "29VT-2003X", "29VT-2003Y",
        "29VT-2005X", "29VT-2005Y", "29VT-2007X", "29VT-2007Y"]
V = pd.DataFrame({"ts": pd.to_datetime(Vfull.iloc[:, 0], errors="coerce")})
for i, s in enumerate(sens):
    V[f"amp_{s}"] = pd.to_numeric(Vfull.iloc[:, 1 + i], errors="coerce")
    V[f"ph_{s}"] = pd.to_numeric(Vfull.iloc[:, 9 + i], errors="coerce")
V = V.dropna(subset=["ts"]).set_index("ts").sort_index()
amp_cols = [f"amp_{s}" for s in sens]
ph_cols = [f"ph_{s}" for s in sens]

# Load process (aligned) sheet
hdr = pd.read_excel(p, sheet_name="33_Aligned", header=None, skiprows=7, nrows=2)
names = [str(v) for v in hdr.iloc[1].tolist()]
D = pd.read_excel(p, sheet_name="33_Aligned", header=None, skiprows=9)
D = D.iloc[:, :12]
D.columns = ["ts"] + names[1:12]
D["ts"] = pd.to_datetime(D["ts"], errors="coerce")
D = D.dropna(subset=["ts"])
num = D.drop(columns=["ts"]).apply(pd.to_numeric, errors="coerce")

# Clean junk patterns
clean = num.copy()
for c in clean.columns:
    m = (clean[c].abs() > 0) & (clean[c].abs() < 1e-10)
    clean.loc[m, c] = np.nan
clean.loc[clean["29SIC2001A"] == 0, "29SIC2001A"] = np.nan

load_cols = ["29SIC2001", "29SIC2001A", "29FI2005", "29FI2006", "29PI2011",
             "29PI2012", "29PDI2007A", "29LI2002A", "29TI2030", "29TI2031", "29TI2026A"]

# Build aligned hourly matrix
L = clean.copy()
L.index = pd.DatetimeIndex(D["ts"].values)
Lh = L.resample("1h").median()

Vh = V.copy()
Vh.index = Vh.index.round("1h")
Vh = Vh[~Vh.index.duplicated(keep="first")]
M = Vh.join(Lh, how="inner")

# Gates
g_run = (M[amp_cols] > 3).sum(axis=1) >= 6
g_load = M["29FI2005"] >= 20000
g_valid = M[amp_cols + ph_cols].notna().all(axis=1) & M[["29SIC2001", "29FI2005"]].notna().all(axis=1)
gate = g_run & g_load & g_valid
trans = (M.index >= pd.Timestamp("2026-05-28")) & (M.index <= pd.Timestamp("2026-06-13 23:00"))
G = M[gate & ~trans].copy()

# Featurize function
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

# Build flat baseline (20/02 - 22/03)
# First build full train for featurize reference
TR_amp_cols = {f"1X_Amp_{s}": f"amp_{s}" for s in sens}
TR_ph_cols = {f"1X_Phase_{s}": f"ph_{s}" for s in sens}

# Build TR dataframe from G (05/02 - 31/03)
TR_full = G.loc[:"2026-03-31"].copy()
TR_full_renamed = TR_full.rename(columns={f"amp_{s}": f"1X_Amp_{s}" for s in sens})
TR_full_renamed = TR_full_renamed.rename(columns={f"ph_{s}": f"1X_Phase_{s}" for s in sens})

# Build flat train (20/02 - 22/03)
TR2_raw = G.loc["2026-02-20":"2026-03-22"].copy()
TR2 = TR2_raw.rename(columns={f"amp_{s}": f"1X_Amp_{s}" for s in sens})
TR2 = TR2.rename(columns={f"ph_{s}": f"1X_Phase_{s}" for s in sens})

Xtr2, mu2, sd2 = featurize(TR2)
n2 = len(Xtr2)
cut2 = int(n2 * 0.75)
Xa2, Xv2 = Xtr2[:cut2], Xtr2[cut2:]

fr = [0.15, 0.3, 0.5, 0.7, 0.85, 1.0]

# Train models on flat baseline
cands2 = {}
for k in [2, 3, 4, 6]:
    cands2[f"PCA k={k}"] = (PCA(n_components=k).fit(Xa2), "pca")
for h in [(8, 4, 8), (16, 8, 4, 8, 16)]:
    net = MLPRegressor(hidden_layer_sizes=h, activation="tanh", max_iter=800,
                       random_state=0, alpha=1e-3, learning_rate_init=3e-3).fit(Xa2, Xa2)
    cands2[f"AE {'-'.join(map(str, h))}"] = (net, "ae")

# Load eval data
EV = pd.read_csv("/home/sontn/.claude-science/orgs/49e3c671-cbbe-4f16-8bad-8cba412d2a77/artifacts/proj_0c140d6162d4/0c353bbe-47bb-45cf-bc88-46c1e3f51393/vf282060f_HQC_eval_expert.csv")
EV["timestamp"] = pd.to_datetime(EV["timestamp"])

# Featurize eval with flat baseline normalization
Xev2, _, _ = featurize(EV, mu2, sd2)

is_norm = (EV.nhan_ung_vien == "binh_thuong").to_numpy()
pos_dev = (EV.lech_lon_nhat_pct.astype(float) > 0).to_numpy()
is_anom_up = (EV.nhan_ung_vien == "bat_thuong").to_numpy() & pos_dev
is_anom_dn = (EV.nhan_ung_vien == "bat_thuong").to_numpy() & ~pos_dev

mask = is_norm | is_anom_up
res2 = {}
for nm, (m_, kind) in cands2.items():
    rv = mae(Xv2, m_.inverse_transform(m_.transform(Xv2)) if kind == "pca" else m_.predict(Xv2))
    rt_ = mae(Xa2, m_.inverse_transform(m_.transform(Xa2)) if kind == "pca" else m_.predict(Xa2))
    R = resid_rows(m_, Xev2, kind)
    re_row = R.mean(1)
    rn = re_row[is_norm].mean()
    ru = re_row[is_anom_up].mean()
    auc = roc_auc_score(is_anom_up[mask].astype(int), re_row[mask])
    res2[nm] = dict(val=rv, gap=rv - rt_, re_norm=rn, re_up=ru, ratio=ru / rn,
                    auc=auc, re_row=re_row, R=R, model=m_, kind=kind)

# Best model: PCA k=6
best2 = "PCA k=6"
B2 = res2[best2]

# Compute anomaly score
re_v2 = resid_rows(B2["model"], Xv2, B2["kind"]).mean(1)
lo3, hi3 = np.percentile(re_v2, 5), np.percentile(re_v2, 95)

def score3(re):
    z = (np.log(re + 1e-6) - np.log(lo3)) / (np.log(hi3 * 3) - np.log(lo3))
    return np.clip(100 / (1 + np.exp(-4 * (z - 0.5))), 0, 100)

# Compute contributions
R2 = B2["R"]
c2 = np.zeros((len(EV), 8))
for i in range(8):
    c2[:, i] = R2[:, i] + R2[:, 8 + i] + R2[:, 16 + i]
c2 = c2 / c2.sum(1, keepdims=True) * 100

# Build output
EV2 = EV[["timestamp", "nhan_ung_vien", "lech_lon_nhat_pct", "cam_bien_lech_nhat"]].copy()
EV2["anomaly_score"] = score3(B2["re_row"]).round(1)
EV2["vung"] = pd.cut(EV2.anomaly_score, [-1, 40, 60, 101], labels=["Normal", "Warning", "Danger"])
for i, s in enumerate(sens):
    EV2[f"contrib_{s}"] = c2[:, i].round(1)
EV2["cam_bien_dong_gop_nhat"] = [sens[i] for i in c2.argmax(1)]

EV2.to_csv("HQC_eval_scored_flat.csv", index=False)