#!/usr/bin/env node
'use strict';

// Inspect the shipped three dedicated physics renderers. Physical oracles use
// actual SVG endpoints, not copied ray/flow implementations or changing text.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { FakeDocument, descendants, hasClass, one } = require('./check_remaining_models.js');
global.document = new FakeDocument();
global.window = {};
require('../web/lesson-models.js');
const curriculum = JSON.parse(fs.readFileSync(path.join(__dirname, '../data/curriculum/03-physics.json'), 'utf8'));
let checks = 0;
const close = (actual, expected, tolerance = 1e-10) => {
  checks += 1;
  assert.ok(Number.isFinite(actual) && Math.abs(actual - expected) <= tolerance,
    `expected ${expected}, got ${actual}`);
};
const mount = id => {
  const lesson = curriculum.nodes.find(node => node.id === id);
  assert.ok(lesson, 'actual lesson binding exists');
  const item = lesson.lesson_media.find(media => media.kind === 'model');
  const root = window.PrimerLessonModels.render(item, {});
  assert.ok(root, 'shipped dedicated renderer mounted');
  return root;
};
const click = (root, label) => one(root, n => n.tagName === 'button' && n.textContent === label, label).dispatch('click');
const attr = (node, name) => Number(node.getAttribute(name));
const readout = root => one(root, n => hasClass(n, 'model-readout'), 'readout').textContent;
const line = node => [[attr(node, 'x1'), attr(node, 'y1')], [attr(node, 'x2'), attr(node, 'y2')]];
const unit = vector => vector.map(x => x / Math.hypot(...vector));
const cross = (a, b) => a[0] * b[1] - a[1] * b[0];

