#!/usr/bin/env python3
"""Preserve original acquired temporal-bone panels with source sequence and caption limits."""
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
IDENT = 'ra.ct-temporal-bone'
PREFIX = 'open-temporal-bone-pmc11913933-fig'
OUT = ROOT/'docs/temporal-bone-published-source-review'
SOURCE = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11913933/'
# Values are original source panel roles, not independently verified acquisition headers.
CONFIG = {
 1: ('CT', dict.fromkeys('ABCDEFGHI','CT'), {'A':'coronal','B':'axial','C':'axial','D':'coronal','E':'axial','F':'coronal','G':'axial','H':'axial','I':'coronal'}, 'Separate healthy and pathological ossicular/scutum cases'),
 2: ('CT', dict.fromkeys('ABCD','CT'), {'A':'sagittal unenhanced CT','B':'axial unenhanced CT','C':'sagittal CT','D':'axial CT'}, 'Separate canal-wall-down and canal-wall-up postoperative cases'),
 3: ('CT', dict.fromkeys('ABCD','CT'), {'A':'axial','B':'coronal','C':'coronal','D':'coronal'}, 'Separate labyrinthine tegmen and cochlear erosion cases'),
 4: ('MRI', dict.fromkeys('ABCD','MRI'), {'A':'axial non-EPI DWI','B':'coronal non-EPI DWI','C':'coronal ADC map with source ROI','D':'original HASTE DWI/T2 SPACE colour fusion'}, 'Source DWI ADC and fused anatomical comparison'),
 5: ('MRI', dict.fromkeys('ABCD','MRI'), {'A':'axial CISS','B':'sagittal CISS','C':'axial CISS','D':'coronal CISS'}, 'Source postoperative herniation and inner-ear interface examples'),
 6: ('MRI', {'A':'CT','B':'MRI','C':'MRI','D':'MRI'}, {'A':'sagittal CT','B':'T2 weighted MRI','C':'T1 weighted MRI','D':'HASTE DWI with original ADC inset'}, 'Source postoperative CT MRI and ADC-inset comparison'),
 7: ('MRI', {'A':'MRI','B':'MRI','C':'CT','D':'MRI','E':'MRI','F':'CT','G':'MRI'}, {'A':'coronal HASTE DWI','B':'axial T1','C':'coronal CT','D':'coronal HASTE DWI','E':'coronal HASTE DWI','F':'axial CT','G':'subsequent coronal HASTE DWI after wax removal'}, 'Separate graft and cerumen DWI mimics'),
}

