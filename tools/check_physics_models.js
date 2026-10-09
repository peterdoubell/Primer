#!/usr/bin/env node
'use strict';

/*
 * Deterministic DOM smoke check for the lesson-bound physics models.
 *
 * This deliberately avoids a browser and third-party DOM packages.  The fake
 * DOM implements only the primitives used while constructing and operating a
 * physics-concept-lab.  It executes the shipped renderer, not a copied model
 * implementation, and treats SVG text as commentary rather than geometry.
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const CURRICULUM_PATH = path.join(ROOT, 'data', 'curriculum', '03-physics.json');
const EXPECTED_SCENARIO_COUNT = 36;

class FakeStyle {
  constructor() {
    this.properties = new Map();
  }

  setProperty(name, value) {
    this.properties.set(String(name), String(value));
  }

  getPropertyValue(name) {
    return this.properties.get(String(name)) || '';
  }
}

class FakeClassList {
  constructor(owner) {
    this.owner = owner;
  }

  values() {
    return new Set(this.owner.className.split(/\s+/).filter(Boolean));
  }

  write(values) {
    this.owner.className = [...values].join(' ');
  }

  add(...names) {
    const values = this.values();
    names.forEach(name => values.add(String(name)));
    this.write(values);
  }

  remove(...names) {
    const values = this.values();
    names.forEach(name => values.delete(String(name)));
    this.write(values);
  }

  contains(name) {
    return this.values().has(String(name));
  }

  toggle(name, force) {
    const values = this.values();
    const present = values.has(String(name));
    const next = force === undefined ? !present : Boolean(force);
    if (next) values.add(String(name));
    else values.delete(String(name));
    this.write(values);
    return next;
  }
}

class FakeTextNode {
  constructor(value) {
    this.nodeType = 3;
    this.parentNode = null;
    this.data = String(value);
  }

  get textContent() {
    return this.data;
  }

  set textContent(value) {
    this.data = String(value);
  }
}

class FakeElement {
  querySelectorAll(selector) {
    const found = [];
    const visit = parent => parent.children.forEach(child => {
      if (child.nodeType !== 1) return;
      if (selector.startsWith('.') ? child.classList.contains(selector.slice(1)) : child.tagName === selector) found.push(child);
      visit(child);
    });
    visit(this);
    return found;
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  constructor(tagName, namespaceURI = null) {
    this.nodeType = 1;
    this.tagName = String(tagName).toLowerCase();
    this.namespaceURI = namespaceURI;
    this.parentNode = null;
    this.children = [];
    this.attributes = new Map();
    this.listeners = new Map();
    this.style = new FakeStyle();
    this._className = '';
    this.value = '';
    this.min = '';
    this.max = '';
    this.step = '';
    this.type = '';
    this.id = '';
    this.classList = new FakeClassList(this);
  }

  get className() {
    return this._className;
  }

  set className(value) {
    this._className = String(value);
    if (this._className) this.attributes.set('class', this._className);
    else this.attributes.delete('class');
  }

  setAttribute(name, value) {
    const key = String(name);
    const text = String(value);
    this.attributes.set(key, text);
    if (key === 'class') this._className = text;
    else if (key === 'value') this.value = text;
    else if (key === 'min') this.min = text;
    else if (key === 'max') this.max = text;
    else if (key === 'step') this.step = text;
    else if (key === 'type') this.type = text;
    else if (key === 'id') this.id = text;
  }

  getAttribute(name) {
    const key = String(name);
    return this.attributes.has(key) ? this.attributes.get(key) : null;
  }

  hasAttribute(name) {
    return this.attributes.has(String(name));
  }

  removeAttribute(name) {
    const key = String(name);
    this.attributes.delete(key);
    if (key === 'class') this._className = '';
  }

  addEventListener(type, listener) {
    const key = String(type);
    if (!this.listeners.has(key)) this.listeners.set(key, []);
    this.listeners.get(key).push(listener);
  }

  dispatch(type) {
    const event = {
      type: String(type),
      target: this,
      currentTarget: this,
      defaultPrevented: false,
      preventDefault() { this.defaultPrevented = true; },
    };
    (this.listeners.get(event.type) || []).forEach(listener => listener.call(this, event));
    return !event.defaultPrevented;
  }

  append(...values) {
    values.forEach(value => {
      const child = value && value.nodeType ? value : new FakeTextNode(value);
      if (child.parentNode) {
        const index = child.parentNode.children.indexOf(child);
        if (index >= 0) child.parentNode.children.splice(index, 1);
      }
      child.parentNode = this;
      this.children.push(child);
    });
  }

  prepend(...values) {
    const additions = values.map(value => value && value.nodeType ? value : new FakeTextNode(value));
    additions.forEach(child => { child.parentNode = this; });
    this.children.unshift(...additions);
  }

  replaceChildren(...values) {
    this.children.forEach(child => { child.parentNode = null; });
    this.children = [];
    this.append(...values);
  }

  get textContent() {
    return this.children.map(child => child.textContent).join('');
  }

  set textContent(value) {
    this.replaceChildren();
    if (value !== '') this.append(new FakeTextNode(value));
  }
}

class FakeDocument {
  createElement(tagName) {
    return new FakeElement(tagName);
  }

  createElementNS(namespaceURI, tagName) {
    return new FakeElement(tagName, namespaceURI);
  }

  createTextNode(value) {
    return new FakeTextNode(value);
  }
}

function descendants(root, predicate) {
  const found = [];
  function visit(node) {
    if (node && node.nodeType === 1 && predicate(node)) found.push(node);
    if (node && node.children) node.children.forEach(visit);
  }
  visit(root);
  return found;
}

function hasClass(node, name) {
  return node.nodeType === 1 && node.classList.contains(name);
}

function one(root, predicate, description) {
  const matches = descendants(root, predicate);
  if (matches.length !== 1) {
    throw new Error('expected exactly one ' + description + ', found ' + matches.length);
  }
  return matches[0];
}

function serializeGeometry(node) {
  if (!node || node.nodeType !== 1 || node.tagName === 'text') return '';
  const attributes = [...node.attributes.entries()]
    .filter(([name]) => !name.startsWith('aria-') && name !== 'focusable')
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([name, value]) => name + '=' + JSON.stringify(value))
    .join(' ');
  const children = node.children.map(serializeGeometry).join('');
  return '<' + node.tagName + (attributes ? ' ' + attributes : '') + '>' +
    children + '</' + node.tagName + '>';
}

function collectPhysicsModels(curriculum) {
  const models = [];
  const seen = new Set();
  for (const lesson of curriculum.nodes || []) {
    for (const media of lesson.lesson_media || []) {
      if (media.kind !== 'model' || media.renderer !== 'physics-concept-lab') continue;
      const scenario = media.props && media.props.scenario;
      if (seen.has(scenario)) throw new Error('duplicate physics scenario in curriculum: ' + scenario);
      seen.add(scenario);
      models.push({ lessonId: lesson.id, media });
    }
  }
  models.sort((left, right) => left.lessonId.localeCompare(right.lessonId, undefined, { numeric: true }));
  return models;
}

function loadRenderer() {
  const document = new FakeDocument();
  const window = {};
  global.document = document;
  global.window = window;
  // Load the repository-owned module through Node's normal module boundary;
  // never evaluate file contents as dynamically supplied code.
  require('../web/lesson-models.js');
  if (!window.PrimerLessonModels || typeof window.PrimerLessonModels.render !== 'function') {
    throw new Error('lesson model registry did not initialize');
  }
  return window.PrimerLessonModels;
}

function alternateValue(input) {
  const start = Number(input.value);
  const minimum = Number(input.min);
  const maximum = Number(input.max);
  if (![start, minimum, maximum].every(Number.isFinite) || minimum === maximum) {
    throw new Error('invalid range control bounds');
  }
  return Math.abs(start - minimum) > Number.EPSILON ? minimum : maximum;
}

function checkScenario(renderer, lessonId, item) {
  const failures = [];
  let root;
  try {
    root = renderer.render(item, {});
  } catch (error) {
    return [lessonId + ': render threw: ' + error.message];
  }
  if (!root) return [lessonId + ': renderer returned no model'];

  let summary;
  let readout;
  let svg;
  let controls;
  let reset;
  let sliders;
  try {
    summary = one(root, node => hasClass(node, 'physics-visual-summary'), 'visible summary');
    readout = one(root, node => hasClass(node, 'model-readout'), 'readout');
    svg = one(root, node => node.tagName === 'svg' && hasClass(node, 'physics-concept-svg'), 'physics SVG');
    controls = one(root, node => hasClass(node, 'model-controls'), 'controls region');
    reset = one(controls, node => node.tagName === 'button' && node.textContent.trim() === 'Reset', 'Reset button');
    sliders = descendants(controls, node => node.tagName === 'input' && node.type === 'range');
  } catch (error) {
    return [lessonId + ': ' + error.message];
  }

  if (!sliders.length) failures.push(lessonId + ': no range controls');
  if (!summary.textContent.trim()) failures.push(lessonId + ': visible summary is empty');
  if (summary.textContent.trim() === 'The model state changed.') {
    failures.push(lessonId + ': visible summary fell back to generic copy');
  }
  if (summary.hasAttribute('hidden') || summary.getAttribute('aria-hidden') === 'true') {
    failures.push(lessonId + ': summary is hidden');
  }
  if (!readout.textContent.trim()) failures.push(lessonId + ': readout is empty');
  if (svg.hasAttribute('hidden')) failures.push(lessonId + ': SVG is hidden');

  const authoredReadout = readout.textContent;
  const authoredGeometry = serializeGeometry(svg);
  const geometryElements = descendants(svg, node =>
    ['circle', 'ellipse', 'line', 'path', 'polygon', 'polyline', 'rect'].includes(node.tagName));
  if (!authoredGeometry || !geometryElements.length) {
    failures.push(lessonId + ': SVG has no geometry');
  }

  sliders.forEach(slider => {
    const control = slider.getAttribute('aria-label') || slider.id || 'unnamed control';
    const beforeValues = sliders.map(candidate => candidate.value);
    let probe;
    try {
      probe = alternateValue(slider);
    } catch (error) {
      failures.push(lessonId + ' / ' + control + ': ' + error.message);
      return;
    }

    slider.value = String(probe);
    try {
      slider.dispatch('input');
      slider.dispatch('change');
    } catch (error) {
      failures.push(lessonId + ' / ' + control + ': interaction threw: ' + error.message);
      return;
    }

    if (readout.textContent === authoredReadout) {
      failures.push(lessonId + ' / ' + control + ': readout did not change');
    }
    if (serializeGeometry(svg) === authoredGeometry) {
      failures.push(lessonId + ' / ' + control + ': SVG geometry/attributes did not change');
    }

    try {
      reset.dispatch('click');
    } catch (error) {
      failures.push(lessonId + ' / ' + control + ': reset threw: ' + error.message);
      return;
    }
    if (readout.textContent !== authoredReadout) {
      failures.push(lessonId + ' / ' + control + ': reset did not restore the readout');
    }
    if (serializeGeometry(svg) !== authoredGeometry) {
      failures.push(lessonId + ' / ' + control + ': reset did not restore SVG geometry');
    }
    const restoredValues = sliders.map(candidate => candidate.value);
    if (restoredValues.some((value, index) => value !== beforeValues[index])) {
      failures.push(lessonId + ' / ' + control + ': reset did not restore all controls');
    }
  });

  return failures;
}

function checkUnknownScenarios(renderer) {
  const failures = [];
  for (const scenario of ['not-a-physics-scenario', 'constructor', 'toString', '__proto__']) {
    const item = {
      id: 'smoke-' + scenario,
      kind: 'model',
      renderer: 'physics-concept-lab',
      title: 'Unknown scenario smoke check',
      instructions: 'This model must fail closed.',
      props: { scenario },
    };
    try {
      const result = renderer.render(item, {});
      if (result !== null) failures.push('unknown scenario ' + JSON.stringify(scenario) + ' did not return null');
    } catch (error) {
      failures.push('unknown scenario ' + JSON.stringify(scenario) + ' threw: ' + error.message);
    }
  }
  return failures;
}

// Scientific checks inspect shipped SVG coordinates and readouts after actual
// slider events.  They cannot be satisfied by merely changing text/attributes.
function checkPhysicsFidelity(renderer, models) {
  const failures = [];
  let checks = 0;
  const requireClose = (actual, expected, tolerance, description) => {
    checks += 1;
    if (!Number.isFinite(actual) || Math.abs(actual - expected) > tolerance) {
      throw new Error(description + ': expected ' + expected + ', got ' + actual);
    }
  };
  const scenario = id => {
    const model = models.find(candidate => candidate.lessonId === id);
    if (!model) throw new Error('missing fidelity scenario ' + id);
    const root = renderer.render(model.media, {});
    return {
      root,
      set(label, value) {
        const input = one(root, candidate => candidate.tagName === 'input' &&
          candidate.getAttribute('aria-label') === label, label);
        input.value = String(value);
        input.dispatch('input');
      },
      svg() { return one(root, candidate => candidate.tagName === 'svg', 'SVG'); },
      readout() { return one(root, candidate => hasClass(candidate, 'model-readout'), 'readout').textContent; },
    };
  };
  const points = path => {
    const values = (path.getAttribute('d').match(/-?\d+(?:\.\d+)?/g) || []).map(Number);
    if (values.length % 2 || values.length < 4) throw new Error('invalid scientific curve');
    return Array.from({ length: values.length / 2 }, (_, index) => values.slice(index * 2, index * 2 + 2));
  };
  const curves = root => descendants(root, candidate => candidate.tagName === 'path' &&
    hasClass(candidate, 'physics-svg-curve'));
  const marker = root => one(root, candidate => candidate.tagName === 'circle' &&
    hasClass(candidate, 'physics-svg-marker'), 'calibrated marker');
  function audit(name, fn) {
    try { fn(); } catch (error) { failures.push(name + ': ' + error.message); }
  }

  audit('photoelectric energy / threshold / plotted slope', () => {
    const lab = scenario('phys.3.modern');
    const h = 6.62607015e-34 / 1.602176634e-19 * 1e14;
    for (const frequency of [5.25, 6, 8, 10]) {
      lab.set('Light frequency', frequency);
      const svg = lab.svg();
      const selected = marker(svg);
      const energy = h * frequency - 2.15;
      requireClose((Number(selected.getAttribute('cy')) - 239) / -205 * 2,
        energy, 1e-12, 'marker energy in eV at f=' + frequency);
      requireClose((Number(selected.getAttribute('cx')) - 88) / 560 * 7 + 3,
        frequency, 1e-12, 'marker frequency');
      const curve = points(curves(svg)[0]);
      const first = curve[0], last = curve[curve.length - 1];
      requireClose((first[0] - 88) / 560 * 7 + 3, 2.15 / h, 0.0001, 'zero-energy threshold');
      requireClose(first[1], 239, 0.005, 'threshold energy zero');
      for (const [x, y] of curve) {
        const plottedFrequency = (x - 88) / 560 * 7 + 3;
        requireClose((239 - y) / 205 * 2, h * plottedFrequency - 2.15,
          0.00008, 'entire energy curve follows Planck slope');
      }
      requireClose(last[0], 648, 0.005, 'upper frequency 10');
      const displayed = lab.readout().match(/K_max = hf − φ = ([\d.]+) eV/);
      if (!displayed) throw new Error('physical-energy readout missing');
      requireClose(Number(displayed[1]), energy, 0.0005, 'readout agrees with marker');
      const before = selected.getAttribute('cy');
      lab.set('Photon arrival-rate scale', 10);
      if (marker(lab.svg()).getAttribute('cy') !== before) throw new Error('photon flux changed electron energy');
    }
    lab.set('Light frequency', 3);
    if (descendants(lab.svg(), candidate => hasClass(candidate, 'physics-svg-marker')).length) {
      throw new Error('below-threshold state plots an electron energy');
    }
  });

  audit('free-particle action / fixed endpoints / separate oscillator', () => {
    const lab = scenario('phys.4.classical');
    for (const deformation of [-1, -0.45, 0, 0.45, 1]) {
      lab.set('Trial-path deformation ε', deformation);
      const path = points(curves(lab.svg())[1]);
      const coordinates = path.map(([x, y]) => [(x - 88) / 350, (239 - y) / 205 * 3 - 1]);
      requireClose(coordinates[0][1], 0, 0.0001, 'fixed start');
      requireClose(coordinates[coordinates.length - 1][1], 1, 0.0001, 'fixed end');
      coordinates.forEach(([time, q]) => requireClose(q,
        time + deformation * Math.sin(Math.PI * time), 0.0003, 'unclipped trial coordinate'));
      const action = coordinates.slice(1).reduce((sum, [time, q], index) => {
        const [previousTime, previousQ] = coordinates[index];
        return sum + .5 * (q - previousQ) ** 2 / (time - previousTime);
      }, 0);
      const expected = .5 + Math.PI ** 2 * deformation ** 2 / 4;
      requireClose(action, expected, 0.0013, 'integrated drawn-path action');
      const displayed = lab.readout().match(/= ([\d.]+) J s and ΔS/);
      if (!displayed) throw new Error('physical-action readout missing');
      requireClose(Number(displayed[1]), expected, 0.0005, 'action readout agrees');
    }
    for (const energy of [.5, 1, 2]) {
      lab.set('Separate oscillator energy', energy);
      const ellipse = one(lab.svg(), candidate => candidate.tagName === 'ellipse' &&
        hasClass(candidate, 'physics-svg-phase-orbit'), 'oscillator orbit');
      requireClose(Number(ellipse.getAttribute('rx')) / 61 * 2, Math.sqrt(2 * energy),
        1e-12, 'q intercept from H=p²/(2m)+kq²/2');
      requireClose(Number(ellipse.getAttribute('ry')) / 35 * 2, Math.sqrt(2 * energy),
        1e-12, 'p intercept from oscillator Hamiltonian');
    }
  });

  audit('interference resultant is the pointwise sum', () => {
    const lab = scenario('phys.3.optics-waves');
    for (const difference of [0, .25, .5, .75, 1, 1.5, 2]) {
      lab.set('Path difference', difference);
      for (const amplitude of [1, 5, 10]) {
        lab.set('Each-wave amplitude', amplitude);
        const svg = lab.svg();
        const paths = ['contribution-1', 'contribution-2', 'resultant'].map(role => points(
          one(svg, candidate => candidate.getAttribute('data-physics-trace') === role, role)));
        const [first, second, result] = paths;
        first.forEach(([x, y], index) => {
          requireClose(result[index][0], x, 0, 'matched phase coordinate');
          requireClose(220 - result[index][1], (92 - y) + (92 - second[index][1]),
            .0151, 'pointwise superposition at phase sample ' + index);
        });
        if (difference === .5 || difference === 1.5) {
          result.forEach(point => requireClose(point[1], 220, .005, 'destructive cancellation'));
        }
      }
    }
  });

  audit('independent uncertainty averages; shared calibration remains', () => {
    const lab = scenario('phys.2.units');
    for (const resolution of [.1, .5, 2]) {
      lab.set('Instrument resolution', resolution);
      for (const calibration of [0, .3, 1]) {
        lab.set('Shared calibration uncertainty', calibration);
        for (const repeats of [1, 5, 25]) {
          lab.set('Repeated readings', repeats);
          const expected = Math.sqrt((1.2 ** 2 + resolution ** 2 / 12) / repeats + calibration ** 2);
          const selected = marker(lab.svg());
          requireClose((239 - Number(selected.getAttribute('cy'))) / 205 * 2,
            expected, 1e-12, 'calibrated uncertainty marker');
          const displayed = lab.readout().match(/u_cal²\] = ([\d.]+) mm/);
          if (!displayed) throw new Error('uncertainty-budget readout missing');
          requireClose(Number(displayed[1]), expected, .0005, 'uncertainty readout agrees');
        }
      }
    }
  });

  audit('stopping motion uses one time coordinate and closes the energy account', () => {
    const lab = scenario('phys.1.motion');
    for (const friction of [0, 1, 3, 8]) {
      lab.set('Surface friction', friction);
      for (const time of [0, 2.2, 4, 6.2, 8]) {
        lab.set('Elapsed time', time);
        const selected = marker(lab.svg());
        const stopTime = friction === 0 ? Infinity : 8 / friction;
        const movingTime = Math.min(time, stopTime);
        const distance = 4 * movingTime - friction * movingTime ** 2 / 4;
        const speed = Math.max(0, 4 - friction * time / 2);
        requireClose((Number(selected.getAttribute('cx')) - 88) / 560 * 8, time, 1e-12,
          'motion marker time');
        requireClose((239 - Number(selected.getAttribute('cy'))) / 205 * 32, distance, 1e-12,
          'motion marker distance');
        requireClose(speed ** 2 + friction * distance, 16, 1e-12, 'closed kinetic/thermal account');
        const curve = points(curves(lab.svg())[0]);
        curve.forEach(([x, y]) => {
          const plottedTime = (x - 88) / 560 * 8;
          const moving = Math.min(plottedTime, stopTime);
          requireClose((239 - y) / 205 * 32, 4 * moving - friction * moving ** 2 / 4,
            .0012, 'full stopping trajectory');
        });
        const displayed = lab.readout().match(/v = ([\d.]+) m\/s/);
        if (!displayed) throw new Error('velocity readout missing');
        requireClose(Number(displayed[1]), speed, .0005, 'displayed speed');
      }
    }
  });

  audit('Lorentz event, interval and simultaneity slice share physical coordinates', () => {
    for (const id of ['phys.3.relativity-intro', 'phys.4.relativity']) {
      const lab = scenario(id);
      const advanced = id === 'phys.4.relativity';
      const maximum = advanced ? 24 : 4;
      const scale = 210 / maximum;
      for (const beta of advanced ? [-.9, -.6, 0, .6, .9] : [0, .6, .95]) {
        lab.set(advanced ? 'Frame speed v/c' : 'Relative speed v/c', beta);
        for (const proper of advanced ? [1, 4, 10] : [1]) {
          if (advanced) lab.set('Proper-time interval', proper);
          const gamma = 1 / Math.sqrt(1 - beta ** 2);
          const event = one(lab.svg(), candidate => candidate.getAttribute('data-physics-role') ===
            'clock-event', 'clock event');
          const space = (Number(event.getAttribute('cx')) - 360) / scale;
          const time = (258 - Number(event.getAttribute('cy'))) / scale;
          requireClose(time, gamma * proper, 1e-12, 'coordinate time');
          requireClose(space, beta * time, 1e-12, 'moving clock worldline');
          requireClose(time ** 2 - space ** 2, proper ** 2, 1e-10, 'Minkowski interval');
          requireClose(gamma * (time - beta * space), proper, 1e-12, 'inverse Lorentz proper time');
          if (advanced) {
            const slice = one(lab.svg(), candidate => candidate.getAttribute('data-physics-role') ===
              'simultaneity-slice', 'moving-frame simultaneity');
            const endpoints = [1, 2].map(index => [
              (Number(slice.getAttribute('x' + index)) - 360) / scale,
              (258 - Number(slice.getAttribute('y' + index))) / scale,
            ]);
            endpoints.forEach(([u, t]) => {
              requireClose(gamma * (t - beta * u), proper, 1e-12, 'constant transformed time over full slice');
              if (t < -1e-12 || t > maximum + 1e-12 || Math.abs(u) > maximum + 1e-12) {
                throw new Error('simultaneity line exceeds physical plot domain');
              }
            });
            requireClose((endpoints[1][1] - endpoints[0][1]) /
              (endpoints[1][0] - endpoints[0][0]), beta, 1e-12, 'simultaneity slope');
          }
        }
      }
    }
  });

  audit('Carnot flow shafts share one energy scale and conserve energy', () => {
    const lab = scenario('phys.3.thermo');
    for (const hot of [400, 600, 1000]) {
      lab.set('Hot reservoir', hot);
      for (const cold of [200, 300, 390]) {
        lab.set('Cold reservoir', cold);
        const input = one(lab.svg(), candidate => candidate.getAttribute('data-physics-flow') === 'input', 'input shaft');
        const work = one(lab.svg(), candidate => candidate.getAttribute('data-physics-flow') === 'work', 'work shaft');
        const rejected = one(lab.svg(), candidate => candidate.getAttribute('data-physics-flow') === 'rejected', 'rejected shaft');
        const widths = [Number(input.getAttribute('width')), Number(work.getAttribute('height')),
          Number(rejected.getAttribute('width'))];
        requireClose(widths[0], 24, 1e-12, '100 J input scale');
        requireClose(widths[1] / 24, 1 - cold / hot, 1e-12, 'work fraction');
        requireClose(widths[2] / 24, cold / hot, 1e-12, 'rejected fraction');
        requireClose(widths[1] + widths[2], widths[0], 1e-12, 'Qh = W + Qc');
        requireClose(widths[2] / .24 / cold - 100 / hot, 0, 1e-12, 'reversible reservoir entropy balance');
      }
    }
  });

  audit('radioactive expectation differs from integer mock survivors', () => {
    const lab = scenario('phys.3.nuclear');
    for (const initial of [32, 64, 128]) {
      lab.set('Starting nuclei', initial);
      for (const realization of [1, 2, 8]) {
        lab.set('Mock realization', realization);
        let fullPath;
        for (const elapsed of [0, .5, 1, 2, 6]) {
          lab.set('Elapsed half-lives', elapsed);
          const svg = lab.svg();
          const selected = marker(svg);
          requireClose((239 - Number(selected.getAttribute('cy'))) / 205, 2 ** -elapsed,
            1e-12, 'fractional ensemble expectation');
          const measurement = one(svg, candidate => hasClass(candidate, 'physics-svg-measurement'), 'mock survivors');
          const observed = (239 - Number(measurement.getAttribute('cy'))) / 205 * initial;
          requireClose(observed, Math.round(observed), 1e-12, 'integer sample survivor count');
          const p = 2 ** -elapsed;
          const deviation = Math.sqrt(initial * p * (1 - p));
          const verticalError = one(svg, candidate => hasClass(candidate, 'physics-svg-measurement-error') &&
            candidate.getAttribute('x1') === candidate.getAttribute('x2'), 'survival standard-deviation bar');
          requireClose((239 - Number(verticalError.getAttribute('y1'))) / 205,
            Math.min(1, (observed + deviation) / initial), 1e-12, 'upper physical-support error bar');
          requireClose((239 - Number(verticalError.getAttribute('y2'))) / 205,
            Math.max(0, (observed - deviation) / initial), 1e-12, 'lower physical-support error bar');
          const sampleCurve = curves(svg)[1];
          if (fullPath !== undefined && fullPath !== sampleCurve.getAttribute('d')) {
            throw new Error('moving time resamples lifetimes');
          }
          fullPath = sampleCurve.getAttribute('d');
          const plotted = points(sampleCurve);
          requireClose(plotted[0][1], 34, .005, 'all nuclei initially undecayed');
          let previous = plotted[0];
          plotted.slice(1).forEach(point => {
            if (point[0] < previous[0] || point[1] < previous[1]) throw new Error('survival trace reverses');
            if (point[1] !== previous[1]) {
              requireClose(point[0], previous[0], .005, 'instantaneous integer decay');
              requireClose((point[1] - previous[1]) / 205 * initial, 1, .0064, 'one nucleus per decay event');
            }
            previous = point;
          });
          const timeX = 88 + elapsed / 6 * 560;
          const matching = plotted.filter(point => point[0] <= timeX + .005).at(-1);
          requireClose((239 - matching[1]) / 205 * initial, observed, .0032, 'selected count belongs to drawn lifetime trace');
          if (elapsed === 0) requireClose(observed, initial, 1e-12, 'no synthetic decay at t=0');
          const displayed = lab.readout().match(/expected N = .* = ([\d.]+) nuclei/);
          if (!displayed) throw new Error('ensemble expectation readout missing');
          requireClose(Number(displayed[1]), initial * 2 ** -elapsed, .0005, 'expected-count equation');
          const spread = lab.readout().match(/standard deviation = ([\d.]+)\./);
          if (!spread) throw new Error('sample standard deviation readout missing');
          requireClose(Number(spread[1]), deviation, .0005, 'binomial survivor standard deviation');
        }
      }
    }
  });
  audit('Born density and histogram preserve every count and physical probability area', () => {
    const lab = scenario('phys.4.quantum');
    for (const n of [1, 2, 3, 4, 5]) {
      lab.set('Box energy state n', n);
      for (const samples of [16, 64, 128]) {
        lab.set('Detection samples', samples);
        for (const length of [.5, 1, 2]) {
          lab.set('Well length L', length);
          const bars = descendants(lab.svg(), candidate => hasClass(candidate, 'physics-svg-histogram'));
          const total = bars.reduce((sum, bar) => sum + Number(bar.getAttribute('data-physics-count')), 0);
          requireClose(total, samples, 0, 'all requested detections retained');
          const ceiling = Number(bars[0].getAttribute('data-physics-density-max'));
          const area = bars.reduce((sum, bar) => sum + Number(bar.getAttribute('width')) / 280 *
            Number(bar.getAttribute('height')) / 205 * ceiling, 0);
          requireClose(area, 1, 1e-12, 'actual histogram probability area');
          const wall = one(lab.svg(), candidate => candidate.hasAttribute('data-physics-wall'), 'hard wall');
          requireClose((Number(wall.getAttribute('x1')) - 88) / 280, length, 1e-12, 'physical well length');
          bars.forEach(bar => {
            const density = Number(bar.getAttribute('height')) / 205 * ceiling;
            requireClose(density, Number(bar.getAttribute('data-physics-count')) / (samples * length / bars.length),
              1e-12, 'physical bin density');
          });
          const path = points(curves(lab.svg())[0]);
          const coordinates = path.map(([x, y]) => [(x - 88) / 280, (239 - y) / 205 * ceiling]);
          let integral = 0;
          coordinates.forEach(([x, density], index) => {
            requireClose(density, x <= length + 1e-5 ? 2 / length * Math.sin(n * Math.PI * x / length) ** 2 : 0,
              .003, 'physical Born-density coordinate');
            if (index) integral += (x - coordinates[index - 1][0]) * (density + coordinates[index - 1][1]) / 2;
          });
          requireClose(integral, 1, .0002, 'normalized displayed theoretical density');
          const energy = lab.readout().match(/= ([\d.]+) eV/);
          if (!energy) throw new Error('well energy readout missing');
          requireClose(Number(energy[1]), .3760301621 * n ** 2 / length ** 2, .0000006, 'electron energy n²/L²');
        }
      }
    }
  });

  audit('charge neutrality, mass action and Fermi level agree with actual band coordinates', () => {
    const lab = scenario('phys.4.solid-state');
    for (const gap of [.5, 1.1, 4]) {
      lab.set('Band gap', gap);
      for (const temperature of [100, 300, 800]) {
        lab.set('Temperature', temperature);
        for (const doping of [-100, 0, 100]) {
          lab.set('Net ionized dopants', doping);
          const conduction = one(lab.svg(), candidate => candidate.getAttribute('data-band-edge') === 'conduction', 'Ec');
          const valence = one(lab.svg(), candidate => candidate.getAttribute('data-band-edge') === 'valence', 'Ev');
          const fermi = one(lab.svg(), candidate => candidate.hasAttribute('data-band-fermi'), 'EF');
          const ef = (Number(conduction.getAttribute('y1')) - Number(fermi.getAttribute('y1'))) / 40;
          const eg = (Number(valence.getAttribute('y1')) - Number(conduction.getAttribute('y1'))) / 40;
          requireClose(eg, gap, 1e-12, 'common-scale gap');
          const kt = 1.380649e-23 / 1.602176634e-19 * temperature;
          const nc = 1e19 * (temperature / 300) ** 1.5;
          const electrons = nc * Math.exp(ef / kt), holes = nc * Math.exp((-eg - ef) / kt);
          requireClose((electrons - holes - doping * 1e14) / Math.max(electrons, holes, Math.abs(doping) * 1e14, 1),
            0, 1e-11, 'charge neutrality inferred from rendered EF');
          requireClose(electrons * holes / (nc ** 2 * Math.exp(-gap / kt)), 1, 1e-11, 'mass action');
          if (electrons / nc > .03 || holes / nc > .03) throw new Error('chosen range leaves dilute carrier approximation');
          const displayed = lab.readout().match(/; n=([^,]+), p=([^ ]+) cm/);
          if (!displayed) throw new Error('carrier densities missing');
          requireClose(Number(displayed[1]) / electrons, 1, .0005, 'electron readout');
          requireClose(Number(displayed[2]) / holes, 1, .0005, 'hole readout');
          if (doping === 0) requireClose(ef, -gap / 2, 1e-12, 'intrinsic symmetric-band Fermi level');
        }
      }
    }
  });

  audit('free mode ladder retains physical vacuum offset and level spacing', () => {
    const lab = scenario('phys.5.qft');
    for (const frequency of [1, 2, 5]) {
      lab.set('Mode frequency', frequency);
      for (const occupation of [0, 3, 6]) {
        lab.set('Excitation number n', occupation);
        const zero = one(lab.svg(), candidate => candidate.hasAttribute('data-qft-zero'), 'energy zero');
        const levels = descendants(lab.svg(), candidate => candidate.hasAttribute('data-qft-level'));
        requireClose(levels.length, 7, 0, 'all levels shown');
        levels.forEach(level => {
          const n = Number(level.getAttribute('data-qft-level'));
          const energy = (Number(zero.getAttribute('y1')) - Number(level.getAttribute('y1'))) * 34 / 198;
          requireClose(energy / frequency - .5, n, 1e-12, 'vacuum offset and nħω spectrum');
          if (n === 0 && !(energy > 0)) throw new Error('vacuum is falsely drawn at zero');
        });
        const selected = one(lab.svg(), candidate => hasClass(candidate, 'physics-svg-qft-level') &&
          hasClass(candidate, 'is-selected'), 'selected occupation');
        requireClose(Number(selected.getAttribute('data-qft-level')), occupation, 0, 'selected number state');
      }
    }
  });

  audit('four-setting CHSH, finite samples and signed error bars are consistent', () => {
    const lab = scenario('phys.5.quantum-info');
    for (const angle of [0, 30, 45, 60, 90]) {
      lab.set('Bob setting angle θ', angle);
      for (const visibility of [0, .5, 1]) {
        lab.set('Singlet visibility', visibility);
        for (const samples of [32, 128, 256]) {
          lab.set('Pairs per setting', samples);
          const angles = [[0,angle],[0,-angle],[90,angle],[90,-angle]];
          const correlations = angles.map(([a,b]) => -visibility * Math.cos((a-b) * Math.PI / 180));
          const theory = correlations[0] + correlations[1] + correlations[2] - correlations[3];
          const selected = marker(lab.svg());
          requireClose((239 - Number(selected.getAttribute('cy'))) / 205 * 8 - 4, theory, 1e-12, 'four-setting signed theory');
          if (Math.abs(theory) > 2 * Math.sqrt(2) + 1e-12) throw new Error('Tsirelson bound exceeded by theory');
          if (angle === 45 && visibility === 1) requireClose(Math.abs(theory), 2 * Math.sqrt(2), 1e-12, 'maximal singlet CHSH');
          const text = lab.readout();
          // A simple bounded extraction handles signed decimal lists without
          // interpreting prose or assuming finite samples are exactly 50/50.
          const mock = text.split('Mock E00,E01,E10,E11: ')[1]?.split('. Mock local')[0]?.split(', ').map(Number);
          if (!mock || mock.length !== 4 || !mock.every(Number.isFinite)) throw new Error('four mock correlations missing');
          mock.forEach(e => requireClose(samples * (1+e)/2, Math.round(samples * (1+e)/2), .00007, 'integer same-outcome count'));
          const measurement = one(lab.svg(), candidate => hasClass(candidate, 'physics-svg-measurement'), 'mock signed S');
          const observed = (239 - Number(measurement.getAttribute('cy'))) / 205 * 8 - 4;
          requireClose(observed,
            mock[0] + mock[1] + mock[2] - mock[3], .0000021, 'mock S assembled from four correlations');
          const sigma = Math.sqrt(correlations.reduce((sum, e) => sum+(1-e*e)/samples, 0));
          const error = one(lab.svg(), candidate => hasClass(candidate, 'physics-svg-measurement-error') &&
            candidate.getAttribute('x1') === candidate.getAttribute('x2'), 'signed S error bar');
          requireClose((239 - Number(error.getAttribute('y1'))) / 205 * 8 - 4,
            Math.min(4, observed + sigma), 1e-12, 'upper signed-S deviation');
          requireClose((239 - Number(error.getAttribute('y2'))) / 205 * 8 - 4,
            Math.max(-4, observed - sigma), 1e-12, 'lower signed-S deviation');
          const reported = text.match(/theoretical standard deviation ([\d.]+)\. Mock/);
          if (!reported) throw new Error('signed-S standard deviation missing');
          requireClose(Number(reported[1]), sigma, .0000006, 'independent-setting variance');
        }
      }
    }
  });
  audit('current gauge retains the complete Ohmic range without false saturation', () => {
    const lab = scenario('phys.2.electricity');
    for (const voltage of [1, 6, 12]) {
      lab.set('Battery voltage', voltage);
      for (const resistance of [1, 6, 20]) {
        lab.set('Resistance', resistance);
        for (const closed of [0, 1]) {
          lab.set('Switch', closed);
          const gauge = one(lab.svg(), candidate => candidate.hasAttribute('data-current-gauge'), 'current gauge');
          const current = closed ? voltage / resistance : 0;
          requireClose(Number(gauge.getAttribute('width')) / 340 * 12, current, 1e-12, 'entire physical current scale');
          if (closed) {
            const reported = lab.readout().match(/load power V × I = ([\d.]+) W/);
            if (!reported) throw new Error('load power missing');
            requireClose(Number(reported[1]), voltage * current, .005, 'P=VI');
          }
        }
      }
    }
  });
  return { failures, checks };
}

function main() {
  const curriculum = JSON.parse(fs.readFileSync(CURRICULUM_PATH, 'utf8'));
  const models = collectPhysicsModels(curriculum);
  const failures = [];
  if (models.length !== EXPECTED_SCENARIO_COUNT) {
    failures.push('expected ' + EXPECTED_SCENARIO_COUNT + ' physics-concept-lab scenarios, found ' + models.length);
  }

  const renderer = loadRenderer();
  for (const { lessonId, media } of models) {
    if (media.props.scenario !== lessonId) {
      failures.push(lessonId + ': scenario is cross-bound to ' + JSON.stringify(media.props.scenario));
      continue;
    }
    failures.push(...checkScenario(renderer, lessonId, media));
  }
  failures.push(...checkUnknownScenarios(renderer));
  const fidelity = checkPhysicsFidelity(renderer, models);
  failures.push(...fidelity.failures);

  if (failures.length) {
    console.error('Physics model DOM smoke check failed (' + failures.length + '):');
    failures.forEach(failure => console.error('- ' + failure));
    process.exitCode = 1;
    return;
  }

  const controls = models.reduce((total, { media }) => {
    const root = renderer.render(media, {});
    return total + descendants(root, node => node.tagName === 'input' && node.type === 'range').length;
  }, 0);
  console.log('Physics model DOM smoke check passed: ' + models.length +
    ' scenarios, ' + controls + ' independently exercised controls; ' + fidelity.checks +
    ' equation/geometry assertions across fourteen targeted scenarios.');
}

try {
  main();
} catch (error) {
  console.error('Physics model DOM smoke check could not run: ' + error.stack);
  process.exitCode = 1;
}
