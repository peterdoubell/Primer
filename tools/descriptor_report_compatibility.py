"""Bounded source view; descriptor UI changes do not extend historical approvals."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/descriptor-reporting-release-20261023/runtime-inverse.json'
PROOF_SHA='ba930365a6ed28c3912f0e96d9a0d429f1e9eb8ccba650b47c5a359f149363c7'
PATHS=frozenset({'primer/reporting_bridge.py','web/app.js','web/radiology-structured.js','web/radiology-structured.css'})

def reviewed():
    source=(ROOT/PROOF).read_bytes()
    if hashlib.sha256(source).hexdigest()!=PROOF_SHA:raise ValueError('Descriptor report proof changed')
    proof=json.loads(source)
    if (set(proof['files'])!=PATHS or proof['scope']!='descriptor_reporting_ui_and_bridge_only'
            or proof['base_commit']!='81a44fa2d51f5b18ce50904120aaa7439a1aafdc'
            or len(proof['files']['web/app.js']['changes'])!=2
            or any(proof[key] is not False for key in ('clinical_approval','extends_historical_approval','canonical_lesson_data_changed'))):
        raise ValueError('Descriptor proof scope changed')
    return proof


def before_descriptor_bytes(path,raw,allow_older=False):
    if str(path) not in PATHS:return raw
    proof=reviewed()
    row=proof['files'][str(path)]
    if hashlib.sha256(raw).hexdigest()==row['before_sha256']:return raw
    if hashlib.sha256(raw).hexdigest()!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed descriptor report change')
    lines=raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('Descriptor source delta changed')
        lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
    restored=''.join(lines).encode()
    if hashlib.sha256(restored).hexdigest()!=row['before_sha256']:raise ValueError('Descriptor source baseline changed')
    return restored


def validate_refresh(step):
    """Advance only the two recorded report-mount/default-tab app changes.

    The standalone report controls and bridge are also byte-bound by the inverse.
    Source files, native renderer/decoder files and historical approval receipts
    stay at their existing hashes. This is not a clinical or anatomy approval.
    """
    from tools.structured_reporting_runtime_compatibility import reviewed as structured_reviewed
    proof=reviewed()
    prior=structured_reviewed()
    row=proof['files']['web/app.js']
    if (step.get('id')!='2026-10-23-descriptor-reporting'
            or step.get('files')!={'web/app.js': {'before': row['before_sha256'], 'after': row['after_sha256']}}
            or step.get('native_presentation_change_scope')!='report_controls_and_initial_report_tab_only'
            or step.get('scoped_compatibility_amendment')!={'path': PROOF, 'sha256': PROOF_SHA}
            or step.get('guarded_paths_sha256')!=prior['guarded_paths_sha256']
            or any(step.get(key) is not False for key in ('clinical_approval','fine_anatomical_approval',
                'reopens_or_extends_any_review','native_presentation_code_touched',
                'native_decoder_mesh_CT_renderer_code_touched','canonical_lesson_data_changed',
                'new_reporting_workflow_validated_by_this_inverse'))):
        raise ValueError('Descriptor reporting refresh leaves its exact scope')
    for path,row in proof['files'].items():
        raw=(ROOT/path).read_bytes()
        if (hashlib.sha256(raw).hexdigest()!=row['after_sha256']
                or hashlib.sha256(before_descriptor_bytes(path,raw)).hexdigest()!=row['before_sha256']):
            raise ValueError('Descriptor reporting current runtime differs')
    for path,expected in {**prior['guarded_paths_sha256'], **prior['canonical_contract_files_sha256']}.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:
            raise ValueError('Descriptor reporting refresh changes a guarded source file')
    return proof
