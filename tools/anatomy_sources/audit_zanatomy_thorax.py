#!/usr/bin/env python3
"""Reproduce source-coordinate diagnostics; topology is not clinical approval."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from pathlib import Path
import gzip,json,hashlib
import numpy as np
from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import topology
import argparse
parser=argparse.ArgumentParser(description='Audit preserved Z-Anatomy source geometry without repair or anatomical approval.');parser.add_argument('--review-root',type=Path,default=Path('docs/thoracic-zanatomy-candidate-review-20261013'));args=parser.parse_args();root=args.review_root;manifest=json.loads((root/'manifest.json').read_text());rows=[]
for record in manifest['records']:
 encoded=(root/record['file']).read_bytes();assert hashlib.sha256(encoded).hexdigest()==record['sha256'];raw=gzip.decompress(encoded);assert hashlib.sha256(raw).hexdigest()==record['decoded_sha256'];obj=json.loads(raw);mesh=obj['evaluated_viewport_mesh'];v=np.asarray(mesh['positions_local'],float);f=np.asarray(mesh['triangle_corner_indices'],int);matrix=np.asarray(obj['matrix_world'],float);assert np.isfinite(v).all() and np.isfinite(matrix).all();world=np.column_stack([v[:,0]*matrix[i,0]+v[:,1]*matrix[i,1]+v[:,2]*matrix[i,2]+matrix[i,3] for i in range(3)]);assert np.isfinite(world).all();assert np.allclose(matrix[3],[0,0,0,1],rtol=0,atol=1e-6)
 area=np.linalg.norm(np.cross(world[f[:,1]]-world[f[:,0]],world[f[:,2]]-world[f[:,0]]),axis=1)/2
 indexed=topology(world,f);points,remap=np.unique(world,axis=0,return_inverse=True);matched=topology(points,remap[f]);
 for metric in [indexed,matched]:
  for component in metric['components']:component['bounds_source_scene_units']=component.pop('bounds_original_mm')
 row={'name':obj['name'],'type':obj['type'],'source_file_sha256':record['sha256'],'evaluated_vertices':len(v),'evaluated_triangles':len(f),'world_bounds':[world.min(0).tolist(),world.max(0).tolist()],'world_extent':np.ptp(world,axis=0).tolist(),'world_surface_area':float(area.sum()),'zero_area_faces':int((area==0).sum()),'matrix_determinant':float(np.linalg.det(matrix[:3,:3])),'indexed_topology':indexed,'exact_position_topology':matched,'geometry_altered':False,'matching_used_only_for_diagnostics':True,'clinical_approval':False};rows.append(row);print(obj['name'],'components',len(matched['components']),'boundary',matched['boundary_edges'],'nonmanifold',matched['nonmanifold_edges'],'zero-area',row['zero_area_faces'],flush=True)
(root/'geometry-audit.json').write_text(json.dumps({'source_scene_sha256':manifest['source_scene_sha256'],'coordinate_units':'source scene metric units, scale_length1; independent acquisition calibration unverified','rows':rows,'clinical_approval':False,'source_geometry_repaired':False},indent=2)+'\n')
