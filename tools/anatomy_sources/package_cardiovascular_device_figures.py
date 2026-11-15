#!/usr/bin/env python3
"""Preserve original device radiographs; exclude permission-only material printed in pixels."""
import argparse,hashlib,json,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT=Path(__file__).resolve().parents[2];FOLDER=ROOT/'docs/cardiovascular-device-published-source-review';PREFIX='open-cardiovascular-device-pmc6837806-fig';IDENT='ra.cardiovascular-devices'
PIN={'PMC6837806':'6721aca5040c70472a85aa8c1d592730ee36b6150d641f5fe5f11329a715c8e3','PMC8661294':'6317fed0fee6c317c1cd971d923b376f804bcbf0eeda5fd9f5309afe19217d87'}
TITLES={1:'Generator components and source MRI marker',2:'Dual-chamber lead projections',3:'Source-described abandoned leads',4:'Atrial lead in the IVC',5:'ICD shock-coil projections',6:'Subcutaneous ICD',7:'External magnet over generator',8:'Atrial lead in the SVC',9:'Source-described subtle lead fracture',10:'Source-described conductor externalisation',11:'CRT and coronary-sinus lead projections',12:'Implantable loop recorder',14:'Mitral annuloplasty ring',15:'Mitral tissue prosthesis',16:'Aortic tissue prosthesis',17:'Transcatheter aortic prosthesis',18:'Tricuspid mechanical prosthesis and epicardial leads',19:'Multiple valve prostheses',20:'Pulmonary valve prosthesis',22:'Source-described ductal-occluder migration'}
PAIRS={2,4,5,8,11,15,16,17,18,19,20,22}
SPECIFIC={1:'The source shows a generator/connector close-up and calls its marker MRI conditional. A marker or generator silhouette does not identify/clear the complete present-day lead/system combination or specialist MRI protocol.',
 2:'Original frontal/lateral views are preserved. Source-described RA appendage/RV apical projections are local case examples, not universal acceptable targets for every pacing configuration.',
 3:'The source calls these abandoned leads. Actual connection status, device records, electrical function and complete-system MRI conditions cannot be established from this image alone.',
 4:'Source frontal/lateral views show an atrial lead extending into the IVC, with other prosthetic valves visible. Complete trajectory, wall contact/perforation and function are not independently resolved.',
 5:'Source shock coils are described at the brachiocephalic/SVC junction and RV. Exact model/configuration, tissue interfaces, electrical interrogation and current suitability remain unverified.',
 6:'Source subcutaneous ICD electrode and generator are visible. The original printed 1-2 cm parasternal description is historical case/device context, not a universal device placement or safety threshold.',
 7:'The original radiograph includes an external doughnut magnet over the generator. Magnet response is device/programming-specific; no instruction to apply a magnet or guarantee of pacing/therapy behaviour is inferred.',
 8:'Source describes the atrial lead tip in the SVC. Projected position is not complete 3D route, wall-contact, perforation or electrical-function verification.',
 9:'Original arrow marks a source-described subtle proximal atrial lead fracture. Full conductor/insulation integrity, projection mimics and functional failure require actual source/device assessment.',
 10:'Source describes externalised RV-lead conductors and failure. The picture does not independently prove the full conductor/insulation geometry, failure mechanism or measured interrogation findings.',
 11:'Source labels CRT leads/coils. The LV-targeting coronary-sinus lead follows a cardiac venous route for epicardial stimulation; it is not an assumed intracavitary LV lead. Full venous trajectory/endpoint remains unverified.',
 12:'Source implantable loop-recorder silhouette is retained. Device model, recording performance and underlying cause of symptoms are not independently established.',
 14:'Source mitral annuloplasty C-ring and accompanying leads are visible. Thin ring/tissue attachment, residual valve physiology and device-specific suitability remain unresolved.',
 15:'Source frontal/lateral views depict a mitral tissue prosthesis. Complete frame/leaflet geometry, annular interface and valve function are not independently resolved.',
 16:'Source frontal/lateral views depict an aortic tissue prosthesis. Complete frame/leaflet geometry, annular interface and valve function are not independently resolved.',
 17:'Source frontal/lateral views depict TAVR hardware with other leads. Exact prosthesis model/landing geometry, coronary relations and haemodynamics remain unresolved.',
 18:'Source tricuspid mechanical prosthesis and epicardial leads are retained. Prosthesis/pacing function and complete tissue/fixation interfaces are not independently established.',
 19:'Source arrows identify aortic, mitral and tricuspid prostheses in one case. These projected structures do not independently resolve every prosthetic/native interface or functional abnormality.',
 20:'Source pulmonary valve prosthesis projections are preserved. The complete outflow/device/native tissue interface and physiological performance are not established.',
 22:'Panel a is a catheter aortogram, b a subsequent chest radiograph; the source describes an occluder in the aortic lumen and migration. This is complication case context, not a recommended deployment route. Exact time/registration, complete native duct/device interfaces and flow are not independently verified.'}
