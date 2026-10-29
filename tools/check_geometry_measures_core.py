from pathlib import Path
import json,subprocess,hashlib,math
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'.research/geometry-fidelity-20261029'
D.mkdir(exist_ok=True)
cases=[]
for w in range(1,13):
 for h in range(1,13):
  cases.append(dict(kind='rectangle',width=w,height=h))
  for apex in range(w+1):cases.append(dict(kind='triangle',width=w,height=h,apex=apex))
  for cw in range(1,w):
   for ch in range(1,h):cases.append(dict(kind='cutout',width=w,height=h,cutWidth=cw,cutHeight=ch))
  for depth in range(1,13):cases.append(dict(kind='cuboid',width=w,height=h,depth=depth))
(D/'cases.json').write_text(json.dumps(cases))
script="""const fs=require('fs'),core=require('../../web/geometry-measures-core.js');let out=[];for(const c of JSON.parse(fs.readFileSync('cases.json'))){const r=c.kind==='cuboid'?core.cuboid(c):core.planar(c);if(r.cubes){const cells=new Set(r.cubes.map(p=>p.join(',')));if(cells.size!==r.volume)throw Error('Duplicate cube');for(const f of r.faces){const n=[...f.cell];n[f.axis]+=f.sign;if(cells.has(n.join(',')))throw Error('Internal face');}out.push({volume:r.volume,surface:r.surfaceArea,layerArea:r.layerArea,layers:r.layers});}else out.push({area:r.area,perimeter:r.perimeter,cells:r.cells.length,polygon:r.polygon});}fs.writeFileSync('results.json',JSON.stringify(out));"""
(D/'check-core.cjs').write_text(script);subprocess.run(['node','check-core.cjs'],cwd=D,check=True);results=json.loads((D/'results.json').read_bytes())
for c,r in zip(cases,results,strict=True):
 w,h=c['width'],c['height'];kind=c['kind']
 if kind=='cuboid':
  d=c['depth'];assert r==dict(volume=w*h*d,surface=2*(w*h+w*d+h*d),layerArea=w*d,layers=h)
 elif kind=='triangle':
  a=c['apex'];assert r['area']==w*h/2;assert abs(r['perimeter']-(w+math.hypot(a,h)+math.hypot(w-a,h)))<1e-10
 else:
  area=w*h-(c['cutWidth']*c['cutHeight'] if kind=='cutout' else 0);assert r['area']==r['cells']==area;assert r['perimeter']==2*(w+h)
  # Independent lattice boundary edge cancellation checks perimeter, including the concave corner.
  occupied={(x,y)for x in range(w)for y in range(h) if kind!='cutout' or x<w-c['cutWidth'] or y<h-c['cutHeight']}
  boundary=sum((x+dx,y+dy)not in occupied for x,y in occupied for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]);assert boundary==r['perimeter']
proof=dict(allPassed=True,states=len(cases),coreSHA256=hashlib.sha256((ROOT/'web/geometry-measures-core.js').read_bytes()).hexdigest(),oracle='Independent closed-form triangle/cuboid formulas and lattice-boundary cancellation',integrated=False,visualVerificationPending=True)
(D/'core-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
