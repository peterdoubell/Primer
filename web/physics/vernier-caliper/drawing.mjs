import { inspectDivision } from './model.mjs';

function surface(canvas) {
  const width = canvas.clientWidth, height = canvas.clientHeight;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.lineCap = 'butt';
  ctx.lineJoin = 'round';
  return { ctx, width, height };
}

function stroke(ctx, from, to, color, thickness = 1) {
  ctx.beginPath();
  ctx.moveTo(...from);
  ctx.lineTo(...to);
  ctx.strokeStyle = color;
  ctx.lineWidth = thickness;
  ctx.stroke();
}

export function instrument(canvas, gap, specimen, reading, angle) {
  const { ctx, width, height } = surface(canvas);
  const rad = angle * Math.PI / 180, tilt = 0.22;
  const factor = Math.min((width - 24) / 70, (height - 12) / 37);
  function project([x, y, z]) {
    x -= 26;
    y += 6;
    const depth = x * Math.sin(rad) + z * Math.cos(rad);
    return [width / 2 + factor * (x * Math.cos(rad) - z * Math.sin(rad)),
      height / 2 - factor * (y * Math.cos(tilt) - depth * Math.sin(tilt)),
      y * Math.sin(tilt) + depth * Math.cos(tilt)];
  }
  const faces = [];
  function face(points, color, engrave) {
    const vertices = points.map(project);
    faces.push({ vertices, color, engrave, depth: vertices.reduce((sum, p) => sum + p[2], 0) / vertices.length });
  }
  // Each transverse profile is extruded along the viewing axis. The jaws' inner faces are x=0 and x=gap.
  function solid(profile, back, front, colors, engrave) {
    const ring = z => profile.map(([x, y]) => [x, y, z]);
    const rear = ring(back), near = ring(front);
    face(rear, colors.edge);
    for (let i = 0; i < profile.length; i++) {
      const j = (i + 1) % profile.length;
      face([rear[i], rear[j], near[j], near[i]], profile[i][1] === profile[j][1] ? colors.top : colors.edge);
    }
    face(near, colors.front, engrave);
  }
  function engraveRuler(start, count, pitch, edge, sign, z) {
    for (let i = 0; i <= count; i++) {
      const x = start + i * pitch, mark = i % 5 === 0 ? 2.8 : 1.4;
      stroke(ctx, project([x, edge, z]).slice(0, 2), project([x, edge + sign * mark, z]).slice(0, 2), '#233b43', .85);
      if (i % 10 === 0 && sign > 0) {
        const [tx, ty] = project([x, edge + 3.4, z]);
        ctx.fillStyle = '#233b43';
        ctx.textAlign = 'center';
        ctx.font = Math.max(7, factor * 1.6) + 'px system-ui, sans-serif';
        ctx.fillText(String(i), tx, ty);
      }
    }
  }
  const steel = { front: '#cbd5d6', top: '#f7fbfa', edge: '#879aa2' };
  const slide = { front: '#e0e7e6', top: '#fff', edge: '#83979b' };
  solid([[-4, 8], [59, 8], [59, 2], [-4, 2]], -2, 2, steel, () => engraveRuler(0, 58, 1, 2, 1, 2));
  solid([[-4, 2], [0, 2], [0, -22], [-1, -22], [-4, -16]], -2, 2, steel);
  solid([[gap, -4.5], [gap + 4, -4.5], [gap + 4, -16], [gap + 1, -22], [gap, -22]], -2, 2, slide);
  solid([[gap - 1.5, 2], [gap + reading.divisions + 1, 2], [gap + reading.divisions + 1, -3.5],
    [gap + 4, -5], [gap, -5], [gap - 1.5, -3.5]], -2.2, 2.2, slide,
    () => engraveRuler(reading.origin, reading.divisions, reading.pitch, 2, -1, 2.2));
  if (specimen !== null) {
    solid([[0, -10], [specimen, -10], [specimen, -18], [0, -18]], -3, 3,
      { front: '#b58c4d', top: '#e3bc7a', edge: '#846234' });
  }
  for (const { vertices, color, engrave } of faces.sort((a, b) => a.depth - b.depth)) {
    ctx.beginPath();
    vertices.forEach(([x, y], i) => { if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); });
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = '#5b6e73';
    ctx.lineWidth = .6;
    ctx.stroke();
    if (engrave) engrave();
  }
}

export function scales(canvas, reading, index, magnified) {
  const { ctx, width, height } = surface(canvas);
  const selected = inspectDivision(reading, index);
  const span = magnified ? 2.5 : reading.divisions + 2.5;
  const start = magnified ? selected.position - span / 2 : Math.floor(reading.origin) - 1.4;
  const pixelsPerMm = (width - 16) / span;
  const X = x => 8 + (x - start) * pixelsPerMm;
  const mid = height / 2;
  ctx.fillStyle = '#f4f7f7'; ctx.fillRect(0, 0, width, mid);
  ctx.fillStyle = '#e0eaeb'; ctx.fillRect(0, mid, width, height - mid);
  stroke(ctx, [0, mid], [width, mid], '#899da2', 1);
  ctx.textAlign = 'center';
  ctx.font = '13px system-ui, sans-serif';
  for (let mark = Math.max(0, Math.ceil(start - 1)); mark <= Math.min(58, start + span + 1); mark++) {
    const x = X(mark);
    stroke(ctx, [x, mid - (magnified || mark % 5 === 0 ? 21 : 14)], [x, mid], '#1f343d', 1.5);
    if (magnified || mark % 5 === 0) {
      ctx.fillStyle = '#1f343d'; ctx.fillText(String(mark), x, mid - 26);
    }
  }
  for (let i = 0; i <= reading.divisions; i++) {
    const x = X(reading.origin + reading.pitch * i);
    if (x < -10 || x > width + 10) continue;
    stroke(ctx, [x, mid], [x, mid + (magnified || i % 5 === 0 ? 21 : 14)], '#1f343d', 1.5);
    if (magnified || i % 5 === 0) { ctx.fillStyle = '#1f343d'; ctx.fillText(String(i), x, mid + 37); }
  }
  if (!magnified) {
    const x = X(selected.position);
    stroke(ctx, [x - 5, mid + 48], [x, mid + 42], '#974326', 2);
    stroke(ctx, [x, mid + 42], [x + 5, mid + 48], '#974326', 2);
  }
}
