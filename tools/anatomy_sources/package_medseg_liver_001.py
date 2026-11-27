"""Losslessly package the exact public MedSeg v2 case 1, retaining all nine masks.

Reads only fixed app-owned original names and refuses nonmatching bytes.
Authoring dependencies: nibabel, NumPy, SciPy, scikit-image. No resampling,
component removal, smoothing, inferred segment-IV division or gap filling.
"""
import gzip
import hashlib
import itertools
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy.ndimage import distance_transform_edt
from skimage.measure import marching_cubes

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'web/anatomy/medseg-liver-001'
DOC = ROOT / 'docs/medseg-liver-001'
PINS = {'original-ct.nii.gz': '047452d93f8afad1f59fc767b9ec3496e258336c0073b9960b70c76256cd162b',
        'original-labels.nii.gz': '82f000ba6905f45b34f8e9c6427993cd7e87c8c637834e4997500c91de887d90'}
KEYS = ['1', '2', '3', '4a', '4b', '5', '6', '7', '8']
BRICK = 32


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_gzip(name, raw):
    encoded = gzip.compress(raw, compresslevel=6, mtime=0)
    (OUT / name).write_bytes(encoded)
    return dict(file=name, bytes=len(encoded), sha256=sha(encoded), decodedSHA256=sha(raw))


def package():
    for name, expected in PINS.items():
        if sha((OUT / name).read_bytes()) != expected:
            raise ValueError('The publisher source bytes changed: ' + name)
    original = nib.load(OUT / 'original-ct.nii.gz')
    original_labels = nib.load(OUT / 'original-labels.nii.gz')
    image32 = np.asarray(original.dataobj.get_unscaled())
    labels32 = np.asarray(original_labels.dataobj.get_unscaled())
    if (image32.shape != (512, 512, 47) or labels32.shape != image32.shape
            or image32.dtype != np.float32 or labels32.dtype != np.float32
            or not np.array_equal(original.affine, original_labels.affine)):
        raise ValueError('The native source geometry changed')
    image = image32.astype('<i2'); labels = labels32.astype('u1')
    for before, after in [(image32, image.astype('<f4')), (labels32, labels.astype('<f4'))]:
        if not np.array_equal(before.view('u4'), after.view('u4')):
            raise ValueError('The integer transport is not float32-byte-lossless')
    if set(np.unique(labels)) != set(range(10)):
        raise ValueError('The publisher label values changed')
    spacing = np.asarray(original.header.get_zooms(), dtype=float)
    key = []
    for line in (OUT / 'source-label-key.txt').read_text().splitlines():
        if line and line[0].isdigit():
            parts = [item.strip() for item in line.split(';')]
            key.append(dict(code=int(parts[0]), name=parts[1], color=list(map(int, parts[2:5]))))
    if len(key) != 9 or [r['code'] for r in key] != list(range(1, 10)):
        raise ValueError('The publisher label key changed')
    checks = []
    for row, identifier in zip(key, KEYS):
        code = row['code']; mask = labels == code
        coords = np.array(np.nonzero(mask)); low, high = coords.min(axis=1), coords.max(axis=1)
        edge = bool(np.any(low == 0) or np.any(high == np.array(image.shape) - 1))
        if edge:
            raise ValueError('This source mask unexpectedly reaches the scan edge')
        focus = np.unravel_index(distance_transform_edt(mask, sampling=spacing).argmax(), mask.shape)
        start, stop = np.maximum(low-1, 0), np.minimum(high+2, image.shape)
        roi = mask[tuple(slice(a,b) for a,b in zip(start,stop))]
        vertices, faces, _, _ = marching_cubes(roi, level=.5, gradient_direction='ascent', allow_degenerate=False)
        vertices = np.ascontiguousarray((vertices+start)*spacing, dtype='<f4')
        faces = np.ascontiguousarray(faces, dtype='<u4')
        a,b,c = vertices[faces].astype(np.float64).transpose(1,0,2)
        signed_volume = np.einsum('ij,ij->i',a,np.cross(b,c)).sum()/6
        if signed_volume < 0:
            faces = np.ascontiguousarray(faces[:,[0,2,1]],dtype='<u4'); signed_volume = -signed_volume
        if not signed_volume > 0:
            raise ValueError('A source surface has no signed volume')
        edges = np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
        _, counts = np.unique(edges,axis=0,return_counts=True)
        if not np.all(counts == 2):
            raise ValueError('The source mask surface is not a closed two-face edge mesh')
        mesh = dict(**write_gzip('segment-'+identifier+'.mesh.gz',vertices.tobytes()+faces.tobytes()),
                    vertices=len(vertices),triangles=len(faces))
        row.update(segment=identifier, sourceName=row['name'], voxelCount=int(mask.sum()),
                   focus=list(map(int,focus)),boundsIndex=[low.tolist(),high.tolist()],touchesGridEdge=edge,mesh=mesh)
        checks.append(dict(segment=identifier,code=code,sourceCells=int(mask.sum()),
                           focus=row['focus'],focusStoredValue=int(image[focus]),
                           focusCode=int(labels[focus]),closedTwoFaceEdges=True,
                           signedMeshVolumeMm3=float(signed_volume),
                           sourceCellVolumeMm3=float(mask.sum()*np.prod(spacing))))
    bricks = []
    for origin in itertools.product(*(range(0,n,BRICK) for n in image.shape)):
        pick = tuple(slice(a,a+BRICK) for a in origin)
        gray = np.ascontiguousarray(image[pick].T,dtype='<i2')
        cells = np.zeros((*gray.shape,4),dtype='u1')
        cells[...,:2] = gray.view('u1').reshape(*gray.shape,2)
        cells[...,2] = labels[pick].T
        bricks.append(dict(**write_gzip('brick-{}-{}-{}.gz'.format(*origin),cells.tobytes()),
                           start=origin,size=gray.shape[::-1]))
    manifest = dict(id='medseg-liver-001',title='MedSeg liver segments · source case 1 (v2)',
                    encoding='int16-le+two-labels',shape=image.shape,spacingMm=spacing.tolist(),
                    affine=original.affine.tolist(),qformCode=int(original.header['qform_code']),
                    sformCode=int(original.header['sform_code']),units=list(original.header.get_xyzt_units()),
                    originalCTDtype='float32',originalLabelDtype='float32',
                    originalSampleSHA256=sha(image32.astype('<f4').tobytes(order='F')),
                    originalLabelSampleSHA256=sha(labels32.astype('<f4').tobytes(order='F')),
                    ctSampleSHA256=sha(image.tobytes(order='F')),
                    labelSampleSHA256=sha(labels.tobytes(order='F')),
                    transport='Integer re-encoding restores the exact original float32 sample bytes; no resampling.',
                    storedRange=[int(image.min()),int(image.max())],
                    labels=key,brickSize=BRICK,bricks=bricks,overlapVoxels=0,
                    labelledVoxels=int(np.count_nonzero(labels)),
                    sourceURL='https://doi.org/10.6084/m9.figshare.13643252.v2',
                    sourceCase='img1.nii.gz paired with mask1.nii.gz in publisher v2 archives; original MSD case ID is not published in this collection.',
                    labelKey='source-label-key.txt',
                    authors=['MedSeg','Håvard Bjørke Jenssen','Tomas Sakinis'],
                    imageLicense=dict(name='CC BY-SA 4.0',url='https://creativecommons.org/licenses/by-sa/4.0/',
                                      primarySource='https://medicaldecathlon.com/',
                                      datasetPaper='https://doi.org/10.1038/s41467-022-30695-9'),
                    annotationLicense=dict(name='CC0 1.0',url='https://creativecommons.org/publicdomain/zero/1.0/'),
                    originals=[dict(file=name,bytes=(OUT/name).stat().st_size,sha256=expected)
                               for name,expected in PINS.items()],
                    scope='Published Couinaud segment annotations from a different CT case than s0028 and the separate MR reference. Phase, diagnosis and original DICOM calibration are not supplied. Source labels are not current-patient registration, LI-RADS observations or clinical approval.')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    (DOC/'package-review.json').write_text(json.dumps(dict(labels=checks,bricks=len(bricks),
        nativeSamples=int(image.size),sourceSampleBytesLossless=True,
        totalTriangles=sum(r['mesh']['triangles']for r in key)),indent=2)+'\n')
    print(len(bricks),'bricks;',len(key),'source segment meshes;',sum(r['mesh']['triangles']for r in key),'triangles')


