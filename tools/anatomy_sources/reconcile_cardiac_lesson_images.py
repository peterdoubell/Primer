#!/usr/bin/env python3
"""Bind reviewed original figures to existing lesson slots without filling patient findings."""
import hashlib,json
from pathlib import Path
from tools.anatomy_sources.package_aortic_rupture_figures import append_evidence
ROOT=Path(__file__).resolve().parents[2];MODULE='rad.5.cardiac-masses-devices';OUT=ROOT/'docs/cardiac-lesson-media-review'
SLOTS={1:'open-cardiac-mimic-pmc10818366-fig20',2:'open-cardiac-mimic-pmc10818366-fig22',3:'open-cardiac-support-pmc10350447-fig9'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def replace_entry(path,key,node):
    raw=path.read_text();start=raw.index('{',raw.index('"'+key+'"'));_,end=json.JSONDecoder().raw_decode(raw,start);path.write_text(raw[:start]+json.dumps(node,indent=2,ensure_ascii=False).replace('\n','\n  ')+raw[end:])
def reconcile():
    OUT.mkdir(parents=True,exist_ok=True);atlases=json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text());allrows={r['id']:r for rows in atlases.values() for r in rows};evidence=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text());allassets={a['id']:a for a in evidence['assets']};registry_path=ROOT/'data/radiology/local-source-figures.json';registry=json.loads(registry_path.read_text());catalog_path=ROOT/'data/radiology/key-images-foundations-body.json';catalog=json.loads(catalog_path.read_text());records=[];assets=[]
    for slot,source_id in SLOTS.items():
        row=allrows[source_id];source_asset=allassets[source_id];id=f'cardiac-masses-devices-image-{slot}';target=f'web/reference-media/source-figures/cardiac-lesson-slot-{slot}.jpg';src='/app/'+target.removeprefix('web/');raw=(ROOT/source_asset['local_path']).read_bytes()
        if sha(raw)!=row['sha256'] or sha(raw)!=source_asset['sha256']:raise ValueError('Reviewed original figure changed')
        path=ROOT/target;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        caption=row['caption']+' Independent source case example for this report slot; it does not supply findings for the examination being reported. No registration between the three teaching cases is inferred.'
        value={'src':src,'sha256':row['sha256'],'alt':caption,'caption':caption,'source_url':row['source_url'],'source_title':source_asset['name'],
            'attribution':row['attribution'],'image_type':'clinical','reviewed_at':'2026-10-06','width':row['width'],'height':row['height'],
            'license':row['license'],'license_url':row['license_url'],'clinical_panels':row['clinical_panels'],'source_context':row['source_context'],
            'ancillary_panels':row.get('ancillary_panels',[]),'limits':row['limits'],'source_figure_id':source_id}
        previous=catalog[id];replace_entry(catalog_path,id,value)
        registry[src]={'sha256':row['sha256'],'source_url':row['source_url'],'original_asset_url':row['asset_source_url'],'license':row['license'],'license_url':row['license_url'],'attribution':row['attribution'],'review_evidence':'docs/cardiac-lesson-media-review.md','width':row['width'],'height':row['height'],'bytes':len(raw)}
        records.append({'slot_id':id,'source_figure_id':source_id,'local_path':target,'sha256':sha(raw),'previous_asset':previous,'report_slot_identity_changed':False})
        assets.append({'id':'cardiac-lesson-slot-'+str(slot),'kind':'clinical_image','name':'Cardiac lesson independent example '+str(slot),'local_path':target,'sha256':row['sha256'],'modality':row['modality'],'module_ids':[MODULE],'investigation_ids':[],'structure_ids':[],'requirement_coverage':{},'source':source_asset['source'],'source_context':row['source_context'],'pixel_provenance':source_asset['pixel_provenance'],'anatomical_review':{'status':'pending','reason':'Independent source cases do not establish complete shared mass/device lesson anatomy or clinical function.'}})
    registry_path.write_text(json.dumps(registry,indent=2,ensure_ascii=False)+'\n');append_evidence(ROOT/'data/radiology/radiology-asset-evidence.json',assets,prefix='cardiac-lesson-slot-')
    path=ROOT/'data/radiology/supplemental-sources.json';supp=json.loads(path.read_text())
    for title,url in [('Cardiac masses and pseudomasses: original multimodality figure examples','https://pmc.ncbi.nlm.nih.gov/articles/PMC10818366/'),('Mechanical support imaging: original device complication example','https://pmc.ncbi.nlm.nih.gov/articles/PMC10350447/')]:
        if not any(r['module_id']==MODULE and r['url']==url for r in supp):supp.append({'module_id':MODULE,'title':title,'url':url,'reviewed_at':'2026-10-06'})
    path.write_text(json.dumps(supp,indent=2,ensure_ascii=False)+'\n')
    report_path=OUT/'original-slot-reconciliation.json'
    if report_path.exists():
        old=json.loads(report_path.read_text());prior={r['slot_id']:r['previous_asset'] for r in old['slots']}
        for r in records:r['previous_asset']=prior[r['slot_id']]
    report_path.write_text(json.dumps({'module_id':MODULE,'slots':records,'source_pixels_changed':False,'patient_findings_prefilled':False,'cases_registered_together':False,'full_curriculum_scope_reconciled':False,'clinical_approval':False},indent=2)+'\n')
    print('Three existing lesson slots now use reviewed original figures; prompt identity and patient findings unchanged.')
if __name__=='__main__':reconcile()
