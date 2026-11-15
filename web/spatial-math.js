/* Lesson-specific spatial mathematics. Coordinates are mapped to a right-handed
   frame with mathematical z vertical; these are sampled explanatory models.
   Cross product / tangent plane: OpenStax Calculus Volume 3, sections 2.4 and 4.4.
   Closed orientable surface genus: mathworld.wolfram.com/Genus.html. */
(function () {
  'use strict';

  const TAU = 2 * Math.PI;
  const number = (value, min, max, fallback) => {
    const n = Number(value);
    return Number.isFinite(n) ? Math.max(min, Math.min(max, n)) : fallback;
  };
  const fixed = (n) => (Math.abs(n) < 0.0005 ? 0 : n).toFixed(3);
  const tuple = (v) => '(' + v.map(fixed).join(', ') + ')';

  window.PrimerSpatial.register({
    'math.2.geometry': {
      initial: { length: 4, width: 3, height: 2, view: 'solid' },
      controls: [
        { key: 'length', label: 'Length', min: 1, max: 4, step: 1, unit: 'units' },
        { key: 'width', label: 'Width', min: 1, max: 4, step: 1, unit: 'units' },
        { key: 'height', label: 'Height: number of layers', min: 1, max: 4, step: 1, unit: 'units' },
        { key: 'view', label: 'Layer view', options: [
          { value: 'solid', label: 'Assembled cuboid' },
          { value: 'layers', label: 'Separate the layers' },
        ] },
      ],
      build(state, g) {
        const c = g.colors;
        const length = Math.round(number(state.length, 1, 4, 4));
        const width = Math.round(number(state.width, 1, 4, 3));
        const height = Math.round(number(state.height, 1, 4, 2));
        const separated = state.view === 'layers';
        const unit = 0.58;
        const gap = separated ? 0.19 : 0;
        // Keep the stack centred as layers are added; its unit cubes do not move
        // off the top of the frame when the learner chooses the maximum height.
        const bottom = -(height * unit + (height - 1) * gap) / 2;
        const top = bottom + height * unit + (height - 1) * gap;
        const colors = [c.teal, c.gold, c.blue, c.plum];
        for (let layer = 0; layer < height; layer++) {
          for (let x = 0; x < length; x++) {
            for (let z = 0; z < width; z++) {
              g.box([
                (x + 0.5 - length / 2) * unit,
                bottom + unit / 2 + layer * (unit + gap),
                (z + 0.5 - width / 2) * unit,
              ], [unit, unit, unit], colors[layer], { stroke: c.ink });
            }
          }
          g.label([length * unit / 2 + 0.18, bottom + unit / 2 + layer * (unit + gap), 0],
            'Layer ' + (layer + 1), colors[layer]);
        }
        const front = width * unit / 2 + 0.18;
        g.line([[-length * unit / 2, bottom - 0.15, front],
          [length * unit / 2, bottom - 0.15, front]], c.ink, { width: 1.5 });
        g.label([0, bottom - 0.3, front], length + ' units long', c.ink);
        g.label([-length * unit / 2 - 0.25, bottom, 0], width + ' units wide', c.ink);
        g.label([0, top + 0.24, 0], (length * width * height) + ' unit cubes', c.ink);
        return {
          readout: 'Each layer has ' + length + ' × ' + width + ' = ' + (length * width) +
            ' unit cubes. ' + height + (height === 1 ? ' layer' : ' layers') + ' × ' +
            (length * width) + ' cubes = ' + (length * width * height) +
            ' cubic units. V = length × width × height. Base area = ' +
            (length * width) + ' square units; base perimeter = ' +
            (2 * (length + width)) + ' units.',
          legend: Array.from({ length: height }, (_, i) => ({
            label: 'Layer ' + (i + 1) + ': ' + (length * width) + ' cubes', color: colors[i],
          })),
          note: separated
            ? 'The gaps only separate layers for counting; they add no cubes and are not part of the cuboid’s height or volume.'
            : 'Every small cube has side length 1 unit. Rotate the solid to inspect the rows and layers; some cubes are hidden behind others.',
        };
      },
    },

    'math.3.vectors': {
      initial: { length: 1.2, angle: 60 },
      camera: { pitch: 38 },
      controls: [
        { key: 'length', label: 'Magnitude of b', min: 0.5, max: 1.5, step: 0.1 },
        { key: 'angle', label: 'Signed angle from a to b in the xy plane', min: -180, max: 180, step: 5, unit: '°' },
      ],
      build(state, g) {
        const c = g.colors;
        const magnitude = number(state.length, 0.5, 1.5, 1.2);
        const degrees = number(state.angle, -180, 180, 60);
        const theta = degrees * Math.PI / 180;
        const bx = magnitude * Math.cos(theta);
        const by = Math.abs(Math.sin(theta)) < 1e-12 ? 0 : magnitude * Math.sin(theta);
        // [x, y, z] -> [x, z, -y] is a rotation, not a reflection.
        const p = (x, y, z) => [0.76 * x, 0.76 * z - 0.25, -0.76 * y];
        const origin = p(0, 0, 0);
        const a = p(1, 0, 0);
        const b = p(bx, by, 0);
        const sum = p(1 + bx, by, 0);
        const cross = p(0, 0, by);
        g.line([p(-1.65, 0, 0), p(2.65, 0, 0)], c.ink, { width: 1, dashed: true });
        g.line([p(0, -1.65, 0), p(0, 1.65, 0)], c.ink, { width: 1, dashed: true });
        g.line([p(0, 0, -1.65), p(0, 0, 1.65)], c.ink, { width: 1, dashed: true });
        g.label(p(2.75, 0, 0), 'x', c.ink);
        g.label(p(0, 1.8, 0), 'y', c.ink);
        g.label(p(0, 0, 1.85), 'z', c.ink);
        g.polygon([origin, a, sum, b], c.gold, { opacity: 0.22, stroke: c.gold });
        g.line([a, sum, b], c.ink, { width: 1.5, dashed: true });
        g.arrow(origin, a, c.blue, { width: 4 });
        g.arrow(origin, b, c.coral, { width: 4 });
        if (Math.hypot(1 + bx, by) > 1e-9) g.arrow(origin, sum, c.teal, { width: 4 });
        else g.sphere(origin, 0.055, c.teal);
        g.label(p(1, -0.18, 0), 'a', c.blue);
        g.label(p(bx, by, 0.18), 'b', c.coral);
        g.label(p(1 + bx, by, 0.32), Math.hypot(1 + bx, by) > 1e-9 ? 'a + b' : 'a + b = 0', c.teal);
        if (Math.abs(by) > 1e-9) {
          g.arrow(origin, cross, c.plum, { width: 4 });
          g.label(p(0.18, 0, by + Math.sign(by) * 0.15), 'a × b', c.plum);
        } else {
          g.sphere(origin, 0.05, c.plum);
          g.label(p(-0.2, 0.2, 0.25), 'a × b = 0', c.plum);
        }
        const angleArc = [];
        for (let i = 0; i <= 30; i++) {
          const angle = theta * i / 30;
          angleArc.push(p(0.35 * Math.cos(angle), 0.35 * Math.sin(angle), 0.015));
        }
        g.line(angleArc, c.gold, { width: 2 });
        g.label(p(0.52 * Math.cos(theta / 2), 0.52 * Math.sin(theta / 2), 0.08),
          degrees + '°', c.gold);
        return {
          readout: 'a = (1, 0, 0); b = ' + tuple([bx, by, 0]) + '. a + b = ' +
            tuple([1 + bx, by, 0]) + ', with magnitude ' + fixed(Math.hypot(1 + bx, by)) +
            '. a · b = ' + fixed(bx) + '. a × b = ' + tuple([0, 0, by]) +
            '. Parallelogram area = |a × b| = ' + fixed(Math.abs(by)) + '.',
          legend: [
            { label: 'a: first vector', color: c.blue },
            { label: 'b: second vector', color: c.coral },
            { label: 'a + b: resultant', color: c.teal },
            { label: 'a × b: perpendicular vector', color: c.plum },
            { label: 'Parallelogram area', color: c.gold },
          ],
          note: Math.abs(by) < 1e-9
            ? 'The vectors are collinear here. Their cross product is the zero vector, which has no direction; the parallelogram has zero area.'
            : 'Both input vectors lie in the xy plane. The right-hand rule puts a × b along the signed z direction. Rotate to see its perpendicular direction; a negative angle reverses it.',
        };
      },
    },

    'math.4.multivar': {
      initial: { x: 0.6, y: 0.4, step: 0.6 },
      controls: [
        { key: 'x', label: 'Tangency point x₀', min: -1, max: 1, step: 0.1 },
        { key: 'y', label: 'Tangency point y₀', min: -1, max: 1, step: 0.1 },
        { key: 'step', label: 'Horizontal displacement h from x₀', min: -0.9, max: 0.9, step: 0.1 },
      ],
      build(state, g) {
        const c = g.colors;
        const x0 = number(state.x, -1, 1, 0.6);
        const y0 = number(state.y, -1, 1, 0.4);
        const h = number(state.step, -0.9, 0.9, 0.6);
        const f = (x, y) => (x * x + y * y) / 4;
        const f0 = f(x0, y0);
        const fx = x0 / 2;
        const fy = y0 / 2;
        const plane = (x, y) => f0 + fx * (x - x0) + fy * (y - y0);
        const p = (x, y, z) => [x * 0.82, z * 0.82 - 0.65, -y * 0.82];
        const point = p(x0, y0, f0);
        const trueValue = f(x0 + h, y0);
        const approximation = plane(x0 + h, y0);
        g.line([p(-2.25, 0, 0), p(2.25, 0, 0)], c.ink, { width: 1, dashed: true });
        g.line([p(0, -2.25, 0), p(0, 2.25, 0)], c.ink, { width: 1, dashed: true });
        g.line([p(0, 0, -0.3), p(0, 0, 2.2)], c.ink, { width: 1, dashed: true });
        g.label(p(2.4, 0, 0), 'x', c.ink);
        g.label(p(0, 2.4, 0), 'y', c.ink);
        g.label(p(0, 0, 2.35), 'z', c.ink);
        // A light mesh keeps the tangent plane below this convex surface visible.
        g.mesh((u, v) => {
          const x = 4 * u - 2;
          const y = 4 * v - 2;
          return p(x, y, f(x, y));
        }, 22, 22, c.blue, { opacity: 0.2, stroke: c.blue });
        const corners = [[x0 - 0.95, y0 - 0.65], [x0 + 0.95, y0 - 0.65],
          [x0 + 0.95, y0 + 0.65], [x0 - 0.95, y0 + 0.65]];
        g.polygon(corners.map(([x, y]) => p(x, y, plane(x, y))),
          c.gold, { opacity: 0.72, stroke: c.gold, width: 2 });
        const slice = [];
        for (let i = 0; i <= 50; i++) {
          const x = -2 + 4 * i / 50;
          slice.push(p(x, y0, f(x, y0)));
        }
        g.line(slice, c.teal, { width: 3 });
        g.line([p(x0 - 0.95, y0, plane(x0 - 0.95, y0)),
          p(x0 + 0.95, y0, plane(x0 + 0.95, y0))], c.gold, { width: 3 });
        g.sphere(point, 0.06, c.coral);
        g.label(point, Math.abs(h) > 0.001 ? 'P' : 'P = Q = L', c.coral);
        const actualPoint = p(x0 + h, y0, trueValue);
        const estimatePoint = p(x0 + h, y0, approximation);
        g.line([estimatePoint, actualPoint], c.plum, { width: 4 });
        g.sphere(estimatePoint, 0.045, c.gold);
        g.sphere(actualPoint, 0.055, c.teal);
        if (Math.abs(h) > 0.001) {
          g.label(actualPoint, 'Q', c.teal);
          g.label(estimatePoint, 'L', c.gold);
        }
        return {
          readout: 'Worked surface: f(x,y) = (x² + y²)/4. P = ' + tuple([x0, y0, f0]) +
            '; ∇f(P) = (' + fixed(fx) + ', ' + fixed(fy) + '). Tangent plane: L(x,y) = ' +
            fixed(f0) + ' + (' + fixed(fx) + ')(x − (' + fixed(x0) + ')) + (' +
            fixed(fy) + ')(y − (' + fixed(y0) + ')). At Q, x = x₀ + h = ' + fixed(x0 + h) +
            ', y = y₀: f = ' + fixed(trueValue) + ', L = ' + fixed(approximation) +
            '. Exact vertical error f − L = h²/4 = ' + fixed(h * h / 4) + '.',
          legend: [
            { label: 'Bowl surface: z = (x² + y²)/4', color: c.blue },
            { label: 'P: point of tangency', color: c.coral },
            { label: 'L: estimated point on the tangent plane', color: c.gold },
            { label: 'Q: exact point on the surface slice at y = y₀', color: c.teal },
            { label: 'Vertical approximation error', color: c.plum },
          ],
          note: 'This bowl is a separate worked example from the saddle in the lesson illustration. The plane agrees with the surface’s value and both partial derivatives at P. It is a local approximation; the displayed mesh is sampled, while all readouts use the exact formulas.',
        };
      },
    },

    'math.5.topology': {
      camera: { pitch: 40 },
      initial: { surface: 'torus', stretch: 1 },
      controls: [
        { key: 'surface', label: 'Choose a surface', options: [
          { value: 'torus', label: 'Torus: one handle' },
          { value: 'sphere', label: 'Sphere: no handles' },
        ] },
        { key: 'stretch', label: 'Horizontal stretch factor s', min: 0.6, max: 1.6, step: 0.1 },
      ],
      build(state, g) {
        const c = g.colors;
        const sphere = state.surface === 'sphere';
        const stretch = number(state.stretch, 0.6, 1.6, 1);
        const transverse = 1 / Math.sqrt(stretch);
        const transform = ([x, y, z]) => [stretch * x, transverse * y, transverse * z];
        const surface = sphere
          ? (u, v) => {
            const azimuth = u * TAU;
            const polar = v * Math.PI;
            return transform([1.15 * Math.sin(polar) * Math.cos(azimuth),
              1.15 * Math.cos(polar), 1.15 * Math.sin(polar) * Math.sin(azimuth)]);
          }
          : (u, v) => {
            const around = u * TAU;
            const tube = v * TAU;
            const radius = 0.9 + 0.35 * Math.cos(tube);
            return transform([radius * Math.cos(around),
              0.35 * Math.sin(tube), radius * Math.sin(around)]);
          };
        g.mesh(surface, sphere ? 24 : 32, sphere ? 18 : 16,
          sphere ? c.blue : c.teal, { opacity: 0.96, stroke: c.ink });
        const loop = [];
        for (let i = 0; i <= 64; i++) loop.push(surface(i / 64, sphere ? 0.5 : 0));
        g.line(loop, c.gold, { width: 3 });
        const genus = sphere ? 0 : 1;
        g.label([0, 1.75, 0], sphere ? 'Sphere surface · genus 0' : 'Torus surface · genus 1', c.ink);
        return {
          readout: (sphere ? 'Sphere' : 'Torus') + ' boundary surface: genus g = ' + genus +
            ', Euler characteristic χ = 2 − 2g = ' + (2 - 2 * genus) +
            '. Stretch s = ' + fixed(stretch) +
            ': (x,y,z) ↦ (s·x, y/√s, z/√s). Because s > 0, this map is continuous with a continuous inverse; the number of handles stays ' +
            genus + '.',
          legend: [
            { label: sphere ? 'Sphere: closed surface, no handle' : 'Torus: closed surface, one handle', color: sphere ? c.blue : c.teal },
            { label: 'A marked loop carried along by the stretch', color: c.gold },
          ],
          note: 'These are surfaces, not filled solids. Choosing sphere or torus selects a different object; it is not a continuous deformation between them. The mesh illustrates the invariant, not a proof. The formula χ = 2 − 2g applies to connected closed orientable surfaces. No cuts, gluing or self-intersections occur during this positive stretch.',
        };
      },
    },
  });
})();
