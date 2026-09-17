/* sae_int8.h — suy luận SAE 24→24×6 bằng số nguyên (trọng số int8/int16 per-layer, kích hoạt int16 Q15, tanh LUT nội suy).
 * Port 1:1 từ scripts/New/26_quantize_sae_int8.py::forward_int; hằng số trong sae_weights.h (sinh tự động). */
#pragma once
#include <stdint.h>

/* Chuẩn hóa đầu vào: 8 biên độ 1X (µm) qua scaler minmax của nền 9b, 8 sin, 8 cos giữ nguyên → 24 số Q10. */
void sae_scale_input(const float amp[8], const float sn[8], const float cs[8], int32_t xq[24]);   /* int32: không kẹp (H3) */

/* Suy luận: xq[24] Q10 → xhat[24] Q15. Trả SPE ở dạng Q30 (chia 2^30 ra đơn vị SPE float), tổng int64. */
int64_t sae_forward_spe_q30(const int32_t xq[24], int16_t xhat[24]);

/* Tổng byte hằng số mô hình trên flash (W + b + mult + LUT), lấy từ sae_weights.h. */
unsigned sae_weights_bytes(void);

/* SPE float và đóng góp từng kênh (r²amp + r²sin + r²cos)/SPE, 8 kênh. */
float sae_spe(const int32_t xq[24], const int16_t xhat[24], float contrib[8]);
