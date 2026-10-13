"""Exact offline inverse of thoracic source additions; no historical approval extension."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/thoracic-ultrasound-source-review-20261013/evidence/historical-data-inverse.json'
PROOF_SHA = 'd26b72ed2d35f9f727e8819adc5ee15b395ea1701ba5e7d285689d4a41a68b41'
CASE = 'ra.thoracic-ultrasound'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA:
        raise ValueError('Thoracic inverse evidence changed')
    proof = json.loads(raw)
    if proof['clinical_approval'] is not False or proof['extends_historical_approval'] is not False:
        raise ValueError('Thoracic inverse cannot extend historical approval')
    return proof


def restore_raw(path, raw, *, allow_historical=False):
    row = reviewed()['files'].get(str(path))
    if row is None or sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_historical:
            return raw  # The existing historical caller must validate its own earlier version.
        raise ValueError('Unreviewed thoracic whole-file change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        start, end = change['after_line_start'], change['after_line_end']
        if ''.join(lines[start:end]) != change['after']:
            raise ValueError('Thoracic inverse literal span changed')
        lines[start:end] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Thoracic inverse changed unrelated bytes')
    return restored


def restore_view(path, data, tokens):
    row = reviewed()['files'].get(str(path))
    if row is None or 'scoped_values' not in row:
        return data, tokens
    data, tokens = copy.deepcopy(data), dict(tokens)
    scope = row['scoped_values']
    if str(path).endswith('radiology-asset-evidence.json'):
        for field, record in scope.items():
            added = {item['id']: item for item in record['added']}
            found = [item for item in data[field] if item['id'] in added]
            if {item['id']: item for item in found} != added or len(found) != len(added):
                raise ValueError('Thoracic added source evidence changed')
            data[field] = [item for item in data[field] if item['id'] not in added]
    else:
        collection = data['investigations'] if scope['nested'] else data
        if collection.get(CASE) != scope['after']:
            raise ValueError('Thoracic scoped source metadata changed')
        if scope['present_before']:
            collection[CASE] = copy.deepcopy(scope['before'])
        else:
            del collection[CASE]
    for key, change in row['tokens'].items():
        if key not in tokens:
            continue  # Some historical callers intentionally omit their own rows.
        if tokens[key] != change['after']:
            raise ValueError('Thoracic raw value token changed')
        if change['before'] is None:
            del tokens[key]
        else:
            tokens[key] = change['before']
    return data, tokens


def restore_contract(identifier, contract):
    if identifier != CASE:
        return contract
    row = reviewed()['contract']
    if contract == row['before']:
        return contract
    if contract != row['after']:
        raise ValueError('Unreviewed thoracic reporting contract')
    return copy.deepcopy(row['before'])


def restore_contract_hashes(contracts):
    from tools.check_radiology_fidelity import digest
    row = reviewed()['contract']
    result = dict(contracts)
    if CASE in result:
        if result[CASE] != digest(row['after']):
            raise ValueError('Thoracic reporting fingerprint changed')
        result[CASE] = digest(row['before'])
    return result
