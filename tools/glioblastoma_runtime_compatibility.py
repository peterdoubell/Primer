"""Restore the three exact shared files for historical verification."""
import hashlib
import json
from pathlib import Path

PROOF = Path(__file__).resolve().parents[1] / "docs/glioblastoma-review-20261104/runtime-inverse.json"
PROOF_SHA256 = "bb094f31f6d187d89cf28111e7fa57f47e6b8566a5814d2d83400cbfb0c9871d"


def before_glioblastoma_bytes(path, raw, allow_older=False):
    if str(path) == "web/app.js" and hashlib.sha256(raw).hexdigest() == "e778eb7a79d73b133b742520aebdf456c0ac46124393019a6400761fc2b5e5cd":
        raw = raw.replace(b"  if (n.id === 'rad.5.uterine-mr') page.append(el('a', { class: 'btn ghost', href: '/app/reference-studies/mullerian-2025/index.html' },\n    'Compare uterine cavity and external contour on source images'));\n", b"", 1)
    if str(path) == "web/app.js" and hashlib.sha256(raw).hexdigest() == "9d93a0f6dd960989e74a874d7617da89e420785e33971fe607acebc3cd926868":
        raw = raw.replace(b"  if (n.id === 'math.3.statistics') page.append(el('a', { class: 'btn ghost', href: '/app/math/sampling-mean/index.html' },\n    'Compare population spread and sampling uncertainty'));\n", b"", 1)
    from tools.module_mission_compatibility import previous_shell_bytes
    raw = previous_shell_bytes(str(path), raw)
    if str(path) == "web/app.js" and hashlib.sha256(raw).hexdigest() == "e8da7f9a2e01343b6855367a61e48907248ad9de8d27455a901e9602eba63a0a":
        raw = raw.replace(b"  if (n.id === 'phys.1.sound') page.append(el('a', { class: 'btn ghost', href: '/app/physics/longitudinal-sound/index.html' },\n    'Explore a longitudinal sound wave'));\n", b"", 1)
    if str(path) == "web/app.js" and hashlib.sha256(raw).hexdigest() == "2c25e11089024f917cfcbb6559f5a6ef4a77fcad2ce0029cab88ab01e931ac58":
        raw = raw.replace(b"  if (n.id === 'phys.1.sound') page.append(el('a', { class: 'btn ghost', href: '/app/physics/longitudinal-sound/index.html' },\n    'Explore a longitudinal sound wave'));\n", b"", 1)
    if str(path) == "web/app.js" and hashlib.sha256(raw).hexdigest() == "1893e5ec4ce605116a17c440a8be0ddd9875fa09cc855ce518378fb4fd990896":
        raw = raw.replace(b"  if (n.id === 'lang.3.media') page.append(el('a', { class: 'btn ghost', href: '/app/language/headline-editor/index.html' },\n    'Edit a headline using counts and rates'));\n", b"", 1)
    if str(path) == "web/app.js" and hashlib.sha256(raw).hexdigest() == "bab461f1add850f4914266490dbda16c8a55a0751c8ba52fb7f5a44722af5834":
        raw = raw.replace(b"  if (n.id === 'rad.5.adrenal') page.append(el('a', { class: 'btn ghost', href: '/app/anatomy/kidney-adrenal-s0028/index.html' },\n    'Inspect kidneys and adrenal glands on CT and in 3D'));\n", b"", 1)
    if str(path) == "web/app.js" and hashlib.sha256(raw).hexdigest() == "122458094c0eb1eddd8b31214695bf0c88a88fe1ad748cc3fe35c9b70f39e167":
        raw = raw.replace(b"  if (n.id === 'rad.4.kidney') page.append(el('a', { class: 'btn ghost', href: '/app/anatomy/cptac-renal-contours/index.html' },\n    'Inspect renal lesion CT and original contours'));\n", b"", 1)
    if str(path) == "web/app.js" and hashlib.sha256(raw).hexdigest() == "895b371767517c736e9c7c7aa10e9641007ee06e04bd6478f852a5a3e90d2a6c":
        raw = raw.replace(b"  if (n.id === 'rad.5.pancreas-tumour') page.append(el('a', { class: 'btn ghost', href: '/app/anatomy/msd-pancreas/index.html' },\n    'Inspect a pancreatic mass on CT and in 3D'));\n", b"", 1)
    if str(path) == "web/app.js" and hashlib.sha256(raw).hexdigest() == "02e4552f25ce70d115dd18c953b6107ec79807176fbf5deb4a522249ec4c628c":
        raw = raw.replace(b"  if (n.id === 'rad.4.liver') page.append(el('a', { class: 'btn ghost', href: '/app/anatomy/liver-s0028/index.html' },\n    'Inspect liver CT in three planes'));\n", b"", 1)
    if str(path) == "web/app.js" and hashlib.sha256(raw).hexdigest() == "ec5a4bf40d5f478da3d80736bd1c9dd2b43417260ff2cc6a2808b217a6079591":
        raw = raw.replace(b"  if (n.id === 'math.2.data') page.append(el('a', { class: 'btn ghost', href: '/app/math/bar-scales/index.html' },\n    'Compare the same scores on two scales'));\n", b"", 1)
    if str(path) == "web/app.js" and hashlib.sha256(raw).hexdigest() == "fc0c36850c32b17eb0fcaa8d8da40aa3b0d6c37cd739b8f1254157efce5c3790":
        raw = raw.replace(b"  if (n.id === 'lang.1.dictionary') page.append(el('a', { class: 'btn ghost', href: '/app/language/dictionary/index.html' },\n    'Play the guide-word hunt'));\n", b"", 1)
    # Project the later experiment link only when the entire reader matches.
    if str(path) == "web/app.js" and hashlib.sha256(raw).hexdigest() == "d1d756aeaac40ea52afaf81732b9559b4a7bbff1076954d75dcce09ae1d80823":
        raw = raw.replace(
            b"  if (n.id === 'phys.4.experiment') page.append(el('a', { class: 'btn ghost', href: '/app/physics/lab-comparison/index.html' },\n"
            b"    'Compare two laboratory measurements'));\n", b"", 1)
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
