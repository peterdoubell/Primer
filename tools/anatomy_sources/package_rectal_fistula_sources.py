#!/usr/bin/env python3
"""Preserve original full rectal MRI/anatomy and fistula source figures with scoped roles."""
import copy,hashlib,json,sys,xml.etree.ElementTree as E
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image
from primer import radiology_catalog as catalog
from primer.curriculum import Curriculum
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
from tools.check_radiology_fidelity import digest
SOURCE=Path('/Users/peter/Documents/ChatGPT/Primer/.research/rectal-original-source');OUT=ROOT/'docs/rectal-fistula-published-source-review'
ANATOMY='PMC9849549';FISTULA='PMC13512459';PREFIX='open-anorectal-';LICENSE='https://creativecommons.org/licenses/by/4.0/'
BINDINGS={1:(2,57),2:(3,82),3:(4,95),4:(4,94),5:(5,124),6:(7,156),7:(7,155),8:(8,175),9:(9,191),10:(10,203),11:(10,202),12:(12,245),13:(13,258),14:(14,269),15:(15,285)}
FISTULA_PAGES={1:3,2:5,3:5,21:15,22:15,23:16,24:17,25:18,26:19,27:21,28:22}
RECTAL_STEPS={1:[1,2],2:[1],3:[0],4:[0,1],5:[1],6:[2],7:[0,1,2],8:[1,2],9:[1],10:[2],11:[2],12:[3],13:[4],14:[4],15:[4]}
FISTULA_STEPS={1:[1,2,3,4],2:[1,3,4],3:[1,3,4],21:[0],22:[0,1],23:[0,1],24:[0,1,2],25:[0,1],26:[1,2,3,4],27:[1,2],28:[1,2,3]}
ROLES={
 1:{'MRI':['a','b']},2:{'MRI':['a','b','d'],'Histology':['c']},3:{'MRI':['a','b']},4:{'MRI':['a'],'Schematic':['b']},5:{'MRI':['b','c'],'Schematic':['a']},6:{'MRI':['a','b']},7:{'MRI':['a','b']},
 8:{'MRI':['a_MRI','b_MRI','c_MRI'],'Schematic':['left_schematic','a_schematic','b_schematic','c_schematic'],'Anatomical specimen photograph':['middle_TME_specimen']},
 9:{'MRI':['a','b','c']},10:{'MRI':['a','b','c']},11:{'MRI':['a','b']},12:{'MRI':['b','c','d'],'MRI-derived plot':['a']},13:{'MRI':['a','b','c','d']},
 14:{'MRI':['a_MRI','b_MRI','c_MRI'],'Schematic':['left_schematic','a_schematic','b_schematic','c_schematic']},15:{'MRI':['a','b']}}
