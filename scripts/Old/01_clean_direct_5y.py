"""01_clean_direct_5y.py — Làm sạch dữ liệu Direct 5 năm của máy P29201A

Vào : Dataraw/P29201A-5y-2026.csv (24 block header, 23 cảm biến duy nhất)
Ra  : Dataclean/P29201A_clean_long.{csv,parquet}, P29201A_wide_8h.parquet,
      P29201A_wide_weekly.parquet, quality_manifest.csv

BẪY QUAN TRỌNG: file có 24 block, mỗi block một cảm biến với header riêng.
Đọc cả file bằng MỘT header là SAI — nó gộp 23 cảm biến thành một chuỗi và sinh
artefact giả (giá trị -32768, cadence 6 phút, 'bước nhảy' không tồn tại).
Phải tách theo dòng bắt đầu bằng 'Machine Name'.
"""
import pandas as pd, numpy as np, re, os

ROOT = "/home/sontn/Projects/HQC_Aware-Forecasting"   # <-- SỬA nếu chạy máy khác
SRC  = f"{ROOT}/Dataraw/P29201A-5y-2026.csv"
OUT  = f"{ROOT}/Dataclean"
os.makedirs(OUT, exist_ok=True)

raw = open(SRC, encoding="utf-8-sig", errors="ignore").read().splitlines()

# --- 1) Tách block theo 'Machine Name' -------------------------------------
starts = [i for i, l in enumerate(raw) if l.startswith("Machine Name")]
starts.append(len(raw))
recs = []
for bi in range(len(starts) - 1):
    b0, b1 = starts[bi], starts[bi + 1]
    point = None
    for j in range(b0, min(b0 + 8, b1)):
        m = re.match(r'Point Name,([^,]+)', raw[j])
        if m:
            point = m.group(1).strip().strip('"')
            break
    if point is None:
        continue
    for l in raw[b0:b1]:
        parts = l.split(",")
        if len(parts) >= 2 and re.match(r'\d{1,2}/\d{1,2}/\d{4}', parts[0]):
            try:
                recs.append((point, pd.to_datetime(parts[0], errors="coerce"),
                             float(parts[1])))
            except ValueError:
                pass
long = pd.DataFrame(recs, columns=["sensor", "ts", "raw_val"]).dropna(subset=["ts"])

# --- 2) Khử sentinel + luật vật lý theo loại cảm biến ---------------------
def kind(p):
    if "VT" in p:  return "vibration"     # µm pp, >= 0
    if "XT" in p:  return "axial_pos"     # µm, có thể âm
    return "temperature"                  # degC

long["kind"] = long["sensor"].map(kind)
long["val"]  = long["raw_val"]
long.loc[long["val"] == -32768, "val"] = np.nan          # int16-min = lỗi cảm biến
long.loc[(long["kind"] == "vibration")   & (long["val"] < 0),    "val"] = np.nan
long.loc[(long["kind"] == "vibration")   & (long["val"] > 2000), "val"] = np.nan
long.loc[(long["kind"] == "temperature") & (long["val"] < -50),  "val"] = np.nan
long.loc[(long["kind"] == "temperature") & (long["val"] > 300),  "val"] = np.nan

# --- 3) Cờ máy-đang-chạy (chỉ ý nghĩa cho cảm biến rung) ------------------
long["running"] = np.where(long["kind"] == "vibration", long["val"] >= 5, np.nan)

clean = long.dropna(subset=["val"]).copy()

# --- 4) Ma trận căn thời gian ở hai lưới ----------------------------------
def widen(df, rule):
    out = {}
    for s, g in df.groupby("sensor"):
        ser = g.set_index("ts")["val"]
        if "VT" in s:
            ser = ser[ser >= 5]                      # chỉ lúc chạy
        out[s] = ser.resample(rule).median()
    return pd.DataFrame(out)

wide_8h   = widen(clean, "8h")
wide_week = widen(clean, "1W")

# --- 5) Manifest chất lượng ------------------------------------------------
man = (clean.groupby("sensor")
            .agg(n=("val", "size"), t0=("ts", "min"), t1=("ts", "max"),
                 median=("val", "median"))
            .reset_index())

clean[["sensor","ts","val","kind","running"]].to_csv(f"{OUT}/P29201A_clean_long.csv", index=False)
clean.to_parquet(f"{OUT}/P29201A_clean_long.parquet")
wide_8h.to_parquet(f"{OUT}/P29201A_wide_8h.parquet")
wide_week.to_parquet(f"{OUT}/P29201A_wide_weekly.parquet")
man.to_csv(f"{OUT}/quality_manifest.csv", index=False)

print(f"cảm biến: {clean['sensor'].nunique()} | dòng sạch: {len(clean)}")
print(f"wide 8h: {wide_8h.shape} | wide tuần: {wide_week.shape}")
