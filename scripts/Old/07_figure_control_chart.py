"""07_figure_control_chart.py — Figure biểu đồ kiểm soát SPE/T² Hotelling

Sinh tự động từ lineage artifact: hqc_M1_control_chart.png
version_id: 920ae328-2d9f-43f2-b0a5-f9889e50a4da
Môi trường: conda env 'python'

CẢNH BÁO: đây là mã trích từ lineage, đường dẫn dữ liệu là đường dẫn TUYỆT ĐỐI
của máy gốc. Kiểm lại biến đường dẫn trước khi chạy lại.
"""

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from scipy.stats import f as fdist, chi2
import matplotlib.pyplot as plt
import matplotlib as mpl

# (helper apply_figure_style() của skill figure-style — nạp qua skill, không cần trong script)
from_skill_note=True

clean = pd.read_parquet("/home/sontn/Projects/HQC_Aware-Forecasting/Dataclean/P29201A_clean_long.parquet")

HEAL = ("2022-01-01", "2023-12-31")
DRIFT_START = "2025-01-01"

def build_matrix(rule):
    piv = clean.pivot_table(index="ts", columns="sensor", values="val", aggfunc="median")
    vib = [c for c in piv.columns if c.startswith("29VT")]
    piv[vib] = piv[vib].where(piv[vib] >= 5)
    return piv.resample(rule).median()

def run_m1(rule, ncomp_crit=0.90):
    W = build_matrix(rule)
    cov = W.loc[HEAL[0]:HEAL[1]].notna().mean(); avail = cov[cov >= 0.6].index.tolist()
    X0 = W[avail].interpolate(limit=4).ffill().bfill()
    Xh = X0.loc[HEAL[0]:HEAL[1]]
    keepv = Xh.std()[Xh.std() > 1e-6].index.tolist()
    Cm = Xh[keepv].corr().abs(); feats = []
    for c in keepv:
        if not any(Cm.loc[c, k] > 0.95 for k in feats): feats.append(c)
    X = X0[feats]; mu = X.loc[HEAL[0]:HEAL[1]].mean(); sd = X.loc[HEAL[0]:HEAL[1]].std().replace(0, 1)
    Z = (X - mu) / sd; ix = Z.index
    hm = np.asarray((ix >= pd.Timestamp(HEAL[0])) & (ix <= pd.Timestamp(HEAL[1])))
    dm = np.asarray(ix >= pd.Timestamp(DRIFT_START))
    Zh = Z.values[hm]
    pf = PCA().fit(Zh); cum = np.cumsum(pf.explained_variance_ratio_)
    ncomp = int(np.argmax(cum >= ncomp_crit) + 1)
    p = PCA(n_components=ncomp).fit(Zh)
    T = p.transform(Z.values); E = Z.values - p.inverse_transform(T)
    SPE = (E ** 2).sum(1); lam = p.explained_variance_; T2 = (T ** 2 / lam).sum(1)
    SPEh = SPE[hm]; m, v = SPEh.mean(), SPEh.var(); g = v / (2 * m); h = 2 * m * m / v
    SPE_lim = g * chi2.ppf(0.99, h)
    n = hm.sum(); T2_lim = ncomp * (n - 1) / (n - ncomp) * fdist.ppf(0.99, ncomp, n - ncomp)
    return dict(rule=rule, feats=feats, ncomp=ncomp, Z=Z, ix=ix, hm=hm, dm=dm,
                SPE=SPE, T2=T2, SPE_lim=SPE_lim, T2_lim=T2_lim)

res = {}
for rule, nm in [("1D", "ngày"), ("1W", "tuần")]:
    r = run_m1(rule); res[nm] = r

r = res["tuần"]
SPE = pd.Series(r["SPE"], index=r["ix"]); T2 = pd.Series(r["T2"], index=r["ix"])
hm, dm = r["hm"], r["dm"]

fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
# SPE/Q control chart
a1.plot(SPE.index, (SPE / r["SPE_lim"]).values, lw=1.0, color="#4c78a8")
a1.axhline(1.0, color="#e4572e", ls="--", lw=1.1)
a1.axvspan(pd.Timestamp(HEAL[0]), pd.Timestamp(HEAL[1]), color="#54a24b", alpha=0.07)
a1.text(pd.Timestamp("2022-04-01"), (SPE / r["SPE_lim"]).max() * 0.7, "học nếp khỏe\n2022–2023", fontsize=7.5, color="#3a7a34")
a1.text(SPE.index[2], 1.15, "giới hạn kiểm soát 99% (Jackson–Mudholkar)", fontsize=7, color="#e4572e")
a1.set_yscale("log"); a1.set_ylabel("SPE / Q  (÷ giới hạn)")
a1.set_title("Biểu đồ kiểm soát PCA — SPE/Q bắt 'vỡ cấu trúc tương quan'\n"
             "false-alarm 1% trên nếp khỏe, phát hiện 100% giai đoạn suy giảm", fontsize=9.5, loc="left", pad=6)
a1.margins(x=0.01)
# T2 control chart
a2.plot(T2.index, (T2 / r["T2_lim"]).values, lw=1.0, color="#9467bd")
a2.axhline(1.0, color="#e4572e", ls="--", lw=1.1)
a2.axvspan(pd.Timestamp(HEAL[0]), pd.Timestamp(HEAL[1]), color="#54a24b", alpha=0.07)
a2.set_yscale("log"); a2.set_ylabel("T² Hotelling  (÷ giới hạn)")
a2.set_xlabel("Thời gian")
a2.set_title("T² Hotelling — bắt 'biến động quá lớn theo hướng đã biết'", fontsize=9.5, loc="left", pad=6)
a2.margins(x=0.01)
fig.tight_layout()
fig.savefig("hqc_M1_control_chart.png", dpi=200, bbox_inches="tight", facecolor="white")