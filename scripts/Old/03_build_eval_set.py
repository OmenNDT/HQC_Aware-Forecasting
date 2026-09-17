"""03_build_eval_set.py — Dựng tập đánh giá 350 mẫu + nhãn ứng viên + 3 ví dụ mẫu cho chuyên gia PDM

Sinh tự động từ lineage artifact: HQC_eval_expert.csv
version_id: bbf0f343-3cba-41f1-91c4-eb9c377350ce
Môi trường: conda env 'python'

CẢNH BÁO: đây là mã trích từ lineage, đường dẫn dữ liệu là đường dẫn TUYỆT ĐỐI
của máy gốc. Kiểm lại biến đường dẫn trước khi chạy lại.
"""

import pandas as pd
import numpy as np
import os

# (helper apply_figure_style() của skill figure-style — nạp qua skill, không cần trong script)
from_skill_note=True

p = "/home/sontn/Projects/HQC_Aware-Forecasting/Dataraw/PI Data.xlsx"

# Load vibration sheet
Vfull = pd.read_excel(p, sheet_name="51_Vib180d", header=None, skiprows=7)
sensors = ["29VT-2001X", "29VT-2001Y", "29VT-2003X", "29VT-2003Y",
           "29VT-2005X", "29VT-2005Y", "29VT-2007X", "29VT-2007Y"]
V = pd.DataFrame({"ts": pd.to_datetime(Vfull.iloc[:, 0], errors="coerce")})
for i, s in enumerate(sensors):
    V[f"amp_{s}"] = pd.to_numeric(Vfull.iloc[:, 1 + i], errors="coerce")
    V[f"ph_{s}"] = pd.to_numeric(Vfull.iloc[:, 9 + i], errors="coerce")
V = V.dropna(subset=["ts"]).set_index("ts").sort_index()
amp_cols = [f"amp_{s}" for s in sensors]
ph_cols = [f"ph_{s}" for s in sensors]

# Load process/load sheet
raw = pd.read_excel(p, sheet_name="33_Aligned", header=None, nrows=8)
hdr = pd.read_excel(p, sheet_name="33_Aligned", header=None, skiprows=7, nrows=2)
groups = [str(v) for v in hdr.iloc[0].tolist()]
names = [str(v) for v in hdr.iloc[1].tolist()]
D_raw = pd.read_excel(p, sheet_name="33_Aligned", header=None, skiprows=9)
D_raw = D_raw.iloc[:, :12]
D_raw.columns = ["ts"] + names[1:12]
D_raw["ts"] = pd.to_datetime(D_raw["ts"], errors="coerce")
D = D_raw.dropna(subset=["ts"])
num = D.drop(columns=["ts"]).apply(pd.to_numeric, errors="coerce")

# Clean junk patterns
clean = num.copy()
# rule 1: junk pattern 6.4e-17 -> NaN
for c in clean.columns:
    m = (clean[c].abs() > 0) & (clean[c].abs() < 1e-10)
    clean.loc[m, c] = np.nan
# rule 2: 29SIC2001A = 0 is junk
clean.loc[clean["29SIC2001A"] == 0, "29SIC2001A"] = np.nan

# Align vibration and load on hourly grid
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

# Training window: nền khỏe
base = G.loc[:"2026-03-31"]
load_cols = ["29SIC2001", "29SIC2001A", "29FI2005", "29FI2006", "29PI2011",
             "29PI2012", "29PDI2007A", "29LI2002A", "29TI2030", "29TI2031", "29TI2026A"]

TR = G.loc[:"2026-03-31", amp_cols + ph_cols + load_cols].copy()
TR.index.name = "timestamp"
TR.columns = [c.replace("amp_", "1X_Amp_").replace("ph_", "1X_Phase_") for c in TR.columns]
train_idx = set(TR.index)

# Baseline limits: p1-p99 from healthy window
lim = {s: (base[f"amp_{s}"].quantile(.01), base[f"amp_{s}"].quantile(.99)) for s in sensors}

# Build eval dataset
E_source = M[g_valid].copy()

def dev_ratio(row):
    d = {}
    for s in sensors:
        lo, hi = lim[s]
        v = row[f"amp_{s}"]
        d[s] = (v - hi) / hi * 100 if v > hi else ((v - lo) / lo * 100 if v < lo else 0.0)
    return d

rows = []
for ts, row in E_source.iterrows():
    dv = dev_ratio(row)
    worst = max(dv, key=lambda k: abs(dv[k]))
    running = (row[amp_cols] > 3).sum() >= 6
    loaded = row["29FI2005"] >= 20000
    rows.append({"timestamp": ts, "may_chay": int(running), "co_tai": int(loaded),
                 **{f"1X_Amp_{s}": round(row[f"amp_{s}"], 3) for s in sensors},
                 **{f"1X_Phase_{s}": round(row[f"ph_{s}"], 2) for s in sensors},
                 **{c: round(row[c], 3) if pd.notna(row[c]) else np.nan for c in load_cols},
                 "lech_lon_nhat_pct": round(dv[worst], 1), "cam_bien_lech_nhat": worst,
                 "so_cam_bien_ngoai_dai": sum(1 for v in dv.values() if abs(v) > 0)})
