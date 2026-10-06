#!/usr/bin/env python3
"""Require actual covered vessel/territory evidence rather than normal runoff or source-era treatment assumptions."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];IDENT='ra.mra-peripheral-vessels'
RA='https://radiologyassistant.nl/cardiovascular/peripheral-mra/contrast-enhanced-mra-of-peripheral-vessels'
PAD='https://www.jacc.org/doi/10.1016/j.jacc.2024.02.013'
def update():
    path=ROOT/'data/radiology/reporting-steps/cardiovascular.json';data=json.loads(path.read_text());entry=data['investigations'][IDENT];steps=entry['steps']
    details=[
        'Trace the actually covered aortic and iliac inflow, each side and branch configuration; identify unassessed proximal segments.',
        'Map every covered common/deep/superficial femoral and popliteal segment, lesion and variant by side and actual anatomical endpoints.',
        'Describe each lesion and its native-source minimum lumen, reference, length, morphology and uncertainty; distinguish signal loss from confirmed occlusion.',
        'Trace each actual tibial/peroneal artery to its resolved distal endpoint and each pedal/plantar connection, collateral and reconstitution; do not assume three patent channels.',
        'State per-station acquisition, coverage, source quality, contrast/flow timing, venous overlap and artefact; distinguish a non-diagnostic segment from disease.']
    looks=[
        'Original arterial source images plus multiple MIP/reformatted views of covered aorta, bifurcation, common/external/internal iliacs and proximal inflow; check station overlap and origin variants.',
        'Each side: common femoral and bifurcation, profunda and relevant branches, superficial femoral course/adductor canal and complete covered popliteal segment. Trace actual high origins and branch variants.',
        'Native source and orthogonal/curved planes with stated calibration. Record each lesion start/end and reference location; do not infer wall composition, calcium, haemodynamic significance or device lumen from a bright-blood projection alone.',
        'Trace anterior tibial, tibioperoneal trunk if present, posterior tibial and peroneal courses; then dorsalis pedis, medial/lateral plantar, actual plantar/dorsal arch and relevant distal branches. State every covered endpoint and unassessed foot extent. When perforator assessment is requested, document the parent artery, exit/course and source-resolved septal/muscular, cutaneous and fibular-landmark relationships with limits.',
        'Inspect acquired precontrast masks and arterial source/station overlap where present; check bolus timing, slow/in-plane/turbulent flow, subtraction misregistration, motion, venous contamination and metal signal loss. Record the effect on each named segment.']
    tips=[
        'An unopacified or uncovered artery is not automatically absent or occluded. Record variant origins and the source evidence for lumen continuity.',
        'Branch names describe actual observed anatomy; hypoplasia, high origin, trifurcation, dominant peroneal supply and postoperative anatomy must be traced rather than substituted with a normal tree.',
        'Stenosis percentage requires a stated measurement/reference convention and adequate native source. MIP overlap, subtraction and flow or metal artefacts can mimic or exaggerate disease; missing lumen evidence remains uncertain.',
        'Tibial channel count does not establish uninterrupted supply to the foot, a complete pedal arch, wound perfusion or tissue viability. Morphological continuity does not by itself establish flow direction, pressure or clinical effect.',
        'Historical scanner/coil, injection, compression-cuff and pixel-count advice is not a universal current protocol or safety clearance. Suspected acute limb ischaemia requires urgent clinical assessment; do not delay care to obtain a routine MRA.']
    for index,step in enumerate(steps):step.update(normal={},detail=details[index],look=looks[index],tip=tips[index])
    steps[0]['findings']=['Source-supported [ ] lesion in the [side, named inflow artery] from [ ] to [ ]; measurement convention and confidence [ ].','[ ] proximal segment is unassessed because [ ]; no normal patency claim is made.']
    steps[3]['findings']=['[Side] actual traced runoff: [named vessels and resolved endpoints]; unassessed distal segments [ ].','Collateral reconstitution of [ ] at [ ], with source-supported distal continuity to [ ]; flow/function evidence [available / unavailable].','Variant [high origin / trifurcation / hypoplastic channel / dominant peroneal / other actual configuration]: [ ].']
    entry['model']={'family':'aorta','reporting_aim':'Partial aortic orientation only. This companion does not supply patient-specific iliac/femoral/tibial/pedal branches, collateral or graft geometry, stenosis/occlusion, arterial wall or measured flow. Actual vessel identity, runoff, variants, lesions and tissue/clinical effects require the obtained source examination.'}
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    path=ROOT/'data/radiology/investigation-overrides-non-msk.json';data=json.loads(path.read_text());entry=data.setdefault(IDENT,{});guide={
      'reviewed_at':'2026-10-06','protocol':[
       'Record the actual clinical question, symptom/limb-threat context supplied by the clinical team, side, acquired arterial territory and prior intervention. State CE-MRA or actual noncontrast method, source sequences and per-station coverage/quality.',
       'Record source voxel calibration and acquired versus reconstructed resolution, mask/arterial phases, station overlap and contrast agent/dose/timing if given. Use original source images with multiple reconstructions; unperformed acquisitions and uncovered segments remain unassessed.'],
      'checklist':[{'label':label,'detail':detail} for label,detail in zip(['Inflow','Segmental Disease','Lesion Morphology','Runoff And Collaterals','Technical Limitations'],details)],
      'measurements':[{'name':'Lesion length','method':'Measure each lesion along its actual vessel axis between named source-supported proximal/distal landmarks; record minimum orthogonal lumen, reference site/convention, units and uncertainty if assessed.','pitfall':'Signal loss is not automatically occlusion; an unsupported percentage or projection width is not a calibrated lumen measurement.'}],
      'classification':None,'criteria_table':None,'pitfalls':tips,
      'impression_prompts':['Summarise dominant source-supported disease by side, named segment, extent and actual distal continuity.','Describe variants, intervention anatomy and confidence; identify unanswered distal-target or clinical questions and non-diagnostic/uncovered segments.','Do not infer haemodynamic severity, wound perfusion, limb viability or treatment outcome from a static angiographic appearance.'],
      'escalation':['Urgently communicate source findings and limitations when acute limb ischaemia or threatened limb is suspected; clinical viability assessment and management should not be delayed for routine MRA.'],
      'template_sections':[
       {'heading':'INFLOW','body':'Actual coverage/side [ ]; covered aortic/iliac origins and branches [ ]; named inflow patency or lesion source [ ]; variant/common origin [ ]; unresolved proximal extent [ ].'},
       {'heading':'SEGMENTAL DISEASE','body':'Each covered right/left named vessel and proximal/distal landmarks [ ]; common femoral/bifurcation, profunda/relevant branches, superficial femoral/adductor and popliteal segments [ ]; each lesion [ ]; high origin/trifurcation/dominance or other variant [ ]; intervention anatomy [ ]; unassessed segments [ ].'},
       {'heading':'LESION MORPHOLOGY','body':'Each actual site/side [ ]; lesion length/axis/endpoints [ ]; minimum orthogonal lumen and reference site/convention if measurable [ ]; percentage or qualitative assessment with confidence [ ]; aneurysm/dissection/thrombus or other component if source resolved [ ]; vessel-wall assessment limits [ ]; flow/metal/subtraction mimics and uncertainty [ ].'},
       {'heading':'RUNOFF AND COLLATERALS','body':'Each actual tibial/peroneal channel and proximal/distal continuity [ ]; dorsalis pedis, medial/lateral plantar and actual pedal/plantar arch connections [ ]; collateral origin/course/reconstitution [ ]; graft distal target/outflow if present [ ]; covered wound-region relation if supplied [ ]; flow/perfusion/viability evidence or unavailable tests [ ]; unassessed foot/branch extent [ ].'},
       {'heading':'TECHNICAL LIMITATIONS','body':'Actual CE/noncontrast method and sequences [ ]; acquired/reconstructed resolution, source calibration and station coverage/overlap [ ]; masks/subtraction and contrast/flow timing [ ]; venous overlap, motion, slow/turbulent flow, susceptibility/metal and other artefact with named affected segments [ ]; source-resolved extravascular findings and limits [ ]; comparison examination/method and interval change [ ]; additional territory requiring separate source/anatomy assessment [ ].'}],
      'sources':[{'title':'Radiology Assistant — peripheral CE-MRA (source-era protocol context)','url':RA},{'title':'2024 multisociety lower-extremity PAD guideline','url':PAD}]}
    entry['reporting']=guide;path.write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':update()
