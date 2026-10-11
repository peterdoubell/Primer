#!/usr/bin/env node
'use strict';

// Browser integration review for a radiology module's original source figures.
//
// Some modules keep a record of what a real browser saw when it opened their
// source figures — docs/<module>-source-review/browser-integration-review.json
// — and the module's test pins that record to the sha256 of web/app.js (and,
// where it says so, web/radiology-detailed-anatomy.js). The record is only
// true of the files it was taken against, so any change to them means running
// the review again. The first reviews were done by hand; this script does the
// same checks so they can be repeated:
//
//   NODE_PATH=/path/to/node_modules node tools/check_source_review_browser.cjs URL MODULE [ROUTE]
//
// MODULE is one of the keys of MODULES below. URL must be an isolated loopback
// server whose disposable database already has an onboarded reader (the script
// never creates one and writes nothing). ROUTE ("reporting" or "lesson")
// repeats one route while investigating; a committed record must come from a
// run of both. The script prints EVIDENCE_DIRECTORY, where review.json and the
// screenshots land. Look at the screenshots before copying them over the
// committed record. It exits non-zero when any check fails, and still writes
// the record, so a failure can be read rather than guessed at.

const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const { createEvidenceDirectory, loopbackQaUrl } = require('./qa-browser.cjs');

const ROOT = path.resolve(__dirname, '..');
const MODULES = {
  cervical: {
    evidence: 'cervical-cancer-source-review', module: 'ra.mri-cervical-cancer', node: 'rad.5.uterine-mr',
    gallery: /^MRI cervical cancer staging/, steps: 8, meshes: 54,
    enlarge: ['open-cervical-cancer-normal-uterus-2018-fig3-1',
      'open-cervical-cancer-pmc10605640-fig11', 'open-cervical-cancer-pmc10886638-fig4'],
    // The book-chapter figure whose "3.1" heading must survive the renderer.
    heading: { id: 'open-cervical-cancer-normal-uterus-2018-fig3-1', startsWith: 'Figure 3.1' },
  },
  endometrial: {
    evidence: 'endometrial-cancer-source-review', module: 'ra.mri-endometrial-cancer', node: 'rad.5.uterine-mr',
    gallery: /^MRI endometrial cancer/, steps: 9, meshes: 54,
    enlarge: ['open-endometrial-cancer-pmc11119523-fig18', 'open-endometrial-cancer-pmc11119523-fig5',
      'open-endometrial-cancer-pmc7643338-fig3', 'open-endometrial-cancer-esr2026-fig5'],
  },
};
// Statements a prompt must not make on the reader's behalf.
const NORMAL_ASSERTIONS = ['No parametrial invasion', 'No vaginal', 'No suspicious', 'Preserved low-signal', 'FIGO IIB'];
const ATLAS = 'hra-female-pelvis-v1.10';

const base = loopbackQaUrl(process.argv[2]);
const name = process.argv[3];
const config = MODULES[name];
if (!config) throw new Error('MODULE must be one of: ' + Object.keys(MODULES).join(', '));
const only = process.argv[4];
const out = createEvidenceDirectory();
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const EVIDENCE = path.join(ROOT, 'docs', config.evidence);

const contractBytes = fs.readFileSync(path.join(EVIDENCE, 'source-figure-contract.json'));
const contract = JSON.parse(contractBytes).structure_atlas;
const bySrc = new Map(contract.map(entry => [entry.src, entry]));
const appJsSha = sha(fs.readFileSync(path.join(ROOT, 'web/app.js')));
const anatomyJsSha = sha(fs.readFileSync(path.join(ROOT, 'web/radiology-detailed-anatomy.js')));
const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, 'web/anatomy', ATLAS, 'manifest.json')));
const manifestByFile = new Map(Object.values(manifest.parts).map(part => [part.file, part]));
const NATIVE_Y_UP = ['native-x-left-y-superior-z-anterior', 'native-gltf-y-up']
  .includes(manifest.coordinate_system && manifest.coordinate_system.display_basis);
const slug = id => id.replace(/^open-[a-z]+-cancer-/, '');

