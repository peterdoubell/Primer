from pathlib import Path
import json,hashlib
R=Path.cwd();D=R/'docs/sellar-source-interfaces-review-20261101';V=D/'viewer';manifest=json.loads((D/'manifest.json').read_bytes());codes={r['code']for r in manifest['sourceClasses']};rows=[];sources={};sha=lambda b:hashlib.sha256(b).hexdigest()
for atlas in ['spl-nac-limbic','spl-nac-reporting','spl-additional-source']:
 p=R/'web/anatomy'/atlas/'manifest.json';raw=p.read_bytes();m=json.loads(raw);sources[atlas]={'file':'/app/anatomy/'+atlas+'/manifest.json','sha256':sha(raw)}
 for row in m['labelMeshes']:
  if row['code']in codes and not any(x['code']==row['code']for x in rows):rows.append(dict(row,sourceAtlas=atlas))
assert {r['code']for r in rows}==codes and len(rows)==21
context={'schemaVersion':1,'sourceCommit':'bec24db25aad5f7600e2df3becfb1f883e61ff56','sourceManifests':sources,'meshes':rows,'allOriginalSourceLabelComponentsRetained':True,'positionsAlreadyRAS':True,'sourceCoordinatesFitted':False,'clinicalApproval':False,'completeReportingCoverage':False};raw=(json.dumps(context,indent=2)+'\n').encode();(V/'context-source.json').write_bytes(raw);print(sha(raw))
p=V/'index.html';s=p.read_text();needle='<canvas id="mesh"';assert s.count(needle)==1;s=s if 'id="show-context"' in s else s.replace(needle,'<section aria-label="3D source context"><label><input id="show-context" type="checkbox" checked> Show transparent source-label context</label><label>3D framing <select id="framing"><option value="context">Fit complete source-label context</option><option value="contact">Fit selected contact only</option></select></label><p id="context-status" role="status"></p><p>Blue: first source class; orange: second source class; magenta: shared categorical-cell faces. Transparent context does not occlude the interface.</p></section>'+needle);p.write_text(s)
