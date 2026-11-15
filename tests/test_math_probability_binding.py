"""Large-number sampling supplements the existing distribution activity."""
import copy
import hashlib
from pathlib import Path
import pytest
from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]


def test_probability_activity_preserves_the_distribution_model():
    n = Curriculum().nodes['math.4.prob-theory']
    assert any(m.get('renderer') == 'concept-lab' for m in n['lesson_media'])
    items = [m for m in n['lesson_media'] if m.get('renderer') == 'math-probability-lab']
    assert len(items) == 1 and items[0]['props'] == {'scenario':'math.4.prob-theory.large-numbers'}
    _validate_lesson_media(n)


@pytest.mark.parametrize('alteration',['lesson','scenario','extra'])
def test_probability_activity_cannot_be_rebound(alteration):
    n=copy.deepcopy(Curriculum().nodes['math.4.prob-theory'])
    item=next(m for m in n['lesson_media'] if m.get('renderer')=='math-probability-lab');n['lesson_media']=[item]
    if alteration=='lesson':n['id']='math.3.probability'
    elif alteration=='scenario':item['props']['scenario']='math.4.prob-theory'
    else:item['props']['url']='https://example.org/data'
    with pytest.raises(ValueError,match='cross-lesson'):_validate_lesson_media(n)


def test_probability_assets_are_loaded_and_content_tagged():
    from primer.server import app_shell
    html=app_shell().body.decode()
    assert html.index('/app/math-probability-lab.js')<html.index('/app/lesson-models.js')
    for name in ('math-probability-lab.js','math-probability-lab.css'):
        tag=hashlib.sha256((ROOT/'web'/name).read_bytes()).hexdigest()[:10]
        assert '/app/'+name+'?v='+tag in html
