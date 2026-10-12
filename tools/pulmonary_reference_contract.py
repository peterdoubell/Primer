"""Offline checks for the one reviewed native pulmonary source companion."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE = 'ra.ct-pulmonary-nodules'
NODE = 'rad.4.pulmonary-nodule'


def assert_native_pulmonary_reference(reference):
    from primer.pulmonary_native_inspectors import references
    expected = references()[CASE]
    assert reference.get('source_native_only') is True
    assert reference.get('source_native_inspectors') == expected and len(expected) == 1
    inspector = expected[0]
    assert inspector['investigation_id'] == CASE and inspector['module_id'] == NODE
    assert inspector['id'] == 'lidc-idri-0525-native' and inspector['license'] == 'CC BY 3.0'
    assert reference['key_images'] == [] and reference.get('structure_atlas', []) == []
    for key in ('clinical_approval', 'fine_anatomical_approval', 'structure_coverage_granted',
                'current_patient_registration', 'whole_goal_complete'):
        assert inspector[key] is False
    raw = (ROOT / 'web/anatomy/lidc-idri-0525/manifest.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == inspector['manifest_sha256']
    manifest = json.loads(raw)
    assert manifest['ct']['shape'] == [512, 512, 429]
    assert manifest['ct']['source_samples'] == 112459776 and len(manifest['ct']['chunks']) == 7
    assert len(manifest['annotations']) == 8 and len(manifest['xml_marks']) == 33
    assert all(row['mesh']['triangles'] > 0 and row['source_samples'] > 0
               for row in manifest['annotations'])
    proof_raw = (ROOT / 'docs/pulmonary-release-integration-review-20261012/current-pulmonary-reader-HTTPS/proof.json').read_bytes()
    assert hashlib.sha256(proof_raw).hexdigest() == '7ddd1bead3ff62b534fa60ca8cbff2a3e7c4345621abfc4b12f59e2647a45c08'
    proof = json.loads(proof_raw)
    assert {(row['width'], row['route']) for row in proof['rows']} == {
        (1440, 'radiology'), (1440, 'node'), (390, 'radiology'), (390, 'node')}
    for row in proof['rows']:
        assert not row['errors']
        assert all(len(sample['planes']) == 3 for sample in row['original_source_planes'])
        assert len(row['full_GPU_models']) == 8 and len(row['all_original_XML_mark_selections']) == 33
    model = reference['spatial_model']
    assert model['source_native_only'] is True and model['family'] == 'thorax'
    assert model['id'] == 'radiology-model-' + NODE
    assert model['scenario'] == 'radiology-reference:' + NODE and model['focus'] == ['native-source']
    walk = reference.get('walkthrough')
    if walk:
        assert walk['spatial_model']['source_native_only'] is True
        assert all(step['landmark'] == 'native-source' and step['parts'] == [] and step['images'] == []
                   for step in walk['steps'])
    return inspector
