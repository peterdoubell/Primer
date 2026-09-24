#!/usr/bin/env node
'use strict';
// Real-browser coverage for every binding outside the concept/3D suites.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const base = process.argv[2];
const out = process.argv[3];
assert.ok(base && out, 'Provide isolated QA URL and evidence directory');
fs.mkdirSync(out, { recursive: true });
const entries = fs.readdirSync(path.join(root, 'data/curriculum')).filter(f => /^\d.*\.json$/.test(f))
  .flatMap(f => JSON.parse(fs.readFileSync(path.join(root, 'data/curriculum', f))).nodes)
  .flatMap(n => (n.lesson_media || []).filter(m => m.kind === 'model' &&
    !['concept-lab', 'spatial-3d'].includes(m.renderer)).map(m => ({ id: n.id, renderer: m.renderer })));
const digest = data => createHash('sha256').update(data).digest('hex');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const results = [], errors = [], sources = {}, reads = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
    page.on('pageerror', e => errors.push(e.message));
    page.on('response', response => {
      const file = new URL(response.url()).pathname.replace(/^\/app\//, '');
      if (['app.js', 'lesson-models.js', 'styles.css'].includes(file)) {
        reads.push(response.body().then(body => { sources[file] = digest(body); }));
      }
    });
    for (const entry of entries) {
      await page.goto(base + '/#/node/' + entry.id);
      const model = page.locator('.lesson-model[data-renderer="' + entry.renderer + '"]');
      await model.waitFor();
      const snapshot = () => model.evaluate(e => ({ canvas: e.querySelector('.model-canvas').innerHTML,
        readout: e.querySelector('.model-readout').textContent, text: e.innerText }));
      let changed = false, exercised = 0;
      const before = await snapshot();
      for (const input of await model.locator('input[type="range"]').all()) {
        const value = await input.inputValue();
        await input.focus();
        await page.keyboard.press(Number(value) >= Number(await input.getAttribute('max')) ? 'ArrowLeft' : 'ArrowRight');
        assert.notEqual(await input.inputValue(), value, entry.id + ' keyboard slider');
        exercised++;
      }
      for (const select of await model.locator('select').all()) {
        const options = await select.locator('option').evaluateAll(es => es.filter(e => !e.disabled).map(e => e.value));
        const value = await select.inputValue();
        const other = options.find(o => o !== value);
        if (other !== undefined) { await select.selectOption(other); exercised++; }
      }
      const buttons = model.locator('.model-controls button:not([disabled]):not([aria-pressed="true"])');
      for (const button of await buttons.all()) {
        const text = await button.innerText();
        if (/reset|read|speak|voice/i.test(text)) continue;
        await button.click();
        exercised++;
        break;
      }
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      changed = JSON.stringify(await snapshot()) !== JSON.stringify(before);
      assert.ok(exercised && changed, entry.id + ': controls must change the model');
      for (const [name, viewport] of [['desktop', { width: 1440, height: 1000 }], ['mobile', { width: 390, height: 844 }]]) {
        await page.setViewportSize(viewport);
        const canvas = model.locator('.model-canvas');
        await canvas.evaluate(e => e.scrollIntoView({ block: 'center', behavior: 'instant' }));
        const box = await canvas.boundingBox();
        assert.ok(box && box.width > 0 && box.height > 0, entry.id + ' visible canvas');
        assert.ok(box.x >= -1 && box.x + box.width <= viewport.width + 1, entry.id + ' ' + name + ' containment');
        for (const svg of await model.locator('svg.science-diagram, svg.physics-concept-svg').all()) {
          const fits = await svg.evaluate(e => e.getBoundingClientRect().width <= e.parentElement.clientWidth + 1);
          assert.ok(fits, entry.id + ': complete SVG must fit by default, not merely its outer card');
        }
        if (name === 'mobile') {
          const enlarge = model.getByRole('button', { name: 'Enlarge diagram', exact: true });
          if (await enlarge.count()) {
            await enlarge.first().click();
            const region = model.locator('.model-diagram-viewport').first();
            assert.ok(await region.evaluate(e => e.scrollWidth > e.clientWidth), entry.id + ': enlargement exposes fine detail');
            await region.focus();
            await page.keyboard.press('End');
            await region.evaluate(e => { e.scrollLeft = e.scrollWidth; });
            assert.ok(await region.evaluate(e => e.scrollLeft > 0), entry.id + ': enlarged content can be reached');
            await model.getByRole('button', { name: 'Fit whole diagram', exact: true }).first().click();
            assert.ok(await region.evaluate(e => e.scrollWidth <= e.clientWidth + 1), entry.id + ': fit restores complete view');
            await canvas.evaluate(e => e.scrollIntoView({ block: 'center', behavior: 'instant' }));
          }
        }
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), entry.id + ' page overflow');
        await page.screenshot({ path: path.join(out, entry.id + '-' + name + '.png') });
      }
      results.push({ ...entry, exercised, changed });
      console.log('BROWSER ' + entry.id + ': ' + exercised + ' controls; desktop/mobile');
      await page.setViewportSize({ width: 1440, height: 1000 });
    }
    await Promise.all(reads);
    assert.deepEqual(errors, []);
    for (const file of ['app.js', 'lesson-models.js', 'styles.css']) {
      assert.equal(sources[file], digest(fs.readFileSync(path.join(root, 'web', file))), 'Current source: ' + file);
    }
    fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({ results, errors, sources }, null, 2));
    console.log('PASS ' + entries.length + ' legacy model bindings');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
