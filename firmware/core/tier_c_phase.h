/* tier_c_phase.h — Tầng C trên chip: chữ ký tuần của pha 1X ổ 2001X. Tuần = khối 7 ngày kể từ nửa đêm ngày đầu luồng (pandas resample 7D,
 * origin start_day), cần ≥100 mẫu. Trung bình/độ lệch tròn (≥10 mẫu), tháo cuộn (gap ≤ 21 ngày), tốc độ quay 4 tuần (span ≤ 28 ngày)
 * ×7, tham chiếu tuần 8 tuần trước (53–59 ngày), cờ khi đổi dấu & |tốc độ| > 1 hai phía & sd < 5; báo khi 2 tuần cờ liên tiếp.
 * post_restart: tuần bắt đầu trong 21 ngày sau lần chạy lại. Port từ scripts/New/18::weekly_signature. */
#pragma once
#include <stdint.h>

#define TC_WEEKS 12
#define TC_MAX_RESTARTS 4                   /* vòng: chỉ 4 lần chạy lại gần nhất là còn ý nghĩa (cửa sổ 21 ngày) */

typedef struct {
    double min_rate, sd_max; int lookback_days, lookback_tol, hold_weeks, post_restart_days, min_rows;
    int64_t origin_ts; int have_origin;
    /* tuần đang gom */
    int64_t cur_bin; double sumS, sumC; int n_rows, n_valid; int64_t bin_first_ts, bin_last_ts, last_ts;
    /* các tuần đã đóng (chỉ tuần đủ mẫu) */
    int64_t wstart[TC_WEEKS], wend[TC_WEEKS]; double ph[TC_WEEKS], sd[TC_WEEKS], unw[TC_WEEKS], rate[TC_WEEKS]; int flag[TC_WEEKS], n;
    int64_t restarts[TC_MAX_RESTARTS]; int n_restarts, restart_head;
    /* kết quả tuần vừa đóng */
    int64_t last_wstart, last_wend; double last_ph, last_sd, last_rate, last_prev8; int last_flag, last_alarm, last_post_restart, has_week;
} tier_c_t;

void tc_init(tier_c_t *s);
void tc_restart(tier_c_t *s, int64_t ts);
int tc_push(tier_c_t *s, int64_t ts, float sin2001x, float cos2001x);   /* trả 1 khi đóng một tuần (đủ mẫu) */
int tc_flush(tier_c_t *s);
