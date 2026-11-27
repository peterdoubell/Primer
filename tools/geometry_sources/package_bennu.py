"""Reproduce the Bennu volume lab from the three PDS v21a type-2 DSK products.

Run from any directory with numpy and spiceypy available. Download the six PDS
files named in SOURCES and NASA's original bennu_dec10.png into the fixed cache
ROOT/.research/bennu-v21a. Sources and output paths are anchored to this checkout.
"""
import gzip
import hashlib
import io
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import spiceypy as spice

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / '.research/bennu-v21a'
OUT = ROOT / 'web/reference-media/lesson-sources/bennu'
UI = ROOT / 'web/math/bennu-sections'
PDS = 'https://naif.jpl.nasa.gov/pub/naif/pds/pds4/orex/orex_spice/spice_kernels/dsk/'
PHOTO = 'https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09/b/bennu_dec10.png'
PHOTO_SHA256 = '8679f05c80b938d9fdb2ea835196f31ffd62a2f153aafed4601c5478ded1b65b'
SOURCES = {'03250': '64179935decab4258069ad029369c21d5d694ebf1386a5795d4398a77b7a4661', '06370': '47935e86df42f64320fe7d6906a743672f7c40382020ec7c238f69fccb7883bb', '12600': 'de48ae4c47f8dd787ed1459c2001f7f1dfa13df2a2f4864fe8ce6c7dd27fbb57'}
STEPS = 128


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def section_area(tris, normal, cut):
    """Signed boundary integral in a right-handed section plane."""
    u, v = (normal + 1) % 3, (normal + 2) % 3
    below = tris[:, :, normal] < cut
    subset = tris[below.any(axis=1) & ~below.all(axis=1)]
    if not len(subset):
        return 0.
    start = np.empty((len(subset), 2)); end = np.empty_like(start)
    for i in range(3):
        a, b = subset[:, i], subset[:, (i+1) % 3]
        for forward, hits in ((False, start), (True, end)):
            crossing = (a[:, normal] < cut) & (b[:, normal] >= cut) if forward else (b[:, normal] < cut) & (a[:, normal] >= cut)
            x, y = a[crossing], b[crossing]
            f = (cut - x[:, normal]) / (y[:, normal] - x[:, normal])
            hits[crossing] = x[:, [u,v]] + f[:, None] * (y[:, [u,v]] - x[:, [u,v]])
    return float(np.sum(start[:,0]*end[:,1] - end[:,0]*start[:,1]) / 2)


def model(code):
    stem = f'bennu_g_{code}mm_alt_obj_0000n00000_v021a'
    kernel, label = CACHE / (stem+'.bds'), CACHE / (stem+'.xml')
    if checksum(label.read_bytes()) != SOURCES[code]:
        raise ValueError('The archived PDS label changed')
    xml = ET.parse(label)
    file = xml.find('.//{*}File')
    src = kernel.read_bytes()
    if (file.findtext('{*}file_name') != kernel.name or int(file.findtext('{*}file_size')) != len(src)
            or hashlib.md5(src).hexdigest() != file.findtext('{*}md5_checksum')):
        raise ValueError('PDS kernel differs from its source label')
    handle = spice.dasopr(str(kernel))
    try:
        segment = spice.dlabfs(handle)
        descriptor = spice.dskgd(handle, segment)
        if (descriptor.center, descriptor.frmcde, descriptor.dtype) != (2101955, 10106, 2):
            raise ValueError('Unexpected body, frame or DSK data type')
        nv, nt = spice.dskz02(handle, segment)
        points = spice.dskv02(handle, segment, 1, nv) * 1000  # SPICE Cartesian km to m
        faces = spice.dskp02(handle, segment, 1, nt).astype('<u4') - 1
    finally:
        spice.dascls(handle)
    if not np.isfinite(points).all() or faces.max() >= nv:
        raise ValueError('Invalid source geometry')
    # Seam vertices in the archive repeat their exact coordinates. Join them for
    # the closure check only; the delivered index table retains the original IDs.
    welded, ids = np.unique(points, axis=0, return_inverse=True)
    topology = ids[faces]
    edges = np.concatenate((topology[:, [0,1]], topology[:, [1,2]], topology[:, [2,0]]))
    unique_edges, inverse, counts = np.unique(np.sort(edges, axis=1), axis=0, return_inverse=True, return_counts=True)
    balance = np.bincount(inverse, weights=np.where(edges[:,0]<edges[:,1],1,-1))
    if not np.all(counts==2) or np.any(balance) or len(welded)-len(unique_edges)+nt != 2:
        raise ValueError('The volume formula requires a closed, consistently oriented surface')
    tris = points[faces]
    a, b, c = tris.transpose(1,0,2)
    normals = np.cross(b-a,c-a)
    areas = np.linalg.norm(normals, axis=1)/2
    volumes = np.einsum('ij,ij->i', a, np.cross(b,c))/6
    if np.any(areas<=0) or volumes.sum() <= 0:
        raise ValueError('Degenerate plates or unexpected global orientation')
    low, high = points.min(axis=0), points.max(axis=0)
    profiles = [[round(section_area(tris,axis,z),6) for z in np.linspace(low[axis],high[axis],STEPS+1)] for axis in range(3)]
    # Retain all native double-precision coordinates for inspection, section
    # integrals and reference totals; WebGL uses a separate float32 display copy.
    raw = points.astype('<f8').tobytes()+faces.tobytes()
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode='wb', compresslevel=9, mtime=0) as output:
        output.write(raw)
    packed = compressed.getvalue()
    name=code+'.mesh.gz'
    (OUT/name).write_bytes(packed)
    return dict(code=code,resolutionM=int(code)/1000,mesh=name,vertices=nv,triangles=nt,
                uniqueVertices=len(welded),edges=len(unique_edges),bounds=[low.tolist(),high.tolist()],
                areaM2=float(areas.sum()),volumeM3=float(volumes.sum()),profiles=profiles,
                bytes=len(packed),sha256=checksum(packed),decodedSHA256=checksum(raw),
                frame=descriptor.frmcde,kernel=PDS+kernel.name,label=PDS+label.name,labelSHA256=checksum(label.read_bytes()),
                kernelSHA256=checksum(src),pdsMD5=file.findtext('{*}md5_checksum'))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records=[model(code) for code in SOURCES]
    photo=(CACHE/'bennu_dec10.png').read_bytes()
    if checksum(photo) != PHOTO_SHA256: raise ValueError('Unexpected mission mosaic')
    (OUT/'polycam.png').write_bytes(photo)
    payload=dict(models=records,steps=STEPS,photo='polycam.png',photoSHA256=PHOTO_SHA256,photoURL=PHOTO,
                 photoPage='https://science.nasa.gov/resource/bennu-mosaic/',photoCredit='NASA/Goddard/University of Arizona',
                 modelCredit='OSIRIS-REx Altimetry Working Group, NASA Planetary Data System; OSIRIS-REx Laser Altimeter contributed by the Canadian Space Agency.')
    (UI/'source.json').write_text(json.dumps(payload,indent=2)+'\n')
    for row in records: print(row['code'],row['vertices'],row['triangles'],row['volumeM3'])


if __name__=='__main__':
    main()
