'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../web/prenatal-sequence.js'), 'utf8');
const registry = fs.readFileSync(path.join(__dirname, '../web/lesson-models.js'), 'utf8');
const assetRoot = '/app/reference-media/prenatal-development/';

class Element {
  constructor(tag) {
    this.tagName = tag;
    this.attributes = new Map();
    this.children = [];
    this.listeners = new Map();
    this.nodeType = 1;
    this.isConnected = false;
    this.hidden = false;
    this.disabled = false;
    this._text = '';
  }
  setAttribute(name, value) {
    this.attributes.set(name, String(value));
    if (['value', 'max', 'min', 'step', 'id', 'type'].includes(name)) this[name] = String(value);
  }
  getAttribute(name) { return this.attributes.get(name) ?? null; }
  append(...elements) { this.children.push(...elements); }
  prepend(...elements) { this.children.unshift(...elements); }
  replaceChildren(...elements) { this.children = elements; this._text = ''; }
  set textContent(text) { this._text = String(text); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent || '').join(''); }
  addEventListener(name, callback) {
    if (!this.listeners.has(name)) this.listeners.set(name, new Set());
    this.listeners.get(name).add(callback);
  }
  removeEventListener(name, callback) { this.listeners.get(name)?.delete(callback); }
  dispatch(name) { for (const callback of this.listeners.get(name) || []) callback({ target: this }); }
  querySelectorAll(tag) { return walk(this).filter(element => element.tagName === tag); }
}

function walk(root) { return root.children.flatMap(child => [child, ...walk(child)]); }
function find(root, selector) {
  const found = walk(root).find(selector);
  assert.ok(found, 'Expected an element matching the selector');
  return found;
}
function button(root, text) { return find(root, element => element.tagName === 'button' && element.textContent === text); }
function slider(root) { return find(root, element => element.getAttribute('type') === 'range'); }
function image(root) { return find(root, element => element.tagName === 'img'); }
function status(root) { return find(root, element => element.getAttribute('role') === 'status'); }
function fixture() {
  return {
    title: 'Human development: the first trimester',
    gif: assetRoot + 'prenatal-development.gif',
    note: 'AI-generated educational reconstructions; not clinical images. Magnification varies; not to scale.',
    sources: [{ title: 'Development', url: 'https://example.org/development' }],
    frames: [5, 6, 83].map(day => ({
      id: 'day-' + String(day).padStart(3, '0'), developmentalDay: day, gestationalDays: day + 14,
      label: 'Day ' + day, ageLabel: Math.floor((day + 14) / 7) + 'w' + ((day + 14) % 7) + 'd',
      src: assetRoot + 'day-' + String(day).padStart(3, '0') + '.webp',
      alt: 'A developmental stage viewed from the same side.', caption: 'Development on day ' + day + '.', durationMs: 1200,
    })),
  };
}

function harness(options = {}) {
  const document = new Element('document');
  document.body = new Element('body');
  document.createElement = tag => new Element(tag);
  document.hidden = false;
  const timers = new Map(), requests = [], observers = [];
  let nextTimer = 0;
  const preference = new Element('preference');
  preference.matches = Boolean(options.reducedMotion);
  const window = { matchMedia: () => preference };
  const context = {
    window, document, AbortController,
    fetch: (url, init) => {
      requests.push({ url, init });
      return options.fetch ? options.fetch(url, init) : Promise.resolve({ ok: true, json: async () => options.data || fixture() });
    },
    MutationObserver: class {
      constructor(callback) { this.callback = callback; this.disconnected = false; observers.push(this); }
      observe() {}
      disconnect() { this.disconnected = true; }
    },
    setTimeout: (callback, delay) => { const id = ++nextTimer; timers.set(id, { callback, delay }); return id; },
    clearTimeout: id => timers.delete(id),
  };
  vm.runInNewContext(source, context);
  vm.runInNewContext(registry, context);
  const root = window.PrimerLessonModels.render({ renderer: 'prenatal-sequence', title: fixture().title,
    instructions: 'Use the slider to compare stages.' });
  root.isConnected = true;
  observers[0].callback();
  return {
    root, document, preference, requests, timers, observers,
    async ready() { await new Promise(resolve => setImmediate(resolve)); },
    tick() {
      const [id, timer] = timers.entries().next().value || [];
      assert.ok(timer, 'Expected a scheduled playback timer');
      timers.delete(id);
      timer.callback();
    },
    remove() { root.isConnected = false; observers[0].callback(); },
  };
}

