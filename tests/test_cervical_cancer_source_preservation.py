"""Independent source-stream, sample, licensing and case-boundary preservation."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import struct
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as E
import zlib

from PIL import Image, ImageCms
import pytest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'docs/cervical-cancer-source-review'
MEDIA = ROOT / 'web/reference-media/radiology-open/cervical-cancer'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def artifacts():
    proof = json.loads((EVIDENCE / 'published-source-preservation.json').read_text())
    rows = json.loads((EVIDENCE / 'source-figure-contract.json').read_text())['structure_atlas']
    return proof, {r['id']:r for r in rows}


def unfilter(encoded, width, height, channels, tagged=True, fixed_filter=None):
    """Independent PNG/PDF prediction decoder; no PIL or packager decoder."""
    stride = width * channels; offset = 0; previous = bytes(stride); result = bytearray()
    for _row in range(height):
        kind = encoded[offset] if tagged else fixed_filter
        offset += int(tagged)
        current = bytearray(encoded[offset:offset + stride]); offset += stride
        assert len(current) == stride and kind in range(5)
        for i in range(stride):
            left = current[i - channels] if i >= channels else 0
            above = previous[i]
            corner = previous[i - channels] if i >= channels else 0
            if kind == 1: predictor = left
            elif kind == 2: predictor = above
            elif kind == 3: predictor = (left + above) // 2
            elif kind == 4:
                p = left + above - corner
                a,b,c = abs(p-left),abs(p-above),abs(p-corner)
                predictor = left if a <= b and a <= c else above if b <= c else corner
            else: predictor = 0
            current[i] = (current[i] + predictor) % 256
        result.extend(current); previous = bytes(current)
    assert offset == len(encoded)
    return bytes(result)


def png_rgb_samples(raw):
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    offset=8; compressed=[]; header=None
    while offset<len(raw):
        count=struct.unpack_from('>I',raw,offset)[0];kind=raw[offset+4:offset+8]
        data=raw[offset+8:offset+8+count]
        assert zlib.crc32(kind+data)&0xffffffff == struct.unpack_from('>I',raw,offset+8+count)[0]
        if kind==b'IHDR':header=struct.unpack('>IIBBBBB',data)
        if kind==b'IDAT':compressed.append(data)
        offset += 12+count
    width,height,depth,color,compression,filtering,interlace=header
    assert (depth,color,compression,filtering,interlace)==(8,2,0,0,0)
    return unfilter(zlib.decompress(b''.join(compressed)),width,height,3)


def native_pdf_flate_samples(stream, proof):
    raw=zlib.decompress(stream); params=proof['decode_parms'] or {}
    if isinstance(params,list):params=next((p for p in params if isinstance(p,dict)),{})
    predictor=int(params.get('/Predictor',1));channels=int(params.get('/Colors',3))
    width=int(params.get('/Columns',proof['width']))
    assert channels==3 and width==proof['width'] and int(params.get('/BitsPerComponent',8))==8
    if predictor==1:
        assert len(raw)==proof['width']*proof['height']*3
        return raw
    assert 10<=predictor<=15
    return unfilter(raw,width,proof['height'],channels,tagged=True)


def strip_jpeg_icc(raw):
    """Independently discard only ICC APP2 metadata, retaining the whole scan."""
    assert raw[:2]==b'\xff\xd8';position=2;result=bytearray(raw[:2])
    while position<len(raw):
        assert raw[position]==255
        marker=raw[position+1]
        if marker==0xda:
            result.extend(raw[position:]);return bytes(result)
        length=struct.unpack_from('>H',raw,position+2)[0]
        segment=raw[position:position+2+length]
        if not (marker==0xe2 and segment[4:].startswith(b'ICC_PROFILE\0')):
            result.extend(segment)
        position+=2+length
    raise AssertionError('JPEG scan missing')


def managed_rgb_samples(raw,profile,require_embedded=False):
    picture=Image.open(io.BytesIO(raw));picture.load()
    if require_embedded and picture.info.get('icc_profile')!=profile:
        raise ValueError('Original source ICC profile missing or changed')
    return ImageCms.profileToProfile(picture,ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                                     ImageCms.createProfile('sRGB'),outputMode='RGB').tobytes()


def test_all_32_complete_source_masters_keep_exact_native_streams_or_decoded_samples():
    proof,rows=artifacts()
    assert len(proof['figures'])==len(rows)==proof['figure_count']==32
    assert sum((MEDIA/f['runtime_file']).stat().st_size for f in proof['figures'])==proof['runtime_total_bytes']
    assert sum(r['kind']=='schematic' for r in rows.values())==2
    assert not list(EVIDENCE.glob('*.pdf'))  # Full PDFs with held graphics stay ignored.
    for figure in proof['figures']:
        row=rows[figure['id']];raw=(MEDIA/figure['runtime_file']).read_bytes()
        assert sha(raw)==figure['sha256']==row['sha256']
        picture=Image.open(io.BytesIO(raw));picture.load()
        assert picture.size==(figure['width'],figure['height'])==(row['width'],row['height'])
        assert picture.mode==figure['pixel_mode']
        assert sha(picture.tobytes())==figure['decoded_pixel_sha256']
        master=figure['source_master']
        streams=[]
        for record in figure['original_PDF_streams']:
            encoded=(EVIDENCE/record['file']).read_bytes();source=gzip.decompress(encoded)
            assert sha(encoded)==record['sha256'] and sha(source)==record['encoded_source_stream_sha256']
            assert len(source)==record['encoded_source_stream_bytes'] and record['bits_per_component']==8
            if record.get('original_ICC'):
                icc=record['original_ICC']
                assert sha((EVIDENCE/icc['file']).read_bytes())==icc['sha256']
                assert icc['channels'] in [1,3]
            streams.append(source)
        if master['kind']=='complete_original_PDF_image_stream':
            assert len(streams)==1 and raw==streams[0]
        elif master['kind']=='complete_original_PDF_JPEG_with_restored_original_ICC_metadata':
            assert len(streams)==1 and strip_jpeg_icc(raw)==streams[0]
            record=figure['original_PDF_streams'][0]
            profile=(EVIDENCE/record['original_ICC']['file']).read_bytes()
            assert picture.info['icc_profile']==profile
            assert managed_rgb_samples(raw,profile,require_embedded=True)==managed_rgb_samples(streams[0],profile)
        elif master['kind']=='lossless_PNG_of_complete_original_decoded_PDF_samples':
            assert len(streams)==1
            expected=native_pdf_flate_samples(streams[0],figure['original_PDF_streams'][0])
            assert png_rgb_samples(raw)==expected==picture.tobytes()
            icc=figure['original_PDF_streams'][0].get('original_ICC')
            if icc:assert picture.info['icc_profile']==(EVIDENCE/icc['file']).read_bytes()
        else:
            assert master['kind']=='complete_original_publisher_annotated_JPEG'
            assert hashlib.md5(raw).hexdigest()==master['publisher_md5']
            assert parse_qs(urlparse(master['source_url']).query)['md5']==[master['publisher_md5']]
            if figure['source_figure_label']=='Figure 2':
                assert 'seven vector arrows' in master['reason']
            else:
                assert 'no separate PDF vector overlay' in master['reason']
        assert not figure['source_pixels_modified']
        assert figure['complete_original_publication_annotations_retained']


def test_original_article_xml_captions_and_actual_ccby_grants_survive():
    proof,rows=artifacts()
    for article in proof['articles']:
        if 'pmcid' not in article:
            assert not article['whole_PDF_redistributed']
            assert article['no_figure3_1_third_party_credit']
            assert 'Creative Commons Attribution 4.0' in article['original_permissions_text']
            assert article['other_figure3_2_external_credit_requires_separate_rights_review']
            continue
        pmc=article['pmcid'];metadata=(EVIDENCE/(pmc+'-original-metadata.json')).read_bytes()
        xml=(EVIDENCE/(pmc+'-original.xml')).read_bytes();meta=json.loads(metadata)
        assert sha(metadata)==article['metadata_sha256'] and sha(xml)==article['xml_sha256']
        assert meta['license_code']=='CC BY' and not meta['is_retracted']
        assert hashlib.md5(xml).hexdigest()==parse_qs(urlparse(meta['xml_url']).query)['md5'][0]
        tree=E.fromstring(xml);permissions=E.tostring(tree.find('.//article-meta/permissions'),encoding='unicode')
        assert permissions==article['original_permissions_xml']
        assert 'https://creativecommons.org/licenses/by/4.0/' in permissions and 'by-nc' not in permissions
        for figure in [f for f in proof['figures'] if f.get('pmcid')==pmc]:
            original=tree.find('.//fig[@id="'+figure['source_figure_id']+'"]')
            assert original is not None and original.find('attrib') is None and original.find('permissions') is None
            caption=' '.join(''.join(original.find('caption').itertext()).split())
            assert caption==figure['source_caption_full']==rows[figure['id']]['source_caption_full']
            assert rows[figure['id']]['source_figure_label']==original.findtext('label')
            authors=', '.join(' '.join(filter(None,[n.findtext('given-names'),n.findtext('surname')]))
                             for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name'))
            assert article['authors']==authors and rows[figure['id']]['attribution'].startswith(authors+'. ')


def test_mixed_case_modalities_and_treatment_timepoints_remain_separate():
    from primer.radiology_catalog import _validate_source_panel_roles
    proof,rows=artifacts()
    for row in rows.values():
        _validate_source_panel_roles(row)
        context=row['source_context']
        assert not context['source_panels_independently_registered']
        assert not context['native_acquisition_arrays_included']
        assert not context['independent_calibrated_measurements_verified']
        assert not context['biological_3d_model_created_from_artwork']
        assert not context['different_figures_assumed_same_patient']
        if context['different_panels_assumed_same_patient']:
            assert context['single_case_link_basis']
            assert len(context['source_case_groups'])==1
        if row['kind']=='clinical-image':
            assert row['modality']=='MRI'
            assert all(context['panel_types'][p]=='MRI' for p in row['clinical_panels'])
    bladder=rows['open-cervical-cancer-pmc10605640-fig11']['source_context']
    assert bladder['source_case_groups']=={'different_source_patient_a':['a'],'different_source_patient_bc':['b','c']}
    assert not bladder['different_panels_assumed_same_patient']
    comparison=rows['open-cervical-cancer-pmc10886638-fig4']['source_context']
    assert len(comparison['source_case_groups'])==2 and not comparison['different_panels_assumed_same_patient']
    assert '3 cm' in comparison['source_scope_issue'] and 'without silently assigning a new FIGO stage' in comparison['source_scope_issue']
    fused=rows['open-cervical-cancer-pmc10886638-fig11']
    assert fused['clinical_panels']==['a','b','d']
    assert fused['ancillary_panels'][0]['kind']=='Nuclear medicine' and fused['ancillary_panels'][0]['panels']==['c','e']
    assert 'PET-CT' in fused['source_caption_full'] and 'PET-MRI' in fused['source_context']['source_scope_issue']
    recurrence=rows['open-cervical-cancer-pmc10605640-fig18']['source_context']
    assert recurrence['source_timepoint_groups']=={'initial_staging':['a'],'6_month_post_treatment':['b'],'later_symptomatic_recurrence':['c','d']}
    assert recurrence['different_panels_assumed_same_patient']
    for n in [14,15,16]:assert rows['open-cervical-cancer-pmc10605640-fig'+str(n)]['source_context']['source_phase']=='during_brachytherapy'
    for key in ['clinical_approval','complete_reporting_anatomy_approved','every_structure_approved','fine_3D_tissue_layers_supplied',
                'native_acquisition_arrays_included','patient_calibration_or_lesion_registration_verified']:
        assert proof[key] is False
    assert rows['open-cervical-cancer-normal-uterus-2018-fig3-1']['figure_number']=='3.1'


def test_stripping_the_original_icc_cannot_pass_source_appearance_even_with_identical_pixel_samples():
    proof,_rows=artifacts()
    tested=0
    for figure in proof['figures']:
        if figure['source_master']['kind']!='complete_original_PDF_JPEG_with_restored_original_ICC_metadata':continue
        tagged=(MEDIA/figure['runtime_file']).read_bytes();stripped=strip_jpeg_icc(tagged)
        profile=(EVIDENCE/figure['original_PDF_streams'][0]['original_ICC']['file']).read_bytes()
        assert Image.open(io.BytesIO(tagged)).tobytes()==Image.open(io.BytesIO(stripped)).tobytes()
        with pytest.raises(ValueError,match='ICC profile missing'):
            managed_rgb_samples(stripped,profile,require_embedded=True)
        tested+=1
    assert tested==20


def test_raw_ignored_original_pdf_objects_match_committed_source_streams_when_available():
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    proof,_rows=artifacts()
    found=False
    for article in proof['articles']:
        path=Path(article['original_pdf_ignored_staging_path'])
        if not path.is_file():continue
        found=True;raw=path.read_bytes()
        assert sha(raw)==article['pdf_sha256'] and len(raw)==article['pdf_bytes']
        if 'pmcid' in article:
            meta=json.loads((EVIDENCE/(article['pmcid']+'-original-metadata.json')).read_text())
            assert hashlib.md5(raw).hexdigest()==parse_qs(urlparse(meta['pdf_url']).query)['md5'][0]
            figures=[f for f in proof['figures'] if f.get('pmcid')==article['pmcid']]
        else:figures=[f for f in proof['figures'] if f['id']=='open-cervical-cancer-normal-uterus-2018-fig3-1']
        reader=PdfReader(io.BytesIO(raw))
        for figure in figures:
            for stream in figure['original_PDF_streams']:
                obj=reader.get_object(IndirectObject(stream['original_object'],0,reader))
                expected=gzip.decompress((EVIDENCE/stream['file']).read_bytes())
                assert obj._data==expected
                assert int(obj['/Width'])==stream['width'] and int(obj['/Height'])==stream['height']
    if not found:pytest.skip('Original acquisition PDFs are intentionally ignored; committed exact streams are verified above')
