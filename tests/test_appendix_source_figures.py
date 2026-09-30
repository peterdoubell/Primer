import copy
import hashlib
import json
from pathlib import Path

from primer.radiology_catalog import _structure_atlases
from tools.check_msk_fidelity import inspect_binding,inspect_requirement_coverage,requirements_for

ROOT=Path(__file__).resolve().parents[1]

def records():
    assets={a['id']:a for a in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']}
    inv=json.loads((ROOT/'data/radiology/non-msk-structure-requirements.json').read_text())['investigations'][0]
    return assets,{r['id']:r for r in requirements_for(inv)}


def test_appendix_figures_are_byte_bound_and_do_not_claim_complete_anatomy():
    assets,leaves=records();images=_structure_atlases()['ra.appendicitis']
    assert len(images)==3
    for image in images:
        asset=assets[image['id']];raw=(ROOT/asset['local_path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==image['sha256']==asset['sha256']
        assert image['license']=='CC BY 4.0'
        assert 'NLM/PMC' in image['attribution']
        assert asset['anatomical_review']['status']=='pending'
        for target in asset['structure_ids']:
            assert not inspect_binding(asset,leaves[target])
            assert inspect_requirement_coverage(asset,leaves[target])==['requirement_coverage_partial']
        assert not any('submucosa' in t or 'perforation' in t or 'tip' in t for t in asset['structure_ids'])


def test_normality_and_mixed_panel_modality_do_not_transfer():
    assets,leaves=records();normal=assets['open-appendix-mostbeck-2016-fig1']
    assert 'source_context_purpose_mismatch' in inspect_binding(normal,leaves['abdomen.appendiceal_perforation.wall_defect'])
    ct=copy.deepcopy(assets['open-appendix-mostbeck-2016-fig3'])
    assert ct['structure_ids']==[]
    assert ct['source_context']['population']=={'life_stage':'adult','age_years':45,'sex':'male'}
    ct['source_context']['selected_panels']=['a'];ct['representation_selection']['panels']=['a']
    assert any('modality' in i for i in inspect_binding(ct,leaves['abdomen.appendix.outer_wall_boundary']))
    assert normal['source_context']['population']['life_stage']=='not_reported'
