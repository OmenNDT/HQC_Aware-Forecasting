/* stats_util.h — trung vị, hồi quy tuyến tính (double, khớp np.polyfit bậc 1), tiện ích ngày. */
#pragma once
#include <stdint.h>
#include <stddef.h>

typedef struct { double slope, intercept, se_slope; int n; } linfit_t;

double median_f(const float *v, int n);             /* sao chép + sắp xếp; n ≤ 256 */
linfit_t linfit(const double *x, const double *y, int n);   /* se_slope = sqrt(SSR/(n-2)/Sxx) như script 17 */
static inline int64_t day_of(int64_t ts) { return ts >= 0 ? ts / 86400 : -((-ts + 86399) / 86400); }
void day_to_str(int64_t day, char out[11]);          /* YYYY-MM-DD (UTC) */
