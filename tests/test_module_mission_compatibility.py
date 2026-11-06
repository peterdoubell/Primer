import hashlib
from pathlib import Path
from tools.knowledge_maps_compatibility import before_knowledge_maps_bytes
from tools.module_mission_compatibility import previous_shell_bytes, BEFORE, AFTER
ROOT=Path(__file__).resolve().parents[1]

def test_only_exact_shell_additions_are_projected():
    raw=before_knowledge_maps_bytes('web/index.html', (ROOT/'web/index.html').read_bytes())
    assert hashlib.sha256(raw).hexdigest()==AFTER
    restored=previous_shell_bytes('web/index.html',raw)
    assert hashlib.sha256(restored).hexdigest()==BEFORE
    assert b'module-mission' not in restored
    assert previous_shell_bytes('web/index.html',restored)==restored
    for mutated in [raw+b'foreign',raw.replace(b'module-mission.js',b'unknown.js')]:
        assert previous_shell_bytes('web/index.html',mutated)==mutated
    assert previous_shell_bytes('unrelated',raw)==raw


def test_historical_chain_entry_projects_the_exact_shell():
    from tools.glioblastoma_runtime_compatibility import before_glioblastoma_bytes
    raw=(ROOT/'web/index.html').read_bytes()
    previous=before_knowledge_maps_bytes('web/index.html',raw)
    assert previous_shell_bytes('web/index.html',raw)==previous_shell_bytes('web/index.html',previous)
    assert before_glioblastoma_bytes('web/index.html',raw)==previous_shell_bytes('web/index.html',previous)
    assert before_glioblastoma_bytes('web/index.html',raw+b'foreign')==raw+b'foreign'
