#!/usr/bin/env python3
"""Preserve complete original cystic lung figures with actual modality and source limits."""
import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/cystic-lung-published-source-review'
IDENT = 'ra.hrct-cystic-lung'
PREFIX = 'open-cystic-lung-pmc13200743-fig'
PIN = 'ab4f4daed3b054e9613a5e47591e5f68be917b5b7cb4c9844e257bb6e3e851e4'
CONFIG = {1: ('Congenital cystic and sequestration examples', 'CT', ['A', 'B', 'C', 'D', 'E', 'F'], 'A/B/C are three different source CPAM cases (women aged63/25/24); D-F are a43-year-old man with source sequestration. The caption calls E a3D reconstruction, but E pixels show an axial mediastinal-window image; F is a flat vascular projection. Preserve this mismatch. Neither image is an interactive native model or independently measured flow.'), 2: ('LAM cysts and lung distribution', 'CT', ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'], 'Original source67-year-old woman with LAM. Actual labels A-I are preserved; the caption names sagittal G-H and omits I. Source-reported smooth cysts and normal intervening parenchyma describe this case subset, not a normal preset or independent whole-lung exclusion.'), 3: ('PLCH baseline and follow-up', 'CT', ['A', 'B', 'C'], 'Original32-year-old male smoker. Source A/B are baseline and C eight-month follow-up. Source chronology is retained, but no independent registration or quantitative change is calculated from these selected views.'), 4: ('Folliculin deficiency syndrome cyst distribution', 'CT', ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'], 'Original58-year-old woman with source FDS, the article terminology for the folliculin/Birt-Hogg-Dube spectrum. Actual A-I labels are preserved; caption sagittal G-H omits I. Morphology does not independently prove FLCN mutation, renal findings or hereditary diagnosis.'), 5: ('LIP cysts and septal/peribronchovascular relationships', 'CT', ['A', 'B', 'C', 'D', 'E', 'F', 'H', 'I', 'K'], 'Original38-year-old woman with Sjogren disease and source LIP. Printed panels are A-F,H,I,K: no G or J panel is supplied, despite caption H-K range. Keep original lettering. Histological lymphocyte infiltration is not resolved from these stills.'), 6: ('Amyloid source nodules, calcium and cysts', 'CT', ['A', 'B', 'C', 'D'], 'Original60-year-old woman with Sjogren disease. Source-labelled amyloid nodules, calcium and mural/intracystic components retain case context; CT alone does not prove protein identity, systemic burden or biopsy results.'), 7: ('Light-chain deposition source cyst and vessel relationships', 'CT', ['A', 'B', 'C'], 'Original46-year-old woman with Sjogren disease. Source PLCDD labels and traversing vessels are preserved. Stills do not independently establish microscopic deposition, full vessel/cyst interfaces or renal/systemic disease.'), 8: ('Castleman source serial parenchymal and cyst changes', 'CT', ['A', 'B', 'C', 'D'], 'Original35-year-old woman. Source A/B December2016 and C/D January2018. Red arrow C is the source new-cyst site. No independent whole-volume registration, interval cyst count or causal inference from ground glass is performed.'), 9: ('PJP source cysts, ground glass and crazy paving', 'CT', ['A', 'B', 'C', 'D', 'E', 'F'], 'Original composite describes different patients without panel-level patient identities. Preserve all A-F; do not merge them into one case or a serial sequence. Subpleural location is not proof of observed rupture or pneumothorax, and CT alone does not confirm the organism.'), 10: ('Alveolar macrophage pneumonia source cysts', 'CT', ['A', 'B', 'C'], 'Original67-year-old nonsmoking woman with systemic lupus erythematosus. Source terminology AMP is retained with actual A-C planes. Do not replace source clinical history or independently equate all ground-glass/cyst patterns with this diagnosis.'), 11: ('Cyst-like mimics and cyst-associated cancer example', 'CT', ['A', 'B', 'C', 'D', 'E', 'F'], 'Original A bulla, B bronchiectasis, C/D emphysema, E honeycombing and F cyst-associated lung cancer are separate examples. F source approximate1.5cm size is not a new calibrated measurement. Wall thinning or low PET uptake cannot independently establish benignity; this image does not include an acquired PET series.')}
COMMON = ' Complete original publisher JPEG and annotations preserved. Source case labels are not independent clinical approval. Full native series, thin tissue/branch interfaces, complete covered anatomy and a validated corresponding 3D model are not supplied.'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def package(source_root):
    OUT.mkdir(parents=True, exist_ok=True)
    archive = OUT / 'packaged-source-images.json'
    removed = (json.loads(archive.read_text())['replaced_unverified_investigation_images'] if archive.exists()
               else detail(Curriculum(), resolve(IDENT))['radiology_reference']['key_images'])
    mp = source_root / 'PMC13200743.1.json'
    if sha(mp.read_bytes()) != PIN: raise ValueError('Reviewed original metadata differs')
    m = json.loads(mp.read_text())
    if m['pmcid'] != 'PMC13200743' or m['is_retracted'] is not False: raise ValueError('Original identity/retraction differs')
    http = lambda u: u.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
    xml = download_verified(http(m['xml_url']), source_root / 'PMC13200743.1.xml')
    tree = E.fromstring(xml); perm = tree.find('.//article-meta/permissions'); lic, url = exact_license(perm)
    if lic != 'CC BY 4.0': raise ValueError('Original grant differs')
    authors = [' '.join([n.findtext('given-names', ''), n.findtext('surname', '')]) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]
    rows = []; entries = []; figures = []
    for n, (title, modality, selected, special) in CONFIG.items():
        fig = tree.find('.//fig[@id="tzag010-F'+str(n)+'"]')
        caption = ' '.join(fig.find('caption').itertext())
        if fig.find('attrib') is not None or fig.find('permissions') is not None or any(w in caption.lower() for w in ['reproduced', 'reprinted', 'courtesy', 'adapted', 'modified from']): raise ValueError('Separate credit requires review')
        filename = fig.find('graphic').get('{http://www.w3.org/1999/xlink}href')
        urls = [u for u in m['media_urls'] if '/'+filename+'?' in u]
        if len(urls) != 1: raise ValueError('Original media absent or ambiguous')
        asset_url = http(urls[0]); raw = download_verified(asset_url, source_root / filename)
        with Image.open(source_root / filename) as im:
            im.load(); proof = {'figure_number': n, 'source_caption': caption, 'source_media_url': asset_url, 'sha256': sha(raw), 'decoded_pixel_sha256': sha(im.tobytes()), 'width': im.width, 'height': im.height, 'pixel_mode': im.mode, 'publisher_md5_verified': True, 'source_pixels_changed': False, 'complete_in_pixel_material_inspected': True}
        figures.append(proof)
        local = f'web/reference-media/radiology-open/cystic-lung-pmc13200743-fig{n}.jpg'; (ROOT/local).write_bytes(raw)
        state = 'source_cystic_lung_case_examples'
        types = dict.fromkeys(selected, modality)
        context = {'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'adult' if n!=9 and n!=11 else 'not_reported'},'extent':'local','depicted_state':state,'selected_panels':selected,'panel_types':types,'panel_states':dict.fromkeys(selected,state),'full_native_series_and_calibration_verified':False,'microscopic_or_genetic_diagnosis_independently_verified':False,'complete_lung_cyst_wall_or_branch_geometry_verified':False,'flat_projection_is_actual_3D_model':False}
        if n==1:context['source_patient_groups']=[{'panels':['A'],'age_years':63,'sex':'female'},{'panels':['B'],'age_years':25,'sex':'female'},{'panels':['C'],'age_years':24,'sex':'female'},{'panels':list('DEF'),'age_years':43,'sex':'male'}];context['caption_E_3D_vs_actual_axial_presentation_mismatch']=True
        if n in [2,4]:context['actual_extra_panel_I_not_named_by_caption']=True
        if n==5:context['actual_sagittal_labels']=['H','I','K'];context['caption_range_does_not_supply_missing_G_or_J']=True
        if n==3:context['source_time_groups']={'baseline':['A','B'],'eight_month_follow_up':['C']}
        if n==8:context['source_time_groups']={'December_2016':['A','B'],'January_2018':['C','D']}
        if n in [3,8]:context['independent_serial_registration_or_measurement_verified']=False
        if n in [9,11]:context['cross_panel_same_patient_identity_verified']=False
        limits = special + COMMON
        credit = ', '.join(authors)+'. '+m['title']+'. DOI '+m['doi']+'. CC BY 4.0. Original complete publisher JPEG preserved; NLM/PMC dataset snapshot may not reflect latest NLM data.'
        row = {'id': PREFIX+str(n), 'kind': 'clinical-image', 'modality': modality, 'figure_number': n, 'src': '/app/'+local.removeprefix('web/'), 'sha256': proof['sha256'], 'width': proof['width'], 'height': proof['height'], 'source_url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC13200743/', 'figure_url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC13200743/#tzag010-F'+str(n), 'asset_source_url': asset_url, 'clinical_panels': selected, 'source_context': context, 'image_state': state, 'caption': f'Original Figure {n}: {title}. '+limits, 'alt': f'Original Figure {n}: {title}. '+limits, 'limits': limits, 'source_caption_full': caption, 'structures_visible': ['Source-local '+title.lower()], 'license': lic, 'license_url': url, 'attribution': credit, 'source_background': 'white', 'rights_reviewed_on': '2026-10-06', 'rights_review': 'Original grant, complete figure captions and pixels inspected; no separate figure credit; caption/pixel mismatches retained.'}
        rows.append(row); entries.append((row,local,proof))
    review = {'pmcid': 'PMC13200743', 'doi': m['doi'], 'title': m['title'], 'authors': authors, 'metadata_sha256': PIN, 'xml_sha256': sha(xml), 'permissions_xml': E.tostring(perm,encoding='unicode'), 'original_license': lic, 'original_license_url': url, 'figures': figures, 'excluded_figure12': 'Diagnostic algorithm with overlapping 20mm thresholds; not tissue anatomy or a validated classifier for this reader.', 'clinical_approval': False, 'model_promoted': False, 'structure_coverage_granted': False}
    proof_path = OUT/'original-source-review.json'; proof_path.write_text(json.dumps(review,indent=2)+'\n'); proof_hash = sha(proof_path.read_bytes()); assets = []
    for row,local,p in entries:
        assets.append({'id': row['id'], 'kind': 'schematic' if row['modality']=='Schematic' else 'clinical_image', 'name': row['caption'].split('. ')[0], 'local_path': local, 'sha256': row['sha256'], 'modality': row['modality'], 'investigation_ids': [IDENT], 'structure_ids': [], 'requirement_coverage': {}, 'source_context': row['source_context'], 'source': {'url': row['source_url'], 'figure_url': row['figure_url'], 'asset_url': row['asset_source_url'], 'license': {'name': lic, 'url': url, 'commercial_use': True, 'redistribution': True, 'review_status': 'verified', 'evidence_path': str(proof_path.relative_to(ROOT)), 'evidence_sha256': proof_hash, 'attribution': row['attribution'], 'reviewed_at': '2026-10-06'}}, 'pixel_provenance': {'source_pixels_changed': False, 'decoded_pixel_sha256': p['decoded_pixel_sha256'], 'highest_resolution_acquired_master_verified': False}, 'anatomical_review': {'status': 'pending', 'reason': 'Original source subset lacks complete native anatomy, all required branches/tissues and independent clinical validation.'}, 'visual_review': {'status': 'source_checked', 'sha256': row['sha256'], 'evidence_path': 'docs/cystic-lung-published-source-review.md', 'reviewed_at': '2026-10-06'}})
    path = ROOT/'data/radiology/radiology-open-images.json'; d=json.loads(path.read_text()); d[IDENT]=[r for r in d.get(IDENT,[]) if not r['id'].startswith(PREFIX)]+rows; path.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';d=json.loads(path.read_text());d.setdefault(IDENT,{})['key_images']=[];path.write_text(json.dumps(d,indent=2)+'\n')
    path=ROOT/'data/radiology/investigation-source-images.json';raw=path.read_text();start=raw.index('[',raw.index('\"'+IDENT+'\"'));old,end=json.JSONDecoder().raw_decode(raw,start);path.write_text(raw[:start]+'[]'+raw[end:])
    path=ROOT/'data/radiology/reporting-steps/chest.json';raw=path.read_text();start=raw.index('{',raw.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(raw,start);node['start']={'images':[PREFIX+'11',PREFIX+'2'],'module_illustrations':False};removed_ids={r['id'] for r in removed}
    for i,numbers in {0:[11,2,4,5,7],1:[2,3,4,5,10],2:[3,6,11],3:[8,9,10,11],4:[1,4,6,9,11]}.items():node['steps'][i]['images']=list(dict.fromkeys([id for id in node['steps'][i].get('images',[]) if id not in removed_ids]+[PREFIX+str(n) for n in numbers]))
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    archive.write_text(json.dumps({'figures':[{'id':r['id'],'local_path':local,'sha256':r['sha256']} for r,local,p in entries],'replaced_unverified_investigation_images':removed,'module_lesson_or_other_investigation_media_changed':False,'clinical_approval':False,'model_promoted':False,'structure_coverage_granted':False},indent=2)+'\n')
    print('Eleven complete original cystic lung figures retained with actual modality and clinical limits.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
