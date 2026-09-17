/* bench_main.h — chế độ bàn thử phase 05, chạy song song với phát lại. */
#pragma once
void bench_start(void);                 /* tạo task lấy mẫu ADXL345 + task điều khiển 1 s */
void bench_note_replay_activity(void);  /* main.c gọi mỗi khi nhận một dòng phát lại: bench im lặng 5 s */
void bench_replay_tier(int worst);      /* main.c gọi khi tầng của luồng phát lại đổi: 0 tắt, 1 xanh, 2 vàng, 3 đỏ + còi */