// Every WebGL draw call, grouped into frames at each clear and kept per
// canvas, so the review can say which objects the last frame actually drew.
function instrumentWebGL() {
  const frames = new WeakMap();
  for (const Ctx of [window.WebGLRenderingContext, window.WebGL2RenderingContext].filter(Boolean)) {
    const clear = Ctx.prototype.clear, draw = Ctx.prototype.drawElements;
    Ctx.prototype.clear = function (mask) {
      const list = frames.get(this.canvas) || [];
      list.push([]); if (list.length > 8) list.shift();
      frames.set(this.canvas, list);
      return clear.call(this, mask);
    };
    Ctx.prototype.drawElements = function (mode, count, type, offset) {
      const list = frames.get(this.canvas) || [[]];
      list[list.length - 1].push({ mode, count, type, offset });
      frames.set(this.canvas, list);
      return draw.call(this, mode, count, type, offset);
    };
  }
  window.__primerLastFrame = canvas => { const list = frames.get(canvas) || []; return list[list.length - 1] || []; };
}

// Waits for an image to finish (load or error), but never forever: a figure
// that does not arrive is recorded as incomplete instead of hanging the run.
function settled(img, ms = 20000) {
  return img.evaluate((el, ms) => el.complete && el.naturalWidth > 0 ? true : new Promise(resolve => {
    el.addEventListener('load', () => resolve(true), { once: true });
    el.addEventListener('error', () => resolve(false), { once: true });
    setTimeout(() => resolve(false), ms);
  }), ms);
}

// Every source figure of this module currently rendered, checked against the
// contract after it has been scrolled into view and has loaded.
async function checkVisibleFigures(page, seen) {
  const srcs = await page.$$eval('figure.rad-anatomy-illustration img[data-source-figure]', imgs =>
    // checkVisibility, not offsetParent: a figure inside a closed <details>
    // still has an offsetParent, but is not rendered and never loads.
    imgs.filter(img => img.checkVisibility()).map(img => img.getAttribute('src')));
  for (const src of srcs) {
    if (!bySrc.has(src) || seen.has(src)) continue;
    const entry = bySrc.get(src);
    const img = page.locator('figure.rad-anatomy-illustration img[data-source-figure][src="' + src + '"]')
      .filter({ visible: true }).first();
    await img.scrollIntoViewIfNeeded();
    await settled(img);
    const figure = await img.evaluate((el, expected) => {
      const box = el.closest('figure');
      const heading = box.querySelector('h4').textContent.trim();
      const limits = [...box.querySelectorAll('figcaption .rad-image-credit')]
        .find(p => p.textContent.trim() === expected.limits.trim());
      const rect = limits && limits.getBoundingClientRect();
      const full = box.querySelector('details.rad-source-caption p');
      return {
        id: expected.id, heading, width: el.naturalWidth, height: el.naturalHeight,
        source_caption_full_matches: expected.source_caption_full === expected.caption
          ? !full : !!full && full.textContent.trim() === expected.source_caption_full.trim(),
        display_filter: getComputedStyle(el).filter,
        case_modality_limits_visible: heading.includes(expected.modality.split(' + ')[0])
          && !!limits && rect.width > 0 && rect.height > 0 && getComputedStyle(limits).visibility === 'visible',
      };
    }, entry);
    figure.complete = figure.width === entry.width && figure.height === entry.height
      && figure.source_caption_full_matches && figure.display_filter === 'none';
    seen.set(src, figure);
  }
}

// Whether the page scrolls sideways, and if so what sticks out — named, so a
// failure says where to look.
const overflowAt = page => page.evaluate(() => {
  const width = window.innerWidth;
  if (document.documentElement.scrollWidth <= width + 1) return null;
  return [...document.querySelectorAll('body *')].filter(e => e.checkVisibility() && e.getBoundingClientRect().right > width + 1)
    .slice(0, 6).map(e => e.tagName.toLowerCase() + '.' + String(e.className).trim().split(/\s+/).join('.')
      + ' → ' + Math.round(e.getBoundingClientRect().right) + 'px');
});

