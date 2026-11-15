/* Original differential-geometry artwork; analytic metrics and transport determine every readout. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg', PI = Math.PI, TAU = 2 * PI;
  let serial = 0;
  const C = { ink: '#263b46', paper: '#f5efdf', grid: '#d5cfbf', teal: '#317e78', coral: '#b96652', blue: '#3e7085', gold: '#9e741c' };
  const initial = Object.freeze({ surface: 'torus', radius: 1, major: 3, u: 30, v: 0, normal: 'outward', coverage: 100, direction: 'positive', leg: '0', progress: 50, startAngle: 0, vectorLength: 1 });
  const controls = Object.freeze([
    { key: 'surface', label: 'Surface', options: [['plane', 'Plane'], ['cylinder', 'Circular cylinder'], ['sphere', 'Round sphere'], ['torus', 'Standard embedded torus']] },
    { key: 'radius', label: 'Radius r (length units)', min: .5, max: 2, step: .25 },
    { key: 'major', label: 'Torus major radius R (length units)', min: 3, max: 6, step: .25 },
    { key: 'u', label: 'Coordinate u', min: -180, max: 180, step: 15 },
    { key: 'v', label: 'Coordinate v', min: -180, max: 180, step: 15 },
    { key: 'normal', label: 'Chosen unit normal', options: [['outward', 'Outward / plane +z'], ['inward', 'Reversed / plane −z']] },
    { key: 'coverage', label: 'Integral patch span (%)', min: 0, max: 100, step: 5 },
    { key: 'direction', label: 'Octant traversal', options: [['positive', 'A → B → C → A'], ['negative', 'A → C → B → A']] },
    { key: 'leg', label: 'Transport leg', options: [['0', 'First geodesic arc'], ['1', 'Second geodesic arc'], ['2', 'Third geodesic arc']] },
    { key: 'progress', label: 'Position on this arc (%)', min: 0, max: 100, step: 1 },
    { key: 'startAngle', label: 'Initial β in fixed (+Y,+Z) basis at A (degrees)', min: 0, max: 360, step: 15 },
    { key: 'vectorLength', label: 'Transported tangent length', min: 0, max: 2, step: .25 },
  ].map(c => Object.freeze({ ...c, options: c.options ? Object.freeze(c.options.map(([value, label]) => Object.freeze({ value, label }))) : undefined })));
  const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const multiply = (a, s) => a.map(v => v * s), norm = a => Math.hypot(...a);
  const degrees = angle => angle * PI / 180;
  const fmt = n => n === 0 ? '0' : Math.abs(n) < .0001 ? n.toExponential(5) : String(Number(n.toPrecision(6)));
  function trig(angle) {
    // Only represented exact quarter turns are symbolic zeros. A nearby point
    // remains nearby: no tolerance can collapse a regular chart onto a pole.
    const q = Math.round(angle / (PI / 2));
    if (Number.isSafeInteger(q) && angle === q * (PI / 2)) {
      const index = ((q % 4) + 4) % 4;
      return { c: [1, 0, -1, 0][index], s: [0, 1, 0, -1][index] };
    }
    return { c: Math.cos(angle), s: Math.sin(angle) };
  }
  function sineDifference(a, b) {
    if (a === b) return 0;
    const qa = Math.round(a / (PI / 2)), qb = Math.round(b / (PI / 2));
    if (Number.isSafeInteger(qa) && Number.isSafeInteger(qb) && a === qa * (PI / 2) && b === qb * (PI / 2)) return trig(b).s - trig(a).s;
    const half = (b - a) / 2, midpoint = a / 2 + b / 2;
    const q = Math.round(midpoint / (PI / 2));
    if (!Number.isSafeInteger(q)) return 2 * Math.cos(midpoint) * Math.sin(half);
    // Average distances from a known quarter turn before forming the midpoint.
    // This retains tiny pole-adjacent patches when the midpoint rounds to π/2.
    const base = q * (PI / 2), residual = ((a - base) + (b - base)) / 2, Q = trig(base);
    return 2 * (Q.c * Math.cos(residual) - Q.s * Math.sin(residual)) * trig(half).s;
  }
  function bounds(key, surface) {
    if (key === 'u' && surface === 'plane') return { min: -2, max: 2, step: .25 };
    if (key === 'v' && ['plane', 'cylinder'].includes(surface)) return { min: -2, max: 2, step: .25 };
    if (key === 'v' && surface === 'sphere') return { min: -90, max: 90, step: 15 };
    const c = controls.find(c => c.key === key); return { min: c.min, max: c.max, step: c.step };
  }
  function normalize(raw) {
    const input = raw && typeof raw === 'object' ? raw : {}, s = { surface: controls[0].options.some(o => o.value === input.surface) ? input.surface : initial.surface };
    for (const c of controls.slice(1)) {
      if (c.options) s[c.key] = c.options.some(o => o.value === input[c.key]) ? input[c.key] : initial[c.key];
      else { const b = bounds(c.key, s.surface), value = Number(input[c.key]), valid = ['number', 'string'].includes(typeof input[c.key]) && !(typeof input[c.key] === 'string' && !input[c.key].trim()) && Number.isFinite(value);
        const v = valid ? value : initial[c.key]; s[c.key] = b.min + Math.round((Math.max(b.min, Math.min(b.max, v)) - b.min) / b.step) * b.step; }
    }
    return s;
  }
  function validate(kind, p) {
    if (!['plane', 'cylinder', 'sphere', 'torus'].includes(kind) || !p || !['u', 'v', 'radius', 'major'].every(k => Number.isFinite(p[k])) || p.radius <= 0 || ![1, -1].includes(p.normalSign)) throw new RangeError('Known surface, finite coordinates, positive radius and normalSign ±1 required.');
    if (kind === 'torus' && p.major <= p.radius) throw new RangeError('A standard ring torus requires R > r > 0.');
    if (kind === 'sphere' && Math.abs(p.v) > PI / 2) throw new RangeError('Sphere latitude must be within [−π/2,π/2].');
  }
  function surfaceAt(kind, parameters) {
    const p = { ...parameters, normalSign: parameters?.normalSign ?? 1 }; validate(kind, p);
    const { u, v, radius: r, major: R, normalSign: sign } = p, U = trig(u), V = trig(v);
    let point, Xu, Xv, Xuu, Xuv, Xvv, outward, E, G, e, g, k1, k2, areaElement, K;
    if (kind === 'plane') {
      point = [u, v, 0]; Xu = [1, 0, 0]; Xv = [0, 1, 0]; Xuu = Xuv = Xvv = [0, 0, 0]; outward = [0, 0, 1]; E = G = areaElement = 1; e = g = k1 = k2 = K = 0;
    } else if (kind === 'cylinder') {
      point = [r * U.c, r * U.s, v]; Xu = [-r * U.s, r * U.c, 0]; Xv = [0, 0, 1]; Xuu = [-r * U.c, -r * U.s, 0]; Xuv = Xvv = [0, 0, 0]; outward = [U.c, U.s, 0]; E = r * r; G = 1; areaElement = r; e = -sign * r; g = 0; k1 = -sign / r; k2 = K = 0;
    } else if (kind === 'sphere') {
      outward = [V.c * U.c, V.c * U.s, V.s]; point = multiply(outward, r);
      Xu = [-r * V.c * U.s, r * V.c * U.c, 0]; Xv = [-r * V.s * U.c, -r * V.s * U.s, r * V.c];
      Xuu = [-r * V.c * U.c, -r * V.c * U.s, 0]; Xuv = [r * V.s * U.s, -r * V.s * U.c, 0]; Xvv = multiply(outward, -r);
      E = r * r * V.c * V.c; G = r * r; areaElement = r * r * V.c; e = -sign * r * V.c * V.c; g = -sign * r; k1 = k2 = -sign / r; K = 1 / (r * r);
    } else {
      const a = R + r * V.c; outward = [V.c * U.c, V.c * U.s, V.s]; point = [a * U.c, a * U.s, r * V.s];
      Xu = [-a * U.s, a * U.c, 0]; Xv = [-r * V.s * U.c, -r * V.s * U.s, r * V.c];
      Xuu = [-a * U.c, -a * U.s, 0]; Xuv = [r * V.s * U.s, -r * V.s * U.c, 0]; Xvv = multiply(outward, -r);
      E = a * a; G = r * r; areaElement = r * a; e = -sign * a * V.c; g = -sign * r; k1 = -sign * V.c / a; k2 = -sign / r; K = V.c / (r * a);
    }
    const regular = E > 0 && G > 0;
    return { kind, parameters: p, point, Xu, Xv, Xuu, Xuv, Xvv, normal: multiply(outward, sign), metric: { E, F: 0, G }, secondForm: { e, f: 0, g }, areaElement,
      principal: [k1, k2], gaussian: K, mean: (k1 + k2) / 2, regular, principalDirections: regular ? [multiply(Xu, 1 / Math.sqrt(E)), multiply(Xv, 1 / Math.sqrt(G))] : null };
  }
  function patchIntegral(kind, parameters, patch) {
    validate(kind, { ...parameters, u: 0, v: 0, normalSign: 1 });
    if (!patch || !['u0', 'u1', 'v0', 'v1'].every(k => Number.isFinite(patch[k])) || patch.u0 > patch.u1 || patch.v0 > patch.v1) throw new RangeError('Ordered finite patch bounds required.');
    if (kind !== 'plane' && patch.u1 - patch.u0 > TAU) throw new RangeError('An angular patch may not wrap more than once.');
    if (kind === 'sphere' && (patch.v0 < -PI / 2 || patch.v1 > PI / 2)) throw new RangeError('Sphere patch latitude bounds required.');
    if (kind === 'torus' && patch.v1 - patch.v0 > TAU) throw new RangeError('Torus tube interval may not wrap more than once.');
    const du = patch.u1 - patch.u0, dv = patch.v1 - patch.v0, ds = sineDifference(patch.v0, patch.v1), r = parameters.radius, R = parameters.major;
    const result = (area, curvatureIntegral, positive = Math.max(0, curvatureIntegral), negative = Math.min(0, curvatureIntegral)) => ({ area, curvatureIntegral, positive, negative, absolute: positive - negative });
    if (kind === 'plane') return result(du * dv, 0);
    if (kind === 'cylinder') return result(r * du * dv, 0);
    if (kind === 'sphere') return result(r * r * du * ds, du * ds);
    // The ring torus has K dA = cos(v) du dv. Split at actual zero rings
    // rather than treating its total as an unsigned curvature magnitude.
    const edges = [patch.v0];
    const first = Math.floor((patch.v0 - PI / 2) / PI) + 1;
    for (let j = first; PI / 2 + j * PI < patch.v1; j++) {
      const edge = PI / 2 + j * PI;
      if (edge <= edges[edges.length - 1]) break;
      edges.push(edge);
    }
    edges.push(patch.v1);
    let positive = 0, negative = 0;
    for (let j = 1; j < edges.length; j++) {
      const contribution = du * sineDifference(edges[j - 1], edges[j]);
      if (contribution > 0) positive += contribution; else negative += contribution;
    }
    return result(r * du * (R * dv + r * ds), du * ds, positive, negative);
  }
  function rotateAxis(vector, axis, angle) {
    const t = trig(angle), perpendicular = cross(axis, vector), parallel = dot(axis, vector);
    return vector.map((v, i) => v * t.c + perpendicular[i] * t.s + axis[i] * parallel * (1 - t.c));
  }
  function transportOctant(raw) {
    const s = normalize(raw), A = [1, 0, 0], B = [0, 1, 0], Cc = [0, 0, 1], vertices = s.direction === 'positive' ? [A, B, Cc, A] : [A, Cc, B, A], sign = s.normal === 'outward' ? 1 : -1;
    const beta = trig(degrees(s.startAngle)), initialVector = [0, s.vectorLength * beta.c, s.vectorLength * beta.s];
    let carried = initialVector.slice(); const legs = [];
    for (let i = 0; i < 3; i++) {
      const axis = cross(vertices[i], vertices[i + 1]), startVector = carried.slice(), endVector = rotateAxis(carried, axis, PI / 2);
      legs.push({ index: i, start: vertices[i], end: vertices[i + 1], axis, startVector, endVector,
        points: Array.from({ length: 33 }, (_, j) => multiply(rotateAxis(vertices[i], axis, PI * j / 64), s.radius)) }); carried = endVector;
    }
    const leg = legs[Number(s.leg)], angle = PI / 2 * s.progress / 100, unitPoint = rotateAxis(leg.start, leg.axis, angle), tangent = rotateAxis(leg.startVector, leg.axis, angle);
    const expected = (s.direction === 'positive' ? 1 : -1) * sign * PI / 2;
    const measured = s.vectorLength === 0 ? null : Math.atan2(dot(multiply(A, sign), cross(initialVector, carried)), dot(initialVector, carried));
    return { radius: s.radius, legs, unitPoint, point: multiply(unitPoint, s.radius), tangent, initialVector, finalVector: carried, measuredHolonomy: measured,
      expectedHolonomy: expected, octantArea: s.radius * s.radius * PI / 2, curvatureIntegral: PI / 2, signedCurvatureIntegral: expected,
      geodesicVelocity: multiply(cross(leg.axis, unitPoint), s.radius), vectorDerivative: cross(leg.axis, tangent), tangentLength: norm(tangent), progressAngle: angle };
  }
  function build(raw) {
    const state = normalize(raw), kind = state.surface, r = state.radius, fraction = state.coverage / 100;
    const u = kind === 'plane' ? state.u : degrees(state.u), v = ['sphere', 'torus'].includes(kind) ? degrees(state.v) : state.v;
    const p = { u, v, radius: r, major: state.major, normalSign: state.normal === 'outward' ? 1 : -1 }, local = surfaceAt(kind, p);
    const fullPatch = kind === 'plane' ? { u0: -r, u1: r, v0: -r, v1: r } : { u0: -PI, u1: PI, v0: kind === 'sphere' ? -PI / 2 : kind === 'torus' ? -PI : -r, v1: kind === 'sphere' ? PI / 2 : kind === 'torus' ? PI : r };
    const patch = { ...fullPatch, u1: fullPatch.u0 + (fullPatch.u1 - fullPatch.u0) * fraction }, integral = patchIntegral(kind, p, patch), fullIntegral = patchIntegral(kind, p, fullPatch);
    const transport = transportOctant(state), closed = kind === 'sphere' || kind === 'torus';
    const signed = { positive: integral.positive, negative: integral.negative, absolute: integral.absolute };
    const seam = kind === 'plane' ? 'This plane chart is regular and globally one-to-one on R².' : kind === 'sphere' && !local.regular ? 'At a pole, E and the longitude area Jacobian vanish. The sphere remains smooth and K=1/r²; this coordinate chart fails and its u direction is undefined.' : 'The angular seam identifies the same physical points and frames at −π and +π; it is not a physical hole. Periodic coordinates do not form a single one-to-one chart on the whole surface.';
    const proof = kind === 'cylinder' ? 'Unroll with s = r u and z = v: ds² + dz² is exactly the plane metric. The cylinder has one nonzero principal curvature but K=0. This is a local isometry; identifying the full circumference changes the global coordinate domain.' :
      kind === 'torus' ? 'For the standard embedded torus, ds² = (R+r cos v)² du² + r² dv², and K = cos v/[r(R+r cos v)]. K dA = cos v du dv. Positive outer curvature integrates to 4π; negative inner curvature integrates to −4π over the whole torus. Total zero is cancellation, not pointwise flatness. An abstract flat quotient torus has a different Euclidean metric and is not this embedded donut.' :
      kind === 'sphere' ? 'For the round sphere, ds² = r² cos² v du² + r² dv² and K = 1/r². Its total curvature is 4π even when r changes. The latitude chart degenerates at the poles; intrinsic curvature does not. A global chart on this compact surface would have compact image, whereas a nonempty open subset of R² is not compact.' :
        'The plane metric is du²+dv² and both principal curvatures vanish. Visible bending and intrinsic curvature must be distinguished using the induced metric, not the apparent shape in a projection.';
    const readout = kind + ': u = ' + fmt(u) + ', v = ' + fmt(v) + (kind === 'plane' ? ' in length units.' : ['sphere', 'torus'].includes(kind) ? ' in radians.' : '; u in radians, v in length units.') +
      ' Metric (E,F,G) = (' + [local.metric.E, 0, local.metric.G].map(fmt).join(', ') + '); dA coefficient = ' + fmt(local.areaElement) +
      '. With S = −Dn and second form n·X_ij, principal curvatures = ' + local.principal.map(fmt).join(', ') + ' per length; K = ' + fmt(local.gaussian) + ' per length squared.' +
      ' Selected patch area = ' + fmt(integral.area) + ' length squared; ∫patch K dA = ' + fmt(integral.curvatureIntegral) + ' radians; positive/negative contributions = ' + fmt(signed.positive) + ', ' + fmt(signed.negative) +
      '. ' + (closed ? 'Full closed-surface area = ' + fmt(fullIntegral.area) + '; total curvature = ' + (kind === 'sphere' ? '4π.' : '0, with +4π and −4π cancellation.') : 'The displayed plane/cylinder patch has boundary; no closed-surface Gauss–Bonnet claim is made for it.') +
      ' ' + seam + ' Octant transport: leg ' + (Number(state.leg) + 1) + ', position ' + state.progress + '%, tangent length = ' + fmt(transport.tangentLength) +
      '. Full-loop signed holonomy relative to the chosen normal = ' + (transport.expectedHolonomy > 0 ? '+' : '−') + 'π/2.' +
      (transport.measuredHolonomy === null ? ' The zero vector has no measurable direction or angle.' : ' Measured from the returned nonzero vector = ' + fmt(transport.measuredHolonomy) + ' radians.') +
      ' Octant area = πr²/2; |∫K dA| = π/2 independently of radius. Fractions of an arc parameterize position, not time.';
    return { state, local, patch, fullPatch, integral, fullIntegral, signed, closed, transport, seam, proof, readout };
  }
  function element(tag, attrs = {}, ...children) { const e = document.createElement(tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v))); children.forEach(c => { if (c != null) e.append(c.nodeType ? c : document.createTextNode(String(c))); }); return e; }
  function shape(tag, attrs = {}, text) { const e = document.createElementNS(NS, tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v))); if (text != null) e.textContent = String(text); return e; }
  function label(svg, x, y, text, attrs = {}) { svg.append(shape('text', { x, y, fill: C.ink, 'font-size': 12, ...attrs }, text)); }
  function line(svg, points, color, attrs = {}) { svg.append(shape('polyline', { points: points.map(p => p.slice(0, 2).join(',')).join(' '), fill: 'none', stroke: color, 'stroke-width': 1.5, ...attrs })); }
  function project(p, scale = 60) { const yaw = -PI / 6, pitch = PI / 7; return [220 + scale * (p[0] * Math.cos(yaw) - p[1] * Math.sin(yaw)), 187 - scale * (p[2] * Math.cos(pitch) + (p[0] * Math.sin(yaw) + p[1] * Math.cos(yaw)) * Math.sin(pitch)), p[0] * Math.sin(yaw) * Math.cos(pitch) + p[1] * Math.cos(yaw) * Math.cos(pitch) - p[2] * Math.sin(pitch)]; }
  function arrow(svg, a, b, color, attrs = {}) { line(svg, [a, b], color, { 'stroke-width': 2.3, ...attrs }); const dx = b[0] - a[0], dy = b[1] - a[1], length = Math.hypot(dx, dy); if (length < 1e-8) return; const x = dx / length, y = dy / length; line(svg, [[b[0] - 7 * x - 4 * y, b[1] - 7 * y + 4 * x], b, [b[0] - 7 * x + 4 * y, b[1] - 7 * y - 4 * x]], color); }
  function render(item, hooks) {
    if (item?.props?.scenario !== 'math.5.diffgeo.curvature-transport' || Object.keys(item.props).length !== 1 || (item.renderer && item.renderer !== 'math-curvature-lab')) return null;
    const uid = 'curvature-' + ++serial, title = item.title || 'Distances, bending and transported directions', instructions = item.instructions || 'Compare induced metrics and principal curvatures. Inspect signed torus curvature, then carry a tangent vector around a spherical octant without turning it at the corners.';
    const root = element('section', { class: 'card lesson-model math-curvature-lab', 'data-renderer': 'math-curvature-lab', 'aria-labelledby': uid + '-title' }), heading = element('div', { class: 'model-heading-row' }, element('h3', { id: uid + '-title' }, title));
    const area = element('div', { class: 'model-controls concept-controls' }), widgets = new Map(), panels = element('div', { class: 'curvature-panels' }), pictures = [];
    ['Surface and coordinate patch', 'Gaussian curvature', 'Parallel transport on the octant'].forEach(name => { const view = element('div', { class: 'curvature-viewport', tabindex: '0', role: 'region', 'aria-label': name + '; enlarge for detail' }), svg = shape('svg', { viewBox: '0 0 440 340', role: 'img', focusable: 'false' }); view.append(svg); panels.append(view); pictures.push(svg); });
    const summary = element('div', { class: 'curvature-summary' }), table = element('table', { class: 'curvature-ledger' }), tableView = element('div', { class: 'curvature-table-region', tabindex: '0', role: 'region', 'aria-label': 'Metric and curvature ledger; scroll horizontally' }, table);
    const readout = element('p', { class: 'model-readout' }), proof = element('p', { class: 'curvature-proof' }), seam = element('p', { class: 'curvature-seam' }), transportNote = element('p', { class: 'spatial-note' });
    const note = element('p', { class: 'spatial-note' }, 'Length units are arbitrary but consistent: principal curvature has inverse-length units, K inverse-length-squared units, and K dA is dimensionless. Our sign convention is S=−Dn, e=n·X_uu: a sphere with outward normal has two negative principal curvatures; reversing the normal changes both signs but leaves K and the metric unchanged. u is a length on the plane and an angle elsewhere; v is a length on plane/cylinder and an angle on sphere/torus. Numeric entries apply when leaving the field. The filled preview uses finite planar facets of the analytic parameterization; its area and curvature integrals come from exact formulas, not pixels or mesh sums. Orthographic screen angles are not intrinsic surface angles. Sphere poles and periodic seams are coordinate failures, not physical holes. The sphere transport is a separate example, present for every selected surface. Its signed angle uses the selected normal orientation; the path and Levi-Civita transport do not depend on an arbitrary change of normal. No finite plot proves Gauss–Bonnet for arbitrary deformations. These Euclidean surface examples do not model Lorentzian spacetime, Weyl curvature or gravitational tidal tensors.');
    const sources = element('p', {}, 'Primary references: ', element('a', { href: 'https://sites.science.oregonstate.edu/coursewikis/GDF/book/gdf/torus.html', target: '_blank', rel: 'noopener noreferrer' }, 'Oregon State: induced torus metric and curvature'), '; ', element('a', { href: 'https://sites.science.oregonstate.edu/coursewikis/GDF/book/gdf/geotri.html', target: '_blank', rel: 'noopener noreferrer' }, 'geodesic triangles'), '; ', element('a', { href: 'https://sites.science.oregonstate.edu/coursewikis/GDF/book/gdf/gaussbonnet.html', target: '_blank', rel: 'noopener noreferrer' }, 'closed-surface Gauss–Bonnet'));
    const live = element('p', { class: 'model-status', role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true' }); let model = build(initial), enlarged = false;
    for (const c of controls) { const id = uid + '-' + c.key, input = element(c.options ? 'select' : 'input', { id, 'data-curvature-control': c.key }); if (c.options) c.options.forEach(o => input.append(element('option', { value: o.value }, o.label))); else input.setAttribute('type', 'number'); input.addEventListener('change', () => { model = build({ ...model.state, [c.key]: input.value }); refresh(true); }); const name = element('span', {}, c.label), labelEl = element('label', { for: id, class: 'model-range-control' }, name, input); widgets.set(c.key, { input, label: labelEl, name }); area.append(labelEl); }
    const buttons = element('div', { class: 'model-button-row' });
    for (const [key, text, patch] of [['outer', 'Torus outer equator', { surface: 'torus', v: 0 }], ['inner', 'Torus inner equator', { surface: 'torus', v: 180 }], ['zero', 'Torus K = 0 ring', { surface: 'torus', v: 90 }], ['pole', 'Sphere pole: chart failure', { surface: 'sphere', v: 90 }], ['closed', 'Complete octant loop', { leg: '2', progress: 100 }], ['reset', 'Reset activity', initial]]) { const b = element('button', { type: 'button', class: 'btn ghost small', 'data-curvature-action': key }, text); b.addEventListener('click', () => { model = build({ ...model.state, ...patch }); if (key === 'reset') size(false); refresh(true); }); buttons.append(b); }
    const enlarge = element('button', { type: 'button', class: 'btn ghost small', 'aria-pressed': 'false', 'data-curvature-action': 'enlarge' }, 'Enlarge plots');
    function size(on) { enlarged = on; root.classList.toggle('is-enlarged', on); enlarge.setAttribute('aria-pressed', String(on)); enlarge.textContent = on ? 'Fit plots' : 'Enlarge plots'; }
    enlarge.addEventListener('click', () => size(!enlarged)); heading.append(enlarge);
    root.append(heading, element('p', { class: 'model-instructions' }, instructions), buttons, area, summary, panels, tableView, seam, readout, proof, transportNote, note, sources, live);
    if (hooks?.speakButton) heading.prepend(hooks.speakButton(() => title + '. ' + instructions + '. ' + readout.textContent + ' ' + proof.textContent + ' ' + transportNote.textContent + ' ' + note.textContent, 'Read this activity aloud'));
    function setup(i, name) { const svg = pictures[i]; svg.replaceChildren(shape('title', { id: uid + '-title-' + i }, name), shape('desc', { id: uid + '-desc-' + i }, model.readout), shape('rect', { x: 0, y: 0, width: 440, height: 340, rx: 10, fill: C.paper })); svg.setAttribute('aria-labelledby', uid + '-title-' + i); svg.setAttribute('aria-describedby', uid + '-desc-' + i); label(svg, 18, 27, name, { 'font-size': 17, 'font-weight': 600 }); return svg; }
    function drawSurface() {
      const svg = setup(0, 'Surface and selected coordinate patch'), m = model, p = m.local.parameters, kind = m.state.surface, bounds = m.patch, scale = kind === 'torus' ? 155 / (p.major + p.radius) : 140 / Math.max(2, p.radius * 1.4), faces = [];
      const nu = kind === 'plane' ? 6 : 24, nv = kind === 'plane' ? 6 : 12;
      if (m.integral.area > 0) for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
        const u0 = bounds.u0 + (bounds.u1 - bounds.u0) * i / nu, u1 = bounds.u0 + (bounds.u1 - bounds.u0) * (i + 1) / nu, v0 = bounds.v0 + (bounds.v1 - bounds.v0) * j / nv, v1 = bounds.v0 + (bounds.v1 - bounds.v0) * (j + 1) / nv;
        const vertices = [[u0, v0], [u1, v0], [u1, v1], [u0, v1]].map(([u, v]) => surfaceAt(kind, { ...p, u, v }).point), K = surfaceAt(kind, { ...p, u: (u0 + u1) / 2, v: (v0 + v1) / 2 }).gaussian;
        faces.push({ vertices, projected: vertices.map(v => project(v, scale)), K });
      }
      faces.sort((a, b) => a.projected.reduce((s, p) => s + p[2], 0) - b.projected.reduce((s, p) => s + p[2], 0)).forEach(face => svg.append(shape('polygon', { points: face.projected.map(p => p.slice(0, 2).join(',')).join(' '), fill: face.K > 0 ? C.teal : face.K < 0 ? C.coral : C.gold, 'fill-opacity': .35, stroke: C.grid, 'stroke-width': .5, 'data-curvature-face': 'patch' })));
      const q = project(m.local.point, scale); svg.append(shape('circle', { cx: q[0], cy: q[1], r: 4, fill: C.blue, 'data-curvature-point': 'local' }));
      const nEnd = m.local.point.map((v, i) => v + m.local.normal[i] * .45 * p.radius); arrow(svg, q, project(nEnd, scale), C.ink, { 'data-curvature-normal': 'chosen' });
      label(svg, 18, 52, 'Teal K>0 · coral K<0 · gold K=0 · blue point'); label(svg, 18, 319, 'Analytic surface, faceted preview; axes fit uniformly.'); label(svg, 18, 337, 'Patch span ' + m.state.coverage + '%; normal arrow is extrinsic.');
    }
    function drawK() {
      const svg = setup(1, 'Gaussian curvature across the surface'), m = model, kind = m.state.surface, p = m.local.parameters, lo = kind === 'sphere' ? -PI / 2 : -PI, hi = kind === 'sphere' ? PI / 2 : PI;
      const values = Array.from({ length: 121 }, (_, j) => { const v = lo + (hi - lo) * j / 120; return { v, K: surfaceAt(kind, { ...p, v: ['torus', 'sphere'].includes(kind) ? v : p.v }).gaussian }; });
      const extent = Math.max(.1, ...values.map(q => Math.abs(q.K))) * 1.1, X = v => 76 + 338 * (v - lo) / (hi - lo), Y = K => 170 - 100 * K / extent;
      for (let j = 0; j <= 4; j++) { const x = lo + (hi - lo) * j / 4, y = -extent + 2 * extent * j / 4; line(svg, [[X(x), 70], [X(x), 270]], C.grid, { 'stroke-width': 1 }); line(svg, [[76, Y(y)], [414, Y(y)]], y === 0 ? C.ink : C.grid, { 'stroke-width': 1 }); label(svg, X(x), 290, Math.round(x * 180 / PI), { 'text-anchor': 'middle', 'font-size': 10 }); label(svg, 69, Y(y) + 4, fmt(y), { 'text-anchor': 'end', 'font-size': 10 }); }
      line(svg, values.map(q => [X(q.v), Y(q.K)]), C.blue, { 'data-curvature-series': 'K' });
      if (['sphere', 'torus'].includes(kind)) svg.append(shape('circle', { cx: X(p.v), cy: Y(m.local.gaussian), r: 4, fill: C.coral }));
      label(svg, 18, 52, 'K (inverse length squared); vertical axis rescales.'); label(svg, 245, 315, ['sphere', 'torus'].includes(kind) ? 'Latitude / tube angle v (degrees)' : 'Angular comparison parameter (degrees)', { 'text-anchor': 'middle' }); label(svg, 18, 337, kind === 'torus' ? 'Exact zero rings at v = ±90°; total zero is cancellation.' : 'Plane/cylinder K=0; sphere K=1/r² at every point.', { 'font-size': 11 });
    }
    function drawTransport() {
      const svg = setup(2, 'Parallel transport around the octant'), t = model.transport, gain = .32, scale = 132 / Math.hypot(t.radius, gain * t.tangentLength);
      for (let j = 0; j < 12; j++) { const u = TAU * j / 12; line(svg, Array.from({ length: 33 }, (_, k) => { const v = -PI / 2 + PI * k / 32; return project([t.radius * Math.cos(v) * Math.cos(u), t.radius * Math.cos(v) * Math.sin(u), t.radius * Math.sin(v)], scale); }), C.grid, { 'stroke-width': .6 }); }
      t.legs.forEach(leg => line(svg, leg.points.map(p => project(p, scale)), C.gold, { 'stroke-width': 2.5, 'data-curvature-geodesic': leg.index }));
      [['A', [t.radius, 0, 0]], ['B', [0, t.radius, 0]], ['C', [0, 0, t.radius]]].forEach(([name, point]) => {
        const q = project(point, scale); label(svg, q[0] + 7, q[1] + 5, name, { 'font-weight': 600, 'data-curvature-vertex': name });
      });
      const at = project(t.point, scale); svg.append(shape('circle', { cx: at[0], cy: at[1], r: 4, fill: C.coral }));
      if (t.tangentLength > 0) arrow(svg, at, project(t.point.map((v, i) => v + gain * t.tangent[i]), scale), C.coral, { 'data-curvature-transported': 'current' });
      if (model.state.vectorLength > 0) { const a = [t.radius, 0, 0]; arrow(svg, project(a, scale), project(a.map((v, i) => v + gain * t.initialVector[i]), scale), C.blue); arrow(svg, project(a, scale), project(a.map((v, i) => v + gain * t.finalVector[i]), scale), C.teal); }
      label(svg, 18, 52, 'Blue initial · teal full-loop return · coral current'); label(svg, 18, 318, 'No manual turn at corners; tangent covariant derivative 0.'); label(svg, 18, 337, 'Closed-loop holonomy: ' + (t.expectedHolonomy > 0 ? '+' : '−') + '90°; screen angles differ.');
    }
    function refresh(announce) {
      const m = model, s = m.state; root.setAttribute('data-curvature-state', JSON.stringify(s));
      widgets.forEach(({ input, label: labelEl, name }, key) => { input.value = String(s[key]); if (key === 'major') { labelEl.hidden = s.surface !== 'torus'; input.disabled = labelEl.hidden; } if (!controls.find(c => c.key === key).options) { const b = bounds(key, s.surface); Object.entries(b).forEach(([k, v]) => input.setAttribute(k, v)); } if (key === 'u' || key === 'v') name.textContent = 'Coordinate ' + key + (key === 'u' ? s.surface === 'plane' ? ' (length)' : ' (degrees)' : ['plane', 'cylinder'].includes(s.surface) ? ' (length)' : ' (degrees)'); });
      widgets.get('radius').name.textContent = s.surface === 'plane' ? 'Patch half-span r (length units)' : s.surface === 'torus' ? 'Torus tube radius r (length units)' : (s.surface === 'sphere' ? 'Sphere' : 'Cylinder') + ' radius r (length units)';
      summary.replaceChildren(...[['Gaussian K', fmt(m.local.gaussian)], ['Principal κ₁', fmt(m.local.principal[0])], ['Principal κ₂', fmt(m.local.principal[1])], ['Patch ∫K dA', fmt(m.integral.curvatureIntegral)]].map(([name, value]) => element('p', {}, element('small', {}, name), element('strong', {}, value))));
      table.replaceChildren(element('caption', {}, 'Metric and shape operator in the stated chart'), element('thead', {}, element('tr', {}, ...['Quantity', 'Value', 'Meaning'].map(v => element('th', { scope: 'col' }, v)))), element('tbody', {}, ...[
        ['E, F, G', [m.local.metric.E, 0, m.local.metric.G].map(fmt).join(', '), 'ds² = E du² + 2F du dv + G dv²'],
        ['e, f, g', [m.local.secondForm.e, 0, m.local.secondForm.g].map(fmt).join(', '), m.local.regular ? 'II = n·X_ij; S = g⁻¹II = −Dn' : 'II = n·X_ij; the degenerate chart has no inverse metric'],
        ['Area coefficient', fmt(m.local.areaElement), 'dA = √(EG−F²) du dv'], ['κ₁, κ₂', m.local.principal.map(fmt).join(', '), 'Signed extrinsic curvatures; inverse length'], ['Gaussian K', fmt(m.local.gaussian), 'κ₁κ₂, independent of normal sign'], ['Patch area', fmt(m.integral.area), 'Actual length-squared measure'], ['Positive / negative ∫K', fmt(m.signed.positive) + ' / ' + fmt(m.signed.negative), 'Signed contributions, not an unsigned area'],
      ].map(([name, value, meaning]) => element('tr', {}, element('th', { scope: 'row' }, name), element('td', {}, value), element('td', {}, meaning)))));
      seam.textContent = m.seam; readout.textContent = m.readout; proof.textContent = m.proof;
      transportNote.textContent = 'The spherical octant has three geodesic quarter-circle edges and three right angles. Initial β uses the fixed (+Y,+Z) tangent basis at A=r(1,0,0); changing the normal keeps this physical vector unchanged. Tangent arrows have a fixed display gain; the camera fits the sphere and arrow endpoints uniformly. Along each edge, transport is the same ambient rotation as the radius vector; its vector derivative is purely normal, so the tangent covariant derivative vanishes. Corner vectors are carried unchanged into the next edge. The complete-loop angle is measured only after return to A in its oriented tangent plane. Partial-path directions at different points are not compared as a holonomy angle. Reversing traversal reverses signed holonomy; changing radius changes area and K separately while their integral stays π/2. A zero tangent vector is transported to zero and has no measured direction. This explicit example does not model arbitrary spacetime transport.';
      drawSurface(); drawK(); drawTransport(); if (announce) live.textContent = m.readout;
    }
    refresh(false); return root;
  }
  const api = Object.freeze({ initial, controls, bounds, normalize, surfaceAt, patchIntegral, rotateAxis, transportOctant, build, render });
  if (typeof window !== 'undefined') window.PrimerMathCurvatureLab = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
}());
