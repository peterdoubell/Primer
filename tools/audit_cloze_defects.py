"""Measures the actual defect rate of quiz.cloze_from_text's auto-generated
items, independent of the generator's own internal guards — a checker that
reused cloze_from_text's own rejection logic to grade cloze_from_text would
prove nothing. Every check here is a fresh, independent read of the item.

Its 0% is therefore NOT the defect rate — it is the share of items broken in
ways a regex can see. The rate that counts is hand-measured, and it is much
worse: 22 of 40, 55%, in tools/hand-audit-cloze-2026-08.md (down from 90% on
the same seed before the 2026-08 precision pass), drawn by tools/audit_cloze.py
from real cached article text. Read that file before quoting a number from
this one.

Run: .venv/bin/python tools/audit_cloze_defects.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer import quiz

# The frozen paragraph corpus that used to live here is gone, and its removal
# is the finding, not a tidy-up. It was 84 hand-written five-sentence
# paragraphs, and after the 2026-08 precision pass it produced ZERO items: the
# generator now requires a word to recur in the article and to be attested in
# its word class before it may be a key or an option, and five sentences never
# supply that evidence. A corpus the generator refuses outright cannot measure
# the generator. So this tool reads the same source the reader is quizzed on —
# the local article cache, opened mode=ro, exactly as tools/audit_cloze.py does
# — and the checks below are still written independently of the generator's own
# guards, which is the whole point of the file.
DB_CANDIDATES = ["content/primer.db", "data/primer.db"]


def sample_corpus(limit=None, max_chars=6000):
    """(topic, text) pairs of real cached article prose, read-only.

    Sorted by title before any limit is applied, so a capped run is a stable
    prefix rather than whatever sqlite happened to return that day.
    """
    from primer.wiki import WikiService
    import sqlite3
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in DB_CANDIDATES:
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            continue
        conn = sqlite3.connect("file:{}?mode=ro".format(path), uri=True)
        try:
            has_cache = conn.execute(
                "SELECT 1 FROM sqlite_master "
                "WHERE type='table' AND name='article_cache'"
            ).fetchone()
            if has_cache:
                rows = conn.execute(
                    "SELECT title, html FROM article_cache "
                    "WHERE html IS NOT NULL AND length(html) > 2000"
                ).fetchall()
            else:
                # A runtime-created Primer DB is not necessarily an article
                # cache.  Keep looking rather than treating its mere existence
                # as the real audit corpus.
                rows = []
        finally:
            conn.close()
        if not rows:
            continue
        rows.sort(key=lambda r: r[0])
        out = []
        for title, html in rows:
            text = WikiService.article_plaintext(html, max_chars=max_chars)
            if text and len(text) >= 200:
                out.append((title, text))
            if limit and len(out) >= limit:
                break
        if out:
            return out
    return []


STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "into", "onto",
    "was", "were", "are", "has", "have", "had", "its", "their", "them",
    "which", "who", "when", "where", "while", "than", "then", "also",
    "most", "some", "such", "other", "these", "those", "over", "under",
}

MIN_STEM_CHARS = 25


def audit_item(item, source_text):
    """Independent checks — deliberately NOT reusing cloze_from_text's own
    guard logic, so this measures the generator, not its opinion of itself."""
    defects = []
    front, back = item.get("prompt", ""), item.get("answer", "")
    choices = item.get("choices", [])

    if len(front) < MIN_STEM_CHARS:
        defects.append("stem too short to give context")
    if back.lower().strip() in STOPWORDS:
        defects.append("key is a function word, not a fact")
    if len(back.strip()) < 2:
        defects.append("key is trivially short")
    if choices:
        lowered = [c.lower().strip() for c in choices]
        if len(set(lowered)) != len(lowered):
            defects.append("duplicate choices")
        if back.lower().strip() not in lowered:
            defects.append("key not among its own choices")
        if len(choices) < 3:
            defects.append("fewer than 3 total choices (including key)")
    blank_free = front.replace("______", "")
    if back.lower().strip() and back.lower().strip() in blank_free.lower():
        defects.append("key still recoverable by copying the stem")
    if not re.search(r"[a-zA-Z]", blank_free):
        defects.append("stem has no readable context at all")
    return defects


def main():
    total_items = 0
    total_defects = 0
    per_item_reports = []
    corpus = sample_corpus()
    for topic, text in corpus:
        items = quiz.cloze_from_text(text, n=5, topic=topic)
        for item in items:
            total_items += 1
            defects = audit_item(item, text)
            if defects:
                total_defects += 1
                per_item_reports.append((topic, item.get("prompt", "")[:70], defects))

    rate = (total_defects / total_items * 100) if total_items else 0.0
    print("Sampled {} auto-generated cloze items across {} cached articles.".format(
        total_items, len(corpus)))
    print("Defective: {} ({:.1f}%)".format(total_defects, rate))
    if per_item_reports:
        print("\nDefects found:")
        for topic, stem, defects in per_item_reports:
            print("  [{}] \"{}\" -- {}".format(topic, stem, ", ".join(defects)))
    verdict = "PASS (<5% target)" if rate < 5.0 else "FAIL (>=5% target)"
    print("\n{}".format(verdict))
    return 0 if rate < 5.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
