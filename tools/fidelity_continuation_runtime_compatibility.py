"""Exact pre-continuation views; new science and anatomy need their own evidence."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = '495aeb17c711ace603f7ad196033d2741e23ff32'
PROOF = 'docs/fidelity-continuation-20261025/runtime-inverse.json'
PROOF_SHA256 = '590b05187dd13e5120e527154d7666afea831fdf111135da29efb1fdd3cec65b'
LEDGER_PATH = 'data/radiology/ui-presentation-refreshes.json'
LEDGER_PROOF = 'docs/fidelity-continuation-20261025/ledger-inverse.json'
LEDGER_PROOF_SHA256 = '2c94e634ddd05e3762016464c78309c146449ec31325a61da29312e35c479c74'
REFRESH_ID = '2026-10-25-integrals-energy-and-atlas-hierarchy'
SCOPE = 'integral_energy_labs_and_exact_holiatlas_hierarchy_only'
IDENTIFIER = 'holiatlas-source-template-reference'
PATHS = frozenset({
    'data/curriculum/03-physics.json', 'data/radiology/holiatlas-reference.json',
    'docs/radiology-fidelity-scope.json', 'primer/holiatlas_reference.py',
    'primer/server.py', 'tools/anatomy_sources/build_holiatlas_registry.py', 'vercel.json',
    'web/anatomy/holiatlas/ATTRIBUTION.txt', 'web/anatomy/holiatlas/config.json',
    'web/anatomy/holiatlas/index.html', 'web/anatomy/holiatlas/viewer.css',
    'web/anatomy/holiatlas/viewer.js', 'web/index.html', 'web/lesson-models.js',
})
READER_PATHS = frozenset({
    'docs/integral-calculus-fidelity-review-20261025/reader/proof.json',
    'docs/energy-momentum-fidelity-review-20261025/reader/proof.json',
    'docs/holiatlas-hierarchy-review-20261025/reader/proof.json',
})
FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'extends_historical_approval',
         'new_science_or_anatomy_validated_by_this_inverse', 'whole_goal_complete')
SOURCE_FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'current_patient_registration',
                'normal_anatomical_atlas_approval', 'complete_reporting_anatomy_approved')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Fidelity continuation inverse evidence changed')
    proof = json.loads(raw)
    replacement = proof['source_inspector_replacement']
    if (proof['base_commit'] != BASE_COMMIT or proof['scope'] != SCOPE
            or set(proof['files']) != PATHS
            or set(proof['current_reader_evidence']) != READER_PATHS
            or proof['bindings'] != ['math.4.int-calc', 'phys.3.energy-work', 'ra.brain-anatomy']
            or set(replacement) != {'before', 'after'}
            or replacement['before']['id'] != IDENTIFIER or replacement['after']['id'] != IDENTIFIER
            or any(item.get(key) is not False for item in replacement.values() for key in SOURCE_FLAGS)
            or len(proof['added_files_sha256']) != 164
            or any(proof[key] is not False for key in FLAGS)):
        raise ValueError('Fidelity continuation inverse leaves exact scope')
    return proof


def reviewed_ledger():
    raw = (ROOT / LEDGER_PROOF).read_bytes()
    if sha(raw) != LEDGER_PROOF_SHA256:
        raise ValueError('Fidelity continuation ledger evidence changed')
    proof = json.loads(raw)
    if (proof['base_commit'] != BASE_COMMIT or proof['path'] != LEDGER_PATH
            or proof['scope'] != 'one_exact_fidelity_continuation_ledger_append_only'
            or proof['source_refresh_id'] != REFRESH_ID
            or proof['runtime_inverse_sha256'] != PROOF_SHA256
            or any(proof[key] is not False for key in FLAGS)):
        raise ValueError('Fidelity continuation ledger inverse leaves exact scope')
    return proof


def before_continuation_bytes(path, raw, allow_older=False):
    """Restore only the exact recorded bytes; older callers retain their own guards."""
    from tools.current_labs_runtime_compatibility import before_current_labs_bytes
    raw = before_current_labs_bytes(path, raw, allow_older=True)
    path = str(path)
    if path not in PATHS and path != LEDGER_PATH:
        return raw
    row = reviewed_ledger() if path == LEDGER_PATH else reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw
        raise ValueError('Unreviewed fidelity continuation byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('Fidelity continuation inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Fidelity continuation inverse changes unrelated baseline bytes')
    return restored


def before_continuation_reference_fields(identifier, fields):
    from tools.atlas_schematic_runtime_compatibility import before_atlas_schematic_reference_fields
    fields = before_atlas_schematic_reference_fields(identifier, fields, allow_older=True)
    if identifier != 'ra.brain-anatomy':
        return fields
    result = copy.deepcopy(fields)
    replacement = reviewed()['source_inspector_replacement']
    items = result.get('source_native_inspectors', [])
    matches = [item for item in items if item.get('id') == IDENTIFIER]
    if not matches:
        return result
    if matches == [replacement['after']]:
        items[items.index(matches[0])] = copy.deepcopy(replacement['before'])
    elif matches != [replacement['before']]:
        raise ValueError('Unreviewed fidelity continuation source descriptor change')
    return result


def validate_current():
    """Check current files and separate current reader proofs; grant no approval."""
    from tools.current_labs_runtime_compatibility import before_current_labs_bytes
    proof = reviewed()
    for path, row in proof['files'].items():
        raw = before_current_labs_bytes(path, (ROOT / path).read_bytes(), allow_older=True)
        if sha(raw) != row['after_sha256'] or sha(before_continuation_bytes(path, raw)) != row['before_sha256']:
            raise ValueError('Fidelity continuation current runtime differs')
    for path, expected in proof['added_files_sha256'].items():
        if sha(before_current_labs_bytes(path, (ROOT / path).read_bytes(), allow_older=True)) != expected:
            raise ValueError('Fidelity continuation added runtime differs')
    readers = {}
    for path, expected in proof['current_reader_evidence'].items():
        raw = (ROOT / path).read_bytes()
        if sha(raw) != expected:
            raise ValueError('Fidelity continuation current reader evidence changed')
        reader = json.loads(raw)
        if (reader.get('allPassed') is not True or reader.get('productionVerified') is not False
                or reader.get('errors') != [] or reader.get('clinicalApproval', False) is not False
                or reader.get('wholeGoalComplete', False) is not False or not reader.get('sourceSHA256')):
            raise ValueError('Fidelity continuation current reader proof is incomplete')
        for source_path, digest in reader['sourceSHA256'].items():
            if sha(before_current_labs_bytes(source_path, (ROOT / source_path).read_bytes(), allow_older=True)) != digest:
                raise ValueError('Fidelity continuation current reader source differs: ' + source_path)
        readers[path] = reader
    return readers


def validate_refresh(step):
    proof = reviewed()
    changes = {path: {'before': row['before_sha256'], 'after': row['after_sha256']}
               for path, row in proof['files'].items()}
    if (step.get('id') != REFRESH_ID or step.get('files') != {}
            or step.get('native_runtime_files') != changes
            or step.get('native_presentation_code_touched') is not True
            or step.get('native_decoder_mesh_CT_renderer_code_touched') is not True
            or step.get('native_presentation_change_scope') != SCOPE
            or step.get('canonical_lesson_data_changed') is not True
            or step.get('guarded_paths_sha256') != proof['guarded_paths_sha256']
            or step.get('scoped_compatibility_amendment') != {'path': PROOF, 'sha256': PROOF_SHA256}
            or any(step.get(key) is not False for key in ('clinical_approval', 'fine_anatomical_approval',
                                                         'reopens_or_extends_any_review'))):
        raise ValueError('Fidelity continuation refresh leaves exact scope')
    for path, digest in step['guarded_paths_sha256'].items():
        if sha((ROOT / path).read_bytes()) != digest:
            raise ValueError('Fidelity continuation changed a guarded source file')
    return validate_current()
