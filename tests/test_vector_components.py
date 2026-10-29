import hashlib,json
from pathlib import Path
from primer.curriculum import Curriculum
ROOT=Path(__file__).resolve().parents[1]

def test_vector_activity_preserves_original_teaching_and_model():
    source=json.loads((ROOT/'data/curriculum/01-mathematics.json').read_bytes())
    node=next(n for n in source['nodes'] if n['id']=='math.3.vectors')
    prior=json.loads((ROOT/'docs/vector-components-review-20261029/original-node.json').read_bytes())
    restored=dict(node);restored['lesson_media']=[m for m in node['lesson_media'] if m.get('renderer')!='vector-components-lab']
    assert restored==prior
    runtime=Curriculum().nodes[node['id']]
    assert [(m['renderer'],m['props']) for m in runtime['lesson_media'] if m.get('kind')=='model']==[('vector-components-lab',{'scenario':'math.3.vectors'}),('spatial-3d',{'scenario':'math.3.vectors'})]

def test_actual_vector_lesson_evidence_matches_current_sources():
    p=json.loads((ROOT/'docs/vector-components-review-20261029/lesson/proof.json').read_bytes())
    assert p['allPassed'] and p['geometryReadbackVerified'] and p['drawnSegmentsChecked']==496
    assert p['syntheticLoopback'] and not p['productionVerified'] and not p['errors']
    assert len(p['states'])==96 and {r['width'] for r in p['states']}=={390,1440}
    assert p['workedExamples']==7 and p['invalidRecoveryVerified']
    assert p['originalSpatialModelPresent'] and p['originalIllustrationLoaded']
    for file,digest in p['sourceSHA256'].items():assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==digest,file

def test_exact_vector_inverse_rejects_unrelated_changes():
    import pytest
    from tools.vector_components_runtime_compatibility import reviewed,before_vector_components_bytes
    for file,row in reviewed()['files'].items():
        raw=(ROOT/file).read_bytes();restored=before_vector_components_bytes(file,raw)
        assert hashlib.sha256(restored).hexdigest()==row['before_sha256']
        assert before_vector_components_bytes(file,restored)==restored
        with pytest.raises(ValueError):before_vector_components_bytes(file,raw+b'foreign change')
