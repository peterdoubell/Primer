(function (host) {
  'use strict';
  const abs = n => n < 0n ? -n : n;
  const power = n => 10n ** BigInt(n);
  function gcd(a, b) { a = abs(a); b = abs(b); while (b) [a, b] = [b, a % b]; return a; }
  function q(n, d = 1n) {
    n = BigInt(n); d = BigInt(d);
    if (!d) throw new RangeError('A divisor cannot be zero.');
    if (d < 0n) { n = -n; d = -d; }
    const g = gcd(n, d); return { n: n / g, d: d / g };
  }
  const add = (a, b) => q(a.n * b.d + b.n * a.d, a.d * b.d);
  const sub = (a, b) => q(a.n * b.d - b.n * a.d, a.d * b.d);
  const mul = (a, b) => q(a.n * b.n, a.d * b.d);
  const div = (a, b) => q(a.n * b.d, a.d * b.n);
  const compare = (a, b) => a.n * b.d < b.n * a.d ? -1 : a.n * b.d > b.n * a.d ? 1 : 0;
  function fixed(n, places) {
    const digits = String(abs(n)).padStart(places + 1, '0');
    return (n < 0n ? '-' : '') + (places ? digits.slice(0, -places) + '.' + digits.slice(-places) : digits);
  }
  function pack(r) {
    let d = r.d, twos = 0, fives = 0;
    while (d % 2n === 0n) { d /= 2n; twos++; }
    while (d % 5n === 0n) { d /= 5n; fives++; }
    const places = Math.max(twos, fives);
    const decimal = d === 1n ? fixed(r.n * (power(places) / r.d), places) : null;
    const fraction = String(r.n) + (r.d === 1n ? '' : '/' + r.d);
    return { n: String(r.n), d: String(r.d), fraction, decimal, exact: decimal === null ? fraction : decimal, value: Number(r.n) / Number(r.d) };
  }
  function parse(value) {
    if (!['string', 'number'].includes(typeof value)) throw new TypeError('Use a decimal number.');
    const raw = String(value).trim();
    if (!/^[+-]?(?:\d{1,7}(?:\.\d{0,6})?|\.\d{1,6})$/.test(raw)) throw new RangeError('Use a plain decimal with at most six decimal places.');
    const sign = raw.startsWith('-') ? -1n : 1n;
    const [whole, fraction = ''] = raw.replace(/^[+-]/, '').split('.');
    const coefficient = sign * BigInt((whole || '0') + fraction), scale = fraction.length;
    const rational = q(coefficient, power(scale));
    if (abs(rational.n) > 1000000n * rational.d) throw new RangeError('Input magnitude must not exceed 1000000.');
    return { raw, coefficient, scale, rational, sign: rational.n < 0n ? -1 : 1, whole: (whole || '0').replace(/^0+(?=\d)/, ''), fraction };
  }
  function integer(value, low, high, label) {
    if (!['string', 'number'].includes(typeof value) || !/^\d+$/.test(String(value))) throw new RangeError(label + ' must be a whole number.');
    const result = BigInt(value);
    if (result < BigInt(low) || result > BigInt(high)) throw new RangeError(label + ' must be between ' + low + ' and ' + high + '.');
    return result;
  }
  function placesFor(a, b = a) {
    const left = Math.max(a.whole.length - 1, b.whole.length - 1, 0), right = Math.max(a.scale, b.scale), rows = [];
    function digit(item, p) {
      return p >= 0 ? Number(item.whole[item.whole.length - 1 - p] || '0') : Number(item.fraction[-p - 1] || '0');
    }
    for (let p = left; p >= -right; p--) {
      const unit = p >= 0 ? q(power(p)) : q(1n, power(-p));
      rows.push({ power: p, unit: pack(unit), aDigit: digit(a, p), bDigit: digit(b, p), aExplicit: p >= 0 ? p < a.whole.length : -p <= a.scale, bExplicit: p >= 0 ? p < b.whole.length : -p <= b.scale, contribution: pack(mul(q(BigInt(digit(a, p) * a.sign)), unit)) });
    }
    return rows;
  }
  function columnWork(a, b, subtract) {
    const scale = Math.max(a.scale, b.scale), A = a.coefficient * power(scale - a.scale), B = b.coefficient * power(scale - b.scale) * (subtract ? -1n : 1n);
    const sameSign = (A < 0n) === (B < 0n), magnitudeOperation = sameSign ? 'add' : 'subtract';
    let x = abs(A), y = abs(B), order = ['A', 'B'];
    if (!sameSign && x < y) { [x, y] = [y, x]; order = ['B', 'A']; }
    const width = Math.max(String(x).length, String(y).length, scale + 1), xs = String(x).padStart(width, '0'), ys = String(y).padStart(width, '0'), columns = [];
    let transfer = 0;
    for (let i = width - 1; i >= 0; i--) {
      const aDigit = Number(xs[i]), bDigit = Number(ys[i]), transferIn = transfer;
      let result;
      if (sameSign) { const sum = aDigit + bDigit + transfer; result = sum % 10; transfer = Math.floor(sum / 10); }
      else { result = aDigit - transfer - bDigit; transfer = result < 0 ? 1 : 0; if (transfer) result += 10; }
      columns.push({ power: width - 1 - i - scale, aDigit, bDigit, transferIn, transferOut: transfer, result });
    }
    if (sameSign && transfer) columns.push({ power: width - scale, aDigit: 0, bDigit: 0, transferIn: transfer, transferOut: 0, result: transfer });
    if (!sameSign && transfer) throw new Error('Magnitude subtraction left an unresolved borrow.');
    const coefficient = A + B;
    return { scale, alignedA: fixed(a.coefficient * power(scale - a.scale), scale), alignedB: fixed(b.coefficient * power(scale - b.scale), scale), magnitudeOperation, magnitudeOrder: order, sign: coefficient < 0n ? -1 : coefficient > 0n ? 1 : 0, columns, result: pack(q(coefficient, power(scale))) };
  }
  const initial = { mode: 'add', a: '0.75', b: '1.6', places: '2', quantityA: '1', quantityB: '1', tender: '10', groupStart: '0' };
  const modes = ['place', 'compare', 'add', 'subtract', 'multiply', 'divide', 'round', 'money'];
  const examples = { place: { a: '1.20' }, compare: { a: '0.089', b: '0.7' }, subtract: { a: '3', b: '0.85' }, multiply: { a: '0.4', b: '0.3' }, divide: { a: '1.8', b: '0.6' }, round: { a: '3.478', places: '2' }, money: { a: '3.40', b: '2.75' } };
  function defaults(mode = 'add') { if (!modes.includes(mode)) throw new RangeError('Unknown decimal operation.'); return { ...initial, ...examples[mode], mode }; }
  function money(r) {
    if (r.n < 0n || r.n * 100n % r.d) throw new RangeError('Prices and tender must be nonnegative exact amounts in whole cents.');
    return fixed(r.n * 100n / r.d, 2);
  }
  function build(raw = {}) {
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw new TypeError('Supply a decimal state object.');
    for (const key of Object.keys(raw)) {
      if (!Object.hasOwn(initial, key)) throw new RangeError('Unknown decimal setting: ' + key);
      if (!['string', 'number'].includes(typeof raw[key])) throw new TypeError('Inputs must be strings or numbers.');
    }
    const state = { ...defaults(raw.mode === undefined ? 'add' : raw.mode), ...raw }, a = parse(state.a), mode = state.mode;
    const model = { state, status: 'defined', a: pack(a.rational) };
    if (mode === 'place') {
      model.columns = placesFor(a); model.expanded = model.columns.map(c => c.contribution);
      model.note = 'A digit’s contribution depends on its place. Trailing zero digits do not change this exact mathematical value.';
    } else if (mode === 'round') {
      const places = Number(integer(state.places, 0, 6, 'Decimal places')), unit = q(1n, power(places)), scaled = div(a.rational, unit);
      let lowerInteger = scaled.n / scaled.d;
      if (scaled.n < 0n && scaled.n % scaled.d) lowerInteger--;
      const lower = mul(q(lowerInteger), unit), upper = add(lower, unit), midpoint = div(add(lower, upper), q(2));
      const magnitude = abs(scaled.n), whole = magnitude / scaled.d, remainder = magnitude % scaled.d;
      const roundedInteger = (whole + (2n * remainder >= scaled.d ? 1n : 0n)) * (scaled.n < 0n ? -1n : 1n);
      Object.assign(model, { places, unit: pack(unit), lower: pack(lower), upper: pack(upper), midpoint: pack(midpoint), rounded: pack(mul(q(roundedInteger), unit)), formatted: fixed(roundedInteger, places), halfway: compare(a.rational, midpoint) === 0, alreadyExact: scaled.n % scaled.d === 0n, note: 'Round to the nearest selected decimal mark. At an exact halfway point, round away from zero. Added display zeros specify the requested decimal places, not measurement uncertainty.' });
    } else {
      const b = parse(state.b); model.b = pack(b.rational);
      if (mode === 'compare') {
        model.columns = placesFor(a, b); model.relation = compare(a.rational, b.rational);
        model.sameSign = (a.rational.n < 0n) === (b.rational.n < 0n);
        const different = model.columns.find(c => c.aDigit !== c.bDigit);
        model.firstDifferentPower = different ? different.power : null;
        model.note = 'Compare signs first, then aligned place values. For two negative values, the greater magnitude is the smaller number. Padding zeros preserves value; digit count alone does not order decimals.';
      } else if (mode === 'add' || mode === 'subtract') {
        Object.assign(model, columnWork(a, b, mode === 'subtract'));
        model.note = 'Align equal places. The column ledger operates on magnitudes; its stated operation, operand order and final sign also cover signed inputs. Every outgoing carry or borrow transfers exactly ten units of the current place to or from the next place.';
      } else if (mode === 'multiply') {
        const result = mul(a.rational, b.rational), largest = [q(abs(a.rational.n), a.rational.d), q(abs(b.rational.n), b.rational.d)].reduce((x, y) => compare(x, y) >= 0 ? x : y);
        const axisExtent = largest.n && compare(largest, q(1,10)) < 0 ? largest : compare(largest, q(1)) > 0 ? largest : q(1);
        Object.assign(model, { result: pack(result), magnitudeA: pack(q(abs(a.rational.n), a.rational.d)), magnitudeB: pack(q(abs(b.rational.n), b.rational.d)), integerA: String(a.coefficient), integerB: String(b.coefficient), integerProduct: String(a.coefficient * b.coefficient), decimalPlaces: a.scale + b.scale, axisExtent: pack(axisExtent), sign: result.n < 0n ? -1 : result.n > 0n ? 1 : 0, note: 'Multiply the integer coefficients, then divide by ten to the sum of the input decimal places. The rectangle uses nonnegative lengths on equally scaled axes; the algebraic sign is stated separately.' });
      } else if (mode === 'divide') {
        const scale = Math.max(a.scale, b.scale); model.scaledA = String(a.coefficient * power(scale - a.scale)); model.scaledB = String(b.coefficient * power(scale - b.scale)); model.scaleFactor = String(power(scale));
        const start = integer(state.groupStart, 0, 1000000000000, 'First group index');
        if (!b.rational.n) { model.status = 'undefined'; model.reason = a.rational.n ? 'Division by zero has no defined quotient.' : 'Zero divided by zero does not determine a unique quotient.'; }
        else {
          const quotient = div(a.rational, b.rational), magnitude = q(abs(quotient.n), quotient.d), full = magnitude.n / magnitude.d, fraction = sub(magnitude, q(full));
          const windowEnd = start + 12n, last = full + (fraction.n ? 1n : 0n), end = last < windowEnd ? last : windowEnd, groups = [];
          for (let i = start; i < end; i++) groups.push({ index: String(i), fraction: pack(i < full ? q(1) : fraction) });
          Object.assign(model, { quotient: pack(quotient), fullGroups: String(full), fractionOfLastGroup: pack(fraction), remainderAmount: pack(mul(fraction, q(abs(b.rational.n), b.rational.d))), sign: quotient.n < 0n ? -1 : quotient.n > 0n ? 1 : 0, groupWindow: { start: String(start), groups, totalPositions: String(last), hiddenBefore: String(start < last ? start : last), hiddenAfter: String(end < last && end >= start ? last - end : 0n), empty: !groups.length }, note: 'Division measures how many divisor-sized groups fit the dividend. The group diagram shows nonnegative magnitudes and a labeled window of at most twelve consecutive groups; the quotient retains its algebraic sign. Multiplying both operands by the same nonzero power of ten preserves the quotient.' });
        }
      } else if (mode === 'money') {
        const quantityA = integer(state.quantityA, 0, 1000, 'First quantity'), quantityB = integer(state.quantityB, 0, 1000, 'Second quantity'), tender = parse(state.tender).rational;
        const priceA = money(a.rational), priceB = money(b.rational), paid = money(tender), costA = mul(a.rational, q(quantityA)), costB = mul(b.rational, q(quantityB)), total = add(costA, costB), balance = sub(tender, total);
        Object.assign(model, { priceA, priceB, paid, costA: pack(costA), costB: pack(costB), total: pack(total), balance: pack(balance), totalMoney: money(total), changeMoney: money(q(abs(balance.n), balance.d)), sufficient: balance.n >= 0n, note: 'Prices and tender are exact nonnegative whole-cent amounts, and quantities are whole numbers. Products, totals and change remain exact cents. A negative balance means an amount is still owed.' });
      }
    }
    return model;
  }
  const api = Object.freeze({ build, defaults, modes, parse, pack, q, add, sub, mul, div, compare, fixed });
  if (host) host.PrimerDecimalCore = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window === 'undefined' ? null : window);