async function enlarge(page, id, shoot) {
  const entry = contract.find(item => item.id === id);
  const img = page.locator('figure.rad-anatomy-illustration img[data-source-figure][src="' + entry.src + '"]')
    .filter({ visible: true }).first();
  await img.scrollIntoViewIfNeeded();
  await img.click();
  const dialog = page.locator('[role="dialog"]').last();
  await dialog.waitFor();
  await settled(dialog.locator('img').first());
  const zoom = dialog.getByRole('button', { name: 'Read labels at full size' });
  const hasZoom = await zoom.count() === 1;
  if (hasZoom) await zoom.click();
  await page.waitForTimeout(150);
  const seen = await dialog.evaluate((box, expected) => {
    const image = box.querySelector('img');
    return {
      id: expected.id, src: image.getAttribute('src'),
      width: image.naturalWidth, height: image.naturalHeight,
      rendered_width: Math.round(image.getBoundingClientRect().width),
      zoomed: !!image.closest('.is-zoomed'), text: box.innerText.slice(0, 600),
    };
  }, entry);
  await shoot(slug(id));
  await page.keyboard.press('Escape');
  await dialog.waitFor({ state: 'detached' }).catch(() => {});
  seen.native_size_control = hasZoom && seen.zoomed && Math.abs(seen.rendered_width - entry.width) <= 2;
  seen.original = seen.src === entry.src && seen.width === entry.width && seen.height === entry.height;
  return seen;
}

async function nativeReference(page, shoot) {
  const roots = page.locator('[data-atlas="' + ATLAS + '"]').filter({ visible: true });
  const root = roots.first();
  await root.scrollIntoViewIfNeeded();
  await page.waitForFunction(atlas => {
    const el = [...document.querySelectorAll('[data-atlas="' + atlas + '"]')].find(e => e.checkVisibility());
    return el && (el.dataset.ready === 'true' || el.dataset.error === 'true');
  }, ATLAS, { timeout: 60000 });
  // Let the renderer settle, then read the last frame it drew.
  await page.waitForTimeout(800);
  const native = await root.evaluate(el => {
    const canvas = el.querySelector('canvas');
    const rect = node => { const r = node.getBoundingClientRect();
      return { x: r.x, y: r.y, width: r.width, height: r.height, top: r.top, right: r.right, bottom: r.bottom, left: r.left }; };
    const orientation = el.querySelector('.detailed-anatomy-orientation');
    const extent = el.querySelector('.detailed-anatomy-crop-status');
    const a = rect(orientation), b = rect(extent);
    return {
      meshes: Number(el.dataset.meshes), triangles: Number(el.dataset.triangles), ready: el.dataset.ready === 'true',
      cropped: canvas ? canvas.dataset.cropped : null,
      draw_calls: canvas ? window.__primerLastFrame(canvas) : [],
      labelRects: { orientation: a, extent: b,
        vertical_overlap_pixels: Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top)) },
      orientation: orientation.textContent.trim(), bodyWidth: document.body.clientWidth,
      note: el.innerText.slice(0, 1200),
    };
  });
  native.viewers = await roots.count();
  await shoot('native-hra');
  return native;
}

