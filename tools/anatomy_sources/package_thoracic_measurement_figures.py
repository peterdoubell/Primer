#!/usr/bin/env python3
"""Attach byte-identical CT/MRI measurement examples without inventing calibrated source volumes."""
import argparse
import hashlib
import json
from pathlib import Path
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'docs/thoracic-measurement-published-source-review'
PREFIX='open-thoracic-measurement-pmc3874367-fig'
IDENT='ra.thoracic-aorta-measurement'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def package(root):
    proof_path=FOLDER/'original-source-review.json';proof_raw=proof_path.read_bytes();proof=json.loads(proof_raw)
    if proof['original_license']!='CC BY 3.0' or len(proof['figures'])!=3:raise ValueError('Unreviewed original selection')
    rows=[];assets=[];packaged=[]
    for source in proof['figures']:
        n=source['figure_number'];ident=PREFIX+str(n);raw=(root/source['original_filename']).read_bytes()
        if sha(raw)!=source['sha256']:raise ValueError('Original publisher JPEG differs')
        local=f'web/reference-media/radiology-open/thoracic-measurement-pmc3874367-fig{n}.jpg';(ROOT/local).write_bytes(raw)
        panels=['whole'] if n==1 else list('abc') if n==2 else list('abcd');modality=source['source_modality']
        if n==1:
            title='Thoracic aortic level/branch locator';visible=['Source-labelled root, ascending, arch, isthmus, descending and arch branch origins']
            limits='Single unlettered sagittal CT reconstruction is a local locator, not a complete set of calibrated orthogonal planes or every root/branch boundary. Caption normality is source-described, not independently validated for all imaged anatomy.'
            sequences={};gating={}
        elif n==2:
            title='Double-oblique ascending-aorta measurement example';visible=['Source coronal/sagittal plane references and short-axis calliper annotations']
            limits='Original printed lengths, pixel-intensity statistics, scale marks and crosshairs are source annotations. Original voxel series, independent endpoint/edge calibration and clinical minimum/maximum dimensions are unavailable; the illustration is not a patient-specific 3D model.'
            sequences={'a':'coronal_CT_reconstruction','b':'sagittal_CT_reconstruction','c':'double_oblique_short_axis_CT'};gating={}
        else:
            title='MRI sequence and edge-depiction examples';visible=['Source local root/aortic-wall appearances across four MRI methods']
            limits='Source a is non-ECG-gated 3D contrast-enhanced MRA, b noncontrast ECG-gated 3D SSFP, c a 2D SSFP cine method represented by one static image, d ECG-gated T2 black blood. No continuous cine, phase registration, same-patient correspondence, calibrated comparison or valve function is independently verified from these snapshots.'
            sequences={'a':'3D_contrast_enhanced_MRA','b':'noncontrast_3D_SSFP','c':'2D_SSFP_cine_method_static_snapshot','d':'T2_black_blood'}
            gating={'a':'not_ECG_gated','b':'ECG_gated','c':'actual_gating_or_cardiac_phase_not_named','d':'ECG_gated'}
        state=f'thoracic_measurement_source_pmc3874367_fig{n}'
        context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'local',
            'depicted_state':state,'selected_panels':panels,'panel_types':dict.fromkeys(panels,modality),
            'panel_states':dict.fromkeys(panels,state),'panel_sequences':sequences,'panel_gating':gating,
            'single_unlettered_image':n==1,'panel_identifiers_from_caption':n!=1,
            'independent_calibrated_measurements_verified':False,'original_acquired_voxel_series_supplied':False,
            'independent_same_patient_or_phase_registration_verified':False,'continuous_cine_supplied':False,
            'independent_anatomical_review_verified':False,'clinical_normality_or_growth_verified':False,'patient_model_derived':False}
        caption=f'Original Figure {n}: {title}. Complete publisher JPEG and original labels/callipers are preserved. '+limits
        credit=proof['copyright']+' '+', '.join(proof['authors'])+'. '+proof['title']+'. DOI '+proof['doi']+'. CC BY 3.0. Original publisher figure reproduced byte-identically without pixel changes. NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.'
        row={'id':ident,'kind':'clinical-image','modality':modality,'src':'/app/'+local.removeprefix('web/'),
            'width':source['width'],'height':source['height'],'sha256':source['sha256'],'figure_number':n,
            'source_url':proof['source_article_url'],'figure_url':proof['source_article_url']+f'#fig{n}',
            'asset_source_url':source['source_media_url'],'clinical_panels':panels,'source_context':context,'image_state':state,
            'caption':caption,'alt':caption,'limits':limits,'source_caption_full':source['source_caption'],'structures_visible':visible,
            'license':'CC BY 3.0','license_url':proof['original_license_url'],'attribution':credit,'source_background':'white',
            'rights_reviewed_on':'2026-10-06','rights_review':'Original XML grant and complete caption checked; complete publisher figure MD5/SHA and byte/pixel identities verified.'}
        rows.append(row);assets.append({'id':ident,'kind':'clinical_image','name':title,'local_path':local,'sha256':source['sha256'],
            'regions':['aorta','thorax'],'investigation_ids':[IDENT],'structure_ids':[],'requirement_coverage':{},
            'modality':modality,'source_context':context,
            'source':{'url':proof['source_article_url'],'figure_url':row['figure_url'],'asset_url':source['source_media_url'],
                'license':{'name':'CC BY 3.0','url':proof['original_license_url'],'commercial_use':True,'redistribution':True,
                    'review_status':'verified','evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_raw),
                    'attribution':credit,'reviewed_at':'2026-10-06'}},
            'pixel_provenance':{'decoded_pixel_sha256':source['decoded_pixel_sha256'],'source_pixels_changed':False,
                'method':source['method'],'highest_resolution_acquired_master_verified':False},
            'anatomical_review':{'status':'pending','reason':'Local instructional source views/callipers are not independent complete boundaries or clinical measurement validation.'},
            'visual_review':{'status':'source_checked','sha256':source['sha256'],'reviewed_at':'2026-10-06','evidence_path':'docs/thoracic-measurement-published-source-review.md'}})
        packaged.append({'figure_number':n,'local_path':local,'sha256':source['sha256'],'source_pixels_changed':False})
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text());data[IDENT]=[r for r in data.get(IDENT,[]) if not r['id'].startswith(PREFIX)]+rows
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/reporting-steps/cardiovascular.json';raw=path.read_text();start=raw.index('{',raw.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(raw,start)
    for index,numbers in {0:[2,3],2:[1,2],3:[1],4:[1]}.items():node['steps'][index]['images']=list(dict.fromkeys(node['steps'][index].get('images',[])+[PREFIX+str(n) for n in numbers]))
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    (FOLDER/'packaged-source-images.json').write_text(json.dumps({'figures':packaged,'clinical_approval':False,'model_promoted':False,'structure_coverage_granted':False},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    package(p.parse_args().source_root)
