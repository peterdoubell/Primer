"""Transport and reader checks do not imply independently approved anatomy."""
import collections,gzip,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ATLAS='totalseg-v3-esophagus-s0358';PROOF=ROOT/'docs/esophagus-native-context-review/s0358'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def test_all_source_faces_and_coordinates_survive_transport_with_open_boundaries():
    manifest=json.loads((ROOT/'web/anatomy'/ATLAS/'manifest.json').read_text());native=json.loads((PROOF/'native-source-review.json').read_text());total=0
    for row in native['targets']:
        stem=row['file'].removesuffix('.nii.gz');part=manifest['parts'][ATLAS+'-'+stem];encoded=(ROOT/'web'/part['file'].removeprefix('/app/')).read_bytes();assert sha(encoded)==part['sha256'];raw=gzip.decompress(encoded);assert sha(raw)==part['decoded_sha256'];magic,n,indices=struct.unpack('<4sII',raw[:12]);assert magic==b'BP3D' and indices==row['triangles']*3
        faces=raw[12+n*24:];original=gzip.decompress((PROOF/(stem+'-triangles.u32.gz')).read_bytes());assert faces==original and sha(faces)==row['triangles_sha256']
        vertices=gzip.decompress((PROOF/(stem+'-positions.f64.gz')).read_bytes());assert sha(vertices)==row['positions_sha256'];maximum=0
        for i,(value,) in enumerate(struct.iter_unpack('<d',vertices)):
            maximum=max(maximum,abs(value-struct.unpack_from('<f',raw,12+i*4)[0]))
        assert maximum<=4e-5
        edges=collections.Counter()
        for a,b,c in struct.iter_unpack('<III',faces):
            for x,y in [(a,b),(b,c),(c,a)]:edges[tuple(sorted((x,y)))]+=1
        assert sum(v==1 for v in edges.values())==row['boundary_edges'];assert all(v<=2 for v in edges.values());total+=indices//3
    assert total==manifest['total_triangles']==686252
    assert manifest['parts'][ATLAS+'-spinal_cord']['source_boundary_edges']==40
    assert manifest['parts'][ATLAS+'-heart']['source_components']==47
    assert manifest['parts'][ATLAS+'-lung_upper_lobe_left']['source_components']==137
    assert not manifest['clinical_approval'] and not manifest['anatomical_approval'] and not manifest['complete_esophageal_geometry_verified']
def test_reader_keeps_source_case_and_pending_all_structure_scope():
    from primer.curriculum import Curriculum
    from primer.radiology_catalog import detail,resolve
    ref=detail(Curriculum(),resolve('ra.esophagus'))['radiology_reference'];entry=next(r for r in ref['source_anatomy_references'] if r['atlas']==ATLAS)
    assert entry['initial_cropped'] is False and entry['family']=='esophagus-source'
    assert 'not a normal esophageal atlas' in entry['population_note'] and 'patient laterality is not independently verified' in entry['population_note']
    ledger=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[r for r in ledger if r['id'].startswith(ATLAS+'-')];assert len(rows)==27
    assert not any(r['id'].startswith('totalseg-v3-s0358-') for r in rows)
    for r in rows:
        assert not r['structure_ids'] and not r['requirement_coverage'] and r['anatomical_review']['status']=='pending'
        grant=r['source']['license'];assert grant['commercial_use'] and grant['redistribution'];assert sha((ROOT/grant['evidence_path']).read_bytes())==grant['evidence_sha256']
    other=detail(Curriculum(),resolve('ra.ultrasound-thyroid'))['radiology_reference'];assert all(x['atlas']!=ATLAS for x in other['source_anatomy_references'])
def test_hosted_missing_mesh_uses_only_verified_static_contract(monkeypatch,tmp_path):
    from primer.source_mesh_integrity import verified_mesh_contract
    import pytest
    data=ROOT/'data/radiology';manifest=json.loads((ROOT/'web/anatomy'/ATLAS/'manifest.json').read_text());part=next(iter(manifest['parts'].values()));monkeypatch.setenv('VERCEL','1')
    header,size=verified_mesh_contract(part,tmp_path/ATLAS,data)
    assert struct.unpack('<4sII',header)==(b'BP3D',part['vertices'],part['triangles']*3)
    assert size==12+part['vertices']*24+part['triangles']*12
    changed=dict(part,sha256='0'*64)
    with pytest.raises(ValueError,match='differs'):verified_mesh_contract(changed,tmp_path/ATLAS,data)
