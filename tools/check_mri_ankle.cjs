#!/usr/bin/env node
'use strict';

// NODE_PATH=/path/to/node_modules node tools/check_mri_ankle.cjs http://127.0.0.1:8783
// Creates a QA learner only on a validated loopback origin; evidence is private.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const { createEvidenceDirectory, loopbackQaUrl } = require('./qa-browser.cjs');
const base = loopbackQaUrl(process.argv[2]);
const out = createEvidenceDirectory();
const root = path.resolve(__dirname, '..');
const read = file => JSON.parse(fs.readFileSync(path.join(root, file)));
const manifest = read('web/anatomy/msk-mri-ankle/manifest.json');
const knee = read('web/anatomy/msk-mri-knee/manifest.json');
const region = manifest.regions.ankle;
const parts = region.parts.map(part => ({ ...manifest.parts[part.id], ...part }));
const byFile = new Map(parts.map(part => [part.file, part]));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const evidence = { status: 'running', sourceHashes: {}, sharedResources: [], initial: {}, layers: [], transport: [], screenshots: [], errors: [],
  qualification: 'Engineering and visual QA only. This subset omits ankle ligaments, cartilage, nerves, vessels, bursae and separately labelled distal tendons other than Achilles. No clinical certification or complete reporting coverage is asserted.',
};

