"""Regression tests for the Primer.

Covers the things that would silently break a multi-year deployment: the HTML
sanitizer (untrusted encyclopedia content reaches the DOM), the SSRF allowlist,
SM-2 scheduling, the mastery model's spaced-pass rule, pacing arithmetic,
curriculum graph integrity, and quiz/practice generation quality.

Run:  .venv/bin/python -m pytest tests/ -q
"""

import os
import re
import shutil
import subprocess
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer import practice, quiz  # noqa: E402
from primer.curriculum import (  # noqa: E402
    Curriculum, LESSON_ILLUSTRATION_DIMENSIONS, PHYSICS_MODEL_SCENARIOS,
    _validate_lesson_media,
)
from primer.learner import LearnerStore, MASTERY_MIN_INTERVAL  # noqa: E402
from primer.pacing import roadmap  # noqa: E402
from primer.render import rewrite_article, sanitize  # noqa: E402
from primer.wiki import WikiService  # noqa: E402


@pytest.fixture
def open_assessment_gate(monkeypatch):
    """Let paper-quality tests sample arbitrary stages without changing gates.

    Curriculum-lock behavior is covered by dedicated API regressions; the tests
    using this fixture measure only paper composition and answer-bank quality.
    """
    import primer.server as srv
    monkeypatch.setattr(srv, "_locked_lesson_response", lambda node, reader_id: None)


# ---------------- security: HTML sanitizer ----------------

XSS_VECTORS = [
    '<img src=x onerror=alert(1)>',
    "<img src=x onerror='alert(1)'>",
    '<img src=x onerror=alert(1) >',
    '<svg onload=alert(1)></svg>',
    '<svg><script>alert(1)</script></svg>',
    '<iframe src="//evil.com"></iframe>',
    '<object data="evil.swf"></object>',
    '<details ontoggle=alert(1)>x</details>',
    '<a href="javascript:alert(1)">click</a>',
    '<a href="JaVaScRiPt:alert(1)">click</a>',
    '<a href="data:text/html;base64,PHNjcmlwdD4=">click</a>',
    '<p onclick=alert(1)>hi</p>',
    '<form action="//evil.com"><input name=p></form>',
    '<math><mtext><script>alert(1)</script></mtext></math>',
    '<body onload=alert(1)>',
    '<style>*{background:url(javascript:alert(1))}</style>',
    '<video onerror=alert(1)><source></video>',
]

BANNED = ('onerror', 'onload', 'ontoggle', 'onclick', 'javascript:', '<script',
          '<svg', '<iframe', '<object', '<form', '<style', '<math', '<video')


@pytest.mark.parametrize('payload', XSS_VECTORS)
def test_sanitizer_blocks_xss(payload):
    out = rewrite_article(payload).lower()
    for bad in BANNED:
        assert bad not in out, 'leaked {!r} from {!r}: {}'.format(bad, payload, out)


def test_sanitizer_keeps_legitimate_content():
    html = ('<p>Water is <b>H<sub>2</sub>O</b>.</p>'
            '<ul><li>One</li><li>Two</li></ul>'
            '<table><tr><td>cell</td></tr></table>')
    out = rewrite_article(html)
    assert '<b>' in out and '<sub>' in out and '<li>' in out and '<td>' in out
    assert 'Water is' in out


def test_wikilinks_become_in_book_navigation():
    out = rewrite_article('<a href="/wiki/Photosynthesis">photosynthesis</a>')
    assert 'data-primer-title="Photosynthesis"' in out
    assert 'primer-wikilink' in out


def test_images_route_through_proxy():
    out = rewrite_article('<img src="https://upload.wikimedia.org/x.jpg" alt="a leaf">')
    assert '/api/image?url=' in out
    assert 'alt="a leaf"' in out


def test_sanitize_escapes_bare_text():
    assert '<script' not in sanitize('<script>alert(1)</script>').lower()


# ---------------- security: SSRF allowlist ----------------

@pytest.mark.parametrize('url,allowed', [
    ('https://upload.wikimedia.org/a/b.jpg', True),
    ('https://thumb.wikimedia.org/a/b.jpg', True),
    ('https://en.wikipedia.org/x.png', True),
    ('https://commons.wikimedia.org/y.svg', True),
    ('http://169.254.169.254/x.wikipedia.org/', False),
    ('http://169.254.169.254/latest/meta-data/', False),
    ('https://evil.com/a.wikipedia.org/x', False),
    ('https://thumb.wikimedia.org.evil.com/x', False),
    ('https://wikipedia.org.evil.com/x', False),
    ('http://localhost:8747/api/state', False),
    ('http://127.0.0.1/', False),
    ('file:///etc/passwd', False),
    ('ftp://upload.wikimedia.org/x', False),
])
def test_image_host_allowlist(url, allowed):
    assert WikiService._image_host_allowed(url) is allowed


# ---------------- learner: mastery model ----------------

@pytest.fixture
def store(tmp_path):
    return LearnerStore(str(tmp_path / 'test.db'))


def test_single_perfect_quiz_does_not_master(store):
    """One lucky quiz right after reading is not mastery."""
    r = store.record_attempt('n1', 1.0)
    assert r['mastered'] is False
    assert r['newly_mastered'] is False


def test_two_passes_too_close_together_do_not_master(store):
    store.record_attempt('n1', 1.0)
    r = store.record_attempt('n1', 1.0)
    assert r['mastered'] is False, 'same-session repeats must not confer mastery'


def test_two_spaced_passes_confer_mastery(store):
    store.record_attempt('n1', 1.0)
    # backdate the first pass beyond the required interval
    with store._conn() as c:
        c.execute('UPDATE mastery SET first_pass_at=? WHERE node_id=?',
                  (time.time() - MASTERY_MIN_INTERVAL - 10, 'n1'))
    r = store.record_attempt('n1', 1.0)
    assert r['mastered'] is True and r['newly_mastered'] is True
    assert 'n1' in store.mastered_set()


def test_failing_scores_never_master(store):
    for _ in range(6):
        store.record_attempt('n2', 0.3)
    assert 'n2' not in store.mastered_set()


def test_gate_map_caps_unmastered_below_gate(store):
    store.record_attempt('n3', 1.0)  # high level, not yet mastered
    assert store.gate_map()['n3'] < 0.8, 'unmastered node must not open gates'


def test_assumed_credit_is_flagged_and_unproven(store):
    store.seed_assumed(['a1', 'a2'])
    assert store.mastered_count() == 2
    assert store.proven_count() == 0, 'placement credit is not proof'


def test_real_attempt_supersedes_assumed_only_once_earned(store):
    """Placement credit is replaced by proof only after two genuinely spaced
    passes — a single quiz does not convert 'assumed' into 'proven'."""
    store.seed_assumed(['a1'])
    store.record_attempt('a1', 1.0)
    assert store.proven_count() == 0, 'one un-spaced pass is not proof'
    with store._conn() as c:
        c.execute('UPDATE mastery SET first_pass_at=? WHERE node_id=?',
                  (time.time() - MASTERY_MIN_INTERVAL - 10, 'a1'))
    store.record_attempt('a1', 1.0)
    assert store.proven_count() == 1, 'two spaced passes convert it to proven'


# ---------------- learner: SM-2 ----------------


def all_due(store):
    """Make every card due now.

    Cards are minted due a few minutes out, so that writing one and grading it
    in the same breath is not a memory test. Tests that add a card and review it
    immediately have to step over that delay.
    """
    with store._conn() as c:
        c.execute('UPDATE srs_cards SET due=?', (time.time() - 1,))


def make_due(store, cid):
    """Wind a card's clock forward so it is due again.

    Reviewing pays only when a card is actually due, so a test that drills one
    card has to let time pass — otherwise it is testing the anti-farming guard,
    not SM-2.
    """
    with store._conn() as c:
        c.execute('UPDATE srs_cards SET due=? WHERE id=?', (time.time() - 1, cid))


def test_sm2_interval_progression(store):
    store.add_cards([{'front': 'f', 'back': 'b', 'node_id': 'n'}])
    all_due(store)
    cid = store.due_cards()[0]['id']
    assert store.review_card(cid, 5)['next_days'] == 1
    make_due(store, cid)
    assert store.review_card(cid, 5)['next_days'] == 6
    make_due(store, cid)
    assert store.review_card(cid, 5)['next_days'] > 6


def test_sm2_lapse_resets_and_penalizes_ef(store):
    """A lapse restarts the card and makes it *easier* (smaller EF → shorter
    intervals), so a card you keep failing stops returning like an easy one."""
    store.add_cards([{'front': 'f', 'back': 'b', 'node_id': 'n'}])
    all_due(store)
    cid = store.due_cards()[0]['id']
    store.review_card(cid, 5)
    make_due(store, cid)
    store.review_card(cid, 5)
    make_due(store, cid)
    with store._conn() as c:
        ef_before = c.execute('SELECT ef FROM srs_cards WHERE id=?', (cid,)).fetchone()[0]
    store.review_card(cid, 0)  # blank
    with store._conn() as c:
        row = c.execute('SELECT ef, reps, lapses FROM srs_cards WHERE id=?', (cid,)).fetchone()
    assert row[1] == 0 and row[2] == 1, 'a lapse restarts the card'
    assert row[0] < ef_before, 'repeated failures must shorten future intervals'
    assert row[0] >= 1.3, 'EF floor still respected'


def test_leech_card_does_not_return_like_an_easy_one(store):
    """Regression: three failures then three successes must not schedule the
    card as far out as a card that was never failed."""
    store.add_cards([{'front': 'leech', 'back': 'b', 'node_id': 'n'},
                     {'front': 'easy', 'back': 'b', 'node_id': 'n'}])
    all_due(store)
    cards = {c['front']: c['id'] for c in store.due_cards()}
    for _ in range(3):
        store.review_card(cards['leech'], 0)
    leech_days = [store.review_card(cards['leech'], 4)['next_days'] for _ in range(3)][-1]
    easy_days = [store.review_card(cards['easy'], 4)['next_days'] for _ in range(3)][-1]
    assert leech_days < easy_days


def test_ef_has_floor(store):
    store.add_cards([{'front': 'f', 'back': 'b', 'node_id': 'n'}])
    all_due(store)
    cid = store.due_cards()[0]['id']
    for _ in range(15):
        store.review_card(cid, 3)
    with store._conn() as c:
        ef = c.execute('SELECT ef FROM srs_cards WHERE id=?', (cid,)).fetchone()[0]
    assert ef >= 1.3


def test_due_queue_interleaves_topics(store):
    cards = []
    for i in range(4):
        cards.append({'front': 'a%d' % i, 'back': 'b', 'node_id': 'nodeA'})
        cards.append({'front': 'z%d' % i, 'back': 'b', 'node_id': 'nodeB'})
    store.add_cards(cards)
    all_due(store)
    seq = [c['node_id'] for c in store.due_cards(8)]
    runs = sum(1 for i in range(1, len(seq)) if seq[i] == seq[i - 1])
    assert runs < len(seq) - 2, 'due cards should not come in one long topic run'


def test_review_lapse_lowers_node_strength(store):
    store.seed_assumed(['nodeX'])
    store.add_cards([{'front': 'f', 'back': 'b', 'node_id': 'nodeX'}])
    all_due(store)
    cid = store.due_cards()[0]['id']
    with store._conn() as c:
        before = c.execute('SELECT strength FROM mastery WHERE node_id=?', ('nodeX',)).fetchone()[0]
    store.review_card(cid, 0)
    with store._conn() as c:
        after = c.execute('SELECT strength FROM mastery WHERE node_id=?', ('nodeX',)).fetchone()[0]
    assert after < before


# ---------------- learner: motivation ----------------

def test_xp_is_not_farmable_by_reopening_articles(store):
    for _ in range(10):
        store.log_reading('Photosynthesis')
    assert store.total_xp() == 3, 'only the first open of a title pays XP'


def test_xp_rewards_success_more_than_failure(store):
    store.record_attempt('n1', 1.0)
    high = store.total_xp()
    store.record_attempt('n2', 0.0)
    assert store.total_xp() - high < high


def test_streak_survives_a_single_missed_day(store):
    now = time.time()
    with store._conn() as c:
        for days_ago in (0, 1, 3, 4):  # day 2 missed
            c.execute("INSERT INTO events(kind,payload,at,xp) VALUES('attempt','{}',?,1)",
                      (now - days_ago * 86400,))
    assert store.streak_days() >= 4, 'a freeze should bridge one missed day'


def test_backup_creates_a_file(store, tmp_path):
    store.save_profile('R', 8, 6, 'balanced', 1, [])
    dest = store.backup(str(tmp_path / 'backups'))
    assert dest and os.path.exists(dest) and os.path.getsize(dest) > 0


# ---------------- curriculum graph ----------------

@pytest.fixture(scope='module')
def curr():
    return Curriculum()


def test_all_prereqs_resolve(curr):
    for nid, node in curr.nodes.items():
        for p in node['prereqs']:
            assert p in curr.nodes, '{} has unknown prereq {}'.format(nid, p)


def test_prereqs_never_point_upward_in_stage(curr):
    for nid, node in curr.nodes.items():
        for p in node['prereqs']:
            assert curr.nodes[p]['stage'] <= node['stage'], \
                '{} requires higher-stage {}'.format(nid, p)


def test_graph_is_acyclic_and_fully_reachable(curr):
    mastery, rounds = {}, 0
    while rounds < 60:
        rounds += 1
        newly = [n['id'] for n in curr.nodes.values()
                 if mastery.get(n['id'], 0) < 0.8 and curr.unlocked(n, mastery)]
        if not newly:
            break
        for nid in newly:
            mastery[nid] = 1.0
    assert all(mastery.get(n, 0) >= 0.8 for n in curr.nodes), 'unreachable nodes exist'


def test_every_stage_is_populated_in_every_domain(curr):
    """A domain has no gaps: whatever stage it starts at, it runs to the end.

    The ten general fields start at 0, which is the book's promise that a domain
    is something a reader travels from preschool to graduate rather than a
    subject handed to them at a level someone else chose. A domain may instead
    declare a later `entry_stage` and begin above the general spine — radiology
    is postgraduate by nature, and inventing preschool radiology to satisfy a
    structural rule would be dishonest about what the book contains. What is not
    allowed either way is a hole in the middle.
    """
    for d in curr.domains:
        stages = {n['stage'] for n in curr.nodes.values() if n['domain'] == d['id']}
        expected = set(range(d.get('entry_stage', 0), 6))
        assert stages == expected, '{} has stages {}, expected {}'.format(
            d['id'], sorted(stages), sorted(expected))


def test_a_specialist_domain_is_still_reachable(curr):
    """A domain that starts above stage 0 has no earlier stage to gate it, so
    `stage_gate_open` waves it straight through — which would make it unlocked
    from the reader's first day if nothing else stood in the way. Its nodes must
    therefore carry cross-domain prereqs, or a five-year-old is offered TAVI
    planning on the Today screen.
    """
    for d in curr.domains:
        if d.get('entry_stage', 0) == 0:
            continue
        own = [n for n in curr.nodes.values() if n['domain'] == d['id']]
        assert any(n['stage'] == d['entry_stage'] for n in own), \
            '{} declares entry_stage {} but has no node there'.format(
                d['id'], d['entry_stage'])
        for n in own:
            assert not curr.unlocked(n, {}), \
                '{} is unlocked for a reader who has mastered nothing'.format(n['id'])
        # …and the earning has to come from outside, or the domain is a closed
        # loop no reader can enter. It need not be every node: a node gated by
        # a sibling is earned through whatever that sibling required.
        roots = [n for n in own
                 if not any(curr.nodes.get(p, {}).get('domain') == d['id']
                            for p in n['prereqs'])]
        assert roots, '{} has no node reachable from outside itself'.format(d['id'])
        for n in roots:
            assert [p for p in n['prereqs']
                    if curr.nodes.get(p, {}).get('domain') != d['id']], \
                '{} is a way in with nothing to earn it'.format(n['id'])


def test_a_reference_field_is_filed_by_section(curr):
    """Eighty peer modules with no filing is a wall, not a library.

    Stages file the general spine; a specialist field has only one stage, so
    the section is the only structure its reader gets. Every module in such a
    field must carry one, and the sections must be few enough to scan.
    """
    for d in curr.domains:
        if d.get('entry_stage', 0) == 0:
            continue
        own = [n for n in curr.nodes.values() if n['domain'] == d['id']]
        missing = [n['id'] for n in own if not n.get('section')]
        assert not missing, '{} modules with no section: {}'.format(
            len(missing), missing[:5])
        # An upper bound only: a reader scans section headings, and twenty is
        # already a long scan. There is no lower bound to enforce — how many
        # sections a field needs is a fact about the field, not a rule.
        sections = {n['section'] for n in own}
        assert len(sections) <= 20, \
            '{} has {} sections'.format(d['id'], len(sections))


def test_advanced_nodes_have_authored_quizzes(curr):
    advanced = [n for n in curr.nodes.values() if n['stage'] >= 2]
    with_quiz = [n for n in advanced if n.get('quiz')]
    assert len(with_quiz) / len(advanced) >= 0.9


def test_young_nodes_have_child_voiced_lessons(curr):
    young = [n for n in curr.nodes.values() if n['stage'] <= 1]
    with_text = [n for n in young if n.get('kid_text')]
    assert len(with_text) / len(young) >= 0.9


def test_the_interactive_lesson_media_cohorts_are_local_and_complete(curr):
    """The bounded-model cohorts keep both their authored plate and model."""
    expected = {
        'math.0.counting': (0, 'counter'),
        'math.0.shapes': (0, 'shape-explorer'),
        'phys.0.light-shadow': (0, 'shadow-lab'),
        'cs.0.instructions': (0, 'sequence-runner'),
        'lang.0.alphabet': (0, 'alphabet-explorer'),
        'hist.0.family': (0, 'inclusive-family-timeline'),
        'earth.0.sky': (0, 'day-night-rotation-lab'),
        'arts.0.colors': (0, 'classroom-paint-mixer'),
        'math.1.addition': (1, 'make-ten'),
        'phys.1.light': (1, 'light-paths'),
        'cs.1.algorithms': (1, 'algorithm-tracer'),
        'bio.1.lifecycles': (1, 'life-cycle'),
        'lang.1.reading': (1, 'reading-path-lab'),
        'hist.1.timelines': (1, 'timeline-order-lab'),
        'earth.1.seasons': (1, 'seasons-tilt-lab'),
        'arts.1.elements': (1, 'art-elements-composer'),
        'math.2.fractions': (2, 'fraction-equivalence-lab'),
        'math.2.negatives': (2, 'integer-number-line-lab'),
        'chem.2.atoms': (2, 'atom-element-builder'),
        'bio.2.cells': (2, 'cell-microscope'),
        'mind.2.logic-intro': (2, 'counterexample-lab'),
        'math.3.functions': (3, 'function-composition-lab'),
        'bio.3.human-anatomy': (3, 'circulation-route-lab'),
        'mind.3.logic': (3, 'truth-table-lab'),
        'cs.3.data-structures': (3, 'stack-queue-lab'),
        'math.4.linalg': (4, 'matrix-transform-lab'),
        'phys.4.fluids': (4, 'venturi-flow-lab'),
        'bio.4.molecular': (4, 'gene-expression-stepper'),
        'cs.4.networks': (4, 'tcp-packet-tracer'),
        'math.5.pde': (5, 'heat-equation-lab'),
        'cs.5.complexity': (5, 'complexity-certificate-lab'),
        'bio.5.developmental': (5, 'morphogen-gradient-lab'),
        'rad.3.ct-image': (5, 'ct-window-lab'),
    }
    expected.update({
        node_id: (curr.nodes[node_id]['stage'], 'physics-concept-lab')
        for node_id in PHYSICS_MODEL_SCENARIOS
    })
    with_models = {
        nid: node for nid, node in curr.nodes.items()
        if any(item['kind'] == 'model' for item in node.get('lesson_media', []))
    }
    assert set(with_models) == set(expected)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for nid, node in with_models.items():
        assert node['stage'] == expected[nid][0], nid
        kinds = [entry['kind'] for entry in node['lesson_media']]
        assert kinds == ['illustration', 'model'], nid
        model = node['lesson_media'][-1]
        assert model['renderer'] == expected[nid][1]
        plate = node['lesson_media'][0]
        assert plate['alt'].strip() and plate['caption'].strip()
        assert (plate['width'], plate['height']) == (1600, 1000)
        candidate_urls = set()
        for candidate in plate['srcset'].split(','):
            url, descriptor = candidate.strip().split()
            candidate_urls.add(url)
            disk = os.path.join(root, 'web', url[len('/app/'):])
            assert os.path.isfile(disk), disk
            assert os.path.getsize(disk) < 300_000, '{} is too heavy'.format(disk)
            actual_width, actual_height = LESSON_ILLUSTRATION_DIMENSIONS[url]
            assert actual_width == int(descriptor[:-1])
            assert actual_width * plate['height'] == actual_height * plate['width']
            with open(disk, 'rb') as fh:
                header = fh.read(12)
            assert header[:4] == b'RIFF' and header[8:] == b'WEBP', disk
        assert plate['src'] in candidate_urls