def write_delivery():
    import re
    viewer = OUT / 'viewer.js'
    text = viewer.read_text()
    text, count = re.subn(r"(const MANIFEST_SHA256 = ')[a-f0-9]{64}(';)", lambda m: m[1]+sha((OUT/'manifest.json').read_bytes())+m[2], text)
    if count != 1:
        raise ValueError('The source inventory pin is missing')
    viewer.write_text(text)
    names = {'index.html','viewer.js','viewer.css','manifest.json','ATTRIBUTION.txt',
             'source-label-key.txt','original-ct.nii.gz','original-labels.nii.gz'}
    names.update('brick-{}-{}-{}.gz'.format(i,j,k)
                 for i in range(0,512,BRICK) for j in range(0,512,BRICK)
                 for k in range(0,47,BRICK))
    names.update('segment-'+segment+'.mesh.gz' for segment in KEYS)
    actual = {path.name for path in OUT.iterdir() if path.is_file() and path.name != 'delivery.json'}
    if actual != names:
        raise ValueError('Unexpected or missing source delivery file')
    files = {}
    for name in sorted(names):
        raw = (OUT/name).read_bytes(); files[name] = dict(bytes=len(raw),sha256=sha(raw))
    (OUT/'delivery.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')


if __name__ == '__main__':
    package()
    write_delivery()
