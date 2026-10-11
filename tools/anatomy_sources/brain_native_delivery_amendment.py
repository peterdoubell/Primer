"""Restore only the separately reviewed additive brain inspector for historical scope."""
import copy
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEW = Path('docs/brain-fine-independent-review-20261011.json')
REVIEW_SHA256 = '96373ba15c914a45e7afc99f58f5e1b7f3c58ea7aa67a234935adb65f0f54af1'
MEDIA = {'id': 'module-native-inspectors-rad.5.brain-anatomy', 'kind': 'source-native-inspectors',
         'title': 'Native source anatomy inspection',
         'instructions': 'Inspect the complete provided source selections against native images and separate atlas probabilities. Read population, sampling and anatomical limits before interpretation.',
         'investigation_ids': ['ra.brain-anatomy']}


def restored_historical_contract(contract, module_id, root=ROOT):
    result = copy.deepcopy(contract)
    if module_id != 'rad.5.brain-anatomy':
        return result
    if hashlib.sha256((root / REVIEW).read_bytes()).hexdigest() != REVIEW_SHA256:
        raise ValueError('Independent native brain inspector review changed')
    additions = [m for m in result['lesson_media'] if m.get('kind') == 'source-native-inspectors']
    if additions != [MEDIA]:
        raise ValueError('Unreviewed native brain inspector lesson scope')
    result['lesson_media'] = [m for m in result['lesson_media'] if m.get('kind') != 'source-native-inspectors']
    return result


def separate_review(root=ROOT):
    if hashlib.sha256((root / REVIEW).read_bytes()).hexdigest() != REVIEW_SHA256:
        raise ValueError('Independent native brain inspector review changed')
    return {'module_id':'rad.5.brain-anatomy','review':REVIEW.as_posix(),'review_sha256':REVIEW_SHA256,
            'source_model_props_changed':False,'historical_approval_extended':False}
