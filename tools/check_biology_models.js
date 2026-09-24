#!/usr/bin/env node
'use strict';

/* Execute the shipped biology lesson renderers against a deliberately small
 * fake DOM. This catches state/geometry/reset regressions without maintaining
 * a second copy of any biological calculation or requiring a browser. */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const CURRICULUM_PATH = path.join(ROOT, 'data', 'curriculum', '04-life-sciences.json');
const EXPECTED_RENDERERS = new Set([
  'life-cycle', 'cell-microscope', 'allele-segregation-lab',
  'circulation-route-lab', 'gene-expression-stepper', 'morphogen-gradient-lab',
]);

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
    const next = force === undefined ? !values.has(String(name)) : Boolean(force);
    if (next) values.add(String(name));
    else values.delete(String(name));
    this.write(values);
    return next;
  }
}

class FakeTextNode {
  constructor(value) { this.nodeType = 3; this.parentNode = null; this.data = String(value); }
  get textContent() { return this.data; }
  set textContent(value) { this.data = String(value); }
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
    this.hidden = false;
    this.disabled = false;
    this.classList = new FakeClassList(this);
  }
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
  get className() { return this._className; }
  set className(value) {
    this._className = String(value);
    if (this._className) this.attributes.set('class', this._className);
    else this.attributes.delete('class');
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
  }
  getAttribute(name) {
    const key = String(name);
    return this.attributes.has(key) ? this.attributes.get(key) : null;
  }
  hasAttribute(name) { return this.attributes.has(String(name)); }
  removeAttribute(name) {
    const key = String(name); this.attributes.delete(key);
    if (key === 'class') this._className = '';
  }
  addEventListener(type, listener) {
    const key = String(type);
    if (!this.listeners.has(key)) this.listeners.set(key, []);
    this.listeners.get(key).push(listener);
  }
  dispatch(type) {
    const event = {
      type: String(type), target: this, currentTarget: this, defaultPrevented: false,
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
  get textContent() { return this.children.map(child => child.textContent).join(''); }
  set textContent(value) { this.replaceChildren(); if (value !== '') this.append(new FakeTextNode(value)); }
}

class FakeDocument {
  createElement(tagName) { return new FakeElement(tagName); }
  createElementNS(namespaceURI, tagName) { return new FakeElement(tagName, namespaceURI); }
  createTextNode(value) { return new FakeTextNode(value); }
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
  if (matches.length !== 1) throw new Error('expected one ' + description + ', found ' + matches.length);
  return matches[0];
}

function serializeVisual(node) {
  if (!node || node.nodeType !== 1 || node.tagName === 'text') return '';
  const attributes = [...node.attributes.entries()]
    .filter(([name]) => !name.startsWith('aria-') && name !== 'focusable' && name !== 'id')
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([name, value]) => name + '=' + JSON.stringify(value)).join(' ');
  return '<' + node.tagName + (attributes ? ' ' + attributes : '') + '>' +
    node.children.map(serializeVisual).join('') + '</' + node.tagName + '>';
}

function collectModels(curriculum) {
  const models = [];
  for (const lesson of curriculum.nodes || []) {
    for (const media of lesson.lesson_media || []) {
      if (media.kind === 'model' && EXPECTED_RENDERERS.has(media.renderer)) {
        models.push({ lessonId: lesson.id, media });
      }
    }
  }
  return models.sort((left, right) => left.lessonId.localeCompare(right.lessonId));
}

function loadRenderer() {
  global.document = new FakeDocument();
  global.window = {};
  require('../web/lesson-models.js');
  if (!window.PrimerLessonModels || typeof window.PrimerLessonModels.render !== 'function') {
    throw new Error('lesson model registry did not initialize');
  }
  return window.PrimerLessonModels;
}

function button(root, label) {
  return one(root, element => element.tagName === 'button' && element.textContent.trim() === label, label + ' button');
}

function exercise(root, renderer) {
  if (renderer === 'life-cycle') {
    button(root, 'Butterfly').dispatch('click');
    button(root, 'Next stage').dispatch('click');
  } else if (renderer === 'cell-microscope') {
    button(root, 'Green leaf').dispatch('click');
    button(root, '400×').dispatch('click');
    button(root, 'Show structure labels').dispatch('click');
  } else if (renderer === 'circulation-route-lab') {
    for (let count = 0; count < 4; count += 1) button(root, 'Next stop').dispatch('click');
  } else if (renderer === 'gene-expression-stepper') {
    button(root, 'Switch gene on').dispatch('click');
    button(root, 'Transcribe').dispatch('click');
    button(root, 'Process RNA').dispatch('click');
    button(root, 'Export mature mRNA').dispatch('click');
    for (let count = 0; count < 3; count += 1) button(root, 'Translate next codon').dispatch('click');
    button(root, 'Read stop codon').dispatch('click');
  } else if (renderer === 'allele-segregation-lab') {
    button(root, 'Separate alleles').dispatch('click');
    button(root, 'Combine gametes').dispatch('click');
  }
  else if (renderer === 'morphogen-gradient-lab') {
    const slider = one(root, element => element.tagName === 'input' &&
      element.getAttribute('aria-label') === 'Signal loss at each cell in percent', 'decay slider');
    slider.value = '35';
    slider.dispatch('input');
    slider.dispatch('change');
  } else throw new Error('no exercise for ' + renderer);
}

