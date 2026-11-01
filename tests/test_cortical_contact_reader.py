from tools.cortical_mri_runtime_compatibility import before_mri_bytes
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
    for name,digest in proof['sourceSHA256'].items():assert hashlib.sha256(before_mri_bytes(name,(R/name).read_bytes())).hexdigest()==digest
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

def test_real_hosted_reader_uses_the_verified_immutable_source():
    proof=json.loads((D/'hosted-proof.json').read_bytes())
    delivery=json.loads((R/'docs/cortical-source-contacts-review-20261101/runtime-delivery.json').read_bytes())
    expected=delivery['files']['source-contacts.mesh.gz']['url']
    assert proof['allPassed'] and proof['hostedDelivery'] and not proof['errors']
    assert len(proof['hostedResponses'])==2
    assert all(row=={'url':expected,'status':200}for row in proof['hostedResponses'])
    assert all(row['allSourceBuffersMatched'] and row['actualDrawRangesVerified']for row in proof['states'])
    for file,digest in proof['sourceSHA256'].items():assert hashlib.sha256(before_mri_bytes(file,(R/file).read_bytes())).hexdigest()==digest

def test_actual_gpu_camera_feedback_matches_independent_rotation():
    proof=json.loads((D/'camera-proof.json').read_bytes())
    assert proof['allPassed'] and proof['poses']==16 and proof['GPUVertexTransformsCompared']==2198352
    assert max(r['maxGPUTransformErrorMm']for r in proof['cases'])<0.00005
    assert all(r['maxAbsoluteNDC']<=1.000001 for r in proof['cases'])
    assert not proof['clinicalAnatomicalAccuracyVerified'] and not proof['sourceGeometryChanged']
    for mapping in ['sourceSHA256','toolsSHA256']:
        for name,digest in proof[mapping].items():assert hashlib.sha256(before_mri_bytes(name,(R/name).read_bytes())).hexdigest()==digest
