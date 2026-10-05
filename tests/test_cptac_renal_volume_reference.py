"""Native 3D CT references retain acquisition, sampling, information and clinical limits."""
import gzip,hashlib,json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
PROVENANCE=ROOT/'docs/cptac-renal-source-review/volume-reference/export-provenance.json'


def test_full_native_acquisition_has_exact_shape_scale_and_separate_spacing_fields():
    m=json.loads(PROVENANCE.read_text())
    assert m['selected_acquisition_number']==1 and m['selected_acquisition_frames']==417
    assert m['other_acquisition_frames_retained_in_source_archive']==433
    assert m['texture_shape_xyz']==[512,512,417] and m['source_shape_zyx']==[417,512,512]
    assert m['uncompressed_bytes']==417*512*512*2
    assert m['source_spacing_xyz_mm']==[.976562,.976562,.625]
    assert m['declared_spacing_between_slices_mm']==2.5 and m['observed_interplane_step_mm']==.625
    assert m['origin_lps_mm']==[-252.1,-250,-251]
    assert m['source_rescale_slope']==1 and m['source_rescale_intercept']==-1024
    assert m['source_stored_values_round_trip_verified'] and m['source_value_encoding_changed']
    assert not m['source_information_changed'] and not m['source_voxels_resampled_cropped_or_dropped']
    assert not m['source_acquisitions_interleaved_or_deduplicated']
    assert len(m['frames'])==len({r['source_sop_instance_uid'] for r in m['frames']})==417
    assert [r['source_position_lps_mm'][2] for r in m['frames']]==[-251+i*.625 for i in range(417)]
    assert not m['annotation_or_segmentation_included'] and not m['named_phase_verified']
    assert not m['clinical_approval'] and not m['model_coverage_granted']


def test_source_identity_and_viewer_pins_are_the_exact_preserved_volume():
    m=json.loads(PROVENANCE.read_text());viewer=(ROOT/'tools/anatomy_sources/viewers/renal-volume/viewer.js').read_text()
    assert m['source_ct_archive_sha256']=='a9ab6c3999aa6d852db6a420dbad6a396cb7d2d3abf0bc3af9df946cbf5bf339'
    assert m['source_selection_sha256']=='7bdd465bf39303a2b3bb471067ecd172febac79de40b8dfa9924708e9145f82b'
    assert m['uncompressed_sha256']=='b83cf54557c17df4a8572e1cc81d3270e6927001763d54e8a432a7405d28fc6c'
    assert all(m[k] in viewer for k in ['source_ct_archive_sha256','source_selection_sha256','uncompressed_sha256'])
    assert 'verifyGPUProbes()' in viewer and 'gl.R16I' in viewer and 'gl.NEAREST' in viewer
    assert 'no downsampled substitute' in viewer
    assert m['license']=='CC BY 4.0'


def test_local_lossless_export_matches_every_plane_and_source_probe():
    m=json.loads(PROVENANCE.read_text());path=ROOT/'.research/cptac-renal-volume-reference'/m['file']
    if not path.exists():pytest.skip('Large licensed native volume is retained in ignored local staging')
    np=pytest.importorskip('numpy')
    packed=path.read_bytes();raw=gzip.decompress(packed)
    assert hashlib.sha256(packed).hexdigest()==m['compressed_sha256']
    assert hashlib.sha256(raw).hexdigest()==m['uncompressed_sha256']
    volume=np.frombuffer(raw,dtype='<i2').reshape(m['source_shape_zyx'])
    for frame in m['frames']:assert hashlib.sha256(volume[frame['index']].tobytes()).hexdigest()==frame['hu_plane_sha256']
    for probe in m['probes']:
        x,y,z=probe['index_xyz'];assert int(volume[z,y,x])==probe['hu']
