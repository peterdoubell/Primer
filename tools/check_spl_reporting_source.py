"""Independent current-file checks for every SPL reporting source cell boundary.

Does not import the mesh producer or infer clinical accuracy from exact geometry.
"""
from pathlib import Path
import gzip
import hashlib
import json
import struct
import numpy as np
from scipy.ndimage import label as connected

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'web/anatomy/spl-nac-reporting'
SHARED=ROOT/'web/anatomy/spl-nac-limbic'
DOCS=ROOT/'docs/spl-reporting-source-review-20261016'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def unpack(row,shared=False):
    data=((SHARED if shared else ASSETS)/row['file']).read_bytes();assert sha(data)==row['gzipSHA256']
    raw=gzip.decompress(data);assert len(raw)==row['byteLength'] and sha(raw)==row['decodedSHA256'];return raw

def verify():
    manifest=json.loads((ASSETS/'manifest.json').read_bytes());base_bytes=(SHARED/'manifest.json').read_bytes()
    assert sha(base_bytes)==manifest['sharedSourceManifestSHA256']=='204f87b6d88a9570eb34664497a1462a5d8bba1afa0c2f7abe1cdf11082de2e6'
    base=json.loads(base_bytes);source=manifest['labelVolume'];source_fields={k:v for k,v in source.items() if k!='sharedSource'};assert source_fields==base['labelVolume']
    for name,row in manifest['volumes'].items():assert {k:v for k,v in row.items() if k!='sharedSource'}==base['volumes'][name]
    labels=np.frombuffer(unpack(source,True),dtype='<i2').reshape((256,256,256),order='F')
    lut={}
    text=gzip.decompress((ROOT/'docs/spl-limbic-source-review-20261016/source-evidence/slicer--colortables--hncma-atlas-lut.ctbl.gz').read_bytes()).decode()
    for line in text.splitlines():
        fields=line.split()
        if fields and not fields[0].startswith('#'):lut[int(fields[0])]=(fields[1],list(map(int,fields[2:5])))
    descriptors={row['code']:row for row in manifest['labels']};assert len(descriptors)==217 and manifest['additionalSourceClassCount']==205 and manifest['generatedBoundaryPayloadCount']==207 and manifest['sharedBoundaryPayloadCount']==10
    meshes=manifest['labelMeshes'];assert len(meshes)==217 and {m['code'] for m in meshes}==set(descriptors)
    records=[]
    for mesh in meshes:
        code=mesh['code'];row=descriptors[code];assert (row['sourceName'],row['color'])==lut[code]
        raw=unpack(mesh,bool(mesh.get('sharedSource')));magic,vertices,triangles,reserved=struct.unpack_from('<4sIII',raw)
        assert (magic,vertices,triangles,reserved)==(b'HVX1',mesh['vertexCount'],mesh['triangleCount'],0)
        points=np.frombuffer(raw,dtype='<f4',offset=16,count=vertices*3).reshape(-1,3)
        indices=np.frombuffer(raw,dtype='<u4',offset=16+vertices*12).reshape(-1,3)
        assert len(raw)==16+vertices*12+triangles*12 and indices.max()<vertices and np.isfinite(points).all()
        assert sha(points.tobytes())==mesh['positionByteSHA256'] and sha(indices.tobytes())==mesh['indexByteSHA256']
        assert np.array_equal(points*2,np.rint(points*2))
        faces=np.frombuffer(unpack(mesh['faceProvenance'],bool(mesh.get('sharedSource'))),dtype='<i2').reshape(-1,5).astype(np.int64)
        assert len(faces)*2==triangles and np.all((faces[:,:3]>=0)&(faces[:,:3]<256))
        assert np.all((faces[:,3]>=0)&(faces[:,3]<3)) and np.all(np.abs(faces[:,4])==1)
        cells=np.argwhere(labels==code);assert len(cells)==row['sourceVoxelCount']==mesh['sourceVoxelCount']
        low=cells.min(0);high=cells.max(0)+1;slices=tuple(slice(int(a),int(b)) for a,b in zip(low,high));mask=labels[slices]==code
        padded=np.pad(mask,1);expected=[]
        for axis in range(3):
            for sign in (-1,1):
                neighbor=[slice(1,-1)]*3;neighbor[axis]=slice(2,None) if sign==1 else slice(None,-2)
                exposed=mask&~padded[tuple(neighbor)];p=np.argwhere(exposed)+low
                expected.append((p[:,0]+256*(p[:,1]+256*p[:,2]))*6+axis*2+int(sign==1))
        expected=np.sort(np.concatenate(expected));actual=(faces[:,0]+256*(faces[:,1]+256*faces[:,2]))*6+faces[:,3]*2+(faces[:,4]==1)
        assert len(actual)==len(np.unique(actual)) and np.array_equal(np.sort(actual),expected)
        xyz=points[indices].reshape(-1,2,3,3).astype(float);centres=128-faces[:,[2,0,1]]
        local=xyz-centres[:,None,None,:];world_axis=np.asarray([1,2,0])[faces[:,3]]
        for axis in range(3):
            use=world_axis==axis
            assert np.all(local[use,:,:,axis]==-faces[use,4,None,None]*.5)
            assert np.all(np.abs(local[use][:,:,:,np.arange(3)!=axis])==.5)
        cross=np.cross(xyz[:,:,1]-xyz[:,:,0],xyz[:,:,2]-xyz[:,:,0]);assert np.all((cross*cross).sum(2)==1)
        normals=np.zeros((len(faces),3));normals[np.arange(len(faces)),world_axis]=-faces[:,4]
        assert np.all((cross*normals[:,None,:]).sum(2)==1)
        common=(xyz[:,0,:,None,:]==xyz[:,1,None,:,:]).all(3).any(2);assert np.all(common.sum(1)==2)
        diagonal=xyz[:,0][common].reshape(-1,2,3);assert np.all(((diagonal[:,0]-diagonal[:,1])**2).sum(1)==2)
        component_counts={}
        for connectivity in (6,26):
            structure=np.ones((3,3,3),dtype='u1') if connectivity==26 else np.array([[[int(abs(i-1)+abs(j-1)+abs(k-1)<=1) for k in range(3)] for j in range(3)] for i in range(3)],dtype='u1')
            comp,n=connected(mask,structure);sizes=np.bincount(comp.ravel());component_counts[str(connectivity)]=sorted(sizes[1:].tolist(),reverse=True)
            if connectivity==26:
                seen=set()
                for c in row['components26']:
                    p=np.asarray(c['focusSourceIJK']);number=int(comp[tuple(p-low)]);assert number>0 and number not in seen and int(sizes[number])==c['sourceVoxelCount'];seen.add(number)
                    assert c['focusRAS']==(128-p[[2,0,1]]).tolist()
                assert len(seen)==n
        assert component_counts['26']==row['componentSizes26'] and component_counts['6']==row['components6']
        records.append({'code':code,'sourceVoxels':len(cells),'faces':len(faces),'triangles':triangles,'vertices':vertices,'allExposedFacesEqualIndependentOccupancyOracle':True,'allTrianglesAreExactOutwardCellFaces':True,'allComponentsRetained':True})
        print(json.dumps(records[-1]),flush=True)
    requirements=json.loads(gzip.decompress((DOCS/'requirements.json.gz').read_bytes()))
    for group in requirements['groups']:
        current=next(g for g in manifest['groups'] if g['id']==group['id']);assert current['codes']==group['available_distinct_current_label_codes']
        assert current['missing_or_unresolved_structures']==group['missing_or_unresolved_structures']
    result={'manifestSHA256':sha((ASSETS/'manifest.json').read_bytes()),'sourceClasses':217,'additionalSourceClasses':205,'generatedPayloads':207,'sharedPayloads':10,'rows':records,'allPassed':True,'clinicalApproval':False,'completeReportingAnatomyApproved':False}
    (DOCS/'current-source-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'}));return result
if __name__=='__main__':verify()
