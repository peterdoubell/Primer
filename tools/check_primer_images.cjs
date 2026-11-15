#!/usr/bin/env node
'use strict';
// Run against an isolated, onboarded server. External article fetching may be disabled.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const base = process.argv[2] || 'http://127.0.0.1:8793';
const out = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'primer-image-review-'));
const root = path.resolve(__dirname, '..');
const curricula = fs.readdirSync(path.join(root, 'data/curriculum')).filter(f => /^\d.*\.json$/.test(f))
  .map(f => JSON.parse(fs.readFileSync(path.join(root, 'data/curriculum', f), 'utf8')));
(async () => {
 const browser = await chromium.launch({headless:true});
 const errors = [], results = [];
 try {
  const page = await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  page.on('pageerror',e=>errors.push(e.message));
  for (const domain of curricula) {
   for (let ni=0;ni<domain.nodes.length;ni++) {
    const n=domain.nodes[ni], plates=n.lesson_media.filter(m=>m.kind==='illustration');
    await page.setViewportSize({width:1440,height:1000});
    await page.goto(base+'/#/node/'+n.id);
    await page.waitForFunction(count=>{
     const imgs=[...document.querySelectorAll('.lesson-illustration img')];
     return imgs.length===count && imgs.every(i=>i.complete&&i.naturalWidth>0);
    },plates.length);
    const figures=page.locator('.lesson-illustration');
    for (const width of [1440,390]) {
     await page.setViewportSize({width,height:1000});
     for (let i=0;i<plates.length;i++) {
      const figure=figures.nth(i),img=figure.locator('img');
      assert.equal(await img.getAttribute('alt'),plates[i].alt,n.id);
      const box=await img.boundingBox();
      assert.ok(box.width>0&&box.x>=-1&&box.x+box.width<=width+1,`${n.id} ${width}: clipped image`);
      const ratio=box.width/box.height;
      assert.ok(Math.abs(ratio-1.6)<.02,`${n.id}: distorted image`);
      assert.ok((await figure.innerText()).includes(plates[i].caption),`${n.id}: missing caption`);
     }
    }
    if (ni===Math.floor(domain.nodes.length/2)||plates.length>1) {
     await figures.last().scrollIntoViewIfNeeded();
     await figures.last().screenshot({path:path.join(out,domain.id+'-'+ni+'-mobile.png')});
     await figures.last().locator('img').click();
     const dialog=page.locator('[role="dialog"]');
     await dialog.waitFor();
     await page.keyboard.press('Escape');
     await dialog.waitFor({state:'hidden'});
    }
    results.push({lesson:n.id,plates:plates.length});
   }
   console.log(`PASS ${domain.id}: ${domain.nodes.length} lessons, desktop/mobile images and viewer`);
  }
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({results,errors},null,2));
  console.log(`PASS ${results.length} lessons; ${results.reduce((sum,r)=>sum+r.plates,0)} images; ${out}`);
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