def test_every_mathematics_lesson_has_one_local_responsive_illustration(curr):
    """Counting through postgraduate work has uninterrupted explanatory visuals."""
    mathematics = {
        nid: node for nid, node in curr.nodes.items() if nid.startswith('math.')
    }
    assert len(mathematics) == 59
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raster_urls = set()
    plate_ids = set()
    for nid, node in mathematics.items():
        plates = [item for item in node.get('lesson_media', [])
                  if item['kind'] == 'illustration']
        assert len(plates) == 1, nid
        plate = plates[0]
        assert plate['id'] not in plate_ids, plate['id']
        plate_ids.add(plate['id'])
        assert len(plate['alt'].split()) >= 8, nid
        assert len(plate['caption'].split()) >= 8, nid
        # The caption must add the mathematical insight; it may not merely
        # repeat the image description as decorative alt copy.
        assert plate['caption'].strip() != plate['alt'].strip(), nid
        assert (plate['width'], plate['height']) == (1600, 1000)
        candidates = {}
        for candidate in plate['srcset'].split(','):
            url, descriptor = candidate.strip().split()
            width = int(descriptor[:-1])
            assert width in (800, 1600), (nid, descriptor)
            assert url not in raster_urls, url
            raster_urls.add(url)
            disk = os.path.join(root, 'web', url[len('/app/'):])
            assert os.path.isfile(disk), disk
            assert os.path.getsize(disk) < 300_000, '{} is too heavy'.format(disk)
            actual_width, actual_height = LESSON_ILLUSTRATION_DIMENSIONS[url]
            assert (actual_width, actual_height) == (width, width * 5 // 8)
            candidates[url] = width
        assert set(candidates.values()) == {800, 1600}, nid
        assert candidates[plate['src']] == 800, nid
    assert len(raster_urls) == 118


def test_every_physics_lesson_has_explanatory_responsive_media(curr):
    """Every physics rung now carries one auditable plate and one live model."""
    physics = {nid: node for nid, node in curr.nodes.items() if nid.startswith('phys.')}
    assert len(physics) == 39
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raster_urls = set()
    plate_ids = set()
    model_ids = set()
    bespoke = {
        'phys.0.light-shadow': 'shadow-lab',
        'phys.1.light': 'light-paths',
        'phys.4.fluids': 'venturi-flow-lab',
    }
    for nid, node in physics.items():
        assert [item['kind'] for item in node.get('lesson_media', [])] == [
            'illustration', 'model'], nid
        plate, model = node['lesson_media']
        assert plate['id'] not in plate_ids, plate['id']
        assert model['id'] not in model_ids, model['id']
        plate_ids.add(plate['id'])
        model_ids.add(model['id'])
        assert len(plate['alt'].split()) >= 8, nid
        assert len(plate['caption'].split()) >= 8, nid
        assert plate['alt'].strip() != plate['caption'].strip(), nid
        assert (plate['width'], plate['height']) == (1600, 1000)
        candidates = {}
        for candidate in plate['srcset'].split(','):
            url, descriptor = candidate.strip().split()
            width = int(descriptor[:-1])
            assert width in (800, 1600), (nid, descriptor)
            assert url.startswith('/app/illustrations/') and url.endswith('.webp')
            assert url not in raster_urls, url
            raster_urls.add(url)
            disk = os.path.join(root, 'web', url[len('/app/'):])
            assert os.path.isfile(disk), disk
            assert os.path.getsize(disk) < 300_000, disk
            assert LESSON_ILLUSTRATION_DIMENSIONS[url] == (width, width * 5 // 8)
            candidates[url] = width
        assert set(candidates.values()) == {800, 1600}, nid
        assert candidates[plate['src']] == 800, nid
        if nid in PHYSICS_MODEL_SCENARIOS:
            assert model['renderer'] == 'physics-concept-lab', nid
            assert model['props'] == {'scenario': nid}, nid
        else:
            assert model['renderer'] == bespoke[nid], nid
    assert len(plate_ids) == len(model_ids) == 39
    assert len(raster_urls) == 78


def test_every_curriculum_lesson_has_one_unique_explanatory_plate():
    """The whole book, not a favoured subject subset, carries visual teaching."""
    from tools.check_curriculum_illustrations import audit

    result = audit()
    assert result['lessons'] == 432
    assert result['illustrated'] == result['lessons']
    assert result['missing'] == 0
    assert result['responsive_webps'] == result['lessons'] * 2
    assert not result['errors'], '\n'.join(result['errors'][:20])
    assert all(domain['illustrated'] == domain['lessons']
               for domain in result['domains'])


def test_physics_visual_copy_keeps_scientific_boundaries(curr):
    sound = str(curr.nodes['phys.1.sound']).lower()
    forces = str(curr.nodes['phys.2.forces']).lower()
    all_physics = (' '.join(str(node).lower() for nid, node in curr.nodes.items()
                            if nid.startswith('phys.')) + ' ' + _web('lesson-models.js').lower())
    assert 'slow big wiggles' not in sound
    assert 'speed changes pitch; size changes loudness' in sound
    assert 'slides steadily when two people' not in forces
    assert 'begins accelerating when two people' in forces
    for boundary in (
        'constant velocity—not necessarily rest',
        'changing magnetic flux',
        'individual events',
        'no real engine exceeds the carnot bound',
        'spacelike door-event order',
        'photographed trajectories',
        'faster-than-light signalling',
        'without a center',
        'air-pressure variation over time, not sideways air motion',
        'heating and sound are transfer pathways',
        'two phases can coexist',
        'one free bosonic mode',
        'one angle cannot show bell violation',
        'outer disk and excludes the galactic center',
        'makes the field transition abrupt',
        'relative density (peak = 1)',
        'fixed 24 μs axis',
        'absolute temperatures in kelvin',
        'normalized squared magnitude',
        'total kinetic energy is conserved only',
        'photon arrival-rate scale',
        'resolution/√12',
        'fusion of light nuclei and fission of heavy nuclei',
        'mean residual',
        'residual scatter',
        'axial pull/push orientation index',
        'turning index',
    ):
        assert boundary in all_physics, boundary


def test_mathematics_visual_copy_keeps_the_audited_boundary_conditions(curr):
    """Plates must not lend authority to the misconceptions found beside them."""
    def copy(node_id):
        return str(curr.nodes[node_id]).lower()

    assert 'bigger digit means colder' not in copy('math.2.negatives')
    assert '115 cm' not in copy('math.2.ratio')
    assert '11520 cm' in copy('math.2.ratio')
    assert 'sensitivity and 99% specificity' in copy('math.3.probability')
    assert 'summaries alone do not determine' in copy('math.3.statistics')
    assert 'with x measured in radians' in copy('math.3.precalc')
    assert 'ordinary improper integral diverges' in copy('math.4.int-calc')
    assert curr.nodes['math.4.complex']['goal'] == \
        'The plane where every nonconstant polynomial has a root.'
    differential_geometry = copy('math.5.diffgeo')
    assert 'positive gaussian curvature on its outer region' in differential_geometry
    assert 'vacuum can still have nonzero weyl curvature' in differential_geometry
    assert 'calculus remains essential' in differential_geometry
    assert 'the equations alone are insufficient under these weak hypotheses' in \
        copy('math.5.complex-analysis')
    frontier_plate = curr.nodes['math.5.frontier']['lesson_media'][0]
    assert frontier_plate['id'] == 'evidence-proof-counterexample-plate'
    assert 'induction chain' in frontier_plate['alt'].lower()
    assert 'finite computation' in frontier_plate['caption'].lower()
    assert 'counterexample refutes' in frontier_plate['caption'].lower()


def test_second_sprout_copy_does_not_reinforce_common_misconceptions(curr):
    """The new media must not sit beside the exact claims it is designed to fix."""
    reading = curr.nodes['lang.1.reading']
    reading_copy = (reading['goal'] + ' ' + reading['kid_text'] + ' ' +
                    ' '.join(item['explain'] for item in reading['quiz'])).lower()
    assert 'all by yourself' not in reading_copy and 'just your eyes' not in reading_copy
    assert 'braille' in reading_copy and 'other writing systems' in reading_copy
    assert 'english lines usually' in reading_copy
    spoken_reading = ' '.join(item.get('say', '') + ' ' + item['explain']
                              for item in reading['quiz']).lower()
    for schwa_sound in ('puh', 'guh', 'kuh', 'tuh'):
        assert schwa_sound not in spoken_reading

    timeline = curr.nodes['hist.1.timelines']
    timeline_copy = (timeline['kid_text'] + ' ' +
                     ' '.join(item['prompt'] + ' ' + item.get('say', '') + ' ' + item['explain']
                              for item in timeline['quiz'])).lower()
    for old_claim in ('learning to walk', 'starting school', 'first you crawl',
                      'a timeline goes from left to right'):
        assert old_claim not in timeline_copy
    assert 'timelines can also run' in timeline_copy
    assert 'this timeline' in timeline_copy and 'dates and arrows' in timeline_copy
    assert 'fifteen hundred' not in timeline_copy and '15:00' not in timeline_copy

    seasons = curr.nodes['earth.1.seasons']
    seasons_copy = (seasons['kid_text'] + ' ' +
                    ' '.join(item['prompt'] + ' ' + item['explain']
                             for item in seasons['quiz'])).lower()
    assert 'we do not move nearer' not in seasons_copy
    assert 'distance changes are not the cause' in seasons_copy
    assert 'opposite astronomical seasons' in seasons_copy
    assert 'temperate' in seasons_copy and 'other regions and cultures' in seasons_copy

    art = curr.nodes['arts.1.elements']
    art_copy = (art['kid_text'] + ' ' +
                ' '.join(item['prompt'] + ' ' + item['explain']
                         for item in art['quiz'])).lower()
    assert 'dark colors can feel gloomy' not in art_copy
    assert 'visual texture' in art_copy and 'picture itself is smooth' in art_copy
    assert 'culture and viewer' in art_copy


@pytest.mark.parametrize('bad_media', [None, {}, '', 0, False])
def test_lesson_media_schema_rejects_explicit_falsy_non_lists(bad_media):
    with pytest.raises(ValueError, match='lesson_media must be a list'):
        _validate_lesson_media({'id': 'test.0.media', 'lesson_media': bad_media})


@pytest.mark.parametrize('descriptor', ['0w', '799w', '800w,duplicate'])
def test_lesson_media_schema_rejects_invalid_srcset_widths(curr, descriptor):
    plate = dict(curr.nodes['math.0.counting']['lesson_media'][0])
    source = plate['src']
    plate['srcset'] = '{} {}'.format(source, descriptor.replace(',duplicate', ', {} 800w'.format(source)))
    with pytest.raises(ValueError, match='invalid srcset'):
        _validate_lesson_media({'id': 'test.0.srcset', 'lesson_media': [plate]})


def test_lesson_media_schema_requires_fallback_in_srcset(curr):
    plate = dict(curr.nodes['math.0.counting']['lesson_media'][0])
    plate['srcset'] = plate['srcset'].split(',')[1].strip()
    with pytest.raises(ValueError, match='src is missing from srcset'):
        _validate_lesson_media({'id': 'test.0.fallback', 'lesson_media': [plate]})


def test_lesson_media_schema_never_resolves_an_authored_path(curr):
    plate = dict(curr.nodes['math.0.counting']['lesson_media'][0])
    escaped = '/app/illustrations/../styles.css.webp'
    plate['src'] = escaped
    plate['srcset'] = escaped + ' 800w'
    with pytest.raises(ValueError, match='illustration manifest'):
        _validate_lesson_media({'id': 'test.0.path', 'lesson_media': [plate]})


def _physics_test_model(props):
    return {
        'id': 'test-physics-model', 'kind': 'model',
        'renderer': 'physics-concept-lab', 'title': 'Physics concept test',
        'instructions': 'Move the bounded scientific control.', 'props': props,
    }


def test_physics_model_props_accept_only_the_matching_lesson_scenario():
    _validate_lesson_media({
        'id': 'phys.0.push-pull',
        'lesson_media': [_physics_test_model({'scenario': 'phys.0.push-pull'})],
    })


@pytest.mark.parametrize('node_id,props', [
    ('phys.0.push-pull', {'scenario': 'phys.9.unknown'}),
    ('phys.0.push-pull', {'scenario': 'phys.1.motion'}),
    ('phys.0.push-pull', {'scenario': 'phys.0.push-pull', 'extra': True}),
    ('phys.0.push-pull', {'scenario': 7}),
    ('phys.0.push-pull', {'scenario': 'constructor'}),
    ('phys.0.light-shadow', {'scenario': 'phys.0.light-shadow'}),
])
def test_physics_model_props_reject_unknown_cross_lesson_and_bespoke_scenarios(
        node_id, props):
    with pytest.raises(ValueError, match='unknown or cross-lesson scenario'):
        _validate_lesson_media({
            'id': node_id, 'lesson_media': [_physics_test_model(props)],
        })


@pytest.mark.parametrize('renderer,props', [
    ('make-ten', {'first': True, 'second': 5}),
    ('make-ten', {'first': 5, 'second': 5}),
    ('light-paths', {'scene': 'mirror'}),
    ('life-cycle', {'species': 'frog'}),
    ('algorithm-tracer', {'scenario': 'unknown'}),
    ('fraction-equivalence-lab', {'numerator': True, 'denominator': 3, 'max_factor': 4}),
    ('fraction-equivalence-lab', {'numerator': 3, 'denominator': 3, 'max_factor': 4}),
    ('fraction-equivalence-lab', {'numerator': 1, 'denominator': 8, 'max_factor': 4}),
    ('atom-element-builder', {'protons': 0, 'neutrons': 6, 'electrons': 6}),
    ('atom-element-builder', {'protons': 6, 'neutrons': 13, 'electrons': 6}),
    ('atom-element-builder', {'protons': 6, 'neutrons': 6, 'electrons': 3}),
    ('cell-microscope', {'start_specimen': 'pond', 'start_magnification': 100}),
    ('cell-microscope', {'start_specimen': 'leaf', 'start_magnification': 200}),
    ('cell-microscope', {'start_specimen': 'leaf', 'start_magnification': True}),
    ('counterexample-lab', {'scenario': 'birds-brown'}),
    ('integer-number-line-lab', {
        'min': True, 'max': 12, 'start_value': -2, 'start_delta': -7,
    }),
    ('integer-number-line-lab', {
        'min': -12, 'max': 12.0, 'start_value': -2, 'start_delta': -7,
    }),
    ('integer-number-line-lab', {
        'min': -12, 'max': 11, 'start_value': -2, 'start_delta': -7,
    }),
    ('integer-number-line-lab', {
        'min': -12, 'max': 12, 'start_value': -2, 'start_delta': -11,
    }),
    ('integer-number-line-lab', {
        'min': -12, 'max': 12, 'start_value': -2, 'start_delta': -7,
        'step': 1,
    }),
    ('function-composition-lab', {
        'f_slope': True, 'f_intercept': 0, 'g_slope': 1, 'g_intercept': -1,
        'x_min': -5, 'x_max': 5, 'start_x': 5,
    }),
    ('function-composition-lab', {
        'f_slope': 0, 'f_intercept': 0, 'g_slope': 1, 'g_intercept': -1,
        'x_min': -5, 'x_max': 5, 'start_x': 5,
    }),
    ('function-composition-lab', {
        'f_slope': 2, 'f_intercept': 6, 'g_slope': 1, 'g_intercept': -1,
        'x_min': -5, 'x_max': 5, 'start_x': 5,
    }),
    ('function-composition-lab', {
        'f_slope': 2, 'f_intercept': 0, 'g_slope': 1, 'g_intercept': -1,
        'x_min': 5, 'x_max': 5, 'start_x': 5,
    }),
    ('function-composition-lab', {
        'f_slope': 2, 'f_intercept': 0, 'g_slope': 1, 'g_intercept': -1,
        'x_min': -5, 'x_max': 5, 'start_x': 6,
    }),
    ('circulation-route-lab', {
        'route': 'systemic', 'start_step': 0, 'show_oxygenation': True,
    }),
    ('circulation-route-lab', {
        'route': 'cardiopulmonary', 'start_step': True, 'show_oxygenation': True,
    }),
    ('circulation-route-lab', {
        'route': 'cardiopulmonary', 'start_step': 9, 'show_oxygenation': True,
    }),
    ('circulation-route-lab', {
        'route': 'cardiopulmonary', 'start_step': 0, 'show_oxygenation': 1,
    }),
    ('truth-table-lab', {'start_operator': 'xor', 'start_p': True, 'start_q': False}),
    ('truth-table-lab', {'start_operator': 'and', 'start_p': 1, 'start_q': False}),
    ('truth-table-lab', {'start_operator': 'or', 'start_p': True, 'start_q': 0}),
    ('stack-queue-lab', {'start_mode': 'deque', 'capacity': 6, 'initial_count': 3}),
    ('stack-queue-lab', {'start_mode': 'stack', 'capacity': True, 'initial_count': 0}),
    ('stack-queue-lab', {'start_mode': 'queue', 'capacity': 2, 'initial_count': 0}),
    ('stack-queue-lab', {'start_mode': 'queue', 'capacity': 8, 'initial_count': True}),
    ('stack-queue-lab', {'start_mode': 'stack', 'capacity': 3, 'initial_count': 4}),
    ('matrix-transform-lab', {'start_transform': 'rotation'}),
    ('matrix-transform-lab', {'start_transform': 'x-shear', 'matrix': [[1, 1], [0, 1]]}),
    ('venturi-flow-lab', {'scenario': 'horizontal-water-venturi', 'start_throat': 'third-area'}),
    ('venturi-flow-lab', {'scenario': 'air-venturi', 'start_throat': 'half-area'}),
    ('gene-expression-stepper', {'scenario': 'eukaryotic-met-glu-phe', 'start_gene_state': True}),
    ('gene-expression-stepper', {'scenario': 'random-codons', 'start_gene_state': 'off'}),
    ('tcp-packet-tracer', {'scenario': 'tcp-random-loss'}),
    ('tcp-packet-tracer', {'scenario': 'tcp-four-segment-loss-two', 'segments': 4}),
    ('heat-equation-lab', {
        'cells': 9, 'hot_cell': 3, 'diffusion_percent': 20, 'max_steps': 10,
    }),
    ('heat-equation-lab', {
        'cells': True, 'hot_cell': 4, 'diffusion_percent': 20, 'max_steps': 10,
    }),
    ('heat-equation-lab', {
        'cells': 9.0, 'hot_cell': 4, 'diffusion_percent': 20, 'max_steps': 10,
    }),
    ('complexity-certificate-lab', {
        'scenario': 'travelling-salesperson', 'start_n': 4, 'max_n': 20,
    }),
    ('complexity-certificate-lab', {
        'scenario': 'sat-certificate', 'start_n': 4, 'max_n': 20, 'base': 2,
    }),
    ('complexity-certificate-lab', {
        'scenario': 'sat-certificate', 'start_n': 4.0, 'max_n': 20,
    }),
    ('morphogen-gradient-lab', {
        'cells': 11, 'source': 100, 'decay_percent': 20,
        'low_threshold': 30, 'high_threshold': 64,
    }),
    ('morphogen-gradient-lab', {
        'cells': 11, 'source': True, 'decay_percent': 20,
        'low_threshold': 30, 'high_threshold': 65,
    }),
    ('morphogen-gradient-lab', {
        'cells': 11, 'source': 100.0, 'decay_percent': 20,
        'low_threshold': 30, 'high_threshold': 65,
    }),
    ('ct-window-lab', {
        'phantom': 'synthetic-hu-reference', 'level': 40, 'width': 401,
    }),
    ('ct-window-lab', {
        'phantom': 'synthetic-hu-reference', 'level': True, 'width': 400,
    }),
    ('ct-window-lab', {
        'phantom': 'synthetic-hu-reference', 'level': 40.0, 'width': 400,
    }),
    ('alphabet-explorer', {
        'alphabet': 'english-basic-latin', 'start_letter': 'a',
        'example_set': 'common-words-v1',
    }),
    ('alphabet-explorer', {
        'alphabet': 'english-basic-latin', 'start_letter': True,
        'example_set': 'common-words-v1',
    }),
    ('alphabet-explorer', {
        'alphabet': 'english-basic-latin', 'start_letter': 1.0,
        'example_set': 'common-words-v1',
    }),
    ('alphabet-explorer', {
        'alphabet': 'english-basic-latin', 'start_letter': 'A',
    }),
    ('alphabet-explorer', {
        'alphabet': 'english-basic-latin', 'start_letter': 'A',
        'example_set': 'common-words-v1', 'locale': 'en',
    }),
    ('inclusive-family-timeline', {
        'scenario': 'fictional-family-three-times', 'start_time': 'yesterday',
    }),
    ('inclusive-family-timeline', {
        'scenario': 'personal-family-three-times', 'start_time': 'today',
    }),
    ('inclusive-family-timeline', {
        'scenario': 'fictional-family-three-times', 'start_time': 'today',
        'names': ['Alex'],
    }),
    ('inclusive-family-timeline', {
        'scenario': 'fictional-family-three-times',
    }),
    ('day-night-rotation-lab', {
        'scenario': 'earth-rotation-equinox-equator',
        'start_hour': True, 'step_hours': 6,
    }),
    ('day-night-rotation-lab', {
        'scenario': 'earth-rotation-equinox-equator',
        'start_hour': 6.0, 'step_hours': 6,
    }),
    ('day-night-rotation-lab', {
        'scenario': 'earth-rotation-equinox-equator',
        'start_hour': 3, 'step_hours': 6,
    }),
    ('day-night-rotation-lab', {
        'scenario': 'earth-rotation-equinox-equator',
        'start_hour': 6, 'step_hours': True,
    }),
    ('day-night-rotation-lab', {
        'scenario': 'earth-rotation-equinox-equator',
        'start_hour': 6, 'step_hours': 6.0,
    }),
    ('day-night-rotation-lab', {
        'scenario': 'earth-rotation-equinox-equator',
        'start_hour': 6,
    }),
    ('classroom-paint-mixer', {
        'scenario': 'equal-parts-classroom-ryb',
        'start_first': 'green', 'start_second': 'yellow',
    }),
    ('classroom-paint-mixer', {
        'scenario': 'equal-parts-classroom-ryb',
        'start_first': 'blue', 'start_second': True,
    }),
    ('classroom-paint-mixer', {
        'scenario': 'equal-parts-classroom-ryb',
        'start_first': 'blue', 'start_second': 1.0,
    }),
    ('classroom-paint-mixer', {
        'scenario': 'equal-parts-classroom-ryb',
        'start_first': 'blue', 'start_second': 'yellow', 'mode': 'rgb',
    }),
    ('classroom-paint-mixer', {
        'scenario': 'equal-parts-classroom-ryb', 'start_first': 'blue',
    }),
    ('reading-path-lab', {
        'scenario': 'simple-english-cat-sat', 'start_phase': 'guess',
    }),
    ('reading-path-lab', {
        'scenario': 'simple-english-cat-sat', 'start_phase': True,
    }),
    ('reading-path-lab', {
        'scenario': 'unknown', 'start_phase': 'sounds',
    }),
    ('reading-path-lab', {
        'scenario': 'simple-english-cat-sat', 'start_phase': 'sounds',
        'sentence': 'The cat sat.',
    }),
    ('timeline-order-lab', {
        'scenario': 'fictional-library-three-dates',
        'start_order': ['opened', 'reading-room'],
    }),
    ('timeline-order-lab', {
        'scenario': 'fictional-library-three-dates',
        'start_order': ['opened', True, 'roof-restored'],
    }),
    ('timeline-order-lab', {
        'scenario': 'fictional-library-three-dates',
        'start_order': ['opened', 'opened', 'roof-restored'],
    }),
    ('timeline-order-lab', {
        'scenario': 'fictional-library-three-dates',
        'start_order': ['opened', 'reading-room', 'demolished'],
    }),
    ('timeline-order-lab', {
        'scenario': 'real-library',
        'start_order': ['opened', 'reading-room', 'roof-restored'],
    }),
    ('timeline-order-lab', {
        'scenario': 'fictional-library-three-dates',
        'start_order': ['opened', 'reading-room', 'roof-restored'],
        'locale': 'en',
    }),
    ('seasons-tilt-lab', {
        'scenario': 'earth-tilt-four-positions',
        'start_position': 'january', 'start_hemisphere': 'north',
    }),
    ('seasons-tilt-lab', {
        'scenario': 'earth-tilt-four-positions',
        'start_position': True, 'start_hemisphere': 'north',
    }),
    ('seasons-tilt-lab', {
        'scenario': 'earth-tilt-four-positions',
        'start_position': 'june-solstice', 'start_hemisphere': 'equator',
    }),
    ('seasons-tilt-lab', {
        'scenario': 'earth-tilt-four-positions',
        'start_position': 'june-solstice', 'start_hemisphere': True,
    }),
    ('seasons-tilt-lab', {
        'scenario': 'elliptical-distance-seasons',
        'start_position': 'june-solstice', 'start_hemisphere': 'north',
    }),
    ('seasons-tilt-lab', {
        'scenario': 'earth-tilt-four-positions',
        'start_position': 'june-solstice', 'start_hemisphere': 'north',
        'axis_degrees': 23.5,
    }),
    ('art-elements-composer', {
        'scenario': 'garden-five-elements', 'start_elements': [],
    }),
    ('art-elements-composer', {
        'scenario': 'garden-five-elements', 'start_elements': [True],
    }),
    ('art-elements-composer', {
        'scenario': 'garden-five-elements', 'start_elements': ['line', 'line'],
    }),
    ('art-elements-composer', {
        'scenario': 'garden-five-elements', 'start_elements': ['line', 'sound'],
    }),
    ('art-elements-composer', {
        'scenario': 'garden-five-elements', 'start_elements': 'line',
    }),
    ('art-elements-composer', {
        'scenario': 'garden-five-elements', 'start_elements': ['line'],
        'palette': 'warm',
    }),
])
def test_lesson_model_props_fail_closed(renderer, props):
    model = {
        'id': 'test-model', 'kind': 'model', 'renderer': renderer,
        'title': 'Test model', 'instructions': 'Test the bounded props.', 'props': props,
    }
    with pytest.raises(ValueError):
        _validate_lesson_media({'id': 'test.1.model', 'lesson_media': [model]})


@pytest.mark.parametrize('field', ('min', 'max', 'start_value', 'start_delta'))
def test_integer_number_line_props_reject_bool_smuggling(field):
    props = {'min': -12, 'max': 12, 'start_value': -2, 'start_delta': -7}
    props[field] = True
    model = {
        'id': 'test-integer-line', 'kind': 'model',
        'renderer': 'integer-number-line-lab',
        'title': 'Test integer number line',
        'instructions': 'Test strict integer props.', 'props': props,
    }
    with pytest.raises(ValueError, match='integer number line lab'):
        _validate_lesson_media({'id': 'test.2.integer-line', 'lesson_media': [model]})


@pytest.mark.parametrize('renderer,props', [
    ('fraction-equivalence-lab', {'numerator': 2, 'denominator': 3, 'max_factor': 4}),
    ('atom-element-builder', {'protons': 6, 'neutrons': 6, 'electrons': 6}),
    ('cell-microscope', {'start_specimen': 'onion', 'start_magnification': 100}),
    ('counterexample-lab', {'scenario': 'squares-and-rectangles'}),
    ('integer-number-line-lab', {
        'min': -12, 'max': 12, 'start_value': -2, 'start_delta': -7,
    }),
    ('function-composition-lab', {
        'f_slope': 2, 'f_intercept': 0, 'g_slope': 1, 'g_intercept': -1,
        'x_min': -5, 'x_max': 5, 'start_x': 5,
    }),
    ('function-composition-lab', {
        'f_slope': -3, 'f_intercept': -5, 'g_slope': 3, 'g_intercept': 5,
        'x_min': -8, 'x_max': 8, 'start_x': -8,
    }),
    ('circulation-route-lab', {
        'route': 'cardiopulmonary', 'start_step': 0, 'show_oxygenation': True,
    }),
    ('circulation-route-lab', {
        'route': 'cardiopulmonary', 'start_step': 8, 'show_oxygenation': False,
    }),
    ('truth-table-lab', {'start_operator': 'and', 'start_p': False, 'start_q': False}),
    ('truth-table-lab', {'start_operator': 'or', 'start_p': False, 'start_q': True}),
    ('truth-table-lab', {'start_operator': 'implies', 'start_p': True, 'start_q': False}),
    ('stack-queue-lab', {'start_mode': 'stack', 'capacity': 3, 'initial_count': 0}),
    ('stack-queue-lab', {'start_mode': 'queue', 'capacity': 8, 'initial_count': 8}),
    ('matrix-transform-lab', {'start_transform': 'identity'}),
    ('matrix-transform-lab', {'start_transform': 'x-stretch'}),
    ('matrix-transform-lab', {'start_transform': 'x-shear'}),
    ('matrix-transform-lab', {'start_transform': 'y-reflection'}),
    ('matrix-transform-lab', {'start_transform': 'x-projection'}),
    ('venturi-flow-lab', {'scenario': 'horizontal-water-venturi', 'start_throat': 'full-area'}),
    ('venturi-flow-lab', {'scenario': 'horizontal-water-venturi', 'start_throat': 'half-area'}),
    ('venturi-flow-lab', {'scenario': 'horizontal-water-venturi', 'start_throat': 'quarter-area'}),
    ('gene-expression-stepper', {'scenario': 'eukaryotic-met-glu-phe', 'start_gene_state': 'off'}),
    ('gene-expression-stepper', {'scenario': 'eukaryotic-met-glu-phe', 'start_gene_state': 'on'}),
    ('tcp-packet-tracer', {'scenario': 'tcp-four-segment-loss-two'}),
    ('heat-equation-lab', {
        'cells': 9, 'hot_cell': 4, 'diffusion_percent': 20, 'max_steps': 10,
    }),
    ('complexity-certificate-lab', {
        'scenario': 'sat-certificate', 'start_n': 4, 'max_n': 20,
    }),
    ('morphogen-gradient-lab', {
        'cells': 11, 'source': 100, 'decay_percent': 20,
        'low_threshold': 30, 'high_threshold': 65,
    }),
    ('ct-window-lab', {
        'phantom': 'synthetic-hu-reference', 'level': 40, 'width': 400,
    }),
    ('alphabet-explorer', {
        'alphabet': 'english-basic-latin', 'start_letter': 'A',
        'example_set': 'common-words-v1',
    }),
    ('alphabet-explorer', {
        'alphabet': 'english-basic-latin', 'start_letter': 'Z',
        'example_set': 'common-words-v1',
    }),
    ('inclusive-family-timeline', {
        'scenario': 'fictional-family-three-times', 'start_time': 'today',
    }),
    ('day-night-rotation-lab', {
        'scenario': 'earth-rotation-equinox-equator',
        'start_hour': 0, 'step_hours': 6,
    }),
    ('day-night-rotation-lab', {
        'scenario': 'earth-rotation-equinox-equator',
        'start_hour': 6, 'step_hours': 6,
    }),
    ('day-night-rotation-lab', {
        'scenario': 'earth-rotation-equinox-equator',
        'start_hour': 12, 'step_hours': 6,
    }),
    ('day-night-rotation-lab', {
        'scenario': 'earth-rotation-equinox-equator',
        'start_hour': 18, 'step_hours': 6,
    }),
    ('classroom-paint-mixer', {
        'scenario': 'equal-parts-classroom-ryb',
        'start_first': 'blue', 'start_second': 'yellow',
    }),
    ('classroom-paint-mixer', {
        'scenario': 'equal-parts-classroom-ryb',
        'start_first': 'red', 'start_second': 'white',
    }),
    ('reading-path-lab', {
        'scenario': 'simple-english-cat-sat', 'start_phase': 'sounds',
    }),
    ('reading-path-lab', {
        'scenario': 'simple-english-cat-sat', 'start_phase': 'meaning',
    }),
    ('timeline-order-lab', {
        'scenario': 'fictional-library-three-dates',
        'start_order': ['roof-restored', 'opened', 'reading-room'],
    }),
    ('timeline-order-lab', {
        'scenario': 'fictional-library-three-dates',
        'start_order': ['opened', 'reading-room', 'roof-restored'],
    }),
    ('seasons-tilt-lab', {
        'scenario': 'earth-tilt-four-positions',
        'start_position': 'march-equinox', 'start_hemisphere': 'south',
    }),
    ('seasons-tilt-lab', {
        'scenario': 'earth-tilt-four-positions',
        'start_position': 'december-solstice', 'start_hemisphere': 'north',
    }),
    ('art-elements-composer', {
        'scenario': 'garden-five-elements', 'start_elements': ['texture'],
    }),
    ('art-elements-composer', {
        'scenario': 'garden-five-elements',
        'start_elements': ['line', 'shape', 'color', 'texture', 'pattern'],
    }),
])
def test_lesson_model_props_accept_the_bounded_contract(renderer, props):
    model = {
        'id': 'test-model', 'kind': 'model', 'renderer': renderer,
        'title': 'Test model', 'instructions': 'Test the bounded props.', 'props': props,
    }
    _validate_lesson_media({'id': 'test.2.model', 'lesson_media': [model]})


def test_authored_quiz_items_are_well_formed(curr):
    for nid, node in curr.nodes.items():
        for q in node.get('quiz', []):
            assert q.get('prompt') and q.get('answer'), nid
            if q.get('kind') == 'choice':
                assert q['answer'] in q['choices'], \
                    '{}: answer not among choices'.format(nid)
                assert len(set(q['choices'])) == len(q['choices']), \
                    '{}: duplicate choices'.format(nid)


def test_unlock_requirements_are_human_readable(curr):
    node = curr.nodes['math.4.diff-calc']
    reqs = curr.unlock_requirements(node, {})
    assert reqs and all(isinstance(r, str) and r for r in reqs)


# ---------------- practice generators ----------------

def test_every_generator_produces_valid_questions():
    for key in practice.list_generators():
        qs = practice.generate_set(key, 5, level=2)
        assert qs, 'generator {} produced nothing'.format(key)
        for q in qs:
            assert q['prompt'] and q['answer']
            assert 'displaystyle' not in q['prompt']
            if q['kind'] == 'choice':
                assert q['answer'] in q['choices'], key
                assert len(set(q['choices'])) == len(q['choices']), key
                assert len(q['choices']) >= 2, key


def test_generators_cover_science_and_computing():
    keys = set(practice.list_generators())
    for expected in ('kinematics', 'molar-mass', 'binary', 'logic-gates', 'ph',
                     'ohms-law', 'atoms', 'units', 'phonics'):
        assert expected in keys


def test_fraction_compare_has_four_real_options():
    for _ in range(30):
        q = practice.g_fractions(2)
        if 'largest' in q['prompt']:
            assert len(q['choices']) == 4
            assert all('/' in c for c in q['choices']), 'options must be fractions'


def test_arithmetic_generators_are_correct():
    for _ in range(50):
        q = practice.g_times_tables(1)
        a, b = [int(x) for x in q['prompt'].replace('=', '').replace('?', '').split('×')]
        assert int(q['answer']) == a * b


# ---------------- quiz generation ----------------

TEXT = ("The Great Barrier Reef is the world's largest coral reef system. "
        "It was designated a World Heritage Site in 1981. "
        "This is another example of that phenomenon. "
        "The reef supports a wide diversity of marine life including turtles. "
        "Suppose Bob travels 300 m east of Tom's house. "
        "{\\displaystyle E=mc^{2}} is a famous equation. "
        "Australia protects the reef through a marine park authority. ")


def test_cloze_rejects_context_dependent_and_example_sentences():
    qs = quiz.cloze_from_text(TEXT, 6, topic='Great Barrier Reef')
    for q in qs:
        assert 'This is another example' not in q['prompt']
        assert 'Suppose Bob' not in q['prompt']
        assert 'displaystyle' not in q['prompt']


def test_cloze_questions_are_answerable():
    qs = quiz.cloze_from_text(TEXT, 6, topic='Great Barrier Reef')
    for q in qs:
        assert '______' in q['prompt']
        assert q['answer'] in q['choices']
        assert len(set(q['choices'])) == 4


def test_cards_are_built_from_missed_questions():
    questions = [
        {'prompt': 'Fill in the blank:\n\nThe reef is ______.', 'answer': 'large',
         'explain': 'The reef is large.'},
        {'prompt': 'Q2', 'answer': 'right', 'explain': 'because'},
    ]
    cards = quiz.cards_from_missed(questions, ['wrong', 'right'], 'node1', 'Reef')
    assert len(cards) == 1
    assert cards[0]['back'].startswith('large')
    assert cards[0]['node_id'] == 'node1'


def test_score_quiz_is_case_insensitive():
    qs = [{'answer': 'Paris'}, {'answer': '42'}]
    assert quiz.score_quiz(qs, ['paris', '42'])['score'] == 1.0
    assert quiz.score_quiz(qs, ['London', '42'])['score'] == 0.5


# ---------------- pacing ----------------

# ---------------- board-found regressions ----------------

def test_failing_a_mastered_node_does_not_make_it_fresher(store):
    """Regression: `strength` used to reset to 1.0 on any attempt, so failing a
    mastered lesson made the book think it was freshly learned."""
    store.record_attempt('n1', 1.0)
    with store._conn() as c:
        c.execute('UPDATE mastery SET first_pass_at=? WHERE node_id=?',
                  (time.time() - MASTERY_MIN_INTERVAL - 10, 'n1'))
    store.record_attempt('n1', 1.0)
    assert 'n1' in store.mastered_set()
    store.record_attempt('n1', 0.0)  # forgot it
    with store._conn() as c:
        row = c.execute('SELECT strength, mastered_at FROM mastery WHERE node_id=?',
                        ('n1',)).fetchone()
    assert row[0] < 1.0, 'failure must not refresh strength'
    assert row[1] is None, 'a failed mastered node must lose its mastery'
    assert 'n1' not in store.mastered_set()


def test_decayed_mastery_relocks_downstream(store):
    """Mastery that has decayed must stop opening gates until refreshed."""
    store.record_attempt('n1', 1.0)
    with store._conn() as c:
        c.execute('UPDATE mastery SET first_pass_at=? WHERE node_id=?',
                  (time.time() - MASTERY_MIN_INTERVAL - 10, 'n1'))
    store.record_attempt('n1', 1.0)
    assert store.gate_map()['n1'] == 1.0
    with store._conn() as c:  # simulate a long absence
        c.execute('UPDATE mastery SET last_seen=? WHERE node_id=?',
                  (time.time() - 400 * 86400, 'n1'))
    assert store.gate_map()['n1'] < 0.8, 'stale mastery must not keep gates open'


def test_placement_credit_cannot_launder_into_proven(store):
    """Regression: assumed credit backdated a pass, so a single un-spaced
    attempt could turn placement into 'proven'."""
    store.seed_assumed(['a1'])
    assert store.proven_count() == 0
    store.record_attempt('a1', 1.0)   # one genuine, un-spaced attempt
    assert store.proven_count() == 0, 'proving still needs two spaced passes'


def test_xp_cannot_be_farmed_by_retaking_the_same_quiz(store):
    for _ in range(10):
        store.record_attempt('n1', 1.0)
    assert store.total_xp() <= 12, 'effort XP is once per node per day'


def test_blank_review_pays_no_xp(store):
    store.add_cards([{'front': 'f', 'back': 'b', 'node_id': 'n'}])
    all_due(store)
    cid = store.due_cards()[0]['id']
    assert store.review_card(cid, 0)['xp_gained'] == 0


def test_reading_event_is_always_logged_even_when_not_first(store):
    """The 'read something today' goal must tick on a re-read."""
    store.log_reading('Photosynthesis')
    store.log_reading('Photosynthesis')
    with store._conn() as c:
        n = c.execute("SELECT COUNT(*) FROM events WHERE kind='read'").fetchone()[0]
    assert n == 2
    assert store.total_xp() == 3, 'but only the first open pays'


def test_long_streak_is_not_truncated_by_event_volume(store):
    """Regression: a LIMIT on the event scan silently shortened long streaks."""
    now = time.time()
    with store._conn() as c:
        for day in range(120):
            for _ in range(20):  # heavy daily use
                c.execute("INSERT INTO events(kind,payload,at,xp) VALUES('attempt','{}',?,1)",
                          (now - day * 86400,))
    assert store.streak_days() >= 120


def test_authored_items_are_not_guessable_by_length(curr):
    """A test-wise learner picking the longest option must score near chance."""
    total = right = 0
    for node in curr.nodes.values():
        for q in node.get('quiz', []):
            if q.get('kind') != 'choice' or not q.get('choices'):
                continue
            total += 1
            longest = max(q['choices'], key=len)
            if longest == q['answer']:
                right += 1
    assert total > 200, 'expected a substantial authored bank'
    rate = right / total
    assert rate < 0.45, 'pick-the-longest scores {:.0%} — length is a cue'.format(rate)


def test_every_young_node_can_be_assessed(curr):
    """Regression: disabling cloze below stage 2 once left 74 nodes with no
    possible assessment, so they could never be mastered."""
    young = [n for n in curr.nodes.values() if n['stage'] <= 1]
    orphans = [n['id'] for n in young if not n.get('quiz') and not n.get('practice')]
    assert not orphans, 'unassessable young nodes: {}'.format(orphans[:5])


def test_young_questions_are_answerable_without_reading(curr):
    """Young items must carry spoken prompts and short options."""
    checked = 0
    for node in curr.nodes.values():
        if node['stage'] > 1:
            continue
        for q in node.get('quiz', []):
            checked += 1
            assert q.get('say'), '{}: young item lacks spoken prompt'.format(node['id'])
            for c in q.get('choices', []):
                assert len(c) <= 40, '{}: option too long to hear/see'.format(node['id'])
    assert checked > 150


def test_story_spans_every_stage_and_leads_to_real_nodes(curr):
    import json as _json
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'data', 'story', 'frame.json')) as f:
        story = _json.load(f)
    stages = {c['unlocks_stage'] for c in story['chapters']}
    assert stages == {0, 1, 2, 3, 4, 5}, 'story must span the whole journey'
    for c in story['chapters'][:-1]:
        assert c['leads_to'] in curr.nodes, '{} leads nowhere'.format(c['id'])
    # The final chapter is an epilogue: it closes the arc and gates nothing.
    assert not story['chapters'][-1]['leads_to']
    # Every stage should carry more than a token single chapter at the top end.
    for stage in (4, 5):
        n = sum(1 for c in story['chapters'] if c['unlocks_stage'] == stage)
        assert n >= 2, 'stage {} has only {} chapter(s)'.format(stage, n)


