"""The frame story: personalization, the reader's cursor, and page-turn gates.

The story's invariants, in brief:
- The reader is the protagonist: the source text names nobody and genders
  nobody. It carries {NAME} and pronoun tokens, and `personalize` renders
  them with the reader's own name and pronouns (see PRONOUNS).
- A chapter position is stored as a stable chapter *id*, never a raw array
  index — an id survives chapters being inserted mid-arc. Legacy profiles
  that predate the id are migrated once (see `resolve_position`).
- A page turns only through the explicit advance endpoint. The cursor itself
  never auto-advances past an earned chapter; only chapters in fields the
  reader never chose are skipped, and that skip is recomputed live so a later
  domain change takes effect immediately.
- Turning a page requires real evidence for the lesson it leads to: one honest
  pass (or standing assumed credit) for lessons at or below the reader's
  placed stage, full two-pass proof for anything ahead of them.

Every function takes its collaborators explicitly — the story dict, the
curriculum and the learner store — so this module holds no state of its own.
"""

import re
from typing import List, Optional


def book_title(story: dict, name: str) -> str:
    """The frame story is titled for its heroine; give it to the reader."""
    if not name or name.strip().lower() == "nell":
        return story["title"]
    return story["title"].replace("Nell", name)


# The reader's pronouns, and the words that have to agree with them. A name
# never tells you someone's pronouns, so the source text carries tokens rather
# than one set of pronouns baked in, and every occurrence is rendered per
# reader. "her" is two different words in English — object ("the fox blinked at
# her") and possessive determiner ("her own name") — which cannot be told apart
# by regex after the fact, so data/story/frame.json marks each one at the
# source as {OBJ} or {POSS}.
#
# Verb agreement is part of the pronoun, not an afterthought: they/them takes
# the plural form. Only forms that actually differ are tokenised — the story is
# largely past tense, where only "was/were" splits — but the table is complete
# so new prose has tokens to reach for.
PRONOUNS = {
    "she": {"SUBJ": "she", "OBJ": "her", "POSS": "her", "POSSPRON": "hers",
            "REFL": "herself", "WAS": "was", "IS": "is", "HAS": "has", "DOES": "does"},
    "he": {"SUBJ": "he", "OBJ": "him", "POSS": "his", "POSSPRON": "his",
           "REFL": "himself", "WAS": "was", "IS": "is", "HAS": "has", "DOES": "does"},
    "they": {"SUBJ": "they", "OBJ": "them", "POSS": "their", "POSSPRON": "theirs",
             "REFL": "themselves", "WAS": "were", "IS": "are", "HAS": "have",
             "DOES": "do"},
}

DEFAULT_PRONOUNS = "they"

_TOKEN = re.compile(r"\{([A-Za-z]+)\}")


def render(text: str, name: str, pronouns: str = DEFAULT_PRONOUNS) -> str:
    """Fill the story's {NAME}/{SUBJ}/{POSS}/... tokens for one reader.

    A token written in Title case ({Subj}) renders capitalised, which is how a
    sentence-initial pronoun stays a sentence-initial pronoun. An unknown token
    is left alone rather than silently blanked: a typo in the source should be
    visible in a test, not swallowed into a hole in the prose.
    """
    words = PRONOUNS.get(pronouns) or PRONOUNS[DEFAULT_PRONOUNS]
    reader = (name or "").strip() or "Nell"

    def sub(m):
        key = m.group(1)
        if key.upper() == "NAME":
            return reader
        word = words.get(key.upper())
        if word is None:
            return m.group(0)
        return word.capitalize() if key[0].isupper() and not key.isupper() else word

    return _TOKEN.sub(sub, text or "")


def reader_pronouns(prof: Optional[dict]) -> str:
    """The reader's pronouns, from the profile, defaulting to the neutral set.

    Lives in `settings` because that is where reader-owned preferences live and
    where the profile row already has room for them. An unrecognised stored
    value falls back rather than raising: a story page is the wrong place to
    discover a bad row.
    """
    stored = ((prof or {}).get("settings") or {}).get("pronouns")
    return stored if stored in PRONOUNS else DEFAULT_PRONOUNS


def personalize(chapter: dict, name: str, pronouns: str = DEFAULT_PRONOUNS) -> dict:
    """Render a chapter for this reader: their name and their pronouns."""
    out = dict(chapter)
    out["text"] = [render(t, name, pronouns) for t in chapter.get("text", [])]
    out["prompt"] = render(chapter.get("prompt") or "", name, pronouns)
    out["title"] = render(chapter.get("title") or "", name, pronouns)
    return out


