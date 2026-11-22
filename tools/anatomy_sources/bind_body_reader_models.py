"""Record the body readers' label meshes in the radiology evidence ledger and bind them to the structures their labels name.

The brain readers' label meshes were recorded on 2026-11-19 (docs/reader-model-bindings-20261119). The body readers show further
3D models that no evidence record covered: BodyParts3D organ and vessel meshes, segment and region labels of source MRI and CT
cases, ColonVessels vessel segments, HRA bladder regions and the LyNoS mediastinal anatomy. On 2026-11-19 the project owner asked
for the body readers' 3D models to be bound. A mesh gets a record only when it binds. A mesh binds a requirement when:

- the reader that shows the mesh is shown in the requirement's investigation (review ``readers``, checked by a test against the
  app and the catalog);
- the mesh's own source label names the requirement: in its own words, in another name, or as one member of a group the
  requirement names (every pair is listed with its reason in the review; removing one makes this tool refuse);
- the requirement leaf is the structure itself (no parts), the part the label names, the part that is the structure's own body
  (``body_parts``), or one member of a named group. A whole is never bound to a requirement that names its parts, and a part is
  never bound to its whole;
- the requirement is anatomy: a leaf whose context asks for an example of pathology is never bound to these anatomy sources;
- a leaf that names a lumen is bound only to a source whose segmentation shows the opacified lumen (``lumen_sources``);
- the source's population fits the investigation: adult sources are not bound in paediatric or neonatal investigations
  (``population_limits``), and a source the review excludes as a whole is not bound at all (``unbound_sources``: the pregnancy
  cervix atlases, the simulation boundaries, and the labels an earlier source review limits to context);
- the geometry is what the label says. A source object whose label disagrees with where it lies, or whose extent is wider than
  its label, is not bound (``source_findings``; the tests measure each finding and check every recorded BodyParts3D label against
  the later object table);
- a side the label states agrees with the requirement and with where the decoded mesh lies. A body side is checked against the
  source's fitted midsagittal plane and the mirror mesh. Where right and left name halves of one organ (the hepatic veins and
  ducts, the atria, the ventricles' papillary muscles, the valve cusps), the mesh must lie on that side of its named partner;
- the fidelity checker finds no conflict.

Coverage is always partial. Nothing here is a clinical approval, and no radiologist has reviewed the bindings.
"""
import gzip
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources import bind_reader_models as brain  # noqa: E402
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second  # noqa: E402
from tools.anatomy_sources import bind_unlocked_figures as unlocked  # noqa: E402

EVIDENCE = ROOT / 'data/radiology/radiology-asset-evidence.json'
DOCS = ROOT / 'docs/body-reader-model-bindings-20261119'
REVIEW, RECEIPT = DOCS / 'review.json', DOCS / 'inverse.json'
ANATOMY = ROOT / 'web/anatomy'
BASES = brain.BASES
EVIDENCE_KINDS = brain.EVIDENCE_KINDS
EACH_SIDE = brain.EACH_SIDE
INSERT_BEFORE = brain.INSERT_BEFORE
SUFFIXES = ('-review-buffer.bin.gz', '.mesh.gz', '.bin.gz', '.bin')
FORMATS = {
    'bp3d': 'BP3D binary: 12-byte header (magic, vertex count, index count), float32 positions, float32 normals, uint32 triangle indices',
    'raw': 'gzip: float32 positions, then uint32 triangle indices; counts from the source manifest',
}
LUMEN_WORDS = ('lumen', 'lumina', 'luminal')
sha = brain.sha
words = brain.words
requirement_leaves = brain.requirement_leaves
stated_side = brain.stated_side


def asset_id(key):
    """The record identifier: the mesh path without its encoding suffix, joined with hyphens and without a repeated directory."""
    directory, rest = key.split('/', 1)
    for suffix in SUFFIXES:
        if rest.endswith(suffix):
            rest = rest[:-len(suffix)]
            break
    rest = rest.removeprefix(directory + '-').replace('/', '-')
    return directory + '-' + rest


