"""Exact offline view of the added CT/lobe source; no anatomical approval extension."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/thoracic-basal-context-review-s0028/integration/runtime-inverse.json'
PROOF_SHA='90919ee79909cc12a0d9f8abb708a487db1f04603f456bfc4da9eec422d1fa8c'


def reviewed():
    raw=(ROOT/PROOF).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PROOF_SHA:raise ValueError('Basal source inverse evidence changed')
    proof=json.loads(raw)
    if proof['clinical_approval'] is not False or proof['extends_historical_approval'] is not False:raise ValueError('Basal source inverse cannot extend approval')
    return proof


def before_basal_bytes(path,raw,allow_older=False):
    from tools.physics_wave_runtime_compatibility import before_wave_bytes
    raw=before_wave_bytes(path,raw,allow_older=True)
    row=reviewed()['files'].get(path)
    if row is None or hashlib.sha256(raw).hexdigest()==row['before_sha256']:return raw
    if hashlib.sha256(raw).hexdigest()!=row['after_sha256']:
        if allow_older:return raw
        raise ValueError('Unreviewed lung source change')
    lines=raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        a,b=change['start'],change['end']
        if ''.join(lines[a:b])!=change['after']:raise ValueError('Basal source inverse literal differs')
        lines[a:b]=change['before'].splitlines(keepends=True)
    result=''.join(lines).encode()
    if hashlib.sha256(result).hexdigest()!=row['before_sha256']:raise ValueError('Basal source inverse changes unrelated bytes')
    return result


def validate_refresh(step):
    row=reviewed()['files']['web/app.js']
    if (step.get('id')!='2026-10-14-thoracic-basal-source' or step.get('files')!={'web/app.js':{'before':row['before_sha256'],'after':row['after_sha256']}} or step.get('scoped_compatibility_amendment')!={'path':PROOF,'sha256':PROOF_SHA} or step.get('native_presentation_change_scope')!='thoracic_CT_basal_context_wrapper_only' or step.get('native_presentation_code_touched') is not True or step.get('native_decoder_mesh_CT_renderer_code_touched') is not False or any(step.get(k) is not False for k in ['clinical_approval','fine_anatomical_approval','reopens_or_extends_any_review'])):raise ValueError('Basal source UI refresh leaves its scope')
    before_basal_bytes('web/app.js',(ROOT/'web/app.js').read_bytes())
    for path,digest in step['guarded_paths_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Basal source changes guarded native code')
    record=step['basal_source_reader_smoke'];raw=(ROOT/record['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=record['sha256']:raise ValueError('Basal source reader evidence changed')
    proof=json.loads(raw)
    if len(proof['rows'])!=4 or {(r['route'],r['width']) for r in proof['rows']}!={(r,w) for r in ['reporting','lesson'] for w in [1440,390]} or len(proof['bodies'])!=21 or any(r['errors'] for r in proof['rows']) or proof['clinical_approval'] is not False:raise ValueError('Basal source reader scope differs')
    return proof
