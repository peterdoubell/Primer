#!/usr/bin/env python3
"""Acquire/package complete original TAVI teaching figures with historical cutoff and simulation limits."""
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
FOLDER=ROOT/'docs/tavi-published-source-review'
PREFIX='open-tavi-pmc9743261-fig'
IDENT='ra.ct-tavi'
META_SHA='8b62330e67a327826bcea1463a472918ede74ea9b1ab90b8818c4c0a1dfa4207'
TITLES={1:'Root components and annular terminology',2:'Annular dimensions and contour example',3:'Bicuspid/tricuspid example views',
    4:'Right coronary ostial height example',5:'Sinus plane and source cusp-to-commissure axes',6:'Sinotubular diameter plane example',
    7:'Sinotubular height example',8:'Ascending-aortic plane example'}

def sha(raw):return hashlib.sha256(raw).hexdigest()

def package(root):
    root.mkdir(parents=True,exist_ok=True);metadata=root/'PMC9743261.1.json'
    if not metadata.exists():
        with urllib.request.urlopen('https://pmc-oa-opendata.s3.amazonaws.com/PMC9743261.1/PMC9743261.1.json',timeout=60) as r:metadata.write_bytes(r.read())
    if sha(metadata.read_bytes())!=META_SHA:raise ValueError('Reviewed metadata snapshot differs')
    meta=json.loads(metadata.read_text());http=lambda u:u.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
    if meta['is_retracted'] is not False:raise ValueError('Source retraction status differs')
    xml=download_verified(http(meta['xml_url']),root/'PMC9743261.1.xml');tree=ET.fromstring(xml);permissions=tree.find('.//article-meta/permissions')
    licence,licence_url=exact_license(permissions)
    if licence!='CC BY 4.0':raise ValueError('Original grant differs')
    authors=[' '.join([n.findtext('given-names',''),n.findtext('surname','')]) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]
    proof_rows=[];rows=[];asset_inputs=[]
    FOLDER.mkdir(parents=True,exist_ok=True)
    for n in range(1,9):
        f=tree.find('.//fig[@id="F'+str(n)+'"]');caption=' '.join(f.find('caption').itertext())
        if f.find('attrib') is not None or f.find('permissions') is not None or any(w in caption.lower() for w in ['reprinted','reproduced','adapted','courtesy']):raise ValueError('Separate credit needs review')
        filename=f.find('graphic').get('{http://www.w3.org/1999/xlink}href')
        url=http(next(u for u in meta['media_urls'] if '/'+filename+'?' in u));raw=download_verified(url,root/filename)
        with Image.open(root/filename) as image:
            image.load();source={'figure_number':n,'source_caption':caption,'source_media_url':url,'publisher_md5_verified':True,
                'sha256':sha(raw),'width':image.width,'height':image.height,'pixel_mode':image.mode,'decoded_pixel_sha256':sha(image.tobytes()),
                'source_pixels_changed':False,'source_method':'complete_original_publisher_jpeg_byte_identical'}
        proof_rows.append(source);schematic=n==1;modality='Schematic' if schematic else 'CT'
        panels=[] if schematic else list('AB') if n==3 else list('ABC') if n in (5,6,8) else ['whole']
        local=f'web/reference-media/radiology-open/tavi-pmc9743261-fig{n}.jpg';(ROOT/local).write_bytes(raw)
        common='Complete acquired voxel series, cardiac phase/calibration, source patient correspondence across figures and independent anatomical/clinical validation are unavailable. No complete patient model, continuous motion or device simulation is inferred.'
        specific={1:'Conceptual root/annular terminology drawing, not acquired CT or patient-specific geometry.',
            2:'Coloured source contour/diameter annotations demonstrate measurement roles; actual calibrated area/perimeter and device sizing are not derived from display pixels.',
            3:'A/B are separate bicuspid/tricuspid teaching examples; do not merge their anatomy or infer one registered comparison.',
            4:'Only the right coronary height is shown. The caption height cutoff is a historical risk association, not a universal obstruction/suitability rule or left-coronary coverage.',
            5:'The source uses cusp-to-commissure axes and a symmetric-root average. Preserve that named planning convention separately from maximum sinus-to-sinus surveillance methods. Caption sinus-width cutoff is not a universal obstruction rule.',
            6:'Source planes and STJ diameter line are local examples, not independently calibrated patient or device-clearance measurements.',
            7:'The displayed height line does not supply the complete annular/STJ contours or independently validated reference plane.',
            8:'Source views illustrate a perpendicular ascending-aorta plane; full aortic/access routes, actual edge convention and maximal extent remain unverified.'}[n]
        limits=specific+' '+common;state=f'tavi_source_pmc9743261_fig{n}'
        context={'setting':'not_reported' if schematic else 'in_vivo','laterality':'right' if n==4 else 'not_reported',
            'population':{'life_stage':'not_reported'},'extent':'local','depicted_state':state,'selected_panels':panels,
            'panel_types':{p:modality for p in panels},'panel_states':{p:state for p in panels},
            'single_unlettered_image':not schematic and panels==['whole'],'conceptual_diagram':schematic,
            'cross_figure_patient_identity_verified':False,'full_acquired_series_included':False,
            'independent_calibrated_measurements_verified':False,'complete_device_simulation_or_suitability_verified':False,
            'independent_anatomical_review_verified':False}
        title=TITLES[n];text=f'Original Figure {n}: {title}. Complete source annotations and JPEG are preserved. '+limits
        credit=', '.join(authors)+'. '+meta['title']+'. DOI '+meta['doi']+'. CC BY 4.0. Original publisher JPEG reproduced byte-identically without sample changes. NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.'
        row={'id':PREFIX+str(n),'kind':'schematic' if schematic else 'clinical-image','modality':modality,
            'src':'/app/'+local.removeprefix('web/'),'width':source['width'],'height':source['height'],'sha256':source['sha256'],'figure_number':n,
            'source_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC9743261/','figure_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC9743261/#F'+str(n),
            'asset_source_url':url,'clinical_panels':panels,'source_context':context,'image_state':state,'caption':text,'alt':text,
            'limits':limits,'source_caption_full':caption,'structures_visible':['Source-local '+title],
            'license':licence,'license_url':licence_url,'attribution':credit,'source_background':'white',
            'rights_reviewed_on':'2026-10-06','rights_review':'Original XML grant/caption and complete publisher MD5/SHA/sample identities reviewed.'}
        rows.append(row);asset_inputs.append((row,local,source))
    proof={'pmcid':'PMC9743261','doi':meta['doi'],'title':meta['title'],'metadata_sha256':META_SHA,'xml_sha256':sha(xml),
        'original_license':licence,'original_license_url':licence_url,'permissions_xml':ET.tostring(permissions,encoding='unicode'),
        'authors':authors,'figures':proof_rows,'source_pixels_changed':False,'clinical_approval':False,'model_promoted':False}
    proof_path=FOLDER/'original-source-review.json';proof_path.write_text(json.dumps(proof,indent=2)+'\n')
    assets=[]
    for row,local,source in asset_inputs:
        assets.append({'id':row['id'],'kind':'schematic' if row['kind']=='schematic' else 'clinical_image','name':TITLES[row['figure_number']],
            'local_path':local,'sha256':row['sha256'],'regions':['aortic_root','thorax'],'investigation_ids':[IDENT],
            'structure_ids':[],'requirement_coverage':{},'modality':row['modality'],'source_context':row['source_context'],
            'source':{'url':row['source_url'],'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],
                'license':{'name':licence,'url':licence_url,'commercial_use':True,'redistribution':True,'review_status':'verified',
                    'evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_path.read_bytes()),'attribution':row['attribution'],'reviewed_at':'2026-10-06'}},
            'pixel_provenance':{'decoded_pixel_sha256':source['decoded_pixel_sha256'],'source_pixels_changed':False,'highest_resolution_acquired_master_verified':False},
            'anatomical_review':{'status':'pending','reason':'Local annotated examples/concept drawing do not independently validate complete patient anatomy, measurement or device outcome.'},
            'visual_review':{'status':'source_checked','sha256':row['sha256'],'reviewed_at':'2026-10-06','evidence_path':'docs/tavi-published-source-review.md'}})
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text());data[IDENT]=[r for r in data.get(IDENT,[]) if not r['id'].startswith(PREFIX)]+rows
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/reporting-steps/cardiovascular.json';raw=path.read_text();start=raw.index('{',raw.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(raw,start)
    for index,figures in {0:[2],1:[3],2:[4,5],3:[5,6,7,8]}.items():node['steps'][index]['images']=list(dict.fromkeys(node['steps'][index].get('images',[])+[PREFIX+str(n) for n in figures]))
    node['start']={'images':[PREFIX+'1'],'module_illustrations':False}
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    (FOLDER/'packaged-source-images.json').write_text(json.dumps({'figures':[{'id':r['id'],'figure_number':r['figure_number'],'local_path':local,'sha256':r['sha256']} for r,local,s in asset_inputs],
        'clinical_approval':False,'structure_coverage_granted':False,'model_promoted':False},indent=2)+'\n')
    print('Eight complete original TAVI CT/schematic figures preserved; no clinical/device approval granted.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    package(p.parse_args().source_root)
