"""Reader references must preserve acquisition identity and unapproved source scope."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
from primer import radiology_catalog as catalog
from primer.curriculum import Curriculum

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'web/reference-media/radiology-open'
ROLES=['arterial-labelled','venous-labelled']


def source_image(role):
    return next(r for r in json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())['ra.ct-pancreatic-cancer'] if r['id']=='native-cptac-c3l02112-'+role+'-ct')


def test_pancreatic_reader_preserves_separate_source_sections_without_structure_credit():
    ref=catalog.detail(Curriculum(),catalog.resolve('ra.ct-pancreatic-cancer'))['radiology_reference']
    images=[r for r in ref['structure_atlas'] if r['id'].startswith('native-cptac-c3l02112-')]
    assert len(images)==2
    for role,count in zip(ROLES,[365,713]):
        image=next(r for r in images if r['id']==source_image(role)['id'])
        proof=json.loads((SOURCE/image['derivation']['evidence_url'].rsplit('/',1)[-1]).read_text())
        assert proof['source_shape']==[count,512,512]
        assert proof['source']['source_role']==role
        assert proof['source']['annotation_doi']=='10.7937/BW9V-BX61'
        assert proof['declared_spacing_between_slices_mm']==-.625
        assert proof['original_instance_order_signed_steps_mm']==[-.625,-.625]
        assert proof['observed_interplane_step_mm']==.625
        assert proof['cross_acquisition_registration'] is False and proof['tracking_identity_reconciled'] is False
        assert 'not registered or matched' in image['caption'] and 'two acquired CT planes unannotated' in image['limits']
        asset=next(a for a in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if a['id']==image['id'])
        assert asset['structure_ids']==[] and asset['requirement_coverage']=={}
        assert asset['anatomical_review']['status']=='pending'
        assert asset['investigation_ids']==['ra.ct-pancreatic-cancer']
    other=catalog.detail(Curriculum(),catalog.resolve('ra.solid-renal-masses'))['radiology_reference']
    assert not any(r['id'].startswith('native-cptac-c3l02112-') for r in other['structure_atlas'])


@pytest.mark.parametrize('role',ROLES)
@pytest.mark.parametrize('field',['cross_acquisition_registration','tracking_identity_reconciled','named_phase_verified',
                                  'histological_diagnosis_verified','source_annotation_is_whole_pancreas',
                                  'source_volume_and_end_extent_reconciled','annotation_geometry_overlaid'])
def test_proof_cannot_remove_source_limits_after_rehash(tmp_path,role,field):
    image=copy.deepcopy(source_image(role))
    name=image['derivation']['evidence_url'].rsplit('/',1)[-1]
    proof=json.loads((SOURCE/name).read_text());proof[field]=True
    path=tmp_path/name;path.write_text(json.dumps(proof))
    image['derivation']['evidence_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):catalog._validate_native_volume_figure(image,tmp_path)


@pytest.mark.parametrize('role',ROLES)
def test_other_acquisition_provenance_cannot_be_substituted(tmp_path,role):
    image=copy.deepcopy(source_image(role));other=source_image(next(r for r in ROLES if r!=role))
    name=image['derivation']['evidence_url'].rsplit('/',1)[-1]
    raw=(SOURCE/other['derivation']['evidence_url'].rsplit('/',1)[-1]).read_bytes()
    (tmp_path/name).write_bytes(raw);image['derivation']['evidence_sha256']=hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError):catalog._validate_native_volume_figure(image,tmp_path)
