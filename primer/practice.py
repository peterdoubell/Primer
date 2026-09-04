"""Procedural practice generators — infinite exercises, no two sessions alike.

Each generator returns question dicts:
  {kind: 'choice'|'numeric'|'order'|'tally', prompt, choices?, items?, answer,
   explain?}
Generators are keyed; curriculum nodes reference them by key. Levels run from
preschool counting to undergraduate calculus and linear algebra.
"""

import json
import math
import os
import random
from fractions import Fraction
from typing import Callable, Dict, List, Optional

R = random.Random()


def _mc(prompt: str, answer, distractors: List, explain: str = "", pad: bool = True) -> Dict:
    opts = [str(answer)] + [str(d) for d in distractors]
    seen, choices = set(), []
    for o in opts:
        if o not in seen:
            seen.add(o)
            choices.append(o)
    if pad:
        # Pad near the answer when it is numeric, so distractors stay plausible
        # instead of random noise.
        try:
            base = float(str(answer))
            guard = 0
            while len(choices) < 4 and guard < 40:
                guard += 1
                delta = R.choice([-3, -2, -1, 1, 2, 3, 5, 10])
                cand = base + delta
                cand = str(int(cand)) if cand == int(cand) else str(round(cand, 2))
                if cand not in seen and cand != str(answer):
                    seen.add(cand)
                    choices.append(cand)
        except (ValueError, TypeError):
            pass
        # Last resort must still look like it belongs beside the key. The old
        # filler was R.randint(1, 99) — for "364 days" scale questions the two
        # noise options sat two orders of magnitude off and the answer was the
        # only plausible number on the card. Scale the filler to the key
        # itself: percentage and small-integer offsets around the numeric
        # answer (or, when the answer is not numeric, around whichever numeric
        # option is already present), deduplicated against everything shown.
        base = None
        for source in [str(answer)] + [str(c) for c in choices]:
            try:
                base = float(source)
                break
            except (ValueError, TypeError):
                continue
        guard = 0
        while len(choices) < 4 and guard < 60:
            guard += 1
            if base is not None:
                mode = R.choice(["pct", "pct", "off"])
                if mode == "pct" and base != 0:
                    cand = base * (1 + R.choice([-0.5, -0.25, -0.1, 0.1, 0.25, 0.5, 1.0]))
                else:
                    step = max(1, round(abs(base) * 0.05))
                    cand = base + R.choice([-3, -2, -1, 1, 2, 3]) * step
                cand = round(cand, 2)
                cand = str(int(cand)) if cand == int(cand) else str(cand)
            else:
                # Nothing numeric anywhere: no scale to honour, so any filler
                # is equally (im)plausible — small integers at least read as
                # options rather than debris.
                cand = str(R.randint(1, 12))
            if cand not in seen and cand != str(answer):
                seen.add(cand)
                choices.append(cand)
        while len(choices) < 4:   # guard exhausted (tiny option space): pad flat
            cand = str(R.randint(1, 99))
            if cand not in seen:
                seen.add(cand)
                choices.append(cand)
    choices = choices[:4]
    R.shuffle(choices)
    return {"kind": "choice", "prompt": prompt, "choices": choices,
            "answer": str(answer), "explain": explain, "ephemeral": True}


def _near_distractors(key: int, k: int = 3, lo: int = None, hi: int = None) -> List[int]:
    """k distinct plausible neighbours of `key`, on a randomly chosen split.

    The exploit these exist to close is the key's RANK once a reader sorts the
    options by size. `_mc` shuffles the display order, which is what every
    position audit measured — and sorting undoes a shuffle, so it was never the
    protection it looked like. What was fixed was the recipe: g_counting offered
    {n-2, n-1, n, n+1}, so the key was permanently the second largest;
    g_patterns offered {nxt-step, nxt, nxt+1, nxt+step}, so for any step>1 it
    was permanently the second smallest; g_shapes was worse again. "Always pick
    the third smallest" scored 87% on counting and 90% on patterns against a 25%
    chance rate, and cleared the 0.8 mastery gate on that alone.

    So the number of neighbours drawn from below the key is chosen at random
    rather than baked into the recipe. `lo`/`hi` bound the sensible range — a
    counting drill must not offer minus one, which is separately why the
    preschool bank was showing negative numbers among its answers.

    A generic version of this once lived inside `_mc` and applied to every
    numeric option set. It was measured and withdrawn: generators whose
    distractors were already well spread (g_place_value draws three random
    distinct digits) came out WORSE, because rebuilding from mirrored offsets
    near the zero floor collapsed the below-side and pinned the key at rank 1 —
    27% became 40%. The generators that need this are the ones with a fixed
    recipe, and they are named here rather than guessed at. The arbiter for all
    of them is tools/check_generators.py.
    """
    want_below = R.randint(0, k)
    below, above = [], []
    d = 1
    while len(below) < want_below and d <= k + 3:
        v = key - d
        if lo is None or v >= lo:
            below.append(v)
        d += 1
    d = 1
    while len(above) < k - len(below) and d <= k + 3:
        v = key + d
        if hi is None or v <= hi:
            above.append(v)
        d += 1
    # Short on one side (the key sits near a bound): make the count up from the
    # other rather than returning fewer options than asked for.
    d = 1
    while len(below) + len(above) < k and d <= k + 6:
        for v in (key - d, key + d):
            if v == key or v in below or v in above:
                continue
            if lo is not None and v < lo:
                continue
            if hi is not None and v > hi:
                continue
            (below if v < key else above).append(v)
            if len(below) + len(above) >= k:
                break
        d += 1
    return below + above


def _choice2(prompt: str, answer, other, explain: str = "", say: str = "") -> Dict:
    """A genuine binary choice (e.g. bigger/smaller) — exactly two options, no
    nonsense padding."""
    choices = [str(answer), str(other)]
    R.shuffle(choices)
    q = {"kind": "choice", "prompt": prompt, "choices": choices,
         "answer": str(answer), "explain": explain, "ephemeral": True}
    if say:
        q["say"] = say
    return q


def _num(prompt: str, answer, explain: str = "") -> Dict:
    # `ephemeral`: a randomly generated instance — drill it via the generator,
    # never as a fixed flashcard.
    return {"kind": "numeric", "prompt": prompt, "answer": str(answer),
            "explain": explain, "ephemeral": True}


# ---------------- Stage 0: Seedling ----------------

COUNT_THINGS = ["🍎", "⭐", "🐟", "🌸", "🎈", "🐞", "🦋", "🐚", "🍄", "☂️"]

def g_counting(level=0):
    """Counting, asked both ways — and mostly asked as counting.

    `g_count_tally` below is a real production instrument for pre-readers: the
    objects themselves are the answering surface, so a child who counts five
    apples correctly but cannot yet read the numeral 5 is marked right. It was
    written, tested (tests/test_tally_generator.py), given a bespoke touch UI
    in app.js and a validator in check_banks.py — and then wired to nothing.
    `grep -rn count-tally` found it only in practice.py and its own test, so no
    reader had ever met it.

    That mattered more than one unused generator, because it was the ONLY
    production item a young reader could have met anywhere: all 622 authored
    items at stages 0-1 are multiple choice, and all twelve generators their
    nodes reference returned choice items at level 0. For the Seedling and
    Sprout years — which the pacing model prices in years, not weeks — the book
    asked the reader to recognise an answer and never once to produce one.

    So counting now mints the tally form most of the time for young readers,
    and keeps the multiple-choice form as the minority case: recognising the
    numeral is a real, separate skill worth practising, it just should not be
    the whole of what "counting" means. Above Sprout the reader can read
    numerals fluently and the choice form is the honest one.
    """
    if (level or 0) <= 1 and R.random() < 0.7:
        return g_count_tally(level)
    n = R.randint(1, 10)
    thing = R.choice(COUNT_THINGS)
    q = _mc("How many do you see?\n\n" + (thing + " ") * n, n,
            _near_distractors(n, 3, lo=1))
    q["say"] = "How many do you see? Count them out loud."
    q["speak_choices"] = True
    return q


