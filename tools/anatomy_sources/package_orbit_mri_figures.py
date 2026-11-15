#!/usr/bin/env python3
"""Preserve original acquired orbital panels with source sequence and caption limits."""
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
IDENT = 'ra.ct-mri-eye'
PREFIX = 'open-orbit-mri-pmc6095049-fig'
OUT = ROOT/'docs/orbit-mri-published-source-review'
SOURCE = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC6095049/'
# Values are original source panel roles, not independently verified acquisition headers.
CONFIG = {
 1: ('Schematic', {'whole':'Schematic'}, {'whole':'conceptual compartment diagram'}, 'Original orbital compartment schematic'),
 2: ('MRI', dict.fromkeys('abc','MRI'), {'a':'caption axial fat-suppressed T1','b':'T2 description not explicitly letter-paired','c':'postcontrast T1 description not explicitly letter-paired'}, 'Source childhood ocular lesion'),
 3: ('MRI', dict.fromkeys('ab','MRI'), {'a':'axial fat-suppressed T2','b':'postcontrast axial fat-suppressed T1'}, 'Source choroidal metastatic case'),
 4: ('MRI', dict.fromkeys('abc','MRI'), {'a':'T1','b':'T2','c':'postcontrast'}, 'Source choroidal melanoma case'),
 5: ('MRI', dict.fromkeys('ab','MRI'), {'a':'axial fat-suppressed T2','b':'sagittal T2'}, 'Source coloboma and lens example'),
 6: ('MRI', dict.fromkeys('ab','MRI'), {'a':'coronal fat-suppressed T2','b':'caption coronal; displayed axial T2'}, 'Source adult persistent-vitreous case; plane disagreement'),
 7: ('MRI', dict.fromkeys('abc','MRI'), {'a':'axial T1','b':'fat-suppressed T2','c':'source enhancement example'}, 'Source childhood optic-region lesion'),
 8: ('MRI', dict.fromkeys('abc','MRI'), {'a':'axial T2','b':'sequence/contrast role unreported in caption','c':'postcontrast fat-suppressed T1'}, 'Source optic nerve signal/enhancement example'),
 9: ('MRI', dict.fromkeys('abcd','MRI'), {'a':'axial fat-suppressed T2','b':'coronal fat-suppressed T2','c':'postcontrast axial fat-suppressed T1','d':'postcontrast axial fat-suppressed T1'}, 'Source orbit/skull-base lesion'),
 10: ('MRI', dict.fromkeys('ab','MRI'), {'a':'coronal T1','b':'sagittal T2'}, 'Source muscle-belly and tendon comparison'),
 11: ('MRI', dict.fromkeys('abc','MRI'), {'a':'coronal T1','b':'sagittal T2','c':'postcontrast axial T1'}, 'Source inflammatory/lacrimal-region example'),
 12: ('MRI', dict.fromkeys('abc','MRI'), {'a':'coronal fat-suppressed T2','b':'caption pre/postcontrast both reference b','c':'displayed third panel unreferenced by caption'}, 'Source myositis example; incomplete phase labels'),
 13: ('MRI', dict.fromkeys('ab','MRI'), {'a':'caption coronal T2; displayed axial','b':'coronal fat-suppressed T1'}, 'Source lacrimal-sac-region lesion; plane disagreement'),
 14: ('MRI', dict.fromkeys('ab','MRI'), {'a':'T2','b':'postcontrast fat-suppressed T1'}, 'Source cavernous-region example'),
 15: ('MRI', dict.fromkeys('ab','MRI'), {'a':'coronal T1','b':'fat-suppressed axial postcontrast T1'}, 'Source fatty lesion example'),
 16: ('MRI', dict.fromkeys('ab','MRI'), {'a':'caption sagittal T2; displayed axial','b':'caption coronal T1; displayed sagittal'}, 'Source cystic lesion example; plane disagreements'),
 17: ('MRI', dict.fromkeys('abc','MRI'), {'a':'coronal T1','b':'caption coronal T2; displayed axial','c':'caption coronal postcontrast T1; displayed axial'}, 'Source vascular-pattern lesion; plane disagreements'),
}
AGES={2:(4,'female'),3:(62,'female'),4:(57,'male'),5:(20,'male'),6:(38,'male'),7:(7,'male'),8:(27,'male'),9:(56,'male'),10:(75,'male'),11:(45,'male'),12:(45,'female'),13:(50,'female'),14:(50,'male'),15:(33,'female'),16:(75,'male'),17:(43,'female')}

