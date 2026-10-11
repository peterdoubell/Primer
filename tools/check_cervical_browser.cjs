#!/usr/bin/env node
'use strict';

// Browser integration review for the cervical-cancer source figures.
//
// tests/test_cervical_cancer_runtime.py pins
// docs/cervical-cancer-source-review/browser-integration-review.json to the
// sha256 of web/app.js: the record says what a real browser saw, and it only
// says it about the app.js it was taken against. Any change to app.js means
// re-running this review against the changed file. That review was first done
// by hand; this script does the same checks so it can be repeated.
//
// Run it against an isolated loopback server whose disposable database already
// has an onboarded reader (it never creates one and writes nothing):
//
//   NODE_PATH=/path/to/node_modules node tools/check_cervical_browser.cjs http://127.0.0.1:8749
//
// It prints EVIDENCE_DIRECTORY; review.json and the screenshots land there.
// Look at the screenshots before copying review.json over the committed record.
// The script exits non-zero when any check fails, and still writes the record,
// so a failure can be read rather than guessed at.

const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const { createEvidenceDirectory, loopbackQaUrl } = require('./qa-browser.cjs');

const ROOT = path.resolve(__dirname, '..');
const EVIDENCE = path.join(ROOT, 'docs/cervical-cancer-source-review');
const base = loopbackQaUrl(process.argv[2]);
const out = createEvidenceDirectory();
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

const contractBytes = fs.readFileSync(path.join(EVIDENCE, 'source-figure-contract.json'));
const contract = JSON.parse(contractBytes).structure_atlas;
const bySrc = new Map(contract.map(entry => [entry.src, entry]));
const appJsSha = sha(fs.readFileSync(path.join(ROOT, 'web/app.js')));
const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, 'web/anatomy/hra-female-pelvis-v1.10/manifest.json')));
const manifestByFile = new Map(Object.values(manifest.parts).map(part => [part.file, part]));
const NATIVE_Y_UP = ['native-x-left-y-superior-z-anterior', 'native-gltf-y-up']
  .includes(manifest.coordinate_system && manifest.coordinate_system.display_basis);

const ROUTES = [
  { route: 'reporting', hash: '#/radiology/ra.mri-cervical-cancer' },
  { route: 'lesson', hash: '#/node/rad.5.uterine-mr' },
];
const WIDTHS = [1440, 390];
// The figures opened in the lightbox: the book-chapter figure whose "3.1"
// heading must survive, one JPEG article figure and one PNG.
const ENLARGE = ['open-cervical-cancer-normal-uterus-2018-fig3-1',
  'open-cervical-cancer-pmc10605640-fig11', 'open-cervical-cancer-pmc10886638-fig4'];
// Statements a prompt must not make on the reader's behalf.
const NORMAL_ASSERTIONS = ['No parametrial invasion', 'No vaginal', 'No suspicious', 'Preserved low-signal', 'FIGO IIB'];
const FIG_3_1 = 'open-cervical-cancer-normal-uterus-2018-fig3-1';

// Waits for an image to finish (load or error), but never forever: a figure
// that does not arrive is recorded as incomplete instead of hanging the run.
function settled(img, ms = 20000) {
  return img.evaluate((el, ms) => el.complete && el.naturalWidth > 0 ? true : new Promise(resolve => {
    el.addEventListener('load', () => resolve(true), { once: true });
    el.addEventListener('error', () => resolve(false), { once: true });
    setTimeout(() => resolve(false), ms);
  }), ms);
}

// Every cervical source figure currently shown (in a visible panel), checked
// against the contract after it has been scrolled into view and has loaded.
async function checkVisibleFigures(page, seen) {
  const srcs = await page.$$eval('figure.rad-anatomy-illustration img[data-source-figure]', imgs =>
    // checkVisibility, not offsetParent: a figure inside a closed <details>
    // still has an offsetParent, but is not rendered and never loads.
    imgs.filter(img => img.checkVisibility()).map(img => img.getAttribute('src')));
  for (const src of srcs) {
    if (!bySrc.has(src) || seen.has(src)) continue;
    const entry = bySrc.get(src);
    const img = page.locator('figure.rad-anatomy-illustration img[data-source-figure][src="' + src + '"]').first();
    await img.scrollIntoViewIfNeeded();
    await settled(img);
    const seenFigure = await img.evaluate((el, expected) => {
      const figure = el.closest('figure');
      const heading = figure.querySelector('h4').textContent.trim();
      const credits = [...figure.querySelectorAll('figcaption .rad-image-credit')];
      const limits = credits.find(p => p.textContent.trim() === expected.limits.trim());
      const limitsBox = limits && limits.getBoundingClientRect();
      const full = figure.querySelector('details.rad-source-caption p');
      return {
        id: expected.id, heading, width: el.naturalWidth, height: el.naturalHeight,
        source_caption_full_matches: expected.source_caption_full === expected.caption
          ? !full : !!full && full.textContent.trim() === expected.source_caption_full.trim(),
        display_filter: getComputedStyle(el).filter,
        case_modality_limits_visible: heading.includes(expected.modality)
          && !!limits && limitsBox.width > 0 && limitsBox.height > 0 && getComputedStyle(limits).visibility === 'visible',
      };
    }, entry);
    seenFigure.complete = seenFigure.width === entry.width && seenFigure.height === entry.height
      && seenFigure.source_caption_full_matches && seenFigure.display_filter === 'none';
    seen.set(src, seenFigure);
  }
}

