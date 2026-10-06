"""Original independent surface findings remain tied to native triangles and voxel context."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import zipfile
import pytest

ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT/'docs/spl-wall-source-review'


def test_all_original_contacts_are_reconstructed_and_quality_holds_remain():
    r=json.loads((REVIEW/'original-self-crossing-review.json').read_text());summary=json.loads((REVIEW/'independent-wall-contact-summary.json').read_text())
    assert r['complete_contact_evidence_sha256']==summary['uncompressed_sha256']
    assert r['source_review_sha256']==hashlib.sha256((REVIEW/'independent-wall-source-review.json').read_bytes()).hexdigest()
    assert len(r['records'])==24 and len(r['regions'])==6
    assert r['classifications']=={'nonparallel_original_strip_triangle_interior_crossing':24}
    assert Counter(i['label_value'] for i in r['records'])=={135:6,136:3,235:12,32:3}
    assert len(r['model_quality_holds'])==4 and all(i['label_value']!=236 for i in r['model_quality_holds'])
    assert all(i['status']=='original_surface_crossings_require_resolution_and_anatomical_review_before_clinical_promotion' for i in r['model_quality_holds'])
    assert min(i['contact_segment_length_mm'] for i in r['records'])==pytest.approx(.005590245762501221)
    assert max(i['contact_segment_length_mm'] for i in r['records'])==pytest.approx(3.939586231652264)
    assert all(min(w)>.001 for i in r['records'] for w in i['midpoint_barycentric_weights'])
    assert max(max(i['midpoint_reconstruction_errors_mm']) for i in r['records'])<2e-14
    assert all(not i['nearest_voxel_is_anatomical_adjudication'] and not i['source_geometry_changed'] for i in r['records'])
    assert not r['clinical_approval'] and not r['runtime_promoted']


def test_original_triangles_and_native_voxel_context_are_exact():
    np=pytest.importorskip('numpy')
    from tools.anatomy_sources.review_spl_wall_source import vtk,nrrd
    archive=ROOT/'.research/wall-independent-sources/spl-abdomen-2016-09.zip'
    if not archive.exists():pytest.skip('Independent source remains in ignored staging')
    r=json.loads((REVIEW/'original-self-crossing-review.json').read_text());source=json.loads((REVIEW/'independent-wall-source-review.json').read_text());meshes={}
    with zipfile.ZipFile(archive) as z:
        _,ct=nrrd(z.read('abdomen-2016-09/Data/I.nrrd'));_,labels=nrrd(z.read('abdomen-2016-09/Data/seg.nrrd'))
        for m in source['records']:
            v,n,f,*_=vtk(z.read(m['source_member']));meshes[m['label_value']]=(v,f)
        for record in r['records']:
            v,f=meshes[record['label_value']];ids=[i['source_face_index'] for i in record['original_source_faces']]
            assert np.array_equal(v[f[ids]].astype(float),record['original_triangles_ras'])
            i,j,k=record['nearest_native_voxel_ijk'];assert int(ct[k,j,i])==record['nearest_native_ct_stored_value']
            assert int(labels[k,j,i])==record['nearest_native_label_value']


def test_all_original_regions_and_contacts_remain_visible_in_source_context():
    r=json.loads((REVIEW/'original-self-crossing-location-review.json').read_text())
    assert r['source_crossing_review_sha256']==hashlib.sha256((REVIEW/'original-self-crossing-review.json').read_bytes()).hexdigest()
    assert len(r['figures'])==6 and sum(i['crossing_segments_displayed'] for i in r['figures'])==24
    assert sorted(i for f in r['figures'] for i in f['contact_record_indices'])==list(range(24))
    for f in r['figures']:
        assert hashlib.sha256((REVIEW/f['file']).read_bytes()).hexdigest()==f['sha256']
        assert not f['source_geometry_or_voxels_changed']
    assert not r['clinical_approval'] and not r['runtime_promoted']
