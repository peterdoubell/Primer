"""Original renal annotation coordinates are planar lines, not a fitted kidney surface."""
import hashlib,json,shutil,subprocess
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/cptac-renal-source-review/volume-reference'


def test_every_source_contour_references_the_exact_native_acquisition_plane():
    source=json.loads((FOLDER/'original-source-polylines.json').read_text());volume=json.loads((FOLDER/'export-provenance.json').read_text())
    assert source['source_volume_provenance_sha256']==hashlib.sha256((FOLDER/'export-provenance.json').read_bytes()).hexdigest()
    assert source['source_volume_uncompressed_sha256']==volume['uncompressed_sha256']
    assert source['source_contours']==len(source['contours'])==75
    assert source['source_points']==sum(c['points'] for c in source['contours'])==5341
    assert len({c['native_acquisition1_plane_index'] for c in source['contours']})==75
    for c in source['contours']:
        frame=volume['frames'][c['native_acquisition1_plane_index']]
        assert frame['source_sop_instance_uid']==c['source_ct_sop']
        assert c['geometric_type']=='CLOSED_PLANAR'
        assert len(c['source_decimal_lps_xyz_mm'])==3*c['points']
        assert all(isinstance(v,str) for v in c['source_decimal_lps_xyz_mm'])
        assert all(float(v)==frame['source_position_lps_mm'][2] for v in c['source_decimal_lps_xyz_mm'][2::3])
    assert min(c['native_acquisition1_plane_index'] for c in source['contours'])==143
    assert max(c['native_acquisition1_plane_index'] for c in source['contours'])==217


def test_source_roi_volume_and_clinical_limits_are_not_silently_reinterpreted():
    source=json.loads((FOLDER/'original-source-polylines.json').read_text())
    assert source['source_rois'][0]['source_name']=='RT KIDNEY - 1'
    assert source['source_rois'][0]['generation_algorithm']=='MANUAL'
    assert source['source_rois'][0]['declared_roi_volume_decimal_cm3']=='35.685833'
    assert not source['source_rois'][0]['independent_whole_organ_or_histology_verified']
    assert not source['whole_kidney_segmentation'] and not source['surface_or_voxel_mask_created']
    assert not source['source_points_transformed_repaired_or_rounded']
    assert not source['different_acquisitions_registered_or_joined']
    assert not source['clinical_approval'] and not source['model_coverage_granted']
    assert source['license']=='CC BY 4.0'


def test_browser_mapping_conserves_every_original_coordinate_with_measured_precision():
    node=shutil.which('node')
    if not node:pytest.skip('Node unavailable for independent native-coordinate display mapping checks')
    r=subprocess.run([node,str(ROOT/'tools/check_renal_source_polyline_mapping.js')],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    assert '5,341 points' in r.stdout and 'reversible LPS display mapping' in r.stdout


def test_uploaded_outline_buffers_preserve_all_source_points_without_surface_credit():
    receipt=json.loads((FOLDER/'full-gpu-readback.json').read_text())
    state=receipt['sourceContourState']
    assert state['verified'] and state['allGPUPointBuffersVerified']
    assert state['contours']==75 and state['points']==5341
    assert state['maximumFloat32DisplayErrorMm']<.000004
    assert not state['sourceCoordinatesChanged'] and not state['surfaceCreated']
    assert not state['wholeKidney'] and not state['clinicalApproval']
    script=ROOT/'tools/anatomy_sources/viewers/renal-volume/source-lines.js'
    assert hashlib.sha256(script.read_bytes()).hexdigest()==receipt['source_line_script_sha256']
