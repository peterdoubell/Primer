"""Original wall pieces retain provenance, contacts and missing-layer limits."""
import gzip
import hashlib
import itertools
import json
from pathlib import Path

import pytest

from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import select, alternative_representations
from tools.anatomy_sources.acquire_bodyparts_wall_upstream import TARGETS

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/bodyparts-wall-source-review'


def read(name):
    return json.loads((REVIEW / name).read_text())


def html(table):
    return '<table>' + ''.join('<tr>' + ''.join('<td>' + v + '</td>' for v in r) + '</tr>'
                              for r in [table['headers']] + table['selected_element_rows']) + '</table>'


def test_m_source_requires_explicit_opt_in_and_original_mapping_identity():
    manifest = (REVIEW / 'selected-version-manifest.txt').read_text()
    tables = read('selected-original-mapping-rows.json')
    with pytest.raises(ValueError, match='Unsupported'):
        select(manifest, html(tables['obj2FMA-4.3.html']), TARGETS)
    groups, mapping = select(manifest, html(tables['obj2FMA-4.3.html']), TARGETS, True)
    receipt = read('acquisition.json')
    assert groups == receipt['source_groups'] and len(mapping) == 5
    alternatives = alternative_representations(html(tables['obj2FMA-partof-4.3.html']), mapping)
    for row in receipt['objects']:
        assert row['original_obj_header']['File ID'] == row['id']
        assert row['original_obj_header']['Concept ID'] == row['source_fma']
        assert row['original_obj_header']['Representation ID'] == row['representation_id']
        assert row['mirrored_source_id'] == row['id'].endswith('M')
        assert any(r['representation_id'] == row['representation_id'] and r['source_fma'] == row['source_fma']
                   for r in [mapping[row['id']]] + alternatives[row['id']])
    assert sum(not r['returned_representation_matches_is_a'] for r in receipt['objects']) == 2
    assert receipt['archive_crc_verified'] and receipt['upstream_default_license'] == 'CC BY-SA 2.1 Japan'
    assert not receipt['archive_40_cc_by_40_grant_reused_for_upstream_meshes']
    for invalid in ['FJ1452MM', 'FJ1452X']:
        with pytest.raises(ValueError, match='Unsupported'):
            select(manifest.replace('FJ1452M', invalid), html(tables['obj2FMA-4.3.html']), TARGETS, True)


def test_all_original_components_and_self_contacts_remain_unrepaired():
    geometry = read('original-obj-geometry-review.json')
    assert geometry['all_expected_original_objects_inspected'] and geometry['expected_original_object_count'] == 5
    assert sum(r['triangles'] for r in geometry['records']) == 237506
    assert sum(len(r['exact_position_analysis_topology']['components']) for r in geometry['records']) == 89
    assert all(r['exact_position_analysis_topology']['boundary_edges'] == 0 for r in geometry['records'])
    assert all(not r['source_positions_faces_or_normals_changed'] for r in geometry['records'])
    summary = read('complete-self-contact-summary.json')
    assert summary['all_expected_original_objects_complete'] and summary['expected_original_object_count'] == 5
    assert sum(r['contact_count'] for r in summary['records']) == 48
    for row in summary['records']:
        packed = (REVIEW / row['file']).read_bytes(); raw = gzip.decompress(packed)
        assert hashlib.sha256(packed).hexdigest() == row['compressed_sha256']
        assert hashlib.sha256(raw).hexdigest() == row['uncompressed_sha256']
        assert row['invalid_source_faces'] == 0 and row['source_triangles'] == row['testable_triangles']
        assert row['candidate_pairs'] == row['explicitly_tested_pairs'] + row['resolved_noncoplanar_shared_edge_pairs']


