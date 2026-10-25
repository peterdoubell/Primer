"""Unreviewed intake files cannot be published as atlas review evidence."""
import hashlib
import json
from pathlib import Path

import pytest

from tools.anatomy_sources.build_holiatlas_hierarchy import (
    COMPOSITIONS_SHA, SEMANTICS_SHA, read_pinned_json,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('path,pin', [
    ('source-scale-display-crosswalk.json', SEMANTICS_SHA),
    ('compositions/composition-manifest.json', COMPOSITIONS_SHA),
])
def test_only_the_reviewed_source_documents_are_accepted(tmp_path, path, pin):
    original = ROOT/'docs/holiatlas-hierarchy-review-20261025'/path
    raw, parsed = read_pinned_json(original, pin)
    assert raw == original.read_bytes() and isinstance(parsed, dict)
    changed = dict(parsed, unexpected_intake_field='must not be copied into the review')
    intake = tmp_path/'caller-selected.json'
    intake.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match='Unreviewed'):
        read_pinned_json(intake, pin)


def test_export_uses_checked_bytes_even_if_intake_is_replaced_after_read(tmp_path):
    intake = tmp_path/'intake.json'
    approved = b'{"reviewed": true}\n'
    intake.write_bytes(approved)
    raw, _ = read_pinned_json(intake, hashlib.sha256(approved).hexdigest())
    intake.write_bytes(b'{"unreviewed_private_content": "do not export"}')
    destination = tmp_path/'fixed-review-output.json'
    destination.write_bytes(raw)
    assert destination.read_bytes() == approved
