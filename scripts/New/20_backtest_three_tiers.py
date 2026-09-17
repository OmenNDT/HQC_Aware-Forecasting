#!/usr/bin/env python3
"""20_backtest_three_tiers.py — Backtest ba tầng, bảng lead-time hai sự kiện, kiểm mù đoạn 11 cho τ₄₅ và luật C.

Bản sửa theo code review 04/09 13:10: không còn --force; lần chạy lại chỉ được phép khi khóa phase 02 được tạo lại
SAU kết quả cũ (và kết quả cũ được lưu thành *_runN.json, ghi vào 'reruns' của file kết quả). Hash gồm tier_a,
feature store, .pkl, lock1. Tham số luật C lấy từ khóa. Ngày báo tầng C = ngày cuối tuần (nhân quả). Cờ 'cắt cụt'
khi ngày báo đầu tiên là ngày sớm nhất luật có thể nổ trong chuỗi liên tục tương ứng.
Ra: Dataclean_new/backtest_three_tiers.json
"""
import glob, hashlib, json, os, pickle, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from alarm_utils import alarm_days, first_before, load_script              # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__))
cv13, s18 = load_script("cv13", "13_blocked_cv_train_compare.py", HERE), load_script("s18", "18_tier_b_slow_scale_and_tier_c.py", HERE)
LOCK2, OUT = f"{DATA_NEW}/locked_params_phase02.json", f"{DATA_NEW}/backtest_three_tiers.json"