def inventory(review):
    """Every label mesh the review's body readers show: 'directory/path' -> atlas, label, code, format, side and investigations."""
    out = {}

    def add(reader, key, row, investigations):
        if key in out:
            raise ValueError('One mesh file listed twice: ' + key)
        if not (ANATOMY / key).is_file():
            raise ValueError('Mesh file missing: ' + key)
        out[key] = dict(row, reader=reader, atlas=review['readers'][reader]['atlas'], side=stated_side(row['label']),
                        investigations=sorted(set(investigations)))

    for reader, spec in review['readers'].items():
        kind = spec['kind']
        if kind == 'bodyparts3d':
            manifest = json.loads((ANATOMY / spec['manifest']).read_text())
            for code, part in manifest['parts'].items():
                regions = [name for name, region in manifest['regions'].items()
                           if any((item['id'] if isinstance(item, dict) else item) == code for item in region['parts'])]
                if not set(regions) & set(spec['regions']):
                    continue  # the MSK regions belong to the MSK ledger
                shown = {investigation for region in regions for investigation in spec['regions'].get(region, [])}
                add(reader, spec['directory'] + '/' + part['file'].split('/')[-1],
                    dict(label=part['name'], code=code, format='bp3d', regions=sorted(regions)), shown)
        elif kind == 'surfaces':
            for case in spec.get('cases') or ['']:
                folder = '/'.join(item for item in (spec['directory'], case) if item)
                for row in json.loads((ANATOMY / folder / 'surfaces.json').read_text()):
                    label = row['name'].split(' · ')[0] if spec.get('label_before_dot') else row['name']
                    add(reader, folder + '/' + row['file'], dict(label=label, code=str(row.get('label') or row.get('sourceLabel')),
                                                                 format='raw', vertices=row['vertices'], triangles=row['triangles'],
                                                                 **({'case': case} if case else {})), spec['investigations'])
        elif kind == 'segments':
            for phase in spec['phases']:
                for row in json.loads((ANATOMY / spec['directory'] / phase / 'surfaces.json').read_text()):
                    segment = '%s %d:%d' % (phase, row['sourceSegment']['layer'], row['sourceSegment']['value'])
                    shown = [investigation for investigation, segments in spec['segments'].items() if segments == 'all' or segment in segments]
                    add(reader, spec['directory'] + '/' + row['file'].removeprefix('../'),
                        dict(label=row['sourceSegment']['name'], code=segment, format='raw', vertices=row['vertices'],
                             triangles=row['triangles']), shown)
        elif kind == 'parts':
            manifest = json.loads((ANATOMY / spec['manifest']).read_text())
            parts = manifest['parts']
            for code, part in (parts.items() if isinstance(parts, dict) else ((item['id'], item) for item in parts)):
                if 'buffer_file' in part:
                    add(reader, spec['directory'] + '/' + part['buffer_file'], dict(label=part['label'], code=code, format='raw',
                                                                                   vertices=part['vertices'], triangles=part['triangles']),
                        spec['investigations'])
                else:
                    add(reader, spec['directory'] + '/' + part['file'].split('/app/anatomy/' + spec['directory'] + '/')[-1],
                        dict(label=part.get('source_label') or part['label'], code=code, format='bp3d'), spec['investigations'])
        else:
            raise ValueError('Unknown reader kind: ' + kind)
    return out


def positions(key, mesh):
    """The decoded vertex positions of one mesh file, with its vertex and triangle counts."""
    raw = (ANATOMY / key).read_bytes()
    if key.endswith('.gz'):
        raw = gzip.decompress(raw)
    if mesh['format'] == 'bp3d':
        magic, vertices, indices = struct.unpack('<4sII', raw[:12])
        if magic != b'BP3D' or indices % 3 or len(raw) != 12 + vertices * 24 + indices * 4:
            raise ValueError('Not a BP3D mesh: ' + key)
        triangles, start = indices // 3, 12
    else:
        vertices, triangles, start = mesh['vertices'], mesh['triangles'], 0
        if len(raw) != vertices * 12 + triangles * 12:
            raise ValueError('Mesh size does not match its manifest counts: ' + key)
    values = struct.unpack('<%df' % (vertices * 3), raw[start:start + vertices * 12])
    return list(zip(values[0::3], values[1::3], values[2::3])), vertices, triangles


def frame_of(mesh, review):
    return review['readers'][mesh['reader']].get('frame')


def reader_of(key, review):
    """The reader that delivers a mesh file."""
    found = [name for name, spec in review['readers'].items() if key.startswith(spec['directory'] + '/')]
    if len(found) != 1:
        raise ValueError('Mesh belongs to no reader, or to several: ' + key)
    return found[0]


