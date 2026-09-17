/* sae_int8.c — xem sae_int8.h. Mọi phép tính trong đường tính là số nguyên; float chỉ ở chuẩn hóa đầu vào và báo cáo. */
#include "sae_int8.h"
#include "sae_weights.h"
#include <math.h>

void sae_scale_input(const float amp[8], const float sn[8], const float cs[8], int32_t xq[24]) {
    float x[24];
    for (int i = 0; i < 8; i++) { x[i] = (amp[i] - SAE_SCALER_A[i]) / SAE_SCALER_B[i]; x[8 + i] = sn[i]; x[16 + i] = cs[i]; }
    for (int i = 0; i < 24; i++) {
        float v = rintf(x[i] * (float)(1 << SAE_X_Q));           /* rintf = làm tròn half-to-even như np.round (chế độ FE_TONEAREST) */
        if (v > (float)SAE_X_MAX) v = (float)SAE_X_MAX;             /* ±2^19 Q10 = ±512 đơn vị scale: xa mọi giá trị vật lý; script 26 định cỡ mult theo giới hạn này */
        if (v < -(float)SAE_X_MAX) v = -(float)SAE_X_MAX;
        xq[i] = (int32_t)v;
    }
}

/* tanh(z) với idx12 = z·4096, nội suy tuyến tính 16 bước giữa hai mục LUT (bước 1/256), bão hòa ngoài [-4,4). */
static inline int16_t tanh_lut_q15(int64_t idx12) {
    const int half = SAE_LUT_N / 2;
    int64_t i = (idx12 >> 4) + half; int f = (int)(idx12 & 15);
    if (i < 0) { i = 0; f = 0; } else if (i > SAE_LUT_N - 2) { i = SAE_LUT_N - 2; f = 16; }
    int32_t y0 = SAE_TANH_LUT[i], y1 = SAE_TANH_LUT[i + 1];
    return (int16_t)((y0 * (16 - f) + y1 * f + 8) >> 4);
}

int64_t sae_forward_spe_q30(const int32_t xq[24], int16_t xhat[24]) {
    int32_t a[24]; int32_t nxt[24];
    for (int i = 0; i < 24; i++) a[i] = xq[i];
    for (int l = 0; l < SAE_L; l++) {
        const int8_t *w8 = (const int8_t *)SAE_W[l]; const int16_t *w16 = (const int16_t *)SAE_W[l];
        for (int o = 0; o < SAE_N; o++) {
            int64_t acc = SAE_B[l][o];
            if (SAE_WBITS[l] == 16) { for (int i = 0; i < SAE_N; i++) acc += (int64_t)w16[o * SAE_N + i] * a[i]; }
            else                    { for (int i = 0; i < SAE_N; i++) acc += (int64_t)w8[o * SAE_N + i] * a[i]; }
            int64_t idx12 = (acc * (int64_t)SAE_MULT[l][o] + ((int64_t)1 << (SAE_SH[l] - 1))) >> SAE_SH[l];
            nxt[o] = tanh_lut_q15(idx12);
        }
        for (int i = 0; i < 24; i++) a[i] = nxt[i];
    }
    int64_t spe = 0;
    for (int i = 0; i < 24; i++) { xhat[i] = (int16_t)a[i]; int64_t d = (int64_t)xq[i] * (1 << (15 - SAE_X_Q)) - a[i]; spe += d * d; }
    return spe;                                                   /* Q30 */
}

float sae_spe(const int32_t xq[24], const int16_t xhat[24], float contrib[8]) {
    double per[8] = {0}, tot = 0;
    for (int i = 0; i < 24; i++) { double d = (double)xq[i] * (1 << (15 - SAE_X_Q)) - xhat[i]; d = d * d; per[i % 8] += d; tot += d; }
    for (int j = 0; j < 8; j++) contrib[j] = tot > 0 ? (float)(per[j] / tot) : 0.f;
    return (float)(tot / 1073741824.0);
}

unsigned sae_weights_bytes(void) { return SAE_WEIGHTS_BYTES; }
