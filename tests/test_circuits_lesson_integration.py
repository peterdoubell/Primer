"""Preservation and authored teaching for the two integrated physics lessons."""
import hashlib,json
from pathlib import Path
from primer.curriculum import _validate_authored_lesson,_validate_lesson_media
ROOT=Path(__file__).resolve().parents[1]
def test_only_teaching_changes_and_original_assessments_and_media_remain():
 original=json.loads((ROOT/'docs/circuits-induction-review-20261026/original-lessons.json').read_text())
 data=json.loads((ROOT/'data/curriculum/03-physics.json').read_text());old={n['id']:n for n in original['nodes']}
 for i,n in enumerate(data['nodes']):
  if n['id'] not in old:continue
  _validate_authored_lesson(n);_validate_lesson_media(n)
  assert len(n['quiz'])==10 and n['quiz']==old[n['id']]['quiz']
  assert {k:v for k,v in n.items() if k not in ('lesson','learning_outcomes')}==old[n['id']]
  data['nodes'][i]=old[n['id']]
 assert hashlib.sha256((json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode()).hexdigest()==original['curriculumSHA256']


def test_current_authenticated_reader_evidence_is_bound_to_actual_sources():
 proof=json.loads((ROOT/'docs/circuits-induction-review-20261026/reader-smoke/proof.json').read_text())
 assert proof['allPassed'] and proof['errors']==[] and not proof['productionVerified']
 for path,digest in proof['sourceSHA256'].items():
  assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
 assert len(proof['cases'])==20
 assert sum(len(c['speeches']) for c in proof['cases'])==126
 assert sum(len(c['boundaries']) for c in proof['cases'])==284
 for case in proof['cases']:
  assert case['invalidDraftPreservedAcceptedState'] and case['resetRestoredViewport']
  for b in case['boundaries']:
   assert b['rejected']==(case['station']=='pipe' and (b['control'],b['value']) in [('lengthCM',15),('releaseCM',25)])
