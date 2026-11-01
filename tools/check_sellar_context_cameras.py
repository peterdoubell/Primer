"""Verify both source layers share the captured GPU camera and source metric."""
from pathlib import Path
import argparse,gzip,json,struct
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

def read_mesh(path):
    raw=gzip.decompress(path.read_bytes());n,t=struct.unpack('<II',raw[4:12])
    points=np.frombuffer(raw,dtype='<f4',count=n*3,offset=16).reshape(-1,3).astype(float)
    indices=np.frombuffer(raw,dtype='<u4',offset=16+n*12).reshape(-1,3)
    assert len(indices)==t
    return points,indices

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--evidence',type=Path,default=ROOT/'docs/sellar-source-interfaces-review-20261101');parser.add_argument('--browser-proof',type=Path);parser.add_argument('--output',type=Path);args=parser.parse_args();d=args.evidence
    manifest=json.loads((d/'viewer/manifest.json').read_bytes());context=json.loads((d/'viewer/context-source.json').read_bytes());browser=json.loads((args.browser_proof or d/'browser-proof.json').read_bytes())
    points,indices=read_mesh(d/'viewer/source-contacts.mesh.gz')
    classes={row['code']:read_mesh(ROOT/'web/anatomy'/row['sourceAtlas']/row['file'])[0]for row in context['meshes']}
    maximum_clip=0.;maximum_rigid=0.;context_states=0;contact_states=0
    for camera in browser['cameras']:
        first,second=map(int,camera['pair'].split(':'));group=next(g for g in manifest['groups']if g['firstCode']==first and g['secondCode']==second)
        contact=points[np.unique(indices[group['firstTriangle']:group['firstTriangle']+group['triangles']])]
        assert camera['selection']['firstTriangle']==group['firstTriangle']and camera['selection']['triangles']==group['triangles']
        assert camera['contextCodes']==[first,second]
        if camera['framing']=='context':
            selected=np.concatenate([contact,classes[first],classes[second]]);context_states+=1
        else:
            assert camera['framing']=='contact';selected=contact;contact_states+=1
        low,high=selected.min(0),selected.max(0);center=(low+high)*.5
        assert camera['center']==np.asarray(center,dtype='<f4').astype(float).tolist()
        expected_radius=np.float32(np.linalg.norm((high-low)*.5)*1.12)
        assert camera['radius']==float(expected_radius)
        basis=np.array([camera['right'],camera['up'],camera['depth']]);error=float(np.max(abs(np.einsum('ij,kj->ik',basis,basis)-np.eye(3))))
        assert error<2e-7;maximum_rigid=max(maximum_rigid,error)
        if camera['contextShown']:
            other=camera['contextCamera'];assert other is not None
            for key,main_key in [('center','center'),('basisRight','right'),('basisUp','up'),('basisDepth','depth'),('radius','radius'),('aspect','aspect')]:assert other[key]==camera[main_key]
        relative=selected-center;world=np.column_stack([relative[:,0],relative[:,2],-relative[:,1]])
        projected=np.einsum('ij,kj->ik',world,basis)/np.array([camera['radius']*camera['aspect'],camera['radius'],4*camera['radius']])
        clip=float(np.max(abs(projected)));assert clip<1;maximum_clip=max(maximum_clip,clip)
    assert context_states==216 and contact_states==144
    result={'allPassed':True,'actualGPUUniformCameraStates':len(browser['cameras']),'wholeContextFramingStates':context_states,'contactOnlyFramingStates':contact_states,'allIntendedSourceVerticesInsideFrustum':True,'allVisibleLayersUseIdenticalGPUCameraUniforms':True,'maxAbsoluteClipCoordinate':maximum_clip,'maxGPUCameraBasisRigidError':maximum_rigid,'sourceCoordinatesFitted':False,'clinicalApproval':False}
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
