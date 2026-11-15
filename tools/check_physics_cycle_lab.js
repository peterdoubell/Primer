#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict'), lab = require('../web/physics-cycle-lab.js');
const near = (a, b, t = 4e-10) => assert.ok(Math.abs(a - b) <= t * Math.max(1, Math.abs(a), Math.abs(b)), `${a} != ${b}`);
// R is independently reconstructed from the exact SI-defining k_B and N_A.
const R = 1.380649e-23 * 6.02214076e23, cv = 3 * R / 2, gamma = 5 / 3;
function oracle(s) {
  const ratio = Math.exp(s.hotHeat / (s.moles * R * s.hot)), adiabatic = Math.pow(s.hot / s.cold, 1.5);
  const corner = (name, V, T) => ({name, V, T, p: s.moles * R * T / V, U: s.moles * cv * T});
  const corners = [corner('A', s.volume, s.hot), corner('B', s.volume * ratio, s.hot),
    corner('C', s.volume * ratio * adiabatic, s.cold), corner('D', s.volume * adiabatic, s.cold)];
  const order = s.mode === 'refrigerator' ? [0, 3, 2, 1, 0] : [0, 1, 2, 3, 0];
  const legs = order.slice(0, 4).map((index, i) => {
    const from = corners[index], to = corners[order[i + 1]], isotherm = from.T === to.T;
    const deltaU = s.moles * cv * (to.T - from.T), Wby = isotherm ? s.moles * R * from.T * Math.log(to.V / from.V) : -deltaU;
    return {from, to, isotherm, deltaU, Wby, Q: isotherm ? Wby : 0};
  });
  return {corners, legs};
}
function point(s, leg, fraction) {
  const V = leg.from.V * Math.pow(leg.to.V / leg.from.V, fraction);
  const T = leg.isotherm ? leg.from.T : leg.from.T * Math.pow(leg.from.V / V, 2 / 3);
  return {V, T, p: s.moles * R * T / V, U: s.moles * cv * T,
    S: s.moles * cv * Math.log(T / s.hot) + s.moles * R * Math.log(V / s.volume)};
}
// Composite Simpson integration in log(V), explicitly integrating pressure dV
// from ideal-gas / polytropic states, rather than using exported work values.
function integratedWork(leg) {
  const a = Math.log(leg.from.V), b = Math.log(leg.to.V), count = 128, dx = (b - a) / count;
  const integrand = x => leg.from.p * Math.pow(leg.from.V / Math.exp(x), leg.isotherm ? 1 : gamma) * Math.exp(x);
  let sum = integrand(a) + integrand(b);
  for (let i = 1; i < count; i++) sum += (i % 2 ? 4 : 2) * integrand(a + i * dx);
  return sum * dx / 3;
}
let balances = 0, integrations = 0;
for (const hot of [250, 600, 1200]) for (const cold of [100, 240, 300, 590, 1100]) for (const moles of [.05, .1, 1])
for (const volume of [.0005, .01]) for (const hotHeat of [10, 400, 2000]) for (const leak of [0, 400, 2000]) for (const mode of ['engine', 'refrigerator']) {
  const m = lab.build({mode, hot, cold, moles, volume, hotHeat, leak}), s = m.state, o = oracle(s), sign = mode === 'engine' ? 1 : -1;
  assert.ok(s.cold < s.hot && s.cold <= s.hot - 10); assert.ok(m.ratio <= 8 + 1e-12);
  m.corners.forEach((q, i) => {assert.equal(q.name, o.corners[i].name); for (const key of ['V', 'T', 'p', 'U']) near(q[key], o.corners[i][key]);});
  let integrated = 0, renderedArea = 0;
  m.legs.forEach((l, i) => {
    const expected = o.legs[i]; near(l.Q, expected.Q); near(l.Wby, expected.Wby); near(l.deltaU, expected.deltaU); near(l.deltaU, l.Q - l.Wby);
    const work = integratedWork(expected); near(work, l.Wby, 2e-9); integrated += work; integrations++;
    assert.equal(l.points.length, 121);
    l.points.forEach((q, j) => {
      const expectedPoint = point(s, expected, j / 120);
      for (const key of ['V', 'T', 'p', 'U', 'S']) near(q[key], expectedPoint[key]);
      near(q.p * q.V, s.moles * R * q.T); near(q.U, s.moles * cv * q.T); near(q.deltaU, q.Q - q.Wby);
      if (!expected.isotherm) {near(q.T * q.V ** (2 / 3), expected.from.T * expected.from.V ** (2 / 3)); assert.equal(q.Q, 0); assert.equal(q.deltaS, 0);}
      if (j) {const prev = l.points[j - 1]; renderedArea += (q.V - prev.V) * (q.p + prev.p) / 2;}
    });
    for (const key of ['V', 'T', 'p', 'U', 'S']) near(l.points.at(-1)[key], m.legs[(i + 1) % 4].points[0][key]);
  });
  near(integrated, m.Wby, 3e-8); near(renderedArea, m.Wby, 6e-5);
  near(m.legs.reduce((v, l) => v + l.deltaU, 0), 0); near(m.legs.reduce((v, l) => v + l.deltaS, 0), 0);
  near(m.legs.reduce((v, l) => v + l.Q, 0), m.Wby); near(m.legs.reduce((v, l) => v + l.Wby, 0), m.Wby);
  near(m.coldGasHeat / s.hotHeat, s.cold / s.hot); near(m.Wby, sign * s.hotHeat * (1 - s.cold / s.hot));
  near(m.hotReservoirHeat, -sign * s.hotHeat - s.leak); near(m.coldReservoirHeat, sign * s.hotHeat * s.cold / s.hot + s.leak);
  near(m.hotReservoirEntropy, m.hotReservoirHeat / s.hot); near(m.coldReservoirEntropy, m.coldReservoirHeat / s.cold);
  near(m.entropyProduced, s.leak * (1 / s.cold - 1 / s.hot)); near(m.hotReservoirEntropy + m.coldReservoirEntropy, m.entropyProduced);
  assert.ok(m.entropyProduced >= 0); if (s.leak === 0) assert.equal(m.entropyProduced, 0);
  near(m.hotReservoirHeat + m.coldReservoirHeat + m.Wby, 0);
  if (mode === 'engine') {assert.ok(m.efficiency <= m.carnotEfficiency + 1e-14); near(m.efficiency, m.Wby / (s.hotHeat + s.leak));}
  else {near(m.roomHeat, -m.Wby); near(m.hotReservoirHeat + m.coldReservoirHeat, m.roomHeat); near(m.hotDelivery, m.coldExtraction + m.workMagnitude);
    if (m.coldExtraction < 0) assert.equal(m.cop, null); else {near(m.cop, m.coldExtraction / m.workMagnitude); assert.ok(m.cop <= m.carnotCop + 1e-12);}}
  balances++;
}
const quiz = lab.build({...lab.initial, leak: 400});
assert.equal(quiz.totalHotInput, 800); assert.equal(quiz.totalColdRejection, 600); assert.equal(quiz.Wby, 200); assert.equal(quiz.efficiency, .25); near(quiz.entropyProduced, 2 / 3);
const idealFridge = lab.build({mode: 'refrigerator'}); assert.equal(idealFridge.cop, 1); assert.equal(idealFridge.heatPumpCop, 2); assert.equal(idealFridge.roomHeat, 200);
assert.equal(idealFridge.totalHotInput, null); assert.equal(idealFridge.totalColdRejection, null);
assert.equal(lab.build({}).coldExtraction, null); assert.equal(lab.build({}).hotDelivery, null);
const cancelled = lab.build({mode: 'refrigerator', leak: 200}); assert.equal(cancelled.coldExtraction, 0); assert.equal(cancelled.cop, 0);
assert.equal(lab.build({mode: 'refrigerator', leak: 201}).cop, null);
const tinyLeak = lab.build({leak: 1e-16}); assert.equal(tinyLeak.state.leak, 1e-16); assert.ok(tinyLeak.entropyProduced > 0); assert.match(tinyLeak.readout, /entropy produced = [^ ]*e-/);
for (const s of [{}, {hot: 1200, cold: 1100, hotHeat: 10, moles: 1}, {hot: 250, cold: 100, hotHeat: 2000, moles: .05}]) {
  const engine = lab.build(s), fridge = lab.build({...s, mode: 'refrigerator'}); near(engine.Wby, -fridge.Wby);
  for (let i = 0; i < 4; i++) for (const u of [0, .00001, .2, .5, .99, 1]) {
    const a = lab.stateAtLeg({...s, mode: 'engine'}, i, u), b = lab.stateAtLeg({...s, mode: 'refrigerator'}, 3 - i, 1 - u);
    for (const key of ['V', 'T', 'p', 'U', 'S']) near(a[key], b[key]);
  }
}
for (const heat of [-1000, -150, 0, 500, 1000]) for (const work of [-1000, -400, 0, 200, 1000]) {
  const m = lab.build({mode: 'first-law', heat, work}); assert.equal(m.deltaU, heat - work); assert.equal(m.workOn, -work); assert.ok(!('legs' in m) && !('current' in m)); balances++;
}
assert.equal(lab.build({mode: 'first-law', heat: -150, work: -400}).deltaU, 250);
assert.equal(lab.build({mode: 'first-law', heat: 0, work: -400}).deltaU, 400);
for (const invalid of [NaN, Infinity, -Infinity, null, undefined, '', true, {}, 'bad']) for (const c of lab.controls) assert.equal(lab.normalize({[c.key]: invalid})[c.key], lab.initial[c.key]);
for (const args of [[{}, -1, .5], [{}, 4, .5], [{}, 0, -1], [{}, 0, Infinity], [{mode: 'first-law'}, 0, .5]]) assert.throws(() => lab.stateAtLeg(...args), RangeError);