# The same countable objects, each carried with the word for it. A tally token
# is a real button, and a button whose entire label is an emoji is announced as
# whatever name the reader's screen reader happens to hold for that glyph — so
# the noun travels with the item and the renderer can name each token, and the
# running count, in words a five-year-old already owns. Singular and plural
# both, because "fish" is not "fishs" and the count line is spoken aloud.
TALLY_THINGS = [("🍎", "apple", "apples"), ("⭐", "star", "stars"),
                ("🐟", "fish", "fish"), ("🌸", "flower", "flowers"),
                ("🎈", "balloon", "balloons"), ("🐞", "ladybird", "ladybirds"),
                ("🦋", "butterfly", "butterflies"), ("🐚", "shell", "shells"),
                ("🍄", "mushroom", "mushrooms"), ("☂️", "umbrella", "umbrellas")]


def g_count_tally(_=0):
    """Counting scored as counting.

    Every other item a pre-reader meets is recognition: `g_counting` above
    draws 🍎🍎🍎 and offers ['2', '3', '4'], so a child who counts the apples
    perfectly but cannot yet read the numeral 3 is marked wrong. That item
    measures numeral reading and files the result under counting. Here the
    objects themselves are the answering surface — one press each, the book
    counting along, then one button to commit — so nothing on the card has to
    be read, and what is scored is the act being taught.

    The item ships the objects and NOT a count: the number of things drawn is
    the key (`len(items) == int(answer)`), so there is no second field for the
    two to drift apart in. And `answer` stays a plain digit string, which is
    what makes this a new gesture rather than a new grading path — a committed
    tally is a number, `_numeric_equal` marks it exactly as it marks a typed
    one, and quiz.py needs no clause for `tally` at all.
    """
    # Three at the floor: one or two are subitised at a glance, so there is no
    # counting to score. Nine at the ceiling: the tokens are hit targets that
    # must all fit a phone screen at once, and a child who can hold a stable
    # count to nine already has the principle the lesson is after.
    n = R.randint(3, 9)
    thing, one, many = R.choice(TALLY_THINGS)
    return {
        "kind": "tally",
        "prompt": "Touch each {}, then press the button.".format(one),
        "items": [thing] * n,
        "answer": str(n),
        # Never enumerates — the same rule the ordering sequences follow. It
        # names the task; saying the count would read the answer aloud.
        "say": "How many {}? Touch each one.".format(many),
        "explain": "There are {} — one number word for each one you touched.".format(n),
        "ephemeral": True,
        # `generate_set` stamps `gen` on the way out, and it is stamped here as
        # well so the item can name its origin even when minted directly. That
        # matters more for this kind than for the others: with no generator
        # named, `quiz.is_ephemeral_prompt` falls back to reading the prompt,
        # and this prompt is an instruction rather than a question — no phrase
        # in it marks the one-off instance it is. An unstamped tally would mint
        # a permanent card fronted "Touch each apple, then press the button."
        # and backed by whichever count that single instance happened to draw.
        "gen": "count-tally",
    }


def g_letters(_):
    letter = R.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    lower = letter.lower()
    mode = R.choice(["match", "sound", "next"])
    if mode == "match":
        wrong = R.sample([c.lower() for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c != letter], 3)
        q = _mc("Which little letter matches the big letter  {} ?".format(letter),
                lower, wrong, pad=False)
        q["say"] = "Which little letter matches the big letter {}?".format(letter)
        q["speak_choices"] = True
        return q
    if mode == "next":
        idx = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".index(letter)
        if idx >= 25:
            letter, idx = "A", 0
        nxt = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[idx + 1]
        wrong = R.sample([c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c != nxt], 3)
        q = _mc("Which letter comes after  {} ?".format(letter), nxt, wrong, pad=False)
        q["say"] = "Which letter comes after {}?".format(letter)
        q["speak_choices"] = True
        return q
    words = {"A": "Apple", "B": "Ball", "C": "Cat", "D": "Dog", "E": "Egg", "F": "Fish",
             "G": "Goat", "H": "Hat", "I": "Ice", "J": "Jam", "K": "Kite", "L": "Lion",
             "M": "Moon", "N": "Nest", "O": "Owl", "P": "Pig", "Q": "Queen", "R": "Rain",
             "S": "Sun", "T": "Tree", "U": "Umbrella", "V": "Van", "W": "Water",
             "X": "Xylophone", "Y": "Yarn", "Z": "Zebra"}
    word = words[letter]
    wrong = R.sample([w for k, w in words.items() if k != letter], 3)
    q = _mc("Which word starts with the letter  {} ?".format(letter), word, wrong, pad=False)
    q["say"] = "Which word starts with the letter {}?".format(letter)
    q["speak_choices"] = True
    return q

def g_compare(_):
    a, b = R.sample(range(1, 20), 2)
    big, small = max(a, b), min(a, b)
    if R.random() < 0.5:
        return _choice2("Which is bigger:  {}  or  {} ?".format(a, b), big, small,
                        say="Which number is bigger, {} or {}?".format(a, b))
    return _choice2("Which is smaller:  {}  or  {} ?".format(a, b), small, big,
                    say="Which number is smaller, {} or {}?".format(a, b))


def _order(prompt: str, items: List[str], say: str, explain: str = "") -> Dict:
    """A tap-in-sequence item.

    A second assessment format for early stages: recognition multiple choice
    only ever asks "which of these?", while ordering asks the child to *produce*
    a sequence. Fully tappable and spoken, so it needs no reading.
    """
    shown = items[:]
    guard = 0
    while shown == items and guard < 20:
        guard += 1
        R.shuffle(shown)
    return {"kind": "order", "prompt": prompt, "items": shown,
            "answer": " ".join(items), "say": say, "explain": explain,
            "speak_choices": True, "ephemeral": True}


def g_order_numbers(level=0):
    start = R.randint(1, 12 if level >= 1 else 5)
    step = R.choice([1, 1, 2]) if level >= 1 else 1
    seq = [str(start + i * step) for i in range(4)]
    return _order("Put them in order, smallest first", seq,
                  "Tap the numbers in order, smallest first.",
                  "They go up by {} each time.".format(step))


def g_order_letters(_=0):
    i = R.randint(0, 22)
    seq = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i:i + 4])
    return _order("Put the letters in alphabet order", seq,
                  "Tap these letters in alphabet order.",
                  "They follow the alphabet song.")


# The spoken line must NOT enumerate the sequence — that would read the answer
# aloud. It names the task only.
LIFE_SEQUENCES = [
    ["🥚", "🐛", "🦋"],
    ["🌱", "🌿", "🌳"],
    ["🥚", "🐣", "🐔"],
    ["🌰", "🌱", "🌳"],
    ["🐛", "🦋", "🥚"][:0] or ["🐣", "🐤", "🐔"],
]


def g_order_lifecycle(_=0):
    seq = R.choice(LIFE_SEQUENCES)
    return _order("Put them in the order they grow", seq,
                  "Tap these pictures in the order that living things grow, "
                  "from the very smallest beginning to the grown-up one.",
                  "Living things start small and grow bigger.")


DAY_SEQUENCES = [
    ["🌅", "☀️", "🌆", "🌙"],
    ["🌱", "☀️", "🍂", "❄️"],
]


def g_order_time(_=0):
    seq = R.choice(DAY_SEQUENCES)
    return _order("Put them in time order", seq,
                  "Tap these pictures in time order, starting with the one "
                  "that comes first.",
                  "That is the order they come around.")


