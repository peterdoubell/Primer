/* Original ℓ² operator artwork and exact sparse rational calculations. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg', MAX_INDEX = 65536;
  const C = { ink: '#263b46', paper: '#f5efdf', grid: '#d5cfbf', blue: '#3e7085', teal: '#317e78', coral: '#b96652', gold: '#9e741c' };
  const initial = Object.freeze({ operator: 'shift', realization: 'infinite', cutoff: 4, index: 1, first: 12, second: 16, lambdaNumerator: 0, lambdaDenominator: 1 });
  const controls = Object.freeze([
    { key: 'operator', label: 'Operator', options: [['shift', 'Right shift S'], ['diagonal', 'Diagonal D: divide coordinate j by j']] },
    { key: 'realization', label: 'Operator and domain', options: [['infinite', 'Infinite operator; crop the view only'], ['matrix', 'N-dimensional compressed matrix'], ['finite-rank', 'Finite-rank operator on infinite ℓ²']] },
    { key: 'cutoff', label: 'Visible cutoff / compression dimension N', min: 1, max: 32, step: 1 },
    { key: 'index', label: 'First occupied coordinate k', min: 1, max: MAX_INDEX, step: 1 },
    { key: 'first', label: 'First coefficient numerator a (coefficient a/4)', min: -16, max: 16, step: 1 },
    { key: 'second', label: 'Next coefficient numerator b (coefficient b/4)', min: -16, max: 16, step: 1 },
    { key: 'lambdaNumerator', label: 'Real spectral probe numerator p', min: -1024, max: 1024, step: 1 },
    { key: 'lambdaDenominator', label: 'Real spectral probe denominator q', min: 1, max: 65536, step: 1 },
  ].map(c => Object.freeze({ ...c, options: c.options ? Object.freeze(c.options.map(([value, label]) => Object.freeze({ value, label }))) : undefined })));
  let serial = 0;
  function normalize(raw) {
    const s = raw && typeof raw === 'object' ? raw : {}, state = {};
    for (const c of controls) {
      if (c.options) state[c.key] = c.options.some(o => o.value === s[c.key]) ? s[c.key] : initial[c.key];
      else { const v = Number(s[c.key]); state[c.key] = s[c.key] == null || typeof s[c.key] === 'boolean' || !Number.isFinite(v) || (typeof s[c.key] === 'string' && !s[c.key].trim()) ? initial[c.key] : Math.round(Math.max(c.min, Math.min(c.max, v))); }
    }
    return state;
  }
  const gcd = (a, b) => { a = a < 0n ? -a : a; while (b) [a, b] = [b, a % b]; return a || 1n; };
  function rat(n, d = 1n) { n = BigInt(n); d = BigInt(d); if (!d) throw new RangeError('Nonzero denominator required.'); if (d < 0n) { n = -n; d = -d; } const g = gcd(n, d); return { n: n / g, d: d / g }; }
  const add = (a, b) => rat(a.n * b.d + b.n * a.d, a.d * b.d);
  const mul = (a, b) => rat(a.n * b.n, a.d * b.d);
  const neg = a => ({ n: -a.n, d: a.d });
  const abs = a => a.n < 0n ? neg(a) : a;
  const compare = (a, b) => a.n * b.d < b.n * a.d ? -1 : a.n * b.d > b.n * a.d ? 1 : 0;
  const text = a => a.d === 1n ? String(a.n) : a.n + '/' + a.d;
  const value = a => Number(a.n) / Number(a.d);
  const pack = a => ({ numerator: String(a.n), denominator: String(a.d), exact: text(a), value: value(a) });
  const unpack = a => rat(a.numerator, a.denominator);
  const format = v => v === 0 ? '0' : Math.abs(v) < .0001 ? v.toExponential(5) : String(Number(v.toPrecision(6)));
  function insert(map, index, coefficient) { const sum = add(map.get(index) || rat(0), coefficient); if (sum.n) map.set(index, sum); else map.delete(index); }
  function normSquared(map, predicate = () => true) { let sum = rat(0); for (const [j, c] of map) if (predicate(j)) sum = add(sum, mul(c, c)); return sum; }
  function vector(map, cutoff) {
    return { entries: [...map].sort((a, b) => a[0] - b[0]).map(([index, c]) => ({ index, ...pack(c) })),
      normSquared: pack(normSquared(map)), visibleSquared: pack(normSquared(map, j => j <= cutoff)), offscreenSquared: pack(normSquared(map, j => j > cutoff)) };
  }
  function spectral(state, realization) {
    const lambda = rat(state.lambdaNumerator, state.lambdaDenominator), N = state.cutoff, zero = rat(0);
    if (state.operator === 'shift') {
      const distance = realization === 'infinite' ? compare(abs(lambda), rat(1)) <= 0 ? zero : add(abs(lambda), rat(-1)) : abs(lambda);
      const inSpectrum = realization === 'infinite' ? compare(abs(lambda), rat(1)) <= 0 : lambda.n === 0n;
      return { kind: realization === 'infinite' ? 'closed-unit-disk' : 'zero', includesZero: true, inSpectrum,
        eigenvalue: realization !== 'infinite' && lambda.n === 0n, eigenIndex: null, distance: pack(distance), closest: null,
        inverseNorm: null, inverseNote: inSpectrum ? 'No bounded inverse.' : 'Inverse exists. Its norm is not evaluated here; reciprocal spectral distance does not generally give a finite-shift inverse norm.' };
    }
    const candidates = [], includeZero = realization !== 'matrix';
    if (includeZero) candidates.push({ at: zero, index: null });
    if (realization === 'infinite') {
      if (lambda.n > 0n) { const floor = lambda.d / lambda.n; for (const k of new Set([floor < 1n ? 1n : floor, floor + 1n])) if (k >= 1n) candidates.push({ at: rat(1, k), index: Number(k) }); }
      else candidates.push({ at: rat(1), index: 1 });
    } else for (let j = 1; j <= N; j++) candidates.push({ at: rat(1, j), index: j });
    let best;
    for (const c of candidates) { const distance = abs(add(c.at, neg(lambda))); if (!best || compare(distance, best.distance) < 0) best = { ...c, distance }; }
    const inSpectrum = best.distance.n === 0n, eigenvalue = inSpectrum && (best.index !== null || realization === 'finite-rank');
    return { kind: realization === 'infinite' ? 'reciprocal-sequence' : 'finite-reciprocals', includesZero: includeZero, inSpectrum, eigenvalue,
      eigenIndex: eigenvalue ? best.index : null, distance: pack(best.distance), closest: { index: best.index, ...pack(best.at) },
      inverseNorm: inSpectrum ? null : pack(rat(best.distance.d, best.distance.n)),
      inverseNote: inSpectrum ? 'No bounded inverse.' : 'D is self-adjoint and normal; inverse norm equals reciprocal distance to its full spectrum.' };
  }
  function realization(state, requested, kind) {
    const N = state.cutoff, accepted = kind === 'matrix' ? new Map([...requested].filter(([j]) => j <= N)) : new Map(requested), output = new Map();
    for (const [j, c] of accepted) {
      if (kind !== 'infinite' && (j > N || (state.operator === 'shift' && j === N))) continue;
      insert(output, state.operator === 'shift' ? j + 1 : j, state.operator === 'shift' ? c : mul(c, rat(1, j)));
    }
    const lambda = rat(state.lambdaNumerator, state.lambdaDenominator), residual = new Map(output);
    for (const [j, c] of accepted) insert(residual, j, neg(mul(lambda, c)));
    const inputSquared = normSquared(accepted), residualSquared = normSquared(residual), spectrum = spectral(state, kind);
    return { kind, input: vector(accepted, N), excludedInputSquared: pack(add(normSquared(requested), neg(inputSquared))), output: vector(output, N), residual: vector(residual, N),
      eigenvector: inputSquared.n !== 0n && residualSquared.n === 0n, zeroInput: inputSquared.n === 0n, spectrum,
      operatorNorm: state.operator === 'diagonal' || kind === 'infinite' || N > 1 ? 1 : 0,
      injective: kind === 'matrix' ? state.operator === 'diagonal' : kind === 'infinite',
      surjective: kind === 'matrix' && state.operator === 'diagonal', compact: kind !== 'infinite' || state.operator === 'diagonal' };
  }
  function build(raw) {
    const state = normalize(raw), requested = new Map(); insert(requested, state.index, rat(state.first, 4)); insert(requested, state.index + 1, rat(state.second, 4));
    const comparisons = ['infinite', 'matrix', 'finite-rank'].map(kind => realization(state, requested, kind)), selected = comparisons.find(c => c.kind === state.realization);
    const N = state.cutoff, k = state.index, diagonalDistance = add(rat(1, BigInt(k) ** 2n), rat(1, BigInt(k + 1) ** 2n));
    const truncation = state.operator === 'diagonal' ? pack(rat(1, N + 1)) : pack(rat(1));
    const names = { infinite: 'infinite operator on ℓ²', matrix: N + '-dimensional compressed matrix', 'finite-rank': 'finite-rank operator on infinite ℓ²' };
    const spec = selected.spectrum, lambda = pack(rat(state.lambdaNumerator, state.lambdaDenominator));
    const proof = state.operator === 'shift' ?
      'On ℓ², S is an isometry, ker S = {0}, and its range consists exactly of sequences with first coordinate zero. Thus e₁ has no preimage. S* S = I and S S* = I − Pₑ₁. Its complex spectrum is the closed unit disk and it has no eigenvalues; that is an analytic operator theorem, not inferred from the finite drawing. Compression drops e_N at the right boundary; the infinite shift sends it to e_(N+1) with norm one. The compressed matrix is nilpotent and has spectrum {0}. The infinite finite-rank extension also has a kernel containing all offscreen inputs. Its truncation error has norm one for every N, witnessed by e_N.' :
      'D e_k = e_k/k, ||D|| = 1, and ker D = {0}. Its full spectrum is {1,1/2,1/3,…} together with 0. Zero is not an eigenvalue: ||D e_k|| = 1/k → 0 gives unit approximate eigenvectors, while D is injective. The range is not all ℓ²: y_k = 1/k is square summable, but its putative inverse has every coordinate equal to one. Finite-rank approximations satisfy ||D − P_N D P_N|| = 1/(N+1); this analytic all-N bound and compactness of finite-rank operators establish compactness. The N-dimensional matrix is invertible at zero, whereas its extension on ℓ² has a genuine zero eigenvalue in the tail.';
    const witness = 'In infinite ℓ², ||e_j − e_k||² = 2 for every pair j ≠ k. Thus this orthonormal sequence in the closed unit ball has no Cauchy or convergent subsequence. The displayed pair is e_k and e_(k+1). All distinct shifted basis images keep squared distance 2, so S is not compact. For D the displayed pair has squared distance 1/k² + 1/(k+1)², here ' + text(diagonalDistance) + '. This decreasing example alone is not a proof of compactness; the all-N operator-norm approximation above supplies the proof for D.';
    const readout = (state.operator === 'shift' ? 'S' : 'D') + ': selected ' + names[state.realization] + '. Requested x = (' + state.first + '/4)e_' + k + ' + (' + state.second + '/4)e_' + (k + 1) +
      '. Requested squared norm = ' + text(normSquared(requested)) + '. Accepted input squared norm = ' + selected.input.normSquared.exact + '; excluded by the finite matrix domain = ' + selected.excludedInputSquared.exact +
      '. Output squared norm = ' + selected.output.normSquared.exact + ' (visible ' + selected.output.visibleSquared.exact + ', offscreen ' + selected.output.offscreenSquared.exact + ').' +
      ' λ = ' + lambda.exact + '; exact residual squared norm ||Tx − λx||² = ' + selected.residual.normSquared.exact +
      ' (offscreen ' + selected.residual.offscreenSquared.exact + '). ' + (selected.zeroInput ? 'The accepted input is zero: a zero residual cannot make it an eigenvector.' : selected.eigenvector ? 'This nonzero accepted input is an eigenvector.' : 'This accepted input is not an eigenvector.') +
      ' Spectral distance = ' + spec.distance.exact + '. ' + (spec.inSpectrum ? 'λ lies in the spectrum and ' + (spec.eigenvalue ? 'is an eigenvalue.' : 'is not an eigenvalue.') : 'λ lies outside the spectrum.') +
      (spec.closest ? ' Nearest spectral point = ' + spec.closest.exact + (spec.closest.index === null ? '.' : ' at coordinate ' + spec.closest.index + '.') : '') +
      (spec.inverseNorm ? ' Exact resolvent norm = ' + spec.inverseNorm.exact + '.' : ' ' + spec.inverseNote) +
      ' Infinite-operator truncation error norm = ' + truncation.exact + '. All values are dimensionless. Fractions are exact; displayed square roots and plot coordinates are rounded.';
    return { state, requested: vector(requested, N), comparisons, selected, lambda, truncation, witness: { basisDistanceSquared: 2, diagonalDistanceSquared: pack(diagonalDistance), text: witness }, proof, readout };
  }
  function element(tag, attrs = {}, ...children) { const e = document.createElement(tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v))); children.forEach(c => { if (c != null) e.append(c.nodeType ? c : document.createTextNode(String(c))); }); return e; }
  function shape(tag, attrs = {}, text) { const e = document.createElementNS(NS, tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v))); if (text != null) e.textContent = String(text); return e; }
  function label(svg, x, y, text, attrs = {}) { svg.append(shape('text', { x, y, fill: C.ink, 'font-size': 12, ...attrs }, text)); }
  function line(svg, points, color, attrs = {}) { svg.append(shape('polyline', { points: points.map(p => p.join(',')).join(' '), fill: 'none', stroke: color, 'stroke-width': 2, ...attrs })); }
  function render(item, hooks) {
    if (item?.props?.scenario !== 'math.5.functional.operators-truncation' || Object.keys(item.props).length !== 1 || (item.renderer && item.renderer !== 'math-operator-lab')) return null;
    const uid = 'operator-' + ++serial, title = item.title || 'Infinite operators and the finite-window trap';
    const instructions = item.instructions || 'Choose an operator and its domain. Move a sparse input to the crop boundary, then compare full norms, offscreen coordinates and exact spectral information.';
    const root = element('section', { class: 'card lesson-model math-operator-lab', 'data-renderer': 'math-operator-lab', 'aria-labelledby': uid + '-title' });
    const heading = element('div', { class: 'model-heading-row' }, element('h3', { id: uid + '-title' }, title));
    const area = element('div', { class: 'model-controls concept-controls' }), widgets = new Map(), panels = element('div', { class: 'operator-panels' }), pictures = [];
    for (const name of ['Input and operator output', 'Residual coordinates', 'Spectrum and real probe']) {
      const view = element('div', { class: 'operator-viewport', tabindex: '0', role: 'region', 'aria-label': name + '; enlarge for detail' });
      const svg = shape('svg', { viewBox: '0 0 440 340', role: 'img', focusable: 'false' }); view.append(svg); panels.append(view); pictures.push(svg);
    }
    const summary = element('div', { class: 'operator-summary' }), ledger = element('table', { class: 'operator-ledger' }), comparison = element('table', { class: 'operator-ledger' });
    const ledgerView = element('div', { class: 'operator-table-region', tabindex: '0', role: 'region', 'aria-label': 'Exact norm ledger; scroll horizontally' }, ledger);
    const comparisonView = element('div', { class: 'operator-table-region', tabindex: '0', role: 'region', 'aria-label': 'All three operator domains; scroll horizontally' }, comparison);
    const entries = element('p', { class: 'operator-entries' }), readout = element('p', { class: 'model-readout' }), proof = element('p', { class: 'operator-proof' }), witness = element('p', { class: 'spatial-note' });
    const note = element('p', { class: 'spatial-note' }, 'The ambient Hilbert space is complex ℓ² with inner product Σ x_j conjugate(y_j); the controls show real finite-support probes. Leave a numeric field to apply its draft; blank entries restore that control’s default. P_N keeps the first N coordinates. Cropping the infinite view does not change the vector or operator. A finite matrix accepts P_N x in C^N and reports excluded input. A finite-rank operator P_N T P_N still acts on all ℓ²; its residual includes −λx in the unseen tail. A zero vector is never an eigenvector. The full infinite diagonal spectrum is calculated independently of N: a spectral point beyond the visible crop still affects the resolvent. The spectrum drawing shows only a finite prefix and its analytically known limit. Finite compressed shifts can be nonnormal: reciprocal spectral distance does not generally give their inverse norm. Plot axes rescale; tiny coordinates may be subpixel while exact fractions remain in the ledger. Paired stems are offset slightly for readability but retain the same labeled coordinate index. The orthonormal sequence is a Hilbert basis with dense finite span, not a Hamel spanning set. No finite picture proves an all-index or infinite-dimensional theorem.');
    const sources = element('p', { class: 'operator-sources' }, 'Primary references: ', element('a', { href: 'https://ocw.mit.edu/courses/18-102-introduction-to-functional-analysis-spring-2021/39ac233d5d7cbfffcdce8086143688f6_MIT18_102s21_lec19.pdf', target: '_blank', rel: 'noopener noreferrer' }, 'MIT: compactness and finite-rank operators'), ' · ', element('a', { href: 'https://ocw.mit.edu/courses/18-102-introduction-to-functional-analysis-spring-2021/9eaaf363541d01d53c330ee7931fc715_MIT18_102s21_lec20.pdf', target: '_blank', rel: 'noopener noreferrer' }, 'MIT: spectra'));
    const live = element('p', { class: 'model-status', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' }); let model = build(initial), enlarged = false;
    for (const c of controls) {
      const id = uid + '-' + c.key, input = element(c.options ? 'select' : 'input', { id, 'data-operator-control': c.key });
      if (c.options) c.options.forEach(o => input.append(element('option', { value: o.value }, o.label)));
      else { input.setAttribute('type', 'number'); for (const key of ['min', 'max', 'step']) input.setAttribute(key, c[key]); }
      // Commit numeric drafts on change, allowing ordinary clearing/typing.
      input.addEventListener('change', () => { model = build({ ...model.state, [c.key]: input.value }); refresh(true); });
      widgets.set(c.key, input); area.append(element('label', { class: 'model-range-control', for: id }, c.label, input));
    }
    const buttons = element('div', { class: 'model-button-row' });
    const presets = [['boundary', 'Shift e_N beyond the crop', { operator: 'shift', realization: 'infinite', index: 4, cutoff: 4, first: 4, second: 0, lambdaNumerator: 0, lambdaDenominator: 1 }],
      ['resolvent', 'D: λ = 2/5 with N = 2', { operator: 'diagonal', realization: 'infinite', index: 3, cutoff: 2, first: 4, second: 0, lambdaNumerator: 2, lambdaDenominator: 5 }],
      ['tiny', 'D e_65536: tiny, still nonzero', { operator: 'diagonal', realization: 'infinite', index: 65536, cutoff: 4, first: 4, second: 0, lambdaNumerator: 0, lambdaDenominator: 1 }],
      ['zero', 'Zero input', { first: 0, second: 0 }], ['reset', 'Reset activity', initial]];
    for (const [key, text, patch] of presets) { const button = element('button', { type: 'button', class: 'btn ghost small', 'data-operator-action': key }, text); button.addEventListener('click', () => { model = build({ ...model.state, ...patch }); if (key === 'reset') size(false); refresh(true); }); buttons.append(button); }
    const enlarge = element('button', { type: 'button', class: 'btn ghost small', 'data-operator-action': 'enlarge', 'aria-pressed': 'false' }, 'Enlarge plots');
    function size(on) { enlarged = on; root.classList.toggle('is-enlarged', on); enlarge.setAttribute('aria-pressed', String(on)); enlarge.textContent = on ? 'Fit plots' : 'Enlarge plots'; }
    enlarge.addEventListener('click', () => size(!enlarged)); heading.append(enlarge);
    root.append(heading, element('p', { class: 'model-instructions' }, instructions), buttons, area, summary, panels, entries, ledgerView, comparisonView, readout, proof, witness, note, sources, live);
    if (hooks?.speakButton) heading.prepend(hooks.speakButton(() => title + '. ' + instructions + '. ' + readout.textContent + ' ' + proof.textContent + ' ' + witness.textContent + ' ' + note.textContent, 'Read this activity aloud'));
    function setup(i, name) { const svg = pictures[i]; svg.replaceChildren(shape('title', { id: uid + '-title-' + i }, name), shape('desc', { id: uid + '-desc-' + i }, model.readout), shape('rect', { x: 0, y: 0, width: 440, height: 340, rx: 10, fill: C.paper })); svg.setAttribute('aria-labelledby', uid + '-title-' + i); svg.setAttribute('aria-describedby', uid + '-desc-' + i); label(svg, 18, 27, name, { 'font-size': 17, 'font-weight': 600 }); return svg; }
    function stems(i, sets, name) {
      const svg = setup(i, name), N = model.state.cutoff, magnitude = Math.max(.01, ...sets.flatMap(s => s.entries.filter(e => e.index <= N).map(e => Math.abs(e.value))));
      const X = j => 76 + 338 * (j - .5) / N, Y = v => 170 - 100 * v / magnitude;
      for (const ratio of [-1, -.5, 0, .5, 1]) { line(svg, [[76, Y(ratio * magnitude)], [414, Y(ratio * magnitude)]], ratio === 0 ? C.ink : C.grid, { 'stroke-width': 1 }); label(svg, 69, Y(ratio * magnitude) + 4, format(ratio * magnitude), { 'text-anchor': 'end', 'font-size': 10 }); }
      const ticks = new Set([1, N, ...Array.from({ length: N }, (_, j) => j + 1).filter(j => (j - 1) % Math.ceil(N / 8) === 0)]);
      for (const j of ticks) label(svg, X(j), 289, j, { 'text-anchor': 'middle', 'font-size': 11 });
      sets.forEach((set, setIndex) => set.entries.filter(e => e.index <= N).forEach(e => {
        const offset = sets.length === 1 ? 0 : setIndex === 0 ? -2 : 2, x = X(e.index) + offset;
        line(svg, [[x, Y(0)], [x, Y(e.value)]], set.color, { 'data-operator-stem': set.name, 'data-index': e.index, 'data-value': e.value, 'data-scale': magnitude });
        svg.append(shape('circle', { cx: x, cy: Y(e.value), r: 3, fill: set.color }));
      }));
      label(svg, 18, 52, 'Coefficient value; vertical axis rescales.', { 'font-size': 12 }); label(svg, 245, 312, 'Coordinate j; only 1…N are visible', { 'text-anchor': 'middle' });
      label(svg, 18, 334, i === 0 ? 'Blue: accepted input · teal: output · tail in ledger' : 'Coral: Tx − λx · hidden terms stay in the ledger', { 'font-size': 11 });
    }
    function spectrumPlot() {
      const svg = setup(2, 'Spectrum and real λ probe'), s = model.state, sp = model.selected.spectrum, L = model.lambda.value;
      const extent = Math.max(1.2, Math.abs(L) * 1.1), X = x => 220 + 145 * x / extent, Y = y => 172 - 105 * y / extent;
      line(svg, [[40, 172], [400, 172]], C.grid); line(svg, [[220, 55], [220, 289]], C.grid);
      // Equal x/y scale is required to draw a circular complex spectral disk.
      const scale = 105 / extent, XR = x => 220 + scale * x;
      if (sp.kind === 'closed-unit-disk') svg.append(shape('circle', { cx: 220, cy: 172, r: scale, fill: C.blue, 'fill-opacity': .15, stroke: C.blue, 'data-operator-spectrum': 'disk' }));
      else {
        const indices = s.operator === 'diagonal' ? Array.from({ length: s.realization === 'infinite' ? 32 : s.cutoff }, (_, j) => j + 1) : [];
        indices.forEach(j => svg.append(shape('circle', { cx: XR(1 / j), cy: 172, r: 3, fill: C.blue, 'data-operator-eigen-index': j })));
        if (sp.includesZero) svg.append(shape('circle', { cx: XR(0), cy: 172, r: 5, fill: s.operator === 'diagonal' && s.realization === 'infinite' ? C.paper : C.blue, stroke: C.blue, 'stroke-width': 2, 'data-operator-zero-eigen': String(!(s.operator === 'diagonal' && s.realization === 'infinite')) }));
      }
      svg.append(shape('circle', { cx: XR(L), cy: 172, r: 4, fill: C.gold, 'data-operator-lambda': model.lambda.exact }));
      for (const x of [-extent, 0, extent]) label(svg, XR(x), 298, format(x), { 'text-anchor': 'middle' });
      label(svg, 387, 163, 'Re', { 'font-size': 11 }); label(svg, 230, 70, 'Im', { 'font-size': 11 });
      label(svg, 18, 52, 'Complex spectrum; λ control stays on the real axis.');
      label(svg, 18, 320, sp.kind === 'closed-unit-disk' ? 'Blue disk: spectrum; S has no eigenvalues.' : s.operator === 'shift' ? 'Blue zero: eigenvalue of the compressed shift.' : s.realization === 'infinite' ? 'First 32 eigenpoints + hollow non-eigenvalue 0.' : 'Finite eigenpoints; tail zero only for finite rank.', { 'font-size': 11 });
      label(svg, 18, 337, 'Gold λ = ' + model.lambda.exact + '; exact classification below.', { 'font-size': 11 });
    }
    function table(target, caption, headers, rows) { target.replaceChildren(element('caption', {}, caption), element('thead', {}, element('tr', {}, ...headers.map(h => element('th', { scope: 'col' }, h)))), element('tbody', {}, ...rows.map(row => element('tr', {}, element('th', { scope: 'row' }, row[0]), ...row.slice(1).map(v => element('td', {}, v)))))); }
    function refresh(announce) {
      const m = model, sel = m.selected; widgets.forEach((input, key) => { input.value = String(m.state[key]); }); root.setAttribute('data-operator-state', JSON.stringify(m.state)); root.setAttribute('data-operator-residual', sel.residual.normSquared.exact);
      summary.replaceChildren(...[['Accepted norm', format(Math.sqrt(sel.input.normSquared.value))], ['Output norm', format(Math.sqrt(sel.output.normSquared.value))], ['Residual norm', format(Math.sqrt(sel.residual.normSquared.value))], ['Exact inverse norm', sel.spectrum.inverseNorm?.exact || (sel.spectrum.inSpectrum ? 'No inverse' : 'Not evaluated')]].map(([name, v]) => element('p', {}, element('small', {}, name), element('strong', {}, v))));
      const describe = v => v.entries.length ? v.entries.map(e => e.exact + ' e_' + e.index + (e.index > m.state.cutoff ? ' (offscreen)' : '')).join(' + ') : '0';
      entries.textContent = 'Full requested x: ' + describe(m.requested) + '. Full accepted x: ' + describe(sel.input) + '. Full output: ' + describe(sel.output) + '. Full residual: ' + describe(sel.residual) + '.';
      table(ledger, 'Exact squared norms: cropping does not erase the tail', ['Vector', 'Visible', 'Offscreen', 'Total'], [['Requested input', m.requested.visibleSquared.exact, m.requested.offscreenSquared.exact, m.requested.normSquared.exact], ['Accepted input', sel.input.visibleSquared.exact, sel.input.offscreenSquared.exact, sel.input.normSquared.exact], ['Output', sel.output.visibleSquared.exact, sel.output.offscreenSquared.exact, sel.output.normSquared.exact], ['Residual', sel.residual.visibleSquared.exact, sel.residual.offscreenSquared.exact, sel.residual.normSquared.exact]]);
      table(comparison, 'Same request and λ; three different domains/operators', ['Realization', 'Excluded input²', 'Output norm²', 'Residual norm²', 'λ / inverse norm'], m.comparisons.map(c => [c.kind, c.excludedInputSquared.exact, c.output.normSquared.exact, c.residual.normSquared.exact, c.spectrum.inSpectrum ? c.spectrum.eigenvalue ? 'Eigenvalue; no inverse' : 'Spectral, not eigen; no inverse' : c.spectrum.inverseNorm ? 'Outside; norm ' + c.spectrum.inverseNorm.exact : 'Outside; norm not evaluated']));
      readout.textContent = m.readout; proof.textContent = m.proof; witness.textContent = m.witness.text;
      stems(0, [{ ...sel.input, color: C.blue, name: 'input' }, { ...sel.output, color: C.teal, name: 'output' }], 'Accepted input and output'); stems(1, [{ ...sel.residual, color: C.coral, name: 'residual' }], 'Residual Tx − λx'); spectrumPlot();
      if (announce) live.textContent = m.readout;
    }
    refresh(false); return root;
  }
  const api = Object.freeze({ initial, controls, normalize, build, render });
  if (typeof window !== 'undefined') window.PrimerMathOperatorLab = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
}());
