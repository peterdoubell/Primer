'use strict';
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const repo = path.resolve(__dirname, '../..');
const api = require('../../web/anatomy/brain-fine-massp2/reference.js');
const source = path.join(repo, 'web/anatomy/brain-fine-massp2');
const output = path.join(repo, '.research/brain-fine-runtime-decoded-20261011');
const manifest = JSON.parse(fs.readFileSync(path.join(source, 'manifest.json'), 'utf8'));
fs.mkdirSync(output, {recursive: true});
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const rows = [manifest.labels, ...Object.values(manifest.contrasts), ...Object.values(manifest.probabilities)];
async function main() {
for (const row of rows) {
  const compressed = fs.readFileSync(path.join(repo, 'web', row.file.replace(/^\/app\//, '')));
  assert.equal(sha(compressed), row.sha256);
  const inflated = zlib.gunzipSync(compressed);
  assert.equal(sha(inflated), row.encoded_raw_sha256);
  const decoded = api.decodeNative(inflated, row, manifest.shape);
  assert.equal(decoded.byteLength, row.decoded_bytes);
  assert.equal(sha(decoded), row.decoded_sha256);
  fs.writeFileSync(path.join(output, path.basename(row.file) + '.decoded'), decoded);
}
let coordinateChecks = 0;
for (let axis = 0; axis < 3; axis++) {
  const [a, b] = api.planeAxes[axis];
  for (let y = 0; y < manifest.shape[b]; y++) for (let x = 0; x < manifest.shape[a]; x++) {
    const p = api.pixelToSource([x, y], axis, Math.floor(manifest.shape[axis] / 2), manifest);
    assert.deepEqual(api.sourceToPixel(p, axis, manifest), [x + 0.5, y + 0.5]);
    const w = api.world(p, manifest);
    p.forEach((v, i) => assert.equal(w[i], manifest.original_affine[i][3] + manifest.original_affine[i][i] * (v + manifest.native_roi_start[i])));
    coordinateChecks++;
  }
}
assert.throws(() => api.decodeNative(new Uint8Array(0), manifest.labels, manifest.shape), /length/);
assert.throws(() => api.decodeNative(new Uint8Array(4), {codec: 'unknown'}, [1, 1, 1]), /Unknown/);
assert.throws(() => api.decodeNative(new Uint8Array(5), {codec: 'native-f32-dictionary-u8-gzip', dictionary_entries: 0}, [1, 1, 1]), /dictionary/);
const cube = {positions: Float32Array.from([0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1]),
  faces: Uint32Array.from([0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7])};
assert.equal(api.meshSection(cube, 2, 0).length, 4, 'coplanar triangulation internal diagonal must disappear');
assert.equal(api.meshSection(cube, 2, 0.5).length, 8);
assert.equal(api.meshSection(cube, 2, -1).length, 0);
assert.equal(api.meshSection(cube, 2, 2).length, 0);
const sections = [];
let compressedMeshTransportChecks = 0, decodedMeshTransportChecks = 0, negativeMeshTransportChecks = 0;
for (const target of manifest.targets) {
  const row = target.mesh, compressed = fs.readFileSync(path.join(repo, 'web', row.file.replace(/^\/app\//, '')));
  assert.equal(sha(compressed), row.sha256);
  const bytes = zlib.gunzipSync(compressed);
  assert.equal(sha(bytes), row.decoded_sha256);
  const mesh = api.decodeMesh(bytes, row);
  const compressedResponse = await api.decodeMeshResponse(compressed, row, zlib.gunzipSync, sha);
  const decodedResponse = await api.decodeMeshResponse(bytes, row, () => { throw Error('Raw BP3D must not inflate again'); }, sha);
  assert.deepEqual(compressedResponse, mesh); compressedMeshTransportChecks++;
  assert.deepEqual(decodedResponse, mesh); decodedMeshTransportChecks++;
  const corruptCompressed = Buffer.from(compressed); corruptCompressed[corruptCompressed.length - 1] ^= 1;
  await assert.rejects(api.decodeMeshResponse(corruptCompressed, row, zlib.gunzipSync, sha), /Compressed source model hash mismatch/); negativeMeshTransportChecks++;
  const corruptDecoded = Buffer.from(bytes); corruptDecoded[corruptDecoded.length - 1] ^= 1;
  await assert.rejects(api.decodeMeshResponse(corruptDecoded, row, zlib.gunzipSync, sha), /Decoded source model hash mismatch/); negativeMeshTransportChecks++;
  const corruptMagic = Buffer.from(bytes); corruptMagic[0] ^= 1;
  await assert.rejects(api.decodeMeshResponse(corruptMagic, row, zlib.gunzipSync, sha), /Compressed source model hash mismatch/); negativeMeshTransportChecks++;
  const wrongHeader = Buffer.from(bytes); wrongHeader.writeUInt32LE(row.vertices + 1, 4);
  await assert.rejects(api.decodeMeshResponse(wrongHeader, {...row, decoded_sha256: sha(wrongHeader)}, zlib.gunzipSync, sha), /Complete source model length mismatch/); negativeMeshTransportChecks++;
  for (let axis = 0; axis < 3; axis++) {
    const lo = Math.ceil((row.bounds[0][axis] - manifest.affine[axis][3]) / manifest.affine[axis][axis]);
    const hi = Math.floor((row.bounds[1][axis] - manifest.affine[axis][3]) / manifest.affine[axis][axis]);
    const planes = Array.from(new Set([0, manifest.shape[axis] - 1, target.center_indices[axis], lo, hi])).filter(i => i >= 0 && i < manifest.shape[axis]);
    for (const index of planes) {
      const coordinate = manifest.affine[axis][3] + manifest.affine[axis][axis] * index;
      sections.push({id: target.id, axis, index, coordinate, lines: api.meshSection(mesh, axis, coordinate)});
    }
  }
}
fs.writeFileSync(path.join(output, 'runtime-sections.json'), JSON.stringify(sections));
console.log(JSON.stringify({decoded_arrays: rows.length, complete_model_section_fixtures: sections.length, coordinate_checks: coordinateChecks,
  original_triangles: manifest.targets.reduce((n, target) => n + target.mesh.triangles, 0), analytic_coplanar_cube_checks: 4,
  negative_transport_fixture_count: 3,
  compressed_mesh_response_checks: compressedMeshTransportChecks, decoded_mesh_response_checks: decodedMeshTransportChecks,
  negative_mesh_response_checks: negativeMeshTransportChecks,
  runtime_javascript_sha256: sha(fs.readFileSync(path.join(source, 'reference.js')))}));
}
main().catch(error => { console.error(error); process.exitCode = 1; });
