"""Package the native s0028 CT and all matching v3 label arrays. No patient axes are inferred."""
import argparse
import colorsys
import gzip
import hashlib
import io
import itertools
import json
import re
import zlib
from pathlib import Path

import nibabel as nib
import numpy as np
from skimage.measure import marching_cubes


ROOT = Path(__file__).resolve().parents[2]
LABEL_DIR = ROOT / '.research/torso-s0028/labels'
CT_PATH = ROOT / 'web/anatomy/totalseg-s0028-lungs/originals/ct.nii.gz'
OUT = ROOT / 'web/anatomy/ct-torso-s0028'
RECEIPT = ROOT / 'docs/ct-torso-s0028/acquisition.json'
BRICK = 64
GROUPS = {
    'Head, neck and chest organs': 'brain lung_upper_lobe_left lung_lower_lobe_left lung_upper_lobe_right lung_middle_lobe_right lung_lower_lobe_right esophagus trachea thyroid_gland heart atrial_appendage_left'.split(),
    'Abdomen and pelvis': 'spleen kidney_right kidney_left gallbladder liver stomach pancreas adrenal_gland_right adrenal_gland_left small_bowel duodenum colon urinary_bladder prostate kidney_cyst_left kidney_cyst_right'.split(),
    'Blood vessels': 'aorta pulmonary_vein brachiocephalic_trunk subclavian_artery_right subclavian_artery_left common_carotid_artery_right common_carotid_artery_left brachiocephalic_vein_left brachiocephalic_vein_right superior_vena_cava inferior_vena_cava portal_vein_and_splenic_vein iliac_artery_left iliac_artery_right iliac_vena_left iliac_vena_right'.split(),
    'Spine and spinal cord': ['sacrum', 'spinal_cord'] + [f'vertebrae_{region}{level}' for region, levels in [('C',7), ('T',12), ('L',6)] for level in range(1, levels+1)],
    'Ribs and chest wall': ['sternum', 'costal_cartilages'] + [f'rib_{side}_{level}' for side in ('left','right') for level in range(1,13)],
    'Other bones': ['skull'] + [f'{bone}_{side}' for bone in ('humerus','scapula','clavicula','femur','hip') for side in ('left','right')],
    'Muscles': [f'{muscle}_{side}' for muscle in ('gluteus_maximus','gluteus_medius','gluteus_minimus','autochthon','iliopsoas') for side in ('left','right')],
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def packed(name, raw):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=6, mtime=0) as stream:
        stream.write(raw)
    encoded = buf.getvalue()
    (OUT / name).write_bytes(encoded)
    return {'file': name, 'bytes': len(encoded), 'sha256': sha(encoded), 'decodedSHA256': sha(raw)}


def display_name(name):
    if name.startswith('vertebrae_'):
        return name.split('_')[1] + ' vertebra'
    if name.startswith('rib_'):
        _, side, level = name.split('_')
        return f'{side.title()} rib {level}'
    parts = name.split('_')
    if parts[-1] in ('right','left'):
        parts = [parts[-1], *parts[:-1]]
    return ' '.join(parts).capitalize()


