"""Native wall instances conserve source geometry, defects and reflected lineage."""
import gzip
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.render_zanatomy_wall_source import decode
from tools.anatomy_sources.review_zanatomy_wall_source import TARGETS, native_polygons

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/zanatomy-wall-source-review'


def report():
    return json.loads((REVIEW / 'native-wall-review.json').read_text())


def evidence(row):
    packed = (REVIEW / row['file']).read_bytes(); raw = gzip.decompress(packed)
    assert hashlib.sha256(packed).hexdigest() == row['compressed_sha256']
    assert hashlib.sha256(raw).hexdigest() == row['uncompressed_sha256']
    return json.loads(raw)


def test_all_sixteen_source_instances_share_only_their_original_nine_geometries():
    r = report()
    assert r['all_expected_native_instances_preserved'] and r['expected_source_instance_count'] == 16
    assert len(r['geometries']) == 9 and len(r['instances']) == 16
    assert {i['name'] for i in r['instances']} == set(TARGETS)
    assert sum(i['native_reflected_instance'] for i in r['instances']) == 7
    assert sum(i['original_polygon_count'] for i in r['instances']) == 244931
    assert sum(i['triangles'] for i in r['instances']) == 257939  # potential tessellation count, not exported faces
    assert r['unit_meters'] == .01 and r['fbx_version'] == 7400
    for name in ['Rectus abdominis muscle', 'Internal abdominal oblique muscle', 'Transversus abdominis muscle']:
        paired = [i for i in r['instances'] if i['name'] in [name + '.r', name + '.l']]
        assert len(paired) == 2 and len({i['source_geometry_id'] for i in paired}) == 1
        assert len({i['source_model_id'] for i in paired}) == 2
        assert all(not i['independent_patient_side_anatomy_verified'] for i in paired)
    assert not r['source_geometry_changed'] and not r['clinical_approval'] and not r['runtime_promoted']


def test_every_original_array_and_polygon_is_losslessly_retained():
    r = report()
    assert sum(g['positions'] for g in r['geometries']) == 65926
    for g in r['geometries']:
        e = evidence(g); positions = decode(e['positions']); indices = decode(e['polygon_vertex_index'])
        polygons = native_polygons(indices, len(positions)//3)
        assert len(polygons) == g['polygons'] and len(positions) == 3*g['positions']
        assert sum(len(p)-2 for p in polygons) == g['derived_triangulation_count_only']
        decode(e['original_edges'])
        for layer in e['original_layers'].values():
            for value in layer.values():
                if isinstance(value, dict): decode(value)
        assert not e['source_array_values_changed'] and not e['polygons_triangulated_or_capped']
    with pytest.raises(ValueError, match='termination'):
        native_polygons([0, 1, 2], 3)
    with pytest.raises(ValueError, match='outside'):
        native_polygons([0, 1, -5], 3)


def test_open_fascia_winding_edges_unused_position_and_nonplanarity_stay_explicit():
    r = report(); geometries = {g['geometry_id']: g for g in r['geometries']}
    expected = {225169782: (5, 11, 0), 607205088: (390, 0, 1), 998952165: (253, 0, 0)}
    for gid, (boundaries, winding, unused) in expected.items():
        g = geometries[gid]; e = evidence(g)
        assert g['native_topology']['boundary_edges'] == boundaries
        assert g['native_topology']['inconsistently_wound_edge_pairs'] == winding
        assert sum(edge['boundary'] for edge in e['source_edge_findings']) == boundaries
        assert sum(edge['inconsistent_winding'] for edge in e['source_edge_findings']) == winding
        assert len(e['unreferenced_source_position_indices']) == unused
    fascia = geometries[607205088]
    assert fascia['polygon_sizes'] == {'4': 5372, '3': 188, '5': 58}
    assert fascia['exact_duplicate_position_records'] == 3
    assert fascia['exact_position_analysis_topology']['boundary_edges'] == 386
    assert not fascia['analysis_welding_changes_source']
    assert max(i['maximum_native_polygon_nonplanarity_mm'] for i in r['instances']) == pytest.approx(2.1880622312871774)
    assert all(not i['material_labels_are_histological_boundaries'] for i in r['instances'])
    assert all(not r['named_model_queries'][q] for q in ['rectus sheath', 'semilunar', 'scarpa', 'camper'])
    assert len(r['named_model_queries']['aponeurosis']) == 6
    assert all('abdom' not in item['name'].lower() for item in r['named_model_queries']['aponeurosis'])


def test_all_original_instances_faces_and_edges_are_shown_in_review_views():
    r = report(); projections = json.loads((REVIEW / 'projection-review.json').read_text())
    assert projections['source_review_sha256'] == hashlib.sha256((REVIEW/'native-wall-review.json').read_bytes()).hexdigest()
    assert len(projections['figures']) == 9
    panels = [p for f in projections['figures'] for p in f['panels']]
    assert len(panels) == 32 and {p['source_model_id'] for p in panels} == {i['source_model_id'] for i in r['instances']}
    assert sum(p['all_native_faces_displayed'] for p in panels) == 2*244931
    assert sum(p['boundary_edges_displayed'] for p in panels) == 2*1043
    assert sum(p['inconsistent_winding_edges_displayed'] for p in panels) == 2*22
    assert sum(p['unused_source_positions_displayed'] for p in panels) == 4
    for f in projections['figures']:
        assert hashlib.sha256((REVIEW/f['file']).read_bytes()).hexdigest() == f['sha256']


def test_retained_arrays_match_pinned_original_fbx_and_every_source_connection():
    source = ROOT / '.research/zanatomy-wall-source/MuscularSystem100.fbx'
    if not source.exists(): pytest.skip('Large original source remains in ignored research staging')
    from tools.anatomy_sources.inspect_fbx import load_fbx, child
    raw = source.read_bytes()
    assert len(raw) == 37343180 and hashlib.sha256(raw).hexdigest() == report()['source_fbx_sha256']
    _, nodes = load_fbx(source)
    objects = {o['properties'][0]: o for o in next(n for n in nodes if n['name']=='Objects')['children'] if o['properties']}
    connections = next(n for n in nodes if n['name']=='Connections')['children']
    for row in report()['geometries']:
        g = objects[row['geometry_id']]; e = evidence(row)
        for field, name in [('positions', 'Vertices'), ('polygon_vertex_index', 'PolygonVertexIndex'), ('original_edges', 'Edges')]:
            assert decode(e[field]).tobytes() == child(g, name)['properties'][0].tobytes()
        for name, layer in e['original_layers'].items():
            original = child(g, name)
            for key, value in layer.items():
                if isinstance(value, dict):
                    assert decode(value).tobytes() == child(original,key)['properties'][0].tobytes()
                else: assert value == child(original,key)['properties']
    for part in report()['instances']:
        assert objects[part['source_model_id']]['properties'][1].split('\0')[0] == part['name']
        assert any(c['properties'][:3] == ['OO', part['source_geometry_id'], part['source_model_id']] for c in connections)
