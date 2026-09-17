#!/usr/bin/env python3
"""09_direct_only_long_tier.py — Dung mo hinh Direct-only (tang dai) va DO xem no bat duoc gi.

Ket luan (da chay 03/09/2026): tang dai KHONG dung duoc doc lap.
Chi tiet o cuoi file.

Nguon : Dataclean/P29201A_clean_long.parquet (23 cam bien, 1.820 ngay, file 5 nam)
Ra    : hqc_direct_only.png + in bang do
Chay  : python 09_direct_only_long_tier.py
"""
import numpy as np, pandas as pd
from scipy import stats
from sklearn.decomposition import PCA

ROOT = "/home/sontn/Projects/HQC_Aware-Forecasting"
RUN_THRESHOLD = 3.0     # um — nguong may chay (khop 99_BaoCao)
MIN_CHANNELS  = 6       # so kenh toi thieu vuot nguong de coi la may chay

# ---------- 1. Nap va loc ----------
def load_direct_wide(path):
    """Doc long-form -> ma tran wide 8 kenh rung tren LUOI NGAY.

    LUU Y (bay da mac 3 lan): timestamp moi cam bien quet RIENG, khong can nhau.
    Pivot theo timestamp goc chi ra ~15 moc du 8 kenh. Phai gop ve luoi ngay.
    Luoi 8h cho IT hon luoi ngay (188 vs 311) vi 8 kenh rai rac trong ngay.
    """
    c5 = pd.read_parquet(path)
    vt = [s for s in c5.sensor.unique() if s.startswith("29VT")]
    d  = c5[c5.sensor.isin(vt)].copy()
    d["bin"] = d.ts.dt.floor("1D")
    w = d.pivot_table(index="bin", columns="sensor", values="val", aggfunc="median")
    running = (w > RUN_THRESHOLD).sum(axis=1) >= MIN_CHANNELS
    return w, w[running].dropna()

# ---------- 2. Tim nen phang ----------
def scan_flat_window(wr, win_days=60, step=10, max_span=150):
    """Quet cua so, chon cua so co do doc trung binh nho nhat.

    Quy tac da chot: KHONG lay dau chuoi lam nen; phai quet va chon theo do doc.
    """
    out = []
    for i in range(0, len(wr) - win_days, step):
        win = wr.iloc[i:i + win_days]
        if (win.index.max() - win.index.min()).days > max_span:
            continue
        x = (win.index - win.index[0]).days.values.astype(float)
        sl = [abs(stats.linregress(x, win[c].values).slope * 30 / win[c].median() * 100)
              for c in wr.columns]
        out.append((win.index[0], win.index[-1], len(win), np.mean(sl), np.max(sl)))
    return pd.DataFrame(out, columns=["t0","t1","n","doc_tb","doc_max"]).sort_values("doc_tb")

# ---------- 3. Huan luyen ----------
def fit_pca(X, k, val_frac=0.25):
    """Fit tren phan dau, giu duoi lam validation (time-blocked, KHONG xao tron)."""
    mu, sd = X.mean(0), X.std(0); sd[sd < 1e-9] = 1
    Z = (X - mu) / sd
    cut = int(len(Z) * (1 - val_frac))
    pc = PCA(n_components=k).fit(Z[:cut])
    spe = lambda M: ((M - pc.inverse_transform(pc.transform(M))) ** 2).sum(1)
    return dict(pc=pc, mu=mu, sd=sd, spe=spe, cut=cut,
                lim=np.percentile(spe(Z[:cut]), 99), base=spe(Z[:cut]).mean())

def score(m, df):
    return m["spe"]((df.to_numpy(float) - m["mu"]) / m["sd"])

