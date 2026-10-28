/* Exact coordinate constructions; display coordinates are derived from these fractions. */
(function (host) {
  'use strict';
  const arithmetic = () => host ? host.PrimerAlgebraFunctionsCore : require('./algebra-functions-core.js');
  const initial = { mode: 'plot', x: '-3', y: '2', dx: '4', dy: '-2', qx: '6', qy: '4', reflection: 'x-axis' };
  const modes = ['plot', 'translate', 'reflect', 'distance', 'rectangle'];
  const reflections = ['x-axis', 'y-axis', 'origin', 'diagonal'];
  const clone = value => JSON.parse(JSON.stringify(value));
  function freeze(value) {
    if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
    return value;
  }
  function accept(raw = {}) {
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw new TypeError('Supply a coordinate state.');
    for (const key of Object.keys(raw)) if (!Object.hasOwn(initial, key)) throw new RangeError('Unknown coordinate setting: ' + key);
    const state = { ...initial, ...raw }, c = arithmetic();
    if (!modes.includes(state.mode) || !reflections.includes(state.reflection)) throw new RangeError('Choose a supported coordinate construction.');
    for (const key of ['x', 'y', 'dx', 'dy', 'qx', 'qy']) {
      const r = c.rational(state[key]);
      if (Math.abs(c.number(r)) > 1000 || r.d > 1000) throw new RangeError('Coordinates and movements need magnitude at most 1000 and reduced denominator at most 1000.');
      state[key] = c.text(r);
    }
    return state;
  }
  function location(x, y) {
    const c = arithmetic(), a = c.rational(x).n, b = c.rational(y).n;
    return !a && !b ? 'origin' : !a ? 'y-axis' : !b ? 'x-axis' : 'Quadrant ' + (a > 0 ? b > 0 ? 'I' : 'IV' : b > 0 ? 'II' : 'III');
  }
  function model(raw = {}) {
    const c = arithmetic(), state = accept(raw), r = key => c.rational(state[key]);
    const neg = a => c.multiply(a, -1), abs = a => a.n < 0 ? neg(a) : a;
    const p = [r('x'), r('y')], origin = [c.rational(0), c.rational(0)], points = [], segments = [];
    const pairText = p => '(' + p.map(c.text).join(', ') + ')';
    const point = (id, label, p) => { points.push({ id, label, x: p[0], y: p[1], exact: true }); return p; };
    const segment = (id, from, to) => segments.push({ id, label: id, from, to });
    const path = (id, from, to) => { const elbow = [to[0], from[1]]; segment(id + '-horizontal', from, elbow); segment(id + '-vertical', elbow, to); };
    point('P', 'P', p);
    const result = { location: location(...p) };
    let readout = 'P = ' + pairText(p) + ': ' + result.location + '.', note = 'Read x first, then y. Both coordinates use the same unit. Axis points belong to no quadrant.';
    if (state.mode === 'plot') {
      path('ordered-pair', origin, p);
      const swapped = point('swapped', 'Coordinates exchanged', [p[1], p[0]]);
      readout += ' Exchanging their order gives ' + pairText(swapped) + '.';
      result.swapped = swapped;
      note += ' The horizontal-then-vertical path explains the ordered pair; its length is not generally the straight-line distance.';
    } else if (state.mode === 'translate') {
      const q = point('Q', 'Q after movement', [c.add(p[0], r('dx')), c.add(p[1], r('dy'))]);
      path('movement', p, q); result.destination = q; result.destinationLocation = location(...q);
      readout += ' Add (' + state.dx + ', ' + state.dy + ') to reach Q = ' + pairText(q) + ': ' + result.destinationLocation + '.';
      note += ' Horizontal movement changes only x; vertical movement changes only y. Zero movement leaves that coordinate unchanged.';
    } else if (state.mode === 'reflect') {
      const q = state.reflection === 'x-axis' ? [p[0], neg(p[1])] : state.reflection === 'y-axis' ? [neg(p[0]), p[1]] : state.reflection === 'origin' ? p.map(neg) : [p[1], p[0]];
      point('Q', 'Q after transformation', q); segment('point-to-image', p, q); result.destination = q; result.destinationLocation = location(...q);
      const name = state.reflection === 'origin' ? 'A half-turn about the origin' : 'Reflection across ' + (state.reflection === 'diagonal' ? 'y = x' : 'the ' + state.reflection);
      readout += ' ' + name + ' gives Q = ' + pairText(q) + ': ' + result.destinationLocation + '.';
      note += ' An origin half-turn reverses both coordinates; it is not a reflection across a line.';
    } else {
      const q = point('Q', 'Opposite point Q', [r('qx'), r('qy')]);
      const dx = c.subtract(q[0], p[0]), dy = c.subtract(q[1], p[1]), width = abs(dx), height = abs(dy);
      Object.assign(result, { dx, dy, width, height });
      if (state.mode === 'distance') {
        path('axis-path', p, q); segment('straight-distance', p, q);
        const squared = c.add(c.multiply(dx, dx), c.multiply(dy, dy));
        const nr = Math.round(Math.sqrt(squared.n)), dr = Math.round(Math.sqrt(squared.d));
        const exact = nr * nr === squared.n && dr * dr === squared.d;
        const distanceText = exact ? c.text(c.divide(nr, dr)) : '√(' + c.text(squared) + ')';
        Object.assign(result, { squaredDistance: squared, straightDistance: distanceText, straightDistanceApproximation: Math.sqrt(c.number(squared)), axisPathLength: c.add(width, height) });
        readout += ' Q = ' + pairText(q) + '. Signed changes: Δx = ' + c.text(dx) + ', Δy = ' + c.text(dy) + '. Straight-line distance = ' + distanceText + ' units; horizontal-plus-vertical path = ' + c.text(result.axisPathLength) + ' units.';
        note += ' Straight-line distance is √((Δx)² + (Δy)²). A horizontal or vertical pair has one zero change. Coincident points have distance zero.';
      } else {
        const corners = [p, [q[0], p[1]], q, [p[0], q[1]]];
        point('B', 'Corner B', corners[1]); point('D', 'Corner D', corners[3]);
        corners.forEach((v, i) => segment('rectangle-side-' + i, v, corners[(i + 1) % 4]));
        const degenerate = width.n === 0 || height.n === 0;
        Object.assign(result, { corners, degenerate, area: c.multiply(width, height), perimeter: degenerate ? null : c.multiply(2, c.add(width, height)) });
        readout += ' Opposite corner Q = ' + pairText(q) + '. Width = ' + c.text(width) + ', height = ' + c.text(height) + ' units; area = ' + c.text(result.area) + ' square units.';
        readout += degenerate ? ' The corners collapse to a segment or point, so this is not a rectangle with positive area; no rectangle perimeter is assigned.' : ' Perimeter = ' + c.text(result.perimeter) + ' units. Remaining corners: ' + pairText(corners[1]) + ' and ' + pairText(corners[3]) + '.';
        note += ' The rectangle sides are parallel to the axes. Opposite corners may be supplied in either order. Area counts square units; perimeter measures boundary length.';
      }
    }
    return freeze({ title: 'The coordinate plane', state, result, readout, note, graph: { points, segments, curves: [], lines: [] } });
  }
  const examples = [
    ['plate', 'Left three, up two', { x: '-3', y: '2' }, [0]],
    ['x-axis', 'A point on the x-axis', { x: '5', y: '0' }, [1]],
    ['fourth-corner', 'Find a fourth corner', { mode: 'rectangle', x: '2', y: '1', qx: '6', qy: '4' }, [2]],
    ['left-down', 'Move left and down', { mode: 'translate', x: '3', y: '5', dx: '-4', dy: '-2' }, [3]],
    ['area', 'Area and perimeter', { mode: 'rectangle', x: '1', y: '1', qx: '7', qy: '5' }, [4]],
    ['cross-axes', 'Move into Quadrant I', { mode: 'translate', x: '-4', y: '-1', dx: '6', dy: '3' }, [5]],
    ['up-seven', 'Move up across an axis', { mode: 'translate', x: '2', y: '-3', dx: '0', dy: '7' }, [6]],
    ['horizontal-gap', 'Distance on a horizontal line', { mode: 'distance', x: '1', y: '4', qx: '7', qy: '4' }, [7]],
    ['order', 'Exchange x and y', { x: '3', y: '5' }, [8]],
    ['third-quadrant', 'Both coordinates negative', { x: '-3', y: '-2' }, [9]],
    ['fractional', 'Fractional coordinates', { x: '-1/2', y: '3/4' }, []],
    ['diagonal-distance', 'A diagonal is shorter than the stepped path', { mode: 'distance', x: '0', y: '0', qx: '3', qy: '4' }, []],
    ['irrational-distance', 'An exact square-root distance', { mode: 'distance', x: '0', y: '0', qx: '1', qy: '1' }, []],
    ['reflection', 'Reflect across the x-axis', { mode: 'reflect', x: '-4', y: '-1' }, []]
  ];
  const api = Object.freeze({ defaults: () => clone(initial), accept, location, model,
    presets: () => freeze(examples.map(([id, label, state, quizIndices]) => ({ id, label, state: accept(state), quizIndices }))) });
  if (host) host.PrimerCoordinatePlaneCore = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window === 'undefined' ? null : window);