EV = pd.DataFrame(rows)

def cand(r):
    if not r["may_chay"] or not r["co_tai"]:
        return "loai_bo_may_dung_hoac_tai_thap"
    if abs(r["lech_lon_nhat_pct"]) >= 25:
        return "bat_thuong"
    if abs(r["lech_lon_nhat_pct"]) >= 10:
        return "can_xem"
    return "binh_thuong"

EV["nhan_ung_vien"] = EV.apply(cand, axis=1)
EV["CHUYEN_GIA_xac_nhan"] = ""
EV["CHUYEN_GIA_nhan_dung"] = ""
EV["CHUYEN_GIA_ghi_chu"] = ""

# Exclude training rows, sample 350
pool = EV[~EV["timestamp"].isin(train_idx)].copy()
rng = np.random.default_rng(42)

def take(df, n):
    if len(df) <= n:
        return df
    df = df.sort_values("timestamp").reset_index(drop=True)
    edges = np.linspace(0, len(df), n + 1).astype(int)
    pick = [rng.integers(edges[i], edges[i + 1]) for i in range(n) if edges[i + 1] > edges[i]]
    return df.iloc[sorted(set(pick))]

norm = take(pool[pool["nhan_ung_vien"] == "binh_thuong"], 150)
anom = take(pool[pool["nhan_ung_vien"] == "bat_thuong"], 200)
EVAL = pd.concat([norm, anom]).sort_values("timestamp").reset_index(drop=True)

# Add example annotations
ex = {
    "2026-04-01 00:00:00": ("Đúng", "binh_thuong",
                             "VÍ DỤ MẪU 1 (máy khỏe) — Cả 8 kênh 1X Amp đều nằm trong dải nền; pha ổn định "
                             "(2003X 224° so nền 218°, lệch 6°). Tải bình thường 4820 rpm. Không có dấu hiệu gì "
                             "→ đồng ý nhãn 'binh_thuong'."),
    "2026-05-28 13:00:00": ("Đúng", "bat_thuong",
                             "VÍ DỤ MẪU 2 (bất thường THẬT) — 2001X leo 35,4 µm (nền 11,3-18,3, tức GẤP ĐÔI) và "
                             "2001Y 32,6 µm (nền 10,9-17,2). Pha 2001X dịch 82,7° so nền 105,6° (lệch 23°) → điểm "
                             "nặng đang đổi hướng. 6 kênh ngoài dải. Ổ 2001 rung tăng mạnh trong khi các ổ khác "
                             "không tăng → nghi mất cân bằng đang tiến triển ở ổ 2001 → đồng ý 'bat_thuong'."),
    "2026-06-03 09:00:00": ("Sai", "binh_thuong",
                             "VÍ DỤ MẪU 3 (luật SAI - chuyên gia bác) — Luật gắn 'bat_thuong' vì lệch -31,8% ngoài "
                             "dải nền, NHƯNG lệch xuống THẤP: 2001X chỉ 7,9 µm (nền 11,3-18,3), 2001Y 7,5 µm. Rung "
                             "THẤP HƠN bình thường KHÔNG phải hư hỏng. Đây là ngày 3 sau khi khởi động lại (máy dừng "
                             "29-31/05) — máy chạy êm hơn trước khi dừng, hợp lý về vận hành. Tải bình thường 4790 rpm. "
                             "→ BÁC nhãn luật, nhãn đúng là 'binh_thuong'."),
}

E = EVAL.copy()
for c in ["CHUYEN_GIA_xac_nhan", "CHUYEN_GIA_nhan_dung", "CHUYEN_GIA_ghi_chu"]:
    E[c] = E[c].astype(object)
    E.loc[E[c].isna(), c] = ""
    E[c] = E[c].replace("nan", "")

for ts, (xn, nd, gc) in ex.items():
    m = E.timestamp == pd.Timestamp(ts)
    E.loc[m, "CHUYEN_GIA_xac_nhan"] = xn
    E.loc[m, "CHUYEN_GIA_nhan_dung"] = nd
    E.loc[m, "CHUYEN_GIA_ghi_chu"] = gc

E["VI_DU_MAU"] = ""
E.loc[E.timestamp.isin([pd.Timestamp(t) for t in ex]), "VI_DU_MAU"] = "<<< VÍ DỤ MẪU - ĐÃ ĐIỀN SẴN"

cols = ["VI_DU_MAU"] + [c for c in E.columns if c != "VI_DU_MAU"]
E = E[cols]
E["_ord"] = (E.VI_DU_MAU == "").astype(int)
E = E.sort_values(["_ord", "timestamp"]).drop(columns="_ord").reset_index(drop=True)

E.to_csv("HQC_eval_expert.csv", index=False)
print("saved HQC_eval_expert.csv:", os.path.getsize("HQC_eval_expert.csv"), "bytes")