def main():
    if not os.path.exists(LOCK2): sys.exit("TỪ CHỐI: chưa khóa phase 02 (chạy script 18).")
    lock2 = json.load(open(LOCK2)); reruns = []
    if os.path.exists(OUT):
        old = json.load(open(OUT))
        if old.get("locked_at") == lock2["locked_at"]:
            sys.exit("TỪ CHỐI: kiểm mù phase 02 đã chạy với đúng bộ khóa này. Muốn chạy lại phải khóa lại (script 18) có lý do.")
        n = len(glob.glob(f"{DATA_NEW}/backtest_three_tiers_run*.json")) + 1
        os.rename(OUT, f"{DATA_NEW}/backtest_three_tiers_run{n}.json"); reruns = old.get("reruns", []) + [{"archived_as": f"run{n}", "locked_at": old.get("locked_at")}]
        print(f"⚠ Kết quả cũ lưu thành run{n}; lần chạy này là lần thứ {n + 1}, có ghi log.")
    model = lock2["model"]; h = hashlib.sha256()
    for p in [f"{DATA_NEW}/tier_b45_daily.parquet", f"{DATA_NEW}/tier_c_weekly.parquet", f"{DATA_NEW}/tier_a_daily.parquet", FEATURE_STORE, f"{MODEL_DIR}/{model}.pkl", LOCK_FILE]:
        h.update(open(p, "rb").read())
    if h.hexdigest() != lock2["inputs_sha256"]: sys.exit("TỪ CHỐI: đầu vào đã đổi sau khi khóa phase 02.")
    tau14, tau45, rule_c = lock2["tau14"], lock2["tau45"], lock2["rule_c"]; consec45 = lock2["slow_consec"]
    fs = pd.read_parquet(FEATURE_STORE); fs10 = fs[fs.cadence_min == 10]
    d = pd.read_parquet(f"{DATA_NEW}/tier_b45_daily.parquet"); obj = pickle.load(open(f"{MODEL_DIR}/{model}.pkl", "rb"))
    blind = fs10[fs10.role == "blind"]; spe_b = cv13.score_segments(obj["model"], obj["scaler"], blind)
    db = pd.DataFrame({"spe": spe_b, "role": "blind", "episode": "ep11"})
    db["slope14"] = cv13.slope_series(db.spe).reindex(db.index.floor("1D")).values; db["slope45"] = s18.slope_slow(db.spe).reindex(db.index.floor("1D")).values
    allb = pd.concat([d, db]).sort_index(); nr = allb[allb.role != "report"]
    daily = lambda col, mask: allb.loc[mask, col].resample("1D").first().dropna()
    b14 = alarm_days(daily("slope14", allb.role != "report"), tau14, CONSEC); b45 = alarm_days(daily("slope45", allb.role != "report"), tau45, consec45)
    ta = pd.read_parquet(f"{DATA_NEW}/tier_a_daily.parquet"); a_al = alarm_days(ta.groupby("day").flag.any().astype(int), 0.5, TIERA_CONSEC)
    restarts = [pd.Timestamp(r) for r in lock2["restarts_true"]]; wC = s18.weekly_signature(fs10, rule_c, restarts)
    c_al = pd.DatetimeIndex(wC.week_end[wC.c_alarm.values]); c_al_clean = pd.DatetimeIndex(wC.week_end[(wC.c_alarm & ~wC.post_restart).values])
    tiers = {"A_direct_65um": a_al, "B14_SAE": b14, "B45_SAE": b45, "C_phase_flip": c_al, "C_phase_flip_excl_post_restart": c_al_clean}
    # cắt cụt: ngày báo đầu ≤ ngày sớm nhất có thể báo của chuỗi 9c (bắt đầu 23/03 + số ngày liên tiếp − 1)
    earliest = {"A_direct_65um": None, "B14_SAE": pd.Timestamp("2026-03-23") + pd.Timedelta(days=CONSEC - 1),
                "B45_SAE": pd.Timestamp("2026-03-23") + pd.Timedelta(days=consec45 - 1), "C_phase_flip": None, "C_phase_flip_excl_post_restart": None}
    res = {"tau14": tau14, "tau45": tau45, "model": model, "locked_at": lock2["locked_at"], "reruns": reruns, "events": {}, "negatives": {}, "blind_ep11": {}}
    for ev, stop in EVENTS.items():
        res["events"][ev] = {"stop": str(stop.date())}
        for name, days in tiers.items():
            f, lt = first_before(days, stop)
            res["events"][ev][name] = {"first_alarm": str(f.date()) if f else None, "lead_days": lt,
                                       "censored": bool(f is not None and earliest[name] is not None and f <= earliest[name] and ev == "dung2")}
    for ep in ["ep7", "ep8", "9a"]:
        idx = allb.index[(allb.episode == ep) & (allb.role == "neg")]
        res["negatives"][ep] = {n: int(sum(1 for x in days if idx.min() <= x <= idx.max())) for n, days in tiers.items()}
    plat, climb = BLIND_PLATEAU, BLIND_CLIMB_FROM
    for name, days in tiers.items():
        p = [x for x in days if plat[0] <= x <= plat[1]]; c = [x for x in days if x >= climb]
        res["blind_ep11"][name] = {"plateau_alarm_days": len(p), "climb_first_alarm": str(c[0].date()) if c else None, "climb_alarm_days": len(c)}
    s45b = daily("slope45", allb.role == "blind")
    res["blind_ep11"]["B45_max_slope_climb"] = round(float(s45b.loc[climb:].max()), 4); res["blind_ep11"]["B45_max_slope_plateau"] = round(float(s45b.loc[plat[0]:plat[1]].max()), 4)
    res["C_weekly_blind"] = wC[wC.role == "blind"][["week_end", "amp_2001X", "ph_2001X", "sd_2001X", "rot_2001X_deg_wk", "rot_prev8w", "c_flag", "c_alarm"]].round(1).reset_index().astype(str).to_dict(orient="records")
    json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=1)
    pd.set_option("display.width", 220)
    print("=== Lead-time (ngày báo đầu tiên trong 120 ngày trước sự kiện; * = cắt cụt):")
    print(pd.DataFrame({ev: {t: (v[t]["first_alarm"] or "—") + (f" ({v[t]['lead_days']} ngày{'*' if v[t]['censored'] else ''})" if v[t]["lead_days"] is not None else "") for t in tiers} for ev, v in res["events"].items()}).to_string())
    print("\n=== Đoạn âm (số ngày/tuần báo):"); print(pd.DataFrame(res["negatives"]).to_string())
    print("\n=== Kiểm mù đoạn 11:"); print(pd.DataFrame({k: v for k, v in res["blind_ep11"].items() if isinstance(v, dict)}).to_string())
    print(f"  dốc 45 max: bình nguyên {res['blind_ep11']['B45_max_slope_plateau']} | đợt leo {res['blind_ep11']['B45_max_slope_climb']} (τ₄₅ = {tau45})")
    print("\n=== Tầng C trên đoạn 11:"); print(wC[wC.role == "blind"][["week_end", "amp_2001X", "ph_2001X", "sd_2001X", "rot_2001X_deg_wk", "rot_prev8w", "c_flag", "c_alarm"]].round(1).to_string())
    print(f"\nsaved {OUT}")


if __name__ == "__main__":
    main()
