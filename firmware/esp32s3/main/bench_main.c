/* bench_main.c — chế độ BÀN THỬ (phase 05): ADXL345 trên khung quạt + tacho → biên độ 1X, RMS mỗi giây; điểm = tỉ số so với nền khỏe
 * (chụp bằng nút BOOT) nhân hệ số gây lỗi (KY-040 / 3 nút kịch bản). Ba tầng: A xanh < 1,5 · B vàng < 3 · C đỏ ≥ 3 (còi).
 * Servo chỉ điểm 0–100, OLED hiện số, JSON mỗi giây ra cổng USB gốc (im lặng 5 s sau mỗi dòng phát lại nhận được để không chen vào demo web).
 * Chạy song song với chế độ phát lại trong main.c; bật bằng HQC_BENCH=1 idf.py build.
 * Không chạy SAE trên quạt: mô hình train trên dữ liệu nhà máy, bàn thử chỉ minh hoạ chuỗi cảm biến → đặc trưng → ngưỡng. */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "driver/usb_serial_jtag.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "bench_pins.h"
#include "adxl345_spi.h"
#include "ssd1306_i2c.h"
#include "tacho_order.h"
#include "led_status.h"
#include "bench_main.h"

static const char *TAG = "bench";
static volatile int s_enc_delta = 0;                 /* KY-040: +1/−1 mỗi khấc */
static float s_gain = 1.0f, s_base_amp = 0.f, s_base_rms = 0.f, s_base_rpm = 0.f; static int s_have_base = 0, s_gated = 0;
static order_block_t s_last; static int s_tier = 0;   /* 0 chưa có nền, 1 A, 2 B, 3 C */
static adc_oneshot_unit_handle_t s_adc;
static volatile int16_t s_raw[3]; static int s_oled_ok = 0, s_adxl_ok = 0;
static volatile int64_t s_replay_seen_us = -10000000;   /* thời điểm nhận dòng phát lại gần nhất */
void bench_note_replay_activity(void) { s_replay_seen_us = esp_timer_get_time(); }
static volatile int s_replay_tier = 0;
void bench_replay_tier(int worst) { s_replay_tier = worst; }

static void IRAM_ATTR enc_isr(void *arg) { (void)arg; s_enc_delta += gpio_get_level(PIN_ENC_DT) ? 1 : -1; }

