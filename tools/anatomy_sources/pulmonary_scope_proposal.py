"""Full conditional pulmonary-nodule scope and bounded question corrections.

This creates reviewable proposals only; it does not grant visual coverage or
change current curriculum/reporting registries.
"""
from pathlib import Path
import copy
import hashlib
import json
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from primer.quiz import score_quiz
REVIEW=ROOT/'docs/pulmonary-nodule-source-review-20261011'


def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def copy_spacing(s):return re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',s)
FLEISCHNER={'title':'MacMahon et al. Fleischner Society incidental pulmonary nodule guidance,2017 (corrected version)','url':'https://doi.org/10.1148/radiol.2017161659'}
MEASUREMENT={'title':'Bankier et al. Recommendations for Measuring Pulmonary Nodules at CT,2017','url':'https://doi.org/10.1148/radiol.2017162894'}
BTS={'title':'Callister et al. BTS pulmonary-nodule guidance,2015 with published correction','url':'https://doi.org/10.1136/thoraxjnl-2015-207168'}
SCREENING={'title':'ACR Lung-RADS v2022 current screening reference','url':'https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/Reporting-and-Data-Systems/Lung-RADS'}


def revised_questions(original):
    q=copy.deepcopy(original)
    q[1]['prompt']='An immunocompetent60-year-old without known primary cancer has an incidental solitary part-solid nodule,14mm overall with a4mm solid component. There are no symptoms of infection and no prior imaging. Applying Fleischner2017, what is the next step?'
    q[1]['explain']='For this qualifying solitary part-solid nodule of at least6mm overall, repeat thin-section CT at3–6months to assess persistence. If it persists without growth and the solid component remains below6mm, annual CT through5years is recommended. This is not the initial schedule for every subsolid nodule: a qualifying solitary pure ground-glass nodule at least6mm uses6–12months initially. Transient inflammatory opacities remain a differential, and persistence does not itself establish a cancer diagnosis.'
    old=q[2]['answer'];new='It does not establish benignity or justify ending CT surveillance';q[2]['answer']=new;q[2]['choices']=[new if v==old else v for v in q[2]['choices']]
    q[2]['explain']='A negative FDG PET result does not reliably exclude malignancy in a persistent pure ground-glass nodule. Low uptake and limited spatial resolution reduce PET sensitivity for this morphology. CT morphology, risk, eligibility and interval change determine further assessment; PET negativity alone should not end indicated CT surveillance. Ground-glass attenuation is not a histological diagnosis, and infection or other benign processes can share the appearance. PET may help selected larger solid nodules, while inflammatory disease can also produce positive uptake.'
    old=q[3]['answer'];new='No nodule follow-up for this typical benign perifissural morphology';q[3]['answer']=new;q[3]['choices']=[new if v==old else v for v in q[3]['choices']]
    q[3]['explain']='The complete homogeneous, smooth, lentiform or triangular perifissural pattern is characteristic of an intrapulmonary lymph node and ordinarily requires no nodule follow-up in the qualifying incidental context. Fissural proximity alone is insufficient, and a suspicious or atypical lesion must not be dismissed on location alone. The report should describe the observed pattern rather than assert histology from CT. This case also supplies genuine four-year comparison imaging; the LIDC source case does not.'
    q[4]['prompt']='An incidental9mm solid nodule in an immunocompetent adult without known primary cancer contains macroscopic fat confirmed with a small intranodular ROI on thin, nonsharpened CT sections, with coarse popcorn-like calcification. The fat ROI excludes adjacent air and edge pixels. What follows?'
    old=q[4]['answer'];new='The imaging pattern strongly supports a benign hamartoma';q[4]['answer']=new;q[4]['choices']=[new if v==old else v for v in q[4]['choices']]
    q[4]['explain']='Verified intranodular macroscopic fat and a characteristic benign calcification pattern strongly support a benign hamartoma pattern, usually removing the need for nodule surveillance in this clinical context. A single negative point value near adjacent air is insufficient because partial volume can simulate fat. Use thin nonsharpened sections and a small ROI; record technique and uncertainty. Diffuse, central, laminated and popcorn patterns are considered benign, whereas eccentric or stippled calcium alone does not exclude malignancy. The imaging diagnosis is not new histological confirmation.'
    q[5]['explain']='Fleischner2017 does not apply to patients under35, immunocompromised patients, patients with known primary cancer, or screening examinations. This patient is both young and immunocompromised. New nodules with fever warrant prompt assessment in the actual clinical context, including infectious and other causes; the incidental small-nodule follow-up table supplies neither a treatment plan nor a safe delay. Investigation and treatment depend on clinical findings, severity, immune status and relevant specialist assessment.'
    q[6]['prompt']='An incidental part-solid nodule in an immunocompetent adult without known primary cancer is assessed on comparable thin-section CT examinations12months apart. It remains15mm overall, but remeasurement confirms the solid component has grown from4mm to9mm. What should happen?'
    q[6]['explain']='Confirmed enlargement of the solid component is suspicious despite unchanged total diameter and warrants further clinical evaluation, with PET-CT, sampling or resection considered according to the individual case. A CT dense component correlates with invasive burden in relevant adenocarcinomas but does not prove histological invasion. Record both total size and the solid component on comparable thin-section images. A persistent solid component of at least6mm is already highly suspicious; the management discussion becomes more concerning with growth or a component exceeding8mm. Negative PET would not reliably exclude a low-uptake malignancy.'
    q[7]['prompt']='On a1mm CT image in the plane showing the nodule’s largest dimensions, an incidental solid nodule measures7.0mm along its long axis and3.8mm along the perpendicular short axis on that same image. Applying the Fleischner measurement convention, what size in millimetres is recorded? Answer with the number alone.'
    q[9]['explain']='For a qualifying solitary pure ground-glass nodule at least6mm, the initial6–12month CT evaluates persistence, followed by CT every2years until5years from the initial examination. The answer is5years in total. Persistence is not proof of a neoplasm or proof that all infectious causes have been excluded. New or increasing solidity, growth, suspicious morphology and the clinical context can change the plan; the surveillance interval is not a guarantee of benignity.'
    q[10]['answer']='The threshold reflects the usually low malignancy risk of solid nodules under6mm and the balance between surveillance benefit and radiation, anxiety, financial cost and downstream procedures. The risk is often below1percent even in high-risk screening cohorts, but suspicious morphology or upper-lobe location can increase it. For a5mm incidental solid nodule in a qualifying heavy smoker, Fleischner2017 permits an optional CT at12months, with patient risk, morphology, comorbidity and preferences guiding the decision. The threshold does not prove the nodule benign or guarantee later curability.'
    q[10]['explain']='No routine follow-up and optional follow-up are recommendations for defined clinical categories, not biological guarantees. Preserve the low-risk/high-risk distinction, the solid/subsolid distinction and single/multiple context. Suspicious morphology can justify a different individualized choice even for a small lesion.'
    q[11]['prompt']='A nodule reported as7mm last year is reported as9mm today. Before accepting growth, describe the measurements and technical factors that should be compared. Name a technique that can improve reproducibility, and state what must remain consistent for that technique.'
    q[11]['answer']='Reopen and remeasure the prior images rather than compare report numbers alone. Compare thin sections, the same mean-diameter convention and plane of greatest dimension, comparable lung window settings, reconstruction thickness and kernel, respiratory state and relevant contrast or surrounding-lung differences. Record any limitation instead of assuming the scans are interchangeable. Semi-automated volumetry can improve reproducibility, but comparisons require the same validated method and consistent software version and segmentation performance. A volume doubling time requires actual measurements and an elapsed time; neither diameter growth nor a growth rate alone establishes histology.'
    q[11]['keywords']=['thin','lung window','volumetry','same','prior','software']
    q[11]['explain']='Diameter and volume measurements both contain uncertainty. The current case supplies no evidence that most reported growth is artefactual. A change around2mm should be interpreted with acquisition quality, measurement reproducibility and the actual prior examination. Volumetry does not remove all disagreement, and a volume doubling time is not a stand-alone benign-versus-malignant test.'
    for item in q:
        for field in ('prompt','answer','explain'):
            item[field]=copy_spacing(item[field])
        if 'choices' in item:item['choices']=[copy_spacing(s) for s in item['choices']]
    return q