def generate():
    receipt = json.loads(RECEIPT.read_bytes())
    source = {r['file']: r for r in receipt['labels']}
    if set(source) != {name+'.nii.gz' for names in GROUPS.values() for name in names}:
        raise ValueError('The selected source mask identities differ from the archive directory')
    if sha(CT_PATH.read_bytes()) != receipt['ctSHA256']:
        raise ValueError('CT differs from the original archive member')
    ct = nib.load(CT_PATH)
    samples = ct.dataobj.get_unscaled()
    if samples.dtype != np.int16 or samples.shape != (299,299,394):
        raise ValueError('Unexpected source CT samples')
    dimensions = samples.shape
    spacing = np.asarray(ct.header.get_zooms(), dtype=float)
    first, second = (np.zeros(dimensions, np.uint8, order='F') for _ in range(2))
    rows = []
    for group, names in GROUPS.items():
        for name in names:
            code = len(rows)+1
            member = name+'.nii.gz'
            raw = (LABEL_DIR/member).read_bytes()
            record = source[member]
            if len(raw) != record['bytes'] or sha(raw) != record['sha256'] or zlib.crc32(raw) != int(record['crc32'],16):
                raise ValueError('Mask differs from archive member '+name)
            image = nib.load(LABEL_DIR/member)
            mask = image.dataobj.get_unscaled()
            if (mask.shape != dimensions or mask.dtype != np.uint8 or mask.max() > 1
                    or not np.array_equal(image.affine,ct.affine)):
                raise ValueError('Mask geometry or sample values differ: '+name)
            coords = np.nonzero(mask)
            n = len(coords[0])
            row = dict(code=code, name=display_name(name), sourceLabel=name, group=group,
                       color=[round(value*255) for value in colorsys.hls_to_rgb(code*.618034%1,.65,.72)],
                       voxelCount=n, sourceSHA256=record['sha256'])
            rows.append(row)
            if not n:
                continue
            if np.any(second[coords]):
                raise ValueError('Two membership channels are insufficient')
            has_first = first[coords] != 0
            second[tuple(col[has_first] for col in coords)] = code
            first[tuple(col[~has_first] for col in coords)] = code
            low, high = np.array([col.min() for col in coords]), np.array([col.max() for col in coords])
            mean = [col.mean() for col in coords]
            nearest = np.argmin(sum((col-mid)**2 for col,mid in zip(coords,mean)))
            row.update(focus=[int(col[nearest]) for col in coords], boundsIndex=[low.tolist(),high.tolist()],
                       touchesGridEdge=bool(np.any(low==0) or np.any(high==np.array(dimensions)-1)))
            # Crop for performance. Never extend the mask beyond the acquired grid to close cut surfaces.
            start, stop = np.maximum(low-1,0), np.minimum(high+2,dimensions)
            region = mask[tuple(slice(a,b) for a,b in zip(start,stop))]
            vertices, faces, _, _ = marching_cubes(region, level=.5, gradient_direction='ascent', allow_degenerate=False)
            positions = np.ascontiguousarray((vertices+start)*spacing,dtype='<f4')
            indices = np.ascontiguousarray(faces,dtype='<u4')
            row['mesh'] = dict(**packed(name.lower().replace('_','-')+'.mesh.gz',positions.tobytes()+indices.tobytes()),
                               vertices=len(vertices),triangles=len(faces))
    bricks = []
    for origin in itertools.product(*(range(0,n,BRICK) for n in dimensions)):
        pick = tuple(slice(a,a+BRICK) for a in origin)
        gray = np.ascontiguousarray(samples[pick].T,dtype='<i2')
        pairs = np.empty((*gray.shape,4),dtype=np.uint8)
        pairs[...,:2] = gray.view('u1').reshape(*gray.shape,2)
        pairs[...,2] = first[pick].T
        pairs[...,3] = second[pick].T
        name = 'brick-{}-{}-{}.gz'.format(*origin)
        bricks.append(dict(**packed(name,pairs.tobytes()),start=origin,size=gray.shape[::-1]))
    result = dict(id='s0028', encoding='int16-le+two-labels', shape=dimensions, spacingMm=spacing.tolist(), affine=ct.affine.tolist(),
                  ctSHA256=receipt['ctSHA256'], ctSampleSHA256=sha(samples.tobytes(order='F')),
                  groups=list(GROUPS), labels=rows, brickSize=BRICK, bricks=bricks,
                  overlapVoxels=int(np.count_nonzero(second)), labelledVoxels=int(np.count_nonzero(first)),
                  sourceURL='https://zenodo.org/records/22688904',license='CC BY 4.0')
    (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(len(bricks),'bricks;',sum(bool(r['voxelCount']) for r in rows),'surfaces;',
          sum(r['mesh']['triangles'] for r in rows if r.get('mesh')),'triangles;',result['overlapVoxels'],'shared cells')


def write_delivery():
    manifest = json.loads((OUT/'manifest.json').read_bytes())
    viewer = OUT / 'viewer.js'
    text, changed = re.subn(r"(await fingerprint\(bytes\)\) !== ')[0-9a-f]{64}(')", lambda m: m[1] + sha((OUT/'manifest.json').read_bytes()) + m[2], viewer.read_text())
    if changed != 1:
        raise ValueError('Missing pinned CT inventory in the reader')
    guide_digest = sha((OUT/'report-guide.json').read_bytes())
    text, changed = re.subn(r"(const guideFingerprint = ')[0-9a-f]{64}(')", lambda m: m[1] + guide_digest + m[2], text)
    if changed != 1:
        raise ValueError('Missing pinned CAP report guide in the reader')
    viewer.write_text(text)
    names = {'index.html', 'viewer.css', 'viewer.js', 'report-areas.json', 'report-guide.json', 'manifest.json'}
    for group in GROUPS.values():
        for name in group:
            if any(row['sourceLabel'] == name and row['voxelCount'] for row in manifest['labels']):
                names.add(name.lower().replace('_','-')+'.mesh.gz')
    for i,j,k in itertools.product(range(0,299,BRICK),range(0,299,BRICK),range(0,394,BRICK)):
        names.add(f'brick-{i}-{j}-{k}.gz')
    files = {}
    for name in sorted(names):
        raw=(OUT/name).read_bytes()
        files[name]={'sha256':sha(raw),'bytes':len(raw)}
    (OUT/'delivery.json').write_text(json.dumps({'files':files},indent=2)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery-only',action='store_true',help='refresh file hashes after editing a viewer')
    if not parser.parse_args().delivery_only:
        generate()
    write_delivery()