# Where chapters were first inserted mid-array, invalidating raw-index
# progress saved by older profiles. Positions at or past it meant "at the
# finale", and a reader at the finale always means the CURRENT finale.
LEGACY_STORY_INSERT_AT = 18


def resolve_position(settings: dict, chapters: List[dict]) -> int:
    """The reader's chapter index, from a stable id when we have one.

    Older profiles only carry a pre-fix raw array index; those are resolved
    once here and re-saved as an id on the next commit.
    """
    chapter_id = settings.get("story_chapter_id")
    if chapter_id:
        for i, ch in enumerate(chapters):
            if ch["id"] == chapter_id:
                return i
        return 0
    legacy = int(settings.get("story_progress", 0))
    if legacy >= LEGACY_STORY_INSERT_AT:
        return len(chapters) - 1
    return legacy


def cursor(story: dict, curr, learner, prof: dict, commit: bool = False):
    """The chapter the reader is on, whether it may be turned, and what it wants.

    Pass commit=True only from a write endpoint: a GET must not persist. Even
    then, only the legacy-format migration is persisted — never the
    domain-skip walk, which must stay recomputable (see module docstring).
    """
    settings = prof.get("settings", {})
    chapters = story["chapters"]
    progress = resolve_position(settings, chapters)
    proven = learner.proven_set()
    passed = learner.passed_set()
    standing = learner.mastered_set()
    domains = prof.get("domains") or [d["id"] for d in curr.domains]
    stage = int(prof.get("stage") or 0)

    def earned(node, target):
        if not target:
            return True
        if target in proven:
            return True
        # A lesson the reader was placed past opens on one honest pass — or on
        # the standing assumed credit the book itself gave them for it, which
        # is what keeps the early arc reachable for readers onboarded above
        # stage 0 (their gate lessons are exactly the ones `next_lessons`
        # will never offer). `mastered_set` is decay-aware, so only credit
        # that still stands today counts.
        return (bool(node) and node["stage"] < stage
                and (target in passed or target in standing))

    def skippable(ch):
        # Only a chapter in a field the reader never chose is skipped. A
        # chapter merely *ahead* of them must wait, not vanish.
        node = curr.node(ch.get("leads_to", "") or "")
        if node is None:
            return False
        return node["domain"] not in domains

    while progress < len(chapters):
        if skippable(chapters[progress]):
            progress += 1
            continue
        break
    stale_format = "story_chapter_id" not in settings
    if commit and stale_format:
        s = dict(settings)
        s["story_chapter_id"] = (chapters[progress]["id"]
                                 if progress < len(chapters) else chapters[-1]["id"])
        s.pop("story_progress", None)
        learner.save_profile(prof["name"], prof["age"], prof["hours_per_week"],
                             prof["breadth"], prof["stage"], prof["domains"], s)
    if progress >= len(chapters):
        # The arc ends rather than disappearing: hold on the last page.
        last = personalize(chapters[-1], prof.get("name", ""), reader_pronouns(prof))
        return last, len(chapters) - 1, False
    chapter = chapters[progress]
    target = chapter.get("leads_to", "")
    node = curr.node(target)
    # The last chapter is an epilogue: it closes the arc and turns to nothing.
    can_advance = bool(target) and earned(node, target) and progress < len(chapters) - 1
    return (personalize(chapter, prof.get("name", ""), reader_pronouns(prof)),
            progress, can_advance)


def needs(curr, learner, chapter: Optional[dict]) -> Optional[dict]:
    """What the current chapter is waiting for, in plain terms."""
    if not chapter:
        return None
    target = chapter.get("leads_to", "")
    node = curr.node(target)
    if not node:
        return None
    info = learner.mastery_detail(target)
    # A lesson the reader was placed past opens on one honest pass; anything
    # ahead of them needs the full two, spaced. Say which.
    prof = learner.get_profile() or {}
    placed_past = node["stage"] < int(prof.get("stage") or 0)
    needed = 1 if placed_past else 2
    # A faded lesson's lifetime pass count is stale evidence — reporting it
    # verbatim reads as "almost there" on a page that is in fact shut until
    # the reader proves it again.
    faded = info.get("faded", False)
    passes = 0 if faded else info.get("passes", 0)
    return {
        "node_id": target,
        "title": node["title"],
        "passes": min(passes, needed),
        "passes_needed": needed,
        "ready_at": None if placed_past else info.get("ready_at"),
        "faded": faded,
        "ever_proven": info.get("ever_proven", False),
    }
