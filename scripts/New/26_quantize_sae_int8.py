#!/usr/bin/env python3
"""26_quantize_sae_int8.py — Phase 04 ngày 1: lượng tử hóa SAE sang số nguyên và mô phỏng BIT-EXACT bằng numpy.

Sơ đồ (port 1:1 sang C):
  x_q  : int16 Q10 (±32; max|x| thực = 24,4) — 24 đầu vào đã scale (amp minmax, sin, cos)      s_a = 2^-10
  W_l  : int8 đối xứng per-output-channel, s_w[l,o] = max|W|/127          (phép thử: hidden int8 sai 83 % → bỏ)
  b_l  : int32 = round(b / (s_w[l,o] * s_a))  với s_a = scale kích hoạt vào lớp l (2^-10 lớp 0, 2^-15 lớp 1..5)
  acc  : int32 = Σ W*a + b; idx12 = (acc * mult[l,o] + 2^(SH_l-1)) >> SH_l, mult = round(s_w*s_a*4096*2^SH_l), SH_l chọn để mult < 2^31
  tanh : LUT 2048 mục int16 Q15 trên [-4,4) bước 1/256, nội suy tuyến tính 16 bước (idx12 = z*4096), bão hòa ngoài
         → kích hoạt int16 Q15 ở MỌI lớp (ẩn và ra)
  SPE  : Σ (x_q·32 − x̂_q15)² / 2^30  (x Q10 → Q15 bằng ×32; tổng int64)
Ra: embed/sae_int8.npz, sae_int8_spe.parquet, quant_report.json, firmware/core/sae_weights.h
Kiểm: SPE int8 vs float (nền, 9c, ep11) và NGÀY BÁO B14/B45 tính lại từ SPE int8 (alarm_utils) so với backtest lần 3.
"""
import hashlib, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from models.reconstruction_base import to_matrix                          # noqa: E402
from alarm_utils import alarm_days, first_before, load_script             # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__)); cv13 = load_script("cv13", "13_blocked_cv_train_compare.py", HERE); s18 = load_script("s18", "18_tier_b_slow_scale_and_tier_c.py", HERE)
EMBED = f"{DATA_NEW}/embed"; FW = f"{ROOT}/firmware/core"
LUT_N, LUT_STEP, X_Q, X_MAX = 2048, 256, 10, 1 << 19                      # LUT [-4,4) bước 1/256; đầu vào Q10 int32, kẹp ±2^19 (±512 đơn vị scale, H3)


