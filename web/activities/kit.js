'use strict';
/* Shared drawing and formatting helpers for the stand-alone lesson activities. */
const Kit = (() => {
  const get = id => document.getElementById(id);
  const fmt = (value, digits = 4) => Number.isFinite(value) ? Number(value.toPrecision(digits)).toString() : '—';
  function ticks(min, max, count = 5) {
    const raw = (max - min) / count, power = 10 ** Math.floor(Math.log10(raw));
    const step = [1, 2, 2.5, 5, 10].map(m => m * power).find(s => s >= raw) || raw;
    const out = [];
    for (let v = Math.ceil(min / step - 1e-9) * step; v <= max + step * 1e-9; v += step) out.push(Math.abs(v) < step * 1e-9 ? 0 : v);
    return out;
  }
  function plot(canvas, {x, y, xlabel = 'x', ylabel = 'y', grid = true}) {
    const ctx = canvas.getContext('2d'), W = canvas.width, H = canvas.height;
    const box = {l: 62, r: W - 18, t: 22, b: H - 44};
    const X = v => box.l + (v - x[0]) * (box.r - box.l) / (x[1] - x[0]);
    const Y = v => box.b - (v - y[0]) * (box.b - box.t) / (y[1] - y[0]);
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H);
    ctx.font = '15px system-ui, sans-serif'; ctx.lineWidth = 1;
    const seg = (x0, y0, x1, y1, colour = '#172533', width = 1, dash = []) => {
      ctx.save(); ctx.strokeStyle = colour; ctx.lineWidth = width; ctx.setLineDash(dash);
      ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); ctx.restore();
    };
    if (grid) {
      for (const v of ticks(x[0], x[1])) {
        seg(X(v), box.t, X(v), box.b, '#d8dfe4');
        ctx.fillStyle = '#172533'; const s = fmt(v); ctx.fillText(s, X(v) - ctx.measureText(s).width / 2, box.b + 18);
      }
      for (const v of ticks(y[0], y[1])) {
        seg(box.l, Y(v), box.r, Y(v), '#d8dfe4');
        ctx.fillStyle = '#172533'; const s = fmt(v); ctx.fillText(s, box.l - 8 - ctx.measureText(s).width, Y(v) + 5);
      }
      const ax = x[0] <= 0 && x[1] >= 0 ? X(0) : box.l, ay = y[0] <= 0 && y[1] >= 0 ? Y(0) : box.b;
      seg(box.l, ay, box.r, ay, '#172533', 1.5); seg(ax, box.t, ax, box.b, '#172533', 1.5);
      ctx.fillStyle = '#172533';
      ctx.fillText(xlabel, box.r - ctx.measureText(xlabel).width, box.b + 36);
      ctx.fillText(ylabel, box.l - 50, box.t - 6);
    }
    const line = (x0, y0, x1, y1, colour, width = 2.5, dash) => seg(X(x0), Y(y0), X(x1), Y(y1), colour, width, dash);
    function curve(fn, colour = '#215783', from = x[0], to = x[1], width = 3) {
      ctx.save(); ctx.beginPath(); ctx.rect(box.l, box.t, box.r - box.l, box.b - box.t); ctx.clip();
      ctx.beginPath(); let pen = false;
      for (let i = 0; i <= 400; i++) {
        const v = from + (to - from) * i / 400, w = fn(v);
        if (!Number.isFinite(w)) { pen = false; continue; }
        if (pen) ctx.lineTo(X(v), Y(w)); else ctx.moveTo(X(v), Y(w));
        pen = true;
      }
      ctx.strokeStyle = colour; ctx.lineWidth = width; ctx.stroke(); ctx.restore();
    }
    function point(px, py, colour = '#963d18', radius = 6, open = false) {
      ctx.beginPath(); ctx.arc(X(px), Y(py), radius, 0, 2 * Math.PI);
      ctx.fillStyle = open ? '#fff' : colour; ctx.strokeStyle = colour; ctx.lineWidth = 2; ctx.fill(); ctx.stroke();
    }
    function text(s, px, py, colour = '#172533', dx = 8, dy = -8) { ctx.fillStyle = colour; ctx.fillText(s, X(px) + dx, Y(py) + dy); }
    function arrow(x0, y0, x1, y1, colour = '#215783', width = 3) {
      const a = X(x0), b = Y(y0), c = X(x1), d = Y(y1), angle = Math.atan2(d - b, c - a);
      seg(a, b, c, d, colour, width);
      if (Math.hypot(c - a, d - b) < 4) return;
      ctx.beginPath(); ctx.moveTo(c, d);
      ctx.lineTo(c - 11 * Math.cos(angle - 0.4), d - 11 * Math.sin(angle - 0.4));
      ctx.lineTo(c - 11 * Math.cos(angle + 0.4), d - 11 * Math.sin(angle + 0.4));
      ctx.closePath(); ctx.fillStyle = colour; ctx.fill();
    }
    return {ctx, X, Y, box, line, curve, point, text, arrow};
  }
  function rows(body, data) {
    body.replaceChildren(...data.map(cells => {
      const row = document.createElement('tr');
      cells.forEach((cell, index) => {
        const node = document.createElement(index ? 'td' : 'th');
        if (!index) node.scope = 'row';
        node.textContent = typeof cell === 'number' ? fmt(cell) : cell;
        row.append(node);
      });
      return row;
    }));
  }
  function bind(ids, draw) {
    for (const id of ids) { const node = get(id); node.addEventListener('input', draw); node.addEventListener('change', draw); }
    draw();
  }
  const num = id => get(id).valueAsNumber;
  function say(id, value, text) { const out = get(id + '-out'); if (out) out.textContent = text; get(id).setAttribute('aria-valuetext', text); }
  return {get, fmt, ticks, plot, rows, bind, num, say};
})();
