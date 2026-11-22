"""Bind the figures that the context-code repair unlocked to the structures and findings they show.

On 2026-11-18 a repair pass (repair_source_context_codes.py) made the figure records of 250 stored figures and models
readable by the fidelity checker. Until then the checker refused every binding of them, so none was bound. The project
owner then asked for the unlocked figures to be bound. This pass reads every caption match on the 156 repaired figures
that have a stored description, for structures and findings alike, and binds a pair only when all of these hold:

1. a sentence of the figure's published caption, or of its stored source note, names the structure or finding;
2. where the figure has selected panels, that sentence is about a selected panel;
3. the fidelity checker finds no modality, state or side conflict for any investigation sharing the requirement;
4. the figure was looked at and is consistent with the sentence.

"Names" is recorded per row as one of the three kinds of evidence of the findings pass:

- own_word: the sentence uses the requirement's own word;
- listed_term: the sentence uses a term that the requirement lists among its required parts; the row names those parts;
- kind_of: the sentence names something that is by definition a kind of what the requirement names (a carcinoma is a
  tumour). Every such pair is listed with its reason in the review record.

Some figures mark organs with letters that their legend spells out ("B, bladder"). Where a selected panel carries the
letter, the row quotes the legend entry and records the letter as its label.

Side handling is unchanged: a stated side binds that side, "both" or "bilateral" binds both, and an unstated side binds
each side only where the two sides are mirror images. Catch-all requirements, measurements and acquisition descriptors
are not bound. Coverage is always partial. Nothing here is a clinical approval, and no radiologist has reviewed the
bindings. The 69 repaired 3D models are reference-only records without a caption, so they are not bound here.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources import bind_finding_figures as findings  # noqa: E402
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second  # noqa: E402

EVIDENCE = second.EVIDENCE
DOCS = ROOT / 'docs/unlocked-figure-bindings-20261118'
REVIEW, RECEIPT = DOCS / 'review.json', DOCS / 'inverse.json'
SIDES = second.SIDES
KINDS = ('structure', 'finding')
EVIDENCE_KINDS = findings.EVIDENCE_KINDS
BOTH_WORDS = findings.BOTH_WORDS
# The findings pass's spelling variants and word forms, and four more plural or adjective forms.
SAME_WORD = dict(findings.SAME_WORD, ductal='ductus', varices='varix', atrial='atrium', ovaries='ovary')


def words(text):
    out = []
    for word in re.findall(r"[A-Za-z][A-Za-z0-9']*", text.replace('_', ' ')):
        word = SAME_WORD.get(word.lower(), word.lower())
        out.append(word.replace('haem', 'hem').replace('oedem', 'edem').replace('ischaem', 'ischem'))
    return out


def named(word, sentence_words):
    """A requirement word is in the sentence as itself, a plural, a word form or a compound ending in it."""
    return any(findings.same(word, other) or findings.same(word, other.rstrip('s')) or (len(word) >= 6 and other.endswith(word))
               for other in sentence_words)


def name_words(name):
    return [word for word in words(name) if word not in findings.FILLER and len(word) > 2]


def evidence_fits(row, requirements, pairs):
    """True when the row's stated evidence really is in its quote and in the requirement."""
    quote, name = row['quote'], requirements[0]['name']
    if row['evidence'] == 'own_word':
        return any(named(word, words(quote)) for word in name_words(name))
    if row['evidence'] == 'listed_term':
        return bool(row['listed_parts']) and row['term'].lower() in quote.lower() and all(
            part in findings.parts(requirements)
            and all(any(findings.same(word, other) for other in words(part)) for word in words(row['term']))
            for part in row['listed_parts'])
    pair = row['kind_of']
    return (pair['caption_word'].lower() in quote.lower() and pair in pairs
            and all(any(findings.same(word, other) for other in words(name)) for word in words(pair['requirement_word'])))


def basis(row):
    source = 'published caption' if row['field'] in second.PUBLISHED_FIELDS else 'stored source note'
    if row['evidence'] == 'own_word':
        text = 'The %s of this figure names the %s: “%s”' % (source, row['kind'], row['quote'])
    elif row['evidence'] == 'listed_term':
        text = 'The %s of this figure names “%s”, %s: “%s”' % (source, row['term'], findings.listed_as(row), row['quote'])
    else:
        pair = row['kind_of']
        text = 'The %s of this figure names “%s”, which this requirement covers under “%s”: “%s”' % (
            source, pair['caption_word'], pair['requirement_word'], row['quote'])
    if row.get('label'):
        text += ' The selected panels label it “%s”.' % row['label']
    if row.get('side_quote'):
        text += ' The caption states the side: “%s”' % row['side_quote']
    if row['side'] == 'side_not_stated':
        text += ' The caption states no side; the figure is used for this side on the assumption that the two sides are mirror images.'
    return text + ' One published figure; the full extent is not demonstrated.'


