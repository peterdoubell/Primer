"""Exact pre-HippUnfold comparison views; no historical approval extension."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/hippunfold-epilepsy-review-20261016/runtime-inverse.json'
PROOF_SHA = 'b6140098624fd68edc72167a0a2a7d30f4f776a480460f153a8a8c55476ad1aa'
READER_PROOF = 'docs/hippunfold-epilepsy-review-20261016/reader-proof.json'
READER_SHA = '96da4fa44dafcb8c394376a515b6435ef6e834e5817e211e51e18e0e57e88a09'
LESSONS = {'rad.5.epilepsy-mri': 'ra.mri-epilepsy', 'rad.5.dementia': 'ra.mri-dementia'}
PATHS = {'web/app.js', 'primer/server.py', 'primer/module_media.py', 'primer/source_native_inspectors.py',
         'vercel.json', 'data/curriculum/11-radiology.json', 'data/radiology/reporting-steps/neuroradiology.json'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA:
        raise ValueError('HippUnfold inverse evidence changed')
    proof = json.loads(raw)
    if (set(proof['files']) != PATHS or proof['base_commit'] != '8c8d841538fdd81cb71f0756b4fbcb437edd3e68'
            or set(proof['lessons']) != set(LESSONS)
            or any(proof[key] is not False for key in ['clinical_approval', 'fine_anatomical_approval',
                                                      'extends_historical_approval', 'structure_coverage_granted'])):
        raise ValueError('HippUnfold inverse leaves its exact scope')
    return proof


def before_hippunfold_bytes(path, raw, allow_older=False):
    row = reviewed()['files'].get(str(path))
    if row is None or sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # The historical caller must validate its own earlier fingerprint.
        raise ValueError('Unreviewed HippUnfold runtime byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        start, end = change['start'], change['end']
        if ''.join(lines[start:end]) != change['after']:
            raise ValueError('HippUnfold inverse literal differs')
        lines[start:end] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('HippUnfold inverse changes unrelated bytes')
    return restored


def _reverse_value(result, change):
    keys = change['path']
    if keys[0] not in result:
        return  # Some historical callers select fewer fields; absent fields are not introduced.
    parent = result
    for key in keys[:-1]:
        parent = parent[key]
    key = keys[-1]
    if parent[key] == change['before']:
        return
    if parent[key] != change['after']:
        raise ValueError('Unreviewed HippUnfold clinical field change')
    parent[key] = copy.deepcopy(change['before'])


def before_hippunfold_lesson_fields(module_id, fields):
    if module_id not in LESSONS:
        return fields
    row = reviewed()['lessons'][module_id]
    result = copy.deepcopy(fields)
    for addition in row['added_media']:
        matching = [item for item in result.get('lesson_media', []) if item.get('id') == addition['id']]
        if matching and matching != [addition]:
            raise ValueError('Unreviewed HippUnfold lesson companion change')
        if matching:
            result['lesson_media'].remove(matching[0])
    for change in row['clinical_fields']:
        _reverse_value(result, change)
    return result


def restore_prior_view(path, data, tokens):
    row = reviewed()['data_values'].get(str(path))
    if row is None:
        return data, tokens
    result, prior_tokens = copy.deepcopy(data), dict(tokens)
    value = result['investigations'][row['investigation_id']]
    # Both existing historical callers hash the same original JSON value span;
    # the myelopathy receipt names that span with an explicit walkthrough prefix.
    namespaces = [row['token_key'], 'walkthrough:' + row['token_key']]
    present = [key for key in namespaces if key in prior_tokens]
    if len(present) != 1:
        raise ValueError('Unreviewed HippUnfold missing or ambiguous raw value token namespace')
    token = present[0]
    if value == row['before'] and prior_tokens.get(token) == row['before_raw_token_sha256']:
        return result, prior_tokens
    if value != row['after'] or prior_tokens.get(token) != row['after_raw_token_sha256']:
        raise ValueError('Unreviewed HippUnfold reporting semantics or raw value token')
    result['investigations'][row['investigation_id']] = copy.deepcopy(row['before'])
    prior_tokens[token] = row['before_raw_token_sha256']
    return result, prior_tokens


def restore_prior_contract(identifier, contract):
    row = reviewed()['contracts'].get(identifier)
    if row is None or contract == row['before']:
        return contract
    if contract != row['after']:
        raise ValueError('Unreviewed HippUnfold effective contract value')
    return copy.deepcopy(row['before'])


def restore_prior_contracts(contracts):
    result = dict(contracts)
    for identifier, row in reviewed()['contracts'].items():
        if identifier not in result or result[identifier] == row['before_sha256']:
            continue
        if result[identifier] != row['after_sha256']:
            raise ValueError('Unreviewed HippUnfold effective contract')
        result[identifier] = row['before_sha256']
    return result


def validate_refresh(step):
    row = reviewed()['files']['web/app.js']
    if (step.get('id') != '2026-10-16-hippunfold-registered-reference'
            or step.get('files') != {'web/app.js': {'before': row['before_sha256'], 'after': row['after_sha256']}}
            or step.get('scoped_compatibility_amendment') != {'path': PROOF, 'sha256': PROOF_SHA}
            or step.get('hippunfold_reader_smoke') != {'path': READER_PROOF, 'sha256': READER_SHA}
            or step.get('native_presentation_change_scope') != 'supplementary_registered_hippocampal_reference_wrappers_only'
            or step.get('native_presentation_code_touched') is not True
            or step.get('native_decoder_mesh_CT_renderer_code_touched') is not False
            or step.get('existing_reporting_guides_retained') is not True
            or any(step.get(key) is not False for key in ['clinical_approval', 'fine_anatomical_approval', 'reopens_or_extends_any_review'])):
        raise ValueError('HippUnfold UI refresh leaves its exact scope')
    before_hippunfold_bytes('web/app.js', (ROOT / 'web/app.js').read_bytes())
    for path, expected in step['guarded_paths_sha256'].items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('HippUnfold refresh changes guarded native code')
    reader = step['hippunfold_reader_smoke']
    raw = (ROOT / reader['path']).read_bytes()
    if sha(raw) != reader['sha256']:
        raise ValueError('HippUnfold reader evidence changed')
    proof = json.loads(raw)
    _validate_reader(proof)
    return proof


def _validate_reader(proof):
    readers = {'Images and registered MRI': 29, '3D anatomy and original source context': 17,
               'Walkthrough original source context': 17, 'Lesson source gallery': 17}
    expected = {(width, identifier, reader) for width in [390, 1440]
                for identifier in LESSONS.values() for reader in readers}
    rows = proof.get('cases', [])
    if (proof.get('productionVerified') is not False or proof.get('errors') != []
            or proof.get('totalReaderCases') != 16 or len(rows) != 16
            or {(row['width'], row['investigation'], row['reader']) for row in rows} != expected
            or proof.get('totalInteractionStates') != 320
            or sum(row['states'] for row in rows) != 320
            or any(row['states'] != readers[row['reader']] or row['gpuMeshes'] != 16
                   or row['gpuPositionAndIndexBytesExact'] is not True
                   or row['noHorizontalOverflow'] is not True for row in rows)
            or proof.get('authentication') != [{'asset': asset, 'unauthenticatedStatus': 401}
                for asset in ['index.html', 'viewer.js', 'manifest.json', 'L-T2w.bin.gz']]
            or proof.get('startupBundle') != {'bytes': 2864514,
                'sha256': 'd18b76355e2237a474b51331a539cea733837ff95ee40427d3e1b324384fee97',
                'currentSourceBytesEqual': True}):
        raise ValueError('HippUnfold reader evidence scope differs')
    for path, expected_sha in proof['sourceSHA256'].items():
        if sha((ROOT / path).read_bytes()) != expected_sha:
            raise ValueError('HippUnfold reader source bytes changed')
    manifest = json.loads((ROOT / 'web/anatomy/hippunfold-hcp101006-registered/manifest.json').read_bytes())
    payloads = {row['file']: row for row in [*manifest['meshes'],
                *(array for side in manifest['hemispheres'] for array in side['arrays'])]}
    observed = proof['deliveredPayloads']
    if set(observed) != set(payloads) or len(observed) != 20:
        raise ValueError('HippUnfold reader delivered payload scope differs')
    for filename, row in observed.items():
        expected_row = payloads[filename]
        representation = row['representation']
        expected_response = expected_row['gzipSHA256'] if representation == 'gzip' else expected_row['decodedSHA256']
        if (representation not in {'gzip', 'HTTP-decoded'} or row['status'] != 200
                or row['bytes'] != expected_row['byteLength']
                or row['decodedSHA256'] != expected_row['decodedSHA256']
                or row['responseSHA256'] != expected_response):
            raise ValueError('HippUnfold reader delivered payload differs')
