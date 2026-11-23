"""Source-backed pulse-counter model and ordinary lesson activity entry."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_counter_event_and_renewal_physics():
    result = subprocess.run(['node', '--test', str(ROOT / 'tests/radiation-counter.test.mjs')],
                            cwd=ROOT, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


def test_counter_is_registered_for_the_existing_nuclear_lesson():
    entry = {'href': '/app/physics/radiation-counter/index.html',
             'label': 'Trace lost pulses through a radiation counter'}
    assert entry in json.loads((ROOT / 'web/activities/registry.json').read_text())['phys.3.nuclear']
    html = (ROOT / 'web/physics/radiation-counter/index.html').read_text()
    assert '/app/#/node/phys.3.nuclear' in html
    assert '10.1088/0026-1394/52/3/S3' in html
    assert 'simulated' in html and 'non-extendable' in html
