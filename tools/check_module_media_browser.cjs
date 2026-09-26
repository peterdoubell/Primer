#!/usr/bin/env node
'use strict';

// Run only against an isolated QA server: this creates a test learner.
// NODE_PATH=/path/to/node_modules node tools/check_module_media_browser.cjs URL
// Evidence uses a fresh private temporary directory; printed as EVIDENCE_DIRECTORY.
// Legacy output-directory argument (slot 3) is ignored; see docs/browser-qa.md.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const { createEvidenceDirectory, loopbackQaUrl } = require('./qa-browser.cjs');
const base = loopbackQaUrl(process.argv[2]);
const output = createEvidenceDirectory();
const galleryOnly = process.argv[4] === '--gallery-only';
const root = path.resolve(__dirname, '..');
const authored = fs.readdirSync(path.join(root, 'data/curriculum'))
  .filter(name => /^\d.*\.json$/.test(name))
  .flatMap(name => {
    const domain = JSON.parse(fs.readFileSync(path.join(root, 'data/curriculum', name)));
    return domain.nodes.map(node => ({ ...node, domain: domain.id }));
  });
const spatial = item => ['spatial-3d', 'radiology-anatomy'].includes(item.renderer);
const hash = buffer => createHash('sha256').update(buffer).digest('hex');


