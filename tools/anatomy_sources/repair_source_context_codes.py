"""Repair figure-record context codes that the fidelity checker cannot read.

Some packaging scripts wrote source_context values in their own words: an extent of
"source_local_views", a depicted state with capital letters, a life stage of "child", a side of
"not_applicable", or a sentence where a record belongs. The checker reads every context field of a
figure for every binding, so one such value made it refuse every binding of that figure.

On 2026-11-18 the project owner asked for these codes to be repaired. Each change rewrites a value
into the checker's vocabulary with the same meaning, under one of the rules in the review record.
Where the old code did not say what the figure shows, the figure was looked at and its caption read.

Only the evidence ledger, which the checker reads, changes. The app's figure catalog keeps the
packaging scripts' original codes: the app reads none of the repaired fields, and the catalog copy is
pinned by reader digests, lesson contracts and the saved fidelity scope. catalog_view() gives the
catalog's copy of a repaired record, so mirror checks still compare like with like.

Nothing else changes: no binding, coverage, review status, caption or pixel. Two kinds of record are
left as they are on purpose: a figure that selects no panel (choosing panels is a content decision),
and a figure whose panel state marks the panel as context only (that restriction is kept, so the
checker still refuses it). Nothing here is a clinical approval.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EVIDENCE = 'data/radiology/radiology-asset-evidence.json'
CATALOG = 'data/radiology/radiology-open-images.json'
DOCS = ROOT / 'docs/source-context-code-repairs-20261118'
REVIEW, RECEIPT = DOCS / 'review.json', DOCS / 'inverse.json'
RULES = ('extent_vocabulary', 'setting_vocabulary', 'laterality_vocabulary', 'laterality_stated', 'life_stage_vocabulary',
         'state_lowercase', 'state_reviewed', 'state_mixed_panels', 'state_same_meaning', 'prose_to_record')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def code(value):
    """The checker's form of a state code: lower-case letters, digits and underscores, starting with a letter."""
    return isinstance(value, str) and bool(re.fullmatch(r'[a-z][a-z0-9_]*', value))


def catalog_rows(data):
    found = {}

    def walk(value):
        if isinstance(value, dict):
            if 'id' in value and 'source_context' in value:
                found.setdefault(value['id'], []).append(value)
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(data)
    return found


def get(context, field):
    return context if field == 'source_context' else (
        context['population']['life_stage'] if field == 'population.life_stage' else context.get(field))


def put(context, field, value):
    if field == 'source_context':
        return copy.deepcopy(value)
    if field == 'population.life_stage':
        context['population']['life_stage'] = value
    else:
        context[field] = value
    return context


def described(asset_id):
    from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second
    entry = second.captions().get(asset_id)
    return ' '.join(second.descriptions(entry).values()) if entry else ''


def check_change(asset_id, change, context, row, vocabulary):
    """True when the change is what its rule allows."""
    rule, field, old, new = change['rule'], change['field'], change['old'], change['new']
    if rule.endswith('_vocabulary'):
        name = rule[:-len('_vocabulary')]
        return field in (name, 'population.' + name) and vocabulary[name].get(old) == new
    if rule == 'laterality_stated':
        quotes = re.findall(r'“([^”]+)”', row.get('reason', ''))
        return (field == 'laterality' and new in ('left', 'right') and quotes
                and all(quote in described(asset_id) for quote in quotes)
                and any(re.search(r'\b%s\b' % new, quote) for quote in quotes))
    if rule == 'state_lowercase':
        if field == 'panel_states':
            return set(old) == set(new) and all(new[key] == (value.lower() if not code(value) else value) for key, value in old.items())
        return field == 'depicted_state' and new == old.lower() and not code(old)
    if rule == 'state_reviewed':
        if field == 'panel_states':
            return set(old) == set(new) and set(new.values()) == {context.get('depicted_state')}
        return field == 'depicted_state' and code(new) and bool(row.get('reason'))
    if rule in ('state_mixed_panels', 'state_same_meaning'):
        panels = context.get('selected_panels') or []
        states = {(context.get('panel_states') or {}).get(panel) for panel in panels}
        if rule == 'state_mixed_panels':
            return field == 'depicted_state' and new == 'mixed' and len(states) > 1
        return field == 'depicted_state' and states == {new} and bool(row.get('reason'))
    if rule == 'prose_to_record':
        return (field == 'source_context' and isinstance(old, str) and isinstance(new, dict)
                and new.get('source_note') == old and set(new) == {'population', 'source_note'})
    return False


