import { sectionAxes } from './geometry.mjs';
const num = (n, d = 0) => n.toLocaleString('en-US', { maximumFractionDigits: d });
function paper(canvas) {
  const w = canvas.clientWidth,
    h = canvas.clientHeight,
    ratio = Math.min(2, window.devicePixelRatio || 1);
  canvas.width = Math.max(1, Math.round(w * ratio));
  canvas.height = Math.max(1, Math.round(h * ratio));
  const ctx = canvas.getContext('2d');
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, w, h);
  ctx.font = '13px system-ui, sans-serif';
  return { ctx, w, h };
}
function line(ctx, x1, y1, x2, y2, colour, weight = 1) {
  ctx.strokeStyle = colour;
  ctx.lineWidth = weight;
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}
export function sectionPlot(canvas, model, axis, slice) {
  const { ctx, w, h } = paper(canvas),
    [u, v] = sectionAxes[axis],
    low = model.bounds[0],
    high = model.bounds[1];
  const scale = Math.min((w - 32) / (high[u] - low[u]), (h - 40) / (high[v] - low[v]));
  const X = (x) => w / 2 + (x - (high[u] + low[u]) / 2) * scale;
  const Y = (y) => h / 2 - (y - (high[v] + low[v]) / 2) * scale;
  const boundary = slice.segments;
  ctx.beginPath();
  for (let i = 0; i < boundary.length; i += 6) {
    ctx.moveTo(w / 2, h / 2);
    ctx.lineTo(X(boundary[i + u]), Y(boundary[i + v]));
    ctx.lineTo(X(boundary[i + 3 + u]), Y(boundary[i + 3 + v]));
    ctx.closePath();
  }
  ctx.fillStyle = '#b7dbd5';
  ctx.fill('evenodd');
  ctx.strokeStyle = '#087479';
  ctx.lineWidth = 2;
  ctx.beginPath();
  const segments = slice.segments;
  for (let i = 0; i < segments.length; i += 6) {
    ctx.moveTo(X(segments[i + u]), Y(segments[i + v]));
    ctx.lineTo(X(segments[i + 3 + u]), Y(segments[i + 3 + v]));
  }
  ctx.stroke();
  ctx.fillStyle = '#18343e';
  ctx.fillText('+' + 'XYZ'[v] + ' ↑     +' + 'XYZ'[u] + ' →', 10, 17);
  line(ctx, 12, h - 12, 12 + 100 * scale, h - 12, '#253440', 2);
  ctx.fillText('100 m', 12, h - 19);
  canvas.dataset.segments = String(segments.length / 6);
}
export function profilePlot(canvas, model, axis, sample, method, selected) {
  const { ctx, w, h } = paper(canvas),
    values = model.profiles[axis],
    steps = values.length - 1;
  const left = 54,
    right = w - 18,
    top = 26,
    bottom = h - 39;
  const max = Math.ceil(Math.max(...values) / 50000) * 50000;
  const X = (t) => left + t * (right - left);
  const Y = (a) => bottom - (a / max) * (bottom - top);
  ctx.fillStyle = '#20313a';
  ctx.fillText('Section area (m²)', left, 16);
  for (let i = 0; i <= 4; i++) {
    const a = (i * max) / 4;
    line(ctx, left, Y(a), right, Y(a), '#e0e4e4');
    ctx.textAlign = 'right';
    ctx.fillText(i === 0 ? '0' : num(a / 1000, 1) + 'k', left - 5, Y(a) + 4);
  }
  const n = sample.slabs.length;
  sample.slabs.forEach((slab, i) => {
    const a = method === 'trapezoid' ? slab.left : slab.sample,
      b = method === 'trapezoid' ? slab.right : slab.sample;
    ctx.beginPath();
    ctx.moveTo(X(i / n), bottom);
    ctx.lineTo(X(i / n), Y(a));
    ctx.lineTo(X((i + 1) / n), Y(b));
    ctx.lineTo(X((i + 1) / n), bottom);
    ctx.closePath();
    ctx.fillStyle = i % 2 ? '#c9e4df' : '#b1d8cf';
    ctx.fill();
    if (n <= 16) {
      ctx.strokeStyle = '#649a90';
      ctx.lineWidth = 0.7;
      ctx.stroke();
    }
  });
  ctx.strokeStyle = '#08545b';
  ctx.lineWidth = 2;
  ctx.beginPath();
  values.forEach((a, i) => {
    if (i === 0) ctx.moveTo(X(0), Y(a));
    else ctx.lineTo(X(i / steps), Y(a));
  });
  ctx.stroke();
  const t = selected / steps;
  line(ctx, X(t), top, X(t), bottom, '#a34923', 1.5);
  ctx.fillStyle = '#a34923';
  ctx.beginPath();
  ctx.arc(X(t), Y(values[selected]), 3, 0, 2 * Math.PI);
  ctx.fill();
  ctx.fillStyle = '#20313a';
  ctx.textAlign = 'left';
  ctx.fillText(num(model.bounds[0][axis], 1), left, bottom + 16);
  ctx.textAlign = 'right';
  ctx.fillText(num(model.bounds[1][axis], 1), right, bottom + 16);
  ctx.textAlign = 'center';
  ctx.fillText('XYZ'[axis] + ' position (m)', (left + right) / 2, h - 5);
}
