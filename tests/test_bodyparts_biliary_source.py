"""Biliary source labels and numerical checks do not approve a complete biological duct tree."""
import gzip
import hashlib
import json
from pathlib import Path

from tools.anatomy_sources.acquire_bodyparts_biliary_upstream import TARGETS
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import select

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/bodyparts-biliary-source-review'


def test_all_twenty_versioned_objects_preserve_the_fourteen_source_groups():
    acquisition = json.loads((REVIEW / 'acquisition.json').read_text())
    mapping = json.loads((REVIEW / 'selected-original-mapping-rows.json').read_text())['obj2FMA-4.3.html']
    html = '<table>' + ''.join('<tr>' + ''.join('<td>' + v + '</td>' for v in r) + '</tr>'
                             for r in [mapping['header'], *mapping['rows']]) + '</table>'
    groups, objects = select((REVIEW / 'selected-version-manifest.txt').read_text(), html, TARGETS)
    assert len(groups) == 14 and len(objects) == 20
    assert groups == acquisition['source_groups']
    assert sum(r['faces'] for r in acquisition['objects']) == 16114
    assert acquisition['upstream_default_license'] == 'CC BY-SA 2.1 Japan'
    assert acquisition['archive_crc_verified'] is True
    assert acquisition['archive_40_cc_by_40_grant_reused_for_upstream_meshes'] is False
    assert acquisition['source_geometry_altered'] is False and acquisition['runtime_promoted'] is False
    assert all(r['original_obj_header']['File ID'] == r['id'] for r in acquisition['objects'])


def test_original_components_and_repeated_representations_are_not_fused():
    geometry = json.loads((REVIEW / 'original-obj-geometry-review.json').read_text())
    assert geometry['expected_original_object_count'] == 20 and geometry['all_expected_original_objects_inspected']
    assert sum(r['triangles'] for r in geometry['records']) == 16114
    assert sum(len(r['exact_position_analysis_topology']['components']) for r in geometry['records']) == 27
    assert all(r['zero_area_triangles'] == 0 and r['source_positions_faces_or_normals_changed'] is False for r in geometry['records'])
    comparisons = json.loads((REVIEW / 'source-geometry-correspondence.json').read_text())
    assert len(comparisons['comparisons']) == 6
    cystic = next(r for r in comparisons['comparisons'] if r['source_ids'] == ['FJ3080', 'FJ4526'])
    assert cystic['face_indices_exactly_equal'] and not cystic['position_records_exactly_equal']
    assert .113 < cystic['same_index_continuous_triangle_displacement_upper_bound_mm'] < .114
    assert sum(r['same_index_continuous_triangle_displacement_upper_bound_mm'] is None for r in comparisons['comparisons']) == 5
    assert comparisons['repeated_objects_deduplicated_fitted_or_fused'] is False
    figures = json.loads((REVIEW / 'source-figure-review.json').read_text())
    assert len(figures['figures']) == 6
    for angle in [35, 215]:
        assert sum(p['original_triangle_count'] for f in figures['figures'] if f['azimuth_degrees'] == angle for p in f['panels']) == 16114
    for figure in figures['figures']:
        assert hashlib.sha256((REVIEW / figure['file']).read_bytes()).hexdigest() == figure['sha256']
    assert figures['clinical_approval'] is False and figures['runtime_promoted'] is False


def test_every_original_object_has_complete_separate_continuous_contact_evidence():
    summary = json.loads((REVIEW / 'complete-self-contact-summary.json').read_text())
    assert summary['all_twenty_original_objects_complete'] is True and len(summary['records']) == 20
    assert sum(r['source_triangles'] for r in summary['records']) == 16114
    assert sum(r['candidate_pairs'] for r in summary['records']) == 138718
    for row in summary['records']:
        packed = (REVIEW / row['file']).read_bytes(); payload = gzip.decompress(packed); evidence = json.loads(payload)
        assert hashlib.sha256(packed).hexdigest() == row['compressed_sha256']
        assert hashlib.sha256(payload).hexdigest() == row['uncompressed_sha256']
        assert evidence['other_source_objects_compared_or_fused'] is False
        assert evidence['preparation']['original_source_triangles'] == evidence['preparation']['numerically_testable_triangles']
        assert evidence['triangle_contact_audit']['unexpected_contact_count'] == row['contact_count'] == 0
        assert row['candidate_pairs'] == row['explicitly_tested_pairs'] + row['resolved_noncoplanar_shared_edge_pairs']
        assert evidence['clinical_approval'] is False and evidence['runtime_promoted'] is False
