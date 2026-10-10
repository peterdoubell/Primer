/* Original Carnot/first-law artwork; ideal-gas states determine the plotted paths. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg', R = 8.31446261815324, CV = 1.5 * R, GAMMA = 5 / 3;
  const initial = Object.freeze({mode: 'engine', hot: 600, cold: 300, moles: .1, volume: .001,
    hotHeat: 400, leak: 0, leg: 0, progress: 0, heat: 500, work: 200});
  const cycleModes = ['engine', 'refrigerator'];
  const modes = Object.freeze([['engine', 'Heat engine'], ['refrigerator', 'Refrigerator / heat pump'], ['first-law', 'First-law energy budget']]);
  const controls = Object.freeze([
    ['hot', 'Hot reservoir temperature', 250, 1200, 'K', cycleModes],
    ['cold', 'Cold reservoir temperature', 100, 1100, 'K', cycleModes],
    ['moles', 'Amount of ideal monatomic gas', .05, 1, 'mol', cycleModes],
    ['volume', 'Volume at state A', .0005, .01, 'm³', cycleModes],
    ['hotHeat', 'Hot isotherm heat magnitude, gas only', 10, 2000, 'J/cycle', cycleModes],
    ['leak', 'Hot-to-cold heat leak, bypassing the gas', 0, 2000, 'J/cycle', cycleModes],
    ['progress', 'Position along the selected leg (not time)', 0, 100, '%', cycleModes],
    ['heat', 'Heat into the system Q (signed)', -1000, 1000, 'J', ['first-law']],
    ['work', 'Work by the system W_by (signed)', -1000, 1000, 'J', ['first-law']]
  ].map(([key, label, min, max, unit, applicable]) => Object.freeze({key, label, min, max, unit, modes: applicable})));
  const colors = ['#b96652', '#536e87', '#317e78', '#b98a2f'];
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const finite = v => ['number', 'string'].includes(typeof v) && !(typeof v === 'string' && !v.trim()) && Number.isFinite(Number(v));
  const fmt = v => Number(v.toPrecision(6)).toString();
  let serial = 0;

  function controlBounds(key, s) {
    const c = controls.find(c => c.key === key);
    if (key === 'cold') return {min: 100, max: Math.min(1100, s.hot - 10)};
    if (key === 'hotHeat') return {min: 10, max: Math.min(2000, s.moles * R * s.hot * Math.log(8))};
    return {min: c.min, max: c.max};
  }
  function normalize(raw = {}) {
    const s = {mode: modes.some(m => m[0] === raw.mode) ? raw.mode : initial.mode};
    for (const c of controls) {
      const limits = controlBounds(c.key, s);
      s[c.key] = finite(raw[c.key]) ? clamp(Number(raw[c.key]), limits.min, limits.max) : clamp(initial[c.key], limits.min, limits.max);
    }
    s.leg = finite(raw.leg) ? Math.round(clamp(Number(raw.leg), 0, 3)) : 0;
    return s;
  }
  function cycleData(s) {
    const logExpansion = s.hotHeat / (s.moles * R * s.hot);
    const logAdiabatic = Math.log1p((s.hot - s.cold) / s.cold) / (GAMMA - 1);
    const ratio = Math.exp(logExpansion), factor = Math.exp(logAdiabatic), entropySwing = s.hotHeat / s.hot;
    const gasState = (name, V, T, S) => ({name, V, T, p: s.moles * R * T / V, U: s.moles * CV * T, S});
    const corners = [gasState('A', s.volume, s.hot, 0), gasState('B', s.volume * ratio, s.hot, entropySwing),
      gasState('C', s.volume * factor * ratio, s.cold, entropySwing), gasState('D', s.volume * factor, s.cold, 0)];
    const coldGasHeat = s.hotHeat * s.cold / s.hot, adiabaticEnergy = s.moles * CV * (s.hot - s.cold);
    const specifications = [
      {kind: 'isothermal', reservoir: 'hot', from: 0, to: 1, Q: s.hotHeat, Wby: s.hotHeat, deltaU: 0, deltaS: entropySwing, logVolumeRatio: logExpansion},
      {kind: 'adiabatic', reservoir: null, from: 1, to: 2, Q: 0, Wby: adiabaticEnergy, deltaU: -adiabaticEnergy, deltaS: 0, logVolumeRatio: logAdiabatic},
      {kind: 'isothermal', reservoir: 'cold', from: 2, to: 3, Q: -coldGasHeat, Wby: -coldGasHeat, deltaU: 0, deltaS: -entropySwing, logVolumeRatio: -logExpansion},
      {kind: 'adiabatic', reservoir: null, from: 3, to: 0, Q: 0, Wby: -adiabaticEnergy, deltaU: adiabaticEnergy, deltaS: 0, logVolumeRatio: -logAdiabatic}
    ];
    const forward = specifications.map((leg, i) => ({...leg, from: corners[leg.from], to: corners[leg.to], color: colors[i]}));
    const legs = s.mode === 'refrigerator' ? [...forward].reverse().map(leg => ({...leg, from: leg.to, to: leg.from,
      Q: leg.Q === 0 ? 0 : -leg.Q, Wby: -leg.Wby, deltaU: leg.deltaU === 0 ? 0 : -leg.deltaU,
      deltaS: leg.deltaS === 0 ? 0 : -leg.deltaS, logVolumeRatio: -leg.logVolumeRatio})) : forward;
    legs.forEach((leg, index) => {leg.index = index; leg.label = leg.from.name + ' → ' + leg.to.name + ': ' +
      (leg.kind === 'isothermal' ? (leg.reservoir === 'hot' ? 'hot' : 'cold') + ' isotherm' : 'reversible adiabat');});
    return {corners, legs, logExpansion, logAdiabatic, ratio, factor, entropySwing, coldGasHeat};
  }
  function atLeg(s, leg, fraction) {
    const u = fraction, from = leg.from, to = leg.to;
    const V = u === 0 ? from.V : u === 1 ? to.V : from.V * Math.exp(leg.logVolumeRatio * u);
    let T, deltaU;
    if (leg.kind === 'isothermal') {T = from.T; deltaU = 0;}
    else {
      const deltaT = from.T * Math.expm1(-(GAMMA - 1) * leg.logVolumeRatio * u);
      T = u === 0 ? from.T : u === 1 ? to.T : from.T + deltaT;
      deltaU = u === 0 ? 0 : u === 1 ? leg.deltaU : s.moles * CV * deltaT;
    }
    const Q = leg.kind === 'isothermal' ? leg.Q * u : 0, Wby = leg.kind === 'isothermal' ? Q : deltaU === 0 ? 0 : -deltaU;
    const deltaS = leg.deltaS * u;
    return {V, T, p: s.moles * R * T / V, U: s.moles * CV * T, S: from.S + deltaS,
      Q, Wby, deltaU, deltaS, leg: leg.index, fraction: u};
  }
  function stateAtLeg(raw, legIndex, fraction) {
    const s = normalize(raw);
    if (s.mode === 'first-law' || !Number.isInteger(legIndex) || legIndex < 0 || legIndex > 3 ||
        !finite(fraction) || Number(fraction) < 0 || Number(fraction) > 1) throw new RangeError('A cycle leg 0…3 and fraction 0…1 are required');
    return atLeg(s, cycleData(s).legs[legIndex], Number(fraction));
  }
  function build(raw = {}) {
    const state = normalize(raw), s = state;
    if (s.mode === 'first-law') {
      const deltaU = s.heat - s.work;
      return {state, Q: s.heat, Wby: s.work, deltaU, workOn: -s.work,
        readout: `Heat into the system Q = ${fmt(s.heat)} joules. Work by the system = ${fmt(s.work)} joules; work on it = ${fmt(-s.work)} joules. ` +
          `Internal-energy change = Q − W_by = ${fmt(deltaU)} joules. ` + (s.heat === 0 && s.work < 0 ? 'Insulation prevents heat transfer; work on the system still raises its internal energy. For an ideal gas this raises temperature.' : ''),
        equation: 'ΔU = Q − W_by = Q + W_on. Positive Q enters; positive W_by leaves as work.',
        note: 'These are prescribed signed energy transfers for a process, not an asserted cycle. A budget alone does not determine pressure, volume, temperature, entropy or a reversible path. Rapid insulated compression has Q ≈ 0 and can raise an ideal gas temperature through work, but its detailed nonequilibrium pressure history is not calculated here.'};
    }
    const data = cycleData(s), direction = s.mode === 'engine' ? 1 : -1;
    const workMagnitude = s.hotHeat * (s.hot - s.cold) / s.hot, Wby = direction * workMagnitude;
    const hotReservoirHeat = -direction * s.hotHeat - s.leak, coldReservoirHeat = direction * data.coldGasHeat + s.leak;
    const hotReservoirEntropy = -direction * data.entropySwing - s.leak / s.hot;
    const coldReservoirEntropy = direction * data.entropySwing + s.leak / s.cold;
    const entropyProduced = s.leak * (s.hot - s.cold) / (s.hot * s.cold);
    const totalHotInput = s.hotHeat + s.leak, totalColdRejection = data.coldGasHeat + s.leak;
    const coldExtraction = data.coldGasHeat - s.leak, hotDelivery = s.hotHeat - s.leak;
    const efficiency = s.mode === 'engine' ? workMagnitude / totalHotInput : null;
    const cop = s.mode === 'refrigerator' && coldExtraction >= 0 ? coldExtraction / workMagnitude : null;
    const heatPumpCop = s.mode === 'refrigerator' && hotDelivery >= 0 ? hotDelivery / workMagnitude : null;
    const current = atLeg(s, data.legs[s.leg], s.progress / 100);
    const legs = data.legs.map(leg => ({...leg, points: Array.from({length: 121}, (_, i) => atLeg(s, leg, i / 120))}));
    const plot = {maxV: Math.max(...data.corners.map(q => q.V)) * 1.06, maxP: Math.max(...data.corners.map(q => q.p)) * 1.08};
    const summary = s.mode === 'engine' ? `Hot reservoir supplies ${fmt(totalHotInput)} joules, including a ${fmt(s.leak)} joule bypass leak. ` +
      `Cold reservoir receives ${fmt(totalColdRejection)} joules. Net work out = ${fmt(workMagnitude)} joules; efficiency = ${fmt(100 * efficiency)} percent. ` :
      `Work input = ${fmt(workMagnitude)} joules. Gas removes ${fmt(data.coldGasHeat)} joules from the cold reservoir and rejects ${fmt(s.hotHeat)} joules to the hot reservoir. ` +
      `The leak returns ${fmt(s.leak)} joules hot to cold. Net cold extraction = ${fmt(coldExtraction)} joules; net hot delivery = ${fmt(hotDelivery)} joules. ` +
      (cop === null ? 'The cold reservoir is heated overall, so this device is not refrigerating and its useful refrigeration COP is unavailable. ' : `Refrigeration COP = ${fmt(cop)}. `) +
      `If both heat exchangers are inside one kitchen, its net gain is ${fmt(workMagnitude)} joules per cycle, equal to compressor work. `;
    return {state, ...data, legs, current, plot, direction, Q: direction * (s.hotHeat - data.coldGasHeat), Wby, deltaU: 0,
      workMagnitude, gasHotHeat: direction * s.hotHeat, gasColdHeat: -direction * data.coldGasHeat,
      hotReservoirHeat, coldReservoirHeat, hotReservoirEntropy, coldReservoirEntropy, entropyProduced, gasCycleEntropy: 0,
      totalHotInput: s.mode === 'engine' ? totalHotInput : null,
      totalColdRejection: s.mode === 'engine' ? totalColdRejection : null,
      coldExtraction: s.mode === 'refrigerator' ? coldExtraction : null,
      hotDelivery: s.mode === 'refrigerator' ? hotDelivery : null, efficiency, cop, heatPumpCop,
      carnotEfficiency: (s.hot - s.cold) / s.hot, carnotCop: s.cold / (s.hot - s.cold), roomHeat: s.mode === 'refrigerator' ? workMagnitude : null,
      readout: `${s.moles} moles of ideal monatomic gas, hot ${fmt(s.hot)} kelvin and cold ${fmt(s.cold)} kelvin. ` + summary +
        `Per completed cycle: gas internal-energy change = 0 joules; hot reservoir entropy change = ${fmt(hotReservoirEntropy)} joules per kelvin; ` +
        `cold reservoir entropy change = ${fmt(coldReservoirEntropy)} joules per kelvin; gas entropy change = 0; total entropy produced = ${fmt(entropyProduced)} joules per kelvin. ` +
        `Selected ${data.legs[s.leg].label}, position ${fmt(s.progress)} percent: volume ${fmt(current.V)} cubic metres, pressure ${fmt(current.p)} pascals, temperature ${fmt(current.T)} kelvin. ` +
        `Since this leg began: Q = ${fmt(current.Q)} joules, W_by = ${fmt(current.Wby)} joules, ΔU = ${fmt(current.deltaU)} joules.`,
      equation: 'pV = nRT; U = n C_v T; ΔU = Q − W_by; W_by = ∫p dV. Isotherm: W_by = nRT ln(V_end/V_start). Reversible adiabat: T V^(γ−1) = constant.',
      note: 'A hypothetical classical monatomic ideal gas has fixed C_v = 3R/2 and γ = 5/3. The four Carnot legs are quasistatic and reversible, with insulated adiabats and isothermal heat exchange at the matching reservoir temperature. These equilibrium adiabats are not a rapid-compression transient. Reverse operation follows the same path backward. Reservoirs remain at fixed absolute temperatures; gas entropy is referenced to state A. A separately prescribed heat leak L goes directly hot to cold, bypassing the gas, and generates L(1/T_c−1/T_h) entropy per completed cycle. It changes neither the gas p–V path nor its work. Path position is not elapsed time; the per-cycle leak is not allocated to a particular gas leg. Friction, finite-rate gas heat exchange, leaks through the working gas and realistic material properties are omitted. The open-fridge kitchen statement is a whole-room energy boundary, not a solved evolving room-temperature model. Mixing of water or ink needs a separate entropy model.'};
  }
  function el(tag, attrs = {}, ...children) {const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v)); for (const c of children) if (c != null) e.append(c.nodeType ? c : document.createTextNode(String(c))); return e;}
  function sn(tag, attrs = {}, value) {const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v)); if (value != null) e.textContent = String(value); return e;}
  function render(item, hooks) {
    if (item?.props?.scenario !== 'phys.3.thermo.cycle-entropy' || Object.keys(item.props).length !== 1) return null;
    const uid = 'cycle-' + ++serial, root = el('section', {class: 'card lesson-model physics-cycle-lab', 'data-renderer': 'physics-cycle-lab', 'aria-labelledby': uid + '-title'});
    let model = build(initial);
    const mode = el('select', {id: uid + '-mode', 'data-cycle-mode': ''}); for (const [key, label] of modes) mode.append(el('option', {value: key}, label));
    mode.addEventListener('change', () => {model = build({...model.state, mode: mode.value, leg: 0, progress: 0}); refresh(true);});
    const inputs = el('div', {class: 'model-controls concept-controls'}), widgets = new Map();
    inputs.append(el('label', {for: uid + '-mode', class: 'cycle-select-control'}, 'System and operating mode', mode));
    const leg = el('select', {id: uid + '-leg', 'data-cycle-leg': ''}), legLabel = el('label', {for: uid + '-leg', class: 'cycle-select-control'}, 'Gas leg to inspect', leg);
    inputs.append(legLabel); leg.addEventListener('change', () => {model = build({...model.state, leg: Number(leg.value), progress: 0}); refresh(true);});
    for (const c of controls) {
      const id = uid + '-' + c.key, range = el('input', {id, type: 'range', step: 'any', 'data-cycle-control': c.key}), output = el('output', {for: id});
      const number = el('input', {type: 'number', step: 'any', 'aria-label': c.label + ' numeric entry', 'data-cycle-number': c.key});
      const label = el('label', {for: id, class: 'model-range-control'}, c.label, output, range, number);
      range.addEventListener('input', () => {model = build({...model.state, [c.key]: range.value}); refresh(false);}); range.addEventListener('change', () => {live.textContent = model.readout;});
      number.addEventListener('change', () => {model = build({...model.state, [c.key]: number.value}); refresh(true);});
      widgets.set(c.key, {label, range, number, output, c}); inputs.append(label);
    }
    const buttons = el('div', {class: 'model-button-row'});
    for (const [key, label, patch] of [
      ['reversible', 'Reversible 600/300 K engine', initial], ['quiz-engine', 'Quiz: 800 J in / 600 J out', {...initial, leak: 400}],
      ['fridge', 'Ideal refrigerator', {...initial, mode: 'refrigerator'}],
      ['first-law-300', 'First law: 500 − 200 J', {mode: 'first-law', heat: 500, work: 200}],
      ['first-law-250', 'First law: −150 + 400 J', {mode: 'first-law', heat: -150, work: -400}],
      ['compression', 'Insulated compression budget', {mode: 'first-law', heat: 0, work: -400}]
    ]) {const b = el('button', {type: 'button', class: 'btn ghost small', 'data-cycle-preset': key}, label); b.addEventListener('click', () => {model = build({...model.state, ...patch}); refresh(true);}); buttons.append(b);}
    const stopCooling = el('button', {type: 'button', class: 'btn ghost small', 'data-cycle-action': 'cancel-cooling'}, 'Leak cancels refrigeration');
    stopCooling.addEventListener('click', () => {model = build({...model.state, mode: 'refrigerator', leak: model.state.hotHeat * model.state.cold / model.state.hot}); refresh(true);}); buttons.append(stopCooling);
    const reset = el('button', {type: 'button', class: 'btn ghost small', 'data-cycle-action': 'reset'}, 'Reset'); reset.addEventListener('click', () => {model = build(initial); refresh(true);}); buttons.append(reset);
    const enlarge = el('button', {type: 'button', class: 'btn ghost small', 'data-cycle-action': 'enlarge', 'aria-pressed': 'false'}, 'Enlarge plots');
    enlarge.addEventListener('click', () => {const on = enlarge.getAttribute('aria-pressed') !== 'true'; enlarge.setAttribute('aria-pressed', String(on)); root.classList.toggle('is-enlarged', on); enlarge.textContent = on ? 'Fit plots' : 'Enlarge plots';});
    const limits = el('p', {class: 'spatial-note cycle-limits'}), readout = el('p', {class: 'cycle-readout'}), equation = el('p', {class: 'cycle-equation'}), note = el('p', {class: 'spatial-note'});
    const live = el('p', {class: 'cycle-live', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true'});
    const panels = el('div', {class: 'cycle-panels'}), views = [], viewports = [];
    for (let i = 0; i < 2; i++) {const svg = sn('svg', {viewBox: '0 0 440 420', role: 'img', 'aria-labelledby': uid + '-svg-title-' + i, 'aria-describedby': uid + '-svg-desc-' + i}), viewport = el('div', {class: 'cycle-viewport', tabindex: 0, role: 'region', 'aria-label': i ? 'Signed reservoir entropy; enlarge and scroll' : 'Pressure-volume path or first-law budget; enlarge and scroll'}, svg); views.push(svg); viewports.push(viewport); panels.append(viewport);}
    const tableBody = el('tbody'), table = el('table', {class: 'cycle-leg-table'}, el('caption', {}, 'Working gas only: complete leg balances (the bypass leak is excluded)'),
      el('thead', {}, el('tr', {}, ...['Leg', 'Q (J)', 'W_by (J)', 'ΔU (J)', 'ΔS_gas (J/K)'].map(v => el('th', {scope: 'col'}, v)))), tableBody);
    const tableRegion = el('div', {class: 'cycle-table-region', tabindex: 0, role: 'region', 'aria-label': 'Leg energy and entropy balances; scroll horizontally'}, table);
    root.append(el('div', {class: 'model-heading-row'}, el('h3', {id: uid + '-title'}, item.title || 'Follow the gas, work and entropy'), enlarge),
      el('p', {class: 'model-instructions'}, item.instructions || 'Follow all four reversible gas legs. Reverse the cycle or add a heat leak, then compare the gas and reservoir ledgers.'), inputs, limits, buttons, panels, tableRegion, equation, readout,
      el('details', {class: 'cycle-assumptions'}, el('summary', {}, 'Model assumptions and boundaries'), note,
        el('p', {class: 'spatial-note'}, el('a', {href: 'https://openstax.org/books/university-physics-volume-2/pages/4-5-the-carnot-cycle', target: '_blank', rel: 'noopener noreferrer'}, 'Carnot cycle'), ' · ',
          el('a', {href: 'https://openstax.org/books/university-physics-volume-2/pages/3-6-adiabatic-processes-for-an-ideal-gas', target: '_blank', rel: 'noopener noreferrer'}, 'Quasistatic adiabats'), ' · ',
          el('a', {href: 'https://openstax.org/books/university-physics-volume-2/pages/4-6-entropy', target: '_blank', rel: 'noopener noreferrer'}, 'Entropy'), ' · ',
          el('a', {href: 'https://physics.nist.gov/cuu/pdf/all.pdf', target: '_blank', rel: 'noopener noreferrer'}, 'NIST gas constant'), '. Original artwork; no source figure copied.')), live);
    if (hooks?.speakButton) root.append(hooks.speakButton(() => model.readout + ' ' + model.equation));
    function text(svg, x, y, value, attrs = {}) {svg.append(sn('text', {x, y, fill: '#263b46', 'font-size': 13, ...attrs}, value));}
    function line(svg, a, b, color, attrs = {}) {svg.append(sn('line', {x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: color, 'stroke-width': 1.5, ...attrs}));}
    function setup(i, title) {const svg = views[i]; svg.replaceChildren(sn('title', {id: uid + '-svg-title-' + i}, title), sn('desc', {id: uid + '-svg-desc-' + i}, model.readout), sn('rect', {x: 0, y: 0, width: 440, height: 420, rx: 10, fill: '#f5efdf'})); text(svg, 18, 27, title, {'font-size': 16, 'font-weight': 600}); return svg;}
    function bars(svg, rows, unit) {
      const scale = Math.max(1e-12, ...rows.map(r => Math.abs(r.value))) * 1.12, X = q => 220 + 170 * q / scale;
      line(svg, [220, 72], [220, 347], '#8b7e66', {'stroke-dasharray': '4 4'});
      rows.forEach((r, i) => {const y = 87 + i * 64; text(svg, 28, y, r.label); text(svg, 412, y, fmt(r.value), {'text-anchor': 'end'}); svg.append(sn('rect', {x: Math.min(X(0), X(r.value)), y: y + 12, width: Math.abs(X(r.value) - X(0)), height: 20, fill: r.color, 'data-cycle-balance': r.key, 'data-cycle-axis': scale, 'data-cycle-unit': unit}));});
      text(svg, 220, 377, `Each half-axis = ${fmt(scale)} ${unit}; centre = 0`, {'text-anchor': 'middle', 'font-size': 12});
    }
    function refresh(announce) {
      const m = model, s = m.state, budget = s.mode === 'first-law'; root.setAttribute('data-cycle-state', JSON.stringify(s)); root.classList.toggle('is-first-law', budget); mode.value = s.mode;
      legLabel.hidden = budget; leg.disabled = budget; viewports[1].hidden = budget; tableRegion.hidden = budget;
      for (const w of widgets.values()) {const active = w.c.modes.includes(s.mode), b = controlBounds(w.c.key, s); w.label.hidden = !active; w.range.disabled = w.number.disabled = !active;
        w.range.min = w.number.min = b.min; w.range.max = w.number.max = b.max; w.range.value = w.number.value = s[w.c.key]; w.output.textContent = fmt(s[w.c.key]) + ' ' + w.c.unit; w.range.setAttribute('aria-valuetext', w.output.textContent);}
      limits.textContent = budget ? 'Heat and work each range −1000…1000 J. Positive heat enters; positive work is done by the system. Entries outside the range use its nearest endpoint. A blank numeric entry restores that control’s default.' :
        `Gas model: hot 250–1200 K; cold 100–min(1100, hot − 10) K; amount 0.05–1 mol; V_A 0.0005–0.01 m³. Gas hot-isotherm heat 10–${fmt(controlBounds('hotHeat', s).max)} J (volume ratio ≤ 8); bypass leak 0–2000 J/cycle. Joint limits clamp incompatible inputs. Position selects a path point, not time.`;
      equation.textContent = m.equation; readout.textContent = m.readout; note.textContent = m.note;
      if (budget) {const a = setup(0, 'First-law signed energy ledger'); text(a, 18, 52, 'Energy (J); no pressure–volume path asserted.'); bars(a, [
        {key: 'Q', label: 'Heat into system Q', value: m.Q, color: colors[0]}, {key: '-Wby', label: 'Work into system −W_by', value: -m.Wby, color: colors[1]},
        {key: 'deltaU', label: 'Internal-energy change ΔU', value: m.deltaU, color: colors[2]}], 'J');}
      else {
        leg.replaceChildren(...m.legs.map(l => el('option', {value: l.index}, l.label))); leg.value = s.leg;
        const a = setup(0, 'Working gas: pressure–volume path'), b = setup(1, 'Reservoir entropy per full cycle');
        const X = V => 72 + 340 * V / m.plot.maxV, Y = p => 334 - 244 * p / m.plot.maxP;
        text(a, 18, 52, 'Pressure (Pa)'); text(a, 18, 74, 'A, B: hot; C, D: cold. State A is the reference.');
        for (let i = 0; i <= 4; i++) {const V = m.plot.maxV * i / 4, p = m.plot.maxP * i / 4; line(a, [X(V), 90], [X(V), 334], '#d5cfbf'); line(a, [72, Y(p)], [412, Y(p)], '#d5cfbf'); text(a, X(V), 356, Number(V.toPrecision(3)).toString(), {'text-anchor': 'middle', 'font-size': 11}); text(a, 64, Y(p) + 4, Number(p.toPrecision(3)).toString(), {'text-anchor': 'end', 'font-size': 11});}
        for (const l of m.legs) {a.append(sn('path', {d: l.points.map((p, i) => (i ? 'L' : 'M') + X(p.V) + ' ' + Y(p.p)).join(' '), stroke: l.color, 'stroke-width': 2.5, fill: 'none', 'data-cycle-path': l.index}));
          const halfway = l.points[60], after = l.points[63], dx = X(after.V) - X(halfway.V), dy = Y(after.p) - Y(halfway.p), len = Math.hypot(dx, dy), ux = dx / len, uy = dy / len, x = X(halfway.V), y = Y(halfway.p);
          a.append(sn('path', {d: `M${x - 7 * ux + 4 * uy} ${y - 7 * uy - 4 * ux} L${x} ${y} L${x - 7 * ux - 4 * uy} ${y - 7 * uy + 4 * ux}`, fill: 'none', stroke: l.color, 'stroke-width': 2, 'data-cycle-direction': l.index}));
        }
        const placed = [];
        for (const q of m.corners) {
          const px = X(q.V), py = Y(q.p); a.append(sn('circle', {cx: px, cy: py, r: 3, fill: '#263b46', 'data-cycle-corner': q.name}));
          let best, score = Infinity;
          for (const [dx, dy] of [[-14, -10], [8, -10], [8, 18], [-14, 18], [-14, -28], [8, -28], [-30, 9], [24, 9]]) {
            const x = clamp(px + dx, 80, 415), y = clamp(py + dy, 105, 326), box = {left: x, right: x + 10, top: y - 13, bottom: y + 3};
            const overlaps = placed.filter(b => box.left < b.right + 3 && box.right + 3 > b.left && box.top < b.bottom + 3 && box.bottom + 3 > b.top).length;
            const value = overlaps * 1e6 + Math.hypot(x + 5 - px, y - 5 - py);
            if (value < score) {best = {x, y, box}; score = value;}
          }
          placed.push(best.box);
          if (Math.hypot(best.x + 5 - px, best.y - 5 - py) > 14) line(a, [px, py], [best.x + 5, best.y - 5], '#8b7e66', {'stroke-width': .8});
          text(a, best.x, best.y, q.name, {'font-weight': 600, 'data-cycle-label': q.name});
        }
        a.append(sn('circle', {cx: X(m.current.V), cy: Y(m.current.p), r: 5, fill: '#263b46', stroke: '#fff', 'stroke-width': 1.5, 'data-cycle-marker': ''}));
        text(a, 242, 386, 'Volume (m³)', {'text-anchor': 'middle'}); text(a, 242, 408, 'Arrows show cycle direction; axes rescale.', {'text-anchor': 'middle', 'font-size': 12});
        text(b, 18, 52, 'Signed entropy changes (J/K)'); bars(b, [
          {key: 'hot', label: 'Hot reservoir ΔS', value: m.hotReservoirEntropy, color: colors[0]},
          {key: 'cold', label: 'Cold reservoir ΔS', value: m.coldReservoirEntropy, color: colors[2]},
          {key: 'gas', label: 'Working gas, full cycle ΔS', value: 0, color: colors[1]},
          {key: 'produced', label: 'Total entropy produced', value: m.entropyProduced, color: colors[3]}], 'J/K');
        text(b, 220, 408, 'Leak bypasses gas; reservoirs include it.', {'text-anchor': 'middle', 'font-size': 12});
        tableBody.replaceChildren(...m.legs.map(l => el('tr', {'data-cycle-leg-row': l.index}, el('th', {scope: 'row'}, l.label), ...[l.Q, l.Wby, l.deltaU, l.deltaS].map(v => el('td', {}, fmt(v))))),
          el('tr', {class: 'cycle-total-row'}, el('th', {scope: 'row'}, 'Gas, full cycle'), ...[m.Q, m.Wby, 0, 0].map(v => el('td', {}, fmt(v)))));
      }
      if (announce) live.textContent = m.readout;
    }
    refresh(false); return root;
  }
  const api = Object.freeze({R, CV, GAMMA, initial, controls, modes, controlBounds, normalize, cycleData, stateAtLeg, build, render});
  if (typeof window !== 'undefined') window.PrimerPhysicsCycleLab = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})();
