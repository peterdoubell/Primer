"""Whole-library clinical-content contract and deterministic composition checks.

These checks establish completeness, provenance and selection behaviour. They do
not constitute clinical validation of the authored reporting vocabulary.
"""
from __future__ import annotations

import copy
import gzip
import importlib.util
import itertools
import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'data/radiology/descriptor-reporting.json').read_text())
SOURCE = json.loads(gzip.decompress((ROOT / 'data/radiology/descriptor-reporting-v1.json.gz').read_bytes()))
SPEC = importlib.util.spec_from_file_location('all_anatomic_engine', ROOT / 'primer/descriptor_reporting.py')
ENGINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENGINE)
EXAMS = {inv['id']: (form, inv) for form in CATALOG['forms'].values() for inv in form['investigations']}
EXAM_PAIRS = list(EXAMS.values())
AUTHORED_PATHS = sorted({*(ROOT / 'data/radiology').glob('msk-anatomic-*.json'),
                         *(ROOT / 'data/radiology').glob('anatomic-*.json')})
AUTHORED = [(path, json.loads(path.read_text())) for path in AUTHORED_PATHS]


def rows(identifier):
    return {row['anatomy_id']: row for row in EXAMS[identifier][1]['sections']}


def findings(row):
    return {finding['id'].rsplit(':', 1)[-1]: finding for finding in row['findings']}


def supplied_values(descriptor):
    # Explicit synthetic observations for validation, never clinical defaults.
    return {slot['id']: slot['options'][0]['value'] if slot['kind'] == 'choice'
            else max(slot.get('minimum', 0), 1) for slot in descriptor['slots']}


def with_parents(section, finding):
    definitions = {item['id']: item for item in section['findings']}
    chosen = {}

    def include(item, chain=frozenset()):
        assert item['id'] not in chain, ('cyclic dependency', item['id'])
        if item['id'] in chosen:
            return
        if item.get('requires_any'):
            include(definitions[item['requires_any'][0]], chain | {item['id']})
        chosen[item['id']] = supplied_values(item)

    include(finding)
    return chosen


def selection(section, chosen):
    value = {'findings': chosen}
    return {'instances': [value]} if section.get('repeatable') else value


def scoped_state(inv, section, state):
    # Explicit synthetic acquisition, never a production default.
    scope=section.get('requires_scope')
    if scope:
        state[scope['section_id']]={'findings':{scope['finding_id']:{scope['slot_id']:scope['values'][0]}}}
    return {'investigation_id':inv['id'],'selections':state}


def render(form, inv, section, chosen, extra=None):
    state = {section['id']: selection(section, chosen)}
    state.update(extra or {})
    return ENGINE.render_descriptors(form, scoped_state(inv,section,state))


def codes(result):
    return {issue['code'] for issue in result['issues']}


def test_every_native_investigation_and_source_worksheet_is_curated_without_fallback():
    original_ids = {inv['id'] for form in SOURCE['forms'].values() for inv in form['investigations']}
    new_mri_exams = {'msk.mri-hip', 'msk.mri-foot', 'msk.mri-wrist', 'msk.mri-hand'}
    authored_ids = [iid for _, authored in AUTHORED for iid in authored['investigations']]
    additions = set(json.loads((ROOT / 'data/radiology/anatomic-additions-20261026.json').read_text())['investigations'])
    expected = 156 + len(additions)
    assert len(CATALOG['forms']) == 98
    assert len(EXAMS) == len(authored_ids) == len(set(authored_ids)) == expected
    assert set(EXAMS) == original_ids | new_mri_exams | additions == set(authored_ids)
    assert {iid for iid in original_ids if iid.startswith('template:')} <= set(authored_ids)
    assert CATALOG['summary']['anatomic_investigations'] == expected
    assert CATALOG['summary']['investigations'] == expected
    assert CATALOG['summary']['descriptors_requiring_context'] == 0
    assert CATALOG['summary']['context_slots'] == 0
    assert len(CATALOG['anatomic_coverage']) == expected
    for form, inv in EXAM_PAIRS:
        assert inv['presentation'] == 'anatomic_rows', inv['id']
        assert inv['clinical_approval'] is False
        assert inv['sections'], inv['id']
        for row in inv['sections']:
            assert row['anatomy_id'] and row['group'] and row['label'], (inv['id'], row['id'])
            for finding in ([row['normal']] if row['normal'] else []) + row['findings']:
                assert finding['source']['source_kind'] == 'curated-anatomic-report'
                assert not finding['requires_context']
                assert {slot['kind'] for slot in finding['slots']} <= {'choice', 'number'}
                assert all('default' not in slot for slot in finding['slots'])
                assert not any(slot.get('type') in {'text', 'textarea'} for slot in finding['slots'])


