#!/usr/bin/env python3
"""Preserve original venous drainage figures with actual panel modalities and source limits."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
from PIL import Image
from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'docs/vascular-venous-published-source-review'
PREFIX='open-vascular-venous-'
IDENT='ra.vascular-anomalies'
PIN={'PMC7561662':'3ba69d70035638308989773f69a4c1827535d4741a9ed3c2e76f7b61c1635a21','PMC8052389':'01cba7bbe2f783f2a5da5be8cbba2f7959dd1d00654b59834e7f429bce07c18a','PMC3038141':'9949d69e4c22adfea454182febeec461ce4cd758e54a3ad54de72ff43347c337'}
# Exact uppercase letters printed in the original JPEG, not silently replaced with caption case.
CONFIG={
 2:('Left SVC drainage endpoints','BDEFG','CH','DF', 'A/B are source-described different patients. A is chest radiography, C/H flat VR, B/D/E/F/G CT views. The caption misidentifies axial F and rendered G/H; actual G is a CT plane and H flat VR. Original labels/caption are retained. ASD and coronary-sinus ostial atresia are explicitly not shown; these diagnoses are not independently proven.'),
 3:('Bilateral/isolated SVC and bridging veins','ABCDE','','','Source A/B/C are different patients. A/B show relative caval sizes, C source-described isolated left SVC, D/E bridging veins. These views do not prove every systemic drainage endpoint or anatomical absence beyond coverage.'),
 4:('Pulmonary venous and septal associations with left SVC','ABCDEFH','GI','','Source A/B, D/E, F/G and H/I describe separate associations. G/I are flat VR. Source septal, ductal and pulmonary venous connections require complete source tracing; static panels do not independently establish shunt direction, ratio or severity.'),
 13:('Heterotaxy, atrial morphology and interrupted IVC context','ABCDEFGHI','','B','Source A-D illustrate right-isomerism features, E-I left-isomerism features; source groups are not a single patient. PLSVC is not shown in A-D. Local enlarged azygos/IVC-absence wording does not prove complete hepatic/IVC/azygos connections. Gross lung or appendage morphology alone is not complete segmental diagnosis.'),
 17:('Vertical vein in partial and total anomalous return','ABCDEGH','F','G','Source A-E depict partial left-upper return; F-H depict supracardiac total return, a separate source patient. F is flat VR. Complete lobar mapping, collector obstruction, calibration and shunt physiology are not supplied.'),
 18:('Levoatriocardinal connection differential','ABCD','EF','','Source A-D are CT planes and E/F flat VR. Single-phase density differences may suggest source flow direction but do not independently measure it; dynamic assessment is separate. No universal flow direction is assumed.'),
 20:('Pericardiophrenic venous collateral pathways','ABCDEF','','','Source A-C describe SVC stenosis; D-F another patient with portal hypertension/Budd-Chiari context. D is non-enhanced; E/F enhanced CT. The transdiaphragmatic/hepatic connection is source-described, not complete independent channel/flow validation.'),
 21:('Left superior intercostal vein before/after obstruction','ABCDEF','','','Source A-C and D-F are described as the same patient before/after SVC occlusion; exact dates, registration and native source are unavailable. No generic diameter threshold or contrast density substitutes for actual calibre and functional evidence.'),
 22:('Subaortic and retrooesophageal brachiocephalic pathways','ABCEFGH','D','','Source A-D depict subaortic course and E-H retrooesophageal course; patient correspondence across groups is not proven. D is flat VR. Complete distal connection/coverage must be traced in the actual examination.'),
 23:('Glenn and systemic-to-pulmonary surgical shunts','ABCDEF','','','Source A-C depict bicaval Glenn; D-F depict another postoperative arterial-shunt context. Original caption describes E/F but omits actual panel D, which is preserved without inferred caption assignment. Native operative details, patency, full topology and flow remain unverified.')}
COMMON=' Complete original JPEG, labels and annotations are unchanged. Original voxel series, physical calibration, independent cross-panel/series registration, highest-resolution acquired master and complete anatomical/clinical approval are unavailable. Flat CT renderings are not actual mesh geometry; static images do not independently prove dynamic flow or treatment suitability.'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(root,ident):
    mp=root/f'{ident}.1.json'
    if not mp.exists():mp.write_bytes(urllib.request.urlopen(f'https://pmc-oa-opendata.s3.amazonaws.com/{ident}.1/{ident}.1.json',timeout=45).read())
    if sha(mp.read_bytes())!=PIN[ident]:raise ValueError('Reviewed metadata differs')
    m=json.loads(mp.read_text());http=lambda u:u.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
    if m['pmcid']!=ident or m['is_retracted'] is not False:raise ValueError('Source identity/retraction differs')
    raw=download_verified(http(m['xml_url']),root/f'{ident}.1.xml');x=ET.fromstring(raw);permissions=x.find('.//article-meta/permissions');licence,url=exact_license(permissions)
    expected='CC BY 2.0' if ident=='PMC3038141' else 'CC BY 4.0'
    if licence!=expected:raise ValueError('Original grant differs')
    authors=[' '.join([e.findtext('given-names',''),e.findtext('surname','')]) for e in x.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]
    return m,x,{'pmcid':ident,'doi':m['doi'],'title':m['title'],'metadata_sha256':PIN[ident],'xml_sha256':sha(raw),
        'original_license':licence,'original_license_url':url,'permissions_xml':ET.tostring(permissions,encoding='unicode'),'authors':authors,'figures':[]}
def package(root):
    root.mkdir(parents=True,exist_ok=True);FOLDER.mkdir(parents=True,exist_ok=True);loaded={i:load(root,i) for i in PIN};rows=[];entries=[]
    m,x,correction=loaded['PMC8052389'];correction['correction_text']=' '.join(x.find('body').itertext());correction['affects']='Reference numbering and author name spelling; source states original article updated. No source figure/clinical approval inferred.'
    for ident,numbers in [('PMC7561662',list(CONFIG)),('PMC3038141',[1])]:
        m,x,proof=loaded[ident];http=lambda u:u.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
        for n in numbers:
            f=x.find('.//fig[@id="'+('Fig' if ident=='PMC7561662' else 'F')+str(n)+'"]');caption=' '.join(f.find('caption').itertext())
            if f.find('attrib') is not None or f.find('permissions') is not None or any(w in caption.lower() for w in ['courtesy','reprinted','reproduced','adapted']):raise ValueError('Separate figure credit needs review')
            filename=f.find('graphic').get('{http://www.w3.org/1999/xlink}href');urls=[u for u in m['media_urls'] if '/'+filename+'?' in u]
            if len(urls)!=1:raise ValueError('Ambiguous original')
            url=http(urls[0]);raw=download_verified(url,root/filename)
            with Image.open(root/filename) as im:
                im.load();source={'figure_number':n,'source_caption':caption,'source_media_url':url,'publisher_md5_verified':True,'sha256':sha(raw),
                    'width':im.width,'height':im.height,'pixel_mode':im.mode,'decoded_pixel_sha256':sha(im.tobytes()),'source_pixels_changed':False,'method':'complete_original_publisher_jpeg_byte_identical'}
            proof['figures'].append(source);id=PREFIX+ident.lower()+'-fig'+str(n);local='web/reference-media/radiology-open/'+id.removeprefix('open-')+'.jpg';(ROOT/local).write_bytes(raw)
            if ident=='PMC7561662':
                title,clinical,rendered,projected,specific=CONFIG[n];modality='CT';types=dict.fromkeys('ABCDEFGHI'[:9 if n in [4,13] else 8 if n in [2,17,22] else 5 if n==3 else 6],'CT')
                if n==2:types['A']='Radiography'
                ancillary=[{'kind':'Radiography','panels':['A'],'structures_visible':['Source-described central venous catheter projection'],'limits':'Different patient from B; chest radiograph does not trace the full venous drainage or determine catheter safety.'}] if n==2 else []
            else:
                title='MRI and echocardiographic anomalous pulmonary return';clinical='D';rendered='';projected='';modality='MRI';types={'A':'Ultrasound','B':'Ultrasound','C':'Ultrasound','D':'MRI'}
                specific='Source A/B are TTE, C TEE and D CMR; the article describes one case with both left pulmonary veins draining to the innominate vein. A-C are separate ultrasound observations, not MR venous anatomy. Color-Doppler stills are not the complete acquired temporal study; the source Qp/Qs 1.1:1 and historical management statements are case context, not independently measurable here or universal intervention rules. Supplementary echo movies exist but are not acquired in this packet.'
                ancillary=[{'kind':'Ultrasound','panels':list('ABC'),'structures_visible':['Source-described ventricular enlargement and interatrial color-Doppler observations'],'limits':'Static TTE/TEE panels from the case are not acquired MR vein anatomy or the full temporal/quantitative functional study.'}]
            state=f'venous_source_{ident.lower()}_fig{n}';limits=specific+COMMON
            context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'local','depicted_state':state,
                'selected_panels':list(clinical),'panel_types':types,'panel_states':dict.fromkeys(types,state),'source_ct_volume_rendering_panels':list(rendered),
                'source_projected_ct_panels':list(projected),'source_panel_identifier_case':'uppercase_in_original_pixels',
                'flat_renderings_are_spatial_geometry':False,'full_acquired_series_included':False,'independent_calibrated_measurements_verified':False,
                'same_series_registration_verified':False,'cross_figure_patient_identity_verified':False,'dynamic_flow_or_quantitative_shunt_verified':False,
                'complete_venous_geometry_verified':False,'native_source_motion_acquired':False}
            credit=', '.join(proof['authors'])+'. '+m['title']+'. DOI '+m['doi']+'. '+proof['original_license']+'. Complete original publisher JPEG preserved byte-identically. '+('Published correction DOI 10.1186/s13244-021-00983-x concerns references/name spelling. ' if ident=='PMC7561662' else '')+'NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.'
            shown=f'Original Figure {n}: {title}. '+limits
            row={'id':id,'kind':'clinical-image','modality':modality,'figure_number':n,'src':'/app/'+local.removeprefix('web/'),
                'width':source['width'],'height':source['height'],'sha256':source['sha256'],'source_url':f'https://pmc.ncbi.nlm.nih.gov/articles/{ident}/',
                'figure_url':f'https://pmc.ncbi.nlm.nih.gov/articles/{ident}/#'+('Fig' if ident=='PMC7561662' else 'F')+str(n),'asset_source_url':url,
                'clinical_panels':list(clinical),'ancillary_panels':ancillary,'source_context':context,'image_state':state,'caption':shown,'alt':shown,'limits':limits,
                'source_caption_full':caption,'structures_visible':['Source-local '+title.lower()],'license':proof['original_license'],'license_url':proof['original_license_url'],
                'attribution':credit,'source_background':'white','rights_reviewed_on':'2026-10-06','rights_review':'Original XML licence, separate figure credits, publisher MD5/file/pixel SHA and source panel roles reviewed; anatomy approval remains pending.'}
            rows.append(row);entries.append((row,local,source))
    proof={'sources':[v[2] for v in loaded.values()],'clinical_approval':False,'model_promoted':False,'source_pixels_changed':False,
        'caption_panel_mismatch_figures':{'PMC7561662':[2,23]},'supplementary_motion_acquired':False}
    path=FOLDER/'original-source-review.json';path.write_text(json.dumps(proof,indent=2)+'\n');proof_sha=sha(path.read_bytes());assets=[]
    for row,local,source in entries:
        assets.append({'id':row['id'],'kind':'clinical_image','name':row['caption'].split('. ')[0],'local_path':local,'sha256':row['sha256'],
            'regions':['thorax','pulmonary_veins','systemic_veins'],'investigation_ids':[IDENT],'structure_ids':[],'requirement_coverage':{},'modality':row['modality'],
            'source_context':row['source_context'],'source':{'url':row['source_url'],'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],
                'license':{'name':row['license'],'url':row['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(path.relative_to(ROOT)),
                    'evidence_sha256':proof_sha,'attribution':row['attribution'],'reviewed_at':'2026-10-06'}},
            'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':source['decoded_pixel_sha256'],'highest_resolution_acquired_master_verified':False},
            'anatomical_review':{'status':'pending','reason':'Local CT/MRI and separate radiographic/echo panels do not independently verify complete venous topology, source motion or haemodynamics.'},
            'visual_review':{'status':'source_checked','sha256':row['sha256'],'reviewed_at':'2026-10-06','evidence_path':'docs/vascular-venous-published-source-review.md'}})
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text());data[IDENT]=[r for r in data.get(IDENT,[]) if not r['id'].startswith(PREFIX)]+rows
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/reporting-steps/cardiovascular.json';raw=path.read_text();start=raw.index('{',raw.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(raw,start)
    ct=lambda n:PREFIX+'pmc7561662-fig'+str(n)
    for i,ids in {3:[ct(4),ct(17),ct(18),PREFIX+'pmc3038141-fig1'],4:[ct(n) for n in [2,3,4,13,18,20,21,22,23]]}.items():
        node['steps'][i]['images']=list(dict.fromkeys(node['steps'][i].get('images',[])+ids))
    for i,extra in {3:' Single-phase contrast density does not independently quantify flow direction or Qp/Qs; report the actual functional source.',4:' Trace vertical/levoatriocardinal, pericardiophrenic and postoperative mimics to their actual endpoints; single-phase density is not a calibrated flow measurement.'}.items():
        if extra not in node['steps'][i]['tip']:node['steps'][i]['tip']+=extra
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    (FOLDER/'packaged-source-images.json').write_text(json.dumps({'figures':[{'id':r['id'],'local_path':local,'sha256':r['sha256']} for r,local,s in entries],
        'clinical_approval':False,'model_promoted':False,'structure_coverage_granted':False},indent=2)+'\n')
    print('Eleven complete venous source figures preserved with CC BY 4.0/2.0, correction and modality/flow limits.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
