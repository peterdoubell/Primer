"""Explicit negative assessments must remain separate from focal observations."""
import json
from pathlib import Path

import pytest

from primer.descriptor_reporting import render_descriptors

ROOT = Path(__file__).resolve().parents[1]


def authored(identifier):
    return json.loads((ROOT / 'data/radiology/anatomic-neuro.json').read_text())['investigations'][identifier]


def compiled(identifier):
    catalog = json.loads((ROOT / 'data/radiology/descriptor-reporting.json').read_text())
    return next((form, investigation) for form in catalog['forms'].values()
                for investigation in form['investigations'] if investigation['id'] == identifier)


def render(form, identifier, selections):
    return render_descriptors(form, {'investigation_id': identifier, 'selections': selections})


def test_authored_node_map_negatives_require_explicit_assessed_station_selection():
    stations = [row for row in authored('ra.cervical-lymph-nodes')['sections'] if row.get('repeatable')]
    assert len(stations) == 29
    for row in stations:
        assert row['normal'].startswith('No morphologically suspicious node is identified in the assessed ')
        assert row['exclude_from_bulk_normal'] is True
        assert row['repeat_label'] == 'Node'
        assert row['source_ids']


def test_authored_sellar_absence_is_explicit_and_regional_lesion_observations_invalidate_it():
    rows = {row['id']: row for row in authored('ra.mri-sella')['sections']}
    assert rows['anterior-gland']['normal'] == 'No focal lesion is identified in the anterior pituitary on the acquired images.'
    assert rows['sellar-lesion']['normal'] == 'No focal sellar or parasellar lesion is identified on the acquired images.'
    assert rows['sellar-lesion']['repeatable']
    for row_id, finding_id in [('hypothalamus', 'lesion'), ('optic-chiasm', 'contact'),
                               ('right-cavernous-sinus', 'extension'), ('left-cavernous-sinus', 'extension')]:
        finding = next(value for value in rows[row_id]['findings'] if value['id'] == finding_id)
        assert 'sellar-lesion' in finding['invalidates_normal']


def test_compiled_node_map_can_record_one_negative_station_and_an_independent_opposite_node():
    identifier = 'ra.cervical-lymph-nodes'
    form, _ = compiled(identifier)
    result = render(form, identifier, {
        'anatomy-right-node-iia': {'normal': True},
        'anatomy-left-node-iia': {'instances': [{'findings': {
            identifier + ':left-node-iia:node': {},
            identifier + ':left-node-iia:morphology': {'slot-1': 'centrally necrotic'},
        }}]},
    })
    assert result['valid'], result['issues']
    assert 'No morphologically suspicious node is identified in the assessed right level IIa' in result['text']
    assert 'left level IIa' in result['text'] and 'centrally necrotic' in result['text']
    assert 'assessed left level IIa' not in result['text']


@pytest.mark.parametrize(('identifier', 'section', 'finding', 'values'), [
    ('ra.cervical-lymph-nodes', 'right-node-iia', 'node', {}),
    ('ra.mri-sella', 'sellar-lesion', 'lesion', {'slot-1': 'right pituitary'}),
])
def test_negative_parent_and_positive_record_cannot_be_copied_together(identifier, section, finding, values):
    form, _ = compiled(identifier)
    result = render(form, identifier, {'anatomy-' + section: {
        'normal': True, 'instances': [{'findings': {identifier + ':' + section + ':' + finding: values}}],
    }})
    assert not result['valid'] and result['text'] == ''


def test_compiled_sellar_parent_negative_copies_explicitly_but_never_from_an_empty_report():
    identifier = 'ra.mri-sella'
    form, _ = compiled(identifier)
    assert render(form, identifier, {})['text'] == ''
    result = render(form, identifier, {'anatomy-sellar-lesion': {'normal': True}})
    assert result['valid'] and 'No focal sellar or parasellar lesion is identified' in result['text']
    result = render(form, identifier, {
        'anatomy-sellar-lesion': {'normal': True},
        'anatomy-hypothalamus': {'findings': {identifier + ':hypothalamus:lesion': {'slot-1': 'solid'}}},
    })
    assert not result['valid'] and result['text'] == ''
    assert 'conflicting_anatomic_normal' in {issue['code'] for issue in result['issues']}
