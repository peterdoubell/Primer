#!/usr/bin/env python3
"""Confirm every retained facet and normal matches the original source exactly."""
import hashlib,json,pathlib
import numpy as np
from stage_malaya_knee import stl,OUT
from check_staged_meshes import read

manifest=json.loads((OUT/'manifest.json').read_text());records=[]
for p in manifest['parts'].values():
 source=pathlib.Path(p['stl_file']).read_bytes();assert hashlib.sha256(source).hexdigest()==p['source_sha256']
 tri,n,nt=stl(source);assert nt==p['source_triangles']
 omitted=p['omitted_source_facet_indices'];keep=np.ones(nt,dtype=bool);keep[omitted]=False
 for i in omitted:
  q=tri[i].astype('f8');assert np.all(np.cross(q[1]-q[0],q[2]-q[0])==0)
  assert np.array_equal(q[0],q[1]) or np.array_equal(q[1],q[2]) or np.array_equal(q[0],q[2])
 raw,positions,normals,ix=read(p['file']);assert hashlib.sha256(raw).hexdigest()==p['sha256']
 assert len(ix)==p['triangles'] and len(positions)==p['export_vertices']
 assert np.array_equal(positions[ix],tri[keep])
 assert np.array_equal(normals[ix],np.repeat(n[keep][:,None,:],3,axis=1))
 assert np.isfinite(positions).all() and np.isfinite(normals).all()
 assert np.array_equal(positions[ix].min(axis=(0,1)),np.array(p['bounds'][0],dtype='f4'))
 assert np.array_equal(positions[ix].max(axis=(0,1)),np.array(p['bounds'][1],dtype='f4'))
 records.append({'id':p['id'],'source_triangles':nt,'render_triangles':len(ix),'omitted_exact_empty_facets':len(omitted),'retained_positions_exact':True,'retained_normals_exact':True,'valid_bounds':True})
assert sum(r['omitted_exact_empty_facets'] for r in records)==48
result={'objects':len(records),'source_triangles':sum(r['source_triangles'] for r in records),'render_triangles':sum(r['render_triangles'] for r in records),'omitted_exact_empty_facets':48,'all_retained_facets_exact':True,'records':records}
(OUT/'geometry-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'}))
