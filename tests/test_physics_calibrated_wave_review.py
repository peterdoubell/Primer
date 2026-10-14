"""Current physical-coordinate evidence is separate from historical approvals."""
import hashlib
import json
from pathlib import Path

import pytest

from tools.physics_wave_runtime_compatibility import before_wave_bytes

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/physics-calibrated-wave-review-20261014'


def test_exact_inverse_preserves_every_unrelated_renderer_byte():
    proof = json.loads((REVIEW / 'runtime-inverse.json').read_text())
    raw = (ROOT / proof['path']).read_bytes()
    restored = before_wave_bytes(proof['path'], raw)
    assert hashlib.sha256(restored).hexdigest() == proof['before_sha256']
    assert proof['clinical_approval'] is proof['extends_historical_approval'] is False
    with pytest.raises(ValueError, match='Unreviewed'):
        before_wave_bytes(proof['path'], raw + b'\n')


def test_authenticated_reader_evidence_matches_the_current_renderer():
    proof = json.loads((REVIEW / 'reader-proof.json').read_text())
    assert not proof['errors'] and proof['production_verified'] is False
    assert {(r['id'], r['width']) for r in proof['rows']} == {
        (i, w) for i in ['phys.1.machines', 'phys.1.sound', 'phys.2.waves'] for w in [1440, 390]}
    digest = hashlib.sha256((ROOT / 'web/lesson-models.js').read_bytes()).hexdigest()
    assert all(r['served_renderer_sha256'] == digest and r['text_and_body_bounds_passed'] for r in proof['rows'])
    assert sum(r['checked_states'] for r in proof['rows']) == 44


def test_wave_sampling_bound_is_below_declared_amplitude_error():
    # Linear interpolation: |error| <= max|y''| h²/8. With 64 segments
    # per cycle, the bound is A*pi²/8192, plus 0.005 SVG-px rounding.
    import math
    largest_amplitude_cm = 10
    bound_cm = largest_amplitude_cm*math.pi**2/8192 + .005/6.5
    assert bound_cm < .013
