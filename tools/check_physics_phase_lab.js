#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const lab = require('../web/physics-phase-lab.js');
const near = (a, b, tolerance = 3e-11) => assert.ok(Math.abs(a - b) <= tolerance * Math.max(1, Math.abs(a), Math.abs(b)), `${a} != ${b}`);
// Independent reference data and a sequential calorimetric budget, rather than
// implementation constants, exported phase fractions or its component function.
const temperatures = [-30, 0, 0, 100, 100, 140];
const widths = [62.7, 334, 418.6, 2256, 80.8];
const thresholds = [-62.7, 0, 334, 752.6, 3008.6, 3089.4];
const starts = {ice18: -37.62, ice0: 0, water20: 417.72, water100: 752.6, steam100: 3008.6, steam120: 3049};
const keys = ['ice', 'fusion', 'liquid', 'vaporization', 'steam'];
function oracle(h) {
  let remaining = h + 62.7, index = 0;
  while (index < 4 && remaining > widths[index]) remaining -= widths[index++];
  const fraction = Math.max(0, Math.min(1, remaining / widths[index]));
  const t = temperatures[index] + fraction * (temperatures[index + 1] - temperatures[index]);
  const fractions = index === 0 ? [1, 0, 0] : index === 1 ? [1 - fraction, fraction, 0] : index === 2 ? [0, 1, 0] : index === 3 ? [0, 1 - fraction, fraction] : [0, 0, 1];
  return {t, fractions};
}
function independentLedger(h0, h, mass) {
  const lo = Math.min(h0, h), hi = Math.max(h0, h), sign = Math.sign(h - h0);
  return keys.map((_, i) => sign * mass * Math.max(0, Math.min(hi, thresholds[i + 1]) - Math.max(lo, thresholds[i])));
}
function checkBalance(m) {
  const expected = oracle(m.currentH), fractions = [m.fractions.ice, m.fractions.water, m.fractions.steam];
  near(m.temperature, expected.t); fractions.forEach((f, i) => {near(f, expected.fractions[i]); assert.ok(f >= 0 && f <= 1);});
  near(fractions.reduce((a, f) => a + f, 0), 1);
  near(m.masses.ice + m.masses.water + m.masses.steam, m.state.mass);
  // Reconstruct enthalpy by weighting independent phase enthalpies at the
  // actual common temperature. This checks coexistence and all latent energy.
  const t = m.temperature;
  const h = fractions[0] * 2.09 * t + fractions[1] * (334 + 4.186 * t) + fractions[2] * (3008.6 + 2.020 * (t - 100));
  near(h, m.currentH); near(m.state.mass * (h - starts[m.state.start]), m.state.energy);
  near(m.deltaH, m.state.energy); near(m.balanceResidual, 0);
  const ledger = independentLedger(starts[m.state.start], h, m.state.mass);
  m.ledger.forEach((row, i) => {assert.equal(row.key, keys[i]); near(row.energy, ledger[i]);});
  near(m.ledger.reduce((sum, row) => sum + row.energy, 0), m.state.energy);
  assert.ok(m.temperature >= -30 - 1e-10 && m.temperature <= 140 + 1e-10);
}
let balances = 0;
for (const mass of [.05, .1, .25, .65, 1, 2]) for (const start of Object.keys(starts)) {
  const hs = [...thresholds, ...thresholds.slice(1, -1).flatMap(h => [h - 1e-6, h + 1e-6]),
    167, 230, 500, 1880.6, 2200, 3049];
  for (const h of hs) {
    const m = lab.build({mass, start, energy: mass * (h - starts[start])}); checkBalance(m); near(m.currentH, h); balances++;
    // Reverse to the starting state and repeat; no hysteresis is invented.
    const back = lab.build({...m.state, energy: 0}); checkBalance(back); near(back.currentH, starts[start]); balances++;
  }
  for (const energy of [-1e9, 1e9]) {
    const m = lab.build({mass, start, energy}); checkBalance(m);
    near(m.currentH, energy < 0 ? -62.7 : 3089.4); balances++;
  }
}
const known = [[3.762, 0, [1, 0, 0]], [20.462, 0, [.5, .5, 0]], [37.162, 0, [0, 1, 0]],
  [79.022, 100, [0, 1, 0]], [191.822, 100, [0, .5, .5]], [304.622, 100, [0, 0, 1]], [308.662, 120, [0, 0, 1]]];
