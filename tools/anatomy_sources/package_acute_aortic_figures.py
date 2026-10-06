#!/usr/bin/env python3
"""Attach original AAS artwork without inferring full source volumes, physiology or patient models."""
import argparse
import hashlib
import json
from pathlib import Path
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'docs/acute-aortic-published-source-review'
IDENT='ra.ct-acute-aortic-syndrome'
PREFIX='open-acute-aortic-pmc3505562-fig'
DATE='2026-10-06'
# Descriptions preserve acquisition/temporal facts actually named by source captions or artwork.
CONFIG={
 1:('Gated and non-gated limited-tear views','abcd',{'a':'contrast_enhanced_phase_not_named','b':'contrast_enhanced_phase_not_named','c':'contrast_enhanced_phase_not_named','d':'contrast_enhanced_phase_not_named'},
    {'a':'non_gated','b':'non_gated','c':'ECG_gated','d':'ECG_gated'},
    {'a':'first_examination','b':'first_examination','c':'one_day_later','d':'one_day_later'},
    'Panels a/b are non-gated, c/d ECG-gated one day later. Different acquisitions/projections are not independently registered; artifact suppression is not proof of every tear or wall boundary.'),
 3:('Classic type A dissection with root/branch context','abcd',dict.fromkeys('abcd','contrast_enhanced_phase_not_named'),
    dict.fromkeys('abcd','ECG_gated'),dict.fromkeys('abcd','same_source_examination'),
    'Local views show source-described flap, root/valve apparatus and brachiocephalic relationship. Aortic regurgitation is source-reported as confirmed on echocardiography, not measured from these CT snapshots.'),
 4:('Intramural haemorrhage and focal intimal disruption','abc',{'a':'unenhanced','b':'contrast_enhanced_phase_not_named','c':'phase_not_named'},
    dict.fromkeys('abc','gating_not_named'),dict.fromkeys('abc','source_examination'),
    'A focal intimal disruption is source-described and later identified during surgery. Absence of a visible classic flap in local views does not prove absence of a tear; operative findings are not independent bitmap geometry.'),
 5:('Tiny tear and source follow-up views','abc',{'a':'unenhanced','b':'phase_not_named','c':'phase_not_named'},
    dict.fromkeys('abc','gating_not_named'),{'a':'visible_artwork_day_2','b':'caption_initial_interval_unspecified','c':'visible_artwork_day_7'},
    'Artwork labels a Day 2 and c Day 7, while the caption describes 7-day follow-up. Both are retained without inventing exact acquisition dates/interval or independent registration; reported eventual resolution is not independently validated here.'),
 6:('Limited intimal tear and wall bulge','abc',{'a':'unenhanced','b':'contrast_enhanced_phase_not_named','c':'phase_not_named'},
    dict.fromkeys('abc','gating_not_named'),dict.fromkeys('abc','source_examination'),
    'Panel d is a flat CT volume-rendered luminal image, excluded from selected clinical CT panels but preserved in the complete artwork. It is not acquired 3D geometry, a complete tear surface or a calibrated measurement.'),
 7:('Ulcerative/haemorrhagic overlap example','ab',{'a':'unenhanced','b':'contrast_enhanced_phase_not_named'},
    {'a':'gating_not_named','b':'ECG_gated'},dict.fromkeys('ab','source_examination'),
    'Panel c is a flat CT volume rendering, not a model. The caption names descending, proximal ascending and arch sites across panels; no independently registered same-site correspondence or corrected segment diagnosis is inferred.'),
 8:('Penetrating ulcer local CT views','ab',dict.fromkeys('ab','contrast_enhanced_phase_not_named'),
    dict.fromkeys('ab','gating_not_named'),dict.fromkeys('ab','source_examination'),
    'Axial and oblique sagittal source views preserve the local ulcer/wall relationship; full aortic coverage and independent calibrated ulcer depth/width are not supplied.'),
 9:('Symptomatic aneurysm wall-change example','abc',{'a':'unenhanced','b':'contrast_enhanced_phase_not_named','c':'phase_not_named'},
    dict.fromkeys('abc','gating_not_named'),dict.fromkeys('abc','symptomatic_source_examination'),
    'The original caption uses historical impending-rupture language. These local wall/bulge views do not establish rupture timing or a universal isolated-sign risk rule; prior images described in the caption are not included.'),
 10:('Haemorrhagic wall lesion and interval changes','abcd',{'a':'contrast_enhanced_phase_not_named','b':'phase_not_named','c':'phase_not_named','d':'phase_not_named'},
    dict.fromkeys('abcd','gating_not_named'),{'a':'initial_interval_not_named','b':'initial_interval_not_named','c':'two_days_after_onset','d':'one_week_later'},
    'Source-described interval tear/outpouching and dilatation are not independently registered or calibrated. Source evolution/resolution does not establish functional outcome, treatment suitability or complete tissue boundaries.')
}

def sha(raw):return hashlib.sha256(raw).hexdigest()