class E {
  constructor(tag) {this.tagName = tag; this.nodeType = 1; this.attributes = {}; this.children = []; this.listeners = {}; this.value = ''; this.classList = {toggle: (k, on) => {const s = new Set((this.attributes.class || '').split(' ')); on ? s.add(k) : s.delete(k); this.attributes.class = [...s].join(' ');}};}
  setAttribute(k, v) {this.attributes[k] = String(v);} getAttribute(k) {return this.attributes[k];}
  append(...x) {this.children.push(...x);} replaceChildren(...x) {this.children = x;} addEventListener(k, fn) {this.listeners[k] = fn;}
  get textContent() {return this.children.map(x => x.textContent).join('');} set textContent(v) {this.children = [{nodeType: 3, textContent: String(v)}];}
}
global.document = {createElement: t => new E(t), createElementNS: (_, t) => new E(t), createTextNode: v => ({nodeType: 3, textContent: String(v)})};
const all = e => [e, ...(e.children || []).flatMap(x => x.nodeType === 1 ? all(x) : [])];
let speech, mounts = 0;
const root = lab.render({props: {scenario: 'phys.3.thermo.cycle-entropy'}}, {speakButton: fn => {speech = fn; return new E('button');}});
const find = (k, v) => all(root).find(e => e.attributes?.[k] === v);
function checkMounted() {
  const s = JSON.parse(root.getAttribute('data-cycle-state')), budget = s.mode === 'first-law', elements = all(root), paths = elements.filter(e => e.attributes?.['data-cycle-path'] != null);
  if (!budget) {
    const o = oracle(s), maxV = Math.max(...o.corners.map(q => q.V)) * 1.06, maxP = Math.max(...o.corners.map(q => q.p)) * 1.08;
    near(paths.length, 4); let area = 0;
    paths.forEach((e, i) => {const coords = e.getAttribute('d').match(/[ML][^ML]+/g).map(v => v.slice(1).split(' ').map(Number)); assert.equal(coords.length, 121);
      coords.forEach((xy, j) => {const p = point(s, o.legs[i], j / 120); near(xy[0], 72 + 340 * p.V / maxV); near(xy[1], 334 - 244 * p.p / maxP);
        if (j) {const a = coords[j - 1]; area += (xy[0] - a[0]) * maxV / 340 * ((334 - xy[1]) + (334 - a[1])) * maxP / 244 / 2;}});
    });
    near(area, (s.mode === 'engine' ? 1 : -1) * s.hotHeat * (1 - s.cold / s.hot), 6e-5);
    const p = point(s, o.legs[s.leg], s.progress / 100), marker = find('data-cycle-marker', ''); near(Number(marker.getAttribute('cx')), 72 + 340 * p.V / maxV); near(Number(marker.getAttribute('cy')), 334 - 244 * p.p / maxP);
    o.corners.forEach(q => {const e = find('data-cycle-corner', q.name); near(Number(e.getAttribute('cx')), 72 + 340 * q.V / maxV); near(Number(e.getAttribute('cy')), 334 - 244 * q.p / maxP);});
    const sign = s.mode === 'engine' ? 1 : -1, values = {hot: (-sign * s.hotHeat - s.leak) / s.hot, cold: (sign * s.hotHeat * s.cold / s.hot + s.leak) / s.cold, gas: 0, produced: s.leak * (1 / s.cold - 1 / s.hot)};
    for (const [key, value] of Object.entries(values)) {const b = find('data-cycle-balance', key), scale = Number(b.getAttribute('data-cycle-axis')); near(Number(b.getAttribute('x')), 220 + 170 * Math.min(0, value) / scale); near(Number(b.getAttribute('width')), 170 * Math.abs(value) / scale);}
  } else {
    for (const [key, value] of [['Q', s.heat], ['-Wby', -s.work], ['deltaU', s.heat - s.work]]) {const b = find('data-cycle-balance', key), scale = Number(b.getAttribute('data-cycle-axis')); near(Number(b.getAttribute('x')), 220 + 170 * Math.min(0, value) / scale); near(Number(b.getAttribute('width')), 170 * Math.abs(value) / scale);}
  }
  for (const c of lab.controls) {const input = find('data-cycle-control', c.key), number = find('data-cycle-number', c.key); assert.equal(input.disabled, !c.modes.includes(s.mode)); assert.equal(number.disabled, input.disabled);}
  assert.match(speech(), /joules/); if (!budget) {assert.match(speech(), /entropy produced/); assert.match(speech(), /pascals/);} mounts++;
}
checkMounted();
for (const mode of ['engine', 'refrigerator', 'first-law']) {
  const select = find('data-cycle-mode', ''); select.value = mode; select.listeners.change(); checkMounted();
  for (const c of lab.controls.filter(c => c.modes.includes(mode))) {
    const range = find('data-cycle-control', c.key);
    for (const v of [range.min, range.max]) {range.value = v; range.listeners.input(); range.listeners.change(); checkMounted();}
    const number = find('data-cycle-number', c.key); number.value = lab.initial[c.key]; number.listeners.change(); checkMounted();
  }
  if (mode !== 'first-law') for (let i = 0; i < 4; i++) {const leg = find('data-cycle-leg', ''); leg.value = i; leg.listeners.change(); const progress = find('data-cycle-control', 'progress'); progress.value = 37; progress.listeners.input(); checkMounted();}
}
for (const b of all(root).filter(e => e.attributes?.['data-cycle-preset'])) {b.listeners.click(); checkMounted();}
find('data-cycle-action', 'cancel-cooling').listeners.click(); checkMounted();
find('data-cycle-action', 'reset').listeners.click(); checkMounted(); assert.deepEqual(JSON.parse(root.getAttribute('data-cycle-state')), lab.initial);
const enlarge = find('data-cycle-action', 'enlarge'); enlarge.listeners.click(); assert.equal(enlarge.getAttribute('aria-pressed'), 'true'); enlarge.listeners.click(); assert.equal(enlarge.getAttribute('aria-pressed'), 'false');
assert.equal(lab.render({props: {scenario: 'wrong'}}), null); assert.equal(lab.render({props: {scenario: 'phys.3.thermo.cycle-entropy', extra: true}}), null);
console.log(`Verified ${balances} cycle/first-law balances, ${integrations} independent pressure-work integrals and ${mounts} mounted physical-coordinate states.`);