def test_numeric_answers_compare_by_value():
    qs = [{'kind': 'numeric', 'answer': '0.5'}, {'kind': 'numeric', 'answer': '12'}]
    assert quiz.score_quiz(qs, ['.50', '12.0'])['score'] == 1.0
    assert quiz.score_quiz(qs, ['1/2', '12'])['score'] == 1.0
    assert quiz.score_quiz(qs, ['0.6', '12'])['score'] == 0.5


def test_procedural_items_are_marked_ephemeral():
    """Random instances must never be stored as flashcards."""
    for key in ('addition', 'times-tables', 'counting'):
        for q in practice.generate_set(key, 3, 1):
            assert q.get('ephemeral') is True


def test_sanitizer_never_swallows_the_article_on_malformed_html():
    """Regression: an unclosed <style> made drop_depth never unwind, returning
    an empty page and losing the whole article."""
    out = rewrite_article('<style>body{}<p>the actual article text</p>')
    assert 'the actual article text' in out


def test_sanitizer_keeps_rel_noopener_on_external_links():
    """rel stays; target is gone on purpose.

    The renderer used to hand every external link `target="_blank"`, so an
    article's several hundred citation links were several hundred unannounced
    exits: one tap and the reader was in a raw browser tab, outside the book's
    typography and its offline guarantee. The destination is kept and marked —
    `data-primer-outside` names the host and the client asks before going — and
    `rel="noopener noreferrer"` still travels with it, because the client opens
    the window itself and the anchor must stay safe if it is ever followed
    directly.
    """
    out = rewrite_article('<a href="https://example.com/x">ext</a>')
    assert 'rel="noopener noreferrer"' in out
    assert 'target=' not in out, "an unannounced exit from the book"
    assert 'data-primer-outside="example.com"' in out
    assert 'class="primer-outside"' in out


def test_sanitizer_drops_unsafe_target_values():
    out = rewrite_article('<a href="https://example.com" target="_top">x</a>')
    assert 'target="_top"' not in out


def test_the_promise_is_computed_not_assumed(curr):
    """Regression: this test used to assert the plan lands inside 5-10 years at
    six hours a week — which is how the per-node minutes came to be reverse-
    engineered from the marketing claim in the first place. What the roadmap
    owes the reader is an honest number and the hours it would actually take.
    """
    graph = curr.graph()
    base = {'breadth': 'balanced', 'domains': ['math', 'physics', 'cs'], 'stage': 1}

    light = roadmap({**base, 'hours_per_week': 6}, graph, {})
    assert light['within_promise'] is False, 'six hours a week is not an education'
    assert light['estimated_years'] > 10
    assert '{:,}'.format(light['total_hours']) in light['note'], 'say what it costs'
    assert str(round(light['hours_for_ten_years'])) in light['note']

    serious = roadmap({**base, 'hours_per_week': 20}, graph, {})
    assert serious['within_promise'] is True, 'at real hours the promise holds'
    assert 5 <= serious['estimated_years'] <= 10

    # Twice the hours, half the years — the estimate tracks the input.
    assert abs(light['estimated_years'] / serious['estimated_years'] - 20 / 6) < 0.2
    assert light['timeline'] and serious['timeline']


def test_the_curriculum_is_priced_against_instructional_time(curr):
    """A whole preschool-to-graduate education across ten fields cannot cost a
    few hundred hours. The classroom equivalent is on the order of 20,000; one
    to one tutoring should come in well under that, and nowhere near a tenth."""
    graph = curr.graph()
    r = roadmap({'breadth': 'polymath', 'domains': [], 'hours_per_week': 20, 'stage': 0},
                graph, {})
    assert 4000 <= r['total_hours'] <= 12000, r['total_hours']


def test_polymath_takes_longer_than_focused(curr):
    graph = curr.graph()
    base = {'hours_per_week': 6, 'stage': 1, 'domains': []}
    poly = roadmap({**base, 'breadth': 'polymath'}, graph, {})
    focus = roadmap({**base, 'breadth': 'focused', 'domains': ['math']}, graph, {})
    assert poly['estimated_years'] > focus['estimated_years']


def test_more_hours_shortens_the_journey(curr):
    graph = curr.graph()
    base = {'breadth': 'balanced', 'domains': ['math'], 'stage': 1}
    slow = roadmap({**base, 'hours_per_week': 4}, graph, {})
    fast = roadmap({**base, 'hours_per_week': 12}, graph, {})
    assert fast['estimated_years'] < slow['estimated_years']


def test_a_domain_stage_override_prices_only_its_own_domains_review(curr):
    """A per-domain slide discounts that domain's below-it nodes as review
    (the 25% weight) without moving a domain the reader never touched off
    the single global stage every profile still falls back to."""
    graph = curr.graph()
    base = {'breadth': 'polymath', 'domains': ['math', 'physics'], 'stage': 0}

    global_only = roadmap(base, graph, {})
    math_only = roadmap(
        {**base, 'settings': {'domain_stage': {'math': 3}}}, graph, {})
    both_high = roadmap({**base, 'stage': 3}, graph, {})

    # Discounting just math's early nodes must land strictly between doing
    # nothing and discounting both domains' early nodes.
    assert both_high['total_hours'] < math_only['total_hours'] < global_only['total_hours']

    # The raw per-curriculum-stage hours remaining is a fact about the
    # graph, not the pacing weight — it must not move with the override.
    assert math_only['stages'] == global_only['stages']


# ---------------- round-2 board regressions ----------------

def test_procedural_prompts_never_become_flashcards():
    """Regression: '7 + 5 = ?' as a flashcard is noise — the generator should
    re-drill it instead. Covers both the annotation and the content shape."""
    questions = [
        {'prompt': '7 + 5 = ?', 'answer': '12', 'ephemeral': True},
        {'prompt': 'What is 12 × 3?', 'answer': '36'},
        {'prompt': 'How many do you see? 🍎 🍎 🍎', 'answer': '3'},
        {'prompt': 'In which year was the Principia published?', 'answer': '1687',
         'explain': 'Newton published it in 1687.'},
    ]
    cards = quiz.cards_from_missed(questions, ['', '', '', ''], 'n', 'a')
    fronts = ' '.join(c['front'] for c in cards)
    assert len(cards) == 1, fronts
    assert 'Principia' in fronts


def test_numeric_equivalence_does_not_mint_a_card():
    """Answering 1/2 when the key says 0.5 is correct — no card should appear."""
    qs = [{'kind': 'numeric', 'prompt': 'Half of one?', 'answer': '0.5'}]
    assert quiz.cards_from_missed(qs, ['1/2'], 'n', 'a') == []


def test_young_learners_get_cards_from_their_lesson():
    """Regression: stage 0–1 card sources were gated to stage >= 2, so a young
    reader's deck could never fill."""
    cards = quiz.cards_from_lesson('Counting', 'Count objects to 10 and back.',
                                   'Counting means giving each thing its own number word.', 'math.0.counting')
    assert cards and all(c['back'] for c in cards)


# Answer shapes a reader with no keyboard skills can still use: pick one, put
# them in order, or touch each thing and commit. The rule is that a pre-reader
# never has to TYPE — this listed only 'choice' because choice was once the
# only shape that satisfied it, and that made a rule about the reader read like
# a rule about the item kind. `tally` is the shape built for exactly these
# readers (touch each apple, the book counting along), and asserting it away
# was part of why it sat unused.
YOUNG_ANSWER_SHAPES = ('choice', 'tally', 'order')


def test_young_practice_never_requires_typing_and_is_voiced(curr):
    """A pre-reader must be able to answer by ear and by tapping."""
    young_gens = {n['practice'] for n in curr.nodes.values()
                  if n['stage'] <= 1 and n.get('practice')}
    assert young_gens
    for key in young_gens:
        for q in practice.generate_set(key, 4, level=1):
            assert q['kind'] in YOUNG_ANSWER_SHAPES, (
                '{} asks a young reader to type ({})'.format(key, q['kind']))
            assert q.get('say'), '{} has no spoken prompt'.format(key)


def test_a_young_reader_is_asked_to_produce_and_not_only_to_recognise(curr):
    """Recognition alone is not practice, and it was all there was.

    Every one of the 622 authored items at stages 0-1 is multiple choice, and
    every young generator returned choice too — so for the Seedling and Sprout
    years, which the pacing model prices in years rather than weeks, the book
    asked the reader to pick an answer and never once to make one. The
    instrument for this existed the whole time: `g_count_tally` scores counting
    AS counting, so a child who counts five apples but cannot yet read the
    numeral 5 is marked right. It was simply wired to nothing.
    """
    produced = 0
    for q in practice.generate_set('counting', 40, level=0):
        if q['kind'] in ('tally', 'numeric', 'order'):
            produced += 1
    assert produced >= 10, (
        'counting minted %d produced items in 40 — a young reader is still only '
        'recognising' % produced)


def test_young_practice_generators_are_topical(curr):
    """Regression: a lesson about animals was serving 'what does murmur mean?'."""
    topical = {
        'counting': ['count'], 'compare': ['compare', 'bigger', 'smaller', 'more'],
        'patterns': ['pattern'], 'shapes': ['shape'], 'letters': ['letter', 'alphabet'],
        'phonics': ['sound', 'phonic', 'letter'], 'spelling': ['spell'],
        'vocabulary': ['word', 'vocabul'], 'addition': ['add'],
        'subtraction': ['subtract', 'take away'], 'times-tables': ['multipl', 'times'],
        'division': ['divi', 'share'], 'place-value': ['place value', 'digit'],
    }
    for node in curr.nodes.values():
        if node['stage'] > 1 or not node.get('practice'):
            continue
        keys = topical.get(node['practice'])
        if not keys:
            continue
        hay = (node['title'] + ' ' + node.get('goal', '') + ' ' + node['id']).lower()
        assert any(k in hay for k in keys), \
            '{} uses off-topic generator {}'.format(node['id'], node['practice'])


def test_decayed_mastery_drops_out_of_the_headline_count(store):
    store.record_attempt('n1', 1.0)
    with store._conn() as c:
        c.execute('UPDATE mastery SET first_pass_at=? WHERE node_id=?',
                  (time.time() - MASTERY_MIN_INTERVAL - 10, 'n1'))
    store.record_attempt('n1', 1.0)
    assert store.proven_count_current() == 1
    with store._conn() as c:
        c.execute('UPDATE mastery SET last_seen=? WHERE node_id=?',
                  (time.time() - 400 * 86400, 'n1'))
    assert store.proven_count_current() == 0, 'the count must regress like the gate'


def test_streak_charges_days_since_the_last_visit(store):
    """Regression: the leading gap was free, so someone absent long enough to
    blow the entire freeze budget still saw an unbroken streak.

    Updated for the later freeze-forgiveness feature: STREAK_FREEZES=2 exists
    precisely to bridge up to 2 real missed days, so idle for exactly that
    long (last activity 3 days ago — meaning only yesterday and the day
    before are actually missed; today's box hasn't closed yet, so it isn't
    charged) must NOT break the streak — see
    test_a_stale_but_freeze_bridgeable_streak_is_not_dropped_to_zero for that
    boundary case. This test instead checks one real day past what any
    freeze budget can cover: last activity 4 days ago means 3 real missed
    days (yesterday, the day before, and the day before that), which
    genuinely exceeds STREAK_FREEZES and must break the streak."""
    now = time.time()
    with store._conn() as c:
        for days_ago in range(4, 20):   # nothing today or the 3 days before it
            c.execute("INSERT INTO events(kind,payload,at,xp) VALUES('attempt','{}',?,1)",
                      (now - days_ago * 86400,))
    assert store.streak_days() == 0, 'idle 3 real days exceeds the 2-day freeze budget'


def test_due_queue_round_robins_across_topics(store):
    cards = []
    for i in range(4):
        for node in ('A', 'B', 'C'):
            cards.append({'front': node + str(i), 'back': 'b', 'node_id': node})
    store.add_cards(cards)
    all_due(store)
    seq = [c['node_id'] for c in store.due_cards(9)]
    runs = max(len(list(g)) for _, g in __import__('itertools').groupby(seq))
    assert runs == 1, 'consecutive cards should change topic: {}'.format(seq)


def test_leech_cards_are_parked_not_ground(store):
    store.add_cards([{'front': 'hard', 'back': 'b', 'node_id': 'n'}])
    all_due(store)
    cid = store.due_cards()[0]['id']
    for _ in range(7):
        make_due(store, cid)
        store.review_card(cid, 0)
    with store._conn() as c:
        due = c.execute('SELECT due FROM srs_cards WHERE id=?', (cid,)).fetchone()[0]
    assert due - time.time() > 5 * 86400, 'a repeatedly failed card should rest'


def test_authored_answers_are_not_guessable_by_position(open_assessment_gate):
    """Regression: the length-parity rewrite left every answer at index 0, so
    'always pick A' scored 94%. Options must be shuffled when served."""
    from fastapi.testclient import TestClient
    import primer.server as srv
    client = TestClient(srv.app)
    first = total = 0
    for node in ('math.3.linear', 'phys.4.quantum', 'bio.4.molecular',
                 'cs.5.complexity', 'math.5.logic', 'chem.4.organic'):
        for _ in range(10):
            paper = client.get('/api/quiz/{}?n=3'.format(node)).json()
            for q in paper['questions']:
                if q.get('kind') != 'choice' or not q.get('choices'):
                    continue
                # The key is not in the payload any more, and feedback costs a
                # committed answer — read the book's own copy instead.
                key = srv._SERVED[paper['token']]["questions"][
                    paper['questions'].index(q)].get('answer')
                if key not in q['choices']:
                    continue
                total += 1
                if q['choices'].index(key) == 0:
                    first += 1
    assert total >= 90, 'not enough items sampled: {}'.format(total)
    assert first / total < 0.40, 'pick-first scores {:.0%}'.format(first / total)


def test_constructed_response_appears_at_higher_stages(open_assessment_gate):
    """Recognition alone flatters the reader; from secondary school upward at
    least one item must be produced."""
    from fastapi.testclient import TestClient
    import primer.server as srv
    client = TestClient(srv.app)
    for node in ('math.3.quadratics', 'phys.4.quantum', 'cs.5.complexity'):
        kinds = [q['kind'] for q in client.get('/api/quiz/{}?n=4'.format(node)).json()['questions']]
        # `numeric` is a produced response too — the reader computes and writes a
        # value rather than picking one. It is the better kind, in fact: it is
        # authored and it counts, where the generated `short` is neither.
        assert {'short', 'numeric'} & set(kinds), \
            '{} has no constructed response: {}'.format(node, kinds)


def test_short_answer_scores_partial_credit():
    q = {'kind': 'short', 'answer': 'Cells are the smallest unit of life',
         'keywords': ['cells', 'smallest', 'life']}
    full = quiz.score_quiz([q], ['cells are the smallest unit of life'])['score']
    part = quiz.score_quiz([q], ['something about cells'])['score']
    none = quiz.score_quiz([q], ['no idea'])['score']
    assert full == 1.0 and 0 < part < 1.0 and none == 0.0


def test_cloze_key_never_appears_in_its_own_stem():
    text = ("Photosynthesis converts light energy into chemical energy in plants. "
            "Chlorophyll absorbs light most strongly in the blue and red bands. "
            "The Calvin cycle fixes carbon dioxide into sugar molecules. "
            "Stomata regulate gas exchange across the leaf surface. "
            "Oxygen is released as a by-product of the light reactions.")
    for q in quiz.cloze_from_text(text, 5, topic='Photosynthesis'):
        stem = q['prompt'].lower()
        assert q['answer'].lower() not in stem, 'answer copyable from stem: ' + q['prompt']


def test_no_single_surface_strategy_beats_chance(curr):
    """The two cues we have actually shipped by accident — longest option, and
    first option — must both sit near chance. Measured over the whole bank."""
    import statistics
    longest = first = total = 0
    chances = []
    for node in curr.nodes.values():
        for q in node.get('quiz', []):
            if q.get('kind') != 'choice' or not q.get('choices'):
                continue
            total += 1
            chances.append(1 / len(q['choices']))
            if max(q['choices'], key=len) == q['answer']:
                longest += 1
            if q['choices'][0] == q['answer']:
                first += 1
    chance = statistics.mean(chances)
    assert total > 500
    # Position is fixed at serve time (see the API test); here we only require
    # that the *stored* length cue stays within a modest margin of chance.
    assert longest / total < chance + 0.14, \
        'pick-longest {:.0%} vs chance {:.0%}'.format(longest / total, chance)


def test_curriculum_is_a_lattice_not_a_chain(curr):
    """Real understanding rests on several strands at once. A single-prereq
    chain lets a reader reach advanced work along one narrow path."""
    above0 = [n for n in curr.nodes.values() if n['stage'] > 0]
    multi = [n for n in above0 if len(n['prereqs']) >= 2]
    assert len(multi) / len(above0) >= 0.85, \
        'only {:.0%} of nodes have 2+ prerequisites'.format(len(multi) / len(above0))


def test_cross_domain_dependencies_are_substantial(curr):
    """Physics must actually require its mathematics."""
    cross = [(n['id'], p) for n in curr.nodes.values() for p in n['prereqs']
             if curr.nodes[p]['domain'] != n['domain']]
    assert len(cross) >= 150, 'only {} cross-domain edges'.format(len(cross))
    # Spot-check the dependencies a subject expert would insist on.
    def requires(node_id, prereq_id):
        return prereq_id in curr.nodes[node_id]['prereqs']
    assert requires('phys.4.quantum', 'math.4.linalg')
    assert requires('cs.4.ml', 'math.4.linalg')
    assert requires('bio.4.biochem', 'chem.4.organic')


def test_story_arc_is_never_silently_truncated():
    """Regression: chapters merely *ahead* of the reader were being discarded
    and the cursor persisted, so the upper half of the arc vanished forever."""
    import tempfile, os as _os, time as _t
    import primer.server as srv
    from primer.learner import LearnerStore
    saved = srv.learner
    try:
        srv.learner = LearnerStore(_os.path.join(tempfile.mkdtemp(), 't.db'))
        srv.learner.save_profile('R', 8, 6, 'balanced', 1,
                                 ['math', 'language', 'physics', 'biology', 'cs'])
        srv.learner.seed_assumed(srv.curr.seed_mastery_for_stage(1))
        chapters = srv.STORY['chapters']
        for ch in chapters[:9]:
            target = ch.get('leads_to')
            if not target:
                continue
            srv.learner.record_attempt(target, 1.0)
            with srv.learner._conn() as c:
                c.execute('UPDATE mastery SET first_pass_at=?, assumed=0 WHERE node_id=?',
                          (_t.time() - 3 * 86400, target))
            srv.learner.record_attempt(target, 1.0)
        _, idx, _adv = srv._story_cursor(srv.learner.get_profile(), 1)
        assert idx <= 10, 'cursor jumped to {} — chapters were discarded'.format(idx)
    finally:
        srv.learner = saved


def test_epilogue_is_terminal():
    """The last chapter closes the arc: it must not offer to turn to nothing."""
    import tempfile, os as _os
    import primer.server as srv
    from primer.learner import LearnerStore
    saved = srv.learner
    try:
        srv.learner = LearnerStore(_os.path.join(tempfile.mkdtemp(), 't.db'))
        last = len(srv.STORY['chapters']) - 1
        srv.learner.save_profile('R', 20, 6, 'balanced', 5, ['math'],
                                 {'story_progress': last})
        _chapter, _idx, can_advance = srv._story_cursor(srv.learner.get_profile(), 1)
        assert can_advance is False
    finally:
        srv.learner = saved


def test_stage_zero_is_not_promoted_by_falsy_check():
    """Regression: `profile.stage || 2` made a preschooler stage 2 on cold boot,
    silencing every auto-read. The frontend must use a finite check."""
    app_js = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               'web', 'app.js')).read()
    assert 'S.state.profile.stage || 2' not in app_js
    assert 'Number.isFinite' in app_js


def test_client_cannot_launder_a_wrong_answer_into_a_right_one():
    """Regression: the browser used to submit the canonical key whenever it
    judged an answer correct, so server-side scoring could only rubber-stamp
    the client's verdict."""
    app_js = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               'web', 'app.js')).read()
    assert 'ok ? q.answer :' not in app_js, 'client still echoes the key'
    assert "answers.push(given || '')" in app_js


def test_early_stages_have_more_than_one_assessment_format(open_assessment_gate):
    """Recognition-only assessment cannot distinguish knowing from guessing."""
    from fastapi.testclient import TestClient
    import primer.server as srv
    client = TestClient(srv.app)
    for node in ('math.0.counting', 'lang.0.alphabet', 'bio.1.lifecycles'):
        kinds = {q['kind'] for q in client.get('/api/quiz/{}?n=5'.format(node)).json()['questions']}
        assert len(kinds) >= 2, '{} offers only {}'.format(node, kinds)


def test_order_items_are_solvable_and_shuffled():
    for key in ('order-numbers', 'order-letters', 'order-lifecycle', 'order-time'):
        for q in practice.generate_set(key, 4, 0):
            assert q['kind'] == 'order' and q.get('say')
            assert set(q['items']) == set(q['answer'].split())
            assert q['items'] != q['answer'].split(), 'items must not start solved'


def test_young_item_banks_are_deep_enough_to_vary(curr):
    """Two spaced passes over the identical paper measure recall of answers,
    not the concept — the bank must exceed what one quiz serves."""
    young = [n for n in curr.nodes.values() if n['stage'] <= 1]
    shallow = [n['id'] for n in young if len(n.get('quiz', [])) < 5]
    assert len(shallow) <= 2, 'nodes with a thin bank: {}'.format(shallow[:5])


def test_cloze_rejects_anaphora_and_lookalike_options():
    text = ("The Calvin cycle fixes carbon dioxide into stable sugar molecules. "
            "This process was characterized by Melvin Calvin during the 1950s. "
            "Chlorophyll absorbs photons most strongly in the blue and red bands. "
            "Oxygen is liberated as a by-product of the light-dependent reactions. "
            "Stomata regulate gaseous exchange across the waxy leaf surface.")
    for q in quiz.cloze_from_text(text, 6, topic='Photosynthesis'):
        stem = q['prompt'].lower()
        assert 'this process' not in stem
        # No two options may share a five-character stem.
        prefixes = [c.lower()[:5] for c in q['choices'] if len(c) >= 5]
        assert len(prefixes) == len(set(prefixes)), 'look-alike options: {}'.format(q['choices'])
        body = q['prompt'].split('\n\n')[-1]
        assert not body.lstrip().startswith('______'), 'blank opens the stem'


def test_no_young_item_has_two_defensible_answers(curr):
    """Regression: a mechanical pass once injected a third option into binary
    items and produced 'Which one is alive? 🐶 🚚' with 🐛 among the choices —
    two correct answers. Items must come from the authored set untouched."""
    living = {'🐶', '🐱', '🐛', '🦋', '🌳', '🌱', '🐟', '🐦', '🐘', '🦆', '🐝', '🌸'}
    for node in curr.nodes.values():
        if node['stage'] > 1:
            continue
        for q in node.get('quiz', []):
            if 'alive' not in q.get('prompt', '').lower():
                continue
            alive_options = [c for c in q.get('choices', []) if c in living]
            assert len(alive_options) <= 1, \
                '{}: {} has {} living options'.format(node['id'], q['prompt'], len(alive_options))


def test_young_items_are_internally_consistent(curr):
    """Every young item's answer must be one of its own options, and its spoken
    line must not simply read the answer out."""
    for node in curr.nodes.values():
        if node['stage'] > 1:
            continue
        for q in node.get('quiz', []):
            assert q['answer'] in q['choices'], '{}: {}'.format(node['id'], q['prompt'])
            assert q.get('say'), '{}: unvoiced item'.format(node['id'])


def test_generated_questions_never_reach_a_graded_quiz(open_assessment_gate):
    """An independent audit put auto-cloze at ~65% defective — mostly items
    solvable from grammar alone, some with more than one defensible answer.
    Every curriculum node now has authored items, so nothing that moves mastery
    is allowed to use generated prose — and since the 2026-08 audit put the
    rate at 55% even after a precision pass, they no longer survive anywhere in
    the app: the self-check that served them is retired.
    """
    from fastapi.testclient import TestClient
    import primer.server as srv
    client = TestClient(srv.app)
    for node in ('math.2.fractions', 'phys.3.mechanics', 'bio.4.molecular',
                 'cs.5.complexity', 'hist.2.civilizations', 'arts.3.music-theory'):
        paper = client.get('/api/quiz/{}?n=6'.format(node)).json()
        assert paper['questions'], node
        for q in paper['questions']:
            assert not q['prompt'].startswith('Fill in the blank'), \
                '{} serves a generated cloze item in a graded quiz'.format(node)


def test_every_node_can_be_assessed_without_generated_prose(curr):
    orphans = [n['id'] for n in curr.nodes.values()
               if not n.get('quiz') and not n.get('practice')]
    assert not orphans, 'nodes with no authored assessment: {}'.format(orphans[:5])


