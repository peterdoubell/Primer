import json
import shutil
import subprocess
from pathlib import Path

from primer.curriculum import Curriculum
from primer import radiology_catalog


def test_all_radiology_references_hide_histology_without_losing_mri_or_step_links():
    curriculum = Curriculum()
    modules = [radiology_catalog.detail(curriculum, item)
               for item in radiology_catalog.catalogue()['investigations']]
    result = subprocess.run([shutil.which('node'), 'tools/check_radiology_presentation.cjs'],
                            cwd=Path(__file__).resolve().parents[1], input=json.dumps(modules),
                            text=True, capture_output=True, check=True)
    assert json.loads(result.stdout)['modules'] == len(modules)


def test_bladder_staging_has_five_source_cases_with_uncropped_sequence_panels():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / 'data/radiology/cancer-staging.json').read_text())
    cases = data['systems']['bladder-tnm']['clinical_examples']
    assert [case['score'] for case in cases] == [1, 2, 3, 4, 5]
    for case in cases:
        assert case['source_url'] == 'https://radiologyassistant.nl/abdomen/bladder/bladder-cancer-vi-rads'
        assert case['figures'][0]['label'] == 'T2-weighted MRI'
        for figure in case['figures']:
            assert figure['src'].startswith('https://radiologyassistant.nl/assets/')
            assert figure['width'] > 500 and figure['height'] > 0
