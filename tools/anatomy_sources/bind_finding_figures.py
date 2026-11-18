"""Bind stored figures of findings to the finding requirements their own descriptions name.

The first two passes (bind_stored_caption_assets.py and its pass 2) bound figures to structures and
left findings and diagnoses alone. On 2026-11-18 the project owner decided that figures of findings
should be bound to finding requirements. This pass does that for the figures already stored.

A pair is bound only when all of these hold:

1. a sentence of the figure's published caption, or of its stored source note, names the finding;
2. where the figure has selected panels, that sentence is about a selected panel;
3. the fidelity checker finds no modality, state or side conflict for any investigation sharing it;
4. the figure was looked at and is consistent with the sentence.

"Names the finding" is one of three things, recorded per row as its evidence:

- own_word: the sentence uses the requirement's own word for the finding;
- listed_term: the sentence uses a term that the requirement lists among its required parts; the row
  names those parts;
- kind_of: the sentence names something that is by definition a kind of what the requirement names
  (a contusion is an injury), or spells out an abbreviation the requirement uses. Every such pair
  is listed in the review record.

Side handling is unchanged from the second pass: a stated side binds that side, "both" binds both,
and an unstated side binds each side only where the two sides are mirror images. The lungs and the
pulmonary arteries are not, so an unsided lung finding is not bound.

Catch-all requirements ("every other", "unlisted"), measurements and acquisition descriptors are
not bound. Nor is a finding that the description mentions only to say that the source's suggestion,
attribution or description of it is unconfirmed. Coverage is always partial. Nothing here is a
clinical approval, and no radiologist has reviewed the bindings.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second  # noqa: E402

EVIDENCE = second.EVIDENCE
DOCS = ROOT / 'docs/finding-figure-bindings-20261118'
REVIEW, RECEIPT = DOCS / 'review.json', DOCS / 'inverse.json'
SIDES = second.SIDES
EVIDENCE_KINDS = ('own_word', 'listed_term', 'kind_of')
BOTH_WORDS = r'\b(both|bilateral(ly)?)\b'
# Words of a requirement name that say how to instantiate it, not what the finding is.
FILLER = frozenset('''actual actually each every covered encountered acquired obtained relevant resolved present source if
when reported or and the of other any all as at in with its their named listed unlisted right left proximal distal course
region regions component components pathway pathways channel channels interface interfaces adjacent size morphology
development level branching segment segments not applicable origin extent complete native site sites type pattern patterns
route routes relation relations relationship structure structures tissue tissues area zone side to for by on a an is are
that which optional separately individual whole entire local visible shown conditional case anatomy related observations
observation findings finding feature features eligible suspected suspicious historical graphic table association
differential recorded interfaces boundary boundaries surrounding attachments connections measurement measurements context
controls comparison variant variants material layers compartment compartments into from than per via whether both either
same new old non'''.split())
# Spelling variants, word forms and exact equivalents treated as the same word.
SAME_WORD = {
    'oesophagus': 'esophagus', 'oesophageal': 'esophageal', 'caecum': 'cecum', 'tumour': 'tumor', 'tumours': 'tumors',
    'fibres': 'fibers', 'grey': 'gray', 'centre': 'center', 'calcium': 'calcification', 'thrombosis': 'thrombus',
    'thrombosed': 'thrombus', 'thrombi': 'thrombus', 'emboli': 'embolus', 'embolism': 'embolus',
    'metastases': 'metastasis', 'metastatic': 'metastasis', 'stenotic': 'stenosis', 'stenoses': 'stenosis',
    'dilatation': 'dilation', 'dilated': 'dilation', 'aneurysmal': 'aneurysm', 'stones': 'stone', 'calculi': 'stone',
    'calculus': 'stone', 'lithiasis': 'stone', 'masses': 'mass', 'fistulae': 'fistula', 'fistulas': 'fistula',
    'fistulous': 'fistula', 'abscesses': 'abscess', 'diverticula': 'diverticulum', 'hernias': 'hernia',
    'herniation': 'hernia', 'herniated': 'hernia', 'nodes': 'node', 'nodal': 'node', 'lymphadenopathy': 'node',
    'infarction': 'infarct', 'infarcts': 'infarct', 'infarcted': 'infarct', 'necrotic': 'necrosis',
    'invagination': 'intussusception', 'invaginated': 'intussusception', 'spasm': 'vasospasm'}


def words(text):
    out = []
    for word in re.findall(r"[A-Za-z][A-Za-z0-9']*", text.replace('_', ' ')):
        word = SAME_WORD.get(word.lower(), word.lower())
        out.append(word.replace('haem', 'hem').replace('oedem', 'edem').replace('ischaem', 'ischem'))
    return out


def same(left, right):
    """Two words are the same word when they share a stem of at least four letters."""
    if left == right:
        return True
    shared = 0
    for a, b in zip(left, right):
        if a != b:
            break
        shared += 1
    return shared >= 4 and shared >= min(5, len(left), len(right))


def named(word, sentence_words):
    """A requirement word is in the sentence as itself, a plural, a word form or a compound ending in it."""
    return any(same(word, other) or same(word, other.rstrip('s')) or (len(word) >= 6 and other.endswith(word))
               for other in sentence_words)


def finding_words(name):
    return [word for word in words(name) if word not in FILLER and len(word) > 2]


def parts(requirements):
    return [part['name'] for requirement in requirements for part in requirement.get('required_parts') or []]


def evidence_fits(row, requirements, pairs):
    """True when the row's stated evidence really is in its quote and in the requirement."""
    quote, name = row['quote'], requirements[0]['name']
    if row['evidence'] == 'own_word':
        return any(named(word, words(quote)) for word in finding_words(name))
    if row['evidence'] == 'listed_term':
        # Every part the row names is a part of this requirement and contains each word of the term.
        return bool(row['listed_parts']) and row['term'].lower() in quote.lower() and all(
            part in parts(requirements) and all(any(same(word, other) for other in words(part)) for word in words(row['term']))
            for part in row['listed_parts'])
    pair = row['kind_of']
    return (pair['caption_word'].lower() in quote.lower() and pair in pairs
            and all(any(same(word, other) for other in words(name)) for word in words(pair['requirement_word'])))