def test_every_stage_offers_at_least_two_assessment_formats(open_assessment_gate):
    """One format is not an assessment: recognition alone cannot separate
    knowing from guessing, at any age."""
    from fastapi.testclient import TestClient
    import primer.server as srv
    client = TestClient(srv.app)
    for node in ('math.0.counting', 'math.1.addition', 'math.2.fractions',
                 'math.3.quadratics', 'math.4.linalg', 'math.5.topology'):
        kinds = {q['kind'] for q in client.get('/api/quiz/{}?n=5'.format(node)).json()['questions']}
        assert len(kinds) >= 2, '{} offers only {}'.format(node, kinds)


def test_history_stage_zero_options_carry_no_length_cue():
    """Regression: 76% of these keyed the longest option (+26pp over chance)."""
    import json as _json
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'data', 'curriculum', '07-history.json')
    with open(path) as f:
        data = _json.load(f)
    total = cued = 0
    for node in data['nodes']:
        if node['stage'] != 0:
            continue
        for q in node.get('quiz', []):
            cs = q.get('choices') or []
            if len(cs) < 2 or not all(c.isascii() for c in cs):
                continue
            total += 1
            if max(cs, key=len) == q['answer'] and len(q['answer']) > min(len(c) for c in cs):
                cued += 1
    assert total >= 15
    assert cued / total <= 0.45, 'length cue on {:.0%} of items'.format(cued / total)


def test_a_card_the_reader_wrote_is_not_evidence(store):
    """Regression: a decayed node was fully restored by adding a card with
    front 'q', back 'a' and self-grading it 5. A note the reader writes for
    themselves is worth studying; it is not proof they know something."""
    store.record_attempt('n', 1.0)
    with store._conn() as c:
        c.execute("UPDATE mastery SET mastered_at=?, strength=0.2, passes=2 WHERE node_id='n'",
                  (time.time() - 90 * 86400,))
    store.add_cards([{'front': 'q', 'back': 'a', 'node_id': 'n', 'origin': 'reader'}])
    all_due(store)
    mine = [c for c in store.due_cards() if c['front'] == 'q'][0]
    store.review_card(mine['id'], 5)
    with store._conn() as c:
        after = c.execute("SELECT strength FROM mastery WHERE node_id='n'").fetchone()[0]
    assert after <= 0.2, 'a self-authored card must not restore strength'

    store.add_cards([{'front': 'real', 'back': 'b', 'node_id': 'n'}])   # book-minted
    all_due(store)
    theirs = [c for c in store.due_cards() if c['front'] == 'real'][0]
    store.review_card(theirs['id'], 5)
    with store._conn() as c:
        assert c.execute("SELECT strength FROM mastery WHERE node_id='n'").fetchone()[0] > after


def test_drilling_one_card_is_not_progress(store):
    """Regression: `/api/review` had no due check, so 50 repeats of a single
    card paid 250 XP and kept topping up a node's strength."""
    store.add_cards([{'front': 'f', 'back': 'b', 'node_id': 'n'}])
    all_due(store)
    cid = store.due_cards()[0]['id']
    first = store.review_card(cid, 5)
    assert first['xp_gained'] > 0
    repeats = [store.review_card(cid, 5) for _ in range(20)]
    assert all(r['xp_gained'] == 0 and r.get('early') for r in repeats)
    assert sum(r['xp_gained'] for r in repeats) == 0


def test_the_book_tells_one_story_about_what_is_mastered(store):
    """Regression: `proven_set` ignored decay while `gate_map` applied it, so
    the curriculum called a node unmastered, its own page called it mastered,
    and today's list counted neither."""
    store.record_attempt('n', 1.0)
    with store._conn() as c:
        c.execute("UPDATE mastery SET mastered_at=?, first_mastered_at=?, strength=1.0, "
                  "last_seen=?, passes=2 WHERE node_id='n'",
                  (time.time() - 400 * 86400, time.time() - 400 * 86400, time.time() - 400 * 86400))
    assert 'n' not in store.proven_set(), 'a faded node is not currently proven'
    assert store.gate_map().get('n', 1.0) < 1.0, 'and its gate is closed too'
    assert 'n' in store.ever_proven_set(), 'but the history of having done it stands'


# ---------------- interface invariants ----------------
#
# These read the served files rather than a browser. They are not a substitute
# for running the app — the real audits were done in one — but they catch the
# specific regressions the board found, which were all one edit away from
# coming back.

def _web(name):
    import os
    from primer.wiki import ROOT
    with open(os.path.join(ROOT, "web", name)) as fh:
        return fh.read()


def test_text_on_a_coloured_fill_flips_with_the_theme():
    """Regression: fills lighten in dark mode while their text stayed `#fff`, so
    the completed-quest tick measured 2.00:1 — the primary completion indicator
    on the Today screen — and the *selected* onboarding chip (2.69:1) was less
    readable than the unselected one (7.61:1)."""
    css = _web("styles.css")
    for sel in (".quest-item.done .tick", ".chip.on"):
        line = next(l for l in css.splitlines() if l.strip().startswith(sel))
        assert "var(--on-fill)" in line, line
        assert "#fff" not in line, line
    assert css.count("--on-fill:") >= 3, "light base and both dark blocks"


def test_older_readers_get_their_own_mode():
    """Regression: stages 0-2 had 30 rules between them and stages 3, 4 and 5 had
    none, so a graduate read the same screen as a nine-year-old with the scaling
    switched off."""
    css = _web("styles.css")
    for stage in ("3", "4", "5"):
        assert css.count('body[data-stage="{}"]'.format(stage)) >= 2, stage


def test_the_youngest_reader_does_not_get_the_smallest_text():
    """Regression: `body[data-stage="0"] .navbtn .label { font-size: 13px }` —
    the smallest nav label in the book, on the pre-reader's screen, against an
    adult default of 15px."""
    css = _web("styles.css")
    line = next(l for l in css.splitlines()
                if 'data-stage="0"' in l and ".navbtn .label" in l)
    assert "13px" not in line, line
    assert "var(--ui-scale)" in line, line


def test_feedback_regions_are_mounted_before_they_are_filled():
    """Regression: every in-card `role="status"` was created already containing
    its text, which assistive tech announces unreliably or not at all. They are
    now mounted empty once and written into."""
    js = _web("app.js")
    assert "class: 'q-live', role: 'status'" in js
    # The old pattern: a status region constructed with its message inline.
    assert "role: 'status' }, m.correct" not in js
    assert "{ class: 'q-nudge', role: 'status' }" not in js


def test_lesson_models_are_local_explanations_not_assessments():
    js = _web('lesson-models.js')
    for renderer in ('counter', 'shape-explorer', 'shadow-lab', 'sequence-runner',
                     'make-ten', 'light-paths', 'algorithm-tracer', 'life-cycle',
                     'fraction-equivalence-lab', 'atom-element-builder',
                     'cell-microscope', 'counterexample-lab',
                     'integer-number-line-lab',
                     'function-composition-lab', 'circulation-route-lab',
                     'truth-table-lab', 'stack-queue-lab',
                     'matrix-transform-lab', 'venturi-flow-lab',
                     'gene-expression-stepper', 'tcp-packet-tracer',
                     'heat-equation-lab', 'complexity-certificate-lab',
                     'morphogen-gradient-lab', 'ct-window-lab',
                     'alphabet-explorer', 'inclusive-family-timeline',
                     'day-night-rotation-lab', 'classroom-paint-mixer',
                     'physics-concept-lab'):
        assert renderer in js
    assert 'fetch(' not in js and '/api/' not in js
    assert "role: 'status'" in js and "'aria-live': 'polite'" in js
    assert "type: 'range'" in js and "type: 'button'" in js
    assert 'runPackBag' in js and 'traceJamSandwich' in js and 'Read this activity aloud' in js
    assert 'PrimerLessonModels' in _web('app.js')
    assert '.model-pebble' in _web('styles.css') and '.make-ten-frame' in _web('styles.css')


def test_physics_scenario_registry_matches_python_and_curriculum_exactly(curr):
    js = _web('lesson-models.js')
    start = js.index('const PHYSICS_SCENARIOS = Object.freeze({')
    end = js.index('function formatPhysicsControl(', start)
    registry = js[start:end]
    scenario_keys = set(re.findall(r"^    '(phys\.[^']+)': \{", registry, re.MULTILINE))
    expected = {
        nid for nid, node in curr.nodes.items()
        if nid.startswith('phys.') and
        node['lesson_media'][-1]['renderer'] == 'physics-concept-lab'
    }
    assert scenario_keys == set(PHYSICS_MODEL_SCENARIOS) == expected
    assert len(scenario_keys) == 36
    assert registry.count('controls: [') == 36
    assert registry.count('caveat:') == 36
    assert registry.count('compute(state)') == 36
    assert registry.count('readout:') >= 36
    assert registry.count('visual:') == 36


def test_physics_model_has_native_controls_resets_live_copy_and_fail_closed_lookup():
    js = _web('lesson-models.js')
    css = _web('styles.css')
    start = js.index('function renderPhysicsConceptLab(')
    end = js.index('const RENDERERS = Object.freeze({', start)
    renderer = js[start:end]
    assert "'physics-concept-lab': renderPhysicsConceptLab" in js
    assert "type: 'range'" in renderer and "type: 'button'" in renderer
    assert "'aria-valuetext'" in renderer and "node('output'" in renderer
    assert "'Reset to the authored starting state'" in renderer
    assert "Object.prototype.hasOwnProperty.call(PHYSICS_SCENARIOS, scenarioId)" in renderer
    assert 'refresh(false)' in renderer and 'onchange:' in renderer
    assert 'physics-svg-scroll' in renderer and 'physics-visual-summary' in renderer
    assert '.physics-svg-scroll' in css and 'overflow-x: auto' in css
    assert '.physics-control-grid' in css and '.physics-slider-value' in css


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js is unavailable')
def test_every_physics_model_control_changes_readout_and_svg_geometry():
    """Execute the shipped renderer, not a parallel copy of its formulas."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = subprocess.run(
        ['node', os.path.join(root, 'tools', 'check_physics_models.js')],
        cwd=root, capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '36 scenarios, 62 independently exercised controls' in result.stdout


def test_sapling_lesson_models_keep_the_read_aloud_control():
    js = _web('app.js')
    media = js[js.index('function renderLessonMedia('):js.index('async function renderNode(')]
    assert 'speakButton: S.stage <= 2 ?' in media
    assert 'speakButton: S.stage <= 1 ?' not in media
    assert 'if (n.kid_text && S.stage <= 1)' in js, \
        'the model-only speech change must not restore automatic older-reader narration'


def test_sapling_model_accessibility_geometry_registration_and_resets():
    """Keep the four Sapling manipulatives usable, not merely named in source."""
    js = _web('lesson-models.js')
    css = _web('styles.css')

    def px_after(text, marker):
        start = text.index(marker) + len(marker)
        return int(text[start:text.index('px', start)])

    for renderer, function in (
        ('fraction-equivalence-lab', 'renderFractionEquivalence'),
        ('atom-element-builder', 'renderAtomElementBuilder'),
        ('cell-microscope', 'renderCellMicroscope'),
        ('counterexample-lab', 'renderCounterexampleLab'),
    ):
        assert "'{}': {}".format(renderer, function) in js

    legend_declaration = js[js.index("const legend = node('div'"):
                            js.index('const specimenButtons', js.index("const legend = node('div'"))]
    assert "class: 'microscope-legend'" in legend_declaration
    assert "'aria-hidden'" not in legend_declaration
    assert "Structures present in this specimen: ' + detail.structures.join(', ')" in js
    assert "role: 'list', 'aria-label': 'Structures present in this specimen'" in js
    assert "role: 'listitem'" in js

    inner_shell = px_after(css, '.atom-shell.is-inner { width: ')
    nucleus_block = css[css.index('.atom-nucleus {'):css.index('}', css.index('.atom-nucleus {'))]
    nucleus = px_after(nucleus_block, 'width: ')
    inner_radius = px_after(js, "--electron-radius', inner ? '")
    electron_radius = 7
    assert inner_shell > nucleus
    assert inner_radius - electron_radius > nucleus / 2

    for reset in (
        'factor = 1;',
        'Object.assign(values, authored);',
        'specimen = authoredSpecimen;',
        'magnification = authoredMagnification;',
        "state = 'forward';",
    ):
        assert js.count(reset) >= 2 or reset == 'Object.assign(values, authored);'


def test_integer_number_line_registration_accessibility_reset_and_accuracy(curr):
    """The first next-stage mathematics model stays exact and independently usable."""
    js = _web('lesson-models.js')
    css = _web('styles.css')
    start = js.index('function renderIntegerNumberLine(')
    end = js.index('\n  function renderFunctionComposition(', start)
    source = js[start:end]
    lower = source.lower()

    assert "'integer-number-line-lab': renderIntegerNumberLine" in js
    model = next(item for item in curr.nodes['math.2.negatives']['lesson_media']
                 if item['kind'] == 'model')
    assert model['renderer'] == 'integer-number-line-lab'
    assert model['props'] == {
        'min': -12, 'max': 12, 'start_value': -2, 'start_delta': -7,
    }

    assert "type: 'range'" in source and source.count("type: 'button'") >= 4
    assert "role: 'group'" in source and 'aria-label' in source
    assert "'aria-valuetext'" in source
    assert "'Reset'" in source and "'Apply move'" in source
    assert 'frame.controls.append' in source
    assert 'frame.readout.textContent' in source
    assert 'frame.status.textContent' in source
    assert source.count('value = authored.startValue;') >= 2
    assert source.count('delta = authored.startDelta;') >= 2

    for phrase in ('current position', 'signed move', 'farther right is greater',
                   'absolute value', 'distance from zero', 'units left', 'units right'):
        assert phrase in lower
    assert 'bigger digit' not in lower
    assert 'math.abs(target)' in lower
    assert 'number.isinteger' in lower

    for selector in ('.integer-number-line-scene', '.integer-number-line-svg',
                     '.integer-number-line-key', '.integer-number-line-buttons'):
        assert selector in css
    button_rule = css[css.index('.integer-number-line-buttons .btn {'):
                      css.index('}', css.index('.integer-number-line-buttons .btn {'))]
    assert 'min-width: 44px' in button_rule
    assert '@media (max-width: 600px)' in css


def test_tree_model_registration_accessibility_resets_and_accuracy_caveats():
    """Keep Tree's four local explanations operable and scientifically honest."""
    js = _web('lesson-models.js')

    def function_source(name):
        start = js.index('function {}('.format(name))
        end = js.find('\n  function ', start + 1)
        if end < 0:
            end = js.index('\n  const RENDERERS', start)
        return js[start:end]

    for renderer, function in (
        ('function-composition-lab', 'renderFunctionComposition'),
        ('circulation-route-lab', 'renderCirculationRoute'),
        ('truth-table-lab', 'renderTruthTable'),
        ('stack-queue-lab', 'renderStackQueue'),
    ):
        assert "'{}': {}".format(renderer, function) in js
        source = function_source(function)
        assert "type: 'button'" in source
        assert "'Reset'" in source
        assert 'frame.controls.append' in source
        assert 'frame.readout.textContent' in source
        assert 'frame.status.textContent' in source

    assert 'fetch(' not in js and '/api/' not in js
    model_frame = js[js.index('function modelFrame('):js.index('function clampNumber(')]
    assert "role: 'status'" in model_frame and "'aria-live': 'polite'" in model_frame

    lower = js.lower()
    for accuracy_phrase in (
        'not commutative', 'pulmonary arter', 'pulmonary vein', 'schematic',
        'material implication', 'false only when', 'last-in, first-out',
        'first-in, first-out',
    ):
        assert accuracy_phrase in lower


def test_grove_model_registration_accessibility_resets_and_accuracy_caveats():
    """Keep Grove's four deterministic models operable and technically exact."""
    js = _web('lesson-models.js')
    css = _web('styles.css')

    def function_source(name):
        start = js.index('function {}('.format(name))
        end = js.find('\n  function ', start + 1)
        if end < 0:
            end = js.index('\n  const RENDERERS', start)
        return js[start:end]

    for renderer, function in (
        ('matrix-transform-lab', 'renderMatrixTransform'),
        ('venturi-flow-lab', 'renderVenturiFlow'),
        ('gene-expression-stepper', 'renderGeneExpression'),
        ('tcp-packet-tracer', 'renderTcpPacketTracer'),
    ):
        assert "'{}': {}".format(renderer, function) in js
        source = function_source(function)
        assert "type: 'button'" in source
        assert "'Reset'" in source
        assert 'frame.controls.append' in source
        assert 'frame.readout.textContent' in source
        assert 'frame.status.textContent' in source

    assert 'fetch(' not in js and '/api/' not in js
    for reset in ('selected = authoredTransform;', 'selected = authoredThroat;',
                  'stage = authoredStage;', 'step = 0;'):
        assert reset in js

    lower = js.lower()
    for accuracy_phrase in (
        'signed area', 'not invertible', '400 cm³/s', 'drop: 1.5', 'drop: 7.5',
        'atg gaa ttt taa', 'aug gaa uuu uaa', 'met–glu–phe',
        'two duplicate acknowledgements', 'not the three needed for fast retransmit',
        'ack 5', 'count byte positions',
    ):
        assert accuracy_phrase in lower

    for selector in ('.matrix-transform-scene', '.venturi-diagram',
                     '.gene-expression-scene', '.tcp-packet-track'):
        assert selector in css


def test_forest_model_registration_accessibility_resets_and_accuracy_caveats():
    """Keep Forest's four deterministic models operable and technically exact."""
    js = _web('lesson-models.js')
    css = _web('styles.css')

    def function_source(name):
        start = js.index('function {}('.format(name))
        end = js.find('\n  function ', start + 1)
        if end < 0:
            end = js.index('\n  const RENDERERS', start)
        return js[start:end]

    for renderer, function in (
        ('heat-equation-lab', 'renderHeatEquation'),
        ('complexity-certificate-lab', 'renderComplexityCertificate'),
        ('morphogen-gradient-lab', 'renderMorphogenGradient'),
        ('ct-window-lab', 'renderCtWindow'),
    ):
        assert "'{}': {}".format(renderer, function) in js
        source = function_source(function)
        assert "type: 'button'" in source
        assert "'Reset'" in source
        assert 'frame.controls.append' in source
        assert 'frame.readout.textContent' in source
        assert 'frame.status.textContent' in source

    assert 'fetch(' not in js and '/api/' not in js

    lower = js.lower()
    for accuracy_phrase in (
        'no-flux boundaries', 'total heat is conserved', 'r = 0.20',
        'p versus np remains open', 'polynomial examples do not prove',
        'certificate', 'illustrative thresholds', '100 × 0.80',
        'dicom linear voi', 'width − 1', 'synthetic phantom',
        'not a diagnosis',
    ):
        assert accuracy_phrase in lower

    for selector in ('.heat-equation-scene', '.complexity-certificate-scene',
                     '.morphogen-gradient-scene', '.ct-window-scene'):
        assert selector in css


def test_second_seedling_model_registration_accessibility_resets_and_guardrails():
    """Keep Seedling pass two local, inclusive, operable and honest."""
    js = _web('lesson-models.js')
    css = _web('styles.css')

    def function_source(name):
        start = js.index('function {}('.format(name))
        end = js.find('\n  function ', start + 1)
        if end < 0:
            end = js.index('\n  const RENDERERS', start)
        return js[start:end]

    sources = {}
    for renderer, function in (
        ('alphabet-explorer', 'renderAlphabetExplorer'),
        ('inclusive-family-timeline', 'renderInclusiveFamilyTimeline'),
        ('day-night-rotation-lab', 'renderDayNightRotation'),
        ('classroom-paint-mixer', 'renderClassroomPaintMixer'),
    ):
        assert "'{}': {}".format(renderer, function) in js
        source = function_source(function)
        sources[renderer] = source.lower()
        assert "type: 'button'" in source
        assert "'Reset'" in source
        assert 'frame.controls.append' in source
        assert 'frame.readout.textContent' in source
        assert 'frame.status.textContent' in source
        assert 'aria-label' in source
        assert 'authored' in source.lower(), '{} reset must restore authored state'.format(renderer)

    assert 'fetch(' not in js and '/api/' not in js

    alphabet = sources['alphabet-explorer']
    assert 'more than one sound' in alphabet
    assert 'one common example' in alphabet
    assert 'index = authored.index;' in alphabet

    family = sources['inclusive-family-timeline']
    assert 'fictional family' in family
    assert 'biological, adoptive, foster, blended, or chosen' in family
    assert 'no names, dates, or personal information' in family
    assert "node('input'" not in family and 'contenteditable' not in family
    assert 'mode = authored.mode;' in family and 'index = authored.index;' in family
    assert "role: 'group', 'aria-label': 'choose timeline scale'" in family

    rotation = sources['day-night-rotation-lab']
    for phrase in ('earth rotates eastward', 'equinox at the equator',
                   'moon can appear during the day', 'stars are still present'):
        assert phrase in rotation
    assert 'index = authored.index;' in rotation

    paint = sources['classroom-paint-mixer']
    for phrase in ('approximate classroom paint', 'equal parts',
                   'real pigments', 'additive light'):
        assert phrase in paint
    assert 'first = authored.first;' in paint and 'second = authored.second;' in paint

    for selector in ('.alphabet-explorer-scene', '.family-timeline-scene',
                     '.day-night-rotation-scene', '.paint-mixer-scene'):
        assert selector in css
    assert 'repeat(auto-fill, minmax(44px, 1fr))' in css
    assert 'repeat(2, minmax(62px, 1fr))' in css


def test_second_sprout_model_registration_accessibility_resets_and_guardrails():
    """Keep Sprout pass two local, keyboard-operable and conceptually honest."""
    js = _web('lesson-models.js')
    css = _web('styles.css')

    def function_source(name):
        start = js.index('function {}('.format(name))
        end = js.find('\n  function ', start + 1)
        if end < 0:
            end = js.index('\n  const RENDERERS', start)
        return js[start:end]

    sources = {}
    for renderer, function in (
        ('reading-path-lab', 'renderReadingPath'),
        ('timeline-order-lab', 'renderTimelineOrder'),
        ('seasons-tilt-lab', 'renderSeasonsTilt'),
        ('art-elements-composer', 'renderArtElementsComposer'),
    ):
        assert "'{}': {}".format(renderer, function) in js
        source = function_source(function)
        sources[renderer] = source.lower()
        assert "type: 'button'" in source
        assert "'Reset'" in source
        assert 'frame.controls.append' in source
        assert 'frame.readout.textContent' in source
        assert 'frame.status.textContent' in source
        assert 'aria-label' in source
        assert 'authored' in source.lower(), \
            '{} reset must restore authored state'.format(renderer)

    assert 'fetch(' not in js and '/api/' not in js

    reading = sources['reading-path-lab']
    for phrase in ('one simple english example', 'blending is one reading strategy',
                   'irregular word', 'accents can differ', 'other scripts',
                   'audio, braille, assistive technology'):
        assert phrase in reading
    assert 'phase = authoredphase;' in reading
    assert "role: 'group'" in reading and 'choose a reading step' in reading
    assert 'the cat sat.' in reading and 'a cat sat.' not in reading
    assert '“the cat sat.” tells who' in reading
    assert 'c spells k' not in reading and 'k, short a, t' not in reading
    assert 'first sound in cup' in reading and 'first sound in top' in reading
    assert "'data-model-speak-text': detail.spoken" in reading
    assert "'aria-label': detail.spoken" not in reading

    timeline = sources['timeline-order-lab']
    for phrase in ('fictional timeline', 'earlier dates on the left',
                   'other timeline layouts', 'historians check dates against sources'):
        assert phrase in timeline
    assert 'order = authoredorder.slice();' in timeline
    assert 'list.append(row.element);' in timeline and '.focus();' in timeline
    assert "role: 'group'" in timeline and 'order the fictional library events' in timeline
    assert "row.eventspeech.setattribute('data-model-speak-text'" in timeline, \
        'timeline read-aloud labels need punctuation and current positions'
    assert "row.eventspeech.setattribute('aria-label'" not in timeline
    assert '.timeline-order-copy > small { display: block; }' in css.replace('\n', ' '), \
        'timeline event labels and details need a visible text break'

    seasons = sources['seasons-tilt-lab']
    for phrase in ('axes stay parallel', 'not-to-scale',
                   'distance from the sun does not cause the seasons',
                   'opposite seasons', 'temperate regions'):
        assert phrase in seasons
    assert 'position = authoredposition;' in seasons
    assert 'hemisphere = authoredhemisphere;' in seasons
    assert seasons.count("role: 'group'") >= 2
    assert 'choose a key position' in seasons and 'choose a hemisphere' in seasons
    assert "position = detail.id;\n          refresh(true);" in seasons, \
        'position announcements need both hemispheres and their seasonal labels'
    assert 'align-items: stretch; gap: 8px;' in css, \
        'season position buttons need equal row heights when labels wrap'

    art = sources['art-elements-composer']
    for phrase in ('not an exhaustive rulebook', 'visual texture suggests touch',
                   'color from being the sole signal', 'people and cultures'):
        assert phrase in art
    assert 'activeelements = new set(authoredelements);' in art
    assert 'activeelements.clear();' in art and "'clear board'" in art
    assert "? 'added: ' : 'removed: '" in art
    assert "role: 'group'" in art and 'choose visual elements' in art
    assert '.art-element-layer[hidden] { display: none; }' in css, \
        'the pattern grid must not override the native hidden state'

    for selector in ('.reading-path-scene', '.timeline-order-scene',
                     '.seasons-tilt-scene', '.art-elements-scene'):
        assert selector in css


def test_a_repaint_cannot_break_out_of_an_open_dialog():
    """Regression: a background refresh called renderRoute() while an
    aria-modal dialog was open and moved focus to #page, so Tab walked the whole
    background. On localhost the race was invisible; at 250ms it was reliable.
    The fix belongs inside renderRoute() itself (it already knows never to
    steal focus from an open dialog) — an earlier attempt instead skipped
    calling renderRoute() at all from stageAscension() whenever a modal was
    open, which "fixed" the focus theft by leaving #page permanently blank:
    renderShell() unconditionally wipes and rebuilds an empty <main id="page">,
    and nothing filled it back in once every modal closed on a route that
    hadn't changed. stageAscension() must always call renderRoute() and rely
    on its own internal guard, not skip the repaint."""
    js = _web("app.js")
    assert "if (!_modalStack.length) page.focus({ preventScroll: true })" in js
    assert "if (!_modalStack.length) renderRoute();" not in js, \
        "renderRoute() must not be skipped while a modal is open — it already " \
        "refuses to steal focus on its own; skipping it entirely blanks #page"


def test_dimmed_cards_do_not_dim_their_own_text():
    """Regression: locked and set-aside story chapters were `opacity:.55`/`.7`
    on the whole card, which multiplies the text down too — 2.20:1 and 2.81:1."""
    js = _web("app.js")
    assert "opacity:0.55" not in js and "opacity:0.7" not in js
    assert "card-quiet" in js and ".card-quiet" in _web("styles.css")


# ---------------- item bank standards ----------------

def _banks():
    import glob
    import json as _j
    import os
    from primer.wiki import ROOT
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "curriculum", "*.json"))):
        yield os.path.basename(f), _j.load(open(f))


def test_every_bank_is_deep_enough_that_two_passes_differ():
    """Regression: stage 2 nodes carried exactly 2 items and stages 3-5 exactly
    3, on all 254 of them. A quiz serves up to 6 and mastery needs two spaced
    passes — so both passes showed the identical paper, and the second measured
    recall of the answers rather than the idea."""
    thin = []
    for name, d in _banks():
        for n in d["nodes"]:
            if n.get("stage", 0) >= 2 and len(n.get("quiz") or []) < 10:
                thin.append((name, n["id"], len(n.get("quiz") or [])))
    assert not thin, "banks below 10 items: {}".format(thin[:8])


def test_every_older_node_can_ask_the_reader_to_produce():
    """Recognition alone flatters the reader. Only 58 of 254 stage-2+ nodes had
    an authored produced-response item; the rest leaned on a generated one whose
    key was the node's published `goal`."""
    missing = []
    for name, d in _banks():
        for n in d["nodes"]:
            if n.get("stage", 0) < 2:
                continue
            if not any(q.get("kind") in ("numeric", "short") for q in (n.get("quiz") or [])):
                missing.append(n["id"])
    assert not missing, "no produced-response item: {}".format(missing[:8])


def test_short_answer_keys_are_hand_written():
    """A `short` item scored on keywords needs keywords chosen for the purpose —
    the generated ones drew on whatever words the goal happened to use, so a
    correct account of order-of-operations lost a quarter of its marks for not
    saying 'mathematicians'."""
    bad = []
    for name, d in _banks():
        for n in d["nodes"]:
            for q in n.get("quiz") or []:
                if q.get("kind") == "short" and len(q.get("keywords") or []) < 3:
                    bad.append((n["id"], q.get("prompt", "")[:40]))
    assert not bad, "short items with thin keys: {}".format(bad[:6])


