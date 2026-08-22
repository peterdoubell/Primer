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
# Quantifiers and comparatives read as adjectives to the tagger below but carry
# no subject knowledge — "languages are ______ focused on control flow" (less)
# was a hand-audit defect, not a question.
WEAK_KEYS.update(
    """less fewer dozens hundreds thousands millions billions numerous""".split())
# Container nouns: grammatically perfect keys that name no fact. "Some ______
# may deal with fully connected graphs" (models) is answerable by *systems*,
# *methods* or *approaches* just as well, and the 2026-08 sheet's ambiguous
# items were dominated by exactly this shape — the blank sits on the generic
# head noun, and every near-synonym in the article is a defensible answer.
# Refusing them costs items and buys the ambiguity bucket outright.
WEAK_KEYS.update(
    """type types kind kinds form forms model models system systems method
    methods way ways thing things part parts case cases term terms area areas
    aspect aspects factor factors feature features group groups set sets
    value values result results effect effects use uses change changes
    version versions level levels state states point points step steps
    process processes idea ideas concept concepts item items element elements
    number numbers amount amounts range ranges series order orders
    condition conditions property properties problem problems""".split())
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
        # The article text arrives truncated at a character budget, so the last
        # "sentence" is routinely a fragment ("...the most widely used and
        # internation"). A fragment reads as a question the reader failed to
        # understand rather than one the generator failed to build.
        if not p.rstrip().endswith((".", "!", "?", ".”", '."')):
            continue
        if REFERENT_START.search(p) or REFERENT_ANY.search(p):
            continue
        if EXAMPLE_MARKER.search(p):
            continue
        if p.count("(") != p.count(")"):
            continue
        if ":" in p:                 # list fragments and section run-ons
            continue
        # Added after a hand audit put the cloze defect rate at 65% (the
        # post-filter rate went unmeasured for as long as these filters
        # existed; it is now measured twice — 29/40, then 22/40 after the
        # precision pass, see tools/hand-audit-cloze-2026-08.md — and still
        # bad). The
        # remaining bad items were dominated by run-on clauses (semicolons),
        # comma-heavy list fragments, quoted speech torn from its speaker,
        # and copula-free noun piles with nothing assertable to blank.
        if ";" in p or p.count(",") >= 4:
            continue
        if p.count('"') + p.count("“") + p.count("”") > 0:
            continue
        # Maths that survived _clean_text still reads as rubble to a learner
        # ("As Δ t becomes infinitesimally small, the ______ up corresponds…").
        # Two tells: leftover single-letter variable tokens, and any Greek or
        # operator glyph. Either one means the sentence is no longer prose.
        # ("a", "A" and "I" are words, not variables — excluding them is what
        # keeps this from rejecting ordinary English.)
        if len(re.findall(r"(?<![A-Za-z])(?![aAI](?![A-Za-z']))[a-zA-Z](?![A-Za-z'])",
                          p)) >= 2:
            continue
        if re.search(r"[Ͱ-Ͽ∀-⋿←-⇿]", p):
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


# A hand audit of 40 items generated from real cached articles (see
# tools/hand-audit-cloze-2026-08.md) put the post-filter defect rate at 90%,
# and one cause dominated: distractors were drawn from anywhere in the article
# and matched only on surface shape (case, length, suffix), so a noun blank
# routinely offered "since", "although", "became", "roughly" beside it. Those
# are not wrong answers, they are impossible ones — the item collapses to a
# grammar puzzle. The fix below is a coarse, corpus-local word-class tagger:
# the key must be a noun or an adjective, and every distractor must carry the
# same class, so replacing the blank with any option yields a sentence that at
# least parses. It is a heuristic, not a parser; it errs toward "other"
# (excluded) when the evidence is mixed, which costs us items rather than
# quality.
CLOSED_CLASS = set(
    """although though since because whereas while unless until whether either
    neither however therefore thus hence moreover furthermore instead rather
    besides meanwhile nevertheless nonetheless otherwise today yesterday
    tomorrow many much several enough themselves himself herself itself
    ourselves yourself myself often always never sometimes usually perhaps
    maybe indeed almost nearly quite still just even yet ever else likewise
    accordingly consequently overall""".split()
)
_DET = set("""a an the its their his her our your my this that some any each every
            no another other one two three both all several most many""".split())
