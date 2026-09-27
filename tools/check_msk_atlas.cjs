#!/usr/bin/env node
'use strict';

// Run only against an isolated loopback Primer server; creates a QA learner.
// NODE_PATH=/path/to/node_modules node tools/check_msk_atlas.cjs http://127.0.0.1:8782
// Add --routes-only to verify source figures and actual reporting-page atlas
// integration without repeating an unchanged six-region renderer sweep.
// --shoulder-only checks both shoulder galleries and the current knee source without repeating unrelated galleries.
// --elbow-only checks the eight elbow figures, including MRI/US and labelled dissection panels.
// --hip-knee-only checks both source galleries and the corrected hip guide; use check_openknee_browser.cjs for the new provider.
// --forefoot-spine-only checks the site- and modality-scoped forefoot/spine references.
// Evidence always uses a fresh private temporary directory. Other CLI paths are ignored.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const { createEvidenceDirectory, loopbackQaUrl } = require('./qa-browser.cjs');
const base = loopbackQaUrl(process.argv[2]);
const shoulderOnly = process.argv.includes('--shoulder-only');
const elbowOnly = process.argv.includes('--elbow-only');
const hipKneeOnly = process.argv.includes('--hip-knee-only');
const forefootSpineOnly = process.argv.includes('--forefoot-spine-only');
const focusedOnly = shoulderOnly || elbowOnly || hipKneeOnly || forefootSpineOnly;
const routesOnly = focusedOnly || process.argv.includes('--routes-only');
const out = createEvidenceDirectory();
const root = path.resolve(__dirname, '..');
const atlasFile = path.join(root, 'web/anatomy/msk-atlas/manifest.json');
const manifest = JSON.parse(fs.readFileSync(atlasFile));
const imageCatalog = JSON.parse(fs.readFileSync(path.join(root, 'data/radiology/msk-open-images.json')));
const sharing = JSON.parse(fs.readFileSync(path.join(root, 'data/radiology/msk-atlas-sharing.json')));
const reportingOverrides = JSON.parse(fs.readFileSync(path.join(root, 'data/radiology/investigation-overrides.json')));
const families = ['shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle'];
const digest = data => createHash('sha256').update(data).digest('hex');
const targets = {
  shoulder: [/^Glenoid labrum\.r$/],
  elbow: [/^Ulnar collateral ligament\.r$/, /^Annular ligament of radius\.r$/],
  wrist: [/^Articular disc of distal radio-ulnar joint\.r$/, /^Scapholunate interosseous ligament\.r$/],
  hip: [/^Acetabular labrum\.r$/],
  knee: [/^Medial meniscus\.r$/, /^Lateral meniscus\.r$/, /^Anterior cruciate ligament\.r$/, /^Posterior cruciate ligament\.r$/],
  ankle: [/^Anterior talofibular ligament\.r$/, /^Calcaneofibular ligament\.r$/, /^Posterior tibiotalar ligament\.r$/],
};
const evidence = {
  status: 'running', atlas: manifest.dataset, atlasStatus: manifest.status,
  disclaimer: 'Rendering and interaction QA only. Positive pixels, names and screenshots do not establish clinical fidelity, anatomical completeness or clinical approval. DRUJ disc evidence does not certify the entire TFCC.',
  sourceHashes: {}, regions: [], routeChecks: [], reportChecks: [], errors: [], failedLocalRequests: [],
};

