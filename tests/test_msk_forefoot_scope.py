"""Conditional forefoot detail cannot remove existing infection scope or imply approval."""
import hashlib
import json
from pathlib import Path

from tools.check_msk_fidelity import audit, requirements_for

ROOT = Path(__file__).resolve().parents[1]


def test_forefoot_additions_preserve_the_original_specification_and_report():
    requirements = json.loads((ROOT / 'data/radiology/msk-structure-requirements.json').read_text())
    proposal = json.loads((ROOT / 'docs/msk-diabetic-foot-forefoot-requirements-proposal.json').read_text())
    foot = next(i for i in requirements['investigations'] if i['investigation_id'] == 'ra.mri-diabetic-foot')
    reconciliation = foot['forefoot_scope_reconciliation']
    assert foot['reporting_checklist'] == proposal['existing_reporting_checklist']
    assert foot['reporting_template_sections'] == proposal['existing_reporting_template_sections']
    original = foot['structures'][:48]
    assert hashlib.sha256(json.dumps(original, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == reconciliation['preserved_original_structures_sha256']
    assert sum(len(s.get('required_parts') or [s]) for s in original) == 203
    additions = foot['structures'][48:]
    assert {s['id'] for s in additions} == {s['id'] for s in proposal['proposed_structures']}
    assert len(additions) == 9 and sum(len(s['required_parts']) for s in additions) == 44
    assert len(requirements_for(foot)) == 247
    for structure in additions:
        assert structure['requires_site_instantiation']
        assert structure['modality_scope'] == ['MRI']
        assert structure['clinical_validation_status'] != 'approved'
        assert structure['required_site_ids']
        for reference in structure['report_refs']:
            actual = foot['reporting_checklist'][reference['checklist_index']]
            assert reference['label'] == actual['label'] and reference['detail'] == actual['detail']
    assert len(foot['expansion_rules'][0]['named_sites_or_targets']) == 14
    assert all(rule['status'] != 'approved' for rule in foot['expansion_rules'])
    result = audit(requirements, {'assets': []})
    assert 'ra.mri-diabetic-foot: site expansion unverified' in result['scope_gaps']
    assert not result['clinical_commercial_ready']


def test_continuous_hallux_tissue_and_fdb_attachment_distinctions_remain_explicit():
    requirements = json.loads((ROOT / 'data/radiology/msk-structure-requirements.json').read_text())
    foot = next(i for i in requirements['investigations'] if i['investigation_id'] == 'ra.mri-diabetic-foot')
    parts = {p['id']: p for s in foot['structures'] for p in s.get('required_parts', [])}
    capsule = parts['diabetic_foot.hallux_plantar_capsulosesamoid_complex.plantar_capsule']
    assert 'continuous' in capsule['name']
    assert 'not an independently separable layer' in capsule['definition']
    for side in ('medial', 'lateral'):
        slip = parts['diabetic_foot.flexor_digitorum_brevis_tendons.' + side + '_distal_slip']
        assert side + ' side of the middle-phalangeal shaft' in slip['name']
