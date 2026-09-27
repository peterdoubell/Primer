"""A native-mesh teaching view must retain its source and adaptation identity."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from primer import radiology_catalog
from tools.check_msk_fidelity import inspect_asset, inspect_binding, requirements_for, review_scope_fingerprint


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / 'web/reference-media/msk-open'


@pytest.fixture
def derived():
    catalog = json.loads((ROOT / 'data/radiology/msk-open-images.json').read_text())
    return [image for image in catalog['ra.mri-knee'] if image.get('origin') == 'source-derived']


def test_derived_views_are_schematics_with_reviewable_native_sources(derived):
    assert len(derived) == 3
    for image in derived:
        assert image['kind'] == 'schematic' and image['modality'] == 'Schematic'
        assert image['figure_title'] and 'figure_number' not in image
        assert image['license'] == 'CC BY-SA 3.0 Unported'
        assert image['license_url'] == 'https://creativecommons.org/licenses/by-sa/3.0/'
        assert hashlib.sha256((FIGURES / Path(image['src']).name).read_bytes()).hexdigest() == image['sha256']
        radiology_catalog._validate_source_derived_figure(image, FIGURES)


@pytest.mark.parametrize('change,reason', [
    ({'kind': 'clinical-image', 'modality': 'MRI'}, 'schematic title'),
    ({'figure_number': 1}, 'schematic title'),
    ({'figure_title': ''}, 'schematic title'),
    ({'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/'}, 'ShareAlike'),
])
def test_source_views_cannot_be_relabelled_as_published_mri_or_relicensed(derived, change, reason):
    image = copy.deepcopy(derived[0])
    image.update(change)
    with pytest.raises(ValueError, match=reason):
        radiology_catalog._validate_source_derived_figure(image, FIGURES)


@pytest.mark.parametrize('field,value,reason', [
    ('source_manifest', '/app/anatomy/msk-mri-knee/manifest.json', 'source provider'),
    ('source_manifest_sha256', '0' * 64, 'source manifest changed'),
    ('rendering_evidence', '/app/reference-media/msk-open/../../private.json', 'evidence is missing'),
    ('rendering_evidence_sha256', '0' * 64, 'evidence changed'),
])
def test_derivation_cannot_silently_switch_sources_or_evidence(derived, field, value, reason):
    image = copy.deepcopy(derived[0])
    image['derivation'][field] = value
    with pytest.raises(ValueError, match=reason):
        radiology_catalog._validate_source_derived_figure(image, FIGURES)


@pytest.mark.parametrize('field,value', [('source_sha256', '0' * 64), ('triangles', 1),
                                       ('retained_triangles', 1), ('source_positions_and_facet_normals_retained', False)])
def test_new_evidence_checksum_cannot_authorize_different_source_geometry(derived, monkeypatch, field, value):
    image = copy.deepcopy(derived[0])
    path = ROOT / 'web' / image['derivation']['rendering_evidence'].removeprefix('/app/')
    evidence = json.loads(path.read_bytes())
    row = next(row for row in evidence['figures'] if row['filename'] == Path(image['src']).name)
    row['parts'][0][field] = value
    altered = json.dumps(evidence).encode()
    image['derivation']['rendering_evidence_sha256'] = hashlib.sha256(altered).hexdigest()
    read = Path.read_bytes
    monkeypatch.setattr(Path, 'read_bytes', lambda self: altered if self == path else read(self))
    with pytest.raises(ValueError, match='source geometry changed'):
        radiology_catalog._validate_source_derived_figure(image, FIGURES)


def test_derived_marker_cannot_be_removed_to_bypass_source_checks(derived, monkeypatch):
    original = radiology_catalog._read
    def changed(name, default=None):
        data = copy.deepcopy(original(name, default))
        if name == 'msk-open-images.json':
            image = next(item for item in data['ra.mri-knee'] if item['id'] == derived[0]['id'])
            image.pop('origin')
        return data
    monkeypatch.setattr(radiology_catalog, '_read', changed)
    radiology_catalog._structure_atlases.cache_clear()
    try:
        with pytest.raises(ValueError, match='actual source figure number'):
            radiology_catalog._structure_atlases()
    finally:
        radiology_catalog._structure_atlases.cache_clear()


def test_only_reviewed_local_faces_become_candidates_not_whole_object_components(derived):
    assets = {item['id']: item for item in json.loads(
        (ROOT / 'data/radiology/msk-asset-evidence.json').read_text())['assets']}
    requirements = json.loads((ROOT / 'data/radiology/msk-structure-requirements.json').read_text())
    knee = next(item for item in requirements['investigations'] if item['investigation_id'] == 'ra.mri-knee')
    leaves = {item['id']: item for item in requirements_for(knee)}
    review_path = ROOT / 'docs/msk-openknee-schematic-review/independent-anchor-review.json'
    assert hashlib.sha256(review_path.read_bytes()).hexdigest() == 'b98c69095500a7355a1ff1fa8034637adf1f9db55189e4972d347fc15f225a53'
    review = json.loads(review_path.read_text())
    assert review['clinical_approval'] is False
    expected = {
        'oks003-ptc': 'knee.patellar_cartilage.articular_surface',
        'oks003-mns-m': 'knee.medial_meniscus.superior_surface',
        'oks003-mns-l': 'knee.lateral_meniscus.superior_surface',
    }
    assert {item['source_part_id']: item['requirement_leaf'] for item in review['proposed_local_candidates']} == expected
    for identifier, leaf in expected.items():
        assert assets[identifier]['structure_ids'] == [leaf]
    for identifier in ['oks003-tbc-m', 'oks003-tbc-l', 'oks003-ptb', 'oks003-tbb', 'oks003-fbb']:
        assert assets[identifier]['structure_ids'] == []
    schematics = [assets[image['id']] for image in derived]
    assert {leaf for item in schematics for leaf in item['structure_ids']} == set(expected.values())
    tibial = next(item for item in schematics if 'tibial' in item['id'])
    assert tibial['structure_ids'] == []
    for item in schematics + [assets[identifier] for identifier in expected]:
        assert item['source_context']['laterality'] == 'left'
        assert item['source_context']['setting'] == 'cadaveric'
        assert item['anatomical_review']['status'] == 'pending'
        for leaf in item['structure_ids']:
            assert inspect_binding(item, leaves[leaf]) == []
        issues = inspect_asset(item, ROOT, review_scope_fingerprint(item, requirements))
        assert 'asset_fingerprint_mismatch' not in issues
        assert 'anatomical_review_missing_or_stale' in issues
        assert 'high_fidelity_unproven' in issues
