#!/usr/bin/env python3
"""Preserve complete original appendix figures with reviewed case and modality boundaries."""
import copy
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from PIL import Image
from primer import radiology_catalog as catalog
from primer.curriculum import Curriculum
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
from tools.check_radiology_fidelity import digest

SOURCE = Path('/Users/peter/Documents/ChatGPT/Primer/.research/appendix-original-source')
REVIEW = ROOT / 'docs/appendix-original-source-review'
INV = 'ra.appendicitis'
PREFIX = 'open-appendix-pmc'
DATE = '2026-10-08'
LICENSE = 'https://creativecommons.org/licenses/by/4.0/'
# Explicit figure/page/object bindings, reviewed against complete numbered PDF pages.
# PDF object iteration order is not figure order (notably PMC4330234 Figures 2/3 and 7/8).
BINDINGS = {
    'PMC8531161': {2:(5,86), 3:(5,85), 4:(6,97), 5:(6,96), 6:(7,106), 7:(8,125), 8:(8,124), 9:(9,144)},
    'PMC6497212': {1:(2,13), 2:(3,17), 3:(3,19)},
    'PMC4330234': {1:(2,17), 2:(3,21), 3:(3,20), 4:(4,30), 5:(5,40), 6:(6,57), 7:(7,68), 8:(7,67)},
}
PANELS = {'PMC8531161':{5:['A','B'],6:['A','B','C','D'],7:['A','B'],9:['A','B']},
          'PMC4330234':{1:['A','B','C','D'],2:['A','B','C'],3:['A','B','C','D'],4:['A','B','C','D'],5:['A','B','C','D'],6:['A','B','C'],7:['A','B','C'],8:['A','B','C','D']}}
STEPS = {'PMC8531161':{2:[0,1],3:[1,3],4:[2],5:[1,2],6:[1],7:[1,2,3],8:[3],9:[3]},
         'PMC6497212':{1:[0,4],2:[0,2,3],3:[1]},
         'PMC4330234':{1:[2,3],2:[2,4],3:[4],4:[1,2,3],5:[3],6:[3],7:[3],8:[3]}}
POPULATIONS = {'PMC8531161':{2:(35,'female'),3:(20,'male'),4:(40,'male'),5:(58,'female'),7:(35,'female'),8:(54,'female')},
               'PMC6497212':{1:(10,'male'),2:(10,'male'),3:(10,'male')},
               'PMC4330234':{1:(32,'male'),2:(51,'male'),3:(16,'female'),6:(22,'male'),7:(17,'male'),8:(24,'male')}}
