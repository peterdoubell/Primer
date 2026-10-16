'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');
const root = path.resolve(__dirname, '..');
const directory = path.join(root, 'web/anatomy/hippunfold-hcp101006-registered');
const base = process.env.HIPP_VIEWER_URL || 'http://127.0.0.1:8867/';
const manifest = JSON.parse(fs.readFileSync(path.join(directory, 'manifest.json')));

(async () => {
  const browser = await chromium.launch({headless: true});
  try {
    const manifestCases = [];
    for (const [name, respond] of [
      ['http-503', route => route.fulfill({status: 503, body: 'Unavailable'})],
      ['network-failure', route => route.abort('failed')],
      ['invalid-json', route => route.fulfill({status: 200, contentType: 'application/json', body: '{'})],
      ['invalid-schema', route => route.fulfill({status: 200, contentType: 'application/json', body: '{}'})]
    ]) {
      const page = await browser.newPage(), errors = [];
      page.on('pageerror', error => errors.push(error.message));
      let release; const pending = new Promise(resolve => { release = resolve; });
      await page.route('**/manifest.json', async route => { await pending; await respond(route); });
      await page.goto(base);
      await page.waitForFunction(() => document.querySelector('#status').textContent === 'Loading reference metadata…');
      const disabled = () => page.evaluate(() => Array.from(document.querySelectorAll('select,input,button')).filter(control => control.id !== 'retry').every(control => control.disabled));
      assert.equal(await disabled(), true);
      assert.equal(await page.locator('#retry').evaluate(button => button.hidden && button.disabled), true);
      release();
      await page.waitForFunction(() => !document.querySelector('#retry').hidden && !document.querySelector('#retry').disabled);
      assert.equal(await disabled(), true);
      assert.equal(await page.locator('#retry').textContent(), 'Retry reference load');
      assert.equal(await page.locator('#mri').evaluate(canvas => canvas.hidden), true);
      assert.equal(await page.locator('#mesh').evaluate(canvas => canvas.hidden), true);
      // Synthetic events also remain safe even though normal controls are disabled.
      await page.evaluate(() => { for (const id of ['plane','class','hemi','surface-scope']) document.getElementById(id).dispatchEvent(new Event('change')); });
      assert.deepEqual(errors, []);
      await page.unroute('**/manifest.json');
      await page.click('#retry');
      await page.waitForFunction(() => document.querySelector('#mri').dataset.ready === 'true' && document.querySelector('#mesh').dataset.ready === 'true');
      assert.equal(await page.locator('#plane').isEnabled(), true);
      assert.equal(await page.locator('#class option').count(), 8);
      assert.equal(await page.locator('#legend > span').count(), 8);
      await page.selectOption('#plane', '0');
      assert.equal(await page.locator('#mri').evaluate(canvas => JSON.parse(canvas.dataset.state).axis), 0);
      assert.deepEqual(errors, []);
      manifestCases.push({case: name, controlsDisabledWhileLoading: true, controlsDisabledAfterFailure: true, hiddenCanvases: true, retrySucceeded: true, safeSyntheticEvents: true, pageErrors: 0});
      await page.close();
    }
    const page = await browser.newPage();
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    await page.goto(base);
    await page.waitForFunction(() => window.HippUnfoldReference && document.querySelector('#mri').dataset.ready === 'true');
    const corrupt = file => { const body = fs.readFileSync(path.join(directory, file)); body[Math.floor(body.length / 2)] ^= 1; return body; };
    await page.route('**/R-T2w.bin.gz', route => route.fulfill({status: 200, contentType: 'application/octet-stream', body: corrupt('R-T2w.bin.gz')}));
    await page.selectOption('#hemi', 'R');
    await page.waitForFunction(() => !document.querySelector('#retry').hidden);
    assert.match(await page.locator('#status').textContent(), /Source payload identity differs/);
    assert.equal(await page.locator('#mri').evaluate(canvas => canvas.hidden && canvas.dataset.ready === 'false' && !canvas.dataset.state && !canvas.dataset.cursor), true);
    assert.equal(await page.locator('#mesh').evaluate(canvas => canvas.hidden), true);
    assert.equal(await page.evaluate(() => window.HippUnfoldReference.state().source), undefined);
    await page.unroute('**/R-T2w.bin.gz');
    await page.click('#retry');
    await page.waitForFunction(() => document.querySelector('#mri').dataset.ready === 'true' && JSON.parse(document.querySelector('#mri').dataset.state).hemi === 'R');
    await page.waitForFunction(() => document.querySelector('#mesh').dataset.ready === 'true');
    await page.route('**/101006-R-label-2.mesh.gz', route => route.fulfill({status: 200, contentType: 'application/octet-stream', body: corrupt('101006-R-label-2.mesh.gz')}));
    await page.selectOption('#class', '2');
    await page.waitForFunction(() => Boolean(document.querySelector('#mesh').dataset.error));
    assert.match(await page.locator('#mesh-status').textContent(), /Source payload identity differs/);
    assert.equal(await page.locator('#mesh').evaluate(canvas => canvas.hidden && canvas.dataset.ready === 'false'), true);
    assert.equal(await page.locator('#mri').evaluate(canvas => !canvas.hidden && canvas.dataset.ready === 'true'), true);
    await page.unroute('**/101006-R-label-2.mesh.gz');
    await page.selectOption('#class', '1');
    await page.waitForFunction(() => document.querySelector('#mesh').dataset.ready === 'true' && document.querySelector('#mesh').dataset.parts === 'R-1');
    for (let value = 1; value <= 8; value++) {
      await page.selectOption('#class', String(value));
      assert.equal(await page.locator('#class-note').textContent(), manifest.classNotes[value]);
    }
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({manifestCases, corruptSourceHidden: true, sourceRetrySucceeded: true, corruptMeshHidden: true, MRIAvailableAfterMeshFailure: true, meshSelectionRecoverySucceeded: true, classNotes: 8, pageErrors: 0}));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