def package(root):
    proof_paths=[FOLDER/'original-source-review.json',FOLDER/'conceptual-diagram/original-source-review.json']
    rows=[];assets=[];packaged=[]
    for proof_path in proof_paths:
        proof_raw=proof_path.read_bytes();proof=json.loads(proof_raw);article=proof['articles'][0]
        if article['pmcid']!='PMC3505562' or article['license']!='CC BY 4.0':raise ValueError('Unreviewed source grant')
        for source in proof['figures']:
            n=source['figure_number'];schematic=n==2;ident=PREFIX+str(n)
            raw=(root/source['extracted_file']).read_bytes()
            if sha(raw)!=source['sha256'] or not source['original_encoded_stream_or_decoded_pixel_readback_verified']:raise ValueError('Original artwork differs')
            extension=Path(source['extracted_file']).suffix;local=f'web/reference-media/radiology-open/acute-aortic-pmc3505562-fig{n}{extension}'
            (ROOT/local).write_bytes(raw)
            if schematic:
                title='Conceptual overlap of acute aortic conditions';panels=[];phases={};gating={};times={}
                limits='Original conceptual diagram, not acquired CT, patient-specific anatomy, a complete structure map or a universal diagnostic/rupture-risk rule. Historical source taxonomy is preserved without inferring biological transition or timing in a patient.'
            else:
                title,selected,phases,gating,times,specific=CONFIG[n];panels=list(selected)
                limits=specific+' Complete original voxel series, independent anatomical review, source calibration and complete branch/compartment coverage are unavailable. No physiological measurement, complete patient 3D reconstruction or clinical approval follows from the artwork.'
            state=f'acute_aortic_source_pmc3505562_fig{n}'
            context={'setting':'not_reported' if schematic else 'in_vivo','laterality':'not_reported',
                'population':{'life_stage':'not_reported' if schematic else 'adult'},'extent':'local','depicted_state':state,
                'selected_panels':panels,'panel_types':source['source_panel_types'],'panel_states':{p:state for p in panels},
                'panel_contrast_phases':phases,'panel_gating':gating,'panel_timepoints':times,
                'source_patient_id':None if schematic else f'paper_case_fig{n}','panel_identifiers_from_caption':not schematic,
                'unlettered_conceptual_diagram':schematic,'source_ct_volume_rendering_panels':['d'] if n==6 else ['c'] if n==7 else [],
                'flat_renderings_are_spatial_geometry':False,'full_acquired_series_included':False,
                'independent_timepoint_registration_verified':False,'independent_calibrated_measurements_verified':False,
                'independent_anatomical_validation_verified':False,'functional_or_outcome_confirmation_verified':False}
            caption=f'Original Figure {n}: {title}. Complete source artwork and original annotations are preserved. '+limits
            credit=article['copyright']+' '+', '.join(article['authors'])+'. '+article['title']+'. DOI '+article['doi']+'. CC BY 4.0. Complete original artwork preserved without sample changes. NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.'
            row={'id':ident,'kind':'schematic' if schematic else 'clinical-image','src':'/app/'+local.removeprefix('web/'),
                'width':source['width'],'height':source['height'],'sha256':source['sha256'],'figure_number':n,
                'source_url':article['source_article_url'],'figure_url':article['source_article_url']+f'#Fig{n}','asset_source_url':article['pdf_url'],
                'modality':'Schematic' if schematic else 'CT','clinical_panels':panels,'source_context':context,'image_state':state,
                'caption':caption,'alt':caption,'limits':limits,'source_caption_full':source['source_caption'],
                'structures_visible':['Conceptual source relationships among dissection/variants, IMH, PAU and aneurysm complications'] if schematic else ['Source-local '+title.lower()],
                'license':'CC BY 4.0','license_url':article['license_url'],'attribution':credit,'source_background':'white',
                'rights_reviewed_on':DATE,'rights_review':'Original XML grant, complete captions, PDF object placement and independent original sample/profile readback reviewed.'}
            rows.append(row)
            assets.append({'id':ident,'kind':'schematic' if schematic else 'clinical_image','name':title,'local_path':local,'sha256':source['sha256'],
                'regions':['thorax','aorta'],'investigation_ids':[IDENT],'structure_ids':[],'requirement_coverage':{},
                'modality':row['modality'],'source_context':context,
                'source':{'url':article['source_article_url'],'figure_url':row['figure_url'],'asset_url':article['pdf_url'],
                    'license':{'name':'CC BY 4.0','url':article['license_url'],'commercial_use':True,'redistribution':True,
                        'review_status':'verified','evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_raw),'attribution':credit,'reviewed_at':DATE}},
                'pixel_provenance':{'source_pdf_sha256':article['pdf_sha256'],'pdf_object_id':source['pdf_object_id'],
                    'decoded_pixel_sha256':source['decoded_pixel_sha256'],'source_pixels_changed':False,'highest_resolution_acquired_master_verified':False},
                'anatomical_review':{'status':'pending','reason':'Published local examples/conceptual chart do not independently validate complete reportable boundaries, physiology or models.'},
                'visual_review':{'status':'source_checked','sha256':source['sha256'],'reviewed_at':DATE,'evidence_path':'docs/acute-aortic-published-source-review.md'}})
            packaged.append({'figure_number':n,'local_path':local,'sha256':source['sha256'],'kind':row['kind'],'source_pixels_changed':False})
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text())
    data[IDENT]=[r for r in data.get(IDENT,[]) if not r['id'].startswith(PREFIX)]+sorted(rows,key=lambda r:r['figure_number'])
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    path=ROOT/'data/radiology/reporting-steps/cardiovascular.json';raw=path.read_text();start=raw.index('{',raw.index('"'+IDENT+'"'))
    node,end=json.JSONDecoder().raw_decode(raw,start)
    placements={0:[1,3,4],1:[3,4,5,6,7,8,9,10],2:[3],4:[1,5,8,10]}
    for index,numbers in placements.items():node['steps'][index]['images']=list(dict.fromkeys(node['steps'][index].get('images',[])+[PREFIX+str(n) for n in numbers]))
    node['start']={'images':[PREFIX+'2'],'module_illustrations':False}
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    (FOLDER/'packaged-source-images.json').write_text(json.dumps({'figures':packaged,'clinical_approval':False,'model_promoted':False,'structure_coverage_granted':False},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    package(p.parse_args().source_root)
