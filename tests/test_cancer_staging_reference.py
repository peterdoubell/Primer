"""Oncology reference coverage and clinically important category distinctions."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def curriculum():
    return Curriculum()


def test_all_dedicated_cancer_staging_modules_have_tables_and_illustrations(curriculum):
    required = {'ra.mri-anal-cancer', 'ra.mri-bladder', 'ra.mri-cervical-cancer',
                'ra.mri-endometrial-cancer', 'ra.ct-pancreatic-cancer', 'ra.mri-prostate',
                'ra.mri-rectal-cancer', 'ra.breast-cancer-staging', 'ra.ct-lung-cancer',
                'ra.solid-renal-masses', 'ra.thymus', 'ra.head-neck-malignancy',
                'ra.bone-tumours', 'ra.mri-brain-tumours', 'ra.paediatric-renal-tumours',
                'ra.paediatric-solid-abdominal-masses', 'ra.liver-lirads', 'ra.recist'}
    data = catalog.cancer_staging_catalog()
    assert required <= set(data['bindings'])
    for identifier in data['bindings']:
        ref = catalog.detail(curriculum, catalog.resolve(identifier))['radiology_reference']
        assert ref['cancer_staging'], identifier
        for system in ref['cancer_staging']:
            assert system['tables'] and system['report_fields'] and system['sources']
            for table in system['tables']:
                assert all(row['category'] and row['criteria'] and row['report_note'] for row in table['rows'])
            path = ROOT / 'web' / system['illustration']['src'].removeprefix('/app/')
            root = ET.parse(path).getroot()
            assert root.tag == '{http://www.w3.org/2000/svg}svg'
            assert not root.findall('.//{http://www.w3.org/2000/svg}script')
            assert root.find('{http://www.w3.org/2000/svg}title') is not None


def test_lung_ninth_edition_uses_station_and_organ_system_subdivisions():
    system = catalog.cancer_staging_catalog()['systems']['lung-tnm9']
    rows = {row['category']: row for t in system['tables'] for row in t['rows']}
    assert 'stations' in rows['N2a / N2b']['criteria']
    assert 'organ systems' in rows['M1c1 / M1c2']['criteria']
    assert 'solid component' in rows['T1a / T1b / T1c']['report_note']


def test_imaging_extent_is_not_conflated_with_probability_grade_or_pathology():
    systems = catalog.cancer_staging_catalog()['systems']
    assert 'DRE' in systems['prostate-local']['scope']
    assert 'LVSI' in systems['endometrium-figo2023']['scope']
    assert 'ER/PR/HER2' in systems['breast-tnm']['scope']
    assert 'no conventional TNM' in systems['cns-classification']['scope']
    assert systems['recist11']['kind'] == 'response'
    wilms = json.dumps(systems['wilms-cog'])
    assert 'not automatically stage IV' in wilms
    rectal = json.dumps(systems['rectal-tnm'])
    assert 'Do not label MRF involvement as T4' in rectal
    assert 'Version 9 (2026)' in json.dumps(systems['head-neck-frameworks'])


def test_staging_systems_are_searchable_and_not_added_to_nononcology_modules(curriculum):
    modules = {m['id']: m for m in catalog.index(curriculum)['modules']}
    assert 'Lung cancer TNM' in modules['ra.ct-lung-cancer']['topics']
    assert modules['ra.ct-lung-cancer']['staging_systems']
    assert not modules['ra.appendicitis']['staging_systems']
    assert 'cancer_staging' not in catalog.detail(curriculum, catalog.resolve('ra.hrct-lung'))['radiology_reference']


def test_requested_annotated_ct_cases_are_available_in_the_relevant_guides(curriculum):
    expected = {
        'ra.ct-lung-cancer': {'bronchopulmonary-segments-annotated-ct-2', 'liver-segments-annotated-ct-1'},
        'ra.head-neck-malignancy': {'lymph-node-levels-of-the-head-and-neck-annotated-ct'},
        'ra.liver-lirads': {'liver-segments-annotated-ct-1'},
    }
    for identifier, cases in expected.items():
        ref = catalog.detail(curriculum, catalog.resolve(identifier))['radiology_reference']
        assert {row['url'].rsplit('/', 1)[-1] for row in ref['annotated_anatomy_links']} == cases
        assert all(row['publisher'] == 'Radiopaedia' and row['reporting_use'] for row in ref['annotated_anatomy_links'])
    assert not catalog.detail(curriculum, catalog.resolve('ra.appendicitis'))['radiology_reference']['annotated_anatomy_links']


def test_embedded_references_preserve_complete_ordered_source_sequences():
    expected = {'bronchopulmonary-segments': (93, 'Peter Jenvey', '54511'),
                'head-neck-node-levels': (100, 'Maciej Debowski', '62672'),
                'liver-segments': (27, 'Jeffrey Hocking', '45972')}
    references = json.loads((ROOT / 'data/radiology/annotated-anatomy-links.json').read_text())['references']
    for identifier, (count, author, case) in expected.items():
        reference = references[identifier]
        stack = reference['stack']
        data = json.loads((ROOT / 'web' / stack['manifest_url'].removeprefix('/app/')).read_text())
        assert len(data['frames']) == count
        assert [frame['index'] for frame in data['frames']] == list(range(count))
        assert len({frame['src'] for frame in data['frames']}) == count
        assert data['source_url'] == reference['url']
        assert data['contributor'] == author and data['source_case_id'] == case
        assert 'Non-commercial' in data['reuse']
        assert all((ROOT / 'web' / frame['src'].removeprefix('/app/')).is_file() for frame in data['frames'])
        assert all(frame['source_image_url'].startswith('https://prod-images-static.radiopaedia.org/images/') for frame in data['frames'])


def test_hosted_stack_delivery_preserves_reader_gate_and_registered_frame_paths(monkeypatch, curriculum):
    from fastapi.testclient import TestClient
    import primer.server as server
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setenv(server.ACCESS_USERNAME_ENV, 'reader')
    monkeypatch.setenv(server.ACCESS_PASSWORD_ENV, 'secret')
    catalog.annotated_anatomy_links.cache_clear()
    catalog.annotated_ct_frames.cache_clear()
    try:
        with TestClient(server.app) as client:
            path = '/app/reference-media/annotated-ct/liver-segments/001.jpeg'
            assert client.get(path).status_code == 401
            response = client.get(path, auth=('reader', 'secret'), follow_redirects=False)
            assert response.status_code == 307
            assert response.headers['location'] == '/source-media/reference-media/annotated-ct/liver-segments/001.jpeg'
            assert client.get('/app/reference-media/annotated-ct/liver-segments/999.jpeg', auth=('reader','secret')).status_code == 404
            assert len(catalog.annotated_ct_frames()) == 220
    finally:
        catalog.annotated_anatomy_links.cache_clear()
        catalog.annotated_ct_frames.cache_clear()
