"""A source CT companion preserves its original arrays, case context and access gate."""
import hashlib,json
from pathlib import Path
import pytest
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail,resolve
from primer import thoracic_lung_native as lung
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/thoracic-lung-source-review-s0028'


def test_combining_sources_does_not_mutate_cached_curated_bindings():
    from primer import source_native_inspectors as combined
    from primer.thoracic_native_inspectors import references as curated
    for _ in range(3):
        combined.references.cache_clear()
        assert [i['id'] for i in combined.references()['ra.thoracic-ultrasound']] == [
            'bp3d-thoracic-original-surfaces', 'totalseg-s0028-lung-native',
            'totalseg-s0028-basal-context', 'totalseg-v1-s0028-cardiac-native']
        assert [i['id'] for i in curated()['ra.thoracic-ultrasound']] == ['bp3d-thoracic-original-surfaces']


def test_curated_and_ct_sources_coexist_without_replacing_images_or_report_fields():
    c=Curriculum();ref=detail(c,resolve('ra.thoracic-ultrasound'))['radiology_reference']
    assert [i['id'] for i in ref['source_native_inspectors']]==['bp3d-thoracic-original-surfaces','totalseg-s0028-lung-native','totalseg-s0028-basal-context','totalseg-v1-s0028-cardiac-native']
    assert len(ref['structure_atlas'])==16 and len(ref['source_motion_references'])==6
    assert all(not s['normal'] for s in ref['walkthrough']['steps'])
    model=next(i for i in c.node('rad.5.pleura')['lesson_media'] if i.get('renderer')=='radiology-anatomy')
    assert model['props']['native_inspectors']==ref['source_native_inspectors']
    item=ref['source_native_inspectors'][1];assert item['modality']=='CT'
    assert not item['clinical_approval'] and not item['normal_anatomical_atlas_approval']
    assert not item['current_patient_registration'] and not item['complete_reporting_anatomy_approved']


def test_runtime_files_are_exact_preserved_review_resources():
    data=lung.registry();assert len(data['files'])==16
    for name,record in data['files'].items():
        actual=lung.validate_file(name).read_bytes()
        assert actual==(REVIEW/name).read_bytes()
        assert hashlib.sha256(actual).hexdigest()==record['sha256'] and len(actual)==record['bytes']
    assert lung.references()['ra.thoracic-ultrasound'][0]['manifest_sha256']==data['files']['viewer-manifest.json']['sha256']


@pytest.mark.parametrize('asset',['../index.html','originals/../viewer.css','originals%2Fct.nii.gz','missing.nii.gz','/index.html'])
def test_unregistered_source_path_is_rejected(asset):
    with pytest.raises(ValueError,match='Unknown'):lung.validate_file(asset)


def test_present_corrupt_source_never_falls_back_to_hosted_copy(tmp_path,monkeypatch):
    lung.registry();p=tmp_path/'web/anatomy/totalseg-s0028-lungs/originals/ct.nii.gz';p.parent.mkdir(parents=True);p.write_bytes(b'corrupt source')
    monkeypatch.setattr(lung,'ROOT',tmp_path);monkeypatch.setenv('VERCEL','1')
    with pytest.raises(ValueError,match='bytes changed'):lung.validate_file('originals/ct.nii.gz')


def test_hosted_metadata_only_applies_to_registered_payloads(tmp_path,monkeypatch):
    lung.registry();monkeypatch.setattr(lung,'ROOT',tmp_path);monkeypatch.delenv('VERCEL',raising=False)
    with pytest.raises(ValueError,match='missing'):lung.validate_file('originals/ct.nii.gz')
    monkeypatch.setenv('VERCEL','1');lung.validate_file('originals/ct.nii.gz')
    with pytest.raises(ValueError,match='missing'):lung.validate_file('index.html')


@pytest.mark.parametrize('path',['primer/server.py','primer/module_media.py','primer/source_native_inspectors.py','web/app.js','vercel.json','tools/thoracic_native_runtime_compatibility.py'])
def test_lung_integration_inverse_rejects_unreviewed_shared_changes(path):
    from tools.thoracic_lung_runtime_compatibility import before_lung_bytes,reviewed
    raw=(ROOT/path).read_bytes();restored=before_lung_bytes(path,raw)
    assert hashlib.sha256(restored).hexdigest()==reviewed()['files'][path]['before_sha256']
    with pytest.raises(ValueError,match='Unreviewed'):before_lung_bytes(path,raw+b'\n')
