/* Original analytic measure/convergence artwork. No sampled pixels determine an integral. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg', MAX_N = 65536;
  const C = Object.freeze({ ink: '#263b46', paper: '#f5efdf', grid: '#d5cfbf', teal: '#317e78', blue: '#3e7085', coral: '#b96652', gold: '#9e741c' });
  const initial = Object.freeze({ n: 4, amplitude: 2, alpha: '1', numerator: 1, denominator: 4, zoom: true });
  const controls = Object.freeze([
    { key: 'alpha', label: 'Exponent α (held fixed as n grows)', options: [
      { value: '0', label: '0: fixed height' }, { value: '0.5', label: '1/2: square-root height' }, { value: '1', label: '1: height proportional to n' },
    ] },
    { key: 'n', label: 'Sequence index n', type: 'number', min: 1, max: MAX_N, step: 1 },
    { key: 'amplitude', label: 'Amplitude A (held fixed as n grows)', min: 0, max: 8, step: .25 },
    { key: 'numerator', label: 'Fixed probe numerator a (0 ≤ a ≤ b)', type: 'number', min: 0, max: MAX_N, step: 1 },
    { key: 'denominator', label: 'Fixed probe denominator b', type: 'number', min: 1, max: MAX_N, step: 1 },
    { key: 'zoom', label: 'Zoom the support-detail plot', type: 'toggle' },
  ].map(c => Object.freeze({ ...c, options: c.options ? Object.freeze(c.options.map(Object.freeze)) : undefined })));
  let serial = 0;
  function normalize(raw) {
    const input = raw && typeof raw === 'object' ? raw : {}, state = {};
    for (const c of controls) {
      const value = Number(input[c.key]);
      if (c.options) state[c.key] = c.options.some(o => o.value === String(input[c.key])) ? String(input[c.key]) : initial[c.key];
      else if (c.type === 'toggle') state[c.key] = typeof input[c.key] === 'boolean' ? input[c.key] : initial[c.key];
      else state[c.key] = input[c.key] == null || !Number.isFinite(value) ? initial[c.key] :
        c.min + Math.round((Math.max(c.min, Math.min(c.max, value)) - c.min) / c.step) * c.step;
    }
    state.numerator = Math.min(state.numerator, state.denominator);
    return state;
  }
  const format = value => value === 0 ? '0' : String(Number(value.toPrecision(6)));
  const tick = value => value !== 0 && Math.abs(value) < .001 ? value.toExponential(2) : format(value);
  function rational(a, b) {
    if (!Number.isSafeInteger(a) || !Number.isSafeInteger(b) || b < 1 || b > MAX_N || a < 0 || a > b)
      throw new RangeError('A unit-interval rational a/b with integers 0 ≤ a ≤ b ≤ 65536 is required.');
  }
  function probeInside(n, a, b) {
    rational(a, b);
    if (!Number.isInteger(n) || n < 1 || n > MAX_N) throw new RangeError('Integer n in [1,65536] required.');
    // Products are integer-exact within the exposed domain; equality is outside.
    return a > 0 && n * a < b;
  }
  function envelopeAt(a, b, amplitude, alpha = '1') {
    rational(a, b);
    if (!Number.isFinite(amplitude) || amplitude < 0) throw new RangeError('Finite nonnegative amplitude required.');
    if (!['0', '0.5', '1'].includes(String(alpha))) throw new RangeError('Exponent must be 0, 1/2 or 1.');
    const maximumIndex = a === 0 ? 0 : Math.floor((b + a - 1) / a) - 1;
    return maximumIndex === 0 ? 0 : amplitude * maximumIndex ** Number(alpha);
  }
  function quantities(n, amplitude, alpha) {
    const exponent = Number(alpha), height = amplitude * n ** exponent;
    return { n, height, intervalMeasure: 1 / n, nonzeroMeasure: amplitude === 0 ? 0 : 1 / n,
      integral: amplitude * n ** (exponent - 1), norm1: amplitude * n ** (exponent - 1),
      norm2Squared: amplitude ** 2 * n ** (2 * exponent - 1), norm2: amplitude * n ** (exponent - .5), supNorm: height };
  }
  function build(raw) {
    const state = normalize(raw), { n, amplitude: A, alpha, numerator: a, denominator: b } = state;
    const q = quantities(n, A, alpha), exponent = Number(alpha), zero = A === 0;
    const inside = probeInside(n, a, b), zeroFrom = a === 0 ? 1 : Math.floor((b + a - 1) / a);
    const probe = { a, b, x: a / b, inside, value: inside ? q.height : 0, zeroFrom,
      envelope: envelopeAt(a, b, A, alpha), dominator: zero || a === 0 ? 0 : alpha === '0' ? A : alpha === '0.5' ? A * Math.sqrt(b / a) : null };
    const convergence = { pointwise: true, almostEverywhere: true, l1: zero || exponent < 1,
      l2: zero || exponent < .5, uniform: zero, dominated: zero || exponent < 1 };
    const dominatorIntegral = zero ? 0 : alpha === '0' ? A : alpha === '0.5' ? 2 * A : null;
    const proof = zero ? 'A = 0: every hₙ is identically zero. All norms vanish; uniform convergence and dominated convergence hold with dominator g = 0.' :
      alpha === '0' ? 'For fixed A > 0, g(x) = A is a common integrable dominator, with ∫g dx = A. The exact L¹ and L² norms tend to zero, but the essential supremum stays A, so convergence is not uniform.' :
      alpha === '0.5' ? 'For fixed A > 0, g(x) = A/√x for x > 0, with g(0) = 0, dominates every hₙ and has integral 2A. Growing peaks therefore do not prevent dominated convergence. L¹ tends to zero, but the L² norm stays A and the supremum grows.' :
        'For fixed A > 0, the common envelope on 0 < x ≤ 1 is supₙ hₙ(x) = A(ceil(1/x) − 1), and it is at least A/(2x) on 0 < x ≤ 1/2. Its integral diverges, so no common integrable dominator exists. The integral stays A despite pointwise convergence to zero. The countably many domination exceptions can be combined into one null set if domination is stated almost everywhere.';
    const pointwise = 'At every fixed x > 0, n ≥ ceil(1/x) excludes x from the open interval; at x = 0 every hₙ is already zero. Thus hₙ → 0 everywhere, hence almost everywhere. This is an analytic statement about all n, not a conclusion proved by the finite plot. At finite n and A > 0, hₙ differs from zero on a set of positive measure; it is not the zero Lᵖ equivalence class.';
    const series = [...new Set([...Array.from({ length: 17 }, (_, k) => 2 ** k), n])].sort((x, y) => x - y).map(k => quantities(k, A, alpha));
    const readout = 'Lebesgue measure dx on [0,1]; all quantities are dimensionless. Fixed A = ' + format(A) + ', α = ' + (alpha === '0.5' ? '1/2' : alpha) +
      '. hₙ(x) = A n^α on the open interval (0,1/n), zero elsewhere. At n = ' + n + ', interval measure = 1/' + n +
      ', height = ' + format(q.height) + ', integral and L¹ norm = ' + format(q.integral) + ', squared L² norm = ' + format(q.norm2Squared) +
      ', L² norm = ' + format(q.norm2) + ', essential supremum = ' + format(q.supNorm) + '.' +
      (zero ? ' The interval remains defined, but the nonzero set is empty.' : '') +
      ' At fixed rational x = ' + a + '/' + b + ', hₙ(x) = ' + format(probe.value) + '; ' +
      (a === 0 ? 'the endpoint is always zero.' : 'every n ≥ ' + zeroFrom + ' gives zero at this same probe.') + ' ' + proof;
    return { state, ...q, probe, convergence, dominatorIntegral, series, proof, pointwise, readout };
  }
  function element(tag, attrs = {}, ...children) {
    const el = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, String(v)));
    children.forEach(child => { if (child != null) el.append(child.nodeType ? child : document.createTextNode(String(child))); });
    return el;
  }
  function shape(tag, attrs = {}, text) {
    const el = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, String(v)));
    if (text != null) el.textContent = String(text);
    return el;
  }
  function label(svg, x, y, text, attrs = {}) { svg.append(shape('text', { x, y, fill: C.ink, 'font-size': 13, ...attrs }, text)); }
  function line(svg, points, color, attrs = {}) { svg.append(shape('polyline', { points: points.map(p => p.join(',')).join(' '), fill: 'none', stroke: color, 'stroke-width': 2, 'vector-effect': 'non-scaling-stroke', ...attrs })); }
  function render(item, hooks) {
    if (item?.props?.scenario !== 'math.5.measure.integration-norms' || (item.renderer && item.renderer !== 'math-measure-lab')) return null;
    const uid = 'measure-lab-' + ++serial;
    const title = item.title || 'Shrinking support: pointwise limits, integrals and norms';
    const instructions = item.instructions || 'Hold the amplitude, exponent and rational probe fixed while increasing n. Compare exact mass with pointwise values, then inspect the hypotheses of dominated convergence.';
    const root = element('section', { class: 'card lesson-model math-measure-lab', 'data-renderer': 'math-measure-lab', 'aria-labelledby': uid + '-title', 'aria-describedby': uid + '-instructions' });
    const heading = element('div', { class: 'model-heading-row' }, element('h3', { id: uid + '-title' }, title));
    const area = element('div', { class: 'model-controls concept-controls' }), widgets = new Map();
    const summary = element('div', { class: 'math-measure-summary' }), probe = element('p', { class: 'math-measure-probe' });
    const panels = element('div', { class: 'math-measure-panels' }), pictures = [];
    ['Function on the unit interval', 'Support detail', 'Accumulated Lebesgue integral', 'Norms as n grows'].forEach((name, i) => {
      const viewport = element('div', { class: 'math-measure-viewport', role: 'region', tabindex: '0', 'aria-label': name + '; enlarge for detail' });
      const svg = shape('svg', { viewBox: '0 0 460 350', role: 'img', focusable: 'false', 'aria-labelledby': uid + '-plot-title-' + i, 'aria-describedby': uid + '-plot-desc-' + i });
      viewport.append(svg); panels.append(viewport); pictures.push(svg);
    });
    const ledger = element('table', { class: 'math-measure-ledger' }), proof = element('p', { class: 'math-measure-proof' });
    const readout = element('p', { class: 'model-readout' }), pointwise = element('p', { class: 'spatial-note' });
    const note = element('p', { class: 'spatial-note' }, 'The graph uses analytic interval endpoints, not a sampled grid. Open circles mark excluded endpoint values; dashed vertical lines locate jumps and are not part of the function. Endpoint changes do not change a Lebesgue integral. A very thin support can be smaller than a pixel; zoom changes the labeled x-axis, while exact mass stays in the readout. Vertical axes rescale to the selected height or mass; compare their tick labels. The norm plot divides by A when A > 0 and uses base-two logarithmic axes. Its formulas describe all integer n; this display stops at 65,536. Changing A, α or the probe changes the example; sequence-limit statements keep those choices fixed. Decimal evaluations are rounded, while the stated formulas are exact.');
    const sources = element('p', { class: 'math-measure-sources' }, 'Primary references: ',
      element('a', { href: 'https://ocw.mit.edu/courses/18-125-measure-and-integration-fall-2003/1473498db368e7a3194855b6935cc616_18125_lec5.pdf', target: '_blank', rel: 'noopener noreferrer' }, 'MIT: dominated convergence and almost-everywhere equality'), ' · ',
      element('a', { href: 'https://ocw.mit.edu/courses/18-125-measure-and-integration-fall-2003/0c85400465928cf42a19e5b87bdc349c_18125_lec15.pdf', target: '_blank', rel: 'noopener noreferrer' }, 'MIT: Lᵖ norms'));
    const status = element('p', { class: 'model-status', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    let model = build(initial), enlarged = false;
    for (const c of controls) {
      const id = uid + '-' + c.key, input = element(c.options ? 'select' : 'input', { id, 'data-measure-control': c.key });
      let output;
      if (c.options) c.options.forEach(o => input.append(element('option', { value: o.value }, o.label)));
      else if (c.type === 'toggle') input.setAttribute('type', 'checkbox');
      else {
        input.setAttribute('type', c.type || 'range');
        for (const key of ['min', 'max', 'step']) input.setAttribute(key, c[key]);
        output = element('output', { for: id });
      }
      input.addEventListener(c.options || c.type === 'toggle' ? 'change' : 'input', () => {
        // A number field can be empty between native keystrokes. Replacing
        // that draft with its normalized value would append the next digit
        // to a fallback (for example, clearing 4 then typing 3 became 13).
        if (c.type === 'number' && input.value === '') return;
        model = build({ ...model.state, [c.key]: c.type === 'toggle' ? input.checked : input.value });
        refresh(Boolean(c.options || c.type === 'toggle'), c.type === 'number' ? c.key : undefined);
      });
      if (!c.options && c.type !== 'toggle') input.addEventListener('change', () => {
        if (c.type === 'number') model = build({ ...model.state, [c.key]: input.value });
        refresh(true);
      });
      widgets.set(c.key, { input, output, c });
      area.append(element('label', { for: id, class: 'model-range-control' }, c.label, output, input));
    }
    const buttons = element('div', { class: 'model-button-row' });
    [1, 4, 16, 256, MAX_N].forEach(n => {
      const button = element('button', { type: 'button', class: 'btn ghost small', 'data-measure-n': n }, 'n = ' + n);
      button.addEventListener('click', () => { model = build({ ...model.state, n }); refresh(true); }); buttons.append(button);
    });
    const enlarge = element('button', { type: 'button', class: 'btn ghost small', 'aria-pressed': 'false', 'data-measure-action': 'enlarge' }, 'Enlarge plots');
    function size(next) { enlarged = next; root.classList.toggle('is-enlarged', enlarged); enlarge.setAttribute('aria-pressed', String(enlarged)); enlarge.textContent = enlarged ? 'Fit plots' : 'Enlarge plots'; }
    enlarge.addEventListener('click', () => size(!enlarged)); heading.append(enlarge);
    const reset = element('button', { type: 'button', class: 'btn ghost small', 'data-measure-action': 'reset' }, 'Reset activity');
    reset.addEventListener('click', () => { model = build(initial); size(false); refresh(false); status.textContent = 'Initial sequence, fixed probe and plot sizes restored.'; }); buttons.append(reset);
    root.append(heading, element('p', { id: uid + '-instructions', class: 'model-instructions' }, instructions), buttons, area,
      summary, probe, panels, ledger, proof, readout, pointwise, note, sources, status);
    if (hooks && typeof hooks.speakButton === 'function') heading.prepend(hooks.speakButton(() =>
      title + '. ' + instructions + '. ' + readout.textContent + '. ' + pointwise.textContent + '. ' + note.textContent, 'Read this activity aloud'));
    function setup(i, name, xMax, yMax, xName, yName) {
      const svg = pictures[i], X = x => 80 + 350 * x / xMax, Y = y => 252 - 180 * y / yMax;
      svg.replaceChildren(shape('title', { id: uid + '-plot-title-' + i }, name), shape('desc', { id: uid + '-plot-desc-' + i }, model.readout),
        shape('rect', { x: 0, y: 0, width: 460, height: 350, rx: 10, fill: C.paper }));
      label(svg, 18, 28, name, { 'font-size': 17, 'font-weight': 600 });
      for (let j = 0; j <= 4; j++) {
        const x = j * xMax / 4, y = j * yMax / 4;
        line(svg, [[X(x), 72], [X(x), 252]], C.grid, { 'stroke-width': 1 });
        line(svg, [[80, Y(y)], [430, Y(y)]], C.grid, { 'stroke-width': 1 });
        label(svg, X(x), 275, tick(x), { 'text-anchor': j === 0 ? 'start' : j === 4 ? 'end' : 'middle', 'font-size': 11 });
        label(svg, 72, Y(y) + 4, tick(y), { 'text-anchor': 'end', 'font-size': 11 });
      }
      label(svg, 255, 299, xName, { 'text-anchor': 'middle' });
      label(svg, 18, 54, yName, { 'font-size': 12 });
      svg.setAttribute('data-measure-x-max', xMax); svg.setAttribute('data-measure-y-max', yMax);
      return { svg, X, Y };
    }
    function functionPlot(i, xMax, name) {
      const { n, amplitude: A } = model.state, h = model.height, p = setup(i, name, xMax, Math.max(1, h) * 1.15, 'x (dimensionless; read zoom scale)', 'hₙ(x); height axis rescales');
      const right = 1 / n, width = p.X(right) - p.X(0);
      p.svg.append(shape('rect', { x: p.X(0), y: p.Y(h), width, height: p.Y(0) - p.Y(h), fill: C.teal, 'fill-opacity': .2,
        'data-measure-support': i, 'data-measure-height': h, 'data-measure-integral': model.integral }));
      line(p.svg, [[p.X(0), p.Y(h)], [p.X(right), p.Y(h)]], C.teal, { 'data-measure-top': i });
      line(p.svg, [[p.X(right), p.Y(0)], [p.X(xMax), p.Y(0)]], C.ink);
      if (h > 0 && width > 14) {
        for (const x of [0, right]) {
          line(p.svg, [[p.X(x), p.Y(0)], [p.X(x), p.Y(h)]], C.teal, { 'stroke-width': 1, 'stroke-dasharray': '3 3' });
          p.svg.append(shape('circle', { cx: p.X(x), cy: p.Y(h), r: 4, fill: C.paper, stroke: C.teal, 'stroke-width': 2, 'data-measure-open-endpoint': x === 0 ? 'left' : 'right' }));
          p.svg.append(shape('circle', { cx: p.X(x), cy: p.Y(0), r: 3, fill: C.ink, 'data-measure-closed-endpoint': x === 0 ? 'left' : 'right' }));
        }
      }
      if (model.probe.x <= xMax) p.svg.append(shape('circle', { cx: p.X(model.probe.x), cy: p.Y(model.probe.value), r: 4, fill: C.coral,
        'data-measure-probe': i, 'data-measure-probe-value': model.probe.value }));
      label(p.svg, 18, 324, A === 0 ? 'A = 0: nonzero set empty; graph is zero.' : width < 1 ? 'Support is subpixel here; exact mass retained.' : width <= 14 ? 'Endpoint detail needs the support zoom.' : 'Open top endpoints; filled zero endpoints.', { 'font-size': 12 });
      label(p.svg, 18, 342, 'Interval (0, 1/' + n + '); exact mass A n^(α−1).', { 'font-size': 12 });
    }
    function draw() {
      functionPlot(0, 1, 'Function on the unit interval');
      functionPlot(1, model.state.zoom ? Math.min(1, 2 / model.state.n) : 1, model.state.zoom ? 'Support detail: zoomed x-axis' : 'Support detail: full x-axis');
      const accumulation = setup(2, 'Accumulated Lebesgue integral', 1, model.integral === 0 ? 1 : model.integral * 1.15, 'Upper integration bound t ∈ [0,1]', 'Hₙ(t) = ∫₀ᵗ hₙ(x) dx; mass axis rescales');
      line(accumulation.svg, [[accumulation.X(0), accumulation.Y(0)], [accumulation.X(1 / model.state.n), accumulation.Y(model.integral)],
        [accumulation.X(1), accumulation.Y(model.integral)]], C.blue, { 'data-measure-accumulation': 'exact' });
      label(accumulation.svg, 18, 324, 'Hₙ(t) = A n^α min(t, 1/n), for t ∈ [0,1].', { 'font-size': 12 });
      label(accumulation.svg, 18, 342, 'Hₙ(1) is the exact mass; endpoints add none.', { 'font-size': 12 });
      const svg = pictures[3];
      svg.replaceChildren(shape('title', { id: uid + '-plot-title-3' }, 'Norms as n grows'), shape('desc', { id: uid + '-plot-desc-3' }, model.readout),
        shape('rect', { x: 0, y: 0, width: 460, height: 350, rx: 10, fill: C.paper }));
      label(svg, 18, 28, 'Norms as n grows: fixed A and α', { 'font-size': 17, 'font-weight': 600 });
      if (model.state.amplitude === 0) {
        label(svg, 28, 105, 'A = 0: every norm is exactly zero.');
        label(svg, 28, 141, 'Norm/A and log₂(0) are undefined.');
        label(svg, 28, 177, 'No zero value is placed on a logarithmic axis.');
        return;
      }
      const X = n => 80 + 350 * Math.log2(n) / 16, Y = exponent => 252 - 180 * (exponent + 16) / 32;
      for (const exponent of [0, 4, 8, 12, 16]) {
        const n = 2 ** exponent;
        line(svg, [[X(n), 72], [X(n), 252]], C.grid, { 'stroke-width': 1 });
        label(svg, X(n), 275, n, { 'text-anchor': 'middle', 'font-size': 11 });
      }
      for (const exponent of [-16, -8, 0, 8, 16]) {
        line(svg, [[80, Y(exponent)], [430, Y(exponent)]], exponent === 0 ? C.ink : C.grid, { 'stroke-width': 1 });
        label(svg, 72, Y(exponent) + 4, exponent, { 'text-anchor': 'end', 'font-size': 11 });
      }
      const alpha = Number(model.state.alpha);
      for (const [name, exponent, color, dash] of [['L¹', alpha - 1, C.blue, ''], ['L²', alpha - .5, C.teal, '7 3'], ['L∞', alpha, C.coral, '2 3']]) {
        line(svg, [[X(1), Y(0)], [X(MAX_N), Y(16 * exponent)]], color, { 'stroke-dasharray': dash, 'data-measure-norm': name, 'data-measure-power': exponent });
        svg.append(shape('circle', { cx: X(model.state.n), cy: Y(Math.log2(model.state.n) * exponent), r: 3.5, fill: color, 'data-measure-selected-norm': name }));
      }
      label(svg, 18, 54, 'Vertical: log₂(norm / A); 0 means norm = A.', { 'font-size': 12 });
      label(svg, 255, 299, 'n (base-two logarithmic scale)', { 'text-anchor': 'middle' });
      label(svg, 18, 324, 'Blue solid L¹ · teal dashed L² · coral dotted L∞', { 'font-size': 12 });
      label(svg, 18, 342, 'Exact power laws; finite display is not a proof.', { 'font-size': 12 });
    }
    function refresh(announce, preserveDraft) {
      const m = model, A = m.state.amplitude;
      widgets.forEach(({ input, output, c }) => {
        if (c.type === 'toggle') input.checked = m.state[c.key];
        else if (c.key !== preserveDraft) input.value = String(m.state[c.key]);
        if (c.key === 'numerator') input.setAttribute('max', m.state.denominator);
        if (output) { output.textContent = format(m.state[c.key]); input.setAttribute('aria-valuetext', output.textContent); }
      });
      root.setAttribute('data-measure-state', JSON.stringify(m.state)); root.setAttribute('data-measure-integral', m.integral);
      root.setAttribute('data-measure-probe-value', m.probe.value); root.setAttribute('data-measure-dominated', m.convergence.dominated);
      summary.replaceChildren(...[['Interval measure', '1/' + m.state.n], ['Height A n^α', format(m.height)], ['Integral = L¹ norm', format(m.integral)], ['L² norm', format(m.norm2)]].map(([name, value]) =>
        element('p', {}, element('small', {}, name), element('strong', {}, value))));
      probe.textContent = 'Fixed probe x = ' + m.probe.a + '/' + m.probe.b + ': hₙ(x) = ' + format(m.probe.value) + '. ' +
        (m.probe.a === 0 ? 'x = 0 is always excluded.' : 'All n ≥ ' + m.probe.zeroFrom + ' exclude this same point, including equality at the right endpoint.') +
        (A === 0 ? ' With A = 0 the function is zero at every point already.' : ' Probe membership uses the exact integer test 0 < n a < b.');
      const exponent = Number(m.state.alpha), limit1 = A === 0 || exponent < 1 ? '0' : format(A), limit2 = A === 0 || exponent < .5 ? '0' : exponent === .5 ? format(A) : '∞';
      ledger.replaceChildren(element('caption', {}, 'Exact formulas and limits as n → ∞ with A and α fixed'),
        element('thead', {}, element('tr', {}, ...['Quantity', 'Exact formula', 'Limit', 'Converges to zero?'].map(name => element('th', { scope: 'col' }, name)))),
        element('tbody', {}, ...[
          ['L¹ norm / integral', 'A n^(α−1)', limit1, m.convergence.l1],
          ['L² norm', 'A n^(α−1/2)', limit2, m.convergence.l2],
          ['Supremum / L∞ norm', 'A n^α', A === 0 ? '0' : exponent === 0 ? format(A) : '∞', m.convergence.uniform],
        ].map(([name, formula, limit, yes]) => element('tr', {}, element('th', { scope: 'row' }, name), element('td', {}, formula), element('td', {}, limit), element('td', {}, yes ? 'Yes' : 'No')))));
      proof.textContent = m.proof; readout.textContent = m.readout; pointwise.textContent = m.pointwise; draw();
      if (announce) status.textContent = 'n = ' + m.state.n + ', integral = ' + format(m.integral) + ', L² norm = ' + format(m.norm2) +
        '. Fixed probe value = ' + format(m.probe.value) + '. Common integrable dominator: ' + (m.convergence.dominated ? 'yes.' : 'no.');
    }
    refresh(false); return root;
  }
  const api = Object.freeze({ MAX_N, initial, controls, normalize, probeInside, envelopeAt, build, render });
  if (typeof window !== 'undefined') window.PrimerMathMeasureLab = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
}());