for (const [energy, temperature, fractions] of known) {
  const m = lab.build({mass: .1, start: 'ice18', energy}); near(m.temperature, temperature);
  [m.fractions.ice, m.fractions.water, m.fractions.steam].forEach((f, i) => near(f, fractions[i]));
}
// Same temperature, distinct phase fractions; temperature alone is insufficient.
for (const h of [1, 83.5, 167, 333]) assert.equal(lab.resolve(h).temperature, 0);
assert.notEqual(lab.resolve(83.5).fractions.water, lab.resolve(167).fractions.water);
for (const h of [753, 1316.6, 1880.6, 3008]) assert.equal(lab.resolve(h).temperature, 100);
assert.notEqual(lab.resolve(1316.6).fractions.steam, lab.resolve(1880.6).fractions.steam);
for (const [h, key] of [[0, 'ice'], [334, 'water'], [752.6, 'water'], [3008.6, 'steam']]) {
  const m = lab.resolve(h); assert.equal(m.fractions[key], 1); assert.match(m.phase, /^Pure /);
}
for (const [h, cp] of [[-20, 2.09], [500, 4.186], [3040, 2.020]]) {
  const a = lab.resolve(h - .01), b = lab.resolve(h + .01); near((b.temperature - a.temperature) / .02, 1 / cp, 1e-8);
}
for (const h of [167, 1880.6]) assert.equal(lab.resolve(h - .01).temperature, lab.resolve(h + .01).temperature);
for (const invalid of [NaN, Infinity, -Infinity, '', null, undefined, true, {}, 'bad', -62.71, 3089.41]) assert.throws(() => lab.resolve(invalid), RangeError);
for (const invalid of [NaN, Infinity, -Infinity, '', null, undefined, true, {}, 'bad']) {
  assert.equal(lab.normalize({mass: invalid}).mass, .25); assert.equal(lab.normalize({energy: invalid}).energy, 0);
}
assert.equal(lab.normalize({mass: -10}).mass, .05); assert.equal(lab.normalize({mass: 10}).mass, 2);
assert.equal(lab.equilibriumAtSpecificEnthalpy, lab.resolve);
// No epsilon band or formatter may silently turn real heat / coexistence into
// zero. These heat-relative tests stay meaningful below the ulp of absolute h.
for (const [start, energy, secondPhase] of [['ice0', 1e-16, 'water'], ['water100', 1e-16, 'steam'], ['steam100', -1e-16, 'water']]) {
  const m = lab.build({mass: .1, start, energy});
  assert.equal(m.state.energy, energy); assert.ok(m.fractions[secondPhase] > 0); assert.ok(m.masses[secondPhase] > 0);
  assert.match(m.phase, /coexist/); assert.ok(m.ledger.some(row => row.energy === energy)); assert.equal(m.deltaH, energy);
  assert.match(m.readout, /1e-16 kilojoules/); assert.doesNotMatch(m.readout, /No heat has/);
}
const tinyCooling = lab.build({mass: .1, start: 'ice0', energy: -1e-16});
assert.equal(tinyCooling.state.energy, -1e-16); assert.ok(tinyCooling.temperature < 0); assert.equal(tinyCooling.fractions.ice, 1);
const nearlyMelted = lab.build({mass: .1, start: 'ice0', energy: .1 * (334 - 1e-12)});
assert.ok(nearlyMelted.fractions.ice > 0 && nearlyMelted.fractions.water > 0); assert.match(nearlyMelted.phase, /coexist/);
assert.equal(lab.resolve(-62.7).temperature, -30); assert.equal(lab.resolve(3089.4).temperature, 140);

