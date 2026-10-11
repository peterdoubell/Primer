/* Named complex functions and explicit theorem hypotheses; no expression evaluator. */
(function () {
  'use strict';
  const PI = Math.PI, TAU = 2 * PI, NS = 'http://www.w3.org/2000/svg';
  const SCENARIO = 'math.5.complex-analysis.holomorphy-contours';
  const COLORS = { ink: '#263b46', paper: '#f5efdf', grid: '#d5cfbf', teal: '#317e78', coral: '#b96652', blue: '#3e7085', gold: '#9e741c' };
  let serial = 0;
  const initial = Object.freeze({ station: 'C1', directionalFn: 'z2', pointRe: 0, pointIm: 0, angle: 45, logStep: -1,
    contourFn: 'laurent', residueA: 1, residueB: 1, circleRe: 0, circleIm: 0, radius: 1, winding: '1',
    taylorFn: 'geometric', terms: 6, inferenceRadius: '2.5', growthFn: 'linear', growthRadius: 2, globalM: 2, proofStep: '6',
    meanFn: 'z2', arcFn: 'quadratic', k: 1, halfPlane: 'upper', arcRadius: 3, poleA: 1 });
  const controls = Object.freeze([
    { key: 'station', label: 'Station', options: [['C1', 'C1 · Directional derivatives and CR'], ['C2', 'C2 · Contours and residues'], ['C3', 'C3 · Taylor radius'], ['C4', 'C4 · Liouville and polynomial roots'], ['C5', 'C5 · Mean value and maximum modulus'], ['C6', 'C6 · Jordan arc']] },
    { key: 'directionalFn', label: 'Function f(z)', stations: ['C1'], options: [['z2', 'z²'], ['exp', 'exp(z)'], ['conjugate', 'conjugate z'], ['abs2', '|z|²'], ['pathology', 'exp(−1/z⁴), extended by 0 at z=0']] },
    { key: 'pointRe', label: 'Probe Re z', stations: ['C1', 'C3'], min: -2, max: 2, step: .25 },
    { key: 'pointIm', label: 'Probe Im z', stations: ['C1', 'C3'], min: -2, max: 2, step: .25 },
    { key: 'angle', label: 'Approach angle θ (degrees)', stations: ['C1'], min: 0, max: 180, step: 15 },
    { key: 'logStep', label: 'log₁₀ step length h', stations: ['C1'], min: -4, max: -.5, step: .5 },
    { key: 'contourFn', label: 'Contour integrand', stations: ['C2'], options: [['rational', 'a/z + b/(z−2), existing example'], ['laurent', '3/z² + 5/z + 7 + 2z + z²'], ['poles', '1/(z²+1)'], ['annulus-inverse', '1/z on the annulus'], ['annulus-z', 'z on the same annulus']] },
    { key: 'residueA', label: 'Real residue a at 0', stations: ['C2'], min: -2, max: 2, step: 1, presets: ['rational'] },
    { key: 'residueB', label: 'Real residue b at 2', stations: ['C2'], min: -2, max: 2, step: 1, presets: ['rational'] },
    { key: 'circleRe', label: 'Circle center Re c', stations: ['C2', 'C5'], min: -2, max: 2, step: .25 },
    { key: 'circleIm', label: 'Circle center Im c', stations: ['C2', 'C5'], min: -2, max: 2, step: .25 },
    { key: 'radius', label: 'Circle radius r', stations: ['C2', 'C5'], min: .25, max: 3, step: .25 },
    { key: 'winding', label: 'Signed circle winding', stations: ['C2'], options: [['1', '+1 counterclockwise'], ['2', '+2 counterclockwise'], ['-1', '−1 clockwise'], ['-2', '−2 clockwise']] },
    { key: 'taylorFn', label: 'Taylor function about 0', stations: ['C3'], options: [['geometric', '1/(1−z)'], ['poles', '1/(z²+1)'], ['exp', 'exp(z), entire']] },
    { key: 'terms', label: 'Highest Taylor degree N', stations: ['C3'], min: 1, max: 24, step: 1 },
    { key: 'inferenceRadius', label: 'Radius consistent with assessed evidence', stations: ['C3'], options: [['2', 'R = 2 (endpoint possible)'], ['2.5', 'R = 2.5'], ['3', 'R = 3 (endpoint possible)']] },
    { key: 'growthFn', label: 'Entire-function growth comparison', stations: ['C4'], options: [['constant', 'Constant 1'], ['linear', 'z'], ['exp', 'exp(z)']] },
    { key: 'growthRadius', label: 'Comparison disk / Cauchy radius R', stations: ['C4'], min: 1, max: 12, step: .5 },
    { key: 'globalM', label: 'Hypothetical GLOBAL bound M', stations: ['C4'], min: .5, max: 6, step: .5 },
    { key: 'proofStep', label: 'Reveal dependent proof steps', stations: ['C4'], options: [['1', '1 · Assume root-free'], ['2', '2 · Entire reciprocal'], ['3', '3 · Bound exterior'], ['4', '4 · Bound compact interior'], ['5', '5 · Apply Liouville'], ['6', '6 · Contradiction']] },
    { key: 'meanFn', label: 'Mean-value function', stations: ['C5'], options: [['z2', 'z², holomorphic'], ['exp', 'exp(z), holomorphic'], ['constant', 'Constant 1'], ['abs2', '|z|², nonholomorphic'], ['peak', '1−|z|², interior maximum contrast'], ['geometric', '1/(1−z), check disk avoids 1']] },
    { key: 'arcFn', label: 'Remaining factor g(z)', stations: ['C6'], options: [['one', '1 · counterexample'], ['linear', '1/(z+ia)'], ['quadratic', '1/(z²+a²)']] },
    { key: 'k', label: 'Real Fourier parameter k', stations: ['C6'], min: -2, max: 2, step: .25 },
    { key: 'halfPlane', label: 'Closure half-plane', stations: ['C6'], options: [['upper', 'Upper · counterclockwise'], ['lower', 'Lower · clockwise']] },
    { key: 'arcRadius', label: 'Semicircle radius R (R>a)', stations: ['C6'], min: 2, max: 8, step: .25 },
    { key: 'poleA', label: 'Pole distance a', stations: ['C6'], min: .5, max: 1.5, step: .25 },
  ].map(c => Object.freeze({ ...c, stations: c.stations ? Object.freeze(c.stations) : undefined,
    options: c.options ? Object.freeze(c.options.map(([value, label]) => Object.freeze({ value, label }))) : undefined })));
  const complex = (re = 0, im = 0) => ({ re, im });
  const add = (a, b) => complex(a.re + b.re, a.im + b.im);
  const sub = (a, b) => complex(a.re - b.re, a.im - b.im);
  const scale = (a, n) => complex(a.re * n, a.im * n);
  const mul = (a, b) => complex(a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re);
  const abs = a => Math.hypot(a.re, a.im);
  function div(a, b) { const n = b.re * b.re + b.im * b.im; return n === 0 ? null : complex((a.re * b.re + a.im * b.im) / n, (a.im * b.re - a.re * b.im) / n); }
  function pow(z, n) { let r = complex(1); for (let j = 0; j < n; j++) r = mul(r, z); return r; }
  function trig(theta) {
    const q = Math.round(theta / (PI / 2));
    if (Number.isSafeInteger(q) && theta === q * (PI / 2)) { const j = ((q % 4) + 4) % 4; return { c: [1, 0, -1, 0][j], s: [0, 1, 0, -1][j] }; }
    return { c: Math.cos(theta), s: Math.sin(theta) };
  }
  function polar(r, theta) { const t = trig(theta); return complex(r * t.c, r * t.s); }
  const fmt = n => n === null ? 'undefined' : !Number.isFinite(n) ? n === Infinity ? '∞' : '−∞' : Math.abs(n) < 1e-9 && n !== 0 ? n.toExponential(3) : String(Number(n.toPrecision(6)));
  function formatComplex(z) { if (!z) return 'undefined / outside finite range'; if (z.im === 0) return fmt(z.re); if (z.re === 0) return fmt(z.im) + 'i'; return fmt(z.re) + (z.im < 0 ? ' − ' : ' + ') + fmt(Math.abs(z.im)) + 'i'; }
  function formatSample(s) { return s.status === 'underflow-log-only' ? 'underflow: nonzero, ln magnitude retained' : s.status === 'overflow-log-only' ? 'overflow: ln magnitude retained' : formatComplex(s.value); }
  function normalize(raw) {
    const input = raw && typeof raw === 'object' ? raw : {}, result = {};
    for (const c of controls) {
      const v = input[c.key];
      if (c.options) result[c.key] = c.options.some(o => o.value === v) ? v : initial[c.key];
      else { const valid = (typeof v === 'number' || typeof v === 'string' && v.trim() !== '') && Number.isFinite(Number(v));
        const n = valid ? Number(v) : initial[c.key]; result[c.key] = Number((c.min + Math.round((Math.max(c.min, Math.min(c.max, n)) - c.min) / c.step) * c.step).toFixed(8)); }
    }
    return result;
  }
  function finitePoint(z) { if (!z || !Number.isFinite(z.re) || !Number.isFinite(z.im)) throw new RangeError('A finite complex point {re,im} is required.'); }
  function sample(value, logAbs, phase, status = 'regular') {
    const magnitude = value ? abs(value) : null;
    return { value, logAbs: logAbs === undefined ? magnitude === 0 ? -Infinity : Math.log(magnitude) : logAbs,
      phase: phase === undefined ? magnitude === 0 ? null : Math.atan2(value.im, value.re) : phase, status };
  }
  function exponential(w) { const logAbs = w.re, phase = Math.atan2(Math.sin(w.im), Math.cos(w.im));
    if (logAbs > 700) return sample(null, logAbs, phase, 'overflow-log-only');
    if (logAbs < -740) return sample(complex(0), logAbs, phase, 'underflow-log-only');
    return sample(polar(Math.exp(logAbs), w.im), logAbs, phase);
  }
  function evaluate(name, z, parameters = {}) {
    finitePoint(z); const z2 = mul(z, z), denominator = add(z2, complex(1));
    if (name === 'z2') return sample(z2);
    if (name === 'exp') return exponential(z);
    if (name === 'conjugate') return sample(complex(z.re, -z.im));
    if (name === 'abs2') return sample(complex(z.re * z.re + z.im * z.im));
    if (name === 'peak') return sample(complex(1 - z.re * z.re - z.im * z.im));
    if (name === 'constant' || name === 'one') return sample(complex(1));
    if (name === 'linear' || name === 'annulus-z') return sample(z);
    if (name === 'pathology') { if (z.re === 0 && z.im === 0) return sample(complex(0), -Infinity, null, 'discontinuous-extension'); return exponential(scale(div(complex(1), pow(z, 4)), -1)); }
    if (name === 'geometric') { const v = div(complex(1), sub(complex(1), z)); return v ? sample(v) : sample(null, Infinity, null, 'pole'); }
    if (name === 'poles') { const v = div(complex(1), denominator); return v ? sample(v) : sample(null, Infinity, null, 'pole'); }
    if (name === 'annulus-inverse') { const v = div(complex(1), z); return v ? sample(v) : sample(null, Infinity, null, 'pole'); }
    if (name === 'rational') {
      const a = parameters.residueA ?? 1, b = parameters.residueB ?? 1;
      if (![a, b].every(Number.isFinite) || Math.abs(a) > 2 || Math.abs(b) > 2) throw new RangeError('Real residues must lie in [−2,2].');
      const t1 = a === 0 ? complex(0) : div(complex(a), z), t2 = b === 0 ? complex(0) : div(complex(b), sub(z, complex(2)));
      return t1 && t2 ? sample(add(t1, t2)) : sample(null, Infinity, null, 'pole');
    }
    if (name === 'laurent') {
      if (abs(z) === 0) return sample(null, Infinity, null, 'pole');
      return sample(add(add(add(div(complex(3), z2), div(complex(5), z)), add(complex(7), scale(z, 2))), z2));
    }
    throw new RangeError('Unknown bounded named complex function.');
  }
  function circlePoints(center, radius, winding = 1, count = 128) {
    finitePoint(center); if (!Number.isFinite(radius) || radius <= 0 || !Number.isInteger(winding) || winding === 0 || Math.abs(winding) > 2 || !Number.isInteger(count) || count < 8 || count > 4096) throw new RangeError('Positive radius, signed winding ±1/±2 and bounded point count required.');
    return Array.from({ length: count + 1 }, (_, j) => add(center, polar(radius, TAU * winding * j / count)));
  }
  function integrate(fn, a, b, count = 512) {
    let result = complex(0), h = (b - a) / count;
    for (let j = 0; j <= count; j++) { const v = fn(a + h * j); if (!v || !Number.isFinite(v.re) || !Number.isFinite(v.im)) return null; result = add(result, scale(v, j === 0 || j === count ? 1 : j % 2 ? 4 : 2)); }
    return scale(result, h / 3);
  }
  function quadratureResolution(radius, winding, gap) {
    // Simpson's periodic weights alias at half the panel count. Resolve the
    // narrow angular scale near a genuine pole, rather than trust a fixed mesh.
    const requested = Number.isFinite(gap) ? Math.max(1024, 64 * radius * Math.abs(winding) / gap) : 1024;
    const panels = Math.min(65536, 2 ** Math.ceil(Math.log2(requested)));
    return { panels, resolved: panels >= requested };
  }
  function quotient(name, z, h, theta) {
    const delta = polar(h, theta), endpoint = add(z, delta), before = evaluate(name, z), after = evaluate(name, endpoint);
    if (name === 'pathology' && z.re === 0 && z.im === 0) {
      // log|f(h e^{iθ})/h| = −cos(4θ)/h⁴ − log h, never exp(large).
      const t = trig(4 * theta), logAbs = -t.c / h ** 4 - Math.log(h), argument = t.s / h ** 4 - theta, phase = Math.atan2(Math.sin(argument), Math.cos(argument));
      return { ...sample(logAbs > 700 ? null : logAbs < -740 ? complex(0) : polar(Math.exp(logAbs), phase), logAbs, phase, logAbs > 700 ? 'overflow-log-only' : logAbs < -740 ? 'underflow-log-only' : 'regular'), endpoint };
    }
    if (!before.value || !after.value) return { ...sample(null, null, null, 'nonfinite-quotient'), endpoint };
    return { ...sample(div(sub(after.value, before.value), delta)), endpoint };
  }
  function directionalModel(raw) {
    const s = normalize(raw), name = s.directionalFn, z = complex(s.pointRe, s.pointIm), h = 10 ** s.logStep, theta = s.angle * PI / 180, origin = abs(z) === 0;
    const probe = evaluate(name, z); let jacobian, derivative = null, pointwise = false, holomorphic = false, regularity;
    if (name === 'z2') { jacobian = { ux: 2 * z.re, uy: -2 * z.im, vx: 2 * z.im, vy: 2 * z.re }; derivative = scale(z, 2); pointwise = holomorphic = true; }
    if (name === 'exp') { const v = probe.value; jacobian = { ux: v.re, uy: -v.im, vx: v.im, vy: v.re }; derivative = v; pointwise = holomorphic = true; }
    if (name === 'conjugate') jacobian = { ux: 1, uy: 0, vx: 0, vy: -1 };
    if (name === 'abs2') { jacobian = { ux: 2 * z.re, uy: 2 * z.im, vx: 0, vy: 0 }; pointwise = origin; derivative = origin ? complex(0) : null; }
    if (name === 'pathology') {
      if (origin) jacobian = { ux: 0, uy: 0, vx: 0, vy: 0 };
      else { const d = probe.value ? mul(probe.value, scale(div(complex(1), pow(z, 5)), 4)) : null; jacobian = d ? { ux: d.re, uy: -d.im, vx: d.im, vy: d.re } : null; derivative = d; pointwise = holomorphic = true; }
    }
    const cr = jacobian ? jacobian.ux === jacobian.vy && jacobian.uy === -jacobian.vx : null;
    regularity = name === 'pathology' && origin ? 'Axis partials exist and are zero, but f is discontinuous at 0: along θ=45°, log|f|=1/h⁴. Real differentiability fails there.' : 'The displayed Jacobian is a real derivative with continuous first partials in a neighborhood of this regular point.';
    const neighborhood = name === 'abs2' || name === 'conjugate' ? 'Holomorphic on no open neighborhood.' : name === 'pathology' ? origin ? 'No holomorphic neighborhood at the discontinuous extension 0.' : 'Holomorphic locally on C\\{0}; the extension at 0 is not holomorphic.' : 'Entire: holomorphic on the open plane.';
    const directions = [0, PI / 4, PI / 2, theta].map(angle => ({ angle, quotient: quotient(name, z, h, angle) }));
    const selected = directions[3].quotient;
    return { functionName: name, z, probe: { z, ...probe }, h, theta, jacobian, cr, derivative, pointwise, holomorphic, regularity, neighborhood, directions, selected,
      steps: Array.from({ length: 15 }, (_, j) => { const step = 10 ** (-.5 - j / 4); return { h: step, quotient: quotient(name, z, step, theta) }; }),
      domain: { kind: name === 'pathology' ? 'punctured-plane-with-extension' : 'plane', holomorphic },
      theorem: 'CR plus real differentiability at the point is sufficient for a complex derivative there. Continuous first partials on an open set plus CR everywhere there are a sufficient condition for holomorphy. For holomorphic f on a disk, Cauchy’s formula f⁽ⁿ⁾(c)=n!/(2πi)∮f(z)/(z−c)ⁿ⁺¹ dz gives derivatives of every order and a convergent Taylor series. Samples of directions alone cannot prove holomorphy.' };
  }
  function contourPoles(name, s) {
    if (name === 'rational') return [[0, 0, s.residueA], [2, 0, s.residueB]].filter(p => p[2] !== 0).map(([re, im, residue]) => ({ z: complex(re, im), order: 1, residue: complex(residue) }));
    if (name === 'laurent') return [{ z: complex(0), order: 2, residue: complex(5) }];
    if (name === 'poles') return [{ z: complex(0, 1), order: 1, residue: complex(0, -.5) }, { z: complex(0, -1), order: 1, residue: complex(0, .5) }];
    if (name === 'annulus-inverse') return [{ z: complex(0), order: 1, residue: complex(1), outsideSelectedDomain: true }];
    return [];
  }
  function contourModel(raw) {
    const s = normalize(raw), name = s.contourFn, center = complex(s.circleRe, s.circleIm), winding = Number(s.winding), radius = s.radius;
    const poles = contourPoles(name, s).map(p => { const distance = abs(sub(p.z, center)), path = Math.abs(distance - radius) <= 1e-12 * Math.max(1, distance, radius); return { ...p, distance, path, winding: path ? null : distance < radius ? winding : 0 }; });
    const pathPole = poles.some(p => p.path), sum = poles.reduce((r, p) => p.winding === null ? r : add(r, scale(p.residue, p.winding)), complex(0));
    const integral = pathPole ? null : mul(complex(0, TAU), sum), annulus = name.startsWith('annulus'), minAbs = Math.abs(abs(center) - radius), maxAbs = abs(center) + radius;
    const contourInDomain = !annulus || minAbs > .25 && maxAbs < 4.5;
    const curve = circlePoints(center, radius, winding), outputCurve = curve.map(z => ({ z, ...evaluate(name, z, s) }));
    const gap = poles.length ? Math.min(...poles.map(p => Math.abs(p.distance - radius))) : Infinity, resolution = pathPole ? { panels: 0, resolved: false } : quadratureResolution(radius, winding, gap);
    const numerical = pathPole ? null : integrate(t => { const offset = polar(radius, winding * t), z = add(center, offset), value = evaluate(name, z, s).value; return value ? mul(value, mul(complex(0, winding), offset)) : null; }, 0, TAU, resolution.panels);
    return { functionName: name, center, radius, winding, poles, pathPole, integral, residueSum: sum, numerical, quadraturePanels: resolution.panels, quadratureResolved: resolution.resolved, curve, outputCurve, contourInDomain,
      probe: { z: curve[0], ...evaluate(name, curve[0], s) }, domain: annulus ? { kind: 'annulus', inner: .25, outer: 4.5, holes: [complex(0)] } : { kind: 'punctured-plane', holes: poles.map(p => p.z) },
      theorem: pathPole ? 'A genuine pole lies on the path: the ordinary contour integral and residue-theorem evaluation are undefined. No principal-value substitution is made.' : annulus ? 'The selected annulus is 0.25<|z|<4.5. A hole alone forces neither zero nor nonzero integral: 1/z gives 2πi times winding about 0, whereas z has an entire primitive z²/2 and gives zero. Cauchy’s theorem applies to a contour null-homologous in a holomorphic domain, or to a disk and boundary contained in that domain. Circles leaving the selected annulus are flagged even though the named formula has a continuation.' : 'For a meromorphic function with no path pole, ∮f dz=2πi Σ winding(γ,p) Res(f,p). A pole of order two can have a residue; only the (z−p)⁻¹ coefficient contributes. For the Laurent preset, the z² term is a specified holomorphic remainder and contributes zero.' };
  }
  function taylorModel(raw) {
    const s = normalize(raw), name = s.taylorFn, z = complex(s.pointRe, s.pointIm), N = s.terms, coefficients = []; let factorial = 1;
    for (let j = 0; j <= N; j++) { if (j > 0) factorial *= j; coefficients.push(name === 'geometric' ? 1 : name === 'poles' ? j % 2 ? 0 : (-1) ** (j / 2) : 1 / factorial); }
    const partial = coefficients.reduce((sum, a, j) => add(sum, scale(pow(z, j), a)), complex(0)), probe = evaluate(name, z), magnitude = abs(z), radius = name === 'exp' ? Infinity : 1;
    const valid = magnitude < radius, m = Math.floor(N / 2), error = probe.value ? sub(probe.value, partial) : null;
    let exactRemainder = null, remainderBound = null;
    if (name === 'geometric' && probe.value) exactRemainder = div(pow(z, N + 1), sub(complex(1), z));
    if (name === 'poles' && probe.value) exactRemainder = div(pow(scale(mul(z, z), -1), m + 1), add(complex(1), mul(z, z)));
    if (valid) remainderBound = name === 'geometric' ? magnitude ** (N + 1) / (1 - magnitude) : name === 'poles' ? magnitude ** (2 * m + 2) / (1 - magnitude * magnitude) : Math.exp(magnitude) * magnitude ** (N + 1) / (factorial * (N + 1));
    const singularities = name === 'exp' ? [] : name === 'geometric' ? [complex(1)] : [complex(0, 1), complex(0, -1)];
    return { functionName: name, z, probe: { z, ...probe }, N, coefficients, partial, error, exactRemainder, remainderBound, radius, valid, singularities,
      domain: { kind: 'convergence-disk', center: complex(0), radius },
      inference: { lower: 2, upper: 3, selected: Number(s.inferenceRadius), endpointsAllowed: true, boundaryDetermined: false },
      theorem: 'For the named series the radius is the distance from 0 to the nearest singularity (exp is entire, R=∞). Convergence is guaranteed strictly inside; outside, a Taylor series diverges. Boundary behavior requires a separate test. The assessed evidence “converges throughout |z|<2; diverges at one point of modulus 3” gives only 2≤R≤3. R=2 and R=3 are both possible; divergence at the modulus-3 point does not force R<3. Selecting an admissible radius illustrates the inference and does not identify an unknown series.' };
  }
  const proofSteps = Object.freeze([
    Object.freeze({ id: 'root-free', requires: [], text: 'Assume, for contradiction, that a polynomial p of degree n≥1 has no complex root.' }),
    Object.freeze({ id: 'reciprocal', requires: ['root-free'], text: 'Then q=1/p is holomorphic everywhere: p never vanishes, so the reciprocal is entire.' }),
    Object.freeze({ id: 'exterior', requires: ['root-free'], text: 'Write p(z)=aₙzⁿ+Σⱼ₌₀ⁿ⁻¹aⱼzʲ with aₙ≠0. If A=Σⱼ<n|aⱼ| and R₀=max(1,2A/|aₙ|), then |z|≥R₀ implies |p(z)|≥|aₙ||z|ⁿ−A|z|ⁿ⁻¹≥(|aₙ|/2)|z|ⁿ. Thus |q(z)|≤2/(|aₙ||z|ⁿ) outside the disk and q(z)→0 as |z|→∞.' }),
    Object.freeze({ id: 'interior', requires: ['root-free', 'reciprocal', 'exterior'], text: 'On the compact disk |z|≤R₀, q is continuous, so |q| attains a finite maximum. Together with the exterior bound this supplies one GLOBAL finite bound for q on C. A finite sampled minimum of |p| would not justify this step.' }),
    Object.freeze({ id: 'liouville', requires: ['reciprocal', 'exterior', 'interior'], text: 'Liouville: every globally bounded entire function is constant. For every center c, Cauchy’s estimate gives |q′(c)|≤M/R for arbitrarily large R; hence q′(c)=0. The connected plane makes q constant.' }),
    Object.freeze({ id: 'contradiction', requires: ['root-free', 'liouville'], text: 'The constant q must be 0 because q→0 at infinity, but q=1/p is never 0. Contradiction. Every nonconstant complex polynomial therefore has a complex root. Repeated division by (z−root) yields its degree-many roots counted with multiplicity.' }),
  ]);
  function polynomialExterior(coefficients) {
    if (!Array.isArray(coefficients) || coefficients.length < 2 || coefficients.length > 16 || coefficients.some(c => !c || !Number.isFinite(c.re) || !Number.isFinite(c.im))) throw new RangeError('Two to sixteen finite complex coefficients in ascending degree required.');
    const leading = abs(coefficients.at(-1)); if (leading === 0) throw new RangeError('Nonzero leading coefficient required.');
    const A = coefficients.slice(0, -1).reduce((total, c) => total + abs(c), 0), radius = Math.max(1, 2 * A / leading), degree = coefficients.length - 1;
    return { A, leading, degree, radius, lowerAtRadius: leading * radius ** degree / 2, reciprocalUpperAtRadius: 2 / (leading * radius ** degree) };
  }
  function liouvilleModel(raw) {
    const s = normalize(raw), R = s.growthRadius, name = s.growthFn, diskMaximum = name === 'constant' ? 1 : name === 'linear' ? R : Math.exp(R), globalBounded = name === 'constant';
    const coefficients = [complex(1, -1), complex(-2), complex(0, 1), complex(1)], exterior = polynomialExterior(coefficients), revealed = proofSteps.slice(0, Number(s.proofStep));
    return { functionName: name, R, diskMaximum, diskCauchyBound: diskMaximum / R, globalM: s.globalM, hypotheticalCauchyBound: s.globalM / R, globalBounded,
      coefficients, exterior, steps: revealed, allSteps: proofSteps,
      growth: Array.from({ length: 45 }, (_, j) => { const radius = .5 + j * 11.5 / 44; return { radius, magnitude: name === 'constant' ? 1 : name === 'linear' ? radius : Math.exp(radius), hypotheticalBound: s.globalM / radius }; }),
      probe: { z: complex(R), ...evaluate(name, complex(R)) }, domain: { kind: 'plane', entire: true },
      theorem: 'Every named comparison is bounded on each fixed compact disk. Only the constant has a finite GLOBAL bound. Liouville requires the same M for all radii: a growing disk maximum M(R) cannot be held fixed in the proof. The hypothetical M/R curve shows a theorem assumption, not a numerical certificate that z or exp(z) is bounded. The polynomial coefficients illustrate a valid exterior inequality; the proof below applies to arbitrary degree n≥1.' };
  }
  function meanModel(raw) {
    const s = normalize(raw), name = s.meanFn, center = complex(s.circleRe, s.circleIm), radius = s.radius, curve = circlePoints(center, radius), probe = evaluate(name, center), distance = abs(sub(center, complex(1))), pathPole = name === 'geometric' && Math.abs(distance - radius) <= 1e-12;
    const holomorphic = !['abs2', 'peak'].includes(name), diskContained = name !== 'geometric' || distance > radius;
    let mean;
    if (pathPole) mean = null;
    else if (name === 'abs2') mean = complex(abs(center) ** 2 + radius ** 2);
    else if (name === 'peak') mean = complex(1 - abs(center) ** 2 - radius ** 2);
    else if (name === 'geometric' && distance < radius) mean = complex(0);
    else mean = probe.value;
    const outputs = curve.slice(0, -1).map(z => ({ z, ...evaluate(name, z) }));
    const resolution = pathPole ? { panels: 0, resolved: false } : quadratureResolution(radius, 1, name === 'geometric' ? Math.abs(distance - radius) : Infinity);
    if (!pathPole) resolution.panels = Math.max(4096, resolution.panels); // |f| can have corners at circle zeros.
    const circleIntegral = pathPole ? null : integrate(theta => evaluate(name, add(center, polar(radius, theta))).value, 0, TAU, resolution.panels);
    const numericMean = circleIntegral ? scale(circleIntegral, 1 / TAU) : null;
    const modulusIntegral = pathPole ? null : integrate(theta => { const value = evaluate(name, add(center, polar(radius, theta))).value; return value ? complex(abs(value)) : null; }, 0, TAU, resolution.panels);
    const numericModulusMean = modulusIntegral ? modulusIntegral.re / TAU : null;
    const minDistance = Math.abs(abs(center) - radius), maxDistance = abs(center) + radius;
    const maxModulus = pathPole ? null : name === 'constant' ? 1 : name === 'z2' || name === 'abs2' ? maxDistance ** 2 : name === 'exp' ? Math.exp(center.re + radius) : name === 'geometric' ? 1 / Math.abs(distance - radius) : Math.max(Math.abs(1 - minDistance ** 2), Math.abs(1 - maxDistance ** 2));
    const meanEquality = holomorphic && diskContained, constantEquality = name === 'constant';
    return { functionName: name, center, radius, probe: { z: center, ...probe }, curve, outputs, mean, numericMean, modulusMean: numericModulusMean, quadraturePanels: resolution.panels, quadratureResolved: resolution.resolved, maxModulus, holomorphic, diskContained, pathPole, meanEquality, constantEquality,
      poles: name === 'geometric' ? [{ z: complex(1), order: 1 }] : [], domain: { kind: name === 'geometric' ? 'punctured-plane' : 'plane', holomorphic },
      theorem: 'If f is holomorphic on an open neighborhood of the closed disk, f(c)=(1/2π)∫f(c+reⁱᶿ)dθ. This is a COMPLEX mean; the mean of |f| generally differs from |f(c)|. At a local modulus maximum choose a small contained disk: |f(c)|≤mean |f|≤|f(c)|. Equality and continuity force the boundary values to have the same phase and modulus (if f(c)=0, all are zero); Cauchy’s formula makes f constant inside. The identity theorem extends constancy throughout the connected domain. To assert that a maximum is attained on the boundary of a bounded domain, also require continuity on its compact closure. Nonholomorphic |z|² and 1−|z|² cannot refute this theorem.' };
  }
  function arcFactor(name, z, a) {
    if (name === 'one') return complex(1);
    if (name === 'linear') return div(complex(1), add(z, complex(0, a)));
    if (name === 'quadratic') return div(complex(1), add(mul(z, z), complex(a * a)));
    throw new RangeError('Unknown Jordan factor.');
  }
  function jordanModel(raw) {
    const s = normalize(raw), R = s.arcRadius, a = s.poleA, k = s.k, lower = s.halfPlane === 'lower', sign = lower ? -1 : 1, name = s.arcFn;
    const factorSupremum = name === 'one' ? 1 : name === 'linear' ? lower ? 1 / (R - a) : 1 / Math.sqrt(R * R + a * a) : 1 / (R * R - a * a);
    const matching = k !== 0 && k * sign > 0, decayingFactor = name !== 'one', jordanBound = matching ? PI * factorSupremum / Math.abs(k) : null;
    const ordinaryLengthBound = matching || k === 0 ? PI * R * factorSupremum : PI * R * factorSupremum * Math.exp(Math.abs(k) * R);
    const integrand = z => mul(exponential(mul(complex(0, k), z)).value, arcFactor(name, z, a));
    const realIntegral = name === 'one' ? complex(k === 0 ? 2 * R : 2 * Math.sin(k * R) / k) : integrate(x => integrand(complex(x)), -R, R, 1024);
    let residueSum = complex(0), poles = [];
    if (name === 'linear') { const residue = complex(Math.exp(k * a)); poles = [{ z: complex(0, -a), residue, enclosed: lower }]; if (lower) residueSum = residue; }
    if (name === 'quadratic') { const upperResidue = complex(0, -Math.exp(-k * a) / (2 * a)), lowerResidue = complex(0, Math.exp(k * a) / (2 * a)); poles = [{ z: complex(0, a), residue: upperResidue, enclosed: !lower }, { z: complex(0, -a), residue: lowerResidue, enclosed: lower }]; residueSum = lower ? lowerResidue : upperResidue; }
    const closedIntegral = mul(complex(0, sign * TAU), residueSum), arcIntegral = sub(closedIntegral, realIntegral);
    const directArc = integrate(theta => { const z = polar(R, sign * theta), dz = mul(complex(0, sign), z); return mul(integrand(z), dz); }, 0, PI, 1024);
    const samples = Array.from({ length: 97 }, (_, j) => { const theta = PI * j / 96, z = polar(R, sign * theta), expLogAbs = -k * z.im; return { z, theta, expLogAbs, value: integrand(z), factorMagnitude: abs(arcFactor(name, z, a)) }; });
    return { functionName: name, R, a, k, halfPlane: s.halfPlane, orientation: sign, matching, decayingFactor, certificate: matching && decayingFactor, factorSupremum, jordanBound, ordinaryLengthBound,
      realIntegral, arcIntegral, directArc, closedIntegral, residueSum, poles, samples, curve: samples.map(p => p.z), probe: { z: samples[48].z, ...sample(samples[48].value) },
      domain: { kind: 'semicircle', radius: R, halfPlane: s.halfPlane },
      theorem: 'For eⁱᵏᶻg(z), |eⁱᵏᶻ|=exp(−k Im z). A matching half-plane is upper for k>0, lower for k<0. On its radius-R arc, M_R=sup|g| gives |∫arc|≤πM_R/|k| using sin θ≥2θ/π on [0,π/2]; M_R→0 then proves decay. The wrong half-plane grows and k=0 has no Jordan certificate. For g=1, M_R=1 does not tend to 0: the arc is exactly −2 sin(kR)/k (or −2R for k=0), so it need not vanish. A rational form by itself supplies no unconditional shortcut. The lower closure is clockwise, so its closed integral is −2πi times its enclosed residues. Displayed arc values use finite residue balance; direct arc quadrature supplies a separate numerical check.' };
  }
  function build(raw) {
    const state = normalize(raw), station = state.station, active = ({ C1: directionalModel, C2: contourModel, C3: taylorModel, C4: liouvilleModel, C5: meanModel, C6: jordanModel })[station](state);
    let rows, readout;
    if (station === 'C1') { const d = active, J = d.jacobian; rows = [['Point f(z)', formatSample(d.probe), d.probe.status], ['Jacobian (uₓ,uᵧ;vₓ,vᵧ)', J ? [J.ux, J.uy, J.vx, J.vy].map(fmt).join(', ') : 'log-only, finite Jacobian unavailable', 'Exact derivatives of the named function'], ['CR equations', d.cr === null ? 'finite readout unavailable' : d.cr ? 'hold' : 'fail', 'uₓ=vᵧ and uᵧ=−vₓ'], ['Complex derivative at this point', d.pointwise ? formatComplex(d.derivative) : 'does not exist', d.regularity], ['Selected quotient', formatSample(d.selected), 'h=' + fmt(d.h) + ', θ=' + fmt(state.angle) + '°'], ['ln |quotient|', fmt(d.selected.logAbs), 'Safe logarithm; underflow/overflow disclosed']]; readout = 'C1: ' + state.directionalFn + ' at ' + formatComplex(d.z) + '. Pointwise complex derivative ' + (d.pointwise ? 'exists: ' + formatComplex(d.derivative) : 'does not exist') + '. CR ' + (d.cr ? 'hold' : d.cr === null ? 'finite ledger unavailable' : 'fail') + '. ' + d.neighborhood + ' Approach angle ' + state.angle + ' degrees; h=' + fmt(d.h) + '; quotient=' + formatSample(d.selected) + '; ln magnitude=' + fmt(d.selected.logAbs) + '. ' + d.regularity; }
    if (station === 'C2') { const d = active; rows = [['Integral ∮ f dz', d.pathPole ? 'UNDEFINED: pole on path' : formatComplex(d.integral), '2πi times signed residue sum'], ['Independent finite quadrature', formatComplex(d.numerical), d.pathPole ? 'Not evaluated at a path pole' : d.quadraturePanels + '-panel Simpson, resolved using nearest pole gap' + (d.quadratureResolved ? '' : '; resolution cap reached: check unresolved')], ['Signed residue sum', formatComplex(d.residueSum), 'Includes complex residues; removed zero terms are not poles'], ...d.poles.map(p => ['Pole ' + formatComplex(p.z), 'order ' + p.order + ', residue ' + formatComplex(p.residue), p.path ? 'ON PATH: undefined' : 'winding ' + p.winding]), ['Contour in selected domain', d.contourInDomain ? 'yes' : 'no', d.domain.kind]]; readout = 'C2: ' + state.contourFn + ', center ' + formatComplex(d.center) + ', radius ' + d.radius + ', signed winding ' + d.winding + '. Integral ' + (d.pathPole ? 'undefined because of a path pole' : formatComplex(d.integral)) + '. ' + d.poles.map(p => 'Pole ' + formatComplex(p.z) + ', order ' + p.order + ', residue ' + formatComplex(p.residue) + ', winding ' + fmt(p.winding) + '.').join(' ') + ' Contour in selected domain: ' + (d.contourInDomain ? 'yes.' : 'no.'); }
    if (station === 'C3') { const d = active; rows = [['Radius R', fmt(d.radius), 'Nearest singularity from expansion center 0'], ['Probe |z|', fmt(abs(d.z)), d.valid ? 'inside convergence disk' : abs(d.z) === d.radius ? 'boundary: no general guarantee' : 'outside convergence disk'], ['Coefficients a₀…aₙ', d.coefficients.map(fmt).join(', '), 'Exact coefficient rule; displayed decimal values'], ['Partial sum Sₙ', formatComplex(d.partial), 'Degrees 0 through ' + d.N], ['f(z)−Sₙ', formatComplex(d.error), 'Finite error does not prove convergence outside R'], ['Valid remainder bound', fmt(d.remainderBound), d.valid ? '|error| ≤ bound' : 'No convergence bound issued at/outside R'], ['Assessed inference', '2 ≤ R ≤ 3', 'Selected ' + d.inference.selected + '; endpoints allowed; boundary undetermined']]; readout = 'C3: Taylor ' + state.taylorFn + ' about 0 through degree ' + d.N + ', probe ' + formatComplex(d.z) + '. Radius ' + fmt(d.radius) + '; partial sum ' + formatComplex(d.partial) + '; actual finite error ' + formatComplex(d.error) + '; valid remainder bound ' + fmt(d.remainderBound) + '. Assessed evidence gives 2≤R≤3; chosen admissible radius ' + d.inference.selected + '. Both endpoints are possible; boundary behavior is not determined.'; }
    if (station === 'C4') { const d = active; rows = [['Named function on radius R', state.growthFn, 'R=' + fmt(d.R)], ['Disk maximum M(R)', fmt(d.diskMaximum), 'Finite-disk boundedness alone does not invoke Liouville'], ['Disk estimate M(R)/R', fmt(d.diskCauchyBound), 'Recomputed as R changes'], ['Hypothetical global M/R', fmt(d.hypotheticalCauchyBound), 'M=' + fmt(d.globalM) + ' held fixed; tends to zero as R→∞'], ['Actually globally bounded preset', d.globalBounded ? 'yes, constant 1' : 'no', 'Global claim follows analytically, not from sampled disks'], ['Illustrative polynomial exterior R₀', fmt(d.exterior.radius), 'p(z)=z³+iz²−2z+(1−i); degree 3'], ['Proof steps revealed', d.steps.length + '/6', 'Dependency order: root-free → entire → exterior + compact interior → Liouville → contradiction']]; readout = 'C4: ' + state.growthFn + ' on radius ' + d.R + ', disk maximum ' + fmt(d.diskMaximum) + ', disk estimate ' + fmt(d.diskCauchyBound) + '. Global boundedness: ' + (d.globalBounded ? 'constant 1 is globally bounded.' : 'this nonconstant preset is not globally bounded.') + ' Hypothetical fixed global M=' + d.globalM + ' gives M/R=' + fmt(d.hypotheticalCauchyBound) + '. Revealed proof steps ' + d.steps.length + ' of 6. ' + d.steps.map(p => p.text).join(' '); }
    if (station === 'C5') { const d = active; rows = [['Center f(c)', formatComplex(d.probe.value), 'c=' + formatComplex(d.center)], ['Complex circle mean', formatComplex(d.mean), d.pathPole ? 'Undefined: boundary pole' : 'Exact named-function mean'], ['Mean |f|', fmt(d.modulusMean), 'Numerical mean of modulus; generally different from |f(c)|'], ['Boundary max |f|', fmt(d.maxModulus), 'Analytic circle maximum for the preset'], ['Holomorphic on neighborhood of closed disk', d.holomorphic && d.diskContained ? 'yes' : 'no', !d.holomorphic ? 'Nonholomorphic contrast' : 'Disk meets/encloses pole'], ['Mean theorem applies', d.meanEquality ? 'yes' : 'no', 'Complex equality requires all hypotheses'], ['Constant equality case', d.constantEquality ? 'yes' : 'no', 'Triangle equality + identity theorem on a connected domain']]; readout = 'C5: ' + state.meanFn + ', center ' + formatComplex(d.center) + ', radius ' + d.radius + '. Center value ' + formatComplex(d.probe.value) + ', complex circle mean ' + formatComplex(d.mean) + ', mean modulus ' + fmt(d.modulusMean) + ', maximum boundary modulus ' + fmt(d.maxModulus) + '. Holomorphic closed-disk hypothesis ' + (d.meanEquality ? 'satisfied.' : 'fails.') + ' Constant equality preset: ' + (d.constantEquality ? 'yes.' : 'no.'); }
    if (station === 'C6') { const d = active; rows = [['Closure and orientation', d.halfPlane + ', ' + (d.orientation > 0 ? 'counterclockwise' : 'clockwise'), 'k=' + d.k + ', R=' + d.R + ', a=' + d.a], ['Finite real segment ∫₋ᴿᴿ', formatComplex(d.realIntegral), 'Real axis travels −R→R'], ['Finite closing arc ∫', formatComplex(d.arcIntegral), 'Arc travels R→−R; finite residue balance'], ['Direct arc quadrature', formatComplex(d.directArc), 'Independent parameter integration; numerical cancellation in growing half-plane'], ['Closed residue integral', formatComplex(d.closedIntegral), (d.orientation > 0 ? '+' : '−') + '2πi Σ residues'], ['M_R=sup arc |g|', fmt(d.factorSupremum), d.decayingFactor ? 'tends to zero as R→∞' : 'equals 1, no decay'], ['Jordan bound πM_R/|k|', fmt(d.jordanBound), d.matching ? 'valid bound; decay also needs M_R→0' : 'not issued: k=0 or wrong half-plane'], ['Jordan decay certificate', d.certificate ? 'yes' : 'no', 'Correct sign, half-plane and decaying remaining factor required'], ['Ordinary arc length bound', fmt(d.ordinaryLengthBound), 'Valid finite bound even without Jordan decay']]; readout = 'C6: exp(ikz) times ' + state.arcFn + ', k=' + d.k + ', ' + d.halfPlane + ' closure, R=' + d.R + ', a=' + d.a + '. Real segment integral ' + formatComplex(d.realIntegral) + ', finite arc integral ' + formatComplex(d.arcIntegral) + ', closed integral ' + formatComplex(d.closedIntegral) + '. M_R=' + fmt(d.factorSupremum) + '; Jordan bound ' + fmt(d.jordanBound) + '; decay certificate ' + (d.certificate ? 'valid.' : 'absent.') + ' At the arc midpoint ln|exponential|=' + fmt(d.samples[48].expLogAbs) + '. ' + (d.k === 0 ? 'k=0 has no exponential decay.' : !d.matching ? 'The chosen exponential grows into this half-plane.' : d.decayingFactor ? 'The remaining factor decays uniformly.' : 'g=1 is a counterexample: its arc oscillates and need not tend to zero.'); }
    const proof = active.theorem;
    return { state, station, active, rows, readout, proof };
  }
  function element(tag, attrs = {}, ...children) { const e = document.createElement(tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v))); children.forEach(c => { if (c != null) e.append(c.nodeType ? c : document.createTextNode(String(c))); }); return e; }
  function shape(tag, attrs = {}, text) { const e = document.createElementNS(NS, tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v))); if (text != null) e.textContent = String(text); return e; }
  function text(svg, x, y, value, attrs = {}) { svg.append(shape('text', { x, y, fill: COLORS.ink, 'font-size': 11, ...attrs }, value)); }
  function axisLabel(value) { return Math.abs(value) >= 1e5 || value !== 0 && Math.abs(value) < 1e-4 ? value.toExponential(2) : fmt(value); }
  function line(svg, points, color, attrs = {}) { if (points.length > 1) svg.append(shape('polyline', { points: points.map(p => p.join(',')).join(' '), fill: 'none', stroke: color, 'stroke-width': 1.8, ...attrs })); }
  function render(item, hooks) {
    if (item?.props?.scenario !== SCENARIO || Object.keys(item.props).length !== 1 || item.renderer && item.renderer !== 'math-complex-lab') return null;
    const uid = 'complex-' + ++serial, title = item.title || 'Holomorphy, contours and theorem hypotheses', instructions = item.instructions || 'Explore six stations with named functions. Read the domain and theorem hypotheses before comparing derivatives, integrals, series and bounds.';
    const root = element('section', { class: 'card lesson-model math-complex-lab', 'data-renderer': 'math-complex-lab', 'aria-labelledby': uid + '-title' });
    const heading = element('div', { class: 'model-heading-row' }, element('h3', { id: uid + '-title' }, title));
    const area = element('div', { class: 'model-controls concept-controls complex-controls' }), widgets = new Map();
    const panels = element('div', { class: 'complex-panels' }), pictures = [];
    ['Input plane / analytic comparison', 'Complex output / bounds'].forEach(name => { const view = element('div', { class: 'complex-viewport', tabindex: '0', role: 'region', 'aria-label': name + '; enlarge for detail' }), svg = shape('svg', { viewBox: '0 0 480 340', role: 'img', focusable: 'false' }); view.append(svg); panels.append(view); pictures.push(svg); });
    const table = element('table', { class: 'complex-ledger' }), tableView = element('div', { class: 'complex-table-region', tabindex: '0', role: 'region', 'aria-label': 'Current calculation and hypothesis ledger; scroll horizontally' }, table);
    const readout = element('p', { class: 'model-readout' }), proof = element('p', { class: 'complex-proof' }), steps = element('ol', { class: 'complex-proof-steps' });
    const caveat = element('p', { class: 'spatial-note' }, 'A finite plot or sampled directions cannot prove an open-set or global theorem. All functions are named presets; numeric quadrature is a check, not a proof. Logarithms retain overflow information. Zero has undefined phase, and genuine poles have undefined function values. Enlarge preserves the state; reset restores every control and fits the plots.');
    const live = element('p', { class: 'model-status', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    let model = build(initial), enlarged = false;
    const stateKey = 'math.5.complex-analysis', stateBus = typeof window !== 'undefined' ? window.PrimerLessonStateBus : null;
    function refresh(announce, publish = false) {
      const s = model.state; root.setAttribute('data-complex-state', JSON.stringify(s));
      widgets.forEach(({ input, label }, key) => { const c = controls.find(c => c.key === key), visible = !c.stations || c.stations.includes(s.station); label.hidden = !visible || c.presets && !c.presets.includes(s.contourFn); input.disabled = label.hidden; input.value = String(s[key]); });
      table.replaceChildren(element('caption', {}, 'Current calculation and theorem hypotheses'), element('thead', {}, element('tr', {}, ...['Quantity', 'Value', 'Meaning / hypothesis'].map(v => element('th', { scope: 'col' }, v)))), element('tbody', {}, ...model.rows.map(row => element('tr', {}, element('th', { scope: 'row' }, row[0]), element('td', {}, row[1]), element('td', {}, row[2])))));
      readout.textContent = model.readout; proof.textContent = model.proof; steps.hidden = s.station !== 'C4'; steps.replaceChildren(...(s.station === 'C4' ? model.active.steps.map(step => element('li', { 'data-complex-proof-step': step.id }, step.text)) : []));
      draw(); if (announce) live.textContent = model.readout;
      if (publish) stateBus?.publish(stateKey, root, model.state);
    }
    for (const c of controls) {
      const id = uid + '-' + c.key, input = element(c.options ? 'select' : 'input', { id, 'data-complex-control': c.key });
      if (c.options) c.options.forEach(o => input.append(element('option', { value: o.value }, o.label)));
      else Object.entries({ type: 'number', min: c.min, max: c.max, step: c.step, inputmode: 'decimal' }).forEach(([k, v]) => input.setAttribute(k, v));
      const commit = () => { model = build({ ...model.state, [c.key]: input.value }); refresh(true, true); };
      input.addEventListener('change', commit); input.addEventListener('blur', () => { if (String(model.state[c.key]) !== input.value) commit(); });
      const label = element('label', { for: id, class: 'model-range-control' }, element('span', {}, c.label), input); widgets.set(c.key, { input, label }); area.append(label);
    }
    const buttons = element('div', { class: 'model-button-row complex-fixtures' });
    const fixtures = [
      ['abszero', '|z|²: derivative only at zero', { station: 'C1', directionalFn: 'abs2', pointRe: 0, pointIm: 0 }],
      ['pathology', 'CR pathology at zero', { station: 'C1', directionalFn: 'pathology', pointRe: 0, pointIm: 0, angle: 45, logStep: -1 }],
      ['laurent', 'Assessed Laurent: +10πi', { station: 'C2', contourFn: 'laurent', circleRe: 0, circleIm: 0, radius: 1, winding: '1' }],
      ['imagpole', 'Only i: residue −i/2', { station: 'C2', contourFn: 'poles', circleRe: 0, circleIm: 1, radius: .5, winding: '1' }],
      ['pathpole', 'Pole on path: undefined', { station: 'C2', contourFn: 'poles', circleRe: 0, circleIm: 0, radius: 1 }],
      ['inference', 'Assessed radius evidence', { station: 'C3', inferenceRadius: '2.5' }],
      ['fta', 'Complete Liouville → FTA proof', { station: 'C4', proofStep: '6' }],
      ['mean', 'Complex mean: z² on a disk', { station: 'C5', meanFn: 'z2', circleRe: 0, circleIm: 0, radius: 1 }],
      ['jordan', 'Jordan: k>0, upper, decaying g', { station: 'C6', arcFn: 'quadratic', k: 1, halfPlane: 'upper', arcRadius: 3, poleA: 1 }],
      ['counterexample', 'g=1: arc need not vanish', { station: 'C6', arcFn: 'one', k: 1, halfPlane: 'upper' }],
    ];
    for (const [key, name, patch] of fixtures) { const button = element('button', { type: 'button', class: 'btn ghost small', 'data-complex-action': key }, name); button.addEventListener('click', () => { model = build({ ...model.state, ...patch }); refresh(true, true); }); buttons.append(button); }
    const reset = element('button', { type: 'button', class: 'btn ghost small', 'data-complex-action': 'reset' }, 'Reset activity'); reset.addEventListener('click', () => { model = build(initial); size(false); refresh(true, true); }); buttons.append(reset);
    const enlarge = element('button', { type: 'button', class: 'btn ghost small', 'aria-pressed': 'false', 'data-complex-action': 'enlarge' }, 'Enlarge plots');
    function size(on) { enlarged = on; root.classList.toggle('is-enlarged', on); enlarge.setAttribute('aria-pressed', String(on)); enlarge.textContent = on ? 'Fit plots' : 'Enlarge plots'; }
    enlarge.addEventListener('click', () => size(!enlarged)); heading.append(enlarge);
    const sources = element('p', { class: 'spatial-note' }, 'Sources: ', element('a', { href: 'https://ocw.mit.edu/courses/18-04-complex-variables-with-applications-spring-2018/pages/lecture-notes/', target: '_blank', rel: 'noopener' }, 'MIT 18.04 notes: analyticity, Cauchy formula, Taylor series and residues'), '.');
    root.append(heading, element('p', { class: 'model-instructions' }, instructions), area, buttons, panels, tableView, readout, proof, steps, caveat, sources, live);
    if (hooks?.speakButton) heading.prepend(hooks.speakButton(() => title + '. ' + instructions + '. ' + model.readout + ' ' + model.rows.map(row => row.join(': ')).join('. ') + '. ' + model.proof + ' ' + (model.station === 'C4' ? model.active.steps.map(p => p.text).join(' ') : '') + ' ' + caveat.textContent, 'Read this activity aloud'));
    function setup(index, name) { const svg = pictures[index]; svg.replaceChildren(shape('title', { id: uid + '-plot-title-' + index }, name), shape('desc', { id: uid + '-plot-desc-' + index }, model.readout), shape('rect', { x: 0, y: 0, width: 480, height: 340, rx: 10, fill: COLORS.paper })); svg.setAttribute('aria-labelledby', uid + '-plot-title-' + index); svg.setAttribute('aria-describedby', uid + '-plot-desc-' + index); text(svg, 18, 27, name, { 'font-size': 16, 'font-weight': 600 }); return svg; }
    function axes(svg, bound, output = false) {
      const X = x => 250 + 110 * x / bound, Y = y => 183 - 110 * y / bound;
      for (let j = -2; j <= 2; j++) { const value = bound * j / 2; line(svg, [[X(value), 73], [X(value), 293]], j === 0 ? COLORS.ink : COLORS.grid, { 'stroke-width': .8 }); line(svg, [[140, Y(value)], [360, Y(value)]], j === 0 ? COLORS.ink : COLORS.grid, { 'stroke-width': .8 }); text(svg, X(value), 309, axisLabel(value), { 'text-anchor': 'middle' }); text(svg, 130, Y(value) + 3, axisLabel(value), { 'text-anchor': 'end' }); }
      text(svg, 250, 332, output ? 'Re output (horizontal) · Im output (vertical)' : 'Re z (horizontal) · Im z (vertical)', { 'text-anchor': 'middle' });
      return z => [X(z.re), Y(z.im)];
    }
    function mark(svg, point, color, attributes = {}) { svg.append(shape('circle', { cx: point[0], cy: point[1], r: 4, fill: color, ...attributes })); }
    function numericPlot(svg, series, xRange, yRange, names) {
      const X = x => 82 + 355 * (x - xRange[0]) / (xRange[1] - xRange[0]), Y = y => 284 - 206 * (y - yRange[0]) / (yRange[1] - yRange[0]);
      for (let j = 0; j <= 4; j++) { const x = xRange[0] + (xRange[1] - xRange[0]) * j / 4, y = yRange[0] + (yRange[1] - yRange[0]) * j / 4; line(svg, [[X(x), 78], [X(x), 284]], COLORS.grid, { 'stroke-width': .8 }); line(svg, [[82, Y(y)], [437, Y(y)]], COLORS.grid, { 'stroke-width': .8 }); text(svg, X(x), 306, axisLabel(x), { 'text-anchor': 'middle' }); text(svg, 72, Y(y) + 3, axisLabel(y), { 'text-anchor': 'end' }); }
      series.forEach((data, j) => line(svg, data.filter(q => q.every(Number.isFinite)).map(([x, y]) => [X(x), Y(Math.max(yRange[0], Math.min(yRange[1], y)))]), [COLORS.blue, COLORS.coral, COLORS.teal][j], { 'data-complex-series': names[j] }));
      return { X, Y };
    }
    function outputPlane(svg, values, centerValue) {
      const finite = values.filter(q => q.value && ['regular', 'discontinuous-extension'].includes(q.status || 'regular')), limit = Math.max(1, ...finite.map(q => abs(q.value)), centerValue ? abs(centerValue) : 0) * 1.15, project = axes(svg, limit, true);
      // Flush at every omitted/pole/log-only point: no line crosses a pole or overflow.
      let segment = []; values.forEach(q => { if (!q.value || q.status && !['regular', 'discontinuous-extension'].includes(q.status)) { line(svg, segment, COLORS.blue, { 'data-complex-output': 'curve' }); segment = []; } else segment.push(project(q.value)); }); line(svg, segment, COLORS.blue, { 'data-complex-output': 'curve' });
      if (centerValue) mark(svg, project(centerValue), COLORS.coral, { 'data-complex-output': 'probe' });
      text(svg, 18, 53, 'Blue finite outputs · coral probe / integral / mean');
    }
    function draw() {
      const d = model.active, s = model.state;
      if (s.station === 'C1') {
        const left = setup(0, 'Directional approaches at the probe'), project = axes(left, Math.max(1, abs(d.z) + d.h) * 1.25);
        d.directions.slice(0, 3).forEach((p, i) => line(left, [project(d.z), project(p.quotient.endpoint)], [COLORS.blue, COLORS.coral, COLORS.teal][i], { 'data-complex-direction': i }));
        line(left, [project(d.z), project(d.selected.endpoint)], COLORS.gold, { 'stroke-width': 3, 'data-complex-direction': 'selected' }); mark(left, project(d.z), COLORS.ink);
        text(left, 18, 53, 'θ=0°,45°,90° plus selected angle; h=' + fmt(d.h));
        const right = setup(1, 'Step-size quotient: natural log magnitude'), finiteLogs = d.steps.map(p => p.quotient.logAbs).filter(Number.isFinite), low = Math.min(-5, ...finiteLogs), high = Math.max(5, ...finiteLogs), range = Math.max(1, high - low);
        numericPlot(right, [d.steps.filter(p => Number.isFinite(p.quotient.logAbs)).map(p => [Math.log10(p.h), p.quotient.logAbs])], [-4, -.5], [low - .05 * range, high + .05 * range], ['log-quotient']); text(right, 18, 53, 'Horizontal log₁₀ h; zero has ln magnitude −∞.'); text(right, 250, 332, 'A finite sample does not prove a directional limit.', { 'text-anchor': 'middle' });
      } else if (s.station === 'C2' || s.station === 'C5') {
        const left = setup(0, s.station === 'C2' ? 'Contour, winding and genuine poles' : 'Circle and closed-disk hypothesis'), max = Math.max(1, abs(d.center) + d.radius, d.domain.outer || 0, ...(d.poles || []).map(p => abs(p.z))) * 1.25, project = axes(left, max);
        if (d.domain.kind === 'annulus') for (const radius of [d.domain.inner, d.domain.outer]) line(left, circlePoints(complex(0), radius).map(project), COLORS.grid, { 'stroke-dasharray': '4 3' });
        line(left, d.curve.map(project), d.pathPole ? COLORS.coral : COLORS.teal, { 'data-complex-circle': s.station }); mark(left, project(d.center), COLORS.gold);
        (d.poles || []).forEach(p => { mark(left, project(p.z), COLORS.coral, { 'data-complex-pole': formatComplex(p.z) }); const q = project(p.z); text(left, q[0] + 7, q[1] - 5, formatComplex(p.z)); });
        text(left, 18, 53, s.station === 'C2' ? 'Winding ' + d.winding + '; ' + (d.pathPole ? 'path pole: integral undefined' : 'no path pole') : d.meanEquality ? 'Holomorphic on a neighborhood of the closed disk.' : 'Mean-value hypotheses fail for this disk/function.');
        const right = setup(1, s.station === 'C2' ? 'Complex outputs along the contour' : 'Complex circle outputs and center value'); outputPlane(right, d.pathPole ? [] : s.station === 'C2' ? d.outputCurve : [...d.outputs, d.outputs[0]], d.pathPole ? null : s.station === 'C2' ? d.integral : d.probe.value);
        if (d.pathPole) text(right, 18, 70, 'Boundary pole: output trace omitted, integral undefined.');
        if (s.station === 'C5' && d.mean) { const finite = d.outputs.filter(q => q.value).map(q => abs(q.value)), bound = Math.max(1, ...finite, d.probe.value ? abs(d.probe.value) : 0) * 1.15; const p = [250 + 110 * d.mean.re / bound, 183 - 110 * d.mean.im / bound]; mark(right, p, COLORS.gold, { 'data-complex-output': 'mean' }); text(right, 18, 70, 'Gold complex mean; modulus mean is in the ledger.'); }
      } else if (s.station === 'C3') {
        const left = setup(0, 'Taylor convergence disk about zero'), bound = Math.max(1.4, abs(d.z) * 1.2), project = axes(left, bound);
        if (Number.isFinite(d.radius)) line(left, circlePoints(complex(0), d.radius).map(project), COLORS.teal, { 'data-complex-convergence': 'radius' });
        d.singularities.forEach(z => mark(left, project(z), COLORS.coral)); mark(left, project(d.z), COLORS.gold, { 'data-complex-probe': 'taylor' }); text(left, 18, 53, 'R=' + fmt(d.radius) + '; inside only, boundary needs a test.');
        const right = setup(1, 'Exact coefficient and finite partial-sum comparison'); outputPlane(right, [{ value: d.partial }, { value: d.probe.value }], d.probe.value); text(right, 18, 70, 'Partial sum ' + formatComplex(d.partial)); text(right, 18, 88, 'Assessed evidence: 2≤R≤3, endpoints allowed.');
      } else if (s.station === 'C4') {
        const left = setup(0, 'Finite disk maxima: ln M(R)'), points = d.growth.map(q => [q.radius, Math.log(q.magnitude)]), lo = Math.min(0, ...points.map(q => q[1])), hi = Math.max(1, ...points.map(q => q[1])); numericPlot(left, [points], [.5, 12], [lo, hi], ['growth']); text(left, 18, 53, 'Constant: 0 · z: ln R · exp: R; finite disk bound.'); text(left, 250, 332, 'Horizontal radius R; vertical natural log maximum.', { 'text-anchor': 'middle' });
        const right = setup(1, 'Hypothetical global Cauchy estimate M/R'); numericPlot(right, [d.growth.map(q => [q.radius, q.hypotheticalBound])], [.5, 12], [0, 2 * d.globalM], ['cauchy-bound']); text(right, 18, 53, 'Same hypothetical global M=' + fmt(d.globalM) + ' for all R.'); text(right, 250, 332, 'Only a global bound permits the limit R→∞.', { 'text-anchor': 'middle' });
      } else {
        const left = setup(0, 'Semicircle, poles and signed closure'), project = axes(left, d.R * 1.2); line(left, d.curve.map(project), COLORS.teal, { 'data-complex-arc': d.halfPlane }); line(left, [project(complex(-d.R)), project(complex(d.R))], COLORS.blue); d.poles.forEach(p => mark(left, project(p.z), p.enclosed ? COLORS.coral : COLORS.grid)); text(left, 18, 53, 'Real −R→R; arc R→−R; ' + (d.orientation > 0 ? 'CCW' : 'CW') + '.');
        const right = setup(1, 'Exponential magnitude along the arc'), logs = d.samples.map(p => [p.theta / PI, p.expLogAbs]); numericPlot(right, [logs], [0, 1], [Math.min(-1, ...logs.map(p => p[1])), Math.max(1, ...logs.map(p => p[1]))], ['arc-log-exponential']); text(right, 18, 53, 'ln |exp(ikz)|=−k Im z; Jordan ' + (d.certificate ? 'certified' : 'uncertified')); text(right, 250, 332, 'Horizontal θ/π; vertical natural log magnitude.', { 'text-anchor': 'middle' });
      }
    }
    root.setModelState = (values, announce = false, fromShared = false) => {
      model = build({ ...model.state, ...values }); refresh(announce, !fromShared); return model.state;
    };
    stateBus?.join(stateKey, root, values => root.setModelState(values, false, true));
    refresh(false); return root;
  }
  const api = Object.freeze({ initial, controls, normalize, complex, add, sub, scale, mul, div, abs, pow, polar, formatComplex, evaluate, circlePoints, quotient, contourPoles,
    directionalModel, contourModel, taylorModel, polynomialExterior, proofSteps, liouvilleModel, meanModel, arcFactor, jordanModel, build, render });
  if (typeof window !== 'undefined') window.PrimerMathComplexLab = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
}());
