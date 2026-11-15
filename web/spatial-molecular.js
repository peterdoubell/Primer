(function () {
  'use strict';

  // Geometry is schematic unless a bond angle is explicitly stated. References:
  // https://openstax.org/books/chemistry-2e/pages/7-6-molecular-structure-and-polarity
  // https://goldbook.iupac.org/terms/view/C01058
  // https://openstax.org/books/organic-chemistry/pages/1-2-atomic-structure-orbitals
  // https://www.ncbi.nlm.nih.gov/books/NBK9896/
  const PI = Math.PI;
  const rad = degrees => degrees * PI / 180;
  const add = (a, b) => a.map((v, i) => v + b[i]);
  const scale = (a, k) => a.map(v => v * k);
  const dot = (a, b) => a.reduce((sum, v, i) => sum + v * b[i], 0);
  const length = a => Math.sqrt(dot(a, a));
  const unit = a => scale(a, 1 / (length(a) || 1));
  const bounded = (value, low, high, fallback) => {
    const n = Number(value);
    return Number.isFinite(n) ? Math.max(low, Math.min(high, n)) : fallback;
  };
  const rotateY = (p, angle) => [
    p[0] * Math.cos(angle) + p[2] * Math.sin(angle),
    p[1],
    -p[0] * Math.sin(angle) + p[2] * Math.cos(angle),
  ];
  const tetrahedron = [
    [0, 1, 0],
    [0, -1 / 3, 2 * Math.sqrt(2) / 3],
    [Math.sqrt(2 / 3), -1 / 3, -Math.sqrt(2) / 3],
    [-Math.sqrt(2 / 3), -1 / 3, -Math.sqrt(2) / 3],
  ];

  function angleArc(g, a, b, radius, color) {
    const u = unit(a);
    const v = unit(b);
    const angle = Math.acos(Math.max(-1, Math.min(1, dot(u, v))));
    const sin = Math.sin(angle);
    const points = Array.from({length: 33}, (_, i) => {
      const t = i / 32;
      return scale(add(scale(u, Math.sin((1 - t) * angle) / sin),
        scale(v, Math.sin(t * angle) / sin)), radius);
    });
    g.line(points, color, {width: 2});
    return angle * 180 / PI;
  }

  function molecularGeometry(state, g) {
    const c = g.colors;
    const name = ['water', 'ammonia', 'methane'].includes(state.molecule) ? state.molecule : 'water';
    const bondLength = 1.3;
    let atoms, lonePairs, element, color, shape, formula;
    if (name === 'water') {
      const halfAngle = rad(104.5 / 2);
      atoms = [[Math.sin(halfAngle), -Math.cos(halfAngle), 0],
        [-Math.sin(halfAngle), -Math.cos(halfAngle), 0]];
      lonePairs = [[0, 0.58, 0.82], [0, 0.58, -0.82]];
      element = 'O'; color = c.coral; shape = 'bent'; formula = 'H₂O';
    } else if (name === 'ammonia') {
      // Three unit vectors separated by 120° in azimuth, with H–N–H = 107°.
      const h = Math.sqrt((Math.cos(rad(107)) + 0.5) / 1.5);
      const r = Math.sqrt(1 - h * h);
      // Turn the pyramid so no hydrogen hides directly behind nitrogen in
      // the starting camera; this rigid rotation preserves every bond angle.
      atoms = [0, 1, 2].map(i => {
        const azimuth = i * PI * 2 / 3 + PI / 4;
        return [r * Math.cos(azimuth), -h, r * Math.sin(azimuth)];
      });
      lonePairs = [[0, 1, 0]];
      element = 'N'; color = c.blue; shape = 'trigonal pyramidal'; formula = 'NH₃';
    } else {
      atoms = tetrahedron;
      lonePairs = [];
      element = 'C'; color = c.ink; shape = 'tetrahedral'; formula = 'CH₄';
    }
    atoms.forEach(p => {
      const end = scale(p, bondLength);
      g.line([[0, 0, 0], end], c.ink, {width: 7});
      g.sphere(end, 0.19, c.blue);
      g.label(scale(p, bondLength + 0.25), 'H', c.ink);
    });
    g.sphere([0, 0, 0], 0.3, color);
    g.label([0, 0.07, 0.31], element, c.ink);
    if (state.domains === 'pairs') {
      lonePairs.forEach((p, i) => {
        const end = scale(unit(p), 0.95);
        g.line([[0, 0, 0], end], c.plum, {width: 1, dashed: true});
        // Markers represent electron-pair domains, not orbiting electrons.
        g.sphere(add(end, [-0.065, 0, 0]), 0.055, c.plum);
        g.sphere(add(end, [0.065, 0, 0]), 0.055, c.plum);
        g.label(scale(unit(p), 1.24), 'Lone pair ' + (i + 1), c.plum);
      });
    }
    const angle = angleArc(g, atoms[0], atoms[1], 0.62, c.gold);
    g.label(scale(unit(add(atoms[0], atoms[1])), 0.82), angle.toFixed(1) + '°', c.ink);
    const showPairs = state.domains === 'pairs';
    return {
      readout: formula + ': ' + shape + '. H–' + element + '–H ≈ ' + angle.toFixed(1) +
        '°. ' + atoms.length + ' bonding pairs and ' + lonePairs.length +
        ' lone pairs around ' + element + '; four electron domains in total. ' +
        (showPairs ? (lonePairs.length ? 'Lone-pair markers are visible.' : 'Methane has no central lone pairs to show.') : 'Lone-pair markers are hidden.'),
      legend: [{label: 'H: hydrogen', color: c.blue}, {label: element + ': central atom', color},
        {label: 'Bond angle', color: c.gold}, {label: 'Lone-pair domain', color: c.plum}],
      note: 'Ball-and-stick model; atom sizes and bond lengths are not to scale. Angles are approximate molecular values; methane uses an ideal tetrahedron. Lone-pair markers are schematic regions, not electron paths.',
    };
  }

  function chirality(state, g) {
    const c = g.colors;
    const achiral = state.substituents === 'repeated';
    const overlay = state.layout === 'overlay';
    const degrees = bounded(state.rotation, 0, 360, 0);
    const angle = rad(degrees);
    const labels = ['H', 'F', 'Cl', achiral ? 'Cl' : 'Br'];
    const colors = [c.blue, c.teal, c.gold, achiral ? c.gold : c.coral];
    const size = overlay ? 1.22 : 0.78;
    const leftCenter = overlay ? [0, 0, 0] : [-1.1, 0, 0];
    const rightCenter = overlay ? [0, 0, 0] : [1.1, 0, 0];
    const original = tetrahedron.map(p => scale(p, size));
    const mirror = tetrahedron.map(p => scale(rotateY([-p[0], p[1], p[2]], angle), size));
    if (!overlay) {
      g.polygon([[0, -1.15, -0.95], [0, 1.15, -0.95], [0, 1.15, 0.95], [0, -1.15, 0.95]],
        c.blue, {opacity: 0.1, stroke: c.blue});
      g.label([0, 1.45, 0], 'Mirror', c.blue);
    }
    const drawMolecule = (center, points, ghost) => {
      g.sphere(center, ghost ? 0.25 : 0.18, c.ink, {opacity: ghost ? 0.25 : 1});
      if (!ghost) g.label(add(center, [0, 0.04, 0.19]), 'C', c.ink);
      points.forEach((p, i) => {
        const end = add(center, p);
        g.line([center, end], colors[i], {width: ghost ? 7 : 4, dashed: ghost});
        g.sphere(end, ghost ? 0.23 : 0.16, colors[i], {opacity: ghost ? 0.25 : 1});
        // In overlay, label the solid reflected molecule only, to avoid duplicate text.
        if (!ghost) g.label(add(center, scale(p, 1.25)), labels[i], c.ink);
      });
    };
    drawMolecule(leftCenter, original, overlay);
    drawMolecule(rightCenter, mirror, false);
    if (!overlay) {
      g.label([-1.1, -1.24, 0], 'Original', c.ink);
      g.label([1.1, -1.24, 0], 'Reflected · ' + degrees + '°', c.ink);
    }
    // Count exact identity-and-position matches after centering the molecules.
    const matches = mirror.filter((p, i) => original.some((q, j) => labels[i] === labels[j] &&
      length(p.map((v, k) => v - q[k])) < 0.00001)).length;
    return {
      readout: (achiral ? 'Two identical Cl substituents: this tetrahedral centre is achiral.' :
        'H, F, Cl and Br are four distinct substituents: this tetrahedral centre is chiral.') +
        ' Reflected molecule rotated ' + degrees + '° about its vertical axis. ' + matches +
        '/4 substituent positions match when the centres coincide. ' +
        (achiral ? 'At 0° or 360°, all four match; the two Cl atoms are interchangeable.' :
          'At 0°, H and F align but Cl and Br exchange places. No rigid rotation can align all four identities.'),
      legend: [{label: 'C: central carbon', color: c.ink}, {label: 'H: hydrogen', color: c.blue}, {label: 'F: fluorine', color: c.teal},
        {label: 'Cl: chlorine', color: c.gold}].concat(achiral ? [] : [{label: 'Br: bromine', color: c.coral}]),
      note: 'Ideal tetrahedral geometry with equal bond lengths, used to compare handedness. Overlay shows the original as larger translucent markers and the reflected molecule as smaller solid markers. Rotation preserves handedness; reflection reverses it. The one-axis slider illustrates this distinction; chirality does not depend on which axis is tried.',
    };
  }

  function orbital(state, g) {
    const c = g.colors;
    const name = ['1s', '2px', '2py', '2pz'].includes(state.orbital) ? state.orbital : '2pz';
    const isS = name === '1s';
    const axis = isS ? 2 : {'2px': 0, '2py': 1, '2pz': 2}[name];
    const showNode = state.node === 'show';
    const direction = ['x', 'y', 'z'][axis];
    [[1.85, 0, 0], [0, 1.85, 0], [0, 0, 1.85]].forEach((p, i) => {
      g.line([scale(p, -1), p], c.ink, {width: 1, dashed: true});
      g.label(p, ['x', 'y', 'z'][i], c.ink);
    });
    if (isS) {
      g.mesh((u, v) => {
        const a = 2 * PI * v, b = PI * u;
        return [1.1 * Math.cos(a) * Math.sin(b), 1.1 * Math.cos(b), 1.1 * Math.sin(a) * Math.sin(b)];
      }, 12, 20, c.teal, {opacity: 0.6, stroke: c.teal});
      g.label([0, 1.36, 0], '1s · one phase', c.teal);
    } else {
      [1, -1].forEach(sign => {
        const color = sign > 0 ? c.teal : c.plum;
        g.mesh((u, v) => {
          // Sample the polar direction first so each tip face starts with
          // three distinct vertices. A collapsed first edge gave the visible
          // pole a false dark disk, easily mistaken for an additional node.
          const azimuth = 2 * PI * v;
          const polar = PI * u / 2;
          const radius = 1.65 * Math.pow(Math.cos(polar), 2);
          const axial = sign * radius * Math.cos(polar);
          const transverse = radius * Math.sin(polar);
          const point = [0, 0, 0];
          point[axis] = axial;
          point[(axis + 1) % 3] = transverse * Math.cos(azimuth);
          point[(axis + 2) % 3] = transverse * Math.sin(azimuth);
          return point;
        }, 12, 16, color, {opacity: 0.75, stroke: color});
        const label = [0, 0, 0]; label[axis] = sign * 1.6;
        label[(axis + 1) % 3] = 0.36;
        g.label(label, sign > 0 ? '+ phase' : '− phase', color);
      });
      if (showNode) {
        const plane = [[-1.1, -1.1], [1.1, -1.1], [1.1, 1.1], [-1.1, 1.1]].map(pair => {
          const point = [0, 0, 0];
          point[(axis + 1) % 3] = pair[0]; point[(axis + 2) % 3] = pair[1];
          return point;
        });
        g.polygon(plane, c.gold, {opacity: 0.2, stroke: c.gold});
        const label = [0, 0, 0], edge = [0, 0, 0];
        label[(axis + 1) % 3] = 1.28; label[(axis + 2) % 3] = -1.4;
        edge[(axis + 1) % 3] = 1.03; edge[(axis + 2) % 3] = -1.03;
        g.line([edge, label], c.gold, {width: 1});
        g.label(label, direction + ' = 0 · node', c.ink);
      }
    }
    g.sphere([0, 0, 0], 0.055, c.ink);
    return {
      readout: isS ? 'Hydrogen-like 1s: spherical symmetry; no radial or angular nodes. The phase is the same throughout. There is no nodal plane to show.' :
        'Hydrogen-like 2p' + direction + ': two lobes of one orbital, with opposite wavefunction signs. One angular node lies in the ' +
        ['yz', 'xz', 'xy'][axis] + ' plane (' + direction + ' = 0); no radial nodes. The nodal plane is ' + (showNode ? 'shown.' : 'hidden.'),
      legend: [{label: 'Positive wavefunction phase', color: c.teal},
        {label: 'Negative wavefunction phase', color: c.plum}, {label: 'Zero-probability nodal plane', color: c.gold}],
      note: 'Schematic probability-region boundaries, not exact isosurfaces or electron paths. The electron can be found outside the drawn surface. Shading shows surface orientation, not probability density. Colour indicates the sign (phase) of ψ, not electric charge; probability density is |ψ|² and is nonnegative. The three 2p orientations have the same energy in an isolated hydrogen-like atom.',
    };
  }

  function cell(state, g) {
    const c = g.colors;
    const explode = bounded(state.explode, 0, 100, 0) / 100;
    const cutaway = state.membrane !== 'closed';
    const focus = ['all', 'membrane', 'nucleus', 'mitochondria'].includes(state.focus) ? state.focus : 'all';
    const opacity = (part, base) => focus === 'all' || focus === part ? base : 0.16;
    const nucleus = [-0.36 - 0.64 * explode, 0.18 + 0.42 * explode, 0.72 * explode];
    const mitoCenters = [[0.57 + 0.75 * explode, 0.49 + 0.19 * explode, 0.35 + 0.6 * explode],
      [0.63 + 0.7 * explode, -0.55 - 0.18 * explode, -0.2 + 0.65 * explode]];
    // The section removes the front half (z > 0); no opaque disk closes it.
    g.mesh((u, v) => {
      const a = (cutaway ? PI : 0) + u * (cutaway ? PI : 2 * PI), b = PI * v;
      return [1.55 * Math.cos(a) * Math.sin(b), 1.25 * Math.cos(b), 1.1 * Math.sin(a) * Math.sin(b)];
    }, 18, 10, c.teal, {opacity: opacity('membrane', cutaway ? 0.18 : 0.27), stroke: c.teal});
    if (cutaway) {
      const rim = Array.from({length: 65}, (_, i) => [1.55 * Math.cos(i * PI / 32), 1.25 * Math.sin(i * PI / 32), 0]);
      g.line(rim, c.teal, {width: 3});
    }
    g.mesh((u, v) => {
      const a = 2 * PI * u, b = PI * v;
      return add(nucleus, [0.53 * Math.cos(a) * Math.sin(b), 0.53 * Math.cos(b), 0.53 * Math.sin(a) * Math.sin(b)]);
    }, 12, 8, c.plum, {opacity: opacity('nucleus', 0.55), stroke: c.plum});
    // DNA is a folded strand schematic inside the nuclear envelope.
    const dna = Array.from({length: 45}, (_, i) => {
      const t = i / 44;
      return add(nucleus, [0.24 * Math.sin(5 * PI * t), 0.7 * (t - 0.5), 0.15 * Math.cos(5 * PI * t)]);
    });
    g.line(dna, c.plum, {width: 3});
    mitoCenters.forEach(center => {
      // Outer membrane is translucent so the folded inner membrane is visible.
      g.mesh((u, v) => {
        const a = 2 * PI * u, b = PI * v;
        return add(center, [0.4 * Math.cos(a) * Math.sin(b), 0.2 * Math.cos(b), 0.2 * Math.sin(a) * Math.sin(b)]);
      }, 12, 6, c.gold, {opacity: opacity('mitochondria', 0.4), stroke: c.gold});
      const crista = Array.from({length: 49}, (_, i) => {
        const t = i / 48;
        return add(center, [0.65 * (t - 0.5), 0.12 * Math.sin(8 * PI * t), 0.04]);
      });
      g.line(crista, c.coral, {width: 3});
    });
    [[-0.9, -0.58, 0.2], [-0.64, -0.76, 0.12], [-0.31, -0.83, 0.3],
      [0.03, -0.72, 0.23], [0.24, 0.84, 0.08]].forEach(p => g.sphere(p, 0.045, c.blue));
    if (explode > 0) {
      g.line([[-0.36, 0.18, 0], nucleus], c.plum, {width: 1, dashed: true});
      [[0.57, 0.49, 0.35], [0.63, -0.55, -0.2]].forEach((p, i) =>
        g.line([p, mitoCenters[i]], c.gold, {width: 1, dashed: true}));
    }
    g.label([0.72, 1.55, 0], 'Plasma membrane', c.teal);
    g.line([[0.72, 1.4, 0], [0.65, 1.12, 0]], c.teal, {width: 1});
    const nucleusLabel = [-1.15, 1.25, 0.65];
    g.label(nucleusLabel, 'Nucleus · DNA', c.plum);
    g.line([add(nucleusLabel, [0, -0.08, 0]), add(nucleus, [0, 0.52, 0])], c.plum, {width: 1});
    const mitoLabel = add(mitoCenters[1], [0, -0.47, 0]);
    g.label(mitoLabel, 'Mitochondria · ATP', c.gold);
    g.line([add(mitoLabel, [0, 0.1, 0]), add(mitoCenters[1], [0, -0.2, 0])], c.gold, {width: 1});
    const functions = {
      all: 'Membrane: selective exchange. Nucleus: stores most cellular DNA and transcribes RNA. Mitochondria: generate ATP through oxidative phosphorylation at the inner membrane. Blue dots: cytosolic ribosomes make proteins.',
      membrane: 'The plasma membrane is a selective lipid-bilayer boundary. Transport proteins regulate which substances cross; it is not a rigid cell wall.',
      nucleus: 'The nuclear envelope encloses most cellular DNA. Transcription produces RNA; processed mRNA exits through nuclear pores for translation by ribosomes.',
      mitochondria: 'The outer membrane surrounds a folded inner membrane. Its cristae support respiration and ATP synthesis through oxidative phosphorylation; the folds increase membrane area.',
    };
    return {
      readout: 'Animal cell · ' + (cutaway ? 'front-half cutaway' : 'transparent complete membrane') +
        ' · separation ' + Math.round(explode * 100) + '%. ' + functions[focus],
      legend: [{label: 'Plasma membrane', color: c.teal}, {label: 'Nucleus / DNA', color: c.plum},
        {label: 'Mitochondrial outer membrane', color: c.gold}, {label: 'Inner-membrane folds', color: c.coral},
        {label: 'Cytosolic ribosomes', color: c.blue}],
      note: 'A simplified animal-cell cutaway: sizes, organelle numbers, membrane thickness and DNA folding are not to scale. Several organelles are omitted. Separation is an exploded teaching view, not a biological process; the membrane becomes transparent to keep internal structures visible.',
    };
  }

  window.PrimerSpatial.register({
    'chem.2.molecules': {
      initial: {molecule: 'water', domains: 'pairs'},
      controls: [
        {key: 'molecule', label: 'Molecule', options: [{value: 'water', label: 'Water · H₂O'},
          {value: 'ammonia', label: 'Ammonia · NH₃'}, {value: 'methane', label: 'Methane · CH₄'}]},
        {key: 'domains', label: 'Electron domains', options: [{value: 'pairs', label: 'Show lone-pair markers'},
          {value: 'bonds', label: 'Bonded atoms only'}]},
      ],
      build: molecularGeometry,
    },
    'chem.4.organic': {
      initial: {substituents: 'distinct', rotation: 0, layout: 'split'},
      controls: [
        {key: 'substituents', label: 'Substituents', options: [{value: 'distinct', label: 'H, F, Cl, Br · chiral'},
          {value: 'repeated', label: 'H, F, Cl, Cl · achiral'}]},
        {key: 'rotation', label: 'Rotate reflected molecule', min: 0, max: 360, step: 15, unit: '°'},
        {key: 'layout', label: 'Compare', options: [{value: 'split', label: 'Side by side'},
          {value: 'overlay', label: 'Overlay at common centre'}]},
      ],
      build: chirality,
    },
    'chem.4.quantum-chem': {
      camera: {yaw: -55, pitch: 18},
      initial: {orbital: '2pz', node: 'show'},
      controls: [
        {key: 'orbital', label: 'Atomic orbital', options: [{value: '1s', label: '1s · spherical'},
          {value: '2px', label: '2pₓ · x axis'}, {value: '2py', label: '2pᵧ · y axis'},
          {value: '2pz', label: '2p_z · z axis'}]},
        {key: 'node', label: 'Angular node', options: [{value: 'show', label: 'Show nodal plane'},
          {value: 'hide', label: 'Hide nodal plane'}]},
      ],
      build: orbital,
    },
    'bio.3.cell-bio': {
      initial: {explode: 0, membrane: 'cutaway', focus: 'all'},
      controls: [
        {key: 'explode', label: 'Separate organelles', min: 0, max: 100, step: 10, unit: '%'},
        {key: 'membrane', label: 'Membrane view', options: [{value: 'cutaway', label: 'Front-half cutaway'},
          {value: 'closed', label: 'Complete transparent membrane'}]},
        {key: 'focus', label: 'Explore function', options: [{value: 'all', label: 'Whole cell'},
          {value: 'membrane', label: 'Plasma membrane'}, {value: 'nucleus', label: 'Nucleus'},
          {value: 'mitochondria', label: 'Mitochondria'}]},
      ],
      build: cell,
    },
  });
}());
