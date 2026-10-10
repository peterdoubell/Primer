import copy
import json
from pathlib import Path
import pytest
from tools.build_msk_review_queue import export_queue
ROOT=Path(__file__).resolve().parents[1]


def inputs():
    return [json.loads((ROOT/p).read_text()) for p in (
        'docs/cervical-cancer-source-review/current-msk-audit.json',
        'data/radiology/msk-structure-requirements.json',
        'data/radiology/msk-asset-evidence.json')]


def test_every_requirement_and_candidate_is_in_the_review_queue(tmp_path):
    report,requirements,evidence=inputs()
    result=export_queue(report,requirements,evidence,tmp_path)
    assert sum(f['requirements'] for f in result['files'])==report['representation_requirements']==5292
    assert len(result['files'])==22
    for item in result['files']:
        text=(tmp_path/item['file']).read_text()
        rows=[r for r in report['requirements'] if r['investigation_id']==item['investigation_id']]
        for row in rows:
            assert row['structure_id'] in text
            for candidate in row['candidates']:
                assert candidate in text
                assert report['review_scope_sha256'][candidate] in text
    assert not result['clinical_commercial_ready']


@pytest.mark.parametrize('change', ['missing_row','duplicate_row','stale_claim','counts'])
def test_incomplete_or_stale_inputs_cannot_be_exported(tmp_path,change):
    report,requirements,evidence=inputs()
    if change=='missing_row':report['requirements'].pop()
    if change=='duplicate_row':report['requirements'].append(copy.deepcopy(report['requirements'][0]))
    if change=='stale_claim':evidence['assets'][0]['limitations']='Changed after review'
    if change=='counts':report['counts']['verified']+=1
    with pytest.raises(ValueError):export_queue(report,requirements,evidence,tmp_path)


def test_candidate_bytes_are_checked_not_just_claims(tmp_path):
    import hashlib
    from tools.build_msk_review_queue import candidate_artifacts
    path=tmp_path/'mesh.bin'
    path.write_bytes(b'original synthetic mesh')
    asset={'id':'fixture','local_path':'mesh.bin','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    report={'requirements':[{'candidates':{'fixture':[]}}, {'candidates':{'fixture':[]}}]}
    assert len(candidate_artifacts(report,{'fixture':asset},tmp_path))==1
    path.write_bytes(b'different bytes; metadata unchanged')
    with pytest.raises(ValueError,match='artifact changed'):
        candidate_artifacts(report,{'fixture':asset},tmp_path)
    path.unlink()
    with pytest.raises(ValueError,match='artifact missing'):
        candidate_artifacts(report,{'fixture':asset},tmp_path)


def test_candidate_paths_cannot_escape_project(tmp_path):
    from tools.build_msk_review_queue import candidate_artifacts
    report={'requirements':[{'candidates':{'fixture':[]}}]}
    with pytest.raises(ValueError,match='outside project'):
        candidate_artifacts(report,{'fixture':{'local_path':'../outside.bin','sha256':'unused'}},tmp_path)


def test_exact_rights_and_attribution_travel_with_every_candidate(tmp_path):
    report,requirements,evidence=inputs()
    export_queue(report,requirements,evidence,tmp_path)
    assets={a['id']:a for a in evidence['assets']}
    for row in report['requirements']:
        text=(tmp_path/(row['investigation_id']+'.md')).read_text()
        for identifier in row['candidates']:
            info=assets[identifier].get('source',{}).get('license',{})
            assert '- Licence: ['+info.get('name','Not recorded')+']' in text
            assert info.get('url','') in text
            attribution=info.get('attribution','Not recorded').replace('|','\\|').replace('\n',' ')
            assert '- Attribution: '+attribution in text
            assert '- Rights evidence: '+info.get('evidence_path','Not recorded') in text
    hip=(tmp_path/'ra.hip-fai.md').read_text()
    assert 'CC BY 2.0' in hip and 'CC BY 4.0' in hip
    knee=(tmp_path/'ra.mri-knee.md').read_text()
    assert 'CC BY-ND 4.0' in knee
