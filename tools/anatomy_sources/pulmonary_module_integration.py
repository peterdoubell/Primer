"""Apply the bounded reviewed pulmonary module amendments, preserving other tokens."""
from pathlib import Path
import copy
import hashlib
import json
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
REVIEW=ROOT/'docs/pulmonary-nodule-integration-review-20261011'
SOURCE_REVIEW=ROOT/'docs/pulmonary-nodule-source-review-20261011'
INDEPENDENT=ROOT/'docs/pulmonary-nodule-independent-review-20261011'
CASE='ra.ct-pulmonary-nodules'
NODE='rad.4.pulmonary-nodule'
DECODER=json.JSONDecoder()


def sha(b):return hashlib.sha256(b).hexdigest()
def digest(x):return sha(json.dumps(x,sort_keys=True,separators=(',',':')).encode())
def spaces(s):return re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',s)


def value_span(raw,start,path):
    """Locate one JSON value by path without rewriting unrelated JSON tokens."""
    while raw[start].isspace():start+=1
    if not path:
        _,stop=DECODER.raw_decode(raw,start);return start,stop
    target,*rest=path
    if raw[start]=='{':
        at=start+1
        while True:
            while raw[at].isspace() or raw[at]==',':at+=1
            if raw[at]=='}':break
            key,at=DECODER.raw_decode(raw,at)
            while raw[at].isspace():at+=1
            assert raw[at]==':';at+=1
            while raw[at].isspace():at+=1
            if key==target:return value_span(raw,at,rest)
            _,at=DECODER.raw_decode(raw,at)
    elif raw[start]=='[':
        at=start+1;index=0
        while True:
            while raw[at].isspace() or raw[at]==',':at+=1
            if raw[at]==']':break
            if index==target:return value_span(raw,at,rest)
            _,at=DECODER.raw_decode(raw,at);index+=1
    raise KeyError(path)


def replace(path,keys,value):
    raw=path.read_text();start,stop=value_span(raw,0,keys)
    original=json.loads(raw[start:stop]);indent=len(raw[:start].rsplit('\n',1)[-1])-len(raw[:start].rsplit('\n',1)[-1].lstrip())
    rendered=json.dumps(value,indent=2,ensure_ascii=False)
    rendered=rendered.replace('\n','\n'+' '*indent)
    path.write_text(raw[:start]+rendered+raw[stop:])
    return dict(path=str(path.relative_to(ROOT)),keys=keys,original_sha256=digest(original),current_sha256=digest(value),unrelated_raw_tokens_preserved=True)


def put_top(path,key,value):
    parsed=json.loads(path.read_text())
    if key in parsed:return replace(path,[key],value)
    raw=path.read_text();close=raw.rfind('}');before=raw[:close].rstrip();entry=json.dumps(value,indent=2,ensure_ascii=False).replace('\n','\n  ')
    new=before+',\n  '+json.dumps(key)+': '+entry+'\n'+raw[close:]
    assert {k:v for k,v in json.loads(new).items() if k!=key}==parsed
    path.write_text(new)
    return dict(path=str(path.relative_to(ROOT)),keys=[key],original_absent=True,current_sha256=digest(value),unrelated_raw_tokens_preserved=True)


def append_list(path,keys,value):
    raw=path.read_text();start,stop=value_span(raw,0,keys)
    entries=json.loads(raw[start:stop]);assert isinstance(entries,list)
    closing=stop-1
    first_line=raw[:start].rsplit('\n',1)[-1]
    indent=len(first_line)-len(first_line.lstrip())+2
    encoded=json.dumps(value,indent=2,ensure_ascii=False).replace('\n','\n'+' '*indent)
    before=raw[:closing].rstrip()
    path.write_text(before+(',\n' if entries else '\n')+' '*indent+encoded+'\n'+' '*(indent-2)+raw[closing:])
    return dict(path=str(path.relative_to(ROOT)),keys=keys,appended_id=value.get('investigation_id'),original_sha256=digest(entries),current_sha256=digest(entries+[value]),unrelated_raw_tokens_preserved=True)


