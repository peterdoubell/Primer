#!/usr/bin/env node
'use strict';

// Smoke check of the native source reader (VerSe vertebrae → CT planes, Liu
// cord/dura) after a UI-only change to web/app.js or web/styles.css.
//
// The full reader proof in docs/native-source-presentation-review-20261011/
// (306 CT frame buffers against native oracles, 204 pointer samples, GPU
// buffers) stays bound to the files it was taken against. A UI-only refresh
// recorded in data/radiology/ui-presentation-refreshes.json does not repeat
// that proof; this check is the evidence the refresh carries instead: the
// reader still opens, every level still links to its own CT reference, the
// Liu contours still load, the native files served are byte-identical to the
// reviewed ones, and nothing errors or overflows.
//
//   NODE_PATH=/path/to/node_modules node tools/check_native_reader_smoke.cjs URL
//
// URL must be an isolated loopback server with an onboarded disposable reader.

const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const { createEvidenceDirectory, loopbackQaUrl } = require('./qa-browser.cjs');

const ROOT = path.resolve(__dirname, '..');
const base = loopbackQaUrl(process.argv[2]);
const out = createEvidenceDirectory();
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const PROOF = JSON.parse(fs.readFileSync(path.join(ROOT,
  'docs/native-source-presentation-review-20261011/reader-presentation-proof.json')));
const SERVED = Object.keys(PROOF.served);
const LEVELS = PROOF.rows[0].meshSelections.map(row => row.level);

async function run(browser, width) {
  const context = await browser.newContext({ viewport: { width, height: 1050 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  page.setDefaultTimeout(30000);
  const errors = [], failed = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('requestfailed', request => failed.push({ url: request.url(), error: request.failure() && request.failure().errorText }));
  page.on('response', response => {
    if (response.status() >= 400) failed.push({ url: response.url(), status: response.status() });
  });
  await page.goto(base + '/#/radiology/ra.thoracolumbar-fractures');
  await page.getByRole('tab', { name: '3D anatomy', exact: true }).click();
  const verse = page.locator('[data-atlas="verse521"]').filter({ visible: true }).first();
  await page.waitForFunction(() => [...document.querySelectorAll('[data-atlas="verse521"]')]
    .some(e => e.checkVisibility() && e.dataset.ready === 'true'), null, { timeout: 60000 });
  const levels = [];
  for (const level of LEVELS) {
    const part = verse.locator('[data-part="verse521-' + level.toLowerCase() + '"]');
    await part.click();
    await page.waitForTimeout(80);
    const links = await page.locator('a[href*="ct-reference.html"]').filter({ visible: true })
      .evaluateAll(as => as.map(a => a.getAttribute('href')));
    const selected = (await verse.locator('.detailed-anatomy-selected').innerText()).trim();
    levels.push({ level, selected, links,
      ok: links.length === 1 && links[0].endsWith('?level=' + level) && selected.startsWith(level + ' ') });
  }
  const meshes = await verse.evaluate(el => Number(el.dataset.meshes));
  await page.screenshot({ path: path.join(out, 'native-reader-' + width + '-verse.png') });
  // Switch the same viewer to the Liu cord/dura source.
  const picker = page.locator('select', { has: page.locator('option', { hasText: 'MRI-derived cord and dural contours' }) })
    .filter({ visible: true }).first();
  const label = await picker.locator('option', { hasText: 'MRI-derived cord and dural contours' }).first().innerText();
  await picker.selectOption({ label: label.trim() });
  await page.waitForFunction(() => [...document.querySelectorAll('[data-atlas="liu-lumbosacral-sub03"]')]
    .some(e => e.checkVisibility() && (e.dataset.ready === 'true' || e.dataset.error === 'true')), null, { timeout: 60000 });
  const liu = await page.locator('[data-atlas="liu-lumbosacral-sub03"]').filter({ visible: true }).first().evaluate(el => ({
    ready: el.dataset.ready === 'true', meshes: Number(el.dataset.meshes),
    parts: [...el.querySelectorAll('[data-part]')].map(p => p.dataset.part),
  }));
  liu.ct_links_after_switch = await page.locator('a[href*="ct-reference.html"]').filter({ visible: true }).count();
  await page.screenshot({ path: path.join(out, 'native-reader-' + width + '-liu.png') });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  // What the server hands out for every file the reviewed proof recorded.
  const served = {};
  for (const file of SERVED) {
    const response = await context.request.get(base + '/app/' + file.replace(/^web\//, ''));
    served[file] = response.ok() ? sha(await response.body()) : 'HTTP ' + response.status();
  }
  await context.close();
  const servedMatches = SERVED.filter(f => !['web/app.js', 'web/styles.css'].includes(f))
    .every(f => served[f] === PROOF.served[f]);
  return {
    width, verse_meshes: meshes, levels, all_levels_link_their_own_ct: levels.length === 17 && levels.every(l => l.ok),
    liu, served, native_files_served_identical_to_reviewed: servedMatches,
    served_app_js_is_current: served['web/app.js'] === sha(fs.readFileSync(path.join(ROOT, 'web/app.js'))),
    served_styles_css_is_current: served['web/styles.css'] === sha(fs.readFileSync(path.join(ROOT, 'web/styles.css'))),
    page_errors: errors, failed_requests: failed, horizontal_overflow: overflow,
  };
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const rows = [];
  try { for (const width of [1440, 390]) rows.push(await run(browser, width)); }
  finally { await browser.close(); }
  const passed = rows.every(r => r.verse_meshes === 17 && r.all_levels_link_their_own_ct
    && r.liu.ready && r.liu.meshes === 2 && r.liu.ct_links_after_switch === 0
    && r.native_files_served_identical_to_reviewed && r.served_app_js_is_current && r.served_styles_css_is_current
    && !r.page_errors.length && !r.failed_requests.length && !r.horizontal_overflow);
  const record = { checked_on: new Date().toISOString().slice(0, 10), qa_only_server: base, passed, rows };
  fs.writeFileSync(path.join(out, 'native-reader-smoke.json'), JSON.stringify(record, null, 1) + '\n');
  for (const r of rows) console.log(r.width + ': levels ' + r.levels.filter(l => l.ok).length + '/17 · liu ' + r.liu.meshes
    + ' · native files identical ' + r.native_files_served_identical_to_reviewed + ' · errors ' + r.page_errors.length
    + ' · failed ' + r.failed_requests.length + ' · overflow ' + r.horizontal_overflow);
  console.log((passed ? 'PASS' : 'FAIL') + ' REPORT=' + path.join(out, 'native-reader-smoke.json'));
  if (!passed) process.exitCode = 1;
})().catch(error => { console.error(error); process.exitCode = 1; });
