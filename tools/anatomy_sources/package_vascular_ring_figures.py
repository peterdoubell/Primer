#!/usr/bin/env python3
"""Preserve complete source ring/slings JPEGs and separate clinical, schematic and rendering panels."""
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
FOLDER=ROOT/'docs/vascular-ring-published-source-review'
PREFIX='open-vascular-ring-pmc4141344-fig'
IDENT='ra.vascular-anomalies'
META_SHA='d9beb69a745ca7f66dad95e59d3e8b32aa9e44fbf7907396f804a643a4ab4e1f'
# Original source panels, inspected against complete publisher JPEGs.
CONFIG={
 1:('Developmental arch schematic','ab','','',''),
 2:('Double aortic arch configurations','a','bcde','fgh','ce'),
 3:('Double arch with atretic left component','','ab','cd',''),
 4:('Postoperative double arch rendering','','','whole',''),
 5:('Right arch with Kommerell diverticulum','a','bce','d','c'),
 6:('Right arch with mirror branches and source-described patent ductus','a','b','c','b'),
 7:('Circumflex right arch local CT planes','','abc','',''),
 8:('Left arch with aberrant right subclavian','a','bc','d','c'),
 9:('Aberrant right subclavian aneurysm','','ab','',''),
 10:('Anomalous innominate artery and tracheal indentation','a','bc','','c'),
 11:('Pulmonary sling and bridging bronchus','a','bc','','c')}
