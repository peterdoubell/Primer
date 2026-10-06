#!/usr/bin/env python3
"""Preserve complete published aortic artwork with explicit patient, phase and representation limits."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
INVESTIGATION='ra.aortic-aneurysm-rupture'
PREFIX='open-aortic-rupture-pmc4035490-fig'
DATE='2026-10-06'
# Panel descriptions are caption-derived, not inferred from pixel appearances.
FIGURES={
 1:('Paired aneurysm size examples',list('ac'),{'a':'enhanced_phase_not_named','c':'enhanced_phase_not_named'},
    {'a':'patient_1','b':'patient_1','c':'patient_1','d':'patient_1'},
    {'a':'baseline','b':'baseline','c':'one_year_later','d':'one_year_later'},
    ['Local axial aneurysm lumen, mural thrombus and outer contour'],
    'Original b/d panels are flat CT-derived parametric renderings, with different displayed colour ranges; they are not acquired geometry, independently registered models or independently calibrated growth measurements.'),
 2:('Calcification discontinuity',list('bc'),dict.fromkeys('bc','unenhanced'),dict.fromkeys('bc','patient_2'),
    {'b':'baseline_asymptomatic','c':'four_years_later_lumbar_pain'},
    ['Local calcified aneurysm wall and source-described new focal gap'],
    'The paired CT views are four years apart. Source-described sizes and focal gap are not independently measured from these bitmaps.'),
 3:('Hyperattenuating crescent',list('b'),{'b':'unenhanced'},{'b':'patient_3'},{'b':'presentation'},
    ['Local aneurysm lumen and source-labelled high-attenuation mural crescent'],
    'The crescent mechanism is illustrated in schematic a. An isolated crescent does not independently establish imminent rupture; symptoms, size/growth and other rupture findings require clinical assessment.'),
 4:('Thrombus fissuration',list('bc'),dict.fromkeys('bc','enhanced_phase_not_named'),dict.fromkeys('bc','patient_4'),dict.fromkeys('bc','pre_repair'),
    ['Local aneurysm lumen, mural thrombus and contrast fissurations in axial/coronal views'],
    'The illustration is schematic a. Static fissuration views do not independently prove the full leak path, haemodynamic behaviour or reported subsequent surgical outcome.'),
 5:('Draped posterior aortic wall',list('b'),{'b':'enhanced_phase_not_named'},{'b':'patient_5'},{'b':'pre_repair'},
    ['Local posterior aneurysm contour, anterior vertebral surface and source-described loss of intervening plane'],
    'Same source patient as Figure 13. Schematic a is a mechanism illustration. Local draping/fissuration needs the full CT and clinical context; the published appearance is not a universal imminent-rupture rule.'),
 6:('Aortoenteric fistula examples',list('bc'),dict.fromkeys('bc','enhanced_phase_not_named'),{'b':'patient_6','c':'patient_7'},
    {'b':'presentation','c':'presentation_after_prior_aaa_repair'},
    ['Local aneurysm/third duodenal portion interface and sac gas in b',
     'Source-described contrast leak into duodenum/stomach in a different patient in c'],
    'Panels b/c depict different patients; never join their anatomy or infer one complete fistula tract. Schematic a is a conceptual bowel connection. Prior graft geometry and operative cause are not resolved by c.'),
 7:('Aortocaval fistula',list('ab'),{'a':'arterial','b':'enhanced_phase_not_named'},dict.fromkeys('ab','patient_8'),dict.fromkeys('ab','presentation'),
    ['Local aneurysm/IVC relationship and source-described fistula leakage with retroperitoneal haematoma'],
    'Panel a is explicitly arterial phase; b is a lower level in the same patient, without separately named phase. These snapshots do not independently delineate the complete tract or measure shunt flow.'),
 8:('Periaortic stranding',list('ab'),dict.fromkeys('ab','enhanced_phase_not_named'),dict.fromkeys('ab','patient_9'),dict.fromkeys('ab','presentation'),
    ['Local periaortic fat stranding in axial/coronal views'],
    'Stranding is nonspecific and cannot alone prove rupture or its absence. A displayed lack of haematoma is confined to the source-described example and provided snapshots.'),
 9:('Contrast extravasation',list('ab'),dict.fromkeys('ab','enhanced_phase_not_named'),dict.fromkeys('ab','patient_10'),dict.fromkeys('ab','presentation'),
    ['Source-described aneurysm contrast leakage and local retroperitoneal haematoma'],
    'The caption does not name arterial or delayed phase. No phase is inferred from brightness; the complete leak, serial evolution and full haemorrhage extent are not supplied.'),
 10:('Retroperitoneal haemorrhage',list('ab'),dict.fromkeys('ab','unenhanced'),dict.fromkeys('ab','patient_11'),dict.fromkeys('ab','presentation'),
     ['Source-labelled bilateral anterior/posterior pararenal haemorrhage, psoas relationships and left kidney displacement'],
     'The caption reports 45 HU, but original calibrated voxel data and independent HU measurements are unavailable. Local axial/coronal views do not establish complete compartment boundaries.'),
 11:('Intraperitoneal and retroperitoneal haemorrhage',list('bc'),dict.fromkeys('bc','unenhanced'),dict.fromkeys('bc','patient_12'),dict.fromkeys('bc','presentation'),
     ['Source-labelled perihepatic space and bilateral paracolic gutters with retroperitoneal haemorrhage'],
     'Schematic a illustrates compartment spread. The caption reports 60 HU, which cannot be independently recovered from display pixels; complete peritoneal and retroperitoneal extent remains unverified.'),
 12:('Open repair context',list('abc'),{'a':'unenhanced','b':'unenhanced','c':'enhanced_phase_not_named'},dict.fromkeys('abc','patient_13'),
     {'a':'pre_repair','b':'pre_repair','c':'post_open_repair_interval_not_named'},
     ['Pre-repair aneurysm and local retroperitoneal haemorrhage', 'Post-repair native aorta/graft junction and source-labelled surgical clip'],
     'Pre/post snapshots are not independently registered; the full graft course, anastomoses, complications and surgical outcome are not validated by these views.'),
 13:('Endovascular repair context',list('ac'),{'a':'enhanced_phase_not_named','c':'post_repair_phase_not_named'},dict.fromkeys('abcd','patient_5'),
     {'a':'pre_repair','b':'deployed_stent_graft_interval_not_named','c':'post_repair_interval_not_named','d':'post_repair_interval_not_named'},
     ['Source-local proximal aneurysm neck in a and deployed stent-graft cross-section in c'],
     'Same patient as Figure 5. Panel b is fluoroscopy, and d is a flat CT-derived volume rendering, not an actual model. Local neck/repair views do not establish every branch, access/landing measurement, endoleak assessment or clinical suitability.')}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def append_evidence(path,assets):
    raw=path.read_text();start=raw.index('[',raw.index('"assets"'))+1;cursor=start;retained=[];decoder=json.JSONDecoder()
    while True:
        cursor+=len(re.match(r'\s*',raw[cursor:]).group())
        if raw[cursor]==']':break
        entry,end=decoder.raw_decode(raw,cursor)
        if not entry['id'].startswith(PREFIX):retained.append(raw[cursor:end])
        cursor=end+len(re.match(r'\s*',raw[end:]).group())
        if raw[cursor]==',':cursor+=1
    retained.extend(json.dumps(a,indent=2,ensure_ascii=False).replace('\n','\n    ') for a in assets)
    path.write_text(raw[:start]+'\n    '+',\n    '.join(retained)+'\n  '+raw[cursor:])


def update_steps(rows):
    path=ROOT/'data/radiology/reporting-steps/abdomen.json';raw=path.read_text();start=raw.index('{',raw.index('"'+INVESTIGATION+'"'))
    node,end=json.JSONDecoder().raw_decode(raw,start);steps=node['steps']
    steps[0]['images']=list(dict.fromkeys(steps[0].get('images',[])+[PREFIX+'1',PREFIX+'13']))
    steps[1]['images']=list(dict.fromkeys(steps[1].get('images',[])+[PREFIX+str(n) for n in (7,8,9,10,11,12)]))
    steps[2]['images']=list(dict.fromkeys(steps[2].get('images',[])+[PREFIX+str(n) for n in (2,3,4,5)]))
    steps[4]['images']=list(dict.fromkeys(steps[4].get('images',[])+[PREFIX+str(n) for n in (6,7,12,13)]))
    steps[1]['normal']='Rupture assessment: [adequate actual phases/coverage / limited / unassessed]. Source-observed leakage, haemorrhage sites/extent and containment uncertainty: [ ].'
    steps[1]['look']='Review actual contrast phases for leak and both retroperitoneal and peritoneal spaces for haemorrhage, including psoas, perirenal/pararenal, pelvic, perihepatic and paracolic compartments. State missing phases or coverage.'
    steps[2]['label']='Wall and thrombus'
    steps[2]['detail']='Describe crescent, fissuration, calcification gaps and posterior wall/vertebral draping in the actual source, with comparison and clinical context. An isolated sign does not establish the timing of rupture.'
    steps[2]['normal']='Wall/thrombus assessment: [adequate actual source and comparison / limited / unassessed]. Observed wall/calcification/thrombus findings and unresolved boundaries: [ ].'
    steps[2]['findings'][0]='Hyperattenuating crescent in the mural thrombus/wall at [ ]; associated findings, symptoms and comparison [ ].'
    steps[2]['tip']='An isolated hyperattenuating crescent is not necessarily a sign of imminent rupture. Assess symptoms, aneurysm size/growth and other CT rupture findings together; immediately communicate suspected rupture or contained leak.'
    steps[3]['normal']='Branch/perfusion assessment: [adequate actual source / limited / unassessed]. Each observed renal/visceral origin, branch patency and organ enhancement finding: [ ]. Uncovered branches, phase and perfusion limits: [ ].'
    steps[3]['look']='Trace actual coeliac, SMA, IMA, bilateral renal and any accessory renal branches through acquired multiplanar images; relate their origins to the neck and sac. Assess covered renal, bowel and visceral enhancement in the actual phase, retaining unassessed branches or organ extent.'
    steps[4]['normal']='Iliac/access/fistula assessment: [adequate actual source / limited / unassessed]. Each side, vessel segment, source measurement and bowel/venous interface finding: [ ]. Repair history, unresolved tract/endpoints and planning limits: [ ].'
    steps[4]['look']='Trace bilateral common/internal/external iliac and common femoral arteries, with actual lumen/wall calibre, tortuosity and calcification. Review source-resolved duodenum/bowel and IVC interfaces and any prior graft/stent-graft. Retain incomplete access, landing-zone, tract or repair coverage.'
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])


def package(root):
    folder=ROOT/'docs/aortic-rupture-published-source-review';proof_path=folder/'original-source-review.json'
    proof_raw=proof_path.read_bytes();proof=json.loads(proof_raw);article=proof['articles'][0]
    if len(proof['articles'])!=1 or article['pmcid']!='PMC4035490' or article['license']!='CC BY 4.0':raise ValueError('Unreviewed article')
    if [s['figure_number'] for s in proof['figures']]!=list(range(1,14)):raise ValueError('Incomplete original selection')
    rows=[];assets=[];packaged=[]
    for source in proof['figures']:
        n=source['figure_number'];ident=PREFIX+str(n);title,panels,phases,patients,timepoints,visible,specific=FIGURES[n]
        source_raw=(root/source['extracted_file']).read_bytes()
        if sha(source_raw)!=source['sha256'] or not source['original_encoded_stream_or_decoded_pixel_readback_verified']:raise ValueError('Original samples differ')
        local=f'web/reference-media/radiology-open/aortic-rupture-pmc4035490-fig{n}.png'
        (ROOT/local).write_bytes(source_raw)
        roles=source['source_panel_types'];schematics=[p for p,t in roles.items() if t=='Schematic']
        state=f'aortic_rupture_source_pmc4035490_fig{n}'
        context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'adult'},'extent':'local',
                 'depicted_state':state,'selected_panels':panels,'panel_types':roles,
                 'panel_states':{p:state for p in panels},'panel_contrast_phases':phases,
                 'panel_patient_ids':patients,'panel_timepoints':timepoints,'panel_identifiers_from_caption':True,
                 'contains_schematic_panels':bool(schematics),'source_schematic_panels':schematics,
                 'source_ct_volume_rendering_panels':list('bd') if n==1 else ['d'] if n==13 else [],
                 'flat_renderings_are_spatial_geometry':False,'full_acquired_series_included':False,
                 'independent_anatomical_validation_verified':False,'independent_timepoint_registration_verified':False,
                 'independent_calibrated_measurements_verified':False,'clinical_suitability_or_outcome_verified':False}
        limits=specific+' Complete acquired voxel series, complete structure/branch/compartment boundaries, independent anatomical review and display calibration are unavailable. No spatial 3D reconstruction, functional measurement or whole-investigation coverage is granted from the artwork.'
        caption=f'Original Figure {n}: {title}. Complete source artwork, labels and annotations are preserved. '+specific
        credit=article['copyright']+' '+', '.join(article['authors'])+'. '+article['title']+'. DOI '+article['doi']+'. CC BY 4.0. Complete original published figure preserved without sample changes. NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.'
        row={'id':ident,'kind':'clinical-image','src':'/app/'+local.removeprefix('web/'),
             'width':source['width'],'height':source['height'],'sha256':source['sha256'],'source_url':article['source_article_url'],
             'figure_url':article['source_article_url']+f'#Fig{n}','figure_number':n,'asset_source_url':article['pdf_url'],
             'modality':'CT','clinical_panels':panels,'image_state':state,'source_context':context,
             'caption':caption,'alt':caption,'source_caption_full':source['source_caption'],'limits':limits,'structures_visible':visible,
             'license':'CC BY 4.0','license_url':article['license_url'],'attribution':credit,'source_background':'white',
             'rights_reviewed_on':DATE,'rights_review':'Original XML grant and complete captions checked for separate credits; original PDF samples/profile and independent Poppler readback verified.'}
        if schematics:row['schematic_structures_visible']=['Original mechanism illustration: '+title]
        if n==13:row['ancillary_structures_visible']=[{'kind':'Radiography','panels':['b'],
            'structures_visible':['Source fluoroscopy of deployed aorto-biiliac stent-graft'],
            'limits':'Fluoroscopy is preserved as ancillary artwork; it is not a CT panel or acquired 3D geometry.'}]
        rows.append(row)
        assets.append({'id':ident,'kind':'clinical_image','name':title+' · original Figure '+str(n),'local_path':local,
            'sha256':source['sha256'],'regions':['abdomen','pelvis'],'investigation_ids':[INVESTIGATION],
            'structure_ids':[],'requirement_coverage':{},'modality':'CT','source_context':context,
            'source':{'url':article['source_article_url'],'figure_url':row['figure_url'],'asset_url':article['pdf_url'],
                      'license':{'name':'CC BY 4.0','url':article['license_url'],'commercial_use':True,'redistribution':True,
                                 'review_status':'verified','evidence_path':str(proof_path.relative_to(ROOT)),
                                 'evidence_sha256':sha(proof_raw),'attribution':credit,'reviewed_at':DATE}},
            'pixel_provenance':{'source_pdf_sha256':article['pdf_sha256'],'pdf_object_id':source['pdf_object_id'],
                                'decoded_pixel_sha256':source['decoded_pixel_sha256'],'source_pixels_changed':False,
                                'highest_resolution_acquired_master_verified':False},
            'anatomical_review':{'status':'pending','reason':'Published local snapshots/mechanism illustrations do not independently validate complete source anatomy, calibrated boundaries or models.'},
            'visual_review':{'status':'source_checked','sha256':source['sha256'],'reviewed_at':DATE,
                             'evidence_path':'docs/aortic-rupture-published-source-review.md'}})
        packaged.append({'local_path':local,'figure_number':n,'sha256':source['sha256'],'source_pixels_changed':False})
    path=ROOT/'data/radiology/radiology-open-images.json';images=json.loads(path.read_text())
    images[INVESTIGATION]=[r for r in images.get(INVESTIGATION,[]) if not r['id'].startswith(PREFIX)]+rows
    path.write_text(json.dumps(images,indent=2,ensure_ascii=False)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets);update_steps(rows)
    (folder/'packaged-source-images.json').write_text(json.dumps({'figures':packaged,'clinical_approval':False,
        'structure_coverage_granted':False,'model_promoted':False},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    package(p.parse_args().source_root)
