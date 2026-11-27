"""Check the full s0028 delivery against the independent original CT and all source masks."""
import gzip
import hashlib
import json
from pathlib import Path

import nibabel as nib
import numpy as np

from package_s0028_torso import BRICK, CT_PATH, GROUPS, LABEL_DIR, OUT, RECEIPT


def decoded(path, row):
    packed = path.read_bytes()
    assert len(packed) == row['bytes'] and hashlib.sha256(packed).hexdigest() == row['sha256']
    raw = gzip.decompress(packed)
    assert hashlib.sha256(raw).hexdigest() == row['decodedSHA256']
    return raw


def verify():
    manifest = json.loads((OUT/'manifest.json').read_bytes())
    receipt = json.loads(RECEIPT.read_bytes())
    rows = {r['sourceLabel']:r for r in manifest['labels']}
    shape = tuple(manifest['shape'])
    ct = nib.load(CT_PATH)
    assert hashlib.sha256(CT_PATH.read_bytes()).hexdigest() == receipt['ctSHA256']
    assert ct.shape == shape and np.array_equal(ct.affine, manifest['affine'])
    original = ct.dataobj.get_unscaled()
    first,second = (np.empty(shape,dtype='u1',order='F') for _ in range(2))
    covered = set()
    for i in range(0,shape[0],BRICK):
        for j in range(0,shape[1],BRICK):
            for k in range(0,shape[2],BRICK):
                covered.add((i,j,k))
    bricks = {tuple(r['start']):r for r in manifest['bricks']}
    assert len(bricks) == len(manifest['bricks']) and set(bricks) == covered
    for i,j,k in sorted(covered):
        row=bricks[i,j,k]
        part=tuple(slice(p,p+BRICK) for p in (i,j,k))
        assert list(original[part].shape) == row['size']
        raw=decoded(OUT/f'brick-{i}-{j}-{k}.gz',row)
        samples=np.frombuffer(raw,dtype='u1').reshape(*reversed(row['size']),4)
        values=samples[...,0].astype(np.int32) + (samples[...,1].view('i1').astype(np.int32) << 8)
        assert np.array_equal(values.T,original[part])
        first[part],second[part]=samples[...,2].T,samples[...,3].T
    assert not np.any((second!=0)&((first==0)|(first==second)))
    assert np.count_nonzero(second)==manifest['overlapVoxels']
    assert np.count_nonzero(first)==manifest['labelledVoxels']
    counts=np.bincount(first.ravel(order='K'),minlength=256)+np.bincount(second.ravel(order='K'),minlength=256)
    assert set(rows)=={name for names in GROUPS.values() for name in names}
    assert sum(r['voxelCount'] for r in rows.values())==np.count_nonzero(first)+np.count_nonzero(second)
    source_records={r['file']:r for r in receipt['labels']}
    points=triangles=ambiguous=0
    probes=[]
    for group,names in GROUPS.items():
        for name in names:
            row=rows[name];file=name+'.nii.gz';path=LABEL_DIR/file
            assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sourceSHA256']==source_records[file]['sha256']
            image=nib.load(path);mask=image.dataobj.get_unscaled()
            assert image.shape==shape and np.array_equal(image.affine,ct.affine)
            coords=np.nonzero(mask);code=row['code']
            assert row['group']==group and len(coords[0])==counts[code]==row['voxelCount']
            assert np.all((first[coords]==code)|(second[coords]==code))
            if not row['voxelCount']:
                assert 'mesh' not in row
                continue
            assert mask[tuple(row['focus'])]==1
            low,high=np.array(row['boundsIndex'])
            assert np.array_equal(low,[col.min() for col in coords]) and np.array_equal(high,[col.max() for col in coords])
            assert row['touchesGridEdge']==bool(np.any(low==0) or np.any(high==np.array(shape)-1))
            mesh=row['mesh']
            raw=decoded(OUT/(name.lower().replace('_','-')+'.mesh.gz'),mesh)
            assert len(raw)==12*(mesh['vertices']+mesh['triangles'])
            v=np.frombuffer(raw,dtype='<f4',count=mesh['vertices']*3).reshape(-1,3)
            f=np.frombuffer(raw,dtype='<u4',offset=v.nbytes).reshape(-1,3)
            assert f.max()<len(v)
            half=np.rint(2*v/manifest['spacingMm']).astype(int)
            assert np.allclose(half*np.asarray(manifest['spacingMm'])/2,v,rtol=0,atol=1e-4)
            odd=(half%2).sum(axis=1);assert np.isin(odd,[1,3]).all()
            edge=half[odd==1]
            assert np.all(mask[tuple((edge//2).T)] != mask[tuple(((edge+1)//2).T)])
            # All source-grid transitions must occur, including at a truncated volume's last plane.
            roi=mask[tuple(slice(max(0,a-1),b+2) for a,b in zip(low,high))]
            assert len(edge)==sum(np.count_nonzero(np.diff(roi,axis=ax)) for ax in range(3))
            for at in half[odd==3]//2:
                cell=mask[tuple(slice(a,a+2) for a in at)];assert cell.any() and not cell.all()
            for axis in range(3):
                selected=f[odd[f[:,axis]]==3]
                if len(selected):
                    co=half[selected[:,axis]]
                    adj=selected[:,[(axis+1)%3,(axis+2)%3]]
                    assert np.all(odd[adj]==1) and np.all(np.abs(half[adj]-co[:,None,:])<=1)
            points+=len(v);triangles+=len(f);ambiguous+=int((odd==3).sum())
            focus=tuple(row['focus'])
            probes.append({'class':name,'position':focus,'storedCT':int(original[focus]),
                           'members':[int(x) for x in (first[focus],second[focus]) if x],
                           'sections':[{
                               'axis':ax,
                               'originalAreaMm2':float(np.take(mask,focus[ax],axis=ax).sum()*2.25),
                               'imageSha256':hashlib.sha256(np.take(original,focus[ax],axis=ax).T[::-1].astype('<i2').tobytes()).hexdigest(),
                               'maskSha256':hashlib.sha256(np.take(mask,focus[ax],axis=ax).T[::-1].tobytes()).hexdigest(),
                           } for ax in range(3)]})
    overlap=np.unravel_index(np.flatnonzero(second)[0],shape)
    result={'storedSamples':int(original.size),'maskArrays':len(rows),'nonemptyMasks':len(probes),
            'sharedVoxels':int(np.count_nonzero(second)),'verifiedVertices':points,'verifiedTriangles':triangles,
            'cellCentres':ambiguous,'edgeTruncatedMasks':sum(r.get('touchesGridEdge',False) for r in rows.values()),
            'overlapProbe':{'position':[int(x) for x in overlap],'storedCT':int(original[overlap]),
                            'members':[int(first[overlap]),int(second[overlap])]},'probes':probes}
    return result


if __name__=='__main__':
    print(json.dumps(verify(),indent=2))
