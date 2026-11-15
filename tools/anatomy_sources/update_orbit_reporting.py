#!/usr/bin/env python3
"""Require actual ocular/orbital source evidence; morphology does not preset diagnosis or function."""
import copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[2];IDENT='ra.ct-mri-eye'
URLS=['https://radiologyassistant.nl/head-neck/orbita/pathology','https://pmc.ncbi.nlm.nih.gov/articles/PMC11893699/','https://pmc.ncbi.nlm.nih.gov/articles/PMC6095049/']

def update():
    guide=copy.deepcopy(detail(Curriculum(),resolve(IDENT))['radiology_reference']['reporting'])
    details=[
      'Describe each actually covered globe, lens, intraocular and preseptal component with source side, extent, technique and uncertainty.',
      'Localise every actual lesion/collection to its obtained preseptal, extraconal, conal, intraconal or other compartment and trace source boundaries/relationships.',
      'Review each source-resolved extraocular muscle/tendon and optic nerve/sheath component; morphology does not alone establish endocrine/inflammatory/neoplastic identity or function.',
      'Trace actual acquired orbital-apical, canal/foraminal, cavernous, neural/vascular and intracranial interfaces; uncovered or unresolved extent remains unassessed.',
      'Describe each source-supported orbital wall/defect, herniated tissue and adjacent sinus/collection relation; imaging configuration is distinct from clinical entrapment or infection causality.'
    ]
    looks=[
      'Review original acquired planes/windows/sequences, coverage and artifact. Follow globe contour, lens position and source-resolved vitreous/retinal/choroidal or other intraocular components, foreign material and preseptal tissue. Unresolved thin layers and small injuries remain explicit.',
      'Trace every lesion component, capsule/margin or unresolved boundary against the globe, muscle cone, lacrimal region, nerve and wall. Record actual CT/MRI contrast phase, DWI/ADC and comparison if supplied; a selected static image does not establish enhancement kinetics, whole extent or unique histology.',
      'Assess every actual muscle belly/tendon/insertion, optic nerve/sheath and available surrounding fat on resolving acquired planes. Record signal/enhancement, compression or other morphology with uncertainty. Tendon sparing or tram-track appearance has overlap and cannot supply a unique diagnosis or measured visual function.',
      'Review actual apex, optic canal, superior/inferior orbital fissure routes, cavernous region, covered optic pathway/brain/dura and relevant vessels. Contrast, diffusion and vascular acquisitions are separate source evidence; no filling defect, thrombosis, perineural extension or intact interface is assumed from unacquired or inadequate images.',
      'Review actual bony source/reformat planes, every fracture/defect and source herniated fat/muscle/other tissue, adjacent sinuses and collections. Distinguish source morphology from clinical motility/entrapment, globe-pressure state or causal infectious route; prior surgery, artifact and uncovered anatomy remain explicit.'
    ]
    tips=[
      'Record actual MRI safety assessment/clearance when metallic foreign material is a concern; no model or teaching image clears a patient for MRI. Source contour change or material appearance needs appropriate clinical/ophthalmic correlation.',
      'Static enhancement, DWI brightness and compartment location do not uniquely establish abscess, vascular lesion or tumour. Quantitative diffusion and time-dependent filling need their actual acquired ADC/phase sources.',
      'Muscle/tendon and optic nerve/sheath patterns overlap across conditions. Imaging displacement, thickening or enhancement does not by itself measure vision, motility, optic neuropathy or a unique tissue diagnosis.',
      'Apparent apical crowding or venous change must be communicated in actual source/clinical context. Unassessed canal, cavernous or intracranial regions cannot become negative extension or vascular-patency statements.',
      'A muscle near or through a fracture is not proof of clinical entrapment. Sinus opacification does not alone prove the cause of an orbital process; trace actual supported interfaces and limits.'
    ]
    bodies=[
      'Actual side and source globe contour/lens/intraocular components [ ]; each source-supported retinal/choroidal/vitreous finding or unresolved layer [ ]; preseptal tissue and foreign material [ ]; actual MRI safety assessment if applicable [ ]; source planes/resolution/artifact and unassessed extent [ ].',
      'Every actual lesion/collection/component and obtained compartment/extent [ ]; source-resolved margin and globe/muscle/nerve/wall relationships [ ]; actual sequence/contrast phase and DWI/ADC if acquired [ ]; local calibrated measurements and proptosis reference method [ ]; differential and unassessed extent [ ].',
      'Each actual muscle belly/tendon/insertion [ ]; optic nerve/sheath and source signal/enhancement [ ]; source-supported displacement/compression or uncertainty [ ]; acquired technique/resolution and uncovered extent [ ]; supplied clinical visual/motility information kept separate [ ].',
      'Every obtained orbital-apical/canal/fissure/cavernous/neural/vascular/intracranial route [ ]; source-supported contact/continuity/encasement or unresolved interface [ ]; actual contrast/diffusion/vascular technique if acquired [ ]; missing sequences, artifact and unassessed extent [ ].',
      'Every source-supported orbital wall/fracture/defect and acquired bone planes [ ]; each herniated component/connection [ ]; adjacent sinus/collection and supported extension relation [ ]; surgical/variant/artifact limits [ ]; clinical entrapment/motility and infectious context if supplied [ ].'
    ]
    guide.update(reviewed_at='2026-10-07',protocol=[
      'Record actual CT/MRI planes, sampling, coverage, contrast phases, DWI/ADC, artifacts and comparisons. Bone, soft-tissue, vascular and quantitative information are only used when actually acquired or supplied.',
      'Record actual side, age/population, symptoms/vision/motility, trauma/surgery/implant and applicable MRI safety assessment. A static image/model cannot supply physiological state, tissue identity or complete anatomy.'
    ],checklist=[{'label':label,'detail':text} for label,text in zip(['Compartment','Globe','Muscles and nerve','Apex and extension','Bone and infection'],[details[1],details[0],details[2],details[3],details[4]])],pitfalls=tips)
    guide['measurements']=[
      {'name':'Lesion/collection','method':'Measure each source-resolved component on actual named local/orthogonal axes with source calibration, sequence/phase/window and obtained extent; trace surrounding interfaces and uncertainty.','pitfall':'Selected stills do not establish full lesion extent or microscopic boundaries; signal/enhancement alone is not unique diagnosis.'},
      {'name':'Proptosis comparison','method':'If supported, state each globe measurement on the same defined source reference plane with alignment, landmark/edge convention, calibration and uncertainty; actual comparable acquisitions are required.','pitfall':'Rotation, asymmetry, differing planes and prior surgery can change apparent position. Position alone does not establish pressure, visual function or a clinical syndrome.'}
    ]
    guide['impression_prompts']=['Describe actual source-supported compartment/structure involvement and full obtained extent with limitations.','Separate differential and suspected complication from supplied tissue/clinical confirmation; identify every unresolved or unassessed critical interface.','Communicate source-supported vision-risk/traumatic/infectious/vascular concerns according to actual clinical context and local pathways.']
    guide['sources']=[{'title':title,'url':url} for title,url in zip(['RA eye/orbit CT/MRI','2025 paediatric orbital lesion review','Orbital MRI source review'],URLS)]
    for section,body in zip(guide['template_sections'],bodies):section['body']=body
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';data=json.loads(path.read_text());data.setdefault(IDENT,{})['reporting']=guide;path.write_text(json.dumps(data,indent=2)+'\n')
    path=ROOT/'data/radiology/reporting-steps/head-neck.json';raw=path.read_text();start=raw.index('{',raw.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(raw,start)
    node['model']={'family':'orbit','reporting_aim':'Partial orbital orientation only. This schematic does not supply native globe layers, all muscle/tendon/nerve/sheath/canal/vascular routes, source lesions/trauma/device or intracranial extent, unique histology or visual/motility/pressure function. Actual acquired sources and unassessed anatomy remain explicit.'}
    findings=[
      ['Source globe contour/volume or intraocular material change [ ]; injury differential and clinical assessment [ ].','Each source foreign material location/type uncertainty and actual MRI safety assessment [ ].','Source retinal/choroidal or other intraocular finding and unresolved layers [ ].'],
      ['Each source collection/lesion compartment, component and obtained extent [ ]; differential [ ].','Actual acquired enhancement phases or DWI/ADC information [ ]; unresolved kinetics/calibration [ ].','Lacrimal/preseptal or other source tissue component [ ].'],
      ['Every actual muscle belly/tendon/insertion change [ ]; differential and acquired sources [ ].','Optic nerve/sheath signal/enhancement or compression morphology [ ]; clinical function kept separate [ ].'],
      ['Source apical/canal/foraminal/cavernous and intracranial relation [ ]; obtained extent and uncertainty [ ].','Actual contrast/vascular evidence and differential [ ]; unperformed or unassessed information [ ].'],
      ['Each source wall/fracture/defect and herniated component [ ]; local measurement and uncertainty [ ].','Clinical entrapment/motility evidence if supplied [ ]; source morphology alone is insufficient [ ].','Actual sinus/collection relationship and supported extension route [ ]; causal/clinical uncertainty [ ].']
    ]
    for i,step in enumerate(node['steps']):step.update(normal={},detail=details[i],look=looks[i],tip=tips[i],findings=findings[i])
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:]);print('Five orbital normal presets removed; source, diagnosis, MRI safety and function remain distinct')

if __name__=='__main__':update()
