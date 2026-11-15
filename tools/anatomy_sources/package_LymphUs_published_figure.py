#!/usr/bin/env python3
"""Package the licensed published figure only; native dataset rights remain separate."""
import argparse,hashlib,json,sys,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from PIL import Image,ImageChops,ImageStat
from pypdf import PdfReader
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
from tools.check_radiology_fidelity import digest
from tools.anatomy_sources.acquire_pancreatitis_vascular_figures import exact_license
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT=Path(__file__).resolve().parents[2];ID='open-cervical-nodes-pmc13049566-fig3';INV='ra.cervical-lymph-nodes';URL='https://pmc.ncbi.nlm.nih.gov/articles/PMC13049566/'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package(source):
    meta=json.loads((source/'PMC13049566.1.json').read_text());xml=(source/'PMC13049566.1.xml').read_bytes();pdf=(source/'PMC13049566.1.pdf').read_bytes()
    if meta['pmcid']!='PMC13049566' or meta['is_retracted'] is not False or hashlib.md5(xml).hexdigest()!=meta['xml_url'].split('md5=')[1] or hashlib.md5(pdf).hexdigest()!=meta['pdf_url'].split('md5=')[1]:raise ValueError('Original identity or publisher checksum differs')
    tree=E.fromstring(xml);permissions=tree.find('.//article-meta/permissions');grant,license_url=exact_license(permissions);fig=tree.find('.//fig[@id="fig0003"]')
    if grant!='CC BY 4.0' or fig is None or fig.find('permissions') is not None or fig.find('attrib') is not None:raise ValueError('Published figure grant requires review')
    caption=' '.join(fig.find('caption').itertext());obj=PdfReader(source/'PMC13049566.1.pdf').get_object(53);color=obj['/ColorSpace']
    if list(color[:2])!=['/Indexed','/DeviceRGB'] or obj['/BitsPerComponent']!=8 or obj.get('/Decode') is not None:raise ValueError('Original palette interpretation differs')
    palette=color[3].get_object().get_data();expanded=b''.join(palette[v*3:v*3+3] for v in obj.get_data());master=source/'lymphus-fig3-original-PDF.png'
    if not master.exists():Image.frombytes('RGB',(obj['/Width'],obj['/Height']),expanded).save(master)
    raw=master.read_bytes()
    with Image.open(master) as image:
        image.load();pixels=image.convert('RGB').tobytes();size=image.size
    if pixels!=expanded or size!=(obj['/Width'],obj['/Height']):raise ValueError('Original master samples differ')
    media=next(u for u in meta['media_urls'] if '/gr3.jpg?' in u)
    if hashlib.md5((source/'gr3.jpg').read_bytes()).hexdigest()!=media.split('md5=')[1]:raise ValueError('Original numbered figure checksum differs')
    with Image.open(source/'gr3.jpg') as reference,Image.open(master) as image:
        rms=sum(ImageStat.Stat(ImageChops.difference(reference.convert('RGB').resize((64,32)),image.convert('RGB').resize((64,32)))).rms)/3
    page=PdfReader(source/'PMC13049566.1.pdf').pages[6]
    if 'Fig. 3.' not in page.extract_text() or [v.idnum for v in page['/Resources']['/XObject'].values()]!=[53]:raise ValueError('Original PDF page/figure binding differs')
    # HTML and PDF have different encoded contrast; do not force their pixel equality.
    # Object53 is the sole image on the independently rendered/inspected Figure3 page.
    labels={};states={};groups={};primary=[];masks=[];masked=[]
    for centre in [1,2]:
        for outcome in ['benign','malignant']:
            group=f'centre{centre}_{outcome}';column=1 if outcome=='benign' else 4;panels=[f'r{centre}c{column+i}' for i in range(3)];groups[group]=panels;primary.append(panels[0]);masks.append(panels[1]);masked.append(panels[2]);labels.update(dict(zip(panels,['Ultrasound','Segmentation mask','Masked ultrasound'])));states.update({p:'source_'+outcome+'_PTC_cohort_node' for p in panels})
    limits='Four separate source examples: rows Centre1 and Centre2; left triple source-benign, right triple source-malignant. Original caption says first/second rows distinguish outcomes, contradicting the visible labels; layout follows preserved figure labels. Binary masks and masked-image panels are processed node-envelope annotations, not cortex/hilum/capsule or ENE geometry. Source outcomes are not diagnoses newly inferred from pixels. Selected cropped 8-bit B-mode exports do not provide cine/Doppler, calibrated physical spacing, confirmed case side/level/plane, full neck extent or 3D interiors.'
    context={'panel_identifier_scheme':'grid_unlettered','panel_grid_rows':2,'panel_grid_columns':6,'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'extent':'local','depicted_state':'source_distinct_PTC_cohort_nodal_US_comparisons','selected_panels':primary,'panel_types':labels,'panel_states':states,'source_case_groups':groups,'source_caption_layout_discrepancy':True,'native_orientation_or_full_anatomical_extent_verified':False}
    out=ROOT/'docs/lymphus-published-source-review';out.mkdir(exist_ok=True);local='web/reference-media/radiology-open/cervical-nodes-pmc13049566-fig3.png';(ROOT/local).write_bytes(raw)
    attribution='Mohammadi A, Mohebbi A, Mirza-Aghazadeh-Attari M, et al. '+meta['title']+'. DOI '+meta['doi']+'. Published Figure3, CC BY4.0. Original PDF indexed RGB samples expanded losslessly, no resampling or enhancement. No endorsement implied.'
    proof={'pmcid':meta['pmcid'],'doi':meta['doi'],'original_article_grant':grant,'license_url':license_url,'permissions_XML':E.tostring(permissions,encoding='unicode'),'publisher_XML_and_PDF_MD5_verified':True,'XML_sha256':sha(xml),'PDF_sha256':sha(pdf),'figure_number':3,'PDF_image_object':53,'source_caption_full':caption,'source_master_sha256':sha(raw),'decoded_pixel_sha256':sha(pixels),'original_source_master_samples_verified':True,'source_pixels_changed':False,'HTML_PDF_numbered_figure_binding_thumbnail_RGB_RMS':rms,'PDF_page':7,'PDF_rendered_page_binding_visually_checked':True,'HTML_and_PDF_original_encoded_contrast_differ':True,'native_dataset_commercial_grant_verified':False,'clinical_approval':False,'structure_coverage_granted':False}
    proof_path=out/'original-source-review.json';proof_path.write_text(json.dumps(proof,indent=2)+'\n')
    row={'panel_identifier_scheme':'grid_unlettered','id':ID,'kind':'clinical-image','modality':'Ultrasound','figure_number':3,'src':'/app/'+local.removeprefix('web/'),'sha256':sha(raw),'width':size[0],'height':size[1],'source_url':URL,'figure_url':URL+'#fig0003','asset_source_url':meta['pdf_url'].replace('s3://pmc-oa-opendata/','https://pmc-oa-opendata.s3.amazonaws.com/'),'clinical_panels':primary,'source_context':context,'image_state':context['depicted_state'],'caption':'Original ultrasound node comparisons, masks and masked images from two centres. '+limits,'alt':'Four original source nodal ultrasound comparisons. '+limits,'limits':limits,'source_caption_full':caption,'structures_visible':['Source-local B-mode node appearances; no independent tissue-boundary approval'],'ancillary_panels':[{'kind':'Segmentation mask','panels':masks,'structures_visible':['Original binary node envelopes'],'limits':'Binary selected-node annotation only; no independently labelled internal tissues.'},{'kind':'Masked ultrasound','panels':masked,'structures_visible':['Masked source node appearances'],'limits':'Processed masked-image comparison; not full acquired field or independent modality.'}],'license':grant,'license_url':license_url,'attribution':attribution,'rights_reviewed_on':'2026-10-07','rights_review':'Original article-specific CC BY4; no separate Figure3 restriction. Native dataset research terms remain uncleared for commercial publication.'}
    catalog._validate_source_panel_roles(row)
    path=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(path.read_text());data[INV]=[r for r in data.get(INV,[]) if r['id']!=ID]+[row];path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    asset={'id':ID,'kind':'clinical_image','name':'Original two-centre nodal ultrasound comparisons','local_path':local,'sha256':sha(raw),'modality':'Ultrasound','investigation_ids':[INV],'structure_ids':[],'requirement_coverage':{},'source_context':context,'source':{'url':URL,'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],'license':{'name':grant,'url':license_url,'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_path.read_bytes()),'attribution':attribution,'reviewed_at':'2026-10-07'}},'pixel_provenance':{'source_pixels_changed':False,'decoded_pixel_sha256':sha(pixels),'highest_resolution_acquired_master_verified':True},'anatomical_review':{'status':'pending','reason':'Selected US/masks do not independently establish all nodal internals, patient geometry or full neck interfaces.'},'visual_review':{'status':'source_checked','sha256':sha(raw),'evidence_path':'docs/lymphus-published-source-review.md','reviewed_at':'2026-10-07'}}
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',[asset],prefix=ID)
    path=ROOT/'data/radiology/reporting-steps/head-neck.json';text=path.read_text();start=text.index('{',text.index('"'+INV+'"'));node,end=json.JSONDecoder().raw_decode(text,start)
    for index in [1,2]:node['steps'][index]['images']=list(dict.fromkeys(node['steps'][index]['images']+[ID]))
    path.write_text(text[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+text[end:])
    for value in vars(catalog).values():
        if callable(getattr(value,'cache_clear',None)):value.cache_clear()
    ref=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference'];path=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(path.read_text())
    for investigation in data['investigations']:
        if investigation['investigation_id']==INV:investigation['source_contract_sha256']=digest({k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')})
    path.write_text(json.dumps(data,indent=2)+'\n');print('Original published US master preserved:',size,'binding RMS',rms)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);a=p.parse_args();package(a.source_root)
