#!/usr/bin/env node
'use strict';

// An isolated loopback server is required; this creates a disposable QA learner.
// NODE_PATH=/path/to/node_modules node tools/check_mri_knee.cjs http://127.0.0.1:8782
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const { createEvidenceDirectory, loopbackQaUrl } = require('./qa-browser.cjs');
const base = loopbackQaUrl(process.argv[2]);
const out = createEvidenceDirectory();
const root = path.resolve(__dirname, '..');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'web/anatomy/msk-mri-knee/manifest.json')));
const region = manifest.regions.knee;
const sourceParts = region.parts.map(part => ({ ...manifest.parts[part.id], ...part }));
// Combined author labels remain provenance records; their complete native
// disconnected children replace them in the display, never overlay them.
const parts = sourceParts.flatMap(part => part.components?.length ? part.components : [part]);
const byId = new Map(parts.map(part => [part.id, part]));
const combinedParents = sourceParts.filter(part => part.components?.length);
const parentFiles = new Set(combinedParents.map(part => part.file));
assert.equal(sourceParts.length, 28);
assert.equal(parts.length, 30);
assert.equal(byId.size, 30, 'Every displayed component has a unique selectable ID');
assert.equal(parts.reduce((sum, part) => sum + part.triangles, 0),
  sourceParts.reduce((sum, part) => sum + part.triangles, 0), 'Exact component split preserves all source triangles');
for (const parent of combinedParents) {
  const children = [...parent.components].sort((a, b) => a.bounds[0][0] - b.bounds[0][0]);
  assert.equal(children.length, 2);
  assert.ok(children[0].bounds[1][0] < children[1].bounds[0][0], parent.id + ': native right LPS component X extents do not overlap');
}
const byFile = new Map(parts.map(part => [part.file, part]));
const sha = data => createHash('sha256').update(data).digest('hex');
const evidence = { status: 'running', sourceHashes: {}, initial: {}, layers: [], isolated: [], transport: [], clinicalFigures: [],
  errors: [], failedAssets: [],
  qualification: 'Browser rendering/transport QA, not clinical certification. Published comparison figures are separate examinations, not registered validation images from this segmented subject. Combined source labels are displayed as exact disconnected components identified by native right-sided LPS position; roots, horns and attachments remain unsegmented and smaller structures are omitted.',
};

