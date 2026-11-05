'use strict';
// Browser checks for the shared module flow without a learner database.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const source = fs.readFileSync(path.join(__dirname, '../web/app.js'), 'utf8');
const helpers = source.slice(source.indexOf('function el('), source.indexOf('/* ---------------- drawn glyphs'));
const teaching = source.slice(source.indexOf('function renderTeachingLesson('), source.indexOf('async function renderNode('));
const mission = teaching + '\n' + fs.readFileSync(path.join(__dirname, '../web/module-mission.js'), 'utf8');
(async () => {
  const browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}) });
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await page.setContent('<main></main>');
    await page.addStyleTag({ path: path.join(__dirname, '../web/styles.css') });
    await page.addStyleTag({ path: path.join(__dirname, '../web/module-mission.css') });
    await page.addScriptTag({ content: `async function renderNode() {} const S = { stage: 3, state: { profile: { xp: 120, streak: 3 } } }; ${helpers}\n${mission}` });
    await page.evaluate(() => {
      const main = document.querySelector('main');
      const lesson = renderTeachingLesson({ stage: 3, lesson: {
        overview: 'First paragraph.\n\nSecond paragraph.', worked_example: 'Example <script> remains text.',
        activity: 'Try the activity.', reflection: 'Explain your reasoning.'
      }});
      main.append(renderModuleMission({}, [{title:'Learn', hint:'Discover', target:lesson},
        {title:'Challenge', hint:'Show what you know', target:lesson}]), lesson);
    });
    assert.equal(await page.locator('.teaching-step:visible').count(), 1);
    await page.getByRole('button', { name: 'Continue', exact: true }).click();
    assert.equal(await page.locator('.teaching-step:visible').innerText(), 'See an example\n\nExample <script> remains text.');
    assert.equal(await page.evaluate(() => document.activeElement.textContent), 'See an example');
    await page.getByRole('button', { name: 'Show full lesson' }).click();
    assert.equal(await page.locator('.teaching-step:visible').count(), 4);
    assert.equal(await page.getByRole('button', { name: 'Continue', exact: true }).isDisabled(), true);
    await page.getByRole('button', { name: 'One step at a time' }).click();
    assert.equal(await page.locator('.teaching-step:visible').count(), 1);
    await page.locator('.module-mission-stop').first().click();
    await page.locator('.module-mission-stop').first().click();
    assert.equal(await page.locator('progress').evaluate(e => e.value), 1, 'Repeated visits do not inflate progress');
    await page.locator('.module-mission-stop').last().click();
    assert.equal(await page.locator('progress').evaluate(e => e.value), 2);
    assert.equal(await page.locator('[aria-current="step"]').count(), 1);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Mobile has no horizontal overflow');
    console.log('Module mission: navigation, progress, focus, plain text, full lesson and mobile checks passed.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
