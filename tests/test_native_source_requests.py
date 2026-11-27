"""Browser source names are finite; offline Node checks cannot make HTTP requests."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_published_current_names_and_offline_network_boundary():
    script = r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { sourceAssetName, assetURL, verifiedBytes } from './web/anatomy/segthy-001/native-volume.mjs';
for (const study of ['segthy-001', 'ct-torso-s0028']) {
  const files=JSON.parse(fs.readFileSync('web/anatomy/'+study+'/delivery.json')).files;
  for (const file of Object.keys(files).filter(name=>name.endsWith('.gz'))) {
    assert.equal(sourceAssetName(study,file),file);
  }
  assert.throws(()=>sourceAssetName(study,'not-published.gz'));
}
for (const file of ['brick-0-0-0.gz','brick-480-480-32.gz','segment-4a.mesh.gz','segment-8.mesh.gz']) {
  assert.equal(sourceAssetName('medseg-liver-001',file),file);
}
assert.throws(()=>sourceAssetName('unknown-study','brick-0-0-0.gz'));
assert.throws(()=>sourceAssetName('segthy-001',null));
assert.throws(()=>sourceAssetName('ct-torso-s0028','segment-4a.mesh.gz'));
let calls=0;
globalThis.fetch=()=>{calls++;throw Error('Unexpected Node HTTP request');};
for (const base of [undefined,'https://example.invalid/app/anatomy/segthy-001/viewer.js']) {
  assert.throws(()=>assetURL('left-0-0-0.gz',base));
  await assert.rejects(verifiedBytes({file:'left-0-0-0.gz'},undefined,base),/namespace/);
}
assert.equal(calls,0);
console.log('Published basenames preserved; offline HTTP requests rejected before fetch.');
'''
    result = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


def test_request_transport_preserves_the_prior_torso_and_source_delivery_proofs():
    import hashlib
    import json
    from tools.source_asset_requests_compatibility import PROOF, PIN, before_source_requests_bytes
    from tools.ct_torso_compatibility import before_torso_bytes
    proof = PROOF.read_bytes()
    assert hashlib.sha256(proof).hexdigest() == PIN
    torso = json.loads((ROOT/'docs/ct-torso-s0028/runtime-inverse.json').read_bytes())
    for path, row in json.loads(proof).items():
        raw = (ROOT/path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['after']
        original = before_source_requests_bytes(path, raw)
        assert hashlib.sha256(original).hexdigest() == row['before'] == torso[path]['after']
        assert hashlib.sha256(before_torso_bytes(path, raw)).hexdigest() == torso[path]['before']
        assert before_source_requests_bytes(path, raw+b'unreviewed') == raw+b'unreviewed'
    path = 'web/anatomy/segthy-001/delivery.json'
    current = json.loads((ROOT/path).read_bytes())['files']
    before = json.loads(before_source_requests_bytes(path, (ROOT/path).read_bytes()))['files']
    assert current.keys() == before.keys()
    assert {k:v for k,v in current.items() if k!='native-volume.mjs'} == {
        k:v for k,v in before.items() if k!='native-volume.mjs'}
