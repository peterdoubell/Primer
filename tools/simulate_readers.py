"""Five simulated readers, driven through the real book, to find what breaks.

The suite tests the book a function at a time. This drives it the way a person
does: onboard, sit a placement, then live a fortnight — open the day, read,
drill, sit quizzes, work the deck, come back tomorrow. Five of them at once, of
different ages and abilities, sharing one database, because several of the
defects this codebase has had were only visible from *inside a life*: a stage
that collapses on the second sitting, mastery farmed by a guesser, one reader's
XP landing in another's profile.

Nothing here touches the reader's real record. A throwaway database is made per
run and PRIMER_DB is set before primer.server is imported, which is the one
ordering that matters — that module attaches to content/primer.db at import.

Run it:

    python3 tools/simulate_readers.py            # a fortnight, five readers
    python3 tools/simulate_readers.py --days 30 --seed 7
    python3 tools/simulate_readers.py --json out.json

It exits 0 when no invariant was violated, 1 when one was. Findings are
reported, never raised: one run should surface everything it can see, not stop
at the first thing.
"""

import argparse
import datetime
import json
import os
import random
import sys
import tempfile
import time

_REAL_TIME = time.time
_REAL_LOCALTIME = time.localtime
DAY = 86400.0


# --------------------------------------------------------------------------
# a clock the simulation can push forward
# --------------------------------------------------------------------------

class Clock:
    """A movable now.

    Days are the unit the book thinks in — mastery needs two passes two days
    apart, streaks are local calendar days, SRS intervals are days — so a
    simulation that cannot move the date can only ever see the first sitting.
    `time.localtime()` is patched alongside `time.time()` because its no-arg
    form reads the C clock directly and would otherwise keep answering with
    the real date while everything around it had moved on.
    """

    def __init__(self):
        # Start at local mid-morning so a simulated day never straddles
        # midnight and turns one sitting into two.
        today = datetime.date.today()
        self.now = time.mktime(datetime.datetime(
            today.year, today.month, today.day, 10, 0).timetuple())

    def install(self):
        time.time = lambda: self.now
        time.localtime = lambda ts=None: _REAL_LOCALTIME(self.now if ts is None else ts)

    @staticmethod
    def restore():
        time.time = _REAL_TIME
        time.localtime = _REAL_LOCALTIME

    def advance_days(self, n=1):
        """Move to the same hour n local days on — calendar arithmetic, not
        n*86400, so a DST boundary does not silently become a missed day."""
        lt = _REAL_LOCALTIME(self.now)
        day = datetime.date(lt.tm_year, lt.tm_mon, lt.tm_mday) + datetime.timedelta(days=n)
        self.now = time.mktime(datetime.datetime(
            day.year, day.month, day.day, lt.tm_hour, lt.tm_min).timetuple())

    def advance_minutes(self, n):
        self.now += n * 60.0


# --------------------------------------------------------------------------
# who is reading
# --------------------------------------------------------------------------

class Persona:
    """A reader, described by what they can do rather than what they score.

    `skill` is the probability of getting a question right at their own level;
    it decays as the material climbs above them and rises as it falls below, so
    a five-year-old handed a graduate paper fails it the way a child does
    rather than at a flat rate. `diligence` is how much of the offered day they
    actually finish, and `honesty` is the share of answers they give a real try
    — the low value on the guesser is the whole point of that persona.
    """

    def __init__(self, key, name, age, hours, domains, skill, level,
                 diligence=1.0, honesty=1.0, attends=1.0, learns=0.25, note=""):
        self.key = key
        self.name = name
        self.age = age
        self.hours = hours
        self.domains = domains
        self.skill = skill
        self.level = level          # the stage they can actually work at
        self.diligence = diligence
        self.honesty = honesty
        self.attends = attends      # chance of opening the book on a given day
        self.learns = learns        # how much one sitting closes the gap
        self.note = note

    def answers_right(self, rng, stage, learned=0.0):
        """Will they get an item at this stage right?

        `learned` is how much of THIS lesson they have picked up from meeting
        it before — without it the simulation models a reader who is exposed to
        a topic forty times and is no better at it on the fortieth, which is
        not a reader, and it makes the book's own bars unanswerable: a young
        lesson asks for three flawless papers, and whether that is a fair ask
        or an unreachable one depends entirely on whether anybody is learning.
        """
        if rng.random() > self.honesty:
            return False            # not really trying
        gap = stage - self.level
        p = self.skill * (0.55 ** max(0, gap)) + (0.08 * max(0, -gap))
        p += (1.0 - p) * max(0.0, min(1.0, learned))
        return rng.random() < min(0.99, p)


