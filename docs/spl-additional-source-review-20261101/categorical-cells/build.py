from pathlib import Path
import gzip,hashlib,json,sys
import numpy as np
R=Path.cwd();sys.path.insert(0,str(R))
from tools.anatomy_sources import spl_limbic_label_boundary as builder
from tools.anatomy_sources.spl_limbic_source import deterministic_gzip
D=R/'.research/spl-additional-cell-models-20261101';builder.RESEARCH=D
m=json.loads((R/'web/anatomy/spl-nac-limbic/manifest.json').read_bytes());row=m['labelVolume'];encoded=(R/'web/anatomy/spl-nac-limbic'/row['file']).read_bytes();sha=lambda raw:hashlib.sha256(raw).hexdigest();assert sha(encoded)==row['gzipSHA256'];raw=gzip.decompress(encoded);assert sha(raw)==row['decodedSHA256'];array=np.frombuffer(raw,dtype=row['dtype']).reshape(row['shape'],order='F');candidates=json.loads((R/'.research/spl-additional-source-candidates-20261101/candidates.json').read_bytes());labels=[{'code':r['code'],'name':r['publisherLUTName'],'sourceName':r['publisherLUTName']}for r in candidates['rows']if r['publisherLUTName']];assert len(labels)==94
source={'repository':'mhalle/spl-brain-atlas','commit':'bec24db25aad5f7600e2df3becfb1f883e61ff56','labelFile':'slicer/volumes/labels/hncma-atlas.nrrd','decodedLabelSHA256':row['decodedSHA256']}
def write(name,raw):
 packed=deterministic_gzip(raw);(D/'package'/name).write_bytes(packed);assert gzip.decompress(packed)==raw;return {'file':name,'byteLength':len(raw),'gzipBytes':len(packed),'gzipSHA256':sha(packed),'decodedSHA256':sha(raw)}
meshes=builder.prepare_label_boundaries(array,np.asarray(row['voxelToRAS']),labels,source,write)
result={'sourceClasses':len(meshes),'allSourceClassesRetained':True,'allSourceFacesAndComponentsPreserved':True,'sourceMRIOrLabelsChanged':False,'sourcePayloadsAreExactCategoricalCellsNotValidatedBiologicalBoundaries':True,'clinicalApproval':False,'anatomicalApproval':False,'meshes':meshes,'builderSHA256':sha(Path('tools/anatomy_sources/spl_limbic_label_boundary.py').read_bytes())};(D/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print({'sourceClasses':len(meshes),'vertices':sum(r['vertexCount']for r in meshes),'triangles':sum(r['triangleCount']for r in meshes),'clinicalApproval':False},flush=True)
