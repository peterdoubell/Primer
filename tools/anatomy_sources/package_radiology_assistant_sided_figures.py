"""Store reviewed Radiology Assistant figures for left and right structures and bind them.

The earlier Radiology Assistant passes skipped every left or right requirement, because a figure
whose record states no side could not be bound to one. The project owner relaxed that rule on
2026-11-17 (tools/check_msk_fidelity.side_unstated), so the article sections that name sided
structures were reviewed.

A figure is bound only when a sentence of its own article section names the structure, the figure
was looked at and shows or marks it, and the fidelity checker finds no modality conflict for any
investigation sharing the structure. It is bound to the side the sentence states. When the sentence
states no side it is bound to each side, and only where the two sides are mirror images. Tables,
photographs, mixed-modality composites and findings were rejected.

The licence is educational only, so every asset keeps the commercial-rights issue. Coverage is
always partial. Nothing here is a clinical approval, and no radiologist has reviewed the bindings.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources.package_radiology_assistant_figures import (  # noqa: E402
    EVIDENCE, LIST_END, MEDIA, TERMS, article_credit, block, download, requirements, sha)

DOCS = ROOT / 'docs/radiology-assistant-sided-figure-bindings-20261117'
REVIEW, RECEIPT = DOCS / 'review.json', DOCS / 'inverse.json'


def basis(row):
    if row['side'] == 'side_not_stated':
        return ('Publisher figure in the article section headed “%s”, whose text names the structure without a side: '
                '“%s” %s The figure is used for this side on the assumption that the paired structure is a mirror '
                'image. One teaching figure; the full extent is not demonstrated.' % (row['heading'], row['quote'], row['seen']))
    return ('Publisher figure in the article section headed “%s”, whose text names the structure and its side: “%s” %s '
            'One teaching figure; the full extent is not demonstrated.' % (row['heading'], row['quote'], row['seen']))


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
        credit = review['article_credits'][article]
        if not path.is_file():
            if not fetch:
                raise ValueError('Stored figure missing: ' + path.name)
            path.write_bytes(download(figure))
        asset = {
            'id': 'ra-figure-' + stem, 'kind': first['kind'],
            'name': '%s: %s' % (credit['title'], first['heading']),
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
                                   'attribution': '%s. %s. The Radiology Assistant. %s' % (credit['authors'], credit['title'], article),
                                   'reviewed_at': review['reviewed_at']}},
            'pixel_provenance': {'source_pixels_changed': False, 'highest_resolution_acquired_master_verified': False},
            'fidelity': 'source_reviewed_not_clinically_approved',
            'anatomical_review': {'status': 'pending',
                                  'reason': 'One published teaching figure; no radiologist has reviewed the binding.'},
            'visual_review': {'status': 'source_checked', 'reviewer': review['reviewer'], 'reviewed_at': review['reviewed_at'],
                              'sha256': sha(path.read_bytes()), 'evidence_path': str(REVIEW.relative_to(ROOT)),
                              'observation': first['seen']},
        }
        for row in rows:
            users = [(investigation, requirement) for (investigation, identifier), requirement in required.items()
                     if identifier == row['structure_id']]
            if any(inspect_binding(asset, requirement) for _, requirement in users):
                raise ValueError('Binding conflict: %s -> %s' % (figure, row['structure_id']))
            for investigation, _ in users:
                if investigation not in asset['investigation_ids']:
                    asset['investigation_ids'].append(investigation)
            asset['structure_ids'].append(row['structure_id'])
            asset['requirement_coverage'][row['structure_id']] = {'extent': 'partial', 'basis': basis(row)}
        out.append(asset)
    return out


def insert():
    raw = EVIDENCE.read_bytes()
    made = records(fetch=True)
    if raw.count(LIST_END) != 1 or any(('"id": "%s"' % item['id']).encode() in raw for item in made):
        raise ValueError('Evidence file is not in the expected state')
    added = block(made)
    start = raw.index(LIST_END)
    after = raw[:start] + added + raw[start:]
    json.loads(after)
    RECEIPT.write_text(json.dumps({
        'path': 'data/radiology/radiology-asset-evidence.json', 'before_sha256': sha(raw), 'after_sha256': sha(after),
        'removed_range': [start, start + len(added)], 'removed_sha256': sha(added),
        'clinical_approval': False, 'extends_historical_approval': False}, indent=2) + '\n')
    EVIDENCE.write_bytes(after)
    return made


def before_radiology_assistant_sided_figures(raw):
    """Exact earlier bytes of the evidence file; any other state is returned unchanged."""
    receipt = json.loads(RECEIPT.read_text())
    if sha(raw) != receipt['after_sha256']:
        return raw
    start, end = receipt['removed_range']
    if sha(raw[start:end]) != receipt['removed_sha256']:
        raise ValueError('Sided Radiology Assistant evidence span changed')
    restored = raw[:start] + raw[end:]
    if sha(restored) != receipt['before_sha256']:
        raise ValueError('Sided Radiology Assistant inverse changed unrelated bytes')
    return restored


if __name__ == '__main__':
    done = insert()
    print(len(done), 'figures;', sum(len(item['structure_ids']) for item in done), 'bindings')
