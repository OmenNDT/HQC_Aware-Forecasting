#include "tier_a_direct.h"
#include "stats_util.h"
#include "hqc_params.h"
#include <math.h>
#include <string.h>

void ta_init(tier_a_t *s) {
    memset(s, 0, sizeof(*s)); s->limit_um = HQC_PLANT_LIMIT_UM; s->horizon_days = HQC_TIERA_HORIZON_DAYS; s->z90 = HQC_TIERA_Z90; s->rise_min = HQC_TIERA_RISE_MIN;
    s->window_rows = HQC_TIERA_WINDOW_ROWS; s->ref_days = HQC_TIERA_REF_DAYS; s->ref_min_obs = HQC_TIERA_REF_MIN_OBS; s->startup_skip = HQC_TIERA_STARTUP_SKIP; s->consec = HQC_TIERA_CONSEC;
    s->cur_day = INT64_MIN; s->last_day = INT64_MIN; s->last_kept_day = INT64_MIN; s->last_stopped_day = INT64_MIN; s->last_flag_day = INT64_MIN;
    s->skip_left = s->startup_skip;                            /* H1 code review: khởi động = sau một lần dừng, bỏ 2 hàng đầu như Python có lịch sử */
}

static void project_last_row(tier_a_t *s) {
    int i = s->n - 1; int64_t t = s->day[i]; double x[TA_ROWS], y[TA_ROWS]; int idx[TA_ROWS], nw = 0;
    for (int k = (i - s->window_rows + 1 > 0 ? i - s->window_rows + 1 : 0); k <= i; k++) if (s->seg[k] == s->seg[i]) idx[nw++] = k;
    s->has_row = 1; s->flag_any = 0;
    if (nw < 8) { for (int c = 0; c < TA_CH; c++) { s->flag_ch[c] = 0; s->level[c] = s->days_left_low[c] = s->ref_med[c] = s->t_stat[c] = NAN; } s->has_row = 0; return; }
    for (int c = 0; c < TA_CH; c++) {
        for (int k = 0; k < nw; k++) { x[k] = (double)(s->day[idx[k]] - s->day[idx[0]]); y[k] = s->val[idx[k]][c]; }
        linfit_t f = linfit(x, y, nw); double level = f.intercept + f.slope * x[nw - 1];
        double tstat = f.se_slope > 0 ? f.slope / f.se_slope : INFINITY; double b_hi = f.slope + s->z90 * f.se_slope;
        double dl_low = b_hi > 0 ? (s->limit_um - level) / b_hi : INFINITY;
        float ref[TA_ROWS]; int nr = 0;
        for (int k = 0; k < i; k++) if (s->day[k] >= t - s->ref_days && s->day[k] <= t - 1) ref[nr++] = s->val[k][c];
        double rm = nr >= s->ref_min_obs ? median_f(ref, nr) : NAN;
        int rising = !isnan(rm) && level > (1 + s->rise_min) * rm;
        s->level[c] = (float)level; s->t_stat[c] = (float)tstat; s->days_left_low[c] = (float)dl_low; s->ref_med[c] = (float)rm;
        s->flag_ch[c] = rising && tstat > s->z90 && dl_low < s->horizon_days; if (s->flag_ch[c]) s->flag_any = 1;
    }
}

static void close_day(tier_a_t *s) {
    int64_t d = s->cur_day; s->last_day = d; s->has_row = 0; s->flag_any = 0; s->alarm = 0;
    float med[TA_CH]; int complete = 1;
    for (int c = 0; c < TA_CH; c++) { if (s->n_hour[c] == 0) { complete = 0; break; } med[c] = (float)median_f(s->hour_vals[c], s->n_hour[c]); }
    if (s->stopped_today) s->last_stopped_day = d;
    if (!complete) return;                                     /* dropna(how="any") */
    /* cắt đoạn: có ngày dừng thật trong (ngày giữ trước, d] */
    int brk = s->last_kept_day != INT64_MIN && s->last_stopped_day != INT64_MIN && s->last_stopped_day > s->last_kept_day && s->last_stopped_day <= d;
    if (brk) { s->seg_cur++; s->skip_left = s->startup_skip; }
    s->last_kept_day = d;
    if (s->skip_left > 0) { s->skip_left--; return; }           /* hàng bị bỏ sau khởi động: không vào bảng */
    if (s->n == TA_ROWS) { memmove(s->day, s->day + 1, (TA_ROWS - 1) * sizeof(int64_t)); memmove(s->val, s->val + 1, (TA_ROWS - 1) * sizeof(s->val[0])); memmove(s->seg, s->seg + 1, (TA_ROWS - 1) * sizeof(int)); s->n--; }
    s->day[s->n] = d; memcpy(s->val[s->n], med, sizeof(med)); s->seg[s->n] = s->seg_cur; s->n++;
    project_last_row(s);
    if (!s->has_row) return;
    /* alarm_days(flag ngày, 0.5, 2): liên tiếp theo lịch trên chuỗi các hàng có kết quả */
    int contiguous = s->last_flag_day != INT64_MIN && d - s->last_flag_day <= 1;
    s->run = s->flag_any ? (contiguous ? s->run + 1 : 1) : 0; s->last_flag_day = d;
    s->alarm = s->run >= s->consec;
}

int ta_push_hour(tier_a_t *s, int64_t ts, const float v[TA_CH]) {
    int64_t d = day_of(ts); int closed = 0;
    if (s->cur_day != INT64_MIN && d < s->cur_day) return 0;   /* M1: mẫu lùi ngày → bỏ */
    if (s->cur_day != INT64_MIN && d != s->cur_day) { close_day(s); closed = 1; }
    if (d != s->cur_day) { s->cur_day = d; memset(s->n_hour, 0, sizeof(s->n_hour)); s->stopped_today = 0; }
    int known = 0, running = 0; for (int c = 0; c < TA_CH; c++) { if (!isnan(v[c])) { known++; if (v[c] > 3.0f) running++; } }
    if (known >= 6) {
        if (running >= 6) { for (int c = 0; c < TA_CH; c++) if (!isnan(v[c]) && s->n_hour[c] < 24) s->hour_vals[c][s->n_hour[c]++] = v[c]; }
        else s->stopped_today = 1;
    }
    return closed;
}

int ta_flush(tier_a_t *s) { if (s->cur_day == INT64_MIN) return 0; close_day(s); s->cur_day = INT64_MIN; return 1; }