test('registry loads the local manifest, starts paused, and fetches only the selected image', async () => {
  const h = harness();
  await h.ready();
  assert.equal(h.requests.length, 1);
  assert.equal(h.requests[0].url, assetRoot + 'sequence.json');
  assert.equal(h.requests[0].init.credentials, 'same-origin');
  assert.equal(h.timers.size, 0);
  assert.equal(walk(h.root).filter(element => element.tagName === 'img').length, 1);
  assert.equal(image(h.root).getAttribute('src'), assetRoot + 'day-005.webp');
  assert.equal(slider(h.root).max, '2');
  assert.equal(button(h.root, 'Previous frame').disabled, true);
  assert.equal(button(h.root, 'Play sequence').getAttribute('aria-pressed'), 'false');
  assert.match(slider(h.root).getAttribute('aria-valuetext'), /Day 5 after fertilisation.*2w5d.*frame 1 of 3/);
  const gif = find(h.root, element => element.getAttribute('download') === 'prenatal-development.gif');
  assert.equal(gif.getAttribute('href'), assetRoot + 'prenatal-development.gif');
  assert.ok(!walk(h.root).some(element => (element.getAttribute('src') || '').endsWith('.gif')));
  h.root.dispose();
});

test('slider and previous/next controls clamp boundaries, update ages, and pause playback', async () => {
  const h = harness();
  await h.ready();
  image(h.root).dispatch('load');
  button(h.root, 'Play sequence').dispatch('click');
  assert.equal(h.timers.size, 1);
  slider(h.root).value = '200';
  slider(h.root).dispatch('input');
  assert.equal(slider(h.root).value, '2');
  assert.equal(h.timers.size, 0);
  assert.equal(button(h.root, 'Next frame').disabled, true);
  assert.match(slider(h.root).getAttribute('aria-valuetext'), /Day 83.*13w6d/);
  button(h.root, 'Previous frame').dispatch('click');
  assert.equal(slider(h.root).value, '1');
  slider(h.root).value = '-100';
  slider(h.root).dispatch('input');
  assert.equal(slider(h.root).value, '0');
  assert.equal(button(h.root, 'Previous frame').disabled, true);
  h.root.dispose();
});

test('playback waits for image loading, advances once per frame, stops at end, and can replay', async () => {
  const h = harness();
  await h.ready();
  button(h.root, 'Play sequence').dispatch('click');
  assert.equal(h.timers.size, 0, 'Do not skip an unloaded frame');
  image(h.root).dispatch('load');
  assert.equal(h.timers.size, 1);
  h.tick();
  assert.equal(slider(h.root).value, '1');
  assert.equal(h.timers.size, 0);
  image(h.root).dispatch('load');
  h.tick();
  assert.equal(slider(h.root).value, '2');
  image(h.root).dispatch('load');
  h.tick();
  assert.equal(h.timers.size, 0);
  assert.equal(button(h.root, 'Replay sequence').getAttribute('aria-pressed'), 'false');
  assert.match(status(h.root).textContent, /End of the first-trimester/);
  button(h.root, 'Replay sequence').dispatch('click');
  assert.equal(slider(h.root).value, '0');
  assert.equal(button(h.root, 'Pause sequence').getAttribute('aria-pressed'), 'true');
  h.root.dispose();
});

