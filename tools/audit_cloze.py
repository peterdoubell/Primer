"""Draw a hand-audit sheet of auto-generated cloze items from REAL article text.

`tools/audit_cloze_defects.py` is the automated half: it re-checks generated
items with independent regexes over a frozen 17-paragraph corpus. It cannot see
the defects that matter most — a stem that is unanswerable because the missing
word was never determined by the sentence, a blank with two defensible answers,
a distractor that is nonsense in context. Those need a person.

quiz.py's own comment records a 65% hand-audited defect rate *before* the
current filters and no number after them, so this tool exists to produce the
after number, the same way `check_banks.py --sample` produces the human half of
the item-bank audit. It prints a numbered sheet; a person marks each item OK or
names the defect; the tally lands in tools/hand-audit-cloze-2026-08.md.

    python3 tools/audit_cloze.py            # month-seeded sheet, 40 items
    python3 tools/audit_cloze.py 60         # bigger draw
    python3 tools/audit_cloze.py 40 2026-08 # pin the seed to reproduce a sheet

Source text is the local article cache (content/primer.db, opened read-only) —
the same Wikipedia prose the reader is actually quizzed on, not a hand-picked
corpus that would flatter the generator.
"""
import os
import random
import sqlite3
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer import quiz
from primer.wiki import WikiService

DB_CANDIDATES = ["content/primer.db", "data/primer.db"]


def _load_articles(rng, n_articles):
    """Read-only draw from the article cache. Opened with mode=ro on purpose:
    an audit tool must not be able to alter the corpus it is grading."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in DB_CANDIDATES:
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            continue
        conn = sqlite3.connect("file:{}?mode=ro".format(path), uri=True)
        try:
            rows = conn.execute(
                "SELECT title, html FROM article_cache "
                "WHERE html IS NOT NULL AND length(html) > 2000"
            ).fetchall()
        finally:
            conn.close()
        if rows:
            rows.sort(key=lambda r: r[0])          # stable order before sampling
            return rng.sample(rows, min(n_articles, len(rows))), rel
    return [], None


def main(argv):
    n_items = int(argv[0]) if argv else 40
    seed = argv[1] if len(argv) > 1 else datetime.date.today().strftime("%Y-%m")
    rng = random.Random(seed)
    # Seed the generator's own RNG too, or the sheet is unreproducible: shuffles
    # inside cloze_from_text pick both the key and the distractors.
    quiz.R.seed("cloze-audit-" + seed)

    articles, src = _load_articles(rng, n_articles=max(12, n_items // 2))
    if not articles:
        print("No article cache found; run the app once to populate it.")
        return 2

    sheet = []
    for title, html in articles:
        if len(sheet) >= n_items:
            break
        text = WikiService.article_plaintext(html, max_chars=6000)
        for item in quiz.cloze_from_text(text, n=3, topic=title):
            sheet.append((title, item))
            if len(sheet) >= n_items:
                break

    print("Cloze hand-audit sheet — seed {}, source {} ({} articles drawn).".format(
        seed, src, len(articles)))
    print("Mark each item OK, or name the defect: UNANSWERABLE (the stem does "
          "not determine the key), AMBIGUOUS (another option also fits), "
          "LEAK (the stem or option list gives the key away), "
          "NONSENSE (a distractor is not a possible answer at all).\n")
    for i, (title, item) in enumerate(sheet, 1):
        stem = item["prompt"].replace("Fill in the blank:\n\n", "")
        print("{:3}. [{}]\n     {}\n     options: {}\n     key: {}\n".format(
            i, title, stem, " / ".join(item["choices"]), item["answer"]))
    print("{} items on the sheet.".format(len(sheet)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
