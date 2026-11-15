// Exercise actual WebGL clipping against each compartment's world-space bounds.
'use strict';
const assert = require('node:assert/strict');
const {readFile} = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');

async function verify() {
  const directory = path.join(__dirname, '../web/anatomy/glioblastoma-ba2');
  const origin = 'http://localhost:4100';
  const browser = await chromium.launch({args: ['--enable-unsafe-swiftshader']});
  try {
    const page = await browser.newPage();
    await page.route(origin + '/**', async route => {
      const file = path.basename(new URL(route.request().url()).pathname);
      const type = file.endsWith('.js') ? 'text/javascript' : file.endsWith('.html') ? 'text/html' : 'application/octet-stream';
      await route.fulfill({body: await readFile(path.join(directory, file)), contentType: type});
    });
    await page.goto(origin + '/index.html');
    await page.waitForFunction(() => document.querySelectorAll('main canvas').length === 4 &&
      document.querySelector('#surface-status').textContent.includes('82,436'));
    const controls = page.locator('.layer');
    const cut = page.locator('#section-cut');
    const canvas = page.locator('#surface');
    const snapshot = () => canvas.evaluate(element => element.toDataURL());
    for (const control of await controls.all()) await control.uncheck();
    const empty = await snapshot();
    const rows = JSON.parse(await readFile(path.join(directory, 'surfaces.json')));
    for (const [index, row] of rows.entries()) {
      await controls.nth(index).check();
      const whole = await snapshot();
      assert.notEqual(whole, empty);
      await cut.check();
      for (const axis of [0, 1, 2]) {
        await page.locator('#plane').selectOption(String(axis));
        const low = Math.floor(row.bounds[0][axis]);
        const high = Math.ceil(row.bounds[1][axis]);
        const middle = Math.round((low + high) / 2);
        for (const coordinate of [low, middle, high]) {
          const slice = [90 - coordinate, coordinate + 126, coordinate + 72][axis];
          await page.locator('#slice').fill(String(slice));
          assert.ok((await page.locator('#cut-info').textContent()).includes(['R','A','S'][axis] + ' = ' + coordinate + ' mm'));
          const image = await snapshot();
          if (coordinate === low) assert.equal(image, empty);
          else if (coordinate === high) assert.equal(image, whole);
          else assert.ok(image !== empty && image !== whole);
        }
      }
      await cut.uncheck();
      assert.equal(await snapshot(), whole);
      await controls.nth(index).uncheck();
    }
    console.log('Verified 27 clipped GPU images and restored all three whole surfaces.');
  } finally {
    await browser.close();
  }
}
verify().catch(error => { console.error(error); process.exitCode = 1; });
