"""Complete original captions reach the actual reader metadata without other drift."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
from tools.anatomy_sources import integrate_acute_stroke_sources as integration
from tools.anatomy_sources import repair_acute_stroke_captions as repair
from tools.anatomy_sources import stroke_registry_amendment as bridge
ROOT=Path(__file__).resolve().parents[1]


def test_all13_full_captions_are_exact_original_and_primary_source_text():
 rows=json.loads((ROOT/repair.REGISTRY).read_text())[integration.INV]
 proposal=json.loads((ROOT/integration.FOLDER/'ctp-final-integration-proposal.json').read_text())
 repair.validate_caption_binding(rows,proposal,require_full=True)
 assert len(rows)==13 and all(r['source_caption_full']==r['original_caption'] for r in rows)
 assert all(r['source_caption_full']!=r['caption'] for r in rows)
 assert 'source_caption_full' in (ROOT/'web/app.js').read_text() # actual reader contract


def test_the_added_field_is_the_only_change_and_frozen_evidence_stays_exact():
 a=json.loads((ROOT/repair.AMENDMENT).read_text());before=a['before_image_rows'];after=a['caption_complete_image_rows']
 assert len(before)==len(after)==13
 for old,new in zip(before,after):
  check=copy.deepcopy(new);assert check.pop('source_caption_full')==old['original_caption'];assert check==old
 for path,h in a['frozen_original_evidence_SHA256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
 for path,h in a['other_four_data_files_SHA256_unchanged'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
 assert hashlib.sha256((ROOT/'data/curriculum/11-radiology.json').read_bytes()).hexdigest()==a['current_quiz_file_SHA256']
 assert a['source_pixels_or_original_caption_changed'] is False and a['clinical_approval'] is False


def test_original_guard_is_preserved_and_only_image_row_hashes_are_extended():
 original=json.loads((ROOT/integration.FOLDER/'stroke-registry-additive-amendment-20261011.json').read_text());current=bridge.reviewed_amendment()
 altered=[p for p in original['files'] if original['files'][p]!=current['files'][p]]
 assert altered==[str(repair.REGISTRY)]
 assert {k:v for k,v in original.items() if k!='files'}=={k:v for k,v in current.items() if k!='files'}
 a=json.loads((ROOT/repair.AMENDMENT).read_text());assert a['original_guard_image_record']==original['files'][str(repair.REGISTRY)]
 assert a['caption_complete_guard_image_record']==current['files'][str(repair.REGISTRY)]


@pytest.mark.parametrize('mutation',['missing_caption','shortened_caption','different_original','missing_row','foreign_row'])
def test_missing_shortened_or_foreign_primary_caption_is_rejected(mutation):
 rows=json.loads((ROOT/repair.REGISTRY).read_text())[integration.INV];rows=copy.deepcopy(rows)
 proposal=json.loads((ROOT/integration.FOLDER/'ctp-final-integration-proposal.json').read_text())
 if mutation=='missing_caption':rows[0].pop('source_caption_full')
 elif mutation=='shortened_caption':rows[0]['source_caption_full']=rows[0]['original_caption'][:30]
 elif mutation=='different_original':rows[0]['original_caption']='Unreviewed clinical statement.';rows[0]['source_caption_full']=rows[0]['original_caption']
 elif mutation=='missing_row':rows.pop()
 else:rows[0]['id']='different-investigation'
 with pytest.raises(ValueError):repair.validate_caption_binding(rows,proposal,require_full=True)


def test_reproducible_normalizer_and_caption_repair_keep_the_same_complete_rows():
 p=json.loads((ROOT/integration.FOLDER/'ctp-final-integration-proposal.json').read_text());expected,_=integration.normalize_rows(p,str(integration.INDEPENDENT),integration.INDEPENDENT_SHA)
 actual=json.loads((ROOT/repair.REGISTRY).read_text())[integration.INV];assert actual==expected
 hashes={str(p):hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in integration.DATA_PATHS}
 repair.repair();assert {str(p):hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in integration.DATA_PATHS}==hashes
