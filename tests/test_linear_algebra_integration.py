"""Bounded linear-algebra binding, exact assessment change and historical views."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from primer.curriculum import Curriculum, _validate_lesson_media
from primer.quiz import score_quiz
from tools import linear_algebra_runtime_compatibility as bridge

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/linear-algebra-fidelity-review-20261016/integration'


def authored():
    data=json.loads((ROOT/bridge.MATH).read_bytes())
    return data,next(node for node in data['nodes'] if node['id']==bridge.MODULE)


def test_exact_quiz8_and_single_companion_preserve_other_authored_material():
    proof=bridge.reviewed();data,node=authored()
    prior=json.loads(bridge.before_linear_algebra_bytes(bridge.MATH,(ROOT/bridge.MATH).read_bytes()))
    original=next(n for n in prior['nodes'] if n['id']==bridge.MODULE)
    assert node['quiz'][8]==proof['after_quiz'] and original['quiz'][8]==proof['before_quiz']
    assert len(node['quiz'])==10 and all(node['quiz'][i]==original['quiz'][i] for i in range(10) if i!=8)
    assert node['lesson_media']==original['lesson_media']+[proof['added_media']]
    restored=copy.deepcopy(data);restored['nodes'][42]['quiz'][8]=proof['before_quiz'];restored['nodes'][42]['lesson_media'].pop()
    assert restored==prior
    assert score_quiz(node['quiz'],[q['answer'] for q in node['quiz']])=={'right':10.,'total':10,'score':1.}
    for choice in node['quiz'][8]['choices']:
        result=score_quiz([node['quiz'][8]],[choice])
        assert result['score']==(1. if choice==node['quiz'][8]['answer'] else 0.)
    assert score_quiz([node['quiz'][8]],[proof['before_quiz']['answer']])['score']==0.


def test_renderer_is_narrow_and_old_five_map_and_plate_metadata_remain():
    _,node=authored();media=bridge.reviewed()['added_media']
    _validate_lesson_media(node)
    assert [m['renderer'] for m in node['lesson_media'] if m['kind']=='model']==['matrix-transform-lab','linear-algebra-lab']
    assert node['lesson_media'][0]['id']=='determinant-area-collapse-plate'
    assert node['lesson_media'][1]['props']=={'start_transform':'x-shear'}
    for patch in [{'id':'math.4.analysis'}, {'props':{'scenario':'math.4.analysis'}}, {'props':{'scenario':'math.4.linalg','extra':True}}]:
        changed=copy.deepcopy(node)
        if 'id' in patch:changed['id']=patch['id']
        else:changed['lesson_media'][-1]['props']=patch['props']
        with pytest.raises(ValueError,match='linear algebra lab'):_validate_lesson_media(changed)
    assert sum(m.get('renderer')=='linear-algebra-lab' for n in Curriculum().nodes.values() for m in n['lesson_media'])==1


@pytest.mark.parametrize('path',sorted(bridge.PATHS))
def test_exact_shared_byte_inverse_rejects_unreviewed_changes(path):
    from tools.structured_reporting_runtime_compatibility import before_structured_bytes
    raw=before_structured_bytes(path, (ROOT/path).read_bytes());row=bridge.reviewed()['files'][path]
    assert hashlib.sha256(raw).hexdigest()==row['after_sha256']
    prior=bridge.before_linear_algebra_bytes(path,raw)
    assert hashlib.sha256(prior).hexdigest()==row['before_sha256']
    assert bridge.before_linear_algebra_bytes(path,prior)==prior
    with pytest.raises(ValueError,match='Unreviewed'):
        bridge.before_linear_algebra_bytes(path,raw+b'\n# unrelated drift\n')


def test_lesson_semantic_inverse_requires_exact_reviewed_values():
    node=Curriculum().node(bridge.MODULE)
    previous=bridge.before_linear_algebra_lesson_fields(bridge.MODULE,node)
    assert all(m.get('renderer')!='linear-algebra-lab' for m in previous['lesson_media'])
    assert {k:v for k,v in previous['quiz'][8].items() if k!='ephemeral'}==bridge.reviewed()['before_quiz']
    assert bridge.before_linear_algebra_lesson_fields(bridge.MODULE,previous)==previous
    for kind in ['duplicate','metadata','quiz','ephemeral']:
        changed=copy.deepcopy(node)
        media=next(m for m in changed['lesson_media'] if m.get('renderer')=='linear-algebra-lab')
        if kind=='duplicate':changed['lesson_media'].append(copy.deepcopy(media))
        elif kind=='metadata':media['instructions']+=' Unreviewed scope.'
        elif kind=='quiz':changed['quiz'][8]['explain']+=' Unreviewed claim.'
        else:changed['quiz'][8]['ephemeral']=0
        with pytest.raises(ValueError,match='Unreviewed'):
            bridge.before_linear_algebra_lesson_fields(bridge.MODULE,changed)


def test_all_stage4_duration_effects_follow_only_the_exact_quiz_counterfactual(tmp_path,monkeypatch):
    import primer.curriculum as curriculum
    current,prior=bridge.duration_counterfactual();proof=bridge.reviewed()['derived_duration']
    assert current['pool_count']==prior['pool_count']==84
    assert current['pool_character_sum']==307230 and prior['pool_character_sum']==306909
    assert len(proof['changed_minutes'])==34
    now=Curriculum();corpus=bridge.source_corpus()
    for path,raw in corpus.items():
        (tmp_path/Path(path).name).write_bytes(bridge.before_linear_algebra_bytes(path,raw))
    monkeypatch.setattr(curriculum,'CURRICULUM_DIR',str(tmp_path));before=Curriculum()
    for row in current['rows']:
        ident=row['id'];old=next(r for r in prior['rows'] if r['id']==ident)
        assert now.node(ident)['minutes']==row['minutes'] and before.node(ident)['minutes']==old['minutes']
        assert bridge.semantic(now.node(ident))==proof['lesson_semantics'][ident]['current_sha256']
        assert bridge.semantic(before.node(ident))==proof['lesson_semantics'][ident]['before_sha256']
    for ident in [bridge.MODULE,'math.4.numtheory','math.4.multivar','phys.4.classical']:
        original=copy.deepcopy(now.node(ident))
        assert bridge.before_linear_algebra_duration_fields(original)==before.node(ident)
        assert original==now.node(ident)
    assert now.node('math.4.numtheory')['minutes']==before.node('math.4.numtheory')['minutes']==1075


@pytest.mark.parametrize('mutation',['unrelated_corpus','quiz_change','unrecorded_minutes','other_node_field'])
def test_counterfactual_rejects_unreviewed_duration_inputs(mutation):
    if mutation in {'unrelated_corpus','quiz_change'}:
        corpus=bridge.source_corpus();path=bridge.MATH if mutation=='quiz_change' else 'data/curriculum/03-physics.json'
        corpus[path]+=b'\n'
        with pytest.raises(ValueError,match='Unreviewed'):bridge.duration_counterfactual(corpus)
    else:
        node=copy.deepcopy(Curriculum().node('math.4.numtheory'))
        if mutation=='unrecorded_minutes':node['minutes']+=5
        else:node['goal']+=' Unreviewed.'
        with pytest.raises(ValueError,match='Unreviewed'):bridge.before_linear_algebra_duration_fields(node)


def test_lesson_API_preserves_assessment_privacy_with_synthetic_storage(tmp_path):
    env={key:value for key,value in os.environ.items() if not key.startswith(('TURSO','PRIMER_ACCESS_','VERCEL','BLOB_'))}
    env.update(TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',PRIMER_DB=str(tmp_path/'reader.db'),PRIMER_CONTENT_DIR=str(tmp_path/'content'),PRIMER_BACKUP_DIR=str(tmp_path/'backups'))
    script='''
import json
from pathlib import Path
from fastapi.testclient import TestClient
import primer.server as server
source=json.loads(Path('data/curriculum/01-mathematics.json').read_text())
authored=next(n for n in source['nodes'] if n['id']=='math.4.linalg')
with TestClient(server.app) as client:
 response=client.get('/api/curriculum/node/math.4.linalg');assert response.status_code==200
 node=response.json();node=node.get('node',node)
 assert node['id']=='math.4.linalg' and node['question_count']==10 and 'quiz' not in node
 for item in authored['lesson_media']:assert next(m for m in node['lesson_media'] if m['id']==item['id'])==item
 serialized=json.dumps(node)
 for question in authored['quiz']:
  assert question['prompt'] not in serialized and question['explain'] not in serialized
print('linear algebra lesson metadata and private assessment fields verified')
'''
    result=subprocess.run([sys.executable,'-B','-c',script],cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
    assert result.returncode==0,result.stdout+result.stderr