PERSONAS = [
    Persona("mira", "Mira", age=4, hours=3, domains=["math", "biology"],
            skill=0.75, level=0, diligence=0.6, attends=0.8, learns=0.22,
            note="pre-reader; short attention, answers by picture"),
    Persona("jonah", "Jonah", age=9, hours=6, domains=["math", "physics", "language"],
            skill=0.7, level=2, diligence=0.9, attends=0.9, learns=0.3,
            note="solid primary reader, works steadily"),
    Persona("tess", "Tess", age=14, hours=8, domains=["math", "cs", "history"],
            skill=0.45, level=2, diligence=0.5, attends=0.55, learns=0.12,
            note="struggling teenager; patchy attendance, often wrong"),
    Persona("wren", "Wren", age=17, hours=12, domains=["math", "physics", "cs", "chemistry"],
            skill=0.92, level=4, diligence=1.0, attends=1.0, learns=0.5,
            note="gifted; should outrun the book, not be held by it"),
    # Learns nothing on purpose: he never reads the page. He is the control
    # for every claim the book makes about evidence.
    Persona("guy", "Guy", age=30, hours=5, domains=["math", "history"],
            skill=0.2, level=1, diligence=1.0, honesty=0.15, attends=1.0, learns=0.0,
            note="adversarial: clicks through without reading, guesses"),
]


# --------------------------------------------------------------------------
# findings
# --------------------------------------------------------------------------

class Findings:
    """Two channels, deliberately.

    A FINDING is something the book promised and did not do — it fails the run.
    An OBSERVATION is something true about the reader's life that a person
    should look at and decide about: a fourteen-year-old handed the pre-reader
    interface is not a broken invariant, it is a judgement nobody has made yet.
    Filing those as failures would either train the run to be ignored or push
    the tool into making product decisions on its own; dropping them loses the
    most interesting thing a simulation can tell you.
    """

    def __init__(self):
        self.items = []
        self.observations = []

    def check(self, ok, reader, what, detail=""):
        if not ok:
            self.items.append({"reader": reader, "what": what, "detail": str(detail)[:400]})
        return ok

    def note(self, reader, what, detail=""):
        self.items.append({"reader": reader, "what": what, "detail": str(detail)[:400]})

    def observe(self, reader, what, detail=""):
        self.observations.append({"reader": reader, "what": what,
                                  "detail": str(detail)[:400]})

    def __len__(self):
        return len(self.items)


# --------------------------------------------------------------------------
# the driver
# --------------------------------------------------------------------------

