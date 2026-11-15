"""Independent question/scope replay and bounded review amendment proposal.

Original owner questions and proposals remain immutable. Grader agreement is
only rubric evidence, never clinical approval or source-case scenario proof.
"""
from pathlib import Path
import copy,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from primer.quiz import score_quiz
OWNER=ROOT/'docs/pulmonary-nodule-source-review-20261011'
REVIEW=ROOT/'docs/pulmonary-nodule-independent-review-20261011'
def digest(o):return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def node_in(o):
    if isinstance(o,dict):
        if o.get('id')=='rad.4.pulmonary-nodule':return o
        for v in o.values():
            r=node_in(v)
            if r:return r
    elif isinstance(o,list):
        for v in o:
            r=node_in(v)
            if r:return r

def main():
    s=json.loads((OWNER/'current-scope-snapshot.json').read_text());p=json.loads((OWNER/'complete-clinical-question-proposal.json').read_text());scope=json.loads((OWNER/'structure-requirements-proposal.json').read_text());report=json.loads((OWNER/'reporting-proposal.json').read_text())
    original=node_in(json.loads(subprocess.check_output(['git','show',s['base_commit']+':data/curriculum/11-radiology.json'],cwd=ROOT)))
    current=node_in(json.loads((ROOT/'data/curriculum/11-radiology.json').read_text()))
    assert original==current
    assert original['quiz']==s['node']['quiz'] and original['goal']==s['node']['goal']
    from primer.curriculum import Curriculum
    curriculum=Curriculum()
    assert curriculum.nodes['rad.4.pulmonary-nodule']==s['node']
    from primer.radiology_catalog import detail,resolve
    assert resolve('ra.ct-pulmonary-nodules')==s['investigation']
    assert detail(curriculum,resolve('ra.ct-pulmonary-nodules'))['radiology_reference']==s['effective_reference']
    assert digest(original['quiz'])==p['original_quiz_sha256']==scope['shared_curriculum_quiz_sha256']
    assert [r['original'] for r in p['questions']]==original['quiz'] and len(p['questions'])==13
    proposed=[r['proposed'] for r in p['questions']];assert digest(proposed)==p['proposed_quiz_sha256']
    assert [r['index'] for r in p['questions'] if r['changed']]==[1,2,3,4,5,6,7,9,10,11]
    structures=scope['structures'];assert len(structures)==79 and len({r['id'] for r in structures})==79
    parts=[v['id'] for r in structures for v in r['required_parts']];assert len(parts)==len(set(parts))==625
    assert scope['representation_obligations_floor']==1875 and scope['verified_representation_obligations']==0 and scope['unresolved_instantiated_denominator']
    for r in structures:
        assert r['required_representations']==['image','schematic','model'] and r['coverage_status']=='required_not_verified'
        assert r['image_bindings']==r['schematic_bindings']==r['model_bindings']==[] and not r['clinical_approval'] and not r['fine_anatomical_approval']
    for r in p['questions']:assert r['required_visuals'] and r['source_case_supplies_actual_question_scenario'] is False
    assert all(r.get('parts')==[] and 'images' not in r and 'landmark' not in r for r in report['proposed_walkthrough_steps'])
    amendments={8:'For the declared sphere, volume is proportional to diameter cubed: 6.0 × 2^(1/3) = 7.5595 mm, recorded here as 7.6 mm. That 26 percent diameter increase can be difficult to distinguish from measurement variation in a small nodule; detectability depends on the method and comparable source images. Validated volumetry can improve reproducibility but also requires consistent technique and software. Actual volume doubling time needs two measured volumes and their elapsed interval. Growth rates overlap between benign and malignant nodules; slow growth or apparent stability alone does not exclude malignancy. This calculation neither proves tumour growth in the reference case nor determines histology.',
      12:'This is a teaching sequence for the stated incidental-nodule task. First establish whether the chosen guideline applies. Then assess the complete benign imaging pattern; verified fat, characteristic calcium or typical perifissural morphology can support a benign imaging interpretation without supplying histological confirmation. Distinguish solid from subsolid, use the appropriate measurement convention, and combine those observations with clinical risk, the actual single/multiple context, prior images and patient preferences. Risk informs real decisions throughout; this ordered exercise is not a universal algorithm or a substitute for the relevant guideline branch.'}
    amended=copy.deepcopy(proposed)
    for index,new in amendments.items():amended[index]['explain']=new
    changes=[]
    for i,(a,b) in enumerate(zip(proposed,amended)):
        if a!=b:
            assert set(k for k in a if a[k]!=b[k])=={'explain'}
            changes.append(dict(index=i,question_number=i+1,field='explain',before=a['explain'],after=b['explain'],answer_unchanged=a['answer']==b['answer']))
    assert [q['answer'] for q in proposed]==[q['answer'] for q in amended]
    grades={label:[dict(index=i,score=score_quiz([q],[str(q['answer'])])['score']) for i,q in enumerate(quiz)] for label,quiz in [('original',original['quiz']),('owner_proposed',proposed),('independent_amended',amended)]}
    assert all(r['score']==1 for rows in grades.values() for r in rows)
    protocols=copy.deepcopy(report['proposed_protocol']);before=protocols[0]
    protocols[0]='Use the complete acquired thorax with contiguous thin reconstructed sections at most 1.5 mm, typically 1 mm, and explicit coverage/quality limitations. Record nominal reconstructed section thickness separately from reconstruction centre spacing and pixel spacing. Record acquisition collimation only when independently documented; do not infer it from DICOM SliceThickness.'
    summaries=['Optional12month high-risk small-solid branch retained.','Solitary qualifying part-solid initial3–6month branch corrected.','Negative PET does not establish benignity.','Typical full perifissural pattern supports benign imaging interpretation.','Verified intranodular fat/calcium with suitable ROI and kernel.','Young immunocompromised febrile patient excluded from Fleischner.','Growing solid component warrants individualized further assessment.','Same greatest-dimension plane/orthogonalmean/rounding gives5mm.','Sphere answer7.6 retained; explain-only precision amendment required.','Qualifying pureGGN total5year surveillance retained.','Low small-solid risk/optional assessment without guarantee.','Comparable prior images and consistent volumetry software.','Teaching-order answer retained; explain-only conditionality amendment required.']
    result=dict(schema_version=1,source_commit='aafe94142f517e1b7714f518c69f24b4171306fc',owner_proposal_sha256=hashlib.sha256((OWNER/'complete-clinical-question-proposal.json').read_bytes()).hexdigest(),owner_original_quiz_sha256=digest(original['quiz']),owner_proposed_quiz_sha256=digest(proposed),independent_amended_quiz_sha256=digest(amended),all_original13questions_exact_base_and_current_node_match=True,original_questions=original['quiz'],owner_proposed_questions=proposed,independent_amended_questions=amended,question_findings=[dict(question_number=i+1,finding=t) for i,t in enumerate(summaries)],bounded_explain_only_amendments=changes,protocol_amendment=dict(index=0,before=before,after=protocols[0]),reference_grader_results=grades,answer_or_rubric_changes=False,source_case_supplies_question_patient_or_prior_PET_history=False,scope=dict(groups=79,parts_floor=625,representation_obligations_floor=1875,verified_obligations=0,actual_instantiated_denominator_unresolved=True),owner_frozen_clinical_proposal_status='NO_GO_pending_two_explanation_and_one_protocol_amendments',amended_proposal_status='GO_for_bounded_correction_and_expert_review_only',clinical_approval=False,fine_anatomical_approval=False,structure_coverage_granted=False,runtime_modified=False,
      primary_evidence=[dict(url='https://pubs.rsna.org/doi/full/10.1148/radiol.2017161659',sections=['General Recommendations','Nodule Growth Rate','Risk Estimation and Risk Models','Additional Considerations:Perifissural nodules'],supports='26percent/100–400day population statement is supported, not the subject of a factual-error finding. Individual decisions need morphology/risk/context; no source histology is supplied.'),dict(url='https://www.brit-thoracic.org.uk/document-library/guidelines/pulmonary-nodules/bts-guidelines-for-the-investigation-and-management-of-pulmonary-nodules/',PDF_pages_1based=[24,26,59],journal_pages=['ii18','ii20','ii53'],supports='Measurement uncertainty depends on study/method; no growth-rate or stability threshold definitely excludes malignancy.'),dict(url='https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.34.12.html',section='TableC.34.12-1 tags0018,0050 and0018,0088',supports='Nominal reconstructed slice thickness and centre spacing are distinct; neither alone proves acquisition collimation.'),dict(url='https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/Lung-RADS',supports='Separate screening pathway; do not blend Lung-RADS and Fleischner thresholds.')],
      advisory=['Q4 explanation should describe the hypothetical stated four-year comparison, not suggest that genuine longitudinal source images are supplied by this candidate.','The reporting findings are selected examples, not a complete executable decision table: all actual single/multiple solid/subsolid branches still require the named guideline and clinical context.','The79groups are a conditional floor. Generic requirements need explicit actual case/structure/timepoint instantiation and thoracic expert review before claiming every reported structure is represented.'])
    (REVIEW/'clinical-amendment-proposal.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(dict(original13questions=True,grader_cases=sum(len(v) for v in grades.values()),all_reference_scores_1=True,explain_only_indices=list(amendments),protocol_indices=[0],groups=79,parts=625,unverified_obligations=1875,runtime_modified=False),indent=2))
if __name__=='__main__':main()
