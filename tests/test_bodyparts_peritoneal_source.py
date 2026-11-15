"""Original peritoneal source labels and fragments cannot imply complete distinct anatomy."""
import gzip,hashlib,json
from pathlib import Path
import pytest
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import select
from tools.anatomy_sources.acquire_bodyparts_peritoneal_upstream import TARGETS

ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT/'docs/bodyparts-peritoneal-source-review'


def test_generic_selector_preserves_default_and_requested_peritoneal_target_scope():
    data=json.loads((REVIEW/'selected-original-mapping-rows.json').read_text())
    header=data['headers'];rows=data['selected_element_rows']
    html='<table>'+''.join('<tr>'+''.join('<td>'+v+'</td>' for v in r)+'</tr>' for r in [header]+rows)+'</table>'
    manifest=(REVIEW/'selected-version-manifest.txt').read_text()
    groups,mapping=select(manifest,html,targets=TARGETS)
    assert groups=={'FMA14643':['FJ3396','FJ4650'],'FMA14647':['FJ3398'],'FMA19757':['FJ4651']}
    assert set(mapping)=={'FJ3396','FJ3398','FJ4650','FJ4651'}
    with pytest.raises(ValueError,match='No source targets'):select(manifest,html,targets={})


def test_all_original_objects_retain_fragmentation_without_deduplication():
    receipt_path=REVIEW/'acquisition.json';receipt=json.loads(receipt_path.read_text());path=REVIEW/'original-obj-geometry-review.json.gz';p=json.loads(gzip.decompress(path.read_bytes()))
    assert p['original_acquisition_sha256']==hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    assert p['expected_original_object_count']==4 and p['all_expected_original_objects_inspected'] is True
    assert len(p['records'])==4 and sum(r['triangles'] for r in p['records'])==79516
    expected={'FJ3396':(38274,331),'FJ4650':(38274,331),'FJ3398':(1484,5),'FJ4651':(1484,5)}
    for r in p['records']:
        count,components=expected[r['id']]
        assert r['triangles']==count and len(r['exact_position_analysis_topology']['components'])==components
        assert r['zero_area_triangles']==0 and r['source_positions_faces_or_normals_changed'] is False
        assert r['analysis_welding_changes_source'] is False
    assert receipt['archive_crc_verified'] is True
    assert receipt['upstream_default_license']=='CC BY-SA 2.1 Japan'
    assert p['runtime_promoted'] is False and p['clinical_approval'] is False


def test_nearly_matching_labels_cannot_become_distinct_complete_anatomy():
    p=json.loads((REVIEW/'source-geometry-correspondence.json').read_text())
    r=next(r for r in p['comparisons'] if r['source_ids']==['FJ3398','FJ4651'])
    assert r['indexed_faces_exactly_equal'] is True and r['position_records_exactly_equal'] is False
    assert r['same_index_continuous_triangle_displacement_upper_bound_mm']==pytest.approx(.010049875621112316)
    assert r['source_meshes_deduplicated_or_roles_reassigned'] is False and r['biological_identity_independently_verified'] is False
    mes=next(r for r in p['comparisons'] if r['source_ids']==['FJ3396','FJ4650'])
    assert mes['same_index_continuous_triangle_displacement_upper_bound_mm'] is None
    assert mes['nearest_vertex_distances_are_continuous_surface_bounds'] is False
    assert p['complete_peritoneal_anatomy_verified'] is False and p['runtime_promoted'] is False


def test_every_original_source_triangle_remains_in_review_views():
    p=json.loads((REVIEW/'source-figure-review.json').read_text())
    assert len(p['figures'])==2 and p['derived_figure_license']=='CC BY-SA 2.1 Japan'
    for f in p['figures']:
        assert hashlib.sha256((REVIEW/f['file']).read_bytes()).hexdigest()==f['sha256']
        assert len(f['panels'])==4 and sum(r['original_triangle_count'] for r in f['panels'])==79516
        assert all(r['source_positions_or_faces_changed'] is False for r in f['panels'])
    assert p['source_meshes_merged_repaired_or_deduplicated'] is False and p['clinical_approval'] is False


def test_complete_inventory_is_lossless_with_separate_container_and_payload_fingerprints():
    receipt=json.loads((REVIEW/'complete-inventory-compression.json').read_text())
    packed=(REVIEW/receipt['file']).read_bytes();payload=gzip.decompress(packed)
    assert hashlib.sha256(packed).hexdigest()==receipt['compressed_sha256']
    assert hashlib.sha256(payload).hexdigest()==receipt['uncompressed_sha256']
    assert len(packed)==receipt['compressed_bytes'] and len(payload)==receipt['uncompressed_bytes']
    assert receipt['complete_component_records_preserved'] is True
    report=json.loads(payload)
    assert sum(r['triangles'] for r in report['records'])==79516
