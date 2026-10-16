"""Exact historical view before the SPL companion; no anatomy approval extension."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/spl-limbic-source-review-20261016/integration/runtime-inverse.json'
PROOF_SHA = 'c80d0ac9ee6bf8f4684a0e3c7cf2c805a92f40c018d2d1079182ae31871231ec'
PATHS = frozenset(['web/app.js', 'primer/server.py', 'primer/module_media.py', 'primer/source_native_inspectors.py', 'vercel.json', 'docs/radiology-fidelity-scope.json'])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA:
        raise ValueError('SPL integration inverse changed')
    proof = json.loads(raw)
    if (set(proof['files']) != PATHS or proof['atlas'] != 'spl-nac-limbic'
            or proof['base_commit'] != '20e467094ece94c5cbf90207c38f69cbe62c74af'
            or proof['source_commit'] != 'bec24db25aad5f7600e2df3becfb1f883e61ff56'
            or set(proof['lessons']) != {'rad.5.epilepsy-mri', 'rad.5.dementia'}
            or proof['bindings'] != ['ra.brain-anatomy', 'ra.mri-dementia', 'ra.mri-epilepsy']
            or proof['source_inspector_addition']['id'] != 'spl-nac-limbic-native-reference'
            or any(proof[key] is not False for key in ['clinical_approval', 'extends_historical_approval',
                                                       'new_source_or_reader_validated_by_this_inverse'])):
        raise ValueError('SPL integration inverse leaves its scope')
    return proof


def before_spl_bytes(path, raw, allow_older=False):
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # Earlier callers must still validate their exact expected identity.
        raise ValueError('Unreviewed SPL runtime byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('SPL inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('SPL inverse changes unrelated bytes')
    return restored


def before_spl_lesson_fields(module_id, fields):
    if module_id not in {'rad.5.epilepsy-mri', 'rad.5.dementia'}:
        return fields
    row = reviewed()['lessons'][module_id]
    result = copy.deepcopy(fields)
    items = result.get('lesson_media', [])
    matches = [item for item in items if item.get('id') == row['after']['id']]
    if not matches or matches == [row['before']]:
        return result
    if matches != [row['after']]:
        raise ValueError('Unreviewed SPL lesson wrapper change')
    items[items.index(matches[0])] = copy.deepcopy(row['before'])
    return result


def before_spl_reference_fields(identifier, fields):
    proof = reviewed()
    if identifier not in proof['bindings']:
        return fields
    result = copy.deepcopy(fields)
    addition = proof['source_inspector_addition']
    entries = result.get('source_native_inspectors', [])
    matches = [item for item in entries if item.get('id') == addition['id']]
    if matches:
        if matches != [addition]:
            raise ValueError('Unreviewed SPL source inspector change')
        entries.remove(matches[0])
    return result


READER_PROOF = 'docs/spl-limbic-source-review-20261016/viewer/reader-proof.json'
READER_SHA = 'fc267e5c440bf6d65fbf6776770e57dae81d8d0cf15e6597d5af4b40e7ff3e6b'
STANDALONE_PROOF = 'docs/spl-limbic-source-review-20261016/viewer/standalone-proof.json'
STANDALONE_SHA = '81608f66cb5505b3d3fc113e09d851cacfb16913ada8fd5fda5d25245d3f308f'


def validate_refresh(step):
    """Advance the shared wrapper only with the actual current reader evidence."""
    row = reviewed()['files']['web/app.js']
    if (step.get('id') != '2026-10-16-spl-native-limbic-reference'
            or step.get('files') != {'web/app.js': {'before': row['before_sha256'], 'after': row['after_sha256']}}
            or step.get('scoped_compatibility_amendment') != {'path': PROOF, 'sha256': PROOF_SHA}
            or step.get('spl_reader_smoke') != {'path': READER_PROOF, 'sha256': READER_SHA}
            or step.get('spl_standalone_verification') != {'path': STANDALONE_PROOF, 'sha256': STANDALONE_SHA}
            or step.get('native_presentation_change_scope') != 'supplementary_SPL_source_wrappers_and_attribution_wrapping_only'
            or step.get('native_presentation_code_touched') is not True
            or step.get('new_source_viewer_files_added') is not True
            or step.get('existing_reporting_guides_retained') is not True
            or any(step.get(key) is not False for key in ['native_decoder_mesh_CT_renderer_code_touched',
                    'clinical_approval', 'fine_anatomical_approval', 'reopens_or_extends_any_review'])):
        raise ValueError('SPL UI refresh leaves its exact scope')
    before_spl_bytes('web/app.js', (ROOT / 'web/app.js').read_bytes())
    for path, expected in step['guarded_paths_sha256'].items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('SPL wrapper refresh changes guarded earlier native code')
    raw = (ROOT / READER_PROOF).read_bytes()
    standalone_raw = (ROOT / STANDALONE_PROOF).read_bytes()
    if sha(raw) != READER_SHA or sha(standalone_raw) != STANDALONE_SHA:
        raise ValueError('SPL reader evidence changed')
    proof, standalone = json.loads(raw), json.loads(standalone_raw)
    expected_cases = {(width, identifier, where) for width in [390, 1440]
                      for identifier in ['ra.brain-anatomy', 'ra.mri-dementia', 'ra.mri-epilepsy']
                      for where in ['Images and MRI sources', '3D anatomy and original source context', 'lesson', 'walkthrough']}
    cases = proof.get('cases', [])
    if (proof.get('allPassed') is not True or proof.get('errors') != [] or 'failure' in proof
            or len(cases) != 24 or {(r['width'], r['investigation'], r['where']) for r in cases} != expected_cases
            or any(row.get('gpuMeshes') != 24 or len(row.get('pixels', [])) != 12 for row in cases)
            or sum(p['pixels'] for row in cases for p in row['pixels']) != 20987904
            or standalone.get('allPassed') is not True or standalone.get('errors') != []
            or len(standalone.get('pixels', [])) != 264
            or sum(row['pixels'] for row in standalone['pixels']) != 19238912):
        raise ValueError('SPL reader coverage differs from the verified source/entry-point scope')
    expected_auth = ['index.html', 'viewer.js', 'manifest.json', 'T1.bin.gz', 'labels.bin.gz', 'label-17.mesh.gz']
    if proof.get('authentication') != [{'asset': name, 'status': 401} for name in expected_auth]:
        raise ValueError('SPL reader access-gate evidence differs')
    for name, expected in proof['sourcePins'].items():
        if sha((ROOT / 'web/anatomy/spl-nac-limbic' / name).read_bytes()) != expected:
            raise ValueError('Current SPL viewer no longer matches reader evidence')
    if proof['sourcePins'] != standalone['sourcePins']:
        raise ValueError('Standalone and actual reader source identities differ')
    if sha((ROOT / 'data/radiology/spl-limbic-reference.json').read_bytes()) != proof['registrySHA256']:
        raise ValueError('Current SPL registry differs from reader evidence')
    shell = (ROOT / 'web/index.html').read_text()
    scripts = re.findall(r'<script src="/app/([\w-]+\.js)(?:\?[^"<>]*)?"></script>', shell)
    styles = re.findall(r'<link rel="stylesheet" href="/app/([\w-]+\.css)(?:\?[^"<>]*)?">', shell)
    startup = b"'use strict';\n" + b'\n;\n'.join((ROOT / 'web' / name).read_bytes() for name in scripts)
    stylesheet = b'\n'.join((ROOT / 'web' / name).read_bytes() for name in styles)
    if (sha(startup) != proof['startupSHA256'] or len(startup) != proof['startupBytes']
            or sha(stylesheet) != proof['stylesheetSHA256'] or len(stylesheet) != proof['stylesheetBytes']):
        raise ValueError('Current reader startup differs from the tested source')
    manifest = json.loads((ROOT / 'web/anatomy/spl-nac-limbic/manifest.json').read_text())
    sources = {row['file']: row for row in [*manifest['volumes'].values(), manifest['labelVolume'],
                                           *manifest['meshes'], *manifest['labelMeshes']]}
    if set(proof['payloads']) != set(sources) or len(sources) != 27:
        raise ValueError('SPL reader payload coverage differs')
    for name, observed in proof['payloads'].items():
        expected = sources[name]
        allowed = {'decoded': (expected['decodedSHA256'], expected['byteLength']),
                   'gzip': (expected['gzipSHA256'], expected['gzipBytes'])}
        if (observed['status'] != 200 or observed.get('representation') not in allowed
                or (observed['sha256'], observed['bytes']) != allowed[observed['representation']]):
            raise ValueError('SPL actual delivered source identity differs')
        if observed['representation'] == 'gzip':
            packed = (ROOT / 'web/anatomy/spl-nac-limbic' / name).read_bytes()
            decoded = gzip.decompress(packed)
            if sha(packed) != observed['sha256'] or sha(decoded) != expected['decodedSHA256'] or len(decoded) != expected['byteLength']:
                raise ValueError('SPL observed gzip does not recover its original source arrays')
    return proof
