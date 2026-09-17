#!/usr/bin/env python3
"""22_export_demo_data.py — Phase 03: xuất số liệu phase 02 sang JSON cho demo phát lại, rồi dựng HTML tự chứa.

KHÔNG tính lại mô hình hay ngưỡng. Chỉ: (1) gộp trung vị ngày các bảng đã có; (2) chấm SPE đoạn 11 bằng .pkl đã khóa
(đúng như script 20); (3) suy ngày báo từng tầng bằng cùng hàm alarm_days + tham số khóa, rồi ĐỐI CHIẾU với
backtest_three_tiers.json — lệch là dừng. Ghi hash các file đầu vào vào JSON.
Ra: Bao_cao/demo/demo_data.json, Bao_cao/demo/demo-ba-tang.html (template + JS/CSS trong scripts/New/demo/ nhúng thẳng).
"""
import hashlib, json, os, pickle, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from alarm_utils import alarm_days, load_script                           # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__))
cv13, s18 = load_script("cv13", "13_blocked_cv_train_compare.py", HERE), load_script("s18", "18_tier_b_slow_scale_and_tier_c.py", HERE)
DEMO_DIR = f"{ROOT}/Bao_cao/demo"; TPL_DIR = f"{HERE}/demo"
CH = ["2001X", "2001Y", "2003X", "2003Y", "2005X", "2005Y", "2007X", "2007Y"]
DIRECT_NAME = {c: f"29VT-{c[:4]}A{c[4]}" if c.startswith("200") and c[:4] in ("2001", "2003") else f"29VT-{c}" for c in CH}
TIERA_NAME = {c: (c[:4] + "A" + c[4]) if c[:4] in ("2001", "2003") else c for c in CH}


def rnd(s, k=2):
    """Series/array → list JSON: NaN → None, làm tròn k chữ số."""
    return [None if (x is None or (isinstance(x, float) and np.isnan(x))) else round(float(x), k) for x in s]


