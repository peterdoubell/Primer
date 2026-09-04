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


def test_settings_strings_and_domain_keys_are_bounded(tmp_path):
    """`SettingsIn` was the one client-writable model with no ceiling.

    Every other bounded field in server.py has one — ProfileIn.name 60,
    TutorIn.title 300, CheckIn.answer 2000 — but `theme`, `name_pronunciation`
    and `domain_stage` had none, and settings are persisted straight into the
    profile row, so an 8 MB string was an 8 MB row for as long as the reader
    kept the book. `domain_stage` is bounded by checking its keys against the
    real fields rather than by counting them: a cap of thirty-two keys still
    admits thirty-two keys of a megabyte each.
    """
    import primer.server as srv
    from primer.learner import LearnerStore
    from primer.wiki import WikiService
    from fastapi.testclient import TestClient

    orig = srv.learner, srv.wiki, srv.BACKUP_DIR
    try:
        db = str(tmp_path / "test.db")
        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        srv.BACKUP_DIR = str(tmp_path / "backups")
        with TestClient(srv.app) as c:
            c.post("/api/profile", json={
                "name": "Ada", "age": 11, "hours_per_week": 6,
                "breadth": "balanced", "domains": ["math"]})

            assert c.post("/api/profile/settings",
                          json={"theme": "x" * 5000}).status_code == 422
            assert c.post("/api/profile/settings",
                          json={"name_pronunciation": "a" * 5000}).status_code == 422
            assert c.post("/api/profile/settings",
                          json={"domain_stage": {"n" * 100000: 3}}).status_code == 422

            ok = c.post("/api/profile/settings",
                        json={"theme": "dark", "domain_stage": {"math": 3}})
            assert ok.status_code == 200
            assert ok.json()["settings"]["domain_stage"]["math"] == 3
    finally:
        srv.learner, srv.wiki, srv.BACKUP_DIR = orig
