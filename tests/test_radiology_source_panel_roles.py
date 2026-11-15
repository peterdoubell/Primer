"""Displayed modalities must match source panel facts; no context means no inferred clinical approval."""
import copy,json
from pathlib import Path
import pytest
from primer import radiology_catalog as catalog
from tools.check_msk_fidelity import inspect_binding
ROOT=Path(__file__).resolve().parents[1]
def source_row(ident):
    for filename in ['msk-open-images.json','radiology-open-images.json']:
        for rows in json.loads((ROOT/'data/radiology'/filename).read_text()).values():
            for r in rows:
                if r['id']==ident:return r
    raise AssertionError(ident)
@pytest.mark.parametrize('change',['wrong_primary_modality','photo_as_CT','selected_absent','duplicate_selected','displayed_selection','null_displayed_selection','ancillary_wrong_kind','ancillary_absent','ancillary_duplicate','ancillary_overlap'])
def test_fixed_lung_mixed_roles_cannot_be_silently_relabelled(change):
    row=copy.deepcopy(source_row('open-hipct-lung-pmc9163096-fig1'));c=row['source_context']
    if change=='wrong_primary_modality':row['modality']='MRI'
    if change=='photo_as_CT':c['selected_panels']=['a'];row['clinical_panels']=['a']
    if change=='selected_absent':c['selected_panels']=['missing'];row['clinical_panels']=['missing']
    if change=='duplicate_selected':c['selected_panels']=['d','d']
    if change=='displayed_selection':row['clinical_panels']=['c']
    if change=='null_displayed_selection':row['clinical_panels']=None
    if change=='ancillary_wrong_kind':row['ancillary_panels'][0]['kind']='Histology'
    if change=='ancillary_absent':row['ancillary_panels'][0]['panels']=['missing']
    if change=='ancillary_duplicate':row['ancillary_panels'][0]['panels']=['a','a']
    if change=='ancillary_overlap':row['ancillary_panels'][0]['panels']=['d']
    with pytest.raises(ValueError):catalog._validate_source_panel_roles(row)
def test_schematic_selection_is_distinct_from_empty_clinical_selection():
    row=source_row('open-knee-semimembranosus-expansions-picasso-s1')
    assert row['clinical_panels']==[] and row['schematic_panels']==['A']
    catalog._validate_source_panel_roles(row)
def test_explicit_empty_proposal_is_preserved_without_granting_evidence():
    row=source_row('open-tavi-access-pmc3948900-fig22');catalog._validate_source_panel_roles(row)
    asset={'kind':'clinical_image','modality':row['modality'],'source_context':row['source_context']}
    assert 'source_context_panel_selection_invalid' in inspect_binding(asset,{'modality_scope':['CT']})
def test_every_existing_typed_source_record_satisfies_display_role_contract():
    records=[]
    for file in ['msk-open-images.json','radiology-open-images.json']:
        for images in json.loads((ROOT/'data/radiology'/file).read_text()).values():
            for row in images:
                if any(k in row.get('source_context',{}) for k in ['selected_panels','panel_types','panel_states']):records.append(row)
    assert len(records)>=371
    for row in records:catalog._validate_source_panel_roles(row)
def test_reader_loading_rejects_conflict_before_serving_source_gallery(monkeypatch):
    original=catalog._read
    def changed(name,default=None):
        d=copy.deepcopy(original(name,default))
        if name=='radiology-open-images.json':
            row=next(r for r in d['ra.hrct-lung'] if r['id']=='open-hipct-lung-pmc9163096-fig1');row['source_context']['panel_types']['d']='MRI'
        return d
    catalog._structure_atlases.cache_clear();monkeypatch.setattr(catalog,'_read',changed)
    try:
        with pytest.raises(ValueError,match='displayed modality'):catalog._structure_atlases()
    finally:catalog._structure_atlases.cache_clear()


@pytest.mark.parametrize('kind,modality',[('clinical-image','Schematic'),('schematic','CT')])
def test_schematic_kind_cannot_be_relabelled_as_clinical_acquisition(kind,modality):
    with pytest.raises(ValueError,match='kind and schematic'):
        catalog._validate_source_panel_roles({'kind':kind,'modality':modality})


def test_legacy_single_panel_keeps_explicit_source_role_without_duplicate_display_field():
    row=source_row('open-knee-medial-posterior-root-mri-ssr-fig2a')
    assert 'clinical_panels' not in row and row['source_context']['selected_panels']==['a']
    catalog._validate_source_panel_roles(row)
    row=copy.deepcopy(row);row['source_context']['panel_types']['a']='Dissection'
    with pytest.raises(ValueError,match='displayed modality'):catalog._validate_source_panel_roles(row)
