"""Exact historical view before grouped SPL source anatomy; no approval waiver."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PROOF='docs/spl-reporting-source-review-20261016/integration/runtime-inverse.json'
PROOF_SHA256='27e9cc90b3a290e3e76f18c2877e8e5accfd630f89f34c6b03903b8cd3e96830'
PATHS=frozenset({'web/app.js','primer/server.py','primer/source_native_inspectors.py','vercel.json','docs/radiology-fidelity-scope.json'})
def sha(raw):return hashlib.sha256(raw).hexdigest()
def reviewed():
    raw=(ROOT/PROOF).read_bytes()
    if sha(raw)!=PROOF_SHA256:raise ValueError('SPL reporting inverse evidence changed')
    data=json.loads(raw)
    if (set(data['files'])!=PATHS or data['base_commit']!='56b2e0246294f2396a7fc5d86b5359ea3c355cd5' or data['bindings']!=['ra.brain-anatomy']
            or data['atlas']!='spl-nac-reporting' or data['source_inspector_addition']['id']!='spl-nac-reporting-native-reference'
            or data['extends_historical_approval'] is not False or data['new_source_or_reader_validated_by_this_inverse'] is not False):raise ValueError('SPL reporting inverse leaves exact scope')
    return data

def before_reporting_bytes(path,raw,allow_older=False):
    from tools.spine_cardiology_runtime_compatibility import before_reference_bytes
    raw = before_reference_bytes(path, raw, allow_older=True)
    path=str(path)
    if path not in PATHS:return raw
    row=reviewed()['files'][path]
    if sha(raw)==row['before_sha256']:return raw
    if sha(raw)!=row['after_sha256']:
        if allow_older:return raw # The earlier consumer retains its own exact identity guard.
        raise ValueError('Unreviewed SPL reporting byte change')
    lines=raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']])!=change['after']:raise ValueError('SPL reporting literal differs')
        lines[change['start']:change['end']]=change['before'].splitlines(keepends=True)
    restored=''.join(lines).encode()
    if sha(restored)!=row['before_sha256']:raise ValueError('SPL reporting inverse changes unrelated bytes')
    return restored

def before_reporting_reference_fields(identifier,fields):
    from tools.holiatlas_runtime_compatibility import before_holiatlas_reference_fields
    fields = before_holiatlas_reference_fields(identifier, fields)
    if identifier!='ra.brain-anatomy':return fields
    result=copy.deepcopy(fields);addition=reviewed()['source_inspector_addition'];items=result.get('source_native_inspectors',[])
    matches=[item for item in items if item.get('id')==addition['id']]
    if matches:
        if matches!=[addition]:raise ValueError('Unreviewed SPL reporting inspector change')
        items.remove(matches[0])
    return result


def validate_refresh(step):
    """Bind this exact parent-wrapper change to its current reader observations."""
    import re
    proof=reviewed();row=proof['files']['web/app.js']
    if (step.get('id')!='2026-10-16-spl-reporting-relationships' or step.get('files')!={'web/app.js':{'before':row['before_sha256'],'after':row['after_sha256']}}
            or step.get('native_presentation_code_touched') is not True
            or step.get('native_presentation_change_scope')!='grouped_SPL_source_wrappers_only'
            or step.get('native_decoder_mesh_CT_renderer_code_touched') is not False
            or any(step.get(k) is not False for k in ['clinical_approval','fine_anatomical_approval','reopens_or_extends_any_review'])
            or step.get('scoped_compatibility_amendment')!={'path':PROOF,'sha256':PROOF_SHA256}):raise ValueError('SPL reporting UI refresh leaves exact scope')
    from tools.spine_cardiology_runtime_compatibility import before_reference_bytes
    if sha(before_reference_bytes('web/app.js', (ROOT/'web/app.js').read_bytes()))!=row['after_sha256']:raise ValueError('Current reporting wrapper differs')
    def receipt(field):
        reference=step[field];raw=(ROOT/reference['path']).read_bytes()
        if sha(raw)!=reference['sha256']:raise ValueError('SPL reporting reader receipt changed')
        return json.loads(raw)
    reader=receipt('reporting_reader');standalone=receipt('reporting_standalone');preservation=receipt('existing_SPL_reader_preservation')
    if preservation.get('allPassed') is not True or preservation.get('errors')!=[] or len(preservation.get('cases',[]))!=2 or any(r.get('gpuMeshes')!=24 for r in preservation['cases']) or preservation['startupSHA256']!=reader['startupSHA256']:raise ValueError('Current original SPL preservation scope differs')
    from tools.spl_unmarked_runtime_compatibility import before_unmarked_bytes
    for case in preservation['cases']:
        for name,pin in case['sourcePins'].items():
            if sha(before_unmarked_bytes('web/anatomy/spl-nac-limbic/'+name,(ROOT/'web/anatomy/spl-nac-limbic'/name).read_bytes()))!=pin:raise ValueError('Original SPL preservation source changed')
    if (reader.get('allPassed') is not True or reader.get('errors')!=[] or reader.get('productionVerified') is not False
            or len(reader.get('cases',[]))!=8 or standalone.get('everyClassHasSelectedOverlayInBothContrastsAndThreePlanes') is not True or standalone.get('allPassed') is not True or standalone.get('errors')!=[]
            or len(standalone.get('gpu',[]))!=2 or any(len(r['meshes'])!=217 for r in standalone['gpu'])):raise ValueError('SPL reporting verification scope differs')
    for evidence in [reader,standalone]:
        for name,pin in evidence['sourcePins'].items():
            if sha((ROOT/'web/anatomy/spl-nac-reporting'/name).read_bytes())!=pin:raise ValueError('SPL reporting viewer changed')
    if reader['registrySHA256']!=sha((ROOT/'data/radiology/spl-reporting-reference.json').read_bytes()):raise ValueError('SPL reporting registry differs')
    shell=before_reference_bytes('web/index.html', (ROOT/'web/index.html').read_bytes(), allow_older=True).decode();scripts=re.findall(r'<script src="/app/([\w-]+\.js)(?:\?[^"<>]*)?"></script>',shell)
    startup=b"'use strict';\n"+b'\n;\n'.join(before_reference_bytes('web/' + name, (ROOT/'web'/name).read_bytes(), allow_older=True) for name in scripts)
    if sha(startup)!=reader['startupSHA256'] or len(startup)!=reader['startupBytes']:raise ValueError('SPL current reader startup differs')
    for path,pin in step['guarded_paths_sha256'].items():
        if sha((ROOT/path).read_bytes())!=pin:raise ValueError('SPL guarded native file changed')
    return reader
