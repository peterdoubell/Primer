#!/usr/bin/env node
'use strict';
// Run against an isolated Primer server. Playwright may be supplied by NODE_PATH.
// Evidence uses a fresh private temporary directory; printed as EVIDENCE_DIRECTORY.
// Legacy output-directory argument (slot 3) is ignored; see docs/browser-qa.md.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const { createEvidenceDirectory, loopbackQaUrl } = require('./qa-browser.cjs');
const base = loopbackQaUrl(process.argv[2] || 'http://127.0.0.1:8768');
const out = createEvidenceDirectory();

const registeredIds = ['arts.1.beat', 'lang.2.etymology', 'lang.2.poetry', 'lang.2.novels', 'lang.2.research', 'lang.2.speaking', 'lang.2.grammar', 'lang.2.paragraphs', 'lang.0.phonics', 'lang.1.handwriting', 'lang.0.speaking', 'lang.1.childrens-lit', 'lang.1.writing-stories', 'lang.1.dictionary', 'lang.1.vocabulary', 'lang.1.spelling', 'lang.1.sentences', 'lang.0.rhymes', 'lang.0.stories', 'earth.5.frontier', 'earth.5.earth-systems', 'earth.5.cosmology', 'earth.5.astrobiology', 'earth.4.planetary', 'earth.4.climatology', 'earth.4.oceanatmos', 'earth.4.geophysics', 'earth.4.astrophysics', 'earth.3.astronomy', 'earth.3.ecology-earth', 'earth.3.climate-sci', 'earth.3.space-exploration', 'earth.2.geology', 'earth.2.oceans', 'earth.2.atmosphere', 'earth.2.environment', 'earth.2.planets', 'earth.2.stars', 'earth.0.weather', 'earth.1.solar-system', 'earth.0.land-water', 'earth.1.water-cycle', 'earth.1.rocks', 'cs.4.security', 'cs.4.systems', 'cs.5.deep-learning', 'cs.5.distributed', 'cs.5.pl-theory', 'cs.5.frontier', 'cs.4.algorithms-adv', 'cs.4.ml', 'cs.4.theory', 'cs.3.web', 'cs.2.internet', 'cs.4.os', 'cs.4.databases-adv', 'cs.3.versioncontrol', 'cs.3.oop', 'cs.3.hardware', 'cs.2.bigo-intro', 'cs.3.algorithms', 'cs.1.blocks', 'cs.2.programming', 'cs.1.parts', 'cs.3.databases', 'cs.2.data-types', 'cs.2.debugging', 'cs.2.functions', 'cs.0.sorting', 'cs.0.patterns', 'chem.3.bonding', 'chem.4.inorganic', 'chem.3.organic-intro', 'chem.2.reactions-intro', 'chem.3.reactions', 'chem.2.periodic', 'chem.2.acids', 'chem.0.materials', 'chem.1.materials-props', 'chem.5.materials', 'chem.1.changes', 'chem.4.electrochem', 'chem.5.biochem', 'chem.5.frontier', 'chem.4.analytical', 'chem.5.compchem', 'chem.2.mixtures', 'chem.3.atomic-structure', 'chem.3.gases', 'chem.3.energy', 'chem.4.physical', 'chem.3.stoichiometry', 'chem.0.mixing', 'chem.0.water-states', 'chem.1.matter', 'bio.1.health', 'bio.3.microbiology', 'bio.5.immunology', 'bio.5.frontier', 'bio.4.neuro', 'bio.4.physiology', 'bio.4.ethology', 'bio.4.genomics', 'bio.5.comp-bio', 'bio.5.systems-bio', 'bio.3.ecology', 'bio.3.botany', 'bio.4.biochem', 'bio.3.evolution', 'bio.4.evo-bio', 'bio.1.human-body', 'bio.2.digestion', 'bio.2.reproduction', 'bio.0.animals', 'bio.1.habitats', 'bio.0.body', 'bio.0.seasons', 'bio.0.living', 'bio.2.classification', 'bio.2.ecosystems', 'bio.2.microbes', 'bio.0.plants', 'bio.1.plants-parts', 'bio.2.photosynthesis', 'bio.1.food-chains', 'math.5.diffgeo', 'math.5.complex-analysis', 'math.5.logic', 'math.5.frontier', 'math.5.abstract', 'math.5.measure', 'math.5.functional', 'math.5.numerical', 'math.4.diffeq', 'math.4.discrete', 'math.4.numtheory', 'math.4.analysis', 'math.4.prob-theory', 'math.3.euclid', 'math.4.complex', 'math.4.diff-calc', 'math.4.int-calc', 'math.3.probability', 'math.3.statistics', 'math.3.precalc', 'math.3.polynomials', 'math.3.trig', 'math.3.expo-logs', 'math.3.sequences', 'math.3.systems', 'math.3.quadratics', 'math.3.linear', 'math.3.slope', 'math.2.primes', 'math.2.ratio', 'math.2.exponents', 'math.2.data', 'math.2.prealgebra', 'math.2.decimals', 'math.2.order-ops', 'math.2.percent', 'math.2.coordinates', 'math.1.measurement', 'math.1.time', 'math.1.fractions-intro', 'math.1.multiplication', 'math.1.division', 'math.1.subtraction', 'math.1.place-value', 'math.0.compare', 'math.0.patterns', 'math.0.numbers20', 'cs.1.binary', 'hist.3.economics-intro', 'lang.4.linguistics', 'mind.5.logic-advanced'];
const requestedIds = process.argv[4] ? process.argv[4].split(',') : registeredIds;
assert.ok(requestedIds.length && new Set(requestedIds).size === requestedIds.length && requestedIds.every(id => registeredIds.includes(id)), 'Only registered, unique scenarios may be selected');
// Derive filenames from the trusted registry, never from CLI text.
const ids = registeredIds.filter(id => requestedIds.includes(id));
const sourceFiles = ['concept-models.js', 'lesson-models.js', 'app.js', 'styles.css'];
const digest = data => createHash('sha256').update(data).digest('hex');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const errors = [], results = [], loadedSources = {}, reads = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce', hasTouch: true });
    page.on('pageerror', error => errors.push(error.message));
    page.on('response', response => {
      const file = new URL(response.url()).pathname.replace(/^\/app\//, '');
      if (sourceFiles.includes(file)) reads.push(response.body().then(body => { loadedSources[file] = digest(body); }));
    });
    for (const id of ids) {
      await page.goto(base + '/#/node/' + id);
      const model = page.locator('.concept-model');
      await model.waitFor();
      assert.equal(await model.getAttribute('data-scenario'), id);
      const reset = model.getByRole('button', { name: 'Reset model', exact: true });
      const snapshot = () => model.evaluate(el => ({
        svg: el.querySelector('svg').innerHTML,
        readout: el.querySelector('.model-readout').textContent,
        detail: el.querySelector('.concept-detail').textContent,
        state: [...el.querySelectorAll('[data-parameter]')].map(e =>
          [e.dataset.parameter, e.tagName === 'BUTTON' ? e.getAttribute('aria-pressed') : e.value]),
      }));
      const initial = await snapshot();
      if (id === 'cs.3.web') {
        const preview = model.locator('[data-action="web-preview"]');
        const counter = model.locator('[data-web-counter]');
        await preview.click();
        assert.equal(await counter.textContent(), 'Preview counter: 1');
        assert.ok(await preview.evaluate(el => document.activeElement === el), 'Preview retains focus after refresh');
        await page.keyboard.press('Space');
        assert.equal(await counter.textContent(), 'Preview counter: 2');
        await model.locator('[data-parameter="enabled"]').click();
        await preview.click();
        assert.equal(await counter.textContent(), 'Preview counter: 2');
        await reset.click();
        assert.deepEqual(await snapshot(), initial, 'Preview resets exactly');
      }
      const capture = async suffix => {
        const canvas = model.locator('.concept-canvas');
        // Centre the drawing below the sticky navigation after controls scroll it.
        await canvas.evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }));
        // Let scrolling reach the compositor before capturing. Element screenshots
        // can perform another implicit scroll and clip a nested SVG inconsistently;
        // retain the whole viewport as evidence instead of an auto-scrolled crop.
        await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        await visible('capture ' + suffix);
        await page.screenshot({ path: path.join(out, id + '-' + suffix + '.png'), animations: 'disabled' });
      };
      const controls = await model.locator('[data-parameter]').evaluateAll(inputs => inputs.map(e => ({
        key: e.dataset.parameter, tag: e.tagName,
        values: e.tagName === 'BUTTON' ? [false, true] : e.tagName === 'SELECT' ? [...e.options].map(o => o.value) : [e.min, e.max],
      })));
      const visible = async label => {
        const state = await model.evaluate(el => {
          const svg = el.querySelector('svg'), vb = svg.viewBox.baseVal;
          const canvas = el.querySelector('.concept-canvas').getBoundingClientRect();
          return { page: document.documentElement.scrollWidth, viewport: innerWidth,
            model: el.scrollWidth, width: el.clientWidth, view: { width: vb.width, height: vb.height },
            labels: [...svg.querySelectorAll('text')].map(e => {
              const { x, y, width, height } = e.getBBox();
              const screen = e.getBoundingClientRect();
              return { text: e.textContent, x, y, width, height,
                contained: screen.left >= canvas.left && screen.top >= canvas.top &&
                  screen.right <= canvas.right && screen.bottom <= canvas.bottom };
            }) };
        });
        assert.ok(state.page <= state.viewport + 1 && state.model <= state.width + 1, id + ': overflow at ' + label);
        state.labels.forEach((a, i) => {
          assert.ok(a.contained, id + ': rendered label outside canvas at ' + label + ': ' + a.text);
          assert.ok(a.x >= 0 && a.y >= 0 && a.x + a.width <= state.view.width && a.y + a.height <= state.view.height,
            id + ': clipped label ' + a.text);
          state.labels.slice(i + 1).forEach(b => assert.ok(!(a.x < b.x + b.width && a.x + a.width > b.x &&
            a.y < b.y + b.height && a.y + a.height > b.y), id + ': labels overlap ' + a.text + ' / ' + b.text));
        });
      };
      await visible('desktop');
      await capture('desktop');
      let states = 0;
      for (const control of controls) {
        const input = model.locator('[data-parameter="' + control.key + '"]');
        let meaningful = false;
        for (const value of control.values) {
          await input.evaluate((e, value) => {
            if (e.tagName === 'BUTTON') {
              if ((e.getAttribute('aria-pressed') === 'true') !== value) e.click();
            } else {
              e.value = value;
              e.dispatchEvent(new Event(e.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true }));
            }
          }, value);
          const changed = await snapshot();
          meaningful ||= changed.readout !== initial.readout || changed.detail !== initial.detail;
          assert.ok(!/NaN|Infinity/.test(changed.svg));
          await visible(control.key + '=' + value);
          states++;
          await reset.click();
          assert.deepEqual(await snapshot(), initial, id + ': exact reset');
        }
        assert.ok(meaningful, id + ': meaningful ' + control.key);
        await input.focus();
        const rangeKey = control.tag === 'INPUT' ? await input.evaluate(e => Number(e.value) >= Number(e.max) ? 'ArrowLeft' : 'ArrowRight') : null;
        if (control.tag === 'SELECT') {
          // Choose a genuinely different option, including when the default is
          // not first or several labels share their first letter (Sand/Salt).
          const alternative = await input.evaluate(e => {
            const option = [...e.options].find(o => !o.disabled && o.value !== e.value);
            return option && { value: option.value, label: option.textContent.trim() };
          });
          assert.ok(alternative, id + ': alternative keyboard selection');
          await page.keyboard.type(alternative.label);
          // Native type-ahead commits on blur on macOS.
          await page.keyboard.press('Tab');
          assert.equal(await input.inputValue(), alternative.value, id + ': exact keyboard selection');
        } else await page.keyboard.press(control.tag === 'BUTTON' ? 'Space' : rangeKey);
        assert.notDeepEqual((await snapshot()).state, initial.state, id + ': keyboard ' + control.key);
        await reset.click();
        if (control.tag === 'BUTTON') {
          await input.click();
          assert.notDeepEqual((await snapshot()).state, initial.state, id + ': pointer ' + control.key);
          await reset.click();
        }
      }
      await page.setViewportSize({ width: 390, height: 844 });
      await visible('mobile');
      await capture('mobile');
      for (const control of controls.filter(control => control.tag === 'BUTTON')) {
        await model.locator('[data-parameter="' + control.key + '"]').click();
        assert.notDeepEqual((await snapshot()).state, initial.state, id + ': mobile pointer ' + control.key);
        await reset.click();
        assert.deepEqual(await snapshot(), initial, id + ': mobile exact reset');
      }
      const evidenceExamples = {
        'lang.2.poetry': [{ foot: 'anapest', feet: 4 }, { foot: 'trochee', feet: 1 }],
        'lang.2.novels': [{ chapter: 2, perspective: 'mina' }, { chapter: 3, perspective: 'mina' }],
        'lang.2.research': [{ third: 'copy', question: 'opening', inspect: 'C' }, { third: 'independent', question: 'cost', inspect: 'C' }],
        'lang.2.speaking': [{ audience: 'new', explanation: false, signposts: false }, { audience: 'familiar', explanation: true, signposts: true }],
        'lang.2.grammar': [{ subject: 'foxes', verb: 'jumps', focus: 'pp' }, { subject: 'foxes', verb: 'jump', focus: 'predicate' }],
        'lang.2.paragraphs': [{ evidence: 'badges', explanation: true, order: 'detail-first' }, { evidence: 'schedule', explanation: false, order: 'claim-first' }],
        'lang.0.phonics': [{ word: 'sat', step: 3 }, { word: 'mat', step: 2 }],
        'lang.1.handwriting': [{ letter: 't', step: 2, guides: true }, { letter: 'i', step: 0, guides: false }],
        'lang.0.speaking': [{ question: 'place', reply: 'train' }, { question: 'toy', reply: 'clarify' }],
        'lang.1.childrens-lit': [{ detail: 'declines', claim: 'reward' }, { detail: 'asks', claim: 'always' }],
        'lang.1.writing-stories': [{ action: 'wait', ending: 'open', part: 3 }, { action: 'wait', ending: 'resolved', part: 3 }],
        'lang.1.dictionary': [{ first: 'cat', second: 'catch', reveal: 4 }, { first: 'cattle', second: 'cattle', reveal: 7 }],
        'lang.1.vocabulary': [{ word: 'trudged', scene: 'mud' }, { word: 'strolled', scene: 'unknown' }],
        'lang.1.spelling': [{ word: 'fish', sound: 3 }, { word: 'this', sound: 1 }],
        'lang.1.sentences': [{ subject: 'kitten', action: 'jumps', verb: false, capital: true, stop: true }, { subject: 'dog', action: 'runs', verb: true, capital: true, stop: true }],
        'lang.0.rhymes': [{ first: 'blue', second: 'shoe' }, { first: 'cat', second: 'cup' }],
        'lang.0.stories': [{ story: 'hat', event: 3, clue: 'what' }, { story: 'key', event: 2, clue: 'where' }],
        'earth.5.frontier': [{ amplitude: .2, phase: 90, polarization: 'cross', angle: 0 }, { amplitude: .2, phase: 90, polarization: 'cross', angle: 45 }],
        'earth.5.earth-systems': [{ initialTemperature: 230, forcing: 0, year: 40, feedback: true }, { initialTemperature: 310, forcing: 0, year: 40, feedback: true }],
        'earth.5.cosmology': [{ matter: 100, scale: .25 }, { matter: 10, scale: 2 }],
        'earth.5.astrobiology': [{ prior: 1, sensitivity: 90, specificity: 90 }, { prior: 1, sensitivity: 50, specificity: 100 }],
        'earth.4.planetary': [{ mass: '0.1', radius: 3, temperature: 1000, molecule: '2' }, { mass: '5', radius: .5, temperature: 100, molecule: '44' }],
        'earth.4.climatology': [{ rate: 50, zero: 50, response: '0.6', year: 60 }, { rate: 10, zero: 10, response: '0.3', year: 0 }],
        'earth.4.oceanatmos': [{ latitude: 0, pressure: 4 }, { latitude: -15, pressure: 4 }, { latitude: 15, pressure: 4 }],
        'earth.4.geophysics': [{ distance: 500, speed: 4, ratio: '0.5', liquid: false }, { distance: 500, speed: 4, ratio: '0.7', liquid: true }],
        'earth.4.astrophysics': [{ temperature: 3000, redshift: 2 }, { temperature: 12000, redshift: 0 }],
        'earth.3.astronomy': [{ temperature: 3000, radius: '100' }, { temperature: 30000, radius: '0.01' }],
        'earth.3.ecology-earth': [{ seasonal: false, capacity: 150, demand: 100, month: 7 }, { seasonal: true, capacity: 300, demand: 50, month: 9 }],
        'earth.3.climate-sci': [{ albedo: 80, infrared: 0, solar: 1000 }, { albedo: 0, infrared: 100, solar: 1600 }],
        'earth.3.space-exploration': [{ dry: 1, propellant: 30, exhaust: 5, burn: 100 }, { dry: 10, propellant: 0, exhaust: 5, burn: 100 }],
        'earth.2.geology': [{ boundary: 'convergent', steps: 6 }, { boundary: 'transform', steps: 6 }, { boundary: 'divergent', steps: 0 }],
        'earth.2.oceans': [{ moon: 90, observer: 90 }, { moon: 180, observer: 180 }, { moon: 45, observer: 345 }],
        'earth.2.atmosphere': [{ shift: 4, departure: -8, year: 30 }, { shift: 4, departure: 8, year: 1 }],
        'earth.2.environment': [{ prevention: 100, cleanup: 0, steps: 8 }, { prevention: 100, cleanup: 8, steps: 8 }, { prevention: 0, cleanup: 0, steps: 8 }],
        'earth.2.planets': [{ first: '4', second: '0' }, { first: '2', second: '2' }],
        'earth.2.stars': [{ luminosity: 1, distance: 8 }, { luminosity: 8, distance: 1 }],
        'earth.0.weather': [{ day: '2', metric: 'temperature' }, { day: '2', metric: 'snow' }, { day: '3', metric: 'wind' }],
        'earth.1.solar-system': [{ planet: '0', scale: 'distance' }, { planet: '7', scale: 'distance' }],
        'earth.0.land-water': [{ start: 4, basin: true, steps: 6 }, { start: 3, basin: false, steps: 1 }, { start: 4, basin: false, steps: 6 }],
        'earth.1.water-cycle': [{ amount: 7, infiltration: 25, stage: 4 }, { amount: 8, infiltration: 100, stage: 5 }, { amount: 8, infiltration: 100, stage: 6 }],
        'earth.1.rocks': [{ material: 'sediment', process: 'consolidate' }, { material: 'igneous', process: 'metamorphism' }, { material: 'magma', process: 'cool' }, { material: 'magma', process: 'weathering' }],
        'cs.4.security': [{ first: 15, second: 0, key: 15 }, { first: 9, second: 9, key: 0 }],
        'cs.4.systems': [{ index: 4, alive: true, action: 'read', value: 99 }, { index: 1, alive: false, action: 'write', value: 99 }, { index: -1, alive: true, action: 'write', value: 99 }],
        'cs.5.deep-learning': [{ query: 3, third: 10, causal: true }, { query: 0, third: 0, causal: false }],
        'cs.5.distributed': [{ first: 3, second: 28 }, { first: 7, second: 28 }, { first: 0, second: 31 }],
        'cs.5.pl-theory': [{ argument: 'true', offset: -2, stage: 2 }, { argument: '0', offset: -2, stage: 2 }],
        'cs.5.frontier': [{ limit: 5, bound: 5, repaired: false }, { limit: 5, bound: 6, repaired: false }, { limit: 0, bound: 6, repaired: true }],
        'cs.4.algorithms-adv': [{ ab: 1, ac: 9, bc: 1, steps: 4 }, { ab: 1, ac: 9, bc: 1, steps: 2 }, { ab: 9, ac: 9, bc: 9, steps: 0 }],
        'cs.4.ml': [{ rate: .24, steps: 8, shift: 4 }, { rate: .1, steps: 8, shift: 4 }, { rate: .02, steps: 0, shift: 0 }],
        'cs.4.theory': [{ word: '', steps: 5 }, { word: '010', steps: 2 }, { word: '010', steps: 3 }, { word: '00101', steps: 5 }],
        'cs.3.web': [{ count: 9, theme: 'blue', enabled: false }, { count: 0, theme: 'plain', enabled: true }],
        'cs.2.internet': [{ site: 'atlas', cached: false, stage: 4 }, { site: 'book', cached: true, stage: 4 }],
        'cs.4.os': [{ policy: 'rr', quantum: 1 }, { policy: 'fcfs', quantum: 4 }],
        'cs.4.databases-adv': [{ amount: 8, failure: true, atomic: false }, { amount: 8, failure: true, atomic: true }, { amount: 0, failure: true, atomic: false }],
        'cs.3.versioncontrol': [{ leftLine: 2, rightLine: 2, same: false, resolution: 'none' }, { leftLine: 2, rightLine: 2, same: false, resolution: 'right' }, { leftLine: 3, rightLine: 3, same: true, resolution: 'none' }],
        'cs.3.oop': [{ first: 0, second: 5, boosted: true }, { first: 5, second: 0, boosted: true }],
        'cs.3.hardware': [{ a: 1, b: 1, carry: 1 }, { a: 0, b: 0, carry: 0 }, { a: 1, b: 0, carry: 1 }],
        'cs.2.bigo-intro': [{ size: 32, target: 33 }, { size: 32, target: 1 }, { size: 4, target: 0 }],
        'cs.3.algorithms': [{ input: 'ties', stage: 4 }, { input: 'mixed', stage: 0 }, { input: 'reverse', stage: 2 }],
        'cs.1.blocks': [{ repeats: 0, star: 0, jump: 3 }, { repeats: 4, star: 2, jump: 3 }, { repeats: 4, star: 4, jump: 3 }],
        'cs.2.programming': [{ threshold: 5, iterations: 3 }, { threshold: 0, iterations: 0 }, { threshold: 9, iterations: 3 }],
        'cs.1.parts': [{ input: 0, operation: 'double', step: 0 }, { input: 0, operation: 'double', step: 3 }, { input: 9, operation: 'increment', step: 3 }],
        'chem.0.materials': [{ object: 'button', material: 'wood' }, { object: 'cup', material: 'steel' }],
        'chem.1.materials-props': [{ clear: true, flexible: true, rain: true }, { clear: false, flexible: false, rain: false }],
        'chem.5.materials': [{ temperature: 1200, barrier: 80, time: 400 }, { temperature: 500, barrier: 160, time: 20 }],
        'cs.3.databases': [{ minimum: 0, group: 'all', descending: false }, { minimum: 100, group: 'B', descending: true }],
        'cs.2.data-types': [{ left: 0, right: 3, leftType: 'text', rightType: 'text' }, { left: 9, right: 9, leftType: 'number', rightType: 'text' }],
        'cs.2.debugging': [{ n: 0, fixed: false }, { n: 6, fixed: true }],
        'cs.2.functions': [{ operation: 'square', first: -3, second: 6 }, { operation: 'add', first: -3, second: -3 }],
        'cs.0.sorting': [{ rule: 'color', count: 6 }, { rule: 'shape', count: 0 }],
        'cs.0.patterns': [{ unit: 'ABB', repeats: 4 }, { unit: 'ABC', repeats: 4 }],
        'chem.3.bonding': [{ material: 'salt', liquid: true, field: true }, { material: 'copper', liquid: false, field: true }, { material: 'iodine', liquid: true, field: true }],
        'chem.4.inorganic': [{ chelates: 3, oxidation: 3, mono: 'ammonia' }, { chelates: 0, oxidation: 2, mono: 'chloride' }],
        'chem.3.organic-intro': [{ carbons: 8, branched: true }, { carbons: 4, branched: true }],
        'chem.2.reactions-intro': [{ progress: 100, closed: false }, { progress: 100, closed: true }],
        'chem.3.reactions': [{ extent: 0 }, { extent: 4 }],
        'chem.2.periodic': [{ atomicNumber: 2 }, { atomicNumber: 18 }],
        'chem.2.acids': [{ ph: 14, reference: 0 }, { ph: 7, reference: 7 }],
        'chem.1.changes': [{ process: 'reaction', stage: 2 }, { process: 'melting', stage: 2 }],
        'chem.4.electrochem': [{ left: 0, right: -3, temperature: 333 }, { left: -2, right: -2, temperature: 298 }],
        'chem.5.biochem': [{ substrate: 10, inhibitor: 8, mechanism: 'noncompetitive' }, { substrate: 0, inhibitor: 0, mechanism: 'competitive' }],
        'chem.5.frontier': [{ economy: 100, yield: 100, solvent: 500, recovery: 0 }, { economy: 50, yield: 0, solvent: 500, recovery: 100 }],
        'chem.4.analytical': [{ concentration: 0, path: 1, blank: 1, correct: false }, { concentration: 10, path: 3, blank: 1, correct: true }],
        'chem.5.compchem': [{ alpha: 10, centre: 0 }, { alpha: 2, centre: 2 }],
        'chem.2.mixtures': [{ water: 100, solute: 20, sand: 10, filter: true }, { water: 500, solute: 20, sand: 0, filter: true }],
        'chem.3.atomic-structure': [{ protons: 10, neutrons: 12, electrons: 12 }, { protons: 1, neutrons: 0, electrons: 0 }],
        'chem.3.gases': [{ volume: 5, temperature: 600, amount: 5 }, { volume: 30, temperature: 200, amount: 1 }],
        'chem.3.energy': [{ change: 60, barrier: 80, catalyst: true }, { change: -60, barrier: 20, catalyst: true }],
        'chem.4.physical': [{ initialB: 10, power: -2, progress: 0 }, { initialB: 0, power: 2, progress: 100 }],
        'chem.3.stoichiometry': [{ hydrogen: 2, oxygen: 1, water: 2 }, { hydrogen: 6, oxygen: 3, water: 6 }, { hydrogen: 6, oxygen: 6, water: 1 }],
        'chem.0.mixing': [{ material: 'salt', resting: true }, { material: 'oil', resting: true }, { material: 'sand', resting: true }],
        'chem.0.water-states': [{ stage: 1 }, { stage: 3 }, { stage: 4 }],
        'chem.1.matter': [{ phase: 'liquid', width: 300 }, { phase: 'gas', width: 140 }],
        'bio.1.health': [{ stage: 3, contact: false }, { stage: 4, contact: true }],
        'bio.3.microbiology': [{ percent: 0, generation: 6, drug: true }, { percent: 10, generation: 1, drug: true }],
        'bio.5.immunology': [{ a: 0, b: 0, kd: 10 }, { a: 20, b: 20, kd: 1 }],
        'bio.5.frontier': [{ input: 5, tolerance: 1, mechanism: 'linear', intervention: true }, { input: 3, tolerance: 0, mechanism: 'saturating', intervention: false }],
        'bio.4.neuro': [{ drive: 1, tau: 30, refractory: 10 }, { drive: 3, tau: 5, refractory: 0 }, { drive: 0, tau: 5, refractory: 0 }],
        'bio.4.physiology': [{ pressure: 100, p50: 10, cooperativity: 40 }, { pressure: 0, p50: 50, cooperativity: 10 }, { pressure: 50, p50: 50, cooperativity: 40 }],
        'bio.4.ethology': [{ travel: 20, depletion: 10, residence: 40 }, { travel: 1, depletion: 2, residence: 0 }],
        'bio.4.genomics': [{ depth: 1, alternate: 1, filter: true }, { depth: 8, alternate: 8, filter: false }, { depth: 8, alternate: 4, filter: true }],
        'bio.5.comp-bio': [{ sequence: 'AGCTAC', mismatch: 5, gap: 1 }, { sequence: 'AAAAAA', mismatch: 2, gap: 1 }, { sequence: 'ACGTAC', mismatch: 1, gap: 3 }],
        'bio.5.systems-bio': [{ production: 10, removal: 10, threshold: 1, feedback: true }, { production: 10, removal: 10, threshold: 10, feedback: false }, { production: 0, removal: 100, threshold: 1, feedback: true }],
        'bio.3.ecology': [{ initial: 100, capacity: 10, rate: 100 }, { initial: 0, capacity: 100, rate: 100 }, { initial: 50, capacity: 50, rate: 0 }],
        'bio.3.botany': [{ opening: 100, humidity: 0 }, { opening: 100, humidity: 100 }, { opening: 0, humidity: 0 }],
        'bio.4.biochem': [{ substrate: 100, km: 1, vmax: 100 }, { substrate: 0, km: 50, vmax: 10 }, { substrate: 50, km: 50, vmax: 100 }],
        'bio.3.evolution': [{ percent: 0, environment: 'a', generation: 12 }, { percent: 100, environment: 'b', generation: 12 }, { percent: 50, environment: 'equal', generation: 6 }, { percent: 1, environment: 'a', generation: 12 }],
        'bio.4.evo-bio': [{ percent: 50, inbreeding: 100 }, { percent: 0, inbreeding: 100 }, { percent: 100, inbreeding: 0 }, { percent: 30, inbreeding: 50 }],
        'bio.1.human-body': [{ step: 0, oxygen: true }, { step: 3, oxygen: true }, { step: 7, oxygen: false }],
        'bio.2.digestion': [{ material: 'co2', step: 3 }, { material: 'urea', step: 3 }, { material: 'residue', step: 3 }],
        'bio.2.reproduction': [{ haploid: 3, divisions: 3 }, { haploid: 1, divisions: 0 }],
        'bio.0.living': ['plant', 'seed', 'flame', 'robot', 'rock'].flatMap(specimen => [{ specimen, inside: false }, { specimen, inside: true }]),
        'bio.2.classification': [{ first: 'bat', second: 'mouse', flight: true }, { first: 'pigeon', second: 'lizard', flight: true }, { first: 'pigeon', second: 'pigeon', flight: true }, { first: 'salmon', second: 'bat', flight: false }],
        'bio.2.ecosystems': [{ removed: 'grass', target: 'foxes' }, { removed: 'rabbits', target: 'foxes' }, { removed: 'mice', target: 'owls' }],
        'bio.2.microbes': [{ sugar: 6, steps: 6, yeast: true }, { sugar: 6, steps: 6, yeast: false }, { sugar: 0, steps: 6, yeast: true }],
        'bio.0.plants': [{ step: 4, water: true, warmth: true, light: false }, { step: 4, water: false, warmth: true, light: true }, { step: 4, water: true, warmth: false, light: true }],
        'bio.1.plants-parts': [{ part: 'flower', flow: true }, { part: 'leaves', flow: false }],
        'bio.2.photosynthesis': [{ carbon: 18, water: 18, light: true }, { carbon: 18, water: 5, light: true }, { carbon: 0, water: 18, light: false }],
        'bio.1.food-chains': [{ energy: 100, percent: 5 }, { energy: 1000, percent: 20 }],
        'math.5.diffgeo': [{ angle: 15, radius: 4 }, { angle: 150, radius: 1 }],
        'math.5.complex-analysis': [{ radius: 2, a: 1, b: -1, clockwise: false }, { radius: 3, a: 2, b: -2, clockwise: true }, { radius: 2, a: 0, b: 0, clockwise: false }],
        'math.5.logic': [{ row1: 0, row2: 0, row3: 0, row4: 0, row5: 0, row6: 0 }, { row1: 63, row2: 63, row3: 63, row4: 63, row5: 63, row6: 63 }],
        'math.5.abstract': [{ n: 12, g: 5, steps: 12 }, { n: 12, g: 0, steps: 0 }],
        'math.5.measure': [{ stage: 5, varying: false }, { stage: 5, varying: true }],
        'math.5.functional': [{ terms: 12, perturb: 0 }, { terms: 12, perturb: 1 }],
        'math.5.numerical': [{ start: 0, iterations: 10 }, { start: -2, iterations: 10 }],
        'math.4.diffeq': [{ rate: 2, initial: 4, steps: 2 }, { rate: 2, initial: 4, steps: 16 }],
        'math.4.discrete': [{ e01: true, e02: false, e03: false, e12: false, e13: false, e23: true, step: 6 }, { e01: true, e02: false, e03: true, e12: true, e13: false, e23: true, step: 6 }, { e01: false, e02: false, e03: false, e12: false, e13: false, e23: false, step: 0 }],
        'math.4.numtheory': [{ a: 21, b: 34 }, { a: 40, b: 40 }],
        'math.4.analysis': [{ a: 3, epsilon: .25, delta: 1 }, { a: 0, epsilon: .25, delta: .5 }],
        'math.4.prob-theory': [{ n: 10, percent: 100, cutoff: 9 }, { n: 10, percent: 0, cutoff: 0 }, { n: 10, percent: 50, cutoff: 5 }],
        'math.3.euclid': [{ a: 1, b: 5, rearranged: false }, { a: 1, b: 5, rearranged: true }],
        'math.4.complex': [{ real: -3, imaginary: 3, turns: 3, scale: 2 }, { real: 0, imaginary: 0, turns: 4, scale: 2 }],
        'math.4.diff-calc': [{ mode: 'absolute', x: 0, closeness: 3, left: true }, { mode: 'absolute', x: 0, closeness: 3, left: false }, { mode: 'square', x: -2, closeness: 0, left: true }],
        'math.4.int-calc': [{ shift: 3, end: 6, count: 20, method: 'midpoint' }, { shift: 3, end: 1, count: 2, method: 'right' }],
        'math.3.probability': [{ target: 12, cumulative: true }, { target: 2, cumulative: false }],
        'math.3.statistics': [{ centre: 10, spread: 4, outlier: 12, sample: true }, { centre: 0, spread: 0, outlier: 0, sample: false }],
        'math.3.precalc': [{ mode: 'hole', a: 3, closeness: 3, point: 0 }, { mode: 'jump', a: 1, closeness: 3, point: 6 }],
        'math.3.polynomials': [{ r1: 1, r2: 1, r3: -2, negative: false, zoom: 4 }, { r1: 2, r2: 2, r3: 2, negative: true, zoom: 10 }],
      };
      if (evidenceExamples[id]) {
        for (const [index, values] of evidenceExamples[id].entries()) {
          await model.locator('[data-parameter]').evaluateAll((inputs, values) => inputs.forEach(e => {
            const value = values[e.dataset.parameter];
            if (e.tagName === 'BUTTON') { if ((e.getAttribute('aria-pressed') === 'true') !== value) e.click(); }
            else { e.value = value; e.dispatchEvent(new Event(e.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true })); }
          }), values);
          await visible('evidence example ' + index); await capture('example-' + index + '-mobile'); states++;
        }
        await reset.click();
      }
      if (id === 'cs.3.web') {
        const preview = model.locator('[data-action="web-preview"]');
        await preview.tap();
        assert.equal(await model.locator('[data-web-counter]').textContent(), 'Preview counter: 1');
        await preview.evaluate(el => el.parentElement.scrollIntoView({ block: 'center', behavior: 'instant' }));
        await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        await page.screenshot({ path: path.join(out, id + '-working-preview-mobile.png'), animations: 'disabled' });
        await reset.click();
      }
      if (id === 'math.3.trig') {
        for (let angle = 0; angle <= 360; angle += 15) {
          await model.locator('input').evaluate((e, angle) => { e.value = angle; e.dispatchEvent(new Event('input', { bubbles: true })); }, angle);
          await visible('angle ' + angle);
          if ([90, 225, 270].includes(angle)) await capture('angle-' + angle + '-mobile');
          states++;
        }
        await reset.click();
      } else if (id === 'math.3.expo-logs') {
        await model.locator('input').evaluateAll(inputs => inputs.forEach(e => {
          e.value = e.dataset.parameter === 'base' ? 5 : -3;
          e.dispatchEvent(new Event('input', { bubbles: true }));
        }));
        await visible('negative exponent reciprocal'); await capture('reciprocal-mobile'); states++;
        await reset.click();
      } else if (id === 'math.3.sequences') {
        await model.locator('select').selectOption('geometric');
        await model.locator('input').evaluateAll(inputs => inputs.forEach(e => {
          e.value = e.max; e.dispatchEvent(new Event('input', { bubbles: true }));
        }));
        await visible('largest geometric series'); await capture('geometric-mobile'); states++;
        await reset.click();
      }
      if (['math.3.systems', 'math.3.quadratics'].includes(id)) {
        const examples = id === 'math.3.systems'
          ? [{ m1: 1, b1: 0, m2: 1, b2: 2 }, { m1: 1, b1: 0, m2: 1, b2: 0 }, { m1: 2, b1: -3, m2: 1, b2: 3 }]
          : [{ h: 2, k: 0, a: 3, down: false }, { h: -2, k: 4, a: 1, down: false }, { h: 2, k: 4, a: 1, down: true }];
        for (const [index, example] of examples.entries()) {
          await model.locator('[data-parameter]').evaluateAll((inputs, values) => inputs.forEach(e => {
            if (e.tagName === 'BUTTON') {
              if ((e.getAttribute('aria-pressed') === 'true') !== values[e.dataset.parameter]) e.click();
            } else { e.value = values[e.dataset.parameter]; e.dispatchEvent(new Event('input', { bubbles: true })); }
          }), example);
          await visible('intersection case ' + index);
          await capture('case-' + index + '-mobile');
          states++;
        }
        await reset.click();
      }
      if (['math.3.linear', 'math.3.slope'].includes(id)) {
        const examples = id === 'math.3.linear'
          ? [{ a: 5, b: 6, c: -12, step: 0 }, { a: 5, b: 6, c: -12, step: 1 }, { a: 5, b: 6, c: -12, step: 2 }]
          : [{ rise: -4, run: 1, intercept: -3 }, { rise: 4, run: 1, intercept: 3 }, { rise: 0, run: 4, intercept: 0 }];
        for (const [index, example] of examples.entries()) {
          await model.locator('input[type="range"]').evaluateAll((inputs, values) => inputs.forEach(e => {
            e.value = values[e.dataset.parameter]; e.dispatchEvent(new Event('input', { bubbles: true }));
          }), example);
          await visible('algebra edge ' + index);
          await capture('edge-' + index + '-mobile');
          states++;
        }
        await reset.click();
      }
      if (['math.2.primes', 'math.2.ratio', 'math.2.exponents', 'math.2.data', 'math.2.prealgebra', 'math.2.decimals', 'math.1.subtraction', 'math.1.place-value', 'math.1.multiplication', 'math.1.division'].includes(id)) {
        await model.locator('input[type="range"]').evaluateAll(inputs => inputs.forEach(e => {
          e.value = e.max; e.dispatchEvent(new Event('input', { bubbles: true }));
        }));
        await visible('combined maximum mobile');
        await capture('maximum-mobile');
        states++;
        await reset.click();
      }
      if (id === 'math.1.division') {
        await model.locator('input[type="range"]').evaluateAll(inputs => inputs.forEach(e => {
          e.value = e.dataset.parameter === 'total' ? 36 : 1;
          e.dispatchEvent(new Event('input', { bubbles: true }));
        }));
        await visible('36 counters in one group mobile');
        await capture('one-group-mobile');
        states++;
        await reset.click();
      }
      if (id === 'math.2.order-ops') {
        await model.locator('[data-parameter="grouped"]').click();
        await visible('parenthesized tree mobile');
        await capture('grouped-mobile');
        states++;
        await reset.click();
      }
      if (id === 'math.0.patterns') {
        await model.locator('select').selectOption('grow');
        await model.locator('[data-parameter="steps"]').evaluate(e => {
          e.value = 6; e.dispatchEvent(new Event('input', { bubbles: true }));
        });
        await visible('six growing steps mobile');
        await capture('grow-mobile');
        states++;
      } else if (id === 'mind.5.logic-advanced') {
        for (let mask = 0; mask < 64; mask++) {
          await model.locator('[data-parameter]').evaluateAll((inputs, mask) => inputs.forEach((e, i) => {
            if ((e.getAttribute('aria-pressed') === 'true') !== Boolean(mask & (1 << i))) e.click();
          }), mask);
          await visible('modal configuration ' + mask);
          states++;
        }
      } else if (id === 'lang.4.linguistics') {
        await model.locator('select').selectOption('noun');
        await visible('noun attachment mobile');
        await capture('noun-mobile');
      }
      await reset.click();
      assert.deepEqual(await snapshot(), initial);
      results.push({ id, controls: controls.length, states });
      console.log('BROWSER ' + id + ': ' + states + ' states, keyboard/reset, desktop/mobile');
      await page.setViewportSize({ width: 1440, height: 1000 });
    }
    assert.deepEqual(errors, []);
    await Promise.all(reads);
    sourceFiles.forEach(file => assert.equal(loadedSources[file], digest(fs.readFileSync(path.resolve(__dirname, '../web', file))),
      'Browser must test current ' + file));
    fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({ captureMode: 'viewport-after-compositor-frames', results, errors, loadedSources }, null, 2));
    console.log('PASS ' + ids.length + ' concept models');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
