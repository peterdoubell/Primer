"""Source namespace, rights, private delivery and thin-runtime integrity boundaries."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

from primer import pulmonary_source_delivery as source, pulmonary_native_inspectors as native
from tools.build_pulmonary_delivery_metadata import registry as build_registry

ROOT = Path(__file__).resolve().parents[1]
from tools.pulmonary_release_baselines import read_baseline


@pytest.fixture(autouse=True)
def clear_pulmonary_caches():
    source.delivery.cache_clear()
    native.references.cache_clear()
    yield
    source.delivery.cache_clear()
    native.references.cache_clear()


@pytest.mark.parametrize('change', [
    'project_id', 'team_id', 'store_id', 'blob_hostname', 'source_case', 'module_id', 'investigation_id',
    'source_proposal_sha256', 'independent_source_review_sha256', 'manifest_sha256',
    'source_url', 'annotation_source_url', 'license_url', 'license', 'missing', 'extra', 'path_alias',
    'role', 'mime', 'bytes_type', 'source_values_changed', 'source_original_bytes_changed',
    'url_host', 'url_userinfo', 'url_hash', 'url_query', 'url_fragment', 'url_extra_directory', 'url_original_name',
    'file_count', 'total_bytes', *source.APPROVAL_FLAGS,
])
def test_delivery_cannot_rebase_source_scope_rights_store_or_original_identity(change, tmp_path, monkeypatch):
    data = json.loads(source.REGISTRY.read_bytes())
    src = source.PREFIX + 'original-ct/00000001.dcm'
    row = data['files'][src]
    if change in {'missing', 'extra', 'path_alias'}:
        if change == 'missing':
            data['files'].pop(src)
        elif change == 'extra':
            data['files'][source.PREFIX + 'original-ct/00000430.dcm'] = copy.deepcopy(row)
        else:
            data['files'][source.PREFIX + 'original-ct/nested/00000001.dcm'] = data['files'].pop(src)
    elif change in {'role', 'mime', 'bytes_type'}:
        row[{'role': 'role', 'mime': 'content_type', 'bytes_type': 'bytes'}[change]] = {
            'role': 'literal-native-SEG-boundary', 'mime': 'text/html', 'bytes_type': True}[change]
    elif change.startswith('url_'):
        if change == 'url_host': row['url'] = row['url'].replace(source.BLOB_HOST, 'unreviewed.example')
        if change == 'url_userinfo': row['url'] = row['url'].replace('https://', 'https://reader@')
        if change == 'url_hash': row['url'] = row['url'].replace(row['sha256'], '0' * 64)
        if change == 'url_query': row['url'] += '?path=other'
        if change == 'url_fragment': row['url'] += '#other'
        if change == 'url_extra_directory': row['url'] = row['url'].replace('/original-ct/', '/nested/original-ct/')
        if change == 'url_original_name': row['url'] = row['url'].replace('00000001.dcm', '00000002.dcm')
    elif change in source.APPROVAL_FLAGS or change in {'source_values_changed', 'source_original_bytes_changed'}:
        row[change] = True
    elif change in {'file_count', 'total_bytes'}:
        data[change] += 1
    else:
        data[change] = 'unreviewed'
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps(data))
    monkeypatch.setattr(source, 'REGISTRY', path)
    # Exercise semantic gates independently of the whole-file fingerprint.
    monkeypatch.setattr(source, 'REGISTRY_SHA256', hashlib.sha256(path.read_bytes()).hexdigest())
    monkeypatch.setattr(source, 'ROOT', tmp_path)
    monkeypatch.setenv('VERCEL', '1')
    with pytest.raises(ValueError):
        source.delivery()


@pytest.mark.parametrize('flag', source.APPROVAL_FLAGS)
def test_top_level_source_packet_cannot_grant_approval(flag, tmp_path, monkeypatch):
    data = json.loads(source.REGISTRY.read_bytes())
    data[flag] = True
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps(data))
    monkeypatch.setattr(source, 'REGISTRY', path)
    monkeypatch.setattr(source, 'REGISTRY_SHA256', hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError):
        source.delivery()


@pytest.mark.parametrize('change', ['binding', 'id', 'module', 'investigation', 'source', 'annotation_source',
                                  'modality', 'publication', 'license', 'script_pin',
                                  'ct_chunk_gap', 'ct_storage', 'ct_source', 'ct_geometry', 'ct_scale',
                                  'annotation_transport', 'annotation_original', 'annotation_shape',
                                  'mask_sample_count', 'mesh_faces', 'xml_marks', 'registration', 'source_crop',
                                  'histology', 'ct_seg_registration', *source.APPROVAL_FLAGS])
def test_inspector_cannot_change_scope_source_geometry_or_approval(change, tmp_path, monkeypatch):
    data = json.loads(native.REGISTRY.read_bytes())
    item = data['inspectors']['lidc-idri-0525-native']
    manifest = json.loads((ROOT / 'web/anatomy/lidc-idri-0525/manifest.json').read_bytes())
    if change == 'binding': data['bindings'] = {'ra.brain-anatomy': ['lidc-idri-0525-native']}
    elif change == 'id': item['id'] = 'another-case'
    elif change in {'module', 'investigation'}: item[change + '_id'] = 'other'
    elif change in {'source', 'annotation_source', 'publication'}:
        item[{'source': 'source_url', 'annotation_source': 'annotation_source_url', 'publication': 'publication_url'}[change]] = 'https://unreviewed.example'
    elif change == 'modality': item['modality'] = 'MRI'
    elif change == 'license': item['license'] = 'CC BY-NC 4.0'
    elif change == 'script_pin': item['script_sha256'] = '0' * 64
    elif change == 'ct_chunk_gap': manifest['ct']['chunks'][1]['first_native_slice'] += 1
    elif change == 'ct_storage': manifest['ct']['dtype'] = '<u1'
    elif change == 'ct_source': manifest['ct']['slices'][0]['filename'] = manifest['ct']['slices'][1]['filename']
    elif change == 'ct_geometry': manifest['ct']['slices'][0]['position_LPS_mm'][2] += 0.7
    elif change == 'ct_scale': manifest['ct']['slices'][0]['slope'] = float('inf')
    elif change == 'annotation_transport': manifest['annotations'][0]['mask']['file'] = manifest['annotations'][1]['mask']['file']
    elif change == 'annotation_original': manifest['annotations'][0]['source_archive'] = 'another-original.zip'
    elif change == 'annotation_shape': manifest['annotations'][0]['source_shape'][2] += 1
    elif change == 'mask_sample_count': manifest['annotations'][0]['mask']['decoded_bytes'] -= 1
    elif change == 'mesh_faces': manifest['annotations'][0]['mesh']['triangles'] -= 2
    elif change == 'xml_marks': manifest['xml_marks'].pop()
    elif change == 'registration': manifest['current_patient_registration'] = True
    elif change == 'source_crop': manifest['source_ct_full_extent'] = False
    elif change == 'histology': manifest['histology_verified'] = True
    elif change == 'ct_seg_registration': manifest['ct_seg_coordinates_identical'] = True
    else: item[change] = True
    directory = tmp_path / 'web/anatomy/lidc-idri-0525'
    directory.mkdir(parents=True)
    for name in ['reference.html', 'reference.js']:
        shutil.copyfile(ROOT / 'web/anatomy/lidc-idri-0525' / name, directory / name)
    (directory / 'manifest.json').write_text(json.dumps(manifest))
    digest = hashlib.sha256((directory / 'manifest.json').read_bytes()).hexdigest()
    item['manifest_sha256'] = digest
    monkeypatch.setitem(native.AUTHORED_SHA256, 'manifest.json', digest)
    registry = tmp_path / 'inspector.json'
    registry.write_text(json.dumps(data))
    monkeypatch.setattr(native, 'ROOT', tmp_path)
    monkeypatch.setattr(native, 'REGISTRY', registry)
    monkeypatch.setattr(native, 'REGISTRY_SHA256', hashlib.sha256(registry.read_bytes()).hexdigest())
    with pytest.raises(ValueError):
        native.references()


def test_exact_metadata_generation_and_only_reviewed_public_redirects():
    data = source.delivery()
    assert build_registry() == data
    assert len(data['files']) == 480 and sum(row['bytes'] for row in data['files'].values()) == 370135064
    config = json.loads((ROOT / 'vercel.json').read_bytes())
    routes = config['routes']
    redirects = [row for row in routes if row.get('dest', '').startswith(source.BLOB_PREFIX)]
    assert len(redirects) == 480
    for src, row in data['files'].items():
        public = '/source-media/' + src.removeprefix('/app/')
        route, = [route for route in redirects if re.fullmatch(route['src'], public)]
        assert route['dest'] == row['url'] and route['status'] == 307
        assert route['headers'] == {'Cache-Control': 'public, max-age=31536000, immutable'}
    # Case-prefix fallback precedes generic filesystem rewrites, including for viewer code.
    barrier = {'src': '/source-media/anatomy/lidc-idri-0525/(.*)', 'dest': '/api/index.py'}
    barrier_index = routes.index(barrier)
    assert barrier_index == 480
    generic_index = next(i for i, row in enumerate(routes) if row.get('src') == '/source-media/(.*)')
    assert barrier_index < generic_index
    for asset in [*source.AUTHORED_FILES, 'original-ct/00000430.dcm', 'nested/reference.html']:
        assert not any(re.fullmatch(route['src'], '/source-media/anatomy/lidc-idri-0525/' + asset) for route in redirects)
    base = json.loads(read_baseline('vercel.json'))
    assert routes[481:] == base['routes']
    thoracic = {'src': 'web/anatomy/bp3d-thoracic-4.3/{transport,originals}/**', 'use': '@vercel/static'}
    lung = {'src': 'web/anatomy/totalseg-s0028-lungs/{originals,surfaces}/**', 'use': '@vercel/static'}
    basal = {'src': 'web/anatomy/totalseg-s0028-basal-context/{originals,surfaces}/**', 'use': '@vercel/static'}
    cardiac = {'src': 'web/anatomy/totalseg-v1-s0028-cardiac/{originals,surfaces}/**', 'use': '@vercel/static'}
    walls = {'src': 'web/anatomy/bp3d-cardiac-4.3/{originals,transport}/**', 'use': '@vercel/static'}
    comparisons = {'src': 'web/reference-media/cardiac-comparisons-2020/images/**', 'use': '@vercel/static'}
    # Compare the earlier build inventory after reversing only the byte-pinned
    # HippUnfold static/exclusion addition. Current pulmonary routes above remain exact.
    from tools.hippunfold_runtime_compatibility import before_hippunfold_bytes
    from tools.spl_limbic_runtime_compatibility import before_spl_bytes
    previous_config = before_spl_bytes('vercel.json', (ROOT / 'vercel.json').read_bytes())
    previous_builds = json.loads(before_hippunfold_bytes('vercel.json', previous_config))['builds']
    assert previous_builds[-6:] == [thoracic, lung, basal, cardiac, walls, comparisons]
    assert previous_builds[1:-6] == base['builds'][1:]
    assert previous_builds[0]['config']['excludeFiles'].startswith(base['builds'][0]['config']['excludeFiles'][:-1] + ',')
    ignored = (ROOT / '.vercelignore').read_text()
    patterns = [line for line in ignored.splitlines() if line.startswith('web/anatomy/lidc-idri-0525/')]
    assert all(not any(Path('web/anatomy/lidc-idri-0525/' + filename).match(pattern) for pattern in patterns)
               for filename in source.AUTHORED_FILES)
    assert all(any(Path('web/' + src.removeprefix('/app/')).match(pattern) for pattern in patterns)
               for src in data['files'])


def test_old_source_registries_and_bindings_are_preserved():
    from primer import source_native_inspectors as combined
    from primer.stroke_native_inspectors import references as stroke_references
    for path in ['data/radiology/native-source-delivery.json', 'data/radiology/native-source-inspectors.json',
                 'data/radiology/acute-stroke-source-delivery.json', 'data/radiology/soop-native-inspector.json',
                 'primer/stroke_source_delivery.py', 'primer/stroke_native_inspectors.py']:
        historical = read_baseline(path)
        assert (ROOT / path).read_bytes() == historical
    combined.references.cache_clear()
    refs = combined.references()
    original_brain = json.loads((ROOT / 'data/radiology/native-source-inspectors.json').read_bytes())
    expected_brain = [original_brain['inspectors'][key] for key in original_brain['bindings']['ra.brain-anatomy']]
    from tools.spl_limbic_runtime_compatibility import before_spl_reference_fields, reviewed as spl_reviewed
    from primer.spl_limbic_reference import references as spl_references
    spl_registered = spl_references()
    assert set(spl_registered) == {'ra.brain-anatomy', 'ra.mri-epilepsy', 'ra.mri-dementia'}
    assert all(items == [spl_reviewed()['source_inspector_addition']] for items in spl_registered.values())
    prior_brain = before_spl_reference_fields('ra.brain-anatomy', {'source_native_inspectors': refs['ra.brain-anatomy']})
    assert prior_brain['source_native_inspectors'] == expected_brain
    assert refs['ra.brain-anatomy'] == [*expected_brain, *spl_registered['ra.brain-anatomy']]
    assert refs['ra.acute-stroke'] == stroke_references()['ra.acute-stroke']
    from primer.cardiac_native_inspector import references as cardiac_references, BINDINGS as cardiac_bindings
    from primer.cardiac_wall_context import references as wall_references
    from primer import hippunfold_reference as hippocampal
    assert hippocampal.BINDINGS == {'ra.mri-epilepsy', 'ra.mri-dementia'}
    registered = hippocampal.references()  # Validates the pinned registry, manifest and source inventory.
    assert set(registered) == hippocampal.BINDINGS
    assert set(refs) == {'ra.brain-anatomy', 'ra.acute-stroke', 'ra.ct-pulmonary-nodules', 'ra.thoracic-ultrasound'} | cardiac_bindings | hippocampal.BINDINGS
    for identifier, expected in registered.items():
        prior = before_spl_reference_fields(identifier, {'source_native_inspectors': refs[identifier]})
        assert prior['source_native_inspectors'] == expected
        assert refs[identifier] == [*expected, *spl_registered[identifier]]
        assert [item['id'] for item in expected] == [hippocampal.IDENTIFIER]
    from primer.thoracic_native_inspectors import references as thoracic_references
    from primer.thoracic_lung_native import references as lung_references
    from primer.thoracic_basal_context import references as basal_references
    assert refs['ra.thoracic-ultrasound'] == [*thoracic_references()['ra.thoracic-ultrasound'], *lung_references()['ra.thoracic-ultrasound'], *basal_references()['ra.thoracic-ultrasound'], *cardiac_references()['ra.thoracic-ultrasound'], *wall_references()['ra.thoracic-ultrasound']]


def test_thin_hosted_metadata_cannot_accept_present_wrong_or_absent_local_source(tmp_path, monkeypatch):
    thin = tmp_path / 'thin'
    directory = thin / 'web/anatomy/lidc-idri-0525'
    directory.mkdir(parents=True)
    for name in source.AUTHORED_FILES:
        shutil.copyfile(ROOT / 'web/anatomy/lidc-idri-0525' / name, directory / name)
    monkeypatch.setattr(source, 'ROOT', thin)
    monkeypatch.setattr(native, 'ROOT', thin)
    monkeypatch.setenv('VERCEL', '1')
    assert len(source.delivery()['files']) == 480
    assert native.references()['ra.ct-pulmonary-nodules'][0]['modality'] == 'CT'
    monkeypatch.delenv('VERCEL')
    source.delivery.cache_clear()
    with pytest.raises(ValueError, match='absent locally'):
        source.delivery()
    monkeypatch.setenv('VERCEL', '1')
    source.delivery.cache_clear()
    wrong = directory / 'original-ct/00000001.dcm'
    wrong.parent.mkdir()
    wrong.write_bytes(b'present corrupt source must not use a hosted fallback')
    with pytest.raises(ValueError, match='Present pulmonary source'):
        source.delivery()
    wrong.unlink()
    wrong.symlink_to(tmp_path / 'missing-file')
    with pytest.raises(ValueError, match='regular file'):
        source.delivery()


def test_actual_full_app_private_get_head_and_hosted_fixtures(tmp_path):
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('TURSO', 'PRIMER_ACCESS_', 'VERCEL', 'BLOB_'))}
    env.update(PRIMER_DB=str(tmp_path / 'reader.db'), PRIMER_CONTENT_DIR=str(tmp_path / 'content'), PRIMER_BACKUP_DIR=str(tmp_path / 'backups'))
    output = tmp_path / 'proof.json'
    result = subprocess.run([sys.executable, str(ROOT / 'tools/check_pulmonary_delivery.py'), '--output', str(output)],
                            cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    proof = json.loads(output.read_text())
    assert proof['all_checks_passed'] and proof['source_payload_count'] == 480
    assert proof['source_payload_bytes'] == 370135064
    assert proof['counts']['local_exact_get'] == proof['counts']['local_exact_head'] == 480
    assert proof['counts']['hosted_fixed_redirects'] == 1920
    assert proof['counts']['unknown_path_rejections'] == 60