PHONEMES = {
    "M": "mmm", "S": "sss", "F": "fff", "A": "aaa (as in apple)", "T": "tuh",
    "B": "buh", "D": "duh", "P": "puh", "N": "nnn", "O": "ah (as in octopus)",
    "L": "lll", "R": "rrr", "K": "kuh", "G": "guh", "H": "huh",
    "I": "ih (as in igloo)", "E": "eh (as in egg)", "U": "uh (as in umbrella)",
    "J": "juh", "V": "vvv", "W": "wuh", "Z": "zzz",
}

def g_phonics(_):
    """A real letter-sound drill. The frontend speaks `say` and can speak each
    single-letter choice on tap, so a pre-reader can play it by ear."""
    letter = R.choice(list(PHONEMES))
    sound = PHONEMES[letter]
    wrong = R.sample([c for c in PHONEMES if c != letter], 3)
    q = _mc("Which letter makes the sound  “{}” ?".format(sound), letter, wrong, pad=False)
    q["say"] = "Which letter makes the sound {}?".format(sound)
    q["speak_choices"] = True
    return q

def g_patterns(_):
    step = R.choice([1, 2, 5, 10])
    start = R.randint(0, 5) * (1 if step == 1 else step)
    seq = [start + i * step for i in range(4)]
    nxt = seq[-1] + step
    q = _mc("What comes next?   {} , ___".format(" , ".join(map(str, seq))),
            nxt, _near_distractors(nxt, 3, lo=0),
            "The pattern counts up by {}.".format(step))
    q["say"] = "What comes next? {}".format(", ".join(map(str, seq)))
    q["speak_choices"] = True
    return q

def g_shapes(_):
    shapes = {"triangle": 3, "square": 4, "pentagon": 5, "hexagon": 6, "octagon": 8}
    name, sides = R.choice(list(shapes.items()))
    if R.random() < 0.5:
        q = _mc("How many sides does a {} have?".format(name), sides,
                # lo=1, not 3: a child's plausible wrong answers include one
                # and two, and refusing them left a triangle with nothing below
                # its own key, pinning it at rank 1 on every draw.
                _near_distractors(sides, 3, lo=1))
        q["say"] = "How many sides does a {} have?".format(name)
    else:
        wrong = R.sample([k for k in shapes if shapes[k] != sides], 3)
        q = _mc("Which shape has {} sides?".format(sides), name, wrong, pad=False)
        q["say"] = "Which shape has {} sides?".format(sides)
    q["speak_choices"] = True
    return q


# ---------------- Stage 1: Sprout ----------------

def _arith_tally(answer: int, story: str, say: str) -> Optional[Dict]:
    """An arithmetic answer COUNTED OUT rather than picked from a list.

    "Below stage 2 a learner should never have to type" was read for years as
    "below stage 2 every item is multiple choice", and the two are not the same
    sentence. The tally shape written for counting proves it: the objects are
    the answering surface, so nothing has to be read or typed, and what is
    scored is the act being taught. Addition and subtraction are the most
    drilled generators in the book and were pure recognition for the readers
    who most need to produce — a child who works out that five and two make
    seven, then picks 7 from a list, has been asked to recognise a numeral at
    the end of doing the real work.

    A committed tally is a plain number, so quiz.py grades it exactly as it
    grades a typed one and no new marking path exists.
    """
    if not (1 <= answer <= 9):
        return None            # the tokens must all fit one small screen
    thing, one, many = R.choice(TALLY_THINGS)
    return {
        "kind": "tally",
        "prompt": "{}\n\nTouch each {}, then press the button.".format(story, one),
        "items": [thing] * answer,
        "answer": str(answer),
        "say": say,
        "explain": "There are {} — one number word for each one you touched.".format(answer),
        "ephemeral": True,
        "gen": "arith-tally",
    }


def _arith(prompt: str, answer: int, say: str, level: int) -> Dict:
    """Below stage 2 a learner should never have to type: offer spoken choices."""
    if level > 1:
        return _num(prompt, answer)
    # The old delta pool was [-3,-2,-1,1,2,3,10] — four of seven above the key —
    # and the `cand >= 0` filter then dropped most of the rest, because at this
    # level the answers are small. So the distractors piled up above the key and
    # "always pick the second smallest" scored 49-56% across addition,
    # subtraction, division and times-tables against a 25% chance rate. These
    # are the most-drilled generators in the book, and the tell was invisible to
    # every audit the project had, all of which measured display order — which
    # _mc does shuffle, and which sorting undoes.
    q = _mc(prompt, answer, _near_distractors(answer, 3, lo=0), pad=False)
    q["say"] = say
    q["speak_choices"] = True
    return q

def g_addition(level):
    hi = 10 if level <= 1 else 100
    a, b = R.randint(1, hi), R.randint(1, hi)
    if (level or 0) <= 1 and R.random() < 0.5:
        # Draw a sum that can actually be counted out on one screen. Left to
        # the general 1-10 draw, four fifths of sums land above nine and fall
        # straight back to multiple choice — the produced form would exist and
        # almost never be reached. Small sums are the right material here
        # anyway: counting on from five is the skill, not adding to twenty.
        a = R.randint(1, 6)
        b = R.randint(1, 9 - a) if a < 9 else 1
        counted = _arith_tally(
            a + b,
            "{} and {} more.".format(a, b),
            "{} and {} more. How many altogether? Touch each one.".format(a, b))
        if counted:
            return counted
    return _arith("{} + {} = ?".format(a, b), a + b,
                  "What is {} plus {}?".format(a, b), level)

def g_subtraction(level):
    hi = 10 if level <= 1 else 100
    if level <= 1:
        # Draw the ANSWER first, then the operands that give it. Drawing two
        # numbers and subtracting makes small differences far commoner than
        # large ones (a difference of 0-2 came up three times as often as 7-9),
        # which is both worse practice — the child mostly meets the easiest
        # cases — and a surface tell: a key of 0, 1 or 2 has no room for three
        # plausible options BELOW it once negatives are excluded, so the key
        # sat at the bottom of the sorted list and "pick the smallest" beat
        # chance by ten points.
        # 1 to 9, not 0 to 9. A remainder of nought has no plausible option
        # BELOW it once negative numbers are off the table for a five-year-old
        # — and they are, deliberately — so every zero-answer card put the key
        # at the bottom of the sorted list. Ten per cent of cards doing that is
        # enough for "pick the smallest" to beat chance. The idea of a nought
        # remainder is not lost: from Sapling up the answer is typed, where a
        # distractor set does not arise.
        answer = R.randint(1, 9)
        b = R.randint(1, hi - answer)
        a = answer + b
    else:
        a, b = R.randint(1, hi), R.randint(1, hi)
        a, b = max(a, b), min(a, b)
    if (level or 0) <= 1 and R.random() < 0.5:
        # Operands drawn INSIDE the branch, so it always yields a countable
        # remainder. Testing the general draw instead only took the branch when
        # the remainder happened to fall in 1-9, which left the multiple-choice
        # half over-supplied with remainders of ZERO — and a key of nought can
        # have no plausible option below it, so the key sat at rank 1 and
        # "always pick the smallest" beat chance by 11pp. The produced form
        # must not bias the recognised one.
        a = R.randint(2, 9)
        b = R.randint(1, a - 1)
        counted = _arith_tally(
            a - b,
            "There were {}, and {} went away.".format(a, b),
            "There were {}, and {} went away. How many are left? Touch each one.".format(a, b))
        if counted:
            return counted
    return _arith("{} − {} = ?".format(a, b), a - b,
                  "What is {} take away {}?".format(a, b), level)