def plan(raw=None):
    """New source_context per repaired asset, checked against the ledger before the repair (by default the file as it is)."""
    from tools.check_msk_fidelity import inspect_source_context
    review = json.loads(REVIEW.read_text())
    assets = {item['id']: item for item in json.loads(raw if raw is not None else (ROOT / EVIDENCE).read_bytes())['assets']}
    rows = catalog_rows(json.loads((ROOT / CATALOG).read_text()))
    out, refused = {}, {row['asset_id']: row['issue'] for row in review['still_refused']}
    for row in review['repairs']:
        asset_id = row['asset_id']
        asset = assets[asset_id]
        if asset_id in out:
            raise ValueError('Repeated repair: ' + asset_id)
        if asset.get('structure_ids') or asset.get('requirement_coverage'):
            raise ValueError('A bound figure needs its bindings rechecked, not a code repair: ' + asset_id)
        mirrors = rows.get(asset_id, [])
        if (row['catalog_mirror'] != bool(mirrors) or len(mirrors) > 1
                or any(mirror['source_context'] != asset['source_context'] for mirror in mirrors)):
            raise ValueError('Catalog row does not hold the record as stored: ' + asset_id)
        context = copy.deepcopy(asset['source_context'])
        for change in row['changes']:
            if change['rule'] not in RULES or get(context, change['field']) != change['old']:
                raise ValueError('Change does not start from the stored value: %s %s' % (asset_id, change['field']))
            context = put(context, change['field'], change['new'])
            if not check_change(asset_id, change, context, row, review['vocabulary']):
                raise ValueError('Change does not follow its rule: %s %s' % (asset_id, change['field']))
        before = inspect_source_context(asset, {})
        after = inspect_source_context(dict(asset, source_context=context), {})
        if not any(issue.endswith('_invalid') for issue in before):
            raise ValueError('Nothing unreadable to repair: ' + asset_id)
        if any(issue.endswith('_invalid') for issue in after) or not set(after) <= set(before):
            raise ValueError('Repair leaves or adds a checker issue: ' + asset_id)
        if after != ([refused[asset_id]] if asset_id in refused else []):
            raise ValueError('Remaining refusal is not recorded: ' + asset_id)
        out[asset_id] = context
    kept = {row['asset_id'] for row in review['left_unchanged']}
    for asset in assets.values():
        unreadable = [issue for issue in inspect_source_context(asset, {}) if issue.endswith('_invalid')]
        if unreadable and asset['id'] not in out and asset['id'] not in kept:
            raise ValueError('Unreadable code left without a decision: ' + asset['id'])
        if asset['id'] in kept and unreadable != ['source_context_panel_selection_invalid']:
            raise ValueError('A record left unchanged no longer has its recorded issue: ' + asset['id'])
    return out


def layout(value, indent):
    """The value as the file writes it: two-space nesting below a key indented by `indent` spaces."""
    lines = json.dumps(value, indent=2, ensure_ascii=False).split('\n')
    return '\n'.join([lines[0]] + [' ' * indent + line for line in lines[1:]])


def context_spans(text, ids):
    """Character span of the source_context value of every JSON object whose own "id" is in ids.

    The file is walked as JSON, so an id inside a nested object of another record, or a record
    written with unusual indentation, cannot be mistaken for the record itself.
    """
    decoder, found = json.JSONDecoder(), {}

    def skip(at):
        while text[at] in ' \t\n\r':
            at += 1
        return at

    def value(at):
        at = skip(at)
        if text[at] == '{':
            at, keys = skip(at + 1), {}
            while text[at] != '}':
                key, at = decoder.raw_decode(text, at)
                start = skip(skip(at) + 1)
                keys[key] = (start, value(start))
                at = skip(keys[key][1])
                at = skip(at + 1) if text[at] == ',' else at
            if 'id' in keys and 'source_context' in keys:
                ident = decoder.raw_decode(text, keys['id'][0])[0]
                if ident in ids:
                    found.setdefault(ident, []).append(keys['source_context'])
            return at + 1
        if text[at] == '[':
            at = skip(at + 1)
            while text[at] != ']':
                at = skip(value(at))
                at = skip(at + 1) if text[at] == ',' else at
            return at + 1
        return decoder.raw_decode(text, at)[1]
    value(0)
    return found


