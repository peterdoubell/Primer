"""Cleared CTP pixel fidelity and enforced withdrawal of the conflicting native source."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/acute-stroke-source-review-20261011'
def sha(b):return hashlib.sha256(b).hexdigest()

def test_complete_ctp_packet_has_native_pixels_all_figures_and_no_coverage_approval():
    from PIL import Image
    p=json.loads((REVIEW/'ctp-integration-proposal.json').read_text());assert p['complete_numbered_figures']==13 and p['source_figure_objects']==22
    assert len(p['images'])==13 and len(p['assets'])==13
    for f in p['source_figures']:
        im=Image.open(ROOT/f['whole_native_display']['path']).convert('RGB');assert sha(im.tobytes())==f['whole_native_display']['decoded_RGB_sha256'];offset=0
        for obj in f['objects']:
            native=Image.open(ROOT/obj['native_display_path']).convert('RGB');assert im.crop((0,offset,im.width,offset+native.height)).tobytes()==native.tobytes();offset+=native.height
            assert sha((ROOT/obj['encoded_stream_path']).read_bytes())==obj['encoded_stream_sha256']
        assert f['source_pixels_changed'] is False and f['native_pixels_resampled'] is False
    assert p['native_display_RGB_pixels']==17052901
    for a in p['assets']:assert a['structure_ids']==[] and a['requirement_coverage']=={} and a['anatomical_review']['status']=='pending'
    for image in p['images']:assert image['source_context']['patient_3D_supplied'] is False


def test_conflicting_native_source_is_absent_from_public_and_runtime_tree():
    proof=json.loads((REVIEW/'native-publication-withdrawal-20261011.json').read_text())
    assert proof['native_publication_allowed'] is False
    assert proof['all_files_preserved_offline'] is True
    assert proof['moved_count']==42
    assert proof['historical_source_owner_receipt_unchanged_sha256']==sha((REVIEW/'source-owner-review.json').read_bytes())
    for row in proof['files']:
        assert not (ROOT/row['path']).exists(),row['path']
    assert not (ROOT/'web/anatomy/isles22-case0140').exists()
    for filename in ['data/radiology/native-source-inspectors.json','data/radiology/native-source-delivery.json','data/radiology/source-blob-delivery.json','vercel.json']:
        assert 'isles22-case0140' not in (ROOT/filename).read_text()
