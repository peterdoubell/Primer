"""Restore only one independently reviewed trauma addition for historical guards.

This is an in-memory comparison bridge, never a registry writer. Fixed reviewed
paths and fingerprints preserve the old myelopathy guard's unrelated semantics
and raw value-token checks. Source, patient and anatomical approvals do not grow.
"""
import copy
import hashlib
import json
from pathlib import Path

from tools.check_radiology_fidelity import digest

ROOT = Path(__file__).resolve().parents[2]
AMENDMENT = ROOT / 'docs/myelopathy-published-source-review-20261011/traumatic-registry-additive-amendment-20261011.json'
AMENDMENT_SHA256 = '1bb68c6cc4b7dca343ad62062141df9a04dc120a53819324c23cace024606692'
INVESTIGATION = 'ra.ct-traumatic-haemorrhage'
PATHS = (
    'data/radiology/radiology-open-images.json',
    'data/radiology/radiology-asset-evidence.json',
    'data/radiology/non-msk-structure-requirements.json',
    'data/radiology/reporting-steps/neuroradiology.json',
)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed_amendment():
    raw = AMENDMENT.read_bytes()
    if _sha(raw) != AMENDMENT_SHA256:
        raise ValueError('Trauma additive amendment fingerprint changed')
    review = json.loads(raw)
    if (review.get('investigation_id') != INVESTIGATION
            or set(review.get('files', {})) != set(PATHS)
            or any(review.get(flag) is not False for flag in
                   ('clinical_approval', 'fine_structure_coverage_granted',
                    'native_patient_registration_verified', 'patient_specific_3D_approved'))):
        raise ValueError('Trauma amendment changes its reviewed scope or approvals')
    for path, expected in review['pinned_originals_SHA256'].items():
        if _sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('Original source/dependency review changed: ' + path)
    return review


def _require_exact(value, tokens, record):
    if (digest(value) != record['current_semantic_SHA256']
            or tokens.get(record['historical_token_key']) != record['current_value_token_SHA256']):
        raise ValueError('Trauma addition differs from its reviewed semantics or raw value token')


def restore_prior_view(path, data, tokens):
    """Remove/restore only the exact approved trauma values in a copied view."""
    path = str(path)
    if path not in PATHS:
        raise ValueError('Unreviewed historical registry path')
    review = reviewed_amendment()
    record = review['files'][path]
    data, tokens = copy.deepcopy(data), dict(tokens)
    if path == PATHS[0]:
        value = data.get(INVESTIGATION)
        _require_exact(value, tokens, record)
        if (len(value) != 15
                or {row['id'] for row in value} != set(review['approved_added_image_ids'])):
            raise ValueError('Trauma source figure selection changed')
        del data[INVESTIGATION]
        tokens.pop(record['historical_token_key'])
    elif path == PATHS[1]:
        expected = {row['id']: row for row in record['added_assets']}
        selected = [row for row in data['assets'] if row['id'] in expected]
        if len(selected) != len(expected) or {row['id'] for row in selected} != set(expected):
            raise ValueError('Trauma asset addition is incomplete or duplicated')
        for row in selected:
            _require_exact(row, tokens, expected[row['id']])
            tokens.pop(expected[row['id']]['historical_token_key'])
        data['assets'] = [row for row in data['assets'] if row['id'] not in expected]
    elif path == PATHS[2]:
        selected = [row for row in data['investigations']
                    if row['investigation_id'] == INVESTIGATION]
        if len(selected) != 1:
            raise ValueError('Trauma requirement addition is incomplete or duplicated')
        _require_exact(selected[0], tokens, record)
        ids = data['scope']['catalog_investigation_ids']
        if (ids.count(INVESTIGATION) != 1
                or tokens.get(record['scope_historical_token_key']) != record['scope_value_token_SHA256']):
            raise ValueError('Trauma scope ID differs from its reviewed addition')
        data['investigations'] = [row for row in data['investigations']
                                  if row['investigation_id'] != INVESTIGATION]
        data['scope']['catalog_investigation_ids'] = [value for value in ids
                                                     if value != INVESTIGATION]
        tokens.pop(record['historical_token_key'])
        tokens.pop(record['scope_historical_token_key'])
    else:
        _require_exact(data['investigations'].get(INVESTIGATION), tokens, record)
        prior = record['prior_value']
        if digest(prior) != record['prior_semantic_SHA256']:
            raise ValueError('Historical trauma walkthrough baseline changed')
        data['investigations'][INVESTIGATION] = copy.deepcopy(prior)
        tokens[record['historical_token_key']] = record['prior_value_token_SHA256']
    return data, tokens


def validate_format_amendment(*, raw=None):
    """Approve the exact canonical formatting while retaining every JSON value."""
    review = reviewed_amendment()
    record = review['format_amendment']
    # A caller may supply the exact in-memory pre-addition comparison view.
    # Full original raw/semantic hashes and canonical format remain mandatory.
    if raw is None:
        raw = (ROOT / PATHS[3]).read_text(encoding='utf-8')
    data = json.loads(raw)
    if (_sha(raw.encode()) != record['after_raw_file_SHA256']
            or digest(data) != record['before_and_after_full_semantic_SHA256']
            or raw != json.dumps(data, indent=2, ensure_ascii=False) + '\n'
            or record['semantic_values_unchanged'] is not True
            or record['all_unrelated_value_tokens_byte_identical'] is not True):
        raise ValueError('Neuroradiology formatting differs from the exact reviewed amendment')
    return record
