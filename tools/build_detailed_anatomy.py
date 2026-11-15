#!/usr/bin/env python3
"""Build selected real anatomical meshes from the official BodyParts3D 4.0 archive.

The source data is CC BY 4.0 (license updated 2025-02-25). This script selects
meshes, preserves their registered coordinates, calculates display normals, and
packs them for local WebGL use. No AI or procedural anatomy is generated.
"""
from __future__ import annotations
import collections, concurrent.futures, hashlib, io, json, math, pathlib, struct, urllib.request, zipfile, zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = pathlib.Path('/tmp/primer-bodyparts3d')
DEST = ROOT / 'web/anatomy/bodyparts3d'
BASE = 'https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/'
ARCHIVE = BASE + 'isa_BP3D_4.0_obj_99.zip'

REGIONS = {
 'shoulder': {'title':'Shoulder', 'names': ['right scapula','right clavicle','right humerus','right supraspinatus','right infraspinatus muscle','right subscapularis','right teres minor','long head of right biceps brachii'], 'bone_count':3},
 'elbow': {'title':'Elbow', 'names':['right humerus','right radius','right ulna','right brachialis','long head of right biceps brachii','long head of right triceps brachii'], 'bone_count':3},
 'hip': {'title':'Hip', 'names':['right hip bone','sacrum','right femur','right gluteus medius','right gluteus minimus','right iliacus','right psoas major'], 'bone_count':3},
 'knee': {'title':'Knee', 'names':['right femur','right tibia','right fibula','right patella','right vastus medialis','right vastus lateralis','medial head of right gastrocnemius','lateral head of right gastrocnemius'], 'bone_count':4},
 'ankle': {'title':'Ankle and foot', 'names':['right tibia','right fibula','right talus','right calcaneus','navicular bone of right foot','right cuboid bone','right medial cuneiform bone','right intermediate cuneiform bone','right lateral cuneiform bone','right first metatarsal bone','right second metatarsal bone','right third metatarsal bone','right fourth metatarsal bone','right fifth metatarsal bone','right calcaneal tendon','right tibialis posterior','right tibialis anterior'], 'bone_count':14},
 'wrist': {'title':'Wrist and carpal arch', 'names':['right radius','right ulna','right scaphoid','right lunate','right triquetral','right pisiform','right trapezium','right trapezoid','right capitate','right hamate','right first metacarpal bone','right second metacarpal bone','right third metacarpal bone','right fourth metacarpal bone','right fifth metacarpal bone','right flexor carpi radialis','right extensor carpi radialis longus','right extensor carpi ulnaris'], 'bone_count':15},
 'coronary': {'title':'Heart and coronary arteries','names':['wall of ventricle','wall of right atrium','wall of left atrium','ascending aorta','trunk of right coronary artery','trunk of left coronary artery','trunk of anterior interventricular branch of left coronary artery','circumflex branch of left coronary artery','posterior interventricular branch of right coronary artery'], 'bone_count':4, 'labels':['Heart','Coronaries'], 'side':'whole organ'},
 'prostate': {'title':'Prostate and neighbouring organs','names':['prostate','urinary bladder','right seminal vesicle','left seminal vesicle'], 'bone_count':1, 'labels':['Prostate','Neighbours'], 'side':'pelvis'},
 'renal': {'title':'Kidneys and urinary tract','names':['right kidney','left kidney','right ureter','left ureter','urinary bladder','right renal artery','left renal artery'], 'bone_count':2, 'labels':['Kidneys','Tracts / vessels'], 'side':'bilateral'},
 'liver': {'title':'Liver segments','names':['caudate lobe of liver','hepatovenous segment ii','hepatovenous segment iii','hepatovenous segment iv','hepatovenous segment v','hepatovenous segment vi','hepatovenous segment vii','hepatovenous segment viii','gallbladder','trunk of portal vein','right hepatic vein','middle hepatic vein','left hepatic vein'], 'bone_count':8, 'labels':['Segments','Vessels / gallbladder'], 'side':'whole organ'},
 'brain': {'title':'Brain','names':['right cerebral hemisphere','left cerebral hemisphere','cerebellum','right lateral ventricle','left lateral ventricle','third ventricle','fourth ventricle'], 'bone_count':3, 'labels':['Brain','Ventricles'], 'side':'bilateral'},
}

def fetch(url, headers=None):
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers or {}),timeout=90) as r:
  return r.read()

def index():
 path=CACHE/'zip-index.json'
 if path.exists(): return json.loads(path.read_text())
 tail=fetch(ARCHIVE,{'Range':'bytes=-65536'})
 marker=tail.rfind(b'PK\x05\x06'); e=struct.unpack('<4s4H2LH',tail[marker:marker+22]);size,start=e[5:7]
 data=fetch(ARCHIVE,{'Range':f'bytes={start}-{start+size+21}'})
 z=zipfile.ZipFile(io.BytesIO(data))
 result={q.filename:{'size':q.compress_size,'offset':q.header_offset+start,'compression':q.compress_type} for q in z.infolist()}
 path.write_text(json.dumps(result));return result