async function assessment(page) {
  await page.getByRole('tab', { name: 'Step by step' }).click();
  const walk = page.locator('.rad-walk').filter({ visible: true }).first();
  await walk.waitFor();
  const api = await page.evaluate(id => fetch('/api/radiology/modules/' + id).then(r => r.json()), config.module);
  const steps = api.radiology_reference.walkthrough.steps;
  await walk.getByRole('button', { name: 'Insert assessment prompts' }).click();
  const labels = await walk.locator('.rad-walk-step-label').allInnerTexts();
  const record = [];
  for (const step of steps) {
    await walk.locator('.rad-walk-step').nth(labels.indexOf(step.label)).click();
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

async function review(browser, route, width) {
  const hash = route === 'reporting' ? '#/radiology/' + config.module : '#/node/' + config.node;
  const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' });
  await context.addInitScript(instrumentWebGL);
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  const pageErrors = [], failed = [], reads = [];
  const images = new Map(), meshes = new Map();
  let servedAppJs = null, servedAnatomyJs = null;
  page.on('pageerror', error => pageErrors.push(error.message));
  page.on('requestfailed', request => failed.push({ url: request.url(), error: request.failure() && request.failure().errorText }));
  page.on('response', response => {
    const url = new URL(response.url());
    if (response.status() >= 400) failed.push({ url: response.url(), status: response.status() });
    if (url.origin !== base) return;
    if (/^\/app\/app(\.[0-9a-f]+)?\.js$/.test(url.pathname)) reads.push(response.body().then(b => { servedAppJs = sha(b); }));
    if (/^\/app\/radiology-detailed-anatomy(\.[0-9a-f]+)?\.js$/.test(url.pathname)) reads.push(response.body().then(b => { servedAnatomyJs = sha(b); }));
    if (bySrc.has(url.pathname)) reads.push(response.body().then(b =>
      images.set(url.pathname, { sha256: sha(b), bytes: b.length, status: response.status() })));
    // Playwright hands back the decoded body, so these compare to the
    // manifest's decoded_sha256.
    if (manifestByFile.has(url.pathname)) reads.push(response.body().then(b =>
      meshes.set(url.pathname, { sha256: sha(b), bytes: b.length, status: response.status() })));
  });
  const seen = new Map(), enlarged = [], shots = [], overflows = [];
  let horizontal = false, walkthrough = null, native;
  let stage = 'load';
  const checkOverflow = async () => {
    const found = await overflowAt(page);
    if (found) { horizontal = true; overflows.push({ stage, elements: found }); }
  };
  const shoot = async label => {
    const file = 'runtime-' + route + '-' + width + '-' + label + '.png';
    await page.screenshot({ path: path.join(out, file) });
    shots.push({ file, sha256: sha(fs.readFileSync(path.join(out, file))) });
  };
  const enlargeVisible = async () => {
    for (const id of config.enlarge) {
      if (enlarged.some(e => e.id === id)) continue;
      const src = contract.find(item => item.id === id).src;
      if (await page.locator('figure.rad-anatomy-illustration img[src="' + src + '"]').filter({ visible: true }).count())
        enlarged.push(await enlarge(page, id, shoot));
    }
  };

  await page.goto(base + '/' + hash);
  await page.locator('.pagehead h2').waitFor();
  if (route === 'reporting') {
    // Every tab, so the figures are checked wherever the module files them.
    const tabs = await page.getByRole('tab').allInnerTexts();
    for (const tab of tabs) {
      stage = 'tab ' + tab;
      await page.getByRole('tab', { name: tab, exact: true }).click();
      await checkVisibleFigures(page, seen);
      await enlargeVisible();
      await checkOverflow();
    }
    stage = '3D anatomy';
    await page.getByRole('tab', { name: '3D anatomy', exact: true }).click();
    native = await nativeReference(page, shoot);
    await checkOverflow();
    stage = 'assessment';
    walkthrough = await assessment(page);
    await checkOverflow();
  } else {
    await page.getByRole('button', { name: 'Load original source figures' }).click();
    await page.waitForFunction(n => document.querySelectorAll('figure.rad-anatomy-illustration img[data-source-figure]').length >= n,
      contract.length, { timeout: 30000 });
    // The shared gallery files each module's originals under its own
    // disclosure; this module's set is opened the way a reader would open it.
    await page.locator('.lesson-source-gallery details > summary', { hasText: config.gallery }).click();
    await checkVisibleFigures(page, seen);
    await checkOverflow();
    await enlargeVisible();
    native = await nativeReference(page, shoot);
    await checkOverflow();
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
      matches_manifest: got.sha256 === part.decoded_sha256 };
  });
  const drawn = native.draw_calls;
  const result = {
    route, url: base + '/' + hash, viewport: { width, height: 1000 },
    ['complete_' + name + '_figure_count']: figureChecks.filter(f => f.complete).length,
    all_native_image_response_hashes_match: imageResponses.length === contract.length
      && imageResponses.every(r => r.status === 200 && r.sha256 === bySrc.get(r.src).sha256),
    source_case_modality_staging_limits_visible: figureChecks.length === contract.length
      && figureChecks.every(f => f.case_modality_limits_visible),
    enlarged_originals_and_native_size_control_verified: enlarged.length === config.enlarge.length
      && enlarged.every(e => e.original && e.native_size_control),
    no_held_remote_ra_images: heldRemote.length === 0,
  };
  if (config.heading) {
    const figure = seen.get(contract.find(item => item.id === config.heading.id).src);
    result.book_heading_preserves_figure_3_1 = !!figure && figure.heading.startsWith(config.heading.startsWith);
  }
  if (walkthrough) Object.assign(result, {
    assessment_step_count: walkthrough.step_count,
    only_source_matched_step_images: walkthrough.all_source_matched_images,
    assessment_prompts_do_not_assert_normality: walkthrough.all_prompts_unfilled,
    assessment: walkthrough,
  });
  Object.assign(result, {
    native_reference_viewer_count: native.viewers,
    native_reference_mesh_count: native.meshes,
    all54_source_objects_GPU_drawn: drawn.length === native.meshes
      && drawn.reduce((sum, call) => sum + call.count, 0) === native.triangles * 3,
    source_labels_nonoverlap: native.labelRects.vertical_overlap_pixels === 0,
    native_reference_uncropped: native.cropped === 'false',
    native_reference_is_independent_and_unregistered: /independent of the published MRI cases/.test(native.note)
      && /registration are unverified/.test(native.note),
    native_reference: { meshes: native.meshes, triangles: native.triangles, cropped: native.cropped,
      native_y_up: NATIVE_Y_UP, draw_calls: drawn, labelRects: native.labelRects,
      orientation: native.orientation, bodyWidth: native.bodyWidth, note: native.note },
    mesh_hashes_match_manifest: meshResponses.length === native.meshes && meshResponses.every(m => m.matches_manifest),
    figure_checks: figureChecks, enlarged, image_responses: imageResponses, mesh_responses: meshResponses,
    screenshots: shots, page_errors: pageErrors, failed_requests: failed, horizontal_overflow: horizontal,
    horizontal_overflow_at: overflows,
    held_remote_images: heldRemote, served_app_js_sha256: servedAppJs, served_detailed_anatomy_js_sha256: servedAnatomyJs,
  });
  return result;
}

