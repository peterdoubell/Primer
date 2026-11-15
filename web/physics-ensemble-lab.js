/* Original equilibrium/counting artwork. No sampled molecular dynamics. */
(function () {
  'use strict';
  const K = 1.380649e-23, NS = 'http://www.w3.org/2000/svg', MAX_N = 1024;
  const scenario = 'phys.4.statmech.ensembles-entropy';
  const modes = [['canonical', 'One canonical two-level site'], ['coins', 'Fair distinguishable coins'],
    ['particles', 'Independent canonical two-level sites'], ['expansion', 'Ideal-gas free expansion'], ['blocks', 'Two isolated thermal blocks']];
  const initial = Object.freeze({mode: 'canonical', temperature: 300, gap: K * 300 / 1e-21, N: 4, j: 2,
    log10N: 4, volumeRatio: 2, tempA: 600, tempB: 300, capacityA: 100, capacityB: 100, transfer: 100});
  const controls = Object.freeze([
    ['temperature', 'Reservoir temperature', 1, 1200, 'K', ['canonical', 'particles']],
    ['gap', 'Upper-minus-lower energy gap', 0, 100, 'zJ (10⁻²¹ J)', ['canonical', 'particles']],
    ['N', 'Distinguishable coins or sites', 1, MAX_N, 'count', ['coins', 'particles']],
    ['j', 'Selected heads or upper-state count', 0, MAX_N, 'count', ['coins', 'particles']],
    ['log10N', 'Particle count N = 10 to this integer power', 0, 25, 'power of ten', ['expansion']],
    ['volumeRatio', 'Final / initial accessible volume', 1, 10, 'dimensionless', ['expansion']],
    ['tempA', 'Initial temperature of block A', 1, 1200, 'K', ['blocks']],
    ['tempB', 'Initial temperature of block B', 1, 1200, 'K', ['blocks']],
    ['capacityA', 'Constant heat capacity of block A', 1, 1000, 'J/K', ['blocks']],
    ['capacityB', 'Constant heat capacity of block B', 1, 1000, 'J/K', ['blocks']],
    ['transfer', 'Fraction of equilibrium heat transfer (not time)', 0, 100, '%', ['blocks']]
  ].map(([key, label, min, max, unit, applicable]) => Object.freeze({key, label, min, max, unit, modes: applicable,
    integer: ['N', 'j', 'log10N'].includes(key)})));
  const finite = x => (typeof x === 'number' || typeof x === 'string' && x.trim() !== '') && Number.isFinite(Number(x));
  const clamp = (x, lo, hi) => Math.min(hi, Math.max(lo, x));
  const fmt = x => Number(x.toPrecision(7)).toString();
  const sum = xs => {let total = 0, correction = 0; for (const x of xs) {const y = x - correction, t = total + y; correction = (t - total) - y; total = t;} return total;};
  let serial = 0;
  function bounds(key, s) {
    const c = controls.find(c => c.key === key);
    if (key === 'gap') return {min: 0, max: Math.min(100, 40 * K * s.temperature / 1e-21)};
    if (key === 'j') return {min: 0, max: s.N};
    return {min: c.min, max: c.max};
  }
  function normalize(raw = {}) {
    const s = {mode: modes.some(([id]) => id === raw.mode) ? raw.mode : initial.mode};
    for (const c of controls) {const b = bounds(c.key, s); let v = finite(raw[c.key]) ? Number(raw[c.key]) : initial[c.key]; if (c.integer) v = Math.round(v); s[c.key] = clamp(v, b.min, b.max);}
    return s;
  }
  function choose(n, j) {
    if (!Number.isInteger(n) || n < 0 || n > MAX_N || !Number.isInteger(j) || j < 0 || j > n) throw new RangeError('Integer 0 ≤ j ≤ N ≤ 1024 required');
    let value = 1n; for (let i = 1; i <= Math.min(j, n - j); i++) value = value * BigInt(n - i + 1) / BigInt(i); return value;
  }
  function logBigInt(value) {
    if (typeof value !== 'bigint' || value < 1n) throw new RangeError('A positive exact integer is required');
    const text = value.toString(), head = text.slice(0, 15); return Math.log(Number(head)) + (text.length - head.length) * Math.LN10;
  }
  function probability(logP, symbolic = '') {
    const log = Math.min(0, logP), computed = Math.exp(log), value = computed > 0 ? computed : null;
    const log10 = log / Math.LN10;
    let display = log === 0 ? '1' : value === null ? 'positive; ln P ≈ ' + fmt(log) + ', log₁₀ P ≈ ' + fmt(log10) :
      '≈ ' + fmt(value) + (value < 1e-6 || value === 1 ? '; ln P ≈ ' + fmt(log) : '');
    if (symbolic) display = symbolic + ' (' + display + ')';
    return {log, log10, value, positive: true, symbolic, display};
  }
  function canonical(s) {
    const energyGapJ = s.gap * 1e-21, x = energyGapJ / (K * s.temperature), factor = Math.exp(-x), logZ = Math.log1p(factor);
    const pUpper = factor / (1 + factor), pLower = 1 / (1 + factor), logUpper = -x - logZ, logLower = -logZ;
    const gibbsOverK = logZ + x * pUpper;
    return {x, energyGapJ, Z: 1 + factor, logZ, pUpper, pLower, logUpper, logLower,
      upperProbability: probability(logUpper), lowerProbability: probability(logLower), populationRatio: probability(-x),
      meanEnergyJ: energyGapJ * pUpper, gibbsOverK, gibbsEntropyJPerK: K * gibbsOverK};
  }
  function enumerate(n, x = 0) {
    if (!Number.isInteger(n) || n < 0 || n > 8) return [];
    const logZ = Math.log1p(Math.exp(-x));
    return Array.from({length: 2 ** n}, (_, index) => {
      const bits = n ? index.toString(2).padStart(n, '0') : '', j = [...bits].filter(b => b === '1').length;
      return {bits, j, logP: -j * x - n * logZ};
    });
  }
  function binomial(s) {
    const c = canonical(s.mode === 'coins' ? {...s, gap: 0} : s), x = c.x, logZ = c.logZ;
    let omega = 1n;
    const rows = Array.from({length: s.N + 1}, (_, j) => {
      if (j) omega = omega * BigInt(s.N - j + 1) / BigInt(j);
      const logOmega = logBigInt(omega), perMicrostateLogP = -j * x - s.N * logZ, macroLogP = logOmega + perMicrostateLogP;
      return {j, omega, logOmega, perMicrostateLogP, macroLogP, probability: probability(macroLogP,
        s.mode === 'coins' ? omega.toString() + ' / 2^' + s.N : '')};
    });
    const macroGibbsOverK = sum(rows.map(r => -(r.probability.value || 0) * r.macroLogP));
    const meanMultiplicityOverK = sum(rows.map(r => (r.probability.value || 0) * r.logOmega));
    const pUpper = s.mode === 'coins' ? .5 : c.pUpper, selected = rows[s.j];
    const microGibbsOverK = s.N * (s.mode === 'coins' ? Math.LN2 : c.gibbsOverK);
    return {...c, x, pUpper, pLower: s.mode === 'coins' ? .5 : c.pLower, rows, selected,
      omega: selected.omega, totalStates: 2n ** BigInt(s.N), multiplicityOverK: selected.logOmega,
      macroLogP: selected.macroLogP, perMicrostateLogP: selected.perMicrostateLogP,
      macroProbability: selected.probability, microProbability: probability(selected.perMicrostateLogP,
        s.mode === 'coins' ? '1 / 2^' + s.N : ''),
      microGibbsOverK, macroGibbsOverK, meanMultiplicityOverK,
      entropyDecompositionResidual: microGibbsOverK - macroGibbsOverK - meanMultiplicityOverK,
      meanUpperCount: s.N * pUpper, varianceUpperCount: s.N * pUpper * (1 - pUpper), enumeration: enumerate(s.N, x)};
  }
  function expansion(s) {
    const particleCount = 10n ** BigInt(s.log10N), n = Number(particleCount), logRatio = Math.log(s.volumeRatio), entropyOverK = n * logRatio;
    return {particleCount, entropyOverK, entropyJPerK: K * entropyOverK, Q: 0, Wby: 0, deltaU: 0, deltaT: 0,
      pressureRatio: 1 / s.volumeRatio, logP: -entropyOverK,
      allInOriginalProbability: probability(-entropyOverK, s.volumeRatio === 2 ? '2^(−' + particleCount + ')' :
        s.volumeRatio === 1 ? '1' : fmt(s.volumeRatio) + '^(−' + particleCount + ')')};
  }
  // Avoid cancellation in ln(1+x)−x for almost equal block temperatures.
  function log1pMinusX(x) {if (Math.abs(x) >= .01) return Math.log1p(x) - x; let value = 0, power = x * x; for (let k = 2; k <= 18; k++) {value += (k % 2 ? 1 : -1) * power / k; power *= x;} return value;}
  function blocks(s) {
    const capacitySum = s.capacityA + s.capacityB, difference = s.tempA - s.tempB;
    const Tf = s.tempA + s.capacityB / capacitySum * (s.tempB - s.tempA), fraction = s.transfer / 100;
    const heatToB = fraction * s.capacityA * s.capacityB / capacitySum * difference;
    const tempA = s.tempA - heatToB / s.capacityA, tempB = s.tempB + heatToB / s.capacityB;
    const a = -heatToB / (s.capacityA * s.tempA), b = heatToB / (s.capacityB * s.tempB);
    const entropyA = s.capacityA * Math.log1p(a), entropyB = s.capacityB * Math.log1p(b);
    const totalEntropy = heatToB * difference / (s.tempA * s.tempB) + s.capacityA * log1pMinusX(a) + s.capacityB * log1pMinusX(b);
    return {Tf, fraction, tempA, tempB, heatA: -heatToB, heatB: heatToB, totalEnergyChange: 0,
      entropyA, entropyB, totalEntropy: totalEntropy === 0 ? 0 : totalEntropy};
  }
  function build(raw = {}) {
    const state = normalize(raw), s = state;
    if (s.mode === 'canonical') {const m = canonical(s); return {state, ...m,
      equation: 'P₁/P₀ = exp(−ΔE/k_B T); Z₁ = 1 + exp(−ΔE/k_B T); P₁ = exp(−ΔE/k_B T)/Z₁; S_G/k_B = ln Z₁ + ⟨E⟩/(k_B T).',
      readout: 'One labelled state at zero energy and a second labelled state at ' + fmt(m.energyGapJ) + ' joules, at ' + fmt(s.temperature) + ' kelvin. ' +
        'Gap divided by k_B T = ' + fmt(m.x) + '. Upper/lower population ratio ' + m.populationRatio.display + '. Normalized upper probability ' + m.upperProbability.display +
        '; lower probability ' + m.lowerProbability.display + '. Mean energy ≈ ' + fmt(m.meanEnergyJ) + ' joules. Gibbs ensemble entropy divided by k_B ≈ ' + fmt(m.gibbsOverK) + '.',
      note: 'Two distinct labelled states in canonical equilibrium with a large positive-temperature reservoir. A positive gap gives one state at each energy; gap zero makes their energies equal. Energy zero is the lower state; 1 zJ = 10⁻²¹ J. The ratio of two populations is not the normalized upper probability. Every finite positive temperature and finite gap has a positive upper probability. The displayed domain limits ΔE/(k_B T) to 0…40; changing T can clamp the gap. At gap zero both probabilities are exactly 1/2. For a fixed positive gap the analytic T→∞ limit is 1/2 and T→0⁺ limit is zero, but neither infinite nor zero temperature is a selectable state. Rounded graphics can hide a small positive population. No occupancy kinetics, time fractions or ergodicity assumption is calculated.'};}
    if (s.mode === 'coins' || s.mode === 'particles') {const m = binomial(s), coins = s.mode === 'coins'; return {state, ...m,
      equation: 'Ω_j = C(N,j); P(j) = Ω_j P₁^j P₀^(N−j); S_j/k_B = ln Ω_j; S_G/k_B = N h(P₁) = H(j) + Σ_j P(j) ln Ω_j.',
      readout: s.N + (coins ? ' distinguishable independent fair coins' : ' independent distinguishable noninteracting two-level sites in canonical equilibrium') +
        '. Selected ' + s.j + (coins ? ' heads' : ' upper states') + ' have exact multiplicity ' + m.omega + ' among ' + m.totalStates + ' possible binary microstates. ' +
        'Selected macrostate probability ' + m.macroProbability.display + '. Each microstate within it has probability ' + m.microProbability.display + '. ' +
        'Selected multiplicity entropy divided by k_B ≈ ' + fmt(m.multiplicityOverK) + '; full microstate Gibbs ensemble entropy divided by k_B ≈ ' + fmt(m.microGibbsOverK) +
        '; entropy of just the count distribution ≈ ' + fmt(m.macroGibbsOverK) + '. Mean upper/head count ≈ ' + fmt(m.meanUpperCount) + '. ' +
        (coins ? 'Coins are a dimensionless counting analogy; no coin heat or temperature is assigned.' : 'Gap ≈ ' + fmt(m.energyGapJ) + ' joules; temperature ' + fmt(s.temperature) + ' kelvin; single-site upper probability ' + m.upperProbability.display + '.'),
      note: 'N labels distinguish independent sites or coins; interactions and Bose/Fermi exchange are omitted. Ω_j is an exact integer, including at N=1024. Logarithms, entropy and canonical probabilities are floating-point approximations. All possible binary strings are accessible. Fair-coin strings have equal probability 2⁻ᴺ; canonical strings with different j generally have unequal probabilities. Given j, fair-coin strings are equiprobable and canonical site strings have equal energy, so their conditional distribution is uniform and ln Ω_j is the conditional multiplicity entropy. It is not the Gibbs entropy of the entire ensemble. H(j) discards which labelled sites are upper; adding the mean ln Ω_j recovers full microstate entropy. The exact N≤8 enumeration shows every binary string, not a simulation. For larger N, the complete count distribution is calculated, while the table lists the selected count, nearby counts and endpoints. Log-probability plots join integer-count points only for legibility; intermediate j is not an allowed macrostate. No observation time or transition rate is inferred.'};}
    if (s.mode === 'expansion') {const m = expansion(s); return {state, ...m,
      equation: 'Q = W_by = ΔU = ΔT = 0; ΔS = N k_B ln(V_f/V_i); P(all N in the specified original region at one instant) = (V_i/V_f)^N.',
      readout: 'Insulated rigid container; ideal gas expands into vacuum from volume V_i to ' + fmt(s.volumeRatio) + ' times V_i. Exact particle count N = ' + m.particleCount +
        '. Heat Q = 0 joules, work by gas = 0 joules, internal-energy change = 0 joules; equilibrium temperature change = 0 kelvin. Entropy increase divided by k_B ≈ ' +
        fmt(m.entropyOverK) + '; entropy increase ≈ ' + fmt(m.entropyJPerK) + ' joules per kelvin. Final / initial equilibrium pressure = ' + fmt(m.pressureRatio) +
        '. At one instant in the final equilibrium ensemble, probability that all particles occupy the specified original region: ' + m.allInOriginalProbability.display + '.',
      note: 'Initial and final equilibrium states of a dilute classical ideal gas in an isolated rigid container. The external boundary does no work; free expansion is irreversible despite Q=0. ΔS is obtained by comparing equilibrium states, not by inserting the actual irreversible heat Q into ΔS=Q/T. Uniform independent equilibrium positions give r⁻ᴺ for one specified original region, not for either half. This calculation does not evolve molecular trajectories, calculate pressure during expansion, infer recurrence/waiting times or assert that return is impossible. N is the exact finite integer 10 to the selected power; decimal entropy and log-probability use a floating-point approximation to N. Even when the probability is too small for a floating-point decimal, its symbolic form and finite logarithm remain. Ratio one is the unchanged-state endpoint with ΔS=0 and probability1. The infinite-N limit at fixed r>1 tends to zero; no finite N is that limit.'};}
    const m = blocks(s); return {state, ...m,
      equation: 'T_f = (C_A T_A + C_B T_B)/(C_A+C_B); Q_A+Q_B = 0; ΔS_i = C_i ln(T_i/T_i,initial).',
      readout: 'Two rigid blocks in an isolated container, with constant positive heat capacities ' + fmt(s.capacityA) + ' and ' + fmt(s.capacityB) + ' joules per kelvin. Initial temperatures ' +
        fmt(s.tempA) + ' and ' + fmt(s.tempB) + ' kelvin; equilibrium temperature ≈ ' + fmt(m.Tf) + ' kelvin. At ' + fmt(s.transfer) + ' percent of the total equilibrium heat transfer (not elapsed time), temperatures are ≈ ' +
        fmt(m.tempA) + ' and ' + fmt(m.tempB) + ' kelvin. Heat into A ≈ ' + fmt(m.heatA) + ' joules; into B ≈ ' + fmt(m.heatB) + ' joules; total energy change = 0 joules. ' +
        'Entropy changes of A and B ≈ ' + fmt(m.entropyA) + ' and ' + fmt(m.entropyB) + ' joules per kelvin; combined entropy change ≈ ' + fmt(m.totalEntropy) + ' joules per kelvin.',
      note: 'Each block is internally at a uniform equilibrium temperature, rigid and described by a constant heat capacity across its selected temperature range. The outside boundary is insulated and does no work. Only energy is exchanged between the two blocks. The selector parametrizes the amount of energy transferred toward equilibrium, not a contact time, a heat-flow rate or an internal temperature gradient. Entropy changes use reversible reference integrals C dT/T for the changing block temperatures; the actual finite-temperature-difference heat transfer is irreversible. Total entropy change is nonnegative for equal or unequal capacities, and positive after nonzero transfer between unequal initial temperatures. Equal initial temperatures or zero transferred energy give exactly zero entropy change. Material-dependent heat capacity, phase transitions, radiation, interface kinetics and spatial diffusion are omitted.'};
  }
  function el(tag, attrs = {}, ...children) {const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v)); for (const c of children) if (c != null) e.append(c.nodeType ? c : document.createTextNode(String(c))); return e;}
  function svgEl(tag, attrs = {}, value) {const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v)); if (value != null) e.textContent = String(value); return e;}
  function render(item, hooks = {}) {
    if (item?.props?.scenario !== scenario || Object.keys(item.props).length !== 1) return null;
    let model = build(initial); const uid = 'ensemble-' + ++serial, root = el('section', {class: 'card lesson-model physics-ensemble-lab', 'data-renderer': 'physics-ensemble-lab', 'aria-labelledby': uid + '-title'});
    const mode = el('select', {id: uid + '-mode', 'data-ensemble-mode': ''}); modes.forEach(([value, label]) => mode.append(el('option', {value}, label)));
    const inputs = el('div', {class: 'model-controls ensemble-controls'}, el('label', {class: 'ensemble-select', for: uid + '-mode'}, 'Statistical model and boundary', mode)), widgets = new Map();
    mode.addEventListener('change', () => {model = build({...model.state, mode: mode.value}); refresh(true);});
    const live = el('p', {class: 'ensemble-live', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true'});
    for (const c of controls) {
      const id = uid + '-' + c.key, range = el('input', {id, type: 'range', step: c.integer ? 1 : 'any', 'data-ensemble-control': c.key}), output = el('output', {for: id});
      const number = el('input', {type: 'number', step: c.integer ? 1 : 'any', 'aria-label': c.label + ' numeric entry', 'data-ensemble-number': c.key});
      const label = el('label', {class: 'model-range-control', for: id}, c.label, output, range, number);
      range.addEventListener('input', () => {model = build({...model.state, [c.key]: range.value}); refresh(false);});
      range.addEventListener('change', () => {live.textContent = model.readout;});
      // Numeric text remains a draft until change/blur; clearing must not rebuild.
      number.addEventListener('change', () => {model = build({...model.state, [c.key]: number.value}); refresh(true);});
      widgets.set(c.key, {c, label, range, number, output}); inputs.append(label);
    }
    const buttons = el('div', {class: 'model-button-row'});
    for (const [key, label, patch] of [
      ['gap-kT', 'Gap equals k_B T', {mode: 'canonical', temperature: 300, gap: initial.gap}],
      ['three-coins', 'Three coins; one head; eight states', {mode: 'coins', N: 3, j: 1}],
      ['four-coins', 'Four coins; two heads', {mode: 'coins', N: 4, j: 2}],
      ['four-sites', 'Four canonical sites; gap k_B T', {mode: 'particles', N: 4, j: 2, temperature: 300, gap: initial.gap}],
      ['large-count', '1024 coins; middle count', {mode: 'coins', N: MAX_N, j: MAX_N / 2}],
      ['free-expansion', 'Doubled gas volume', {mode: 'expansion', log10N: 4, volumeRatio: 2}],
      ['blocks-equal', 'Equal-capacity 600/300 K blocks', {mode: 'blocks', tempA: 600, tempB: 300, capacityA: 100, capacityB: 100, transfer: 100}]
    ]) {const b = el('button', {type: 'button', class: 'btn ghost small', 'data-ensemble-preset': key}, label); b.addEventListener('click', () => {model = build({...model.state, ...patch}); refresh(true);}); buttons.append(b);}
    const reset = el('button', {type: 'button', class: 'btn ghost small', 'data-ensemble-action': 'reset'}, 'Reset'); reset.addEventListener('click', () => {model = build(initial); refresh(true);}); buttons.append(reset);
    const enlarge = el('button', {type: 'button', class: 'btn ghost small', 'data-ensemble-action': 'enlarge', 'aria-pressed': 'false'}, 'Enlarge diagram'); enlarge.addEventListener('click', () => {const on = enlarge.getAttribute('aria-pressed') !== 'true'; enlarge.setAttribute('aria-pressed', String(on)); root.classList.toggle('is-enlarged', on); enlarge.textContent = on ? 'Fit diagram' : 'Enlarge diagram';});
    const limits = el('p', {class: 'spatial-note ensemble-limits'}), readout = el('p', {class: 'ensemble-readout'}), equation = el('p', {class: 'ensemble-equation'}), note = el('p', {class: 'spatial-note ensemble-note'});
    const svg = svgEl('svg', {viewBox: '0 0 500 340', role: 'img', 'aria-labelledby': uid + '-svg-title', 'aria-describedby': uid + '-svg-desc'});
    const viewport = el('div', {class: 'ensemble-viewport', tabindex: 0, role: 'region', 'aria-label': 'Equilibrium/counting diagram; enlarge and scroll'}, svg);
    const tableBody = el('tbody'), caption = el('caption'), table = el('table', {class: 'ensemble-table'}, caption,
      el('thead', {}, el('tr', {}, ...['Count j', 'Exact Ω_j', 'ln Ω_j', 'ln P(j)'].map(text => el('th', {scope: 'col'}, text)))), tableBody);
    const tableRegion = el('div', {class: 'ensemble-table-region', tabindex: 0, role: 'region', 'aria-label': 'Exact counts and log probabilities; scroll'}, table);
    const enumerationText = el('p', {class: 'spatial-note'}), enumerationList = el('ul', {class: 'ensemble-microstates'}), enumeration = el('details', {class: 'ensemble-enumeration'}, el('summary', {}, 'Inspect every small-N microstate'), enumerationText, enumerationList);
    root.append(el('div', {class: 'model-heading-row'}, el('h3', {id: uid + '-title'}, item.title || 'Count states; normalize probabilities; compare entropy'), enlarge),
      el('p', {class: 'model-instructions'}, item.instructions || 'Compare a population ratio with a normalized probability, inspect exact binomial states, then check isolated-system entropy ledgers.'), inputs, limits, buttons, viewport, tableRegion, enumeration, equation, readout,
      el('details', {class: 'ensemble-assumptions'}, el('summary', {}, 'Model assumptions and boundaries'), note,
        el('p', {class: 'spatial-note'}, el('a', {href: 'https://ocw.mit.edu/courses/8-333-statistical-mechanics-i-statistical-mechanics-of-particles-fall-2013/resources/lecture-12/', target: '_blank', rel: 'noopener noreferrer'}, 'Two-level state counting'), ' · ',
          el('a', {href: 'https://ocw.mit.edu/courses/8-333-statistical-mechanics-i-statistical-mechanics-of-particles-fall-2013/resources/lecture-14/', target: '_blank', rel: 'noopener noreferrer'}, 'Canonical ensemble'), ' · ',
          el('a', {href: 'https://ocw.mit.edu/courses/8-333-statistical-mechanics-i-statistical-mechanics-of-particles-fall-2013/resources/lecture-13/', target: '_blank', rel: 'noopener noreferrer'}, 'Ideal-gas entropy'), '. Original artwork; no source figure copied.')), live);
    if (hooks.speakButton) root.append(hooks.speakButton(() => model.readout + ' ' + model.equation));
    const text = (x, y, value, attrs = {}) => svg.append(svgEl('text', {x, y, fill: '#263b46', 'font-size': 12, ...attrs}, value));
    const line = (a, b, attrs = {}) => svg.append(svgEl('line', {x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: '#8b7e66', 'stroke-width': 1.3, ...attrs}));
    function plotCurve(points, attrs) {svg.append(svgEl('polyline', {points: points.map(p => p.join(',')).join(' '), fill: 'none', 'stroke-width': 2, ...attrs}));}
    function draw() {
      const m = model, s = m.state, title = s.mode === 'canonical' ? 'Normalized canonical populations' : s.mode === 'coins' || s.mode === 'particles' ? 'Discrete count distribution: natural-log probability' : s.mode === 'expansion' ? 'Free-expansion equilibrium endpoints' : 'Isolated thermal blocks: energy conserved';
      svg.replaceChildren(svgEl('title', {id: uid + '-svg-title'}, title), svgEl('desc', {id: uid + '-svg-desc'}, m.readout), svgEl('rect', {x: 0, y: 0, width: 500, height: 340, rx: 10, fill: '#f5efdf'}));
      text(18, 26, title, {'font-size': 15, 'font-weight': 600});
      if (s.mode === 'canonical') {
        text(18, 50, 'Probability (dimensionless); bars sum to 1');
        for (const [index, value, logP, label, color] of [[0, m.pLower, m.logLower, 'Lower: E = 0 J', '#536e87'], [1, m.pUpper, m.logUpper, 'Upper: E = ΔE', '#b98a2f']]) {
          const x = 110 + index * 210; svg.append(svgEl('rect', {x, y: 250 - 160 * value, width: 80, height: 160 * value, fill: color, 'data-ensemble-population': index, 'data-probability': value, 'data-log-probability': logP}));
          text(x + 40, 275, label, {'text-anchor': 'middle'}); text(x + 40, 295, 'P ≈ ' + fmt(value), {'text-anchor': 'middle'});
        }
        line([72, 90], [72, 250]); line([72, 250], [445, 250]);
        for (const p of [0, .5, 1]) {text(62, 254 - 160 * p, p, {'text-anchor': 'end'}); line([68, 250 - 160 * p], [445, 250 - 160 * p], {'stroke-dasharray': '3 4', opacity: .4});}
        text(250, 322, 'Ratio P₁/P₀ ≈ ' + fmt(m.populationRatio.value) + '; gap / k_B T ≈ ' + fmt(m.x), {'text-anchor': 'middle'});
      } else if (s.mode === 'coins' || s.mode === 'particles') {
        const low = Math.min(...m.rows.map(r => r.macroLogP), -1), X = j => 65 + 405 * j / s.N, Y = log => 70 - 215 * log / (-low);
        line([65, 70], [65, 285]); line([65, 285], [470, 285]);
        for (const f of [0, .5, 1]) text(58, Y(low * f) + 4, fmt(low * f), {'text-anchor': 'end', 'font-size': 11});
        for (const j of [...new Set([0, Math.floor(s.N / 2), s.N])]) text(X(j), 304, j, {'text-anchor': 'middle'});
        plotCurve(m.rows.map(r => [X(r.j), Y(r.macroLogP)]), {stroke: '#317e78', 'data-ensemble-distribution': '', 'data-min-log': low, 'data-N': s.N});
        if (s.N <= 32) m.rows.forEach(r => svg.append(svgEl('circle', {cx: X(r.j), cy: Y(r.macroLogP), r: 2, fill: '#317e78'})));
        svg.append(svgEl('circle', {cx: X(s.j), cy: Y(m.macroLogP), r: 5, fill: '#b96652', 'data-ensemble-selected-count': s.j}));
        text(18, 50, 'ln P(j) ≤ 0; all finite-N probabilities remain positive');
        text(250, 325, 'j is an integer. Lines join discrete points only for viewing.', {'text-anchor': 'middle', 'font-size': 11});
      } else if (s.mode === 'expansion') {
        svg.append(svgEl('rect', {x: 65, y: 85, width: 405, height: 95, fill: '#dedacb', stroke: '#536e87'}));
        svg.append(svgEl('rect', {x: 65, y: 85, width: 405 / s.volumeRatio, height: 95, fill: '#317e78', opacity: .5, 'data-ensemble-original-region': '', 'data-volume-fraction': 1 / s.volumeRatio}));
        text(65, 70, 'Specified original volume is 1/r of final accessible volume');
        text(250, 206, 'Q = W_by = ΔU = 0 J; equilibrium ΔT = 0 K', {'text-anchor': 'middle'});
        text(250, 235, 'ΔS / (N k_B) = ln r ≈ ' + fmt(Math.log(s.volumeRatio)), {'text-anchor': 'middle'});
        text(250, 265, 'ln P(all in original region) / N = −ln r ≈ ' + fmt(-Math.log(s.volumeRatio)), {'text-anchor': 'middle'});
        text(250, 302, 'Endpoint comparison and one-instant probability; no motion/time model.', {'text-anchor': 'middle', 'font-size': 11});
      } else {
        const max = Math.max(s.tempA, s.tempB), rows = [['A', m.tempA, '#536e87'], ['B', m.tempB, '#b98a2f']];
        rows.forEach(([name, T, color], i) => {const y = 94 + i * 70; text(25, y + 14, name + ': ' + fmt(T) + ' K'); svg.append(svgEl('rect', {x: 160, y, width: 300 * T / max, height: 25, fill: color, 'data-ensemble-block': name, 'data-temperature': T}));});
        text(250, 235, 'Q_A + Q_B = 0 J; T_f ≈ ' + fmt(m.Tf) + ' K', {'text-anchor': 'middle'});
        text(250, 263, 'ΔS_total ≈ ' + fmt(m.totalEntropy) + ' J/K', {'text-anchor': 'middle'});
        text(250, 297, 'Energy-transfer fraction ' + fmt(s.transfer) + '%; no elapsed-time scale', {'text-anchor': 'middle'});
        text(250, 322, 'Bar lengths are temperatures relative to max(initial T_A, T_B).', {'text-anchor': 'middle', 'font-size': 11});
      }
    }
    function refresh(announce) {
      const m = model, s = m.state, countMode = ['coins', 'particles'].includes(s.mode); root.setAttribute('data-ensemble-state', JSON.stringify(s)); mode.value = s.mode;
      for (const w of widgets.values()) {const active = w.c.modes.includes(s.mode), b = bounds(w.c.key, s); w.label.hidden = !active; w.range.disabled = w.number.disabled = !active;
        w.range.min = w.number.min = b.min; w.range.max = w.number.max = b.max; w.range.value = w.number.value = s[w.c.key]; w.output.textContent = fmt(s[w.c.key]) + ' ' + w.c.unit; w.range.setAttribute('aria-valuetext', w.output.textContent);}
      limits.textContent = ['canonical', 'particles'].includes(s.mode) ? 'Positive reservoir T: 1…1200 K. Gap: 0…min(100, 40 k_B T / 10⁻²¹) zJ; current maximum ' + fmt(bounds('gap', s).max) + ' zJ. Joint bounds give ΔE/(k_B T) ≤ 40. ' + (countMode ? 'N: 1…1024 integer sites; j: 0…N.' : '') :
        s.mode === 'coins' ? 'N: 1…1024 distinguishable fair coins; j: 0…N. Fractional counts round to nearest integer.' : s.mode === 'expansion' ? 'Exact N = 10^q, integer q: 0…25; final/initial volume ratio: 1…10. No time variable.' :
          'Initial block temperatures: 1…1200 K; positive constant capacities: 1…1000 J/K; transferred-energy fraction: 0…100%, not time.';
      limits.textContent += ' Out-of-range committed entries clamp; a committed blank restores that control’s default. Numeric typing stays a draft until change/blur.';
      readout.textContent = m.readout; equation.textContent = m.equation; note.textContent = m.note;
      tableRegion.hidden = enumeration.hidden = !countMode; tableBody.replaceChildren(); enumerationList.replaceChildren();
      if (countMode) {
        const selected = s.N <= 12 ? m.rows : m.rows.filter(r => r.j === 0 || r.j === s.N || Math.abs(r.j - s.j) <= 2 || Math.abs(r.j - Math.floor(m.meanUpperCount)) <= 1);
        caption.textContent = (s.N <= 12 ? 'Every count j' : 'Selected/nearby counts, near the mean, and endpoints; other integer counts remain in the plot') + '. Counts are exact; logarithms are approximations.';
        for (const r of selected) tableBody.append(el('tr', {'data-ensemble-row': r.j, class: r.j === s.j ? 'ensemble-selected-row' : ''}, el('th', {scope: 'row'}, r.j), el('td', {class: 'ensemble-exact-count'}, r.omega), el('td', {}, fmt(r.logOmega)), el('td', {}, fmt(r.macroLogP))));
        enumerationText.textContent = m.enumeration.length ? 'Every labelled binary string; 1 denotes a head or an upper state. Highlighting selects j=' + s.j + '. ' + (s.mode === 'coins' ? 'All strings have equal probability.' : 'Strings with unequal j generally have unequal canonical probabilities.') : 'Full enumeration is shown only for N≤8. Exact multiplicities and every count probability are still calculated for this larger N.';
        for (const e of m.enumeration) enumerationList.append(el('li', {'data-ensemble-bits': e.bits, class: e.j === s.j ? 'ensemble-selected-microstate' : '', 'aria-label': e.bits + ', count ' + e.j + ', log probability ' + fmt(e.logP)}, e.bits, el('small', {}, 'j=' + e.j + '; ln P≈' + fmt(e.logP))));
      }
      draw(); if (announce) live.textContent = m.readout;
    }
    refresh(false); return root;
  }
  const api = Object.freeze({scenario, K, MAX_N, modes, initial, controls, bounds, normalize, choose, logBigInt, probability, enumerate, build, render});
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else globalThis.PrimerPhysicsEnsembleLab = api;
})();
