"""Reader integration of scoped anatomy sources without completeness claims."""
from pathlib import Path
import copy,gzip,hashlib,json
import pytest
from primer.curriculum import Curriculum
from primer import radiology_catalog as catalog
ROOT=Path(__file__).resolve().parents[1]


def test_thoracolumbar_has_partial_neural_reference_and_original_walkthrough():
    ref=catalog.detail(Curriculum(),catalog.resolve('ra.thoracolumbar-fractures'))['radiology_reference']
    source=ref['source_anatomy_references'][0]
    assert source['family']=='lumbosacral-neural' and source['initial_layer']=='cord'
    assert source['initial_cropped'] is False
    assert ref['walkthrough']['spatial_model']['family']=='spine'
    assert ref['spatial_model']['family']=='spine'
    image=source['source_image'];data=(ROOT/'web'/image['src'].removeprefix('/app/')).read_bytes();assert hashlib.sha256(data).hexdigest()==image['sha256']
    manifest=json.loads((ROOT/'web/anatomy/liu-lumbosacral-sub03/manifest.json').read_text())
    assert manifest['clinical_approval'] is False and manifest['runtime_promoted'] is True
    assert set(manifest['parts'])=={'cord','dura'}
    original=json.loads((ROOT/'docs/msk-lumbosacral-nerve-source-review/open-envelope-loft-audit.json').read_text())
    assert sum(p['triangles'] for p in manifest['parts'].values())==62680
    for name,p in manifest['parts'].items():
        data=(ROOT/'web'/p['file'].removeprefix('/app/')).read_bytes()
        assert hashlib.sha256(data).hexdigest()==p['sha256']
        assert gzip.decompress(data)[:4]==b'BP3D'
        row=next(x for x in original['parts'] if x['category']==name)
        assert row['boundary_matches_only_first_last_rings']


@pytest.mark.parametrize('mutation',['unknown_atlas','wrong_family','wrong_path','wrong_hash','wrong_layer','duplicate','image_path','image_hash','image_size'])
def test_invalid_source_reference_is_rejected(monkeypatch,mutation):
    original=catalog._read
    def changed(name,default=None):
        data=copy.deepcopy(original(name,default))
        if name=='source-anatomy-references.json':
            entry=data['ra.thoracolumbar-fractures'][0]
            if mutation=='unknown_atlas':entry['atlas']='other'
            if mutation=='wrong_family':entry['family']='cervical'
            if mutation=='wrong_path':entry['manifest_url']='/app/anatomy/../index.html'
            if mutation=='wrong_hash':entry['manifest_sha256']='0'*64
            if mutation=='wrong_layer':entry['initial_layer']='nerve'
            if mutation=='image_path':entry['source_image']['src']='/app/reference-media/liu-lumbosacral-sub03/../../index.html'
            if mutation=='image_hash':entry['source_image']['sha256']='0'*64
            if mutation=='image_size':entry['source_image']['width']=1
            if mutation=='duplicate':data['ra.thoracolumbar-fractures'].append(copy.deepcopy(entry))
        return data
    catalog._source_anatomy_references.cache_clear();monkeypatch.setattr(catalog,'_read',changed)
    try:
        with pytest.raises(ValueError):catalog._source_anatomy_references()
    finally:catalog._source_anatomy_references.cache_clear()


def test_recovery_copy_illustrations_are_not_opened(tmp_path,monkeypatch):
    from primer import curriculum as module
    names=['lesson-800.webp','lesson-800 2.webp','lesson-1600 3.webp','lesson-1600 10.webp']
    for name in names:(tmp_path/name).touch()
    monkeypatch.setattr(module,'ILLUSTRATION_ROOT',str(tmp_path))
    opened=[]
    def dimensions(path):
        opened.append(Path(path).name)
        if Path(path).name!='lesson-800.webp':raise AssertionError('Recovery copy was opened')
        return 800,600
    monkeypatch.setattr(module,'_webp_dimensions',dimensions)
    assert module._discover_lesson_illustrations()=={'/app/illustrations/lesson-800.webp':(800,600)}
    assert opened==['lesson-800.webp']
