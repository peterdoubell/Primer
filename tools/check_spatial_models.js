#!/usr/bin/env node
'use strict';

// Exercise the shipped scene builders and geometry engine directly, without a DOM.
const assert = require('assert/strict');
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
// This executable owns its fake browser globals. Load only these fixed, shipped
// modules through Node's module loader; no file contents become executable input.
const context = { window: {} };
globalThis.window = context.window;
require('../web/spatial-models.js');
require('../web/spatial-math.js');
require('../web/spatial-physical.js');
require('../web/spatial-molecular.js');
require('../web/spatial-cross-subject.js');
require('../web/spatial-radiology.js');
const api = context.window.PrimerSpatial;
const expected = ['math.2.geometry', 'math.3.vectors', 'math.4.multivar', 'math.5.topology',
  'phys.4.em-maxwell', 'phys.4.solid-state', 'earth.1.seasons', 'earth.3.earth-science',
  'chem.2.molecules', 'chem.4.organic', 'chem.4.quantum-chem', 'bio.3.cell-bio',
  'arts.2.color-theory', 'cs.5.quantum', 'rad.3.ct-image', 'rad.5.tavi-ct', 'rad.3.fracture-description'].sort();
assert.equal(JSON.stringify([...api.supported].sort()), JSON.stringify(expected));
const nodes = fs.readdirSync(path.join(ROOT, 'data/curriculum')).filter(file => /^\d.*\.json$/.test(file))
  .flatMap(file => JSON.parse(fs.readFileSync(path.join(ROOT, 'data/curriculum', file), 'utf8')).nodes);
const entries = nodes.flatMap(node => (node.lesson_media || []).filter(item => item.renderer === 'spatial-3d')
  .map(item => ({ node, item })));
assert.equal(entries.length, expected.length, 'Every spatial scene must be reachable from its curriculum lesson');
assert.equal(JSON.stringify(entries.map(({ node }) => node.id).sort()), JSON.stringify(expected));
entries.forEach(({ node, item }) => assert.deepEqual(item.props, { scenario: node.id }));
assert.equal(nodes.flatMap(node => node.lesson_media || []).filter(item => item.kind === 'model' &&
  !['spatial-3d', 'concept-lab', 'music-listening-lab', 'doppler-angle-lab'].includes(item.renderer)).length,
  70, 'The 70 existing lesson models must remain present');
assert.equal(nodes.flatMap(node => node.lesson_media || []).filter(item => item.renderer === 'music-listening-lab').length,
  8, 'The eight music grade listening models must remain present');
assert.equal(nodes.flatMap(node => node.lesson_media || []).filter(item => item.renderer === 'doppler-angle-lab').length,
  1, 'The ultrasound Doppler model must remain present');

