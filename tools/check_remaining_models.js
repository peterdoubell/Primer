#!/usr/bin/env node
'use strict';

/*
 * Deterministic DOM smoke check for every curriculum lesson model not already
 * exercised by the physics, biology, spatial, music-listening, or Doppler checks.
 *
 * The fake DOM intentionally implements only the browser primitives used by
 * the shipped renderers.  The model code itself is loaded through Node's
 * module boundary; this file does not duplicate any teaching calculation.
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const CURRICULUM_DIR = path.join(ROOT, 'data', 'curriculum');
const BIOLOGY_CHECKED = new Set([
  'life-cycle', 'cell-microscope', 'allele-segregation-lab',
  'circulation-route-lab', 'gene-expression-stepper', 'morphogen-gradient-lab',
]);

const EXPECTED_BINDINGS = Object.freeze({
  'math.0.counting': 'counter',
  'math.0.shapes': 'shape-explorer',
  'math.1.addition': 'make-ten',
  'math.2.fractions': 'fraction-equivalence-lab',
  'math.2.negatives': 'integer-number-line-lab',
  'math.3.functions': 'function-composition-lab',
  'math.4.linalg': 'matrix-transform-lab',
  'math.5.pde': 'heat-equation-lab',
  'lang.0.alphabet': 'alphabet-explorer',
  'lang.1.reading': 'reading-path-lab',
  'phys.0.light-shadow': 'shadow-lab',
  'phys.1.light': 'light-paths',
  'phys.4.fluids': 'venturi-flow-lab',
  'chem.2.atoms': 'atom-element-builder',
  'cs.0.instructions': 'sequence-runner',
  'cs.1.algorithms': 'algorithm-tracer',
  'cs.3.data-structures': 'stack-queue-lab',
  'cs.4.networks': 'tcp-packet-tracer',
  'cs.5.complexity': 'complexity-certificate-lab',
  'hist.0.family': 'inclusive-family-timeline',
  'hist.1.timelines': 'timeline-order-lab',
  'earth.0.sky': 'day-night-rotation-lab',
  'earth.1.seasons': 'seasons-tilt-lab',
  'arts.0.colors': 'classroom-paint-mixer',
  'arts.1.elements': 'art-elements-composer',
  'mind.2.logic-intro': 'counterexample-lab',
  'mind.3.logic': 'truth-table-lab',
  'rad.3.ct-image': 'ct-window-lab',
});

class FakeStyle {
  constructor() { this.properties = new Map(); }
  setProperty(name, value) { this.properties.set(String(name), String(value)); }
  getPropertyValue(name) { return this.properties.get(String(name)) || ''; }
}

class FakeClassList {
  constructor(owner) { this.owner = owner; }
  values() { return new Set(this.owner.className.split(/\s+/).filter(Boolean)); }
  write(values) { this.owner.className = [...values].join(' '); }
  add(...names) { const values = this.values(); names.forEach(name => values.add(String(name))); this.write(values); }
  remove(...names) { const values = this.values(); names.forEach(name => values.delete(String(name))); this.write(values); }
  contains(name) { return this.values().has(String(name)); }
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
  constructor(value, ownerDocument) {
    this.nodeType = 3;
    this.parentNode = null;
    this.ownerDocument = ownerDocument;
    this.data = String(value);
  }
  get textContent() { return this.data; }
  set textContent(value) { this.data = String(value); }
  remove() {
    if (!this.parentNode) return;
    const index = this.parentNode.children.indexOf(this);
    if (index >= 0) this.parentNode.children.splice(index, 1);
    this.parentNode = null;
  }
}

function matchesSelector(element, selector) {
  if (!element || element.nodeType !== 1) return false;
  if (selector.startsWith('.')) return element.classList.contains(selector.slice(1));
  if (/^[a-z][a-z0-9-]*$/i.test(selector)) return element.tagName === selector.toLowerCase();
  throw new Error('fake DOM does not implement selector ' + JSON.stringify(selector));
}

class FakeElement {
  constructor(tagName, ownerDocument, namespaceURI = null) {
    this.nodeType = 1;
    this.tagName = String(tagName).toLowerCase();
    this.ownerDocument = ownerDocument;
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
    this.disabled = false;
    this.hidden = false;
    this.classList = new FakeClassList(this);
  }
  get className() { return this._className; }
  set className(value) {
    this._className = String(value);
    if (this._className) this.attributes.set('class', this._className);
    else this.attributes.delete('class');
  }
  get firstElementChild() { return this.children.find(child => child.nodeType === 1) || null; }
  get lastElementChild() {
    for (let index = this.children.length - 1; index >= 0; index -= 1) {
      if (this.children[index].nodeType === 1) return this.children[index];
    }
    return null;
  }
  setAttribute(name, value) {
    const key = String(name); const text = String(value);
    this.attributes.set(key, text);
    if (key === 'class') this._className = text;
    else if (key === 'value') this.value = text;
    else if (key === 'min') this.min = text;
    else if (key === 'max') this.max = text;
    else if (key === 'step') this.step = text;
    else if (key === 'type') this.type = text;
    else if (key === 'id') this.id = text;
    else if (key === 'disabled') this.disabled = true;
    else if (key === 'hidden') this.hidden = true;
  }
  getAttribute(name) {
    const key = String(name);
    return this.attributes.has(key) ? this.attributes.get(key) : null;
  }
  hasAttribute(name) { return this.attributes.has(String(name)); }
  removeAttribute(name) {
    const key = String(name);
    this.attributes.delete(key);
    if (key === 'class') this._className = '';
    else if (key === 'disabled') this.disabled = false;
    else if (key === 'hidden') this.hidden = false;
  }
  addEventListener(type, listener) {
    const key = String(type);
    if (!this.listeners.has(key)) this.listeners.set(key, []);
    this.listeners.get(key).push(listener);
  }
  dispatch(type) {
    if (this.disabled && String(type) === 'click') return false;
    const event = {
      type: String(type), target: this, currentTarget: this, defaultPrevented: false,
      preventDefault() { this.defaultPrevented = true; },
    };
    (this.listeners.get(event.type) || []).forEach(listener => listener.call(this, event));
    return !event.defaultPrevented;
  }
  append(...values) {
    values.forEach(value => {
      const child = value && value.nodeType ? value : new FakeTextNode(value, this.ownerDocument);
      if (child.parentNode) {
        const index = child.parentNode.children.indexOf(child);
        if (index >= 0) child.parentNode.children.splice(index, 1);
      }
      child.parentNode = this;
      this.children.push(child);
    });
  }
  prepend(...values) {
    const additions = values.map(value => value && value.nodeType
      ? value : new FakeTextNode(value, this.ownerDocument));
    additions.forEach(child => {
      if (child.parentNode) {
        const index = child.parentNode.children.indexOf(child);
        if (index >= 0) child.parentNode.children.splice(index, 1);
      }
      child.parentNode = this;
    });
    this.children.unshift(...additions);
  }
  replaceChildren(...values) {
    this.children.forEach(child => { child.parentNode = null; });
    this.children = [];
    this.append(...values);
  }
  querySelectorAll(selector) { return descendants(this, element => matchesSelector(element, selector)); }
  focus() { this.ownerDocument.activeElement = this; }
  remove() {
    if (!this.parentNode) return;
    const index = this.parentNode.children.indexOf(this);
    if (index >= 0) this.parentNode.children.splice(index, 1);
    this.parentNode = null;
  }
  get textContent() { return this.children.map(child => child.textContent).join(''); }
  set textContent(value) { this.replaceChildren(); if (value !== '') this.append(new FakeTextNode(value, this.ownerDocument)); }
}

class FakeDocument {
  constructor() { this.activeElement = null; }
  createElement(tagName) { return new FakeElement(tagName, this); }
  createElementNS(namespaceURI, tagName) { return new FakeElement(tagName, this, namespaceURI); }
  createTextNode(value) { return new FakeTextNode(value, this); }
}

function descendants(root, predicate) {
  const found = [];
  function visit(current) {
    if (current && current.nodeType === 1 && predicate(current)) found.push(current);
    if (current && current.children) current.children.forEach(visit);
  }
  visit(root);
  return found;
}

function hasClass(element, name) {
  return element && element.nodeType === 1 && element.classList.contains(name);
}

function one(root, predicate, description) {
  const matches = descendants(root, predicate);
  if (matches.length !== 1) {
    throw new Error('expected exactly one ' + description + ', found ' + matches.length);
  }
  return matches[0];
}

function styleEntries(style) {
  const entries = [...style.properties.entries()];
  Object.keys(style).filter(key => key !== 'properties').forEach(key => {
    const value = style[key];
    if (typeof value === 'string' || typeof value === 'number') entries.push([key, String(value)]);
  });
  return entries.sort(([left], [right]) => left.localeCompare(right));
}

function serialize(node) {
  if (!node) return '';
  if (node.nodeType === 3) return '#text(' + JSON.stringify(node.data) + ')';
  const attributes = [...node.attributes.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([name, value]) => name + '=' + JSON.stringify(value)).join(' ');
  const state = [
    'disabled=' + String(Boolean(node.disabled)),
    'hidden=' + String(Boolean(node.hidden)),
    'value=' + JSON.stringify(String(node.value)),
    'min=' + JSON.stringify(String(node.min)),
    'max=' + JSON.stringify(String(node.max)),
    'step=' + JSON.stringify(String(node.step)),
  ];
  const styles = styleEntries(node.style).map(([name, value]) => name + '=' + JSON.stringify(value));
  return '<' + node.tagName + (attributes ? ' ' + attributes : '') +
    ' [' + state.concat(styles).join(' ') + ']>' +
    node.children.map(serialize).join('') + '</' + node.tagName + '>';
}

function normalizeGeneratedIds(value) {
  return value.replace(/(shadow-position|lesson-spectrum)-\d+/g, '$1-#');
}

function modelState(root) {
  const canvas = one(root, element => hasClass(element, 'model-canvas'), 'model canvas');
  const controls = one(root, element => hasClass(element, 'model-controls'), 'model controls');
  const readout = one(root, element => hasClass(element, 'model-readout'), 'model readout');
  return {
    canvas: normalizeGeneratedIds(serialize(canvas)),
    controls: normalizeGeneratedIds(serialize(controls)),
    readout: readout.textContent,
  };
}

function buttonText(root, label) {
  return one(root, element => element.tagName === 'button' && element.textContent.trim() === label,
    'button labelled ' + JSON.stringify(label));
}

function buttonAria(root, label) {
  return one(root, element => element.tagName === 'button' && element.getAttribute('aria-label') === label,
    'button with aria-label ' + JSON.stringify(label));
}

function rangeAria(root, label) {
  return one(root, element => element.tagName === 'input' && element.type === 'range' &&
    element.getAttribute('aria-label') === label, 'range with aria-label ' + JSON.stringify(label));
}

function click(control) {
  if (control.disabled) throw new Error('planned control is disabled');
  control.dispatch('click');
}

function setRange(control, value) {
  const minimum = Number(control.min); const maximum = Number(control.max);
  if (!Number.isFinite(minimum) || !Number.isFinite(maximum) || minimum >= maximum) {
    throw new Error('range has invalid bounds');
  }
  if (value < minimum || value > maximum || String(value) === String(control.value)) {
    throw new Error('planned range value is not a distinct in-bounds value');
  }
  control.value = String(value);
  control.dispatch('input');
  control.dispatch('change');
}

const INTERACTIONS = Object.freeze({
  counter: { description: 'count pebble 1', actions: 1,
    run: root => click(buttonAria(root, 'Pebble 1, not counted yet')) },
  'shape-explorer': { description: 'select Triangle', actions: 1,
    run: root => click(buttonText(root, 'Triangle')) },
  'make-ten': { description: 'move one counter into the ten-frame', actions: 1,
    run: root => click(buttonText(root, 'Move one into the ten-frame')) },
  'fraction-equivalence-lab': { description: 'split each part into 2', actions: 1,
    run: root => click(buttonText(root, 'Split each part into 2')) },
  'integer-number-line-lab': { description: 'change signed move from −7 to −6', actions: 1,
    run: root => setRange(rangeAria(root, 'Choose a signed move'), -6) },
  'function-composition-lab': { description: 'reverse the function order', actions: 1,
    run: root => click(buttonText(root, 'Apply g, then f')) },
  'matrix-transform-lab': { description: 'project onto the x-axis', actions: 1,
    run: root => click(buttonText(root, 'Project onto x-axis')) },
  'heat-equation-lab': { description: 'diffuse one step', actions: 1,
    run: root => click(buttonText(root, 'Diffuse one step')) },
  'alphabet-explorer': { description: 'advance from A to B', actions: 1,
    run: root => click(buttonAria(root, 'Next letter')) },
  'reading-path-lab': { description: 'select the Blend step', actions: 1,
    run: root => click(buttonText(root, 'Blend')) },
  'shadow-lab': { description: 'move the blocker from 45 to 0', actions: 1,
    run: root => setRange(one(root, element => element.tagName === 'input' && element.type === 'range',
      'shadow position range'), 0) },
  'light-paths': { description: 'select Mirror', actions: 1,
    run: root => click(buttonText(root, 'Mirror')) },
  'venturi-flow-lab': { description: 'select quarter-area throat', actions: 1,
    run: root => click(buttonText(root, 'Quarter area (1 cm²)')) },
  'atom-element-builder': { description: 'add one proton', actions: 1,
    run: root => click(buttonAria(root, 'Add one proton')) },
  'sequence-runner': { description: 'move Close later, then run the reordered steps', actions: 2,
    reset: 'Mix them again', run: root => {
      click(buttonAria(root, 'Move Close the bag later'));
      click(buttonText(root, 'Run the steps'));
    } },
  'algorithm-tracer': { description: 'leave out the jam step', actions: 1,
    run: root => click(buttonAria(root, 'Include step: Spread jam on one slice')) },
  'stack-queue-lab': { description: 'switch from stack to queue', actions: 1,
    run: root => click(buttonText(root, 'Queue')) },
  'tcp-packet-tracer': { description: 'advance to the next TCP event', actions: 1,
    run: root => click(buttonText(root, 'Send next event')) },
  'complexity-certificate-lab': { description: 'toggle certificate variable A', actions: 1,
    run: root => click(buttonText(root, 'A = True')) },
  'inclusive-family-timeline': { description: 'switch to fictional family history', actions: 1,
    run: root => click(buttonText(root, 'Family history')) },
  'timeline-order-lab': { description: 'move the 1910 event earlier', actions: 1,
    run: root => click(buttonAria(root, 'Move 1910, Library opened, earlier')) },
  'day-night-rotation-lab': { description: 'turn Earth ahead six hours', actions: 1,
    run: root => click(buttonText(root, 'Turn 6 hours')) },
  'seasons-tilt-lab': { description: 'select December solstice', actions: 1,
    run: root => click(buttonText(root, 'December solstice')) },
  'classroom-paint-mixer': { description: 'change first paint to Red', actions: 1,
    run: root => click(buttonAria(root, 'First paint: Red')) },
  'art-elements-composer': { description: 'add the Color layer', actions: 1,
    run: root => click(buttonText(root, 'Color')) },
  'counterexample-lab': { description: 'test the reversed claim', actions: 1,
    run: root => click(buttonText(root, 'Test the reverse')) },
  'truth-table-lab': { description: 'switch from IMPLIES to AND', actions: 1,
    run: root => click(buttonText(root, 'AND')) },
  'ct-window-lab': { description: 'change window level from 40 to 100', actions: 1,
    expectStatus: false, run: root => setRange(rangeAria(root, 'Window level'), 100) },
});

function collectRemainingModels() {
  const entries = [];
  const lessonIds = new Set();
  for (const filename of fs.readdirSync(CURRICULUM_DIR).filter(name => name.endsWith('.json')).sort()) {
    const curriculum = JSON.parse(fs.readFileSync(path.join(CURRICULUM_DIR, filename), 'utf8'));
    for (const lesson of curriculum.nodes || []) {
      for (const media of lesson.lesson_media || []) {
        if (media.kind !== 'model' || media.renderer === 'physics-concept-lab' ||
            ['spatial-3d', 'concept-lab', 'music-listening-lab', 'doppler-angle-lab'].includes(media.renderer) ||
            BIOLOGY_CHECKED.has(media.renderer)) continue;
        if (lessonIds.has(lesson.id)) throw new Error('duplicate remaining model lesson ' + lesson.id);
        lessonIds.add(lesson.id);
        entries.push({ filename, lessonId: lesson.id, media });
      }
    }
  }
  return entries.sort((left, right) => left.lessonId.localeCompare(right.lessonId, undefined, { numeric: true }));
}

function loadRegistry() {
  global.document = new FakeDocument();
  global.window = {};
  require('../web/lesson-models.js');
  if (!window.PrimerLessonModels || typeof window.PrimerLessonModels.render !== 'function' ||
      !Array.isArray(window.PrimerLessonModels.supported)) {
    throw new Error('lesson model registry did not initialize');
  }
  return window.PrimerLessonModels;
}

function validateBindings(models, failures) {
  const actual = new Map(models.map(entry => [entry.lessonId, entry.media.renderer]));
  if (actual.size !== Object.keys(EXPECTED_BINDINGS).length) {
    failures.push('expected 28 remaining curriculum models, found ' + actual.size);
  }
  Object.entries(EXPECTED_BINDINGS).forEach(([lessonId, renderer]) => {
    if (!actual.has(lessonId)) failures.push('missing remaining curriculum model ' + lessonId);
    else if (actual.get(lessonId) !== renderer) failures.push(lessonId + ': expected renderer ' +
      renderer + ', found ' + actual.get(lessonId));
  });
  actual.forEach((renderer, lessonId) => {
    if (!Object.prototype.hasOwnProperty.call(EXPECTED_BINDINGS, lessonId)) {
      failures.push('unexpected remaining curriculum model ' + lessonId + ' (' + renderer + ')');
    }
  });
}

function checkModel(registry, lessonId, media) {
  const failures = [];
  const plan = INTERACTIONS[media.renderer];
  if (!plan) return { failures: [lessonId + ': no interaction plan for ' + media.renderer] };
  let root;
  let comparisonRoot;
  try {
    root = registry.render(media, {});
    comparisonRoot = registry.render(media, {});
  } catch (error) {
    return { failures: [lessonId + ': render threw: ' + error.message] };
  }
  if (!root || !comparisonRoot) return { failures: [lessonId + ': renderer returned no model'] };

  let canvas; let controls; let readout; let status; let initial;
  try {
    canvas = one(root, element => hasClass(element, 'model-canvas'), 'model canvas');
    controls = one(root, element => hasClass(element, 'model-controls'), 'model controls');
    readout = one(root, element => hasClass(element, 'model-readout'), 'model readout');
    status = one(root, element => hasClass(element, 'model-status'), 'live status');
    initial = modelState(root);
    const comparison = modelState(comparisonRoot);
    if (JSON.stringify(initial) !== JSON.stringify(comparison)) {
      failures.push(lessonId + ': two authored renders are not deterministic');
    }
    if (!canvas.children.length) failures.push(lessonId + ': model canvas is empty');
    if (!controls.children.length) failures.push(lessonId + ': controls are empty');
    if (!readout.textContent.trim()) failures.push(lessonId + ': authored readout is empty');
    if (status.getAttribute('role') !== 'status' || status.getAttribute('aria-live') !== 'polite') {
      failures.push(lessonId + ': status is not a polite live region');
    }
    const svgs = descendants(canvas, element => element.tagName === 'svg');
    if (svgs.length) {
      const geometry = descendants(canvas, element =>
        ['circle', 'ellipse', 'line', 'path', 'polygon', 'polyline', 'rect'].includes(element.tagName));
      if (!geometry.length) failures.push(lessonId + ': SVG canvas has no geometry');
    } else if (descendants(canvas, element => element !== canvas).length < 2) {
      failures.push(lessonId + ': non-SVG canvas has no meaningful DOM visual');
    }
  } catch (error) {
    return { failures: [lessonId + ': ' + error.message] };
  }

  try { plan.run(root); }
  catch (error) { failures.push(lessonId + ': interaction threw: ' + error.message); }
  const changed = modelState(root);
  if (changed.readout === initial.readout) failures.push(lessonId + ': planned control did not change readout');
  if (changed.canvas === initial.canvas) failures.push(lessonId + ': planned control did not change DOM/SVG visual');
  if (plan.expectStatus !== false && !status.textContent.trim()) {
    failures.push(lessonId + ': planned control did not announce live status');
  }

  const resetLabel = plan.reset || 'Reset';
  try { click(buttonText(controls, resetLabel)); }
  catch (error) { failures.push(lessonId + ': reset threw: ' + error.message); }
  const restored = modelState(root);
  if (restored.readout !== initial.readout) failures.push(lessonId + ': reset did not restore readout');
  if (restored.canvas !== initial.canvas) failures.push(lessonId + ': reset did not restore DOM/SVG visual');
  if (restored.controls !== initial.controls) failures.push(lessonId + ': reset did not restore control state');
  return { failures, plan };
}

function checkUnknownRenderers(registry) {
  const failures = [];
  for (const name of ['not-a-renderer', 'constructor', 'toString', '__proto__']) {
    try {
      const result = registry.render({ id: 'unknown-' + name, kind: 'model', renderer: name }, {});
      if (result !== null) failures.push('unknown renderer ' + JSON.stringify(name) + ' did not return null');
    } catch (error) {
      failures.push('unknown renderer ' + JSON.stringify(name) + ' threw: ' + error.message);
    }
  }
  return failures;
}

function main() {
  const failures = [];
  const models = collectRemainingModels();
  validateBindings(models, failures);
  const registry = loadRegistry();
  const supported = new Set(registry.supported);
  const coverage = [];
  let actions = 0;
  let resets = 0;

  for (const { lessonId, media } of models) {
    if (!supported.has(media.renderer)) {
      failures.push(lessonId + ': renderer is absent from the shipped registry: ' + media.renderer);
      continue;
    }
    const result = checkModel(registry, lessonId, media);
    failures.push(...result.failures);
    if (result.plan) {
      actions += result.plan.actions;
      resets += 1;
      coverage.push(lessonId + ' = ' + media.renderer + ' [' + result.plan.description + ']');
    }
  }
  failures.push(...checkUnknownRenderers(registry));

  if (failures.length) {
    console.error('Remaining lesson-model DOM smoke check failed (' + failures.length + '):');
    failures.forEach(failure => console.error('- ' + failure));
    process.exitCode = 1;
    return;
  }
  console.log('Remaining lesson-model DOM smoke check passed: ' + models.length +
    ' models, ' + actions + ' exercised control changes, ' + resets + ' verified resets.');
  coverage.forEach(entry => console.log('COVER ' + entry));
}

try { main(); }
catch (error) {
  console.error('Remaining lesson-model DOM smoke check could not run: ' + error.stack);
  process.exitCode = 1;
}
