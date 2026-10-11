#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict'), fs = require('node:fs'), lab = require('../web/physics-ensemble-lab.js');
if (process.argv.includes('--oracle-json')) {
  const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
  assert.ok(Array.isArray(cases) && cases.length <= 100);
  fs.writeFileSync(1, JSON.stringify(cases.map(s => lab.build(s)), (_, v) => typeof v === 'bigint' ? v.toString() : v) + '\n');
  process.exit(0);
}
const near = (a, b, t = 3e-11) => assert.ok(Math.abs(a - b) <= t * Math.max(1, Math.abs(a), Math.abs(b)), `${a} != ${b}`);
const factorial = n => {let f = 1n; for (let k = 2n; k <= BigInt(n); k++) f *= k; return f;};
const independentChoose = (n, j) => factorial(n) / (factorial(j) * factorial(n - j));
let exactCounts = 0, canonicalStates = 0, blockStates = 0, mountedStates = 0;
for (const N of [1, 3, 4, 8, 16, 64, 1000, 1024]) {
  const m = lab.build({mode: 'coins', N, j: Math.floor(N / 2)});
  assert.equal(m.totalStates, 1n << BigInt(N)); assert.equal(m.x, 0); assert.equal(m.pUpper, .5); assert.equal(m.upperProbability.value, .5); near(m.gibbsOverK, Math.LN2);
  assert.equal(m.rows.reduce((n, row) => n + row.omega, 0n), m.totalStates);
  for (const j of [...new Set([0, 1, Math.floor(N / 2), N - 1, N])]) {assert.equal(m.rows[j].omega, independentChoose(N, j)); assert.equal(lab.choose(N, j), m.rows[j].omega); exactCounts++;}
  near(m.rows.reduce((p, row) => p + (row.probability.value || 0), 0), 1);
  near(m.microGibbsOverK, N * Math.LN2); near(m.entropyDecompositionResidual, 0, 1e-10);
  assert.equal(m.rows[0].logOmega, 0); assert.equal(m.rows[N].logOmega, 0);
}
assert.equal(lab.choose(64, 32), 1832624140942590534n);
near(lab.logBigInt(lab.choose(1000, 500)), 689.4672615678512);
assert.deepEqual(lab.build({mode: 'coins', N: 3}).rows.map(r => r.omega), [1n, 3n, 3n, 1n]);
assert.deepEqual(lab.build({mode: 'coins', N: 4}).rows.map(r => r.omega), [1n, 4n, 6n, 4n, 1n]);
const small = lab.build({mode: 'coins', N: 3, j: 1});
assert.deepEqual(small.enumeration.filter(s => s.j === 1).map(s => s.bits), ['001', '010', '100']);
assert.equal(small.enumeration.length, 8); near(small.microGibbsOverK, Math.log(8));
const four = lab.build({mode: 'coins', N: 4, j: 2}); near(four.multiplicityOverK, Math.log(6)); near(four.macroGibbsOverK, 1.407531740719315); near(four.microGibbsOverK, Math.log(16));

