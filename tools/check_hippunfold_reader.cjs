/* Authenticated, isolated real-reader proof for the registered source reference. */
'use strict';
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const assert = require('assert/strict'), { chromium } = require('playwright');
const fixture = JSON.parse(fs.readFileSync(process.argv[2]));
assert.equal(new URL(fixture.url).hostname, '127.0.0.1');
const ROOT = path.resolve(__dirname, '..');
const ATLAS = 'hippunfold-hcp101006-registered';
const PREFIX = '/app/anatomy/' + ATLAS + '/';
const ID = 'hippunfold-hcp101006-registered-reference';
const ASSETS = path.join(ROOT, 'web/anatomy', ATLAS);
const hash = raw => crypto.createHash('sha256').update(raw).digest('hex');
const manifest = JSON.parse(fs.readFileSync(path.join(ASSETS, 'manifest.json')));
const registry = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/radiology/hippunfold-reference.json')));
const shell = fs.readFileSync(path.join(ROOT, 'web/index.html'), 'utf8');
const scriptNames = [...shell.matchAll(/<script src="\/app\/([\w-]+\.js)(?:\?[^"<>]*)?"><\/script>/g)].map(m => m[1]);
const expectedBundle = Buffer.from("'use strict';\n" + scriptNames.map(n => fs.readFileSync(path.join(ROOT, 'web', n), 'utf8')).join('\n;\n'));
const rows = [...manifest.hemispheres.flatMap(h => h.arrays), ...manifest.meshes];
const sources = ['web/app.js', 'web/index.html', 'primer/server.py', 'primer/hippunfold_reference.py',
  'primer/module_media.py', 'data/radiology/hippunfold-reference.json', 'data/curriculum/11-radiology.json',
  'data/radiology/reporting-steps/neuroradiology.json', ...Object.keys(registry.files).map(n => 'web/anatomy/' + ATLAS + '/' + n)];
const proof = { scope: 'Current authenticated reporting and lesson readers, isolated loopback synthetic data',
  productionVerified: false, sourceSHA256: Object.fromEntries(sources.map(n => [n, hash(fs.readFileSync(path.join(ROOT, n)))])),
  cases: [], deliveredPayloads: {}, errors: [] };
const openLabel = 'Inspect registered hippocampal MRI and surfaces inline';

async function ready(frame, side = 'L') {
  await frame.locator('#mri[data-ready="true"]').waitFor({ timeout: 60000 });
  await frame.locator('#mesh[data-ready="true"]').waitFor({ timeout: 60000 });
  assert.equal(await frame.locator('#mri').evaluate(c => JSON.parse(c.dataset.state).hemi), side);
  assert.equal(await frame.locator('#mesh').getAttribute('data-error'), null);
}

