#!/usr/bin/env python3
"""Add complete original CT/operative source composites with explicit per-investigation attachments."""
import argparse,hashlib,json,re,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CAPTIONS={3:'Source hepatoduodenal-ligament and hepatorenal-recess observations on CT A, with an operative view B retained separately.',
4:'Source pelvic/pouch-of-Douglas mass on CT A with a separate operative view B; the image pair is not calibrated 3D geometry.',
8:'Source omental-cake appearance on CT A and corresponding operative omental involvement B; complete source extent remains unapproved.',
9:'Source CT-enteroclysis bowel-serosal/loop changes A with operative deposits B. A routine CT cannot borrow the enteroclysis protocol or surgical visibility.',
11:'Source mesenteric fat change on CT-enteroclysis A, paired with small implants described at surgery B. CT appearance alone does not establish microscopic implants.',
15:'Source distorted/retracted mesentery and bowel-wall changes on CT A, with operative involvement B; this does not independently decide cytoreduction suitability.',
16:'Source mucinous/gelatinous peritoneal material and organ-surface scalloping on CT A, with operative material B. CT distribution alone is not histological proof.'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root):
 folder=ROOT/'docs/peritoneal-published-source-review';proof_path=folder/'original-source-review.json';proof=json.loads(proof_path.read_text())
 streams=json.loads((folder/'original-pdf-stream-selection.json').read_text());images_path=ROOT/'data/radiology/radiology-open-images.json';asset_path=ROOT/'data/radiology/radiology-asset-evidence.json';images=json.loads(images_path.read_text());new=[];assets=[];records=[]
 for r in proof['figures']:
  number=r['figure_number'];s=next(s for s in streams['figures'] if s['figure_number']==number);file=root/s['extracted_file']
  if sha(file)!=s['sha256'] or streams['source_pdf_sha256']!=proof['pdf_sha256']:raise ValueError('Original encoded figure/PDF changed')
  name='peritoneal-pmc8589944-fig'+str(number)+'.jpg';target=ROOT/'web/reference-media/radiology-open'/name;shutil.copyfile(file,target)
  credit=proof['source_copyright']+' '+', '.join(proof['authors'])+'. '+proof['article_title']+'. DOI '+proof['doi']+'. CC BY 4.0. Original complete Figure '+str(number)+' JPEG retained from verified publication PDF without pixel alteration. NLM/PMC Article Dataset snapshot; may not reflect latest NLM data. No endorsement implied.'
  context={'setting':'in_vivo','laterality':'not_reported','population':{'life_stage':'not_reported'},'depicted_state':'peritoneal_source_case_fig'+str(number),'extent':'local',
           'selected_panels':['a'],'panel_types':{'a':'CT','b':'Clinical photograph'},'panel_states':{'a':'peritoneal_source_case_fig'+str(number),'b':'peritoneal_source_case_fig'+str(number)}}
  limits='Original selected CT section only: no calibrated native DICOM volume, independently verified full surfaces/implant boundaries, actual source-phase timing or patient-specific 3D reconstruction. Operative/specimen photograph B is separate clinical context and cannot supply CT features, histology or operative eligibility. Source arrows/labels and operative correspondence are author descriptions, not independent anatomical approval.'
  for module,suffix in [('ra.ct-peritoneum','anatomy'),('ra.ct-peritoneal-carcinomatosis','metastatic')]:
   ident='open-peritoneal-'+suffix+'-pmc8589944-fig'+str(number)
   row={'id':ident,'kind':'clinical-image','src':'/app/reference-media/radiology-open/'+name,'width':s['width'],'height':s['height'],'sha256':s['sha256'],
        'source_url':proof['source_article_url'],'figure_url':proof['source_article_url']+'#Fig'+str(number),'figure_number':number,'asset_source_url':proof['pdf_url'],
        'modality':'CT','clinical_panels':['a'],'image_state':context['depicted_state'],'source_context':context,'caption':CAPTIONS[number],'alt':CAPTIONS[number],
        'structures_visible':['Source-described local peritoneal/omental/mesenteric observation; full reporting anatomy not approved'],
        'ancillary_panels':[{'kind':'Clinical photograph','panels':['b'],'structures_visible':['Source operative/specimen context'],
          'limits':'Separate clinical photograph, not CT; no calibrated anatomy, histology or independent registered spatial correspondence is inferred.'}],
        'limits':limits,'license':'CC BY 4.0','license_url':proof['license_url'],'attribution':credit,'rights_reviewed_on':'2026-10-04',
        'rights_review':'Original XML CC BY 4.0 grant and selected captions checked; original media/PDF MD5 and complete encoded stream readback verified.'}
   new.append((module,row))
   assets.append({'id':ident,'kind':'clinical_image','name':proof['article_title']+' Fig'+str(number),'local_path':'web/reference-media/radiology-open/'+name,
    'sha256':s['sha256'],'regions':['abdomen'],'investigation_ids':[module],'structure_ids':[],'modality':'CT','source_context':context,'requirement_coverage':{},
    'source':{'url':proof['source_article_url'],'figure_url':row['figure_url'],'asset_url':proof['pdf_url'],'license':{'name':'CC BY 4.0','url':proof['license_url'],
       'commercial_use':True,'redistribution':True,'review_status':'verified','evidence_path':str(proof_path.relative_to(ROOT)),'evidence_sha256':sha(proof_path),'attribution':credit,'reviewed_at':'2026-10-04'}},
    'pixel_provenance':{'source_pdf_sha256':proof['pdf_sha256'],'pdf_object_id':s['pdf_object_id'],'encoded_stream_sha256':s['sha256'],'source_pixels_changed':False,
       'original_encoded_stream_readback_verified':True,'highest_resolution_acquired_master_verified':False},
    'anatomical_review':{'status':'pending','reason':'Published local sections and separate operative photographs do not establish complete high-fidelity CT structures or registered clinical models.'},
    'visual_review':{'status':'source_checked','sha256':s['sha256'],'reviewed_at':'2026-10-04','evidence_path':'docs/peritoneal-published-source-review.md'}})
  records.append({'figure_number':number,'local_path':'web/reference-media/radiology-open/'+name,'sha256':s['sha256'],'width':s['width'],'height':s['height'],
                  'repository_dimensions':[r['width'],r['height']],'source_panel_types':r['source_panel_types'],'selected_ct_panels':['a'],'source_pixels_changed':False})
 ids={row['id'] for _,row in new}
 for module in ['ra.ct-peritoneum','ra.ct-peritoneal-carcinomatosis']:
  images[module]=[r for r in images.get(module,[]) if r['id'] not in ids]+[r for m,r in new if m==module]
 images_path.write_text(json.dumps(images,indent=2,ensure_ascii=False)+'\n')
 raw=asset_path.read_text();start=raw.index('[',raw.index('"assets"'))+1;cursor=start;decoder=json.JSONDecoder();retained=[]
 while True:
  cursor+=len(re.match(r'\s*',raw[cursor:]).group())
  if raw[cursor]==']':break
  r,end=decoder.raw_decode(raw,cursor)
  if r['id'] not in ids:retained.append(raw[cursor:end])
  cursor=end;cursor+=len(re.match(r'\s*',raw[cursor:]).group())
  if raw[cursor]==',':cursor+=1
 retained += [json.dumps(r,indent=2,ensure_ascii=False).replace('\n','\n    ') for r in assets]
 asset_path.write_text(raw[:start]+'\n    '+',\n    '.join(retained)+'\n  '+raw[cursor:])
 (folder/'packaged-source-images.json').write_text(json.dumps({'figures':records,'seven_unique_figures_attached_to_two_investigations':True,
    'clinical_approval':False,'structure_coverage_granted':False},indent=2)+'\n')


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);package(p.parse_args().source_root)
