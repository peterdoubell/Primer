from pathlib import Path
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[2];D=R/'.research/epilepsy-grey-white-20261030';p=json.loads((D/'contact-proof.json').read_bytes());payload=D/'source-grey-white-contacts.npz';assert hashlib.sha256(payload.read_bytes()).hexdigest()==p['payloadSHA256'];z=np.load(payload);faces=z['faces'];centres=z['centresRAS'];rows=[]
for pair in p['pairs']:
 opposite=('left' in pair['whiteName'] and 'right' in pair['corticalName'])or('right' in pair['whiteName'] and 'left' in pair['corticalName'])
 if not opposite:continue
 mask=(faces[:,5]==pair['whiteCode'])&(faces[:,6]==pair['corticalCode']);selected=faces[mask];world=centres[mask];assert len(selected)==pair['sourceContactFaces']
 contacts=[]
 for f,point in zip(selected,world):
  owner=f[:3].copy();neighbour=owner.copy();neighbour[f[3]]+=f[4]
  contacts.append({'whiteSourceIJK':owner.tolist(),'corticalSourceIJK':neighbour.tolist(),'faceAxis':int(f[3]),'faceSign':int(f[4]),'centreRASmm':point.tolist()})
 rows.append({**pair,'contacts':contacts,'reviewStatus':'unresolved source adjacency; no anatomical error or pathology inferred'})
assert sum(len(r['contacts'])for r in rows)==31
covered=set(int(c) for c in faces[:,6]);missing=sorted(set(p['corticalCodes'])-covered)
proof={'sourceContactPayloadSHA256':p['payloadSHA256'],'oppositeNamedSideContacts':rows,'oppositeNamedSideFaceCount':31,'corticalClassesWithAtLeastOneContact':len(covered),'corticalClassesWithoutContact':missing,'contactsRetainedInMesh':True,'anatomicalDefectInferred':False,'patientAbnormalityInferred':False,'nextReview':'Inspect original MRI, label grids and anatomical context at each listed position; do not repair or discard source cells based on label names alone.','clinicalApproval':False};(D/'side-contact-review.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'oppositeNamedSideFaces':31,'sourceClassPairs':len(rows),'corticalClassesWithContact':len(covered),'missingCorticalClasses':missing}))
