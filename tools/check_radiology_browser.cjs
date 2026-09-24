#!/usr/bin/env node
'use strict';
// Run only against an isolated, onboarded QA server; never creates a reader.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const base = process.argv[2];
if (!base) throw new Error('Usage: URL');
const out = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'primer-radiology-qa-'));
console.log('Screenshots: ' + out);
const nodes = JSON.parse(fs.readFileSync(path.join(__dirname, '../data/curriculum/11-radiology.json'))).nodes;
(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    for (const n of nodes) {
      await page.goto(base + '/#/node/' + n.id);
      await page.locator('.lesson-illustration img').waitFor();
      await page.waitForFunction(() => {
        const image = document.querySelector('.lesson-illustration img');
        return image.complete && image.naturalWidth > 0;
      });
      assert.equal(await page.locator('.lesson-illustration img').count(), n.lesson_media.filter(m => m.kind === 'illustration').length, n.id);
      await page.waitForFunction(() => [...document.querySelectorAll('.lesson-illustration img')].every(i => i.complete && i.naturalWidth > 0));
      if (n.reference) assert.equal(await page.locator('.reference-card').count(), 1, n.id);
    }
    await page.goto(base + '/#/node/rad.5.ultrasound-physics');
    const model = page.locator('[data-renderer="doppler-angle-lab"]');
    await model.waitFor();
    await page.getByRole('button', { name: 'View diagrams and models', exact: true }).click();
    assert.equal(await page.locator('.lesson-media').evaluate(e => document.activeElement === e), true);
    const control = name => model.getByRole('slider', { name, exact: true });
    const set = async (name, value) => control(name).fill(String(value));
    const readout = () => model.locator('.model-readout').innerText();
    assert.match(await readout(), /60.0 cm\/s.*0.0% error/);
    const original = await readout();
    for (const angle of [0, 30, 45, 60, 75, 85]) {
      await set('Beam-to-flow angle', angle);
      await set('Assumed correction angle', angle);
      assert.match(await readout(), /60.0 cm\/s.*0.0% error/);
    }
    await set('Beam-to-flow angle', 60); await set('Assumed correction angle', 0);
    assert.match(await readout(), /30.0 cm\/s.*-50.0% error/);
    await set('Beam-to-flow angle', 90);
    assert.match(await readout(), /0 Hz.*velocity cannot be recovered/);
    assert.ok(!/NaN|Infinity/.test(await readout()));
    await model.getByRole('button', { name: 'Reset', exact: true }).click();
    assert.equal(await readout(), original);
    for (const name of ['Beam-to-flow angle', 'Assumed correction angle', 'True flow speed']) {
      const slider = control(name), before = await slider.inputValue();
      await slider.focus(); await page.keyboard.press('ArrowRight');
      assert.notEqual(await slider.inputValue(), before);
      await model.getByRole('button', { name: 'Reset', exact: true }).click();
    }
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      if (width === 390) {
        await page.getByRole('button', { name: 'View diagrams and models', exact: true }).click();
        const top = await page.locator('.lesson-media').boundingBox();
        const header = await page.locator('#sidebar').boundingBox();
        assert.ok(top.y >= header.y + header.height - 1, 'Jump clears the sticky mobile header');
      }
      await model.scrollIntoViewIfNeeded();
      const box = await model.boundingBox();
      assert.ok(box.x >= 0 && box.x + box.width <= width + 1, JSON.stringify({ width, box }));
      const geometry = await model.locator('.radiology-angle-svg').evaluate(e => ({ width: e.getBoundingClientRect().width, parent: e.parentElement.clientWidth }));
      assert.ok(geometry.width <= geometry.parent + 1);
      // Isolated card capture; separate assertion above checks real sticky-header clearance.
      await model.screenshot({ path: path.join(out, 'doppler-' + width + '.png'), style: '#sidebar { visibility:hidden; }' });
    }
    const theme = page.locator('#theme-toggle');
    const beforeTheme = await theme.getAttribute('aria-label');
    await theme.click();
    assert.notEqual(await theme.getAttribute('aria-label'), beforeTheme);
    await model.screenshot({ path: path.join(out, 'doppler-alternate-mobile.png'), style: '#sidebar { visibility:hidden; }' });
    await page.locator('.lesson-illustration img').click();
    assert.ok(await page.locator('[role="dialog"]').isVisible());
    await page.keyboard.press('Escape');
    assert.deepEqual(errors, []);
    console.log('PASS 84 radiology pages: images load, reference preserved; Doppler numerical states, keyboard, reset, desktop/mobile, night/day; image viewer');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
