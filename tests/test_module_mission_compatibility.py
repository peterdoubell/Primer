import hashlib
from pathlib import Path
from tools.module_mission_compatibility import previous_shell_bytes, BEFORE, AFTER
ROOT=Path(__file__).resolve().parents[1]

def test_only_exact_shell_additions_are_projected():
    raw=(ROOT/'web/index.html').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==AFTER
    restored=previous_shell_bytes('web/index.html',raw)
    assert hashlib.sha256(restored).hexdigest()==BEFORE
    assert b'module-mission' not in restored
    assert previous_shell_bytes('web/index.html',restored)==restored
    for mutated in [raw+b'foreign',raw.replace(b'module-mission.js',b'unknown.js')]:
        assert previous_shell_bytes('web/index.html',mutated)==mutated
    assert previous_shell_bytes('unrelated',raw)==raw