class Reader:
    """One persona with a session, a history, and the book in front of them."""

    def __init__(self, persona, client, srv, rng, findings):
        self.p = persona
        self.c = client
        self.srv = srv
        self.rng = rng
        self.f = findings
        self.reader_id = srv.learner.upsert_google_reader(
            "sim-" + persona.key, persona.key + "@sim.invalid", persona.name)
        self.token = srv.learner.create_session(self.reader_id)
        self.history = []           # a row per simulated day
        self.mastered_seen = set()
        self.xp = 0
        self.learned = {}           # node_id -> how much of it they now hold

    # --- plumbing -------------------------------------------------------
    def _cookies(self):
        return {self.srv.READER_COOKIE: self.token}

    def get(self, path, **kw):
        r = self.c.get(path, cookies=self._cookies(), **kw)
        self._no_crash("GET " + path, r)
        return r

    def post(self, path, payload=None, **kw):
        r = self.c.post(path, json=payload or {}, cookies=self._cookies(), **kw)
        self._no_crash("POST " + path, r)
        return r

    def _no_crash(self, where, r):
        self.f.check(r.status_code < 500, self.p.key, "server error on " + where,
                     "%s %s" % (r.status_code, r.text[:200]))

    def _served(self, token):
        """The book's own copy of a paper, answer key included. This is how the
        simulation knows what is right — the wire copy deliberately does not
        carry the key, and reading it from the store rather than guessing is
        what lets a persona's skill be the only thing that decides the mark."""
        entry = self.srv._SERVED.get(token)
        return entry["questions"] if entry else []

    def _answer(self, questions, stage, node_id=""):
        out = []
        learned = self.learned.get(node_id, 0.0) if node_id else 0.0
        for q in questions:
            right = str(q.get("answer", ""))
            if self.p.answers_right(self.rng, stage, learned):
                out.append(right)
                continue
            options = [o for o in (q.get("options") or []) if str(o) != right]
            out.append(str(self.rng.choice(options)) if options else "definitely not that")
        return out

    # --- a life ---------------------------------------------------------
    def onboard(self):
        r = self.post("/api/profile", {
            "name": self.p.name, "age": self.p.age, "hours_per_week": self.p.hours,
            "breadth": "balanced", "domains": self.p.domains, "pronouns": "she"})
        if r.status_code != 200:
            self.f.note(self.p.key, "onboarding refused", r.text[:200])
            return
        prof = r.json()
        self.f.check(prof.get("stage") == 0, self.p.key,
                     "a new reader did not start at stage 0", prof.get("stage"))
        self.f.check(set(prof.get("domains") or []) == set(self.p.domains), self.p.key,
                     "the fields the reader chose were not the fields saved",
                     prof.get("domains"))

    def sit_placement(self, domain):
        """Walk the staircase for one field, answering as this persona would."""
        for _ in range(16):
            paper = self.get("/api/placement/next?domain=" + domain).json()
            if paper.get("settled") or paper.get("done") or not paper.get("questions"):
                return
            served = self._served(paper["token"])
            if not served:
                self.f.note(self.p.key, "placement served a paper the book did not keep", domain)
                return
            self.f.check(len(served) >= 4, self.p.key,
                         "placement paper below the four-item floor",
                         "%s: %d items" % (domain, len(served)))
            answers = self._answer(served, paper["stage"])
            out = self.post("/api/placement/submit", {
                "domain": domain, "stage": paper["stage"],
                "token": paper["token"], "answers": answers}).json()
            if out.get("settled") or out.get("done"):
                return

    def stage(self):
        prof = self.get("/api/state").json().get("profile") or {}
        return prof.get("stage"), prof.get("xp", 0), prof

    def study_day(self, day):
        """One sitting: the day's lessons, then the deck."""
        row = {"day": day, "attended": False, "quizzes": 0, "passes": 0,
               "mastered": 0, "reviews": 0, "xp": 0, "stage": None}
        if self.rng.random() > self.p.attends:
            self.history.append(row)
            return row
        row["attended"] = True

        today = self.get("/api/today")
        if today.status_code != 200:
            self.f.note(self.p.key, "the day would not open", today.text[:200])
            self.history.append(row)
            return row
        day_view = today.json()
        self._check_day_shape(day_view)

        lessons = day_view.get("lessons") or []
        take = max(1, int(round(len(lessons) * self.p.diligence)))
        for node in lessons[:take]:
            self._work_lesson(node, row)
            self.clock.advance_minutes(6)

        self._work_deck(row)

        stage, xp, _ = self.stage()
        row["stage"] = stage
        row["xp"] = xp
        self.f.check(xp >= self.xp, self.p.key, "XP went backwards",
                     "%s -> %s on day %d" % (self.xp, xp, day))
        self.xp = xp
        self.history.append(row)
        return row

    def _check_day_shape(self, view):
        """What the day promises has to be true of the day it hands over."""
        key = self.p.key
        for node in view.get("lessons") or []:
            self.f.check(node.get("title"), key, "a lesson with no title", node.get("id"))
            self.f.check("quiz" not in node, key,
                         "the answer key rode out on the day's lessons", node.get("id"))
        quest = view.get("quest") or {}
        done, total = view.get("quest_done"), view.get("quest_total")
        if isinstance(done, int) and isinstance(total, int):
            self.f.check(0 <= done <= total, key, "the quest counter is out of its own range",
                         "%s/%s" % (done, total))
        # The day is meant to be stable on refresh: same five lessons, same order.
        again = self.get("/api/today")
        if again.status_code == 200:
            first = [n["id"] for n in view.get("lessons") or []]
            second = [n["id"] for n in again.json().get("lessons") or []]
            self.f.check(first == second, key, "the day reshuffled on refresh",
                         "%s vs %s" % (first, second))

    def _work_lesson(self, node, row):
        node_id = node["id"]
        stage = node.get("stage", 0)
        # Read it first, the way the reader would.
        for title in (node.get("articles") or [])[:1]:
            self.get("/api/article", params={"title": title})
            self.post("/api/reading/time", {"title": title, "seconds": 240})

        paper = self.get("/api/quiz/" + node_id)
        if paper.status_code == 409:
            return                  # locked, or the bank is spent — both legitimate
        if paper.status_code != 200:
            self.f.note(self.p.key, "a lesson offered today would not open",
                        "%s %s" % (node_id, paper.text[:160]))
            return
        served = self._served(paper.json()["token"])
        if not served:
            self.f.note(self.p.key, "quiz served a paper the book did not keep", node_id)
            return
        answers = self._answer(served, stage, node_id)
        # Meeting a lesson teaches it. Sitting its quiz and being shown what
        # you missed is the strongest form of that, which is the whole premise
        # of the loop, so it is what the simulation models.
        self.learned[node_id] = min(1.0, self.learned.get(node_id, 0.0) + self.p.learns)
        out = self.post("/api/quiz/submit", {
            "node_id": node_id, "token": paper.json()["token"], "answers": answers,
            "confidence": [], "seconds": 200, "make_cards": True})
        if out.status_code != 200:
            return
        res = out.json()
        row["quizzes"] += 1
        # The quiz route nests its verdict under "mastery"; the practice route
        # returns the same fields flat. Reading only the flat shape is how the
        # first draft of this tool reported "nobody mastered anything in a
        # fortnight" for five readers at once — the mastery checks below were
        # running against a key that was never there.
        verdict = res.get("mastery") or res
        score = res.get("result", {}).get("score", verdict.get("level", 0))
        if score >= 0.8:
            row["passes"] += 1
        if verdict.get("newly_mastered"):
            row["mastered"] += 1
            self._check_mastery_is_earned(node_id, score, verdict)

    def _check_mastery_is_earned(self, node_id, score, verdict):
        """Mastery is the book's strongest claim about a reader. It is supposed
        to need two passing sittings at least a couple of days apart — so any
        first-sitting mastery, and any mastery at all for the guesser, is a
        hole in the thing the whole record rests on."""
        key = self.p.key
        self.f.check(node_id not in self.mastered_seen, key,
                     "the same lesson was newly mastered twice", node_id)
        self.mastered_seen.add(node_id)
        self.f.check(self.p.honesty > 0.3, key,
                     "a reader who never read anything mastered a lesson",
                     "%s at score %.2f" % (node_id, score))
        # Mastery is two passes, genuinely spaced. A newly-mastered node
        # reporting fewer than its own stated requirement means the count and
        # the verdict have come apart.
        passes = verdict.get("passes")
        needed = verdict.get("passes_needed")
        if isinstance(passes, int) and isinstance(needed, int):
            self.f.check(passes >= needed, key,
                         "a lesson was mastered on fewer passes than it asks for",
                         "%s: %d of %d" % (node_id, passes, needed))
        self.f.check(verdict.get("proven") is not False, key,
                     "a lesson was newly mastered without being proven", node_id)

    def _work_deck(self, row):
        due = self.get("/api/review/due?limit=20")
        if due.status_code != 200:
            return
        deck = due.json()
        cards = deck.get("cards") or []
        goal = deck.get("goal") or 0
        self.f.check(goal >= 0, self.p.key, "the deck asked for a negative number of cards", goal)
        for card in cards[:max(0, int(round(len(cards) * self.p.diligence)))]:
            right = self.p.answers_right(self.rng, self.p.level,
                                         self.learned.get(card.get("node_id") or "", 0.0))
            r = self.post("/api/review", {"card_id": card["id"],
                                          "quality": 5 if right else 1, "seconds": 20})
            if r.status_code == 200:
                row["reviews"] += 1
            self.clock.advance_minutes(1)


