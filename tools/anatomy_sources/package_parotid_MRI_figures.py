#!/usr/bin/env python3
"""Preserve distinct adult/adolescent MRI cases and keep derived curves outside image anatomy."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from PIL import Image
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_radiology_fidelity import digest
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT=Path(__file__).resolve().parents[2];INV='ra.head-neck-malignancy';PREFIX='open-parotid-pmc11719534-fig';URL='https://pmc.ncbi.nlm.nih.gov/articles/PMC11719534/'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package(source):
    proof_path=ROOT/'docs/parotid-MRI-published-source-review/original-source-review.json';proof=json.loads(proof_path.read_text());archive=proof_path.parent/'packaged-source-images.json'
    if proof['original_article_grant']!='CC BY 4.0' or not proof['all_three_original_masters_and_source_PDF_pages_visually_inspected']:raise ValueError('Reviewed source rights/layout differs')
    replaced=json.loads(archive.read_text())['replaced_investigation_images'] if archive.exists() else catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference']['key_images'];rows=[];assets=[]
    for figure in proof['figures']:
        n=figure['figure_number'];ident=PREFIX+str(n);case=proof['source_case_contexts'][str(n)];path=source/'PMC11719534/original-PDF-masters'/figure['source_master_filename'];raw=path.read_bytes()
        if sha(raw)!=figure['source_master_sha256']:raise ValueError('Original master changed')
        with Image.open(path) as im:
            im.load();pixels=im.tobytes()
            if sha(pixels)!=figure['decoded_pixel_sha256'] or im.size!=(figure['width'],figure['height']):raise ValueError('Original decoded samples differ')
        primary=list('abcde');context={'setting':'in_vivo','laterality':case['laterality'],'population':{'age_years':case['age_years'],'sex':case['sex'],'life_stage':'child' if case['age_years']<18 else 'adult'},'extent':'local','depicted_state':'source_distinct_parotid_tumour_example','selected_panels':primary,'panel_types':{**{p:'MRI' for p in primary},'f':'MRI-derived plot'},'panel_states':{p:'source_distinct_parotid_tumour_example' for p in 'abcdef'},'source_case_groups':{'source_patient_figure_'+str(n):list('abcdef')},'source_sequence_roles':proof['source_panel_roles'],'source_tissue_label':case['source_label'],'different_figures_assumed_same_patient':False,'source_panels_independently_registered':False,'native_orientation_or_full_anatomical_extent_verified':False,'source_normalized_signal_or_ADC_are_independent_new_measurements':False,'source_classifier_is_current_patient_diagnostic_guarantee':False}
        limits='Distinct source '+str(case['age_years'])+'-year-old '+case['sex']+', '+case['laterality']+' parotid. T1/T2/late postcontrast/DWI/ADC views are separate source sequences; panel f is a derived DCE signal-time plot. Source tissue label and normalized ratios are publication context, not new histology, calibrated ADC/DCE measurements or a universal classifier. Selected stills do not supply full gland/duct/nerve/vessel/node interfaces, native registration, physiological function or matched patient 3D.'
        attribution=', '.join(proof['original_author_names'])+'. High Field MRI in Parotid Gland Tumors: A Diagnostic Algorithm. DOI '+proof['doi']+'. Figure '+str(n)+'. CC BY4.0. Complete original PDF samples preserved without enhancement/resampling; no endorsement implied.'
        local=f'web/reference-media/radiology-open/parotid-pmc11719534-fig{n}.png';(ROOT/local).write_bytes(raw)
        row={'id':ident,'kind':'clinical-image','modality':'MRI','figure_number':n,'src':'/app/'+local.removeprefix('web/'),'sha256':sha(raw),'width':figure['width'],'height':figure['height'],'source_url':URL,'figure_url':URL+'#cancers-17-00071-f00'+str(n),'asset_source_url':'https://pmc-oa-opendata.s3.amazonaws.com/PMC11719534.1/PMC11719534.1.pdf','clinical_panels':primary,'ancillary_panels':[{'kind':'MRI-derived plot','panels':['f'],'structures_visible':['Source DCE signal-intensity/time plot'],'limits':'Derived source plot, not tissue anatomy or the full native/calibrated DCE acquisition; source curve type does not independently establish a unique diagnosis.'}],'source_context':context,'image_state':context['depicted_state'],'caption':'Source Figure '+str(n)+': '+str(case['age_years'])+'-year-old '+case['sex']+', '+case['laterality']+' parotid MRI example.','alt':'Complete source parotid MRI Figure '+str(n)+' with separate DCE plot.','limits':limits,'source_caption_full':figure['source_caption_full'],'structures_visible':['Source-local parotid and lesion components; full tissue boundaries unapproved'],'license':proof['original_article_grant'],'license_url':proof['license_url'],'attribution':attribution,'rights_reviewed_on':'2026-10-07','rights_review':'Explicit original CC BY4 source grant; individual PDF page/caption/master binding and exact samples reviewed. Clinical algorithm not adopted.'}
        catalog._validate_source_panel_roles(row);rows.append(row)
        assets.append({'id':ident,'kind':'clinical_image','name':'Original parotid MRI source case '+str(n),'local_path':local,'sha256':sha(raw),'modality':'MRI','investigation_ids':[INV],'structure_ids':[],'requirement_coverage':{},'source_context':context,'source':{'url':URL,'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],'license':{'name':proof['original_article_grant'],'url':proof['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_path.read_bytes()),'attribution':attribution,'reviewed_at':'2026-10-07'}},'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':sha(pixels),'source_PDF_object':figure['source_PDF_object'],'highest_resolution_acquired_master_verified':True,'HTML_PDF_encoded_contrast_difference_preserved':True},'anatomical_review':{'status':'pending','reason':'Source case images/derived curves do not establish every actual gland/duct/internal tissue/nerve/vessel/node or lesion interface.'},'visual_review':{'status':'source_checked','sha256':sha(raw),'evidence_path':'docs/parotid-MRI-published-source-review.md','reviewed_at':'2026-10-07'}})
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text());data[INV]=[r for r in data.get(INV,[]) if not r['id'].startswith(PREFIX)]+rows;path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';data=json.loads(path.read_text());data[INV]['key_images']=[];path.write_text(json.dumps(data,indent=2)+'\n')
    path=ROOT/'data/radiology/investigation-source-images.json';text=path.read_text()
    if '"'+INV+'"' in text:
        start=text.index('[',text.index('"'+INV+'"'));_,end=json.JSONDecoder().raw_decode(text,start);path.write_text(text[:start]+'[]'+text[end:])
    path=ROOT/'data/radiology/reporting-steps/head-neck.json';text=path.read_text();start=text.index('{',text.index('"'+INV+'"'));node,end=json.JSONDecoder().raw_decode(text,start);old={r['id'] for r in replaced};node['start']={'images':[],'module_illustrations':False}
    for step in node['steps']:step['images']=[i for i in step.get('images',[]) if i not in old and not i.startswith(PREFIX)]
    for index in [0,1]:node['steps'][index]['images']=list(dict.fromkeys(node['steps'][index]['images']+[r['id'] for r in rows]))
    path.write_text(text[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+text[end:]);archive.write_text(json.dumps({'replaced_investigation_images':replaced,'published_figure_ids':[r['id'] for r in rows],'clinical_approval':False,'structure_coverage_granted':False},indent=2)+'\n')
    for value in vars(catalog).values():
        if callable(getattr(value,'cache_clear',None)):value.cache_clear()
    ref=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference'];path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
    for item in data['investigations']:
        if item['investigation_id']==INV:item['source_contract_sha256']=digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    path.write_text(json.dumps(data,indent=2)+'\n');print('Three original adult/adolescent MRI cases integrated with separate derived plot role')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);a=p.parse_args();package(a.source_root)