(async () => {
  const browser = await chromium.launch({ headless: true });
  const evidence = { checks: [], lessons: [], errors: [] };
  try {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce', hasTouch: true,
    });
    const profile = await context.request.post(base + '/api/profile', { data: {
      name: 'Module media browser QA', age: 35, hours_per_week: 3,
      breadth: 'balanced', domains: [],
    } });
    assert.equal(profile.status(), 200, 'Isolated QA learner is available');
    await context.request.post(base + '/api/profile/settings', { data: { speak: false } });
    const galleryResponse = await context.request.get(base + '/api/curriculum/visuals');
    assert.equal(galleryResponse.status(), 200);
    const gallery = await galleryResponse.json();
    const plates = gallery.items.filter(item => item.kind === 'illustration');
    const models = gallery.items.filter(spatial);
    const ids = new Set(authored.map(node => node.id));
    assert.equal(authored.length, 558, 'Full Primer lesson count');
    assert.equal(gallery.domains.length, 19, 'Full Primer subject count');
    assert.ok(!gallery.items.some(item => !['illustration', 'model'].includes(item.kind)), 'Only lesson plates and models');
    assert.equal(gallery.counts.illustrations, plates.length, 'Gallery illustration count matches records');
    for (const id of ids) {
      assert.ok(plates.some(item => item.lesson_id === id), id + ': at least one lesson illustration');
      assert.ok(models.some(item => item.lesson_id === id), id + ': at least one interactive 3D model');
    }
    evidence.coverage = { lessons: ids.size, subjects: gallery.domains.length,
      illustrations: plates.length, spatialModels: models.length };
    evidence.sourceHashes = {};
    for (const file of ['app.js', 'styles.css', 'spatial-module-objects.js', 'lesson-models.js']) {
      const response = await context.request.get(base + '/app/' + file);
      assert.equal(response.status(), 200, file + ' is served');
      const digest = hash(await response.body());
      assert.equal(digest, hash(fs.readFileSync(path.join(root, 'web', file))), file + ' matches workspace');
      evidence.sourceHashes[file] = digest;
    }
    const page = await context.newPage();
    const touch = await context.newCDPSession(page);
    page.setDefaultTimeout(30000);
    page.on('pageerror', error => evidence.errors.push(error.message));
    await page.goto(base + '/#/math-images');
    const kind = page.getByRole('combobox', { name: 'Kind', exact: true });
    assert.equal(await kind.locator('option[value="photograph"]').count(), 0, 'No photorealistic scene filter');
    await kind.selectOption('illustration');
    await page.waitForFunction(count => document.querySelector('.math-gallery-live')?.textContent
      .startsWith('Showing ' + count + ' of ' + count + ' illustrations'), plates.length);
    assert.equal(await page.locator('.math-image-card:not([hidden])').count(), plates.length);
    assert.equal(await page.locator('.math-image-card:not([hidden]) img[loading="lazy"]').count(), plates.length);
    // One plate per subject, at every published resolution, decodes.
    const sample = gallery.domains.map(domain => plates.find(item => item.domain === domain.id)).filter(Boolean);
    const sources = [...new Set(sample.flatMap(item => [item.src,
      ...String(item.srcset || '').split(',').map(part => part.trim().split(/\s+/)[0])]).filter(Boolean))];
    const decoded = await page.evaluate(async sources => Promise.all(sources.map(async src => {
      const image = new Image();
      image.src = src;
      await image.decode();
      return { src, width: image.naturalWidth, height: image.naturalHeight };
    })), sources);
    assert.ok(decoded.every(image => image.width > 0 && image.height > 0), 'Every sampled plate resolution decodes');
    evidence.decodedPlates = decoded;
    await page.getByRole('searchbox').fill('fractions');
    const found = await page.locator('.math-image-card:not([hidden])').count();
    assert.ok(found > 0 && found < plates.length, 'Search filters lesson plates');
    await page.getByRole('searchbox').fill('');
    await page.screenshot({ path: path.join(output, 'illustration-gallery-desktop.png'), animations: 'disabled' });
    await kind.selectOption('spatial-3d');
    assert.equal(await page.locator('.math-image-card:not([hidden])').count(), models.length);
    await page.setViewportSize({ width: 390, height: 844 });
    await kind.selectOption('illustration');
    await assertNoOverflow('Gallery mobile');
    await page.screenshot({ path: path.join(output, 'illustration-gallery-mobile.png'), animations: 'disabled' });
    evidence.checks.push('Gallery illustration/3D filters, search, lazy loading and mobile layout');
    if (galleryOnly) {
      assert.deepEqual(evidence.errors, [], 'No uncaught browser exceptions');
      fs.writeFileSync(path.join(output, 'gallery-evidence.json'), JSON.stringify(evidence, null, 2) + '\n');
      console.log('PASS gallery coverage: ' + JSON.stringify(evidence.coverage));
      return;
    }

    // Each subject plus each shared new spatial scenario gets a real lesson
    // route. Distinct lesson-specific existing scenarios remain covered by the
    // dedicated spatial suite; repeated new families only need one interaction.
    const selected = new Map();
    for (const domain of gallery.domains) {
      const node = authored.find(node => node.domain === domain.id);
      selected.set(node.id, node);
    }
    const families = new Set();
    const existingSpatialIds = new Set();
    for (const node of authored) for (const item of node.lesson_media || []) {
      if (item.renderer === 'spatial-3d') {
        selected.set(node.id, node);
        existingSpatialIds.add(node.id);
      }
    }
    const bindings = JSON.parse(fs.readFileSync(path.join(root, 'data/module-models.json'))).models;
    for (const binding of bindings) {
      if (existingSpatialIds.has(binding.node_id) || families.has(binding.family)) continue;
      const node = authored.find(node => node.id === binding.node_id);
      assert.ok(node, 'New 3D family has a real lesson: ' + binding.family);
      families.add(binding.family);
      selected.set(node.id, { ...node, qaFamily: binding.family, qaScenario: 'module.' + node.id });
    }
    evidence.newSpatialFamilies = [...families];
    let pointerDragVerified = false;
    let touchDragVerified = false;
    for (const node of selected.values()) {
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.goto(base + '/#/node/' + encodeURIComponent(node.id));
      await page.waitForFunction(title => document.querySelector('.pagehead h2')?.textContent === title, node.title);
      assert.equal(await page.locator('.lesson-photograph').count(), 0, node.id + ': no photorealistic scene');
      const plate = page.locator('.lesson-media > .lesson-illustration img').first();
      await plate.waitFor();
      await plate.scrollIntoViewIfNeeded();
      await plate.evaluate(image => image.decode());
      assert.equal(await plate.getAttribute('loading'), 'eager', node.id + ': leading plate loads eagerly');
      assert.equal(await plate.getAttribute('role'), 'button', node.id + ': image is keyboard accessible');
      assert.ok((await plate.getAttribute('aria-label') || '').trim(), node.id + ': image has an accessible name');
      const laterImages = await page.locator('.lesson-media > .lesson-illustration img').evaluateAll(images => images.slice(1).map(image => image.loading));
      assert.ok(laterImages.every(value => value === 'lazy'), node.id + ': lower lesson images load lazily');
      await plate.focus();
      await page.keyboard.press('Enter');
      const dialog = page.getByRole('dialog');
      await dialog.waitFor();
      await dialog.locator('.lightbox img').evaluate(image => image.decode());
      await dialog.getByRole('button', { name: 'Read labels at full size', exact: true }).click();
      assert.equal(await dialog.locator('.lightbox-zoom').getAttribute('aria-pressed'), 'true');
      await page.keyboard.press('Escape');
      await dialog.waitFor({ state: 'hidden' });
      assert.ok(await plate.evaluate(image => document.activeElement === image), node.id + ': Escape restores image focus');

      const model = page.locator(node.qaScenario
        ? '.spatial-model[data-scenario="' + node.qaScenario + '"]' : '.spatial-model').first();
      let scenario = null;
      if (await model.count()) {
        await model.waitFor();
        scenario = await model.getAttribute('data-scenario');
        const snapshot = () => model.evaluate(element => ({
          view: element.dataset.view, geometry: element.querySelector('svg g').innerHTML,
          readout: element.querySelector('.spatial-readout').textContent,
          state: [...element.querySelectorAll('[data-parameter]')].map(input => [input.dataset.parameter, input.value]),
        }));
        const before = await snapshot();
        const controls = await model.locator('[data-parameter]').evaluateAll(inputs => inputs.map(input => ({
          key: input.dataset.parameter,
          value: input.tagName === 'SELECT' ? [...input.options].find(option => option.value !== input.value)?.value
            : input.value === input.max ? input.min : input.max,
        })));
        assert.ok(controls.length, node.id + ': interactive model parameters');
        for (const control of controls) {
          await model.locator('[data-parameter="' + control.key + '"]').evaluate((input, value) => {
            input.value = value;
            input.dispatchEvent(new Event(input.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true }));
          }, control.value);
          const changed = await snapshot();
          assert.notDeepEqual(changed, before, node.id + ': ' + control.key + ' updates model');
          assert.ok(!/NaN|Infinity/.test(changed.geometry), node.id + ': finite projected geometry');
          await model.getByRole('button', { name: 'Reset model', exact: true }).click();
          assert.deepEqual(await snapshot(), before, node.id + ': exact parameter reset');
        }
        await model.getByRole('button', { name: 'Rotate right', exact: true }).click();
        assert.notEqual((await snapshot()).geometry, before.geometry, node.id + ': rotation changes projection');
        await model.getByRole('button', { name: 'Reset view', exact: true }).click();
        assert.deepEqual(await snapshot(), before, node.id + ': exact camera reset');
        await model.locator('.spatial-svg').focus();
        await page.keyboard.press('ArrowLeft');
        assert.notEqual((await snapshot()).view, before.view, node.id + ': keyboard rotation');
        await page.keyboard.press('Home');
        assert.deepEqual(await snapshot(), before, node.id + ': keyboard reset');
        if (!pointerDragVerified && scenario.startsWith('module.')) {
          const svg = model.locator('.spatial-svg');
          await svg.scrollIntoViewIfNeeded();
          const box = await svg.boundingBox();
          await page.mouse.move(box.x + box.width * .45, box.y + box.height * .45);
          await page.mouse.down();
          await page.mouse.move(box.x + box.width * .62, box.y + box.height * .58, { steps: 6 });
          await page.mouse.up();
          assert.notEqual((await snapshot()).geometry, before.geometry, node.id + ': real pointer drag changes projection');
          await model.getByRole('button', { name: 'Reset view', exact: true }).click();
          assert.deepEqual(await snapshot(), before, node.id + ': pointer drag resets');
          pointerDragVerified = true;
          evidence.checks.push('Real mouse drag and reset: ' + node.id);
        }
        await model.locator('.spatial-canvas').screenshot({ path: path.join(output, node.id + '-model-desktop.png') });
      } else {
        const anatomy = page.locator('.detailed-anatomy');
        await anatomy.waitFor();
        await page.waitForFunction(() => document.querySelector('.detailed-anatomy')?.dataset.ready === 'true');
        assert.ok(Number(await anatomy.getAttribute('data-triangles')) > 0, node.id + ': detailed anatomical meshes loaded');
      }
      await page.setViewportSize({ width: 390, height: 844 });
      await assertNoOverflow(node.id + ' mobile');
      await plate.scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(output, node.id + '-plate-mobile.png'), animations: 'disabled' });
      if (await model.count()) {
        await model.locator('.spatial-canvas').screenshot({ path: path.join(output, node.id + '-model-mobile.png') });
        await assertNoOverflow(node.id + ' mobile model');
        if (!touchDragVerified && scenario.startsWith('module.')) {
          const svg = model.locator('.spatial-svg');
          await svg.scrollIntoViewIfNeeded();
          const box = await svg.boundingBox();
          const beforeTouch = await model.getAttribute('data-view');
          const point = { x: box.x + box.width * .4, y: box.y + box.height * .45 };
          await touch.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [point] });
          await touch.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: point.x + 40, y: point.y + 25 }] });
          await touch.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
          assert.notEqual(await model.getAttribute('data-view'), beforeTouch, node.id + ': real touch drag rotates at 390px');
          await model.getByRole('button', { name: 'Reset view', exact: true }).click();
          assert.equal(await model.getAttribute('data-view'), beforeTouch, node.id + ': touch drag resets');
          touchDragVerified = true;
          evidence.checks.push('Real mobile touch drag and reset: ' + node.id);
        }
      }
      evidence.lessons.push({ id: node.id, domain: node.domain, scenario, family: node.qaFamily });
      console.log('PASS ' + node.id + ': plate, zoom, 3D, mobile' + (scenario ? ' (' + scenario + ')' : ''));
    }
    assert.ok(pointerDragVerified && touchDragVerified, 'Mouse and touch model rotation were exercised');
    // The separate reporting workspace has its own lazy-built Images panel.
    const radiologyCatalog = await (await context.request.get(base + '/api/radiology/modules')).json();
    await page.goto(base + '/#/radiology/' + radiologyCatalog.modules[0].id);
    await page.getByRole('tab', { name: /^Images \(/ }).click();
    await page.locator('.rad-desk-panel:not([hidden]) .rad-key-images').waitFor();
    assert.equal(await page.locator('.rad-desk-panel:not([hidden]) .lesson-photograph').count(), 0, 'No photorealistic scene on the Images tab');
    await assertNoOverflow('Radiology image tab mobile');
    await page.getByRole('tab', { name: /3D anatomy|Spatial guide/ }).click();
    assert.ok(await page.locator('.rad-desk-panel:not([hidden]) .detailed-anatomy, .rad-desk-panel:not([hidden]) .spatial-model').count() >= 1);
    assert.ok(await page.locator('.rad-desk-panel:not([hidden]) .detailed-anatomy').count() <= 1, 'Radiology anatomy is not duplicated');
    evidence.checks.push('Radiology Images tab without scenes and nonduplicated 3D anatomy');
    assert.deepEqual(evidence.errors, [], 'No uncaught browser exceptions');
    fs.writeFileSync(path.join(output, 'evidence.json'), JSON.stringify(evidence, null, 2) + '\n');
    console.log('PASS all-module coverage: ' + JSON.stringify(evidence.coverage));

    async function assertNoOverflow(label) {
      const bounds = await page.evaluate(() => ({
        viewport: innerWidth, document: document.documentElement.scrollWidth,
        overflowing: [...document.querySelectorAll('.lesson-media, .lesson-illustration, .spatial-model, .math-gallery-overview')]
          .filter(element => element.getBoundingClientRect().width && element.scrollWidth > element.clientWidth + 1)
          .map(element => element.className),
      }));
      assert.ok(bounds.document <= bounds.viewport + 1, label + ': page fits viewport ' + JSON.stringify(bounds));
      assert.deepEqual(bounds.overflowing, [], label + ': media fits container');
    }
  } catch (error) {
    evidence.failure = String(error.stack || error);
    fs.writeFileSync(path.join(output, 'failure.json'), JSON.stringify(evidence, null, 2) + '\n');
    throw error;
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
