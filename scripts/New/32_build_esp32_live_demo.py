#!/usr/bin/env python3
"""32_build_esp32_live_demo.py — Dựng Bao_cao/demo/demo-esp32-live.html: trang Web Serial nói chuyện với bo ESP32-S3 thật.
Nhúng CSS + module vẽ của demo phát lại và phần kỳ vọng (ngày báo Python, tham số) rút từ demo_data.json."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import ROOT                                              # noqa: E402
DEMO, TPL = f"{ROOT}/Bao_cao/demo", f"{os.path.dirname(os.path.abspath(__file__))}/demo"
D = json.load(open(f"{DEMO}/demo_data.json"))
exp = {k: D[k] for k in ["days", "role", "channels", "alarms", "stops", "events", "params"]}
html = open(f"{TPL}/demo-esp32-live-template.html").read()
for tag, fn in [("/*__CSS__*/", "demo-ba-tang-style.css"), ("/*__CHARTS__*/", "demo-charts-canvas.js"), ("/*__APP__*/", "demo-esp32-live-app.js")]:
    html = html.replace(tag, open(f"{TPL}/{fn}").read())
html = html.replace("/*__DATA__*/", "window.EXP = " + json.dumps(exp, ensure_ascii=False, separators=(",", ":")) + ";")
open(f"{DEMO}/demo-esp32-live.html", "w").write(html); print(f"saved {DEMO}/demo-esp32-live.html ({len(html)//1024} KB)")
