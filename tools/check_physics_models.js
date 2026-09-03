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
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const CURRICULUM_PATH = path.join(ROOT, 'data', 'curriculum', '03-physics.json');
const MODELS_PATH = path.join(ROOT, 'web', 'lesson-models.js');
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
  const context = vm.createContext({ document, window, console });
  const source = fs.readFileSync(MODELS_PATH, 'utf8');
  new vm.Script(source, { filename: MODELS_PATH }).runInContext(context);
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
    ' scenarios, ' + controls + ' independently exercised controls.');
}

try {
  main();
} catch (error) {
  console.error('Physics model DOM smoke check could not run: ' + error.stack);
  process.exitCode = 1;
}
