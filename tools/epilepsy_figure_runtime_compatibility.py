"""Exact pre-figure comparison views; no historical approval or anatomy extension."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/epilepsy-pathology-figure-review-20261016/runtime-inverse.json'
PROOF_SHA = '796b0ddf3c1dedf0a5f053b09478f2046a3c6748168d58c22282f9fef1928340'
CASE = 'ra.mri-epilepsy'
MODULE = 'rad.5.epilepsy-mri'
FIGURES = frozenset({'open-epilepsy-pmc4557590-fig1', 'open-epilepsy-pmc4557590-fig6',
                    'open-epilepsy-pmc4557590-fig7', 'open-epilepsy-pmc8353251-fig2',
                    'open-epilepsy-pmc8353251-fig3', 'open-epilepsy-pmc8353251-fig4'})
PATHS = frozenset({'data/radiology/radiology-open-images.json', 'data/radiology/radiology-asset-evidence.json',
                   'data/radiology/radiology-static-rasters.json', 'data/radiology/reporting-steps/neuroradiology.json',
                   'docs/radiology-fidelity-scope.json'})


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA:
        raise ValueError('Epilepsy figure inverse evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != '6881f3238f26c4c3fba36d4970faa8e01045ad36'
            or set(proof['files']) != PATHS or set(proof['figure_ids']) != FIGURES
            or proof['lesson']['module_id'] != MODULE or proof['contract']['investigation_id'] != CASE
            or any(proof[key] is not False for key in ['clinical_approval', 'fine_anatomical_approval',
                                                      'structure_coverage_granted', 'extends_historical_approval'])):
        raise ValueError('Epilepsy figure inverse leaves its fixed scope')
    return proof


def before_figure_bytes(path, raw, allow_older=False):
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'].get(path)
    if row is None or sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # The caller must bind an earlier version to its own exact fingerprint.
        raise ValueError('Unreviewed epilepsy figure byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        start, end = change['start'], change['end']
        if ''.join(lines[start:end]) != change['after']:
            raise ValueError('Epilepsy figure inverse literal differs')
        lines[start:end] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Epilepsy figure inverse changes unrelated bytes')
    return restored


def before_figure_lesson_fields(module_id, fields):
    if module_id != MODULE:
        return fields
    expected = reviewed()['lesson']['added_media']
    result = copy.deepcopy(fields)
    matches = [item for item in result.get('lesson_media', []) if item.get('id') == expected['id']]
    if matches and matches != [expected]:
        raise ValueError('Unreviewed epilepsy figure lesson companion')
    if matches:
        result['lesson_media'].remove(matches[0])
    return result


def _token_key(tokens, keys):
    present = [key for key in keys if key in tokens]
    if len(present) != 1:
        raise ValueError('Unreviewed epilepsy figure missing or ambiguous raw value token namespace')
    return present[0]


def restore_prior_view(path, data, tokens):
    path = str(path)
    if path not in {'data/radiology/radiology-open-images.json', 'data/radiology/radiology-asset-evidence.json',
                    'data/radiology/reporting-steps/neuroradiology.json'}:
        return data, tokens
    row = reviewed()['data_values'].get(path)
    if row is None:
        return data, tokens
    result, prior_tokens = copy.deepcopy(data), dict(tokens)
    if row['kind'] == 'added_mapping':
        key = row['key']
        if key not in result:
            if any(token in prior_tokens for token in row['token_keys']):
                raise ValueError('Unreviewed epilepsy figure orphan raw value token')
            return result, prior_tokens
        token = _token_key(prior_tokens, row['token_keys'])
        if result[key] != row['after'] or prior_tokens[token] != row['after_raw_token_sha256']:
            raise ValueError('Unreviewed epilepsy figure source semantics or raw value token')
        del result[key]
        del prior_tokens[token]
    elif row['kind'] == 'added_array_records':
        matches = [item for item in result[row['field']] if item.get('id') in FIGURES]
        if not matches:
            if any(row['token_prefix'] + identifier in prior_tokens for identifier in FIGURES):
                raise ValueError('Unreviewed epilepsy figure orphan asset token')
            return result, prior_tokens
        if matches != row['after']:
            raise ValueError('Unreviewed epilepsy figure asset semantics, omission or duplicate')
        for item in matches:
            key = row['token_prefix'] + item['id']
            if prior_tokens.get(key) != row['raw_token_sha256'][item['id']]:
                raise ValueError('Unreviewed epilepsy figure asset raw value token')
            del prior_tokens[key]
        # All six exact records were checked above; unfamiliar IDs remain visible.
        result[row['field']] = [item for item in result[row['field']] if item.get('id') not in FIGURES]
    else:
        token = _token_key(prior_tokens, row['token_keys'])
        value = result[row['field']][row['key']]
        if value == row['before'] and prior_tokens[token] == row['before_raw_token_sha256']:
            return result, prior_tokens
        if value != row['after'] or prior_tokens[token] != row['after_raw_token_sha256']:
            raise ValueError('Unreviewed epilepsy figure walkthrough semantics or raw value token')
        result[row['field']][row['key']] = copy.deepcopy(row['before'])
        prior_tokens[token] = row['before_raw_token_sha256']
    return result, prior_tokens


def restore_prior_contract(identifier, contract):
    if identifier != CASE:
        return contract
    row = reviewed()['contract']
    if contract == row['before']:
        return contract
    if contract != row['after']:
        raise ValueError('Unreviewed epilepsy figure effective contract value')
    return copy.deepcopy(row['before'])


def restore_prior_contracts(contracts):
    if CASE not in contracts:
        return contracts
    row = reviewed()['contract']
    if contracts[CASE] == row['before_sha256']:
        return contracts
    if contracts[CASE] != row['after_sha256']:
        raise ValueError('Unreviewed epilepsy figure effective contract')
    result = dict(contracts)
    result[CASE] = row['before_sha256']
    return result
