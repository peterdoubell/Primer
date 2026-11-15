'use strict';

// Browser regression for verified source-mesh retry and WebGL context recovery.
// Every request is fulfilled from the checked-out web/ tree; no server is needed.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs/promises');
const path = require('node:path');
const zlib = require('node:zlib');

const origin = 'http://localhost:9123';
const webRoot = path.resolve(__dirname, '../web');
const atlasRoot = path.join(webRoot, 'anatomy/kcl-cervix');

async function localResponse(route) {
  const request = route.request();
  const url = new URL(request.url());
  assert.equal(url.origin, origin, 'The regression must not contact external services');
  assert.equal(request.method(), 'GET');
  assert.ok(url.pathname.startsWith('/app/'));
  const file = path.resolve(webRoot, url.pathname.slice('/app/'.length));
  assert.ok(file.startsWith(webRoot + path.sep));
  const contentType = file.endsWith('.js') ? 'text/javascript' :
    file.endsWith('.css') ? 'text/css' : file.endsWith('.html') ? 'text/html' :
      file.endsWith('.json') ? 'application/json' : 'application/octet-stream';
  await route.fulfill({body: await fs.readFile(file), contentType});
}

async function ready(page, triangles) {
  await page.waitForFunction(expected => {
    const canvas = document.querySelector('#surface');
    return canvas && !canvas.hidden &&
      document.querySelector('#surface-status').textContent === expected;
  }, triangles.toLocaleString('en-US') + ' source triangles visible');
}

async function sourceRows(atlas) {
  return JSON.parse(await fs.readFile(path.join(atlasRoot, atlas, 'surfaces.json'), 'utf8'));
}

async function verifyBuffers(page, atlas, rows) {
  const layers = page.locator('.layer');
  assert.equal(await layers.count(), rows.length);
  for (const layer of await layers.all()) await layer.uncheck();
  for (const [index, row] of rows.entries()) {
    await layers.nth(index).check();
    await ready(page, row.triangles);
    const actual = await page.locator('#surface').evaluate(canvas => {
      const gl = canvas.getContext('webgl2');
      if (!gl || gl.isContextLost()) throw Error('Expected a restored WebGL context');
      const program = gl.getParameter(gl.CURRENT_PROGRAM);
      const position = gl.getAttribLocation(program, 'position');
      const previous = gl.getParameter(gl.ARRAY_BUFFER_BINDING);
      gl.bindBuffer(gl.ARRAY_BUFFER, gl.getVertexAttrib(position, gl.VERTEX_ATTRIB_ARRAY_BUFFER_BINDING));
      const vertices = new Float32Array(gl.getBufferParameter(gl.ARRAY_BUFFER, gl.BUFFER_SIZE) / 4);
      const indices = new Uint32Array(gl.getBufferParameter(gl.ELEMENT_ARRAY_BUFFER, gl.BUFFER_SIZE) / 4);
      gl.getBufferSubData(gl.ARRAY_BUFFER, 0, vertices);
      gl.getBufferSubData(gl.ELEMENT_ARRAY_BUFFER, 0, indices);
      gl.bindBuffer(gl.ARRAY_BUFFER, previous);
      return {vertices: Array.from(vertices), indices: Array.from(indices)};
    });
    const raw = zlib.gunzipSync(await fs.readFile(path.join(atlasRoot, atlas, row.file)));
    assert.equal(crypto.createHash('sha256').update(raw).digest('hex'), row.sha256);
    assert.deepEqual(actual.vertices,
      Array.from(new Float32Array(raw.buffer, raw.byteOffset, 3 * row.vertices)), atlas + ' positions');
    assert.deepEqual(actual.indices,
      Array.from(new Uint32Array(raw.buffer, raw.byteOffset + 12 * row.vertices, 3 * row.triangles)),
      atlas + ' indices');
    await layers.nth(index).uncheck();
  }
}

async function loseContext(page) {
  await page.locator('#surface').evaluate(canvas => {
    const gl = canvas.getContext('webgl2');
    const extension = gl && gl.getExtension('WEBGL_lose_context');
    if (!extension) throw Error('WEBGL_lose_context is required for this regression');
    window.cervixTestContext = {extension, lossPrevented: false, restored: false};
    // Registered after the renderer, so this observes its preventDefault call.
    canvas.addEventListener('webglcontextlost', event => {
      window.cervixTestContext.lossPrevented = event.defaultPrevented;
    }, {once: true});
    canvas.addEventListener('webglcontextrestored', () => {
      window.cervixTestContext.restored = true;
    }, {once: true});
    extension.loseContext();
  });
  await page.waitForFunction(() => window.cervixTestContext.lossPrevented);
  assert.ok(await page.locator('#surface').isHidden());
  assert.match(await page.locator('#surface-status').textContent(), /context was lost/);
  await page.getByRole('button', {name: 'Reload page to retry'}).waitFor();
}

async function restoreContext(page, triangles) {
  await page.evaluate(() => window.cervixTestContext.extension.restoreContext());
  await page.waitForFunction(() => window.cervixTestContext.restored);
  await ready(page, triangles);
  assert.ok(await page.getByRole('button', {name: 'Reload page to retry'}).isHidden());
}