def g_times_tables(level=2):
    a, b = R.randint(2, 12), R.randint(2, 12)
    return _arith("{} × {} = ?".format(a, b), a * b,
                  "What is {} times {}?".format(a, b), level)

def g_division(level=2):
    b, q = R.randint(2, 12), R.randint(2, 12)
    return _arith("{} ÷ {} = ?".format(b * q, b), q,
                  "What is {} shared into {} equal groups?".format(b * q, b), level)

def g_place_value(_):
    n = R.randint(102, 9999)
    places = ["ones", "tens", "hundreds", "thousands"]
    digits = str(n)[::-1]
    i = R.randint(0, len(digits) - 1)
    return _mc("In the number {}, what digit is in the {} place?".format(n, places[i]),
               digits[i], R.sample([d for d in "0123456789" if d != digits[i]], 3))

SIGHT_WORDS = ["the", "and", "said", "have", "with", "they", "this", "from", "want",
               "little", "could", "there", "about", "would", "because", "friend",
               "before", "again", "always", "together"]

def g_spelling(level=0):
    """Spelling, asked as spelling about half the time.

    "Which spelling is correct? [ugain / aagin / again / agian]" is the inverse
    of the skill: it asks a child to RECOGNISE a misspelling, and it puts three
    wrong spellings of a word they are still learning in front of their eyes.
    Building the word from its own letters is the thing being taught, and the
    ordering surface — tap in sequence, fully spoken, no typing — already
    exists for exactly this kind of answer.

    The recognition form is kept as the minority case: telling a right spelling
    from a near-miss is its own real skill, it just should not be the whole of
    what "spelling" means to a five-year-old.
    """
    if (level or 0) <= 1 and R.random() < 0.5:
        # Short enough that every tile fits one row on a phone, and long enough
        # that the order is not obvious from two letters.
        buildable = [w for w in SIGHT_WORDS if 3 <= len(w) <= 6 and len(set(w)) == len(w)]
        if buildable:
            word = R.choice(buildable)
            return _order(
                "Put the letters in order to spell “{}”.".format(word),
                list(word),
                "Spell {}. Tap the letters in order.".format(word),
                "{} — one letter at a time, in that order.".format(word))
    # Prefer words long enough to misspell in several distinct ways; short
    # words (the/and) can only be scrambled one way, so we also mine other
    # sight words as plausible distractors and cap the search.
    word = R.choice([w for w in SIGHT_WORDS if len(w) >= 4] or SIGHT_WORDS)
    chars = list(word)
    wrongs = set()
    # All adjacent-swap misspellings.
    for i in range(len(chars) - 1):
        c = chars[:]
        c[i], c[i + 1] = c[i + 1], c[i]
        s = "".join(c)
        if s != word:
            wrongs.add(s)
    # Vowel-substitution misspellings, if still short.
    vowels = "aeiou"
    for i, ch in enumerate(word):
        if ch in vowels and len(wrongs) < 6:
            for v in vowels:
                if v != ch:
                    s = word[:i] + v + word[i + 1:]
                    if s != word:
                        wrongs.add(s)
    wrongs.discard(word)
    wrongs = list(wrongs)
    R.shuffle(wrongs)
    if len(wrongs) < 3:
        wrongs += [w for w in SIGHT_WORDS if w != word][:3]
    q = _mc("Which spelling is correct?", word, wrongs[:3], pad=False)
    q["say"] = 'Which spelling is correct for the word "{}"?'.format(word)
    q["speak_choices"] = True
    return q

VOCAB = [
    ("enormous", "very big"), ("fragile", "breaks easily"),
    ("ancient", "very old"), ("rapid", "very fast"), ("silent", "no sound"),
    ("brave", "not afraid"), ("curious", "wants to know"),
    ("gather", "bring together"), ("vanish", "disappear"),
    ("gleaming", "shining"), ("weary", "very tired"),
    ("murmur", "speak softly"), ("summit", "mountain top"),
    ("voyage", "long journey"), ("shelter", "a safe place"),
]

def g_vocabulary(_):
    word, meaning = R.choice(VOCAB)
    wrong = R.sample([m for w, m in VOCAB if w != word], 3)
    q = _mc('What does "{}" mean?'.format(word), meaning, wrong, pad=False)
    q["say"] = 'What does the word "{}" mean?'.format(word)
    q["speak_choices"] = True
    return q


# ---------------- Stage 2: Sapling ----------------

def g_fractions(_):
    mode = R.choice(["add", "compare", "simplify", "mult"])
    if mode == "add":
        d = R.choice([2, 3, 4, 5, 6, 8, 10, 12])
        a, b = R.randint(1, d - 1), R.randint(1, d - 1)
        ans = Fraction(a, d) + Fraction(b, d)
        return _num("{}/{} + {}/{} = ?  (answer like 3/4 or a whole number)".format(a, d, b, d),
                    ans if ans.denominator > 1 else ans.numerator,
                    "Add the numerators; simplify.")
    if mode == "compare":
        # Four *proper* fractions (numerator < denominator so none collapses to
        # a whole number), ask which is largest — a real 4-way choice.
        fracs = set()
        while len(fracs) < 4:
            den = R.randint(2, 12)
            num = R.randint(1, den - 1)
            fracs.add(Fraction(num, den))
        fracs = list(fracs)
        largest = max(fracs)
        labels = {f: "{}/{}".format(f.numerator, f.denominator) for f in fracs}
        return _mc("Which fraction is the largest?", labels[largest],
                   [labels[f] for f in fracs if f != largest],
                   "Give them a common denominator to compare.")
    if mode == "simplify":
        k = R.randint(2, 6)
        f = Fraction(R.randint(1, 9), R.randint(2, 10))
        return _num("Simplify: {}/{}".format(f.numerator * k, f.denominator * k),
                    f if f.denominator > 1 else f.numerator)
    f1 = Fraction(R.randint(1, 5), R.randint(2, 6))
    f2 = Fraction(R.randint(1, 5), R.randint(2, 6))
    ans = f1 * f2
    return _num("{} × {} = ?".format(f1, f2), ans if ans.denominator > 1 else ans.numerator,
                "Multiply tops together and bottoms together, then simplify.")

def g_decimals(_):
    a = round(R.uniform(0.1, 20), R.choice([1, 2]))
    b = round(R.uniform(0.1, 20), R.choice([1, 2]))
    if R.random() < 0.5:
        ans = round(a + b, 4)
        return _num("{} + {} = ?".format(a, b), int(ans) if ans == int(ans) else ans)
    big, small = max(a, b), min(a, b)
    ans = round(big - small, 4)
    return _num("{} − {} = ?".format(big, small), int(ans) if ans == int(ans) else ans)

def g_percent(_):
    p = R.choice([5, 10, 20, 25, 50, 75])
    n = R.choice([20, 40, 60, 80, 120, 200, 300])
    return _num("What is {}% of {}?".format(p, n), int(n * p / 100))

def g_negatives(_):
    a, b = R.randint(-15, 15), R.randint(-15, 15)
    op = R.choice(["+", "−"])
    ans = a + b if op == "+" else a - b
    return _num("({}) {} ({}) = ?".format(a, op, b), ans)

def g_order_of_ops(_):
    a, b, c = R.randint(2, 9), R.randint(2, 9), R.randint(2, 9)
    form = R.choice(["a+b*c", "(a+b)*c", "a*b-c"])
    if form == "a+b*c":
        expr, ans = "{} + {} × {}".format(a, b, c), a + b * c
    elif form == "(a+b)*c":
        expr, ans = "({} + {}) × {}".format(a, b, c), (a + b) * c
    else:
        expr, ans = "{} × {} − {}".format(a, b, c), a * b - c
    return _num(expr + " = ?", ans,
                "Multiply before adding unless parentheses say otherwise.")

