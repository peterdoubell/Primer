#!/usr/bin/env python3
"""Use original embedded PDF figure masters; verify palette expansion or unchanged JPEG streams."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2]
OBJECTS=[613,11,13,15,19,21,23,27,29,31,35,37,39,45,47,49,43]
IMAGE_INDICES=[17,18,19,20,21,22,23,24,25,26,27,28,29,31,32,33,30]
PREFIX='open-orbit-mri-pmc6095049-fig'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def upgrade(source):
    meta=json.loads((source/'PMC6095049.1.json').read_text());pdf=source/'PMC6095049.1.pdf'
    if hashlib.md5(pdf.read_bytes()).hexdigest()!=meta['pdf_url'].split('md5=')[1]:raise ValueError('Original PDF differs')
    reader=PdfReader(pdf);proof_path=ROOT/'docs/orbit-mri-published-source-review/original-source-review.json';proof=json.loads(proof_path.read_text());facts={r['figure_number']:r for r in proof['figures']};rows=[]
    registry_path=ROOT/'data/radiology/radiology-open-images.json';registry=json.loads(registry_path.read_text())
    evidence_path=ROOT/'data/radiology/radiology-asset-evidence.json';evidence=json.loads(evidence_path.read_text())
    for n,object_id in enumerate(OBJECTS,1):
        obj=reader.get_object(object_id);is_jpeg=str(obj['/Filter'])=='/DCTDecode';extension='.jpg' if is_jpeg else '.png';master=source/'pdf-original-images'/('image-'+f'{IMAGE_INDICES[n-1]:03d}'+extension);raw=master.read_bytes()
        with Image.open(master) as image:
            image.load();width,height=image.size;pixels=image.convert('RGB').tobytes()
        if is_jpeg:
            if raw!=obj._data or obj['/ColorSpace']!='/DeviceRGB' or obj.get('/Decode') is not None:raise ValueError('JPEG stream interpretation differs')
        else:
            color=obj['/ColorSpace']
            if list(color[:2])!=['/Indexed','/DeviceRGB'] or obj['/BitsPerComponent']!=8 or obj.get('/Decode') not in [None,[0,255]]:raise ValueError('Indexed source interpretation differs')
            palette=color[3].get_object().get_data();samples=obj.get_data();expanded=b''.join(palette[v*3:v*3+3] for v in samples)
            if pixels!=expanded:raise ValueError('Lossless original PDF palette samples differ')
        with Image.open(source/f'jbsr-102-1-1308-g{n}.jpg') as reference, Image.open(master) as full:
            rms=sum(ImageStat.Stat(ImageChops.difference(reference.convert('RGB').resize((64,32)),full.convert('RGB').resize((64,32)))).rms)/3
        if rms>5:raise ValueError('Original PDF object does not match the numbered HTML figure')
        if (width,height)!=(obj['/Width'],obj['/Height']):raise ValueError('Original master dimensions differ')
        row=next(r for r in registry['ra.ct-mri-eye'] if r['id']==PREFIX+str(n));old_path=ROOT/'web'/row['src'].removeprefix('/app/');new_path=old_path.with_suffix(extension);new_path.write_bytes(raw)
        if new_path!=old_path:old_path.unlink()
        row.update(src='/app/'+str(new_path.relative_to(ROOT/'web')),sha256=sha(raw),width=width,height=height,asset_source_url=meta['pdf_url'].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/'))
        asset=next(a for a in evidence['assets'] if a['id']==row['id']);asset.update(local_path=str(new_path.relative_to(ROOT)),sha256=sha(raw));asset['source']['asset_url']=row['asset_source_url'];asset['visual_review']['sha256']=sha(raw)
        asset['pixel_provenance'].update(decoded_pixel_sha256=sha(pixels),source_pixels_changed=False,highest_resolution_acquired_master_verified=True,master_origin='Original publisher PDF image object; unchanged JPEG stream or exact lossless indexed-RGB expansion, no resampling')
        facts[n].setdefault('HTML_reference_sha256',facts[n]['sha256']);facts[n].setdefault('HTML_reference_source_media_url',facts[n]['source_media_url']);facts[n]['source_media_url']=row['asset_source_url'];facts[n].update(sha256=sha(raw),decoded_pixel_sha256=sha(pixels),width=width,height=height,pixel_mode='RGB',source_master_PDF_object=object_id,original_PDF_samples_verified=True)
        rows.append({'figure_number':n,'PDF_object_id':object_id,'master_width':width,'master_height':height,'sha256':sha(raw),'decoded_RGB_sha256':sha(pixels),'source_stream_or_exact_palette_samples_verified':True,'resampling_or_pixel_enhancement':False,'HTML_PDF_numbered_figure_binding_thumbnail_RGB_RMS':rms})
    proof.update(original_PDF_sha256=sha(pdf.read_bytes()),original_PDF_publisher_MD5_verified=True,figures=list(facts.values()))
    proof_path.write_text(json.dumps(proof,indent=2)+'\n')
    for a in evidence['assets']:
        if a['id'].startswith(PREFIX):a['source']['license']['evidence_sha256']=sha(proof_path.read_bytes())
    registry_path.write_text(json.dumps(registry,indent=2,ensure_ascii=False)+'\n');evidence_path.write_text(json.dumps(evidence,indent=2)+'\n')
    (proof_path.parent/'original-PDF-master-review.json').write_text(json.dumps({'PDF_sha256':sha(pdf.read_bytes()),'figures':rows,'anatomical_approval':False,'structure_coverage_granted':False},indent=2)+'\n');print('17 original PDF masters preserved; all encoded/palette samples independently verified')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);upgrade(p.parse_args().source_root)
