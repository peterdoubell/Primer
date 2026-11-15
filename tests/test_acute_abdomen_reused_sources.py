"""Reused source references preserve original identity/context without inheriting clinical coverage."""
import copy
import hashlib
import json
from pathlib import Path
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools.anatomy_sources.package_acute_abdomen_references import SELECTION, digest

ROOT=Path(__file__).resolve().parents[1]


def test_all_twelve_references_keep_exact_original_files_and_source_records():
    images=json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text())
    rows={r['source_reuse']['original_asset_id']:r for r in images['ra.acute-abdomen']}
    assert len(rows)==12
    proof=json.loads((ROOT/'docs/acute-abdomen-reused-source-review/source-reuse-evidence.json').read_text())
    assert not proof['new_physical_image_files_created'] and not proof['structure_coverage_granted']
    for source,ids in SELECTION.items():
        original={r['id']:r for r in images[source]}
        for ident in ids:
            row=copy.deepcopy(rows[ident]);reuse=row.pop('source_reuse');row['id']=ident
            assert row==original[ident]
            assert reuse['original_investigation_id']==source and reuse['original_source_record_sha256']==digest(row)
            assert hashlib.sha256((ROOT/'web'/row['src'].removeprefix('/app/')).read_bytes()).hexdigest()==row['sha256']
            assert reuse['same_physical_file'] and not reuse['source_pixels_or_context_changed']
            assert not reuse['shared_patient_or_exam_inferred'] and not reuse['structure_coverage_granted']


def test_normal_partial_appendix_and_mri_projection_contexts_are_not_relabelled():
    ref=detail(Curriculum(),resolve('ra.acute-abdomen'))['radiology_reference']
    rows={r['source_reuse']['original_asset_id']:r for r in ref['structure_atlas']}
    assert rows['open-appendix-mostbeck-2016-fig1']['source_context']['depicted_state']=='normal_anatomy'
    assert rows['open-appendix-mostbeck-2016-fig2']['source_context']['depicted_state']=='acute_appendicitis'
    paired=rows['open-appendix-mostbeck-2016-fig3']
    assert paired['modality']=='CT' and paired['source_context']['selected_panels']==['b']
    assert paired['source_context']['panel_types']=={'a':'Ultrasound','b':'CT'}
    assert '0.3 cm' in rows['open-appendix-mostbeck-2016-fig1']['caption']
    assert 'not a complete native duct volume' in rows['open-cbd-stone-pmc12463306-fig3']['caption']
    assert rows['open-bowel-wall-pmc3999365-fig6']['license']=='CC BY 2.0'
    assert len(ref['structure_atlas'])==12


def test_step_links_are_complete_and_existing_source_bindings_do_not_transfer():
    ref=detail(Curriculum(),resolve('ra.acute-abdomen'))['radiology_reference']
    assert {i for s in ref['walkthrough']['steps'] for i in s['images'] if i.startswith('open-acute-abdomen-ref-')}=={r['id'] for r in ref['structure_atlas']}
    assert not ref['walkthrough']['steps'][4]['images']
    evidence=json.loads((ROOT/'data/radiology/radiology-asset-evidence.json').read_text());assets={r['id']:r for r in evidence['assets']}
    for row in ref['structure_atlas']:
        candidate=assets[row['id']];original=assets[row['source_reuse']['original_asset_id']]
        assert candidate['structure_ids']==[] and candidate['requirement_coverage']=={}
        assert candidate['anatomical_review']['status']=='pending'
        assert candidate['source_context']==original['source_context']
        assert candidate['source']==original['source'] and candidate['investigation_ids']==['ra.acute-abdomen']
        rights=candidate['source']['license']
        assert rights['review_status']=='verified' and rights['commercial_use'] and rights['redistribution']
        assert hashlib.sha256((ROOT/rights['evidence_path']).read_bytes()).hexdigest()==rights['evidence_sha256']
    source=assets['open-appendix-mostbeck-2016-fig1']
    assert source['structure_ids'] and all(v['extent']=='partial' for v in source['requirement_coverage'].values())
