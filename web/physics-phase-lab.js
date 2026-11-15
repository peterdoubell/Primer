/* Original educational artwork. A constant-pressure enthalpy balance sets every state. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  // Representative, constant-property approximations; energy units are kJ and kg.
  const CONSTANTS = Object.freeze({cIce: 2.09, cWater: 4.186, cSteam: 2.020,
    fusion: 334, vaporization: 2256, melt: 0, boil: 100,
    tMin: -30, tMax: 140, pressureKPa: 101.325});
  const C = CONSTANTS;
  // Decimal endpoints avoid making the printed −62.7/3089.4 limits inaccessible
  // because a multiplication rounds one ulp toward the interior.
  const H = Object.freeze({min: -62.7, ice0: 0, water0: 334,
    water100: 752.6, steam100: 3008.6, max: 3089.4});
  const starts = Object.freeze([
    ['ice18', 'Ice at −18 °C', -18 * C.cIce], ['ice0', 'Ice at 0 °C', H.ice0],
    ['water20', 'Liquid water at 20 °C', H.water0 + 20 * C.cWater],
    ['water100', 'Liquid water at 100 °C', H.water100],
    ['steam100', 'Water vapour at 100 °C', H.steam100],
    ['steam120', 'Water vapour at 120 °C', H.steam100 + 20 * C.cSteam]
  ].map(([key, label, enthalpy]) => Object.freeze({key, label, enthalpy})));
  const initial = Object.freeze({mass: .25, start: 'ice18', energy: 0});
  const bindings = Object.freeze({'phys.2.matter.phase-change': initial,
    'phys.0.hot-cold.melting-ice': Object.freeze({mass: .05, start: 'ice0', energy: 0})});
  const controls = Object.freeze([
    Object.freeze({key: 'mass', label: 'Mass of the sample', min: .05, max: 2, step: .05, unit: 'kg'}),
    Object.freeze({key: 'energy', label: 'Heat supplied since the start', step: 'any', unit: 'kJ'})
  ]);
  const stages = Object.freeze([
    ['ice', 'Ice temperature change', '#536e87'], ['fusion', 'Melting / freezing', '#547f91'],
    ['liquid', 'Liquid temperature change', '#317e78'], ['vaporization', 'Boiling / condensing', '#b98a2f'],
    ['steam', 'Vapour temperature change', '#ae6655']
  ].map(([key, label, color]) => Object.freeze({key, label, color})));
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));
  const finite = v => ['number', 'string'].includes(typeof v) && !(typeof v === 'string' && !v.trim()) && Number.isFinite(Number(v));
  const fmt = n => Number(n.toPrecision(6)).toString();
  let serial = 0;

  function startFor(key) { return starts.find(s => s.key === key) || starts[0]; }
  function bounds(mass, start) {
    const h0 = startFor(start).enthalpy;
    return {min: mass * (H.min - h0), max: mass * (H.max - h0)};
  }
  function normalize(raw = {}) {
    const mass = finite(raw.mass) ? clamp(Number(raw.mass), .05, 2) : initial.mass;
    const start = starts.some(s => s.key === raw.start) ? raw.start : initial.start;
    const limits = bounds(mass, start);
    const energy = finite(raw.energy) ? clamp(Number(raw.energy), limits.min, limits.max) : 0;
    return {mass, start, energy};
  }
  function equilibriumOnHeatAxis(mass, h0, q, enthalpy) {
    const qi = mass * (H.ice0 - h0), qw = mass * (H.water0 - h0),
      qb = mass * (H.water100 - h0), qv = mass * (H.steam100 - h0);
    let temperature, ice = 0, water = 0, steam = 0, phase;
    if (q <= qi) {temperature = (q - qi) / (mass * C.cIce); ice = 1; phase = q === qi ? 'Pure ice at its melting point' : 'Solid ice';}
    else if (q < qw) {
      temperature = 0;
      // Compute the small residual from its nearby endpoint. A genuinely tiny
      // second phase must survive even if 1 − its fraction rounds to one.
      if (q - qi <= (qw - qi) / 2) {water = (q - qi) / (mass * C.fusion); ice = 1 - water;}
      else {ice = (qw - q) / (mass * C.fusion); water = 1 - ice;}
      phase = 'Ice and liquid water coexist';
    } else if (q <= qb) {temperature = q === qb ? 100 : (q - qw) / (mass * C.cWater); water = 1; phase = q === qw ? 'Pure liquid at its freezing point' : q === qb ? 'Pure liquid at its boiling point' : 'Liquid water';}
    else if (q < qv) {
      temperature = 100;
      if (q - qb <= (qv - qb) / 2) {steam = (q - qb) / (mass * C.vaporization); water = 1 - steam;}
      else {water = (qv - q) / (mass * C.vaporization); steam = 1 - water;}
      phase = 'Liquid water and vapour coexist';
    } else {temperature = 100 + (q - qv) / (mass * C.cSteam); steam = 1; phase = q === qv ? 'Pure vapour at its condensation point' : 'Water vapour';}
    if (q === mass * (H.min - h0)) temperature = C.tMin;
    if (q === mass * (H.max - h0)) temperature = C.tMax;
    return {enthalpy, temperature, fractions: {ice, water, steam}, phase};
  }
  function resolve(enthalpy) {
    if (!finite(enthalpy) || Number(enthalpy) < H.min || Number(enthalpy) > H.max) throw new RangeError('Enthalpy outside the educational −30…140 °C domain');
    const h = Number(enthalpy);
    return equilibriumOnHeatAxis(1, 0, h, h);
  }
  function components(h) {
    return {ice: Math.min(h, 0), fusion: clamp(h, 0, C.fusion),
      liquid: clamp(h - H.water0, 0, C.cWater * 100),
      vaporization: clamp(h - H.water100, 0, C.vaporization),
      steam: Math.max(0, h - H.steam100)};
  }
  function build(raw = {}) {
    const state = normalize(raw), begin = startFor(state.start), initialH = begin.enthalpy;
    let currentH = initialH + state.energy / state.mass;
    // Exact heat targets identify boundaries. No tolerance erases small phases.
    for (const h of Object.values(H)) if (state.energy === state.mass * (h - initialH)) currentH = h;
    currentH = clamp(currentH, H.min, H.max);
    const current = equilibriumOnHeatAxis(state.mass, initialH, state.energy, currentH), start = resolve(initialH);
    const qEdges = Object.values(H).map(h => state.mass * (h - initialH));
    const qLo = Math.min(0, state.energy), qHi = Math.max(0, state.energy), sign = Math.sign(state.energy);
    const ledger = stages.map((s, i) => ({...s, energy: sign * Math.max(0, Math.min(qHi, qEdges[i + 1]) - Math.max(qLo, qEdges[i]))}));
    const masses = Object.fromEntries(Object.entries(current.fractions).map(([k, f]) => [k, state.mass * f]));
    const limits = bounds(state.mass, state.start), deltaH = ledger.reduce((sum, row) => sum + row.energy, 0);
    const points = [H.min, H.ice0, H.water0, H.water100, H.steam100, H.max].map(h => ({energy: state.mass * (h - initialH), temperature: resolve(h).temperature, enthalpy: h}));
    let change = state.energy === 0 ? 'No heat has been supplied or removed.' : state.energy > 0 ? 'Positive heat enters the sample.' : 'Negative heat means heat leaves the sample.';
    if (current.fractions.ice > 0 && current.fractions.water > 0) change += ' At 0 °C, heat changes the ice/water fraction; it does not change temperature.';
    if (current.fractions.water > 0 && current.fractions.steam > 0) change += ' At 100 °C, heat changes the liquid/vapour fraction; it does not change temperature.';
    const readout = `The sample started as ${begin.label.toLowerCase()}, mass ${fmt(state.mass)} kilograms. Signed heat supplied = ${fmt(state.energy)} kilojoules. ` +
      `Now: ${fmt(current.temperature)} degrees Celsius; ${current.phase.toLowerCase()}. ` +
      `Ice ${fmt(masses.ice)} kilograms (${fmt(current.fractions.ice * 100)} percent), liquid ${fmt(masses.water)} kilograms (${fmt(current.fractions.water * 100)} percent), ` +
      `vapour ${fmt(masses.steam)} kilograms (${fmt(current.fractions.steam * 100)} percent). Enthalpy change = ${fmt(deltaH)} kilojoules. ${change}`;
    return {state, initialH, currentH, start, ...current, masses, ledger, limits, deltaH,
      balanceResidual: deltaH - state.energy, points, readout, change,
      equation: 'At fixed pressure: Q = ΔH = m(h − h_start). Within one phase: Δh ≈ c_p ΔT. On a plateau: Δh = L Δf.',
      note: 'An ideal, captured pure-water sample stays at approximately 1 atmosphere (101.325 kPa), while its volume may change. Heat equals its enthalpy change, including expansion work; it is not all an internal-energy change. No mass escapes. Each state is uniform and in phase equilibrium, with approximate transition temperatures of 0 and 100 °C. The heat capacities and latent heats are held constant. Cooling follows the same equilibrium path backward; supercooling, superheating, nucleation, real heat-transfer rates and heat leaks are omitted. This is an energy-controlled example, not a timing model of an ice cube in a hand. Open-air evaporation below boiling, pressure-dependent transitions, molecular motion, density and compressibility need separate models. Vapour is a gas, not visible liquid mist.'};
  }
  function el(tag, attrs = {}, ...children) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
    for (const c of children) if (c != null) e.append(c.nodeType ? c : document.createTextNode(String(c)));
    return e;
  }
  function sn(tag, attrs = {}, value) {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
    if (value != null) e.textContent = String(value);
    return e;
  }
  function render(item, hooks) {
    const scenario = item?.props?.scenario;
    if (!Object.prototype.hasOwnProperty.call(bindings, scenario) || Object.keys(item.props).length !== 1) return null;
    const uid = 'phase-' + ++serial, startState = bindings[scenario];
    const root = el('section', {class: 'card lesson-model physics-phase-lab', 'data-renderer': 'physics-phase-lab', 'aria-labelledby': uid + '-title'});
    let model = build(startState);
    const summary = el('p', {class: 'phase-summary'}), limitsNote = el('p', {class: 'spatial-note phase-limits'}), readout = el('p', {class: 'phase-readout'}), equation = el('p', {class: 'phase-equation'});
    const live = el('p', {class: 'phase-live', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true'});
    const inputs = el('div', {class: 'model-controls concept-controls'}), widgets = new Map();
    const select = el('select', {id: uid + '-start', 'data-phase-start': ''});
    for (const s of starts) select.append(el('option', {value: s.key}, s.label));
    inputs.append(el('label', {for: uid + '-start', class: 'phase-start-control'}, 'Starting sample (changes reset heat to zero)', select));
    select.addEventListener('change', () => {model = build({...model.state, start: select.value, energy: 0}); refresh(true);});
    for (const c of controls) {
      const id = uid + '-' + c.key, input = el('input', {id, type: 'range', step: c.step, 'data-phase-control': c.key});
      const output = el('output', {for: id}), label = el('label', {for: id, class: 'model-range-control'}, c.label, output, input);
      input.addEventListener('input', () => {model = build({...model.state, [c.key]: input.value}); refresh(false);});
      input.addEventListener('change', () => {live.textContent = model.readout;});
      inputs.append(label); widgets.set(c.key, {input, output});
    }
    const number = el('input', {id: uid + '-energy-number', type: 'number', step: 'any', 'data-phase-energy-number': ''});
    inputs.append(el('label', {for: uid + '-energy-number', class: 'phase-number-control'}, 'Enter signed heat (kJ)', number));
    number.addEventListener('change', () => {model = build({...model.state, energy: number.value}); refresh(true);});
    const presets = el('div', {class: 'model-button-row'});
    const targets = [['ice0', H.ice0, 'Ice reaches 0 °C'], ['half-melt', C.fusion / 2, 'Half melted'],
      ['water0', H.water0, 'All liquid at 0 °C'], ['water100', H.water100, 'Liquid reaches 100 °C'],
      ['half-boil', H.water100 + C.vaporization / 2, 'Half vapour'], ['steam100', H.steam100, 'All vapour at 100 °C']];
    for (const [key, h, label] of targets) {
      const b = el('button', {type: 'button', class: 'btn ghost small', 'data-phase-target': key}, label);
      b.addEventListener('click', () => {model = build({...model.state, energy: model.state.mass * (h - model.initialH)}); refresh(true);}); presets.append(b);
    }
    const returnStart = el('button', {type: 'button', class: 'btn ghost small', 'data-phase-action': 'return'}, 'Return to starting state');
    returnStart.addEventListener('click', () => {model = build({...model.state, energy: 0}); refresh(true);}); presets.append(returnStart);
    const cool = el('button', {type: 'button', class: 'btn ghost small', 'data-phase-action': 'cool'}, 'Condense warm vapour');
    cool.addEventListener('click', () => {model = build({mass: model.state.mass, start: 'steam120', energy: model.state.mass * (H.water100 + C.vaporization / 2 - startFor('steam120').enthalpy)}); refresh(true);}); presets.append(cool);
    const reset = el('button', {type: 'button', class: 'btn ghost small', 'data-phase-action': 'reset'}, 'Reset');
    reset.addEventListener('click', () => {model = build(startState); refresh(true);}); presets.append(reset);
    const enlarge = el('button', {type: 'button', class: 'btn ghost small', 'data-phase-action': 'enlarge', 'aria-pressed': 'false'}, 'Enlarge plots');
    enlarge.addEventListener('click', () => {const on = enlarge.getAttribute('aria-pressed') !== 'true'; enlarge.setAttribute('aria-pressed', String(on)); root.classList.toggle('is-enlarged', on); enlarge.textContent = on ? 'Fit plots' : 'Enlarge plots';});
    const panels = el('div', {class: 'phase-panels'}), views = [];
    for (let i = 0; i < 2; i++) {
      const svg = sn('svg', {viewBox: '0 0 440 420', role: 'img', 'aria-labelledby': uid + '-svg-title-' + i, 'aria-describedby': uid + '-svg-desc-' + i});
      views.push(svg); panels.append(el('div', {class: 'phase-viewport', tabindex: 0, role: 'region', 'aria-label': i ? 'Phase mass fractions and signed energy ledger; enlarge and scroll' : 'Temperature versus signed heat; enlarge and scroll'}, svg));
    }
    const assumptions = el('details', {class: 'phase-assumptions'}, el('summary', {}, 'Model assumptions and limits'),
      el('p', {class: 'spatial-note'}, model.note),
      el('p', {class: 'spatial-note'}, 'Constant values: ice 2.09, liquid 4.186 and vapour 2.020 kJ/(kg·K); fusion 334 and vaporization 2256 kJ/kg. These are representative educational approximations, not an IAPWS property calculation.'),
      el('p', {class: 'spatial-note'}, el('a', {href: 'https://openstax.org/books/university-physics-volume-2/pages/1-4-heat-transfer-specific-heat-and-calorimetry', target: '_blank', rel: 'noopener noreferrer'}, 'OpenStax heat capacities'), ' · ',
        el('a', {href: 'https://openstax.org/books/university-physics-volume-2/pages/1-5-phase-changes', target: '_blank', rel: 'noopener noreferrer'}, 'OpenStax latent heat'), ' · ',
        el('a', {href: 'https://iapws.org/technical-guidance/release/IAPWS-95', target: '_blank', rel: 'noopener noreferrer'}, 'IAPWS fluid properties'), '. Original artwork; no source figure copied.'));
    root.append(el('div', {class: 'model-heading-row'}, el('h3', {id: uid + '-title'}, item.title || 'Heat changes the state of water'), enlarge),
      el('p', {class: 'model-instructions'}, item.instructions || 'Add or remove heat. Inspect the flat sections, where energy changes phase fractions while temperature stays fixed.'),
      summary, inputs, limitsNote, presets, panels, equation, readout, assumptions, live);
    if (hooks?.speakButton) root.append(hooks.speakButton(() => model.readout + ' ' + model.equation));
    function text(svg, x, y, value, attrs = {}) {svg.append(sn('text', {x, y, fill: '#263b46', 'font-size': 13, ...attrs}, value));}
    function line(svg, a, b, color, attrs = {}) {svg.append(sn('line', {x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: color, 'stroke-width': 1.5, ...attrs}));}
    function setup(i, title) {
      const svg = views[i]; svg.replaceChildren(sn('title', {id: uid + '-svg-title-' + i}, title), sn('desc', {id: uid + '-svg-desc-' + i}, model.readout), sn('rect', {x: 0, y: 0, width: 440, height: 420, fill: '#f5efdf', rx: 10}));
      text(svg, 18, 27, title, {'font-size': 16, 'font-weight': 600}); return svg;
    }
    function refresh(announce) {
      const m = model, s = m.state;
      root.setAttribute('data-phase-state', JSON.stringify(s)); select.value = s.start;
      for (const c of controls) {
        const w = widgets.get(c.key), limits = c.key === 'mass' ? c : m.limits;
        w.input.min = limits.min; w.input.max = limits.max; w.input.value = s[c.key];
        w.output.textContent = fmt(s[c.key]) + ' ' + c.unit;
        w.input.setAttribute('aria-valuetext', c.key === 'energy' ? fmt(s.energy) + ' kilojoules; ' + fmt(m.temperature) + ' degrees Celsius; ' + m.phase : w.output.textContent);
      }
      number.min = m.limits.min; number.max = m.limits.max; number.value = s.energy;
      summary.textContent = `${startFor(s.start).label}; ${fmt(s.mass)} kg. Fixed pressure ≈ 1 atm; all mass stays in a sample that can expand. Negative heat cools the sample. Mass changes keep the same heat input within the stated range.`;
      limitsNote.textContent = `Model range: 0.05–2 kg and −30–140 °C. For this starting sample, heat can range from ${fmt(m.limits.min)} to ${fmt(m.limits.max)} kJ. Entries beyond these limits use the nearest endpoint; a blank heat entry resets to zero.`;
      equation.textContent = m.equation; readout.textContent = m.readout;
      const a = setup(0, 'Temperature versus supplied heat'), b = setup(1, 'Mass fractions and energy ledger');
      const X = q => 68 + 344 * (q - m.limits.min) / (m.limits.max - m.limits.min);
      const Y = t => 334 - 238 * (t + 30) / 170;
      text(a, 18, 52, 'Temperature (°C)'); text(a, 18, 73, 'Flat sections change phase, not temperature.');
      for (const t of [-30, 0, 50, 100, 140]) {line(a, [68, Y(t)], [412, Y(t)], '#d5cfbf'); text(a, 60, Y(t) + 4, fmt(t), {'text-anchor': 'end'});}
      for (let i = 0; i <= 4; i++) {
        const q = m.limits.min + (m.limits.max - m.limits.min) * i / 4;
        line(a, [X(q), 96], [X(q), 334], '#d5cfbf'); text(a, X(q), 356, Number(q.toPrecision(4)).toString(), {'text-anchor': 'middle', 'font-size': 12});
      }
      line(a, [X(0), 96], [X(0), 334], '#8b7e66', {'stroke-dasharray': '4 4', 'data-phase-zero': ''});
      for (let i = 0; i < 5; i++) {
        const p = m.points[i], next = m.points[i + 1];
        a.append(sn('path', {d: `M${X(p.energy)} ${Y(p.temperature)} L${X(next.energy)} ${Y(next.temperature)}`, fill: 'none', stroke: stages[i].color, 'stroke-width': 3, 'data-phase-segment': stages[i].key}));
      }
      a.append(sn('circle', {cx: X(0), cy: Y(m.start.temperature), r: 5, fill: '#f5efdf', stroke: '#263b46', 'stroke-width': 2, 'data-phase-marker': 'start'}),
        sn('circle', {cx: X(s.energy), cy: Y(m.temperature), r: 5, fill: '#263b46', stroke: '#fff', 'stroke-width': 1.5, 'data-phase-marker': 'current'}));
      text(a, 240, 386, 'Signed heat Q since start (kJ)', {'text-anchor': 'middle'});
      text(a, 240, 408, '○ start (Q = 0)    ● current sample', {'text-anchor': 'middle'});
      text(b, 18, 51, 'Widths show mass fractions, not volumes.');
      let fractionX = 28;
      for (const [key, color] of [['ice', '#536e87'], ['water', '#317e78'], ['steam', '#b98a2f']]) {
        const fraction = m.fractions[key]; b.append(sn('rect', {x: fractionX, y: 67, width: 384 * fraction, height: 30, fill: color, 'data-phase-fraction': key})); fractionX += 384 * fraction;
      }
      b.append(sn('rect', {x: 28, y: 67, width: 384, height: 30, fill: 'none', stroke: '#263b46', 'stroke-width': 1}));
      [['ice', 'Ice', '#536e87'], ['water', 'Liquid', '#317e78'], ['steam', 'Vapour', '#b98a2f']].forEach(([key, label, color], i) => {
        b.append(sn('rect', {x: 28, y: 111 + i * 22, width: 11, height: 11, fill: color}));
        text(b, 47, 122 + i * 22, `${label}: ${fmt(m.masses[key])} kg (${fmt(100 * m.fractions[key])}%)`);
      });
      text(b, 18, 189, 'Signed parts of Q (kJ)', {'font-weight': 600});
      const scale = s.mass * C.vaporization, B = q => 220 + 170 * q / scale;
      line(b, [220, 201], [220, 379], '#8b7e66', {'stroke-dasharray': '3 3'});
      m.ledger.forEach((row, i) => {
        const y = 212 + i * 34;
        text(b, 28, y, row.label); text(b, 412, y, fmt(row.energy), {'text-anchor': 'end'});
        b.append(sn('rect', {x: Math.min(B(0), B(row.energy)), y: y + 5, width: Math.abs(B(row.energy) - B(0)), height: 13, fill: row.color, 'data-phase-ledger': row.key}));
      });
      text(b, 220, 398, `Each half-axis = ${fmt(scale)} kJ; centre = 0`, {'text-anchor': 'middle', 'font-size': 12});
      if (announce) live.textContent = m.readout;
    }
    refresh(false); return root;
  }
  const api = Object.freeze({CONSTANTS, H, initial, bindings, controls, starts, stages, bounds, normalize, resolve,
    equilibriumAtSpecificEnthalpy: resolve, components, build, render});
  if (typeof window !== 'undefined') window.PrimerPhysicsPhaseLab = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})();
