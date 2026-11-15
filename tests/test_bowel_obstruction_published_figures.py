"""Original loop/phase examples do not supply native whole-loop geometry or viability guarantees."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/bowel-obstruction-published-source-review'


def test_all_ten_source_figures_preserve_original_encoded_pdf_streams():
    source=json.loads((REVIEW/'original-source-review.json').read_text());packaged=json.loads((REVIEW/'packaged-source-images.json').read_text())
    assert len(source['figures'])==len(packaged['figures'])==10
    assert all(a['license']=='CC BY 4.0' and a['publisher_xml_pdf_md5_verified'] for a in source['articles'])
    for row in packaged['figures']:
        s=next(r for r in source['figures'] if (r['pmcid'],r['figure_number'])==(row['pmcid'],row['figure_number']))
        assert s['acquisition']=='original_pdf_dct_stream_byte_identical'
        path=ROOT/row['local_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']==s['sha256']
        with Image.open(path) as im:
            assert im.size==(s['width'],s['height']) and hashlib.sha256(im.tobytes()).hexdigest()==s['decoded_pixel_sha256']
        assert s['publisher_media_md5_verified'] and s['source_pixels_changed'] is False


def test_reader_retains_original_phase_pairing_repeat_planes_and_distinct_mechanisms():
    ref=detail(Curriculum(),resolve('ra.ct-bowel-obstruction'))['radiology_reference'];rows={r['id']:r for r in ref['structure_atlas'] if r['id'].startswith('open-bowel-obstruction-')}
    assert len(rows)==10 and all(r['modality']=='CT' for r in rows.values())
    comparison=rows['open-bowel-obstruction-pmc10066158-fig2']
    assert comparison['clinical_panels']==['A','B']
    assert 'unenhanced CT A and enhanced CT B' in comparison['caption']
    assert 'not itself a mechanical-obstruction diagnosis' in comparison['caption']
    assert 'not counted as another acquisition or patient' in rows['open-bowel-obstruction-pmc10066158-fig4']['caption']
    assert 'not an independent case' in rows['open-bowel-obstruction-pmc4729712-fig4']['caption']
    assert 'clinical_panels' not in rows['open-bowel-obstruction-pmc4729712-fig3']


def test_licensed_source_frames_do_not_approve_wall_or_loop_coverage():
    data=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text());rows=[r for r in data['assets'] if r['id'].startswith('open-bowel-obstruction-')]
    assert len(rows)==10
    for row in rows:
        assert row['structure_ids']==[] and row['requirement_coverage']=={} and row['anatomical_review']['status']=='pending'
        rights=row['source']['license'];assert rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT/rights['evidence_path']).read_bytes()).hexdigest()==rights['evidence_sha256']