def test_authored_coverage_and_reference_lineage_are_complete_and_not_clinical_approval():
    coverage = {record['investigation_id']: record for record in CATALOG['anatomic_coverage']}
    for path, authored in AUTHORED:
        source_map = {source['id']: source for source in authored['sources']}
        assert len(source_map) == len(authored['sources'])
        for source in source_map.values():
            parsed = urlsplit(source['url'])
            assert parsed.scheme == 'https' and parsed.netloc and not parsed.username and not parsed.password
            assert source['title'].strip()
        manifest = authored['coverage']
        if isinstance(manifest, list):
            declared = {record['investigation_id']: record['expected_anatomy_ids'] for record in manifest}
        else:
            # The released MSK authoring files predate the uniform list format.
            declared = {key: value['structure_ids'] if isinstance(value, dict) else value
                        for key, value in manifest.items()}
        assert set(declared) == set(authored['investigations'])
        for iid, definition in authored['investigations'].items():
            form, inv = EXAMS[iid]
            expected = [row['id'] for row in definition['sections']]
            assert expected == declared[iid] == coverage[iid]['anatomy_ids']
            assert [row['anatomy_id'] for row in inv['sections']] == expected
            assert coverage[iid]['structures'] == len(expected)
            assert coverage[iid]['findings'] == sum(len(row['findings']) for row in definition['sections'])
            assert coverage[iid]['source_file'] == str(path.relative_to(ROOT))
            for row in inv['sections']:
                for finding in ([row['normal']] if row['normal'] else []) + row['findings']:
                    provenance = finding['source']
                    assert provenance['clinical_approval'] is False
                    assert provenance['source_file'] == str(path.relative_to(ROOT))
                    assert provenance['source_ids'] and set(provenance['source_ids']) <= set(source_map)
                    assert len(provenance['reference_ids']) == len(provenance['source_ids'])
                    for source_id, reference_id in zip(provenance['source_ids'], provenance['reference_ids']):
                        assert form['anatomic_sources'][reference_id] == source_map[source_id]


