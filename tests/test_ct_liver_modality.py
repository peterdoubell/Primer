"""CT variants use CT observations, with prior report versions retained exactly."""
import gzip
import json
from pathlib import Path

from fastapi.testclient import TestClient
from primer.server import app
from tools.authoring.examination_additions_20261112 import filter_text, source_rows

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'data/radiology'
CT = {'ct.liver-mass':'ra.liver-masses', 'ct.liver-lirads':'ra.liver-lirads'}
PRIOR = '0c3932955802d8634f5dddad784f2b886fd3705983cdfd7bcabde4044998f38e'


def observation(investigation):
    return next(s for s in investigation['sections'] if s['anatomy_id'] == 'hepatic-observation')


def test_current_catalog_changes_only_the_two_ct_signal_intensity_choices():
    old = json.loads(gzip.decompress((BASE/'descriptor-history'/(PRIOR+'.json.gz')).read_bytes()))
    packed = gzip.decompress((BASE/'descriptor-reporting.json.gz').read_bytes())
    assert packed == (BASE/'descriptor-reporting.json').read_bytes()
    current = json.loads(packed)
    assert old['schema_hash'] == PRIOR and current['schema_hash'] != PRIOR
    assert old['summary']['investigations'] == current['summary']['investigations'] == 335
    assert old['summary']['descriptors'] - current['summary']['descriptors'] == 2
    for key, form in old['forms'].items():
        before = form['investigations']
        after = current['forms'][key]['investigations']
        assert len(before) == len(after)
        for previous, actual in zip(before,after):
            if previous['id'] in CT:
                fields = observation(previous)['findings']
                field, = [f for f in fields if f['id'] == previous['id']+':hepatic-observation:hb']
                assert 'hepatobiliary phase' in field['text'] and 'hypointense' in field['text']
                fields.remove(field)
            assert previous == actual


def test_source_variant_builder_preserves_mr_and_excludes_mr_signal_in_ct():
    forms = json.loads((BASE/'descriptor-reporting.json').read_bytes())['forms']
    exams = {i['id']:i for f in forms.values() for i in f['investigations']}
    with TestClient(app) as client:
        for variant, parent in CT.items():
            mr = observation(exams[parent])
            assert any(f['id'].endswith(':hb') for f in mr['findings'])
            for modality, expect in [('MRI',True),('CT',False)]:
                row, = source_rows([mr],modality)
                assert ('hb' in {f['id'] for f in row['findings']}) is expect
            detail = client.get('/api/radiology/modules/'+variant).json()['radiology_reference']['structured_form']
            actual, = [i for i in detail['descriptor_form']['investigations'] if i['id'] == variant]
            fields = observation(actual)['findings']
            assert {f['id'].rsplit(':',1)[1] for f in fields} >= {'ap','pv','delayed','growth'}
            assert all('hepatobiliary phase' not in f['text'].lower() for f in fields)


def test_quick_ct_liver_template_keeps_enhancement_choices_and_mr_keeps_hepatobiliary_signal():
    files = sorted((BASE/'report-templates').glob('*.json'))
    templates = {key:t for file in files for key,t in json.loads(file.read_bytes())['templates'].items()}
    def lesion_options(exam):
        return next(s['options'] for s in templates[exam]['sections'] if s['heading']=='Focal lesions')
    original = next(option for option in lesion_options('ra.liver-masses') if 'hepatobiliary hypointensity' in option)
    assert filter_text(original, 'MRI') == original
    corrected = filter_text(original, 'CT')
    assert corrected == original.replace(' / hepatobiliary hypointensity', '')
    assert corrected in lesion_options('ct.liver-mass')
    with TestClient(app) as client:
        report = client.get('/api/radiology/modules/ct.liver-mass').json()['radiology_reference']['quick_report']
        assert 'hepatobiliary hypointensity' not in json.dumps(report).lower()
        assert 'peripheral nodular enhancement' in json.dumps(report).lower()