function strings(n) {if (!n) return ['']; return strings(n - 1).flatMap(s => [s + '0', s + '1']);}
for (const N of [1, 3, 4, 8]) for (const x of [0, .01, 1, 2, 10, 40]) {
  const temperature = 100, gap = x * 1.380649e-23 * temperature / 1e-21, m = lab.build({mode: 'particles', N, j: Math.floor(N / 2), temperature, gap});
  const states = strings(N).map(bits => ({bits, j: [...bits].filter(b => b === '1').length}));
  const partition = states.reduce((Z, s) => Z + Math.exp(-x * s.j), 0);
  const probabilities = states.map(s => Math.exp(-x * s.j) / partition);
  const entropy = -probabilities.reduce((S, p) => S + (p ? p * Math.log(p) : 0), 0);
  near(m.microGibbsOverK, entropy);
  near(m.meanUpperCount, states.reduce((n, s, i) => n + s.j * probabilities[i], 0));
  m.rows.forEach(row => {near(row.probability.value || 0, states.reduce((p, s, i) => p + (s.j === row.j ? probabilities[i] : 0), 0));});
  near(m.entropyDecompositionResidual, 0); assert.ok(m.microGibbsOverK > 0);
  assert.deepEqual(m.enumeration.map(s => s.bits), states.map(s => s.bits).sort()); canonicalStates++;
}
const canonical = lab.build(); near(canonical.populationRatio.value, Math.exp(-1)); near(canonical.pUpper, 1 / (1 + Math.E)); near(canonical.gibbsOverK, .5822031088882179);
assert.notEqual(canonical.populationRatio.value, canonical.pUpper);
for (const temperature of [1, 100, 300, 1200]) for (const gap of [0, 1e-16, 1, 10, 100]) {
  const m = lab.build({temperature, gap}); assert.ok(m.state.temperature > 0 && m.x >= 0 && m.x <= 40 + 1e-13);
  assert.ok(m.pUpper > 0 && m.upperProbability.value > 0 && m.gibbsOverK > 0); near(m.pUpper + m.pLower, 1); canonicalStates++;
}
const tail = lab.build({mode: 'particles', temperature: 1, gap: 100, N: 1024, j: 1024});
assert.equal(tail.macroProbability.value, null); assert.ok(tail.macroProbability.positive); assert.ok(Number.isFinite(tail.macroLogP)); assert.match(tail.macroProbability.display, /positive; ln P/); assert.ok(tail.microGibbsOverK > 0);
for (const log10N of [0, 1, 4, 25]) for (const volumeRatio of [1, 1.00000001, 2, 10]) {
  const m = lab.build({mode: 'expansion', log10N, volumeRatio}), N = 10n ** BigInt(log10N);
  assert.equal(m.particleCount, N); near(m.entropyOverK, Number(N) * Math.log(volumeRatio)); near(m.logP, -m.entropyOverK);
  assert.equal(m.Q, 0); assert.equal(m.Wby, 0); assert.equal(m.deltaU, 0); assert.equal(m.deltaT, 0); assert.ok(m.allInOriginalProbability.positive);
  if (volumeRatio === 1) {assert.equal(m.allInOriginalProbability.value, 1); assert.equal(m.entropyOverK, 0);}
  else assert.ok(m.entropyOverK > 0 && m.logP < 0);
}
assert.equal(lab.build({mode: 'expansion', log10N: 25}).allInOriginalProbability.value, null);

// Independent integration of the positive entropy-production derivative in the
// transferred-energy parameter, rather than reusing C ln(T/T_initial).
function integrate(f, lo, hi, tolerance = 1e-8) {
  const simpson = (a, b, fa, fm, fb) => (b - a) / 6 * (fa + 4 * fm + fb);
  const walk = (a, b, fa, fm, fb, whole, tol, depth) => {const mid = (a + b) / 2, lm = (a + mid) / 2, rm = (mid + b) / 2, fl = f(lm), fr = f(rm), left = simpson(a, mid, fa, fl, fm), right = simpson(mid, b, fm, fr, fb), delta = left + right - whole;
    if (!depth || Math.abs(delta) <= 15 * tol) return left + right + delta / 15;
    return walk(a, mid, fa, fl, fm, left, tol / 2, depth - 1) + walk(mid, b, fm, fr, fb, right, tol / 2, depth - 1);};
  const fa = f(lo), fb = f(hi), fm = f((lo + hi) / 2); return walk(lo, hi, fa, fm, fb, simpson(lo, hi, fa, fm, fb), tolerance, 24);
}
for (const tempA of [1, 300, 600, 1200]) for (const tempB of [1, 300, 600, 1200]) for (const capacityA of [1, 100, 1000]) for (const capacityB of [1, 100, 1000]) for (const transfer of [0, 25, 100]) {
  const m = lab.build({mode: 'blocks', tempA, tempB, capacityA, capacityB, transfer}), f = transfer / 100, q = capacityA * capacityB / (capacityA + capacityB) * (tempA - tempB);
  near(m.Tf, (capacityA * tempA + capacityB * tempB) / (capacityA + capacityB)); near(m.heatA + m.heatB, 0);
  near(capacityA * m.tempA + capacityB * m.tempB, capacityA * tempA + capacityB * tempB);
  const entropy = integrate(u => {const a = tempA - u * q / capacityA, b = tempB + u * q / capacityB; return q * (a - b) / (a * b);}, 0, f);
  near(m.totalEntropy, entropy, 1e-9); assert.ok(m.totalEntropy >= 0);
  if (tempA === tempB || transfer === 0) assert.equal(m.totalEntropy, 0); blockStates++;
}
for (const difference of [1e-12, 1e-8, .001]) {const m = lab.build({mode: 'blocks', tempA: 300 + difference, tempB: 300, transfer: 100}); assert.ok(m.totalEntropy > 0);}
for (const invalid of [null, undefined, '', NaN, Infinity, true, {}, 'bad']) for (const c of lab.controls) assert.equal(lab.normalize({[c.key]: invalid})[c.key], lab.initial[c.key]);
assert.equal(lab.normalize({N: 3, j: 9}).j, 3); assert.equal(lab.normalize({N: 3.6, j: 2.2}).N, 4);
assert.throws(() => lab.choose(1025, 1), RangeError); assert.throws(() => lab.logBigInt(0n), RangeError);

