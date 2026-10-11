"""Add only the missing complete-caption field on the13 frozen CTP metadata rows.

The old source GO, proposals, data receipt, guard amendment and validation remain
unchanged. All source bytes and all non-caption row values are preserved exactly.
"""
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from tools.anatomy_sources import integrate_acute_stroke_sources as integration
from tools.anatomy_sources.integrate_myelopathy_sources import member,replace_member
from tools.check_radiology_fidelity import digest
ROOT=Path(__file__).resolve().parents[2];FOLDER=integration.FOLDER
REGISTRY=integration.DATA_PATHS[0]
AMENDMENT=FOLDER/'source-caption-full-addition-amendment-20261011.json'
OLD_PINS={
 'runtime-data-integration-20261011.json':'af4b98a3e40d2158c425abce296ff18569c45414518dec31f7cfe2063ca7ced3',
 'stroke-registry-additive-amendment-20261011.json':'c8e9d7ee4f023314e1a6e5901db2e9247694ea12b56339c5771c32043f961d36',
 'stroke-historical-guard-validation-20261011.json':'3fe6bf0f1793ff9dda8d418d673cbcc79ee24c3ce3541289bfbcea4fc1139dd9',
 'ctp-final-integration-proposal.json':'df1debaec552d12bbb9af778cdd2ac7a2c9e7597fea2b70071986504afabe368',
 'independent-review.json':'4af86b0db18667fd1b5af5e3c8244e7654828d4b2c0cfa5584de1b2f9deecde4',
}
XML=FOLDER/'source-ctp-2023/PMC9914845.1.xml'

def sha(raw):return hashlib.sha256(raw).hexdigest()


def validate_caption_binding(rows,proposal,*,require_full=False):
 expected={r['id']:r for r in proposal['images']}
 if len(rows)!=13 or {r['id'] for r in rows}!=set(expected):raise ValueError('Complete13 approved CTP caption bindings required')
 source=ET.parse(ROOT/XML)
 for row in rows:
  n=row['figure_number'];fig=source.find(f'.//fig[@id="diagnostics-13-00447-f{n:03d}"]')
  text=' '.join(' '.join(fig.find('caption').itertext()).split()) if fig is not None else None
  if (not isinstance(text,str) or not text or row.get('original_caption')!=text
      or row['original_caption']!=expected[row['id']]['original_caption']):raise ValueError('Original caption differs from primary publication binding')
  if require_full and 'source_caption_full' not in row:raise ValueError('Complete source caption field is missing')
  if 'source_caption_full' in row and row['source_caption_full']!=row['original_caption']:raise ValueError('Complete caption field differs from exact original')


