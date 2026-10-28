"""Behavioural checks for the anatomy-specific MSK reporting contract.

These verify coverage and safe deterministic composition, not clinical approval.
"""
from __future__ import annotations

import copy
import gzip
import importlib.util
import itertools
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'data/radiology/descriptor-reporting.json').read_text())
SPEC = importlib.util.spec_from_file_location('msk_descriptor_engine', ROOT / 'primer/descriptor_reporting.py')
ENGINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENGINE)
# MSK remains a separately guarded subset as the rest of radiology is expanded.
MSK_IDS = {identifier for path in (ROOT / 'data/radiology').glob('msk-anatomic-*.json')
           for identifier in json.loads(path.read_text())['investigations']}
ANATOMIC = [(form, investigation) for form in CATALOG['forms'].values()
            for investigation in form['investigations'] if investigation['id'] in MSK_IDS]
EXAMS = {investigation['id']: (form, investigation) for form, investigation in ANATOMIC}


def rows(exam):
    return {section['anatomy_id']: section for section in EXAMS[exam][1]['sections']}


def supplied_values(descriptor):
    """Explicit test observations, never patient defaults."""
    return {slot['id']: slot['options'][0]['value'] if slot['kind'] == 'choice'
            else slot.get('minimum', 1) for slot in descriptor['slots']}


def selected_with_parents(section, finding):
    definitions = {item['id']: item for item in section['findings']}
    chosen = {}
    def include(item):
        if item['id'] in chosen:
            return
        if item.get('requires_any'):
            include(definitions[item['requires_any'][0]])
        chosen[item['id']] = supplied_values(item)
    include(finding)
    return chosen


def render(form, investigation, section, chosen, extra=None):
    selections = {section['id']: {'findings': chosen}}
    selections.update(extra or {})
    return ENGINE.render_descriptors(form, {'investigation_id': investigation['id'], 'selections': selections})


def issues(result):
    return {item['code'] for item in result['issues']}


def test_each_cuff_tendon_and_muscle_is_independently_selectable():
    sections = rows('ra.mri-shoulder')
    for tendon in ('supraspinatus', 'infraspinatus', 'subscapularis', 'teres-minor'):
        assert tendon + '-tendon' in sections
        assert tendon + '-muscle' in sections
        assert sections[tendon + '-tendon']['normal']
        assert sections[tendon + '-muscle']['normal']
        finding_ids = {finding['id'].rsplit(':', 1)[-1] for finding in sections[tendon + '-tendon']['findings']}
        assert {'partial-tear', 'full-tear', 'retraction'} <= finding_ids
    required = {'superior-labrum', 'anterosuperior-labrum', 'anterior-labrum', 'anteroinferior-labrum',
                'inferior-labrum', 'posteroinferior-labrum', 'posterior-labrum', 'posterosuperior-labrum',
                'sghl', 'mghl', 'ighl-anterior', 'ighl-posterior', 'axillary-pouch', 'rotator-interval',
                'coracohumeral', 'coracoacromial', 'conoid', 'trapezoid', 'ac-superior', 'ac-inferior'}
    assert required <= sections.keys()


def test_knee_has_each_meniscal_segment_root_ligament_and_cartilage_surface():
    sections = rows('ra.mri-knee')
    menisci = {f'{side}-meniscus-{segment}' for side in ('medial', 'lateral')
               for segment in ('anterior-horn', 'body', 'posterior-horn', 'anterior-root', 'posterior-root')}
    stabilisers = {'acl', 'pcl', 'mcl-superficial', 'mcl-deep-meniscofemoral', 'mcl-deep-meniscotibial',
                   'lcl', 'popliteofibular-ligament', 'arcuate-ligament', 'posterior-oblique-ligament',
                   'popliteus', 'biceps-femoris', 'mpfl', 'quadriceps', 'patellar-tendon'}
    surfaces = {'medial-femoral-cartilage', 'medial-tibial-cartilage', 'lateral-femoral-cartilage',
                'lateral-tibial-cartilage', 'patellar-medial-cartilage', 'patellar-lateral-cartilage',
                'patellar-ridge-cartilage', 'trochlear-cartilage'}
    assert menisci | stabilisers | surfaces <= sections.keys()
    for key in ('medial-meniscus-body', 'lateral-meniscus-posterior-horn'):
        findings = {f['id'].rsplit(':', 1)[-1]: f for f in sections[key]['findings']}
        assert findings['extent']['requires_any'] == [findings['radial-tear']['id']]
        assert findings['horizontal-tear']['id'] not in findings['extent']['requires_any']