@pytest.mark.parametrize(('exam', 'required'), [
    ('ra.ct-temporal-bone', {f'{side}-{structure}' for side in ('right', 'left') for structure in (
        'malleus', 'incus', 'stapes', 'incudomalleolar-joint', 'incudostapedial-joint', 'cochlea', 'vestibule',
        'superior-semicircular-canal', 'posterior-semicircular-canal', 'lateral-semicircular-canal',
        'labyrinthine-facial-canal', 'tympanic-facial-canal', 'mastoid-facial-canal', 'tegmen-tympani', 'tegmen-mastoideum')}),
    ('ra.mri-trigeminal', {f'{side}-{structure}' for side in ('right', 'left') for structure in (
        'nucleus', 'root-entry', 'cisternal', 'meckel', 'cavernous', 'v2', 'v3', 'masseter',
        'temporalis', 'medial-pterygoid', 'lateral-pterygoid')}),
    ('ra.mri-lumbar-disc', {f'{level}-{structure}' for level in ('l1-l2', 'l2-l3', 'l3-l4', 'l4-l5', 'l5-s1')
        for structure in ('disc', 'canal', 'right-recess', 'left-recess', 'right-foramen', 'left-foramen', 'right-facet', 'left-facet')}),
    ('ra.mri-prostate', {'prostate-lesion', 'prostatic-capsule', 'right-neurovascular-bundle', 'left-neurovascular-bundle',
        'right-seminal-vesicle', 'left-seminal-vesicle', 'bladder-neck', 'external-urethral-sphincter',
        'nodes-right-obturator', 'nodes-left-obturator', 'nodes-right-internal-iliac', 'nodes-left-internal-iliac'}),
    ('ra.liver-masses', {'segment-i', 'segment-ii', 'segment-iii', 'segment-iva', 'segment-ivb', 'segment-v',
        'segment-vi', 'segment-vii', 'segment-viii', 'right-hepatic-vein', 'middle-hepatic-vein', 'left-hepatic-vein',
        'main-portal-vein', 'right-portal-vein', 'left-portal-vein'}),
    ('ra.mri-endometriosis', {'right-ovary', 'left-ovary', 'right-distal-ureter', 'left-distal-ureter',
        'right-uterosacral-ligament', 'left-uterosacral-ligament', 'torus-uterinus', 'rectovaginal-septum',
        'posterior-vaginal-fornix', 'pouch-of-douglas', 'bladder-dome', 'anterior-rectal-wall', 'rectosigmoid'}),
    ('ra.ct-coronary', {'rca-proximal', 'rca-mid', 'rca-distal', 'left-main', 'lad-proximal', 'lad-mid',
        'lad-distal', 'first-diagonal', 'second-diagonal', 'lcx-proximal', 'lcx-distal', 'first-obtuse-marginal',
        'second-obtuse-marginal', 'right-pda', 'left-pda', 'ramus-intermedius'}),
    ('ra.mri-cardiomyopathy', {'myocardium-'+name for name in (
        'basal-anterior', 'basal-anteroseptal', 'basal-inferoseptal', 'basal-inferior', 'basal-inferolateral', 'basal-anterolateral',
        'mid-anterior', 'mid-anteroseptal', 'mid-inferoseptal', 'mid-inferior', 'mid-inferolateral', 'mid-anterolateral',
        'apical-anterior', 'apical-septal', 'apical-inferior', 'apical-lateral', 'apical-cap')}),
    ('ra.mri-breast', {f'{side}-{structure}' for side in ('right', 'left') for structure in (
        'upper-outer-quadrant', 'upper-inner-quadrant', 'lower-inner-quadrant', 'lower-outer-quadrant',
        'retroareolar-region', 'axillary-tail', 'skin', 'nipple', 'axillary-level-i', 'axillary-level-ii',
        'axillary-level-iii', 'internal-mammary-chain')}),
    ('ra.ultrasound-neonatal-brain', {f'{side}-{structure}' for side in ('right', 'left') for structure in (
        'germinal-matrix', 'lateral-ventricle', 'periventricular-white-matter', 'basal-ganglia', 'cortex')}),
    ('ra.ultrasound-paediatric-scrotum', {f'{side}-{structure}' for side in ('right', 'left') for structure in (
        'testis', 'testicular-flow', 'cord', 'epididymis-head', 'epididymis-body', 'epididymis-tail', 'appendage', 'tunica', 'inguinal')}),
    ('ra.paediatric-chest-ct', {'right-upper-lobe', 'right-middle-lobe', 'right-lower-lobe', 'left-upper-lobe',
        'lingula', 'left-lower-lobe', 'airway-right-main-bronchus', 'airway-left-main-bronchus',
        'airway-bronchus-intermedius', 'right-pleura', 'left-pleura', 'congenital-lung-lesion'}),
], ids=lambda value: value if isinstance(value, str) else None)
def test_representative_reports_preserve_named_structures_and_bilateral_assessments(exam, required):
    assert required <= rows(exam).keys()
    sections = rows(exam)
    assert all(sections[key]['findings'] for key in required)
    assert len({sections[key]['id'] for key in required}) == len(required)


@pytest.mark.parametrize(('form', 'inv'), EXAM_PAIRS, ids=list(EXAMS))
def test_every_authored_finding_path_and_required_parent_renders_without_invented_values(form, inv):
    for section in inv['sections']:
        for finding in section['findings']:
            chosen = with_parents(section, finding)
            state = copy.deepcopy(chosen)
            result = render(form, inv, section, chosen)
            assert result['valid'], (inv['id'], finding['id'], result['issues'])
            assert chosen == state, 'Rendering must not mutate saved observations'
            assert '__' not in result['text'] and '[' not in result['text'] and ']' not in result['text']
            reported = {item['id'] for item in section['findings'] if item.get('report') is not False}
            assert result['selected_finding_count'] == len(set(chosen) & reported) + int(bool(section.get('requires_scope')))
            if set(chosen) & reported:
                assert result['text'], (inv['id'], finding['id'])
            if finding.get('requires_any'):
                missing = render(form, inv, section, {finding['id']: supplied_values(finding)})
                assert not missing['valid'] and 'inactive_descriptor_finding' in codes(missing), finding['id']
                by_id = {item['id']: item for item in section['findings']}
                for parent_id in finding['requires_any']:
                    alternative = with_parents(section, by_id[parent_id])
                    alternative[finding['id']] = supplied_values(finding)
                    accepted = render(form, inv, section, alternative)
                    assert accepted['valid'], (finding['id'], parent_id, accepted['issues'])