static void gpio_setup(void) {
    gpio_config_t out = { .pin_bit_mask = (1ULL << PIN_LED_RED) | (1ULL << PIN_LED_YELLOW) | (1ULL << PIN_LED_GREEN) | (1ULL << PIN_BUZZER), .mode = GPIO_MODE_OUTPUT };
    gpio_config(&out);
    gpio_config_t in = { .pin_bit_mask = (1ULL << PIN_BTN_HEALTHY) | (1ULL << PIN_BTN_APRIL) | (1ULL << PIN_BTN_MAY) | (1ULL << PIN_BTN_BOOT),
                         .mode = GPIO_MODE_INPUT, .pull_up_en = GPIO_PULLUP_ENABLE };
    gpio_config(&in);
#if PIN_ENC_CLK >= 0
    gpio_config_t enc_in = { .pin_bit_mask = (1ULL << PIN_ENC_DT) | (1ULL << PIN_ENC_SW), .mode = GPIO_MODE_INPUT, .pull_up_en = GPIO_PULLUP_ENABLE };
    gpio_config(&enc_in);
    gpio_config_t clk = { .pin_bit_mask = 1ULL << PIN_ENC_CLK, .mode = GPIO_MODE_INPUT, .pull_up_en = GPIO_PULLUP_ENABLE, .intr_type = GPIO_INTR_NEGEDGE };
    gpio_config(&clk); gpio_isr_handler_add(PIN_ENC_CLK, enc_isr, NULL);   /* isr service đã cài trong tacho_init */
#endif
    /* servo: LEDC 50 Hz, 14 bit; quạt PWM 25 kHz tuỳ chọn (để 100 %) */
    ledc_timer_config_t st = { .speed_mode = LEDC_LOW_SPEED_MODE, .timer_num = LEDC_TIMER_0, .duty_resolution = LEDC_TIMER_14_BIT, .freq_hz = 50, .clk_cfg = LEDC_AUTO_CLK };
    ledc_timer_config(&st);
#if PIN_SERVO >= 0
    ledc_channel_config_t sc = { .gpio_num = PIN_SERVO, .speed_mode = LEDC_LOW_SPEED_MODE, .channel = LEDC_CHANNEL_0, .timer_sel = LEDC_TIMER_0, .duty = 0 };
    ledc_channel_config(&sc);
#endif
    ledc_timer_config_t ft = { .speed_mode = LEDC_LOW_SPEED_MODE, .timer_num = LEDC_TIMER_1, .duty_resolution = LEDC_TIMER_8_BIT, .freq_hz = 25000, .clk_cfg = LEDC_AUTO_CLK };
    ledc_timer_config(&ft);
    ledc_channel_config_t fc = { .gpio_num = PIN_FAN_PWM, .speed_mode = LEDC_LOW_SPEED_MODE, .channel = LEDC_CHANNEL_1, .timer_sel = LEDC_TIMER_1, .duty = 255 };
    ledc_channel_config(&fc);
#if PIN_POT_SPEED >= 0
    adc_oneshot_unit_init_cfg_t ac = { .unit_id = ADC_UNIT_1 };
    adc_oneshot_new_unit(&ac, &s_adc);
    adc_oneshot_chan_cfg_t cc = { .atten = ADC_ATTEN_DB_12, .bitwidth = ADC_BITWIDTH_DEFAULT };
    adc_oneshot_config_channel(s_adc, ADC_CHANNEL_1, &cc);   /* GPIO2 = ADC1_CH1 */
#endif
}

static void servo_score(float score) {                /* 0–100 điểm → 0–180° → 0,5–2,5 ms trên 20 ms, 14 bit */
    if (score < 0) score = 0;
    if (score > 100) score = 100;
#if PIN_SERVO >= 0
    uint32_t duty = (uint32_t)((0.5f + 2.0f * score / 100.f) / 20.f * 16383.f);
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, duty); ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
#else
    (void)score;
#endif
}
static void leds(int tier, int beep, int touch_rgb) {
    gpio_set_level(PIN_LED_GREEN, tier == 1); gpio_set_level(PIN_LED_YELLOW, tier == 2); gpio_set_level(PIN_LED_RED, tier == 3);
    gpio_set_level(PIN_BUZZER, beep); if (touch_rgb) led_status_set(tier == 0 ? 0 : tier);   /* LED RGB onboard nhường cho chế độ phát lại khi đang nhận dữ liệu */
}

/* task lấy mẫu 1 kHz (tick FreeRTOS = 1 ms): trục X của ADXL345 bắt cứng theo phương ngang qua tâm quạt */
static void sample_task(void *arg) {
    (void)arg; TickType_t t = xTaskGetTickCount(); int16_t x, y, z;
    for (;;) { vTaskDelayUntil(&t, 1); tacho_poll(esp_timer_get_time()); if (adxl345_read_xyz(&x, &y, &z) == 0) { s_raw[0] = x; s_raw[1] = y; s_raw[2] = z; order_push_sample(esp_timer_get_time(), adxl345_lsb_to_mg(x)); } }
}

