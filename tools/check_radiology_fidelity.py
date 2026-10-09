#!/usr/bin/env python3
"""Audit the complete radiology scope without treating UI presence as fidelity."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from primer.curriculum import Curriculum
from primer import radiology_catalog
from tools.check_msk_fidelity import audit, validate_reporting_snapshots
from tools.msk_runtime_rights import reference_images, audit_reference_image_rights


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def additional_requirements():
    path=ROOT/'data/radiology/non-msk-structure-requirements.json'
    return json.loads(path.read_text()) if path.exists() else None


def build_scope(curriculum=None):
    curriculum = curriculum or Curriculum()
    catalog = radiology_catalog.catalogue()
    requirements = json.loads((ROOT/'data/radiology/msk-structure-requirements.json').read_text())
    known = {i['investigation_id'] for i in requirements['investigations']}
    additional=additional_requirements()
    expanded={i['investigation_id']:i for i in additional['investigations']} if additional else {}
    inventory_hash=digest(requirements)
    additional_hash=digest(additional) if additional else None
    extras = {i['module_id']:i for i in requirements['additional_scope']}
    investigations = []
    for item in catalog['investigations']:
        ref = radiology_catalog.detail(curriculum,item)['radiology_reference']
        contract = {k:ref.get(k) for k in ('reporting','report_templates','walkthrough','reading')}
        if item['id'] in expanded and expanded[item['id']]['source_contract_sha256'] != digest(contract):
            raise ValueError('Additional structure inventory has a stale reporting contract: '+item['id'])
        investigations.append(dict(
            id=item['id'],title=item['title'],section=item['section'],module_id=item['module_id'],
            modality=item['modality'],reporting_contract=contract,reporting_contract_sha256=digest(contract),
            structure_inventory=('data/radiology/msk-structure-requirements.json' if item['id'] in known else 'data/radiology/non-msk-structure-requirements.json' if item['id'] in expanded else None),
            structure_inventory_sha256=inventory_hash if item['id'] in known else additional_hash if item['id'] in expanded else None,
            structure_expansion_status='draft_inventory_exists' if item['id'] in known or item['id'] in expanded else 'required_not_yet_expanded',
            observed_visual_descriptors={k:ref.get(k) for k in ('key_images','structure_atlas','anatomical_illustrations','spatial_model','source_anatomy_references','source_motion_references','source_study_references')},
            clinical_approval=False))
    modules = []
    for node in sorted(curriculum.nodes.values(),key=lambda n:n['id']):
        if node.get('domain') != 'radiology':
            continue
        contract = {k:node.get(k) for k in ('goal','learning_outcomes','lesson','reference','radiology_reference','visual_spec','lesson_media','model_family','model_context','practice','quiz','kid_text')}
        linked = [i['id'] for i in investigations if i['module_id']==node['id']]
        modules.append(dict(id=node['id'],title=node['title'],stage=node['stage'],section=node.get('section'),
                            investigation_ids=linked,has_reporting_reference=bool(node.get('radiology_reference')),
                            module_contract=contract,module_contract_sha256=digest(contract),
                            existing_msk_scope_note=extras.get(node['id']),
                            reconciliation_status='requires_explicit_module_review',clinical_approval=False))
    return dict(schema_version=1,objective_scope='all_radiology_modules',
                scope_note='Includes every source-catalogue investigation and every radiology curriculum node. Unmapped and foundational nodes are retained for explicit review.',
                presence_is_not_clinical_fidelity=True,investigations=investigations,curriculum_modules=modules)


def validate_scope(saved,current):
    for key,field in [('investigations','reporting_contract_sha256'),('curriculum_modules','module_contract_sha256')]:
        old,new=saved[key],current[key]
        if len({r['id'] for r in old})!=len(old) or {r['id'] for r in old}!={r['id'] for r in new}:
            raise ValueError('Incomplete or duplicate radiology scope: '+key)
        by_id={r['id']:r for r in new}
        for row in old:
            contract_key='reporting_contract' if key=='investigations' else 'module_contract'
            if row[field]!=digest(row[contract_key]) or row[field]!=by_id[row['id']][field]:
                raise ValueError('Stale reporting contract: '+row['id'])
            if row != by_id[row['id']]:
                raise ValueError('Scope metadata or visual descriptors changed: '+row['id'])


def build_report(scope,curriculum=None):
    curriculum=curriculum or Curriculum()
    validate_scope(scope,build_scope(curriculum))
    data=ROOT/'data/radiology'
    requirements=json.loads((data/'msk-structure-requirements.json').read_text())
    evidence=json.loads((data/'msk-asset-evidence.json').read_text())
    extra_path=data/'radiology-asset-evidence.json'
    extra_evidence=json.loads(extra_path.read_text()) if extra_path.exists() else {'assets':[]}
    all_evidence={'assets':evidence['assets']+extra_evidence['assets'],'reference_rights_assets':extra_evidence.get('reference_rights_assets',[])}
    if len({a['id'] for a in all_evidence['assets']}) != len(all_evidence['assets']):
        raise ValueError('Repeated asset identifier across radiology evidence inventories')
    catalog=radiology_catalog.catalogue()
    expected_msk={i['id'] for i in catalog['investigations'] if i['section']=='Musculoskeletal'}
    reporting={i['id']:radiology_catalog.detail(curriculum,i)['radiology_reference']['reporting']
               for i in catalog['investigations'] if i['id'] in expected_msk}
    validate_reporting_snapshots(requirements,reporting)
    msk=audit(requirements,evidence,expected_catalog_ids=expected_msk,
              runtime_images=reference_images(curriculum,catalog,requirements,radiology_catalog.detail))
    additional=additional_requirements()
    extra_report=None
    if additional:
        ids={i['investigation_id'] for i in additional['investigations']}
        authoritative={i['id'] for i in catalog['investigations'] if i['section']!='Musculoskeletal'}
        if not ids <= authoritative:
            raise ValueError('Additional inventory names an unknown or duplicate MSK investigation')
        guides={i['id']:radiology_catalog.detail(curriculum,i)['radiology_reference']['reporting']
                for i in catalog['investigations'] if i['id'] in ids}
        validate_reporting_snapshots(additional,guides)
        candidate_evidence={'assets':[a for a in all_evidence['assets'] if ids.intersection(a.get('investigation_ids',[]))]}
        extra_report=audit(additional,candidate_evidence,expected_catalog_ids=ids)
    all_images=reference_images(curriculum,catalog,
        {'additional_scope':[{'module_id':m['id']} for m in scope['curriculum_modules']]},
        radiology_catalog.detail,catalog_section=None)
    rights=audit_reference_image_rights(all_images,all_evidence,ROOT)
    unexpanded=[r['id'] for r in scope['investigations'] if not r['structure_inventory']]
    modules=[m['id'] for m in scope['curriculum_modules'] if m['reconciliation_status']!='verified']
    return dict(objective_scope='all_radiology_modules',clinical_commercial_ready=False,
                investigation_count=len(scope['investigations']),curriculum_node_count=len(scope['curriculum_modules']),
                sections=dict(sorted(Counter(i['section'] for i in scope['investigations']).items())),
                investigations_requiring_structure_expansion=unexpanded,curriculum_surfaces_requiring_reconciliation=modules,
                known_representation_requirements=msk['representation_requirements']+(extra_report['representation_requirements'] if extra_report else 0),
                total_representation_requirements=None,
                total_count_note='Unknown until all investigations and curriculum surfaces are expanded; unknown requirements are not zero.',
                msk_subaudit={k:msk[k] for k in ('clinical_commercial_ready','representation_requirements','counts','scope_gaps')},
                additional_structure_audit=extra_report,
                runtime_reference_image_rights=rights,
                limitations=['MSK evidence is a subaudit, not all-radiology approval.',
                             'Visual descriptors and complete walkthroughs do not establish anatomical fidelity.',
                             'Other lesson media, procedural models and schematic/code geometry still require explicit evidence inventories.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-scope',type=Path)
    parser.add_argument('--scope',type=Path,default=ROOT/'docs/radiology-fidelity-scope.json')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--require-complete',action='store_true')
    args=parser.parse_args()
    current=build_scope()
    if args.write_scope:
        args.write_scope.write_text(json.dumps(current,indent=2)+'\n')
    scope=json.loads(args.scope.read_text()) if args.scope.exists() else current
    report=build_report(scope)
    if args.output:args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(f"{report['investigation_count']} investigations; {report['curriculum_node_count']} curriculum nodes")
    print(f"Unexpanded investigations: {len(report['investigations_requiring_structure_expansion'])}; full clinical/commercial readiness NOT ESTABLISHED")
    raise SystemExit(1 if args.require_complete and not report['clinical_commercial_ready'] else 0)


if __name__=='__main__':main()