test('stale image events cannot change the current frame; an image error pauses and supports retry', async () => {
  const h = harness();
  await h.ready();
  const stale = image(h.root);
  button(h.root, 'Next frame').dispatch('click');
  const selected = image(h.root);
  stale.dispatch('error');
  assert.ok(!button(h.root, 'Play sequence').disabled);
  button(h.root, 'Play sequence').dispatch('click');
  selected.dispatch('error');
  assert.equal(h.timers.size, 0);
  assert.equal(button(h.root, 'Play sequence').disabled, true);
  assert.equal(button(h.root, 'Retry frame').hidden, false);
  assert.match(status(h.root).textContent, /Frame unavailable/);
  button(h.root, 'Retry frame').dispatch('click');
  assert.equal(slider(h.root).value, '1');
  assert.notEqual(image(h.root), selected);
  image(h.root).dispatch('load');
  assert.equal(image(h.root).hidden, false);
  assert.equal(button(h.root, 'Play sequence').disabled, false);
  h.root.dispose();
});

test('missing manifest leaves the lesson usable and a successful retry restores the sequence', async () => {
  let attempts = 0;
  const h = harness({ fetch: async () => ++attempts === 1
    ? { ok: false } : { ok: true, json: async () => fixture() } });
  await h.ready();
  assert.equal(button(h.root, 'Retry sequence').hidden, false);
  assert.match(status(h.root).textContent, /rest of this lesson is ready/);
  assert.equal(walk(h.root).filter(element => element.tagName === 'img').length, 0);
  button(h.root, 'Retry sequence').dispatch('click');
  await h.ready();
  assert.equal(h.requests.length, 2);
  assert.equal(button(h.root, 'Retry sequence').hidden, true);
  assert.equal(image(h.root).getAttribute('src'), assetRoot + 'day-005.webp');
  h.root.dispose();
});

test('malformed, unordered, duplicate and external frames never become image requests', async () => {
  for (const mutate of [
    data => { data.frames = []; },
    data => { data.frames[0].src = 'https://example.org/private.webp'; },
    data => { data.frames[0].src = assetRoot + '../other.webp'; },
    data => { data.frames[1].id = data.frames[0].id; },
    data => { data.frames.reverse(); },
    data => { data.frames[0].gestationalDays = 5; },
    data => { data.gif = 'javascript:alert(1)'; },
  ]) {
    const data = fixture();
    mutate(data);
    const h = harness({ data });
    await h.ready();
    assert.equal(button(h.root, 'Retry sequence').hidden, false);
    assert.equal(walk(h.root).filter(element => element.tagName === 'img').length, 0);
    h.root.dispose();
  }
});

test('navigation aborts requests, clears playback, removes listeners, and ignores late completion', async () => {
  const h = harness();
  await h.ready();
  image(h.root).dispatch('load');
  button(h.root, 'Play sequence').dispatch('click');
  h.remove();
  assert.equal(h.timers.size, 0);
  assert.equal(h.requests[0].init.signal.aborted, true);
  assert.equal(h.observers[0].disconnected, true);
  assert.equal(h.document.listeners.get('visibilitychange').size, 0);
  assert.equal(h.preference.listeners.get('change').size, 0);
  let resolve;
  const pending = harness({ fetch: () => new Promise(done => { resolve = done; }) });
  pending.remove();
  resolve({ ok: true, json: async () => fixture() });
  await pending.ready();
  assert.equal(walk(pending.root).filter(element => element.tagName === 'img').length, 0);
  assert.equal(pending.requests[0].init.signal.aborted, true);
});

test('reduced motion uses slower discrete frames, and hidden pages or changed preferences pause', async () => {
  const h = harness({ reducedMotion: true });
  await h.ready();
  image(h.root).dispatch('load');
  button(h.root, 'Play sequence').dispatch('click');
  assert.equal(h.timers.values().next().value.delay, 2000);
  h.document.hidden = true;
  h.document.dispatch('visibilitychange');
  assert.equal(h.timers.size, 0);
  assert.equal(button(h.root, 'Play sequence').getAttribute('aria-pressed'), 'false');
  h.document.hidden = false;
  button(h.root, 'Play sequence').dispatch('click');
  h.preference.matches = false;
  h.preference.dispatch('change');
  assert.equal(h.timers.size, 0);
  assert.equal(button(h.root, 'Play sequence').getAttribute('aria-pressed'), 'false');
  h.root.dispose();
});