def test_ankle_has_individual_tendons_ligament_components_and_retinacula():
    sections = rows('ra.mri-ankle')
    required = {'tibialis-posterior', 'flexor-digitorum-longus', 'flexor-hallucis-longus',
                'peroneus-longus', 'peroneus-brevis', 'tibialis-anterior', 'extensor-hallucis-longus',
                'extensor-digitorum-longus', 'achilles', 'plantaris', 'atfl', 'cfl', 'ptfl', 'aitfl', 'pitfl',
                'interosseous-tibiofibular', 'transverse-tibiofibular', 'deltoid-tibionavicular',
                'deltoid-tibiospring', 'deltoid-tibiocalcaneal', 'deltoid-superficial-posterior',
                'deltoid-deep-anterior', 'deltoid-deep-posterior', 'spring-superomedial',
                'spring-inferoplantar', 'spring-medioplantar', 'superior-peroneal-retinaculum',
                'inferior-peroneal-retinaculum', 'flexor-retinaculum', 'superior-extensor-retinaculum',
                'inferior-extensor-retinaculum', 'tarsal-tunnel', 'tibial-nerve-ankle',
                'plantar-fascia-central', 'long-plantar-ligament', 'short-plantar-ligament'}
    assert required <= sections.keys()


def test_new_hip_and_foot_mri_examinations_do_not_turn_radiographs_into_mri():
    for added, base in [('msk.mri-hip', 'ra.hip-fai'), ('msk.mri-foot', 'ra.foot-ankle-cases')]:
        investigation = EXAMS[added][1]
        assert investigation['modality'] == 'MRI'
        assert investigation['base_investigation_id'] == base
    for exam in ['ra.hip-fai', 'ra.foot-ankle-cases', 'ra.paediatric-hip', 'ra.ankle-fractures', 'ra.hip-arthroplasty']:
        investigation = EXAMS[exam][1]
        assert 'MRI' not in investigation['modality']
        normal_text = ' '.join(s['normal']['text'] for s in investigation['sections'] if s['normal']).lower()
        assert 'marrow' not in normal_text
        assert 'ligament' not in normal_text
        assert 'labrum' not in normal_text
    assert {'labrum-anterosuperior', 'gluteus-medius-tendon', 'gluteus-minimus-tendon', 'iliofemoral-ligament',
            'pubofemoral-ligament', 'ischiofemoral-ligament', 'ligamentum-teres'} <= rows('msk.mri-hip').keys()
    assert {'lisfranc-dorsal', 'lisfranc-interosseous', 'lisfranc-plantar', 'mtp-1-plantar-plate',
            'mtp-5-plantar-plate', 'webspace-3', 'medial-hallux-sesamoid', 'lateral-hallux-sesamoid'} <= rows('msk.mri-foot').keys()


@pytest.mark.parametrize(('form', 'investigation'), ANATOMIC, ids=[i['id'] for _, i in ANATOMIC])
def test_every_curated_finding_renders_with_explicit_values_and_its_parent(form, investigation):
    for section in investigation['sections']:
        for finding in section['findings']:
            chosen = selected_with_parents(section, finding)
            result = render(form, investigation, section, chosen)
            location = (investigation['id'], section['anatomy_id'], finding['id'])
            assert result['valid'], (location, result['issues'])
            assert result['text'], location
            assert '__' not in result['text'] and '[' not in result['text'] and ']' not in result['text'], location
            assert result['selected_finding_count'] == len(chosen), location
            assert not finding['requires_context'], location
            assert {slot['kind'] for slot in finding['slots']} <= {'choice', 'number'}, location
            assert all('default' not in slot for slot in finding['slots']), location