def test_original_m_representation_is_not_exact_reflection_or_independent_patient_side():
    mirror = read('original-M-source-comparison.json')
    assert mirror['original_vertex_counts'] == [63907, 63893]
    assert mirror['source_triangle_counts'] == [111826, 111826]
    assert mirror['maximum_reflected_nearest_vertex_distance_mm'] == pytest.approx(0.28673714949409485)
    assert not mirror['source_X_reflected_position_sets_exactly_equal']
    assert not mirror['face_indices_exactly_equal'] and not mirror['normal_indices_exactly_equal']
    assert mirror['reflection_is_analysis_only_not_source_export_transform']
    assert not mirror['independent_left_right_patient_geometry_verified']
    assert not mirror['nearest_vertex_distance_is_continuous_surface_distance']
    assert not mirror['source_geometry_changed'] and not mirror['clinical_approval']


def test_every_original_pair_has_complete_contact_and_proximity_accounting():
    summary = read('complete-source-pair-summary.json')
    assert summary['all_five_original_objects_inspected']
    assert summary['source_triangles'] == summary['testable_triangles'] == 237506
    assert summary['within_object_contact_count'] == 48
    assert summary['contact_count'] == 2116 and summary['between_object_contact_count'] == 2068
    assert summary['candidate_pairs'] == 2357374
    packed = (REVIEW / summary['file']).read_bytes(); raw = gzip.decompress(packed)
    assert hashlib.sha256(packed).hexdigest() == summary['compressed_sha256']
    assert hashlib.sha256(raw).hexdigest() == summary['uncompressed_sha256']
    evidence = json.loads(raw); pairs = read('complete-pair-proximity-contact-review.json')
    assert {tuple(r['source_ids']) for r in pairs['pairs']} == set(itertools.combinations(sorted(evidence['source_part_ids']), 2))
    assert sum(r['continuous_triangle_contact_count'] for r in pairs['pairs']) + pairs['within_source_contact_count'] == summary['contact_count']
    assert all(not r['biological_junction_or_gap_verified'] for r in pairs['pairs'])


def test_missing_layers_and_all_review_figures_cannot_grant_clinical_coverage():
    holds = read('source-selection-holds.json')
    assert len(holds['named_layer_or_landmark_queries']) == 10
    assert all(not rows for rows in holds['named_layer_or_landmark_queries'].values())
    assert not holds['missing_layers_derived_from_outer_muscle']
    assert not holds['clinical_approval'] and not holds['runtime_promoted']
    figures = read('source-figure-review.json')
    for row in figures['figures']:
        assert hashlib.sha256((REVIEW / row['file']).read_bytes()).hexdigest() == row['sha256']
    assert len(figures['figures']) == 10
    assert {r['source_group'] for r in figures['figures']} == set(TARGETS)
    assert sum(p['original_triangle_count'] for r in figures['figures'] for p in r['panels']) == 2 * 237506
    assert all(not p['source_positions_or_faces_changed'] for r in figures['figures'] for p in r['panels'])
    self_figures = read('self-contact-location-review.json')['figures']
    assert sum(r['contact_pairs_displayed'] for r in self_figures) == 48
    for row in self_figures:
        assert hashlib.sha256((REVIEW / row['file']).read_bytes()).hexdigest() == row['sha256']
    locations = read('source-pair-location-review.json')
    assert locations['panels'][0]['contact_pairs'] == read('complete-source-pair-summary.json')['contact_count']
    assert hashlib.sha256((REVIEW / locations['file']).read_bytes()).hexdigest() == locations['sha256']


def test_locally_retained_original_objs_match_every_geometry_record():
    source = ROOT / '.research/bodyparts-wall-source/objects'
    if not source.exists():
        pytest.skip('Original licensed OBJ archive is retained in ignored research staging')
    pytest.importorskip('numpy')
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import read_obj
    for row in read('original-obj-geometry-review.json')['records']:
        raw = (source / (row['id'] + '.obj')).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['source_sha256']
        v, n, f, nf = read_obj(raw.decode())
        for array, dtype, key in [(v, '<f8', 'positions_float64_le_sha256'),
                                  (n, '<f8', 'normals_float64_le_sha256'),
                                  (f, '<i8', 'face_indices_int64_le_sha256'),
                                  (nf, '<i8', 'normal_indices_int64_le_sha256')]:
            assert hashlib.sha256(array.astype(dtype).tobytes()).hexdigest() == row[key]
