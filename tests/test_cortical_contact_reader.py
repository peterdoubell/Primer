from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1]
A=R/'web/anatomy/spl-source-contacts'
D=R/'docs/cortical-source-contacts-review-20261101/reader'

def test_contact_review_viewer_matches_verified_gpu_evidence():
    proof=json.loads((D/'proof.json').read_bytes())
    assert proof['allPassed'] and not proof['errors'] and not proof['integrated'] and not proof['clinicalApproval']
    assert {r['width']for r in proof['states']}=={390,1440}
    for row in proof['states']:
        assert row['allSourceBuffersMatched'] and row['sourcePairsSelected']==77 and row['actualDrawRangesVerified']
    for name,digest in proof['sourceSHA256'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest
    raw=(A/'manifest.json').read_bytes();manifest=json.loads(raw)
    pin=re.search(r"const expected='([a-f0-9]{64})'",(A/'viewer.js').read_text()).group(1)
    assert hashlib.sha256(raw).hexdigest()==pin
    assert manifest['contactFaces']==274109 and manifest['oppositeNamedSideFacesRetained']==31
    assert sum(g['triangles']for g in manifest['groups'])==548218
    assert not manifest['clinicalApproval'] and not manifest['anatomicalBoundaryValidated'] and not manifest['completeReportingCoverage']
