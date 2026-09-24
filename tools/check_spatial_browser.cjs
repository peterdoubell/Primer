#!/usr/bin/env node
'use strict';

// Optional end-to-end QA. Run against an isolated Primer database/dev server.
// NODE_PATH=/path/to/node_modules node tools/check_spatial_browser.cjs URL OUTDIR
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const base = process.argv[2] || 'http://127.0.0.1:8768';
const out = process.argv[3] || fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'primer-spatial-qa-'));
fs.mkdirSync(out, { recursive: true });
console.log('Screenshots: ' + out);
const curriculum = path.resolve(__dirname, '../data/curriculum');
const entries = fs.readdirSync(curriculum).filter(f => /^\d.*\.json$/.test(f))
  .flatMap(f => JSON.parse(fs.readFileSync(path.join(curriculum, f), 'utf8')).nodes)
  .flatMap(n => (n.lesson_media || []).filter(m => m.renderer === 'spatial-3d')
    .map(m => ({ id: n.id, title: m.title })));

(async () => {
  const browser = await chromium.launch({ headless: true });
  const results = [], errors = [];
  const sourceFiles = ['spatial-models.js', 'spatial-math.js', 'spatial-molecular.js',
    'spatial-physical.js', 'spatial-cross-subject.js', 'spatial-radiology.js', 'concept-models.js', 'lesson-models.js', 'app.js', 'styles.css'];
  const digest = bytes => createHash('sha256').update(bytes).digest('hex');
  const loadedSources = {}, sourceReads = [];
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce', hasTouch: true });
    const page = await context.newPage();
    const touch = await context.newCDPSession(page);
    page.on('pageerror', error => errors.push(error.message));
    page.on('response', response => {
      const file = new URL(response.url()).pathname.replace(/^\/app\//, '');
      if (sourceFiles.includes(file)) sourceReads.push(response.body().then(body => { loadedSources[file] = digest(body); }));
    });
    const galleryResponse = await context.request.get(base + '/api/curriculum/visuals');
    assert.equal(galleryResponse.status(), 200);
    const gallery = await galleryResponse.json();
    const galleryModels = gallery.items.filter(item => ['spatial-3d', 'radiology-anatomy'].includes(item.renderer));
    for (const entry of entries) assert.ok(galleryModels.some(item => item.lesson_id === entry.id && item.renderer === 'spatial-3d'),
      entry.id + ': authored spatial scene remains reachable through the gallery');
    await page.goto(base + '/#/math-images');
    await page.getByRole('combobox', { name: /^kind$/i }).selectOption('spatial-3d');
    await page.waitForFunction(count => document.querySelectorAll('.math-image-card:not([hidden])').length === count, galleryModels.length);
    const firstCard = page.locator('.math-image-card:not([hidden])').first();
    await firstCard.getByRole('button', { name: 'Open model →', exact: true }).click();
    await page.locator('.spatial-model').waitFor();
    assert.ok(page.url().includes('/node/'), 'Gallery must open a real lesson');

    for (const entry of entries) {
      await page.goto(base + '/#/node/' + entry.id);
      const model = page.locator('.spatial-model[data-scenario="' + entry.id + '"]');
      await model.waitFor();
      assert.equal(await model.getAttribute('data-scenario'), entry.id);
      const svg = model.locator('.spatial-svg');
      const snapshot = () => model.evaluate(el => ({
        view: el.dataset.view,
        geometry: el.querySelector('svg g').innerHTML,
        readout: el.querySelector('.spatial-readout').textContent,
        state: [...el.querySelectorAll('[data-parameter]')].map(e => [e.dataset.parameter, e.value]),
      }));
      const visualBounds = () => model.evaluate(el => {
        const boxes = [...el.querySelectorAll('svg polygon, svg polyline, svg circle')].map(e => e.getBBox());
        const labels = [...el.querySelectorAll('svg text')].map(e => {
          const { x, y, width, height } = e.getBBox();
          return { text: e.textContent, x, y, width, height };
        });
        return { left: Math.min(...boxes.map(b => b.x)), top: Math.min(...boxes.map(b => b.y)),
          right: Math.max(...boxes.map(b => b.x + b.width)), bottom: Math.max(...boxes.map(b => b.y + b.height)), labels };
      });
      const checkVisible = async state => {
        const bounds = await visualBounds();
        assert.ok(bounds.left >= 0 && bounds.top >= 0 && bounds.right <= 600 && bounds.bottom <= 420,
          entry.id + ': geometry must stay in frame at ' + state);
        for (const [i, label] of bounds.labels.entries()) {
          assert.ok(label.x >= 0 && label.y >= 0 && label.x + label.width <= 600 && label.y + label.height <= 420,
            entry.id + ': label must stay in frame: ' + label.text);
          for (const other of bounds.labels.slice(i + 1)) {
            const overlap = label.x < other.x + other.width && label.x + label.width > other.x &&
              label.y < other.y + other.height && label.y + label.height > other.y;
            assert.ok(!overlap, entry.id + ': overlapping labels at ' + state + ': ' + label.text + ' / ' + other.text);
          }
        }
        return { state, bounds };
      };
      const initial = await snapshot();
      const checks = [await checkVisible('initial')];
      await model.locator('.spatial-canvas').screenshot({ path: path.join(out, entry.id + '-desktop.png') });
      const controls = await model.locator('[data-parameter]').evaluateAll(inputs => inputs.map(e => ({
        key: e.dataset.parameter, options: e.tagName === 'SELECT' ? [...e.options].map(o => o.value) : [e.min, e.max],
      })));
      let interactions = 0;
      for (const control of controls) {
        const input = model.locator('[data-parameter="' + control.key + '"]');
        for (const value of control.options) {
          await input.evaluate((e, value) => {
            e.value = value;
            e.dispatchEvent(new Event(e.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true }));
          }, value);
          const changed = await snapshot();
          assert.ok(!/NaN|Infinity/.test(changed.geometry), entry.id + ': finite SVG');
          assert.ok(changed.readout.trim());
          checks.push(await checkVisible(control.key + '=' + value));
          interactions++;
          await model.getByRole('button', { name: 'Reset model', exact: true }).click();
          assert.deepEqual(await snapshot(), initial, entry.id + ': full model reset');
        }
      }
      // Also combine extrema: maximum layers plus separation, maximum stretch
      // plus a different surface, and changed shape plus lone-pair visibility.
      for (const side of [0, -1]) {
        await model.locator('[data-parameter]').evaluateAll((inputs, side) => inputs.forEach(e => {
          e.value = e.tagName === 'SELECT' ? [...e.options].at(side).value : side === 0 ? e.min : e.max;
          e.dispatchEvent(new Event(e.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true }));
        }), side);
        checks.push(await checkVisible('combined ' + side));
        for (const button of ['Tilt up', 'Rotate right', 'Rotate right', 'Tilt down']) {
          await model.getByRole('button', { name: button, exact: true }).click();
          checks.push(await checkVisible('combined ' + side + ' ' + button));
        }
        await model.getByRole('button', { name: 'Reset model', exact: true }).click();
      }
      await model.getByRole('button', { name: 'Rotate right', exact: true }).click();
      assert.notEqual((await snapshot()).geometry, initial.geometry, entry.id + ': rotation changes projection');
      await svg.focus();
      await page.keyboard.press('ArrowUp');
      await page.keyboard.press('+');
      assert.notEqual((await snapshot()).view, initial.view);
      await page.keyboard.press('Home');
      assert.deepEqual(await snapshot(), initial, entry.id + ': keyboard reset');
      await svg.scrollIntoViewIfNeeded();
      const box = await svg.boundingBox();
      await page.mouse.move(box.x + box.width * .5, box.y + box.height * .5);
      await page.mouse.down();
      await page.mouse.move(box.x + box.width * .6, box.y + box.height * .6, { steps: 6 });
      await page.mouse.up();
      assert.notEqual((await snapshot()).view, initial.view, entry.id + ': real pointer drag');
      await model.getByRole('button', { name: 'Reset view', exact: true }).click();
      assert.deepEqual(await snapshot(), initial);
      await page.setViewportSize({ width: 390, height: 844 });
      await model.locator('.spatial-canvas').screenshot({ path: path.join(out, entry.id + '-mobile.png') });
      checks.push(await checkVisible('mobile'));
      await svg.scrollIntoViewIfNeeded();
      const mobileBox = await svg.boundingBox();
      const touchPoint = { x: mobileBox.x + mobileBox.width * .45, y: mobileBox.y + mobileBox.height * .45 };
      await touch.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [touchPoint] });
      await touch.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: touchPoint.x + 50, y: touchPoint.y + 40 }] });
      await touch.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
      const dragged = await snapshot();
      assert.notEqual(dragged.view, initial.view, entry.id + ': touch rotation');
      assert.notEqual(dragged.view.split(',')[1], initial.view.split(',')[1], entry.id + ': vertical touch must tilt rather than cancel into page scroll');
      await model.getByRole('button', { name: 'Reset view', exact: true }).click();
      const dimensions = await model.evaluate(el => ({
        page: document.documentElement.scrollWidth, viewport: innerWidth,
        model: el.scrollWidth, width: el.clientWidth,
        text: [...el.querySelectorAll('svg text')].map(e => {
          const { x, y, width, height } = e.getBBox();
          return { text: e.textContent, box: { x, y, width, height } };
        }),
      }));
      assert.ok(dimensions.page <= dimensions.viewport + 1, entry.id + ': no page overflow');
      assert.ok(dimensions.model <= dimensions.width + 1, entry.id + ': no model overflow');
      await model.getByRole('button', { name: 'Rotate left', exact: true }).click();
      assert.notEqual((await snapshot()).view, initial.view, entry.id + ': mobile rotation control');
      await model.getByRole('button', { name: 'Reset model', exact: true }).click();
      results.push({ id: entry.id, interactions, dimensions, checks });
      console.log('BROWSER ' + entry.id + ': ' + interactions + ' parameter states; drag, keyboard, reset, mobile');
      await page.setViewportSize({ width: 1440, height: 1000 });
    }
    assert.deepEqual(errors, [], 'No browser JavaScript errors');
    await Promise.all(sourceReads);
    for (const file of sourceFiles) assert.equal(loadedSources[file],
      digest(fs.readFileSync(path.resolve(__dirname, '../web', file))),
      'Browser must have tested current ' + file + ', not a stale or concurrently edited version');
    fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({ results, errors, loadedSources }, null, 2));
    console.log('PASS ' + entries.length + ' scenes; screenshots in ' + out);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
