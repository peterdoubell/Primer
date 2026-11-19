"""Record the brain readers' label meshes in the radiology evidence ledger and bind them to the structures their labels name.

Both evidence ledgers' stored 3D models were reviewed on 2026-11-18 (docs/model-bindings-20261118,
docs/msk-model-bindings-20261118). The brain readers show further 3D models that no evidence record covered: the exact
label-boundary meshes of the SPL/NAC brain atlas, holiAtlas and HippUnfold. On 2026-11-19 the project owner asked again
for the 3D models to be bound. A mesh gets a record only when it binds. A mesh binds a requirement when:

- the reader that shows the mesh is shown in the requirement's investigation (review ``readers``, recomputed by a test
  from the catalog's source inspectors);
- the mesh's own source label names the requirement: in its own words, in another name, or as one member of a group
  the requirement names (every pair is listed with its reason in the review; removing one makes this tool refuse);
- the requirement leaf is the structure itself (no parts), the part the label names, the part that is the structure's
  own body (``body_parts``), or one member of a named group or union. A whole is never bound to a requirement that names
  its parts, and a part is never bound to its whole;
- a side the label states agrees with the requirement and with where the decoded mesh lies against the source's own
  midline. A source class that holds both sides is bound to a sided requirement only when its mesh lies on both sides;
- the fidelity checker finds no conflict.

Coverage is always partial. Nothing here is a clinical approval, and no radiologist has reviewed the bindings.
"""
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.anatomy_sources import bind_msk_models as msk  # noqa: E402
from tools.anatomy_sources import bind_stored_caption_assets_pass2 as second  # noqa: E402
from tools.anatomy_sources import bind_unlocked_figures as unlocked  # noqa: E402

EVIDENCE = ROOT / 'data/radiology/radiology-asset-evidence.json'
REQUIREMENTS = ROOT / 'data/radiology/non-msk-structure-requirements.json'
DOCS = ROOT / 'docs/reader-model-bindings-20261119'
REVIEW, RECEIPT = DOCS / 'review.json', DOCS / 'inverse.json'
ANATOMY = ROOT / 'web/anatomy'
BASES = ('structure', 'named_part', 'body_part', 'group_member')
EVIDENCE_KINDS = ('own_word', 'another_name', 'kind_of')
# A source class that holds both sides must have at least this share of its vertices on each side of the midline.
EACH_SIDE = 0.15
INSERT_BEFORE = '\n  ],\n  "reference_rights_assets"'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def words(text):
    return msk.words(text)


def requirement_leaves():
    """Each requirement leaf (a part, or a structure without parts) per investigation, its full name and structure name."""
    from tools.check_msk_fidelity import requirements_for
    leaves, names, structures = {}, {}, {}
    for investigation in json.loads(REQUIREMENTS.read_text())['investigations']:
        for requirement in requirements_for(investigation):
            leaves.setdefault(requirement['id'], {})[investigation['investigation_id']] = requirement
        for structure in investigation['structures']:
            names[structure['id']] = structure['name']
            structures[structure['id']] = structure['name']
            for part in structure.get('required_parts') or []:
                names[part['id']] = structure['name'] + ': ' + part['name']
                structures[part['id']] = structure['name']
    return leaves, names, structures


def stated_side(name, declared=None):
    if declared in ('Right', 'Left', 'right', 'left'):
        return declared.lower()
    found = {side for side in ('right', 'left') if side in words(name)}
    return found.pop() if len(found) == 1 else None


