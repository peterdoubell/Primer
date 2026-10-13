"""Candidate geometry must stay source-bound and cannot become approved anatomy by naming."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import topology

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'docs/thoracic-zanatomy-candidate-review-20261013'


def source_rows():
    manifest = json.loads((REVIEW/'manifest.json').read_text())
    rows = []
    for record in manifest['records']:
        encoded = (REVIEW/record['file']).read_bytes()
        assert hashlib.sha256(encoded).hexdigest() == record['sha256']
        raw = gzip.decompress(encoded)
        assert hashlib.sha256(raw).hexdigest() == record['decoded_sha256']
        obj = json.loads(raw)
        v = np.asarray(obj['evaluated_viewport_mesh']['positions_local'], float)
        m = np.asarray(obj['matrix_world'], float)
        world = np.column_stack([v[:,0]*m[i,0]+v[:,1]*m[i,1]+v[:,2]*m[i,2]+m[i,3] for i in range(3)])
        assert np.isfinite(world).all()
        faces = np.asarray(obj['evaluated_viewport_mesh']['triangle_corner_indices'], int)
        rows.append((record, obj, world, faces))
    return manifest, rows


def test_all_nine_preserved_exports_match_original_recorded_hashes_and_topology():
    manifest, rows = source_rows()
    audit = json.loads((REVIEW/'geometry-audit.json').read_text())
    assert len(rows) == 9 and sum(len(f) for _,_,_,f in rows) == 156160
    assert audit['source_scene_sha256'] == manifest['source_scene_sha256']
    assert not manifest['clinical_approval'] and not manifest['runtime_promoted']
    license_bytes = (REVIEW/manifest['license_evidence']['file']).read_bytes()
    assert hashlib.sha256(license_bytes).hexdigest() == manifest['license_evidence']['compressed_sha256']
    assert hashlib.sha256(gzip.decompress(license_bytes)).hexdigest() == manifest['license_evidence']['original_sha256']
    for record, obj, world, faces in rows:
        measured = next(r for r in audit['rows'] if r['name'] == obj['name'])
        points, remap = np.unique(world, axis=0, return_inverse=True)
        current = topology(points, remap[faces])
        for key in ['boundary_edges','nonmanifold_edges']:
            assert current[key] == measured['exact_position_topology'][key]
        assert len(current['components']) == len(measured['exact_position_topology']['components'])
        assert measured['world_bounds'] == [world.min(0).tolist(), world.max(0).tolist()]
        assert not obj['source_modified'] and not obj['clinical_approval']


def test_source_authoring_cannot_be_relabeled_as_independently_sampled_pleural_layers():
    details = json.loads((REVIEW/'source-authoring-details.json').read_text())
    pleura = next(r for r in details['objects'] if r['name'] == 'Pleura')
    assert [m['type'] for m in pleura['modifiers']] == ['SUBSURF','SOLIDIFY','SOLIDIFY']
    decision = json.loads((REVIEW/'decision.json').read_text())
    assert decision['status'] == 'hold_for_anatomical_correspondence_review'
    assert not decision['clinical_approval'] and not decision['structure_coverage_granted'] and not decision['runtime_promoted']
    assert decision['pleura']['evaluated_surface_components'] == 8
    assert not decision['pleura']['independently_sampled_tissue_layers']
    assert not decision['pleura']['component_order_assigns_parietal_or_visceral_identity']
    assert not decision['pleura']['fissural_correspondence_verified']


def test_enclosure_discrepancy_is_retained_in_recorded_source_coordinates():
    _, rows = source_rows()
    pleura = next(v for _,o,v,_ in rows if o['name'] == 'Pleura')
    lobe = next(v for _,o,v,_ in rows if o['name'] == 'Inferior lobe of left lung')
    difference = float((pleura[:,2].min()-lobe[:,2].min())*1000)
    assert 1.27 < difference < 1.29
    decision = json.loads((REVIEW/'decision.json').read_text())
    assert difference == decision['pleura']['left_lower_lobe_extends_below_total_pleura_bounds_source_mm']
    assert not decision['venous_sources']['endpoints_or_atrial_junction_independently_verified']
