"""Original large specimen surfaces remain intact and cannot become a complete clinical atlas."""
import gzip,hashlib,json,struct
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'web/anatomy/openear-zeta';PROOF=ROOT/'docs/openear-native-source-review'
def sha(raw):return hashlib.sha256(raw).hexdigest()

def test_all_source_positions_and_faces_are_exactly_preserved_in_reader_transport():
    m=json.loads((OUT/'manifest.json').read_text());source=json.loads((PROOF/'ZETA-original-geometry-header-review.json').read_text());checks=json.loads((PROOF/'reader-geometry-package-review.json').read_text())
    assert len(m['parts'])==13 and m['total_triangles']==7349910
    for part,row,check in zip(m['parts'].values(),source['meshes'],checks['parts']):
        encoded=(ROOT/'web'/part['file'].removeprefix('/app/')).read_bytes();raw=gzip.decompress(encoded);magic,n,k=struct.unpack('<4sII',raw[:12])
        assert (magic,n,k)==(b'BP3D',row['vertices'],row['triangles']*3)
        assert sha(encoded)==part['sha256'] and sha(raw)==part['decoded_sha256'] and len(raw)==12+n*24+k*4
        assert sha(raw[12:12+n*12])==row['source_float32_position_sha256']
        assert sha(raw[12+n*24:])==row['source_int32_face_sha256']
        assert check['source_zero_area_triangles_retained']==row['zero_area_triangles']
        assert check['original_positions_and_faces_preserved_exactly'] and part['clinical_fidelity']=='unverified'
    assert not m['clinical_approval'] and not m['anatomical_approval'] and not m['photographic_texture_promoted']
    assert m['regions']['temporal-source']['lazy_layers'] and m['regions']['temporal-source']['source_coordinate_cameras']


def test_reader_attaches_original_specimen_photograph_without_calling_it_patient_CT():
    r=detail(Curriculum(),resolve('ra.ct-temporal-bone'))['radiology_reference'];e=next(e for e in r['source_anatomy_references'] if e['atlas']=='openear-zeta')
    assert e['initial_layer']=='source_structures' and not e['initial_cropped']
    assert e['manifest_sha256']==sha((OUT/'manifest.json').read_bytes())
    image=e['source_image'];assert image['width']==3606 and image['height']==3640
    assert sha((ROOT/'web'/image['src'].removeprefix('/app/')).read_bytes())==image['sha256']
    assert 'microscopy' in image['title'].lower() and 'prepared cadaver' in image['title'].lower()
    assert 'Patient anatomical directions and laterality are not independently verified' in e['population_note']


def test_every_source_model_keeps_empty_leaf_coverage_and_pending_review():
    assets=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'];rows=[a for a in assets if a['id'].startswith('openear-zeta-')]
    assert len(rows)==13
    for a in rows:
        assert a['kind']=='model' and not a['structure_ids'] and not a['requirement_coverage'] and a['anatomical_review']['status']=='pending'
        rights=a['source']['license'];assert rights['commercial_use'] and rights['redistribution']
        assert sha((ROOT/rights['evidence_path']).read_bytes())==rights['evidence_sha256']


def test_specimen_photo_rights_are_separate_from_CT_MRI_coverage():
    import copy
    import pytest
    from tools.msk_runtime_rights import audit_reference_image_rights
    ledger=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text());photo=next(a for a in ledger['reference_rights_assets'] if a['id']=='openear-zeta-original-microscopy135')
    inventory={'surfaces':['source-reference'],'images':[{'src':'/app/reference-media/openear-zeta/original-microscopy-135.png','uses':[]}]}
    result=audit_reference_image_rights(inventory,ledger,ROOT)
    assert result['counts']['cleared']==1 and photo['kind']=='anatomical_specimen_photo'
    assert not any(a['id']==photo['id'] for a in ledger['assets'])
    forged=copy.deepcopy(ledger);forged['reference_rights_assets'][0]['requirement_coverage']={'some_CT_structure':{'extent':'complete'}}
    with pytest.raises(ValueError,match='cannot carry'):audit_reference_image_rights(inventory,forged,ROOT)