def download(fid, archive_index):
 p=CACHE/(fid+'.obj')
 if not p.exists():
  ent=archive_index['isa_BP3D_4.0_obj_99/'+fid+'.obj'];off=ent['offset']
  data=fetch(ARCHIVE,{'Range':f"bytes={off}-{off+ent['size']+256}"})
  if data[:4]!=b'PK\x03\x04':raise ValueError('Bad local header for '+fid)
  namelen,extra=struct.unpack_from('<HH',data,26);raw=data[30+namelen+extra:30+namelen+extra+ent['size']]
  p.write_bytes(zlib.decompress(raw,-15) if ent['compression']==8 else raw)
 return p

def mesh(fid,paths):
 positions=[];indices=[]
 for path in paths:
  offset=len(positions)
  for line in path.read_text().splitlines():
   bits=line.split()
   if not bits:continue
   if bits[0]=='v':positions.append([float(v) for v in bits[1:4]])
   if bits[0]=='f':
    face=[int(s.split('/')[0])-1+offset for s in bits[1:]]
    for i in range(1,len(face)-1):indices.extend([face[0],face[i],face[i+1]])
 normals=[[0.,0.,0.] for _ in positions]
 for i in range(0,len(indices),3):
  ia,ib,ic=indices[i:i+3];a,b,c=[positions[j] for j in (ia,ib,ic)]
  u=[b[j]-a[j] for j in range(3)];v=[c[j]-a[j] for j in range(3)]
  normal=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
  for ix in (ia,ib,ic):
   for j in range(3):normals[ix][j]+=normal[j]
 for n in normals:
  length=math.sqrt(sum(v*v for v in n)) or 1
  for j in range(3):n[j]/=length
 output=bytearray(struct.pack('<4sII',b'BP3D',len(positions),len(indices)))
 for p in positions:output.extend(struct.pack('<3f',*p))
 for n in normals:output.extend(struct.pack('<3f',*n))
 output.extend(struct.pack('<'+'I'*len(indices),*indices))
 dest=DEST/(fid+'.bin');dest.write_bytes(output)
 return {'id':fid,'file':'/app/anatomy/bodyparts3d/'+fid+'.bin','vertices':len(positions),'triangles':len(indices)//3,'bounds':[[min(p[j] for p in positions) for j in range(3)],[max(p[j] for p in positions) for j in range(3)]],'source_sha256':{path.stem:hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},'sha256':hashlib.sha256(output).hexdigest(),'bytes':len(output)}

def main():
 CACHE.mkdir(exist_ok=True);DEST.mkdir(parents=True,exist_ok=True)
 for name in ['isa_parts_list_e.txt','isa_element_parts.txt','partof_element_parts.txt']:
  p=CACHE/name
  if not p.exists():p.write_bytes(fetch(BASE+name))
 elements={}
 for filename in ['partof_element_parts.txt','isa_element_parts.txt']:
  rows=collections.defaultdict(list)
  for l in (CACHE/filename).read_text().splitlines()[1:]:
   row=l.split('\t')
   if len(row)>=3:rows[row[1]].append(row)
  elements.update(rows)
 names={n for r in REGIONS.values() for n in r['names']}
 selected={}
 for name in sorted(names):
  if name not in elements:raise ValueError('No source mesh: '+name)
  rows=elements[name];fids=sorted({r[2] for r in rows});fid=fids[0] if len(fids)==1 else rows[0][0]
  selected[fid]={'name':name,'fma':rows[0][0],'source_ids':fids}
 archive_index=index();files={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
  pending={pool.submit(download,fid,archive_index):fid for fid in {fid for p in selected.values() for fid in p['source_ids']}}
  for fut in concurrent.futures.as_completed(pending):files[pending[fut]]=fut.result()
 for fid,item in selected.items():
  item.update(mesh(fid,[files[x] for x in item['source_ids']]));print(fid,item['name'],item['triangles'],flush=True)
 for old in DEST.glob('*.bin'):
  if old.stem not in selected:old.unlink()
 byname={q['name']:q for q in selected.values()}
 regions={}
 for key,region in REGIONS.items():
  regions[key]={'title':region['title'],'side':region.get('side','right'),'labels':region.get('labels',['Bones','Soft tissue']),'parts':[{'id':byname[n]['id'],'layer':'bone' if i<region['bone_count'] else 'soft'} for i,n in enumerate(region['names'])]}
 manifest={'dataset':'BodyParts3D 4.0','license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','source_url':'https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html','source_archive':ARCHIVE,'license_evidence':'https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/README_e.html#license','attribution':'BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International','adaptations':'Selected meshes from the 99% polygon-reduced archive, converted to indexed binary geometry with averaged vertex normals. Registered source coordinates preserved. Display cropping only; no generated anatomy.','parts':selected,'regions':regions}
 (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('TOTAL',len(selected),'meshes',sum(p['bytes'] for p in selected.values()),'bytes')
if __name__=='__main__':main()
