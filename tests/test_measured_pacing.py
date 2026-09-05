"""The roadmap is priced from this reader's rate, not only from the model.

Several audited rounds named the same structure: every node costs a stage
constant scaled by prose density, so the plan was a model of how long a node
takes *somebody*. A reader who had consistently taken half the modelled time
still saw the model's years, and a reader taking twice as long saw a promise
their own record already said they would miss.

The first attempt at this failed in two ways worth keeping written down, both
found by audit rather than by test:

  * It divided recorded reading minutes by the node's *mastery* total — reading
    plus practice plus quizzing plus review. Those are different quantities and
    not close: about 478 modelled minutes per linked article against the book's
    own six. Every reader came out at the floor and the function reported
    `measured: True` over a constant.
  * `reading_log.seconds` was never written by anything. The column that says
    how long this reader reads had been zero for every row ever inserted, so
    the whole term was a per-reader correction wired to nothing — the same
    defect the roadmap call site had with `deck`, one layer down.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer import pacing  # noqa: E402


def _graph(n=60, minutes=100):
    return {"domains": [{"id": "d", "name": "D"}],
            "nodes": [{"id": "n%d" % i, "domain": "d", "stage": 1,
                       "minutes": minutes, "articles": ["A%d" % i]}
                      for i in range(n)]}


def _reading(n, per_article):
    return {"A%d" % i: float(per_article) for i in range(n)}


def test_an_unmeasured_reader_gets_the_model_exactly():
    g = _graph()
    for reading in (None, {}, _reading(10, 30)):
        rate = pacing.instructional_rate(g, reading)
        assert rate["factor"] == 1.0
        assert rate["measured"] is False


def test_a_reader_at_the_books_own_figure_scores_one():
    """Six minutes an article is what the book tells the reader an article
    takes. A reader who reads at exactly that must not move their own plan."""
    rate = pacing.instructional_rate(_graph(), _reading(60, 6))
    assert rate["measured"] is True and rate["clamped"] is False
    assert rate["factor"] == 1.0
    assert rate["per_article"] == 6.0


def test_a_slower_reader_is_measured_as_slower():
    rate = pacing.instructional_rate(_graph(), _reading(60, 9))
    assert rate["measured"] is True and rate["clamped"] is False
    assert rate["factor"] == 1.5


def test_a_faster_reader_is_measured_as_faster():
    rate = pacing.instructional_rate(_graph(), _reading(60, 4.5))
    assert rate["measured"] is True and rate["clamped"] is False
    assert rate["factor"] == 0.75


def test_a_clamped_value_says_so():
    """A number that hit a bound is a bound, not a measurement."""
    # Enough articles and enough minutes to be a rate, at a quarter of the
    # modelled pace — measured, and then held at the floor.
    low = pacing.instructional_rate(_graph(200), _reading(200, 1.5))
    assert low["factor"] == pacing.RATE_FLOOR and low["clamped"] is True
    high = pacing.instructional_rate(_graph(), _reading(60, 60))
    assert high["factor"] == pacing.RATE_CEIL and high["clamped"] is True


def test_the_ordinary_reader_is_not_at_a_bound():
    """The first version put every real reader on the floor. A rate whose only
    output is a constant is not a rate."""
    for per_article in (4.0, 5, 6, 7.5, 9, 10):
        rate = pacing.instructional_rate(_graph(), _reading(60, per_article))
        assert rate["clamped"] is False, per_article


def test_a_thin_sample_is_not_a_rate():
    g = _graph()
    assert pacing.instructional_rate(g, _reading(10, 90))["measured"] is False
    assert pacing.instructional_rate(g, _reading(60, 1))["measured"] is False


def test_reading_off_the_curriculum_does_not_move_the_plan():
    """Wiki-wandering is real reading, but it is not the reading the plan
    prices, and letting it in moves an estimate with time never asked for."""
    g = _graph()
    off = {"Some other article %d" % i: 40.0 for i in range(30)}
    assert pacing.instructional_rate(g, off)["measured"] is False
    mixed = dict(off)
    mixed.update(_reading(60, 6))
    rate = pacing.instructional_rate(g, mixed)
    assert rate["articles"] == 60 and rate["factor"] == 1.0


def test_the_roadmap_moves_with_the_measured_rate():
    """The point of the whole exercise: the plan changes."""
    g = {"domains": [{"id": "d", "name": "D"}],
         "nodes": [{"id": "n%d" % i, "domain": "d", "stage": 1, "minutes": 900,
                    "articles": ["A%d" % i]} for i in range(400)]}
    profile = {"breadth": "balanced", "hours_per_week": 10, "stage": 0}
    mastery = {"n%d" % i: (1.0 if i < 20 else 0.0) for i in range(400)}

    modelled = pacing.roadmap(profile, g, mastery)
    # Sixty articles at 4.5 minutes is 270 minutes — over the four-hour
    # minimum; forty at 4.5 was 180, below it, and "fast" silently became
    # "unmeasured", which is the exact thing the threshold exists to do.
    slow = pacing.roadmap(profile, g, mastery, reading=_reading(60, 9))
    fast = pacing.roadmap(profile, g, mastery, reading=_reading(60, 4.5))

    assert modelled["instructional_rate"]["measured"] is False
    assert slow["instructional_rate"]["measured"] is True
    assert fast["total_hours"] < modelled["total_hours"] < slow["total_hours"]
    assert fast["hours_for_ten_years"] <= slow["hours_for_ten_years"]


def test_the_maintenance_half_is_not_scaled_twice():
    """SRS minutes already carry their own per-reader term."""
    g = {"domains": [{"id": "d", "name": "D"}],
         "nodes": [{"id": "n%d" % i, "domain": "d", "stage": 1, "minutes": 100,
                    "articles": ["A%d" % i]} for i in range(40)]}
    profile = {"breadth": "balanced", "hours_per_week": 10, "stage": 0}
    mastery = {"n%d" % i: (1.0 if i < 20 else 0.0) for i in range(40)}
    r = pacing.roadmap(profile, g, mastery, reading=_reading(40, 9))
    per_node = 100 + 6 * (r["instructional_rate"]["factor"] - 1) + r["srs_minutes_per_node"]
    assert abs(r["total_hours"] - (20 * per_node) / 60) < 1.0
