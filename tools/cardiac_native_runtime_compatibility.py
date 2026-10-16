"""Exact prior runtime view of the cardiac source addition; no approval waiver."""
import hashlib
import json
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/cardiac-native-source-review-v1-s0028/integration/runtime-inverse.json'
PROOF_SHA = 'ac9f8cb4095f84a223506457b80c7975982a235c2e59375845d4cbe42c8f426a'
LESSON_BINDINGS = {'rad.5.cardiac-mri': 'ra.mri-cardiomyopathy', 'rad.5.coronary-ct': 'ra.ct-coronary',
                   'rad.5.cardiac-masses-devices': 'ra.cardiac-masses'}
CARDIAC_INSTRUCTIONS = 'Inspect the original v1 cardiac CT, LV-myocardium label and four chamber regions in matching source planes and complete source-derived interfaces. This CT context does not supply MRI signal, coronary arteries, masses, RV/atrial walls, valves or pericardium; function, normality and current-patient registration remain unverified.'


def before_cardiac_lesson_fields(module_id, fields):
    """Remove only the exact new companion from an older figure-only comparison."""
    from tools.cardiac_wall_runtime_compatibility import before_wall_lesson_fields
    fields = before_wall_lesson_fields(module_id, fields)
    if module_id not in LESSON_BINDINGS:
        return fields
    restored = copy.deepcopy(fields)
    expected = {'id': 'module-native-inspectors-' + module_id, 'kind': 'source-native-inspectors',
                'title': 'Original CT cardiac source anatomy', 'instructions': CARDIAC_INSTRUCTIONS,
                'investigation_ids': [LESSON_BINDINGS[module_id]]}
    additions = [item for item in restored['lesson_media'] if item.get('id') == expected['id']]
    if not additions:
        return restored
    if additions != [expected]:
        raise ValueError('Unreviewed cardiac lesson companion change')
    restored['lesson_media'].remove(additions[0])
    return restored


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROOF_SHA:
        raise ValueError('Cardiac inverse evidence changed')
    proof = json.loads(raw)
    if proof['clinical_approval'] is not False or proof['extends_historical_approval'] is not False:
        raise ValueError('Cardiac inverse cannot extend approval')
    return proof


def before_cardiac_bytes(path, raw, allow_older=False):
    from tools.cardiac_wall_runtime_compatibility import before_wall_bytes
    raw = before_wall_bytes(path, raw, allow_older=allow_older)
    row = reviewed()['files'].get(path)
    if row is None or hashlib.sha256(raw).hexdigest() == row['before_sha256']:
        return raw
    if hashlib.sha256(raw).hexdigest() != row['after_sha256']:
        if allow_older:
            return raw
        raise ValueError('Unreviewed cardiac source byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        start, end = change['start'], change['end']
        if ''.join(lines[start:end]) != change['after']:
            raise ValueError('Cardiac inverse literal differs')
        lines[start:end] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if hashlib.sha256(restored).hexdigest() != row['before_sha256']:
        raise ValueError('Cardiac inverse changes unrelated bytes')
    return restored


def validate_refresh(step):
    row = reviewed()['files']['web/app.js']
    if (step.get('id') != '2026-10-14-cardiac-native-source'
            or step.get('files') != {'web/app.js': {'before': row['before_sha256'], 'after': row['after_sha256']}}
            or step.get('scoped_compatibility_amendment') != {'path': PROOF, 'sha256': PROOF_SHA}
            or step.get('native_presentation_change_scope') != 'cardiac_original_CT_and_interfaces_wrapper_only'
            or step.get('native_presentation_code_touched') is not True
            or step.get('native_decoder_mesh_CT_renderer_code_touched') is not False
            or any(step.get(flag) is not False for flag in ['clinical_approval', 'fine_anatomical_approval', 'reopens_or_extends_any_review'])):
        raise ValueError('Cardiac source UI refresh leaves its exact scope')
    before_cardiac_bytes('web/app.js', (ROOT / 'web/app.js').read_bytes())
    for path, digest in step['guarded_paths_sha256'].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('Cardiac source changes guarded native code')
    record = step['cardiac_source_reader_smoke']
    raw = (ROOT / record['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != record['sha256']:
        raise ValueError('Cardiac source reader evidence changed')
    proof = json.loads(raw)
    ids = {'ra.thoracic-ultrasound', 'ra.mri-cardiomyopathy', 'ra.ct-coronary', 'ra.cardiac-masses'}
    expected = {(route, width, identifier) for route in ['reporting', 'lesson'] for width in [1440, 390] for identifier in ids}
    if (len(proof['rows']) != 16 or {(r['route'], r['width'], r['investigation']) for r in proof['rows']} != expected
            or len(proof['bodies']) != 17 or any(r['errors'] or r['source_triangles'] != 86072
                or not r['browser_CT_and_mask_payloads_exact'] or not r['existing_reporting_guides_retained'] for r in proof['rows'])
            or proof['clinical_approval'] is not False or proof['production_verified'] is not False):
        raise ValueError('Cardiac source reader scope differs')
    return proof
