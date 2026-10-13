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
EVIDENCE = ROOT / 'docs/endometrial-cancer-source-review'
MEDIA = ROOT / 'web/reference-media/radiology-open/endometrial-cancer'


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


def test_complete_masters_keep_original_streams_samples_and_source_color_appearance():
    proof,rows=artifacts()
    assert len(proof['figures'])==len(rows)==proof['figure_count']==36
    assert sum((MEDIA/f['runtime_file']).stat().st_size for f in proof['figures'])==proof['runtime_total_bytes']<20*1024*1024
    assert not list(EVIDENCE.rglob('*.pdf')) and not list(MEDIA.rglob('*.pdf'))
    for f in proof['figures']:
        raw=(MEDIA/f['runtime_file']).read_bytes();row=rows[f['id']];p=Image.open(io.BytesIO(raw));p.load()
        assert sha(raw)==f['sha256']==row['sha256']
        assert p.size==(f['width'],f['height'])==(row['width'],row['height']) and p.mode==f['pixel_mode']
        assert sha(p.tobytes())==f['decoded_pixel_sha256']
        assert len(f['original_PDF_streams'])==1
        record=f['original_PDF_streams'][0];encoded=(EVIDENCE/record['file']).read_bytes();original=gzip.decompress(encoded)
        assert sha(encoded)==record['sha256'] and sha(original)==record['encoded_source_stream_sha256']
        assert len(original)==record['encoded_source_stream_bytes'] and record['bits_per_component']==8
        master=f['source_master']['kind']
        if master=='complete_original_PDF_JPEG':
            assert raw==original and p.tobytes()==Image.open(io.BytesIO(original)).tobytes()
        elif master=='complete_original_PDF_JPEG_with_restored_original_ICC_metadata':
            assert strip_jpeg_icc(raw)==original
            assert p.tobytes()==Image.open(io.BytesIO(original)).tobytes()
        else:
            assert master=='lossless_PNG_of_complete_original_decoded_PDF_samples'
            assert png_rgb_samples(raw)==native_pdf_flate_samples(original,record)==p.tobytes()
        if record.get('original_ICC'):
            profile=(EVIDENCE/record['original_ICC']['file']).read_bytes()
            assert sha(profile)==record['original_ICC']['sha256'] and p.info.get('icc_profile')==profile
            source_image=Image.open(io.BytesIO(original)) if record['filter']=='/DCTDecode' else Image.frombytes('RGB',p.size,native_pdf_flate_samples(original,record))
            source_rgb=ImageCms.profileToProfile(source_image,ImageCms.ImageCmsProfile(io.BytesIO(profile)),ImageCms.createProfile('sRGB'),outputMode='RGB').tobytes()
            assert managed_rgb_samples(raw,profile,require_embedded=True)==source_rgb
        assert f['source_pixels_modified'] is False and f['complete_original_publication_annotations_retained'] is True
        assert f['annotation_preservation']['source_vector_or_text_annotation_loss'] is False


