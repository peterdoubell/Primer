"""Fixed offline union views; no source, clinical or historical approval waiver."""
import hashlib
import json
from pathlib import Path
from tools.systems_runtime_compatibility import previous_runtime_bytes
ROOT=Path(__file__).resolve().parents[1]
PRODUCT_PROOF='docs/number-theory-integrated-release-review-20261012/shared-product-inverses.json'
PRODUCT_SHA256='f7cd4dab45b9dc2c78797029aaf062cead49c2802eafe5db699a328134e4e98b'
TEST_PROOF='docs/number-theory-integrated-release-review-20261012/test-source-inverses.json'
TEST_SHA256='c134d177e4ab33a6a23a4adb6b3fe8b7041cef7d78684db3f102b0ab20390b94'


def product_view(relative,raw,view):
    raw=previous_runtime_bytes(relative,raw)
    evidence=(ROOT/PRODUCT_PROOF).read_bytes()
    if hashlib.sha256(evidence).hexdigest()!=PRODUCT_SHA256:
        raise ValueError('Number theory union inverse evidence changed')
    proof=json.loads(evidence)
    if view not in {'pulmonary_views','math_views'}:
        raise ValueError('Unknown historical union view')
    row=proof[view].get(relative)
    if row is None:
        return raw
    digest=hashlib.sha256(raw).hexdigest()
    if digest==row['baseline_sha256']:
        return raw
    if digest!=row['current_sha256']:
        raise ValueError('Unreviewed number theory union byte change')
    text=raw.decode()
    for change in row['changes']:
        if text.count(change['after'])!=1:
            raise ValueError('Number theory union lacks its unique literal change')
        text=text.replace(change['after'],change['before'],1)
    restored=text.encode()
    if hashlib.sha256(restored).hexdigest()!=row['baseline_sha256']:
        raise ValueError('Number theory union changed unrelated bytes')
    return restored


def pulmonary_product_bytes(relative,raw):
    return product_view(relative,raw,'pulmonary_views')


def math_product_bytes(relative,raw):
    return product_view(relative,raw,'math_views')


def math_test_bytes(relative,raw):
    evidence=(ROOT/TEST_PROOF).read_bytes()
    if hashlib.sha256(evidence).hexdigest()!=TEST_SHA256:
        raise ValueError('Number theory test inverse evidence changed')
    row=json.loads(evidence)['files'].get(relative)
    if row is None:
        return raw
    digest=hashlib.sha256(raw).hexdigest()
    if digest==row['baseline_sha256']:
        return raw
    if digest!=row['current_sha256']:
        raise ValueError('Unreviewed number theory test byte change')
    text=raw.decode()
    for change in row['changes']:
        if text.count(change['after'])!=1:
            raise ValueError('Number theory test inverse lacks unique change')
        text=text.replace(change['after'],change['before'],1)
    restored=text.encode();path=ROOT
    for part in Path(row['baseline_copy']).parts:
        path=path/part
        if path.is_symlink():
            raise ValueError('Number theory inert test source cannot be a symlink')
    if not path.is_file() or not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Number theory inert test source must be a regular file')
    baseline=path.read_bytes()
    if len(baseline)!=row['bytes'] or hashlib.sha256(baseline).hexdigest()!=row['baseline_sha256'] or restored!=baseline:
        raise ValueError('Number theory inverse changed historical oracle bytes')
    return restored
