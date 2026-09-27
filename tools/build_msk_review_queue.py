#!/usr/bin/env python3
"""Export every MSK requirement for review, without modifying claims or approvals."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.check_msk_fidelity import requirements_for, review_scope_fingerprint, KINDS


def candidate_artifacts(report, assets, root):
    """Read actual candidate bytes once; metadata equality is insufficient."""
    result = {}
    root = root.resolve()
    candidates = {identifier for row in report['requirements'] for identifier in row['candidates']}
    for identifier in sorted(candidates):
        asset = assets.get(identifier)
        if not asset or not isinstance(asset.get('local_path'), str):
            raise ValueError('Candidate has no local artifact: ' + identifier)
        path = (root / asset['local_path']).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('Candidate artifact missing or outside project: ' + identifier)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != asset.get('sha256'):
            raise ValueError('Candidate artifact changed: ' + identifier)
        dependencies = asset.get('presentation_dependencies', {})
        if not isinstance(dependencies, dict):
            raise ValueError('Invalid candidate presentation dependencies')
        for name, expected in dependencies.items():
            dependency = (root / name).resolve()
            if (not dependency.is_relative_to(root) or not dependency.is_file()
                    or hashlib.sha256(dependency.read_bytes()).hexdigest() != expected):
                raise ValueError('Candidate presentation dependency changed or missing: ' + identifier)
        result[identifier] = {'local_path': asset['local_path'], 'sha256': digest}
    return result


def export_queue(report, requirements, evidence, output, root=ROOT):
    assets = {a['id']: a for a in evidence['assets']}
    expected = {(i['investigation_id'], r['id'], k) for i in requirements['investigations']
                for r in requirements_for(i) for k in KINDS}
    observed = [(r['investigation_id'], r['structure_id'], r['kind']) for r in report['requirements']]
    if len(observed) != len(set(observed)) or set(observed) != expected:
        raise ValueError('Audit does not cover the exact current requirement scope')
    counts = Counter(r['status'] for r in report['requirements'])
    if set(counts) - {'verified', 'unverified', 'missing'} or any(
            counts[status] != report['counts'].get(status) for status in ('verified', 'unverified', 'missing')):
        raise ValueError('Audit counts do not match requirement rows')
    for identifier, asset in assets.items():
        if report['review_scope_sha256'].get(identifier) != review_scope_fingerprint(asset, requirements):
            raise ValueError('Stale review scope: ' + identifier)
    artifacts = candidate_artifacts(report, assets, root)
    output.mkdir(parents=True, exist_ok=True)
    index = ['# MSK clinical review queue', '',
             'This is an evidence index, not approval. Every image, schematic and model requirement remains in scope.',
             'Partial or unknown coverage cannot be approved as complete merely because the source looks correct.',
             'Review anatomical identity, full extent, side/population, modality, fidelity, source rights and the exact artifact before recording any decision.',
             'Changes must be made in the authoritative evidence ledger with actual reviewer identity, evidence and current fingerprints; this export does not import approvals.', '',
             '| Investigation | Verified | Unverified | Missing |', '|---|---:|---:|---:|']
    rows_by_key = dict(zip(observed, report['requirements']))
    files = []
    def safe(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    for inv in requirements['investigations']:
        ident = inv['investigation_id']
        if '/' in ident or '\\' in ident or ident in {'.', '..'}:
            raise ValueError('Invalid investigation filename')
        rows = [r for r in report['requirements'] if r['investigation_id'] == ident]
        counts = Counter(r['status'] for r in rows)
        filename = ident + '.md'
        index.append(f"| [{safe(inv['title'])}]({filename}) | {counts['verified']} | {counts['unverified']} | {counts['missing']} |")
        lines = ['# ' + inv['title'], '', 'Investigation: `' + ident + '`', '',
                 '## Reporting obligations', '']
        for item in inv['reporting_checklist']:
            lines.append('- **' + safe(item['label']) + ':** ' + safe(item['detail']))
        lines += ['', '## Requirement coverage', '', '| Structure | Clinical image | Schematic | Model | Conditions / modalities |', '|---|---|---|---|---|']
        for leaf in requirements_for(inv):
            statuses = [rows_by_key[(ident, leaf['id'], kind)]['status'] for kind in KINDS]
            lines.append('| ' + safe(leaf['name']) + ' (`' + leaf['id'] + '`) | ' + ' | '.join(statuses)
                         + ' | ' + safe(leaf['condition']) + ' / ' + safe(', '.join(leaf['modality_scope'])) + ' |')
        lines += ['', '## Candidate evidence', '']
        for row in rows:
            if not row['candidates']:
                continue
            lines += ['### ' + row['structure_id'] + ' — ' + row['kind'], '']
            for identifier, issues in row['candidates'].items():
                asset = assets[identifier]
                license_info = asset.get('source', {}).get('license', {})
                lines += ['- Asset: `' + identifier + '`',
                          '- Local file: [' + safe(asset.get('local_path', 'Unavailable')) + '](../../' + asset.get('local_path', '') + ')',
                          '- Artifact SHA-256: `' + asset.get('sha256', 'Unavailable') + '`',
                          '- Review-scope SHA-256: `' + report['review_scope_sha256'][identifier] + '`',
                          '- Source: [Original source](' + asset.get('source', {}).get('url', '') + ')',
                          '- Licence: [' + safe(license_info.get('name', 'Not recorded')) + '](' + license_info.get('url', '') + ')',
                          '- Recorded rights: commercial use=' + safe(license_info.get('commercial_use', 'unknown'))
                          + '; redistribution=' + safe(license_info.get('redistribution', 'unknown'))
                          + '; review status=' + safe(license_info.get('review_status', 'not recorded')),
                          '- Attribution: ' + safe(license_info.get('attribution', 'Not recorded')),
                          '- Rights evidence: ' + safe(license_info.get('evidence_path', 'Not recorded')),
                          '- Licence use plan: ' + safe(asset.get('license_use_plan', 'No separate use plan recorded; inspect the exact licence and rights evidence')),
                          '- Presentation dependencies: ' + safe(asset.get('presentation_dependencies', 'Not separately recorded')),
                          '- Coverage: ' + safe(asset.get('requirement_coverage', {}).get(row['structure_id'], {'extent': 'not recorded'})),
                          '- Selection: ' + safe(asset.get('representation_selection', 'Not recorded')),
                          '- Source context: ' + safe(asset.get('source_context', 'Not recorded')),
                          '- Limits: ' + safe(asset.get('limitations', asset.get('requirement_binding_scope', 'Not recorded'))),
                          '- Gate findings: ' + ', '.join(issues), '']
        lines += ['## Scope blockers', '']
        lines += ['- ' + safe(gap) for gap in report['scope_gaps'] if gap.startswith(ident + ':')]
        (output / filename).write_text('\n'.join(lines) + '\n')
        files.append({'investigation_id': ident, 'file': filename, 'requirements': len(rows), 'counts': dict(counts)})
    index += ['', '## Cross-module and specification blockers', '']
    identifiers = {i['investigation_id'] for i in requirements['investigations']}
    index += ['- ' + safe(gap) for gap in report['scope_gaps'] if gap.split(':', 1)[0] not in identifiers]
    (output / 'README.md').write_text('\n'.join(index) + '\n')
    for entry in files:
        entry['sha256'] = hashlib.sha256((output / entry['file']).read_bytes()).hexdigest()
    manifest = {'requirements': len(expected), 'counts': report['counts'], 'clinical_commercial_ready': report['clinical_commercial_ready'],
                'candidate_artifacts': artifacts, 'files': files}
    (output / 'index.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = export_queue(json.loads(args.audit.read_text()),
        json.loads((ROOT/'data/radiology/msk-structure-requirements.json').read_text()),
        json.loads((ROOT/'data/radiology/msk-asset-evidence.json').read_text()), args.output)
    print(f"Exported {result['requirements']} requirements across {len(result['files'])} investigations; no approvals changed.")
