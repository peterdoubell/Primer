"""Original source identity and pixel conservation do not silently approve pelvic geometry."""
import gzip
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources.review_cvh5_pelvic_source import blocks, inventory

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/cvh5-pelvic-source-review'


def test_complete_original_stream_and_resource_mapping_are_conserved():
    r=json.loads((REVIEW/'original-model-inventory.json').read_text())
    packed=(REVIEW/r['retained_file']).read_bytes();raw=gzip.decompress(packed)
    assert hashlib.sha256(packed).hexdigest()==r['retained_sha256']
    assert len(raw)==10392492 and hashlib.sha256(raw).hexdigest()==r['u3d_sha256']=='90a7bbae314e1276c62fd9a3b0144bb8a9bacafc1f34f1cf36c4f26ed8b0fc3e'
    parsed=inventory(raw)
    assert parsed['model_nodes']==r['model_nodes'] and parsed['modifier_chains']==r['modifier_chains']
    assert len(r['top_level_blocks'])==181 and len(r['modifier_chains'])==96 and len(r['model_nodes'])==47
    assert set(i['resource_name'] for i in r['model_nodes'])==set(r['extension_mesh_resources'])
    assert len({i['name'] for i in r['model_nodes']})==47
    for name in ['Internal anal sphincter ','External anal sphincter','Mesorectum','Anal intermuscular septum','Vaginal wall','Perineal body']:
        assert name in {i['name'] for i in r['model_nodes']}
    assert all(any(i['type']=='0x100' for i in c['modifiers']) for c in r['modifier_chains'] if c['chain_type']==1)
    assert not r['decoded_geometry'] and not r['clinical_approval'] and not r['pdf_actions_or_scripts_executed']


def test_truncated_or_nonzero_padding_is_rejected():
    with pytest.raises(ValueError):blocks(b'\0'*11)
    # One byte of payload and three explicitly invalid alignment bytes.
    import struct
    with pytest.raises(ValueError):blocks(struct.pack('<III',0x123,1,0)+b'Xabc')
    with pytest.raises(ValueError):blocks(struct.pack('<III',0x123,100,0))


def test_all_native_section_samples_profiles_and_corrected_identities_remain_explicit():
    from PIL import Image
    r=json.loads((REVIEW/'source-review.json').read_text())
    assert r['article_xml_sha256']==hashlib.sha256((REVIEW/'source-article.xml').read_bytes()).hexdigest()
    assert r['correction_xml_sha256']==hashlib.sha256((REVIEW/'source-correction.xml').read_bytes()).hexdigest()
    assert r['source_metadata_sha256']==hashlib.sha256((REVIEW/'source-metadata.json').read_bytes()).hexdigest()
    assert r['model_pdf_source_id']=='pone.0132226.s003' and r['sections_pdf_source_id']=='pone.0132226.s004'
    assert len(r['sections'])==93 and [i['source_page'] for i in r['sections']]==list(range(1,94))
    assert r['model_node_count']==47 and r['source_caption_structure_count']==46 and not r['count_discrepancy_resolved']
    for i in r['sections']:
        p=REVIEW/i['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==i['sha256']
        with Image.open(p) as image:
            image.load();assert image.size==(466,530)
            assert hashlib.sha256(image.tobytes()).hexdigest()==i['decoded_pixel_sha256']
            assert hashlib.sha256(image.info['icc_profile']).hexdigest()==i['icc_sha256']
        assert not i['source_samples_or_profile_changed']
    assert r['source_setting']=='cadaveric' and not r['source_sections_are_clinical_MRI']
    assert not r['source_section_master_resolution_verified'] and not r['section_model_registration_verified']
    assert not r['arbitrary_anterior_pubovisceral_puborectal_partition_is_real_boundary']
    assert not r['positive_tumour_or_nodal_pathology_coverage_granted'] and not r['structure_coverage_granted']


def test_all_source_pages_are_in_context_without_substitution():
    r=json.loads((REVIEW/'section-context-review.json').read_text())
    assert r['source_review_sha256']==hashlib.sha256((REVIEW/'source-review.json').read_bytes()).hexdigest()
    assert [p for i in r['figures'] for p in i['source_pages']]==list(range(1,94))
    for i in r['figures']:assert hashlib.sha256((REVIEW/i['file']).read_bytes()).hexdigest()==i['sha256']


def test_original_pdf_stream_and_section_sample_readback_when_source_available():
    pypdf=pytest.importorskip('pypdf');from PIL import Image
    source=ROOT/'.research/anal-source-review'
    if not (source/'pone.0132226.s004.pdf').exists():pytest.skip('Full original PDFs remain in ignored research staging')
    r=json.loads((REVIEW/'source-review.json').read_text())
    pdf=pypdf.PdfReader(source/'pone.0132226.s004.pdf')
    for page,i in zip(pdf.pages,r['sections']):
        obj=next(iter(page['/Resources']['/XObject'].values())).get_object()
        assert hashlib.sha256(obj._data).hexdigest()==i['original_jpeg_stream_sha256']
        assert (source/f"independent-section-{i['source_page']-1:03d}.jpg").read_bytes()==obj._data
    pdf=pypdf.PdfReader(source/'pone.0132226.s003.pdf')
    obj=next(a.get_object() for a in pdf.pages[0]['/Annots'] if a.get_object().get('/Subtype')=='/3D')
    assert obj['/3DD'].get_data()==gzip.decompress((REVIEW/'original-model.u3d.gz').read_bytes())
