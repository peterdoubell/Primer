"""Show BodyParts3D 4.3 object FJ3079 as two labelled parts, divided where the cystic duct meets it.

The source labels the whole object "common hepatic duct" and has no common bile duct object. The
object runs from the hepatic duct confluence to about 60 mm below the cystic duct. The common bile
duct is, by definition, the duct below the union of the cystic duct and the common hepatic duct, so
the part of the object below that union is common bile duct.

This tool does not make geometry. Every source triangle goes whole to one of two parts, by the side
of one plane on which its centroid lies. The plane passes through the centre of the place where the
source's cystic duct objects touch FJ3079 and is perpendicular to the duct's course there. The two
parts together hold exactly the source triangles, each once, with the source's float32 coordinates.

It is an adaptation of the source under CC BY-SA 2.1 Japan, and the reader says so. Nothing here
approves anatomy: no radiologist has reviewed the position of the division.
"""
import gzip
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
READER = ROOT / 'web/anatomy/bp3d-biliary-4.3'
DOCS = ROOT / 'docs/bp3d-biliary-duct-partition-20261124'
ORIGINAL = DOCS / 'evidence/FJ3079.mesh.gz'
ORIGINAL_GZ_SHA256 = '0685ffa9813a152d87fe81f67b4cdc3ed10c30ab4df2511be7f92a5ef8e1774d'
ORIGINAL_SHA256 = 'a6645963ec0b29670a2bdefb2521dd74f4b1919890bb7a29d348b853611304c9'
OBJECT = 'FJ3079'
CYSTIC = ('FJ3080', 'FJ4526')
HEPATIC = ('FJ3096', 'FJ3123')
CONTACT_MM = 1.0   # a duct vertex within this distance of a cystic duct vertex belongs to the junction
COURSE_MM = 10.0   # the duct's course is taken from its vertices within this distance of the junction centre
PARTS = {
    'above': dict(file='FJ3079-common-hepatic.mesh.gz', name='Common hepatic duct · FJ3079 above the cystic duct',
                  structure='common hepatic duct'),
    'below': dict(file='FJ3079-common-bile.mesh.gz', name='Common bile duct · FJ3079 below the cystic duct',
                  structure='common bile duct'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw, vertices, triangles):
    if len(raw) != 12 * (vertices + triangles):
        raise ValueError('Mesh size differs')
    return (np.frombuffer(raw, '<f4', 3 * vertices).reshape(-1, 3),
            np.frombuffer(raw, '<u4', 3 * triangles, 12 * vertices).reshape(-1, 3))


def reader_mesh(row):
    return decode(gzip.decompress((READER / row['file']).read_bytes()), row['vertices'], row['triangles'])


def original():
    packed = ORIGINAL.read_bytes()
    raw = gzip.decompress(packed)
    if sha(packed) != ORIGINAL_GZ_SHA256 or sha(raw) != ORIGINAL_SHA256:
        raise ValueError('Stored source object differs')
    return decode(raw, 684, 1364)


def nearest(points, others):
    return np.linalg.norm(points[:, None, :].astype(float) - others[None, :, :].astype(float), axis=2).min(axis=1)


def components(count, triangles):
    parent = list(range(count))

    def find(item):
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item
    for a, b, c in triangles.tolist():
        parent[find(a)] = find(b)
        parent[find(b)] = find(c)
    return len({find(item) for item in range(count)})


def plane(positions, rows):
    """The dividing plane and the measurements it rests on."""
    cystic = {code: reader_mesh(rows[code])[0] for code in CYSTIC}
    gap = np.minimum.reduce([nearest(positions, cystic[code]) for code in CYSTIC])
    contact = positions[gap < CONTACT_MM].astype(float)
    if len(contact) < 3:
        raise ValueError('The cystic duct does not touch the object')
    centre = contact.mean(axis=0)
    near = positions[np.linalg.norm(positions.astype(float) - centre, axis=1) < COURSE_MM].astype(float)
    # The course is the direction of greatest spread of the nearby duct surface, pointed upwards (+Z).
    axis = np.linalg.svd(near - near.mean(axis=0))[2][0]
    if axis[2] < 0:
        axis = -axis
    along = (contact - centre) @ axis
    return centre, axis, dict(
        contact_vertices=int(len(contact)), contact_distance_mm=CONTACT_MM,
        contact_minimum_gap_mm={code: round(float(nearest(positions, cystic[code]).min()), 3) for code in CYSTIC},
        contact_z_mm=[round(float(contact[:, 2].min()), 2), round(float(contact[:, 2].max()), 2)],
        contact_extent_along_course_mm=round(float(along.max() - along.min()), 2),
        centre_mm=[round(float(value), 3) for value in centre],
        course_direction=[round(float(value), 4) for value in axis],
        course_vertices=int(len(near)), course_distance_mm=COURSE_MM)


def partition():
    rows = {row['label']: row for row in json.loads((READER / 'surfaces.json').read_text()) if 'sourcePart' not in row}
    positions, triangles = original()
    centre, axis, measured = plane(positions, rows)
    side = ((positions[triangles].astype(float).mean(axis=1) - centre) @ axis) >= 0
    height = (positions.astype(float) - centre) @ axis
    out = {}
    for key, keep in (('above', side), ('below', ~side)):
        chosen = triangles[keep]
        used = np.unique(chosen)                       # ascending: the source's vertex order is kept
        remap = np.full(len(positions), -1, dtype=np.int64)
        remap[used] = np.arange(len(used))
        part_positions = np.ascontiguousarray(positions[used], dtype='<f4')
        part_triangles = np.ascontiguousarray(remap[chosen], dtype='<u4')
        if components(len(used), part_triangles) != 1:
            raise ValueError('A part is not one connected piece: ' + key)
        raw = part_positions.tobytes() + part_triangles.tobytes()
        out[key] = dict(raw=raw, vertices=int(len(used)), triangles=int(len(chosen)),
                        bounds=[[float(value) for value in part_positions.min(axis=0)],
                                [float(value) for value in part_positions.max(axis=0)]],
                        source_triangles=np.flatnonzero(keep))
    hepatic = np.minimum.reduce([nearest(positions, reader_mesh(rows[code])[0]) for code in HEPATIC])
    confluence = height[hepatic < CONTACT_MM]
    measured.update(
        extent_above_plane_mm=round(float(height.max()), 1), extent_below_plane_mm=round(float(-height.min()), 1),
        hepatic_confluence_above_plane_mm=[round(float(confluence.min()), 1), round(float(confluence.max()), 1)],
        boundary_vertices=int(len(np.intersect1d(np.unique(triangles[side]), np.unique(triangles[~side])))),
        boundary_spread_along_course_mm=round(float(np.ptp(height[np.intersect1d(np.unique(triangles[side]),
                                                                                  np.unique(triangles[~side]))])), 2))
    return out, measured


def gz(raw):
    return gzip.compress(raw, 9, mtime=0)


def text(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def write():
    parts, measured = partition()
    surfaces = json.loads((READER / 'surfaces.json').read_text())
    whole = [row for row in surfaces if row['label'] == OBJECT and 'sourcePart' not in row]
    if len(whole) != 1:
        raise ValueError('The reader no longer lists the whole object')
    source = whole[0]
    rows = []
    for row in surfaces:
        if row is not source:
            rows.append(row)
            continue
        for key in ('above', 'below'):
            part = parts[key]
            rows.append(dict(name=PARTS[key]['name'], label=OBJECT, sourceFma=source['sourceFma'], color=source['color'] if key == 'above' else [142, 201, 150],
                             file=PARTS[key]['file'], vertices=part['vertices'], triangles=part['triangles'], sha256=sha(part['raw']),
                             originalSha256=source['originalSha256'], bounds=part['bounds'],
                             sourcePart=dict(object=OBJECT, sourceLabel='Common hepatic duct', side=key,
                                             structure=PARTS[key]['structure'], sourceObjectSha256=ORIGINAL_SHA256)))
            (READER / PARTS[key]['file']).write_bytes(gz(part['raw']))
    rows.sort(key=lambda row: row['name'])
    (READER / source['file']).unlink()
    (READER / 'surfaces.json').write_bytes(text(rows))
    publish(rows, measured)
    return rows, measured


NOTE_BEFORE = ('The source labels include gallbladder, common hepatic duct, cystic duct, right and left hepatic ducts and selected tributaries. '
               'A <a href="https://pubmed.ncbi.nlm.nih.gov/30815072/">published comparison of anatomical resources</a> flagged a BodyParts3D '
               'common hepatic duct segmentation error. The label here identifies the source object. Its anatomical boundary remains under review. '
               'A separately labelled common bile duct, continuous lumina, wall layers and clinical variants remain outside this collection.</p>')
ADAPTED_BEFORE = 'Adaptations include binary encoding, colour and interactive viewing.'


def publish(rows, measured):
    """The reader page, its provenance and its delivery inventory, from the rows just written."""
    page = (READER / 'index.html').read_text()
    start, end = page.index('<fieldset><legend>Source objects</legend>'), page.index('</fieldset>')
    checked = {'Common hepatic duct', 'Common bile duct', 'Cystic duct', 'Gallbladder', 'Left hepatic duct', 'Right hepatic duct'}
    boxes = '\n'.join('<label><input class="layer" type="checkbox" %s>%s</label>' % (
        'checked ' if row['name'].split(' · ')[0] in checked else '', row['name']) for row in rows)
    page = page[:start] + '<fieldset><legend>Source objects</legend>' + boxes + page[end:]
    intro = ('<p>Inspect 20 original BodyParts3D objects across 14 source groups. Each control selects one object by its published label '
             'and identifier.</p>')
    note = ('The source labels include gallbladder, common hepatic duct, cystic duct, right and left hepatic ducts and selected tributaries. '
            'The source labels all of object FJ3079 common hepatic duct and has no common bile duct object. The object runs from the hepatic '
            'duct confluence to about %d mm below the cystic duct, so most of it is common bile duct. '
            'A <a href="https://pubmed.ncbi.nlm.nih.gov/30815072/">published comparison of anatomical resources</a> flagged this segmentation. '
            'Here the object is shown in two parts, divided where the source cystic duct meets it, to within about 3 mm. Every source triangle '
            'is in one part, unchanged. The division was placed by measurement and no radiologist has reviewed it. '
            'Continuous lumina, wall layers, the intrapancreatic and intramural segments and clinical variants remain outside this collection.</p>'
            % round(measured['extent_below_plane_mm'], -1))
    for before, after in (
            (intro, intro.replace('Each control selects one object', 'Object FJ3079 is shown in two parts. Each other control selects one object')),
            (NOTE_BEFORE, note),
            (ADAPTED_BEFORE, 'Adaptations include binary encoding, colour, interactive viewing and the division of object FJ3079 into two parts.')):
        if page.count(before) != 1:
            raise ValueError('Reader page differs: ' + before[:40])
        page = page.replace(before, after)
    surfaces = (READER / 'surfaces.json').read_bytes()
    marker = 'data-surfaces-sha256="'
    at = page.index(marker) + len(marker)
    page = page[:at] + sha(surfaces) + page[at + 64:]
    (READER / 'index.html').write_text(page)
    provenance = json.loads((READER / 'provenance.json').read_text())
    provenance['partition'] = dict(
        object=OBJECT, source_label='Common hepatic duct', source_object_sha256=ORIGINAL_SHA256,
        parts={key: dict(file=PARTS[key]['file'], structure=PARTS[key]['structure']) for key in PARTS},
        method='Each source triangle is assigned whole to one part by the side of one plane on which its centroid lies. '
               'No vertex is moved and none is made.',
        plane=dict(point_mm=measured['centre_mm'], normal=measured['course_direction']),
        record='docs/bp3d-biliary-duct-partition-20261124/review.json', anatomical_review='none')
    (READER / 'provenance.json').write_bytes(text(provenance))
    files = {}
    for path in sorted(READER.iterdir()):
        if path.name != 'delivery.json':
            raw = path.read_bytes()
            files[path.name] = dict(bytes=len(raw), sha256=sha(raw))
    (READER / 'delivery.json').write_bytes(text(dict(files=files)))


if __name__ == '__main__':
    made, measurements = write()
    print(json.dumps(measurements, indent=1))
    print(len(made), 'rows')