class E {
  constructor(tag) {this.tagName = tag; this.nodeType = 1; this.attributes = {}; this.children = []; this.listeners = {}; this.value = ''; this.classList = {toggle: (k, on) => {const s = new Set((this.attributes.class || '').split(' ')); on ? s.add(k) : s.delete(k); this.attributes.class = [...s].join(' ');}};}
  setAttribute(k, v) {this.attributes[k] = String(v);} getAttribute(k) {return this.attributes[k];}
  append(...cs) {this.children.push(...cs);} replaceChildren(...cs) {this.children = cs;}
  addEventListener(name, listener) {this.listeners[name] = listener;}
  set textContent(v) {this.children = [String(v)];} get textContent() {return this.children.map(c => typeof c === 'string' ? c : c.textContent).join('');}
}
global.document = {createElement: tag => new E(tag), createElementNS: (_, tag) => new E(tag), createTextNode: text => ({nodeType: 3, textContent: text})};
let speech;
const root = lab.render({props: {scenario: lab.scenario}}, {speakButton: get => {speech = get; return new E('button');}});
const all = e => [e, ...e.children.flatMap(c => typeof c === 'object' && c.children ? all(c) : [])];
const find = (key, value) => all(root).find(e => e.attributes?.[key] === String(value));
function checkMounted() {
  const state = JSON.parse(root.getAttribute('data-ensemble-state')), expected = lab.build(state);
  assert.equal(find('class', 'ensemble-readout').textContent, expected.readout); assert.ok(speech().includes(expected.equation));
  for (const c of lab.controls) {const range = find('data-ensemble-control', c.key), number = find('data-ensemble-number', c.key); assert.equal(range.disabled, !c.modes.includes(state.mode)); assert.equal(number.disabled, range.disabled);}
  if (state.mode === 'canonical') for (const [index, p] of [[0, expected.pLower], [1, expected.pUpper]]) {const bar = find('data-ensemble-population', index); near(Number(bar.getAttribute('height')), 160 * p); near(Number(bar.getAttribute('data-probability')), p);}
  if (state.mode === 'coins' || state.mode === 'particles') {const plot = find('data-ensemble-distribution', ''), low = Number(plot.getAttribute('data-min-log')); const points = plot.getAttribute('points').split(' ').map(x => x.split(',').map(Number)); assert.equal(points.length, state.N + 1);
    points.forEach(([x, y], j) => {near(x, 65 + 405 * j / state.N); near(y, 70 - 215 * expected.rows[j].macroLogP / (-low));});}
  if (state.mode === 'expansion') near(Number(find('data-ensemble-original-region', '').getAttribute('width')), 405 / state.volumeRatio);
  if (state.mode === 'blocks') for (const name of ['A', 'B']) near(Number(find('data-ensemble-block', name).getAttribute('data-temperature')), expected['temp' + name]);
  mountedStates++;
}
checkMounted();
for (const [mode] of lab.modes) {const select = find('data-ensemble-mode', ''); select.value = mode; select.listeners.change(); checkMounted();
  for (const c of lab.controls.filter(c => c.modes.includes(mode))) {const range = find('data-ensemble-control', c.key); for (const end of [range.min, range.max]) {range.value = end; range.listeners.input(); range.listeners.change(); checkMounted();}
    const number = find('data-ensemble-number', c.key), before = root.getAttribute('data-ensemble-state'); number.value = ''; assert.equal(number.listeners.input, undefined); assert.equal(root.getAttribute('data-ensemble-state'), before); number.listeners.change(); checkMounted();}
}
for (const b of all(root).filter(e => e.attributes?.['data-ensemble-preset'])) {b.listeners.click(); checkMounted();}
find('data-ensemble-action', 'reset').listeners.click(); checkMounted(); assert.deepEqual(JSON.parse(root.getAttribute('data-ensemble-state')), lab.initial);
find('data-ensemble-action', 'enlarge').listeners.click(); assert.equal(find('data-ensemble-action', 'enlarge').getAttribute('aria-pressed'), 'true');
assert.equal(lab.render({props: {scenario: 'wrong'}}), null); assert.equal(lab.render({props: {scenario: lab.scenario, extra: true}}), null);
console.log(`Verified ${exactCounts} independent exact factorial counts, ${canonicalStates} canonical/enumerated states, ${blockStates} independent entropy quadratures and ${mountedStates} mounted physical-coordinate states.`);

