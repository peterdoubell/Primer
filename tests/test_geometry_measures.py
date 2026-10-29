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
