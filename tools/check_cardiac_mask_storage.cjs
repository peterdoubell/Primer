'use strict';
const fs = require('node:fs'), zlib = require('node:zlib'), crypto = require('node:crypto'), assert = require('node:assert/strict');
const path = require('node:path');
const root = path.resolve(__dirname, '../web/anatomy/totalseg-v1-s0028-cardiac');
const storage = require('../web/anatomy/totalseg-v1-s0028-cardiac/mask-storage.js');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'viewer-manifest.json')));
const count = manifest.shape.reduce((a, b) => a * b, 1);
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
let checked = 0, packedBytes = 0;
for (const part of manifest.parts) {
  const raw = zlib.gunzipSync(fs.readFileSync(path.join(root, part.mask_file))).subarray(part.mask_voxel_offset);
  assert.equal(raw.length, count);
  assert.equal(hash(raw), part.mask_payload_sha256);
  const packed = storage.pack(raw), restored = Buffer.alloc(count);
  assert.equal(packed.length, Math.ceil(count / 8));
  for (let i = 0; i < count; i++) {
    restored[i] = storage.value(packed, i);
    if (restored[i] !== raw[i]) throw new Error(part.id + ': changed original mask sample ' + i);
  }
  assert.equal(hash(restored), part.mask_payload_sha256);
  checked += count; packedBytes += packed.byteLength;
}
for (const length of [0, 1, 7, 8, 9, 31, 65]) {
  const raw = Uint8Array.from({ length }, (_, i) => Number(i % 3 === 0));
  const packed = storage.pack(raw);
  assert.deepEqual(Uint8Array.from({ length }, (_, i) => storage.value(packed, i)), raw);
}
assert.throws(() => storage.pack(new Uint8Array([0, 2, 1])), RangeError);
assert.throws(() => storage.pack(new Int16Array([0, 1])), TypeError);
console.log(JSON.stringify({ originalMaskSamplesChecked: checked, packedMaskBytes: packedBytes,
  originalDenseMaskBytes: count * manifest.parts.length, CTOriginalSignedInt32Bytes: count * 4,
  residentSourceVoxelBuffersBytes: count * 4 + manifest.ct_voxel_offset + packedBytes }));
