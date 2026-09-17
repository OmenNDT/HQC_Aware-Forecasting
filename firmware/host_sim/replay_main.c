/* replay_main.c — mô phỏng trên máy tính: đọc luồng văn bản (cùng định dạng khung UART) từ stdin, in JSON ra stdout.
 *   S,<epoch>,amp0..7,sin0..7,cos0..7   mẫu 1X 10 phút
 *   D,<epoch>,v0..7                     Direct theo giờ (nan cho phép)
 *   R,<epoch>                           máy chạy lại sau dừng thật
 *   E                                   hết luồng → đóng ngày/tuần đang gom
 * Cùng mã core sẽ chạy trên ESP32-S3 (main.c chỉ thay stdin bằng UART). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "../core/hqc_engine.h"

static void emit(const char *line, void *u) { (void)u; puts(line); }

static int parse_floats(char *p, float *out, int n) {                    /* M1: mọi trường phải là số hợp lệ hoặc "nan"; đúng đủ n trường */
    for (int i = 0; i < n; i++) { char *tok = strsep(&p, ","); if (!tok || !*tok) return 0; if (strcmp(tok, "nan") == 0) { out[i] = NAN; continue; } char *e; out[i] = strtof(tok, &e); if (*e) return 0; }
    return p == NULL || *p == 0;
}
static int parse_ts(char *tok, int64_t *ts) { if (!tok || !*tok) return 0; char *e; *ts = strtoll(tok, &e, 10); return *e == 0 && *ts > 0; }

int main(void) {
    static hqc_t h; hqc_init(&h, emit, NULL); char line[1024]; long ns = 0, nd = 0;
    while (fgets(line, sizeof line, stdin)) {
        char *p = line; size_t L = strlen(p); while (L && (p[L - 1] == '\n' || p[L - 1] == '\r')) p[--L] = 0;
        if (p[0] == 'E') break;
        char *kind = strsep(&p, ","); if (!kind || !p) continue; int64_t ts; if (!parse_ts(strsep(&p, ","), &ts)) continue;
        if (kind[0] == 'S') { float v[24]; if (parse_floats(p, v, 24)) { hqc_sample_10min(&h, ts, v, v + 8, v + 16); ns++; } }
        else if (kind[0] == 'D') { float v[8]; if (parse_floats(p, v, 8)) { hqc_direct_hour(&h, ts, v); nd++; } }
        else if (kind[0] == 'R') hqc_restart(&h, ts);
    }
    hqc_flush(&h);
    printf("{\"t\":\"END\",\"samples\":%ld,\"direct_hours\":%ld,\"inferences\":%u}\n", ns, nd, h.n_infer);
    return 0;
}
