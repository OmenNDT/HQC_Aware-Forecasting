#!/usr/bin/env python3
"""33_serial_ws_bridge.py — Cầu nối WebSocket ↔ cổng nối tiếp cho trang demo-esp32-live.html khi trình duyệt không có/không dùng được Web Serial.

Dùng: python3 33_serial_ws_bridge.py --port /dev/ttyACM0   (Windows: --port COM4)   [--ws-port 18795]
Mỗi khung văn bản WebSocket = một dòng gửi xuống bo; mỗi dòng bo trả về = một khung gửi lên trang. Mở cổng với DTR/RTS BẬT
(mặc định của hệ điều hành): với USB-Serial-JTAG của ESP32-S3, đổi trạng thái DTR/RTS mới làm chip reset, giữ nguyên thì không.
Chỉ lắng nghe 127.0.0.1. Cổng 18795 đã đăng ký trong start-servers.sh (chạy theo yêu cầu, không tự khởi động).
"""
import argparse, asyncio, sys
import serial
import websockets


async def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--port", required=True); ap.add_argument("--baud", type=int, default=115200); ap.add_argument("--ws-port", type=int, default=18795); a = ap.parse_args()
    ser = serial.Serial(a.port, a.baud, timeout=0.05); print(f"serial {a.port} mở; WebSocket ws://127.0.0.1:{a.ws_port}", flush=True)
    clients = set()

    async def serial_reader():
        buf = b""
        while True:
            chunk = await asyncio.to_thread(ser.read, 4096)
            if chunk:
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1); text = line.decode("utf-8", "replace").strip()
                    if text and clients: await asyncio.gather(*(c.send(text) for c in list(clients)), return_exceptions=True)
            else:
                await asyncio.sleep(0.005)

    async def handler(ws):
        clients.add(ws); print("trang kết nối", flush=True)
        try:
            async for msg in ws:
                if isinstance(msg, str): ser.write((msg.rstrip("\n") + "\n").encode())
        finally:
            clients.discard(ws); print("trang rời", flush=True)

    asyncio.create_task(serial_reader())
    async with websockets.serve(handler, "127.0.0.1", a.ws_port, max_size=1 << 20):
        await asyncio.Future()


if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: sys.exit(0)