def midline(name, review, meshes, cache):
    """The source's midsagittal plane x = a + b*y + c*z, fitted to the vertices of its thin midline structures (or x = a)."""
    if ('plane', name) not in cache:
        frame = review['frames'][name]
        points = [point for key in frame['midline_meshes'] for point in positions(key, meshes[key])[0]]
        if frame['fit'] == 'constant':
            # Midline structures close together cannot fix a tilt; the plane is then x = their mean position.
            cache[('plane', name)] = (sum(x for x, _, _ in points) / len(points), 0.0, 0.0)
            return cache[('plane', name)]
        sums, target = [[0.0] * 3 for _ in range(3)], [0.0] * 3
        for x, y, z in points:
            row = (1.0, y, z)
            for i in range(3):
                target[i] += row[i] * x
                for j in range(3):
                    sums[i][j] += row[i] * row[j]
        cache[('plane', name)] = tuple(brain.solve(sums, target))
    return cache[('plane', name)]


def measure(key, meshes, review, cache):
    """Vertex and triangle counts and, in a frame, the share of vertices right of the midline and the centroid offset (mm)."""
    if key not in cache:
        mesh = meshes[key]
        points, vertices, triangles = positions(key, mesh)
        found = {'vertices': vertices, 'triangles': triangles}
        name = frame_of(mesh, review)
        if name:
            frame = review['frames'][name]
            a, b, c = midline(name, review, meshes, cache)
            sign = {'+x': 1.0, '-x': -1.0}[frame['right']] * frame['unit_mm']
            values = [sign * (x - (a + b * y + c * z)) for x, y, z in points]
            found.update(share_right=round(sum(1 for value in values if value > 0) / len(values), 4),
                         centroid_mm=round(sum(values) / len(values), 2))
        cache[key] = found
    return cache[key]


def mesh_side(key, meshes, review, cache):
    """Where the decoded mesh lies, and whether that supports its label's side.

    A body side holds when most of the mesh lies on that side of the fitted midsagittal plane and its centroid lies on that side
    of its mirror mesh's centroid. An organ half (the label's side word names a half of one organ) holds when the centroid lies on
    that side of its named partner's centroid; the organ itself may lie across the midline. A class that holds both sides must have
    at least EACH_SIDE of its vertices on each side.
    """
    measured = measure(key, meshes, review, cache)
    mesh, partner = meshes[key], review['partners'].get(key)
    if 'share_right' not in measured:
        if mesh['side'] or partner:
            raise ValueError('A sided mesh needs a source frame: ' + key)
        return dict(measured, located='not_measured', partner=None, partner_centroid_mm=None, partner_kind=None)
    other = None
    if partner:
        if partner['partner'] not in meshes or not mesh['side'] or meshes[partner['partner']]['side'] != {'right': 'left', 'left': 'right'}[mesh['side']]:
            raise ValueError('A partner must be a mesh of the same reader that states the other side: ' + key)
        other = measure(partner['partner'], meshes, review, cache)['centroid_mm']
    right, centroid, side = measured['share_right'], measured['centroid_mm'], mesh['side']
    if side:
        apart = other is None or (centroid > other if side == 'right' else centroid < other)
        if partner and partner['kind'] == 'organ_half':
            located = side if apart else 'contradicts_label'
        else:
            on_side = right > 0.5 if side == 'right' else right < 0.5
            located = side if on_side and apart else 'contradicts_label'
    else:
        located = 'both' if min(right, 1 - right) >= EACH_SIDE else 'right' if right > 0.5 else 'left'
    return dict(measured, located=located, partner=partner and partner['partner'], partner_centroid_mm=other,
                partner_kind=partner and partner['kind'])


def context_targets(requirement):
    """The requirement's context constraints as a list."""
    targets = requirement.get('context_requirements', [])
    return [targets] if isinstance(targets, dict) else list(targets)


def label_word_in(quote, label_word):
    """The listed label words appear in the quote as whole words: segment ii is not segment iii, and segment 2 is not 23."""
    return re.search(r'(?<![a-z0-9])' + re.escape(label_word.lower()) + r'(?![a-z0-9])', quote.lower()) is not None


def evidence_fits(row, name, pairs):
    """True when the row's evidence is in its label and in the requirement's full name."""
    if not brain.evidence_fits(row, name, pairs):
        return False
    return row['evidence'] == 'own_word' or label_word_in(row['quote'], row[row['evidence']]['label_word'])