// A mounted DOM contract. Numerical checks below use independent data and the
// actual path/bar/marker attributes, not metadata supplied by the renderer.
class E {
  constructor(tag) {this.tagName = tag; this.nodeType = 1; this.attributes = {}; this.children = []; this.listeners = {}; this.value = ''; this.classList = {toggle: (k, on) => {const s = new Set((this.attributes.class || '').split(' ')); on ? s.add(k) : s.delete(k); this.attributes.class = [...s].join(' ');}};}
  setAttribute(k, v) {this.attributes[k] = String(v);} getAttribute(k) {return this.attributes[k];}
  append(...x) {this.children.push(...x);} replaceChildren(...x) {this.children = x;} addEventListener(k, fn) {this.listeners[k] = fn;}
  get textContent() {return this.children.map(x => x.textContent).join('');} set textContent(v) {this.children = [{nodeType: 3, textContent: String(v)}];}
}
global.document = {createElement: t => new E(t), createElementNS: (_, t) => new E(t), createTextNode: v => ({nodeType: 3, textContent: String(v)})};
const all = e => [e, ...(e.children || []).flatMap(x => x.nodeType === 1 ? all(x) : [])];
let mounted = 0;
for (const scenario of Object.keys(lab.bindings)) {
  let speech;
  const root = lab.render({props: {scenario}}, {speakButton: fn => {speech = fn; return new E('button');}});
  assert.ok(root);
  const find = (k, v) => all(root).find(e => e.attributes?.[k] === v);
  const check = () => {
    const s = JSON.parse(root.getAttribute('data-phase-state')), h0 = starts[s.start], h = h0 + s.energy / s.mass, m = oracle(h);
    const min = s.mass * (-62.7 - h0), max = s.mass * (3089.4 - h0);
    const X = q => 68 + 344 * (q - min) / (max - min), Y = t => 334 - 238 * (t + 30) / 170;
    keys.forEach((key, i) => {
      const path = find('data-phase-segment', key), match = path.getAttribute('d').match(/^M([^ ]+) ([^ ]+) L([^ ]+) ([^ ]+)$/);
      assert.ok(match); const q0 = s.mass * (thresholds[i] - h0), q1 = s.mass * (thresholds[i + 1] - h0);
      [X(q0), Y(temperatures[i]), X(q1), Y(temperatures[i + 1])].forEach((coordinate, j) => near(Number(match[j + 1]), coordinate));
      if (i === 1 || i === 3) near(Number(match[2]), Number(match[4]));
    });
    for (const [name, q, t] of [['start', 0, oracle(h0).t], ['current', s.energy, m.t]]) {
      const marker = find('data-phase-marker', name); near(Number(marker.getAttribute('cx')), X(q)); near(Number(marker.getAttribute('cy')), Y(t));
    }
    let x = 28;
    ['ice', 'water', 'steam'].forEach((key, i) => {const bar = find('data-phase-fraction', key); near(Number(bar.getAttribute('x')), x); near(Number(bar.getAttribute('width')), 384 * m.fractions[i]); x += 384 * m.fractions[i];}); near(x, 412);
    independentLedger(h0, h, s.mass).forEach((q, i) => {const bar = find('data-phase-ledger', keys[i]); near(Number(bar.getAttribute('x')), 220 + 170 * Math.min(0, q) / (s.mass * 2256)); near(Number(bar.getAttribute('width')), 170 * Math.abs(q) / (s.mass * 2256));});
    near(Number(find('data-phase-control', 'energy').min), min); near(Number(find('data-phase-control', 'energy').max), max);
    assert.match(speech(), /kilojoules/); assert.match(speech(), /percent/); assert.match(speech(), /enthalpy/i);
    mounted++;
  };
  check();
  for (const start of Object.keys(starts)) {
    const select = find('data-phase-start', ''); select.value = start; select.listeners.change(); check();
    assert.equal(JSON.parse(root.getAttribute('data-phase-state')).energy, 0);
    for (const mass of [.05, 2]) {
      const input = find('data-phase-control', 'mass'); input.value = mass; input.listeners.input(); input.listeners.change(); check();
      for (const button of all(root).filter(e => e.attributes?.['data-phase-target'])) {button.listeners.click(); check();}
      const q = find('data-phase-control', 'energy');
      for (const energy of [q.min, q.max, 0]) {q.value = energy; q.listeners.input(); q.listeners.change(); check();}
      const number = find('data-phase-energy-number', ''); number.value = mass * (167 - starts[start]); number.listeners.change(); check();
    }
  }
  find('data-phase-action', 'cool').listeners.click(); check(); assert.ok(JSON.parse(root.getAttribute('data-phase-state')).energy < 0);
  find('data-phase-action', 'return').listeners.click(); check(); assert.equal(JSON.parse(root.getAttribute('data-phase-state')).energy, 0);
  find('data-phase-action', 'reset').listeners.click(); check(); assert.deepEqual(JSON.parse(root.getAttribute('data-phase-state')), lab.bindings[scenario]);
  const enlarge = find('data-phase-action', 'enlarge'); enlarge.listeners.click(); assert.equal(enlarge.getAttribute('aria-pressed'), 'true'); enlarge.listeners.click(); assert.equal(enlarge.getAttribute('aria-pressed'), 'false');
}
assert.equal(lab.render({props: {scenario: 'wrong'}}), null);
assert.equal(lab.render({props: {scenario: 'phys.2.matter.phase-change', extra: true}}), null);
console.log(`Verified ${balances} independent phase balances and ${mounted} mounted enthalpy-coordinate/fraction/ledger states.`);

