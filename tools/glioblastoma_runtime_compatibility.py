"""Restore the three exact shared files for historical verification."""
import hashlib
import json
from pathlib import Path

PROOF = Path(__file__).resolve().parents[1] / "docs/glioblastoma-review-20261104/runtime-inverse.json"
PROOF_SHA256 = "bb094f31f6d187d89cf28111e7fa57f47e6b8566a5814d2d83400cbfb0c9871d"


def before_glioblastoma_bytes(path, raw, allow_older=False):
    if str(path) not in {"web/app.js", "primer/server.py", "tools/language_computation_runtime_compatibility.py"}:
        return raw
    proof = PROOF.read_bytes()
    if hashlib.sha256(proof).hexdigest() != PROOF_SHA256:
        raise ValueError("Glioblastoma integration evidence changed")
    row = json.loads(proof)[str(path)]
    digest = hashlib.sha256(raw).hexdigest()
    if digest == row["before_sha256"]:
        return raw
    if digest != row["after_sha256"]:
        if allow_older:
            return raw
        raise ValueError("Unreviewed glioblastoma integration change")
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row["changes"]):
        start, end = change["start"], change["end"]
        if "".join(lines[start:end]) != change["after"]:
            raise ValueError("Glioblastoma integration literal differs")
        lines[start:end] = change["before"].splitlines(keepends=True)
    restored = "".join(lines).encode()
    if hashlib.sha256(restored).hexdigest() != row["before_sha256"]:
        raise ValueError("Glioblastoma integration inverse differs")
    return restored
