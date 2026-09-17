/* main.c — ESP32-S3: nhận luồng phát lại qua UART0 (USB-UART, 115200 8N1), chạy ba tầng (../core), trả JSON từng ngày/tuần,
 * đo micro giây mỗi lần suy luận SAE và RAM. Cùng định dạng dòng với host_sim/replay_main.c:
 *   S,<epoch>,amp×8,sin×8,cos×8 | D,<epoch>,Direct×8 | R,<epoch> | E (kết thúc) | P (ping: thống kê)
 * LED RGB (WS2812, GPIO48 hoặc 38 tùy bản bo) hiển thị màu tầng nặng nhất: đỏ = báo, hổ phách = cờ, xanh = bình thường, tắt = máy dừng. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/uart.h"
#ifdef HQC_IO_USB                      /* -DHQC_IO_USB=1 từ CMake: dữ liệu qua cổng USB gốc (USB-Serial-JTAG); log ESP-IDF vẫn ra UART0 */
#include "driver/usb_serial_jtag.h"
#endif
#include "esp_timer.h"
#include "esp_heap_caps.h"
#include "esp_system.h"
#include "hqc_engine.h"
#include "sae_int8.h"
#include "led_status.h"
#ifdef HQC_BENCH
#include "bench_main.h"
#endif

#define UART_NUM UART_NUM_0
#define RX_BUF 4096
#define LINE_MAX 1024

static hqc_t g_h; static int64_t g_infer_us_total = 0, g_infer_us_max = 0; static uint32_t g_n_infer = 0;
static int g_state_A = 0, g_state_B = 0, g_state_C = 0;   /* 0 tắt, 1 xanh, 2 hổ phách, 3 đỏ */

/* lớp I/O: cùng giao diện cho UART0 (cổng USB-UART) và USB-Serial-JTAG (cổng USB gốc) */
static void io_write(const char *buf, size_t n) {
#ifdef HQC_IO_USB
    usb_serial_jtag_write_bytes(buf, n, pdMS_TO_TICKS(1000));
#else
    uart_write_bytes(UART_NUM, buf, n);
#endif
}
static int io_read_byte(uint8_t *ch) {
#ifdef HQC_IO_USB
    return usb_serial_jtag_read_bytes(ch, 1, pdMS_TO_TICKS(100));
#else
    return uart_read_bytes(UART_NUM, ch, 1, pdMS_TO_TICKS(100));
#endif
}
static void emit(const char *line, void *u) {
    (void)u; io_write(line, strlen(line)); io_write("\n", 1);
    /* cập nhật đèn từ dòng JSON vừa phát (đơn giản: tìm khóa) */
    if (strstr(line, "\"t\":\"B\"")) g_state_B = strstr(line, "\"B14\":1") || strstr(line, "\"B45\":1") ? 3 : 1;
    if (strstr(line, "\"t\":\"A\"")) g_state_A = strstr(line, "\"A\":1") ? 3 : (strstr(line, "\"flag\":1") ? 2 : 1);
    if (strstr(line, "\"t\":\"C\"")) g_state_C = strstr(line, "\"C\":1") ? 3 : (strstr(line, "\"flag\":1") ? 2 : 1);
    int worst = g_state_A > g_state_B ? g_state_A : g_state_B; if (g_state_C > worst) worst = g_state_C; led_status_set(worst);
#ifdef HQC_BENCH
    bench_replay_tier(worst);   /* LED xanh/vàng/đỏ + còi trên breadboard đi theo tầng nặng nhất của luồng phát lại */
#endif
}

static int parse_floats(char *p, float *out, int n) {                    /* M1: mọi trường phải là số hợp lệ hoặc "nan"; đúng đủ n trường */
    for (int i = 0; i < n; i++) { char *tok = strsep(&p, ","); if (!tok || !*tok) return 0; if (strcmp(tok, "nan") == 0) { out[i] = NAN; continue; } char *e; out[i] = strtof(tok, &e); if (*e) return 0; }
    return p == NULL || *p == 0;
}
static int parse_ts(char *tok, int64_t *ts) { if (!tok || !*tok) return 0; char *e; *ts = strtoll(tok, &e, 10); return *e == 0 && *ts > 0; }

