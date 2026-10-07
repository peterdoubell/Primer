"""Transport and reader checks do not imply independently approved anatomy."""
import collections,gzip,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ATLAS='totalseg-v3-s0358';PROOF=ROOT/'docs/thyroid-native-source-review/s0358'
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
    assert total==manifest['total_triangles']==52040
    assert manifest['parts'][ATLAS+'-thyroid_gland']['source_components']==2
    for side in ['left','right']:assert manifest['parts'][ATLAS+'-common_carotid_artery_'+side]['source_boundary_edges']==22
    assert not manifest['clinical_approval'] and not manifest['anatomical_approval'] and not manifest['complete_thyroid_geometry_verified']
def test_reader_is_explicitly_partial_CT_context_with_no_US_or_leaf_approval():
    from primer.curriculum import Curriculum
    from primer.radiology_catalog import detail,resolve
    ref=detail(Curriculum(),resolve('ra.ultrasound-thyroid'))['radiology_reference'];entry=ref['source_anatomy_references'][0];assert entry['atlas']==ATLAS and entry['initial_cropped'] is False
    assert 'not a dedicated neck CT' in entry['population_note'] and 'no ultrasound echogenicity' in entry['population_note']
    ledger=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[r for r in ledger if r['id'].startswith(ATLAS+'-')];assert len(rows)==8
    for r in rows:
        assert not r['structure_ids'] and not r['requirement_coverage'] and r['anatomical_review']['status']=='pending'
        grant=r['source']['license'];assert grant['commercial_use'] and grant['redistribution'];assert sha((ROOT/grant['evidence_path']).read_bytes())==grant['evidence_sha256']
