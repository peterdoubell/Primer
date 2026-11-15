#!/usr/bin/env python3
"""Preserve original gallbladder source pixels, including indexed colour and PDF soft masks."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET

SELECTION = {'PMC5359147': {3: (3,25,36),5: (5,27,55),6: (6,30,69),7: (6,28,67),8: (6,29,68),9: (7,31,80)},
             'PMC12181115': {1: (4,3,18),4: (6,8,33),6: (7,10,41)}}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def acquire(root, output):
    from PIL import Image
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    from tools.anatomy_sources.acquire_adrenal_published_figures import download_verified
    from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
    output.mkdir(parents=True, exist_ok=True); articles=[]; figures=[]
    for pmc, selection in SELECTION.items():
        meta_path=root/(pmc+'.1.json'); meta=json.loads(meta_path.read_text())
        http=lambda u:u.replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/')
        xml=download_verified(http(meta['xml_url']),root/(pmc+'.1.xml')); pdf_path=root/(pmc+'.1.pdf')
        pdf=download_verified(http(meta['pdf_url']),pdf_path); tree=ET.fromstring(xml)
        if meta['pmcid']!=pmc or meta['is_retracted'] is not False:
            raise ValueError('Original source identity/retraction differs')
        permissions=tree.find('.//article-meta/permissions'); license_name,license_url=exact_license(permissions)
        if license_name!='CC BY 4.0':raise ValueError('Selected source grant differs')
        articles.append({'pmcid':pmc,'doi':meta['doi'],'title':meta['title'],'source_article_url':'https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/',
            'metadata_sha256':sha(meta_path.read_bytes()),'xml_sha256':sha(xml),'pdf_sha256':sha(pdf),'pdf_url':http(meta['pdf_url']),
            'publisher_xml_pdf_md5_verified':True,'license':license_name,'license_url':license_url,
            'permissions_xml':ET.tostring(permissions,encoding='unicode'),'copyright':permissions.findtext('copyright-statement'),
            'authors':[' '.join([n.findtext('given-names',''),n.findtext('surname','')]) for n in tree.findall('.//article-meta/contrib-group/contrib/name')]})
        reader=PdfReader(pdf_path)
        for number,(page,index,oid) in selection.items():
            figure=tree.find('.//fig[@id="Fig'+str(number)+'"]'); caption=' '.join(figure.find('caption').itertext())
            if figure.find('attrib') is not None or figure.find('permissions') is not None or any(s in caption.lower() for s in ['courtesy','reproduced','reprinted','adapted','provided by','(from:']):
                raise ValueError('Unreviewed separate figure credit')
            filename=figure.find('graphic').get('{http://www.w3.org/1999/xlink}href')
            links=[u for u in meta['media_urls'] if u.split('?')[0].endswith('/'+filename)]
            if len(links)!=1:raise ValueError('Source media absent/ambiguous')
            media=download_verified(http(links[0]),root/filename)
            with Image.open(io.BytesIO(media)) as im:repository_dimensions=list(im.size)
            obj=reader.get_object(IndirectObject(oid,0,reader)); w,h=obj['/Width'],obj['/Height']
            if oid not in {r.idnum for r in reader.pages[page-1]['/Resources']['/XObject'].values()} or obj['/BitsPerComponent']!=8:
                raise ValueError('Original page/sample identity differs')
            jpeg=str(obj['/Filter'])=='/DCTDecode'; prefix='wall-pdf' if pmc=='PMC5359147' else 'acute-pdf'
            extracted=root/(prefix+'-'+f'{index:03d}'+('.jpg' if jpeg else '.png'))
            raw=extracted.read_bytes()
            with Image.open(io.BytesIO(raw)) as im:im.load(); image=im.copy()
            if image.size!=(w,h):raise ValueError('Original image dimensions differ')
            space=obj['/ColorSpace']; source_rgb=None
            if jpeg:
                if raw!=obj._data:raise ValueError('Encoded source JPEG differs from independent extraction')
                method='original_pdf_dct_stream_byte_identical'
            elif str(space[0])=='/Indexed':
                if obj['/Decode']!=[0,255]:raise ValueError('Unreviewed indexed sample decode')
                indices=obj.get_data(); palette=space[3].get_object().get_data()
                if max(indices)>space[2] or len(palette)!=3*(space[2]+1):raise ValueError('Source colour-table bounds differ')
                source_rgb=b''.join(palette[i*3:i*3+3] for i in indices)
                if image.mode!='RGB' or image.tobytes()!=source_rgb:raise ValueError('Indexed PNG pixels differ from original palette decoding')
                method='lossless_png_original_indexed_pdf_pixels_exact'
            else:
                expected='L' if str(space)=='/DeviceGray' else 'RGB'
                if expected=='RGB' and (str(space[0])!='/ICCBased' or space[1].get_object()['/N']!=3):raise ValueError('Unreviewed source colour space')
                if obj.get('/Decode') is not None or image.mode!=expected or image.tobytes()!=obj.get_data():raise ValueError('Original decoded PDF samples differ')
                method='lossless_png_original_pdf_samples_exact'
            soft_mask=None
            if '/SMask' in obj:
                mask=obj['/SMask']
                if str(mask['/Filter'])!='/DCTDecode' or str(mask['/ColorSpace'])!='/DeviceGray':raise ValueError('Unreviewed original mask decode')
                alpha=Image.open(io.BytesIO(mask._data)); alpha.load()
                if alpha.mode!='L' or alpha.size!=(w,h):raise ValueError('Original soft-mask shape differs')
                independent=Image.open(root/(prefix+'-'+f'{index+1:03d}'+'.jpg'));independent.load()
                if mask._data!=(root/(prefix+'-'+f'{index+1:03d}'+'.jpg')).read_bytes() or alpha.tobytes()!=independent.tobytes():raise ValueError('Independent encoded/decoded soft-mask readback differs')
                original_color=image.convert('RGB').tobytes(); image=image.convert('RGB');image.putalpha(alpha)
                soft_mask={'encoded_sha256':sha(mask._data),'decoded_alpha_sha256':sha(alpha.tobytes()),'alpha_range':list(alpha.getextrema()),
                           'original_colour_sha256':sha(original_color),'source_mask_preserved':True,'paper_background_compositing_review_required':True}
                method='lossless_rgba_original_pdf_colour_and_soft_mask_exact'
            target=output/(pmc.lower()+'-fig'+str(number)+('.jpg' if jpeg and soft_mask is None else '.png'))
            if jpeg and soft_mask is None:target.write_bytes(raw)
            else:image.save(target)
            with Image.open(target) as check:
                if check.mode!=image.mode or check.tobytes()!=image.tobytes():raise ValueError('Lossless output changed source samples')
            figures.append({'pmcid':pmc,'figure_number':number,'file':target.name,'source_caption':caption,
                'source_filename':filename,'source_media_url':http(links[0]),'repository_media_sha256':sha(media),'repository_dimensions':repository_dimensions,'publisher_media_md5_verified':True,
                'pdf_page':page,'pdf_image_index':index,'pdf_object_id':oid,'pdf_image_encoded_sha256':sha(obj._data),
                'sha256':sha(target.read_bytes()),'decoded_pixel_sha256':sha(image.tobytes()),'width':w,'height':h,'pixel_mode':image.mode,
                'acquisition':method,'original_colour_and_mask_readback_verified':True,'soft_mask':soft_mask,
                'source_samples_changed':False,'clinical_approval':False,'display_colour_calibration_verified':False})
    roles={('PMC5359147',3):{'a':'Ultrasound','b':'CT'}, ('PMC5359147',5):dict.fromkeys('abcde','Ultrasound'),
           ('PMC5359147',6):dict.fromkeys('ab','Ultrasound'), ('PMC5359147',7):{'whole':'Ultrasound'},
           ('PMC5359147',8):{'whole':'Ultrasound'}, ('PMC5359147',9):dict.fromkeys('ab','Ultrasound'),
           ('PMC12181115',1):{'whole':'Ultrasound'}, ('PMC12181115',4):{'a':'Ultrasound','b':'CT','c':'Radiography'},
           ('PMC12181115',6):{'left':'Ultrasound','middle':'CT','right':'CT'}}
    for row in figures:
        row['source_panel_roles']=roles[(row['pmcid'],row['figure_number'])]
        row['panel_identifier_scheme']=('position_unlettered' if 'left' in row['source_panel_roles'] else
                                        'whole_unlettered' if 'whole' in row['source_panel_roles'] else 'original_letters')
        row['panel_roles_are_source_and_visual_review_claims_not_anatomical_approval']=True
    (output/'original-source-review.json').write_text(json.dumps({'articles':articles,'figures':figures,
        'separately_credited_figure_excluded':{'pmcid':'PMC5359147','figure':4},'clinical_approval':False,'runtime_promoted':False,
        'limits':['Static source images do not establish mobility, compression response, tenderness or complete dynamic contrast/flow behaviour.',
                  'Twinkling Doppler artifact is not wall hypervascularity; CEUS still frames cannot prove every phase of an examination.',
                  'Original tissue colour and separate PDF alpha samples are preserved; consistent source-paper background and display calibration still require review.']},indent=2)+'\n')
    print('Nine complete source figures preserved, including original PDF mask samples.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();acquire(args.source_root,args.output)
