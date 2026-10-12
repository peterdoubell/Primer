"""Historical comparison removes one exact addition, retaining every other guard."""
import copy
import json
from pathlib import Path
import pytest
from tools import pulmonary_data_compatibility as bridge
from tools.anatomy_sources import integrate_traumatic_haemorrhage_sources as trauma


def observed(path):
    raw=(bridge.ROOT/path).read_bytes()
    return raw,json.loads(raw),trauma.unrelated_tokens(raw.decode(),Path(path),set())


@pytest.mark.parametrize('path',sorted(bridge.PATHS))
def test_exact_current_raw_restores_original_main_fingerprint(path):
    raw=(bridge.ROOT/path).read_bytes();restored=bridge.restore_main_raw(path,raw)
    assert bridge.sha(restored)==bridge.reviewed()['files'][path]['main_sha256']
    assert bridge.restore_main_raw(path,restored)==restored


@pytest.mark.parametrize('path',sorted(bridge.PATHS))
def test_even_semantically_identical_unreviewed_raw_bytes_are_rejected(path):
    raw=(bridge.ROOT/path).read_bytes()
    with pytest.raises(ValueError,match='raw-token'):bridge.restore_main_raw(path,raw+b'\n')


@pytest.mark.parametrize('path',[bridge.REQUIREMENTS,bridge.OVERRIDE])
def test_changed_scoped_semantics_or_raw_token_is_rejected(path):
    _,data,tokens=observed(path);bad=copy.deepcopy(data)
    row=next(v for v in bad['investigations'] if v['investigation_id']==bridge.CASE) if path==bridge.REQUIREMENTS else bad[bridge.CASE]
    row['unreviewed_claim']=True
    with pytest.raises(ValueError,match='scoped semantics'):bridge.restore_prior_view(path,bad,tokens)
    record=bridge.reviewed()['files'][path]['scoped_records']['investigation']
    key=next(k for k in record['token_keys'] if k in tokens);tokens[key]='0'*64
    with pytest.raises(ValueError,match='raw value token'):bridge.restore_prior_view(path,data,tokens)


def test_duplicate_scope_and_ambiguous_namespace_are_rejected():
    _,data,tokens=observed(bridge.REQUIREMENTS);data['scope']['catalog_investigation_ids'].append(bridge.CASE)
    with pytest.raises(ValueError,match='duplicated'):bridge.restore_prior_view(bridge.REQUIREMENTS,data,tokens)
    _,data,tokens=observed(bridge.REQUIREMENTS);record=bridge.reviewed()['files'][bridge.REQUIREMENTS]['scoped_records']['catalog']
    for key in record['token_keys']:tokens[key]=record['raw_value_token_sha256']
    with pytest.raises(ValueError,match='ambiguous'):bridge.restore_prior_view(bridge.REQUIREMENTS,data,tokens)


def test_unrelated_semantic_and_raw_token_drift_is_preserved_for_original_guard():
    _,data,tokens=observed(bridge.REQUIREMENTS);other=next(v for v in data['investigations'] if v['investigation_id']!=bridge.CASE)
    other['unreviewed_claim']='must remain visible';key='investigations:'+other['investigation_id'];tokens[key]='f'*64
    before=copy.deepcopy(data);restored,old=bridge.restore_prior_view(bridge.REQUIREMENTS,data,tokens)
    assert data==before and tokens[key]=='f'*64
    assert next(v for v in restored['investigations'] if v['investigation_id']==other['investigation_id'])==other
    assert old[key]=='f'*64 and all(v['investigation_id']!=bridge.CASE for v in restored['investigations'])


def test_unknown_paths_do_not_receive_a_comparison_waiver():
    data={'unexpected':True};tokens={'unknown':'f'*64}
    assert bridge.restore_prior_view('unknown.json',data,tokens)==(data,tokens)
    assert bridge.restore_main_raw('unknown.json',b'unreviewed')==b'unreviewed'


def test_contract_restoration_keeps_unrelated_drift_and_rejects_changed_pulmonary():
    record=bridge.reviewed()['nonstroke_contract'];contracts={bridge.CASE:record['current_sha256'],'unknown':'f'*64}
    assert bridge.restore_prior_contracts(contracts)=={bridge.CASE:record['prior_sha256'],'unknown':'f'*64}
    contracts[bridge.CASE]='0'*64
    with pytest.raises(ValueError,match='effective contract'):bridge.restore_prior_contracts(contracts)


def test_mutated_amendment_evidence_is_rejected(tmp_path,monkeypatch):
    raw=(bridge.ROOT/bridge.PROOF).read_bytes();p=tmp_path/bridge.PROOF;p.parent.mkdir(parents=True);p.write_bytes(raw+b'\n')
    monkeypatch.setattr(bridge,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='fingerprint'):bridge.reviewed()
