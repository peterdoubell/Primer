"""Procedure illustrations retain actual modality and partial anatomy scope."""
import copy
import hashlib
import json
from pathlib import Path
from PIL import Image
from primer.radiology_catalog import _structure_atlases
from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage, requirements_for
ROOT = Path(__file__).resolve().parents[1]


def test_injection_references_keep_native_pixels_and_selected_ultrasound_panels():
    images = _structure_atlases()['ra.ultrasound-joint-injection']
    assets = json.loads((ROOT/'data/radiology/msk-asset-evidence.json').read_text())['assets']
    specification = json.loads((ROOT/'data/radiology/msk-structure-requirements.json').read_text())
    inv = next(i for i in specification['investigations'] if i['investigation_id']=='ra.ultrasound-joint-injection')
    leaves = {r['id']: r for r in requirements_for(inv)}
    assert len(leaves)==75
    for number, panels, size in [(8,['d'],(1500,1066)),(10,['b'],(1500,480))]:
        identifier = f'open-injection-patel-fig{number}'
        image = next(i for i in images if i['id']==identifier)
        asset = next(a for a in assets if a['id']==identifier)
        path = ROOT/asset['local_path']
        original = ROOT/'docs/msk-upper-injection-source-review'/path.name
        assert path.read_bytes()==original.read_bytes()
        assert hashlib.sha256(path.read_bytes()).hexdigest()==asset['sha256']==image['sha256']
        with Image.open(path) as im: assert im.size==size
        assert asset['representation_selection']['panels']==panels
        assert len(asset['structure_ids'])==2
        assert asset['anatomical_review']['status']=='pending'
        assert image['pixel_provenance']['independent_poppler_encoded_bytes_match']
        assert 'not an actual needle' in image['limits']
        for identifier in asset['structure_ids']:
            assert inspect_binding(asset,leaves[identifier])==[]
            assert inspect_requirement_coverage(asset,leaves[identifier])==['requirement_coverage_partial']
        wrong = copy.deepcopy(asset)
        wrong['representation_selection']['panels']=['a']
        wrong['source_context']['selected_panels']=['a']
        assert 'source_context_panel_type_invalid' in inspect_binding(wrong,leaves[asset['structure_ids'][0]])
