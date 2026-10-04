"""A positive source frame and MRI counterparts do not provide complete ultrasound clearance."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/cbd-stone-published-source-review'


def test_five_source_frames_preserve_original_pdf_streams_and_actual_modalities():
    source=json.loads((REVIEW/'original-source-review.json').read_text())
    packaged=json.loads((REVIEW/'packaged-source-images.json').read_text())
    assert len(source['figures'])==len(packaged['figures'])==5
    assert all(a['license']=='CC BY 4.0' for a in source['articles'])
    assert all('Alexander Muacevic' not in a['authors'] and 'John R Adler' not in a['authors'] for a in source['articles'])
    assert {r['pmcid'] for r in source['rights_holds']}=={'PMC8942730','PMC7559666'}
    for row in packaged['figures']:
        s=next(r for r in source['figures'] if (r['pmcid'],r['figure_number'])==(row['pmcid'],row['figure_number']))
        assert s['acquisition']=='original_pdf_dct_stream_byte_identical'
        raw=(ROOT/row['local_path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==s['sha256']==row['sha256']
        with Image.open(ROOT/row['local_path']) as image:
            assert image.size==(s['width'],s['height']) and hashlib.sha256(image.tobytes()).hexdigest()==s['decoded_pixel_sha256']
        assert s['publisher_media_md5_verified'] and s['original_encoded_stream_or_decoded_pixel_readback_verified']
        assert s['source_pixels_changed'] is False and s['clinical_approval'] is False


def test_reader_retains_unlettered_us_and_separate_ct_mri_context():
    ref=detail(Curriculum(),resolve('ra.ultrasound-bile-duct-stones'))['radiology_reference']
    rows={r['id']:r for r in ref['structure_atlas'] if r['id'].startswith('open-cbd-stone-')}
    assert len(rows)==5
    ultrasound=rows['open-cbd-stone-pmc12017295-fig1']
    assert ultrasound['modality']=='Ultrasound' and 'clinical_panels' not in ultrasound
    assert ultrasound['figure_url'].endswith('#FIG1')
    assert 'cannot exclude the whole clinical episode' in ultrasound['caption']
    assert rows['open-cbd-stone-pmc12017295-fig3']['modality']=='CT'
    assert rows['open-cbd-stone-pmc12463306-fig1']['modality']=='MRI'
    assert 'exact panel/site correspondence remains unapproved' in rows['open-cbd-stone-pmc12017295-fig5']['caption']


def test_new_sources_are_licensed_candidates_without_structure_credit():
    data=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text());rows=[r for r in data['assets'] if r['id'].startswith('open-cbd-stone-')]
    assert len(rows)==5
    for r in rows:
        assert r['structure_ids']==[] and r['requirement_coverage']=={} and r['anatomical_review']['status']=='pending'
        rights=r['source']['license'];assert rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT/rights['evidence_path']).read_bytes()).hexdigest()==rights['evidence_sha256']
