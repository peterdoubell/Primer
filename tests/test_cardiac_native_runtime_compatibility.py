"""The cardiac source addition cannot broaden frozen byte or figure-only approvals."""
import copy
import hashlib
from pathlib import Path

import pytest
from primer.curriculum import Curriculum
from tools import cardiac_native_runtime_compatibility as bridge

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('path', ['primer/server.py', 'primer/module_media.py', 'primer/source_native_inspectors.py', 'web/app.js', 'vercel.json'])
def test_exact_shared_file_inverse_rejects_every_other_change(path):
    raw = (ROOT / path).read_bytes()
    restored = bridge.before_cardiac_bytes(path, raw)
    assert hashlib.sha256(restored).hexdigest() == bridge.reviewed()['files'][path]['before_sha256']
    with pytest.raises(ValueError, match='Unreviewed'):
        bridge.before_cardiac_bytes(path, raw + b'changed')


def test_figure_only_view_removes_only_the_registered_companion_and_retains_unrelated_drift():
    curriculum = Curriculum()
    for module in bridge.LESSON_BINDINGS:
        fields = {'lesson_media': copy.deepcopy(curriculum.node(module)['lesson_media']), 'unrelated_extra': 'retain'}
        original = copy.deepcopy(fields)
        restored = bridge.before_cardiac_lesson_fields(module, fields)
        assert fields == original and restored['unrelated_extra'] == 'retain'
        removed = [item for item in fields['lesson_media'] if item not in restored['lesson_media']]
        assert len(removed) == 1 and removed[0]['id'] == 'module-native-inspectors-' + module
        changed = copy.deepcopy(fields)
        next(item for item in changed['lesson_media'] if item['id'] == removed[0]['id'])['clinical_approval'] = True
        with pytest.raises(ValueError, match='Unreviewed'):
            bridge.before_cardiac_lesson_fields(module, changed)


def test_UI_scope_rejects_clinical_or_renderer_approval_expansion():
    import json
    ledger = json.loads((ROOT / 'data/radiology/ui-presentation-refreshes.json').read_text())
    step = next(row for row in ledger['refreshes'] if row['id'] == '2026-10-14-cardiac-native-source')
    assert len(bridge.validate_refresh(step)['rows']) == 16
    for field, value in [('clinical_approval', True), ('native_decoder_mesh_CT_renderer_code_touched', True),
                         ('native_presentation_change_scope', 'all_rendering')]:
        changed = copy.deepcopy(step)
        changed[field] = value
        with pytest.raises(ValueError, match='scope'):
            bridge.validate_refresh(changed)