def side_basis_for(mesh, requirement, name, located, partner_kind):
    """The side basis the row must record, or a ValueError naming the disagreement."""
    wanted = brain.requirement_side(requirement, name)
    if mesh['side']:
        if located != mesh['side'] or (wanted and wanted != mesh['side']):
            raise ValueError('Side of the label, the mesh and the requirement disagree')
        return ('organ_' if partner_kind == 'organ_half' else '') + mesh['side']
    if requirement['laterality'] == 'bilateral':
        if located != 'both':
            raise ValueError('A bilateral requirement needs a mesh that lies on both sides')
        return 'bilateral'
    if requirement['laterality'] in ('left', 'right'):
        if located != 'both':
            raise ValueError('An unsided label must lie on both sides to bind a sided requirement')
        return 'both'
    # A side word in the name of a requirement without a body side names a half of an organ (the left lateral liver segments).
    return 'unsided'


def basis(row, review):
    source = review['sources'][row['atlas']]['title']
    text = 'Source label “%s” of the %s, shown in this investigation’s reader.' % (row['quote'], source)
    if row['evidence'] != 'own_word':
        pair = row[row['evidence']]
        reason = review[row['evidence'] + '_reasons']['%s>%s' % (pair['label_word'], pair['requirement_word'])]
        text += ' %s%s.' % (reason[0].upper(), reason[1:])
    part = row['name'].split(': ', 1)[-1].lower()
    if row['leaf_basis'] == 'body_part' and row['evidence'] == 'kind_of':
        text += (' The requirement names a group; the label names one member, and this part (“%s”) is that member’s own body, '
                 'which the labelled mesh shows as the source delineates it.' % part)
    elif row['leaf_basis'] == 'body_part':
        text += (' The label names the structure, and this part (“%s”) is the structure’s own body, which the labelled mesh shows as '
                 'the source delineates it; the mesh delineates no other part.' % part)
    else:
        text += {'structure': ' The label names this structure.', 'named_part': ' The label names this part.',
                 'group_member': ' The requirement names a group or union; the label names one member of it.'}[row['leaf_basis']]
    if any(word in words(part) for word in LUMEN_WORDS):
        text += ' ' + review['lumen_sources'][row['atlas']]
    text += {'right': ' The label states the right side, and the mesh lies right of the source midline and of its left-side mirror.',
             'left': ' The label states the left side, and the mesh lies left of the source midline and of its right-side mirror.',
             'organ_right': ' The side word names the right half of the organ, not a side of the body; the mesh lies right of its left-named partner.',
             'organ_left': ' The side word names the left half of the organ, not a side of the body; the mesh lies left of its right-named partner.',
             'both': ' The source class holds both sides; its mesh lies on both sides of the source midline, so the side is not stated.',
             'bilateral': ' The midline structure’s mesh lies on both sides of the source midline, so the record states both sides.',
             'unsided': ''}[row['side_basis']]
    frame = review['readers'][reader_of(row['mesh'], review)].get('frame')
    if row['side_basis'] != 'unsided' and review['frames'][frame]['axes_basis'] == 'convention':
        text += ' The axes are the source release’s convention; this organ’s own anatomy cannot check them.'
    return text + ' One source-labelled mesh; the full extent and boundaries of the named anatomy are not established.'


