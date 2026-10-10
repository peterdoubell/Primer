"""Parent lesson previews reuse only release-verified original source rasters."""
import copy,json
from pathlib import Path
import pytest
from primer.curriculum import Curriculum
from primer import radiology
from primer.source_raster_integrity import _inventory
ROOT=Path(__file__).resolve().parents[1]
def test_parent_uterine_previews_are_the_actual_licensed_source_objects():
 c=Curriculum();rows=c.node('rad.5.uterine-mr')['radiology_reference']['key_images']
 original={r['id']:r for r in json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())['ra.mri-cervical-cancer']}
 assert len(rows)==3
 for row in rows:
  source=original[row['original_asset_id']]
  assert row['src']==source['src'] and row['sha256']==source['sha256']
  assert row['license']=='CC BY 4.0' and row['source_context']['current_patient_findings'] is False
  assert 'radiologyassistant.nl/assets/' not in row['src']
  radiology.validate_image_source(row['src'])
 assert rows[1]['original_asset_id'].endswith('pmc10605640-fig1')
def test_unknown_or_escaping_open_source_paths_cannot_be_registered_by_prefix():
 prefix='/app/reference-media/radiology-open/'
 for relative in ['missing.jpg','../outside.jpg','cervical-cancer/%2e%2e/escape.jpg','cervical-cancer\\escape.jpg','cervical-cancer/cervical-cancer-pmc10605640-fig1.jpg?x=1']:
  with pytest.raises(ValueError):radiology.validate_image_source(prefix+relative)
def test_changed_registered_metadata_is_rejected_even_with_a_known_url(monkeypatch):
 original=radiology._read;data=json.loads((ROOT/'data/radiology/radiology-static-rasters.json').read_text());url='/app/reference-media/radiology-open/cervical-cancer/cervical-cancer-pmc10605640-fig1.jpg';bad=copy.deepcopy(data);bad['files'][url]['sha256']='0'*64
 monkeypatch.setattr(radiology,'_read',lambda name:bad if name=='radiology-static-rasters.json' else original(name))
 with pytest.raises(ValueError,match='changed'):radiology.validate_image_source(url)

def test_hosted_parent_preview_needs_the_exact_verified_registry_when_file_is_missing(monkeypatch):
 url='/app/reference-media/radiology-open/cervical-cancer/cervical-cancer-pmc10605640-fig1.jpg'
 path=(ROOT/'web'/url.removeprefix('/app/')).resolve();original=Path.is_file
 monkeypatch.setattr(Path,'is_file',lambda self:False if self.resolve()==path else original(self))
 monkeypatch.delenv('VERCEL',raising=False)
 with pytest.raises(ValueError,match='missing'):radiology.validate_image_source(url)
 monkeypatch.setenv('VERCEL','1');_inventory.cache_clear()
 radiology.validate_image_source(url)
 read=radiology._read;bad=copy.deepcopy(read('radiology-static-rasters.json'));bad['files'][url]['width']+=1
 monkeypatch.setattr(radiology,'_read',lambda name:bad if name=='radiology-static-rasters.json' else read(name))
 with pytest.raises(ValueError,match='differs'):radiology.validate_image_source(url)
