"""Keep a requirement's laterality marker out of its anatomical display name."""
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = Path('data/radiology/non-msk-structure-requirements.json')


def display_structure_name(name, laterality):
    """Remove only an explicit non-sided metadata prefix, retaining real sides."""
    if laterality != 'not_applicable':
        return name
    for prefix in ('not applicable ', 'not_applicable '):
        if name.lower().startswith(prefix):
            label = name[len(prefix):]
            return label[:1].upper() + label[1:]
    return name


def before_structure_display_name_bytes(path, raw):
    if str(path) not in {str(INVENTORY), 'docs/radiology-fidelity-scope.json'}:
        return raw
    encoded = raw.encode() if isinstance(raw, str) else raw
    from tools.colonvessels_compatibility import _restore
    proof = ROOT / 'docs/structure-display-names/inventory-inverse.json'
    restored = _restore(str(path), encoded, proof, '10b12a8983533adc23bbc4c413a835aff206e686177473a2c963d1aad7958086')
    return restored.decode() if isinstance(raw, str) else restored


def before_structure_display_names(raw):
    return before_structure_display_name_bytes(INVENTORY, raw)


def regenerate(root=ROOT):
    """Refresh display strings only, retaining every recorded source match."""
    path = root / INVENTORY
    before = path.read_text()
    inventory = json.loads(before)
    expected = Counter()
    changes = {}
    investigations = {}
    for investigation in inventory['investigations']:
        labels = {}
        for structure in investigation['structures']:
            original = structure['name']
            clean = display_structure_name(original, structure['laterality'])
            labels[structure['id']] = clean
            if clean != original:
                expected[original] += 1
                changes[original] = clean
                structure['name'] = clean
        investigations[investigation['investigation_id']] = labels
    after = before
    for original, clean in changes.items():
        token = '"name": ' + json.dumps(original)
        if after.count(token) != expected[original]:
            raise ValueError('An inventory display name occurs outside the reviewed structures.')
        after = after.replace(token, '"name": ' + json.dumps(clean))
    path.write_text(after)

    rows = 0
    files = 0
    for locator in sorted((root / 'web/radiology/structure-atlas/locators').glob('*.json')):
        original = locator.read_text()
        detail = json.loads(original)
        labels = investigations.get(detail['investigation_id'])
        if labels is None:
            # The independent MSK inventory has its own labels.
            continue
        if list(labels) != [row['id'] for row in detail['structures']]:
            raise ValueError('Locator identities differ from the current inventory.')
        text = original
        for row in detail['structures']:
            clean = labels[row['id']]
            if row['name'] == clean:
                continue
            token = '"name": ' + json.dumps(row['name'])
            if text.count(token) != 1:
                raise ValueError('A locator display name is ambiguous.')
            text = text.replace(token, '"name": ' + json.dumps(clean), 1)
            rows += 1
        if text != original:
            locator.write_text(text)
            files += 1
    return {'inventory_names': sum(expected.values()), 'locator_names': rows, 'locator_files': files}


if __name__ == '__main__':
    print(json.dumps(regenerate()))
