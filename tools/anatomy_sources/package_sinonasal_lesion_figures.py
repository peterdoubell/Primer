#!/usr/bin/env python3
"""Preserve original acquired sinonasal lesion panels with source sequence and caption limits."""
import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PIL import Image
from primer import radiology_catalog as catalog
from primer.curriculum import Curriculum
from tools.check_radiology_fidelity import digest
from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence

ROOT = Path(__file__).resolve().parents[2]
IDENT = 'ra.mri-sinuses'
PREFIX = 'open-sinonasal-lesion-pmc11392720-fig'
OUT = ROOT/'docs/sinonasal-lesion-source-review'
SOURCE = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11392720/'
# Values are original source panel roles, not independently verified acquisition headers.
CONFIG = {
 2: ('MRI', {'A':'MRI','B':'MRI'}, {'A':'axial T1 postcontrast','B':'axial T2'}, 'Sphenoid/orbital/clival source lesion'),
 3: ('MRI', dict.fromkeys('ABC','MRI'), {'A':'axial T1','B':'axial T1 postcontrast','C':'sagittal T1 postcontrast'}, 'Ethmoid/extraconal source lesion'),
 4: ('MRI', {'A':'CT','B':'MRI','C':'MRI'}, {'A':'coronal CT','B':'axial T2','C':'coronal T1 postcontrast'}, 'Maxillary/palatal source lesion with separate CT'),
 5: ('MRI', dict.fromkeys('ABCD','MRI'), {'A':'coronal T2','B':'coronal T1 postcontrast','C':'axial T1','D':'axial DWI'}, 'Maxillary/orbital/intracranial source lesion'),
 6: ('MRI', dict.fromkeys('AB','MRI'), {'A':'coronal T1 postcontrast','B':'coronal T2'}, 'Anterior cranial/orbital source lesion'),
 7: ('MRI', {'A':'MRI','B':'MRI','C':'MRI','D':'CT','E':'MRI','F':'Nuclear medicine'}, {'A':'coronal T2','B':'axial T1 postcontrast','C':'axial T2','D':'axial CT bone','E':'axial DWI','F':'caption PET; displayed fused PET/CT'}, 'Nasal/orbital source lesion across MRI CT and PET display'),
 8: ('MRI', dict.fromkeys('ABC','MRI'), {'A':'axial DWI','B':'coronal T2','C':'coronal T1 postcontrast'}, 'Maxillary/ethmoid source lymphoma example'),
 9: ('MRI', dict.fromkeys('ABCDEF','MRI'), {'A':'coronal T2','B':'coronal T1 postcontrast','C':'axial DWI','D':'axial T1 postcontrast','E':'sagittal T1 postcontrast','F':'coronal T1 postcontrast'}, 'Separate rhabdomyosarcoma and meningioma source examples'),
 10: ('MRI', dict.fromkeys('AB','MRI'), {'A':'axial T2','B':'axial T1 postcontrast'}, 'Maxillary source papilloma example'),
 11: ('MRI', {'whole':'MRI'}, {'whole':'axial T2'}, 'Maxillary/nasal source polyp example'),
 12: ('CT', dict.fromkeys('ABC','CT'), {'A':'axial','B':'caption sagittal; displayed coronal','C':'caption coronal; displayed sagittal'}, 'Sphenoid source retention-cyst example; plane disagreement'),
 13: ('CT', dict.fromkeys('ABC','CT'), {'A':'sagittal','B':'coronal','C':'axial'}, 'Source expansile lesion with uncertain diagnostic label'),
 14: ('MRI', dict.fromkeys('AB','MRI'), {'A':'sagittal T1','B':'source coraxial T1 wording; oblique displayed image'}, 'Anterior nasal source cyst/tract; wording uncertainty'),
}
COMMON = (' Complete original publisher figure and annotations retained. Source-local selected sequences and views are '
          'distinct from a whole native acquisition or complete 3D extent. Source diagnosis and laterality are attributed '
          'to the publication; independent anatomy, histology and native orientation validation remain pending. '
          'No calibrated ADC, enhancement, full nerve/wall geometry or clinical approval is supplied.')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def package(root):
    OUT.mkdir(parents=True, exist_ok=True)
    metadata = root/'PMC11392720.1.json'; m = json.loads(metadata.read_text())
    if m['pmcid'] != 'PMC11392720' or m['is_retracted'] is not False:
        raise ValueError('Source identity/retraction differs')
    http = lambda u: u.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
    raw_xml = download_verified(http(m['xml_url']), root/'PMC11392720.1.xml')
    tree = E.fromstring(raw_xml); permission = tree.find('.//article-meta/permissions')
    grant, grant_url = exact_license(permission)
    if grant != 'CC BY 4.0': raise ValueError('Source grant differs')
    authors = [' '.join([n.findtext('given-names',''), n.findtext('surname','')]) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]
    rows, facts, paths = [], [], []
    for number, (primary, types, sequences, title) in CONFIG.items():
        figure = tree.find('.//fig[@id="F'+str(number)+'"]'); caption = ' '.join(figure.find('caption').itertext())
        if figure.find('attrib') is not None or figure.find('permissions') is not None or any(w in caption.lower() for w in ['courtesy','reproduced','reprinted','adapted','modified from','permission']):
            raise ValueError('Separate figure rights require review')
        filename = figure.find('graphic').get('{http://www.w3.org/1999/xlink}href')
        pointers = [u for u in m['media_urls'] if '/'+filename+'?' in u]
        if len(pointers) != 1: raise ValueError('Source pointer ambiguous')
        url = http(pointers[0]); raw = download_verified(url, root/filename)
        with Image.open(root/filename) as image:
            image.load(); fact = {'figure_number':number,'source_caption_full':caption,'source_media_url':url,
                                 'sha256':sha(raw),'decoded_pixel_sha256':sha(image.tobytes()),
                                 'width':image.width,'height':image.height,'pixel_mode':image.mode,
                                 'publisher_MD5_verified':True,'complete_original_pixels_inspected':True,'source_pixels_changed':False}
        special = ''
        if number in [5,7,8,9]: special += 'DWI is shown without an acquired ADC map here; source restricted-diffusion labels do not supply independently verified restriction or an ADC measurement. '
        if number == 7: special += 'Panel F is a fused PET/CT display although the caption says PET; no tracer, SUV calibration or metabolic specificity is independently established. '
        if number == 8: special += 'Source pathology/CD5/CD10 statements are publication text, not image-derived molecular identity. '
        if number == 9: special += 'A/B/C and D/E/F are separate lesion examples, not one progression or one registered patient dataset. '
        if number == 12: special += 'Source caption labels B sagittal and C coronal, but displayed B is coronal and C sagittal. Original captions/pixels retained with this disagreement; no plane-specific coverage granted. '
        if number == 13: special += 'Source caption says possibly pleomorphic adenoma; this uncertain diagnosis is not upgraded to histological confirmation. '
        if number == 14: special += 'Source heading says dermoid, body says desmoid and B uses coraxial wording. These original uncertainties are retained; no unique tissue diagnosis, axis or complete tract is inferred. '
        limits = special+COMMON
        selected = [panel for panel, modality in types.items() if modality == primary]
        context = {'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'local',
                   'depicted_state':'source_sinonasal_lesion_examples','selected_panels':selected,'panel_types':types,
                   'panel_states':dict.fromkeys(selected,'source_sinonasal_lesion_examples'),
                   'source_sequence_and_plane_roles':sequences,'independent_native_series_registration_or_calibration_verified':False,
                   'full_native_anatomical_or_3D_extent_verified':False}
        if number == 9: context['source_case_groups'] = {'rhabdomyosarcoma_example':['A','B','C'],'meningioma_example':['D','E','F']}
        if number == 12: context['source_caption_plane_disagreement'] = True
        if number == 14: context['source_diagnostic_and_plane_wording_uncertainty'] = True
        local = f'web/reference-media/radiology-open/sinonasal-lesion-pmc11392720-fig{number}.jpg'; (ROOT/local).write_bytes(raw)
        attribution = ', '.join(authors)+'. '+m['title']+'. DOI '+m['doi']+'. CC BY 4.0. Complete original figure retained. NLM/PMC dataset snapshot may not reflect latest NLM data.'
        row = {'id':PREFIX+str(number),'kind':'clinical-image','modality':primary,'figure_number':number,
               'src':'/app/'+local.removeprefix('web/'),'sha256':fact['sha256'],'width':fact['width'],'height':fact['height'],
               'source_url':SOURCE,'figure_url':SOURCE+'#F'+str(number),'asset_source_url':url,'clinical_panels':selected,
               'source_context':context,'image_state':'source_sinonasal_lesion_examples','caption':f'Original Figure {number}: {title}. '+limits,
               'alt':f'Original Figure {number}: {title}. '+limits,'limits':limits,'source_caption_full':caption,
               'structures_visible':['Source-local '+title.lower()],'license':grant,'license_url':grant_url,
               'attribution':attribution,'rights_reviewed_on':'2026-10-07','rights_review':'Original explicit article grant and whole unchanged figure checked; illustrator Figure1 held.'}
        if set(types.values())-{primary}:
            row['ancillary_panels'] = [{'kind':kind,'panels':[p for p,v in types.items() if v==kind],
                                       'structures_visible':['Separate source '+kind+' example'],
                                       'limits':'Actual separately displayed modality; no independent whole-series registration, calibration or unique diagnosis.'} for kind in sorted(set(types.values())-{primary})]
        rows.append(row); facts.append(fact); paths.append(local)
    proof = {'pmcid':m['pmcid'],'doi':m['doi'],'title':m['title'],'authors':authors,'metadata_sha256':sha(metadata.read_bytes()),
             'xml_sha256':sha(raw_xml),'permissions_xml':E.tostring(permission,encoding='unicode'),'original_license':grant,
             'original_license_url':grant_url,'figures':facts,'held_figures':[{'figure_number':1,'source_caption':' '.join(tree.find('.//fig[@id="F1"]/caption').itertext()),
             'reason':'Illustrator permission says use in this article; broader reuse scope unresolved.','runtime_promoted':False}],
             'clinical_approval':False,'model_promoted':False,'structure_coverage_granted':False}
    proof_path = OUT/'original-source-review.json'; proof_path.write_text(json.dumps(proof,indent=2)+'\n')
    assets = []
    for row, local, fact in zip(rows, paths, facts):
        assets.append({'id':row['id'],'kind':'clinical_image','name':row['caption'].split('. ')[0],'local_path':local,
                       'sha256':row['sha256'],'modality':row['modality'],'investigation_ids':[IDENT],'structure_ids':[],
                       'requirement_coverage':{},'source_context':row['source_context'],
                       'source':{'url':SOURCE,'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],
                                 'license':{'name':grant,'url':grant_url,'commercial_use':True,'redistribution':True,'review_status':'verified',
                                            'evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_path.read_bytes()),
                                            'attribution':row['attribution'],'reviewed_at':'2026-10-07'}},
                       'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':fact['decoded_pixel_sha256'],
                                           'highest_resolution_acquired_master_verified':False},
                       'anatomical_review':{'status':'pending','reason':'Original local stills and source roles do not establish full anatomy; caption uncertainties retained.'},
                       'visual_review':{'status':'source_checked','sha256':row['sha256'],'evidence_path':'docs/sinonasal-lesion-source-review.md','reviewed_at':'2026-10-07'}})
    path = ROOT/'data/radiology/radiology-open-images.json'; data = json.loads(path.read_text())
    data[IDENT] = [r for r in data.get(IDENT,[]) if not r['id'].startswith(PREFIX)]+rows
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path = ROOT/'data/radiology/reporting-steps/head-neck.json'; raw = path.read_text()
    start = raw.index('{',raw.index('"'+IDENT+'"')); node,end = json.JSONDecoder().raw_decode(raw,start)
    node.setdefault('start',{}).update(images=[PREFIX+'2',PREFIX+'4'],module_illustrations=False)
    for index, numbers in {0:[2,5,6,10,11,12,13],1:[10,11],3:[2,3,4,5,6,7,8,9,10,12,13,14],4:[2,3,4,5,6,7,8,9,14]}.items():
        node['steps'][index]['images'] = list(dict.fromkeys(node['steps'][index].get('images',[])+[PREFIX+str(n) for n in numbers]))
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    for value in vars(catalog).values():
        if callable(getattr(value,'cache_clear',None)): value.cache_clear()
    ref = catalog.detail(Curriculum(),catalog.resolve(IDENT))['radiology_reference']
    path = ROOT/'data/radiology/non-msk-structure-requirements.json'; data = json.loads(path.read_text())
    for item in data['investigations']:
        if item['investigation_id']==IDENT: item['source_contract_sha256']=digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    path.write_text(json.dumps(data,indent=2)+'\n')
    print('13 unchanged original sinonasal lesion figures; MRI/CT/nuclear roles and source caption uncertainties retained; illustrator figure held')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--source-root',type=Path,required=True)
    package(parser.parse_args().source_root)
