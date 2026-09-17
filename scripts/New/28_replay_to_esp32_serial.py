#!/usr/bin/env python3
"""28_replay_to_esp32_serial.py — Phase 04 ngày 4: gửi luồng phát lại xuống ESP32-S3 qua USB-UART, gom JSON trả về, rồi đối chiếu.

Dùng: python3 28_replay_to_esp32_serial.py --port /dev/ttyUSB0 [--baud 115200] [--limit N]
Ra: Dataclean_new/embed/esp32_replay_log.jsonl (mọi dòng chip trả), embed_measurements.json (STAT: latency, heap, kích thước).
Sau đó: python3 27_replay_feature_store_to_uart.py --from-device Dataclean_new/embed/esp32_replay_log.jsonl
Điều khiển luồng: gửi từng dòng, cứ --chunk dòng (mặc định 8, ≈ 2,5 KB) chờ chip trả lời lệnh P (ping) để không tràn đệm RX 4 KB.
"""
import argparse, json, os, sys, time
import serial

try:                                                                       # chạy trong repo: đường dẫn từ cấu hình
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from phase01_config import DATA_NEW                                   # noqa: E402
    EMBED = f"{DATA_NEW}/embed"
except Exception:                                                          # chạy độc lập trên máy có bo (Windows/WSL): thư mục hiện hành
    EMBED = os.getcwd()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--port", required=True); ap.add_argument("--baud", type=int, default=115200); ap.add_argument("--limit", type=int, default=0); ap.add_argument("--chunk", type=int, default=8, help="số dòng gửi trước mỗi lần chờ STAT (đệm RX trên chip 4 KB)"); ap.add_argument("--dir", default=None, help="thư mục chứa replay_stream.txt và nơi ghi log (mặc định EMBED)"); a = ap.parse_args()
    global EMBED
    if a.dir: EMBED = a.dir
    lines = [l for l in open(f"{EMBED}/replay_stream.txt").read().splitlines() if l.strip()]
    if a.limit: lines = lines[:a.limit] + ["E"]
    ser = serial.Serial(); ser.port, ser.baudrate, ser.timeout = a.port, a.baud, 2
    ser.dtr = False; ser.rts = False; ser.open()                                # USB-Serial-JTAG: DTR/RTS điều khiển reset/BOOT → giữ tắt để chip không bị reset khi mở cổng
    time.sleep(1.5); raw0 = ser.read(ser.in_waiting or 1); print("bo đang phát:", raw0[:200]); ser.reset_input_buffer()
    out = open(f"{EMBED}/esp32_replay_log.jsonl", "w"); got = []; t0 = time.time()

    def drain(block_until=None, max_wait=30.0):
        t_start = time.time()
        while True:
            raw = ser.readline()
            if not raw:
                if block_until and time.time() - t_start < max_wait: continue
                if block_until: sys.exit(f"KHÔNG nhận được '{block_until}' sau {max_wait:.0f} s: bo chưa chạy firmware (còn ở chế độ nạp?) hoặc sai cổng")
                return
            s = raw.decode("utf-8", "replace").strip()
            if not s.startswith("{"): continue
            out.write(s + "\n"); j = json.loads(s); got.append(j)
            if block_until and j.get("t") == block_until: return
            if not block_until and ser.in_waiting == 0: return

    ser.write(b"P\n"); drain(block_until="STAT", max_wait=10)                      # bắt tay: chip phải trả STAT trong 10 s
    print("bo trả lời:", got[-1] if got else None)

    for i, l in enumerate(lines):
        ser.write((l + "\n").encode())
        if i % a.chunk == a.chunk - 1: ser.write(b"P\n"); drain(block_until="STAT")
        elif ser.in_waiting: drain()
        if i % 5000 == 0: print(f"  {i}/{len(lines)} dòng, {time.time() - t0:.0f} s, {len(got)} JSON")
    drain(block_until="END"); out.close(); ser.close()
    stats = [j for j in got if j.get("t") == "STAT"]; hello = [j for j in got if j.get("t") == "HELLO"]
    meas = {"port": a.port, "baud": a.baud, "lines_sent": len(lines), "json_received": len(got), "seconds": round(time.time() - t0, 1), "hello": hello[-1] if hello else None,
            "final_stat": stats[-1] if stats else None, "infer_us_mean_series": [s["infer_us_mean"] for s in stats[-5:]]}
    json.dump(meas, open(f"{EMBED}/embed_measurements.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(meas, ensure_ascii=False, indent=1)); print(f"→ {EMBED}/esp32_replay_log.jsonl; tiếp: 27_replay_feature_store_to_uart.py --from-device …")


if __name__ == "__main__":
    main()
