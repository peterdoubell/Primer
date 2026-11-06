import hashlib
from pathlib import Path

import pytest

from tools.knowledge_maps_compatibility import before_knowledge_maps_bytes


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(("path", "previous_hash"), [
    ("web/app.js", "9d93a0f6dd960989e74a874d7617da89e420785e33971fe607acebc3cd926868"),
    ("web/index.html", "528c7b9793bc601214767509642a9307b5645d1c9bb8b2c5447d83850f927d92"),
])
def test_maps_restore_only_the_exact_previous_shared_bytes(path, previous_hash):
    raw = (ROOT / path).read_bytes()
    restored = before_knowledge_maps_bytes(path, raw)
    assert hashlib.sha256(restored).hexdigest() == previous_hash
    assert before_knowledge_maps_bytes(path, restored) == restored
    assert before_knowledge_maps_bytes(path, raw + b"foreign") == raw + b"foreign"
    assert before_knowledge_maps_bytes("unrelated", raw) == raw
