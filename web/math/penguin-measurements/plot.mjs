import { bins, domain, fit, project, species, traits } from './data.mjs';

const colors = ['#007570', '#a44518', '#564aa3'];
const label = (key) => traits[key].name + ' (' + traits[key].unit + ')';
const tick = (n) => Number(n.toFixed(1)).toLocaleString('en-US');

export function plot(canvas, all, rows, cfg) {
  const w = canvas.clientWidth,
    h = canvas.clientHeight,
    ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(w * ratio);
  canvas.height = Math.round(h * ratio);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, w, h);
  ctx.font = '13px system-ui, sans-serif';
  const left = 55,
    right = w - 18,
    top = 33,
    bottom = h - 50,
    picks = [];
  function line(x0, y0, x1, y1, color, width = 1) {
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.stroke();
  }
  function text(str, x, y, align = 'left') {
    ctx.textAlign = align;
    ctx.fillStyle = '#223743';
    ctx.fillText(str, x, y);
  }
  function point(px, py, row) {
    const group = species.indexOf(row.species),
      r = 3.8;
    ctx.fillStyle = colors[group];
    ctx.beginPath();
    if (group === 0) ctx.arc(px, py, r, 0, 2 * Math.PI);
    else if (group === 1) ctx.rect(px - r, py - r, 2 * r, 2 * r);
    else {
      ctx.moveTo(px, py - r - 1);
      ctx.lineTo(px + r + 1, py + r);
      ctx.lineTo(px - r - 1, py + r);
      ctx.closePath();
    }
    ctx.fill();
    picks.push({ px, py, row: row.row });
  }
  const xDomain = domain(all, cfg.x);
  function cartesian(xr, yr, verticalName) {
    const X = (v) => left + ((v - xr[0]) / (xr[1] - xr[0])) * (right - left);
    const Y = (v) => bottom - ((v - yr[0]) / (yr[1] - yr[0])) * (bottom - top);
    for (let i = 0; i <= 4; i++) {
      const x = xr[0] + ((xr[1] - xr[0]) * i) / 4;
      line(X(x), top, X(x), bottom, '#e2e8e8');
      text(tick(x), X(x), bottom + 19, 'center');
    }
    const yTicks = cfg.mode === 'hist' ? Math.min(4, yr[1]) : 4;
    for (let i = 0; i <= yTicks; i++) {
      const y = yr[0] + ((yr[1] - yr[0]) * i) / yTicks;
      line(left, Y(y), right, Y(y), '#d4dede');
      text(tick(y), left - 5, Y(y) + 4, 'right');
    }
    line(left, top, left, bottom, '#465963');
    line(left, bottom, right, bottom, '#465963');
    text(verticalName, left, 18);
    text(label(cfg.x), (left + right) / 2, h - 6, 'center');
    return { X, Y };
  }
  if (cfg.mode === 'hist') {
    const histogram = bins(rows, cfg.x, xDomain);
    const peak = Math.max(1, ...histogram.map((b) => b.total));
    const ceiling = peak <= 4 ? peak : 4 * Math.ceil(peak / 4);
    const { X, Y } = cartesian(xDomain, [0, ceiling], 'Number of birds');
    for (const b of histogram) {
      let count = 0;
      b.counts.forEach((n, s) => {
        ctx.fillStyle = colors[s];
        ctx.fillRect(
          X(b.start) + 0.5,
          Y(count + n),
          Math.max(1, X(b.end) - X(b.start) - 1),
          Y(count) - Y(count + n)
        );
        count += n;
      });
    }
  } else if (cfg.mode === 'xy') {
    const { X, Y } = cartesian(xDomain, domain(all, cfg.y), label(cfg.y));
    const regression = fit(rows, cfg.x, cfg.y);
    ctx.save();
    ctx.beginPath();
    ctx.rect(left, top, right - left, bottom - top);
    ctx.clip();
    rows.forEach((row) => point(X(row[cfg.x]), Y(row[cfg.y]), row));
    if (regression) {
      const { min, max, slope, intercept } = regression;
      line(X(min), Y(min * slope + intercept), X(max), Y(max * slope + intercept), '#152933', 2);
    }
    ctx.restore();
  } else {
    const keys = [cfg.x, cfg.y, cfg.z],
      domains = keys.map((key) => domain(all, key));
    const scale = Math.min((w - 45) / 3.15, (h - 65) / 3.45);
    const screen = (v) => {
      const p = project(v, cfg.yaw, cfg.pitch);
      return { x: w / 2 + p.x * scale, y: h / 2 - p.y * scale, depth: p.depth };
    };
    function edge(a, b) {
      const start = screen(a),
        end = screen(b);
      line(start.x, start.y, end.x, end.y, '#879b9e');
    }
    // Keep the same physical ranges while rotating or filtering the field records.
    for (const at of [-0.5, 0, 0.5]) {
      edge([-1, -1, at], [1, -1, at]);
      edge([at, -1, -1], [at, -1, 1]);
    }
    for (let dim = 0; dim < 3; dim++) {
      for (const a of [-1, 1])
        for (const b of [-1, 1]) {
          const start = [0, 0, 0];
          start[dim] = -1;
          start[(dim + 1) % 3] = a;
          start[(dim + 2) % 3] = b;
          const end = start.slice();
          end[dim] = 1;
          edge(start, end);
        }
      const tip = [-1, -1, -1];
      tip[dim] = 1;
      const projected = screen(tip);
      text(['X', 'Y', 'Z'][dim], projected.x, projected.y - 5, 'center');
    }
    const projected = rows.map((row) => {
      const p = keys.map(
        (key, i) => (2 * (row[key] - domains[i][0])) / (domains[i][1] - domains[i][0]) - 1
      );
      return { ...screen(p), row };
    });
    projected.sort((a, b) => a.depth - b.depth).forEach((p) => point(p.x, p.y, p.row));
  }
  const chosen = picks.find((p) => p.row === cfg.selected);
  if (chosen) {
    ctx.beginPath();
    ctx.arc(chosen.px, chosen.py, 7.5, 0, 2 * Math.PI);
    ctx.strokeStyle = '#142731';
    ctx.lineWidth = 2;
    ctx.stroke();
  }
  return picks;
}
