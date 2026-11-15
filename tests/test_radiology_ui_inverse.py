"""Historical comparisons accept only the exact recorded UI changes."""
import hashlib
from pathlib import Path

from tools.anatomy_sources import radiology_presentation_compatibility as bridge

ROOT = Path(__file__).resolve().parents[1]


def test_exact_ui_and_helper_inverses_preserve_the_original_hashes():
    for path, expected in [('web/app.js', bridge.BEFORE),
                           ('web/styles.css', bridge.STYLE_BEFORE),
                           (bridge.HELPER_PATH, bridge.HELPER_BEFORE)]:
        current = (ROOT / path).read_bytes()
        historical = bridge.restore_presentation_bytes(path, current)
        assert hashlib.sha256(historical).hexdigest() == expected
        changed = current + b'\n// unreviewed change\n'
        assert bridge.restore_presentation_bytes(path, changed) == changed
        assert hashlib.sha256(changed).hexdigest() != expected
