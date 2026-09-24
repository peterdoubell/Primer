#!/usr/bin/env node
'use strict';
// Exercise delayed request boundaries without a browser or learner record.
const assert = require('node:assert/strict');
// Import a fixed module with inert event registration; no source extraction or
// dynamic execution, and no real reader/profile/route is opened by this check.
globalThis.window = { addEventListener() {} };
globalThis.document = { addEventListener() {} };
const { reportingGuard } = require('../web/app.js');
const context = { _readerContextSeq: 1, location: { hash: '#/radiology/first' } };
const dependencies = {
  routeVersion: () => context._readerContextSeq, routeHash: () => context.location.hash,
  showLoading() {}, missingProfile: () => false, onboard() {},
  errorCard: error => ({ error: String(error) }), rerender() {},
};
context.reportingGuard = (page, fn) => reportingGuard(page, fn, dependencies);
function page() {
  return { isConnected: true, clears: 0, errors: [],
    replaceChildren() { this.clears++; }, append(value) { this.errors.push(value); } };
}
async function run() {
  const normal = page();
  const result = await context.reportingGuard(normal, () => Promise.resolve({ id: 'current' }));
  assert.equal(result.id, 'current'); assert.equal(normal.clears, 1);
  for (const failed of [false, true]) {
    const oldPage = page(); let resolve, reject;
    const pending = context.reportingGuard(oldPage, () => new Promise((yes, no) => { resolve = yes; reject = no; }));
    context._readerContextSeq++;
    context.location.hash = '#/radiology/newer-' + failed;
    if (failed) reject(new Error('Old request failed')); else resolve({ id: 'old' });
    assert.equal(await pending, null);
    assert.equal(oldPage.clears, 0, 'A stale response must not clear the newer route');
    assert.equal(oldPage.errors.length, 0, 'A stale error must not replace the newer route');
  }
  const removed = page(); let finish;
  const pending = context.reportingGuard(removed, () => new Promise(resolve => { finish = resolve; }));
  removed.isConnected = false; finish({ id: 'detached' });
  assert.equal(await pending, null); assert.equal(removed.clears, 0);
  const failed = page();
  await context.reportingGuard(failed, () => Promise.reject(new Error('Current failure')));
  assert.equal(failed.clears, 1); assert.equal(failed.errors.length, 1);
  console.log('Passed: current response, stale success/error, detached page and current error boundaries.');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
