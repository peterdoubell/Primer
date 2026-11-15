"""An OPL artist reference is not a POL or complete measured ligament volume."""
from pathlib import Path
import json,hashlib
from tools.check_msk_fidelity import requirements_for,inspect_binding,inspect_requirement_coverage
ROOT=Path(__file__).resolve().parents[1]
def test_native_opl_candidate_is_explicitly_partial_and_unapproved():
 asset=next(a for a in json.loads((ROOT/'data/radiology/msk-asset-evidence.json').read_text())['assets'] if a['id']=='za-joints-711785439')
 assert asset['structure_ids']==['knee.oblique_popliteal_ligament.course']
 assert asset['source_context']['laterality']=='right'
 assert asset['anatomical_review']['status']=='pending'
 assert 'artist' in asset['limitations'].lower() and 'measured' in asset['limitations'].lower()
 assert hashlib.sha256((ROOT/asset['local_path']).read_bytes()).hexdigest()==asset['sha256']
 requirements=json.loads((ROOT/'data/radiology/msk-structure-requirements.json').read_text());knee=next(i for i in requirements['investigations'] if i['investigation_id']=='ra.mri-knee');target=next(r for r in requirements_for(knee) if r['id']==asset['structure_ids'][0]);assert not inspect_binding(asset,target)
 assert inspect_requirement_coverage(asset,target)==['requirement_coverage_partial']
 assert not any('posterior_oblique' in target or 'attachments' in target for target in asset['structure_ids'])
 audit=json.loads((ROOT/'docs/msk-knee-ligament-volume-source-review/existing-opl-geometry-audit.json').read_text())
 assert audit['source']['read_now_from_reacquired_original_fbx'] is True
 assert audit['source']['native_positions']==186 and asset['geometry']['triangles']==368
