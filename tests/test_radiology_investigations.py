"""Source-derived investigation boundaries and detailed visual contracts."""
from collections import Counter
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from primer.curriculum import Curriculum
from primer import radiology_catalog


@pytest.fixture(scope='module')
def curriculum():
    return Curriculum()


def test_all_reference_headings_are_backed_by_radiology_assistant():
    cat = radiology_catalog.catalogue()
    sources = json.loads((ROOT/'data/radiology/source-catalog.json').read_text())['articles']
    refs = cat['investigations']
    assert len(refs) == 136
    counts = Counter(a for item in refs for a in item['article_ids'])
    assert set(counts) == {a['id'] for a in sources}
    assert all(count == 1 for count in counts.values())
    assert {i['section'] for i in refs} == {'Abdomen', 'Breast', 'Cardiovascular', 'Chest', 'Head/Neck', 'Musculoskeletal', 'Neuroradiology', 'Pediatrics', 'More'}


def test_unsupported_reference_topics_are_removed(curriculum):
    items = radiology_catalog.index(curriculum)['modules']
    offered = {i['module_id'] for i in items}
    unsupported = [n['id'] for n in curriculum.nodes.values()
                   if n['domain'] == 'radiology' and n['id'].startswith('rad.')
                   and not n['reference_count']]
    assert len(unsupported) == 13
    assert not offered.intersection(unsupported)
    assert all(radiology_catalog.resolve(identifier) is None for identifier in unsupported)


def test_msk_filter_contains_only_source_msk_investigations(curriculum):
    items = radiology_catalog.index(curriculum)['modules']
    msk = [item for item in items if item['section']=='Musculoskeletal']
    assert len(msk) == 22
    assert {'ra.mri-shoulder','ra.ultrasound-shoulder','ra.mri-ankle','ra.mri-diabetic-foot'} <= {i['id'] for i in msk}
    assert not any(i['module_id'] in ('rad.5.prostate-mri','rad.5.coronary-ct') for i in msk)


def test_every_investigation_has_its_own_source_gallery(curriculum):
    for item in radiology_catalog.catalogue()['investigations']:
        ref = radiology_catalog.detail(curriculum, item)['radiology_reference']
        assert ref['key_images'], item['id']
        allowed = {a['url'].rstrip('/') for a in ref['reading']}
        assert all(i['source_url'].rstrip('/') in allowed for i in ref['key_images']), item['id']
        assert len({i['src'] for i in ref['key_images']}) == len(ref['key_images'])


def test_split_investigations_do_not_inherit_the_wrong_modality_or_classification(curriculum):
    entries = radiology_catalog.catalogue()['investigations']
    defecography = next(i for i in entries if 'defecography' in i['title'].lower())
    ref = radiology_catalog.detail(curriculum, defecography)['radiology_reference']
    technique = next(s['body'] for s in ref['report_templates'][0]['sections'] if s['heading']=='TECHNIQUE AND QUALITY').lower()
    assert 'fluoroscop' in technique or 'barium' in technique
    assert 'mri' not in technique
    solid = next(i for i in entries if 'solid renal' in i['title'].lower())
    ref = radiology_catalog.detail(curriculum, solid)['radiology_reference']
    assert ref['reporting']['classification'] is None
    assert not ref['reporting'].get('criteria_table')


def test_shoulder_modalities_have_distinct_reporting_content(curriculum):
    mr = radiology_catalog.detail(curriculum, radiology_catalog.resolve('ra.mri-shoulder'))
    us = radiology_catalog.detail(curriculum, radiology_catalog.resolve('ra.ultrasound-shoulder'))
    assert mr['title'] == 'MRI shoulder'
    assert mr['modality'] == 'MRI' and us['modality']=='Ultrasound'
    assert mr['radiology_reference']['report_templates'] != us['radiology_reference']['report_templates']
    us_report = str(us['radiology_reference']['reporting']).lower()
    assert 'anisotrop' in us_report and 'dynamic' in us_report
    assert mr['radiology_reference']['key_images'] and us['radiology_reference']['key_images']
    for reference in (mr,us):
        allowed={a['url'].rstrip('/') for a in reference['radiology_reference']['reading']}
        assert all(i['source_url'].rstrip('/') in allowed for i in reference['radiology_reference']['key_images'])


def test_native_anatomy_manifest_has_traceable_geometry():
    import hashlib,struct
    directory=ROOT/'web/anatomy/bodyparts3d'
    m=json.loads((directory/'manifest.json').read_text())
    assert m['dataset']=='BodyParts3D 4.0' and m['license']=='CC BY 4.0'
    assert {'shoulder','elbow','hip','knee','ankle','wrist'} <= set(m['regions'])
    assert len(m['parts'])>=57
    for part in m['parts'].values():
        data=(ROOT/'web'/part['file'].removeprefix('/app/')).read_bytes()
        assert hashlib.sha256(data).hexdigest()==part['sha256']
        magic,vertices,indices=struct.unpack('<III',data[:12])
        assert magic==0x44335042 and len(data)==12+vertices*24+indices*4
    shoulder=m['regions']['shoulder']
    names=' '.join(m['parts'][p['id']]['name'].lower() for p in shoulder['parts'])
    for structure in ('scapula','humerus','clavicle','supraspinatus','infraspinatus','subscapularis','teres minor'):
        assert structure in names


def test_generated_illustration_is_separate_from_clinical_images(curriculum):
    ref=radiology_catalog.detail(curriculum,radiology_catalog.resolve('ra.mri-shoulder'))['radiology_reference']
    for image in ref['anatomical_illustrations']:
        assert image['kind']=='generated-illustration'
        assert 'AI-generated' in image['attribution']
        assert not any(image['src']==clinical['src'] for clinical in ref['key_images'])
