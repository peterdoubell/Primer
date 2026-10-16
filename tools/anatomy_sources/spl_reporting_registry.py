"""Pin the current reporting viewer after exact source and standalone validation."""
from pathlib import Path
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[2]
ASSETS=ROOT/'web/anatomy/spl-nac-reporting'
DOCS=ROOT/'docs/spl-reporting-source-review-20261016'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def build():
    manifest=json.loads((ASSETS/'manifest.json').read_bytes());source=json.loads((DOCS/'current-source-verification.json').read_bytes())
    browser=json.loads((DOCS/'viewer/standalone-proof.json').read_bytes())
    assert source['allPassed'] and source['sourceClasses']==217 and source['manifestSHA256']==sha((ASSETS/'manifest.json').read_bytes())
    assert browser['allPassed'] and browser.get('everyClassHasSelectedOverlayInBothContrastsAndThreePlanes') is True and not browser['errors'] and all(len(row['meshes'])==217 for row in browser['gpu'])
    for name,pin in browser['sourcePins'].items():assert sha((ASSETS/name).read_bytes())==pin,name
    review={'schema_version':1,'source_class_count':217,'additional_source_classes':205,'generated_boundary_payload_sets':207,'shared_boundary_payload_sets':10,
            'source_verification_sha256':sha((DOCS/'current-source-verification.json').read_bytes()),'standalone_proof_sha256':sha((DOCS/'viewer/standalone-proof.json').read_bytes()),
            'native_pixel_cases':len(browser['pixels']),'native_pixels':sum(row['pixels'] for row in browser['pixels']),
            'source_components_inspected':len(browser['components']),'source_commit':manifest['sourceCommit'],
            'clinical_approval':False,'complete_reporting_anatomy_approved':False,'whole_goal_complete':False}
    (DOCS/'source-review.json').write_text(json.dumps(review,indent=2)+'\n')
    old=json.loads((ROOT/'data/radiology/spl-limbic-reference.json').read_bytes())['inspectors']['spl-nac-limbic-native-reference']
    identifier='spl-nac-reporting-native-reference';prefix='/app/anatomy/spl-nac-reporting/'
    files={p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(ASSETS.iterdir()) if p.is_file()}
    assert len(files)==418
    item={**old,'id':identifier,'title':'Brain reporting relationships in native MRI and exact source boundaries','src':prefix+'index.html','manifest_url':prefix+'manifest.json',
          'sha256':files['index.html']['sha256'],'manifest_sha256':files['manifest.json']['sha256'],'modality':'Native T1/T2 MRI and grouped brain source-label boundaries',
          'caption':'Explore 217 source classes in thirteen relationship groups, with 205 additions to the earlier twelve-structure reference. Locate each class in native axial, coronal and sagittal T1/T2, compare source objects, and inspect retained small components. Exact categorical-cell geometry preserves the source; missing capsule limbs, separate callosal segments, cisterns, vascular territories and unacquired sulcal curves remain explicit. This single-subject source does not establish diagnostic accuracy or complete reporting anatomy.',
          'attribution':old['attribution'].split(' Original MRI/label')[0]+' Original native MRI and categorical label samples are retained. Primer’s marked adaptation derives exact label-cell boundaries and adds grouped native-image relationship controls, preserving source components without fitted registration or cleanup. Full original source notices and licensing terms accompany the reference.',
          'bound_source_ids':[identifier],
          'source_grain':{'kind':'single-subject anatomical research atlas','subject_count':1,'MRI':'native 0.75 mm T1/T2','categorical_labels':'separate native 1 mm Int16 grid','selected_label_classes':217,'additional_source_classes':205,'generated_boundary_payload_sets':207,'reused_boundary_payload_sets':10,'default_surface':'exact categorical voxel-cell boundaries','separately_labelled_CA_fields_or_subiculum':False}}
    registry={'schema_version':1,'source_repository':'https://github.com/mhalle/spl-brain-atlas','source_commit':manifest['sourceCommit'],'source_review_sha256':sha((DOCS/'source-review.json').read_bytes()),
              'source_class_count':217,'additional_source_class_count':205,'generated_boundary_payload_sets':207,'shared_boundary_payload_sets':10,
              'bindings':{'ra.brain-anatomy':[identifier]},'inspectors':{identifier:item},'files':files}
    destination=ROOT/'data/radiology/spl-reporting-reference.json';destination.write_text(json.dumps(registry,indent=2)+'\n')
    module=ROOT/'primer/spl_reporting_reference.py';text=module.read_text();text,n=re.subn(r"REGISTRY_SHA256='(?:PENDING|[a-f0-9]{64})'","REGISTRY_SHA256='"+sha(destination.read_bytes())+"'",text);assert n==1;module.write_text(text)
    print(json.dumps({'registrySHA256':sha(destination.read_bytes()),'files':len(files),'classes':217,'additionalClasses':205}))
if __name__=='__main__':build()
