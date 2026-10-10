#!/usr/bin/env python3
"""Bind reviewed cervical originals without granting patient geometry or fine-layer coverage."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];INV='ra.mri-cervical-cancer';PREFIX='open-cervical-cancer-';REVIEW=ROOT/'docs/cervical-cancer-source-review'
def save(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def integrate():
 contract=json.loads((REVIEW/'source-figure-contract.json').read_text());proof=json.loads((REVIEW/'published-source-preservation.json').read_text());independent=json.loads((ROOT/'docs/cervical-cancer-independent-source-review-20261010.json').read_text())
 rows=contract['structure_atlas'];assert len(rows)==32 and proof['figure_count']==32 and not contract['clinical_approval']
 assert independent['independent_primary_objects_checked'] and independent['figure_count']==32 and not independent['source_preservation_blockers_remaining']
 reviewed={f['id']:f['runtime_sha256'] for f in independent['figures']}
 assert reviewed=={row['id']:row['sha256'] for row in rows}
 for row in rows:assert sha(ROOT/'web'/row['src'].removeprefix('/app/'))==row['sha256']
 # The shared parent previews must not retain the held remote thumbnails.
 p=ROOT/'data/radiology/key-images-foundations-body.json';catalog=json.loads(p.read_text());by={row['id']:row for row in rows}
 archive=REVIEW/'held-parent-lesson-key-images.json'
 if not archive.exists():save(archive,{'legacy':{key:catalog[key] for key in ['uterine-mr-image-1','uterine-mr-image-2','uterine-mr-image-3']},'reason':'Unknown commercial grants and generic source-role mismatches; complete reviewed local previews replace them.','clinical_approval':False})
 chosen=[PREFIX+'normal-uterus-2018-fig3-1',PREFIX+'pmc10605640-fig1',PREFIX+'pmc11171278-fig2']
 guides_path=ROOT/'data/radiology/module-guides.json';guides=json.loads(guides_path.read_text());parent=guides['rad.5.uterine-mr']
 for index,identifier in enumerate(chosen,1):
  row=by[identifier];slot='uterine-mr-image-'+str(index)
  catalog[slot]={key:row[key] for key in ['src','alt','source_url','attribution','license','license_url','sha256','width','height','source_caption_full']}
  catalog[slot].update(caption=row['caption']+' '+row['limits'],source_title=row['source_figure_label'],image_type='clinical',reviewed_at='2026-10-10',source_context=dict(row['source_context'],current_patient_findings=False),original_asset_id=row['id'])
  image=next(image for image in parent['key_images'] if image['id']==slot);image.update(label=row['caption'],description=row['caption']+' '+row['limits'])
 save(p,catalog);save(guides_path,guides)
 p=ROOT/'data/radiology/radiology-open-images.json';d=json.loads(p.read_text());d[INV]=rows;save(p,d)
 p=ROOT/'data/radiology/reporting-steps/abdomen.json';d=json.loads(p.read_text());entry=d['investigations'][INV]
 def f(pmc,n):return PREFIX+pmc+'-fig'+str(n)
 book=PREFIX+'normal-uterus-2018-fig3-1'
 entry['start']['images']=[f('pmc11171278',1),book,f('pmc10605640',1)]
 groups=[
  [f('pmc10605640',1),f('pmc11171278',1),book]+[f('pmc7338830',n) for n in [3,4,6]],
  [f('pmc10605640',n) for n in [3,4,5,13]]+[f('pmc10886638',4)],
  [f('pmc10605640',n) for n in [6,8]]+[f('pmc10886638',n) for n in [10,11]]+[f('pmc11171278',2)],
  [f('pmc10605640',n) for n in [5,7]]+[f('pmc10886638',3)],
  [f('pmc10605640',n) for n in [8,10]]+[f('pmc11171278',1)],
  [f('pmc10605640',11)]+[f('pmc10886638',n) for n in [1,6]]+[f('pmc11171278',2)],
  [f('pmc10605640',n) for n in [2,9,10,12]]+[f('pmc10886638',n) for n in [8,10]],
  [f('pmc10605640',n) for n in [13,17,18]]+[f('pmc10886638',4)]]
 assert len(entry['steps'])==len(groups)==8
 ids={r['id'] for r in rows}
 for step,images in zip(entry['steps'],groups):assert set(images)<=ids;step['images']=images
 # Procedure/device examples remain complete gallery references, explicitly
 # distinguished from pretreatment staging by their original source context.
 save(p,d)
 assets=[];article={a.get('pmcid') or a.get('source_id'):a for a in proof['articles']}
 records={r['id']:r for r in proof['figures']}
 for row in rows:
  rec=records[row['id']];key=rec.get('pmcid')
  if key is None:
   assert row['id']==PREFIX+'normal-uterus-2018-fig3-1';key='normal-uterus-2018'
  a=article[key]
  evidence=REVIEW/(a['pmcid']+'-original.xml') if a.get('pmcid') else REVIEW/'normal-uterus-2018-license-and-caption-evidence.json'
  assert evidence.is_file()
  assets.append({'id':row['id'],'kind':row['kind'].replace('-','_'),'modality':row['modality'],'name':row['caption'],'local_path':'web/'+row['src'].removeprefix('/app/'),'sha256':row['sha256'],'investigation_ids':[INV],'structure_ids':[],'requirement_coverage':{},'reference_only':True,'representation':'complete_original_published_source_artwork_with_source_colour_profile','source_context':row['source_context'],'source':{'dataset':a['title'],'url':row['source_url'],'license':{'name':'CC BY 4.0','url':row['license_url'],'commercial_use':True,'redistribution':True,'review_status':'verified','reviewed_at':'2026-10-10','evidence_path':str(evidence.relative_to(ROOT)),'evidence_sha256':sha(evidence),'attribution':row['attribution']}},'presentation_dependencies':{'web/app.js':sha(ROOT/'web/app.js'),'data/radiology/radiology-open-images.json':sha(ROOT/'data/radiology/radiology-open-images.json')},'visual_review':{'status':'source_checked','sha256':row['sha256'],'reviewed_at':'2026-10-10','evidence_path':'docs/cervical-cancer-independent-source-review-20261010.json','basis':'Independent original encoded samples, ICC, author/caption and complete annotation preservation; all32 actual browser source-profile appearances match.'},'anatomical_review':{'status':'pending','reason':'Publication appearance, source names and licensed pixels do not approve every fine structure, histological tissue, clinical interpretation or patient registration.'},'limitations':row['limits']})
 p=ROOT/'data/radiology/radiology-asset-evidence.json';d=json.loads(p.read_text());d['assets']=[a for a in d['assets'] if not a['id'].startswith(PREFIX)]+assets
 # Refresh changed additive presentation registrations while keeping anatomical
 # approval and source bytes unchanged. Unknown unrelated dependencies stay held.
 changed=['web/lesson-models.js','web/spatial-models.js','web/spatial-module-objects.js','data/radiology/radiology-open-images.json','data/radiology/source-anatomy-references.json']
 for a in d['assets']:
  for f in changed:
   if f in a.get('presentation_dependencies',{}):assert a['anatomical_review']['status']=='pending';a['presentation_dependencies'][f]=sha(ROOT/f)
 d['updated_at']='2026-10-10';save(p,d)
 p=ROOT/'data/radiology/msk-asset-evidence.json';d=json.loads(p.read_text())
 for a in d['assets']:
  for f in ['web/lesson-models.js','web/spatial-models.js','web/spatial-module-objects.js']:
   if f in a.get('presentation_dependencies',{}):assert a['anatomical_review']['status']=='pending';a['presentation_dependencies'][f]=sha(ROOT/f)
 save(p,d)
 held=ROOT.parent/'cervical-held-legacy-20261010.json';save(REVIEW/'held-legacy-source-use.json',{'investigation':INV,'legacy_remote_images':json.loads(held.read_text()),'reason':'No independently recorded commercial redistribution grant; planning image was incorrectly used for stromal/parametrial invasion. Effective scoped key_images is explicitly empty. Other examinations in the shared lesson remain separately scoped.','clinical_approval':False})
 print('32 complete reviewed source figures bound to8cervical assessment areas; no anatomical or current-patient approval.')
if __name__=='__main__':integrate()
