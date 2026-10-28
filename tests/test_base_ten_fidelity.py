"""Five actual lessons preserve assessments and use independently checked quantities."""
from pathlib import Path
import copy,hashlib,json,subprocess,sys
import pytest
from primer.curriculum import _validate_authored_lesson,_validate_lesson_media
from tools import base_ten_runtime_compatibility as bridge
from tools.nextbrain_runtime_compatibility import before_nextbrain_bytes
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/base-ten-fidelity-review-20261027';IDS={'math.1.place-value','math.1.addition','math.1.subtraction','math.1.multiplication','math.1.division'}
@pytest.mark.parametrize('kind',['core','spatial'])
def test_independent_current_base_ten_oracle(kind):
 r=subprocess.run([sys.executable,str(ROOT/f'tools/check_base_ten_{kind}.py')],cwd=ROOT,text=True,capture_output=True,timeout=180);assert r.returncode==0,r.stdout+r.stderr;p=json.loads(r.stdout);assert p['allPassed']and not p['wholeGoalComplete']
 if kind=='core':assert p['cases']==56774 and p['checks']==615446 and p['undefinedCases']==290 and p['invalidStatesRejected']==12;assert p['sourceSHA256']==hashlib.sha256((ROOT/'web/base-ten-core.js').read_bytes()).hexdigest()
 else:
  assert p['states']==1382 and p['closedOutwardFaceChecks']==273570 and p['pieceVolumeChecks']==45595 and p['nonoverlapChecks']==1919837 and p['maxPrimitives']==2604
  for path,h in p['sourceSHA256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h

def test_only_the_five_lesson_teaching_and_companions_change():
 scope=json.loads((D/'initial-scope.json').read_bytes());data=json.loads(before_nextbrain_bytes('data/curriculum/01-mathematics.json',(ROOT/'data/curriculum/01-mathematics.json').read_bytes()));bindings=json.loads(before_nextbrain_bytes('data/module-models.json',(ROOT/'data/module-models.json').read_bytes()));originals={n['id']:n for n in scope['originalNodes']};old_bindings={n['node_id']:n for n in scope['originalBindings']};assert set(originals)==IDS and sum(len(n['quiz'])for n in originals.values())==35
 for n in data['nodes']:
  if n['id']not in IDS:continue
  old=originals[n['id']];_validate_authored_lesson(n);_validate_lesson_media(n);assert n['quiz']==old['quiz']and n['prereqs']==old['prereqs']and n['lesson_media'][:2]==old['lesson_media'];assert len(n['learning_outcomes'])==5
  assert {k:v for k,v in n.items()if k not in ['lesson','learning_outcomes','lesson_media']}=={k:v for k,v in old.items()if k!='lesson_media'}
  added=n['lesson_media'][2];assert added['renderer']=='base-ten-lab'and added['props']=={'scenario':n['id']};b=next(b for b in bindings['models']if b['node_id']==n['id']);assert b['family']=='base-ten-'+n['id'].split('.')[-1]and b['mode']=='model';bindings['models'][bindings['models'].index(b)]=old_bindings[n['id']]
 data['nodes']=[originals.get(n['id'],n)for n in data['nodes']]
 assert hashlib.sha256((json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode()).hexdigest()==scope['baselineCurriculumSHA256']
 assert hashlib.sha256((json.dumps(bindings,indent=2,ensure_ascii=False)+'\n').encode()).hexdigest()==bridge.reviewed()['files']['data/module-models.json']['before_sha256']

@pytest.mark.parametrize('path',sorted(bridge.PATHS))
def test_exact_integration_inverse_preserves_unrelated_drift(path):
 raw=before_nextbrain_bytes(path,(ROOT/path).read_bytes());row=bridge.reviewed()['files'][path];assert bridge.sha(raw)==row['after_sha256'];old=bridge.before_base_ten_bytes(path,raw);assert bridge.sha(old)==row['before_sha256'];assert bridge.before_base_ten_bytes(path,old)==old
 with pytest.raises(ValueError,match='Unreviewed'):bridge.before_base_ten_bytes(path,raw+b'\n')
 assert bridge.before_base_ten_bytes('unrelated',b'exact')==b'exact'

def test_schema_rejects_unknown_cross_lesson_and_extra_props():
 data=json.loads((ROOT/'data/curriculum/01-mathematics.json').read_bytes())
 for n in data['nodes']:
  if n['id']not in IDS:continue
  for props in [{'scenario':'math.2.ratio'},{'scenario':next(id for id in IDS if id!=n['id'])},{'scenario':n['id'],'extra':True},{}]:
   changed=copy.deepcopy(n);changed['lesson_media'][2]['props']=props
   with pytest.raises(ValueError):_validate_lesson_media(changed)
 script="global.window={};require('./web/base-ten-core.js');require('./web/base-ten-lab.js');const a=require('assert/strict');for(const item of [null,{}, {renderer:'concept-lab',props:{scenario:'math.1.addition'}},{renderer:'base-ten-lab',props:{scenario:'math.2.ratio'}},{renderer:'base-ten-lab',props:{scenario:'math.1.addition',extra:true}}])a.equal(window.PrimerBaseTenLab.render(item),null);"
 subprocess.run(['node','-e',script],cwd=ROOT,check=True,capture_output=True,text=True)

def test_every_preserved_assessment_has_a_corresponding_worked_example():
 script="const c=require('./web/base-ten-core.js'),l=require('./web/base-ten-lab.js');console.log(JSON.stringify(Object.fromEntries(Object.entries(l.presets).map(([id,rows])=>[id,Object.fromEntries(rows.map(([key,,s])=>[key,c.build(id,s)]))]))));"
 models=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT,text=True));scope=json.loads((D/'initial-scope.json').read_bytes());answers={n['id']:[q['answer']for q in n['quiz']]for n in scope['originalNodes']}
 cases={'math.1.place-value':[('forty-seven',lambda m:m['places'][1]['contribution']),('sixty',lambda m:m['places'][1]['digit']),('forty-seven',lambda m:m['value']),('fifty-eight',lambda m:m['places'][0]['contribution']),('thirty',lambda m:m['places'][1]['digit']),('ninety',lambda m:m['value']),('twenty-six',lambda m:m['value'])]}
 for id,names in {'math.1.addition':['five-three','eight-five','tens','friendly','double','ten-more','swapped'],'math.1.subtraction':['nine-four','sweets','compare','eight-three','birds','twelve-five','inverse'],'math.1.multiplication':['cookies','two-five','six-six','three-three','sweets','largest','seven-two'],'math.1.division':['friends','ten-two','inverse','eight-two','baskets','twenty-five','fifteen-five']}.items():cases[id]=[(name,lambda m,key='quotient'if id.endswith('division')else'result':m[key])for name in names]
 for id,rows in cases.items():assert [str(extract(models[id][name]))for name,extract in rows]==answers[id]

