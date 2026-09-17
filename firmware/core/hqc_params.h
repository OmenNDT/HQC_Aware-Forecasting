/* hqc_params.h — SINH TỰ ĐỘNG bởi scripts/New/26_quantize_sae_int8.py từ locked_params.json + locked_params_phase02.json. KHÔNG sửa tay.
 * lock1 2026-09-04T00:06 · lock2 2026-09-04T12:33 · sha256(lock1+lock2) 7a6bd6f3efeec41b */
#pragma once
#define HQC_LOCK_HASH "7a6bd6f3efeec41b"
#define HQC_TAU14 0.135f
#define HQC_TAU45 0.035f
#define HQC_CONSEC14 3
#define HQC_CONSEC45 5
#define HQC_SEQ_GAP_DAYS 3
#define HQC_SLOPE_DAYS 14
#define HQC_SLOPE_MIN_OBS 10
#define HQC_SLOW_DAYS 45
#define HQC_SLOW_MIN_OBS 30
#define HQC_PLANT_LIMIT_UM 65.0f
#define HQC_TIERA_HORIZON_DAYS 30.0f
#define HQC_TIERA_Z90 1.645f
#define HQC_TIERA_RISE_MIN 0.1f
#define HQC_TIERA_WINDOW_ROWS 14
#define HQC_TIERA_REF_DAYS 90
#define HQC_TIERA_REF_MIN_OBS 30
#define HQC_TIERA_STARTUP_SKIP 2
#define HQC_TIERA_CONSEC 2
#define HQC_RULEC_MIN_RATE 1.0
#define HQC_RULEC_SD_MAX 5.0
#define HQC_RULEC_LOOKBACK_DAYS 56
#define HQC_RULEC_LOOKBACK_TOL 3
#define HQC_RULEC_HOLD_WEEKS 2
#define HQC_RULEC_POST_RESTART_DAYS 21
#define HQC_RULEC_MIN_ROWS 100   /* weekly_signature: len(g) >= 100 */
