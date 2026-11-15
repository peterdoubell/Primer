'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

// QA evidence always belongs to a new private directory. In particular, neither
// the URL nor a legacy CLI output argument can select an existing directory or
// a file that a screenshot, report, or cleanup operation could overwrite.
function createEvidenceDirectory() {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'primer-browser-qa-'));
  console.log('EVIDENCE_DIRECTORY=' + directory);
  return directory;
}

function loopbackQaUrl(value) {
  if (!value) throw new Error('Supply an isolated loopback QA server URL');
  const url = new URL(value);
  if (!['http:', 'https:'].includes(url.protocol)
      || !['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname)
      || url.username || url.password || url.search || url.hash
      || url.pathname !== '/') {
    throw new Error('QA must use an isolated loopback HTTP server origin');
  }
  return url.origin;
}

module.exports = { createEvidenceDirectory, loopbackQaUrl };