def record(key, mesh, rows, review, geometry, leaves):
    source = review['sources'][mesh['atlas']]
    path = ANATOMY / key
    raw = path.read_bytes()
    context = dict(source['source_context'])
    sided = any(requirement['laterality'] in ('left', 'right') for row in rows for requirement in leaves[row['structure_id']].values())
    if mesh['side'] and (geometry['partner_kind'] != 'organ_half' or sided):
        # An organ half states its side only where a requirement of that side needs it; the side then names the organ's half.
        context['laterality'] = mesh['side']
    elif any(row['side_basis'] == 'bilateral' for row in rows):
        if any(row['side_basis'] == 'both' for row in rows):
            raise ValueError('One mesh cannot state both sides and bind a requirement of one side: ' + key)
        context['laterality'] = 'bilateral'
    directory = review['readers'][mesh['reader']]['directory']
    measured = {field: geometry[field] for field in ('share_right', 'centroid_mm') if field in geometry}
    return {
        'id': asset_id(key), 'kind': 'model', 'name': mesh['label'],
        'local_path': str(path.relative_to(ROOT)), 'sha256': sha(raw),
        'regions': sorted({row['region'] for row in rows}),
        'investigation_ids': sorted({investigation for row in rows for investigation in row['investigations']}),
        'structure_ids': [row['structure_id'] for row in rows],
        'source_context': context,
        'source': {'url': source['url'], 'license': source['license']},
        'geometry': dict({'format': FORMATS[mesh['format']], 'vertices': geometry['vertices'], 'triangles': geometry['triangles'],
                          'source_label': mesh['label'], 'source_label_code': mesh['code']},
                         **({'source_frame': frame_of(mesh, review), 'source_frame_axes_basis': review['frames'][frame_of(mesh, review)]['axes_basis'],
                             'share_of_vertices_right_of_source_midline': measured['share_right'],
                             'centroid_mm_right_of_source_midline': measured['centroid_mm']} if measured else {}),
                         **({'partner_mesh': 'web/anatomy/' + geometry['partner'], 'partner_kind': geometry['partner_kind'],
                             'partner_centroid_mm_right_of_source_midline': geometry['partner_centroid_mm']} if geometry['partner'] else {})),
        'requirement_coverage': {row['structure_id']: {'extent': 'partial', 'basis': basis(row, review)} for row in rows},
        # A reader review covers its whole directory unless a separate review covers this mesh.
        'visual_review': dict(source['visual_review'].get(key) or source['visual_review'][directory], sha256=sha(raw)),
        'anatomical_review': {'status': 'pending',
                              'reason': 'A source label boundary is not an independently validated anatomical boundary; no radiologist has reviewed this binding.'},
    }


def plan():
    """The new records, checked row by row. Refuses any row that breaks a rule."""
    from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage
    from tools.anatomy_sources.structure_display_names import display_structure_name
    review = json.loads(REVIEW.read_text())
    meshes = inventory(review)
    leaves, names, structures = requirement_leaves()
    pairs = {'another_name': review['another_name_pairs'], 'kind_of': review['kind_of_pairs']}
    for kind in pairs:
        if {'%s>%s' % (pair['label_word'], pair['requirement_word']) for pair in pairs[kind]} != set(review[kind + '_reasons']):
            raise ValueError('Every %s pair needs exactly one reason' % kind)
    existing = {item['id'] for item in json.loads(EVIDENCE.read_bytes())['assets']}
    by_mesh, cache, geometry = {}, {}, {}
    for row in review['accepted']:
        problem = lambda text: ValueError('%s / %s: %s' % (row['mesh'], row['structure_id'], text))  # noqa: E731
        mesh = meshes.get(row['mesh'])
        if mesh is None:
            raise problem('Mesh is not shown by the review’s readers')
        if row['quote'] != mesh['label'] or row['atlas'] != mesh['atlas']:
            raise problem('Label is not the mesh’s source label')
        if mesh['atlas'] in review['unbound_sources']:
            raise problem('Source is not bound: ' + review['unbound_sources'][mesh['atlas']])
        if row['asset_id'] != asset_id(row['mesh']):
            raise problem('Record identifier does not follow the mesh file')
        if row['structure_id'] not in leaves:
            raise problem('Requirement leaf or its name is not recorded')
        requirement = next(iter(leaves[row['structure_id']].values()))
        if display_structure_name(row['name'], requirement['laterality']) != names[row['structure_id']]:
            raise problem('Requirement leaf or its name is not recorded')
        shown = sorted(investigation for investigation in leaves[row['structure_id']] if investigation in mesh['investigations'])
        if not shown or row['investigations'] != shown:
            raise problem('Requirement is not in an investigation whose reader shows the mesh')
        if any(target.get('purpose') == 'pathology_example' for investigation in shown
               for target in context_targets(leaves[row['structure_id']][investigation])):
            raise problem('A requirement for an example of pathology is not bound to an anatomy source')
        stage = (review['sources'][mesh['atlas']]['source_context'].get('population') or {}).get('life_stage')
        for investigation in shown:
            limit = review['population_limits'].get(investigation)
            if limit and stage != limit['life_stage']:
                raise problem('Source population does not fit the investigation: ' + limit['reason'])
        if row['evidence'] not in EVIDENCE_KINDS or not evidence_fits(row, names[row['structure_id']], pairs):
            raise problem('Label does not name the requirement')
        part = row['name'].split(': ', 1)[1] if ': ' in row['name'] else ''
        is_part = requirement['parent_id'] != row['structure_id']
        named = words(row['term'] if row['evidence'] == 'own_word' else row[row['evidence']]['requirement_word'])
        # A structure without parts is bound as itself, or, when it names a group or union, by one of its members.
        if (row['leaf_basis'] not in BASES
                or (is_part and row['leaf_basis'] == 'structure')
                or (not is_part and row['leaf_basis'] not in ('structure', 'group_member'))
                or (row['leaf_basis'] == 'body_part') != (part.lower() in review['body_parts'])
                or (row['leaf_basis'] == 'named_part' and not any(len(word) > 3 and unlocked.named(word, words(part)) for word in named))
                or (row['leaf_basis'] == 'group_member' and row['evidence'] != 'kind_of'
                    and not (' and ' in structures[row['structure_id']] or '/' in structures[row['structure_id']]))):
            raise problem('Requirement is not the kind of leaf recorded')
        if any(word in words(part) for word in LUMEN_WORDS) and row['atlas'] not in review['lumen_sources']:
            raise problem('Only a source whose segmentation shows the opacified lumen may bind a lumen')
        if row['mesh'] not in geometry:
            geometry[row['mesh']] = mesh_side(row['mesh'], meshes, review, cache)
        found = geometry[row['mesh']]
        try:
            side_basis = side_basis_for(mesh, requirement, row['name'], found['located'], found['partner_kind'])
        except ValueError as error:
            raise problem(str(error)) from None
        if row['side_basis'] != side_basis or row['mesh_side'] != found['located']:
            raise problem('Side basis is not what the mesh shows')
        if row['region'] not in review['regions']:
            raise problem('Unknown region')
        by_mesh.setdefault(row['mesh'], []).append(row)
    records = []
    for key, rows in by_mesh.items():
        if len({row['structure_id'] for row in rows}) != len(rows) or asset_id(key) in existing:
            raise ValueError('Repeated binding or existing record: ' + key)
        item = record(key, meshes[key], rows, review, geometry[key], leaves)
        for row in rows:
            for investigation in row['investigations']:
                requirement = leaves[row['structure_id']][investigation]
                if inspect_binding(item, requirement) != [] or inspect_requirement_coverage(item, requirement) != ['requirement_coverage_partial']:
                    raise ValueError('%s / %s: The checker refuses the binding' % (key, row['structure_id']))
        records.append(item)
    unrecorded = set(meshes) - set(by_mesh)
    if set(review['not_recorded']) != unrecorded or not all(review['not_recorded'].values()):
        raise ValueError('Every other mesh of the readers needs a reason')
    for kind in pairs:
        used = [row[kind] for row in review['accepted'] if row['evidence'] == kind]
        if any(pair not in used for pair in pairs[kind]):
            raise ValueError('A listed %s pair is used by no binding' % kind)
    return sorted(records, key=lambda item: item['id'])