_PRIMES_TO_60 = [n for n in range(2, 61)
                 if all(n % i for i in range(2, int(n ** 0.5) + 1))]
_COMPOSITES_TO_60 = [n for n in range(2, 61) if n not in set(_PRIMES_TO_60)]


def g_primes(_):
    # Drawing n first and asking whether it happens to be prime keys the item
    # "no" by construction: there are 17 primes below 60 and 42 composites, so
    # "always answer no" scored 71.7% against a 50% chance rate and passed 48%
    # of six-item drill papers outright. Choose the answer first, then a number
    # that has it, and the two keys come out even.
    is_prime = R.random() < 0.5
    n = R.choice(_PRIMES_TO_60 if is_prime else _COMPOSITES_TO_60)
    return _choice2("Is {} a prime number?".format(n), "yes" if is_prime else "no",
                    "no" if is_prime else "yes",
                    "A prime has exactly two divisors: 1 and itself.")

def g_area_perimeter(_):
    w, h = R.randint(2, 15), R.randint(2, 15)
    if R.random() < 0.5:
        return _num("A rectangle is {} wide and {} tall. What is its area?".format(w, h),
                    w * h, "Area = width × height.")
    return _num("A rectangle is {} wide and {} tall. What is its perimeter?".format(w, h),
                2 * (w + h), "Perimeter = 2 × (width + height).")

def g_ratios(_):
    a, b = R.randint(2, 9), R.randint(2, 9)
    k = R.randint(2, 6)
    return _num("If the ratio is {}:{} — when the first number is {}, what is the second?"
                .format(a, b, a * k), b * k)

def g_exponents(_):
    base = R.randint(2, 10)
    exp = R.randint(2, 3 if base > 5 else 4)
    return _num("{}^{} = ?".format(base, exp), base ** exp)


# ---------------- Stage 3: Tree ----------------

def g_linear_eq(_):
    x = R.randint(-9, 9)
    a = R.choice([2, 3, 4, 5, -2, -3])
    b = R.randint(-10, 10)
    c = a * x + b
    return _num("Solve for x:   {}x {} {} = {}".format(a, "+" if b >= 0 else "−", abs(b), c), x)

def g_quadratics(_):
    r1, r2 = R.randint(-6, 6), R.randint(-6, 6)
    b, c = -(r1 + r2), r1 * r2
    def term(coef, sym):
        if coef == 0:
            return ""
        sign = " + " if coef > 0 else " − "
        return "{}{}{}".format(sign, abs(coef) if abs(coef) != 1 or not sym else "", sym)
    expr = "x²" + term(b, "x") + term(c, "")
    roots = sorted({r1, r2})
    ans = ", ".join(map(str, roots))
    wrong = [", ".join(map(str, sorted({-r1, -r2}))),
             ", ".join(map(str, sorted({r1 + 1, r2 - 1}))),
             ", ".join(map(str, sorted({r1, r2 + 1})))]
    return _mc("The roots of  {} = 0  are:".format(expr), ans,
               [w for w in wrong if w != ans],
               "Factor: (x − {})(x − {}) = 0.".format(r1, r2))

def g_slope(_):
    x1, y1, x2 = R.randint(-5, 5), R.randint(-5, 5), R.randint(-5, 5)
    while True:
        x2 = R.randint(-5, 5)
        if x2 != x1:
            break
    m = R.choice([-3, -2, -1, 1, 2, 3])
    y2 = y1 + m * (x2 - x1)
    return _num("What is the slope of the line through ({}, {}) and ({}, {})?"
                .format(x1, y1, x2, y2), m, "slope = rise / run.")

def g_trig(_):
    table = {("sin", 0): 0, ("sin", 30): "1/2", ("sin", 90): 1,
             ("cos", 0): 1, ("cos", 60): "1/2", ("cos", 90): 0,
             ("tan", 0): 0, ("tan", 45): 1}
    (fn, deg), val = R.choice(list(table.items()))
    return _mc("{}({}°) = ?".format(fn, deg), val,
               [v for v in ["0", "1", "1/2", "√2/2", "√3/2"] if str(v) != str(val)][:3])

def g_logs(_):
    base = R.choice([2, 3, 10])
    exp = R.randint(1, 4 if base == 10 else 6)
    return _num("log base {} of {} = ?".format(base, base ** exp), exp)

# Keyed by the ANSWER, then a question that has it. Drawing the question first
# is what made "1/4" the answer 40% of the time (both the coin and the card
# branch keyed it) and then "1/2" 33% once those were varied: the key follows
# whatever the question list happens to contain. Draw the key uniformly and the
# imbalance cannot arise, whatever questions are added later.
PROBABILITY_QUESTIONS = {
    "1/6": ["A fair six-sided die is rolled. P(a six) = ?",
            "A fair six-sided die is rolled. P(number ≤ 1) = ?"],
    "1/3": ["A fair six-sided die is rolled. P(number ≤ 2) = ?",
            "A fair six-sided die is rolled. P(a multiple of 3) = ?"],
    "1/2": ["A fair six-sided die is rolled. P(number ≤ 3) = ?",
            "Two fair coins are flipped. P(exactly one head) = ?",
            "One card is drawn from a 52-card deck. P(a red card) = ?"],
    "2/3": ["A fair six-sided die is rolled. P(number ≤ 4) = ?"],
    "1/4": ["Two fair coins are flipped. P(both heads) = ?",
            "Two fair coins are flipped. P(no heads) = ?",
            "One card is drawn from a 52-card deck. P(a heart) = ?"],
    "3/4": ["Two fair coins are flipped. P(at least one head) = ?"],
    "1/13": ["One card is drawn from a 52-card deck. P(an ace) = ?"],
    "3/13": ["One card is drawn from a 52-card deck. P(a face card) = ?"],
}
_PROBABILITY_KEYS = sorted(PROBABILITY_QUESTIONS)


def g_probability(_):
    key = R.choice(_PROBABILITY_KEYS)
    prompt = R.choice(PROBABILITY_QUESTIONS[key])
    others = [k for k in _PROBABILITY_KEYS if k != key]
    R.shuffle(others)
    return _mc(prompt, key, others[:3], pad=False)


