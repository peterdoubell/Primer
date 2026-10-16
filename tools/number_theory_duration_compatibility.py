"""Exact historical derived-duration view after four reviewed fluids corrections.

This helper never changes product pacing or treats a source change as approval.
"""
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/fluids-fidelity-review-20261016/number-theory-duration-counterfactual.json'
PROOF_SHA256 = '22cdd2141aad3a892b9220958ae19c521e89fb4c4b27bc22f7095d1a5ea6d513'
LESSON = 'math.4.numtheory'
PHYSICS = 'data/curriculum/03-physics.json'
TEST_PATH = 'tests/test_math_number_theory_lab.py'
HISTORICAL_SEMANTIC = '40e083972a0b87c9cd28f17dab8c5af2052d04eded764a7bb9ddf25c910f2c36'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def semantic(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode())


def current_corpus():
    return {str(path.relative_to(ROOT)): path.read_bytes() for path in sorted((ROOT / 'data/curriculum').glob('*.json'))}


def character_count(node):
    """Independent raw-authored input calculation; generated media is not content text."""
    pieces = [node.get('kid_text') or '']
    pieces.extend(question.get(field, '') for question in node.get('quiz') or []
                  for field in ('prompt', 'explain', 'answer'))
    if not all(isinstance(piece, str) for piece in pieces):
        raise ValueError('Duration source text is not authored string content')
    return sum(map(len, pieces))


def stage_pool(corpus):
    rows = []
    for path, raw in sorted(corpus.items()):
        data = json.loads(raw)
        threshold = int(data.get('reference_stage', data.get('entry_stage', 0)))
        for node in data['nodes']:
            if node['stage'] != 4 or (threshold > 0 and node['stage'] >= threshold):
                continue
            rows.append({'id': node['id'], 'domain': data['id'], 'file': path,
                         'characters': character_count(node),
                         'authored_minutes_present': 'minutes' in node})
    if len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Duplicate stage-4 source lesson')
    return sorted(rows, key=lambda row: row['id'])


def estimate(rows):
    target = [row for row in rows if row['id'] == LESSON]
    if len(target) != 1 or target[0]['authored_minutes_present']:
        raise ValueError('Number theory duration is not a unique derived estimate')
    total = sum(row['characters'] for row in rows)
    if not total:
        raise ValueError('Stage-4 general pool is empty')
    ratio = Fraction(target[0]['characters'] * len(rows), total)
    ratio = min(Fraction(3, 2), max(Fraction(1, 2), ratio))
    unrounded = 1680 * ratio
    return {'pool_count': len(rows), 'pool_character_sum': total,
            'average_characters_numerator': total, 'average_characters_denominator': len(rows),
            'lesson_characters': target[0]['characters'], 'stage_default_minutes': 1680,
            'clamped_ratio_numerator': ratio.numerator, 'clamped_ratio_denominator': ratio.denominator,
            'unrounded_minutes_numerator': unrounded.numerator, 'unrounded_minutes_denominator': unrounded.denominator,
            'rounded_minutes': max(5, round(unrounded / 5) * 5)}


def derive(corpus):
    from tools.fluids_runtime_compatibility import before_fluids_bytes
    if PHYSICS not in corpus:
        raise ValueError('Physics source absent from duration corpus')
    previous = dict(corpus)
    previous[PHYSICS] = before_fluids_bytes(PHYSICS, corpus[PHYSICS])
    current, prior = stage_pool(corpus), stage_pool(previous)
    current_ids = [row['id'] for row in current]
    if current_ids != [row['id'] for row in prior]:
        raise ValueError('Counterfactual changes the stage-4 general pool')
    changed = [{'id': a['id'], 'before_characters': b['characters'], 'after_characters': a['characters']}
               for a, b in zip(current, prior, strict=True) if a != b]
    if {row['id'] for row in changed} != {'phys.4.fluids'}:
        raise ValueError('Counterfactual changes content outside reviewed fluids')
    return {'current_input_sha256': {path: sha(raw) for path, raw in sorted(corpus.items())},
            'previous_physics_sha256': sha(previous[PHYSICS]), 'current_stage4_general_rows': current,
            'previous_stage4_general_rows': prior, 'changed_content_counts': changed,
            'current_estimate': estimate(current), 'previous_estimate': estimate(prior)}


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('Number theory duration counterfactual proof changed')
    proof = json.loads(raw)
    if (proof['lesson_id'] != LESSON or proof['historical_node_semantic_sha256'] != HISTORICAL_SEMANTIC
            or proof['current_minutes'] != 1075 or proof['historical_minutes'] != 1080
            or proof['counterfactual_source_paths'] != [PHYSICS]
            or proof['test_source_inverse']['path'] != TEST_PATH
            or any(proof[field] is not False for field in ['product_pacing_changed', 'math_content_changed', 'historical_approval_extended'])):
        raise ValueError('Duration counterfactual leaves its exact scope')
    return proof


def historical_number_theory_duration(lesson, corpus=None):
    proof = reviewed()
    from tools.fluids_runtime_compatibility import PROOF_SHA as fluids_pin
    if fluids_pin != proof['fluids_inverse_sha256']:
        raise ValueError('Reviewed fluids inverse changed')
    curriculum_source = (ROOT / 'primer/curriculum.py').read_bytes()
    if sha(curriculum_source) != proof['curriculum_algorithm_sha256']:
        raise ValueError('Product duration algorithm changed')
    corpus = current_corpus() if corpus is None else corpus
    hashes = {path: sha(raw) for path, raw in sorted(corpus.items())}
    if hashes != proof['derivation']['current_input_sha256']:
        raise ValueError('Unreviewed duration source corpus change')
    calculated = derive(corpus)
    if calculated != proof['derivation']:
        raise ValueError('Independent duration counterfactual differs')
    if (calculated['current_estimate']['rounded_minutes'] != proof['current_minutes']
            or calculated['previous_estimate']['rounded_minutes'] != proof['historical_minutes']):
        raise ValueError('Derived durations do not match the exact historical comparison')
    if semantic(lesson) not in {proof['current_node_semantic_sha256'], HISTORICAL_SEMANTIC}:
        raise ValueError('Unreviewed number theory lesson change')
    result = copy.deepcopy(lesson)
    result['minutes'] = calculated['previous_estimate']['rounded_minutes']
    if semantic(result) != HISTORICAL_SEMANTIC:
        raise ValueError('Duration inverse changes unrelated number theory fields')
    return result


def before_duration_test_bytes(relative, raw):
    if str(relative) != TEST_PATH:
        return raw
    row = reviewed()['test_source_inverse']
    if sha(raw) in {row['before_sha256'], row['earlier_oracle_sha256']}:
        return raw
    if sha(raw) != row['after_sha256']:
        raise ValueError('Unreviewed number theory duration test-source change')
    text = raw.decode()
    for change in reversed(row['changes']):
        if text.count(change['after']) != 1:
            raise ValueError('Duration test inverse literal is not unique')
        text = text.replace(change['after'], change['before'], 1)
    restored = text.encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('Duration test inverse changes prior oracle bytes')
    return restored
