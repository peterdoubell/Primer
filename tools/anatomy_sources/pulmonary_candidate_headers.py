from pathlib import Path
import concurrent.futures
import hashlib
import io
import json
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / '.research/pulmonary-intake-20261011'
sys.path.insert(0, str(PRIVATE / 'python-deps'))
import pydicom


def get(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def one(s):
    uid = s['SeriesInstanceUID']
    base = 'https://services.cancerimagingarchive.net/nbia-api/services/v1/'
    raw = get(base + 'getSOPInstanceUIDs?' + urllib.parse.urlencode({'SeriesInstanceUID': uid}))
    sop = json.loads(raw)[0]['SOPInstanceUID']
    source = get(base + 'getSingleImage?' + urllib.parse.urlencode({'SeriesInstanceUID': uid, 'SOPInstanceUID': sop}))
    d = pydicom.dcmread(io.BytesIO(source))
    (PRIVATE / (s['PatientID'] + '-first.dcm')).write_bytes(source)
    keys = ['PatientID', 'Rows', 'Columns', 'PixelSpacing', 'SliceThickness', 'SpacingBetweenSlices',
            'ImagePositionPatient', 'ImageOrientationPatient', 'RescaleSlope', 'RescaleIntercept',
            'ConvolutionKernel', 'BitsAllocated', 'BitsStored', 'PixelRepresentation', 'ContrastBolusAgent',
            'SeriesDescription', 'ReconstructionDiameter']
    return dict(metadata=s, first_sha256=hashlib.sha256(source).hexdigest(),
                header={key: str(getattr(d, key, 'ABSENT')) for key in keys})


def main():
    selected = {'LIDC-IDRI-0429', 'LIDC-IDRI-0473', 'LIDC-IDRI-0525', 'LIDC-IDRI-0947', 'LIDC-IDRI-0663'}
    series = [s for s in json.loads((PRIVATE / 'series-inventory.json').read_text()) if s['PatientID'] in selected]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        rows = list(pool.map(one, series))
    (PRIVATE / 'candidate-header-receipt.json').write_text(json.dumps(rows, indent=2) + '\n')
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