def g_stats(_):
    nums = sorted(R.sample(range(1, 30), 5))
    if R.random() < 0.5:
        total = sum(nums)
        if total % 5:
            nums[0] += 5 - total % 5
            nums.sort()
        return _num("Find the mean of: {}".format(", ".join(map(str, nums))),
                    sum(nums) // 5)
    return _num("Find the median of: {}".format(", ".join(map(str, nums))), nums[2])

def g_functions(_):
    a, b = R.randint(2, 5), R.randint(-6, 6)
    x = R.randint(-5, 5)
    kind = R.choice(["lin", "quad"])
    if kind == "lin":
        return _num("If f(x) = {}x {} {}, what is f({})?".format(
            a, "+" if b >= 0 else "−", abs(b), x), a * x + b)
    return _num("If f(x) = x² {} {}, what is f({})?".format(
        "+" if b >= 0 else "−", abs(b), x), x * x + b)


# ---------------- Stage 4: Grove ----------------

def g_derivatives(_):
    mode = R.choice(["power", "trig", "exp", "chain"])
    if mode == "power":
        n = R.randint(2, 7)
        c = R.randint(2, 6)
        return _mc("d/dx of  {}x^{}  = ?".format(c, n), "{}x^{}".format(c * n, n - 1),
                   ["{}x^{}".format(c * n, n), "{}x^{}".format(c, n - 1),
                    "{}x^{}".format(c * (n - 1), n)])
    if mode == "trig":
        pair = R.choice([("sin x", "cos x"), ("cos x", "−sin x"), ("tan x", "sec² x")])
        return _mc("d/dx of  {}  = ?".format(pair[0]), pair[1],
                   [p for p in ["cos x", "−sin x", "sec² x", "sin x", "−cos x"]
                    if p != pair[1]][:3])
    if mode == "exp":
        pair = R.choice([("e^x", "e^x"), ("ln x", "1/x"), ("e^(2x)", "2e^(2x)")])
        return _mc("d/dx of  {}  = ?".format(pair[0]), pair[1],
                   [p for p in ["e^x", "1/x", "x·e^(x−1)", "2e^(2x)", "ln x"]
                    if p != pair[1]][:3])
    k = R.randint(2, 5)
    return _mc("d/dx of  sin({}x)  = ?".format(k), "{}cos({}x)".format(k, k),
               ["cos({}x)".format(k), "−{}cos({}x)".format(k, k), "{}sin({}x)".format(k, k)])

def g_integrals(_):
    mode = R.choice(["power", "trig", "exp"])
    if mode == "power":
        n = R.randint(1, 6)
        return _mc("∫ x^{} dx  = ?".format(n), "x^{}/{} + C".format(n + 1, n + 1),
                   ["x^{}/{} + C".format(n, n), "{}x^{} + C".format(n, n - 1),
                    "x^{} + C".format(n + 1)])
    if mode == "trig":
        pair = R.choice([("cos x", "sin x + C"), ("sin x", "−cos x + C")])
        return _mc("∫ {} dx  = ?".format(pair[0]), pair[1],
                   [p for p in ["sin x + C", "−cos x + C", "cos x + C", "−sin x + C"]
                    if p != pair[1]][:3])
    return _mc("∫ e^x dx  = ?", "e^x + C", ["x·e^x + C", "e^(x+1)/(x+1) + C", "ln x + C"])

def g_limits(_):
    mode = R.choice(["poly", "ratio", "sinx"])
    if mode == "poly":
        a, c = R.randint(1, 4), R.randint(-5, 5)
        x0 = R.randint(-3, 3)
        return _num("lim (x→{}) of  {}x² {} {}  = ?".format(
            x0, a, "+" if c >= 0 else "−", abs(c)), a * x0 * x0 + c)
    if mode == "sinx":
        # One hard-coded item whose key was both fixed at "1" and the shortest
        # string on the card, so "pick the shortest" beat chance by 11pp.
        k = R.randint(1, 4)
        expr, key = R.choice([
            ("sin({}x)/x".format(k), str(k)),
            ("sin(x)/({}x)".format(k), "1/{}".format(k)),
            ("(1 − cos(x))/x", "0"),
            ("tan({}x)/x".format(k), str(k)),
        ])
        pool = [str(k), "1/{}".format(k), "0", "∞", str(k + 1), "1"]
        return _mc("lim (x→0) of  {}  = ?".format(expr), key,
                   [c for c in pool if c != key][:3], pad=False)
    r = R.randint(1, 5)
    return _num("lim (x→{r}) of  (x² − {r2}) / (x − {r})  = ?".format(r=r, r2=r * r),
                2 * r, "Factor the numerator as (x−{r})(x+{r}).".format(r=r))

def g_matrices(_):
    a, b, c, d = [R.randint(-5, 5) for _ in range(4)]
    if R.random() < 0.5:
        return _num("Determinant of [[{}, {}], [{}, {}]] = ?".format(a, b, c, d),
                    a * d - b * c, "ad − bc.")
    e, f, g, h = [R.randint(-3, 3) for _ in range(4)]
    top_left = a * e + b * g
    return _num("If M = [[{}, {}], [{}, {}]] × [[{}, {}], [{}, {}]], what is M[1][1] "
                "(top-left entry)?".format(a, b, c, d, e, f, g, h), top_left)

def g_vectors(_):
    v = [R.randint(-5, 5) for _ in range(3)]
    w = [R.randint(-5, 5) for _ in range(3)]
    return _num("Dot product of ({}, {}, {}) and ({}, {}, {}) = ?".format(*v, *w),
                sum(x * y for x, y in zip(v, w)))

def g_combinatorics(_):
    n = R.randint(4, 9)
    k = R.randint(2, n - 1)
    return _num("How many ways can you choose {} items from {} (order doesn't matter)?"
                .format(k, n), math.comb(n, k), "n choose k = n!/(k!(n−k)!).")

def g_complex(_):
    a, b, c, d = [R.randint(-4, 4) for _ in range(4)]
    real, imag = a * c - b * d, a * d + b * c
    ans = "{}{}{}i".format(real, "+" if imag >= 0 else "−", abs(imag))
    wrong = ["{}{}{}i".format(a * c, "+" if b * d >= 0 else "−", abs(b * d)),
             "{}{}{}i".format(real + 1, "+" if imag >= 0 else "−", abs(imag)),
             "{}{}{}i".format(real, "+" if imag + 1 >= 0 else "−", abs(imag + 1))]
    return _mc("({}{}{}i) × ({}{}{}i) = ?".format(
        a, "+" if b >= 0 else "−", abs(b), c, "+" if d >= 0 else "−", abs(d)),
        ans, [w for w in wrong if w != ans], "Use i² = −1.")

def g_bigo(_):
    pairs = [("binary search", "O(log n)"), ("linear scan of a list", "O(n)"),
             ("bubble sort (worst case)", "O(n²)"), ("merge sort", "O(n log n)"),
             ("hash-table lookup (average)", "O(1)"),
             ("nested loops over n items", "O(n²)"),
             ("visiting every node of a balanced tree", "O(n)")]
    task, ans = R.choice(pairs)
    return _mc("Time complexity of {}: ?".format(task), ans,
               list({o for _, o in pairs if o != ans})[:3], pad=False)


# ---------------- Science & computing (stages 2–4) ----------------

def g_kinematics(_):
    mode = R.choice(["dist", "speed", "vfinal"])
    if mode == "dist":
        v, t = R.randint(2, 30), R.randint(2, 12)
        return _num("A car travels at {} m/s for {} s. How far does it go (metres)?"
                    .format(v, t), v * t, "distance = speed × time.")
    if mode == "speed":
        d, t = R.randint(20, 300), R.randint(2, 10)
        d = (d // t) * t  # keep it whole
        return _num("An object covers {} m in {} s. What is its speed (m/s)?"
                    .format(d, t), d // t, "speed = distance ÷ time.")
    u, a, t = R.randint(0, 10), R.randint(1, 5), R.randint(1, 6)
    return _num("Starting at {} m/s and accelerating {} m/s² for {} s, "
                "what is the final speed (m/s)?".format(u, a, t), u + a * t,
                "v = u + a·t.")

def g_units(_):
    pairs = [("m", "cm", 100), ("km", "m", 1000), ("kg", "g", 1000),
             ("L", "mL", 1000), ("m", "mm", 1000), ("hour", "minutes", 60)]
    big, small, factor = R.choice(pairs)
    n = R.randint(2, 9)
    return _num("{} {} = ? {}".format(n, big, small), n * factor,
                "1 {} = {} {}.".format(big, factor, small))

def g_ohms(_):
    mode = R.choice(["v", "i", "r"])
    i, r = R.randint(1, 9), R.randint(1, 12)
    if mode == "v":
        return _num("A current of {} A flows through {} Ω. What is the voltage (V)?"
                    .format(i, r), i * r, "V = I × R.")
    if mode == "i":
        v = i * r
        return _num("{} V is applied across {} Ω. What is the current (A)?"
                    .format(v, r), v // r if v % r == 0 else round(v / r, 2), "I = V ÷ R.")
    v = i * r
    return _num("{} V drives {} A. What is the resistance (Ω)?".format(v, i),
                v // i if v % i == 0 else round(v / i, 2), "R = V ÷ I.")

ATOMS = [("Hydrogen", 1), ("Helium", 2), ("Carbon", 6), ("Nitrogen", 7),
         ("Oxygen", 8), ("Sodium", 11), ("Chlorine", 17), ("Iron", 26), ("Gold", 79)]

def g_atoms(_):
    name, z = R.choice(ATOMS)
    mode = R.choice(["protons", "electrons"])
    prop = "protons" if mode == "protons" else "electrons (when neutral)"
    return _num("How many {} does a {} atom have?".format(prop, name), z,
                "The atomic number of {} is {}.".format(name, z))

MOLAR = {"H": 1, "C": 12, "N": 14, "O": 16, "Na": 23, "S": 32, "Cl": 35}

def g_molar_mass(_):
    mols = [("H2O", [("H", 2), ("O", 1)]), ("CO2", [("C", 1), ("O", 2)]),
            ("NaCl", [("Na", 1), ("Cl", 1)]), ("CH4", [("C", 1), ("H", 4)]),
            ("O2", [("O", 2)]), ("NH3", [("N", 1), ("H", 3)])]
    formula, parts = R.choice(mols)
    mass = sum(MOLAR[e] * k for e, k in parts)
    return _num("Approximate molar mass of {} (g/mol)?".format(formula), mass,
                "Add the atomic masses: " +
                " + ".join("{}×{}".format(k, MOLAR[e]) for e, k in parts) + ".")

# Grouped by answer, not listed flat. The flat list held three acids, three
# bases and one neutral, so drawing an ITEM at random keyed "acid" or "base"
# 43% of the time each against a 33% chance rate. Draw the answer first, then
# something that has it.
PH_ITEMS = {
    "acid": ["lemon juice", "vinegar", "battery acid", "orange juice", "black coffee"],
    "base": ["soap", "baking soda solution", "bleach", "oven cleaner", "milk of magnesia"],
    "neutral": ["pure water", "table salt solution", "blood plasma", "milk"],
}


def g_ph(_):
    kind = R.choice(list(PH_ITEMS))
    thing = R.choice(PH_ITEMS[kind])
    return _mc("Is {} an acid, a base, or neutral?".format(thing), kind,
               [k for k in PH_ITEMS if k != kind], pad=False)

def g_binary(_):
    if R.random() < 0.5:
        n = R.randint(1, 31)
        return _num("Write the number {} in binary (base 2).".format(n),
                    format(n, "b"), "Sum of powers of two.")
    n = R.randint(1, 31)
    b = format(n, "b")
    return _num("What decimal number is binary {}?".format(b), n,
                "Each place is a power of two.")

def g_logic_gates(_):
    a, b = R.randint(0, 1), R.randint(0, 1)
    gate = R.choice(["AND", "OR", "XOR", "NAND"])
    res = {"AND": a & b, "OR": a | b, "XOR": a ^ b, "NAND": 1 - (a & b)}[gate]
    return _choice2("{} gate: input {} and {} → output?".format(gate, a, b),
                    res, 1 - res, "Recall the truth table for {}.".format(gate))


# ---------------- Knowledge drills for the young nodes ----------------
#
# Seventy-five of the eighty-nine stage 0-1 nodes had no practice generator at
# all. Not because nobody had got to them, but because the generators here are
# procedural — they compute an answer — and "Which one is a mammal?" has no
# arithmetic to compute. So the youngest half of the book, the half whose
# reader most needs to meet a thing more than once, had a read step and a quiz
# and nothing in between: the interactive loop could not close on a node with
# nothing to practise.
#
# The material a knowledge drill needs is authored (data/practice/young.json);
# the *drill* is procedural, and that is the split that makes this worth
# building rather than writing four thousand more bank items. One node's entry
# supplies groups, pairs, sequences and facts; this code mints an unbounded
# stream of items out of them — category picks and their negatives, matches
# either way round, orderings the child produces rather than recognises.
#
# Every item is fully spoken and fully tappable: nothing here asks a
# five-year-old to read or type.

_YOUNG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "data", "practice", "young.json")
_YOUNG_CACHE: Optional[Dict[str, Dict]] = None


def young_material() -> Dict[str, Dict]:
    """The authored material behind the knowledge drills, loaded once."""
    global _YOUNG_CACHE
    if _YOUNG_CACHE is None:
        try:
            with open(_YOUNG_PATH, encoding="utf-8") as fh:
                _YOUNG_CACHE = json.load(fh)
        except (OSError, ValueError):
            # A missing or broken file must not take the book down: the node
            # keeps its authored bank and simply offers no drill.
            _YOUNG_CACHE = {}
    return _YOUNG_CACHE


def _length_balanced(key: str, pool: List[str], k: int = 3) -> List[str]:
    """Pick k distractors whose lengths straddle the key's.

    Picking at random from a pool leaves length readable: "Which one is a
    mammal?" against {bat, hippopotamus, wren} tells a non-reader nothing, but
    tells a reader plenty when the key is reliably the long one. So the draw
    takes one shorter, one longer, and one nearest, and falls back to random
    only when the pool has no such member.
    """
    pool = [p for p in dict.fromkeys(pool) if p != key]
    if len(pool) <= k:
        return pool
    n = len(key)
    shorter = sorted([p for p in pool if len(p) < n], key=lambda p: n - len(p))
    longer = sorted([p for p in pool if len(p) > n], key=lambda p: len(p) - n)
    nearest = sorted(pool, key=lambda p: abs(len(p) - n))
    out: List[str] = []
    # Round-robin, one from each bucket in turn. Draining the "shorter" bucket
    # first — which an in-order loop does — puts the key at the long end of
    # every card it can, and that is exactly the tell being guarded against.
    buckets = [longer, shorter, nearest, pool]
    idx = [0, 0, 0, 0]
    guard = 0
    while len(out) < k and guard < 200:
        guard += 1
        for b, bucket in enumerate(buckets):
            while idx[b] < len(bucket) and bucket[idx[b]] in out:
                idx[b] += 1
            if idx[b] < len(bucket) and len(out) < k:
                out.append(bucket[idx[b]])
                idx[b] += 1
    return out[:k]


def _know_group(spec: Dict) -> Optional[Dict]:
    groups = spec.get("groups") or {}
    names = [g for g, members in groups.items() if len(members) >= 1]
    if len(names) < 2:
        return None
    cat = R.choice(names)
    others = [m for g, ms in groups.items() if g != cat for m in ms]
    if len(others) < 3:
        return None
    not_prompt = spec.get("group_not_prompt")
    # As with pairs: the negative is asked only where its own wording was
    # written. "Which one would you measure with a scale?" does not negate into
    # "Which one is NOT a scale?" by rule.
    if not_prompt and len(groups[cat]) >= 3 and R.random() < 0.3:
        key = R.choice(others)
        prompt = not_prompt.format(cat)
        q = _mc(prompt, key, _length_balanced(key, groups[cat]), pad=False)
    else:
        key = R.choice(groups[cat])
        prompt = spec.get("group_prompt", "Which one is a {}?").format(cat)
        q = _mc(prompt, key, _length_balanced(key, others), pad=False)
    q["say"] = prompt
    q["speak_choices"] = True
    return q


def _know_pair(spec: Dict) -> Optional[Dict]:
    pairs = [p for p in (spec.get("pairs") or []) if len(p) == 2]
    if len(pairs) < 4:
        return None
    left, right = R.choice(pairs)
    back = spec.get("pair_back_prompt")
    # The reverse direction is only asked when it has been authored. Running a
    # forward template backwards produced "How many are in one 7 days?" — the
    # sentence a template cannot survive being read from the wrong end.
    if back and R.random() < 0.5:
        prompt = back.format(right)
        key, pool = left, [a for a, b in pairs if a != left]
    else:
        prompt = spec.get("pair_prompt", "What goes with {}?").format(left)
        key, pool = right, [b for a, b in pairs if b != right]
    q = _mc(prompt, key, _length_balanced(key, pool), pad=False)
    q["say"] = prompt
    q["speak_choices"] = True
    return q


def _know_fact(spec: Dict) -> Optional[Dict]:
    facts = [f for f in (spec.get("facts") or []) if len(f.get("d") or []) >= 3]
    if not facts:
        return None
    f = R.choice(facts)
    q = _mc(f["q"], f["a"], _length_balanced(str(f["a"]), list(f["d"])),
            f.get("explain", ""), pad=False)
    q["say"] = f.get("say", f["q"])
    q["speak_choices"] = True
    return q


def _know_order(spec: Dict) -> Optional[Dict]:
    seqs = [s for s in (spec.get("sequences") or []) if len(s) >= 3]
    if not seqs:
        return None
    seq = R.choice(seqs)
    prompt = spec.get("sequence_prompt", "Put them in the right order")
    return _order(prompt, [str(x) for x in seq],
                  spec.get("sequence_say", "Tap them in the right order."),
                  spec.get("sequence_explain", ""))


def make_knowledge_generator(node_id: str) -> Callable:
    """One drill over one node's authored material.

    Production is not an afterthought here. On a young paper an ordering item
    — tap these in the order they happen — is the only shape that asks the
    child to *make* the answer rather than spot it, so it is drawn first
    whenever the node has a sequence to order.
    """
    turn = {"n": 0}

    def gen(level=0):
        spec = young_material().get(node_id) or {}
        # The SHAPE rotates; only the content is drawn. Sampling the shape too
        # meant a four-item drill could come out all ordering, and whether that
        # drill was worth a review card then depended on the draw — the exact
        # coin-flip that `is_durable_item` exists to have stopped. Rotating
        # also guarantees what sampling only made likely: every drill of four
        # asks the child to produce something, and asks for recall as well.
        turn["n"] += 1
        i = turn["n"]
        recall = [_know_group, _know_pair, _know_fact]
        order_first = i % 4 == 0
        shapes = ([_know_order] if order_first else []) + \
            recall[i % 3:] + recall[:i % 3] + \
            ([] if order_first else [_know_order])
        for shape in shapes:
            q = shape(spec)
            if q is not None:
                return q
        # Nothing authored for this node yet: say so rather than mint noise.
        return None
    gen.__name__ = "g_know_%s" % node_id.replace(".", "_").replace("-", "_")
    return gen


GENERATORS: Dict[str, Callable] = {
    "counting": g_counting, "count-tally": g_count_tally,
    "letters": g_letters, "phonics": g_phonics,
    "order-numbers": g_order_numbers, "order-letters": g_order_letters,
    "order-lifecycle": g_order_lifecycle, "order-time": g_order_time,
    "compare": g_compare, "patterns": g_patterns, "shapes": g_shapes,
    "addition": g_addition, "subtraction": g_subtraction,
    "times-tables": g_times_tables, "division": g_division,
    "place-value": g_place_value, "spelling": g_spelling, "vocabulary": g_vocabulary,
    "fractions": g_fractions, "decimals": g_decimals, "percent": g_percent,
    "negatives": g_negatives, "order-of-ops": g_order_of_ops, "primes": g_primes,
    "area-perimeter": g_area_perimeter, "ratios": g_ratios, "exponents": g_exponents,
    "linear-equations": g_linear_eq, "quadratics": g_quadratics, "slope": g_slope,
    "trig": g_trig, "logs": g_logs, "probability": g_probability, "stats": g_stats,
    "functions": g_functions,
    "derivatives": g_derivatives, "integrals": g_integrals, "limits": g_limits,
    "matrices": g_matrices, "vectors": g_vectors, "combinatorics": g_combinatorics,
    "complex-numbers": g_complex, "big-o": g_bigo,
    # science & computing
    "kinematics": g_kinematics, "units": g_units, "ohms-law": g_ohms,
    "atoms": g_atoms, "molar-mass": g_molar_mass, "ph": g_ph,
    "binary": g_binary, "logic-gates": g_logic_gates,
}

# One drill per node that has authored material. Registered at import so
# `list_generators()` — and therefore tools/check_generators.py — sees them
# exactly like the procedural ones, and they are audited on the same terms.
for _node_id in sorted(young_material()):
    GENERATORS["know:" + _node_id] = make_knowledge_generator(_node_id)


def generate_set(gen_key: str, n: int = 6, level: int = 1) -> List[Dict]:
    fn = GENERATORS.get(gen_key)
    if fn is None:
        return []
    out, guard = [], 0
    seen = set()
    while len(out) < n and guard < n * 12:
        guard += 1
        q = fn(level)
        if q is None:      # a knowledge drill with no material for this node
            break
        # Key on prompt+answer: some generators deliberately reuse one prompt
        # (e.g. "Which spelling is correct?") so the child must listen.
        key = (q["prompt"], q.get("answer"))
        if key not in seen:
            seen.add(key)
            q["id"] = len(out)
            # Where this item came from, so a card minted later can ask the
            # generator what kind of thing it is instead of reading its text.
            q["gen"] = gen_key
            q["level"] = level
            out.append(q)
    return out


# Which drills ask the reader to RECALL something, and which ask them to WORK
# something out. Only the first kind is worth a permanent review card: a card
# is a thing you meet again and answer from memory, so "How many sides does a
# hexagon have?" belongs on one and "Dot product of (4, 2, -1) and (2, 3, -4)"
# does not — that is a calculation to perform, and filing one instance of it
# away forever teaches nothing.
#
# This is a declaration, not an inference, and that is the point. It replaced a
# classifier that sampled each generator and called a prompt durable if it
# recurred with a stable answer. That measured something real, but it settled a
# permanent property of an item by drawing samples, so the same prompt came out
# durable on one run and ephemeral on the next — identical items landing 2-in-8
# to 5-in-8 across re-samples, and one generator declaring 155 durable prompts
# on one pass and 167 on another. Card-worthiness is a fact about what a drill
# IS. It belongs written down once, where it can be read and argued with, not
# re-derived by coin flip on every process start.
#
# Every node carrying a practice generator also carries an authored bank
# (checked: no node depends on a generator alone), so a drill declared
# ephemeral here still leaves that node a source of cards for its errors.
DURABLE_GENERATORS = frozenset({
    "atoms",          # proton/electron count for a named element
    "big-o",          # complexity of a named algorithm
    "letters",        # which word starts with a given letter
    "logic-gates",    # truth tables
    "logs",           # log base 10 of a power of ten
    "molar-mass",     # molar mass of a named compound
    "ph",             # acid / base / neutral for a named substance
    "phonics",        # letter-sound correspondences
    "primes",         # primality of a small number
    "probability",    # the classic fixed set-ups
    "shapes",         # sides of a named shape
    "trig",           # exact values at the standard angles
    "units",          # the conversion factor is the thing being recalled
    "vocabulary",     # word meanings
})


def is_durable_item(gen_key: str, level: int, prompt: str) -> bool:
    """True when this generated item names a fact worth a review card.

    Deterministic by construction: the same item is judged the same way in
    every process, on every run.
    """
    if gen_key.startswith("know:"):
        # A knowledge drill asks for a fact about the world, and a fact is
        # exactly what a review card is for. Its order items are excluded
        # upstream by kind, where every generator's are.
        return True
    return gen_key in DURABLE_GENERATORS


def list_generators() -> List[str]:
    return sorted(GENERATORS.keys())
