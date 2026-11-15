#!/usr/bin/env python3
"""Reuse exact reviewed source artwork in acute-abdomen steps with unchanged context and no coverage credit."""
import copy
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
SELECTION={
 'ra.appendicitis':['open-appendix-mostbeck-2016-fig1','open-appendix-mostbeck-2016-fig2','open-appendix-mostbeck-2016-fig3'],
 'ra.ct-bowel-wall':['open-bowel-wall-pmc3999365-fig6','open-bowel-wall-pmc3999365-fig9'],
 'ra.ct-bowel-obstruction':['open-bowel-obstruction-pmc4729712-fig2','open-bowel-obstruction-pmc4729712-fig7'],
 'ra.ct-pancreatitis':['open-pancreatitis-sureka-2015-fig1'],
 'ra.ultrasound-gallbladder':['open-gallbladder-pmc12181115-fig1'],
 'ra.ultrasound-bile-duct-stones':['open-cbd-stone-pmc12017295-fig1','open-cbd-stone-pmc12463306-fig1','open-cbd-stone-pmc12463306-fig3'],
}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def package():
    images_path=ROOT/'data/radiology/radiology-open-images.json';assets_path=ROOT/'data/radiology/radiology-asset-evidence.json'
    images=json.loads(images_path.read_text());evidence=json.loads(assets_path.read_text());by_id={r['id']:r for r in evidence['assets']}
    rows,assets,proof=[],[],[]
    for investigation,ids in SELECTION.items():
        original={r['id']:r for r in images[investigation]}
        for ident in ids:
            source=original[ident];asset=by_id[ident];local=(ROOT/'web'/source['src'].removeprefix('/app/')).resolve()
            if (not local.is_relative_to(ROOT/'web/reference-media') or hashlib.sha256(local.read_bytes()).hexdigest()!=source['sha256']
                    or asset['sha256']!=source['sha256'] or asset['source']['license']['review_status']!='verified'
                    or not asset['source']['license']['commercial_use'] or not asset['source']['license']['redistribution']
                    or asset['anatomical_review']['status']!='pending'):
                raise ValueError('Original source/rights/unapproved scope differs: '+ident)
            license_evidence=ROOT/asset['source']['license']['evidence_path']
            if hashlib.sha256(license_evidence.read_bytes()).hexdigest()!=asset['source']['license']['evidence_sha256']:
                raise ValueError('Original license evidence changed')
            target_id='open-acute-abdomen-ref-'+ident.removeprefix('open-')
            row=copy.deepcopy(source);row['id']=target_id
            row['source_reuse']={'original_asset_id':ident,'original_investigation_id':investigation,'original_source_record_sha256':digest(source),
                                 'same_physical_file':True,'source_pixels_or_context_changed':False,'shared_patient_or_exam_inferred':False,'structure_coverage_granted':False}
            candidate=copy.deepcopy(asset);candidate['id']=target_id;candidate['investigation_ids']=['ra.acute-abdomen']
            candidate['structure_ids']=[];candidate['requirement_coverage']={}
            candidate['source_reuse']=copy.deepcopy(row['source_reuse'])
            rows.append(row);assets.append(candidate)
            proof.append({'id':target_id,'original_asset_id':ident,'original_investigation_id':investigation,'original_source_record_sha256':digest(source),
                          'local_path':str(local.relative_to(ROOT)),'sha256':source['sha256'],'modality':source['modality'],
                          'source_context_sha256':digest(source.get('source_context')),'original_asset_context_sha256':digest(asset.get('source_context')),
                          'original_binding_metadata_sha256':digest({'structure_ids':asset['structure_ids'],'requirement_coverage':asset['requirement_coverage']}),
                          'license':source['license'],'license_url':source['license_url'],'clinical_approval':False,'structure_coverage_granted':False})
    ids={r['id'] for r in rows}
    images['ra.acute-abdomen']=[r for r in images.get('ra.acute-abdomen',[]) if r['id'] not in ids]+rows
    images_path.write_text(json.dumps(images,indent=2,ensure_ascii=False)+'\n')
    # Preserve unrelated source-evidence text rather than rewriting that corpus.
    raw=assets_path.read_text();start=raw.index('[',raw.index('"assets"'))+1;cursor=start;retained=[];decoder=json.JSONDecoder()
    while True:
        cursor+=len(re.match(r'\s*',raw[cursor:]).group())
        if raw[cursor]==']':break
        record,end=decoder.raw_decode(raw,cursor)
        if record['id'] not in ids:retained.append(raw[cursor:end])
        cursor=end+len(re.match(r'\s*',raw[end:]).group())
        if raw[cursor]==',':cursor+=1
    retained.extend(json.dumps(r,indent=2,ensure_ascii=False).replace('\n','\n    ') for r in assets)
    assets_path.write_text(raw[:start]+'\n    '+',\n    '.join(retained)+'\n  '+raw[cursor:])
    out=ROOT/'docs/acute-abdomen-reused-source-review';out.mkdir(exist_ok=True)
    (out/'source-reuse-evidence.json').write_text(json.dumps({'target_investigation_id':'ra.acute-abdomen','figures':proof,
        'new_physical_image_files_created':False,'normal_sources_relabelled_as_pathology':False,
        'patient_or_modality_correspondence_inferred':False,'clinical_approval':False,'structure_coverage_granted':False},indent=2)+'\n')
    print('Reused twelve exact source figures with preserved context and no coverage grants.')


if __name__=='__main__':
    package()