def inventory(review):
    """Every label mesh the review's readers show: 'directory/file' -> label, code, stated side, readers, investigations."""
    out = {}

    def add(reader, directory, file, row):
        key = directory + '/' + file
        if key in out:
            if out[key]['label'] != row['label']:
                raise ValueError('One mesh file under two labels: ' + key)
            out[key]['readers'] = sorted(set(out[key]['readers']) | {reader})
            out[key]['investigations'] = sorted(set(out[key]['investigations']) | set(review['readers'][reader]['investigations']))
            return
        out[key] = dict(row, directory=directory, file=file, readers=[reader],
                        investigations=sorted(review['readers'][reader]['investigations']))

    readers = review['readers']
    for reader in ('spl-nac-reporting', 'spl-nac-limbic', 'spl-additional-source', 'spl-epilepsy-context'):
        manifest = json.loads((ANATOMY / readers[reader]['manifest']).read_text())
        codes = None
        if reader == 'spl-epilepsy-context':
            # This reader shows one group of the reporting classes; the server redirects its mesh files to the reporting reader.
            codes = set(next(group for group in manifest['groups'] if group['id'] == manifest['defaultGroup'])['codes'])
        for row in manifest['labelMeshes']:
            if codes is not None and row['code'] not in codes:
                continue
            directory = ('spl-nac-limbic' if row.get('sharedSource') == 'spl-nac-limbic' else readers[reader]['served_from'])
            add(reader, directory, row['file'], dict(atlas='spl', label=row['name'].replace('_', ' '), code=row['code'],
                                                     side=stated_side(row['name']), faces=row['faceProvenance']['file']))
    labels = json.loads(gzip.decompress((ROOT / readers['holiatlas']['labels']).read_bytes()))
    for row in labels['sourceClasses']:
        if row.get('mesh'):
            add('holiatlas', 'holiatlas', row['mesh']['file'], dict(atlas='holiatlas', label=row['name'].strip(), code=row['code'], level='fine',
                                                                    side=stated_side(row['name'], row.get('side')),
                                                                    faces=row['mesh']['file'].replace('.mesh.gz', '-faces.bin.gz')))
    hierarchy = json.loads(gzip.decompress((ROOT / readers['holiatlas']['hierarchy']).read_bytes()))
    for level, data in hierarchy['levels'].items():
        for row in data['sourceClasses']:
            if row.get('mesh'):
                add('holiatlas', 'holiatlas', row['mesh']['file'], dict(
                    atlas='holiatlas', label=row['name'].strip(), code=row['code'], level=level, side=stated_side(row['name']),
                    faces=(row.get('facesPayload') or {}).get('file') or row['mesh']['file'].replace('.mesh.gz', '-faces.bin.gz'),
                    fine_codes=row.get('fineSourceCodes')))
    hippunfold = json.loads((ANATOMY / readers['hippunfold']['manifest']).read_text())
    for row in hippunfold['meshes']:
        add('hippunfold', 'hippunfold-hcp101006-registered', row['file'], dict(
            atlas='hippunfold', label=hippunfold['labels'][row['label']], code=row['label'], hemisphere=row['sourceHemisphereName'],
            side={'L': 'left', 'R': 'right'}[row['sourceHemisphereName']], faces=None))
    territories = json.loads((ANATOMY / readers['schirmer-vascular']['labels']).read_text())
    for row in territories['sourceClasses']:
        if row.get('mesh'):
            add('schirmer-vascular', 'schirmer-vascular', row['mesh']['file'], dict(
                atlas='schirmer', label=row['name'], code=row['code'], side=stated_side(row['name']), faces=row['facesPayload']['file']))
    return out


def positions(path):
    raw = gzip.decompress(path.read_bytes())
    magic, vertices, triangles = struct.unpack('<4sII', raw[:12])
    if magic != b'HVX1' or len(raw) != 16 + vertices * 12 + triangles * 12:
        raise ValueError('Not an HVX1 mesh: ' + str(path))
    return struct.unpack('<%df' % (vertices * 3), raw[16:16 + vertices * 12]), vertices, triangles


def world(mesh, review):
    """The decoded mesh's vertices in its source's millimetre frame (+x is the subject's right)."""
    values, vertices, triangles = positions(ANATOMY / mesh['directory'] / mesh['file'])
    points = list(zip(values[0::3], values[1::3], values[2::3]))
    if mesh['atlas'] == 'hippunfold':
        affine = next(item['affine'] for item in json.loads((ANATOMY / review['readers']['hippunfold']['manifest']).read_text())['hemispheres']
                      if item['name'] == mesh['hemisphere'])
        points = [tuple(row[0] * x + row[1] * y + row[2] * z + row[3] for row in affine[:3]) for x, y, z in points]
    return points, vertices, triangles


def solve(matrix, vector):
    """Gaussian elimination for a small square system."""
    rows = [list(row) + [value] for row, value in zip(matrix, vector)]
    size = len(rows)
    for column in range(size):
        pivot = max(range(column, size), key=lambda index: abs(rows[index][column]))
        rows[column], rows[pivot] = rows[pivot], rows[column]
        for index in range(size):
            if index != column:
                factor = rows[index][column] / rows[column][column]
                rows[index] = [a - factor * b for a, b in zip(rows[index], rows[column])]
    return [rows[index][size] / rows[index][index] for index in range(size)]


