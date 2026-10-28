/* Isolated activity verification. This does not claim authenticated-reader integration. */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), assert = require('assert/strict');
const root = path.resolve(__dirname, '..');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const proof = { isolatedActivity: true, authenticatedReaderVerified: false, cases: [], errors: [] };
  try {
    for (const width of [390, 1440]) {
      const page = await browser.newPage({ viewport: { width, height: 1000 } });
      page.on('pageerror', e => proof.errors.push(e.message));
      await page.setContent('<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="margin:16px;font-family:system-ui"><main></main></body></html>');
      await page.addStyleTag({ path: path.join(root, 'web/coordinate-plane-lab.css') });
      for (const file of ['algebra-functions-core.js', 'coordinate-plane-core.js', 'coordinate-plane-spatial.js', 'coordinate-plane-lab.js']) await page.addScriptTag({ path: path.join(root, 'web', file) });
      await page.evaluate(() => {
        window.activity = PrimerCoordinatePlaneLab.render({ renderer: 'coordinate-plane-lab', props: { scenario: 'math.2.coordinates' } });
        document.querySelector('main').append(activity);
      });
      const presets = await page.evaluate(() => PrimerCoordinatePlaneCore.presets().map(p => p.id));
      for (const id of presets) {
        await page.locator('[data-coordinate-presets]').selectOption(id);
        const result = await page.evaluate(() => {
          const s = activity.coordinatePlane.getScene(), svg = activity.querySelector('svg');
          const scale = Number(svg.dataset.gain), errors = [];
          for (const marker of svg.querySelectorAll('[data-coordinate-marker]')) {
            const p = s.points.find(p => p.id === marker.dataset.coordinateMarker.split('/')[0]);
            if (Math.abs((Number(marker.getAttribute('cx')) - 340) / scale - p.x) > 1e-10 || Math.abs((320 - Number(marker.getAttribute('cy'))) / scale - p.y) > 1e-10) errors.push(p.id);
          }
          return { state: s.model.state, exactTable: s.points.every(p => [...activity.querySelectorAll('tbody tr')].some(row => row.cells[1].textContent === p.label && row.cells[2].textContent === p.xText && row.cells[3].textContent === p.yText)), overflow: document.documentElement.scrollWidth > innerWidth, geometryErrors: errors };
        });
        assert(result.exactTable && !result.overflow && !result.geometryErrors.length);
        proof.cases.push({ width, preset: id, ...result });
      }
      await page.locator('[data-coordinate-presets]').selectOption('fractional');
      const before = await page.evaluate(() => ({ state: activity.coordinatePlane.getState(), speech: activity.getModelSpeech(), svg: activity.querySelector('svg').outerHTML }));
      await page.locator('[data-coordinate-field=x]').fill('1/0');
      await page.locator('[data-coordinate-field=x]').press('Enter');
      const after = await page.evaluate(() => ({ state: activity.coordinatePlane.getState(), speech: activity.getModelSpeech(), svg: activity.querySelector('svg').outerHTML }));
      assert.deepEqual(after, before);
      assert.match(await page.locator('[data-coordinate-error]').textContent(), /zero/);
      await page.locator('[data-coordinate-field=x]').press('Escape');
      assert.equal(await page.locator('[data-coordinate-field=x]').inputValue(), '-1/2');
      await page.locator('[data-coordinate-field=x]').fill('1/3');
      await page.locator('[data-coordinate-field=x]').press('Enter');
      assert.equal(await page.evaluate(() => document.activeElement.dataset.coordinateField), 'x');
      const directory = path.join(root, '.research/coordinate-plane'); fs.mkdirSync(directory, { recursive: true });
      await page.screenshot({ path: path.join(directory, 'activity-' + width + '.png'), fullPage: true });
      await page.close();
    }
    assert.deepEqual(proof.errors, []); proof.allPassed = true;
    fs.writeFileSync(path.join(root, '.research/coordinate-plane/activity-proof.json'), JSON.stringify(proof, null, 2) + '\n');
    console.log(JSON.stringify({ states: proof.cases.length, errors: proof.errors, allPassed: true }));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