async function browserReview() {
  const path = require('node:path'), crypto = require('node:crypto'), {chromium} = require('playwright');
  const {createEvidenceDirectory, loopbackQaUrl} = require('./qa-browser.cjs');
  const origin = loopbackQaUrl(process.argv[process.argv.indexOf('--browser') + 1]), evidence = createEvidenceDirectory();
  const proof = {origin, productionVerified: false, rows: [], errors: [], failures: []};
  const browser = await chromium.launch({headless: true, ...(process.platform === 'darwin' ? {executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'} : {})});
  let reviewPage;
  try {
    const context = await browser.newContext({viewport: {width: 1440, height: 980}, reducedMotion: 'reduce'}), page = await context.newPage();
    reviewPage = page;
    page.on('pageerror', e => proof.errors.push(String(e)));
    page.on('response', r => {if (r.url().startsWith(origin) && r.status() >= 400) proof.failures.push({url: r.url(), status: r.status()});});
    await page.addInitScript(() => {localStorage.setItem('primer-speak', '0'); localStorage.setItem('primer-theme', 'light');});
    await page.goto(origin + '/sign-in'); await page.locator('[name=username]').fill('reader'); await page.locator('[name=password]').fill('qa-only');
    await page.getByRole('button', {name: 'Open the book →', exact: true}).click(); await page.waitForURL(url => !url.pathname.includes('sign-in'));
    const response = await context.request.get(origin + '/api/curriculum/node/phys.4.statmech'); assert.equal(response.status(), 200);
    proof.binding = (await response.json()).lesson_media.filter(m => m.renderer === 'physics-ensemble-lab');
    assert.equal(proof.binding.length, 1); assert.deepEqual(proof.binding[0].props, {scenario: lab.scenario});
    for (const width of [1440, 390]) {
      await page.setViewportSize({width, height: 980}); await page.goto(origin + '/?ensemble_qa=' + width + '#/node/phys.4.statmech');
      const root = page.locator('.physics-ensemble-lab'); await root.waitFor({state: 'visible'});
      const skip = page.getByRole('button', {name: 'Skip for now', exact: true}); if (await skip.isVisible()) {await skip.click(); await page.reload(); await root.waitFor({state: 'visible'});}
      await root.locator('[data-ensemble-action=reset]').click();
      const row = {width, states: [], endpoints: [], drafts: [], speech: []}; proof.rows.push(row);
      const snap = async () => {
        const r = await root.evaluate(e => ({state: JSON.parse(e.dataset.ensembleState), readout: e.querySelector('.ensemble-readout').textContent,
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
          bars: [...e.querySelectorAll('[data-ensemble-population]')].map(b => ({p: Number(b.dataset.probability), h: Number(b.getAttribute('height'))})),
          rows: [...e.querySelectorAll('[data-ensemble-row]')].map(r => ({j: Number(r.dataset.ensembleRow), values: [...r.children].map(c => c.textContent)})),
          enumeration: [...e.querySelectorAll('[data-ensemble-bits]')].map(b => b.dataset.ensembleBits),
          labels: [...e.querySelectorAll('svg text')].map(t => {const b = t.getBBox(); return {text: t.textContent, x: b.x, y: b.y, w: b.width, h: b.height};})}));
        assert.equal(r.overflow, false); assert.ok(!/NaN|Infinity/.test(r.readout));
        for (const b of r.labels) assert.ok(b.x >= -.5 && b.y >= -.5 && b.x + b.w <= 500.5 && b.y + b.h <= 340.5, 'clipped ' + b.text);
        return r;
      };
      const numeric = async (key, value) => {const e = root.locator('[data-ensemble-number=' + key + ']'); await e.fill(String(value)); await e.press('Tab'); return snap();};
      const speak = async mode => {
        const r = await root.evaluate(e => {const ss = speechSynthesis, a = ss.speak, b = ss.cancel, chunks = [], expected = e.querySelector('.ensemble-readout').textContent + ' ' + e.querySelector('.ensemble-equation').textContent;
          try {ss.speak = u => {chunks.push(u.text); u.onend?.();}; ss.cancel = () => {}; e.querySelector('.speak-btn').click();} finally {ss.speak = a; ss.cancel = b;}
          return {expected, chunks, exact: chunks.join(' ') === expected.replace(/\s+/g, ' ').trim(), longest: Math.max(...chunks.map(t => t.length))};});
        assert.ok(r.exact && r.chunks.length && r.longest <= 1200); row.speech.push({mode, ...r});
      };
      const shot = async name => {await root.locator('.ensemble-viewport').scrollIntoViewIfNeeded(); await page.screenshot({path: path.join(evidence, width + '-' + name + '.png')});};
      for (const [mode] of lab.modes) {
        await root.locator('[data-ensemble-mode]').selectOption(mode); assert.equal((await snap()).state.mode, mode);
        for (const c of lab.controls.filter(c => c.modes.includes(mode))) {
          const input = root.locator('[data-ensemble-control=' + c.key + ']');
          for (const end of ['Home', 'End']) {
            const bound = Number(await input.getAttribute(end === 'Home' ? 'min' : 'max'));
            await input.focus(); await input.press(end); const actual = await snap(); near(actual.state[c.key], bound);
            row.endpoints.push({mode, key: c.key, requested: bound, actual: actual.state[c.key]});
          }
          const before = (await snap()).state, number = root.locator('[data-ensemble-number=' + c.key + ']'); await number.fill('');
          assert.deepEqual((await snap()).state, before); await number.press('Tab');
          const after = (await snap()).state; assert.deepEqual(after, lab.normalize({...before, [c.key]: ''})); row.drafts.push({mode, key: c.key, unchangedWhileEmpty: true, committedState: after});
        }
        await speak(mode);
      }
      for (const preset of ['gap-kT', 'three-coins', 'four-coins', 'four-sites', 'large-count', 'free-expansion', 'blocks-equal']) {
        await root.locator('[data-ensemble-preset=' + preset + ']').click(); const r = await snap();
        if (preset === 'gap-kT') {near(r.bars[1].p, 1 / (1 + Math.E)); assert.match(r.readout, /ratio ≈ 0.3678794/); assert.match(r.readout, /upper probability ≈ 0.2689414/);}
        if (['three-coins', 'four-coins', 'four-sites'].includes(preset)) {assert.equal(r.enumeration.length, 2 ** r.state.N); r.rows.forEach(row => assert.equal(BigInt(row.values[1]), independentChoose(r.state.N, row.j)));}
        if (preset === 'three-coins') assert.match(r.readout, /ensemble entropy divided by k_B ≈ 2.079442/);
        if (preset === 'large-count') {assert.equal(BigInt(r.rows.find(r => r.j === 512).values[1]), independentChoose(1024, 512)); await speak('large-count');}
        row.states.push({preset, ...r}); await shot(preset);
      }
      await root.locator('[data-ensemble-mode]').selectOption('expansion'); await numeric('log10N', 25); const gas = await numeric('volumeRatio', 2);
      assert.match(gas.readout, /10000000000000000000000000/); assert.match(gas.readout, /positive; ln P/); assert.match(gas.readout, /temperature change = 0 kelvin/);
      row.states.push({preset: 'finite-gas-log-tail', ...gas}); await speak('finite-gas-log-tail'); await shot('large-gas-probability');
      const nochange = await numeric('volumeRatio', 1); assert.match(nochange.readout, /Entropy increase divided by k_B ≈ 0/); row.states.push({preset: 'unchanged-volume', ...nochange});
      await root.locator('[data-ensemble-mode]').selectOption('blocks');
      for (const [key, value] of [['tempA', 600], ['tempB', 300], ['capacityA', 100], ['capacityB', 300], ['transfer', 100]]) await numeric(key, value);
      const unequal = await snap(); assert.match(unequal.readout, /equilibrium temperature ≈ 375 kelvin/); assert.match(unequal.readout, /Heat into A ≈ -22500 joules/); row.states.push({preset: 'unequal-capacity-blocks', ...unequal});
      const tiny = await numeric('tempA', 300.00000001); assert.ok(!tiny.readout.includes('combined entropy change ≈ 0 joules')); row.states.push({preset: 'tiny-positive-block-entropy', ...tiny}); await speak('tiny-block-entropy');
      await root.locator('[data-ensemble-action=enlarge]').click();
      const enlarged = await root.locator('.ensemble-viewport').evaluate(e => ({width: e.clientWidth, scroll: e.scrollWidth, svg: e.querySelector('svg').getBoundingClientRect().width}));
      assert.ok(enlarged.svg >= 740); if (width === 390) assert.ok(enlarged.scroll > enlarged.width); row.enlarged = enlarged;
      await root.locator('[data-ensemble-action=enlarge]').click(); await root.locator('[data-ensemble-action=reset]').click(); assert.deepEqual((await snap()).state, lab.initial); row.resetExact = true;
    }
    proof.assets = {};
    for (const file of ['physics-ensemble-lab.js', 'physics-ensemble-lab.css']) {const r = await context.request.get(origin + '/app/' + file); assert.equal(r.status(), 200);
      const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex'); const served = hash(await r.body()), local = hash(fs.readFileSync(path.join(__dirname, '..', 'web', file))); assert.equal(served, local); proof.assets[file] = {served, local};}
    assert.deepEqual(proof.errors, []); assert.deepEqual(proof.failures, []); proof.passed = true;
    console.log(JSON.stringify({passed: true, evidence, rows: proof.rows.map(r => ({width: r.width, states: r.states.length, endpoints: r.endpoints.length, drafts: r.drafts.length, speech: r.speech.length}))}));
  } catch (error) {proof.passed = false; proof.error = String(error.stack || error); if (reviewPage) {proof.failedRoute = reviewPage.url(); proof.failedVisibleText = (await reviewPage.locator('body').innerText()).slice(0, 5000); await reviewPage.screenshot({path: path.join(evidence, 'failed-route.png')}); console.log(JSON.stringify({failedRoute: proof.failedRoute, failedVisibleText: proof.failedVisibleText}));} throw error;}
  finally {fs.writeFileSync(path.join(evidence, 'ensemble-browser-proof.json'), JSON.stringify(proof, null, 2) + '\n'); await browser.close();}
}
if (process.argv.includes('--browser')) browserReview().catch(error => {console.error(error); process.exitCode = 1;});