SPECIFIC={
 1:'Panels a/b are conceptual developmental/normal-arch drawings, not fetal CT or patient geometry. The source explicitly states that all six embryonic arches are not present simultaneously and the fifth is absent in most fetuses.',
 2:'Panel a is schematic; b/c/d/e are CT or CT projections; f/g/h are flat renderings, including airway h. The source identifies e/g as another patient and e/g as the same patient. Do not combine these configurations into a single patient model.',
 3:'Panels a/b are local CT; c is flat VR and d virtual bronchoscopy. Source-described atresia and ring completion require secondary-sign/operative context; these views do not directly resolve every non-opacified arch/ligamentous segment or prove dynamic airway dysfunction.',
 4:'The complete single panel is a flat postoperative CT volume rendering. No acquired clinical CT panel, operative record, original geometry or complete residual compression assessment is supplied.',
 5:'Panel a is schematic; b/c/e are CT or CT projections; d is flat VR. Local wall/diverticulum/airway examples do not establish complete ductal/ligamentous attachments, independent dimensions or functional severity.',
 6:'Panel a is schematic, b is a coronal CT MIP and c flat VR. The caption describes a patent ductus from the left brachiocephalic artery to the left pulmonary artery and calls it a ring. The complete connection and encirclement are source-described, not independently validated from a projection or generic model.',
 7:'Panels a/b/c are local axial CT. The original caption has incomplete/ambiguous side wording (a reaches "the side", b "reached the right" yet continues as a left descending aorta). The original caption is retained; no silent side correction or source-series registration is inferred.',
 8:'Panel a is schematic; b/c are CT or CT projections; d is flat VR. The aberrant right subclavian course does not alone establish every component of a complete vascular ring.',
 9:'Panels a/b are axial/coronal CT of a source-described partially thrombosed aberrant right subclavian aneurysm; the caption identifies the same patient. Original dimensions, volumetric extent, clinical urgency and independent same-series registration are not supplied.',
 10:'Panel a is schematic; b is axial CT and c sagittal MinIP. Static anterior tracheal indentation does not establish dynamic malacia, symptoms or operative significance.',
 11:'Panel a is schematic, b axial CT and c airway MinIP. The source describes an LPA sling and a bridging bronchus supplying right middle/lower lobes. Complete tracheal cartilage rings, dynamic motion and all lobar/vascular connections are not independently resolved.'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package(root):
    root.mkdir(parents=True,exist_ok=True);mp=root/'PMC4141344.1.json'
    if not mp.exists():mp.write_bytes(urllib.request.urlopen('https://pmc-oa-opendata.s3.amazonaws.com/PMC4141344.1/PMC4141344.1.json',timeout=45).read())
    if sha(mp.read_bytes())!=META_SHA:raise ValueError('Reviewed source metadata differs')
    m=json.loads(mp.read_text());http=lambda u:u.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
    if m['pmcid']!='PMC4141344' or m['is_retracted'] is not False:raise ValueError('Source identity/retraction differs')
    xml=download_verified(http(m['xml_url']),root/'PMC4141344.1.xml');x=ET.fromstring(xml);permissions=x.find('.//article-meta/permissions');licence,licence_url=exact_license(permissions)
    if licence!='CC BY 4.0':raise ValueError('Original grant differs')
    authors=[' '.join([e.findtext('given-names',''),e.findtext('surname','')]) for e in x.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]
    FOLDER.mkdir(parents=True,exist_ok=True);sources=[];rows=[];entries=[]
    for n,(title,schematic,clinical,rendered,projected) in CONFIG.items():
        f=x.find('.//fig[@id="Fig'+str(n)+'"]');caption=' '.join(f.find('caption').itertext())
        if f.find('attrib') is not None or f.find('permissions') is not None or any(w in caption.lower() for w in ['courtesy','reprinted','reproduced','adapted','provided by']):raise ValueError('Separate figure credit needs review')
        filename=f.find('graphic').get('{http://www.w3.org/1999/xlink}href');urls=[u for u in m['media_urls'] if '/'+filename+'?' in u]
        if len(urls)!=1:raise ValueError('Original source media ambiguous')
        url=http(urls[0]);raw=download_verified(url,root/filename)
        with Image.open(root/filename) as im:
            im.load();source={'figure_number':n,'source_caption':caption,'source_media_url':url,'publisher_md5_verified':True,'sha256':sha(raw),
                'width':im.width,'height':im.height,'pixel_mode':im.mode,'decoded_pixel_sha256':sha(im.tobytes()),'source_pixels_changed':False,
                'method':'complete_original_publisher_jpeg_byte_identical'}
        sources.append(source);local=f'web/reference-media/radiology-open/vascular-ring-pmc4141344-fig{n}.jpg';(ROOT/local).write_bytes(raw)
        limits=SPECIFIC[n]+' Complete original annotations/JPEG are preserved. Full acquired series, voxel/measurement calibration, independently verified patient/phase/series correspondence and complete anatomical/clinical review are unavailable. Flat renderings are not actual 3D geometry; no clinical severity, shunt or procedural outcome is inferred.'
        state=f'vascular_ring_source_pmc4141344_fig{n}';letters=list('ab') if n==1 else list('abcdefgh') if n==2 else list('abcd') if n in [3,8] else ['whole'] if n==4 else list('abcde') if n==5 else list('ab') if n==9 else list('abc')
        rendered_panels=['whole'] if rendered=='whole' else list(rendered)
        context={'setting':'conceptual' if n==1 else 'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'local',
            'depicted_state':state,'selected_panels':list(clinical),'panel_types':{p:('Schematic' if p in schematic else 'CT') for p in letters},
            'panel_states':dict.fromkeys(letters,state),'source_schematic_panels':list(schematic),'source_ct_volume_rendering_panels':rendered_panels,
            'source_projected_ct_panels':list(projected),'virtual_bronchoscopy_panels':['d'] if n==3 else [],'all_panels_flat_renderings_only':n==4,
            'flat_renderings_are_spatial_geometry':False,'full_acquired_series_included':False,'independent_calibrated_measurements_verified':False,
            'complete_ring_components_directly_visualised':False,'cross_figure_patient_identity_verified':False,'same_series_registration_verified':False,
            'dynamic_airway_or_haemodynamic_function_verified':False,'complete_structure_coverage_verified':False}
        credit=permissions.findtext('copyright-statement','')+' '+', '.join(authors)+'. '+m['title']+'. DOI '+m['doi']+'. CC BY 4.0. Complete original publisher JPEG preserved byte-identically; no anatomical/clinical endorsement. NLM/PMC Article Dataset snapshot; may not reflect latest NLM data.'
        shown=f'Original Figure {n}: {title}. '+limits
        row={'id':PREFIX+str(n),'kind':'schematic' if n==1 else 'clinical-image','modality':'Schematic' if n==1 else 'CT','figure_number':n,
            'src':'/app/'+local.removeprefix('web/'),'width':source['width'],'height':source['height'],'sha256':source['sha256'],
            'source_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC4141344/','figure_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC4141344/#Fig'+str(n),
            'asset_source_url':url,'clinical_panels':list(clinical),'contains_schematic_panels':bool(schematic) and n!=1,'source_context':context,'image_state':state,
            'caption':shown,'alt':shown,'limits':limits,'source_caption_full':caption,'structures_visible':['Source-described '+title.lower()],
            'license':licence,'license_url':licence_url,'attribution':credit,'source_background':'white','rights_reviewed_on':'2026-10-06',
            'rights_review':'Original CC BY 4.0 XML, figure credits/captions and complete publisher MD5/SHA/pixels reviewed; anatomy not independently approved.'}
        if schematic:row['schematic_structures_visible']=['Source conceptual illustration: '+title]
        rows.append(row);entries.append((row,local,source))
    proof={'pmcid':'PMC4141344','doi':m['doi'],'title':m['title'],'metadata_sha256':META_SHA,'xml_sha256':sha(xml),'original_license':licence,
        'original_license_url':licence_url,'permissions_xml':ET.tostring(permissions,encoding='unicode'),'authors':authors,'figures':sources,
        'clinical_approval':False,'model_promoted':False,'source_pixels_changed':False,'source_caption_side_ambiguity_figures':[7],
        'source_reported_multiple_patient_figures':[2],'noncommercial_other_article_images_not_reused':'PMC9705143'}
    path=FOLDER/'original-source-review.json';path.write_text(json.dumps(proof,indent=2)+'\n');proof_sha=sha(path.read_bytes());assets=[]
    for row,local,source in entries:
        assets.append({'id':row['id'],'kind':'schematic' if row['figure_number']==1 else 'clinical_image','name':CONFIG[row['figure_number']][0],
            'local_path':local,'sha256':row['sha256'],'regions':['aorta','thorax','airway','pulmonary_artery'],'investigation_ids':[IDENT],
            'structure_ids':[],'requirement_coverage':{},'modality':row['modality'],'source_context':row['source_context'],
            'source':{'url':row['source_url'],'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],
                'license':{'name':licence,'url':licence_url,'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(path.relative_to(ROOT)),
                    'evidence_sha256':proof_sha,'attribution':row['attribution'],'reviewed_at':'2026-10-06'}},
            'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':source['decoded_pixel_sha256'],'highest_resolution_acquired_master_verified':False},
            'anatomical_review':{'status':'pending','reason':'Local clinical/schematic/rendered source panels do not independently validate complete anomaly geometry, directly seen ring components or function.'},
            'visual_review':{'status':'source_checked','sha256':row['sha256'],'reviewed_at':'2026-10-06','evidence_path':'docs/vascular-ring-published-source-review.md'}})
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text());data[IDENT]=[r for r in data.get(IDENT,[]) if not r['id'].startswith(PREFIX)]+rows
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/reporting-steps/cardiovascular.json';raw=path.read_text();start=raw.index('{',raw.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(raw,start)
    node['start']={'images':[PREFIX+'1',PREFIX+'11'],'module_illustrations':False}
    for i,figs in {0:[2,3,4,5,6,7,8,9],1:[2,3,5,10,11],2:[6,11]}.items():
        node['steps'][i]['images']=list(dict.fromkeys(node['steps'][i].get('images',[])+[PREFIX+str(n) for n in figs]))
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    (FOLDER/'packaged-source-images.json').write_text(json.dumps({'figures':[{'figure_number':r['figure_number'],'local_path':local,'sha256':r['sha256']} for r,local,s in entries],
        'clinical_approval':False,'model_promoted':False,'structure_coverage_granted':False},indent=2)+'\n')
    print('Eleven complete original arch/ring/sling figures preserved; schematic and flat rendered panels remain explicit.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
