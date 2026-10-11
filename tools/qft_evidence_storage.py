"""Read exact relocated historical evidence as data; never import/evaluate it."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
RELOCATIONS = {'docs/physics-qft-integrated-science-review-20261011/final-check-harness-failure.js': {'data_path': 'docs/physics-qft-integrated-science-review-20261011/final-check-harness-failure.js.txt', 'sha256': '11815308c637fd0f2e175ba9ba10e4ebe6b1a62ebfd65b7a565d5a6b91d1e007', 'bytes': 9751}, 'docs/physics-qft-integrated-science-review-20261011/final-independent-emission-check.js': {'data_path': 'docs/physics-qft-integrated-science-review-20261011/final-independent-emission-check.js.txt', 'sha256': 'bae1f81708614792318218dfecee1cf285fa662351c1ae442122fdd449a99741', 'bytes': 9880}, 'docs/physics-qft-integrated-science-review-20261011/independent-emission-check.js': {'data_path': 'docs/physics-qft-integrated-science-review-20261011/independent-emission-check.js.txt', 'sha256': '0d63ec0f4db0527fa86999169d715aa7f98aba403bf2390e2e9a9f0f0584bf93', 'bytes': 8588}, 'docs/physics-qft-integrated-science-review-20261011/independent-render-parity.js': {'data_path': 'docs/physics-qft-integrated-science-review-20261011/independent-render-parity.js.txt', 'sha256': '1dd5df0360bebfa927bc096280d9820983334afe007e23d5450b27fe6f093eb9', 'bytes': 6581}, 'docs/physics-qft-integrated-science-review-20261011/representability-failed-function-identity.js': {'data_path': 'docs/physics-qft-integrated-science-review-20261011/representability-failed-function-identity.js.txt', 'sha256': '8f09462bf17331e89cb3ab8df1142c744c3d5816211b17744599f15f60d37722', 'bytes': 8148}, 'docs/physics-qft-integrated-science-review-20261011/representability-independent-check.js': {'data_path': 'docs/physics-qft-integrated-science-review-20261011/representability-independent-check.js.txt', 'sha256': '3728208d3d04af1234b0e8b007ab0e791b20544563b7fc80d22fe5390ea0ee04', 'bytes': 9161}, 'docs/physics-qft-integrated-reader-review-20261011/pr134-historical-runtime/primer__server.py': {'data_path': 'docs/physics-qft-integrated-reader-review-20261011/pr134-historical-runtime/primer__server.py.txt', 'sha256': 'c1ef46900f09553c8bcebaa020d4f9f004352724ea9c1f15307273fb62d93fd0', 'bytes': 190974}}

def relocated_evidence_bytes(historical_path, expected_sha256):
    row = RELOCATIONS.get(historical_path)
    if row is None or expected_sha256 != row['sha256']:
        raise ValueError('Unknown historical evidence path or SHA256')
    path = ROOT / row['data_path']
    if path.is_symlink() or not path.is_file():
        raise ValueError('Historical evidence data unavailable')
    raw = path.read_bytes()
    if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise ValueError('Historical evidence data changed')
    return raw
