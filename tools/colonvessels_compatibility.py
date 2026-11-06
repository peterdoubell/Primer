"""Restore only the reviewed vessel delivery and navigation changes."""
import hashlib
import json
from pathlib import Path

PROOF = Path(__file__).resolve().parents[1] / "docs/colonvessels-source/runtime-inverse.json"
PIN = "7aed07f76d382badcc6bad7bf527bb87732479bbb8c189da04ab6f0431ca4e1c"

def before_colonvessels_bytes(path, raw):
    if str(path) not in {"primer/server.py", "vercel.json", "web/app.js"}:
        return raw
    proof = PROOF.read_bytes()
    if hashlib.sha256(proof).hexdigest() != PIN:
        raise ValueError("Vessel delivery proof changed")
    record = json.loads(proof)[str(path)]
    if hashlib.sha256(raw).hexdigest() != record["after"]:
        return raw
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(record["changes"]):
        start, end = change["start"], change["end"]
        if "".join(lines[start:end]) != change["after"]:
            raise ValueError("Vessel delivery literal differs")
        lines[start:end] = change["before"].splitlines(keepends=True)
    restored = "".join(lines).encode()
    if hashlib.sha256(restored).hexdigest() != record["before"]:
        raise ValueError("Vessel delivery changed unrelated bytes")
    return restored