const shadow = mount('phys.0.light-shadow');
const shadowStart = readout(shadow);
const position = one(shadow, n => n.tagName === 'input', 'position control');
for (let p = 0; p <= 100; p++) {
  position.value = String(p); position.dispatch('input');
  const card = one(shadow, n => n.hasAttribute('data-shadow-blocker'), 'actual opaque rectangle');
  const translated = Number(card.parentNode.getAttribute('transform').match(/translate\(([^ ]+)/)[1]);
  const front = translated + attr(card, 'x');
  const cast = one(shadow, n => hasClass(n, 'shadow-cast'), 'cast shadow');
  const screen = one(shadow, n => hasClass(n, 'shadow-screen'), 'screen');
  const rays = descendants(shadow, n => hasClass(n, 'shadow-ray'));
  assert.equal(rays.length, 2);
  rays.forEach((ray, index) => {
    const [[sx, sy], [ex, ey]] = line(ray);
    const intersection = sy + (ey - sy) * (front - sx) / (ex - sx);
    close(intersection, attr(card, 'y') + index * attr(card, 'height'));
    close(ex, attr(screen, 'x'));
  });
  close(attr(cast, 'y'), attr(rays[0], 'y2'));
  close(attr(cast, 'height'), attr(rays[1], 'y2') - attr(rays[0], 'y2'));
  close(attr(cast, 'height') / attr(card, 'height'),
    (attr(screen, 'x') - attr(rays[0], 'x1')) / (front - attr(rays[0], 'x1')));
  assert.ok(attr(cast, 'y') >= attr(screen, 'y') &&
    attr(cast, 'y') + attr(cast, 'height') <= attr(screen, 'y') + attr(screen, 'height'));
}
click(shadow, 'Turn lamp off');
descendants(shadow, n => hasClass(n, 'shadow-ray') || hasClass(n, 'shadow-cast')).forEach(n => assert.equal(n.style.display, 'none'));
click(shadow, 'Reset');
assert.equal(readout(shadow), shadowStart);

const venturi = mount('phys.4.fluids');
const venturiStart = readout(venturi);
for (const [label, area] of [['Full area (4 cm²)', 4], ['Half area (2 cm²)', 2], ['Quarter area (1 cm²)', 1]]) {
  click(venturi, label);
  const shafts = ['inlet', 'throat', 'outlet'].map(role => one(venturi,
    n => n.getAttribute('data-venturi-speed') === role, role + ' velocity'));
  const speeds = shafts.map(n => (attr(n, 'x2') - attr(n, 'x1')) / 20);
  close(speeds[0], 1); close(speeds[2], 1); close(speeds[1] * area * 100, 400);
  const walls = descendants(venturi, n => hasClass(n, 'venturi-wall')).map(n =>
    n.getAttribute('d').match(/-?\d+(?:\.\d+)?/g).map(Number));
  assert.equal(walls.length, 2);
  const wideDiameter = walls[1][1] - walls[0][1];
  const throatDiameter = walls[1][5] - walls[0][5];
  close((throatDiameter / wideDiameter) ** 2, area / 4);
  const columns = ['inlet', 'throat', 'outlet'].map(role => one(venturi,
    n => n.getAttribute('data-venturi-head') === role, role + ' head'));
  const heads = columns.map(n => (attr(n, 'y1') - attr(n, 'y2')) / 60);
  close(heads[0] * 1000 * 9.81, 16500); close(heads[2], heads[0]);
  close((heads[0] - heads[1]) * 1000 * 9.81,
    .5 * 1000 * (speeds[1] ** 2 - speeds[0] ** 2));
  close(attr(columns[0], 'y1'), attr(columns[1], 'y1'));
}
click(venturi, 'Reset'); assert.equal(readout(venturi), venturiStart);

const optics = mount('phys.1.light');
const opticsStart = readout(optics);
const choice = one(optics, n => n.tagName === 'input' && n.getAttribute('aria-label') === 'Prism light', 'spectrum choice');
// Independent source table: SCHOTT N-BK7 optical datasheet, wavelengths in nm.
const source = [[706.5,1.51289],[643.8,1.51472],[589.3,1.51673],[546.1,1.51872],
  [486.1,1.52238],[435.8,1.52668],[404.7,1.53024]];
for (let selection = 0; selection <= 7; selection++) {
  choice.value = String(selection); choice.dispatch('input');
  const internals = descendants(optics, n => n.getAttribute('data-optical-segment') === 'internal');
  assert.equal(internals.length, selection === 0 ? 7 : 1);
  const incident = one(optics, n => hasClass(n, 'light-white-ray'), 'incoming ray');
  const screen = one(optics, n => hasClass(n, 'light-screen'), 'optical screen');
  for (const internal of internals) {
    const lambda = attr(internal, 'data-optical-wavelength'), index = attr(internal, 'data-optical-index');
    const sourceRow = source.find(row => row[0] === lambda);
    assert.ok(sourceRow); close(index, sourceRow[1], 0);
    const outgoing = one(optics, n => n.getAttribute('data-optical-segment') === 'outgoing' &&
      attr(n, 'data-optical-wavelength') === lambda, 'outgoing ray');
    const [entry, exit] = line(internal), [joined, end] = line(outgoing);
    close(entry[0], attr(incident, 'x2')); close(entry[1], attr(incident, 'y2'));
    close(exit[0], joined[0]); close(exit[1], joined[1]);
    close(entry[1], 58 - 164 / 50 * (entry[0] - 320));
    close(exit[1], 58 + 164 / 50 * (exit[0] - 320));
    const air = unit([entry[0] - attr(incident, 'x1'), entry[1] - attr(incident, 'y1')]);
    const glass = unit(exit.map((x, i) => x - entry[i]));
    const emerging = unit(end.map((x, i) => x - exit[i]));
    close(Math.abs(cross(air, unit([164,50]))), index * Math.abs(cross(glass, unit([164,50]))));
    close(index * Math.abs(cross(glass, unit([164,-50]))), Math.abs(cross(emerging, unit([164,-50]))));
    close(end[0], attr(screen, 'x'));
    assert.ok(end[1] >= attr(screen, 'y') && end[1] <= attr(screen, 'y') + attr(screen, 'height'));
  }
}
click(optics, 'Mirror');
const incomingMirror = one(optics, n => hasClass(n, 'light-white-ray'), 'mirror incident');
const reflected = one(optics, n => hasClass(n, 'light-reflected-ray'), 'mirror reflected');
const [start, hit] = line(incomingMirror), [same, end] = line(reflected);
close(hit[0], same[0]); close(hit[1], same[1]);
close((hit[1] - start[1]) / (hit[0] - start[0]), -(end[1] - hit[1]) / (end[0] - hit[0]));
click(optics, 'Toy');
const toy = one(optics, n => hasClass(n, 'light-toy'), 'opaque toy');
const toyIncoming = one(optics, n => hasClass(n, 'light-white-ray'), 'toy incident');
descendants(optics, n => hasClass(n, 'light-reflected-ray') || hasClass(n, 'light-scatter-ray')).forEach(n => {
  close(attr(n, 'x1'), attr(toy, 'x')); close(attr(n, 'x1'), attr(toyIncoming, 'x2'));
  close(attr(n, 'y1'), attr(toyIncoming, 'y2'));
  assert.ok(attr(n, 'x2') < attr(toy, 'x'), 'reflected ray remains in illuminated outward half-space');
});
click(optics, 'Reset'); assert.equal(readout(optics), opticsStart); assert.equal(choice.value, '0');
console.log(`Dedicated physics fidelity passed: ${checks} quantitative assertions; 101 shadow positions, three Venturi geometries, eight prism states, mirror/toy paths and resets.`);
