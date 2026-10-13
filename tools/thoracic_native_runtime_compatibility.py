"""Exact offline inverse of the curated thoracic source integration."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/thoracic-native-anatomy-review-20261013/integration/runtime-inverse.json'
PROOF_SHA = '671f77153747ed5f239fa0d0888d6c8ecd99ab5fa861c1e2cec9e5bc97a6a1e7'


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROOF_SHA:
        raise ValueError('Thoracic native inverse evidence changed')
    proof = json.loads(raw)
    if proof['clinical_approval'] is not False or proof['historical_approval_extended'] is not False:
        raise ValueError('Thoracic source inverse cannot extend approval')
    return proof


def previous_runtime_bytes(path, raw, allow_older=False):
    row = reviewed()['files'].get(path)
    if row is None or hashlib.sha256(raw).hexdigest() == row['before_sha256']:
        return raw
    if hashlib.sha256(raw).hexdigest() != row['after_sha256']:
        if allow_older:
            return raw  # Existing historical callers must verify their own older hashes.
        raise ValueError('Unreviewed thoracic native source change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        a, b = change['start'], change['end']
        if ''.join(lines[a:b]) != change['after']:
            raise ValueError('Thoracic native literal change differs')
        lines[a:b] = change['before'].splitlines(keepends=True)
    result = ''.join(lines).encode()
    if hashlib.sha256(result).hexdigest() != row['before_sha256']:
        raise ValueError('Thoracic native inverse changes unrelated bytes')
    return result


def validate_refresh(step):
    proof = reviewed(); row = proof['files']['web/app.js']
    if (step.get('id') != '2026-10-13-thoracic-curated-source-viewer'
            or step.get('files') != {'web/app.js': {'before': row['before_sha256'], 'after': row['after_sha256']}}
            or step.get('scoped_compatibility_amendment') != {'path': PROOF, 'sha256': PROOF_SHA}
            or step.get('native_presentation_change_scope') != 'thoracic_curated_source_wrapper_only'
            or step.get('native_presentation_code_touched') is not True
            or step.get('native_decoder_mesh_CT_renderer_code_touched') is not False
            or any(step.get(k) is not False for k in ['clinical_approval','fine_anatomical_approval','reopens_or_extends_any_review'])):
        raise ValueError('Thoracic native UI refresh leaves its scope')
    previous_runtime_bytes('web/app.js', (ROOT/'web/app.js').read_bytes())
    for path, digest in step['guarded_paths_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
            raise ValueError('Thoracic integration changes guarded native code')
    record = step['curated_source_reader_smoke']; raw = (ROOT/record['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != record['sha256']:
        raise ValueError('Thoracic integrated browser evidence changed')
    browser = json.loads(raw)
    if ({(r['route'],r['width']) for r in browser['rows']} != {(route,width) for route in ['reporting','lesson'] for width in [1440,390]}
            or len(browser['source_bodies']) != 28 or any(r['errors'] for r in browser['rows'])
            or browser['clinical_approval'] is not False):
        raise ValueError('Thoracic integrated browser scope differs')
    return browser
