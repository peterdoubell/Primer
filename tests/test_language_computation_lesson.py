"""Actual language algorithms, calculated diagrams and ephemeral practice feedback."""
from pathlib import Path
import copy,hashlib,json,subprocess,sys
import pytest
from primer.curriculum import Curriculum,_validate_lesson_media
from tools.language_computation_runtime_compatibility import before_language_computation_bytes,reviewed
R=Path(__file__).resolve().parents[1];D=R/'docs/language-computation-review-20261104'

def test_authored_scope_and_original_context_are_preserved():
    path='data/curriculum/02-language.json';raw=(R/path).read_bytes();now=json.loads(raw);old=json.loads(before_language_computation_bytes(path,raw))
    assert len(now['nodes'])==len(old['nodes'])==40
    for current,previous in zip(now['nodes'],old['nodes']):
        if current['id']!='lang.5.comp-ling':assert current==previous;continue
        assert {k:v for k,v in current.items()if k!='lesson_media'}=={k:v for k,v in previous.items()if k!='lesson_media'}
        assert current['lesson_media'][:-1]==previous['lesson_media']
        assert current['lesson_media'][-1]['props']=={'scenario':'lang.5.comp-ling'}
    node=Curriculum().node('lang.5.comp-ling');assert len(node['quiz'])==10
    models=[m for m in node['lesson_media']if m['kind']=='model'];assert [m['renderer']for m in models]==['language-computation-lab','spatial-3d']
    assert models[1]['props']['family']=='computer'and models[1]['props']['mode']=='context'

@pytest.mark.parametrize('mutation',['node','scenario','extra'])
def test_binding_rejects_foreign_lessons_or_settings(mutation):
    n=copy.deepcopy(Curriculum().node('lang.5.comp-ling'));studio=next(m for m in n['lesson_media']if m.get('renderer')=='language-computation-lab')
    if mutation=='node':n['id']='lang.4.linguistics'
    elif mutation=='scenario':studio['props']['scenario']='lang.4.linguistics'
    else:studio['props']['extra']=True
    with pytest.raises(ValueError):_validate_lesson_media(n)

def test_shipped_core_against_independent_earley_oracles_and_fractions(tmp_path):
    out=tmp_path/'proof.json';p=subprocess.run([sys.executable,str(R/'tools/check_language_computation_core.py'),'--output',str(out)],cwd=R,capture_output=True,text=True,timeout=30)
    assert p.returncode==0,p.stdout+p.stderr
    r=json.loads(out.read_bytes());assert r['allPassed']and r['sentenceCases']==71 and r['completeTreesCompared']==156
    assert r['invalidInputsRejected']==20
    assert r['independentChartSymbolStates']==6728 and r['exactProbabilityEntries']==384 and r['confusionMatrices']==691
    assert r['sourceSHA256']==hashlib.sha256((R/'web/language-computation-core.js').read_bytes()).hexdigest()

def test_actual_reader_calculated_geometry_and_practice_lifecycle():
    r=json.loads((D/'reader/browser-proof.json').read_bytes());g=json.loads((D/'reader/rendered-proof.json').read_bytes())
    assert r['allPassed']and r['authenticatedSyntheticApp']and not r['productionLearnerWrites']and r['errors']==[]
    assert r['parserCases']==20 and r['probabilityCases']==96 and r['evaluationCases']==10 and r['ambiguityCases']==10
    assert r['practiceFeedbackChecks']==228 and r['independentMounts']==4 and r['routeReopenChecks']==2
    for name,digest in r['sourceSHA256'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
    assert g['allPassed']and g['renderedChartCells']==722 and g['renderedTreeNodes']==392 and g['renderedTreeEdges']==376
    assert g['renderedProbabilityCells']==768 and g['renderedProbabilityBars']==704 and g['renderedTransitionEdges']==544 and g['renderedMetricBars']==16

def test_exact_historical_projection_rejects_unreviewed_bytes():
    for name,row in reviewed()['files'].items():
        raw=(R/name).read_bytes();assert hashlib.sha256(before_language_computation_bytes(name,raw)).hexdigest()==row['before_sha256']
        with pytest.raises(ValueError):before_language_computation_bytes(name,raw+b'foreign')
