#!/usr/bin/env python3
"""Preserve complete original breast US figures and source/ancillary device roles."""
import hashlib,json,xml.etree.ElementTree as E
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_radiology_fidelity import digest
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path('/Users/peter/Documents/ChatGPT/Primer/.research/breast-clinical-source-review')
INV='ra.ultrasound-breast';PREFIX='open-breast-us-pmc10000574-fig';URL='https://pmc.ncbi.nlm.nih.gov/articles/PMC10000574/'
ROLES={1:{'Ultrasound':['full']},2:{'Ultrasound':['full']},3:{'Ultrasound':['A','B']},4:{'Ultrasound':['full']},5:{'Ultrasound':['full']},6:{'Ultrasound':['full']},7:{'Ultrasound':['middle'],'Ultrasound-derived display':['right']},8:{'Ultrasound':['full']},9:{'Ultrasound':['B'],'Clinical photograph':['A']},10:{'Ultrasound':['B'],'Radiography':['A']},11:{'Ultrasound':['B'],'CT':['A']}}
CASES={9:'male',10:'female',11:'female'}
EXTRA={1:'Power Doppler and MV-Flow are distinct processed source modes; colour does not supply a calibrated flow measurement.',2:'Source22MHz transducer context is not independently verified effective tissue resolution or a complete duct/lobular map.',3:'Extended field-of-view is a processed source acquisition; native3D sampling, stitched-image calibration and timing are not supplied.',4:'Source strain ratio and ROI are original device output, not calibrated modulus, a universal threshold or independent histology.',5:'A published coronal3D ultrasound rendering is not a supplied native volume, complete tumour segmentation or source mesh.',6:'MicroPure is processed ultrasound; a highlighted dot does not independently establish every calcific boundary or tissue identity.',7:'Original S-Detect position icon, middle ultrasound and right/footer device-derived classification/measurements remain separate. Device segmentation and possibly-benign label are not independently verified native boundaries, current BI-RADS assessment or current diagnosis.',8:'Source submuscular implant appearance does not establish every shell/capsule layer, integrity, rupture or malignancy.',9:'Source young-male/ingrown-hair clinical context is not an independently verified age, organism, complete gland/duct map or current diagnostic cause.',10:'Source mammography and ultrasound are separate modalities. Negative source mammography does not exclude the source ultrasound/surgically established lesion; source triple-negative tissue identity is not inferred for a new patient.',11:'Source venous-phase contrast CT and targeted ultrasound are distinct acquisitions. Source right-sided/tubular carcinoma and rectal-cancer context do not supply current metastatic identity or validated native registration.'}
USES={'ra.ultrasound-breast':{n:[1,2,3] for n in range(1,12)},'ra.breast-cancer-staging':{n:[0,1] for n in [1,2,3,5,10,11]},'ra.breast-implants':{6:[4],8:[0,1],10:[4]},'ra.male-breast':{9:[0,3]}}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package():
    proof_path=ROOT/'docs/breast-US-published-source-review/original-source-review.json';proof=json.loads(proof_path.read_text())
    assert proof['original_article_grant']=='CC BY 4.0' and len(proof['figures'])==11
    tree=E.parse(SOURCE/'PMC10000574.1.xml');authors=[' '.join(filter(None,[n.findtext('given-names'),n.findtext('surname')])) for n in tree.findall('.//article-meta/contrib-group/contrib/name')]
    rows=[];assets=[]
    for f in proof['figures']:
        n=f['figure_number'];ident=PREFIX+str(n);raw=(SOURCE/'PMC10000574/original-PDF-masters'/f['source_master_filename']).read_bytes();assert sha(raw)==f['source_master_sha256']
        with Image.open(SOURCE/'PMC10000574/original-PDF-masters'/f['source_master_filename']) as im:assert sha(im.tobytes())==f['decoded_pixel_sha256'] and im.size==(f['width'],f['height'])
        role=ROLES[n];types={p:k for k,panels in role.items() for p in panels};population={'life_stage':'unknown','age_not_supplied':True,'sex_not_supplied':n not in CASES};population.update({'sex':CASES[n]} if n in CASES else {})
        if n==7:types['left']='Schematic'
        groups={'source_figure_case_identity_not_independently_verified':list(types)}
        context={'setting':'in_vivo','laterality':'right' if n==11 else 'unknown','population':population,'extent':'local','depicted_state':'source_breast_case_or_device_example','selected_panels':role['Ultrasound'],'panel_types':types,'panel_states':{p:'source_breast_case_or_device_example' for p in types},'source_case_groups':groups,'source_panels_are_different_patients':False,'source_different_figures_assumed_same_patient':False,'source_native_registration_verified':False,'source_full_microanatomical_coverage_approved':False,'source_static_views_supply_calibrated_flow_stiffness_or_native3D':False,'source_labels_are_current_patient_histology_or_cause':False,'source_device_classification_is_current_validated_assessment':False}
        limit='Complete original source figure; acquired/processed ultrasound and all ancillary roles remain distinct. Selected views do not supply every fine tissue/interface, raw volumetric registration, calibrated physiology or current histology/diagnosis. '+EXTRA[n]
        path=f'web/reference-media/radiology-open/breast-us-pmc10000574-fig{n}.png';(ROOT/path).write_bytes(raw)
        attribution=', '.join(authors)+'. '+tree.findtext('.//article-title')+'. DOI '+proof['doi']+'. Figure '+str(n)+'. CC BY 4.0. Complete original decoded PDF pixels and ICC preserved; no crop, enhancement, resize or relabelling. No endorsement implied.'
        row={'id':ident,'kind':'clinical-image','modality':'Ultrasound','figure_number':n,'src':'/app/'+path.removeprefix('web/'),'sha256':sha(raw),'width':f['width'],'height':f['height'],'source_url':URL,'figure_url':URL+'#Fig'+str(n),'asset_source_url':'https://pmc-oa-opendata.s3.amazonaws.com/PMC10000574.1/PMC10000574.1.pdf','clinical_panels':role['Ultrasound'],'source_context':context,'image_state':context['depicted_state'],'caption':'Original source Figure '+str(n)+': '+f['source_caption_full'].split('.')[0]+'.','alt':'Complete original breast ultrasound source Figure '+str(n)+'.','limits':limit,'source_caption_full':f['source_caption_full'],'structures_visible':['Source-local breast/lesion and adjacent tissue interfaces; complete native boundaries unapproved'],'license':'CC BY 4.0','license_url':proof['license_url'],'attribution':attribution,'rights_reviewed_on':'2026-10-08','rights_review':'Original XML CC BY4 grant, no figure-specific exception, numbered original PDF page and full master reviewed.','ancillary_panels':[{'kind':k,'panels':v,'structures_visible':['Separate original '+k+' source panels'],'limits':'Source case context only; no current diagnosis or registered anatomy inferred.'} for k,v in role.items() if k!='Ultrasound']}
        if n==7:row.update(panel_identifier_scheme='position_unlettered',contains_schematic_panels=True,schematic_panels=['left'],schematic_structures_visible=['Original source device position icon; not native registered patient anatomy']);context['panel_identifier_scheme']='position_unlettered'
        catalog._validate_source_panel_roles(row);rows.append(row)
        assets.append({'id':ident,'kind':'clinical_image','name':'Original breast ultrasound source Figure '+str(n),'local_path':path,'sha256':sha(raw),'modality':'Ultrasound','investigation_ids':[INV],'structure_ids':[],'requirement_coverage':{},'source_context':context,'source':{'url':URL,'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],'license':{'name':'CC BY 4.0','url':proof['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_path.read_bytes()),'attribution':attribution,'reviewed_at':'2026-10-08'}},'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':f['decoded_pixel_sha256'],'source_PDF_object':f['source_PDF_object'],'source_PDF_page':f['source_PDF_page'],'source_ICC_sha256':f['source_ICC_sha256'],'highest_resolution_acquired_master_verified':True},'anatomical_review':{'status':'pending','reason':'Published selected views do not independently validate every reported structure or matched native3D.'}})
    archive=ROOT/'docs/breast-US-published-source-review/replaced-investigation-images.json';open_path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(open_path.read_text());over_path=ROOT/'data/radiology/investigation-overrides-non-msk.json';over=json.loads(over_path.read_text());steps_path=ROOT/'data/radiology/reporting-steps/breast.json';steps=json.loads(steps_path.read_text());old_images={};all_assets=[]
    for inv,placements in USES.items():
        old_images[inv]=catalog.detail(Curriculum(),catalog.resolve(inv))['radiology_reference']['key_images'];old_ids={r['id'] for r in old_images[inv]};copies=[]
        for row,asset in zip(rows,assets):
            if row['figure_number'] not in placements:continue
            import copy
            r=copy.deepcopy(row);a=copy.deepcopy(asset);ident=PREFIX+str(row['figure_number'])+'-'+inv.removeprefix('ra.');r['id']=a['id']=ident;a['investigation_ids']=[inv];copies.append(r);all_assets.append(a)
        data[inv]=[r for r in data.get(inv,[]) if not r['id'].startswith(PREFIX)]+copies;over.setdefault(inv,{})['key_images']=[];node=steps['investigations'][inv];node['start']={'images':[],'module_illustrations':False}
        for st in node['steps']:st['images']=[i for i in st.get('images',[]) if i not in old_ids and not i.startswith(PREFIX)]
        for r in copies:
            for index in placements[r['figure_number']]:node['steps'][index]['images'].append(r['id'])
    if not archive.exists():archive.write_text(json.dumps({'replaced_investigation_images':old_images,'reason':'Remote placeholders are not locally bound complete original source masters; source reader context/media are preserved in this archive.'},indent=2)+'\n')
    open_path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');over_path.write_text(json.dumps(over,indent=2)+'\n');steps_path.write_text(json.dumps(steps,indent=2,ensure_ascii=False)+'\n');append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',all_assets,prefix=PREFIX)
    source_path=ROOT/'data/radiology/investigation-source-images.json';text=source_path.read_text()
    for inv in USES:
        if '"'+inv+'"' in text:
            start=text.index('[',text.index('"'+inv+'"'));_,end=json.JSONDecoder().raw_decode(text,start);text=text[:start]+'[]'+text[end:]
    source_path.write_text(text)
    for v in vars(catalog).values():
        if callable(getattr(v,'cache_clear',None)):v.cache_clear()
    p=ROOT/'data/radiology/non-msk-structure-requirements.json';requirements=json.loads(p.read_text())
    for item in requirements['investigations']:
        if item['investigation_id'] in USES:
            ref=catalog.detail(Curriculum(),catalog.resolve(item['investigation_id']))['radiology_reference'];item['source_contract_sha256']=digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    p.write_text(json.dumps(requirements,indent=2)+'\n');print('11 complete original breast US figures,21 distinct scoped references; no anatomy/physiology approval granted')
if __name__=='__main__':package()
