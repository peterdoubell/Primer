import copy
import json
from pathlib import Path

import pytest

from primer.curriculum import Curriculum
from primer.radiology_catalog import catalogue
from tools.check_radiology_fidelity import build_scope, build_report, validate_scope, digest

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def scope():
    return build_scope()


def test_all_reference_and_curriculum_surfaces_are_retained(scope):
    assert {i['id'] for i in scope['investigations']} == {i['id'] for i in catalogue()['investigations']}
    curriculum=Curriculum()
    assert {m['id'] for m in scope['curriculum_modules']} == {n['id'] for n in curriculum.nodes.values() if n.get('domain')=='radiology'}
    assert any(m['id']=='rad.5.pet-ct' and not m['investigation_ids'] for m in scope['curriculum_modules'])
    assert any(m['id']=='img.0.shadows' for m in scope['curriculum_modules'])


@pytest.mark.parametrize('change',['missing_section','missing_module','changed_report','forged_hash','forged_inventory'])
def test_missing_or_relabelled_scope_cannot_pass(scope,change):
    saved=copy.deepcopy(scope)
    if change=='missing_section':saved['investigations']=[r for r in saved['investigations'] if r['section']!='Neuroradiology']
    elif change=='missing_module':saved['curriculum_modules'].pop()
    elif change in ('changed_report','forged_hash'):
        r=saved['investigations'][0];r['reporting_contract']['reporting']['checklist'].pop()
        if change=='forged_hash':r['reporting_contract_sha256']=digest(r['reporting_contract'])
    else:saved['investigations'][0]['structure_inventory']='invented-approval.json'
    with pytest.raises(ValueError):validate_scope(saved,scope)


def test_unexpanded_scope_is_unknown_and_includes_non_msk_media(scope):
    report=build_report(scope)
    assert report['known_representation_requirements']==69336
    assert report['msk_subaudit']['representation_requirements']==5292
    assert len(report['investigations_requiring_structure_expansion'])==68
    assert report['total_representation_requirements'] is None
    assert not report['clinical_commercial_ready']
    assert len(report['curriculum_surfaces_requiring_reconciliation'])==106
    surfaces=report['runtime_reference_image_rights']['surfaces']
    assert 'reporting:ra.appendicitis' in surfaces
    assert 'lesson:rad.5.pet-ct' in surfaces
    assert report['runtime_reference_image_rights']['counts']['images']>231


def test_saved_scope_is_current(scope):
    saved=json.loads((ROOT/'docs/radiology-fidelity-scope.json').read_text())
    validate_scope(saved,scope)
