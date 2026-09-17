/* hqc_engine.h — keo ba tầng: nhận mẫu 1X 10 phút, Direct theo giờ, sự kiện chạy lại; phát dòng JSON khi đóng ngày/tuần. */
#pragma once
#include <stdint.h>
#include "tier_b_slopes.h"
#include "tier_a_direct.h"
#include "tier_c_phase.h"

typedef void (*hqc_emit_fn)(const char *json_line, void *user);

typedef struct { tier_b_t b; tier_a_t a; tier_c_t c; hqc_emit_fn emit; void *user; uint32_t n_infer; int64_t last_spe_ts; float last_spe, last_contrib[8]; } hqc_t;

void hqc_init(hqc_t *h, hqc_emit_fn emit, void *user);
void hqc_sample_10min(hqc_t *h, int64_t ts, const float amp[8], const float sn[8], const float cs[8]);
void hqc_direct_hour(hqc_t *h, int64_t ts, const float v[8]);
void hqc_restart(hqc_t *h, int64_t ts);
void hqc_flush(hqc_t *h);