def make_lut():
    z = (np.arange(LUT_N) - LUT_N // 2) / LUT_STEP
    return np.clip(np.round(np.tanh(z) * 32767), -32767, 32767).astype(np.int16)


def quantize(W, b, wbits):
    """wbits: số bit trọng số từng lớp (8 hoặc 16). Lớp int16 lưu int16, tích lũy int64."""
    qmax = np.array([2 ** (k - 1) - 1 for k in wbits], float)
    s_w = np.max(np.abs(W), axis=2) / qmax[:, None]                            # (6, 24)
    Wq = np.stack([np.clip(np.round(W[l] / s_w[l][:, None]), -qmax[l], qmax[l]) for l in range(6)]).astype(np.int32)
    s_a = np.array([2.0 ** -X_Q] + [2.0 ** -15] * 5)                           # scale kích hoạt VÀO từng lớp
    bq = np.round(b / (s_w * s_a[:, None])).astype(np.int32)
    raw = s_w * s_a[:, None] * LUT_STEP * 16                                    # idx12 = acc * raw
    acc_max = 24.0 * qmax * np.array([X_MAX] + [32767] * 5) + np.abs(bq).max(axis=1)        # |acc| lớn nhất có thể (đầu vào tới ±X_MAX)
    mult_cap = np.minimum(2 ** 31, 2 ** 62 / acc_max)                            # acc*mult phải < 2^63
    sh = np.floor(np.log2(mult_cap / raw.max(axis=1))).astype(np.int32) - 1
    mult = np.round(raw * 2.0 ** sh[:, None]).astype(np.int64); assert mult.max() < 2 ** 31
    return Wq, bq, mult.astype(np.int32), sh, s_w


def forward_int(Xq, Wq, bq, mult, sh, lut):
    """Mô phỏng số nguyên (port 1:1 sang C). Xq (n,24) int Q10 (không kẹp int16). Trả x̂ Q15 int16 và SPE (từ tổng int64)."""
    a = Xq.astype(np.int64); half = LUT_N // 2
    for l in range(6):
        acc = a @ Wq[l].T.astype(np.int64) + bq[l].astype(np.int64)                     # int32 nếu W int8, int64 nếu W int16
        assert np.abs(acc).max() < 2 ** 62, "acc tràn int64"
        idx12 = (acc * mult[l].astype(np.int64) + (1 << (int(sh[l]) - 1))) >> int(sh[l])   # z * 4096
        i = (idx12 >> 4) + half; f = idx12 & 15
        lo = i < 0; hi = i > LUT_N - 2; i0 = np.clip(i, 0, LUT_N - 2); f = np.where(lo, 0, np.where(hi, 16, f))
        a = (lut[i0].astype(np.int64) * (16 - f) + lut[i0 + 1].astype(np.int64) * f + 8) >> 4    # int16 Q15
    xhat = a; d = Xq.astype(np.int64) * (1 << (15 - X_Q)) - xhat; spe = (d * d).sum(axis=1) / float(2 ** 30)
    return xhat.astype(np.int16), spe


def alarm_days_both(ref, spe_q, lock2):
    """Ngày báo B14/B45 từ SPE float và SPE lượng tử, cùng hàm dốc + ngưỡng khóa (bỏ vai trò report như script 20)."""
    out = ref.assign(spe_int8=spe_q); nr = out[out.role != "report"]; res = {}
    for name, col in [("float", "spe_float"), ("int8", "spe_int8")]:
        s = nr[col]; s14 = cv13.slope_series(s); s45 = s18.slope_slow(s)
        b14 = alarm_days(s14.dropna(), lock2["tau14"], CONSEC); b45 = alarm_days(s45.dropna(), lock2["tau45"], lock2["slow_consec"])
        res[name] = {"B14_days": [str(d.date()) for d in b14], "B45_days": [str(d.date()) for d in b45],
                     "B14_first_dung2": (lambda f: str(f[0].date()) if f[0] else None)(first_before(b14, STOP2)), "B45_first_dung2": (lambda f: str(f[0].date()) if f[0] else None)(first_before(b45, STOP2))}
    return res


def alarm_check(ref, spe_q, lock2):
    r = alarm_days_both(ref, spe_q, lock2)
    return (r["float"]["B14_days"] == r["int8"]["B14_days"], r["float"]["B45_days"] == r["int8"]["B45_days"]), {"B14": r["int8"]["B14_first_dung2"], "B45": r["int8"]["B45_first_dung2"]}


def write_params_header(lock1, lock2):
    """firmware/core/hqc_params.h — mọi hằng số luật ba tầng lấy từ file khóa phase 01/02 và phase01_config (M2 code review)."""
    rc = lock2["rule_c"]; h = hashlib.sha256((json.dumps(lock1, sort_keys=True) + json.dumps(lock2, sort_keys=True)).encode()).hexdigest()[:16]
    L = ["/* hqc_params.h — SINH TỰ ĐỘNG bởi scripts/New/26_quantize_sae_int8.py từ locked_params.json + locked_params_phase02.json. KHÔNG sửa tay.",
         f" * lock1 {lock1.get('locked_at', '?')} · lock2 {lock2['locked_at']} · sha256(lock1+lock2) {h} */", "#pragma once",
         f"#define HQC_LOCK_HASH \"{h}\"", f"#define HQC_TAU14 {float(lock2['tau14'])}f", f"#define HQC_TAU45 {float(lock2['tau45'])}f", f"#define HQC_CONSEC14 {CONSEC}", f"#define HQC_CONSEC45 {lock2['slow_consec']}",
         f"#define HQC_SEQ_GAP_DAYS {SEQ_GAP_DAYS}", f"#define HQC_SLOPE_DAYS {SLOPE_DAYS}", f"#define HQC_SLOPE_MIN_OBS {SLOPE_MIN_OBS}", f"#define HQC_SLOW_DAYS {lock2['slow_days']}", f"#define HQC_SLOW_MIN_OBS {lock2['slow_min_obs']}",
         f"#define HQC_PLANT_LIMIT_UM {float(PLANT_LIMIT_UM)}f", f"#define HQC_TIERA_HORIZON_DAYS {float(TIERA_HORIZON_DAYS)}f", f"#define HQC_TIERA_Z90 {float(TIERA_Z90)}f", f"#define HQC_TIERA_RISE_MIN {float(TIERA_RISE_MIN)}f",
         f"#define HQC_TIERA_WINDOW_ROWS {TIERA_WINDOW_RUN_DAYS}", f"#define HQC_TIERA_REF_DAYS {TIERA_REF_DAYS}", f"#define HQC_TIERA_REF_MIN_OBS {TIERA_REF_MIN_OBS}", f"#define HQC_TIERA_STARTUP_SKIP {TIERA_STARTUP_SKIP}", f"#define HQC_TIERA_CONSEC {TIERA_CONSEC}",
         f"#define HQC_RULEC_MIN_RATE {float(rc['min_rate_deg_wk'])}", f"#define HQC_RULEC_SD_MAX {float(rc['sd_max_deg'])}", f"#define HQC_RULEC_LOOKBACK_DAYS {rc['lookback_days']}", f"#define HQC_RULEC_LOOKBACK_TOL {rc['lookback_tol_days']}",
         f"#define HQC_RULEC_HOLD_WEEKS {rc['hold_weeks']}", f"#define HQC_RULEC_POST_RESTART_DAYS {rc['post_restart_days']}", "#define HQC_RULEC_MIN_ROWS 100   /* weekly_signature: len(g) >= 100 */"]
    os.makedirs(FW, exist_ok=True); open(f"{FW}/hqc_params.h", "w").write("\n".join(L) + "\n"); return h


def write_header(Wq, bq, mult, sh, lut, sc_a, sc_b, meta):
    os.makedirs(FW, exist_ok=True); L = []
    L += ["/* sae_weights.h — SINH TỰ ĐỘNG bởi scripts/New/26_quantize_sae_int8.py. KHÔNG sửa tay.", f" * model {meta['model']} · pkl sha256 {meta['pkl_sha256'][:16]} · lock2 {meta['locked_at']} */",
          "#pragma once", "#include <stdint.h>", f"#define SAE_L 6\n#define SAE_N 24\n#define SAE_X_Q {X_Q}\n#define SAE_X_MAX {X_MAX}\n#define SAE_LUT_N {LUT_N}\n#define SAE_LUT_STEP {LUT_STEP}"]
    L.append("static const int8_t SAE_SH[SAE_L] = {" + ", ".join(str(int(v)) for v in sh) + "};")
    L.append("static const float SAE_SCALER_A[8] = {" + ", ".join(f"{v:.7g}f" for v in sc_a) + "};")
    L.append("static const float SAE_SCALER_B[8] = {" + ", ".join(f"{v:.7g}f" for v in sc_b) + "};")
    L.append("static const int8_t SAE_WBITS[SAE_L] = {" + ", ".join(str(int(v)) for v in meta["wbits"]) + "};")
    for l, Wl in enumerate(Wq):
        t = "int16_t" if meta["wbits"][l] == 16 else "int8_t"
        L.append(f"static const {t} SAE_W{l}[SAE_N][SAE_N] = {{" + ",".join("{" + ",".join(str(int(v)) for v in row) + "}" for row in Wl) + "};")
    L.append("static const void *SAE_W[SAE_L] = {" + ", ".join(f"SAE_W{l}" for l in range(6)) + "};")
    L.append("static const int32_t SAE_B[SAE_L][SAE_N] = {" + ",".join("{" + ",".join(str(int(v)) for v in bl) + "}" for bl in bq) + "};")
    L.append("static const int32_t SAE_MULT[SAE_L][SAE_N] = {" + ",".join("{" + ",".join(str(int(v)) for v in ml) + "}" for ml in mult) + "};")
    L.append("static const int16_t SAE_TANH_LUT[SAE_LUT_N] = {" + ",".join(str(int(v)) for v in lut) + "};")
    wb = sum(576 * (2 if k == 16 else 1) for k in meta["wbits"]); L.append(f"#define SAE_WEIGHTS_BYTES {wb + bq.size * 4 + mult.size * 4 + LUT_N * 2}   /* W + b + mult + LUT */")
    open(f"{FW}/sae_weights.h", "w").write("\n".join(L) + "\n")


def main():
    z = np.load(f"{EMBED}/sae_float.npz", allow_pickle=True); W, b, sc_a, sc_b = z["W"], z["b"], z["scaler_a"], z["scaler_b"]
    lock2 = json.load(open(f"{DATA_NEW}/locked_params_phase02.json")); bt = json.load(open(f"{DATA_NEW}/backtest_three_tiers.json"))
    lut = make_lut()
    ref = pd.read_parquet(f"{EMBED}/sae_reference_spe.parquet"); fs = pd.read_parquet(FEATURE_STORE); fs10 = fs.loc[ref.index]
    X = to_matrix(fs10); X[:, :8] = (X[:, :8] - sc_a) / sc_b
    Xq = np.clip(np.round(X * 2 ** X_Q), -X_MAX, X_MAX).astype(np.int64); assert np.abs(X * 2 ** X_Q).max() < X_MAX, "đầu vào vượt X_MAX"
    # ứng viên từ nhẹ tới nặng; chọn sơ đồ NHẸ NHẤT giữ nguyên toàn bộ ngày báo B14/B45 (phép đo quyết định, không đoán)
    schemes = {"int8_all": [8] * 6, "L0_int16": [16, 8, 8, 8, 8, 8], "L0L1_int16": [16, 16, 8, 8, 8, 8], "int16_all": [16] * 6}
    trials = {}; chosen = None
    for name, wbits in schemes.items():
        Wq, bq, mult, sh, s_w = quantize(W, b, wbits); xhat, spe_q = forward_int(Xq, Wq, bq, mult, sh, lut)
        same, first = alarm_check(ref, spe_q, lock2)
        trials[name] = {"wbits": wbits, "weights_bytes": int(sum(576 * (2 if k == 16 else 1) for k in wbits)), "B14_identical": same[0], "B45_identical": same[1], "int8_first_dung2": first,
                        "train_rel_p95": float(((spe_q - ref.spe_float) / ref.spe_float)[ref.role == "train"].abs().quantile(.95))}
        print(f"  {name:12s} W {trials[name]['weights_bytes']} B | train p95 {trials[name]['train_rel_p95']:.3f} | B14 giữ nguyên {same[0]} | B45 {same[1]} | báo đầu {first}")
        if chosen is None and same[0] and same[1]: chosen = name
    assert chosen, "không sơ đồ nào giữ nguyên ngày báo"; wbits = schemes[chosen]; print("→ chọn", chosen, wbits)
    Wq, bq, mult, sh, s_w = quantize(W, b, wbits); xhat, spe_q = forward_int(Xq, Wq, bq, mult, sh, lut)
    out = ref.copy(); out["spe_int8"] = spe_q; out.to_parquet(f"{EMBED}/sae_int8_spe.parquet")
    rel = (out.spe_int8 - out.spe_float) / out.spe_float; log_d = np.log10(out.spe_int8) - np.log10(out.spe_float)
    rep = {"scheme": f"W {wbits} bit per-out-channel, in int16 Q10, mọi kích hoạt int16 Q15 (LUT 2048 nội suy 16 bước), SPE int64→/2^30", "SH": [int(v) for v in sh], "lut_n": LUT_N,
           "x_max_abs": float(np.abs(X).max()), "s_w_max": float(s_w.max()), "err_by_role": {}}
    for role, g in out.groupby("role"):
        r = ((g.spe_int8 - g.spe_float) / g.spe_float); rep["err_by_role"][role] = {"n": int(len(g)), "rel_median": float(r.median()), "rel_p95_abs": float(r.abs().quantile(.95)), "rel_max_abs": float(r.abs().max()),
                                                                                  "log10_p95_abs": float((np.log10(g.spe_int8) - np.log10(g.spe_float)).abs().quantile(.95))}
    res = alarm_days_both(ref, spe_q, lock2)
    same14 = res["float"]["B14_days"] == res["int8"]["B14_days"]; same45 = res["float"]["B45_days"] == res["int8"]["B45_days"]
    rep["trials"] = trials; rep["chosen_scheme"] = chosen; rep["wbits"] = wbits
    rep["alarms"] = {"B14_identical_days": same14, "B45_identical_days": same45, "int8_first_dung2": {"B14": res["int8"]["B14_first_dung2"], "B45": res["int8"]["B45_first_dung2"]},
                     "backtest_first_dung2": {"B14": bt["events"]["dung2"]["B14_SAE"]["first_alarm"], "B45": bt["events"]["dung2"]["B45_SAE"]["first_alarm"]},
                     "n_days_float": [len(res["float"]["B14_days"]), len(res["float"]["B45_days"])], "n_days_int8": [len(res["int8"]["B14_days"]), len(res["int8"]["B45_days"])],
                     "diff_B14": sorted(set(res["float"]["B14_days"]) ^ set(res["int8"]["B14_days"])), "diff_B45": sorted(set(res["float"]["B45_days"]) ^ set(res["int8"]["B45_days"]))}
    meta = {"model": str(z["model"]), "pkl_sha256": str(z["pkl_sha256"]), "locked_at": lock2["locked_at"], "wbits": wbits}
    np.savez(f"{EMBED}/sae_int8.npz", Wq=Wq, bq=bq, mult=mult, sh=sh, lut=lut, s_w=s_w, scaler_a=sc_a, scaler_b=sc_b, **meta)
    rep["params_lock_hash"] = write_params_header(json.load(open(LOCK_FILE)), lock2)
    write_header(Wq, bq, mult, sh, lut, sc_a, sc_b, meta); rep["weights_header_sha256"] = hashlib.sha256(open(f"{FW}/sae_weights.h", "rb").read()).hexdigest()[:16]
    rep["sizes_bytes"] = {"W": int(sum(576 * (2 if k == 16 else 1) for k in wbits)), "b_int32": int(bq.size * 4), "mult_int32": int(mult.size * 4), "lut_int16": int(lut.size * 2), "float32_equiv": int((W.size + b.size) * 4)}
    json.dump(rep, open(f"{EMBED}/quant_report.json", "w"), ensure_ascii=False, indent=1)
    pd.set_option("display.width", 200); print(pd.DataFrame(rep["err_by_role"]).T.round(4).to_string())
    print("max|x| đầu vào:", round(rep['x_max_abs'], 1), "| SH:", rep["SH"], "| kích thước:", rep["sizes_bytes"])
    print("Ngày báo int8 = float?", "B14", same14, "B45", same45, "| int8 báo đầu dừng 2:", rep["alarms"]["int8_first_dung2"], "| backtest:", rep["alarms"]["backtest_first_dung2"])
    if not (same14 and same45): print("  khác B14:", rep["alarms"]["diff_B14"], "\n  khác B45:", rep["alarms"]["diff_B45"])
    print(f"saved {EMBED}/quant_report.json, sae_int8.npz, {FW}/sae_weights.h")


if __name__ == "__main__":
    main()
