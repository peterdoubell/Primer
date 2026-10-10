#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const lab = require('../web/physics-buoyancy-lab.js');
function close(a, b) { assert.ok(Math.abs(a - b) < 2e-11 * Math.max(1, Math.abs(a), Math.abs(b)), `${a} != ${b}`); }
let states = 0;
for (const volume of [50, 80, 100, 120, 150, 200]) for (const mass of [50, 120, 150, 200])
for (const density of [800, 1000, 1200]) for (const height of [5, 10, 15]) for (const gravity of [1, 9.81, 20])
for (const mode of ['predict', 'hold']) for (const depth of [0, 2, 5, 10, 15, 20]) {
  const m = lab.build({ volume, mass, density, height, gravity, mode, depth });
  const expectedDepth = mode === 'hold' ? depth : mass < density * volume / 1000
    ? 1000 * mass * height / (density * volume) : height + 2;
  const wet = expectedDepth < height ? expectedDepth : height;
  const displacedCm3 = volume * wet / height, force = density * displacedCm3 / 1e6 * gravity;
  close(m.depth, expectedDepth); close(m.immersedHeight, wet); close(m.displaced * 1e6, displacedCm3);
  close(m.weight, mass / 1000 * gravity); close(m.buoyancy, force);
  // Independent integration of gauge pressure over the horizontal faces, and the lateral pair.
  const area = (volume / height) / 1e4;
  const pressure = z => z < 0 ? 0 : density * gravity * z / 100;
  close(m.bottomPressure, pressure(expectedDepth)); close(m.topPressure, pressure(expectedDepth - height));
  close(m.pressureBuoyancy, area * (pressure(expectedDepth) - pressure(expectedDepth - height)));
  close(m.widthCm ** 2 * height, volume);
  close(m.holding + m.buoyancy - m.weight, mode === 'hold' ? 0 : m.imbalance);
  assert.ok(Math.abs(m.imbalance) <= 5 && Math.abs(m.holding) <= 5 && m.buoyancy <= 5 && m.weight <= 5);
  if (mode === 'predict' && mass <= density * volume / 1000) assert.equal(m.imbalance, 0);
  states++;
}
// Full-immersion buoyancy is independent of depth. A neutral body has no selected equilibrium depth.
for (const depth of [10, 12, 20]) {
  const m = lab.build({ ...lab.initial, volume: 120, mode: 'hold', depth });
  assert.equal(m.neutral, true); close(m.buoyancy, m.weight);
  assert.equal(m.equilibriumDepth, null);
}
const dry = lab.build({ ...lab.initial, mode: 'hold', depth: 0 });
assert.equal(dry.buoyancy, 0); close(dry.holding, dry.weight);
const underwater = lab.build({ ...lab.initial, mode: 'hold', depth: 20 });
assert.ok(underwater.holding < 0); assert.equal(underwater.direction, 'upward');
// Small literal DOM, so the shipped renderer's geometry is checked without evaluating filesystem text.
class Element {
  constructor(tag) { this.tagName = tag; this.nodeType = 1; this.attributes = {}; this.children = []; this.listeners = {}; this.value = ''; this.disabled = false;
    this.classList = { toggle: (key, on) => { const s = new Set((this.attributes.class || '').split(' ')); on ? s.add(key) : s.delete(key); this.attributes.class = [...s].join(' '); } }; }
  setAttribute(k, v) { this.attributes[k] = String(v); }
  getAttribute(k) { return this.attributes[k]; }
  append(...items) { this.children.push(...items); }
  replaceChildren(...items) { this.children = items; }
  addEventListener(k, fn) { this.listeners[k] = fn; }
  get textContent() { return this.children.map(x => x.textContent).join(''); }
  set textContent(v) { this.children = [{ nodeType: 3, textContent: String(v) }]; }
}
global.document = { createElement: tag => new Element(tag), createElementNS: (_ns, tag) => new Element(tag),
  createTextNode: v => ({ nodeType: 3, textContent: String(v) }) };