# --------------------------------------------------------------------------
# cross-reader invariants
# --------------------------------------------------------------------------

def check_isolation(readers, findings, before):
    """Five readers, one database. Whatever one of them did today, it must not
    show up in anyone else's record."""
    for r in readers:
        _, xp, prof = r.stage()
        was = before[r.p.key]
        findings.check(prof.get("name") == r.p.name, r.p.key,
                       "a reader is looking at someone else's profile", prof.get("name"))
        findings.check(prof.get("reader_id") == r.reader_id, r.p.key,
                       "the session resolved to the wrong reader",
                       "%s != %s" % (prof.get("reader_id"), r.reader_id))
        if not was["attended"]:
            findings.check(xp == was["xp"], r.p.key,
                           "a reader who did not open the book gained XP",
                           "%s -> %s" % (was["xp"], xp))


def check_outcomes(readers, findings):
    """The shape of a life, once it has been lived. These are about the book
    doing its job, not about it staying upright: a gifted reader held at the
    nursery door and a guesser waved through are both silent failures."""
    by_key = {r.p.key: r for r in readers}

    # A suite that cannot fail is not evidence. If nobody mastered anything,
    # every mastery check above ran on an empty set and the run proved nothing
    # about the thing it exists to watch — so say so rather than print a clean
    # sheet. This is not hypothetical: it was true of this tool's first draft.
    findings.check(any(r.mastered_seen for r in readers), "-",
                   "no reader mastered anything, so the mastery checks proved nothing",
                   "raise --days, or the frontier has stalled")

    guy = by_key["guy"]
    findings.check(not guy.mastered_seen, "guy",
                   "guessing alone produced mastery",
                   sorted(guy.mastered_seen)[:6])

    wren = by_key["wren"]
    stage, xp, _ = wren.stage()
    findings.check(stage >= 3, "wren",
                   "a reader who aces everything is still being taught below their level",
                   "stage %s" % stage)
    findings.check(xp > 0, "wren", "a fortnight of correct work paid nothing", xp)

    mira = by_key["mira"]
    stage, _, _ = mira.stage()
    findings.check(stage <= 2, "mira",
                   "a four-year-old was promoted past what she can read", "stage %s" % stage)

    for r in readers:
        # Stage <= 1 is not a difficulty setting, it is an interface: the web
        # client keys read-aloud, picture-tap answers, "Look and see", toddler
        # praise and a hidden score off `S.stage <= 1` in fourteen places. A
        # reader old enough to notice, working at that level because the book
        # measured them there, gets all of it. Whether that is support or
        # humiliation is a call for a person, so it is filed as something to
        # look at rather than something that failed.
        stage, _, _ = r.stage()
        if r.p.age >= 10 and stage is not None and stage <= 1:
            findings.observe(r.p.key,
                             "an older reader is being shown the pre-reader interface",
                             "age %s at stage %s — read-aloud, picture taps, no score"
                             % (r.p.age, stage))
        if not r.mastered_seen and any(row["attended"] for row in r.history):
            findings.observe(r.p.key, "attended but mastered nothing all run",
                             "%d quizzes" % sum(row["quizzes"] for row in r.history))

        stages = [row["stage"] for row in r.history if row["stage"] is not None]
        for i in range(1, len(stages)):
            findings.check(stages[i] >= stages[i - 1] - 1, r.p.key,
                           "the reading level collapsed between two days",
                           "%s -> %s" % (stages[i - 1], stages[i]))
        attended = [row for row in r.history if row["attended"]]
        if attended and r.p.honesty > 0.5 and r.p.skill > 0.6:
            worked = sum(row["quizzes"] for row in attended)
            findings.check(worked > 0, r.p.key,
                           "a reader attended every day and was never given anything to do")


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------

