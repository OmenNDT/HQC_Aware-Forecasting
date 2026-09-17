/* adxl345_spi.h — ADXL345 (GY-291) qua SPI 4 dây, mode 3, 2 MHz, full-res ±4 g, ODR 1600 Hz. */
#pragma once
#include <stdint.h>
int  adxl345_init(void);                       /* 0 = ok, -1 = không thấy chip (DEVID != 0xE5) */
int  adxl345_read_xyz(int16_t *x, int16_t *y, int16_t *z);   /* LSB, full-res: 3,9 mg/LSB */
float adxl345_lsb_to_mg(int16_t v);
int  adxl345_probe(void);                      /* dò lại chip khi đang chạy; 0 = thấy và đã cấu hình */
uint8_t adxl345_devid(void);                   /* DEVID đọc lúc init, 0xE5 = đúng chip */
