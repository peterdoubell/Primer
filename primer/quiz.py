"""Quiz engine: turns any encyclopedia article into a comprehension check.

Two sources of questions:
1. Authored banks on curriculum nodes (highest quality, written into the
   curriculum data — application/transfer items, especially at higher stages).
2. Auto-generated cloze questions from article text — pick *self-contained*,
   informative sentences, blank out a key term or number, and offer distractors
   drawn from the same article that match the answer in case and rough length.

The board flagged the original generator for LaTeX junk ("displaystyle"),
context-dependent sentences ("This is another example of ___"), arbitrary
worked-example numbers, and mismatched distractors. All are filtered here.
"""

import random
import re
from typing import Dict, List, Optional

R = random.Random()

STOPWORDS = set(
    """the a an and or but if then than that this those these is are was were be
    been being have has had do does did will would can could may might shall
    should must of in on at to from by with without for as it its it's he she
    they them his her their there here when where which who whom whose what why
    how not no nor so such very also into over under between among after before
    during about above below out up down off again further once more most other
    some any each few both all only own same too s t don now""".split()
)

# Sentences opening with these are context-dependent — they refer back to
# something we've stripped away, so they make bad standalone questions.
REFERENT_START = re.compile(
    r"^\s*(this|that|these|those|it|they|he|she|him|her|them|here|there|"
    r"such|its|their|his|hers|then|thus|hence|therefore|however|moreover|"
    r"for example|for instance|in addition|as a result|both|either|neither|"
    r"instead|in contrast|furthermore|similarly|conversely|likewise|also|finally|"
    r"later|even if|the same|because of this|as such|by contrast|"
    r"on the other hand|a second|the theorem)\b",
    re.IGNORECASE,
)
# Back-references anywhere in the sentence also make it unanswerable alone
# ("…follows these precursors", "…the term is used").
REFERENT_ANY = re.compile(
    r"\b(these|those|the term|the former|the latter|as (?:noted|described|mentioned) above|"
    r"the following|as follows|aforementioned|said (?:process|method|system)|"
    # "this algorithm", "that process" — a pointer to something we cut away
    r"(?:this|that|these|those)\s+[a-z]{3,}|"
    r"the\s+(?:number|models?|term|algorithm|process|idea|equation|figure|table|result)\b|"
    r"here is|see\s+§|the most important ones|"
    r"\b(?:it|they|their|its|he|she|his|her|them)\s+"
    r"(?:is|are|was|were|has|have|had|can|could|will|would|may|might|do|does|did)|"
    r"\b(?:this|that|these|those)\b)",
    re.IGNORECASE,
)
# Abstract connective words make terrible cloze keys — blanking them tests
# nothing about the subject.
WEAK_KEYS = set(
    """particularly generally typically usually often sometimes however therefore
    moreover furthermore additionally specific specifically theoretical practical
    various several certain particular different similar related relationship
    important significant possible available following previous approximately
    including includes included example examples known called named considered
    described defined referred regarded consists consisting according
    respectively essentially primarily mainly largely commonly widely
    characterized believed invented developed compared fields materials
    development together representing containing involving providing
    resulting forming causing making using taking giving showing
    longer shorter difficult historically simply merely rather quite""".split()
)
# Worked-example scaffolding — arbitrary and unanswerable out of context.
EXAMPLE_MARKER = re.compile(
    r"(?:\be\.g\.|\bi\.e\.|\b(?:example|suppose|let\s|for instance|imagine|"
    r"say that|consider|Alice|Bob|Carol|Tom|Sally|John Doe)\b)", re.IGNORECASE)


