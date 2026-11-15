/* Original finite-sample probability artwork and teaching calculations.
   PCG32 portion adapted from pcg-c-basic: Copyright 2014 Melissa O'Neill.
   PCG32 is under Apache-2.0; see math-probability-lab.LICENSE.txt. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg', MAX_N = 8192;
  const colors = Object.freeze({ ink: '#263b46', blue: '#3e7085', teal: '#317e78', coral: '#b96652', gold: '#b98a2f', grid: '#d5cfbf' });
  const initial = Object.freeze({ experiment: 'bernoulli', n: 256, percent: 50, seed: 42, tolerance: 10 });
  const controls = Object.freeze([
    { key: 'experiment', label: 'Experiment', options: [
      { value: 'bernoulli', label: 'Bernoulli success/failure' }, { value: 'die', label: 'Fair die: count sixes' },
    ] },
    { key: 'n', label: 'Included trials n', min: 1, max: MAX_N, step: 1 },
    { key: 'percent', label: 'Bernoulli success probability (%)', min: 0, max: 100, step: 1 },
    { key: 'seed', label: 'Replay seed', min: 0, max: 9999, step: 1, type: 'number' },
    { key: 'tolerance', label: 'Proportion error tolerance ε (%)', min: 1, max: 50, step: 1 },
  ].map(c => Object.freeze({ ...c, options: c.options ? Object.freeze(c.options.map(Object.freeze)) : undefined })));
  const pathCache = new Map(), distributionCache = new Map(), concentrationCache = new Map();
  let serial = 0;
  function cached(cache, key, limit, calculate) {
    if (cache.has(key)) return cache.get(key);
    const result = calculate(); cache.set(key, result);
    if (cache.size > limit) cache.delete(cache.keys().next().value);
    return result;
  }
  function normalize(raw) {
    const source = raw && typeof raw === 'object' ? raw : {}, state = {};
    controls.forEach(c => {
      if (c.options) state[c.key] = c.options.some(o => o.value === source[c.key]) ? source[c.key] : initial[c.key];
      else {
        const value = Number(source[c.key]);
        state[c.key] = source[c.key] == null || !Number.isFinite(value) ? initial[c.key] :
          Math.round(Math.max(c.min, Math.min(c.max, value)));
      }
    });
    return state;
  }
  const format = n => n === 0 ? '0' : String(Number(n.toPrecision(6)));

  function pcg32(seed, stream = 54) {
    if (!Number.isSafeInteger(seed) || seed < 0 || !Number.isSafeInteger(stream) || stream < 0) throw new RangeError('Nonnegative integer seed and stream required.');
    const mask = (1n << 64n) - 1n, increment = (BigInt(stream) << 1n) | 1n;
    let state = 0n;
    function word() {
      const old = state;
      state = (old * 6364136223846793005n + increment) & mask;
      const shifted = Number((((old >> 18n) ^ old) >> 27n) & 0xffffffffn) >>> 0;
      const rotation = Number(old >> 59n);
      return ((shifted >>> rotation) | (shifted << ((-rotation) & 31))) >>> 0;
    }
    word(); state = (state + BigInt(seed)) & mask; word();
    function bounded(bound) {
      if (!Number.isInteger(bound) || bound < 1 || bound > 0x100000000) throw new RangeError('Invalid integer bound.');
      const threshold = 0x100000000 % bound;
      let value;
      do { value = word(); } while (value < threshold);
      return value % bound;
    }
    return Object.freeze({ word, bounded });
  }
  function probability(state) { return state.experiment === 'die' ? 1 / 6 : state.percent / 100; }
  function samplePath(raw) {
    const state = normalize(raw), p = probability(state);
    const key = [state.experiment, state.seed, state.percent].join(':');
    return cached(pathCache, key, 6, () => {
      const rng = pcg32(state.seed), rows = []; let count = 0, faceSum = 0;
      for (let k = 1; k <= MAX_N; k++) {
        const outcome = state.experiment === 'die' ? 1 + rng.bounded(6) : Number(rng.bounded(100) < state.percent);
        const success = state.experiment === 'die' ? Number(outcome === 6) : outcome;
        count += success; faceSum += outcome;
        rows.push(Object.freeze({ k, outcome, success, count, proportion: count / k,
          deviation: count - k * p, faceMean: faceSum / k }));
      }
      return Object.freeze(rows);
    });
  }
  function logSum(values) {
    const maximum = Math.max(...values);
    if (maximum === -Infinity) return -Infinity;
    let sum = 0, compensation = 0;
    for (const value of values) {
      const next = Math.exp(value - maximum) - compensation, updated = sum + next;
      compensation = (updated - sum) - next; sum = updated;
    }
    return maximum + Math.log(sum);
  }
  function binomial(n, p) {
    if (!Number.isInteger(n) || n < 1 || n > MAX_N || !Number.isFinite(p) || p < 0 || p > 1) throw new RangeError('Supported binomial domain: integer n in [1,8192], p in [0,1].');
    return cached(distributionCache, n + ':' + p, 18, () => {
      const logs = Array(n + 1).fill(-Infinity);
      if (p === 0 || p === 1) logs[p === 0 ? 0 : n] = 0;
      else {
        const mode = Math.min(n, Math.floor((n + 1) * p)), lp = Math.log(p), lq = Math.log1p(-p);
        logs[mode] = 0;
        for (let k = mode; k > 0; k--) logs[k - 1] = logs[k] + Math.log(k) - Math.log(n - k + 1) + lq - lp;
        for (let k = mode; k < n; k++) logs[k + 1] = logs[k] + Math.log(n - k) - Math.log(k + 1) + lp - lq;
        const normalizer = logSum(logs);
        for (let k = 0; k <= n; k++) logs[k] -= normalizer;
      }
      return Object.freeze({ n, p, logs: Object.freeze(logs), pmf: Object.freeze(logs.map(Math.exp)) });
    });
  }
  function outside(k, raw) {
    const s = normalize(raw);
    // These cross-products are integer-exact over the exposed controls. Border
    // outcomes count in the >= event; binary rounding cannot omit a tie.
    return s.experiment === 'die' ? 100 * Math.abs(6 * k - s.n) >= 6 * s.n * s.tolerance
      : Math.abs(100 * k - s.n * s.percent) >= s.n * s.tolerance;
  }
  function tail(raw) {
    const s = normalize(raw), distribution = binomial(s.n, probability(s));
    const selected = [], outcomes = [];
    for (let k = 0; k <= s.n; k++) if (outside(k, s)) { selected.push(distribution.logs[k]); outcomes.push(k); }
    const logProbability = Math.min(0, logSum(selected));
    return { logProbability, value: Math.exp(logProbability), outcomes };
  }
  function probabilityText(logProbability) {
    if (logProbability === -Infinity) return '0';
    if (logProbability > -16) return format(Math.exp(logProbability));
    const exponent = Math.floor(logProbability / Math.LN10);
    const mantissa = Math.exp(logProbability - exponent * Math.LN10);
    return Number(mantissa.toPrecision(5)) + ' × 10^' + exponent;
  }
  function concentration(raw) {
    const s = normalize(raw);
    const key = [s.experiment, s.percent, s.tolerance].join(':');
    return cached(concentrationCache, key, 6, () => Array.from({ length: 14 }, (_, i) => {
      const n = 2 ** i, p = probability(s), t = tail({ ...s, n });
      const bound = Math.min(1, p * (1 - p) / (n * (s.tolerance / 100) ** 2));
      return Object.freeze({ n, logTail: t.logProbability, bound, logBound: bound === 0 ? -Infinity : Math.log(bound) });
    }));
  }
  function build(raw) {
    const state = normalize(raw), p = probability(state), path = samplePath(state).slice(0, state.n);
    const current = path[path.length - 1], countMean = state.n * p, countVariance = state.n * p * (1 - p);
    const proportionVariance = p * (1 - p) / state.n, epsilon = state.tolerance / 100;
    const finiteTail = tail(state), bound = Math.min(1, proportionVariance / epsilon ** 2);
    const points = concentration(state), nextChance = state.experiment === 'die' ? '1/6' : format(p);
    const dieNote = state.experiment === 'die' ? ' Actual face average = ' + format(current.faceMean) +
      '; E[face] = 3.5, Var(face) = 35/12, Var(face average) = ' + format(35 / (12 * state.n)) +
      '. The count and proportion plots use only the six indicator, not the raw face value.' : '';
    const readout = 'Replay seed ' + state.seed + ', prefix n = ' + state.n + '. ' +
      (state.experiment === 'die' ? 'Success means a six: p = 1/6.' : 'Bernoulli success probability p = ' + format(p) + '.') +
      ' Sₙ = ' + current.count + ', E[Sₙ] = ' + format(countMean) + ', Var(Sₙ) = ' + format(countVariance) +
      ', count standard deviation = ' + format(Math.sqrt(countVariance)) +
      '. Sₙ/n = ' + format(current.proportion) + ', E[Sₙ/n] = ' + format(p) +
      ', Var(Sₙ/n) = ' + format(proportionVariance) + ', proportion standard deviation = ' + format(Math.sqrt(proportionVariance)) +
      '. This path’s count deviation Sₙ−np = ' + format(current.deviation) + '; proportion error = ' + format(current.proportion - p) +
      '. Model probability P(|Sₙ/n−p| ≥ ' + format(epsilon) + ') ≈ ' + probabilityText(finiteTail.logProbability) +
      '; Chebyshev upper bound = ' + format(bound) + '.' + dieNote +
      ' Under the IID model, the next success chance remains ' + nextChance + ' after any history. A finite path does not prove convergence or force the next outcome to compensate for earlier outcomes.';
    return { state, p, path, current, countMean, countVariance, proportionVariance, finiteTail, bound, points, readout };
  }

  function element(tag, attributes = {}, ...children) {
    const result = document.createElement(tag);
    Object.entries(attributes).forEach(([key, value]) => result.setAttribute(key, String(value)));
    children.forEach(child => { if (child != null) result.append(child.nodeType ? child : document.createTextNode(String(child))); });
    return result;
  }
  function shape(tag, attributes = {}, text) {
    const result = document.createElementNS(NS, tag);
    Object.entries(attributes).forEach(([key, value]) => result.setAttribute(key, String(value)));
    if (text != null) result.textContent = String(text);
    return result;
  }
  function line(svg, points, color, attrs = {}) {
    if (points.length < 2) return;
    svg.append(shape('polyline', { points: points.map(p => p.join(',')).join(' '), fill: 'none', stroke: color,
      'stroke-width': 2, 'vector-effect': 'non-scaling-stroke', ...attrs }));
  }
  function label(svg, x, y, value, attrs = {}) {
    svg.append(shape('text', { x, y, 'font-size': 14, fill: colors.ink, ...attrs }, value));
  }
  function render(item, hooks) {
    if (item?.props?.scenario !== 'math.4.prob-theory.large-numbers') return null;
    const uid = 'probability-path-' + ++serial;
    const title = item.title || 'A longer sample does not force the path to balance';
    const instruction = item.instructions || 'Extend the same sample path. Compare the shrinking spread of proportions with the growing spread of counts, then inspect exact model tail probabilities.';
    const root = element('section', { class: 'card lesson-model math-probability-lab', 'data-renderer': 'math-probability-lab',
      'aria-labelledby': uid + '-title', 'aria-describedby': uid + '-instructions' });
    const heading = element('div', { class: 'model-heading-row' }, element('h3', { id: uid + '-title' }, title));
    const controlArea = element('div', { class: 'model-controls concept-controls' }), widgets = new Map();
    const summary = element('div', { class: 'math-probability-summary' });
    const outcomes = element('div', { class: 'math-probability-outcomes', role: 'list', 'aria-label': 'Last twenty included outcomes' });
    const outcomeCaption = element('p', { class: 'spatial-note' });
    const panels = element('div', { class: 'math-probability-panels' }), pictures = [];
    ['Running success proportion', 'Signed count deviation', 'Finite-n concentration'].forEach((name, i) => {
      const viewport = element('div', { class: 'math-probability-viewport', tabindex: '0', role: 'region', 'aria-label': name + '; enlarge for fine detail' });
      const svg = shape('svg', { viewBox: '0 0 440 350', role: 'img', focusable: 'false', 'aria-labelledby': uid + '-plot-title-' + i,
        'aria-describedby': uid + '-plot-desc-' + i });
      viewport.append(svg); panels.append(viewport); pictures.push(svg);
    });
    const readout = element('p', { class: 'model-readout' }), status = element('p', { class: 'model-status', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    const note = element('p', { class: 'spatial-note' },
      'The probability calculations assume independent, identically distributed trials with one fixed success probability p. The displayed path is a deterministic PCG32 pseudorandom illustration; its seed is a replay control, not proof of physical randomness or independence. Extending n preserves its earlier outcomes. ' +
      'For the die, the plotted success variable is 1 for a six and 0 otherwise; actual face values and their average are reported separately. The probability slider applies only to Bernoulli trials. ' +
      'The fixed ε band describes an error event, not a guarantee for the path. A sample proportion can move farther from p after moving closer and can leave the band again. Count deviation need not shrink; its model standard deviation grows as √n while proportion standard deviation shrinks as 1/√n for 0<p<1. ' +
      'Gold count curves are ±1 model standard deviation, not confidence limits or bounds on one trajectory. The count plot fits the selected prefix; read its changing axis labels to compare count units. Blue concentration points sum the binomial distribution; gold points give the Chebyshev bound p(1−p)/(nε²), capped at 1. Connecting lines guide the eye between selected integer sizes. Exact finite-n tail probabilities may oscillate because counts are integers. ' +
      'Logarithmic axes are labelled. Positive probabilities too small for ordinary floating-point display retain scientific notation; impossible events are zero. No normal approximation is used. The weak law follows because the Chebyshev bound tends to zero for each fixed ε>0; no finite simulated path proves the infinite limit.');
    const sources = element('p', { class: 'spatial-note' },
      element('a', { href: 'https://ocw.mit.edu/courses/18-440-probability-and-random-variables-spring-2014/9adbf88f8a8b456963d6299ea683e954_MIT18_440S14_Lecture30.pdf', target: '_blank', rel: 'noopener noreferrer' }, 'MIT: Chebyshev and the weak law'), ' · ',
      element('a', { href: 'https://www.pcg-random.org/using-pcg-c-basic.html', target: '_blank', rel: 'noopener noreferrer' }, 'PCG: reproducible pseudorandom examples'));
    let model = build(initial), enlarged = false;
    for (const control of controls) {
      const id = uid + '-' + control.key, output = control.options ? null : element('output', { for: id });
      const input = control.options ? element('select', { id, 'data-probability-control': control.key }) :
        element('input', { id, type: control.type || 'range', min: control.min, max: control.max, step: control.step, 'data-probability-control': control.key });
      control.options?.forEach(o => input.append(element('option', { value: o.value }, o.label)));
      input.addEventListener(control.options ? 'change' : 'input', () => { model = build({ ...model.state, [control.key]: input.value }); refresh(Boolean(control.options)); });
      if (!control.options) input.addEventListener('change', () => refresh(true));
      widgets.set(control.key, { input, output, control });
      controlArea.append(element('label', { class: 'model-range-control', for: id }, control.label, output, input));
    }
    const buttons = element('div', { class: 'model-button-row' });
    [10, 100, 1000, 6000].forEach(n => {
      const button = element('button', { type: 'button', class: 'btn ghost small', 'data-probability-n': n }, n + ' trials');
      button.addEventListener('click', () => { model = build({ ...model.state, n }); refresh(true); }); buttons.append(button);
    });
    const another = element('button', { type: 'button', class: 'btn ghost small', 'data-probability-action': 'next-seed' }, 'Next replay seed');
    another.addEventListener('click', () => { model = build({ ...model.state, seed: (model.state.seed + 1) % 10000 }); refresh(true); });
    const reset = element('button', { type: 'button', class: 'btn ghost small', 'data-probability-action': 'reset' }, 'Reset');
    reset.addEventListener('click', () => { model = build(initial); refresh(false); status.textContent = 'Initial experiment and replay seed restored.'; });
    buttons.append(another, reset);
    const enlarge = element('button', { type: 'button', class: 'btn ghost small', 'aria-pressed': 'false', 'data-probability-action': 'enlarge' }, 'Enlarge plots');
    enlarge.addEventListener('click', () => {
      enlarged = !enlarged; root.classList.toggle('is-enlarged', enlarged); enlarge.setAttribute('aria-pressed', String(enlarged));
      enlarge.textContent = enlarged ? 'Fit plots' : 'Enlarge plots';
    });
    heading.append(enlarge);
    root.append(heading, element('p', { id: uid + '-instructions', class: 'model-instructions' }, instruction), buttons,
      controlArea, summary, outcomeCaption, outcomes, panels, readout, note, sources, status);
    if (hooks && typeof hooks.speakButton === 'function') heading.prepend(hooks.speakButton(() =>
      title + '. ' + instruction + '. ' + readout.textContent + '. ' + note.textContent, 'Read this activity aloud'));
    const X = k => 72 + 342 * Math.log2(k) / 13;
    function plot(i, name, low, high, yName) {
      const svg = pictures[i], Y = value => 260 - 210 * (value - low) / (high - low);
      svg.replaceChildren(shape('title', { id: uid + '-plot-title-' + i }, name), shape('desc', { id: uid + '-plot-desc-' + i }, model.readout),
        shape('rect', { x: 0, y: 0, width: 440, height: 350, rx: 10, fill: '#f5efdf' }));
      label(svg, 22, 25, name, { 'font-size': 18, 'font-weight': 600 });
      [1, 4, 16, 64, 256, 1024, 8192].forEach(k => {
        line(svg, [[X(k), 50], [X(k), 260]], colors.grid, { 'stroke-width': 1 });
        label(svg, X(k), 282, k, { 'text-anchor': 'middle', 'font-size': 12 });
      });
      for (let j = 0; j <= 4; j++) {
        const value = low + (high - low) * j / 4;
        line(svg, [[72, Y(value)], [414, Y(value)]], colors.grid, { 'stroke-width': 1 });
        label(svg, 62, Y(value) + 5, String(Number(value.toPrecision(3))), { 'text-anchor': 'end', 'font-size': 13 });
      }
      label(svg, 243, 309, 'Included trials k (log₂ scale)', { 'text-anchor': 'middle' });
      label(svg, 18, 155, yName, { transform: 'rotate(-90 18 155)', 'text-anchor': 'middle' });
      return { svg, Y };
    }
    function mark(svg, x, y, role) {
      svg.append(shape('circle', { cx: x, cy: y, r: 4, fill: colors.coral, stroke: colors.ink, 'data-probability-marker': role }));
    }
    function draw() {
      const proportion = plot(0, 'Running success proportion', 0, 1, 'Sₖ / k');
      const epsilon = model.state.tolerance / 100, bottom = Math.max(0, model.p - epsilon), top = Math.min(1, model.p + epsilon);
      proportion.svg.append(shape('rect', { x: 72, y: proportion.Y(top), width: 342, height: proportion.Y(bottom) - proportion.Y(top),
        fill: colors.gold, 'fill-opacity': .12 }));
      line(proportion.svg, [[72, proportion.Y(model.p)], [414, proportion.Y(model.p)]], colors.ink, { 'stroke-dasharray': '4 4' });
      line(proportion.svg, model.path.map(row => [X(row.k), proportion.Y(row.proportion)]), colors.blue, { 'data-probability-path': 'proportion' });
      mark(proportion.svg, X(model.state.n), proportion.Y(model.current.proportion), 'proportion');
      label(proportion.svg, 22, 340, 'Dashed target p · gold error band ±ε', { 'font-size': 13 });
      const extent = Math.max(2, ...model.path.map(row => Math.abs(row.deviation)), 4 * Math.sqrt(model.countVariance));
      const magnitude = 10 ** Math.floor(Math.log10(extent));
      const roundedExtent = [1, 2, 5, 10].map(value => value * magnitude).find(value => value >= extent);
      const deviation = plot(1, 'Signed count deviation', -roundedExtent, roundedExtent, 'Sₖ − kp');
      line(deviation.svg, [[72, deviation.Y(0)], [414, deviation.Y(0)]], colors.ink);
      for (const sign of [-1, 1]) line(deviation.svg, model.path.map(row => [X(row.k), deviation.Y(sign * Math.sqrt(row.k * model.p * (1 - model.p)))]), colors.gold,
        { 'stroke-width': 1.3, 'stroke-dasharray': '3 3' });
      line(deviation.svg, model.path.map(row => [X(row.k), deviation.Y(row.deviation)]), colors.teal, { 'data-probability-path': 'count' });
      mark(deviation.svg, X(model.state.n), deviation.Y(model.current.deviation), 'count');
      label(deviation.svg, 22, 340, 'Gold ±1 count SD: not a path bound', { 'font-size': 13 });
      const finiteLogs = model.points.flatMap(point => [point.logTail, point.logBound]).filter(Number.isFinite);
      if (!finiteLogs.length) {
        const zero = plot(2, 'Finite-n concentration', -1, 0, 'log₁₀ probability');
        zero.svg.replaceChildren(shape('title', { id: uid + '-plot-title-2' }, 'Degenerate success probability'),
          shape('desc', { id: uid + '-plot-desc-2' }, model.readout), shape('rect', { x: 0, y: 0, width: 440, height: 350, rx: 10, fill: '#f5efdf' }));
        label(zero.svg, 22, 40, 'At p = ' + model.p + ', the count is deterministic.', { 'font-size': 17 });
        label(zero.svg, 22, 90, 'The error-event probability is exactly zero.');
        label(zero.svg, 22, 130, 'Its logarithm has no finite plotted value.');
      } else {
        const low = Math.floor(Math.min(...finiteLogs) / Math.LN10 / 10) * 10;
        const conc = plot(2, 'Finite-n concentration', Math.min(-1, low), 0, 'log₁₀ probability');
        for (const [property, color] of [['logTail', colors.blue], ['logBound', colors.gold]]) {
          const points = model.points.filter(point => Number.isFinite(point[property]));
          line(conc.svg, points.map(point => [X(point.n), conc.Y(point[property] / Math.LN10)]), color,
            { 'stroke-width': 1.5, 'data-probability-concentration': property });
          points.forEach(point => conc.svg.append(shape('circle', { cx: X(point.n), cy: conc.Y(point[property] / Math.LN10), r: 2.5, fill: color })));
        }
        mark(conc.svg, X(model.state.n), conc.Y(model.finiteTail.logProbability / Math.LN10), 'tail');
        label(conc.svg, 22, 340, 'Blue binomial tail · gold Chebyshev bound', { 'font-size': 13 });
      }
    }
    function refresh(announce) {
      widgets.forEach(({ control, input, output }) => {
        input.value = String(model.state[control.key]);
        if (control.key === 'percent') input.disabled = model.state.experiment === 'die';
        if (output) {
          output.textContent = control.key === 'percent' && model.state.experiment === 'die' ? 'Not used; die p = 1/6' : format(model.state[control.key]);
          input.setAttribute('aria-valuetext', output.textContent);
        }
      });
      root.setAttribute('data-probability-count', String(model.current.count));
      root.setAttribute('data-probability-proportion', String(model.current.proportion));
      root.setAttribute('data-probability-n', String(model.state.n));
      root.setAttribute('data-probability-tail', probabilityText(model.finiteTail.logProbability));
      summary.replaceChildren(...[['Success count', model.current.count], ['Sample proportion', model.current.proportion],
        ['Count SD', Math.sqrt(model.countVariance)], ['Proportion SD', Math.sqrt(model.proportionVariance)]].map(([name, value]) =>
        element('p', {}, element('small', {}, name), element('strong', {}, format(value)))));
      outcomeCaption.textContent = 'Last ' + Math.min(20, model.state.n) + ' included ' + (model.state.experiment === 'die' ? 'die faces; a six is a success.' : 'success indicators (1 = success, 0 = failure).');
      outcomes.replaceChildren(...model.path.slice(-20).map(row => element('span', { role: 'listitem', class: row.success ? 'is-success' : '',
        'data-probability-trial': row.k, 'data-probability-outcome': row.outcome, 'aria-label': 'Trial ' + row.k + ': ' + row.outcome + (model.state.experiment === 'die' ? ', ' + (row.success ? 'six' : 'not six') : '') }, row.outcome)));
      readout.textContent = model.readout; draw();
      if (announce) status.textContent = 'Seed ' + model.state.seed + ', ' + model.state.n + ' included trials. Success count ' + model.current.count +
        ', proportion ' + format(model.current.proportion) + '. Model error-event probability ' + probabilityText(model.finiteTail.logProbability) + '.';
    }
    refresh(false);
    return root;
  }
  window.PrimerMathProbabilityLab = Object.freeze({ MAX_N, controls, initial, normalize, pcg32, probability, samplePath, binomial, outside, tail,
    probabilityText, concentration, build, render });
}());
