#!/usr/bin/env python3
"""Preserve corrected CVH5 source identities, native U3D blocks and every published section."""
import argparse
from collections import Counter
import gzip
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import xml.etree.ElementTree as ET


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blocks(raw, start=0, stop=None):
    stop=len(raw) if stop is None else stop
    rows=[];pos=start
    while pos<stop:
        if pos+12>stop:raise ValueError('Truncated block header')
        kind,size,meta=struct.unpack_from('<III',raw,pos)
        data_start=pos+12;data_end=data_start+size
        meta_start=(data_end+3)//4*4;end=(meta_start+meta+3)//4*4
        if end>stop or any(raw[data_end:meta_start]) or any(raw[meta_start+meta:end]):raise ValueError('Block boundary/padding differs')
        rows.append({'offset':pos,'type':hex(kind),'data_start':data_start,'data_end':data_end,
                     'data_bytes':size,'metadata_bytes':meta,'end':end,'sha256':sha(raw[pos:end])})
        pos=end
    if pos!=stop:raise ValueError('Incomplete block accounting')
    return rows


def string(raw,pos,stop):
    if pos+2>stop:raise ValueError('Truncated string')
    n=struct.unpack_from('<H',raw,pos)[0];end=pos+2+n
    if end>stop:raise ValueError('Truncated string content')
    return raw[pos+2:end].decode('utf-8'),end


def inventory(raw):
    top=blocks(raw);chains=[];nodes=[]
    if top[0]['type']!='0x443355':raise ValueError('Not a U3D stream')
    for b in top:
        if b['type']!='0xffffff14':continue
        name,pos=string(raw,b['data_start'],b['data_end'])
        kind,attrs=struct.unpack_from('<II',raw,pos);pos+=8
        if attrs&~3:raise ValueError('Unknown chain attributes')
        if attrs&1:pos+=16
        if attrs&2:pos+=24
        aligned=(pos+3)//4*4
        if any(raw[pos:aligned]):raise ValueError('Chain padding differs')
        count=struct.unpack_from('<I',raw,aligned)[0]
        nested=blocks(raw,aligned+4,b['data_end'])
        if len(nested)!=count:raise ValueError('Modifier count differs')
        chains.append({'name':name,'chain_type':kind,'attributes':attrs,'block_offset':b['offset'],'modifiers':nested})
        for child in nested:
            if child['type']!='0xffffff22':continue
            node,pos=string(raw,child['data_start'],child['data_end'])
            count=struct.unpack_from('<I',raw,pos)[0];pos+=4;parents=[]
            for _ in range(count):
                parent,pos=string(raw,pos,child['data_end'])
                if pos+64>child['data_end']:raise ValueError('Truncated node transform')
                matrix=list(struct.unpack_from('<16f',raw,pos));pos+=64
                parents.append({'name':parent,'matrix_values_in_source_order':matrix,'matrix_bytes_sha256':sha(raw[pos-64:pos])})
            resource,pos=string(raw,pos,child['data_end'])
            if pos+4!=child['data_end']:raise ValueError('Model node fields differ')
            visibility=struct.unpack_from('<I',raw,pos)[0]
            if node!=name:raise ValueError('Node and chain names differ')
            nodes.append({'name':node,'resource_name':resource,'parents':parents,'visibility':visibility,'source_block_sha256':child['sha256']})
    return {'top_level_blocks':top,'block_type_counts':dict(Counter(b['type'] for b in top)),
            'modifier_chains':chains,'model_nodes':nodes,'decoded_geometry':False,
            'extension_mesh_resources':[c['name'] for c in chains if c['chain_type']==1],
            'source_bytes_changed':False,'patient_axis_units_or_registration_verified':False}


