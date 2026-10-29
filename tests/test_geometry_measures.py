import json
from pathlib import Path
from primer.curriculum import Curriculum

ROOT=Path(__file__).resolve().parents[1]

def test_geometry_activity_preserves_quiz_and_dedicated_layer_view():
    source=json.loads((ROOT/'data/curriculum/01-mathematics.json').read_bytes())
    node=next(n for n in source['nodes'] if n['id']=='math.2.geometry')
    prior=json.loads((ROOT/'docs/geometry-measures-review-20261029/initial-scope-audit.json').read_bytes())['node']
    assert node['quiz']==prior['quiz'] and len(node['quiz'])==10
    runtime=Curriculum().nodes[node['id']]
    models=[m for m in runtime['lesson_media'] if m.get('kind')=='model']
    assert [(m['renderer'],m['props']) for m in models]==[
        ('geometry-measures-lab',{'scenario':'math.2.geometry'}),
        ('spatial-3d',{'scenario':'math.2.geometry'})]
    assert not any(m['props'].get('family')=='lattice' for m in models)

def test_authenticated_geometry_lesson_evidence_matches_current_sources():
    import hashlib
    proof=json.loads((ROOT/'docs/geometry-measures-review-20261029/lesson/proof.json').read_bytes())
    assert proof['allPassed'] and proof['syntheticLoopback'] and not proof['productionVerified']
    assert not proof['errors'] and {r['width'] for r in proof['cases']}=={390,1440}
    for row in proof['cases']:
        assert len(row['states'])==12 and row['quizItemsPreserved']==10
        assert row['originalLayerModelPresent'] and row['layerSeparationAndCameraChecked']
        assert row['originalIllustrationLoaded'] and row['invalidInputClearsGeometry']
    for file,digest in proof['sourceSHA256'].items():
        assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==digest,file