CASES={1:{'source_52_year_male':['a'],'source_55_year_female':['b']},2:{'source_example_a':['a'],'source_example_b':['b'],'source_histology_unregistered':['c'],'source_63_year_male':['d']},5:{'source_62_year_male':['b'],'source_59_year_female':['c'],'conceptual_drawing':['a']},7:{'source_male':['a'],'source_female':['b']},8:{'source_MRI_identity_unverified':['a_MRI','b_MRI','c_MRI'],'unregistered_TME_specimen':['middle_TME_specimen'],'conceptual_drawings':['left_schematic','a_schematic','b_schematic','c_schematic']},10:{'source_male_without_rectal_cancer':['a','b'],'different_source_case':['c']},11:{'source_63_year_male':['a'],'source_83_year_female':['b']},13:{'source_74_year_male_baseline_postCRT':['a','b'],'source_62_year_male_baseline_postCRT':['c','d']},14:{'source_local_excision':['a_MRI'],'source_LAR':['b_MRI'],'source_APR':['c_MRI'],'conceptual_drawings':['left_schematic','a_schematic','b_schematic','c_schematic']}}
EXTRA={
 2:'MRI a/b/d and histology c are different evidence; histology is not registered to these source MRI planes. Typical two-layered MRI does not separately resolve all histological layers or universally distinguish T1 fromT2.',
 4:'MRI a is a source male anatomy example; drawing b shows landmarks including the dentate line,which is not ordinarily resolved by MRI. No drawn position becomes an acquired native boundary.',
 5:'b andc are different patients with different source invasion patterns. The conceptual drawing a is not their registered sphincter geometry.',
 8:'Left and right drawings,TME specimen and MRI examples remain separate. Specimen ink and drawn tumour labels do not supply native patient registration,current stage or a complete surgical margin.',
 10:'a/b are source normal-appearing vascular context in one male; c is a different source dilated venous-plexus case. No calibrated flow,pressure or same-patient reconstruction is inferred.',
 12:'a is a processed anatomical overview calledMRI in the source; its raw acquisition/rendering method and native3D geometry are not provided. b/c/d are actual source MRI planes; compartment colours are publication annotations,not independently validated nodal masks.',
 13:'a/b andc/d are two different baseline/postCRT patients. Source follow-up and pathology differ; no current-patient response is inferred. T2 fibrosis does not independently prove pathological complete response or persistent invasion.',
 14:'Three different source postoperative techniques/MRI examples remain separate from drawings. Do not infer one registered patient,full surgical reconstruction or a current treatment recommendation.',
 15:'Source postoperative fibrosis and source ypT3N2 history belong to this41-year-old male. Selected views are not universal exclusion of recurrent disease.'}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def package():
    OUT.mkdir(parents=True,exist_ok=True);proof={'reviewed_on':'2026-10-08','source_figures_resampled_cropped_enhanced_or_relabelled':False,'clinical_anatomical_or_full_reporting_approval_granted':False,'articles':[]};rows=[];assets=[]
    for pmc,selected in [(ANATOMY,list(BINDINGS)),(FISTULA,list(FISTULA_PAGES))]:
        xml=(SOURCE/(pmc+'.1.xml')).read_bytes();tree=E.fromstring(xml);grant=tree.find('.//permissions/license');assert LICENSE in E.tostring(grant,encoding='unicode')
        authors=[' '.join(filter(None,[n.findtext('given-names'),n.findtext('surname')])) for n in tree.findall('.//article-meta/contrib-group/contrib/name')];title=''.join(tree.find('.//article-title').itertext());doi=tree.findtext('.//article-id[@pub-id-type="doi"]')
        figures={int(''.join(f.find('label').itertext()).split()[-1].rstrip('.')):f for f in tree.findall('.//fig')};pdf=json.loads((SOURCE/pmc/'PDF-masters/inventory.json').read_text());article={'pmcid':pmc,'title':title,'doi':doi,'authors':authors,'license':'CC BY4.0','source_XML_sha256':sha(xml),'source_PDF_sha256':sha((SOURCE/(pmc+'.1.pdf')).read_bytes()),'source_metadata_sha256':sha((SOURCE/(pmc+'.1.json')).read_bytes()),'figures':[]}
        (OUT/(pmc+'-original.xml')).write_bytes(xml)
        for n in selected:
            figure=figures[n];assert figure.find('attrib') is None;caption=''.join(figure.find('caption').itertext());html_name=figure.find('graphic').attrib['{http://www.w3.org/1999/xlink}href'];html_path=SOURCE/pmc/'HTML-masters'/html_name
            if pmc==ANATOMY:
                page,obj=BINDINGS[n];master=next(m for m in pdf if m['page']==page and m['object']==obj);path=SOURCE/pmc/'PDF-masters'/master['file'];raw=path.read_bytes();assert sha(raw)==master['sha256'];source_kind='Complete original decoded PDF raster';source_url='https://pmc-oa-opendata.s3.amazonaws.com/'+pmc+'.1/'+pmc+'.1.pdf'
                with Image.open(html_path) as im:html_size=im.size
                with Image.open(path) as im:assert im.width>=html_size[0] and im.height>=html_size[1]
                roles=ROLES[n];mode='MRI';scheme=roles.get('Schematic',[]);types={p:k for k,panels in roles.items() for p in panels};clinical=roles['MRI'];groups=CASES.get(n,{'source_figure_patient_correspondence_unverified':list(types)})
                populations={9:{'life_stage':'adult','age_years':48,'sex':'female'},15:{'life_stage':'adult','age_years':41,'sex':'male'}};population=populations.get(n,{'life_stage':'unknown','age_not_supplied':True,'sex_not_supplied':True})
                extra=EXTRA.get(n,'Source normal/pathological labels and local tissue appearances do not establish every fine boundary or a new current-patient diagnosis.')
            else:
                page=FISTULA_PAGES[n];obj=None;path=html_path;raw=path.read_bytes();source_kind='Complete original publisher HTML WebP';source_url='https://pmc-oa-opendata.s3.amazonaws.com/'+pmc+'.1/'+html_name;roles={'Schematic':['full']} if n==1 else {'MRI':(['full'] if n==21 else ['A','A+'] if n==27 else ['A','A+','B','B+','C','C+'] if n in [2,24,25] else ['A','A+','B','B+'])};mode='Schematic' if n==1 else 'MRI';scheme=roles.get('Schematic',[]);types={p:k for k,panels in roles.items() for p in panels};clinical=roles[mode];groups={'conceptual_source_diagram' if n==1 else 'source_figure_case_correspondence_not_independently_verified':list(types)};population={'life_stage':'unknown','age_not_supplied':True,'sex_not_supplied':True};html_size=Image.open(html_path).size
                extra='Publisher drawn fills/arrows and annotated/unannotated pairs are original source display,not supplied native segmentation masks or full tract-lumen geometry. No calibrated source acquisition or3D registration is supplied.'
                if n>=21:extra+=' The source describes a lithotomy clock convention; actual MRI acquisition position is not independently verified and is not inferred from that wording.'
                if n==27:extra+=' Source legend says another patient while referring toFigure26; identity across the figures is unresolved and never merged. This is a source blind-ending sinus example,not proof of a complete external opening/fistula.'
            with Image.open(path) as im:
                im.load();pixels=sha(im.tobytes());icc=sha(im.info.get('icc_profile',b''));width,height=im.size;image_mode=im.mode
            ident=PREFIX+pmc.lower()+'-fig'+str(n);local='web/reference-media/radiology-open/anorectal-'+pmc.lower()+'-fig'+str(n)+('.webp' if pmc==FISTULA else '.png');(ROOT/local).write_bytes(raw)
            context={'setting':'source_illustration' if mode=='Schematic' else 'in_vivo','laterality':'unknown','population':population,'extent':'local','depicted_state':'source_anorectal_anatomy_pathology_or_postoperative_example','selected_panels':clinical,'panel_types':types,'panel_states':{p:'source_only_case_or_illustration' for p in types},'source_case_groups':groups,'source_panels_are_different_patients':n in [1,5,7,10,11,13,14] if pmc==ANATOMY else False,'source_different_figures_assumed_same_patient':False,'source_native_registration_verified':False,'source_full_fine_anatomy_approved':False,'source_current_diagnosis_or_histology_inferred':False}
            attribution=', '.join(authors)+'. '+title+'. DOI'+doi+'. Figure'+str(n)+'. CC BY4.0. '+source_kind+' pixels/profile preserved; no crop,resize,enhancement or relabelling. No endorsement implied.'
            limits='Complete original source figure; selected source planes and conceptual/pathology/specimen evidence remain distinct. No every-structure native3D,full acquisition/temporal/physiological calibration,current histology or independent whole-reporting approval is supplied. '+extra
            row={'id':ident,'kind':'schematic' if mode=='Schematic' else 'clinical-image','modality':mode,'figure_number':n,'src':'/app/'+local.removeprefix('web/'),'sha256':sha(raw),'width':width,'height':height,'source_url':'https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/','figure_url':'https://pmc.ncbi.nlm.nih.gov/articles/'+pmc+'/#'+figure.attrib['id'],'asset_source_url':source_url,'alt':'Complete original anorectal source '+pmc+' Figure'+str(n)+'.','caption':'Original '+pmc+' Figure'+str(n)+' · '+source_kind+'; source case/illustration context only.','source_caption_full':caption,'clinical_panels':clinical,'source_context':context,'image_state':context['depicted_state'],'structures_visible':['Source-local anorectal tissue,compartment,lesion or route; full native boundaries unapproved'],'limits':limits,'license':'CC BY 4.0','license_url':LICENSE,'attribution':attribution,'rights_reviewed_on':'2026-10-08','rights_review':'Original XML CC BY4 grant and complete numbered PDF/HTML figures reviewed; no excluded figure credit found.'}
            if pmc==ANATOMY and n in [8,14]:
                row['panel_identifier_scheme']='descriptive_source_positions';context['panel_identifier_scheme']='descriptive_source_positions'
            if scheme:
                row['schematic_panels']=scheme;row['schematic_structures_visible']=['Original conceptual source anorectal layers/routes/operative relationships; not registered native geometry']
                if mode!='Schematic':row['contains_schematic_panels']=True
            ancillary=[{'kind':k,'panels':v,'structures_visible':['Separate original source '+k+' evidence'],'limits':'Source display role only; no borrowed native registration,current tissue diagnosis or full fine-anatomical coverage.'} for k,v in roles.items() if k not in [mode,'Schematic']]
            if ancillary:row['ancillary_panels']=ancillary
            catalog._validate_source_panel_roles(row);rows.append(row)
            fproof={'figure_number':n,'source_master_kind':source_kind,'source_master_filename':str(path.relative_to(SOURCE)),'source_master_sha256':sha(raw),'decoded_pixel_sha256':pixels,'source_ICC_sha256':icc,'width':width,'height':height,'mode':image_mode,'source_PDF_page':page,'source_PDF_object':obj,'original_HTML_dimensions':html_size,'source_caption_full':caption,'original_source_pixels_resampled_cropped_enhanced_or_relabelled':False,'original_acquisition_matrix_or_native_geometry_verified':False};article['figures'].append(fproof)
            assets.append({'id':ident,'kind':'schematic' if mode=='Schematic' else 'clinical_image','name':row['alt'],'local_path':local,'sha256':sha(raw),'modality':mode,'investigation_ids':['ra.mri-rectal-cancer' if pmc==ANATOMY else 'ra.mri-perianal-fistula'],'structure_ids':[],'requirement_coverage':{},'source_context':context,'source':{'url':row['source_url'],'asset_url':source_url,'license':{'name':'CC BY 4.0','url':LICENSE,'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':'docs/rectal-fistula-published-source-review/original-source-review.json','attribution':attribution,'reviewed_at':'2026-10-08'}},'pixel_provenance':fproof,'anatomical_review':{'status':'pending','reason':'Published source figures do not independently supply every reported layer/interface,registered native3D or current diagnosis.'}})
        proof['articles'].append(article)
    proof_path=OUT/'original-source-review.json';proof_path.write_text(json.dumps(proof,indent=2)+'\n');copies=[];all_assets=[]
    for inv in ['ra.mri-rectal-cancer','ra.mri-perianal-fistula']:
        selected_rows=[]
        for row,asset in zip(rows,assets):
            pmc=ANATOMY if ANATOMY.lower() in row['id'] else FISTULA;n=row['figure_number']
            if inv=='ra.mri-rectal-cancer' and pmc!=ANATOMY:continue
            if inv=='ra.mri-perianal-fistula' and pmc==ANATOMY and n not in [2,4,5,6]:continue
            r=copy.deepcopy(row);a=copy.deepcopy(asset);r['id']=a['id']=row['id']+'-'+inv.removeprefix('ra.');a['investigation_ids']=[inv];a['source']['license']['evidence_sha256']=sha(proof_path.read_bytes());selected_rows.append(r);all_assets.append(a)
        copies.append((inv,selected_rows))
    p=ROOT/'data/radiology/radiology-open-images.json';data=json.loads(p.read_text());steps_path=ROOT/'data/radiology/reporting-steps/abdomen.json';text=steps_path.read_text()
    for inv,images in copies:
        data[inv]=[r for r in data.get(inv,[]) if not r['id'].startswith(PREFIX)]+images;start=text.index('{',text.index('"'+inv+'"'));node,end=json.JSONDecoder().raw_decode(text,start)
        for step in node['steps']:step['images']=[id for id in step.get('images',[]) if not id.startswith(PREFIX)]
        for row in images:
            n=row['figure_number'];anatomy=ANATOMY.lower() in row['id'];indices=RECTAL_STEPS[n] if inv=='ra.mri-rectal-cancer' else [1,3,4] if anatomy else FISTULA_STEPS[n]
            for index in indices:node['steps'][index]['images'].append(row['id'])
        text=text[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n    ')+text[end:]
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');steps_path.write_text(text);append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',all_assets,prefix=PREFIX)
    for value in vars(catalog).values():
        if callable(getattr(value,'cache_clear',None)):value.cache_clear()
    p=ROOT/'data/radiology/non-msk-structure-requirements.json';data=json.loads(p.read_text())
    for item in data['investigations']:
        if item['investigation_id'] in [inv for inv,_ in copies]:
            ref=catalog.detail(Curriculum(),catalog.resolve(item['investigation_id']))['radiology_reference'];item['source_contract_sha256']=digest({k:ref.get(k) for k in ['reporting','report_templates','walkthrough','reading']})
    p.write_text(json.dumps(data,indent=2)+'\n');print('26 complete original masters;30 scoped references;previous clinical references preserved;full coverage unapproved')

if __name__=='__main__':package()
