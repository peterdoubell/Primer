"""Source artwork counts separately from plates and must remain referenced and intact."""
import copy
import json
from pathlib import Path
import shutil

import pytest

from tools import check_curriculum_illustrations as illustrations

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path, monkeypatch):
    language = json.loads((ROOT / 'data/curriculum/02-language.json').read_text())
    node = copy.deepcopy(next(node for node in language['nodes'] if node['id'] == 'lang.5.comp-ling'))
    plate = next(media for media in node['lesson_media'] if media['kind'] == 'illustration')
    node['lesson_media'] = [plate]
    curriculum = tmp_path / 'data/curriculum'
    curriculum.mkdir(parents=True)
    (curriculum / 'language.json').write_text(json.dumps(dict(id='language', name='Language', nodes=[node])))
    for relative in ['web/language/word-samples', 'web/illustrations/word-samples']:
        shutil.copytree(ROOT / relative, tmp_path / relative)
    for relative in ['web/activities/registry.json', 'docs/word-samples/source.json', 'data/lesson-illustrations.json']:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    for candidate in plate['srcset'].split(','):
        relative = 'web/' + candidate.strip().split()[0].removeprefix('/app/')
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    monkeypatch.setattr(illustrations, 'ROOT', tmp_path)
    monkeypatch.setattr(illustrations, 'WEB_ROOT', tmp_path / 'web')
    monkeypatch.setattr(illustrations, 'CURRICULUM_ROOT', curriculum)
    return tmp_path


def test_registered_source_figures_do_not_hide_an_unreferenced_image(project):
    report = illustrations.audit()
    assert report['lessons'] == report['plates'] == 1
    assert report['responsive_webps'] == 2 and report['activity_source_webps'] == 82
    assert report['errors'] == report['orphan_webps'] == []
    # Even in the recognised source directory, a real image without a corpus reference is an orphan.
    folder = project / 'web/illustrations/word-samples'
    shutil.copyfile(next(folder.glob('*-800.webp')), folder / 'unused.webp')
    report = illustrations.audit()
    assert report['orphan_webps'] == ['illustrations/word-samples/unused.webp']
    assert report['errors']


def test_a_displayable_image_with_changed_bytes_does_not_pass_its_source_receipt(project):
    path = next((project / 'web/illustrations/word-samples').glob('*-800.webp'))
    original = path.read_bytes()
    path.write_bytes(original + b'changed')
    report = illustrations.audit()
    assert report['activity_source_webps'] == 0
    assert any('rendition differs' in error for error in report['errors'])
    assert report['orphan_webps']


def test_artwork_requires_a_live_activity_registration(project):
    registry = project / 'web/activities/registry.json'
    data = json.loads(registry.read_text())
    data['lang.5.comp-ling'] = []
    registry.write_text(json.dumps(data))
    report = illustrations.audit()
    assert report['activity_source_webps'] == 0 and len(report['orphan_webps']) == 82
    assert any('no registered' in error for error in report['errors'])