def apply(raw, records):
    return brain.apply(raw, records)


def bind():
    raw = EVIDENCE.read_bytes()
    records = plan()
    after, edits = apply(raw, records)
    old, new = json.loads(raw), json.loads(after)
    if new['assets'] != old['assets'] + records or {k: v for k, v in old.items() if k != 'assets'} != {k: v for k, v in new.items() if k != 'assets'}:
        raise ValueError('Unintended change to the evidence file')
    RECEIPT.write_text(json.dumps({
        'path': 'data/radiology/radiology-asset-evidence.json', 'before_sha256': sha(raw), 'after_sha256': sha(after),
        'edits': edits, 'clinical_approval': False, 'extends_historical_approval': False}, indent=1, ensure_ascii=False) + '\n')
    EVIDENCE.write_bytes(after)
    return records


def before_body_reader_model_records(raw):
    """Exact earlier bytes of the evidence file; any other state is returned unchanged."""
    receipt = json.loads(RECEIPT.read_text())
    if second.sha(raw) != receipt['after_sha256']:
        return raw
    shift = sum(len(new.encode()) - len(old.encode()) for _, old, new in receipt['edits'])
    for start, old, new in sorted(receipt['edits'], reverse=True):
        shift -= len(new.encode()) - len(old.encode())
        at = start + shift
        if raw[at:at + len(new.encode())] != new.encode():
            raise ValueError('Body reader model record literal changed')
        raw = raw[:at] + old.encode() + raw[at + len(new.encode()):]
    if second.sha(raw) != receipt['before_sha256']:
        raise ValueError('Body reader model record inverse changed unrelated bytes')
    return raw


if __name__ == '__main__':
    made = bind()
    print(len(made), 'records;', sum(len(item['structure_ids']) for item in made), 'bindings')