_PREP = set("""of in on at to from by with within without through across during
             among between into onto for about against under over near""".split())
_BE = set("""is are was were be been being becomes become became seems seemed
           appears appeared remains remained looks feels""".split())
_MODAL = set("""can could will would may might shall should must to""".split())


def _tag_classes(sents: List[str]):
    """Assign each word a coarse class from how it is used in THIS article.

    Corpus-local on purpose: a fixed lexicon would mislabel domain words
    ("transit", "control", "map"), whereas the article itself shows the word in
    the slots it actually occupies. Evidence is tallied across occurrences and
    the majority wins; a tie means we do not know, which is "other".

    Returns the classes *and* how much contextual evidence each verdict rests
    on. The second number matters as much as the first: the 2026-08 hand audit
    found the residual nonsense distractors were nearly all words the tagger
    had seen once, in a slot it half-understood, or not at all (decided by
    suffix alone) — "inward", "equivalent", "gives", "made". A verdict with one
    vote behind it is a guess, and a guess is exactly what must not become a
    distractor. Callers demand attested evidence for options; keys may lean on
    the weaker signal, since a mis-keyed sentence is caught by other filters.
    """
    votes: Dict[str, Dict[str, int]] = {}

    def vote(word: str, cls: str):
        votes.setdefault(word.lower(), {}).setdefault(cls, 0)
        votes[word.lower()][cls] += 1

    for s in sents:
        toks = re.findall(r"[A-Za-z][A-Za-z'-]*", s)
        for i, w in enumerate(toks):
            lw = w.lower()
            if len(lw) < 4 or lw in CLOSED_CLASS:
                continue
            prev = toks[i - 1].lower() if i else ""
            nxt = toks[i + 1].lower() if i + 1 < len(toks) else ""
            nxt_content = bool(nxt) and nxt not in STOPWORDS and nxt not in _PREP
            if i and w[0].isupper():
                # Capitalised away from the sentence opening: a name. Kept as
                # its own class so a name blank is only ever offered names —
                # "including Dijkstra / Although / Control" was the failure.
                vote(w, "propn")
                continue
            if lw.endswith("ly"):
                vote(w, "other")
                continue
            if prev in _MODAL:
                vote(w, "verb")
                continue
            if prev in _BE:
                # "is electrolytic" (adj) vs "is decomposed by" (participle verb)
                vote(w, "verb" if lw.endswith("ing") else "adj")
                continue
            if prev in _DET or prev in _PREP:
                # "the ______ cell" reads as a modifier; "the ______ ." a noun.
                vote(w, "adj" if nxt_content else "noun")
                continue
            if nxt in _BE or nxt == "of":
                vote(w, "noun")
                continue
            if nxt_content and w[0].islower() and lw.endswith(("ic", "al", "ous",
                                                               "ive", "ary")):
                vote(w, "adj")
                continue
            vote(w, "other")

    classes: Dict[str, str] = {}
    strength: Dict[str, int] = {}
    for word, tally in votes.items():
        best = max(tally.values())
        winners = [c for c, v in tally.items() if v == best]
        cls = winners[0] if len(winners) == 1 else "other"
        strength[word] = best if len(winners) == 1 and cls != "other" else 0
        if cls == "other":
            # Short articles give a word one or two occurrences, often in slots
            # none of the rules above cover, and an "other" verdict there means
            # "no evidence" rather than "not a noun". Morphology is a weaker
            # signal than context, so it is consulted only as the tiebreak —
            # without it a five-sentence paragraph yields almost no items.
            cls = _suffix_prior(word)
        classes[word] = cls
    return classes, strength


_NOUN_SUFFIX = ("tion", "sion", "ment", "ness", "ity", "ance", "ence", "ism",
                "ist", "ology", "ography", "ure", "age", "ship", "hood", "cy")
