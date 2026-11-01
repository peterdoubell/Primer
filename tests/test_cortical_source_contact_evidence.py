from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
D=R/'docs/cortical-source-contacts-review-20261101'
def test_pinned_contact_evidence_and_explicit_limits():
    index=json.loads((D/'evidence-index.json').read_bytes())
    for name,digest in index['toolsSHA256'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest
    for name,digest in index['evidenceSHA256'].items():assert hashlib.sha256((D/name).read_bytes()).hexdigest()==digest
    contacts=json.loads((D/'contact-proof.json').read_bytes());mesh=json.loads((D/'mesh-proof.json').read_bytes());sides=json.loads((D/'side-contact-review.json').read_bytes())
    assert contacts['contactFaces']==274109==sum(r['sourceContactFaces']for r in contacts['pairs'])
    assert mesh['triangles']==548218==sum(r['triangles']for r in mesh['groups'])
    end=0
    for group in mesh['groups']:
        assert group['firstTriangle']==end
        end+=group['triangles']
    assert end==mesh['triangles'] and mesh['allSourceContactsMatchedIndependentEnumeration']
    assert sides['oppositeNamedSideFaceCount']==31==sum(len(r['contacts'])for r in sides['oppositeNamedSideContacts'])
    assert sides['contactsRetainedInMesh'] and not sides['anatomicalDefectInferred']
    assert not index['clinicalApproval'] and not index['runtimeIntegrated'] and not index['wholeGoalComplete']