COMMON=' Complete original JPEG/annotations and printed source notes are unchanged. Original projection/voxel calibration, full acquisition, independent same-examination/cross-figure patient correspondence, actual current device model/system, complete 3D anatomy and clinical approval are unavailable. No mesh geometry, electrical/valve/pump function, universal safe position or procedure recommendation is derived from a projection.'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package(root):
    FOLDER.mkdir(parents=True,exist_ok=True);root.mkdir(parents=True,exist_ok=True);sources=[];loaded={}
    for ident in PIN:
        path=root/f'{ident}.1.json'
        if not path.exists():path.write_bytes(urllib.request.urlopen(f'https://pmc-oa-opendata.s3.amazonaws.com/{ident}.1/{ident}.1.json',timeout=45).read())
        raw=path.read_bytes()
        if PIN[ident] is not None and sha(raw)!=PIN[ident]:raise ValueError('Reviewed metadata differs')
        m=json.loads(raw);http=lambda u:u.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
        if m['is_retracted'] is not False:raise ValueError('Source retraction changed')
        xml=download_verified(http(m['xml_url']),root/f'{ident}.1.xml');x=ET.fromstring(xml);perm=x.find('.//article-meta/permissions');licence,url=exact_license(perm)
        if licence!='CC BY 4.0':raise ValueError('Original licence differs')
        authors=[' '.join([e.findtext('given-names',''),e.findtext('surname','')]) for e in x.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]
        p={'pmcid':ident,'doi':m['doi'],'title':m['title'],'metadata_sha256':sha(raw),'xml_sha256':sha(xml),'original_license':licence,'original_license_url':url,'permissions_xml':ET.tostring(perm,encoding='unicode'),'authors':authors,'figures':[]}
        if ident=='PMC8661294':p['correction_scope']='Original Research to Review Article classification only; no independent figure/clinical approval.'
        sources.append(p);loaded[ident]=(m,x,p)
    m,x,proof=loaded['PMC6837806'];rows=[];entries=[];excluded=[]
    for n in range(1,23):
        f=x.find('.//fig[@id="F'+str(n).zfill(4)+'"]');caption=' '.join(f.find('caption').itertext());filename=f.find('graphic').get('{http://www.w3.org/1999/xlink}href');u=http(next(u for u in m['media_urls'] if '/'+filename+'?' in u));raw=download_verified(u,root/filename)
        with Image.open(root/filename) as im:
            im.load();s={'figure_number':n,'source_caption':caption,'source_media_url':u,'publisher_md5_verified':True,'sha256':sha(raw),'decoded_pixel_sha256':sha(im.tobytes()),'width':im.width,'height':im.height,'pixel_mode':im.mode,'source_pixels_changed':False}
        if n in [13,21]:
            excluded.append({**s,'not_reused':True,'reason':'Original JPEG footer explicitly states reproduced with permission from Cressman et al., DOI 10.1067/j.cpradiol.2018.05.006. That permission is not a commercial redistribution/sublicence grant to this project; source XML caption omits the in-pixel notice.'});continue
        if f.find('attrib') is not None or f.find('permissions') is not None or any(w in caption.lower() for w in ['courtesy','reproduced','reprinted','adapted']):raise ValueError('Separate credit requires review')
        proof['figures'].append(s);id=PREFIX+str(n);local=f'web/reference-media/radiology-open/cardiovascular-device-pmc6837806-fig{n}.jpg';(ROOT/local).write_bytes(raw);panels=list('ab') if n in PAIRS else ['whole'];limits=SPECIFIC[n]+COMMON;state=f'cardiovascular_device_source_pmc6837806_fig{n}'
        context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'local','depicted_state':state,'selected_panels':panels,
            'panel_types':dict.fromkeys(panels,'Radiography'),'panel_states':dict.fromkeys(panels,state),'source_projection_subtypes':{'a':'Catheter angiography','b':'Chest radiography'} if n==22 else {},
            'full_acquired_series_included':False,'independent_calibrated_measurements_verified':False,'same_examination_registration_verified':False,'cross_figure_patient_identity_verified':False,
            'current_complete_device_system_or_mri_conditions_verified':False,'electrical_or_haemodynamic_function_verified':False,'complete_device_and_tissue_geometry_verified':False,'radiographic_projections_are_actual_3d_geometry':False}
        credit=', '.join(proof['authors'])+'. '+m['title']+'. DOI '+m['doi']+'. CC BY 4.0. Complete original publisher JPEG preserved byte-identically. Erratum DOI 10.4102/sajr.v25i1.2256 corrects article classification only. Historical case/device statements do not establish current conditions or clinical approval. NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.'
        shown=f'Original Figure {n}: {TITLES[n]}. '+limits
        row={'id':id,'kind':'clinical-image','modality':'Radiography','figure_number':n,'src':'/app/'+local.removeprefix('web/'),'width':s['width'],'height':s['height'],'sha256':s['sha256'],
            'source_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC6837806/','figure_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC6837806/#F'+str(n).zfill(4),'asset_source_url':u,
            'clinical_panels':panels,'source_context':context,'image_state':state,'caption':shown,'alt':shown,'limits':limits,'source_caption_full':caption,
            'structures_visible':['Source-local '+TITLES[n].lower()],'license':'CC BY 4.0','license_url':proof['original_license_url'],'attribution':credit,'source_background':'white',
            'rights_reviewed_on':'2026-10-06','rights_review':'Original XML and complete image pixels reviewed; permission-only third-party Figures 13/21 excluded; source case/functional approval remains pending.'}
        rows.append(row);entries.append((row,local,s))
    p={'sources':sources,'in_pixel_permission_material_not_reused':excluded,'clinical_approval':False,'model_promoted':False,'source_pixels_changed':False,
        'noncommercial_other_article_images_not_reused':'PMC4286824'}
    path=FOLDER/'original-source-review.json';path.write_text(json.dumps(p,indent=2)+'\n');proof_sha=sha(path.read_bytes());assets=[]
    for row,local,s in entries:
        assets.append({'id':row['id'],'kind':'clinical_image','name':TITLES[row['figure_number']],'local_path':local,'sha256':row['sha256'],'modality':'Radiography',
            'regions':['heart','thorax','cardiovascular_devices'],'investigation_ids':[IDENT],'structure_ids':[],'requirement_coverage':{},'source_context':row['source_context'],
            'source':{'url':row['source_url'],'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],'license':{'name':'CC BY 4.0','url':row['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(path.relative_to(ROOT)),'evidence_sha256':proof_sha,'attribution':row['attribution'],'reviewed_at':'2026-10-06'}},
            'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':s['decoded_pixel_sha256'],'highest_resolution_acquired_master_verified':False},
            'anatomical_review':{'status':'pending','reason':'Published projection cases do not independently validate every device component/interface, full geometry or clinical function.'},
            'visual_review':{'status':'source_checked','reviewed_at':'2026-10-06','sha256':row['sha256'],'evidence_path':'docs/cardiovascular-device-published-source-review.md'}})
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text());data[IDENT]=[r for r in data.get(IDENT,[]) if not r['id'].startswith(PREFIX)]+rows;path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/investigation-source-images.json';raw=path.read_text();start=raw.index('[',raw.index('"'+IDENT+'"'));old,end=json.JSONDecoder().raw_decode(raw,start);removed=[i for i in old if i['id'] in ['ra-cardiovascular-devices-source-1','ra-cardiovascular-devices-source-2']];remaining=[i for i in old if i not in removed];
    if not removed and (FOLDER/'packaged-source-images.json').exists():removed=json.loads((FOLDER/'packaged-source-images.json').read_text())['replaced_unverified_remote_figures']
    path.write_text(raw[:start]+json.dumps(remaining,indent=2,ensure_ascii=False)+raw[end:])
    path=ROOT/'data/radiology/reporting-steps/cardiovascular.json';raw=path.read_text();start=raw.index('{',raw.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(raw,start);node['start']={'images':[PREFIX+'1',PREFIX+'11'],'module_illustrations':False}
    for i,ns in {0:[1,2,3,5,6,7,11,12,14,15,16,17,18,19,20],1:[2,3,4,8,9,10,11,18],2:[2,4,8,11,14,15,16,17,18,19,20,22],3:[4,8,9,10,22]}.items():
        node['steps'][i]['images']=[id for id in node['steps'][i].get('images',[]) if id not in [r['id'] for r in removed]]
        node['steps'][i]['images']=list(dict.fromkeys(node['steps'][i]['images']+[PREFIX+str(n) for n in ns]))
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    (FOLDER/'packaged-source-images.json').write_text(json.dumps({'figures':[{'figure_number':r['figure_number'],'local_path':local,'sha256':r['sha256']} for r,local,s in entries],
        'replaced_unverified_remote_figures':removed,'clinical_approval':False,'model_promoted':False,'structure_coverage_granted':False},indent=2)+'\n')
    print('Twenty original figures packaged; permission-only 13/21 excluded; two unverified remote figures replaced.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
