#include "tier_c_phase.h"
#include "stats_util.h"
#include "hqc_params.h"
#include <math.h>
#include <string.h>

#define RAD2DEG 57.29577951308232

void tc_init(tier_c_t *s) {
    memset(s, 0, sizeof(*s)); s->min_rate = HQC_RULEC_MIN_RATE; s->sd_max = HQC_RULEC_SD_MAX; s->lookback_days = HQC_RULEC_LOOKBACK_DAYS; s->lookback_tol = HQC_RULEC_LOOKBACK_TOL; s->hold_weeks = HQC_RULEC_HOLD_WEEKS; s->post_restart_days = HQC_RULEC_POST_RESTART_DAYS; s->min_rows = HQC_RULEC_MIN_ROWS;
    s->cur_bin = INT64_MIN; s->last_rate = s->last_prev8 = NAN;
}

void tc_restart(tier_c_t *s, int64_t ts) { s->restarts[s->restart_head] = ts; s->restart_head = (s->restart_head + 1) % TC_MAX_RESTARTS; if (s->n_restarts < TC_MAX_RESTARTS) s->n_restarts++; }

static double wrap180(double d) { d = fmod(d + 180.0, 360.0); if (d < 0) d += 360.0; return d - 180.0; }

static void close_week(tier_c_t *s) {
    s->has_week = 0;
    if (s->n_rows < s->min_rows) return;                      /* M3: đủ mẫu tính theo TỔNG dòng như Python */
    double ph = NAN, sd = NAN;
    if (s->n_valid >= 10) { double C = s->sumC / s->n_valid, S = s->sumS / s->n_valid; double R = hypot(C, S); if (R < 1e-9) R = 1e-9; ph = fmod(atan2(S, C) * RAD2DEG + 360.0, 360.0); sd = sqrt(-2.0 * log(R)) * RAD2DEG; }
    if (s->n == TC_WEEKS) { memmove(s->wstart, s->wstart + 1, (TC_WEEKS - 1) * sizeof(int64_t)); memmove(s->wend, s->wend + 1, (TC_WEEKS - 1) * sizeof(int64_t)); memmove(s->ph, s->ph + 1, (TC_WEEKS - 1) * sizeof(double)); memmove(s->sd, s->sd + 1, (TC_WEEKS - 1) * sizeof(double)); memmove(s->unw, s->unw + 1, (TC_WEEKS - 1) * sizeof(double)); memmove(s->rate, s->rate + 1, (TC_WEEKS - 1) * sizeof(double)); memmove(s->flag, s->flag + 1, (TC_WEEKS - 1) * sizeof(int)); s->n--; }
    int i = s->n; int64_t ws = s->origin_ts + s->cur_bin * 7 * 86400;
    s->wstart[i] = ws; s->wend[i] = s->bin_last_ts; s->ph[i] = ph; s->sd[i] = sd;
    /* tháo cuộn */
    if (i == 0) s->unw[i] = ph;
    else { int64_t gap = (ws - s->wstart[i - 1]) / 86400; s->unw[i] = (gap <= 21 && !isnan(s->unw[i - 1])) ? s->unw[i - 1] + wrap180(ph - s->unw[i - 1]) : ph; }
    /* tốc độ 4 tuần */
    s->rate[i] = NAN;
    if (i >= 3 && (ws - s->wstart[i - 3]) / 86400 <= 28) { double x[4], y[4]; int ok = 1; for (int k = 0; k < 4; k++) { x[k] = (double)((s->wstart[i - 3 + k] - s->wstart[i - 3]) / 86400); y[k] = s->unw[i - 3 + k]; if (isnan(y[k])) ok = 0; } if (ok) s->rate[i] = linfit(x, y, 4).slope * 7.0; }
    /* tham chiếu 8 tuần trước theo lịch: tuần có wstart trong [ws-59d, ws-53d], lấy tuần muộn nhất có tốc độ */
    double prev = NAN; for (int k = 0; k < i; k++) { int64_t dd = (ws - s->wstart[k]) / 86400; if (dd >= s->lookback_days - s->lookback_tol && dd <= s->lookback_days + s->lookback_tol && !isnan(s->rate[k])) prev = s->rate[k]; }
    int flip = !isnan(s->rate[i]) && !isnan(prev) && ((s->rate[i] > 0) != (prev > 0)) && fabs(s->rate[i]) > s->min_rate && fabs(prev) > s->min_rate && !isnan(sd) && sd < s->sd_max;
    s->flag[i] = flip; s->n++;
    s->last_wstart = ws; s->last_wend = s->bin_last_ts; s->last_ph = ph; s->last_sd = sd; s->last_rate = s->rate[i]; s->last_prev8 = prev; s->last_flag = flip;
    s->last_alarm = flip && i > 0 && s->flag[i - 1];
    s->last_post_restart = 0; for (int r = 0; r < s->n_restarts; r++) { int64_t dd = (ws - s->restarts[r]); if (dd >= 0 && dd / 86400 <= s->post_restart_days) s->last_post_restart = 1; }
    s->has_week = 1;
}

int tc_push(tier_c_t *s, int64_t ts, float sn, float cs) {
    if (!s->have_origin) { s->origin_ts = day_of(ts) * 86400; s->have_origin = 1; }
    if (s->have_origin && ts < s->last_ts) return 0;           /* M1: mẫu lùi thời gian → bỏ */
    int64_t bin = (ts - s->origin_ts) / (7 * 86400); int closed = 0;
    if (s->cur_bin != INT64_MIN && bin != s->cur_bin) { close_week(s); closed = s->has_week; }
    if (bin != s->cur_bin) { s->cur_bin = bin; s->sumS = s->sumC = 0; s->n_rows = s->n_valid = 0; s->bin_first_ts = ts; }
    s->n_rows++; s->bin_last_ts = ts; s->last_ts = ts;
    if (!isnan(sn) && !isnan(cs)) { double a = atan2(sn, cs); s->sumS += sin(a); s->sumC += cos(a); s->n_valid++; }
    return closed;
}

int tc_flush(tier_c_t *s) { if (s->cur_bin == INT64_MIN) return 0; close_week(s); s->cur_bin = INT64_MIN; return s->has_week; }
