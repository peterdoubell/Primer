#!/usr/bin/env python3
"""Reconcile endometrial MRI reporting scope with acquired anatomy and FIGO 2023.

This authors assessment prompts; it does not assign a patient's stage or approve
published figures, atlas tissues, microscopic disease or treatment eligibility.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INV = 'ra.mri-endometrial-cancer'
DATA = ROOT / 'data/radiology'
SOURCES = [
    {'title': 'FIGO staging of endometrial cancer: 2023 (primary committee publication)',
     'url': 'https://doi.org/10.1002/ijgo.14923'},
    {'title': 'Correction to FIGO staging of endometrial cancer: 2023',
     'url': 'https://doi.org/10.1002/ijgo.15193'},
    {'title': 'Updated ESUR Guidelines for Endometrial Cancer (2025 online; 2026 volume)',
     'url': 'https://doi.org/10.1007/s00330-025-11700-3'},
    {'title': 'ESR Essentials: uterine cancers (2026; staging discrepancy recorded in review)',
     'url': 'https://doi.org/10.1007/s00330-026-12705-2'},
    {'title': 'Radiology Assistant — Endometrial Cancer - MR staging (assigned reading scope)',
     'url': 'https://radiologyassistant.nl/abdomen/unsorted/mr-in-endometrial-cancer'},
]

AREAS = [
    ('Source adequacy, uterus and tumour', 'UTERUS AND TUMOUR', 'endometrium',
     'Record supplied histology and biopsy/treatment dates, menopausal/cycle context, actual acquisition quality and coverage. Describe uterine orientation, cavity, tumour epicentre and growth pattern; correlate T2, high-b-value DWI/ADC and acquired enhancement. Record each tumour dimension and whole uterine size with real planes and scale.',
     'Sequences/coverage and missing clinical inputs: [__]. Uterine orientation and dimensions: [__]. Tumour site, morphology, signal and dimensions in stated planes: [__]. Uncertain or unassessed extent: [__].'),
    ('Myometrial invasion', 'MYOMETRIAL INVASION', 'uterus',
     'Evaluate the endometrium–junctional-zone interface and deepest source-supported tumour penetration. Measure depth and full myometrial thickness at the same site in aligned planes. Distinguish absent, superficial (<50%), deep (≥50%) and indeterminate invasion; document cavity expansion, thin cornual wall, adenomyosis or leiomyoma distortion.',
     'Evaluable tumour–myometrial interface/site: [__]. Invasion depth and local full wall thickness: [__]/[__] mm, method/plane [__]. Imaging category [absent / <50% / ≥50% / indeterminate], supporting sequences and uncertainty [__].'),
    ('Cervical canal and stroma', 'CERVIX', 'cervix',
     'Assess internal os, endocervical canal and source-resolved cervical stromal boundaries. Separate canal protrusion or glandular extension and mass-effect thinning from tumour signal extending into cervical stroma. Record the actual involved region, extent and equivocal interface.',
     'Internal-os/canal relationship: [__]. Stromal interface and source-supported extent: [__]. Protrusion, invasion concern or indeterminate boundary and supporting sequences: [__].'),
    ('Uterine outer wall and adnexa', 'SEROSA AND ADNEXA', 'ovaries',
     'Assess subserosa/serosal contour and each covered ovary and tube, including actual tumour interfaces and discontinuous lesions. Describe adnexal morphology and laterality. Distinguish imaging findings from the pathological and clinical criteria for synchronous ovarian disease or FIGO IA3; a published image cannot supply those criteria.',
     'Outer uterine contour/subserosal or serosal concern: [__]. Right and left adnexal coverage, findings and interfaces: [__]. Separate lesion, uncertainty and required pathological correlation: [__].'),
    ('Vagina, parametria and adjacent organs', 'VAGINA AND ADJACENT ORGANS', 'cervix',
     'Map each actual vaginal, parametrial, sidewall and adjacent-organ interface. Separate contact, muscular-wall findings and mucosal/luminal concern in bladder and bowel; loss of fat plane or oedema alone does not prove mucosal invasion. Record covered ureteric relationships and obstruction when relevant, and the limits of wall-layer resolution.',
     'Vaginal/parametrial sites and extent: [__]. Bladder and each contacted bowel segment: contact, wall and mucosal/luminal evidence [__]. Sidewall/ureteric findings, uncertainty and unacquired extent: [__].'),
    ('Regional and distant nodes', 'LYMPH NODES', 'uterus',
     'Map each suspicious node by actual station, side, short-axis measurement and morphology. Record para-aortic extent relative to the acquired renal-vessel reference, inguinal or other distant stations and incomplete coverage. Node size or diffusion cannot establish microscopic metastatic burden or replace sentinel-node/pathological assessment.',
     'Acquired stations and renal-vessel reference/coverage: [__]. Each suspicious node: station/side, short axis, morphology and uncertainty [__]. Unassessed stations and pathological inputs: [__].'),
    ('Peritoneal and distant disease', 'PERITONEUM AND DISTANT SITES', 'uterus',
     'Separate pelvic peritoneal deposits from abdominal peritoneal disease beyond the pelvis. Map actual omental, mesenteric, organ-surface and other covered lesions, ascites and distant organ findings. State which abdominal/chest sites are acquired or assessed by another dated examination; a pelvic MRI cannot exclude unacquired distant disease.',
     'Pelvic peritoneal findings: [__]. Extrapelvic peritoneal/omental/mesenteric findings: [__]. Other covered distant lesions, modality/date and uncertainty: [__]. Unacquired sites: [__].'),
    ('Planning, variants and benign mimics', 'PLANNING AND MIMICS', 'uterus',
     'Record actual uterine size, position or developmental variants, source-visible zones and benign abnormalities that affect measurement or planning. Assess atypical enhancement and differential diagnosis without inferring histology from appearance. State imaging evidence relevant to an actual fertility-preservation request; eligibility requires multidisciplinary clinical/pathological assessment.',
     'Actual size/orientation/variant and leiomyoma, adenomyosis, endometriosis or other mimic: [__]. Effect on assessment/planning and unresolved interfaces: [__]. Supplied fertility question and evaluable imaging findings/limitations: [__].'),
    ('Supplied treatment or comparison examination', 'COMPARISON AND TREATMENT CONTEXT', 'cervix',
     'When an actual treatment or comparison study is supplied, record its date, therapy and surgery, source matching and altered anatomy. Assess each suspected residual/recurrent lesion and organ-wall change with acquired sequences; distinguish fibrosis/oedema and uncertainty. Do not infer complete microscopic response or serial behaviour from unrelated publication cases.',
     'Applicable comparison/treatment, dates and altered anatomy: [__ / not supplied]. Matched site/lesion and acquired signal/extent: [__]. Residual/recurrent concern, alternatives, uncertainty and unassessed interfaces: [__].'),
]


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    path = DATA / 'investigation-overrides-non-msk.json'
    overrides = json.loads(path.read_text())
    guide = overrides[INV]['reporting']
    guide.update(
        reviewed_at='2026-10-11',
        protocol=[
            'Use high-resolution sagittal and uterine-axis-aligned oblique T2 with matched DWI/ADC. Record actual quality, coverage and examination/treatment context.',
            'Current ESUR guidance recommends multiphase contrast-enhanced MRI for excluding any myometrial invasion. Assess early subendometrial enhancement, equilibrium myometrial depth and cervical stromal enhancement in their actual acquired phases; record missing phases or contraindications. Without gadolinium, use T2/DWI and state reduced confidence for excluding superficial invasion.',
            'Record covered nodal, peritoneal and distant regions and the renal-vessel reference; relate additional staging examinations by modality/date rather than asserting whole-body coverage from pelvic MRI.',
        ],
        checklist=[{'label': label, 'detail': detail} for label, _, _, detail, _ in AREAS],
        template_sections=[{'heading': heading, 'body': body} for _, heading, _, _, body in AREAS],
        measurements=[
            {'name': 'Myometrial invasion', 'method': 'Measure deepest invasion and total wall thickness at the same actual site, using the reconstructed inner myometrial boundary and aligned planes; record ratio only when both endpoints are evaluable.', 'pitfall': 'Do not substitute a different wall thickness, cavity expansion or an unresolved junctional-zone interface. Exactly 50% belongs to the ≥50% imaging category.'},
            {'name': 'Tumour and whole uterine dimensions', 'method': 'Record maximal and orthogonal tumour axes in millimetres and whole uterine axes, including cervical extent, in stated planes/units.', 'pitfall': 'Diffuse thickening and atypical signal can obscure true margins. A uterine size value alone does not dictate a universal surgical approach.'},
            {'name': 'Nodes and reported interfaces', 'method': 'Measure each actual suspicious node short axis and any clinically relevant source-resolved interface distance in stated planes, with side/station and uncertainty.', 'pitfall': 'Published pixels and independent atlas coordinates are not current-patient measurement scale; size cannot assign microscopic nodal burden.'},
        ],
        pitfalls=[
            'MRI-visible zones differ with age, cycle, distortion and treatment. Histological endometrium, junctional-zone signal and unresolved wall layers are not interchangeable.',
            'Adenomyosis, leiomyomas, cornual geometry, cavity expansion and thin myometrium can mimic or conceal invasion. Canal protrusion with preserved stromal interface is distinct from cervical stromal tumour.',
            'FIGO 2023 integrates histology/grade, LVSI, pathological nodes and molecular results unavailable from MRI alone. Retain the existing versioned staging reference; report acquired anatomical findings and missing inputs.',
            'In FIGO 2023, pelvic peritoneal disease, extrapelvic peritoneal disease and other distant metastases are distinct categories. The 2026 ESR nodal paragraph calls above-renal-vessel nodes IVB; primary FIGO identifies these as IVC. Do not propagate this secondary-source discrepancy.',
            'Absent enhancement, diffusion or a published normal example does not establish an unassessed interface or complete response in the current patient.',
        ],
        impression_prompts=[
            'Summarise actual tumour site/size, myometrial and cervical stromal assessment, outer-wall/adnexal and adjacent-organ findings with confidence and limits.',
            'Separate acquired nodal stations, pelvic versus extrapelvic peritoneal findings and other distant sites. State missing coverage and clinical/pathological/molecular inputs.',
            'Address the supplied planning or comparison question using actual source findings; do not automatically assign stage, response or treatment eligibility.',
        ],
        sources=SOURCES,
    )
    overrides[INV]['key_images'] = []
    save(path, overrides)
    path = DATA / 'reporting-steps/abdomen.json'
    walks = json.loads(path.read_text())
    previous = walks['investigations'][INV]
    old_images = {step['label']: step.get('images', []) for step in previous['steps']}
    steps = []
    for label, heading, landmark, detail, body in AREAS:
        steps.append({'label': label, 'detail': detail, 'sections': [heading], 'look': detail,
                      'normal': {heading: body}, 'findings': ['Source-supported finding at [site/side]: [__]; method, extent and uncertainty: [__].'],
                      'images': [], 'landmark': landmark, 'parts': [],
                      'measurements': ['Myometrial invasion'] if heading == 'MYOMETRIAL INVASION' else ['Tumour and whole uterine dimensions'] if heading in {'UTERUS AND TUMOUR', 'PLANNING AND MIMICS'} else ['Nodes and reported interfaces'] if heading in {'LYMPH NODES', 'VAGINA AND ADJACENT ORGANS'} else [],
                      'tip': 'Use actual acquired findings and state uncertain or unassessed boundaries. Independent published figures and source atlas geometry are references; they do not supply current-patient findings.'})
    walks['investigations'][INV] = {'steps': steps, 'start': {'images': [], 'module_illustrations': False},
        'preset_mode': 'assessment-prompts', 'walkthrough_reviewed_at': '2026-10-11',
        'model': {'family': 'female', 'reporting_aim': 'Conceptual pelvic orientation only. The independent original HRA atlas supplies gross source surfaces; it does not approve fine uterine/cervical/organ-wall layers, current-patient tumour, nodal extent, microscopic disease or registration.'}}
    save(path, walks)
    path = DATA / 'investigation-source-images.json'
    pool = json.loads(path.read_text())
    archive = ROOT / 'docs/endometrial-held-legacy-images.json'
    if not archive.exists():
        save(archive, {'investigation_id': INV, 'legacy_images': pool.get(INV, []), 'legacy_walkthrough_bindings': old_images,
                      'reason': 'No recorded commercial redistribution grant. The tumour-length example was assigned to invasion depth. Hold both source roles until licensed original coverage is independently reviewed.', 'clinical_approval': False})
    pool.pop(INV, None)
    save(path, pool)
    path = DATA / 'source-anatomy-references.json'
    mapping = json.loads(path.read_text())
    mapping[INV] = copy.deepcopy(mapping['ra.mri-cervical-cancer'])
    save(path, mapping)
    path = DATA / 'radiology-asset-evidence.json'
    evidence = json.loads(path.read_text())
    for asset in evidence['assets']:
        if 'hra-female-pelvis' in asset['id'] and 'ra.mri-cervical-cancer' in asset.get('investigation_ids', []):
            if INV not in asset['investigation_ids']:
                asset['investigation_ids'].append(INV)
    save(path, evidence)
    print('Nine endometrial MRI assessment areas authored; two mismatched/unlicensed remote roles held; original HRA source association added without fine-layer approval.')


if __name__ == '__main__':
    main()
