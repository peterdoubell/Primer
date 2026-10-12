"""Re-read every original source sample and compare independent cell topology.

The source files and XML/SR remain authoritative. This verifies transport and
released-source agreement, never clinical or fine-anatomical approval.
"""
from pathlib import Path
import gzip
import hashlib
import io
import json
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.research/pulmonary-intake-20261011'
sys.path.insert(0,str(PRIVATE/'python-deps'))
import pydicom
from matplotlib.path import Path as Polygon

OUT = ROOT / 'web/anatomy/lidc-idri-0525'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def verify(row):
    b=(OUT/row['file']).read_bytes()
    assert len(b)==row['bytes'] and sha(b)==row['sha256']
    if row.get('codec'):
        b=gzip.decompress(b)
        assert len(b)==row['decoded_bytes'] and sha(b)==row['decoded_sha256']
    return b


def tagged(e,tag):
    return next((x.text for x in e.iter() if x.tag.rsplit('}',1)[-1]==tag),None)


def source_dicom(a):
    with zipfile.ZipFile(OUT/a['source_archive']) as z:
        return pydicom.dcmread(io.BytesIO(z.read(next(n for n in z.namelist() if n.endswith('.dcm')))))


def run():
    m=json.loads((OUT/'manifest.json').read_text())
    raw=b''.join(verify(c) for c in m['ct']['chunks'])
    assert len(raw)==m['ct']['decoded_bytes'] and sha(raw)==m['ct']['decoded_sha256']
    assert [(c['first_native_slice'],c['stop_native_slice_exclusive']) for c in m['ct']['chunks']]==[(i,min(i+64,429)) for i in range(0,429,64)]
    ct=np.frombuffer(raw,dtype='<u2').reshape(429,512,512)
    for f in m['original_files']:verify(f)
    for z,f in enumerate(m['ct']['slices']):
        d=pydicom.dcmread(OUT/'original-ct'/f['filename'])
        assert np.array_equal(d.pixel_array,ct[z])
        assert list(map(float,d.ImagePositionPatient))==f['position_LPS_mm']
        assert list(map(float,d.ImageOrientationPatient))==f['orientation']==[1,0,0,0,1,0]
        assert float(d.RescaleSlope)==1 and float(d.RescaleIntercept)==-1024
        assert int(d.BitsStored)==12 and int(d.PixelRepresentation)==0
    root=ET.fromstring((OUT/'original-0525.xml').read_bytes())
    originals=[x for x in root.iter() if x.tag.rsplit('}',1)[-1] in ('unblindedReadNodule','nonNodule')]
    assert len(originals)==len(m['xml_marks'])==33
    ids={tagged(x,'noduleID'):x for x in originals if tagged(x,'noduleID') is not None}
    yy,xx=np.indices((512,512));test_points=np.c_[xx.ravel(),yy.ravel()]
    rows=[]
    for a in m['annotations']:
        d=source_dicom(a);mask=np.frombuffer(verify(a['mask']),dtype=np.uint8).reshape((-1,512,512))
        assert np.array_equal(mask,d.pixel_array)
        assert int(mask.sum())==a['occupied_voxels']
        original=ids[a['id'].removeprefix('annotation-')]
        rois=[x for x in original if x.tag.rsplit('}',1)[-1]=='roi']
        xml_mask=np.zeros_like(mask)
        sop_to_frame={s:i for i,s in enumerate(a['source_CT_sop_uids'])}
        for inclusion in ('TRUE','FALSE'):
            for roi in rois:
                if tagged(roi,'inclusion')!=inclusion:continue
                sop=tagged(roi,'imageSOP_UID');fi=sop_to_frame[sop]
                points=np.array([[int(tagged(x,'xCoord')),int(tagged(x,'yCoord'))] for x in roi if x.tag.rsplit('}',1)[-1]=='edgeMap'])
                polygon=np.vstack([points,points[0]])
                inside=Polygon(polygon,closed=True).contains_points(test_points).reshape(512,512)
                if inclusion=='TRUE':xml_mask[fi]|=inside
                else:xml_mask[fi]&=~inside
                xml_mask[fi,points[:,1],points[:,0]]=0
        differing=int(np.count_nonzero(xml_mask!=mask))
        # Preserve a real mismatch as a failure; no altered source expected value.
        assert differing==0,(a['id'],'original XML to source SEG mismatch',differing)
        face_raw=verify(a['face_records']);face_records=np.frombuffer(face_raw,dtype='<i4').reshape(-1,5)
        expected=set()
        occupied={tuple(p) for p in np.argwhere(mask)}
        for p in occupied:
            for axis in range(3):
                for sign in (-1,1):
                    q=list(p);q[axis]+=sign
                    if tuple(q) not in occupied:expected.add((*p,axis,sign))
        assert {tuple(p) for p in face_records}==expected and len(face_records)==len(expected)
        b=verify(a['mesh']);magic,n,t=struct.unpack('<4sII',b[:12]);assert magic==b'LPC1'
        vertices=np.frombuffer(b[12:12+n*24],dtype='<f8').reshape(n,3)
        triangles=np.frombuffer(b[12+n*24:],dtype='<u4').reshape(t,3)
        assert n==a['mesh']['vertices'] and t==a['mesh']['triangles']==2*len(expected)
        assert np.all(triangles<n) and np.isfinite(vertices).all()
        # Independently reconstruct each face from its source cell and exact
        # per-frame origins; compare sets of world triangles, not export indices.
        origins=np.asarray(a['source_frame_origins_LPS_mm']);z=origins[:,2]
        zedges=np.r_[z[0]-a['source_spacing_mm']/2,(z[:-1]+z[1:])/2,z[-1]+a['source_spacing_mm']/2]
        expected_face_points=set()
        for k,y,x,axis,sign in expected:
            sides=[[(x-.5)*a['pixel_spacing_mm'][1]+origins[0,0],(x+.5)*a['pixel_spacing_mm'][1]+origins[0,0]],
                   [(y-.5)*a['pixel_spacing_mm'][0]+origins[0,1],(y+.5)*a['pixel_spacing_mm'][0]+origins[0,1]],
                   [zedges[k],zedges[k+1]]]
            world_axis=2-axis
            val=sides[world_axis][int(sign>0)]
            other=[v for v in range(3) if v!=world_axis]
            corners=[]
            for u,v in [(0,0),(1,0),(1,1),(0,1)]:
                point=[0.,0.,0.];point[world_axis]=val;point[other[0]]=sides[other[0]][u];point[other[1]]=sides[other[1]][v];corners.append(tuple(point))
            expected_face_points.add(frozenset(corners))
        actual_faces={frozenset(tuple(vertices[j]) for j in set(triangles[2*i])|set(triangles[2*i+1])) for i in range(t//2)}
        assert actual_faces==expected_face_points
        rows.append(dict(id=a['id'],XML_ROIs=len(rois),XML_exclusions=sum(tagged(r,'inclusion')=='FALSE' for r in rois),
                         all_original_SEG_samples=int(mask.size),original_XML_SEG_differing_values=differing,
                         occupied_voxels=int(mask.sum()),complete_exposed_faces=len(expected),triangles=t))
    result=dict(manifest_sha256=sha((OUT/'manifest.json').read_bytes()),full_CT_samples=int(ct.size),
                complete_original_CT_instances=429,original_XML_marks=33,source_SEG_checks=rows,
                all_original_pixels_positions_HU_scaling_verified=True,all_source_face_sets_verified=True,
                clinical_approval=False,fine_anatomical_approval=False,structure_coverage_granted=False)
    (ROOT/'docs/pulmonary-nodule-source-review-20261011/source-parity-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':run()
