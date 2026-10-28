"""The four real lessons preserve assessments and use their accepted exact state."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import pytest
from primer.curriculum import Curriculum,_validate_lesson_media,_validate_authored_lesson
from tools.algebra_openear_runtime_compatibility import before_algebra_openear_bytes
from tools.coordinate_plane_runtime_compatibility import before_coordinate_plane_bytes
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/algebra-functions-review-20261027'
IDS={'math.3.linear','math.3.slope','math.3.quadratics','math.3.polynomials'}

def digest(raw):return hashlib.sha256(raw).hexdigest()

def test_four_authored_lessons_keep_original_assessments_and_figures():
    scope=json.loads((D/'initial-scope.json').read_bytes());current=json.loads(before_coordinate_plane_bytes('data/curriculum/01-mathematics.json',(ROOT/'data/curriculum/01-mathematics.json').read_bytes()));bindings=json.loads(before_coordinate_plane_bytes('data/module-models.json',(ROOT/'data/module-models.json').read_bytes()));originals={n['id']:n for n in scope['originalNodes']};old_bindings={n['node_id']:n for n in scope['originalBindings']}
    assert set(originals)==IDS and sum(len(n['quiz'])for n in originals.values())==40
    for node in current['nodes']:
        if node['id']not in IDS:continue
        old=originals[node['id']];_validate_authored_lesson(node);_validate_lesson_media(node)
        assert {k:v for k,v in node.items()if k not in ['lesson_media','lesson','learning_outcomes']}=={k:v for k,v in old.items()if k!='lesson_media'}
        assert node['lesson_media'][0]==old['lesson_media'][0]and len(node['lesson_media'])==2 and len(node['learning_outcomes'])==6
        assert node['lesson_media'][1]['renderer']=='algebra-functions-lab'and node['lesson_media'][1]['props']=={'scenario':node['id']}
        row=next(r for r in bindings['models']if r['node_id']==node['id']);assert row['family']=='algebra-functions-'+node['id'].split('.')[-1]and row['mode']=='model';bindings['models'][bindings['models'].index(row)]=old_bindings[node['id']]
    current['nodes']=[originals.get(n['id'],n)for n in current['nodes']]
    assert digest((json.dumps(current,indent=2,ensure_ascii=False)+'\n').encode())==scope['curriculumSHA256']
    assert digest((json.dumps(bindings,indent=2,ensure_ascii=False)+'\n').encode())==scope['bindingsSHA256']


def test_unknown_or_cross_lesson_renderer_settings_rejected():
    curriculum=Curriculum()
    for id in IDS:
        n=curriculum.node(id);item=next(m for m in n['lesson_media']if m.get('renderer')=='algebra-functions-lab')
        for props in [{},{'scenario':'math.2.ratio'},{'scenario':next(x for x in IDS if x!=id)},{'scenario':id,'extra':True}]:
            bad=copy.deepcopy(n);next(m for m in bad['lesson_media']if m.get('renderer')=='algebra-functions-lab')['props']=props
            with pytest.raises(ValueError):_validate_lesson_media(bad)
        assert item['props']=={'scenario':id}


def test_recorded_independent_core_oracle_covers_current_practice_functions():
    proof=json.loads((D/'independent-core-proof.json').read_bytes());assert proof['allPassed']and proof['models']==17706 and proof['practiceCases']==9823 and proof['checks']==171549 and not proof['wholeGoalComplete']
    assert proof['sourceSHA256']==digest((ROOT/'web/algebra-functions-core.js').read_bytes())
    assert proof['oracleSHA256']==digest((ROOT/'tools/check_algebra_functions_independent.py').read_bytes())
    source=(ROOT/'primer/practice.py').read_text();functions={n.name:ast.get_source_segment(source,n)for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
    assert set(proof['practiceFunctionSHA256'])=={'g_linear_eq','g_slope','g_quadratics'}
    for name,h in proof['practiceFunctionSHA256'].items():assert digest(functions[name].encode())==h


def test_actual_reader_matches_current_source_and_linked_states():
    proof=json.loads((D/'reader/proof.json').read_bytes());assert proof['allPassed']and proof['syntheticLoopback']and not proof['productionVerified']and proof['profileAge']==15 and proof['errors']==[]
    for file,h in proof['sourceSHA256'].items():assert digest(before_coordinate_plane_bytes(file,(ROOT/file).read_bytes()))==h,file
    assert {(c['lesson'],c['width'])for c in proof['cases']}=={(id,w)for id in IDS for w in [390,1440]}
    assert sum(len(c['states'])for c in proof['cases'])==116
    assert sum(len(c['poses'])for c in proof['cases'])==56
    for c in proof['cases']:
        assert all(c[k]for k in ['originalIllustrationLoaded','assessmentsPreserved','invalidDraftPreservesBothViews','acceptedEditRetainsFocus','modelResetSynchronizesBothViews','cameraPreservesAcceptedState','keyboardHorizontalScroll'])
        for state in c['states']+c['poses']:
            assert state['linked']and state['exactPointTable']and state['distinctTicks']and not state['overflow']
            if not state['vertices']:
                assert c['lesson']=='math.3.slope' and state['state']['A']==state['state']['B']=='0'
                assert state['state']['C']in ['0','1'] and state['preset']in ['entire-plane','empty-equation']