(async () => {
  const browser = await chromium.launch({ headless: true });
  let page;
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1080 }, reducedMotion: 'reduce', hasTouch: true });
    assert.equal((await context.request.post(base + '/api/profile', { data: {
      name: 'MRI knee browser QA', age: 35, hours_per_week: 3, breadth: 'balanced', domains: ['radiology'],
    } })).status(), 200);
    await context.request.post(base + '/api/profile/settings', { data: { speak: false } });
    const sourceFiles = ['app.js', 'styles.css', 'radiology-detailed-anatomy.js', 'anatomy/msk-mri-knee/manifest.json'];
    for (const file of sourceFiles) {
      const response = await context.request.get(base + '/app/' + file);
      assert.equal(response.status(), 200, file + ': HTTP source');
      const hash = sha(await response.body());
      assert.equal(hash, sha(fs.readFileSync(path.join(root, 'web', file))), file + ': source matches workspace');
      evidence.sourceHashes[file] = hash;
    }
    const detail = await (await context.request.get(base + '/api/radiology/modules/ra.mri-knee')).json();
    const requested = [], zRequested = [], combinedRequested = [], transportTasks = [], transportErrors = [];
    page = await context.newPage();
    page.setDefaultTimeout(60000);
    page.on('pageerror', error => evidence.errors.push(error.message));
    page.on('request', request => {
      const pathname = new URL(request.url()).pathname;
      if (byFile.has(pathname)) requested.push(pathname);
      if (parentFiles.has(pathname)) combinedRequested.push(pathname);
      if (pathname.startsWith('/app/anatomy/msk-atlas/') && pathname.endsWith('.bin')) zRequested.push(pathname);
    });
    page.on('response', response => {
      const pathname = new URL(response.url()).pathname, part = byFile.get(pathname);
      if (!part) return;
      const task = (async () => {
        assert.equal(response.status(), 200, part.id + ': encoded asset HTTP status');
        const headers = await response.allHeaders();
        assert.equal(headers['content-encoding'], 'gzip', part.id + ': HTTP gzip metadata');
        assert.equal(headers['content-type'], 'application/octet-stream', part.id + ': binary MIME');
        const decoded = await response.body();
        assert.equal(decoded.readUInt32LE(0), 0x44335042, part.id + ': browser transparently decompresses BP3D header');
        assert.equal(decoded.length, part.decoded_bytes, part.id + ': decoded byte length');
        assert.equal(decoded.readUInt32LE(4), part.vertices, part.id + ': decoded vertex count');
        assert.equal(decoded.readUInt32LE(8), part.triangles * 3, part.id + ': decoded index count');
        assert.equal(sha(decoded), part.decoded_sha256, part.id + ': exact decoded checksum');
        evidence.transport.push({ id: part.id, encoding: headers['content-encoding'], encodedBytes: part.bytes,
          decodedBytes: decoded.length, decodedSha256: part.decoded_sha256 });
      })().catch(error => transportErrors.push(String(error.stack || error)));
      transportTasks.push(task);
    });
    await page.goto(base + '/#/radiology/ra.mri-knee');
    await page.locator('.rad-reporting-desk').waitFor();
    await page.getByRole('tab', { name: '3D anatomy', exact: true }).click();
    const selector = page.getByRole('combobox', { name: 'Knee anatomy source', exact: true });
    assert.equal(await selector.inputValue(), 'malaya-mri', 'MRI source is the actual default');
    const model = page.locator('.rad-desk-panel:not([hidden]) .detailed-anatomy');
    await ready('malaya-mri');
    assert.equal(Number(await model.getAttribute('data-meshes')), 30, '28 source labels expand to 30 displayed objects');
    assert.equal(Number(await model.getAttribute('data-triangles')), sourceParts.reduce((sum, part) => sum + part.triangles, 0), 'No duplicate parent triangles are rendered');
    assert.deepEqual(await model.locator('[data-part]').evaluateAll(nodes => nodes.map(node => node.dataset.part).sort()), parts.map(part => part.id).sort(), 'Component controls replace both combined parent controls');
    assert.equal(await model.locator('[data-part]:visible').count(), parts.filter(part => part.layer === 'bone').length);
    const initialPaths = [...new Set(requested)].sort();
    assert.deepEqual(initialPaths, parts.filter(part => part.layer === 'bone').map(part => part.file).sort(), 'Initial rendering requests bones only');
    assert.deepEqual(zRequested, [], 'No Z-Anatomy geometry fetched into the MRI default');
    await Promise.all(transportTasks); assert.deepEqual(transportErrors, []);
    evidence.initial = { requested: initialPaths, boneObjects: initialPaths.length,
      encodedBytes: initialPaths.reduce((sum, file) => sum + byFile.get(file).bytes, 0), nonBoneRequests: 0, zAnatomyRequests: 0 };
    const notes = await model.locator('.detailed-anatomy-note').textContent();
    for (const text of ['MRI-derived right-knee', 'native LPS millimeter', 'not fitted', 'complete disconnected medial/lateral components', 'native right-sided LPS positions', 'No roots, horns, attachments or cartilage sublayers are independently segmented', '1.154', 'independent clinical fidelity review', 'CC0 1.0'])
      assert.ok(notes.includes(text), 'Visible provenance/limitation: ' + text);
    assert.equal(await model.getByRole('link', { name: manifest.dataset, exact: true }).getAttribute('href'), manifest.source_url);
    assert.equal(await model.getByRole('link', { name: manifest.license, exact: true }).getAttribute('href'), manifest.license_url);
    await capture('default-desktop');
    const loadedLayers = new Set(['bone']);
    for (const [layer, label] of region.layers) {
      const prior = new Set(requested);
      await chooseLayer(layer, label);
      loadedLayers.add(layer);
      const expectedIds = parts.filter(part => part.layer === layer).map(part => part.id).sort();
      assert.deepEqual(await model.locator('[data-part]:visible').evaluateAll(nodes => nodes.map(node => node.dataset.part).sort()), expectedIds);
      assert.ok(requested.every(file => loadedLayers.has(byFile.get(file).layer)), layer + ': no unselected layer downloaded early');
      const pixels = await pixelStats();
      evidence.layers.push({ layer, label, objects: expectedIds.length, requestsAdded: [...new Set(requested)].filter(file => !prior.has(file)), ...pixels });
      await capture('layer-' + layer + '-desktop');
      if (layer === 'cartilage') {
        await model.getByRole('button', { name: 'Superior', exact: true }).click(); await settled();
        await capture('cartilage-volumes-superior');
        assert.equal(await model.locator('.detailed-anatomy-orientation').textContent(), 'Right side · Superior');
        await model.getByRole('button', { name: 'Anterior', exact: true }).click(); await settled();
      }
    }
    await Promise.all(transportTasks); assert.deepEqual(transportErrors, []);
    assert.deepEqual([...new Set(requested)].sort(), parts.map(part => part.file).sort(), 'All 30 displayed source objects fetched through selected layers');
    assert.equal(new Set(evidence.transport.map(part => part.id)).size, 30, 'All 30 compressed HTTP responses decoded and hashed');
    assert.deepEqual(zRequested, [], 'All MRI layers remain in one unmixed source coordinate frame');
    assert.deepEqual(combinedRequested, [], 'Combined parent transports are not requested or drawn alongside their children');
    evidence.componentReconciliation = { originalSourceLabels: sourceParts.length, displayedObjects: parts.length,
      trianglesPreserved: Number(await model.getAttribute('data-triangles')), combinedParentsRequested: 0,
      sourceLabels: combinedParents.map(part => ({ id: part.id, children: part.components.map(child => ({ id: child.id, bounds: child.bounds, triangles: child.triangles })) })) };
    await chooseLayer('all', 'Together');
    await capture('together-desktop');
    const beforeFull = await model.locator('canvas').evaluate(canvas => canvas.toDataURL());
    await model.getByRole('button', { name: 'Full structures', exact: true }).click(); await settled();
    assert.equal(await model.locator('canvas').getAttribute('data-cropped'), 'false');
    assert.notEqual(await model.locator('canvas').evaluate(canvas => canvas.toDataURL()), beforeFull, 'Full structures changes the clipped regional view');
    await pixelStats(); await capture('full-structures-desktop');
    await model.getByRole('button', { name: 'Reset', exact: true }).click(); await settled();
    for (const id of ['um-knee-cartilage-femur-distal', 'um-knee-cartilage-patella',
      'um-knee-medial-tibial-plateau-cartilage', 'um-knee-lateral-tibial-plateau-cartilage',
      'um-knee-medial-meniscus', 'um-knee-lateral-meniscus', 'um-knee-ligament-acl', 'um-knee-ligament-pcl']) {
      const part = byId.get(id), layerLabel = region.layers.find(layer => layer[0] === part.layer)[1];
      await chooseLayer(part.layer, layerLabel);
      await model.locator('[data-part="' + id + '"]').focus();
      await page.keyboard.press('Enter');
      await model.getByRole('button', { name: 'Isolate', exact: true }).click(); await settled();
      assert.equal(await model.locator('canvas').getAttribute('data-cropped'), 'false');
      assert.equal(await model.getByRole('button', { name: 'Isolate', exact: true }).getAttribute('aria-pressed'), 'true');
      assert.equal(await model.locator('.detailed-anatomy-selected').textContent(), part.name);
      assert.equal(await model.locator('[data-part][aria-pressed="true"]').count(), 1, 'Exactly one source component selected');
      assert.equal(await model.locator('.detailed-anatomy-crop-status').textContent(), 'Uncropped source');
      const pixels = await pixelStats();
      evidence.isolated.push({ id, name: part.name, triangles: part.triangles, sourceVolume: part.volume_native_units_cubed, ...pixels });
      await capture('isolated-' + id + '-desktop');
      await model.getByRole('button', { name: 'Superior', exact: true }).click(); await settled();
      await capture('isolated-' + id + '-superior');
      await page.setViewportSize({ width: 390, height: 844 }); await settled(); await noOverflow();
      await pixelStats(); await capture('isolated-' + id + '-mobile');
      await page.setViewportSize({ width: 1440, height: 1080 });
      await model.getByRole('button', { name: 'Reset', exact: true }).click(); await settled();
    }
    for (const parent of combinedParents) {
      const renders = parent.components.map(part => evidence.isolated.find(item => item.id === part.id));
      assert.equal(renders.length, 2);
      assert.notEqual(renders[0].projectionSha256, renders[1].projectionSha256, parent.id + ': medial/lateral component isolation renders are distinct');
    }
    await chooseLayer('all', 'Together');
    await model.locator('[data-part="um-knee-cartilage-femur-distal"]').click(); await settled();
    await capture('femoral-cartilage-in-source-context');
    await page.setViewportSize({ width: 390, height: 844 }); await settled(); await noOverflow();
    await capture('cartilage-context-mobile');

    // Observe the detached canvas to prove GPU context disposal, not merely
    // that the selector's label changed while both providers remain mounted.
    const oldMRI = await model.locator('canvas').elementHandle();
    await selector.selectOption('z-anatomy'); await ready('z-anatomy');
    await page.waitForFunction(canvas => !canvas.isConnected && canvas.getContext('webgl').isContextLost(), oldMRI);
    assert.equal(await page.locator('.rad-anatomy-model-host .detailed-anatomy').count(), 1);
    assert.ok((await model.locator('[data-part]').evaluateAll(nodes => nodes.map(node => node.dataset.part))).every(id => id.startsWith('za-')));
    await capture('broader-source-mobile'); await noOverflow();
    const oldZ = await model.locator('canvas').elementHandle();
    await selector.selectOption('malaya-mri'); await ready('malaya-mri');
    await page.waitForFunction(canvas => !canvas.isConnected && canvas.getContext('webgl').isContextLost(), oldZ);
    assert.equal(await page.locator('.rad-anatomy-model-host .detailed-anatomy').count(), 1);
    assert.ok((await model.locator('[data-part]').evaluateAll(nodes => nodes.map(node => node.dataset.part))).every(id => id.startsWith('um-knee-')));
    assert.equal(await model.locator('canvas').getAttribute('data-layer'), 'bone');
    evidence.sourceSwitch = { mriDisposed: true, zAnatomyDisposed: true, singleMountedProvider: true, mixedParts: false, resetToBones: true };
    await capture('mri-source-return-mobile');

    // Keep comparison figures separate: these are the published clinical
    // examples in this lesson, not a registered scan of the model's subject.
    await page.getByRole('tab', { name: /^Images \(/ }).click();
    const clinical = (detail.radiology_reference.structure_atlas || []).filter(asset => asset.kind === 'clinical-image');
    assert.ok(clinical.length, 'Clinical anatomy comparison figures are available');
    for (const asset of clinical) {
      const image = page.locator('.rad-desk-panel:not([hidden]) .rad-structure-atlas img[src="' + asset.src + '"]');
      assert.ok(asset.modality, 'Clinical comparison modality is explicit');
      assert.equal(await image.locator('..').locator('h4').textContent(), 'Figure ' + asset.figure_number + (asset.source_panel || '') + ' · ' + asset.modality + (asset.contains_schematic_panels ? ' + schematic panels' : ''));
      await image.scrollIntoViewIfNeeded(); await image.evaluate(image => image.decode());
      await noOverflow();
      await page.screenshot({ path: path.join(out, 'clinical-comparison-' + asset.id + '-mobile.png'), animations: 'disabled' });
      await page.setViewportSize({ width: 1440, height: 1080 }); await image.scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(out, 'clinical-comparison-' + asset.id + '-desktop.png'), animations: 'disabled' });
      evidence.clinicalFigures.push({ id: asset.id, src: asset.src, modality: asset.modality, sourceUrl: asset.source_url, limits: asset.limits,
        interpretation: 'Separate published anatomical reference; no same-subject registration or geometric validation claimed.' });
      await page.setViewportSize({ width: 390, height: 844 });
    }
    await Promise.all(transportTasks); assert.deepEqual(transportErrors, []);
    assert.deepEqual(evidence.errors, [], 'No uncaught browser exceptions');
    for (const file of sourceFiles) assert.equal(sha(fs.readFileSync(path.join(root, 'web', file))), evidence.sourceHashes[file], file + ': frozen source during QA');
    evidence.status = 'passed';
    fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(evidence, null, 2) + '\n');
    console.log('PASS MRI knee: 4 bone-only initial requests; 30 gzip transports decoded and hashed; 6 layers; 8 isolated cartilage/meniscus/cruciate objects; source-switch disposal and mobile. Evidence: ' + out);

    async function settled() { await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))); }
    async function ready(atlas) {
      await page.waitForFunction(atlas => { const element = document.querySelector('.rad-desk-panel:not([hidden]) .detailed-anatomy');
        if (element?.dataset.error) throw new Error(element.querySelector('.detailed-anatomy-status').textContent);
        return element?.dataset.atlas === atlas && element.dataset.ready === 'true' && element.querySelector('canvas')?.dataset.rendered === 'true';
      }, atlas, { timeout: 120000 });
      await settled();
    }
    async function chooseLayer(layer, label) {
      await model.getByRole('button', { name: label, exact: true }).click();
      await page.waitForFunction(layer => document.querySelector('.rad-desk-panel:not([hidden]) .detailed-anatomy canvas')?.dataset.layer === layer, layer, { timeout: 120000 });
      await settled();
    }
    async function pixelStats() {
      await settled();
      const pixels = await model.locator('canvas').evaluate(canvas => {
        const gl = canvas.getContext('webgl'), data = new Uint8Array(canvas.width * canvas.height * 4);
        gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, data);
        let count = 0; for (let i = 3; i < data.length; i += 4) if (data[i] > 20) count++;
        return { pixels: count, glError: gl.getError(), width: canvas.width, height: canvas.height, view: canvas.dataset.view };
      });
      assert.equal(pixels.glError, 0); assert.ok(pixels.pixels > 100, 'Visible MRI-derived geometry: ' + JSON.stringify(pixels));
      return { ...pixels, projectionSha256: sha(await model.locator('canvas').evaluate(canvas => canvas.toDataURL())) };
    }
    async function capture(name) {
      await model.locator('.detailed-anatomy-stage').evaluate(element => element.scrollIntoView({ block: 'center', behavior: 'instant' }));
      await settled();
      await page.screenshot({ path: path.join(out, name + '.png'), animations: 'disabled', timeout: 30000 });
    }
    async function noOverflow() {
      const dimensions = await page.evaluate(() => ({ viewport: innerWidth, page: document.documentElement.scrollWidth,
        overflow: [...document.querySelectorAll('.detailed-anatomy, .rad-structure-atlas')].filter(element => element.getBoundingClientRect().width && element.scrollWidth > element.clientWidth + 1).map(element => element.className) }));
      assert.ok(dimensions.page <= dimensions.viewport + 1 && !dimensions.overflow.length, JSON.stringify(dimensions));
    }
  } catch (error) {
    evidence.status = 'failed'; evidence.failure = String(error.stack || error);
    if (page) await page.screenshot({ path: path.join(out, 'failure.png') }).catch(() => {});
    fs.writeFileSync(path.join(out, 'failure.json'), JSON.stringify(evidence, null, 2) + '\n');
    throw error;
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
