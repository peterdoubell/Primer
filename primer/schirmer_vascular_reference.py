"""Pinned vascular study-template reference with figure-derived region names."""
from functools import lru_cache
from pathlib import Path
import gzip,hashlib,json,os,re
ROOT=Path(__file__).resolve().parents[1]
ATLAS='schirmer-vascular'
IDENTIFIER='schirmer-vascular-template-reference'
PREFIX='/app/anatomy/'+ATLAS+'/'
REGISTRY=ROOT/'data/radiology/schirmer-vascular-reference.json'
REGISTRY_SHA256 = '945b5f2a1dc2922e77dc00a8264e3b40cf2251786eda62e4fe7ee19ae0ee5437'
AUTHORED=frozenset({'index.html','viewer.js','viewer.css','schematic.js','config.json','manifest.json','labels.json','hierarchy.json','semantic-mapping.json','ATTRIBUTION.txt','LICENSE.txt'})
FLAGS=('clinical_approval','fine_anatomical_approval','current_patient_registration','normal_anatomical_atlas_approval','complete_reporting_anatomy_approved')
NAMES={2:'Right ACA',4:'Right MCA',6:'Right PCA',8:'Right Pons/Medulla',10:'Right Cerebellum',12:'Left ACA',14:'Left MCA',16:'Left PCA',18:'Left Pons/Medulla',19:None,20:'Left Cerebellum'}
SOURCE_HASHES={'mni_vascular_territories.nii.gz':'780e3f5194c8ade355cc965c90076b872cb24a43226991da3210927aba7e7a1f','caa_t1_in_mni_template_smooth.nii.gz':'3658328d55646173fde001de7645b848361d7ca1924fb3d2a5e088dd08e4378c','caa_t2_in_mni_template_smooth.nii.gz':'11fdeb2ce2c12e5400275fc6965e4a36275ed7187a903dbda41d7379dbef54fb','caa_flair_in_mni_template_smooth.nii.gz':'e1281c640814592f8f54fd366c121c9492e271f50c6259a731c4d3b3719475e4'}
AFFINE=[[-1,0,0,90],[0,1,0,-126],[0,0,1,-72],[0,0,0,1]]
def sha(raw):return hashlib.sha256(raw).hexdigest()
@lru_cache(maxsize=1)
def registry():
 if any(p.is_symlink()for p in [REGISTRY,*REGISTRY.parents]if p==ROOT or ROOT in p.parents):raise ValueError('Vascular registry cannot use a symlink')
 raw=REGISTRY.read_bytes()
 if sha(raw)!=REGISTRY_SHA256:raise ValueError('Vascular template registry changed')
 d=json.loads(raw);packs={f'{v}-axis-{a}-part-{p}.pack'for v in ['labels','T1','T2','FLAIR']for a in range(3)for p in ([0]if v=='labels'else[0,1])};meshes={f'territory-{n}.{suffix}.gz'for n in NAMES for suffix in ['mesh','faces']}
 if (d.get('schema_version')!=1 or d.get('atlas')!=ATLAS or d.get('source_record')!='https://zenodo.org/records/3379848'
     or d.get('bindings')!={k:[IDENTIFIER]for k in ['ra.brain-anatomy','ra.acute-stroke']} or set(d.get('inspectors',{}))!={IDENTIFIER}
     or set(d.get('files',{}))!=AUTHORED|packs|meshes|{'publication-figure1.webp'}
     or any(d.get(k)is not False for k in FLAGS)
     or [d.get(k)for k in ['source_classes','named_source_classes','uninterpreted_values','components26','triangles','planes']]!=[11,10,[19],15,754024,2328]):raise ValueError('Vascular template source scope differs')
 if {r['file']:r['sha256']for r in d['source_inputs']}!=SOURCE_HASHES:raise ValueError('Vascular template original source identities differ')
 for name,row in d['files'].items():
  if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*',name)or type(row.get('bytes'))is not int or row['bytes']<=0 or not re.fullmatch(r'[0-9a-f]{64}',row.get('sha256','')):raise ValueError('Invalid vascular source asset identity')
 return d
@lru_cache(maxsize=3)
def metadata_bytes(name):
 if name not in {'manifest.json','labels.json','hierarchy.json'}:raise ValueError('Unknown vascular metadata')
 row=registry()['runtime_metadata'][name];expected='data/radiology/schirmer-vascular-'+name+'.gz'
 if row['path']!=expected:raise ValueError('Vascular metadata leaves its fixed path')
 p=ROOT/expected
 if any(q.is_symlink()for q in [p,*p.parents]if q==ROOT or ROOT in q.parents)or not p.is_file():raise ValueError('Vascular metadata must be a regular file')
 packed=p.read_bytes()
 if len(packed)!=row['bytes']or sha(packed)!=row['sha256']:raise ValueError('Vascular metadata transport changed')
 raw=gzip.decompress(packed)
 if len(raw)!=row['decoded_bytes']or sha(raw)!=row['decoded_sha256']or registry()['files'][name]!={'bytes':len(raw),'sha256':sha(raw)}:raise ValueError('Vascular metadata decoded bytes changed')
 return raw
