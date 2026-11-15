/* Original coordinate artwork. Fixed real 2×2 lesson examples; no API or credit. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  let serial = 0;
  const fmt = n => n === 0 ? '0' : String(Number(n.toPrecision(6)));
  const vec = v => '(' + v.map(fmt).join(', ') + ')';
  const multiply = (a, v) => [a[0][0] * v[0] + a[0][1] * v[1], a[1][0] * v[0] + a[1][1] * v[1]];
  function nullBasis(a) {
    if (a.flat().every(x => x === 0)) return [[1, 0], [0, 1]];
    const row = Math.hypot(...a[0]) >= Math.hypot(...a[1]) ? a[0] : a[1];
    const size = Math.hypot(...row);
    const v = [-row[1] / size, row[0] / size];
    return [v.map(x => Object.is(x, -0) ? 0 : x)];
  }
  function analyze(matrix, angle = 45) {
    if (!Array.isArray(matrix) || matrix.length !== 2 || matrix.some(r => !Array.isArray(r) || r.length !== 2) ||
        !matrix.flat().every(Number.isFinite)) throw new TypeError('A finite real 2×2 matrix is required.');
    if (!Number.isFinite(angle) || angle < 0 || angle > 180) throw new RangeError('Angle must be in [0,180] degrees.');
    const [[a, b], [c, d]] = matrix;
    const trace = a + d, determinant = a * d - b * c;
    const discriminant = (a - d) ** 2 + 4 * b * c;
    const rank = determinant !== 0 ? 2 : matrix.flat().some(x => x !== 0) ? 1 : 0;
    const kernel = rank === 2 ? [] : nullBasis(matrix);
    const columns = [[a, c], [b, d]];
    const range = rank === 2 ? columns : rank === 1 ? [columns.find(v => v.some(x => x !== 0))] : [];
    const roots = discriminant < 0 ? [] : discriminant === 0 ? [trace / 2] :
      [(trace + Math.sqrt(discriminant)) / 2, (trace - Math.sqrt(discriminant)) / 2];
    const spaces = roots.map(value => {
      const basis = nullBasis([[a - value, b], [c, d - value]]);
      return { value, multiplicity: discriminant === 0 ? 2 : 1, basis, dimension: basis.length };
    });
    const cardinal = { 0: [1, 0], 90: [0, 1], 180: [-1, 0] };
    const v = cardinal[angle] || [Math.cos(angle * Math.PI / 180), Math.sin(angle * Math.PI / 180)];
    const image = multiply(matrix, v);
    const quotient = (v[0] * image[0] + v[1] * image[1]) / (v[0] ** 2 + v[1] ** 2);
    const parallel = v.map(x => quotient * x), residual = image.map((x, i) => x - parallel[i]);
    const residualNorm = Math.hypot(...residual);
    return { matrix, angle, trace, determinant, rank, kernel, range, spaces,
      diagonalizable: spaces.reduce((n, s) => n + s.dimension, 0) === 2,
      v, image, quotient, parallel, residual, residualNorm };
  }
  function element(tag, attrs = {}, ...children) {
    const e = document.createElement(tag);
    Object.entries(attrs).forEach(([key, value]) => e.setAttribute(key, String(value)));
    children.forEach(child => { if (child != null) e.append(child.nodeType ? child : document.createTextNode(String(child))); });
    return e;
  }
  function shape(tag, attrs, content) {
    const e = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([key, value]) => e.setAttribute(key, String(value)));
    if (content != null) e.textContent = String(content);
    return e;
  }
  function create() {
    const uid = 'eigen-space-' + ++serial;
    const root = element('section', { class: 'math-eigenspace', 'aria-labelledby': uid + '-title' });
    const output = element('output', { for: uid + '-angle' });
    const input = element('input', { type: 'range', id: uid + '-angle', min: 0, max: 180, step: 5, value: 45,
      'data-eigen-angle': 'true' });
    const svg = shape('svg', { viewBox: '0 0 440 400', class: 'math-eigen-svg', role: 'img',
      'aria-labelledby': uid + '-graph-title', 'aria-describedby': uid + '-graph-desc' });
    const viewport = element('div', { class: 'math-eigen-viewport', tabindex: 0, role: 'region',
      'aria-label': 'Eigenvector coordinate plot; enlarge and scroll for detail' }, svg);
    const table = element('table', { class: 'math-eigen-table' });
    const readout = element('p', { class: 'math-eigen-readout', 'data-model-speak': 'true' });
    const spacesNote = element('p', { class: 'math-eigen-spaces', 'data-model-speak': 'true' });
    const live = element('p', { role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    const enlarge = element('button', { class: 'btn ghost small', type: 'button', 'aria-pressed': 'false' }, 'Enlarge eigenvector plot');
    let matrix = [[1, 1], [0, 1]], angle = 45, label = 'Shear x by y', enlarged = false;
    root.append(element('div', { class: 'model-heading-row' }, element('h4', { id: uid + '-title' }, 'Eigenvectors, range and kernel'), enlarge),
      element('p', { 'data-model-speak': 'true' }, 'In this lower plot, rotate a separate nonzero unit vector v; the upper grid panels retain their fixed vector (1,1). An eigenvector satisfies Av = λv, including a reversed direction for λ < 0 and a zero image for λ = 0.'),
      element('label', { class: 'model-range-control', for: uid + '-angle' }, 'Probe vector angle', output, input),
      element('div', { class: 'model-button-row' }, ...[0, 45, 90].map(degrees => {
        const button = element('button', { type: 'button', class: 'btn ghost small', 'data-eigen-preset': degrees }, degrees + '°');
        button.addEventListener('click', () => { angle = degrees; refresh(true); });
        return button;
      })), viewport, readout, element('div', { class: 'math-eigen-table-scroll', tabindex: 0, role: 'region',
        'aria-label': 'Eigenvalues and bases' }, table), spacesNote,
      element('p', { class: 'spatial-note', 'data-model-speak': 'true' }, 'Solid blue: v; solid coral: Av; gold: the component qv parallel to v; dashed coral: the perpendicular residual r. The thin blue circle contains all unit vectors; the thin coral curve is its transformed image, collapsing to a line for projection. q = (v·Av)/(v·v) is a scalar projection, not automatically an eigenvalue. Dashed teal lines show one-dimensional eigenspaces; the identity has the entire plane as its eigenspace. Vectors and coordinates are dimensionless. This activity treats five fixed real 2×2 matrices, not general numerical eigensolvers or higher-dimensional vector spaces.'),
      element('p', { class: 'spatial-note' }, element('a', { href: 'https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/pages/least-squares-determinants-and-eigenvalues/eigenvalues-and-eigenvectors/', target: '_blank', rel: 'noopener noreferrer' }, 'MIT OpenCourseWare: eigenvalues and eigenvectors')), live);
    const X = x => 232 + 72 * x, Y = y => 195 - 72 * y;
    function segment(start, end, color, attrs = {}) {
      svg.append(shape('line', { x1: X(start[0]), y1: Y(start[1]), x2: X(end[0]), y2: Y(end[1]),
        stroke: color, 'stroke-width': 2.5, ...attrs }));
    }
    function arrow(start, end, color, role, dashed = false) {
      segment(start, end, color, { 'data-eigen-vector': role, ...(dashed ? { 'stroke-dasharray': '4 4' } : {}) });
      const dx = X(end[0]) - X(start[0]), dy = Y(end[1]) - Y(start[1]), n = Math.hypot(dx, dy);
      if (n > 1e-10) {
        const ux = dx / n, uy = dy / n, x = X(end[0]), y = Y(end[1]);
        svg.append(shape('polygon', { fill: color, points: [[x, y], [x - 9 * ux - 4 * uy, y - 9 * uy + 4 * ux],
          [x - 9 * ux + 4 * uy, y - 9 * uy - 4 * ux]].map(p => p.join(',')).join(' ') }));
      } else svg.append(shape('circle', { cx: X(end[0]), cy: Y(end[1]), r: 4, fill: color, 'data-eigen-zero-image': role }));
    }
    function refresh(announce) {
      const m = analyze(matrix, angle);
      input.value = String(angle); output.textContent = angle + '°'; input.setAttribute('aria-valuetext', angle + ' degrees');
      const spectrum = m.spaces.map(s => 'λ = ' + fmt(s.value) + ': multiplicity ' + s.multiplicity +
        ', eigenspace dimension ' + s.dimension).join('; ');
      readout.textContent = label + '. v = ' + vec(m.v) + '; Av = ' + vec(m.image) +
        '. q = ' + fmt(m.quotient) + '; r = Av − qv = ' + vec(m.residual) + '; |r| = ' + fmt(m.residualNorm) +
        '. An exact zero residual means this nonzero v is an eigenvector; nonzero residual means it is not. ' + spectrum + '.';
      spacesNote.textContent = 'Column-space basis: ' + (m.range.map(vec).join(', ') || 'empty basis for {0}') +
        '; dimension (rank) ' + m.rank + '. Kernel basis: ' + (m.kernel.map(vec).join(', ') || 'empty basis for {0}') +
        '; dimension ' + m.kernel.length + '. Rank + nullity = 2. ' + (m.diagonalizable ? 'Two independent eigenvectors form an eigenbasis.' :
          'This shear has a repeated eigenvalue but only one independent eigenvector; it has no eigenbasis.');
      table.replaceChildren(element('caption', {}, 'Exact eigenspaces of the selected matrix'),
        element('thead', {}, element('tr', {}, ...['Eigenvalue', 'Multiplicity', 'Eigenspace basis', 'Dimension'].map(t => element('th', { scope: 'col' }, t)))),
        element('tbody', {}, ...m.spaces.map(s => element('tr', {}, element('th', { scope: 'row' }, fmt(s.value)),
          element('td', {}, s.multiplicity), element('td', {}, s.basis.map(vec).join(', ')), element('td', {}, s.dimension)))));
      svg.replaceChildren(shape('title', { id: uid + '-graph-title' }, 'Vector and image in shared coordinates'),
        shape('desc', { id: uid + '-graph-desc' }, readout.textContent + ' ' + spacesNote.textContent),
        shape('rect', { x: 0, y: 0, width: 440, height: 400, rx: 10, fill: '#f5efdf' }));
      for (let n = -2; n <= 2; n++) {
        segment([n, -2.2], [n, 2.2], '#ddd6c7', { 'stroke-width': 1 });
        segment([-2.2, n], [2.2, n], '#ddd6c7', { 'stroke-width': 1 });
        svg.append(shape('text', { x: X(n), y: 373, 'text-anchor': 'middle', fill: '#263b46', 'font-size': 14 }, n),
          shape('text', { x: 56, y: Y(n) + 5, 'text-anchor': 'end', fill: '#263b46', 'font-size': 14 }, n));
      }
      segment([-2.2, 0], [2.2, 0], '#263b46', { 'stroke-width': 1.5 });
      segment([0, -2.2], [0, 2.2], '#263b46', { 'stroke-width': 1.5 });
      const circle = Array.from({ length: 121 }, (_, i) => {
        const a = i * Math.PI / 60, p = multiply(matrix, [Math.cos(a), Math.sin(a)]);
        return [X(p[0]), Y(p[1])].join(',');
      }).join(' ');
      svg.append(shape('circle', { cx: X(0), cy: Y(0), r: 72, fill: 'none', stroke: '#3e7085', 'stroke-width': 1 }),
        shape('polyline', { points: circle, fill: 'none', stroke: '#b96652', 'stroke-width': 1, 'data-eigen-circle-image': 'true' }));
      m.spaces.filter(s => s.dimension === 1).forEach(s => {
        const u = s.basis[0], length = 2.1 / Math.max(Math.abs(u[0]), Math.abs(u[1]));
        segment(u.map(x => -x * length), u.map(x => x * length), '#317e78', { 'stroke-dasharray': '5 5', 'data-eigen-line': fmt(s.value) });
      });
      arrow([0, 0], m.parallel, '#936915', 'projection');
      arrow(m.parallel, m.image, '#b96652', 'residual', true);
      arrow([0, 0], m.image, '#b96652', 'image');
      arrow([0, 0], m.v, '#3e7085', 'probe');
      svg.append(shape('text', { x: 232, y: 394, 'text-anchor': 'middle', fill: '#263b46', 'font-size': 14 }, 'x coordinate'),
        shape('text', { x: 17, y: 195, transform: 'rotate(-90 17 195)', 'text-anchor': 'middle', fill: '#263b46', 'font-size': 14 }, 'y coordinate'));
      if (announce) live.textContent = readout.textContent;
    }
    input.addEventListener('input', () => { angle = Number(input.value); refresh(false); });
    input.addEventListener('change', () => refresh(true));
    enlarge.addEventListener('click', () => {
      enlarged = !enlarged; root.classList.toggle('is-enlarged', enlarged);
      enlarge.setAttribute('aria-pressed', String(enlarged));
      enlarge.textContent = enlarged ? 'Fit eigenvector plot' : 'Enlarge eigenvector plot';
    });
    refresh(false);
    return Object.freeze({ element: root,
      setMatrix(next, name) { matrix = next; label = name; refresh(false); },
      reset() { angle = 45; refresh(false); live.textContent = 'Probe direction reset to 45 degrees.'; } });
  }
  window.PrimerMathEigenspace = Object.freeze({ analyze, multiply, create });
}());
