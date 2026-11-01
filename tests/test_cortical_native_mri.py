"""Linked native MRI evidence, without anatomical or clinical approval transfer."""
from pathlib import Path
import copy
import hashlib
import json
import pytest
from tools.cortical_mri_runtime_compatibility import reviewed, before_mri_bytes, before_mri_reference_fields
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs/cortical-native-mri-review-20261101'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
load = lambda name: json.loads((DOCS / name).read_bytes())

def test_native_anchor_samples_are_bound_to_original_sources():
    proof = load('anchor-proof.json')
    assert proof['allPassed'] and proof['allSamplesAndLabelsExact']
    assert proof['sourcePairs'] == proof['sourceAdjacencies'] == 77
    assert proof['originalMRISamplesVerified'] == len(proof['checks']) == 308
    assert not proof['sourceResampled'] and not proof['clinicalApproval'] and not proof['anatomicalVisibilityVerified']
    for name, digest in proof['sourceSHA256'].items():
        assert sha((ROOT / name).read_bytes()) == digest, name


def test_current_reader_and_navigation_match_original_native_pixels():
    for name, states, pixels, crosshairs in [('mri-pixel-proof.json', 616, 269344768, 3696),
                                            ('mri-navigation-pixel-proof.json', 192, 83951616, 1152)]:
        proof = load(name)
        assert proof['allPassed'] and proof['states'] == states
        assert proof['actualCanvasPixelsCompared'] == pixels and proof['crosshairLocationsChecked'] == crosshairs
        assert not proof['sourceSamplesResampled'] and not proof['anatomicalVisibilityVerified'] and not proof['clinicalApproval']
    reader = load('mri-reader-browser-proof.json')
    assert reader['allPassed'] and reader['cases'] == 616
    assert reader['meshDeliveryFixture'] and not reader['realHostedBrowserDeliveryVerified']
    headed = load('headed-browser-proof.json')
    assert headed['allPassed'] and not headed['meshFixture']
    assert headed['sourceReadback']['status'] == 200 and headed['sourceReadback']['bytes'] == 3105294
    assert headed['sourceReadback']['sha256'] == '489336496765b14873dfcb788e62301be573e795918837cc51c4ee8d7fce87fa'
    assert headed['viewer']['returnedNativeVoxel'] == headed['viewer']['nativeVoxel'] == [248,168,106]
    assert not headed['clinicalApproval'] and not headed['wholeGoalComplete']
    navigation = load('mri-navigation-browser-proof.json')
    assert navigation['allPassed'] and navigation['cases'] == 192 and navigation['sourceAnchorResets'] == 208
    lifecycle = load('mri-lifecycle-proof.json')
    assert lifecycle['allPassed'] and len(lifecycle['cases']) == 6
    assert {(row['width'], row['scenario']) for row in lifecycle['cases']} == {
        (width, scenario) for width in [390, 1440] for scenario in ['late-response', 'clear-selection', 'corrupt-and-retry']}
    index = load('evidence-index.json')
    assert index['clinicalApproval'] is False and index['wholeGoalComplete'] is False
    for name, digest in index['sourceSHA256'].items():
        assert sha((ROOT / name).read_bytes()) == digest, name
    for name, digest in index['proofSHA256'].items():
        assert sha((DOCS / name).read_bytes()) == digest, name


def test_actual_lessons_render_current_mri_and_restore_initial_state():
    proof = load('lesson/proof.json')
    assert proof['allPassed'] and proof['syntheticLoopback'] and not proof['productionLearnerWrites']
    assert not proof['errors'] and not proof['clinicalApproval']
    assert proof['meshDeliveryFixture'] and not proof['realHostedBrowserDeliveryVerified']
    assert len(proof['mounts']) == 4 and len(proof['mriCases']) == 332
    assert {(row['width'], row['identifier']) for row in proof['mounts']} == {
        (width, identifier) for width in [390, 1440] for identifier in ['ra.brain-anatomy', 'ra.mri-epilepsy']}
    assert sum(len(row['states']) for row in proof['mounts']) == 308
    assert all(row['allSourceGPUBytesMatched'] and row['reopened'] for row in proof['mounts'])
    assert len(proof['responses']) == 8 and all(row['status'] == 200 for row in proof['responses'])
    for name, digest in proof['sourceSHA256'].items():
        assert sha((ROOT / name).read_bytes()) == digest, name
    pixels = load('lesson/mri-pixel-proof.json')
    assert pixels['allPassed'] and pixels['states'] == 332 and pixels['crosshairLocationsChecked'] == 1992
    assert not pixels['sourceSamplesResampled'] and not pixels['clinicalApproval']


def test_exact_mri_reversal_cannot_extend_historical_approval():
    proof = reviewed()
    for name, row in proof['files'].items():
        raw = (ROOT / name).read_bytes(); original = before_mri_bytes(name, raw)
        assert sha(original) == row['before_sha256']
        assert before_mri_bytes(name, original) == original
        with pytest.raises(ValueError):
            before_mri_bytes(name, raw + b'foreign edit')
    for identifier in proof['bindings']:
        fields = {'source_native_inspectors': [proof['after_inspector']]}
        assert before_mri_reference_fields(identifier, fields) == {'source_native_inspectors': [proof['before_inspector']]}
        for key in ['clinical_approval', 'fine_anatomical_approval', 'current_patient_registration', 'normal_anatomical_atlas_approval', 'complete_reporting_anatomy_approved']:
            changed = copy.deepcopy(fields); changed['source_native_inspectors'][0][key] = True
            with pytest.raises(ValueError):
                before_mri_reference_fields(identifier, changed)
        with pytest.raises(ValueError):
            before_mri_reference_fields(identifier, {'source_native_inspectors': [proof['after_inspector']] * 2})
    with pytest.raises(ValueError):
        before_mri_reference_fields('ra.mri-dementia', fields)
