"""Procedural practice generators — infinite exercises, no two sessions alike.

Each generator returns question dicts:
  {kind: 'choice'|'numeric'|'text', prompt, choices?, answer, explain?}
Generators are keyed; curriculum nodes reference them by key. Levels run from
preschool counting to undergraduate calculus and linear algebra.
"""

import math
import random
from fractions import Fraction
from typing import Callable, Dict, List

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
        while len(choices) < 4:
            cand = str(R.randint(1, 99))
            if cand not in seen:
                seen.add(cand)
                choices.append(cand)
    choices = choices[:4]
    R.shuffle(choices)
    return {"kind": "choice", "prompt": prompt, "choices": choices,
            "answer": str(answer), "explain": explain, "ephemeral": True}


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

def g_counting(_):
    n = R.randint(1, 10)
    thing = R.choice(COUNT_THINGS)
    q = _mc("How many do you see?\n\n" + (thing + " ") * n, n,
            [max(1, n - 1), n + 1, max(1, n - 2)])
    q["say"] = "How many do you see? Count them out loud."
    q["speak_choices"] = True
    return q

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
            nxt, [nxt - step, nxt + step, nxt + 1],
            "The pattern counts up by {}.".format(step))
    q["say"] = "What comes next? {}".format(", ".join(map(str, seq)))
    q["speak_choices"] = True
    return q

def g_shapes(_):
    shapes = {"triangle": 3, "square": 4, "pentagon": 5, "hexagon": 6, "octagon": 8}
    name, sides = R.choice(list(shapes.items()))
    if R.random() < 0.5:
        q = _mc("How many sides does a {} have?".format(name), sides,
                [sides - 1, sides + 1, sides + 2])
        q["say"] = "How many sides does a {} have?".format(name)
    else:
        wrong = R.sample([k for k in shapes if shapes[k] != sides], 3)
        q = _mc("Which shape has {} sides?".format(sides), name, wrong, pad=False)
        q["say"] = "Which shape has {} sides?".format(sides)
    q["speak_choices"] = True
    return q


# ---------------- Stage 1: Sprout ----------------

def _arith(prompt: str, answer: int, say: str, level: int) -> Dict:
    """Below stage 2 a learner should never have to type: offer spoken choices."""
    if level > 1:
        return _num(prompt, answer)
    wrong = set()
    while len(wrong) < 3:
        d = R.choice([-3, -2, -1, 1, 2, 3, 10])
        cand = answer + d
        if cand >= 0 and cand != answer:
            wrong.add(cand)
    q = _mc(prompt, answer, sorted(wrong), pad=False)
    q["say"] = say
    q["speak_choices"] = True
    return q

def g_addition(level):
    hi = 10 if level <= 1 else 100
    a, b = R.randint(1, hi), R.randint(1, hi)
    return _arith("{} + {} = ?".format(a, b), a + b,
                  "What is {} plus {}?".format(a, b), level)

def g_subtraction(level):
    hi = 10 if level <= 1 else 100
    a, b = R.randint(1, hi), R.randint(1, hi)
    a, b = max(a, b), min(a, b)
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

def g_spelling(_):
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

def g_primes(_):
    n = R.randint(2, 60)
    is_prime = n > 1 and all(n % i for i in range(2, int(n ** 0.5) + 1))
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

def g_probability(_):
    mode = R.choice(["die", "cards", "coins"])
    if mode == "die":
        k = R.choice([1, 2, 3])
        return _mc("A fair six-sided die is rolled. P(number ≤ {}) = ?".format(k),
                   "{}/6".format(k) if k not in (2, 3) else {2: "1/3", 3: "1/2"}[k],
                   ["1/6", "1/2", "1/3", "2/3"])
    if mode == "coins":
        return _mc("Two fair coins are flipped. P(both heads) = ?", "1/4",
                   ["1/2", "1/3", "3/4"])
    return _mc("One card is drawn from a 52-card deck. P(a heart) = ?", "1/4",
               ["1/13", "1/2", "4/13"])

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
        return _mc("lim (x→0) of  sin(x)/x  = ?", "1", ["0", "∞", "does not exist"])
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

def g_ph(_):
    items = [("lemon juice", "acid"), ("soap", "base"), ("pure water", "neutral"),
             ("vinegar", "acid"), ("baking soda solution", "base"),
             ("battery acid", "acid"), ("bleach", "base")]
    thing, kind = R.choice(items)
    return _mc("Is {} an acid, a base, or neutral?".format(thing), kind,
               [k for k in ["acid", "base", "neutral"] if k != kind], pad=False)

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


GENERATORS: Dict[str, Callable] = {
    "counting": g_counting, "letters": g_letters, "phonics": g_phonics,
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


def generate_set(gen_key: str, n: int = 6, level: int = 1) -> List[Dict]:
    fn = GENERATORS.get(gen_key)
    if fn is None:
        return []
    out, guard = [], 0
    seen = set()
    while len(out) < n and guard < n * 12:
        guard += 1
        q = fn(level)
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
    return gen_key in DURABLE_GENERATORS


def list_generators() -> List[str]:
    return sorted(GENERATORS.keys())
