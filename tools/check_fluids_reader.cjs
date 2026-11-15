'use strict';
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const {chromium} = require('playwright');
const fixture = JSON.parse(fs.readFileSync(0, 'utf8')), origin = new URL(fixture.url);
assert.equal(origin.hostname, '127.0.0.1'); assert.equal(origin.protocol, 'http:');
assert.equal(origin.pathname, '/'); assert.equal(origin.username, ''); assert.equal(origin.password, '');
const base = origin.origin, root = path.resolve(__dirname, '..'), out = path.join(root, 'docs/fluids-fidelity-review-20261016/reader');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const fileHash = name => hash(fs.readFileSync(path.join(root, name)));
const shell = fs.readFileSync(path.join(root, 'web/index.html'), 'utf8');
const names = [...shell.matchAll(/<script src="\/app\/([\w-]+\.js)(?:\?[^"<>]*)?"><\/script>/g)].map(match => match[1]);
assert(names.includes('fluids-lab.js'));
const expectedBundle = Buffer.from("'use strict';\n" + names.map(name => fs.readFileSync(path.join(root, 'web', name), 'utf8')).join('\n;\n'));
const authored = JSON.parse(fs.readFileSync(path.join(root, 'data/curriculum/03-physics.json'))).nodes.find(node => node.id === 'phys.4.fluids');
const media = authored.lesson_media.find(row => row.renderer === 'fluids-concept-lab');
const illustration = authored.lesson_media.find(row => row.kind === 'illustration');
const venturi = authored.lesson_media.find(row => row.renderer === 'venturi-flow-lab');
const selections = {
  continuity: ['continuity-400', 'continuity-800'],
  hydrostatics: ['hydro-vacuum', 'hydro-vapor'], pistons: ['piston-example'],
  hull: ['hull-floating', 'hull-neutral', 'hull-overload'], pipe: ['pipe-baseline', 'pipe-reverse'],
  boundary: ['boundary-baseline', 'boundary-downstream'], settling: ['settling-heavy', 'settling-neutral', 'settling-rise'],
  lift: ['lift-symmetric', 'lift-positive', 'lift-negative'], plume: ['plume-base', 'plume-eightfold'],
};
(async () => {
  fs.mkdirSync(out, {recursive: true});
  const browser = await chromium.launch({headless: true});
  const proof = {scope: 'Actual authenticated fluids lesson on an isolated synthetic database', productionVerified: false,
    sourceSHA256: Object.fromEntries(['web/fluids-lab.js', 'web/lesson-models.js', 'web/index.html', 'web/app.js', 'primer/curriculum.py', 'data/curriculum/03-physics.json'].map(name => [name, fileHash(name)])),
    authentication: [], readerCases: [], errors: [], independentPhysicsEstablishedByThisReaderCheck: false};
  try {
    const anonymous = await browser.newContext();
    for (const asset of ['/app/fluids-lab.js', '/app/startup.js', '/api/curriculum/node/phys.4.fluids']) {
      const response = await anonymous.request.get(base + asset); assert.equal(response.status(), 401);
      proof.authentication.push({asset, status: response.status()});
    }
    await anonymous.close();
    for (const width of [390, 1440]) {
      const context = await browser.newContext({viewport: {width, height: 1000}, reducedMotion: 'reduce',
        extraHTTPHeaders: {Authorization: 'Basic ' + Buffer.from(fixture.username + ':' + fixture.password).toString('base64')}});
      const profile = await context.request.post(base + '/api/profile', {headers: {Origin: base}, data: {name: 'Synthetic fluids QA', age: 30, domains: ['physics']}});
      assert.equal(profile.status(), 200);
      await context.request.post(base + '/api/profile/settings', {headers: {Origin: base}, data: {speak: false}});
      const response = await context.request.get(base + '/api/curriculum/node/phys.4.fluids'); assert.equal(response.status(), 200);
      const body = await response.json(), node = body.node || body;
      assert.equal(node.id, authored.id); assert.equal(node.quiz, undefined); assert.equal(node.question_count, 10);
      for (const item of [media, illustration, venturi]) assert.deepEqual(node.lesson_media.find(row => row.id === item.id), item);
      for (const question of authored.quiz) for (const key of ['prompt', 'explain']) assert(!JSON.stringify(node).includes(question[key]));
      const asset = await context.request.get(base + '/app/fluids-lab.js'); assert.equal(asset.status(), 200);
      assert.equal(hash(await asset.body()), proof.sourceSHA256['web/fluids-lab.js']);
      const page = await context.newPage(), errors = [], external = [], bundles = [], states = [], speech = [];
      await page.route('**/*', route => {
        if (new URL(route.request().url()).origin !== base) {external.push(route.request().url()); return route.abort();}
        return route.continue();
      });
      await page.addInitScript(() => {
        window.fluidsCSP = []; window.fluidsSpoken = [];
        document.addEventListener('securitypolicyviolation', event => window.fluidsCSP.push({directive: event.violatedDirective, blocked: event.blockedURI}));
        Object.defineProperty(speechSynthesis, 'speak', {configurable: true, value: utterance => {
          window.fluidsSpoken.push(utterance.text); setTimeout(() => utterance.onend?.(), 0);
        }});
      });
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => {if (message.type() === 'error') errors.push(message.text());});
      page.on('response', response => {
        if (new URL(response.url()).pathname === '/app/startup.js') bundles.push(response.body().then(bytes => {
          assert(bytes.equals(expectedBundle)); proof.startupBundle = {bytes: bytes.length, sha256: hash(bytes), currentSourceBytesEqual: true};
        }).catch(error => errors.push('Startup identity: ' + error.message)));
      });
      await page.goto(base + '/app/#/node/phys.4.fluids');
      const model = page.locator('.lesson-model[data-renderer="fluids-concept-lab"][data-fluids-lab]'); await model.waitFor();
      assert.equal(await model.count(), 1);
      assert.equal(await model.locator('.model-heading-row h3').textContent(), media.title);
      assert.equal(await model.locator('.model-instructions').textContent(), media.instructions);
      assert.equal(await page.locator('.lesson-model[data-renderer="venturi-flow-lab"]').count(), 1);
      await page.waitForFunction(src => [...document.querySelectorAll('img')].some(image => image.getAttribute('src') === src && image.complete && image.naturalWidth > 0), illustration.src);
      const choose = station => model.locator('[data-fluids-control="station"]').selectOption(station);
      const check = async label => {
        const result = await model.evaluate(element => {
          const state = element.fluids.getState(), panel = element.querySelector('[data-fluids-panel="' + state.station + '"]');
          const plots = [...panel.querySelectorAll('svg[data-fluids-plot]')];
          return {state, readout: element.querySelector('.model-readout').textContent,
            error: panel.dataset.error || null, visible: !panel.hidden,
            plots: plots.map(svg => ({name: svg.dataset.fluidsPlot, viewBox: svg.getAttribute('viewBox'),
              invalidNumericGeometry: [...svg.querySelectorAll('*')].some(child => [...child.attributes].some(attr => /(?:NaN|Infinity)/.test(attr.value)))})),
            overflow: document.documentElement.scrollWidth > innerWidth};
        });
        assert.equal(result.error, null); assert(result.visible); assert.equal(result.overflow, false);
        assert(result.readout.trim().length > 0); assert(!/NaN|Infinity/.test(result.readout)); assert(result.plots.length > 0);
        assert(result.plots.every(plot => !plot.invalidNumericGeometry));
        states.push({label, station: result.state.station, readout: result.readout, plots: result.plots,
          noHorizontalOverflow: true, allGeometryFinite: true});
      };
      await check('authored state');
      for (const [station, presets] of Object.entries(selections)) {
        await choose(station);
        for (const preset of presets) {await model.locator('[data-fluids-preset="' + preset + '"]').click(); await check(preset);}
        await model.locator('[data-fluids-action="enlarge"]').click(); await check(station + ' enlarged');
        const svg = model.locator('[data-fluids-panel="' + station + '"] svg[data-fluids-plot]').first();
        const region = svg.locator('..');
        if (await region.evaluate(element => element.scrollWidth > element.clientWidth)) {
          await region.focus(); await page.keyboard.press('ArrowRight');
          await page.waitForFunction(element => element.scrollLeft > 0, await region.elementHandle());
        }
        await model.locator('[data-fluids-action="enlarge"]').click(); await check(station + ' fitted');
        await page.evaluate(() => {window.fluidsSpoken = [];});
        await model.getByRole('button', {name: 'Read this activity aloud', exact: true}).click();
        await page.waitForFunction(() => !document.querySelector('[data-fluids-lab] .speak-btn').classList.contains('speaking'));
        const spoken = await page.evaluate(() => window.fluidsSpoken.join(' '));
        const readout = await model.locator('.model-readout').textContent();
        assert(spoken.replace(/\s+/g, ' ').includes(readout.replace(/\s+/g, ' ')));
        speech.push({station, readoutIncluded: true, characters: spoken.length});
        await model.screenshot({path: path.join(out, station + '-' + width + '.png')});
      }
      for (const [station, field, invalid, restored] of [
        ['hull', 'retainedWaterMass', 2000, 0], ['pipe', 'mu', 0, .001], ['boundary', 'x', 0, .5],
      ]) {
        await choose(station);
        if (station === 'hull') await model.locator('[data-fluids-preset="hull-floating"]').click();
        const control = model.locator('[data-fluids-control="' + station + '.' + field + '"]');
        await control.fill(String(invalid)); await control.dispatchEvent('change');
        const panel = model.locator('[data-fluids-panel="' + station + '"]');
        assert(await panel.getAttribute('data-error')); assert.equal(await panel.locator('svg').count(), 0);
        assert((await model.locator('.model-readout').textContent()).includes('Invalid input'));
        states.push({label: station + ' invalid physical domain', station, invalidValueRejected: true, stalePlotHidden: true});
        await control.fill(String(restored)); await control.dispatchEvent('change'); await check(station + ' domain recovery');
      }
      await model.locator('[data-fluids-action="reset"]').click(); await check('reset');
      assert(await model.locator('input,select').evaluateAll(inputs => inputs.every(input => input.labels?.length > 0)));
      await Promise.all(bundles); assert(bundles.length > 0); assert.deepEqual(errors, []); assert.deepEqual(external, []);
      assert.deepEqual(await page.evaluate(() => window.fluidsCSP), []);
      proof.readerCases.push({width, states, speech, preservedVenturi: true, originalIllustrationLoaded: true,
        originalMediaIdentityPreserved: true, quizAnswersNotExposedByPublicNodeAPI: true,
        currentStartupBundleExact: true, CSPViolations: [], pageErrors: [], externalRequests: []});
      await context.close();
    }
    proof.totalStates = proof.readerCases.reduce((count, row) => count + row.states.length, 0);
    proof.speechCases = proof.readerCases.reduce((count, row) => count + row.speech.length, 0);
    proof.allPassed = true;
    fs.writeFileSync(path.join(out, 'proof.json'), JSON.stringify(proof, null, 2) + '\n');
    console.log(JSON.stringify({actualReaderStates: proof.totalStates, speechCases: proof.speechCases,
      startupBytes: proof.startupBundle.bytes, pageErrors: 0, productionVerified: false}));
  } finally {await browser.close();}
})().catch(error => {console.error(error); process.exit(1);});
