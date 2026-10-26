"""Construct a pinned, append-only atlas extension in an explicit output folder."""
from pathlib import Path
import copy,gzip,hashlib,json,argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--intake',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();R=Path(__file__).resolve().parents[2];O=args.output;I=args.intake;O.mkdir(parents=True,exist_ok=True)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pinned(p,digest):
 raw=p.read_bytes()
 if sha(raw)!=digest:raise ValueError('Unreviewed input: '+str(p))
 return raw
base=pinned(R/'docs/holiatlas-schematic-review-20261026/before-hierarchy.json','d6b511eedcdabc09999581eb8b40c315eed388fb358ea15947739b8043682b13')
intake=pinned(I/'composition-manifest.json','63a6acae6d9dbfdbc41ede93ba2b3b423450ef0ded4ba1b32c139422b6305a4c')
v=json.loads(base);m=json.loads(intake);original=copy.deepcopy(v)
assert m['count']==2 and not m['clinicalApproval'] and not m['runtimeBound']
assert m['sourceArchiveSHA256']==v['sourceArchiveSHA256']
assert m['sourceLabelSHA256']==v['levels']['composition']['nativeSHA256']
for name,digest in m['proofs'].items():
 raw=pinned(I/name,digest)
 if name in ['boundary-proof.json','independent-verification.json']:assert json.loads(raw)['allPassed']
assert len(v['levels']['composition']['sourceClasses'])==16
assets={}
for code,item in enumerate(m['compositions'],17):
 side='right' if code==17 else 'left';identifier=side+'-angular-supramarginal-cortex'
 assert item['id']==identifier and item['sourceMemberCodes']==([170,178] if code==17 else [171,179])
 assert item['clinicalRequirementComplete'] is False
 payloads={}
 for kind,suffix in [('mesh','.mesh.gz'),('facesPayload','-faces.bin.gz')]:
  p=copy.deepcopy(item[kind]);assert p['file']==identifier+suffix
  encoded=pinned(I/p['file'],p['gzipSHA256']);decoded=gzip.decompress(encoded)
  assert len(encoded)==p['gzipBytes'] and len(decoded)==p['bytes'] and sha(decoded)==p['sha256']
  name='hierarchy-composition-'+identifier+suffix;(O/name).write_bytes(encoded);p['file']=name;payloads[kind]=p;assets[name]=sha(encoded)
 row={'code':code,'sourceCompositionId':identifier,'level':'composition','name':item['displayName'],'sourceName':item['displayName'],'sourceDefinedMeaning':item['extentDefinition'],'exclusionsAndLimits':[item['remainingLimit']],'voxels':item['sourceVoxels'],'triangles':item['triangles'],'fineSourceCodes':item['sourceMemberCodes'],'fineSourceNames':item['sourceMemberNames'],'components26':item['components26'],'boundsSourceWorld':item['boundsSourceWorld'],**payloads}
 v['levels']['composition']['sourceClasses'].append(row)
v['levels']['composition']['totalTriangles']+=m['triangles'];v['presentClasses']+=2;v['totalTriangles']+=m['triangles']
restored=copy.deepcopy(v);restored['levels']['composition']['sourceClasses']=restored['levels']['composition']['sourceClasses'][:-2];restored['levels']['composition']['totalTriangles']-=m['triangles'];restored['presentClasses']-=2;restored['totalTriangles']-=m['triangles']
assert restored==original and (json.dumps(restored,indent=2)+'\n').encode()==base
raw=(json.dumps(v,indent=2)+'\n').encode();(O/'hierarchy.json').write_bytes(raw);(O/'before-hierarchy.json').write_bytes(base)
old_gzip=(R/'docs/holiatlas-schematic-review-20261026/before-hierarchy.json.gz').read_bytes();assert gzip.decompress(old_gzip)==base;(O/'before-hierarchy.json.gz').write_bytes(old_gzip)
proof={'allPassed':True,'beforeSHA256':sha(base),'afterSHA256':sha(raw),'beforeGzipSHA256':sha(old_gzip),'intakeSHA256':sha(intake),'previousEntriesPreserved':79,'addedEntries':2,'presentClasses':v['presentClasses'],'totalTriangles':v['totalTriangles'],'assets':assets,'sourceBoundaryEvidenceRechecked':True,'priorMetadataRestoredByteExactly':True,'runtimeBindingEstablished':False,'clinicalApproval':False,'wholeGoalComplete':False}
(O/'extension-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
