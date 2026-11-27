"""Lossless source packing, real file-presence paths, and exact older byte views."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from primer import reporting_bridge
from tools.pack_structured_reporting import encode
from tools.structured_forms_runtime_compatibility import PROOF, PIN, before_structured_forms_pack_bytes

ROOT = Path(__file__).resolve().parents[1]


def test_packed_forms_are_deterministic_and_byte_identical_to_the_author_source():
    source = ROOT/'data/radiology/structured-reporting.json'
    raw = source.read_bytes()
    packed = source.with_suffix('.json.gz').read_bytes()
    assert gzip.decompress(packed) == raw
    assert packed == encode(raw) == encode(raw)
    config = json.loads((ROOT/'vercel.json').read_text())
    assert 'data/radiology/structured-reporting.json,' in config['builds'][0]['config']['excludeFiles']
    assert 'data/radiology/structured-reporting.json.gz' not in config['builds'][0]['config']['excludeFiles']


@pytest.mark.parametrize('author,packed', [(True, False), (False, True), (True, True), (False, False)])
def test_actual_author_packed_and_absent_file_paths(tmp_path, monkeypatch, author, packed):
    module = tmp_path/'primer/reporting_bridge.py'
    directory = tmp_path/'data/radiology'
    directory.mkdir(parents=True)
    authored = {'forms': {'authored': {'title': 'Current source'}}}
    runtime = {'forms': {'packed': {'title': 'Packed source'}}}
    if author:
        (directory/'structured-reporting.json').write_text(json.dumps(authored))
    if packed:
        (directory/'structured-reporting.json.gz').write_bytes(encode(json.dumps(runtime).encode()))
    monkeypatch.setattr(reporting_bridge, '__file__', str(module))
    reporting_bridge.structured_forms.cache_clear()
    try:
        assert reporting_bridge.structured_forms() == (authored if author else runtime if packed else {'forms': {}})
    finally:
        reporting_bridge.structured_forms.cache_clear()


def test_invalid_packed_data_is_not_silently_replaced_with_empty_forms(tmp_path, monkeypatch):
    module = tmp_path/'primer/reporting_bridge.py'
    directory = tmp_path/'data/radiology'
    directory.mkdir(parents=True)
    (directory/'structured-reporting.json.gz').write_bytes(b'invalid gzip')
    monkeypatch.setattr(reporting_bridge, '__file__', str(module))
    reporting_bridge.structured_forms.cache_clear()
    try:
        with pytest.raises(OSError):
            reporting_bridge.structured_forms()
    finally:
        reporting_bridge.structured_forms.cache_clear()


def test_shared_runtime_and_build_bytes_keep_the_exact_prior_inverse():
    raw = PROOF.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PIN
    for path, record in json.loads(raw).items():
        current = (ROOT/path).read_bytes()
        assert hashlib.sha256(current).hexdigest() == record['after']
        previous = before_structured_forms_pack_bytes(path, current)
        assert hashlib.sha256(previous).hexdigest() == record['before']
        assert before_structured_forms_pack_bytes(path, previous) == previous
        assert before_structured_forms_pack_bytes(path, current+b'foreign') == current+b'foreign'
    from tools import salivary_surface_compatibility as surfaces
    current = (ROOT/'vercel.json').read_bytes()
    historical = surfaces.before_surface_bytes('vercel.json', current)
    record = json.loads(surfaces.PROOF.read_bytes())['vercel.json']
    assert hashlib.sha256(historical).hexdigest() == record['before']