(async () => {
  const browser = await chromium.launch({ headless: true });
  let page;
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1080 }, reducedMotion: 'reduce', hasTouch: true });
    const response = await context.request.post(base + '/api/profile', { data: {
      name: 'MSK atlas QA', age: 35, hours_per_week: 3, breadth: 'balanced', domains: ['radiology'],
    } });
    assert.equal(response.status(), 200, 'Isolated QA learner is available');
    await context.request.post(base + '/api/profile/settings', { data: { speak: false } });
    const files = ['app.js', 'styles.css', 'radiology-detailed-anatomy.js', 'anatomy/msk-atlas/manifest.json'];
    for (const file of files) {
      const served = await context.request.get(base + '/app/' + file);
      assert.equal(served.status(), 200, file + ': served');
      const hash = digest(await served.body());
      assert.equal(hash, digest(fs.readFileSync(path.join(root, 'web', file))), file + ': exact workspace source');
      evidence.sourceHashes[file] = hash;
    }
    page = await context.newPage();
    page.setDefaultTimeout(45000);
    page.on('pageerror', error => evidence.errors.push(error.message));
    page.on('response', response => {
      if ((response.url().startsWith(base + '/app/anatomy/msk-atlas/') || response.url().startsWith(base + '/app/reference-media/msk-open/')) && response.status() >= 400)
        evidence.failedLocalRequests.push({ url: response.url(), status: response.status() });
    });
    await page.goto(base + '/#/radiology');
    await page.locator('.rad-desk-catalog').waitFor();
    assert.equal(await page.evaluate(() => typeof window.PrimerDetailedAnatomy?.render), 'function');
    for (const family of routesOnly ? [] : families) {
      await page.setViewportSize({ width: 1440, height: 1080 });
      const region = manifest.regions[family];
      assert.ok(region && region.parts.length, family + ': populated manifest region');
      const parts = region.parts.map(part => ({ ...manifest.parts[part.id], ...part }));
      assert.deepEqual([...new Set(parts.map(part => part.layer))].sort(), region.layers.map(layer => layer[0]).sort(), family + ': every part layer has a filter');
      await page.evaluate(family => {
        document.querySelector('.detailed-anatomy')?.dispose();
        const model = window.PrimerDetailedAnatomy.render({ family, atlas: 'z-anatomy' });
        if (!model) throw new Error('Atlas renderer returned no model');
        document.querySelector('main').replaceChildren(model);
      }, family);
      const model = page.locator('.detailed-anatomy');
      await page.waitForFunction(() => {
        const model = document.querySelector('.detailed-anatomy');
        if (model?.dataset.error) throw new Error(model.querySelector('.detailed-anatomy-status').textContent);
        return model?.dataset.ready === 'true' && model.querySelector('canvas')?.dataset.rendered === 'true';
      }, null, { timeout: 90000 });
      await settled();
      assert.equal(await model.getAttribute('data-atlas'), 'z-anatomy');
      assert.equal(Number(await model.getAttribute('data-meshes')), parts.length);
      assert.match(await model.locator('.detailed-anatomy-note').innerText(), /CC BY-SA 4\.0/);
      const result = { family, meshes: parts.length, layers: [], isolated: [], orientation: [], screenshots: [] };
      evidence.regions.push(result);
      const canvas = model.locator('canvas');
      const button = name => model.getByRole('button', { name, exact: true });
      const orientation = model.locator('.detailed-anatomy-orientation');
      const capture = async suffix => {
        const filename = family + '-' + suffix + '.png';
        await model.locator('.detailed-anatomy-stage').screenshot({ path: path.join(out, filename), animations: 'disabled' });
        result.screenshots.push(filename);
      };
      const pixelStats = async label => {
        await settled();
        const colors = [...new Set(parts.filter(part => label === 'all' || part.layer === label).map(part => part.color))];
        const stats = await canvas.evaluate((canvas, colors) => {
          const gl = canvas.getContext('webgl');
          const pixels = new Uint8Array(canvas.width * canvas.height * 4);
          gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
          const chroma = rgb => { const low = Math.min(...rgb); const c = rgb.map(v => v - low); const sum = c.reduce((a, b) => a + b, 0); return sum ? c.map(v => v / sum) : [0, 0, 0]; };
          const expected = colors.filter(Boolean).map(value => chroma(value.match(/\w\w/g).map(v => parseInt(v, 16))));
          let solid = 0, chromatic = 0, sourceHue = 0, left = canvas.width, right = 0, top = canvas.height, bottom = 0;
          for (let i = 0; i < pixels.length; i += 4) {
            if (pixels[i + 3] <= 20) continue;
            solid++;
            const x = (i / 4) % canvas.width, y = Math.floor(i / 4 / canvas.width);
            left = Math.min(left, x); right = Math.max(right, x); top = Math.min(top, y); bottom = Math.max(bottom, y);
            const rgb = [pixels[i], pixels[i + 1], pixels[i + 2]];
            if (Math.max(...rgb) - Math.min(...rgb) > 8) {
              chromatic++;
              const c = chroma(rgb);
              if (expected.some(e => e.reduce((sum, value, index) => sum + Math.abs(value - c[index]), 0) < .25)) sourceHue++;
            }
          }
          return { solid, chromatic, sourceHue, glError: gl.getError(), width: canvas.width, height: canvas.height,
            bounds: solid ? { left, right, top, bottom } : null };
        }, colors);
        assert.equal(stats.glError, 0, family + '/' + label + ': WebGL error');
        assert.ok(stats.solid > 100, family + '/' + label + ': blank or insignificant geometry ' + JSON.stringify(stats));
        assert.ok(stats.sourceHue > 25, family + '/' + label + ': source material colors not visible ' + JSON.stringify(stats));
        return stats;
      };
      result.defaultPixels = await pixelStats('bone');
      await capture('default-desktop');
      for (const [layer, label] of region.layers) {
        await button(label).click();
        await page.waitForFunction(layer => document.querySelector('.detailed-anatomy canvas').dataset.layer === layer, layer);
        const visible = await model.locator('[data-part]:visible').evaluateAll(elements => elements.map(element => element.dataset.part).sort());
        assert.deepEqual(visible, parts.filter(part => part.layer === layer).map(part => part.id).sort(), family + '/' + layer + ': structure filter');
        const swatches = await model.locator('[data-part]:visible').evaluateAll(elements => elements.map(element => ({
          id: element.dataset.part, color: element.querySelector('.detailed-anatomy-swatch').style.backgroundColor,
        })));
        for (const swatch of swatches) {
          const hex = parts.find(part => part.id === swatch.id).color;
          const rgb = hex.match(/\w\w/g).map(value => parseInt(value, 16));
          assert.equal(swatch.color, 'rgb(' + rgb.join(', ') + ')', family + ': source swatch ' + swatch.id);
        }
        const stats = await pixelStats(layer);
        result.layers.push({ layer, label, visibleParts: visible.length, ...stats });
        await capture('layer-' + layer);
      }
      await button('Together').click();
      await settled();
      result.togetherPixels = await pixelStats('all');
      await capture('together-desktop');
      const croppedHash = await canvas.evaluate(canvas => canvas.toDataURL());
      await button('Full structures').click();
      await settled();
      assert.equal(await canvas.getAttribute('data-cropped'), 'false');
      assert.equal(await button('Full structures').getAttribute('aria-pressed'), 'true');
      assert.notEqual(await canvas.evaluate(canvas => canvas.toDataURL()), croppedHash, family + ': full/cropped geometry changes');
      result.fullPixels = await pixelStats('all');
      await capture('full-structures-desktop');
      await button('Full structures').click();
      await settled();
      assert.equal(await canvas.getAttribute('data-cropped'), 'true');
      const presets = [['Anterior', 'Anterior'], ['Posterior', 'Posterior'], ['Lateral', 'Right lateral'],
        ['Medial', 'Left lateral'], ['Superior', 'Superior'], ['Inferior', 'Inferior']];
      for (const [preset, label] of presets) {
        await button(preset).click();
        await settled();
        assert.equal(await orientation.textContent(), 'Right side · ' + label, family + ': exact ' + preset + ' label');
        result.orientation.push({ preset, label: await orientation.textContent(), view: await canvas.getAttribute('data-view') });
      }
      await button('Anterior').click(); await settled();
      await canvas.focus(); await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowDown'); await settled();
      assert.equal(await orientation.textContent(), 'Right side · Rotated view · yaw 9° · tilt 9°', family + ': keyboard orientation');
      await button('Anterior').click(); await settled();
      await canvas.scrollIntoViewIfNeeded();
      const box = await canvas.boundingBox(), x = Math.round(box.x + box.width * .48), y = Math.round(box.y + box.height * .45);
      const beforeDrag = await canvas.evaluate(canvas => canvas.toDataURL());
      await page.mouse.move(x, y); await page.mouse.down(); await page.mouse.move(x + 50, y + 20, { steps: 5 }); await page.mouse.up(); await settled();
      assert.equal(await orientation.textContent(), 'Right side · Rotated view · yaw 26° · tilt 10°', family + ': mouse orientation');
      assert.notEqual(await canvas.evaluate(canvas => canvas.toDataURL()), beforeDrag, family + ': pointer changes projection');
      await capture('rotated-desktop');
      await button('Anterior').click(); await settled();
      const cartilage = parts.find(part => part.layer === 'cartilage-surface' && /humerus|scapula|femur|tibia|talus|radius|lunate/i.test(part.name))
        || parts.find(part => part.layer === 'cartilage-surface');
      assert.ok(cartilage, family + ': cartilage material submesh');
      await model.locator('[data-part="' + cartilage.id + '"]').click(); await settled();
      await capture('cartilage-in-context');
      await button('Reset').click(); await settled();
      for (const pattern of targets[family]) {
        const part = parts.find(part => pattern.test(part.name));
        assert.ok(part, family + ': missing focused soft-tissue target ' + pattern);
        await button('Together').click(); await settled();
        await model.locator('[data-part="' + part.id + '"]').click();
        await button('Isolate').click(); await settled();
        assert.equal(await button('Isolate').getAttribute('aria-pressed'), 'true');
        assert.equal(await button('Full structures').getAttribute('aria-pressed'), 'true');
        assert.equal(await canvas.getAttribute('data-cropped'), 'false', family + ': isolated structure is complete');
        assert.equal(await model.locator('[data-part="' + part.id + '"]').getAttribute('aria-pressed'), 'true');
        const stats = await pixelStats('all');
        result.isolated.push({ id: part.id, name: part.name, layer: part.layer,
          sourceTriangles: part.triangles, sourceVertices: part.vertices, ...stats });
        await capture('isolated-' + part.id + '-desktop');
        await page.setViewportSize({ width: 390, height: 844 }); await settled();
        await noOverflow(family + ': mobile isolated');
        await capture('isolated-' + part.id + '-mobile');
        await page.setViewportSize({ width: 1440, height: 1080 });
        await button('Reset').click(); await settled();
      }
      await page.setViewportSize({ width: 390, height: 844 }); await settled();
      await noOverflow(family + ': mobile default'); await pixelStats('bone'); await capture('default-mobile');
      await button('Together').click(); await settled(); await noOverflow(family + ': mobile together');
      await pixelStats('all'); await capture('together-mobile');
      await button('Reset').click(); await settled();
      assert.equal(await canvas.getAttribute('data-layer'), 'bone');
      assert.equal(await canvas.getAttribute('data-cropped'), 'true');
      assert.equal(await canvas.getAttribute('data-view'), '-0.22,0.10');
      console.log('PASS ' + family + ': ' + result.layers.length + ' layers; ' + result.isolated.length + ' focused soft tissues; orientation, crop, colors, mobile');
      fs.writeFileSync(path.join(out, 'progress.json'), JSON.stringify(evidence, null, 2) + '\n');
    }

    // Exercise the actual application paths as well as the direct renderer.
    // Metadata determines all expected figures, so a larger source selection
    // automatically extends these checks without a fixed figure-count claim.
    const routes = forefootSpineOnly ? [['ra.mri-diabetic-foot', 'ankle'], ['ra.thoracolumbar-fractures', 'spine']] : hipKneeOnly ? [['ra.mri-knee', 'knee'], ['ra.hip-fai', 'hip']] : elbowOnly ? [['ra.mri-elbow', 'elbow']] : shoulderOnly ? [['ra.mri-shoulder', 'shoulder'], ['ra.ultrasound-shoulder', 'shoulder']] :
      [['ra.mri-shoulder', 'shoulder'], ['ra.mri-elbow', 'elbow'], ['ra.wrist-instability', 'wrist'],
      ['ra.mri-knee', 'knee'], ['ra.hip-fai', 'hip'], ['ra.mri-ankle', 'ankle'], ['ra.mri-diabetic-foot', 'ankle'], ['ra.thoracolumbar-fractures', 'spine']];
    for (const [id, family] of routes) {
      const response = await context.request.get(base + '/api/radiology/modules/' + id);
      assert.equal(response.status(), 200, id + ': investigation API');
      const detail = await response.json(), ref = detail.radiology_reference;
      const assets = ref.structure_atlas || [];
      const shared = sharing[id];
      const expectedAssets = typeof shared === 'string' ? imageCatalog[shared]
        : shared ? shared.include_ids.map(id => imageCatalog[shared.source].find(asset => asset.id === id)) : imageCatalog[id];
      assert.deepEqual(assets, expectedAssets, id + ': API figure metadata matches the current scoped source catalogue');
      if (id === 'ra.ultrasound-shoulder') {
        assert.equal(assets.length, 3);
        assert.ok(assets.every(asset => ['Ultrasound', 'Schematic'].includes(asset.modality)), 'MRI/arthrography scans are not copied to the ultrasound source gallery');
        assert.equal(assets.filter(asset => asset.modality === 'Ultrasound').length, 1);
      }
      if (focusedOnly) assert.deepEqual(ref.reporting, reportingOverrides[id].reporting, id + ': source guide remains investigation-specific');
      assert.ok(assets.some(asset => asset.kind === 'clinical-image'), id + ': source clinical anatomy supplied');
      assert.equal((ref.anatomical_illustrations || []).length, 0, id + ': generated bone pictures removed from the MSK desk');
      const checked = { id, family, figures: [], modelAtlas: null };
      evidence.routeChecks.push(checked);
      await page.setViewportSize({ width: 1440, height: 1080 });
      await page.goto(base + '/#/radiology/' + id);
      await page.waitForFunction(title => document.querySelector('.pagehead h2')?.textContent === title, detail.title);
      if (focusedOnly) {
        const guideText = await page.locator('.rad-reporting-guide').innerText();
        for (const item of ref.reporting.checklist) assert.ok(guideText.includes(item.label) && guideText.includes(item.detail), id + ': actual guide preserves its own checklist');
        if (hipKneeOnly && id === 'ra.hip-fai') {
          assert.match(guideText, /compatible symptoms, examination signs and imaging findings/);
          assert.match(guideText, /If MRI was acquired/);
          assert.doesNotMatch(guideText, /require labral and cartilage injury|must.*labral.*cartilage.*injury/i);
        }
      }
      for (const [kind, tabName] of [['clinical-image', /^Images \(/], ['schematic', 'Diagram']]) {
        await page.getByRole('tab', { name: tabName }).click();
        const active = page.locator('.rad-desk-panel:not([hidden])');
        const relevant = assets.filter(asset => asset.kind === kind || (kind === 'schematic' && asset.contains_schematic_panels));
        assert.equal(await active.locator('.rad-structure-atlas figure').count(), relevant.length, id + ': figures in correct ' + kind + ' pane');
        assert.equal(await active.locator('.lesson-photograph').count(), 0, id + ': no AI equipment scene in reporting panes');
        assert.doesNotMatch(await active.innerText(), /Generated anatomical illustration/);
        for (const asset of relevant) {
          const image = active.locator('.rad-structure-atlas img[src="' + asset.src + '"]');
          const figure = image.locator('..');
          assert.ok(asset.modality, id + ': source modality is explicit');
          const ancillary = asset.ancillary_panels || [];
          const modality = asset.modality + (asset.contains_schematic_panels ? ' + schematic panels' : '')
            + [...new Set(ancillary.map(entry => entry.kind.toLowerCase()))].map(kind => ' + ' + kind + ' panels').join('');
          const derived = asset.origin === 'source-derived';
          const figureTitle = derived ? asset.figure_title : 'Figure ' + asset.figure_number + (asset.source_panel || '');
          assert.equal(await figure.locator('h4').textContent(), figureTitle + ' · ' + modality, id + ': exact source identity and modality heading');
          await image.scrollIntoViewIfNeeded();
          await image.evaluate(image => image.decode());
          assert.equal(await image.getAttribute('data-full-src'), asset.src, id + ': source resolution retained');
          assert.equal(await image.getAttribute('role'), 'button', id + ': keyboard image opener');
          const dimensions = await image.evaluate(image => ({ width: image.naturalWidth, height: image.naturalHeight }));
          assert.deepEqual(dimensions, { width: asset.width, height: asset.height }, id + ': native figure dimensions');
          if (elbowOnly && asset.id === 'open-elbow-triceps-insertion-mri-valgaeren-fig2') {
            const pixels = await image.evaluate(image => {
              const canvas = document.createElement('canvas'); canvas.width = image.naturalWidth; canvas.height = image.naturalHeight;
              const context = canvas.getContext('2d'); context.drawImage(image, 0, 0);
              const data = context.getImageData(0, 0, canvas.width, canvas.height).data;
              let yellow = 0, black = 0, white = 0, midGray = 0;
              for (let i = 0; i < data.length; i += 4) { const [r, g, b] = data.slice(i, i + 3);
                if (r > 150 && g > 120 && b < 110 && r - b > 50 && g - b > 40) yellow++;
                if (Math.max(r, g, b) < 20) black++;
                if (Math.min(r, g, b) > 235) white++;
                if (Math.max(r, g, b) - Math.min(r, g, b) < 12 && r > 40 && r < 215) midGray++;
              }
              return { yellow, black, white, midGray, pixels: canvas.width * canvas.height };
            });
            assert.ok(pixels.yellow > 20 && pixels.midGray > 1000 && pixels.black > 1000, 'Browser preserves yellow arrows and MRI grayscale from the source PDF colour rendition');
            evidence.cmykRendering = { id: asset.id, ...dimensions, ...pixels, sha256: asset.sha256 };
          }

          const caption = await figure.locator('figcaption').textContent();
          assert.ok(caption.includes(asset.caption) && caption.includes(asset.attribution) && caption.includes(asset.limits), id + ': caption, attribution and coverage limits retained');
          const captionRows = await figure.locator('figcaption > p').allTextContents();
          const imagingLead = asset.contains_schematic_panels ? 'Identified in imaging panels: ' : 'Identified in this figure: ';
          assert.ok(captionRows.includes(imagingLead + asset.structures_visible.join('; ') + '.'), id + ': exact imaging/figure structure scope');
          if (asset.contains_schematic_panels) {
            assert.equal(asset.kind, 'clinical-image', id + ': mixed source figure belongs in Images');
            assert.ok(asset.schematic_structures_visible?.length, id + ': mixed figure has separate schematic metadata');
            assert.ok(captionRows.includes('Identified in schematic panels: ' + asset.schematic_structures_visible.join('; ') + '.'), id + ': schematic structures are not merged into imaging coverage');
          }
          for (const entry of ancillary) {
            assert.ok(['Dissection', 'Histology'].includes(entry.kind));
            const lead = 'Identified in ' + entry.kind.toLowerCase() + ' panels (' + entry.panels.join(', ') + '): ';
            assert.ok(captionRows.includes(lead + entry.structures_visible.join('; ') + '. ' + entry.limits), id + ': ancillary panel identity, anatomy and limits stay distinct from imaging coverage');
            assert.ok(entry.panels.every(panel => !(asset.clinical_panels || []).includes(panel)), id + ': ancillary panels are not labelled clinical MRI');
          }
          if (id === 'ra.mri-diabetic-foot') {
            assert.match(asset.limits, /does not depict infection|not.*infection|anatomical adjunct/i);
            if (asset.anatomical_digit === 1 && asset.modality === 'MRI') {
              assert.equal(asset.image_state, 'cadaveric normal anatomy study');
              assert.deepEqual(asset.clinical_panels, ['c', 'd']);
              assert.match(asset.limits, /specimen/i);
            }
            if (asset.id === 'open-lesser-mtp3-plantar-plate-mri-siddle-fig1') {
              assert.equal(asset.anatomical_digit, 3);
              assert.deepEqual(asset.clinical_panels, ['a', 'b']);
            }
            if (asset.id === 'open-forefoot-second-fdl-ultrasound-chen-fig7c') {
              assert.equal(asset.anatomical_digit, 2);
              assert.equal(asset.modality, 'Ultrasound');
              assert.equal(asset.source_panel, 'c');
            }
          }
          if (asset.source_panel) assert.ok(asset.source_caption_full, id + ': extracted panel retains its complete source caption');
          if (asset.source_caption_full && asset.source_caption_full !== asset.caption) {
            const disclosure = figure.locator('.rad-source-caption');
            await disclosure.locator('summary').focus(); await page.keyboard.press('Enter');
            assert.equal(await disclosure.getAttribute('open'), '', id + ': complete caption expands by keyboard');
            assert.equal(await disclosure.locator('p').textContent(), asset.source_caption_full);
            await disclosure.locator('summary').focus(); await page.keyboard.press('Enter');
            assert.equal(await disclosure.getAttribute('open'), null);
          }
          assert.equal(await figure.getByRole('link', { name: asset.license, exact: true }).getAttribute('href'), asset.license_url);
          assert.equal(await figure.getByRole('link', { name: derived ? 'Source dataset' : 'Source article', exact: true }).getAttribute('href'), asset.source_url);
          assert.equal(await figure.getByRole('link', { name: derived ? 'Source geometry' : 'Original figure', exact: true }).getAttribute('href'), asset.figure_url);
          const accessibleName = await image.getAttribute('aria-label');
          assert.ok(!accessibleName.includes(asset.caption + 'Identified'), id + ': caption blocks have readable spacing');
          const bytes = await context.request.get(base + asset.src);
          assert.equal(bytes.status(), 200, id + ': figure source loads locally');
          assert.equal(digest(await bytes.body()), asset.sha256, id + ': figure bytes match recorded checksum');
          if (asset.license === 'CC BY-ND 4.0') {
            const original = await bytes.body();
            assert.equal(createHash('md5').update(original).digest('hex'), asset.source_bytes_md5, asset.id + ': exact original NLM MD5');
            assert.equal(digest(original), asset.source_bytes_sha256, asset.id + ': exact original source SHA');
            assert.equal(asset.license_use_plan.mode, 'unchanged_complete_figure');
            assert.equal(asset.license_use_plan.preserve_all_panels, true);
            assert.ok(!asset.source_panel, 'Unchanged ND figures retain all source panels');
            evidence.unchangedNdFigures = [...(evidence.unchangedNdFigures || []), { id: asset.id, sha256: asset.source_bytes_sha256, md5: asset.source_bytes_md5, ...dimensions }];
          }
          if (asset.id === 'open-hip-gluteus-minimus-comparison-mri-amin-fig3') {
            assert.match(caption, /LEFT/); assert.match(caption, /RIGHT/);
            assert.equal(asset.normal_reference_selection.laterality, 'left');
            assert.equal(asset.normal_reference_selection.panel, 'a');
          }

          assert.equal(await image.getAttribute('data-source-figure'), 'true', 'Source figure retains its appearance marker');
          assert.equal(await image.evaluate(image => getComputedStyle(image).filter), 'none', 'Reading theme does not alter medical source pixels');
          await image.focus(); await page.keyboard.press('Enter');
          const dialog = page.getByRole('dialog'); await dialog.waitFor();
          const large = dialog.locator('.lightbox img'); await large.evaluate(image => image.decode());
          assert.equal(await large.evaluate(image => getComputedStyle(image).filter), 'none', 'Enlargement does not dim, invert or recolour source figures');
          assert.deepEqual(await large.evaluate(image => ({ width: image.naturalWidth, height: image.naturalHeight })), dimensions);
          await dialog.getByRole('button', { name: 'Read labels at full size', exact: true }).click();
          assert.equal(await dialog.locator('.lightbox-zoom').getAttribute('aria-pressed'), 'true');
          assert.equal(await dialog.locator('.lightbox-image-scroll').getAttribute('tabindex'), '0');
          if (elbowOnly || hipKneeOnly || forefootSpineOnly || asset.source_panel || asset.contains_schematic_panels)
            await dialog.screenshot({ path: path.join(out, id + '-' + asset.id + '-' + kind + '-native-zoom.png'), animations: 'disabled' });
          await page.keyboard.press('Escape'); await dialog.waitFor({ state: 'hidden' });
          assert.ok(await image.evaluate(image => document.activeElement === image), id + ': Escape restores figure focus');
          const fileStem = id + '-' + asset.id + '-' + kind;
          await image.scrollIntoViewIfNeeded();
          await page.screenshot({ path: path.join(out, fileStem + '-desktop.png'), animations: 'disabled' });
          await page.setViewportSize({ width: 390, height: 844 }); await settled();
          await noOverflow(id + ': source figure mobile');
          await image.scrollIntoViewIfNeeded();
          await page.screenshot({ path: path.join(out, fileStem + '-mobile.png'), animations: 'disabled' });
          checked.figures.push({ id: asset.id, kind: asset.kind, pane: kind, modality: asset.modality, sourcePanel: asset.source_panel || null,
            mixedPanels: Boolean(asset.contains_schematic_panels), imagingStructures: asset.structures_visible,
            ancillaryPanels: asset.ancillary_panels || [], clinicalPanels: asset.clinical_panels || [],
            schematicStructures: asset.schematic_structures_visible || [], completeCaptionAvailable: Boolean(asset.source_caption_full),
            src: asset.src, ...dimensions, checksum: asset.sha256, zoom: true, licenseVisible: true, mobile: true });
          if (ancillary.length) {
            await figure.locator('figcaption > p').filter({ hasText: imagingLead }).evaluate(element => element.scrollIntoView({ block: 'start', behavior: 'instant' }));
            await page.screenshot({ path: path.join(out, fileStem + '-panel-scope-mobile.png'), animations: 'disabled' });
          }
          await page.setViewportSize({ width: 1440, height: 1080 });
          if (ancillary.length) {
            await figure.locator('figcaption > p').filter({ hasText: imagingLead }).evaluate(element => element.scrollIntoView({ block: 'center', behavior: 'instant' }));
            await page.screenshot({ path: path.join(out, fileStem + '-panel-scope-desktop.png'), animations: 'disabled' });
          }
        }
      }
      if (hipKneeOnly && id === 'ra.hip-fai') {
        await page.getByRole('tab', { name: 'Report template', exact: true }).click();
        const text = await page.locator('.rad-report-editor').first().inputValue();
        for (const section of ref.reporting.template_sections) assert.ok(text.includes(section.heading) && text.includes(section.body));
        checked.reportTemplatePreserved = true;
      }
      if (focusedOnly || family === 'spine') {
        console.log('PASS focused source gallery ' + id + ': ' + checked.figures.length + ' credited pane placements; native pixels, guide, keyboard zoom and mobile');
        continue;
      }
      await page.getByRole('tab', { name: '3D anatomy', exact: true }).click();
      if (family === 'knee') {
        const source = page.getByRole('combobox', { name: 'Knee anatomy source', exact: true });
        assert.equal(await source.inputValue(), 'malaya-mri', 'The actual knee default remains the MRI-derived provider');
        await source.selectOption('z-anatomy');
      }
      const liveModel = page.locator('.rad-desk-panel:not([hidden]) .detailed-anatomy');
      await liveModel.waitFor();
      assert.equal(await liveModel.getAttribute('data-family'), family, id + ': actual model family including aliases');
      assert.equal(await liveModel.getAttribute('data-atlas'), 'z-anatomy', id + ': actual page uses the expanded atlas');
      await page.waitForFunction(() => document.querySelector('.rad-desk-panel:not([hidden]) .detailed-anatomy')?.dataset.ready === 'true');
      if (id === 'ra.mri-diabetic-foot') {
        assert.equal(await liveModel.getAttribute('data-view-preset'), 'whole-foot');
        assert.match(await liveModel.locator('h3').textContent(), /Adult right foot/);
        checked.modelView = 'whole-foot';
      }
      checked.modelAtlas = await liveModel.getAttribute('data-atlas');
      checked.meshes = Number(await liveModel.getAttribute('data-meshes'));
      assert.equal(checked.meshes, manifest.regions[family].parts.length);
      await page.setViewportSize({ width: 390, height: 844 }); await settled();
      await noOverflow(id + ': actual model mobile');
      await liveModel.locator('.detailed-anatomy-stage').screenshot({ path: path.join(out, id + '-actual-model-mobile.png'), animations: 'disabled' });
      console.log('PASS actual route ' + id + ': ' + checked.figures.length + ' credited figure placements, keyboard zoom and ' + checked.modelAtlas + '/' + family);
    }
    const checkedSources = forefootSpineOnly ? [...imageCatalog['ra.mri-diabetic-foot'], ...imageCatalog['ra.thoracolumbar-fractures']] : hipKneeOnly ? [...imageCatalog['ra.mri-knee'], ...imageCatalog['ra.hip-fai']] : elbowOnly ? imageCatalog['ra.mri-elbow'] : shoulderOnly ? imageCatalog['ra.mri-shoulder'] : Object.values(imageCatalog).flat();
    assert.deepEqual([...new Set(evidence.routeChecks.flatMap(route => route.figures.map(figure => figure.id)))].sort(),
      checkedSources.map(figure => figure.id).sort(), 'Every source in the selected QA scope is exercised');
    evidence.sourceFigureCount = checkedSources.length;
    evidence.figurePlacementCount = evidence.routeChecks.reduce((sum, route) => sum + route.figures.length, 0);
    evidence.scope = forefootSpineOnly ? 'Forefoot and thoracolumbar source figures with actual digit, modality and normality limits' : hipKneeOnly ? 'Knee and hip source figures, including unchanged ND originals, mixed panels, MRA and source-local intact anatomy' : elbowOnly ? 'Eight elbow source figures and their explicit MRI/US/schematic/dissection context' : shoulderOnly ? 'MRI shoulder and selectively shared ultrasound shoulder galleries, plus knee source smoke check' : 'All primary source galleries';
    if (!shoulderOnly) assert.equal(evidence.figurePlacementCount, checkedSources.reduce((sum, figure) => sum + (figure.contains_schematic_panels ? 2 : 1), 0));

    if (!focusedOnly) {
    // The report editors must expose the corrected effective guide, including
    // explicit absent/unknown states, without regaining their old boilerplate.
    for (const id of ['ra.thoracolumbar-fractures', 'ra.ankle-fractures']) {
      const detail = await (await context.request.get(base + '/api/radiology/modules/' + id)).json();
      await page.goto(base + '/#/radiology/' + id);
      await page.waitForFunction(title => document.querySelector('.pagehead h2')?.textContent === title, detail.title);
      const guide = await page.locator('.rad-reporting-guide').textContent();
      for (const item of detail.radiology_reference.reporting.checklist) assert.ok(guide.includes(item.label) && guide.includes(item.detail));
      await page.getByRole('tab', { name: 'Report template', exact: true }).click();
      const report = await page.locator('.rad-report-editor').first().inputValue();
      for (const section of detail.radiology_reference.reporting.template_sections)
        assert.ok(report.includes(section.heading) && report.includes(section.body), id + ': corrected finding section reaches the editor');
      if (id === 'ra.thoracolumbar-fractures') {
        assert.doesNotMatch(report, /LEVEL-BY-LEVEL DEGENERATION/);
        assert.match(report, /POSTERIOR TENSION BAND/);
        assert.match(report, /clinical neurological status \[not supplied/i);
        assert.match(report, /not assigned because required inputs are missing/);
      } else {
        assert.match(report, /not directly assessed on radiographs/);
        assert.match(report, /supplemental MRI\/ultrasound \[not obtained/i);
        assert.match(report, /proximal fibula \[not imaged/i);
        assert.match(report, /FOOT AND HINDFOOT COVERAGE/);
      }
      await page.setViewportSize({ width: 390, height: 844 }); await settled(); await noOverflow(id + ': corrected report mobile');
      await page.locator('.rad-report-editor').first().scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(out, id + '-corrected-report-mobile.png'), animations: 'disabled' });
      evidence.reportChecks.push({ id, actualTemplateMatchesGuide: true, clinicalAndModalityLimits: true, mobile: true });
    }

    await page.goto(base + '/#/radiology/ra.paediatric-elbow-fractures');
    await page.locator('.rad-reporting-desk').waitFor();
    const guide = await page.locator('.rad-reporting-guide').innerText();
    assert.match(guide, /Elbow alignment/);
    assert.doesNotMatch(guide, /\bDDH\b|\bGraf\b|Hip plane|Hip development|Painful hip/i);
    await page.getByRole('tab', { name: 'Report template', exact: true }).click();
    const report = await page.locator('.rad-report-editor').first().inputValue();
    assert.match(report, /FRACTURE MORPHOLOGY/);
    assert.doesNotMatch(report, /\bDDH\b|\bGraf\b|\bhip\b/i);
    await page.getByRole('tab', { name: /3D anatomy|Spatial guide/ }).click();
    const paediatricModel = page.locator('.rad-desk-panel:not([hidden]) .detailed-anatomy');
    await paediatricModel.waitFor();
    assert.equal(await paediatricModel.getAttribute('data-family'), 'elbow');
    assert.equal(await paediatricModel.getAttribute('data-atlas'), 'z-anatomy');
    assert.match(await paediatricModel.innerText(), /Adult elbow reference only/);
    assert.match(await paediatricModel.innerText(), /ossification centres/);
    await page.waitForFunction(() => document.querySelector('.rad-desk-panel:not([hidden]) .detailed-anatomy')?.dataset.ready === 'true');
    await noOverflow('Paediatric elbow mobile');
    await page.screenshot({ path: path.join(out, 'paediatric-elbow-model-mobile.png'), animations: 'disabled' });
    evidence.paediatricElbow = { guideScoped: true, templateScoped: true, modelFamily: 'elbow', modelAtlas: 'z-anatomy', ageLimitationVisible: true };
    const spectRegistry = JSON.parse(fs.readFileSync(path.join(root, 'data/radiology/local-source-figures.json')));
    const spectPath = '/app/reference-media/source-figures/spect-ct-fusion.jpg';
    const spectSource = spectRegistry[spectPath];
    const spectNode = await (await context.request.get(base + '/api/curriculum/node/rad.5.nuclear-general')).json();
    const spect = spectNode.radiology_reference.key_images.find(item => item.src === spectPath);
    assert.ok(spect, 'Nuclear module API uses the pinned local SPECT/CT image');
    assert.match(spect.caption, /teaching composite/);
    assert.match(spect.caption, /Original 487×544 source pixels/);
    await page.setViewportSize({ width: 1440, height: 1080 });
    await page.goto(base + '/#/node/rad.5.nuclear-general');
    const spectImage = page.locator('.rad-image-example img[src="' + spectPath + '"]');
    await spectImage.waitFor();
    await spectImage.scrollIntoViewIfNeeded(); await spectImage.evaluate(image => image.decode());
    assert.deepEqual(await spectImage.evaluate(image => ({ width: image.naturalWidth, height: image.naturalHeight })), { width: 487, height: 544 });
    const spectFigure = spectImage.locator('xpath=ancestor::figure[1]');
    const spectCaption = await spectFigure.locator('figcaption').textContent();
    assert.ok(spectCaption.includes(spect.caption) && spectCaption.includes(spectSource.attribution));
    assert.equal(await spectFigure.getByRole('link', { name: spect.license, exact: true }).getAttribute('href'), spectSource.license_url);
    assert.equal(await spectFigure.getByRole('link', { name: 'Source and case details for ' + spect.label, exact: true }).getAttribute('href'), spect.source_url);
    const spectBytes = await context.request.get(base + spectPath);
    assert.equal(spectBytes.status(), 200);
    assert.equal(digest(await spectBytes.body()), spectSource.sha256);
    await spectImage.focus(); await page.keyboard.press('Enter');
    const spectDialog = page.getByRole('dialog'); await spectDialog.waitFor();
    await spectDialog.locator('.lightbox img').evaluate(image => image.decode());
    await spectDialog.getByRole('button', { name: 'Read labels at full size', exact: true }).click();
    assert.equal(await spectDialog.locator('.lightbox-zoom').getAttribute('aria-pressed'), 'true');
    await page.screenshot({ path: path.join(out, 'spect-ct-native-zoom-desktop.png'), animations: 'disabled' });
    await page.keyboard.press('Escape'); await spectDialog.waitFor({ state: 'hidden' });
    assert.ok(await spectImage.evaluate(image => document.activeElement === image));
    await page.setViewportSize({ width: 390, height: 844 }); await settled(); await noOverflow('SPECT/CT mobile');
    await spectFigure.evaluate(element => element.scrollIntoView({ block: 'center', behavior: 'instant' }));
    await page.screenshot({ path: path.join(out, 'spect-ct-local-source-mobile.png'), animations: 'disabled' });
    evidence.spectTeachingComposite = { route: 'rad.5.nuclear-general', src: spectPath, sha256: spectSource.sha256,
      width: 487, height: 544, attribution: spectSource.attribution, license: spectSource.license,
      caption: spect.caption, keyboardZoom: true, mobile: true, anatomicalAtlasClaim: false };

    }
    if (shoulderOnly) {
      const kneeFile = 'anatomy/msk-mri-knee/manifest.json';
      const served = await context.request.get(base + '/app/' + kneeFile);
      const knee = await served.json();
      const manifestHash = digest(fs.readFileSync(path.join(root, 'web', kneeFile)));
      assert.equal(digest(await served.body()), manifestHash);
      evidence.sourceHashes[kneeFile] = manifestHash;
      files.push(kneeFile);
      assert.equal(knee.clinical_image_pair.available, false);
      assert.equal(knee.clinical_image_pair.independent_clinical_validation, false);
      assert.match(knee.source_image_correspondence.status, /offline_research_only/);
      const rawPattern = /\.(?:nrrd|nii|dcm|dicom|mha|mhd|raw|nifti)(?:\.gz)?(?:$|[?#])/i;
      const rawFiles = [];
      function walk(directory) {
        for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
          const file = path.join(directory, entry.name);
          if (entry.isDirectory()) walk(file);
          else if (rawPattern.test(file)) rawFiles.push(file);
        }
      }
      walk(path.join(root, 'web'));
      assert.deepEqual(rawFiles, [], 'Raw scan/reference volumes are outside the static web tree');
      const scanRequests = [];
      page.on('request', request => { if (rawPattern.test(request.url())) scanRequests.push(request.url()); });
      await page.setViewportSize({ width: 1440, height: 1080 });
      await page.goto(base + '/#/radiology/ra.mri-knee');
      await page.getByRole('tab', { name: '3D anatomy', exact: true }).click();
      assert.equal(await page.getByRole('combobox', { name: 'Knee anatomy source', exact: true }).inputValue(), 'malaya-mri');
      await page.waitForFunction(() => { const model = document.querySelector('.rad-desk-panel:not([hidden]) .detailed-anatomy');
        return model?.dataset.ready === 'true' && model.querySelector('canvas')?.dataset.rendered === 'true'; });
      const model = page.locator('.rad-desk-panel:not([hidden]) .detailed-anatomy');
      assert.equal(await model.getAttribute('data-atlas'), 'malaya-mri');
      const displayed = knee.regions.knee.parts.flatMap(entry => { const part = { ...knee.parts[entry.id], ...entry }; return part.components?.length ? part.components : [part]; });
      assert.equal(Number(await model.getAttribute('data-meshes')), displayed.length);
      assert.equal(displayed.length, 30);
      assert.match(await model.innerText(), /independent clinical fidelity review/);
      const stats = await model.locator('canvas').evaluate(canvas => { const gl = canvas.getContext('webgl'), data = new Uint8Array(canvas.width * canvas.height * 4);
        gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, data); let pixels = 0;
        for (let i = 3; i < data.length; i += 4) if (data[i] > 20) pixels++; return { pixels, error: gl.getError() }; });
      assert.equal(stats.error, 0); assert.ok(stats.pixels > 100);
      await model.locator('.detailed-anatomy-stage').evaluate(element => element.scrollIntoView({ block: 'center', behavior: 'instant' }));
      await page.screenshot({ path: path.join(out, 'knee-current-source-default.png'), animations: 'disabled' });
      await page.getByRole('tab', { name: /^Images \(/ }).click();
      const sourceImages = await page.locator('.rad-desk-panel:not([hidden]) img').evaluateAll(images => images.map(image => image.getAttribute('src')));
      assert.ok(sourceImages.length && sourceImages.every(src => !rawPattern.test(src)));
      assert.deepEqual(scanRequests, [], 'Viewer/image pane does not fetch any research scan volume');
      evidence.kneeSourceSmoke = { atlas: 'malaya-mri', objects: displayed.length, ...stats,
        rawStaticFiles: 0, rawScanRequests: 0, diagnosticPairOffered: false, imageSources: sourceImages,
        sourceCorrespondenceStatus: knee.source_image_correspondence.status };
    }
    for (const file of files) {
      assert.equal(digest(fs.readFileSync(path.join(root, 'web', file))), evidence.sourceHashes[file], file + ': source changed during QA; repeat against frozen files');
    }
    assert.deepEqual(evidence.errors, [], 'No uncaught JavaScript errors');
    assert.deepEqual(evidence.failedLocalRequests, [], 'No local atlas fetch failures');
    evidence.status = 'passed';
    fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(evidence, null, 2) + '\n');
    console.log('PASS MSK atlas QA: ' + evidence.regions.length + ' direct-rendered regions; ' + evidence.routeChecks.length + ' actual figure/model routes; ' + evidence.regions.reduce((sum, region) => sum + region.layers.length, 0) + ' layer checks; ' + evidence.regions.reduce((sum, region) => sum + region.isolated.length, 0) + ' focused isolated structures. Evidence: ' + out);

    async function settled() { await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))); }
    async function noOverflow(label) {
      const bounds = await page.evaluate(() => ({ width: innerWidth, page: document.documentElement.scrollWidth,
        models: [...document.querySelectorAll('.detailed-anatomy')].filter(element => element.getBoundingClientRect().width).map(element => ({ width: element.clientWidth, scroll: element.scrollWidth })) }));
      assert.ok(bounds.page <= bounds.width + 1 && bounds.models.every(model => model.scroll <= model.width + 1), label + ': horizontal overflow ' + JSON.stringify(bounds));
    }
  } catch (error) {
    evidence.status = 'failed'; evidence.failure = String(error.stack || error);
    if (page) await page.screenshot({ path: path.join(out, 'failure.png') }).catch(() => {});
    fs.writeFileSync(path.join(out, 'failure.json'), JSON.stringify(evidence, null, 2) + '\n');
    throw error;
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