function expectedEvidence(renderer) {
  return {
    'life-cycle': ['butterfly', 'caterpillar'],
    'cell-microscope': ['green leaf', '400×', 'chloroplast'],
    'circulation-route-lab': ['pulmonary veins', 'higher-oxygen'],
    'gene-expression-stepper': ['stop and release', 'met–glu–phe'],
    'allele-segregation-lab': ['1/4 pp', '3/4 purple'],
    'morphogen-gradient-lab': ['0.65^i', 'illustrative thresholds'],
  }[renderer] || [];
}

function checkModel(renderer, lessonId, item) {
  const failures = [];
  let root;
  try { root = renderer.render(item, {}); }
  catch (error) { return [lessonId + ': render threw: ' + error.message]; }
  try {
    const canvas = one(root, element => hasClass(element, 'model-canvas'), 'model canvas');
    const readout = one(root, element => hasClass(element, 'model-readout'), 'model readout');
    const status = one(root, element => hasClass(element, 'model-status'), 'live status');
    const reset = button(root, 'Reset');
    const diagrams = descendants(canvas, element => element.tagName === 'svg');
    const geometry = descendants(canvas, element =>
      ['circle', 'ellipse', 'line', 'path', 'polygon', 'polyline', 'rect'].includes(element.tagName));
    if (!diagrams.length || !geometry.length) failures.push(lessonId + ': no meaningful SVG geometry');
    if (status.getAttribute('role') !== 'status' || status.getAttribute('aria-live') !== 'polite') {
      failures.push(lessonId + ': status region is not polite live output');
    }
    const authoredReadout = readout.textContent;
    const authoredVisual = serializeVisual(canvas);
    exercise(root, item.renderer);
    if (readout.textContent === authoredReadout) failures.push(lessonId + ': interaction did not change readout');
    if (serializeVisual(canvas) === authoredVisual) failures.push(lessonId + ': interaction did not change visual geometry/state');
    if (!status.textContent.trim()) failures.push(lessonId + ': interaction did not announce status');
    const exercisedReadout = readout.textContent.toLowerCase();
    expectedEvidence(item.renderer).forEach(evidence => {
      if (!exercisedReadout.includes(evidence)) failures.push(lessonId + ': missing exercised evidence ' + evidence);
    });
    reset.dispatch('click');
    if (readout.textContent !== authoredReadout) failures.push(lessonId + ': Reset did not restore authored readout');
    if (serializeVisual(canvas) !== authoredVisual) failures.push(lessonId + ': Reset did not restore authored visual');
  } catch (error) { failures.push(lessonId + ': ' + error.message); }
  return failures;
}

function main() {
  const curriculum = JSON.parse(fs.readFileSync(CURRICULUM_PATH, 'utf8'));
  const models = collectModels(curriculum);
  const actualRenderers = new Set(models.map(entry => entry.media.renderer));
  const failures = [];
  if (models.length !== EXPECTED_RENDERERS.size) {
    failures.push('expected ' + EXPECTED_RENDERERS.size + ' biology models, found ' + models.length);
  }
  for (const name of EXPECTED_RENDERERS) {
    if (!actualRenderers.has(name)) failures.push('missing curriculum model: ' + name);
  }
  const renderer = loadRenderer();
  models.forEach(({ lessonId, media }) => failures.push(...checkModel(renderer, lessonId, media)));
  const css = fs.readFileSync(path.join(ROOT, 'web', 'styles.css'), 'utf8');
  for (const selector of ['.science-diagram-scroll', '.biology-control-grid', '.allele-segregation-diagram',
    '.circulation-diagram', '.gene-expression-diagram', '.morphogen-gradient-diagram']) {
    if (!css.includes(selector)) failures.push('missing responsive CSS selector ' + selector);
  }
  if (!css.includes('.lesson-model .btn { min-height: 44px; }')) failures.push('model controls lost 44px minimum height');
  if (failures.length) {
    failures.forEach(failure => process.stderr.write('FAIL ' + failure + '\n'));
    process.exitCode = 1;
    return;
  }
  process.stdout.write(models.length + ' biology models, ' + models.length + ' independently exercised interactions\n');
}

main();
