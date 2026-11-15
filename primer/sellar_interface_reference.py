"""Source-exact sellar interface references; no biological approval transfer."""
from functools import lru_cache
from pathlib import Path
import gzip
import hashlib
import json
import os

ROOT=Path(__file__).resolve().parents[1]
ATLAS='spl-sellar-interfaces'
IDENTIFIER='spl-sellar-source-interfaces-reference'
PREFIX='/app/anatomy/'+ATLAS+'/'
REGISTRY=ROOT/'data/radiology/sellar-interface-reference.json'
REGISTRY_SHA256='1e1b11b772d6b20b9cbcddba518789bec00d0c0d69101d399f414a0b32c785f0'
BINDINGS=['ra.brain-anatomy','ra.mri-sella']
FLAGS=('clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved')
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def regular(path,missing=False):
    if any(p.is_symlink()for p in [path,*path.parents]if p==ROOT or ROOT in p.parents)or(path.exists()and not path.is_file()):
        raise ValueError('Sellar reference resource must be a regular file')
    if not missing and not path.is_file():raise ValueError('Sellar reference resource missing')

@lru_cache(maxsize=1)
def registry():
    regular(REGISTRY);raw=REGISTRY.read_bytes()
    if sha(raw)!=REGISTRY_SHA256:raise ValueError('Sellar interface registry changed')
    data=json.loads(raw)
    if (data['schema_version']!=1 or data['bindings']!=BINDINGS or len(data['files'])!=120 or
            set(data['virtual_metadata'])!={'viewer/manifest.json','viewer/mri-source.json','viewer/context-source.json'}or
            any(data[k]is not False for k in ['clinicalApproval','completeReportingCoverage','wholeGoalComplete'])):
        raise ValueError('Sellar interface source scope differs')
    return data

@lru_cache(maxsize=3)
def metadata_bytes(asset):
    row=registry()['virtual_metadata'][asset]
    expected='data/radiology/sellar-interface-'+asset.removeprefix('viewer/').removesuffix('.json')+'.json.gz'
    if row['path']!=expected:raise ValueError('Sellar metadata address differs')
    path=ROOT/row['path'];regular(path);packed=path.read_bytes()
    if len(packed)!=row['bytes']or sha(packed)!=row['sha256']:raise ValueError('Sellar metadata transport differs')
    raw=gzip.decompress(packed)
    if len(raw)!=row['decodedBytes']or sha(raw)!=row['decodedSHA256']:raise ValueError('Sellar decoded metadata differs')
    return raw

def validate_file(asset):
    data=registry()
    if asset not in data['files']:raise ValueError('Unknown sellar interface resource')
    path=ROOT/'web/anatomy'/ATLAS/asset
    static=asset.endswith(('.svg','.mesh.gz'))
    regular(path,missing=asset in data['virtual_metadata']or static and bool(os.environ.get('VERCEL')))
    if asset in data['virtual_metadata']:raw=metadata_bytes(asset)
    elif path.is_file():raw=path.read_bytes()
    else:return path
    row=data['files'][asset]
    if len(raw)!=row['bytes']or sha(raw)!=row['sha256']:raise ValueError('Sellar interface file changed')
    return path

@lru_cache(maxsize=1)
def references():
    from . import spl_limbic_reference as native,spl_reporting_reference as reporting,spl_additional_reference as additional
    for source in [native,reporting,additional]:source.references()
    data=registry()
    for asset in data['files']:validate_file(asset)
    manifest=json.loads(metadata_bytes('viewer/manifest.json'));mri=json.loads(metadata_bytes('viewer/mri-source.json'));context=json.loads(metadata_bytes('viewer/context-source.json'))
    if (manifest['sourceCommit']!=data['source_commit']or manifest['contactFaces']!=652 or len(manifest['groups'])!=36 or
            manifest['oppositeNamedSideFacesRetained']!=23 or manifest['meshes']['contacts']['triangles']!=1304 or
            any(manifest[k]is not False for k in ['clinicalApproval','anatomicalBoundaryValidated','completeReportingCoverage','sourceSamplesChanged','gapsBridged'])):
        raise ValueError('Sellar source interface meaning differs')
    original=json.loads(native.validate_file('manifest.json').read_bytes())
    if mri['volumes']!=original['volumes']or mri['labelVolume']!=original['labelVolume']:raise ValueError('Sellar source MRI changed')
    if len(mri['pairs'])!=36 or {(r['firstCode'],r['secondCode'])for r in mri['pairs']}!={(g['firstCode'],g['secondCode'])for g in manifest['groups']}:raise ValueError('Sellar MRI anchors differ')
    sources={native.ATLAS:original,reporting.ATLAS:json.loads(reporting.manifest_bytes()),additional.ATLAS:json.loads(additional.manifest_bytes())}
    if len(context['meshes'])!=21 or len({r['code']for r in context['meshes']})!=21 or context['sourceCoordinatesFitted']is not False or context['clinicalApproval']is not False:raise ValueError('Sellar source context changed')
    for atlas,row in context['sourceManifests'].items():
        raw=native.validate_file('manifest.json').read_bytes()if atlas==native.ATLAS else reporting.manifest_bytes()if atlas==reporting.ATLAS else additional.manifest_bytes()if atlas==additional.ATLAS else b''
        if row['file']!='/app/anatomy/'+atlas+'/manifest.json'or sha(raw)!=row['sha256']:raise ValueError('Sellar parent identity differs')
    for row in context['meshes']:
        atlas=row['sourceAtlas'];expected=next(r for r in sources[atlas]['labelMeshes']if r['code']==row['code'])
        if {k:v for k,v in row.items()if k!='sourceAtlas'}!=expected:raise ValueError('Sellar source context geometry differs')
    mesh=manifest['meshes']['contacts'];file=data['files']['viewer/'+mesh['file']]
    if file!={'bytes':mesh['compressedBytes'],'sha256':mesh['compressedSHA256']}:raise ValueError('Sellar contact transport differs')
    item=data['inspector']
    if (item['id']!=IDENTIFIER or item['src']!=PREFIX+'viewer/index.html'or item['manifest_url']!=PREFIX+'viewer/manifest.json'or
            item['bound_source_ids']!=[IDENTIFIER]or item['sha256']!=data['files']['viewer/index.html']['sha256']or
            item['manifest_sha256']!=data['files']['viewer/manifest.json']['sha256']or any(item.get(flag)is not False for flag in FLAGS)):
        raise ValueError('Sellar interface inspector identity or approval differs')
    return {identifier:[item]for identifier in BINDINGS}
