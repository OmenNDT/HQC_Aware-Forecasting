#!/usr/bin/env python3
"""14_configure_rate_alarm_and_score.py — Gộp kết quả CV, áp tiêu chí, khóa MỘT ngưỡng tốc độ chung τ.

Bản sửa theo code review:
  - Gộp Dataclean_new/cv_rows/*.json → cv_results.csv (không đua ghi).
  - Tiêu chí 1 có thật: FA leave-one-fold-out trung bình ≤ 3% và lớn nhất ≤ 10% (tham số CLI).
  - τ chỉ chỉnh trên các mô hình đã qua tiêu chí 1–2, và CHỈ trên nửa cấu hình của 9c (23/03–30/04)
    cộng ba đoạn âm. Nửa kiểm trước (01–29/05) chỉ báo cáo.
  - Luật chọn τ: τ nhỏ nhất (báo sớm nhất) sao cho mọi mô hình đã qua 1–2 có 0 ngày báo trên đoạn âm;
    nếu không tồn tại, τ nhỏ nhất làm đa số mô hình đạt.
  - Lead-time = ngày báo đầu tiên (trên chuỗi liên tục 9b→9c) tới lúc dừng 2; đánh dấu "cắt cụt" nếu
    ngày báo đầu rơi vào 3 ngày đầu có thể báo.

Chạy: python scripts/New/14_configure_rate_alarm_and_score.py [--fa-mean 0.03 --fa-max 0.10] [--tau 0.1]
"""
import argparse, glob, hashlib, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402


def alarm_days(s, tau):
    hit = (s > tau).astype(int).rolling(CONSEC).sum()
    return s.index[(hit >= CONSEC).values]


def load_model_series(tag):
    d = pd.read_parquet(f"{SPE_DIR}/{tag}.parquet")
    daily = lambda mask: d.loc[mask, "slope14"].resample("1D").first().dropna()
    return {"neg": {ep: daily((d.episode == ep) & (d.role == "neg")) for ep in ["ep7", "ep8", "9a"]},
            "cfg": daily(d.role == "config_pos"), "pre": daily(d.role == "precheck_pos"), "d": d}


def tau_table(series, tags, tau):
    rows = []
    for t in tags:
        s = series[t]; n_neg = sum(len(alarm_days(x, tau)) for x in s["neg"].values())
        al = alarm_days(s["cfg"], tau); first = al[0] if len(al) else pd.NaT
        rows.append({"model": t, "neg_alarm_days": n_neg, "first_alarm_cfg": first,
                     "lead_days": (STOP2.normalize() - first).days if pd.notna(first) else np.nan,
                     "censored": bool(pd.notna(first) and first <= s["cfg"].index.min() + pd.Timedelta(days=CONSEC - 1)),
                     "precheck_alarm_days": len(alarm_days(s["pre"], tau))})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fa-mean", type=float, default=FA_FOLD_MEAN_MAX)
    ap.add_argument("--fa-max", type=float, default=FA_FOLD_MAX_MAX); ap.add_argument("--tau", type=float, default=None); a = ap.parse_args()
    if os.path.exists(BLIND_FILE):
        sys.exit("TỪ CHỐI: kiểm mù đã chạy (blind_test_ep11.json tồn tại). Khóa lại sau kiểm mù là vi phạm giao thức.")
    rows = [json.load(open(p)) for p in sorted(glob.glob(f"{ROWS_DIR}/*.json"))]
    res = pd.DataFrame(rows).set_index("model"); res.to_csv(CV_RESULTS)
    tags = list(res.index); series = {t: load_model_series(t) for t in tags}
    crit1 = (res.fa_fold_mean <= a.fa_mean) & (res.fa_fold_max <= a.fa_max)
    crit2 = res["sep_ratio_16-30apr"] >= SEP_MIN
    eligible = [t for t in tags if crit1[t] and crit2[t]]
    print(f"Tiêu chí 1 (FA fold mean ≤ {a.fa_mean}, max ≤ {a.fa_max}): {int(crit1.sum())}/{len(tags)} đạt | tiêu chí 2 (tách ≥ {SEP_MIN}): {int(crit2.sum())}/{len(tags)}")
    print("Đủ 1–2:", eligible)
    if a.tau is None:
        cand = None
        for tau in TAU_GRID:                       # τ nhỏ nhất mà MỌI mô hình đủ điều kiện im trên đoạn âm và còn báo được trên 9c
            tt = tau_table(series, eligible, tau)
            if len(tt) and (tt.neg_alarm_days == 0).all() and tt.lead_days.notna().all():
                cand = tau; break
        if cand is None:
            scores = [(tau, int(((tt := tau_table(series, eligible, tau)).neg_alarm_days == 0).sum() + tt.lead_days.notna().sum())) for tau in TAU_GRID]
            cand = max(scores, key=lambda z: (z[1], -z[0]))[0]
        tau = cand
    else:
        tau = a.tau
    tt = tau_table(series, tags, tau).set_index("model").join(res[["n_params", "sep_ratio_16-30apr", "fa_fold_mean", "fa_fold_max", "limit99_6h", "spe_oos_median", "epochs_refit"]])
    tt["crit12"] = [t in eligible for t in tt.index]
    tt["pass"] = tt.crit12 & (tt.neg_alarm_days == 0) & tt.lead_days.notna()
    ranked = tt.sort_values(["pass", "lead_days", "n_params"], ascending=[False, False, True])
    pd.set_option("display.width", 260); print(f"\nτ chung = {tau}\n"); print(ranked.to_string())
    chosen = ranked[ranked["pass"]].index[0] if ranked["pass"].any() else None
    anchors = None
    if chosen:
        d = series[chosen]["d"]; oos = d.oos_spe.dropna(); c9 = d.loc[d.role.isin(["config_pos", "precheck_pos"]), "spe"].dropna()
        anchors = {"median_oos_9b": float(oos.median()), "p99_oos_9b_6h": float(res.loc[chosen, "limit99_6h"]), "p99_9c": float(np.percentile(c9, 99))}
    h = hashlib.sha256()
    for p in [CV_RESULTS] + sorted(glob.glob(f"{SPE_DIR}/*.parquet")) + sorted(glob.glob(f"{MODEL_DIR}/*.pkl")):
        h.update(open(p, "rb").read())
    lock = {"tau_common": tau, "consecutive_days": CONSEC, "criteria": {"fa_fold_mean_max": a.fa_mean, "fa_fold_max_max": a.fa_max, "sep_min": SEP_MIN},
            "eligible": eligible, "chosen_model": chosen, "anchors": anchors,
            "ranking": ranked.reset_index().assign(first_alarm_cfg=lambda x: x.first_alarm_cfg.astype(str)).to_dict(orient="records"),
            "inputs_sha256": h.hexdigest(), "locked_at": pd.Timestamp.now().isoformat(timespec="minutes")}
    json.dump(lock, open(LOCK_FILE, "w"), ensure_ascii=False, indent=1, default=str)
    print(f"\nMô hình chọn: {chosen} | mốc thang điểm: {anchors}\nsaved {LOCK_FILE}")


if __name__ == "__main__":
    main()