static void draw(float score, float ratio, int pot) {
    char b[32]; oled_clear();
    snprintf(b, sizeof b, "%4.0f RPM  G%.1f", (double)s_last.rpm, (double)s_gain); oled_text(0, 0, b, 1);
    snprintf(b, sizeof b, "1X %5.0f MG", (double)s_last.amp1x_mg); oled_text(0, 10, b, 1);
    snprintf(b, sizeof b, "RMS%5.0f MG", (double)s_last.rms_mg); oled_text(0, 20, b, 1);
    if (!s_have_base) { oled_text(0, 34, "BAM BOOT = NEN", 1); oled_text(0, 46, "KHOE", 2); }
    else if (s_gated) { oled_text(0, 34, "NGOAI CONG LOC", 1); oled_text(0, 46, "TOC DO THAP", 2); }
    else { snprintf(b, sizeof b, "%3.0f", (double)score); oled_text(0, 34, b, 3);
           static const char *name[4] = { "--", "A BINH THUONG", "B CAN XEM", "C BAT THUONG" }; oled_text(64, 34, name[s_tier], 1);
           snprintf(b, sizeof b, "X%.2f P%d", (double)ratio, pot); oled_text(64, 46, b, 1); oled_bar(64, 56, 62, 7, (int)(score * 0.62f)); }
    oled_flush();
}

static void bench_task(void *arg) {
    (void)arg; tacho_init(); gpio_setup();
    int oled_ok = oled_init() == 0, adxl_ok = adxl345_init() == 0; s_oled_ok = oled_ok; s_adxl_ok = adxl_ok;
    if (oled_ok) { oled_text(0, 0, "HQC BENCH", 2); oled_text(0, 20, adxl_ok ? "ADXL345 OK" : "ADXL345 LOI", 1); oled_text(0, 32, "QUAY QUAT, CHO 3S", 1); oled_flush(); }
    xTaskCreatePinnedToCore(sample_task, "adxl", 4096, NULL, 10, NULL, 1);
    char line[384]; int beep_ticks = 0, boot_prev = 1, sw_prev = 1, b_prev[3] = { 1, 1, 1 }; float base_acc = 0; int base_n = 0;
    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(1000));
        order_close_block(&s_last);
        /* tự dò lại thiết bị chưa thấy (cắm dây lúc đang chạy) */
        if (!s_adxl_ok && adxl345_probe() == 0) s_adxl_ok = adxl_ok = 1;
        if (!s_oled_ok && oled_init() == 0) { s_oled_ok = oled_ok = 1; }
        /* núm và nút */
        int d = s_enc_delta; s_enc_delta = 0; if (d) { s_gain *= powf(1.15f, (float)d); s_gain = s_gain < 0.5f ? 0.5f : (s_gain > 8.f ? 8.f : s_gain); }
#if PIN_ENC_CLK >= 0
        int sw = gpio_get_level(PIN_ENC_SW); if (!sw && sw_prev) s_gain = 1.0f; sw_prev = sw;
#else
        (void)sw_prev;
#endif
        const int bpin[3] = { PIN_BTN_HEALTHY, PIN_BTN_APRIL, PIN_BTN_MAY }; const float bgain[3] = { 1.0f, 1.8f, 3.5f };
        for (int i = 0; i < 3; i++) { int v = gpio_get_level(bpin[i]);
            if (!v && b_prev[i]) { s_gain = bgain[i]; char ev[40]; int n = snprintf(ev, sizeof ev, "{\"t\":\"BTN\",\"n\":%d}\n", i + 1); usb_serial_jtag_write_bytes(ev, n, pdMS_TO_TICKS(50)); }
            b_prev[i] = v; }
        int boot = gpio_get_level(PIN_BTN_BOOT);
        if (!boot && boot_prev) { base_acc = 0; base_n = 0; s_have_base = 0; }                    /* bắt đầu chụp nền: trung bình 3 khối kế tiếp */
        boot_prev = boot;
        if (!s_have_base && s_last.valid && base_n < 3 && base_acc >= 0) { base_acc += s_last.amp1x_mg; base_n++;
            if (base_n == 3) { s_base_amp = base_acc / 3.f; s_base_rms = s_last.rms_mg; s_base_rpm = s_last.rpm; s_have_base = 1; if (s_base_amp < 5.f) s_base_amp = 5.f; } }
        /* điểm: tỉ số 1X so với nền (nhân hệ số), thang log qua 3 mốc như demo_monitor: 1× → 20, 1,5× → 70, 4× → 95 */
        float ratio = s_have_base && s_last.valid ? s_last.amp1x_mg * s_gain / s_base_amp : 0.f;
        float score = 0.f;
        if (ratio > 0) { float l = logf(ratio); float l1 = logf(1.5f), l2 = logf(4.f);
            score = l <= 0 ? 20.f * expf(l) : (l < l1 ? 20.f + 50.f * l / l1 : 70.f + 25.f * (l - l1) / (l2 - l1)); if (score > 100) score = 100; }
        s_tier = !s_have_base || !s_last.valid ? 0 : (ratio < 1.5f ? 1 : (ratio < 3.f ? 2 : 3));
        int pot = 4095;   /* không có biến trở: quạt toàn tốc */