def plan():
    """Per asset: the structure ids and coverage entries to add. Every row is checked first."""
    from tools.check_msk_fidelity import inspect_binding, side_unstated
    from tools.anatomy_sources.structure_display_names import display_structure_name
    from tools.anatomy_sources.repair_source_context_codes import REVIEW as REPAIRS
    review = json.loads(REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(EVIDENCE.read_text())['assets']}
    repaired = {row['asset_id'] for row in json.loads(REPAIRS.read_text())['repairs']}
    described = second.captions()
    required, holders = second.requirements()
    out, seen = {}, set()
    for row in review['accepted']:
        asset, where = assets[row['asset_id']], '%s -> %s' % (row['asset_id'], row['structure_id'])
        if (row['asset_id'], row['structure_id']) in seen:
            raise ValueError('Repeated row: ' + where)
        seen.add((row['asset_id'], row['structure_id']))
        if row['asset_id'] not in repaired or asset['kind'] == 'model':
            raise ValueError('Not a figure that the context-code repair unlocked: ' + where)
        if not holders[row['structure_id']] & set(asset['investigation_ids']):
            raise ValueError('Requirement is not in an investigation of the figure: ' + where)
        requirement = required[row['structure_id']][0]
        if display_structure_name(row['name'], requirement.get('laterality')) != requirement['name'] or row['kind'] not in KINDS:
            raise ValueError('Row does not name its requirement: ' + where)
        text = second.descriptions(described[row['asset_id']]).get(row['field'], '')
        if text.count(row['quote']) < 1 or len(row['quote']) < 8 or row.get('side_quote', row['quote']) not in text:
            raise ValueError('Quote is not in the stored description: ' + where)
        if row.get('label') is not None and row['label'].lower() not in row['quote'].lower():
            raise ValueError('The quoted legend does not spell out the label: ' + where)
        selected = (asset.get('source_context') or {}).get('selected_panels')
        if selected:
            known = {str(panel).lower() for panel in selected}
            if not row['panels'] or any(str(panel).lower() not in known for panel in row['panels']):
                raise ValueError('Sentence is not about a selected panel: ' + where)
        probe = dict(asset, structure_ids=[row['structure_id']])
        if any(inspect_binding(probe, requirement) for requirement in required[row['structure_id']]):
            raise ValueError('Binding conflict: ' + where)
        if row['evidence'] not in EVIDENCE_KINDS or not evidence_fits(row, required[row['structure_id']], review['kind_of_pairs']):
            raise ValueError('The quote does not name the requirement as recorded: ' + where)
        sides = {requirement.get('laterality') for requirement in required[row['structure_id']]} & {'left', 'right'}
        assumed = any(side_unstated(probe, requirement) for requirement in required[row['structure_id']])
        if (row['side'] in ('caption_states_side', 'side_not_stated')) != assumed or row['side'] not in SIDES \
                or (row['side'] == 'not_sided') != (not sides):
            raise ValueError('Side label does not fit the requirement and record: ' + where)
        stated = row['quote'] + ' ' + row.get('side_quote', '')
        if row['side'] == 'caption_states_side' and not (
                any(re.search(second.SIDE_WORDS[side], stated, re.I if side in stated.lower() else 0) for side in sides)
                or re.search(BOTH_WORDS, stated, re.I)):
            raise ValueError('Quote does not state the side: ' + where)
        if ('side_quote' in row) and row['side'] != 'caption_states_side':
            raise ValueError('A side sentence is recorded for a binding that states no side: ' + where)
        if row['structure_id'] in asset['structure_ids'] or row['structure_id'] in asset['requirement_coverage']:
            raise ValueError('Already bound: ' + where)
        entry = out.setdefault(row['asset_id'], {'structure_ids': [], 'requirement_coverage': {}, 'corrected': {}})
        entry['structure_ids'].append(row['structure_id'])
        entry['requirement_coverage'][row['structure_id']] = {'extent': 'partial', 'basis': basis(row)}
    return out


def bind():
    raw = EVIDENCE.read_bytes()
    changes = plan()
    after, edits = second.apply(raw, changes)
    for old, new in zip(json.loads(raw)['assets'], json.loads(after)['assets']):
        if new != (dict(old, **second.merged(old, changes[old['id']])) if old['id'] in changes else old):
            raise ValueError('Unintended change in ' + old['id'])
    if {key: value for key, value in json.loads(raw).items() if key != 'assets'} != \
            {key: value for key, value in json.loads(after).items() if key != 'assets'}:
        raise ValueError('Unintended change outside the asset list')
    RECEIPT.write_text(json.dumps({
        'path': 'data/radiology/radiology-asset-evidence.json', 'before_sha256': second.sha(raw),
        'after_sha256': second.sha(after), 'edits': edits, 'clinical_approval': False,
        'extends_historical_approval': False}, indent=1, ensure_ascii=False) + '\n')
    EVIDENCE.write_bytes(after)
    return changes


def before_unlocked_figure_bindings(raw):
    """Exact earlier bytes of the evidence file; any other state is returned unchanged."""
    receipt = json.loads(RECEIPT.read_text())
    if second.sha(raw) != receipt['after_sha256']:
        return raw
    # Offsets are byte positions in the earlier file, so undo from the last edit to the first.
    shift = sum(len(new.encode()) - len(old.encode()) for _, old, new in receipt['edits'])
    for start, old, new in sorted(receipt['edits'], reverse=True):
        shift -= len(new.encode()) - len(old.encode())
        at = start + shift
        if raw[at:at + len(new.encode())] != new.encode():
            raise ValueError('Unlocked-figure binding literal changed')
        raw = raw[:at] + old.encode() + raw[at + len(new.encode()):]
    if second.sha(raw) != receipt['before_sha256']:
        raise ValueError('Unlocked-figure binding inverse changed unrelated bytes')
    return raw


if __name__ == '__main__':
    made = bind()
    print(len(made), 'figures;', sum(len(item['structure_ids']) for item in made.values()), 'bindings')
