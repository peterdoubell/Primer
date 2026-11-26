"""Typed requirements for one actual descriptor-only examination, not clinical approval."""
from copy import deepcopy
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASE = 'us.soft-tissue-neck'
AUTHOR = 'data/radiology/anatomic-additions-20261119.json'
COMPILED = 'data/radiology/descriptor-reporting.json'
FAST = 'data/radiology/report-templates/additions-20261119.json'
OUTPUT = 'data/radiology/descriptor-requirements/soft-tissue-neck.json'
KINDS = ['clinical_image', 'schematic', 'model']
GUIDANCE = 'aium-head-neck-2023'
EXPECTED_SECTIONS = ['technique', 'area-of-concern', 'parotid-glands', 'submandibular-glands',
                     'thyroid-gland', 'right-neck-nodes', 'left-neck-nodes', 'vessels', 'muscles-and-soft-tissues']
# Explicit author-field dispositions; no anatomy or evidence type is inferred from its name.
TYPES = {
    'technique': {'assessment': 'examination_scope'},
    'area-of-concern': {'lesion': 'current_finding', 'size': 'measurement', 'vascularity': 'flow_assessment', 'nature': 'interpretation'},
    'parotid-glands': {'lesion': 'current_finding', 'size': 'measurement', 'diffuse': 'current_finding', 'calculus': 'current_finding'},
    'submandibular-glands': {'lesion': 'current_finding', 'size': 'measurement', 'diffuse': 'current_finding', 'calculus': 'current_finding'},
    'thyroid-gland': {'nodule': 'current_finding', 'size': 'measurement', 'tirads': 'classification', 'diffuse': 'current_finding'},
    'right-neck-nodes': {'node': 'current_finding', 'size': 'measurement', 'features': 'current_finding'},
    'left-neck-nodes': {'node': 'current_finding', 'size': 'measurement', 'features': 'current_finding'},
    'vessels': {'thrombus': 'current_finding', 'carotid': 'current_finding'},
    'muscles-and-soft-tissues': {'abnormal': 'current_finding'},
}
GUIDANCE_SECTIONS = {
    'technique': ['Specification of the Examination', 'Documentation', 'Equipment Specification'],
    'area-of-concern': ['Indications', 'Specification of the Examination'],
    'parotid-glands': ['Parotid and Submandibular Evaluation'],
    'submandibular-glands': ['Parotid and Submandibular Evaluation'],
    'thyroid-gland': ['Thyroid Evaluation'],
    'right-neck-nodes': ['Cervical Lymph Node Evaluation'],
    'left-neck-nodes': ['Cervical Lymph Node Evaluation'],
    'vessels': ['Specification of the Examination', 'Equipment Specification'],
    'muscles-and-soft-tissues': ['Indications', 'Specification of the Examination'],
}
EVIDENCE = {
    'examination_scope': ['actual_exam_scope_and_unassessed_limits'],
    'current_exam_assessment': ['actual_acquired_grayscale_assessment'],
    'current_finding': ['actual_patient_acquisition_and_localization'],
    'measurement': ['actual_patient_calibrated_measurement'],
    'flow_assessment': ['actual_patient_flow_sensitive_acquisition'],
    'interpretation': ['actual_patient_findings_and_clinical_context'],
    'classification': ['actual_patient_features_and_named_classification'],
    'assessment_scope': ['actual_exam_level_and_site_documentation'],
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def read(path, root=ROOT):
    return json.loads((root / path).read_bytes())


def report_sources(root=ROOT):
    authored = read(AUTHOR, root)['investigations'][CASE]
    raw = read(COMPILED, root)
    compiled, = [row for form in raw['forms'].values() for row in form['investigations'] if row['id'] == CASE]
    if [s['id'] for s in authored['sections']] != EXPECTED_SECTIONS:
        raise ValueError('Neck report section scope changed')
    if [s['anatomy_id'] for s in compiled['sections']] != EXPECTED_SECTIONS:
        raise ValueError('Authored/compiled neck report scope differs')
    for section, actual in zip(authored['sections'], compiled['sections']):
        if {f['id'] for f in section['findings']} != set(TYPES[section['id']]):
            raise ValueError('Neck report field scope changed: ' + section['id'])
        if section['label'] != actual['label'] or [f['text'] for f in section['findings']] != [f['text'] for f in actual['findings']]:
            raise ValueError('Authored/compiled neck statements differ')
        if section.get('normal') != (actual.get('normal') or {}).get('text'):
            raise ValueError('Authored/compiled neck normal statement differs')
        for field, compiled_field in zip(section['findings'], actual['findings']):
            expected = [CASE + ':' + section['id'] + ':' + value for value in field.get('requires_any', [])]
            if compiled_field.get('requires_any', []) != expected:
                raise ValueError('Authored/compiled neck finding dependency differs')
    return authored, compiled


def build(root=ROOT):
    authored, compiled = report_sources(root)
    by_section = {s['id']: s for s in authored['sections']}
    actual_by_section = {s['anatomy_id']: s for s in compiled['sections']}
    targets, records = [], []

    def target(organ, side, name, section, tissue):
        parent = by_section[section]
        identifier = 'neck_us.' + organ + '.' + side
        targets.append(dict(id=identifier, name=name, requirement_type='anatomical_landmark',
            laterality=side, tissue_class=tissue, source_section_id=section,
            report_provenance={'path': AUTHOR, 'section_id': section, 'section_sha256': digest(parent)},
            guidance=[{'source_id': GUIDANCE, 'sections': list(GUIDANCE_SECTIONS[section])}],
            required_representations=list(KINDS), modality_scope=['Ultrasound'],
            required_extent='The named structure, its relevant interfaces and acquired limits. A partial source or a label alone cannot establish the complete requirement.',
            clinical_approval=False, representation_completion_claim=False))
        if tissue == 'salivary_duct':
            targets[-1]['acquisition_condition'] = 'Duct/obstruction question and actual visibility; no claim that a normal nondilated duct must be fully visible.'
        if section == 'vessels':
            targets[-1]['guidance_scope'] = 'Target identity comes from the actual report; the parameter supports acquisition/documentation, not a complete vascular protocol.'
        return identifier

    for section, organ, label in [('parotid-glands', 'parotid', 'parotid gland'),
                                  ('submandibular-glands', 'submandibular', 'submandibular gland')]:
        for side in ['right', 'left']:
            target(organ, side, side + ' ' + label, section, 'gland_body')
            target(organ + '_duct', side, side + ' main ' + label.replace('gland', 'duct'), section, 'salivary_duct')
    target('thyroid_lobe', 'right', 'right thyroid lobe', 'thyroid-gland', 'gland_body')
    target('thyroid_lobe', 'left', 'left thyroid lobe', 'thyroid-gland', 'gland_body')
    target('thyroid_isthmus', 'not_applicable', 'thyroid isthmus', 'thyroid-gland', 'gland_body')
    for side in ['right', 'left']:
        target('common_carotid', side, side + ' common carotid artery', 'vessels', 'artery_landmark')
        target('internal_jugular', side, side + ' internal jugular vein', 'vessels', 'vein_landmark')

    for section in authored['sections']:
        section_id = section['id']; actual = actual_by_section[section_id]
        fields = ([dict(id='normal', text=section['normal'])] if section.get('normal') else []) + section['findings']
        for field in fields:
            key = field['id']
            kind = ('flow_assessment' if section_id == 'vessels' else 'current_exam_assessment') if key == 'normal' else TYPES[section_id][key]
            actual_field = actual['normal'] if key == 'normal' else next(f for f in actual['findings'] if f['id'].rsplit(':', 1)[-1] == key)
            record = dict(id='neck_us.' + section_id + '.' + key, name=field.get('label', section['label'] + ' assessment'),
                requirement_type=kind, source_section_id=section_id, source_field_id=key,
                report_provenance={'path': AUTHOR, 'section_id': section_id, 'field_id': key,
                    'statement': field['text'], 'statement_sha256': digest(field['text']),
                    'compiled_field_id': actual_field['id'], 'compiled_field_sha256': digest(actual_field)},
                guidance=[{'source_id': GUIDANCE, 'sections': list(GUIDANCE_SECTIONS[section_id])}],
                requires_any=list(actual_field.get('requires_any', [])),
                source_slots=[{k: slot[k] for k in ['id', 'kind', 'unit', 'source_token', 'options'] if k in slot} for slot in actual_field.get('slots', [])],
                required_evidence=list(EVIDENCE[kind]), required_representations=[],
                repeated_instances='each_actual_finding_when_present' if kind in ['current_finding', 'measurement', 'flow_assessment', 'interpretation', 'classification'] else 'actual_exam_scope',
                current_patient_evidence='requires_actual_exam; teaching assets cannot satisfy it',
                clinical_approval=False, representation_completion_claim=False)
            if kind == 'measurement':
                record['measurement'] = dict(unit='mm', number_of_values=sum(s['kind'] == 'number' for s in actual_field['slots']),
                    axis_definition='short_axis' if section_id in ['right-neck-nodes', 'left-neck-nodes'] else 'three_dimensions' if section_id == 'area-of-concern' else 'dimension_not_specified_by_this_field')
            records.append(record)
        # These options carry flow meaning inside a broader appearance statement.
        if section_id in ['thyroid-gland', 'right-neck-nodes', 'left-neck-nodes']:
            field_id, value = ('diffuse', 'hypervascular') if section_id == 'thyroid-gland' else ('features', 'peripheral vascularity')
            source = next(row for row in records if row['source_section_id'] == section_id and row['source_field_id'] == field_id)
            flow = deepcopy(source); flow.update(id=source['id'] + '.flow', name='Conditional flow finding',
                requirement_type='flow_assessment', required_evidence=list(EVIDENCE['flow_assessment']),
                applies_when={'compiled_field_id': source['report_provenance']['compiled_field_id'], 'selected_value': value})
            records.append(flow)
        if section_id in ['right-neck-nodes', 'left-neck-nodes']:
            side = section_id.split('-', 1)[0]
            records.append(dict(id='neck_us.nodal_scope.' + side, name=side + ' neck nodal assessment scope',
                requirement_type='assessment_scope', source_section_id=section_id,
                report_provenance={'path': AUTHOR, 'section_id': section_id, 'section_sha256': digest(section)},
                guidance=[{'source_id': GUIDANCE, 'sections': ['Cervical Lymph Node Evaluation']}],
                laterality=side, source_level_choices=['I', 'II', 'III', 'IV', 'V', 'VI'],
                level_meaning='Report location choices, not twelve independent anatomical compartments or complete station volumes. Preserve actual node location and unassessed regions, including central-compartment ambiguity.',
                required_evidence=list(EVIDENCE['assessment_scope']), required_representations=[],
                clinical_approval=False, representation_completion_claim=False))

    return dict(schema_version=1, schema='primer.typed-descriptor-requirements/1', investigation_id=CASE,
        title=authored['title'], guide_id=authored['guide_id'], clinical_validation_status='unreviewed',
        clinical_approval=False, structure_coverage_granted=False, representation_completion_claim=False,
        source_report={'author_path': AUTHOR, 'author_investigation_sha256': digest(authored),
            'compiled_path': COMPILED, 'compiled_investigation_sha256': digest(compiled),
            'fast_report_path': FAST, 'fast_report_sha256': digest(read(FAST, root)['templates'][CASE]),
            'source_section_ids': list(EXPECTED_SECTIONS), 'source_section_count': 9,
            'authored_report_citation_ids': ['acr-parameters'],
            'citation_scope': 'The original authoring cites the generic ACR parameter index. The specific AIUM citation is an independent audit rationale; no direct derivation of the author text is claimed.'},
        sources=[{'id': 'current-neck-authoring', 'kind': 'current_authored_report', 'path': AUTHOR,
                  'clinical_approval': False},
                 {'id': GUIDANCE, 'kind': 'author_guidance', 'title': 'AIUM Practice Parameter for Diagnostic Ultrasound of the Thyroid and Extracranial Head and Neck',
                  'doi': '10.1002/jum.16251', 'url': 'https://onlinelibrary.wiley.com/doi/10.1002/jum.16251',
                  'published': '2023-05-05', 'checked_on': '2026-11-22',
                  'use': 'Requirement rationale and scope; no copied images, altered report, clinical approval or automatic classification.'}],
        conventions={'ordinary_anatomy': 'Image, schematic and model are separate Primer learning obligations, not a claim that the guidance mandates three teaching representations.',
            'current_observations': 'Findings, measurements, flow, classification and examination scope need actual patient evidence. They do not create automatic normal-mesh obligations.',
            'sides': 'Paired targets follow explicit right/left report choices and the authored bilateral examination. The thyroid isthmus is not duplicated.',
            'vasculature': 'Named common-carotid and internal-jugular landmarks are distinct from patency, thrombus and stenosis assessment. No quantitative duplex thresholds or complete duplex protocol are added.',
            'scope': 'A focused examination retains acquired and unassessed limits. No unlisted muscle set, sublingual glands, parathyroids, arterial branches or twelve full nodal station volumes are inferred.',
            'completion': 'A label, literal binding, license or multiple partial examples never establishes a complete set or clinical approval.'},
        sections=[dict(id=s['id'], label=s['label'], section_sha256=digest(s),
            anatomical_requirement_ids=[t['id'] for t in targets if t['source_section_id'] == s['id']],
            typed_record_ids=[r['id'] for r in records if r['source_section_id'] == s['id']]) for s in authored['sections']],
        anatomical_requirements=targets, evidence_requirements=records,
        report_guidance_gaps=[
            {'section_ids': ['parotid-glands', 'submandibular-glands'], 'source_id': GUIDANCE,
             'guidance_section': 'Parotid and Submandibular Evaluation',
             'gap': 'The report has one lesion-size value. Three-dimensional size, margins and internal flow are not supplied by that value or the static source examples.'},
            {'section_ids': ['thyroid-gland'], 'source_id': GUIDANCE, 'guidance_section': 'Thyroid Evaluation',
             'gap': 'A single nodule dimension and a TR choice do not document all three dimensions or every feature required for the selected risk-stratification system.'},
            {'section_ids': ['right-neck-nodes', 'left-neck-nodes'], 'source_id': GUIDANCE,
             'guidance_section': 'Cervical Lymph Node Evaluation',
             'gap': 'Level labels do not instantiate each current node, site boundaries or unassessed tissue. Source shape/hilum observations alone are not specific malignant diagnoses.'},
            {'section_ids': ['vessels'], 'source_id': 'current-neck-authoring',
             'gap': 'The form contains no velocity criteria or full dedicated vascular protocol. An ordinary vessel landmark cannot establish patency, thrombus or stenosis severity.'}],
        source_contexts=[{'source_id': 'segthy-001', 'sections': ['thyroid-gland', 'vessels'],
            'role': 'Separate tracked ultrasound sweeps with original labels and surfaces; source-label ambiguities remain explicit.',
            'requirement_ids': [], 'coverage_granted': False, 'current_patient_registration': False},
            {'source_id': 'salivary-us-2025', 'figure_id': 'salivary-us-2025-figure3', 'panels': ['A', 'B'],
             'sections': ['parotid-glands', 'submandibular-glands'], 'role': 'Unsided healthy-subject grayscale examples only.',
             'side': 'not_reported', 'plane': 'not_reported', 'requirement_ids': [], 'coverage_granted': False}],
        counts={'anatomical_requirements': len(targets), 'representation_obligations': len(targets) * len(KINDS),
                'typed_evidence_records': len(records), 'evidence_records_by_type': dict(sorted(Counter(r['requirement_type'] for r in records).items()))})


def validate(inventory, root=ROOT):
    expected = build(root)
    if inventory != expected:
        raise ValueError('Typed neck inventory differs from the current exact report or reviewed dispositions')
    return inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--write', action='store_true'); args = parser.parse_args()
    expected = build(); path = ROOT / OUTPUT
    if args.write: path.write_text(json.dumps(expected, indent=2, ensure_ascii=False) + '\n')
    else: validate(read(OUTPUT))
    print(json.dumps(expected['counts'], indent=2))


if __name__ == '__main__':
    main()
