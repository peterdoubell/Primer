"""Download a complete source ZIP and preserve the returned source license."""
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
import zipfile
from pulmonary_nodule_intake import PRIVATE


def main():
    s = next(s for s in json.loads((PRIVATE / 'series-inventory.json').read_text()) if s['PatientID'] == 'LIDC-IDRI-0525')
    url = 'https://services.cancerimagingarchive.net/nbia-api/services/v1/getImageWithMD5Hash?' + urllib.parse.urlencode({'SeriesInstanceUID': s['SeriesInstanceUID']})
    path = PRIVATE / 'LIDC-IDRI-0525-complete-original.zip'
    if not path.exists():
        with urllib.request.urlopen(url, timeout=600) as r, path.with_suffix('.partial').open('wb') as out:
            while b := r.read(1024 * 1024):
                out.write(b)
        path.with_suffix('.partial').rename(path)
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        print('ZIP names', len(names))
        for name in names:
            if any(t in name.lower() for t in ('license', 'md5', '.txt', '.csv')):
                raw = z.read(name)
                print(name, raw.decode(errors='replace')[:16000])
                (PRIVATE / Path(name).name).write_bytes(raw)
        print('zip_crc_failure', z.testzip())
    row = dict(series=s, url=url, bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), archive_names=names)
    (PRIVATE / 'original-series-download-receipt.json').write_text(json.dumps(row, indent=2) + '\n')
    print('source_archive', row['bytes'], row['sha256'])


if __name__ == '__main__':
    main()
