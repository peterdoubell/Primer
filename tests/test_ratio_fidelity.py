"""Exact quantity, geometry, reader and lesson-scope requirements for ratios."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
import pytest
from primer.curriculum import _validate_authored_lesson,_validate_lesson_media
from tools import ratio_runtime_compatibility as bridge
from tools.base_ten_runtime_compatibility import before_base_ten_bytes
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/ratio-fidelity-review-20261027'
@pytest.mark.parametrize('name',['core','spatial'])
def test_independent_ratio_oracle(name):
 r=subprocess.run([sys.executable,str(ROOT/f'tools/check_ratio_{name}.py')],cwd=ROOT,text=True,capture_output=True,timeout=120);assert r.returncode==0,r.stdout+r.stderr;p=json.loads(r.stdout);assert p['allPassed']and not p['wholeGoalComplete']
 if name=='core':assert p['cases']==2408 and p['exactQuantityChecks']==9222 and p['undefinedCases']==119 and p['invalidStatesRejected']==10
 else:assert p['states']==818 and p['closedOutwardFaceChecks']==17376 and p['pieceVolumeChecks']==2896 and p['nonoverlapChecks']==6728
 for path,digest in p['sourceSHA256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest

def test_ratio_changes_only_authored_teaching_and_its_companion():
 old=json.loads((D/'original-node.json').read_bytes());p='data/curriculum/01-mathematics.json';data=json.loads(before_base_ten_bytes(p,(ROOT/p).read_bytes()));n=next(n for n in data['nodes']if n['id']=='math.2.ratio');_validate_authored_lesson(n);_validate_lesson_media(n)
 assert n['quiz']==old['quiz']and len(n['quiz'])==10 and n['prereqs']==old['prereqs']and n['lesson_media'][0]==old['lesson_media'][0]and len(n['learning_outcomes'])==9
 assert {k:v for k,v in n.items()if k not in ['lesson','learning_outcomes','lesson_media']}=={k:v for k,v in old.items()if k!='lesson_media'}
 data['nodes'][data['nodes'].index(n)]=old;audit=json.loads((D/'initial-scope-audit.json').read_bytes());assert hashlib.sha256((json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode()).hexdigest()==audit['curriculumSHA256']
 p='data/module-models.json';m=json.loads(before_base_ten_bytes(p,(ROOT/p).read_bytes()));b=next(b for b in m['models']if b['node_id']=='math.2.ratio');assert b['family']=='ratio-calibrated-volumes'and b['mode']=='model';m['models'][m['models'].index(b)]=json.loads((D/'original-binding.json').read_bytes());assert hashlib.sha256((json.dumps(m,indent=2,ensure_ascii=False)+'\n').encode()).hexdigest()==audit['bindingsSHA256']
 for bad in ['math.2.percent','unknown',None]:
  changed=copy.deepcopy(n);changed['lesson_media'][1]['props']['scenario']=bad
  with pytest.raises(ValueError):_validate_lesson_media(changed)

@pytest.mark.parametrize('path',sorted(bridge.PATHS))
def test_exact_historical_inverse_preserves_unrelated_drift(path):
 raw=(ROOT/path).read_bytes();row=bridge.reviewed()['files'][path];assert bridge.sha(before_base_ten_bytes(path,raw,allow_older=True))==row['after_sha256'];before=bridge.before_ratio_bytes(path,raw);assert bridge.sha(before)==row['before_sha256'];assert bridge.before_ratio_bytes(path,before)==before
 with pytest.raises(ValueError,match='Unreviewed'):bridge.before_ratio_bytes(path,raw+b'\n')
 assert bridge.before_ratio_bytes('unrelated',b'exact')==b'exact'

def test_reader_proof_is_bound_to_actual_runtime_and_oracles():
 p=json.loads((D/'reader/proof.json').read_bytes());assert p['allPassed']and p['errors']==[]and p['syntheticLoopback']and not p['productionVerified']
 for path,digest in p['sourceSHA256'].items():assert hashlib.sha256(before_base_ten_bytes(path,(ROOT/path).read_bytes(),allow_older=True)).hexdigest()==digest,path
 assert {c['width']for c in p['cases']}=={390,1440};assert sum(len(c['states'])for c in p['cases'])==70;assert sum(len(c['spatialCases'])for c in p['cases'])==140;assert sum(len(c['speeches'])+len(c['spatialSpeeches'])for c in p['cases'])==92
 for c in p['cases']:
  assert c['originalIllustrationLoaded']and c['invalidDraftPreservesAcceptedState']and c['labZoomPreservesSpeechIconAndCompanionSize']and c['keyboardScroll']and c['inactiveSpatialControlsHiddenAndDisabled'];assert len(c['sliders'])==5
  assert {s['state']['mode']for s in c['states']}=={'scale','compare','share','missing','rate','recipe','map','model','mapCompare'}

def test_every_existing_quiz_example_has_an_exact_workbench_answer():
 script="""const c=require('./web/ratio-core.js'),lab=require('./web/ratio-lab.js');console.log(JSON.stringify(Object.fromEntries(lab.presets.map(([key,,state])=>[key,c.build(state)]))));"""
 p=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT,text=True))
 for preset,key,expected in [('flour','resultB','9'),('map','groundKm','40'),('eggs','result','15'),('car','modelCm','20'),('paint','resultA','15'),('missing','resultB','39'),('drink','resultA','100'),('books','result','4'),('maps','secondToFirst','4'),('class','fractionA','3/7')]:assert p[preset][key]['exact']==expected
 assert p['equal']['equivalent']and not p['addition']['equivalent']and p['third']['result']['exact']=='2/3'and not p['zero']['equivalent']and p['undefined']['status']=='undefined'
