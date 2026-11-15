"""New report controls cannot waive historical source fingerprints or alter lessons."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from tools import structured_reporting_runtime_compatibility as bridge
from tools.anatomy_sources import ui_refresh

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('path', sorted(bridge.PATHS))
def test_only_the_exact_shared_file_additions_have_an_inverse(path):
    row = bridge.reviewed()['files'][path]
    raw = (ROOT / path).read_bytes()
    restored = bridge.before_structured_bytes(path, raw)
    assert hashlib.sha256(restored).hexdigest() == row['before_sha256']
    assert bridge.before_structured_bytes(path, restored) == restored
    for changed in [raw + b'\n', raw.replace(b'\n', b'\n# unrelated change\n', 1)]:
        with pytest.raises(ValueError, match='Unreviewed'):
            bridge.before_structured_bytes(path, changed)
        assert bridge.before_structured_bytes(path, changed, allow_older=True) == changed
    assert bridge.before_structured_bytes('unknown', b'unchanged') == b'unchanged'


def test_historical_shell_excludes_only_the_two_new_asset_includes():
    from tools.fidelity_continuation_runtime_compatibility import before_continuation_bytes
    raw = before_continuation_bytes('web/index.html', (ROOT / 'web/index.html').read_bytes())
    previous = bridge.before_structured_bytes('web/index.html', raw)
    assert b'/app/radiology-structured.js' in raw and b'/app/radiology-structured.css' in raw
    assert b'/app/radiology-structured.js' not in previous and b'/app/radiology-structured.css' not in previous
    assert previous == raw.replace(b'  <link rel="stylesheet" href="/app/radiology-structured.css">\n', b'').replace(
        b'  <script src="/app/radiology-structured.js"></script>\n', b'')


def test_refresh_keeps_canonical_source_and_all_native_guards_exact():
    step = next(item for item in ui_refresh.load()['refreshes'] if item['id'] == '2026-10-22-structured-reporting')
    proof = bridge.validate_refresh(step)
    assert proof['canonical_lesson_data_changed'] is False
    assert set(proof['canonical_contract_files_sha256']) == {
        'primer/radiology.py', 'primer/radiology_catalog.py', 'docs/radiology-fidelity-scope.json'}
    for path, expected in proof['canonical_contract_files_sha256'].items():
        from tools.holiatlas_runtime_compatibility import before_holiatlas_bytes
        assert hashlib.sha256(before_holiatlas_bytes(path, (ROOT / path).read_bytes(), allow_older=True)).hexdigest() == expected
    for key in ['clinical_approval', 'fine_anatomical_approval', 'native_decoder_mesh_CT_renderer_code_touched']:
        changed = copy.deepcopy(step)
        changed[key] = True
        with pytest.raises(ValueError, match='scope'):
            bridge.validate_refresh(changed)
    changed = copy.deepcopy(step)
    changed['files']['web/app.js']['after'] = '0' * 64
    with pytest.raises(ValueError, match='scope'):
        bridge.validate_refresh(changed)
    changed = copy.deepcopy(step)
    changed['guarded_paths_sha256']['web/radiology-detailed-anatomy.js'] = '0' * 64
    with pytest.raises(ValueError, match='scope'):
        bridge.validate_refresh(changed)


def test_existing_spine_cardiology_refresh_still_accepts_only_its_own_delta():
    from tools.spine_cardiology_runtime_compatibility import validate_refresh
    step = next(item for item in ui_refresh.load()['refreshes'] if item['id'] == '2026-10-22-spine-cardiology-references')
    assert validate_refresh(step)['extends_historical_approval'] is False
