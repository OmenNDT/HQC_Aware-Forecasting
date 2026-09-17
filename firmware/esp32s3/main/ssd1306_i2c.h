/* ssd1306_i2c.h — OLED 0,96" 128×64 I2C 0x3C, framebuffer 1 KB, chữ 5×7 có phóng to. */
#pragma once
#include <stdint.h>
int  oled_init(void);                                        /* 0 = ok */
void oled_clear(void);
void oled_text(int x, int y, const char *s, int scale);      /* x,y pixel; scale 1 = 6×8 px mỗi ký tự, 2 = 12×16 */
void oled_hline(int x0, int x1, int y);
void oled_bar(int x, int y, int w, int h, int fill_w);       /* thanh ngang: khung + phần đầy */
void oled_flush(void);
const char *oled_i2c_found(void);                            /* danh sách địa chỉ I2C có ACK lúc init, để chẩn đoán dây */
