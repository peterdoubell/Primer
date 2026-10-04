"""The full packet retains source pixels, positional roles and paper-background requirements."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
from PIL import Image
from primer.curriculum import Curriculum
from primer import radiology_catalog

ROOT=Path(__file__).resolve().parents[1]


def test_all_nine_figures_are_delivered_with_original_samples_and_explicit_roles():
    ref=radiology_catalog.detail(Curriculum(),radiology_catalog.resolve('ra.ultrasound-gallbladder'))['radiology_reference']
    rows={r['id']:r for r in ref['structure_atlas'] if r['id'].startswith('open-gallbladder-')}
    proof=json.loads((ROOT/'docs/gallbladder-published-source-review/original-source-review.json').read_text())
    assert len(rows)==9
    for source in proof['figures']:
        r=rows['open-gallbladder-'+source['pmcid'].lower()+'-fig'+str(source['figure_number'])]
        path=ROOT/'web'/r['src'].removeprefix('/app/')
        assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']==r['sha256']
        with Image.open(path) as image:assert hashlib.sha256(image.tobytes()).hexdigest()==source['decoded_pixel_sha256']
        assert r['source_background']=='white'
    masked=rows['open-gallbladder-pmc12181115-fig6']
    assert masked['clinical_panels']==['left']
    assert masked['ancillary_panels'][0]['panels']==['middle','right']
    assert masked['panel_identifier_scheme']=='position_unlettered'
    assert rows['open-gallbladder-pmc12181115-fig4']['ancillary_panels'][1]['kind']=='Radiography'
    assert 'clinical_panels' not in rows['open-gallbladder-pmc12181115-fig1']
    assert 'not wall hypervascularity' in rows['open-gallbladder-pmc5359147-fig5']['caption']


@pytest.mark.parametrize('change',['scheme','primary_modality','ancillary_modality','background'])
def test_unlettered_roles_and_reviewed_background_are_validated(monkeypatch,change):
    original=radiology_catalog._read
    def altered(name,default=None):
        data=copy.deepcopy(original(name,default))
        if name=='radiology-open-images.json':
            row=next(r for r in data['ra.ultrasound-gallbladder'] if r['id']=='open-gallbladder-pmc12181115-fig6')
            if change=='scheme':row.pop('panel_identifier_scheme')
            if change=='primary_modality':row['source_context']['panel_types']['left']='CT'
            if change=='ancillary_modality':row['ancillary_panels'][0]['kind']='MRI'
            if change=='background':row['source_background']='red'
        return data
    monkeypatch.setattr(radiology_catalog,'_read',altered);radiology_catalog._structure_atlases.cache_clear()
    try:
        with pytest.raises(ValueError):radiology_catalog._structure_atlases()
    finally:radiology_catalog._structure_atlases.cache_clear()


def test_no_new_gallbladder_image_claims_structure_or_clinical_approval():
    data=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())
    rows=[r for r in data['assets'] if r['id'].startswith('open-gallbladder-')]
    assert len(rows)==9
    assert all(r['structure_ids']==[] and r['requirement_coverage']=={} and r['anatomical_review']['status']=='pending' for r in rows)
