(function () {
  'use strict';

  // Projection: https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html
  // Qubit coordinates and phase conventions:
  // https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/bloch-sphere
  // X-basis measurement:
  // https://quantum.cloud.ibm.com/learning/en/modules/quantum-mechanics/stern-gerlach-measurements-with-qiskit
  const TAU = 2 * Math.PI;
  const radians = degrees => degrees * Math.PI / 180;
  const bounded = (value, min, max, fallback) => {
    const n = Number(value);
    return Number.isFinite(n) ? Math.max(min, Math.min(max, n)) : fallback;
  };
  const fixed = n => (Math.abs(n) < 0.0005 ? 0 : n).toFixed(3);
  const tuple = point => '(' + point.map(fixed).join(', ') + ')';
  const scale = (point, amount) => point.map(value => value * amount);
  const percent = p => (Math.max(0, Math.min(1, p)) * 100).toFixed(1) + '%';
  const cubeEdges = [[0,1], [1,2], [2,3], [3,0], [4,5], [5,6], [6,7], [7,4],
    [0,4], [1,5], [2,6], [3,7]];

  function perspective(state, g) {
    const c = g.colors;
    const depth = bounded(state.depth, 3.2, 5.6, 3.6);
    const focal = bounded(state.focal, 1, 2, 1.6);
    const side = 1.2, half = side / 2;
    const eye = [0, 0, 0];
    // Every physical edge remains 1.2 units long as depth and focal vary.
    const vertices = [[-1,-1,-1], [1,-1,-1], [1,1,-1], [-1,1,-1],
      [-1,-1,1], [1,-1,1], [1,1,1], [-1,1,1]]
      .map(([x, y, z]) => [0.8 + half * x, half * y, depth + half * z]);
    // The picture plane is in front of the eye. All cube points satisfy z > f > 0.
    const project = ([x, y, z]) => [focal * x / z, focal * y / z, focal];
    const projected = vertices.map(project);
    const plane = [[-0.75,-0.92,focal], [1.25,-0.92,focal],
      [1.25,0.92,focal], [-0.75,0.92,focal]];
    g.polygon(plane, c.teal, {opacity: 0.1, stroke: c.teal, width: 1.2});
    for (const x of [-0.5, 0, 0.5, 1]) {
      g.line([[x,-0.92,focal], [x,0.92,focal]], c.teal, {width: 1, opacity: 0.25});
    }
    for (const y of [-0.5, 0, 0.5]) {
      g.line([[-0.75,y,focal], [1.25,y,focal]], c.teal, {width: 1, opacity: 0.25});
    }
    g.line([eye, [0,0,depth + 0.9]], c.ink, {width: 1, dashed: true, opacity: 0.55});
    // Eight rays contain their exact image-plane intersections; segmenting at
    // each intersection also lets the shared renderer sort the plane correctly.
    vertices.forEach((vertex, i) => {
      g.line([eye, projected[i], vertex], c.gold, {width: 1.2, opacity: 0.6});
    });
    g.box([0.8,0,depth], [side,side,side], c.blue, {opacity: 0.1, stroke: false});
    cubeEdges.forEach(([a, b]) => {
      g.line([vertices[a], vertices[b]], c.blue, {width: 2.5});
      g.line([projected[a], projected[b]], c.coral, {width: 3});
    });
    g.sphere(eye, 0.09, c.ink);
    g.sphere([0,0,focal], 0.035, c.teal);
    // One corresponding corner makes the numerical example easy to locate.
    const point = vertices[2], imagePoint = projected[2];
    g.sphere(point, 0.045, c.coral);
    g.sphere(imagePoint, 0.035, c.coral);
    g.label([-0.13,-0.16,0], 'Eye E', c.ink);
    g.label([-0.55,1.02,focal], 'Picture plane', c.teal);
    g.label([0.8,0.94,depth + half], 'Cube · 1.2 units', c.blue);
    g.label(point, 'P', c.coral);
    g.label(imagePoint, 'P′', c.coral);
    const near = depth - half, far = depth + half;
    return {
      readout: 'Eye E = (0, 0, 0); picture plane z = f = ' + fixed(focal) +
        '. Cube centre depth = ' + fixed(depth) + '; every cube edge stays 1.200 units. ' +
        'Perspective rule: x′ = f·x/z, y′ = f·y/z. P = ' + tuple(point) +
        ' projects to P′ = ' + tuple(imagePoint) + '. Near-face image width = ' +
        fixed(side * focal / near) + '; far-face image width = ' + fixed(side * focal / far) +
        '. Increasing depth shrinks the image; increasing f enlarges it.',
      legend: [
        {label: 'Blue: physical cube with constant edge lengths', color: c.blue},
        {label: 'Coral: projected cube edges and matching corner P / P′', color: c.coral},
        {label: 'Gold: sightlines from the eye through the picture plane', color: c.gold},
        {label: 'Teal: picture plane; dot is the vanishing point (0, 0, f)', color: c.teal},
      ],
      note: 'This is a geometric model of one-point perspective for drawing. The picture plane sits in front of the eye, so its upright image uses positive f; it is not a sensor behind a pinhole. Edges parallel to the depth axis converge toward the teal vanishing point in the projected drawing. Dragging rotates your view of this construction; the marked projection eye stays fixed. All lengths use the same arbitrary units.',
    };
  }

  function bloch(state, g) {
    const c = g.colors;
    const polar = bounded(state.polar, 0, 180, 60);
    const phase = bounded(state.phase, 0, 360, 45);
    const theta = radians(polar), phi = radians(phase);
    const sine = Math.sin(theta);
    const vector = [sine * Math.cos(phi), sine * Math.sin(phi), Math.cos(theta)]
      .map(value => Math.abs(value) < 1e-14 ? 0 : value);
    // A proper rigid rotation places quantum Z vertically without reversing
    // the handedness of X, Y, Z. Geometry still has unit Bloch-vector length.
    const world = ([x, y, z]) => [x, z, -y];
    const point = world(vector);
    const pole = polar === 0 || polar === 180;
    const circle = fn => Array.from({length: 65}, (_, i) => world(fn(i * TAU / 64)));
    g.mesh((u, v) => {
      const a = TAU * v, b = Math.PI * u;
      return world([Math.sin(b) * Math.cos(a), Math.sin(b) * Math.sin(a), Math.cos(b)]);
    }, 12, 24, c.blue, {opacity: 0.055, stroke: false});
    g.line(circle(a => [Math.cos(a), Math.sin(a), 0]), c.teal, {width: 1.7, opacity: 0.8});
    g.line(circle(a => [Math.cos(a), 0, Math.sin(a)]), c.blue, {width: 1, opacity: 0.45});
    g.line(circle(a => [0, Math.cos(a), Math.sin(a)]), c.blue, {width: 1, opacity: 0.45});
    g.line([world([-1.3,0,0]), world([1.3,0,0])], c.ink, {width: 1.3});
    g.line([world([0,-1.25,0]), world([0,1.25,0])], c.ink, {width: 1.3, dashed: true});
    g.arrow(world([0,0,-1.23]), world([0,0,1.25]), c.teal, {width: 1.7});
    if (!pole) {
      // This latitude is the family of states obtained by changing phase at
      // fixed polar angle: every point has exactly the same Z probabilities.
      g.line(circle(a => [sine * Math.cos(a), sine * Math.sin(a), vector[2]]),
        c.gold, {width: 2, dashed: true});
      g.line([point, world([vector[0],vector[1],0]), [0,0,0]],
        c.plum, {width: 1.5, dashed: true});
      if (phase > 0) {
        g.line(Array.from({length: 33}, (_, i) => world([
          0.32 * Math.cos(phi * i / 32), 0.32 * Math.sin(phi * i / 32), 0])),
        c.plum, {width: 2.5});
      }
    }
    if (polar > 0) {
      // At either pole azimuth is arbitrary; keep the angle guide independent
      // of phase too, so changing phase does not suggest a different state.
      const guidePhi = pole ? 0 : phi;
      g.line(Array.from({length: 33}, (_, i) => {
        const angle = theta * i / 32;
        return world([0.43 * Math.sin(angle) * Math.cos(guidePhi),
          0.43 * Math.sin(angle) * Math.sin(guidePhi), 0.43 * Math.cos(angle)]);
      }), c.gold, {width: 2.5});
    }
    g.arrow([0,0,0], point, c.coral, {width: 4});
    g.sphere(point, 0.065, c.coral);
    g.sphere([0,0,0], 0.035, c.ink);
    g.label(world([0,0,1.42]), '+Z · |0⟩', c.teal);
    g.label(world([0,0,-1.4]), '−Z · |1⟩', c.teal);
    g.label(world([1.46,0,0]), '+X · |+⟩', c.ink);
    g.label(world([0,1.42,0]), '+Y', c.ink);
    g.label(scale(point, 1.12), 'r', c.coral);
    const p0 = (1 + vector[2]) / 2, pPlus = (1 + vector[0]) / 2;
    return {
      readout: 'θ = ' + polar + '°, φ = ' + phase + '°. Bloch vector r = ' + tuple(vector) +
        '; |r| = 1. Z measurement: P(0) = (1 + r_z)/2 = ' + percent(p0) +
        '; P(1) = ' + percent(1 - p0) + '. X measurement: P(+) = (1 + r_x)/2 = ' +
        percent(pPlus) + '; P(−) = ' + percent(1 - pPlus) + '. ' +
        (pole ? 'At this pole, φ is arbitrary: changing it leaves the physical state and all probabilities unchanged.' :
          'Changing φ at fixed θ leaves both Z probabilities unchanged, but can change the X probabilities.'),
      legend: [
        {label: 'Coral: unit Bloch vector r for the prepared state', color: c.coral},
        {label: 'Teal: Z axis and equator (equal Z probabilities)', color: c.teal},
        {label: 'Gold: polar angle θ and latitude with fixed Z probabilities', color: c.gold},
        {label: 'Plum: relative phase φ and equatorial projection', color: c.plum},
      ],
      note: 'Pure single-qubit states only: |ψ⟩ = cos(θ/2)|0⟩ + e^(iφ)sin(θ/2)|1⟩. A common global phase has no observable effect and is omitted. Z measurements alone cannot reveal relative phase; even Z and X cannot distinguish φ from 360° − φ without Y information. Each measurement pair describes separate trials on identically prepared qubits. Mixed states lie inside the sphere; entangled multi-qubit states need a richer description. This sphere is a state diagram, not the qubit’s position in space.',
    };
  }

  window.PrimerSpatial.register({
    'arts.2.color-theory': {
      camera: {yaw: 62, pitch: 15},
      initial: {depth: 3.6, focal: 1.6},
      controls: [
        {key: 'depth', label: 'Cube centre depth', min: 3.2, max: 5.6, step: 0.2, unit: ' units'},
        {key: 'focal', label: 'Eye-to-picture-plane distance f', min: 1, max: 2, step: 0.1, unit: ' units'},
      ],
      build: perspective,
    },
    'cs.5.quantum': {
      camera: {yaw: -30, pitch: 20},
      initial: {polar: 60, phase: 45},
      controls: [
        {key: 'polar', label: 'Polar angle θ from +Z', min: 0, max: 180, step: 15, unit: '°'},
        {key: 'phase', label: 'Relative phase φ around Z', min: 0, max: 360, step: 15, unit: '°'},
      ],
      build: bloch,
    },
  });
}());
