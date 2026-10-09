/* A double Riemann sum and the flux form of Green's theorem on the SAME
   explicit rectangle. All coordinates and field values are dimensionless.
   Uses PrimerSpatial.rotate only for the camera; no extra spatial scene or
   arbitrary surface is registered. Mathematical source: OpenStax Calculus 3,
   sections 5.1 and 6.4. The artwork and worked fields are original. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const C = Object.freeze({ ink: '#263b46', teal: '#317e78', coral: '#b96652', blue: '#3e7085',
    gold: '#b98a2f', plum: '#876888', paper: '#f5efdf', grid: '#d5cfbf' });
  const initial = Object.freeze({ field: 'quadratic', left: -1, width: 2, bottom: -1, height: 2,
    resolution: 4, portion: 100, method: 'midpoint', order: 'dxdy', orientation: 'outward', yaw: -30 });
  const controls = Object.freeze([
    { key: 'field', label: 'Linked integrand and field', options: [
      { value: 'quadratic', label: 'f = x² + 2y; F = (x³/3, y²)' },
      { value: 'linear', label: 'f = x + y; F = (x²/2, y²/2)' },
    ] },
    { key: 'left', label: 'Lower x bound a', min: -2, max: 1, step: .25 },
    { key: 'width', label: 'Rectangle width b − a', min: 0, max: 3, step: .25 },
    { key: 'bottom', label: 'Lower y bound c', min: -2, max: 1, step: .25 },
    { key: 'height', label: 'Rectangle height d − c', min: 0, max: 3, step: .25 },
    { key: 'resolution', label: 'Cells in each direction n', min: 1, max: 12, step: 1 },
    { key: 'portion', label: 'Accumulate from c toward d (%)', min: 0, max: 100, step: 5 },
    { key: 'method', label: 'Riemann sample in each cell', options: [
      { value: 'midpoint', label: 'Cell midpoint' }, { value: 'left', label: 'Lower left corner' },
    ] },
    { key: 'order', label: 'Order of exact integration', options: [
      { value: 'dxdy', label: 'Integrate x first, then y' }, { value: 'dydx', label: 'Integrate y first, then x' },
    ] },
    { key: 'orientation', label: 'Traversal and normal to its right', options: [
      { value: 'outward', label: 'Counterclockwise; outward normal' },
      { value: 'inward', label: 'Clockwise; inward normal' },
    ] },
    { key: 'yaw', label: 'Rotate the prism view (degrees)', min: -180, max: 180, step: 15 },
  ].map(control => Object.freeze({ ...control, options: control.options ? Object.freeze(control.options.map(Object.freeze)) : undefined })));
  let serial = 0;

  function normalize(raw) {
    const input = raw && typeof raw === 'object' ? raw : {};
    const state = {};
    for (const control of controls) {
      if (control.options) state[control.key] = control.options.some(o => o.value === input[control.key])
        ? input[control.key] : initial[control.key];
      else {
        const value = Number(input[control.key]);
        state[control.key] = input[control.key] == null || !Number.isFinite(value) ? initial[control.key]
          : Math.max(control.min, Math.min(control.max, value));
      }
    }
    state.resolution = Math.round(state.resolution);
    return state;
  }
  const format = value => value === 0 ? '0' : String(Number(value.toPrecision(6)));
  function fieldAt(kind, x, y) {
    if (![x, y].every(Number.isFinite)) throw new RangeError('Finite coordinates required.');
    if (kind === 'quadratic') return { p: x ** 3 / 3, q: y * y, f: x * x + 2 * y };
    if (kind === 'linear') return { p: x * x / 2, q: y * y / 2, f: x + y };
    throw new RangeError('Unknown field.');
  }
  function validateBounds(bounds) {
    if (!bounds || !['a', 'b', 'c', 'd'].every(key => Number.isFinite(bounds[key]))) throw new RangeError('Finite rectangle bounds required.');
    if (bounds.a > bounds.b || bounds.c > bounds.d) throw new RangeError('Geometric rectangle bounds must be ordered.');
  }
  function integral(kind, bounds) {
    validateBounds(bounds);
    const { a, b, c, d } = bounds;
    if (kind === 'quadratic') return (d - c) * (b ** 3 - a ** 3) / 3 + (b - a) * (d * d - c * c);
    if (kind === 'linear') return ((d - c) * (b * b - a * a) + (b - a) * (d * d - c * c)) / 2;
    throw new RangeError('Unknown field.');
  }
  function boundaryFlux(kind, bounds, orientation = 'outward') {
    validateBounds(bounds);
    if (!['outward', 'inward'].includes(orientation)) throw new RangeError('Unknown normal orientation.');
    const { a, b, c, d } = bounds, sign = orientation === 'outward' ? 1 : -1;
    // Independent boundary calculation: evaluate the appropriate normal field
    // component on each side, then multiply by that side's length. Do not use
    // the double integral as the flux result.
    const left = fieldAt(kind, a, (c + d) / 2), right = fieldAt(kind, b, (c + d) / 2);
    const bottom = fieldAt(kind, (a + b) / 2, c), top = fieldAt(kind, (a + b) / 2, d);
    const sides = [
      { id: 'bottom', label: 'Bottom y = c', start: [a, c], end: [b, c], normal: [0, -sign], flux: -sign * bottom.q * (b - a) },
      { id: 'right', label: 'Right x = b', start: [b, c], end: [b, d], normal: [sign, 0], flux: sign * right.p * (d - c) },
      { id: 'top', label: 'Top y = dₚ', start: [b, d], end: [a, d], normal: [0, sign], flux: sign * top.q * (b - a) },
      { id: 'left', label: 'Left x = a', start: [a, d], end: [a, c], normal: [-sign, 0], flux: -sign * left.p * (d - c) },
    ];
    if (sign < 0) sides.forEach(side => { [side.start, side.end] = [side.end, side.start]; });
    return { sides, total: sides.reduce((sum, side) => sum + side.flux, 0), sign };
  }
  function build(raw) {
    const state = normalize(raw), { left: a, bottom: c, width, height } = state;
    const b = a + width, fullD = c + height, d = c + height * state.portion / 100;
    const bounds = { a, b, c, d }, n = state.resolution, dx = width / n, dy = (d - c) / n;
    const area = width * (d - c), cells = [];
    const offset = state.method === 'midpoint' ? .5 : 0;
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
      const x0 = a + i * dx, y0 = c + j * dy;
      const x = x0 + offset * dx, y = y0 + offset * dy, value = fieldAt(state.field, x, y).f;
      cells.push({ i, j, x0, x1: x0 + dx, y0, y1: y0 + dy, x, y, height: value, area: dx * dy, contribution: value * dx * dy });
    }
    const sum = cells.reduce((value, cell) => value + cell.contribution, 0);
    const positive = cells.reduce((value, cell) => value + Math.max(0, cell.contribution), 0);
    const negative = cells.reduce((value, cell) => value + Math.min(0, cell.contribution), 0);
    const exact = integral(state.field, bounds), flux = boundaryFlux(state.field, bounds, state.orientation);
    const accumulation = Array.from({ length: 81 }, (_, i) => {
      const y = c + height * i / 80;
      return { y, value: integral(state.field, { a, b, c, d: y }) };
    });
    const sliceIntegral = state.field === 'quadratic' ? (b ** 3 - a ** 3) / 3 + 2 * width * d
      : (b * b - a * a) / 2 + width * d;
    const degenerate = width === 0 || d === c;
    const fText = state.field === 'quadratic' ? 'x² + 2y' : 'x + y';
    const fieldText = state.field === 'quadratic' ? '(x³/3, y²)' : '(x²/2, y²/2)';
    let iterated;
    if (state.order === 'dxdy') iterated = state.field === 'quadratic'
      ? 'Integrate x first: ∫cᵈᵖ [(b³−a³)/3 + 2(b−a)y] dy.'
      : 'Integrate x first: ∫cᵈᵖ [(b²−a²)/2 + (b−a)y] dy.';
    else iterated = state.field === 'quadratic'
      ? 'Integrate y first: ∫aᵇ [(dₚ−c)x² + dₚ²−c²] dx.'
      : 'Integrate y first: ∫aᵇ [(dₚ−c)x + (dₚ²−c²)/2] dx.';
    const readout = 'Dₚ = [' + format(a) + ', ' + format(b) + '] × [' + format(c) + ', ' + format(d) +
      '], area ' + format(area) + '. f = div F = ' + fText + '; F = ' + fieldText + '. ' +
      n + ' × ' + n + ' cells: Δx = ' + format(dx) + ', Δy = ' + format(dy) +
      '. Signed Riemann sum = ' + format(positive) + ' + (' + format(negative) + ') = ' + format(sum) +
      '; exact double integral = ' + format(exact) + '; exact minus sum = ' + format(exact - sum) + '. ' + iterated +
      ' Boundary flux with ' + state.orientation + ' normals = ' + format(flux.total) +
      (state.orientation === 'outward' ? ' = ∫∫Dₚ div F dA.' : ' = −∫∫Dₚ div F dA.') +
      ' G(u) = ∫∫[a,b]×[c,u] f dA; G′(dₚ) = ' + format(sliceIntegral) +
      '. ' + (degenerate ? 'The region has no enclosed area. The zero integral follows from coincident bounds; Green’s theorem is not claimed for this collapsed boundary.' :
        'Green’s flux theorem applies to this closed rectangle and smooth polynomial field.');
    return { state, bounds, fullD, area, dx, dy, cells, sum, positive, negative, exact,
      error: exact - sum, flux, accumulation, sliceIntegral, degenerate, fText, fieldText, iterated, readout };
  }

  function element(tag, attributes = {}, ...children) {
    const el = document.createElement(tag);
    Object.entries(attributes).forEach(([key, value]) => el.setAttribute(key, String(value)));
    children.forEach(child => { if (child != null) el.append(child.nodeType ? child : document.createTextNode(String(child))); });
    return el;
  }
  function svgElement(tag, attributes = {}, text) {
    const el = document.createElementNS(NS, tag);
    Object.entries(attributes).forEach(([key, value]) => el.setAttribute(key, String(value)));
    if (text != null) el.textContent = String(text);
    return el;
  }
  function line(svg, points, color, width = 1.5, attrs = {}) {
    svg.append(svgElement('polyline', { points: points.map(point => point.join(',')).join(' '), fill: 'none',
      stroke: color, 'stroke-width': width, 'vector-effect': 'non-scaling-stroke', ...attrs }));
  }
  function label(svg, x, y, value, attrs = {}) {
    svg.append(svgElement('text', { x, y, fill: C.ink, 'font-size': 15, ...attrs }, value));
  }
  function arrow(svg, start, end, color, attrs = {}) {
    const dx = end[0] - start[0], dy = end[1] - start[1], norm = Math.hypot(dx, dy);
    if (norm < 1e-10) return;
    const ux = dx / norm, uy = dy / norm, head = Math.min(5, norm / 3);
    line(svg, [start, end], color, 1.5, attrs);
    line(svg, [[end[0] - head * ux - head * .6 * uy, end[1] - head * uy + head * .6 * ux], end,
      [end[0] - head * ux + head * .6 * uy, end[1] - head * uy - head * .6 * ux]], color);
  }

  function render(item, hooks) {
    if (item?.props?.scenario !== 'math.4.multivar.integral-flux' || !window.PrimerSpatial?.rotate) return null;
    const uid = 'math-field-' + ++serial;
    const title = item.title || 'Accumulate an integral and measure boundary flux';
    const instructions = item.instructions || 'Change the rectangle and cell size. Move the accumulation boundary, then compare the exact double integral with flux through all four sides.';
    const root = element('section', { class: 'card lesson-model math-field-lab', 'data-renderer': 'math-field-lab',
      'aria-labelledby': uid + '-title', 'aria-describedby': uid + '-instructions' });
    const heading = element('div', { class: 'model-heading-row' }, element('h3', { id: uid + '-title' }, title));
    const equation = element('p', { class: 'math-field-equation' });
    const controlArea = element('div', { class: 'model-controls concept-controls' });
    const pictures = [], panels = element('div', { class: 'math-field-panels' });
    ['Signed Riemann prisms', 'The vector field and boundary normals', 'Exact accumulation G(u)'].forEach((title, index) => {
      const viewport = element('div', { class: 'math-field-viewport', tabindex: '0', role: 'region', 'aria-label': title + '; enlarge for fine detail' });
      const picture = svgElement('svg', { viewBox: '0 0 440 360', role: 'img', focusable: 'false',
        'aria-labelledby': uid + '-plot-title-' + index, 'aria-describedby': uid + '-plot-desc-' + index });
      viewport.append(picture); panels.append(viewport); pictures.push(picture);
    });
    const summary = element('div', { class: 'math-field-summary' });
    const ledger = element('table', { class: 'math-field-ledger' });
    const readout = element('p', { class: 'model-readout' });
    const status = element('p', { class: 'model-status', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    const note = element('p', { class: 'spatial-note' },
      'All coordinates, field components and integrals are dimensionless mathematical quantities. Each prism contributes f(sample)ΔxΔy; teal is positive and coral is negative. ' +
      'Negative terms are subtracted, so this is signed accumulation, not always ordinary volume. The continuous wire surface is sampled separately from the flat Riemann boxes. ' +
      'The prism height axis is scaled separately for visibility; do not measure slopes or angles from perspective. The field arrows have a shared display multiplier and show vectors, not particle paths; a dot represents a zero vector with no direction. ' +
      'Gold normals lie to the right of the shown traversal: counterclockwise gives outward normals; clockwise gives inward normals. Reversing a parametrization while keeping the physical outward normal fixed does not reverse outward flux. ' +
      'This is the two-dimensional flux form of Green’s theorem, not circulation or a three-dimensional surface integral. The fields are smooth everywhere and the nondegenerate domain is a simply connected rectangle. ' +
      'The G curve samples 81 exact accumulated values; its marked value and derivative use the exact formulas. Changing integration order keeps the same region. General nonrectangular regions require rewriting the limits; they are not simulated here.');
    const sources = element('p', { class: 'spatial-note' },
      element('a', { href: 'https://openstax.org/books/calculus-volume-3/pages/5-1-double-integrals-over-rectangular-regions', target: '_blank', rel: 'noopener noreferrer' }, 'OpenStax: double integrals'), ' · ',
      element('a', { href: 'https://openstax.org/books/calculus-volume-3/pages/6-4-greens-theorem', target: '_blank', rel: 'noopener noreferrer' }, 'OpenStax: Green’s flux theorem'));
    let model = build(initial), enlarged = false;
    const widgets = new Map();
    for (const control of controls) {
      const id = uid + '-' + control.key, output = control.options ? null : element('output', { for: id });
      const input = control.options ? element('select', { id, 'data-field-control': control.key }) :
        element('input', { type: 'range', id, min: control.min, max: control.max, step: control.step, 'data-field-control': control.key });
      control.options?.forEach(option => input.append(element('option', { value: option.value }, option.label)));
      input.addEventListener(control.options ? 'change' : 'input', () => {
        model = build({ ...model.state, [control.key]: input.value }); refresh(Boolean(control.options));
      });
      if (!control.options) input.addEventListener('change', () => refresh(true));
      widgets.set(control.key, { control, input, output });
      controlArea.append(element('label', { class: 'model-range-control', for: id }, control.label, output, input));
    }
    const enlarge = element('button', { type: 'button', class: 'btn ghost small', 'aria-pressed': 'false', 'data-field-action': 'enlarge' }, 'Enlarge diagrams');
    enlarge.addEventListener('click', () => {
      enlarged = !enlarged; root.classList.toggle('is-enlarged', enlarged);
      enlarge.setAttribute('aria-pressed', String(enlarged)); enlarge.textContent = enlarged ? 'Fit diagrams' : 'Enlarge diagrams';
    });
    const reset = element('button', { type: 'button', class: 'btn ghost small', 'data-field-action': 'reset' }, 'Reset');
    reset.addEventListener('click', () => { model = build(initial); refresh(false); status.textContent = 'Rectangle, field, resolution and orientation reset.'; });
    const unit = element('button', { type: 'button', class: 'btn ghost small', 'data-field-action': 'unit-square' }, 'Unit-square example');
    unit.addEventListener('click', () => {
      model = build({ ...initial, field: 'linear', left: 0, width: 1, bottom: 0, height: 1 }); refresh(true);
    });
    heading.append(enlarge);
    root.append(heading, element('p', { id: uid + '-instructions', class: 'model-instructions' }, instructions), equation,
      element('div', { class: 'model-button-row' }, unit, reset), controlArea, summary, panels, ledger, readout, note, sources, status);
    if (hooks && typeof hooks.speakButton === 'function') heading.prepend(hooks.speakButton(() =>
      title + '. ' + instructions + '. ' + readout.textContent + '. ' + note.textContent, 'Read this activity aloud'));

    function startPicture(index, title, desc) {
      const svg = pictures[index];
      svg.replaceChildren(svgElement('title', { id: uid + '-plot-title-' + index }, title),
        svgElement('desc', { id: uid + '-plot-desc-' + index }, desc));
      label(svg, 22, 25, title, { 'font-size': 18, 'font-weight': 600 });
      return svg;
    }
    function drawPrisms() {
      const svg = startPicture(0, 'Signed Riemann prisms', model.readout);
      const { a, b, c, d } = model.bounds;
      const fieldValues = [a, b, Math.max(a, Math.min(b, 0))].flatMap(x => [c, d].map(y => fieldAt(model.state.field, x, y).f));
      const maxF = Math.max(1, ...fieldValues.map(Math.abs)), zScale = 1.6 / maxF;
      const cx = (a + b) / 2, cy = (c + d) / 2, camera = { yaw: model.state.yaw, pitch: 24 };
      const rotate = point => window.PrimerSpatial.rotate([point[0] - cx, point[2] * zScale, -(point[1] - cy)], camera);
      const world = [[a, c, 0], [b, c, 0], [b, d, 0], [a, d, 0], ...fieldValues.map(z => [a, c, z])].map(rotate);
      const extent = Math.max(1.4, ...world.map(p => Math.hypot(p[0], p[1])));
      const scale = 132 / extent;
      const project = point => { const p = rotate(point); return [220 + scale * p[0], 180 - scale * p[1], p[2]]; };
      const faces = [];
      if (!model.degenerate) for (const cell of model.cells) {
        if (cell.height === 0) continue;
        const lo = Math.min(0, cell.height), hi = Math.max(0, cell.height);
        const p = [[cell.x0, cell.y0, lo], [cell.x1, cell.y0, lo], [cell.x1, cell.y1, lo], [cell.x0, cell.y1, lo],
          [cell.x0, cell.y0, hi], [cell.x1, cell.y0, hi], [cell.x1, cell.y1, hi], [cell.x0, cell.y1, hi]].map(project);
        [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [3, 7, 6, 2], [0, 4, 7, 3], [1, 2, 6, 5]].forEach((ids, face) => {
          const points = ids.map(i => p[i]);
          faces.push({ points, depth: points.reduce((v, p) => v + p[2], 0) / 4, cell, face });
        });
      }
      faces.sort((left, right) => left.depth - right.depth).forEach(face => svg.append(svgElement('polygon', {
        points: face.points.map(p => p.slice(0, 2).join(',')).join(' '), fill: face.cell.height > 0 ? C.teal : C.coral,
        'fill-opacity': .45, stroke: C.ink, 'stroke-width': .5, 'data-field-cell': face.cell.i + ',' + face.cell.j,
        'data-field-height': face.cell.height, 'data-field-area': face.cell.area, 'data-field-face': face.face,
      })));
      line(svg, [[a, c, 0], [b, c, 0], [b, d, 0], [a, d, 0], [a, c, 0]].map(project).map(p => p.slice(0, 2)), C.ink, 2);
      if (!model.degenerate) {
        // A wire surface from the true polynomial, not a smoothed box mesh.
        for (let i = 0; i <= 8; i++) {
          const x = a + (b - a) * i / 8, y = c + (d - c) * i / 8;
          const alongY = [], alongX = [];
          for (let j = 0; j <= 24; j++) {
            const yy = c + (d - c) * j / 24, xx = a + (b - a) * j / 24;
            alongY.push(project([x, yy, fieldAt(model.state.field, x, yy).f]).slice(0, 2));
            alongX.push(project([xx, y, fieldAt(model.state.field, xx, y).f]).slice(0, 2));
          }
          line(svg, alongY, C.plum, .7, { opacity: .65 }); line(svg, alongX, C.plum, .7, { opacity: .65 });
        }
      }
      const xp = project([b, c, 0]), yp = project([a, d, 0]);
      svg.append(svgElement('rect', { x: xp[0] + 4, y: xp[1] + 2, width: 18, height: 20, rx: 3, fill: C.paper, opacity: .9 }),
        svgElement('rect', { x: yp[0] - 15, y: yp[1] + 2, width: 18, height: 20, rx: 3, fill: C.paper, opacity: .9 }));
      label(svg, xp[0] + 7, xp[1] + 16, 'x', { 'font-weight': 600 });
      label(svg, yp[0] - 12, yp[1] + 16, 'y', { 'font-weight': 600 });
      const base = project([a, c, 0]), top = project([a, c, maxF]);
      arrow(svg, base.slice(0, 2), top.slice(0, 2), C.ink);
      label(svg, top[0] + 4, top[1] - 5, 'f = ' + format(maxF));
      label(svg, 22, 332, 'Teal + · coral − · plum: sampled f surface', { 'font-size': 14 });
      label(svg, 22, 352, model.degenerate ? 'Zero enclosed area; no prisms.' :
        'Height scale: ' + format(zScale) + ' per unit of f', { 'font-size': 14 });
    }
    function drawFlux() {
      const svg = startPicture(1, 'Field and oriented boundary', model.readout);
      const { a, b, c, d } = model.bounds, allD = model.fullD;
      const spanX = Math.max(1, b - a), spanY = Math.max(1, allD - c), scale = Math.min(258 / spanX, 218 / spanY);
      const X = x => 220 + (x - (a + b) / 2) * scale, Y = y => 174 - (y - (c + allD) / 2) * scale;
      line(svg, [[X(a), Y(c)], [X(b), Y(c)], [X(b), Y(allD)], [X(a), Y(allD)], [X(a), Y(c)]], C.grid, 1.5, { 'stroke-dasharray': '4 4' });
      svg.append(svgElement('rect', { x: X(a), y: Y(d), width: (b - a) * scale, height: (d - c) * scale,
        fill: C.gold, 'fill-opacity': .08, stroke: C.ink, 'stroke-width': 2, 'data-field-domain': 'true' }));
      const arrows = [];
      if (!model.degenerate) for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) {
        const x = a + (b - a) * (i + .5) / 5, y = c + (d - c) * (j + .5) / 5;
        arrows.push({ x, y, ...fieldAt(model.state.field, x, y) });
      }
      const maxVector = Math.max(1e-12, ...arrows.map(p => Math.hypot(p.p, p.q)));
      const vectorScale = Math.min(19, Math.max(3, Math.min(b - a, d - c) * scale / 7)) / maxVector;
      for (const point of arrows) {
        const attrs = { 'data-field-vector': 'true', 'data-field-x': point.x, 'data-field-y': point.y,
          'data-field-p': point.p, 'data-field-q': point.q };
        if (point.p === 0 && point.q === 0) svg.append(svgElement('circle', {
          cx: X(point.x), cy: Y(point.y), r: 2, fill: C.blue, ...attrs,
        }));
        else arrow(svg, [X(point.x), Y(point.y)],
          [X(point.x) + point.p * vectorScale, Y(point.y) - point.q * vectorScale], C.blue, attrs);
      }
      if (!model.degenerate) for (const side of model.flux.sides) {
        const mid = side.start.map((value, i) => (value + side.end[i]) / 2);
        arrow(svg, [X(mid[0]), Y(mid[1])], [X(mid[0]) + side.normal[0] * 22, Y(mid[1]) - side.normal[1] * 22], C.gold,
          { 'data-field-normal': side.id, 'data-field-nx': side.normal[0], 'data-field-ny': side.normal[1] });
        const along = side.end.map((value, i) => value - side.start[i]);
        const len = Math.hypot(...along), tx = along[0] / len, ty = along[1] / len;
        arrow(svg, [X(mid[0]) - tx * 13, Y(mid[1]) + ty * 13], [X(mid[0]) + tx * 13, Y(mid[1]) - ty * 13], C.coral,
          { 'data-field-tangent': side.id, 'data-field-tx': tx, 'data-field-ty': ty });
      }
      label(svg, X(a), Y(c) + 28, (a === b ? 'a = b = ' : 'a = ') + format(a), { 'text-anchor': 'middle', 'font-size': 13 });
      if (a !== b) label(svg, X(b), Y(c) + 28, 'b = ' + format(b), { 'text-anchor': 'middle', 'font-size': 13 });
      label(svg, X(a) - (c === d ? 14 : 28), Y(c), (c === d ? 'c=dₚ=' : 'c=') + format(c), { 'text-anchor': 'end', 'font-size': 13 });
      if (c !== d) label(svg, X(a) - 28, Y(d), 'dₚ=' + format(d), { 'text-anchor': 'end', 'font-size': 13 });
      label(svg, 22, 332, 'Blue F · gold normal · coral traversal', { 'font-size': 14 });
      label(svg, 22, 352, model.degenerate ? 'Collapsed boundary: theorem not applied.' :
        '∮ (P dy − Q dx) = ' + format(model.flux.total), { 'font-size': 15 });
    }
    function drawAccumulation() {
      const svg = startPicture(2, 'Exact accumulation G(u)', model.readout);
      const { c, d } = model.bounds, xmax = model.fullD > c ? model.fullD : c + 1;
      if (model.state.height === 0) {
        label(svg, 30, 140, 'Final upper bound d equals c = ' + format(c) + '.');
        label(svg, 30, 174, 'Only G(c) = 0 is selected; no y interval.', { 'font-size': 16 });
        svg.append(svgElement('circle', { cx: 220, cy: 224, r: 5, fill: C.coral, stroke: C.ink,
          'data-field-accumulation-point': 'true', 'data-field-upper-y': d, 'data-field-exact': model.exact }));
        return;
      }
      const values = model.accumulation.map(p => p.value), low = Math.min(0, ...values), high = Math.max(0, ...values);
      const desired = Math.max(.25, (high - low) / 4), base = 10 ** Math.floor(Math.log10(desired));
      const step = [1, 2, 2.5, 5, 10].map(factor => factor * base).find(value => value >= desired);
      const tickLow = Math.floor(low / step) * step, tickHigh = Math.max(tickLow + step, Math.ceil(high / step) * step);
      const ymin = tickLow - step * .12, ymax = tickHigh + step * .12;
      const X = x => 68 + 344 * (x - c) / (xmax - c), Y = y => 269 - 218 * (y - ymin) / (ymax - ymin);
      for (let i = 0; i <= 4; i++) {
        const x = c + (xmax - c) * i / 4;
        line(svg, [[X(x), 51], [X(x), 269]], C.grid, 1);
        label(svg, X(x), 291, format(x), { 'text-anchor': 'middle', 'font-size': 13 });
      }
      for (let y = tickLow; y <= tickHigh + step * 1e-8; y += step) {
        line(svg, [[68, Y(y)], [412, Y(y)]], C.grid, 1);
        label(svg, 59, Y(y) + 5, String(Number(y.toPrecision(3))), { 'text-anchor': 'end', 'font-size': 13 });
      }
      line(svg, [[68, Y(0)], [412, Y(0)]], C.ink, 1.5);
      line(svg, model.accumulation.map(p => [X(p.y), Y(p.value)]), C.teal, 2.5);
      line(svg, [[X(d), 51], [X(d), 269]], C.coral, 1.5, { 'stroke-dasharray': '3 3' });
      svg.append(svgElement('circle', { cx: X(d), cy: Y(model.exact), r: 5, fill: C.coral, stroke: C.ink,
        'data-field-accumulation-point': 'true', 'data-field-upper-y': d, 'data-field-exact': model.exact }));
      label(svg, 240, 319, 'Upper y bound u (dimensionless)', { 'text-anchor': 'middle' });
      label(svg, 18, 160, 'G(u)', { transform: 'rotate(-90 18 160)', 'text-anchor': 'middle' });
      label(svg, 22, 352, 'G′(dₚ) = ∫aᵇ f(x,dₚ) dx = ' + format(model.sliceIntegral), { 'font-size': 15 });
    }
    function refresh(announce) {
      const s = model.state;
      root.setAttribute('data-field-exact', String(model.exact));
      root.setAttribute('data-field-sum', String(model.sum));
      root.setAttribute('data-field-flux', String(model.flux.total));
      root.setAttribute('data-field-degenerate', String(model.degenerate));
      equation.textContent = 'f = div F = ' + model.fText + '; F = ' + model.fieldText +
        '. Dₚ = [' + format(model.bounds.a) + ', ' + format(model.bounds.b) + '] × [' + format(model.bounds.c) + ', ' +
        format(model.bounds.d) + ']. Final upper bound d = ' + format(model.fullD) + '.';
      widgets.forEach(({ control, input, output }) => {
        input.value = String(s[control.key]);
        if (output) {
          output.textContent = format(s[control.key]); input.setAttribute('aria-valuetext', output.textContent);
        }
      });
      summary.replaceChildren(...[['Riemann sum', model.sum], ['Exact integral', model.exact],
        [s.orientation + ' flux', model.flux.total]].map(([name, value]) => element('p', {},
        element('small', {}, name), element('strong', {}, format(value)))));
      ledger.replaceChildren(element('caption', {}, 'Four boundary contributions (' + s.orientation + ' normals)'),
        element('thead', {}, element('tr', {}, element('th', { scope: 'col' }, 'Side'),
          element('th', { scope: 'col' }, 'Unit normal'), element('th', { scope: 'col' }, 'Exact flux'))),
        element('tbody', {}, ...model.flux.sides.map(side => element('tr', { 'data-field-side': side.id },
          element('th', { scope: 'row' }, side.label), element('td', {}, '(' + side.normal.join(', ') + ')'),
          element('td', {}, format(side.flux))))));
      drawPrisms(); drawFlux(); drawAccumulation(); readout.textContent = model.readout;
      if (announce) status.textContent = 'Exact signed integral ' + format(model.exact) + '; Riemann sum ' +
        format(model.sum) + '; ' + s.orientation + ' flux ' + format(model.flux.total) +
        (model.degenerate ? '. No enclosed area.' : '.');
    }
    refresh(false);
    return root;
  }
  window.PrimerMathFieldLab = Object.freeze({ controls, initial, normalize, fieldAt, integral, boundaryFlux, build, render });
}());
