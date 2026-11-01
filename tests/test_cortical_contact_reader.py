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

def test_delivery_package_evidence_matches_current_metadata_and_tools():
    root=R/'docs/cortical-source-contacts-review-20261101'
    package=json.loads((root/'package-proof.json').read_bytes())
    independent=json.loads((root/'package-independent-proof.json').read_bytes())
    raw=(A/'manifest.json').read_bytes();row=json.loads(raw)['meshes']['contacts']
    assert package['allPassed'] and independent['allPassed']
    assert hashlib.sha256(raw).hexdigest()==package['manifestSHA256']==independent['manifestSHA256']
    assert package['compressedSHA256']==row['compressedSHA256'] and package['compressedBytes']==row['compressedBytes']
    assert package['decodedSHA256']==row['sha256'] and package['decodedBytes']==row['bytes']
    assert independent['allCoordinatesExact'] and independent['allIndicesExact']
    assert independent['verticesCompared']==274786 and independent['trianglesCompared']==548218
    assert independent['packageProofSHA256']==hashlib.sha256((root/'package-proof.json').read_bytes()).hexdigest()
    assert package['packagerSHA256']==hashlib.sha256((R/'tools/anatomy_sources/package_cortical_source_contacts.py').read_bytes()).hexdigest()
    assert independent['checkerSHA256']==hashlib.sha256((R/'tools/anatomy_sources/check_cortical_contact_package.py').read_bytes()).hexdigest()
    assert not package['runtimeBound'] and not independent['clinicalApproval']
