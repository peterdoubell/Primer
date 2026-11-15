#!/usr/bin/env python3
"""Require acquired nodal morphology and named map; never preset benignity, pENE or primary stage."""
import copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
ROOT=Path(__file__).resolve().parents[2];IDENT='ra.cervical-lymph-nodes'
URLS=['https://radiologyassistant.nl/head-neck/cervical-node-mapping/cervical-node-map','https://ashnr.org/iene/','https://pubmed.ncbi.nlm.nih.gov/38936388/','https://pmc.ncbi.nlm.nih.gov/articles/PMC12883938/']
def update():
    guide=copy.deepcopy(detail(Curriculum(),resolve(IDENT))['radiology_reference']['reporting'])
    details=[
      'Assign every source node/group actual side and descriptive location using the explicitly named map/version, acquired boundaries and coverage limits.',
      'Inventory actual covered nodes/components and distribution; index-node measurements do not replace all obtained nodal or non-nodal extent.',
      'Describe each source-resolved nodal margin/cortex/hilum/content and actual signal/contrast/diffusion or ultrasound findings with uncertainty and differential.',
      'Trace source nodal-to-fat/adjacent-node/muscle/skin/gland/vascular interfaces; separate imaging suspicion from supplied pathological ENE and vascular function.',
      'Review actual covered primary-site/airway/other tissue and supplied clinical/tissue/assay/staging context; morphology alone does not identify a primary, organism or molecular category.'
    ]
    looks=[
      'Use actual acquired skull-base/lower-neck extent, planes and map-specific boundaries such as glands, muscles, hyoid, cricoid and vessels. Extended radiotherapy and surgical labels are not interchangeable; record descriptive location for every unassigned or differently defined region.',
      'Trace every actual covered node/group and conglomerate component, including tiny or normal-sized but morphologically concerning nodes. Measure source-resolved local short/long axes with node identity, site, sequence/phase, calibration and comparison; selected index nodes do not quantify all burden.',
      'Inspect each actual source margin, cortical/hilar/content component, necrotic-appearing/cystic/calcific area and adjacent node. CT/MRI contrast/DWI/ADC, ultrasound cortex/hilum and Doppler are separate acquired sources; a permitted modality does not supply unperformed measurements or tissue identity.',
      'Assess all source-supported adjacent tissue and vascular contacts, fat-plane/capsular appearances, coalescent components and obtained extent. Record actual source technique, uncertainty and comparison. Contact/stranding or matting alone is not pathological ENE, vessel invasion, thrombosis, flow loss or surgical resectability.',
      'Review only actually covered mucosal/tonsillar/tongue-base/laryngeal, thyroid/salivary and other source sites. Record supplied primary/treatment/surgery/biopsy/HPV or other assay dates separately. Any staging system/version/category needs the confirmed applicable clinical/tissue context and all required source findings.'
    ]
    tips=[
      'Name the map and version. A level number in one surgical/extended radiotherapy convention cannot silently become the same compartment in another; unknown boundaries remain unassigned.',
      'Small size or a preserved visible feature does not prove benignity or exclude microscopic metastasis. Size thresholds and index-node choices depend on the actual disease/level and source context.',
      'Cystic adult lateral-neck nodes/masses require an appropriate differential and clinical/tissue evaluation; neither benign congenital cyst nor unique metastatic/HPV/thyroid identity is established from morphology alone.',
      'Imaging-detected ENE is distinct from pathological ENE. Use actual applicability and source criteria with confidence; post-treatment inflammation, unresolved borders and vessel contact require explicit limits.',
      'Absent visible primary in limited imaging is not exclusion of an occult primary. Assay/organism/histology and primary-specific stage are supplied evidence, not geometry or generic nodal patterns.'
    ]
    bodies=[
      'Actual named map/version and descriptive boundaries [ ]; every obtained right/left/group/other region and node identity [ ]; map-dependent/unassigned labels [ ]; coverage, technique and unresolved extent [ ].',
      'Every relevant actual node/group/component and source distribution [ ]; index-node identity/side/descriptive location/map level [ ]; local short/long axes/calibration/sequence/series/image [ ]; actual comparison if obtained [ ]; uncovered nodes or unresolved burden [ ].',
      'Each source-resolved node margin/cortex/hilum/content [ ]; actual cystic/necrotic-appearing/calcific/other components and differential [ ]; acquired CT/MRI contrast/DWI/ADC or US/Doppler information [ ]; coalescence/comparison and tissue/technique uncertainty [ ].',
      'Every actual nodal-to-fat/node/muscle/skin/gland/vascular interface and obtained extent [ ]; imaging-detected ENE suspicion/criteria/applicability/confidence or unassessed state [ ]; actual vessel contact/course/phase and unresolved wall/patency/flow [ ]; supplied pathological ENE if available kept separate [ ].',
      'Actually covered mucosal/thyroid/salivary/other sites and airway [ ]; source-supported primary finding/differential and unassessed anatomy [ ]; supplied primary/treatment/tissue/HPV or other clinical evidence and dates [ ]; applicable staging system/version and unresolved required components [ ].'
    ]
    guide.update(reviewed_at='2026-10-07',protocol=[
      'Record actual CT/MRI/ultrasound coverage, planes, sampling, contrast/DWI/ADC/Doppler, artifact and comparison. Node levels need the named map and acquired boundaries; sources are not borrowed across patients or modalities.',
      'Record supplied primary, histology/assays, treatment/surgery and dates. Imaging morphology is distinct from pathological ENE, molecular identity, organism, vascular function and primary-specific stage.'
    ],checklist=[{'label':label,'detail':text} for label,text in zip(['Map','Burden','Morphology','Extranodal spread','Primary and pathway'],details)],pitfalls=tips)
    guide['measurements']=[
      {'name':'Nodal dimensions','method':'For every relevant index node, state actual identity/site/map/side, local short/long-axis planes, edge convention, calibrated source, series/image and uncertainty.','pitfall':'Normal-sized morphology does not exclude disease; thresholds are context/level dependent and must not be borrowed from another population or primary.'},
      {'name':'Conglomerate extent','method':'Map every obtained coalescent component and actual local/orthogonal source dimensions with adjacent vessel/skin/muscle/gland interfaces, phase/calibration and uncertainty.','pitfall':'Matting, contact or a measured arc does not itself prove pathological ENE, invasion, flow compromise or resectability.'}
    ]
    guide['classification'].update(version='Actual explicitly named surgical or extended radiotherapy map/version',applicability='Source-supported anatomic localisation only; iENE applicability and primary-specific staging remain separate actual clinical/source domains.',summary='Give descriptive location plus map-dependent label and unresolved boundary. Do not assign a universal ENE grade, primary stage or molecular category from generic morphology.')
    guide['impression_prompts']=['Describe actual source node/group distribution, morphology and obtained extent with the named map/limits.','Report source-supported imaging ENE/adjacent vascular/tissue concerns and uncertainty; pathological/clinical evidence remains separate.','State supplied primary-specific/assay/treatment context and unresolved staging/sampling questions without inventing missing evidence.']
    guide['sources']=[{'title':title,'url':url} for title,url in zip(['RA cervical node map','ASHNR imaging ENE framework','HNCIG 2024 imaging ENE consensus','2026 source imaging ENE review'],URLS)]
    for section,body in zip(guide['template_sections'],bodies):section['body']=body
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';data=json.loads(path.read_text());data.setdefault(IDENT,{})['reporting']=guide;path.write_text(json.dumps(data,indent=2)+'\n')
    path=ROOT/'data/radiology/reporting-steps/head-neck.json';raw=path.read_text();start=raw.index('{',raw.index('"'+IDENT+'"'));node,end=json.JSONDecoder().raw_decode(raw,start)
    node['model']={'family':'neck','reporting_aim':'Partial neck orientation only. This schematic does not supply every native patient node/level boundary, cortex/hilum/capsule or extranodal/vascular interface, microscopic metastasis, primary/assay identity, stage or flow. Actual acquired sources and unassessed anatomy remain explicit.'}
    findings=[
      ['Every actual source side/descriptive group/node [ ]; map/version/level or unresolved assignment [ ].','Retropharyngeal/parotid/other source region [ ]; named convention and actual boundaries [ ].'],
      ['Each index node/component with actual identity/local axes/source measurement [ ].','Actual obtained distribution/coalescence and unresolved burden [ ].'],
      ['Source cystic/necrotic-appearing/hilar/cortical/calcium or other component [ ]; differential and supplied tissue/assay information [ ].','Actual acquired contrast/DWI/ADC/US/Doppler details and unavailable source information [ ].'],
      ['Source margin/adjacent tissue/vascular relation [ ]; imaging ENE suspicion and confidence [ ].','Actual carotid/venous contact/phase/source measurement and unassessed wall/patency/function [ ].','Pathological ENE if supplied [ ]; not established solely by imaging [ ].'],
      ['Every covered primary-site/airway/other tissue finding and unassessed extent [ ].','Supplied primary/assay/treatment evidence and applicable staging system/version [ ]; unresolved components [ ].']
    ]
    for i,s in enumerate(node['steps']):s.update(normal={},detail=details[i],look=looks[i],tip=tips[i],findings=findings[i])
    path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+raw[end:]);print('Three unsupported normal presets removed; map, imaging/pathology ENE and staging evidence kept separate')
if __name__=='__main__':update()
