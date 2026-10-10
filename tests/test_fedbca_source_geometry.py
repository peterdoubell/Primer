"""Complete original source values and label-cell geometry cannot imply clinical truth."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct

import numpy as np
import pytest

from tools.anatomy_sources.review_fedbca_sources import read_nifti
from tools.anatomy_sources.build_fedbca_label_surfaces import cell_boundary, CASES
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT=Path(__file__).resolve().parents[1]
PROOF=ROOT/'docs/fedbca-bladder-source-review'


def test_complete_cohort_counts_and_each_table_association_are_preserved():
    summary=json.loads((PROOF/'summary.json').read_text());raw=(PROOF/'complete-source-review.json.gz').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==summary['review_sha256']
    review=json.loads(gzip.decompress(raw));records=review['complete_source_records'];pairs=review['complete_table_pairs']
    assert len(records)==496 and len(pairs)==275
    assert len({p['mask_member'] for p in pairs})==275 and len({p['image_member'] for p in pairs})==221
    assert sum(p['selected_affines_bit_identical'] for p in pairs)==38
    assert len(review['blank_source_table_rows_retained'])==3
    assert sum(r['source_voxels'] for r in records.values())==1937729152
    assert all(r['all_stored_values_independently_decoded'] for r in records.values())
    assert not review['original_DICOM_acquisitions_received'] and not review['clinical_approval']
    for p in pairs:
        assert records[p['image_member']]['dimensions']==records[p['mask_member']]['dimensions']
        assert not p['image_or_mask_fitted_resampled_or_modified']


@pytest.mark.parametrize('center,case',CASES)
def test_every_original_case_sample_geometry_and_component_reaches_model_and_viewer(center,case):
    key=center.lower()+'-'+case;atlas='fedbca-'+key
    source=json.loads((PROOF/'source-surface-review.json').read_text());row=next(r for r in source if r['case_id']==key)
    image,A,ih=read_nifti(PROOF/(center+'-T2WI-'+case+'.nii.gz'));mask,B,mh=read_nifti(PROOF/(center+'-Annotation-'+case+'.nii.gz'))
    assert image.shape==mask.shape and set(np.unique(mask))=={0,1}
    assert int((mask==1).sum())==row['source_label_voxels']
    pos=np.frombuffer(gzip.decompress((PROOF/(key+'-positions.f64.gz')).read_bytes()),'<f8').reshape(-1,3)
    faces=np.frombuffer(gzip.decompress((PROOF/(key+'-triangles.u32.gz')).read_bytes()),'<u4').reshape(-1,3)
    # Independent inverse-coordinate recovery proves every point is an exact
    # source cell corner rather than a fitted biological contour.
    inverse=np.linalg.inv(B[:3,:3]);grid=np.column_stack([sum((pos[:,k]-B[k,3])*inverse[j,k] for k in range(3)) for j in range(3)])
    assert np.max(np.abs(grid*2-np.round(grid*2)))<1e-9
    assert np.all(np.mod(np.round(grid*2).astype(np.int64),2)==1)
    origin=pos.mean(0);tri=pos[faces]-origin;volume=np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6
    assert np.isclose(volume,(mask==1).sum()*abs(np.linalg.det(B[:3,:3])),rtol=1e-10,atol=1e-7)
    manifest=json.loads((ROOT/'web/anatomy'/atlas/'manifest.json').read_text());part=next(iter(manifest['parts'].values()))
    packed=(ROOT/'web'/part['file'].removeprefix('/app/')).read_bytes();decoded=gzip.decompress(packed)
    assert hashlib.sha256(packed).hexdigest()==part['sha256']
    assert struct.unpack('<4sII',decoded[:12])==(b'BP3D',len(pos),faces.size)
    assert np.array_equal(np.frombuffer(decoded,'<u4',count=faces.size,offset=12+len(pos)*24).reshape(-1,3),faces)
    assert np.max(np.abs(np.frombuffer(decoded,'<f4',count=pos.size,offset=12).reshape(-1,3).astype(float)-pos))<1e-4
    assert part['source_components']==row['components_6_connected']
    assert not manifest['clinical_approval'] and not manifest['complete_reporting_anatomy_approved']
    html=(ROOT/'web/anatomy'/atlas/'mri-reference.html').read_text();data=json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>',html,re.S).group(1))
    for name,array,h in [('image',image,ih),('mask',mask,mh)]:
        payload=gzip.decompress((ROOT/'web/anatomy'/atlas/data[name]['file']).read_bytes())
        assert payload==array.tobytes(order='F') and hashlib.sha256(payload).hexdigest()==h['raw_source_voxel_sha256']
    assert data['source_voxels']==image.size+mask.size
    assert np.array_equal(data['image']['selected_affine'],A) and np.array_equal(data['mask']['selected_affine'],B)


def test_tiny_disconnected_annotation_component_is_retained():
    row=next(r for r in json.loads((PROOF/'source-surface-review.json').read_text()) if r['case_id']=='center2-01')
    assert row['components_6_connected']==2 and sorted(row['component_voxel_counts'])==[2,38456]
    mask,_,_=read_nifti(PROOF/'Center2-Annotation-01.nii.gz')
    assert mask[315,167,12]==mask[316,167,12]==1
    assert sum(mask[315+dx,167+dy,12+dz] for dx,dy,dz in [(0,0,-1),(0,0,1),(0,-1,0),(0,1,0),(-1,0,0),(1,0,0)])==1
    assert not row['source_labels_modified_or_components_deleted']
    assert not row['surface_smoothed_decimated_fitted_or_hole_repaired']


def test_exact_voxel_cell_union_has_independently_known_geometry():
    mask=np.zeros((4,4,4),np.uint16);mask[1,1,1]=1;mask[2,1,1]=1
    affine=np.eye(4);affine[:3,:3]=np.diag([-2,3,5]);affine[:3,3]=[70,80,90]
    pos,faces,proof=cell_boundary(mask,affine)
    assert len(pos)==12 and len(faces)==20 and proof['original_exposed_cell_faces']==10
    assert proof['boundary_edges']==proof['nonmanifold_edges']==0
    assert np.isclose(proof['signed_cell_boundary_volume_source_mm3'],60)
    assert np.array_equal(pos.min(0),[65,81.5,92.5]) and np.array_equal(pos.max(0),[69,84.5,97.5])


def test_bad_scalar_extent_or_degenerate_form_is_rejected(tmp_path):
    original=PROOF/'Center4-T2WI-01.nii.gz';raw=bytearray(gzip.decompress(original.read_bytes()));path=tmp_path/'bad.nii.gz'
    path.write_bytes(gzip.compress(raw[:-2],mtime=0))
    with pytest.raises(ValueError,match='extent'):read_nifti(path)
    struct.pack_into('<2h',raw,252,0,0);path.write_bytes(gzip.compress(raw,mtime=0))
    with pytest.raises(ValueError,match='spatial form'):read_nifti(path)


def test_reference_cases_are_separate_from_hra_and_the_original_tcia_study():
    ref=detail(Curriculum(),resolve('ra.mri-bladder'))['radiology_reference']
    sources=[s for s in ref['source_anatomy_references'] if s['atlas'].startswith('fedbca-')]
    assert len(sources)==4 and len({s['atlas'] for s in sources})==4
    assert len(ref['source_study_references'])==1 and ref['source_study_references'][0]['id']=='tcga-dk-aa6p'
    assert all(s['source_volume']['src'].startswith('/app/anatomy/'+s['atlas']+'/') for s in sources)


def test_both_source_arrays_are_required_even_when_hosted(monkeypatch):
    from unittest.mock import patch
    from primer.source_volume_integrity import verified_volume_identity
    import copy
    ref=detail(Curriculum(),resolve('ra.mri-bladder'))['radiology_reference']
    volume=copy.deepcopy(next(s for s in ref['source_anatomy_references'] if s['atlas']=='fedbca-center4-01')['source_volume'])
    missing=copy.deepcopy(volume);missing['data_files'].pop()
    with pytest.raises(ValueError,match='both complete'):verified_volume_identity(missing,ROOT/'web',ROOT/'data/radiology')
    original=Path.is_file
    with patch.object(Path,'is_file',lambda p:False if 'fedbca-center4-01' in p.parts and p.name.endswith(('.html','.bin.gz')) else original(p)):
        monkeypatch.delenv('VERCEL',raising=False)
        with pytest.raises(ValueError,match='missing'):verified_volume_identity(volume,ROOT/'web',ROOT/'data/radiology')
        monkeypatch.setenv('VERCEL','1');assert verified_volume_identity(volume,ROOT/'web',ROOT/'data/radiology')>0
        volume['data_files'][0]['raw_source_voxel_sha256']='0'*64
        with pytest.raises(ValueError,match='inventory'):verified_volume_identity(volume,ROOT/'web',ROOT/'data/radiology')


def test_every_current_case_model_prop_matches_its_full_current_delivery_proof():
    from primer.module_media import source_model_bindings
    from tools.check_radiology_fidelity import digest
    curr=Curriculum();proof=json.loads((PROOF/'current-source-delivery-review.json').read_text());bindings=source_model_bindings()
    # The retained case-delivery proof precedes the separately reviewed Sella
    # registration; its original contracts must remain exactly reproducible.
    reviewed_ids={row['module_id'] for row in proof['modules']}
    reviewed_bindings={key:value for key,value in bindings.items() if key in reviewed_ids}
    assert set(reviewed_bindings)=={row['module_id'] for row in proof['modules']}
    assert proof['matching_lessons']==len(reviewed_bindings)==11 and proof['source_references']==20
    fields=['goal','learning_outcomes','lesson','reference','radiology_reference','visual_spec','lesson_media','model_family','model_context','practice','quiz','kid_text']
    for row in proof['modules']:
        node=curr.node(row['module_id']);model=next(m for m in node['lesson_media'] if m.get('renderer')=='radiology-anatomy')
        assert digest({k:node.get(k) for k in fields})==row['current_module_contract_sha256']
        assert digest(model['props'])==row['model_props_sha256']
        assert digest(bindings[node['id']])==row['source_references_sha256']


def test_viewer_script_and_scalar_files_are_published_with_the_static_viewer():
    import fnmatch
    config=json.loads((ROOT/'vercel.json').read_text());patterns=[b['src'] for b in config['builds'] if b['use']=='@vercel/static']
    def expanded(pattern):
        if '{' not in pattern:return [pattern]
        before,rest=pattern.split('{',1);options,after=rest.split('}',1)
        return [before+item+after for item in options.split(',')]
    for center,case in CASES:
        prefix='web/anatomy/fedbca-'+center.lower()+'-'+case+'/'
        for filename in ['mri-reference.html','mri-reference.js','source-image.bin.gz','source-label.bin.gz']:
            path=prefix+filename
            # **/* also includes files directly within the matched folder.
            assert any(fnmatch.fnmatch(path,p) or fnmatch.fnmatch(path,p.replace('/**/','/')) for pattern in patterns for p in expanded(pattern))
