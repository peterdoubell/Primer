"""Grouped SPL source anatomy, retaining exact categorical cells and native grids."""
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ATLAS='spl-nac-reporting'
IDENTIFIER='spl-nac-reporting-native-reference'
PREFIX='/app/anatomy/'+ATLAS+'/'
REGISTRY=ROOT/'data/radiology/spl-reporting-reference.json'
REGISTRY_SHA256='beba53ebfe78a7a947397d57701d3a66f564a4d24a7bde78ee715fcf62702b31'
AUTHORED=frozenset({'index.html','viewer.js','viewer.css','manifest.json'})
BINDINGS=frozenset({'ra.brain-anatomy'})
FLAGS=('clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved')
SOURCE_COMMIT='bec24db25aad5f7600e2df3becfb1f883e61ff56'

def sha(raw):return hashlib.sha256(raw).hexdigest()
@lru_cache(maxsize=1)
def registry():
    raw=REGISTRY.read_bytes()
    if sha(raw)!=REGISTRY_SHA256:raise ValueError('SPL reporting registry changed')
    data=json.loads(raw)
    if (data.get('schema_version')!=1 or data.get('source_commit')!=SOURCE_COMMIT
            or data.get('bindings')!={key:[IDENTIFIER] for key in BINDINGS}
            or set(data.get('inspectors',{}))!={IDENTIFIER} or len(data.get('files',{}))!=418
            or not AUTHORED<=set(data['files'])
            or data.get('source_class_count')!=217 or data.get('additional_source_class_count')!=205
            or data.get('generated_boundary_payload_sets')!=207 or data.get('shared_boundary_payload_sets')!=10):
        raise ValueError('SPL reporting source scope differs')
    return data

def validate_file(asset):
    files=registry()['files']
    if asset not in files:raise ValueError('Unknown SPL reporting asset')
    file=ROOT/'web/anatomy'/ATLAS/asset
    if any(p.is_symlink() for p in [file,*file.parents]) or (file.exists() and not file.is_file()):raise ValueError('SPL reporting asset must be a regular file')
    row=files[asset]
    if file.is_file():
        raw=file.read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise ValueError('SPL reporting asset bytes changed')
    elif asset in AUTHORED or not os.environ.get('VERCEL'):raise ValueError('SPL reporting asset missing')
    return file

@lru_cache(maxsize=1)
def references():
    from . import spl_limbic_reference as shared
    shared.references()
    data=registry()
    for asset in data['files']:validate_file(asset)
    item=data['inspectors'][IDENTIFIER]
    if (item.get('id')!=IDENTIFIER or item.get('src')!=PREFIX+'index.html' or item.get('manifest_url')!=PREFIX+'manifest.json'
            or item.get('bound_source_ids')!=[IDENTIFIER] or any(item.get(flag) is not False for flag in FLAGS)
            or item.get('sha256')!=data['files']['index.html']['sha256'] or item.get('manifest_sha256')!=data['files']['manifest.json']['sha256']
            or item.get('source_grain',{}).get('selected_label_classes')!=217 or item.get('source_grain',{}).get('subject_count')!=1
            or item.get('source_grant',{}).get('terms_url')!=shared.PREFIX+'LICENSE.txt'):
        raise ValueError('SPL reporting identity or source meaning differs')
    manifest=json.loads(validate_file('manifest.json').read_bytes())
    base=json.loads(shared.validate_file('manifest.json').read_bytes())
    if (manifest.get('sourceCommit')!=SOURCE_COMMIT or manifest.get('sourceCoordinateSystem')!='RAS'
            or manifest.get('sharedSourceManifestSHA256')!=shared.SOURCE_MANIFEST_SHA256
            or any(manifest.get(k) is not False for k in ['clinicalApproval','completeReportingAnatomyApproved','normalPopulationAtlas','currentPatientRegistration','newFittedTransforms'])
            or len(manifest.get('labels',[]))!=217 or len(manifest.get('labelMeshes',[]))!=217 or len(manifest.get('groups',[]))!=13):
        raise ValueError('SPL reporting manifest leaves reviewed scope')
    for row,expected in [(manifest['labelVolume'],base['labelVolume']),*[(v,base['volumes'][k]) for k,v in manifest['volumes'].items()]]:
        if row.get('sharedSource')!='spl-nac-limbic' or {k:v for k,v in row.items() if k!='sharedSource'}!=expected:raise ValueError('SPL shared native array descriptor differs')
    labels={row['code']:row for row in manifest['labels']}
    if len(labels)!=217 or {m['code'] for m in manifest['labelMeshes']}!=set(labels):raise ValueError('SPL reporting class identity differs')
    own=set(AUTHORED);shared_count=0
    for row in manifest['labelMeshes']:
        if (row.get('coordinateSystem')!='RAS' or row.get('positionsAlreadyRAS') is not True or row.get('sourceAffine')!=shared.IDENTITY
                or row.get('sourceLabelVoxelToRAS')!=shared.LABEL_AFFINE or row.get('allComponentsAndCavitiesRetained') is not True
                or row.get('allCellFacesExact') is not True or row.get('smoothedOrRepairedByPrimer') is not False):raise ValueError('SPL reporting boundary meaning differs')
        if row.get('sharedSource'):
            expected=next((r for r in base['labelMeshes'] if r['code']==row['code']),None)
            if row['sharedSource']!='spl-nac-limbic' or {k:v for k,v in row.items() if k!='sharedSource'}!=expected:raise ValueError('Shared boundary descriptor differs')
            shared_count+=1
        else:
            for payload in [row,row['faceProvenance']]:
                file=payload['file'];own.add(file)
                if data['files'][file]['sha256']!=payload['gzipSHA256'] or data['files'][file]['bytes']!=payload['gzipBytes']:raise ValueError('Reporting payload transport differs')
        label=labels[row['code']]
        if sum(c['sourceVoxelCount'] for c in label['components26'])!=row['sourceVoxelCount']:raise ValueError('Reporting source components differ')
    if shared_count!=10 or own!=set(data['files']):raise ValueError('SPL reporting payload inventory differs')
    for group in manifest['groups']:
        if group.get('completeReportingRequirementApproved') is not False or any(code not in labels for code in group['codes']):raise ValueError('Reporting group approval or identity differs')
    return {key:[item] for key in BINDINGS}
