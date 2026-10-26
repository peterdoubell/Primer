"""Assessment preservation, exact lesson scope and real-reader evidence."""
import hashlib,json
from pathlib import Path
from primer.curriculum import _validate_authored_lesson,_validate_lesson_media
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/percentage-fidelity-review-20261026'
def test_original_assessments_and_illustration_remain():
 old=json.loads((D/'original-node.json').read_text());data=json.loads((ROOT/'data/curriculum/01-mathematics.json').read_text());n=next(n for n in data['nodes']if n['id']=='math.2.percent')
 _validate_authored_lesson(n);_validate_lesson_media(n)
 assert len(n['quiz'])==10 and n['quiz']==old['quiz']
 assert n['prereqs']==old['prereqs']
 assert n['lesson_media'][0]==old['lesson_media'][0]
 assert {k:v for k,v in n.items()if k not in ('lesson','learning_outcomes','lesson_media')}=={k:v for k,v in old.items()if k!='lesson_media'}
 for i,node in enumerate(data['nodes']):
  if node['id']=='math.2.percent':data['nodes'][i]=old
 assert hashlib.sha256((json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode()).hexdigest()=='27e713d0c7579bbef7b61b66014c58d57c73a5f299637f37c99272e9b515e19e'
def test_real_reader_evidence_matches_current_sources():
 p=json.loads((D/'reader/proof.json').read_text())
 assert p['allPassed'] and p['errors']==[] and not p['productionVerified']
 for path,digest in p['sourceSHA256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
 assert {c['width']for c in p['cases']}=={390,1440}
 assert sum(len(c['states'])for c in p['cases'])==52
 assert sum(len(c['speech'])for c in p['cases'])==50
 for c in p['cases']:assert c['originalIllustrationLoaded'] and c['invalidDraftRetainsAcceptedState'] and c['speechIconUnchangedOnZoom'] and c['keyboardScrolling']
def test_wrong_renderer_or_cross_lesson_binding_is_rejected_before_dom():
 import subprocess
 script="const a=require('./web/percentage-lab.js'),assert=require('assert/strict');for(const item of [null,{}, {renderer:'fraction-arithmetic-lab',props:{scenario:'math.2.percent'}},{renderer:'concept-lab',props:{scenario:'math.2.decimals'}},{renderer:'concept-lab',props:{scenario:'math.2.percent',extra:true}}])assert.equal(a.render(item),null);"
 subprocess.run(['node','-e',script],cwd=ROOT,text=True,capture_output=True,check=True)
