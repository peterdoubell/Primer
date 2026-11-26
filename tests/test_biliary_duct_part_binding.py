"""The upper part of the divided biliary duct object is bound to the one requirement its source label names."""
import json
from pathlib import Path

import pytest

from tools.anatomy_sources import bind_biliary_duct_part as tool
from tools.anatomy_sources import bind_body_reader_models as body
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second

ROOT = Path(__file__).resolve().parents[1]
PATH = 'data/radiology/radiology-asset-evidence.json'
LOWER = 'bp3d-biliary-4.3/FJ3079-common-bile.mesh.gz'


def test_the_record_is_the_one_the_tool_plans_and_states_the_division():
    review = json.loads(tool.REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(tool.EVIDENCE.read_text())['assets']}
    row, = review['accepted']
    item = assets[row['asset_id']]
    assert row['mesh'] == tool.PART and row['quote'] == 'Common hepatic duct' == item['name'] == item['geometry']['source_label']
    assert item['structure_ids'] == ['gallbladder.ducts.common_hepatic_duct'] and item['investigation_ids'] == ['ra.ultrasound-gallbladder']
    coverage = item['requirement_coverage']['gallbladder.ducts.common_hepatic_duct']
    assert coverage['extent'] == 'partial' and coverage['basis'].endswith(tool.DIVISION)
    assert 'No radiologist has reviewed the division' in coverage['basis'] and 'is not bound' in coverage['basis']
    part = item['geometry']['source_object_part']
    partition = json.loads((ROOT / tool.PARTITION).read_text())
    assert part['object'] == 'FJ3079' and part['source_object_sha256'] == partition['source']['mesh_sha256']
    assert item['sha256'] == partition['parts']['above']['delivered_file_sha256'] == item['visual_review']['sha256']
    assert item['anatomical_review']['status'] == 'pending'
    assert 'not a radiologist review' in review['reviewer']


def test_the_lower_part_and_the_other_candidates_stay_unbound_with_reasons():
    review = json.loads(tool.REVIEW.read_text())
    assets = json.loads(tool.EVIDENCE.read_text())['assets']
    assert not any(item['local_path'] == 'web/anatomy/' + LOWER for item in assets)
    reason = review['not_recorded'][LOWER]
    assert 'does not name it' in reason and 'A whole is not bound to its parts' in reason
    leaves, names, _ = body.requirement_leaves()
    shown = set(review['readers']['bp3d-biliary-4.3']['investigations'])
    # Every leaf of the reader's investigations that names the common bile duct is a part of a segment or names a segment.
    for structure_id, by_investigation in leaves.items():
        if shown & set(by_investigation) and 'common bile' in names[structure_id].lower().replace('_', ' '):
            name = names[structure_id].lower()
            assert any(word in name for word in ('supraduodenal', 'retroduodenal', 'intrapancreatic', 'intramural', 'visible segment', 'distal')), name
    assert len(review['candidates_not_bound']) == 6 and all(review['candidates_not_bound'].values())
    assert set(review['not_recorded']) | {tool.PART} == set(body.inventory(review))


def test_the_record_has_an_exact_inverse_and_the_chain_peels_it_first():
    from tools.acute_abdomen_panels_compatibility import before_acute_panel_evidence

    receipt = json.loads(tool.RECEIPT.read_text())
    raw = before_acute_panel_evidence(tool.EVIDENCE.read_bytes())
    assert second.sha(raw) == receipt['after_sha256'] and receipt['path'] == PATH
    before = tool.before_biliary_duct_part_record(raw)
    assert second.sha(before) == receipt['before_sha256'] == json.loads(body.RECEIPT.read_text())['after_sha256']
    assert tool.before_biliary_duct_part_record(before) == before
    assert tool.before_biliary_duct_part_record(raw + b'\n') == raw + b'\n'
    old, new = json.loads(before), json.loads(raw)
    assert new['assets'][:-1] == old['assets'] and new['assets'][-1]['id'] == 'bp3d-biliary-4.3-FJ3079-common-hepatic'
    assert {k: v for k, v in old.items() if k != 'assets'} == {k: v for k, v in new.items() if k != 'assets'}
    assert receipt['clinical_approval'] is False and receipt['extends_historical_approval'] is False
    assert body.before_body_reader_model_records(raw) == body.before_body_reader_model_records(before)


def test_the_tool_refuses_the_lower_part_and_a_lumen(tmp_path, monkeypatch):
    from tools.acute_abdomen_panels_compatibility import before_acute_panel_evidence

    review = json.loads(tool.REVIEW.read_text())
    receipt = json.loads(tool.RECEIPT.read_text())
    monkeypatch.setattr(tool, 'EVIDENCE', tmp_path / 'evidence.json')
    monkeypatch.setattr(body, 'EVIDENCE', tmp_path / 'evidence.json')
    (tmp_path / 'evidence.json').write_bytes(tool.before_biliary_duct_part_record((ROOT / PATH).read_bytes()))
    assert second.sha((tmp_path / 'evidence.json').read_bytes()) == receipt['before_sha256']
    made, = tool.plan()
    assert made == json.loads(before_acute_panel_evidence((ROOT / PATH).read_bytes()))['assets'][-1]
    document = tmp_path / 'review.json'
    monkeypatch.setattr(tool, 'REVIEW', document)
    row = review['accepted'][0]
    cases = [
        dict(row, structure_id='biliary.duct_common_hepatic.complete_lumen', name='Complete common_hepatic source anatomy: complete lumen',
             leaf_basis='body_part', investigations=['ra.biliary-duct-pathology']),
        dict(row, quote='Common bile duct'),
    ]
    for case in cases:
        document.write_text(json.dumps(dict(review, accepted=[case])))
        with pytest.raises(ValueError):
            tool.plan()
    lower = dict(row, mesh=LOWER, asset_id=body.asset_id(LOWER))
    document.write_text(json.dumps(dict(review, accepted=[lower])))
    with pytest.raises(ValueError, match='This pass binds one mesh'):
        tool.plan()
