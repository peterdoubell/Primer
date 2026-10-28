"""Pinned before/after evidence for the independently reproduced GL lifecycle fault.

The captured browser run is not repeated in CI. These tests bind its source and
GPU observations to the current viewer and pin the historical viewer through a
self-contained Git object chain, without requiring a deep checkout or downloads.
"""
from pathlib import Path
import base64
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'docs/nextbrain-context-recovery-20261027'
VIEWER = ROOT / 'web/anatomy/nextbrain'
BASELINE_COMMIT = 'e2d2003d22f0e8516d9066ab15fc9ac5346c795d'
BEFORE_VIEWER_SHA256 = 'aec69df347f00b2f41f8e1bf7d49e8c96e913c273e5f773a4877ad34beacb0b7'
AFTER_VIEWER_SHA256 = '717c65c4bb9976f52ca04526ce4698c38276afb1a646787010804df084c6de40'
SOURCE_FILES = {'viewer.js', 'transport.js', 'index.html', 'viewer.css',
                'manifest.json', 'config.json', 'labels.json'}


def read(name):
    return json.loads((EVIDENCE / name).read_bytes())


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def git_object_id(kind, raw):
    return hashlib.sha1(kind.encode() + b' ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def tree_entries(raw):
    entries = {}
    offset = 0
    while offset < len(raw):
        end = raw.index(b'\0', offset)
        mode, name = raw[offset:end].split(b' ', 1)
        name = name.decode()
        oid = raw[end + 1:end + 21]
        assert len(oid) == 20 and name not in entries
        entries[name] = (mode.decode(), oid.hex())
        offset = end + 21
    assert offset == len(raw)
    return entries


def stale_deletes(proof):
    return [event for event in proof['bufferEvents']
            if event['owner'] is not None
            and event['owner']['epoch'] != event['currentEpoch']]


def test_frozen_before_viewer_is_exactly_the_deployed_merge_file():
    evidence = read('baseline-git-proof.json')
    assert evidence['commit'] == BASELINE_COMMIT
    assert evidence['sourcePath'] == 'web/anatomy/nextbrain/viewer.js'
    commit = base64.b64decode(evidence['commitObjectBase64'], validate=True)
    assert git_object_id('commit', commit) == BASELINE_COMMIT
    expected_oid = commit.splitlines()[0].removeprefix(b'tree ').decode()
    expected_paths = ['', 'web', 'web/anatomy', 'web/anatomy/nextbrain']
    names = ['web', 'anatomy', 'nextbrain', 'viewer.js']
    assert [row['path'] for row in evidence['treePath']] == expected_paths
    for i, row in enumerate(evidence['treePath']):
        raw = base64.b64decode(row['objectBase64'], validate=True)
        assert git_object_id('tree', raw) == row['oid'] == expected_oid
        mode, expected_oid = tree_entries(raw)[names[i]]
        assert mode == ('100644' if i == 3 else '40000')
    frozen = (EVIDENCE / 'viewer.before.js.txt').read_bytes()
    assert git_object_id('blob', frozen) == expected_oid == evidence['blobOid']
    assert len(frozen) == evidence['viewerBytes']
    assert sha256(frozen) == evidence['viewerSHA256'] == BEFORE_VIEWER_SHA256
    assert read('before-proof.json')['sourceSHA256']['viewer.js'] == BEFORE_VIEWER_SHA256


def test_before_failure_and_after_recovery_are_explicit_and_current():
    before, after = read('before-proof.json'), read('after-proof.json')
    assert before['allPassed'] is False
    assert before['pageErrors'] == ['3D draw failed']
    assert [row['code'] for row in before['glErrors']] == [1282]
    deleted = stale_deletes(before)
    assert len(deleted) == 2
    assert {row['owner']['id'] for row in deleted} == {3, 4}
    assert all(row['owner']['epoch'] == 0 and row['currentEpoch'] == 1
               and row['lost'] is False for row in deleted)
    assert after['allPassed'] is True
    assert after['pageErrors'] == after['glErrors'] == after['findings'] == []
    assert after['bufferEvents']  # The observer was active; absence is not an empty capture.
    assert stale_deletes(after) == []
    assert all(not row['lost'] and row['owner']['epoch'] == row['currentEpoch']
               for row in after['bufferEvents'])
    assert set(before['sourceSHA256']) == set(after['sourceSHA256']) == SOURCE_FILES
    assert after['sourceSHA256']['viewer.js'] == AFTER_VIEWER_SHA256
    for name, digest in after['sourceSHA256'].items():
        assert sha256((VIEWER / name).read_bytes()) == digest, name
        if name != 'viewer.js':
            assert before['sourceSHA256'][name] == digest
    assert len(after['cases']) == 1
    case = after['cases'][0]
    assert case['name'] == 'old decompression completes after restored replacement mesh'
    assert case['passed'] and case['heldDecoders'] == 7
    assert case['code'] == 29 and case['meshReady'] == '29' and case['error'] == 0


def test_complete_restored_code29_gpu_matches_current_source_manifest():
    proof = read('after-proof.json')
    raw = (VIEWER / 'manifest.json').read_bytes()
    assert sha256(raw) == proof['sourceSHA256']['manifest.json']
    manifest = json.loads(raw)
    mesh = manifest['meshParts']['29']
    gpu = proof['gpuBuffers']
    assert gpu['code'] == 29 and gpu['glError'] == 0
    expected = []
    for kind in ['positions', 'indices']:
        group = mesh['parts'][kind]
        offset = 0
        for chunk in group['chunks']:
            assert chunk['offset'] == offset
            expected.append({'kind': kind, 'offset': offset, 'bytes': chunk['bytes'],
                             'sha256': chunk['sha256'], 'expected': chunk['sha256']})
            offset += chunk['bytes']
        assert offset == group['bytes']
    assert gpu['rows'] == expected  # Exact set/order; no unverified or omitted buffer spans.
    assert len(expected) == 5
    assert sum(row['bytes'] for row in expected) == 13959144