const C = { blue: '#3e7085', teal: '#317e78', gold: '#b98a2f', coral: '#b96652', plum: '#876888', green: '#5c7754', ink: '#263b46' };
const near = (a, b, tolerance = 1e-7) => assert.ok(Math.abs(a - b) <= tolerance, `${a} differs from ${b}`);
const sub = (a, b) => a.map((v, i) => v - b[i]);
const dot = (a, b) => a.reduce((sum, v, i) => sum + v * b[i], 0);
const norm = a => Math.hypot(...a);
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const primitives = (scene, kind, color) => scene.primitives.filter(p => p.kind === kind && (!color || p.color === color));
const teaching = scene => JSON.stringify({ primitives: scene.primitives, readout: scene.readout, note: scene.note, legend: scene.legend });
let scenarioChecks = 0;
let controlChecks = 0;
function verify(id, supplied) {
  const scene = api.build(id, supplied);
  assert.ok(scene.primitives.length > 0 && scene.primitives.length <= 3000, id + ': geometry budget');
  assert.equal(JSON.stringify(scene), JSON.stringify(api.build(id, supplied)), id + ': deterministic rebuild');
  assert.ok(typeof scene.readout === 'string' && scene.readout.trim());
  assert.ok(typeof scene.note === 'string' && scene.note.trim());
  assert.ok(scene.legend.length > 0);
  scene.primitives.forEach(p => {
    assert.ok(['polygon', 'line', 'sphere', 'label'].includes(p.kind));
    assert.ok(p.points.length > 0);
    p.points.forEach(point => assert.ok(point.length === 3 && point.every(Number.isFinite), id + ': finite coordinates'));
    if (p.kind === 'sphere') assert.ok(Number.isFinite(p.radius) && p.radius > 0);
    if (p.opacity != null) assert.ok(Number.isFinite(p.opacity) && p.opacity >= 0 && p.opacity <= 1);
    if (p.width != null) assert.ok(Number.isFinite(p.width) && p.width > 0);
  });
  scenarioChecks += 1;
  return scene;
}
for (const id of expected) {
  const initial = verify(id);
  for (const control of api.controls(id)) {
    const values = control.options ? control.options.map(o => o.value) : [control.min, (control.min + control.max) / 2, control.max];
    const versions = values.map(value => verify(id, { ...initial.state, [control.key]: value }));
    assert.ok(versions.some(scene => teaching(scene) !== teaching(initial)), id + ': ' + control.key + ' must change the explanation or geometry');
    if (!control.options) {
      for (const invalid of [NaN, Infinity, -Infinity, 'not a number']) {
        assert.equal(JSON.stringify(verify(id, { [control.key]: invalid })), JSON.stringify(initial));
      }
    }
    controlChecks += 1;
  }
  console.log('COVER ' + id);
}
for (const id of ['missing', 'constructor', 'toString', '__proto__', null]) {
  assert.equal(api.build(id), null);
  assert.equal(api.render({ props: { scenario: id } }), null);
  assert.equal(api.controls(id).length, 0);
}
// Camera rotation must preserve distances, dot products, and orientation.
for (const yaw of [-180, -28, 0, 90, 180]) for (const pitch of [-85, 0, 18, 85]) {
  const camera = { yaw, pitch, zoom: 1 };
  const basis = [[1, 0, 0], [0, 1, 0], [0, 0, 1]].map(p => api.rotate(p, camera));
  basis.forEach(p => near(norm(p), 1));
  near(dot(basis[0], basis[1]), 0);
  near(dot(cross(basis[0], basis[1]), basis[2]), 1);
}

// Unit-cube geometry establishes volume independently of the displayed formula.
for (const dims of [[1, 1, 1], [4, 3, 2], [4, 4, 4]]) for (const view of ['solid', 'layers']) {
  const [length, width, height] = dims;
  const scene = verify('math.2.geometry', { length, width, height, view });
  const faces = primitives(scene, 'polygon');
  assert.equal(faces.length / 6, length * width * height);
  for (let i = 0; i < faces.length; i += 6) {
    const points = faces.slice(i, i + 6).flatMap(p => p.points);
    [0, 1, 2].forEach(axis => near(Math.max(...points.map(p => p[axis])) - Math.min(...points.map(p => p[axis])), 0.58));
  }
}
function arrowVector(scene, color) {
  const shafts = primitives(scene, 'line', color).filter(p => p.width === 4);
  return shafts.length ? sub(shafts.at(-1).points.at(-1), shafts[0].points[0]) : [0, 0, 0];
}
for (const angle of [-180, -90, -30, 0, 60, 90, 180]) {
  const scene = verify('math.3.vectors', { length: 1.2, angle });
  const a = arrowVector(scene, C.blue), b = arrowVector(scene, C.coral);
  const result = arrowVector(scene, C.teal), normal = arrowVector(scene, C.plum);
  [0, 1, 2].forEach(i => { near(result[i], a[i] + b[i]); near(normal[i], cross(a, b)[i] / 0.76); });
  near(dot(normal, a), 0); near(dot(normal, b), 0);
}
for (const x of [-1, 0, 1]) for (const y of [-1, 0.4, 1]) for (const step of [-0.8, 0, 0.4, 0.8]) {
  const scene = verify('math.4.multivar', { x, y, step });
  const q = primitives(scene, 'sphere', C.teal)[0].points[0];
  const l = primitives(scene, 'sphere', C.gold)[0].points[0];
  const worldX = q[0] / 0.82, worldY = -q[2] / 0.82;
  near((q[1] + 0.65) / 0.82, (worldX ** 2 + worldY ** 2) / 4);
  near((q[1] - l[1]) / 0.82, step ** 2 / 4);
  primitives(scene, 'polygon', C.gold)[0].points.forEach(point => {
    near((point[1] + 0.65) / 0.82, (x * x + y * y) / 4 + x / 2 * (point[0] / 0.82 - x) + y / 2 * (-point[2] / 0.82 - y));
  });
}
// Count Euler characteristic from actual welded mesh vertices, edges, and faces.
function euler(scene) {
  const vertices = new Set(), edges = new Set(); let faces = 0;
  primitives(scene, 'polygon').forEach(face => {
    const ids = face.points.map(point => point.map(v => Math.round(v * 1e6)).join(','));
    const unique = [...new Set(ids)];
    if (unique.length < 3) return;
    unique.forEach(id => vertices.add(id));
    unique.forEach((id, i) => edges.add([id, unique[(i + 1) % unique.length]].sort().join('|')));
    faces += 1;
  });
  return vertices.size - edges.size + faces;
}
for (const surface of ['sphere', 'torus']) for (const stretch of [0.6, 1, 1.6]) {
  assert.equal(euler(verify('math.5.topology', { surface, stretch })), surface === 'sphere' ? 2 : 0);
}

