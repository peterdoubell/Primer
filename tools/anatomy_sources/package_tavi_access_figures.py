#!/usr/bin/env python3
"""Preserve original historical access-route examples and keep flat renderings out of model claims."""
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
FOLDER=ROOT/'docs/tavi-access-published-source-review'
PREFIX='open-tavi-access-pmc3948900-fig'
IDENT='ra.ct-tavi'
META_SHA='1cbe518691caa0edf26f18e7e4b92fa2a015a9ef273b184a6485e46774fb8fc3'
CONFIG={21:('Iliofemoral pathway and orthogonal workspace views',list('adef'),list('b'),list('c')),
        22:('Iliac angulation on flat volume renderings',[],list('abc'),[]),
        23:('Paired subclavian pathway and local lumen views',list('abde'),list('cf'),[]),
        24:('Direct-aortic access locator and local plane',list('cd'),list('ab'),[])}

def sha(raw):return hashlib.sha256(raw).hexdigest()

def package(root):
    root.mkdir(parents=True,exist_ok=True);meta_path=root/'PMC3948900.1.json'
    if not meta_path.exists():
        with urllib.request.urlopen('https://pmc-oa-opendata.s3.amazonaws.com/PMC3948900.1/PMC3948900.1.json',timeout=60) as r:meta_path.write_bytes(r.read())
    if sha(meta_path.read_bytes())!=META_SHA:raise ValueError('Reviewed metadata differs')
    m=json.loads(meta_path.read_text());http=lambda u:u.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
    if m['is_retracted'] is not False:raise ValueError('Source retraction differs')
    xml=download_verified(http(m['xml_url']),root/'PMC3948900.1.xml');x=ET.fromstring(xml);permissions=x.find('.//article-meta/permissions')
    licence,licence_url=exact_license(permissions)
    if licence!='CC BY 2.0':raise ValueError('Original grant differs')
    authors=[' '.join([e.findtext('given-names',''),e.findtext('surname','')]) for e in x.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]
    rows=[];sources=[];evidence_input=[]
    FOLDER.mkdir(parents=True,exist_ok=True)
    for n,(title,clinical,rendered,projected) in CONFIG.items():
        f=x.find('.//fig[@id="Fig'+str(n)+'"]');caption=' '.join(f.find('caption').itertext())
        if (f.find('attrib') is not None or f.find('permissions') is not None
                or any(w in caption.lower() for w in ['source:','courtesy','reprinted','reproduced','adapted'])):
            raise ValueError('Separate figure credit needs review')
        filename=f.find('graphic').get('{http://www.w3.org/1999/xlink}href');url=http(next(u for u in m['media_urls'] if '/'+filename+'?' in u))
        raw=download_verified(url,root/filename)
        with Image.open(root/filename) as im:
            im.load();source={'figure_number':n,'source_caption':caption,'source_media_url':url,'publisher_md5_verified':True,
                'sha256':sha(raw),'width':im.width,'height':im.height,'pixel_mode':im.mode,'decoded_pixel_sha256':sha(im.tobytes()),
                'source_pixels_changed':False,'method':'complete_original_publisher_jpeg_byte_identical'}
        sources.append(source);local=f'web/reference-media/radiology-open/tavi-access-pmc3948900-fig{n}.jpg';(ROOT/local).write_bytes(raw)
        specific={21:'Panels a/d/e/f contain CT curved/orthogonal workspace views; d/e/f also retain rendered insets. Panel b is flat VR and c projected/MIP artwork. No native volume, complete calibrated lumen minima or proven same-series registration is supplied.',
            22:'All a/b/c panels are flat CT volume renderings. The original 98-degree angle is a source annotation, not an independently calibrated centreline/clinical tortuosity measure. No acquired clinical CT panel or actual 3D geometry is selected.',
            23:'Source a/b show right/left subclavian views and d/e local measurement workspaces; c/f are flat VR. Full subclavian/axillary route, branch/coronary-graft relations and independent laterality/site measurement remain incomplete.',
            24:'Source c/d are local curved/orthogonal workspaces; a/b are flat VR. The original 8.5-cm puncture-range description is historical procedure/device-era context, not a current universal safe access rule.'}[n]
        limits=specific+' Original complete JPEG/annotations are preserved. Cross-figure patient identity, acquisition/phase, source calibration, full route coverage and current device/sheath suitability are not independently verified. No geometry, access recommendation or procedure outcome is derived from the picture.'
        state=f'tavi_access_source_pmc3948900_fig{n}';letters=list('abcdef') if n in (21,23) else list('abc') if n==22 else list('abcd')
        context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'local',
            'depicted_state':state,'selected_panels':clinical,'panel_types':dict.fromkeys(letters,'CT'),
            'panel_states':dict.fromkeys(letters,state),'source_ct_volume_rendering_panels':rendered,
            'source_projected_ct_panels':projected,'workspace_panels_with_mixed_2D_3D_subviews':list('def') if n==21 else list('de') if n==23 else [],
            'all_panels_flat_renderings_only':n==22,'flat_renderings_are_spatial_geometry':False,
            'full_acquired_series_included':False,'complete_access_route_or_minimum_lumen_verified':False,
            'independent_calibrated_measurements_verified':False,'cross_figure_patient_identity_verified':False,
            'current_device_suitability_or_procedural_safety_verified':False}
        credit=permissions.findtext('copyright-statement','')+' '+', '.join(authors)+'. '+m['title']+'. DOI '+m['doi']+'. CC BY 2.0. Complete original publisher JPEG preserved byte-identically. Historical procedure/device illustrations are not current instructions. NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.'
        caption=f'Original Figure {n}: {title}. '+limits
        row={'id':PREFIX+str(n),'kind':'clinical-image','modality':'CT','figure_number':n,
            'src':'/app/'+local.removeprefix('web/'),'width':source['width'],'height':source['height'],'sha256':source['sha256'],
            'source_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC3948900/','figure_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC3948900/#Fig'+str(n),
            'asset_source_url':url,'clinical_panels':clinical,'source_context':context,'image_state':state,
            'caption':caption,'alt':caption,'limits':limits,'source_caption_full':source['source_caption'],
            'structures_visible':['Source-described '+title.lower()],'license':licence,'license_url':licence_url,'attribution':credit,
            'source_background':'white','rights_reviewed_on':'2026-10-06','rights_review':'Original CC BY 2.0 XML/captions and complete publisher figure MD5/SHA/pixels reviewed; separately credited manufacturer figures excluded.'}
        rows.append(row);evidence_input.append((row,local,source))
    proof={'pmcid':'PMC3948900','doi':m['doi'],'title':m['title'],'metadata_sha256':META_SHA,'xml_sha256':sha(xml),
        'original_license':licence,'original_license_url':licence_url,'permissions_xml':ET.tostring(permissions,encoding='unicode'),
        'authors':authors,'figures':sources,'separately_credited_manufacturer_figures_not_acquired':[4,6,7],
        'clinical_approval':False,'model_promoted':False,'source_pixels_changed':False}
    path=FOLDER/'original-source-review.json';path.write_text(json.dumps(proof,indent=2)+'\n');proof_sha=sha(path.read_bytes())
    assets=[]
    for row,local,source in evidence_input:
        assets.append({'id':row['id'],'kind':'clinical_image','name':CONFIG[row['figure_number']][0],'local_path':local,
            'sha256':row['sha256'],'regions':['aorta','iliofemoral_access','thorax'],'investigation_ids':[IDENT],
            'structure_ids':[],'requirement_coverage':{},'modality':'CT','source_context':row['source_context'],
            'source':{'url':row['source_url'],'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],
                'license':{'name':licence,'url':licence_url,'commercial_use':True,'redistribution':True,'review_status':'verified',
                    'evidence_path':str(path.relative_to(ROOT)),'evidence_sha256':proof_sha,'attribution':row['attribution'],'reviewed_at':'2026-10-06'}},
            'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':source['decoded_pixel_sha256'],'highest_resolution_acquired_master_verified':False},
            'anatomical_review':{'status':'pending','reason':'Published local workspaces/flat renderings do not independently validate every access wall/lumen, current-device geometry or procedural safety.'},
            'visual_review':{'status':'source_checked','sha256':row['sha256'],'reviewed_at':'2026-10-06','evidence_path':'docs/tavi-access-published-source-review.md'}})
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text());data[IDENT]=[r for r in data[IDENT] if not r['id'].startswith(PREFIX)]+rows
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/reporting-steps/cardiovascular.json';raw=path.read_text();start=raw.index('{',raw.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(raw,start)
    node['steps'][4]['images']=list(dict.fromkeys(node['steps'][4].get('images',[])+[r['id'] for r in rows]))
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    (FOLDER/'packaged-source-images.json').write_text(json.dumps({'figures':[{'figure_number':r['figure_number'],'local_path':local,'sha256':r['sha256']} for r,local,s in evidence_input],
        'clinical_approval':False,'model_promoted':False,'structure_coverage_granted':False},indent=2)+'\n')
    print('Four complete historical CT access-workspace/flat-render figures preserved under original CC BY 2.0.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    package(p.parse_args().source_root)
