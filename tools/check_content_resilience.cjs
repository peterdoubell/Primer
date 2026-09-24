#!/usr/bin/env node
'use strict';
// An onboarded isolated QA server only. Includes deliberate request failures.
// Evidence uses a fresh private temporary directory; printed as EVIDENCE_DIRECTORY.
// Legacy output-directory argument (slot 3) is ignored; see docs/browser-qa.md.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const { createEvidenceDirectory, loopbackQaUrl } = require('./qa-browser.cjs');
const base = loopbackQaUrl(process.argv[2]);
const out = createEvidenceDirectory();
const curriculum = fs.readdirSync(path.join(__dirname, '../data/curriculum')).filter(f => /^\d.*\.json$/.test(f))
  .flatMap(f => JSON.parse(fs.readFileSync(path.join(__dirname, '../data/curriculum', f))).nodes);
(async () => {
  const browser = await chromium.launch({headless:true});
  const errors = [], times = [];
  try {
    const page = await browser.newPage({viewport:{width:1200,height:900}, reducedMotion:'reduce'});
    page.on('pageerror', e => errors.push(e.message));
    // Every local lesson response must work, independent of Wikipedia.
    let next = 0;
    await Promise.all(Array.from({length:4}, async () => {
      while (next < curriculum.length) {
        const n = curriculum[next++], start = Date.now();
        const response = await page.request.get(base + '/api/curriculum/node/' + n.id);
        assert.equal(response.status(),200,n.id);
        const body = await response.json();
        assert.ok(body.lesson_media.some(m=>m.kind==='illustration'),n.id);
        times.push(Date.now()-start);
      }
    }));
    console.log('PASS '+curriculum.length+' local lesson API responses; max '+Math.max(...times)+' ms');
    const nodes = curriculum.filter(n => n.id.startsWith('rad.')).concat(
      ['math.0.counting','bio.3.genetics','chem.3.atomic-structure','lang.3.essays','arts.1.beat'].map(id=>curriculum.find(n=>n.id===id)).filter(Boolean));
    for (const n of nodes) {
      await page.goto(base+'/#/node/'+n.id);
      await page.locator('.lesson-illustration img').waitFor();
      for (const image of await page.locator('.lesson-illustration img').all()) {
        await image.scrollIntoViewIfNeeded();
        await image.evaluate(i=>i.decode());
      }
      assert.equal(await page.locator('.err-card,.picture-fallback').count(),0,n.id);
    }
    console.log('PASS '+nodes.length+' real lesson browser routes');
    const blocked = '**/illustrations/**/bio-3-genetics-*.webp*';
    await page.route(blocked, r=>r.fulfill({status:503,body:'temporary failure'}));
    await page.goto(base+'/#/node/bio.3.genetics');
    const plate = page.locator('.lesson-illustration');
    await plate.scrollIntoViewIfNeeded();
    await plate.getByRole('button',{name:'Retry image',exact:true}).waitFor();
    assert.equal(await page.locator('.picture-fallback').count(),0);
    assert.equal(await plate.locator('img').isVisible(),false);
    await page.unroute(blocked);
    await plate.getByRole('button',{name:'Retry image',exact:true}).click();
    await page.waitForFunction(()=>{const i=document.querySelector('.lesson-illustration img');return i.naturalWidth>0&&!i.hidden});
    assert.equal(await plate.locator('.image-load-note').count(),0);
    await page.setViewportSize({width:390,height:844});
    await page.route('**/bio-3-genetics-1600.webp*', r=>r.fulfill({status:503,body:'temporary failure'}));
    await page.reload();
    await page.locator('.lesson-illustration').scrollIntoViewIfNeeded();
    await page.waitForFunction(()=>{const i=document.querySelector('.lesson-illustration img');return i&&i.naturalWidth>0});
    await page.locator('.lesson-illustration img').click();
    await page.waitForFunction(()=>{const i=document.querySelector('.lightbox img');return i&&i.naturalWidth>0});
    await page.keyboard.press('Escape');
    await page.unroute('**/bio-3-genetics-1600.webp*');
    console.log('PASS failed-image recovery, manual retry and full-size viewer fallback');
    const api = '**/api/curriculum/node/bio.3.genetics';
    await page.route(api,r=>r.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'test outage'})}));
    await page.reload();
    await page.locator('.err-card').waitFor();
    assert.equal(await page.locator('.err-card .dont-panic').count(),1);
    await page.unroute(api);
    await page.getByRole('button',{name:'Try again',exact:true}).click();
    await page.locator('.lesson-illustration img').waitFor();
    await page.locator('.lesson-illustration').scrollIntoViewIfNeeded();
    await page.waitForFunction(()=>document.querySelector('.lesson-illustration img').naturalWidth>0);
    await page.locator('.lesson-illustration').screenshot({path:path.join(out,'recovered-genetics-mobile.png')});
    const article = '**/api/article?*';
    await page.route(article,r=>r.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'article temporarily unavailable'})}));
    await page.goto(base+'/#/read/Genetics/bio.3.genetics');
    await page.locator('#article .err-card').waitFor();
    assert.equal(await page.locator('.err-card .dont-panic').count(),1);
    await page.unroute(article);
    await page.getByRole('button',{name:'Try again',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('#article h1'));
    assert.equal(await page.locator('#article').count(),1,'retry must not append a second reader');
    assert.equal(await page.locator('#reader-layout').count(),1);
    assert.equal(await page.locator('.err-card,.picture-fallback').count(),0);
    assert.deepEqual(errors,[]);
    console.log('PASS banner only on genuine failures, page/reader retry without duplicate readers, mobile image and zero JavaScript exceptions');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
