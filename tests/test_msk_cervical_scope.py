import json
from pathlib import Path
from tools.check_msk_fidelity import requirements_for, inspect_binding
ROOT=Path(__file__).resolve().parents[1]


def test_cervical_ligaments_add_scope_without_replacing_generic_sites():
    r=json.loads((ROOT/'data/radiology/msk-structure-requirements.json').read_text())
    inv=next(i for i in r['investigations'] if i['investigation_id']=='ra.arthritis')
    proof=json.loads((ROOT/'docs/msk-craniocervical-mri-review/scope-extension.json').read_text())
    assert set(proof['original_structure_ids'])<=set(s['id'] for s in inv['structures'])
    assert inv['expansion_rules']
    assert inv.get('site_expansion_review',{}).get('status')!='approved'
    leaves={x['id']:x for x in requirements_for(inv)}
    assert len(proof['added_leaf_ids'])==9
    for identifier in proof['added_leaf_ids']:
        leaf=leaves[identifier]
        assert leaf['modality_scope']==['MRI']
        assert 'When cervical MRI is acquired' in leaf['condition']
        assert 'clinical_image_modality_not_in_requirement_scope' in inspect_binding({'kind':'clinical_image','modality':'Radiography'},leaf)
    parents={s['id']:s for s in inv['structures']}
    assert parents['arthritis.cervical.left_alar_ligament']['laterality']=='left'
    assert parents['arthritis.cervical.right_alar_ligament']['laterality']=='right'
    assert all(parents[x]['clinical_validation_status']=='draft_requires_msk_radiologist_review' for x in proof['added_structure_ids'])
    assert 'pattern_not_one_joint' in {x['code'] for x in inv['source_scope_issues']}


def test_cervical_figure_is_local_mri_not_complete_or_side_specific_coverage():
    import hashlib
    from tools.check_msk_fidelity import inspect_requirement_coverage
    from primer.radiology_catalog import _structure_atlases
    image=_structure_atlases()['ra.arthritis'][0]
    assets=json.loads((ROOT/'data/radiology/msk-asset-evidence.json').read_text())['assets']
    asset=next(a for a in assets if a['id']==image['id'])
    target='arthritis.cervical.transverse_atlantal_ligament.visible_course'
    assert asset['structure_ids']==[target]
    assert asset['source_context']['population']['life_stage']=='unknown'
    assert asset['anatomical_review']['status']=='pending'
    assert inspect_requirement_coverage(asset,{'id':target})==['requirement_coverage_partial']
    path=ROOT/asset['local_path']
    assert path.read_bytes()==(ROOT/'docs/msk-craniocervical-mri-review'/path.name).read_bytes()
    assert hashlib.sha256(path.read_bytes()).hexdigest()==image['sha256']==asset['sha256']
    assert (image['width'],image['height'])==(769,563)
    assert image['modality']=='MRI'
