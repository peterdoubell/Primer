#!/usr/bin/env python3
"""Preserve original MRI composites, source case boundaries and caption conflicts."""
import hashlib,json,xml.etree.ElementTree as E
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_radiology_fidelity import digest
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path('/Users/peter/Documents/ChatGPT/Primer/.research/esophagus-clinical-source-review')
INV='ra.esophagus';PREFIX='open-esophagus-pmc11227487-fig';URL='https://pmc.ncbi.nlm.nih.gov/articles/PMC11227487/'
ROLES={1:{'MRI':list('bcghlmqrvwx'),'CT':list('afkpu'),'Endoscopy':list('dinsy'),'Ultrasound':list('ejot')},2:{'MRI':list('cd'),'CT':list('ab'),'Endoscopy':['e'],'Radiography':['f']},3:{'MRI':list('cdefgh'),'CT':list('ab'),'Endoscopy':['i'],'Ultrasound':['j'],'Histology':['k']},4:{'MRI':list('bcdef'),'CT':['a'],'Endoscopy':['g'],'Ultrasound':['h'],'Histology':['i']},5:{'MRI':list('bcdef'),'CT':['a'],'Endoscopy':['g'],'Ultrasound':['h'],'Histology':list('ij')},6:{'MRI':list('bcd'),'CT':['a'],'Endoscopy':['e'],'Ultrasound':['f'],'Histology':['g']}}
CASES={2:(62,'male'),3:(67,'female'),4:(63,'male'),5:(64,'male'),6:(68,'female')}
CONFLICTS={1:'Original caption repeats d for final endoscopic ultrasound and capital I for i; image labels show t and i. T4 panels u/v and w/x/y are explicitly two cases; do not merge them.',2:'Caption refers to an orange fistula arrow not visible in the original f panel; do not add or infer an annotation.',5:'Caption identifies the second histology as h, but original inset is labelled j; h is ultrasound. The conflicting histology subtype/marker assignment remains unverified.',6:'Caption describes green histology arrow, while original g appears black; no colour/annotation replacement.'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package():
    proof_path=ROOT/'docs/esophagus-mri-source-review/original-source-review.json';proof=json.loads(proof_path.read_text())
    assert proof['original_article_grant']=='CC BY 4.0' and len(proof['figures'])==6
    tree=E.parse(SOURCE/'PMC11227487.1.xml');authors=[' '.join(filter(None,[n.findtext('given-names'),n.findtext('surname')])) for n in tree.findall('.//article-meta/contrib-group/contrib/name')]
    rows=[];assets=[]
    for f in proof['figures']:
        n=f['figure_number'];ident=PREFIX+str(n);raw=(SOURCE/'PMC11227487/original-PDF-masters'/f['source_master_filename']).read_bytes();assert sha(raw)==f['source_master_sha256']
        with Image.open(SOURCE/'PMC11227487/original-PDF-masters'/f['source_master_filename']) as im:assert sha(im.tobytes())==f['decoded_pixel_sha256'] and im.size==(f['width'],f['height'])
        role=ROLES[n];types={p:k for k,panels in role.items() for p in panels};population={'life_stage':'unknown','age_not_supplied':True,'sex_not_supplied':True} if n==1 else {'life_stage':'adult','age_years':CASES[n][0],'sex':CASES[n][1]}
        groups={'source_T1a':list('abcde'),'source_T1b':list('fghij'),'source_T2':list('klmno'),'source_T3':list('pqrst'),'source_T4_aortic_case':list('uv'),'different_source_T4_bronchial_case':list('wxy')} if n==1 else {'explicit_source_case':list(types)}
        context={'setting':'in_vivo','laterality':'not_applicable','population':population,'extent':'local','depicted_state':'source_esophageal_mass_or_fistula','selected_panels':role['MRI'],'panel_types':types,'panel_states':{p:'source_esophageal_mass_or_fistula' for p in types},'source_case_groups':groups,'source_panels_are_different_patients':n==1,'source_different_figures_assumed_same_patient':False,'source_native_registration_verified':False,'source_full_microanatomical_coverage_approved':False,'source_static_views_supply_timed_transit_or_pressure':False,'source_labels_are_current_patient_histology_or_cause':False,'source_caption_panel_discrepancy':n in CONFLICTS}
        limit='Complete original publication composite; MRI is primary, CT/endoscopy/ultrasound/histology remain distinct source panels. Source stage, biopsy, ADC and response labels apply only to the published case; no independent current diagnosis, calibrated ADC threshold, acquisition timing, registered native3D or complete microscopic anatomy is established. '+CONFLICTS.get(n,'')
        path=f'web/reference-media/radiology-open/esophagus-pmc11227487-fig{n}.png';(ROOT/path).write_bytes(raw)
        attribution=', '.join(authors)+'. '+tree.findtext('.//article-title')+'. DOI '+proof['doi']+'. Figure '+str(n)+'. CC BY 4.0. Complete original decoded PDF pixels and ICC preserved; no crop, enhancement, resize or relabelling. No endorsement implied.'
        row={'id':ident,'kind':'clinical-image','modality':'MRI','figure_number':n,'src':'/app/'+path.removeprefix('web/'),'sha256':sha(raw),'width':f['width'],'height':f['height'],'source_url':URL,'figure_url':URL+'#Fig'+str(n),'asset_source_url':'https://pmc-oa-opendata.s3.amazonaws.com/PMC11227487.1/PMC11227487.1.pdf','clinical_panels':role['MRI'],'source_context':context,'image_state':context['depicted_state'],'caption':'Original source Figure '+str(n)+': '+f['source_caption_full'].split('.')[0]+'.','alt':'Complete original esophageal MRI source Figure '+str(n)+'.','limits':limit,'source_caption_full':f['source_caption_full'],'structures_visible':['Source-local muscular wall and tumour/adjacent tissue interfaces; complete native boundaries unapproved'],'license':'CC BY 4.0','license_url':proof['license_url'],'attribution':attribution,'rights_reviewed_on':'2026-10-08','rights_review':'Original XML CC BY4 grant, no figure-specific exception, numbered original PDF page and full master reviewed.','ancillary_panels':[{'kind':k,'panels':v,'structures_visible':['Separate original '+k+' source panels'],'limits':'Source case context only; no current diagnosis or registered anatomy inferred.'} for k,v in role.items() if k!='MRI']}
        catalog._validate_source_panel_roles(row);rows.append(row)
        assets.append({'id':ident,'kind':'clinical_image','name':'Original esophageal MRI source Figure '+str(n),'local_path':path,'sha256':sha(raw),'modality':'MRI','investigation_ids':[INV],'structure_ids':[],'requirement_coverage':{},'source_context':context,'source':{'url':URL,'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],'license':{'name':'CC BY 4.0','url':proof['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_path.read_bytes()),'attribution':attribution,'reviewed_at':'2026-10-08'}},'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':f['decoded_pixel_sha256'],'source_PDF_object':f['source_PDF_object'],'source_PDF_page':f['source_PDF_page'],'source_ICC_sha256':f['source_ICC_sha256'],'highest_resolution_acquired_master_verified':True},'anatomical_review':{'status':'pending','reason':'Published selected views do not independently validate every reported structure or matched native3D.'}})
    p=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(p.read_text());data[INV]=[r for r in data[INV] if not r['id'].startswith(PREFIX)]+rows;p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    p=ROOT/'data/radiology/reporting-steps/chest.json';text=p.read_text();start=text.index('{',text.index('"'+INV+'"'));node,end=json.JSONDecoder().raw_decode(text,start)
    for index,s in enumerate(node['steps']):
        s['images']=[i for i in s.get('images',[]) if not i.startswith(PREFIX)]
        s['images'] += [PREFIX+str(n) for n in (range(1,7) if index==1 else [2] if index==4 else [])]
    p.write_text(text[:start]+json.dumps(node,indent=2).replace('\n','\n    ')+text[end:])
    for v in vars(catalog).values():
        if callable(getattr(v,'cache_clear',None)):v.cache_clear()
    ref=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference'];p=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(p.read_text());next(r for r in data['investigations'] if r['investigation_id']==INV)['source_contract_sha256']=digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']});p.write_text(json.dumps(data,indent=2)+'\n')
    print('Six original MRI composites integrated with distinct ancillary roles and caption conflicts')
if __name__=='__main__':package()