def review(root,output):
    from pypdf import PdfReader
    from PIL import Image
    output.mkdir(parents=True,exist_ok=True);(output/'sections').mkdir(exist_ok=True)
    article_raw=(root/'pone.0132226.xml').read_bytes();correction_raw=(root/'pone.0140736.xml').read_bytes()
    article=ET.fromstring(article_raw);correction=ET.fromstring(correction_raw)
    permission=article.find('.//permissions');license=permission.find('license')
    if license.get('{http://www.w3.org/1999/xlink}href')!='http://creativecommons.org/licenses/by/4.0/':raise ValueError('Source grant differs')
    correction_text=' '.join(correction.itertext())
    if 'incorrectly switched' not in correction_text:raise ValueError('Correction not preserved')
    for name,raw in [('source-article.xml',article_raw),('source-correction.xml',correction_raw)]:
        # Full CC-BY primary source, including corrected captions, remains auditable.
        (output/name).write_bytes(raw)
    model_pdf=root/'pone.0132226.s003.pdf';section_pdf=root/'pone.0132226.s004.pdf'
    metadata=json.loads((root/'PMC4549266.1.json').read_text())
    if metadata['pmcid']!='PMC4549266' or metadata['is_retracted'] is not False:raise ValueError('Source identity or retraction status differs')
    metadata_raw=(root/'PMC4549266.1.json').read_bytes()
    (output/'source-metadata.json').write_bytes(metadata_raw)
    for p in [model_pdf,section_pdf]:
        url=next(u for u in metadata['media_urls'] if '/'+p.name+'?' in u)
        if hashlib.md5(p.read_bytes()).hexdigest()!=url.split('md5=')[1]:raise ValueError('Publisher repository checksum differs')
    reader=PdfReader(model_pdf);anns=[a.get_object() for p in reader.pages for a in p.get('/Annots',[]) if a.get_object().get('/Subtype')=='/3D']
    if len(anns)!=1 or anns[0]['/3DD'].get('/Subtype')!='/U3D':raise ValueError('Original embedded model differs')
    stream=anns[0]['/3DD'];raw=stream.get_data();parsed=inventory(raw)
    packed=gzip.compress(raw,mtime=0);(output/'original-model.u3d.gz').write_bytes(packed)
    # Parsing does not execute PDF actions, document JavaScript or 3D scripts.
    parsed.update({'original_pdf_sha256':sha(model_pdf.read_bytes()),'u3d_bytes':len(raw),'u3d_sha256':sha(raw),
                   'retained_file':'original-model.u3d.gz','retained_sha256':sha(packed),
                   'pdf_actions_or_scripts_executed':False,'clinical_approval':False,'runtime_promoted':False})
    (output/'original-model-inventory.json').write_text(json.dumps(parsed,indent=2)+'\n')
    subprocess.run(['pdfimages','-j',str(section_pdf),str(root/'independent-section')],check=True)
    reader=PdfReader(section_pdf);rows=[]
    for page_number,page in enumerate(reader.pages,1):
        images=[(key,obj,obj.get_object()) for key,obj in page['/Resources']['/XObject'].items() if obj.get_object().get('/Subtype')=='/Image']
        if len(images)!=1:raise ValueError('Source page has ambiguous image placement')
        key,ref,obj=images[0];space=obj['/ColorSpace']
        if obj.get('/Filter')!='/DCTDecode' or obj.get('/BitsPerComponent')!=8 or obj.get('/SMask') is not None or obj.get('/Decode') is not None or obj.get('/ImageMask',False) or str(space[0])!='/ICCBased':raise ValueError('Source interpretation differs')
        if (root/f'independent-section-{page_number-1:03d}.jpg').read_bytes()!=obj._data:raise ValueError('Independent JPEG stream readback differs')
        profile=space[1].get_object();icc=profile.get_data()
        if profile.get('/N')!=3 or icc[16:20]!=b'RGB ':raise ValueError('Unreviewed profile')
        with Image.open(io.BytesIO(obj._data)) as native:
            native.load()
            if native.mode!='RGB' or native.size!=(obj['/Width'],obj['/Height']):raise ValueError('Source samples differ')
            samples=native.tobytes();target=output/'sections'/f'section-{page_number:03d}.png';native.save(target,icc_profile=icc)
        with Image.open(target) as saved:
            saved.load()
            if saved.tobytes()!=samples or saved.info.get('icc_profile')!=icc:raise ValueError('Source pixels/profile changed')
        rows.append({'source_page':page_number,'pdf_object_id':ref.idnum,'file':str(target.relative_to(output)),
                     'width':obj['/Width'],'height':obj['/Height'],'sha256':sha(target.read_bytes()),
                     'original_jpeg_stream_sha256':sha(obj._data),'decoded_pixel_sha256':sha(samples),'icc_sha256':sha(icc),
                     'source_samples_or_profile_changed':False,'anatomical_axis_or_spacing_registered':False})
    if len(rows)!=93:raise ValueError('Incomplete source sections')
    report={'source_doi':'10.1371/journal.pone.0132226','correction_doi':'10.1371/journal.pone.0140736',
            'article_xml_sha256':sha(article_raw),'correction_xml_sha256':sha(correction_raw),
            'source_metadata_sha256':sha(metadata_raw),
            'license_name':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
            'attribution':'Wu et al. (2015), 3D Topography of the Young Adult Anal Sphincter Complex Reconstructed from Undeformed Serial Anatomical Sections. PLOS ONE. No endorsement implied.',
            'model_pdf_source_id':'pone.0132226.s003','sections_pdf_source_id':'pone.0132226.s004',
            'original_pdf_publisher_repository_md5_verified':True,'section_pdf_sha256':sha(section_pdf.read_bytes()),
            'model_inventory_sha256':sha((output/'original-model-inventory.json').read_bytes()),'sections':rows,
            'model_node_count':len(parsed['model_nodes']),'source_caption_structure_count':46,
            'source_main_text_structure_count':47,'count_discrepancy_resolved':False,
            'source_setting':'cadaveric','source_specimen':'CVH5','source_sections_are_clinical_MRI':False,
            'source_section_master_resolution_verified':False,'section_model_registration_verified':False,
            'arbitrary_anterior_pubovisceral_puborectal_partition_is_real_boundary':False,
            'positive_tumour_or_nodal_pathology_coverage_granted':False,'source_geometry_decoded':False,
            'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (output/'source-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Preserved',len(rows),'native section sample arrays and',len(parsed['model_nodes']),'original model-node identities.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.source_root,a.output)
