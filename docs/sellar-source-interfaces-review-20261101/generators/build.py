from pathlib import Path
import gzip,hashlib,json,struct,html,textwrap
import numpy as np
R=Path.cwd();D=R/'.research/sellar-source-interfaces-20261101';P=D/'package';P.mkdir(exist_ok=True);S=D/'schematics';S.mkdir(exist_ok=True);audit=json.loads((D/'audit.json').read_bytes());m=json.loads((R/'web/anatomy/spl-nac-limbic/manifest.json').read_bytes());v=m['labelVolume'];raw=gzip.decompress((R/'web/anatomy/spl-nac-limbic'/v['file']).read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(raw)==audit['labelDecodedSHA256'];labels=np.frombuffer(raw,dtype=v['dtype']).reshape(v['shape'],order='F');A=np.asarray(audit['sourceAffine']);faces=np.load(D/'source-faces.npz')['faces'];models=[];schematics=[];lut={}
lutraw=gzip.decompress((R/'docs/spl-limbic-source-review-20261016/source-evidence/slicer--colortables--hncma-atlas-lut.ctbl.gz').read_bytes()).decode()
for line in lutraw.splitlines():
 fields=line.split()
 if fields and not fields[0].startswith('#'):
  try:lut[int(fields[0])]=fields[1]
  except(ValueError,IndexError):pass
world=lambda p:np.einsum('...j,ij->...i',p,A[:3,:3])+A[:3,3]
for pair in audit['pairs']:
 if not pair['sharedCellFaces']:continue
 codes=pair['codes'];slug='contact-'+str(codes[0])+'-'+str(codes[1]);selected=faces[(faces[:,5]==codes[0])&(faces[:,6]==codes[1])];vertices=[];lookup={};triangles=[]
 for f in selected:
  p=f[:3];axis=int(f[3]);sign=int(f[4]);others=[i for i in range(3)if i!=axis];corners=[]
  for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]:
   q=2*p.copy();q[axis]+=sign;q[others[0]]+=x;q[others[1]]+=y;key=tuple(map(int,q))
   if key not in lookup:lookup[key]=len(vertices);vertices.append(q)
   corners.append(lookup[key])
  xyz=world(np.asarray([vertices[i]for i in corners])*.5)
  if np.dot(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]),A[:3,axis]*sign)<0:corners=[corners[0],corners[3],corners[2],corners[1]]
  triangles.extend([corners[:3],[corners[0],corners[2],corners[3]]])
 native=np.asarray(vertices)*.5;positions=world(native).astype('<f4');indices=np.asarray(triangles,dtype='<u4');payload=struct.pack('<4sIII',b'HVX1',len(positions),len(indices),0)+positions.tobytes()+indices.tobytes();packed=gzip.compress(payload,mtime=0);file=slug+'.mesh.gz';(P/file).write_bytes(packed);fraw=selected.astype('<i4').tobytes();fpacked=gzip.compress(fraw,mtime=0);ffile=slug+'-faces.bin.gz';(P/ffile).write_bytes(fpacked);anchor=selected[len(selected)//2];opposite=('left' in pair['names'][0]and 'right'in pair['names'][1])or('right'in pair['names'][0]and 'left'in pair['names'][1]);models.append({'id':slug,'sourceCodes':codes,'sourceNames':pair['names'],'file':file,'gzipBytes':len(packed),'gzipSHA256':sha(packed),'decodedBytes':len(payload),'decodedSHA256':sha(payload),'vertices':len(positions),'triangles':len(indices),'positionByteSHA256':sha(positions.tobytes()),'indexByteSHA256':sha(indices.tobytes()),'sourceFaces':len(selected),'sourceCellFaceAreaMm2':len(selected),'sourceFaceProvenance':{'file':ffile,'dtype':'<i4','fields':['ownerI','ownerJ','ownerK','nativeAxis','sign','ownerCode','neighbourCode'],'gzipBytes':len(fpacked),'gzipSHA256':sha(fpacked),'decodedSHA256':sha(fraw)},'anchorOwnerIJK':anchor[:3].tolist(),'anchorRAS':world(anchor[:3]+np.eye(3)[anchor[3]]*anchor[4]*.5).tolist(),'boundsRAS':[positions.min(0).tolist(),positions.max(0).tolist()],'oppositeSideNamedSourceContact':bool(opposite),'anatomicalConnectionVerified':False,'sourceToRAS':audit['sourceAffine'],'positionsAlreadyRAS':True,'coordinateSystem':'RAS','spaceUnits':'mm','sourceSamplesChanged':False,'smoothedOrRepaired':False,'fittedRegistration':False,'clinicalApproval':False})
 cells=np.argwhere(np.isin(labels,codes));lo=np.maximum(cells.min(0)-3,0);hi=np.minimum(cells.max(0)+3,np.asarray(labels.shape)-1);focus=anchor[:3];plotrows=[]
 for plane,wa,edges in [('axial',[2,0,1],['R','L','A','P']),('coronal',[1,0,2],['R','L','S','I']),('sagittal',[0,1,2],['A','P','S','I'])]:
  n,u,w=[int(np.flatnonzero(A[i,:3])[0])for i in wa];flip_u=A[wa[1],u]>0;flip_v=A[wa[2],w]>0;W=int(hi[u]-lo[u]+1);H=int(hi[w]-lo[w]+1);yy,xx=np.indices((H,W));ijk=np.zeros((3,H,W),int);ijk[n]=focus[n];ijk[u]=hi[u]-xx if flip_u else lo[u]+xx;ijk[w]=hi[w]-yy if flip_v else lo[w]+yy;values=labels[tuple(ijk)];scale=min(330/W,285/H);tx=(400-W*scale)/2;ty=148;bottom=ty+H*scale;lines=[]
  parts=['<svg xmlns="http://www.w3.org/2000/svg" width="400" height="520" viewBox="0 0 400 520">','<rect width="400" height="520" fill="#101820"/>']
  title=f'{codes[0]} / {codes[1]} · {plane}'
  parts.append(f'<text x="15" y="24" fill="white" font-family="sans-serif" font-size="17">{html.escape(title)}</text>')
  for line_no,line in enumerate(textwrap.wrap(' / '.join(n.replace('_',' ')for n in pair['names']),width=47)):parts.append(f'<text x="15" y="{46+line_no*16}" fill="#ccd8e4" font-family="sans-serif" font-size="13">{html.escape(line)}</text>')
  parts.append(f'<text x="15" y="114" fill="#ccd8e4" font-family="sans-serif" font-size="13">Native slice {focus[n]}; RAS {"xyz"[wa[0]]}={world(focus)[wa[0]]:g} mm</text>');parts.append(f'<text x="15" y="134" fill="#ccd8e4" font-family="sans-serif" font-size="13">Left/right/top/bottom: {" / ".join(edges)}</text>');parts.append(f'<g transform="translate({tx:g} {ty}) scale({scale:g})" shape-rendering="crispEdges" data-plane="{plane}" data-native-fixed-axis="{n}" data-native-slice="{focus[n]}" data-native-u="{u}" data-native-v="{w}" data-native-low="{",".join(map(str,lo))}" data-native-high="{",".join(map(str,hi))}" data-flip-u="{int(flip_u)}" data-flip-v="{int(flip_v)}"><rect width="{W}" height="{H}" fill="#080c12"/>')
  for y in range(H):
   x=0
   while x<W:
    value=int(values[y,x]);end=x+1
    while end<W and int(values[y,end])==value:end+=1
    if value:
     color='#64a0f0'if value==codes[0]else '#ff8000'if value==codes[1]else '#334657';parts.append(f'<rect x="{x}" y="{y}" width="{end-x}" height="1" fill="{color}" data-source-code="{value}"><title>{value}: {html.escape(lut.get(value,"not named in publisher LUT"))}</title></rect>')
    x=end
  for faceid,f in enumerate(selected):
   axis=int(f[3]);sign=int(f[4]);owner=f[:3]
   if axis==n or owner[n]!=focus[n]:continue
   # A face intersects this native cell-centre plane in a unit segment.
   other=next(i for i in range(3)if i not in [n,axis]);p=owner.astype(float);q=p.copy();p[axis]+=sign*.5;q[axis]+=sign*.5;p[other]-=.5;q[other]+=.5
   display=lambda z:np.array([hi[u]-z[u]+.5 if flip_u else z[u]-lo[u]+.5,hi[w]-z[w]+.5 if flip_v else z[w]-lo[w]+.5]);a,b=display(p),display(q);parts.append(f'<line x1="{a[0]:g}" y1="{a[1]:g}" x2="{b[0]:g}" y2="{b[1]:g}" stroke="#ff61d8" stroke-width="1.6" vector-effect="non-scaling-stroke" data-source-face-id="{faceid}"/>');lines.append({'sourceFaceIndex':faceid,'sourceEndpointsIJK':[p.tolist(),q.tolist()],'displayEndpoints':[a.tolist(),b.tolist()]})
  parts.append('</g>');parts.extend(['<text x="15" y="458" fill="#64a0f0" font-family="sans-serif" font-size="13">Blue: first class; orange: second class</text>','<text x="15" y="478" fill="#ff61d8" font-family="sans-serif" font-size="13">Magenta: exact shared-cell face section</text>','<text x="15" y="500" fill="#ccd8e4" font-family="sans-serif" font-size="12">Source cells; not MRI signal or a verified biological wall.</text>','</svg>']);name=slug+'-'+plane+'.svg';data='\n'.join(parts).encode();(S/name).write_bytes(data);plotrows.append({'plane':plane,'file':name,'sha256':sha(data),'nativeFixedAxis':n,'nativeSlice':int(focus[n]),'nativeU':u,'nativeV':w,'cropLowIJK':lo.tolist(),'cropHighIJK':hi.tolist(),'widthCells':W,'heightCells':H,'sourcePlaneBytesSHA256':sha(values.astype('<i2').tobytes()),'contactSections':lines})
 schematics.append({'sourceCodes':codes,'pair':slug,'oppositeSideNamedSourceContact':bool(opposite),'sourceFaces':len(selected),'planes':plotrows})
manifest={'sourceCommit':audit['sourceCommit'],'labelDecodedSHA256':audit['labelDecodedSHA256'],'sourceClasses':audit['sourceClasses'],'sourceFaceCount':len(faces),'sourceContactPairs':len(models),'models':models,'sourceSamplesChanged':False,'gapsBridged':False,'contactsAreNotConfirmedAnatomicalInterfaces':True,'clinicalApproval':False,'wholeGoalComplete':False};(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(D/'schematics.json').write_text(json.dumps(schematics,indent=2)+'\n');print({'models':len(models),'faces':len(faces),'triangles':sum(r['triangles']for r in models),'SVGsections':len(schematics)*3,'oppositeSideNamedPairs':[r['sourceCodes']for r in models if r['oppositeSideNamedSourceContact']]})
