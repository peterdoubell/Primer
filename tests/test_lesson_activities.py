"""Stand-alone lesson activities: tested models, a registry, and one pinned reader hook."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_activity_models_and_pages_pass_their_node_checks():
    result = subprocess.run(['node', '--test', str(ROOT / 'tests/activity-models.test.cjs')],
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-2000:]


def test_registry_lists_only_existing_activities_for_real_modules():
    registry = json.loads((ROOT / 'web/activities/registry.json').read_text())
    nodes = set()
    for path in (ROOT / 'data/curriculum').glob('*.json'):
        def walk(value):
            if isinstance(value, dict):
                if 'id' in value and 'stage' in value:
                    nodes.add(value['id'])
                for item in value.values():
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)
        walk(json.loads(path.read_text()))
    for node, links in registry.items():
        assert node in nodes, node
        for link in links:
            assert set(link) == {'href', 'label'}
            assert (ROOT / 'web' / link['href'].removeprefix('/app/')).is_file(), link['href']


def test_reader_hook_is_registry_driven_with_an_exact_inverse():
    from tools.lesson_activities_compatibility import (
        AFTER, BEFORE, BLOCK, DICTATION_LAYOUT, PATH, before_activity_registry_bytes,
    )
    from tools.recist_pelvic_runtime_compatibility import PROOF, before_recist_pelvic_delivery_bytes
    from tools.report_layout_compatibility import before_rich_report_format_bytes
    from tools.source_studies_compatibility import before_combined_source_release_bytes
    raw = (ROOT / PATH).read_bytes()
    assert raw.count(BLOCK) == 1 and b"fetch('/app/activities/registry.json')" in BLOCK
    # Only same-site activity links are rendered.
    assert b"String(activity.href).startsWith('/app/')" in BLOCK
    dictation_revision, current, previous = DICTATION_LAYOUT
    pelvic_reader = before_rich_report_format_bytes(PATH, raw)
    assert hashlib.sha256(pelvic_reader).hexdigest() == json.loads(PROOF.read_bytes())[PATH]['after']
    dictation_reader = before_recist_pelvic_delivery_bytes(PATH, raw)
    assert hashlib.sha256(dictation_reader).hexdigest() == dictation_revision
    assert dictation_reader.count(current) == 1
    assert hashlib.sha256(dictation_reader.replace(current, previous, 1)).hexdigest() == AFTER
    assert hashlib.sha256(before_activity_registry_bytes(PATH, raw)).hexdigest() == BEFORE
    assert before_activity_registry_bytes(PATH, raw + b'\n') == raw + b'\n'
    assert hashlib.sha256(before_combined_source_release_bytes(PATH, raw)).hexdigest() not in (AFTER, BEFORE)
