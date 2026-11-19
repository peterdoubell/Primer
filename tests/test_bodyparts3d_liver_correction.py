"""The BodyParts3D liver region shows each mesh under the name its geometry supports."""
import collections
import hashlib
import importlib.util
import json
import re
import struct
from pathlib import Path

import pytest

from primer.source_mesh_integrity import REVIEWED_MANIFEST_SUCCESSORS, is_reviewed_manifest
from tools import liver_atlas_compatibility as link

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / 'web/anatomy/bodyparts3d'
DOCS = ROOT / 'docs/bodyparts3d-liver-correction-20261119'
REMOVED = ('FJ2409', 'FMA14329', 'FMA15746')
ADDED = ('FJ2823', 'FJ2824', 'FJ3082', 'FJ3102', 'FJ3122')
SEGMENTS = {'i': 'FJ2816', 'ii': 'FJ2818', 'iii': 'FJ2819', 'iv': 'FJ2820', 'v': 'FJ2821', 'vi': 'FJ2822', 'vii': 'FJ2823', 'viii': 'FJ2824'}
PORTAL = ['FJ3082', 'FJ3122', 'FJ3102']
LIVER = ('ra.liver-masses', 'ra.liver-lirads')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def manifest():
    return json.loads((ATLAS / 'manifest.json').read_text())


def review():
    return json.loads((DOCS / 'review.json').read_text())


def mesh(code):
    """Positions and triangles of one delivered atlas mesh."""
    raw = (ATLAS / (code + '.bin')).read_bytes()
    magic, vertices, indices = struct.unpack('<4sII', raw[:12])
    assert magic == b'BP3D' and len(raw) == 12 + vertices * 24 + indices * 4
    flat = struct.unpack('<%df' % (vertices * 3), raw[12:12 + vertices * 12])
    points = [flat[index:index + 3] for index in range(0, vertices * 3, 3)]
    return points, struct.unpack('<%dI' % indices, raw[12 + vertices * 24:])


def centre(code):
    points = mesh(code)[0]
    return [sum(point[axis] for point in points) / len(points) for axis in range(3)]


def box(code):
    points = mesh(code)[0]
    return [bound(point[axis] for point in points) for bound in (min, max) for axis in range(3)]