def test_picking_by_length_still_cannot_pass_a_paper(open_assessment_gate):
    """The residue, measured honestly.

    Three rounds of chasing the length statistic produced longest-key, then
    first-position, then shortest-key — each fix overshooting into the opposite
    tell. What matters is not where the key sits in a length ranking but whether
    reading length lets someone through the gate. It does not: a shortest-picker
    gains about five points of marks and passes nothing.

    This is the guard that counts. The per-domain edge is tracked separately by
    tools/check_banks.py, which reports it as an authoring standard rather than
    a security property.
    """
    import random
    import statistics
    from fastapi.testclient import TestClient
    import primer.server as srv

    client = TestClient(srv.app)
    client.post("/api/profile", json={
        "name": "Len", "age": 12, "hours_per_week": 15, "breadth": "balanced",
        "domains": [d["id"] for d in srv.curr.domains]})
    rng = random.Random(99)
    sample = rng.sample([n["id"] for n in srv.curr.nodes.values() if n["stage"] >= 2], 90)
    # /api/quiz draws its n=5 items from each node's bank via quiz.R, a
    # module-level random.Random shared with every other test in the
    # process — the node SAMPLE above is seeded and deterministic, but
    # which items get served for each node was not, so this measurement
    # depended on suite execution order. Seed it too for a reproducible read.
    quiz.R.seed(20260807)
    # ...and the module-level `random` the server actually draws items with
    # (_draw_from_bank at server.py:904). Seeding only quiz.R left this
    # measurement order-dependent: it read differently depending on how much
    # global randomness earlier tests had consumed, which is how a 1-in-3
    # flake hid behind a comment claiming reproducibility.
    random.seed(20260807)

    for how in ("shortest", "longest"):
        scores = []
        for nid in sample:
            paper = client.get("/api/quiz/{}?n=5".format(nid)).json()
            if "token" not in paper:
                continue
            served = srv._SERVED[paper["token"]]["questions"]
            graded = []
            for pub, q in zip(paper["questions"], served):
                if q.get("ungraded"):
                    continue
                ch = pub.get("choices") or []
                choice = "" if not ch else (min(ch, key=len) if how == "shortest"
                                            else max(ch, key=len))
                graded.append(str(choice).strip().lower()
                              == str(q.get("answer", "")).strip().lower())
            if graded:
                scores.append(sum(graded) / len(graded))
        passing = sum(s >= 0.8 for s in scores) / len(scores)
        assert passing <= 0.02, \
            "'{}' passes {:.1%} of papers".format(how, passing)
        assert statistics.mean(scores) < 0.30, \
            "'{}' scores {:.1%}".format(how, statistics.mean(scores))


def test_the_key_is_not_findable_by_its_length():
    """Regression, third time: the answer was longest, then first, then
    second-longest at 46% (chance 25%), where 'pick the second-longest' scored
    44%. Every rank must sit near chance, not just the extremes."""
    import collections
    rank = collections.Counter()
    for _, d in _banks():
        for n in d["nodes"]:
            if n.get("stage", 0) < 2:
                continue
            for q in n.get("quiz") or []:
                ch = q.get("choices") or []
                if len(ch) == 4 and q.get("answer") in ch:
                    rank[sorted(ch, key=len).index(q["answer"])] += 1
    total = sum(rank.values())
    assert total > 400, "expected a large four-option pool, got {}".format(total)
    for r in range(4):
        share = rank[r] / total
        # A loose bound only. Optimising this number directly is what produced
        # three successive tells; `test_picking_by_length_still_cannot_pass_a_paper`
        # is the guard that matters.
        assert 0.12 <= share <= 0.40, \
            "length-rank {} holds {:.0%} of keys (chance is 25%)".format(r, share)


def test_the_graduate_stage_is_not_a_glossary():
    """Regression: stage 5 was the most recall-bound stage in the book — 24.5%
    bare definitions and only 7.5% posing a novel situation, which is backwards.
    """
    import re
    banned = re.compile(r"\b(refers to|is best described as|is defined as)\b", re.I)
    offenders = []
    for _, d in _banks():
        for n in d["nodes"]:
            if n.get("stage", 0) < 4:
                continue
            for q in n.get("quiz") or []:
                if banned.search(q.get("prompt", "")):
                    offenders.append((n["id"], q["prompt"][:50]))
    assert not offenders, "definitional stems at stage 4-5: {}".format(offenders[:6])


def test_knowing_nothing_scores_like_knowing_nothing(open_assessment_gate):
    """The end-to-end version of the surface-cue tests: sit real papers from the
    live API with several knowledge-free strategies and check none of them beats
    chance or clears a mastery gate.

    At audit, a solver that read only the served JSON scored 63-65% and cleared
    the gate on 83-88 of 343 nodes, because `explain` shipped with the paper and
    named the answer. "Pick the second-longest" scored 44%.
    """
    import random
    import statistics
    from fastapi.testclient import TestClient
    import primer.server as srv

    client = TestClient(srv.app)
    client.post("/api/profile", json={
        "name": "Cue", "age": 10, "hours_per_week": 15, "breadth": "balanced",
        "domains": [d["id"] for d in srv.curr.domains]})
    rng = random.Random(11)
    sample = rng.sample([n["id"] for n in srv.curr.nodes.values() if n["stage"] >= 2], 60)

    def pick(q, how):
        ch = q.get("choices") or []
        if not ch:
            return ""
        if how == "longest":
            return max(ch, key=len)
        if how == "second_longest":
            return sorted(ch, key=len)[max(0, len(ch) - 2)]
        if how == "first":
            return ch[0]
        # "leak": believe anything in the payload that echoes an option
        blob = " ".join(str(v) for k, v in q.items()
                        if k not in ("choices", "id", "kind")).lower()
        hit = [o for o in ch if o and str(o).lower() in blob]
        return hit[0] if hit else sorted(ch, key=len)[max(0, len(ch) - 2)]

    for how in ("first", "longest", "second_longest", "leak"):
        scores = []
        for nid in sample:
            paper = client.get("/api/quiz/{}?n=6".format(nid)).json()
            served = srv._SERVED[paper["token"]]["questions"]
            graded = [(pick(pub, how), q.get("answer", ""))
                      for pub, q in zip(paper["questions"], served)
                      if not q.get("ungraded")]
            if not graded:
                continue
            right = sum(1 for a, k in graded
                        if str(a).strip().lower() == str(k).strip().lower())
            scores.append(right / len(graded))
        mean = statistics.mean(scores)
        cleared = sum(s >= 0.8 for s in scores) / len(scores)
        assert mean < 0.34, "'{}' scores {:.1%} — a cue, not a guess".format(how, mean)
        assert cleared < 0.05, \
            "'{}' clears the mastery gate on {:.0%} of nodes".format(how, cleared)


def test_the_youngest_papers_are_not_coin_flips():
    """Regression: 61% of stage 0-1 items offered two options (97% in physics),
    so a child who knows nothing passes half of them — at the stage that gates
    the entire ladder above it. Maths and language were already at 17-20% with
    items that work fine for four-year-olds, so the bar was always reachable."""
    binary = total = 0
    worst = []
    for name, d in _banks():
        b = t = 0
        for n in d["nodes"]:
            if n.get("stage", 0) > 1:
                continue
            for q in n.get("quiz") or []:
                if q.get("choices"):
                    t += 1
                    if len(q["choices"]) == 2:
                        b += 1
        if t and b / t > 0.15:
            worst.append((name, b, t))
        binary += b
        total += t
    assert total > 500, "expected a large young bank, got {}".format(total)
    assert not worst, "domains still mostly two-option: {}".format(worst)
    assert binary / total < 0.12, "{:.0%} of young items are coin flips".format(binary / total)


def test_no_young_item_shows_only_its_own_answer():
    """Regression: `phys.1.motion` asked "Ball rolls this way ⬅️. Which arrow?"
    with options ⬅️ ➡️ — the stem displayed the key and nothing else, so the
    child matched a picture. `lang.0.stories` asked "What did the duck lose? 🎩",
    where the emoji *is* the hat."""
    offenders = []
    for _, d in _banks():
        for n in d["nodes"]:
            if n.get("stage", 0) > 1:
                continue
            for q in n.get("quiz") or []:
                ch, ans = q.get("choices") or [], str(q.get("answer", ""))
                stem = q.get("prompt", "")
                if not ch or not ans:
                    continue
                shown = [o for o in ch if str(o) and str(o) in stem]
                if shown == [ans]:
                    offenders.append((n["id"], stem[:44]))
    assert not offenders, "answer is the only option shown: {}".format(offenders[:6])


def test_the_feedback_region_is_never_removed_from_the_tree():
    """Regression, and a subtle one: the JS was fixed to mount an empty live
    region and write into it, and then a single CSS rule — `.q-live:empty
    { display: none }` — undid it. A hidden element is absent from the
    accessibility tree, so revealing it with its text already inside announces
    exactly as badly as inserting a pre-filled region."""
    css = _web("styles.css")
    empty_rules = [l for l in css.splitlines() if ".q-live:empty" in l]
    assert empty_rules, "the empty-state rule should exist, just not hide it"
    for line in empty_rules:
        assert "display: none" not in line and "display:none" not in line, line


def test_the_lesson_card_has_a_perceivable_edge():
    """The primary lesson-launch control was the one component still on the
    decorative hairline: 1.20:1 light, 1.34:1 dark, against SC 1.4.11's 3:1."""
    css = _web("styles.css")
    line = next(l for l in css.splitlines() if l.strip().startswith(".lesson-card {"))
    assert "var(--edge)" in line, line


def test_a_table_keeps_its_rows_and_cells():
    """Regression: `#article table { display: block }` is the usual trick for
    making a wide table scroll, and it strips every row and cell out of the
    accessibility tree — 23 tables on one article, 26 rows and 50 cells gone.
    The table stays a table; a focusable wrapper does the scrolling."""
    from primer.render import rewrite_article
    out = rewrite_article("<p>x</p><table><tr><td>a</td><td>b</td></tr></table>")
    assert '<div class="table-scroll" tabindex="0" role="region" aria-label="Table 1">' in out
    assert out.count("<tr") == 1 and out.count("<td") == 2

    # Nested tables (Wikipedia infoboxes) get one wrapper, not one each.
    nested = rewrite_article(
        "<table><tr><td><table><tr><td>inner</td></tr></table></td></tr></table>")
    assert nested.count("table-scroll") == 1
    assert nested.count("<tr") == 2, "inner rows must survive"

    css = _web("styles.css")
    table_rule = next(l for l in css.splitlines() if l.startswith("#article table {"))
    assert "display: block" not in table_rule, table_rule


MATH_IMG = (
    '<span class="mwe-math-element mwe-math-element-inline">'
    '<img src="https://wikimedia.org/api/rest_v1/media/math/render/svg/abc123"'
    ' class="mwe-math-fallback-image-inline" style="vertical-align: -0.338ex;'
    ' width:6.685ex; height:2.843ex;" alt="{\\displaystyle e^{-E/kT}}"></span>'
)


def test_a_formula_keeps_its_own_size_and_baseline():
    """Wikipedia states a formula's geometry in the image's `style`, in ex —
    none of them carry width/height attributes. `style` is not an allowed
    attribute and must not become one, so the numbers are lifted off before
    sanitizing and written back after, like every other marker this renderer
    owns.

    Without them the browser falls back to the SVG's own root dimensions, which
    resolve against the SVG's default font size and not the reader's: every
    formula frozen at one size whatever stage the reader is at, and every one of
    them off the baseline.
    """
    from primer.render import rewrite_article

    out = rewrite_article(MATH_IMG)
    assert 'style="height:2.843ex;vertical-align:-0.338ex;width:6.685ex"' in out

    # The style is rebuilt from parsed numbers, never echoed: an article cannot
    # smuggle a declaration through the maths path or any other.
    for hostile in (
        '<img src="https://wikimedia.org/api/rest_v1/media/math/render/svg/x"'
        ' style="width:1ex;position:fixed;top:0;left:0;height:100ex">',
        '<img src="https://wikimedia.org/api/rest_v1/media/math/render/svg/y"'
        ' style="width:expression(alert(1))ex">',
        '<img src="https://upload.wikimedia.org/x.png" style="width:9ex">',
        '<p style="position:fixed">x</p>',
        '<div style="background:url(javascript:alert(1))">y</div>',
    ):
        got = rewrite_article(hostile)
        assert "position" not in got and "expression" not in got, got
        assert "javascript" not in got, got

    # A non-maths image is left alone entirely.
    assert "style" not in rewrite_article('<img src="https://upload.wikimedia.org/a.jpg">')


def test_a_picture_reserves_its_own_space():
    """Rebuilding every <img> from src+alt threw away the intrinsic size the
    encyclopedia states — 295 of 416 images in a seven-article sample carry
    both. Each picture then occupied no space until it had loaded, so the
    article reflowed under the reader once per image; with figures set beside
    the prose, a caption appeared first, alone, and jumped when its picture
    arrived.

    Only a plain integer is passed through: the value goes straight into an
    attribute, and `max-width`/`height: auto` in the stylesheet are what keep it
    a ratio rather than a fixed size.
    """
    from primer.render import rewrite_article

    out = rewrite_article(
        '<img src="https://upload.wikimedia.org/a.png" width="500" height="322">')
    assert 'width="500"' in out and 'height="322"' in out

    # Parsoid writes the source file's dimensions before its displayed box.
    # ``\bwidth`` matched the suffix of data-file-width, so a 20px icon backed
    # by a 180px SVG was stretched into a blurry 180px placeholder.  Only the
    # actual HTML width/height attributes reserve layout space.
    parsoid = rewrite_article(
        '<img src="//upload.wikimedia.org/thumb/icon.svg/20px-icon.svg.png" '
        'srcset="//upload.wikimedia.org/thumb/icon.svg/40px-icon.svg.png 2x" '
        'data-file-width="180" data-file-height="185" width="12" height="16" alt="">')
    assert 'width="12"' in parsoid and 'height="16"' in parsoid, parsoid
    assert 'width="180"' not in parsoid and 'height="185"' not in parsoid, parsoid

    metadata_only = rewrite_article(
        '<img src="https://upload.wikimedia.org/a.png" '
        'data-file-width="4000" data-file-height="3000">')
    assert 'width="' not in metadata_only and 'height="' not in metadata_only

    for hostile in ('<img src="https://upload.wikimedia.org/a.png" width="100%">',
                    '<img src="https://upload.wikimedia.org/a.png" width="1e9">',
                    '<img src="https://upload.wikimedia.org/a.png" height="-5">',
                    '<img src="https://upload.wikimedia.org/a.png" width="&quot; onerror=x">'):
        got = rewrite_article(hostile)
        assert 'width="' not in got and 'height="' not in got, got

    css = _web("styles.css")
    assert "height: auto" in css, "a stated width without height:auto distorts"


def test_a_picture_uses_its_sharpest_safe_srcset_candidate():
    """A retina display must not enlarge the low-density fallback thumbnail.

    srcset itself stays out of the sanitized document so every request still
    passes through the Primer's cache/proxy; its best candidate becomes src.
    """
    from primer.render import rewrite_article

    out = rewrite_article(
        '<img src="//upload.wikimedia.org/thumb/map.svg/250px-map.svg.png?x=1&amp;y=2" '
        'srcset="//upload.wikimedia.org/thumb/map.svg/500px-map.svg.png?x=1&amp;y=2 2x" '
        'width="250" height="180" alt="Map">')
    assert "500px-map.svg.png" in out and "250px-map.svg.png" not in out, out
    assert "srcset" not in out
    assert 'width="250"' in out and 'height="180"' in out
    assert 'src="https://' not in out and 'src="//' not in out

    # Invalid/mixed candidates cannot displace a good fallback.
    mixed = rewrite_article(
        '<img src="https://upload.wikimedia.org/fallback.png" '
        'srcset="https://upload.wikimedia.org/a.png 2x, https://upload.wikimedia.org/b.png 900w">')
    assert "fallback.png" in mixed and "a.png" not in mixed and "b.png" not in mixed

    # Presentation markers are data about the pixels, not permission to carry
    # arbitrary upstream classes into the app.  Keep only the two markers that
    # make dark line-work visible on the night page.
    invert = rewrite_article(
        '<img class="mw-file-element skin-invert invented" '
        'src="https://upload.wikimedia.org/hieroglyph.png" alt="glyph">')
    assert 'class="skin-invert"' in invert, invert
    assert "mw-file-element" not in invert and "invented" not in invert
    invert_image = rewrite_article(
        '<img class="skin-invert-image" '
        'src="https://upload.wikimedia.org/line-art.png" alt="line art">')
    assert 'class="skin-invert-image"' in invert_image


def test_an_external_link_is_escaped_exactly_once():
    """fix_link runs downstream of sanitize(), so the href it captures is
    already entity-escaped; escaping it again turned every & in a citation URL
    into &amp;amp;, and the browser then asked Google Books for a page named
    "amp;pg=PA5" — 328 links across a seven-article sample. fix_img has the
    mirror-image fault: it runs on raw source, where values are source-escaped,
    so the image proxy was asked for parameters literally named "amp;utm_…",
    and a formula's alt text spoke "&amp;=" where its LaTeX says "&=".
    """
    import re

    from primer.render import rewrite_article

    out = rewrite_article(
        '<a href="https://books.google.com/books?id=X&amp;q=ratio&amp;pg=7">b</a>')
    assert 'href="https://books.google.com/books?id=X&amp;q=ratio&amp;pg=7"' in out
    assert "&amp;amp;" not in out

    img = rewrite_article(
        '<img src="https://upload.wikimedia.org/a.png?x=1&amp;y=2" alt="a &amp;= b">')
    assert "%26y%3D2" in img and "%26amp%3B" not in img
    assert 'alt="a &amp;= b"' in img

    # A navbox summary is text pulled back out of sanitized markup, so it had
    # the same fault: no title in the sample corpus contains an ampersand,
    # which is exactly how it would have shipped unnoticed.
    navbox = ('<div class="navbox"><table><tbody><tr><th class="navbox-title">'
              "Rock &amp; roll &amp; Newton&#39;s &quot;laws&quot;</th></tr>"
              '<tr><td class="navbox-list">x</td></tr></tbody></table></div>')
    summary = re.search(r"<summary>(.*?)</summary>", rewrite_article(navbox)).group(1)
    assert summary == "Rock &amp; roll &amp; Newton&#x27;s &quot;laws&quot;", summary

    # Un-escaping must not let an entity-encoded scheme back in: the value that
    # comes out of unescape is exactly the one sanitize() already approved.
    for hostile in ('<a href="&#106;avascript:alert(1)">x</a>',
                    '<a href=" javascript:alert(1)">x</a>',
                    '<a href="java&#09;script:alert(1)">x</a>',
                    '<img src="&#106;avascript:alert(1)">'):
        got = rewrite_article(hostile)
        assert "alert(1)" not in got, (hostile, got)

    # …nor let a title break out of the summary element it is written into.
    breakout = rewrite_article(
        '<div class="navbox"><table><tbody><tr><th class="navbox-title">'
        "&lt;/summary&gt;&lt;img src=x onerror=alert(1)&gt;</th></tr>"
        "</tbody></table></div>")
    assert "</summary><img" not in breakout
    assert "onerror=alert(1)>" not in breakout


def test_parsoid_metadata_cannot_leak_into_the_text():
    """Parsoid's <link>/<meta> tags carry template JSON in a single-quoted
    data-mw attribute, and that JSON freely contains `>` — a `<ref ... />`
    inside a quoted string, for instance. The old `[^>]*` tag-stripping regexes
    stopped at the first `>` inside the attribute, so the rest of the JSON fell
    out of the tag and rendered as visible article text: sixteen fragments of
    `"}},"i":0}}]}' id="mwB6Q"` across a seven-article sample, three of them in
    the middle of Isaac Newton's blockquotes.
    """
    from primer.render import rewrite_article

    poem = (
        '<link rel="mw-deduplicated-inline-style" about="#mwt862" '
        'typeof="mw:Extension/templatestyles mw:Transclusion" '
        'data-mw=\'{"parts":[{"template":{"params":{"1":{"wt":'
        '"Nature was hid in night. &lt;ref name=\\"x\\" />"}},"i":0}}]}\' '
        'id="mwB6Q"/><blockquote><p>God said, Let Newton be!</p></blockquote>'
    )
    out = rewrite_article(poem)
    assert "Let Newton be!" in out
    for fragment in ("data-mw", '"i":0', "}}]}", "mwB6Q", '"wt"'):
        assert fragment not in out, (fragment, out)

    # Same shape on a meta tag.
    meta = '<meta property="x" content=\'{"a":"&lt;b />"}\' id="mwF"/><p>after</p>'
    got = rewrite_article(meta)
    assert "after" in got and '"a"' not in got

    # A tag whose quotes do not balance is beyond any parser, and the two
    # failure modes to avoid are opposite ones: showing the raw tag to the
    # reader, and swallowing prose up to the next matching quote (which is what
    # a conformant parser does with `data-m='>` before "Newton's laws" — correct
    # per the spec, and no use at all inside a book).
    for doc, keep in (
        ("<p>Intro.</p><link href=x data-m='><p>Newton's laws.</p><p>Kept.</p>",
         ["Newton's laws", "Kept"]),
        ('<p>Intro.</p><link href=x data-m="> a sentence <em>emph</em> on.<p>B.</p>',
         ["a sentence", "emph", "B."]),
        ("<p>a</p><!-- <link href=x data-m='> --><p>Newton's law.</p><p>b</p>",
         ["Newton's law", "b"]),
    ):
        out = rewrite_article(doc)
        for text in keep:
            assert text in out, (text, out)
        assert "<link" not in out and "&lt;link" not in out, out
        assert "data-m" not in out, out


