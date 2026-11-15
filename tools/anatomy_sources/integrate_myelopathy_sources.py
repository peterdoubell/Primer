#!/usr/bin/env python3
"""Integrate independently reviewed myelopathy figures without granting anatomical coverage.

Only four radiology data files and this source folder are written. All unrelated
JSON value tokens are retained exactly; reviewed source/proposal/media hashes
are checked before any shared mutation. Schema normalization preserves the
original facts separately and cannot promote clinical or fine anatomy approval.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_msk_fidelity import inspect_binding,requirements_for,validate_reporting_snapshots,audit
from tools.check_radiology_fidelity import digest

INV='ra.mri-myelopathy'
FOLDER=Path('docs/myelopathy-published-source-review-20261011')
PROOF_SHA='ef78550db4d9aebf9cf3471f3467227b9ec626ea098229dbbb5734408695640a'
INDEPENDENT_PATH=Path('docs/myelopathy-independent-source-review-20261011.json')
INDEPENDENT_SHA='ac775f60d6011bca10099a6607da02e4d99ea9489e9868ff0cf3948c60cba1b1'
PREFIXES=('open-myelopathy-moghaddam2018-','open-myelopathy-mogad2025-')
DATA_PATHS=[Path('data/radiology/'+x) for x in ['radiology-open-images.json','radiology-asset-evidence.json','non-msk-structure-requirements.json','reporting-steps/neuroradiology.json']]
STEP_IMAGES={0:['open-myelopathy-moghaddam2018-fig23'],1:['open-myelopathy-moghaddam2018-fig4','open-myelopathy-moghaddam2018-fig5','open-myelopathy-moghaddam2018-fig6','open-myelopathy-moghaddam2018-fig7','open-myelopathy-moghaddam2018-fig9','open-myelopathy-mogad2025-fig1'],2:['open-myelopathy-moghaddam2018-fig4','open-myelopathy-moghaddam2018-fig5','open-myelopathy-moghaddam2018-fig6','open-myelopathy-moghaddam2018-fig11','open-myelopathy-moghaddam2018-fig22','open-myelopathy-moghaddam2018-fig24','open-myelopathy-mogad2025-fig1'],3:['open-myelopathy-moghaddam2018-fig5','open-myelopathy-moghaddam2018-fig6','open-myelopathy-moghaddam2018-fig9','open-myelopathy-moghaddam2018-fig10','open-myelopathy-moghaddam2018-fig12','open-myelopathy-moghaddam2018-fig13','open-myelopathy-moghaddam2018-fig15','open-myelopathy-moghaddam2018-fig16','open-myelopathy-moghaddam2018-fig17','open-myelopathy-moghaddam2018-fig21','open-myelopathy-moghaddam2018-fig23'],4:['open-myelopathy-moghaddam2018-fig6','open-myelopathy-moghaddam2018-fig7','open-myelopathy-moghaddam2018-fig8','open-myelopathy-moghaddam2018-fig14','open-myelopathy-moghaddam2018-fig18','open-myelopathy-moghaddam2018-fig19','open-myelopathy-moghaddam2018-fig20']}
START_IMAGES=['open-myelopathy-moghaddam2018-fig1','open-myelopathy-moghaddam2018-fig2','open-myelopathy-moghaddam2018-fig3']
NORMAL_PROMPTS=[
 'Compression assessment [__]; actual covered levels, cause and cord/root relation [__]. Unassessed extent is not a normal finding.',
 'Cord signal and longitudinal extent [__]; actual covered levels [__]; motion/partial-volume limitations [__].',
 'Axial distribution and cross-sectional involvement [__]; each actual side/tract/horn [__]; unresolved boundaries [__].',
 'Cord calibre [__]; diagnostic contrast acquired [__]; enhancement [not acquired / unassessed / pattern: __].',
 'Perimedullary vessels, conus and actually acquired brain/orbital observations [__]; unacquired regions [__].']


def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(root,path):return json.loads((root/path).read_text())
def checked(root,path,expected):
 raw=(root/path).read_bytes()
 if sha(raw)!=expected:raise ValueError('Reviewed fingerprint differs: '+str(path))
 return json.loads(raw)

def validate_approved_sources(root=ROOT):
 root=Path(root);review=checked(root,INDEPENDENT_PATH,INDEPENDENT_SHA);proof=checked(root,FOLDER/'original-source-review.json',PROOF_SHA)
 if review.get('held_source_row_ids')!=[] or any(review.get(k) is not False for k in ['clinical_approval','fine_anatomical_approval','structure_coverage_granted','runtime_integration_approved']):raise ValueError('Independent holds or unsupported approval changed')
 if any(proof.get(k) is not False for k in ['clinical_approval','fine_anatomical_approval','requirement_coverage_granted']):raise ValueError('Source proof cannot grant anatomical coverage')
 proposals={}
 for name in ['proposed-image-rows.json','proposed-asset-evidence-rows.json','complete-requirement-draft.json']:
  path=FOLDER/name;proposals[name]=checked(root,path,review['reviewed_file_SHA256'][str(path)])
 images=proposals['proposed-image-rows.json'][INV];assets=proposals['proposed-asset-evidence-rows.json']['assets'];draft=proposals['complete-requirement-draft.json'];ids={r['id'] for r in images}
 if len(images)!=25 or len(ids)!=25 or ids!=set(review['approved_source_rows_as_frozen']) or ids!=set(review['source_pixel_preservation_verified_ids']) or {a['id'] for a in assets}!=ids:raise ValueError('Exact approved source set changed')
 total=0;media=[]
 for fig in proof['figures']:
  path=root/fig['packaged_path'];raw=path.read_bytes()
  if sha(raw)!=fig['sha256'] or len(raw)!=fig['bytes'] or not fig['original_PDF_samples_verified'] or fig['source_pixels_changed'] is not False:raise ValueError('Frozen source figure differs')
  total+=len(raw);media.append({'path':fig['packaged_path'],'sha256':sha(raw),'bytes':len(raw)})
 for article in proof['articles']:
  path=root/article['packaged_original_PDF_path'];raw=path.read_bytes()
  if sha(raw)!=article['original_PDF_sha256'] or len(raw)!=article['packaged_original_PDF_bytes'] or article['license']!='CC BY 4.0' or article['license_url']!='https://creativecommons.org/licenses/by/4.0/':raise ValueError('Original PDF or source grant changed')
  total+=len(raw);media.append({'path':article['packaged_original_PDF_path'],'sha256':sha(raw),'bytes':len(raw)})
 if len(media)!=27 or total!=8738864 or total!=proof['packaged_asset_bytes']:raise ValueError('Complete media byte bound differs')
 if len(draft['structures'])!=231 or len(requirements_for(draft))!=2422 or any(a['structure_ids'] or a['requirement_coverage'] or a['anatomical_review']['status']!='pending' for a in assets):raise ValueError('Draft scope or pending coverage changed')
 return proof,review,images,assets,draft,media

def normalized_context(original,schematic=False):
 c=copy.deepcopy(original);changes=[]
 def assign(key,value):
  old=c.get(key)
  if old!=value:c['original_'+key]=copy.deepcopy(old);c[key]=value;changes.append({'field':key,'original':old,'normalized':value})
 assign('setting',c['setting'] if c['setting'] in {'in_vivo','ex_vivo','cadaveric','mixed','conceptual'} else 'unknown')
 assign('laterality',c['laterality'] if c['laterality'] in {'left','right','bilateral'} else 'unknown')
 pop=c.get('population',{});life=pop.get('life_stage');new='immature' if life=='paediatric' else life if life in {'adult','immature','mixed'} else 'unknown'
 if life!=new:pop['original_life_stage']=life;pop['life_stage']=new;changes.append({'field':'population.life_stage','original':life,'normalized':new})
 c['source_medium']='schematic publication artwork' if schematic else 'complete published clinical composite';c['extent']='local';c['current_patient_findings']=False;c['clinical_approval']=False;c['fine_anatomical_approval']=False
 if schematic:
  # Empty typed selection fields on an unpanelled schematic would invent a
  # selection contract. Keep the original empty facts under explicit provenance.
  saved={k:c.pop(k) for k in ['panel_types','panel_states','selected_panels','clinical_panels'] if k in c}
  if saved:c['original_unpanelled_selection_fields']=saved;changes.append({'field':'unpanelled_selection_fields','original':saved,'normalized':'absent; source artwork has no panel selection'})
 else:
  types=c['panel_types'];c['original_panel_types']=copy.deepcopy(types)
  for panel,kind in list(types.items()):
   if kind=='DSA':types[panel]='Radiography';changes.append({'field':'panel_types.'+panel,'original':'DSA','normalized':'Radiography; source_subtype=Digital subtraction angiography'})
  c['source_panel_acquisition_subtypes']={p:'Digital subtraction angiography' for p,k in c['original_panel_types'].items() if k=='DSA'}
  c['selected_panels']=list(c['clinical_panels'])
  if not c['selected_panels'] or any(types[p]!='MRI' for p in c['selected_panels']):raise ValueError('Non-MRI panel cannot be selected as MRI evidence')
  c['panel_states']={p:c['depicted_state'] for p in c['selected_panels']}
 return c,changes

def normalize_rows(images,assets,proof):
 out_images=[];out_assets=[];normalizations=[];by_asset={a['id']:a for a in assets};articles={a['pmcid']:a for a in proof['articles']};facts={r['packaged_path']:r for r in proof['figures']}
 for raw in images:
  row=copy.deepcopy(raw);a=copy.deepcopy(by_asset[row['id']]);schematic=row['kind']=='anatomical-illustration';context,changes=normalized_context(row['source_context'],schematic)
  row['source_context']=context;row['kind']='schematic' if schematic else 'clinical-image';row['modality']='Schematic' if schematic else 'MRI';row['integration_status']='registered_source_example_no_anatomical_coverage';row['clinical_approval']=row['fine_anatomical_approval']=False
  row['rights_review']='Exact independent source-rights/pixels/context review '+INDEPENDENT_SHA+' approves this unchanged complete figure with CC BY 4.0. Source proof '+PROOF_SHA+'. No anatomical coverage or clinical approval.'
  fact=facts[a['local_path']];article=articles[fact['pmcid']];row['source_caption_full']=row['caption'];row['original_publication_pdf']={'src':'/app/'+article['packaged_original_PDF_path'].removeprefix('web/'),'sha256':article['original_PDF_sha256'],'bytes':article['packaged_original_PDF_bytes'],'title':article['title'],'license':'CC BY 4.0','license_url':article['license_url'],'unchanged_original':True,'rendering_context_and_profiles_preserved':True}
  row['source_context_original_proof_relation']={'evidence_path':str(FOLDER/'original-source-review.json'),'evidence_sha256':PROOF_SHA,'original_source_context_sha256':digest(raw['source_context']),'schema_normalization_only':True}
  if schematic:
   for key in ['clinical_panels','schematic_panels','ancillary_panels']:row.pop(key,None)
  else:
   row['clinical_panels']=list(context['selected_panels'])
   for ancillary in row['ancillary_panels']:
    if ancillary['kind']=='DSA':ancillary['original_source_kind']='DSA';ancillary['kind']='Radiography';ancillary['source_subtype']='Digital subtraction angiography'
    ancillary['structures_visible']=['Separate source '+ancillary.get('source_subtype',ancillary['kind'])+' observations; no MRI evidence transferred']
   a['representation_selection']={'panels':list(context['selected_panels'])}
  a['source_context']=copy.deepcopy(context);a['kind']='schematic' if schematic else 'clinical_image';a['modality']=row['modality'];a['name']=article['title']+' Figure '+str(row['figure_number']);a['source']['license']['review_status']='verified';a['source']['license']['independent_review_path']=str(INDEPENDENT_PATH);a['source']['license']['independent_review_sha256']=INDEPENDENT_SHA;a['clinical_approval']=a['fine_anatomical_approval']=False;a['structure_ids']=[];a['requirement_coverage']={};a['visual_review']={'status':'source_checked','sha256':row['sha256'],'evidence_path':str(INDEPENDENT_PATH),'evidence_sha256':INDEPENDENT_SHA,'reviewed_at':'2026-10-11','anatomical_or_clinical_approval':False};a['runtime_registered']=True
  a['source_context_original_proof_relation']=copy.deepcopy(row['source_context_original_proof_relation'])
  catalog._validate_source_panel_roles(row)
  issues=inspect_binding(a,{'modality_scope':['MRI'],'context_requirements':[]})
  if issues:raise ValueError('Normalized source context is invalid: '+row['id']+' '+str(issues))
  out_images.append(row);out_assets.append(a);normalizations.append({'id':row['id'],'original_source_context_sha256':digest(raw['source_context']),'registered_source_context_sha256':digest(context),'changes':changes,'all_original_facts_retained_in_proof_and_explicit_original_fields':True})
 return out_images,out_assets,normalizations

# Span edits preserve every unrelated JSON value token byte-for-byte.
def skip(raw,pos):
 while pos<len(raw) and raw[pos].isspace():pos+=1
 return pos
DECODER=json.JSONDecoder()
def object_members(raw,start=0):
 pos=skip(raw,start);assert raw[pos]=='{';pos=skip(raw,pos+1)
 while raw[pos]!='}':
  key,end=DECODER.raw_decode(raw,pos);pos=skip(raw,end);assert raw[pos]==':';start_value=skip(raw,pos+1);value,end=DECODER.raw_decode(raw,start_value);yield key,value,start_value,end;pos=skip(raw,end)
  if raw[pos]==',':pos=skip(raw,pos+1)
  else:assert raw[pos]=='}'
def member(raw,path):
 start=skip(raw,0)
 for key in path:
  matches=[x for x in object_members(raw,start) if x[0]==key]
  if len(matches)!=1:raise KeyError(path)
  _,value,start,end=matches[0]
 return value,start,end

def replace_member(raw,path,value):
 _,start,end=member(raw,path);return raw[:start]+json.dumps(value,indent=2,ensure_ascii=False)+raw[end:]
def add_member(raw,path,key,value):
 _,start,end=member(raw,path) if path else (json.loads(raw),skip(raw,0),DECODER.raw_decode(raw,skip(raw,0))[1]);obj=json.loads(raw[start:end]);assert key not in obj
 close=end-1;prefix=raw[:close].rstrip();addition=(',' if obj else '')+'\n  '+json.dumps(key)+': '+json.dumps(value,indent=2,ensure_ascii=False)+'\n';return prefix+addition+raw[close:]
def array_values(raw,start,end):
 pos=skip(raw,start+1)
 while raw[pos]!=']':
  value,next_pos=DECODER.raw_decode(raw,pos);yield value,raw[pos:next_pos];pos=skip(raw,next_pos)
  if raw[pos]==',':pos=skip(raw,pos+1)
  else:assert raw[pos]==']'
def upsert_array(raw,path,rows,key,predicate):
 _,start,end=member(raw,path);retained=[token for value,token in array_values(raw,start,end) if not predicate(value)];retained.extend(json.dumps(r,indent=2,ensure_ascii=False) for r in rows);return raw[:start]+'[\n    '+',\n    '.join(retained)+'\n  ]'+raw[end:]
def unrelated_token_fingerprints(raw,path,ids):
 result={}
 if path==DATA_PATHS[0]:
  for k,v,a,b in object_members(raw):
   if k!=INV:result['image_collection:'+k]=sha(raw[a:b].encode())
 elif path in [DATA_PATHS[1],DATA_PATHS[2]]:
  field='assets' if path==DATA_PATHS[1] else 'investigations';_,a,b=member(raw,[field])
  for value,token in array_values(raw,a,b):
   ident=value['id'] if field=='assets' else value['investigation_id']
   if (ident not in ids if field=='assets' else ident!=INV):result[field+':'+ident]=sha(token.encode())
  for k,v,a,b in object_members(raw):
   if k not in {field,'scope'}:result['top:'+k]=sha(raw[a:b].encode())
  if path==DATA_PATHS[2]:
   _,a,_=member(raw,['scope'])
   for k,v,c,d in object_members(raw,a):
    if k!='catalog_investigation_ids':result['scope:'+k]=sha(raw[c:d].encode())
   _,a,b=member(raw,['scope','catalog_investigation_ids'])
   for value,token in array_values(raw,a,b):
    if value!=INV:result['catalog_id:'+value]=sha(token.encode())
 else:
  for k,v,a,b in object_members(raw):
   if k!='investigations':result['top:'+k]=sha(raw[a:b].encode())
  _,a,_=member(raw,['investigations'])
  for k,v,c,d in object_members(raw,a):
   if k!=INV:result['walkthrough:'+k]=sha(raw[c:d].encode())
 return result
def clear_catalog_caches():
 for value in vars(catalog).values():
  if callable(getattr(value,'cache_clear',None)):value.cache_clear()

def normalize_inventory(draft):
 item=copy.deepcopy(draft);changes=[]
 for group in item['structures']:
  original=group.pop('context_requirements',{});group['context_instantiation_rules']=original
  # Actual side constraints are already typed in group.laterality. No shared
  # reference state or patient age is invented from advisory scope prose.
  typed={'purpose':'pathology_example'} if any(token in group['id'] for token in ['.condition.','.literal_TM_table.','.literal_RA_differential.','.literal_article_context.','.literal_Fig2.','.quiz']) else {}
  group['context_requirements']=typed;group['site_instantiation_status']='pending';group['population_and_state_instantiation_status']='pending';group['clinical_approval']=False
  original_modes=copy.deepcopy(group['modality_scope']);modes=[]
  for mode in original_modes:
   canonical='MRI' if mode.startswith(('MRI','MRA')) else 'CT' if mode.startswith(('CT','CTA')) else 'Radiography' if mode.startswith(('DSA','lateral_radiograph')) else mode
   if canonical not in {'MRI','CT','Radiography'}:raise ValueError('Unknown named modality requirement '+mode)
   if canonical not in modes:modes.append(canonical)
  group['modality_instantiation_rules']=original_modes;group['modality_scope']=modes;changes.append({'id':group['id'],'original_advisory_context':original,'typed_constraints':typed,'original_modality_phrases':original_modes,'typed_modalities':modes})
 item['original_source_draft_shared_inventory_or_evidence_mutated']=item.get('shared_inventory_or_evidence_mutated');item['shared_inventory_or_evidence_mutated']=True
 item['context_normalization_status']='typed_schema_constraints_only; original_actual_site_population_state_and_acquisition_rules_retained';item['runtime_integrated']=True;item['clinical_approval']=item['fine_anatomical_approval']=item['structure_coverage_granted']=False
 return item,changes

def integrate(root=ROOT):
 root=Path(root);proof,review,images,assets,draft,media=validate_approved_sources(root);images,assets,context_changes=normalize_rows(images,assets,proof);item,requirement_changes=normalize_inventory(draft)
 before={str(p):(root/p).read_text() for p in DATA_PATHS};outputs={};ids={r['id'] for r in images}
 raw=before[str(DATA_PATHS[0])];old=json.loads(raw);rows=[r for r in old.get(INV,[]) if r['id'] not in ids]+images
 outputs[str(DATA_PATHS[0])]=replace_member(raw,[INV],rows) if INV in old else add_member(raw,[],INV,rows)
 raw=before[str(DATA_PATHS[1])];outputs[str(DATA_PATHS[1])]=upsert_array(raw,['assets'],assets,'id',lambda a:a['id'] in ids)
 raw=before[str(DATA_PATHS[3])];node=copy.deepcopy(read(root,DATA_PATHS[3])['investigations'][INV]);node.setdefault('start',{}).update(images=START_IMAGES,module_illustrations=False);node['preset_mode']='assessment-prompts';node['clinical_approval']=node['fine_anatomical_approval']=False;node['source_example_conditions']='Published source cases are examples, never findings in the reader patient. Normal observations require actual diagnostic acquisition.'
 for i,step in enumerate(node['steps']):
  step.setdefault('original_normal_report_statement',copy.deepcopy(step.get('normal')));step['normal']={step['sections'][0]:NORMAL_PROMPTS[i]};step['images']=STEP_IMAGES[i];step['clinical_approval']=False;step['source_example_note']='Actual source case/sequence/side/timepoint only; no fine boundary or clinical approval and no unrelated mesh highlighted.';step['parts']=[]
 outputs[str(DATA_PATHS[3])]=replace_member(raw,['investigations',INV],node)
 # Register source galleries and walkthrough before computing the exact current
 # effective contract. The inventory entry is written only after that digest.
 for p in [DATA_PATHS[0],DATA_PATHS[1],DATA_PATHS[3]]:(root/p).write_text(outputs[str(p)])
 clear_catalog_caches();reference=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference'];contract={k:reference.get(k) for k in ['reporting','report_templates','walkthrough','reading']};item['source_contract_sha256']=digest(contract)
 validate_reporting_snapshots({'investigations':[item]},{INV:reference['reporting']})
 raw=before[str(DATA_PATHS[2])];raw=upsert_array(raw,['investigations'],[item],'investigation_id',lambda a:a['investigation_id']==INV);scope=json.loads(raw)['scope'];catalog_ids=scope['catalog_investigation_ids']
 if INV not in catalog_ids:raw=replace_member(raw,['scope','catalog_investigation_ids'],catalog_ids+[INV])
 outputs[str(DATA_PATHS[2])]=raw;(root/DATA_PATHS[2]).write_text(raw)
 # Recount actual obligations; empty bindings deliberately keep every one missing.
 scoped={'investigations':[item],'scope':{'catalog_investigation_ids':[INV]},'clinical_validation_status':'draft_requires_neuroradiologist_and_spinal_specialist_review'};report=audit(scoped,{'assets':assets},root,expected_catalog_ids={INV})
 if report['representation_requirements']!=7266 or report['counts']!={'verified':0,'unverified':0,'missing':7266}:raise ValueError('Integration granted unexpected anatomical coverage')
 untouched={}
 for p in DATA_PATHS:
  previous=json.loads(before[str(p)]);current=read(root,p)
  if p==DATA_PATHS[0]:left={k:v for k,v in previous.items() if k!=INV};right={k:v for k,v in current.items() if k!=INV}
  elif p==DATA_PATHS[1]:left={**previous,'assets':[a for a in previous['assets'] if a['id'] not in ids]};right={**current,'assets':[a for a in current['assets'] if a['id'] not in ids]}
  elif p==DATA_PATHS[2]:left={**previous,'investigations':[a for a in previous['investigations'] if a['investigation_id']!=INV],'scope':{**previous['scope'],'catalog_investigation_ids':[i for i in previous['scope']['catalog_investigation_ids'] if i!=INV]}};right={**current,'investigations':[a for a in current['investigations'] if a['investigation_id']!=INV],'scope':{**current['scope'],'catalog_investigation_ids':[i for i in current['scope']['catalog_investigation_ids'] if i!=INV]}}
  else:left={**previous,'investigations':{k:v for k,v in previous['investigations'].items() if k!=INV}};right={**current,'investigations':{k:v for k,v in current['investigations'].items() if k!=INV}}
  if left!=right:raise ValueError('Unrelated data changed: '+str(p))
  old_tokens=unrelated_token_fingerprints(before[str(p)],p,ids);new_tokens=unrelated_token_fingerprints((root/p).read_text(),p,ids)
  if old_tokens!=new_tokens:raise ValueError('Unrelated JSON value token changed: '+str(p))
  untouched[str(p)]={'unrelated_semantics_unchanged':True,'unrelated_semantic_sha256':digest(left),'unrelated_value_tokens_unchanged':True,'unrelated_value_token_count':len(old_tokens),'unrelated_value_token_fingerprints':old_tokens}
 receipt={'source_proof_sha256':PROOF_SHA,'independent_source_review_sha256':INDEPENDENT_SHA,'registered_ids':sorted(ids),'registered_complete_figures':25,'original_media_files':media,'original_media_bytes':8738864,'clinical_approval':False,'fine_anatomical_approval':False,'requirement_coverage_granted':False,'standalone_browser_colour_equivalence_verified':False,'source_context_normalizations':context_changes,'requirement_context_and_modality_normalizations':requirement_changes,'source_proof_relation':'Pinned source proof and proposals are unchanged. Only schema vocabulary/selection normalization and explicit contextual provenance fields are added; source pixels, ICC, PDF object intents, captions, credits and clinical facts are preserved.','current_myelopathy_source_contract_sha256':item['source_contract_sha256'],'original_source_contract_sha256':draft['source_contract_sha256'],'source_contract_changed_only_for_curated_walkthrough_images_and_assessment_prompts':True,'normal_report_conditions':'Actual diagnostic acquisitions required; unacquired enhancement and fields remain unassessed. Source examples never become reader-patient findings.','source_qualification_flags':draft['scope_review_flags'],'unrelated_data':untouched,'scoped_fidelity_counts':report['counts'],'representation_obligations':7266,'current_reference_key_images_empty':reference['key_images']==[],'root_owned_pending':(['Key-image override for inherited remote example'] if reference['key_images'] else [])+['Final reader/browser QA and shared dependency refresh'],'core_app_or_unrelated_dependency_hashes_refreshed':False}
 (root/FOLDER/'integration-receipt.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n');(root/FOLDER/'integrated-effective-reporting-contract.json').write_text(json.dumps(contract,indent=2,ensure_ascii=False)+'\n');(root/FOLDER/'integrated-focused-fidelity-audit.json').write_text(json.dumps({k:v for k,v in report.items() if k!='requirements'},indent=2)+'\n')
 print('Registered 25 complete figures, 231 groups/2422 parts/7266 missing obligations; all 27 media unchanged and no clinical/fine coverage granted. Current contract '+item['source_contract_sha256'])
 return receipt

if __name__=='__main__':integrate()
