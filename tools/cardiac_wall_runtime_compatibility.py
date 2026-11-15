"""Exact pre-wall-context view for frozen evidence; no clinical approval extension."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/cardiac-wall-context-review-20261016/integration/runtime-inverse.json'
PROOF_SHA = 'e766b39ef9b1be1ef09a4356829fb211b74e8db3ce7cca7acf45b987d1e6f2ad'
LESSONS = {'rad.5.pleura': 'ra.thoracic-ultrasound', 'rad.5.cardiac-mri': 'ra.mri-cardiomyopathy',
           'rad.5.coronary-ct': 'ra.ct-coronary', 'rad.5.cardiac-masses-devices': 'ra.cardiac-masses'}
NEW_INSTRUCTIONS = 'Inspect each cardiac source separately: original v1 CT and LV-myocardium/chamber labels, curated wall/cusp/papillary objects, and published CT comparison PNGs. In the methods-defined comparisons, green is manual annotation and red is model prediction. Source defects, incomplete anatomy, unverified MRI signal/function and absent current-patient registration remain explicit.'
OLD_INSTRUCTIONS = 'Inspect the original v1 cardiac CT, LV-myocardium label and four chamber regions in matching source planes and complete source-derived interfaces. This CT context does not supply MRI signal, coronary arteries, masses, RV/atrial walls, valves or pericardium; function, normality and current-patient registration remain unverified.'
NEW_THORACIC = 'Inspect original curated sources, separate cardiac/lung CT sources and published CT annotation/prediction comparisons. Their coordinates, versions and case identities remain separate; none is registered to the ultrasound examples or current patient. Required anatomy and clinical validation remain incomplete.'
OLD_THORACIC = 'Inspect original curated surfaces and separate CT sources for lung, basal-organ and LV-myocardium/chamber context. The v1 cardiac and v3 lung images remain distinct, and no source is registered to the ultrasound examples; required anatomy remains incomplete.'


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROOF_SHA:
        raise ValueError('Cardiac wall inverse evidence changed')
    proof = json.loads(raw)
    if proof['clinical_approval'] is not False or proof['extends_historical_approval'] is not False:
        raise ValueError('Cardiac wall inverse cannot extend approval')
    return proof


def before_wall_bytes(path, raw, allow_older=False):
    from tools.hippunfold_runtime_compatibility import before_hippunfold_bytes
    raw = before_hippunfold_bytes(path, raw, allow_older=allow_older)
    row = reviewed()['files'].get(path)
    if row is None or hashlib.sha256(raw).hexdigest() == row['before_sha256']:
        return raw
    if hashlib.sha256(raw).hexdigest() != row['after_sha256']:
        if allow_older:
            return raw
        raise ValueError('Unreviewed cardiac wall context byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        start, end = change['start'], change['end']
        if ''.join(lines[start:end]) != change['after']:
            raise ValueError('Cardiac wall inverse literal differs')
        lines[start:end] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if hashlib.sha256(restored).hexdigest() != row['before_sha256']:
        raise ValueError('Cardiac wall inverse changes unrelated bytes')
    return restored


def before_wall_lesson_fields(module_id, fields):
    from tools.hippunfold_runtime_compatibility import before_hippunfold_lesson_fields
    fields = before_hippunfold_lesson_fields(module_id, fields)
    if module_id not in LESSONS:
        return fields
    result = copy.deepcopy(fields)
    from primer.cardiac_wall_context import REGISTRY, REGISTRY_SHA256, CURATED, COMPARISONS
    raw = REGISTRY.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA256:
        raise ValueError('Cardiac source semantic identity changed')
    data = json.loads(raw)
    additions = [data['groups'][key]['inspector'] for key in [CURATED, COMPARISONS]]
    for media in result.get('lesson_media', []):
        if media.get('id') == 'module-native-inspectors-' + module_id:
            title = 'Original curated thoracic anatomy' if module_id == 'rad.5.pleura' else 'Separate cardiac source anatomy contexts'
            expected = {'id': media['id'], 'kind': 'source-native-inspectors', 'title': title,
                        'instructions': NEW_THORACIC if module_id == 'rad.5.pleura' else NEW_INSTRUCTIONS,
                        'investigation_ids': [LESSONS[module_id]]}
            if media == expected:
                media['title'] = 'Original curated thoracic anatomy' if module_id == 'rad.5.pleura' else 'Original CT cardiac source anatomy'
                media['instructions'] = OLD_THORACIC if module_id == 'rad.5.pleura' else OLD_INSTRUCTIONS
            elif media.get('instructions') not in {OLD_INSTRUCTIONS, OLD_THORACIC}:
                raise ValueError('Unreviewed cardiac context companion fields')
        props = media.get('props', {})
        if 'native_inspectors' in props:
            for addition in additions:
                matching = [item for item in props['native_inspectors'] if item.get('id') == addition['id']]
                if matching and matching != [addition]:
                    raise ValueError('Unreviewed cardiac context inspector fields')
                if matching:
                    props['native_inspectors'].remove(matching[0])
    return result


def validate_refresh(step):
    row = reviewed()['files']['web/app.js']
    if (step.get('id') != '2026-10-16-cardiac-wall-context'
            or step.get('files') != {'web/app.js': {'before': row['before_sha256'], 'after': row['after_sha256']}}
            or step.get('scoped_compatibility_amendment') != {'path': PROOF, 'sha256': PROOF_SHA}
            or step.get('native_presentation_change_scope') != 'supplementary_cardiac_wall_and_comparison_wrappers_only'
            or step.get('native_presentation_code_touched') is not True
            or step.get('native_decoder_mesh_CT_renderer_code_touched') is not False
            or step.get('existing_reporting_guides_retained') is not True
            or any(step.get(key) is not False for key in ['clinical_approval', 'fine_anatomical_approval', 'reopens_or_extends_any_review'])):
        raise ValueError('Cardiac wall context UI refresh leaves its exact scope')
    before_wall_bytes('web/app.js', (ROOT / 'web/app.js').read_bytes())
    for path, expected in step['guarded_paths_sha256'].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError('Cardiac wall context changes guarded native code')
    reader = step['cardiac_wall_reader_smoke']
    raw = (ROOT / reader['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != reader['sha256']:
        raise ValueError('Cardiac wall reader evidence changed')
    proof = json.loads(raw)
    expected = {(route, width, identifier) for route in ['reporting', 'lesson'] for width in [1440, 390]
                for identifier in LESSONS.values()}
    if (len(proof['rows']) != 16 or {(r['route'], r['width'], r['investigation']) for r in proof['rows']} != expected
            or len(proof['bodies']) != 42 or any(r['errors'] or r['curated_source_triangles'] != 72572
                 or not r['existing_reporting_guides_retained'] or not r['eight_comparison_categories_pixels_exact']
                 or not r['uncertain_categories_excluded'] for r in proof['rows'])
            or proof['clinical_approval'] is not False or proof['production_verified'] is not False):
        raise ValueError('Cardiac wall reader evidence scope differs')
    return proof