def test_stripping_an_attribute_cannot_reopen_the_tag():
    """The renderer strips an article's own class/target/rel before stating its
    own, because browsers honour the first of a duplicated attribute. The strip
    patterns ended `[^\\s>]+`, which will happily eat a closing quote: in
    `class="external target=x" title="onclick=alert(1) zz"` the match ran to
    ` target=x"`, quote included, leaving class= unterminated — and the rest of
    the tag re-tokenised into live attributes with onclick among them. Article
    HTML reaches the page through innerHTML, so that is stored XSS arriving
    through the one guarantee the sanitizer exists to give.

    An unquoted value may no longer contain a quote, and the match has to land
    on a real attribute boundary.
    """
    from html.parser import HTMLParser

    from primer.render import rewrite_article

    hostile = ('<a href="https://example.com/x" class="external target=x" '
               'title="onclick=alert(1) zz">read</a>')
    out = rewrite_article(hostile)

    seen = []

    class _Parse(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == "a":
                seen.extend(attrs)

    _Parse().feed(out)
    assert seen, out
    assert not any(name.startswith("on") for name, _ in seen), seen
    # The text survives where it belongs — inside title, which is inert. So is
    # the "target=x" the class value happens to contain: counting raw substrings
    # would find it, which is why the check is on parsed attributes.
    assert ("title", "onclick=alert(1) zz") in seen, seen
    # The hostile `target=x` rides inside a value and stays there: it must never
    # appear as an attribute of its own. (On an external anchor the article's
    # class is now replaced by the book's own marker rather than preserved, so
    # the surviving-value evidence is `title` above; what matters here is that
    # nothing re-tokenised.)
    assert ("class", "primer-outside") in seen, seen
    assert not any(name == "target" for name, _ in seen), seen
    names = [name for name, _ in seen]
    assert names.count("rel") == 1, names

    # A value that really is target is stripped and not restated.
    assert "target=" not in rewrite_article(
        '<a href="https://example.com" target="_blank">x</a>')


def test_an_unquoted_value_cannot_open_a_quoted_run():
    """A quote may open an attribute value only directly after `=`. Allowing one
    anywhere meant a bare apostrophe inside an unquoted value opened a run that
    paired with the next apostrophe in the English prose: `<meta name=Newton's>`
    ran past its own `>`, past "Newton's laws say F", and ended at a raw `>` in
    the body text — taking the sentence with it.

    A tag that cannot be read is declined, which is what hands it to the second
    pass; it is never guessed at.
    """
    from primer.render import rewrite_article

    for doc, keep in (
        ("<p>Intro.</p><meta name=Newton's> Newton's laws say F > ma.<p>Tail.</p>",
         "Newton's laws say F"),
        ("<p>Intro.</p><img src=x alt=Newton's> In 1687 x > y.<p>Tail.</p>",
         "In 1687 x"),
        ("<p>Intro.</p><link href=a\"> Newton's 6\" telescope x > y.<p>Tail.</p>",
         "telescope x"),
    ):
        out = rewrite_article(doc)
        assert keep in out, (keep, out)
        assert "Intro." in out and "Tail." in out, out


def test_a_void_element_never_opens_a_subtree():
    """link/meta/base/input/area/source/track/embed are void — they are never
    closed. They sit in DROP_WITH_CONTENT but were missing from VOID_TAGS, so
    one that was not written self-closing raised the sanitizer's drop depth with
    nothing to lower it. The unclosed-drop-tag repair then deleted every inline
    run between that tag and the next block element: a whole sentence of the
    article replaced by a space.
    """
    from primer.render import DROP_WITH_CONTENT, VOID_TAGS, sanitize

    doc = ('<p>one</p><link rel="s" href="/x.css">This sentence sits between '
           "the link and the next block. <em>Real prose.</em><p>two</p>")
    out = sanitize(doc)
    assert "This sentence sits between" in out
    assert "<em>Real prose.</em>" in out
    assert "one" in out and "two" in out

    for tag in ("link", "meta", "base", "input", "source", "track", "area"):
        got = sanitize("<p>one</p><%s><p>two</p>" % tag)
        assert "one" in got and "two" in got, (tag, got)
        assert "<%s" % tag not in got, (tag, got)

    # The invariant, so this cannot come back by someone adding a void element
    # to DROP_WITH_CONTENT alone: every void element that is droppable must also
    # be known to be void. (source/track are deliberately not droppable — they
    # only ever occur inside audio/video, which are.)
    html_void = {"area", "base", "br", "col", "embed", "hr", "img", "input",
                 "link", "meta", "source", "track", "wbr"}
    missing = sorted((DROP_WITH_CONTENT & html_void) - VOID_TAGS)
    assert not missing, "droppable void elements not marked void: {}".format(missing)

    # And on <img>, which is read out of raw source and so is exposed to the
    # same truncation — an alt of "a > b" lost its text and spilled the rest of
    # the tag into the page. Nothing in the sample corpus happens to contain
    # one, so only a written test keeps this fixed.
    img = rewrite_article(
        '<p>before</p><img src="https://upload.wikimedia.org/a.png" alt="a > b" '
        'title="t"><p>after</p>')
    assert 'alt="a &gt; b"' in img
    assert "before" in img and "after" in img
    assert 'title="t"&gt;' not in img, "tag remainder leaked as text"

    # A tag whose quote never closes must not swallow the rest of the article.
    runaway = rewrite_article(
        '<p>before</p><img src="https://upload.wikimedia.org/a.png" alt="oops'
        "<p>after</p>")
    assert "before" in runaway and "after" in runaway


def test_the_two_night_palettes_cannot_drift_apart():
    """The stylesheet declares the night palette twice — once for the media
    query, once for the explicit toggle — and both must set the same properties
    or the book looks different depending on how night arrived. They have
    drifted before, silently, on --gold and --gold-bright: a variable added to
    one block and not the other produces a bug that is invisible in whichever
    theme you happen to be testing.

    Both blocks read from the --dk-* definitions in :root, so this also checks
    that every night value has a single source rather than a literal.
    """
    import re

    css = _web("styles.css")
    media = re.search(
        r'@media \(prefers-color-scheme: dark\) \{\s*'
        r':root:not\(\[data-theme="light"\]\) \{(.*?)\n  \}\n\}', css, re.S)
    toggle = re.search(r':root\[data-theme="dark"\] \{(.*?)\n\}', css, re.S)
    assert media and toggle, "both night-palette blocks must exist"

    names = lambda block: set(re.findall(r"(--[a-z0-9-]+)\s*:", block))
    in_media, in_toggle = names(media.group(1)), names(toggle.group(1))
    assert in_media == in_toggle, "night palettes drifted: {}".format(
        sorted(in_media ^ in_toggle))

    root = re.search(r"^:root \{(.*?)\n\}", css, re.S | re.M).group(1)
    sources = names(root)
    missing = sorted(v for v in in_media if "--dk-" + v[2:] not in sources)
    assert not missing, "night values with no --dk-* source: {}".format(missing)


NAVBOX = (
    '<div class="navbox"><table class="navbox-inner"><tbody>'
    '<tr><th class="navbox-title" colspan="2">'
    '<div class="navbar plainlinks hlist"><ul><li><a href="/wiki/Template:X">'
    "<abbr>v</abbr></a></li><li><a href=\"/wiki/Template_talk:X\">"
    "<abbr>t</abbr></a></li></ul></div>Sir Isaac Newton</th></tr>"
    '<tr><th class="navbox-group">Publications</th>'
    '<td class="navbox-list"><ul><li><a href="/wiki/Opticks">Opticks</a></li></ul></td>'
    "</tr></tbody></table></div>"
)


def test_a_navigation_box_is_folded_but_not_lost():
    """A navbox is the encyclopedia's footer of links to every related article.
    They arrived open and stacked: twelve of them and roughly 15 000px of link
    soup at the foot of Isaac Newton, against 70 000px of article — the reader
    reaches the end of the prose and hits a wall.

    Folded into a disclosure, the tail is ~760px and every link is still in the
    document, still reachable by keyboard and screen reader. Closed, not gone —
    which is the whole difference between this and hiding the content.
    """
    from primer.render import rewrite_article

    out = rewrite_article(NAVBOX)
    assert out.count('<details class="primer-navbox">') == 1
    assert out.count("</details>") == 1
    # The summary carries the box's own title, not the v/t/e template bar that
    # opens the title cell — "vtSir Isaac Newton" would be the giveaway.
    assert "<summary>Sir Isaac Newton</summary>" in out
    # Nothing is dropped: the links are inside the fold, not removed from it.
    assert "Opticks" in out and "Publications" in out
    # No `open` attribute — the reader opens it, the book does not.
    assert "<details open" not in out

    # A box that never closes must not swallow the rest of the article.
    truncated = rewrite_article(NAVBOX.replace("</table></div>", "</table>") + "<p>after</p>")
    assert "after" in truncated

    # Nested boxes travel inside their parent rather than being folded twice.
    nested = rewrite_article(
        '<div class="navbox"><p>outer</p>' + NAVBOX + "</div>")
    assert nested.count("<details") == 1, "one fold per outermost box"
    assert "outer" in nested and "Opticks" in nested

    # Classes that merely start with "navbox" are parts of a box, not boxes.
    for part in ("navbox-styles", "navbox-inner", "navbox-list"):
        assert "<details" not in rewrite_article(
            '<div class="%s">x</div>' % part), part


def test_an_article_subject_sidebar_is_a_named_toggle_not_an_open_wall():
    """Wikipedia promises collapsed groups with site JS Primer does not run.

    Genetics therefore arrived as a permanently expanded table, including
    dozens of topic links and tiny maintenance icons.  The native disclosure
    keeps every link but gives the whole guide one accurate name and a toggle.
    """
    from primer.render import rewrite_article

    genetics = (
        '<table class="sidebar sidebar-collapse" role="navigation">'
        '<tbody><tr><td class="sidebar-pretitle">Part of a series on</td></tr>'
        '<tr><th class="sidebar-title-with-pretitle">'
        '<a href="./Genetics">Genetics</a></th></tr>'
        '<tr><td class="sidebar-content"><div class="sidebar-list mw-collapsed">'
        '<a href="./DNA">DNA</a></div></td></tr></tbody></table>'
    )
    out = rewrite_article(genetics)
    assert out.count('<details class="primer-article-guide">') == 1, out
    assert "<summary>Genetics topics</summary>" in out, out
    assert "DNA" in out and "primer-wikilink" in out
    assert "<details open" not in out

    # The marker is renderer-owned: an article cannot fold arbitrary claims.
    forged = rewrite_article(
        '<div class="primer-article-guide">not a real guide</div>')
    assert "primer-article-guide" not in forged
    assert "not a real guide" in forged


def test_showing_an_answer_cannot_be_done_twice():
    """Regression: "Show answer" stayed live, so three clicks appended three
    grading groups with identical labels and twelve live buttons."""
    js = _web("app.js")
    # Asserted on the disabling, not on the whole call: revealBack now also
    # carries what the reader wrote before turning the card (benchmark 12), and
    # pinning the exact argument list made this a test of the signature rather
    # than of the regression it exists for.
    i = js.index("showBtn.disabled = true;")
    assert "revealBack(c, answerRegion" in js[i:i + 120]


def test_the_end_of_the_deck_keeps_focus():
    """Regression: the one review re-render that bypassed renderRoute's focus
    handling, so finishing a deck dropped focus to <body>."""
    js = _web("app.js")
    i = js.index("renderReview(page);")
    assert "h.focus()" in js[i:i + 420], "end-of-deck must place focus"


def test_two_sittings_are_not_the_same_paper(open_assessment_gate):
    """The point of a bank is that it is bigger than the paper drawn from it.

    Round 10 set the depth target to 6 while a quiz served 5-6, so two spaced
    passes shared 85% of their items and 102 of 254 nodes served a literally
    identical set — the second pass measured recall of the answers, which is
    the exact defect the deepening was meant to cure.
    """
    import statistics
    from fastapi.testclient import TestClient
    import primer.server as srv

    client = TestClient(srv.app)
    client.post("/api/profile", json={
        "name": "Overlap", "age": 12, "hours_per_week": 15, "breadth": "balanced",
        "domains": [d["id"] for d in srv.curr.domains]})

    overlaps, identical, n = [], 0, 0
    for nid, node in srv.curr.nodes.items():
        if node["stage"] < 2:
            continue
        sittings = []
        for _ in range(2):
            # The width the app actually requests — measuring at a narrower one
            # reports a number on a paper the reader never sits.
            paper = client.get("/api/quiz/{}?n=5".format(nid)).json()
            served = srv._SERVED[paper["token"]]["questions"]
            sittings.append({q.get("prompt", "") for q in served})
        a, b = sittings
        if not (a and b):
            continue
        overlaps.append(len(a & b) / max(len(a), len(b)))
        identical += a == b
        n += 1

    assert n > 200
    assert statistics.mean(overlaps) < 0.65, \
        "two sittings share {:.0%} of their items".format(statistics.mean(overlaps))
    assert identical / n < 0.10, \
        "{:.0%} of nodes serve an identical paper twice".format(identical / n)


def test_an_authored_produced_item_is_never_displaced(open_assessment_gate):
    """Regression: a slot was reserved for an authored produced-response item at
    index n-1, and the generated reflection item then truncated the paper to
    n-1 — selecting the authored item and discarding it in the same breath. On
    one node, three authored numeric items never once reached a paper, and the
    test meant to catch it passed on the *generated* short item instead."""
    from fastapi.testclient import TestClient
    import primer.server as srv

    client = TestClient(srv.app)
    client.post("/api/profile", json={
        "name": "Produced", "age": 12, "hours_per_week": 15, "breadth": "balanced",
        "domains": [d["id"] for d in srv.curr.domains]})

    missing = []
    for nid, node in list(srv.curr.nodes.items())[:80]:
        if node["stage"] < 2:
            continue
        if not any(q.get("kind") in ("numeric", "short") for q in (node.get("quiz") or [])):
            continue
        paper = client.get("/api/quiz/{}?n=5".format(nid)).json()
        served = srv._SERVED[paper["token"]]["questions"]
        if not any(q.get("kind") in ("numeric", "short") and not q.get("ungraded")
                   for q in served):
            missing.append(nid)
    assert not missing, "authored produced item never served: {}".format(missing[:5])


def test_every_item_in_a_bank_can_actually_be_drawn(open_assessment_gate):
    """A bank item that never reaches a paper is not an item. Selection has to
    reach all of them over enough sittings, or the effective bank is smaller
    than it looks — which is how three numeric items sat unused."""
    import collections
    from fastapi.testclient import TestClient
    import primer.server as srv

    client = TestClient(srv.app)
    for nid in ("math.3.slope", "phys.4.quantum", "bio.4.molecular"):
        node = srv.curr.nodes[nid]
        seen = collections.Counter()
        for _ in range(40):
            paper = client.get("/api/quiz/{}?n=5".format(nid)).json()
            for q in srv._SERVED[paper["token"]]["questions"]:
                if not q.get("ungraded"):
                    seen[q.get("prompt", "")] += 1
        assert len(seen) >= len(node["quiz"]), \
            "{}: only {} of {} bank items ever served".format(nid, len(seen), len(node["quiz"]))


def test_every_short_item_can_be_passed_by_its_own_model_answer():
    """A produced-response item the canonical answer fails is unpassable.

    28 of 189 were: authored keys like "subtract 5 first" and "x = 5" are
    multi-word, and the scorer matched single whole words only, so they could
    never be met. Others demanded a term the model answer never used —
    "Vitali", "Hahn-Banach" — penalising a reader who reasoned correctly for
    not knowing a label the question never asked for.
    """
    failures = []
    for name, d in _banks():
        for n in d["nodes"]:
            for q in n.get("quiz") or []:
                if q.get("kind") != "short":
                    continue
                score = quiz.score_short_answer(str(q.get("answer", "")),
                                                q.get("keywords") or [])
                if score < 0.6:
                    failures.append((n["id"], round(score, 2), q.get("keywords")))
    assert not failures, "model answer fails its own item: {}".format(failures[:5])


def test_the_short_answer_scorer_still_refuses_a_run_on():
    """The multi-word fix must not re-open the substring cheat that started all
    this: "photosynthesisrespirationnutrients" once scored a perfect 1.0."""
    assert quiz.score_short_answer(
        "photosynthesisrespirationnutrientsabsorb", ["photosynthesis", "respiration"]) == 0.0
    assert quiz.score_short_answer("no idea at all", ["compactness", "constant"]) == 0.0
    # ...while ordinary word-building still counts.
    assert quiz.score_short_answer(
        "it grows finitely and balances", ["finite", "balance"]) == 1.0


def test_the_results_screen_keeps_focus():
    """Regression: `finish()` emptied the modal while "See results" had focus,
    leaving it on <body> inside a dialog still claiming `aria-modal` — so the
    trap could not even wrap, and the results were never announced. This was
    already fixed for the end of the review deck and left in the commonest path
    in the app. Placement had it too."""
    js = _web("app.js")
    assert js.count("class: 'result-heading'") >= 2, "quiz and placement both need one"
    i = js.index("async function finish(modal, close)")
    # Scoped to the function, not to a byte count. This read `js[i:i + 900]`,
    # which asks "is the focus call within 900 characters of the declaration" —
    # a question about comment length, not about behaviour. Adding five lines of
    # comment inside `finish` pushed the call to character 901 and failed a test
    # whose subject had not changed. The rule being kept is that focus moves to
    # the results heading somewhere inside `finish`, so the window is `finish`.
    rest = js[i:]
    end = rest.index("\n  function ", 1) if "\n  function " in rest[1:] else len(rest)
    assert "splashHead.focus()" in rest[:end], (
        "finish() must move focus to the results heading")


def test_a_wide_table_scrolls_without_widening_the_page():
    """Regression: wrapping tables in a scroller restored the accessibility tree
    but broke Reflow (SC 1.4.10) — `#article` is a grid item, and a grid item's
    default `min-width: auto` let the widest table's min-content width push the
    whole document past a 400px viewport."""
    css = _web("styles.css")
    assert "#article, #reader-layout > * { min-width: 0; }" in css


def test_wrapping_tables_survives_broken_markup():
    """A stray `</table>` drove the depth counter negative and suppressed the
    wrapper on every table after it; an unclosed `<table>` left a `<div>` open
    and swallowed the rest of the article."""
    from primer.render import rewrite_article
    for html in ("</table><table><tr><td>x</td></tr></table><table><tr><td>y</td></tr></table>",
                 "<table><tr><td>x</td></tr><p>tail</p>",
                 "<table><tr><td><table><tr><td>i</td></tr></table></td></tr></table>"):
        out = rewrite_article(html)
        assert out.count("<div") == out.count("</div>"), out
    stray = rewrite_article(
        "</table><table><tr><td>x</td></tr></table><table><tr><td>y</td></tr></table>")
    assert stray.count("table-scroll") == 2, "a stray close must not disable later wrappers"


def test_the_internal_reader_route_is_not_a_dead_end():
    """`#/reader` — the internal view name, and a plausible hand-typed hash —
    rendered a completely blank page with no message and focus on an empty
    <main>."""
    js = _web("app.js")
    assert "if (view === 'reader' && !parts[1]) return { view: 'library-search', arg: null };" in js


def test_the_readers_place_is_read_before_the_page_can_collapse():
    """Regression: the scroll memory restored a layout artefact, never a place.

    renderRoute empties #page, so by the time renderReader is entered the
    document is a toolbar, a skeleton and the tutor panel. The browser clamps
    the scroll offset to whatever that short page allows and fires a scroll
    event for it — and that event lands *after* `S.readerTitle = title` has
    claimed the slot for the article now arriving, so it writes the clamp into
    that article's memory. Reading the value after the fetch read the clamp
    back: measured in the browser, a never-visited article opened 533px down
    its own page, and returning to one genuinely remembered at 1212 landed at
    533 and overwrote the 1212 with it.

    The whole feature therefore has one ordering requirement: the remembered
    offset is read in the same synchronous breath that claims the title,
    before the first await hands the task back to the browser.
    """
    js = _web("app.js")
    body = js[js.index("async function renderReader("):]
    body = body[:body.index("\n}\n")]
    claim = body.index("S.readerTitle = title;")
    read = body.index("readerScroll.get(title)")
    first_await = body.index("const a = await articlePromise;")
    assert claim < read < first_await, \
        "the remembered offset must be read before renderReader's first await"


def test_practice_errors_still_become_cards(store):
    """Regression: every practice generator stamps `ephemeral: True` on every
    item, and `cards_from_missed` trusted that flag — so the 41 nodes assessed
    through practice could never mint a single review card, however badly the
    reader did. "5 + 3 = ?" is a one-off instance; "Which shape has 8 sides?" is
    a fact that happens to come from a generator."""
    durable = [{"kind": "choice", "prompt": "Which shape has 8 sides?",
                "answer": "octagon", "choices": ["octagon", "hexagon"], "ephemeral": True},
               {"kind": "numeric", "prompt": "What is 5 + 3?",
                "answer": "8", "ephemeral": True}]
    cards = quiz.cards_from_missed(durable, ["hexagon", "9"], "math.0.shapes", "")
    fronts = [c["front"] for c in cards]
    assert "Which shape has 8 sides?" in fronts, "a durable fact must come back"
    assert "What is 5 + 3?" not in fronts, "a one-off instance must not"


def test_a_new_card_is_not_instantly_cashable(store):
    """Regression: cards were due the moment they were created, so a decayed
    node could be restored to full strength in zero elapsed time by minting a
    few cards and grading them. Writing a card and answering it in the same
    breath is not a memory test."""
    store.add_cards([{"front": "brand new", "back": "b", "node_id": "n"}])
    assert store.due_cards() == [], "a card must not be due the instant it exists"


def test_only_spaced_repetition_builds_durability(store):
    """Regression: `reinforcements` counted every successful review with no
    spacing requirement, and the half-life doubled each time — so three weeks of
    daily drilling pinned a node at the ceiling and it still read as proven four
    years later. Fixing "everything evaporates" by making nothing evaporate is
    not a fix."""
    store.record_attempt("n", 1.0)

    def reinforcements():
        with store._conn() as c:
            return c.execute(
                "SELECT reinforcements FROM mastery WHERE node_id='n'").fetchone()[0]

    start = reinforcements()
    store.add_cards([{"front": "c%d" % i, "back": "b", "node_id": "n"} for i in range(15)])
    all_due(store)
    for card in store.due_cards(limit=15):
        store.review_card(card["id"], 5)
    assert reinforcements() <= start + 1, "massed repetition must not compound"

    # ...and the ceiling still lets everything fade eventually. Read the law
    # from `_half_life` rather than restating it: this test used to carry an
    # algebraic copy of the growth formula, which kept passing unchanged when
    # the formula it was mirroring was replaced.
    import primer.learner as lm
    for r in (1, 5, 20, 60):
        four_years = 0.5 ** ((4 * 365 * 86400) / lm._half_life(r))
        assert four_years < 0.35, "r={} still proven after four years".format(r)


def test_a_self_written_card_cannot_un_master_a_node(store):
    """A card the reader wrote cannot *overturn* proven work: eight self-graded
    failures still leave the node mastered, and only a book card can revoke it.

    Superseded assertion: this used to require the strength be untouched too,
    on the grounds that non-evidence must not move anything. But failure is
    evidence in a way success is not — a card the reader wrote is the easiest
    possible test, so blanking on it is a real signal of forgetting — so the
    strength is now allowed to fall. What must not happen is a self-written
    card tearing down mastery on its own."""
    store.record_attempt("n", 1.0)
    with store._conn() as c:
        c.execute("UPDATE mastery SET mastered_at=?, strength=1.0, passes=2 "
                  "WHERE node_id='n'", (time.time(),))
    store.add_cards([{"front": "mine", "back": "b", "node_id": "n", "origin": "reader"}])
    all_due(store)
    cid = [c for c in store.due_cards() if c["front"] == "mine"][0]["id"]
    for _ in range(8):
        make_due(store, cid)
        store.review_card(cid, 0)
    with store._conn() as c:
        row = c.execute("SELECT strength, mastered_at FROM mastery WHERE node_id='n'").fetchone()
    assert row[1] is not None, "a reader-written card must not revoke mastery"
    assert row[0] < 1.0, "repeated failure on it is still evidence of forgetting"


def test_the_due_queue_interleaves_a_lopsided_backlog(store):
    """Regression: `due_cards` prefetched `limit * 3` rows by due date and
    round-robined *within that window*, so it interleaved only when the deck was
    already balanced. Sixty cards due on one node and five on another produced a
    queue that was 100% the first node — and a backlog after a break is exactly
    when interleaving matters most."""
    store.add_cards([{"front": "a%d" % i, "back": "b", "node_id": "node.A"} for i in range(60)])
    store.add_cards([{"front": "b%d" % i, "back": "b", "node_id": "node.B"} for i in range(5)])
    all_due(store)
    seq = [c["node_id"] for c in store.due_cards(limit=20)]
    assert "node.B" in seq, "the smaller node never appeared at all"
    assert seq.count("node.B") >= 4, seq.count("node.B")


def test_an_upgrade_does_not_re_lock_what_a_reader_earned():
    """Regression: a migration that adds a column is only half the job when live
    code reads it. `strength` was added with `DEFAULT 0` and never backfilled,
    so once `proven_set` and `gate_map` became decay-aware, every node a reader
    had genuinely proven before the upgrade read as forgotten the moment they
    opened the book."""
    import sqlite3
    import tempfile
    import primer.learner as lm

    db = os.path.join(tempfile.mkdtemp(), "old.db")
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE profile(id INTEGER PRIMARY KEY, name TEXT, age REAL,
            hours_per_week REAL, breadth TEXT, stage INTEGER, domains TEXT,
            settings TEXT, created_at REAL);
        CREATE TABLE mastery(node_id TEXT PRIMARY KEY, level REAL, attempts INTEGER,
            mastered_at REAL);
        CREATE TABLE events(id INTEGER PRIMARY KEY, kind TEXT, payload TEXT, at REAL);
        CREATE TABLE srs_cards(id INTEGER PRIMARY KEY, front TEXT, back TEXT,
            node_id TEXT, article TEXT, ef REAL DEFAULT 2.5, interval REAL DEFAULT 0,
            reps INTEGER DEFAULT 0, due REAL, created_at REAL);
        CREATE TABLE reading_log(id INTEGER PRIMARY KEY, title TEXT, at REAL);
        CREATE TABLE placement(domain TEXT PRIMARY KEY, stage INTEGER, asked TEXT,
            done INTEGER);
    """)
    recent = time.time() - 5 * 86400
    con.execute("INSERT INTO profile VALUES(1,'Nell',9,6,'balanced',2,'[]','{}',?)", (recent,))
    for nid in ("a.1.x", "a.1.y", "a.2.z"):
        con.execute("INSERT INTO mastery(node_id, level, attempts, mastered_at) "
                    "VALUES(?,1.0,3,?)", (nid, recent))
    con.commit()
    con.close()

    store = lm.LearnerStore(db)                     # migrations + backfill
    assert store.get_profile()["name"] == "Nell"
    assert len(store.proven_set()) == 3, "an active reader's record must survive"
    assert sum(1 for v in store.gate_map().values() if v >= 1.0) == 3
    assert len(store.ever_proven_set()) == 3


def test_a_paper_is_a_sitting_not_a_standing_offer():
    """Papers were evicted only by the size cap, so a token minted months ago
    stayed redeemable as long as the book had been quiet."""
    import primer.server as srv
    token = srv._remember([{"id": 0, "prompt": "p", "answer": "a"}], "quiz", "n.0.x", 1)
    assert srv._recall(token, "quiz", "n.0.x", 1) is not None

    token = srv._remember([{"id": 0, "prompt": "p", "answer": "a"}], "quiz", "n.0.x", 1)
    srv._SERVED[token]["at"] = time.time() - srv._SERVED_TTL - 1
    assert srv._recall(token, "quiz", "n.0.x", 1) is None, "a stale paper must not be redeemable"


def test_focus_is_held_across_the_marking_round_trip():
    """Regression: disabling the control that has focus drops it to <body>, and
    marking an answer is a whole network hop. On any real connection the dialog
    spent every question with focus outside itself — and the trap cannot help,
    because with activeElement on body it matches neither first nor last, so Tab
    walks straight out."""
    js = _web("app.js")
    assert js.count("holdFocus(card, 'Checking…')") == 5, \
        "all five submit paths must hold focus before awaiting"
    i = js.index("function holdFocus")
    assert "region.focus()" in js[i:i + 900]


def test_a_bare_url_cannot_widen_the_page():
    """Regression: a citation URL is one unbreakable 378px word, and there was
    no `overflow-wrap` anywhere in the stylesheet — so seven of twelve sampled
    articles still pushed the document sideways at the 320px reflow threshold,
    long after the tables themselves had been fixed."""
    css = _web("styles.css")
    matching_rules = [line for line in css.splitlines()
                      if "overflow-wrap: anywhere" in line]
    assert any("#article" in rule for rule in matching_rules), matching_rules


def test_the_graduate_stage_is_its_own_mode():
    """Regression: every `data-stage="5"` rule was paired with `="4"` except one
    pointing at a `.kbd-hint` class no template ever emitted — five modes
    wearing six labels."""
    css = _web("styles.css")
    solo = [l for l in css.splitlines()
            if 'body[data-stage="5"]' in l and 'data-stage="4"' not in l]
    assert len(solo) >= 6, "stage 5 needs rules of its own: {}".format(len(solo))
    assert not any("kbd-hint" in l for l in solo), "and not one pointing at nothing"


def test_no_two_items_in_a_bank_share_an_answer_and_a_shape():
    """A bank of ten holding a near-duplicate pair is a bank of nine, and if the
    twins share an answer the second is free to anyone who met the first. Four
    such pairs survived the sweep: two loops both landing on 8, two DFAs both
    needing 3 states, two schedulers both averaging 2.5 ms, two oscillators both
    completing 4 cycles."""
    import re

    def words(q):
        text = " ".join([str(q.get("prompt", "")), str(q.get("answer", ""))]
                        + sorted(str(o) for o in (q.get("choices") or [])))
        return {w.lower() for w in re.findall(r"[^\W\d_]{4,}", text)}

    twins = []
    for name, d in _banks():
        for n in d["nodes"]:
            # This used to skip stage 0-1, so it could not see that "Gigantic
            # means…" and "Enormous means the same as…" both key *huge* in one
            # bank. A young reader meets both in a five-item paper.
            qs = n.get("quiz") or []
            for i in range(len(qs)):
                for j in range(i + 1, len(qs)):
                    a, b = words(qs[i]), words(qs[j])
                    threshold = 6 if n.get("stage", 0) >= 2 else 3
                    if len(a) < threshold or len(b) < threshold:
                        continue
                    same_answer = (str(qs[i].get("answer", "")).strip().lower()
                                   == str(qs[j].get("answer", "")).strip().lower())
                    overlap = len(a & b) / len(a | b)
                    if same_answer and overlap >= 0.55:
                        twins.append((n["id"], i, j, round(overlap, 2)))
    assert not twins, "same answer, same shape: {}".format(twins[:5])


def test_an_article_cannot_mint_the_renderers_own_markers():
    """The renderer gives behaviour to three markers: `table-scroll`, which the
    stylesheet turns into a scroll region, `primer-navbox`, which folds a
    subtree behind a disclosure, and `data-primer-title`, which the client
    navigates on. All were reachable from article markup — `class` is
    allowlisted, and an anchor with no `href` never reached the link rewriter at
    all, so it could simply declare its own destination.

    All are applied downstream of the sanitizer now, so nothing upstream can
    forge one. `primer-navbox` matters most of the three: a forged one would let
    an article fold arbitrary content — its own retraction, say — out of sight
    behind a summary of its own choosing.
    """
    from primer.render import rewrite_article

    assert "table-scroll" not in rewrite_article('<div class="table-scroll">x</div>')
    forged_fold = rewrite_article('<div class="primer-navbox">hidden claim</div>')
    assert "primer-navbox" not in forged_fold
    assert "<details" not in forged_fold
    assert "hidden claim" in forged_fold

    # primer-wikilink is the class that makes a link look like part of this
    # book. Forged onto an external anchor it cannot navigate anywhere — the
    # client reads data-primer-title, which is unforgeable — but it would still
    # give the book's own in-book styling to a link that middle-clicks out.
    forged_link = rewrite_article(
        '<a class="primer-wikilink" href="https://evil.example.com/x">looks internal</a>')
    assert "primer-wikilink" not in forged_link
    assert "looks internal" in forged_link
    assert "primer-wikilink" not in rewrite_article(
        '<span class="primer-wikilink">not even a link</span>')

    # An external link states target/rel once, in the renderer's own words: an
    # article carrying its own produced the attribute twice, and browsers take
    # the first one.
    dup = rewrite_article('<a href="https://example.com" target="_blank" rel="noopener">x</a>')
    assert dup.count("target=") == 0 and dup.count("rel=") == 1, dup
    # The marker on a door out of the book is the book's to state, like every
    # other reserved class: an article must not be able to dress one of its own
    # links as one, nor dress a door as ordinary prose.
    forged_outside = rewrite_article(
        '<a class="primer-outside" data-primer-outside="evil.test" '
        'href="https://real.test/x">x</a>')
    # The substring occurs twice legitimately — the attribute name and the class
    # — so count the class, and check the forged HOST was replaced by the real
    # destination rather than carried through.
    assert forged_outside.count('class="primer-outside"') == 1, forged_outside
    assert 'data-primer-outside="real.test"' in forged_outside, forged_outside
    assert "evil.test" not in forged_outside, forged_outside


def test_no_image_reaches_the_reader_on_an_upstream_url():
    """Proxying every `src` through /api/image is what makes the book work
    offline and what stops the reader's browser announcing itself to Wikimedia
    on every page view. fix_img does it, but fix_img finds tags with a regex on
    raw markup, and a regex can be handed something it will not match — an
    <img> with a raw `<` in an attribute value slipped past whole, and sanitize
    is content to keep an https:// src. The guarantee is restated downstream of
    the parser so it does not depend on that match succeeding.
    """
    from primer.render import rewrite_article

    for hostile in ('<img src="https://upload.wikimedia.org/secret.png" alt="a < b">',
                    "<img src=\"https://upload.wikimedia.org/x.png\" title='a < b'>",
                    '<img alt="a < b" src="https://upload.wikimedia.org/z.png">',
                    # Protocol-relative is the form Wikipedia actually writes,
                    # and the backstop matched only ^https?:// at first.
                    '<img src="//upload.wikimedia.org/a.png" alt="a < b">',
                    '<img src="//upload.wikimedia.org/b.png" alt="a < b" width="220">'):
        out = rewrite_article(hostile)
        assert 'src="https://' not in out, out
        assert 'src="//' not in out, out
        assert "/api/image?url=https%3A%2F%2F" in out, out

    # Archive-relative sources are served from the ZIM and must not be proxied.
    assert 'src="/zim/rel/a.png"' in rewrite_article('<img src="/zim/rel/a.png">')
    for forged in ('<a data-primer-title="Evil">x</a>',
                   "<a data-primer-title='Evil'>x</a>",
                   '<a data-primer-title=Evil>x</a>',
                   '<a class="primer-wikilink" data-primer-title="Evil">x</a>',
                   '<span data-primer-title="Evil">x</span>'):
        assert "Evil" not in rewrite_article(forged), forged

    # ...while the renderer's own still work.
    real = rewrite_article('<a href="/wiki/Carbon">C</a>')
    assert 'data-primer-title="Carbon"' in real and "primer-wikilink" in real
    assert "table-scroll" in rewrite_article("<table><tr><td>x</td></tr></table>")
    # A legitimate class is untouched.
    assert 'class="infobox"' in rewrite_article('<div class="infobox">x</div>')


def test_a_stray_closing_div_cannot_break_out_of_the_scroll_region():
    """An article's own `</div>` — legal markup — closed the wrapper early and
    left the rest of the table outside it, with `</table></div>` dangling past
    the end."""
    from primer.render import rewrite_article
    for html in ('<table><tr><td>a</td></tr></div><tr><td>b</td></tr></table><p>after</p>',
                 '<table><tr><td><div>x</td></tr></table><p>after</p>',
                 '</div></div><table><tr><td>a</td></tr></table>',
                 '<div><p>hello',                       # left hanging
                 '<style>body{}<div><table><tr><td>x</td></tr></table>'):  # and malformed
        out = rewrite_article(html)
        assert out.count("<div") == out.count("</div>"), out


def test_the_renderer_survives_a_structural_fuzz():
    """Judge the parsed output, not its text: a fuzzer emitting the literal
    string "javascript:" as body text sees it escaped and echoed back, which a
    substring search calls a leak and a browser renders as five words."""
    import random
    import re as _re
    from html.parser import HTMLParser
    from primer.render import rewrite_article

    danger = _re.compile(r"^\s*(javascript|vbscript|data)\s*:", _re.I)

    class Probe(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.bad = []

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "iframe", "svg", "style", "object", "embed"):
                self.bad.append(tag)
            for k, v in attrs:
                k = (k or "").lower()
                if k.startswith("on"):
                    self.bad.append(k)
                if k in ("href", "src") and danger.match(v or ""):
                    self.bad.append(v)
                if k == "data-primer-title" and tag != "a":
                    self.bad.append("nav on <{}>".format(tag))

    tokens = ['<table>', '</table>', '<div>', '</div>', '<script>alert(1)</script>',
              'javascript:alert(1)', 'onerror=alert(1)', '<a href="javascript:alert(1)">',
              '<a href="/wiki/X">', '</a>', '<td>', '</td>', '<tr>', '</tr>',
              '<div class="table-scroll">', '<a data-primer-title="E">',
              '<img src=x onerror=alert(1)>', '<svg onload=alert(1)>', 'text', '<!--', '-->']
    rng = random.Random(7)
    for _ in range(1500):
        html = "".join(rng.choice(tokens) for _ in range(rng.randint(3, 12)))
        probe = Probe()
        probe.feed(rewrite_article(html))
        probe.close()
        assert not probe.bad, "{!r} -> {}".format(html[:70], probe.bad[:3])


def test_the_document_the_reader_gets_is_always_balanced():
    """An article closing a container it never opened ends the reading column
    and throws the rest of the page out of layout; one it never closes swallows
    the page into the article. Neither is a security hole and both wreck the
    book, and the repair branch used to return its second parse raw — so a
    malformed <style> beside an unclosed <div> still escaped.
    """
    import random
    from html.parser import HTMLParser
    from primer.render import rewrite_article

    class Depth(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.depth = 0
            self.lowest = 0

        def handle_starttag(self, tag, attrs):
            if tag == "div":
                self.depth += 1

        def handle_endtag(self, tag):
            if tag == "div":
                self.depth -= 1
                self.lowest = min(self.lowest, self.depth)

    tokens = ['<table>', '</table>', '<div>', '</div>', '<style>body{}', '<p>', '</p>',
              '<td>', '</td>', '<tr>', '</tr>', '<div class="table-scroll">', 'text',
              '<script>x</script>', '<!--', '-->', '<']
    rng = random.Random(11)
    for _ in range(1200):
        html = "".join(rng.choice(tokens) for _ in range(rng.randint(3, 12)))
        d = Depth()
        d.feed(rewrite_article(html))
        d.close()
        assert d.depth == 0, "left {} div(s) open: {!r}".format(d.depth, html[:60])
        assert d.lowest >= 0, "closed a div it never opened: {!r}".format(html[:60])


def test_a_review_card_is_something_to_recall_not_to_read(store):
    """Regression: cards appended the whole explanation to the answer, so the
    longest back ran to 369 characters — the exam question again rather than a
    single fact. And a constructed-response item's model answer is a paragraph
    by nature; what the reader needs back from one of those is the ideas it has
    to contain, not the essay.
    """
    long_explain = (
        "The mean chases extreme values while the median does not, so a mean above "
        "the median is the signature of a right tail. This matters whenever an "
        "average is quoted for a skewed quantity such as income or commute time, "
        "where the typical case and the arithmetic mean part company entirely.")
    cards = quiz.cards_from_missed(
        [{"kind": "numeric", "prompt": "Which is larger?", "answer": "the mean",
          "explain": long_explain}], ["the median"], "stats.1.x", "")
    assert len(cards[0]["back"]) <= 220, cards[0]["back"]
    assert cards[0]["back"].startswith("the mean"), "the answer still comes first"

    essay = quiz.cards_from_missed(
        [{"kind": "short", "prompt": "Explain why the mean exceeds the median here.",
          "answer": "A long paragraph of model prose that runs on and on and on, "
                    "well past anything anyone would want on the back of a card.",
          "keywords": ["skew", "tail", "mean", "median"]}], ["no idea"], "stats.1.x", "")
    assert essay and essay[0]["back"] == "Cover: skew, tail, mean, median"
    assert len(essay[0]["back"]) <= 220


def test_sibling_table_landmarks_can_be_told_apart():
    """Several regions all named "Table" are indistinguishable in a landmark
    rotor — one article carried eight of them."""
    import re
    from primer.render import rewrite_article
    out = rewrite_article("<table><tr><td>a</td></tr></table><p>x</p>"
                          "<table><tr><td>b</td></tr></table>")
    names = re.findall(r'aria-label="(Table[^"]*)"', out)
    assert names == ["Table 1", "Table 2"], names


def test_an_unknown_route_corrects_the_address_bar():
    """Falling back to Today while leaving the hash on a bogus route left no nav
    item marked `aria-current`, and a reload landed nowhere."""
    js = _web("app.js")
    assert "KNOWN_VIEWS" in js
    assert "if (corrected) { location.replace('#/' + view); return; }" in js


def test_mathematics_image_dashboard_is_a_complete_accessible_route():
    js = _web("app.js")
    css = _web("styles.css")

    assert "['math-images', 'gallery', 'Math Images']" in js
    assert "'math-images': renderMathImages" in js
    assert "/api/curriculum/mathematics/illustrations" in js
    assert "function renderMathImages(page)" in js
    assert "role: 'radiogroup'" in js and "aria-checked" in js
    assert "['ArrowDown', 'ArrowRight', 'ArrowUp', 'ArrowLeft', 'Home', 'End']" in js
    assert "role: 'status', 'aria-live': 'polite'" in js
    assert "loading: 'lazy'" in js and "srcset: item.srcset" in js
    assert "(max-width: 700px) calc(100vw - 48px)" in js
    assert "attachPictureHandlers(board)" in js
    assert "img.dataset.fullSrc || img.currentSrc" in js
    assert "math-image-card[hidden]" in css
    assert ".math-image-grid" in css and ".math-stage-filters" in css
    assert ".math-search-row input[type=search]" in css
    assert 'body[data-stage="0"] .math-stage-option' in css
    assert 'body[data-stage="4"] .math-image-card' in css
    assert "@media (max-width: 430px)" in css


def test_reader_keeps_exact_lesson_context_in_a_toggleable_navigator():
    js = _web("app.js")
    css = _web("styles.css")

    assert "id: 'reader-context-slot'" in js
    assert "function openLessonNavigator(data, articleTitle)" in js
    assert "function openIndependentReaderNavigator(articleTitle)" in js
    assert "Independent reading: ' + articleTitle" in js
    assert "showIndependentReaderContext(title)" in js
    assert "/navigation')" in js
    assert "readerContextStillCurrent(contextSeq, title, nodeId)" in js
    assert "'aria-haspopup': 'dialog'" in js
    assert "'aria-current': active ? 'page' : null" in js
    assert "'aria-current': active ? 'location' : null" in js
    assert "'Lessons in ' + domain.name" in js
    assert "current.section || current.stage_name" in js
    assert "Reading: ' + articleTitle" in js
    assert "Linked reading · still in " in js
    assert ".reader-context-toggle" in css
    assert ".lesson-nav-groups" in css
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in css
    assert "@media (max-width: 600px)" in css


def test_failed_article_images_become_text_states_not_broken_placeholders():
    js = _web("app.js")
    css = _web("styles.css")

    assert "im.addEventListener('error', failed, { once: true })" in js
    assert "im.complete && !im.naturalWidth" in js
    assert "'aria-label': 'Picture unavailable'" in js
    assert "': ' + altText" in js
    assert "wrapper.hidden = true" in js
    assert "img.closest('figure, .thumb, .thumbinner, .gallerybox')" in js
    assert "figure, .thumb, .thumbinner, .gallerybox, .infobox" not in js
    assert "const inversionSource = img.closest('.skin-invert, .skin-invert-image')" in js
    assert "inversionSource.classList.contains(marker)" in js
    assert ".picture-fallback" in css


def test_lesson_illustrations_have_a_full_resolution_keyboard_viewer():
    js = _web("app.js")
    css = _web("styles.css")

    assert "dataset: { fullSrc: largestSrcFromSet(item.srcset, item.src) }" in js
    assert "attachPictureHandlers(media)" in js
    assert "Read labels at full size" in js
    assert "Full-resolution image. Scroll horizontally and vertically" in js
    assert "lightbox-image-scroll is-zoomed" not in js  # state is toggled, not baked in
    assert ".lightbox-image-scroll.is-zoomed" in css
    assert "width: var(--zoom-width, 1600px)" in css


def test_radiology_diagrams_have_complete_html_text_equivalents(curr):
    """Clinical reasoning must not be trapped in tiny text inside a raster."""
    generated = {
        node_id: node for node_id, node in curr.nodes.items()
        if node_id.startswith('rad.') and node_id != 'rad.3.ct-image'
    }
    assert len(generated) == 83
    for node_id, node in generated.items():
        plate = next(item for item in node['lesson_media']
                     if item['kind'] == 'illustration')
        description = plate.get('long_description')
        assert set(description) == {'title', 'mode', 'items', 'takeaway'}, node_id
        assert description['title'] == node['title']
        assert description['mode'] in {'flow', 'compare', 'map', 'scale', 'physics'}
        assert description['takeaway'] == plate['caption']
        assert len(description['items']) == 3
        for item in description['items']:
            assert set(item) == {'heading', 'label', 'detail'}
            assert all(isinstance(item[key], str) and item[key].strip()
                       for key in item)

    js = _web('app.js')
    css = _web('styles.css')
    assert 'function lessonLongDescription(item)' in js
    assert "ordered ? 'ol' : 'ul'" in js
    assert "peers to compare, not steps in a sequence" in js
    assert "'Read this diagram as text'" in js
    assert "part.heading !== part.label" in js
    assert "image.setAttribute('aria-describedby', longDescription.id)" in js
    assert "window.matchMedia('(max-width: 720px)').matches" in js
    assert '.lesson-diagram-steps' in css
    assert '@media (max-width: 720px)' in css
    assert 'grid-template-columns: 1fr' in css


def test_review_card_decays_strength_before_adjusting_it(store):
    """Regression: `review_card` read the raw stored `strength` instead of
    decaying it to now, so a single blank review on a node that had faded to
    near-zero over two years subtracted 0.25 from the stale value of 1.0 —
    landing at 0.75, comfortably above the 0.35 gate, and read as proven."""
    store.record_attempt("n", 1.0)
    with store._conn() as c:
        c.execute("UPDATE mastery SET mastered_at=?, strength=1.0, passes=2, "
                  "last_seen=?, reinforcements=1 WHERE node_id='n'",
                  (time.time() - 2 * 365 * 86400,) * 2)
    assert "n" not in store.proven_set(), "the node must already read as faded"
    store.add_cards([{"front": "f", "back": "b", "node_id": "n"}])
    with store._conn() as c:
        c.execute("UPDATE srs_cards SET due=?", (0,))
    store.review_card(store.due_cards()[0]["id"], 0)
    assert "n" not in store.proven_set(), "a failed review must not raise a faded node"


def test_a_reader_cards_grade_never_revives_a_faded_node(store):
    """Regression: `last_seen` — the decay clock's zero point — was written
    unconditionally on every review, book or reader card, any grade. So
    `/api/review/add` followed by a single quality-0 grade on the resulting
    card restored a two-year-faded node's clock to right now.

    The invariant being defended is that a reader-written card cannot make a
    node read fresher, not that it never writes the clock at all: a failure
    now subtracts from the *decayed* strength, so the value written can never
    exceed what the reader actually retains and moving the clock with it
    cannot revive anything."""
    store.record_attempt("n", 1.0)
    old_seen = time.time() - 2 * 365 * 86400
    with store._conn() as c:
        c.execute("UPDATE mastery SET mastered_at=?, strength=1.0, passes=2, "
                  "last_seen=?, reinforcements=1 WHERE node_id='n'", (old_seen, old_seen))
    store.add_cards([{"front": "q", "back": "a", "node_id": "n", "origin": "reader"}])
    with store._conn() as c:
        c.execute("UPDATE srs_cards SET due=?", (0,))
    assert "n" not in store.proven_set(), "the node must already read as faded"
    store.review_card(store.due_cards()[0]["id"], 0)
    with store._conn() as c:
        strength = c.execute(
            "SELECT strength FROM mastery WHERE node_id='n'").fetchone()[0]
    assert strength < 0.35, "a reader-card grade must not restore a faded node"
    assert "n" not in store.proven_set()


def test_massed_attempts_on_one_node_do_not_compound_reinforcement(store):
    """Regression: `_apply_attempt`'s reinforcement increment had no spacing
    gate, so 31 quiz papers on one node in a single sitting bought 31
    reinforcements and pinned the half-life at its ceiling immediately."""
    with store._conn() as c:
        for _ in range(20):
            store._apply_attempt(c, 1, "n", 1.0, False, time.time())
    with store._conn() as c:
        r = c.execute("SELECT reinforcements FROM mastery WHERE node_id='n'").fetchone()[0]
    assert r <= 2, "20 same-instant passing attempts bought {} reinforcements".format(r)


def test_a_card_reviewed_exactly_on_schedule_never_reads_as_faded(store):
    """The end-to-end claim: a reader who reviews a card precisely when it
    comes due, for as long as SM-2 keeps scheduling it, must never see their
    node read as faded in between. Two independent bugs broke this — SM-2's
    interval is unbounded while strength decay is capped, and the small
    additive `+0.15` recovery converged to a fixed point below the gate once
    the interval outgrew what it could repay in one step.
    """
    store.record_attempt("n", 1.0)
    with store._conn() as c:
        c.execute("UPDATE mastery SET mastered_at=?, strength=1.0, passes=2, "
                  "last_seen=?, reinforcements=1 WHERE node_id='n'", (time.time(),) * 2)
    store.add_cards([{"front": "f", "back": "b", "node_id": "n"}])

    def age(seconds):
        with store._conn() as c:
            c.execute("UPDATE mastery SET last_seen=last_seen-?, "
                      "reinforced_at=reinforced_at-?", (seconds, seconds))
            c.execute("UPDATE srs_cards SET due=due-?", (seconds,))

    worst = 1.0
    for _ in range(50):
        with store._conn() as c:
            due = c.execute("SELECT due FROM srs_cards WHERE node_id='n'").fetchone()[0]
        age(max(0, due - time.time()))
        store.review_card(store.due_cards(limit=1)[0]["id"], 5)
        worst = min(worst, store.gate_map().get("n", 0))
    assert worst >= 1.0, "an on-schedule reader must never see a faded gate: {}".format(worst)

    # Genuine neglect must still fade — this is not "nothing ever decays" again.
    # By now reinforcements have hit the half-life ceiling (365 days), so the
    # gap has to exceed what even the slowest decay survives (~553 days).
    with store._conn() as c:
        c.execute("UPDATE mastery SET last_seen=last_seen-?", (900 * 86400,))
    assert store.gate_map().get("n", 1.0) < 1.0, "real neglect must still fade the gate"


def test_the_readers_headline_agrees_with_the_gates(store):
    """`proven_count_current` (the /api/today headline) and `gate_map`
    (what actually opens the next lesson) read `_strength_now` with different
    argument sets, so a well-drilled node could read proven to the gates and
    unproven to the reader in the same response."""
    store.record_attempt("n", 1.0)
    with store._conn() as c:
        c.execute("UPDATE mastery SET mastered_at=?, strength=1.0, passes=2, "
                  "last_seen=?, reinforcements=8 WHERE node_id='n'", (time.time(),) * 2)
    assert store.proven_count_current() == len(
        [k for k, v in store.gate_map().items() if v >= 1.0]
    ), "the headline count and the gates must agree"


def test_read_xp_is_capped_even_across_distinct_titles(store):
    """Regression: only the first-ever open of a title paid XP, which assumed a
    small library. The shelf holds hundreds of thousands of titles plus live
    Wikipedia with no floor, so every click of "Surprise me" was a *different*
    title and the guard never once engaged — 60 distinct opens paid 60 x 3 XP."""
    for i in range(60):
        store.log_reading("Distinct Article {}".format(i))
    with store._conn() as c:
        total = c.execute(
            "SELECT COALESCE(SUM(xp), 0) FROM events WHERE kind='read'").fetchone()[0]
    assert total <= store.READ_XP_DAILY_CAP, total
    # The event still logs unconditionally, so the day's reading quest still ticks.
    with store._conn() as c:
        rows = c.execute("SELECT COUNT(*) FROM events WHERE kind='read'").fetchone()[0]
    assert rows == 60, "every open must still be logged, only the XP is capped"


def test_local_day_is_immune_to_dst(store):
    """Regression: the day index was `epoch_of_local_midnight // 86400`, which
    assumes every day is exactly 86400 seconds. It is not, across a DST
    transition — identical daily behaviour read as streak 38 in a DST-free
    window and streak 2 across the US fall-back for a 00:30 learner."""
    import datetime
    import os
    import time as _time

    import primer.learner as lm
    old_tz = os.environ.get("TZ")
    os.environ["TZ"] = "America/New_York"
    _time.tzset()
    try:
        start = datetime.date(2024, 10, 30)      # spans the Nov 3 fall-back
        prev = None
        for i in range(8):
            d = start + datetime.timedelta(days=i)
            dt = datetime.datetime(d.year, d.month, d.day, 0, 30)
            ts = _time.mktime(dt.timetuple())
            idx = lm._local_day(ts)
            if prev is not None:
                assert idx - prev == 1, "{} -> {} is not a single day".format(prev, idx)
            prev = idx
    finally:
        if old_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old_tz
        _time.tzset()


def test_local_midnight_is_immune_to_dst():
    """Regression: `_local_midnight` had the identical flaw `_local_day` was
    already fixed for — subtracting wall-clock hour/min/sec (in seconds)
    from an epoch timestamp assumes every day is exactly 86400 seconds,
    which is false across a DST transition. `_local_day` was rewritten to
    build a datetime.date directly; `_local_midnight` was never fixed, and
    it is what the XP daily caps (READ_XP_DAILY_CAP, REVIEW_XP_DAILY_CAP)
    and the "already attempted this node today" guard both read from. On
    spring-forward it landed an hour before true midnight (counting an hour
    of yesterday's XP against today's cap); on fall-back it landed an hour
    after (silently dropping the first hour of today out of every "since
    midnight" sum, effectively raising that day's earning limit)."""
    import datetime
    import os
    import time as _time

    import primer.learner as lm
    old_tz = os.environ.get("TZ")
    os.environ["TZ"] = "America/New_York"
    _time.tzset()
    try:
        # Spring-forward 2026-03-08: naive subtraction landed an hour early,
        # on the wrong calendar date entirely.
        dt = datetime.datetime(2026, 3, 8, 10, 0, 0)
        ts = _time.mktime(dt.timetuple())
        mid = lm._local_midnight(ts)
        expected = _time.mktime(datetime.datetime(2026, 3, 8, 0, 0, 0).timetuple())
        assert mid == expected, "spring-forward midnight landed on {} not {}".format(
            _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime(mid)), dt.date())

        # Fall-back 2026-11-01: naive subtraction landed an hour late.
        dt2 = datetime.datetime(2026, 11, 1, 10, 0, 0)
        ts2 = _time.mktime(dt2.timetuple())
        mid2 = lm._local_midnight(ts2)
        expected2 = _time.mktime(datetime.datetime(2026, 11, 1, 0, 0, 0).timetuple())
        assert mid2 == expected2, "fall-back midnight landed on {} not {}".format(
            _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime(mid2)), dt2.date())
    finally:
        if old_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old_tz
        _time.tzset()


