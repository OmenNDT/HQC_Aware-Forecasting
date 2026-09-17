#!/usr/bin/env python3
"""27_replay_feature_store_to_uart.py — Phase 04 ngày 2: dựng luồng phát lại (định dạng khung UART), chạy host_sim (mã C) và ĐỐI CHIẾU với Python.

Luồng: S,<epoch>,amp×8,sin×8,cos×8 (mọi mẫu 10 phút của kho, mọi vai trò) · D,<epoch>,Direct×8 theo giờ (lưới 1 h, gần nhất ±4 h,
như script 17) · R,<epoch> (chạy lại sau dừng thật, từ khóa phase 02) · E. Epoch = giây kể từ 1970 coi giờ địa phương như UTC.
Đối chiếu (Python tính trên CÙNG tập mẫu chip nhận, tức mọi mẫu 10 phút — khác backtest chỉ ở chỗ backtest bỏ vai trò 'report'):
  B: trung vị ngày SPE (chip int8 vs float), dốc 14/45, tập NGÀY BÁO B14/B45; A: tập ngày cờ/báo vs tier_a_daily; C: cờ/báo từng tuần vs weekly_signature.
Ra: Dataclean_new/embed/replay_stream.txt, host_sim_out.jsonl, host_sim_compare.json.  --from-device <jsonl>: đối chiếu log từ ESP32 thay vì host_sim.
"""
import argparse, json, os, subprocess, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from alarm_utils import alarm_days, first_before, load_script             # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__)); cv13 = load_script("cv13", "13_blocked_cv_train_compare.py", HERE); s18 = load_script("s18", "18_tier_b_slow_scale_and_tier_c.py", HERE)
EMBED = f"{DATA_NEW}/embed"; SIM = f"{ROOT}/firmware/host_sim/replay"
CH = ["2001X", "2001Y", "2003X", "2003Y", "2005X", "2005Y", "2007X", "2007Y"]; DCH = ["2001AX", "2001AY", "2003AX", "2003AY", "2005X", "2005Y", "2007X", "2007Y"]
EPOCH = pd.Timestamp("1970-01-01"); ep = lambda t: int((pd.Timestamp(t) - EPOCH).total_seconds())
f6 = lambda v: "nan" if pd.isna(v) else f"{v:.9g}"                          # M4: 9 chữ số để chip nhận đúng float32


def hourly_direct():
    """Lưới Direct 1 giờ, gần nhất ±4 h, khử trùng — giống script 17 daily_direct (phần lưới)."""
    c5 = pd.read_parquet(DIRECT_LONG); d = c5[c5.sensor.isin([f"29VT-{c}" for c in DCH])]
    grid = pd.date_range(d.ts.min().floor("1D"), d.ts.max().ceil("1D"), freq="1h"); cols = {}
    for c in DCH:
        s = d[d.sensor == f"29VT-{c}"].set_index("ts").val.sort_index().groupby(level=0).median()
        cols[c] = s.reindex(grid, method="nearest", tolerance=pd.Timedelta(hours=4))
    return pd.DataFrame(cols, index=grid)


def build_stream(fs10, wide, restarts, path):
    ev = []
    for t, r in zip(fs10.index, fs10[[f"amp_{c}" for c in CH] + [f"sin_{c}" for c in CH] + [f"cos_{c}" for c in CH]].to_numpy()):
        ev.append((ep(t), 0, "S," + str(ep(t)) + "," + ",".join(f6(v) for v in r)))
    w = wide[wide.index >= fs10.index.min().floor("1D")]
    for t, r in zip(w.index, w.to_numpy()):
        ev.append((ep(t), 1, "D," + str(ep(t)) + "," + ",".join(f6(v) for v in r)))
    for t in restarts: ev.append((ep(t), -1, f"R,{ep(t)}"))
    ev.sort(key=lambda e: (e[0], e[1]))
    with open(path, "w") as f: f.write("\n".join(e[2] for e in ev) + "\nE\n")
    return len(ev)


def python_reference(fs10, restarts, lock2):
    spe = pd.read_parquet(f"{EMBED}/sae_reference_spe.parquet").spe_float.reindex(fs10.index)
    s14 = cv13.slope_series(spe); s45 = s18.slope_slow(spe); med = spe.resample("1D").median().dropna()
    b14 = alarm_days(s14.dropna(), lock2["tau14"], CONSEC); b45 = alarm_days(s45.dropna(), lock2["tau45"], lock2["slow_consec"])
    ta = pd.read_parquet(f"{DATA_NEW}/tier_a_daily.parquet"); a_flag = ta.groupby("day").flag.any(); a_al = alarm_days(a_flag.astype(int), 0.5, TIERA_CONSEC)
    a_level = ta[ta.ch == "2001AX"].set_index("day").level
    wC = s18.weekly_signature(fs10, lock2["rule_c"], restarts)
    return {"med": med, "s14": s14, "s45": s45, "b14": set(str(d.date()) for d in b14), "b45": set(str(d.date()) for d in b45),
            "a_flag": set(str(d.date()) for d in a_flag.index[a_flag]), "a_days": set(str(d.date()) for d in a_flag.index), "a_al": set(str(d.date()) for d in a_al), "a_level": a_level,
            "c": {str(pd.Timestamp(r.week_end).date()): (bool(r.c_flag), bool(r.c_alarm), bool(r.post_restart)) for _, r in wC.iterrows()}}


