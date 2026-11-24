"""Only literal side/class source matches become discoverable stroke context."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

import pytest
from primer import schirmer_territory_context as context
from primer import schirmer_vascular_reference as source
from primer.curriculum import Curriculum
from primer.radiology_catalog import detail, resolve
from tools import schirmer_navigation_compatibility as inverse
from tools.schirmer_runtime_compatibility import before_schirmer_reference_fields

ROOT = Path(__file__).resolve().parents[1]


def test_four_exact_stroke_parent_roles_are_context_with_no_requirement_bindings(monkeypatch):
    inventory_path = ROOT / 'data/radiology/non-msk-structure-requirements.json'
    inventory = json.loads(inventory_path.read_bytes())
    study = next(row for row in inventory['investigations'] if row['investigation_id'] == context.CASE)
    parents = {row['id']: row['name'] for row in study['structures']}
    assert all(parents[parent] == name for parent, name, _, _ in context.MATCHES)
    # Vercel excludes the authoring inventory from the deployed Python function.
    read_bytes = Path.read_bytes
    def bundled_read(path):
        if path == inventory_path:
            raise FileNotFoundError(path)
        return read_bytes(path)
    with monkeypatch.context() as hosted:
        hosted.setattr(Path, 'read_bytes', bundled_read)
        context.examples.cache_clear()
        examples = context.examples()
    assert [(row['requirement_parent_id'], row['source_code']) for row in examples] == [
        ('stroke.arterial_territory.ACA.left', 12), ('stroke.arterial_territory.ACA.right', 2),
        ('stroke.arterial_territory.PCA.left', 16), ('stroke.arterial_territory.PCA.right', 6)]
    for row in examples:
        assert row['evidence_role'] == 'source-study territory context'
        assert row['structure_coverage_granted'] is False
        assert row['src'] == source.PREFIX + 'index.html?code=' + str(row['source_code'])
    refs = source.references()
    assert 'source_territory_contexts' not in refs['ra.brain-anatomy'][0]
    assert refs[context.CASE][0]['source_territory_contexts'] == examples
    assert 19 not in {row['source_code'] for row in examples}
    assert all('required_parts' not in row and 'structure_bindings' not in row for row in examples)
    review = json.loads((ROOT / 'docs/schirmer-source-links-20261122/source-role-review.json').read_bytes())
    assert review['structure_bindings_added'] == 0
    assert review['source_value_19_interpreted'] is False
    assert [row['source_code'] for row in review['matches']] == [12, 2, 16, 6]
    assert all(any(part.endswith('.actual_tissue_extent_without_generic_territory_mask_claim')
                   for part in row['required_parts_retained_unbound']) for row in review['matches'])
    from tools.anatomy_sources.bind_biliary_duct_part import before_biliary_duct_part_record

    for path, record in review['unchanged_evidence_files'].items():
        raw = (ROOT / path).read_bytes()
        if path == 'data/radiology/radiology-asset-evidence.json':
            # The review of 2026-11-22 pins the ledger of its day; the record added on 2026-11-24 is peeled first.
            raw = before_biliary_duct_part_record(raw)
        assert len(raw) == record['bytes'] and hashlib.sha256(raw).hexdigest() == record['sha256']



def test_current_reporting_and_lesson_preserve_every_existing_source_and_historical_scope():
    curriculum = Curriculum()
    ref = detail(curriculum, resolve(context.CASE))['radiology_reference']
    inspector, = [row for row in ref['source_native_inspectors'] if row['id'] == source.IDENTIFIER]
    assert inspector['source_territory_contexts'] == context.examples()
    assert all(inspector[flag] is False for flag in source.FLAGS)
    projected = inverse.before_schirmer_navigation_reference_fields(context.CASE, ref)
    assert 'source_territory_contexts' not in next(row for row in projected['source_native_inspectors'] if row['id'] == source.IDENTIFIER)
    assert before_schirmer_reference_fields(context.CASE, ref) == before_schirmer_reference_fields(context.CASE, projected)
    lesson = curriculum.node(context.NODE)
    gallery, = [media for media in lesson['lesson_media'] if media.get('kind') == 'source-native-inspectors']
    assert context.CASE in gallery['investigation_ids']
    # The existing lesson gallery retrieves the current report descriptor on demand.
    assert 'source_territory_contexts' not in json.dumps(lesson)



@pytest.mark.parametrize('change', ['code', 'duplicate', 'role', 'coverage', 'wrong_case'])
def test_historical_field_projection_rejects_unreviewed_context_rows(change):
    fields = {'source_native_inspectors': deepcopy(source.references()[context.CASE]), 'observation': 'retained'}
    rows = fields['source_native_inspectors'][0]['source_territory_contexts']
    case = context.CASE
    if change == 'code': rows[0]['source_code'] = 14
    elif change == 'duplicate': rows.append(deepcopy(rows[0]))
    elif change == 'role': rows[0]['evidence_role'] = 'actual patient tissue extent'
    elif change == 'coverage': rows[0]['structure_coverage_granted'] = True
    else: case = 'ra.brain-anatomy'
    with pytest.raises(ValueError, match='Unreviewed'):
        inverse.before_schirmer_navigation_reference_fields(case, fields)


def test_exact_inverse_restores_only_reviewed_five_files_and_checks_its_proof(tmp_path, monkeypatch):
    proof = inverse.PROOF.read_bytes()
    assert hashlib.sha256(proof).hexdigest() == inverse.PIN
    for path, row in json.loads(proof).items():
        from tools.segthy_runtime_compatibility import before_segthy_bytes
        raw = before_segthy_bytes(path, (ROOT / path).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == row['after']
        restored = inverse.before_schirmer_navigation_bytes(path, raw)
        assert hashlib.sha256(restored).hexdigest() == row['before']
        assert inverse.before_schirmer_navigation_bytes(path, restored) == restored
        assert inverse.before_schirmer_navigation_bytes(path, raw + b'foreign') == raw + b'foreign'
    assert inverse.before_schirmer_navigation_bytes('unrelated', b'exact') == b'exact'
    target = tmp_path / 'proof.json'; target.write_bytes(proof + b'\n')
    monkeypatch.setattr(inverse, 'PROOF', target)
    with pytest.raises(ValueError, match='evidence changed'):
        inverse.before_schirmer_navigation_bytes('web/app.js', (ROOT / 'web/app.js').read_bytes())


def test_query_selection_refuses_unknown_ambiguous_or_nonliteral_source_codes():
    js = (ROOT / 'web/anatomy/schirmer-vascular/viewer.js').read_text()
    start = js.index('const sourceLink=')
    stop = js.index('populateGroups();populateStructures();windowDefaults();', start)
    script = '''const assert=require('assert/strict'),vm=require('vm');
const block=JSON.parse(process.argv[1]);
for(const [query,expected] of [['',2],['?code=12',12],['?code=19',19],['?code=20',20]]){
 const c={URLSearchParams,location:{search:query},labels:{sourceClasses:[2,4,6,8,10,12,14,16,18,19,20].map(code=>({code}))},state:{code:2}};
 vm.runInNewContext(block,c);assert.equal(c.state.code,expected);
}
for(const query of ['?code=13','?code=0','?code=','?code=02','?code=2.0','?code=2&code=12','?code=ACA','?code=-2']){
 const c={URLSearchParams,location:{search:query},labels:{sourceClasses:[{code:2},{code:12}]},state:{code:2}};
 assert.throws(()=>vm.runInNewContext(block,c),/Unknown source region link/);
}'''
    run = subprocess.run(['node', '-e', script, json.dumps(js[start:stop])], text=True, capture_output=True)
    assert run.returncode == 0, run.stdout + run.stderr
