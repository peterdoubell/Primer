/* Original finite witnesses and theorem-hypothesis diagrams. No theorem prover or model of ZFC is simulated. */
(function () {
  'use strict';
  const scenario = 'math.5.logic.diagonal-models-proof', NS = 'http://www.w3.org/2000/svg'; let serial = 0;
  const stations = Object.freeze([
    ['powerset', 'L1 · A subset missing from every proposed row'],
    ['decimal', 'L2 · Diagonal digits without decimal ambiguity'],
    ['relations', 'L3 · Relations as subsets of ordered pairs'],
    ['incomplete', 'L4 · Effective axioms and relative incompleteness'],
    ['consistency', 'L5 · An internal limit and an external consistency proof'],
    ['skolem', 'L6 · Which universe contains the bijection?'],
    ['independence', 'L7 · A proof dependency is not an independence proof'],
    ['compactness', 'L8 · Every finite demand has a standard witness']
  ]);
  const initial = Object.freeze({station: 'powerset', size: 6, rows: Object.freeze([3, 12, 21, 42, 48, 63]),
    decimalRows: Object.freeze(['12345678', '31415926', '27182818', '14142135', '61803398', '57721566', '69314718', '30102999']),
    relationSize: 3, relationMask: 273, theory: 'pa', extension: 1, viewpoint: 'inside', statement: 'choice',
    proofView: 'internal', ordinalDepth: 3, bound: 6, witness: 7});
  const controls = Object.freeze([
    {key: 'station', label: 'Logical construction', options: stations.map(([value, label]) => ({value, label}))},
    {key: 'size', label: 'Elements and proposed subsets n', min: 1, max: 6, step: 1, stations: ['powerset']},
    {key: 'relationSize', label: 'Relation domain size n', min: 1, max: 4, step: 1, stations: ['relations']},
    {key: 'relationMask', label: 'Relation encoding (row-major binary bits)', min: 0, max: 65535, step: 1, stations: ['relations']},
    {key: 'theory', label: 'Theory assumptions', options: [
      ['pa', 'PA · consistent, effective, includes arithmetic'], ['infinite', 'Infinitely many effectively listed axioms'],
      ['true', 'True Arithmetic · all standard arithmetic truths'], ['weak', 'Presburger arithmetic · addition only'],
      ['inconsistent', 'An inconsistent classical theory']].map(([value, label]) => ({value, label})), stations: ['incomplete']},
    {key: 'extension', label: 'Finite number of added independent sentences', min: 0, max: 4, step: 1, stations: ['incomplete']},
    {key: 'proofView', label: 'Location of the consistency argument', options: [
      {value: 'internal', label: 'Inside PA'}, {value: 'gentzen', label: 'Gentzen: PRA plus the required transfinite induction'}], stations: ['consistency']},
    {key: 'ordinalDepth', label: 'Displayed omega-tower depth', min: 1, max: 5, step: 1, stations: ['consistency']},
    {key: 'viewpoint', label: 'Quantifier domain', options: [
      {value: 'inside', label: 'Bijections that belong to M'}, {value: 'outside', label: 'External functions in the metatheory'}], stations: ['skolem']},
    {key: 'statement', label: 'Statement and known dependency', options: [
      ['choice', 'Axiom of choice'], ['wellorder', 'Every set can be well-ordered'],
      ['finite', 'Choice for finitely many nonempty sets'], ['ch', 'Continuum hypothesis'],
      ['unknown', 'An arbitrary theorem with a known proof using choice']].map(([value, label]) => ({value, label})), stations: ['independence']},
    {key: 'bound', label: 'Largest requested numeral K', min: 0, max: 20, step: 1, stations: ['compactness']},
    {key: 'witness', label: 'Try a standard natural number for c', min: 0, max: 22, step: 1, stations: ['compactness']}
  ].map(c => Object.freeze(c)));
  const clone = o => JSON.parse(JSON.stringify(o));
  const integer = (x, lo, hi, fallback) => Number.isFinite(Number(x)) ? Math.max(lo, Math.min(hi, Math.round(Number(x)))) : fallback;
  function normalize(raw = {}) {
    const s = {...clone(initial), ...raw};
    for (const c of controls) {
      if (c.options) { if (!c.options.some(o => o.value === s[c.key])) s[c.key] = initial[c.key]; }
      else s[c.key] = integer(s[c.key], c.min, c.max, initial[c.key]);
    }
    s.rows = Array.from({length: 6}, (_, i) => integer(raw.rows?.[i] ?? initial.rows[i], 0, 63, initial.rows[i]));
    s.decimalRows = Array.from({length: 8}, (_, i) => /^\d{8}$/.test(raw.decimalRows?.[i] ?? '') ? raw.decimalRows[i] : initial.decimalRows[i]);
    // Keep unused higher bits so returning to a larger relation domain restores the authored relation.
    return Object.fromEntries([...Object.keys(initial)].map(k => [k, s[k]]));
  }
  function diagonal(rows, size) {
    const mask = 2 ** size - 1, table = rows.slice(0, size).map(r => Array.from({length: size}, (_, j) => Boolean(r & 2 ** j)));
    const missing = table.reduce((r, row, i) => r + (!row[i] ? 2 ** i : 0), 0);
    const comparisons = table.map((row, i) => ({row: i, listed: rows[i] & mask, diagonal: missing, index: i,
      listedContains: row[i], diagonalContains: !row[i], equal: (rows[i] & mask) === missing}));
    return {table, missing, comparisons, subsetCount: 2 ** size, subsetLabels: Array.from({length: size}, (_, i) => i + 1)};
  }
  function decimalDiagonal(rows) {
    const digits = rows.map((r, i) => r[i] === '1' ? '2' : '1');
    return {digits, prefix: '0.' + digits.join(''), comparisons: rows.map((r, i) => ({row: i, index: i,
      listed: r[i], constructed: digits[i], differs: r[i] !== digits[i]}))};
  }
  function relation(size, encoding) {
    const mask = encoding % 2 ** (size * size), has = (i, j) => Boolean(mask & 2 ** (i * size + j));
    const pairs = [], failures = {reflexive: [], symmetric: [], antisymmetric: [], transitive: []};
    for (let i = 0; i < size; i++) for (let j = 0; j < size; j++) {
      if (has(i, j)) pairs.push([i, j]);
      if (i === j && !has(i, i)) failures.reflexive.push([i]);
      if (has(i, j) && !has(j, i)) failures.symmetric.push([i, j]);
      if (i !== j && has(i, j) && has(j, i)) failures.antisymmetric.push([i, j]);
      for (let k = 0; k < size; k++) if (has(i, j) && has(j, k) && !has(i, k)) failures.transitive.push([i, j, k]);
    }
    return {size, encoding: mask, pairSlots: size * size, relationCount: 2 ** (size * size), pairs,
      table: Array.from({length: size}, (_, i) => Array.from({length: size}, (_, j) => has(i, j))),
      properties: Object.fromEntries(Object.entries(failures).map(([k, v]) => [k, !v.length])), failures};
  }
  const graph = (labels, edges, title) => ({kind: 'graph', title,
    nodes: labels.map((label, i) => ({id: String(i), label, x: 220, y: 48 + i * 66})),
    edges: edges.map(([from, to, label]) => ({from: String(from), to: String(to), label}))});
  const table = (title, rowLabels, columnLabels, cells, extra = {}) => ({kind: 'table', title, rowLabels, columnLabels, cells, ...extra});
  function build(raw = {}) {
    const state = normalize(raw), s = state; let data, panels, readout, proof, boundary;
    if (s.station === 'powerset') {
      data = diagonal(s.rows, s.size);
      panels = [table('f(i): proposed subsets', data.subsetLabels, data.subsetLabels, data.table, {editable: 'powerset', diagonal: true}),
        table('The missing subset D', ['D'], data.subsetLabels, [data.table.map((row, i) => !row[i])])];
      readout = 'There are ' + data.subsetCount + ' subsets of this ' + s.size + '-element set. D has encoding ' + data.missing + '. At every row i, membership of i in D differs from membership in f(i). No displayed row equals D.';
      proof = ['For any set S and any proposed map f:S→P(S), define D={s∈S:s∉f(s)}.', 'If f(t)=D, then t∈D exactly when t∉D, a contradiction. Thus f cannot be onto.', 'The singleton map s↦{s} is injective. Together with the absence of a surjection this gives the strict cardinal comparison in the usual cardinal ordering; no axiom of choice is needed.'];
      boundary = 'The editable table is a complete finite example. The quantified argument, rather than a finite size trend, covers an arbitrary set S.';
    } else if (s.station === 'decimal') {
      data = decimalDiagonal(s.decimalRows);
      panels = [table('Eight displayed decimal prefixes', s.decimalRows.map((_, i) => i + 1), data.digits.map((_, i) => i + 1), s.decimalRows.map(r => [...r]), {diagonal: true}),
        table('New prefix: use 2 if the diagonal is 1, otherwise 1', ['d'], data.digits.map((_, i) => i + 1), [data.digits])];
      readout = data.prefix + '… differs from each of the eight displayed rows at that row’s diagonal digit. Its continuation uses the same 1-or-2 rule for every later row of a hypothetical infinite list.';
      proof = ['Write each proposed real using a canonical decimal expansion that is not eventually all 9s.', 'For row n, choose dₙ=2 when its n-th digit is 1, and dₙ=1 otherwise. The infinite decimal d differs at position n from row n.', 'Only digits 1 and 2 occur, so the constructed number is neither eventually 0 nor eventually 9. The alternate-expansion exception cannot undo the disagreement.'];
      boundary = 'Eight prefixes do not specify eight complete real numbers or prove uncountability by computation. The infinite construction supplies the proof.';
    } else if (s.station === 'relations') {
      data = relation(s.relationSize, s.relationMask);
      const labels = Array.from({length: data.size}, (_, i) => i + 1);
      panels = [table('R ⊆ S × S: row is the first coordinate', labels, labels, data.table, {editable: 'relations'}),
        {kind: 'relation', title: 'Every included ordered pair', nodes: labels.map((label, i) => ({id: String(i), label: String(label), x: 220 + 100 * Math.cos(2 * Math.PI * i / data.size), y: 190 + 95 * Math.sin(2 * Math.PI * i / data.size)})),
          edges: data.pairs.map(([i, j]) => ({from: String(i), to: String(j), label: '(' + (i + 1) + ',' + (j + 1) + ')'}))}];
      readout = data.pairSlots + ' independent ordered-pair slots give 2^' + data.pairSlots + ' = ' + data.relationCount + ' relations. Selected relation: ' + data.pairs.length + ' pairs. ' + Object.entries(data.properties).map(([k, v]) => k + ': ' + (v ? 'yes' : 'no')).join('; ') + '.';
      proof = ['A binary relation on S is a subset of S×S. On n elements, the product has n² ordered pairs.', 'Each pair is independently included or omitted. This is a bijection between relations and n²-bit strings, giving exactly 2^(n²).', 'The property checks quantify over every element, ordered pair and triple of the displayed finite domain. Failed properties retain all counterexamples below.'];
      boundary = 'These are finite structures in a one-relation language. They are not finite models of PA or ZFC, and no infinite-model conclusion follows from their enumeration.';
    } else if (s.station === 'incomplete') {
      const cases = {
        pa: {effective: true, consistent: true, arithmetic: true, applies: true, label: 'PA, under the consistency hypothesis'},
        infinite: {effective: true, consistent: true, arithmetic: true, applies: true, label: 'A consistent effective extension of arithmetic'},
        true: {effective: false, consistent: true, arithmetic: true, applies: false, label: 'Th(N): all truths of standard arithmetic'},
        weak: {effective: true, consistent: true, arithmetic: false, applies: false, label: 'Presburger arithmetic'},
        inconsistent: {effective: true, consistent: false, arithmetic: true, applies: false, label: 'An inconsistent classical extension'}
      };
      data = {...cases[s.theory], extension: s.extension};
      const rows = [['Effective axiom enumeration', data.effective], ['Consistency hypothesis', data.consistent], ['Enough arithmetic (e.g. extends Q)', data.arithmetic]];
      const labels = data.applies ? Array.from({length: s.extension + 1}, (_, i) => i ? 'T' + i + ' = T' + (i - 1) + ' + R' + (i - 1) : 'T0: effective consistent arithmetic') : [data.label, 'A required hypothesis is absent'];
      panels = [table('Theorem hypotheses, not runtime verification', rows.map(r => r[0]), ['Assumed'], rows.map(r => [r[1]])), graph(labels, labels.slice(1).map((_, i) => [i, i + 1, 'add a true independent Rosser sentence']), 'A finite chain of stronger theories')];
      readout = data.applies ? 'Gödel–Rosser applies under these stated hypotheses. Adding ' + s.extension + ' true independent sentences leaves an effective consistent arithmetic theory; a new independent sentence remains.' : s.theory === 'true' ? 'True Arithmetic is complete and consistent but is not effectively enumerable. This abandons an essential hypothesis, rather than supplying a machine that knows every truth.' : s.theory === 'weak' ? 'Addition-only Presburger arithmetic is decidable and complete; it cannot express enough arithmetic for this incompleteness theorem.' : 'Classical inconsistency proves every sentence and its negation. That is not a reliable complete account of arithmetic truth.';
      proof = ['The strengthened first theorem assumes a consistent computably enumerable theory containing enough arithmetic. It does not require finitely many axioms.', 'Gödel–Rosser supplies a sentence neither proved nor refuted in that fixed theory. Its standard truth is assessed in the metatheory under the consistency hypothesis.', 'A finite true extension changes the theory, not the universal limitation. A sentence may be provable in a stronger theory without being provable in the original one.'];
      boundary = 'The graph records a theorem schema. It does not generate arithmetized Rosser sentences, decide consistency, check arbitrary axioms, or exhibit a proof in PA.';
    } else if (s.station === 'consistency') {
      let ordinal = 'ω'; const ordinals = [ordinal];
      for (let i = 1; i < s.ordinalDepth; i++) { ordinal = 'ω^(' + ordinal + ')'; ordinals.push(ordinal); }
      data = {ordinals, supremum: 'ε₀', internal: s.proofView === 'internal', consistencyAssumed: true};
      panels = [table('Increasing ordinal notations, with no numeric scale', ordinals.map((_, i) => i + 1), ['Notation'], ordinals.map(x => [x])),
        graph(data.internal ? ['PA with its standard proof predicate', 'Con(PA): no PA proof of contradiction', 'Not a PA theorem, if PA is consistent'] : ['PRA + the required induction up to ε₀', 'Gentzen’s reduction of PA derivations', 'Con(PA), proved in this metatheory'], [[0, 1, data.internal ? 'expresses' : 'supports'], [1, 2, data.internal ? 'second incompleteness' : 'well-founded descent']], 'Where the proof lives')];
      readout = data.internal ? 'For the usual arithmetization and derivability conditions, consistent PA cannot prove Con(PA). Expressing Con(PA) is not proving it.' : 'Gentzen’s argument uses transfinite induction beyond what PA proves. PRA plus the required ε₀ induction is a sufficient metatheory; it need not contain every theorem of PA.';
      proof = ['Second incompleteness concerns a specified internal consistency sentence and the standard provability conditions.', 'An external argument can establish that consistency using additional principles. This does not produce the forbidden internal PA proof.', 'The displayed finite ω-tower sequence has supremum ε₀ over all finite depths. No displayed last tower equals ε₀, and a finite diagram does not verify well-foundedness.'];
      boundary = 'Ordinal text and arrows record logical dependencies and order, not measurable distance or a numerical animation of transfinite induction.';
    } else if (s.station === 'skolem') {
      data = {viewpoint: s.viewpoint, modelAssumption: 'M is a countable model of ZFC, in the metatheory',
        inside: 'M ⊨ “there is no bijection ω→A”', outside: 'Externally, both ω^M and A^M are countably infinite, so a bijection between them exists',
        externalBijectionRepresentedInM: false};
      panels = [graph(['Consistent ZFC in its countable first-order language', 'Completeness: a ZFC model exists and is infinite', 'Downward Löwenheim–Skolem: a countable model M'], [[0, 1, 'metatheory'], [1, 2, 'elementary submodel']], 'Countable-model existence, conditional on consistency'),
        graph(s.viewpoint === 'inside' ? ['Quantifier: functions f belonging to M', 'M’s naturals ω^M and its set A', 'No such internal f is a bijection'] : ['Quantifier: external functions', 'The external countable sets ω^M and A^M', 'An external bijection has no internal function witness'], [[0, 1, 'domain of the formula'], [1, 2, 'different quantifier domain']], 'Internal and external cardinal statements')];
      readout = s.viewpoint === 'inside' ? data.inside + '. The quantifier ranges over functions in M. An external enumeration is not an internal witness.' : data.outside + '. No function element of M represents that bijection. External N and M’s possibly nonstandard ω^M must not be silently identified.';
      proof = ['In the usual classical metatheory, consistency plus completeness and downward Löwenheim–Skolem yields a countable model of ZFC.', 'For an internally uncountable set, its members in M form an externally countable set. M contains no function witnessing the forbidden internal bijection.', 'The two statements use different domains of quantification. First-order completeness does not imply a theory is complete, categorical, or has only countable models.'];
      boundary = 'No actual countable model of ZFC is computed here. The boxes are theorem statements and quantifier scopes; they are not a finite approximation to its membership relation.';
    } else if (s.station === 'independence') {
      const facts = {
        choice: {name: 'AC', base: 'ZF', status: 'Independent of ZF, assuming consistency', branches: ['ZF + AC', 'ZF + ¬AC'], detail: 'Both branches are relatively consistent. The axiom’s independence is a proved result, not inferred merely from a proof that uses it.'},
        wellorder: {name: 'Well-ordering theorem', base: 'ZF', status: 'Equivalent to AC over ZF', branches: ['ZF + well-ordering', 'ZF + ¬well-ordering'], detail: 'Because ZF proves the equivalence with AC, the same independence transfers under the consistency hypothesis.'},
        finite: {name: 'Finite-family choice', base: 'ZF', status: 'A theorem of ZF', branches: ['ZF proves finite-family choice'], detail: 'Induction on a finite family suffices. A proof using full AC does not show that AC was necessary.'},
        ch: {name: 'CH', base: 'ZFC', status: 'Independent of ZFC, assuming consistency', branches: ['ZFC + CH', 'ZFC + ¬CH'], detail: 'Relative consistency of each branch rules out a ZFC proof of either side if ZFC is consistent. A claimed ZFC proof must be checked; one cannot assume its error as a new theorem.'},
        unknown: {name: 'An unspecified theorem T', base: 'ZF', status: 'Unknown from the stated proof dependency', branches: ['Known: ZFC proves T', 'Unsettled here: whether ZF proves T'], detail: 'AC’s independence alone does not establish T’s independence. T may already be a ZF theorem, or may need additional axioms; another argument is required.'}
      };
      data = facts[s.statement];
      const labels = [data.base + ': stated base theory', ...data.branches];
      panels = [graph(labels, data.branches.map((_, i) => [0, i + 1, s.statement === 'finite' ? 'ordinary finite induction' : s.statement === 'unknown' ? 'proof-dependency information only' : 'relative consistency / equivalence']), 'Axiom and statement dependencies'),
        table('What has actually been established', ['Statement', 'Status', 'Necessary qualification'], ['Fact'], [[data.name], [data.status], [s.statement === 'finite' || s.statement === 'unknown' ? 'No independence inference from a proof alone' : 'Relative to consistency of the base theory']])];
      readout = data.name + ': ' + data.status + '. ' + data.detail;
      proof = ['A proof in ZF+AC is a proof under those axioms. Removing AC requires an independent argument about the particular conclusion.', 'For an independent sentence φ, both T+φ and T+¬φ are relatively consistent when T is consistent. This is a metatheorem, not a construction of models by clicking.', 'CH states that no cardinal lies strictly between |N| and |R|. In ZFC this is equivalent to 2^ℵ₀=ℵ₁; set sizes are not positions on a metric axis.'];
      boundary = 'The activity displays established dependency facts and an explicitly unknown case. It neither runs forcing nor decides arbitrary theorem dependence.';
    } else {
      const constraints = Array.from({length: s.bound + 1}, (_, n) => ({n, label: 'c > ' + n, holds: s.witness > n}));
      data = {constraints, witness: s.witness, allSatisfied: constraints.every(c => c.holds), canonicalWitness: s.bound + 1};
      panels = [table('The whole displayed finite set of demands', constraints.map(c => c.label), ['Holds for c=' + s.witness], constraints.map(c => [c.holds])),
        graph(['For each finite set of demands, choose c>K', 'N with this interpretation satisfies that finite subset', 'Compactness gives a model of PA + every c>n', 'There c exceeds every standard numeral'], [[0, 1, 'finite witness'], [1, 2, 'first-order compactness'], [2, 3, 'nonstandard element']], 'Finite witnesses and an infinite-model conclusion')];
      readout = 'The trial c=' + s.witness + (data.allSatisfied ? ' satisfies' : ' fails') + ' the finite demands c>0,…,c>' + s.bound + '. c=' + data.canonicalWitness + ' is a witness for all these demands. No standard natural number satisfies every demand for all n.';
      proof = ['Add a new constant c and the sentences c>n̄ for every standard natural number n to PA.', 'Any finite subset uses only finitely many such demands. Interpret c above their largest n in the standard natural numbers, where the PA axioms hold.', 'Compactness supplies a model of the entire theory. Its c is not any standard numeral. PA is respected; this does not create a largest natural number or a standard value “infinity”.'];
      boundary = 'The table verifies every displayed finite inequality. The infinite conclusion is the compactness theorem, not a limit of the slider’s finite witnesses.';
    }
    return {state, station: s.station, data, panels, readout, proof, boundary,
      note: 'Finite witnesses are calculated exactly. Infinite cardinalities, consistency, model existence and independence require the stated metatheorems; diagram layout has no metric meaning.'};
  }
  function snapshot(raw) { return clone(build(raw)); }
  function el(tag, attrs = {}, ...children) {
    const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs)) if (v !== undefined) e.setAttribute(k, String(v));
    for (const child of children.flat()) if (child !== null && child !== undefined) e.append(typeof child === 'string' ? document.createTextNode(child) : child);
    return e;
  }
  function svg(tag, attrs = {}, text) { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v)); if (text !== undefined) e.textContent = text; return e; }
  function render(item, hooks) {
    if (item?.props?.scenario !== scenario) return null;
    const uid = 'logic-' + ++serial, root = el('section', {class: 'card lesson-model math-logic-lab', 'data-renderer': 'math-logic-lab', 'aria-labelledby': uid + '-title'});
    let model = build(initial); const inputs = new Map(), controlsBox = el('div', {class: 'logic-controls'});
    const stateBus = typeof window !== 'undefined' ? window.PrimerLessonStateBus : null;
    const live = el('p', {class: 'logic-live', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true'});
    function update(next, announce, fromShared = false) { model = build(next); refresh(announce); if (!fromShared) stateBus?.publish('math.5.logic', root, clone(model.state)); }
    for (const c of controls) {
      const id = uid + '-' + c.key, input = c.options ? el('select', {id, 'data-logic-control': c.key}) : el('input', {id, type: 'number', min: c.min, max: c.max, step: c.step, 'data-logic-control': c.key});
      if (c.options) for (const o of c.options) input.append(el('option', {value: o.value}, o.label));
      const label = el('label', {for: id}, c.label, input);
      input.addEventListener('change', () => { if (!c.options && (input.value.trim() === '' || !Number.isFinite(Number(input.value)))) { input.setAttribute('aria-invalid', 'true'); live.textContent = 'Enter a finite whole number; the last accepted construction is retained.'; return; } input.removeAttribute('aria-invalid'); update({...model.state, [c.key]: c.options ? input.value : Number(input.value)}, true); });
      controlsBox.append(label); inputs.set(c.key, {c, input, label});
    }
    const decimalInput = el('textarea', {id: uid + '-decimals', rows: 8, spellcheck: 'false', 'data-logic-decimals': '', 'aria-describedby': uid + '-decimal-help'});
    const decimalBox = el('div', {}, el('label', {for: uid + '-decimals'}, 'Eight rows, each with exactly eight decimal digits', decimalInput), el('p', {id: uid + '-decimal-help'}, 'These are prefixes after the decimal point. Canonical infinite expansions are an assumption of the proof.'));
    const decimalApply = el('button', {type: 'button', class: 'btn ghost small', 'data-logic-action': 'decimals'}, 'Use these prefixes');
    decimalApply.addEventListener('click', () => {
      const rows = decimalInput.value.trim().split(/\r?\n/).map(r => r.trim());
      if (rows.length !== 8 || rows.some(r => !/^\d{8}$/.test(r))) { decimalInput.setAttribute('aria-invalid', 'true'); live.textContent = 'Enter eight lines of eight digits. The last accepted table is retained.'; return; }
      decimalInput.removeAttribute('aria-invalid'); update({...model.state, decimalRows: rows}, true);
    }); decimalBox.append(decimalApply);
    const presets = el('div', {class: 'logic-actions'});
    for (const [name, patch] of [['Empty relation', {station: 'relations', relationMask: 0}], ['Identity on three elements', {station: 'relations', relationSize: 3, relationMask: 273}], ['Witness c=K+1', 'witness']]) {
      const button = el('button', {type: 'button', class: 'btn ghost small', 'data-logic-preset': name}, name);
      button.addEventListener('click', () => update({...model.state, ...(patch === 'witness' ? {station: 'compactness', witness: model.state.bound + 1} : patch)}, true)); presets.append(button);
    }
    const reset = el('button', {type: 'button', class: 'btn ghost small', 'data-logic-action': 'reset'}, 'Reset'); reset.addEventListener('click', () => update(initial, true));
    const enlarge = el('button', {type: 'button', class: 'btn ghost small', 'data-logic-action': 'enlarge', 'aria-pressed': 'false'}, 'Read diagram labels at full size');
    enlarge.addEventListener('click', () => { const on = enlarge.getAttribute('aria-pressed') !== 'true'; enlarge.setAttribute('aria-pressed', String(on)); root.classList.toggle('is-enlarged', on); enlarge.textContent = on ? 'Fit diagrams' : 'Read diagram labels at full size'; });
    const panelsBox = el('div', {class: 'logic-panels'}), readout = el('p', {class: 'logic-readout'}), proofBox = el('ol', {class: 'logic-proof'}), boundary = el('p', {class: 'spatial-note logic-boundary'}), witnesses = el('details', {}, el('summary', {}, 'Exact witness and counterexample ledger')), witnessText = el('pre', {class: 'logic-witness'}); witnesses.append(witnessText);
    root.append(el('h3', {id: uid + '-title'}, item.title || 'Diagonal constructions, models, and the limits of proof'), el('p', {class: 'model-instructions'}, item.instructions || 'Edit exact finite witnesses, then inspect the hypotheses and quantifier domains of each infinite theorem.'), controlsBox, decimalBox, presets, reset, enlarge, panelsBox, readout, el('h4', {}, 'Why the conclusion follows'), proofBox, boundary, witnesses,
      el('p', {class: 'spatial-note'}, 'Two-dimensional tables and dependency diagrams preserve memberships, ordered pairs and logical scope. Their layout does not encode cardinal size, ordinal distance, or physical depth.'),
      el('p', {class: 'spatial-note'}, el('a', {href: 'https://philippschlicht.github.io/teaching/files/mathematicallogic2021.pdf', target: '_blank', rel: 'noopener noreferrer'}, 'Logic and model theory · Schlicht'), ' · ', el('a', {href: 'https://math.berkeley.edu/~marks/notes/set_theory_notes_4.pdf', target: '_blank', rel: 'noopener noreferrer'}, 'Set theory · Marks'), ' · ', el('a', {href: 'https://math.berkeley.edu/~marks/notes/computability_notes_v1.pdf', target: '_blank', rel: 'noopener noreferrer'}, 'Computability and incompleteness · Marks'), ' · ', el('a', {href: 'https://www.math.uwaterloo.ca/~snburris/htdocs/LOGIC/LOGICIANS/notes2.pdf', target: '_blank', rel: 'noopener noreferrer'}, 'Gentzen’s arithmetic consistency argument · Burris'), '. Original code and diagrams.'), live);
    if (hooks?.speakButton) root.append(hooks.speakButton(() => model.readout + ' ' + model.proof.join(' ') + ' ' + model.boundary));
    function renderTable(p, index) {
      const out = el('div', {class: 'logic-table-scroll', tabindex: 0, role: 'region', 'aria-label': p.title}), t = el('table', {'data-logic-table': index}, el('caption', {}, p.title));
      t.append(el('thead', {}, el('tr', {}, el('th', {scope: 'col', 'aria-label': 'Row index'}, p.editable ? 'i' : 'Item'), p.columnLabels.map(x => el('th', {scope: 'col'}, String(x))))));
      const body = el('tbody'); p.cells.forEach((row, i) => {
        const tr = el('tr', {}, el('th', {scope: 'row'}, String(p.rowLabels[i])));
        row.forEach((v, j) => {
          const cell = el('td', {class: p.diagonal && i === j ? 'logic-diagonal' : '', 'data-logic-cell': i + ',' + j});
          if (p.editable) {
            const b = el('button', {type: 'button', 'aria-pressed': String(v), 'aria-label': (p.editable === 'powerset' ? 'Subset row ' : 'Relation row ') + (i + 1) + ', element ' + (j + 1) + ': ' + (v ? 'included' : 'omitted'), 'data-logic-toggle': p.editable + ':' + i + ':' + j}, v ? '1' : '0');
            b.addEventListener('click', () => {
              const next = clone(model.state); if (p.editable === 'powerset') next.rows[i] ^= 2 ** j; else next.relationMask ^= 2 ** (i * next.relationSize + j);
              update(next, true); root.querySelector('[data-logic-toggle="' + p.editable + ':' + i + ':' + j + '"]')?.focus();
            }); cell.append(b);
          } else cell.textContent = typeof v === 'boolean' ? (v ? 'yes' : 'no') : String(v);
          tr.append(cell);
        }); body.append(tr);
      }); t.append(body); out.append(t); return out;
    }
    function renderGraph(p, index) {
      const height = p.kind === 'relation' ? 350 : Math.max(300, p.nodes.length * 66 + 42), image = svg('svg', {viewBox: '0 0 440 ' + height, role: 'img', 'aria-labelledby': uid + '-graph-' + index, 'data-logic-graph': index});
      image.append(svg('title', {id: uid + '-graph-' + index}, p.title), svg('desc', {}, p.nodes.map(n => n.label).join('; ') + '. ' + p.edges.map(e => e.label).join('; ')));
      const nodes = new Map(p.nodes.map(n => [n.id, n]));
      for (const e of p.edges) {
        const a = nodes.get(e.from), b = nodes.get(e.to);
        if (p.kind === 'relation') {
          const dx = b.x - a.x, dy = b.y - a.y, length = Math.hypot(dx, dy), ux = length ? dx / length : 0, uy = length ? dy / length : 0;
          if (!length) image.append(svg('path', {d: 'M' + (a.x - 12) + ' ' + (a.y - 12) + ' C' + (a.x - 62) + ' ' + (a.y - 72) + ' ' + (a.x + 62) + ' ' + (a.y - 72) + ' ' + (a.x + 12) + ' ' + (a.y - 12), fill: 'none', stroke: '#3e7085', 'stroke-width': 2, 'data-logic-edge': e.from + ',' + e.to}));
          else {
            const x = b.x - 21 * ux, y = b.y - 21 * uy;
            image.append(svg('line', {x1: a.x + 21 * ux, y1: a.y + 21 * uy, x2: x, y2: y, stroke: '#3e7085', 'stroke-width': 2, 'data-logic-edge': e.from + ',' + e.to}), svg('path', {d: 'M' + (x - 10 * ux + 5 * uy) + ' ' + (y - 10 * uy - 5 * ux) + ' L' + x + ' ' + y + ' L' + (x - 10 * ux - 5 * uy) + ' ' + (y - 10 * uy + 5 * ux), fill: 'none', stroke: '#3e7085', 'stroke-width': 2}));
          }
        } else image.append(svg('line', {x1: a.x, y1: a.y + 20, x2: b.x, y2: b.y - 20, stroke: '#3e7085', 'stroke-width': 2}), svg('path', {d: 'M' + (b.x - 5) + ' ' + (b.y - 28) + ' L' + b.x + ' ' + (b.y - 20) + ' L' + (b.x + 5) + ' ' + (b.y - 28), fill: 'none', stroke: '#3e7085', 'stroke-width': 2}));
      }
      for (const n of p.nodes) {
        if (p.kind === 'relation') image.append(svg('circle', {cx: n.x, cy: n.y, r: 19, fill: '#f5efdf', stroke: '#263b46'}), svg('text', {x: n.x, y: n.y + 5, 'text-anchor': 'middle', fill: '#263b46', 'font-size': 16}, n.label));
        else {
          image.append(svg('rect', {x: 10, y: n.y - 22, width: 420, height: 44, rx: 6, fill: '#f5efdf', stroke: '#3e7085'}));
          const words = n.label.split(' '), lines = []; let current = '';
          for (const word of words) { if ((current + ' ' + word).trim().length > 54 && current) { lines.push(current); current = word; } else current = (current + ' ' + word).trim(); } lines.push(current);
          const text = svg('text', {x: n.x, y: n.y - (lines.length > 1 ? 4 : -4), 'text-anchor': 'middle', fill: '#263b46', 'font-size': 12});
          lines.forEach((line, i) => text.append(svg('tspan', {x: n.x, dy: i ? 15 : 0}, line))); image.append(text);
        }
      }
      return el('div', {class: 'logic-graph'}, el('h4', {}, p.title), el('div', {class: 'logic-graph-viewport', tabindex: 0, role: 'region', 'aria-label': p.title + '; use full-size labels and scroll'}, image), el('ol', {class: 'logic-edge-ledger'}, p.edges.map(e => el('li', {}, nodes.get(e.from).label + ' → ' + nodes.get(e.to).label + ': ' + e.label))));
    }
    function refresh(announce) {
      root.setAttribute('data-logic-state', JSON.stringify(model.state));
      for (const {c, input, label} of inputs.values()) { label.hidden = Boolean(c.stations && !c.stations.includes(model.station)); input.disabled = label.hidden; input.value = String(model.state[c.key]); }
      decimalBox.hidden = model.station !== 'decimal'; if (model.station === 'decimal') decimalInput.value = model.state.decimalRows.join('\n');
      panelsBox.replaceChildren(...model.panels.map((p, i) => p.kind === 'table' ? renderTable(p, i) : renderGraph(p, i)));
      readout.textContent = model.readout; proofBox.replaceChildren(...model.proof.map(p => el('li', {}, p))); boundary.textContent = model.boundary;
      witnessText.textContent = JSON.stringify(model.data, null, 2);
      if (announce) live.textContent = model.readout;
    }
    root.setModelState = (values, announce = false, fromShared = false) => { update({...model.state, ...values}, announce, fromShared); return clone(model.state); };
    root.getModelSpeech = () => model.readout + ' ' + model.proof.join(' ') + ' ' + model.boundary;
    stateBus?.join('math.5.logic', root, values => root.setModelState(values, false, true));
    refresh(false); return root;
  }
  const api = Object.freeze({scenario, initial, stations, controls, normalize, diagonal, decimalDiagonal, relation, build, snapshot, render});
  if (typeof window !== 'undefined') window.PrimerMathLogicLab = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
}());