def listed_as(row):
    """How the requirement lists the row's term: nothing to add when the part is the term itself."""
    listed = row['listed_parts']
    if [part.lower() for part in listed] == [row['term'].lower()]:
        return 'which this requirement lists'
    quoted = ['“%s”' % part for part in listed]
    return 'which this requirement lists as ' + (', '.join(quoted[:-1]) + ' and ' + quoted[-1] if len(quoted) > 1 else quoted[0])


def basis(row):
    source = 'published caption' if row['field'] in second.PUBLISHED_FIELDS else 'stored source note'
    if row['evidence'] == 'own_word':
        text = 'The %s of this figure names the finding: “%s”' % (source, row['quote'])
    elif row['evidence'] == 'listed_term':
        text = 'The %s of this figure names “%s”, %s: “%s”' % (source, row['term'], listed_as(row), row['quote'])
    else:
        pair = row['kind_of']
        relation = ('which this requirement abbreviates as %s' if pair['requirement_word'].isupper()
                    else 'which this requirement covers under “%s”') % pair['requirement_word']
        text = 'The %s of this figure names “%s”, %s: “%s”' % (source, pair['caption_word'], relation, row['quote'])
    if row.get('side_quote'):
        text += ' The caption states the side: “%s”' % row['side_quote']
    if row['side'] == 'side_not_stated':
        text += ' The caption states no side; the figure is used for this side on the assumption that the two sides are mirror images.'
    return text + ' One published figure; the full extent is not demonstrated.'


def plan():
    """Per asset: the structure ids and coverage entries to add. Every row is checked first."""
    from tools.check_msk_fidelity import inspect_binding, side_unstated
    review = json.loads(REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(EVIDENCE.read_text())['assets']}
    described = second.captions()
    required, holders = second.requirements()
    out, seen = {}, set()
    for row in review['accepted']:
        asset, where = assets[row['asset_id']], '%s -> %s' % (row['asset_id'], row['structure_id'])
        if (row['asset_id'], row['structure_id']) in seen:
            raise ValueError('Repeated row: ' + where)
        seen.add((row['asset_id'], row['structure_id']))
        if not holders[row['structure_id']] & set(asset['investigation_ids']):
            raise ValueError('Finding is not in an investigation of the figure: ' + where)
        text = second.descriptions(described[row['asset_id']]).get(row['field'], '')
        if text.count(row['quote']) < 1 or len(row['quote']) < 8 or row.get('side_quote', row['quote']) not in text:
            raise ValueError('Quote is not in the stored description: ' + where)
        selected = (asset.get('source_context') or {}).get('selected_panels')
        if selected:
            known = {str(panel).lower() for panel in selected}
            if not row['panels'] or any(str(panel).lower() not in known for panel in row['panels']):
                raise ValueError('Sentence is not about a selected panel: ' + where)
        probe = dict(asset, structure_ids=[row['structure_id']])
        if any(inspect_binding(probe, requirement) for requirement in required[row['structure_id']]):
            raise ValueError('Binding conflict: ' + where)
        if row['evidence'] not in EVIDENCE_KINDS or not evidence_fits(row, required[row['structure_id']], review['kind_of_pairs']):
            raise ValueError('The quote does not name the finding as recorded: ' + where)
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


def before_finding_figure_bindings(raw):
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
            raise ValueError('Finding binding literal changed')
        raw = raw[:at] + old.encode() + raw[at + len(new.encode()):]
    if second.sha(raw) != receipt['before_sha256']:
        raise ValueError('Finding binding inverse changed unrelated bytes')
    return raw


if __name__ == '__main__':
    made = bind()
    print(len(made), 'figures;', sum(len(item['structure_ids']) for item in made.values()), 'bindings')
