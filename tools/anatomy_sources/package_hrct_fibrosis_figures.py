#!/usr/bin/env python3
"""Preserve complete original fibrotic lung figures with actual modality and source limits."""
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
OUT = ROOT / 'docs/hrct-fibrosis-published-source-review'
IDENT = 'ra.hrct-lung'
PREFIX = 'open-hrct-fibrosis-pmc11914337-fig'
PIN = 'fb5fa507fd073de694d7cf9098a7e35c50303a44416268449ce837fef67f857f'
CONFIG = {1: ('Honeycombing, traction bronchiectasis and fibrotic reticulation', 'CT', ['a', 'b', 'c'], 'Original a/b/c are separate source morphology examples. Fibrotic septa and airway distortion are CT appearances, not resolved microscopic histology or independent whole-lung burden.'), 3: ('UIP, probable UIP and fibrotic NSIP source patterns', 'CT', ['a', 'b', 'c', 'd', 'e', 'f'], 'Original a/b UIP, c/d probable UIP and e/f fibrotic NSIP are distinct source examples. A CT UIP pattern does not itself establish idiopathic pulmonary fibrosis or exclude secondary causes. Whole native series and independent multidisciplinary diagnoses are unavailable.'), 4: ('Fibrotic sarcoidosis and hypersensitivity source patterns', 'CT', ['a', 'b', 'c', 'd', 'e', 'f'], 'Original a-c source fibrotic sarcoidosis and d-f source fibrotic HP are different cases. Mosaic/three-density appearances and source air-trapping statements do not supply an unperformed expiratory acquisition, unique aetiology or measured perfusion.'), 5: ('Source fibrotic HP serial comparison', 'CT', ['a', 'b', 'c', 'd', 'e', 'f'], 'Original a-c baseline and d-f 13-month follow-up with source pigeon exposure and multidisciplinary HP context. Source PPF label and treatment history are retained; these images alone do not prove the named 2022 within-one-year PPF criteria, confirm exposure causality or recommend therapy.'), 6: ('Source systemic-sclerosis NSIP serial comparison', 'CT', ['a', 'b', 'c', 'd', 'e', 'f'], 'Original a-c baseline and d-f 15-month follow-up in source systemic sclerosis. Source matched-level comparison, symptom worsening and PPF/treatment labels are retained. No new registration, physiological trend or fulfilment of the named within-one-year PPF definition is inferred.'), 7: ('Source IPF acute opacity and pneumomediastinum sequence', 'CT', ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'], 'Original a-c baseline, d-f 15-month acute respiratory-distress study, g-i 40 days after the acute phase with source pneumomediastinum. New ground glass is not unique for acute exacerbation; infection, oedema and other causes require clinical/source assessment. Source alveolar-rupture mechanism is not directly imaged microscopic proof.')}
COMMON = ' Complete original publisher JPEG and annotations preserved. Source case labels are not independent clinical approval. Full native series, thin tissue/branch interfaces, complete covered anatomy and a validated corresponding 3D model are not supplied.'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def package(source_root):
    OUT.mkdir(parents=True, exist_ok=True)
    archive = OUT / 'packaged-source-images.json'
    removed = (json.loads(archive.read_text())['replaced_unverified_investigation_images'] if archive.exists()
               else detail(Curriculum(), resolve(IDENT))['radiology_reference']['key_images'])
    mp = source_root / 'PMC11914337.1.json'
    if sha(mp.read_bytes()) != PIN: raise ValueError('Reviewed original metadata differs')
    m = json.loads(mp.read_text())
    if m['pmcid'] != 'PMC11914337' or m['is_retracted'] is not False: raise ValueError('Original identity/retraction differs')
    http = lambda u: u.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
    xml = download_verified(http(m['xml_url']), source_root / 'PMC11914337.1.xml')
    tree = E.fromstring(xml); perm = tree.find('.//article-meta/permissions'); lic, url = exact_license(perm)
    if lic != 'CC BY 4.0': raise ValueError('Original grant differs')
    authors = [' '.join([n.findtext('given-names', ''), n.findtext('surname', '')]) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]
    rows = []; entries = []; figures = []
    for n, (title, modality, selected, special) in CONFIG.items():
        fig = tree.find('.//fig[@id="Fig'+str(n)+'"]')
        caption = ' '.join(fig.find('caption').itertext())
        if fig.find('attrib') is not None or fig.find('permissions') is not None or any(w in caption.lower() for w in ['reproduced', 'reprinted', 'courtesy', 'adapted', 'modified from']): raise ValueError('Separate credit requires review')
        filename = fig.find('graphic').get('{http://www.w3.org/1999/xlink}href')
        urls = [u for u in m['media_urls'] if '/'+filename+'?' in u]
        if len(urls) != 1: raise ValueError('Original media absent or ambiguous')
        asset_url = http(urls[0]); raw = download_verified(asset_url, source_root / filename)
        with Image.open(source_root / filename) as im:
            im.load(); proof = {'figure_number': n, 'source_caption': caption, 'source_media_url': asset_url, 'sha256': sha(raw), 'decoded_pixel_sha256': sha(im.tobytes()), 'width': im.width, 'height': im.height, 'pixel_mode': im.mode, 'publisher_md5_verified': True, 'source_pixels_changed': False, 'complete_in_pixel_material_inspected': True}
        figures.append(proof)
        local = f'web/reference-media/radiology-open/hrct-fibrosis-pmc11914337-fig{n}.jpg'; (ROOT/local).write_bytes(raw)
        state = 'source_fibrotic_lung_case_examples'
        types = dict.fromkeys(selected,modality)
        context = {'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'local','depicted_state':state,'selected_panels':selected,'panel_types':types,'panel_states':dict.fromkeys(selected,state),'full_native_series_and_calibration_verified':False,'microscopic_or_multidisciplinary_diagnosis_independently_verified':False,'complete_lobular_wall_or_branch_geometry_verified':False,'actual_expiratory_acquisition_verified':False,'quantified_fibrosis_or_physiology_independently_verified':False}
        if n==3:context['source_pattern_groups']={'UIP':list('ab'),'probable_UIP':list('cd'),'fibrotic_NSIP':list('ef')}
        if n==4:context['source_case_groups']={'fibrotic_sarcoidosis':list('abc'),'fibrotic_HP':list('def')}
        if n in [5,6]:context['source_time_groups']={'baseline':list('abc'),'follow_up':list('def')};context['source_follow_up_months']=13 if n==5 else 15;context['named_2022_within_one_year_PPF_criteria_independently_verified']=False
        if n==7:context['source_time_groups']={'baseline':list('abc'),'15_month_acute_study':list('def'),'40_days_after_acute_phase':list('ghi')};context['source_mechanism_is_direct_microscopic_imaging']=False
        if n in [5,6,7]:context['independent_serial_registration_or_measurement_verified']=False
        limits = special + COMMON
        credit = ', '.join(authors)+'. '+m['title']+'. DOI '+m['doi']+'. CC BY 4.0. Original complete publisher JPEG preserved; NLM/PMC dataset snapshot may not reflect latest NLM data.'
        row = {'id': PREFIX+str(n), 'kind': 'clinical-image', 'modality': modality, 'figure_number': n, 'src': '/app/'+local.removeprefix('web/'), 'sha256': proof['sha256'], 'width': proof['width'], 'height': proof['height'], 'source_url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11914337/', 'figure_url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11914337/#Fig'+str(n), 'asset_source_url': asset_url, 'clinical_panels': selected, 'source_context': context, 'image_state': state, 'caption': f'Original Figure {n}: {title}. '+limits, 'alt': f'Original Figure {n}: {title}. '+limits, 'limits': limits, 'source_caption_full': caption, 'structures_visible': ['Source-local '+title.lower()], 'license': lic, 'license_url': url, 'attribution': credit, 'source_background': 'white', 'rights_reviewed_on': '2026-10-06', 'rights_review': 'Original grant, complete figure captions and pixels inspected; no separate figure credit; caption/pixel mismatches retained.'}
        rows.append(row); entries.append((row,local,proof))
    review = {'pmcid': 'PMC11914337', 'doi': m['doi'], 'title': m['title'], 'authors': authors, 'metadata_sha256': PIN, 'xml_sha256': sha(xml), 'permissions_xml': E.tostring(perm,encoding='unicode'), 'original_license': lic, 'original_license_url': url, 'figures': figures, 'excluded_figure2': 'Diagnostic flowchart, not tissue anatomy or an independently validated reader classifier.', 'clinical_approval': False, 'model_promoted': False, 'structure_coverage_granted': False}
    proof_path = OUT/'original-source-review.json'; proof_path.write_text(json.dumps(review,indent=2)+'\n'); proof_hash = sha(proof_path.read_bytes()); assets = []
    for row,local,p in entries:
        assets.append({'id': row['id'], 'kind': 'schematic' if row['modality']=='Schematic' else 'clinical_image', 'name': row['caption'].split('. ')[0], 'local_path': local, 'sha256': row['sha256'], 'modality': row['modality'], 'investigation_ids': [IDENT], 'structure_ids': [], 'requirement_coverage': {}, 'source_context': row['source_context'], 'source': {'url': row['source_url'], 'figure_url': row['figure_url'], 'asset_url': row['asset_source_url'], 'license': {'name': lic, 'url': url, 'commercial_use': True, 'redistribution': True, 'review_status': 'verified', 'evidence_path': str(proof_path.relative_to(ROOT)), 'evidence_sha256': proof_hash, 'attribution': row['attribution'], 'reviewed_at': '2026-10-06'}}, 'pixel_provenance': {'source_pixels_changed': False, 'decoded_pixel_sha256': p['decoded_pixel_sha256'], 'highest_resolution_acquired_master_verified': False}, 'anatomical_review': {'status': 'pending', 'reason': 'Original source subset lacks complete native anatomy, all required branches/tissues and independent clinical validation.'}, 'visual_review': {'status': 'source_checked', 'sha256': row['sha256'], 'evidence_path': 'docs/hrct-fibrosis-published-source-review.md', 'reviewed_at': '2026-10-06'}})
    path = ROOT/'data/radiology/radiology-open-images.json'; d=json.loads(path.read_text()); d[IDENT]=[r for r in d.get(IDENT,[]) if not r['id'].startswith(PREFIX)]+rows; path.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';d=json.loads(path.read_text());d.setdefault(IDENT,{})['key_images']=[];path.write_text(json.dumps(d,indent=2)+'\n')
    path=ROOT/'data/radiology/investigation-source-images.json';raw=path.read_text()
    if '\"'+IDENT+'\"' in raw:
        start=raw.index('[',raw.index('\"'+IDENT+'\"'));old,end=json.JSONDecoder().raw_decode(raw,start);path.write_text(raw[:start]+'[]'+raw[end:])
    path=ROOT/'data/radiology/reporting-steps/chest.json';raw=path.read_text();start=raw.index('{',raw.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(raw,start);node['start']={'images':[PREFIX+'1',PREFIX+'3'],'module_illustrations':False};removed_ids={r['id'] for r in removed}
    for i,numbers in {0:[1,3,4],1:[3,4],2:[1,3,5,6],3:[1,4,5],4:[5,6,7]}.items():node['steps'][i]['images']=list(dict.fromkeys([id for id in node['steps'][i].get('images',[]) if id not in removed_ids]+[PREFIX+str(n) for n in numbers]))
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    archive.write_text(json.dumps({'figures':[{'id':r['id'],'local_path':local,'sha256':r['sha256']} for r,local,p in entries],'replaced_unverified_investigation_images':removed,'module_lesson_or_other_investigation_media_changed':False,'clinical_approval':False,'model_promoted':False,'structure_coverage_granted':False},indent=2)+'\n')
    print('Six complete original fibrotic lung figures retained with actual modality and clinical limits.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
