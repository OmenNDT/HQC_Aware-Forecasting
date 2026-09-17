/* demo-charts-canvas.js — vẽ đồ thị đường theo ngày trên canvas (không thư viện), cắt tại ngày đang xem (nhân quả). */
const PAL = { "2001X": "#e8a06a", "2001Y": "#c97c4a", "2003X": "#7fb3d5", "2003Y": "#4f8fc9", "2005X": "#9fcf9a", "2005Y": "#5f9a6a", "2007X": "#c9a0d8", "2007Y": "#8f6aa8" };
const CSS = getComputedStyle(document.documentElement); const tok = (n) => CSS.getPropertyValue(n).trim();

class DayChart {
  /* opts: {el, days, idx, series:[{key,vals,color,width}], ymin,ymax, ylog, yticks, hlines:[{y,label,color}], bands:[{color,set}], stops} */
  constructor(opts) {
    Object.assign(this, opts); this.cv = document.getElementById(this.el); this.ctx = this.cv.getContext("2d");
    this.pad = { l: 58, r: 14, t: 10, b: 24 }; this.resize();
  }
  resize() { const r = this.cv.getBoundingClientRect(); this.cv.width = r.width * devicePixelRatio; this.cv.height = r.height * devicePixelRatio; this.W = r.width; this.H = r.height; this.ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0); }
  x(i) { return this.pad.l + (i / (this.days.length - 1)) * (this.W - this.pad.l - this.pad.r); }
  y(v) { const a = this.ylog ? Math.log10(Math.max(v, 1e-6)) : v; return this.pad.t + (1 - (a - this.ymin) / (this.ymax - this.ymin)) * (this.H - this.pad.t - this.pad.b); }
  draw(cut) {
    const c = this.ctx, W = this.W, H = this.H; c.clearRect(0, 0, W, H);
    const y0 = this.pad.t, y1 = H - this.pad.b, x0 = this.pad.l, x1 = W - this.pad.r;
    (this.stops || []).forEach(s => { const a = this.idx[s.stop], b = this.idx[s.restart]; if (a == null || b == null) return; c.fillStyle = "rgba(255,255,255,.04)"; c.fillRect(this.x(a), y0, Math.max(2, this.x(b) - this.x(a)), y1 - y0); });
    (this.bands || []).forEach((bd, k) => { c.fillStyle = bd.color; bd.set.forEach(d => { const i = this.idx[d]; if (i != null && i <= cut) c.fillRect(this.x(i) - 1.5, y0 + k * 6, 3, 5); }); });
    c.strokeStyle = tok("--mute"); c.lineWidth = 1; c.fillStyle = tok("--dim"); c.font = "11px Inter,system-ui,sans-serif"; c.textAlign = "right";
    (this.yticks || []).forEach(v => { const yy = this.y(v); c.beginPath(); c.moveTo(x0, yy); c.lineTo(x1, yy); c.globalAlpha = .5; c.stroke(); c.globalAlpha = 1; c.fillText(String(v), x0 - 6, yy + 4); });
    c.textAlign = "center"; this.days.forEach((d, i) => { if (d.slice(8) === "01") { const xx = this.x(i); c.globalAlpha = .35; c.beginPath(); c.moveTo(xx, y0); c.lineTo(xx, y1); c.stroke(); c.globalAlpha = 1; c.fillText(d.slice(5, 7) + "/" + d.slice(2, 4), xx, H - 8); } });
    (this.hlines || []).forEach(h => { const yy = this.y(h.y); c.strokeStyle = h.color; c.setLineDash([6, 5]); c.beginPath(); c.moveTo(x0, yy); c.lineTo(x1, yy); c.stroke(); c.setLineDash([]); c.fillStyle = h.color; c.textAlign = "left"; c.fillText(h.label, x0 + 6, yy - 4); });
    this.series.forEach(s => {
      c.strokeStyle = s.color; c.lineWidth = s.width || 1.6; c.globalAlpha = s.alpha || 1; c.beginPath(); let pen = false;
      for (let i = 0; i <= cut; i++) { const v = s.vals[i]; if (v == null || (this.ylog && v <= 0)) { pen = false; continue; } const xx = this.x(i), yy = this.y(v); pen ? c.lineTo(xx, yy) : c.moveTo(xx, yy); pen = true; }
      c.stroke(); c.globalAlpha = 1;
      const last = this.lastValid(s.vals, cut); if (last != null) { c.fillStyle = s.color; c.beginPath(); c.arc(this.x(last), this.y(s.vals[last]), 3.2, 0, 7); c.fill(); }
    });
    const xc = this.x(cut); c.strokeStyle = "#f2d7a3"; c.globalAlpha = .8; c.lineWidth = 1; c.beginPath(); c.moveTo(xc, y0); c.lineTo(xc, y1); c.stroke(); c.globalAlpha = 1;
  }
  lastValid(v, cut) { for (let i = cut; i >= Math.max(0, cut - 6); i--) if (v[i] != null) return i; return null; }
}

/* La bàn pha: vết các tuần ≤ ngày cut, mũi tên tuần mới nhất; bán kính = biên độ 1X (tối đa 40 µm). */
function drawCompass(cv, weeks, cutDay) {
  const r = cv.getBoundingClientRect(); cv.width = r.width * devicePixelRatio; cv.height = r.height * devicePixelRatio; const c = cv.getContext("2d"); c.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
  const W = r.width, H = r.height, cx = W / 2, cy = H / 2 + 4, R = Math.min(W, H) / 2 - 22; c.clearRect(0, 0, W, H);
  c.strokeStyle = tok("--mute"); c.lineWidth = 1; [R, R * .5].forEach(rr => { c.beginPath(); c.arc(cx, cy, rr, 0, 7); c.stroke(); });
  c.fillStyle = tok("--dim"); c.font = "11px Inter,system-ui,sans-serif"; c.textAlign = "center";
  [0, 90, 180, 270].forEach(a => { const t = -a * Math.PI / 180; c.fillText(a + "°", cx + (R + 12) * Math.cos(t), cy + (R + 12) * Math.sin(t) + 4); });
  const ws = weeks.filter(w => w.end <= cutDay); const pt = w => { const t = -w.ph["2001X"] * Math.PI / 180, rr = R * Math.min(1, w.amp2001X / 40); return [cx + rr * Math.cos(t), cy + rr * Math.sin(t)]; };
  c.strokeStyle = PAL["2001X"]; c.lineWidth = 1.4; c.globalAlpha = .55; c.beginPath(); ws.forEach((w, i) => { const [x, y] = pt(w); i ? c.lineTo(x, y) : c.moveTo(x, y); }); c.stroke(); c.globalAlpha = 1;
  ws.forEach(w => { const [x, y] = pt(w); c.fillStyle = w.alarm ? tok("--red") : w.flag ? tok("--amber") : PAL["2001X"]; c.beginPath(); c.arc(x, y, 2.6, 0, 7); c.fill(); });
  const last = ws[ws.length - 1]; if (last) { const [x, y] = pt(last); c.strokeStyle = "#f2d7a3"; c.lineWidth = 2.2; c.beginPath(); c.moveTo(cx, cy); c.lineTo(x, y); c.stroke(); c.fillStyle = "#f2d7a3"; c.beginPath(); c.arc(x, y, 4.5, 0, 7); c.fill(); }
  return last;
}