def test_pruning_never_silently_truncates_a_long_streak(store):
    """Regression: `prune()` deleted every zero-XP event older than the
    window, and `streak_days()` counts distinct days across *all* events —
    zero-XP included, since a day whose only activity was an early review or a
    reading-cap hit still counts. A streak longer than the prune window
    silently lost its oldest days."""
    import time as _time

    now = _time.time()
    with store._conn() as c:
        for i in range(450):                     # older than the 400-day window
            day_ts = now - (450 - i) * 86400 + 1800
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                      ("read", "{}", day_ts, 0))  # zero-XP, as an early-review day is
    before = store.streak_days()
    store.prune(keep_days=400)
    after = store.streak_days()
    assert after == before, "pruning changed the streak from {} to {}".format(before, after)


def test_best_streak_survives_a_broken_current_streak(store):
    """Regression: the backend has kept every day's history past the prune
    window since the truncation fix, but nothing computed or surfaced a
    reader's best-ever run — the moment today's streak broke, their longest
    stretch became invisible even though the data survived. best_streak_days
    must find the longest run anywhere in history, not just the tail
    connected to today, and must apply the same freeze-bridging budget a
    live streak gets rather than a stricter rule."""
    import time as _time

    import primer.learner as lm
    # Anchor to today's local midnight, not a fixed offset from `now` — a
    # `now - d*86400 + 1800` offset drifts across the local-day boundary
    # depending on what time of day the suite happens to run: at 23:31
    # local, "day 0" (`now + 1800`) lands 30 minutes into TOMORROW, silently
    # breaking the "3 consecutive days" the test fabricates.
    midnight = lm._local_midnight(_time.time())
    with store._conn() as c:
        # A 10-day run, long ago, with one single-day gap bridged by a freeze.
        old_days = list(range(60, 65)) + list(range(66, 71))  # skip day 65
        for d in old_days:
            ts = midnight - d * 86400 + 1800
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                      ("read", "{}", ts, 0))
        # A short, unbroken, more recent 3-day run.
        for d in (2, 1, 0):
            ts = midnight - d * 86400 + 1800
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                      ("read", "{}", ts, 0))

    assert store.best_streak_days() == 10, \
        "the old 10-day run (with one freeze-bridged gap) must be found, not just the current 3-day run"
    assert store.streak_days() == 3, "the CURRENT streak is still just the recent 3 days"


def test_order_items_never_mint_review_cards():
    """Regression: an order item's prompt is fixed boilerplate ("Put them in
    order") while the sequence being ordered is randomised fresh every time —
    the prompt alone cannot tell one occurrence's card front from the next's.
    Trusting the prompt heuristic (which does not recognise order-style text as
    ephemeral) meant a single front silently mapped to a different back on 30
    nodes."""
    order_q = {"kind": "order", "prompt": "Put them in order", "items": ["a", "b", "c"],
               "answer": "a b c", "ephemeral": True}
    cards = quiz.cards_from_missed([order_q], ["b a c"], "n.0.x", "")
    assert cards == [], "an order item must never produce a card"

    # A durable practice item — same generated-content situation, different
    # kind — must still produce one.
    durable_q = {"kind": "choice", "prompt": "Which shape has 8 sides?",
                "answer": "octagon", "choices": ["octagon", "hexagon"], "ephemeral": True}
    cards2 = quiz.cards_from_missed([durable_q], ["hexagon"], "n.0.x", "")
    assert len(cards2) == 1, "a durable practice item must still mint a card"


def test_cards_from_text_never_blanks_a_self_answerable_word():
    """Regression: cards_from_text built its cloze blanks without the guards
    cloze_from_text already applies to the same kind of sentence — a key that
    still appeared elsewhere in the stem (whole or as a shared word-stem), or a
    blank opening the sentence with no lead-in, made the card answerable
    without recalling anything."""
    title = "Osmosis"
    text = ("Osmosis moves water. Diffusion diffusion is the spread of "
            "particles from high concentration to low concentration areas.")
    cards = quiz.cards_from_text(title, text, "n.0.x")
    for c in cards[1:]:
        front, back = c["front"], c["back"]
        assert not front.lstrip().startswith("______"), \
            "a blank at the start of the stem gives no lead-in context"
        remaining = front.replace("______", "")
        assert back.lower() not in remaining.lower(), \
            "the key must not still appear in what's left of the stem"


def test_node_minutes_are_calibrated_per_node_not_flat_by_stage(curr):
    """Regression: every node used to get the identical stage-flat default
    minutes estimate regardless of authored depth ("Counting to 10" priced
    the same as "Gödel's incompleteness theorems"). Minutes now scale with
    each node's own content density against its stage's average."""
    by_stage = {}
    for n in curr.nodes.values():
        by_stage.setdefault(n["stage"], set()).add(n["minutes"])
    for stage, vals in by_stage.items():
        if stage == 0:
            continue  # stage 0 content is deliberately uniform in depth
        assert len(vals) > 1, \
            "stage {} nodes all got the identical flat minutes estimate".format(stage)


def test_reinforcement_gap_scales_with_reader_age(store):
    """Regression: REINFORCE_MIN_GAP was a single one-day constant for every
    reader. Distributed-practice research finds young children's natural
    spacing cycle is hours, not days; a flat day-wide gate under-counts
    genuine spaced repetition for a 5-year-old the way it would not for a
    teenager. The gap now scales down for younger readers while still
    blocking same-sitting massed reinforcement."""
    store.save_profile("Young", 5, 6, "balanced", 0, ["math"])
    with store._conn() as c:
        store._apply_attempt(c, 1, "n", 1.0, False, time.time())
    with store._conn() as c:
        before = c.execute("SELECT reinforcements FROM mastery WHERE node_id='n'").fetchone()[0]
        c.execute("UPDATE mastery SET reinforced_at = reinforced_at - 14400 "
                  "WHERE node_id='n'")  # 4 hours ago: past a 5-year-old's 3h gap
        store._apply_attempt(c, 1, "n", 1.0, False, time.time())
        after_spaced = c.execute(
            "SELECT reinforcements FROM mastery WHERE node_id='n'").fetchone()[0]
    assert after_spaced == before + 1, \
        "a 4-hour gap should count as spaced for a 5-year-old (3h minimum)"

    with store._conn() as c:
        store._apply_attempt(c, 1, "n", 1.0, False, time.time())
        after_massed = c.execute(
            "SELECT reinforcements FROM mastery WHERE node_id='n'").fetchone()[0]
    assert after_massed == after_spaced, \
        "same-instant attempts still must not compound, regardless of age"


def test_auto_cloze_defect_rate_stays_under_5_percent():
    """Regression: #2's audit named "<5% defective auto-items" as an
    unverified requirement. tools/audit_cloze_defects.py measures this with
    checks independent of cloze_from_text's own internal guards (a checker
    built from the same rejection logic it's auditing would prove nothing).
    Locks the measured rate in as a real, enforced gate.

    cloze_from_text draws on quiz.R, a single module-level random.Random
    shared for the whole process — every other test that generates content
    advances its internal state, so this test's measured rate depended on
    which tests happened to run before it and in what order: green in
    isolation, red under the full suite, with no code change in between.
    Seeding quiz.R here makes the measurement reproducible regardless of
    what ran earlier, which is the only way a rate-threshold gate can mean
    anything — a flaky gate catches nothing."""
    import importlib
    import sys
    tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
    sys.path.insert(0, tools_dir)
    try:
        audit = importlib.import_module("audit_cloze_defects")
        # Reads real cached prose rather than the frozen paragraph corpus that
        # used to live in the tool: after the 2026-08 precision pass the
        # generator requires a word to recur in the article and be attested in
        # its class, and a five-sentence paragraph supplies neither, so that
        # corpus produced zero items. A corpus the generator refuses cannot
        # gate the generator. See the note at the top of the tool.
        corpus = audit.sample_corpus(limit=120)
        if not corpus:
            pytest.skip("needs a real cached article corpus; clean checkouts have none")
        quiz.R.seed(20260807)
        total_items, total_defects = 0, 0
        for topic, text in corpus:
            items = quiz.cloze_from_text(text, n=5, topic=topic)
            for item in items:
                total_items += 1
                if audit.audit_item(item, text):
                    total_defects += 1
        if total_items <= 20:
            pytest.skip(
                "cached corpus produced only {} items; too few to measure a rate".format(
                    total_items))
        rate = total_defects / total_items * 100
        assert rate < 5.0, "auto-cloze defect rate {:.1f}% exceeds the 5% target".format(rate)
    finally:
        sys.path.remove(tools_dir)


def test_no_cross_domain_twin_at_the_same_stage():
    """Regression: an audit found identical numeric items living in two
    different domain files at the same stage (a redshift calculation shared
    verbatim between earth-space and physics cosmology, a 12-qubit amplitude
    count shared between computer-science and physics) plus two identical
    pattern-recognition drills between math and computer-science at stage 0.
    A reader who studies both domains met the exact same question twice, with
    the second answerable from memory rather than understanding."""
    import re

    def norm(q):
        text = " ".join([str(q.get("prompt", "")), str(q.get("answer", ""))])
        return " ".join(sorted(re.findall(r"[^\W\d_]{3,}", text.lower())))

    by_stage = {}
    for name, d in _banks():
        domain = d.get("id", name)
        for n in d["nodes"]:
            stage = n.get("stage", 0)
            for q in n.get("quiz") or []:
                key = norm(q)
                if not key:
                    continue
                by_stage.setdefault(stage, {}).setdefault(key, set()).add(domain)

    cross_domain_twins = []
    for stage, keys in by_stage.items():
        for key, domains in keys.items():
            if len(domains) > 1:
                cross_domain_twins.append((stage, key, domains))
    assert not cross_domain_twins, \
        "identical items across domains at the same stage: {}".format(cross_domain_twins[:5])


def test_cloze_defect_rate_on_real_curriculum_articles_stays_under_5_percent(tmp_path):
    """The synthetic-corpus audit (above) is fast and reproducible, but it
    only proves the generator behaves on 17 hand-picked paragraphs. The
    reviewer who asked for a 9/10 on assessment validity specifically wanted
    the <5% target checked against what the app actually serves: real
    article text for real curriculum node references, pulled from the
    offline archive. A 120-title sample of this passed at 0.22%, but a
    reviewer scoring assessment validity called a sample "one snapshot," not
    the standing evidence a 9.9 needs — so this checks every article
    reference in the curriculum, not a sample of them."""
    import glob
    import importlib
    import json

    tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
    sys.path.insert(0, tools_dir)
    try:
        audit = importlib.import_module("audit_cloze_defects")
    finally:
        sys.path.remove(tools_dir)

    curr_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "curriculum")
    titles = set()
    for f in glob.glob(os.path.join(curr_dir, "*.json")):
        d = json.load(open(f))
        for n in d["nodes"]:
            titles.update(n.get("articles", []))

    # A runtime-created SQLite file is not an article corpus.  The old
    # existence-only decorator treated an empty DB as the full offline shelf,
    # then `get_article` silently fell through to hundreds of live Wikipedia
    # requests.  Run this expensive standing audit only with a real ZIM or the
    # substantial cache the documented measurement was made against.
    cached = dict(audit.sample_corpus(max_chars=6000))
    import primer.wiki as wiki_module
    has_zim = wiki_module.HAVE_LIBZIM and bool(
        glob.glob(os.path.join(wiki_module.CONTENT_DIR, "*.zim")))
    if not has_zim and len(cached) < 500:
        pytest.skip("needs a real offline archive or substantial article cache")
    # Use a throwaway cache for ZIM reads.  The audit must never initialise,
    # migrate, or write the reader's real Primer DB merely because pytest ran.
    wiki = WikiService(str(tmp_path / "audit.db")) if has_zim else None
    if wiki:
        wiki._live_fetch_blocked_until = float("inf")
    total_items, total_defects = 0, 0
    for t in sorted(titles):
        text = cached.get(t)
        if text is None and wiki:
            r = wiki.get_article(t)
            if r and r.get("html"):
                # 6000 chars is what the retired /api/selfcheck passed; the
                # second half carries evidence the precision filters need.
                text = wiki.article_plaintext(r["html"], max_chars=6000)
        if not text or len(text) < 200:
            continue
        for item in quiz.cloze_from_text(text, n=5, topic=t):
            total_items += 1
            if audit.audit_item(item, text):
                total_defects += 1

    # Was >1000. The 2026-08 precision pass cut real-corpus yield from 1,960
    # items across 586 of 753 curriculum articles to roughly 250 across 69 of
    # them — deliberately: every filter it added refuses items the generator
    # cannot build well, and most articles now fall under the three-item floor
    # and return nothing at all, which is what the UI's honest empty state is
    # for. The floor here is a coverage bar for the measurement, not a yield
    # target for the feature; it is set well under the measured 250 so a real
    # collapse still trips it.
    assert total_items > 150, "coverage too thin to call this the full corpus"
    rate = total_defects / total_items * 100
    assert rate < 5.0, "real-article cloze defect rate {:.2f}% exceeds the 5% target".format(rate)


