/* bench_pins.h — chân ESP32-S3-DevKitC-1 N16R8 cho bàn thử quạt (phase 05).
 * BỐ TRÍ MỘT HÀNG CHÂN (16/09/2026): board cắm hàng chân 3V3 vào hàng a của breadboard, thân treo ngoài mép; hàng chân kia không dùng.
 * Thứ tự hàng 3V3 từ đầu anten: 3V3 3V3 RST 4 5 6 7 15 16 17 18 8 3 46 9 10 11 12 13 14 5V GND → cột 4..25 khi chân đầu ở a4.
 * Không dùng 35-37 (PSRAM), 19/20 (USB), 0/3/45/46 (strapping), 43/44 (UART). Chân = -1 nghĩa là chức năng tắt. */
#pragma once
#define PIN_TACHO         4   /* dây vàng quạt, pull-up nội, ngắt cạnh xuống, 2 xung/vòng      → lỗ d7 */
#define PIN_LED_GREEN     5   /* tầng A, qua 330 Ω                                             → lỗ d8 */
#define PIN_LED_YELLOW    6   /* tầng B                                                        → lỗ d9 */
#define PIN_LED_RED       7   /* tầng C                                                        → lỗ d10 */
#define PIN_BUZZER       15   /* còi active, HIGH kêu                                          → lỗ d11 */
#define PIN_BTN_HEALTHY  16   /* nút xanh: nền khỏe (hệ số 1,0)                                → lỗ d12 */
#define PIN_BTN_APRIL    17   /* nút vàng: tháng 4 (1,8)                                       → lỗ d13 */
#define PIN_BTN_MAY      18   /* nút trắng: tháng 5 (3,5)                                      → lỗ d14 */
#define PIN_I2C_SDA       8   /* OLED 0x3C                                                     → lỗ d15 */
#define PIN_I2C_SCL       9   /*                                                               → lỗ d18 */
#define PIN_SPI_CS       10   /* ADXL345                                                       → lỗ d19 */
#define PIN_SPI_MOSI     11   /*                                                               → lỗ d20 */
#define PIN_SPI_SCK      12   /*                                                               → lỗ d21 */
#define PIN_SPI_MISO     13   /*                                                               → lỗ d22 */
#define PIN_FAN_PWM      14   /* dây xanh quạt, tuỳ chọn                                       → lỗ d23 */
#define PIN_ENC_CLK      -1   /* KY-040 tắt trong bố trí một hàng chân */
#define PIN_ENC_DT       -1
#define PIN_ENC_SW       -1
#define PIN_POT_SPEED    -1   /* biến trở tắt; quạt chạy toàn tốc */
#define PIN_SERVO        -1   /* servo tắt */
#define PIN_BTN_BOOT      0   /* nút BOOT trên board: chụp nền khỏe */
#define TACHO_PULSES_PER_REV 2
