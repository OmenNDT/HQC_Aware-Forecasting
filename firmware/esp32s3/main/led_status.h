/* led_status.h — đèn RGB WS2812 trên bo DevKitC-1 (GPIO 48 bản v1.0, GPIO 38 bản v1.1; đổi HQC_LED_GPIO nếu không sáng). */
#pragma once
void led_status_init(void);
void led_status_set(int state);   /* 0 tắt, 1 xanh trầm, 2 hổ phách, 3 đỏ */
