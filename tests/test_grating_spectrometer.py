"""Independent optical model checks, published reference facts and reader entry."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_finite_grating_and_detector_physics():
    result = subprocess.run(['node', '--test', str(ROOT / 'tests/grating-spectrometer.test.mjs')],
                            cwd=ROOT, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


def test_original_nist_tables_support_the_exact_air_wavelength_transcription():
    directory = ROOT / 'docs/grating-spectrometer'
    receipt = json.loads((directory / 'source-receipt.json').read_text())
    for record in receipt['files']:
        raw = (directory / record['file']).read_bytes()
        assert len(raw) == record['bytes']
        assert hashlib.sha256(raw).hexdigest() == record['sha256']
        decoded = gzip.decompress(raw)
        assert len(decoded) == record['decodedBytes']
        assert hashlib.sha256(decoded).hexdigest() == record['decodedSHA256']
    source = json.loads((ROOT / 'web/physics/grating-spectrometer/source.json').read_text())
    strong = gzip.decompress((directory / 'nist-sodium-table2.html.gz').read_bytes()).decode()
    assert 'Air' in strong and 'R56' in strong
    persistent = re.sub('<[^>]+>', ' ', gzip.decompress((directory / 'nist-sodium-table3.html.gz').read_bytes()).decode())
    refs = re.sub('<[^>]+>', ' ', gzip.decompress((directory / 'nist-sodium-table7.html.gz').read_bytes()).decode())
    for item in source['lines']:
        assert item['wavelengthAngstrom'] in persistent and item['wavelengthAngstrom'] in strong
        assert float(item['wavelengthAngstrom']) / 10 == item['wavelengthNm']
    assert 'Risberg' in refs and '1956' in refs
    assert 'higher-accuracy' in refs


def test_ordinary_reader_entries_preserve_existing_optics_and_experiment_activities():
    registry = json.loads((ROOT / 'web/activities/registry.json').read_text())
    href = '/app/physics/grating-spectrometer/index.html'
    for module in ('phys.3.optics-waves', 'phys.4.experiment'):
        assert sum(row['href'] == href for row in registry[module]) == 1
    assert any(row['href'] == '/app/physics/vernier-caliper/index.html'
               for row in registry['phys.4.experiment'])
    html = (ROOT / 'web/physics/grating-spectrometer/index.html').read_text()
    assert '/app/#/node/phys.3.optics-waves' in html
    assert 'NIST' in html and 'not a captured lamp spectrum' in html
    assert 'in air' in html and 'equal normalized weights' in html
