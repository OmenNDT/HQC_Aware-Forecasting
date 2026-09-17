#ifdef HQC_NO_LED
/* bản giả lập QEMU: RMT chưa được mô phỏng → bỏ đèn */
#include "led_status.h"
void led_status_init(void) {}
void led_status_set(int state) { (void)state; }
#else
#include "led_status.h"
#include "led_strip.h"
#ifndef HQC_LED_GPIO
#define HQC_LED_GPIO 48
#endif
static led_strip_handle_t s_strip;
void led_status_init(void) {
    led_strip_config_t sc = { .strip_gpio_num = HQC_LED_GPIO, .max_leds = 1, .led_model = LED_MODEL_WS2812, .color_component_format = LED_STRIP_COLOR_COMPONENT_FMT_GRB, .flags.invert_out = false };
    led_strip_rmt_config_t rc = { .clk_src = RMT_CLK_SRC_DEFAULT, .resolution_hz = 10 * 1000 * 1000, .flags.with_dma = false };
    if (led_strip_new_rmt_device(&sc, &rc, &s_strip) == ESP_OK) led_strip_clear(s_strip);
}
void led_status_set(int state) {
    if (!s_strip) return;
    static const unsigned char rgb[4][3] = { {0, 0, 0}, {0, 24, 12}, {40, 24, 0}, {48, 4, 2} };
    led_strip_set_pixel(s_strip, 0, rgb[state & 3][0], rgb[state & 3][1], rgb[state & 3][2]); led_strip_refresh(s_strip);
}
#endif