async function verifyRetryAndRestoration(browser) {
  const context = await browser.newContext({locale: 'en-US'});
  const pageErrors = [];
  let corruptFirstMesh = true;
  let meshesChecked = 0;
  try {
    await context.route('**/*', async route => {
      if (corruptFirstMesh && new URL(route.request().url()).pathname.endsWith('/055t/label-1.mesh.gz')) {
        corruptFirstMesh = false;
        await route.fulfill({body: Buffer.from('invalid source mesh'), contentType: 'application/octet-stream'});
      } else {
        await localResponse(route);
      }
    });
    const page = await context.newPage();
    page.setDefaultTimeout(20000);
    page.on('pageerror', error => pageErrors.push(error.message));
    for (const atlas of ['055t', '3t']) {
      const rows = await sourceRows(atlas);
      const initialTriangles = rows[0].triangles + rows[1].triangles;
      await page.goto(origin + '/app/anatomy/kcl-cervix/' + atlas + '/index.html');
      if (atlas === '055t') {
        await page.getByRole('button', {name: 'Retry 3D view'}).waitFor();
        assert.ok(await page.locator('#surface').isHidden());
        assert.match(await page.locator('#surface-status').textContent(), /could not be loaded/);
        await page.getByRole('button', {name: 'Retry 3D view'}).click();
      }
      await ready(page, initialTriangles);
      await verifyBuffers(page, atlas, rows);
      meshesChecked += rows.length;
      await page.locator('.layer').nth(0).check();
      await page.locator('#rotation').fill('61');
      await page.locator('#tilt').fill('-28');
      await ready(page, rows[0].triangles);
      const frame = await page.locator('#surface').evaluate(canvas => canvas.toDataURL());
      await loseContext(page);
      await restoreContext(page, rows[0].triangles);
      assert.equal(await page.locator('#rotation').inputValue(), '61');
      assert.equal(await page.locator('#tilt').inputValue(), '-28');
      assert.equal(await page.locator('#surface').evaluate(canvas => canvas.toDataURL()), frame,
        'Restoration must reproduce the selected geometry and camera');
      await verifyBuffers(page, atlas, rows);
      meshesChecked += rows.length;
    }
    assert.deepEqual(pageErrors, []);
    return meshesChecked;
  } finally {
    await context.close();
  }
}

async function verifyObsoleteFailure(browser) {
  const context = await browser.newContext({locale: 'en-US'});
  const pageErrors = [];
  let releaseOldRoute;
  let oldRoute;
  const intercepted = new Promise(resolve => { releaseOldRoute = resolve; });
  try {
    await context.addInitScript(() => {
      const originalFetch = window.fetch.bind(window);
      let firstMesh = true;
      window.cervixDelayedFetchSettled = false;
      window.fetch = (input, options = {}) => {
        const url = new URL(input instanceof Request ? input.url : input, location.href);
        if (firstMesh && url.pathname.endsWith('/055t/label-1.mesh.gz')) {
          firstMesh = false;
          // Simulate an asynchronous stage that survives abort, so the test
          // exercises the generation guard independently of request cancellation.
          const withoutSignal = {...options};
          delete withoutSignal.signal;
          return originalFetch(input, withoutSignal).then(response => {
            window.cervixDelayedFetchSettled = true;
            return response;
          });
        }
        return originalFetch(input, options);
      };
    });
    await context.route('**/*', async route => {
      if (!oldRoute && new URL(route.request().url()).pathname.endsWith('/055t/label-1.mesh.gz')) {
        oldRoute = route;
        releaseOldRoute();
        return;
      }
      await localResponse(route);
    });
    const page = await context.newPage();
    page.setDefaultTimeout(20000);
    page.on('pageerror', error => pageErrors.push(error.message));
    await page.goto(origin + '/app/anatomy/kcl-cervix/055t/index.html');
    let interceptionTimeout;
    try {
      await Promise.race([
        intercepted,
        new Promise((_, reject) => {
          interceptionTimeout = setTimeout(() => reject(Error('Initial mesh request was not intercepted')), 20000);
        }),
      ]);
    } finally {
      clearTimeout(interceptionTimeout);
    }
    assert.ok(await page.locator('#surface').isHidden());
    await loseContext(page);
    const rows = await sourceRows('055t');
    const initialTriangles = rows[0].triangles + rows[1].triangles;
    await restoreContext(page, initialTriangles);
    const restoredFrame = await page.locator('#surface').evaluate(canvas => canvas.toDataURL());
    await oldRoute.fulfill({status: 500, body: 'obsolete request failed'});
    await page.waitForFunction(() => window.cervixDelayedFetchSettled);
    // Wait for the pending draw/event turn, rather than an arbitrary delay.
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(resolve)));
    await ready(page, initialTriangles);
    assert.ok(await page.getByRole('button', {name: 'Retry 3D view'}).isHidden());
    assert.equal(await page.locator('#surface').evaluate(canvas => canvas.toDataURL()), restoredFrame);
    await page.locator('#rotation').fill('85');
    assert.notEqual(await page.locator('#surface').evaluate(canvas => canvas.toDataURL()), restoredFrame,
      'Restored controls must remain connected after the obsolete failure');
    assert.deepEqual(pageErrors, []);
  } finally {
    await context.close();
  }
}

(async () => {
  const browser = await chromium.launch({args: ['--enable-unsafe-swiftshader']});
  try {
    const meshes = await verifyRetryAndRestoration(browser);
    await verifyObsoleteFailure(browser);
    console.log('KCL mesh retry, both context restorations, ' + meshes +
      ' exact GPU buffer checks, preserved cameras and obsolete-request failure passed.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
