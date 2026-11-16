"""Store reviewed Radiology Assistant figures locally and bind each to the structure its section names.

The project owner directed on 2026-11-16 that Radiology Assistant figures be stored and
bound, for personal use. The publisher permits reproduction for educational purposes with
credit to the original author and the Radiology Assistant. That is recorded as it is: the
licence is educational only, so every asset here keeps the commercial-rights issue.

Candidates were sections whose heading is the structure name. Each figure was then looked
at; tables, photographs, mixed-modality composites and figures that did not plainly show
the structure were rejected (docs/radiology-assistant-figure-bindings-20261116/review.json).
A binding is kept only if the fidelity checker finds no modality or side conflict.
Coverage is always partial. Nothing here is a clinical approval.
"""
import hashlib
import html
import json
import re
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
EVIDENCE = ROOT / 'data/radiology/radiology-asset-evidence.json'
DOCS = ROOT / 'docs/radiology-assistant-figure-bindings-20261116'
REVIEW, TERMS, RECEIPT = DOCS / 'review.json', DOCS / 'publisher-reuse-terms.txt', DOCS / 'inverse.json'
MEDIA = ROOT / 'web/reference-media/radiology-assistant'
LIST_END = b'\n  ],\n  "reference_rights_assets": ['
CACHE = Path(tempfile.gettempdir()) / 'primer-structure-locator-cache'
# Articles whose header has a subtitle and no publication date line; author read from the page.
SUBTITLED_ARTICLE_AUTHORS = {
    'https://radiologyassistant.nl/abdomen/ultrasound/transvaginal-ultrasound-for-non-gynaecological-conditions':
        'Julien Puylaert',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def download(url):
    request = urllib.request.Request(url.replace(' ', '%20'), headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def article_credit(url):
    """Title and author line as printed at the head of the article."""
    path = CACHE / (sha(url.encode())[:24] + '.html')
    page = path.read_text(encoding='utf-8', errors='replace') if path.is_file() else download(url).decode('utf-8', 'replace')
    head = page[page.index('<h1'):]
    title = html.unescape(re.sub(r'<[^>]+>', '', head[:head.index('</h1>')])).strip()
    after = [' '.join(html.unescape(part).split()) for part in re.split(r'<[^>]+>', head[head.index('</h1>'):][:3000])]
    parts = [part for part in after if part][:8]
    # The author line sits two lines above the publication date, after any subtitle.
    if 'Publicationdate' in parts[2:]:
        authors = parts[parts.index('Publicationdate') - 2]
    else:
        authors = SUBTITLED_ARTICLE_AUTHORS[url]
    authors = re.sub(r'^by\s+', '', authors)
    return title, authors


def requirements():
    found = {}
    for name in ('msk', 'non-msk'):
        data = json.loads((ROOT / 'data/radiology' / (name + '-structure-requirements.json')).read_text())
        for investigation in data['investigations']:
            for structure in investigation['structures']:
                found[(investigation['investigation_id'], structure['id'])] = structure
    return found


def records(fetch=False):
    from tools.check_msk_fidelity import inspect_binding
    review, required = json.loads(REVIEW.read_text()), requirements()
    terms_sha = sha(TERMS.read_bytes())
    by_figure = {}
    for row in review['accepted']:
        by_figure.setdefault(row['figure'], []).append(row)
    out = []
    for figure, rows in sorted(by_figure.items()):
        first = rows[0]
        article = first['url'].split('#')[0]
        stem = re.sub(r'[^a-z0-9]+', '-', figure.split('/assets/')[1].rsplit('.', 1)[0].lower()).strip('-')[:80]
        path = MEDIA / (stem + '.' + figure.rsplit('.', 1)[1].lower())
        # Credits are read once at packaging time and kept in the review record, so checks run offline.
        credit = review.get('article_credits', {}).get(article)
        title, authors = (credit['title'], credit['authors']) if credit else article_credit(article)
        probe = {'kind': first['kind'], 'modality': first['modality'], 'source_context': {'laterality': 'not_reported'}}
        bindable = [row for row in rows if not inspect_binding(probe, required[(row['investigation_id'], row['structure_id'])])]
        if not bindable:
            continue  # Wrong modality for every report that names it, or a side the figure does not state.
        if not path.is_file():
            if not fetch:
                raise ValueError('Stored figure missing: ' + path.name)
            MEDIA.mkdir(parents=True, exist_ok=True)
            path.write_bytes(download(figure))
        asset = {
            'id': 'ra-figure-' + stem, 'kind': first['kind'],
            'name': '%s: %s' % (title, first['heading']),
            'local_path': str(path.relative_to(ROOT)), 'sha256': sha(path.read_bytes()), 'modality': first['modality'],
            'investigation_ids': [], 'structure_ids': [], 'requirement_coverage': {},
            'source_context': {'setting': 'conceptual' if first['kind'] == 'schematic' else 'in_vivo',
                               'laterality': 'not_reported', 'population': {'life_stage': 'not_reported'},
                               'extent': 'local', 'depicted_state': first['depicted_state']},
            'source': {'url': article, 'section_url': first['url'], 'asset_url': figure,
                       'license': {'name': 'Radiology Assistant: reproduction for educational purposes with credit',
                                   'url': 'https://radiologyassistant.nl/disclaimer',
                                   'commercial_use': False, 'redistribution': False, 'educational_reproduction': True,
                                   'review_status': 'verified',
                                   'evidence_path': str(TERMS.relative_to(ROOT)), 'evidence_sha256': terms_sha,
                                   'attribution': '%s. %s. The Radiology Assistant. %s' % (authors, title, article),
                                   'reviewed_at': review['reviewed_at']}},
            'pixel_provenance': {'source_pixels_changed': False, 'highest_resolution_acquired_master_verified': False},
            'fidelity': 'source_reviewed_not_clinically_approved',
            'anatomical_review': {'status': 'pending',
                                  'reason': 'One published teaching figure; no radiologist has reviewed the binding.'},
            'visual_review': {'status': 'source_checked', 'reviewer': review['reviewer'], 'reviewed_at': review['reviewed_at'],
                              'sha256': sha(path.read_bytes()), 'evidence_path': str(REVIEW.relative_to(ROOT)),
                              'observation': first['seen']},
        }
        for row in bindable:
            if row['investigation_id'] not in asset['investigation_ids']:
                asset['investigation_ids'].append(row['investigation_id'])
            if row['structure_id'] not in asset['structure_ids']:
                asset['structure_ids'].append(row['structure_id'])
            asset['requirement_coverage'][row['structure_id']] = {
                'extent': 'partial',
                'basis': ('Publisher figure in the article section headed “%s”. %s One teaching figure; '
                          'the full extent is not demonstrated.' % (row['heading'], row['seen']))}
        out.append(asset)
    return out


def block(items):
    return ''.join(',\n' + '\n'.join('    ' + line for line in json.dumps(item, indent=2, ensure_ascii=False).splitlines())
                   for item in items).encode()


def insert():
    raw = EVIDENCE.read_bytes()
    if raw.count(LIST_END) != 1 or b'"ra-figure-' in raw:
        raise ValueError('Evidence file is not in the expected state')
    added = block(records(fetch=True))
    start = raw.index(LIST_END)
    after = raw[:start] + added + raw[start:]
    json.loads(after)
    RECEIPT.write_text(json.dumps({
        'path': 'data/radiology/radiology-asset-evidence.json', 'before_sha256': sha(raw), 'after_sha256': sha(after),
        'removed_range': [start, start + len(added)], 'removed_sha256': sha(added),
        'clinical_approval': False, 'extends_historical_approval': False}, indent=2) + '\n')
    EVIDENCE.write_bytes(after)


def before_radiology_assistant_figures(raw):
    """Exact earlier bytes of the evidence file; any other state is returned unchanged."""
    receipt = json.loads(RECEIPT.read_text())
    if sha(raw) != receipt['after_sha256']:
        return raw
    start, end = receipt['removed_range']
    if sha(raw[start:end]) != receipt['removed_sha256']:
        raise ValueError('Radiology Assistant evidence span changed')
    restored = raw[:start] + raw[end:]
    if sha(restored) != receipt['before_sha256']:
        raise ValueError('Radiology Assistant inverse changed unrelated bytes')
    return restored


if __name__ == '__main__':
    insert()
    made = records()
    print(len(made), 'figures;', sum(len(item['structure_ids']) for item in made), 'bindings')
