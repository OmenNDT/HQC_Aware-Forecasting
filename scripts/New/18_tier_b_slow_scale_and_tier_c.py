#!/usr/bin/env python3
"""18_tier_b_slow_scale_and_tier_c.py — Tầng B thang 45 ngày (τ₄₅) và tầng C chữ ký hệ, KHÔNG chạm đoạn 11.

Sửa theo code review 04/09 13:10:
  - Dốc 45 ngày tính trên TOÀN chuỗi liên tục (9b→9c liền nhau), không cắt theo episode (C1).
  - Tuần mang cả `week_end` (dòng cuối trong tuần); báo động gắn vào week_end để nhân quả (C2).
  - Tham chiếu "8 tuần trước" theo LỊCH (56 ± 3 ngày), đòi |rate| > 1 ở cả hai phía (H2); vai trò tuần theo đa số.
  - Đánh dấu tuần trong 21 ngày sau lần dừng thật (post_restart) để báo cáo riêng, không bỏ (H3).
  - Mô hình lấy từ quyết định nhóm, ghi rõ vào khóa (override so với lock1.chosen_model).
Ra: tier_b45_daily.parquet, tier_c_weekly.parquet, locked_params_phase02.json (hash gồm cả tier_a + feature store).
"""
import glob, hashlib, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from alarm_utils import alarm_days                                         # noqa: E402

CH = ["2001X", "2001Y", "2003X", "2003Y", "2005X", "2005Y", "2007X", "2007Y"]
SLOW_DAYS, SLOW_MIN_OBS, SLOW_CONSEC = 45, 30, 5
TAU45_GRID = [round(0.005 * i, 3) for i in range(1, 41)]
RULE_C = {"lookback_days": 56, "lookback_tol_days": 3, "hold_weeks": 2, "sd_max_deg": 5.0, "min_rate_deg_wk": 1.0, "post_restart_days": 21}
MODEL_OVERRIDE = {"model": "SAE_b0.001_s0", "reason": "quyết định nhóm 04/09 11:40: lead-time đo được thật, giải thích đúng ổ; lock1.chosen_model=PCA_k8 bị cắt cụt"}
LOCK2 = f"{DATA_NEW}/locked_params_phase02.json"


def slope_slow(spe):
    d = np.log(spe.resample("1D").median().dropna()); out = pd.Series(np.nan, index=d.index)
    seg = np.cumsum(np.r_[True, np.diff(d.index.values) > np.timedelta64(SEQ_GAP_DAYS, "D")])
    for s in np.unique(seg):
        ds = d[seg == s]
        for t in ds.index:
            w = ds.loc[t - pd.Timedelta(days=SLOW_DAYS - 1): t]
            if len(w) >= SLOW_MIN_OBS:
                x = (w.index - w.index[0]).days.values.astype(float); out[t] = np.polyfit(x, w.values, 1)[0]
    return out


def circ_mean_sd(a):
    a = np.deg2rad(np.asarray(a, float)); a = a[~np.isnan(a)]
    if len(a) < 10: return np.nan, np.nan
    C, S = np.cos(a).mean(), np.sin(a).mean(); R = max(np.hypot(C, S), 1e-9)
    return np.rad2deg(np.arctan2(S, C)) % 360, np.rad2deg(np.sqrt(-2 * np.log(R)))


def weekly_signature(fs, rule=RULE_C, restarts=(), ch=CH, sig="2001X"):
    """Chữ ký tuần; `sig` = kênh chữ ký (A: 2001X; P29202A: 2017X, quyết định 10/09/2026), `ch` = danh sách kênh tóm tắt."""
    rows = []
    for t, g in fs.resample("7D"):
        if len(g) < 100: continue
        r = {"week": t, "week_end": g.index.max(), "n": len(g), "episode": g.episode.mode().iloc[0], "role": g.role.mode().iloc[0]}
        for c in ch:
            ph = np.rad2deg(np.arctan2(g[f"sin_{c}"], g[f"cos_{c}"])) % 360
            r[f"ph_{c}"], r[f"sd_{c}"] = circ_mean_sd(ph); r[f"amp_{c}"] = g[f"amp_{c}"].median()
        rows.append(r)
    w = pd.DataFrame(rows).set_index("week")
    ph = w[f"ph_{sig}"].values; unw = ph.copy()
    for i in range(1, len(ph)):
        gap = (w.index[i] - w.index[i - 1]).days; d = ((ph[i] - unw[i - 1] + 180) % 360) - 180
        unw[i] = unw[i - 1] + d if gap <= 21 else ph[i]
    w[f"ph_{sig}_unw"] = unw; rate = pd.Series(np.nan, index=w.index)
    for i in range(3, len(w)):
        if (w.index[i] - w.index[i - 3]).days <= 28:
            x = (w.index[i - 3:i + 1] - w.index[i - 3]).days.values.astype(float); rate.iloc[i] = np.polyfit(x, unw[i - 3:i + 1], 1)[0] * 7
    w[f"rot_{sig}_deg_wk"] = rate
    # tham chiếu 8 tuần trước theo lịch
    prev = pd.Series(np.nan, index=w.index)
    for t in w.index:
        cand = w.loc[t - pd.Timedelta(days=rule["lookback_days"] + rule["lookback_tol_days"]): t - pd.Timedelta(days=rule["lookback_days"] - rule["lookback_tol_days"]), f"rot_{sig}_deg_wk"].dropna()
        if len(cand): prev[t] = cand.iloc[-1]
    w["rot_prev8w"] = prev
    flip = (np.sign(rate) != np.sign(prev)) & rate.notna() & prev.notna() & (rate.abs() > rule["min_rate_deg_wk"]) & (prev.abs() > rule["min_rate_deg_wk"]) & (w[f"sd_{sig}"] < rule["sd_max_deg"])
    w["c_flag"] = flip; w["c_alarm"] = flip & flip.shift(1).fillna(False)
    w["post_restart"] = [any(0 <= (t - r).days <= rule["post_restart_days"] for r in restarts) for t in w.index]
    return w


