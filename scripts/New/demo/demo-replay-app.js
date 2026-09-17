/* demo-replay-app.js — trạng thái phát lại: ngày đang xem, đèn bốn tầng, chú thích, phím tắt (để Computer Use điều khiển bằng phím). */
(() => {
  const D = window.DEMO, N = D.days.length, idx = Object.fromEntries(D.days.map((d, i) => [d, i])); const P = D.params;
  const set = (name) => new Set(D.alarms[name]); const AL = { A: set("A"), B14: set("B14"), B45: set("B45"), C: set("C") };
  const fmt = (d) => d ? d.slice(8, 10) + "/" + d.slice(5, 7) + "/" + d.slice(0, 4) : "—"; const $ = (id) => document.getElementById(id);
  const stopsShade = D.stops.map(s => ({ stop: s.stop, restart: s.restart }));
  const ser = (src, keys, w) => keys.map(k => ({ key: k, vals: src[k], color: PAL[k], width: (k === "2001X" || k === "2003Y") ? 2.2 : (w || 1.3), alpha: (k === "2001X" || k === "2003Y") ? 1 : .75 }));
  const charts = [
    new DayChart({ el: "cDirect", days: D.days, idx, series: ser(D.direct, D.channels), ymin: 0, ymax: 80, yticks: [0, 20, 40, 60, 80], stops: stopsShade,
      hlines: [{ y: P.limit_um, label: "ngưỡng nhà máy 65 µm p-p", color: tok("--red") }], bands: [{ color: tok("--red"), set: D.alarms.A }] }),
    new DayChart({ el: "cSpe", days: D.days, idx, series: [{ key: "spe", vals: D.spe, color: "#f2d7a3", width: 2 }], ylog: true, ymin: -2, ymax: 3, yticks: [0.01, 0.1, 1, 10, 100, 1000], stops: stopsShade,
      hlines: [{ y: P.limit99_6h, label: "giới hạn kiểm soát 99% trên nền (" + P.limit99_6h + ")", color: tok("--blue") }], bands: [{ color: tok("--red"), set: D.alarms.B14 }, { color: tok("--amber"), set: D.alarms.B45 }] }),
    new DayChart({ el: "cAmp", days: D.days, idx, series: ser(D.amp1x, D.channels), ymin: 0, ymax: 60, yticks: [0, 15, 30, 45, 60], stops: stopsShade }),
  ];
  const legend = (id, keys) => $(id).innerHTML = keys.map(k => `<span><i style="background:${PAL[k]}"></i>${k}</span>`).join("");
  legend("legDirect", D.channels); legend("legAmp", D.channels); $("legSpe").innerHTML = `<span><i style="background:${tok("--red")}"></i>ngày B₁₄ báo (τ₁₄ = ${P.tau14})</span><span><i style="background:${tok("--amber")}"></i>ngày B₄₅ báo (τ₄₅ = ${P.tau45})</span>`;
  const light = (id, cls, state, detail) => { const el = $(id); el.className = "light " + cls; el.querySelector(".lstate").textContent = state; el.querySelector(".ldetail").textContent = detail; };
  const running = (i) => D.channels.filter(k => D.amp1x[k][i] != null && D.amp1x[k][i] > 3).length >= 6;   // máy chạy = kho đặc trưng 1X có mẫu qua cổng
  const hasDirect = (i) => D.channels.some(k => D.direct[k][i] != null);
  function lights(i) {
    const d = D.days[i], run = running(i);
    if (!run) { ["lA", "lB14", "lB45"].forEach(id => light(id, "gray", "máy dừng", "")); }
    else {
      const fa = D.tierA_flag[d]; if (!hasDirect(i)) light("lA", "gray", "chưa có Direct", "Direct kéo tới 21/07"); else light("lA", AL.A.has(d) ? "red" : fa ? "amber" : "green", AL.A.has(d) ? "BÁO" : fa ? "cờ" : "bình thường", fa ? `${fa.ch} · ${Math.round(fa.dl)} ngày tới 65` : (D.dl2001[i] != null && D.dl2001[i] < 200 ? `2001X · ${Math.round(D.dl2001[i])} ngày tới 65` : "không kênh nào leo"));
      const s14 = D.slope14[i], s45 = D.slope45[i];
      light("lB14", s14 == null ? "gray" : AL.B14.has(d) ? "red" : s14 > P.tau14 ? "amber" : "green", s14 == null ? "chưa đủ 14 ngày" : AL.B14.has(d) ? "BÁO" : s14 > P.tau14 ? "cờ" : "bình thường", s14 == null ? "" : `dốc ${s14.toFixed(3)} / τ ${P.tau14}`);
      light("lB45", s45 == null ? "gray" : AL.B45.has(d) ? "red" : s45 > P.tau45 ? "amber" : "green", s45 == null ? "chưa đủ 45 ngày" : AL.B45.has(d) ? "BÁO" : s45 > P.tau45 ? "cờ" : "bình thường", s45 == null ? "" : `dốc ${s45.toFixed(3)} / τ ${P.tau45}`);
    }
    const w = drawCompass($("cComp"), D.weeks, d);
    if (!w) { light("lC", "gray", "chưa có tuần", ""); $("compTxt").textContent = ""; }
    else { light("lC", w.alarm ? "red" : w.flag ? "amber" : "green", w.alarm ? "CẦN XEM" : w.flag ? "cờ tuần 1" : "bình thường", `quay ${w.rot ?? "—"}°/tuần · 8 tuần trước ${w.rot8 ?? "—"}${w.post ? " · sau khởi động" : ""}`);
      $("compTxt").textContent = `tuần tới ${fmt(w.end)} · pha 2001X ${w.ph["2001X"]}° · biên ${w.amp2001X} µm · ${w.post ? "trong 21 ngày sau khởi động" : "chế độ thường"}`; }
  }
  function channels(i) {
    const d = D.days[i], fa = D.tierA_flag[d];
    $("chan").innerHTML = D.channels.map(k => { const v = D.direct[k][i]; const hot = fa && fa.ch === k && AL.A.has(d); const warm = fa && fa.ch === k;
      return `<div class="ch ${hot ? "hot" : warm ? "warm" : ""}"><div class="n">${k}</div><div class="v">${v == null ? "—" : v.toFixed(1)}</div><div class="d">${hot || warm ? "còn " + Math.round(fa.dl) + " ngày" : v == null ? "chưa có Direct" : v > 3 ? Math.round(v / P.limit_um * 100) + "% của 65" : "dừng"}</div></div>`; }).join("");
  }
  function note(i) { const d = D.days[i]; let n = null; for (const x of NOTES) if (x.d <= d) n = x; if (!n) return; $("noteTitle").textContent = n.t; $("noteBody").innerHTML = n.b; $("noteDate").textContent = "mốc " + fmt(n.d); }
  function model() {
    const e = D.events.dung2, lt = (k) => e[k].lead_days == null ? "không báo" : `${fmt(e[k].first_alarm)} · ${e[k].lead_days} ngày`;
    $("model").innerHTML = `<table><tr><td>Mô hình tầng B</td><td>${P.model} (SAE, phạt L1)</td></tr><tr><td>Kiến trúc</td><td>${P.arch}</td></tr><tr><td>Tham số</td><td>${P.n_params.toLocaleString("vi")} · float32 ${(P.n_params * 4 / 1024).toFixed(1)} KB · int8 ${(P.n_params / 1024).toFixed(1)} KB</td></tr>
      <tr><td>Một lần suy luận</td><td>≈ ${(6 * 576).toLocaleString("vi")} phép nhân-cộng · mỗi 10 phút</td></tr><tr><td>Ngưỡng khóa</td><td>τ₁₄ ${P.tau14} (3 ngày) · τ₄₅ ${P.tau45} (${P.consec45} ngày) · 65 µm · chân trời ${P.horizon_days} ngày</td></tr>
      <tr><td>Đầu vào · trạng thái</td><td>24 số (8 biên độ 1X, 8 sin, 8 cos) · đệm 45 ngày ≈ 25 KB</td></tr><tr><td>Lead-time dừng 2</td><td>B₁₄ ${lt("B14_SAE")} · B₄₅ ${lt("B45_SAE")} · A ${lt("A_direct_65um")}</td></tr></table>
      <div style="margin-top:6px;color:var(--dim);font-size:12px">Khóa ${D.backtest_locked_at} · hash đầu vào ghi trong file · phase 04: int8, mã C, đo trên ARM</div>`;
  }
  function summary() {
    const e = D.events, r = (k, n) => `<tr><td>${n}</td><td>${e.dung1[k].lead_days == null ? "không báo" : e.dung1[k].lead_days + " ngày"}</td><td>${e.dung2[k].first_alarm ? `<b>${fmt(e.dung2[k].first_alarm)} · ${e.dung2[k].lead_days} ngày</b>` : "không báo"}</td><td>${["ep7", "ep8", "9a"].map(x => D.negatives[x][k]).join(" / ")}</td><td>${D.blind[k].plateau_alarm_days} / ${D.blind[k].climb_alarm_days}</td></tr>`;
    $("summary").innerHTML = `<h2>Tổng kết backtest (lần chạy 3, đã khóa)</h2><table><tr><th>Tầng</th><th>Dừng 1 · 04/01/2026</th><th>Dừng 2 · 29/05/2026</th><th>Đoạn âm 7 / 8 / 9a</th><th>Đoạn 11 mù: bình nguyên / leo</th></tr>
      ${r("A_direct_65um", "A · Direct → 65 µm (29/04 do 2003Y, hợp lệ theo luật)")}${r("B14_SAE", "B₁₄ · SAE, dốc 14 ngày, τ = " + P.tau14)}${r("B45_SAE", "B₄₅ · SAE, dốc 45 ngày, τ = " + P.tau45)}${r("C_phase_flip", "C · chữ ký pha 2001 (1 tuần 9a nằm trong 21 ngày sau khởi động)")}</table>
      <p>Dừng 1: không tầng nào báo, đúng kỳ vọng. Dừng 2: tầng B báo 53 và 48 ngày trước; B₄₅ giữ báo suốt tháng 5 khi B₁₄ đã tắt. Đoạn 11: không báo giả; đợt leo chậm từ 19/07 chưa tầng nào báo, C đang ở cờ đơn. Phase 04: lượng tử hóa SAE 3.600 tham số sang int8 và nhúng.</p>`;
  }
  let cur = 0, playing = false, speed = 3, acc = 0, last = 0; const RATE = { 1: .5, 3: 1.5, 10: 5 };
  function render(i) { cur = Math.max(0, Math.min(N - 1, i)); $("slider").value = cur; const d = D.days[cur]; $("day").textContent = fmt(d); const role = { train: "nền gốc · huấn luyện", config_pos: "9c nửa đầu · chỉnh ngưỡng", precheck_pos: "9c nửa sau · kiểm trước", neg: "đoạn âm", report: "chỉ mô tả", blind: "kiểm mù đoạn 11" }[D.role[cur]] || (running(cur) ? "chưa có nền" : "máy dừng"); $("role").textContent = role; charts.forEach(c => c.draw(cur)); lights(cur); channels(cur); note(cur); }
  function tick(t) { if (!playing) return; acc += (t - last) / 1000 * RATE[speed]; last = t; if (acc >= 1) { const n = Math.floor(acc); acc -= n; render(cur + n); if (cur >= N - 1) toggle(false); } requestAnimationFrame(tick); }
  function toggle(on) { playing = on == null ? !playing : on; $("btnPlay").textContent = playing ? "⏸ Dừng" : "▶ Phát"; $("btnPlay").classList.toggle("on", playing); if (playing) { last = performance.now(); acc = 0; requestAnimationFrame(tick); } }
  function setSpeed(s) { speed = s; document.querySelectorAll(".sp").forEach(b => b.classList.toggle("on", +b.dataset.s === s)); }
  const jump = (d) => { toggle(false); render(idx[d] ?? 0); };
  document.addEventListener("keydown", (e) => { const k = e.key; if (k === " ") { e.preventDefault(); toggle(); } else if (k === "ArrowRight") render(cur + 1); else if (k === "ArrowLeft") render(cur - 1);
    else if (/^[0-9]$/.test(k)) { const n = NOTES.find(x => x.k === k); if (n) jump(n.d); } else if (k === "n" || k === "p") { const d = D.days[cur]; const nx = k === "n" ? NOTES.find(x => x.d > d) : [...NOTES].reverse().find(x => x.d < d); if (nx) jump(nx.d); }
    else if (k === "F9") { $("summary").hidden = !$("summary").hidden; } else if (k === "Escape") { $("summary").hidden = true; } /* F9 thay "t": tránh phím chữ lạc làm bật bảng */ else if (k === "a") setSpeed(1); else if (k === "s") setSpeed(3); else if (k === "d") setSpeed(10); });
  $("btnPlay").onclick = () => toggle(); document.querySelectorAll(".sp").forEach(b => b.onclick = () => setSpeed(+b.dataset.s)); $("slider").max = N - 1; $("slider").oninput = (e) => { toggle(false); render(+e.target.value); };
  $("d0").textContent = fmt(D.days[0]); $("d1").textContent = fmt(D.days[N - 1]); setSpeed(3); model(); summary(); const h = location.hash.slice(1); render(idx[h] ?? 0);   // #YYYY-MM-DD: mở thẳng tại một ngày (cho ảnh chụp và kịch bản quay)
})();
