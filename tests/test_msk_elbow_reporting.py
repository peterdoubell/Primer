"""Elbow origin/insertion wording and existing brachialis scope stay consistent."""
import hashlib
import json
from pathlib import Path

import pytest

from primer import radiology_catalog
from primer.curriculum import Curriculum
from tools.check_msk_fidelity import validate_reporting_snapshots


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def elbow():
    reference = radiology_catalog.detail(
        Curriculum(), radiology_catalog.resolve('ra.mri-elbow'))['radiology_reference']
    requirements = json.loads((ROOT / 'data/radiology/msk-structure-requirements.json').read_text())
    investigation = next(item for item in requirements['investigations']
                         if item['investigation_id'] == 'ra.mri-elbow')
    return reference, investigation


def test_elbow_tendons_distinguish_common_origins_and_include_existing_brachialis(elbow):
    reference, _ = elbow
    detail = reference['reporting']['checklist'][0]['detail'].lower()
    assert 'common flexor/extensor origins at the epicondyles' in detail
    assert all(name in detail for name in ('distal biceps', 'brachialis', 'triceps'))
    assert 'covered course and bony attachments' in detail
    sections = [reference['reporting']['template_sections']]
    sections += [template['sections'] for template in reference['report_templates']]
    for group in sections:
        tendon = next(section['body'].lower() for section in group
                      if section['heading'] == 'TENDONS')
        assert 'common extensor origin' in tendon
        assert 'common flexor origin' in tendon
        assert 'brachialis [ ]' in tendon
        assert 'lacertus fibrosus' in tendon


def test_distal_biceps_coverage_limitation_is_explicit(elbow):
    reference, _ = elbow
    protocol = ' '.join(reference['reporting']['protocol']).lower()
    assert 'radial tuberosity in axial coverage' in protocol
    assert 'state if the insertion is not covered' in protocol


def test_elbow_live_report_and_all_structure_references_agree(elbow):
    reference, investigation = elbow
    guide = reference['reporting']
    validate_reporting_snapshots({'investigations': [investigation]}, {'ra.mri-elbow': guide})
    digest = hashlib.sha256(json.dumps(guide['checklist'], sort_keys=True,
                                      separators=(',', ':')).encode()).hexdigest()
    assert investigation['reporting_checklist_sha256'] == digest
    assert len(guide['checklist']) == len(guide['template_sections']) == 5


def test_wording_correction_preserves_every_elbow_anatomical_requirement(elbow):
    _, investigation = elbow
    structures = investigation['structures']
    assert len(structures) == 38
    assert sum(len(s['required_parts']) for s in structures) == 83
    # Captured before the reporting-only correction. This includes every ID,
    # name, tissue class, modality, condition, source URL and component record.
    scope = [{k: v for k, v in s.items() if k != 'report_refs'} for s in structures]
    digest = hashlib.sha256(json.dumps(scope, sort_keys=True, separators=(',', ':'),
                                      ensure_ascii=False).encode()).hexdigest()
    assert digest == 'a159ef175d02aa323c240dea2ac20203fdbd8163c93346167e824d00ae9d3f06'
    assert investigation['clinical_validation_status'] == 'draft_requires_msk_radiologist_review'
    lucl = next(s for s in structures if s['id'] == 'elbow.lateral_ulnar_collateral_ligament')
    assert lucl['tissue_class'] == 'ligament'
    assert {p['id'] for p in lucl['required_parts']} == {
        'elbow.lateral_ulnar_collateral_ligament.attachments',
        'elbow.lateral_ulnar_collateral_ligament.complete_course',
    }