def test_authored_fraction_word_problems_still_mint_review_cards():
    """Regression: _COMPUTATION's "what is <number><operator>" alternative
    included "/" in its operator class to catch live generator instances
    like "What is 7 + 5?" — but "/" is also how an authored, durable
    fraction word problem writes its fraction ("What is 3/4 of 20?"), and
    the regex could not tell "3/4" the fraction from "3 / 4" the division
    operator. A reader who missed a fixed curriculum question like this
    never got a review card for it: the fact silently never entered the
    SRS deck. No generator in practice.py ever produces a "What is
    <number><symbol>" prompt with a bare "/" right after the first
    number — every generated division prompt spells it out ("shared into
    groups") or uses "÷" — so "/" specifically must not trigger this
    alternative."""
    q = {"kind": "numeric", "prompt": "What is 3/4 of 20?", "answer": "15",
         "explain": "One quarter of 20 is 5, so three quarters is 3 x 5 = 15."}
    assert not quiz.is_ephemeral_prompt(q["prompt"], "numeric")
    cards = quiz.cards_from_missed([q], ["10"], node_id="n1", article="Fractions")
    assert len(cards) == 1 and cards[0]["back"].startswith("15")

    # Genuine generator instances must still be filtered.
    for prompt in ("What is 7 + 5?", "7 + 5 = ?", "2 / 4 = ?", "3/4 × 2"):
        assert quiz.is_ephemeral_prompt(prompt, "numeric"), \
            "{!r} must still be treated as ephemeral".format(prompt)


def test_placement_submit_does_not_drop_focus_from_the_open_dialog():
    """Regression: runPlacement()'s final-submit spinner wiped the modal to a
    bare, unlabelled `<div class="spinner">` — no role, no aria-label, no
    focus management — while a network round trip scored the check. The
    element that held focus was removed from the DOM, so focus fell to
    <body>; with activeElement on body the dialog's own Tab-trap matches
    neither its first nor last focusable element, so Tab walked straight out
    of a dialog still claiming aria-modal="true", and nothing was announced
    to a screen reader during the wait. The exact same failure mode was
    already fixed once for per-question grading via holdFocus() in
    runQuestions() — this was the one place it was never carried over to."""
    js = _web("app.js")
    assert "modal.innerHTML = ''; modal.append(el('div', { class: 'spinner' }));" not in js, \
        "the unlabelled, unfocused spinner must not reappear on the placement submit path"
    assert "'aria-label': 'Scoring your answers…'" in js
    assert "status.focus();" in js


def test_named_theorems_are_defined_where_they_are_used():
    """Regression: a pedagogical read (not a graph/prereq check — coverage
    there was already 100%) found quiz items whose "explain" field named a
    theorem, law, or statistic the curriculum never taught anywhere else:
    the remainder theorem, reduced chi-squared, the squeeze theorem,
    Sylow's theorems, Gödel's second incompleteness theorem, Rice's
    theorem, de Moivre's theorem, and the master theorem for recurrence
    relations were each cited in exactly one node's item and used nowhere
    else across the 348-node graph, asserted rather than stated. Stage 2+
    nodes have no content field beyond "goal" plus prereqs, so a missed
    item's explain field IS the only teaching text a reader ever sees at
    the point of failure — it must be self-contained.

    This is deliberately a targeted allowlist, not a general "every named
    theorem must be locally defined" heuristic — one was tried and
    rejected: flagging every capitalized "X's theorem/law/principle/rule"
    that appears in only one node produced 44 hits across the curriculum,
    almost all false positives on well-known laws (Ohm's, Boyle's,
    Faraday's, Ampere's) that don't need restating because they're
    genuinely common knowledge by the stage they appear at. A number that
    looks like it measures "undefined named concepts" but is actually
    measuring "concepts a regex doesn't recognize as already well-known"
    is the same false-precision trap tools/check_banks.py's own comments
    already document and rejected for a different heuristic. Each term
    below was individually read and confirmed as a genuine gap before being
    added — this list grows only that way, one verified instance at a
    time, same as the four prior audits that found the first seven."""
    checks = [
        ("remainder theorem", lambda e: "p(a)" in e or ("evaluate" in e.lower() and "p(" in e)),
        ("chi-squared", lambda e: "residuals" in e.lower() and "degrees of freedom" in e.lower()),
        ("squeeze theorem", lambda e: "trapped between" in e.lower()),
        ("sylow", lambda e: "prime" in e.lower() and "divides" in e.lower()),
        ("second incompleteness", lambda e: "cannot prove its own consistency" in e.lower()),
        ("rice's theorem", lambda e: "non-trivial property" in e.lower()),
        ("de moivre's theorem", lambda e: "multiplies its angle" in e.lower() or "multiplies the angle" in e.lower()),
        ("master theorem", lambda e: "n^(log_b a)" in e or "n^(log_2" in e),
    ]
    for name, d in _banks():
        for n in d["nodes"]:
            for q in n.get("quiz") or []:
                # A reader sees the prompt and the explain together — a
                # theorem stated in one and applied in the other is still
                # self-contained; only check the "explain" field alone
                # when the term appears there but the prompt never touched it.
                explain = q.get("explain", "")
                full = " ".join([q.get("prompt", ""), q.get("answer", ""), explain])
                low = explain.lower()
                for term, is_defined in checks:
                    if term in low:
                        assert is_defined(explain) or is_defined(full), \
                            "{}: {!r} must be stated, not just named".format(n["id"], term)


def test_a_missed_card_back_never_exceeds_220_chars_even_with_a_long_answer():
    """Regression: cards_from_missed capped only the EXPLANATION portion of a
    card's back at 150 chars, not the total — so a choice-kind item whose
    "answer" text was itself a long sentence (common for scenario-style
    stage 3-5 items) could still produce a back well past the intended
    single-fact cap, up to 255 chars in the real bank across 51 items. A
    card that long is something to read, not something to recall — exactly
    the "819 → 220 char" regression the cap exists to prevent, just from
    the other operand. Cap the total, budgeting whatever room the answer
    text leaves for the explanation."""
    q = {
        "kind": "choice",
        "prompt": "Judge the argument.",
        "answer": "A very long answer sentence that by itself already eats most of the two "
                  "hundred and twenty character budget this card's back is allowed to spend, "
                  "leaving almost nothing for the explanation that follows it.",
        "explain": "This is exactly the kind of long-winded explanatory sentence that, if simply "
                   "appended after an already-long answer with no regard for the combined total, "
                   "would push a card's back well past any reasonable single-fact recall length.",
    }
    cards = quiz.cards_from_missed([q], ["wrong"], node_id="n1", article="")
    assert len(cards) == 1
    assert len(cards[0]["back"]) <= 220, \
        "back is {} chars, must never exceed 220 regardless of answer length".format(len(cards[0]["back"]))


def test_freezes_left_is_not_drained_by_old_disconnected_history(store):
    """Regression: freezes_left() shares streak_days()'s bridging loop, but
    unlike streak_days() (which only returns a count, unaffected by
    whatever the loop does after the live streak chain has already ended),
    freezes_left() returns the leftover budget itself — and the loop kept
    decrementing that budget one day at a time while trying to bridge
    toward ANY older row still in `days`, even a day from a completely
    separate, disconnected historical stretch far beyond what any freeze
    budget could ever close. Only after wastefully draining the budget did
    it discover the bridge failed and break. Any reader with more history
    than STREAK_FREEZES days' worth of gap somewhere in their past — which
    prune()'s "keep one row per day forever" fix makes the normal case for
    a long-term user, not a rare one — saw freezes_left pinned at 0 during
    a perfectly clean, unbroken current streak that had spent nothing."""
    import time as _time

    import primer.learner as lm

    now = _time.time()
    midnight = lm._local_midnight(now)
    with store._conn() as c:
        # A clean 10-day current streak, no gaps at all.
        for d in range(10):
            ts = midnight - d * 86400 + 1800
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                      ("read", "{}", ts, 0))
        # Old activity, disconnected from the live streak by a gap far
        # larger than STREAK_FREEZES could ever bridge.
        for d in range(60, 63):
            ts = midnight - d * 86400 + 1800
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                      ("read", "{}", ts, 0))

    assert store.streak_days() == 10, "the current streak itself must still read correctly"
    assert store.freezes_left() == lm.STREAK_FREEZES, \
        "an unbroken current streak must report its full, unspent freeze budget " \
        "regardless of any disconnected older history"


def test_an_authored_item_is_never_refused_a_card_for_looking_generated():
    """Regression: the errors most worth reviewing produced nothing.

    `is_ephemeral_prompt` read an item's text to decide whether it was a
    one-off instance. That is a proxy for "was this generated", and it was
    wrong for 39 authored bank items across 16 nodes whose text happens to
    look generated: "5 + 3 = ?" is always 8, "How many sides? 🔺" is always
    3. math.1.addition minted ZERO review cards from a fully-missed paper —
    a stage-1 reader could get every addition question wrong and the book
    would decide none of it was worth seeing again.

    The flag cannot simply replace the text rules (a generator stamps it on
    both "7 + 5 = ?" and the always-octagon "Which shape has 8 sides?", and
    trusting it wholesale left 41 practice-assessed nodes card-less), but it
    is decisive in the durable direction: authored items are stamped
    `ephemeral: False` where they load, and a human-fixed prompt with a
    human-fixed answer does not need its text second-guessed.
    """
    from primer.curriculum import Curriculum
    curr = Curriculum()

    suppressed = [(nid, q.get("prompt"))
                  for nid, node in curr.nodes.items()
                  for q in node.get("quiz", [])
                  if quiz.is_ephemeral_prompt(q.get("prompt", ""), q.get("kind", ""),
                                              q.get("ephemeral"))]
    assert suppressed == [], \
        "authored bank items are durable by construction: {}".format(suppressed[:5])

    node = curr.nodes["math.1.addition"]
    questions = list(node["quiz"])
    assert questions, "setup: this node must have an authored bank"
    cards = quiz.cards_from_missed(questions, ["__wrong__"] * len(questions),
                                   "math.1.addition", "")
    assert len(cards) == len(questions), \
        "every missed authored item must come back as a card"


def test_a_one_off_computed_instance_never_becomes_a_permanent_card():
    """Regression: the deck filled with arithmetic nobody should memorise.

    Whether a generated item deserves a review card was decided by matching
    its prompt against a regex. That regex recognised 6 of the ~21
    computation generators, and missed "(7) + (-14) = ?" outright because a
    leading parenthesis defeats its anchor — so failed practice sets minted
    hundreds of permanent cards, each filing one specific randomly-generated
    sum away forever as though it were a fact.

    Extending the pattern again is the trap this codebase has documented
    twice. Nor can it be inferred by sampling: a first fix classified prompts
    by whether they recurred with a stable answer, which measured something
    real but settled a permanent property of an item by drawing samples — the
    same prompt came out durable on one run and ephemeral on the next. Each
    generator now declares which kind of drill it is, once, in
    practice.DURABLE_GENERATORS, so the verdict is a fact about the drill
    rather than a coin flip taken at process start.
    """
    from primer import practice

    # A wrong answer that cannot collide with a real one. Using "x" here hid
    # this test's own bug once: it is the correct answer to a letters item,
    # so the item scored CORRECT and was skipped rather than classified.
    wrong = "zzz_not_the_answer_zzz"

    # Drills that ask the reader to work something out: a card would file one
    # particular instance away forever.
    for gen, level in (("vectors", 4), ("matrices", 4), ("stats", 3),
                       ("place-value", 2), ("negatives", 2), ("decimals", 2),
                       ("complex-numbers", 4), ("slope", 3), ("percent", 2),
                       ("area-perimeter", 2), ("ratios", 3), ("functions", 3),
                       ("kinematics", 4), ("linear-equations", 3), ("addition", 1)):
        items = practice.generate_set(gen, 6, level=level)
        assert items, "setup: {} must generate at level {}".format(gen, level)
        cards = quiz.cards_from_missed(items, [wrong] * len(items), "n.0.x", "")
        assert cards == [], \
            "{}: a computation to perform must not become a card ({})".format(
                gen, [c["front"] for c in cards][:3])

    # Drills that ask the reader to recall a fact must still produce cards —
    # otherwise this "fix" is just switching the deck off.
    for gen, level in (("shapes", 1), ("trig", 3), ("vocabulary", 2),
                       ("primes", 2), ("atoms", 3), ("ph", 3), ("logic-gates", 3)):
        items = practice.generate_set(gen, 4, level=level)
        cards = quiz.cards_from_missed(items, [wrong] * len(items), "n.0.x", "")
        assert len(cards) == len(items), \
            "{}: a fact to recall must still come back as a card".format(gen)


def test_card_worthiness_is_declared_not_sampled():
    """Regression: the classifier decided a permanent property by coin flip.

    Whether a generated item deserved a review card was settled by sampling
    the generator and asking whether that prompt recurred with a stable
    answer. Identical items came out durable on some runs and ephemeral on
    others; one generator declared 155 durable prompts on one pass and 167 on
    the next. A card either belongs in the deck or it does not — that cannot
    depend on which draws a process happened to take at start-up.

    Every generator is declared now, so the same item is judged the same way
    in every process on every run. This asserts it directly rather than
    trusting it."""
    from primer import practice

    wrong = "zzz_not_the_answer_zzz"
    first = {}
    for run in range(25):
        for gen in sorted(practice.GENERATORS):
            for level in (1, 3):
                try:
                    items = practice.generate_set(gen, 4, level=level)
                except Exception:
                    continue
                if not items:
                    continue
                cards = quiz.cards_from_missed(items, [wrong] * len(items), "n.0.x", "")
                verdict = len(cards) > 0
                key = (gen, level)
                if key in first:
                    assert first[key] == verdict, \
                        "{} level {}: judged {} earlier, {} on run {}".format(
                            gen, level, first[key], verdict, run)
                first[key] = verdict

    assert set(practice.DURABLE_GENERATORS) <= set(practice.GENERATORS), \
        "every declared generator must actually exist"


def test_every_practice_generator_declares_its_items_ephemeral():
    """The guard the fix above leans on. Authored items are treated as durable
    because they carry `ephemeral: False`; that is only safe while everything
    *generated* keeps declaring itself. A new generator that forgot the flag
    would have its one-off instances read as authored and mint cards bound to
    a front whose answer changes next sitting — the exact stranded-card bug
    several rounds of this file already fixed one instance at a time."""
    from primer import practice

    missing = []
    for key in sorted(practice.GENERATORS):
        for level in range(6):
            try:
                items = practice.generate_set(key, 4, level=level)
            except Exception:
                continue
            for q in items:
                if q.get("ephemeral") is not True:
                    missing.append((key, level, q.get("prompt", "")[:40]))
    assert missing == [], \
        "these generated items do not declare their provenance: {}".format(missing[:5])


def test_generic_comparison_prompts_never_mint_a_stranded_card():
    """Regression: g_fractions' "compare" mode and g_spelling both emit a
    FIXED, generic prompt ("Which fraction is the largest?" / "Which
    spelling is correct?") while the choices — and therefore the correct
    answer — are freshly randomised on every call, the same shape of bug
    already fixed for order items. is_ephemeral_prompt's prompt-text
    heuristic couldn't tell these apart from a genuinely durable fixed
    prompt like "Which shape has 8 sides?" (always octagon, regardless of
    how many times it's generated) or "P(both heads) = ?" (always 1/4). A
    missed instance minted a card bound to whichever answer happened to be
    correct that one sitting — unanswerable out of context on the next."""
    ephemeral = [
        {"kind": "choice", "prompt": "Which fraction is the largest?",
         "answer": "2/3", "choices": ["2/3", "1/4", "3/8", "1/2"]},
        {"kind": "choice", "prompt": "Which spelling is correct?",
         "answer": "enormous", "choices": ["enormous", "enourmous", "enormus", "inormous"]},
    ]
    cards = quiz.cards_from_missed(ephemeral, ["1/4", "enourmous"], "n.0.x", "")
    assert cards == [], "a fixed-prompt-but-varying-answer item must never mint a card"

    # A genuinely durable fixed prompt must still produce one.
    durable = [{"kind": "choice", "prompt": "Two fair coins are flipped. P(both heads) = ?",
                "answer": "1/4", "choices": ["1/4", "1/2", "1/3"]}]
    cards2 = quiz.cards_from_missed(durable, ["1/2"], "n.0.x", "")
    assert len(cards2) == 1, "a fixed prompt with a genuinely constant answer must still mint a card"


def test_best_streak_is_never_less_than_the_current_streak(store):
    """Regression: best_streak_days() scanned oldest-to-newest with a
    greedy forward algorithm, spending its whole freeze budget on the
    FIRST gap it walked into regardless of whether a later gap needed it
    more. streak_days() always starts counting from today, so it naturally
    spends its own freeze budget on the gap nearest the present — which
    means the two functions could disagree about which span is longest for
    the exact same underlying data, and best_streak_days() could report a
    number strictly LESS than the live streak: a direct contradiction of
    its own contract (a reader's best-ever run can never be shorter than
    the run they are currently on, since the current run IS one instance
    of a run they've put together). Reproduced with activity 10, 7, 6, 5,
    2, 1, 0 days ago and STREAK_FREEZES=2: the old greedy scan spent both
    freezes bridging the older 10-to-7 gap, then had none left for the
    5-to-2 gap and reset, reporting best=4 while the live streak was
    genuinely 6. Fixed with a two-pointer sliding window that checks every
    possible span rather than committing to the first gap encountered."""
    import time as _time

    import primer.learner as lm

    midnight = lm._local_midnight(_time.time())
    with store._conn() as c:
        for d in (10, 7, 6, 5, 2, 1, 0):
            ts = midnight - d * 86400 + 1800
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                      ("read", "{}", ts, 0))

    current = store.streak_days()
    best = store.best_streak_days()
    assert best >= current, \
        "best_streak_days() ({}) must never be less than the current streak ({})".format(best, current)
    assert current == 6 and best == 6, \
        "both must find the true longest 6-day span for this data"


def test_freezes_left_does_not_charge_for_a_day_not_yet_over(store):
    """Regression: freezes_left() anchored its count to `today`
    unconditionally, treating "hasn't logged anything yet today" as if it
    were a missed day worth spending a freeze on — wrong the moment the
    reader's most recent activity is today or yesterday, since today's box
    isn't closed yet. A reader active every single day through yesterday,
    who simply hasn't opened the book yet this morning, saw freezes_left()
    report one less than their true unspent budget — self-correcting the
    instant they logged today's activity, but wrong for a large fraction of
    every day for effectively every returning reader, and rendered directly
    in the UI as misleading "rest days left" text. A genuinely stale streak
    (last activity several days ago, already broken) must still anchor to
    today, since that gap is real and past, not "today hasn't happened
    yet"."""
    import time as _time

    import primer.learner as lm

    midnight = lm._local_midnight(_time.time())

    # Active every day through yesterday; nothing logged yet today.
    with store._conn() as c:
        for d in range(1, 8):
            ts = midnight - d * 86400 + 1800
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                      ("read", "{}", ts, 0))
    assert store.streak_days() == 7
    assert store.freezes_left() == lm.STREAK_FREEZES, \
        "a perfect, unbroken streak must report its full freeze budget even before today's activity is logged"


def test_streak_days_gets_the_same_not_yet_today_anchor_as_freezes_left(store):
    """Regression: freezes_left() was fixed to stop charging a freeze for
    "hasn't logged anything yet today" — but streak_days() itself, the
    number rendered as the primary "N-day streak" badge on every profile
    load, shares the exact same unconditional `expect=today` starting
    point and was never given the analogous fix in the same round. For a
    reader active every day through yesterday with real historical gaps
    that legitimately consume the full freeze budget, the phantom
    "haven't logged in yet today" spend competed with those genuine gaps
    for the same limited budget and broke the count early: streak_days()
    and best_streak_days() disagreed for data that was one single
    connected span (they must always agree in that case, since best-ever
    IS the current run when nothing more recent or longer exists), and
    freezes_left()==0 while streak_days() under-reported the very streak
    that spent both freezes sustaining it — an internally self-contradictory
    result. prune()'s indefinite retention makes "some real gap somewhere
    in a long history" the normal case for a long-term reader, not the
    exception."""
    import time as _time

    import primer.learner as lm

    midnight = lm._local_midnight(_time.time())
    with store._conn() as c:
        # 9-day span (1-9 days ago, nothing today), with days 4 and 7
        # skipped — two single-day gaps needing exactly STREAK_FREEZES=2
        # to bridge into one fully connected 7-day run.
        for d in (1, 2, 3, 5, 6, 8, 9):
            ts = midnight - d * 86400 + 1800
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                      ("read", "{}", ts, 0))

    streak = store.streak_days()
    best = store.best_streak_days()
    freezes = store.freezes_left()
    assert streak == best, \
        "streak_days() ({}) must equal best_streak_days() ({}) when the whole " \
        "history is one connected span".format(streak, best)
    assert streak == 7 and freezes == 0, \
        "the true connected run is 7 days, spending both freezes on the two real gaps"


def test_a_failed_background_download_is_logged(tmp_path, caplog):
    """Regression: _download_worker runs a multi-GB ZIM download entirely
    outside any request context, exactly like server.py's _maintenance_loop
    — but unlike its sibling, which wraps its work in try/except and logs
    any failure (the whole point of this session's correlation-id logging
    infrastructure being that operators can grep the server log for
    failures), _download_worker's except block updated an in-memory dict
    and nothing else. library.py imported no logging module at all. A
    download that failed hours in — network drop, disk full, timeout —
    left zero trace in the server's logs; the only way to discover it was
    to actively poll GET /api/library and read the error field."""
    import logging as _logging
    import urllib.request

    import primer.library as lib

    dest = str(tmp_path / "nope.zim")
    state = {"key": "test_key", "status": "downloading", "url": "http://example.invalid/nope.zim",
              "bytes": 0, "total": 0, "error": ""}

    def fake_urlopen(*a, **k):
        raise ConnectionResetError("Connection reset by peer")

    orig = urllib.request.urlopen
    urllib.request.urlopen = fake_urlopen
    try:
        with caplog.at_level(_logging.ERROR, logger="primer.library"):
            lib._download_worker(state, "http://example.invalid/nope.zim", dest)
    finally:
        urllib.request.urlopen = orig

    assert state["status"] == "error"
    assert any("test_key" in r.message and "ConnectionResetError" in r.message
               for r in caplog.records), \
        "a failed background download must be logged with enough context to find it"


def test_streak_days_and_freezes_left_share_one_implementation(store):
    """Regression: streak_days(), freezes_left() and best_streak_days()
    carried independent copies of the identical anchor-and-walk logic, and
    five consecutive rounds each fixed a day-boundary bug in one copy while
    missing the same bug in the others — discovered only when they started
    disagreeing about the same underlying data. Refactored to share a single
    implementation (_streak_walk / _bridged_run_ending_at) precisely so this
    bug class becomes structurally impossible: there is now exactly one
    place this logic lives, so a fix to one is a fix to all three by
    construction. This test asserts the three stay consistent across a
    spread of scenarios, not just that today's specific values happen to
    match."""
    import time as _time

    import primer.learner as lm

    midnight = lm._local_midnight(_time.time())
    scenarios = [
        ("unbroken through yesterday", [1, 2, 3, 4, 5, 6, 7]),
        ("unbroken through today", [0, 1, 2, 3, 4, 5, 6, 7]),
        ("two real gaps consuming the full budget", [1, 2, 3, 5, 6, 8, 9]),
        ("no events at all", []),
    ]
    for name, offsets in scenarios:
        with store._conn() as c:
            c.execute("DELETE FROM events")
            for d in offsets:
                ts = midnight - d * 86400 + 1800
                c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                          ("read", "{}", ts, 0))
        streak, freezes, best = store._streak_walk()
        assert store.streak_days() == streak, \
            "{}: streak_days() must equal the shared walk's own streak count".format(name)
        assert store.freezes_left() == freezes, \
            "{}: freezes_left() must equal the shared walk's own remaining budget".format(name)
        assert store.best_streak_days() == best, \
            "{}: best_streak_days() must equal the shared walk's own best count".format(name)
        assert best >= streak, \
            "{}: best_streak_days() must never be less than the current streak".format(name)


def test_freeze_debt_expires_instead_of_taxing_a_reader_forever(store):
    """Regression: forgiveness was a lifetime debt that never cleared.

    A reader with an eleven-month run and two single-day sick absences near
    its start saw freezes_left() read 0 every day since — nothing ever
    earned it back — and best_streak_days(), free to choose a window that
    simply started after that old debt, read the very same connected
    history as roughly a month LONGER than streak_days(), which is anchored
    at today and forced to spend its fixed lifetime budget on whichever
    gaps it reaches first walking backward. A single fresh missed day
    eleven months later then cost over a month of CURRENT streak length —
    not because that one miss was expensive on its own, but because paying
    for it left no budget for debt from a year prior that had nothing to do
    with it.

    A spent freeze now expires STREAK_FREEZE_RENEW_DAYS after it was used,
    so an old absence stops competing with today's budget once enough time
    has passed, and streak_days()/best_streak_days() agree on the same
    connected history instead of disagreeing by weeks.
    """
    import time as _time

    import primer.learner as lm

    midnight = lm._local_midnight(_time.time())
    with store._conn() as c:
        # Active every day from 365 down to 2 days ago, except two sick days
        # 330/329 days back; missed yesterday too; active again today.
        sick = {330, 329}
        for d in range(2, 366):
            if d not in sick:
                ts = midnight - d * 86400 + 1800
                c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                          ("read", "{}", ts, 0))
        for d in (0,):
            ts = midnight - d * 86400 + 1800
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                      ("read", "{}", ts, 0))

    streak = store.streak_days()
    best = store.best_streak_days()
    freezes = store.freezes_left()
    assert streak == best, \
        "streak_days() ({}) and best_streak_days() ({}) must agree on one " \
        "connected history once old debt has expired".format(streak, best)
    assert freezes == 1, \
        "only yesterday's real, recent miss should still count against the " \
        "budget — the year-old sick days must have aged out (got {})".format(freezes)
    assert streak >= 360, \
        "the long-expired sick days must not still be blocking the bulk of " \
        "this connected history (got streak={})".format(streak)


def test_a_stale_but_freeze_bridgeable_streak_is_not_dropped_to_zero(store):
    """Regression: the fresh-audit-caught bug in the just-shared walk.
    Falling back to `expect=today` for a genuinely stale streak (last
    activity 2+ days ago) folded "today hasn't closed yet" into the very
    first gap it charged, on top of the real missed days before it — an
    extra, phantom day of charge that a merely-active-through-yesterday
    reader never pays (that branch anchors to `days[0]`, not `today`, so it
    never double-counts). With STREAK_FREEZES=2, a reader stale for exactly
    3 days (last activity 3 days ago, missing only the 2 real days since —
    today does not count, it is not over yet) has exactly enough freeze
    budget to bridge back to an otherwise-unbroken 8-day run before that.
    The old code charged 3 "days" for that single gap (today included) and
    broke on the spot: streak_days() collapsed to 0 while best_streak_days()
    still correctly reported 8 and freezes_left() reported 2 unspent — the
    exact three-way disagreement (0, 8, 2) an independent audit caught,
    directly defeating the freeze feature for the short-break case it
    exists to protect."""
    import time as _time

    import primer.learner as lm

    midnight = lm._local_midnight(_time.time())
    with store._conn() as c:
        # Last activity 3 days ago; before that, 8 fully connected days
        # (days 3 through 10 ago) with no gaps anywhere in that span.
        for d in range(3, 11):
            ts = midnight - d * 86400 + 1800
            c.execute("INSERT INTO events(kind, payload, at, xp) VALUES(?,?,?,?)",
                      ("read", "{}", ts, 0))

    streak = store.streak_days()
    best = store.best_streak_days()
    freezes = store.freezes_left()
    assert streak == best == 8, \
        "streak_days() ({}) must equal best_streak_days() ({}) — the whole " \
        "history is one connected, freeze-bridgeable span".format(streak, best)
    assert freezes == 0, \
        "both freezes must show spent bridging the 2 real missed days (today doesn't count)"
