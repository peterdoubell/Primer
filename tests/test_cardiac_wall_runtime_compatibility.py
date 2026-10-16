"""Frozen evidence accepts only the exact supplementary-source delta."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from primer.curriculum import Curriculum
from tools import cardiac_wall_runtime_compatibility as bridge

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('path', ['primer/server.py', 'primer/module_media.py', 'primer/source_native_inspectors.py', 'web/app.js', 'vercel.json', '.vercelignore'])
def test_exact_five_file_inverse_cannot_hide_unrelated_byte_changes(path):
    raw = (ROOT / path).read_bytes()
    restored = bridge.before_wall_bytes(path, raw)
    assert hashlib.sha256(restored).hexdigest() == bridge.reviewed()['files'][path]['before_sha256']
    with pytest.raises(ValueError, match='Unreviewed'):
        bridge.before_wall_bytes(path, raw + b'changed')


def test_semantic_view_restores_only_known_context_fields_and_preserves_other_drift():
    c = Curriculum()
    for module in bridge.LESSONS:
        fields = {'lesson_media': copy.deepcopy(c.node(module)['lesson_media']), 'unrelated_value': 'retain'}
        original = copy.deepcopy(fields)
        restored = bridge.before_wall_lesson_fields(module, fields)
        assert fields == original and restored['unrelated_value'] == 'retain'
        media = next(item for item in restored['lesson_media'] if item['id'] == 'module-native-inspectors-' + module)
        assert media['instructions'] == (bridge.OLD_THORACIC if module == 'rad.5.pleura' else bridge.OLD_INSTRUCTIONS)
        changed = copy.deepcopy(fields)
        next(item for item in changed['lesson_media'] if item['id'] == media['id'])['clinical_approval'] = True
        with pytest.raises(ValueError, match='Unreviewed'):
            bridge.before_wall_lesson_fields(module, changed)


def test_supplementary_wrapper_cannot_grant_clinical_or_old_renderer_approval():
    ledger = json.loads((ROOT / 'data/radiology/ui-presentation-refreshes.json').read_text())
    step = next(row for row in ledger['refreshes'] if row['id'] == '2026-10-16-cardiac-wall-context')
    assert len(bridge.validate_refresh(step)['rows']) == 16
    for field, value in [('clinical_approval', True), ('native_decoder_mesh_CT_renderer_code_touched', True),
                         ('existing_reporting_guides_retained', False)]:
        changed = copy.deepcopy(step)
        changed[field] = value
        with pytest.raises(ValueError, match='scope'):
            bridge.validate_refresh(changed)
