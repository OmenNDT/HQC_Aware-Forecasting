#include "hqc_engine.h"
#include "sae_int8.h"
#include "stats_util.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "hqc_params.h"                       /* ngưỡng khóa phase 01/02, SINH TỰ ĐỘNG bởi script 26 */
#define TAU14 HQC_TAU14
#define TAU45 HQC_TAU45
#define CONSEC14 HQC_CONSEC14
#define CONSEC45 HQC_CONSEC45

static const char *fnum(double v, char *buf) { if (isnan(v) || isinf(v)) return "null"; snprintf(buf, 24, "%.6g", v); return buf; }

void hqc_init(hqc_t *h, hqc_emit_fn emit, void *user) { memset(h, 0, sizeof(*h)); tb_init(&h->b, TAU14, CONSEC14, TAU45, CONSEC45); ta_init(&h->a); tc_init(&h->c); h->emit = emit; h->user = user; }

static void emit_b(hqc_t *h) {
    char d[11], b1[24], b2[24], b3[24], line[256]; day_to_str(h->b.last_day, d);
    snprintf(line, sizeof line, "{\"t\":\"B\",\"day\":\"%s\",\"spe_med\":%s,\"slope14\":%s,\"slope45\":%s,\"B14\":%d,\"B45\":%d}", d, fnum(h->b.last_med, b1), fnum(h->b.slope14, b2), fnum(h->b.slope45, b3), h->b.alarm14, h->b.alarm45);
    h->emit(line, h->user);
}
static void emit_a(hqc_t *h) {
    char d[11], line[512], b1[24], b2[24]; day_to_str(h->a.last_day, d); int best = -1;
    for (int c = 0; c < 8; c++) if (h->a.flag_ch[c] && (best < 0 || h->a.days_left_low[c] < h->a.days_left_low[best])) best = c;
    snprintf(line, sizeof line, "{\"t\":\"A\",\"day\":\"%s\",\"row\":%d,\"flag\":%d,\"A\":%d,\"ch\":%d,\"dl_low\":%s,\"level_2001X\":%s}", d, h->a.has_row, h->a.flag_any, h->a.alarm, best, fnum(best >= 0 ? h->a.days_left_low[best] : NAN, b1), fnum(h->a.has_row ? h->a.level[0] : NAN, b2));
    h->emit(line, h->user);
}
static void emit_c(hqc_t *h) {
    char ws[11], we[11], line[320], b1[24], b2[24], b3[24], b4[24]; day_to_str(day_of(h->c.last_wstart), ws); day_to_str(day_of(h->c.last_wend), we);
    snprintf(line, sizeof line, "{\"t\":\"C\",\"week\":\"%s\",\"week_end\":\"%s\",\"ph\":%s,\"sd\":%s,\"rate\":%s,\"prev8\":%s,\"flag\":%d,\"C\":%d,\"post_restart\":%d}", ws, we, fnum(h->c.last_ph, b1), fnum(h->c.last_sd, b2), fnum(h->c.last_rate, b3), fnum(h->c.last_prev8, b4), h->c.last_flag, h->c.last_alarm, h->c.last_post_restart);
    h->emit(line, h->user);
}

void hqc_sample_10min(hqc_t *h, int64_t ts, const float amp[8], const float sn[8], const float cs[8]) {
    int32_t xq[24]; int16_t xhat[24]; int any_nan = 0;
    for (int i = 0; i < 8; i++) if (isnan(amp[i]) || isnan(sn[i]) || isnan(cs[i])) any_nan = 1;
    float spe = NAN;
    if (!any_nan) { sae_scale_input(amp, sn, cs, xq); sae_forward_spe_q30(xq, xhat); spe = sae_spe(xq, xhat, h->last_contrib); h->n_infer++; }
    h->last_spe = spe; h->last_spe_ts = ts;
    if (tb_push(&h->b, ts, spe)) emit_b(h);
    if (tc_push(&h->c, ts, sn[0], cs[0])) emit_c(h);
}

void hqc_direct_hour(hqc_t *h, int64_t ts, const float v[8]) { if (ta_push_hour(&h->a, ts, v)) emit_a(h); }
void hqc_restart(hqc_t *h, int64_t ts) { tc_restart(&h->c, ts); }
void hqc_flush(hqc_t *h) { if (tb_flush(&h->b)) emit_b(h); if (ta_flush(&h->a)) emit_a(h); if (tc_flush(&h->c)) emit_c(h); }