static void stats_line(char *buf, size_t n) {
    snprintf(buf, n, "{\"t\":\"STAT\",\"inferences\":%lu,\"infer_us_mean\":%.2f,\"infer_us_max\":%lld,\"heap_free\":%u,\"heap_min_free\":%u,\"engine_bytes\":%u,\"weights_bytes\":%u}",
             (unsigned long)g_n_infer, g_n_infer ? (double)g_infer_us_total / g_n_infer : 0.0, (long long)g_infer_us_max,
             (unsigned)heap_caps_get_free_size(MALLOC_CAP_8BIT), (unsigned)heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT), (unsigned)sizeof(hqc_t), sae_weights_bytes());
}

static void handle_line(char *p) {
    size_t L = strlen(p); while (L && (p[L - 1] == '\n' || p[L - 1] == '\r')) p[--L] = 0;
    if (!L) return;
    char out[256];
    if (p[0] == 'E') { hqc_flush(&g_h); stats_line(out, sizeof out); emit(out, NULL); io_write("{\"t\":\"END\"}\n", 12); return; }
    if (p[0] == 'P') { stats_line(out, sizeof out); emit(out, NULL); return; }
    if (p[0] == 'X') {   /* xoá trạng thái ba tầng để phát lại từ một mốc khác mà không cần bấm RST */
        hqc_init(&g_h, emit, NULL); g_infer_us_total = g_infer_us_max = 0; g_n_infer = 0; g_state_A = g_state_B = g_state_C = 0; led_status_set(0);
#ifdef HQC_BENCH
        bench_replay_tier(0);
#endif
        io_write("{\"t\":\"RESET\"}\n", 14); return; }
    char *kind = strsep(&p, ","); if (!kind || !p) return; int64_t ts; if (!parse_ts(strsep(&p, ","), &ts)) return;
    if (kind[0] == 'S') { float v[24]; if (parse_floats(p, v, 24)) { int64_t t0 = esp_timer_get_time(); hqc_sample_10min(&g_h, ts, v, v + 8, v + 16); int64_t dt = esp_timer_get_time() - t0; g_infer_us_total += dt; if (dt > g_infer_us_max) g_infer_us_max = dt; g_n_infer++; } }
    else if (kind[0] == 'D') { float v[8]; if (parse_floats(p, v, 8)) hqc_direct_hour(&g_h, ts, v); }
    else if (kind[0] == 'R') hqc_restart(&g_h, ts);
}

void app_main(void) {
#ifdef HQC_IO_USB
    usb_serial_jtag_driver_config_t ucfg = { .tx_buffer_size = RX_BUF, .rx_buffer_size = RX_BUF };
    usb_serial_jtag_driver_install(&ucfg);
#else
    uart_config_t cfg = { .baud_rate = 115200, .data_bits = UART_DATA_8_BITS, .parity = UART_PARITY_DISABLE, .stop_bits = UART_STOP_BITS_1, .flow_ctrl = UART_HW_FLOWCTRL_DISABLE, .source_clk = UART_SCLK_DEFAULT };
    uart_driver_install(UART_NUM, RX_BUF, RX_BUF, 0, NULL, 0); uart_param_config(UART_NUM, &cfg);
#endif
    led_status_init(); hqc_init(&g_h, emit, NULL);
#ifdef HQC_BENCH
    bench_start();
#endif
    char line[LINE_MAX]; int n = 0; uint8_t ch; char hello[200];
    snprintf(hello, sizeof hello, "{\"t\":\"HELLO\",\"fw\":\"hqc-three-tier\",\"chip\":\"esp32s3\",\"engine_bytes\":%u,\"weights_bytes\":%u}\n", (unsigned)sizeof(hqc_t), sae_weights_bytes());
    io_write(hello, strlen(hello));
    for (;;) {
        int got = io_read_byte(&ch);
        if (got <= 0) continue;
        if (ch == '\n' || n >= LINE_MAX - 1) { line[n] = 0;
#ifdef HQC_BENCH
            bench_note_replay_activity();
#endif
            handle_line(line); n = 0; } else line[n++] = (char)ch;
    }
}
