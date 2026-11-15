"""Cine transport identity, container parsing and honest sample-domain claims."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
from primer.source_motion import validate_motion_references, _validate_yuv_fidelity
from primer.source_motion_contract import parse_motion_contract

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/radiology'


def registry():
    return {'ra.thoracic-ultrasound': json.loads((DATA / 'source-motion-references.json').read_text())['ra.thoracic-ultrasound']}


def test_every_original_and_browser_container_matches_verified_sample_proof():
    rows = registry()
    validate_motion_references(rows, set(rows), ROOT / 'web')
    proof = json.loads((DATA / 'thoracic-ultrasound-motion-proof.json').read_text())
    assert len(rows['ra.thoracic-ultrasound']) == 6
    assert sum(r['frames'] for r in rows['ra.thoracic-ultrasound']) == 1630
    for row in rows['ra.thoracic-ultrasound']:
        assert row['decoded_RGB_frames_unchanged'] is False
        assert row['decoded_YUV_frames_unchanged'] is True
        _validate_yuv_fidelity(row, DATA)
        for field, times in [('original_src', 'source_pts_seconds'), ('src', 'transport_pts_seconds')]:
            parsed = parse_motion_contract(ROOT / 'web' / row[field].removeprefix('/app/'))
            assert parsed['pts_seconds'] == row[times]
        item = proof['clips'][row['id']]
        assert item['original_decoded_YUV_frame_sha256'] == item['transport_decoded_YUV_frame_sha256']
        assert not row['motion_context']['acquisition_timing_verified']
        if '12871_' in row['id']:
            assert row['motion_context']['source_overlay_clock_repeats']
            assert 'scanner clock resets' in row['limits']


@pytest.mark.parametrize('field,value', [('decoded_RGB_frames_unchanged', True), ('decoded_YUV_frames_unchanged', False), ('original_sha256', '0'*64), ('sha256', '0'*64), ('frames', 1), ('width', 1), ('frame_fidelity_proof_sha256', '0'*64)])
def test_yuv_proof_cannot_be_relabelled_or_detached_from_container(field, value):
    row = copy.deepcopy(registry()['ra.thoracic-ultrasound'][0])
    row[field] = value
    with pytest.raises(ValueError):
        _validate_yuv_fidelity(row, DATA)


def test_unknown_source_range_requires_visible_disclosure():
    row = next(r for r in registry()['ra.thoracic-ultrasound'] if 'add2' in r['id'])
    row['limits'] = 'Undisclosed range'
    with pytest.raises(ValueError, match='color-range'):
        _validate_yuv_fidelity(row, DATA)


def test_quicktime_alias_external_reference_and_unsupported_avi_codec_fail_closed():
    rows = registry()['ra.thoracic-ultrasound']
    mov = next(r for r in rows if r['original_src'].endswith('.mov'))
    original = (ROOT / 'web' / mov['original_src'].removeprefix('/app/')).read_bytes()
    marker = b'\x00\x00\x00\x0calis\x00\x00\x00\x01'
    assert original.count(marker) == 1
    with pytest.raises(ValueError, match='External media'):
        parse_motion_contract(original.replace(marker, marker[:-1]+b'\x00'))
    avi = next(r for r in rows if r['original_src'].endswith('.avi'))
    original = (ROOT / 'web' / avi['original_src'].removeprefix('/app/')).read_bytes()
    assert original.count(b'MP42') == 1
    with pytest.raises(ValueError, match='codec'):
        parse_motion_contract(original.replace(b'MP42', b'FAKE'))


def test_stripping_yuv_fields_cannot_upgrade_known_source_to_legacy_rgb():
    rows = registry()
    row = rows['ra.thoracic-ultrasound'][0]
    row.pop('frame_fidelity')
    row.pop('decoded_YUV_frames_unchanged')
    row['decoded_RGB_frames_unchanged'] = True
    with pytest.raises(ValueError, match='relabelled'):
        validate_motion_references(rows, set(rows), ROOT / 'web')


def test_motion_ui_inverse_restores_exact_previous_app_and_rejects_other_changes():
    from tools.thoracic_motion_ui_compatibility import restore_previous_motion_ui, BEFORE
    app = (ROOT / 'web/app.js').read_text()
    restored = restore_previous_motion_ui(app)
    assert hashlib.sha256(restored.encode()).hexdigest() == BEFORE
    with pytest.raises(ValueError):
        restore_previous_motion_ui(app + '// unreviewed change\n')
