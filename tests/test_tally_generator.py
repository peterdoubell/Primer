"""The `tally` question kind: counting answered by touching, graded as a number.

Two things are being pinned down here. The first is that the item is honest —
what is drawn is what is asked for, so a child who counts the objects in front
of her and commits that count is right by construction. The second is that the
new gesture cost the marking scheme nothing: a tally answer is a digit string,
so it runs through `quiz._numeric_equal` exactly as a typed number does, and
neither `quiz.score_quiz` nor `/api/quiz/check` needed a clause for it. That
second claim is the reason this file exists — a fourth answering shape that
required a fourth grading path would be a much larger change than it looks.
"""

import os
import sys

import pytest
from starlette.requests import Request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer import practice, quiz

# A cookie-less request, for calling an endpoint function directly rather than
# through TestClient — current_reader() reads no cookie from this and so
# resolves to reader_id=1, same as any request that predates Google sign-in.
_ANON_REQUEST = Request(scope={"type": "http", "headers": []})


def _tally_items(n=24, level=1):
    """Items as the server draws them — deduplicated and stamped with `gen`."""
    return practice.generate_set("count-tally", n, level=level)


def _raw(n=300, level=1):
    """Straight from the generator. `generate_set` deduplicates on
    (prompt, answer), so it can only ever hand back as many items as there are
    distinct combinations — no way to take a large random sample through it."""
    return [practice.g_count_tally(level) for _ in range(n)]


# ---------------- the item itself ----------------

def test_the_generator_is_registered_under_its_key():
    assert "count-tally" in practice.GENERATORS
    assert "count-tally" in practice.list_generators()
    assert practice.GENERATORS["count-tally"] is practice.g_count_tally


def test_items_are_well_formed_across_the_range():
    """Well-formed at every level the book might ask for, not just level 1."""
    for level in range(6):
        items = _tally_items(12, level=level)
        assert items, "no items at level {}".format(level)
        for q in items:
            assert q["kind"] == "tally"
            assert q["prompt"].strip()
            assert q["say"].strip()
            assert q["explain"].strip()
            assert q["ephemeral"] is True
            assert q["gen"] == "count-tally"
            # Nothing to read and nothing to type: the objects are the answer
            # surface, so a tally must never arrive carrying choices.
            assert "choices" not in q


def test_the_count_always_matches_the_objects_drawn():
    """The one invariant a child can catch the book breaking.

    She counts what is on the card. If the key disagrees with what is drawn,
    the book marks correct counting wrong — the precise failure this kind
    exists to remove.
    """
    for q in _raw(400):
        assert q["items"], "a tally with nothing to touch"
        assert len(q["items"]) == int(q["answer"])
        # One kind of thing per card. Counting a mixed handful is a different
        # (harder) task, and the spoken prompt names a single noun.
        assert len(set(q["items"])) == 1


def test_the_range_is_countable_but_worth_counting():
    seen = set()
    for q in _raw(400):
        n = int(q["answer"])
        assert 3 <= n <= 9, "n={} is outside the touchable range".format(n)
        seen.add(n)
    assert len(seen) >= 4, "the range barely varies: {}".format(sorted(seen))


def test_the_spoken_prompt_never_reads_the_answer_aloud():
    """`say` is played automatically for a pre-reader. Saying the count would
    hand her the answer before she has touched a single object."""
    for q in _raw(200):
        assert q["answer"] not in q["say"]
        assert q["answer"] not in q["prompt"]


def test_the_generator_varies_its_objects():
    things = {q["items"][0] for q in _raw(200)}
    assert len(things) >= 3, "every card draws the same thing: {}".format(things)


def test_a_tally_never_becomes_a_review_card():
    """A generated instance is not a fact to recall.

    The count is freshly randomised per instance while the prompt is fixed
    boilerplate, so a card minted from one would bind a permanent front to
    whichever number that single sitting happened to draw.
    """
    items = _tally_items(8)
    cards = quiz.cards_from_missed(items, ["1"] * len(items), "math.0.counting", "")
    assert cards == []
    # And directly: the item declares itself, rather than being classified by
    # how its prompt happens to read.
    for q in items:
        assert quiz.is_ephemeral_prompt(q["prompt"], q["kind"], q.get("ephemeral"),
                                        q.get("gen", ""), q.get("level", 0)) is True
    assert "count-tally" not in practice.DURABLE_GENERATORS


