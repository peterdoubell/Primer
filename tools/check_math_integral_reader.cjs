'use strict';
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const { chromium } = require('playwright');
const fixture = JSON.parse(fs.readFileSync(0, 'utf8')), origin = new URL(fixture.url);
assert.equal(origin.hostname, '127.0.0.1'); assert.equal(origin.protocol, 'http:'); assert.equal(origin.pathname, '/'); assert.equal(origin.username, ''); assert.equal(origin.password, '');
const base = origin.origin, rootPath = path.resolve(__dirname, '..'), output = path.join(rootPath, 'docs/integral-calculus-fidelity-review-20261025/reader');
fs.mkdirSync(output, { recursive: true });
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex'), fileHash = name => hash(fs.readFileSync(path.join(rootPath, name)));
const shell = fs.readFileSync(path.join(rootPath, 'web/index.html'), 'utf8'), scripts = [...shell.matchAll(/<script src="\/app\/([\w-]+\.js)(?:\?[^"<>]*)?"><\/script>/g)].map(m => m[1]);
assert(scripts.includes('math-integral-lab.js'));
const bundle = Buffer.from("'use strict';\n" + scripts.map(n => fs.readFileSync(path.join(rootPath, 'web', n), 'utf8')).join('\n;\n'));
const authored = JSON.parse(fs.readFileSync(path.join(rootPath, 'data/curriculum/01-mathematics.json'))).nodes.find(n => n.id === 'math.4.int-calc');
const sourcePaths = ['web/math-integral-lab.js', 'web/math-integral-lab.css', 'web/lesson-models.js', 'web/index.html', 'web/app.js', 'primer/server.py', 'data/curriculum/01-mathematics.json', 'tools/check_math_integral_reader.cjs', 'tools/check_math_integral_reader.py', 'tests/test_math_integral_lab.py'];
// Independent browser geometry oracle: exact Simpson quadrature for these
// quadratic polynomials; no values/functions imported from the implementation.
const coefficients = { square: [0, 0, 3], linear: [0, 2, 0], signed: [-1, 0, 1], velocity: [0, 6, 0], inflow: [1, 4, 0], increasing: [1, 0, 1], between: [0, 1, -1] };
const f = (id, x) => coefficients[id][0] + coefficients[id][1] * x + coefficients[id][2] * x * x;
const integral = (id, a, b) => (b - a) * (f(id, a) + 4 * f(id, (a + b) / 2) + f(id, b)) / 6;
const near = (a, b, label = '') => assert.ok(Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) <= 2e-8 * Math.max(1, Math.abs(b)), `${label}: ${a} != ${b}`);
(async () => {
  const browser = await chromium.launch({ headless: true });
  const proof = { scope: 'Authenticated actual Integral Calculus reader, synthetic local data; independent rendered-coordinate and quadrature oracle', productionVerified: false, wholeGoalComplete: false, sourceSHA256: Object.fromEntries(sourcePaths.map(p => [p, fileHash(p)])), authentication: [], readerCases: [], errors: [] };
  try {
    const anonymous = await browser.newContext();
    for (const asset of ['/app/math-integral-lab.js', '/app/math-integral-lab.css', '/app/startup.js', '/api/curriculum/node/math.4.int-calc']) { const response = await anonymous.request.get(base + asset); assert.equal(response.status(), 401); proof.authentication.push({ asset, status: 401 }); }
    await anonymous.close();
    for (const width of [390, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce', extraHTTPHeaders: { Authorization: 'Basic ' + Buffer.from(fixture.username + ':' + fixture.password).toString('base64') } });
      assert.equal((await context.request.post(base + '/api/profile', { headers: { Origin: base }, data: { name: 'Synthetic integral QA', age: 30, domains: ['math'] } })).status(), 200);
      assert.equal((await context.request.post(base + '/api/profile/settings', { headers: { Origin: base }, data: { speak: false } })).status(), 200);
      const api = await context.request.get(base + '/api/curriculum/node/math.4.int-calc'); assert.equal(api.status(), 200); const raw = await api.json(), node = raw.node || raw;
      assert.equal(node.id, authored.id); assert.equal(node.question_count, 10); assert.equal(node.quiz, undefined); for (const media of authored.lesson_media) assert.deepEqual(node.lesson_media.find(m => m.id === media.id), media);
      for (const q of authored.quiz) { assert(!JSON.stringify(node).includes(q.prompt)); assert(!JSON.stringify(node).includes(q.explain)); }
      for (const file of ['math-integral-lab.js', 'math-integral-lab.css']) { const r = await context.request.get(base + '/app/' + file); assert.equal(r.status(), 200); assert.equal(hash(await r.body()), proof.sourceSHA256['web/' + file]); }
      const page = await context.newPage(), errors = [], external = [], startup = [], states = [], centeredCaptures = [];
      await page.route('**/*', route => { if (new URL(route.request().url()).origin !== base) { external.push(route.request().url()); return route.abort(); } return route.continue(); });
      await page.addInitScript(() => { window.integralCSP = []; window.integralSpoken = []; document.addEventListener('securitypolicyviolation', e => window.integralCSP.push({ directive: e.violatedDirective, blocked: e.blockedURI })); Object.defineProperty(speechSynthesis, 'speak', { configurable: true, value: utterance => { window.integralSpoken.push(utterance.text); setTimeout(() => utterance.onend?.(), 0); } }); });
      page.on('pageerror', e => errors.push(e.message)); page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
      page.on('response', response => { if (new URL(response.url()).pathname === '/app/startup.js') startup.push(response.body().then(bytes => { assert(bytes.equals(bundle)); proof.startupBundle = { bytes: bytes.length, sha256: hash(bytes), currentSourceBytesEqual: true }; }).catch(e => errors.push('Startup: ' + e.message))); });
      await page.goto(base + '/app/#/node/math.4.int-calc'); const lab = page.locator('.math-integral-lab'); await lab.waitFor(); assert.equal(await lab.count(), 1);
      assert.equal(await page.locator('.concept-lab[data-scenario="math.4.int-calc"]').count(), 0);
      const illustration = authored.lesson_media.find(m => m.kind === 'illustration');
      await page.waitForFunction(src => [...document.querySelectorAll('img')].some(image => image.getAttribute('src') === src && image.complete && image.naturalWidth > 0), illustration.src);
      const set = async (key, value) => { const control = lab.locator('[data-integral-' + key + ']'); if (await control.evaluate(e => e.tagName === 'SELECT')) await control.selectOption(String(value)); else { await control.fill(String(value)); await control.dispatchEvent('change'); } };
      const check = async label => {
        const data = await lab.evaluate(el => ({ state: el.integral.getState(), model: el.integral.getModel(), readout: el.querySelector('.integral-readout').textContent, overflow: document.documentElement.scrollWidth > innerWidth + 1, plots: [...el.querySelectorAll('[data-integral-plot]')].map(plot => ({ name: plot.dataset.integralPlot, domain: JSON.parse(plot.dataset.domain), transform: JSON.parse(plot.dataset.transform), series: [...plot.querySelectorAll('[data-integral-series]')].map(line => ({ name: line.dataset.integralSeries, points: line.getAttribute('points').trim().split(/\s+/).map(p => p.split(',').map(Number)) })), rectangles: [...plot.querySelectorAll('[data-integral-rectangle]')].map(rect => Object.fromEntries(['x', 'y', 'width', 'height'].map(k => [k, Number(rect.getAttribute(k))]))), points: [...plot.querySelectorAll('[data-integral-point]')].map(point => ({ name: point.dataset.integralPoint, x: Number(point.getAttribute('cx')), y: Number(point.getAttribute('cy')) })), regions: [...plot.querySelectorAll('[data-integral-region]')].map(region => ({ kind: region.dataset.integralRegion, bounds: JSON.parse(region.dataset.regionBounds), points: region.getAttribute('points').trim().split(/\s+/).map(p => p.split(',').map(Number)) })), textFits: [...plot.querySelectorAll('text')].every(t => { const b = t.getBBox(); return b.x >= -1 && b.y >= -1 && b.x + b.width <= 681 && b.y + b.height <= 391; }) })) }));
        assert.equal(data.overflow, false, label + ' page width'); assert(!/NaN|Infinity/.test(data.readout));
        const s = data.state; let checkedCoordinates = 0;
        if (s.station === 'proper') { near(data.model.exact, integral(s.example, s.a, s.b), label + ' exact'); assert.equal(data.plots.length, 2); }
        for (const plot of data.plots) {
          assert.equal(plot.textFits, true, label + ' tick labels fit'); assert.deepEqual(plot.transform, { x0: 82, x1: 644, y0: 322, y1: 28 });
          const d = plot.domain, project = ([x, y]) => [82 + (x - d.x[0]) * 562 / (d.x[1] - d.x[0]), 322 - (y - d.y[0]) * 294 / (d.y[1] - d.y[0])], unproject = ([x, y]) => [d.x[0] + (x - 82) * (d.x[1] - d.x[0]) / 562, d.y[0] + (322 - y) * (d.y[1] - d.y[0]) / 294];
          for (const series of plot.series) for (const p of series.points) {
            assert(p[0] >= 82 - 1e-7 && p[0] <= 644 + 1e-7 && p[1] >= 28 - 1e-7 && p[1] <= 322 + 1e-7, label + ' finite curve inside plotted domain');
            const [x, y] = unproject(p); let expected;
            if (series.name === 'integrand') expected = f(s.example, x);
            else if (series.name === 'upper') expected = x;
            else if (series.name === 'lower') expected = x * x;
            else if (series.name === 'accumulation') expected = integral(s.example, s.a, x);
            else if (series.name === 'antiderivative') expected = integral(s.example, 0, x) + s.constant;
            else if (series.name === 'tangent') expected = integral(s.example, s.a, s.cursor) + (x - s.cursor) * f(s.example, s.cursor);
            else if (series.name === 'left-limit') expected = -x * Math.LN10;
            else if (series.name === 'right-limit') expected = (s.path === 'equal' ? x : s.path === 'half' ? x + Math.LOG10E * Math.log(2) : s.path === 'square' ? 2 * x : s.rightExponent) * Math.LN10;
            else if (series.name === 'combined-limit') expected = (s.path === 'equal' ? 0 : s.path === 'half' ? Math.log(2) : s.path === 'square' ? x * Math.LN10 : (s.rightExponent - x) * Math.LN10);
            else if (series.name === 'power-limit') expected = s.power === 1 ? x * Math.LN10 : (1 - Math.pow(10, -x * (1 - s.power))) / (1 - s.power);
            else if (series.name === 'finite-limit') expected = 1 / (1 - s.power);
            else throw Error('Unrecognized rendered series ' + series.name);
            near(y, expected, label + ' ' + series.name); checkedCoordinates++;
          }
          if (plot.name === 'integrand') {
            assert.equal(plot.rectangles.length, s.count); const step = (s.b - s.a) / s.count;
            for (let i = 0; i < s.count; i++) { const rectangle = plot.rectangles[i], begin = s.a + i * step, end = s.a + (i + 1) * step, sample = s.method === 'left' ? Math.min(begin, end) : s.method === 'right' ? Math.max(begin, end) : (begin + end) / 2, p = project([Math.min(begin, end), f(s.example, sample)]), zero = project([0, 0]); near(rectangle.x, p[0], label + ' rectangle x'); near(rectangle.y, Math.min(p[1], zero[1]), label + ' rectangle y'); near(rectangle.width, Math.abs(step * 562 / (d.x[1] - d.x[0])), label + ' rectangle width'); near(rectangle.height, Math.abs(p[1] - zero[1]), label + ' rectangle height'); checkedCoordinates += 4; }
            for (const region of plot.regions) {
              const [left, right] = region.bounds; assert(left < right); const areaPoints = region.points.map(unproject);
              for (const [x, y] of areaPoints) { assert(x >= left - 1e-7 && x <= right + 1e-7); if (region.kind === 'between') assert(Math.min(Math.abs(y - x), Math.abs(y - x * x)) < 1e-7); else assert(Math.min(Math.abs(y), Math.abs(y - f(s.example, x))) < 1e-7); checkedCoordinates++; }
            }
          }
          for (const point of plot.points) {
            if (point.name === 'power-sequence') continue;
            const expected = point.name === 'integrand-probe' ? [s.cursor, f(s.example, s.cursor)] : point.name === 'accumulation-probe' ? [s.cursor, integral(s.example, s.a, s.cursor)] : point.name === 'anchor' ? [s.a, 0] : [s.b, integral(s.example, s.a, s.b)];
            const position = project(expected); near(point.x, position[0]); near(point.y, position[1]); checkedCoordinates += 2;
          }
        }
        states.push({ label, station: s.station, example: s.station === 'proper' ? s.example : s.singular, checkedRenderedCoordinates: checkedCoordinates, noHorizontalOverflow: true, labelsInsidePlot: true }); return data;
      };
      const captureCenteredPlots = async label => {
        for (const figure of await lab.locator('.integral-output figure').all()) {
          await figure.evaluate(e => e.scrollIntoView({ block: 'center', inline: 'nearest' }));
          const visible = await figure.evaluate(e => { const r = e.getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight && [r.top + 4, (r.top + r.bottom) / 2, r.bottom - 4].every(y => e.contains(document.elementFromPoint(r.left + r.width / 2, y))); });
          assert(visible, label + ' centred figure must be unobscured in the actual viewport');
          const name = await figure.locator('[data-integral-plot]').getAttribute('data-integral-plot'), file = label + '-' + name + '-' + width + '-centered.png';
          await figure.screenshot({ path: path.join(output, file) }); centeredCaptures.push({ file, viewportCentered: true, sampledHitTestsUnobscured: true });
        }
      };
      await check('authored entry');
      for (const preset of ['power', 'constant', 'signed', 'velocity', 'between', 'inflow', 'increasing']) { await set('preset', preset); await check(preset); if (['signed', 'between'].includes(preset)) { await lab.screenshot({ path: path.join(output, preset + '-' + width + '.png') }); await captureCenteredPlots(preset); } }
      await set('preset', 'signed'); for (const method of ['left', 'midpoint', 'right']) { await set('method', method); for (const n of [1, 128]) { await set('count', n); await check(method + ' ' + n); } }
      for (const [a, b, cursor] of [[4, -3, 4], [-3, 4, -3], [1, 1, 1]]) { await set('a', a); await set('b', b); await set('cursor', cursor); await check('bounds ' + [a, b, cursor]); }
      await set('preset', 'constant'); const baseline = await lab.evaluate(e => e.integral.getModel()); await set('constant', -10); const shifted = await check('constant shift'); near(shifted.model.exact, baseline.exact); near(shifted.model.cursor.slope, baseline.cursor.slope);
      const input = lab.locator('[data-integral-count]'), oldState = await lab.evaluate(e => e.integral.getState()); for (const invalid of ['', '0', '129', '1.5']) { await input.fill(invalid); await input.press('Enter'); assert.equal(await input.getAttribute('aria-invalid'), 'true'); assert.deepEqual(await lab.evaluate(e => e.integral.getState()), oldState); } await input.press('Escape'); assert.equal(await input.inputValue(), String(oldState.count)); await check('invalid input restored');
      const zoomCheck = async () => { const before = await lab.evaluate(e => e.integral.getState()); await lab.locator('[data-integral-enlarge]').click(); const viewport = lab.locator('.integral-viewport').first(); near(await viewport.locator('svg').evaluate(e => e.getBoundingClientRect().width), 900); assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)); if (await viewport.evaluate(e => e.scrollWidth > e.clientWidth)) { await viewport.focus(); await page.keyboard.press('ArrowRight'); await page.waitForFunction(e => e.scrollLeft > 0, await viewport.elementHandle()); } await lab.locator('[data-integral-enlarge]').click(); assert.deepEqual(await lab.evaluate(e => e.integral.getState()), before); };
      await zoomCheck(); await check('proper enlarge scroll fit');
      await set('station', 'improper');
      for (const cutoffPath of ['equal', 'half', 'square', 'independent']) { await set('path', cutoffPath); await set('leftExponent', 6); if (cutoffPath === 'independent') await set('rightExponent', .5); await check('reciprocal ' + cutoffPath); await lab.screenshot({ path: path.join(output, 'reciprocal-' + cutoffPath + '-' + width + '.png') }); await captureCenteredPlots('reciprocal-' + cutoffPath); }
      await set('singular', 'power'); for (const power of [.25, .5, .95, 1, 1.05, 2]) { await set('power', power); await check('endpoint p=' + power); if ([.5, 1, 2].includes(power)) { await lab.screenshot({ path: path.join(output, 'endpoint-' + power + '-' + width + '.png') }); await captureCenteredPlots('endpoint-' + power); } }
      await zoomCheck(); await check('improper enlarge scroll fit');
      const speech = [];
      for (const station of ['proper', 'improper']) { await set('station', station); await page.evaluate(() => { window.integralSpoken = []; }); const button = lab.getByRole('button', { name: /Read.*aloud/ }); assert.equal(await button.count(), 1); await button.click(); await page.waitForFunction(() => !document.querySelector('.math-integral-lab .speak-btn').classList.contains('speaking')); const spoken = await page.evaluate(() => window.integralSpoken.join(' ')), expected = await lab.evaluate(e => e.getModelSpeech()); assert.equal(spoken.replace(/\s+/g, ' ').trim(), expected.replace(/\s+/g, ' ').trim()); speech.push({ station, fullDynamicSpeech: true, characters: spoken.length }); }
      await set('station', 'proper'); await lab.locator('[data-integral-reset]').click(); await check('reset');
      assert(await lab.locator('input,select').evaluateAll(elements => elements.every(e => e.labels?.length || e.getAttribute('aria-label'))));
      await Promise.all(startup); assert(startup.length > 0); assert.deepEqual(await page.evaluate(() => window.integralCSP), []); assert.deepEqual(errors, []); assert.deepEqual(external, []);
      proof.readerCases.push({ width, states, speech, centeredCaptures, authoredMediaIdentityPreserved: true, originalIllustrationLoaded: true, quizAnswersNotExposed: true, startupBundleExact: true, CSPViolations: [], pageErrors: [], externalRequests: [] }); await context.close();
    }
    proof.totalStates = proof.readerCases.reduce((n, r) => n + r.states.length, 0); proof.checkedRenderedCoordinates = proof.readerCases.flatMap(r => r.states).reduce((n, s) => n + s.checkedRenderedCoordinates, 0); proof.allPassed = true;
    fs.writeFileSync(path.join(output, 'proof.json'), JSON.stringify(proof, null, 2) + '\n'); console.log(JSON.stringify({ actualReaderStates: proof.totalStates, checkedRenderedCoordinates: proof.checkedRenderedCoordinates, speechCases: 4, startupBytes: proof.startupBundle.bytes, pageErrors: 0, productionVerified: false }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