def _clean_text(text: str) -> str:
    # Strip LaTeX/MathML residue and template noise that leaks from articles.
    text = re.sub(r"\{\\displaystyle[^}]*\}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    text = re.sub(r"[{}\\]", " ", text)
    text = text.replace("displaystyle", " ")
    # Invisible math operators and formatting marks that survive HTML stripping.
    text = re.sub(r"[⁡-⁤​-‏  ﻿]", " ", text)
    text = re.sub(r"\[\d+\]", "", text)          # footnote markers
    # MathML alt-text often repeats a token ("Opposite Opposite"); collapse it.
    text = re.sub(r"\b(\w{3,})(\s+\1\b)+", r"\1", text)
    # Navigation furniture that survives HTML stripping.
    text = re.sub(r"\b(Related pages|See also|References|External links|"
                  r"Further reading|Notes|Citations|Bibliography)\b", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _sentences(text: str) -> List[str]:
    text = _clean_text(text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9“\"'])", text)
    good = []
    for p in parts:
        p = p.strip()
        if not (40 <= len(p) <= 240):
            continue
        if REFERENT_START.search(p) or REFERENT_ANY.search(p):
            continue
        if EXAMPLE_MARKER.search(p):
            continue
        if p.count("(") != p.count(")"):
            continue
        if ":" in p:                 # list fragments and section run-ons
            continue
        # Added after a hand audit put the cloze defect rate at 65%: the
        # remaining bad items were dominated by run-on clauses (semicolons),
        # comma-heavy list fragments, quoted speech torn from its speaker,
        # and copula-free noun piles with nothing assertable to blank.
        if ";" in p or p.count(",") >= 4:
            continue
        if p.count('"') + p.count("“") + p.count("”") > 0:
            continue
        if not re.search(
                r"\b(is|are|was|were|has|have|had|can|could|will|would|may|"
                r"means|uses|used|makes|made|became|become|becomes|contains?|"
                r"consists?|forms?|formed|produces?|produced|calls?|called|"
                r"causes?|caused|allows?|allowed|gives?|gave|takes?|took|"
                r"holds?|held|shows?|showed|occurs?|occurred|includes?|"
                r"describes?|described|creates?|created|led|leads?)\b",
                p, re.IGNORECASE):
            continue             # no assertion, nothing worth blanking
        good.append(p)
    return good


def _lemma(word: str) -> str:
    """Crude stem so inflections of a weak key are caught too."""
    w = word.lower()
    for suf in ("ationally", "ically", "ingly", "ation", "ally", "ing", "ely", "ly", "es", "ed", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def _keywords(sentence: str, topic_terms: Optional[set] = None) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z'-]{3,}", sentence)
    weak_lemmas = {_lemma(w) for w in WEAK_KEYS}
    good = [w for w in words
            if w.lower() not in STOPWORDS
            and w.lower() not in WEAK_KEYS
            and _lemma(w) not in weak_lemmas       # catches inflections too
            and "displaystyle" not in w.lower()]
    # Deliberately do NOT rank topic membership or length first: doing so made
    # the key guessable from the option list alone ("the one echoing the title",
    # "the longest one"). Rank only by being a contentful proper noun, then
    # shuffle within rank so neither length nor topic leaks.
    def rank(w):
        return (w[0].isupper() and sentence.find(w) > 0,)
    R.shuffle(good)
    good.sort(key=rank, reverse=True)
    return good


def _numbers(sentence: str) -> List[str]:
    return re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", sentence)


def _year_like(tokens):
    return [t for t in tokens if re.fullmatch(r"\d{3,4}", t.replace(",", ""))]


def cloze_from_text(text: str, n: int = 5, topic: str = "") -> List[Dict]:
    """Generate up to n multiple-choice cloze questions from article text."""
    sents = _sentences(text)
    if not sents:
        return []
    # Terms from the topic itself make the best keys — they test the subject.
    topic_terms = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", topic)}
    all_words, all_nums = set(), set()
    for s in sents:
        all_words.update(_keywords(s, topic_terms)[:5])
        all_nums.update(_numbers(s))

    questions, used, used_keys = [], set(), set()
    order = list(range(len(sents)))
    R.shuffle(order)
    for idx in order:
        if len(questions) >= n or idx in used:
            continue
        s = sents[idx]
        nums = _numbers(s)
        years = _year_like(nums)
        keys = [k for k in _keywords(s, topic_terms) if k.lower() != topic.lower()]
        target: Optional[str] = None
        pool: List[str] = []
        # Prefer blanking a year/date (self-contained) or a proper-noun keyword.
        if years and R.random() < 0.5:
            target = years[0]
            pool = [x for x in _year_like(list(all_nums)) if x != target]
        elif keys:
            target = keys[0]
            same_case = target[0].isupper()
            # Match the key's surface shape so no option stands out: same case,
            # similar length, and the same word-class ending where we can tell.
            def suffix_class(w):
                for suf in ("tion", "sion", "ment", "ness", "ity", "ing", "ed",
                            "ly", "al", "ic", "ous", "ive", "er", "or", "s"):
                    if w.lower().endswith(suf):
                        return suf
                return ""
            tgt_class = suffix_class(target)
            band = max(3, len(target) // 3)
            pool = [w for w in all_words
                    if w.lower() != target.lower()
                    and w[0].isupper() == same_case
                    and abs(len(w) - len(target)) <= band
                    and suffix_class(w) == tgt_class]
            if len(set(pool)) < 3:      # relax the class match before giving up
                pool = [w for w in all_words
                        if w.lower() != target.lower()
                        and w[0].isupper() == same_case
                        and abs(len(w) - len(target)) <= band]
            # A key that is the only title word among the options gives itself
            # away — require distractors from the same family or drop the item.
            if topic_terms and target.lower() in topic_terms:
                if not any(w.lower() in topic_terms for w in pool):
                    continue
        if not target or len(set(pool)) < 3:
            continue
        if _lemma(target) in used_keys:
            continue   # don't key three questions on the same word
        blanked = re.sub(r"\b" + re.escape(target) + r"\b", "______", s, count=1)
        if "______" not in blanked:
            continue
        # If the key (or an inflection) still appears in the stem, the blank is
        # answerable by copying — reject it.
        stem_lemmas = {_lemma(w) for w in re.findall(r"[A-Za-z]{3,}", blanked)}
        if _lemma(target) in stem_lemmas:
            continue
        if len(tgt := target.lower()) >= 5 and any(
                w.lower()[:5] == tgt[:5] for w in re.findall(r"[A-Za-z]{5,}", blanked)):
            continue
        # A stem that opens with the blank gives no lead-in context.
        if blanked.lstrip().startswith("______"):
            continue
        # Reject a distractor that appears in the stem, or that shares a stem
        # with the key ("compose" vs "composition" gives the answer away).
        stem_words = {w.lower() for w in re.findall(r"[A-Za-z]{3,}", blanked)}
        stem_pref = {w.lower()[:5] for w in re.findall(r"[A-Za-z]{5,}", blanked)}
        tgt = target.lower()
        pool = [w for w in set(pool)
                if w.lower() not in stem_words
                and w.lower()[:5] not in stem_pref
                and not (len(w) >= 5 and len(tgt) >= 5 and w.lower()[:5] == tgt[:5])]
        if len(pool) < 3:
            continue
        # And the options must be separable from each other.
        chosen = []
        for w in sorted(pool):
            if any(len(w) >= 5 and len(c) >= 5 and w.lower()[:5] == c.lower()[:5]
                   for c in chosen + [target]):
                continue
            chosen.append(w)
        if len(chosen) < 3:
            continue
        pool = chosen
        distractors = R.sample(list(pool), 3)
        choices = [target] + distractors
        R.shuffle(choices)
        used.add(idx)
        used_keys.add(_lemma(target))
        questions.append({
            "kind": "choice",
            "prompt": "Fill in the blank:\n\n" + blanked,
            "choices": choices,
            "answer": target,
            "explain": s,
        })
    return questions


def definition_question(title: str, extract: str, other_summaries: List[Dict]) -> Optional[Dict]:
    """'Which topic does this describe?' — needs summaries of other topics."""
    sents = _sentences(extract)
    if not sents or len(other_summaries) < 3:
        return None
    first = sents[0]
    pattern = re.compile(re.escape(title), re.IGNORECASE)
    desc = pattern.sub("____", first)
    if "____" not in desc:
        return None
    others = R.sample(other_summaries, 3)
    choices = [title] + [o["title"] for o in others]
    R.shuffle(choices)
    return {
        "kind": "choice",
        "prompt": "Which topic does this describe?\n\n" + desc,
        "choices": choices,
        "answer": title,
        "explain": first,
    }


def cards_from_text(title: str, text: str, node_id: str = "", max_cards: int = 4) -> List[Dict]:
    """Build spaced-repetition cards from an article just read."""
    sents = _sentences(text)
    cards: List[Dict] = []
    if sents:
        cards.append({
            "front": "In your own words: what is {}?".format(title),
            "back": sents[0],
            "node_id": node_id,
            "article": title,
        })
    for s in sents[1:]:
        if len(cards) >= max_cards:
            break
        nums = _numbers(s)
        keys = _keywords(s)
        if _year_like(nums):
            y = _year_like(nums)[0]
            blanked = re.sub(r"\b" + re.escape(y) + r"\b", "______", s, count=1)
            if "______" in blanked:
                cards.append({"front": blanked, "back": y, "node_id": node_id, "article": title})
        elif keys and keys[0].lower() not in title.lower():
            key = keys[0]
            blanked = re.sub(r"\b" + re.escape(key) + r"\b", "______", s, count=1)
            if "______" not in blanked:
                continue
            # Same guards cloze_from_text applies: a blank with no lead-in
            # context, or a key that still appears (whole or as a stem) in
            # what's left, can be answered without recalling anything.
            if blanked.lstrip().startswith("______"):
                continue
            stem_lemmas = {_lemma(w) for w in re.findall(r"[A-Za-z]{3,}", blanked)}
            if _lemma(key) in stem_lemmas:
                continue
            if len(key) >= 5 and any(
                    w.lower()[:5] == key.lower()[:5]
                    for w in re.findall(r"[A-Za-z]{5,}", blanked)):
                continue
            cards.append({"front": blanked, "back": key, "node_id": node_id, "article": title})
    return cards[:max_cards]


# A card is only worth keeping if it carries a durable fact. Randomly generated
# computations ("7 + 5 = ?") are infinite and instance-specific: drill them with
# the generator, never as fixed flashcards.
_COMPUTATION = re.compile(
    # Operands may be parenthesised — "(7) + (-14) = ?" is the negatives drill's
    # normal shape, and the closing paren after the first operand used to break
    # the match, so every one of those became a permanent card.
    r"^[\s(]*[-+]?[\d.,/]+\)?\s*[-+×x*÷/−]\s*[\s(]*[-+]?[\d.,/]+"  # 7 + 5, (4) − (15)
    # "What is 7 + 5" is a live generator instance; "What is 3/4 of 20?" is an
    # authored fraction word problem — "/" here is a fraction separator, not
    # an arithmetic operator, so it must not trigger this alternative. Every
    # generator-produced "What is ..." prompt in practice.py spells its
    # operator out in words ("plus", "times", "% of"), never with a bare
    # symbol straight after the first number.
    r"|^\s*what is\s+[-+]?[\d.,]+\s*[-+×x*÷−]"                    # what is 7 + 5
    r"|^\s*\d+\s*[-+×x*÷/−]\s*\d+\s*=", re.IGNORECASE)


def is_ephemeral_prompt(prompt: str, kind: str = "",
                        ephemeral: Optional[bool] = None,
                        gen: str = "", level: int = 0) -> bool:
    """True when the item is a one-off instance rather than a durable fact.

    An order item\'s prompt is usually fixed boilerplate ("Put them in order")
    while the sequence being ordered is freshly randomised every time — the
    prompt text alone cannot tell one occurrence\'s card front apart from the
    next\'s, so trusting it meant a single front silently mapped to a
    different back on every sitting. Ordering is ephemeral by construction,
    the same way a generated arithmetic instance is, whatever its prompt
    happens to say.

    The prompt rules below cannot be replaced by the `ephemeral` flag, because
    a generator mints both kinds: "7 + 5 = ?" is a one-off instance, while
    "Which shape has 8 sides?" from the same generator is always octagon.
    Trusting the flag alone meant the 41 nodes assessed only through practice
    never produced a review card, however badly the reader did.

    But the flag settles the *other* direction outright. An authored bank item
    is stamped `ephemeral: False` where it loads: a human wrote it, fixed
    prompt, fixed answer, the same tomorrow as today. Reading its text anyway
    suppressed 39 authored items across 16 nodes — "5 + 3 = ?" is always 8 and
    "How many sides? 🔺" is always 3, but both read exactly like a generated
    instance, so math.1.addition minted nothing at all from a fully-missed
    paper: precisely the lesson whose errors most need to come back tomorrow.
    Declared provenance beats a guess about the text; absent a declaration,
    the text is still the best evidence there is.
    """
    if ephemeral is False:
        # Authored, and therefore durable — with one exception that holds
        # however an item was made: an order item's sequence is reshuffled per
        # instance, so a fixed front maps to a different back each sitting.
        return kind == "order"
    if gen and kind != "order":
        # Generated, and it says which generator made it — so ask that
        # generator whether this prompt recurs and is stably answered, rather
        # than inferring it from how the text reads. Recurrence is necessary
        # but not sufficient: a small-space drill like negatives at level 2
        # repeats "(4) − (15) = ?" often enough to look like a fact, and it
        # still is not one — it is a sum to work out, not something to recall.
        # So a generated item must clear BOTH bars, and falls through to the
        # text rules below, which is where bare computation is vetoed.
        from . import practice
        if not practice.is_durable_item(gen, level, prompt):
            return True
    if kind == "order":
        return True
    p = (prompt or "").strip()
    if not p:
        return True
    if _COMPUTATION.search(p):
        return True
    # Same shape as an order item's boilerplate: a fixed, generic prompt
    # whose actual content lives entirely in the freshly-randomised choices
    # — "Which fraction is the largest?" and "Which spelling is correct?"
    # give no information about what's being compared, so the SAME prompt
    # text answers differently every time g_fractions or g_spelling runs. A
    # missed card minted from one of these binds a fixed front to whichever
    # answer happened to be correct that one instance — unanswerable out of
    # context on the next sitting. Contrast with a fixed prompt whose answer
    # is genuinely constant regardless of instance ("P(both heads) = ?" is
    # always 1/4): those stay durable. This is a targeted, individually
    # verified set, not a general "generic-sounding prompt" heuristic —
    # the same false-precision risk documented for the named-theorem check.
    if p in ("Which fraction is the largest?", "Which spelling is correct?"):
        return True
    # "How many do you see? 🍎 🍎 🍎" is a random instance; "How many days in a
    # week?" is a durable fact. Only the emoji-run form is ephemeral.
    if re.search(r"how many\b", p, re.IGNORECASE):
        tail = p.split("?")[-1]
        emoji_run = re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", tail)
        if emoji_run or re.search(r"do you see", p, re.IGNORECASE):
            return True
    return False


def cards_from_missed(questions: List[Dict], answers: List[str],
                      node_id: str = "", article: str = "") -> List[Dict]:
    """Turn the questions a learner got wrong into review cards — errors are
    exactly what should come back tomorrow."""
    cards = []
    for q, a in zip(questions, answers):
        correct = str(q.get("answer", "")).strip()
        if not correct:
            continue
        num = _numeric_equal(str(a), correct)
        got_it = num is True or (num is None and str(a).strip().lower() == correct.lower())
        if not got_it:
            # The flag alone cannot decide this: a generator stamps it on both
            # "5 + 3 = ?" and "Which shape has 8 sides?", so trusting it meant
            # the 41 nodes assessed through practice never produced a review
            # card, however badly the reader did. It is decisive only when it
            # says *durable* — an authored item is one a human fixed in place,
            # whatever its text happens to look like.
            if is_ephemeral_prompt(q.get("prompt", ""), q.get("kind", ""),
                                   q.get("ephemeral"), q.get("gen", ""),
                                   q.get("level", 0)):
                continue
            front = q.get("prompt", "").replace("Fill in the blank:\n\n", "").strip()
            explain = (q.get("explain", "") or "").strip()
            if q.get("kind") == "short":
                # A constructed-response model answer is a paragraph, and a card
                # whose back is a paragraph is something to read rather than
                # something to recall. What a reader needs to bring back is the
                # ideas the answer has to contain.
                keys = [str(k) for k in (q.get("keywords") or []) if str(k).strip()]
                if keys:
                    cards.append({
                        "front": front,
                        "back": "Cover: " + ", ".join(keys),
                        "node_id": node_id,
                        "article": article,
                    })
                continue
            # A card's back is the answer and just enough reason to make it
            # stick. Appending the whole explanation turned some cards into the
            # exam question again — the longest ran to 369 characters, which is
            # something to read rather than something to recall. Capping only
            # the explanation portion at 150 chars still let the total run past
            # 220 whenever `correct` itself was long (some choice-kind answers
            # are full sentences) — 51 real bank items did exactly that, up to
            # 255 chars. Cap the total, budgeting whatever room the answer left.
            MAX_BACK = 220
            if explain and explain != front:
                budget = MAX_BACK - len(correct) - len(" — ")
                first = re.split(r"(?<=[.!?])\s+", explain)[0].strip()
                if budget > 10 and len(first) > budget:
                    first = first[:budget - 3].rsplit(" ", 1)[0] + "…"
                back = correct + " — " + first if budget > 10 else correct
            else:
                back = correct
            if len(back) > MAX_BACK:
                back = back[:MAX_BACK - 1].rsplit(" ", 1)[0] + "…"
            cards.append({
                "front": front or ("What is the answer? " + explain[:80]),
                "back": back,
                "node_id": node_id,
                "article": article,
            })
    return cards


def _numeric_equal(given: str, expected: str) -> Optional[bool]:
    """Compare numeric answers by value, so '0.5', '.50' and '1/2' all match —
    returns None when either side isn't numeric."""
    def parse(v):
        v = str(v).strip().replace(",", "").replace("−", "-").replace(" ", "")
        if not v:
            return None
        try:
            return float(v)
        except ValueError:
            m = re.fullmatch(r"(-?\d+)\s*/\s*(\d+)", v)
            if m and float(m.group(2)) != 0:
                return float(m.group(1)) / float(m.group(2))
        return None
    g, e = parse(given), parse(expected)
    if g is None or e is None:
        return None
    return abs(g - e) <= max(1e-6, abs(e) * 1e-6)


def cards_from_lesson(title: str, goal: str, kid_text: str = "",
                      node_id: str = "") -> List[Dict]:
    """Durable concept cards for early stages, drawn from the authored lesson
    rather than from encyclopedia prose (which young readers do not use)."""
    cards = []
    if goal:
        cards.append({"front": "What are you learning when you learn “{}”?".format(title),
                      "back": goal, "node_id": node_id, "article": title})
    if kid_text:
        first = _sentences(kid_text)
        sentence = first[0] if first else kid_text.strip()
        if sentence and sentence.lower() != (goal or "").lower():
            cards.append({"front": "Tell it back: what is {}?".format(title),
                          "back": sentence, "node_id": node_id, "article": title})
    return cards


def short_answer_from_node(title: str, goal: str, articles: List[str]) -> Optional[Dict]:
    """A constructed-response prompt: the reader must produce, not recognise.
    Graded on whether the key ideas appear, and always shown with a model
    answer so it teaches even when it scores loosely."""
    if not goal:
        return None
    # Unicode-aware: "Schrödinger" must not become "dinger".
    keywords = [w for w in re.findall(r"[^\W\d_]{5,}", goal, re.UNICODE)
                if w.lower() not in STOPWORDS and w.lower() not in WEAK_KEYS]
    if len(keywords) < 2:
        return None
    return {
        "kind": "short",
        "prompt": "In two or three sentences, explain {} in your own words.".format(title),
        "answer": goal,
        "keywords": keywords[:4],
        "explain": "A good answer covers: " + goal,
        # This item is worth writing and worth reading a model answer to — but it
        # is not worth marks. Its key is the node's `goal`, which the reader can
        # see on the lesson page, so pasting it scored 1.0 on all 248 nodes that
        # carry one. And its keywords are whatever words the goal happened to
        # use: an excellent account of order-of-operations lost a quarter of the
        # marks for not saying "mathematicians". Authored short-answer items,
        # with keys written for the purpose, are the ones that count.
        "ungraded": True,
    }


_NEGATORS = ("un", "non", "dis", "ir", "im", "in", "a")

# What may legitimately remain of a word once its shared stem is removed and
# still count as the same idea: real derivational endings only. "transport" /
# "transform" (remainders "port"/"form") are different roots and must not
# match; "anecdote" / "anecdotal" (remainders "e"/"al") are one idea.
_DERIVATIONAL_SUFFIXES = {
    "e", "s", "es", "ed", "ing", "ion", "tion", "ation", "al", "ial", "ive",
    "ity", "ty", "ly", "er", "or", "ist", "ism", "ment", "ness", "ous", "ic",
    "ical", "ance", "ence", "ant", "ent", "able", "ible", "y",
}


def _common_prefix(a: str, b: str) -> str:
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    return a[:i]


def _negates(a: str, b: str) -> bool:
    """Whether one word is the other with a negating prefix bolted on.

    "discontinuous" must not satisfy a key of *continuous*: it is the word that
    means the opposite. Two items were passable only through a match like that.
    """
    long, short = (a, b) if len(a) > len(b) else (b, a)
    return any(long.startswith(p) and long[len(p):].startswith(short[:4])
               and len(short) >= 4 for p in _NEGATORS)


# Words that join a list rather than build a sentence. Held out of the
# structure test in score_short_answer so a comma-and-conjunction list
# cannot pose as prose.
LIST_JOINERS = {"and", "or", "plus", "also", "then", "with"}


def score_short_answer(given: str, keywords: List[str]) -> float:
    """Fraction of the expected ideas the reader actually produced.

    Matched whole word by whole word. A substring test scored
    "photosynthesisrespirationnutrients" a perfect 1.0, which is not writing —
    it is knowing which letters to run together.
    """
    if not keywords:
        return 1.0
    text = (given or "").lower()
    words = {_lemma(w) for w in re.findall(r"[^\W\d_]{3,}", text, re.UNICODE)}
    nums = set(re.findall(r"-?\d+(?:\.\d+)?", text))

    def known(word):
        """Whether the reader produced this word, allowing for word-building.

        "finitely" for *finite*, "balancing" for *balance*, "unrepresentative"
        for *representative*. The length guard is what keeps this from
        re-opening the substring cheat: a run-on like
        "photosynthesisrespirationnutrients" is far longer than any word it
        pretends to contain, and is rejected.
        """
        w = _lemma(word)
        if w in words:
            return True
        if len(w) < 5:
            # Short keys must match exactly. Containment on three-letter words
            # credited "for" from *formula* and "are" from *share*.
            return False
        for other in words:
            if len(other) < 5 or abs(len(other) - len(w)) > 4:
                continue
            # Word-building shares a beginning: "finitely" for *finite*,
            # "anecdotal" for *anecdote*. A shared *ending* is what let
            # "discontinuous" credit *continuous* and "nonstandard" credit
            # *standard* — crediting a key for the word that negates it.
            if other.startswith(w) or w.startswith(other):
                return True
            # A long shared prefix alone is not word-building: "transport"
            # and "transform" share six letters and no meaning. Genuine
            # derivation leaves only a suffix behind once the shared stem is
            # removed — so credit the match only when BOTH remainders are
            # recognisable derivational endings, never when either word
            # continues with fresh root material.
            stem = _common_prefix(w, other)
            if (len(stem) >= 6 and not _negates(w, other)
                    and w[len(stem):] in _DERIVATIONAL_SUFFIXES
                    and other[len(stem):] in _DERIVATIONAL_SUFFIXES):
                return True
        return False

    def hit(key):
        key = str(key).strip().lower()
        if not key:
            return False
        parts = re.findall(r"[^\W\d_]{3,}", key, re.UNICODE)
        digits = re.findall(r"-?\d+(?:\.\d+)?", key)
        if len(parts) + len(digits) > 1:
            # A multi-word key like "undo addition" or "x = 5" is met when the
            # reader has produced its parts — not necessarily verbatim and not
            # necessarily adjacent. Matching these as single tokens meant they
            # could never be met at all: 28 of 189 authored short items scored
            # their own model answer below the pass mark.
            return (all(known(w) for w in parts)
                    and all(d in nums for d in digits))
        if digits:
            return digits[0] in nums
        return known(parts[0]) if parts else False

    coverage = sum(1 for k in keywords if hit(k)) / len(keywords)

    # Keyword presence is necessary but it is not writing. A bare unordered
    # dump — "photosynthesis sunlight energy" — hit every key and scored a
    # clean pass without a single connecting thought. The tell is structural
    # and conservative: every token in the answer is one of the keys (or a
    # word built from one) and not one function word joins them. Any real
    # sentence, however terse — "photosynthesis is from sunlight" — carries a
    # connective and keeps full fuzzy/near-miss credit; only the naked list
    # loses half. Single-key answers are exempt: one word can be the whole
    # legitimate answer ("mitochondria").
    if coverage > 0 and len(keywords) >= 2:
        tokens = re.findall(r"[^\W\d_]+", text, re.UNICODE)
        key_lemmas = {_lemma(w) for k in keywords
                      for w in re.findall(r"[^\W\d_]+", str(k).lower(), re.UNICODE)}

        def keywordish(tok):
            t = _lemma(tok)
            return any(t == k
                       or (len(t) >= 5 and len(k) >= 5
                           and (t.startswith(k) or k.startswith(t)))
                       for k in key_lemmas)

        # "Any stopword at all" was too weak a test for structure: a list
        # joined by conjunctions is still a list, so "photosynthesis and
        # sunlight and energy" satisfied it and kept full coverage — the one
        # connective escape hatch. Conjunctions and commas are how lists are
        # written; they are not evidence of a sentence. Any *other* function
        # word ("is", "from", "the", "because") still is.
        # Two tests, and joiners must be held out of BOTH. Holding them out
        # of the structure test alone changed nothing: "and" is not itself
        # keyword-ish, so all(keywordish) already failed and the penalty was
        # skipped — which is exactly how "photosynthesis and sunlight and
        # energy" kept full marks. Strip the joiners, then ask whether what
        # remains is nothing but keywords with no function word holding them
        # together.
        content = [t for t in tokens if t not in LIST_JOINERS]
        structural = any(t in STOPWORDS and t not in LIST_JOINERS for t in tokens)
        if content and not structural and all(keywordish(t) for t in content):
            coverage *= 0.5
    return coverage


def score_quiz(questions: List[Dict], answers: List[str]) -> Dict:
    """Mark a paper. Items flagged `ungraded` are shown and answered and given
    feedback, but do not count — see `short_answer_from_node` for why."""
    right = 0.0
    total = 0
    for q, a in zip(questions, answers):
        if q.get("ungraded"):
            continue
        total += 1
        expected = str(q.get("answer", "")).strip()
        given = str(a).strip()
        if q.get("kind") == "short":
            # Partial credit: producing most of the idea is most of the way there.
            right += score_short_answer(given, q.get("keywords") or [])
            continue
        num = _numeric_equal(given, expected)
        if num is True or (num is None and given.lower() == expected.lower()):
            right += 1
    total = max(total, 1)
    return {"right": round(right, 2), "total": total, "score": right / total}
