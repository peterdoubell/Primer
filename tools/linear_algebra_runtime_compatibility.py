"""Exact historical view of one linear-algebra companion and one clarified quiz.

Native/current behavior is tested separately; this inverse grants no approval.
"""
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/linear-algebra-fidelity-review-20261016/integration/runtime-inverse.json'
PROOF_SHA256 = '939513afdbf83a6a141d039d297da7bb6429c4644df871d4ca4c722eb4a1f872'
MATH = 'data/curriculum/01-mathematics.json'
MODULE = 'math.4.linalg'
PATHS = frozenset({MATH, 'primer/curriculum.py', 'web/index.html', 'web/lesson-models.js'})


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def semantic(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode())


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Linear algebra inverse evidence changed')
    proof = json.loads(raw)
    if (set(proof['files']) != PATHS or proof['module_id'] != MODULE
            or proof['base_commit'] != '4a2cd9bd856beae68e85d4d9050cd10cce5f9651'
            or proof['quiz_index'] != 8
            or any(proof[field] is not False for field in ['extends_historical_approval', 'product_pacing_overridden',
                                                          'new_linear_algebra_science_and_reader_validated_by_this_inverse'])):
        raise ValueError('Linear algebra inverse leaves its exact scope')
    return proof


def before_linear_algebra_bytes(path, raw, allow_older=False):
    from tools.structured_reporting_runtime_compatibility import before_structured_bytes
    raw = before_structured_bytes(path, raw, allow_older=True)
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw  # The earlier caller must still prove its own exact historical identity.
        raise ValueError('Unreviewed linear algebra runtime byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('Linear algebra inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Linear algebra inverse changes unrelated bytes')
    return restored


def before_linear_algebra_lesson_fields(module_id, fields):
    if module_id != MODULE:
        return fields
    proof = reviewed()
    result = copy.deepcopy(fields)
    media = result.get('lesson_media', [])
    matches = [item for item in media if item.get('id') == proof['added_media']['id']]
    if matches:
        if matches != [proof['added_media']]:
            raise ValueError('Unreviewed linear algebra companion metadata change')
        media.remove(matches[0])
    if 'quiz' in result:
        question = result['quiz'][8]
        marker = question.get('ephemeral', None)
        authored = {key: value for key, value in question.items() if key != 'ephemeral'}
        if (marker is not None and marker is not False) or authored not in [proof['before_quiz'], proof['after_quiz']]:
            raise ValueError('Unreviewed linear algebra quiz change')
        if authored == proof['after_quiz']:
            result['quiz'][8] = copy.deepcopy(proof['before_quiz'])
            if 'ephemeral' in question:
                result['quiz'][8]['ephemeral'] = marker
    return result


def source_corpus():
    return {str(path.relative_to(ROOT)): path.read_bytes() for path in sorted((ROOT / 'data/curriculum').glob('*.json'))}


def independent_stage4_budget(corpus):
    """Raw authored text and exact rational rounding, independent of Curriculum."""
    rows = []
    for path, raw in sorted(corpus.items()):
        data = json.loads(raw)
        threshold = int(data.get('reference_stage', data.get('entry_stage', 0)))
        for node in data['nodes']:
            if node['stage'] != 4 or (threshold > 0 and node['stage'] >= threshold):
                continue
            pieces = [node.get('kid_text') or '']
            pieces.extend(question.get(key, '') for question in node.get('quiz') or [] for key in ['prompt', 'explain', 'answer'])
            if not all(isinstance(piece, str) for piece in pieces):
                raise ValueError('Unreviewed nontext duration source')
            rows.append({'id': node['id'], 'file': path, 'characters': sum(map(len, pieces)),
                         'authored_minutes': node.get('minutes')})
    rows.sort(key=lambda row: row['id'])
    total = sum(row['characters'] for row in rows)
    if not total or len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Unreviewed stage-4 duration pool')
    for row in rows:
        ratio = min(Fraction(3, 2), max(Fraction(1, 2), Fraction(row['characters'] * len(rows), total)))
        minutes = 1680 * ratio
        row.update(unrounded_numerator=minutes.numerator, unrounded_denominator=minutes.denominator,
                   minutes=row['authored_minutes'] if row['authored_minutes'] is not None else max(5, round(minutes / 5) * 5))
    return {'pool_count': len(rows), 'pool_character_sum': total, 'rows': rows}


def duration_counterfactual(corpus=None):
    proof = reviewed()['derived_duration']
    corpus = source_corpus() if corpus is None else corpus
    if {path: sha(raw) for path, raw in sorted(corpus.items())} != proof['current_corpus_sha256']:
        raise ValueError('Unreviewed linear algebra duration corpus change')
    previous = dict(corpus)
    previous[MATH] = before_linear_algebra_bytes(MATH, corpus[MATH])
    current, prior = independent_stage4_budget(corpus), independent_stage4_budget(previous)
    if current != proof['current'] or prior != proof['before']:
        raise ValueError('Independent linear algebra duration counterfactual differs')
    return current, prior


def before_linear_algebra_duration_fields(lesson):
    proof = reviewed()
    row = proof['derived_duration']['lesson_semantics'].get(lesson.get('id'))
    if row is None:
        return lesson
    current, prior = duration_counterfactual()
    if semantic(lesson) not in {row['current_sha256'], row['before_sha256']}:
        raise ValueError('Unreviewed lesson fields in linear algebra duration inverse')
    result = before_linear_algebra_lesson_fields(lesson['id'], lesson)
    result = copy.deepcopy(result)
    result['minutes'] = next(item['minutes'] for item in prior['rows'] if item['id'] == lesson['id'])
    if semantic(result) != row['before_sha256']:
        raise ValueError('Linear algebra duration inverse changes unrelated lesson fields')
    return result
