"""Current fractions arithmetic, mesh geometry, lesson binding and preservation."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/fractions-fidelity-review-20261026'

def report(tool):
 run=subprocess.run([sys.executable,'tools/'+tool],cwd=ROOT,text=True,capture_output=True,timeout=90,check=True)
 return json.loads(run.stdout)

def test_exact_rational_operations_and_all_partition_intersections():
 proof=report('check_fractions_lab.py')
 assert proof['allPassed'] and proof['cases']==5060 and proof['defined']==3596 and proof['undefined']==1464

def test_companion_is_closed_outward_equal_volume_and_exact_readout():
 proof=report('check_fractions_companion.py')
 assert proof['allPassed'] and proof['validControlStates']==96 and proof['normalizedBoundaryStates']==7
 assert proof['closedSectorFaceChecks']>11000

def test_only_target_lesson_presentation_changes_and_assessment_is_preserved():
 original=json.loads((DOC/'original-fractions-node.json').read_text())
 from tools.percentage_runtime_compatibility import before_percentage_bytes
 path=ROOT/'data/curriculum/01-mathematics.json';all_nodes=json.loads(before_percentage_bytes('data/curriculum/01-mathematics.json',path.read_bytes()));node=next(n for n in all_nodes['nodes'] if n['id']=='math.2.fractions')
 assert node['quiz']==original['quiz'] and len(node['quiz'])==10
 assert node['prereqs']==original['prereqs']
 assert [m for m in node['lesson_media'] if m['kind']=='illustration']==[m for m in original['lesson_media'] if m['kind']=='illustration']
 assert {k:v for k,v in node.items() if k not in ['lesson_media','learning_outcomes','lesson']}=={k:v for k,v in original.items() if k not in ['lesson_media','learning_outcomes','lesson']}
 index=all_nodes['nodes'].index(node);all_nodes['nodes'][index]=original
 restored=(json.dumps(all_nodes,ensure_ascii=False,indent=2)+'\n').encode()
 identity=json.loads((DOC/'original-curriculum-identity.json').read_text());assert hashlib.sha256(restored).hexdigest()==identity['sha256']

def test_shared_companion_changes_are_confined_to_one_family():
 current=(ROOT/'web/spatial-module-objects.js').read_text();start=current.index("  define('fraction-disk'");end=current.index("\n  define('clock'",start)
 old=(DOC/'fraction-disk.before.js.txt').read_text();identity=json.loads((DOC/'fraction-disk-refresh.json').read_text())
 assert hashlib.sha256((current[:start]+old+current[end:]).encode()).hexdigest()==identity['before_sha256']
 assert hashlib.sha256(current[:start].encode()).hexdigest()==identity['unchanged_prefix_sha256']
 assert hashlib.sha256(current[end:].encode()).hexdigest()==identity['unchanged_suffix_sha256']

def test_exact_lesson_schema_rejects_cross_lesson_or_malformed_props():
 from primer.curriculum import _validate_lesson_media
 node=next(n for n in json.loads((ROOT/'data/curriculum/01-mathematics.json').read_text())['nodes'] if n['id']=='math.2.fractions')
 _validate_lesson_media(node)
 media=next(m for m in node['lesson_media'] if m.get('renderer')=='fraction-arithmetic-lab')
 for changed_id,props in [('math.2.decimals',{'scenario':'math.2.fractions'}),('math.2.fractions',{}),('math.2.fractions',{'scenario':'math.2.percent'}),('math.2.fractions',{'scenario':'math.2.fractions','unreviewed':True}),('math.2.fractions',{'scenario':None})]:
  altered=copy.deepcopy(node);altered['id']=changed_id;altered['lesson_media']=[dict(media,props=props)]
  with pytest.raises(ValueError):_validate_lesson_media(altered)

def test_renderer_rejects_wrong_binding_before_dom_and_unknown_model_keys():
 script="""const a=require('./web/fractions-lab.js'),assert=require('assert/strict');for(const item of [null,{}, {renderer:'fraction-equivalence-lab',props:{scenario:a.scenario}},{renderer:'fraction-arithmetic-lab',props:{scenario:'math.2.decimals'}},{renderer:'fraction-arithmetic-lab',props:{scenario:a.scenario,extra:true}}])assert.equal(a.render(item),null);assert.throws(()=>a.build({unknown:1}));assert.equal(a.scenario,'math.2.fractions');"""
 subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True,check=True)
