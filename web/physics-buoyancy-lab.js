/* Original hydrostatic prism model. Geometry and force arrows use fixed physical scales. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const initial = Object.freeze({ mode: 'predict', volume: 200, mass: 120, height: 10,
    density: 1000, gravity: 9.81, depth: 12 });
  const controls = Object.freeze([
    { key: 'volume', label: 'Object volume', min: 50, max: 200, step: 5, unit: 'cm³' },
    { key: 'mass', label: 'Object mass', min: 50, max: 200, step: 10, unit: 'g' },
    { key: 'height', label: 'Object height', min: 5, max: 15, step: .5, unit: 'cm' },
    { key: 'density', label: 'Liquid density', min: 800, max: 1200, step: 50, unit: 'kg/m³' },
    { key: 'gravity', label: 'Gravity', min: 1, max: 20, step: .01, unit: 'm/s²' },
    { key: 'depth', label: 'Depth of the bottom below the surface', min: 0, max: 20, step: .1, unit: 'cm' },
  ].map(Object.freeze));
  const fmt = n => Number(n.toPrecision(6)).toString();
  let serial = 0;
  function normalize(raw = {}) {
    const state = { mode: raw.mode === 'hold' ? 'hold' : 'predict' };
    for (const c of controls) state[c.key] = Number.isFinite(Number(raw[c.key]))
      ? Math.max(c.min, Math.min(c.max, Number(raw[c.key]))) : initial[c.key];
    return state;
  }
  function build(raw) {
    const state = normalize(raw), volume = state.volume * 1e-6, mass = state.mass * .001;
    const area = volume / (state.height * .01), widthCm = Math.sqrt(area) * 100;
    const density = mass / volume, ratio = density / state.density;
    const capacityGrams = state.density * state.volume * .001;
    // Compare decimal UI inputs in grams: the exact neutral preset remains neutral.
    const neutral = state.mass === capacityGrams;
    const floats = state.mass < capacityGrams;
    const equilibriumDepth = floats ? state.height * ratio : null;
    const depth = state.mode === 'hold' ? state.depth : floats ? equilibriumDepth : state.height + 2;
    const immersedHeight = Math.max(0, Math.min(state.height, depth));
    const displaced = area * immersedHeight * .01;
    const bottomPressure = state.density * state.gravity * Math.max(0, depth) * .01;
    const topPressure = state.density * state.gravity * Math.max(0, depth - state.height) * .01;
    const weight = mass * state.gravity, pressureBuoyancy = area * (bottomPressure - topPressure);
    // A mathematically balanced prediction must not display a floating-point residual as a force.
    const displacedMassGrams = state.density * state.volume * immersedHeight / (state.height * 1000);
    const buoyancy = state.mode === 'predict' && (floats || neutral) ? weight : displacedMassGrams * .001 * state.gravity;
    const imbalance = buoyancy - weight;
    const holding = state.mode === 'hold' ? -imbalance : 0;
    const balanceTolerance = 32 * Number.EPSILON * Math.max(weight, buoyancy, 1);
    const direction = Math.abs(imbalance) <= balanceTolerance ? 'balanced' : imbalance > 0 ? 'upward' : 'downward';
    const prediction = floats ? 'Floats with part above the surface' : neutral
      ? 'Neutral when fully immersed: no preferred depth' : 'Too dense to float: downward imbalance';
    const readout = prediction + '. Average object density = ' + fmt(density) + ' kg/m³; liquid density = ' + fmt(state.density) +
      ' kg/m³. Bottom depth = ' + fmt(depth) + ' cm; submerged fraction = ' + fmt(immersedHeight / state.height) +
      '; displaced liquid volume = ' + fmt(displaced * 1e6) + ' cm³. Buoyancy = ' + fmt(buoyancy) +
      ' N; weight = ' + fmt(weight) + ' N. ' + (state.mode === 'hold'
        ? 'An external holding force of ' + fmt(holding) + ' N (positive upward) keeps this position fixed. Without that force, B − W is ' + fmt(imbalance) + ' N: ' + direction + '.'
        : floats ? 'This is the predicted free floating equilibrium, with buoyancy equal to weight.'
          : neutral ? 'This fully immersed inspection position is one of infinitely many neutral depths.'
            : 'The pictured fully immersed position is a test snapshot, not an equilibrium or a simulated fall.');
    return { state, area, widthCm, density, ratio, depth, equilibriumDepth, neutral, floats, immersedHeight,
      displaced, bottomPressure, topPressure, pressureBuoyancy, buoyancy, weight, imbalance, holding, direction, prediction, readout };
  }
  function element(tag, attrs = {}, ...children) {
    const e = document.createElement(tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v)));
    children.forEach(c => { if (c != null) e.append(c.nodeType ? c : document.createTextNode(String(c))); }); return e;
  }
  function svgNode(tag, attrs = {}, value) {
    const e = document.createElementNS(NS, tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v)));
    if (value != null) e.textContent = String(value); return e;
  }
  function render(item, hooks) {
    if (item?.props?.scenario !== 'phys.0.float-sink.hydrostatics') return null;
    const uid = 'buoyancy-' + ++serial, root = element('section', { class: 'card lesson-model physics-buoyancy-lab',
      'data-renderer': 'physics-buoyancy-lab', 'aria-labelledby': uid + '-title' });
    const title = item.title || 'How much water holds it up?', readout = element('p', { class: 'buoyancy-readout' });
    const live = element('p', { role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    const summary = element('p', { class: 'buoyancy-prediction' });
    let model = build(initial), enlarged = false;
    const presets = element('div', { class: 'model-button-row' }), modeButtons = [];
    const select = next => { model = build(next); refresh(true); };
    for (const [mode, label] of [['predict', 'Predict floating'], ['hold', 'Hold at a chosen depth']]) {
      const button = element('button', { type: 'button', class: 'btn ghost small', 'data-buoyancy-mode': mode }, label);
      button.addEventListener('click', () => select({ ...model.state, mode })); presets.append(button); modeButtons.push(button);
    }
    for (const [volume, label] of [[200, 'Wide: 120 g / 200 cm³'], [80, 'Compact: 120 g / 80 cm³'], [120, 'Neutral: 120 g / 120 cm³']]) {
      const button = element('button', { type: 'button', class: 'btn ghost small', 'data-buoyancy-preset': volume }, label);
      button.addEventListener('click', () => select({ ...initial, volume })); presets.append(button);
    }
    const widgets = new Map(), inputs = element('div', { class: 'model-controls concept-controls' });
    const advanced = element('details', { class: 'buoyancy-advanced' }, element('summary', {}, 'Change mass, shape, liquid, gravity or held depth'));
    const advancedInputs = element('div', { class: 'model-controls concept-controls' }); advanced.append(advancedInputs);
    for (const c of controls) {
      const id = uid + '-' + c.key, output = element('output', { for: id });
      const input = element('input', { type: 'range', id, min: c.min, max: c.max, step: c.step, 'data-buoyancy-control': c.key });
      input.addEventListener('input', () => { model = build({ ...model.state, [c.key]: Number(input.value) }); refresh(false); });
      input.addEventListener('change', () => { live.textContent = model.readout; });
      const label = element('label', { class: 'model-range-control', for: id }, c.label, output, input);
      (c.key === 'volume' ? inputs : advancedInputs).append(label); widgets.set(c.key, { input, output, c });
    }
    const panels = element('div', { class: 'buoyancy-panels' }), views = [];
    ['Physical side section', 'Forces at the shown position'].forEach((label, i) => {
      const svg = svgNode('svg', { viewBox: '0 0 440 440', role: 'img', focusable: 'false',
        'aria-labelledby': uid + '-plot-title-' + i, 'aria-describedby': uid + '-plot-desc-' + i });
      panels.append(element('div', { class: 'buoyancy-viewport', tabindex: 0, role: 'region', 'aria-label': label + '; enlarge and scroll for detail' }, svg)); views.push(svg);
    });
    const enlarge = element('button', { type: 'button', class: 'btn ghost small', 'aria-pressed': 'false', 'data-buoyancy-action': 'enlarge' }, 'Enlarge diagrams');
    enlarge.addEventListener('click', () => { enlarged = !enlarged; root.classList.toggle('is-enlarged', enlarged);
      enlarge.setAttribute('aria-pressed', String(enlarged)); enlarge.textContent = enlarged ? 'Fit diagrams' : 'Enlarge diagrams'; });
    const reset = element('button', { type: 'button', class: 'btn ghost small', 'data-buoyancy-action': 'reset' }, 'Reset');
    reset.addEventListener('click', () => select(initial)); presets.append(reset);
    root.append(element('div', { class: 'model-heading-row' }, element('h3', { id: uid + '-title' }, title), enlarge),
      element('p', { class: 'model-instructions' }, item.instructions || 'Guess whether the same mass floats when its sealed volume changes. Inspect the position and the actual forces.'),
      summary, presets, inputs, advanced, panels, readout,
      element('p', { class: 'spatial-note' }, 'A rigid sealed prism has a square horizontal base, fixed vertical orientation and uniformly distributed mass. The side section uses the same calibrated centimetre scale in both directions. Its out-of-plane width equals its shown width; volume is base width² × height. Blue inside the outline marks the submerged volume fraction, not water entering the object. The liquid has uniform density, a fixed level in a large open reservoir and no bottom contact. Gauge pressure is relative to the common surface air pressure; opposite horizontal pressure forces cancel. All force arrows use the same fixed newton scale on the displayed axis and never saturate. Positive signed forces point upward. Arrows are separated horizontally for legibility, not applied at different physical points. Air buoyancy, surface tension, flooding, rotation, compressibility, waves, drag and transient fluid motion are omitted. These static pressure calculations and release-force predictions do not simulate motion or establish its acceleration.'),
      element('p', { class: 'spatial-note' }, element('a', { href: 'https://openstax.org/books/university-physics-volume-1/pages/14-4-archimedes-principle-and-buoyancy', target: '_blank', rel: 'noopener noreferrer' }, 'Archimedes’ principle and hydrostatic pressure · OpenStax'), ' · Original diagrams and code; no textbook image reproduced.'), live);
    if (hooks?.speakButton) root.append(hooks.speakButton(() => readout.textContent));
    function text(svg, x, y, value, attrs = {}) { svg.append(svgNode('text', { x, y, fill: '#263b46', 'font-size': 13, ...attrs }, value)); }
    function line(svg, x1, y1, x2, y2, attrs = {}) { svg.append(svgNode('line', { x1, y1, x2, y2, stroke: '#87999c', 'stroke-width': 1, ...attrs })); }
    function background(svg, i, label) {
      svg.replaceChildren(svgNode('title', { id: uid + '-plot-title-' + i }, label), svgNode('desc', { id: uid + '-plot-desc-' + i }, model.readout),
        svgNode('rect', { x: 0, y: 0, width: 440, height: 440, rx: 10, fill: '#f5efdf' }));
      text(svg, 22, 28, label, { 'font-size': 15, 'font-weight': 600 });
    }
    function refresh(announce) {
      const m = model, s = m.state, Y = depth => 198 + 8 * depth;
      summary.textContent = m.prediction; readout.textContent = m.readout;
      root.setAttribute('data-buoyancy-state', JSON.stringify(s));
      for (const { input, output, c } of widgets.values()) {
        input.value = s[c.key]; output.textContent = fmt(s[c.key]) + ' ' + c.unit;
        input.setAttribute('aria-valuetext', output.textContent);
        input.disabled = c.key === 'depth' && s.mode !== 'hold';
      }
      widgets.get('depth').output.textContent = s.mode === 'hold' ? fmt(s.depth) + ' cm' : 'Chosen only in held-depth mode';
      widgets.get('depth').input.setAttribute('aria-valuetext', widgets.get('depth').output.textContent);
      modeButtons.forEach(b => b.setAttribute('aria-pressed', String(b.getAttribute('data-buoyancy-mode') === s.mode)));
      const picture = views[0]; background(picture, 0, 'Side section: square-base sealed prism');
      picture.append(svgNode('rect', { x: 86, y: Y(0), width: 320, height: Y(20) - Y(0), fill: '#d4e5e7' }));
      for (const z of [-15, -10, -5, 0, 5, 10, 15, 20]) { line(picture, 70, Y(z), 406, Y(z), { 'stroke-dasharray': '3 4' }); text(picture, 62, Y(z) + 4, z, { 'text-anchor': 'end' }); }
      text(picture, 20, 54, 'Depth (cm), positive downward');
      const width = 8 * m.widthCm, x = 246 - width / 2, top = Y(m.depth - s.height);
      picture.append(svgNode('rect', { x, y: top, width, height: 8 * s.height, fill: '#e3b57b',
        'data-buoyancy-geometry': 'body', 'data-width-cm': m.widthCm, 'data-height-cm': s.height }));
      picture.append(svgNode('rect', { x, y: Y(m.depth - m.immersedHeight), width, height: 8 * m.immersedHeight,
        fill: '#5c9baf', 'data-buoyancy-geometry': 'submerged', 'data-volume-cm3': m.displaced * 1e6 }));
      picture.append(svgNode('rect', { x, y: top, width, height: 8 * s.height, fill: 'none', stroke: '#263b46', 'stroke-width': 2 }));
      line(picture, 86, Y(0), 406, Y(0), { stroke: '#207487', 'stroke-width': 2 });
      text(picture, 400, 190, 'liquid surface', { 'text-anchor': 'end' });
      text(picture, 22, 389, 'Base width = ' + fmt(m.widthCm) + ' cm; area = ' + fmt(m.area * 1e4) + ' cm²');
      text(picture, 22, 413, 'Height = ' + fmt(s.height) + ' cm; volume = ' + fmt(s.volume) + ' cm³');
      const forces = views[1]; background(forces, 1, 'Signed forces: upward is positive');
      for (const force of [-5, -2.5, 0, 2.5, 5]) { line(forces, 62, 202 - 30 * force, 412, 202 - 30 * force, { 'stroke-dasharray': '3 4' }); text(forces, 55, 206 - 30 * force, force, { 'text-anchor': 'end' }); }
      text(forces, 22, 54, 'N');
      for (const [x, value, label, key, colour] of [[112, m.buoyancy, 'Buoyancy', 'buoyancy', '#207487'], [200, -m.weight, 'Weight', 'weight', '#bc634a'],
        [288, m.holding, 'Holding', 'holding', '#806f92'], [376, m.imbalance, 'B − W', 'release', '#926f27']]) {
        const end = 202 - 30 * value;
        line(forces, x, 202, x, end, { stroke: colour, 'stroke-width': 3, 'data-buoyancy-force': key, 'data-newtons': value });
        if (Math.abs(value) > 1e-12) {
          const size = Math.min(6, Math.abs(end - 202) * .35), sign = Math.sign(value);
          forces.append(svgNode('path', { d: `M${x - size} ${end + sign * size} L${x} ${end} L${x + size} ${end + sign * size}`, fill: 'none', stroke: colour, 'stroke-width': 2 }));
        }
        text(forces, x, 381, label, { 'text-anchor': 'middle', 'font-size': 12 });
        text(forces, x, 401, fmt(value) + ' N', { 'text-anchor': 'middle', 'font-size': 11 });
      }
      text(forces, 22, 428, 'B − W: imbalance without a holding force', { 'font-size': 12 });
      readout.textContent += ' Base area = ' + fmt(m.area) + ' m²; bottom gauge pressure = ' + fmt(m.bottomPressure) +
        ' Pa; top gauge pressure = ' + fmt(m.topPressure) + ' Pa. B = area × pressure difference = ρ_liquid g V_displaced.';
      if (announce) live.textContent = readout.textContent;
    }
    refresh(false); return root;
  }
  const api = Object.freeze({ initial, controls, normalize, build, render });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else globalThis.PrimerPhysicsBuoyancyLab = api;
})();
