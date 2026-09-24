#!/usr/bin/env node
'use strict';

// Copy only verified regular runtime files from `vercel deploy --dry --json`.
// Never archive the working tree: archive tools can recurse ignored directories.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
// Read the manifest on stdin; no caller-selected filesystem path is opened.
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const root = fs.realpathSync(path.resolve(__dirname, '..'));
assert.equal(path.resolve(input.basePath), root);
const files = input.files;
const forbidden = /(^|\/)(content|artifacts|\.git|\.venv|\.vercel|\.env[^/]*|\.agents|\.claude|\.github|\.pytest_cache|__pycache__|docs|tests|tools)(\/|$)|\.db(?:-|$)| 2\./;
for (const file of files) {
  assert.ok(!path.isAbsolute(file.path) && !file.path.split('/').includes('..'), file.path);
  assert.ok(!forbidden.test(file.path), 'Excluded path in release: ' + file.path);
  const absolute = path.join(root, file.path);
  const stat = fs.lstatSync(absolute);
  assert.ok(stat.isFile() && !stat.isSymbolicLink(), 'Only regular files: ' + file.path);
  assert.equal(stat.size, file.size, 'Size changed: ' + file.path);
  if (file.sha) assert.equal(createHash('sha1').update(fs.readFileSync(absolute)).digest('hex'), file.sha, 'Content changed: ' + file.path);
}
// Compare exact asset paths with the trusted runtime tree, not a lesson count
// that becomes stale when another subject or photographic scene is added.
function webps(directory) {
  return fs.readdirSync(directory, {withFileTypes: true}).flatMap(entry => {
    const full = path.join(directory, entry.name);
    if (entry.isDirectory()) return webps(full);
    return entry.isFile() && entry.name.endsWith('.webp') && !entry.name.includes(' 2.')
      ? [path.relative(root, full).split(path.sep).join('/')] : [];
  });
}
const expectedWebps = webps(path.join(root, 'web'));
assert.ok(expectedWebps.length > 0, 'Runtime image inventory cannot be empty');
assert.deepEqual(files.filter(f => f.path.endsWith('.webp')).map(f => f.path).sort(), expectedWebps.sort());
const release = fs.mkdtempSync(path.join(os.tmpdir(), 'primer-release-'));
for (const file of files) {
  const destination = path.join(release, file.path);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.copyFileSync(path.join(root, file.path), destination);
}
// Project identity only; never copy pulled environment files or build outputs.
fs.mkdirSync(path.join(release, '.vercel'));
fs.copyFileSync(path.join(root, '.vercel/project.json'), path.join(release, '.vercel/project.json'));
console.log(JSON.stringify({ release, files: files.length, bytes: files.reduce((n, f) => n + f.size, 0) }));
