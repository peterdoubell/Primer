"""Recover the exact bytes from before the BodyParts3D liver correction (2026-11-19).

The correction rebuilt the liver region of ``web/anatomy/bodyparts3d``: segments VII and VIII are
separate meshes from the objects that carry those names, and the portal vein is three labelled
meshes. Five pinned text files changed with it: the atlas manifest, the liver reporting steps that
list its part identifiers, the two reporting-contract fingerprints of the liver investigations,
the fidelity scope that repeats them, and the catalogue line that accepts the corrected manifest.

Older compatibility checks restore historical bytes of those files. This link runs first and
removes exactly the recorded lines, and only from the exact bytes recorded in
``docs/bodyparts3d-liver-correction-20261119/inverse.json``. Any other change leaves a file
untouched here, so it still fails the checks further down the chain. Nothing here approves
anatomy.
"""
import copy
import hashlib
import json
import struct
from pathlib import Path

from tools.colonvessels_compatibility import _restore

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / 'docs/bodyparts3d-liver-correction-20261119/inverse.json'
PIN = '0434c3ca3e7a6b2bd7e0cae27814ed5d65cae18dd6eb3c5dd6733f72080be385'
MANIFEST = 'web/anatomy/bodyparts3d/manifest.json'
REQUIREMENTS = 'data/radiology/non-msk-structure-requirements.json'
STEPS = 'data/radiology/reporting-steps/abdomen.json'
SCOPE = 'docs/radiology-fidelity-scope.json'
CATALOGUE = 'primer/radiology_catalog.py'
PATHS = frozenset({MANIFEST, REQUIREMENTS, STEPS, SCOPE, CATALOGUE})
# The effective reporting contract of each liver investigation, before and after. Its walkthrough
# lists the atlas parts each step highlights; nothing else in it changed.
CONTRACTS = {
    'ra.liver-masses': {'before': '43c76d03f8a912f8e46830b54119628e1a644f24b374ef28e61db1f0d831d9f1',
                        'after': 'db4d3aa79db92846a1cc11c00b881d0591f7e64a2e6c1c44400f48254a5f0c6e'},
    'ra.liver-lirads': {'before': 'a657efff11ca7cfc89b20969b96cdc321d07a33989541bcc7424bb505e134fe3',
                        'after': '3ff4032b11da97233d99233f968f6bbd82caaca848f76446f7b4d8cde3696454'},
}
EARLIER_PART = {'FJ2823': 'FJ2409', 'FJ2824': 'FMA15746'}
PORTAL_PARTS = ['FJ3082', 'FJ3122', 'FJ3102']
EARLIER_PORTAL_PART = 'FMA14329'


def before_liver_correction_bytes(path, raw):
    if str(path) not in PATHS:
        return raw
    return _restore(path, raw, PROOF, PIN)


def before_liver_correction_requirements(raw):
    return before_liver_correction_bytes(REQUIREMENTS, raw)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def before_liver_correction_contract(identifier, contract):
    """Restore the part identifiers a liver walkthrough listed; any other contract is returned untouched."""
    row = CONTRACTS.get(identifier)
    if row is None or digest(contract) != row['after']:
        return contract
    restored = copy.deepcopy(contract)
    for step in restored['walkthrough']['steps']:
        parts = [EARLIER_PART.get(part, part) for part in step['parts']]
        if PORTAL_PARTS[0] in parts:
            at = parts.index(PORTAL_PARTS[0])
            if parts[at:at + len(PORTAL_PARTS)] != PORTAL_PARTS:
                raise ValueError('Liver correction walkthrough differs')
            parts[at:at + len(PORTAL_PARTS)] = [EARLIER_PORTAL_PART]
        step['parts'] = parts
    if digest(restored) != row['before']:
        raise ValueError('Liver correction changed unrelated contract values')
    return restored


def before_liver_correction_contract_hashes(contracts):
    result = dict(contracts)
    for identifier, row in CONTRACTS.items():
        if result.get(identifier) == row['after']:
            result[identifier] = row['before']
    return result


def before_liver_correction_inventory(investigation):
    """A requirement record with the contract fingerprint it carried before; any other record is returned untouched."""
    row = CONTRACTS.get(investigation.get('investigation_id'))
    if row is None or investigation.get('source_contract_sha256') != row['after']:
        return investigation
    return dict(investigation, source_contract_sha256=row['before'])


def united(first, second):
    """The single mesh the earlier build made of two source objects, from their separate meshes.

    The builder writes positions, then normals, then triangle indices. Two objects share no
    vertex, so each keeps its own normals, and the second object's indices follow the first's
    vertices.
    """
    def parts(raw):
        magic, vertices, indices = struct.unpack('<4sII', raw[:12])
        if magic != b'BP3D' or len(raw) != 12 + vertices * 24 + indices * 4:
            raise ValueError('Not a BodyParts3D atlas mesh')
        return (vertices, indices, raw[12:12 + vertices * 12], raw[12 + vertices * 12:12 + vertices * 24],
                struct.unpack('<%dI' % indices, raw[12 + vertices * 24:]))
    v1, i1, p1, n1, t1 = parts(first)
    v2, i2, p2, n2, t2 = parts(second)
    shifted = tuple(index + v1 for index in t2)
    return (struct.pack('<4sII', b'BP3D', v1 + v2, i1 + i2) + p1 + p2 + n1 + n2
            + struct.pack('<%dI' % (i1 + i2), *(t1 + shifted)))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()
