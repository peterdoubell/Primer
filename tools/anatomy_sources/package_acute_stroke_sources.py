"""Package all 13 licensed CTP source figures at their native PDF raster resolution.

No registry writes. Full untouched PDF, original publisher JPEGs and every encoded
PDF figure image stream remain. Split strips are stacked without resampling,
filtering, added annotation or removed pixels, in source top-to-bottom order.
"""
from pathlib import Path
import hashlib
import io
import json
import shutil
import xml.etree.ElementTree as ET
from PIL import Image
import pymupdf
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[2]
INPUT=ROOT.parent.parent/'.research/acute-stroke-source-20261011/source-ctp-2023'
REVIEW=ROOT/'docs/acute-stroke-source-review-20261011'
SOURCE=REVIEW/'source-ctp-2023'
OUT=ROOT/'web/reference-media/radiology-open/acute-stroke'
# Whole native raster or sequential original top/bottom strips, no source pixel scaling.
OBJECTS={1:[95],2:[96,97],3:[129],4:[130,128],5:[161,162],6:[178,179],7:[192],8:[208,209],9:[225,226],10:[243,244],11:[260,261],12:[280],13:[298,299]}
PAGES={1:6,2:6,3:7,4:7,5:8,6:9,7:9,8:10,9:11,10:12,11:13,12:15,13:16}
SUMMARIES={1:'Right MCA-territory CT/CTP and distal ICA occlusion on CTA after cardiac catheterisation.',2:'Right occipital change after TAVI; CT/CTP abnormality with no apparent CTA occlusion in the source.',3:'Basilar tip thrombotic occlusion, CT/CTP and posterior-circulation source presentation after TAVI.',4:'Left basal-ganglia CT/CTP change and inferior MCA trunk occlusion on CTA.',5:'Source follow-up after hemicraniectomy for malignant right MCA infarction; swelling and vascular rarefaction.',6:'Posterior fossa CTP compared with next-day DWI: bilateral cerebellar lesions and source CT/MRI discrepancy.',7:'Right cerebellar CT/CTP change and source-described absent right superior cerebellar artery; contralateral duplicated SCA.',8:'Traumatic brain injury with source cerebral circulatory-arrest context; selected CT/CTP/CTA examples do not establish brain death.',9:'Delayed supply in severe arterial inflow stenosis; example of hypoperfusion without source CT demarcation.',10:'Source CT/CTP after carotid endarterectomy; watershed perfusion restriction and postsurgical carotid thrombotic stenosis.',11:'Source vasospasm after ruptured left MCA aneurysm clipping, selected CTA/CTP findings.',12:'Epilepsy presentation with right posterior hyperperfusion; source seizure stroke-mimic example.',13:'Severe CTP motion artefact and source manual reprocessing; dynamic frames and two map sets retained.'}

def sha(b):return hashlib.sha256(b).hexdigest()

