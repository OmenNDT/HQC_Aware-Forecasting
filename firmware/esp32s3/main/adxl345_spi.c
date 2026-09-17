/* adxl345_spi.c — driver tối thiểu cho ADXL345 trên SPI2 (FSPI) của ESP32-S3.
 * Thanh ghi: DEVID 0x00 (=0xE5), BW_RATE 0x2C, POWER_CTL 0x2D, DATA_FORMAT 0x31, DATAX0 0x32.
 * Đọc: bit7 = 1 (read), bit6 = 1 (multi-byte). */
#include "adxl345_spi.h"
#include "bench_pins.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "esp_log.h"

static const char *TAG = "adxl";
static spi_device_handle_t s_dev; static uint8_t s_devid = 0;
uint8_t adxl345_devid(void) { return s_devid; }

static int reg_write(uint8_t reg, uint8_t val) {
    uint8_t tx[2] = { (uint8_t)(reg & 0x3F), val };
    spi_transaction_t t = { .length = 16, .tx_buffer = tx };
    return spi_device_polling_transmit(s_dev, &t) == ESP_OK ? 0 : -1;
}
static int reg_read(uint8_t reg, uint8_t *buf, int n) {
    uint8_t tx[8] = { (uint8_t)(0x80 | (n > 1 ? 0x40 : 0) | (reg & 0x3F)) };
    uint8_t rx[8] = { 0 };
    spi_transaction_t t = { .length = 8 * (1 + n), .tx_buffer = tx, .rx_buffer = rx };
    if (spi_device_polling_transmit(s_dev, &t) != ESP_OK) return -1;
    for (int i = 0; i < n; i++) buf[i] = rx[1 + i];
    return 0;
}

static int s_bus_ready = 0;
/* dò lại chip: đọc DEVID, đúng 0xE5 thì cấu hình và trả 0; gọi lại mỗi giây khi chưa thấy chip (cắm dây lúc đang chạy) */
int adxl345_probe(void) {
    if (!s_bus_ready) return -1;
    uint8_t id = 0; reg_read(0x00, &id, 1); s_devid = id;
    if (id != 0xE5) return -1;
    reg_write(0x31, 0x09); reg_write(0x2C, 0x0E); reg_write(0x2D, 0x08);   /* DATA_FORMAT 0x09 = FULL_RES | ±4 g, SPI 4 dây */
    ESP_LOGI(TAG, "ADXL345 ok, full-res ±4 g, 1600 Hz");
    return 0;
}
int adxl345_init(void) {
    spi_bus_config_t bus = { .mosi_io_num = PIN_SPI_MOSI, .miso_io_num = PIN_SPI_MISO, .sclk_io_num = PIN_SPI_SCK,
                             .quadwp_io_num = -1, .quadhd_io_num = -1, .max_transfer_sz = 16 };
    if (spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_DISABLED) != ESP_OK) return -1;
    spi_device_interface_config_t dev = { .clock_speed_hz = 2 * 1000 * 1000, .mode = 3, .spics_io_num = PIN_SPI_CS, .queue_size = 2 };
    if (spi_bus_add_device(SPI2_HOST, &dev, &s_dev) != ESP_OK) return -1;
    s_bus_ready = 1;
    if (adxl345_probe()) { ESP_LOGE(TAG, "DEVID=0x%02X (mong 0xE5): kiểm tra dây CS/SDO/SDA/SCL, VCC 3V3", s_devid); return -1; }
    return 0;
}

int adxl345_read_xyz(int16_t *x, int16_t *y, int16_t *z) {
    uint8_t b[6];
    if (reg_read(0x32, b, 6)) return -1;
    *x = (int16_t)((b[1] << 8) | b[0]); *y = (int16_t)((b[3] << 8) | b[2]); *z = (int16_t)((b[5] << 8) | b[4]);
    return 0;
}

float adxl345_lsb_to_mg(int16_t v) { return v * 3.9f; }
