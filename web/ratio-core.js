(function (host) {
  'use strict';
  const q = host ? host.PrimerDecimalCore : require('./decimal-core.js');
  const modes = ['scale', 'compare', 'share', 'missing', 'rate', 'recipe', 'map', 'model', 'mapCompare'];
  const initial = { mode: 'scale', a: '2', b: '3', c: '3', d: '9', target: '6' };
  const examples = {
    compare: { a: '2', b: '3', c: '6', d: '9' }, share: { a: '3', b: '5', target: '40' },
    missing: { a: '7', b: '3', target: '91' }, rate: { a: '6', b: '2.4', target: '10' },
    recipe: { a: '12', b: '9', target: '20' }, map: { a: '5', target: '8' },
    model: { a: '24', b: '4.8' }, mapCompare: { a: '200', b: '50', target: '1000' },
  };
  function defaults(mode = 'scale') {
    if (!modes.includes(mode)) throw new RangeError('Unknown ratio investigation.');
    return { ...initial, ...examples[mode], mode };
  }
  const fields = {
    scale: [['a', 'Original A'], ['b', 'Original B'], ['c', 'Scale factor']],
    compare: [['a', 'First A'], ['b', 'First B'], ['c', 'Second A'], ['d', 'Second B']],
    share: [['a', 'Parts A'], ['b', 'Parts B'], ['target', 'Total amount']],
    missing: [['a', 'Parts A'], ['b', 'Parts B'], ['target', 'Known amount A']],
    rate: [['a', 'Original number of books'], ['b', 'Original mass (kg)'], ['target', 'New number of books']],
    recipe: [['a', 'Original servings'], ['b', 'Original eggs'], ['target', 'New servings']],
    map: [['a', 'Ground km per map cm'], ['target', 'Map distance (cm)']],
    model: [['a', 'Scale denominator, 1 : n'], ['b', 'Actual length (m)']],
    mapCompare: [['a', 'First map: ground m per cm'], ['b', 'Second map: ground m per cm'], ['target', 'Same ground distance (m)']],
  };
  function build(raw = {}) {
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw new TypeError('Supply a ratio state object.');
    for (const key of Object.keys(raw)) if (!Object.hasOwn(initial, key) || !['string', 'number'].includes(typeof raw[key])) throw new RangeError('Unknown or invalid ratio setting: ' + key);
    const state = { ...defaults(raw.mode === undefined ? 'scale' : raw.mode), ...raw };
    const values = {};
    for (const [key] of fields[state.mode]) {
      const value = q.parse(state[key]).rational;
      if (value.n < 0n) throw new RangeError('Amounts and scale factors must be nonnegative.');
      values[key] = value;
    }
    const { a, b, c, d, target } = values;
    const m = { state, status: 'defined', inputs: Object.fromEntries(Object.entries(values).map(([k, v]) => [k, q.pack(v)])), charts: [], steps: [] };
    const set = (key, value) => (m[key] = q.pack(value));
    const chart = (title, unit, rows) => m.charts.push({ title, unit, rows: rows.map(([label, value, role]) => ({ label, amount: q.pack(value), role })) });
    const undefinedResult = reason => { m.status = 'undefined'; m.reason = reason; return m; };
    if (['scale', 'compare', 'share', 'missing'].includes(state.mode) && !q.add(a, b).n) return undefinedResult('The ratio 0 : 0 does not specify relative parts. Choose at least one positive part.');
    if (state.mode === 'scale') {
      const A = q.mul(a, c), B = q.mul(b, c);
      set('resultA', A); set('resultB', B); set('total', q.add(A, B));
      m.equivalent = c.n > 0n;
      m.steps = ['Multiply both parts by ' + q.pack(c).exact + '.', q.pack(a).exact + ' × ' + q.pack(c).exact + ' = ' + m.resultA.exact, q.pack(b).exact + ' × ' + q.pack(c).exact + ' = ' + m.resultB.exact];
      chart('Original and scaled quantities', 'amount units', [['Original A', a, 'A'], ['Original B', b, 'B'], ['Scaled A', A, 'A'], ['Scaled B', B, 'B']]);
      m.note = m.equivalent ? 'The same positive multiplier preserves the ratio. Adding the same number to both parts generally changes it.' : 'A zero multiplier gives zero of both ingredients. The resulting 0 : 0 does not preserve a defined ratio.';
    } else if (state.mode === 'compare') {
      if (!q.add(c, d).n) return undefinedResult('The second ratio 0 : 0 does not specify relative parts.');
      const left = q.mul(a, d), right = q.mul(b, c);
      set('crossLeft', left); set('crossRight', right); m.equivalent = q.compare(left, right) === 0;
      set('firstFractionA', q.div(a, q.add(a, b))); set('secondFractionA', q.div(c, q.add(c, d)));
      m.steps = ['A × second B = ' + m.crossLeft.exact, 'B × second A = ' + m.crossRight.exact, m.equivalent ? 'The cross-products are equal: the ratios are equivalent.' : 'The cross-products differ: the ratios are not equivalent.'];
      chart('Share of A in each whole', 'fraction of its own whole', [['First A share', q.div(a, q.add(a, b)), 'A'], ['Second A share', q.div(c, q.add(c, d)), 'B']]);
      m.note = 'Order matters: A : B compares A with B, while A/(A+B) compares A with the whole. Zero in one part is allowed; 0 : 0 has no defined proportion.';
    } else if (state.mode === 'share' || state.mode === 'missing') {
      if (state.mode === 'missing' && !a.n) return undefinedResult(target.n ? 'A has zero parts, so a positive known amount A is inconsistent with this ratio.' : 'Zero known A and zero parts A do not determine the scale or amount B.');
      const factor = state.mode === 'share' ? q.div(target, q.add(a, b)) : q.div(target, a);
      const A = q.mul(a, factor), B = q.mul(b, factor);
      set('factor', factor); set('resultA', A); set('resultB', B); set('total', q.add(A, B));
      set('fractionA', q.div(a, q.add(a, b))); set('fractionB', q.div(b, q.add(a, b)));
      m.steps = [state.mode === 'share' ? 'One part = total ÷ (parts A + parts B) = ' + m.factor.exact : 'One part = known A ÷ parts A = ' + m.factor.exact, 'A = ' + m.resultA.exact + '; B = ' + m.resultB.exact, 'Check: A + B = ' + m.total.exact];
      chart('Parts of the total', 'amount units', [['A', A, 'A'], ['B', B, 'B'], ['Whole', q.add(A, B), 'whole']]);
      m.note = 'The ratio has ' + q.pack(q.add(a, b)).exact + ' total parts. The share of A is ' + m.fractionA.exact + ', and the share of B is ' + m.fractionB.exact + '. Quantities here are divisible amounts; a whole-object interpretation may require whole counts.';
    } else if (state.mode === 'rate' || state.mode === 'recipe') {
      if (!a.n) return undefinedResult('A rate per original input cannot be determined from zero original input.');
      const factor = q.div(target, a), rate = q.div(b, a), output = q.mul(rate, target), recipe = state.mode === 'recipe';
      set('factor', factor); set('unitRate', rate); set('result', output);
      m.steps = ['Scale factor = new input ÷ original input = ' + m.factor.exact, 'Output per input = ' + m.unitRate.exact, 'New output = ' + m.result.exact];
      chart(recipe ? 'Servings' : 'Identical books', recipe ? 'servings' : 'books', [['Original input', a, 'A'], ['New input', target, 'A']]);
      chart(recipe ? 'Eggs required' : 'Total mass', recipe ? 'eggs' : 'kg', [['Original output', b, 'B'], ['New output', output, 'B']]);
      m.note = recipe ? 'This assumes every ingredient scales with servings. Fractional egg amounts are exact recipe proportions; measure beaten egg or choose a compatible batch size. Cooking time need not scale this way.' : 'This assumes identical books with constant mass per book. Fractional book inputs describe proportional amounts, while an actual count of complete books must be whole.';
    } else if (state.mode === 'map') {
      if (!a.n) return undefinedResult('A map needs a positive ground distance per centimetre.');
      set('groundKm', q.mul(a, target)); set('scaleDenominator', q.mul(a, q.q(100000)));
      m.steps = ['1 km = 100000 cm, so the dimensionless scale is 1 : ' + m.scaleDenominator.exact, 'Ground distance = map cm × ground km per cm = ' + m.groundKm.exact + ' km'];
      chart('Map ruler', 'cm on this map', [['1 map cm', q.q(1), 'A'], ['Selected distance', target, 'A']]);
      chart('Ground ruler', 'km on the ground', [['Ground per cm', a, 'B'], ['Ground distance', q.mul(a, target), 'B']]);
      m.note = 'The two rulers have different units and independently labelled axes. This linear distance model assumes a constant local map scale; it does not calculate projection distortion or a travel route.';
    } else if (state.mode === 'model') {
      if (!a.n) return undefinedResult('The scale denominator must be positive.');
      const actualCm = q.mul(b, q.q(100)), modelCm = q.div(actualCm, a);
      set('actualCm', actualCm); set('modelCm', modelCm); set('lengthFactor', q.div(q.q(1), a));
      m.steps = ['Actual metres × 100 = ' + m.actualCm.exact + ' cm', 'Model cm = actual cm ÷ ' + q.pack(a).exact + ' = ' + m.modelCm.exact + ' cm'];
      chart('Lengths in the same units', 'cm', [['Actual length', actualCm, 'A'], ['Model length', modelCm, 'B']]);
      m.note = 'A scale 1 : n compares model length with actual length after converting both to the same unit. Similar shapes scale areas by the square of the length factor and volumes by its cube.';
    } else {
      if (!a.n || !b.n) return undefinedResult('Both maps need a positive ground distance per centimetre.');
      const first = q.div(target, a), second = q.div(target, b);
      set('firstMapCm', first); set('secondMapCm', second); set('secondToFirst', q.div(a, b));
      m.steps = ['First drawing length = ground m ÷ first m per cm = ' + m.firstMapCm.exact + ' cm', 'Second drawing length = ground m ÷ second m per cm = ' + m.secondMapCm.exact + ' cm', 'Second/first length factor for any positive common ground distance = ' + m.secondToFirst.exact];
      chart('The same ground distance on two maps', 'map cm', [['First map', first, 'A'], ['Second map', second, 'B']]);
      m.note = 'Fewer ground metres per centimetre gives a larger drawing of the same positive distance. At zero ground distance both drawn lengths are zero; the displayed scale factor still compares the maps, not 0 divided by 0.';
    }
    return m;
  }
  const api = Object.freeze({ build, defaults, modes, fields });
  if (host) host.PrimerRatioCore = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window === 'undefined' ? null : window);
