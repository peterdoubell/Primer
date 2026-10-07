#!/usr/bin/env python3
"""Acquire complete licensed original figure masters; retain modality and branch-caption conflicts."""
import argparse,hashlib,io,json,sys,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from pypdf import PdfReader
from PIL import Image,ImageChops,ImageStat,ImageCms
from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
SELECTION=['Fig1','Fig6','Fig12','Fig13','Fig19','Fig20','Fig21','Fig22','Fig28']
def sha(raw):return hashlib.sha256(raw).hexdigest()
def review(source,out,ident='PMC6420596',selection=None):
    selection=SELECTION if selection is None else selection;m=json.loads((source/(ident+'.1.json')).read_text());xml=(source/(ident+'.1.xml')).read_bytes();pdf=source/ident/(ident+'.1.pdf')
    if hashlib.md5(xml).hexdigest()!=m['xml_url'].split('md5=')[1] or hashlib.md5(pdf.read_bytes()).hexdigest()!=m['pdf_url'].split('md5=')[1] or m['is_retracted'] is not False:raise ValueError('Publisher original identity differs')
    tree=E.fromstring(xml);grant,url=exact_license(tree.find('.//article-meta/permissions'));reader=PdfReader(pdf);candidates={};masters=source/ident/'original-PDF-masters';masters.mkdir(exist_ok=True)
    for page_number,page in enumerate(reader.pages,1):
        for ref in page['/Resources'].get('/XObject',{}).values():
            obj=ref.get_object()
            if obj.get('/Subtype')!='/Image' or ref.idnum in candidates:continue
            colour=obj['/ColorSpace'];profile=None
            if colour=='/DeviceGray':mode='1' if obj['/BitsPerComponent']==1 else 'L'
            elif colour=='/DeviceRGB':mode='RGB'
            elif isinstance(colour,list) and colour[0]=='/ICCBased':
                icc=colour[1].get_object();profile=icc.get_data()
                if icc['/N']!=3:raise ValueError('Unsupported original ICC channels')
                mode='RGB'
            else:raise ValueError('Original colour interpretation requires review')
            if obj.get('/Decode') is not None:raise ValueError('Original decode transform requires review')
            if str(obj['/Filter'])=='/DCTDecode':image=Image.open(io.BytesIO(obj._data));image.load();pixels=image.tobytes()
            else:pixels=obj.get_data();image=Image.frombytes(mode,(obj['/Width'],obj['/Height']),pixels)
            if image.mode!=mode or image.size!=(obj['/Width'],obj['/Height']):raise ValueError('Original decoded samples/mode differ')
            path=masters/f'object{ref.idnum}.png';image.save(path,**({'icc_profile':profile} if profile else {}))
            with Image.open(path) as im:
                if im.tobytes()!=pixels or (profile is not None and im.info.get('icc_profile')!=profile):raise ValueError('Original sample/profile writeback differs')
            candidates[ref.idnum]={'page':page_number,'image':image,'path':path,'sha256':sha(path.read_bytes()),'decoded_pixel_sha256':sha(pixels),'profile_sha256':sha(profile) if profile else None,'profile_name':ImageCms.getProfileName(ImageCms.ImageCmsProfile(io.BytesIO(profile))).strip() if profile else None,'mode':mode}
    out.mkdir(parents=True,exist_ok=True);rows=[]
    for fid in selection:
        fig=tree.find('.//fig[@id="'+fid+'"]')
        if fig.find('attrib') is not None or fig.find('permissions') is not None:raise ValueError('Separate figure grant requires review')
        filename=fig.find('.//graphic').get('{http://www.w3.org/1999/xlink}href');reference=Image.open(source/ident/filename).convert('RGB').resize((64,32));scores=[]
        link=next(u for u in m['media_urls'] if '/'+filename+'?' in u)
        if hashlib.md5((source/ident/filename).read_bytes()).hexdigest()!=link.split('md5=')[1]:raise ValueError('Original numbered figure checksum differs')
        for key,c in candidates.items():scores.append((sum(ImageStat.Stat(ImageChops.difference(reference,c['image'].convert('RGB').resize((64,32)))).rms)/3,key))
        scores.sort();rms,key=scores[0];c=candidates[key]
        if rms>5:raise ValueError(f'{fid}: numbered figure/PDF binding needs review (RMS {rms})')
        caption=' '.join(fig.find('caption').itertext());rows.append({'figure_id':fid,'figure_number':int(fid.removeprefix('Fig')),'source_caption_full':caption,'original_HTML_filename':filename,'original_HTML_sha256':sha((source/ident/filename).read_bytes()),'source_PDF_object':key,'source_PDF_page':c['page'],'source_master_filename':c['path'].name,'width':c['image'].width,'height':c['image'].height,'source_master_sha256':c['sha256'],'decoded_pixel_sha256':c['decoded_pixel_sha256'],'pixel_mode':c['mode'],'source_ICC_sha256':c['profile_sha256'],'source_ICC_name':c['profile_name'],'numbered_HTML_PDF_thumbnail_RGB_RMS':rms,'original_decoded_samples_and_ICC_preserved':True,'source_pixels_resampled_or_enhanced':False,'source_caption_mandibular_V2_discrepancy':ident=='PMC6420596' and fid=='Fig21','clinical_approval':False})
    report={'pmcid':ident,'doi':m['doi'],'source_article_url':'https://pmc.ncbi.nlm.nih.gov/articles/'+ident+'/','original_article_grant':grant,'license_url':url,'permissions_XML':E.tostring(tree.find('.//article-meta/permissions'),encoding='unicode'),'metadata_sha256':sha((source/(ident+'.1.json')).read_bytes()),'original_XML_sha256':sha(xml),'original_PDF_sha256':sha(pdf.read_bytes()),'publisher_original_MD5_checks_passed':True,'figures':rows,'original_anatomical_or_case_approval_granted':False,'runtime_promoted':False,'structure_coverage_granted':False};(out/'original-source-review.json').write_text(json.dumps(report,indent=2)+'\n');print([(r['figure_id'],r['source_PDF_object'],round(r['numbered_HTML_PDF_thumbnail_RGB_RMS'],3)) for r in rows])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();review(a.source_root,a.proof_dir)
