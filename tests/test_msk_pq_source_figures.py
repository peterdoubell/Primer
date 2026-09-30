"""Keep the published PQ variant distinct from ordinary muscles and full geometry."""
from pathlib import Path
import json,hashlib
from tools.check_msk_fidelity import requirements_for,inspect_binding,inspect_requirement_coverage
ROOT=Path(__file__).resolve().parents[1]
def records():
 req=json.loads((ROOT/'data/radiology/msk-structure-requirements.json').read_text());ankle=next(i for i in req['investigations'] if i['investigation_id']=='ra.mri-ankle');leaves={r['id']:r for r in requirements_for(ankle)};assets={a['id']:a for a in json.loads((ROOT/'data/radiology/msk-asset-evidence.json').read_text())['assets']};return assets,leaves

def test_pq_source_pixels_context_and_partial_extent():
 from primer.radiology_catalog import _structure_atlases
 images=_structure_atlases()['ra.mri-ankle'];assets,leaves=records()
 for identifier,filename,dimensions in [('open-ankle-peroneus-quartus-mri-yuksel-fig2','yuksel2025-peroneus-quartus-mri-fig2.jpg',(760,331)),('open-ankle-peroneus-quartus-pattern-yuksel-fig1','yuksel2025-peroneus-quartus-pattern-fig1.jpg',(664,625))]:
  image=next(i for i in images if i['id']==identifier);raw=(ROOT/'web'/image['src'].removeprefix('/app/')).read_bytes();assert hashlib.sha256(raw).hexdigest()==image['sha256']
  asset=assets[identifier];prior=asset['prior_repository_preview'];assert hashlib.sha256((ROOT/'docs/msk-accessory-ankle-source-review'/filename).read_bytes()).hexdigest()==prior['sha256'];assert (prior['width'],prior['height'])==dimensions
  assert asset['source_context']['anatomical_variant']=='peroneus_quartus' and asset['anatomical_review']['status']=='pending';assert asset['pixel_provenance']['higher_resolution_pixels_verified'] is True;assert asset['pixel_provenance']['highest_resolution_master_verified'] is False
  assert not any('attachment' in t or 'accessory_soleus' in t or 'accessorius_longus' in t for t in asset['structure_ids'])
  for target in asset['structure_ids']:
   assert not inspect_binding(asset,leaves[target]);assert inspect_requirement_coverage(asset,leaves[target])==['requirement_coverage_partial']
  assert 'source_context_anatomical_variant_mismatch' in inspect_binding(asset,leaves['ankle.accessory_soleus_muscle.muscle_belly'])

def test_signed_illustration_is_not_mri_or_author_created_provenance():
 assets,leaves=records();scheme=assets['open-ankle-peroneus-quartus-pattern-yuksel-fig1'];assert scheme['kind']=='schematic' and scheme['modality']=='Schematic';assert 'Eylem 2025' in scheme['source']['license']['attribution'];review=json.loads((ROOT/'docs/msk-accessory-ankle-source-review/figure1-license-attribution-followup.json').read_text());assert review['artist_signature_preserved'] and not review['creator_full_identity_established'] and not review['author_created_provenance_claimed']
 mri=assets['open-ankle-peroneus-quartus-mri-yuksel-fig2'];assert mri['source_context']['selected_panels']==['a','b','c'];assert mri['source_context']['laterality']=='not_reported';assert mri['source_context']['population']['life_stage']=='not_reported'


def test_variant_presence_does_not_establish_pathology():
 import copy
 assets,leaves=records();asset=assets['open-ankle-peroneus-quartus-mri-yuksel-fig2'];target=copy.deepcopy(leaves['ankle.peroneus_quartus_muscle.muscle_belly']);target['context_requirements'].append({'purpose':'pathology_example'})
 assert 'source_context_depicted_state_unresolved' in inspect_binding(asset,target)
