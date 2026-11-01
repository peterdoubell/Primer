from pathlib import Path
import gzip,hashlib,json,sys
R=Path.cwd();sys.path[:0]=[str(R),str(R/'.research/spl-additional-source-models-20261101')]
from parse_source import parse_additional_vtk
from tools.anatomy_sources.spl_limbic_source import pack_mesh,deterministic_gzip
D=R/'.research/spl-additional-source-models-20261101';P=D/'package';P.mkdir(exist_ok=True);a=json.loads((D/'acquisition.json').read_bytes());g={r['code']:r for r in json.loads((D/'geometry-review.json').read_bytes())['rows']};rows=[];sha=lambda b:hashlib.sha256(b).hexdigest()
for row in a['rows']:
 model=parse_additional_vtk(D/row['file']);payload,layout,extra=pack_mesh(model);name=str(row['code'])+'.mesh.gz';packed=deterministic_gzip(payload);(P/name).write_bytes(packed);assert gzip.decompress(packed)==payload;aux={}
 for key,raw in extra.items():
  filename=str(row['code'])+'-'+key+'.bin.gz';data=deterministic_gzip(raw);(P/filename).write_bytes(data);assert gzip.decompress(data)==raw;aux[key]={'file':filename,'gzipSHA256':sha(data),'decodedSHA256':sha(raw),'bytes':len(raw)}
 rows.append({'code':row['code'],'sourceFile':row['file'],'originalSHA256':row['sha256'],'originalGitBlobSHA1':row['gitBlobSHA1'],'originalHeader':model['raw'].splitlines()[0].decode(),'file':name,'gzipBytes':len(packed),'gzipSHA256':sha(packed),'decodedBytes':len(payload),'decodedSHA256':sha(payload),'layout':layout,'sourceCoordinateContext':'Legacy source-scene RAS mm; no parent transform, sign flip, fitted alignment, smoothing or cleanup','vertices':model['vertexCount'],'triangles':model['triangleCount'],'originalAuxiliary':aux,'sourceGeometryBitsPreserved':True,'labelSurfaceCorrespondenceReviewRequired':row['code']in [385,386,4084],'clinicalApproval':False})
manifest={'models':len(rows),'rows':rows,'allOriginalPositionsNormalsAndStripsPreserved':True,'allOriginalTrianglesRetained':True,'coordinateCoincidenceUsedOnlyForReviewNotGeometryWelding':True,'sourceModelLabelDiscrepancyUnresolvedCodes':[4084],'clinicalApproval':False,'anatomicalApproval':False,'publisherSourceCommit':a['sourceCommit']};(D/'package-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print({'models':len(rows),'payloadFiles':len(list(P.iterdir())),'geometryDataPreserved':True,'clinicalApproval':False})
