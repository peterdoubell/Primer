"""The biliary reader shows BodyParts3D 4.3 object FJ3079 as two ducts, without changing its geometry."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from tools.anatomy_sources import partition_biliary_duct as tool

ROOT = Path(__file__).resolve().parents[1]
READER = ROOT / 'web/anatomy/bp3d-biliary-4.3'
DOCS = ROOT / 'docs/bp3d-biliary-duct-partition-20261124'


def rows():
    return json.loads((READER / 'surfaces.json').read_text())


def delivered(row):
    raw = gzip.decompress((READER / row['file']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == row['sha256']
    return tool.decode(raw, row['vertices'], row['triangles'])


def triangle_bytes(positions, triangles):
    return sorted(positions[triangle].tobytes() for triangle in triangles)


def parts():
    found = {row['sourcePart']['side']: row for row in rows() if 'sourcePart' in row}
    assert set(found) == {'above', 'below'}
    return found


def test_the_two_parts_hold_exactly_the_source_triangles():
    review = json.loads((DOCS / 'review.json').read_text())
    positions, triangles = tool.original()           # checks the kept copy against both recorded hashes
    assert review['source']['delivered_file_sha256'] == tool.ORIGINAL_GZ_SHA256 == hashlib.sha256(tool.ORIGINAL.read_bytes()).hexdigest()
    source = triangle_bytes(positions, triangles)
    assert len(source) == 1364 == len(set(source))
    both = []
    for side, row in parts().items():
        part_positions, part_triangles = delivered(row)
        assert tool.components(len(part_positions), part_triangles) == 1
        assert len(np.unique(part_triangles)) == len(part_positions)          # no unused vertex
        assert {vertex.tobytes() for vertex in part_positions} <= {vertex.tobytes() for vertex in positions}  # none moved or made
        assert row['sourcePart']['sourceObjectSha256'] == tool.ORIGINAL_SHA256 and row['label'] == 'FJ3079'
        assert review['parts'][side]['mesh_sha256'] == row['sha256']
        assert review['parts'][side]['delivered_file_sha256'] == hashlib.sha256((READER / row['file']).read_bytes()).hexdigest()
        both += triangle_bytes(part_positions, part_triangles)
    assert sorted(both) == source


def test_the_tool_reproduces_the_delivered_parts_and_the_recorded_measurements():
    made, measured = tool.partition()
    review = json.loads((DOCS / 'review.json').read_text())
    assert measured == review['measurements']
    for side, row in parts().items():
        assert tool.sha(made[side]['raw']) == row['sha256']
        # Compressed bytes differ between zlib builds; the mesh inside must be the same.
        assert gzip.decompress(tool.gz(made[side]['raw'])) == made[side]['raw'] == gzip.decompress((READER / row['file']).read_bytes())
        assert made[side]['bounds'] == row['bounds']


def test_the_division_lies_where_the_cystic_duct_meets_the_object():
    review = json.loads((DOCS / 'review.json').read_text())
    measured = review['measurements']
    found = parts()
    upper, lower = delivered(found['above'])[0], delivered(found['below'])[0]
    all_rows = {row['file']: row for row in rows()}
    cystic = [delivered(all_rows[code + '.mesh.gz'])[0] for code in tool.CYSTIC]
    hepatic = [delivered(all_rows[code + '.mesh.gz'])[0] for code in tool.HEPATIC]
    # Both cystic duct objects touch each part: the division passes through the junction.
    for mesh in cystic:
        assert tool.nearest(upper, mesh).min() < 1 and tool.nearest(lower, mesh).min() < 1
    # The hepatic ducts meet only the upper part, at its top; the lower part stays far from them.
    for mesh in hepatic:
        assert tool.nearest(upper, mesh).min() < 0.5 and tool.nearest(lower, mesh).min() > 15
    low, high = measured['hepatic_confluence_above_plane_mm']
    assert 18 < low < high < 26
    # Most of the object lies below the cystic duct: the source's label fitted only its upper quarter.
    assert upper[:, 2].max() - lower[:, 2].min() > 84 and measured['centre_mm'][2] - lower[:, 2].min() > 60
    assert found['below']['triangles'] > found['above']['triangles']
    assert measured['contact_extent_along_course_mm'] < 2 * review['tolerance_mm']
    assert measured['boundary_spread_along_course_mm'] <= 2 * review['tolerance_mm'] + 0.1
    assert measured['course_direction'][2] > 0.7


def test_the_reader_names_both_ducts_and_says_what_was_done():
    page = (READER / 'index.html').read_text()
    listed = rows()
    assert len(listed) == 21 and [row['name'] for row in listed] == sorted(row['name'] for row in listed)
    assert not (READER / 'FJ3079.mesh.gz').exists() and not any(row['file'] == 'FJ3079.mesh.gz' for row in listed)
    boxes = page.split('<fieldset><legend>Source objects</legend>')[1].split('</fieldset>')[0].split('\n')
    assert [box.split('>')[2].split('<')[0] for box in boxes] == [row['name'] for row in listed]   # the viewer pairs them by position
    names = {row['sourcePart']['structure']: row['name'] for row in parts().values()}
    assert names == {'common hepatic duct': 'Common hepatic duct · FJ3079 above the cystic duct',
                     'common bile duct': 'Common bile duct · FJ3079 below the cystic duct'}
    for name in names.values():
        assert '<label><input class="layer" type="checkbox" checked >%s</label>' % name in page
    assert 'Common hepatic duct · FJ3079</label>' not in page and 'remains under review' not in page
    assert hashlib.sha256((READER / 'surfaces.json').read_bytes()).hexdigest() in page
    for sentence in ('has no common bile duct object', 'shown in two parts, divided where the source cystic duct meets it',
                     'Every source triangle is in one part, unchanged', 'no radiologist has reviewed it',
                     'the division of object FJ3079 into two parts', 'creativecommons.org/licenses/by-sa/2.1/jp/'):
        assert sentence in page, sentence
    provenance = json.loads((READER / 'provenance.json').read_text())
    assert provenance['partition']['anatomical_review'] == 'none' and provenance['license'] == 'CC BY-SA 2.1 Japan'
    assert 'FJ3079' in provenance['reacquisition']['matchedPreviouslyReviewedObjects']
    review = json.loads((DOCS / 'review.json').read_text())
    assert 'not a radiologist review' in review['reviewer'] and review['bindings'].startswith('None')
