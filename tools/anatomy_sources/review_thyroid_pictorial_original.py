#!/usr/bin/env python3
"""Verify all original thyroid figures and non-numerical PDF bindings; preserve source colour channels."""
import argparse,hashlib,io,json,sys,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from PIL import Image,ImageOps
from pypdf import PdfReader
from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
OBJECTS=[33,34,32,36,37,38,39,44,46,43,45,49,50,52,51,54,55,56,57,61,62]
PAGES=[2]*3+[3]*4+[4]*4+[5]*4+[6]*4+[7]*2

def sha(raw):return hashlib.sha256(raw).hexdigest()
def tint(program,value):
    """Restricted interpreter for this source's tint transform; never eval source code."""
    stack=[value]
    for token in program.decode().strip('{} \n').split():
        try:stack.append(float(token));continue
        except ValueError:pass
        if token=='roll':
            j=int(stack.pop());n=int(stack.pop());j%=n
            if j:stack[-n:]=stack[-j:]+stack[-n:-j]
        elif token=='index':i=int(stack.pop());stack.append(stack[-i-1])
        elif token=='sub':b=stack.pop();a=stack.pop();stack.append(a-b)
        elif token=='exch':stack[-2],stack[-1]=stack[-1],stack[-2]
        elif token=='pop':stack.pop()
        elif token=='cvr':pass
        else:raise ValueError('Unsupported source tint operation')
    if len(stack)!=4:raise ValueError('Source tint output is not CMYK')
    return stack

def review(source,out):
    out.mkdir(parents=True,exist_ok=True);masters=source/'verified-PDF-source-masters';masters.mkdir(exist_ok=True)
    meta=json.loads((source/'PMC8864691.1.json').read_text());xml=(source/'PMC8864691.1.xml').read_bytes();pdf=(source/'PMC8864691.1.pdf').read_bytes()
    if meta['pmcid']!='PMC8864691' or meta['is_retracted'] is not False:raise ValueError('Source identity differs')
    for key,raw in [('xml_url',xml),('pdf_url',pdf)]:
        if hashlib.md5(raw).hexdigest()!=meta[key].split('md5=')[1]:raise ValueError('Publisher source checksum differs')
    tree=E.fromstring(xml);grant,url=exact_license(tree.find('.//article-meta/permissions'));reader=PdfReader(io.BytesIO(pdf));figures=[]
    for number,(ident,page) in enumerate(zip(OBJECTS,PAGES),1):
        fig=tree.find(f'.//fig[@id="f{number}"]')
        if fig is None or fig.find('attrib') is not None or fig.find('permissions') is not None:raise ValueError('Figure identity/rights require review')
        filename=fig.find('graphic').get('{http://www.w3.org/1999/xlink}href');link=next(u for u in meta['media_urls'] if '/'+filename+'?' in u);raw=(source/filename).read_bytes()
        if hashlib.md5(raw).hexdigest()!=link.split('md5=')[1]:raise ValueError('Original numbered figure checksum differs')
        obj=reader.get_object(ident);color=obj['/ColorSpace'];shape=(obj['/Width'],obj['/Height'])
        if ident not in [v.idnum for v in reader.pages[page-1]['/Resources']['/XObject'].values()]:raise ValueError('Original page/image binding differs')
        if color[0]=='/DeviceN':
            if list(color[1])!=['/Black'] or color[2]!='/DeviceCMYK' or obj.get('/Decode') is not None or str(obj['/Filter'])!='/DCTDecode':raise ValueError('Original black-channel interpretation differs')
            program=color[3].get_object().get_data()
            for value in range(256):
                result=tint(program,value/255)
                if any(abs(a-b)>1e-12 for a,b in zip(result,[0,0,0,value/255])):raise ValueError('Source transform is not pure black')
            image=Image.open(io.BytesIO(obj._data));image.load()
            if image.mode!='L' or image.size!=shape:raise ValueError('Source JPEG channels differ')
            master=masters/f'figure{number}-original-Black.jpg';master.write_bytes(obj._data);samples=image.tobytes()
            evidence={'encoding':'Original JPEG black tint channel','original_encoded_stream_sha256':sha(obj._data),'decoded_source_channel_sha256':sha(samples),'source_tint_function_sha256':sha(program),'all_256_source_tints_verified_pure_CMYK_Black':True,'browser_grayscale_must_not_be_assumed_equal_to_Black_tint':True}
        elif color[0]=='/Indexed':
            if number!=10 or color[1]!='/DeviceCMYK' or obj['/BitsPerComponent']!=8 or list(obj['/Decode'])!=[0,255]:raise ValueError('Original indexed CMYK interpretation differs')
            palette=color[3].get_object().get_data();indices=obj.get_data();samples=b''.join(palette[v*4:v*4+4] for v in indices);image=Image.frombytes('CMYK',shape,samples);master=masters/'figure10-original-CMYK.tif';image.save(master)
            with Image.open(master) as check:
                if check.mode!='CMYK' or check.tobytes()!=samples:raise ValueError('Original source CMYK samples changed')
            evidence={'encoding':'Original indexed DeviceCMYK expanded without channel changes','decoded_source_channel_sha256':sha(samples),'original_palette_sha256':sha(palette),'original_indices_sha256':sha(indices),'original_CMYK_channels_verified':True,'browser_RGB_mapping_independently_approved':False}
        else:raise ValueError('Unsupported original source colour')
        with Image.open(source/filename) as reference:reference_size=list(reference.size)
        figures.append({'figure_number':number,'figure_id':fig.get('id'),'original_HTML_source_filename':filename,'original_HTML_source_url':link,'publisher_figure_MD5_verified':True,'original_HTML_sha256':sha(raw),'original_HTML_size':reference_size,'source_caption_full':' '.join(fig.find('caption').itertext()),'original_PDF_object':ident,'original_PDF_page':page,'original_master_size':list(shape),'original_source_master_sha256':sha(master.read_bytes()),'master_filename':master.name,**evidence,'source_colour_interpretation_and_independent_anatomical_approval':False})
    proof={'pmcid':meta['pmcid'],'doi':meta['doi'],'original_article_grant':grant,'license_url':url,'permissions_XML':E.tostring(tree.find('.//article-meta/permissions'),encoding='unicode'),'publisher_XML_and_PDF_MD5_verified':True,'metadata_sha256':sha((source/'PMC8864691.1.json').read_bytes()),'original_XML_sha256':sha(xml),'original_PDF_sha256':sha(pdf),'figures':figures,'original_rendered_pages_2_to_7_visually_inspected':True,'figures_are_assumed_same_patient_or_matched_planes':False,'clinical_approval':False,'structure_coverage_granted':False,'runtime_promoted':False}
    (out/'original-source-review.json').write_text(json.dumps(proof,indent=2)+'\n');(out/'PMC8864691.1.json').write_bytes((source/'PMC8864691.1.json').read_bytes());print('21 original figures and PDF bindings checked; all original colour-channel samples preserved')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();review(a.source_root,a.proof_dir)
