"""Advance local package metadata only after complete publisher-byte authentication.

This does not upload, expose app routes, grant clinical approval, or publish a
registry. The metadata change requires fresh package and reader verification.
"""
from pathlib import Path
import copy
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / '.research/epilepsy-source-20261028'
ARCHIVE_SHA256 = 'e76586274bba73f64f2355b093da3ae671fb8e77bb62c13528cfac9d4893ba2e'
ARCHIVE_BYTES = 13046575553
ACQUISITION_SHA256 = 'dfab764bc92a28f6366c926cb90eae0201a20acd2c23db00bfb47893ddb5f63b'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def authenticate():
    receipt_path = DATA / 'dryad-stream-verification.json'
    if not receipt_path.is_file():
        raise ValueError('Full publisher archive authentication has not completed')
    receipt_raw = receipt_path.read_bytes()
    receipt = json.loads(receipt_raw)
    acquisition_raw = (DATA / 'dryad-case10-acquisition.json').read_bytes()
    if sha(acquisition_raw) != ACQUISITION_SHA256:
        raise ValueError('Selected-source acquisition changed')
    acquisition = json.loads(acquisition_raw)
    if (receipt.get('state') != 'complete'
            or receipt.get('matchesPublisherSHA256') is not True
            or receipt.get('sha256') != ARCHIVE_SHA256
            or receipt.get('bytes') != ARCHIVE_BYTES
            or receipt.get('selectedAcquisitionRangesIndependentlyVerified') != len(acquisition['rangeRequests'])):
        raise ValueError('Publisher archive authentication is incomplete or belongs to another source')
    cursor = 0
    for chunk in receipt.get('chunks', []):
        if chunk['start'] != cursor or chunk['end'] < cursor or len(chunk['sha256']) != 64:
            raise ValueError('Authenticated archive range coverage is incomplete')
        cursor = chunk['end'] + 1
    if cursor != ARCHIVE_BYTES:
        raise ValueError('Authenticated archive ranges do not cover the complete source')
    for row in acquisition['files']:
        raw = (DATA / row['file']).read_bytes()
        if len(raw) != row['bytes'] or sha(raw) != row['sha256']:
            raise ValueError('Original selected source bytes changed')
    reference = json.loads((DATA / 'second-rater-reference-proof.json').read_bytes())
    if (reference.get('allPassed') is not True or reference.get('identicalCompleteNiftiBytes') is not True
            or reference.get('sha256') != '8757ead3ca70dd77ea7dcab0ebe686416b3be44ae1455a0ede5475efc036027e'
            or reference.get('archiveChunk', {}).get('sha256') != receipt['chunks'][0]['sha256']):
        raise ValueError('Both annotations have no verified identical reference image')
    path = DATA / 'native-package/manifest.json'
    before = path.read_bytes()
    manifest = json.loads(before)
    authentication = {'archiveSHA256': ARCHIVE_SHA256, 'archiveBytes': ARCHIVE_BYTES,
                      'verificationReceiptSHA256': sha(receipt_raw),
                      'acquisitionReceiptSHA256': ACQUISITION_SHA256,
                      'selectedRangesVerified': len(acquisition['rangeRequests'])}
    if manifest.get('fullArchiveVerificationPending') is False:
        if manifest.get('sourceArchiveAuthentication') != authentication:
            raise ValueError('Existing authentication has a different identity')
        return {'alreadyAuthenticated': True, 'manifestSHA256': sha(before)}
    proof = json.loads((DATA / 'native-package-independent-proof.json').read_bytes())
    if (proof.get('allPassed') is not True or proof.get('manifestSHA256') != sha(before)
            or proof.get('planes') != 4944 or len(proof.get('meshes', [])) != 13):
        raise ValueError('Current native package has no matching independent verification')
    if (manifest.get('sourceDOI') != '10.5061/dryad.2v6wwpzt3'
            or manifest.get('sourceVersion') != 7 or manifest.get('license') != 'CC0-1.0'
            or manifest.get('fullArchiveVerificationPending') is not True
            or manifest.get('clinicalApproval') is not False
            or manifest.get('annotationReferenceVolume') != 'mean'
            or manifest.get('rawRepetitionAnatomicalRegistrationVerified') is not False):
        raise ValueError('Source interpretation changed')
    after = copy.deepcopy(manifest)
    after['fullArchiveVerificationPending'] = False
    after['sourceArchiveAuthentication'] = authentication
    encoded = (json.dumps(after, separators=(',', ':')) + '\n').encode()
    transition = {'beforeSHA256': sha(before), 'afterSHA256': sha(encoded),
                  'metadataChangesOnly': ['fullArchiveVerificationPending', 'sourceArchiveAuthentication'],
                  'authentication': authentication, 'payloadsChanged': False,
                  'freshVerificationRequired': True, 'clinicalApproval': False,
                  'published': False, 'wholeGoalComplete': False}
    # Preserve the exact pre-authentication package identity, then atomically
    # change the local manifest. Runtime assets are untouched by this tool.
    (DATA / 'manifest-before-authentication.json').write_bytes(before)
    (DATA / 'package-authentication-transition.json').write_text(json.dumps(transition, indent=2) + '\n')
    temp = path.with_suffix('.tmp')
    with temp.open('wb') as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)
    return transition


if __name__ == '__main__':
    print(json.dumps(authenticate(), indent=2))
