#!/usr/bin/env python3
"""Preserve complete original pulmonary vascular figures with actual modality and source limits."""
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
OUT = ROOT / 'docs/pulmonary-hypertension-published-source-review'
IDENT = 'ra.pulmonary-hypertension'
PREFIX = 'open-pulmonary-htn-pmc9698386-fig'
PIN = '5ac0b8597957b3b283d1c55aa8e4650d43c5ef8ba943ad4546ba056125cba9bc'
CONFIG = {
 1: ('Conceptual chronic obstruction and microvasculopathy', 'Schematic', ['whole'], 'Conceptual drawing, credited in the article acknowledgments to Hyejin Kim. Branch counts, tissue boundaries, obstruction extent and hypertrophy are illustrative, not patient-specific anatomy, histology or measured physiology.'),
 2: ('Index-case CT with enlarged pulmonary artery and right ventricle', 'CT', ['whole'], 'Source index case is a 46-year-old woman with persistent symptoms after treated PE. Six unlettered views retain the original layout. The caption reports no PE or parenchymal disease; this published subset cannot independently exclude distal chronic disease or prove microscopic disease.'),
 3: ('Echocardiography and Doppler source examples', 'Ultrasound', list('ABCD'), 'A/B are ultrasound stills; C/D are actual Doppler recordings. The source TR Vmax is rounded to 4.2 m/s while the screen displays 415 cm/s. Preserve both. A still does not supply a complete cine cycle, validated pressure estimate or invasive PH confirmation.'),
 4: ('CT pulmonary artery and ventricular size examples', 'CT', list('AB'), 'Source arrows and ratios illustrate main-PA/ascending-aorta and RV/LV comparisons. Raw voxel calibration, exact measurement protocol, cardiac phase and ECG gating are unavailable; no new diameter, EF or pressure is calculated.'),
 5: ('Source chronic and acute thrombus comparison', 'CT', list('AB'), 'A is source-labelled chronic wall-adherent material; B is a source-labelled acute central defect. Different examples are not a longitudinal same-patient comparison. Acute material can also be eccentric: location or angle alone cannot date clot or exclude mixed disease.'),
 6: ('CT chronic material, mosaic pattern, calcium and rendered views', 'CT', list('ABCDEF'), 'A/B show source wall-adherent material; C is mosaic attenuation; D/E have source calcified material; F is a flat volume-rendered CT image, not an acquired interactive model. No cross-panel same-patient registration is verified. Mosaic attenuation alone does not distinguish vascular, airway and infiltrative causes.'),
 7: ('CT iodine blood-volume maps and matching rendered views', 'CT', list('AB'), 'A/B label two composite rows, each containing an iodine/PBV map and two flat rendered views. The source describes right-upper/right-lower hypoperfusion and corresponding vessel changes in one CTEPH patient. Iodine distribution is not a measured flow rate or haemodynamic pressure. Raw dual-energy data, calibration and registration are unavailable.'),
 8: ('Planar ventilation and perfusion source projections', 'Nuclear medicine', ['whole'], 'Left two columns are perfusion and right two columns ventilation, with six named projections each. Keep original ANT, R lat, RPO, POST, LPO and L lat labels. Planar scintigraphy is not CT anatomy, SPECT geometry or an independently quantified perfusion fraction.'),
 9: ('Catheter pressure trace and pulmonary angiography', 'Radiography', ['B'], 'A is an original pressure tracing with printed PCWP 15/2/8, PA 54/18/30, RV 51/6/10 and RA 10/10/8. B contains two angiographic projections. These are distinct acquired sources; neither provides complete native anatomy, independent calibration or a new treatment/operability decision. Preserve printed numbers without deriving PVR or flow.')
}
COMMON = ' Complete original publisher JPEG and annotations preserved. Source case labels are not independent clinical approval. Full native series, thin tissue/branch interfaces, complete covered anatomy and a validated corresponding 3D model are not supplied.'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def package(source_root):
    OUT.mkdir(parents=True, exist_ok=True)
    archive = OUT / 'packaged-source-images.json'
    removed = (json.loads(archive.read_text())['replaced_unverified_investigation_images'] if archive.exists()
               else detail(Curriculum(), resolve(IDENT))['radiology_reference']['key_images'])
    mp = source_root / 'PMC9698386.1.json'
    if sha(mp.read_bytes()) != PIN: raise ValueError('Reviewed original metadata differs')
    m = json.loads(mp.read_text())
    if m['pmcid'] != 'PMC9698386' or m['is_retracted'] is not False: raise ValueError('Original identity/retraction differs')
    http = lambda u: u.replace('s3://pmc-oa-opendata/', 'https://pmc-oa-opendata.s3.amazonaws.com/')
    xml = download_verified(http(m['xml_url']), source_root / 'PMC9698386.1.xml')
    tree = E.fromstring(xml); perm = tree.find('.//article-meta/permissions'); lic, url = exact_license(perm)
    if lic != 'CC BY 4.0': raise ValueError('Original grant differs')
    authors = [' '.join([n.findtext('given-names', ''), n.findtext('surname', '')]) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]
    rows = []; entries = []; figures = []
    for n, (title, modality, selected, special) in CONFIG.items():
        fig = tree.find('.//fig[@id="jcm-11-06678-f'+f'{n:03d}'+'"]')
        caption = ' '.join(fig.find('caption').itertext())
        if fig.find('attrib') is not None or fig.find('permissions') is not None or any(w in caption.lower() for w in ['reproduced', 'reprinted', 'courtesy', 'adapted', 'modified from']): raise ValueError('Separate credit requires review')
        filename = fig.find('graphic').get('{http://www.w3.org/1999/xlink}href')
        urls = [u for u in m['media_urls'] if '/'+filename+'?' in u]
        if len(urls) != 1: raise ValueError('Original media absent or ambiguous')
        asset_url = http(urls[0]); raw = download_verified(asset_url, source_root / filename)
        with Image.open(source_root / filename) as im:
            im.load(); proof = {'figure_number': n, 'source_caption': caption, 'source_media_url': asset_url, 'sha256': sha(raw), 'decoded_pixel_sha256': sha(im.tobytes()), 'width': im.width, 'height': im.height, 'pixel_mode': im.mode, 'publisher_md5_verified': True, 'source_pixels_changed': False, 'complete_in_pixel_material_inspected': True}
        figures.append(proof)
        local = f'web/reference-media/radiology-open/pulmonary-htn-pmc9698386-fig{n}.jpg'; (ROOT/local).write_bytes(raw)
        state = 'conceptual_chronic_obstruction' if n == 1 else 'source_pulmonary_vascular_case_examples'
        types = dict.fromkeys(selected, modality)
        if n == 9: types['A'] = 'Haemodynamic tracing'
        context = {'setting': 'conceptual' if n == 1 else 'in_vivo', 'laterality': 'not_reported', 'population': {'life_stage': 'adult' if n == 2 else 'not_reported'}, 'extent': 'local', 'depicted_state': state, 'selected_panels': selected, 'panel_types': types, 'panel_states': dict.fromkeys(selected, state), 'full_native_series_and_calibration_verified': False, 'clinical_function_or_pressure_independently_verified': False, 'complete_tissue_or_branch_geometry_verified': False, 'flat_rendering_is_actual_3D_model': False}
        if n == 2: context['source_patient'] = {'age_years': 46, 'sex': 'female', 'article_index_case': True}; context['unlettered_layout'] = 'three axial views above three coronal views'
        if n == 3: context['ultrasound_panel_roles'] = {'A': 'apical chamber still', 'B': 'short-axis septal/effusion still', 'C': 'pulsed-wave RVOT Doppler', 'D': 'continuous-wave tricuspid Doppler'}
        if n == 5: context['panel_states'] = {'A': 'source_chronic_thrombus', 'B': 'source_acute_thrombus'}; context['same_patient_serial_comparison_verified'] = False
        if n == 6: context['panel_presentation'] = {'A': 'axial CT', 'B': 'coronal CT', 'C': 'lung-window CT', 'D': 'coronal CT', 'E': 'coronal CT', 'F': 'flat_volume_rendering'}
        if n == 7: context['panel_presentation'] = dict.fromkeys('AB', 'iodine_map_and_two_flat_volume_renderings'); context['source_same_patient_statement'] = True
        if n == 8: context['scintigraphy_layout'] = {'left_two_columns': 'perfusion', 'right_two_columns': 'ventilation', 'projections_each': ['ANT','R lat','RPO','POST','LPO','L lat']}
        if n == 9: context['projection_subtype'] = {'B': 'DSA'}; context['pressure_trace_is_CT_acquisition'] = False
        limits = special + COMMON
        credit = ', '.join(authors)+'. '+m['title']+'. DOI '+m['doi']+'. CC BY 4.0. Original complete publisher JPEG preserved; NLM/PMC dataset snapshot may not reflect latest NLM data.'
        if n == 1: credit += ' Article acknowledgment credits Hyejin Kim for the illustration.'
        row = {'id': PREFIX+str(n), 'kind': 'schematic' if n == 1 else 'clinical-image', 'modality': modality, 'figure_number': n, 'src': '/app/'+local.removeprefix('web/'), 'sha256': proof['sha256'], 'width': proof['width'], 'height': proof['height'], 'source_url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC9698386/', 'figure_url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC9698386/#jcm-11-06678-f'+f'{n:03d}', 'asset_source_url': asset_url, 'clinical_panels': selected, 'source_context': context, 'image_state': state, 'caption': f'Original Figure {n}: {title}. '+limits, 'alt': f'Original Figure {n}: {title}. '+limits, 'limits': limits, 'source_caption_full': caption, 'structures_visible': ['Source-local '+title.lower()], 'license': lic, 'license_url': url, 'attribution': credit, 'source_background': 'white', 'rights_reviewed_on': '2026-10-06', 'rights_review': 'Original grant, figure captions and complete pixels inspected; no separate figure credit. Illustration acknowledgment retained.'}
        if n == 9: row['ancillary_panels'] = [{'kind': 'Haemodynamic tracing', 'panels': ['A'], 'structures_visible': ['Source-labelled catheter pressure waveforms; no anatomical tissue image'], 'limits': 'Printed source pressures only; not CT anatomy or independently calibrated pressure, flow or PVR.'}]
        rows.append(row); entries.append((row,local,proof))
    review = {'pmcid': 'PMC9698386', 'doi': m['doi'], 'title': m['title'], 'authors': authors, 'metadata_sha256': PIN, 'xml_sha256': sha(xml), 'permissions_xml': E.tostring(perm,encoding='unicode'), 'original_license': lic, 'original_license_url': url, 'figures': figures, 'illustration_acknowledgment': 'Hyejin Kim', 'clinical_approval': False, 'model_promoted': False, 'structure_coverage_granted': False}
    proof_path = OUT/'original-source-review.json'; proof_path.write_text(json.dumps(review,indent=2)+'\n'); proof_hash = sha(proof_path.read_bytes()); assets = []
    for row,local,p in entries:
        assets.append({'id': row['id'], 'kind': 'schematic' if row['modality']=='Schematic' else 'clinical_image', 'name': row['caption'].split('. ')[0], 'local_path': local, 'sha256': row['sha256'], 'modality': row['modality'], 'investigation_ids': [IDENT], 'structure_ids': [], 'requirement_coverage': {}, 'source_context': row['source_context'], 'source': {'url': row['source_url'], 'figure_url': row['figure_url'], 'asset_url': row['asset_source_url'], 'license': {'name': lic, 'url': url, 'commercial_use': True, 'redistribution': True, 'review_status': 'verified', 'evidence_path': str(proof_path.relative_to(ROOT)), 'evidence_sha256': proof_hash, 'attribution': row['attribution'], 'reviewed_at': '2026-10-06'}}, 'pixel_provenance': {'source_pixels_changed': False, 'decoded_pixel_sha256': p['decoded_pixel_sha256'], 'highest_resolution_acquired_master_verified': False}, 'anatomical_review': {'status': 'pending', 'reason': 'Original source subset lacks complete native anatomy, all required branches/tissues and independent clinical validation.'}, 'visual_review': {'status': 'source_checked', 'sha256': row['sha256'], 'evidence_path': 'docs/pulmonary-hypertension-published-source-review.md', 'reviewed_at': '2026-10-06'}})
    path = ROOT/'data/radiology/radiology-open-images.json'; d=json.loads(path.read_text()); d[IDENT]=[r for r in d.get(IDENT,[]) if not r['id'].startswith(PREFIX)]+rows; path.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';d=json.loads(path.read_text());d[IDENT]['key_images']=[];path.write_text(json.dumps(d,indent=2)+'\n')
    path=ROOT/'data/radiology/reporting-steps/cardiovascular.json';raw=path.read_text();start=raw.index('{',raw.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(raw,start);node['start']={'images':[PREFIX+'2',PREFIX+'1'],'module_illustrations':False};removed_ids={r['id'] for r in removed}
    for i,numbers in {0:[2,4],1:[5],2:[5,6,9],3:[4,3,9],4:[6,7,8,1]}.items():node['steps'][i]['images']=list(dict.fromkeys([id for id in node['steps'][i].get('images',[]) if id not in removed_ids]+[PREFIX+str(n) for n in numbers]))
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    archive.write_text(json.dumps({'figures':[{'id':r['id'],'local_path':local,'sha256':r['sha256']} for r,local,p in entries],'replaced_unverified_investigation_images':removed,'module_lesson_or_other_investigation_media_changed':False,'clinical_approval':False,'model_promoted':False,'structure_coverage_granted':False},indent=2)+'\n')
    print('Nine complete original pulmonary vascular figures retained with actual modality and clinical limits.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