_ADJ_SUFFIX = ("ous", "ive", "ful", "less", "able", "ible", "ical", "ic",
               "al", "ary", "ish", "ant", "ent")


_VERBAL_SUFFIX = ("ed", "ing")


def _morph_ok(word: str, cls: str) -> bool:
    """Whether a word's *shape* agrees with the class its context suggested.

    The corpus tagger reads slots, and slots lie: "a poetic ______ for the
    planet" was offered *fluid*, *orbital* and *denser*, all three voted noun
    because the article happened to use them after a determiner. Morphology is
    the independent second opinion — weaker on its own (that is why it is only
    the tiebreak inside _tag_classes) but decisive as a veto. Requiring both
    signals to agree is what stops an adjective being offered for a noun blank
    and vice versa, and it refuses participles outright: "two other forms
    ______ themselves" beside *used* and *given* is a verb blank wearing a
    noun's clothes.
    """
    w = word.lower()
    if w.endswith(_VERBAL_SUFFIX) and len(w) > 5:
        return False
    prior = _suffix_prior(word)
    if prior == "other":
        return True            # shape says nothing; context stands unopposed
    return prior == cls


def _suffix_prior(word: str) -> str:
    w = word.lower()
    if w.endswith(_NOUN_SUFFIX):
        return "noun"
    if w.endswith(_ADJ_SUFFIX):
        return "adj"
    if w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return "noun"
    return "other"


def _numbers(sentence: str) -> List[str]:
    return re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", sentence)


def _year_like(tokens):
    """Tokens that are plausibly a year, not merely four digits long.

    "3,629 kilometres" satisfied a bare digit-count test and was then offered
    as a date; the comma is the tell that the number is a quantity, and a
    figure past 2100 is not a year anyone is being asked to recall.
    """
    return [t for t in tokens
            if re.fullmatch(r"\d{3,4}", t) and int(t) <= 2100]


def _plural(word: str) -> bool:
    """Surface number, good enough to keep options agreeing with the frame.

    "Often-discussed ______ are inductive, abductive and analogical reasoning"
    offered *analysis* beside *types*: only one option can follow "are", so the
    item stops being a knowledge check. Agreement is cheap to enforce and it
    removes a whole family of give-aways.
    """
    w = word.lower()
    return w.endswith("s") and not w.endswith(("ss", "us", "is", "ics", "ous"))


# How many separate times a word must appear in the article before it may be a
# key or an option. Words the article uses once are the arbitrary ones — the
# 2026-08 sheet's "Solla", "Nuzi", "inward", "salt" were all singletons — while
# a word the article returns to is part of its actual subject matter, which is
# both what is worth asking about and what makes a credible wrong answer.
MIN_OCCURRENCES = 2

# Contextual votes (not suffix guesses) required before a word may stand as a
# distractor. See _tag_classes for why one vote is not evidence.
MIN_CLASS_EVIDENCE = 2

# A blank needs left-hand context to constrain it. "Early ______ were not
# necessarily precise" leaves the reader guessing between every plural noun in
# the article; the same sentence with six words of run-up does not.
MIN_WORDS_BEFORE_BLANK = 4

# Below this many surviving items, an article yields none at all — see the note
# at the end of cloze_from_text.
MIN_ITEMS_PER_ARTICLE = 3

# Which blanks may be built at all. Adjective keys are the ambiguity engine —
# "implemented in ______ form" is answered as well by *conditional* as by
# *functional*, and nothing here can tell them apart — so a modifier blank is
# only worth building when the sentence names the thing being modified. Kept
# separate from the filter so the audit tool can vary it.
KEY_CLASSES = ("noun",)


