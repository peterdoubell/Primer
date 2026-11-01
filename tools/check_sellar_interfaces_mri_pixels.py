from pathlib import Path
import json,gzip,hashlib,os
import numpy as np

def main():
    R=Path(__file__).resolve().parents[1];parser=__import__('argparse').ArgumentParser();parser.add_argument('--evidence',type=Path,default=R/'docs/sellar-source-interfaces-review-20261101');parser.add_argument('--output',type=Path);args=parser.parse_args();D=args.evidence;S=R/'web/anatomy/spl-nac-limbic';m=json.loads((S/'manifest.json').read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
    def array(row):
     packed=(S/row['file']).read_bytes();assert sha(packed)==row['gzipSHA256'];raw=gzip.decompress(packed);assert sha(raw)==row['decodedSHA256'];return np.frombuffer(raw,dtype=row['dtype']).reshape(row['shape'],order='F')
    scans={k:array(v)for k,v in m['volumes'].items()};labels=array(m['labelVolume']);cases=json.loads((D/os.environ.get('MRI_CASES','mri-browser-cases.json')).read_bytes());pixels=0
    for case in cases:
     white,cortical=map(int,case['pair'].split(':'));row=m['volumes'][case['contrast']];probe=case['probe'];point=case.get('inspectionVoxel',case['anchor']['sourceIJK']);assert probe['value']==float(scans[case['contrast']][tuple(point)]);assert probe['voxel']==point
     if 'expectedVoxel'in case:assert point==case['expectedVoxel']
     sample=np.floor((np.einsum('ij,jk,k->i',np.linalg.inv(m['labelVolume']['voxelToRAS']),np.asarray(row['voxelToRAS']),np.array([*point,1])))[:3]+.5).astype(int);inside=np.all((sample>=0)&(sample<np.asarray(labels.shape)));assert probe['label']==(int(labels[tuple(sample)])if inside else None)
     if case.get('atSourceAnchor',True):assert probe['label']==(white if case['side']=='first'else cortical)
     for state in case['states']:
      n,u,v={'axial':(1,2,0),'coronal':(0,2,1),'sagittal':(2,0,1)}[state['plane']];assert state['spec']['fixed']==n and state['spec']['horizontal']==u and state['spec']['vertical']==v;assert not state['spec']['flipHorizontal']and not state['spec']['flipVertical'];assert state['slice']==point[n]
      y,x=np.indices((row['shape'][v],row['shape'][u]));points=np.ones((*x.shape,4));points[...,u]=x;points[...,v]=y;points[...,n]=state['slice'];values=scans[case['contrast']][tuple(points[...,:3].astype(int).transpose(2,0,1))].astype(np.float64);grey=np.floor(np.clip(255*(values-state['low'])/(state['high']-state['low']),0,255)).astype(np.uint8);rgb=np.repeat(grey[...,None],3,axis=2);mapping=np.einsum('ij,jk->ik',np.linalg.inv(m['labelVolume']['voxelToRAS']),np.asarray(row['voxelToRAS']));coords=np.floor(np.einsum('...j,ij->...i',points,mapping)[...,:3]+.5).astype(int);inside=np.all((coords>=0)&(coords<np.asarray(labels.shape)),axis=-1);codes=np.zeros(x.shape,np.int16);codes[inside]=labels[tuple(coords[inside].T)];marked=rgb.copy()
      for code,color in [(white,[100,160,240]),(cortical,[255,128,0])]:
       mask=codes==code;marked[mask]=np.floor(.55*rgb[mask]+.45*np.array(color)+.5).astype(np.uint8)
      for mode,color in [('plain',rgb),('labels',marked)]:
       expected=np.concatenate([color,np.full((*x.shape,1),255,np.uint8)],axis=2);actual=next(p for p in case['pixels']if p['plane']==state['plane']and p['mode']==mode);assert actual['sha256']==sha(expected.tobytes()),(case['pair'],case['contrast'],case['side'],state['plane'],mode);pixels+=x.size
    for case in cases:
     point=case.get('inspectionVoxel',case['anchor']['sourceIJK'])
     for cross in case['crosshairs']:
      n,u,v={'axial':(1,2,0),'coronal':(0,2,1),'sagittal':(2,0,1)}[cross['plane']];assert cross['pixel']==[point[u],point[v]]
    proof={'crosshairLocationsChecked':sum(len(c['crosshairs'])for c in cases),'allPassed':True,'states':len(cases),'actualCanvasPixelsCompared':pixels,'sourceSamplesResampled':False,'anatomicalVisibilityVerified':False,'clinicalApproval':False};
    if args.output:args.output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))

if __name__=='__main__':main()