def pieces(code):
    """Connected components of a mesh, after joining vertices at the same position."""
    points, faces = mesh(code)
    first = {}
    same = [first.setdefault(point, index) for index, point in enumerate(points)]
    parent = list(range(len(points)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index
    for start in range(0, len(faces), 3):
        a, b, c = (same[faces[start + offset]] for offset in range(3))
        parent[find(a)] = find(b)
        parent[find(b)] = find(c)
    return len({find(same[index]) for index in range(len(points))})


def nearest(first, second):
    a, b = mesh(first)[0], mesh(second)[0]
    return min(sum((p[axis] - q[axis]) ** 2 for axis in range(3)) for p in a for q in b) ** 0.5


def builder():
    spec = importlib.util.spec_from_file_location('build_detailed_anatomy', ROOT / 'tools/build_detailed_anatomy.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_liver_region_names_each_mesh_by_the_concept_its_geometry_supports():
    data = manifest()
    parts, region = data['parts'], data['regions']['liver']
    assert not set(REMOVED) & set(parts) and not any((ATLAS / (code + '.bin')).exists() for code in REMOVED)
    assert [row['id'] for row in region['parts']] == list(SEGMENTS.values()) + ['FJ2817'] + PORTAL + ['FJ2416', 'FJ2414', 'FJ2415']
    assert [row['layer'] for row in region['parts']] == ['bone'] * 8 + ['soft'] * 7 and region['labels'] == ['Segments', 'Vessels / gallbladder']
    names = {code: parts[code]['name'] for code in SEGMENTS.values()}
    assert names == {'FJ2816': 'caudate lobe of liver', 'FJ2818': 'hepatovenous segment ii', 'FJ2819': 'hepatovenous segment iii',
                     'FJ2820': 'hepatovenous segment iv', 'FJ2821': 'hepatovenous segment v', 'FJ2822': 'hepatovenous segment vi',
                     'FJ2823': 'hepatovenous segment vii', 'FJ2824': 'hepatovenous segment viii'}
    assert [parts[code]['name'] for code in PORTAL] == ['pre-hepatic portal vein', 'trunk of right portal vein', 'trunk of left portal vein']
    # Each liver mesh is one source object, delivered with the recorded bytes.
    for row in region['parts']:
        part = parts[row['id']]
        assert part['source_ids'] == [row['id']] and part['file'] == '/app/anatomy/bodyparts3d/%s.bin' % row['id']
        raw = (ATLAS / (row['id'] + '.bin')).read_bytes()
        assert sha(raw) == part['sha256'] and len(raw) == part['bytes']
        assert struct.unpack('<4sII', raw[:12]) == (b'BP3D', part['vertices'], part['triangles'] * 3)
    # No other label names a segment or a portal trunk.
    labels = collections.Counter(part['name'] for part in parts.values())
    assert all(count == 1 for count in labels.values()) and 'trunk of portal vein' not in labels


def test_the_builder_states_its_two_corrections_and_the_official_table_supports_the_rest():
    module, parts = builder(), manifest()['parts']
    official = collections.defaultdict(list)
    excerpt = json.loads((DOCS / 'evidence/bodyparts3d-4.0-isa-element-parts-excerpt.json').read_text())
    for line in excerpt['lines'].values():
        concept, name, element = line.split('\t')
        official[name].append(element)
    names = module.REGIONS['liver']['names']
    assert 'trunk of portal vein' not in names and names.index('pre-hepatic portal vein') < names.index('trunk of right portal vein')
    assert set(module.SOURCE_CORRECTIONS) == {'hepatovenous segment vii', 'hepatovenous segment viii'}
    for name in names:
        code = next(code for code, part in parts.items() if part['name'] == name)
        correction = module.SOURCE_CORRECTIONS.get(name)
        if correction:
            # The official table says otherwise, and the manifest records what it says and why.
            assert official[name] == correction['table_source_ids'] != correction['source_ids'] == parts[code]['source_ids']
            assert parts[code]['source_correction'] == {'official_table_source_ids': correction['table_source_ids'], 'reason': correction['reason']}
        elif name in official:
            assert official[name] == parts[code]['source_ids'] and 'source_correction' not in parts[code]
    # The official table itself lists the two trunks and the main vein by these names.
    assert official['trunk of left portal vein'] == ['FJ3102'] and official['pre-hepatic portal vein'] == ['FJ3082']
    assert official['trunk of portal vein'] == ['FJ3102', 'FJ3122'] and official['hepatovenous segment vii'] == ['FJ2409']
    assert 'BodyParts3D 4.3 object table' in manifest()['adaptations']
    # The later object table gives each object the name the atlas now shows.
    table = (ROOT / 'docs/cardiac-wall-context-review-20261016/obj2FMA-4.3.html').read_text(encoding='utf-8', errors='replace')
    later = dict(re.findall(r'<td class="art_id">([^<]*)</td>\s*<td class="rep_id">[^<]*</td>\s*<td class="cdi_name">[^<]*</td>\s*'
                            r'<td class="cdi_name_e">([^<]*)</td>', table))
    assert later['FJ2409'] == later['FJ2822'] == 'Hepatovenous segment VI'
    for code in ('FJ2823', 'FJ2824', 'FJ3082', 'FJ3102', 'FJ3122'):
        assert later[code].lower() == parts[code]['name']
    assert review()['later_object_table']['objects'] == {
        code: {'concept': re.search(r'<td class="art_id">%s</td>\s*<td class="rep_id">[^<]*</td>\s*<td class="cdi_name">([^<]*)</td>' % code, table).group(1),
               'name': later[code]} for code in ('FJ2409', 'FJ2822', 'FJ2823', 'FJ2824', 'FJ3082', 'FJ3102', 'FJ3122')}


def test_each_segment_is_its_own_mesh_and_lies_where_its_number_says():
    # BodyParts3D coordinates: -X is the body's right, -Y is anterior, +Z is up.
    at = {name: centre(code) for name, code in SEGMENTS.items()}
    assert all(at[name][0] < -40 for name in ('v', 'vi', 'vii', 'viii')) and at['ii'][0] > 0 and at['iii'][0] > 0
    assert at['vii'][2] > at['vi'][2] + 30 and at['viii'][2] > at['v'][2] + 30         # superior above inferior
    assert at['viii'][1] < at['vii'][1] - 30 and at['v'][1] < at['vi'][1] - 30         # anterior before posterior
    assert at['ii'][2] > at['iii'][2] and at['iii'][0] > at['iv'][0] > at['v'][0]      # left lateral, medial, right
    # Segments VII and VIII were one mesh of two pieces; each is now a single piece.
    assert pieces('FJ2823') == 1 and pieces('FJ2824') == 1
    # No two segment meshes fill the same box: the object the official table calls segment VII had the bounds of segment VI.
    boxes = {name: box(code) for name, code in SEGMENTS.items()}
    for first in boxes:
        for second in boxes:
            if first < second:
                assert max(abs(a - b) for a, b in zip(boxes[first], boxes[second])) > 15, (first, second)
    earlier = review()['meshes_removed']['FJ2409']['bounds']
    assert max(abs(a - b) for a, b in zip(earlier[0] + earlier[1], boxes['vi'])) < 0.4
    assert review()['measurements']['segment_vi_and_the_object_the_official_table_calls_vii_largest_bound_difference_mm'] == 0.325


def test_the_portal_vein_is_a_main_trunk_that_divides_into_a_right_and_a_left_trunk():
    main, right, left = (centre(code) for code in PORTAL)
    low, high = box('FJ3082')[2], box('FJ3082')[5]
    assert high - low > 45 and main[2] < right[2] and main[2] < left[2]                 # the main vein rises to the hilum
    assert right[0] < left[0] - 10                                                      # the right trunk lies on the body's right
    # The three meshes meet at the top of the main vein.
    assert nearest('FJ3082', 'FJ3122') < 1 and nearest('FJ3082', 'FJ3102') < 1 and nearest('FJ3122', 'FJ3102') < 1
    assert abs(box('FJ3122')[2] - high) < 8 and abs(box('FJ3102')[2] - high) < 8
    measured = review()['measurements']['nearest_distance_mm']
    assert measured == {'pre-hepatic portal vein to trunk of left portal vein': round(nearest('FJ3082', 'FJ3102'), 2),
                        'pre-hepatic portal vein to trunk of right portal vein': round(nearest('FJ3082', 'FJ3122'), 2),
                        'trunk of left portal vein to trunk of right portal vein': round(nearest('FJ3122', 'FJ3102'), 2)}
    assert all(pieces(code) == 1 for code in PORTAL)


def test_the_split_meshes_hold_exactly_the_geometry_delivered_before():
    record = review()
    removed = record['meshes_removed']
    assert set(removed) == set(REMOVED) and set(record['meshes_added']) == set(ADDED)
    for code, sources in (('FMA15746', ['FJ2823', 'FJ2824']), ('FMA14329', ['FJ3102', 'FJ3122'])):
        assert removed[code]['source_ids'] == sources == record['same_geometry'][code]['from']
        joined = link.united(*((ATLAS / (source + '.bin')).read_bytes() for source in sources))
        assert sha(joined) == removed[code]['sha256'] == record['same_geometry'][code]['reproduced_sha256'] and len(joined) == removed[code]['bytes']
        # In the other order the bytes differ, so the check is not vacuous.
        assert sha(link.united(*((ATLAS / (source + '.bin')).read_bytes() for source in reversed(sources)))) != removed[code]['sha256']
    for code in ADDED:
        raw = (ATLAS / (code + '.bin')).read_bytes()
        assert record['meshes_added'][code]['sha256'] == sha(raw) == manifest()['parts'][code]['sha256']
    with pytest.raises(ValueError, match='Not a BodyParts3D atlas mesh'):
        link.united(b'BP3D' + bytes(8) + b'x', (ATLAS / 'FJ2824.bin').read_bytes())


def test_only_the_liver_region_changed_and_the_registry_keeps_its_reviewed_hash():
    current = (ATLAS / 'manifest.json').read_bytes()
    earlier = link.before_liver_correction_bytes(link.MANIFEST, current)
    old, new = json.loads(earlier), json.loads(current)
    assert {key for key in new if old[key] != new[key]} == {'adaptations', 'parts', 'regions'}
    assert {key for key in new['regions'] if old['regions'][key] != new['regions'][key]} == {'liver'}
    assert set(old['parts']) - set(new['parts']) == set(REMOVED) and set(new['parts']) - set(old['parts']) == set(ADDED)
    assert all(old['parts'][code] == new['parts'][code] for code in old['parts'] if code in new['parts'])
    assert len(old['parts']) == 96 and len(new['parts']) == 98
    # The source registry is untouched. Its brain reference still pins the manifest it was reviewed against.
    registry = json.loads((ROOT / 'data/radiology/source-anatomy-references.json').read_text())
    entry, = [row for rows in registry.values() for row in rows if row['atlas'] == 'bodyparts3d']
    assert entry['family'] == 'brain' and entry['manifest_sha256'] == sha(earlier) == review()['manifest']['before_sha256']
    assert review()['manifest']['after_sha256'] == sha(current)
    # Only the corrected manifest may stand in for the reviewed one, and only for this atlas.
    assert REVIEWED_MANIFEST_SUCCESSORS == {('bodyparts3d', entry['manifest_sha256']): sha(current)}
    assert is_reviewed_manifest('bodyparts3d', current, entry['manifest_sha256'])
    assert is_reviewed_manifest('bodyparts3d', earlier, entry['manifest_sha256'])
    assert not is_reviewed_manifest('bodyparts3d', current + b'\n', entry['manifest_sha256'])
    assert not is_reviewed_manifest('bp3d-sella-4.3', current, entry['manifest_sha256'])
    assert not is_reviewed_manifest('bodyparts3d', current, '0' * 64)
    # The brain reference shows the same meshes as before.
    for row in new['regions']['brain']['parts']:
        assert sha((ATLAS / (row['id'] + '.bin')).read_bytes()) == old['parts'][row['id']]['sha256']


def test_the_catalogue_accepts_the_corrected_manifest_and_refuses_any_other(monkeypatch):
    from primer import radiology_catalog as catalog
    from primer import source_mesh_integrity as integrity
    catalog._source_anatomy_references.cache_clear()
    assert 'ra.brain-anatomy' in catalog._source_anatomy_references()
    # Without the recorded successor, the changed manifest is refused.
    monkeypatch.setattr(integrity, 'REVIEWED_MANIFEST_SUCCESSORS', {})
    catalog._source_anatomy_references.cache_clear()
    with pytest.raises(ValueError, match='Source anatomy manifest changed'):
        catalog._source_anatomy_references()
    monkeypatch.undo()
    catalog._source_anatomy_references.cache_clear()
    assert catalog._source_anatomy_references()


def test_the_liver_steps_highlight_the_corrected_meshes():
    from primer.curriculum import Curriculum
    from primer.radiology_catalog import detail, mesh_region, resolve
    curriculum = Curriculum()
    region = [row['id'] for row in manifest()['regions']['liver']['parts']]
    for identifier in LIVER:
        ref = detail(curriculum, resolve(identifier))['radiology_reference']
        assert mesh_region(ref['spatial_model']['family']) == 'liver'
        steps = ref['walkthrough']['steps']
        assert len(steps) == 5 and all(set(step['parts']) <= set(region) for step in steps)
        for step in steps:
            if step['landmark'] == 'segments':
                assert step['parts'][:8] == list(SEGMENTS.values())
            if any(code in step['parts'] for code in PORTAL):
                at = step['parts'].index(PORTAL[0])
                assert step['parts'][at:at + 3] == PORTAL
        assert [step['landmark'] for step in steps] == ['segments'] * 4 + ['portal'] and PORTAL[0] in steps[4]['parts']
    for path in sorted((ROOT / 'data/radiology/reporting-steps').glob('*.json')):
        assert not any('"%s"' % code in path.read_text() for code in REMOVED)


def test_the_inverse_restores_each_pinned_file_exactly_and_rejects_other_bytes():
    receipt = json.loads(link.PROOF.read_text())
    assert sha(link.PROOF.read_bytes()) == link.PIN and set(receipt) == link.PATHS
    for path in sorted(link.PATHS):
        raw = (ROOT / path).read_bytes()
        assert sha(raw) == receipt[path]['after']
        earlier = link.before_liver_correction_bytes(path, raw)
        assert sha(earlier) == receipt[path]['before'] != receipt[path]['after']
        assert link.before_liver_correction_bytes(path, earlier) == earlier
        assert link.before_liver_correction_bytes(path, raw + b'\n') == raw + b'\n'
    assert link.before_liver_correction_bytes('web/app.js', b'anything') == b'anything'
    # The earlier steps listed the three removed meshes and none of the new ones.
    earlier_steps = link.before_liver_correction_bytes(link.STEPS, (ROOT / link.STEPS).read_bytes()).decode()
    assert all('"%s"' % code in earlier_steps for code in REMOVED) and not any('"%s"' % code in earlier_steps for code in ADDED)
    # The catalogue's only change is the line that accepts the corrected manifest.
    changes = receipt[link.CATALOGUE]['changes']
    assert len(changes) == 2 and all('is_reviewed_manifest' in change['after'] and 'is_reviewed_manifest' not in change['before'] for change in changes)
    # The requirements file's only change is the two liver contract fingerprints.
    changes = receipt[link.REQUIREMENTS]['changes']
    assert sorted((re.search(r'[0-9a-f]{64}', change['before']).group(), re.search(r'[0-9a-f]{64}', change['after']).group()) for change in changes) \
        == sorted((row['before'], row['after']) for row in link.CONTRACTS.values())
    # The chain hands over to the links that were newest before it.
    remaining = json.loads((ROOT / 'docs/remaining-reporting-inventories-20261116/inverse.json').read_text())
    assert receipt[link.REQUIREMENTS]['before'] == remaining['after_sha256']
    lynos = json.loads((ROOT / 'docs/lynos-pat9-source-review/runtime-inverse.json').read_text())
    assert receipt[link.SCOPE]['before'] == lynos[link.SCOPE]['after']
    from tools.lynos_pat9_runtime_compatibility import before_lynos_pat9_bytes
    assert sha(before_lynos_pat9_bytes(link.SCOPE, (ROOT / link.SCOPE).read_bytes())) == lynos[link.SCOPE]['before']
    from tools.anatomy_sources.expand_remaining_requirements import before_remaining_inventories
    assert sha(before_remaining_inventories((ROOT / link.REQUIREMENTS).read_bytes())) == remaining['before_sha256']


def test_the_two_liver_contracts_restore_to_their_earlier_fingerprints():
    from primer.curriculum import Curriculum
    from primer.radiology_catalog import detail, resolve
    from tools.check_radiology_fidelity import digest
    from tools.hippunfold_runtime_compatibility import restore_prior_contract, restore_prior_contracts
    curriculum = Curriculum()
    requirements = {row['investigation_id']: row for row in json.loads((ROOT / link.REQUIREMENTS).read_text())['investigations']}
    for identifier in LIVER:
        ref = detail(curriculum, resolve(identifier))['radiology_reference']
        contract = {key: ref.get(key) for key in ('reporting', 'report_templates', 'walkthrough', 'reading')}
        row = link.CONTRACTS[identifier]
        assert digest(contract) == link.digest(contract) == row['after'] == requirements[identifier]['source_contract_sha256']
        earlier = link.before_liver_correction_contract(identifier, contract)
        assert digest(earlier) == row['before'] and restore_prior_contract(identifier, contract) == earlier
        assert {key for key in contract if contract[key] != earlier[key]} == {'walkthrough'}
        assert [step['parts'] for step in earlier['walkthrough']['steps']] != [step['parts'] for step in contract['walkthrough']['steps']]
        assert all({k: v for k, v in old.items() if k != 'parts'} == {k: v for k, v in new.items() if k != 'parts'}
                   for old, new in zip(earlier['walkthrough']['steps'], contract['walkthrough']['steps']))
        # A contract that is not the recorded one is returned untouched.
        other = dict(contract, reading=['changed'])
        assert link.before_liver_correction_contract(identifier, other) is other
    assert link.before_liver_correction_contract('ra.brain-anatomy', {'walkthrough': {}}) == {'walkthrough': {}}
    hashes = {identifier: row['after'] for identifier, row in link.CONTRACTS.items()}
    assert link.before_liver_correction_contract_hashes(dict(hashes, other='x')) == dict(
        {identifier: row['before'] for identifier, row in link.CONTRACTS.items()}, other='x')
    assert restore_prior_contracts(hashes) == {identifier: row['before'] for identifier, row in link.CONTRACTS.items()}
    # A requirement record restores to the fingerprint it carried, and to nothing else.
    for identifier in LIVER:
        earlier = link.before_liver_correction_inventory(requirements[identifier])
        assert earlier['source_contract_sha256'] == link.CONTRACTS[identifier]['before'] and list(earlier) == list(requirements[identifier])
        assert {key for key in earlier if earlier[key] != requirements[identifier][key]} == {'source_contract_sha256'}
        assert link.before_liver_correction_inventory(earlier) is earlier
    other = requirements['ra.brain-anatomy']
    assert link.before_liver_correction_inventory(other) is other


def test_the_delivery_reviews_and_the_attribution_describe_the_delivered_atlas():
    current = sha((ATLAS / 'manifest.json').read_bytes())
    delivery = json.loads((ROOT / 'docs/fedbca-bladder-source-review/current-source-delivery-review.json').read_text())
    files = {row['path']: row for row in delivery['renewal']['verified_current_source_files']}
    assert files['web/anatomy/bodyparts3d/manifest.json']['sha256'] == current
    for code in ADDED:
        assert files['web/anatomy/bodyparts3d/%s.bin' % code]['sha256'] == manifest()['parts'][code]['sha256']
    assert not any('web/anatomy/bodyparts3d/%s.bin' % code in files for code in REMOVED)
    lesson = json.loads((ROOT / 'docs/bladder-anatomy-fidelity-review/current-source-model-lesson-delivery-review.json').read_text())
    assert current in json.dumps(lesson)
    note = (ATLAS / 'ATTRIBUTION.md').read_text()
    assert 'Corrections to the official table' in note and 'FJ2823' in note and 'FJ2409' in note and 'pre-hepatic portal vein' in note
    assert 'CC Attribution 4.0 International' in note