COMMON = (' Complete original publisher figure and annotations retained. Source-local selected sequences and views are '
          'distinct from a whole native acquisition or complete 3D extent. Source diagnosis and laterality are attributed '
          'to the publication; independent anatomy, histology and native orientation validation remain pending. '
          'No independently calibrated ADC, enhancement, full nerve/wall geometry or clinical approval is supplied.')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def package(root):
    OUT.mkdir(parents=True, exist_ok=True)
    archive = OUT/'packaged-source-images.json'
    replaced = json.loads(archive.read_text())['replaced_investigation_images'] if archive.exists() else catalog.detail(Curriculum(),catalog.resolve(IDENT))['radiology_reference']['key_images']
    metadata = root/'PMC11913933.1.json'; m = json.loads(metadata.read_text())
    if m['pmcid'] != 'PMC11913933' or m['is_retracted'] is not False:
        raise ValueError('Source identity/retraction differs')
    http = lambda u: u.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
    raw_xml = download_verified(http(m['xml_url']), root/'PMC11913933.1.xml')
    tree = E.fromstring(raw_xml); permission = tree.find('.//article-meta/permissions')
    grant, grant_url = exact_license(permission)
    if grant != 'CC BY 4.0': raise ValueError('Source grant differs')
    authors = [' '.join([n.findtext('given-names',''), n.findtext('surname','')]) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]
    rows, facts, paths = [], [], []
    for number, (primary, types, sequences, title) in CONFIG.items():
        figure = tree.find('.//fig[@id="Fig'+str(number)+'"]'); caption = ' '.join(figure.find('caption').itertext())
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
        if number == 1: special += 'A/B/C are a healthy right source reference, D/E a different pars-flaccida case, F/G a pars-tensa case, H/I a left chronic-otitis case. They are not one patient progression. '
        if number == 2: special += 'A/B and C/D are different source patients with different mastoidectomy types, not a before/after sequence. '
        if number == 3: special += 'A/B, C and D are separate patients/lesion examples; they do not establish one continuous erosion tract. '
        if number == 4: special += 'C contains an original ADC ROI; the printed mean/unit scaling is retained without conversion or independent calibration. D is the published fused MRI image, not newly registered or synthesized anatomy. '
        if number == 5: special += 'A/B and C/D describe distinct source examples; shared patient identity is not established. Lower perilymph signal does not independently measure protein content or function. '
        if number == 6: special += 'D includes the original ADC inset. Caption value 590×10−6 mm²/s and printed overlay units/scaling remain attributed to the source; no new calibration, ADC measurement or whole-series registration is supplied. '
        if number == 7: special += 'A/B fat graft, C/D cartilage graft and E/F/G cerumen are separate source examples. Only G is stated subsequent after wax removal; no source interval or universal negative DWI rule is inferred. '
        limits = special+COMMON
        selected = [panel for panel, modality in types.items() if modality == primary]
        context = {'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'local',
                   'depicted_state':'source_multiple_temporal_bone_case_examples','selected_panels':selected,'panel_types':types,
                   'panel_states':dict.fromkeys(selected,'source_multiple_temporal_bone_case_examples'),
                   'source_sequence_and_plane_roles':sequences,'independent_native_series_registration_or_calibration_verified':False,
                   'full_native_anatomical_or_3D_extent_verified':False}
        if number == 1:
            context['panel_states'] = {p:('normal_anatomy' if p in 'ABC' else 'source_temporal_pathology_example') for p in types}
            context['source_case_groups'] = {'healthy_right':['A','B','C'],'pars_flaccida_right':['D','E'],'pars_tensa_right':['F','G'],'chronic_otitis_left':['H','I']}
        if number == 2: context['source_case_groups'] = {'canal_wall_down_case':['A','B'],'different_canal_wall_up_case':['C','D']}
        if number == 3: context['source_case_groups'] = {'lateral_canal_case':['A','B'],'different_tegmen_case':['C'],'different_cochlear_case':['D']}
        if number == 4: context['source_ADC_and_fusion_roles'] = {'C':'original ADC ROI with unverified overlay scaling','D':'original published MRI fusion'}
        if number == 5: context['source_example_groups'] = {'prior_CWUM_herniation_example':['A','B'],'expanding_matrix_inner_ear_example':['C','D']}; context['same_patient_identity_between_groups_verified']=False
        if number == 6: context['source_ADC_and_fusion_roles'] = {'D':'DWI with original ADC inset; source caption vs printed units/scaling not independently calibrated'}
        if number == 7: context['source_case_groups'] = {'fat_graft_case':['A','B'],'cartilage_graft_case':['C','D'],'cerumen_case':['E','F','G']}; context['source_time_groups']={'cerumen_before_removal':['E','F'],'subsequent_after_wax_removal':['G']}
        local = f'web/reference-media/radiology-open/temporal-bone-pmc11913933-fig{number}.jpg'; (ROOT/local).write_bytes(raw)
        attribution = ', '.join(authors)+'. '+m['title']+'. DOI '+m['doi']+'. CC BY 4.0. Complete original figure retained. NLM/PMC dataset snapshot may not reflect latest NLM data.'
        row = {'id':PREFIX+str(number),'kind':'clinical-image','modality':primary,'figure_number':number,
               'src':'/app/'+local.removeprefix('web/'),'sha256':fact['sha256'],'width':fact['width'],'height':fact['height'],
               'source_url':SOURCE,'figure_url':SOURCE+'#Fig'+str(number),'asset_source_url':url,'clinical_panels':selected,
               'source_context':context,'image_state':'source_multiple_temporal_bone_case_examples','caption':f'Original Figure {number}: {title}. '+limits,
               'alt':f'Original Figure {number}: {title}. '+limits,'limits':limits,'source_caption_full':caption,
               'structures_visible':['Source-local '+title.lower()],'license':grant,'license_url':grant_url,
               'attribution':attribution,'rights_reviewed_on':'2026-10-07','rights_review':'Original explicit article grant and whole unchanged figure checked; flowchart Figure8 excluded from anatomical coverage.'}
        if set(types.values())-{primary}:
            row['ancillary_panels'] = [{'kind':kind,'panels':[p for p,v in types.items() if v==kind],
                                       'structures_visible':['Separate source '+kind+' example'],
                                       'limits':'Actual separately displayed modality; no independent whole-series registration, calibration or unique diagnosis.'} for kind in sorted(set(types.values())-{primary})]
        rows.append(row); facts.append(fact); paths.append(local)
    proof = {'pmcid':m['pmcid'],'doi':m['doi'],'title':m['title'],'authors':authors,'metadata_sha256':sha(metadata.read_bytes()),
             'xml_sha256':sha(raw_xml),'permissions_xml':E.tostring(permission,encoding='unicode'),'original_license':grant,
             'original_license_url':grant_url,'figures':facts,'held_figures':[{'figure_number':8,'reason':'Management flowchart, reference only; not an anatomical image/model source.','runtime_promoted':False}],
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
                       'visual_review':{'status':'source_checked','sha256':row['sha256'],'evidence_path':'docs/temporal-bone-published-source-review.md','reviewed_at':'2026-10-07'}})
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
    node.setdefault('start',{}).update(images=[PREFIX+'1',PREFIX+'4'],module_illustrations=False)
    for index, numbers in {0:[1,2,4,7],1:[2,3,5,6],2:[3,4,5],3:[3,4,5],4:[2,3,4,5,6,7]}.items():
        node['steps'][index]['images'] = list(dict.fromkeys([id for id in node['steps'][index].get('images',[]) if id not in removed_ids]+[PREFIX+str(n) for n in numbers]))
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    for value in vars(catalog).values():
        if callable(getattr(value,'cache_clear',None)): value.cache_clear()
    ref = catalog.detail(Curriculum(),catalog.resolve(IDENT))['radiology_reference']
    path = ROOT/'data/radiology/non-msk-structure-requirements.json'; data = json.loads(path.read_text())
    for item in data['investigations']:
        if item['investigation_id']==IDENT: item['source_contract_sha256']=digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    path.write_text(json.dumps(data,indent=2)+'\n')
    print('Seven unchanged original temporal-bone figures; source case/sequence/ADC roles retained; flowchart not promoted')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--source-root',type=Path,required=True)
    package(parser.parse_args().source_root)
