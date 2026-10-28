/* Source-coordinate algebra graphs in a rotatable chart plane.
 * Algebra state belongs to the linked workbench; the camera changes only view.
 */
(function (host) {
  'use strict';
  const copy = value => JSON.parse(JSON.stringify(value));
  const IDS = ['math.3.linear', 'math.3.slope', 'math.3.quadratics', 'math.3.polynomials'];
  const TITLES = ['Equivalent equations and their intersections', 'Lines, signed rise and run', 'Quadratic vertices and real intercepts', 'Polynomial values and exact identities'];
  const MAX_LEAVES = 32768, MAX_DEPTH = 64;
  function core() {
    const value = host ? host.PrimerAlgebraFunctionsCore : require('./algebra-functions-core.js');
    if (!value) throw new Error('Algebra function core is unavailable');
    return value;
  }
  function numeric(value) {
    const n = typeof value === 'number' ? value : core().number(value);
    if (!Number.isFinite(n)) throw new TypeError('A graph coordinate must be finite');
    return Object.is(n, -0) ? 0 : n;
  }
  function pair(value) {
    if (!Array.isArray(value) || value.length !== 2) throw new TypeError('A graph point must have two coordinates');
    return value.map(numeric);
  }
  function validateBounds(bounds) {
    const values = ['xmin', 'xmax', 'ymin', 'ymax'].map(key => bounds?.[key]);
    if (!values.every(v => typeof v === 'number' && Number.isFinite(v)) || values[0] >= values[1] || values[2] >= values[3]) throw new TypeError('Graph bounds need finite, increasing x and y intervals');
    if (!Number.isFinite(values[1] - values[0]) || !Number.isFinite(values[3] - values[2])) throw new RangeError('Graph window exceeds finite display range');
    return { xmin: values[0], xmax: values[1], ymin: values[2], ymax: values[3] };
  }
  function contains(p, b) { return p[0] >= b.xmin && p[0] <= b.xmax && p[1] >= b.ymin && p[1] <= b.ymax; }
  function clipSegment(from, to, b) {
    const dx = to[0] - from[0], dy = to[1] - from[1]; let t0 = 0, t1 = 1;
    for (const [p, q] of [[-dx, from[0] - b.xmin], [dx, b.xmax - from[0]], [-dy, from[1] - b.ymin], [dy, b.ymax - from[1]]]) {
      if (p === 0) { if (q < 0) return null; continue; }
      const r = q / p;
      if (p < 0) { if (r > t1) return null; t0 = Math.max(t0, r); }
      else { if (r < t0) return null; t1 = Math.min(t1, r); }
    }
    const at = t => [from[0] + t * dx, from[1] + t * dy];
    const trimRoundoff = p => [Math.max(b.xmin, Math.min(b.xmax, p[0])), Math.max(b.ymin, Math.min(b.ymax, p[1]))];
    return { from: trimRoundoff(at(t0)), to: trimRoundoff(at(t1)), t: [t0, t1], clipped: t0 !== 0 || t1 !== 1 };
  }
  function autoBounds(graph) {
    const points = [[0, 0]];
    for (const p of graph.points || []) points.push([numeric(p.x), numeric(p.y)]);
    for (const s of graph.segments || []) points.push(pair(s.from), pair(s.to));
    for (const l of graph.lines || []) {
      const [A, B, C] = [l.A, l.B, l.C].map(numeric), denominator = A * A + B * B;
      if (denominator > 0 && Number.isFinite(denominator)) points.push([A * C / denominator, B * C / denominator]);
    }
    // Modest local values supply context when there are no intercept/vertex markers.
    // Do not use endpoint growth to erase all the root neighbourhoods from view.
    if (!graph.points?.length) for (const c of graph.curves || []) {
      const coefficients = c.coefficients.map(sourceRational);
      for (const x of [-1, 0, 1]) points.push([x, toDouble(bernstein(coefficients, x, x)[0]).value]);
    }
    const extent = Math.max(6, ...points.flat().map(v => Math.abs(v) * 1.2));
    if (!Number.isFinite(extent) || extent <= 0) throw new RangeError('Cannot construct a finite graph window');
    return { xmin: -extent, xmax: extent, ymin: -extent, ymax: extent };
  }
  function lineInWindow(line, bounds) {
    const [A, B, C] = [line.A, line.B, line.C].map(numeric), points = [];
    const result = { id: line.id, label: line.label, A, B, C, status: 'line', segment: null };
    const [ar, br, cr] = [line.A, line.B, line.C].map(sourceRational);
    if (!ar[0] && !br[0]) { result.status = cr[0] ? 'empty' : 'all-plane'; return result; }
    const [xmin, xmax, ymin, ymax] = [bounds.xmin, bounds.xmax, bounds.ymin, bounds.ymax].map(fromDouble);
    const compare = (a, b) => a[0] * b[1] - b[0] * a[1];
    function add(x, y) {
      if (compare(x, xmin) < 0n || compare(x, xmax) > 0n || compare(y, ymin) < 0n || compare(y, ymax) > 0n) return;
      if (!points.some(p => compare(p[0], x) === 0n && compare(p[1], y) === 0n)) points.push([x, y]);
    }
    if (br[0]) for (const x of [xmin, xmax]) add(x, rdiv(rsub(cr, rmul(ar, x)), br));
    if (ar[0]) for (const y of [ymin, ymax]) add(rdiv(rsub(cr, rmul(br, y)), ar), y);
    if (!points.length) return result;
    // At most two unique intersections exist for a line and a rectangle;
    // an exact corner contact intentionally returns the same endpoint twice.
    const endpoints = points.length === 1 ? [points[0], points[0]] : [points[0], points[1]];
    result.segment = endpoints.map(p => p.map((v, axis) => {
      const value = toDouble(v).value;
      return Math.max(axis ? bounds.ymin : bounds.xmin, Math.min(axis ? bounds.ymax : bounds.xmax, value));
    }));
    result.exactSegment = endpoints.map(p => p.map(v => ({ n: v[0].toString(), d: v[1].toString() })));
    result.endpointRoundoffBounds = endpoints.map((p, i) => p.map((v, axis) => {
      const residual = toDouble(rsub(v, fromDouble(result.segment[i][axis])));
      return nextFloat(Math.abs(residual.value) + residual.error, 1);
    }));
    return result;
  }
  // Exact rational Bernstein coefficients keep high-degree repeated-root plots
  // stable even when their expanded coefficients almost cancel in floating Horner.
  function gcdBig(a, b) { a = a < 0n ? -a : a; while (b) { const r = a % b; a = b; b = r; } return a; }
  function rat(n, d = 1n) {
    if (!d) throw new RangeError('Zero display denominator');
    if (d < 0n) { n = -n; d = -d; }
    if (!n) return [0n, 1n];
    const g = gcdBig(n, d); return [n / g, d / g];
  }
  const radd = (a, b) => rat(a[0] * b[1] + b[0] * a[1], a[1] * b[1]);
  const rsub = (a, b) => rat(a[0] * b[1] - b[0] * a[1], a[1] * b[1]);
  const rmul = (a, b) => rat(a[0] * b[0], a[1] * b[1]);
  const rdiv = (a, b) => rat(a[0] * b[1], a[1] * b[0]);
  function fromDouble(value) {
    if (!Number.isFinite(value)) throw new TypeError('A graph coefficient must be finite');
    if (!value) return [0n, 1n];
    const view = new DataView(new ArrayBuffer(8)); view.setFloat64(0, value, false);
    const bits = view.getBigUint64(0, false), exponentBits = Number((bits >> 52n) & 2047n);
    let n = bits & ((1n << 52n) - 1n); if (exponentBits) n += 1n << 52n;
    if (bits >> 63n) n = -n;
    const exponent = exponentBits ? exponentBits - 1023 - 52 : -1022 - 52;
    return exponent >= 0 ? rat(n << BigInt(exponent)) : rat(n, 1n << BigInt(-exponent));
  }
  function sourceRational(value) {
    if (typeof value === 'number') return fromDouble(value);
    if (!value || !Number.isSafeInteger(value.n) || !Number.isSafeInteger(value.d) || value.d <= 0) throw new TypeError('Expected an exact graph coefficient');
    return rat(BigInt(value.n), BigInt(value.d));
  }
  function nextFloat(value, direction) {
    if (value === Infinity || value === -Infinity) return value;
    if (!value) return direction * Number.MIN_VALUE;
    const data = new DataView(new ArrayBuffer(8)); data.setFloat64(0, value, false);
    let bits = data.getBigUint64(0, false); bits += (value > 0) === (direction > 0) ? 1n : -1n;
    data.setBigUint64(0, bits, false); return data.getFloat64(0, false);
  }
  function approximateRatio(value) {
    if (!value[0]) return 0;
    const negative = value[0] < 0n, n = negative ? -value[0] : value[0], d = value[1];
    const nb = n.toString(2).length, db = d.toString(2).length, ns = Math.max(0, nb - 54), ds = Math.max(0, db - 54);
    const result = (negative ? -1 : 1) * Number(n >> BigInt(ns)) / Number(d >> BigInt(ds)) * 2 ** (ns - ds);
    if (!Number.isFinite(result)) throw new RangeError('Exact polynomial value exceeds finite display range');
    return result;
  }
  function toDouble(value) {
    const result = approximateRatio(value), difference = rsub(value, fromDouble(result));
    if (!difference[0]) return { value: result, error: 0 };
    const error = Math.abs(approximateRatio(difference));
    return { value: result, error: nextFloat(error * (1 + 16 * Number.EPSILON) + 8 * Number.MIN_VALUE, 1) };
  }
  function choose(n, k) { let out = 1; for (let i = 1; i <= k; i++) out = out * (n + 1 - i) / i; return BigInt(Math.round(out)); }
  function bernstein(coefficients, a, b) {
    const degree = coefficients.length - 1, ar = fromDouble(a), h = rsub(fromDouble(b), ar);
    const ap = [[1n, 1n]], hp = [[1n, 1n]];
    for (let i = 1; i <= degree; i++) { ap.push(rmul(ap[i - 1], ar)); hp.push(rmul(hp[i - 1], h)); }
    const powers = [];
    for (let j = 0; j <= degree; j++) {
      let sum = [0n, 1n];
      for (let k = j; k <= degree; k++) sum = radd(sum, rmul(rmul(coefficients[k], [choose(k, j), 1n]), ap[k - j]));
      powers.push(rmul(sum, hp[j]));
    }
    const net = [];
    for (let i = 0; i <= degree; i++) {
      let sum = [0n, 1n];
      for (let j = 0; j <= i; j++) sum = radd(sum, rmul(powers[j], [choose(i, j), choose(degree, j)]));
      net.push(sum);
    }
    return net;
  }
  function curveInWindow(curve, bounds, tolerance, knots) {
    const sourceCoefficients = curve.coefficients.map(sourceRational), coefficients = curve.coefficients.map(numeric), degree = coefficients.length - 1;
    if (!coefficients.length || coefficients.length > 17) throw new RangeError('Unsupported polynomial graph degree');
    const segments = [], omittedIntervals = []; let leaves = 0, maxChordError = 0;
    const yminExact = fromDouble(bounds.ymin), ymaxExact = fromDouble(bounds.ymax), compare = (a, b) => a[0] * b[1] - b[0] * a[1];
    const serialRational = v => ({ n: v[0].toString(), d: v[1].toString() });
    function visit(a, b, depth) {
      const net = bernstein(sourceCoefficients, a, b), values = net.map(toDouble);
      const minimum = net.reduce((a, b) => compare(a, b) <= 0n ? a : b), maximum = net.reduce((a, b) => compare(a, b) >= 0n ? a : b);
      const exactYRange = [serialRational(minimum), serialRational(maximum)];
      const yRange = [Math.min(...values.map(v => nextFloat(v.value - v.error, -1))), Math.max(...values.map(v => nextFloat(v.value + v.error, 1)))];
      if (compare(maximum, yminExact) < 0n || compare(minimum, ymaxExact) > 0n) {
        if (++leaves > MAX_LEAVES) throw new RangeError('Graph sampling budget exceeded; narrow the graph window');
        omittedIntervals.push({ fromX: a, toX: b, yRange, exactYRange, reason: 'Bernstein hull is outside the y window' }); return;
      }
      let errorBound = 0;
      if (degree > 0) for (let i = 0; i <= degree; i++) {
        const chord = radd(net[0], rmul(rsub(net[degree], net[0]), [BigInt(i), BigInt(degree)]));
        const error = toDouble(rsub(net[i], chord)); errorBound = Math.max(errorBound, nextFloat(Math.abs(error.value) + error.error, 1));
      }
      const endpointRoundoffBound = Math.max(values[0].error, values[degree].error);
      errorBound = nextFloat(errorBound + endpointRoundoffBound, 1);
      if (errorBound > tolerance) {
        const midpoint = (a + b) / 2;
        if (depth >= MAX_DEPTH || midpoint === a || midpoint === b) throw new RangeError('Graph tolerance cannot be reached in this window');
        visit(a, midpoint, depth + 1); visit(midpoint, b, depth + 1); return;
      }
      const sourceFrom = [a, values[0].value], sourceTo = [b, values[degree].value], clipped = clipSegment(sourceFrom, sourceTo, bounds);
      // A chord outside the frame does not prove that the curve is outside:
      // a small extremum may still enter the window between its endpoints.
      if (!clipped) {
        const midpoint = (a + b) / 2;
        if (depth < MAX_DEPTH && midpoint !== a && midpoint !== b) { visit(a, midpoint, depth + 1); visit(midpoint, b, depth + 1); return; }
      }
      let clippingRoundoffBound = 0;
      if (clipped) {
        for (const point of [clipped.from, clipped.to]) {
          point[0] = Math.max(a, Math.min(b, point[0]));
          const t = rdiv(rsub(fromDouble(point[0]), fromDouble(a)), rsub(fromDouble(b), fromDouble(a)));
          const chord = radd(fromDouble(sourceFrom[1]), rmul(rsub(fromDouble(sourceTo[1]), fromDouble(sourceFrom[1])), t));
          const residual = toDouble(rsub(chord, fromDouble(point[1])));
          clippingRoundoffBound = Math.max(clippingRoundoffBound, nextFloat(Math.abs(residual.value) + residual.error, 1));
        }
        const totalError = nextFloat(errorBound + clippingRoundoffBound, 1);
        if (totalError > tolerance) {
          const midpoint = (a + b) / 2;
          if (clippingRoundoffBound >= tolerance || depth >= MAX_DEPTH || midpoint === a || midpoint === b) throw new RangeError('Curve clipping cannot resolve this focus window. Increase its radius.');
          visit(a, midpoint, depth + 1); visit(midpoint, b, depth + 1); return;
        }
        errorBound = totalError;
      }
      if (++leaves > MAX_LEAVES) throw new RangeError('Graph sampling budget exceeded; narrow the graph window');
      maxChordError = Math.max(maxChordError, errorBound);
      if (clipped) segments.push({ ...clipped, sourceInterval: [a, b], sourceFrom, sourceTo, chordErrorBound: errorBound, endpointRoundoffBound, clippingRoundoffBound });
      else omittedIntervals.push({ fromX: a, toX: b, yRange, exactYRange, reason: 'boundary unresolved at floating coordinate resolution', resolutionLimited: true, chordErrorBound: errorBound });
    }
    const splits = [...new Set([bounds.xmin, bounds.xmax, 0, ...knots].filter(x => x >= bounds.xmin && x <= bounds.xmax))].sort((a, b) => a - b);
    for (let i = 1; i < splits.length; i++) visit(splits[i - 1], splits[i], 0);
    const paths = [];
    for (const s of segments) {
      const last = paths.at(-1), end = last?.at(-1);
      if (end && end[0] === s.from[0] && end[1] === s.from[1]) last.push(s.to);
      else paths.push([s.from, s.to]);
    }
    const boundaryUncertain = omittedIntervals.some(v => v.resolutionLimited);
    return { id: curve.id, label: curve.label, coefficients, paths, segments, omittedIntervals, boundaryUncertain, maxChordError, leaves, status: segments.length ? 'visible' : boundaryUncertain ? 'boundary-uncertain' : 'outside-window', errorMethod: 'exact-rational Bernstein convex hull plus endpoint conversion roundoff' };
  }
  function scene(model, options = {}) {
    if (!model || !IDS.includes(model.lessonId) || !model.graph) throw new TypeError('Expected one of the four authored algebra graph models');
    const graph = model.graph, bounds = validateBounds(options.bounds || autoBounds(graph));
    const width = bounds.xmax - bounds.xmin, height = bounds.ymax - bounds.ymin;
    const gain = 6 / Math.max(width, height), tolerance = options.tolerance ?? Math.max(width, height) / 4096;
    if (!Number.isFinite(tolerance) || tolerance <= 0 || tolerance > Math.max(width, height) / 64) throw new RangeError('Graph tolerance must be positive and no coarser than one sixty-fourth of the window');
    const points = (graph.points || []).map((p, i) => ({ ...p, x: numeric(p.x), y: numeric(p.y), xText: typeof p.x === 'number' ? String(p.x) : core().text(p.x), yText: typeof p.y === 'number' ? String(p.y) : core().text(p.y), exact: p.exact !== false, marker: 'M' + (i + 1), visible: contains([numeric(p.x), numeric(p.y)], bounds) }));
    const segments = (graph.segments || []).map(s => {
      const sourceFrom = pair(s.from), sourceTo = pair(s.to), clipped = clipSegment(sourceFrom, sourceTo, bounds);
      return { ...s, sourceFrom, sourceTo, from: clipped?.from || sourceFrom, to: clipped?.to || sourceTo, clipped: clipped?.clipped || false, visible: Boolean(clipped) };
    });
    const curves = (graph.curves || []).map(c => curveInWindow(c, bounds, tolerance, points.map(p => p.x)));
    const lines = (graph.lines || []).map(l => lineInWindow(l, bounds));
    const axes = [];
    if (bounds.ymin <= 0 && bounds.ymax >= 0) axes.push({ axis: 'x', from: [bounds.xmin, 0], to: [bounds.xmax, 0] });
    if (bounds.xmin <= 0 && bounds.xmax >= 0) axes.push({ axis: 'y', from: [0, bounds.ymin], to: [0, bounds.ymax] });
    const markerGroups = [];
    for (const point of points) if (point.visible) {
      let group = markerGroups.find(g => g.x === point.x && g.y === point.y);
      if (!group) { group = { x: point.x, y: point.y, pointIds: [], markers: [], exact: true }; markerGroups.push(group); }
      group.pointIds.push(point.id); group.markers.push(point.marker); group.exact = group.exact && point.exact;
    }
    for (const group of markerGroups) group.label = group.markers.join('/');
    const maxChordError = Math.max(0, ...curves.map(c => c.maxChordError));
    return { lessonId: model.lessonId, state: model.state, bounds, transform: { gain, center: [(bounds.xmin + bounds.xmax) / 2, (bounds.ymin + bounds.ymax) / 2], planeZ: 0 }, curves, lines, points, markerGroups, segments, axes, maxChordError, tolerance,
      note: 'This finite coordinate window clips infinite lines and polynomial graphs. The x and y axes have equal coordinate scale in the mathematical plane. Oblique camera projection can change apparent angles; judge perpendicularity in the 2D graph or exact equations. Curves are piecewise-linear approximations certified by exact-rational Bernstein hulls and a stated vertical chord-error bound; markers retain the exact or approximate status supplied by the algebra core. The chart occupies z = 0; rotating it does not introduce a third algebra variable.' };
  }
  function algebraState(raw = {}) {
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw new TypeError('Expected a mathematical state object');
    const state = copy(raw); delete state.chartFocus; delete state.chartRadius; return state;
  }
  function viewState(model, raw = {}) {
    if (!model?.graph || !raw || typeof raw !== 'object' || Array.isArray(raw)) throw new TypeError('Expected a graph and display state');
    const chartFocus = Object.hasOwn(raw, 'chartFocus') ? raw.chartFocus : 'overview';
    const value = Object.hasOwn(raw, 'chartRadius') ? raw.chartRadius : 6;
    const chartRadius = (typeof value === 'number' || typeof value === 'string' && value.trim()) ? Number(value) : NaN;
    if (!Number.isFinite(chartRadius) || chartRadius < 1e-12 || chartRadius > 1e12) throw new RangeError('Chart radius must be a finite number from 1e-12 to 1e12');
    if (typeof chartFocus !== 'string' || (chartFocus !== 'overview' && (model.graph.points || []).filter(p => p.id === chartFocus).length !== 1)) throw new RangeError('Choose Overview or a special point in the current graph');
    const view = { chartFocus, chartRadius };
    if (chartFocus !== 'overview') focusedBounds(model, view);
    return view;
  }
  function focusedBounds(model, view) {
    const point = model.graph.points.find(p => p.id === view.chartFocus);
    if (!point) throw new RangeError('The selected focus point is absent from this graph');
    const [x, y] = [point.x, point.y].map(numeric), r = view.chartRadius;
    const bounds = { xmin: x - r, xmax: x + r, ymin: y - r, ymax: y + r };
    if (!Object.values(bounds).every(Number.isFinite) || !(bounds.xmin < x && x < bounds.xmax && bounds.ymin < y && y < bounds.ymax)) throw new RangeError('This focus radius is below reliable coordinate resolution here. Increase the radius.');
    // If float spacing consumes a visible part of the requested window, refuse
    // it instead of silently substituting a wider radius or collapsing an axis.
    const widths = [x - bounds.xmin, bounds.xmax - x, y - bounds.ymin, bounds.ymax - y];
    if (widths.some(w => w <= 0 || Math.abs(w - r) > r / 4096)) throw new RangeError('This focus radius is below reliable coordinate resolution here. Increase the radius.');
    return bounds;
  }
  function viewOptions(model, raw = {}) {
    const view = viewState(model, raw);
    return view.chartFocus === 'overview' ? {} : { bounds: focusedBounds(model, view) };
  }
  function sceneForState(model, raw = {}) {
    const view = viewState(model, raw), result = scene(model, viewOptions(model, view));
    result.view = view;
    if (view.chartFocus !== 'overview') {
      const point = model.graph.points.find(p => p.id === view.chartFocus);
      result.focus = { pointId: point.id, label: point.label, x: numeric(point.x), y: numeric(point.y), exact: point.exact !== false };
      result.transform.center = [result.focus.x, result.focus.y];
    }
    return result;
  }
  const fmt = x => Number(x.toPrecision(7)).toString();
  function buildFromModel(model, g, options = {}) {
    if (options.view && (options.bounds || options.tolerance)) throw new TypeError('Use a focused view or explicit bounds, not both');
    const s = options.view ? sceneForState(model, options.view) : scene(model, options), { gain, center } = s.transform;
    const world = p => [(p[0] - center[0]) * gain, (p[1] - center[1]) * gain, 0];
    const b = s.bounds, corners = [[b.xmin, b.ymin], [b.xmax, b.ymin], [b.xmax, b.ymax], [b.xmin, b.ymax]];
    for (let i = 0; i < 4; i++) g.line([world(corners[i]), world(corners[(i + 1) % 4])], '#b9c8c4', { algebra_kind: 'frame', width: .8 });
    for (const a of s.axes) g.line([world(a.from), world(a.to)], g.colors.ink, { algebra_kind: 'axis', axis: a.axis, width: 1.2 });
    const offsetX = Boolean(s.focus) || fmt(b.xmin) === fmt(b.xmax), offsetY = Boolean(s.focus) || fmt(b.ymin) === fmt(b.ymax);
    g.label(world([b.xmax, b.ymin]), (offsetX ? 'Δx: ' : 'x: ') + fmt(b.xmin - (offsetX ? center[0] : 0)) + '…' + fmt(b.xmax - (offsetX ? center[0] : 0)));
    g.label(world([b.xmin, b.ymax]), (offsetY ? 'Δy: ' : 'y: ') + fmt(b.ymin - (offsetY ? center[1] : 0)) + '…' + fmt(b.ymax - (offsetY ? center[1] : 0)));
    const colors = [g.colors.blue, g.colors.coral, g.colors.plum, g.colors.green, g.colors.gold];
    s.curves.forEach((c, i) => c.paths.forEach(path => g.line(path.map(world), colors[i % colors.length], { algebra_kind: 'curve', curveId: c.id, width: 2.2 })));
    s.lines.forEach((l, i) => {
      if (l.status === 'all-plane') g.polygon(corners.map(world), colors[(s.curves.length + i) % colors.length], { algebra_kind: 'solution-plane', lineId: l.id, opacity: .1, stroke: false });
      if (l.segment) g.line(l.segment.map(world), colors[(s.curves.length + i) % colors.length], { algebra_kind: 'line', lineId: l.id, width: 2.2 });
    });
    for (const segment of s.segments) if (segment.visible) g.line([world(segment.from), world(segment.to)], g.colors.teal, { algebra_kind: 'construction', segmentId: segment.id, width: 1.8 });
    for (const group of s.markerGroups) {
      const p = world([group.x, group.y]);
      g.sphere(p, .045, group.exact ? g.colors.gold : g.colors.coral, { algebra_kind: 'marker', pointId: group.pointIds[0], pointIds: group.pointIds, marker: group.label, exact: group.exact });
      g.label([p[0], p[1] + .15, p[2]], group.label);
    }
    const markers = s.points.map(p => p.marker + ': ' + p.label + ' (' + p.xText + ', ' + p.yText + ')' + (p.exact ? '' : ' approximately') + (p.visible ? '' : ' — outside this window')).join('; ');
    const hidden = s.curves.filter(c => c.status === 'outside-window').map(c => c.label).concat(s.lines.filter(l => l.status === 'line' && !l.segment).map(l => l.label));
    const uncertain = s.curves.filter(c => c.boundaryUncertain).map(c => c.label);
    const descriptions = [...s.curves, ...s.lines].map((c, i) => ({ label: c.label + (c.status === 'empty' ? ' (no points)' : c.status === 'all-plane' ? ' (every point)' : ''), color: colors[i % colors.length] }));
    return { state: { ...copy(model.state), ...(s.view || {}) }, readout: model.summary + ' ' + markers + (hidden.length ? ' Outside the displayed window: ' + hidden.join('; ') + '.' : '') + (uncertain.length ? ' Boundary visibility is unresolved at coordinate resolution for: ' + uncertain.join('; ') + '. Change the focus radius to inspect it.' : ''),
      note: s.note + (s.focus ? ' Focus: ' + s.focus.label + '; requested coordinate radius ' + s.view.chartRadius + (s.focus.exact ? '.' : '; the marker position is approximate.') : '') + (offsetX || offsetY ? ' Δ labels are offsets from x₀ = ' + String(center[0]) + ', y₀ = ' + String(center[1]) + '; add the stated centre to recover absolute coordinates.' : '') + ' Window: x ∈ [' + String(b.xmin) + ', ' + String(b.xmax) + '], y ∈ [' + String(b.ymin) + ', ' + String(b.ymax) + ']. Both coordinates use ' + gain.toPrecision(16) + ' world units per algebra unit. Maximum vertical chord-error bound (approximately): ' + s.maxChordError.toPrecision(6) + ' algebra units. Clipped boundary endpoints belong to the interpolating chords, not additional exact function samples. Coincident markers share one glyph while retaining every named mathematical point. Marker sizes identify locations and do not encode values. Algebra controls remain in the linked workbench; camera controls preserve its accepted state.',
      legend: [...descriptions, { label: 'Exact special points', color: g.colors.gold }, { label: 'Approximate irrational points', color: g.colors.coral }, { label: 'Signed constructions', color: g.colors.teal }], algebraFunctionsGeometry: s };
  }
  const families = {};
  for (let i = 0; i < IDS.length; i++) {
    const id = IDS[i];
    families[id] = { title: TITLES[i], requires: 'PrimerAlgebraFunctionsCore', linkedStateKey: id, camera: { yaw: -15, pitch: 12 },
      initialFactory: () => ({ ...core().defaults(id), chartFocus: 'overview', chartRadius: 6 }), controls: [], controlsFactory: () => [],
      normalize: raw => { const model = core().model(id, algebraState(raw)); return { ...copy(model.state), ...viewState(model, raw) }; },
      build: (state, g) => { const model = core().model(id, algebraState(state)); return buildFromModel(model, g, { view: viewState(model, state) }); } };
  }
  const api = Object.freeze({ scene, sceneForState, viewState, viewOptions, algebraState, buildFromModel, families, clipSegment, lineInWindow });
  if (host) { host.PrimerAlgebraFunctionsSpatial = api; host.PrimerAlgebraFunctionsSpatialFamilies = families; }
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window === 'undefined' ? null : window);