async function checkViewer(page, section, full, drainResponses) {
  await section.getByRole('button', { name: openLabel, exact: true }).click();
  const iframe = section.locator('iframe');
  await iframe.waitFor();
  assert.equal(await iframe.getAttribute('src'), PREFIX + 'index.html');
  const frame = await (await iframe.elementHandle()).contentFrame();
  await ready(frame);
  let states = 0;
  for (const side of ['L', 'R']) {
    await frame.locator('#hemi').selectOption(side);
    await ready(frame, side);
    for (const plane of ['0', '1', '2']) {
      await frame.locator('#plane').selectOption(plane);
      const state = await frame.locator('#mri').evaluate(c => JSON.parse(c.dataset.state));
      assert.equal(state.axis, Number(plane));
      assert.equal(state.hemi, side);
      states++;
    }
    for (const label of full ? ['1', '2', '3', '4', '5', '6', '7', '8'] : ['2', '8']) {
      await frame.locator('#class').selectOption(label);
      await ready(frame, side);
      assert.equal(await frame.locator('#mesh').getAttribute('data-parts'), side + '-' + label);
      assert.match(await frame.locator('#class-note').innerText(), /\S/);
      states++;
    }
    await frame.locator('#surface-scope').selectOption('all');
    await ready(frame, side);
    assert.equal((await frame.locator('#mesh').getAttribute('data-parts')).split(',').length, 8);
    assert.equal(Number(await frame.locator('#mesh').getAttribute('data-triangles')),
      manifest.meshes.filter(m => m.sourceHemisphereName === side).reduce((n, m) => n + m.triangleCount, 0));
    await frame.locator('#surface-scope').selectOption('selected');
    await ready(frame, side);
    states++;
  }
  const before = await frame.evaluate(() => window.HippUnfoldReference.state().renderState);
  await frame.locator('#mesh').focus();
  await page.keyboard.press('ArrowRight');
  const after = await frame.evaluate(() => window.HippUnfoldReference.state().renderState);
  assert(after.azimuth > before.azimuth);
  await frame.locator('#reset-3d').click();
  assert.equal(await frame.evaluate(() => window.HippUnfoldReference.state().renderState.azimuth), 0);
  await frame.locator('#mri').focus();
  const beforeSlice = await frame.locator('#slice').inputValue();
  await page.keyboard.press('ArrowDown');
  assert.equal(Number(await frame.locator('#slice').inputValue()), Math.max(0, Number(beforeSlice) - 1));
  await frame.locator('#enlarge-mri').click();
  assert(await frame.locator('#mri').evaluate(c => c.closest('section').classList.contains('enlarged')));
  assert(await frame.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await frame.locator('#enlarge-mri').click();
  await frame.locator('#enlarge-3d').click();
  assert(await frame.locator('#mesh').evaluate(c => c.closest('section').classList.contains('enlarged')));
  assert(await frame.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await frame.locator('#enlarge-3d').click();
  states += 5;
  const deliveries = await frame.evaluate(() => window.hippReaderPayloads);
  for (const [name, data] of Object.entries(deliveries)) {
    const row = rows.find(r => r.file === name);
    assert(row, 'Unknown delivered payload ' + name);
    assert.equal(data.status, 200);
    if (data.representation === 'gzip') assert.equal(data.responseSHA256, row.gzipSHA256);
    assert.equal(data.decodedSHA256, row.decodedSHA256);
    assert.equal(data.bytes, row.byteLength);
    proof.deliveredPayloads[name] = data;
  }
  assert.equal(Object.keys(deliveries).length, 20);
  assert.deepEqual(await frame.evaluate(() => window.hippReaderDeliveryErrors), []);
  const gpu = await frame.evaluate(() => window.HippUnfoldReference.gpuReadback());
  assert.equal(gpu.length, 16);
  for (const row of gpu) {
    const m = manifest.meshes.find(m => m.sourceHemisphereName + '-' + m.label === row.key);
    assert.equal(row.positionSHA256, m.positionByteSHA256);
    assert.equal(row.indexSHA256, m.indexByteSHA256);
    assert.equal(row.positionByteLength, m.vertexCount * 12);
    assert.equal(row.indexByteLength, m.triangleCount * 12);
  }
  assert.deepEqual(await frame.evaluate(() => window.hippReaderCSPViolations), []);
  assert(await frame.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await drainResponses();
  await section.getByRole('button', { name: 'Close source viewer', exact: true }).click();
  assert.equal(await section.locator('iframe').count(), 0);
  return { states, gpuMeshes: gpu.length, gpuPositionAndIndexBytesExact: true, noHorizontalOverflow: true };
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const unauthenticated = await browser.newContext();
    proof.authentication = [];
    for (const name of ['index.html', 'viewer.js', 'manifest.json', 'L-T2w.bin.gz']) {
      const denied = await unauthenticated.request.get(fixture.url + PREFIX + name);
      assert.equal(denied.status(), 401);
      proof.authentication.push({ asset: name, unauthenticatedStatus: denied.status() });
    }
    await unauthenticated.close();
    for (const width of [390, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 1000 },
        extraHTTPHeaders: { Authorization: 'Basic ' + Buffer.from(fixture.username + ':' + fixture.password).toString('base64') } });
      await context.addInitScript(({ prefix }) => {
        window.hippReaderCSPViolations = [];
        window.hippReaderPayloads = {};
        window.hippReaderDeliveryErrors = [];
        document.addEventListener('securitypolicyviolation', e => window.hippReaderCSPViolations.push({ directive: e.violatedDirective, blocked: e.blockedURI }));
        const originalFetch = window.fetch.bind(window);
        const sha = async bytes => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), x => x.toString(16).padStart(2, '0')).join('');
        // Inspect a clone of the response actually returned to the viewer.
        // Chromium's devtools body cache evicts these large MRI responses;
        // this hook leaves the original response and its body unchanged.
        window.fetch = async (...args) => {
          const response = await originalFetch(...args);
          const pathname = new URL(response.url).pathname;
          if (pathname.startsWith(prefix) && pathname.endsWith('.gz')) {
            try {
              const raw = await response.clone().arrayBuffer(), bytes = new Uint8Array(raw);
              const compressed = bytes[0] === 31 && bytes[1] === 139;
              const decoded = compressed ? await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer() : raw;
              window.hippReaderPayloads[pathname.slice(prefix.length)] = { status: response.status,
                responseSHA256: await sha(raw), decodedSHA256: await sha(decoded), bytes: decoded.byteLength,
                representation: compressed ? 'gzip' : 'HTTP-decoded' };
            } catch (error) { window.hippReaderDeliveryErrors.push(error.message); }
          }
          return response;
        };
      }, { prefix: PREFIX });
      const profile = await context.request.post(fixture.url + '/api/profile', {
        headers: { Origin: fixture.url }, data: { name: 'Synthetic hippocampal reference QA', age: 30, domains: ['radiology'] } });
      assert.equal(profile.status(), 200);
      for (const bad of ['%69ndex.html', 'L%2FT2w.bin.gz', 'missing.bin.gz']) {
        const missing = await context.request.get(fixture.url + PREFIX + bad);
        assert.equal(missing.status(), 404);
      }
      const page = await context.newPage(), errors = [], responses = [];
      let bundleCount = 0;
      page.on('pageerror', error => errors.push(error.message));
      page.on('response', response => {
        const pathname = new URL(response.url()).pathname;
        if (pathname.startsWith(PREFIX)) {
          if (response.headers()['cache-control'] !== 'private, no-store') errors.push('Unexpected viewer cache policy ' + pathname);
          if (pathname === PREFIX + 'index.html' && !response.headers()['content-security-policy']?.includes("frame-ancestors 'self'")) errors.push('Viewer iframe policy differs');
        }
        if (pathname === '/app/startup.js') responses.push(response.body().then(raw => {
          assert(raw.equals(expectedBundle)); bundleCount++;
          proof.startupBundle = { bytes: raw.length, sha256: hash(raw), currentSourceBytesEqual: true };
        }).catch(e => errors.push('Startup source: ' + e.message)));
        if (pathname.startsWith(PREFIX) && !pathname.endsWith('.gz')) responses.push(response.body().then(raw => {
          const name = pathname.slice(PREFIX.length);
          assert.equal(response.status(), 200);
          assert.equal(hash(raw), registry.files[name].sha256);
        }).catch(e => errors.push('Viewer source ' + pathname + ': ' + e.message)));
      });
      for (const [investigation, lesson] of [['ra.mri-epilepsy', 'rad.5.epilepsy-mri'], ['ra.mri-dementia', 'rad.5.dementia']]) {
        const moduleResponse = await context.request.get(fixture.url + '/api/radiology/modules/' + investigation);
        assert.equal(moduleResponse.status(), 200);
        const module = await moduleResponse.json(), ref = module.radiology_reference;
        assert(ref.reporting.checklist.length && ref.walkthrough.steps.length && ref.report_templates.length);
        const item = ref.source_native_inspectors.find(i => i.id === ID);
        assert(item && item.coordinate_context === 'published-registered-training-grid');
        for (const flag of ['clinical_approval', 'fine_anatomical_approval', 'current_patient_registration', 'normal_anatomical_atlas_approval', 'complete_reporting_anatomy_approved']) assert.equal(item[flag], false);
        await page.goto(fixture.url + '/app/#radiology/' + investigation);
        for (const tabName of ['Images and registered MRI', '3D anatomy and original source context']) {
          await page.getByRole('tab', { name: tabName, exact: true }).click();
          const section = page.locator('.source-native-inspector:visible').filter({ has: page.locator('a[href="' + PREFIX + 'index.html"]') });
          assert.equal(await section.count(), 1);
          const checks = await checkViewer(page, section, tabName === 'Images and registered MRI', () => Promise.all(responses));
          proof.cases.push({ width, investigation, reader: tabName, ...checks });
        }
        await page.getByRole('tab', { name: 'Checklist', exact: true }).click();
        assert(await page.locator('[role="tabpanel"]:visible').innerText());
        await page.getByRole('tab', { name: 'Step by step', exact: true }).click();
        assert(await page.locator('[role="tabpanel"]:visible').innerText());
        if (investigation === 'ra.mri-epilepsy') {
          await page.locator('.rad-walk-step').filter({ hasText: 'Cortex and neuronal migration' }).click();
          assert.match(await page.locator('.rad-walk-main').innerText(), /supports focal cortical dysplasia type II, most often IIb; imaging does not establish the histological subtype/);
        }
        await page.getByRole('button', { name: 'Original source context', exact: true }).click();
        const walkthroughSource = page.locator('.rad-walk .source-native-inspector:visible').filter({ has: page.locator('a[href="' + PREFIX + 'index.html"]') });
        proof.cases.push({ width, investigation, reader: 'Walkthrough original source context', ...await checkViewer(page, walkthroughSource, false, () => Promise.all(responses)) });
        await page.goto(fixture.url + '/app/#/node/' + lesson);
        const gallery = page.getByRole('region', { name: 'Registered hippocampal MRI and source surfaces', exact: true });
        await gallery.getByRole('button', { name: 'Load original registered MRI references', exact: true }).click();
        await gallery.getByText(/Original registered MRI references loaded/).waitFor();
        await gallery.locator('details > summary').click();
        const section = gallery.locator('.source-native-inspector').filter({ has: page.locator('a[href="' + PREFIX + 'index.html"]') });
        proof.cases.push({ width, investigation, lesson, reader: 'Lesson source gallery', ...await checkViewer(page, section, false, () => Promise.all(responses)) });
      }
      await Promise.all(responses);
      assert(bundleCount > 0);
      assert.deepEqual(errors, []);
      assert.deepEqual(await page.evaluate(() => window.hippReaderCSPViolations), []);
      await context.close();
    }
    assert.equal(Object.keys(proof.deliveredPayloads).length, 20);
    for (const [name, expected] of Object.entries(proof.sourceSHA256)) assert.equal(hash(fs.readFileSync(path.join(ROOT, name))), expected, name + ' changed during proof');
    proof.totalReaderCases = proof.cases.length;
    proof.totalInteractionStates = proof.cases.reduce((n, c) => n + c.states, 0);
    proof.timestamp = new Date().toISOString();
    const out = process.argv[3] || path.join(ROOT, 'docs/hippunfold-epilepsy-review-20261016/reader-proof.json');
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, JSON.stringify(proof, null, 2) + '\n');
    console.log(JSON.stringify({ proof: out, readerCases: proof.totalReaderCases, interactionStates: proof.totalInteractionStates, exactDeliveredPayloads: 20, errors: [] }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