async function overflow(page) {
  return page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
}

async function enlarge(page, id) {
  if (process.env.QA_TRACE) console.log('  enlarge ' + id);
  const entry = contract.find(item => item.id === id);
  const img = page.locator('figure.rad-anatomy-illustration img[data-source-figure][src="' + entry.src + '"]')
    .filter({ visible: true }).first();
  await img.scrollIntoViewIfNeeded();
  await img.click();
  const dialog = page.locator('[role="dialog"]').last();
  await dialog.waitFor();
  const big = dialog.locator('img').first();
  await settled(big);
  const zoom = dialog.getByRole('button', { name: 'Read labels at full size' });
  const hasZoom = await zoom.count() === 1;
  if (hasZoom) await zoom.click();
  await page.waitForTimeout(150);
  const seen = await dialog.evaluate((box, expected) => {
    const image = box.querySelector('img');
    const scroller = image.closest('.is-zoomed');
    return {
      id: expected.id, src: image.getAttribute('src'),
      width: image.naturalWidth, height: image.naturalHeight,
      rendered_width: Math.round(image.getBoundingClientRect().width),
      zoomed: !!scroller, text: box.innerText.slice(0, 600),
    };
  }, entry);
  await page.keyboard.press('Escape');
  await dialog.waitFor({ state: 'detached' }).catch(() => {});
  seen.native_size_control = hasZoom && seen.zoomed && Math.abs(seen.rendered_width - entry.width) <= 2;
  seen.original = seen.src === entry.src && seen.width === entry.width && seen.height === entry.height;
  return seen;
}

async function nativeReference(page) {
  if (process.env.QA_TRACE) console.log('  native reference');
  const root = page.locator('[data-atlas="hra-female-pelvis-v1.10"]').filter({ visible: true }).first();
  await root.scrollIntoViewIfNeeded();
  await page.waitForFunction(() => {
    const el = [...document.querySelectorAll('[data-atlas="hra-female-pelvis-v1.10"]')].find(e => e.offsetParent !== null);
    return el && (el.dataset.ready === 'true' || el.dataset.error === 'true');
  }, null, { timeout: 60000 });
  return root.evaluate(el => {
    const canvas = el.querySelector('canvas');
    return { meshes: Number(el.dataset.meshes), triangles: Number(el.dataset.triangles),
      ready: el.dataset.ready === 'true', cropped: canvas ? canvas.dataset.cropped : null, note: el.innerText.slice(0, 1200) };
  });
}

async function assessment(page) {
  await page.getByRole('tab', { name: 'Step by step' }).click();
  const walk = page.locator('.rad-walk').filter({ visible: true }).first();
  await walk.waitFor();
  const api = await page.evaluate(() => fetch('/api/radiology/modules/ra.mri-cervical-cancer').then(r => r.json()));
  const steps = api.radiology_reference.walkthrough.steps;
  await walk.getByRole('button', { name: 'Insert assessment prompts' }).click();
  const labels = await walk.locator('.rad-walk-step-label').allInnerTexts();
  const record = [];
  for (const step of steps) {
    const index = labels.indexOf(step.label);
    await walk.locator('.rad-walk-step').nth(index).click();
    await walk.getByRole('button', { name: /^Figures/ }).click();
    await page.waitForTimeout(150);
    const shown = await walk.locator('.rad-walk-figures img').evaluateAll(imgs => imgs.map(i => i.getAttribute('src')));
    // The step's own assessment fields (the ones its preset fills), read back
    // from the page after "Insert assessment prompts".
    const fields = await walk.locator('.rad-walk-main .rad-walk-field').evaluateAll(nodes => nodes.map(node =>
      ({ heading: node.querySelector('label').textContent.trim(), value: node.querySelector('textarea').value })));
    const own = fields.filter(field => Object.prototype.hasOwnProperty.call(step.normal || {}, field.heading));
    record.push({
      label: step.label, source_images: shown,
      unfilled_assessment_prompts: own.length === Object.keys(step.normal || {}).length && own.length > 0
        && own.every(field => field.value.includes('[__]') && !NORMAL_ASSERTIONS.some(t => field.value.includes(t))),
    });
  }
  await walk.locator('.rad-walk-step').last().click();
  const report = await walk.locator('textarea.rad-walk-preview').inputValue();
  const template = (api.radiology_reference.report_templates || [])[0];
  const headings = template && template.sections ? template.sections.map(s => s.heading) : [];
  return {
    step_count: record.length, steps: record,
    all_source_matched_images: record.every(s => s.source_images.length > 0 && s.source_images.every(src => bySrc.has(src))),
    all_prompts_unfilled: record.every(s => s.unfilled_assessment_prompts),
    assembled_report_has_all_sections: headings.length > 0 && headings.every(h => report.includes(h)),
  };
}

