"""The three-scan RECIST comparison preserves the publisher's target identities."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from primer.recist_pelvic_reference import ANATOMY, CASES, delivery, references

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / 'docs/recist-pelvic-longitudinal'
BASELINE = 'recist-pelvic-023'


def test_publisher_target_identities_and_observed_nadir_reach_the_comparison():
    document = json.loads((PROOF / 'timepoints.json').read_text())
    ordered = document['timepoints']
    assert [row['studyOrder'] for row in ordered] == ['baseline', 'follow-up-1', 'follow-up-2']
    assert [
        [(target['alias'], target['caseMaskValue'], target['caseLabelMapTerm'],
          target['publisherShortAxisMm']) for target in row['targets']]
        for row in ordered
    ] == [
        [('A', 1, 'n,iliac', 16), ('B', 6, 'n,aortocaval', 16)],
        [('A', 1, 'n,inguinal', 17), ('B', 9, 'n,retroperitoneal', 13)],
        [('A', 1, 'n,pelvis', 16), ('B', 8, 'n,retroperitoneal', 14)],
    ]
    assert [sum(item['publisherShortAxisMm'] for item in row['targets']) for row in ordered] == [32, 30, 30]
    assert document['documentedTargetNadirStudyOrders'] == ['follow-up-1', 'follow-up-2']
    html = (ANATOMY / BASELINE / 'comparison.html').read_text()
    for row in ordered:
        assert f'<time datetime="{row["sourceDate"]}">' in html
        for target in row['targets']:
            assert (f'{target["publisherShortAxisMm"]} mm<br><code>'
                    f'{target["caseLabelMapTerm"]}</code> · mask {target["caseMaskValue"]}') in html
    for suffix in ('index.html', 'surfaces.html'):
        assert f'href="{suffix}"' in html
        for index in (1, 2):
            assert f'href="../{BASELINE}-follow-up-{index}/{suffix}"' in html
    assert [asset['id'] for asset in references()['ra.recist']] == [BASELINE]
    assert 'comparison.html' in delivery(BASELINE)


@pytest.mark.parametrize(
    ('order', 'in_plane_spacing', 'z_start', 'z_stop', 'expected_triangles'),
    ((1, 0.673828125, 23, 56, 10808), (2, 0.625, 27, 61, 12008)),
)
def test_followup_transport_keeps_only_its_target_a_surface_and_native_grid(
        order, in_plane_spacing, z_start, z_stop, expected_triangles):
    case_id = f'{BASELINE}-follow-up-{order}'
    folder = ANATOMY / case_id
    source = json.loads((folder / 'source.json').read_text())
    manifest, = json.loads((folder / 'surfaces.json').read_text())
    expected, = source['nodalLabels']
    assert source['study'] == f'follow-up-{order}'
    assert expected['targetAlias'] == 'A' and manifest['label'] == str(expected['label'])
    assert source['spacingXYZMm'] == [in_plane_spacing, in_plane_spacing, 2.5]
    assert source['nominalSourceSliceThicknessMm'] == 5.0
    assert source['shapeSliceRowColumn'] == [z_stop - z_start, 512, 512]
    assert (source['sourceZStart'], source['sourceZStopExclusive']) == (z_start, z_stop)
    assert (source['cropAffineRAS'][2][3]
            == source['originalAffineRAS'][2][3] + z_start * source['spacingXYZMm'][2])
    for volume in source['volumes'].values():
        packed = (folder / volume['file']).read_bytes()
        raw = gzip.decompress(packed)
        assert len(raw) == volume['decodedBytes'] == 2 * (z_stop - z_start) * 512 * 512
        assert hashlib.sha256(raw).hexdigest() == volume['decodedSHA256']
    mesh = gzip.decompress((folder / manifest['file']).read_bytes())
    assert manifest['triangles'] == expected_triangles
    assert len(mesh) == 12 * (manifest['vertices'] + expected_triangles)
    assert hashlib.sha256(mesh).hexdigest() == manifest['sha256']
    assert len(delivery(case_id)) == 7 and case_id in CASES
