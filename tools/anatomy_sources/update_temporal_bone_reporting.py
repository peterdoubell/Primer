#!/usr/bin/env python3
"""Require acquired temporal-bone detail; do not preset normality, tissue identity or implant scala."""
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT = Path(__file__).resolve().parents[2]
IDENT = 'ra.ct-temporal-bone'
URLS = ['https://radiologyassistant.nl/head-neck/temporal-bone/anatomy',
        'https://radiologyassistant.nl/head-neck/temporal-bone/anatomy-2-0',
        'https://radiologyassistant.nl/head-neck/temporal-bone/pathology',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC11913933/']


def update():
    guide = copy.deepcopy(detail(Curriculum(),resolve(IDENT))['radiology_reference']['reporting'])
    details = [
        'Describe each covered canal, membrane, ossicular component/joint, middle-ear compartment and source lesion with actual side, extent and resolution limits.',
        'Assess every covered mastoid cell/septum, aditus/antrum, tegmen and cortical interface; separate opacification from source-supported destruction or complication.',
        'Trace actual cochlear, vestibular, semicircular, window and aqueduct anatomy with source-resolved bone versus unassessed membranous/neural structures.',
        'Describe each acquired facial/neurovascular canal and adjacent ear interface, variant or defect; a visible bony channel does not establish nerve tissue, vascular flow or integrity.',
        'Map every focal lesion, actual fracture course, postoperative change and device component; report acquired source support, extent, artifact and unresolved relationships.'
    ]
    looks = [
        'Review actual thin-section CT planes, sampling and artifact. Follow malleus/incus/stapes components and joints, scutum, membrane, Prussak space and other recesses. Do not replace unresolved tiny structures with a generic ossicular model.',
        'Review covered mastoid/antral regions, septa, tegmen tympani/mastoideum, inner/outer cortex and adjacent dura/venous interfaces. Distinguish source opacification, prior surgical removal, suspected erosion and acquisition limits.',
        'Use actual canal-aligned and orthogonal CT planes when evaluating suspected dehiscence; record the obtained reformat/measurement basis. Trace each cochlear turn, vestibule, canal/crus/ampulla, window and aqueduct where resolved. MRI fluid/neural detail is a separate acquired source.',
        'Follow covered labyrinthine/geniculate/tympanic/mastoid facial canal, IAC, carotid/jugular and sigmoid interfaces and actual variants. Describe source bone coverage and uncertainty rather than assuming normal nerve or vessel course/flow.',
        'Follow full obtained lesion/fracture/device course and all relevant ear, facial, vascular, skull-base and intracranial interfaces. Record surgical history, device type, source artifact and actually acquired contrast/MRI/DWI/ADC information; do not borrow another case or sequence.'
    ]
    tips = [
        'Middle-ear soft tissue and scutum/ossicular change support a differential but do not alone prove cholesteatoma or unique tissue identity. Clinical/otoscopic and acquired MRI evidence remain separate.',
        'Mastoid opacification alone is not proof of coalescent infection. Destruction, extraskeletal extension and adjacent complication need source/clinical support; prior surgery can change expected margins.',
        'Thin bone and partial volume can mimic canal or roof defects. A canal/aqueduct measurement needs its named site, plane, edge convention and calibration; unassessed membranous or neural anatomy stays unresolved.',
        'Suspected exposed/aberrant vascular structures require source-specific characterization and appropriate clinical communication. CT canal shape alone does not establish vessel patency, flow or nerve function.',
        'CT opacification cannot reliably distinguish all postoperative tissue. Actual non-EPI or suitable multi-shot DWI and anatomical MRI are distinct acquired evidence; small lesions/artifact and mimics limit negative and positive interpretations. Exact electrode scala or insertion extent is not assumed when unresolved.'
    ]
    bodies = [
        'Actual side/coverage and canal/membrane findings [ ]; each source-resolved ossicular component/joint [ ]; epitympanic/mesotympanic/hypotympanic/recess extent [ ]; scutum/walls [ ]; soft tissue or erosion with differential [ ]; source resolution/artifact and unassessed structures [ ].',
        'Every covered mastoid/antral/aditus region and cell/septum [ ]; source content/aeration [ ]; tegmen/cortical boundary, surgical removal or suspected defect [ ]; adjacent dural/venous/soft-tissue relation [ ]; source uncertainty and uncovered extent [ ].',
        'Actual cochlear turns/vestibule/canals/crura/ampullae, otic capsule and windows [ ]; aqueduct course/measurement source if supported [ ]; actual CT/reformat planes/resolution [ ]; acquired MRI fluid/neural source if supplied [ ]; variants/lesion and unresolved extent [ ].',
        'Each covered facial canal segment/geniculate region and IAC [ ]; carotid/jugular/sigmoid bony and adjacent tissue interfaces [ ]; source-supported variants/defects or uncertainty [ ]; actual vascular/neural MRI/contrast source if acquired [ ]; unassessed tissue, flow and integrity [ ].',
        'Each source lesion/component and full obtained extent [ ]; acquired MRI sequence/contrast/non-EPI or multi-shot DWI/ADC if available [ ]; actual fracture course and ear/neurovascular/intracranial relations [ ]; supplied surgery/device type and every resolved component [ ]; implant/artifact/scala or endpoint uncertainty [ ]; clinical/otoscopic comparison and unassessed extent [ ].'
    ]
    guide.update(reviewed_at='2026-10-07', protocol=[
        'Record actual CT sampling/reconstruction/planes/coverage, artifact and comparison. Thin-bone, contrast, MRI IAC/inner-ear, DWI/ADC or vascular information are only used when actually acquired or supplied.',
        'Record actual side, supplied hearing/otoscopic symptoms, trauma, surgery/device details and dates. Morphology is distinct from tissue diagnosis, hearing/neural function, flow or complete native anatomy.'
    ])
    guide['checklist'] = [{'label':label,'detail':text} for label,text in zip(['External/middle ear','Mastoid and tegmen','Inner ear','Critical channels','Trauma/postoperative'],details)]
    guide['measurements'] = [
        {'name':'Soft tissue/erosion','method':'Measure each source-resolved lesion/component on actual named orthogonal/local axes with sequence/window, source calibration and obtained extent; map each involved recess/wall rather than a single generic size.','pitfall':'Opacification, erosion or enhancement is not unique histology; selected stills do not establish full extent or postoperative tissue identity.'},
        {'name':'Bony defect','method':'State actual acquired thin-bone source, named defect/canal/aqueduct site, appropriate orthogonal/reformat planes, edge convention, calibration and uncertainty.','pitfall':'Partial volume, artifact, normal variant and prior surgical removal can mimic defects; an unresolved edge cannot yield a normal or dehiscent classification.'}
    ]
    guide['pitfalls'] = tips
    guide['impression_prompts'] = ['Describe actual supported compartment/lesion/device anatomy, full obtained extent and source limitations.',
        'Separate morphology and differential from supplied tissue/clinical confirmation; identify unresolved critical interfaces and unperformed MRI/vascular information.',
        'Report relevant source-supported complications/variants and communicate according to actual clinical context and local pathways.']
    guide['sources'] = [{'title':title,'url':url} for title,url in zip(['RA temporal anatomy1','RA temporal anatomy2','RA temporal pathology','ESHNR middle-ear cholesteatoma recommendations'],URLS)]
    for section,body in zip(guide['template_sections'],bodies): section['body'] = body
    path = ROOT/'data/radiology/investigation-overrides-non-msk.json'; data = json.loads(path.read_text());data.setdefault(IDENT,{})['reporting']=guide
    path.write_text(json.dumps(data,indent=2)+'\n')
    path = ROOT/'data/radiology/reporting-steps/head-neck.json';raw=path.read_text();start=raw.index('{',raw.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(raw,start)
    node['model'] = {'family':'temporal','reporting_aim':'Partial enlarged temporal-bone orientation only. This schematic does not supply native tiny ossicular/joint/wall geometry, all facial/neurovascular/inner-ear/drainage routes, source lesions, implant scala/endpoints, tissue identity or physiological function. Actual acquired sources and unassessed anatomy remain explicit.'}
    findings = [
        ['Source soft tissue in [recess/compartment] with scutum/ossicular change [ ]; differential and supplied clinical/MRI evidence [ ].','Each source-resolved ossicular component/joint abnormality or uncertainty [ ].','Source canal wall/exostosis or other focal change [ ].'],
        ['Mastoid content and each source-supported septal/cortical change [ ]; infection versus postoperative/other differential [ ].','Source tegmen/interface defect or uncertainty [ ]; acquired measurement and adjacent tissue [ ].','Actual postoperative cavity/removal extent and unresolved margins [ ].'],
        ['Source perifenestral/otic-capsule change [ ]; differential and acquired planes [ ].','Aqueduct morphology [ ]; named source measurement/definition if supported [ ].','Source canal/roof defect or partial-volume uncertainty [ ].','Every actual malformation/variant and obtained extent [ ].'],
        ['Each facial canal segment boundary/variant/defect or uncertainty [ ].','Jugular/carotid/sigmoid relation and source-supported variant [ ].','Acquired vascular/neural evidence and missing information [ ].'],
        ['Every obtained fracture course and source ear/neurovascular/intracranial interface [ ].','Every device component/endpoint and source-supported position [ ]; scala/insertion/functional uncertainty [ ].','Each lesion with actually acquired contrast/DWI/anatomical sequences and differential [ ].']
    ]
    for i,step in enumerate(node['steps']):step.update(normal={},detail=details[i],look=looks[i],tip=tips[i],findings=findings[i])
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:])
    print('Five unsupported normal presets removed; temporal anatomy and CT/MRI/device evidence remain source-specific')


if __name__ == '__main__':update()
