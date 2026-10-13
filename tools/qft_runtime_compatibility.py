"""Bounded offline historical proof views; no runtime or approval rebaseline."""
from pathlib import Path
import hashlib
import json
from tools.qft_evidence_storage import relocated_evidence_bytes
from tools.pulmonary_runtime_compatibility import restore_main_runtime_bytes

ROOT=Path(__file__).resolve().parents[1]
FILES={'primer/server.py': {'baseline_copy': 'docs/physics-qft-integrated-reader-review-20261011/pr134-historical-runtime/primer__server.py', 'baseline_sha256': 'c1ef46900f09553c8bcebaa020d4f9f004352724ea9c1f15307273fb62d93fd0', 'current_sha256': '8c0071159fa528ce1b5453d18dc2357663e349b0edf02dd6a54a42c90723a906'}, 'primer/module_media.py': {'baseline_copy': 'docs/physics-qft-integrated-reader-review-20261011/pr134-historical-runtime/primer__module_media.py', 'baseline_sha256': 'c561382a38b38d4c259e4a32a1a785e801d20d45ce69d2263f6b7ca56a64475f', 'current_sha256': '078861258791477395df54b3b1135a121187a47379416141d54d258f12ceb1f1'}, 'web/index.html': {'baseline_copy': 'docs/physics-qft-integrated-reader-review-20261011/pr134-historical-runtime/web__index.html', 'baseline_sha256': '41b5b72f6bfaeebc8d987b38f04491d6b6744643314377b8ec2518cf18338eb9', 'current_sha256': 'db4b20a758453f29b96d891efefb91dea499e7beb20532a61e6a20d88cae8404'}, 'web/lesson-state.js': {'baseline_copy': 'docs/physics-qft-integrated-reader-review-20261011/pr134-historical-runtime/web__lesson-state.js', 'baseline_sha256': '837cea8445bb6d0ac4c943e0b78cd919ac07a5569cad5ac58e99086da3a4674f', 'current_sha256': '947708921588aeaad0fb186e08a09cfb6cc4bb5c143318f3d36ad84a2f447139'}, 'web/spatial-module-objects.js': {'baseline_copy': 'docs/physics-qft-integrated-reader-review-20261011/pr134-historical-runtime/web__spatial-module-objects.js', 'baseline_sha256': '3ff2e3a28e38d65b755f2977c2c25167f7c5cd4c8a4e95491b45a0ed8b1b362d', 'current_sha256': 'ca8cbf328cc1c38e3fc89826d72f47e0e72f3abb1fe6ffbb70889b923ea974fe'}, 'web/spatial-models.js': {'baseline_copy': 'docs/physics-qft-integrated-reader-review-20261011/pr134-historical-runtime/web__spatial-models.js', 'baseline_sha256': '21dd37ae78eef1a15a25d75e3eca4211bd1e7383482f0b4feb51f6da54d3bffb', 'current_sha256': 'd16b25a18d59a79cb5d9f94c5573c486f19d01099d7ced70d74b4ecee0e20136'}, 'web/lesson-models.js': {'baseline_copy': 'docs/physics-qft-integrated-reader-review-20261011/pr134-historical-runtime/web__lesson-models.js', 'baseline_sha256': 'd7268996aa06b8675f2ff831046f5067b876da1c5ac83f5f98a9119456a945be', 'current_sha256': '2ac415278e51eb56cbc183e97f67f2371ad66082177a7a0fd79efc988c251c50'}, 'data/curriculum/03-physics.json': {'baseline_copy': 'docs/physics-qft-integrated-reader-review-20261011/pr134-historical-runtime/data__curriculum__03-physics.json', 'baseline_sha256': '366985f456bedffe10684e05a70db9e3e5e4b8ba37edba6f0dd9be94aeb2fadc', 'current_sha256': '5fec2b6e611cd32b64a0532daa507ec1bee2d157e8a8e1b9e879702fd60060ea'}, 'data/module-models.json': {'baseline_copy': 'docs/physics-qft-integrated-reader-review-20261011/pr134-historical-runtime/data__module-models.json', 'baseline_sha256': 'b5a30978115e78482fca0eefc8a3d39bd4a20f7f151e606b2cc582156a6e96d3', 'current_sha256': '20d2fcd58a6367b09fc2bfcfe97f0685a65c4dbbfe5f1d15612588ce1ac10210'}, 'tests/test_maxwell_cosmology_independent.py': {'baseline_copy': 'docs/physics-qft-integrated-reader-review-20261011/pr134-historical-runtime/tests__test_maxwell_cosmology_independent.py', 'baseline_sha256': 'baac9998d93d3ad7922f7082886b8984561449709a9cced4734e7b96ee91d461', 'current_sha256': '3b6aeef8914a74696aea82180db58ddea76b068c251e75dcd96ee27cc304c31e'}}

def historical_runtime_bytes(relative, current):
    """Preserve only the exact PR134/current-QFT artifact pairs named below.

    Original receipts prove historical bytes. Current science/reader proofs
    separately validate the new behavior; this helper grants no approval.
    """
    from tools.thoracic_data_compatibility import restore_raw
    from tools.anatomy_sources.radiology_presentation_compatibility import restore_presentation_bytes
    current = restore_presentation_bytes(relative, current)
    current=restore_raw(relative,current,allow_historical=True)
    try:
        current=restore_main_runtime_bytes(relative,current)
    except ValueError as error:
        raise ValueError("Unreviewed QFT compatibility byte change: "+str(error)) from error
    row=FILES.get(relative)
    if row is None:
        return current
    digest=lambda data:hashlib.sha256(data).hexdigest()
    baseline=(relocated_evidence_bytes(row['baseline_copy'],row['baseline_sha256'])
              if relative=='primer/server.py' else (ROOT/row['baseline_copy']).read_bytes())
    if digest(baseline)!=row['baseline_sha256']:
        raise ValueError('Historical QFT compatibility source changed')
    if digest(current)==row['baseline_sha256']:
        return current
    if digest(current)!=row['current_sha256']:
        raise ValueError('Unreviewed QFT compatibility byte change')
    if relative in {'data/curriculum/03-physics.json','data/module-models.json'}:
        old,new=json.loads(baseline),json.loads(current)
        key='nodes' if 'curriculum/' in relative else 'models'
        identity='id' if key=='nodes' else 'node_id'
        old_rows={row[identity]:row for row in old[key]}
        new_rows={row[identity]:row for row in new[key]}
        if set(old_rows)!=set(new_rows) or any(new_rows[k]!=v for k,v in old_rows.items() if k!='phys.5.qft'):
            raise ValueError('Unrelated physics/binding change in QFT compatibility view')
        if {k:v for k,v in old.items() if k!=key}!={k:v for k,v in new.items() if k!=key}:
            raise ValueError('Unrelated physics/binding metadata change')
    return baseline
