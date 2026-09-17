#include "tier_b_slopes.h"
#include "stats_util.h"
#include "hqc_params.h"
#include <math.h>
#include <string.h>

#define GAP_DAYS HQC_SEQ_GAP_DAYS

void tb_init(tier_b_t *s, float tau14, int consec14, float tau45, int consec45) {
    memset(s, 0, sizeof(*s)); s->tau14 = tau14; s->consec14 = consec14; s->tau45 = tau45; s->consec45 = consec45;
    s->cur_day = INT64_MIN; s->last_day = INT64_MIN; s->last14_day = s->last45_day = INT64_MIN; s->slope14 = s->slope45 = NAN;
}

/* dốc trên các ngày cùng đoạn với ngày cuối, ngày ≥ last - (win-1); cần ≥ min_obs; x = ngày − ngày đầu cửa sổ (đúng np.polyfit của Python) */
static double slope_window(const tier_b_t *s, int win, int min_obs) {
    double x[TB_DAYS], y[TB_DAYS]; int n = 0; int64_t last = s->day[s->n - 1]; int segl = s->seg[s->n - 1];
    for (int i = 0; i < s->n; i++) if (s->seg[i] == segl && s->day[i] >= last - (win - 1)) { x[n] = (double)s->day[i]; y[n] = s->lnmed[i]; n++; }
    if (n < min_obs) return NAN;
    double x0 = x[0]; for (int i = 0; i < n; i++) x[i] -= x0;
    return linfit(x, y, n).slope;
}

static void close_day(tier_b_t *s) {
    double med = median_f(s->buf, s->n_buf); s->n_buf = 0;
    if (!(med > 0)) { s->last_day = s->cur_day; s->last_med = med; s->slope14 = s->slope45 = NAN; s->flag14 = s->flag45 = s->alarm14 = s->alarm45 = 0; return; }
    if (s->n > 0 && s->cur_day - s->day[s->n - 1] > GAP_DAYS) s->seg_cur++;
    if (s->n == TB_DAYS) { memmove(s->day, s->day + 1, (TB_DAYS - 1) * sizeof(int64_t)); memmove(s->lnmed, s->lnmed + 1, (TB_DAYS - 1) * sizeof(double)); memmove(s->seg, s->seg + 1, (TB_DAYS - 1) * sizeof(int)); s->n--; }
    s->day[s->n] = s->cur_day; s->lnmed[s->n] = log(med); s->seg[s->n] = s->seg_cur; s->n++;
    s->slope14 = slope_window(s, HQC_SLOPE_DAYS, HQC_SLOPE_MIN_OBS); s->slope45 = slope_window(s, HQC_SLOW_DAYS, HQC_SLOW_MIN_OBS);
    s->flag14 = (!isnan(s->slope14) && s->slope14 > s->tau14); s->flag45 = (!isnan(s->slope45) && s->slope45 > s->tau45);
    /* alarm_days: đếm trên chuỗi các ngày CÓ dốc (NaN đã bỏ); "liên tiếp" = cách ngày có dốc trước ≤ 1 ngày */
    if (!isnan(s->slope14)) { int c = s->last14_day != INT64_MIN && s->cur_day - s->last14_day <= 1; s->run14 = s->flag14 ? (c ? s->run14 + 1 : 1) : 0; s->last14_day = s->cur_day; }
    if (!isnan(s->slope45)) { int c = s->last45_day != INT64_MIN && s->cur_day - s->last45_day <= 1; s->run45 = s->flag45 ? (c ? s->run45 + 1 : 1) : 0; s->last45_day = s->cur_day; }
    s->alarm14 = !isnan(s->slope14) && s->run14 >= s->consec14; s->alarm45 = !isnan(s->slope45) && s->run45 >= s->consec45;   /* ngày không có dốc: không báo */
    s->last_med = med; s->last_day = s->cur_day;
}

int tb_push(tier_b_t *s, int64_t ts, float spe) {
    int64_t d = day_of(ts); int closed = 0;
    if (s->cur_day != INT64_MIN && d < s->cur_day) return 0;   /* M1: mẫu lùi ngày → bỏ */
    if (s->cur_day != INT64_MIN && d != s->cur_day) { close_day(s); closed = 1; }
    if (d != s->cur_day) { s->cur_day = d; s->n_buf = 0; }
    if (!isnan(spe) && s->n_buf < TB_MAX_PER_DAY) s->buf[s->n_buf++] = spe;
    return closed;
}

int tb_flush(tier_b_t *s) { if (s->cur_day == INT64_MIN || s->n_buf == 0) return 0; close_day(s); s->cur_day = INT64_MIN; return 1; }
