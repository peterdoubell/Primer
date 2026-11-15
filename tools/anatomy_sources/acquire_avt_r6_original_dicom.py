#!/usr/bin/env python3
"""Resume pinned, anonymous public original DICOM acquisition with per-object byte checks."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request
from tools.anatomy_sources.verify_avt_r6_dicom_linkage import OUTPUT,MANIFEST_SHA,INDEX_SHA


def acquire(root):
    raw=(OUTPUT/'original-dicom-object-manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA:raise ValueError('Pinned object manifest differs')
    manifest=json.loads(raw);folder=root/'r6-matched-dicom';folder.mkdir(parents=True,exist_ok=True)
    def object_file(item):
        if not item['key'].startswith('853e29fb-a9ce-4733-8325-71ac1e10a812/') or not item['key'].endswith('.dcm'):raise ValueError('Unreviewed public source object')
        target=folder/Path(item['key']).name
        if not target.exists():
            with urllib.request.urlopen('https://idc-open-data.s3.amazonaws.com/'+item['key'],timeout=60) as response:data=response.read()
            if len(data)!=item['bytes'] or hashlib.md5(data).hexdigest()!=item['etag'].strip('"'):raise ValueError('Original downloaded object differs')
            target.write_bytes(data)
        data=target.read_bytes()
        if len(data)!=item['bytes'] or hashlib.md5(data).hexdigest()!=item['etag'].strip('"'):raise ValueError('Cached source object differs')
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(object_file,manifest['objects']))
    (root/'r6-matched-dicom-objects.json').write_bytes(raw)
    for source,target in [('original-source-doi-metadata.json','rider-pet-ct-doi.json'),
        ('original-collection-license-rows.json','rider-pet-ct-license-rows.json'),('original-index-candidate-rows.json','idc-geometry-candidates.json'),
        ('original-candidate-sample-geometries.json','candidate-sample-geometry.json')]:
        (root/target).write_bytes((OUTPUT/source).read_bytes())
    index=root/'idc-24.2.2/idc_index.parquet';index.parent.mkdir(exist_ok=True)
    if not index.exists():
        with urllib.request.urlopen('https://github.com/ImagingDataCommons/idc-index-data/releases/download/24.2.2/idc_index.parquet',timeout=60) as r:data=r.read()
        if hashlib.sha256(data).hexdigest()!=INDEX_SHA:raise ValueError('Original index differs')
        index.write_bytes(data)
    if hashlib.sha256(index.read_bytes()).hexdigest()!=INDEX_SHA:raise ValueError('Cached index differs')
    print('All pinned original DICOM objects and index verified; full clinical approval still requires anatomical review.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    acquire(p.parse_args().source_root)
