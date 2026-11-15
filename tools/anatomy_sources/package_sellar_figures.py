#!/usr/bin/env python3
"""Preserve whole licensed sellar MRI/CT figures with their actual case/sequence roles."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
INV = 'ra.mri-sella'
PREFIX = 'open-sella-'
DATE = '2026-10-09'
SELECTION = {
    'PMC10366012': {3:(7,118,2),4:(8,145,3),5:(9,160,4),6:(10,181,5),7:(12,225,6),8:(13,237,7),9:(14,247,8)},
    'PMC10366287': {1:(5,56,0),2:(6,73,1),3:(7,90,2),4:(8,103,3),5:(9,117,4),6:(10,140,5),7:(12,179,6),8:(13,194,7),9:(14,207,8),10:(16,262,9),11:(17,275,10),12:(18,284,11),13:(19,291,12)},
}
PANELS = {
    'PMC10366012': {3:['full_figure'],4:list('ab'),5:list('abcd'),6:list('ab'),7:list('abcdef'),8:list('abcde'),9:list('abc')},
    'PMC10366287': {1:list('abcde'),2:list('abcd'),3:list('abcd'),4:list('abcdef'),5:list('abcd'),6:list('abcde'),7:list('abcd'),8:list('abcd'),9:list('abcde'),10:list('abc'),11:list('abcd'),12:list('abcd'),13:list('abcde')},
}
CT = {'PMC10366012': {7:['a']}, 'PMC10366287': {1:['e'],2:['d'],3:['d'],4:['f'],5:['a'],6:['a'],13:['a']}}
NAMES = {
    'PMC10366012': {3:'Small source lesion on a 90-second dynamic MRI still',4:'Suprasellar extension and source posterior-lobe interpretation',5:'Fluid levels, chiasm compression and intermediate cavernous relationship',6:'Source T2/contrast sellar lesion',7:'Sellar, cavernous, sphenoid and clival extension',8:'Source haemorrhage/necrosis example and sphenoid mucosa',9:'Separate baseline and two-year treatment comparison'},
    'PMC10366287': {1:'Paediatric solid/cystic suprasellar mass, gland, chiasm and CT calcification',2:'Third-ventricular/stalk interface',3:'Suprasellar lesion, vessels and ventricular enlargement',4:'Stalk/optic-chiasm mass and separate source biopsy context',5:'Tuberculum-sellae mass, dura and optic-nerve compression',6:'Clival mass, bone fragments and displaced gland',7:'Thickened stalk and other acquired brain sites',8:'Source cyst-wall/diffusion example',9:'Gland/stalk/dural changes and three-month comparison',10:'Paediatric gland enlargement and ten-year treatment comparison',11:'Rathke-cleft source cyst, nodule and compressed gland',12:'Source sellar cyst and chiasm compression',13:'Partially thrombosed vascular mimic and MRA display'},
}
LIMITS = ('Complete selected published figure, not a native MRI/CT examination or registered source volume. '
          'Actual source sequence, phase, age, side and comparison context remain separate for every case. '
          'Source diagnostic, operative, tissue, hormonal and outcome statements are publication context, not a new diagnosis. '
          'Displayed signal and a flow void do not independently establish tissue identity, secretion, visual function, vascular patency or microscopic invasion. '
          'No independent calibrated distance/ADC measurement, complete tiny neural/vascular/dural boundary, source 3D model or full reporting-anatomy approval is supplied.')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def context_for(pmc, number):
    panels = PANELS[pmc][number]
    ct = CT[pmc].get(number, [])
    child = (pmc,number) in {('PMC10366012',3),('PMC10366287',1),('PMC10366287',10)}
    return {'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'child' if child else 'adult'},
        'extent':'local','depicted_state':'source_sellar_lesion_example',
        'selected_panels':[p for p in panels if p not in ct], 'panel_types':{p:'CT' if p in ct else 'MRI' for p in panels},
        'source_case_groups':{pmc + '_figure' + str(number):panels},
        'different_figures_assumed_same_patient':False, 'source_panels_independently_registered':False,
        'native_acquisition_arrays_included':False, 'independent_anatomical_validation_verified':False,
        'hormone_or_visual_function_inferred_from_images':False, 'biological_3d_model_created_from_artwork':False}


def package(source):
    from PIL import Image
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    from primer.radiology_catalog import _validate_source_panel_roles
    from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
    from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
    from tools.check_static_raster_inventory import inventory
    output = ROOT / 'docs/sellar-published-source-review'
    output.mkdir(parents=True, exist_ok=True)
    visual = json.loads((source / 'visual-review.json').read_text())
    if visual.get('all_twenty_complete_masters_and_pdf_bindings_inspected') is not True:
        raise ValueError('All original figure/page bindings require visual inspection')
    records, articles, rows, assets = [], [], [], []
    for pmc, selection in SELECTION.items():
        metadata_raw = (source / (pmc + '.1.json')).read_bytes(); meta = json.loads(metadata_raw)
        if meta['pmcid'] != pmc or meta['is_retracted'] is not False or meta['license_code'] != 'CC BY':
            raise ValueError('Original identity/grant/retraction changed')
        http = lambda url:url.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
        xml = download_verified(http(meta['xml_url']), source / (pmc + '.1.xml'))
        pdf = download_verified(http(meta['pdf_url']), source / (pmc + '.1.pdf'))
        tree = ET.fromstring(xml); permissions = tree.find('.//article-meta/permissions')
        if 'https://creativecommons.org/licenses/by/4.0/' not in ET.tostring(permissions,encoding='unicode'):
            raise ValueError('Explicit original CC BY4 grant missing')
        authors = ', '.join(' '.join([n.findtext('given-names',''),n.findtext('surname','')]) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name'))
        reader = PdfReader(io.BytesIO(pdf)); article_url = 'https://link.springer.com/article/' + meta['doi']
        articles.append({'pmcid':pmc,'doi':meta['doi'],'title':meta['title'],'authors':authors,
            'original_XML_sha256':sha(xml),'original_PDF_sha256':sha(pdf),'metadata_sha256':sha(metadata_raw),
            'publisher_XML_PDF_md5_verified':True,'permissions_xml':ET.tostring(permissions,encoding='unicode'),'licence':'CC BY4.0'})
        (output / (pmc + '-metadata.json')).write_bytes(metadata_raw)
        for number,(page,object_id,index) in selection.items():
            fig = tree.find('.//fig[@id="Fig' + str(number) + '"]'); caption = ' '.join(' '.join(fig.find('caption').itertext()).split())
            if fig.find('attrib') is not None or fig.find('permissions') is not None or any(t in caption.lower() for t in ['reproduced','courtesy','reprinted','adapted from']):
                raise ValueError('Separate source credit requires its own clearance')
            name = fig.find('graphic').get('{http://www.w3.org/1999/xlink}href')
            urls = [u for u in meta['media_urls'] if u.split('?')[0].endswith('/' + name)]
            if len(urls) != 1: raise ValueError('Ambiguous original media')
            web_media = download_verified(http(urls[0]), source / name)
            obj = reader.get_object(IndirectObject(object_id,0,reader))
            if (object_id not in {v.idnum for v in reader.pages[page-1]['/Resources']['/XObject'].values()}
                    or str(obj['/Filter']) != '/DCTDecode' or str(obj['/ColorSpace']) != '/DeviceGray'
                    or obj['/BitsPerComponent'] != 8 or obj.get('/Decode') is not None):
                raise ValueError('Unreviewed original figure identity or sample interpretation')
            raw = obj._data
            poppler = source / ('part1' if pmc == 'PMC10366012' else 'part2')
            poppler_path = source / (poppler.name + f'-poppler-{index:03d}.jpg')
            if raw != poppler_path.read_bytes(): raise ValueError('Independent Poppler original DCT stream differs')
            with Image.open(io.BytesIO(raw)) as image:
                image.load(); pixels = image.tobytes(); dimensions = [image.width,image.height]
                if image.mode != 'L' or dimensions != [obj['/Width'],obj['/Height']]:
                    raise ValueError('Original grayscale dimensions differ')
            inspected = next(r for r in visual['figures'] if r['pmcid'] == pmc and r['figure_number'] == number)
            if inspected['sha256'] != sha(raw) or not inspected['all_panels_and_original_page_binding_inspected']:
                raise ValueError('Visually inspected source differs')
            with Image.open(io.BytesIO(web_media)) as small: small_dimensions = list(small.size)
            local = f'web/reference-media/radiology-open/sella-{pmc.lower()}-fig{number}.jpg'; (ROOT/local).write_bytes(raw)
            ident = PREFIX + pmc.lower() + '-fig' + str(number); context = context_for(pmc,number)
            special = ''
            if (pmc,number) == ('PMC10366012',3):
                context['source_dynamic_time_seconds'] = 90
                special = 'Only the source 90-second frame is published here; it is not a complete dynamic sequence or independently measured enhancement curve. '
            if (pmc,number) == ('PMC10366012',5):
                context['source_caption_correction'] = '10.1007/s11604-023-01414-1'
                special = 'Corrected Figure 5b describes anterior T1 hyperintensity and posterior mild hypointensity. Intermediate cavernous protrusion in this source case did not have invasion at surgery; the grade is not microscopic proof. '
            if (pmc,number) in {('PMC10366012',9),('PMC10366287',9),('PMC10366287',10)}:
                months = {('PMC10366012',9):24,('PMC10366287',9):3,('PMC10366287',10):120}[(pmc,number)]
                context['source_followup_months'] = months; context['independent_timepoint_registration_verified'] = False
                special = 'Baseline and source-reported treatment follow-up views are separate timepoints, not independently registered geometry or a simulated response. '
            if (pmc,number) == ('PMC10366287',10):
                context['population']['life_stage'] = 'not_reported'
                context['panel_population_context'] = {'a':'Source 10-year-old at baseline','b':'Source 10-year-old at baseline',
                    'c':'Source 10-year follow-up; attained age not separately stated in caption'}
                special += 'Panels a/b show the 10-year-old at baseline; c is the ten-year follow-up and must not be treated as a same-age normal reference. '
            if (pmc,number) == ('PMC10366012',6):
                context['source_text_discrepancy'] = 'Caption uses transiliac sinus approach; operative wording not independently verified or adopted as clinical instruction.'
                special += 'The original caption says transiliac sinus approach; this unresolved wording is not adopted as procedural advice. '
            if (pmc,number) == ('PMC10366287',13):
                context['panel_processing'] = {'e':'published MRA display, not a native vessel model or independent flow measurement'}
                special = 'Panel e is a source MRA display; the partially thrombosed vascular mimic cannot be excluded by a simple solid/cystic or flow-void rule. '
            short = 'Original source Figure ' + str(number) + ': ' + NAMES[pmc][number] + '. ' + special
            attribution = authors + '. ' + meta['title'] + '. DOI ' + meta['doi'] + '. Figure ' + str(number) + '. CC BY 4.0. Complete original PDF JPEG stream retained without crop, resize, enhancement or relabelling. No endorsement implied.'
            row = {'id':ident,'kind':'clinical-image','modality':'MRI','figure_number':number,
                'src':'/app/' + local.removeprefix('web/'),'sha256':sha(raw),'width':dimensions[0],'height':dimensions[1],
                'source_url':article_url,'figure_url':article_url + '/figures/' + str(number),'asset_source_url':http(meta['pdf_url']),
                'clinical_panels':context['selected_panels'],'source_context':context,'image_state':context['depicted_state'],
                'caption':short,'alt':short,'source_caption_full':caption,'limits':special + LIMITS,
                'structures_visible':['Source-local ' + NAMES[pmc][number].lower() + '; complete interfaces unapproved'],
                'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','attribution':attribution,
                'rights_reviewed_on':DATE,'rights_review':'Original grant and each complete caption reviewed; separate-credit Figures1/2/10 of Part1 withheld. Publisher checksums and independent original PDF DCT stream readback verified.'}
            if PANELS[pmc][number] == ['full_figure']:
                row['panel_identifier_scheme'] = 'descriptive_source_positions'; context['panel_identifier_scheme'] = 'descriptive_source_positions'
            if CT[pmc].get(number):
                row['ancillary_panels'] = [{'kind':'CT','panels':CT[pmc][number],
                    'structures_visible':['Original source CT bone/material/context observations in the named panels'],
                    'limits':'Separate actual CT views; not MRI signal, independently calibrated native CT data, registered 3D or proof of every cortical boundary.'}]
            _validate_source_panel_roles(row); rows.append(row)
            records.append({'pmcid':pmc,'figure_number':number,'pdf_page':page,'pdf_object_id':object_id,'sha256':sha(raw),
                'decoded_pixel_sha256':sha(pixels),'width':dimensions[0],'height':dimensions[1], 'source_mode':'L',
                'repository_dimensions':small_dimensions,'repository_media_sha256':sha(web_media),'publisher_media_md5_verified':True,
                'original_DCT_stream_independent_Poppler_byte_exact':True,'source_pixels_changed':False,'all_panels_preserved':True})
            assets.append({'id':ident,'kind':'clinical_image','name':NAMES[pmc][number],'local_path':local,'sha256':sha(raw),
                'modality':'MRI','investigation_ids':[INV],'structure_ids':[],'requirement_coverage':{},'source_context':context,
                'source':{'url':article_url,'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],'license':{
                    'name':'CC BY 4.0','url':row['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified',
                    'evidence_path':'docs/sellar-published-source-review/original-source-review.json','attribution':attribution,'reviewed_at':DATE}},
                'pixel_provenance':{'source_pixels_changed':False,'original_encoded_stream_byte_exact':True,'decoded_pixel_sha256':sha(pixels),'source_pdf_object':object_id,'highest_resolution_acquired_master_verified':True,'original_voxel_arrays_available':False},
                'anatomical_review':{'status':'pending','reason':special + LIMITS}})
    correction_meta = json.loads((source/'PMC10366233.1.json').read_text())
    correction_xml = download_verified(correction_meta['xml_url'].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/'), source/'PMC10366233.1.xml')
    (output/'source-correction.xml').write_bytes(correction_xml)
    proof = {'articles':articles,'figures':records,'source_correction_sha256':sha(correction_xml),
        'separate_credit_holds':{'PMC10366012':[1,2,10]},'full_source_PDFs_containing_held_graphics_redistributed':False,
        'clinical_approval':False,'every_sellar_structure_approved':False,'native_3D_model_created':False,'source_tissue_or_voxels_modified':False}
    proof_path = output/'original-source-review.json'; proof_path.write_text(json.dumps(proof,indent=2,ensure_ascii=False)+'\n')
    (output/'visual-review.json').write_text(json.dumps(visual,indent=2)+'\n')
    for asset in assets:asset['source']['license']['evidence_sha256'] = sha(proof_path.read_bytes())
    path = ROOT/'data/radiology/radiology-open-images.json'; data = json.loads(path.read_text())
    data[INV] = [r for r in data.get(INV,[]) if not r['id'].startswith(PREFIX)] + rows
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    (ROOT/'data/radiology/radiology-static-rasters.json').write_text(json.dumps(inventory(),indent=2)+'\n')
    print('20 complete source sellar MRI/CT figures retained with separate cases and no anatomy approval.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--source-root',type=Path,required=True)
    package(parser.parse_args().source_root)
