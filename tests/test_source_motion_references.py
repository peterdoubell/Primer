"""Source movies retain reviewed bytes and chronology without clinical coverage."""
import copy,hashlib,json
from pathlib import Path
import pytest
from primer.source_motion import validate_motion_references
ROOT=Path(__file__).resolve().parents[1];INV='ra.swallowing'
def registry():return json.loads((ROOT/'data/radiology/source-motion-references.json').read_text())
def test_source_and_transport_are_bound_to_all_reviewed_frames():
    data=registry();validate_motion_references(data,{INV},ROOT/'web');r=data[INV][0]
    proof=json.loads((ROOT/r['source_proof_path']).read_text());transport=json.loads((ROOT/r['transport_proof_path']).read_text())
    assert r['original_sha256']==proof['source']['sha256']==transport['original_movie_sha256']
    assert r['sha256']==transport['browser_movie_sha256'] and r['frames']==64
    assert transport['decoded_RGB_frame_sha256']==[f['decoded_RGB_sha256'] for f in proof['frames']]
    assert r['source_pts_seconds']==transport['source_pts_seconds'] and r['transport_pts_seconds']==transport['transport_pts_seconds']
    assert transport['maximum_transport_timestamp_rounding_seconds']<.001
    assert not r['motion_context']['modality_is_primary_VFSS'] and not r['motion_context']['independent_12_fps_sampling_verified']
@pytest.mark.parametrize('change',['coverage','clinical','unregistered_patient','time_order','dropped_frame','transport_hash','path_escape','nan_tolerance','negative_tolerance','paired_times','dimensions','paired_count'])
def test_movie_metadata_cannot_silently_become_clinical_or_different_source(change):
    data=copy.deepcopy(registry());r=data[INV][0]
    if change=='coverage':r['requirement_coverage']={'fake':{'extent':'complete'}}
    if change=='clinical':r['clinical_approval']=True
    if change=='unregistered_patient':r['motion_context']['current_patient_registered']=True
    if change=='time_order':r['transport_pts_seconds'][4]=r['transport_pts_seconds'][3]
    if change=='dropped_frame':r['source_pts_seconds'].pop()
    if change=='transport_hash':r['sha256']='0'*64
    if change=='nan_tolerance':r['max_transport_timestamp_error_seconds']=float('nan');r['transport_pts_seconds']=[2*t for t in r['transport_pts_seconds']]
    if change=='paired_times':r['source_pts_seconds']=[2*t for t in r['source_pts_seconds']];r['transport_pts_seconds']=[2*t for t in r['transport_pts_seconds']]
    if change=='dimensions':r['width']+=1
    if change=='paired_count':r['frames']-=1;r['source_pts_seconds'].pop();r['transport_pts_seconds'].pop()
    if change=='negative_tolerance':r['max_transport_timestamp_error_seconds']=-1
    if change=='path_escape':r['src']='/app/reference-media/radiology-motion/../movie.webm'
    with pytest.raises(ValueError):validate_motion_references(data,{INV},ROOT/'web')
def test_motion_rights_are_inspected_but_never_grant_anatomical_coverage():
    from tools.msk_runtime_rights import audit_reference_image_rights
    from tools.check_msk_fidelity import inspect_asset
    ledger=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text());row=registry()[INV][0];inventory={'surfaces':['reporting:'+INV],'images':[{'src':row['src'],'uses':[]},{'src':row['original_src'],'uses':[]}]};result=audit_reference_image_rights(inventory,ledger,ROOT)
    assert result['counts']['cleared']==2
    for r in ledger['reference_rights_assets']:
        if r['kind']=='source_motion_reference':
            assert not r['structure_ids'] and not r['requirement_coverage']
            with pytest.raises(ValueError,match='Unknown representation kind'):inspect_asset(r,ROOT,'')


def test_playback_clock_fallback_uses_active_interval_not_nearest_frame():
    import shutil,subprocess
    if not shutil.which('node'):pytest.skip('Node unavailable')
    code="""const assert=require('node:assert/strict');global.window={addEventListener(){}};global.document={addEventListener(){}};const {sourceMotionFrameAtTime}=require('./web/app.js');const t=[0,.081,.162,.243];for(const [time,index] of [[0,0],[.061,0],[.081,1],[.142,1],[.162,2],[.242999,2],[.243,3],[5,3]])assert.equal(sourceMotionFrameAtTime(t,time),index);"""
    result=subprocess.run(['node','-e',code],cwd=ROOT,capture_output=True,text=True);assert result.returncode==0,result.stderr
