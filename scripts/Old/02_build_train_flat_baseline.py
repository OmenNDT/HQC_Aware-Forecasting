"""02_build_train_flat_baseline.py — Dựng nền train phẳng 20/02–22/03/2026 (743 giờ) — thay nền cũ bị nhiễm

Sinh tự động từ lineage artifact: HQC_train_healthy_flat.csv
version_id: 1eb375fe-a625-4aed-a5a2-a970b48759f2
Môi trường: conda env 'python'

CẢNH BÁO: đây là mã trích từ lineage, đường dẫn dữ liệu là đường dẫn TUYỆT ĐỐI
của máy gốc. Kiểm lại biến đường dẫn trước khi chạy lại.
"""

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPRegressor

# (helper apply_figure_style() của skill figure-style — nạp qua skill, không cần trong script)
from_skill_note=True

p = "/home/sontn/Projects/HQC_Aware-Forecasting/Dataraw/PI Data.xlsx"

# Load vibration sheet (51_Vib180d)
Vfull = pd.read_excel(p, sheet_name="51_Vib180d", header=None, skiprows=7)
sensors = ["29VT-2001X", "29VT-2001Y", "29VT-2003X", "29VT-2003Y",
           "29VT-2005X", "29VT-2005Y", "29VT-2007X", "29VT-2007Y"]
V = pd.DataFrame({"ts": pd.to_datetime(Vfull.iloc[:, 0], errors="coerce")})
for i, s in enumerate(sensors):
    V[f"amp_{s}"] = pd.to_numeric(Vfull.iloc[:, 1 + i], errors="coerce")
    V[f"ph_{s}"] = pd.to_numeric(Vfull.iloc[:, 9 + i], errors="coerce")
V = V.dropna(subset=["ts"]).set_index("ts").sort_index()

# Load process/load sheet (33_Aligned)
hdr = pd.read_excel(p, sheet_name="33_Aligned", header=None, skiprows=7, nrows=2)
names = [str(v) for v in hdr.iloc[1].tolist()]
D = pd.read_excel(p, sheet_name="33_Aligned", header=None, skiprows=9)
D = D.iloc[:, :12]
D.columns = ["ts"] + names[1:12]
D["ts"] = pd.to_datetime(D["ts"], errors="coerce")
D = D.dropna(subset=["ts"])
num = D.drop(columns=["ts"]).apply(pd.to_numeric, errors="coerce")

# Clean junk values
clean = num.copy()
for c in clean.columns:
    m = (clean[c].abs() > 0) & (clean[c].abs() < 1e-10)
    clean.loc[m, c] = np.nan
clean.loc[clean["29SIC2001A"] == 0, "29SIC2001A"] = np.nan

# Build aligned matrix (hourly)
amp_cols = [f"amp_{s}" for s in sensors]
ph_cols = [f"ph_{s}" for s in sensors]
load_cols = ["29SIC2001", "29SIC2001A", "29FI2005", "29FI2006", "29PI2011",
             "29PI2012", "29PDI2007A", "29LI2002A", "29TI2030", "29TI2031", "29TI2026A"]

# Resample load to hourly
L = clean.copy()
L.index = pd.DatetimeIndex(D["ts"].values)
Lh = L.resample("1h").median()

# Resample vibration to hourly
Vh = V.copy()
Vh.index = Vh.index.round("1h")
Vh = Vh[~Vh.index.duplicated(keep="first")]

# Join
M = Vh.join(Lh, how="inner")

# Gates
g_run = (M[amp_cols] > 3).sum(axis=1) >= 6
g_load = M["29FI2005"] >= 20000
g_valid = M[amp_cols + ph_cols].notna().all(axis=1) & M[["29SIC2001", "29FI2005"]].notna().all(axis=1)
gate = g_run & g_load & g_valid

# Exclude transition window
trans = (M.index >= pd.Timestamp("2026-05-28")) & (M.index <= pd.Timestamp("2026-06-13 23:00"))

G = M[gate & ~trans].copy()

# Flat baseline window
TR2 = G.loc["2026-02-20":"2026-03-22"].copy()

# Export train file
TR2_out = TR2[amp_cols + ph_cols + load_cols].copy()
TR2_out.index.name = "timestamp"
TR2_out.columns = [c.replace("amp_", "1X_Amp_").replace("ph_", "1X_Phase_") for c in TR2_out.columns]
TR2_out.round(4).to_csv("HQC_train_healthy_flat.csv")
print(f"Wrote HQC_train_healthy_flat.csv: {len(TR2_out)} rows x {len(TR2_out.columns)} cols")
print(f"Range: {TR2_out.index.min()} -> {TR2_out.index.max()}")