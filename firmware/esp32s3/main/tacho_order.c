/* tacho_order.c — ISR tacho ghi thời điểm xung; mỗi mẫu gia tốc được gán góc trục θ = 2π·(t − t_xung)/(chu kỳ xung)/PPR + pha xung.
 * Order tracking 1X: S = Σ x·sin θ, C = Σ x·cos θ → amp = 2·√(S²+C²)/n, pha = atan2. RMS lấy trên thành phần AC (trừ trung bình). */
#include "tacho_order.h"
#include "bench_pins.h"
#include <math.h>
#include "driver/gpio.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/portmacro.h"

static volatile int64_t s_t_last = 0, s_t_prev = 0;   /* hai xung gần nhất */
static volatile uint32_t s_pulse_count = 0;
static portMUX_TYPE s_mux = portMUX_INITIALIZER_UNLOCKED;

static double s_S = 0, s_C = 0, s_sum = 0, s_sum2 = 0; static int s_n = 0; static uint32_t s_pulse_at_open = 0; static int64_t s_t_open = 0;

static void IRAM_ATTR __attribute__((unused)) tacho_isr(void *arg) {
    (void)arg; int64_t now = esp_timer_get_time();
    portENTER_CRITICAL_ISR(&s_mux);
    if (now - s_t_last > 300) { s_t_prev = s_t_last; s_t_last = now; s_pulse_count++; }   /* lọc dội < 300 µs (tương đương > 100.000 vòng/phút) */
    portEXIT_CRITICAL_ISR(&s_mux);
}

void tacho_init(void) {
    /* Đọc tacho bằng lấy mẫu 1 kHz trong task lấy mẫu (tacho_poll), không dùng ngắt: dây dài + pull-up nội yếu nhiễm nhiễu
     * gây hàng nghìn xung/giây. Mức phải giữ nguyên 2 mẫu liên tiếp (2 ms) mới tính là cạnh; quạt < 6000 vòng/phút → xung ≤ 200 Hz. */
    gpio_config_t io = { .pin_bit_mask = 1ULL << PIN_TACHO, .mode = GPIO_MODE_INPUT, .pull_up_en = GPIO_PULLUP_ENABLE, .intr_type = GPIO_INTR_DISABLE };
    gpio_config(&io);
    gpio_install_isr_service(0);   /* vẫn cài service cho các module khác (encoder) */
    s_t_open = esp_timer_get_time(); s_pulse_at_open = 0;
}

static volatile uint32_t s_raw_edges = 0; static volatile int s_raw_lvl = 1;
uint32_t tacho_raw_edges(void) { uint32_t e = s_raw_edges; s_raw_edges = 0; return e; }
int tacho_raw_level(void) { return s_raw_lvl; }
void tacho_poll(int64_t now) {
    static int lvl = 1, cand = 1, cand_n = 0;
    int v = gpio_get_level(PIN_TACHO); if (v != s_raw_lvl) s_raw_edges++; s_raw_lvl = v;
    if (v != cand) { cand = v; cand_n = 1; return; }
    if (++cand_n < 2 || cand == lvl) return;           /* chưa ổn định 2 mẫu, hoặc không đổi mức */
    lvl = cand;
    if (lvl == 0 && now - s_t_last > 4000) {            /* cạnh xuống, tối thiểu 4 ms giữa hai xung (≤ 7500 vòng/phút với 2 xung/vòng) */
        portENTER_CRITICAL(&s_mux); s_t_prev = s_t_last; s_t_last = now; s_pulse_count++; portEXIT_CRITICAL(&s_mux);
    }
}

void order_push_sample(int64_t t_us, float x_mg) {
    int64_t t_last, t_prev; uint32_t cnt;
    portENTER_CRITICAL(&s_mux); t_last = s_t_last; t_prev = s_t_prev; cnt = s_pulse_count; portEXIT_CRITICAL(&s_mux);
    s_sum += x_mg; s_sum2 += (double)x_mg * x_mg; s_n++;
    int64_t period = t_last - t_prev;
    if (period <= 0 || t_us - t_last > 2 * period) return;   /* chưa có xung hoặc quạt dừng: không tính góc */
    double frac = (double)(t_us - t_last) / (double)period;  /* phần chu kỳ xung đã trôi qua */
    double theta = 2.0 * M_PI * ((double)(cnt % TACHO_PULSES_PER_REV) + frac) / TACHO_PULSES_PER_REV;
    s_S += x_mg * sin(theta); s_C += x_mg * cos(theta);
}

int order_close_block(order_block_t *out) {
    int64_t now = esp_timer_get_time(); uint32_t cnt; int64_t t_last, t_prev;
    portENTER_CRITICAL(&s_mux); cnt = s_pulse_count; t_last = s_t_last; t_prev = s_t_prev; portEXIT_CRITICAL(&s_mux);
    uint32_t pulses = cnt - s_pulse_at_open; double dt_s = (now - s_t_open) / 1e6;
    out->n_samples = s_n; out->n_revs = (int)(pulses / TACHO_PULSES_PER_REV);
    out->rpm = (dt_s > 0 && now - t_last < 500000) ? (float)(pulses / (double)TACHO_PULSES_PER_REV / dt_s * 60.0) : 0.f;
    double mean = s_n ? s_sum / s_n : 0, var = s_n ? s_sum2 / s_n - mean * mean : 0;
    out->rms_mg = var > 0 ? (float)sqrt(var) : 0.f;
    /* trừ thành phần DC ra khỏi S, C: Σ mean·sinθ ≈ 0 trên số vòng nguyên, bỏ qua phần dư */
    out->amp1x_mg = s_n ? (float)(2.0 * sqrt(s_S * s_S + s_C * s_C) / s_n) : 0.f;
    out->phase_deg = (float)(atan2(s_S, s_C) * 180.0 / M_PI);
    if (out->rpm > 8000.f) { out->rpm = 0.f; out->n_revs = 0; }   /* quá nhanh cho quạt = nhiễu */
    out->valid = (out->n_revs >= 3 && s_n >= 100) ? 1 : 0;
    (void)t_prev;
    s_S = s_C = s_sum = s_sum2 = 0; s_n = 0; s_pulse_at_open = cnt; s_t_open = now;
    return out->valid;
}
