"""Keep the multi-region cut planes and section-sampling lesson tied to the original CT labels."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from urllib.parse import urlsplit

from tools.anatomy_sources import build_liver_section_profile as profiles

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT/'web/radiology/liver-segment-assembly'


def test_every_sampled_area_is_reproducible_from_the_publisher_mask():
    raw = (STUDY/'axial-profile.json').read_bytes()
    profile = json.loads(raw)
    assert profile == profiles.build(ROOT)
    assert len(profile['countsByAxialSection']) == 47 and profile['codes'] == list(range(1,10))
    assert sum(map(sum, profile['countsByAxialSection'])) == 504041
    code = (STUDY/'lab.js').read_text()
    assert hashlib.sha256(raw).hexdigest() in code
    manifest = (ROOT/'web/anatomy/medseg-liver-001/manifest.json').read_bytes()
    assert hashlib.sha256(manifest).hexdigest() in code
    registry = json.loads((ROOT/'web/activities/registry.json').read_bytes())
    for lesson in ['math.3.statistics','math.5.measure']:
        entry, = [link for link in registry[lesson] if '/liver-segment-assembly/' in link['href']]
        url = urlsplit(entry['href'])
        assert url.path == '/app/radiology/liver-segment-assembly/index.html'
        assert not url.query and not url.fragment
        assert f'href="/app/#/node/{lesson}"' in (STUDY/'index.html').read_text()


def test_actual_sampling_module_matches_direct_sums_for_all_starts_and_regions():
    script = """
import fs from 'node:fs';
import {estimates} from './web/radiology/liver-segment-assembly/sampling.mjs';
const p=JSON.parse(fs.readFileSync('./web/radiology/liver-segment-assembly/axial-profile.json'));
const rows=[];
for(let region=0;region<=9;region++){
 const counts=p.countsByAxialSection.map(v=>region?v[region-1]:v.reduce((a,b)=>a+b,0));
 for(const stride of [1,2,3,4,5,6,8,10])rows.push({region,stride,...estimates(counts,p.spacingMm,stride)});
}
console.log(JSON.stringify(rows));
"""
    actual = json.loads(subprocess.run(['node','--input-type=module','--eval',script],cwd=ROOT,
                                       capture_output=True,text=True,check=True).stdout)
    profile = json.loads((STUDY/'axial-profile.json').read_bytes())
    x,y,z = profile['spacingMm']
    assert len(actual) == 80
    for row in actual:
        values = [r[row['region']-1] if row['region'] else sum(r) for r in profile['countsByAxialSection']]
        stride = row['stride']
        exact = sum(values)*x*y*z/1000
        expected = [sum(values[start::stride])*x*y*z*stride/1000 for start in range(stride)]
        assert abs(row['exact']-exact) < 1e-9 and abs(row['mean']-exact) < 1e-9
        assert len(expected) == len(row['volumes'])
        assert all(abs(a-b)<1e-9 for a,b in zip(row['volumes'],expected))
        assert abs(row['sd']-(sum((v-exact)**2 for v in expected)/stride)**.5) < 1e-9


def test_profile_reproduction_uses_the_owned_checkout_from_another_cwd(tmp_path):
    script = ROOT/'tools/anatomy_sources/build_liver_section_profile.py'
    output = STUDY/'axial-profile.json'
    before = output.read_bytes()
    relative = os.path.relpath(ROOT, tmp_path)
    for arguments in [[], ['--root', str(ROOT)], ['--root', relative, '--write']]:
        result = subprocess.run([sys.executable, str(script), *arguments], cwd=tmp_path,
                                capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        assert '47 original sections, 9 regions' in result.stdout
        assert output.read_bytes() == before


def test_profile_rejects_other_roots_before_source_reads_or_writes(tmp_path, monkeypatch):
    output = STUDY/'axial-profile.json'
    before = output.read_bytes()
    def unexpected_load(*args, **kwargs):
        pytest.fail('An unowned root reached source-array loading')
    monkeypatch.setattr(profiles.nib, 'load', unexpected_load)
    with pytest.raises(ValueError, match='checkout containing this script'):
        profiles.build(tmp_path)
    script = ROOT/'tools/anatomy_sources/build_liver_section_profile.py'
    other = tmp_path/'unowned-profile-root'
    result = subprocess.run([sys.executable, str(script), '--root', str(other), '--write'],
                            cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode != 0
    assert 'checkout containing this script' in result.stderr
    assert not other.exists()
    assert output.read_bytes() == before
