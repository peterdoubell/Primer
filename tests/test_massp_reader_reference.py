import gzip,hashlib,json,struct
from pathlib import Path
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog

ROOT=Path(__file__).resolve().parents[1]


def test_partial_population_reference_preserves_the_whole_brain_context():
    ref=catalog.detail(Curriculum(),catalog.resolve('ra.brain-anatomy'))['radiology_reference']
    entries=ref['source_anatomy_references']
    assert [x['atlas'] for x in entries]==['massp2-subcortex','bodyparts3d']
    assert entries[0]['initial_cropped'] is False
    assert 'independent of BodyParts3D' in entries[0]['population_note']
    assert ref['walkthrough']['steps'][1]['parts']==[]
    assert ref['walkthrough']['spatial_model']['family']=='brain'
    image=entries[0]['source_image']
    assert '105 adults' in image['caption'] and '97 adults' in image['caption']
    assert 'unverified' in image['caption']


def test_every_packaged_structure_has_a_byte_bound_complete_transport_contract():
    manifest=json.loads((ROOT/'web/anatomy/massp2-subcortex/manifest.json').read_text())
    assert manifest['clinical_approval'] is False
    assert manifest['coordinate_system']['basis']=='RAS'
    assert len(manifest['parts'])==6
    assert manifest['total_triangles']==329192
    report=json.loads((ROOT/'docs/brain-massp-source-review/reader-package.json').read_text())
    for row in report['parts']:
        part=manifest['parts'][row['id']]
        raw=(ROOT/'web'/part['file'].removeprefix('/app/')).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==part['sha256']
        decoded=gzip.decompress(raw)
        assert hashlib.sha256(decoded).hexdigest()==part['decoded_sha256']
        magic,vertices,indices=struct.unpack('<4sII',decoded[:12])
        assert magic==b'BP3D' and len(decoded)==12+vertices*24+indices*4
        assert indices==part['triangles']*3 and vertices==part['vertices']
        assert row['faces_unchanged'] and row['maximum_position_conversion_error_mm']<=2e-6
        assert part['clinical_fidelity']=='unverified'


def test_source_licensing_and_interpretation_do_not_grant_anatomical_approval():
    evidence=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())
    models=[a for a in evidence['assets'] if a['id'].startswith('reader-massp2-') and a['kind']=='model']
    assert len(models)==6
    assert all(a['anatomical_review']['status']=='pending' for a in models)
    assert all(next(iter(a['requirement_coverage'].values()))['extent']=='partial' for a in models)
    assert all(a['source']['license']['review_status']=='verified' for a in models)
