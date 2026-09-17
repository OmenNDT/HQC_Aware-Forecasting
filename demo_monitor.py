#!/usr/bin/env python3
"""demo_monitor.py — DEMO mô hình đã train, chạy trên máy tính (KHÔNG cần thiết bị nhúng)

Mô phỏng hệ giám sát: đọc lần lượt từng giờ dữ liệu như thể đang nhận realtime,
tính điểm sức khỏe 0-100, phân vùng, và chỉ ra cảm biến đóng góp nhiều nhất.

Dùng:
  python demo_monitor.py                 # phát lại 20 giờ gần nhất
  python demo_monitor.py --from 2026-05-01 --hours 30
  python demo_monitor.py --speed 0.3     # giãn nhịp cho dễ xem
"""
import argparse, json, time, sys
import numpy as np, pandas as pd

MODEL = "model_pca_k6.json"     # tham số mô hình đã train (không train lại)
DATA  = "/home/sontn/Projects/HQC_Aware-Forecasting/Dataraw/PI Data.xlsx"
SENS  = ['29VT-2001X', '29VT-2001Y', '29VT-2003X', '29VT-2003Y', '29VT-2005X', '29VT-2005Y', '29VT-2007X', '29VT-2007Y']

def load_model(path):
    m = json.load(open(path))
    return (np.array(m["W"]), np.array(m["pca_mean"]), np.array(m["mu"]),
            np.array(m["sd"]), m["score_anchors"])

def featurize(amp, phase_deg):
    ph = np.radians(phase_deg)
    return np.concatenate([amp, np.sin(ph), np.cos(ph)])

def infer(x, W, c, mu, sd):
    z = (x - mu) / sd
    t = (z - c) @ W.T
    r = z - (t @ W + c)
    return float((r**2).sum()), r

def to_score(spe, anc):
    """Thang 0-100, noi tuyen tren truc log qua 3 moc:
       median nen khoe -> 20 | nguong kiem soat -> 70 | p99 toan chuoi -> 95"""
    x = np.log(max(spe, 1e-9))
    pts = [(np.log(anc["median_healthy"]), 20.0),
           (np.log(anc["spe_limit"]),      70.0),
           (np.log(anc["p99_all"]),        95.0)]
    if x <= pts[0][0]:
        lo = np.log(max(anc["p1_healthy"], 1e-9))
        return float(np.clip(20 + (x - pts[0][0]) * 20 / (pts[0][0] - lo), 0, 100))
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if x <= x2:
            return float(np.clip(y1 + (x - x1) * (y2 - y1) / (x2 - x1), 0, 100))
    return float(np.clip(95 + (x - pts[-1][0]) * 5 / (np.log(anc["max_all"]) - pts[-1][0]), 0, 100))

def zone(s):
    return "BINH THUONG" if s < 40 else ("CAN XEM" if s < 70 else "BAT THUONG")

def contribution(r):
    per = {s: r[i]**2 + r[8+i]**2 + r[16+i]**2 for i, s in enumerate(SENS)}
    tot = sum(per.values())
    return {k: v/tot*100 for k, v in per.items()}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="t0", default=None)
    ap.add_argument("--hours", type=int, default=20)
    ap.add_argument("--speed", type=float, default=0.15)
    a = ap.parse_args()

    W, c, mu, sd, ANC = load_model(MODEL)

    # doc du lieu (thay bang doc PI realtime khi trien khai that)
    h = pd.read_excel(DATA, sheet_name="51_Vib180d", header=None, skiprows=6, nrows=2)
    g = [str(v) for v in h.iloc[0]]; n = [str(v) for v in h.iloc[1]]
    V = pd.read_excel(DATA, sheet_name="51_Vib180d", header=None, skiprows=8, usecols=range(17))
    V.columns = ["ts"] + [f"{x}|{y}" for x, y in zip(g[1:17], n[1:17])]
    V["ts"] = pd.to_datetime(V["ts"], errors="coerce")
    V = V.dropna(subset=["ts"]).set_index("ts").apply(pd.to_numeric, errors="coerce").dropna()

    rows = V.loc[a.t0:] if a.t0 else V
    rows = rows.tail(a.hours) if not a.t0 else rows.head(a.hours)

    print(f"{'thoi diem':<18}{'diem':>6}  {'vung':<12}{'cam bien nghi ngo':<14}{'%':>6}")
    print("-" * 60)
    for ts, row in rows.iterrows():
        amp = row[[f"1X Amp|{s}" for s in SENS]].to_numpy(float)
        pha = row[[f"1X Phase|{s}" for s in SENS]].to_numpy(float)
        spe, r = infer(featurize(amp, pha), W, c, mu, sd)
        sc = to_score(spe, ANC); cb = contribution(r)
        top = max(cb, key=cb.get)
        bar = "#" * int(sc/4)
        print(f"{ts.strftime('%d/%m %Hh'):<18}{sc:>6.1f}  {zone(sc):<12}{top.replace('29VT-',''):<14}{cb[top]:>6.1f}  {bar}")
        time.sleep(a.speed)

if __name__ == "__main__":
    main()