def main():
    lock2 = json.load(open(f"{DATA_NEW}/locked_params_phase02.json")); bt = json.load(open(f"{DATA_NEW}/backtest_three_tiers.json"))
    assert bt["locked_at"] == lock2["locked_at"], "backtest và khóa phase 02 không cùng phiên bản"
    model = lock2["model"]; tau14, tau45, consec45 = lock2["tau14"], lock2["tau45"], lock2["slow_consec"]
    inputs = [f"{DATA_NEW}/tier_b45_daily.parquet", f"{DATA_NEW}/tier_c_weekly.parquet", f"{DATA_NEW}/tier_a_daily.parquet",
              FEATURE_STORE, f"{MODEL_DIR}/{model}.pkl", LOCK_FILE, f"{DATA_NEW}/locked_params_phase02.json",
              f"{DATA_NEW}/backtest_three_tiers.json", f"{DATA_NEW}/restart_checks.csv", DIRECT_LONG]
    hashes = {os.path.basename(p): hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] for p in inputs}

    fs = pd.read_parquet(FEATURE_STORE); fs10 = fs[fs.cadence_min == 10]
    days = pd.date_range(fs.index.min().floor("1D"), fs.index.max().floor("1D"), freq="1D")
    # --- Tầng B: SPE + dốc; đoạn 11 chấm bằng pkl đã khóa (như script 20) ---
    d = pd.read_parquet(f"{DATA_NEW}/tier_b45_daily.parquet"); obj = pickle.load(open(f"{MODEL_DIR}/{model}.pkl", "rb"))
    blind = fs10[fs10.role == "blind"]; db = pd.DataFrame({"spe": cv13.score_segments(obj["model"], obj["scaler"], blind), "role": "blind", "episode": "ep11"})
    db["slope14"] = cv13.slope_series(db.spe).reindex(db.index.floor("1D")).values; db["slope45"] = s18.slope_slow(db.spe).reindex(db.index.floor("1D")).values
    allb = pd.concat([d, db]).sort_index(); nr = allb[allb.role != "report"]
    spe_day = allb.spe.resample("1D").median().reindex(days); s14 = nr.slope14.resample("1D").first().reindex(days); s45 = nr.slope45.resample("1D").first().reindex(days)
    b14 = alarm_days(s14.dropna(), tau14, CONSEC); b45 = alarm_days(s45.dropna(), tau45, consec45)
    role_day = allb.role.resample("1D").agg(lambda x: x.mode().iloc[0] if len(x) else None).reindex(days)
    # --- Tầng A ---
    ta = pd.read_parquet(f"{DATA_NEW}/tier_a_daily.parquet"); a_al = alarm_days(ta.groupby("day").flag.any().astype(int), 0.5, TIERA_CONSEC)
    a_flag = ta[ta.flag].groupby("day").apply(lambda g: g.loc[g.days_left_low.idxmin(), ["ch", "days_left_low"]].tolist())
    a_rows = {str(k.date()): {"ch": v[0].replace("A", ""), "dl": round(v[1], 1)} for k, v in a_flag.items()}
    dl2001 = ta[ta.ch == "2001AX"].set_index("day").days_left_low.reindex(days).replace(np.inf, np.nan)
    # --- Direct 8 kênh, trung vị ngày (mọi giờ, kể cả lúc dừng → thấy máy dừng) ---
    c5 = pd.read_parquet(DIRECT_LONG); c5 = c5[c5.ts >= days[0]]
    direct = {c: rnd(c5[c5.sensor == DIRECT_NAME[c]].set_index("ts").val.resample("1D").median().ffill(limit=2).reindex(days), 1) for c in CH}   # kênh quét lệch ~8 h: lấp ≤ 2 ngày
    amp1x = {c: rnd(fs[f"amp_{c}"].resample("1D").median().reindex(days), 2) for c in CH}
    # --- Tầng C: tuần ---
    wC = pd.read_parquet(f"{DATA_NEW}/tier_c_weekly.parquet")
    weeks = [{"end": str(pd.Timestamp(r.week_end).date()), "ph": {c: round(float(r[f"ph_{c}"]), 1) for c in CH}, "amp2001X": round(float(r.amp_2001X), 2),
              "rot": None if pd.isna(r.rot_2001X_deg_wk) else round(float(r.rot_2001X_deg_wk), 1), "rot8": None if pd.isna(r.rot_prev8w) else round(float(r.rot_prev8w), 1),
              "flag": bool(r.c_flag), "alarm": bool(r.c_alarm), "post": bool(r.post_restart)} for _, r in wC.iterrows()]
    # tuần đoạn 11 (kiểm mù) không nằm trong tier_c_weekly.parquet → lấy từ backtest chính thức (C_weekly_blind), cùng luật, cùng khóa
    restart_blind = pd.Timestamp(lock2["restarts_true"][-1]); post_days = lock2["rule_c"]["post_restart_days"]
    for r in bt["C_weekly_blind"]:
        we = pd.Timestamp(r["week_end"]); f = lambda k: None if r[k] in ("nan", "None") else round(float(r[k]), 1)
        weeks.append({"end": str(we.date()), "ph": {"2001X": f("ph_2001X")}, "amp2001X": f("amp_2001X"), "rot": f("rot_2001X_deg_wk"), "rot8": f("rot_prev8w"),
                      "flag": r["c_flag"] == "True", "alarm": r["c_alarm"] == "True", "post": bool(we <= restart_blind + pd.Timedelta(days=post_days))})
    weeks.sort(key=lambda w: w["end"]); assert len({w["end"] for w in weeks}) == len(weeks), "tuần trùng giữa parquet và backtest"
    c_al = [w["end"] for w in weeks if w["alarm"]]
    # --- Đối chiếu với backtest chính thức ---
    fa = lambda al, stop: min([x for x in al if stop - pd.Timedelta(days=120) <= x <= stop], default=None)   # ngày báo đầu trong 120 ngày trước sự kiện
    got = {"A_direct_65um": fa(a_al, STOP2), "B14_SAE": fa(b14, STOP2), "B45_SAE": fa(b45, STOP2), "C_phase_flip": fa(pd.to_datetime(c_al), STOP2)}
    for k, v in got.items():
        exp = bt["events"]["dung2"][k]["first_alarm"]; assert (str(v.date()) if v is not None else None) == exp, f"LỆCH {k}: demo {v} ≠ backtest {exp}"
    print("Đối chiếu ngày báo đầu trước dừng 2 với backtest: KHỚP", {k: str(v.date()) if v is not None else None for k, v in got.items()})
    rc = pd.read_csv(f"{DATA_NEW}/restart_checks.csv")
    stops = [{"stop": str(pd.Timestamp(r.stop).date()), "restart": str(pd.Timestamp(r.restart).date()), "days": r.stop_days} for _, r in rc.iterrows()]
    out = {"generated_at": pd.Timestamp.now().strftime("%Y-%m-%dT%H:%M"), "inputs_sha256_16": hashes, "backtest_locked_at": bt["locked_at"],
           "params": {"model": model, "n_params": 3600, "arch": "24→24→24→24→24→24→24 (6 lớp tuyến tính, tanh)", "tau14": tau14, "tau45": tau45, "consec14": CONSEC,
                      "consec45": consec45, "limit_um": PLANT_LIMIT_UM, "horizon_days": TIERA_HORIZON_DAYS, "tierA_consec": TIERA_CONSEC, "rule_c": lock2["rule_c"],
                      "limit99_6h": float(pd.read_csv(f"{DATA_NEW}/cv_results.csv").set_index("model").loc[model, "limit99_6h"])},
           "days": [str(x.date()) for x in days], "role": [None if pd.isna(x) else x for x in role_day], "channels": CH,
           "direct": direct, "amp1x": amp1x, "spe": rnd(spe_day, 4), "slope14": rnd(s14, 4), "slope45": rnd(s45, 4),
           "dl2001": rnd(dl2001, 1), "tierA_flag": a_rows,
           "alarms": {"A": [str(x.date()) for x in a_al], "B14": [str(x.date()) for x in b14], "B45": [str(x.date()) for x in b45], "C": c_al},
           "weeks": weeks, "stops": stops, "events": bt["events"], "negatives": bt["negatives"], "blind": {k: v for k, v in bt["blind_ep11"].items() if isinstance(v, dict)}}
    os.makedirs(DEMO_DIR, exist_ok=True); js = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    open(f"{DEMO_DIR}/demo_data.json", "w").write(js)
    html = open(f"{TPL_DIR}/demo-ba-tang-template.html").read()
    for tag, fn in [("/*__CSS__*/", "demo-ba-tang-style.css"), ("/*__CHARTS__*/", "demo-charts-canvas.js"), ("/*__APP__*/", "demo-replay-app.js"), ("/*__NOTES__*/", "demo-annotations-vi.js")]:
        html = html.replace(tag, open(f"{TPL_DIR}/{fn}").read())
    html = html.replace("/*__DATA__*/", f"window.DEMO = {js};")
    open(f"{DEMO_DIR}/demo-ba-tang.html", "w").write(html)
    print(f"ngày: {len(days)} | báo A/B14/B45/C: {len(a_al)}/{len(b14)}/{len(b45)}/{len(c_al)} | JSON {len(js)//1024} KB | HTML {len(html)//1024} KB → {DEMO_DIR}")


if __name__ == "__main__":
    main()
