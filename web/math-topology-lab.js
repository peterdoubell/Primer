/* Finite open-set calculations and explicit infinite proofs; no formula parser. */
(function () {
  'use strict';
  const PI = Math.PI, TAU = 2 * PI, NS = 'http://www.w3.org/2000/svg';
  const SCENARIO = 'math.5.topology.opens-covers-surfaces';
  const INK = '#263b46', TEAL = '#317e78', CORAL = '#b96652', BLUE = '#3e7085', GRID = '#d5cfbf';
  const initial = Object.freeze({ station: 'T1', familyMask: 135, domainTopology: 'discrete', targetTopology: 'indiscrete', mapCode: 21,
    coverN: 8, coverMesh: 6, cofiniteA: 3, cofiniteB: 4, sineCycles: 8, sineTarget: .5, sequenceN: 4,
    genus: 2, refinement: 1, stretch: 1, bend: 0, circleDomain: 'halfopen', logEpsilon: -2, angleFraction: .25, theoremStep: 4 });
  const controls = Object.freeze([
    { key: 'station', label: 'Station', options: [['T1', 'T1 · Open-set axioms'], ['T2', 'T2 · Continuity by preimages'], ['T3', 'T3 · Compactness and covers'], ['T4', 'T4 · Cofinite T1, not Hausdorff'], ['T5', 'T5 · Connected, not path-connected'], ['T6', 'T6 · Genus and homeomorphic deformation'], ['T7', 'T7 · Circle quotient and inverse']] },
    { key: 'familyMask', label: 'Proposed family code (0–255; table explains bits)', stations: ['T1'], min: 0, max: 255, step: 1 },
    { key: 'domainTopology', label: 'Domain open sets', stations: ['T2'], options: [['discrete', 'Discrete: all subsets'], ['indiscrete', 'Indiscrete: empty and whole'], ['chain', 'Chain: empty, {a}, {a,b}, whole'], ['fork', 'Fork: empty, {a}, {b}, {a,b}, whole']] },
    { key: 'targetTopology', label: 'Target open sets', stations: ['T2'], options: [['discrete', 'Discrete: all subsets'], ['indiscrete', 'Indiscrete: empty and whole'], ['chain', 'Chain: empty, {a}, {a,b}, whole'], ['fork', 'Fork: empty, {a}, {b}, {a,b}, whole']] },
    { key: 'mapCode', label: 'Map code f(a)+3f(b)+9f(c), a=0,b=1,c=2', stations: ['T2'], min: 0, max: 26, step: 1 },
    { key: 'coverN', label: 'Largest chosen cover index N', stations: ['T3'], min: 2, max: 80, step: 1 },
    { key: 'coverMesh', label: 'Closed-interval example: grid intervals m', stations: ['T3'], min: 2, max: 16, step: 1 },
    { key: 'cofiniteA', label: 'First finite exclusion count', stations: ['T4'], min: 1, max: 12, step: 1 },
    { key: 'cofiniteB', label: 'Second finite exclusion count', stations: ['T4'], min: 1, max: 12, step: 1 },
    { key: 'sineCycles', label: 'Resolved oscillations in finite graph window', stations: ['T5'], min: 2, max: 24, step: 1 },
    { key: 'sineTarget', label: 'Closure target y on vertical segment', stations: ['T5'], min: -1, max: 1, step: .25 },
    { key: 'sequenceN', label: 'Displayed closure-sequence index n', stations: ['T5'], min: 1, max: 20, step: 1 },
    { key: 'genus', label: 'Genus g (selects a different closed surface)', stations: ['T6'], min: 0, max: 3, step: 1 },
    { key: 'refinement', label: 'Mesh subdivision level', stations: ['T6'], min: 1, max: 2, step: 1 },
    { key: 'stretch', label: 'Positive horizontal stretch s', stations: ['T6'], min: .5, max: 2, step: .125 },
    { key: 'bend', label: 'Invertible shear b in x′ = sx + by', stations: ['T6'], min: -.75, max: .75, step: .125 },
    { key: 'circleDomain', label: 'Circle map domain / identification', stations: ['T7'], options: [['halfopen', '[0,2π): bijection, inverse discontinuous'], ['closed', '[0,2π]: compact surjection, not injective'], ['quotient', '[0,2π] with endpoints identified']] },
    { key: 'logEpsilon', label: 'log₁₀ angular approach ε', stations: ['T7'], min: -5, max: -.5, step: .5 },
    { key: 'angleFraction', label: 'Selected angle t / 2π', stations: ['T7'], min: 0, max: .875, step: .125 },
    { key: 'theoremStep', label: 'Compact–Hausdorff proof steps', stations: ['T7'], min: 1, max: 4, step: 1 },
  ].map(c => Object.freeze({ ...c, stations: c.stations ? Object.freeze(c.stations) : undefined,
    options: c.options ? Object.freeze(c.options.map(([value, label]) => Object.freeze({ value, label }))) : undefined })));
  let serial = 0;
  const fmt = x => String(Number(x.toPrecision(6)));
  const yes = b => b ? 'yes' : 'no';
  const setName = m => m === 0 ? '∅' : '{' + ['a', 'b', 'c'].filter((_, j) => m & 1 << j).join(',') + '}';
  const family = code => Array.from({ length: 8 }, (_, j) => j).filter(j => code & 1 << j);
  const topologyCodes = Object.freeze({ discrete: 255, indiscrete: 129, chain: 139, fork: 143 });
  function normalize(raw) {
    const input = raw && typeof raw === 'object' ? raw : {}, s = {};
    for (const c of controls) {
      const v = input[c.key];
      if (c.options) s[c.key] = c.options.some(o => o.value === v) ? v : initial[c.key];
      else { const valid = typeof v === 'number' || typeof v === 'string' && v.trim() !== '';
        const n = valid && Number.isFinite(Number(v)) ? Number(v) : initial[c.key];
        s[c.key] = Number((c.min + Math.round((Math.min(c.max, Math.max(c.min, n)) - c.min) / c.step) * c.step).toFixed(8)); }
    }
    return s;
  }
  function finiteAxioms(code) {
    if (!Number.isInteger(code) || code < 0 || code > 255) throw new RangeError('Family code must be an integer in [0,255].');
    const opens = family(code), missing = [0, 7].filter(j => !opens.includes(j)), unions = [], intersections = [];
    // On a finite set, any arbitrary indexed union reduces to a subfamily of
    // these finitely many distinct subsets. This is an exhaustive finite proof.
    for (let selected = 0; selected < 2 ** opens.length; selected++) {
      const members = opens.filter((_, j) => selected & 1 << j), result = members.reduce((a, b) => a | b, 0);
      if (!opens.includes(result)) unions.push({ members, result });
    }
    for (let j = 0; j < opens.length; j++) for (let k = j; k < opens.length; k++) {
      const result = opens[j] & opens[k]; if (!opens.includes(result)) intersections.push({ members: [opens[j], opens[k]], result });
    }
    return { code, opens, missing, unions, intersections, valid: !missing.length && !unions.length && !intersections.length,
      subfamilyCount: 2 ** opens.length, pairCount: opens.length * (opens.length + 1) / 2 };
  }
  function finiteSeparation(opens) {
    const t1 = [1, 2, 4].every(bit => opens.includes(7 ^ bit));
    const pairs = [[0, 1], [0, 2], [1, 2]].map(([a, b]) => ({ a, b, disjoint: opens.some(u => u & 1 << a && opens.some(v => v & 1 << b && !(u & v))) }));
    return { t1, hausdorff: pairs.every(p => p.disjoint), pairs };
  }
  function finiteModel(raw) {
    const s = normalize(raw), d = finiteAxioms(s.familyMask), sep = finiteSeparation(d.opens);
    return { ...d, separation: d.valid ? sep : null, subsets: Array.from({ length: 8 }, (_, mask) => ({ mask, name: setName(mask), included: d.opens.includes(mask), contribution: 1 << mask })),
      theorem: 'A topology contains ∅ and X, is closed under arbitrary unions and finite intersections. On this three-point universe, enumerating every distinct subfamily checks arbitrary unions exactly; pairwise intersection closure plus X proves finite intersection closure by induction. Complement closure is not an axiom.' };
  }
  function decodeMap(code) { if (!Number.isInteger(code) || code < 0 || code > 26) throw new RangeError('Map code must lie in [0,26].'); return [code % 3, Math.floor(code / 3) % 3, Math.floor(code / 9)]; }
  function preimage(mapping, mask) { return mapping.reduce((a, y, x) => mask & 1 << y ? a | 1 << x : a, 0); }
  function continuityModel(raw) {
    const s = normalize(raw), domain = family(topologyCodes[s.domainTopology]), target = family(topologyCodes[s.targetTopology]), mapping = decodeMap(s.mapCode);
    const preimages = target.map(open => { const inverseImage = preimage(mapping, open); return { open, preimage: inverseImage, openInDomain: domain.includes(inverseImage) }; });
    const continuous = preimages.every(p => p.openInDomain), injective = new Set(mapping).size === 3, onto = injective;
    const images = domain.map(open => ({ open, image: mapping.reduce((a, y, x) => open & 1 << x ? a | 1 << y : a, 0) }));
    const inverseContinuous = injective ? images.every(p => target.includes(p.image)) : null;
    const separation = finiteSeparation(target);
    return { domain, target, mapping, preimages, images, continuous, injective, onto, bijective: injective, inverseContinuous,
      homeomorphism: continuous && injective && inverseContinuous, targetHausdorff: separation.hausdorff, domainCompact: true,
      theorem: 'Continuity is equivalent to every target open set having an open preimage. A homeomorphism also requires bijectivity and a continuous inverse. All finite spaces are compact, but a finite target is Hausdorff only when discrete. The identity from discrete to indiscrete is a continuous bijection whose inverse fails: compactness alone does not repair it.' };
  }
  function coverModel(raw) {
    const s = normalize(raw), N = s.coverN, m = s.coverMesh, radius = .75 / m;
    return { N, witness: 1 / (2 * N), omittedBoundary: 1 / N, selected: Array.from({ length: N - 1 }, (_, j) => ({ n: j + 2, start: 1 / (j + 2), end: 1, startIncluded: false, endIncluded: false })),
      finiteUnion: { start: 1 / N, end: 1, startIncluded: false, endIncluded: false },
      closedCover: Array.from({ length: m + 1 }, (_, j) => ({ center: j / m, start: j / m - radius, end: j / m + radius })), radius, maximumCenterDistance: .5 / m,
      openIntervalCompact: false, closedIntervalCompact: true,
      theorem: 'For every x∈(0,1), choose an integer n>max(1/x,1): x∈(1/n,1). For ANY nonempty finite selection let N be its largest index; the union is (1/N,1), so x=1/(2N) remains uncovered. Thus the infinite cover has no finite subcover. The same family does not cover [0,1], because 0 and 1 are missing. Heine–Borel, rather than this drawn example, proves [0,1] compact. The second panel is one separate finite open cover of [0,1]; every point is within 1/(2m)<3/(4m) of a grid center.' };
  }
  function cofiniteModel(raw) {
    const s = normalize(raw), excludedA = Array.from({ length: s.cofiniteA }, (_, j) => j), excludedB = Array.from({ length: s.cofiniteB }, (_, j) => j + 2), excludedUnion = [...new Set([...excludedA, ...excludedB])].sort((a, b) => a - b);
    const witness = Math.max(...excludedUnion) + 1;
    return { universe: 'infinite real line', excludedA, excludedB, excludedUnion, witness, t1: true, hausdorff: false, compact: true,
      theorem: 'Here X=ℝ is infinite, with ∅ and complements of finite sets open. A union with at least one nonempty member has complement contained in that member’s finite exclusions; a union of only empty sets is empty. Finite intersections of nonempty cofinite opens have finite exclusion unions; an empty member makes the intersection empty. Each singleton is closed, so the space is T1. Any two nonempty opens intersect: their combined finite exclusions cannot exhaust ℝ. It is not Hausdorff, hence no metric induces this topology. This infinite cofinite space is also compact: choose one nonempty set from any open cover; its finite complement needs only finitely many further cover members. The marked integers are examples, not a finite replacement for ℝ.' };
  }
  function sineModel(raw) {
    const s = normalize(raw), uMax = 1 + TAU * s.sineCycles, samples = 48 * s.sineCycles;
    const graph = Array.from({ length: samples + 1 }, (_, j) => { const u = 1 + (uMax - 1) * j / samples; return [1 / u, Math.sin(u)]; });
    const phase = Math.asin(s.sineTarget), sequence = Array.from({ length: 20 }, (_, j) => { const n = j + 1, u = phase + TAU * n; return { n, u, x: 1 / u, y: s.sineTarget }; });
    const selected = sequence[s.sequenceN - 1];
    return { graph, vertical: [[0, -1], [0, 1]], xMin: 1 / uMax, uMax, selected, sequence, target: [0, s.sineTarget],
      positiveExtrema: Array.from({ length: 12 }, (_, n) => [1 / (PI / 2 + TAU * (n + 1)), 1]), negativeExtrema: Array.from({ length: 12 }, (_, n) => [1 / (3 * PI / 2 + TAU * (n + 1)), -1]),
      connected: true, pathConnected: false, compact: true, pathComponents: 2,
      theorem: 'The graph on (0,1] is a continuous image of a connected interval. For every y∈[−1,1], xₙ=1/(arcsin(y)+2πn)>0 gives sin(1/xₙ)=y and xₙ→0; its closure is exactly the graph plus the vertical segment. A closure of a connected set is connected, and this closed bounded plane set is compact. A path leaving x=0 has a component (a,b) where x(t)>0 and x(a)=0. The intermediate value theorem forces it through x-values of arbitrarily small positive and negative sine extrema as t↓a; the y-coordinate would approach both +1 and −1, contradicting continuity. Thus no path connects the segment to the graph. The finite graph is truncated at x_min>0; it is never joined to x=0.' };
  }
  function deform(point, stretch, bend) { return [stretch * point[0] + bend * point[1], point[1], point[2]]; }
  function undeform(point, stretch, bend) { return [(point[0] - bend * point[1]) / stretch, point[1], point[2]]; }
  function surfaceMesh(genus, refinement = 1) {
    if (!Number.isInteger(genus) || genus < 0 || genus > 3 || ![1, 2].includes(refinement)) throw new RangeError('Genus 0–3 and refinement 1–2 required.');
    const factor = refinement, nx = (genus ? 4 * genus + 2 : 6) * factor, ny = 6 * factor;
    const holes = Array.from({ length: genus }, (_, h) => ({ x0: (2 + 4 * h) * factor, x1: (4 + 4 * h) * factor, y0: 2 * factor, y1: 4 * factor }));
    const active = (i, j) => !holes.some(h => i >= h.x0 && i < h.x1 && j >= h.y0 && j < h.y1);
    const vertices = [], faces = [], keyed = new Map(), boundary = new Set();
    const xy = (i, j) => [(i - nx / 2) / factor, (j - ny / 2) / factor];
    function height(i, j) {
      let distance = Math.min(i, nx - i, j, ny - j) / factor;
      for (const h of holes) { const dx = Math.max(h.x0 - i, 0, i - h.x1), dy = Math.max(h.y0 - j, 0, j - h.y1); distance = Math.min(distance, Math.hypot(dx, dy) / factor); }
      return .65 * Math.min(1.2, distance);
    }
    function vertex(i, j, side) {
      const z = height(i, j), key = i + ',' + j + ',' + (z === 0 ? 'boundary' : side);
      if (!keyed.has(key)) { const v = [...xy(i, j), side * z]; keyed.set(key, vertices.length); vertices.push(v); if (z === 0) boundary.add(vertices.length - 1); }
      return keyed.get(key);
    }
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) if (active(i, j)) for (const side of [1, -1]) {
      const corners = [[i, j], [i + 1, j], [i + 1, j + 1], [i, j + 1]].map(p => vertex(p[0], p[1], side)), center = vertex(i + .5, j + .5, side);
      for (let k = 0; k < 4; k++) { const tri = [corners[k], corners[(k + 1) % 4], center]; faces.push(side === 1 ? tri : [tri[1], tri[0], tri[2]]); }
    }
    const edgeMap = new Map();
    faces.forEach((f, index) => f.forEach((a, k) => { const b = f[(k + 1) % 3], key = Math.min(a, b) + ':' + Math.max(a, b); if (!edgeMap.has(key)) edgeMap.set(key, { vertices: [Math.min(a, b), Math.max(a, b)], faces: [], orientations: [] }); const edge = edgeMap.get(key); edge.faces.push(index); edge.orientations.push(a < b ? 1 : -1); }));
    const edges = [...edgeMap.values()], counts = { V: vertices.length, E: edges.length, F: faces.length }; counts.chi = counts.V - counts.E + counts.F;
    return { vertices, faces, edges, counts, boundary: [...boundary], holes, nx, ny, refinement,
      construction: 'Double a connected rectangular planar domain with g rectangular holes; identify corresponding vertices along every boundary component. Upper and lower interiors remain separate. Each retained grid cell is a four-triangle fan with a positive-height center, so no doubled face coincides flatly.' };
  }
  function surfaceModel(raw) {
    const s = normalize(raw), mesh = surfaceMesh(s.genus, s.refinement), deformed = mesh.vertices.map(p => deform(p, s.stretch, s.bend));
    const baseFigureEight = Array.from({ length: 129 }, (_, j) => { const t = TAU * j / 128; return [Math.sin(t), Math.sin(2 * t), 0]; });
    // Make the single shared crossing exact, rather than depend on sin(π).
    for (const j of [0, 64, 128]) baseFigureEight[j] = [0, 0, 0];
    const figureEight = baseFigureEight.map(p => deform(p, s.stretch, s.bend));
    const quotient = s.genus === 0 ? { V: 1, E: 0, F: 1, chi: 2, word: 'S²: one 0-cell and one 2-cell, constant attaching map' }
      : { V: 1, E: 2 * s.genus, F: 1, chi: 2 - 2 * s.genus, word: Array.from({ length: s.genus }, (_, j) => 'a' + (j + 1) + ' b' + (j + 1) + ' a' + (j + 1) + '⁻¹ b' + (j + 1) + '⁻¹').join(' · ') };
    return { genus: s.genus, mesh, vertices: deformed, faces: mesh.faces, edges: mesh.edges, counts: mesh.counts, quotient,
      figureEight, baseFigureEight, crossing: [0, 0, 0], jacobianDeterminant: s.stretch, closed: mesh.edges.every(e => e.faces.length === 2), oriented: mesh.edges.every(e => e.orientations[0] + e.orientations[1] === 0),
      metric: { originalChord: 2, transformedChord: 2 * s.stretch },
      inverseFormula: 'F⁻¹(x′,y′,z′)=((x′−b y′)/s,y′,z′), s>0',
      theorem: 'These are closed connected orientable surfaces: a planar region with g holes is doubled along its g+1 boundary circles. Its Euler characteristic is 2(1−g), also computed directly from the actual triangles V−E+F. The distinct CW quotient count uses a different cell decomposition, not the same triangle counts. F(x,y,z)=(sx+by,y,z) has a global continuous inverse for s>0 and the interpolation from s=1,b=0 keeps s positive; it cannot cut, glue or remove a handle. Changing g selects a different object. The figure-eight has one shared crossing vertex of valence four; this incidence survives F while lengths and angles may change. For closed connected orientable surfaces genus classifies homeomorphism type; genus alone is not a universal classifier of arbitrary spaces.' };
  }
  const compactHausdorffProof = Object.freeze([
    'For a continuous bijection f:X→Y with X compact and Y Hausdorff, take any closed A⊆X. Closed subsets of compact spaces are compact.',
    'The continuous image f(A) is compact.',
    'A compact subset of a Hausdorff space is closed: separate each outside point from each point of the compact set, then use finitely many separating neighborhoods.',
    'Thus f is a closed bijection. For g=f⁻¹, g⁻¹(A)=f(A) is closed for every closed A⊆X, so g is continuous. No metric is required.'
  ]);
  function circleModel(raw) {
    const s = normalize(raw), epsilon = 10 ** s.logEpsilon, angle = TAU * s.angleFraction;
    const circle = Array.from({ length: 129 }, (_, j) => [Math.cos(TAU * j / 128), Math.sin(TAU * j / 128)]); circle[128] = [1, 0];
    const upper = [Math.cos(epsilon), Math.sin(epsilon)], lower = [Math.cos(epsilon), -Math.sin(epsilon)], jumpSequence = Array.from({ length: 10 }, (_, j) => { const e = 10 ** (-.5 * (j + 1)); return { epsilon: e, point: [Math.cos(e), -Math.sin(e)], preimage: TAU - e, imageDistance: 2 * Math.sin(e / 2), inverseDistance: TAU - e }; });
    const preimageWitnessArc = { radius: PI / 2, neighborhood: '[0,π/2) in [0,2π)', imageArc: '[0,π/2) angular arc; not open in S¹ at (1,0)' };
    return { domain: s.circleDomain, epsilon, angle, selected: [Math.cos(angle), Math.sin(angle)], circle, upper, lower,
      preimages: { upper: epsilon, lower: TAU - epsilon, seam: s.circleDomain === 'closed' ? [0, TAU] : [0] },
      jumpSequence, imageDistance: 2 * Math.sin(epsilon / 2), inverseDistance: TAU - epsilon,
      continuous: true, onto: true, bijective: s.circleDomain !== 'closed', domainCompact: s.circleDomain !== 'halfopen', targetHausdorff: true,
      homeomorphism: s.circleDomain === 'quotient', inverseContinuous: s.circleDomain === 'closed' ? null : s.circleDomain === 'quotient', preimageWitnessArc,
      steps: compactHausdorffProof.slice(0, s.theoremStep),
      theorem: 'The map t↦(cos t,sin t) from [0,2π) is a continuous bijection. The sequence qₙ=(cos εₙ,−sin εₙ)→(1,0) has inverse 2π−εₙ, which does not tend to the inverse 0; its inverse is discontinuous. The domain is not compact. With [0,2π] instead, the domain is compact and connected, and its image is compact, connected and Hausdorff, but 0 and 2π share an image: there is no inverse. The interval and circle are not homeomorphic: removing an interior interval point disconnects it, whereas removing any circle point leaves a connected arc. Identifying the endpoints produces a compact quotient Q; the induced continuous bijection Q→S¹ is a homeomorphism by the compact–Hausdorff theorem. The angle coordinate still jumps at the seam: it is not a continuous real coordinate on Q.' };
  }
  function build(raw) {
    const state = normalize(raw), station = state.station, makers = { T1: finiteModel, T2: continuityModel, T3: coverModel, T4: cofiniteModel, T5: sineModel, T6: surfaceModel, T7: circleModel }, active = makers[station](state);
    let rows, readout;
    if (station === 'T1') { const d = active; rows = [['Open family', d.opens.map(setName).join(' · ') || 'empty family', 'Subset bit k contributes 2ᵏ to the family code.'], ['∅ and whole X', d.missing.length ? 'missing ' + d.missing.map(setName).join(', ') : 'both present', 'Empty union is ∅; empty intersection is X.'], ['Arbitrary unions', d.unions.length ? d.unions[0].members.map(setName).join(' ∪ ') + ' = ' + setName(d.unions[0].result) + ' is missing' : 'all ' + d.subfamilyCount + ' subfamilies pass', 'Finite universe: exhaustive distinct subfamilies suffice.'], ['Finite intersections', d.intersections.length ? d.intersections[0].members.map(setName).join(' ∩ ') + ' = ' + setName(d.intersections[0].result) + ' is missing' : 'all ' + d.pairCount + ' pairs pass', 'Pairwise closure implies finite closure; X handles zero members.'], ['Is a topology?', yes(d.valid), 'Complements are not required.']]; readout = 'T1. Family ' + state.familyMask + ': ' + (d.valid ? 'a topology.' : 'not a topology.') + ' ' + rows[2][1] + '.'; }
    else if (station === 'T2') { const d = active; rows = [['Domain open sets', d.domain.map(setName).join(' · '), 'Chosen topology on X.'], ['Target open sets', d.target.map(setName).join(' · '), 'Chosen topology on Y.'], ['Map', d.mapping.map((y, x) => ['a', 'b', 'c'][x] + '↦' + ['a', 'b', 'c'][y]).join(', '), 'Coordinates and distances play no part.'], ...d.preimages.map(p => ['Preimage of ' + setName(p.open), setName(p.preimage), p.openInDomain ? 'Open in X' : 'Not open in X: discontinuity witness']), ['Continuous / bijective', yes(d.continuous) + ' / ' + yes(d.bijective), 'All target opens checked; all three images compared.'], ['Inverse continuous', d.inverseContinuous === null ? 'No inverse' : yes(d.inverseContinuous), 'Images of domain opens are inverse preimages.'], ['Homeomorphism', yes(d.homeomorphism), 'Continuity + bijection + continuous inverse.'], ['Compact X / Hausdorff Y', 'yes / ' + yes(d.targetHausdorff), 'Every finite space is compact; the theorem also needs Hausdorff Y.']]; readout = 'T2. Continuous ' + yes(d.continuous) + ', bijective ' + yes(d.bijective) + ', homeomorphism ' + yes(d.homeomorphism) + '.'; }
    else if (station === 'T3') { const d = active; rows = [['Selected finite union', '(1/' + d.N + ',1)', 'Both endpoints excluded.'], ['Uncovered witness', 'x=1/(2N)=' + fmt(d.witness), '0<x<1/N for every positive N.'], ['Infinite cover', 'n=2,3,4,… covers every x∈(0,1)', 'Choose n>1/x; the integer family has no largest index.'], ['Any finite selection', 'Has a largest index N', 'Therefore leaves x=1/(2N) uncovered.'], ['[0,1] compact', 'Heine–Borel: closed and bounded', 'The failing open-interval cover does not cover these endpoints.'], ['Separate finite cover of [0,1]', String(d.closedCover.length) + ' open intervals', 'Maximum center distance ' + fmt(d.maximumCenterDistance) + ' < radius ' + fmt(d.radius) + '. This single example is not a proof of compactness.']]; readout = 'T3. (0,1) is not compact; any finite selection with maximum N=' + d.N + ' leaves x=' + fmt(d.witness) + ' uncovered. [0,1] is compact by Heine–Borel.'; }
    else if (station === 'T4') { const d = active; rows = [['Universe', 'Infinite ℝ', 'The displayed integers are only illustrative points.'], ['U excludes', d.excludedA.join(', '), 'U=ℝ minus this finite set.'], ['V excludes', d.excludedB.join(', '), 'V=ℝ minus this finite set.'], ['U∩V excludes', d.excludedUnion.join(', '), 'A finite union of finite exclusions.'], ['Intersection witness', String(d.witness), 'This real number belongs to both opens.'], ['T1 / Hausdorff', 'yes / no', 'Singletons closed; nonempty opens never disjoint.'], ['Metric / compact', 'No compatible metric / compact', 'Metric spaces are Hausdorff; a finite-complement cover argument proves compactness.']]; readout = 'T4. The infinite cofinite real line is T1 and compact, but not Hausdorff. ' + d.witness + ' belongs to both displayed nonempty opens.'; }
    else if (station === 'T5') { const d = active; rows = [['Graph window', 'x∈[' + fmt(d.xMin) + ',1]', 'Resolved by uniform steps in u=1/x, not x. The graph beyond the window is omitted.'], ['Closure sequence', 'xₙ=1/(arcsin(y)+2πn)', 'For all n≥1, yₙ=y and xₙ→0.'], ['Selected n / point', state.sequenceN + ' / (' + fmt(d.selected.x) + ',' + fmt(d.selected.y) + ')', 'A point on the actual graph, not a bridge to the target.'], ['Connected', 'yes', 'Closure of a connected graph.'], ['Path-connected', 'no; two path components', 'IVT forces alternating extrema near any proposed departure from x=0.'], ['Compact', 'yes', 'Exactly the closed bounded closure in ℝ².']]; readout = 'T5. The complete topologist’s sine closure is connected and compact but not path-connected. Its graph and vertical segment are separate path components; the drawing truncates at positive x.'; }
    else if (station === 'T6') { const d = active; rows = [['Genus', String(d.genus), 'A different genus selects a different object.'], ['Actual triangular V / E / F', d.counts.V + ' / ' + d.counts.E + ' / ' + d.counts.F, 'Unique indices and actual edge incidences, not decorative holes.'], ['Euler characteristic', String(d.counts.chi) + ' = 2−2g', 'Computed V−E+F agrees with double-of-domain construction.'], ['Different CW cell decomposition', d.quotient.V + '−' + d.quotient.E + '+' + d.quotient.F + '=' + d.quotient.chi, d.quotient.word], ['Closed / coherently oriented', yes(d.closed) + ' / ' + yes(d.oriented), 'Each edge has two incident triangles with opposite orientations.'], ['Deformation parameters', 's=' + fmt(state.stretch) + ', b=' + fmt(state.bend), 'F(x,y,z)=(sx+by,y,z); exact affine image of every triangle.'], ['Homeomorphic deformation', 'det DF=' + fmt(d.jacobianDeterminant) + '>0', d.inverseFormula], ['Horizontal figure-eight chord', fmt(d.metric.originalChord) + ' → ' + fmt(d.metric.transformedChord), 'Metric length may change; the valence-four crossing remains one point.']]; readout = 'T6. Closed orientable genus ' + d.genus + ' has χ=' + d.counts.chi + '. Positive stretch and invertible affine shear preserve every mesh incidence and the figure-eight crossing.'; }
    else { const d = active; rows = [['Domain', d.domain === 'halfopen' ? '[0,2π)' : d.domain === 'closed' ? '[0,2π]' : 'Q=[0,2π]/(0∼2π)', 'The angle parameter is not globally continuous on the quotient.'], ['Continuous / onto / bijective', 'yes / yes / ' + yes(d.bijective), 'The closed interval identifies distinct endpoints.'], ['Compact domain / Hausdorff target', yes(d.domainCompact) + ' / ' + yes(d.targetHausdorff), 'Both hypotheses plus bijection are required.'], ['Inverse / homeomorphism', d.inverseContinuous === null ? 'No inverse / no' : yes(d.inverseContinuous) + ' / ' + yes(d.homeomorphism), 'Half-open bijection has an inverse jump.'], ['Selected angle and image', 't/(2π)=' + fmt(state.angleFraction) + '; (' + fmt(d.selected[0]) + ',' + fmt(d.selected[1]) + ')', 'The green selected image is separate from the near-seam approaches.'], ['Approach ε', fmt(d.epsilon), 'Angular approach; the plotted points retain their true coordinates.'], ['Near-seam image distance', fmt(d.imageDistance), 'Chord distance to (1,0): 2 sin(ε/2)→0.'], ['Half-open inverse distance', fmt(d.inverseDistance), '2π−ε→2π rather than 0: discontinuous inverse.'], ['Non-homeomorphic interval / circle', 'Remove one interior point', 'Interval disconnects; punctured circle stays connected.']]; readout = 'T7. ' + rows[0][1] + ' to S¹: continuous surjection, bijective ' + yes(d.bijective) + ', homeomorphism ' + yes(d.homeomorphism) + '. The compact–Hausdorff theorem requires every stated hypothesis.'; }
    return { state, station, active, rows, readout, proof: active.theorem };
  }
  function element(tag, attrs = {}, ...children) { const e = document.createElement(tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v))); children.forEach(c => { if (c != null) e.append(c.nodeType ? c : document.createTextNode(String(c))); }); return e; }
  function shape(tag, attrs = {}, content) { const e = document.createElementNS(NS, tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v))); if (content != null) e.textContent = String(content); return e; }
  function text(svg, x, y, content, attrs = {}) { svg.append(shape('text', { x, y, fill: INK, 'font-size': 11, ...attrs }, content)); }
  function line(svg, points, color = TEAL, attrs = {}) { if (points.length > 1) svg.append(shape('polyline', { points: points.map(p => p.join(',')).join(' '), fill: 'none', stroke: color, 'stroke-width': 1.6, ...attrs })); }
  function dot(svg, p, color = TEAL, attrs = {}) { svg.append(shape('circle', { cx: p[0], cy: p[1], r: 4, fill: color, ...attrs })); }
  function render(item, hooks) {
    if (item?.props?.scenario !== SCENARIO || Object.keys(item.props).length !== 1 || item.renderer && item.renderer !== 'math-topology-lab') return null;
    const uid = 'topology-' + ++serial, title = item.title || 'Open sets, covers, connectedness and surfaces', instructions = item.instructions || 'Explore seven stations. Check exact finite witnesses and the stated hypotheses of infinite-space proofs; distance is not needed to define continuity.';
    const root = element('section', { class: 'card lesson-model math-topology-lab', 'data-renderer': 'math-topology-lab', 'aria-labelledby': uid + '-title' });
    const heading = element('div', { class: 'model-heading-row' }, element('h3', { id: uid + '-title' }, title));
    const area = element('div', { class: 'model-controls concept-controls topology-controls' }), widgets = new Map(), panels = element('div', { class: 'topology-panels' }), pictures = [];
    ['Exact finite or geometric witness', 'Independent property and proof comparison'].forEach(name => { const viewport = element('div', { class: 'topology-viewport', tabindex: '0', role: 'region', 'aria-label': name + '; enlarge for detail' }), svg = shape('svg', { viewBox: '0 0 480 340', role: 'img', focusable: 'false' }); viewport.append(svg); panels.append(viewport); pictures.push(svg); });
    const table = element('table', { class: 'topology-ledger' }), tableView = element('div', { class: 'topology-table-region', tabindex: '0', role: 'region', 'aria-label': 'Current exact calculations and theorem hypotheses; scroll horizontally' }, table);
    const readout = element('p', { class: 'model-readout' }), proof = element('p', { class: 'topology-proof' }), steps = element('ol', { class: 'topology-proof-steps' });
    const caveat = element('p', { class: 'spatial-note' }, 'Finite pictures do not prove infinite cover, separation or limit claims. The ledgers state the necessary arguments. The sine graph has no connecting line to its vertical closure segment. Changing genus chooses another surface; positive stretch and invertible shear deform only the chosen surface. Enlarge preserves all state; reset restores every control.');
    const live = element('p', { class: 'model-status', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    let model = build(initial), enlarged = false;
    const stateKey = 'math.5.topology', stateBus = typeof window !== 'undefined' ? window.PrimerLessonStateBus : null;
    function refresh(announce, publish = false) {
      const s = model.state; root.setAttribute('data-topology-state', JSON.stringify(s));
      widgets.forEach(({ input, label }, key) => { const c = controls.find(c => c.key === key); label.hidden = Boolean(c.stations && !c.stations.includes(s.station)); input.disabled = label.hidden; input.value = String(s[key]); });
      table.replaceChildren(element('caption', {}, 'Current calculation and theorem hypotheses'), element('thead', {}, element('tr', {}, ...['Quantity', 'Value', 'Meaning / hypothesis'].map(v => element('th', { scope: 'col' }, v)))), element('tbody', {}, ...model.rows.map(row => element('tr', {}, element('th', { scope: 'row' }, row[0]), element('td', {}, row[1]), element('td', {}, row[2])))));
      readout.textContent = model.readout; proof.textContent = model.proof; steps.hidden = s.station !== 'T7'; steps.replaceChildren(...(s.station === 'T7' ? model.active.steps.map((p, j) => element('li', { 'data-topology-proof-step': j + 1 }, p)) : []));
      draw(); if (announce) live.textContent = model.readout;
      if (publish) stateBus?.publish(stateKey, root, model.state);
    }
    for (const c of controls) {
      const input = element(c.options ? 'select' : 'input', { id: uid + '-' + c.key, 'data-topology-control': c.key });
      if (c.options) c.options.forEach(o => input.append(element('option', { value: o.value }, o.label)));
      else Object.entries({ type: 'number', min: c.min, max: c.max, step: c.step, inputmode: 'decimal' }).forEach(([k, v]) => input.setAttribute(k, v));
      const commit = () => { model = build({ ...model.state, [c.key]: input.value }); refresh(true, true); };
      input.addEventListener('change', commit); input.addEventListener('blur', () => { if (String(model.state[c.key]) !== input.value) commit(); });
      input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault?.(); commit(); } else if (e.key === 'Escape') { e.preventDefault?.(); input.value = String(model.state[c.key]); } });
      const label = element('label', { for: uid + '-' + c.key, class: 'model-range-control' }, element('span', {}, c.label), input); widgets.set(c.key, { input, label }); area.append(label);
    }
    const buttons = element('div', { class: 'model-button-row topology-fixtures' });
    const fixtures = [
      ['missingunion', 'Assessed missing union', { station: 'T1', familyMask: 135 }], ['validchain', 'Topology without complement closure', { station: 'T1', familyMask: 139 }],
      ['identityfail', 'Bijective continuous; inverse fails', { station: 'T2', domainTopology: 'discrete', targetTopology: 'indiscrete', mapCode: 21 }],
      ['homeomorphism', 'Finite homeomorphism', { station: 'T2', domainTopology: 'discrete', targetTopology: 'discrete', mapCode: 7 }],
      ['cover', 'No finite subcover', { station: 'T3', coverN: 8 }], ['cofinite', 'T1 does not imply Hausdorff', { station: 'T4', cofiniteA: 3, cofiniteB: 4 }],
      ['sine', 'Sine closure: no path across', { station: 'T5', sineCycles: 8, sineTarget: .5, sequenceN: 4 }],
      ['genusthree', 'Assessed genus three: χ=−4', { station: 'T6', genus: 3, stretch: 1, bend: 0 }],
      ['halfopen', 'Half-open bijection: inverse jump', { station: 'T7', circleDomain: 'halfopen', logEpsilon: -2, theoremStep: 4 }],
      ['surjection', 'Compact connected surjection', { station: 'T7', circleDomain: 'closed' }], ['quotient', 'Endpoint quotient homeomorphism', { station: 'T7', circleDomain: 'quotient', theoremStep: 4 }],
    ];
    for (const [key, name, patch] of fixtures) { const button = element('button', { type: 'button', class: 'btn ghost small', 'data-topology-action': key }, name); button.addEventListener('click', () => { model = build({ ...model.state, ...patch }); refresh(true, true); }); buttons.append(button); }
    const reset = element('button', { type: 'button', class: 'btn ghost small', 'data-topology-action': 'reset' }, 'Reset activity'); reset.addEventListener('click', () => { model = build(initial); size(false); refresh(true, true); }); buttons.append(reset);
    const enlarge = element('button', { type: 'button', class: 'btn ghost small', 'aria-pressed': 'false', 'data-topology-action': 'enlarge' }, 'Enlarge plots');
    function size(on) { enlarged = on; root.classList.toggle('is-enlarged', on); enlarge.setAttribute('aria-pressed', String(on)); enlarge.textContent = on ? 'Fit plots' : 'Enlarge plots'; }
    enlarge.addEventListener('click', () => size(!enlarged)); heading.append(enlarge);
    const sources = element('p', { class: 'spatial-note' }, 'Sources: ', element('a', { href: 'https://www.math.ucla.edu/~sharifi/notes/topology-ch02.html', target: '_blank', rel: 'noopener' }, 'UCLA: continuous maps'), '; ', element('a', { href: 'https://www.math.ucla.edu/~sharifi/notes/topology-ch03.html', target: '_blank', rel: 'noopener' }, 'UCLA: compact and connected spaces'), '; ', element('a', { href: 'https://pi.math.cornell.edu/~mec/Winter2009/Victor/part5.htm', target: '_blank', rel: 'noopener' }, 'Cornell: Euler characteristic'), '.');
    root.append(heading, element('p', { class: 'model-instructions' }, instructions), area, buttons, panels, tableView, readout, proof, steps, caveat, sources, live);
    if (hooks?.speakButton) heading.prepend(hooks.speakButton(() => title + '. ' + instructions + '. ' + model.readout + ' ' + model.rows.map(row => row.join(': ')).join('. ') + '. ' + model.proof + ' ' + (model.station === 'T7' ? model.active.steps.join(' ') : '') + ' ' + caveat.textContent, 'Read this activity aloud'));
    function setup(index, name) { const svg = pictures[index]; svg.replaceChildren(shape('title', { id: uid + '-plot-title-' + index }, name), shape('desc', { id: uid + '-plot-desc-' + index }, model.readout), shape('rect', { x: 0, y: 0, width: 480, height: 340, rx: 10, fill: '#f5efdf' })); svg.setAttribute('aria-labelledby', uid + '-plot-title-' + index); svg.setAttribute('aria-describedby', uid + '-plot-desc-' + index); text(svg, 18, 27, name, { 'font-size': 16, 'font-weight': 600 }); return svg; }
    function bullet(svg, y, value, color = INK) { text(svg, 24, y, value, { fill: color }); }
    function draw() {
      const d = model.active, s = model.state;
      if (s.station === 'T1') {
        const left = setup(0, 'All subsets of {a,b,c}: family membership'), loc = [[240, 267], [100, 205], [240, 205], [380, 205], [100, 130], [240, 130], [380, 130], [240, 65]];
        // Positions indexed by subset, not by row order.
        const position = [loc[0], loc[1], loc[2], loc[4], loc[3], loc[5], loc[6], loc[7]];
        for (let a = 0; a < 8; a++) for (let j = 0; j < 3; j++) if (!(a & 1 << j)) line(left, [position[a], position[a | 1 << j]], GRID, { 'stroke-width': 1 });
        d.subsets.forEach(p => { dot(left, position[p.mask], p.included ? TEAL : '#f5efdf', { r: 9, stroke: p.included ? TEAL : CORAL, 'data-topology-subset': p.mask }); text(left, position[p.mask][0], position[p.mask][1] + 23, p.name + ' · bit ' + p.mask, { 'text-anchor': 'middle' }); });
        bullet(left, 323, 'Filled = proposed open; hollow = omitted subset');
        const right = setup(1, 'Axiom witnesses, not complement tests');
        bullet(right, 62, 'Code = sum of 2ᵏ for each included subset k');
        bullet(right, 95, '∅ and X: ' + (d.missing.length ? 'missing ' + d.missing.map(setName).join(', ') : 'present'));
        bullet(right, 130, d.unions.length ? 'Union failure:' : 'Every distinct subfamily union is included.', d.unions.length ? CORAL : TEAL);
        if (d.unions.length) bullet(right, 155, d.unions[0].members.map(setName).join(' ∪ ') + ' = ' + setName(d.unions[0].result) + ' missing', CORAL);
        bullet(right, 194, d.intersections.length ? 'Intersection failure:' : 'Every pairwise intersection is included.', d.intersections.length ? CORAL : TEAL);
        if (d.intersections.length) bullet(right, 219, d.intersections[0].members.map(setName).join(' ∩ ') + ' = ' + setName(d.intersections[0].result) + ' missing', CORAL);
        bullet(right, 256, 'Topology: ' + yes(d.valid)); bullet(right, 286, 'Complement closure is not required.');
      } else if (s.station === 'T2') {
        const left = setup(0, 'Map between finite topological spaces');
        d.mapping.forEach((y, x) => line(left, [[95, 100 + x * 75], [385, 100 + y * 75]], [TEAL, CORAL, BLUE][x], { 'data-topology-map': x }));
        for (let j = 0; j < 3; j++) { dot(left, [95, 100 + j * 75], INK); dot(left, [385, 100 + j * 75], INK); text(left, 75, 104 + j * 75, ['a', 'b', 'c'][j]); text(left, 398, 104 + j * 75, ['a', 'b', 'c'][j]); }
        bullet(left, 65, 'X: ' + s.domainTopology + '       Y: ' + s.targetTopology); bullet(left, 310, 'A bijection alone does not test the inverse.');
        const right = setup(1, 'Preimages of every target open set');
        text(right, 24, 62, 'Open V in Y'); text(right, 182, 62, 'f⁻¹(V) in X'); text(right, 345, 62, 'Open in X?');
        d.preimages.forEach((p, j) => { const y = 90 + j * 23; text(right, 24, y, setName(p.open)); text(right, 182, y, setName(p.preimage)); text(right, 345, y, yes(p.openInDomain), { fill: p.openInDomain ? TEAL : CORAL, 'data-topology-preimage': p.open }); });
        bullet(right, 298, 'Continuous ' + yes(d.continuous) + '; homeomorphism ' + yes(d.homeomorphism));
        bullet(right, 321, 'Inverse: ' + (d.inverseContinuous === null ? 'does not exist' : d.inverseContinuous ? 'continuous' : 'discontinuous'));
      } else if (s.station === 'T3') {
        const left = setup(0, 'Finite subfamily of the infinite cover'), X = x => 75 + 345 * x;
        line(left, [[X(0), 277], [X(1), 277]], INK); text(left, X(0), 298, '0', { 'text-anchor': 'middle' }); text(left, X(1), 298, '1', { 'text-anchor': 'middle' });
        const shown = [...new Set([2, 3, 4, d.N].filter(n => n <= d.N))];
        shown.forEach((n, j) => { const y = 93 + j * 38; text(left, 20, y + 4, 'n=' + n); line(left, [[X(1 / n), y], [X(1), y]], TEAL, { 'data-topology-cover-index': n }); for (const v of [1 / n, 1]) dot(left, [X(v), y], '#f5efdf', { stroke: TEAL }); });
        line(left, [[X(0), 261], [X(1 / d.N), 261]], CORAL, { 'stroke-width': 4 }); dot(left, [X(d.witness), 277], CORAL, { 'data-topology-cover-witness': d.witness });
        bullet(left, 55, 'Representative n from {2,…,' + d.N + '}; endpoints open.'); bullet(left, 323, 'Red x=1/(2N) is outside every selected set.');
        const right = setup(1, 'Separate finite open cover of [0,1]'), scale = x => 55 + 370 * (x + d.radius) / (1 + 2 * d.radius);
        d.closedCover.forEach((p, j) => { const y = 82 + 11 * j; line(right, [[scale(p.start), y], [scale(p.end), y]], BLUE, { 'data-topology-closed-cover': j }); dot(right, [scale(p.center), y], BLUE, { r: 2 }); for (const v of [p.start, p.end]) dot(right, [scale(v), y], '#f5efdf', { r: 2, stroke: BLUE }); });
        line(right, [[scale(0), 279], [scale(1), 279]], INK, { 'stroke-width': 3 }); dot(right, [scale(0), 279], INK); dot(right, [scale(1), 279], INK);
        bullet(right, 55, 'm=' + s.coverMesh + ', radius=3/(4m); centers j/m.'); bullet(right, 304, 'Heine–Borel proves compactness for ALL covers.'); bullet(right, 323, 'One successful drawn cover is only an example.');
      } else if (s.station === 'T4') {
        const left = setup(0, 'Examples in the INFINITE cofinite real line'), max = d.witness + 1, X = n => 55 + 370 * n / max;
        [['U', d.excludedA, 112, TEAL], ['V', d.excludedB, 179, BLUE], ['U∩V', d.excludedUnion, 246, CORAL]].forEach(([name, excluded, y, color]) => { line(left, [[35, y], [450, y]], color); text(left, 20, y - 18, name + ': finite exclusions hollow'); for (let n = 0; n <= max; n++) dot(left, [X(n), y], excluded.includes(n) ? '#f5efdf' : color, { r: 3, stroke: color, 'data-topology-cofinite': name + ':' + n }); });
        for (let n = 0; n <= max; n++) text(left, X(n), 267, n, { 'text-anchor': 'middle' });
        bullet(left, 58, 'The line continues in both directions.'); bullet(left, 291, 'Witness ' + d.witness + ' is beyond all combined exclusions.'); bullet(left, 320, 'Finite illustrations do not replace the universe ℝ.');
        const right = setup(1, 'Separation depends on opens, not distance');
        ['ℝ minus {p} is open → {p} closed → T1.', 'U∩V = ℝ minus (finite A∪B).', 'An infinite set cannot be exhausted by A∪B.', 'Every pair of nonempty opens intersects.', 'Distinct points cannot have disjoint neighborhoods.', 'Therefore: not Hausdorff; no compatible metric.', 'Choose one cover set; cover its finite complement.', 'Thus the infinite cofinite space is compact.'].forEach((p, j) => bullet(right, 66 + j * 31, p, j === 5 ? CORAL : INK));
      } else if (s.station === 'T5') {
        const left = setup(0, 'Sine closure: disconnected DRAWN pieces'), X = x => 80 + 330 * x, Y = y => 188 - 95 * y;
        line(left, [[X(0), Y(0)], [X(1), Y(0)]], GRID); line(left, d.vertical.map(([x, y]) => [X(x), Y(y)]), CORAL, { 'stroke-width': 3, 'data-topology-sine': 'vertical' });
        line(left, d.graph.map(([x, y]) => [X(x), Y(y)]), TEAL, { 'data-topology-sine': 'graph' }); dot(left, [X(d.selected.x), Y(d.selected.y)], BLUE, { 'data-topology-sine': 'sequence-probe' }); dot(left, [X(0), Y(s.sineTarget)], CORAL, { r: 5, 'data-topology-sine': 'closure-target' });
        text(left, 80, 310, '0'); text(left, 410, 310, '1'); text(left, 51, Y(1) + 4, '+1'); text(left, 51, Y(-1) + 4, '−1');
        bullet(left, 55, 'Graph: x≥' + fmt(d.xMin) + '. No line joins x=0.'); bullet(left, 328, 'Horizontal x · vertical y=sin(1/x), plus closure segment.');
        const right = setup(1, 'Exact closure sequence at selected y'), Xn = n => 85 + 325 * (n - 1) / 19, Yn = x => 286 - 200 * x / .25;
        line(right, [[85, 85], [85, 286], [410, 286]], GRID); line(right, d.sequence.map(p => [Xn(p.n), Yn(p.x)]), BLUE, { 'data-topology-sine-sequence': 'xn' });
        d.sequence.forEach(p => dot(right, [Xn(p.n), Yn(p.x)], p.n === s.sequenceN ? CORAL : BLUE, { r: p.n === s.sequenceN ? 4 : 2 }));
        bullet(right, 55, 'xₙ=1/(arcsin(' + fmt(s.sineTarget) + ')+2πn), yₙ=' + fmt(s.sineTarget));
        text(right, 85, 307, 'n=1'); text(right, 410, 307, '20', { 'text-anchor': 'end' }); text(right, 75, 90, 'x=.25', { 'text-anchor': 'end' }); text(right, 75, 288, '0', { 'text-anchor': 'end' });
        bullet(right, 328, 'Limit xₙ→0 is proved by the formula, not this sample.');
      } else if (s.station === 'T6') {
        const left = setup(0, 'Actual triangle mesh: an oblique projection');
        const projected = d.vertices.map(p => [p[0] + .45 * p[1], .4 * p[1] + p[2]]), xs = projected.map(p => p[0]), ys = projected.map(p => p[1]), xmin = Math.min(...xs), xmax = Math.max(...xs), ymin = Math.min(...ys), ymax = Math.max(...ys), gain = Math.min(390 / (xmax - xmin), 205 / (ymax - ymin)), project = p => [240 + gain * (p[0] - (xmin + xmax) / 2), 183 - gain * (p[1] - (ymin + ymax) / 2)];
        d.faces.map((f, j) => ({ f, j, depth: f.reduce((a, v) => a + d.vertices[v][1] - d.vertices[v][2], 0) })).sort((a, b) => b.depth - a.depth).forEach(({ f, j }) => left.append(shape('polygon', { points: f.map(i => project(projected[i]).join(',')).join(' '), fill: d.mesh.vertices[f[2]][2] > 0 ? '#83b3a0' : '#c7d7c5', stroke: '#547569', 'stroke-width': .35, 'data-topology-face': j })));
        bullet(left, 55, 'g=' + d.genus + ', χ=' + d.counts.chi + ', triangulated closed surface'); bullet(left, 315, 'The paired boundary circles are shared seam vertices.'); bullet(left, 332, 'This projection can occlude holes; rotate the linked 3D view.');
        const right = setup(1, 'Figure-eight incidence survives F');
        const X = x => 240 + 90 * x / 2.75, Y = y => 187 - 85 * y;
        line(right, d.baseFigureEight.map(p => [X(p[0]), Y(p[1])]), GRID, { 'stroke-width': 3, 'data-topology-figure': 'original' });
        line(right, d.figureEight.map(p => [X(p[0]), Y(p[1])]), TEAL, { 'data-topology-figure': 'deformed' }); dot(right, [X(0), Y(0)], CORAL, { r: 5, 'data-topology-crossing': 'shared' });
        bullet(right, 55, 'Gray original · teal image · coral shared crossing'); bullet(right, 306, 'F=(sx+by,y,z), s=' + fmt(s.stretch) + ', b=' + fmt(s.bend)); bullet(right, 329, 'One valence-four crossing; lengths and angles can change.');
      } else {
        const left = setup(0, 'Circle seam and the actual image points'), C = p => [240 + 100 * p[0], 185 - 100 * p[1]];
        line(left, d.circle.map(C), TEAL, { 'data-topology-circle': 'unit' }); dot(left, C([1, 0]), INK, { 'data-topology-circle': 'seam' }); dot(left, C(d.upper), BLUE, { r: 5, 'data-topology-circle': 'upper' }); dot(left, C(d.lower), CORAL, { r: 5, 'data-topology-circle': 'lower' }); dot(left, C(d.selected), TEAL, { r: 5, 'data-topology-circle': 'selected' });
        bullet(left, 55, 'Blue: ε; coral: 2π−ε, ε=' + fmt(d.epsilon)); bullet(left, 312, 'Both images approach (1,0) from opposite sides.'); bullet(left, 331, 'These points are not magnified away from the seam.');
        const right = setup(1, 'Half-open inverse: chord tends to 0, t does not');
        const X = log => 82 + 328 * (log + 5) / 4.5, Y = t => 279 - 200 * t / TAU;
        line(right, [[82, 78], [82, 279], [410, 279]], GRID);
        line(right, d.jumpSequence.map(p => [X(Math.log10(p.epsilon)), Y(p.preimage)]), CORAL, { 'data-topology-inverse': 'angle' });
        dot(right, [X(s.logEpsilon), Y(d.preimages.lower)], CORAL, { 'data-topology-inverse': 'probe' });
        text(right, 73, 84, '2π', { 'text-anchor': 'end' }); text(right, 73, 281, '0', { 'text-anchor': 'end' }); text(right, 82, 301, '−5'); text(right, 410, 301, '−0.5', { 'text-anchor': 'end' });
        bullet(right, 55, 'Vertical t=2π−ε; horizontal log₁₀ ε.'); bullet(right, 325, 'At the seam, the half-open inverse is t=0.');
      }
    }
    root.setModelState = (values, announce = false, fromShared = false) => { model = build({ ...model.state, ...values }); refresh(announce, !fromShared); return model.state; };
    stateBus?.join(stateKey, root, values => root.setModelState(values, false, true)); refresh(false); return root;
  }
  const api = Object.freeze({ SCENARIO, initial, controls, normalize, setName, family, topologyCodes, finiteAxioms, finiteSeparation, finiteModel, decodeMap, preimage,
    continuityModel, coverModel, cofiniteModel, sineModel, deform, undeform, surfaceMesh, surfaceModel, compactHausdorffProof, circleModel, build, render });
  if (typeof window !== 'undefined') window.PrimerMathTopologyLab = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
}());