def midline(atlas, review, cache):
    """The source's own midsagittal plane x = a + b*y + c*z, fitted to the vertices of its thin midline structures."""
    if atlas not in cache:
        frame = review['frames'][atlas]
        if frame.get('midline_x') is not None:
            cache[atlas] = (frame['midline_x'], 0.0, 0.0)
        else:
            points = [point for key in frame['midline_meshes'] for point in
                      world(dict(atlas=atlas, directory=key.split('/')[0], file=key.split('/')[1]), review)[0]]
            sums = [[0.0] * 3 for _ in range(3)]
            target = [0.0] * 3
            for x, y, z in points:
                row = (1.0, y, z)
                for i in range(3):
                    target[i] += row[i] * x
                    for j in range(3):
                        sums[i][j] += row[i] * row[j]
            cache[atlas] = tuple(solve(sums, target))
    return cache[atlas]


def offsets(mesh, review, cache):
    """Each vertex's signed distance (mm along x) from the source's midsagittal plane; positive is the subject's right."""
    a, b, c = midline(mesh['atlas'], review, cache)
    points, vertices, triangles = world(mesh, review)
    return [x - (a + b * y + c * z) for x, y, z in points], vertices, triangles


def partner(key, meshes):
    """The mirror-image mesh: the same source label with the other side, in the same directory."""
    mesh = meshes[key]
    if not mesh['side']:
        return None
    other = {'right': 'left', 'left': 'right'}[mesh['side']]
    swap = lambda text: ' '.join(other.capitalize() if word == mesh['side'].capitalize() else other if word == mesh['side'] else word  # noqa: E731
                                 for word in text.split(' '))
    found = [candidate for candidate, item in meshes.items() if item['atlas'] == mesh['atlas'] and item['directory'] == mesh['directory']
             and item.get('level') == mesh.get('level') and item['label'] == swap(mesh['label'])
             and item.get('hemisphere') != mesh.get('hemisphere', object())]
    return found[0] if len(found) == 1 else None


def measure(key, meshes, review, cache):
    """A mesh's share of vertices right of its source's midsagittal plane, and its centroid offset from it (mm)."""
    if key not in cache:
        values, vertices, triangles = offsets(meshes[key], review, cache)
        cache[key] = {'share_right': round(sum(1 for value in values if value > 0) / len(values), 4),
                      'centroid_mm': round(sum(values) / len(values), 2), 'vertices': vertices, 'triangles': triangles}
    return cache[key]


def mesh_side(key, meshes, review, cache):
    """Where the decoded mesh lies against its source's midline, and whether that supports its label's side.

    A labelled side is supported when most of the mesh lies on that side of the fitted midsagittal plane and its centroid lies on
    that side of its mirror mesh's centroid. Medial structures (the cuneus, the mammillary bodies, the medial thalamic nuclei)
    touch or cross the midline, so no stricter share is asked of them; a swapped pair of labels still fails. A class that holds both
    sides must have at least EACH_SIDE of its vertices on each side.
    """
    measured = measure(key, meshes, review, cache)
    right, centroid = measured['share_right'], measured['centroid_mm']
    mirror = partner(key, meshes)
    mirror_centroid = measure(mirror, meshes, review, cache)['centroid_mm'] if mirror else None
    side = meshes[key]['side']
    if side:
        on_side = right > 0.5 if side == 'right' else right < 0.5
        apart = mirror_centroid is None or (centroid > mirror_centroid if side == 'right' else centroid < mirror_centroid)
        located = side if on_side and apart else 'contradicts_label'
    else:
        located = 'both' if min(right, 1 - right) >= EACH_SIDE else 'right' if right > 0.5 else 'left'
    return dict(measured, located=located, mirror=mirror, mirror_centroid_mm=mirror_centroid)


def evidence_fits(row, name, pairs):
    """True when the row's evidence is in its label and in the requirement's full name."""
    if row['evidence'] == 'own_word':
        term = words(row.get('term', ''))
        return bool(term) and any(len(word) > 2 for word in term) and all(
            unlocked.named(word, words(row['quote'])) and unlocked.named(word, words(name)) for word in term)
    if row['evidence'] not in ('another_name', 'kind_of'):
        return False
    pair = row[row['evidence']]
    return (pair in pairs.get(row['evidence'], []) and pair['label_word'].lower() in row['quote'].lower()
            and all(unlocked.named(word, words(name)) for word in words(pair['requirement_word'])))


def requirement_side(requirement, name):
    if requirement['laterality'] in ('left', 'right'):
        return requirement['laterality']
    return stated_side(name.split(': ', 1)[-1]) or stated_side(name.split(': ', 1)[0])