const root = lab.render({ props: { scenario: 'phys.0.float-sink.hydrostatics' } });
assert.ok(root); assert.equal(lab.render({ props: { scenario: 'phys.2.matter' } }), null);
function all(e) { return [e, ...(e.children || []).flatMap(x => x.nodeType === 1 ? all(x) : [])]; }
function find(key, value) { return all(root).find(e => e.attributes[key] === value); }
let mounts = 0;
function geometry() {
  const m = lab.build(JSON.parse(root.getAttribute('data-buoyancy-state')));
  const body = find('data-buoyancy-geometry', 'body'), submerged = find('data-buoyancy-geometry', 'submerged');
  close(Number(body.getAttribute('height')), 8 * m.state.height); close(Number(body.getAttribute('width')), 8 * m.widthCm);
  close(Number(body.getAttribute('y')), 198 + 8 * (m.depth - m.state.height));
  close(Number(submerged.getAttribute('height')), 8 * m.immersedHeight);
  close(Number(submerged.getAttribute('data-volume-cm3')), m.displaced * 1e6);
  for (const [key, force] of [['buoyancy', m.buoyancy], ['weight', -m.weight], ['holding', m.holding], ['release', m.imbalance]]) {
    const line = find('data-buoyancy-force', key);
    close(Number(line.getAttribute('y1')) - Number(line.getAttribute('y2')), 30 * force);
    close(Number(line.getAttribute('data-newtons')), force);
  }
  mounts++;
}
geometry();
find('data-buoyancy-mode', 'hold').listeners.click(); geometry();
for (const c of lab.controls) {
  const input = find('data-buoyancy-control', c.key);
  assert.equal(input.disabled, false);
  for (const value of [c.min, c.max]) { input.value = value; input.listeners.input(); geometry(); input.listeners.change(); }
}
for (const volume of [200, 80, 120]) { find('data-buoyancy-preset', String(volume)).listeners.click(); geometry(); }
assert.equal(find('data-buoyancy-control', 'depth').disabled, true);
find('data-buoyancy-action', 'reset').listeners.click(); assert.deepEqual(JSON.parse(root.getAttribute('data-buoyancy-state')), lab.initial);
find('data-buoyancy-action', 'enlarge').listeners.click(); assert.equal(find('data-buoyancy-action', 'enlarge').getAttribute('aria-pressed'), 'true');
global.window = { PrimerPhysicsBuoyancyLab: lab };
require('../web/spatial-models.js'); require('../web/spatial-module-objects.js');
const item = { props: { scenario: 'module.phys.0.float-sink', family: 'buoyant-prism', mode: 'model',
  context: 'Source physical prism.', lesson: 'Floating and Sinking' } };
assert.ok(window.PrimerModuleObjects.ensure(item));
const cross = (a,b) => [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
function orientedVolume(faces) {
  let v = 0;
  for (const face of faces) for (let i = 1; i + 1 < face.points.length; i++) {
    const n = cross(face.points[i], face.points[i+1]);
    v += face.points[0].reduce((total, p, j) => total + p*n[j], 0)/6;
  }
  return v;
}
let spatialStates = 0;
for (const volume of [50, 120, 200]) for (const height of [5, 10, 15]) for (const depth of [0, 2, 5, 10, 15, 20]) {
  const scene = window.PrimerSpatial.build(item.props.scenario, { volume, height, depth });
  const faces = scene.primitives.filter(p => ['wet','dry','top','bottom'].includes(p.buoyancy_surface));
  const points = faces.flatMap(f=>f.points);
  const width = Math.sqrt(volume / height);
  close(1000 * orientedVolume(faces), volume);
  close(10 * (Math.max(...points.map(p=>p[1]))-Math.min(...points.map(p=>p[1]))), height);
  for (const axis of [0,2]) close(10*(Math.max(...points.map(p=>p[axis]))-Math.min(...points.map(p=>p[axis]))), width);
  const wet = faces.filter(f=>f.buoyancy_surface==='wet' || (f.buoyancy_surface==='bottom'&&depth>0) || (f.buoyancy_surface==='top'&&depth>=height));
  close(1000 * orientedVolume(wet), volume * Math.min(depth/height,1));
  close(scene.hydrostatics.displaced*1e6,1000*orientedVolume(wet));
  for (const [key, value] of [['buoyancy',scene.hydrostatics.buoyancy],['weight',-scene.hydrostatics.weight],['holding',scene.hydrostatics.holding]]) {
    const shaft=scene.primitives.filter(p=>p.kind==='line'&&p.buoyancy_force===key);
    if (Math.abs(value) < 1e-8) { assert.equal(shaft.length,0); continue; }
    assert.equal(shaft.length,12);
    close(shaft.at(-1).points[1][1]-shaft[0].points[0][1],.15*value);
  }
  spatialStates++;
}
console.log(`Verified ${states} hydrostatic states, ${mounts} mounted geometries and ${spatialStates} closed 3D volumes; SI pressure-force integration, immersion, neutral depths, fixed-scale arrows, controls and resets passed.`);
