"""The lobe case retains its source role beside the independent LIDC example."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from primer.curriculum import Curriculum
from primer import pulmonary_lobe_reference as lobes
from primer import pulmonary_native_inspectors as nodules
from primer import source_native_inspectors as combined
from primer.radiology_catalog import detail, resolve
from tools.pulmonary_lobe_runtime_compatibility import (
    before_pulmonary_lobe_lesson_fields, before_pulmonary_lobe_reference_fields,
)

ROOT = Path(__file__).resolve().parents[1]


def test_both_cases_reach_the_current_report_and_lesson_without_changing_lidc():
    curriculum = Curriculum()
    reference = detail(curriculum, resolve(lobes.CASE))['radiology_reference']
    expected = nodules.references()[lobes.CASE]
    assert reference['source_native_inspectors'] == [*expected, *lobes.references()[lobes.CASE]]
    assert reference['source_native_inspectors'][0] == expected[0]
    assert reference['key_images'] == [] and reference['source_native_only']
    lesson = curriculum.node(lobes.NODE)
    model, = [row for row in lesson['lesson_media'] if row.get('renderer') == 'radiology-anatomy']
    assert model['props']['native_inspectors'] == reference['source_native_inspectors']
    assert before_pulmonary_lobe_reference_fields(lobes.CASE, reference)['source_native_inspectors'] == expected
    historical = before_pulmonary_lobe_lesson_fields(lobes.NODE, lesson)
    prior_model, = [row for row in historical['lesson_media'] if row.get('renderer') == 'radiology-anatomy']
    assert prior_model['props']['native_inspectors'] == expected
    assert before_pulmonary_lobe_reference_fields('ra.thoracic-ultrasound', reference) is reference


def test_source_roles_name_only_the_five_lobe_bodies_and_leave_stronger_parts_unbound():
    item, = lobes.references()[lobes.CASE]
    manifest = json.loads((ROOT / 'web/anatomy/totalseg-s0028-lungs/viewer-manifest.json').read_bytes())
    source_labels = {part['id'] for part in manifest['parts']}
    roles = item['named_lobe_examples']
    assert {row['source_label'] for row in roles} == source_labels
    assert all(row['extent'] == 'partial' and row['evidence_role'] == 'source-labelled lobe body' for row in roles)
    assert all('.part-' not in row['requirement_parent_id'] for row in roles)
    assert item['structure_coverage_granted'] is False
    review = json.loads((ROOT / 'docs/pulmonary-lobe-context-20261119/source-role-review.json').read_text())
    assert len(review['lobe_examples']) == 5 and review['ledger_leaf_bindings_added'] == 0
    assert review['full_extent_leaves_bound'] is False and review['source_case_registered_to_LIDC'] is False
    assert review['source_triangles'] == 351784
    assert sum(len(row['required_leaves_retained_unbound']) for row in review['lobe_examples']) == 40


@pytest.mark.parametrize('mutation', ['caption', 'duplicate', 'coverage'])
def test_historical_projection_rejects_unreviewed_lobe_source_descriptors(mutation):
    source = deepcopy(lobes.references()[lobes.CASE])
    if mutation == 'caption':
        source[0]['caption'] += ' Added anatomical approval.'
    elif mutation == 'duplicate':
        source.append(deepcopy(source[0]))
    else:
        source[0]['structure_coverage_granted'] = True
    with pytest.raises(ValueError, match='Unreviewed pulmonary lobe'):
        before_pulmonary_lobe_reference_fields(lobes.CASE, {'source_native_inspectors': source})


def test_other_native_reference_bindings_remain_the_same():
    refs = combined.references()
    assert len(refs['ra.thoracic-ultrasound']) == 6
    assert all(row['id'] != 'totalseg-s0028-lung-native' for row in refs['ra.ct-lung-cancer'])