for (const time of [0, 0.25, 0.5, 0.75]) for (const polarization of [0, 45, 90]) {
  const scene = verify('phys.4.em-maxwell', { time, polarization });
  const e = primitives(scene, 'line', C.coral).find(p => p.points.length > 100).points;
  const b = primitives(scene, 'line', C.blue).find(p => p.points.length > 100).points;
  e.forEach((point, i) => {
    const ev = [0, point[1], point[2]], bv = [0, b[i][1], b[i][2]];
    near(point[0], b[i][0]); near(norm(ev), norm(bv)); near(dot(ev, bv), 0);
    assert.ok(cross(ev, bv)[0] >= -1e-10, 'Energy must travel along +x');
  });
  const center = e[Math.floor(e.length / 2)];
  near(center[1], -0.68 * Math.sin(2 * Math.PI * time) * Math.cos(polarization * Math.PI / 180));
  near(center[2], -0.68 * Math.sin(2 * Math.PI * time) * Math.sin(polarization * Math.PI / 180));
}
for (const [lattice, count] of [['sc', 1], ['bcc', 2], ['fcc', 4]]) {
  const scene = verify('phys.4.solid-state', { lattice, view: 'touching' });
  const sites = primitives(scene, 'sphere');
  const effective = sites.reduce((sum, p) => sum + 1 / 2 ** p.points[0].filter(v => Math.abs(Math.abs(v) - 0.82) < 1e-8).length, 0);
  near(effective, count);
  const distances = sites.flatMap((site, i) => sites.slice(i + 1).map(other => norm(sub(site.points[0], other.points[0]))));
  near(Math.min(...distances), 2 * sites[0].radius);
}
let fixedAxis;
for (const orbit of [0, 90, 180, 270, 360]) for (const latitude of ['45', '-45', '0']) {
  const scene = verify('earth.1.seasons', { orbit, latitude });
  const shafts = primitives(scene, 'line', C.plum);
  const axis = sub(shafts.at(-1).points.at(-1), shafts[0].points[0]);
  if (fixedAxis) axis.forEach((v, i) => near(v, fixedAxis[i])); else fixedAxis = axis;
  near(Math.acos(axis[1] / norm(axis)) * 180 / Math.PI, 23.4);
  const surface = primitives(scene, 'polygon').filter(p => [C.teal, C.blue, C.ink].includes(p.color)).flatMap(p => p.points);
  const center = [0, 1, 2].map(axis => surface.reduce((sum, p) => sum + p[axis], 0) / surface.length);
  near(norm(center), 1.4);
  const day = Number(scene.readout.match(/≈ ([\d.]+) hours/)[1]);
  const expectedHours = latitude === '0' || orbit % 180 === 90 ? 12 : (orbit % 360 === 0) === (latitude === '45') ? 15.4 : 8.6;
  near(day, expectedHours, 0.05);
}
for (const opening of [30, 100, 160]) {
  const scene = verify('earth.3.earth-science', { opening });
  for (const [color, km] of [[C.plum, 1221], [C.coral, 3480], [C.gold, 6336], [C.green, 6371]]) {
    const maxRadius = Math.max(...primitives(scene, 'polygon', color).flatMap(p => p.points).map(norm));
    near(maxRadius / 1.42 * 6371, km);
  }
}
for (const [molecule, count, degrees] of [['water', 2, 104.5], ['ammonia', 3, 107], ['methane', 4, Math.acos(-1 / 3) * 180 / Math.PI]]) {
  const scene = verify('chem.2.molecules', { molecule, domains: 'bonds' });
  const hydrogens = primitives(scene, 'sphere', C.blue).filter(p => norm(p.points[0]) > 1).map(p => p.points[0]);
  assert.equal(hydrogens.length, count);
  hydrogens.forEach((p, i) => hydrogens.slice(i + 1).forEach(q => near(Math.acos(dot(p, q) / norm(p) / norm(q)) * 180 / Math.PI, degrees)));
}
for (const substituents of ['distinct', 'repeated']) {
  const scene = verify('chem.4.organic', { substituents, rotation: 0, layout: 'overlay' });
  const spheres = primitives(scene, 'sphere').filter(p => norm(p.points[0]) > 1);
  const original = spheres.filter(p => p.opacity < 1), reflected = spheres.filter(p => p.opacity === 1);
  const matches = reflected.filter(p => original.some(q => p.color === q.color && norm(sub(p.points[0], q.points[0])) < 1e-8)).length;
  assert.equal(matches, substituents === 'distinct' ? 2 : 4);
  if (substituents === 'distinct') {
    const volumeSign = points => Math.sign(dot(sub(points[0], points[3]), cross(sub(points[1], points[3]), sub(points[2], points[3]))));
    assert.equal(volumeSign(original.map(p => p.points[0])), -volumeSign(reflected.map(p => p.points[0])));
  }
}
for (const orbital of ['2px', '2py', '2pz']) {
  const axis = { '2px': 0, '2py': 1, '2pz': 2 }[orbital];
  const scene = verify('chem.4.quantum-chem', { orbital, node: 'show' });
  primitives(scene, 'polygon', C.gold).flatMap(p => p.points).forEach(p => near(p[axis], 0));
  primitives(scene, 'polygon', C.teal).flatMap(p => p.points).forEach(p => assert.ok(p[axis] >= -1e-8));
  primitives(scene, 'polygon', C.plum).flatMap(p => p.points).forEach(p => assert.ok(p[axis] <= 1e-8));
}
const spherical = verify('chem.4.quantum-chem', { orbital: '1s', node: 'show' });
assert.equal(primitives(spherical, 'polygon', C.gold).length, 0);
primitives(spherical, 'polygon', C.teal).flatMap(p => p.points).forEach(p => near(norm(p), 1.1));
const cutCell = verify('bio.3.cell-bio', { explode: 0, membrane: 'cutaway' });
primitives(cutCell, 'polygon', C.teal).flatMap(p => p.points).forEach(p => assert.ok(p[2] <= 1e-8));
const closedCell = verify('bio.3.cell-bio', { membrane: 'closed' });
assert.ok(primitives(closedCell, 'polygon', C.teal).some(p => p.points.some(point => point[2] > 0.5)));

