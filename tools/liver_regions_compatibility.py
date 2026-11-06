"""Restore exact reviewed shared files before the liver-region study."""
import hashlib
import json
from pathlib import Path

PROOF = Path(__file__).resolve().parents[1] / "docs/liver-regions-integration/runtime-inverse.json"
PIN = "719eb66eedd392b4dc4eab1375e583f36a64e3c0493d3bf6e22ca6e0cbabd6c2"

def before_liver_regions_bytes(path, raw):
    if str(path) not in {"primer/server.py", "vercel.json", "web/app.js"}:
        return raw
    proof = PROOF.read_bytes()
    if hashlib.sha256(proof).hexdigest() != PIN:
        raise ValueError("Liver integration proof changed")
    record = json.loads(proof)[str(path)]
    if hashlib.sha256(raw).hexdigest() != record["after"]:
        return raw
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(record["changes"]):
        start, end = change["start"], change["end"]
        if "".join(lines[start:end]) != change["after"]:
            raise ValueError("Liver integration literal differs")
        lines[start:end] = change["before"].splitlines(keepends=True)
    restored = "".join(lines).encode()
    if hashlib.sha256(restored).hexdigest() != record["before"]:
        raise ValueError("Liver integration changed unrelated bytes")
    return restored
