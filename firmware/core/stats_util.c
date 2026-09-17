#include "stats_util.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

double median_f(const float *v, int n) {
    float t[256]; if (n <= 0) return NAN; if (n > 256) n = 256;
    memcpy(t, v, n * sizeof(float));
    for (int i = 1; i < n; i++) { float k = t[i]; int j = i - 1; while (j >= 0 && t[j] > k) { t[j + 1] = t[j]; j--; } t[j + 1] = k; }
    return (n & 1) ? t[n / 2] : 0.5 * ((double)t[n / 2 - 1] + t[n / 2]);
}

linfit_t linfit(const double *x, const double *y, int n) {
    linfit_t r = {NAN, NAN, NAN, n}; if (n < 2) return r;
    double mx = 0, my = 0; for (int i = 0; i < n; i++) { mx += x[i]; my += y[i]; } mx /= n; my /= n;
    double sxx = 0, sxy = 0; for (int i = 0; i < n; i++) { sxx += (x[i] - mx) * (x[i] - mx); sxy += (x[i] - mx) * (y[i] - my); }
    if (sxx <= 0) return r;
    r.slope = sxy / sxx; r.intercept = my - r.slope * mx;
    double ssr = 0; for (int i = 0; i < n; i++) { double e = y[i] - (r.intercept + r.slope * x[i]); ssr += e * e; }
    r.se_slope = sqrt(ssr / (n - 2 > 0 ? n - 2 : 1) / sxx);
    return r;
}

void day_to_str(int64_t day, char out[11]) {                 /* thuật toán ngày dân dụng (Howard Hinnant) */
    int64_t z = day + 719468; int64_t era = (z >= 0 ? z : z - 146096) / 146097; int64_t doe = z - era * 146097;
    int64_t yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365; int64_t y = yoe + era * 400;
    int64_t doy = doe - (365 * yoe + yoe / 4 - yoe / 100); int64_t mp = (5 * doy + 2) / 153;
    int64_t d = doy - (153 * mp + 2) / 5 + 1; int64_t m = mp < 10 ? mp + 3 : mp - 9; if (m <= 2) y++;
    if (y < 0 || y > 9999) y = 0;                              /* ngoài phạm vi: in 0000 thay vì tràn đệm */
    snprintf(out, 11, "%04d-%02d-%02d", (int)y, (int)m, (int)d);
}
