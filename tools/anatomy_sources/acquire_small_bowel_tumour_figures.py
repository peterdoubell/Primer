#!/usr/bin/env python3
"""Preserve complete CT-source tumour figures, native RGB samples/ICC profiles and original repository JPEGs."""
import argparse,hashlib,io,json,urllib.parse,xml.etree.ElementTree as ET,zlib
from pathlib import Path

# Original PDF page, Poppler image index and object identity. Figure 12 is two
# adjoining native rows, not a new panel arrangement. Repeated PDF placements
# of the same artwork are not additional studies.
SELECTION={2:(9,[(1,124)]),3:(9,[(2,125)]),4:(10,[(5,181)]),5:(10,[(6,182)]),
 6:(11,[(9,239)]),7:(11,[(10,240)]),9:(12,[(18,326)]),10:(12,[(19,327)]),
 11:(13,[(22,383)]),12:(14,[(23,414),(24,415)]),14:(15,[(31,480)]),
 15:(16,[(32,509)]),16:(17,[(33,538)]),18:(18,[(37,595)]),19:(19,[]),20:(19,[])}
PANELS={2:dict.fromkeys('ABCD','CT'),3:dict.fromkeys('AB','CT'),4:dict.fromkeys('AB','CT'),5:dict.fromkeys('ABCD','CT'),
 6:dict.fromkeys('AB','CT'),7:dict.fromkeys('AB','CT'),9:dict.fromkeys('ABC','CT'),10:dict.fromkeys('AB','CT'),11:dict.fromkeys('ABC','CT'),
 12:{**dict.fromkeys('ABC','CT'),'D':'Clinical photograph'},14:{'A':'CT','B':'CT','C':'Clinical photograph'},
 15:{'A':'CT','B':'CT',**dict.fromkeys('CDEF','MRI')},16:dict.fromkeys('ABC','CT'),18:dict.fromkeys('AB','CT'),
 19:{'A':'CT','B':'CT',**dict.fromkeys('CDEF','MRI')},20:{'A':'CT','B':'CT','C':'PET-CT'}}

def sha(raw):return hashlib.sha256(raw).hexdigest()

def placements(reader,page_number):
    from pypdf.generic import ContentStream
    out=[]
    def mul(a,b):return [a[0]*b[0]+a[1]*b[2],a[0]*b[1]+a[1]*b[3],a[2]*b[0]+a[3]*b[2],a[2]*b[1]+a[3]*b[3],a[4]*b[0]+a[5]*b[2]+b[4],a[4]*b[1]+a[5]*b[3]+b[5]]
    def walk(stream,resources,base,depth=0):
        if depth>10:raise ValueError('Unreviewed nested source form')
        matrix=base[:];stack=[]
        for operands,op in ContentStream(stream,reader).operations:
            if op==b'q':stack.append(matrix[:])
            elif op==b'Q':matrix=stack.pop()
            elif op==b'cm':matrix=mul([float(v) for v in operands],matrix)
            elif op==b'Do':
                obj=resources['/XObject'][operands[0]].get_object()
                if str(obj.get('/Subtype'))=='/Image':out.append({'pdf_object_id':obj.indirect_reference.idnum,'matrix_points':matrix[:]})
                elif str(obj.get('/Subtype'))=='/Form':walk(obj,obj.get('/Resources',resources),mul([float(v) for v in obj.get('/Matrix',[1,0,0,1,0,0])],matrix),depth+1)
    page=reader.pages[page_number-1];walk(page.get_contents(),page['/Resources'],[1,0,0,1,0,0]);return out

