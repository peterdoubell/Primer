"""Source-panel and injury-context boundaries for the new knee references."""
import copy
import json
from pathlib import Path

import pytest

from tools.check_msk_fidelity import inspect_asset, inspect_binding, requirements_for, review_scope_fingerprint


ROOT = Path(__file__).resolve().parents[1]
NEW_IDS = (
    'open-knee-mcl-layers-bolog-fig14',
    'open-knee-anterior-meniscofemoral-bolog-fig18',
    'open-knee-posterior-meniscofemoral-bolog-fig19',
    'open-knee-plc-anatomy-wu-fig1',
    'open-knee-plc-anatomy-wu-fig1-schematic-panels',
    'open-knee-popliteofibular-mri-wu-fig4',
    'open-knee-medial-posterior-root-mri-ssr-fig2a',
)


def records():
    requirements = json.loads((ROOT / 'data/radiology/msk-structure-requirements.json').read_text())
    investigation = next(i for i in requirements['investigations'] if i['investigation_id'] == 'ra.mri-knee')
    leaves = {r['id']: r for r in requirements_for(investigation)}
    assets = json.loads((ROOT / 'data/radiology/msk-asset-evidence.json').read_text())['assets']
    return requirements, leaves, {a['id']: a for a in assets}


def test_plc_composite_cannot_swap_cadaver_or_schematic_for_mri():
    _, leaves, assets = records()
    clinical = assets['open-knee-plc-anatomy-wu-fig1']
    schematic = assets['open-knee-plc-anatomy-wu-fig1-schematic-panels']
    target = leaves['knee.popliteofibular_ligament.course']
    assert clinical['structure_ids'] == []
    assert clinical['source_context']['selected_panels'] == ['b']
    assert schematic['source_context']['selected_panels'] == ['c', 'd']
    assert schematic['modality'] == 'Schematic'
    for panel in ['a', 'c']:
        changed = copy.deepcopy(clinical)
        changed['source_context']['selected_panels'] = [panel]
        changed['representation_selection']['panels'] = [panel]
        assert 'source_context_selected_panel_not_clinical_image' in inspect_binding(changed, target)


def test_normal_root_candidate_does_not_claim_a_normal_whole_knee_or_child_mri():
    _, leaves, assets = records()
    asset = assets['open-knee-medial-posterior-root-mri-ssr-fig2a']
    context = asset['source_context']
    assert context['depicted_state'] == 'normal_root_in_acl_injured_knee'
    assert context['population']['age_years'] == 22
    assert context['selected_panels'] == ['a']
    assert asset['structure_ids'] == ['knee.medial_meniscus.posterior_root']
    normal_exam = copy.deepcopy(leaves[asset['structure_ids'][0]])
    normal_exam['context_requirements'] = [{'depicted_state': 'normal_anatomy'}]
    assert 'source_context_depicted_state_mismatch' in inspect_binding(asset, normal_exam)


def test_pfl_evidence_selects_only_its_marked_panel():
    _, _, assets = records()
    asset = assets['open-knee-popliteofibular-mri-wu-fig4']
    assert asset['source_context']['selected_panels'] == ['a']
    assert asset['representation_selection']['panels'] == ['a']
    assert not any('Fabellofibular' in name for name in asset['structures_observed'])
    assert not any(target.endswith('.attachments') for target in asset['structure_ids'])


@pytest.mark.parametrize('identifier', NEW_IDS)
def test_knee_source_reconciliation_cannot_establish_clinical_approval(identifier):
    requirements, leaves, assets = records()
    asset = assets[identifier]
    for target in asset['structure_ids']:
        assert not inspect_binding(asset, leaves[target])
    issues = inspect_asset(asset, ROOT, review_scope_fingerprint(asset, requirements))
    assert 'asset_fingerprint_mismatch' not in issues
    assert 'commercial_rights_unverified' not in issues
    assert 'high_fidelity_unproven' in issues
    assert 'anatomical_review_missing_or_stale' in issues
    assert asset['anatomical_review']['status'] == 'pending'
