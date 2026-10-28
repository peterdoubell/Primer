"""Execute the bounded algebra core checks; independent science review is separate."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_current_algebra_core_implementation_checks():
    run = subprocess.run(
        ['node', str(ROOT / 'tools/check_algebra_functions_core.cjs')],
        cwd=ROOT, capture_output=True, text=True, timeout=90,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    result = json.loads(run.stdout)
    assert result['allPassed']
    assert result['models'] >= 32000
    assert result['checks'] >= 290000
    assert result['coveredQuizItems'] == 40
    assert result['implementationSelfCheck'] is True
    assert result['independentReviewClaimed'] is False
    assert result['coreSHA256'] == hashlib.sha256(
        (ROOT / 'web/algebra-functions-core.js').read_bytes()
    ).hexdigest()