@pytest.mark.parametrize(('form', 'investigation'), ANATOMIC, ids=[i['id'] for _, i in ANATOMIC])
def test_normal_requires_explicit_selection_and_no_unselected_structure_is_invented(form, investigation):
    empty = ENGINE.render_descriptors(form, {'investigation_id': investigation['id'], 'selections': {}})
    assert empty['valid'] and empty['text'] == '' and empty['sections'] == []
    for section in investigation['sections']:
        if section['normal']:
            result = ENGINE.render_descriptors(form, {'investigation_id': investigation['id'], 'selections': {section['id']: {'normal': True}}})
            assert result['valid'], (section['id'], result['issues'])
            assert result['text'].endswith(section['normal']['text'])
            assert len(result['sections']) == 1
            assert section['normal']['slots'] == []
        else:
            result = ENGINE.render_descriptors(form, {'investigation_id': investigation['id'], 'selections': {section['id']: {'normal': True}}})
            assert not result['valid'] and 'normal_not_available' in issues(result)


def test_each_optional_followup_is_rejected_without_an_active_parent():
    checked = 0
    for form, investigation in ANATOMIC:
        for section in investigation['sections']:
            for finding in section['findings']:
                if not finding.get('requires_any'):
                    continue
                result = render(form, investigation, section, {finding['id']: supplied_values(finding)})
                assert not result['valid'] and result['text'] == '', finding['id']
                assert 'inactive_descriptor_finding' in issues(result), (finding['id'], result['issues'])
                checked += 1
    assert checked > 100


def test_mutually_exclusive_findings_cannot_be_rendered_together():
    checked = 0
    for form, investigation in ANATOMIC:
        for section in investigation['sections']:
            groups = {}
            for finding in section['findings']:
                if finding.get('exclusive_group'):
                    groups.setdefault(finding['exclusive_group'], []).append(finding)
            for group in groups.values():
                for left, right in itertools.combinations(group, 2):
                    chosen = {**selected_with_parents(section, left), **selected_with_parents(section, right)}
                    result = render(form, investigation, section, chosen)
                    assert not result['valid'] and result['text'] == ''
                    assert 'conflicting_descriptor_findings' in issues(result), (left['id'], right['id'], result['issues'])
                    checked += 1
    assert checked > 500


def test_every_declared_cross_structure_conflict_rejects_a_normal_statement():
    checked = 0
    for form, investigation in ANATOMIC:
        by_id = {s['id']: s for s in investigation['sections']}
        for section in investigation['sections']:
            for finding in section['findings']:
                for target in finding.get('invalidates_normal', []):
                    assert target in by_id, finding['id']
                    if not by_id[target]['normal'] or target == section['id']:
                        continue
                    result = render(form, investigation, section, selected_with_parents(section, finding), {target: {'normal': True}})
                    assert not result['valid'] and result['text'] == '', finding['id']
                    assert 'conflicting_anatomic_normal' in issues(result), (finding['id'], target, result['issues'])
                    checked += 1
    assert checked > 20


def test_each_numeric_bound_rejects_out_of_range_observations():
    checked = 0
    for form, investigation in ANATOMIC:
        for section in investigation['sections']:
            for finding in section['findings']:
                for slot in finding['slots']:
                    if slot['kind'] != 'number':
                        continue
                    for boundary, delta in [('minimum', -1), ('maximum', 1)]:
                        if boundary not in slot:
                            continue
                        chosen = selected_with_parents(section, finding)
                        chosen[finding['id']][slot['id']] = slot[boundary] + delta
                        result = render(form, investigation, section, chosen)
                        assert not result['valid'] and result['text'] == '', (finding['id'], slot['id'])
                        assert 'descriptor_number_out_of_range' in issues(result), result['issues']
                        checked += 1
                    if slot.get('unit') == '%':
                        assert slot.get('minimum') == 0 and slot.get('maximum') == 100, (finding['id'], slot)
    assert checked > 100