def apply(raw, contexts):
    """Replace each named record's source_context in place, keeping the file's layout. Returns bytes and edits."""
    text, edits = raw.decode('utf-8'), []
    spans = context_spans(text, set(contexts))
    for asset_id, (old, new) in contexts.items():
        if len(spans.get(asset_id, [])) != 1:
            raise ValueError('Record not found exactly once: ' + asset_id)
        begin, end = spans[asset_id][0]
        line = text[text.rindex('\n', 0, begin) + 1:begin]
        indent = len(line) - len(line.lstrip(' '))
        if json.loads(text[begin:end]) != old:
            raise ValueError('Stored context is not the expected one: ' + asset_id)
        if text[begin:end] == layout(old, indent):
            edits.append((begin, text[begin:end], layout(new, indent)))
        elif text[begin:end] == json.dumps(old, ensure_ascii=False):
            edits.append((begin, text[begin:end], json.dumps(new, ensure_ascii=False)))
        else:
            raise ValueError('Stored context has an unexpected layout: ' + asset_id)
    out, done = text, []
    for begin, old, new in sorted(edits, reverse=True):
        out = out[:begin] + new + out[begin + len(old):]
        done.append([len(text[:begin].encode('utf-8')), old, new])
    return out.encode('utf-8'), sorted(done)


def unchanged_elsewhere(before, after, repaired):
    """True when the two parsed files differ only in the repaired records' source_context."""
    def strip(value):
        if isinstance(value, dict):
            return {key: ('<repaired>' if key == 'source_context' and value.get('id') in repaired else strip(item))
                    for key, item in value.items()}
        if isinstance(value, list):
            return [strip(item) for item in value]
        return value
    return strip(before) == strip(after)


def catalog_view(asset_id, context):
    """A repaired ledger context as the app's figure catalog keeps it: the recorded changes undone."""
    row = next((item for item in json.loads(REVIEW.read_text())['repairs'] if item['asset_id'] == asset_id), None)
    for change in reversed(row['changes'] if row else []):
        context = put(copy.deepcopy(context), change['field'], change['old'])
    return context


def repair():
    planned = plan()
    raw = (ROOT / EVIDENCE).read_bytes()
    old = {item['id']: item.get('source_context') for item in json.loads(raw)['assets']}
    after, edits = apply(raw, {asset_id: (old[asset_id], new) for asset_id, new in planned.items()})
    parsed = json.loads(after)
    if not unchanged_elsewhere(json.loads(raw), parsed, set(planned)):
        raise ValueError('Unintended change in the evidence file')
    if any(item['source_context'] != planned[item['id']] for item in parsed['assets'] if item['id'] in planned):
        raise ValueError('A record was not repaired as planned')
    RECEIPT.write_text(json.dumps({
        'path': EVIDENCE, 'before_sha256': sha(raw), 'after_sha256': sha(after), 'edits': edits,
        'clinical_approval': False, 'extends_historical_approval': False}, indent=1, ensure_ascii=False) + '\n')
    (ROOT / EVIDENCE).write_bytes(after)
    return planned


def before_source_context_repairs(path, raw):
    """Exact earlier bytes of the evidence file; any other file or state is returned unchanged."""
    entry = json.loads(RECEIPT.read_text())
    if str(path) != entry['path'] or sha(raw) != entry['after_sha256']:
        return raw
    # Offsets are byte positions in the earlier file, so undo from the last edit to the first.
    shift = sum(len(new.encode()) - len(old.encode()) for _, old, new in entry['edits'])
    for start, old, new in sorted(entry['edits'], reverse=True):
        shift -= len(new.encode()) - len(old.encode())
        at = start + shift
        if raw[at:at + len(new.encode())] != new.encode():
            raise ValueError('Repaired context literal changed')
        raw = raw[:at] + old.encode() + raw[at + len(new.encode()):]
    if sha(raw) != entry['before_sha256']:
        raise ValueError('Context repair inverse changed unrelated bytes')
    return raw


if __name__ == '__main__':
    print(len(repair()), 'records repaired in the evidence ledger')
