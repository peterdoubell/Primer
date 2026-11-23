"""Verify the source model inventory, registered examinations, anatomical limits and section math."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient
from primer.server import app
from primer.salivary_surface_reference import ATLAS, EXAMS

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / 'web/anatomy' / ATLAS


def test_meshes_are_named_metric_source_objects_and_page_pin_agrees():
    raw = (DIR / 'surfaces.json').read_bytes()
    rows = json.loads(raw)
    assert len(rows) == 18 and [sum(r['group'] == group for r in rows) for group in ['gland', 'duct', 'landmark']] == [6, 4, 8]
    assert sum(r['vertices'] for r in rows) == 18356 and sum(r['triangles'] for r in rows) == 36650
    html = (DIR / 'index.html').read_text()
    assert 'data-surfaces-sha256="' + hashlib.sha256(raw).hexdigest() + '"' in html
    assert json.loads((DIR / 'source.json').read_text())['worldUnitToMillimetres'] == 1000
    delivery = json.loads((DIR / 'delivery.json').read_text())['files']
    assert set(delivery) == {p.name for p in DIR.iterdir() if p.is_file() and p.name != 'delivery.json'}
    for name, record in delivery.items():
        content = (DIR / name).read_bytes()
        assert (len(content), hashlib.sha256(content).hexdigest()) == (record['bytes'], record['sha256'])
    for row in rows:
        assert f'value="{row["label"]}"' in html
        assert row['sourceType'] == ('CURVE' if row['group'] == 'duct' else 'MESH')
        unpacked = gzip.decompress((DIR / row['file']).read_bytes())
        assert len(unpacked) == 12 * (row['vertices'] + row['triangles'])
        assert hashlib.sha256(unpacked).hexdigest() == row['sha256']


def test_three_reports_expose_the_gross_atlas_and_retains_separate_neck_examples():
    with TestClient(app) as client:
        for identifier in EXAMS:
            ref = client.get('/api/radiology/modules/' + identifier).json()['radiology_reference']
            card, = [row for row in ref['source_native_inspectors'] if row['id'] == ATLAS]
            assert card['modality'] == 'Gross anatomical atlas' and card['clinical_approval'] is False
            assert card['structure_ids'] == [] and card['current_patient_registration'] is False
            assert client.get(card['src']).status_code == 200
            if identifier == 'us.soft-tissue-neck':
                assert {'salivary-us-2025', 'segthy-001'} <= {row['id'] for row in ref['source_native_inspectors']}
        thyroid = client.get('/api/radiology/modules/ra.ultrasound-thyroid').json()['radiology_reference']
        assert ATLAS not in {row['id'] for row in thyroid['source_native_inspectors']}


def test_triangle_plane_intersections_retain_source_coordinates_and_handle_coplanarity():
    js = """
import assert from 'node:assert/strict';
import {sectionSegments} from './web/anatomy/zanatomy-salivary/planes.mjs';
const tri = [0,1,2], pts = [0,0,0, 4,0,0, 0,2,4];
assert.deepEqual(sectionSegments(pts,tri,'xy',2), [[[2,1],[0,1]]]);
assert.deepEqual(sectionSegments(pts,tri,'yz',2), [[[0,0],[1,2]]]);
assert.deepEqual(sectionSegments(pts,tri,'xz',1), [[[2,2],[0,2]]]);
assert.deepEqual(sectionSegments(pts,tri,'xy',4), []);
assert.deepEqual(sectionSegments(pts,tri,'xy',5), []);
assert.deepEqual(sectionSegments([0,0,1, 1,0,1, 0,1,1],tri,'xy',1), []);
"""
    subprocess.run(['node', '--input-type=module', '-e', js], cwd=ROOT, check=True)
