"""Standalone cardiology references and their reporting-workbench contracts."""
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest
from primer import cardiology, radiology_catalog

ROOT = Path(__file__).resolve().parents[1]


def test_both_modules_resolve_and_render_without_borrowing_a_ct_or_mri_lesson():
    for item in cardiology.investigations():
        assert radiology_catalog.resolve(item['id']) == item
        result = radiology_catalog.detail(None, item)
        assert result['id'] == result['module_id'] == item['id']
        assert result['section'] == 'Cardiovascular'
        ref = result['radiology_reference']
        assert ref['source_label'] == 'Cardiology society references'
        assert ref['reading'] == ref['reporting']['sources']
        assert not ref['key_images'] and not result['lesson_media']
        template = ref['report_templates'][0]
        walk = ref['walkthrough']
        assert walk['complete'] and len(walk['steps']) == 6
        headings = [s['heading'] for s in template['sections']]
        owned = walk['start']['sections'] + [s for step in walk['steps'] for s in step['sections']] + walk['finish']['sections']
        assert owned == headings and len(set(owned)) == len(owned)
        assert walk['template_id'] == template['id']
        assert all(step['findings'] and step['look'] and step['tip'] for step in walk['steps'])
        for diagram in ref['reporting_diagrams']:
            svg = ET.parse(ROOT / 'web' / diagram['src'].removeprefix('/app/')).getroot()
            assert svg.find('{http://www.w3.org/2000/svg}title') is not None
            assert svg.find('{http://www.w3.org/2000/svg}desc') is not None


def test_coronary_catheter_and_echo_protocols_keep_their_clinical_scope():
    angio, echo = [cardiology.detail(item)['radiology_reference'] for item in cardiology.investigations()]
    angiography_text = str(angio['report_templates'])
    assert 'Contrast agent and volume (mL)' in angiography_text
    assert 'PCI: [not performed' in angiography_text
    assert 'FFR / iFR' in angiography_text and 'TIMI' in angiography_text
    assert 'CAD-RADS' in str(angio['reporting']['pitfalls'])
    echo_text = str(echo['report_templates'])
    assert 'LVEF' in echo_text and 'Diastolic assessment' in echo_text
    assert 'TEE' in str(echo['reporting']['protocol'])
    assert 'PCI:' not in echo_text and 'LVEF' not in angiography_text


def test_both_modules_are_in_the_searchable_radiology_index(monkeypatch):
    # Isolate the existing foundation entries; no unrelated atlas byte reads.
    monkeypatch.setattr(radiology_catalog, 'catalogue', lambda: {'investigations': [], 'foundation_url': 'https://radiologyassistant.nl/'})
    modules = radiology_catalog.index(None)['modules']
    assert {item['id'] for item in modules} == {item['id'] for item in cardiology.investigations()}
    assert all(item['step_count'] == 6 and item['template_count'] == 1 for item in modules)
    assert 'PCI' in modules[0]['topics'] and 'TTE' in modules[1]['topics']


def test_invalid_step_coverage_is_rejected(monkeypatch):
    import json
    original = json.loads
    def changed(*args, **kwargs):
        data = original(*args, **kwargs)
        data['investigations'][0]['steps'].pop()
        return data
    monkeypatch.setattr(cardiology.json, 'loads', changed)
    cardiology.investigations.cache_clear()
    try:
        with pytest.raises(ValueError, match='cover every finding'):
            cardiology.investigations()
    finally:
        cardiology.investigations.cache_clear()


def test_reporting_steps_use_existing_anatomy_landmarks():
    import subprocess
    import json
    script = "global.window={addEventListener(){}};global.document={addEventListener(){}};require('./web/spatial-models.js');require('./web/radiology-reference-models.js');console.log(JSON.stringify(Object.fromEntries(['coronary','heart'].map(f=>[f,Object.keys(window.PrimerRadiologyReferenceModels.landmarks(f))]))));"
    families = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT, text=True))
    for item in cardiology.investigations():
        assert item['focus'] in families[item['family']]
        assert all(step['landmark'] in families[item['family']] for step in item['steps'])
