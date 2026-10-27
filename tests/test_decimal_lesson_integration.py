"""Preserve original content, exact bindings and authenticated-reader evidence."""
import copy,hashlib,json,subprocess
from pathlib import Path
from tools.schirmer_runtime_compatibility import before_schirmer_bytes
from tools.ratio_runtime_compatibility import before_ratio_bytes
import pytest
from primer.curriculum import _validate_authored_lesson,_validate_lesson_media
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/decimal-fidelity-review-20261026'
def test_only_decimal_teaching_and_companion_binding_change():
 old=json.loads((D/'original-node.json').read_bytes());data=json.loads(before_ratio_bytes('data/curriculum/01-mathematics.json',(ROOT/'data/curriculum/01-mathematics.json').read_bytes()));node=next(n for n in data['nodes']if n['id']=='math.2.decimals')
 _validate_authored_lesson(node);_validate_lesson_media(node)
 assert len(node['quiz'])==10 and node['quiz']==old['quiz'] and node['prereqs']==old['prereqs'] and node['lesson_media'][0]==old['lesson_media'][0]
 assert len(node['learning_outcomes'])==8
 assert {k:v for k,v in node.items()if k not in ['lesson','learning_outcomes','lesson_media']}=={k:v for k,v in old.items()if k!='lesson_media'}
 data['nodes'][data['nodes'].index(node)]=old
 assert hashlib.sha256((json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode()).hexdigest()==json.loads((D/'initial-scope-audit.json').read_bytes())['curriculumSHA256']
 manifest=json.loads(before_ratio_bytes('data/module-models.json',(ROOT/'data/module-models.json').read_bytes()));binding=next(n for n in manifest['models']if n['node_id']=='math.2.decimals');assert binding['family']=='decimal-base-ten' and binding['mode']=='model'
 manifest['models'][manifest['models'].index(binding)]=json.loads((D/'original-binding.json').read_bytes())
 assert hashlib.sha256((json.dumps(manifest,indent=2,ensure_ascii=False)+'\n').encode()).hexdigest()==json.loads((D/'original-binding-identity.json').read_bytes())['sha256']
def test_actual_reader_proof_matches_current_sources():
 p=json.loads((D/'reader/proof.json').read_bytes());assert p['allPassed']and not p['productionVerified']and p['errors']==[]
 for f,h in p['sourceSHA256'].items():assert hashlib.sha256(before_schirmer_bytes(f,(ROOT/f).read_bytes(),allow_older=True)).hexdigest()==h,f
 assert {c['width']for c in p['cases']}=={390,1440}
 assert sum(len(c['states'])for c in p['cases'])==62 and sum(len(c['speeches'])+len(c['spatialSpeeches'])for c in p['cases'])==78
 assert sum(len(c['spatialCases'])for c in p['cases'])==98 and sum(len(c['sliders'])for c in p['cases'])==10
 for c in p['cases']:assert c['originalIllustrationLoaded']and c['invalidDraftPreservesAcceptedState']and c['labZoomPreservesSpeechIconAndCompanionSize']and c['keyboardScroll']
def test_renderer_and_authored_schema_reject_wrong_binding():
 script="const a=require('./web/decimal-lab.js'),assert=require('assert/strict');for(const item of [null,{}, {renderer:'fraction-arithmetic-lab',props:{scenario:'math.2.decimals'}},{renderer:'concept-lab',props:{scenario:'math.2.percent'}},{renderer:'concept-lab',props:{scenario:'math.2.decimals',extra:true}}])assert.equal(a.render(item),null);"
 subprocess.run(['node','-e',script],cwd=ROOT,check=True,capture_output=True,text=True)
 n=next(n for n in json.loads((ROOT/'data/curriculum/01-mathematics.json').read_bytes())['nodes']if n['id']=='math.2.decimals')
 for scenario in ['math.2.percent','unknown',None]:
  changed=copy.deepcopy(n);changed['lesson_media'][1]['props']['scenario']=scenario
  with pytest.raises(ValueError):_validate_lesson_media(changed)