@lru_cache(maxsize=256)
def _check_file(path,size,mtime,expected):
 raw=Path(path).read_bytes()
 if len(raw)!=size or sha(raw)!=expected:raise ValueError('Vascular source asset bytes changed')
def validate_file(name):
 if name not in registry()['files']:raise ValueError('Unknown vascular source asset')
 p=ROOT/'web/anatomy'/ATLAS/name
 if any(q.is_symlink()for q in [p,*p.parents]if q==ROOT or ROOT in q.parents):raise ValueError('Vascular source asset cannot use a symlink')
 if p.exists():
  if not p.is_file():raise ValueError('Vascular source asset must be a regular file')
  st=p.stat();row=registry()['files'][name]
  if st.st_size!=row['bytes']:raise ValueError('Vascular source asset length changed')
  _check_file(str(p),st.st_size,st.st_mtime_ns,row['sha256'])
 elif name in {'manifest.json','labels.json','hierarchy.json'}and os.environ.get('VERCEL'):metadata_bytes(name)
 elif name in AUTHORED or not os.environ.get('VERCEL'):raise ValueError('Vascular source asset missing')
 return p
@lru_cache(maxsize=1)
def references():
 d=registry()
 for name in d['files']:validate_file(name)
 for row in d['source_inputs']:
  p=ROOT/'web/anatomy'/ATLAS/'originals'/row['file']
  if any(q.is_symlink()for q in [p,*p.parents]if q==ROOT or ROOT in q.parents):raise ValueError('Vascular original cannot use a symlink')
  if p.is_file():
   st=p.stat()
   if st.st_size!=row['bytes']:raise ValueError('Vascular original length changed')
   _check_file(str(p),st.st_size,st.st_mtime_ns,row['sha256'])
  elif not os.environ.get('VERCEL'):raise ValueError('Vascular original source missing')
 m=json.loads(metadata_bytes('manifest.json'));labels=json.loads(metadata_bytes('labels.json'));hierarchy=json.loads(metadata_bytes('hierarchy.json'));config=json.loads(validate_file('config.json').read_bytes());meaning=json.loads(validate_file('semantic-mapping.json').read_bytes())
 if m.get('schemaVersion')!=1 or m.get('sourceRecord')!=3379848 or m.get('clinicalApproval')is not False or m.get('currentPatientRegistration')is not False or m.get('normalPopulationAtlasApproval')is not False or m.get('sourceGridIsAcquisitionResolution')is not False or set(m.get('volumes',{}))!={'labels','T1','T2','FLAIR'}or len(m.get('packs',{}))!=21 or m.get('planeCount')!=2328:raise ValueError('Vascular source interpretation differs')
 if m.get('sourceCohort')!={'subjects':16,'CAA':12,'controls':4,'processedAndSmoothed':True}:raise ValueError('Vascular source cohort differs')
 if labels.get('sourceRecord')!=3379848 or labels.get('clinicalApproval')is not False or labels.get('currentPatientRegistration')is not False or labels.get('normalPopulationAtlasApproval')is not False or labels.get('namedSourceClasses')!=10 or labels.get('uninterpretedSourceClasses')!=[19]or labels.get('components26')!=15:raise ValueError('Vascular label interpretation differs')
 if hierarchy.get('sourceRecord')!=3379848 or hierarchy.get('clinicalApproval')is not False or hierarchy.get('levels')!={}:raise ValueError('Unreviewed vascular hierarchy')
 for name in ['manifest.json','labels.json','hierarchy.json']:
  if config[name.removesuffix('.json')+'SHA256']!=d['files'][name]['sha256']:raise ValueError('Vascular viewer metadata identity differs')
 for name,row in m['packs'].items():
  if d['files'][name]!={'bytes':row['bytes'],'sha256':row['sha256']}:raise ValueError('Vascular pack identity differs')
 count=0;used=set()
 for name,v in m['volumes'].items():
  if v.get('shape')!=[182,218,182]or v.get('voxelToSourceWorld')!=AFFINE or v.get('sourceSHA256')!=SOURCE_HASHES.get(v.get('sourceFile'))or v.get('encodedDatatype')!=('<u2'if name=='labels'else'<f8'):raise ValueError('Vascular source grid or datatype differs')
  for axis in range(3):
   rows=v['planes'][str(axis)];others=[i for i in range(3)if i!=axis];shape=[v['shape'][i]for i in others]
   if len(rows)!=v['shape'][axis]:raise ValueError('Vascular source plane omitted')
   for i,row in enumerate(rows):
    if row['index']!=i or row['sourceAxes']!=others or row['shape']!=shape or row['byteLength']!=shape[0]*shape[1]*(2 if name=='labels'else 8)or row['offset']<0 or row['offset']+row['gzipBytes']>m['packs'][row['file']]['bytes']:raise ValueError('Vascular plane address differs')
    used.add(row['file']);count+=1
 if count!=2328 or used!=set(m['packs']):raise ValueError('Vascular range coverage differs')
 rows=labels['sourceClasses']
 if {r['code']:r['publishedFigureLegendName']for r in rows}!=NAMES or len(rows)!=11 or sum(r['triangles']for r in rows)!=754024 or sum(len(r['components26'])for r in rows)!=15:raise ValueError('Vascular region name or geometry inventory differs')
 for row in rows:
  if row.get('clinicalApproval')is not False or row.get('individualFineStructureCoverageApproved')is not False or row.get('numericMeaningProvenance')!=('uninterpreted'if row['code']==19 else'publication-figure-derived'):raise ValueError('Vascular source region approval changed')
  for payload in [row['mesh'],row['facesPayload']]:
   if d['files'][payload['file']]!={'bytes':payload['gzipBytes'],'sha256':payload['gzipSHA256']}:raise ValueError('Vascular region payload differs')
  if sum(c['voxels']for c in row['components26'])!=row['voxels']:raise ValueError('Vascular components omitted')
  for c in row['components26']:
   i,j,k=c['focusSourceIJK']
   if any(type(n)is not int for n in [i,j,k])or not(0<=i<182 and 0<=j<218 and 0<=k<182)or c['focusSourceWorld']!=[90-i,j-126,k-72]:raise ValueError('Vascular component focus differs')
  if row['code']==19 and(row['voxels']!=1 or row['components26'][0]['focusSourceIJK']!=[142,73,25]):raise ValueError('Vascular singleton was changed')
 if (meaning.get('sourceRecord')!=3379848 or meaning.get('stableInteriorMatches')!=69328 or meaning.get('stableInteriorBackground')!=0 or meaning.get('stableInteriorWrongNamedClass')!=0 or meaning.get('negativeControls')!=48 or meaning.get('fullFigureBoundaryIdentityClaimed')is not False or meaning.get('clinicalApproval')is not False or meaning.get('fineAnatomicalApproval')is not False or meaning.get('currentPatientRegistration')is not False or meaning.get('completeReportingAnatomyApproved')is not False or {r['code']:r['publishedLegendName']for r in meaning['rows']}!=NAMES or meaning.get('figureSHA256')!=d['files']['publication-figure1.webp']['sha256']):raise ValueError('Vascular semantic evidence differs')
 item=d['inspectors'][IDENTIFIER]
 if item.get('src')!=PREFIX+'index.html'or item.get('manifest_url')!=PREFIX+'manifest.json'or item.get('sha256')!=d['files']['index.html']['sha256']or item.get('manifest_sha256')!=d['files']['manifest.json']['sha256']or item.get('bound_source_ids')!=[IDENTIFIER]or any(item.get(k)is not False for k in FLAGS):raise ValueError('Vascular source inspector differs')
 if item.get('source_url')!='https://zenodo.org/records/3379848'or item.get('publication_url')!='https://doi.org/10.3389/fneur.2019.00208'or item.get('license')!='CC BY 4.0'or item.get('license_url')!='https://creativecommons.org/licenses/by/4.0/'or item.get('source_grant')!={'publisher_explicitly_applies_license_to_data':True,'terms_url':'https://creativecommons.org/licenses/by/4.0/legalcode','attribution_url':PREFIX+'ATTRIBUTION.txt','marked_derived_version':True}:raise ValueError('Vascular source provenance differs')
 if item['source_grain']!={'kind':'processed older-adult study template','subject_count':16,'CAA_subject_count':12,'control_count':4,'supplied_grid_mm':[1,1,1],'supplied_grid_is_acquisition_resolution':False,'present_source_values':11,'figure_named_source_values':10,'uninterpreted_source_values':[19],'pons_medulla_combined':True,'numeric_name_mapping_derived_from_figure':True}:raise ValueError('Vascular source grain differs')
 return {key:[item]for key in d['bindings']}
