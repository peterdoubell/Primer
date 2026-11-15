"""The continuum wave activity supplements the original insulated heat rod."""
import copy
import hashlib
from pathlib import Path
import pytest
from primer.curriculum import Curriculum, _validate_lesson_media

ROOT = Path(__file__).resolve().parents[1]


def test_wave_activity_preserves_original_heat_and_uses_own_lesson():
    n = Curriculum().nodes['math.5.pde']
    assert any(m.get('renderer') == 'heat-equation-lab' for m in n['lesson_media'])
    wave = [m for m in n['lesson_media'] if m.get('renderer') == 'math-wave-lab']
    assert len(wave) == 1 and wave[0]['props'] == {'scenario': 'math.5.pde.wave-field'}
    _validate_lesson_media(n)


@pytest.mark.parametrize('alteration', ['lesson', 'scenario', 'extra'])
def test_wave_cannot_switch_lesson_or_fetch_extra_assets(alteration):
    n = copy.deepcopy(Curriculum().nodes['math.5.pde'])
    item = next(m for m in n['lesson_media'] if m.get('renderer') == 'math-wave-lab')
    n['lesson_media'] = [item]
    if alteration == 'lesson': n['id'] = 'math.4.diffeq'
    elif alteration == 'scenario': item['props']['scenario'] = 'math.5.pde'
    else: item['props']['url'] = 'https://example.org/extra.js'
    with pytest.raises(ValueError, match='cross-lesson'): _validate_lesson_media(n)


def test_wave_asset_order_and_hashes():
    from primer.server import app_shell
    html = app_shell().body.decode()
    assert html.index('/app/math-wave-lab.js') < html.index('/app/lesson-models.js')
    for name in ('math-wave-lab.js', 'math-wave-lab.css'):
        tag = hashlib.sha256((ROOT/'web'/name).read_bytes()).hexdigest()[:10]
        assert '/app/'+name+'?v='+tag in html
