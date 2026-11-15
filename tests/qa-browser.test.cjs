'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { createEvidenceDirectory, loopbackQaUrl } = require('../tools/qa-browser.cjs');

test('evidence gets a fresh private directory regardless of a legacy output argument', () => {
  const existing = fs.mkdtempSync(path.join(os.tmpdir(), 'primer-qa-sentinel-'));
  const sentinel = path.join(existing, 'results.json');
  fs.writeFileSync(sentinel, 'leave existing evidence intact');
  const originalArg = process.argv[3];
  const created = [];
  try {
    for (const supplied of [existing, path.join(existing, '..'), '/tmp/../../etc', 'relative/output']) {
      process.argv[3] = supplied;
      const directory = createEvidenceDirectory();
      created.push(directory);
      assert.equal(path.dirname(directory), os.tmpdir());
      assert.match(path.basename(directory), /^primer-browser-qa-[A-Za-z0-9]+$/);
      assert.notEqual(directory, existing);
      assert.deepEqual(fs.readdirSync(directory), []);
      if (process.platform !== 'win32') assert.equal(fs.statSync(directory).mode & 0o777, 0o700);
      fs.writeFileSync(path.join(directory, 'results.json'), 'new evidence');
    }
    assert.equal(new Set(created).size, created.length);
    assert.equal(fs.readFileSync(sentinel, 'utf8'), 'leave existing evidence intact');
  } finally {
    if (originalArg === undefined) delete process.argv[3];
    else process.argv[3] = originalArg;
    for (const directory of created) fs.rmSync(directory, { recursive: true });
    fs.rmSync(existing, { recursive: true });
  }
});

test('QA server accepts only a loopback HTTP origin', () => {
  for (const origin of ['http://127.0.0.1:8793', 'http://localhost:8793', 'https://[::1]:8793']) {
    assert.equal(loopbackQaUrl(origin), origin);
    assert.equal(loopbackQaUrl(origin + '/'), origin);
  }
  for (const value of [undefined, '', 'https://primer.example', 'http://localhost.example',
    'http://127.0.0.1.example', 'http://localhost@primer.example', 'ftp://localhost',
    'file:///tmp/example', 'http://localhost/a', 'http://localhost/?x=1',
    'http://localhost/#part', 'http://user:password@localhost']) {
    assert.throws(() => loopbackQaUrl(value), undefined, String(value));
  }
});
