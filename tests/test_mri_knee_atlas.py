"""Lossless source anatomy and real HTTP decoding for the MRI-derived knee."""
import gzip
import hashlib
import json
from pathlib import Path
import struct

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def manifest():
    return json.loads((ROOT / 'web/anatomy/msk-mri-knee/manifest.json').read_text())


def test_knee_provider_preserves_source_frame_and_distinguishes_volumes(manifest):
    assert manifest['coordinate_system']['basis'] == 'LPS'
    assert manifest['coordinate_system']['units'] == 'millimeters'
    assert manifest['license'] == 'CC0 1.0'
    assert manifest['source_doi'] == '10.22452/RD/5T6TZ7'
    assert manifest['regions']['knee']['lazy_layers'] is True
    assert manifest['regions']['knee']['side'] == 'right'
    cartilage = [part for part in manifest['parts'].values() if part['layer'] == 'cartilage']
    assert {part['name'] for part in cartilage} == {'Distal femoral cartilage', 'Patellar cartilage', 'Tibial cartilage'}
    assert all(not part.get('surface_overlay') and part['volume_native_units_cubed'] > 0 for part in cartilage)
    assert 'not' in manifest['sampling_limits']['effective_spatial_resolution'].lower()
    assert manifest['sampling_limits']['segmentation_grid_mm'] == manifest['sampling_limits']['segmentation_reference_exported_grid_mm']
    assert manifest['sampling_limits']['segmentation_grid_mm'] != manifest['sampling_limits']['separate_T2_FS_comparison_exported_grid_mm']
    assert 'paired_T2_FS_exported_grid_mm' not in manifest['sampling_limits']


def test_reference_volume_is_not_a_clinically_validated_image_pair(manifest):
    assert manifest['clinical_image_pair']['available'] is False
    assert manifest['clinical_image_pair']['independent_clinical_validation'] is False
    correspondence = manifest['source_image_correspondence']
    reference = correspondence['segmentation_reference']
    comparison = correspondence['separate_comparison_sequence']
    assert reference['mrml_volume_id'] == 'vtkMRMLScalarVolumeNode25'
    assert reference['member'].endswith('108 T1 SAG VIBE DIXON_W L-LIMB.nrrd')
    assert comparison['member'].endswith('19 RT T2 FS spc_SAG_iso (KNEE).nrrd')
    assert comparison['is_segmentation_reference'] is False
    assert comparison['cross_sequence_alignment_validated'] is False
    assert correspondence['no_fitted_transform'] is True
    validation = manifest['registration_validation']
    assert validation['clinical_alignment_approval'] is False
    assert 'STL-to-author-segmentation' in validation['scope']
    assert validation['evidence_file'].startswith('/app/anatomy/msk-mri-knee/')
    data = (ROOT / 'web' / validation['evidence_file'].removeprefix('/app/')).read_bytes()
    assert hashlib.sha256(data).hexdigest() == validation['evidence_sha256']
    evidence = json.loads(data)
    assert evidence['source_image_correspondence'] == correspondence
    assert evidence['derivative_dicom_technical_fields']['Modality'] == 'CT'
    assert evidence['derivative_dicom_technical_fields']['Manufacturer'] == '3D Slicer'
    assert evidence['derivative_dicom_technical_fields']['RepetitionTime'] == 'ABSENT'
    assert 'PatientName' not in evidence['derivative_dicom_technical_fields']
    assert '/tmp/' not in data.decode()


def test_compressed_exports_are_bit_exact_and_omit_only_recorded_empty_facets(manifest):
    omitted = 0
    for part in manifest['parts'].values():
        encoded = (ROOT / 'web' / part['file'].removeprefix('/app/')).read_bytes()
        assert len(encoded) == part['bytes']
        assert hashlib.sha256(encoded).hexdigest() == part['sha256']
        decoded = gzip.decompress(encoded)
        assert len(decoded) == part['decoded_bytes']
        assert hashlib.sha256(decoded).hexdigest() == part['decoded_sha256']
        magic, vertices, indices = struct.unpack('<4sII', decoded[:12])
        assert magic == b'BP3D'
        assert vertices == part['vertices'] and indices == part['triangles'] * 3
        assert len(decoded) == 12 + vertices * 24 + indices * 4
        omitted_indices = part['omitted_source_facet_indices']
        assert len(set(omitted_indices)) == len(omitted_indices)
        assert part['source_triangles'] - part['triangles'] == len(omitted_indices)
        omitted += len(omitted_indices)
        assert part['normals_preserved_exactly']
        assert part['source_segmentation']['id']
        assert part['geometry_transform'].startswith('identity')
    assert omitted == manifest['omission_evidence']['total_facets']
    evidence = (ROOT / 'web' / manifest['omission_evidence']['file'].removeprefix('/app/')).read_bytes()
    assert hashlib.sha256(evidence).hexdigest() == manifest['omission_evidence']['sha256']


def test_static_serving_decompresses_to_real_geometry(manifest, tmp_path, monkeypatch):
    monkeypatch.setenv('PRIMER_DB', str(tmp_path / 'http.db'))
    monkeypatch.setenv('PRIMER_BACKUP_DIR', str(tmp_path / 'backups'))
    from fastapi.testclient import TestClient
    from primer.server import app
    part = manifest['parts']['um-knee-bone-patella']
    with TestClient(app) as client:
        response = client.get(part['file'], headers={'Accept-Encoding': 'gzip'})
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/octet-stream'
    assert response.headers['content-encoding'] == 'gzip'
    assert response.content[:4] == b'BP3D'
    assert hashlib.sha256(response.content).hexdigest() == part['decoded_sha256']