async function review(browser, { route, hash }, width) {
  const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  const pageErrors = [], failed = [], reads = [];
  const images = new Map(), meshes = new Map();
  let servedAppJs = null;
  page.on('pageerror', error => pageErrors.push(error.message));
  page.on('requestfailed', request => failed.push({ url: request.url(), error: request.failure() && request.failure().errorText }));
  page.on('response', response => {
    const url = new URL(response.url());
    if (response.status() >= 400) failed.push({ url: response.url(), status: response.status() });
    if (url.origin !== base) return;
    if (/^\/app\/app(\.[0-9a-f]+)?\.js$/.test(url.pathname)) reads.push(response.body().then(b => { servedAppJs = sha(b); }));
    if (bySrc.has(url.pathname)) reads.push(response.body().then(b =>
      images.set(url.pathname, { sha256: sha(b), bytes: b.length, status: response.status() })));
    if (manifestByFile.has(url.pathname)) reads.push(response.body().then(b =>
      meshes.set(url.pathname, { sha256: sha(b), bytes: b.length, status: response.status() })));
  });
  const seen = new Map();
  let horizontal = false;
  const tag = route + '-' + width;
  const shots = [];
  const shoot = async name => {
    const file = 'runtime-' + tag + '-' + name + '.png';
    await page.screenshot({ path: path.join(out, file) });
    shots.push({ file, sha256: sha(fs.readFileSync(path.join(out, file))) });
  };

  await page.goto(base + '/' + hash);
  await page.locator('.pagehead h2').waitFor();
  let walkthrough = null, native;
  const enlarged = [];
  if (route === 'reporting') {
    for (const name of ['Images', 'Diagram']) {
      await page.getByRole('tab', { name: new RegExp('^' + name) }).click();
      await checkVisibleFigures(page, seen);
      horizontal = horizontal || await overflow(page);
      if (name === 'Images') await shoot('images');
      for (const id of ENLARGE) {
        const src = contract.find(item => item.id === id).src;
        const here = await page.locator('figure.rad-anatomy-illustration img[src="' + src + '"]').filter({ visible: true }).count();
        if (here && !enlarged.some(e => e.id === id)) enlarged.push(await enlarge(page, id));
      }
    }
    await page.getByRole('tab', { name: '3D anatomy' }).click();
    native = await nativeReference(page);
    horizontal = horizontal || await overflow(page);
    await shoot('anatomy');
    walkthrough = await assessment(page);
    horizontal = horizontal || await overflow(page);
    await shoot('assessment');
  } else {
    await page.getByRole('button', { name: 'Load original source figures' }).click();
    await page.waitForFunction(n => document.querySelectorAll('figure.rad-anatomy-illustration img[data-source-figure]').length >= n,
      contract.length, { timeout: 30000 });
    // The shared gallery files each module's originals under its own
    // disclosure; the cervical set is opened the way a reader would open it.
    await page.locator('.lesson-source-gallery details > summary', { hasText: /^MRI cervical cancer staging/ }).click();
    await checkVisibleFigures(page, seen);
    horizontal = horizontal || await overflow(page);
    await shoot('figures');
    for (const id of ENLARGE) enlarged.push(await enlarge(page, id));
    native = await nativeReference(page);
    horizontal = horizontal || await overflow(page);
    await shoot('anatomy');
  }
  const heldRemote = await page.$$eval('img', imgs => imgs
    .map(img => img.currentSrc || img.src).filter(src => src && !src.startsWith(location.origin)
      && !src.startsWith('data:') && !src.startsWith('blob:')));
  await Promise.all(reads);
  await context.close();

  const figureChecks = contract.filter(entry => seen.has(entry.src)).map(entry => seen.get(entry.src));
  const imageResponses = contract.filter(entry => images.has(entry.src))
    .map(entry => ({ id: entry.id, src: entry.src, ...images.get(entry.src) }));
  const meshResponses = [...meshes].map(([file, got]) => {
    const part = manifestByFile.get(file);
    return { path: file, ...got, vertices: part.vertices, triangles: part.triangles,
      matches_manifest: got.sha256 === part.sha256 || got.sha256 === part.decoded_sha256 };
  });
  const fig31 = seen.get(contract.find(item => item.id === FIG_3_1).src);
  const result = {
    route, url: base + '/' + hash, viewport: { width, height: 1000 },
    complete_cervical_figure_count: figureChecks.filter(f => f.complete).length,
    all_native_image_response_hashes_match: imageResponses.length === contract.length
      && imageResponses.every(r => r.status === 200 && r.sha256 === bySrc.get(r.src).sha256),
    book_heading_preserves_figure_3_1: !!fig31 && fig31.heading.startsWith('Figure 3.1'),
    source_case_modality_staging_limits_visible: figureChecks.length === contract.length
      && figureChecks.every(f => f.case_modality_limits_visible),
    enlarged_originals_and_native_size_control_verified: enlarged.length === ENLARGE.length
      && enlarged.every(e => e.original && e.native_size_control),
    no_held_remote_ra_images: heldRemote.length === 0,
  };
  if (walkthrough) Object.assign(result, {
    assessment_step_count: walkthrough.step_count,
    only_source_matched_step_images: walkthrough.all_source_matched_images,
    assessment_prompts_do_not_assert_normality: walkthrough.all_prompts_unfilled,
  });
  Object.assign(result, {
    native_reference_mesh_count: native.meshes,
    native_reference_uncropped: native.cropped === 'false',
    native_reference_is_independent_and_unregistered: /independent of the published MRI cases/.test(native.note)
      && /registration are unverified/.test(native.note),
    native_reference: { meshes: native.meshes, triangles: native.triangles, cropped: native.cropped,
      native_y_up: NATIVE_Y_UP, note: native.note },
    mesh_hashes_match_manifest: meshResponses.length === native.meshes && meshResponses.every(m => m.matches_manifest),
    figure_checks: figureChecks, enlarged, image_responses: imageResponses, mesh_responses: meshResponses,
    screenshots: shots, page_errors: pageErrors, failed_requests: failed, horizontal_overflow: horizontal,
    held_remote_images: heldRemote, served_app_js_sha256: servedAppJs,
  });
  if (walkthrough) result.assessment = walkthrough;
  return result;
}

