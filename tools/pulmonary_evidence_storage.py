"""Read exact relocated pulmonary baseline evidence as data; never evaluate it."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
RELOCATIONS={'docs/pulmonary-nodule-integration-review-20261011/baseline/primer/module_media.py': {'data_path': 'docs/pulmonary-nodule-integration-review-20261011/baseline/primer/module_media.py.txt', 'sha256': 'c561382a38b38d4c259e4a32a1a785e801d20d45ce69d2263f6b7ca56a64475f', 'bytes': 6889}, 'docs/pulmonary-nodule-integration-review-20261011/baseline/primer/radiology.py': {'data_path': 'docs/pulmonary-nodule-integration-review-20261011/baseline/primer/radiology.py.txt', 'sha256': '0f916341c045ac77d86593025315972a977500a48a0534c497bf2076175d14ec', 'bytes': 17751}, 'docs/pulmonary-nodule-integration-review-20261011/baseline/primer/radiology_catalog.py': {'data_path': 'docs/pulmonary-nodule-integration-review-20261011/baseline/primer/radiology_catalog.py.txt', 'sha256': 'f0dd76a325682456bbfae06c614d4942dd114ca8103a2aad91d7dbd177ea60dd', 'bytes': 73858}, 'docs/pulmonary-nodule-integration-review-20261011/baseline/web/app.js': {'data_path': 'docs/pulmonary-nodule-integration-review-20261011/baseline/web/app.js.txt', 'sha256': 'd77de3b299fc8af358e6c5fd2c785b22f3a8f19aa89f27a713d40be7c22b11a0', 'bytes': 420354}, 'docs/pulmonary-nodule-integration-review-20261011/baseline/web/lesson-models.js': {'data_path': 'docs/pulmonary-nodule-integration-review-20261011/baseline/web/lesson-models.js.txt', 'sha256': 'd7268996aa06b8675f2ff831046f5067b876da1c5ac83f5f98a9119456a945be', 'bytes': 332665}}

def historical_evidence_bytes(historical_path, expected_sha256):
    row=RELOCATIONS.get(historical_path)
    if row is None or expected_sha256!=row['sha256']:
        raise ValueError('Unknown pulmonary historical evidence path or SHA256')
    relative=Path(row['data_path']);target=ROOT/relative
    if any((ROOT/Path(*relative.parts[:i])).is_symlink() for i in range(1,len(relative.parts)+1)) or not target.is_file():
        raise ValueError('Historical pulmonary evidence data unavailable or symlink')
    raw=target.read_bytes()
    if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
        raise ValueError('Historical pulmonary evidence data changed')
    return raw
