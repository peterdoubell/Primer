"""Published processed pituitary source case, explicitly using retained supplied sforms."""
from functools import lru_cache
from pathlib import Path
import gzip,hashlib,json,os

ROOT=Path(__file__).resolve().parents[1]
ATLAS='pituitary-pandit-case1'
IDENTIFIER='pandit-pituitary-case1-processed-reference'
PREFIX='/app/anatomy/'+ATLAS+'/'
REGISTRY=ROOT/'data/radiology/pituitary-case1-reference.json'
REGISTRY_SHA256='fa81881c36d3e2597c02ab690aab2efe049f7ca09d16623fafc624facc1de4f2'
BINDINGS=['ra.mri-sella']
FLAGS=('clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved')
HOST='ja2lsnp9uca4bivw.public.blob.vercel-storage.com'
BLOB_PREFIX='https://'+HOST+'/radiology-native/pituitary-pandit-v1/case-1/'
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def regular(path,missing=False):
    if any(p.is_symlink()for p in [path,*path.parents]if p==ROOT or ROOT in p.parents)or(path.exists()and not path.is_file()):raise ValueError('Pituitary source resource must be a regular file')
    if not missing and not path.is_file():raise ValueError('Pituitary source resource missing')

@lru_cache(maxsize=1)
def registry():
    regular(REGISTRY);raw=REGISTRY.read_bytes()
    if sha(raw)!=REGISTRY_SHA256:raise ValueError('Pituitary source registry identity differs')
    data=json.loads(raw)
    if (data['schema_version']!=1 or data['bindings']!=BINDINGS or data['source_dataset_doi']!='10.6084/m9.figshare.27894084.v1'or data['source_file_id']!=50793273 or
            data['blob_store_id']!='store_JA2lsNp9UCA4bivw'or data['blob_host']!=HOST or data['blob_prefix']!=BLOB_PREFIX or
            len(data['files'])!=9 or len(data['virtual_metadata'])!=3 or len(data['payloads'])!=84 or len(data['originals'])!=4 or data['remote_delivery_verified']is not True or
            any(data[k]is not False for k in ['clinicalApproval','completeReportingCoverage','wholeGoalComplete'])):raise ValueError('Pituitary source scope differs')
    for group,kind in [('payloads','runtime'),('originals','originals')]:
        for asset,row in data[group].items():
            name=asset.rsplit('/',1)[-1]
            if row['url']!=BLOB_PREFIX+kind+'/'+row['sha256']+'/'+name or type(row['bytes'])is not int or row['bytes']<=0:raise ValueError('Pituitary immutable source address differs')
    return data

@lru_cache(maxsize=3)
def metadata_bytes(asset):
    row=registry()['virtual_metadata'][asset]
    names={'plane-package/manifest.json':'manifest','plane-package/view-config.json':'view-config','provided-plane-viewer/model-metadata.json':'model-metadata'}
    if row['path']!='data/radiology/pituitary-case1-'+names[asset]+'.json.gz':raise ValueError('Pituitary metadata address differs')
    path=ROOT/row['path'];regular(path);packed=path.read_bytes()
    if len(packed)!=row['bytes']or sha(packed)!=row['sha256']:raise ValueError('Pituitary metadata transport differs')
    raw=gzip.decompress(packed)
    if len(raw)!=row['decodedBytes']or sha(raw)!=row['decodedSHA256']:raise ValueError('Pituitary metadata decoded identity differs')
    return raw

def validate_file(asset):
    data=registry()
    if asset not in data['files']:raise ValueError('Unknown pituitary source resource')
    path=ROOT/'web/anatomy'/ATLAS/asset;regular(path,missing=asset in data['virtual_metadata'])
    raw=metadata_bytes(asset)if asset in data['virtual_metadata']else path.read_bytes();row=data['files'][asset]
    if len(raw)!=row['bytes']or sha(raw)!=row['sha256']:raise ValueError('Pituitary source file identity differs')
    return path

@lru_cache(maxsize=84)
def local_payload(asset):
    row=registry()['payloads'][asset]
    if os.environ.get('VERCEL'):return None
    name=asset.rsplit('/',1)[-1];folder='plane-package/payloads/'if asset.startswith('plane-package/payloads/')else 'source-models/'
    expected='.research/pituitary-case-source-20261101/'+folder+name
    if row['local_cache']!=expected:raise ValueError('Pituitary local cache address differs')
    path=ROOT/expected;regular(path,missing=True)
    if not path.is_file():return None
    raw=path.read_bytes()
    if len(raw)!=row['bytes']or sha(raw)!=row['sha256']:raise ValueError('Pituitary cached payload differs')
    return path

