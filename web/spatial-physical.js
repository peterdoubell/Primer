/* Spatial explanations for physics and Earth science. No network or animation loop.
 * Sources: OpenStax University Physics 2 §16.2 and Chemistry §10.6;
 * NASA Space Place, What Causes the Seasons?; USGS, Inside the Earth.
 */
(function () {
  'use strict';

  const TAU = 2 * Math.PI;
  const radians = degrees => degrees * Math.PI / 180;
  const add = (a, b) => a.map((value, i) => value + b[i]);
  const scale = (point, factor) => point.map(value => value * factor);
  const dot = (a, b) => a.reduce((sum, value, i) => sum + value * b[i], 0);
  const number = (value, fallback, min, max) => Number.isFinite(Number(value))
    ? Math.min(max, Math.max(min, Number(value))) : fallback;
  const fixed = (value, digits) => (Math.abs(value) < 0.5 * Math.pow(10, -digits) ? 0 : value).toFixed(digits);
  const ring = (center, first, second, radius, segments = 64) => Array.from({ length: segments + 1 }, (_, i) => {
    const angle = TAU * i / segments;
    return add(center, add(scale(first, radius * Math.cos(angle)), scale(second, radius * Math.sin(angle))));
  });

  window.PrimerSpatial.register({
    'phys.4.em-maxwell': {
      initial: { time: 0, polarization: 0 },
      controls: [
        { key: 'time', label: 'Time through one period', min: 0, max: 1, step: 0.025, unit: 'T' },
        { key: 'polarization', label: 'Linear polarization angle', min: 0, max: 180, step: 15, unit: '°' },
      ],
      build(state, g) {
        const c = g.colors;
        const time = number(state.time, 0, 0, 1);
        const angle = number(state.polarization, 0, 0, 180);
        const alpha = radians(angle);
        const electric = [0, Math.cos(alpha), Math.sin(alpha)];
        // +x cross E = cB, so E cross B always transports energy in +x.
        const magnetic = [0, -Math.sin(alpha), Math.cos(alpha)];
        const field = x => Math.sin(TAU * (x / 1.6 - time));
        const point = (x, direction, fraction = 1) => add([x, 0, 0], scale(direction, 0.68 * field(x) * fraction));
        [ [electric, c.coral], [magnetic, c.blue] ].forEach(([direction, color]) => {
          g.mesh((u, v) => point(-1.6 + 3.2 * u, direction, v), 64, 1, color, { opacity: 0.16 });
          g.line(Array.from({ length: 129 }, (_, i) => point(-1.6 + i * 3.2 / 128, direction)), color, { width: 2.6 });
          for (let i = 0; i <= 5; i += 1) {
            const x = -1.6 + 3.2 * i / 5;
            if (Math.abs(field(x)) > 0.04) g.arrow([x, 0, 0], point(x, direction), color, { width: 1.4 });
          }
        });
        g.arrow([-1.8, 0, 0], [1.85, 0, 0], c.ink, { width: 1.4 });
        g.label([1.6, -0.3, 0], '+x: propagation', c.ink);
        g.arrow([-1.8, 0, 0], add([-1.8, 0, 0], scale(electric, 0.9)), c.coral, { width: 2 });
        g.arrow([-1.8, 0, 0], add([-1.8, 0, 0], scale(magnetic, 0.9)), c.blue, { width: 2 });
        g.label(add([-1.8, 0, 0], scale(electric, 1.08)), 'E direction', c.coral);
        g.label(add([-1.8, 0, 0], scale(magnetic, 1.08)), 'B direction', c.blue);
        const value = field(0);
        return {
          readout: `At x = 0: E/E₀ = cB/E₀ = ${fixed(value, 2)}. Time = ${fixed(time, 3)} T; polarization = ${angle}°. E ⟂ B ⟂ propagation; E × B points in +x wherever the fields are nonzero.`,
          legend: [{ label: 'Electric field E', color: c.coral }, { label: 'Magnetic field cB', color: c.blue }, { label: 'Propagation +x', color: c.ink }],
          note: 'A linearly polarized plane wave in vacuum: E and B are in phase and E₀ = cB₀. Both field amplitudes are normalized to the same drawing scale; the ribbons trace field vectors, not a material surface or a particle path. Increasing time moves the crests in +x.',
        };
      },
    },

    'phys.4.solid-state': {
      initial: { lattice: 'bcc', view: 'sites' },
      controls: [
        { key: 'lattice', label: 'Cubic unit cell', options: [
          { value: 'sc', label: 'Simple cubic' }, { value: 'bcc', label: 'Body-centered cubic' }, { value: 'fcc', label: 'Face-centered cubic' },
        ] },
        { key: 'view', label: 'Atom representation', options: [
          { value: 'sites', label: 'Small spheres: see every site' }, { value: 'touching', label: 'Touching spheres: see packing' },
        ] },
      ],
      build(state, g) {
        const c = g.colors;
        const type = ['sc', 'bcc', 'fcc'].includes(state.lattice) ? state.lattice : 'bcc';
        const touching = state.view === 'touching';
        const half = 0.82;
        const edge = 2 * half;
        const radius = touching ? ({ sc: edge / 2, bcc: Math.sqrt(3) * edge / 4, fcc: Math.sqrt(2) * edge / 4 })[type] : 0.15;
        const corners = [];
        [-half, half].forEach(x => [-half, half].forEach(y => [-half, half].forEach(z => corners.push([x, y, z]))));
        corners.forEach(center => g.sphere(center, radius, c.blue, { opacity: touching ? 0.65 : 1 }));
        for (let i = 0; i < corners.length; i += 1) {
          for (let j = i + 1; j < corners.length; j += 1) {
            if (corners[i].filter((value, axis) => value !== corners[j][axis]).length === 1) {
              g.line([corners[i], corners[j]], c.ink, { width: 1.4 });
            }
          }
        }
        if (type === 'bcc') g.sphere([0, 0, 0], radius, c.coral, { opacity: touching ? 0.8 : 1 });
        if (type === 'fcc') {
          [[half, 0, 0], [-half, 0, 0], [0, half, 0], [0, -half, 0], [0, 0, half], [0, 0, -half]].forEach(center => g.sphere(center, radius, c.gold, { opacity: touching ? 0.8 : 1 }));
        }
        g.label([-half, half + radius + 0.14, -half], 'Corner: ⅛ per cell', c.blue);
        if (type === 'bcc') g.label([0, -0.3, 0], 'Body center: 1', c.coral);
        if (type === 'fcc') g.label([0, half + radius + 0.14, 0], 'Face: ½ per cell', c.gold);
        const descriptions = {
          sc: { name: 'Simple cubic', count: '8 corners × ⅛ = 1 atom per cell', coordination: 6, packing: 52.4, relation: '2r = a' },
          bcc: { name: 'Body-centered cubic', count: '8 corners × ⅛ + 1 body center × 1 = 2 atoms per cell', coordination: 8, packing: 68.0, relation: '4r = √3 a' },
          fcc: { name: 'Face-centered cubic', count: '8 corners × ⅛ + 6 faces × ½ = 4 atoms per cell', coordination: 12, packing: 74.0, relation: '4r = √2 a' },
        };
        const info = descriptions[type];
        return {
          readout: `${info.name}: ${info.count}. In the extended crystal, coordination number = ${info.coordination}; hard-sphere packing fraction ≈ ${fixed(info.packing, 1)}%. ${touching ? `Touching-sphere geometry: ${info.relation}, where a is the cube edge.` : 'Small spheres expose the sites; their radii are reduced for clarity.'}`,
          legend: [{ label: 'Corner sites (shared by 8 cells)', color: c.blue }, ...(type === 'bcc' ? [{ label: 'Body-center site (inside this cell)', color: c.coral }] : []), ...(type === 'fcc' ? [{ label: 'Face sites (shared by 2 cells)', color: c.gold }] : [])],
          note: 'The wire cube is one conventional unit cell of an ideal monatomic crystal. Whole boundary atoms are shown, but only the fraction inside the cube is counted. Coordination includes neighbors in adjoining cells. This spatial arrangement complements the lesson’s separate energy-band model.',
        };
      },
    },

    'earth.1.seasons': {
      initial: { orbit: 0, latitude: '45' },
      controls: [
        { key: 'orbit', label: 'Orbit from June solstice', min: 0, max: 360, step: 15, unit: '°' },
        { key: 'latitude', label: 'Observe daylight at', options: [
          { value: '45', label: '45° north' }, { value: '-45', label: '45° south' }, { value: '0', label: 'Equator' },
        ] },
      ],
      build(state, g) {
        const c = g.colors;
        const orbit = number(state.orbit, 0, 0, 360);
        const angle = radians(orbit);
        const latitude = ['45', '-45', '0'].includes(String(state.latitude)) ? Number(state.latitude) : 45;
        const tilt = radians(23.4);
        const axis = [Math.sin(tilt), Math.cos(tilt), 0];
        const equatorial = [Math.cos(tilt), -Math.sin(tilt), 0];
        const radius = 0.42;
        const earth = [-1.4 * Math.cos(angle), 0, 1.4 * Math.sin(angle)];
        const sunward = [Math.cos(angle), 0, -Math.sin(angle)];
        g.line(ring([0, 0, 0], [1, 0, 0], [0, 0, 1], 1.4), c.ink, { width: 1, dashed: true });
        g.sphere([0, 0, 0], 0.26, c.gold);
        g.label([0, -0.45, 0], 'Sun', c.gold);
        // Latitude/longitude facets retain the same axial orientation at every orbit position.
        const surface = (lon, lat) => add(scale(equatorial, Math.cos(lat) * Math.cos(lon)), add(scale([0, 0, 1], Math.cos(lat) * Math.sin(lon)), scale(axis, Math.sin(lat))));
        for (let i = 0; i < 20; i += 1) {
          for (let j = 0; j < 10; j += 1) {
            const lon = TAU * (i + 0.5) / 20;
            const lat = Math.PI * ((j + 0.5) / 10 - 0.5);
            const lit = dot(surface(lon, lat), sunward) >= 0;
            const color = lit ? (lat >= 0 ? c.teal : c.blue) : c.ink;
            g.polygon([[i, j], [i + 1, j], [i + 1, j + 1], [i, j + 1]].map(([u, v]) => add(earth, scale(surface(TAU * u / 20, Math.PI * (v / 10 - 0.5)), radius))), color, { opacity: 1 });
          }
        }
        g.line(ring(earth, equatorial, [0, 0, 1], radius * 1.01), '#e5d7bb', { width: 1 });
        const latRadians = radians(latitude);
        const latitudeCenter = add(earth, scale(axis, radius * Math.sin(latRadians)));
        g.line(ring(latitudeCenter, equatorial, [0, 0, 1], radius * Math.cos(latRadians) * 1.015), c.coral, { width: 2.4 });
        g.arrow(add(earth, scale(axis, -0.65)), add(earth, scale(axis, 0.72)), c.plum, { width: 2.5 });
        g.label(add(earth, scale(axis, 0.86)), 'N · fixed axis', c.plum);
        g.label(add(earth, scale(axis, -0.77)), 'S', c.plum);
        g.line([earth, add(earth, [0, 0.73, 0])], c.ink, { width: 1, dashed: true });
        g.label(add(earth, [0.05, 0.55, 0]), '23.4°', c.plum);
        [-0.2, 0, 0.2].forEach(offset => {
          const shift = [0, offset, 0];
          g.arrow(add(scale(earth, 0.28), shift), add(scale(earth, 0.65), shift), c.gold, { width: 1.7 });
        });
        const declination = Math.asin(dot(axis, sunward));
        const dayHours = 24 / Math.PI * Math.acos(-Math.tan(latRadians) * Math.tan(declination));
        const quarter = orbit % 360 / 90;
        const events = ['June solstice', 'September equinox', 'December solstice', 'March equinox', 'June solstice'];
        const event = quarter % 1 === 0 ? events[quarter] : `Between ${events[Math.floor(quarter)]} and ${events[Math.floor(quarter) + 1]}`;
        const hemisphere = Math.abs(declination) < 0.0001 ? 'Both hemispheres receive equal-length days in this geometric model.' : `${declination > 0 ? 'Northern' : 'Southern'} Hemisphere tilts toward the Sun; the opposite hemisphere tilts away.`;
        return {
          readout: `${event}. ${hemisphere} Sun overhead at latitude ${fixed(declination * 180 / Math.PI, 1)}°. Daylight at ${latitude === 0 ? 'the equator' : `${Math.abs(latitude)}° ${latitude > 0 ? 'north' : 'south'}`} ≈ ${fixed(dayHours, 1)} hours.`,
          legend: [{ label: 'Sunlight direction', color: c.gold }, { label: 'Axis fixed in space', color: c.plum }, { label: 'Selected latitude', color: c.coral }, { label: 'Night side', color: c.ink }],
          note: 'Sizes and distances are schematic. The circular orbit deliberately keeps distance constant: axial tilt changes sunlight angle and daylight duration. The 23.4° tilt is measured from the perpendicular to the orbital plane. Daylight estimates omit atmospheric refraction and the Sun’s angular size. Four temperate-season names do not describe every region.',
        };
      },
    },

    'earth.3.earth-science': {
      initial: { opening: 100 },
      controls: [
        { key: 'opening', label: 'Open a slice through Earth', min: 30, max: 160, step: 10, unit: '°' },
      ],
      build(state, g) {
        const c = g.colors;
        const opening = number(state.opening, 100, 30, 160);
        const radius = 1.42;
        const open = radians(opening);
        const start = Math.PI / 2 + open / 2;
        const end = Math.PI / 2 + TAU - open / 2;
        const layers = [
          { label: 'Solid inner core', inner: 0, outer: 1221, color: c.plum },
          { label: 'Liquid outer core', inner: 1221, outer: 3480, color: c.coral },
          { label: 'Solid mantle', inner: 3480, outer: 6336, color: c.gold },
          { label: 'Crust', inner: 6336, outer: 6371, color: c.green },
        ];
        const at = (r, angle, longitude) => [r * Math.sin(angle) * Math.cos(longitude), r * Math.cos(angle), r * Math.sin(angle) * Math.sin(longitude)];
        // Exterior retains its true spherical surface while two radial faces expose the layers.
        g.mesh((u, v) => at(radius, Math.PI * v, start + (end - start) * u), 24, 12, c.green, { opacity: 1 });
        [start, end].forEach(longitude => {
          layers.forEach(layer => {
            const inner = radius * layer.inner / 6371;
            const outer = radius * layer.outer / 6371;
            for (let i = 0; i < 24; i += 1) {
              const a = Math.PI * i / 24;
              const b = Math.PI * (i + 1) / 24;
              g.polygon([at(inner, a, longitude), at(outer, a, longitude), at(outer, b, longitude), at(inner, b, longitude)], layer.color, { opacity: 1 });
            }
            g.line(Array.from({ length: 33 }, (_, i) => at(outer, Math.PI * i / 32, longitude)), c.ink, { width: layer.label === 'Crust' ? 1.3 : 0.8 });
          });
        });
        // Labels sit on the open face, with leaders identifying the actual radial layer.
        const face = start;
        [
          { index: 3, angle: 0.36, radiusKm: 6353.5, label: [-1.6, 1.52, 0.1] },
          { index: 2, angle: 0.93, radiusKm: 5000, label: [-1.6, 0.88, 0.1] },
          { index: 1, angle: 1.67, radiusKm: 2300, label: [-1.6, -0.26, 0.1] },
          { index: 0, angle: 2.32, radiusKm: 650, label: [-1.6, -0.88, 0.1] },
        ].forEach(item => {
          const layer = layers[item.index];
          g.line([at(radius * item.radiusKm / 6371, item.angle, face), item.label], layer.color, { width: 1.4 });
          g.label(item.label, layer.label, layer.color);
        });
        return {
          readout: `Slice opening: ${opening}°. Approximate distances from the center: inner-core boundary 1,221 km; core–mantle boundary 3,480 km; surface 6,371 km. The crust is about 5–70 km thick; this section uses 35 km.`,
          legend: layers.slice().reverse().map(layer => ({ label: layer.label, color: layer.color })),
          note: 'A simplified concentric Earth with boundaries drawn to their approximate radial proportions. The crust is extremely thin at this scale. The mantle is mostly solid rock that flows over geological time, the outer core is liquid, and the inner core is solid. The open wedge is a viewing cut, not a gap inside Earth; boundary depths vary geographically.',
        };
      },
    },
  });
}());
