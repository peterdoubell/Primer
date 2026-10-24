"""Exact pre-expansion byte view; historical approvals never cover new reports.

This receipt isolates the reporting renderer, deterministic composer, reporting-only
catalogue exposure and package exclusions. Neither this inverse nor an unchanged native presentation ledger is
clinical validation of report content, repeated lesions or calculator bindings.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = 'docs/all-reporting-release-20261023/runtime-inverse.json'
PROOF_SHA256 = '7a6f1ea3c6f10b06908412e9af3cb4b43127c587a6ed4f7c45d2f12223dbb8a6'
BASE_COMMIT = 'fd43c37003a7e894df350bf6b551bd000ba35677'
PATHS = frozenset({'.vercelignore', 'primer/descriptor_reporting.py',
                   'primer/reporting_bridge.py', 'primer/server.py',
                   'web/radiology-structured.js', 'web/radiology-structured.css'})
ADDED_PATHS = frozenset({'primer/descriptor_calculations.py'})
UNCHANGED_PATHS = frozenset({'web/app.js', 'web/styles.css',
                            'data/radiology/ui-presentation-refreshes.json'})
FLAGS = ('clinical_approval', 'fine_anatomical_approval', 'extends_historical_approval',
         'native_decoder_mesh_CT_renderer_code_touched', 'canonical_lesson_data_changed',
         'new_reporting_workflow_validated_by_this_inverse', 'clinical_content_validated_by_this_inverse')
SCOPE = 'all_anatomic_reporting_controls_composition_catalogue_and_packaging_only'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed():
    raw = (ROOT / PROOF).read_bytes()
    if sha(raw) != PROOF_SHA256:
        raise ValueError('All-report compatibility evidence changed')
    proof = json.loads(raw)
    from tools.msk_report_compatibility import reviewed as msk_reviewed
    prior = msk_reviewed()
    if (set(proof['files']) != PATHS
            or set(proof['added_files_sha256']) != ADDED_PATHS
            or set(proof['unchanged_runtime_sha256']) != UNCHANGED_PATHS
            or proof['base_commit'] != BASE_COMMIT
            or proof['scope'] != SCOPE
            or proof['ui_presentation_ledger_changed'] is not False
            or proof['guarded_paths_sha256'] != prior['guarded_paths_sha256']
            or proof['canonical_contract_files_sha256'] != prior['canonical_contract_files_sha256']
            or any(proof[key] is not False for key in FLAGS)):
        raise ValueError('All-report inverse leaves its exact scope')
    return proof


def before_all_reports_bytes(path, raw, allow_older=False):
    """Undo only the hash-bound expansion; retain unrelated or historical bytes.

    Permissive passthrough is solely for older chained receipts, which must still
    check their own before/after hashes. It never transforms an unknown delta.
    """
    path = str(path)
    if path not in PATHS:
        return raw
    row = reviewed()['files'][path]
    if sha(raw) == row['before_sha256']:
        return raw
    if sha(raw) != row['after_sha256']:
        if allow_older:
            return raw
        raise ValueError('Unreviewed all-report runtime byte change')
    lines = raw.decode().splitlines(keepends=True)
    for change in reversed(row['changes']):
        if ''.join(lines[change['start']:change['end']]) != change['after']:
            raise ValueError('All-report inverse literal differs')
        lines[change['start']:change['end']] = change['before'].splitlines(keepends=True)
    restored = ''.join(lines).encode()
    if sha(restored) != row['before_sha256']:
        raise ValueError('All-report inverse changes unrelated baseline bytes')
    return restored


def validate_current():
    """Check this release separately; do not fabricate a UI-ledger transition."""
    proof = reviewed()
    for path, row in proof['files'].items():
        raw = (ROOT / path).read_bytes()
        if (sha(raw) != row['after_sha256']
                or sha(before_all_reports_bytes(path, raw)) != row['before_sha256']):
            raise ValueError('All-report current runtime differs')
    for path, expected in proof['added_files_sha256'].items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('All-report added runtime differs')
    for path, expected in {**proof['unchanged_runtime_sha256'], **proof['guarded_paths_sha256'],
                           **proof['canonical_contract_files_sha256']}.items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('All-report release changes an unchanged or guarded source file')
    return proof