def test_explicit_commercial_grants_original_captions_and_author_only_credits():
    proof,rows=artifacts()
    for article in proof['articles']:
        assert article['whole_PDF_redistributed'] is False
        if article.get('source_id')=='ESR2026':
            record=(EVIDENCE/article['license_and_caption_evidence_file']).read_bytes();licence=json.loads(record)
            assert sha(record)==article['license_and_caption_evidence_sha256']
            assert licence['license_url']=='https://creativecommons.org/licenses/by/4.0/' and licence['commercial_use'] and licence['redistribution']
            assert licence['selected_figure_has_no_third_party_credit'] and not licence['whole_PDF_redistributed']
            assert 'Common pitfalls in the imaging interpretation of endometrial cancer' in licence['original_figure_HTML_fragment']
            assert 'Creative Commons Attribution 4.0' in licence['original_permissions_HTML_fragment']
            assert rows['open-endometrial-cancer-esr2026-fig5']['source_caption_full']==licence['source_caption_full']
            continue
        pmc=article['pmcid'];meta_raw=(EVIDENCE/(pmc+'-original-metadata.json')).read_bytes();xml=(EVIDENCE/(pmc+'-original.xml')).read_bytes();meta=json.loads(meta_raw)
        assert sha(meta_raw)==article['metadata_sha256'] and sha(xml)==article['xml_sha256']
        assert meta['license_code']=='CC BY' and not meta['is_retracted'] and meta['is_pmc_openaccess']
        assert hashlib.md5(xml).hexdigest()==parse_qs(urlparse(meta['xml_url']).query)['md5'][0]
        tree=E.fromstring(xml);grant=E.tostring(tree.find('.//article-meta/permissions'),encoding='unicode')
        assert grant==article['original_permissions_xml'] and article['license_url'] in grant and 'by-nc' not in grant
        authors=', '.join(' '.join(filter(None,[n.findtext('given-names'),n.findtext('surname')])) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name'))
        assert authors==article['authors']
        for f in [f for f in proof['figures'] if f.get('pmcid')==pmc]:
            source=tree.find('.//fig[@id="'+f['source_figure_id']+'"]');caption=' '.join(''.join(source.find('caption').itertext()).split())
            assert caption==f['source_caption_full']==rows[f['id']]['source_caption_full']
            assert source.find('attrib') is None and source.find('permissions') is None
            assert rows[f['id']]['source_figure_label']==source.findtext('label')
            assert rows[f['id']]['attribution'].startswith(authors+'. ')
    assert rows['open-endometrial-cancer-pmc8648287-fig5']['license']=='CC BY 3.0'


def test_separate_source_cases_modalities_figo_versions_and_holds_cannot_be_conflated():
    from primer.radiology_catalog import _validate_source_panel_roles
    proof,rows=artifacts()
    for row in rows.values():
        _validate_source_panel_roles(row);context=row['source_context']
        assert set(context['panel_types'])==set(context['all_source_panels'])
        assert set(row['clinical_panels'])==set(context['selected_panels'])
        occupied=list(context['selected_panels'])+[p for group in row.get('ancillary_panels',[]) for p in group['panels']]
        assert len(occupied)==len(set(occupied))==len(context['panel_types'])
        for field in ['source_panels_independently_registered','native_acquisition_arrays_included','independent_calibrated_measurements_verified','biological_3d_model_created_from_artwork','current_patient_findings','different_figures_assumed_same_patient']:
            assert context[field] is False
        if context['different_panels_assumed_same_patient']:
            assert context['single_case_link_basis'] and len(context['source_case_groups'])==1
        assert 'microscopic LVSI' in row['limits'] and 'registered 3D' in row['limits']
    assert rows['open-endometrial-cancer-pmc11119523-fig16']['source_context']['panel_types']==dict(a='MRI',b='MRI',c='CT',d='CT')
    assert rows['open-endometrial-cancer-pmc11119523-fig19']['clinical_panels']==['a','d']
    assert rows['open-endometrial-cancer-pmc11119523-fig19']['ancillary_panels'][0]['panels']==list('bcef')
    recurrence=rows['open-endometrial-cancer-pmc7643338-fig3']['source_context']
    assert len(recurrence['source_case_groups'])==3 and not recurrence['different_panels_assumed_same_patient']
    assert recurrence['same_case_panel_pairs']==[['a','b'],['c','d'],['e','f']]
    assert not rows['open-endometrial-cancer-pmc7643338-fig2']['source_context']['different_panels_assumed_same_patient']
    assert len(rows['open-endometrial-cancer-pmc8648287-fig4']['source_context']['source_case_groups'])==2
    assert 'FIGO 2009' in rows['open-endometrial-cancer-pmc8648287-fig4']['source_context']['source_staging_framework']
    assert 'one_year_post' in rows['open-endometrial-cancer-pmc8648287-fig5']['source_context']['source_phase']
    assert not rows['open-endometrial-cancer-esr2026-fig5']['source_context']['different_panels_assumed_same_patient']
    assert 'IVB' in rows['open-endometrial-cancer-esr2026-fig5']['limits'] and 'IVC' in rows['open-endometrial-cancer-esr2026-fig5']['limits']
    assert 'IIIB2POLEmut' in rows['open-endometrial-cancer-pmc11119523-fig11']['source_caption_full']
    assert 'not endorsed' in rows['open-endometrial-cancer-pmc11119523-fig11']['limits']
    assert 'stages I/II' in rows['open-endometrial-cancer-pmc11119523-fig11']['limits']
    assert 'stages III/IV molecular class may be recorded with m without changing' in rows['open-endometrial-cancer-pmc11119523-fig11']['limits']
    peritoneal=rows['open-endometrial-cancer-pmc11119523-fig15']
    assert 'pelvic peritoneal' not in peritoneal['caption'].lower() and 'Peritoneal implant' in peritoneal['structures_visible']
    assert 'author-supplied' in peritoneal['limits'] and 'complete peritoneal distribution' in peritoneal['limits']
    assert rows['open-endometrial-cancer-pmc11119523-fig19']['structures_visible']==['Bladder base','Urethra']
    assert 'open-endometrial-cancer-pmc11119523-fig3' not in rows
    for field in ['clinical_approval','complete_reporting_anatomy_approved','every_structure_approved','fine_3D_tissue_layers_supplied','native_acquisition_arrays_included','patient_calibration_or_lesion_registration_verified']:
        assert proof[field] is False


def test_stripped_or_changed_icc_cannot_pass_source_appearance_with_identical_samples():
    proof,_rows=artifacts();tested=0
    for f in proof['figures']:
        if f['source_master']['kind']!='complete_original_PDF_JPEG_with_restored_original_ICC_metadata':continue
        raw=(MEDIA/f['runtime_file']).read_bytes();stripped=strip_jpeg_icc(raw);profile=(EVIDENCE/f['original_PDF_streams'][0]['original_ICC']['file']).read_bytes()
        assert Image.open(io.BytesIO(raw)).tobytes()==Image.open(io.BytesIO(stripped)).tobytes()
        with pytest.raises(ValueError,match='ICC profile missing'):managed_rgb_samples(stripped,profile,require_embedded=True)
        with pytest.raises(ValueError,match='ICC profile missing'):managed_rgb_samples(raw,profile[:-1],require_embedded=True)
        tested+=1
    assert tested==14


def test_independent_original_pdf_readback_and_spatial_figure_identity_when_available():
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    proof,_rows=artifacts()
    if not any(Path(a['original_pdf_ignored_staging_path']).is_file() for a in proof['articles']):
        pytest.skip('Ignored original acquisition masters are not present in this checkout')
    pymupdf=pytest.importorskip('pymupdf')
    checked=0
    for article in proof['articles']:
        path=Path(article['original_pdf_ignored_staging_path'])
        if not path.exists():continue
        raw=path.read_bytes();assert sha(raw)==article['pdf_sha256'] and len(raw)==article['pdf_bytes'];reader=PdfReader(io.BytesIO(raw));view=pymupdf.open(stream=raw,filetype='pdf')
        for f in [f for f in proof['figures'] if f.get('pmcid',f.get('source_id'))==article.get('pmcid',article.get('source_id'))]:
            record=f['original_PDF_streams'][0];obj=reader.get_object(IndirectObject(record['original_object'],0,reader))
            assert obj._data==gzip.decompress((EVIDENCE/record['file']).read_bytes())
            original=next(i for i in reader.pages[f['source_PDF_page']-1].images if i.indirect_reference.idnum==record['original_object'])
            # pypdf's exported image object may re-encode its JPEG. Decode the
            # original encoded stream directly, without that export round trip.
            native_samples=(Image.open(io.BytesIO(obj._data)).tobytes() if record['filter']=='/DCTDecode'
                            else native_pdf_flate_samples(obj._data,record))
            assert native_samples==Image.open(MEDIA/f['runtime_file']).tobytes()
            # Image placement precedes this figure's visible numbered caption.
            page=view[f['source_PDF_page']-1];rect=next(x['bbox'] for x in page.get_image_info(xrefs=True) if x['xref']==record['original_object'])
            label=f['source_figure_label'];candidate=[b for b in page.get_text('blocks') if b[4].startswith(label+'.') or b[4].startswith(label+'\u2002') or b[4].startswith(label+' ') or b[4].startswith(label+'\n')]
            if f.get('pmcid') not in ['PMC7643338','PMC8648287'] and f.get('source_id')!='ESR2026':
                assert candidate and any(0<=b[1]-rect[3]<25 for b in candidate), (f['id'],label,rect,candidate)
            checked+=1
    if not checked:pytest.skip('Ignored original acquisition masters are not present in this checkout')
    assert checked==36


def test_recorded_actual_browser_appearance_cannot_be_reused_after_source_change():
    proof,rows=artifacts();review=json.loads((EVIDENCE/'browser-source-appearance-review.json').read_text())
    assert review['source_contract_sha256']==sha((EVIDENCE/'source-figure-contract.json').read_bytes())
    assert review['all_native_image_requests_SHA_verified'] and review['all_complete_native_extents_verified']
    assert review['figure_count']==len(review['results'])==36 and {r['id'] for r in review['results']}==set(rows)
    for result in review['results']:
        row=rows[result['id']];figure=next(f for f in proof['figures'] if f['id']==row['id']);stream=figure['original_PDF_streams'][0]
        assert result['sha256']==row['sha256']==sha((MEDIA/result['runtime_file']).read_bytes())
        assert (result['natural_width'],result['natural_height'])==(row['width'],row['height'])
        assert result['native_stream_sha256']==stream['encoded_source_stream_sha256']
        assert result['native_ICC_sha256']==stream.get('original_ICC',{}).get('sha256')
        assert result['runtime_vs_original_samples_and_ICC_max_RGB_difference']==0
        assert result['runtime_vs_original_samples_and_ICC_different_RGB_channels']==0
        assert result['runtime_vs_independent_LCMS_sRGB_max_RGB_difference']<=1
    assert not review['clinical_approval'] and not review['fine_3D_layers_approved'] and not review['patient_registration_verified']


def test_actual_reader_browser_retains_every_original_and_nine_unfilled_areas():
    proof,rows=artifacts()
    # Preserve both prior reviews; bridge only this exact app revision.
    historical_raw=(EVIDENCE/'browser-integration-review.json').read_bytes()
    amendment_raw=(EVIDENCE/'browser-compatibility-amendment-20261011.json').read_bytes()
    previous_raw=(EVIDENCE/'browser-compatibility-amendment-algebra-trauma-20261011.json').read_bytes()
    current_raw=(EVIDENCE/'browser-compatibility-amendment-stroke-source-case-20261011.json').read_bytes()
    assert sha(previous_raw)=='8f048b16048e9f1c83a0e01eb7b487d26ccded97af09fdf5152b99388ac405b1'
    assert sha(current_raw)=='973279ee5d5c3a0067dee71fef8ed62fea9c2d5287f397c8fd792e24b2db5f79'
    assert sha(historical_raw)=='eb09ba589f99e695d833aa0cd5d29c232b313a986652b93390eea633842799a5'
    assert sha(amendment_raw)=='0571958acfe92cc2750580a8daee68b7109a728530f230365225e01dfbcffcd2'
    historical=json.loads(historical_raw);amendment=json.loads(amendment_raw);previous=json.loads(previous_raw);current=json.loads(current_raw)
    assert amendment['historical_review_sha256']==sha(historical_raw)
    assert amendment['historical_app_js_sha256']==historical['app_js_sha256']=='4c88dab41f6e1e3d1b1b3c15721dc9d45eade4441fc6725df52a871e2464e563'
    assert amendment['app_js_sha256']=='be5ea9dcc4f1e44049a007771a6bb265e0d73c448a0df70c6e190084a42b468f'
    assert previous['app_js_sha256']=='a8dc2985ad28ed9a9b07bd17f87857b3bc389feb7d316049f66ff8f3cf22d29d'
    from tools.anatomy_sources.pulmonary_ui_compatibility import restore_previous_app
    # The prior receipt still binds d77 exactly; undo only the three recorded pulmonary functions.
    assert current['app_js_sha256']==sha(restore_previous_app().encode())=='d77de3b299fc8af358e6c5fd2c785b22f3a8f19aa89f27a713d40be7c22b11a0'
    assert current['historical_review_sha256']==sha(historical_raw)
    assert current['historical_app_js_sha256']==historical['app_js_sha256']
    assert previous['previous_compatibility_amendment_sha256']==sha(amendment_raw)
    assert previous['previous_compatibility_app_js_sha256']==amendment['app_js_sha256']
    assert current['previous_compatibility_amendment_sha256']==sha(previous_raw)
    assert current['previous_compatibility_app_js_sha256']==previous['app_js_sha256']
    assert current['preserved_earlier_compatibility_amendment_sha256']==sha(amendment_raw)
    assert current['native_citation_wrapper_code_touched'] is True
    assert current['native_decoder_mesh_CT_renderer_code_touched'] is False
    assert current['new_explicit_metadata_field']=='publication_url'
    assert current['old_atlas_citation_fallback_unchanged']
    assert current['app_bytes_outside_changed_function_identical']
    assert current['historical_approval_scope_unchanged'] and not current['supersedes_historical_review']
    assert not current['supersedes_previous_compatibility_amendment']
    assert current['authenticated_reader'] and current['disposable_database_and_backups']
    assert not current['persistent_browser_profile_used'] and not current['production_or_deployment_verification']
    assert current['browser_and_contexts_closed'] and current['server_shutdown_owned_by_parent']
    assert current['unchanged_native_manifest_sha256']==sha((ROOT/'web/anatomy/hra-female-pelvis-v1.10/manifest.json').read_bytes())
    assert current['reviewed_visual_capture_count']==sum(len(r['screenshots']) for r in current['results'])
    for result in current['results']:
        assert result['served_app_js_sha256']==current['app_js_sha256']
        assert result['served_detailed_anatomy_js_sha256']==current['detailed_anatomy_js_sha256']
        assert result['source_context_documents_absent'] and result['api_source_context_documents_absent']
        assert result['source_context_document_checks']
        assert all(check['document_count']==0 for check in result['source_context_document_checks'])
        assert all(s['file'].startswith('stroke-source-case-20261011-') for s in result['screenshots'])
    assert amendment['historical_approval_scope_unchanged'] and not amendment['supersedes_historical_review']
    assert amendment['authenticated_reader'] and amendment['disposable_database_and_backups']
    assert not amendment['persistent_browser_profile_used'] and not amendment['production_or_deployment_verification']
    assert amendment['unchanged_native_manifest_sha256']==sha((ROOT/'web/anatomy/hra-female-pelvis-v1.10/manifest.json').read_bytes())
    assert previous['historical_review_sha256']==sha(historical_raw)
    assert previous['historical_app_js_sha256']==historical['app_js_sha256']
    assert previous['historical_approval_scope_unchanged'] and not previous['supersedes_historical_review']
    assert not previous['supersedes_previous_compatibility_amendment']
    assert previous['authenticated_reader'] and previous['disposable_database_and_backups']
    assert previous['browser_and_contexts_closed'] and previous['server_shutdown_owned_by_parent']
    assert previous['reviewed_visual_capture_count']==sum(len(r['screenshots']) for r in previous['results'])
    for result in previous['results']:
        assert result['served_app_js_sha256']==previous['app_js_sha256']
        assert result['source_context_documents_absent'] and result['api_source_context_documents_absent']
        assert all(s['file'].startswith('algebra-trauma-20261011-') for s in result['screenshots'])
    for review in [historical,amendment,previous,current]:
        assert review['all_requested_routes_and_viewports_passed'] and review['owned_isolated_qa_server']
        assert review['source_contract_sha256']==sha((EVIDENCE/'source-figure-contract.json').read_bytes())
        assert review['detailed_anatomy_js_sha256']==sha((ROOT/'web/radiology-detailed-anatomy.js').read_bytes())
        assert {(r['route'],r['viewport']['width']) for r in review['results']}=={('reporting',1440),('reporting',390),('lesson',1440),('lesson',390)}
        manifest=json.loads((ROOT/'web/anatomy/hra-female-pelvis-v1.10/manifest.json').read_text())
        parts={p['file']:p for p in manifest['parts'].values()}
        for result in review['results']:
            assert result['complete_endometrial_figure_count']==36 and result['all_native_image_response_hashes_match']
            assert {r['id'] for r in result['image_responses']}==set(rows)
            for response in result['image_responses']:
                assert response['status']==200 and response['sha256']==rows[response['id']]['sha256']
            assert result['source_case_modality_staging_limits_visible'] and result['enlarged_originals_and_native_size_control_verified']
            assert result['no_held_remote_ra_images'] and not result['horizontal_overflow']
            assert not result['page_errors'] and not result['failed_requests']
            assert result['native_reference_viewer_count']==1 and result['native_reference_mesh_count']==54
            assert result['all54_source_objects_GPU_drawn'] and result['native_reference_uncropped'] and result['native_reference_is_independent_and_unregistered']
            assert len(result['mesh_responses'])==54 and {r['path'] for r in result['mesh_responses']}==set(parts)
            for response in result['mesh_responses']:
                assert response['status']==200 and response['sha256']==parts[response['path']]['decoded_sha256']
                assert response['vertices']==parts[response['path']]['vertices'] and response['triangles']==parts[response['path']]['triangles']
            native=result['native_reference']
            assert native['native_y_up'] and native['cropped']=='false' and len(native['draw_calls'])==54
            assert sum(p['count'] for p in native['draw_calls'])==293490*3
            assert native['labelRects']['vertical_overlap_pixels']==0 and result['source_labels_nonoverlap']
            if result['route']=='reporting':
                assert result['assessment_step_count']==9 and result['only_source_matched_step_images'] and result['assessment_prompts_do_not_assert_normality']
                assert len(result['assessment']['steps'])==9 and all(s['unfilled_assessment_prompts'] for s in result['assessment']['steps'])
                assert result['assessment']['assembled_report_has_all_sections']
            assert len(result['screenshots'])==5
            for screenshot in result['screenshots']:assert sha((EVIDENCE/screenshot['file']).read_bytes())==screenshot['sha256']
        assert not review['clinical_approval'] and not review['every_structure_approved'] and not review['fine_3D_tissue_layers_approved'] and not review['patient_registration_verified']



def test_pulmonary_source_only_amendment_preserves_current_legacy_browser_evidence():
    from tools.anatomy_sources import pulmonary_ui_compatibility as bridge
    raw=(EVIDENCE/'browser-compatibility-amendment-pulmonary-source-only-20261011.json').read_bytes()
    assert sha(raw)=='50115182dd33a7ff1150468d358a35e34d54094570cd67cbf9d4abf6093fd701'
    amendment=json.loads(raw)
    assert amendment['schema_version']==1
    from tools.thoracic_motion_ui_compatibility import restore_previous_motion_ui
    from tools.thoracic_data_compatibility import restore_raw
    assert amendment['app_js_sha256']==bridge.AFTER==sha(restore_previous_motion_ui((ROOT/'web/app.js').read_text()).encode())
    assert amendment['previous_app_js_sha256']==bridge.BEFORE==sha(bridge.restore_previous_app().encode())
    assert amendment['native_presentation_change_scope']=='pulmonary_source_only_mounting'
    assert amendment['historical_approval_scope_unchanged'] is True
    for field in ['clinical_approval','fine_anatomical_approval','structure_coverage_granted',
                  'current_patient_registration','every_structure_approved','fine_3D_tissue_layers_approved',
                  'patient_registration_verified','whole_goal_complete','supersedes_historical_review',
                  'supersedes_previous_compatibility_amendment','supersedes_any_historical_receipt',
                  'historical_capture_reconstruction_or_replacement','production_or_deployment_verification',
                  'native_decoder_mesh_CT_renderer_code_touched',
                  'server_restart_or_shutdown_performed_by_amendment_agent']:
        assert amendment[field] is False
    for filename,digest in amendment['preserved_historical_receipts_sha256'].items():
        assert sha((EVIDENCE/filename).read_bytes())==digest
    assert len(amendment['preserved_historical_receipts_sha256'])==4
    previous=json.loads((EVIDENCE/'browser-compatibility-amendment-stroke-source-case-20261011.json').read_bytes())
    assert amendment['previous_compatibility_amendment_sha256']==sha((EVIDENCE/'browser-compatibility-amendment-stroke-source-case-20261011.json').read_bytes())
    assert amendment['unchanged_native_manifest_sha256']==previous['unchanged_native_manifest_sha256']==sha((ROOT/'web/anatomy/hra-female-pelvis-v1.10/manifest.json').read_bytes())
    inverse=amendment['exact_app_inverse']
    assert inverse['path']==bridge.DELTA and inverse['sha256']==bridge.DELTA_SHA
    assert sha(restore_raw(inverse['helper_path'], (ROOT/inverse['helper_path']).read_bytes()))==inverse['helper_sha256']
    assert inverse['changed_functions']==['sourceNativeInspector','renderRadiologyDesk','renderReportWalkthrough']
    assert inverse['app_bytes_outside_changed_functions_identical'] is True
    assert inverse['reconstructed_previous_app_sha256']==bridge.BEFORE
    delta=json.loads((ROOT/bridge.DELTA).read_bytes())
    assert amendment['guarded_paths_sha256']==delta['guarded_paths_sha256']
    assert amendment['native_reader_smoke']==delta['native_reader_smoke']
    assert sha((ROOT/amendment['native_reader_smoke']['path']).read_bytes())==amendment['native_reader_smoke']['sha256']
    for path,digest in amendment['guarded_paths_sha256'].items():
        assert sha((ROOT/path).read_bytes())==digest
    browser_record=amendment['browser_review']
    assert browser_record['path']=='docs/pulmonary-nodule-integration-review-20261011/compatibility-browser/endometrial/review.json'
    browser_raw=(ROOT/browser_record['path']).read_bytes()
    assert sha(browser_raw)==browser_record['sha256']
    browser=json.loads(browser_raw)
    assert browser['all_requested_routes_and_viewports_passed'] is True and browser['owned_isolated_qa_server'] is True
    assert browser['app_js_sha256']==bridge.AFTER
    assert browser['source_contract_sha256']==amendment['source_contract_sha256']==sha((EVIDENCE/'source-figure-contract.json').read_bytes())
    assert browser['detailed_anatomy_js_sha256']==amendment['detailed_anatomy_js_sha256']==sha((ROOT/'web/radiology-detailed-anatomy.js').read_bytes())
    assert {(row['route'],row['viewport']['width']) for row in browser['results']}=={('reporting',1440),('reporting',390),('lesson',1440),('lesson',390)}
    original_rows=json.loads((EVIDENCE/'source-figure-contract.json').read_bytes())['structure_atlas']
    originals={row['id']:row for row in original_rows}
    manifest=json.loads((ROOT/'web/anatomy/hra-female-pelvis-v1.10/manifest.json').read_bytes())
    parts={row['file']:row for row in manifest['parts'].values()}
    for result in browser['results']:
        assert result['served_app_js_sha256']==bridge.AFTER
        assert result['served_detailed_anatomy_js_sha256']==amendment['detailed_anatomy_js_sha256']
        assert result['complete_endometrial_figure_count']==36
        assert result['all_native_image_response_hashes_match'] is True
        assert {row['id'] for row in result['image_responses']}==set(originals)
        for response in result['image_responses']:
            original=originals[response['id']]
            body=(ROOT/'web'/original['src'].removeprefix('/app/')).read_bytes()
            assert response['status']==200 and response['src']==original['src']
            assert response['sha256']==original['sha256']==sha(body) and response['bytes']==len(body)
        assert all(row['complete'] and row['source_caption_full_matches'] and row['case_modality_limits_visible'] and row['display_filter']=='none' for row in result['figure_checks'])
        assert result['source_case_modality_staging_limits_visible'] is True
        assert result['enlarged_originals_and_native_size_control_verified'] is True and result['no_held_remote_ra_images'] is True
        assert all(row['native_size_control'] and row['original'] for row in result['enlarged'])
        assert result['native_reference_viewer_count']==1 and result['native_reference_mesh_count']==54
        assert result['all54_source_objects_GPU_drawn'] is True and result['native_reference_uncropped'] is True
        assert result['native_reference_is_independent_and_unregistered'] is True
        assert len(result['mesh_responses'])==54 and {row['path'] for row in result['mesh_responses']}==set(parts)
        for response in result['mesh_responses']:
            part=parts[response['path']]
            assert response['status']==200 and response['sha256']==part['decoded_sha256']
            assert response['vertices']==part['vertices'] and response['triangles']==part['triangles']
        native=result['native_reference']
        assert native['native_y_up'] is True and native['cropped']=='false' and len(native['draw_calls'])==54
        assert sum(row['count'] for row in native['draw_calls'])==293490*3
        assert result['source_labels_nonoverlap'] is True and native['labelRects']['vertical_overlap_pixels']==0
        assert result['page_errors']==[] and result['failed_requests']==[] and result['horizontal_overflow'] is False
        if result['route']=='reporting':
            assert result['assessment_step_count']==9 and result['only_source_matched_step_images'] is True
            assert result['assessment_prompts_do_not_assert_normality'] is True
            assert result['assessment']['all_prompts_unfilled'] is True and result['assessment']['assembled_report_has_all_sections'] is True
    assert amendment['capture_count']==20==sum(len(row['screenshots']) for row in browser['results'])
    assert amendment['capture_file_hashes_verified'] is True
    expected_captures=[{'path':str(Path(browser_record['path']).parent/shot['file']),'sha256':shot['sha256']} for row in browser['results'] for shot in row['screenshots']]
    assert amendment['screenshots']==expected_captures
    for capture in amendment['screenshots']:
        assert sha((ROOT/capture['path']).read_bytes())==capture['sha256']
    for field in ['clinical_approval','every_structure_approved','fine_3D_tissue_layers_approved','patient_registration_verified','production_or_deployment_verification']:
        assert browser[field] is False