# ---------------- grading, through the path that already exists ----------------

def test_a_tally_answer_is_graded_by_value_not_by_kind():
    """The whole point: `quiz.py` needs no clause for `tally`.

    `score_quiz` sends everything that is not `short` through `_numeric_equal`,
    and a committed tally is the number of tokens the reader caught. So the
    marking is the numeric one — including the tolerant forms the client might
    send ('5', ' 5 ', '5.0') — with no new code anywhere in the scorer.
    """
    for q in _raw(40):
        n = int(q["answer"])
        assert quiz.score_quiz([q], [str(n)])["score"] == 1.0
        assert quiz.score_quiz([q], [" {} ".format(n)])["score"] == 1.0
        assert quiz.score_quiz([q], ["{}.0".format(n)])["score"] == 1.0
        # Miscounted by one — the ordinary childhood error — must be wrong.
        assert quiz.score_quiz([q], [str(n - 1)])["score"] == 0.0
        assert quiz.score_quiz([q], [str(n + 1)])["score"] == 0.0
        # An empty commit is not a zero.
        assert quiz.score_quiz([q], [""])["score"] == 0.0


def test_grading_really_travels_through_numeric_equal():
    """Asserting the route, not just the verdict.

    A tally could pass the checks above through the case-insensitive string
    fallback and nobody would notice — until the client sent '5.0' or a future
    answer carried a space. Spy on `_numeric_equal` to confirm the numeric
    comparison is what decides a tally.
    """
    q = _tally_items(1)[0]
    calls = []
    real = quiz._numeric_equal

    def spy(given, expected):
        out = real(given, expected)
        calls.append((given, expected, out))
        return out

    quiz._numeric_equal = spy
    try:
        assert quiz.score_quiz([q], [q["answer"]])["score"] == 1.0
    finally:
        quiz._numeric_equal = real
    assert calls and calls[-1][2] is True, \
        "a tally was marked by string comparison, not by value: {}".format(calls)


# ---------------- end to end, over the wire ----------------

@pytest.fixture(scope="module")
def srv(tmp_path_factory):
    """The server module pointed at a throwaway database.

    The reader's real record is never opened: the module's own service factory
    is rebuilt against a temp path, and the originals are put back afterwards
    (reassigned, not reconstructed, so the real database is not touched on the
    way out either).
    """
    import primer.server as server
    saved = (server.wiki, server.curr, server.learner, server.STORY)
    server.init_services(str(tmp_path_factory.mktemp("tallydb") / "test.db"))
    yield server
    server.wiki, server.curr, server.learner, server.STORY = saved


def test_the_check_endpoint_marks_a_tally_with_no_change_to_the_server(srv):
    """`/api/quiz/check` grades a tally today, unmodified.

    The endpoint scores with `score_quiz([q], [locked])["score"] >= 1.0`, which
    is kind-agnostic below `short`. This exercises the real commit-then-reveal
    path — the one the tally's single big button will post to — so the client
    work in a later round has a graded item waiting for it.
    """
    q = _tally_items(1)[0]
    n = int(q["answer"])

    # A paper with no subject, so nothing here can burn an item or touch a node.
    token = srv._remember([q], "practice", "", 1)
    right = srv.check_one(srv.CheckIn(token=token, id=q["id"], answer=str(n)),
                          _ANON_REQUEST)
    assert right["correct"] is True
    assert right["answer"] == str(n)

    token = srv._remember([q], "practice", "", 1)
    wrong = srv.check_one(srv.CheckIn(token=token, id=q["id"], answer=str(n + 1)),
                          _ANON_REQUEST)
    assert wrong["correct"] is False


def test_the_served_copy_carries_the_objects_but_not_the_key(srv):
    """What the renderer will actually receive.

    `_public` strips the answer key; it passes unknown fields through untouched,
    which is what lets a new kind ship its own payload without a server change.
    The tokens to draw must survive that trip — they are the question.
    """
    q = _tally_items(1)[0]
    pub = srv._public([q])[0]
    assert pub["kind"] == "tally"
    assert pub["items"] == q["items"]
    assert pub["prompt"] and pub["say"]
    assert "answer" not in pub and "explain" not in pub
    # The count is not a separate field — it is how many things were drawn, so
    # a renderer that counts presses is comparing against the same number the
    # book is holding.
    assert len(pub["items"]) == int(q["answer"])
