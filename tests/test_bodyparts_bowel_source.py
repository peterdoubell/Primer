"""Original regional pieces cannot stand for validated bowel continuity or wall layers."""
import gzip
import hashlib
import json
from pathlib import Path
from tools.anatomy_sources.acquire_bodyparts_bowel_upstream import TARGETS
from tools.anatomy_sources.acquire_bodyparts_pancreatic_upstream import select

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/bodyparts-bowel-source-review'


def test_all_sixty_bowel_source_pieces_match_original_groups_and_headers():
    acquisition=json.loads((REVIEW/'acquisition.json').read_text());mapping=json.loads((REVIEW/'selected-original-mapping-rows.json').read_text())['obj2FMA-4.3.html']
    html='<table>'+''.join('<tr>'+''.join('<td>'+v+'</td>' for v in row)+'</tr>' for row in [mapping['header'],*mapping['rows']])+'</table>'
    groups,objects=select((REVIEW/'selected-version-manifest.txt').read_text(),html,TARGETS)
    assert len(groups)==11 and len(objects)==60 and groups==acquisition['source_groups']
    assert sum(r['faces'] for r in acquisition['objects'])==30546
    assert acquisition['archive_crc_verified'] and acquisition['upstream_default_license']=='CC BY-SA 2.1 Japan'
    assert acquisition['archive_40_cc_by_40_grant_reused_for_upstream_meshes'] is False
    assert all(r['original_obj_header']['File ID']==r['id'] for r in acquisition['objects'])
    assert acquisition['runtime_promoted'] is False and acquisition['source_geometry_altered'] is False


def test_each_source_piece_and_every_rendered_triangle_are_retained():
    geometry=json.loads((REVIEW/'original-obj-geometry-review.json').read_text())
    assert geometry['expected_original_object_count']==60 and geometry['all_expected_original_objects_inspected']
    assert sum(r['triangles'] for r in geometry['records'])==30546
    assert all(r['zero_area_triangles']==0 and len(r['exact_position_analysis_topology']['components'])==1 for r in geometry['records'])
    assert all(r['source_positions_faces_or_normals_changed'] is False for r in geometry['records'])
    figures=json.loads((REVIEW/'source-figure-review.json').read_text());assert len(figures['figures'])==22
    for angle in [35,215]:
        assert sum(p['original_triangle_count'] for f in figures['figures'] if f['azimuth_degrees']==angle for p in f['panels'])==30546
    for figure in figures['figures']:
        assert hashlib.sha256((REVIEW/figure['file']).read_bytes()).hexdigest()==figure['sha256']
    assert figures['source_meshes_merged_repaired_or_deduplicated'] is False and figures['runtime_promoted'] is False


def test_every_piece_has_complete_lossless_separate_contact_evidence():
    summary=json.loads((REVIEW/'complete-self-contact-summary.json').read_text())
    assert summary['all_sixty_original_objects_complete'] and len(summary['records'])==60
    assert sum(r['source_triangles'] for r in summary['records'])==30546
    for row in summary['records']:
        raw=(REVIEW/row['file']).read_bytes();payload=gzip.decompress(raw);e=json.loads(payload)
        assert hashlib.sha256(raw).hexdigest()==row['compressed_sha256']
        assert hashlib.sha256(payload).hexdigest()==row['uncompressed_sha256']
        assert row['source_triangles']==row['testable_triangles'] and row['contact_count']==0
        assert row['candidate_pairs']==row['explicitly_tested_pairs']+row['resolved_noncoplanar_shared_edge_pairs']
        assert e['other_source_objects_compared_or_fused'] is False
        assert e['clinical_approval'] is False and e['runtime_promoted'] is False