async function browserReview() {
  const fs = require('node:fs'), path = require('node:path'), http = require('node:http'), {chromium} = require('playwright'), {createEvidenceDirectory} = require('./qa-browser.cjs');
  const source = path.resolve(__dirname, '..'), evidence = createEvidenceDirectory(), files = new Map(['/styles.css', '/physics-cycle-lab.css', '/physics-cycle-lab.js'].map(url => [url, path.join(source, 'web', url.slice(1))]));
  const server = http.createServer((req, res) => {
    if (files.has(req.url)) {res.writeHead(200, {'Content-Type': req.url.endsWith('.css') ? 'text/css' : 'text/javascript'}); res.end(fs.readFileSync(files.get(req.url)));}
    else if (req.url === '/') {res.writeHead(200, {'Content-Type': 'text/html'}); res.end('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/physics-cycle-lab.css"><body style="padding:16px"><main id="model" style="max-width:1000px;margin:auto"></main><script src="/physics-cycle-lab.js"></script>');}
    else {res.writeHead(404); res.end();}
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve)); let browser, checked = 0;
  try {
    const executablePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
    browser = await chromium.launch({headless: true, ...(fs.existsSync(executablePath) ? {executablePath} : {})}); const page = await browser.newPage(), errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    for (const width of [1440, 390]) {
      await page.setViewportSize({width, height: 980}); await page.goto(`http://127.0.0.1:${server.address().port}/`);
      await page.evaluate(() => {document.getElementById('model').append(window.PrimerPhysicsCycleLab.render({props: {scenario: 'phys.3.thermo.cycle-entropy'}}, {speakButton: fn => {const b = document.createElement('button'); b.dataset.cycleSpeak = ''; b.textContent = 'Read numbers aloud'; b.addEventListener('click', () => {window.cycleSpoken = fn();}); return b;}}));});
      const root = page.locator('.physics-cycle-lab');
      async function inspect() {
        const r = await root.evaluate(root => {
          const svgs = [...root.querySelectorAll('.cycle-viewport:not([hidden]) svg')], labels = [...root.querySelectorAll('[data-cycle-label]')].map(e => {const b = e.getBBox(); return {text: e.textContent, x: b.x, y: b.y, w: b.width, h: b.height};});
          const clipped = svgs.flatMap(svg => [...svg.querySelectorAll('text')].filter(e => {const b = e.getBBox(); return b.x < -.5 || b.y < -.5 || b.x + b.width > 440.5 || b.y + b.height > 420.5;}).map(e => e.textContent));
          return {state: JSON.parse(root.dataset.cycleState), clipped, labels, overflow: document.documentElement.scrollWidth > innerWidth + 1, marker: root.querySelector('[data-cycle-marker]') ? ['cx', 'cy'].map(k => Number(root.querySelector('[data-cycle-marker]').getAttribute(k))) : null};
        });
        assert.equal(r.overflow, false); assert.deepEqual(r.clipped, []);
        if (r.state.mode !== 'first-law') {
          const o = oracle(r.state), p = point(r.state, o.legs[r.state.leg], r.state.progress / 100), maxV = Math.max(...o.corners.map(q => q.V)) * 1.06, maxP = Math.max(...o.corners.map(q => q.p)) * 1.08;
          near(r.marker[0], 72 + 340 * p.V / maxV); near(r.marker[1], 334 - 244 * p.p / maxP);
          for (let i = 0; i < r.labels.length; i++) for (const b of r.labels.slice(i + 1)) {const a = r.labels[i]; assert.ok(!(a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y), 'Overlapping cycle state labels');}
        }
        checked++; return r.state;
      }
      await inspect();
      for (const mode of ['engine', 'refrigerator', 'first-law']) {
        await root.locator('[data-cycle-mode]').selectOption(mode); await inspect();
        for (const c of lab.controls.filter(c => c.modes.includes(mode))) {
          const range = root.locator(`[data-cycle-control="${c.key}"]`);
          for (const end of ['Home', 'End']) {await range.focus(); await range.press(end); await inspect();}
          const number = root.locator(`[data-cycle-number="${c.key}"]`); await number.fill(String(lab.initial[c.key])); await number.press('Tab'); await inspect();
        }
        if (mode !== 'first-law') for (let i = 0; i < 4; i++) {await root.locator('[data-cycle-leg]').selectOption(String(i)); await root.locator('[data-cycle-number=progress]').fill('37'); await root.locator('[data-cycle-number=progress]').press('Tab'); await inspect();}
        await root.locator('[data-cycle-speak]').click(); assert.match(await page.evaluate(() => window.cycleSpoken), /joules/);
        await page.screenshot({path: path.join(evidence, `${width}-${mode}.png`), fullPage: true});
      }
      for (const key of ['reversible', 'quiz-engine', 'fridge', 'first-law-300', 'first-law-250', 'compression']) {await root.locator(`[data-cycle-preset="${key}"]`).click(); await inspect();}
      await root.locator('[data-cycle-action=cancel-cooling]').click(); await inspect();
      await root.locator('[data-cycle-action=reset]').click(); assert.deepEqual(await inspect(), lab.initial);
      await root.locator('[data-cycle-action=enlarge]').click(); await inspect(); assert.ok(await root.locator('svg').first().evaluate(e => e.getBoundingClientRect().width) >= 660);
      await root.locator('[data-cycle-action=enlarge]').click(); await inspect();
      await root.locator('[data-cycle-preset=quiz-engine]').click(); await inspect(); await page.screenshot({path: path.join(evidence, `${width}-quiz-engine.png`), fullPage: true});
    }
    assert.deepEqual(errors, []); fs.writeFileSync(path.join(evidence, 'cycle-browser-proof.json'), JSON.stringify({checked, errors, viewports: [1440, 390]}, null, 2));
    console.log(`Verified ${checked} browser cycle states, keyboard/numeric controls, state-label bounds, speech, fit/enlarged layout and overflow.`);
  } finally {if (browser) await browser.close(); await new Promise(resolve => server.close(resolve));}
}
if (process.argv.includes('--browser')) browserReview().catch(e => {console.error(e); process.exitCode = 1;});
