"""Validate the displayed PDS geometry and area profiles by independent tetrahedron cuts."""
from pathlib import Path
import gzip
import hashlib
import json

import numpy as np
import spiceypy as spice

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / '.research/bennu-v21a'
MEDIA = ROOT / 'web/reference-media/lesson-sources/bennu'
CODES = ('03250','06370','12600')


def tetra_sections(vertices, plates, axis, cut):
    """Sum the plane cuts through the origin-to-face tetrahedra, not the exterior contour."""
    coords = vertices[plates]
    axes = [(axis+1)%3,(axis+2)%3]
    cuts = np.column_stack([np.zeros(len(plates)),coords[:,:,axis]])
    signs = cuts < cut
    patterns = signs @ np.array([1,2,4,8])
    accum = 0.
    for pattern in range(1,15):
        keep = patterns == pattern
        if not keep.any():
            continue
        t = np.concatenate((np.zeros((keep.sum(),1,3)),coords[keep]),axis=1)
        under = [i for i in range(4) if pattern & (1<<i)]
        over = [i for i in range(4) if not pattern & (1<<i)]
        if len(over)==1:
            under,over=over,under
        edges = [(under[0],j) for j in over] if len(under)==1 else (
            [(under[0],over[0]),(under[0],over[1]),(under[1],over[1]),(under[1],over[0])])
        polygon=[]
        for i,j in edges:
            a,b=t[:,i],t[:,j]
            f=(cut-a[:,axis])/(b[:,axis]-a[:,axis])
            polygon.append(a[:,axes]+f[:,None]*(b[:,axes]-a[:,axes]))
        for j in range(1,len(polygon)-1):
            b,c=polygon[j]-polygon[0],polygon[j+1]-polygon[0]
            accum+=np.abs(b[:,0]*c[:,1]-b[:,1]*c[:,0]).sum()/2
    return float(accum)


def main():
    models=json.loads((ROOT/'web/math/bennu-sections/source.json').read_bytes())['models']
    errors=[]
    for code,model in zip(CODES,models,strict=True):
        assert model['code']==code
        stem=f'bennu_g_{code}mm_alt_obj_0000n00000_v021a'
        h=spice.dasopr(str(CACHE/(stem+'.bds')))
        try:
            seg=spice.dlabfs(h);nv,nf=spice.dskz02(h,seg)
            v=spice.dskv02(h,seg,1,nv)*1000
            f=spice.dskp02(h,seg,1,nf)-1
        finally:
            spice.dascls(h)
        raw=gzip.decompress((MEDIA/(code+'.mesh.gz')).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==model['decodedSHA256']
        assert np.array_equal(np.frombuffer(raw,dtype='<f8',count=nv*3).reshape(-1,3),v)
        assert np.array_equal(np.frombuffer(raw,dtype='<u4',offset=nv*24).reshape(-1,3),f)
        a,b,c=v[f].transpose(1,0,2)
        normals=np.cross(b-a,c-a)
        # Flux through the closed surface gives the same volume with a different origin.
        center=np.mean(v,axis=0)
        volume=np.einsum('ij,ij->i',normals,(a+b+c)/3-center).sum()/6
        assert abs(model['volumeM3']-volume)<.0001
        assert np.all(np.einsum('ij,ij->i',a,normals)>0)
        for ax in range(3):
            low,high=model['bounds']
            for k in (1,16,32,48,64,80,96,112,127):
                cut=low[ax]+k*(high[ax]-low[ax])/128
                error=abs(tetra_sections(v,f,ax,cut)-model['profiles'][ax][k])
                errors.append(error);assert error<.0001,(code,ax,k,error)
        print(f"{code}: {nv} original vertices, {nf} faces, volume {volume:.3f} m³")
    print(f"{len(errors)} independent tetrahedron sections, maximum difference {max(errors):.9f} m²")


if __name__=='__main__':
    main()
