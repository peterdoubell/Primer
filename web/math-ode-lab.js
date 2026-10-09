/* Exact homogeneous second-order ODE activity. The SVG curves are samples of
   analytic solutions; no time-stepping method drives the displayed motion.
   Reference: OpenStax Calculus Volume 3, 7.1 and 7.3. */
(function () {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';
  const C = Object.freeze({ ink: '#263b46', blue: '#3e7085', teal: '#317e78',
    gold: '#b98a2f', coral: '#b96652', grid: '#ddd6c7' });
  const initial = Object.freeze({ damping: .35, frequency: 2, position: 1, velocity: 0, time: 0 });
  const controls = Object.freeze([
    { key: 'damping', label: 'Damping ratio ζ', min: 0, max: 2, step: .05, unit: '' },
    { key: 'frequency', label: 'Natural angular frequency ω₀', min: .5, max: 3, step: .25, unit: 'rad/s' },
    { key: 'position', label: 'Initial displacement x(0)', min: -2, max: 2, step: .25, unit: 'm' },
    { key: 'velocity', label: 'Initial velocity x′(0)', min: -3, max: 3, step: .25, unit: 'm/s' },
    { key: 'time', label: 'Inspect time t', min: 0, max: 12, step: .05, unit: 's' },
  ].map(Object.freeze));
  let serial = 0;

  function normalize(raw) {
    const source = raw && typeof raw === 'object' ? raw : {};
    return Object.fromEntries(controls.map(control => {
      const value = Number(source[control.key]);
      return [control.key, source[control.key] == null || !Number.isFinite(value)
        ? initial[control.key] : Math.max(control.min, Math.min(control.max, value))];
    }));
  }

  // These series remove the removable singularities at zero. In particular,
  // parameters very close to critical damping are not rounded into that case.
  function sinc(value) {
    if (Math.abs(value) < 1e-4) return 1 - value * value / 6 + value ** 4 / 120;
    return Math.sin(value) / value;
  }
  function sinhc(value) {
    if (Math.abs(value) < 1e-4) return 1 + value * value / 6 + value ** 4 / 120;
    return Math.sinh(value) / value;
  }

  function exact(state, time) {
    const s = normalize(state);
    const t = Number(time);
    if (!Number.isFinite(t) || t < 0 || t > 12) throw new RangeError('Time must be in [0, 12] seconds.');
    const omega = s.frequency, alpha = s.damping * omega;
    const discriminant = alpha * alpha - omega * omega;
    const beta = Math.sqrt(Math.abs(discriminant));
    const cosine = discriminant < 0 ? Math.cos(beta * t) : discriminant > 0 ? Math.cosh(beta * t) : 1;
    const sine = t * (discriminant < 0 ? sinc(beta * t) : discriminant > 0 ? sinhc(beta * t) : 1);
    const decay = Math.exp(-alpha * t), x0 = s.position, v0 = s.velocity;
    const x = decay * (x0 * cosine + (v0 + alpha * x0) * sine);
    const v = decay * (v0 * cosine - (alpha * v0 + omega * omega * x0) * sine);
    const a = decay * (-(2 * alpha * v0 + omega * omega * x0) * cosine +
      ((2 * alpha * alpha - omega * omega) * v0 + alpha * omega * omega * x0) * sine);
    const energy = .5 * (v * v + omega * omega * x * x);
    return { t, x, v, a, energy, energyRate: -2 * alpha * v * v };
  }

  // Tiny decay values are nonzero: avoid suggesting finite-time arrival at
  // equilibrium by rounding them to a literal zero in the teaching readout.
  const text = value => value === 0 ? '0' : String(Number(value.toPrecision(6)));
  function build(raw) {
    const state = normalize(raw), alpha = state.damping * state.frequency;
    const discriminant = alpha * alpha - state.frequency ** 2;
    const beta = Math.sqrt(Math.abs(discriminant));
    const regime = state.damping === 0 ? 'Undamped' : state.damping < 1 ? 'Underdamped' :
      state.damping === 1 ? 'Critically damped' : 'Overdamped';
    let roots, formula, basis;
    if (discriminant < 0) {
      roots = [{ real: -alpha, imaginary: beta }, { real: -alpha, imaginary: -beta }];
      formula = 'x(t) = exp(−' + text(alpha) + 't)[' + text(state.position) + ' cos(' + text(beta) +
        't) + (' + text((state.velocity + alpha * state.position) / beta) + ') sin(' + text(beta) + 't)].';
      basis = 'Complex conjugate roots give two independent sine and cosine solutions. The oscillation angular frequency is ' +
        text(beta) + ' rad/s; ω₀ is the natural undamped frequency.';
    } else if (discriminant === 0) {
      roots = [{ real: -alpha, imaginary: 0 }, { real: -alpha, imaginary: 0 }];
      formula = 'x(t) = exp(−' + text(alpha) + 't)[' + text(state.position) + ' + (' +
        text(state.velocity + alpha * state.position) + ')t].';
      basis = 'The repeated root needs exp(−ω₀t) AND t exp(−ω₀t). Writing the same exponential twice does not give two independent solutions.';
    } else {
      // The reciprocal form avoids cancellation in the slower root.
      const fast = -state.frequency * (state.damping + Math.sqrt(state.damping ** 2 - 1));
      const slow = -state.frequency / (state.damping + Math.sqrt(state.damping ** 2 - 1));
      roots = [{ real: slow, imaginary: 0 }, { real: fast, imaginary: 0 }];
      const a = (state.velocity - fast * state.position) / (slow - fast), b = state.position - a;
      formula = 'x(t) = (' + text(a) + ') exp(' + text(slow) + 't) + (' + text(b) + ') exp(' + text(fast) + 't).';
      basis = 'Two distinct negative real roots give independent decaying exponentials. A non-oscillatory solution can cross equilibrium once; its initial velocity matters.';
    }
    const start = exact(state, 0), current = exact(state, state.time);
    const samples = Array.from({ length: 601 }, (_, i) => exact(state, i / 50));
    const rootsText = roots.map(root => text(root.real) + (root.imaginary === 0 ? '' :
      (root.imaginary < 0 ? ' − ' : ' + ') + text(Math.abs(root.imaginary)) + 'i')).join(', ');
    const readout = regime + '. Characteristic roots: ' + rootsText + '. ' + formula +
      ' At t = ' + text(current.t) + ' s: x = ' + text(current.x) + ' m, x′ = ' + text(current.v) +
      ' m/s, x″ = ' + text(current.a) + ' m/s². Energy per unit mass E = ' + text(current.energy) +
      ' m²/s²; dE/dt = ' + text(current.energyRate) + ' m²/s³. ' + basis;
    return { state, alpha, discriminant, roots, regime, formula, basis, start, current, samples, readout };
  }

  function element(tag, attributes = {}, ...children) {
    const result = document.createElement(tag);
    for (const [key, value] of Object.entries(attributes)) result.setAttribute(key, String(value));
    for (const child of children) if (child != null) result.append(child.nodeType ? child : document.createTextNode(String(child)));
    return result;
  }
  function svgElement(tag, attributes = {}, content) {
    const result = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attributes)) result.setAttribute(key, String(value));
    if (content != null) result.textContent = String(content);
    return result;
  }

  function render(item, hooks) {
    if (item?.props?.scenario !== 'math.4.diffeq.second-order') return null;
    const uid = 'math-ode-' + ++serial;
    const title = item.title || 'Two initial conditions select a second-order solution';
    const instructions = item.instructions || 'Compare the damping regimes. Change both initial conditions, then scrub time to link displacement, phase space and energy.';
    const root = element('section', { class: 'card lesson-model math-ode-lab', 'data-renderer': 'math-ode-lab',
      'aria-labelledby': uid + '-title', 'aria-describedby': uid + '-instructions' });
    const heading = element('div', { class: 'model-heading-row' }, element('h3', { id: uid + '-title' }, title));
    const readout = element('p', { class: 'model-readout', id: uid + '-readout' });
    const status = element('p', { class: 'model-status', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    const panels = element('div', { class: 'math-ode-panels' });
    const diagramViews = [];
    ['Displacement against time', 'Phase plane: displacement and velocity', 'Mechanical energy'].forEach((label, index) => {
      const viewport = element('div', { class: 'math-ode-viewport', tabindex: '0', role: 'region',
        'aria-label': label + '; use Enlarge graphs for fine detail' });
      const svg = svgElement('svg', { viewBox: '0 0 440 320', role: 'img', focusable: 'false',
        'aria-labelledby': uid + '-plot-title-' + index, 'aria-describedby': uid + '-plot-desc-' + index });
      viewport.append(svg); panels.append(viewport); diagramViews.push(svg);
    });
    const controlArea = element('div', { class: 'model-controls concept-controls' });
    const widgets = new Map();
    let model = build(initial), enlarged = false;
    const equation = element('p', { class: 'math-ode-equation' });
    const note = element('p', { class: 'spatial-note' },
      'A linear, unforced spring–damper equation measured from equilibrium: x″ + 2ζω₀x′ + ω₀²x = 0. ' +
      'Mass is divided out; E = (x′² + ω₀²x²)/2 is mechanical energy per unit mass. Damping removes energy at rate −2ζω₀x′². ' +
      'The curves sample exact analytic solutions every 0.02 s; the inspected values use the formulas at the chosen time. ' +
      'Blue traces cover 0–12 s, the gold phase trace covers the elapsed time, coral marks the inspected state, and teal shows energy. ' +
      'Graph axes have labelled units and independent scales. A phase arrow shows direction, not speed or a finite integration step. ' +
      'Zero displacement and zero velocity give the equilibrium solution. Critical or overdamped motion is not necessarily monotone for arbitrary initial velocity. ' +
      'This activity does not model forcing, nonlinear springs or real apparatus tolerances.');
    const source = element('p', { class: 'spatial-note' }, element('a', {
      href: 'https://openstax.org/books/calculus-volume-3/pages/7-3-applications', target: '_blank', rel: 'noopener noreferrer',
    }, 'OpenStax Calculus Volume 3: second-order applications'));
    const presetArea = element('div', { class: 'model-button-row' });
    for (const [label, damping] of [['Undamped', 0], ['Underdamped', .35], ['Critical', 1], ['Overdamped', 1.7]]) {
      const button = element('button', { type: 'button', class: 'btn ghost small', 'data-ode-damping': damping }, label);
      button.addEventListener('click', () => { model = build({ ...model.state, damping }); refresh(true); });
      presetArea.append(button);
    }
    for (const control of controls) {
      const inputId = uid + '-' + control.key;
      const output = element('output', { for: inputId });
      const input = element('input', { type: 'range', id: inputId, min: control.min, max: control.max,
        step: control.step, 'data-ode-control': control.key });
      input.addEventListener('input', () => {
        model = build({ ...model.state, [control.key]: input.value }); refresh(false);
      });
      input.addEventListener('change', () => refresh(true));
      widgets.set(control.key, { input, output, control });
      controlArea.append(element('label', { class: 'model-range-control', for: inputId }, control.label, output, input));
    }
    const reset = element('button', { type: 'button', class: 'btn ghost small', 'data-ode-action': 'reset' }, 'Reset');
    reset.addEventListener('click', () => { model = build(initial); refresh(false); status.textContent = 'Initial conditions and parameters reset.'; });
    const enlarge = element('button', { type: 'button', class: 'btn ghost small', 'aria-pressed': 'false',
      'data-ode-action': 'enlarge' }, 'Enlarge graphs');
    enlarge.addEventListener('click', () => {
      enlarged = !enlarged;
      root.classList.toggle('is-enlarged', enlarged);
      enlarge.setAttribute('aria-pressed', String(enlarged));
      enlarge.textContent = enlarged ? 'Fit graphs' : 'Enlarge graphs';
    });
    heading.append(enlarge);
    presetArea.append(reset);
    root.append(heading, element('p', { id: uid + '-instructions', class: 'model-instructions' }, instructions),
      equation, presetArea, controlArea, panels, readout, note, source, status);
    if (hooks && typeof hooks.speakButton === 'function') heading.prepend(hooks.speakButton(() =>
      title + '. ' + instructions + '. ' + readout.textContent + '. ' + note.textContent, 'Read this activity aloud'));

    function line(svg, points, color, width = 2, attributes = {}) {
      svg.append(svgElement('polyline', { points: points.map(p => p.join(',')).join(' '), fill: 'none',
        stroke: color, 'stroke-width': width, 'vector-effect': 'non-scaling-stroke', ...attributes }));
    }
    function plot(svg, index, label, desc, xmin, xmax, ymin, ymax, xlabel, ylabel, yTicks) {
      svg.replaceChildren(svgElement('title', { id: uid + '-plot-title-' + index }, label),
        svgElement('desc', { id: uid + '-plot-desc-' + index }, desc));
      const X = x => 62 + (x - xmin) * 360 / (xmax - xmin), Y = y => 244 - (y - ymin) * 202 / (ymax - ymin);
      svg.append(svgElement('text', { x: 62, y: 24, fill: C.ink, 'font-size': 18, 'font-weight': 600 }, label));
      for (let tick = 0; tick <= 4; tick++) {
        const x = xmin + (xmax - xmin) * tick / 4;
        line(svg, [[X(x), 42], [X(x), 244]], C.grid, 1);
        svg.append(svgElement('text', { x: X(x), y: 267, fill: C.ink, 'font-size': 15, 'text-anchor': 'middle' }, text(x)));
        const y = yTicks ? yTicks[tick] : ymin + (ymax - ymin) * tick / 4;
        line(svg, [[62, Y(y)], [422, Y(y)]], C.grid, 1);
        svg.append(svgElement('text', { x: 56, y: Y(y) + 5, fill: C.ink, 'font-size': 14, 'text-anchor': 'end' }, text(y)));
      }
      line(svg, [[62, 42], [62, 244], [422, 244]], C.ink, 1.5);
      if (ymin < 0 && ymax > 0) line(svg, [[62, Y(0)], [422, Y(0)]], C.ink, 1, { 'stroke-dasharray': '4 4' });
      if (xmin < 0 && xmax > 0) line(svg, [[X(0), 42], [X(0), 244]], C.ink, 1, { 'stroke-dasharray': '4 4' });
      svg.append(svgElement('text', { x: 242, y: 303, fill: C.ink, 'font-size': 16, 'text-anchor': 'middle' }, xlabel),
        svgElement('text', { x: 16, y: 143, fill: C.ink, 'font-size': 16,
          transform: 'rotate(-90 16 143)', 'text-anchor': 'middle' }, ylabel));
      return { X, Y };
    }
    function marker(svg, x, y) {
      svg.append(svgElement('circle', { cx: x, cy: y, r: 5, fill: C.coral, stroke: C.ink, 'stroke-width': 1.5,
        'data-ode-current-point': 'true' }));
    }
    function refresh(announce) {
      const s = model.state, q = model.current;
      root.setAttribute('data-ode-regime', model.regime);
      root.setAttribute('data-ode-time', String(s.time));
      equation.textContent = 'x″ + ' + text(2 * model.alpha) + 'x′ + ' + text(s.frequency ** 2) +
        'x = 0; x(0) = ' + text(s.position) + ' m; x′(0) = ' + text(s.velocity) + ' m/s.';
      widgets.forEach(({ input, output, control }) => {
        input.value = String(s[control.key]);
        output.textContent = text(s[control.key]) + (control.unit ? ' ' + control.unit : '');
        input.setAttribute('aria-valuetext', output.textContent);
      });
      const extentX = Math.max(.5, Math.ceil(Math.sqrt(2 * model.start.energy) / s.frequency * 5) / 5);
      const extentV = Math.max(.5, Math.ceil(Math.sqrt(2 * model.start.energy) * 5) / 5);
      const xplot = plot(diagramViews[0], 0, 'Displacement against time', model.readout,
        0, 12, -extentX, extentX, 'Time t (s)', 'Displacement x (m)');
      line(diagramViews[0], model.samples.map(p => [xplot.X(p.t), xplot.Y(p.x)]), C.blue, 2.5);
      line(diagramViews[0], [[xplot.X(q.t), 42], [xplot.X(q.t), 244]], C.coral, 1.5, { 'stroke-dasharray': '3 3' });
      marker(diagramViews[0], xplot.X(q.t), xplot.Y(q.x));
      const phase = plot(diagramViews[1], 1, 'Phase plane: x and x′',
        'The same solution in phase space. The gold trace runs from time zero to the inspected time. ' + model.readout,
        -extentX, extentX, -extentV, extentV, 'Displacement x (m)', 'Velocity x′ (m/s)');
      line(diagramViews[1], model.samples.map(p => [phase.X(p.x), phase.Y(p.v)]), C.blue, 2.5);
      const prefix = model.samples.filter(p => p.t < q.t).concat(q);
      if (q.t > 0) line(diagramViews[1], prefix.map(p => [phase.X(p.x), phase.Y(p.v)]), C.gold, 3);
      // Direction in scaled screen coordinates. Arrow length deliberately does
      // not encode speed, which has incompatible units on these two axes.
      const dx = q.v * 360 / (2 * extentX), dy = -q.a * 202 / (2 * extentV), magnitude = Math.hypot(dx, dy);
      if (magnitude > 1e-12) {
        const ux = dx / magnitude, uy = dy / magnitude, x = phase.X(q.x), y = phase.Y(q.v);
        const ex = x + 18 * ux, ey = y + 18 * uy;
        line(diagramViews[1], [[x, y], [ex, ey]], C.coral, 2);
        line(diagramViews[1], [[ex - 6 * ux - 4 * uy, ey - 6 * uy + 4 * ux], [ex, ey],
          [ex - 6 * ux + 4 * uy, ey - 6 * uy - 4 * ux]], C.coral, 2);
      }
      marker(diagramViews[1], phase.X(q.x), phase.Y(q.v));
      const eplot = plot(diagramViews[2], 2, 'Energy per unit mass',
        'Energy per unit mass, divided by its initial value when that value is nonzero. ' + model.readout,
        0, 12, 0, 1.05, 'Time t (s)', model.start.energy > 0 ? 'Energy fraction E/E(0)' : 'Energy E = 0', [0, .25, .5, .75, 1]);
      const ratio = p => model.start.energy > 0 ? p.energy / model.start.energy : 0;
      line(diagramViews[2], model.samples.map(p => [eplot.X(p.t), eplot.Y(ratio(p))]), C.teal, 2.5);
      marker(diagramViews[2], eplot.X(q.t), eplot.Y(ratio(q)));
      readout.textContent = model.readout;
      if (announce) status.textContent = model.regime + '; at ' + text(q.t) + ' seconds, displacement ' +
        text(q.x) + ' metres and velocity ' + text(q.v) + ' metres per second.';
    }
    refresh(false);
    return root;
  }

  window.PrimerMathODELab = Object.freeze({ controls, initial, normalize, exact, build, render });
}());