def compare(lines, ref, lock2, bt):
    B = [j for j in lines if j["t"] == "B"]; A = [j for j in lines if j["t"] == "A"]; C = [j for j in lines if j["t"] == "C"]
    db = pd.DataFrame(B).set_index(pd.to_datetime([j["day"] for j in B]))
    med_rel = ((db.spe_med - ref["med"].reindex(db.index)) / ref["med"].reindex(db.index)).dropna()
    d14 = (db.slope14 - ref["s14"].reindex(db.index)).dropna(); d45 = (db.slope45 - ref["s45"].reindex(db.index)).dropna()
    c_b14 = set(db.index[db.B14 == 1].strftime("%Y-%m-%d")); c_b45 = set(db.index[db.B45 == 1].strftime("%Y-%m-%d"))
    da = pd.DataFrame(A); da = da[da.row == 1]; c_af = set(da.day[da.flag == 1]); c_aa = set(da.day[da.A == 1])
    a_rows_chip = set(da.day); lv = ref["a_level"].reindex(pd.to_datetime(sorted(a_rows_chip & ref["a_days"]))); lv_chip = da.set_index(pd.to_datetime(da.day)).level_2001X.reindex(lv.index)
    level_diff = float((lv_chip - lv).abs().max()) if len(lv) else None
    since = "2026-01-01"; f = lambda S: {d for d in S if d >= since}
    dc = {j["week_end"]: (bool(j["flag"]), bool(j["C"]), bool(j["post_restart"])) for j in C}
    c_keys = sorted(set(dc) & set(ref["c"])); c_mis = [k for k in c_keys if dc[k][:2] != ref["c"][k][:2]]
    def first(S): d = sorted(x for x in S if "2026-01-29" <= x <= "2026-05-29"); return d[0] if d else None
    out = {"B": {"n_days": int(len(db)), "spe_med_rel_p95": float(med_rel.abs().quantile(.95)), "spe_med_rel_max": float(med_rel.abs().max()),
                 "slope14_absdiff_max": float(d14.abs().max()), "slope45_absdiff_max": float(d45.abs().max()),
                 "B14_days_identical": c_b14 == ref["b14"], "B45_days_identical": c_b45 == ref["b45"], "B14_diff": sorted(c_b14 ^ ref["b14"]), "B45_diff": sorted(c_b45 ^ ref["b45"]),
                 "B14_first_dung2_chip": first(c_b14), "B45_first_dung2_chip": first(c_b45), "backtest": {"B14": bt["events"]["dung2"]["B14_SAE"]["first_alarm"], "B45": bt["events"]["dung2"]["B45_SAE"]["first_alarm"]}},
           "A": {"rows_chip": int(len(da)), "rows_python": len(ref["a_days"]), "flag_days_identical_since_2026": f(c_af) == f(ref["a_flag"]), "flag_diff_since_2026": sorted(f(c_af) ^ f(ref["a_flag"])),
                 "alarm_days_identical_since_2026": f(c_aa) == f(ref["a_al"]), "alarm_diff_since_2026": sorted(f(c_aa) ^ f(ref["a_al"])), "flag_diff_before_2026": sorted((c_af ^ ref["a_flag"]) - f(c_af ^ ref["a_flag"])),
                 "row_days_identical": a_rows_chip == ref["a_days"], "row_days_diff": sorted(a_rows_chip ^ ref["a_days"]), "level_2001X_absdiff_max": level_diff,
                 "A_first_dung2_chip": first(c_aa), "backtest": bt["events"]["dung2"]["A_direct_65um"]["first_alarm"]},
           "C": {"weeks_chip": len(dc), "weeks_python": len(ref["c"]), "weeks_common": len(c_keys), "flag_alarm_identical": not c_mis, "mismatch_weeks": c_mis,
                 "alarm_weeks_chip": sorted(k for k, v in dc.items() if v[1]), "alarm_weeks_python": sorted(k for k, v in ref["c"].items() if v[1]),
                 "post_restart_identical": all(dc[k][2] == ref["c"][k][2] for k in c_keys)}}
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--from-device", default=None, help="jsonl log từ ESP32 thay cho host_sim"); ap.add_argument("--skip-build", action="store_true"); a = ap.parse_args()
    lock2 = json.load(open(f"{DATA_NEW}/locked_params_phase02.json")); bt = json.load(open(f"{DATA_NEW}/backtest_three_tiers.json"))
    fs = pd.read_parquet(FEATURE_STORE); fs10 = fs[fs.cadence_min == 10].sort_index(); restarts = [pd.Timestamp(r) for r in lock2["restarts_true"]]
    os.makedirs(EMBED, exist_ok=True); n = build_stream(fs10, hourly_direct(), restarts, f"{EMBED}/replay_stream.txt"); print(f"luồng: {n} dòng → {EMBED}/replay_stream.txt")
    if a.from_device: lines = [json.loads(l) for l in open(a.from_device) if l.strip()]; src = a.from_device
    else:
        if not a.skip_build: subprocess.run(["make", "-s", "-C", f"{ROOT}/firmware/host_sim"], check=True)
        out = subprocess.run([SIM], stdin=open(f"{EMBED}/replay_stream.txt"), capture_output=True, text=True, check=True).stdout
        open(f"{EMBED}/host_sim_out.jsonl", "w").write(out); lines = [json.loads(l) for l in out.splitlines() if l.strip()]; src = "host_sim"
    print("host_sim:", [j for j in lines if j["t"] == "END"][0])
    res = compare(lines, python_reference(fs10, restarts, lock2), lock2, bt); res["source"] = src
    json.dump(res, open(f"{EMBED}/host_sim_compare.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