@pytest.mark.parametrize('invalid', [True, False, '10', float('nan'), float('inf'), -float('inf'), {}, []])
def test_measurements_must_be_finite_numbers_not_coerced_values(invalid):
    form, investigation = EXAMS['ra.mri-knee']
    section = rows('ra.mri-knee')['medial-meniscus-position']
    finding = next(f for f in section['findings'] if f['id'].endswith(':extrusion-mm'))
    chosen = selected_with_parents(section, finding)
    chosen[finding['id']]['slot-1'] = invalid
    result = render(form, investigation, section, chosen)
    assert not result['valid'] and 'invalid_descriptor_number' in issues(result)


def test_missing_and_unenumerated_values_are_not_silently_filled_or_copied():
    form, investigation = EXAMS['ra.mri-knee']
    section = rows('ra.mri-knee')['medial-meniscus-body']
    finding = next(f for f in section['findings'] if f['id'].endswith(':extent'))
    chosen = selected_with_parents(section, finding)
    chosen[finding['id']] = {}
    result = render(form, investigation, section, chosen)
    assert not result['valid'] and result['text'] == '' and 'missing_descriptor_value' in issues(result)
    chosen[finding['id']]['slot-1'] = 'unsupported descriptor'
    result = render(form, investigation, section, chosen)
    assert not result['valid'] and result['text'] == '' and 'invalid_descriptor_choice' in issues(result)


def test_bounded_percentages_and_long_distances_have_distinct_constraints():
    form, investigation = EXAMS['ra.mri-knee']
    section = rows('ra.mri-knee')['medial-meniscus-position']
    finding = next(f for f in section['findings'] if f['id'].endswith(':extrusion-mm'))
    slot = finding['slots'][0]
    assert slot['minimum'] == 0 and 'maximum' not in slot
    chosen = selected_with_parents(section, finding)
    chosen[finding['id']][slot['id']] = 101
    assert render(form, investigation, section, chosen)['valid']


def test_ddh_measurements_require_a_valid_plane_and_do_not_guess_graf_grade():
    form, investigation = EXAMS['ra.ultrasound-ddh']
    for side in ('right', 'left'):
        section = rows('ra.ultrasound-ddh')[side + '-standard-plane']
        definitions = {f['id'].rsplit(':', 1)[-1]: f for f in section['findings']}
        assert section['normal'] is None
        assert section['exclude_from_bulk_normal']
        assert definitions['valid']['exclusive_group'] == definitions['invalid']['exclusive_group']
        for key in ('alpha', 'beta', 'coverage'):
            finding = definitions[key]
            assert finding['requires_any'] == [definitions['valid']['id']]
            chosen = {finding['id']: supplied_values(finding), definitions['invalid']['id']: {}}
            result = render(form, investigation, section, chosen)
            assert not result['valid'] and 'inactive_descriptor_finding' in issues(result)
    assert not any('Graf type' in finding['text'] for section in investigation['sections'] for finding in section['findings'])


def test_comparison_cement_and_stress_normals_are_not_bulk_assertions():
    arthroplasty = rows('ra.hip-arthroplasty')
    for key in ('cup-migration', 'stem-subsidence', 'cement'):
        assert arthroplasty[key]['exclude_from_bulk_normal']
    for side in ('right', 'left'):
        assert rows('ra.ultrasound-ddh')[side + '-stress']['exclude_from_bulk_normal']


