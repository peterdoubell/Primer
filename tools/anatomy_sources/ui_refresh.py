"""Follow recorded UI-only refreshes of shared front-end files.

web/app.js and web/styles.css are bound by hash into independently reviewed
radiology presentation records. data/radiology/ui-presentation-refreshes.json
records changes to those two files that left every native presentation file
byte-identical. A check that compares a reviewed hash with the current file
asks `advance` for the hash the file is expected to have now. Only the two
refreshable paths ever advance; every other file stays bound to its reviewed
hash exactly.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / 'data/radiology/ui-presentation-refreshes.json'


def load():
    return json.loads(LEDGER.read_text())


def advance(path, reviewed_sha256, ledger=None):
    """The expected current hash of `path`, following the recorded refreshes in order."""
    ledger = ledger or load()
    if path not in ledger['refreshable_paths']:
        return reviewed_sha256
    current = reviewed_sha256
    for step in ledger['refreshes']:
        change = step['files'].get(path)
        if change and change['before'] == current:
            current = change['after']
    return current


def validate_source_case_citation_refresh(step):
    """A single exact citation-wrapper delta may advance shared app compatibility.

    A true presentation-code flag is candid here. Native decoder, mesh and CT
    renderer changes remain ineligible; every prior review/guarded file stays bound.
    """
    import hashlib
    expected_id = '2026-10-11-source-case-citation-wrapper'
    before = 'a8dc2985ad28ed9a9b07bd17f87857b3bc389feb7d316049f66ff8f3cf22d29d'
    after = 'd77de3b299fc8af358e6c5fd2c785b22f3a8f19aa89f27a713d40be7c22b11a0'
    path = 'docs/native-source-presentation-review-20261011/source-case-citation-compatibility-amendment-20261011.json'
    fingerprint = 'd239b53fef9d8456387dfb6fd628e20afdcd8a962d09cde455782d8ebec4d8b4'
    def sha(raw): return hashlib.sha256(raw).hexdigest()
    if (step.get('id') != expected_id or step.get('files') != {'web/app.js': {'before': before, 'after': after}}
            or step.get('native_presentation_code_touched') is not True
            or step.get('native_presentation_change_scope') != 'source_citation_wrapper_only'
            or step.get('native_decoder_mesh_CT_renderer_code_touched') is not False
            or step.get('new_explicit_metadata_field') != 'publication_url'
            or step.get('old_atlas_citation_fallback_unchanged') is not True
            or step.get('scoped_compatibility_amendment') != {'path': path, 'sha256': fingerprint}
            or any(step.get(k) is not False for k in ('clinical_approval', 'fine_anatomical_approval', 'reopens_or_extends_any_review'))):
        raise ValueError('Citation refresh leaves its exact reviewed scope')
    raw = (ROOT / path).read_bytes()
    if sha(raw) != fingerprint: raise ValueError('Citation compatibility evidence changed')
    proof = json.loads(raw)
    app = (ROOT / 'web/app.js').read_text()
    # A later exact, separately checked case-only bridge may retain this
    # historical wrapper proof. Roll back only its three recorded functions.
    from .pulmonary_ui_compatibility import AFTER as pulmonary_after, restore_previous_app
    if sha(app.encode()) != after:
        app = restore_previous_app(app)
    if (sha(app.encode()) != after or app.count(proof['after_function']) != 1
            or sha(app.replace(proof['after_function'], proof['before_function'], 1).encode()) != before
            or proof['native_decoder_mesh_CT_renderer_code_touched'] is not False
            or proof['app_bytes_outside_changed_function_identical'] is not True
            or proof['old_atlas_citation_fallback_unchanged'] is not True):
        raise ValueError('Shared app change is not exactly the recorded citation wrapper')
    if step['guarded_paths_sha256'] != proof['guarded_paths_sha256']:
        raise ValueError('Citation refresh changes guarded source bindings')
    for guarded, expected in proof['guarded_paths_sha256'].items():
        if sha((ROOT / guarded).read_bytes()) != expected: raise ValueError('Guarded native file changed')
    return proof
