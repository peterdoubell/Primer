'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const zlib = require('node:zlib');
const root = path.resolve(__dirname, '..');
const directory = path.join(root, 'web/anatomy/hippunfold-hcp101006-registered');
const {decode, fetchPayload} = require(path.join(directory, 'payload.js'));
const manifest = JSON.parse(fs.readFileSync(path.join(directory, 'manifest.json')));
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const buffer = bytes => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);

(async () => {
  let accepted = 0, rejected = 0;
  for (const row of [...manifest.hemispheres.flatMap(side => side.arrays), ...manifest.meshes]) {
    const gzip = fs.readFileSync(path.join(directory, row.file));
    const decoded = zlib.gunzipSync(gzip);
    assert.equal(gzip.length > 0, true);
    assert.equal(digest(gzip), row.gzipSHA256);
    assert.equal(digest(decoded), row.decodedSHA256);
    assert.equal(decoded.byteLength, row.byteLength);
    for (const bytes of [gzip, decoded]) {
      assert.deepEqual(Buffer.from(await decode(row, buffer(bytes))), decoded);
      accepted++;
      const corrupt = Buffer.from(bytes); corrupt[Math.floor(corrupt.length / 2)] ^= 1;
      for (const bad of [corrupt, bytes.subarray(0, bytes.length - 1), Buffer.concat([bytes, Buffer.of(0)])]) {
        await assert.rejects(decode(row, buffer(bad)), /identity differs/);
        rejected++;
      }
      await assert.rejects(decode({...row, byteLength: row.byteLength - 1}, buffer(bytes)), /length differs/);
      rejected++;
    }
    await assert.rejects(decode({...row, decodedSHA256: '0'.repeat(64)}, buffer(gzip)), /identity or length differs/);
    rejected++;
  }
  // Gzip-like decoded data must not be decompressed a second time.
  const decoded = Buffer.from([0x1f, 0x8b, 0x08, 0x00, 0x91, 0x33, 0x7f]);
  const packed = zlib.gzipSync(decoded);
  const row = {file: 'fixture', gzipSHA256: digest(packed), decodedSHA256: digest(decoded), byteLength: decoded.length};
  assert.deepEqual(Buffer.from(await decode(row, buffer(decoded))), decoded); accepted++;
  for (const byteLength of [0, -1, NaN, Infinity, 1.5, undefined]) {
    await assert.rejects(decode({...row, byteLength}, buffer(packed)), /descriptor is invalid/); rejected++;
  }
  const originalFetch = global.fetch;
  try {
    for (const bytes of [packed, decoded]) {
      global.fetch = async () => new Response(bytes);
      assert.deepEqual(Buffer.from(await fetchPayload(row)), decoded); accepted++;
    }
    global.fetch = async () => new Response(packed, {status: 403});
    await assert.rejects(fetchPayload(row), /request failed: 403/); rejected++;
  } finally { global.fetch = originalFetch; }
  console.log(JSON.stringify({payloads: 20, acceptedRepresentations: accepted, rejectedInvalidInputs: rejected, exactBinarySourceFiles: true}));
})().catch(error => { console.error(error); process.exit(1); });
