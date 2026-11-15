"""Preserve all standardized reader SEG/SR series for the chosen full CT case."""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import urllib.parse
import urllib.request
import zipfile
from pulmonary_nodule_intake import PRIVATE


def one(s):
    name = 'source-' + s['SeriesInstanceUID'] + '.zip'
    path = PRIVATE / 'standardized-annotations' / name
    url = 'https://services.cancerimagingarchive.net/nbia-api/services/v1/getImageWithMD5Hash?' + urllib.parse.urlencode({'SeriesInstanceUID': s['SeriesInstanceUID']})
    if not path.exists():
        with urllib.request.urlopen(url, timeout=180) as r:
            raw = r.read()
        path.write_bytes(raw)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        files = [dict(name=n, bytes=len(z.read(n)), sha256=hashlib.sha256(z.read(n)).hexdigest()) for n in z.namelist()]
    return dict(series=s, source_url=url, archive_name=name, bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(), files=files)


def main():
    (PRIVATE / 'standardized-annotations').mkdir(exist_ok=True)
    series = [s for s in json.loads((PRIVATE / 'all-0525.json').read_text()) if s['Modality'] != 'CT']
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(one, series))
    (PRIVATE / 'annotations-download-receipt.json').write_text(json.dumps(rows, indent=2) + '\n')
    print('complete_standardized_series', len(rows), 'bytes', sum(x['bytes'] for x in rows))


if __name__ == '__main__':
    main()