def main():
    REVIEW.mkdir(exist_ok=True)
    amendment_raw=(INDEPENDENT/'clinical-amendment-proposal.json').read_bytes()
    assert sha(amendment_raw)=='f172a46b75c14554b830c480e65ea7991a5e63457b71bc054ce8be65eb5075a1'
    amendment=json.loads(amendment_raw)
    reporting=json.loads((SOURCE_REVIEW/'reporting-proposal.json').read_text())
    original=json.loads((SOURCE_REVIEW/'current-scope-snapshot.json').read_text())
    guide=copy.deepcopy(original['effective_reference']['reporting'])
    guide['protocol']=reporting['proposed_protocol']
    assert guide['protocol'][0]==amendment['protocol_amendment']['before']
    guide['protocol'][0]=amendment['protocol_amendment']['after']
    details=[
      'Record actual indication, age, immune status, cancer history, screening context, relevant risk/comorbidity and guideline exclusions before a follow-up decision.',
      'Inventory every actual nodule by ID, side/lobe/segment where supported, source series/image and solid/pure-ground-glass/part-solid appearance; retain unassessed localization or morphology.',
      'Describe actual whole-nodule and dense-component boundaries, margins, verified fat/calcium pattern and pleural/fissural/airway/vascular interfaces. CT appearance and reader ratings are not histology.',
      'Record actual same-plane long/short axes, rounded mean diameter and separate dense-component dimensions; use consistent validated volumetry and software where appropriate. Distinguish point HU from a verified small intranodular ROI.',
      'Review genuine original comparison studies, technical compatibility and actual interval; identify each new or changing component and the most suspicious nodule without inventing a prior from a source example.'
    ]
    for i,row in enumerate(guide['checklist']):row['detail']=details[i]
    guide['measurements']=[
      {'name':'Mean diameter','method':'On thin reconstructed images use the plane showing largest dimensions, average long and perpendicular short axes on the same image and record the nearest whole mm. Record actual source plane and uncertainty.','pitfall':'Source SR maximal axial outside-contour diameter is not the Fleischner mean-caliper measurement; thick or incompatible reconstructions and partial volume can alter apparent morphology/size.'},
      {'name':'Solid component','method':'Measure each actual dense component separately on comparable thin-section lung-window images; record total size, component size, source plane and technical limitations.','pitfall':'Whole-nodule stability does not negate dense-component growth; CT density is not proof of histological invasion.'},
      {'name':'Intranodular attenuation ROI','method':'When measuring suspected fat or calcium, use the thinnest available nonsharpened source CT series and a small ROI within the actual nodule, excluding adjacent air, edges and artefact; record mean/range, source calibration and limitations.','pitfall':'A native point HU readout or edge-contaminated negative value does not establish intranodular macroscopic fat, a hamartoma or a clinical diagnosis.'},
      {'name':'Interval size or volume change','method':'Reopen actual prior images, remeasure comparable anatomy and record dates, elapsed time, reconstruction/kernel compatibility and method/software version. State uncertainty where growth cannot be established.','pitfall':'This LIDC source supplies one examination; deidentified dates, reader disagreements and separate masks are not longitudinal growth or patient registration.'}
    ]
    guide['classification']['summary']='Use the applicable single/multiple and solid/pure-ground-glass/part-solid pathway and actual risk/context. Screening uses its current programme system; known malignancy/immunocompromise and other exclusions require the actual clinical pathway. Guidelines and source annotations do not automatically determine a patient recommendation.'
    guide['pitfalls']=[
      'Fleischner2017 applies to qualifying incidental nodules in adults 35 or older, excluding screening, immunocompromise and known primary cancer. Do not mix Fleischner, BTS and Lung-RADS thresholds.',
      'Complete typical benign perifissural morphology matters; fissural proximity alone is insufficient. Apparent fat requires a verified intranodular ROI on appropriate source reconstructions.',
      'Negative FDG PET does not reliably exclude malignancy in a pure-ground-glass or low-uptake lesion; morphology, size, actual interval change and clinical context remain necessary.',
      'Persistence, reader malignancy ratings, a dense component and a source binary mask do not establish histology or guaranteed biological behaviour.',
      'DICOM SliceThickness records nominal reconstructed thickness; acquired collimation, true tissue resolution and registration must not be inferred from the voxel grid.',
      'LIDC-IDRI-0525 is one independent source case. Its33marks/eight separate released masks and source SR metrics neither autofill the current report nor label every lobe, segment, airway, vessel or diagnostic morphology.'
    ]
    guide['pitfalls']=[spaces(s) for s in guide['pitfalls']]
    guide['impression_prompts']=[
      'Describe every actual nodule with supported site, morphology, total/dense-component measurement and uncertainty.',
      'State genuine comparison findings and reconstruction/method compatibility, or explicitly state that no comparable prior was supplied.',
      'Identify the most suspicious nodule and give an individualized recommendation only after recording eligibility, risk, the exact guideline/version/category and rationale.'
    ]
    guide['template_sections']=[
      {'heading':'PATHWAY','body':'Actual context: [incidental / screening / oncology / infection or other]. Age, immune status, cancer history, symptoms, risk/comorbidity and preferences: [ ]. Guideline eligibility/exclusions and selected pathway/version: [ ].'},
      {'heading':'NODULE INVENTORY','body':'Every actual nodule ID: [ ]. Side/lobe/segment and localization limits: [ ]. Source series/image: [ ]. Appearance: [solid / pure ground glass / part-solid / uncertain]; unresolved extent or limits: [ ].'},
      {'heading':'SIZE AND MORPHOLOGY','body':'Actual largest-dimension source plane: [ ]. Long/short axes: [ ]/[ ] mm; rounded mean: [ ] mm. Total/each dense-component size: [ ]. Validated volume/software/version if used: [ ]. Margins and actual pleural/fissural/airway/vascular relations: [ ]. Verified ROI fat/calcium distribution and method/limits: [ ].'},
      {'heading':'INTERVAL CHANGE','body':'Genuine prior date and source examination: [ ]. Remeasured previous/current total/dense-component size or volume: [ ]. Method, software/version, thickness/kernel and other comparability: [ ]. Change: [none demonstrated / present / uncertain / not assessable]; elapsed interval and limits: [ ].'},
      {'heading':'ASSESSMENT','body':'Most suspicious actual nodule and reason: [ ]. Benign-pattern evidence and uncertainty: [ ]. Applicable single/multiple and solid/subsolid guideline/version/category: [ ]. Individualized recommendation, timeframe, rationale and communication if needed: [ ].'}
    ]
    guide['sources']=copy.deepcopy(reporting['proposed_additional_primary_sources'])+[
      {'title':'Original LIDC-IDRI CT data and source annotations','url':'https://doi.org/10.7937/K9/TCIA.2015.LO9QL9SX'},
      {'title':'Standardized LIDC DICOM SEG/SR source data','url':'https://doi.org/10.7937/TCIA.2018.h7umfurq'},
      {'title':'Armato et al. original LIDC reader methods','url':'https://doi.org/10.1118/1.3528204'},
      {'title':'Fedorov et al. standardized DICOM re-encoding methods','url':'https://doi.org/10.1002/mp.14445'}]
    guide['reviewed_at']='2026-10-11'
    deltas=[]
    path=ROOT/'data/curriculum/11-radiology.json';curriculum=json.loads(path.read_text());index=next(i for i,n in enumerate(curriculum['nodes']) if n['id']==NODE)
    assert curriculum['nodes'][index]['quiz'] in (amendment['original_questions'],amendment['independent_amended_questions'])
    deltas.append(replace(path,['nodes',index,'quiz'],amendment['independent_amended_questions']))
    deltas.append(replace(ROOT/'data/radiology/reporting-body.json',[NODE],guide))
    models=json.loads((ROOT/'data/radiology/reporting-models.json').read_text());model=copy.deepcopy(models[NODE])
    model.update(title='Native CT and separate original nodule models',instructions='Inspect the complete source CT and all separate released reader masks in the native source viewer. No generic lobe geometry or current-patient anatomical coverage is assigned.',source_native_only=True,focus=['native-source'],reporting_aim='Complete source-case inspection with explicit unresolved reporting-structure fidelity.')
    deltas.append(replace(ROOT/'data/radiology/reporting-models.json',[NODE],model))
    steps=copy.deepcopy(reporting['proposed_walkthrough_steps'])
    for i,step in enumerate(steps):
        step['landmark']='native-source';step['parts']=[];step['images']=[]
        heading=step['sections'][0];step['normal']={heading:guide['template_sections'][i]['body']}
        step['anatomy_note']='Source CT and separate released reader masks remain inspectable. None of the79conditional reporting groups has been granted clinical/fine-anatomical coverage, and this case does not provide a current-patient observation or a matched prior/PET study.'
        step['detail']=details[{0:0,1:1,2:3,3:4,4:0}[i]]
    steps[2]['measurements']=['Mean diameter','Solid component','Intranodular attenuation ROI']
    steps[2]['look']='Use the actual largest-dimension thin source plane for calipers; measure suspected fat/calcium with a small intranodular ROI on the thinnest available nonsharpened reconstruction, excluding air/edges. The native viewer point readout is not that ROI.'
    steps[3]['measurements']=['Interval size or volume change']
    steps[3]['look']='Compare actual original prior CT with explicit dates, reconstruction/kernel compatibility, matching convention and consistent validated volumetry/software if used; this source case has no longitudinal examination.'
    step_value={'walkthrough_reviewed_at':'2026-10-11','preset_mode':'assessment-prompts','start':{'images':[],'module_illustrations':False},'steps':steps}
    deltas.append(replace(ROOT/'data/radiology/reporting-steps/chest.json',['investigations',CASE],step_value))
    override=dict(reporting=guide,reading=copy.deepcopy(guide['sources']),additional_sources=copy.deepcopy(guide['sources']),key_images=[],suppress_visual_fallback=True,source_native_only=True,
      overview='Assess the full incidental-nodule context, every actual nodule/diagnostic feature and real interval comparison. Inspect the complete reviewed LIDC source CT with all original XML marks and separate released masks, while retaining all unresolved clinical and fine-anatomical coverage.',
      learning_points=['Use the actual incidental/screening/oncology/infectious pathway and eligibility, with explicit single/multiple and solid/subsolid distinctions.','Preserve original source values, geometry, reader disagreements and measurement definitions; source annotations are not histology or a current-patient diagnosis.','All79conditional structure groups and625parts still require explicit actual-site representation review; every1875image/schematic/model obligation remains unverified.'],spatial_model=model)
    deltas.append(put_top(ROOT/'data/radiology/investigation-overrides-non-msk.json',CASE,override))
    # Build the actual changed effective contract only after all registry/guide
    # changes are present, never carry forward the former reporting hash.
    from primer.curriculum import Curriculum
    from primer import radiology_catalog
    c=Curriculum();r=radiology_catalog.detail(c,radiology_catalog.resolve(CASE))['radiology_reference']
    contract={k:r.get(k) for k in ['reporting','report_templates','walkthrough','reading']}
    inventory=copy.deepcopy(json.loads((SOURCE_REVIEW/'structure-requirements-proposal.json').read_text()))
    inventory.update(clinical_validation_status='draft_requires_thoracic_radiologist_review',source_contract_sha256=digest(contract),reporting_checklist=guide['checklist'],reporting_template_sections=guide['template_sections'],shared_curriculum_quiz_sha256=digest(amendment['independent_amended_questions']),modality_scope=['CT','PET-CT'],original_source_scope_proposal_sha256=sha((SOURCE_REVIEW/'structure-requirements-proposal.json').read_bytes()),original_shared_curriculum_quiz_sha256=amendment['owner_original_quiz_sha256'],runtime_integrated=True)
    for structure in inventory['structures']:
        structure['modality_scope']=['PET-CT','CT'] if '.PET_' in structure['id'] else ['CT']
        structure['condition']=structure.pop('conditional_scope')
        structure['requirement_basis']='complete_reporting_and13_question_conditional_scope'
    path=ROOT/'data/radiology/non-msk-structure-requirements.json';all_inventory=json.loads(path.read_text());entries=all_inventory['investigations']
    old_index=next((i for i,n in enumerate(entries) if n['investigation_id']==CASE),None)
    if old_index is None:
        deltas.append(append_list(path,['investigations'],inventory))
    else:deltas.append(replace(path,['investigations',old_index],inventory))
    all_inventory=json.loads(path.read_text())
    if CASE not in all_inventory['scope']['catalog_investigation_ids']:
        deltas.append(replace(path,['scope','catalog_investigation_ids'],all_inventory['scope']['catalog_investigation_ids']+[CASE]))
    baseline_inventory=json.loads((REVIEW/'baseline/data/radiology/non-msk-structure-requirements.json').read_text())
    indexed=json.loads(path.read_text())['scope']['catalog_investigation_ids']
    assert indexed==baseline_inventory['scope']['catalog_investigation_ids']+[CASE]
    result=dict(schema_version=1,source_commit='bca576f8d03c5a6ed3c49ea7c7370bde7fb7327e',independent_amendment_sha256=sha(amendment_raw),bounded_deltas=deltas,original_questions_preserved_in_frozen_source_reviews=True,
       changed_question_indices=[i for i,(a,b) in enumerate(zip(amendment['original_questions'],amendment['independent_amended_questions'])) if a!=b],current_quiz_sha256=digest(amendment['independent_amended_questions']),current_effective_contract_sha256=digest(contract),
       groups=79,parts_floor=625,representation_obligations_floor=1875,verified_obligations=0,clinical_approval=False,fine_anatomical_approval=False,structure_coverage_granted=False)
    result['scope_index_expansion']={'path':'data/radiology/non-msk-structure-requirements.json','keys':['scope','catalog_investigation_ids'],
                                    'original_ids_sha256':digest(baseline_inventory['scope']['catalog_investigation_ids']),
                                    'current_ids_sha256':digest(indexed),'only_appended_id':CASE}
    (REVIEW/'clinical-reporting-scope-integration.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='bounded_deltas'},indent=2))


if __name__=='__main__':main()