def cloze_from_text(text: str, n: int = 5, topic: str = "") -> List[Dict]:
    """Generate up to n multiple-choice cloze questions from article text.

    No longer reachable from the app. The self-check at /api/selfcheck was its
    only caller and was retired on the 2026-08 hand audit (55% defective; see
    tools/hand-audit-cloze-2026-08.md). What is left standing here is the
    measurement apparatus, not a feature: tools/audit_cloze.py and
    tools/audit_cloze_defects.py draw and score sheets from it, and the
    regression tests hold the rate to the 5% bar the feature would have to
    clear to come back. Delete this only together with those.

    Precision over yield, deliberately. The feature has an honest empty state
    ("Not enough prose here to make questions"), so an item the generator
    cannot build well is better dropped than padded: two sound items beat five
    of which three mislead. Every filter below was added because a hand-audited
    sheet showed it removing broken items, and each one costs yield.
    """
    sents = _sentences(text)
    if not sents:
        return []
    # Terms from the topic itself make the best keys — they test the subject.
    topic_terms = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", topic)}
    all_words, all_nums = set(), set()
    for s in sents:
        all_words.update(_keywords(s, topic_terms)[:8])
        all_nums.update(_numbers(s))
    # Evidence comes from the WHOLE article, not just the sentences good enough
    # to be quizzed on. `sents` is a heavily filtered minority — often five or
    # six sentences — and asking it how a word behaves, or how often the
    # article uses it, was answering "once, in a slot I don't recognise" for
    # almost everything. The rejected sentences are poor questions and perfectly
    # good evidence.
    corpus = [p.strip() for p in re.split(r"(?<=[.!?])\s+", _clean_text(text))
              if p.strip()] or sents
    word_class, class_evidence = _tag_classes(corpus)
    # How often the article uses each word. Recurrence is the only cheap signal
    # we have for "this word belongs to the subject" as against "this word
    # wandered in once" — see MIN_OCCURRENCES.
    counts: Dict[str, int] = {}
    for s in corpus:
        for w in re.findall(r"[A-Za-z][A-Za-z'-]{3,}", s):
            counts[w.lower()] = counts.get(w.lower(), 0) + 1
    # Distractors draw from a wider net than keys do in *what* they may be —
    # any recurring word of the key's class, not only a rankable keyword — but
    # a narrower one in evidence: the tagger must have actually seen the word
    # used that way, twice, in this article. Starving the pool is what used to
    # force the generator to reach across classes; refusing the item is the
    # right answer to a starved pool, not a looser bar.
    weak_lemmas = {_lemma(w) for w in WEAK_KEYS}
    distractor_pool = {
        w for s in sents for w in re.findall(r"[A-Za-z][A-Za-z'-]{3,}", s)
        if w.lower() not in STOPWORDS
        and w.lower() not in WEAK_KEYS
        and _lemma(w) not in weak_lemmas
        and "displaystyle" not in w.lower()
        and counts.get(w.lower(), 0) >= MIN_OCCURRENCES
        and class_evidence.get(w.lower(), 0) >= MIN_CLASS_EVIDENCE
        and _morph_ok(w, word_class.get(w.lower(), "other"))
    }

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
        # Prefer blanking a year/date (self-contained) or a content keyword.
        if years and R.random() < 0.5:
            target = years[0]
            # Years must be comparable to be wrong answers rather than
            # impossible ones. "James Gregory (______–1675)" was offered 1716,
            # which no reader can believe, and 1675, which the stem prints two
            # characters later. Same digit-count, same century-ish band, and
            # never a number already visible in the sentence.
            pool = [x for x in _year_like(list(all_nums))
                    if x != target and len(x) == len(target)
                    and abs(int(x) - int(target)) <= 120
                    and x not in nums]
        elif keys:
            # Only blank something the reader could name: a noun or a modifier.
            # Blanking a verb or a connective ("the error ______ in the logical
            # form") makes a grammar puzzle, not a knowledge check.
            #
            # Names are excluded outright, against the intuition that a name is
            # the most concrete thing on the page. The 2026-08 sheet says
            # otherwise: every name item on it was broken, because a credible
            # wrong name has to be the same *kind* of thing as the right one —
            # another astronomer, another empire — and nothing in this file
            # knows that. It produced "Babylonia mechanism", "Solla counting
            # house", "the Discovery geographer". Class agreement cannot rescue
            # a name blank, so name blanks are not built.
            keys = [k for k in keys
                    if word_class.get(k.lower()) in KEY_CLASSES
                    and counts.get(k.lower(), 0) >= MIN_OCCURRENCES
                    and class_evidence.get(k.lower(), 0) >= MIN_CLASS_EVIDENCE
                    and _morph_ok(k, word_class.get(k.lower(), "other"))]
            if not keys:
                continue
            # Deliberately still keys[0], with no walk down the ranking. A
            # variant that tried each candidate in turn raised the item count
            # by roughly half and hand-audited worse (29/40 defective against
            # 23/40) — not a controlled comparison, since the distractor pool
            # widened in the same step, but the direction was clear and the
            # keys further down the ranking are the ones ranking already
            # judged weakest. Yield is the cheaper thing to give up: three
            # sound items beat five of which two are broken.
            target = keys[0]
            key_class = word_class.get(target.lower())
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
            # Substitutability first: an option that cannot occupy the blank is
            # not a distractor, it is a hint. Both pools below draw from here.
            same_class = {w for w in distractor_pool
                          if word_class.get(w.lower()) == key_class
                          and _plural(w) == _plural(target)}
            pool = [w for w in same_class
                    if w.lower() != target.lower()
                    and w[0].isupper() == same_case
                    and abs(len(w) - len(target)) <= band
                    and suffix_class(w) == tgt_class]
            if len(set(pool)) < 3:      # relax the class match before giving up
                # Relax the *suffix* match, never the word class — a wider
                # length band is a cosmetic loss, a cross-class option is a
                # broken item.
                pool = [w for w in same_class
                        if w.lower() != target.lower()
                        and w[0].isupper() == same_case
                        and abs(len(w) - len(target)) <= band]
            if len(set(pool)) < 3:      # then the length band, class last
                pool = [w for w in same_class
                        if w.lower() != target.lower()
                        and w[0].isupper() == same_case]
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
        # A stem that opens with the blank gives no lead-in context — and one
        # that nearly opens with it gives almost none. "Early ______ were not
        # necessarily precise" is a sound English sentence and a hopeless
        # question: two words cannot pin down which plural noun belongs there.
        lead = blanked.split("______")[0]
        if len(re.findall(r"[A-Za-z]{2,}", lead)) < MIN_WORDS_BEFORE_BLANK:
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
    # A thin paper is worse than no paper. The UI's empty state ("Not enough
    # prose here to make questions") is honest and cheap; one or two survivors
    # from an article that fought every filter are the ones most likely to have
    # squeaked through them, and they arrive dressed as a real self-check. So
    # the article clears the floor or it offers nothing.
    if len(questions) < min(MIN_ITEMS_PER_ARTICLE, n):
        return []
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
        # Authored, and therefore durable — order included.
        #
        # This used to except order outright, on the grounds that "an order
        # item's sequence is reshuffled per instance, so a fixed front maps to
        # a different back each sitting". That is true of a GENERATED order
        # item, where the content being ordered is drawn afresh every time:
        # front "Put them in order", back "2 3 5 7" today and "1 4 6 9"
        # tomorrow. It is not true of an authored one, whose prompt and answer
        # are both written down and fixed.
        #
        # What is shuffled for an authored item is only the presentation — the
        # chips are dealt in a random order so the reader cannot score by
        # tapping left to right — and a card never stores the chips. Its front
        # is the prompt and its back is the answer (see cards_from_missed),
        # both of which are constant. So the card is stable and the reader
        # should get one when they miss the item.
        #
        # The exception could not be tested either way while the corpus held
        # no authored order items; the first ones written exposed it.
        return False
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
            # Spaces were removed above, so a fraction has exactly two plain
            # integer parts. Splitting avoids a backtracking numeric regexp on
            # an answer string supplied by the client.
            parts = v.split("/")
            if len(parts) == 2:
                numerator, denominator = parts
                numerator_digits = numerator[1:] if numerator.startswith("-") else numerator
                if (numerator_digits.isascii() and numerator_digits.isdigit()
                        and denominator.isascii() and denominator.isdigit()
                        and float(denominator) != 0):
                    return float(numerator) / float(denominator)
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
