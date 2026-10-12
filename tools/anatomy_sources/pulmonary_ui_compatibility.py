"""Exact bounded pulmonary UI bridge; native data/earlier approvals do not advance."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DELTA='docs/pulmonary-nodule-integration-review-20261011/bounded-app-source-only-delta.json'
DELTA_SHA='7ab2a9eb1fe06acd5407a05f738e8fddba9f64221e72c669c955e78e94edb76f'
BEFORE='d77de3b299fc8af358e6c5fd2c785b22f3a8f19aa89f27a713d40be7c22b11a0'
AFTER='7e67a08f5a87983957418daf855069293ad6079c5375304c0dee83e1132029dc'
REFRESH_ID='2026-10-11-pulmonary-source-only-mounting'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def restore_previous_app(app=None):
    raw=(ROOT/DELTA).read_bytes()
    if sha(raw)!=DELTA_SHA:raise ValueError('Pulmonary UI compatibility evidence changed')
    proof=json.loads(raw)
    if (proof['before_app_sha256']!=BEFORE or proof['after_app_sha256']!=AFTER
        or {x['function'] for x in proof['changed_functions']}!={'sourceNativeInspector','renderRadiologyDesk','renderReportWalkthrough'}
        or len(proof['changed_functions'])!=3
        or proof['app_bytes_outside_changed_functions_identical'] is not True
        or any(proof[k] is not False for k in ['clinical_approval','fine_anatomical_approval','extends_any_historical_approval'])):
        raise ValueError('Pulmonary UI bridge leaves its exact reviewed scope')
    app=(ROOT/'web/app.js').read_text() if app is None else app
    if sha(app.encode())!=AFTER:raise ValueError('Unreviewed pulmonary shared-app change')
    for change in proof['changed_functions']:
        if app.count(change['after'])!=1:raise ValueError('Pulmonary UI bridge lacks its exact changed function')
        app=app.replace(change['after'],change['before'],1)
    if sha(app.encode())!=BEFORE:raise ValueError('Pulmonary UI bridge changes unreviewed shared-app bytes')
    for path,digest in proof['guarded_paths_sha256'].items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Pulmonary UI bridge changes guarded native source')
    for record in [proof['native_reader_smoke'],*proof['uterine_browser_checks']]:
        if sha((ROOT/record['path']).read_bytes())!=record['sha256']:raise ValueError('Pulmonary UI compatibility reader evidence changed')
    return app


def validate_refresh(step):
    if (step.get('id')!=REFRESH_ID or step.get('files')!={'web/app.js':{'before':BEFORE,'after':AFTER}}
        or step.get('native_presentation_code_touched') is not True
        or step.get('native_presentation_change_scope')!='pulmonary_source_only_mounting'
        or step.get('native_decoder_mesh_CT_renderer_code_touched') is not False
        or step.get('scoped_compatibility_amendment')!={'path':DELTA,'sha256':DELTA_SHA}
        or any(step.get(k) is not False for k in ['clinical_approval','fine_anatomical_approval','reopens_or_extends_any_review'])):
        raise ValueError('Pulmonary UI refresh leaves its exact reviewed scope')
    restore_previous_app()
    proof=json.loads((ROOT/DELTA).read_bytes())
    if step['guarded_paths_sha256']!=proof['guarded_paths_sha256']:
        raise ValueError('Pulmonary UI refresh changes guarded native source')
    return proof
