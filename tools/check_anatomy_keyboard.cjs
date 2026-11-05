'use strict';
const {chromium} = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({args:['--enable-unsafe-swiftshader']});
  const directory = path.resolve(__dirname,'../web');
  try {
    const page = await browser.newPage();
    let release;
    const hold = new Promise(resolve => { release = resolve; });
    await page.route('http://localhost:4100/**',async route => {
      const name = new URL(route.request().url()).pathname;
      if (name.endsWith('/ct.gz')) await hold;
      const type = name.endsWith('.js') ? 'text/javascript' : name.endsWith('.html') ? 'text/html' : 'application/octet-stream';
      await route.fulfill({body:await fs.readFile(path.join(directory,name)),contentType:type});
    });
    await page.goto('http://localhost:4100/anatomy/kidney-adrenal-s0028/index.html');
    assert.ok(await page.locator('#organ').isDisabled());
    release();
    await page.waitForFunction(() => !document.querySelector('#organ').disabled);
    for (const organ of ['0','1','2','3']) {
      await page.selectOption('#organ',organ);
      for (const [panel,h,v] of [[0,0,1],[1,0,2],[2,1,2]]) {
        const canvas = page.locator('.views canvas').nth(panel);
        const voxel = async () => (await page.locator('#point').textContent()).match(/\(([^)]+)\)/)[1].split(',').map(Number);
        const before = await voxel();
        await canvas.press('ArrowRight');
        const right = before.slice(); right[h]--;
        assert.deepEqual(await voxel(),right);
        await canvas.press('ArrowUp');
        right[v]++;
        assert.deepEqual(await voxel(),right);
        await canvas.press('ArrowDown');
        await canvas.press('ArrowLeft');
        assert.deepEqual(await voxel(),before);
      }
    }
    await page.locator('#ruler-start').click();
    // Axial measurement requires a fixed z plane. A sagittal keyboard move changes z.
    await page.locator('.views canvas').nth(2).press('ArrowUp');
    assert.ok(await page.locator('#ruler-end').isDisabled());
    await page.locator('.views canvas').nth(2).press('ArrowDown');
    assert.ok(await page.locator('#ruler-end').isEnabled());
    console.log('Verified loading gate, 48 keyboard movements and same-slice caliper enforcement.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode=1; });
