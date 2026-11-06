"""Restore only the reviewed vessel delivery and navigation changes."""
import hashlib
import json
from pathlib import Path

PROOF = Path(__file__).resolve().parents[1] / "docs/colonvessels-source/runtime-inverse.json"
PIN = "7aed07f76d382badcc6bad7bf527bb87732479bbb8c189da04ab6f0431ca4e1c"

NAVIGATION_PROOF = PROOF.parents[1] / "vessel-study-navigation/runtime-inverse.json"
NAVIGATION_PIN = "a0b4ea5f3810fbccd373115b3199b828fd99fbcc74831c78504db38422372add"


def _restore(path, raw, source, pin):
    proof = source.read_bytes()
    if hashlib.sha256(proof).hexdigest() != pin:
        raise ValueError("Vessel evidence changed")
    record = json.loads(proof).get(str(path))
    if record is None or hashlib.sha256(raw).hexdigest() != record["after"]:
        return raw
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(record["changes"]):
        start, end = change["start"], change["end"]
        if "".join(lines[start:end]) != change["after"]:
            raise ValueError("Vessel integration literal differs")
        lines[start:end] = change["before"].splitlines(keepends=True)
    restored = "".join(lines).encode()
    if hashlib.sha256(restored).hexdigest() != record["before"]:
        raise ValueError("Vessel integration changed unrelated bytes")
    return restored


def before_vessel_navigation_bytes(path, raw):
    if str(path) != "web/app.js":
        return raw
    return _restore(path, raw, NAVIGATION_PROOF, NAVIGATION_PIN)


def before_colonvessels_bytes(path, raw):
    if str(path) not in {"primer/server.py", "vercel.json", "web/app.js"}:
        return raw
    return _restore(path, raw, PROOF, PIN)
