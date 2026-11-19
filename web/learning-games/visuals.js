/* Drawn explanations for learning sequences.

   Every visual here is authored as a line of text ("tree 60(6(2,3),10(2,5))")
   and drawn by the book itself, in the reader's own theme: nothing is an
   image file, nothing is borrowed.  Each drawing carries a text description
   for a reader who cannot see it, and none relies on colour alone.  */
(function (scope) {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';

  function node(tag, attrs, ...kids) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null) continue;
      if (k === 'class') e.className = v; else e.setAttribute(k, v);
    }
    for (const kid of kids) if (kid != null) e.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    return e;
  }
  function svg(tag, attrs, ...kids) {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) if (v != null) e.setAttribute(k, v);
    for (const kid of kids) if (kid != null) e.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    return e;
  }
  function frame(width, height, label) {
    return svg('svg', { viewBox: '0 0 ' + width + ' ' + height, class: 'lg-svg', role: 'img', 'aria-label': label,
      preserveAspectRatio: 'xMidYMid meet', style: 'max-width:' + width + 'px' });
  }
  const text = (x, y, value, extra) => svg('text', Object.assign({ x, y, 'text-anchor': 'middle', class: 'lg-svg-text' }, extra), value);

  /* ---- arithmetic language (display only; the server re-computes) ---- */
  const FUNCTIONS = { sqrt: Math.sqrt, abs: Math.abs, min: Math.min, max: Math.max, round: Math.round,
    floor: Math.floor, ceil: Math.ceil, sin: Math.sin, cos: Math.cos, tan: Math.tan, log: Math.log,
    log10: Math.log10, exp: Math.exp };
  const CONSTANTS = { pi: Math.PI, e: Math.E };
  function tokenize(source) {
    const out = [], re = /\s*(\d+\.?\d*|\.\d+|[A-Za-z_][A-Za-z_0-9]*|\*\*|\/\/|<=|>=|==|!=|[-+*/%^()<>,])/y;
    const clean = String(source).replace(/×|·/g, '*').replace(/÷/g, '/').replace(/−/g, '-')
      .replace(/≤/g, '<=').replace(/≥/g, '>=').replace(/≠/g, '!=');
    let at = 0;
    while (at < clean.length) {
      if (/^\s*$/.test(clean.slice(at))) break;
      re.lastIndex = at;
      const match = re.exec(clean);
      if (!match) throw new Error('Unreadable expression');
      out.push(match[1]); at = re.lastIndex;
    }
    return out;
  }
  function evaluate(source, variables) {
    const tokens = tokenize(source), vars = Object.assign({}, CONSTANTS, variables || {});
    let at = 0;
    const peek = () => tokens[at], take = () => tokens[at++];
    const close = (a, b) => Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(a), Math.abs(b));
    function or() { let v = and(); while (peek() === 'or') { take(); const r = and(); v = v || r; } return v; }
    function and() { let v = not(); while (peek() === 'and') { take(); const r = not(); v = v && r; } return v; }
    function not() { if (peek() === 'not') { take(); return !not(); } return comparison(); }
    function comparison() {
      let left = sum(), result = null;
      while (['<', '>', '<=', '>=', '==', '!='].includes(peek())) {
        const op = take(), right = sum();
        const ok = op === '==' ? close(left, right) : op === '!=' ? !close(left, right)
          : op === '<' ? left < right && !close(left, right) : op === '>' ? left > right && !close(left, right)
          : op === '<=' ? left < right || close(left, right) : left > right || close(left, right);
        result = (result === null ? true : result) && ok; left = right;
      }
      return result === null ? left : result;
    }
    function sum() { let v = product(); while (peek() === '+' || peek() === '-') { const op = take(), r = product(); v = op === '+' ? v + r : v - r; } return v; }
    function product() {
      let v = unary();
      while (['*', '/', '%', '//'].includes(peek())) {
        const op = take(), r = unary();
        v = op === '*' ? v * r : op === '/' ? v / r : op === '//' ? Math.floor(v / r) : v - r * Math.floor(v / r);
      }
      return v;
    }
    function unary() { if (peek() === '-') { take(); return -unary(); } if (peek() === '+') { take(); return unary(); } return power(); }
    function power() { const base = atom(); if (peek() === '^' || peek() === '**') { take(); return Math.pow(base, unary()); } return base; }
    function atom() {
      const token = take();
      if (token === undefined) throw new Error('Unfinished expression');
      if (token === '(') { const v = or(); if (take() !== ')') throw new Error('Missing bracket'); return v; }
      if (/^[\d.]/.test(token)) return Number(token);
      if (Object.hasOwn(FUNCTIONS, token) && peek() === '(') {
        take(); const args = [];
        if (peek() !== ')') { args.push(or()); while (peek() === ',') { take(); args.push(or()); } }
        if (take() !== ')') throw new Error('Missing bracket');
        return FUNCTIONS[token](...args);
      }
      if (Object.hasOwn(vars, token)) return vars[token];
      throw new Error('Unknown name ' + token);
    }
    const value = or();
    if (at !== tokens.length) throw new Error('Unreadable expression');
    return value;
  }
  function shown(value) {
    if (typeof value === 'boolean') return value ? 'yes' : 'no';
    if (!Number.isFinite(value)) return '—';
    return String(Number(Number(value).toPrecision(6)));
  }

  /* ---------------------------------------------------------- drawings */
  function digits(v) {
    const chars = v.value.split(''), n = chars.length, last = v.last || 0, hide = v.hide || 0, marks = v.mark || [];
    const row = node('div', { class: 'lg-digits', role: 'img',
      'aria-label': 'The number ' + chars.map(c => c === '?' ? 'hidden digit' : c).join(' ')
        + (last ? '. The last ' + (last === 1 ? 'digit is' : last + ' digits are') + ' marked.' : '') });
    chars.forEach((c, i) => {
      const fromRight = n - i, hidden = c === '?' || i < hide;
      const cell = node('span', { class: 'lg-digit' + (fromRight <= last ? ' lg-digit-key' : '')
        + (hidden ? ' lg-digit-hidden' : '') + (marks.includes(fromRight) ? ' lg-digit-mark' : ''), 'aria-hidden': 'true' },
        hidden ? '' : c);
      if ((n - i) % 3 === 0 && i > 0) cell.classList.add('lg-digit-gap');
      row.append(cell);
    });
    if (last) row.append(node('span', { class: 'lg-digits-note', 'aria-hidden': 'true' },
      last === 1 ? 'last digit' : 'last ' + last + ' digits'));
    return row;
  }
  function isPrime(n) { if (n < 2) return false; for (let d = 2; d * d <= n; d++) if (n % d === 0) return false; return true; }
  function tree(v) {
    const leaves = [];
    let depth = 0;
    (function measure(n, d) { depth = Math.max(depth, d); n.d = d; if (n.kids) n.kids.forEach(k => measure(k, d + 1)); else leaves.push(n); })(v.root, 0);
    const gap = 62, level = 62, width = Math.max(leaves.length * gap + 20, 140), height = depth * level + 62;
    leaves.forEach((leaf, i) => { leaf.x = (i + 0.5) * (width / leaves.length); });
    (function place(n) { if (n.kids) { n.kids.forEach(place); n.x = (n.kids[0].x + n.kids[1].x) / 2; } n.y = 30 + n.d * level; })(v.root);
    const described = [];
    (function say(n) {
      if (n.kids) { described.push((n.v === '?' ? 'a hidden number' : n.v) + ' splits into ' + n.kids.map(k => k.v === '?' ? 'a hidden number' : k.v).join(' and ')); n.kids.forEach(say); }
    })(v.root);
    const out = frame(width, height, 'Factor tree. ' + (described.join('; ') || 'A single number: ' + v.root.v) + '. Squares are primes; circles can still be split.');
    (function lines(n) { if (!n.kids) return; n.kids.forEach(k => { out.append(svg('line', { x1: n.x, y1: n.y + 18, x2: k.x, y2: k.y - 18, class: 'lg-svg-line' })); lines(k); }); })(v.root);
    (function draw(n) {
      const hidden = n.v === '?', prime = !hidden && !n.kids && isPrime(Number(n.v));
      // Two shapes, not two colours: a prime leaf is a square, anything that
      // can still be split is a circle, and a hidden node is dashed.
      out.append(prime
        ? svg('rect', { x: n.x - 19, y: n.y - 19, width: 38, height: 38, rx: 4, class: 'lg-svg-prime' })
        : svg('circle', { cx: n.x, cy: n.y, r: 20, class: 'lg-svg-node' + (hidden ? ' lg-svg-hidden' : '') }));
      out.append(text(n.x, n.y + 5, hidden ? '?' : n.v, { class: 'lg-svg-text' + (prime ? ' lg-svg-text-strong' : '') }));
      if (n.kids) n.kids.forEach(draw);
    })(v.root);
    return out;
  }
  function cycle(v) {
    const n = v.values.length, long = v.values.some(x => x.length > 2), r = long ? 86 : 64, c = r + 46;
    const out = frame(c * 2, c * 2, 'A repeating cycle: ' + v.values.join(', then ') + ', then back to ' + v.values[0] + '.');
    out.append(svg('circle', { cx: c, cy: c, r, class: 'lg-svg-ring' }));
    v.values.forEach((value, i) => {
      const a = -Math.PI / 2 + i * 2 * Math.PI / n, x = c + r * Math.cos(a), y = c + r * Math.sin(a);
      const w = long ? Math.max(40, value.length * 8 + 14) : 34;
      out.append(svg('rect', { x: x - w / 2, y: y - 15, width: w, height: 30, rx: 15, class: 'lg-svg-node' + (i === 0 ? ' lg-svg-start' : '') }));
      out.append(text(x, y + 5, value, { class: 'lg-svg-text' + (long ? ' lg-svg-small' : '') }));
      const mid = a + Math.PI / n, ax = c + (r - 0) * Math.cos(mid), ay = c + r * Math.sin(mid);
      out.append(svg('path', { d: 'M -5 -4 L 4 0 L -5 4 Z', transform: 'translate(' + ax + ' ' + ay + ') rotate(' + ((mid + Math.PI / 2) * 180 / Math.PI) + ')', class: 'lg-svg-arrow' }));
    });
    out.append(text(c, c + 4, 'repeats', { class: 'lg-svg-text lg-svg-small lg-svg-muted' }));
    return out;
  }
  function dots(v) {
    const total = v.count || v.rows * v.cols, group = v.group || v.cols || 10, perRow = v.rows ? v.cols : group;
    const rows = Math.ceil(total / perRow), full = Math.floor(total / perRow), over = total - full * perRow;
    const out = frame(perRow * 22 + 16, rows * 22 + 12, v.rows
      ? total + ' dots in ' + v.rows + ' rows of ' + v.cols + '.'
      : total + ' dots' + (v.group ? ' in groups of ' + v.group + ': ' + full + ' full ' + (full === 1 ? 'group' : 'groups') + ' and ' + over + ' left over.' : '.'));
    for (let i = 0; i < total; i++) {
      const r = Math.floor(i / perRow), c = i % perRow, spare = v.group && r === full;
      out.append(svg('circle', { cx: 19 + c * 22, cy: 17 + r * 22, r: 7.5, class: spare ? 'lg-svg-spare' : 'lg-svg-dot' }));
    }
    if (v.group) for (let r = 0; r < full; r++) out.append(svg('rect', { x: 8, y: 6 + r * 22, width: perRow * 22, height: 22, rx: 11, class: 'lg-svg-band' }));
    return out;
  }
  function numberLine(v) {
    const width = 520, pad = 28, y = 46, X = value => pad + (value - v.min) * (width - 2 * pad) / (v.max - v.min);
    const span = v.max - v.min, step = v.step || (span <= 12 ? 1 : span <= 24 ? 2 : span <= 60 ? 5 : span <= 120 ? 10 : Math.pow(10, Math.floor(Math.log10(span))) / 2);
    const marks = v.mark || [], hops = v.hops || [];
    const out = frame(width, 84, 'A number line from ' + v.min + ' to ' + v.max
      + (marks.length ? ', with ' + marks.join(' and ') + ' marked' : '') + (hops.length ? ', and a jump from ' + hops.map(h => h[0] + ' to ' + h[1]).join(', then ') : '') + '.');
    out.append(svg('line', { x1: pad - 10, y1: y, x2: width - pad + 10, y2: y, class: 'lg-svg-line' }));
    for (let value = v.min; value <= v.max + 1e-9; value += step) {
      out.append(svg('line', { x1: X(value), y1: y - 6, x2: X(value), y2: y + 6, class: 'lg-svg-line' }));
      out.append(text(X(value), y + 24, shown(value), { class: 'lg-svg-text lg-svg-small' }));
    }
    hops.forEach(([from, to]) => {
      const a = X(from), b = X(to), mid = (a + b) / 2, lift = Math.min(30, Math.abs(b - a) / 2 + 8);
      out.append(svg('path', { d: 'M ' + a + ' ' + (y - 8) + ' Q ' + mid + ' ' + (y - 8 - lift * 1.6) + ' ' + b + ' ' + (y - 8), class: 'lg-svg-hop' }));
      out.append(svg('path', { d: 'M -5 -6 L 0 2 L 5 -6 Z', transform: 'translate(' + b + ' ' + (y - 8) + ')', class: 'lg-svg-arrow' }));
    });
    marks.forEach(value => out.append(svg('circle', { cx: X(value), cy: y, r: 6.5, class: 'lg-svg-mark' })));
    return out;
  }
  function bars(v, current) {
    const list = v.bars, max = Math.max(...list.map(b => Math.abs(b.value)), 1e-9), slot = Math.min(72, 460 / list.length), width = list.length * slot + 30, base = 132;
    const out = frame(width, 168, 'Bar chart. ' + list.map(b => b.label + ': ' + shown(b.value) + (v.unit ? ' ' + v.unit : '')).join('; ') + '.');
    out.append(svg('line', { x1: 12, y1: base, x2: width - 12, y2: base, class: 'lg-svg-line' }));
    // Narrow slots cannot hold every label: write every few, and always the
    // current one. The chart's own description still lists every value.
    const every = slot < 40 ? Math.ceil(40 / slot) : 1;
    list.forEach((b, i) => {
      const h = Math.max(2, 108 * Math.abs(b.value) / max), x = 20 + i * slot, w = Math.max(8, slot - 14);
      const labelled = current === i || (i % every === 0 && (current == null || Math.abs(i - current) >= every));
      out.append(svg('rect', { x, y: base - h, width: w, height: h, rx: 2, class: 'lg-svg-bar' + (current === i ? ' lg-svg-bar-now' : '') }));
      if (!labelled) return;
      out.append(text(x + w / 2, base - h - 6, shown(b.value), { class: 'lg-svg-text lg-svg-small' }));
      out.append(text(x + w / 2, base + 18, b.label, { class: 'lg-svg-text lg-svg-small' + (current === i ? ' lg-svg-text-strong' : '') }));
    });
    return out;
  }
  function table(v) {
    const t = node('table', { class: 'lg-table' });
    t.append(node('thead', {}, node('tr', {}, ...v.head.map(cell => node('th', { scope: 'col' }, cell)))));
    t.append(node('tbody', {}, ...v.rows.map(row => node('tr', {}, ...row.map((cell, i) => node(i ? 'td' : 'th', i ? {} : { scope: 'row' }, cell))))));
    return node('div', { class: 'lg-table-wrap' }, t);
  }
  const steps = v => node('ol', { class: 'lg-steps' }, ...v.items.map(item => node('li', {}, item)));
  const chips = v => node('ul', { class: 'lg-chips' }, ...v.items.map(item => node('li', {}, item)));
  function flow(v) {
    const list = node('ol', { class: 'lg-flow' });
    v.items.forEach((item, i) => {
      list.append(node('li', {}, item));
      if (i < v.items.length - 1) list.append(node('li', { class: 'lg-flow-arrow', 'aria-hidden': 'true' }, '→'));
    });
    return list;
  }
  function timeline(v) {
    return node('ol', { class: 'lg-time' }, ...v.events.map(e => node('li', {}, node('b', {}, e.at), node('span', {}, e.label))));
  }
  function fractions(v) {
    const width = v.parts.length * 150, out = frame(width, 118, v.parts.map(p => p[0] + ' out of ' + p[1] + ' equal parts shaded').join('; ') + '.');
    v.parts.forEach(([top, bottom], i) => {
      const x = 14 + i * 150, w = 122, cell = w / bottom;
      for (let k = 0; k < bottom; k++) out.append(svg('rect', { x: x + k * cell, y: 20, width: cell, height: 46, class: k < top ? 'lg-svg-fill' : 'lg-svg-empty' }));
      out.append(text(x + w / 2, 96, top + '/' + bottom, { class: 'lg-svg-text' }));
    });
    return out;
  }
  function plot(v, mark) {
    const W = 460, H = 240, box = { l: 44, r: W - 14, t: 14, b: H - 34 }, pts = [];
    // An exploration passes a function; an authored plot passes an expression in x.
    const at = v.fn || (x => evaluate(v.expr, { x }));
    for (let i = 0; i <= 120; i++) {
      const x = v.x[0] + (v.x[1] - v.x[0]) * i / 120;
      let y; try { y = at(x); } catch (e) { y = NaN; }
      if (Number.isFinite(y)) pts.push([x, y]);
    }
    const ys = pts.map(p => p[1]), lo = Math.min(0, ...ys), hi = Math.max(0, ...ys, lo + 1e-9);
    const X = x => box.l + (x - v.x[0]) * (box.r - box.l) / (v.x[1] - v.x[0]), Y = y => box.b - (y - lo) * (box.b - box.t) / (hi - lo);
    const out = frame(W, H, 'Graph of ' + (v.label || v.expr) + ' for ' + (v.variable || 'x') + ' from ' + v.x[0] + ' to ' + v.x[1]
      + '. It runs from ' + shown(ys[0]) + ' to ' + shown(ys[ys.length - 1]) + '.');
    out.append(svg('line', { x1: box.l, y1: Y(0), x2: box.r, y2: Y(0), class: 'lg-svg-line' }));
    out.append(svg('line', { x1: box.l, y1: box.t, x2: box.l, y2: box.b, class: 'lg-svg-line' }));
    [v.x[0], (v.x[0] + v.x[1]) / 2, v.x[1]].forEach(x => out.append(text(X(x), box.b + 20, shown(x), { class: 'lg-svg-text lg-svg-small' })));
    [lo, hi].forEach(y => out.append(text(box.l - 6, Y(y) + 4, shown(y), { class: 'lg-svg-text lg-svg-small', 'text-anchor': 'end' })));
    if (pts.length) out.append(svg('path', { d: pts.map((p, i) => (i ? 'L ' : 'M ') + X(p[0]).toFixed(1) + ' ' + Y(p[1]).toFixed(1)).join(' '), class: 'lg-svg-curve' }));
    (v.mark || []).concat(mark == null ? [] : [mark]).forEach(x => {
      let y; try { y = at(x); } catch (e) { return; }
      if (Number.isFinite(y)) out.append(svg('circle', { cx: X(x), cy: Y(y), r: 6, class: 'lg-svg-mark' }));
    });
    return out;
  }
  function balance(v) {
    const out = frame(420, 150, 'A balance. Left pan: ' + v.left + '. Right pan: ' + v.right + '. The pans are level.');
    out.append(svg('path', { d: 'M 210 34 L 196 128 L 224 128 Z', class: 'lg-svg-node' }));
    out.append(svg('line', { x1: 60, y1: 40, x2: 360, y2: 40, class: 'lg-svg-line lg-svg-thick' }));
    [[60, v.left], [360, v.right]].forEach(([x, label]) => {
      out.append(svg('line', { x1: x, y1: 40, x2: x, y2: 70, class: 'lg-svg-line' }));
      out.append(svg('rect', { x: x - 54, y: 70, width: 108, height: 36, rx: 6, class: 'lg-svg-node' }));
      out.append(text(x, 94, label, { class: 'lg-svg-text' }));
    });
    return out;
  }
  function grid(v) {
    const cell = Math.min(34, 300 / Math.max(v.rows, v.cols)), on = new Set(v.on);
    const out = frame(v.cols * cell + 8, v.rows * cell + 8, 'A grid of ' + v.rows + ' rows and ' + v.cols + ' columns with '
      + v.on.length + (v.on.length === 1 ? ' square' : ' squares') + ' filled' + (v.on.length ? ': ' + v.on.join(', ') + ', counting along the rows.' : '.'));
    for (let r = 0; r < v.rows; r++) for (let c = 0; c < v.cols; c++) {
      const filled = on.has(r * v.cols + c + 1);
      out.append(svg('rect', { x: 4 + c * cell, y: 4 + r * cell, width: cell, height: cell, class: filled ? 'lg-svg-fill' : 'lg-svg-empty' }));
      if (filled) out.append(svg('path', { d: 'M ' + (4 + c * cell + 4) + ' ' + (4 + r * cell + 4) + ' l ' + (cell - 8) + ' ' + (cell - 8), class: 'lg-svg-hatch' }));
    }
    return out;
  }
  function clock(v) {
    const out = frame(170, 170, 'A clock showing ' + v.hour + ':' + String(v.minute).padStart(2, '0') + '.'), c = 85;
    out.append(svg('circle', { cx: c, cy: c, r: 74, class: 'lg-svg-node' }));
    for (let h = 1; h <= 12; h++) {
      const a = h * Math.PI / 6 - Math.PI / 2;
      out.append(text(c + 58 * Math.cos(a), c + 58 * Math.sin(a) + 5, h, { class: 'lg-svg-text lg-svg-small' }));
    }
    const minute = v.minute * Math.PI / 30 - Math.PI / 2, hour = ((v.hour % 12) + v.minute / 60) * Math.PI / 6 - Math.PI / 2;
    out.append(svg('line', { x1: c, y1: c, x2: c + 34 * Math.cos(hour), y2: c + 34 * Math.sin(hour), class: 'lg-svg-line lg-svg-thick' }));
    out.append(svg('line', { x1: c, y1: c, x2: c + 50 * Math.cos(minute), y2: c + 50 * Math.sin(minute), class: 'lg-svg-line' }));
    out.append(svg('circle', { cx: c, cy: c, r: 4, class: 'lg-svg-mark' }));
    return out;
  }
  const SHAPES = {
    circle: () => svg('circle', { cx: 30, cy: 30, r: 24 }),
    oval: () => svg('ellipse', { cx: 30, cy: 30, rx: 27, ry: 17 }),
    square: () => svg('rect', { x: 8, y: 8, width: 44, height: 44 }),
    rectangle: () => svg('rect', { x: 3, y: 14, width: 54, height: 32 }),
    triangle: () => svg('polygon', { points: '30,6 56,52 4,52' }),
    diamond: () => svg('polygon', { points: '30,4 54,30 30,56 6,30' }),
    pentagon: () => svg('polygon', { points: '30,5 55,23 46,53 14,53 5,23' }),
    hexagon: () => svg('polygon', { points: '17,7 43,7 56,30 43,53 17,53 4,30' }),
    star: () => svg('polygon', { points: '30,4 37,22 56,23 41,35 46,54 30,43 14,54 19,35 4,23 23,22' }),
  };
  function shapes(v) {
    const out = frame(v.items.length * 70 + 6, 66, 'Shapes in a row: ' + v.items.join(', ') + '.');
    v.items.forEach((name, i) => {
      const shape = SHAPES[name]();
      shape.setAttribute('class', 'lg-svg-node');
      out.append(svg('g', { transform: 'translate(' + (6 + i * 70) + ' 3)' }, shape));
    });
    return out;
  }

  function draw(visual, context) {
    if (!visual) return null;
    const v = visual, ctx = context || {};
    switch (v.kind) {
      case 'art': return ctx.art ? ctx.art() : null;
      case 'text': return node('p', { class: 'lg-callout' }, v.text);
      case 'emoji': return node('p', { class: 'lg-emoji', role: 'img', 'aria-label': ctx.emojiLabel || 'Pictures: ' + v.text }, v.text);
      case 'pair': return node('div', { class: 'lg-pair' }, ...v.items.map(item => node('div', { class: 'lg-pair-side' }, draw(item, ctx))));
      case 'digits': return digits(v);
      case 'tree': return tree(JSON.parse(JSON.stringify(v)));
      case 'cycle': return cycle(v);
      case 'dots': return dots(v);
      case 'line': return numberLine(v);
      case 'bars': return bars(v);
      case 'table': return table(v);
      case 'steps': return steps(v);
      case 'chips': return chips(v);
      case 'flow': return flow(v);
      case 'time': return timeline(v);
      case 'frac': return fractions(v);
      case 'plot': return plot(v);
      case 'balance': return balance(v);
      case 'grid': return grid(v);
      case 'clock': return clock(v);
      case 'shapes': return shapes(v);
      default: return null;
    }
  }
  const api = Object.freeze({ draw, evaluate, shown, bars, plot, node });
  scope.PrimerLearningVisuals = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
