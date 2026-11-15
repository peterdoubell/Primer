"""Source muscle envelopes do not establish tendon or internal anatomy."""
import hashlib
import json
from pathlib import Path
from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage, requirements_for

ROOT = Path(__file__).resolve().parents[1]


def test_four_native_muscle_candidates_remain_partial_and_separate_from_tendons():
    evidence=json.loads((ROOT/'data/radiology/msk-asset-evidence.json').read_text())
    requirements=json.loads((ROOT/'data/radiology/msk-structure-requirements.json').read_text())
    investigation=next(i for i in requirements['investigations'] if i['investigation_id']=='ra.mri-hamstring')
    leaves={r['id']:r for r in requirements_for(investigation)}
    proof=json.loads((ROOT/'docs/msk-hamstring-model-review/mesh-bounds.json').read_text())
    assets={a['id']:a for a in evidence['assets']}
    assert len(proof['parts'])==4
    for record in proof['parts']:
        a=assets[record['id']]
        assert a['investigation_ids']==['ra.mri-hamstring']
        assert len(a['structure_ids'])==1
        target=a['structure_ids'][0]
        assert target.endswith('_muscle.muscle_belly')
        assert inspect_binding(a,leaves[target])==[]
        assert inspect_requirement_coverage(a,leaves[target])==['requirement_coverage_partial']
        assert a['anatomical_review']['status']=='pending'
        assert a['fidelity']!='high'
        assert a['representation_selection']['part_ids']==[a['id']]
        assert hashlib.sha256((ROOT/a['local_path']).read_bytes()).hexdigest()==record['sha256']==a['sha256']
        surface=assets[a['id']+'-material-0']
        assert surface['representation']=='source_material_surface'
        assert surface['structure_ids']==[]


def test_shared_hamstring_figures_preserve_source_identity_and_scope(monkeypatch):
    import copy
    import pytest
    from primer import radiology_catalog as catalog
    catalog._structure_atlases.cache_clear()
    atlas=catalog._structure_atlases()
    selected=[x for x in atlas['ra.mri-hamstring'] if x['id'].startswith('open-hip-')]
    assert atlas['ra.mri-hamstring'][0]['id']=='open-hamstring-intramuscular-tendon-weber-fig3'
    assert [x['id'] for x in selected]==['open-hip-proximal-hamstring-schematic-balius-fig2','open-hip-tendon-boutin-fig6-5']
    for image in selected:
        assert image==next(x for x in atlas['ra.hip-fai'] if x['id']==image['id'])
    original=catalog._read
    def changed(name,default=None):
        value=original(name,default)
        if name=='msk-atlas-sharing.json':
            value=copy.deepcopy(value)
            value['ra.mri-hamstring']['include_ids'].append('open-hip-rectus-femoris-course-mecho-fig2')
        return value
    monkeypatch.setattr(catalog,'_read',changed)
    catalog._structure_atlases.cache_clear()
    with pytest.raises(ValueError,match='scope review'):
        catalog._structure_atlases()
    catalog._structure_atlases.cache_clear()


def test_append_requires_explicit_mode_and_preserves_authored_figures(monkeypatch):
    import copy
    import hashlib
    import pytest
    from primer import radiology_catalog as catalog
    original=catalog._read
    mode=['append']
    def changed(name,default=None):
        value=copy.deepcopy(original(name,default))
        if name=='msk-open-images.json':
            # A real preserved source serves only as a synthetic authored-gallery fixture.
            value['ra.mri-hamstring']=[value['ra.hip-fai'].pop(0)]
        if name=='msk-atlas-sharing.json':
            record=value['ra.mri-hamstring']
            if mode[0]: record['mode']=mode[0]
            else: record.pop('mode',None)
            payload={'source':record['source'],'target':'ra.mri-hamstring','include_ids':record['include_ids'],
                     'evidence_sha256':record['cross_topic_review']['sha256']}
            if mode[0]=='append':payload['mode']='append'
            record['cross_topic_review']['scope_sha256']=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        return value
    monkeypatch.setattr(catalog,'_read',changed)
    try:
        catalog._structure_atlases.cache_clear()
        result=catalog._structure_atlases()['ra.mri-hamstring']
        assert len(result)==3
        assert result[0]['id']==original('msk-open-images.json')['ra.hip-fai'][0]['id']
        mode[0]=None
        catalog._structure_atlases.cache_clear()
        with pytest.raises(ValueError,match='overwrite'):catalog._structure_atlases()
        mode[0]='replace'
        catalog._structure_atlases.cache_clear()
        with pytest.raises(ValueError,match='explicitly append'):catalog._structure_atlases()
    finally:
        catalog._structure_atlases.cache_clear()


def test_intramuscular_tendon_mri_preserves_injury_context_and_partial_extent():
    from primer import radiology_catalog as catalog
    from PIL import Image
    catalog._structure_atlases.cache_clear()
    image=catalog._structure_atlases()['ra.mri-hamstring'][0]
    assets=json.loads((ROOT/'data/radiology/msk-asset-evidence.json').read_text())['assets']
    asset=next(a for a in assets if a['id']==image['id'])
    target='hamstring.biceps_femoris_long_head_tendon.intramuscular_tendon'
    assert asset['structure_ids']==[target]
    assert asset['source_context']['depicted_state']=='mixed'
    assert asset['source_context']['panel_states']=={'a':'mixed','b':'mixed'}
    assert asset['anatomical_review']['status']=='pending'
    assert inspect_requirement_coverage(asset,{'id':target})==['requirement_coverage_partial']
    path=ROOT/asset['local_path']
    preserved=ROOT/'docs/msk-hamstring-mri-source-review'/path.name
    assert path.read_bytes()==preserved.read_bytes()
    assert hashlib.sha256(path.read_bytes()).hexdigest()==image['sha256']==asset['sha256']
    with Image.open(path) as im:
        assert im.size==(1500,964)
        assert im.mode=='L'


def test_semimembranosus_sequence_does_not_call_scarred_healing_normal():
    assets=json.loads((ROOT/'data/radiology/msk-asset-evidence.json').read_text())['assets']
    asset=next(a for a in assets if a['id']=='open-hamstring-semimembranosus-weber-fig7')
    assert asset['structure_ids']==['hamstring.semimembranosus_tendon.intramuscular_tendon']
    assert asset['source_context']['selected_panels']==list('abcdef')
    assert asset['source_context']['depicted_state']=='mixed'
    for p in ['e','f']:assert asset['source_context']['panel_states'][p]=='scarred_thickened_tendon_after_healing'
    assert asset['anatomical_review']['status']=='pending'
    assert inspect_requirement_coverage(asset,{'id':asset['structure_ids'][0]})==['requirement_coverage_partial']
    path=ROOT/asset['local_path'];original=ROOT/'docs/msk-hamstring-mri-source-review'/path.name
    assert path.read_bytes()==original.read_bytes()
    assert hashlib.sha256(path.read_bytes()).hexdigest()==asset['sha256']
