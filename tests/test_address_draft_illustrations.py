import hashlib
import json
from pathlib import Path

from PIL import Image

from tools import check_curriculum_illustrations as audit


ROOT = Path(__file__).resolve().parents[1]


def test_draft_pages_preserve_source_pixels_and_reading_regions():
    metadata = json.loads((ROOT / 'web/language/address-drafts/witnesses.json').read_text())
    checked = []
    for key, witness in metadata['witnesses'].items():
        for page in witness['pages']:
            asset = ROOT / 'web' / page['image'].removeprefix('/app/')
            with Image.open(asset) as image:
                assert image.size == (page['width'], page['height'])
                assert hashlib.sha256(image.convert('RGB').tobytes()).hexdigest() == page['rgbSHA256']
        for passage in witness['passages']:
            revision = passage.get('revision')
            if revision:
                page = witness['pages'][revision['page']-1]
                x0,y0,x1,y1 = revision['box']
                assert 0 <= x0 < x1 <= page['width'] and 0 <= y0 < y1 <= page['height']
                assert any(b['page'] == page['number'] and b['top'] <= y0 and y1 <= b['bottom']
                           for b in passage['bands'])
                checked.append((key, revision['page']))
    assert checked == [('hay', 1), ('hay', 1), ('hay', 2)]


def test_only_four_referenced_source_pages_enter_the_curriculum_audit():
    errors = []
    paths = audit.manuscript_illustrations(errors)
    assert errors == []
    assert paths == {Path('illustrations/address-drafts') / f'{key}-{number}.webp'
                     for key in ('nicolay', 'hay') for number in (1, 2)}
