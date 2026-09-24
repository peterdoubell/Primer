#!/usr/bin/env node
'use strict';
// Run against an already-onboarded, isolated QA server; never creates readers.
// Evidence uses a fresh private temporary directory; printed as EVIDENCE_DIRECTORY.
// Legacy output-directory argument (slot 3) is ignored; see docs/browser-qa.md.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const { createEvidenceDirectory, loopbackQaUrl } = require('./qa-browser.cjs');
const base = loopbackQaUrl(process.argv[2]);
const out = createEvidenceDirectory();
const nodes = fs.readdirSync(path.join(__dirname, '../data/curriculum'))
  .filter(file => /^\d.*\.json$/.test(file))
  .flatMap(file => JSON.parse(fs.readFileSync(path.join(__dirname, '../data/curriculum', file))).nodes);
const early = nodes.find(node => node.stage === 0 && node.lesson);
const advanced = nodes.find(node => node.stage === 5 && node.lesson);
assert.ok(early && advanced, 'Expansion must include taught lessons at both ends of the pathway');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const errors = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, reducedMotion: 'reduce' });
    page.on('pageerror', error => errors.push(error.message));
    const state = await (await page.request.get(base + '/api/state')).json();
    assert.ok(state.onboarded, 'Use an already-onboarded QA server');
    const graph = await (await page.request.get(base + '/api/curriculum')).json();
    assert.equal(graph.nodes.length, nodes.length);
    assert.ok(graph.nodes.every(node => !node.lesson && !node.learning_outcomes), 'Atlas payload must omit teaching bodies');
    const domain = graph.nodes.find(node => node.id === early.id).domain;
    await page.goto(base + '/#/atlas');
    await page.locator('.pathway-overview').waitFor();
    assert.equal(await page.locator('#atlas-field-filter option').count(), graph.domains.length + 1);
    assert.equal(await page.locator('.pathway-stage').count(), state.stages.length);
    assert.match(await page.locator('.pathway-stages').innerText(), /3–5/);
    assert.match(await page.locator('.pathway-stages').innerText(), /master/i);
    await page.screenshot({ path: path.join(out, 'pathways-desktop.png') });

    await page.goto(base + '/#/atlas/' + domain + '/0');
    await page.locator('.pathway-stage[aria-pressed="true"]').waitFor();
    assert.equal(await page.locator('#atlas-field-filter').inputValue(), domain);
    assert.equal(await page.locator('.atlas-board .domain-block').count(), 1);
    assert.equal(await page.locator('.atlas-board .node-dot').count(), graph.nodes.filter(node => node.domain === domain && node.stage === 0).length);
    await page.locator('.pathway-stage').nth(5).focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('.pathway-stage[aria-pressed="true"]').count(), 1);
    assert.equal(await page.locator('.atlas-board .node-dot').count(), graph.nodes.filter(node => node.domain === domain && node.stage === 5).length);
    await page.getByRole('button', { name: 'Show all stages', exact: true }).click();
    const expectedLesson = graph.nodes.find(node => node.domain === domain && node.stage === 0);
    await page.locator('#atlas-lesson-search').fill(expectedLesson.title);
    assert.ok(await page.locator('.atlas-board .node-dot').count() > 0);
    assert.ok((await page.locator('.atlas-board').innerText()).includes(expectedLesson.title));

    for (const node of [early, advanced]) {
      await page.goto(base + '/#/node/' + node.id);
      await page.locator('.teaching-lesson').waitFor();
      assert.equal(await page.locator('.teaching-step').count(), 4, node.id);
      assert.equal(await page.locator('.lesson-outcomes li').count(), node.learning_outcomes.length, node.id);
      assert.ok((await page.locator('.teaching-lesson').innerText()).includes(node.lesson.worked_example));
      assert.equal(await page.locator('.lesson-pathway-links a').count(), 2);
      if (node.stage === 0) assert.equal(await page.getByRole('button', { name: 'Read this lesson aloud', exact: true }).count(), 1);
    }
    await page.goto(base + '/#/node/' + early.id);
    await page.locator('.lesson-pathway-links').waitFor();
    await page.locator('.lesson-pathway-links').getByRole('link', { name: 'Visuals at this stage' }).click();
    await page.locator('#visual-stage-filter').waitFor();
    assert.equal(await page.locator('#visual-domain-filter').inputValue(), domain);
    assert.equal(await page.locator('#visual-stage-filter').inputValue(), '0');
    assert.ok(await page.locator('.math-image-card:visible').count() >= 3, 'Stage pathway should have scenes, illustrations and models');
    await page.getByRole('button', { name: 'Browse this learning pathway' }).click();
    await page.locator('.pathway-overview').waitFor();
    assert.equal(await page.locator('#atlas-field-filter').inputValue(), domain);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(out, 'pathways-mobile.png') });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Atlas must fit mobile width');
    await page.goto(base + '/#/node/' + early.id);
    await page.locator('.teaching-lesson').waitFor();
    await page.locator('.teaching-lesson').scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(out, 'early-lesson-mobile.png') });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Lesson must fit mobile width');
    assert.deepEqual(errors, []);
    console.log('PASS dynamic field/stage coverage, keyboard filters, teaching content, age-3 listening, gallery round-trip, mobile width and zero browser exceptions');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
