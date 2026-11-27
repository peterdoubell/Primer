"""Independently verify native publisher arrays, all transport cells and surfaces.

Does not import the packaging implementation. Fixed, app-owned paths only.
Default checks the saved scientific receipt; --write regenerates that receipt.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy.ndimage import map_coordinates

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'web/anatomy/medseg-liver-001'
PROOF = ROOT / 'docs/medseg-liver-001/source-comparison.json'
SEGMENTS = ['1','2','3','4a','4b','5','6','7','8']
PINS = {'original-ct.nii.gz':'047452d93f8afad1f59fc767b9ec3496e258336c0073b9960b70c76256cd162b',
        'original-labels.nii.gz':'82f000ba6905f45b34f8e9c6427993cd7e87c8c637834e4997500c91de887d90'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify():
    manifest = json.loads((OUT/'manifest.json').read_bytes())
    ct = nib.load(OUT/'original-ct.nii.gz'); source = np.asarray(ct.dataobj.get_unscaled())
    lm = nib.load(OUT/'original-labels.nii.gz'); source_labels = np.asarray(lm.dataobj.get_unscaled())
    originals = {}
    for name, expected in PINS.items():
        raw = (OUT/name).read_bytes(); assert sha(raw) == expected
        originals[name] = dict(bytes=len(raw),sha256=expected)
    assert source.dtype == source_labels.dtype == np.float32
    assert source.shape == source_labels.shape == tuple(manifest['shape']) == (512,512,47)
    assert np.array_equal(ct.affine,lm.affine) and np.array_equal(ct.affine,manifest['affine'])
    assert np.array_equal(ct.header.get_zooms(),manifest['spacingMm'])
    assert np.array_equal(ct.affine[:3,:3],np.diag(ct.header.get_zooms()))
    assert ct.header.get_xyzt_units()[0] == 'mm'
    for volume in [ct,lm]:
        q,qc=volume.get_qform(coded=True);s,sc=volume.get_sform(coded=True)
        assert qc == sc == 1 and np.array_equal(q,s) and np.array_equal(s,ct.affine)
        assert volume.dataobj.slope == 1 and volume.dataobj.inter == 0
    image=np.empty(source.shape,dtype='<i2');labels=np.empty(source.shape,dtype='u1');coverage=np.zeros(source.shape,dtype='u1')
    cells_compared=0
    for row in manifest['bricks']:
        start=row['start']; assert len(start)==3 and all(isinstance(x,int)and x>=0 for x in start)
        name='brick-{}-{}-{}.gz'.format(*start);assert row['file']==name
        packed=(OUT/name).read_bytes();assert len(packed)==row['bytes'] and sha(packed)==row['sha256']
        raw=gzip.decompress(packed);assert sha(raw)==row['decodedSHA256']
        size=tuple(row['size']);assert len(raw)==np.prod(size)*4
        samples=np.frombuffer(raw,dtype=np.dtype({'names':['ct','label','second'],'formats':['<i2','u1','u1'],'offsets':[0,2,3],'itemsize':4}))
        gray=samples['ct'].reshape(size,order='F');codes=samples['label'].reshape(size,order='F')
        assert not np.any(samples['second']);pick=tuple(slice(a,a+b)for a,b in zip(start,size))
        assert np.array_equal(gray.astype('<f4').view('u4'),source[pick].view('u4'))
        assert np.array_equal(codes.astype('<f4').view('u4'),source_labels[pick].view('u4'))
        assert not np.any(coverage[pick]);image[pick]=gray;labels[pick]=codes;coverage[pick]=1;cells_compared+=gray.size
    assert np.all(coverage==1)and cells_compared==source.size
    source_hash=sha(source.astype('<f4').tobytes(order='F'));label_source_hash=sha(source_labels.astype('<f4').tobytes(order='F'))
    assert source_hash==manifest['originalSampleSHA256']==sha(image.astype('<f4').tobytes(order='F'))
    assert label_source_hash==manifest['originalLabelSampleSHA256']==sha(labels.astype('<f4').tobytes(order='F'))
    assert sha(image.tobytes(order='F'))==manifest['ctSampleSHA256']
    assert sha(labels.tobytes(order='F'))==manifest['labelSampleSHA256']
    key_raw=(OUT/'source-label-key.txt').read_bytes()
    assert hashlib.md5(key_raw).hexdigest()=='470c86bb3740991af74a64212bd2a486'
    key_identity=dict(file='source-label-key.txt',bytes=len(key_raw),sha256=sha(key_raw),publisherMD5='470c86bb3740991af74a64212bd2a486')
    key=[]
    for line in(OUT/'source-label-key.txt').read_text().splitlines():
        if line and line[0].isdigit():
            parts=[x.strip()for x in line.split(';')];key.append((int(parts[0]),parts[1],list(map(int,parts[2:5]))))
    assert [r['code']for r in manifest['labels']]==list(range(1,10))
    checked=[];spacing=np.array(ct.header.get_zooms(),dtype=float)
    for row,(code,name,color),segment in zip(manifest['labels'],key,SEGMENTS):
        assert row['code']==code and row['segment']==segment and row['sourceName']==row['name']==name and row['color']==color
        mask=source_labels==code;xyz=np.array(np.nonzero(mask));n=int(mask.sum());low,high=xyz.min(axis=1),xyz.max(axis=1)
        assert n==row['voxelCount'] and row['boundsIndex']==[low.tolist(),high.tolist()]
        focus=row['focus'];assert source_labels[tuple(focus)]==code
        edge=bool(np.any(low==0)or np.any(high==np.array(source.shape)-1));assert edge==row['touchesGridEdge']==False
        mesh=row['mesh'];file='segment-'+segment+'.mesh.gz';assert mesh['file']==file
        packed=(OUT/file).read_bytes();assert len(packed)==mesh['bytes']and sha(packed)==mesh['sha256']
        raw=gzip.decompress(packed);assert sha(raw)==mesh['decodedSHA256']
        assert len(raw)==12*(mesh['vertices']+mesh['triangles'])
        vertices=np.frombuffer(raw,dtype='<f4',count=mesh['vertices']*3).reshape(-1,3)
        faces=np.frombuffer(raw,dtype='<u4',offset=mesh['vertices']*12).reshape(-1,3)
        assert np.isfinite(vertices).all()and faces.max()<len(vertices)
        indices=vertices.astype(float)/spacing
        assert np.all(indices>=0)and np.all(indices<=np.array(source.shape)-1)
        # Float32 transport can perturb a native integer/half-integer by ~1e-5.
        nearest=np.rint(indices*2)/2;indices=np.where(np.abs(indices-nearest)<1e-4,nearest,indices)
        lo=np.floor(indices).astype(int);hi=np.ceil(indices).astype(int)
        values=np.stack([mask[np.where(a,hi[:,0],lo[:,0]),np.where(b,hi[:,1],lo[:,1]),np.where(c,hi[:,2],lo[:,2])]for a in[0,1]for b in[0,1]for c in[0,1]])
        assert np.all(values.min(axis=0)==0)and np.all(values.max(axis=0)==1)
        continuous=map_coordinates(mask.astype('f4'),indices.T,order=1,mode='nearest')
        level_deviation=float(np.abs(continuous-.5).max())
        edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
        _,edge_counts=np.unique(edges,axis=0,return_counts=True);assert np.all(edge_counts==2)
        points=vertices.astype(float)-vertices.astype(float).mean(axis=0)
        triangles=points[faces];volume=float(np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6);assert volume>0
        sections=[]
        for plane,axis in[('ij',2),('ik',1),('jk',0)]:
            fixed=focus[axis];a=np.take(source,fixed,axis=axis).T[::-1].copy();b=np.take(source_labels,fixed,axis=axis).T[::-1].copy();pitch=np.delete(spacing,axis);area_cells=int(np.count_nonzero(b==code))
            sections.append(dict(plane=plane,fixed=fixed,width=a.shape[1],height=a.shape[0],sourceCTFloat32SHA256=sha(a.astype('<f4').tobytes()),ctInt16SHA256=sha(a.astype('<i2').tobytes()),sourceLabelsFloat32SHA256=sha(b.astype('<f4').tobytes()),labelSHA256=sha(b.astype('u1').tobytes()),areaPixels=area_cells,areaMm2=round(float(area_cells*np.prod(pitch)),8)))
        checked.append(dict(code=code,segment=segment,sourceName=name,color=color,voxelCount=n,focus=focus,focusVerified=True,focusCode=int(source_labels[tuple(focus)]),focusStoredValue=int(source[tuple(focus)]),focusRASmm=nib.affines.apply_affine(ct.affine,focus).tolist(),boundsIndex=row['boundsIndex'],touchesGridEdge=edge,mesh=dict(**mesh,allVerticesMeetSourceBoundaryCells=True,maximumTrilinearLevelDeviation=round(level_deviation,8),closedTwoFaceEdges=True,outwardSignedVolumeMm3=round(volume,6)),sections=sections))
    originals['original-ct.nii.gz'].update(dtype='float32',sampleSHA256=source_hash)
    originals['original-labels.nii.gz'].update(dtype='float32',sampleSHA256=label_source_hash)
    return dict(schemaVersion=1,caseId='medseg-liver-001',source=originals,labelKey=key_identity,
                geometry=dict(shape=list(source.shape),spacingMm=list(map(float,spacing)),affine=ct.affine.tolist(),qformCode=1,sformCode=1,units='mm',axes=list(nib.aff2axcodes(ct.affine))),
                labels=checked,transport=dict(bricks=len(manifest['bricks']),cellsCompared=int(cells_compared),allCTValuesMatchSource=True,allLabelCodesMatchSource=True,float32CTBytesRestored=True,float32LabelBytesRestored=True,emptyOverlapSlot=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args();proof=verify()
    if args.write:PROOF.write_text(json.dumps(proof,indent=2)+'\n')
    else:assert json.loads(PROOF.read_text())==proof
    print('Verified every native sample in',proof['transport']['bricks'],'bricks and all',len(proof['labels']),'original segment surfaces')