function passed(result) {
  return result.complete_cervical_figure_count === contract.length
    && result.all_native_image_response_hashes_match && result.book_heading_preserves_figure_3_1
    && result.source_case_modality_staging_limits_visible && result.enlarged_originals_and_native_size_control_verified
    && result.no_held_remote_ra_images && result.native_reference_mesh_count === 54 && result.native_reference_uncropped
    && result.native_reference_is_independent_and_unregistered && result.mesh_hashes_match_manifest
    && result.page_errors.length === 0 && result.failed_requests.length === 0 && !result.horizontal_overflow
    && (result.served_app_js_sha256 === null || result.served_app_js_sha256 === appJsSha)
    && (result.route !== 'reporting' || (result.assessment_step_count === 8
      && result.only_source_matched_step_images && result.assessment_prompts_do_not_assert_normality
      && result.assessment.assembled_report_has_all_sections));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    // Optional slot 3: one route name, to repeat a single route while
    // investigating. The committed record must come from a run of both.
    const only = process.argv[3];
    for (const target of ROUTES.filter(r => !only || r.route === only)) for (const width of WIDTHS) {
      console.log('Reviewing ' + target.route + ' at ' + width + 'px');
      results.push(await review(browser, target, width));
    }
  } finally {
    await browser.close();
  }
  const record = {
    reviewed_on: new Date().toISOString().slice(0, 10),
    qa_only_server: base,
    browser_session: 'tools/check_cervical_browser.cjs · headless Chromium (Playwright)',
    all_requested_routes_and_viewports_passed: results.every(passed),
    app_js_sha256: appJsSha,
    source_contract_sha256: sha(contractBytes),
    production_or_deployment_verification: false,
    clinical_approval: false,
    every_structure_approved: false,
    fine_3D_tissue_layers_approved: false,
    patient_registration_verified: false,
    results,
  };
  fs.writeFileSync(path.join(out, 'review.json'), JSON.stringify(record, null, 1) + '\n');
  for (const result of results) {
    console.log(result.route + ' ' + result.viewport.width + ': ' + (passed(result) ? 'pass' : 'FAIL') + ' · '
      + result.complete_cervical_figure_count + ' figures · ' + result.native_reference_mesh_count + ' meshes');
  }
  console.log('REVIEW=' + path.join(out, 'review.json'));
  if (!record.all_requested_routes_and_viewports_passed) process.exitCode = 1;
})().catch(error => { console.error(error); process.exitCode = 1; });