def simulate(days, seed, quiet=True):
    tmp = tempfile.mkdtemp(prefix="primer-sim-")
    db = os.path.join(tmp, "sim.db")
    # Before primer.server is imported: that module attaches to the reader's
    # real record unless this points elsewhere.
    os.environ["PRIMER_DB"] = db
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    import logging
    if quiet:
        logging.disable(logging.WARNING)

    clock = Clock()
    clock.install()
    try:
        import primer.server as srv
        from primer.learner import LearnerStore
        from primer.wiki import WikiService
        from fastapi.testclient import TestClient

        srv.learner = LearnerStore(db)
        srv.wiki = WikiService(db)
        srv.BACKUP_DIR = os.path.join(tmp, "backups")

        findings = Findings()
        rng = random.Random(seed)
        with TestClient(srv.app) as client:
            readers = []
            for persona in PERSONAS:
                r = Reader(persona, client, srv, random.Random(rng.random()), findings)
                r.clock = clock
                r.onboard()
                readers.append(r)

            for r in readers:
                for domain in r.p.domains:
                    r.sit_placement(domain)
                stage, _, _ = r.stage()
                print("  placed %-6s age %-3s -> stage %s  (%s)"
                      % (r.p.name, r.p.age, stage, r.p.note))

            for day in range(1, days + 1):
                before = {}
                for r in readers:
                    _, xp, _ = r.stage()
                    before[r.p.key] = {"xp": xp}
                rows = {}
                for r in readers:
                    rows[r.p.key] = r.study_day(day)
                    before[r.p.key]["attended"] = rows[r.p.key]["attended"]
                check_isolation(readers, findings, before)
                clock.advance_days(1)

            check_outcomes(readers, findings)

            summary = []
            for r in readers:
                stage, xp, prof = r.stage()
                attended = sum(1 for row in r.history if row["attended"])
                summary.append({
                    "reader": r.p.name, "age": r.p.age, "note": r.p.note,
                    "stage": stage, "xp": xp, "streak": prof.get("streak"),
                    "days_attended": attended,
                    "quizzes": sum(row["quizzes"] for row in r.history),
                    "passes": sum(row["passes"] for row in r.history),
                    "mastered": len(r.mastered_seen),
                    "reviews": sum(row["reviews"] for row in r.history),
                })
        return summary, findings
    finally:
        clock.restore()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--json", default="")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    print("Five readers, %d days, seed %d" % (args.days, args.seed))
    summary, findings = simulate(args.days, args.seed, quiet=not args.verbose)

    print("\n%-7s %-4s %-6s %-7s %-7s %-8s %-8s %s"
          % ("reader", "age", "stage", "days", "quizzes", "passed", "mastered", "xp"))
    for row in summary:
        print("%-7s %-4s %-6s %-7s %-7s %-8s %-8s %s"
              % (row["reader"], row["age"], row["stage"], row["days_attended"],
                 row["quizzes"], row["passes"], row["mastered"], row["xp"]))

    if findings.items:
        print("\n%d finding(s):" % len(findings))
        seen = {}
        for item in findings.items:
            key = (item["reader"], item["what"])
            seen.setdefault(key, []).append(item["detail"])
        for (reader, what), details in seen.items():
            print("  [%s] %s (x%d)" % (reader, what, len(details)))
            if details[0]:
                print("        %s" % details[0])
    else:
        print("\nNo invariant violated.")

    if findings.observations:
        print("\n%d thing(s) worth a look (not failures):" % len(findings.observations))
        for item in findings.observations:
            print("  [%s] %s" % (item["reader"], item["what"]))
            if item["detail"]:
                print("        %s" % item["detail"])

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"summary": summary, "findings": findings.items,
                   "observations": findings.observations}, fh, indent=2)
        print("\nwrote %s" % args.json)

    return 1 if findings.items else 0


if __name__ == "__main__":
    sys.exit(main())
