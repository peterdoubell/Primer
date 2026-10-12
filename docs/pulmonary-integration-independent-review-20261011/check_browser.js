'use strict';
// Isolated, authenticated local fixture. No user browser profile or remote mutation.
const fs = require('fs'), path = require('path'), crypto = require('crypto'), assert = require('assert');
const { chromium } = require('/Users/peter/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = path.resolve(__dirname, '../..');
const folder = path.join(__dirname, 'browser');
fs.mkdirSync(folder, { recursive: true });
const fixture = JSON.parse(fs.readFileSync(path.join(root, '.research/pulmonary-integrated-reader-20261011/fixture.json')));
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'web/anatomy/lidc-idri-0525/manifest.json')));
const oracle = JSON.parse(fs.readFileSync(path.join(root, 'docs/pulmonary-nodule-independent-review-20261011/source-oracle.json')));
const digest = b => crypto.createHash('sha256').update(b).digest('hex');
const headers = { Authorization: 'Basic ' + Buffer.from(fixture.username + ':' + fixture.password).toString('base64') };
const proof = { schema_version: 1, source_scope: 'authenticated local pulmonary reporting and shared lesson integration',
  cloud_or_hosted_blob_verified: false, clinical_approval: false, fine_anatomical_approval: false,
  structure_coverage_granted: false, whole_goal_complete: false, rows: [] };

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    for (const width of [1440, 390]) {
      for (const route of ['radiology', 'node']) {
        const context = await browser.newContext({ viewport: { width, height: 950 }, extraHTTPHeaders: headers });
        await context.addInitScript(() => {
          window.independentMeshBuffers = []; window.independentMeshDraws = [];
          const old = WebGLRenderingContext.prototype.bufferData;
          const draw = WebGLRenderingContext.prototype.drawArrays;
          WebGLRenderingContext.prototype.bufferData = function (target, data, usage) {
            if (data instanceof Float32Array) independentMeshBuffers.push(new Uint8Array(data.buffer, data.byteOffset, data.byteLength).slice());
            return old.call(this, target, data, usage);
          };
          WebGLRenderingContext.prototype.drawArrays = function (mode, first, count) {
            independentMeshDraws.push({ mode, first, count }); return draw.call(this, mode, first, count);
          };
        });
        const page = await context.newPage(); const errors = [], bodies = [], jobs = [];
        page.on('pageerror', e => errors.push(String(e)));
        page.on('console', e => { if (e.type() === 'error' && !e.text().includes('favicon')) errors.push(e.text()); });
        page.on('response', r => {
          const url = new URL(r.url());
          if (url.origin === fixture.url && r.status() === 200 &&
              (url.pathname.includes('/anatomy/lidc-idri-0525/') || ['/app/app.js', '/app/lesson-models.js'].includes(url.pathname))) {
            if (r.request().method() === 'HEAD') return;
            // Chromium inspector cannot reliably retain the seven large CT bodies;
            // full CT samples are verified through original-source RGB oracles below.
            if (url.pathname.includes('/ct.native.')) return;
            const job = (async () => { const b = await r.body(); const local = fs.readFileSync(path.join(root, 'web', url.pathname.replace(/^\/app\//, '')));
              if (b.length !== local.length) fs.writeFileSync(path.join(folder, 'body-length-observation.json'), JSON.stringify({ path: url.pathname, method: r.request().method(), status: r.status(), headers: r.headers(), bytes: b.length, expected_bytes: local.length }, null, 2));
              assert.strictEqual(digest(b), digest(local)); assert.strictEqual(b.length, local.length);
              bodies.push({ path: url.pathname, bytes: b.length, sha256: digest(b) }); })();
            job.catch(() => {}); jobs.push(job);
          }
        });
        const id = route === 'radiology' ? 'ra.ct-pulmonary-nodules' : 'rad.4.pulmonary-nodule';
        await page.goto(fixture.url + '/app/#/' + route + '/' + id);
        await page.waitForSelector(route === 'radiology' ? '.rad-reporting-desk' : '.lesson-media', { timeout: 60000 });
        let entry;
        const row = { width, route, report_steps: [], source_body_pins: bodies, errors };
        if (route === 'radiology') {
          await page.getByRole('tab', { name: 'Step by step', exact: true }).click();
          const walk = page.locator('.rad-walk');
          assert.deepStrictEqual(await walk.locator('.rad-walk-mode').allTextContents(), ['Native source']);
          assert.strictEqual(await walk.locator('.rad-walk-model canvas').count(), 0);
          const buttons = walk.locator('.rad-walk-steps button');
          assert.strictEqual(await buttons.count(), 8);
          for (let i = 0; i < 8; i++) {
            await buttons.nth(i).click();
            const fields = await walk.locator('.rad-walk-editor').evaluateAll(nodes => nodes.map(n => n.value));
            assert(fields.every(v => v.includes('[')), [i, fields]);
            assert.strictEqual(await walk.locator('.detailed-anatomy, .spatial-model, .rad-walk-model canvas').count(), 0);
            row.report_steps.push({ index: i, title: await walk.locator('.rad-walk-title').textContent(), blank_field_count: fields.length });
          }
          const report = await walk.locator('.rad-walk-preview').inputValue();
          for (const heading of ['PATHWAY', 'NODULE INVENTORY', 'SIZE AND MORPHOLOGY', 'INTERVAL CHANGE', 'ASSESSMENT']) assert(report.includes(heading));
          assert(report.includes('['));
          await walk.getByRole('button', { name: 'Insert assessment prompts', exact: true }).click();
          assert((await walk.locator('.rad-walk-preview').inputValue()).includes('['));
          await page.getByRole('tab', { name: 'Native source models', exact: true }).click();
          const active = page.locator('[role="tabpanel"]:visible');
          assert.strictEqual(await active.locator('.detailed-anatomy, .rad-anatomy-model-host canvas').count(), 0);
          entry = active.locator('.source-native-inspector');
          assert.strictEqual(await entry.count(), 1);
        } else {
          const model = page.locator('.lesson-native-anatomy');
          assert.strictEqual(await model.count(), 1);
          assert.strictEqual(await model.locator('canvas, .detailed-anatomy').count(), 0);
          assert.strictEqual(await model.locator('a[href="/app/anatomy/lidc-idri-0525/reference.html"]').count(), 1);
          const gallery = page.locator('.lesson-media .lesson-source-gallery');
          await gallery.getByRole('button', { name: 'Load original native source inspections', exact: true }).click();
          await gallery.locator('details').waitFor({ state: 'attached', timeout: 60000 });
          await gallery.locator('summary').click();
          entry = page.locator('.lesson-media .source-native-inspector');
          await entry.waitFor({ state: 'visible', timeout: 60000 });
          assert.strictEqual(await entry.count(), 1);
        }
        assert((await entry.textContent()).includes('Original CT source dataset'));
        assert((await entry.textContent()).includes('Original standardized annotations'));
        assert((await entry.textContent()).includes('CC BY 3.0'));
        assert.strictEqual(await entry.locator('iframe').count(), 0);
        const toggle = entry.getByRole('button', { name: 'Inspect source CT and models inline', exact: true });
        await toggle.focus(); await toggle.press('Enter');
        await entry.locator('iframe').waitFor();
        const frame = await entry.locator('iframe').elementHandle().then(e => e.contentFrame());
        await frame.waitForFunction(() => document.getElementById('plane-2')?.dataset.ready === 'true', null, { timeout: 180000 });
        row.inline_exact_source = await entry.locator('iframe').getAttribute('src');
        assert.strictEqual(row.inline_exact_source, '/app/anatomy/lidc-idri-0525/reference.html');
        assert.strictEqual(await frame.locator('#annotation option').count(), 8);
        assert.strictEqual(await frame.locator('#xml-mark option').count(), 33);
        row.original_source_planes = [];
        for (const sample of [oracle.native_plane_oracles[0], oracle.native_plane_oracles.at(-1)]) {
          for (let axis = 0; axis < 3; axis++) { await frame.locator('#number-' + axis).fill(String(sample.cursor[axis])); await frame.locator('#number-' + axis).press('Enter'); }
          const planes = await frame.evaluate(async () => {
            const list = [];
            for (let axis = 0; axis < 3; axis++) { const c = document.getElementById('plane-' + axis), data = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
              const sha256 = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', data)), b => b.toString(16).padStart(2, '0')).join('');
              list.push({ width: c.width, height: c.height, sha256 }); }
            return list;
          });
          assert.deepStrictEqual(planes, sample.planes);
          assert((await frame.locator('#values').textContent()).includes('Stored integer ' + sample.stored_integer + ' · original HU ' + sample.HU));
          row.original_source_planes.push({ cursor: sample.cursor, planes });
        }
        row.full_GPU_models = [];
        for (const annotation of manifest.annotations) {
          await frame.locator('#annotation').selectOption(annotation.id);
          await frame.waitForFunction(id => document.getElementById('mesh').dataset.annotation === id, annotation.id);
          const gpu = await frame.evaluate(async () => { const b = independentMeshBuffers.at(-1); return { bytes: b.length,
            sha256: Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', b)), v => v.toString(16).padStart(2, '0')).join(''), draw: independentMeshDraws.at(-1) }; });
          const expected = oracle.GPU_buffer_oracles.find(v => v.id === annotation.id);
          assert.strictEqual(gpu.sha256, expected.sha256); assert.strictEqual(gpu.bytes, expected.bytes);
          assert.strictEqual(gpu.draw.count, annotation.mesh.triangles * 3);
          await frame.locator('#yaw').focus(); await frame.locator('#yaw').press('ArrowRight');
          await frame.locator('#pitch').focus(); await frame.locator('#pitch').press('ArrowUp');
          await frame.locator('#reset').click();
          assert.strictEqual(await frame.locator('#yaw').inputValue(), '25');
          assert.strictEqual(await frame.locator('#pitch').inputValue(), '-20');
          row.full_GPU_models.push({ id: annotation.id, gpu, keyboard_camera_and_reset: true });
        }
        row.all_original_XML_mark_selections = [];
        for (let i = 0; i < manifest.xml_marks.length; i++) {
          await frame.locator('#xml-mark').selectOption(String(i));
          const source = manifest.xml_marks[i].rois[0];
          assert.strictEqual(await frame.locator('#number-0').inputValue(), String(source.points[0][0]));
          assert.strictEqual(await frame.locator('#number-1').inputValue(), String(source.points[0][1]));
          assert.strictEqual(await frame.locator('#number-2').inputValue(), String(source.ct_slice));
          row.all_original_XML_mark_selections.push({ index: i, source_id: manifest.xml_marks[i].source_id,
            session_index: manifest.xml_marks[i].session_index, source_CT_slice: source.ct_slice });
        }
        await frame.locator('#jump').click();
        await frame.locator('#plane-2').scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(folder, `${width}-${route}-CT.png`) });
        await frame.locator('#mesh').scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(folder, `${width}-${route}-models.png`) });
        row.parent_overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
        row.source_overflow = await frame.evaluate(() => document.documentElement.scrollWidth > innerWidth);
        assert.strictEqual(row.parent_overflow, false); assert.strictEqual(row.source_overflow, false);
        await entry.getByRole('button', { name: 'Close source viewer', exact: true }).focus();
        await entry.getByRole('button', { name: 'Close source viewer', exact: true }).press('Space');
        assert.strictEqual(await entry.locator('iframe').count(), 0);
        row.keyboard_open_and_close = true;
        await Promise.all(jobs); assert.deepStrictEqual(errors, []);
        proof.rows.push(row); await context.close();
        fs.writeFileSync(path.join(folder, 'progress.json'), JSON.stringify(proof, null, 2) + '\n');
      }
    }
    proof.current_app_js_sha256 = digest(fs.readFileSync(path.join(root, 'web/app.js')));
    proof.current_lesson_models_sha256 = digest(fs.readFileSync(path.join(root, 'web/lesson-models.js')));
    fs.writeFileSync(path.join(folder, 'proof.json'), JSON.stringify(proof, null, 2) + '\n');
    console.log(JSON.stringify({ rows: proof.rows.length, original_RGB_planes: proof.rows.length * 6,
      complete_GPU_models: proof.rows.length * 8, errors: 0, actual_cloud_verified: false }));
  } catch (error) {
    fs.writeFileSync(path.join(folder, 'failed-proof.json'), JSON.stringify({ proof, error: String(error.stack) }, null, 2) + '\n');
    throw error;
  } finally { await browser.close(); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