def test_anatomic_coverage_and_reference_lineage_match_authored_files():
    coverage = {item['investigation_id']: item for item in CATALOG['anatomic_coverage']}
    authored_ids = set()
    for path in sorted((ROOT / 'data/radiology').glob('msk-anatomic-*.json')):
        authored = json.loads(path.read_text())
        source_ids = {source['id'] for source in authored['sources']}
        for identifier, definition in authored['investigations'].items():
            authored_ids.add(identifier)
            form, investigation = EXAMS[identifier]
            expected = [section['id'] for section in definition['sections']]
            assert coverage[identifier]['anatomy_ids'] == expected
            assert coverage[identifier]['structures'] == len(expected)
            assert sorted(section['anatomy_id'] for section in investigation['sections']) == sorted(expected)
            assert investigation['clinical_approval'] is False
            for section in investigation['sections']:
                for finding in ([section['normal']] if section['normal'] else []) + section['findings']:
                    source = finding['source']
                    assert source['source_kind'] == 'curated-anatomic-report'
                    assert set(source['source_ids']) <= source_ids
                    assert source['clinical_approval'] is False
                    assert all(key in form['anatomic_sources'] for key in source['reference_ids'])
    assert authored_ids == set(EXAMS) == MSK_IDS
    assert authored_ids <= set(coverage)
    assert len(MSK_IDS) == 32
    assert sum(coverage[i]['structures'] for i in MSK_IDS) == sum(len(i['sections']) for _, i in ANATOMIC)


def test_packaged_gzip_and_plain_contract_are_identical():
    plain = (ROOT / 'data/radiology/descriptor-reporting.json').read_bytes()
    assert gzip.decompress((ROOT / 'data/radiology/descriptor-reporting.json.gz').read_bytes()) == plain


def test_compiler_rejects_invalid_anatomy_references_and_context_slots(tmp_path):
    compiler_spec = importlib.util.spec_from_file_location('msk_test_compiler', ROOT / 'tools/build_descriptor_reporting.py')
    compiler = importlib.util.module_from_spec(compiler_spec)
    compiler_spec.loader.exec_module(compiler)
    anatomy_spec = importlib.util.spec_from_file_location('msk_test_anatomy', ROOT / 'tools/msk_descriptor_catalog.py')
    anatomy = importlib.util.module_from_spec(anatomy_spec)
    anatomy_spec.loader.exec_module(anatomy)
    directory = tmp_path / 'data/radiology'
    directory.mkdir(parents=True)
    path = directory / 'msk-anatomic-test.json'
    base = {'version': '2026-10-23', 'sources': [{'id': 'source', 'title': 'Reference', 'url': 'https://example.org/reference'}],
            'investigations': {'mri': {'guide_id': 'guide', 'title': 'MRI structure', 'modality': 'MRI',
                'base_investigation_id': 'source-exam', 'sections': [{'id': 'tendon', 'label': 'Tendon', 'normal': 'Tendon intact.',
                    'group': 'Tendons', 'source_ids': ['source'], 'findings': [
                        {'id': 'tear', 'label': 'Tear', 'text': '[Partial / Complete] tendon tear.'},
                        {'id': 'size', 'label': 'Size', 'text': 'Tear length __ mm.', 'requires_any': ['tear'],
                         'slot_overrides': {'slot-1': {'minimum': 0}}}]}]}}}
    def compile_authored(authored):
        path.write_text(json.dumps(authored))
        forms = {'guide': {'investigations': [], 'sources': [], 'provenance': {}}}
        coverage = anatomy.apply_anatomic_reports(forms, tmp_path, compiler.compile_statement, compiler.digest, compiler.slug)
        return forms, coverage
    forms, coverage = compile_authored(base)
    assert coverage[0]['structures'] == 1 and coverage[0]['findings'] == 2
    assert forms['guide']['investigations'][0]['sections'][0]['findings'][1]['requires_any'] == ['mri:tendon:tear']
    malformed = []
    def changed(edit):
        result = copy.deepcopy(base)
        edit(result['investigations']['mri']['sections'])
        malformed.append(result)
    changed(lambda ss: ss.append(copy.deepcopy(ss[0])))
    changed(lambda ss: ss[0].update(source_ids=['missing']))
    changed(lambda ss: ss[0]['findings'][0].update(text='Tear at [location].'))
    changed(lambda ss: ss[0]['findings'][1].update(requires_any=['missing']))
    changed(lambda ss: ss[0]['findings'][0].update(requires_any=['size']))
    changed(lambda ss: ss[0]['findings'][0].update(invalidates_normal=['missing']))
    changed(lambda ss: ss[0]['findings'][1].update(slot_overrides={'slot-2': {'minimum': 0}}))
    for authored in malformed:
        with pytest.raises(ValueError):
            compile_authored(authored)