// Optional real-browser verification: serve original resources normally, never
// execute JS file text through eval/vm. Requires Playwright on NODE_PATH.
async function browserReview() {
  const fs = require('node:fs'), path = require('node:path'), http = require('node:http');
  const {chromium} = require('playwright'), {createEvidenceDirectory} = require('./qa-browser.cjs');
  const baseDirectory = path.resolve(__dirname, '..'), evidence = createEvidenceDirectory();
  const files = new Map(['/styles.css', '/physics-phase-lab.css', '/physics-phase-lab.js'].map(url => [url, path.join(baseDirectory, 'web', url.slice(1))]));
  const server = http.createServer((req, res) => {
    if (files.has(req.url)) {res.writeHead(200, {'Content-Type': req.url.endsWith('.css') ? 'text/css' : 'text/javascript'}); res.end(fs.readFileSync(files.get(req.url)));}
    else if (req.url === '/') {res.writeHead(200, {'Content-Type': 'text/html'}); res.end('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/physics-phase-lab.css"><body style="padding:16px"><main id="model" style="max-width:1000px;margin:auto"></main><script src="/physics-phase-lab.js"></script>');}
    else {res.writeHead(404); res.end();}
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser, checked = 0;
  try {
    const executablePath = process.env.PHASE_LAB_CHROMIUM_EXECUTABLE || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
    browser = await chromium.launch({headless: true, ...(fs.existsSync(executablePath) ? {executablePath} : {})});
    const page = await browser.newPage();
    const errors = []; page.on('pageerror', err => errors.push(String(err)));
    async function inspect() {
      const rendered = await page.evaluate(() => {
        const root = document.querySelector('[data-renderer="physics-phase-lab"]');
        const attrs = (selector, names) => [...root.querySelectorAll(selector)].map(e => Object.fromEntries(names.map(k => [k, e.getAttribute(k)])));
        const clipped = [...root.querySelectorAll('svg text')].filter(e => {const b = e.getBBox(); return b.x < -1 || b.y < -1 || b.x + b.width > 441 || b.y + b.height > 421;}).map(e => e.textContent);
        return {state: JSON.parse(root.dataset.phaseState), clipped, overflow: document.documentElement.scrollWidth > innerWidth + 1,
          paths: attrs('[data-phase-segment]', ['data-phase-segment', 'd']), fractions: attrs('[data-phase-fraction]', ['data-phase-fraction', 'x', 'width']),
          ledger: attrs('[data-phase-ledger]', ['data-phase-ledger', 'x', 'width']), markers: attrs('[data-phase-marker]', ['data-phase-marker', 'cx', 'cy'])};
      });
      assert.deepEqual(rendered.clipped, []); assert.equal(rendered.overflow, false);
      const s = rendered.state, h0 = starts[s.start], h = h0 + s.energy / s.mass, expected = oracle(h);
      const min = s.mass * (-62.7 - h0), max = s.mass * (3089.4 - h0), X = q => 68 + 344 * (q - min) / (max - min), Y = t => 334 - 238 * (t + 30) / 170;
      rendered.paths.forEach((row, i) => {
        assert.equal(row['data-phase-segment'], keys[i]); const coordinates = row.d.match(/^M([^ ]+) ([^ ]+) L([^ ]+) ([^ ]+)$/).slice(1).map(Number);
        [X(s.mass * (thresholds[i] - h0)), Y(temperatures[i]), X(s.mass * (thresholds[i + 1] - h0)), Y(temperatures[i + 1])].forEach((v, j) => near(coordinates[j], v));
      });
      let x = 28; rendered.fractions.forEach((row, i) => {near(Number(row.x), x); near(Number(row.width), 384 * expected.fractions[i]); x += 384 * expected.fractions[i];});
      const ledger = independentLedger(h0, h, s.mass); rendered.ledger.forEach((row, i) => {near(Number(row.x), 220 + 170 * Math.min(0, ledger[i]) / (s.mass * 2256)); near(Number(row.width), 170 * Math.abs(ledger[i]) / (s.mass * 2256));});
      const current = rendered.markers.find(row => row['data-phase-marker'] === 'current'); near(Number(current.cx), X(s.energy)); near(Number(current.cy), Y(expected.t));
      checked++; return s;
    }
    for (const width of [1440, 390]) {
      await page.setViewportSize({width, height: 980});
      for (const scenario of Object.keys(lab.bindings)) {
        await page.goto(`http://127.0.0.1:${server.address().port}/`);
        await page.evaluate(scenario => {
          const hooks = {speakButton: fn => {window.phaseSpeech = fn; const b = document.createElement('button'); b.dataset.phaseSpeak = ''; b.textContent = 'Read numbers aloud'; b.addEventListener('click', () => {window.phaseSpoken = fn();}); return b;}};
          document.getElementById('model').append(window.PrimerPhysicsPhaseLab.render({props: {scenario}}, hooks));
        }, scenario);
        await inspect();
        for (const start of Object.keys(starts)) {
          await page.locator('[data-phase-start]').selectOption(start); await inspect();
          for (const key of ['mass', 'energy']) for (const end of ['Home', 'End']) {
            const input = page.locator(`[data-phase-control="${key}"]`); await input.focus(); await input.press(end); const s = await inspect();
            near(s[key], key === 'mass' ? (end === 'Home' ? .05 : 2) : s.mass * ((end === 'Home' ? -62.7 : 3089.4) - starts[s.start]));
          }
          for (const target of ['ice0', 'half-melt', 'water0', 'water100', 'half-boil', 'steam100']) {await page.locator(`[data-phase-target="${target}"]`).click(); await inspect();}
        }
        await page.locator('[data-phase-action="cool"]').click(); await inspect();
        await page.locator('[data-phase-speak]').click(); assert.match(await page.evaluate(() => window.phaseSpoken), /kilojoules/);
        await page.locator('[data-phase-action="enlarge"]').click(); await inspect();
        assert.equal(await page.locator('[data-phase-action="enlarge"]').getAttribute('aria-pressed'), 'true');
        await page.locator('[data-phase-action="enlarge"]').click(); await inspect();
        await page.locator('[data-phase-action="reset"]').click(); assert.deepEqual(await inspect(), lab.bindings[scenario]);
        await page.locator('[data-phase-target="half-melt"]').click(); await inspect();
        await page.screenshot({path: path.join(evidence, `${width}-${scenario.includes('hot-cold') ? 'melting' : 'matter'}.png`), fullPage: true});
      }
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(evidence, 'phase-browser-proof.json'), JSON.stringify({checked, viewports: [1440, 390], scenarios: Object.keys(lab.bindings), errors}, null, 2));
    console.log(`Verified ${checked} real-browser phase states, SVG text bounds, keyboard extrema, speech, fit/enlarged layout and body overflow.`);
  } finally {if (browser) await browser.close(); await new Promise(resolve => server.close(resolve));}
}
if (process.argv.includes('--browser')) browserReview().catch(error => {console.error(error); process.exitCode = 1;});