def basis(row, review):
    source = review['sources'][row['atlas']]['title']
    text = 'Source label “%s” of the %s, shown in this investigation’s reader.' % (row['quote'], source)
    if row['evidence'] != 'own_word':
        pair = row[row['evidence']]
        reason = review[row['evidence'] + '_reasons']['%s>%s' % (pair['label_word'], pair['requirement_word'])]
        text += ' %s%s.' % (reason[0].upper(), reason[1:])
    if row['leaf_basis'] == 'body_part':
        text += (' This part is the structure’s own %s, which the whole labelled mesh shows; the mesh does not delineate the other parts.'
                 % row['name'].split(': ', 1)[1].lower())
    else:
        text += {'structure': ' The label names this structure.', 'named_part': ' The label names this part.',
                 'group_member': ' The requirement names a group or union; the label names one member of it.'}[row['leaf_basis']]
    text += {'right': ' The label states the right side, and the mesh lies right of the source midline and of its left-side mirror.',
             'left': ' The label states the left side, and the mesh lies left of the source midline and of its right-side mirror.',
             'both': ' The source class holds both sides; its mesh lies on both sides of the source midline, so the side is not stated.',
             'bilateral': ' The midline structure’s mesh lies on both sides of the source midline, so the record states both sides.',
             'unsided': ''}[row['side_basis']]
    return text + ' One source-labelled mesh; the full extent and boundaries of the named anatomy are not established.'


def record(mesh, rows, review, geometry):
    source = review['sources'][mesh['atlas']]
    path = ANATOMY / mesh['directory'] / mesh['file']
    raw = path.read_bytes()
    context = dict(source['source_context'])
    if mesh['side']:
        context['laterality'] = mesh['side']
    elif any(row['side_basis'] == 'bilateral' for row in rows):
        # A bilateral requirement needs a source that states both sides; a mesh that binds a requirement of one side must not.
        if any(row['side_basis'] == 'both' for row in rows):
            raise ValueError('One mesh cannot state both sides and bind a requirement of one side: ' + rows[0]['mesh'])
        context['laterality'] = 'bilateral'
    faces = ANATOMY / mesh['directory'] / mesh['faces'] if mesh['faces'] else None
    return {
        'id': rows[0]['asset_id'], 'kind': 'model', 'name': mesh['label'],
        'local_path': str(path.relative_to(ROOT)), 'sha256': sha(raw),
        'regions': sorted({row['region'] for row in rows}),
        'investigation_ids': sorted({investigation for row in rows for investigation in row['investigations']}),
        'structure_ids': [row['structure_id'] for row in rows],
        'source_context': context,
        'source': {'url': source['url'], 'license': source['license']},
        'geometry': dict({'format': 'HVX1 gzip: little-endian header, float32 positions, uint32 triangle indices',
                          'vertices': geometry['vertices'], 'triangles': geometry['triangles'], 'source_label': mesh['label'],
                          'source_label_code': mesh['code'], 'share_of_vertices_right_of_source_midline': geometry['share_right'],
                          'centroid_mm_right_of_source_midline': geometry['centroid_mm']},
                         **({'mirror_mesh': geometry['mirror'], 'mirror_centroid_mm_right_of_source_midline': geometry['mirror_centroid_mm']}
                            if geometry['mirror'] else {}),
                         **({'faces_path': str(faces.relative_to(ROOT)), 'faces_sha256': sha(faces.read_bytes())} if faces else {})),
        'requirement_coverage': {row['structure_id']: {'extent': 'partial', 'basis': basis(row, review)} for row in rows},
        'visual_review': {'status': 'source_checked', 'sha256': sha(raw), 'reviewed_at': source['visual_reviewed_at'][mesh['directory']],
                          'evidence_path': source['visual_evidence'][mesh['directory']],
                          'scope': 'The reader review checked this mesh against every exposed cell face of its source label class.'},
        'anatomical_review': {'status': 'pending',
                              'reason': 'A source label boundary is not an independently validated anatomical boundary; no radiologist has reviewed this binding.'},
    }


