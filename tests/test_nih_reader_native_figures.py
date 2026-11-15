import copy
import hashlib
import json
from pathlib import Path
import pytest
from primer import radiology_catalog as catalog
from primer.curriculum import Curriculum

ROOT = Path(__file__).resolve().parents[1]


def test_original_nih_numeric_labels_are_visible_without_station_or_clinical_credit():
    ref = catalog.detail(Curriculum(), catalog.resolve('ra.ct-mediastinum'))['radiology_reference']
    images = [x for x in ref['structure_atlas'] if x['id'].startswith('native-nih-med001')]
    assert len(images) == 3
    assets = json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets']
    for image in images:
        raw = (ROOT/'web'/image['src'].removeprefix('/app/')).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == image['sha256']
        proof = json.loads((ROOT/'web'/image['derivation']['evidence_url'].removeprefix('/app/')).read_text())
        assert proof['source']['ct_dicom_files'] == 666
        assert proof['source']['original_label_pixel_mismatches'] == 0
        assert proof['annotation_geometry_overlaid'] is False
        assert proof['source']['original_acquisition_resolution_verified'] is False
        assert proof['source_label_is_station_id'] is False and proof['clinical_approval'] is False
        assert 'figure_number' not in image and image['license'] == 'CC BY 3.0'
        asset = next(a for a in assets if a['id'] == image['id'])
        assert asset['structure_ids'] == [] and asset['anatomical_review']['status'] == 'pending'
        if proof['source_label'] == 2:
            assert proof['single_plane_annotation'] is True
            assert 'only one plane' in image['caption'] and 'complete 3D' in image['caption']


@pytest.mark.parametrize('change', ['relabeled_license', 'invented_figure_number', 'changed_provenance', 'wrong_dimensions'])
def test_nih_source_identity_and_render_contract_cannot_be_relabelled(monkeypatch, change):
    original = catalog._read
    def altered(name, default=None):
        data = copy.deepcopy(original(name, default))
        if name == 'radiology-open-images.json':
            image = next(x for x in data['ra.ct-mediastinum'] if x['id'].startswith('native-nih-med001'))
            if change == 'relabeled_license':
                image['license'] = 'CC BY 4.0'; image['license_url'] = 'https://creativecommons.org/licenses/by/4.0/'
            elif change == 'invented_figure_number': image['figure_number'] = 1
            elif change == 'changed_provenance': image['derivation']['evidence_sha256'] = '0'*64
            else: image['height'] = 1
        return data
    catalog._structure_atlases.cache_clear(); monkeypatch.setattr(catalog, '_read', altered)
    try:
        with pytest.raises(ValueError): catalog._structure_atlases()
    finally:
        catalog._structure_atlases.cache_clear()
