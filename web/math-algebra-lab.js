/* Exact finite algebra and separately stated proofs for infinite structures. */
(function () {
  'use strict';
  const SCENARIO = 'math.5.abstract.groups-rings-fields', NS = 'http://www.w3.org/2000/svg';
  const INK = '#263b46', TEAL = '#317e78', CORAL = '#b96652', BLUE = '#3e7085', PAPER = '#f5efdf';
  const initial = Object.freeze({ station: 'A1', axiomsSystem: 'C3', tableCode: 8229, groupKind: 'cyclic', groupMod: 6, generator: 4,
    permutation: 9, secondPermutation: 6, permutationPower: 1, ringMod: 12, ringA: 3, ringB: 4, coefficient: 3,
    multiplier: 3, integerWindow: 5, targetInteger: 1, sylowStep: 7, crtResidue: 1, quotientGroup: 'S3', subgroupChoice: 1,
    fieldPrime: '5', fieldMap: 'scalar', idealGenerator: 2 });
  const controls = Object.freeze([
    { key: 'station', label: 'Station', options: [['A1', 'A1 · Group axioms'], ['A2', 'A2 · Orders, subgroups and cosets'], ['A3', 'A3 · Permutations of four letters'], ['A4', 'A4 · Rings, units and zero divisors'], ['A5', 'A5 · An integer homomorphism'], ['A6', 'A6 · Every group of order fifteen'], ['A7', 'A7 · Normal subgroups and quotients'], ['A8', 'A8 · Field ideals and injectivity']] },
    { key: 'axiomsSystem', label: 'Set and operation', stations: ['A1'], options: [['C3', 'C₃: addition modulo three'], ['max', '{0,1,2}: maximum'], ['subtract', '{0,1,2}: subtraction modulo three'], ['custom', 'Custom three-element operation table'], ['positive', 'Positive integers under addition'], ['integers', 'All integers under addition'], ['rationals', 'All rational numbers under addition']] },
    { key: 'tableCode', label: 'Custom table base-three code: row-major nine entries', stations: ['A1'], min: 0, max: 19682, step: 1 },
    { key: 'groupKind', label: 'Finite group', stations: ['A2'], options: [['cyclic', 'Cₙ: addition modulo n'], ['klein', 'Klein group: componentwise addition modulo two']] },
    { key: 'groupMod', label: 'Cyclic group size n', stations: ['A2'], min: 2, max: 20, step: 1 },
    { key: 'generator', label: 'Selected element (reduced to this group)', stations: ['A2'], min: 0, max: 19, step: 1 },
    { key: 'permutation', label: 'First permutation σ, lexicographic index', stations: ['A3'], min: 0, max: 23, step: 1 },
    { key: 'secondPermutation', label: 'Second permutation τ, lexicographic index', stations: ['A3'], min: 0, max: 23, step: 1 },
    { key: 'permutationPower', label: 'Power r in σʳ', stations: ['A3'], min: 0, max: 12, step: 1 },
    { key: 'ringMod', label: 'Ring modulus n', stations: ['A4'], min: 2, max: 19, step: 1 },
    { key: 'ringA', label: 'Factor a (reduced modulo n)', stations: ['A4'], min: 0, max: 18, step: 1 },
    { key: 'ringB', label: 'Factor b (reduced modulo n)', stations: ['A4'], min: 0, max: 18, step: 1 },
    { key: 'coefficient', label: 'Coefficient c in cx=0 (reduced modulo n)', stations: ['A4'], min: 0, max: 18, step: 1 },
    { key: 'multiplier', label: 'Integer multiplier k in f(n)=kn', stations: ['A5'], min: -6, max: 6, step: 1 },
    { key: 'integerWindow', label: 'Displayed integer window −W,…,W', stations: ['A5'], min: 2, max: 8, step: 1 },
    { key: 'targetInteger', label: 'Target integer m: does an inverse exist?', stations: ['A5'], min: -18, max: 18, step: 1 },
    { key: 'sylowStep', label: 'Highlighted universal proof step', stations: ['A6'], min: 1, max: 7, step: 1 },
    { key: 'crtResidue', label: 'Selected residue in C₁₅', stations: ['A6'], min: 0, max: 14, step: 1 },
    { key: 'quotientGroup', label: 'Ambient group', stations: ['A7'], options: [['S3', 'S₃: all permutations of three letters'], ['C12', 'C₁₂: addition modulo twelve']] },
    { key: 'subgroupChoice', label: 'Subgroup choice (0 trivial, 1 normal, 2 comparison)', stations: ['A7'], min: 0, max: 2, step: 1 },
    { key: 'fieldPrime', label: 'Prime field Fₚ', stations: ['A8'], options: [['2', 'p=2'], ['3', 'p=3'], ['5', 'p=5'], ['7', 'p=7']] },
    { key: 'fieldMap', label: 'Map and target assumptions', stations: ['A8'], options: [['scalar', 'a↦aI₂ into M₂(Fₚ): unital, nonzero target'], ['zero', 'a↦0₂ into M₂(Fₚ): nonunital'], ['zeroRing', 'Unique map into the zero ring: unital, zero target']] },
    { key: 'idealGenerator', label: 'Element a generating an ideal (reduced modulo p)', stations: ['A8'], min: 0, max: 6, step: 1 },
  ].map(c => Object.freeze({ ...c, stations: c.stations ? Object.freeze(c.stations) : undefined,
    options: c.options ? Object.freeze(c.options.map(([value, label]) => Object.freeze({ value, label }))) : undefined })));
  const mod = (a, n) => (a % n + n) % n;
  function gcd(a, b) { a = Math.abs(a); b = Math.abs(b); while (b) [a, b] = [b, a % b]; return a; }
  const range = n => Array.from({ length: n }, (_, i) => i);
  const yes = x => x ? 'yes' : 'no';
  const set = a => '{' + a.join(', ') + '}';
  function normalize(raw) {
    const input = raw && typeof raw === 'object' ? raw : {}, state = {};
    for (const c of controls) {
      const v = input[c.key];
      if (c.options) state[c.key] = c.options.some(o => o.value === v) ? v : initial[c.key];
      else {
        const valid = typeof v === 'number' || typeof v === 'string' && v.trim() !== '';
        const n = valid && Number.isFinite(Number(v)) ? Number(v) : initial[c.key];
        state[c.key] = c.min + Math.round((Math.min(c.max, Math.max(c.min, n)) - c.min) / c.step) * c.step;
      }
    }
    return state;
  }
  function operationTable(n, operation) { return range(n).map(a => range(n).map(b => operation(a, b))); }
  function groupAxioms(table) {
    const n = table.length;
    if (!n || table.some(row => !Array.isArray(row) || row.length !== n)) throw new RangeError('A nonempty square operation table is required.');
    const closure = [], associativity = [], identities = [], inverses = [];
    for (const a of range(n)) for (const b of range(n)) if (!Number.isInteger(table[a][b]) || table[a][b] < 0 || table[a][b] >= n) closure.push({ a, b, value: table[a][b] });
    if (!closure.length) {
      for (const a of range(n)) for (const b of range(n)) for (const c of range(n)) {
        const left = table[table[a][b]][c], right = table[a][table[b][c]];
        if (left !== right) associativity.push({ a, b, c, left, right });
      }
      for (const e of range(n)) if (range(n).every(a => table[e][a] === a && table[a][e] === a)) identities.push(e);
      for (const e of identities) for (const a of range(n)) inverses.push({ e, a, partners: range(n).filter(b => table[a][b] === e && table[b][a] === e) });
    }
    const valid = !closure.length && !associativity.length && identities.length === 1 && inverses.every(row => row.partners.length > 0);
    return { n, table, closure, associativity, identities, inverses, valid, pairChecks: n * n, tripleChecks: closure.length ? 0 : n ** 3 };
  }
  function decodeTable(code) {
    if (!Number.isInteger(code) || code < 0 || code > 19682) throw new RangeError('A nine-digit base-three table code is required.');
    return range(3).map(a => range(3).map(b => Math.floor(code / 3 ** (3 * a + b)) % 3));
  }
  const circle = (count, radius = 1) => range(count).map(j => ({ key: String(j), label: String(j), x: radius * Math.cos(2 * Math.PI * j / count), y: radius * Math.sin(2 * Math.PI * j / count) }));
  const tablePanel = (title, table, names, selected = null) => ({ kind: 'table', title, table, names, selected });
  const graphPanel = (title, nodes, edges, note) => ({ kind: 'graph', title, nodes, edges, note });
  function axiomsModel(raw) {
    const s = normalize(raw), infinite = ['positive', 'integers', 'rationals'].includes(s.axiomsSystem);
    if (infinite) {
      const positive = s.axiomsSystem === 'positive', rational = s.axiomsSystem === 'rationals';
      const samples = range(7).map(j => positive ? j + 1 : j - 3);
      const nodes = samples.map(n => ({ key: String(n), label: String(n), x: n, y: 0 }));
      return { infinite: true, universe: positive ? 'ℤ>0' : rational ? 'ℚ' : 'ℤ', operation: 'ordinary addition', valid: !positive,
        closure: true, associative: true, identity: positive ? null : 0, inverseRule: positive ? null : 'a↦−a', samples,
        rows: [['Universe', positive ? 'all positive integers' : rational ? 'all rational numbers' : 'all integers', 'This is an infinite set; displayed integers are examples.'], ['Closure', 'yes', 'A sum remains in the stated set.'], ['Associativity', 'yes', '(a+b)+c=a+(b+c) for every three members.'], ['Identity', positive ? 'absent' : '0', positive ? 'Any additive identity would satisfy e+1=1, hence e=0, outside this set.' : '0 belongs to this set and a+0=0+a=a.'], ['Inverses', positive ? 'absent' : '−a for every a', positive ? '1 has no positive b with 1+b=0.' : rational ? 'If a=u/v with v≠0, then −u/v is rational.' : 'The negative of an integer is an integer.'], ['Group', yes(!positive), 'These statements quantify over the entire infinite set.']],
        panels: [graphPanel('Finite examples in an infinite set', nodes, [], 'Spacing is a drawing convention; ℚ also contains nonintegral rationals.'), graphPanel('Identity and inverse witnesses', positive ? [{ key: 'one', label: '1', x: -1, y: 0 }, { key: 'zero', label: '0 outside ℤ>0', x: 1, y: 0, excluded: true }] : [{ key: 'a', label: 'a', x: -1, y: 0 }, { key: '-a', label: '−a', x: 1, y: 0 }, { key: 'e', label: 'a+(−a)=0', x: 0, y: -1 }], [], 'The symbolic argument proves the result.')],
        proof: positive ? 'Ordinary addition is closed and associative on ℤ>0. Its only possible identity is 0, which is excluded, and additive inverses are excluded. Thus it is a semigroup, not a group.' : 'For all a,b,c in the stated set, addition is closed and associative, 0 is a two-sided identity, and −a is a two-sided inverse. These identities prove the group axioms for ℤ or ℚ without treating a finite drawing as exhaustive.' };
    }
    const table = s.axiomsSystem === 'custom' ? decodeTable(s.tableCode) : operationTable(3, s.axiomsSystem === 'max' ? Math.max : s.axiomsSystem === 'subtract' ? (a, b) => mod(a - b, 3) : (a, b) => (a + b) % 3), checked = groupAxioms(table);
    const w = checked.associativity[0];
    return { ...checked, infinite: false, universe: '{0,1,2}',
      rows: [['Closure', yes(!checked.closure.length), 'All nine ordered pairs checked.'], ['Associativity', yes(!checked.associativity.length), w ? '(' + w.a + '★' + w.b + ')★' + w.c + '=' + w.left + ', but ' + w.a + '★(' + w.b + '★' + w.c + ')=' + w.right + '.' : 'All 27 ordered triples checked.'], ['Two-sided identities', set(checked.identities), 'Both e★a=a and a★e=a are required.'], ...checked.inverses.map(r => ['Inverse of ' + r.a, set(r.partners), 'Both products must equal identity ' + r.e + '.']), ['Group', yes(checked.valid), 'Closure, associativity, a two-sided identity, and a two-sided inverse for each element.']],
      panels: [tablePanel('Exact operation: row ★ column', table, ['0', '1', '2']), graphPanel('Two-sided inverse pairs', circle(3), checked.inverses.flatMap(r => r.partners.map(b => ({ from: String(r.a), to: String(b), label: 'inverse' }))), 'Associativity cannot be inferred from a symmetric table.')],
      proof: 'For this three-element universe, every ordered pair, every ordered triple, every identity candidate, and every inverse candidate is tested. Maximum is associative with identity 0 but lacks inverses for 1 and 2. Subtraction modulo three has a right identity but no two-sided identity, and is not associative. A custom table need not satisfy any group axiom.' };
  }
  function generated(table, identity, element) {
    const powers = [identity]; let next = table[identity][element];
    while (next !== identity && powers.length <= table.length) { powers.push(next); next = table[next][element]; }
    if (next !== identity) throw new RangeError('Powers must be requested in a finite group.');
    return powers;
  }
  function cosets(table, subgroup, right = false) {
    const result = [];
    for (const a of range(table.length)) { const members = [...new Set(subgroup.map(h => right ? table[h][a] : table[a][h]))].sort((x, y) => x - y); if (!result.some(c => c.members.join(',') === members.join(','))) result.push({ representative: a, members }); }
    return result;
  }
  function groupModel(raw) {
    const s = normalize(raw), klein = s.groupKind === 'klein', n = klein ? 4 : s.groupMod, table = operationTable(n, klein ? (a, b) => a ^ b : (a, b) => (a + b) % n), element = s.generator % n;
    const names = klein ? ['(0,0)', '(0,1)', '(1,0)', '(1,1)'] : range(n).map(String), powers = generated(table, 0, element), orders = range(n).map(a => generated(table, 0, a).length);
    const subgroups = klein ? [[0], [0, 1], [0, 2], [0, 3], [0, 1, 2, 3]] : range(n).filter(d => n % (d + 1) === 0).map(d => { const size = d + 1; return range(size).map(j => j * n / size); });
    const selectedCosets = cosets(table, powers), nodes = circle(n).map((p, i) => ({ ...p, label: names[i], group: selectedCosets.findIndex(c => c.members.includes(i)), selected: powers.includes(i) }));
    return { n, table, names, element, powers, order: powers.length, orders, subgroups, cosets: selectedCosets, inverse: klein ? element : mod(-element, n), abelian: true,
      rows: [['Group', klein ? 'C₂×C₂ (Klein)' : 'C' + n, 'Operation: ' + (klein ? 'componentwise addition modulo two.' : 'addition modulo ' + n + '.')], ['Selected element', names[element], 'Requested value ' + s.generator + ' reduced to this group.'], ['Powers / repeated sums', powers.map(i => names[i]).join(' → ') + ' → ' + names[0], 'The identity is the first entry; the final return is not a new element.'], ['Element order', String(powers.length), 'Smallest positive r with r·a=0; equals |⟨a⟩|.'], ['Inverse', names[klein ? element : mod(-element, n)], 'Selected element plus its inverse equals zero.'], ['Every element order', orders.map((o, i) => names[i] + ':' + o).join('; '), 'C₄ has order-four elements; Klein has none.'], ...subgroups.map(h => ['Subgroup of size ' + h.length, set(h.map(i => names[i])), 'Complete subgroup enumeration for this family.']), ...selectedCosets.map((c, i) => ['Coset ' + i, set(c.members.map(j => names[j])), 'Each has |H|=' + powers.length + ' members.']), ['Lagrange', n + '=' + selectedCosets.length + '×' + powers.length, 'Cosets partition the group into equal-size blocks. For |G|=20, 8 cannot be |H|.']],
      panels: [tablePanel('Group operation: row + column', table, names, [element, klein ? element : mod(-element, n)]), graphPanel('Add the selected element', nodes, range(n).map(a => ({ from: String(a), to: String(table[a][element]), label: '+' + names[element] })), 'Color gives coset membership; positions carry no algebraic distance.')],
      proof: 'The orbit of 0 under adding a generates ⟨a⟩. In Cₙ its size is n/gcd(n,a); every subgroup is the unique subgroup of some divisor order. In the Klein group, each nonzero element has order two, giving three distinct subgroups of order two. For any finite group, left multiplication is a bijection H→gH and distinct cosets are disjoint, so |G|=[G:H]|H|. Divisibility is necessary; Lagrange does not guarantee a subgroup of every divisor order in an arbitrary group.' };
  }
  function permutations(n) {
    const output = [];
    function next(prefix, remaining) { if (!remaining.length) output.push(prefix); else remaining.forEach((value, j) => next([...prefix, value], remaining.filter((_, k) => k !== j))); }
    next([], range(n)); return output;
  }
  const S4 = permutations(4), S3 = permutations(3);
  function compose(a, b) { return b.map(i => a[i]); } // a∘b: b acts first.
  function power(p, r) { let result = range(p.length); for (let j = 0; j < r; j++) result = compose(p, result); return result; }
  function cycles(p) {
    const seen = new Set(), output = [];
    for (const start of range(p.length)) if (!seen.has(start)) { const cycle = []; let j = start; do { cycle.push(j); seen.add(j); j = p[j]; } while (j !== start); output.push(cycle); }
    return output;
  }
  const cycleName = p => cycles(p).map(c => '(' + c.map(i => i + 1).join(' ') + ')').join('');
  const permutationOrder = p => cycles(p).reduce((a, c) => a * c.length / gcd(a, c.length), 1);
  function permutationModel(raw) {
    const s = normalize(raw), sigma = S4[s.permutation], tau = S4[s.secondPermutation], sigmaTau = compose(sigma, tau), tauSigma = compose(tau, sigma), selectedPower = power(sigma, s.permutationPower), order = permutationOrder(sigma);
    const enumeration = S4.map((p, index) => ({ index, images: p, cycles: cycles(p), notation: cycleName(p), order: permutationOrder(p) })), orderFour = enumeration.filter(p => p.order === 4);
    const nodes = range(4).flatMap(i => [{ key: 'a' + i, label: String(i + 1), x: -1, y: 1 - 2 * i / 3 }, { key: 'b' + i, label: String(i + 1), x: 1, y: 1 - 2 * i / 3 }]);
    return { sigma, tau, sigmaTau, tauSigma, selectedPower, order, enumeration, orderFour,
      rows: [['σ', cycleName(sigma), 'Index ' + s.permutation + '; images [' + sigma.map(i => i + 1).join(',') + '].'], ['τ', cycleName(tau), 'Index ' + s.secondPermutation + '; images [' + tau.map(i => i + 1).join(',') + '].'], ['σ∘τ: τ first', cycleName(sigmaTau), 'At i, the result is σ(τ(i)).'], ['τ∘σ: σ first', cycleName(tauSigma), 'These compositions ' + (sigmaTau.join() === tauSigma.join() ? 'agree for this pair.' : 'differ: S₄ is nonabelian.')], ['σʳ', cycleName(selectedPower), 'r=' + s.permutationPower + '; r=0 gives the identity.'], ['Order of σ', String(order), 'Least common multiple of its disjoint cycle lengths.'], ...enumeration.map(p => ['S₄ element ' + p.index, p.notation, 'Order ' + p.order + '; images [' + p.images.map(i => i + 1).join(',') + '].']), ['Order-four elements', String(orderFour.length), 'Exactly the six four-cycles: ' + orderFour.map(p => p.notation).join(', ') + '.']],
      panels: [graphPanel('σ: each letter to its image', nodes, range(4).map(i => ({ from: 'a' + i, to: 'b' + sigma[i], label: String(i + 1) + '↦' + (sigma[i] + 1) })), 'Image lists and cycles use letters 1,2,3,4.'), graphPanel('Actual permutation power σʳ', circle(4).map((p, j) => ({ ...p, label: String(j + 1) })), range(4).map(i => ({ from: String(i), to: String(selectedPower[i]), label: 'σʳ' })), 'In σ∘τ, τ acts first.')],
      proof: 'A permutation decomposes into disjoint cycles. Its rth power is the identity exactly when every cycle length divides r, so its order is their least common multiple. On four letters, order four requires one four-cycle. Write it starting at 1: the remaining three letters can occur in 3!=6 orders. All 24 permutations are enumerated in the ledger; no relabelled rotations are double-counted.' };
  }
  function ringModel(raw) {
    const s = normalize(raw), n = s.ringMod, a = s.ringA % n, b = s.ringB % n, c = s.coefficient % n, addition = operationTable(n, (x, y) => (x + y) % n), multiplication = operationTable(n, (x, y) => x * y % n);
    const units = range(n).filter(x => range(n).some(y => multiplication[x][y] === 1)), zeroDivisors = range(n).filter(x => x !== 0 && range(n).some(y => y !== 0 && multiplication[x][y] === 0)), solutions = range(n).filter(x => multiplication[c][x] === 0), image = [...new Set(multiplication[c])].sort((x, y) => x - y), prime = units.length === n - 1;
    const ideals = range(n).filter(j => n % (j + 1) === 0).map(j => { const d = j + 1; return { generator: d, members: range(n / d).map(k => k * d) }; });
    return { n, a, b, c, addition, multiplication, units, zeroDivisors, solutions, image, ideals, prime, product: a * b % n,
      rows: [['Ring', 'ℤ/' + n + 'ℤ', 'Addition and multiplication are reduced modulo n; identity is 1.'], ['Ring axioms', 'abelian additive group; associative multiplication; two distributive laws', 'These laws descend from integer arithmetic to residue classes.'], ['Selected product', a + '×' + b + '≡' + (a * b % n), 'a and b are residues ' + a + ' and ' + b + '.'], ['Units', set(units), 'An element is a unit exactly when gcd(a,n)=1.'], ['Nonzero zero divisors', set(zeroDivisors), 'Each has a nonzero partner whose product is zero.'], ['Field', yes(prime), 'For ℤ/nℤ this holds exactly when n is prime.'], ['Solutions of ' + c + 'x=0', set(solutions), 'Kernel of multiplication by c; size gcd(c,n).'], ['Image of x↦' + c + 'x', set(image), 'This image differs from the kernel in general.'], ...range(n).map(x => ['Residue ' + x, 'inverse ' + (units.includes(x) ? multiplication[x].indexOf(1) : 'absent'), zeroDivisors.includes(x) ? 'Nonzero annihilator(s): ' + set(range(n).filter(y => y && multiplication[x][y] === 0)) : x === 0 ? 'Zero is excluded from our zero-divisor convention.' : 'No nonzero annihilator.']), ...ideals.map(i => ['Ideal (' + i.generator + ')', set(i.members), 'All ideals of this modular ring; n generates the zero ideal.'])],
      panels: [tablePanel('Modular multiplication: row × column', multiplication, range(n).map(String), [a, b]), graphPanel('Multiplication by c: x → cx', circle(n).map((p, x) => ({ ...p, selected: solutions.includes(x), group: units.includes(x) ? 0 : zeroDivisors.includes(x) ? 1 : 2 })), range(n).map(x => ({ from: String(x), to: String(multiplication[c][x]), label: String(c) + 'x' })), 'Coral marks the kernel; units and zero divisors are classified separately.')],
      proof: 'Addition is an abelian group operation, multiplication is associative with identity 1, and a(b+c)=ab+ac and (a+b)c=ac+bc hold because these integer identities descend to residue classes. Changing a representative by a multiple of n changes sums and products by a multiple of n. Bézout gives an inverse exactly when gcd(a,n)=1. For a nonzero residue a, if d=gcd(a,n)>1, then a·(n/d)=0 modulo n with n/d nonzero. Thus ℤ/nℤ is a field exactly for prime n. The equation cx=0 has gcd(c,n) solutions, the multiples of n/gcd(c,n). In ℤ/12ℤ, 3x=0 has {0,4,8}; its image is {0,3,6,9}. Over ℚ, a nonzero coefficient can be cancelled; this requires absence of zero divisors.' };
  }
  function integerModel(raw) {
    const s = normalize(raw), k = s.multiplier, W = s.integerWindow, m = s.targetInteger, domain = range(2 * W + 1).map(j => j - W), targetExtent = Math.max(8, Math.abs(k) * W, Math.abs(m));
    const injective = k !== 0, onto = Math.abs(k) === 1, hasPreimage = k === 0 ? m === 0 : m % k === 0, inverseValue = k && hasPreimage ? (m === 0 ? 0 : m / k) : null;
    const arrows = domain.map(n => ({ source: n, target: k * n }));
    return { k, W, m, domain, arrows, targetExtent, injective, onto, isomorphismOntoIntegers: onto, isomorphismOntoImage: injective, hasPreimage, inverseValue,
      rows: [['Map', 'f:ℤ→ℤ, f(n)=' + k + 'n', 'Both source and target are the entire infinite integer group.'], ['Homomorphism', 'yes', 'k(a+b)=ka+kb for all integers a,b.'], ['Kernel', k ? '{0}' : 'ℤ', k ? 'kn=0 implies n=0 by integer cancellation.' : 'Every integer maps to zero.'], ['Image', k ? (Math.abs(k) === 1 ? 'ℤ' : k + 'ℤ') : '{0}', 'The image is exact, beyond the finite window.'], ['Injective', yes(injective), 'Equivalent to k≠0.'], ['Onto ℤ', yes(onto), 'Equivalent to k=1 or k=−1.'], ['Preimage of target ' + m, hasPreimage ? k ? String(inverseValue) : 'every integer' : 'undefined', k ? 'Defined on kℤ by m↦m/k, with integer output.' : 'The zero map has no inverse because it is not injective.'], ['Isomorphism ℤ→image', yes(injective), 'Injective homomorphisms are isomorphisms onto their image.'], ['Element orders in ℤ', '0 has order one; every nonzero integer has infinite order', 'For n≠0 and every positive r, rn≠0.'], ['All subgroups of ℤ', 'dℤ for a unique d≥0', 'd=0 gives {0}; d>0 is the least positive element. Division with remainder proves all members are multiples of d.'], ...arrows.map(p => ['Displayed integer ' + p.source, String(p.target), 'Exact sample; not a finite replacement of ℤ.'])],
      panels: [graphPanel('Exact samples of n → kn', [...domain.map(n => ({ key: 'a' + n, label: String(n), x: -1, y: -n / W })), ...[...new Set(arrows.map(p => p.target))].map(m => ({ key: 'b' + m, label: String(m), x: 1, y: -m / Math.max(1, Math.abs(k) * W) }))], arrows.map(p => ({ from: 'a' + p.source, to: 'b' + p.target, label: String(k) + 'n' })), 'Each distinct target is one node; column scales are separately normalized.'), { kind: 'points', title: 'Integer-coordinate graph of f', points: arrows.map(p => ({ x: p.source, y: p.target, label: p.source + '↦' + p.target })), xRange: [-W, W], yRange: [-targetExtent, targetExtent], xLabel: 'n ∈ ℤ', yLabel: 'f(n) ∈ ℤ', note: 'Only integer points belong; no interpolating lines.' }],
      proof: 'For k≠0, kn=kn′ implies n=n′, and m has a preimage exactly when k divides m. Hence f:ℤ→kℤ has inverse m↦m/k. It is onto ℤ only when k=±1: if |k|>1, the integer 1 is missed, and if k=0 all outputs are zero. Thus f(n)=3n is injective and an isomorphism onto 3ℤ, but is not an automorphism of ℤ. Every nonzero integer has infinite additive order. For a nonzero subgroup H⊆ℤ, choose its least positive member d. Divide any h∈H as h=qd+r, 0≤r<d; then r∈H, so minimality forces r=0. Thus H=dℤ. The zero subgroup is 0ℤ. The finite diagram illustrates these identities and does not prove them by sampling.' };
  }
  const sylowProof = Object.freeze([
    'Sylow existence provides subgroups P and Q of orders 5 and 3 in every group G of order 15.',
    'The number n₅ divides 3 and satisfies n₅≡1 (mod 5). Divisor candidates {1,3} leave only 1.',
    'The number n₃ divides 5 and satisfies n₃≡1 (mod 3). Divisor candidates {1,5} leave only 1.',
    'Each is unique, so conjugation preserves it: P and Q are normal. Their intersection has order dividing both 5 and 3, hence is {e}.',
    'For p∈P and q∈Q, the commutator pqp⁻¹q⁻¹ lies in both P and Q by normality, hence is e. Thus P and Q commute elementwise.',
    'The map P×Q→G, (p,q)↦pq, is a homomorphism with trivial kernel. Both sides have 15 elements, so it is an isomorphism.',
    'Groups of prime order are cyclic. Choose generators p and q. If (pq)ʳ=e, then pʳ=q⁻ʳ lies in P∩Q, so 5|r and 3|r, hence 15|r. Thus pq generates G≅C₁₅.',
  ]);
  function sylowModel(raw) {
    const s = normalize(raw), selected = s.crtResidue, pairs = range(15).map(n => ({ n, a: n % 3, b: n % 5 }));
    return { pairs, selected: pairs[selected], candidate5: [1, 3], admissible5: [1], candidate3: [1, 5], admissible3: [1], steps: sylowProof, highlightedStep: s.sylowStep,
      productTable: operationTable(15, (a, b) => (a + b) % 15),
      rows: [['n₅ divisor candidates', '{1,3}', 'Must divide |G|/5=3.'], ['n₅ after congruence', '{1}', 'Must also be 1 modulo 5.'], ['n₃ divisor candidates', '{1,5}', 'Must divide |G|/3=5.'], ['n₃ after congruence', '{1}', 'Must also be 1 modulo 3.'], ['Intersection', '{e}', 'Its order divides both prime orders.'], ['Direct product', 'C₃×C₅≅C₁₅', 'Prime-order factors are cyclic and commute.'], ...pairs.map(p => ['CRT residue ' + p.n, '(' + p.a + ',' + p.b + ')', 'Inverse: (10a+6b) mod 15=' + mod(10 * p.a + 6 * p.b, 15)]), ['Generator (1,1)', 'order 15', 'An exponent must be divisible by both 3 and 5.']],
      panels: [graphPanel('C₁₅: add one', circle(15).map((p, n) => ({ ...p, selected: n === selected })), range(15).map(n => ({ from: String(n), to: String((n + 1) % 15), label: '+1' })), 'The seven-step proof applies to every order-15 group.'), graphPanel('CRT coordinates: C₃ × C₅', pairs.map(p => ({ key: String(p.n), label: p.n + ':(' + p.a + ',' + p.b + ')', x: p.a - 1, y: p.b / 2 - 1, selected: p.n === selected })), range(15).map(n => ({ from: String(n), to: String((n + 1) % 15), label: '+(1,1)' })), 'All 15 pairs occur once; spacing is layout.')],
      proof: 'Sylow constraints force both prime-order subgroups to be unique and normal. Coprime-order normal subgroups need not themselves be cyclic in general; prime order supplies that fact here. The separate steps prove trivial intersection, commutation, direct product, and the order of a generator product. The CRT map [n]₁₅↦([n]₃,[n]₅) has inverse (a,b)↦[10a+6b]₁₅ and preserves addition.' };
  }
  function quotientModel(raw) {
    const s = normalize(raw), cyclic = s.quotientGroup === 'C12', n = cyclic ? 12 : 6;
    const table = cyclic ? operationTable(12, (a, b) => (a + b) % 12) : operationTable(6, (a, b) => S3.findIndex(p => p.join() === compose(S3[a], S3[b]).join()));
    const names = cyclic ? range(n).map(String) : S3.map(cycleName), subgroup = cyclic ? s.subgroupChoice === 0 ? [0] : generated(table, 0, s.subgroupChoice === 1 ? 3 : 4) : s.subgroupChoice === 0 ? [0] : s.subgroupChoice === 1 ? [0, 3, 4] : [0, 1];
    const left = cosets(table, subgroup), right = cosets(table, subgroup, true), inverse = range(n).map(a => range(n).find(b => table[a][b] === 0 && table[b][a] === 0));
    const conjugates = range(n).map(g => ({ g, members: subgroup.map(h => table[table[g][h]][inverse[g]]).sort((a, b) => a - b) })), normal = conjugates.every(row => row.members.join() === [...subgroup].sort((a, b) => a - b).join());
    const cosetIndex = a => left.findIndex(c => c.members.includes(a)), failures = [];
    for (const A of left) for (const B of left) { const products = A.members.flatMap(a => B.members.map(b => ({ a, b, product: table[a][b], coset: cosetIndex(table[a][b]) }))), results = [...new Set(products.map(p => p.coset))]; if (results.length !== 1) failures.push({ a: A.members, b: B.members, results, products }); }
    const quotientTable = normal ? left.map(A => left.map(B => cosetIndex(table[A.representative][B.representative]))) : null, witness = failures[0];
    return { n, table, names, subgroup, left, right, inverse, conjugates, normal, quotientTable, failures,
      rows: [['Ambient group', s.quotientGroup, 'S₃ composition σ∘τ means τ acts first.'], ['Subgroup H', set(subgroup.map(i => names[i])), 'Identity, closure and inverses hold.'], ['Normal', yes(normal), 'Every conjugate gHg⁻¹ is compared with H.'], ...left.map((c, i) => ['Left coset ' + i, set(c.members.map(j => names[j])), 'gH: g=' + names[c.representative]]), ...right.map((c, i) => ['Right coset ' + i, set(c.members.map(j => names[j])), 'Hg: g=' + names[c.representative]]), ['Quotient multiplication', normal ? 'well defined' : 'not well defined', normal ? 'Every pair of representatives gives the same product coset.' : 'Coset pair ' + left.findIndex(c => c.members.join() === witness.a.join()) + ',' + left.findIndex(c => c.members.join() === witness.b.join()) + ' gives product cosets ' + witness.results.join(',') + ': ' + witness.products.map(p => names[p.a] + '∘' + names[p.b] + '=' + names[p.product] + ' in H' + p.coset).join('; ') + '.'], ['First isomorphism theorem', normal ? 'ker π=H; image π=G/H' : 'No quotient-group projection exists for this H', normal ? 'π(g)=gH preserves multiplication and is surjective.' : 'Left cosets exist as sets, but this product fails.']],
      panels: [graphPanel('Group members colored by left coset', circle(n).map((p, a) => ({ ...p, label: names[a], group: cosetIndex(a), selected: subgroup.includes(a) })), range(n).map(a => ({ from: String(a), to: String(table[a][1]), label: cyclic ? '+1' : 'right compose (2 3)' })), 'Equal coset sizes illustrate Lagrange; normality is separate.'), normal ? tablePanel('Quotient: row coset × column coset', quotientTable, left.map((_, i) => 'H' + i)) : graphPanel('Representative independence fails', left.map((c, i) => ({ key: String(i), label: 'H' + i, x: Math.cos(2 * Math.PI * i / left.length), y: Math.sin(2 * Math.PI * i / left.length), selected: witness.results.includes(i) })), witness.results.map(i => ({ from: '0', to: String(i), label: 'possible product' })), 'Different output cosets forbid quotient-group multiplication.')],
      proof: 'Normality means gHg⁻¹=H for every g, equivalently left and right cosets agree. For normal H, (gH)(kH)=gkH is independent of representatives and the projection has kernel H. In S₃, A₃={e,(1 2 3),(1 3 2)} is normal and S₃/A₃≅C₂. H={e,(2 3)} is not normal; the ledger checks every representative pair to exhibit failure. Every subgroup of an abelian group, including C₁₂, is normal.' };
  }
  function fieldModel(raw) {
    const s = normalize(raw), p = Number(s.fieldPrime), a = s.idealGenerator % p, zeroTarget = s.fieldMap === 'zeroRing', scalar = s.fieldMap === 'scalar', images = range(p).map(x => scalar ? [x, 0, 0, x] : [0, 0, 0, 0]), targetIdentity = zeroTarget ? [0, 0, 0, 0] : [1, 0, 0, 1], kernel = range(p).filter(x => images[x].every(v => v === 0)), unital = images[1].join() === targetIdentity.join(), injective = new Set(images.map(v => v.join())).size === p;
    const ideal = [...new Set(range(p).map(r => r * a % p))].sort((x, y) => x - y), inverse = a === 0 ? null : range(p).find(b => a * b % p === 1);
    const proofSteps = ['A kernel is an additive subgroup: if φ(a)=φ(b)=0, then φ(a−b)=0.', 'For r∈F and a in the kernel, φ(ra)=φ(r)φ(a)=0, so the kernel is an ideal of F.', 'Any nonzero ideal element a has a⁻¹ in F, giving 1=a⁻¹a in the ideal; every r=r·1 then belongs. Only {0} and F are ideals.', 'If the target is nonzero and φ(1)=1, then 1 is not in the kernel. The kernel cannot be F and must be {0}.', 'If φ(a)=φ(b), then a−b lies in the zero kernel, hence a=b. This proves injectivity for every unital map into any nonzero ring.'];
    return { p, a, images, targetIdentity, kernel, unital, injective, targetNonzero: !zeroTarget, ideal, inverse, steps: proofSteps,
      rows: [['Source', 'F' + p, 'Prime p; all nonzero elements have inverses.'], ['Target', zeroTarget ? 'zero ring (0=1)' : 'M₂(F' + p + ')', zeroTarget ? 'Violates the nonzero-target hypothesis.' : 'A noncommutative ring with p⁴ elements.'], ['Map', scalar ? 'a↦aI₂' : 'a↦0', 'Addition and multiplication are preserved.'], ['Unital', yes(unital), 'φ(1)=' + set(images[1]) + '; target identity=' + set(targetIdentity) + '.'], ['Kernel', set(kernel), 'One of the only two ideals of this field.'], ['Injective', yes(injective), scalar ? 'Scalar diagonal matrices are distinct.' : 'All elements have the same image.'], ['Ideal generated by ' + a, set(ideal), a ? 'a⁻¹=' + inverse + '; inverse times a gives 1, so this ideal is the whole field.' : 'Multiples of zero give the zero ideal.'], ...images.map((v, x) => ['φ(' + x + ')', '[[' + v[0] + ',' + v[1] + '],[' + v[2] + ',' + v[3] + ']]', 'Entries reduced modulo p.']), ['Conclusion hypotheses', unital && !zeroTarget ? 'satisfied' : 'not satisfied', 'Both a nonzero target and preservation of 1 are used.']],
      panels: [graphPanel('Exact field-to-ring images', range(p).flatMap(x => [{ key: 'a' + x, label: String(x), x: -1, y: 1 - 2 * x / Math.max(1, p - 1) }, ...(scalar || x === 0 ? [{ key: 'b' + x, label: scalar ? x + 'I₂' : zeroTarget ? '0=1' : '0₂', x: 1, y: scalar ? 1 - 2 * x / Math.max(1, p - 1) : 0 }] : [])]), range(p).map(x => ({ from: 'a' + x, to: 'b' + (scalar ? x : 0), label: 'φ' })), 'The image consists of scalar matrices; the full matrix ring is not a field.'), tablePanel('Field multiplication: row × column', operationTable(p, (x, y) => x * y % p), range(p).map(String), a ? [a, inverse] : [0, 0])],
      proof: 'The five steps prove the general theorem without assuming the target ring is commutative or a field. Scalar matrices give a unital embedding into M₂(Fₚ). The zero map into this nonzero ring preserves addition and multiplication but not 1, so it is not a counterexample. The unique map into the zero ring preserves its identity 0=1 but violates the nonzero-target requirement. Ideals and kernels refer to the entire selected finite field.' };
  }
  const builders = Object.freeze({ A1: axiomsModel, A2: groupModel, A3: permutationModel, A4: ringModel, A5: integerModel, A6: sylowModel, A7: quotientModel, A8: fieldModel });
  function build(raw) { const state = normalize(raw), active = builders[state.station](state), rows = [...active.rows, ...active.panels.filter(p => p.kind === 'table').flatMap(p => p.table.map((row, a) => [p.title + ': row ' + p.names[a], row.map(v => p.names[v]).join(' | '), 'Columns in order: ' + p.names.join(', ') + '.']))]; return { state, station: state.station, active, panels: active.panels, rows, proof: active.proof,
    readout: state.station + '. ' + controls[0].options.find(o => o.value === state.station).label.split(' · ')[1] + '. ' + active.rows.slice(0, 7).map(row => row[0] + ': ' + row[1]).join('. ') + '.' }; }
  const snapshot = raw => build(raw);
  let serial = 0;
  function element(tag, attrs = {}, ...children) { const e = document.createElement(tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v))); children.forEach(c => { if (c != null) e.append(c.nodeType ? c : document.createTextNode(String(c))); }); return e; }
  function shape(tag, attrs = {}, content) { const e = document.createElementNS(NS, tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v))); if (content != null) e.textContent = String(content); return e; }
  function text(svg, x, y, value, attrs = {}) { svg.append(shape('text', { x, y, fill: INK, 'font-size': 11, ...attrs }, value)); }
  const fixtures = Object.freeze([
    ['positive', 'Positive integers fail', { station: 'A1', axiomsSystem: 'positive' }], ['nonassociative', 'Subtraction fails', { station: 'A1', axiomsSystem: 'subtract' }],
    ['inverse6', 'Inverse of four modulo six', { station: 'A2', groupKind: 'cyclic', groupMod: 6, generator: 4 }], ['C4', 'C₄ has order-four elements', { station: 'A2', groupKind: 'cyclic', groupMod: 4, generator: 1 }],
    ['klein', 'Klein: nonidentity order two', { station: 'A2', groupKind: 'klein', generator: 1 }], ['lagrange', 'Lagrange at order twenty', { station: 'A2', groupKind: 'cyclic', groupMod: 20, generator: 4 }],
    ['S4', 'All six four-cycles', { station: 'A3', permutation: 9, secondPermutation: 6, permutationPower: 1 }], ['ring6', 'Modulo six is not a field', { station: 'A4', ringMod: 6, ringA: 2, ringB: 3, coefficient: 2 }],
    ['annihilator', '3x=0 modulo twelve', { station: 'A4', ringMod: 12, ringA: 3, ringB: 4, coefficient: 3 }], ['prime', 'Prime field modulo five', { station: 'A4', ringMod: 5, ringA: 2, ringB: 3, coefficient: 3 }],
    ['triple', '3n misses target one', { station: 'A5', multiplier: 3, targetInteger: 1 }], ['sylow', 'Every order-fifteen group', { station: 'A6', sylowStep: 7, crtResidue: 1 }],
    ['normal', 'S₃/A₃ is a group', { station: 'A7', quotientGroup: 'S3', subgroupChoice: 1 }], ['nonnormal', 'Nonnormal cosets fail', { station: 'A7', quotientGroup: 'S3', subgroupChoice: 2 }],
    ['field', 'Unital field embedding', { station: 'A8', fieldMap: 'scalar', fieldPrime: '5', idealGenerator: 2 }], ['zeromap', 'Dropping preservation of one', { station: 'A8', fieldMap: 'zero' }], ['zeroring', 'Dropping the nonzero target', { station: 'A8', fieldMap: 'zeroRing' }],
  ]);
  function render(item, hooks) {
    if (item?.props?.scenario !== SCENARIO || Object.keys(item.props).length !== 1 || item.renderer && item.renderer !== 'math-algebra-lab') return null;
    const uid = 'algebra-' + ++serial, title = item.title || 'Groups, rings and fields: exact structure', instructions = item.instructions || 'Explore eight stations. Compare complete finite calculations with proofs over all integers, rationals, or groups satisfying the stated hypotheses.';
    const root = element('section', { class: 'card lesson-model math-algebra-lab', 'data-renderer': 'math-algebra-lab', 'aria-labelledby': uid + '-title' }), heading = element('div', { class: 'model-heading-row' }, element('h3', { id: uid + '-title' }, title));
    const area = element('div', { class: 'model-controls concept-controls algebra-controls' }), widgets = new Map(), panels = element('div', { class: 'algebra-panels' }), pictures = [];
    for (let j = 0; j < 2; j++) { const viewport = element('div', { class: 'algebra-viewport', tabindex: '0', role: 'region', 'aria-label': 'Exact algebra panel ' + (j + 1) + '; enlarge and scroll for detail' }), svg = shape('svg', { viewBox: '0 0 480 390', role: 'img', focusable: 'false' }); viewport.append(svg); panels.append(viewport); pictures.push(svg); }
    const table = element('table', { class: 'algebra-ledger' }), tableView = element('div', { class: 'algebra-table-region', tabindex: '0', role: 'region', 'aria-label': 'Complete calculations and hypotheses; scroll horizontally' }, table), readout = element('p', { class: 'model-readout' }), proof = element('p', { class: 'algebra-proof' }), steps = element('ol', { class: 'algebra-proof-steps' }), live = element('p', { class: 'model-status', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    const caveat = element('p', { class: 'spatial-note' }, 'Finite pictures do not prove infinite claims. Tables and permutation lists are exhaustive for their finite sets; universal statements have separate proofs. Graph positions and colors express membership and mappings, not physical distances. Enlarge preserves state. Reset restores every control, including inactive stations.');
    let model = build(initial), enlarged = false;
    const stateBus = typeof window !== 'undefined' ? window.PrimerLessonStateBus : null, stateKey = 'math.5.abstract';
    function refresh(announce, publish = false) {
      root.setAttribute('data-algebra-state', JSON.stringify(model.state));
      widgets.forEach(({ input, rangeInput, label }, key) => { const c = controls.find(c => c.key === key); label.hidden = Boolean(c.stations && !c.stations.includes(model.station)); input.disabled = label.hidden; input.value = String(model.state[key]); if (rangeInput) { rangeInput.disabled = label.hidden; rangeInput.value = String(model.state[key]); } });
      table.replaceChildren(element('caption', {}, 'Current exact calculation and theorem hypotheses'), element('thead', {}, element('tr', {}, ...['Quantity', 'Value', 'Meaning / hypothesis'].map(v => element('th', { scope: 'col' }, v)))), element('tbody', {}, ...model.rows.map(row => element('tr', {}, element('th', { scope: 'row' }, row[0]), element('td', {}, row[1]), element('td', {}, row[2])))));
      readout.textContent = model.readout; proof.textContent = model.proof;
      steps.hidden = !model.active.steps; steps.replaceChildren(...(model.active.steps || []).map((p, j) => element('li', { 'data-algebra-proof-step': j + 1, class: model.station === 'A6' && model.state.sylowStep === j + 1 ? 'is-highlighted' : '' }, p)));
      draw(); if (announce) live.textContent = model.readout; if (publish) stateBus?.publish(stateKey, root, model.state);
    }
    for (const c of controls) {
      const input = element(c.options ? 'select' : 'input', { id: uid + '-' + c.key, 'data-algebra-control': c.key });
      if (c.options) c.options.forEach(o => input.append(element('option', { value: o.value }, o.label)));
      else Object.entries({ type: 'number', min: c.min, max: c.max, step: c.step, inputmode: 'numeric' }).forEach(([k, v]) => input.setAttribute(k, v));
      const commit = () => { model = build({ ...model.state, [c.key]: input.value }); refresh(true, true); };
      input.addEventListener('change', commit); input.addEventListener('blur', () => { if (String(model.state[c.key]) !== input.value) commit(); });
      input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault?.(); commit(); } else if (e.key === 'Escape') { e.preventDefault?.(); input.value = String(model.state[c.key]); } });
      const label = element('label', { for: uid + '-' + c.key, class: 'model-range-control' }, element('span', {}, c.label), input);
      let rangeInput;
      if (!c.options) { rangeInput = element('input', { type: 'range', min: c.min, max: c.max, step: c.step, 'aria-label': c.label + ' slider', 'data-algebra-range': c.key }); rangeInput.addEventListener('input', () => { model = build({ ...model.state, [c.key]: rangeInput.value }); refresh(true, true); }); label.append(rangeInput); }
      widgets.set(c.key, { input, rangeInput, label }); area.append(label);
    }
    const buttons = element('div', { class: 'model-button-row algebra-fixtures' });
    for (const [key, label, patch] of fixtures) { const button = element('button', { type: 'button', class: 'btn ghost small', 'data-algebra-action': key }, label); button.addEventListener('click', () => { model = build({ ...model.state, ...patch }); refresh(true, true); }); buttons.append(button); }
    const reset = element('button', { type: 'button', class: 'btn ghost small', 'data-algebra-action': 'reset' }, 'Reset activity'); reset.addEventListener('click', () => { model = build(initial); size(false); refresh(true, true); }); buttons.append(reset);
    const enlarge = element('button', { type: 'button', class: 'btn ghost small', 'data-algebra-action': 'enlarge', 'aria-pressed': 'false' }, 'Enlarge diagrams');
    function size(on) { enlarged = on; root.classList.toggle('is-enlarged', on); enlarge.setAttribute('aria-pressed', String(on)); enlarge.textContent = on ? 'Fit diagrams' : 'Enlarge diagrams'; }
    enlarge.addEventListener('click', () => size(!enlarged)); heading.append(enlarge);
    const sources = element('p', { class: 'spatial-note' }, 'Sources: ', element('a', { href: 'https://www.jmilne.org/math/CourseNotes/GT.pdf', target: '_blank', rel: 'noopener' }, 'Milne: Group Theory'), '; ', element('a', { href: 'https://math.ucla.edu/~sharifi/notes/algebra-ch03.html', target: '_blank', rel: 'noopener' }, 'Sharifi, UCLA: ring theory'), '.');
    root.append(heading, element('p', { class: 'model-instructions' }, instructions), area, buttons, panels, tableView, readout, proof, steps, caveat, sources, live);
    if (hooks?.speakButton) heading.prepend(hooks.speakButton(() => title + '. ' + model.readout + ' ' + model.rows.map(row => row.join(': ')).join('. ') + '. ' + model.proof + ' ' + (model.active.steps || []).join(' ') + ' ' + caveat.textContent, 'Read this activity aloud'));
    function draw() {
      model.panels.forEach((panel, j) => {
        const svg = pictures[j]; svg.replaceChildren(shape('title', { id: uid + '-panel-title-' + j }, panel.title), shape('desc', { id: uid + '-panel-desc-' + j }, model.readout), shape('rect', { x: 0, y: 0, width: 480, height: 390, rx: 10, fill: PAPER })); svg.setAttribute('aria-labelledby', uid + '-panel-title-' + j); svg.setAttribute('aria-describedby', uid + '-panel-desc-' + j);
        text(svg, 18, 25, panel.title, { 'font-size': 15, 'font-weight': 600 });
        if (panel.kind === 'table') {
          const n = panel.table.length, cell = 290 / n, x0 = 95, y0 = 64;
          for (let a = 0; a < n; a++) { text(svg, x0 - 9, y0 + cell * (a + .65), panel.names[a], { 'text-anchor': 'end', 'font-size': Math.min(12, cell * .5) }); text(svg, x0 + cell * (a + .5), y0 - 7, panel.names[a], { 'text-anchor': 'middle', 'font-size': Math.min(12, cell * .5) });
            for (let b = 0; b < n; b++) { const selected = panel.selected && panel.selected[0] === a && panel.selected[1] === b; svg.append(shape('rect', { x: x0 + cell * b, y: y0 + cell * a, width: cell, height: cell, fill: selected ? '#dab29d' : (a + b) % 2 ? '#ece5d5' : PAPER, stroke: '#d5cfbf', 'stroke-width': .5, 'data-algebra-cell': a + ':' + b })); text(svg, x0 + cell * (b + .5), y0 + cell * (a + .65), panel.names[panel.table[a][b]], { 'text-anchor': 'middle', 'font-size': Math.min(13, cell * .55), 'data-algebra-entry': a + ':' + b }); }
          }
          text(svg, 20, 379, 'Every cell is shown; enlarge for detail.');
        } else if (panel.kind === 'points') {
          const [xmin, xmax] = panel.xRange, [ymin, ymax] = panel.yRange, X = x => 55 + 370 * (x - xmin) / (xmax - xmin), Y = y => 330 - 260 * (y - ymin) / (ymax - ymin);
          svg.append(shape('line', { x1: X(xmin), y1: Y(0), x2: X(xmax), y2: Y(0), stroke: '#b8b1a0' }), shape('line', { x1: X(0), y1: Y(ymin), x2: X(0), y2: Y(ymax), stroke: '#b8b1a0' }));
          panel.points.forEach((p, i) => svg.append(shape('circle', { cx: X(p.x), cy: Y(p.y), r: 4, fill: TEAL, 'data-algebra-point': i, 'data-algebra-x': p.x, 'data-algebra-y': p.y })));
          text(svg, 55, 354, xmin); text(svg, 425, 354, xmax, { 'text-anchor': 'end' }); text(svg, 240, 355, panel.xLabel, { 'text-anchor': 'middle' }); text(svg, 14, 76, ymax); text(svg, 14, 332, ymin); text(svg, 55, 52, panel.yLabel); text(svg, 20, 379, 'Exact integer points; no interpolating lines.');
        } else {
          const xs = panel.nodes.map(p => p.x), ys = panel.nodes.map(p => p.y), minx = Math.min(...xs), maxx = Math.max(...xs), miny = Math.min(...ys), maxy = Math.max(...ys), dx = Math.max(maxx - minx, 2), dy = Math.max(maxy - miny, 2), X = x => 240 + 155 * (x - (minx + maxx) / 2) / (dx / 2), Y = y => 202 - 120 * (y - (miny + maxy) / 2) / (dy / 2), positions = new Map(panel.nodes.map(p => [p.key, [X(p.x), Y(p.y)]]));
          panel.edges.forEach((edge, k) => {
            const a = positions.get(edge.from), b = positions.get(edge.to); if (!a || !b) throw new Error('Graph edges must name existing nodes.');
            const color = edge.from === edge.to ? BLUE : '#9ba9a1';
            if (edge.from === edge.to) svg.append(shape('circle', { cx: a[0] + 8, cy: a[1] - 8, r: 8, fill: 'none', stroke: color, 'data-algebra-edge': k, 'data-algebra-from': edge.from, 'data-algebra-to': edge.to }));
            else { const len = Math.hypot(b[0] - a[0], b[1] - a[1]), ux = (b[0] - a[0]) / len, uy = (b[1] - a[1]) / len, tip = [b[0] - ux * 9, b[1] - uy * 9]; svg.append(shape('line', { x1: a[0], y1: a[1], x2: tip[0], y2: tip[1], stroke: color, 'stroke-width': 1.5, 'data-algebra-edge': k, 'data-algebra-from': edge.from, 'data-algebra-to': edge.to }), shape('polygon', { points: [tip, [tip[0] - ux * 7 - uy * 3, tip[1] - uy * 7 + ux * 3], [tip[0] - ux * 7 + uy * 3, tip[1] - uy * 7 - ux * 3]].map(p => p.join(',')).join(' '), fill: color })); }
          });
          panel.nodes.forEach(node => { const [x, y] = positions.get(node.key), color = node.selected ? CORAL : node.group == null ? TEAL : [TEAL, BLUE, '#a08357', '#886a85', '#60764d', CORAL][node.group % 6]; svg.append(shape('circle', { cx: x, cy: y, r: node.excluded ? 7 : 5, fill: node.excluded ? PAPER : color, stroke: color, 'data-algebra-node': node.key })); text(svg, x, y - 12, node.label, { 'text-anchor': 'middle', 'font-size': panel.nodes.length > 14 ? 9 : 11 }); });
          text(svg, 20, 365, 'Arrows encode mappings; layout has no metric meaning.');
          text(svg, 20, 381, panel.edges.length + ' arrows · ' + panel.nodes.length + ' labelled nodes. Exact values in ledger.');
        }
      });
    }
    root.setModelState = (values, announce = false, fromShared = false) => { model = build({ ...model.state, ...values }); refresh(announce, !fromShared); return model.state; };
    stateBus?.join(stateKey, root, values => root.setModelState(values, false, true)); refresh(false); return root;
  }
  const api = Object.freeze({ SCENARIO, initial, controls, fixtures, normalize, mod, gcd, operationTable, groupAxioms, decodeTable, generated, cosets, permutations, compose, power, cycles, cycleName, permutationOrder, S4, S3, axiomsModel, groupModel, permutationModel, ringModel, integerModel, sylowModel, quotientModel, fieldModel, build, snapshot, render });
  if (typeof window !== 'undefined') window.PrimerMathAlgebraLab = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
}());
