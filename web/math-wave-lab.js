/* Exact continuum fields; SVG samples never drive a numerical time integrator. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const controls = Object.freeze([
    { key: 'length', label: 'Interval length L', min: 1, max: 5, step: .25, unit: 'm' },
    { key: 'speed', label: 'Wave speed c', min: .5, max: 3, step: .25, unit: 'm/s' },
    { key: 'amplitude', label: 'Initial first-mode / pulse amplitude A', min: -1, max: 1, step: .1, unit: '' },
    { key: 'second', label: 'Initial second-mode amplitude B', min: -.5, max: .5, step: .1, unit: '' },
    { key: 'velocity', label: 'Initial first-mode velocity V', min: -1, max: 1, step: .1, unit: 's⁻¹' },
    { key: 'diffusivity', label: 'Heat diffusivity κ', min: .05, max: 1, step: .05, unit: 'm²/s' },
    { key: 'time', label: 'Inspect time t', min: 0, max: 8, step: .025, unit: 's' },
  ].map(Object.freeze));
  const initial = Object.freeze({ mode: 'modes', length: 2, speed: 1, amplitude: 1, second: .3,
    velocity: 0, diffusivity: .2, time: .75 });
  const fmt = n => n === 0 ? '0' : String(Number(n.toPrecision(6)));
  let serial = 0;
  function normalize(raw = {}) {
    const s = { mode: raw?.mode === 'pulse' ? 'pulse' : 'modes' };
    controls.forEach(c => {
      const value = Number(raw?.[c.key]);
      s[c.key] = raw?.[c.key] == null || !Number.isFinite(value) ? initial[c.key] :
        Math.max(c.min, Math.min(c.max, value));
    });
    return s;
  }
  function bump(s, coordinate) {
    const period = 2 * s.length;
    const position = ((coordinate % period) + period) % period;
    const width = .08 * s.length, z = (position - .3 * s.length) / width;
    if (Math.abs(z) >= 1) return { f: 0, first: 0, second: 0 };
    const a = s.amplitude, q = 1 - z * z;
    return { f: a * q ** 3, first: -6 * a * z * q ** 2 / width,
      second: -6 * a * q * (1 - 5 * z * z) / width ** 2 };
  }
  function point(raw, x, t) {
    const s = normalize(raw);
    if (!Number.isFinite(x) || x < 0 || x > s.length || !Number.isFinite(t) || t < 0 || t > 24) {
      throw new RangeError('The point must lie in [0,L], with time in [0,24] seconds.');
    }
    let u = 0, ut = 0, ux = 0, uxx = 0, utt = 0, heat = 0, heatX = 0, heatXX = 0, heatT = 0;
    if (s.mode === 'pulse') {
      // F is a 2L-periodic right-moving C² bump. Its negative mirror enforces
      // both fixed endpoints; it is not a continuation through a boundary.
      const right = bump(s, x - s.speed * t), mirror = bump(s, -x - s.speed * t);
      u = right.f - mirror.f; ut = s.speed * (mirror.first - right.first);
      ux = right.first + mirror.first; uxx = right.second - mirror.second; utt = s.speed ** 2 * uxx;
      heat = heatX = heatXX = heatT = null;
    } else {
      for (const [n, a, v] of [[1, s.amplitude, s.velocity], [2, s.second, 0]]) {
        const k = n * Math.PI / s.length, omega = s.speed * k;
        const sn = x === 0 || x === s.length ? 0 : Math.sin(k * x);
        const cs = x === 0 ? 1 : x === s.length ? (-1) ** n : Math.cos(k * x);
        const coefficient = a * Math.cos(omega * t) + v * Math.sin(omega * t) / omega;
        const velocity = -a * omega * Math.sin(omega * t) + v * Math.cos(omega * t);
        const h = a * Math.exp(-s.diffusivity * k * k * t);
        u += coefficient * sn; ut += velocity * sn; ux += k * coefficient * cs;
        uxx -= k * k * coefficient * sn; utt -= omega * omega * coefficient * sn;
        heat += h * sn; heatX += k * h * cs; heatXX -= k * k * h * sn;
        heatT -= s.diffusivity * k * k * h * sn;
      }
    }
    if (x === 0 || x === s.length) u = ut = uxx = utt = 0;
    return { x, t, u, ut, ux, uxx, utt, heat, heatX, heatXX, heatT };
  }
  function quantities(raw, t) {
    const s = normalize(raw);
    if (!Number.isFinite(t) || t < 0 || t > 24) throw new RangeError('Time must be in [0,24] seconds.');
    if (s.mode === 'pulse') return { wave: 1024 * s.speed ** 2 * s.amplitude ** 2 / (385 * .08 * s.length), heat: null };
    let wave = 0, heat = 0;
    for (const [n, a, v] of [[1, s.amplitude, s.velocity], [2, s.second, 0]]) {
      const k = n * Math.PI / s.length, omega = s.speed * k;
      const q = a * Math.cos(omega * t) + v * Math.sin(omega * t) / omega;
      const qt = -a * omega * Math.sin(omega * t) + v * Math.cos(omega * t);
      wave += s.length * (qt * qt + omega * omega * q * q) / 4;
      heat += s.length * a * a * Math.exp(-2 * s.diffusivity * k * k * t) / 4;
    }
    return { wave, heat };
  }
  function build(raw) {
    const state = normalize(raw), start = quantities(state, 0), current = quantities(state, state.time);
    const k = Math.PI / state.length;
    const scale = Math.max(.25, state.mode === 'pulse' ? Math.abs(state.amplitude) :
      Math.abs(state.amplitude) + Math.abs(state.second) + Math.abs(state.velocity) / (state.speed * k));
    const period = 2 * state.length / state.speed, windowStart = Math.floor(state.time / period) * period;
    const profile = Array.from({ length: 321 }, (_, i) => point(state, state.length * i / 320, state.time));
    const readout = 'At t = ' + fmt(state.time) + ' s, wave E = ½∫(u_t² + c²u_x²)dx = ' + fmt(current.wave) +
      ' m/s²; E(0) = ' + fmt(start.wave) + '. ' + (state.mode === 'pulse'
        ? 'A right-moving pulse reflects with sign inversion at each fixed end. Centre at time zero: 0.3L; support half-width: 0.08L. Its first leading edge reaches the right end at ' + fmt(.62 * state.length / state.speed) + ' s. Heat comparison and independent modal velocity are not used in this pulse case.'
        : 'Heat H = ½∫u²dx = ' + fmt(current.heat) + ' m; H(0) = ' + fmt(start.heat) +
          '. The wave requires u and u_t at time zero; heat requires u only. They share u(x,0) = A sin(πx/L) + B sin(2πx/L), with both endpoints fixed to zero.');
    return { state, start, current, scale, period, windowStart, profile, readout };
  }
  function element(tag, attrs = {}, ...children) {
    const e = document.createElement(tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v)));
    children.forEach(c => { if (c != null) e.append(c.nodeType ? c : document.createTextNode(String(c))); }); return e;
  }
  function svgNode(tag, attrs = {}, text) {
    const e = document.createElementNS(NS, tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v)));
    if (text != null) e.textContent = String(text); return e;
  }
  function render(item, hooks) {
    if (item?.props?.scenario !== 'math.5.pde.wave-field') return null;
    const uid = 'wave-field-' + ++serial, title = item.title || 'Fields in space and time: waves and heat';
    const root = element('section', { class: 'card lesson-model math-wave-lab', 'data-renderer': 'math-wave-lab',
      'aria-labelledby': uid + '-title', 'aria-describedby': uid + '-instructions' });
    const readout = element('p', { class: 'math-wave-readout' });
    const equation = element('p', { class: 'math-wave-equation' });
    const live = element('p', { role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    const panels = element('div', { class: 'math-wave-panels' }), views = [];
    ['Current spatial profiles', 'Wave field in space and time', 'Normalized quadratic quantities'].forEach((name, i) => {
      const picture = svgNode('svg', { viewBox: '0 0 440 330', role: 'img', focusable: 'false',
        'aria-labelledby': uid + '-plot-title-' + i, 'aria-describedby': uid + '-plot-desc-' + i });
      panels.append(element('div', { class: 'math-wave-viewport', tabindex: 0, role: 'region', 'aria-label': name + '; enlarge and scroll for detail' }, picture)); views.push(picture);
    });
    const widgets = new Map(), inputs = element('div', { class: 'model-controls concept-controls' });
    let model = build(initial), enlarged = false;
    for (const c of controls) {
      const id = uid + '-' + c.key, output = element('output', { for: id });
      const input = element('input', { type: 'range', id, min: c.min, max: c.max, step: c.step, 'data-wave-control': c.key });
      input.addEventListener('input', () => { model = build({ ...model.state, [c.key]: Number(input.value) }); refresh(false); });
      input.addEventListener('change', () => { live.textContent = model.readout; });
      inputs.append(element('label', { class: 'model-range-control', for: id }, c.label, output, input)); widgets.set(c.key, { c, input, output });
    }
    const presets = element('div', { class: 'model-button-row' }), modeButtons = [];
    for (const [mode, label] of [['modes', 'Two sine modes + heat'], ['pulse', 'Travelling pulse + reflection']]) {
      const button = element('button', { class: 'btn ghost small', type: 'button', 'data-wave-preset': mode }, label);
      button.addEventListener('click', () => { model = build({ ...model.state, mode }); refresh(true); }); presets.append(button); modeButtons.push(button);
    }
    const reset = element('button', { class: 'btn ghost small', type: 'button', 'data-wave-action': 'reset' }, 'Reset');
    reset.addEventListener('click', () => { model = build(initial); refresh(true); }); presets.append(reset);
    const enlarge = element('button', { class: 'btn ghost small', type: 'button', 'data-wave-action': 'enlarge', 'aria-pressed': 'false' }, 'Enlarge field plots');
    enlarge.addEventListener('click', () => { enlarged = !enlarged; root.classList.toggle('is-enlarged', enlarged);
      enlarge.setAttribute('aria-pressed', String(enlarged)); enlarge.textContent = enlarged ? 'Fit field plots' : 'Enlarge field plots'; });
    const note = element('p', { class: 'spatial-note' },
      'These are exact solutions of linear one-dimensional PDEs with homogeneous Dirichlet boundaries u(0,t)=u(L,t)=0. ' +
      'u is a dimensionless signed scalar field, not absolute temperature or a calibrated physical string displacement. ' +
      'E and H are different mathematical quadratic quantities with different units, not directly comparable physical energies. Their fractions use their own initial values; a zero initial value is shown separately. ' +
      'Profile/quantity curves: blue is the wave, coral is heat. In the colour map, blue is positive u, coral is negative u and pale is zero. The colour map samples a 50-by-64 grid at cell centres over one wave period, starting at the displayed time-window origin; it is not a continuous or full-history image. The thin horizontal line marks the inspected time. ' +
      'The profile samples the analytic field at 321 spatial points. The pulse is C², has compact support, and starts with velocity −c f′; the mirrored periodic formula enforces actual fixed-end reflection. ' +
      'Fixed-zero heat boundaries can exchange field content, so the spatial integral need not be conserved. The separate nine-cell heat activity uses insulated boundaries; it is a different boundary-value problem. Forcing, dissipation of waves, nonlinear media, multidimensional fields and arbitrary initial profiles are outside this activity.');
    const heading = element('div', { class: 'model-heading-row' }, element('h3', { id: uid + '-title' }, title), enlarge);
    const instructions = item.instructions || 'Compare oscillation with smoothing, then follow a compact pulse as it reflects from fixed endpoints.';
    root.append(heading, element('p', { id: uid + '-instructions', class: 'model-instructions' }, instructions), equation, presets, inputs, panels, readout, note,
      element('p', { class: 'spatial-note' }, element('a', { href: 'https://ocw.mit.edu/courses/2-062j-wave-propagation-spring-2017/pages/lecture-notes/', target: '_blank', rel: 'noopener noreferrer' }, 'MIT OpenCourseWare: wave propagation and fixed-end reflection')), live);
    if (hooks?.speakButton) heading.prepend(hooks.speakButton(() => title + '. ' + instructions + '. ' + readout.textContent + '. ' + note.textContent, 'Read this activity aloud'));
    function line(svg, points, color, attributes = {}) {
      svg.append(svgNode('polyline', { points: points.map(p => p.join(',')).join(' '), fill: 'none', stroke: color,
        'stroke-width': 2, 'vector-effect': 'non-scaling-stroke', ...attributes }));
    }
    function axes(svg, index, title, x0, x1, y0, y1, xLabel, yLabel) {
      svg.replaceChildren(svgNode('title', { id: uid + '-plot-title-' + index }, title), svgNode('desc', { id: uid + '-plot-desc-' + index }, model.readout),
        svgNode('rect', { x: 0, y: 0, width: 440, height: 330, rx: 10, fill: '#f5efdf' }));
      const X = x => 78 + 332 * (x - x0) / (x1 - x0), Y = y => 265 - 217 * (y - y0) / (y1 - y0);
      svg.append(svgNode('text', { x: 78, y: 26, fill: '#263b46', 'font-size': 15, 'font-weight': 600 }, title));
      for (let i = 0; i <= 4; i++) {
        const x = x0 + (x1 - x0) * i / 4, y = y0 + (y1 - y0) * i / 4;
        line(svg, [[X(x), 48], [X(x), 265]], '#d5cfbf', { 'stroke-width': 1 });
        line(svg, [[78, Y(y)], [410, Y(y)]], '#d5cfbf', { 'stroke-width': 1 });
        svg.append(svgNode('text', { x: X(x), y: 289, fill: '#263b46', 'font-size': 13, 'text-anchor': 'middle' }, fmt(x)),
          svgNode('text', { x: 68, y: Y(y) + 4, fill: '#263b46', 'font-size': 13, 'text-anchor': 'end' }, fmt(y)));
      }
      if (y0 < 0 && y1 > 0) line(svg, [[78, Y(0)], [410, Y(0)]], '#263b46', { 'stroke-width': 1, 'stroke-dasharray': '3 4' });
      svg.append(svgNode('text', { x: 244, y: 320, fill: '#263b46', 'font-size': 14, 'text-anchor': 'middle' }, xLabel),
        svgNode('text', { x: 18, y: 156, transform: 'rotate(-90 18 156)', fill: '#263b46', 'font-size': 14, 'text-anchor': 'middle' }, yLabel)); return { X, Y };
    }
    function refresh(announce) {
      const s = model.state;
      root.setAttribute('data-wave-mode', s.mode);
      widgets.forEach(({ c, input, output }) => {
        input.value = String(s[c.key]); input.disabled = s.mode === 'pulse' && ['second', 'velocity', 'diffusivity'].includes(c.key);
        output.textContent = fmt(s[c.key]) + (c.unit ? ' ' + c.unit : ''); input.setAttribute('aria-valuetext', output.textContent);
      });
      modeButtons.forEach(button => button.setAttribute('aria-pressed', String(button.getAttribute('data-wave-preset') === s.mode)));
      equation.textContent = s.mode === 'pulse' ? 'u(x,t)=F(x−ct)−F(−x−ct); F(s+2L)=F(s); F(s)=A[1−((s−0.3L)/(0.08L))²]³ inside its support, zero outside.' :
        'Wave: u_tt=c²u_xx. Heat: u_t=κu_xx. u(x,0)=A sin(πx/L)+B sin(2πx/L); wave u_t(x,0)=V sin(πx/L).';
      const p = axes(views[0], 0, s.mode === 'pulse' ? 'Compact pulse and fixed-end reflection' : 'Wave oscillates; heat smooths', 0, s.length, -model.scale, model.scale, 'Position x (m)', 'Field u (dimensionless)');
      line(views[0], model.profile.map(q => [p.X(q.x), p.Y(q.u)]), '#3e7085', { 'data-wave-trace': 'wave' });
      if (s.mode === 'modes') line(views[0], model.profile.map(q => [p.X(q.x), p.Y(q.heat)]), '#b96652', { 'data-wave-trace': 'heat' });
      const m = axes(views[1], 1, 'Wave: one period in space and time', 0, s.length, model.windowStart, model.windowStart + model.period, 'Position x (m)', 'Time t (s)');
      for (let row = 0; row < 64; row++) for (let col = 0; col < 50; col++) {
        const x = (col + .5) * s.length / 50, t = model.windowStart + (row + .5) * model.period / 64;
        const value = point(s, x, t).u / model.scale, strength = Math.min(1, Math.abs(value));
        const colour = value < 0 ? [185, 79, 58] : [37, 110, 147];
        const rgb = colour.map((v, i) => Math.round([245, 239, 223][i] * (1 - strength) + v * strength));
        views[1].append(svgNode('rect', { x: 78 + col * 332 / 50, y: 265 - (row + 1) * 217 / 64,
          width: 332 / 50 + .02, height: 217 / 64 + .02, fill: 'rgb(' + rgb.join(',') + ')' }));
      }
      line(views[1], [[78, m.Y(s.time)], [410, m.Y(s.time)]], '#263b46', { 'stroke-width': 1.5, 'data-wave-time-marker': s.time });
      const e = axes(views[2], 2, 'Different normalized quadratic quantities', 0, 8, 0, 1.05, 'Time t (s)', 'Wave E/E(0); heat H/H(0)');
      const times = Array.from({ length: 161 }, (_, i) => i / 20);
      if (model.start.wave > 0) line(views[2], times.map(t => [e.X(t), e.Y(quantities(s, t).wave / model.start.wave)]), '#3e7085', { 'data-wave-quantity': 'wave' });
      else views[2].append(svgNode('text', { x: 90, y: 100, fill: '#3e7085', 'font-size': 14 }, 'Wave E(0)=0: E/E(0) is undefined.'));
      if (s.mode === 'modes' && model.start.heat > 0) line(views[2], times.map(t => [e.X(t), e.Y(quantities(s, t).heat / model.start.heat)]), '#b96652', { 'data-wave-quantity': 'heat' });
      else if (s.mode === 'modes') views[2].append(svgNode('text', { x: 90, y: 126, fill: '#b96652', 'font-size': 14 }, 'Heat H(0)=0: H/H(0) is undefined.'));
      line(views[2], [[e.X(s.time), 48], [e.X(s.time), 265]], '#263b46', { 'stroke-width': 1, 'stroke-dasharray': '3 4' });
      readout.textContent = model.readout + ' Colour-map time window: ' + fmt(model.windowStart) + '–' + fmt(model.windowStart + model.period) + ' s. ' +
        (model.start.wave === 0 ? 'Wave E(0)=0: zero wave solution, no normalization. ' : '') +
        (model.start.heat === 0 ? 'Heat H(0)=0: zero heat solution, no normalization.' : '');
      if (announce) live.textContent = readout.textContent;
    }
    refresh(false); return root;
  }
  window.PrimerMathWaveLab = Object.freeze({ controls, initial, normalize, bump, point, quantities, build, render });
}());
