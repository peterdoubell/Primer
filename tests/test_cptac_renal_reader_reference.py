import copy
import hashlib
import json
from pathlib import Path
import pytest
from primer import radiology_catalog as catalog
from primer.curriculum import Curriculum

ROOT=Path(__file__).resolve().parents[1]
ID='native-cptac-c3n03018-acq1-ct'


def source_image():
    return next(r for r in json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())['ra.solid-renal-masses'] if r['id']==ID)


def test_native_renal_ct_is_visible_only_in_solid_mass_context_without_fine_coverage():
    ref=catalog.detail(Curriculum(),catalog.resolve('ra.solid-renal-masses'))['radiology_reference']
    image=next(r for r in ref['structure_atlas'] if r['id']==ID)
    proof=json.loads((ROOT/'web'/image['derivation']['evidence_url'].removeprefix('/app/')).read_text())
    assert proof['source_shape']==[417,512,512]
    assert proof['source']['ct_dicom_files']==850
    assert proof['source']['selected_acquisition_dicom_files']==417
    assert proof['source_acquisitions_interleaved_or_deduplicated'] is False
    assert proof['declared_spacing_between_slices_mm']==2.5 and proof['observed_interplane_step_mm']==.625
    assert proof['source_volume_and_end_extent_reconciled'] is False
    assert {p['axis'] for p in proof['planes']}=={0,1,2}
    assert 'original spacing tag' in image['caption']
    assert image['license']=='CC BY 4.0' and 'figure_number' not in image
    cyst=catalog.detail(Curriculum(),catalog.resolve('ra.renal-cysts-bosniak'))['radiology_reference']
    assert not any(r['id']==ID for r in cyst['structure_atlas'])
    asset=next(a for a in json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text())['assets'] if a['id']==ID)
    assert asset['structure_ids']==[] and asset['requirement_coverage']=={}
    assert asset['anatomical_review']['status']=='pending'


@pytest.mark.parametrize('key,value',[('source_acquisitions_interleaved_or_deduplicated',True),('named_phase_verified',True),
 ('source_annotation_is_whole_kidney',True),('source_volume_and_end_extent_reconciled',True),('annotation_geometry_overlaid',True)])
def test_native_renal_proof_cannot_upgrade_source_scope_after_rehash(tmp_path,key,value):
    image=copy.deepcopy(source_image());source=ROOT/'web/reference-media/radiology-open'
    proof_path=source/image['derivation']['evidence_url'].rsplit('/',1)[-1]
    proof=json.loads(proof_path.read_text());proof[key]=value
    target=tmp_path/proof_path.name;target.write_text(json.dumps(proof));image['derivation']['evidence_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    (tmp_path/image['src'].rsplit('/',1)[-1]).write_bytes((source/image['src'].rsplit('/',1)[-1]).read_bytes())
    with pytest.raises(ValueError):catalog._validate_native_volume_figure(image,tmp_path)


def test_native_renal_source_cannot_combine_acquisitions_as_one_volume(tmp_path):
    image=copy.deepcopy(source_image());source=ROOT/'web/reference-media/radiology-open'
    proof=json.loads((source/image['derivation']['evidence_url'].rsplit('/',1)[-1]).read_text());proof['source']['selected_acquisition_dicom_files']=850;proof['source_shape']=[850,512,512]
    target=tmp_path/image['derivation']['evidence_url'].rsplit('/',1)[-1];target.write_text(json.dumps(proof));image['derivation']['evidence_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    with pytest.raises(ValueError):catalog._validate_native_volume_figure(image,tmp_path)