def plan():
    """The new records, checked row by row. Refuses any row that breaks a rule."""
    from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage
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
        if row['asset_id'] != mesh['directory'] + '-' + mesh['file'].removesuffix('.mesh.gz'):
            raise problem('Record identifier does not follow the mesh file')
        if row['structure_id'] not in leaves or row['name'] != names[row['structure_id']]:
            raise problem('Requirement leaf or its name is not recorded')
        shown = sorted(investigation for investigation in leaves[row['structure_id']] if investigation in mesh['investigations'])
        if not shown or row['investigations'] != shown:
            raise problem('Requirement is not in an investigation whose reader shows the mesh')
        if row['evidence'] not in EVIDENCE_KINDS or not evidence_fits(row, row['name'], pairs):
            raise problem('Label does not name the requirement')
        requirement = next(iter(leaves[row['structure_id']].values()))
        part = row['name'].split(': ', 1)[1] if ': ' in row['name'] else ''
        is_part = requirement['parent_id'] != row['structure_id']
        named = words(row['term'] if row['evidence'] == 'own_word' else row[row['evidence']]['requirement_word'])
        if (row['leaf_basis'] not in BASES
                or (row['leaf_basis'] == 'structure') == is_part
                or (row['leaf_basis'] == 'body_part') != (part.lower() in review['body_parts'])
                or (row['leaf_basis'] == 'named_part' and not any(len(word) > 3 and unlocked.named(word, words(part)) for word in named))
                or (row['leaf_basis'] == 'group_member' and row['evidence'] != 'kind_of'
                    and not (' and ' in structures[row['structure_id']] or '/' in structures[row['structure_id']]))):
            raise problem('Requirement is not the kind of leaf recorded')
        if row['mesh'] not in geometry:
            geometry[row['mesh']] = mesh_side(row['mesh'], meshes, review, cache)
        located = geometry[row['mesh']]['located']
        wanted = requirement_side(requirement, row['name'])
        if mesh['side']:
            if located != mesh['side'] or (wanted and wanted != mesh['side']):
                raise problem('Side of the label, the mesh and the requirement disagree')
            side_basis = mesh['side']
        elif requirement['laterality'] == 'bilateral':
            if located != 'both':
                raise problem('A bilateral requirement needs a mesh that lies on both sides')
            side_basis = 'bilateral'
        elif wanted:
            if located != 'both':
                raise problem('An unsided label must lie on both sides to bind a sided requirement')
            side_basis = 'both'
        else:
            side_basis = 'unsided'
        if row['side_basis'] != side_basis or row['mesh_side'] != located:
            raise problem('Side basis is not what the mesh shows')
        if row['region'] not in review['regions']:
            raise problem('Unknown region')
        by_mesh.setdefault(row['mesh'], []).append(row)
    records = []
    for key, rows in by_mesh.items():
        if len({row['structure_id'] for row in rows}) != len(rows) or rows[0]['asset_id'] in existing:
            raise ValueError('Repeated binding or existing record: ' + key)
        item = record(meshes[key], rows, review, geometry[key])
        for row in rows:
            for investigation in row['investigations']:
                requirement = leaves[row['structure_id']][investigation]
                if inspect_binding(item, requirement) != [] or inspect_requirement_coverage(item, requirement) != ['requirement_coverage_partial']:
                    raise ValueError('%s / %s: The checker refuses the binding' % (key, row['structure_id']))
        records.append(item)
    unrecorded = set(meshes) - set(by_mesh)
    if set(review['not_recorded']) != unrecorded or not all(review['not_recorded'].values()):
        raise ValueError('Every other mesh of the readers needs a reason')
    return sorted(records, key=lambda item: item['id'])


def apply(raw, records):
    text = raw.decode('utf-8')
    at = text.index(INSERT_BEFORE)
    new = ''.join(',\n    ' + json.dumps(item, indent=2, ensure_ascii=False).replace('\n', '\n    ') for item in records)
    return (text[:at] + new + text[at:]).encode('utf-8'), [[len(text[:at].encode('utf-8')), '', new]]


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


def before_reader_model_records(raw):
    """Exact earlier bytes of the evidence file; any other state is returned unchanged."""
    receipt = json.loads(RECEIPT.read_text())
    if second.sha(raw) != receipt['after_sha256']:
        return raw
    shift = sum(len(new.encode()) - len(old.encode()) for _, old, new in receipt['edits'])
    for start, old, new in sorted(receipt['edits'], reverse=True):
        shift -= len(new.encode()) - len(old.encode())
        at = start + shift
        if raw[at:at + len(new.encode())] != new.encode():
            raise ValueError('Reader model record literal changed')
        raw = raw[:at] + old.encode() + raw[at + len(new.encode()):]
    if second.sha(raw) != receipt['before_sha256']:
        raise ValueError('Reader model record inverse changed unrelated bytes')
    return raw


if __name__ == '__main__':
    made = bind()
    print(len(made), 'records;', sum(len(item['structure_ids']) for item in made), 'bindings')