CAPTIONS = {
 'PMC8531161':{2:'Source uncomplicated appendix: coronal CT with a fluid-filled lumen and enhancing wall.',3:'Source gangrenous appendix: focal wall enhancement defect on axial CT.',4:'Source appendix with surrounding fat stranding on axial CT.',5:'Source gangrenous appendix with distal wall hyperenhancement: axial and sagittal CT.',6:'Four different source patients: obliterated, air-filled, fluid-filled and mixed-content appendiceal lumens.',7:'Source appendicolith: ultrasound A and subsequent CT B, with source pelvic fluid and peritoneal enhancement.',8:'Source perforated appendix: extraluminal air and fluid collection on coronal CT.',9:'Two different source patients: extraluminal mesoappendiceal air A and periappendiceal fluid B.'},
 'PMC6497212':{1:'Source abdominal radiograph: right hypochondrial opacity in a 10-year-old boy with a high retrocaecal appendix.',2:'Source ultrasound: high retrocaecal appendix with a 14.4 mm caliper and adjacent complex fluid.',3:'Source ultrasound: appendicolith appearance and posterior acoustic shadowing.'},
 'PMC4330234':{1:'Source CT before and three days after appendectomy: preoperative collection, postoperative gas, ileus and drain.',2:'Source CT before and three weeks after appendectomy: reactive caecal thickening and obtained comparison.',3:'Source postoperative MRI: T2 and postcontrast T1 bowel, caecal and pelvic views in a 16-year-old girl.',4:'Two different postoperative source patients: dropped appendicolith on unenhanced CT A; peritoneal enhancement on contrast CT B–D.',5:'Two different postoperative source patients with pericaecal and infracaecal abscesses.',6:'Source preoperative unenhanced CT A and postoperative contrast CT B/C with subphrenic and infrahepatic collections.',7:'Source postoperative pelvic and pericaecal abscesses with bladder displacement.',8:'Source liver abscess: initial CT A–C and later CT D after antibiotics.'},
}
EXTRA = {
 ('PMC8531161',3):'Source mucosal enhancement defect and source gangrenous histology remain distinct; a still does not resolve every wall layer or establish new-patient necrosis.',
 ('PMC8531161',5):'The source case was gangrenous despite mucosal hyperenhancement; enhancement is not automatic proof of uncomplicated disease.',
 ('PMC8531161',6):'A, B, C and D are four different patients. A and B were source uncomplicated cases; C perforated; D gangrenous. Intraluminal air or appearance alone does not exclude appendicitis or assign severity.',
 ('PMC8531161',7):'A is ultrasound, B subsequent CT in the same source case. Their source correspondence does not establish validated native registration, acquisition timing or calibrated measurements.',
 ('PMC8531161',9):'A and B are different patients (source 73-year-old man and 39-year-old man respectively); extraluminal air and fluid are not one reconstructed case.',
 ('PMC6497212',1):'This is an abdominal radiograph in the source 10-year-old boy, not an ultrasound or CT appendix view. The projected opacity alone does not establish appendiceal origin; ultrasound and surgery supplied separate source confirmation.',
 ('PMC6497212',2):'Source high ascending retrocaecal appendix in a 10-year-old boy, with a published 14.4 mm caliper. Source surgery found mid-shaft perforation and a healthy base. The still does not independently demonstrate compression, the complete course or every perforation boundary.',
 ('PMC6497212',3):'Source acoustic shadowing and clinical/surgical appendicolith context remain separate. An echogenic focus is not an independently segmented stone or a universal perforation classifier.',
 ('PMC4330234',1):'A is preoperative, B–D are three days after appendectomy in the same source patient. Residual postoperative gas, drain and ileus are not an intact normal appendix or automatic abscess/perforation in a new examination.',
 ('PMC4330234',2):'A is preoperative, B–C three weeks after appendectomy. Reactive caecal thickening and source recovery are not a normal intact appendix, Crohn diagnosis or universal clearance of infection.',
 ('PMC4330234',3):'This is postoperative MRI in a 16-year-old girl, 15 weeks after appendectomy. A/B are T2; C/D are postcontrast T1 with/without fat suppression. It is not CT, an intact appendix, validated diffusion or a supplied native volume.',
 ('PMC4330234',4):'A is unenhanced CT in one 22-year-old woman three days after appendectomy; B–D are contrast CT in a different 26-year-old woman nine days after surgery. Do not transfer phase, patient identity or dropped-appendicolith confirmation between these groups.',
 ('PMC4330234',5):'A/B are one 38-year-old woman; C/D a different 36-year-old man. Both are postoperative abscess examples, not a registered volume or shared treatment response.',
 ('PMC4330234',6):'A is preoperative unenhanced CT; B/C are postoperative contrast CT two weeks later in the same source man. Subphrenic and infrahepatic abscess confirmation is source surgical context, not calibrated enhancement or a new drainage recommendation.',
 ('PMC4330234',7):'Source postoperative pelvic and pericaecal communicating collections displace the bladder. Published selected planes do not establish every tract wall or a current surgical plan.',
 ('PMC4330234',8):'A–C are initial source liver-abscess CT; D is a later CT after antibiotics. Source ultrasound detection is described in the paper but no ultrasound panel is shown. Selected images do not supply calibrated temporal registration, liquefaction volume or universal drainage suitability.',
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def context(pmc, number, panels, mode):
    cases = {'source_case':panels}
    if (pmc,number)==('PMC8531161',6):
        cases = {f'case_{p}':[p] for p in panels}
    elif (pmc,number)==('PMC8531161',9):
        cases = {'source_73_year_male':['A'],'source_39_year_male':['B']}
    elif (pmc,number)==('PMC4330234',4):
        cases = {'source_22_year_female':['A'],'source_26_year_female':['B','C','D']}
    elif (pmc,number)==('PMC4330234',5):
        cases = {'source_38_year_female':['A','B'],'source_36_year_male':['C','D']}
    age_sex = POPULATIONS.get(pmc,{}).get(number)
    population = {'life_stage':'unknown','age_not_supplied':True,'sex_not_supplied':True}
    if age_sex:
        age,sex = age_sex
        population = {'life_stage':'child' if age<18 else 'adult','age_years':age,'sex':sex,'age_not_supplied':False,'sex_not_supplied':False}
    types = {p:mode for p in panels}
    if (pmc,number)==('PMC8531161',7):
        types = {'A':'Ultrasound','B':'CT'}
    return {'setting':'in_vivo','laterality':'unknown','population':population,'extent':'local',
            'depicted_state':'postoperative_source_example' if pmc=='PMC4330234' else 'source_appendiceal_pathology_example',
            'selected_panels':['B'] if (pmc,number)==('PMC8531161',7) else panels,
            'panel_types':types,'panel_states':{p:'source_case_context_only' for p in panels},
            'source_case_groups':cases,'source_panels_are_different_patients':len(cases)>1,
            'source_different_figures_assumed_same_patient':False,
            'source_same_case_across_figures':'PMC6497212_case_report' if pmc=='PMC6497212' else None,
            'source_native_registration_verified':False,'source_full_microanatomical_coverage_approved':False,
            'source_pixels_supply_compression_flow_or_complete_native3D':False,
            'source_labels_are_current_patient_histology_or_cause':False}

def package():
    REVIEW.mkdir(parents=True,exist_ok=True)
    proof = {'schema_version':1,'reviewed_on':DATE,'commercial_reuse_verified':True,
             'source_pixel_changes':False,'clinical_anatomical_or_full_reporting_approval_granted':False,
             'held_candidates':json.loads((SOURCE/'rights-held-review.json').read_text()),'articles':[]}
    rows,assets = [],[]
    for pmc,bindings in BINDINGS.items():
        xml = (SOURCE/(pmc+'.1.xml')).read_bytes()
        tree = ET.fromstring(xml)
        permissions = tree.find('.//permissions/license')
        assert LICENSE in ET.tostring(permissions,encoding='unicode')
        authors = [' '.join(filter(None,[n.findtext('given-names'),n.findtext('surname')])) for n in tree.findall('.//article-meta/contrib-group/contrib/name')]
        title = ''.join(tree.find('.//article-title').itertext())
        doi = tree.findtext('.//article-id[@pub-id-type="doi"]')
        figures = {int(''.join(f.find('label').itertext()).split()[-1].rstrip('.')):f for f in tree.findall('.//fig')}
        inventory = json.loads((SOURCE/pmc/'PDF-masters/image-inventory.json').read_text())
        article = {'pmcid':pmc,'doi':doi,'title':title,'authors':authors,'license':'CC BY 4.0','license_url':LICENSE,
                   'original_XML_sha256':sha(xml),'original_PDF_sha256':sha((SOURCE/(pmc+'.1.pdf')).read_bytes()),
                   'original_metadata_sha256':sha((SOURCE/(pmc+'.1.json')).read_bytes()),'figures':[]}
        (REVIEW/(pmc+'-original.xml')).write_bytes(xml)
        for number,(page,obj) in bindings.items():
            figure = figures[number]
            assert figure.find('attrib') is None
            master = next(r for r in inventory if r['page']==page and r['object']==obj)
            path = SOURCE/pmc/'PDF-masters'/master['filename']
            raw = path.read_bytes()
            assert sha(raw)==master['sha256']
            html_name = figure.find('graphic').attrib['{http://www.w3.org/1999/xlink}href']
            with Image.open(SOURCE/pmc/'HTML-masters'/html_name) as html:
                html_size = html.size
            with Image.open(path) as im:
                assert sha(im.tobytes())==master['pixel_sha256']
                assert im.width>=html_size[0] and im.height>=html_size[1]
                assert sha(im.info.get('icc_profile',b''))==master['icc_sha256']
            caption = ''.join(figure.find('caption').itertext())
            mode = 'Radiography' if (pmc,number)==('PMC6497212',1) else 'Ultrasound' if pmc=='PMC6497212' else 'MRI' if (pmc,number)==('PMC4330234',3) else 'CT'
            panels = PANELS.get(pmc,{}).get(number,['full'])
            ctx = context(pmc,number,panels,mode)
            ident = PREFIX+pmc.removeprefix('PMC')+'-fig'+str(number)
            local = 'web/reference-media/radiology-open/appendix-'+pmc.lower()+'-fig'+str(number)+'.png'
            (ROOT/local).write_bytes(raw)
            url = 'https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/'
            fig_id = figure.attrib['id']
            attribution = ', '.join(authors)+'. '+title+'. DOI '+doi+'. Original '+''.join(figure.find('label').itertext())+'. CC BY 4.0. Complete original decoded PDF pixels and ICC preserved; no crop, resize, enhancement or relabelling. No endorsement implied.'
            limits = 'Complete published source figure, not a raw DICOM series or source segmentation. Source-labelled morphology, selected planes and source surgery/histology remain case context; no every-layer boundary, current-patient diagnosis, calibrated physiology or native3D registration is approved. '+EXTRA.get((pmc,number),'Selected published CT morphology is not an independently complete appendix, wall-layer or surrounding-tissue map.')
            row = {'id':ident,'kind':'clinical-image','modality':mode,'figure_number':number,'src':'/app/'+local.removeprefix('web/'),
                   'sha256':sha(raw),'width':master['size'][0],'height':master['size'][1],'source_url':url,'figure_url':url+'#'+fig_id,
                   'asset_source_url':'https://pmc-oa-opendata.s3.amazonaws.com/'+pmc+'.1/'+pmc+'.1.pdf',
                   'clinical_panels':ctx['selected_panels'],'source_context':ctx,'image_state':ctx['depicted_state'],
                   'caption':'Original '+pmc+' '+''.join(figure.find('label').itertext())+': '+CAPTIONS[pmc][number],
                   'alt':'Complete original '+mode+' source '+pmc+' '+''.join(figure.find('label').itertext())+'.',
                   'source_caption_full':caption,'limits':limits,'structures_visible':['Source-local appendix or postoperative site and adjacent acquired interfaces; full native boundaries unapproved'],
                   'license':'CC BY 4.0','license_url':LICENSE,'attribution':attribution,'rights_reviewed_on':DATE,
                   'rights_review':'Original CC BY4 XML grant, numbered complete PDF pages and matching HTML figures reviewed; no excluded figure-specific credit found.'}
            if (pmc,number)==('PMC8531161',7):
                row['ancillary_panels']=[{'kind':'Ultrasound','panels':['A'],'structures_visible':['Original source ultrasound appendix/appendicolith view'],'limits':'Separate source modality, same source case; no validated native registration or calibrated measurements.'}]
            catalog._validate_source_panel_roles(row)
            rows.append(row)
            transport = {'figure_number':number,'source_PDF_page':page,'source_PDF_object':obj,'source_master_filename':master['filename'],
                         'source_master_sha256':sha(raw),'width':master['size'][0],'height':master['size'][1],'mode':master['mode'],
                         'decoded_pixel_sha256':master['pixel_sha256'],'source_ICC_sha256':master['icc_sha256'],
                         'HTML_master_dimensions':html_size,'highest_resolution_acquired_master_verified':True,
                         'source_caption_full':caption,'source_pixels_resampled_or_enhanced':False,'source_pixel_changes':False}
            article['figures'].append(transport)
            assets.append({'id':ident,'kind':'clinical_image','name':row['alt'],'local_path':local,'sha256':sha(raw),'modality':mode,
                           'investigation_ids':[INV],'structure_ids':[],'requirement_coverage':{},'source_context':ctx,
                           'source':{'url':url,'figure_url':row['figure_url'],'asset_url':row['asset_source_url'],
                                     'license':{'name':'CC BY 4.0','url':LICENSE,'commercial_use':True,'redistribution':True,'review_status':'verified',
                                                'evidence_path':'docs/appendix-original-source-review/original-source-review.json','attribution':attribution,'reviewed_at':DATE}},
                           'pixel_provenance':transport,'anatomical_review':{'status':'pending','reason':'Full published figures do not establish every reported structure/interface or independent clinical/pathological approval.'}})
        proof['articles'].append(article)
    proof_path = REVIEW/'original-source-review.json'
    proof_path.write_text(json.dumps(proof,indent=2,ensure_ascii=False)+'\n')
    for asset in assets:
        asset['source']['license']['evidence_sha256']=sha(proof_path.read_bytes())
    p=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(p.read_text())
    data[INV]=[r for r in data.get(INV,[]) if not r['id'].startswith(PREFIX)]+rows
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix=PREFIX)
    previous = catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference']['key_images']
    archive=REVIEW/'replaced-investigation-images.json'
    if not archive.exists():
        archive.write_text(json.dumps({'replaced_investigation_images':previous,'reason':'Remote placeholders replaced with local original source figures; source originals and limitations retained.'},indent=2)+'\n')
    p=ROOT/'data/radiology/investigation-overrides-non-msk.json';data=json.loads(p.read_text());data.setdefault(INV,{})['key_images']=[];p.write_text(json.dumps(data,indent=2)+'\n')
    p=ROOT/'data/radiology/investigation-source-images.json';text=p.read_text()
    if '"'+INV+'"' in text:
        start=text.index('[',text.index('"'+INV+'"'));_,end=json.JSONDecoder().raw_decode(text,start);p.write_text(text[:start]+'[]'+text[end:])
    p=ROOT/'data/radiology/reporting-steps/abdomen.json';text=p.read_text();start=text.index('{',text.index('"'+INV+'"'));node,end=json.JSONDecoder().raw_decode(text,start)
    node['start']={'images':[],'module_illustrations':False}
    old_ids={r['id'] for r in previous}
    for step in node['steps']:
        step['images']=[i for i in step.get('images',[]) if i not in old_ids and not i.startswith(PREFIX)]
        step['normal']={}
    for pmc,figs in STEPS.items():
        for number,indices in figs.items():
            for index in indices:node['steps'][index]['images'].append(PREFIX+pmc.removeprefix('PMC')+'-fig'+str(number))
    # Preserve existing normal/local US examples in the actual reporting steps.
    for number,indices in {1:[0,1],2:[1,2],3:[0,2]}.items():
        for index in indices:
            ident='open-appendix-mostbeck-2016-fig'+str(number)
            if ident not in node['steps'][index]['images']:node['steps'][index]['images'].append(ident)
    node['model']={'family':'bowel','reporting_aim':'Partial schematic orientation only. It does not reproduce the actual complete appendiceal course, every wall layer, mesoappendix, vessel/nerve, perforation, collection or postoperative anatomy. Native full-course and every-structure image/schematic/model coverage remain unverified.'}
    node['steps'][4]['look']+=' Distinguish source postoperative reactive caecal change and obtained comparisons from an intact appendix or a new bowel diagnosis; retain unacquired urinary, adnexal and other alternative-diagnosis scope.'
    p.write_text(text[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+text[end:])
    for value in vars(catalog).values():
        if callable(getattr(value,'cache_clear',None)):value.cache_clear()
    ref=catalog.detail(Curriculum(),catalog.resolve(INV))['radiology_reference']
    p=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(p.read_text())
    next(r for r in data['investigations'] if r['investigation_id']==INV)['source_contract_sha256']=digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    p.write_text(json.dumps(data,indent=2)+'\n')
    print('19 complete original source masters integrated; original 3 US references preserved; no full anatomical coverage approved')

if __name__=='__main__':
    package()
