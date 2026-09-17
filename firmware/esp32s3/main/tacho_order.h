/* tacho_order.h — xung tacho quạt + order tracking 1X: gom mẫu gia tốc theo góc trục, mỗi khối ~1 s trả biên độ/pha 1X và RMS. */
#pragma once
#include <stdint.h>
typedef struct { float rpm; float amp1x_mg; float phase_deg; float rms_mg; int n_samples; int n_revs; int valid; } order_block_t;
void tacho_init(void);                       /* GPIO ngắt cạnh xuống, pull-up nội */
void tacho_poll(int64_t t_us);
uint32_t tacho_raw_edges(void);            /* số lần đổi mức thô kể từ lần gọi trước (chẩn đoán) */
int tacho_raw_level(void);                 /* mức hiện tại của chân tacho */              /* gọi mỗi 1 ms từ task lấy mẫu, trước order_push_sample */
void order_push_sample(int64_t t_us, float x_mg);   /* gọi ở tốc độ lấy mẫu; tự tra góc trục từ xung tacho */
int  order_close_block(order_block_t *out); /* đóng khối hiện tại, trả 1 nếu có đủ xung tacho và mẫu */