(async () => {
  const browser = await chromium.launch({ headless: true });
  let page;
  try {
    assert.equal(parts.length, 20);
    assert.equal(byFile.size, 20);
    assert.equal(parts.filter(part => part.layer === 'bone').length, 9);
    assert.deepEqual(region.layers.map(layer => layer[0]).sort(), ['bone', 'muscle', 'tendon']);
    const shared = parts.filter(part => part.file.startsWith('/app/anatomy/msk-mri-knee/'));
    assert.equal(shared.length, 5, 'Five resources are shared with the same source knee dataset');
    assert.equal(manifest.source_archive_sha256, knee.source_archive_sha256);
    assert.equal(manifest.coordinate_system.basis, 'LPS');
    assert.equal(manifest.coordinate_system.units, 'millimeters');
    for (const part of shared) {
      const original = Object.values(knee.parts).find(other => other.file === part.file);
      assert.ok(original, part.id + ': shared path is a real source knee resource');
      for (const key of ['sha256', 'decoded_sha256', 'source_sha256', 'decoded_bytes', 'vertices', 'triangles'])
        assert.equal(part[key], original[key], part.id + ': same-source identity ' + key);
      evidence.sharedResources.push({ ankleId: part.id, kneeId: original.id, file: part.file, decodedSha256: part.decoded_sha256 });
    }
    const context = await browser.newContext({ viewport: { width: 1440, height: 1080 }, reducedMotion: 'reduce', hasTouch: true });
    assert.equal((await context.request.post(base + '/api/profile', { data: {
      name: 'MRI ankle browser QA', age: 35, hours_per_week: 3, breadth: 'balanced', domains: ['radiology'],
    } })).status(), 200);
    await context.request.post(base + '/api/profile/settings', { data: { speak: false } });
    const files = ['app.js', 'styles.css', 'radiology-detailed-anatomy.js', 'anatomy/msk-mri-ankle/manifest.json', 'anatomy/msk-mri-knee/manifest.json'];
    for (const file of files) {
      const response = await context.request.get(base + '/app/' + file);
      assert.equal(response.status(), 200);
      const hash = sha(await response.body());
      assert.equal(hash, sha(fs.readFileSync(path.join(root, 'web', file))), file + ': served source matches workspace');
      evidence.sourceHashes[file] = hash;
    }
    const requests = [], zRequests = [], transportTasks = [], transportErrors = [];
    page = await context.newPage(); page.setDefaultTimeout(60000);
    page.on('pageerror', error => evidence.errors.push(error.message));
    page.on('request', request => {
      const pathname = new URL(request.url()).pathname;
      if (byFile.has(pathname)) requests.push(pathname);
      if (pathname.startsWith('/app/anatomy/msk-atlas/') && pathname.endsWith('.bin')) zRequests.push(pathname);
    });
    page.on('response', response => {
      const part = byFile.get(new URL(response.url()).pathname);
      if (!part) return;
      transportTasks.push((async () => {
        assert.equal(response.status(), 200, part.id + ': transport status');
        const headers = await response.allHeaders(), decoded = await response.body();
        assert.equal(headers['content-encoding'], 'gzip');
        assert.equal(headers['content-type'], 'application/octet-stream');
        assert.equal(decoded.readUInt32LE(0), 0x44335042, part.id + ': transparent BP3D decompression');
        assert.equal(decoded.length, part.decoded_bytes);
        assert.equal(decoded.readUInt32LE(4), part.vertices);
        assert.equal(decoded.readUInt32LE(8), part.triangles * 3);
        assert.equal(sha(decoded), part.decoded_sha256, part.id + ': decoded source fingerprint');
        evidence.transport.push({ id: part.id, file: part.file, encoding: headers['content-encoding'], encodedBytes: part.bytes,
          decodedBytes: decoded.length, decodedSha256: part.decoded_sha256 });
      })().catch(error => transportErrors.push(String(error.stack || error))));
    });
    await page.goto(base + '/#/radiology/ra.mri-ankle');
    await page.locator('.rad-reporting-desk').waitFor();
    await page.getByRole('tab', { name: '3D anatomy', exact: true }).click();
    const selector = page.getByRole('combobox', { name: 'Ankle anatomy source', exact: true });
    const model = page.locator('.rad-desk-panel:not([hidden]) .detailed-anatomy');
    const button = name => model.getByRole('button', { name, exact: true });
    const canvas = model.locator('canvas');
    const badge = model.locator('.detailed-anatomy-crop-status');
    assert.equal(await selector.inputValue(), 'z-anatomy', 'Broader atlas stays the actual ankle default');
    await ready('z-anatomy');
    assert.deepEqual(requests, [], 'Optional MRI source is not prefetched with the Z default');
    const firstZ = await canvas.elementHandle(), initialZRequests = zRequests.length;
    await selector.selectOption('malaya-ankle'); await ready('malaya-ankle');
    await disposed(firstZ);
    const initial = [...new Set(requests)].sort();
    assert.deepEqual(initial, parts.filter(part => part.layer === 'bone').map(part => part.file).sort(), 'Only nine bone resources requested initially');
    assert.equal(zRequests.length, initialZRequests, 'MRI selection does not fetch/mix more Z geometry');
    assert.equal(await model.locator('[data-part]:visible').count(), 9);
    assert.equal(await badge.textContent(), 'Cropped to region');
    await Promise.all(transportTasks); assert.deepEqual(transportErrors, []);
    evidence.initial = { defaultAtlas: 'z-anatomy', mriAtlas: 'malaya-ankle', bones: initial.length, requests: initial,
      encodedBytes: initial.reduce((sum, file) => sum + byFile.get(file).bytes, 0), softTissueRequests: 0 };
    const notes = await model.locator('.detailed-anatomy-note').textContent();
    for (const phrase of ['one adult male', 'LPS millimeter', 'not fitted', 'separate source segmentation',
      'Ankle ligaments, cartilage, nerves, vessels and bursae are not supplied', 'Full structures', 'complete Achilles', 'CC0 1.0'])
      assert.ok(notes.includes(phrase), 'Visible source limitation: ' + phrase);
    await capture('mri-bones-desktop');
    const loadedLayers = new Set(['bone']);
    for (const [layer, label] of region.layers) {
      const previous = new Set(requests); await choose(layer, label); loadedLayers.add(layer);
      assert.ok(requests.every(file => loadedLayers.has(byFile.get(file).layer)), layer + ': other tissues remain lazy');
      assert.deepEqual(await model.locator('[data-part]:visible').evaluateAll(elements => elements.map(e => e.dataset.part).sort()),
        parts.filter(part => part.layer === layer).map(part => part.id).sort());
      evidence.layers.push({ layer, objects: parts.filter(part => part.layer === layer).length,
        requestsAdded: [...new Set(requests)].filter(file => !previous.has(file)), ...await pixels() });
      await capture('layer-' + layer + '-desktop');
    }
    await Promise.all(transportTasks); assert.deepEqual(transportErrors, []);
    assert.equal(new Set(evidence.transport.map(part => part.id)).size, 20);
    assert.deepEqual([...new Set(requests)].sort(), parts.map(part => part.file).sort());
    assert.equal(zRequests.length, initialZRequests, 'MRI layer changes use only one subject/source frame');
    console.log('PASS MRI ankle transport and three lazy layers');
    const achilles = parts.find(part => part.name === 'Achilles tendon');
    assert.ok(achilles, 'Separately labelled Achilles object exists');
    assert.ok(achilles.bounds[1][2] > region.source_up_range[1], 'Source Achilles extends proximal to the regional crop');
    await choose('tendon', 'Tendons');
    const cropped = await canvas.evaluate(element => element.toDataURL());
    await button('Full structures').click(); await settled();
    assert.equal(await canvas.getAttribute('data-cropped'), 'false');
    assert.equal(await badge.textContent(), 'Uncropped source');
    const whole = await canvas.evaluate(element => element.toDataURL());
    assert.notEqual(whole, cropped, 'Whole Achilles is visibly distinct from the regional crop');
    await pixels(); await capture('achilles-full-structures-desktop');
    await button('Full structures').click(); await settled();
    assert.equal(await badge.textContent(), 'Cropped to region');
    assert.equal(await canvas.evaluate(element => element.toDataURL()), cropped, 'Crop reset restores original geometry');
    await model.locator('[data-part="' + achilles.id + '"]').click();
    await button('Isolate').click(); await settled();
    assert.equal(await canvas.getAttribute('data-cropped'), 'false');
    assert.equal(await badge.textContent(), 'Uncropped source');
    assert.equal(await button('Full structures').getAttribute('aria-pressed'), 'true');
    assert.equal(await model.locator('.detailed-anatomy-selected').textContent(), 'Achilles tendon');
    evidence.achilles = { id: achilles.id, sourceBoundsLpsMm: achilles.bounds, cropSuperiorRange: region.source_up_range,
      fullStructuresChangesView: true, isolateRemovesCrop: true, ...await pixels() };
    await capture('achilles-isolated-desktop');
    await button('Lateral').click(); await settled(); await capture('achilles-isolated-lateral');
    await page.setViewportSize({ width: 390, height: 844 }); await settled(); await noOverflow();
    await pixels(); await capture('achilles-isolated-mobile');
    console.log('PASS complete source Achilles and mobile isolation');
    await button('Reset').click(); await settled();
    assert.equal(await badge.textContent(), 'Cropped to region');
    await choose('all', 'Together');
    const achillesChoice = model.locator('[data-part="' + achilles.id + '"]');
    await achillesChoice.focus(); await page.keyboard.press('Enter'); await settled();
    assert.equal(await achillesChoice.getAttribute('aria-pressed'), 'true');
    await button('Lateral').focus(); await page.keyboard.press('Enter'); await settled();
    await pixels(); await capture('achilles-bone-context-cropped-mobile');
    await button('Full structures').click(); await settled();
    assert.equal(await badge.textContent(), 'Uncropped source');
    await pixels(); await capture('achilles-bone-context-full-mobile');
    await page.setViewportSize({ width: 1440, height: 1080 }); await settled();
    await capture('achilles-bone-context-full-desktop');
    console.log('PASS Achilles/bone context and crop badges');
    const oldMRI = await canvas.elementHandle();
    await selector.selectOption('z-anatomy'); await ready('z-anatomy'); await disposed(oldMRI);
    assert.equal(await page.locator('.rad-anatomy-model-host .detailed-anatomy').count(), 1);
    assert.ok((await model.locator('[data-part]').evaluateAll(elements => elements.map(e => e.dataset.part))).every(id => id.startsWith('za-')));
    const oldZ = await canvas.elementHandle();
    await selector.selectOption('malaya-ankle'); await ready('malaya-ankle'); await disposed(oldZ);
    assert.equal(await page.locator('.rad-anatomy-model-host .detailed-anatomy').count(), 1);
    assert.ok((await model.locator('[data-part]').evaluateAll(elements => elements.map(e => e.dataset.part))).every(id => id.startsWith('um-ankle-')));
    assert.equal(await canvas.getAttribute('data-layer'), 'bone');
    assert.equal(await badge.textContent(), 'Cropped to region');
    await page.setViewportSize({ width: 390, height: 844 }); await settled(); await noOverflow(); await pixels();
    await capture('mri-bones-return-mobile');
    evidence.sourceSwitch = { defaultZDisposed: true, mriDisposed: true, returnedZDisposed: true, oneProviderMounted: true, restoredBoneCrop: true };
    await Promise.all(transportTasks); assert.deepEqual(transportErrors, []); assert.deepEqual(evidence.errors, []);
    for (const file of files) assert.equal(sha(fs.readFileSync(path.join(root, 'web', file))), evidence.sourceHashes[file], file + ': source changed during QA');
    evidence.status = 'passed'; fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(evidence, null, 2) + '\n');
    console.log('PASS MRI ankle: 9 initial bones; 20 decoded transports including 5 same-source shared resources; 3 layers; whole Achilles, crop badges, disposal and mobile. Evidence: ' + out);

    async function settled() { await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))); }
    async function ready(atlas) {
      await page.waitForFunction(atlas => { const el = document.querySelector('.rad-desk-panel:not([hidden]) .detailed-anatomy');
        if (el?.dataset.error) throw new Error(el.querySelector('.detailed-anatomy-status').textContent);
        return el?.dataset.atlas === atlas && el.dataset.ready === 'true' && el.querySelector('canvas')?.dataset.rendered === 'true';
      }, atlas, { timeout: 120000 }); await settled();
    }
    async function disposed(handle) { await page.waitForFunction(element => !element.isConnected && element.getContext('webgl').isContextLost(), handle); }
    async function choose(layer, label) {
      await button(label).click(); await page.waitForFunction(layer => document.querySelector('.rad-desk-panel:not([hidden]) .detailed-anatomy canvas')?.dataset.layer === layer, layer, { timeout: 120000 }); await settled();
    }
    async function pixels() {
      await settled(); const result = await canvas.evaluate(canvas => { const gl = canvas.getContext('webgl'), data = new Uint8Array(canvas.width * canvas.height * 4);
        gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, data);
        let count = 0; for (let i = 3; i < data.length; i += 4) if (data[i] > 20) count++;
        return { pixels: count, glError: gl.getError(), width: canvas.width, height: canvas.height }; });
      assert.equal(result.glError, 0); assert.ok(result.pixels > 100, JSON.stringify(result)); return result;
    }
    async function capture(name) {
      const file = name + '.png';
      // Explicit instant scrolling avoids the element-screenshot stability
      // loop when the app's sticky header and long structure list reflow.
      await model.locator('.detailed-anatomy-stage').evaluate(element => element.scrollIntoView({ block: 'center', behavior: 'instant' }));
      await settled();
      await page.screenshot({ path: path.join(out, file), animations: 'disabled', timeout: 30000 });
      evidence.screenshots.push(file);
    }
    async function noOverflow() { const bounds = await page.evaluate(() => ({ viewport: innerWidth, page: document.documentElement.scrollWidth,
      models: [...document.querySelectorAll('.detailed-anatomy')].filter(el => el.getBoundingClientRect().width).map(el => [el.clientWidth, el.scrollWidth]) }));
      assert.ok(bounds.page <= bounds.viewport + 1 && bounds.models.every(([w, s]) => s <= w + 1), JSON.stringify(bounds)); }
  } catch (error) {
    evidence.status = 'failed'; evidence.failure = String(error.stack || error);
    if (page) await page.screenshot({ path: path.join(out, 'failure.png') }).catch(() => {});
    fs.writeFileSync(path.join(out, 'failure.json'), JSON.stringify(evidence, null, 2) + '\n'); throw error;
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
