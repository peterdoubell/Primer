import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/epilepsy-structure-coverage-20261030'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def test_native_review_evidence_is_current_and_does_not_claim_clinical_adequacy():
    anchors=json.loads((D/'mesial-source-anchors.json').read_bytes())
    review=json.loads((D/'native-review/proof.json').read_bytes())
    independent=json.loads((D/'native-review/independent-pixel-proof.json').read_bytes())
    manifest=ROOT/'web/anatomy/spl-nac-limbic/manifest.json'
    assert anchors['manifestSHA256']==review['sourceManifestSHA256']==digest(manifest)
    assert anchors['auditToolSHA256']==digest(ROOT/'tools/anatomy_sources/audit_epilepsy_mesial_sources.py')
    assert review['generatorSHA256']==digest(ROOT/'tools/anatomy_sources/render_epilepsy_mesial_review.py')
    assert independent['checkerSHA256']==digest(ROOT/'tools/anatomy_sources/check_epilepsy_review_pixels.py')
    assert independent['sourceProofSHA256']==digest(D/'native-review/proof.json')
    assert independent['allPassed'] and independent['originalSamplesCompared']==183652
    assert independent['renderedPixelCentresCompared']==367304
    assert len(anchors['structures'])==len(review['reviewSheets'])==12
    for sheet in review['reviewSheets']:
        assert digest(D/'native-review'/sheet['image'])==sheet['sha256']
        assert len(sheet['panels'])==6 and sheet['clinicalVisibilityReviewed'] is False
    assert anchors['completeReportingCoverage'] is False and review['clinicalApproval'] is False
    assert independent['clinicalAdequacyVerified'] is False