# ---------- 4. Chay ----------
if __name__ == "__main__":
    w_all, wr = load_direct_wide(f"{ROOT}/Dataclean/P29201A_clean_long.parquet")
    print(f"ngay du 8 kenh luc chay: {len(wr)} / {len(w_all)} ngay co du lieu")
    print(f"phan bo theo nam:\n{wr.groupby(wr.index.year).size().to_string()}")

    R = scan_flat_window(wr)
    print(f"\ncua so phang nhat: {R.iloc[0].t0.date()} -> {R.iloc[0].t1.date()} "
          f"(doc TB {R.iloc[0].doc_tb:.2f} %/thang)")

    W  = wr.loc["2025-01-01":]                       # bo phan truoc 2025 (may dung)
    TR = W.loc[str(R.iloc[0].t0.date()):str(R.iloc[0].t1.date())]

    print(f"\n{'k':>3}{'SPE lim':>9}{'FA nen':>8}{'gap val':>9}")
    for k in [1, 2, 3, 4]:
        m = fit_pca(TR.to_numpy(float), k)
        Z = (TR.to_numpy(float) - m["mu"]) / m["sd"]
        fa = (m["spe"](Z) > m["lim"]).mean()
        print(f"{k:>3}{m['lim']:>9.2f}{fa*100:>7.1f}%"
              f"{m['spe'](Z[m['cut']:]).mean()/m['base']:>8.2f}x")

    m = fit_pca(TR.to_numpy(float), 3)
    print(f"\n=== tang dai bat duoc gi (k=3) ===")
    for lo, hi, nm in [("2025-01","2025-05","2025 T1-5"), ("2025-06","2025-09","2025 T6-9"),
                       ("2025-10","2025-12","2025 T10-12"), ("2026-01","2026-01","2026 T1"),
                       ("2026-02","2026-04","2026 T2-4 (nen)"), ("2026-05","2026-05","2026 T5"),
                       ("2026-06","2026-07","2026 T6-7")]:
        seg = W.loc[lo:hi]
        if len(seg) == 0: continue
        r = score(m, seg)
        print(f"  {nm:<18} n={len(seg):>3} | residual {r.mean()/m['base']:>6.1f}x nen "
              f"| vuot nguong {(r > m['lim']).mean()*100:>5.0f}%")

# =====================================================================
# KET QUA DO DUOC (03/09/2026) — tang dai KHONG dung duoc doc lap:
#
# 1. "5 nam" chi la ngay LICH. Thuc te 1.431/1.810 ngay may A DUNG
#    -> chi 311 ngay du 8 kenh luc chay, va 296/311 (95%) thuoc 2025-2026.
#    Truoc 2025 chi 15 ngay. Nguyen nhan: A la may phu, B chay chinh
#    (Run Hours: A 491h vs B 2.684h).
#
# 2. False-alarm nen 10-15% thay vi 1% nhu thiet ke. Nguyen nhan: 60 mau
#    cho 8 cot = 7,5 mau-cot (bo 1X co 742 mau / 24 cot = 31 mau-cot).
#    Luoi ngay lam mat 24x so mau so luoi gio.
#
# 3. MOI giai doan vuot nguong ~100%, ke ca 2025 (27-263x nen).
#    Mo hinh khong phan biet duoc giai doan nao la binh thuong
#    -> khong dung lam bo do canh bao.
#
# 4. Ngay nen train cung chua phang: 2001AX +4,09 %/thang (p=6,2e-04),
#    2001AY +3,49 %/thang (p=4,8e-04) -> lai la "phang sau khi leo".
#
# 5. Moc bao tri 31/05/2025: chi 19 ngay TRUOC moc -> khong du (can >=30)
#    de do lead-time. Do la ly do muc 4 trong YEUCAU-du-lieu-v6 yeu cau
#    keo Direct+nhiet khoang 01/08/2024-30/09/2025 rieng.
#
# => KET LUAN: Direct KHONG the thay 1X lam truc early-warning doc lap.
#    Vai tro dung cua Direct: (a) cong loc trang thai chay, (b) boi canh
#    dai han khi CO du diem, (c) do lead-time qua cac moc bao tri — nhung
#    ca (c) cung can keo them du lieu.
# =====================================================================