@pytest.mark.parametrize(('form', 'inv'), EXAM_PAIRS, ids=list(EXAMS))
def test_unselected_anatomy_and_absent_normals_are_never_filled_in(form, inv):
    empty = ENGINE.render_descriptors(form, {'investigation_id': inv['id'], 'selections': {}})
    assert empty['valid'] and empty['text'] == '' and empty['sections'] == []
    for section in inv['sections']:
        result = ENGINE.render_descriptors(form, scoped_state(inv,section,{section['id']: {'normal': True}}))
        if section['normal']:
            assert result['valid'], (section['id'], result['issues'])
            assert result['text'].endswith(section['normal']['text'])
            assert len(result['sections']) == 1 + int(bool(section.get('requires_scope')))
            assert not section['normal']['slots']
        else:
            assert not result['valid'] and 'normal_not_available' in codes(result)


def test_every_declared_cross_normal_and_exclusive_pair_is_enforced():
    cross_count = exclusive_count = 0
    for form, inv in EXAM_PAIRS:
        by_id = {row['id']: row for row in inv['sections']}
        for section in inv['sections']:
            groups = {}
            for finding in section['findings']:
                if finding.get('exclusive_group'):
                    groups.setdefault(finding['exclusive_group'], []).append(finding)
                for target in finding.get('invalidates_normal', []):
                    assert target in by_id
                    if target == section['id'] or not by_id[target]['normal']:
                        continue
                    result = render(form, inv, section, with_parents(section, finding), {target: {'normal': True}})
                    assert not result['valid'] and result['text'] == ''
                    assert 'conflicting_anatomic_normal' in codes(result), (finding['id'], target, result['issues'])
                    cross_count += 1
            for group in groups.values():
                for left, right in itertools.combinations(group, 2):
                    chosen = {**with_parents(section, left), **with_parents(section, right)}
                    result = render(form, inv, section, chosen)
                    assert not result['valid'] and result['text'] == ''
                    assert 'conflicting_descriptor_findings' in codes(result), (left['id'], right['id'], result['issues'])
                    exclusive_count += 1
    assert cross_count > 500
    assert exclusive_count > 500


def test_all_declared_numeric_bounds_are_enforced_and_nonfinite_values_are_rejected():
    tested = 0
    for form, inv in EXAM_PAIRS:
        for section in inv['sections']:
            for finding in section['findings']:
                for slot in finding['slots']:
                    if slot['kind'] != 'number':
                        continue
                    if 'minimum' in slot and 'maximum' in slot:
                        assert slot['minimum'] <= slot['maximum'], finding['id']
                    for key, delta in [('minimum', -1), ('maximum', 1)]:
                        if key not in slot:
                            continue
                        chosen = with_parents(section, finding)
                        chosen[finding['id']][slot['id']] = slot[key] + delta
                        result = render(form, inv, section, chosen)
                        assert not result['valid'] and result['text'] == ''
                        assert 'descriptor_number_out_of_range' in codes(result), (finding['id'], slot, result['issues'])
                        tested += 1
                    for invalid in (True, '12', float('nan'), float('inf')):
                        chosen = with_parents(section, finding)
                        chosen[finding['id']][slot['id']] = invalid
                        result = render(form, inv, section, chosen)
                        assert not result['valid'] and 'invalid_descriptor_number' in codes(result), finding['id']
    assert tested > 1000


def test_repeat_instances_preserve_independent_sides_and_measurements_and_do_not_deduplicate():
    form, inv = EXAMS['ra.ultrasound-breast']
    section = rows(inv['id'])['breast-lesion']
    by_id = findings(section)
    first = {**with_parents(section, by_id['side']), **with_parents(section, by_id['size'])}
    second = copy.deepcopy(first)
    first[by_id['side']['id']]['slot-1'] = 'right'
    second[by_id['side']['id']]['slot-1'] = 'left'
    first[by_id['size']['id']] = {'slot-1': 12, 'slot-2': 8, 'slot-3': 6}
    second[by_id['size']['id']] = {'slot-1': 22, 'slot-2': 14, 'slot-3': 9}
    original = copy.deepcopy([first, second])
    state = {'investigation_id': inv['id'], 'selections': {section['id']: {'instances': [
        {'findings': first}, {'findings': second}, {'findings': copy.deepcopy(first)}]}}}
    result = ENGINE.render_descriptors(form, state)
    assert result['valid'], result['issues']
    assert 'Lesion 1:' in result['text'] and 'Lesion 2:' in result['text'] and 'Lesion 3:' in result['text']
    assert result['text'].count('12 × 8 × 6 mm') == 2
    assert result['text'].count('22 × 14 × 9 mm') == 1
    assert 'right breast' in result['text'] and 'left breast' in result['text']
    assert [first, second] == original
    broken = copy.deepcopy(state)
    broken['selections'][section['id']]['instances'][1]['findings'][by_id['size']['id']]['slot-1'] = -1
    failed = ENGINE.render_descriptors(form, broken)
    assert not failed['valid'] and failed['text'] == '' and 'descriptor_number_out_of_range' in codes(failed)
    assert first[by_id['size']['id']]['slot-1'] == 12
    conflicting = copy.deepcopy(state)
    conflicting['selections'][section['id']]['normal'] = True
    failed = ENGINE.render_descriptors(form, conflicting)
    assert not failed['valid'] and 'invalid_repeat_instances' in codes(failed)


