import copy,json,hashlib
from pathlib import Path
import pytest
from primer import radiology_catalog as catalog
from primer.curriculum import Curriculum
from tools.check_msk_fidelity import requirements_for,inspect_requirement_coverage

ROOT=Path(__file__).resolve().parents[1]


def test_native_ct_image_has_source_provenance_and_no_model_approval():
    ref=catalog.detail(Curriculum(),catalog.resolve('ra.ct-airways'))['radiology_reference']
    image=next(x for x in ref['structure_atlas'] if x['id']=='native-aeropath-case1-ct')
    assert image['origin']=='native-volume-sections' and image['modality']=='CT'
    assert 'figure_number' not in image and 'not designated normal' in image['caption']
    raw=(ROOT/'web'/image['src'].removeprefix('/app/')).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==image['sha256']
    proof=json.loads((ROOT/'web'/image['derivation']['evidence_url'].removeprefix('/app/')).read_text())
    assert proof['clinical_approval'] is False and proof['model_geometry_overlaid'] is False
    assert len(proof['planes'])==3
    evidence=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())
    asset=next(a for a in evidence['assets'] if a['id']==image['id'])
    inv=next(i for i in json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'] if i['investigation_id']=='ra.ct-airways')
    leaves={x['id']:x for x in requirements_for(inv)}
    assert len(asset['structure_ids'])==4 and asset['anatomical_review']['status']=='pending'
    assert all(inspect_requirement_coverage(asset,leaves[k])==['requirement_coverage_partial'] for k in asset['structure_ids'])
    assert not any('wall' in k or 'rb' in k or 'lb' in k for k in asset['structure_ids'])


@pytest.mark.parametrize('change',['fake_publisher_number','wrong_hash','bad_dimensions','escaping_provenance','wrong_modality'])
def test_native_source_figure_contract_tampering_is_rejected(monkeypatch,change):
    original=catalog._read
    def altered(name,default=None):
        data=copy.deepcopy(original(name,default))
        if name=='radiology-open-images.json':
            image=data['ra.ct-airways'][0]
            if change=='fake_publisher_number':image['figure_number']=1
            elif change=='wrong_hash':image['derivation']['evidence_sha256']='0'*64
            elif change=='bad_dimensions':image['width']=1
            elif change=='escaping_provenance':image['derivation']['evidence_url']='/app/reference-media/radiology-open/../../index.html'
            else:image['modality']='MRI'
        return data
    catalog._structure_atlases.cache_clear();monkeypatch.setattr(catalog,'_read',altered)
    try:
        with pytest.raises(ValueError):catalog._structure_atlases()
    finally:catalog._structure_atlases.cache_clear()
