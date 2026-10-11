"""Equivalent residues grade exactly, without executing arbitrary expressions."""
from fractions import Fraction
import pytest

from primer.quiz import _numeric_equal, cards_from_missed, score_quiz
from primer.rational_complex import parse_rational_complex


@pytest.mark.parametrize('answer', ['1/(2i)', '-i/2', '−i/2', '-0.5i', '(-1/2)i',
                                   '-5e-1*i', '1/(2*i)', ' - i / 2 ', '-0.5j'])
def test_residue_equivalents_score_and_do_not_create_wrong_answer_cards(answer):
    question = {'kind': 'numeric', 'prompt': 'Give the residue at i of 1/(z²+1).',
                'answer': '1/(2i)', 'ephemeral': False}
    assert parse_rational_complex(answer) == (Fraction(0), Fraction(-1, 2))
    assert score_quiz([question], [answer])['score'] == 1
    assert cards_from_missed([question], [answer]) == []


@pytest.mark.parametrize('answer', ['i/2', '-1/2', '0.5', 'i', '1/(0i)', 'i**2',
                                   '__import__("os").system("true")', 'NaN*i', 'Infinity*i',
                                   '1e999999999i', '(' * 100 + 'i' + ')' * 100,
                                   '1'*257, 'ii', '3 4i', '1/(2i) trailing'])
def test_wrong_or_unbounded_or_executable_answers_are_rejected(answer):
    assert _numeric_equal(answer, '1/(2i)') is False


def test_complex_arithmetic_is_exact_and_real_grading_is_unchanged():
    assert parse_rational_complex('(1+2i)/(1-2i)') == (Fraction(-3, 5), Fraction(4, 5))
    assert parse_rational_complex('(0.1+0.2)i') == (Fraction(0), Fraction(3, 10))
    assert _numeric_equal('1/2', '0.5') is True
    assert _numeric_equal('0.5000001', '0.5') is True
    assert _numeric_equal('1/2', 'two equal parts') is None
    assert _numeric_equal('i', 'point') is None
    assert score_quiz([{'kind': 'choice', 'answer': 'I'}], ['1i'])['score'] == 0
    assert score_quiz([{'kind': 'choice', 'answer': 'I'}], ['i'])['score'] == 1