#if PIN_POT_SPEED >= 0
        adc_oneshot_read(s_adc, ADC_CHANNEL_1, &pot);
#endif
        /* biến trở = điều tốc quạt qua dây PWM (30–100 %); cổng lọc tải: rpm < 70 % rpm nền → không chấm điểm, như 'máy dừng' ở nhà máy */
        uint32_t duty = 77 + (uint32_t)(pot * 178 / 4095); ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1, duty); ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1);
        s_gated = s_have_base && s_base_rpm > 0 && s_last.rpm < 0.7f * s_base_rpm;
        if (s_gated) { s_tier = 0; score = 0; ratio = 0; }
        beep_ticks = s_tier == 3 ? (beep_ticks + 1) : 0;
        int replay_busy = esp_timer_get_time() - s_replay_seen_us < 5000000;
        if (replay_busy) { int rt = s_replay_tier; static int rb = 0; rb = rt == 3 ? rb + 1 : 0; leds(rt, rt == 3 && (rb % 2) == 1, 0); }
        else leds(s_tier, s_tier == 3 && (beep_ticks % 2) == 1, 1);
        servo_score(score);
        if (oled_ok) draw(score, ratio, pot * 100 / 4095);
        snprintf(line, sizeof line, "{\"t\":\"BENCH\",\"rpm\":%.0f,\"amp1x_mg\":%.1f,\"phase_deg\":%.0f,\"rms_mg\":%.1f,\"n\":%d,\"revs\":%d,\"base_mg\":%.1f,\"gain\":%.2f,\"ratio\":%.2f,\"score\":%.0f,\"tier\":%d,\"pot\":%d,\"gated\":%d,\"adxl_ok\":%d,\"devid\":\"0x%02X\",\"oled_ok\":%d,\"i2c\":\"%s\",\"xyz\":[%d,%d,%d],\"btn\":[%d,%d,%d],\"boot\":%d,\"tacho_lvl\":%d,\"tacho_edges\":%lu}\n",
                 (double)s_last.rpm, (double)s_last.amp1x_mg, (double)s_last.phase_deg, (double)s_last.rms_mg, s_last.n_samples, s_last.n_revs,
                 (double)s_base_amp, (double)s_gain, (double)ratio, (double)score, s_tier, pot, s_gated, s_adxl_ok, adxl345_devid(), s_oled_ok, oled_i2c_found(), s_raw[0], s_raw[1], s_raw[2], gpio_get_level(PIN_BTN_HEALTHY), gpio_get_level(PIN_BTN_APRIL), gpio_get_level(PIN_BTN_MAY), gpio_get_level(PIN_BTN_BOOT), tacho_raw_level(), (unsigned long)tacho_raw_edges());
        if (!replay_busy) usb_serial_jtag_write_bytes(line, strlen(line), pdMS_TO_TICKS(50));
        ESP_LOGD(TAG, "%s", line);
    }
}

void bench_start(void) { xTaskCreatePinnedToCore(bench_task, "bench", 6144, NULL, 5, NULL, 1); }