def main():
    snapshot=json.loads((REVIEW/'current-scope-snapshot.json').read_text());ref=snapshot['effective_reference'];node=snapshot['node']
    proposed=revised_questions(node['quiz']);review=[]
    descriptions=[
      'Small qualifying incidental solitary solid nodule and optional high-risk follow-up; existing answer retained.',
      'Specify eligibility and solitary part-solid context; correct explanation that generalized the initial interval to all subsolid nodules.',
      'Remove absolute risk-neutral and histological claims; PET negativity does not justify ending indicated CT surveillance.',
      'Describe complete typical perifissural imaging morphology, not histological certainty or proximity alone.',
      'Confirm true intranodular fat on a small ROI with appropriate nonsharpened reconstruction and benign calcium pattern; remove a point-value and certainty shortcut.',
      'Preserve guideline exclusions; remove an invented fixed investigation/treatment timeline.',
      'Confirm comparable-source growth, distinguish CT solidity from histological invasion, and individualize escalation.',
      'Specify the supplied same-plane measurements show largest dimensions; preserve numeric answer5.',
      'Retain the explicit sphere assumption and numeric answer7.6; not a real nodule-shape model.',
      'Preserve total5year answer while removing persistence-excludes-infection inference.',
      'Keep small-solid risk and optional surveillance; remove unsupported near-zero-yield/guaranteed-curability reasoning.',
      'Remove unsupported prevalence claim about growth artefact and require consistent volumetry software.',
      'Retain this conditional teaching order; not an executable universal patient-management rule.'
    ]
    visual_requirements=[
      ['right lower lobe localization','complete smooth noncalcified solid nodule boundary','same-plane caliper convention and true maximum plane','eligibility/risk pathway stated separately from anatomy'],
      ['left upper lobe localization','whole part-solid nodule extent','separate actual dense-component extent','true total/dense-component measurements and conditional follow-up'],
      ['whole pure ground-glass opacity with preserved underlying structures','genuine co-localized FDG PET when supplied and its resolution/background','CT growth/solid-component surveillance context'],
      ['complete lentiform/triangular smooth homogeneous nodule','actual oblique-fissure plane and attachment','actual pleural tail and relevant interface','genuine matched four-year prior CT'],
      ['verified intranodular fat ROI excluding air/edges','actual benign popcorn-like calcific distribution','complete nodule boundary on appropriate nonsharpened native CT'],
      ['every actual small nodule and relevant infectious/other background pattern','immune/age/fever context is clinical data, not invented geometry'],
      ['whole part-solid nodule at both genuine examinations','separate dense-component boundaries at both dates','same-source measurement comparability','no CT opacity promoted to histological invasion'],
      ['same-plane orthogonal long/short axes in the plane of largest dimensions','a calibrated schematic of mean diameter and rounding, labelled conceptual if no matching real source'],
      ['an explicitly declared sphere diagram/model showing r³ volume scaling','real nodules must retain genuine morphology and must not be silently replaced by that sphere'],
      ['whole pure-ground-glass nodule on real baseline and persistence CT','actual ground-glass/dense-component evolution when available','five-year follow-up timeline labelled guidance, not measured source-case history'],
      ['true small solid nodule margin/location','actual emphysema or fibrosis where taught','evidence/risk/harm pathway separated from anatomical models'],
      ['complete actual source nodule and matching prior','both reconstruction kernels/thicknesses and native measurement planes','validated volume segmentation at both timepoints with consistent software','uncertainty and actual elapsed interval'],
      ['eligibility and guideline context','complete benign morphology including true fat/calcium where relevant','solid/subsolid classification and same-plane diameter','clinical risk; a teaching sequence cannot manufacture those observations']
    ]
    for i,(old,new) in enumerate(zip(node['quiz'],proposed)):
        review.append(dict(index=i,question_number=i+1,original=old,proposed=new,
            source_review=descriptions[i],sources=[FLEISCHNER,MEASUREMENT] if i in (7,8,11) else [BTS,FLEISCHNER] if i in (2,3,4) else [FLEISCHNER],
            changed=old!=new,source_case_supplies_actual_question_scenario=False,
            required_visuals=visual_requirements[i],
            unresolved='LIDC0525 is one source examination and is not the actual described hypothetical patient, comparison study or PET case.'))
    grade=[dict(index=i,score=score_quiz([q],[str(q['answer'])])['score']) for i,q in enumerate(proposed)]
    assert all(x['score']==1 for x in grade)
    clinical=dict(schema_version=1,base_commit=snapshot['base_commit'],module_id=node['id'],investigation_id='ra.ct-pulmonary-nodules',
      original_question_count=len(node['quiz']),original_quiz_sha256=digest(node['quiz']),proposed_quiz_sha256=digest(proposed),
      original_questions_preserved=True,questions=review,reference_grader_results=grade,
      original_goal=node['goal'],proposed_goal=node['goal'],clinical_approval=False,fine_anatomical_approval=False,
      runtime_curriculum_changed=False,sources=[FLEISCHNER,MEASUREMENT,BTS,SCREENING])
    (REVIEW/'complete-clinical-question-proposal.json').write_text(json.dumps(clinical,indent=2,ensure_ascii=False)+'\n')
    common=['complete actual source extent and unassessed limits','all resolved external boundaries and interfaces','true source coordinates and component topology','all actual site/laterality/timepoint instances','acquisition and reconstruction resolution limitations']
    structures=[]
    def add(key,name,kind,parts,condition):
        structures.append(dict(id='pulmonary.'+key,name=name,tissue_class=kind,laterality=('left' if key.startswith('left') else 'right' if key.startswith('right') else 'variable'),
           conditional_scope=condition,required_parts=[dict(id='pulmonary.'+key+'.part-'+str(i+1),name=s) for i,s in enumerate(common+parts)],
           required_representations=['image','schematic','model'],coverage_status='required_not_verified',image_bindings=[],schematic_bindings=[],model_bindings=[],clinical_approval=False,fine_anatomical_approval=False))
    for side in ('right','left'):
        add(side+'.lung',side+' lung parenchyma','lung',['apex-to-base actually acquired extent','pleural and hilar interfaces','dependent aeration and background emphysema/fibrosis'], 'Required for nodule localization and background-risk assessment; not automatically labelled by nodule masks.')
        add(side+'.pleura',side+' visceral pleural interface','pleura',['costal mediastinal and diaphragmatic surfaces where visible','subpleural nodule contact and attachment versus mere proximity','pleural indentation or retraction if actually present'],'Every actual interface relevant to a reported juxtapleural nodule.')
    for key,name in [('right.upper','right upper lobe'),('right.middle','right middle lobe'),('right.lower','right lower lobe'),('left.upper','left upper lobe including lingula'),('left.lower','left lower lobe')]:
        add(key,name,'lung',['complete true lobe extent','true lobar fissural boundaries and incomplete-fissure limits','hilar/lobar bronchovascular continuity'],'Required wherever lobe is reported; separate complete source geometry/labels are still missing.')
    for key,name in [('right.oblique_fissure','right oblique fissure'),('right.horizontal_fissure','right horizontal fissure'),('left.oblique_fissure','left oblique fissure'),('accessory_fissure','every actual accessory fissure or variant')]:
        add(key,name,'pleura',['complete visible fissural plane and unresolved parts','true junction with adjacent lobes','actual nodule attachment morphology'],'Primary fissures required for localization; accessory variant only where actually present.')
    segment_names={'right':[(1,'apical upper'),(2,'posterior upper'),(3,'anterior upper'),(4,'lateral middle'),(5,'medial middle'),(6,'superior lower'),(7,'medial basal'),(8,'anterior basal'),(9,'lateral basal'),(10,'posterior basal')],
                   'left':[(1,'apical upper variant'),(2,'posterior upper variant'),(3,'anterior upper'),(4,'superior lingular'),(5,'inferior lingular'),(6,'superior lower'),(7,'medial basal variant'),(8,'anterior basal variant'),(9,'lateral basal'),(10,'posterior basal')]}
    for side,rows in segment_names.items():
        for number,label in rows:
            add(side+'.S'+str(number),side+' S'+str(number)+' '+label+' segment','lung',['actual segmental extent inferred only from supported bronchovascular anatomy','segmental bronchus and vascular continuity','interface and uncertainty against neighbouring segments'],'Instantiate only for actual supplied anatomy and reported segment; left apicoposterior/anteromedial combined variants must not be forced into distinct pseudo-boundaries.')
            add(side+'.B'+str(number),side+' B'+str(number)+' supplying bronchial branch','airway',['patent lumen versus partial-volume/nonvisualized portion','true branching origin and continuity','nodule-adjacent airway relationship if present'],'Needed where reported segment or airway relationship depends on this resolved branch; no invented universal bronchial tree.')
    for key,name in [('left.S1+2','left combined apicoposterior segment'),('left.S7+8','left combined anteromedial basal segment')]:
        add(key,name,'lung',['actual combined bronchovascular anatomy','resolved segmental extent and shared boundaries'],'Conditional actual combined anatomical variant; not additive anatomy forced on every case.')
    features={
      'nodule.entire':'every actual whole nodule',
      'nodule.solid':'solid nodule and its external boundary',
      'nodule.ground_glass':'pure ground-glass opacity extent and preserved underlying structures',
      'nodule.part_solid':'part-solid opacity and separate dense and ground-glass extents',
      'nodule.solid_component':'each actual dense component in a part-solid nodule',
      'nodule.margin':'smooth lobulated or spiculated external nodule margin',
      'nodule.fat':'every verified intranodular macroscopic-fat focus',
      'nodule.calcification':'every actual calcific focus and its distribution',
      'nodule.perifissural':'typical perifissural or juxtapleural whole morphology',
      'nodule.cystic':'actual cyst wall cavity/bubble-like lucencies and adjacent nodularity',
      'nodule.airway_contact':'actual nodule-airway interface and internal air bronchogram',
      'nodule.vascular_contact':'actual nodule-vessel interface and traversing vessels',
      'nodule.pleural_contact':'actual nodule-pleural/fissural interface and retraction',
      'nodule.prior_extent':'every genuine matched prior nodule and morphology',
      'nodule.PET_extent':'actual correlated PET nodule uptake distribution when acquired',
      'background.emphysema':'actual background emphysema relevant to risk and measurement',
      'background.fibrosis':'actual background fibrosis/scar relevant to risk and measurement',
      'background.atelectasis':'actual adjacent atelectasis or dependent change affecting measurement',
      'background.infection':'actual infectious or inflammatory pattern relevant to the excluded pathway',
    }
    for key,name in features.items():
        add(key,name,'nodule_or_conditional_background',['every actual component and native boundary','precise diagnostic morphology at true source resolution','no source-defined cell surface interpreted as histology'],'Conditional per actual nodule/feature/modality/timepoint. Separate reader marks remain separate; no pooled inferred consensus.')
    for pattern in ('diffuse','central','laminated','popcorn','eccentric_or_stippled'):
        add('calcification.'+pattern,'actual '+pattern.replace('_',' ')+' calcification pattern','calcification',['all genuine calcific components and native distribution','relationship to nodule boundary and noncalcified component'],'Required where this pattern is taught or reported; a source ordinal calcification score alone does not supply expert-verified morphology.')
    inventory=dict(schema_version=1,investigation_id='ra.ct-pulmonary-nodules',module_id=node['id'],title='Pulmonary nodules: whole reporting and13-question conditional structure draft',
       source_contract_definition='Exact current effective reporting/report_templates/walkthrough/reading snapshot at base main; proposals are separate and do not overwrite historical contract.',
       source_contract_sha256=snapshot['effective_contract_sha256'],shared_curriculum_quiz_sha256=digest(node['quiz']),
       scope_status='conditional_whole_module_draft_requires_thoracic_radiologist_review_and_actual_site_instantiation',
       required_representations=['image','schematic','model'],modality_scope=['complete_native_thin_section_CT','all_actual_reconstruction_kernels','genuine_prior_CT_when_supplied','PET_CT_if_actually_acquired'],
       reporting_checklist=ref['reporting']['checklist'],reporting_template_sections=ref['reporting']['template_sections'],structures=structures,
       non_anatomical_report_dependencies=['age and eligibility/exclusions','actual cancer/immune/screening context','individual risk/preferences/comorbidity','quality and reconstruction comparability','actual dates and elapsed interval','calibrated HU, linear/volume convention and software version','complete correct single/multiple solid/subsolid guideline branch and rationale'],
       scope_review_flags=['Every actual nodule/neighbor/variant/timepoint requires explicit instantiation; this is a known minimum, not a fixed complete denominator.','Full native CT source is present but unlabelled anatomy is not approved representation coverage.','All source binary nodule masks represent released annotations, not clinician-approved true tissue boundaries.','No real follow-up, PET, histology or complete example-bank diagnostic-morphology coverage exists for this source case.'],
       runtime_integrated=False,clinical_approval=False,fine_anatomical_approval=False,structure_coverage_granted=False,
       named_requirement_groups=len(structures),named_required_parts_floor=sum(len(x['required_parts']) for x in structures),
       representation_obligations_floor=3*sum(len(x['required_parts']) for x in structures),verified_representation_obligations=0,
       unresolved_instantiated_denominator=True)
    (REVIEW/'structure-requirements-proposal.json').write_text(json.dumps(inventory,indent=2,ensure_ascii=False)+'\n')
    steps=copy.deepcopy(ref['walkthrough']['steps'])
    for step in steps:
        step.pop('images',None);step.pop('landmark',None);step['parts']=[]
        step['anatomy_note']='Actual named structure fidelity remains unverified; these fields are assessment prompts and do not bind generic lobe geometry.'
    steps[-1]['findings']=[copy_spacing(s) for s in [
       'For an eligible incidental solitary solid nodule under6mm: no routine follow-up at low risk; optional12month CT at high risk, adjusted for morphology/context.',
       'For an eligible incidental solitary solid6–8mm nodule: initial CT6–12months; later18–24month assessment depends on risk and stability.',
       'For qualifying multiple solid nodules with at least one6mm nodule: initial CT3–6months; assess the most suspicious nodule and the applicable later follow-up branch.',
       'For qualifying solitary pure ground-glass nodules at least6mm: initial CT6–12months, then every2years until5years if persistent and appropriate.',
       'For qualifying solitary part-solid nodules at least6mm overall: initial CT3–6months; persistent dense-component size, growth and morphology can warrant further evaluation.',
       'Screening, known malignancy, immunocompromise, young adults and alternative causes require their actual pathway; do not combine Fleischner/BTS/Lung-RADS thresholds.'
    ]]
    protocol=[copy_spacing(s) for s in [
      'Use the complete acquired thorax with contiguous thin sections at most1.5mm, typically1mm, and explicit coverage/quality limitations. Record acquired thickness separately from reconstruction interval and pixel spacing.',
      'Use suitable lung windows and actual multiplanar reconstructions to distinguish nodule/linear scar and solid/subsolid components; retain the actual source reconstructions and kernel.',
      'Measure verified fat or calcium on the thinnest available nonsharpened series with a small ROI, excluding air/edge partial-volume contamination. A single point value is insufficient.',
      'Compare all available original prior studies, including early baseline; document dates, reconstruction/software compatibility and uncertainty. A current source example is not an invented prior examination.',
      'Declare incidental/screening/oncology/infectious context, eligibility and exclusions before applying a named current guideline. Distinguish single/multiple and solid/pure-ground-glass/part-solid pathways.',
      'Document each nodule ID/site/series/image, total/solid-component measurement, margins, verified fat/calcification, relevant pleural/airway/vascular relationships and actual interval change. Reader scores are not histological diagnoses.'
    ]]
    report=dict(schema_version=1,investigation_id='ra.ct-pulmonary-nodules',current_effective_contract_sha256=snapshot['effective_contract_sha256'],
                proposed_protocol=protocol,proposed_walkthrough_steps=steps,proposed_additional_primary_sources=[FLEISCHNER,MEASUREMENT,BTS,SCREENING],
                reporting_fields_are_unfilled_prompts=True,original_reference_preserved_in_snapshot=True,
                clinical_approval=False,structure_coverage_granted=False,runtime_integrated=False)
    (REVIEW/'reporting-proposal.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(dict(question_count=13,changed_question_indices=[r['index'] for r in review if r['changed']],reference_grader_all_1=True,
                         groups=inventory['named_requirement_groups'],required_parts_floor=inventory['named_required_parts_floor'],representation_floor=inventory['representation_obligations_floor'],verified_obligations=0),indent=2))


if __name__=='__main__':main()
