"""Fixed inert historical bytes; never imports or evaluates copied source."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
BASELINES={'vercel.json': {'file': 'docs/pulmonary-release-integration-review-20261012/source-delivery-baselines/vercel.json.txt', 'sha256': 'eec673997c205cf346461b71485fb7335982e6de191428c882db1cf84dfca684', 'bytes': 41494}, 'data/radiology/native-source-delivery.json': {'file': 'docs/pulmonary-release-integration-review-20261012/source-delivery-baselines/data/radiology/native-source-delivery.json.txt', 'sha256': 'da4cf26352796ebfcc920d31823d45edeb830d58bf6b9aea08c2477ab0781e75', 'bytes': 5199}, 'data/radiology/native-source-inspectors.json': {'file': 'docs/pulmonary-release-integration-review-20261012/source-delivery-baselines/data/radiology/native-source-inspectors.json.txt', 'sha256': '8e73e9f64d64eceffb800a30330d7bcb88ed49d12ffcb145bcf7a2001fb8e9de', 'bytes': 1983}, 'data/radiology/acute-stroke-source-delivery.json': {'file': 'docs/pulmonary-release-integration-review-20261012/source-delivery-baselines/data/radiology/acute-stroke-source-delivery.json.txt', 'sha256': '5dd069f8237dc81aed27d421bfab395da5aefc0c3fb9a3edd915675a114234a2', 'bytes': 36846}, 'data/radiology/soop-native-inspector.json': {'file': 'docs/pulmonary-release-integration-review-20261012/source-delivery-baselines/data/radiology/soop-native-inspector.json.txt', 'sha256': '449ac4b15f9b9104bb35da36e2441571bca458a8947b874eeb1b87034b39c13e', 'bytes': 2495}, 'primer/stroke_source_delivery.py': {'file': 'docs/pulmonary-release-integration-review-20261012/source-delivery-baselines/primer/stroke_source_delivery.py.txt', 'sha256': 'e37562d5d24c5b70d05e405d8d56f8db0b056751a3e1ee7d0b71a264beeaf8e0', 'bytes': 7182}, 'primer/stroke_native_inspectors.py': {'file': 'docs/pulmonary-release-integration-review-20261012/source-delivery-baselines/primer/stroke_native_inspectors.py.txt', 'sha256': '9a968a449890a0bb5540f1688a799d2b07e8b759d3dc75fd753d9ab6fe5804dd', 'bytes': 8628}}

def read_baseline(name):
    if name not in BASELINES:
        raise ValueError('Unknown pulmonary source baseline')
    row=BASELINES[name];relative=Path(row['file']);path=ROOT
    for part in relative.parts:
        path=path/part
        if path.is_symlink():
            raise ValueError('Pulmonary baseline cannot be a symlink')
    if not path.is_file() or not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Pulmonary baseline must be a fixed regular file')
    raw=path.read_bytes()
    if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
        raise ValueError('Pulmonary historical baseline bytes changed')
    return raw
