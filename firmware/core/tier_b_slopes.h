/* tier_b_slopes.h — Tầng B trên chip: trung vị ngày của SPE → ln → dốc 14 ngày (≥10 quan sát) và 45 ngày (≥30) trên chuỗi liên tục
 * (cắt khi trống > 3 ngày) → báo khi dốc > τ trong n ngày liên tiếp (liên tiếp theo LỊCH, reset khi cách > 1 ngày).
 * Port từ scripts/New/13 (slope_series), 18 (slope_slow), alarm_utils.alarm_days. */
#pragma once
#include <stdint.h>

#define TB_DAYS 45
#define TB_MAX_PER_DAY 200

typedef struct {
    float tau14, tau45; int consec14, consec45;
    /* ngày đang gom */
    int64_t cur_day; float buf[TB_MAX_PER_DAY]; int n_buf;
    /* vòng 45 ngày đã đóng: ngày, ln(trung vị), id đoạn */
    int64_t day[TB_DAYS]; double lnmed[TB_DAYS]; int seg[TB_DAYS]; int n, seg_cur;
    int run14, run45; int64_t last14_day, last45_day;   /* đếm ngày liên tiếp vượt ngưỡng, ngày có dốc gần nhất */
    /* kết quả ngày vừa đóng */
    double last_med, slope14, slope45; int alarm14, alarm45, flag14, flag45; int64_t last_day;
} tier_b_t;

void tb_init(tier_b_t *s, float tau14, int consec14, float tau45, int consec45);
/* Nạp một mẫu SPE (đơn vị float) tại ts; nếu sang ngày mới thì đóng ngày cũ và trả 1 (kết quả ở các trường last_*). */
int tb_push(tier_b_t *s, int64_t ts, float spe);
int tb_flush(tier_b_t *s);                 /* đóng ngày đang gom (cuối luồng) */
