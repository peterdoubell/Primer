"""Exact source geometry and honest scope are distinct from clinical validation."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import struct

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT/'docs/laryngeal-phonation-source-review'
ATLAS = 'larynx-jasa19629778-phase01'
PART = ATLAS+'-original-air-tissue-interface'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_transport():
    manifest = json.loads((ROOT/'web/anatomy'/ATLAS/'manifest.json').read_text())
    part = manifest['parts'][PART]
    encoded = (ROOT/'web'/part['file'].removeprefix('/app/')).read_bytes()
    assert sha(encoded) == part['sha256']
    decoded = gzip.decompress(encoded)
    assert sha(decoded) == part['decoded_sha256']
    magic, vertices, indices = struct.unpack('<4sII', decoded[:12])
    assert magic == b'BP3D' and vertices == 14831 and indices == 29326*3
    assert len(decoded) == 12+vertices*24+indices*4
    return manifest, part, decoded, vertices


def test_original_ordered_face_corner_bits_and_open_components_survive_transport():
    manifest, part, decoded, count = load_transport()
    original = (PROOF/'original-frame_01.stl').read_bytes()
    assert sha(original) == part['source_member_sha256'] == 'dddf49ed16942555eefcda5f97db3f39942676532bd816f348277895715480d2'
    positions = decoded[12:12+count*12]
    faces = decoded[12+count*24:]
    restored_corners = b''.join(positions[index*12:index*12+12] for (index,) in struct.iter_unpack('<I',faces))
    original_corners = b''.join(original[start+12:start+48] for start in range(84,len(original),50))
    assert restored_corners == original_corners
    assert sha(positions) == part['source_positions_sha256']
    assert sha(faces) == part['source_triangles_sha256']
    edges = Counter()
    adjacency = {i:set() for i in range(count)}
    triangles = list(struct.iter_unpack('<III', faces))
    for a,b,c in triangles:
        for x,y in ((a,b),(b,c),(c,a)):
            edges[tuple(sorted((x,y)))] += 1
            adjacency[x].add(y)
            adjacency[y].add(x)
    assert sum(value == 1 for value in edges.values()) == part['source_boundary_edges'] == 328
    assert not any(value > 2 for value in edges.values())
    unseen = set(adjacency)
    component_face_counts = []
    while unseen:
        pending = [next(iter(unseen))]
        component = set()
        while pending:
            v = pending.pop()
            if v in component:
                continue
            component.add(v)
            pending.extend(adjacency[v]-component)
        unseen -= component
        component_face_counts.append(sum(face[0] in component for face in triangles))
    assert sorted(component_face_counts,reverse=True) == [29294,16,8,8]
    assert part['source_components'] == 4 and manifest['total_triangles'] == 29326


def test_partial_reference_has_no_patient_axes_registration_or_claimed_tissue_coverage():
    manifest, part, _, _ = load_transport()
    assert len(manifest['parts']) == 1
    assert part['name'] == 'Original segmented air–tissue interface · source phonation phase01'
    basis = manifest['coordinate_system']
    assert basis['basis'] == 'unknown original STL XYZ'
    assert basis['unit_meters'] is None
    assert 'unverified' in basis['registration']
    region = manifest['regions']['larynx-phonation-source']
    assert region['source_coordinate_cameras'] is True
    assert region['parts'] == [{'id':PART,'layer':'source_interface'}]
    for field in ['clinical_approval','anatomical_approval','source_MRI_registration_approved','complete_reporting_anatomy_verified','photographic_texture_promoted']:
        assert manifest[field] is False
    note = ' '.join(manifest['viewer_notes'])
    for text in ['not swallowing','0.8 mm native','zero-filled','not consecutive independent live frames', 'No MRI overlay', 'Individual cartilage', 'four source components', '328 open boundary edges']:
        assert text in note
    candidate = json.loads((PROOF/'registry-candidate.json').read_text())
    assert 'source_image' not in candidate['entry'] and 'source_volume' not in candidate['entry']
    assert candidate['entry']['initial_cropped'] is False
    asset = candidate['asset']
    assert asset['structure_ids'] == [] and asset['requirement_coverage'] == {}
    assert asset['anatomical_review']['status'] == 'pending'
    rights = asset['source']['license']
    assert rights['commercial_use'] and rights['redistribution']
    assert sha((ROOT/rights['evidence_path']).read_bytes()) == rights['evidence_sha256']
    metadata = json.loads((ROOT/rights['evidence_path']).read_text())
    assert metadata['id'] == 19629778 and metadata['metadata']['license']['id'] == 'cc-by-4.0'


def test_preserved_acquisition_affine_conflict_and_transport_proof_are_explicit():
    review = json.loads((PROOF/'reader-transport-review.json').read_text())
    assert review['all_87978_source_face_corners_byte_exact']
    assert review['all_29326_original_faces_retained_in_order']
    assert review['maximum_position_transport_error_source_units'] == 0
    assert not review['source_geometry_modified'] and not review['source_MRI_overlay_presented']
    assert not review['producer_registration_verified'] and not review['clinical_or_anatomical_coverage_approved']
    for proof in review['source_input_proofs']:
        data = (PROOF/proof['file']).read_bytes()
        assert sha(data) == proof['sha256'] and len(data) == proof['bytes']
    acquisition = json.loads((PROOF/'original-acquisition.json').read_text())
    assert acquisition['publisher_size_and_checksum_stable_before_after']
    assert not acquisition['whole_archive_MD5_verified'] and acquisition['remote_entity_tag'] is None
    coordinate = json.loads((PROOF/'coordinate-interface-review.json').read_text())
    assert coordinate['affines']['convention_only_equivalent'] is False
    assert coordinate['affines']['NRRD_convention_only_RAS'][0][0] < 0
    assert coordinate['affines']['inherited_NIfTI_srow'][0][0] > 0
    assert coordinate['affines']['NRRD_convention_only_RAS'][2][2] < 0
    assert coordinate['affines']['inherited_NIfTI_srow'][2][2] > 0
    assert all(not row['transform_approved'] for row in coordinate['fixed_hypothesis_tests'])


@pytest.mark.parametrize('mutation', ['truncated', 'face_count', 'nonfinite'])
def test_changed_source_binary_contract_is_rejected(mutation):
    from tools.anatomy_sources.package_laryngeal_phonation_reference import read_original_STL
    raw = bytearray((PROOF/'original-frame_01.stl').read_bytes())
    if mutation == 'truncated':
        raw.pop()
    elif mutation == 'face_count':
        struct.pack_into('<I',raw,80,29325)
    else:
        struct.pack_into('<f',raw,96,float('nan'))
    with pytest.raises(ValueError):
        read_original_STL(raw)


@pytest.mark.parametrize('selection', ['other', 'child', 'escape'])
def test_arbitrary_source_selection_is_rejected_before_any_reads(monkeypatch, tmp_path, selection):
    from tools.anatomy_sources import package_laryngeal_phonation_reference as packager
    candidates = {
        'other': tmp_path,
        'child': packager.TRUSTED_SOURCE_ROOT/'unreviewed-child',
        'escape': packager.TRUSTED_SOURCE_ROOT/'..'/'unreviewed-sibling',
    }
    def forbidden_read(*args, **kwargs):
        raise AssertionError('Untrusted source selection reached a filesystem read')
    monkeypatch.setattr(Path, 'read_bytes', forbidden_read)
    monkeypatch.setattr(Path, 'read_text', forbidden_read)
    with pytest.raises(ValueError, match='fixed reviewed laryngeal source cache'):
        packager.package(candidates[selection])


def test_known_source_reproduces_identical_runtime_bytes_in_isolated_output(monkeypatch, tmp_path):
    from tools.anatomy_sources import package_laryngeal_phonation_reference as packager
    if not (packager.TRUSTED_SOURCE_ROOT/'stiff-phase01/frame_01.stl').is_file():
        pytest.skip('Original acquisition cache is intentionally outside the repository')
    expected = ROOT/'web/anatomy'/ATLAS
    monkeypatch.setattr(packager, 'ROOT', tmp_path)
    monkeypatch.setattr(packager, 'PROOF', tmp_path/'docs/laryngeal-phonation-source-review')
    packager.package(packager.TRUSTED_SOURCE_ROOT)
    actual = tmp_path/'web/anatomy'/ATLAS
    for filename in ['manifest.json', 'ATTRIBUTION.md', PART+'.bin.gz']:
        assert (actual/filename).read_bytes() == (expected/filename).read_bytes()
    assert not (tmp_path/'data/radiology/source-anatomy-references.json').exists()
    assert not (tmp_path/'data/radiology/radiology-asset-evidence.json').exists()


def test_gzip_transport_header_has_fixed_platform_marker():
    from tools.anatomy_sources.package_laryngeal_phonation_reference import canonical_gzip
    payload=b'Original reviewed source geometry'*200
    encoded=canonical_gzip(payload)
    assert encoded[:10]==bytes.fromhex('1f8b08000000000002ff')
    assert gzip.decompress(encoded)==payload
