#!/usr/bin/env node
'use strict';

// Read-only against a disposable QA server. Every live model
// is mounted through the shipped renderer registry; route interaction and
// responsive-layout coverage belongs to check_module_media_browser.cjs.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { execFileSync } = require('node:child_process');
const { chromium } = require('playwright');
const { createEvidenceDirectory, loopbackQaUrl } = require('./qa-browser.cjs');
const base = loopbackQaUrl(process.argv[2]);
const output = createEvidenceDirectory();
const root = path.resolve(__dirname, '..');
const digest = data => createHash('sha256').update(data).digest('hex');
const inventory = JSON.parse(execFileSync(process.env.PRIMER_QA_PYTHON || 'python3', ['-c',
  'import json; from primer.curriculum import Curriculum; c=Curriculum(); print(json.dumps([{ "id":n["id"], "domain":n["domain"], "models":[m for m in n.get("lesson_media",[]) if m.get("kind")=="model"] } for n in c.nodes.values()]))',
], { cwd: root, maxBuffer: 20 * 1024 * 1024, encoding: 'utf8' }));

(async () => {
  const evidence = { sourceHashes: {}, lessons: [], models: [], errors: [] };
  const browser = await chromium.launch({ headless: true });
  let page;
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
    const galleryResponse = await context.request.get(base + '/api/curriculum/visuals');
    assert.equal(galleryResponse.status(), 200);
    const gallery = await galleryResponse.json();
    assert.equal(gallery.counts.lessons, inventory.length, 'Live catalogue matches workspace curriculum');
    const expectedModels = inventory.flatMap(lesson => lesson.models.map(item => ({ lesson, item })));
    assert.equal(gallery.counts.models, expectedModels.length, 'Live model inventory is complete');
    for (const lesson of inventory) {
      assert.ok(lesson.models.some(item => ['spatial-3d', 'radiology-anatomy'].includes(item.renderer)),
        lesson.id + ': has an interactive 3D binding');
    }

    // Read every live lesson's exact props; the answer-free gallery intentionally
    // omits them. Bounded requests avoid competing heavily with route QA.
    let cursor = 0;
    await Promise.all(Array.from({ length: 4 }, async () => {
      while (cursor < inventory.length) {
        const lesson = inventory[cursor++];
        const response = await context.request.get(base + '/api/curriculum/node/' + encodeURIComponent(lesson.id));
        assert.equal(response.status(), 200, lesson.id + ': live lesson API');
        const live = await response.json();
        const models = (live.lesson_media || []).filter(item => item.kind === 'model');
        assert.deepEqual(models, lesson.models, lesson.id + ': exact live/workspace model bindings');
        const cards = gallery.items.filter(item => item.lesson_id === lesson.id && item.kind === 'model');
        assert.deepEqual(cards.map(item => item.media_id).sort(), models.map(item => item.id).sort(),
          lesson.id + ': every model is reachable from the gallery');
      }
    }));

    const html = fs.readFileSync(path.join(root, 'web/index.html'), 'utf8');
    const scripts = [...html.matchAll(/<script\b[^>]*\bsrc=["']([^"']+)["']/g)]
      .map(match => match[1]).filter(src => src.startsWith('/app/'));
    for (const src of scripts) {
      const response = await context.request.get(base + src);
      assert.equal(response.status(), 200, src + ': script served');
      const local = path.join(root, 'web', src.split('?')[0].slice('/app/'.length));
      evidence.sourceHashes[src] = digest(await response.body());
      assert.equal(evidence.sourceHashes[src], digest(fs.readFileSync(local)), src + ': exact workspace source');
    }

    page = await context.newPage();
    page.on('pageerror', error => evidence.errors.push(error.message));
    await page.goto(base + '/#/node/' + encodeURIComponent(inventory[0].id));
    // Model mounting does not require a learner session. Full lesson routing
    // and its profile setup are exercised by the complementary route checker.
    await page.waitForFunction(() => window.PrimerLessonModels && document.querySelector('#root')?.childElementCount);
    await page.evaluate(() => {
      document.querySelector('#root').hidden = true;
      const host = document.createElement('main');
      host.id = 'all-model-mount-qa';
      host.className = 'lesson-media';
      host.style.cssText = 'max-width:1100px;margin:20px auto';
      document.body.append(host);
    });

    // Keep WebGL viewers sequential to avoid browser context limits. All other
    // models are mounted in six-item batches, never the entire curriculum at once.
    const regular = expectedModels.filter(record => record.item.renderer !== 'radiology-anatomy');
    const anatomy = expectedModels.filter(record => record.item.renderer === 'radiology-anatomy');
    for (let start = 0; start < regular.length; start += 6) {
      await mount(regular.slice(start, start + 6));
    }
    for (const record of anatomy) await mount([record]);
    await page.evaluate(() => {
      for (const model of document.querySelector('#all-model-mount-qa').children) model.dispose?.();
      document.querySelector('#all-model-mount-qa').replaceChildren();
    });
    assert.equal(evidence.models.length, expectedModels.length, 'Every interactive model mounted');
    assert.deepEqual(evidence.errors, [], 'No uncaught browser exceptions');
    for (const lesson of inventory) {
      const records = evidence.models.filter(record => record.lesson_id === lesson.id);
      assert.equal(records.length, lesson.models.length);
      evidence.lessons.push({ id: lesson.id, domain: lesson.domain, models: records.length,
        spatial: records.filter(record => ['spatial-3d', 'radiology-anatomy'].includes(record.renderer)).length });
    }
    evidence.summary = {
      lessons: evidence.lessons.length, subjects: new Set(inventory.map(lesson => lesson.domain)).size,
      mountedModels: evidence.models.length,
      spatialModels: evidence.lessons.reduce((total, lesson) => total + lesson.spatial, 0),
      spatialGeometryAndRotationChecks: evidence.models.filter(record => record.spatial).length,
      loadedAnatomicalViewers: evidence.models.filter(record => record.anatomy).length,
      rendererCounts: evidence.models.reduce((counts, model) => {
        counts[model.renderer] = (counts[model.renderer] || 0) + 1; return counts;
      }, {}),
    };
    fs.writeFileSync(path.join(output, 'all-model-mounts.json'), JSON.stringify(evidence, null, 2) + '\n');
    console.log('PASS every live model: ' + JSON.stringify(evidence.summary));

    async function mount(records) {
      const mounted = await page.evaluate(records => {
        const host = document.querySelector('#all-model-mount-qa');
        for (const previous of host.children) previous.dispose?.();
        host.replaceChildren();
        return records.map(({ lesson, item }, index) => {
          const model = window.PrimerLessonModels.render(item, {});
          if (!model) throw new Error(lesson.id + '/' + item.id + ': renderer returned no model');
          model.dataset.qaIndex = String(index);
          host.append(model);
          return { lesson_id: lesson.id, media_id: item.id, renderer: item.renderer,
            anatomy: model.classList.contains('detailed-anatomy'),
            spatial: model.classList.contains('spatial-model'),
            prenatal: model.classList.contains('prenatal-sequence') };
        });
      }, records);
      for (const [index, record] of mounted.entries()) {
        const model = page.locator('#all-model-mount-qa > [data-qa-index="' + index + '"]');
        if (record.anatomy) {
          await model.scrollIntoViewIfNeeded();
          await page.waitForFunction(index => {
            const model = document.querySelector('#all-model-mount-qa > [data-qa-index="' + index + '"]');
            return model?.dataset.error || (model?.dataset.ready === 'true' && model.querySelector('canvas')?.dataset.rendered === 'true');
          }, index, { timeout: 60000 });
          assert.equal(await model.getAttribute('data-error'), null, record.lesson_id + ': anatomy load succeeds');
          record.triangles = Number(await model.getAttribute('data-triangles'));
          assert.ok(record.triangles > 0, record.lesson_id + ': source triangles are rendered');
        }
        if (record.prenatal) {
          await model.locator('.prenatal-content').waitFor({ state: 'visible' });
          await model.locator('.prenatal-image-host img').evaluate(image => image.decode());
        }
        const result = await model.evaluate(model => {
          const shapeCount = model.querySelectorAll('svg polygon,svg polyline,svg path,svg circle,svg rect,svg line').length;
          const coordinates = [...model.querySelectorAll('svg *')].flatMap(element => [...element.attributes]
            .filter(attr => ['d', 'points', 'transform', 'x', 'y', 'x1', 'x2', 'y1', 'y2', 'cx', 'cy', 'r', 'width', 'height'].includes(attr.name))
            .map(attr => attr.value));
          const finite = coordinates.every(value => !/NaN|Infinity/.test(value));
          const controls = model.querySelectorAll('button,input,select').length;
          let rotation = null;
          if (model.classList.contains('spatial-model')) {
            const geometry = () => model.querySelector('svg g').innerHTML;
            const initial = geometry();
            [...model.querySelectorAll('button')].find(button => button.textContent === 'Rotate right').click();
            const changed = geometry() !== initial;
            [...model.querySelectorAll('button')].find(button => button.textContent === 'Reset view').click();
            rotation = { changed, reset: geometry() === initial };
          }
          return { shapeCount, controls, finite, rotation };
        });
        assert.ok(result.controls > 0, record.lesson_id + '/' + record.media_id + ': interactive controls mounted');
        assert.ok(result.finite, record.lesson_id + '/' + record.media_id + ': finite SVG geometry');
        if (record.spatial) {
          assert.ok(result.shapeCount > 0, record.lesson_id + ': spatial geometry mounted');
          assert.deepEqual(result.rotation, { changed: true, reset: true }, record.lesson_id + ': rotation and reset work');
        }
        evidence.models.push({ ...record, ...result });
      }
      if (evidence.models.length % 60 === 0) console.log('Mounted ' + evidence.models.length + '/' + expectedModels.length);
    }
  } catch (error) {
    evidence.failure = String(error.stack || error);
    fs.writeFileSync(path.join(output, 'all-model-mounts-failed.json'), JSON.stringify(evidence, null, 2) + '\n');
    if (page) await page.screenshot({ path: path.join(output, 'failure.png') }).catch(() => {});
    throw error;
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
