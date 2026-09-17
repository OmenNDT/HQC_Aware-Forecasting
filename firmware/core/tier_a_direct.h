/* tier_a_direct.h — Tầng A trên chip: Direct theo giờ (8 kênh, NaN cho phép) → cổng máy chạy theo giờ → trung vị ngày trên giờ chạy
 * → đoạn chạy (cắt tại ngày dừng thật, bỏ 2 hàng sau) → hồi quy 14 hàng cùng đoạn (≥8) → còn bao nhiêu ngày tới 65 (cận dưới 90 %)
 * → cờ khi kênh leo > 1,10 × trung vị 90 ngày trước (≥30 hàng), t > 1,645, cận dưới < 30 → báo khi 2 ngày liên tiếp.
 * Port từ scripts/New/17_tier_a_direct_projection.py. */
#pragma once
#include <stdint.h>

#define TA_ROWS 100                         /* giữ 100 hàng ngày (đủ cửa sổ 90 ngày + 14) */
#define TA_CH 8

typedef struct {
    float limit_um, horizon_days, z90, rise_min; int window_rows, ref_days, ref_min_obs, startup_skip, consec;
    /* ngày đang gom */
    int64_t cur_day; float hour_vals[TA_CH][24]; int n_hour[TA_CH]; int stopped_today; int64_t last_stopped_day;
    /* bảng ngày đã giữ (không gồm hàng bị bỏ sau khởi động) */
    int64_t day[TA_ROWS]; float val[TA_ROWS][TA_CH]; int seg[TA_ROWS]; int n, seg_cur, skip_left; int64_t last_kept_day;
    /* kết quả ngày vừa đóng */
    int64_t last_day; int has_row, flag_any, alarm, run; int flag_ch[TA_CH]; float level[TA_CH], days_left_low[TA_CH], ref_med[TA_CH], t_stat[TA_CH];
    int64_t last_flag_day;
} tier_a_t;

void ta_init(tier_a_t *s);
int ta_push_hour(tier_a_t *s, int64_t ts, const float v[TA_CH]);   /* trả 1 khi đóng một ngày */
int ta_flush(tier_a_t *s);
