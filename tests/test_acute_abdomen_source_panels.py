"""Named source panels reach their actual report/anatomy targets without granting completion."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess

from tools import acute_abdomen_panels_compatibility as history
from tools.anatomy_sources import build_acute_abdomen_source_panels as package
from tools.check_msk_fidelity import inspect_binding, inspect_requirement_coverage, requirements_for

ROOT = Path(__file__).resolve().parents[1]


def records():
    manifest = json.loads((ROOT / package.MANIFEST).read_text())
    raw = (ROOT / package.EVIDENCE).read_bytes()
    current = json.loads(raw)
    previous = json.loads(history.before_acute_panel_evidence(raw))
    inventory = json.loads((ROOT / 'data/radiology/non-msk-structure-requirements.json').read_text())
    investigation, = [row for row in inventory['investigations'] if row['investigation_id'] == package.EXAM]
    return manifest, current, previous, investigation


def test_all_preserved_figure_pixels_context_and_rights_survive_the_new_partial_bindings():
    manifest, current, previous, _ = records()
    old = {row['id']: row for row in previous['assets']}
    new = {row['id']: row for row in current['assets']}
    assert len(manifest['figures']) == 12 and len(manifest['panels']) == 17
    figure_ids = {row['id'] for row in manifest['figures']}
    image_pairs = 0
    for identifier in figure_ids:
        candidate = copy.deepcopy(new[identifier])
        candidate['structure_ids'] = old[identifier]['structure_ids']
        candidate['requirement_coverage'] = old[identifier]['requirement_coverage']
        assert candidate == old[identifier]
        assert candidate['source_reuse']['structure_coverage_granted'] is False
        assert candidate['source_reuse']['shared_patient_or_exam_inferred'] is False
        assert candidate['anatomical_review']['status'] == 'pending'
        assert candidate.get('fidelity') != 'high'
        assert hashlib.sha256((ROOT / candidate['local_path']).read_bytes()).hexdigest() == candidate['sha256']
        rights = candidate['source']['license']
        assert hashlib.sha256((ROOT / rights['evidence_path']).read_bytes()).hexdigest() == rights['evidence_sha256']
        assert rights['review_status'] == 'verified' and rights['commercial_use'] and rights['redistribution']
        image_pairs += len(new[identifier]['structure_ids'])
    assert image_pairs == 39
    assert new['open-acute-abdomen-ref-bowel-wall-pmc3999365-fig6']['source']['license']['name'] == 'CC BY 2.0'
    assert {key: value for key, value in current.items() if key != 'assets'} == {key: value for key, value in previous.items() if key != 'assets'}
    assert all(new[identifier] == row for identifier, row in old.items() if identifier not in figure_ids)


def test_each_binding_is_a_compatible_leaf_and_stays_partial_with_its_source_state():
    manifest, current, _, investigation = records()
    leaves = {row['id']: row for row in requirements_for(investigation)}
    assert len(investigation['structures']) == 102 and len(leaves) == 724
    assert manifest['inventory_counts'] == {'parent_structures': 102, 'required_leaves': 724}
    candidates = [row for row in current['assets'] if row['investigation_ids'] == [package.EXAM]]
    assert len(candidates) == 14
    pairs = 0
    for candidate in candidates:
        for identifier in candidate['structure_ids']:
            assert identifier in leaves
            assert inspect_binding(candidate, leaves[identifier]) == []
            assert inspect_requirement_coverage(candidate, leaves[identifier]) == ['requirement_coverage_partial']
            assert candidate['anatomical_review']['status'] == 'pending'
            pairs += 1
    assert pairs == 41 and len(manifest['targets']) == 23
    normal = next(row for row in candidates if row['id'].endswith('mostbeck-2016-fig1'))
    assert normal['source_context']['depicted_state'] == 'normal_anatomy'
    assert 'source_context_purpose_mismatch' in inspect_binding(normal, leaves['acute_abdomen.bowel_observations.appendix_abnormal_region'])
    assert not manifest['clinical_approval'] and not manifest['requirement_completion_granted']


def test_mixed_panels_caption_uncertainty_and_panel_rectangles_are_not_reinterpreted():
    manifest, current, _, _ = records()
    figures = {row['id']: row for row in manifest['figures']}
    assets = {row['id']: row for row in current['assets']}
    for panel in manifest['panels']:
        figure = figures[panel['figure_id']]
        x, y, width, height = panel['panel_bounds']
        assert min(x, y) >= 0 and min(width, height) > 0
        assert x + width <= figure['width'] and y + height <= figure['height']
        assert 'not an anatomical boundary' in panel['bounds_meaning']
        if panel['bindings']:
            selected = figure['source_context'].get('selected_panels') or ['whole']
            assert panel['source_panel'] in selected
            assert panel['modality'] == assets[figure['id']]['modality']
    ultrasound, = [row for row in manifest['panels'] if row['id'] == 'appendix-mostbeck-2016-fig3-a']
    assert ultrasound['modality'] == 'Ultrasound' and ultrasound['bindings'] == []
    mixed = figures['open-acute-abdomen-ref-appendix-mostbeck-2016-fig3']
    assert mixed['default_panel'] == 'b' and mixed['source_context']['selected_panels'] == ['b']
    calculus = 'acute_abdomen.solid_observations.calculus_or_obstructing_interface_if_supported'
    for number in (1, 3):
        identifier = 'open-acute-abdomen-ref-cbd-stone-pmc12463306-fig' + str(number)
        assert 'suggestive' in figures[identifier]['caption_full']
        assert calculus not in assets[identifier]['structure_ids']
    assert 'Muscle-star correspondence is unresolved' in manifest['panels'][0]['observation']


def test_the_two_native_candidates_keep_the_original_model_bytes_and_lumen_scope():
    manifest, current, previous, _ = records()
    old = {row['id']: row for row in previous['assets']}
    new = {row['id']: row for row in current['assets']}
    assert len(manifest['native_references']) == 2 and len(new) == len(old) + 2
    for source in manifest['native_references']:
        candidate = new['acute-abdomen-' + source['id']]
        original = old[candidate['source_reuse']['original_asset_id']]
        assert candidate['kind'] == 'model' and len(candidate['structure_ids']) == 1
        assert candidate['structure_ids'][0].endswith('.lumen_if_resolved')
        assert candidate['source'] == original['source'] and candidate['geometry'] == original['geometry']
        assert candidate['source_context'] == original['source_context']
        assert candidate['visual_review'] == original['visual_review']
        assert hashlib.sha256((ROOT / candidate['local_path']).read_bytes()).hexdigest() == candidate['sha256'] == original['sha256']
        mesh = gzip.decompress((ROOT / candidate['local_path']).read_bytes())
        assert len(mesh) == 12 * (candidate['geometry']['vertices'] + candidate['geometry']['triangles'])
        assert source['case_group'] == 'ColonVessels-pat_012-separate-case'
        assert source['reader_url'].endswith(('segment=3:1', 'segment=1:11'))


def test_generated_map_and_professional_row_links_match_the_reviewed_source_and_rows():
    manifest = json.loads((ROOT / package.MANIFEST).read_text())
    generated, _, _ = package.build()
    assert manifest == generated
    assert len(manifest['report_rows']) == 9
    script = (ROOT / 'web/radiology-structured.js').read_text()
    encoded, = re.findall(r'  const ACUTE_SOURCE_ROWS = (.*?);\n', script)
    registry = json.loads(encoded)
    assert registry == {row['id']: {'target': row['target_id'], 'label': row['link_label']} for row in manifest['report_rows']}
    panels = {row['id']: row for row in manifest['panels']}
    for row in manifest['report_rows']:
        assert row['target_id'] in {target['id'] for target in manifest['targets']}
        assert all(any(binding['target_id'] == row['target_id'] for binding in panels[identifier]['bindings']) for identifier in row['panels'])
    sigmoid = next(row for row in manifest['report_rows'] if row['id'] == 'anatomy-sigmoid-colon')
    assert set(sigmoid['panels']) == {'bowel-wall-pmc3999365-fig6-whole', 'appendix-mostbeck-2016-fig3-b'}
    # Unspecified small-bowel loops must not become a source labelled jejunum or ileum.
    assert not {'anatomy-jejunum', 'anatomy-proximal-ileum'} & set(registry)
    reader = (ROOT / 'web/radiology/acute-abdomen-panels/lab.js').read_text()
    assert hashlib.sha256((ROOT / package.MANIFEST).read_bytes()).hexdigest() in reader


def test_exact_inverse_retains_foreign_edits_and_the_locator_keeps_all_original_rows():
    from tools.ct_torso_compatibility import before_torso_bytes
    raw = history.PROOF.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == history.PIN
    for path, entry in json.loads(raw).items():
        current = before_torso_bytes(path, history.before_liver_row_sources(path, (ROOT / path).read_bytes()))
        assert hashlib.sha256(current).hexdigest() == entry['after']
        before = history.before_acute_panel_bytes(path, current)
        assert hashlib.sha256(before).hexdigest() == entry['before']
        assert history.before_acute_panel_bytes(path, current + b'\n') == current + b'\n'
        assert history.before_acute_panel_bytes(path, before) == before
    path = str(package.LOCATOR)
    before = json.loads(history.before_acute_panel_bytes(path, (ROOT / path).read_bytes()))
    current = json.loads((ROOT / path).read_bytes())
    assert current['counts'] == before['counts']
    assert [{key: value for key, value in row.items() if key != 'source_panels'} for row in current['structures']] == before['structures']
    assert len(current['structures']) == 102 and current['source_panel_rows'] == 10
    source = """
const assert=require('node:assert/strict'),L=require('./web/radiology/structure-atlas/lab.js');
const row={name:'Appendix',source_panels:[{target_name:'Appendix: lumen',label:'Figure 2 · a · Ultrasound'}]};
assert.equal(L.visible(row,'LUMEN',true),true);
assert.equal(L.visible({name:'Appendix'},'',true),false);
assert.ok(L.panelUrl('/app/radiology/acute-abdomen-panels/index.html?target=acute_abdomen.appendix.lumen&panel=appendix-mostbeck-2016-fig2-a'));
assert.equal(L.panelUrl('https://example.com/source'),null);
"""
    result = subprocess.run(['node', '-e', source], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
