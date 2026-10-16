"""Cardiac source roles, complete originals and supplementary-only display stay bounded."""
import copy
import gzip
import hashlib
import json
from pathlib import Path

import pytest
from primer import cardiac_wall_context as context
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve

ROOT = Path(__file__).resolve().parents[1]


def test_every_context_resource_matches_its_pinned_original_or_authored_display():
    data = context.registry()
    assert {key: len(group['files']) for key, group in data['groups'].items()} == {context.CURATED: 31, context.COMPARISONS: 6064}
    for key, group in data['groups'].items():
        for name, row in group['files'].items():
            raw = context.validate_file(key, name).read_bytes()
            assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']


def test_comparison_categories_and_colour_roles_cannot_be_relabelled_native_CT_or_3D():
    group = context.registry()['groups'][context.COMPARISONS]
    manifest = json.loads(context.validate_file(context.COMPARISONS, 'image-inventory.json').read_bytes())
    assert len(manifest['files']) == 6061
    assert set(manifest['categories']) == set(manifest['paper_defined_categories'])
    assert set(manifest['excluded_additional_categories']) == {'Left atrial appendage', 'Papillary muscle – LV', 'Posterior mitral leaflet'}
    assert manifest['paper_colour_roles'] == {'red': 'model prediction', 'green': 'manual ground-truth annotation'}
    assert manifest['source_native_DICOM_or_NIfTI_present'] is manifest['spatial_spacing_orientation_and_3D_registration_established'] is False
    assert all(row['dimensions'] == [512, 256] and row['member'] == 'images/' + row['sha256'] + '.png' for row in manifest['files'])
    assert 'Three additional archive categories' in group['inspector']['caption']
    html = context.validate_file(context.COMPARISONS, 'index.html').read_text()
    assert '<script src="gallery.js"></script>' in html and '<script>' not in html


def test_curated_original_topology_is_preserved_and_not_repaired_or_split_into_new_walls():
    group = context.registry()['groups'][context.CURATED]
    manifest = json.loads(context.validate_file(context.CURATED, 'manifest.json').read_bytes())
    assert len(manifest['parts']) == 14 and sum(part['faces'] for part in manifest['parts']) == 72572
    ventricular = next(part for part in manifest['parts'] if part['id'] == 'FJ2428')
    diagnostic = ventricular['source_diagnostics']
    assert diagnostic['exact_position_diagnostic_components'] == 8
    assert diagnostic['exact_position_nonmanifold_edges'] == 7 and diagnostic['zero_area_source_triangles'] == 3
    assert diagnostic['source_geometry_modified'] is False
    for part in manifest['parts']:
        original = gzip.decompress(context.validate_file(context.CURATED, part['source_obj']).read_bytes())
        assert hashlib.sha256(original).hexdigest() == part['source_sha256']
        raw = gzip.decompress(context.validate_file(context.CURATED, part['file']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == part['decoded_sha256']
        assert len(raw) == 12 + part['vertices'] * 24 + part['faces'] * 12
    assert group['inspector']['license'] == 'CC BY-SA 2.1 Japan'


def test_contexts_are_only_supplements_to_four_correct_reports_with_every_previous_source_retained():
    c = Curriculum()
    for identifier, entries in context.references().items():
        ref = detail(c, resolve(identifier))['radiology_reference']
        assert ref['source_native_inspectors'][-2:] == entries
        assert any(item['id'] == 'totalseg-v1-s0028-cardiac-native' for item in ref['source_native_inspectors'])
        assert all(item['supplementary_anatomy_context'] and all(item[flag] is False for flag in context.FLAGS) for item in entries)
        modified = copy.deepcopy(ref)
        modified['source_native_inspectors'][-1]['clinical_approval'] = True
        assert context.references()[identifier][-1]['clinical_approval'] is False


@pytest.mark.parametrize('asset', ['../index.html', 'images%2Funknown.png', 'missing.png', '/index.html'])
def test_unknown_resource_paths_fail_closed(asset):
    with pytest.raises(ValueError, match='Unknown'):
        context.validate_file(context.COMPARISONS, asset)


def test_present_corrupt_resource_never_redirects_to_a_different_hosted_copy(tmp_path, monkeypatch):
    data = context.registry()
    monkeypatch.setattr(context, 'ROOT', tmp_path)
    monkeypatch.setenv('VERCEL', '1')
    group = data['groups'][context.COMPARISONS]
    name = next(name for name in group['files'] if name.startswith('images/'))
    path = tmp_path / group['directory'] / name
    path.parent.mkdir(parents=True)
    path.write_bytes(b'wrong source')
    with pytest.raises(ValueError, match='bytes changed'):
        context.validate_file(context.COMPARISONS, name)