def package():
    SOURCE.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    acquisition=json.loads((INPUT/'acquisition.json').read_text());meta=json.loads((INPUT/'PMC9914845.1.json').read_text())
    for row in acquisition['files']:
        b=(INPUT/row['name']).read_bytes()
        if sha(b)!=row['sha256'] or hashlib.md5(b).hexdigest()!=row['source_md5']:raise ValueError('Pinned source file changed')
    tree=ET.parse(INPUT/'PMC9914845.1.xml');grant=ET.tostring(tree.find('.//article-meta/permissions'),encoding='unicode')
    if 'https://creativecommons.org/licenses/by/4.0/' not in grant:raise ValueError('Unrestricted BY4 source license required')
    if any('permission' in ''.join(f.itertext()).lower() or 'reproduced' in ''.join(f.itertext()).lower() for f in tree.findall('.//fig')):raise ValueError('Figure credit needs separate donor review')
    for n in ['acquisition.json','PMC9914845.1.json','PMC9914845.1.xml']:shutil.copyfile(INPUT/n,SOURCE/n)
    pdf=(INPUT/'PMC9914845.1.pdf').read_bytes();name='ctp-2023-original-publication.pdf';(OUT/name).write_bytes(pdf)
    doc=pymupdf.open(stream=pdf,filetype='pdf');reader=PdfReader(io.BytesIO(pdf));figures=[];images=[];assets=[];total_pixels=0
    authors=[' '.join([n.findtext('given-names',''),n.findtext('surname','')]).strip() for n in tree.findall('.//article-meta/contrib-group/contrib/name')]
    attribution=', '.join(authors)+'. '+meta['title']+'. Diagnostics 2023;13:447. DOI 10.3390/diagnostics13030447. © Authors 2023. CC BY4. Native PDF strips assembled without changing any source pixel; source markings retained.'
    for number,xrefs in OBJECTS.items():
        strips=[];objects=[]
        for xref in xrefs:
            p=pymupdf.Pixmap(doc,xref)
            if p.n!=3:p=pymupdf.Pixmap(pymupdf.csRGB,p)
            im=Image.frombytes('RGB',(p.width,p.height),p.samples);strips.append(im)
            image_obj=reader.get_object(xref);stream=image_obj._data
            object_path=SOURCE/f'fig{number}-object{xref}-original-stream.bin';object_path.write_bytes(stream)
            png_path=SOURCE/f'fig{number}-object{xref}-native.png';im.save(png_path)
            objects.append({'xref':xref,'PDF_page':PAGES[number],'width':im.width,'height':im.height,'source_color_space':str(image_obj.get('/ColorSpace')),'source_filter':str(image_obj.get('/Filter')),'encoded_stream_path':str(object_path.relative_to(ROOT)),'encoded_stream_sha256':sha(stream),'encoded_stream_bytes':len(stream),'native_RGB_channels_sha256':sha(im.tobytes()),'native_display_path':str(png_path.relative_to(ROOT)),'native_display_sha256':sha(png_path.read_bytes())})
        width=strips[0].width
        if any(im.width!=width for im in strips):raise ValueError('Strip widths differ; pixel-preserving assembly must be reviewed')
        assembled=Image.new('RGB',(width,sum(im.height for im in strips)));offset=0
        for im in strips:
            assembled.paste(im,(0,offset))
            if assembled.crop((0,offset,width,offset+im.height)).tobytes()!=im.tobytes():raise ValueError('Original pixels changed during assembly')
            offset+=im.height
        filename=f'ctp-2023-fig{number}-native.png';assembled.save(OUT/filename)
        web_name=f'ctp-2023-fig{number}-original-publisher.jpg';web_original=(INPUT/f'diagnostics-13-00447-g{number:03d}.jpg').read_bytes();(OUT/web_name).write_bytes(web_original)
        f=tree.find(f'.//fig[@id="diagnostics-13-00447-f{number:03d}"]');caption=' '.join(' '.join(f.find('caption').itertext()).split())
        panels=list('ABCDEF') if number<=12 else ['A','B','C','D','E','F','G','H','I','K','L','M'];types={x:('MRI_DWI_next_day' if number==6 and x=='F' else 'CTA' if x=='F' and number<=12 else 'NCCT' if x=='E' and number<=12 else 'CTP_source_map_or_dynamic_frame') for x in panels}
        ident=f'open-acute-stroke-ctp2023-fig{number}';display=(OUT/filename).read_bytes();total_pixels+=assembled.width*assembled.height
        context={'source_patient_only':True,'current_patient_findings':False,'full_acquired_stack_supplied':False,'native_DICOM':False,'segmentation_supplied':False,'patient_3D_supplied':False,'fine_structure_coverage_granted':False,'source_calibration_or_HU_recoverable':False,'panels':types,'unlettered_additional_artwork':(['source time-attenuation curve of arterial, venous and bilateral parenchymal measurements; numeric time series absent'] if number==8 else []),'same_patient_relation':'all panels in the numbered figure source case; separate figures are not co-registered','CT_MRI_temporal_relation':'Fig6 DWI is next day; not registered to the CT' if number==6 else None,'dynamic_phase_interpretation':'Fig13 A/B are different motion timepoints; C/D source reprocessed MIP; map sets are source processing, not recovered numerical maps' if number==13 else 'Published selected static maps; dynamic time series absent'}
        row={'id':ident,'title':'Source CTP review · Figure '+str(number),'src':'/app/reference-media/radiology-open/acute-stroke/'+filename,'width':assembled.width,'height':assembled.height,'sha256':sha(display),'modality':'CT','alt':SUMMARIES[number],'caption':SUMMARIES[number]+' '+('Panel F is next-day DWI; CT and MRI are not registered. ' if number==6 else '')+'Complete native publication artwork; source numerical maps, full stacks and patient meshes are not supplied.','source_url':'https://doi.org/10.3390/diagnostics13030447','asset_source_url':'https://pmc-oa-opendata.s3.amazonaws.com/PMC9914845.1/PMC9914845.1.pdf','license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','attribution':attribution,'original_caption':caption,'source_context':context}
        images.append(row);assets.append({'id':ident,'kind':'clinical_image','name':row['title'],'local_path':str((OUT/filename).relative_to(ROOT)),'sha256':row['sha256'],'investigation_ids':['ra.acute-stroke'],'structure_ids':[],'requirement_coverage':{},'source':{'url':row['source_url'],'license':{'id':'CC-BY-4.0','url':row['license_url'],'commercial_reuse_permitted':True}},'anatomical_review':{'status':'pending','reason':'Complete native publication artwork is source context, not full patient anatomy or fine structure approval.'}})
        figures.append({'number':number,'source_caption':caption,'objects':objects,'whole_native_display':{'path':str((OUT/filename).relative_to(ROOT)),'sha256':sha(display),'width':assembled.width,'height':assembled.height,'decoded_RGB_sha256':sha(assembled.tobytes())},'original_web_JPEG':{'path':str((OUT/web_name).relative_to(ROOT)),'sha256':sha(web_original),'bytes':len(web_original)},'source_pixels_changed':False,'native_pixels_resampled':False,'composition':'single complete original PDF image' if len(xrefs)==1 else 'exact top/bottom native RGB strips; no gap, padding, resampling, crop or new annotation'})
    proposal={'schema_version':1,'reviewed_at':'2026-10-11','investigation_id':'ra.acute-stroke','module_id':'rad.4.stroke','source':{'doi':meta['doi'],'pmcid':meta['pmcid'],'authors':authors,'license':'CC BY 4.0','permissions_XML':grant,'original_PDF':{'path':str((OUT/name).relative_to(ROOT)),'bytes':len(pdf),'sha256':sha(pdf),'pages':len(doc)},'source_file_acquisition':acquisition},'images':images,'assets':assets,'source_figures':figures,'source_figure_objects':sum(len(x) for x in OBJECTS.values()),'complete_numbered_figures':13,'native_display_RGB_pixels':total_pixels,'native_DICOM_or_3D_from_this_publication':False,'clinical_approval':False,'fine_anatomical_approval':False,'runtime_integrated':False}
    (REVIEW/'ctp-integration-proposal.json').write_text(json.dumps(proposal,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'figures':13,'native_objects':proposal['source_figure_objects'],'pixels':total_pixels,'media_files':len(list(OUT.iterdir())),'media_bytes':sum(p.stat().st_size for p in OUT.iterdir())}))
    return proposal
if __name__=='__main__':package()
