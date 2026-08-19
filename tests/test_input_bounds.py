"""Bounds on client-controlled grading input and numeric parsing."""

import pytest
from pydantic import ValidationError

from primer import quiz
from primer.server import AttemptIn, CheckIn, PlacementSubmitIn, QuizSubmitIn


@pytest.mark.parametrize(
    "build",
    [
        lambda answer: CheckIn(token="token", id=0, answer=answer),
        lambda answer: AttemptIn(node_id="math.0.counting", answers=[answer]),
        lambda answer: QuizSubmitIn(
            node_id="math.0.counting", token="token", answers=[answer]),
        lambda answer: PlacementSubmitIn(
            domain="math", stage=0, token="token", answers=[answer]),
    ],
)
def test_grading_answers_have_a_length_limit(build):
    with pytest.raises(ValidationError):
        build("9" * 2001)


def test_numeric_fraction_parser_uses_plain_integer_parts():
    assert quiz._numeric_equal("1/2", "0.5") is True
    assert quiz._numeric_equal("-3/4", "-0.75") is True
    assert quiz._numeric_equal("--3/4", "-0.75") is None
    assert quiz._numeric_equal("1/0", "0") is None