def test_actual_child_reader_and_all_camera_evidence_match_current_sources():
 p=json.loads((D/'reader/proof.json').read_bytes());assert p['allPassed']and p['errors']==[]and p['profileAge']==8 and p['syntheticLoopback']and not p['productionVerified']
 # Preserve the exact recorded base-ten proof after removing only the pinned NextBrain integration.
 for path,h in p['sourceSHA256'].items():assert hashlib.sha256(before_nextbrain_bytes(path,(ROOT/path).read_bytes())).hexdigest()==h,path
 assert {(c['lesson'],c['width'])for c in p['cases']}=={(id,w)for id in IDS for w in [390,1440]};assert sum(len(c['states'])for c in p['cases'])==116;assert sum(len(c['poses'])for c in p['cases'])==462;assert sum(len(c['speeches'])+len(c['spatialSpeeches'])for c in p['cases'])==192
 for c in p['cases']:
  assert c['originalIllustrationLoaded']and c['originalTeachingModelPreserved']and c['invalidDraftPreservesAcceptedState']and c['zoomPreservesSpeechIconAndCompanionSize']and c['keyboardHorizontalScroll'];assert c['controls']
  if c['lesson']=='math.1.place-value':assert c['exchangeVerified']
  if c['lesson']in ['math.1.addition','math.1.multiplication']:assert c['swapVerified']
  if c['lesson']=='math.1.division':assert c['keyboardVerticalScroll']
  assert {pose['camera']for pose in c['poses']}=={'Reset view','Rotate left','Rotate right','Tilt up','Tilt down','Zoom in','Zoom out'}
  assert all(pose['geometry']['allProjectedVerticesMatch']and pose['geometry']['labelsWithinCanvasAndSeparate']and pose['geometry']['croppedNoticeMatchesGeometry']for pose in c['poses'])