@lru_cache(maxsize=1)
def references():
    data=registry()
    for asset in data['files']:validate_file(asset)
    manifest=json.loads(metadata_bytes('plane-package/manifest.json'));config=json.loads(metadata_bytes('plane-package/view-config.json'));models=json.loads(metadata_bytes('provided-plane-viewer/model-metadata.json'))
    if (manifest['sourceDatasetDOI']!=data['source_dataset_doi']or manifest['sourceCaseId']!='1'or len(manifest['packs'])!=82 or set(manifest['volumes'])!={'T1CE','T2','tumourGland','carotids'}or
            manifest['planePayloadsPreserveAllProvidedSourceSamples']is not True or any(manifest[k]is not False for k in ['storedPlanesAreAnatomicalReslices','sourceImagesAreAcquisitionNative','sourceHeadersChanged','clinicalApproval','completeReportingCoverage','wholeGoalComplete'])):raise ValueError('Pituitary provided-plane source meaning differs')
    if (config['manifestSHA256']!=sha(metadata_bytes('plane-package/manifest.json'))or config['annotationQformDiscrepancyMm']!=22.5 or config['coordinateConflictResolved']is not False or config['sourceCoordinatesUseProvidedSform']is not True or config['clinicalApproval']is not False or config['currentPatientRegistration']is not False):raise ValueError('Pituitary source frame choice differs')
    members=0
    for key,volume in manifest['volumes'].items():
        if volume['shape']!=[499,404,342]or volume['providedVoxelSizeMm']!=[.5,.5,.5]or volume['acquisitionNative']is not False or volume['sourceSamplesResampledByPrimer']is not False or volume['dtype']!=('|u1'if key=='carotids'else'<f4'):raise ValueError('Pituitary provided sample grid differs')
        for axis in range(3):
            rows=volume['planes'][str(axis)]
            if [r['sourceIndex']for r in rows]!=list(range(volume['shape'][axis])):raise ValueError('Pituitary source planes missing')
            for row in rows:
                pack=manifest['packs'][row['pack']];runtime=data['payloads']['plane-package/payloads/'+row['pack']]
                if runtime['bytes']!=pack['bytes']or runtime['sha256']!=pack['sha256']or row['sourceFixedAxis']!=axis or row['offset']<0 or row['compressedBytes']<=0 or row['offset']+row['compressedBytes']>pack['bytes']:raise ValueError('Pituitary source range differs')
                members+=1
    if members!=4980 or len(models['models'])!=2 or models['registrationConflictResolved']is not False or models['clinicalApproval']is not False:raise ValueError('Pituitary source annotation scope differs')
    for row in models['models']:
        payload=data['payloads']['source-models/'+row['file']]
        if payload['sha256']!=row['gzipSHA256']or row['sourceCoordinatesFitted']is not False or row['sourceSmoothingOrRepairAppliedByPrimer']is not False or row['biologicalWallsResolved']is not False:raise ValueError('Pituitary source-mask geometry meaning differs')
    item=data['inspector'];grain=item['source_grain']
    if (item['id']!=IDENTIFIER or item['bound_source_ids']!=[IDENTIFIER]or item['src']!=PREFIX+'provided-plane-viewer/index.html'or item['manifest_url']!=PREFIX+'plane-package/manifest.json'or
            item['sha256']!=data['files']['provided-plane-viewer/index.html']['sha256']or item['manifest_sha256']!=data['files']['plane-package/manifest.json']['sha256']or
            any(item.get(k)is not False for k in FLAGS)or grain['subject_count']!=1 or grain['acquisition_native']is not False or grain['source_header_conflict_resolved']is not False or grain['annotation_qform_displacement_mm']!=22.5):raise ValueError('Pituitary source inspector identity or approval differs')
    return {identifier:[item]for identifier in BINDINGS}


async def remote_range(asset,start,end):
    """Relay an exact bounded public source range without forwarding credentials."""
    import httpx
    data=registry();row=data['payloads'].get(asset,data['originals'].get(asset))
    if row is None or not 0<=start<=end<row['bytes'] or end-start+1>2*1024*1024:raise ValueError('Invalid source range')
    try:
        async with httpx.AsyncClient(timeout=45,follow_redirects=False,trust_env=False)as client:
            async with client.stream('GET',row['url'],headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'})as response:
                if response.status_code!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{row["bytes"]}':raise ValueError('Remote source range differs')
                chunks=[];size=0
                async for chunk in response.aiter_raw():
                    size+=len(chunk)
                    if size>end-start+1:raise ValueError('Remote source range exceeds declared length')
                    chunks.append(chunk)
                if size!=end-start+1:raise ValueError('Remote source range is incomplete')
                return b''.join(chunks)
    except httpx.HTTPError as error:
        raise OSError('Remote source range unavailable')from error
