#!/usr/bin/env node
'use strict';
// Exercise the shipped renderer with its existing curriculum items in a fresh
// browser context. No database, credentials, learner records, or remote writes.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const evidence = path.join(root, 'docs/math-growth-series-fidelity-20261014/browser');
fs.mkdirSync(evidence, { recursive: true });
const ids = ['math.3.sequences', 'math.3.expo-logs'], items = {};
function find(value) {
  if (!value || typeof value !== 'object') return;
  if (ids.includes(value.id)) items[value.id] = value.lesson_media.find(x => x.kind === 'model' && x.props?.scenario === value.id);
  Object.values(value).forEach(child => { if (Array.isArray(child)) child.forEach(find); else find(child); });
}
find(JSON.parse(fs.readFileSync(path.join(root, 'data/curriculum/01-mathematics.json'))));
const examples = {
  'math.3.sequences': [
    { mode: 'arithmetic', first: -4, step: -4, count: 24 },
    { mode: 'arithmetic', first: 4, step: 0, count: 24 },
    { mode: 'geometric', first: 1, step: .5, count: 24 },
    { mode: 'geometric', first: -4, step: -.75, count: 24 },
    { mode: 'geometric', first: 4, step: -1, count: 24 },
    { mode: 'geometric', first: 0, step: -4, count: 24 },
    { mode: 'geometric', first: -4, step: -4, count: 24 },
    { mode: 'geometric', first: -4, step: 4, count: 24 },
    { mode: 'geometric', first: 4, step: 0, count: 1 },
    { mode: 'geometric', first: 1, step: .25, count: 24 },
  ],
  'math.3.expo-logs': [
    { base: .25, exponent: -3 }, { base: .5, exponent: .5 },
    { base: .75, exponent: -2.75 }, { base: 1, exponent: .25 },
    { base: 1.25, exponent: 3 }, { base: 2, exponent: -3 },
    { base: 5, exponent: 3 }, { base: 5, exponent: -3 },
  ],
};
(async () => {
  const browser = await chromium.launch({ headless: true }), results = [], errors = [];
  try {
    for (const width of [1440, 390]) {
      const page = await browser.newPage({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' });
      page.on('pageerror', e => errors.push(e.message));
      await page.setContent('<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body><main style="max-width:620px;margin:12px auto" id="model"></main></body></html>');
      await page.addStyleTag({ path: path.join(root, 'web/styles.css') });
      await page.addScriptTag({ path: path.join(root, 'web/concept-models.js') });
      for (const id of ids) {
        await page.evaluate(item => document.querySelector('#model').replaceChildren(window.PrimerConceptModels.render(item)), items[id]);
        const section = page.locator('.concept-model');
        const initial = await section.locator('.model-readout').textContent();
        for (const [index, state] of examples[id].entries()) {
          await section.locator('[data-parameter]').evaluateAll((inputs, s) => inputs.forEach(e => {
            e.value = String(s[e.dataset.parameter]);
            e.dispatchEvent(new Event(e.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true }));
          }), state);
          const proof = await section.evaluate(el => {
            const svg = el.querySelector('svg'), labels = [...svg.querySelectorAll('text')].map(e => {
              const b = e.getBBox(); return { text: e.textContent, x: b.x, y: b.y, width: b.width, height: b.height };
            });
            return { labels, width: el.clientWidth, scroll: el.scrollWidth, page: document.documentElement.scrollWidth,
              viewport: innerWidth, readout: el.querySelector('.model-readout').textContent,
              state: [...el.querySelectorAll('[data-parameter]')].map(e => [e.dataset.parameter, e.value]),
              invalid: [...svg.querySelectorAll('*')].flatMap(e => [...e.attributes].filter(a => /NaN|Infinity/.test(a.value)).map(a => a.value)) };
          });
          assert.equal(proof.invalid.length, 0); assert.ok(proof.page <= width + 1 && proof.scroll <= proof.width + 1, `${id} overflow`);
          for (const a of proof.labels) {
            assert.ok(a.x >= 0 && a.y >= 0 && a.x + a.width <= 420 && a.y + a.height <= 350, `${id} clipped label ${JSON.stringify(a)}`);
          }
          for (let i = 0; i < proof.labels.length; i++) for (let j = i + 1; j < proof.labels.length; j++) {
            const a = proof.labels[i], b = proof.labels[j];
            assert.ok(!(a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y), `${id}: labels overlap ${a.text} / ${b.text}`);
          }
          const expected = await page.evaluate(({ id, state }) => window.PrimerConceptModels.build(id, state).readout, { id, state });
          assert.equal(proof.readout, expected);
          if ([0, 2, 3, examples[id].length - 1].includes(index)) await section.screenshot({ path: path.join(evidence, `${id}-${width}-${index}.png`), animations: 'disabled' });
          results.push({ id, width, index, state, readout: proof.readout, labelCount: proof.labels.length });
        }
        await section.getByRole('button', { name: 'Reset model', exact: true }).click();
        assert.equal(await section.locator('.model-readout').textContent(), initial);
        const key = id === 'math.3.sequences' ? 'step' : 'base';
        const input = section.locator(`[data-parameter="${key}"]`);
        await input.focus(); const before = await input.inputValue(); await page.keyboard.press('ArrowRight');
        assert.equal(Number(await input.inputValue()), Number(before) + .25);
        assert.equal(await input.evaluate(el => document.activeElement === el), true);
        results.push({ id, width, keyboard: true, parameter: key, before, after: await input.inputValue() });
      }
      await page.close();
    }
    assert.deepEqual(errors, []);
    const hashes = Object.fromEntries(['web/concept-models.js', 'web/styles.css', 'data/curriculum/01-mathematics.json'].map(file => [file, createHash('sha256').update(fs.readFileSync(path.join(root, file))).digest('hex')]));
    fs.writeFileSync(path.join(evidence, 'proof.json'), JSON.stringify({ scope: 'Standalone shipped renderer with existing curriculum items; not authenticated reader or hosted delivery', hashes, errors, results }, null, 2) + '\n');
    console.log(`Verified ${results.length} browser states at 1440 and 390 pixels, label containment, calibrated controls, keyboard and resets.`);
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
