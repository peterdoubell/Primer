"""Native coordinate/label guards; source presentation is not anatomy approval."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import numpy as np
import pytest

from tools.anatomy_sources import reconcile_native_source_presentation as review

ROOT = Path(__file__).resolve().parents[1]


def test_original_forty_issues_remain_recorded_without_approval():
    path = ROOT / 'docs/native-source-presentation-review-20261011/initial-dependency-issues.json'
    data = json.loads(path.read_text())
    assert data['issue_count'] == len(data['original_issues']) == 40
    assert data['asset_count'] == len({row['id'] for row in data['original_issues']}) == 20
    assert {row['id'] for row in data['original_issues']} == set(review.SOURCE_IDS)
    assert all(row['anatomical_status'] == 'pending' for row in data['original_issues'])
    assert data['reconciliation_is_not_anatomical_approval']


def test_proposed_updates_require_native_reader_evidence_and_remain_pending():
    directory = ROOT / 'docs/native-source-presentation-review-20261011'
    contract = json.loads((directory / 'proposed-presentation-amendments.json').read_text())
    browser = json.loads((directory / 'reader-presentation-proof.json').read_text())
    assert browser['passed'] and not browser['errors'] and not browser['localHttpFailures']
    assert [r['width'] for r in browser['rows']] == [1440, 390]
    assert contract['source_presentation_verified'] and not contract['clinical_approval']
    assert not contract['fine_anatomical_approval'] and not contract['unrelated_holds_or_approvals_cleared']
    assert len(contract['amendments']) == 20 and contract['original_issue_count'] == 40
    assert len(contract['remaining_fine_boundary_gaps']) >= 5
    for amendment in contract['amendments']:
        assert amendment['anatomical_review_status_after'] == 'pending'
        assert not amendment['clinical_approval'] and not amendment['fine_3d_approval']
        assert amendment['requirement_coverage_after'] == {}
        assert amendment['original_issue_count'] == len(amendment['original_issues']) == 2
        assert 'anatomical_review' in amendment['preserve_fields_exactly']
        assert hashlib.sha256((ROOT / amendment['source_local_path']).read_bytes()).hexdigest() == amendment['unchanged_source_sha256']
    for row in browser['rows']:
        assert len(row['meshSelections']) == len(row['ct']) == 17 and len(row['liu']) == 2
        assert sum(len(p['slices']) for level in row['ct'] for p in level['planes']) == 153
        assert sum(len(p['pointers']) for level in row['ct'] for p in level['planes']) == 102
        assert all(p['outside'] for level in row['ct'] for p in level['planes'])


def test_review_evidence_is_portable_complete_and_byte_bound():
    directory = ROOT / 'docs/native-source-presentation-review-20261011'
    contract = json.loads((directory / 'proposed-presentation-amendments.json').read_text())
    for entry in contract['evidence']:
        path = Path(entry['path'])
        assert not path.is_absolute() and '..' not in path.parts
        assert path.parts[:2] == ('docs', 'native-source-presentation-review-20261011')
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == entry['sha256']
    browser = json.loads((directory / 'reader-presentation-proof.json').read_text())
    assert browser['api']['id'] == 'ra.thoracolumbar-fractures'
    review.validate_reader_oracles(browser, json.loads((directory / 'reader-native-oracles.json').read_text()))
    screenshots = json.loads((directory / 'screenshots.json').read_text())
    assert screenshots['screenshot_count'] == len(screenshots['screenshots']) == 6
    assert not screenshots['clinical_approval'] and not screenshots['raw_native_source_media_added']
    assert not screenshots['private_location_authoritative']
    for entry in [screenshots['attribution'], *screenshots['screenshots']]:
        data = (ROOT / entry['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry['sha256']
        if 'visually_inspected' in entry:
            assert entry['visually_inspected'] and data.startswith(b'\x89PNG\r\n\x1a\n')
            assert entry['license'] in {'CC BY 4.0', 'CC BY-SA 4.0'}


def test_contract_rejects_stale_served_proof_and_changed_native_pixels(tmp_path):
    directory = ROOT / 'docs/native-source-presentation-review-20261011'
    browser = json.loads((directory / 'reader-presentation-proof.json').read_text())
    browser['served']['web/app.js'] = '0' * 64
    stale = tmp_path / 'stale-reader.json'
    stale.write_text(json.dumps(browser))
    with pytest.raises(AssertionError, match='Reader proof is stale: web/app.js'):
        review.proposed_contract(directory / 'liu-native-coordinate-proof.json', stale)
    browser = json.loads((directory / 'reader-presentation-proof.json').read_text())
    browser['served']['web/styles.css'] = '0' * 64
    stale.write_text(json.dumps(browser))
    with pytest.raises(AssertionError, match='Reader proof is stale: web/styles.css'):
        review.proposed_contract(directory / 'liu-native-coordinate-proof.json', stale)
    browser = json.loads((directory / 'reader-presentation-proof.json').read_text())
    browser['rows'][0]['ct'][0]['planes'][0]['slices'][0]['rgba'] = '0' * 64
    with pytest.raises(AssertionError, match='Reader native pixel oracle mismatch'):
        review.validate_reader_oracles(browser, json.loads((directory / 'reader-native-oracles.json').read_text()))


def test_each_current_mesh_and_label_crop_uses_the_recorded_native_affine():
    from scipy.ndimage import map_coordinates
    dataset = review.embedded_verse_dataset()
    manifest = json.loads((ROOT / 'web/anatomy/verse521/manifest.json').read_text())
    assert dataset['axes'] == ['L', 'A', 'S']
    affine = np.asarray(dataset['affine'])
    inverse = np.linalg.inv(affine[:3, :3])
    assert np.array_equal(np.linalg.norm(affine[:3, :3], axis=0), dataset['spacing'])
    assert np.array_equal(np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]]).T @ np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]]), np.eye(3))
    chain = json.loads((ROOT / 'docs/msk-verse-source-review/chain-surface-audit.json').read_text())
    for item in dataset['levels']:
        level = item['level']
        label = int(level[1:]) + (7 if level.startswith('T') else 19)
        assert item['label'] == label
        part = manifest['parts']['verse521-' + level.lower()]
        v, normals, faces, encoded, decoded = review.mesh(ROOT / 'web' / part['file'].removeprefix('/app/'))
        assert encoded == part['sha256'] and decoded == part['decoded_sha256']
        assert part['source_label'] == label and part['clinical_fidelity'] == 'unverified'
        voxel = np.einsum('ni,ji->nj', v.astype(float) - affine[:3, 3], inverse)
        assert np.isfinite(voxel).all()
        ct_raw = gzip.decompress(base64.b64decode(item['ct']))
        membership_raw = gzip.decompress(base64.b64decode(item['mask']))
        assert hashlib.sha256(ct_raw).hexdigest() == item['ct_sha256']
        assert hashlib.sha256(membership_raw).hexdigest() == item['label_sha256']
        membership = np.frombuffer(membership_raw, 'u1').reshape(item['shape'])
        assert set(np.unique(membership)) == {0, 1} and int(membership.sum()) == item['foreground_voxels']
        scalar = map_coordinates(membership.astype(float), (voxel - np.asarray(item['start'])).T, order=1, mode='constant', cval=0)
        half_count = np.isclose(voxel - np.floor(voxel), .5, rtol=0, atol=1e-7).sum(axis=1)
        assert np.all(np.isin(half_count, [1, 3]))
        assert np.max(np.abs(scalar[half_count == 1] - .5)) < 1e-7
        expected = next(row for row in chain['levels'] if row['level'] == level)
        assert int((half_count == 3).sum()) == expected['cell_center_helper_vertices']
        assert np.max(np.abs(scalar - .5)) == pytest.approx(expected['maximum_saved_vertex_isovalue_residual'])
    assert manifest['clinical_approval'] is False


def test_pointer_readout_separates_all_seventeen_source_ids_from_membership(tmp_path):
    """Run the real helper by normal CommonJS import against tiny DOM fixtures."""
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node required')
    values = np.arange(100, 108, dtype='<f4').tobytes()
    mask = bytes([0, 0, 1, 0, 0, 0, 0, 0])
    levels = [{'level': level, 'label': label, 'shape': [2, 2, 2], 'start': [10, 20, 30], 'foreground_voxels': 1,
               'ct': base64.b64encode(gzip.compress(values)).decode(), 'mask': base64.b64encode(gzip.compress(mask)).decode()}
              for level, label in [(f'T{i}', i + 7) for i in range(1, 13)] + [(f'L{i}', i + 19) for i in range(1, 6)]]
    dataset = {'levels': levels, 'axes': ['L', 'A', 'S'], 'spacing': [1, 1, 1], 'affine': np.eye(4).tolist()}
    harness = tmp_path / 'native-pointer-fixture.cjs'
    harness.write_text(r'''
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const data=JSON.parse(fs.readFileSync(0,'utf8')),elements={};
class Element {
 constructor(id){this.id=id;this.value='0';this.children=[];this.listeners={};this.dataset={};this.style={};this.checked=true;this.textContent='';}
 append(e){this.children.push(e);}addEventListener(name,callback){this.listeners[name]=callback;}
 get selectedOptions(){return [this.children[Number(this.value)]||{text:'plane'}];}
 getContext(){return {createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData:()=>{}};}
 getBoundingClientRect(){return {left:100,top:200,right:300,bottom:300,width:200,height:100};}
}
for(const id of ['dataset','level','plane','slice','view','position','status','sample','scope','center','width','overlay','left','right','top','bottom','bone','soft'])elements[id]=new Element(id);
elements.dataset.textContent=JSON.stringify(data);elements.plane.value='2';elements.center.value='400';elements.width.value='1200';
global.document={getElementById:id=>elements[id],createElement:()=>new Element('option')};global.location={search:''};
require(process.argv[2]);
async function ready(){for(let count=0;count<100;count++){if(elements.view.dataset.ready==='true')return;await new Promise(r=>setTimeout(r,5));}throw new Error('helper did not decode fixture');}
(async()=>{let checked=0,zero=0,one=0,outside=0;
for(let i=0;i<data.levels.length;i++){
 elements.level.value=String(i);elements.level.listeners.change();await ready();
 const item=data.levels[i];
 for(let axis=0;axis<3;axis++)for(let slice=0;slice<2;slice++){
  elements.plane.value=String(axis);elements.plane.listeners.change();elements.slice.value=String(slice);elements.slice.listeners.input();
  for(let x=0;x<2;x++)for(let y=0;y<2;y++){
   elements.view.listeners.pointermove({clientX:100+(x+.5)*100,clientY:200+(y+.5)*50});
   const remaining=[0,1,2].filter(k=>k!==axis),point=[0,0,0];point[axis]=slice;point[remaining[0]]=x;point[remaining[1]]=1-y;
   const index=(point[0]*2+point[1])*2+point[2],membership=index===2;
   const expected=item.level+' · original source label '+item.label+' · source voxel '+point.map((v,k)=>v+item.start[k]).join(', ')+' · scaled CT '+(100+index)+' · target membership '+(membership?'present':'absent')+'.';
   assert.equal(elements.sample.textContent,expected);membership?one++:zero++;checked++;
  }
 }
 for(const [x,y]of [[99,250],[300,250],[200,199],[200,300],[NaN,250]]){
  elements.view.listeners.pointermove({clientX:x,clientY:y});assert.equal(elements.sample.textContent,item.level+' · original source label '+item.label+' · pointer outside image; no voxel sampled.');outside++;
 }
 elements.view.listeners.pointerleave({});assert.ok(elements.sample.textContent.endsWith('no voxel sampled.'));
}
assert.equal(checked,408);assert.ok(zero>0&&one>0);assert.equal(outside,85);
console.log(JSON.stringify({levels:data.levels.length,inside:checked,present:one,absent:zero,outside}));
})().catch(e=>{console.error(e);process.exitCode=1;});
''')
    result = subprocess.run([node, str(harness), str(ROOT / 'web/anatomy/verse521/ct-reference.js')],
                            input=json.dumps(dataset), capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    proof = json.loads(result.stdout)
    assert proof['levels'] == 17 and proof['inside'] == 408 and proof['outside'] == 85
    assert proof['present'] > 0 and proof['absent'] > 0


def test_pointer_sample_clears_during_pending_failed_and_superseded_loads(tmp_path):
    """Delay real gzip decoding so previous-level samples cannot survive a new request."""
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node required')
    encoded_ct = base64.b64encode(gzip.compress(np.arange(100, 108, dtype='<f4').tobytes())).decode()
    encoded_mask = base64.b64encode(gzip.compress(bytes([0, 0, 1, 0, 0, 0, 0, 0]))).decode()
    dataset = {'axes': ['L', 'A', 'S'], 'spacing': [1, 1, 1], 'affine': np.eye(4).tolist(), 'levels': [
        {'level': f'T{i}', 'label': 7 + i, 'shape': [2, 2, 2], 'start': [10, 20, 30],
         'foreground_voxels': 1, 'ct': encoded_ct, 'mask': encoded_mask} for i in [1, 2]]}
    harness = tmp_path / 'pending-pointer-fixture.cjs'
    harness.write_text(r'''
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),data=JSON.parse(fs.readFileSync(0,'utf8')),elements={};
class Element {
 constructor(id){this.id=id;this.value='0';this.children=[];this.listeners={};this.dataset={};this.style={};this.checked=true;this.textContent='';}
 append(e){this.children.push(e);}addEventListener(name,callback){this.listeners[name]=callback;}
 get selectedOptions(){return [this.children[Number(this.value)]||{text:'plane'}];}
 getContext(){return {createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData:()=>{}};}
 getBoundingClientRect(){return {left:100,top:200,right:300,bottom:300,width:200,height:100};}
}
for(const id of ['dataset','level','plane','slice','view','position','status','sample','scope','center','width','overlay','left','right','top','bottom','bone','soft'])elements[id]=new Element(id);
elements.dataset.textContent=JSON.stringify(data);elements.plane.value='2';elements.center.value='400';elements.width.value='1200';
global.document={getElementById:id=>elements[id],createElement:()=>new Element('option')};global.location={search:''};
let blocked=false,pending=[];const NativeResponse=global.Response;
global.Response=class extends NativeResponse {async arrayBuffer(){if(blocked)await new Promise((resolve,reject)=>pending.push({resolve,reject}));return super.arrayBuffer();}};
require(process.argv[2]);
async function until(predicate){for(let i=0;i<100;i++){if(predicate())return;await new Promise(r=>setTimeout(r,5));}throw Error('fixture wait timed out');}
function sample(){elements.view.listeners.pointermove({clientX:150,clientY:225});}
function pendingSample(){assert.equal(elements.view.dataset.ready,'false');assert.equal(elements.sample.textContent,'Source arrays loading; no voxel sampled.');elements.view.listeners.pointermove({clientX:99,clientY:250});elements.view.listeners.pointerleave({});assert.equal(elements.sample.textContent,'Source arrays loading; no voxel sampled.');}
(async()=>{
 await until(()=>elements.view.dataset.ready==='true');sample();assert.match(elements.sample.textContent,/T1 · original source label 8 · source voxel/);
 blocked=true;elements.level.value='1';elements.level.listeners.change();pendingSample();await until(()=>pending.length===2);pending.splice(0).forEach(x=>x.resolve());await until(()=>elements.view.dataset.ready==='true');sample();assert.match(elements.sample.textContent,/T2 · original source label 9 · source voxel/);
 elements.level.value='0';elements.level.listeners.change();pendingSample();await until(()=>pending.length===2);const failed=pending.splice(0);failed[0].reject(Error('controlled decode failure'));failed[1].resolve();await until(()=>elements.status.textContent.includes('controlled decode failure'));assert.equal(elements.view.dataset.ready,'false');assert.equal(elements.sample.textContent,'Source arrays unavailable; no voxel sampled.');elements.view.listeners.pointermove({clientX:99,clientY:250});elements.view.listeners.pointerleave({});assert.equal(elements.sample.textContent,'Source arrays unavailable; no voxel sampled.');
 elements.level.listeners.change();pendingSample();await until(()=>pending.length===2);const superseded=pending.splice(0);blocked=false;elements.level.value='1';elements.level.listeners.change();await until(()=>elements.view.dataset.ready==='true');sample();const current=elements.sample.textContent;superseded[0].reject(Error('stale failure'));superseded[1].resolve();await new Promise(r=>setTimeout(r,20));assert.equal(elements.view.dataset.ready,'true');assert.equal(elements.sample.textContent,current);assert.ok(!elements.status.textContent.includes('stale failure'));
 console.log(JSON.stringify({pending_cleared:true,error_cleared:true,superseded_error_ignored:true}));
})().catch(error=>{console.error(error);process.exitCode=1;});
''')
    result = subprocess.run([node, str(harness), str(ROOT / 'web/anatomy/verse521/ct-reference.js')],
                            input=json.dumps(dataset), capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert all(json.loads(result.stdout).values())
