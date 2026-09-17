/* demo-esp32-live-app.js — trang trình diễn với bo thật: Web Serial (Chrome) gửi luồng phát lại xuống ESP32-S3, vẽ kết quả bo trả về
 * và đối chiếu với ngày báo kỳ vọng của Python (window.EXP, sinh từ demo_data.json). */
(() => {
  const E = window.EXP, $ = (id) => document.getElementById(id), fmt = (d) => d ? d.slice(8, 10) + "/" + d.slice(5, 7) + "/" + d.slice(0, 4) : "—";
  const EXP = { B14: new Set(E.alarms.B14), B45: new Set(E.alarms.B45), A: new Set(E.alarms.A), C: new Set(E.alarms.C) };
  const idx = Object.fromEntries(E.days.map((d, i) => [d, i])); const N = E.days.length;
  const spe = new Array(N).fill(null), us = new Array(N).fill(null), heap = new Array(N).fill(null);
  const got = { B14: new Set(), B45: new Set(), A: new Set(), C: new Set() }; let seenB = 0, seenA = 0, seenC = 0;
  const chS = new DayChart({ el: "cSpe", days: E.days, idx, series: [{ key: "spe", vals: spe, color: "#f2d7a3", width: 2 }], ylog: true, ymin: -2, ymax: 3, yticks: [0.01, 0.1, 1, 10, 100, 1000],
    hlines: [{ y: E.params.limit99_6h, label: "giới hạn kiểm soát 99% (" + E.params.limit99_6h + ")", color: tok("--blue") }],
    bands: [{ color: tok("--red"), set: [] }, { color: tok("--amber"), set: [] }, { color: "rgba(214,215,222,.35)", set: E.alarms.B14 }, { color: "rgba(214,215,222,.35)", set: E.alarms.B45 }], stops: E.stops });
  const chL = new DayChart({ el: "cLat", days: E.days, idx, series: [{ key: "us", vals: us, color: "#7fb3d5", width: 1.8 }, { key: "heap", vals: heap, color: "#9fcf9a", width: 1.4 }], ymin: 0, ymax: 800, yticks: [0, 200, 400, 600, 800], stops: E.stops });
  $("legSpe").innerHTML = `<span><i style="background:${tok("--red")}"></i>bo báo B₁₄</span><span><i style="background:${tok("--amber")}"></i>bo báo B₄₅</span><span><i style="background:rgba(214,215,222,.5)"></i>Python báo (kỳ vọng)</span>`;
  $("legLat").innerHTML = `<span><i style="background:#7fb3d5"></i>µs / mẫu (TB tích lũy)</span><span><i style="background:#9fcf9a"></i>heap còn trống, KB (thang 0–800)</span>`;
  $("model").innerHTML = `<table><tr><td>Mô hình</td><td>${E.params.model} · lớp 0–1 int16, lớp 2–5 int8</td></tr><tr><td>Ngưỡng khóa</td><td>τ₁₄ ${E.params.tau14} · τ₄₅ ${E.params.tau45} · 65 µm · chân trời 30 ngày</td></tr><tr><td>Kỳ vọng (Python)</td><td>B₁₄ ${fmt(E.events.dung2.B14_SAE.first_alarm)} · B₄₅ ${fmt(E.events.dung2.B45_SAE.first_alarm)} · A ${fmt(E.events.dung2.A_direct_65um.first_alarm)}</td></tr></table>`;
  const light = (id, cls, state, detail) => { const el = $(id); el.className = "light " + cls; el.querySelector(".lstate").textContent = state; el.querySelector(".ldetail").textContent = detail; };
  let cA = 1, cB = 1, cC = 1; const worst = () => Math.max(cA, cB, cC);
  const log = (s, cls = "") => { const el = $("log"); const line = document.createElement("div"); line.textContent = s; if (cls) line.className = cls; el.appendChild(line); while (el.childElementCount > 400) el.removeChild(el.firstChild); el.scrollTop = el.scrollHeight; };
  function cmp() {
    const same = (k) => { const a = [...got[k]].filter(d => d <= lastDay), b = [...EXP[k]].filter(d => d <= lastDay); return a.length === b.length && a.every(d => EXP[k].has(d)); };
    const row = (k, name) => { const a = [...got[k]].filter(d => d <= lastDay).length, b = [...EXP[k]].filter(d => d <= lastDay).length; return `<div>${name}: bo ${a} ngày báo · Python ${b} · <b style="color:${same(k) ? "#8fd3b0" : "#f0a08e"}">${same(k) ? "trùng" : "LỆCH"}</b></div>`; };
    $("cmp").innerHTML = row("B14", "B₁₄") + row("B45", "B₄₅") + row("A", "Tầng A") + row("C", "Tầng C (tuần)") + `<div style="color:var(--dim);margin-top:6px">tính tới ngày ${fmt(lastDay)}</div>`;
  }
  let lastDay = "";
  function onJson(j) {
    if (j.t === "B") { const i = idx[j.day]; if (i != null) { spe[i] = j.spe_med; } lastDay = j.day; $("day").textContent = fmt(j.day); $("role").textContent = E.role[i] || "";
      if (j.B14) got.B14.add(j.day); if (j.B45) got.B45.add(j.day); chS.bands[0].set = [...got.B14]; chS.bands[1].set = [...got.B45]; seenB++;
      cB = (j.B14 || j.B45) ? 3 : (j.slope14 == null ? 0 : 1); light("lB14", j.slope14 == null ? "gray" : j.B14 ? "red" : "green", j.slope14 == null ? "chưa đủ 14 ngày" : j.B14 ? "BÁO" : "bình thường", j.slope14 == null ? "" : `dốc ${j.slope14.toFixed(3)} / τ ${E.params.tau14}`);
      light("lB45", j.slope45 == null ? "gray" : j.B45 ? "red" : "green", j.slope45 == null ? "chưa đủ 45 ngày" : j.B45 ? "BÁO" : "bình thường", j.slope45 == null ? "" : `dốc ${j.slope45.toFixed(3)} / τ ${E.params.tau45}`);
      chS.draw(i ?? 0); cmp(); }
    else if (j.t === "A") { if (j.A) got.A.add(j.day); seenA++; cA = j.A ? 3 : (j.flag ? 2 : (j.row ? 1 : 0));
      light("lA", j.row ? (j.A ? "red" : j.flag ? "amber" : "green") : "gray", j.row ? (j.A ? "BÁO" : j.flag ? "dấu hiệu" : "bình thường") : "chưa đủ 8 hàng", j.ch >= 0 ? `${E.channels[j.ch]} · ${Math.round(j.dl_low)} ngày tới 65` : (j.level_2001X != null ? `2001X mức ${j.level_2001X.toFixed(1)} µm` : "")); }
    else if (j.t === "C") { if (j.C) got.C.add(j.week_end); seenC++; cC = j.C ? 3 : (j.flag ? 2 : 1);
      light("lC", j.C ? "red" : j.flag ? "amber" : "green", j.C ? "CẦN XEM" : j.flag ? "dấu hiệu tuần 1" : "bình thường", `tuần tới ${fmt(j.week_end)} · quay ${j.rate ?? "—"}°/tuần${j.post_restart ? " · sau khởi động" : ""}`); }
    else if (j.t === "STAT") { $("sInf").textContent = j.inferences.toLocaleString("vi"); $("sUs").textContent = j.infer_us_mean.toFixed(0); $("sMax").textContent = j.infer_us_max.toLocaleString("vi"); $("sHeap").textContent = (j.heap_free / 1024).toFixed(0); $("sEng").textContent = j.engine_bytes;
      const i = idx[lastDay]; if (i != null) { us[i] = j.infer_us_mean; heap[i] = j.heap_free / 1024; chL.draw(i); } }
    else if (j.t === "HELLO") log("bo chào: " + JSON.stringify(j), "ok");
  }
  /* ---- Web Serial ---- */
  let port = null, reader = null, writer = null, lines = null, running = false, buf = "";
  const pending = []; // resolver chờ STAT
  let lost = false;
  async function readLoop() {
    const dec = new TextDecoder(); lost = false;
    while (port && port.readable) {
      reader = port.readable.getReader();
      try { for (;;) { const { value, done } = await reader.read(); if (done) break; buf += dec.decode(value); let k;
        while ((k = buf.indexOf("\n")) >= 0) { const s = buf.slice(0, k).trim(); buf = buf.slice(k + 1); onLine(s); } } }
      catch (e) { log("đọc cổng: " + e.message, "warn"); lost = true; try { reader.releaseLock(); } catch {} break; }
      finally { try { reader.releaseLock(); } catch {} }
    }
  }
  /* Mở cổng: khi mở, USB-Serial-JTAG làm chip reset và USB rớt ~2 s → chờ rồi mở lại đúng cổng đã được cấp quyền. */
  async function openPort(p) {
    await p.open({ baudRate: 115200 });                        /* KHÔNG đụng DTR/RTS sau khi mở: đổi trạng thái DTR làm USB-Serial-JTAG reset chip */
    writer = p.writable.getWriter(); port = p; readLoop();
  }
  async function connectWithRetry(p) {
    await openPort(p); await new Promise(r => setTimeout(r, 2500));
    for (let attempt = 0; attempt < 4; attempt++) {
      if (lost || !port.readable) {
        log(`bo vừa khởi động lại, nối lại lần ${attempt + 1}…`, "warn"); try { writer.releaseLock(); } catch {} try { await port.close(); } catch {}
        await new Promise(r => setTimeout(r, 2500)); const ports = await navigator.serial.getPorts(); const same = ports.find(x => x.getInfo().usbVendorId === 0x303A) || ports[0];
        if (!same) throw new Error("không tìm lại được cổng sau khi bo khởi động lại"); await openPort(same); await new Promise(r => setTimeout(r, 1500)); continue;
      }
      try { return await ping(); } catch (e) { log("bắt tay: " + e.message, "warn"); }
    }
    throw new Error("bo không trả lời sau 4 lần thử");
  }
  let ws = null;
  const send = async (s) => { if (ws) { ws.send(s); return; } await writer.write(new TextEncoder().encode(s + "\n")); };
  function onLine(s) {
    if (!s.startsWith("{")) { if (s) log(s, "warn"); return; }
    let j; try { j = JSON.parse(s); } catch { log("JSON lỗi: " + s, "err"); return; } onJson(j);
    if (j.t !== "STAT" || Math.random() < .02) log(s.slice(0, 160), j.t === "B" && (j.B14 || j.B45) ? "err" : "");
    if (j.t === "STAT" && pending.length) pending.shift()(j);
  }
  $("btnWs").onclick = async () => {
    const url = $("wsUrl").value || "ws://127.0.0.1:18795"; $("msg").textContent = "Đang nối cầu nối " + url + "…";
    try { ws = await new Promise((res, rej) => { const w = new WebSocket(url); w.onopen = () => res(w); w.onerror = () => rej(new Error("không nối được " + url + " (đã chạy 33_serial_ws_bridge.py chưa?)")); });
      ws.onmessage = (ev) => onLine(String(ev.data).trim()); ws.onclose = () => { log("cầu nối đã đóng", "warn"); ws = null; };
      const st = await ping(); $("msg").textContent = `Đã nối qua cầu nối. Bo trả lời: ${st.inferences} mẫu đã suy luận, heap ${(st.heap_free / 1024).toFixed(0)} KB.` + (st.inferences ? " Bo còn trạng thái cũ: bấm RST trên bo rồi nối lại." : " Trạng thái trắng, sẵn sàng phát lại."); $("role").textContent = "đã kết nối (cầu nối)"; if (lines) $("btnRun").disabled = false; }
    catch (e) { ws = null; $("msg").textContent = "Cầu nối lỗi: " + e.message; log(e.message, "err"); }
  };
  const ping = () => new Promise((res, rej) => {                       // dùng chung cho Web Serial và WebSocket
    let cb; const t = setTimeout(() => { const i = pending.indexOf(cb); if (i >= 0) pending.splice(i, 1); rej(new Error("bo không trả STAT trong 15 s")); }, 15000); cb = (j) => { clearTimeout(t); res(j); }; pending.push(cb); send("P").catch(rej); });
  $("btnConn").onclick = async () => {
    if (!("serial" in navigator)) { $("msg").textContent = "Trình duyệt không có Web Serial. Dùng Chrome hoặc Edge trên máy cắm bo."; return; }
    try { $("msg").textContent = "Đang kết nối, bo sẽ khởi động lại khi mở cổng…"; const p = await navigator.serial.requestPort({ filters: [{ usbVendorId: 0x303A }] }); const st = await connectWithRetry(p);
      $("msg").textContent = `Đã kết nối. Bo trả lời: ${st.inferences} mẫu đã suy luận, heap ${(st.heap_free / 1024).toFixed(0)} KB.` + (st.inferences ? " Bo còn trạng thái cũ: bấm RST trên bo rồi kết nối lại." : " Trạng thái trắng, sẵn sàng phát lại."); $("role").textContent = "đã kết nối"; if (lines) $("btnRun").disabled = false; }
    catch (e) { $("msg").textContent = "Kết nối lỗi: " + e.message + " — nếu Chrome trên Linux báo \"device has been lost\", dùng cầu nối WebSocket."; log("kết nối lỗi: " + e.message, "err"); }
  };
  $("btnFile").onclick = () => $("file").click();
  $("file").onchange = async (ev) => { const f = ev.target.files[0]; if (!f) return; const txt = await f.text(); lines = txt.split(/\r?\n/).filter(l => l.trim()); $("msg").textContent = `Đã nạp ${lines.length.toLocaleString("vi")} dòng từ ${f.name}.`; if (writer || ws) $("btnRun").disabled = false; };
  $("btnRun").onclick = async () => {
    running = true; $("btnRun").disabled = true; $("btnStop").disabled = false; const t0 = performance.now(); const CH = 8;
    try { for (let i = 0; i < lines.length && running; i++) { await send(lines[i]); if (i % CH === CH - 1) { await ping(); $("prog").style.width = (100 * i / lines.length).toFixed(1) + "%"; if (i % 800 === CH - 1) await new Promise(r => setTimeout(r, 0)); } }
      if (running) { await ping(); $("prog").style.width = "100%"; $("msg").textContent = `Phát lại xong ${lines.length.toLocaleString("vi")} dòng trong ${((performance.now() - t0) / 1000).toFixed(0)} s.`; log("HẾT LUỒNG", "ok"); } }
    catch (e) { $("msg").textContent = "Dừng vì lỗi: " + e.message; log(e.message, "err"); }
    running = false; $("btnStop").disabled = true; $("btnRun").disabled = false;
  };
  $("btnStop").onclick = () => { running = false; };
  chS.draw(0); chL.draw(0); cmp();
})();
