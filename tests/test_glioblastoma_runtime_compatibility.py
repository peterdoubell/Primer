"""Later reader links must unwind in order without admitting unreviewed bytes."""
import hashlib
import importlib
import json
from pathlib import Path

import pytest

from tools.glioblastoma_runtime_compatibility import PROOF, before_glioblastoma_bytes
from tools.knowledge_maps_compatibility import before_knowledge_maps_bytes

ROOT = Path(__file__).resolve().parents[1]
STATISTICS = (
    b"  if (n.id === 'math.3.statistics') page.append(el('a', { class: 'btn ghost', href: '/app/math/sampling-mean/index.html' },\n"
    b"    'Compare population spread and sampling uncertainty'));\n"
)


@pytest.mark.parametrize('include_statistics', [True, False])
def test_current_and_previous_reader_restore_the_exact_historical_bytes(include_statistics):
    raw = (ROOT / 'web/app.js').read_bytes()
    if not include_statistics:
        raw = before_knowledge_maps_bytes('web/app.js', raw)
        raw = raw.replace(STATISTICS, b'', 1)
    restored = before_glioblastoma_bytes('web/app.js', raw)
    expected = json.loads(PROOF.read_bytes())['web/app.js']['before_sha256']
    assert hashlib.sha256(restored).hexdigest() == expected
    assert before_glioblastoma_bytes('web/app.js', restored) == restored


@pytest.mark.parametrize('mutation', ['append', 'duplicate', 'edit'])
def test_reader_projection_rejects_unreviewed_bytes(mutation):
    raw = (ROOT / 'web/app.js').read_bytes()
    changed = {
        'append': raw + b'foreign edit',
        'duplicate': raw + STATISTICS,
        'edit': raw.replace(b'Compare population spread', b'Alter population spread', 1),
    }[mutation]
    with pytest.raises(ValueError, match='Unreviewed glioblastoma integration change'):
        before_glioblastoma_bytes('web/app.js', changed)
    assert before_glioblastoma_bytes('web/app.js', changed, allow_older=True) == changed
    assert before_glioblastoma_bytes('unrelated.js', changed) == changed


@pytest.mark.parametrize('module,function', [
    ('cavernous_photo', 'before_cavernous_bytes'),
    ('cortical_contact', 'before_contact_bytes'),
    ('particle', 'before_particle_bytes'),
    ('pituitary_case', 'before_pituitary_bytes'),
    ('sellar_interface', 'before_interfaces_bytes'),
    ('spl_additional', 'before_additional_bytes'),
    ('spl_epilepsy', 'before_context_bytes'),
])
def test_reader_reaches_downstream_historical_baselines(module, function):
    helper = importlib.import_module(f'tools.{module}_runtime_compatibility')
    raw = (ROOT / 'web/app.js').read_bytes()
    restored = getattr(helper, function)('web/app.js', raw)
    expected = helper.reviewed()['files']['web/app.js']['before_sha256']
    assert hashlib.sha256(restored).hexdigest() == expected
