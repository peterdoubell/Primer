"""Record the stand-alone activities that web/app.js links from lesson pages.

Most stand-alone activities are listed in ``web/activities/registry.json``,
which the learning-sequence service already reads. Older ones are linked
directly from ``web/app.js`` with ``if (n.id === '<module>') page.append(...)``.
This tool extracts those links into ``data/learning-games/reader-links.json`` so
each module's learning sequence can point readers to everything the module
already offers.

    python tools/learning_games_inventory.py          # rewrite the record
    python tools/learning_games_inventory.py --check  # fail if it is stale
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READER = ROOT / "web" / "app.js"
RECORD = ROOT / "data" / "learning-games" / "reader-links.json"

GUARD = re.compile(r"if \(n\.id === '([^']+)'\) page\.append\(")
LINK = re.compile(r"href: '(/app/[^']+)' \},\s*'((?:[^'\\]|\\.)+)'")


def extract(source: str):
    links = {}
    guards = list(GUARD.finditer(source))
    for index, guard in enumerate(guards):
        end = guards[index + 1].start() if index + 1 < len(guards) else len(source)
        block = source[guard.end():min(end, guard.end() + 800)]
        for href, label in LINK.findall(block):
            bucket = links.setdefault(guard.group(1), [])
            entry = {"href": href, "label": label.replace("\\'", "'")}
            if entry not in bucket:
                bucket.append(entry)
    return dict(sorted(links.items()))


def render(links) -> str:
    return json.dumps(links, indent=2, ensure_ascii=False) + "\n"


def main(argv):
    text = render(extract(READER.read_text(encoding="utf-8")))
    if "--check" in argv:
        current = RECORD.read_text(encoding="utf-8") if RECORD.exists() else ""
        if current != text:
            print("%s is stale: run python tools/learning_games_inventory.py" % RECORD.relative_to(ROOT))
            return 1
        print("reader links up to date: %d modules" % len(json.loads(text)))
        return 0
    RECORD.write_text(text, encoding="utf-8")
    print("wrote %s: %d modules" % (RECORD.relative_to(ROOT), len(json.loads(text))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
