#!/usr/bin/env python3
"""Generate/check hosted raster metadata from actual reviewed original files; never infer clinical coverage."""
import argparse,hashlib,json,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def inventory():
    data=json.loads((ROOT/'data/radiology/radiology-open-images.json').read_text());files={}
    for images in data.values():
        for row in images:
            src=row['src'];prefix='/app/reference-media/radiology-open/'
            if not src.startswith(prefix):raise ValueError('Unexpected source directory')
            root=(ROOT/'web/reference-media/radiology-open').resolve();path=(root/src.removeprefix(prefix)).resolve()
            if not path.is_relative_to(root) or not path.is_file():raise ValueError('Source path absent or escaped')
            raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
            with Image.open(path) as im:
                im.load();width,height=im.size
            if digest!=row['sha256'] or (width,height)!=(row['width'],row['height']):raise ValueError('Reviewed bytes/dimensions changed: '+row['id'])
            entry={'md5':hashlib.md5(raw).hexdigest(),'sha256':digest,'width':width,'height':height,'bytes':len(raw),'header_hex':raw[:24].hex()}
            if src in files and files[src]!=entry:raise ValueError('Conflicting source file metadata')
            files[src]=entry
    return {'schema_version':1,'scope':'Original radiology rasters hosted statically; integrity metadata only, not anatomical approval.','files':dict(sorted(files.items()))}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args();path=ROOT/'data/radiology/radiology-static-rasters.json';data=inventory()
    if args.write:path.write_text(json.dumps(data,indent=2)+'\n')
    elif json.loads(path.read_text())!=data:raise SystemExit('Static raster inventory differs from original source files; review changes before regenerating.')
    print(len(data['files']),'original raster file hashes/dimensions verified')
