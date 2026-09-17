#!/usr/bin/env bash
# 23_record_demo_screen.sh — quay màn hình thật (X11 :0, 1920x1080, 30 fps) cho demo phase 03.
#   start [tên]  → chạy ffmpeg nền, ghi PID vào Bao_cao/demo/.rec.pid, log Bao_cao/demo/.rec.log
#   stop         → gửi SIGINT (đóng file MP4 sạch), in thời lượng bằng ffprobe
#   frames       → trích 6 khung tại các mốc (giây) cho báo cáo: Bao_cao/demo/khung/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; OUT="$ROOT/Bao_cao/demo"; mkdir -p "$OUT/khung"
case "${1:-}" in
  start)
    NAME="${2:-demo-ba-tang}"; export DISPLAY=:0
    nohup ffmpeg -y -f x11grab -framerate 30 -video_size 1920x1080 -probesize 50M -draw_mouse 0 -i :0.0 \
      -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -movflags +faststart "$OUT/$NAME.mp4" >"$OUT/.rec.log" 2>&1 &
    echo $! >"$OUT/.rec.pid"; sleep 2; kill -0 "$(cat "$OUT/.rec.pid")" && echo "đang quay → $OUT/$NAME.mp4 (PID $(cat "$OUT/.rec.pid"))" ;;
  stop)
    PID=$(cat "$OUT/.rec.pid"); kill -INT "$PID"; for i in $(seq 1 20); do kill -0 "$PID" 2>/dev/null || break; sleep 0.5; done
    F=$(ls -t "$OUT"/*.mp4 | head -1); echo "đã dừng: $F · thời lượng $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$F") s" ;;
  frames)
    F="${2:-$OUT/demo-ba-tang.mp4}"; shift 2 || true
    for T in "$@"; do ffmpeg -y -v error -ss "$T" -i "$F" -frames:v 1 "$OUT/khung/khung-${T}s.png"; done; ls "$OUT/khung" ;;
  *) echo "dùng: $0 start [tên] | stop | frames [file.mp4] giây..." ;;
esac