console.log(`Verified ${expected.length} spatial models, ${controlChecks} meaningful controls, ${scenarioChecks} finite deterministic builds, and scientific geometry invariants.`);

// Radiology: validate actual section geometry, not only readout strings.
for (const plane of ['axial', 'coronal', 'sagittal']) {
  const axis = { axial: 1, coronal: 2, sagittal: 0 }[plane];
  for (const position of [-.6, 0, .6, 1]) {
    const section = api.build('rad.3.ct-image', { plane, position });
    const contours = primitives(section, 'line', C.coral);
    assert.equal(contours.length, Math.abs(position) < .65 ? 1 : 0);
    contours.flatMap(p => p.points).forEach(p => { near(p[axis], position); near(norm(p), .65); });
  }
}
for (const tilt of [0, 30, 60]) {
  const section = api.build('rad.5.tavi-ct', { tilt });
  const diameter = primitives(section, 'line', C.coral).find(p => p.points.length === 2);
  near(norm(sub(...diameter.points)), 1.1 / Math.cos(tilt * Math.PI / 180));
  primitives(section, 'line', C.coral).flatMap(p => p.points).forEach(p => {
    near(Math.hypot(p[0], p[2]), .55);
    near(p[1], p[0] * Math.tan(tilt * Math.PI / 180));
  });
}
for (const direction of ['lateral', 'anterior']) {
  const scene = api.build('rad.3.fracture-description', { translation: 1, angle: 40, direction });
  const faces = primitives(scene, 'polygon', C.coral);
  // The fracture face centre translates exactly one shaft width, independent of angle.
  const centre = faces[2].points.reduce((sum,p) => sum.map((v,i) => v+p[i]/4), [0,0,0]);
  near(centre[direction === 'lateral' ? 0 : 2], .4);
  near(centre[1], -.08);
}
console.log('Verified radiology section, obliquity and fragment-position invariants.');
