"""Clinical source display movies remain distinct from acquired functional proof."""
import copy,hashlib,json,shutil
from pathlib import Path
import pytest
from primer.source_motion import validate_motion_references
from primer.source_motion_contract import parse_motion_contract
from primer.source_motion_integrity import verified_motion_contract
ROOT=Path(__file__).resolve().parents[1]
def registry():return json.loads((ROOT/'data/radiology/source-motion-references.json').read_text())
def test_every_source_frame_byte_contract_and_role_is_retained():
    data=registry();validate_motion_references(data,set(data),ROOT/'web');rows=data['ra.tinnitus'];proof=json.loads((ROOT/'docs/tinnitus-motion-source-review/original-and-browser-transport-review.json').read_text())['movies'];assert len(rows)==len(proof)==2
    assert [r['modality'] for r in rows]==['CT','Radiography']
    for r,p in zip(rows,proof):
        assert r['frames']==12 and r['width']==r['height']==1024
        assert p['all_12_decoded_RGB_frames_identical'] and len(p['native_rgb555le_frame_sha256'])==len(p['original_and_browser_decoded_RGB_sha256'])==12
        assert p['source_contract']['pts_seconds']==[i/3 for i in range(12)]
        assert not r['motion_context']['independent_3fps_acquisition_verified'] and not r['motion_context']['calibrated_flow_pressure_or_reflux_grade_verified']
        assert not r['motion_context']['current_patient_registered'] and not r['requirement_coverage'] and not r['structure_ids']
        for key,sha in [('src','sha256'),('original_src','original_sha256')]:
            raw=(ROOT/'web'/r[key].removeprefix('/app/')).read_bytes();assert hashlib.sha256(raw).hexdigest()==r[sha];contract=parse_motion_contract(raw);assert contract['frames']==12
    assert 'processed' in rows[0]['title'].lower() and 'MIP' in rows[0]['title']
def test_hosted_missing_movie_requires_exact_release_inventory(monkeypatch,tmp_path):
    row=registry()['ra.tinnitus'][0];monkeypatch.delenv('VERCEL',raising=False)
    with pytest.raises(ValueError,match='missing'):verified_motion_contract(tmp_path/'missing',row['src'],row['sha256'],ROOT/'data/radiology')
    monkeypatch.setenv('VERCEL','1');contract=verified_motion_contract(tmp_path/'missing',row['src'],row['sha256'],ROOT/'data/radiology');assert contract['frames']==12
    with pytest.raises(ValueError,match='differs'):verified_motion_contract(tmp_path/'missing',row['src'],'0'*64,ROOT/'data/radiology')
    simulated=tmp_path/'web/reference-media/radiology-motion';simulated.mkdir(parents=True);shutil.copytree(ROOT/'data/radiology',tmp_path/'data/radiology')
    validate_motion_references({'ra.tinnitus':registry()['ra.tinnitus']},{'ra.tinnitus'},tmp_path/'web')
@pytest.mark.parametrize('change',['times','count','dimensions','coverage'])
def test_changed_movie_contract_cannot_pass_hosted_metadata(monkeypatch,tmp_path,change):
    data={'ra.tinnitus':copy.deepcopy(registry()['ra.tinnitus'])};r=data['ra.tinnitus'][0]
    if change=='times':r['source_pts_seconds']=[2*t for t in r['source_pts_seconds']];r['transport_pts_seconds']=[2*t for t in r['transport_pts_seconds']]
    if change=='count':r['frames']=11;r['source_pts_seconds'].pop();r['transport_pts_seconds'].pop()
    if change=='dimensions':r['width']-=1
    if change=='coverage':r['requirement_coverage']={'fake':{'extent':'complete'}}
    with pytest.raises(ValueError):validate_motion_references(data,set(data),ROOT/'web')