@pytest.mark.parametrize(('exam', 'row_ids'), [
    ('ra.mri-breast', {'right-upper-outer-quadrant', 'left-upper-outer-quadrant', 'right-chest-wall', 'left-chest-wall'}),
    ('ra.ct-tavi', {'right-common-iliac-artery', 'left-common-iliac-artery', 'right-common-femoral-artery', 'left-common-femoral-artery'}),
    ('ra.cardiovascular-devices', {'central-line', 'right-atrial-lead', 'right-ventricular-lead', 'lvad'}),
    ('ra.thymus', {'chemical-shift', 'thymic-enhancement'}),
    ('ra.ct-acute-aortic-syndrome', {'right-renal-artery', 'left-renal-artery', 'coronary-extension'}),
    ('ra.tinnitus', {'right-cochlear-nerve', 'left-cochlear-nerve', 'right-internal-auditory-canal', 'left-internal-auditory-canal'}),
    ('ra.venous-sinus-thrombosis', {'superior-sagittal-sinus', 'straight-sinus', 'right-transverse-sinus', 'left-transverse-sinus'}),
    ('ra.mri-rectal-cancer', {'prostate', 'seminal-vesicles', 'vaginal-wall', 'restaging'}),
])
def test_modality_coverage_sex_and_procedure_specific_rows_are_excluded_from_bulk_normal(exam, row_ids):
    sections = rows(exam)
    for key in row_ids:
        assert sections[key]['exclude_from_bulk_normal'], (exam, key)


def test_physics_protocol_and_safety_worksheets_cannot_bulk_assert_a_completed_procedure():
    ids = ['template:modalities-report', 'template:radiation-safety-report', 'template:ct-image-report',
           'template:mri-sequences-report', 'template:structured-reporting-report', 'template:ultrasound-physics-report',
           'ra.paediatric-ultrasound-values', 'ra.ct-contrast-protocols', 'template:biopsy-safety-report']
    for iid in ids:
        for section in EXAMS[iid][1]['sections']:
            assert section['normal'] is None, (iid, section['id'])
            assert section['exclude_from_bulk_normal'], (iid, section['id'])
    for iid, row_id, performed in [('template:biopsy-safety-report', 'biopsy-event', 'performed'),
                                    ('template:biopsy-safety-report', 'drainage-event', 'performed'),
                                    ('ra.ct-contrast-protocols', 'actual-injection', 'performed')]:
        section = rows(iid)[row_id]
        definitions = findings(section)
        assert not definitions[performed].get('requires_any')
        for key, descriptor in definitions.items():
            if key != performed:
                assert descriptor['requires_any'] == [definitions[performed]['id']]


def test_relevant_followups_do_not_cross_incompatible_lesion_or_implant_types():
    breast = findings(rows('ra.mri-breast')['breast-lesion'])
    assert breast['mass']['exclusive_group'] == breast['nonmass']['exclusive_group']
    assert breast['shape']['requires_any'] == [breast['mass']['id']]
    assert breast['nme-distribution']['requires_any'] == [breast['nonmass']['id']]
    for side in ('right', 'left'):
        implant = findings(rows('ra.breast-implants')[side + '-implant'])
        assert implant['silicone']['exclusive_group'] == implant['saline']['exclusive_group'] == implant['dual']['exclusive_group']
        assert implant['intracapsular']['requires_any'] == [implant['silicone']['id'], implant['dual']['id']]
        assert implant['saline']['id'] not in implant['extracapsular']['requires_any']
    coronary = findings(rows('ra.ct-coronary')['lad-proximal'])
    assert not coronary['plaque'].get('requires_any'), 'Plaque may exist without measurable luminal stenosis'
    assert coronary['highrisk']['requires_any'] == [coronary['plaque']['id']]