def acquire(root,output):
    from PIL import Image
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
    from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
    pmc='PMC12071709';meta_path=root/(pmc+'.1.json');meta=json.loads(meta_path.read_text());http=lambda u:u.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
    xml=download_verified(http(meta['xml_url']),root/(pmc+'.1.xml'));pdf_path=root/(pmc+'.1.pdf');pdf=download_verified(http(meta['pdf_url']),pdf_path);tree=ET.fromstring(xml)
    if meta['pmcid']!=pmc or meta['is_retracted'] is not False or tree.findtext('.//article-id[@pub-id-type="doi"]')!=meta['doi']:raise ValueError('Article identity differs')
    permissions=tree.find('.//article-meta/permissions');name,url=exact_license(permissions)
    if name!='CC BY 4.0':raise ValueError('Original grant differs')
    article={'pmcid':pmc,'doi':meta['doi'],'title':meta['title'],'source_article_url':'https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/',
        'metadata_sha256':sha(meta_path.read_bytes()),'xml_sha256':sha(xml),'pdf_sha256':sha(pdf),'pdf_url':http(meta['pdf_url']),
        'publisher_xml_pdf_md5_verified':True,'license':name,'license_url':url,'permissions_xml':ET.tostring(permissions,encoding='unicode'),
        'copyright':permissions.findtext('copyright-statement'),'authors':[' '.join([n.findtext('given-names',''),n.findtext('surname','')]) for n in tree.findall('.//article-meta/contrib-group/contrib[@contrib-type="author"]/name')]}
    reader=PdfReader(pdf_path);rows=[]
    for number,(page,components) in SELECTION.items():
        figure=tree.find('.//fig[@id="healthcare-13-01071-f'+str(number).zfill(3)+'"]');caption=' '.join(figure.find('caption').itertext())
        if figure.find('attrib') is not None or figure.find('permissions') is not None or any(x in caption.lower() for x in ['adapted','reproduced','reprinted','courtesy','provided by']):raise ValueError('Separate source credit requires review')
        filename=figure.find('graphic').get('{http://www.w3.org/1999/xlink}href');links=[u for u in meta['media_urls'] if urllib.parse.urlparse(u).path.endswith('/'+filename)]
        if len(links)!=1:raise ValueError('Original repository figure ambiguous')
        media=download_verified(http(links[0]),root/filename)
        with Image.open(io.BytesIO(media)) as im:repository_dimensions=list(im.size)
        native=[];proof=[];profiles=[];location=placements(reader,page)
        for index,oid in components:
            obj=reader.get_object(IndirectObject(oid,0,reader));places=[p for p in location if p['pdf_object_id']==oid]
            if not places or obj['/BitsPerComponent']!=8 or obj.get('/Decode') not in (None,[0,1,0,1,0,1]) or obj.get('/SMask') is not None:raise ValueError('Original image placement/sample interpretation differs')
            space=obj['/ColorSpace'];profile=space[1].get_object()
            if str(space[0])!='/ICCBased' or profile['/N']!=3 or str(profile.get('/Alternate'))!='/DeviceRGB':raise ValueError('Unreviewed source ICC interpretation')
            icc=profile.get_data();profiles.append(icc);width,height=obj['/Width'],obj['/Height'];encoded=obj._data
            if str(obj['/Filter'])=='/FlateDecode' and obj.get('/DecodeParms') is None:
                samples=zlib.decompress(encoded)
                if samples!=obj.get_data():raise ValueError('Independent zlib/PDF sample readback differs')
                method='original_pdf_flate_rgb_samples_exact'
            elif str(obj['/Filter'])=='/DCTDecode':
                extracted=(root/f'tumour-pdf-{index:03d}.jpg').read_bytes()
                if extracted!=encoded:raise ValueError('Independent encoded JPEG readback differs')
                with Image.open(io.BytesIO(extracted)) as im:
                    im.load()
                    if im.mode!='RGB' or im.size!=(width,height):raise ValueError('Original JPEG sample interpretation differs')
                    samples=im.tobytes()
                method='original_pdf_dct_stream_byte_verified_png_rgb_samples_exact'
            else:raise ValueError('Unreviewed original PDF filter/predictor')
            if len(samples)!=width*height*3:raise ValueError('Original native RGB sample length differs')
            native.append(Image.frombytes('RGB',(width,height),samples));proof.append({'pdf_image_index':index,'pdf_object_id':oid,'width':width,'height':height,
                'encoded_stream_sha256':sha(encoded),'native_rgb_sample_sha256':sha(samples),'icc_profile_sha256':sha(icc),'acquisition':method,'original_pdf_placements':places})
        if components:
            if len(set(profiles))!=1 or len({im.width for im in native})!=1:raise ValueError('Source rows have incompatible interpretation')
            if len(native)>1:
                a,b=(p['original_pdf_placements'][0]['matrix_points'] for p in proof)
                if any(abs(m[1])+abs(m[2])>1e-8 for m in [a,b]) or abs(a[4]-b[4])>1e-8 or abs(a[0]-b[0])>1e-8 or abs(a[5]-(b[5]+b[3]))>1e-6:raise ValueError('Original rows are not aligned/adjoining')
            image=Image.new('RGB',(native[0].width,sum(im.height for im in native)));offset=0
            for im in native:image.paste(im,(0,offset));offset+=im.height
            path=root/('complete-tumour-fig'+str(number)+'.png');image.save(path,icc_profile=profiles[0]);raw=path.read_bytes()
            with Image.open(path) as check:
                check.load()
                if check.tobytes()!=image.tobytes() or check.info.get('icc_profile')!=profiles[0]:raise ValueError('Native RGB/ICC preservation differs')
            method='lossless_png_original_pdf_rgb_and_icc_preserved';pixels=image.tobytes();dimensions=list(image.size)
        else:
            path=root/filename;raw=media
            with Image.open(path) as image:image.load();pixels=image.tobytes();dimensions=list(image.size)
            method='original_repository_encoded_jpeg_byte_identical'
        rows.append({'pmcid':pmc,'figure_number':number,'source_figure_id':figure.get('id'),'source_caption':caption,'source_panel_types':PANELS[number],
            'source_modality':'CT','source_media_url':http(links[0]),'publisher_media_md5_verified':True,'repository_media_sha256':sha(media),'repository_dimensions':repository_dimensions,
            'pdf_page':page,'pdf_object_id':components[0][1] if components else None,'pdf_components':proof,'extracted_file':path.name,'sha256':sha(raw),'width':dimensions[0],'height':dimensions[1],
            'pixel_mode':'RGB','decoded_pixel_sha256':sha(pixels),'acquisition':method,'original_encoded_stream_or_decoded_pixel_readback_verified':True,
            'source_pixels_changed':False,'clinical_approval':False,'display_color_calibration_verified':False,'native_acquired_master_verified':False})
        print('Verified complete figure',number,dimensions,'components',len(components),flush=True)
    holds=[{'pmcid':'PMC9935952','reason':'Source article has a noncommercial grant; not approved for commercial image redistribution.','runtime_promoted':False}]
    output.mkdir(exist_ok=True,parents=True);(output/'original-source-review.json').write_text(json.dumps({'articles':[article],'figures':rows,'rights_holds':holds,'clinical_approval':False,'runtime_promoted':False},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();acquire(a.source_root,a.output)