def repair():
 for name,h in OLD_PINS.items():
  if sha((ROOT/FOLDER/name).read_bytes())!=h:raise ValueError('Frozen caption/source review changed: '+name)
 original=json.loads((ROOT/integration.ORIGINAL_RECEIPT).read_text());proposal=json.loads((ROOT/FOLDER/'ctp-final-integration-proposal.json').read_text())
 raw=(ROOT/REGISTRY).read_text();rows,a,b=member(raw,[integration.INV]);validate_caption_binding(rows,proposal)
 if any('source_caption_full' in r for r in rows):
  if not all('source_caption_full' in r for r in rows):raise ValueError('Partial pre-existing caption amendment is not approved')
  prior=json.loads((ROOT/AMENDMENT).read_text());new=(ROOT/REGISTRY).read_bytes()
  if sha(new)!=prior['after_registry_SHA256']:raise ValueError('Caption-complete registry differs from prior exact repair')
  print('Complete13 captions already match the exact reviewed repair');return prior
 before={str(p):sha((ROOT/p).read_bytes()) for p in integration.DATA_PATHS}
 if before!=original['data_file_SHA256']:raise ValueError('Pre-caption five-file data differs from frozen receipt')
 updated=copy.deepcopy(rows)
 for r in updated:r['source_caption_full']=r['original_caption']
 for old,new in zip(rows,updated):
  check=copy.deepcopy(new);check.pop('source_caption_full')
  if check!=old:raise ValueError('Non-caption row metadata changed')
 new_raw=replace_member(raw,[integration.INV],updated);ids={r['id'] for r in rows}
 if integration.unrelated_tokens(raw,REGISTRY,ids)!=integration.unrelated_tokens(new_raw,REGISTRY,ids):raise ValueError('Unrelated source registry token changed')
 validate_caption_binding(updated,proposal,require_full=True)
 receipt=copy.deepcopy(original);receipt['data_file_SHA256'][str(REGISTRY)]=sha(new_raw.encode())
 receipt.update(source_caption_full_exact_original_caption=True,complete_source_captions=13,previous_runtime_data_receipt=str(integration.ORIGINAL_RECEIPT),previous_runtime_data_receipt_sha256=integration.ORIGINAL_RECEIPT_SHA)
 receipt_raw=json.dumps(receipt,indent=2,ensure_ascii=False)+'\n'
 old_guard=json.loads((ROOT/FOLDER/'stroke-registry-additive-amendment-20261011.json').read_text());old_record=old_guard['files'][str(REGISTRY)]
 if digest(rows)!=old_record['current_semantic_SHA256'] or sha(raw[a:b].encode())!=old_record['current_raw_value_token_SHA256']:raise ValueError('Original strict guard row hashes differ')
 _,c,d=member(new_raw,[integration.INV])
 patch={'token_keys':old_record['token_keys'],'current_semantic_SHA256':digest(updated),'current_raw_value_token_SHA256':sha(new_raw[c:d].encode()),'prior_present':False}
 amendment={'reviewed_at':'2026-10-11','investigation_id':integration.INV,'module_id':integration.MODULE,'purpose':'Authenticated reader requires source_caption_full; add exactly the complete existing original_caption on all13 CTP rows.','source_decision':'Existing immutable CTP-only source GO; no new source or patient interpretation','frozen_original_evidence_SHA256':{str(FOLDER/n):h for n,h in OLD_PINS.items()},'primary_XML_path':str(XML),'primary_XML_SHA256':sha((ROOT/XML).read_bytes()),'current_data_receipt_path':str(integration.RECEIPT),'current_data_receipt_SHA256':sha(receipt_raw.encode()),'before_registry_SHA256':before[str(REGISTRY)],'after_registry_SHA256':sha(new_raw.encode()),'before_collection_semantic_SHA256':digest(rows),'after_collection_semantic_SHA256':digest(updated),'before_collection_raw_value_token_SHA256':old_record['current_raw_value_token_SHA256'],'after_collection_raw_value_token_SHA256':patch['current_raw_value_token_SHA256'],'original_guard_image_record':old_record,'caption_complete_guard_image_record':patch,'approved_image_ids':[integration.FIG(n) for n in range(1,14)],'added_field':'source_caption_full','only_caption_field_added':True,'other_four_data_files_SHA256_unchanged':{p:h for p,h in before.items() if p!=str(REGISTRY)},'all_unrelated_registry_value_tokens_unchanged':True,'source_pixels_or_original_caption_changed':False,'clinical_approval':False,'fine_anatomical_approval':False,'structure_coverage_granted':False,'patient_specific_3D_approved':False,'current_quiz_changed':False,'current_quiz_file_SHA256':'59808fe7a7ca20799338155aa5abcaa08c0e3e8335502f571171ca7c45e85e0a','caption_bindings':[{'id':r['id'],'figure_number':r['figure_number'],'exact_original_caption_SHA256':sha(r['original_caption'].encode()),'source_final_caption_exact':True,'primary_XML_caption_exact':True} for r in updated],'before_image_rows':rows,'caption_complete_image_rows':updated}
 if sha((ROOT/'data/curriculum/11-radiology.json').read_bytes())!=amendment['current_quiz_file_SHA256']:raise ValueError('Frozen current quiz changed')
 (ROOT/REGISTRY).write_text(new_raw);(ROOT/integration.RECEIPT).write_text(receipt_raw)
 (ROOT/AMENDMENT).write_text(json.dumps(amendment,indent=2,ensure_ascii=False)+'\n')
 integration.clear_catalog_caches();print(json.dumps({'complete_source_captions':13,'only_added_field':'source_caption_full','other_four_data_files_unchanged':True,'amendment_SHA256':sha((ROOT/AMENDMENT).read_bytes())}))
 return amendment
if __name__=='__main__':repair()