function passed(result) {
  return result['complete_' + name + '_figure_count'] === contract.length
    && result.all_native_image_response_hashes_match && result.source_case_modality_staging_limits_visible
    && result.enlarged_originals_and_native_size_control_verified && result.no_held_remote_ra_images
    && (!config.heading || result.book_heading_preserves_figure_3_1)
    && result.native_reference_viewer_count === 1 && result.native_reference_mesh_count === config.meshes
    && result.all54_source_objects_GPU_drawn && result.source_labels_nonoverlap
    && result.native_reference_uncropped && result.native_reference_is_independent_and_unregistered
    && result.mesh_hashes_match_manifest
    && result.page_errors.length === 0 && result.failed_requests.length === 0 && !result.horizontal_overflow
    && result.served_app_js_sha256 === appJsSha && result.served_detailed_anatomy_js_sha256 === anatomyJsSha
    && (result.route !== 'reporting' || (result.assessment_step_count === config.steps
      && result.only_source_matched_step_images && result.assessment_prompts_do_not_assert_normality
      && result.assessment.assembled_report_has_all_sections));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const route of ['reporting', 'lesson'].filter(r => !only || r === only)) for (const width of [1440, 390]) {
      console.log('Reviewing ' + name + ' ' + route + ' at ' + width + 'px');
      results.push(await review(browser, route, width));
    }
  } finally {
    await browser.close();
  }
  const record = {
    reviewed_on: new Date().toISOString().slice(0, 10),
    qa_only_server: base,
    owned_isolated_qa_server: true,
    browser_session: 'tools/check_source_review_browser.cjs ' + name + ' · headless Chromium (Playwright)',
    all_requested_routes_and_viewports_passed: results.every(passed),
    app_js_sha256: appJsSha,
    detailed_anatomy_js_sha256: anatomyJsSha,
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
      + result['complete_' + name + '_figure_count'] + ' figures · ' + result.native_reference_mesh_count + ' meshes · '
      + result.native_reference.draw_calls.length + ' draw calls');
  }
  console.log('REVIEW=' + path.join(out, 'review.json'));
  if (!record.all_requested_routes_and_viewports_passed) process.exitCode = 1;
})().catch(error => { console.error(error); process.exitCode = 1; });