def true_restarts(fs_all, direct_long=DIRECT_LONG, min_run_ch=6):
    """Thời điểm chạy lại sau lần dừng thật (khoảng trống > 12 h có ngày Direct không chạy). min_run_ch: số kênh > 3 µm để coi là chạy."""
    c5 = pd.read_parquet(direct_long); vt = [s for s in c5.sensor.unique() if s.startswith("29VT")]
    d = c5[c5.sensor.isin(vt)].copy(); d["day"] = d.ts.dt.floor("1D")
    wide = d.pivot_table(index="day", columns="sensor", values="val", aggfunc="median"); stop_days = set(wide.index[(wide > 3.0).sum(axis=1) < min_run_ch])
    gaps = fs_all.index.to_series().diff() > pd.Timedelta(hours=12); out = []
    for t in fs_all.index[gaps.values]:
        t0 = fs_all.index[fs_all.index < t].max()
        if any(dd in stop_days for dd in pd.date_range(t0.floor("1D"), t.floor("1D"))): out.append(t)
    return out


def main():
    fs_all = pd.read_parquet(FEATURE_STORE); fs = fs_all[(fs_all.cadence_min == 10) & (fs_all.role != "blind")]
    lock1 = json.load(open(LOCK_FILE)); model = MODEL_OVERRIDE["model"]
    d = pd.read_parquet(f"{SPE_DIR}/{model}.parquet")
    d["slope45"] = slope_slow(d.spe).reindex(d.index.floor("1D")).values          # toàn chuỗi liên tục (C1)
    daily = lambda mask: d.loc[mask, "slope45"].resample("1D").first().dropna()
    negs = {ep: daily((d.episode == ep) & (d.role == "neg")) for ep in ["ep7", "ep8", "9a"]}
    cfg = daily(d.role == "config_pos"); pre = daily(d.role == "precheck_pos")
    print("Số ngày có dốc 45: " + ", ".join(f"{k}={len(v)}" for k, v in negs.items()) + f", 9c cấu hình={len(cfg)}, kiểm trước={len(pre)}")
    print("Dốc 45 max: " + ", ".join(f"{k}={v.max():.3f}" for k, v in negs.items() if len(v)) + f", 9c cấu hình={cfg.max():.3f}, kiểm trước={pre.max():.3f}")
    tau45 = next((tau for tau in TAU45_GRID if sum(len(alarm_days(s, tau, SLOW_CONSEC)) for s in negs.values() if len(s)) == 0 and len(alarm_days(cfg, tau, SLOW_CONSEC))), None)
    first = alarm_days(cfg, tau45, SLOW_CONSEC) if tau45 is not None else []
    print(f"τ₄₅ = {tau45} | báo đầu trên 9c cấu hình: {first[0].date() if len(first) else '—'} | ngày báo kiểm trước: {len(alarm_days(pre, tau45, SLOW_CONSEC)) if tau45 else '—'}")
    d[["spe", "role", "episode", "slope14", "slope45"]].to_parquet(f"{DATA_NEW}/tier_b45_daily.parquet")
    restarts = true_restarts(fs_all); w = weekly_signature(fs, RULE_C, restarts); w.to_parquet(f"{DATA_NEW}/tier_c_weekly.parquet")
    pd.set_option("display.width", 220)
    print("\nTầng C — tuần ổ 2001X (phần không mù):"); print(w[["week_end", "role", "amp_2001X", "ph_2001X", "sd_2001X", "rot_2001X_deg_wk", "rot_prev8w", "c_flag", "c_alarm", "post_restart"]].round(1).to_string())
    al = w[w.c_alarm]; print(f"\nLuật C nổ: {len(al)} tuần → " + ", ".join(f"{t.date()} (kết thúc {e.date()}{', sau khởi động' if p else ''})" for t, e, p in zip(al.index, al.week_end, al.post_restart)))
    h = hashlib.sha256()
    for p in [f"{DATA_NEW}/tier_b45_daily.parquet", f"{DATA_NEW}/tier_c_weekly.parquet", f"{DATA_NEW}/tier_a_daily.parquet", FEATURE_STORE, f"{MODEL_DIR}/{model}.pkl", LOCK_FILE]:
        h.update(open(p, "rb").read())
    prev_lock = json.load(open(LOCK2)) if os.path.exists(LOCK2) else None
    lock = {"model": model, "model_override": MODEL_OVERRIDE, "lock1_chosen_model": lock1["chosen_model"], "tau14": lock1["tau_common"], "tau45": tau45,
            "slow_days": SLOW_DAYS, "slow_min_obs": SLOW_MIN_OBS, "slow_consec": SLOW_CONSEC, "rule_c": RULE_C,
            "restarts_true": [str(r) for r in restarts], "first_alarm45_cfg": str(first[0].date()) if len(first) else None,
            "inputs_sha256": h.hexdigest(), "locked_at": pd.Timestamp.now().isoformat(timespec="minutes"),
            "relock_history": (prev_lock.get("relock_history", []) + [{"at": prev_lock["locked_at"], "tau45": prev_lock.get("tau45")}]) if prev_lock else []}
    json.dump(lock, open(LOCK2, "w"), indent=1, ensure_ascii=False); print(f"saved {LOCK2}")


if __name__ == "__main__":
    main()
