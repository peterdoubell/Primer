"""Exact offline comparison views for the reviewed pulmonary-only data delta."""
import copy
import hashlib
import json
from pathlib import Path
from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/pulmonary-release-integration-review-20261012/pulmonary-data-guard-amendment-linear.json'
PROOF_SHA256 = '2bb05a0d5601c1ff0394d97cba0fab7e677bb418edad5d04721e7bee795d83b3'
CASE = 'ra.ct-pulmonary-nodules'
CURRICULUM = 'data/curriculum/11-radiology.json'
REQUIREMENTS = 'data/radiology/non-msk-structure-requirements.json'
OVERRIDE = 'data/radiology/investigation-overrides-non-msk.json'
PATHS = {CURRICULUM, REQUIREMENTS, OVERRIDE}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Pulmonary data amendment fingerprint changed')
    proof = json.loads(raw)
    if (set(proof['files']) != PATHS or proof['main_commit'] != '1e1337aecef27acdc90ce7be93f6a92c3bd36360'
            or any(proof[k] is not False for k in ('clinical_approval', 'fine_anatomical_approval',
                                                  'structure_coverage_granted', 'whole_goal_complete'))):
        raise ValueError('Pulmonary data amendment leaves its fixed scope')
    return proof


def restore_main_raw(path, raw):
    path = str(path)
    if path not in PATHS:
        return raw
    record = reviewed()['files'][path]
    if sha(raw) == record['main_sha256']:
        return raw
    if sha(raw) != record['current_sha256']:
        raise ValueError('Unreviewed pulmonary whole-file or raw-token change')
    text = raw.decode()
    for change in record['changes']:
        if text.count(change['after']) != 1:
            raise ValueError('Pulmonary data amendment lacks its unique literal span')
        text = text.replace(change['after'], change['before'], 1)
    restored = text.encode()
    if sha(restored) != record['main_sha256']:
        raise ValueError('Pulmonary data amendment changes unrelated raw bytes')
    return restored


def _exact(value, tokens, record):
    keys = [key for key in record['token_keys'] if key in tokens]
    if len(keys) != 1:
        raise ValueError('Pulmonary data has missing or ambiguous token namespace')
    key = keys[0]
    if digest(value) != record['semantic_sha256'] or tokens[key] != record['raw_value_token_sha256']:
        raise ValueError('Pulmonary scoped semantics or raw value token changed')
    return key


def restore_prior_view(path, data, tokens):
    """Remove only exact pulmonary additions; preserve unrelated caller drift."""
    path = str(path)
    data, tokens = copy.deepcopy(data), dict(tokens)
    if path not in {REQUIREMENTS, OVERRIDE}:
        return data, tokens
    records = reviewed()['files'][path]['scoped_records']
    if path == OVERRIDE:
        key = _exact(data.get(CASE), tokens, records['investigation'])
        del data[CASE]
        tokens.pop(key)
    else:
        rows = [row for row in data['investigations'] if row['investigation_id'] == CASE]
        if len(rows) != 1 or data['scope']['catalog_investigation_ids'].count(CASE) != 1:
            raise ValueError('Pulmonary addition missing or duplicated')
        keys = [_exact(rows[0], tokens, records['investigation']), _exact(CASE, tokens, records['catalog'])]
        data['investigations'] = [row for row in data['investigations'] if row['investigation_id'] != CASE]
        data['scope']['catalog_investigation_ids'].remove(CASE)
        for key in keys:
            tokens.pop(key)
    return data, tokens


def restore_prior_contracts(contracts):
    record = reviewed()['nonstroke_contract']
    if sha((ROOT / record['prior_receipt_path']).read_bytes()) != record['prior_receipt_sha256']:
        raise ValueError('Frozen nonstroke contract evidence changed')
    if contracts.get(CASE) != record['current_sha256']:
        raise ValueError('Unreviewed pulmonary effective contract')
    restored = dict(contracts)
    restored[CASE] = record['prior_sha256']
    return restored
