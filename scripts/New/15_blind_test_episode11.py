#!/usr/bin/env python3
"""15_blind_test_episode11.py — Kiểm mù đoạn 11 (14/06–02/09/2026), chạy MỘT lần sau khi khóa tham số.

Bản sửa theo code review: script này TỰ chấm đoạn 11 bằng mô hình đã lưu (Dataclean_new/models/*.pkl),
không đọc điểm số tính sẵn; từ chối chạy nếu hash đầu vào khác hash khóa, hoặc nếu đã có kết quả kiểm mù.

Ra: Dataclean_new/blind_test_ep11.json
"""
import glob, hashlib, json, os, pickle, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from models.reconstruction_base import to_matrix                           # noqa: E402
import importlib.util
_spec = importlib.util.spec_from_file_location("cv13", os.path.join(os.path.dirname(os.path.abspath(__file__)), "13_blocked_cv_train_compare.py"))
cv13 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(cv13)


def alarm_days(s, tau):
    hit = (s > tau).astype(int).rolling(CONSEC).sum()
    return s.index[(hit >= CONSEC).values]


def main():
    if os.path.exists(BLIND_FILE) and "--force" not in sys.argv:
        sys.exit("TỪ CHỐI: kiểm mù đã chạy một lần (blind_test_ep11.json tồn tại). Chạy lại là vi phạm giao thức.")
    lock = json.load(open(LOCK_FILE))
    h = hashlib.sha256()
    for p in [CV_RESULTS] + sorted(glob.glob(f"{SPE_DIR}/*.parquet")) + sorted(glob.glob(f"{MODEL_DIR}/*.pkl")):
        h.update(open(p, "rb").read())
    if h.hexdigest() != lock["inputs_sha256"]:
        sys.exit("TỪ CHỐI: đầu vào đã đổi sau khi khóa (hash khác).")
    tau = lock["tau_common"]; res = pd.read_csv(CV_RESULTS).set_index("model")
    fs = pd.read_parquet(FEATURE_STORE); blind = fs[(fs.role == "blind") & (fs.cadence_min == 10)]
    passing = [r["model"] for r in lock["ranking"] if r["pass"]]
    out = {"tau": tau, "chosen": lock["chosen_model"], "models": {}}
    for tag in passing:
        obj = pickle.load(open(f"{MODEL_DIR}/{tag}.pkl", "rb")); m, sc = obj["model"], obj["scaler"]
        spe = cv13.score_segments(m, sc, blind); sl = cv13.slope_series(spe)
        plat, climb = sl.loc[BLIND_PLATEAU[0]:BLIND_PLATEAU[1]], sl.loc[BLIND_CLIMB_FROM:]
        al_p, al_c = alarm_days(plat, tau), alarm_days(climb, tau)
        six = spe.resample(SUBSAMPLE).first().dropna(); lim = res.loc[tag, "limit99_6h"]
        r = {"plateau_alarm_days": int(len(al_p)), "climb_first_alarm": str(al_c[0].date()) if len(al_c) else None,
             "climb_alarm_days": int(len(al_c)), "state_frac_above_limit_6h": round(float((six > lim).mean()), 3),
             "median_spe_plateau": round(float(spe.loc[BLIND_PLATEAU[0]:BLIND_PLATEAU[1]].median()), 3),
             "median_spe_climb": round(float(spe.loc[BLIND_CLIMB_FROM:].median()), 3),
             "max_slope_plateau": round(float(np.nanmax(plat)), 4) if len(plat) else None,
             "max_slope_climb": round(float(np.nanmax(climb)), 4) if len(climb) else None}
        out["models"][tag] = r
        flag = " ← mô hình chọn" if tag == lock["chosen_model"] else ""
        print(f"{tag:14s} bình nguyên: {r['plateau_alarm_days']} ngày báo | đợt leo: báo đầu {r['climb_first_alarm']} ({r['climb_alarm_days']} ngày) | "
              f"trạng thái vượt giới hạn {r['state_frac_above_limit_6h']*100:.0f}% | SPE {r['median_spe_plateau']} → {r['median_spe_climb']} | dốc max {r['max_slope_climb']}{flag}")
    json.dump(out, open(BLIND_FILE, "w"), ensure_ascii=False, indent=1)
    print(f"\nsaved {BLIND_FILE}  (kiểm mù đã chạy — không sửa τ hay mô hình sau bước này)")


if __name__ == "__main__":
    main()