COMMON = (' Complete original publisher figure and annotations retained. Source-local selected sequences and views are '
          'distinct from a whole native acquisition or complete 3D extent. Source diagnosis and laterality are attributed '
          'to the publication; independent anatomy, histology and native orientation validation remain pending. '
          'No independently calibrated ADC, enhancement, full nerve/wall geometry or clinical approval is supplied.')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def package(root):
    from tools.anatomy_sources.upgrade_orbit_PDF_masters import upgrade
    if not (root/"PMC6095049.1.pdf").is_file() or not (root/"pdf-original-images/image-033.png").is_file():
        raise ValueError("Original PDF and complete extracted masters required before packaging")
    OUT.mkdir(parents=True, exist_ok=True)
    archive = OUT/'packaged-source-images.json'
    replaced = json.loads(archive.read_text())['replaced_investigation_images'] if archive.exists() else catalog.detail(Curriculum(),catalog.resolve(IDENT))['radiology_reference']['key_images']
    metadata = root/'PMC6095049.1.json'; m = json.loads(metadata.read_text())
    if m['pmcid'] != 'PMC6095049' or m['is_retracted'] is not False:
        raise ValueError('Source identity/retraction differs')
    http = lambda u: u.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
    raw_xml = download_verified(http(m['xml_url']), root/'PMC6095049.1.xml')
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
        if number == 1: special += 'Conceptual compartment schematic, not a clinical image, native surface model or complete orbital anatomy. '
        if number in [2,7]: special += 'Original paediatric source case, not an adult/current reader patient. '
        if number == 2: special += 'Caption does not explicitly letter-pair all sequence descriptions; roles remain source-order statements, not independently verified headers. '
        if number == 4: special += 'Original 15×9×15 mm and histopathology are source statements, not independently calibrated dimensions or new tissue confirmation. '
        if number == 6: special += 'Caption calls b coronal, whereas displayed b is axial; disagreement retained without relabelling. '
        if number == 8: special += 'Displayed b has no explicit sequence/contrast role in the source caption; no role is invented. '
        if number == 12: special += 'Caption refers to b for both pre/postcontrast and does not reference displayed c. Original phase uncertainty retained without assigning new quantitative enhancement. '
        if number == 13: special += 'Caption calls a coronal, whereas displayed a is axial; disagreement retained. '
        if number == 16: special += 'Caption calls a sagittal and b coronal, whereas displayed a is axial and b sagittal; disagreement retained. '
        if number == 17: special += 'Caption calls b/c coronal, whereas displayed b/c are axial. Source historic cavernous-hemangioma wording and static enhancement do not independently establish lesion identity, haemodynamics or fill-in kinetics. '
        limits = special+COMMON
        selected = [panel for panel, modality in types.items() if modality == primary]
        context = {'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'local',
                   'depicted_state':'source_orbital_MRI_case_examples','selected_panels':selected,'panel_types':types,
                   'panel_states':dict.fromkeys(selected,'source_orbital_MRI_case_examples'),
                   'source_sequence_and_plane_roles':sequences,'independent_native_series_registration_or_calibration_verified':False,
                   'full_native_anatomical_or_3D_extent_verified':False}
        context['setting']='conceptual' if number==1 else 'in_vivo'
        if number==1:
            context['panel_states']={'whole':'conceptual_orbital_compartment_schematic'}
            context['depicted_state']='conceptual_orbital_compartment_schematic'
        else:
            age,sex=AGES[number];context['population']={'life_stage':'immature' if age<18 else 'adult','source_age_years':age,'source_sex':sex}
        if number in [6,13,16,17]:context['source_caption_plane_disagreement']=True
        if number in [2,8,12]:context['source_panel_sequence_or_phase_uncertainty']=True
        local = f'web/reference-media/radiology-open/orbit-mri-pmc6095049-fig{number}.jpg'; (ROOT/local).write_bytes(raw)
        attribution = ', '.join(authors)+'. '+m['title']+'. DOI '+m['doi']+'. CC BY 4.0. Complete original figure retained. NLM/PMC dataset snapshot may not reflect latest NLM data.'
        row = {'id':PREFIX+str(number),'kind':'schematic' if primary=='Schematic' else 'clinical-image','modality':primary,'figure_number':number,
               'src':'/app/'+local.removeprefix('web/'),'sha256':fact['sha256'],'width':fact['width'],'height':fact['height'],
               'source_url':SOURCE,'figure_url':SOURCE+'#F'+str(number),'asset_source_url':url,('schematic_panels' if primary=='Schematic' else 'clinical_panels'):selected,
               'source_context':context,'image_state':context['depicted_state'],'caption':f'Original Figure {number}: {title}. '+limits,
               'alt':f'Original Figure {number}: {title}. '+limits,'limits':limits,'source_caption_full':caption,
               'structures_visible':['Source-local '+title.lower()],'license':grant,'license_url':grant_url,
               'attribution':attribution,'rights_reviewed_on':'2026-10-07','rights_review':'Original explicit article grant and whole unchanged figure checked; Original clinical and conceptual roles kept separate; no new anatomical coverage.'}
        if set(types.values())-{primary}:
            row['ancillary_panels'] = [{'kind':kind,'panels':[p for p,v in types.items() if v==kind],
                                       'structures_visible':['Separate source '+kind+' example'],
                                       'limits':'Actual separately displayed modality; no independent whole-series registration, calibration or unique diagnosis.'} for kind in sorted(set(types.values())-{primary})]
        rows.append(row); facts.append(fact); paths.append(local)
    proof = {'pmcid':m['pmcid'],'doi':m['doi'],'title':m['title'],'authors':authors,'metadata_sha256':sha(metadata.read_bytes()),
             'xml_sha256':sha(raw_xml),'permissions_xml':E.tostring(permission,encoding='unicode'),'original_license':grant,
             'original_license_url':grant_url,'figures':facts,'held_figures':[],
             'clinical_approval':False,'model_promoted':False,'structure_coverage_granted':False}
    proof_path = OUT/'original-source-review.json'; proof_path.write_text(json.dumps(proof,indent=2)+'\n')
    assets = []
    for row, local, fact in zip(rows, paths, facts):
        assets.append({'id':row['id'],'kind':'schematic' if row['modality']=='Schematic' else 'clinical_image','name':row['caption'].split('. ')[0],'local_path':local,
                       'sha256':row['sha256'],'modality':row['modality'],'investigation_ids':[IDENT],'structure_ids':[],
                       'requirement_coverage':{},'source_context':row['source_context'],
                       'source':{'url':SOURCE,'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],
                                 'license':{'name':grant,'url':grant_url,'commercial_use':True,'redistribution':True,'review_status':'verified',
                                            'evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_path.read_bytes()),
                                            'attribution':row['attribution'],'reviewed_at':'2026-10-07'}},
                       'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':fact['decoded_pixel_sha256'],
                                           'highest_resolution_acquired_master_verified':False},
                       'anatomical_review':{'status':'pending','reason':'Original local stills and source roles do not establish full anatomy; caption uncertainties retained.'},
                       'visual_review':{'status':'source_checked','sha256':row['sha256'],'evidence_path':'docs/orbit-mri-published-source-review.md','reviewed_at':'2026-10-07'}})
    path = ROOT/'data/radiology/radiology-open-images.json'; data = json.loads(path.read_text())
    data[IDENT] = [r for r in data.get(IDENT,[]) if not r['id'].startswith(PREFIX)]+rows
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path = ROOT/'data/radiology/investigation-overrides-non-msk.json'; data = json.loads(path.read_text()); data[IDENT]['key_images']=[]; path.write_text(json.dumps(data,indent=2)+'\n')
    path = ROOT/'data/radiology/investigation-source-images.json'; raw = path.read_text()
    if '"'+IDENT+'"' in raw:
        start = raw.index('[',raw.index('"'+IDENT+'"')); old,end = json.JSONDecoder().raw_decode(raw,start); path.write_text(raw[:start]+'[]'+raw[end:])
    archive.write_text(json.dumps({'replaced_investigation_images':replaced,'clinical_approval':False,'structure_coverage_granted':False},indent=2)+'\n')
    removed_ids = {r['id'] for r in replaced}
    path = ROOT/'data/radiology/reporting-steps/head-neck.json'; raw = path.read_text()
    start = raw.index('{',raw.index('"'+IDENT+'"')); node,end = json.JSONDecoder().raw_decode(raw,start)
    node.setdefault('start',{}).update(images=[PREFIX+'3',PREFIX+'8'],module_illustrations=False)
    for index, numbers in {0:[2,3,4,5,6],1:[1,3,4,9,11,13,15,16,17],2:[7,8,10,11,12],3:[7,8,9,14],4:[9,13]}.items():
        node['steps'][index]['images'] = list(dict.fromkeys([id for id in node['steps'][index].get('images',[]) if id not in removed_ids]+[PREFIX+str(n) for n in numbers]))
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    for value in vars(catalog).values():
        if callable(getattr(value,'cache_clear',None)): value.cache_clear()
    ref = catalog.detail(Curriculum(),catalog.resolve(IDENT))['radiology_reference']
    path = ROOT/'data/radiology/non-msk-structure-requirements.json'; data = json.loads(path.read_text())
    for item in data['investigations']:
        if item['investigation_id']==IDENT: item['source_contract_sha256']=digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    path.write_text(json.dumps(data,indent=2)+'\n')
    upgrade(root)
    print('16 original orbital MRI figures and one original schematic preserved; age/phase/plane limits retained')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--source-root',type=Path,required=True)
    package(parser.parse_args().source_root)
