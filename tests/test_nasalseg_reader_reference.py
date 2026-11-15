"""Reader transport retains source topology and limited anatomy, without granting coverage."""
import gzip
import hashlib
import json
import struct
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'web/anatomy/nasalseg-p001'
PROOF = ROOT/'docs/nasalseg-native-source-review'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def test_every_original_surface_face_and_position_survives_reader_transport():
    manifest = json.loads((OUT/'manifest.json').read_text())
    report = json.loads((PROOF/'source-label-surface-review.json').read_text())
    checks = {r['id']:r for r in json.loads((PROOF/'reader-package-review.json').read_text())['parts']}
    assert len(manifest['parts']) == 5 and manifest['total_triangles'] == 134496
    for row in report['models']:
        identifier = 'nasalseg-p001-label'+str(row['source_label']); part = manifest['parts'][identifier]
        encoded = (ROOT/'web'/part['file'].removeprefix('/app/')).read_bytes(); raw = gzip.decompress(encoded)
        magic, vertices, indices = struct.unpack('<4sII',raw[:12])
        assert magic == b'BP3D' and vertices == row['vertices'] and indices == row['triangles']*3
        assert sha(encoded) == part['sha256'] and sha(raw) == part['decoded_sha256']
        source_faces = gzip.decompress((PROOF/(identifier+'-triangles.u32.gz')).read_bytes())
        source_positions = gzip.decompress((PROOF/(identifier+'-positions.f64.gz')).read_bytes())
        assert raw[12+vertices*24:] == source_faces and sha(source_faces) == part['source_triangles_sha256']
        positions = struct.iter_unpack('<d',source_positions); stored = struct.iter_unpack('<f',raw[12:12+vertices*12])
        error = max(abs(a[0]-b[0]) for a,b in zip(positions,stored))
        assert error == checks[identifier]['maximum_position_conversion_error_declared_mm'] and error <= 4e-5
        assert part['source_components'] == row['surface_components'] and part['source_boundary_edges'] == row['boundary_edges']
        assert part['clinical_fidelity'] == 'unverified'
    assert manifest['coordinate_system']['basis'] == 'LPS'
    assert not manifest['anatomical_approval'] and not manifest['clinical_approval'] and not manifest['complete_sinonasal_geometry_verified']


def test_source_reader_keeps_same_case_CT_and_scan_truncation_explicit():
    ref = detail(Curriculum(),resolve('ra.mri-sinuses'))['radiology_reference']
    entry = next(e for e in ref['source_anatomy_references'] if e['atlas'] == 'nasalseg-p001')
    assert entry['family'] == 'sinonasal-source' and entry['initial_cropped'] is False
    assert entry['manifest_sha256'] == sha((OUT/'manifest.json').read_bytes())
    assert '98 open' in entry['population_note'] and 'Frontal/ethmoid/sphenoid' in entry['population_note']
    image = entry['source_image']; assert sha((ROOT/'web'/image['src'].removeprefix('/app/')).read_bytes()) == image['sha256']
    manifest = json.loads((OUT/'manifest.json').read_text())
    assert manifest['regions']['sinonasal-source']['uncropped_label'] == 'Acquired source extent · scan-truncated'
    assert 'Partial sinonasal orientation' in ref['walkthrough']['spatial_model']['reporting_aim']


def test_source_assets_have_explicit_dataset_rights_without_anatomical_leaf_approval():
    rows = json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    rows = [r for r in rows if r['id'].startswith('nasalseg-p001-')]
    assert len(rows) == 6 and sum(r['kind']=='model' for r in rows) == 5
    for r in rows:
        assert not r['structure_ids'] and not r['requirement_coverage'] and r['anatomical_review']['status'] == 'pending'
        rights = r['source']['license']; assert rights['commercial_use'] and rights['redistribution']
        assert rights['url'] == 'https://creativecommons.org/licenses/by/4.0/'
        assert sha((ROOT/rights['evidence_path']).read_bytes()) == rights['evidence_sha256']
