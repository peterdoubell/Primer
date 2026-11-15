#!/usr/bin/env python3
"""Inspect independent delivered CT/labels and unchanged SPL wall triangle strips."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import zipfile

ARCHIVE_SHA='1cf85dbc820767b7c3095790ff38ae150a085af713061a2f0e950e355e4dc7c8'
TARGETS={135:'right_external_oblique_muscle',136:'right_internal_oblique_muscle',
         235:'left_external_oblique_muscle',236:'left_internal_oblique_muscle',32:'rectus_abdominis_muscle'}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def nrrd(raw):
    import numpy as np
    header,packed=raw.split(b'\n\n',1)
    fields={line.split(': ',1)[0]:line.split(': ',1)[1] for line in header.decode().splitlines() if ': ' in line and not line.startswith('#')}
    if any(fields[k]!=v for k,v in {'type':'short','dimension':'3','space':'left-posterior-superior','endian':'little','encoding':'gzip'}.items()):raise ValueError('Unreviewed delivered grid format')
    dims=list(map(int,fields['sizes'].split()));values=np.frombuffer(gzip.decompress(packed),'<i2')
    if len(values)!=dims[0]*dims[1]*dims[2]:raise ValueError('Delivered voxel count differs')
    return fields,values.reshape(dims[::-1])


def vtk(raw):
    import numpy as np
    if not raw.startswith(b'# vtk DataFile Version 4.0\nvtk output\nBINARY\nDATASET POLYDATA\n'):raise ValueError('Unreviewed original VTK form')
    match=re.search(rb'POINTS (\d+) float\n',raw);count=int(match[1]);start=match.end()
    points=np.frombuffer(raw,'>f4',count*3,start).reshape(-1,3);position_bytes=raw[start:start+count*12];offset=start+count*12
    match=re.match(rb'\nTRIANGLE_STRIPS (\d+) (\d+)\n',raw[offset:])
    if match is None:raise ValueError('Unreviewed native cell type')
    cells,entries=map(int,match.groups());start=offset+match.end();encoded=np.frombuffer(raw,'>i4',entries,start);connectivity_bytes=raw[start:start+entries*4]
    strips=[];cursor=0;triangles=[]
    for _ in range(cells):
        n=int(encoded[cursor]);s=encoded[cursor+1:cursor+1+n];cursor+=n+1
        if n<3 or s.min()<0 or s.max()>=count:raise ValueError('Invalid original strip')
        strips.append(s.tolist())
        for i in range(n-2):triangles.append([int(s[i]),int(s[i+1]),int(s[i+2])] if i%2==0 else [int(s[i+1]),int(s[i]),int(s[i+2])])
    if cursor!=entries:raise ValueError('Original strip accounting differs')
    offset=start+entries*4;match=re.match(rb'\nPOINT_DATA (\d+)\nNORMALS Normals float\n',raw[offset:])
    if match is None or int(match[1])!=count:raise ValueError('Original normal domain differs')
    start=offset+match.end();normals=np.frombuffer(raw,'>f4',count*3,start).reshape(-1,3)
    if raw[start+count*12:].strip():raise ValueError('Unreviewed remaining VTK attributes')
    if not np.isfinite(points).all() or not np.isfinite(normals).all():raise ValueError('Nonfinite source arrays')
    return points,normals,np.asarray(triangles,dtype=np.int64),strips,position_bytes,connectivity_bytes,raw[start:start+count*12]


def review(archive,output):
    import numpy as np
    from tools.anatomy_sources.review_bodyparts_pancreatic_geometry import topology
    raw=archive.read_bytes()
    if sha(raw)!=ARCHIVE_SHA or len(raw)!=34861066:raise ValueError('Independent original archive differs')
    output.mkdir(parents=True,exist_ok=True);rows=[]
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:raise ValueError('Original archive CRC differs')
        prefix='abdomen-2016-09/';structure_raw=z.read(prefix+'atlasStructure.json');structures=json.loads(structure_raw)
        ct_raw=z.read(prefix+'Data/I.nrrd');seg_raw=z.read(prefix+'Data/seg.nrrd');ct_fields,ct=nrrd(ct_raw);seg_fields,seg=nrrd(seg_raw)
        if ct_fields!=seg_fields:raise ValueError('Native CT and label grids differ')
        origin=np.asarray([float(v) for v in ct_fields['space origin'].strip('()').split(',')])
        directions=np.asarray([[float(v) for v in m.split(',')] for m in re.findall(r'\(([^)]+)\)',ct_fields['space directions'])]).T
        for label,name in TARGETS.items():
            file='Data/Model_'+str(label)+'_'+name+'.vtk';model_raw=z.read(prefix+file)
            points,normals,triangles,strips,pbytes,cbytes,nbytes=vtk(model_raw)
            selected=[r for r in structures if r.get('@type')=='Structure' and r.get('annotation',{}).get('name')==name.replace('_',' ')]
            if len(selected)!=1:raise ValueError('Original anatomical label is ambiguous')
            selectors=selected[0]['sourceSelector'];lm=next(s for s in selectors if 'LabelMapSelector' in s['@type']);gm=next(s for s in selectors if 'GeometrySelector' in s['@type'])
            source=next(r for r in structures if r.get('@id')==gm['dataSource'])
            if lm['dataKey']!=label or not lm['authoritative'] or gm['authoritative'] or source['source']!=file:raise ValueError('Original label/model authority mapping differs')
            coordinates=np.argwhere(seg==label)
            if not len(coordinates):raise ValueError('Expected source label has no voxels')
            # Source model RAS to original NRRD LPS basis only; no fitting or resampling.
            lps=points.astype(float)*[-1,-1,1];ijk=np.linalg.solve(directions,(lps-origin).T).T
            grid_dims=np.asarray(list(map(int,ct_fields['sizes'].split())))
            unique,inverse=np.unique(points,axis=0,return_inverse=True)
            areas=np.linalg.norm(np.cross(points[triangles[:,1]]-points[triangles[:,0]],points[triangles[:,2]]-points[triangles[:,0]]),axis=1)/2
            rows.append({'label_value':label,'source_name':selected[0]['annotation']['name'],'source_member':prefix+file,'source_vtk_sha256':sha(model_raw),
                'position_records':len(points),'normal_records':len(normals),'native_triangle_strips':len(strips),'strip_lengths':{str(n):sum(len(s)==n for s in strips) for n in sorted({len(s) for s in strips})},
                'analysis_triangles':len(triangles),'positions_big_endian_float32_sha256':sha(pbytes),'connectivity_big_endian_int32_sha256':sha(cbytes),'normals_big_endian_float32_sha256':sha(nbytes),
                'source_bounds_ras':np.stack([points.min(0),points.max(0)]).tolist(),'source_label_voxels':len(coordinates),
                'label_voxel_bounds_ijk':np.stack([coordinates[:,::-1].min(0),coordinates[:,::-1].max(0)]).tolist(),
                'model_vertices_outside_delivered_grid':int(np.any((ijk<-.5)|(ijk>grid_dims-.5),axis=1).sum()),
                'zero_area_analysis_triangles':int((areas==0).sum()),'indexed_triangle_topology':topology(points,triangles),
                'exact_duplicate_position_records':len(points)-len(unique),'exact_position_analysis_topology':topology(unique,inverse[triangles]),'analysis_welding_changes_source':False,
                'source_label_selector':lm,'source_geometry_selector':gm,'source_positions_indices_normals_changed':False,
                'source_derived_model_is_authoritative_label':False,'independent_anatomical_accuracy_verified':False,'clinical_approval':False})
        missing={q:[r['annotation']['name'] for r in structures if r.get('@type')=='Structure' and q in r.get('annotation',{}).get('name','').lower()]
                 for q in ['transversus','rectus sheath','scarpa','camper','semilunar']}
        result={'archive_url':'https://www.openanatomy.org/atlases/nac/abdomen-2016-09.zip','archive_sha256':sha(raw),'archive_bytes':len(raw),'archive_crc_verified':True,
            'source_atlas_url':'https://www.openanatomy.org/atlas-pages/atlas-spl-abdomen.html','source_structure_sha256':sha(structure_raw),
            'ct_member_sha256':sha(ct_raw),'label_member_sha256':sha(seg_raw),'ct_grid':ct_fields,'label_grid':seg_fields,
            'all_delivered_voxels_inspected':True,'delivered_voxel_count':int(ct.size),'ct_original_voxel_bytes_sha256':sha(ct.astype('<i2').tobytes()),
            'label_original_voxel_bytes_sha256':sha(seg.astype('<i2').tobytes()),'ct_value_range':[int(ct.min()),int(ct.max())],
            'highest_resolution_acquired_ct_verified':False,'ct_hu_calibration_or_phase_verified':False,'patient_metadata_verified':False,
            'records':rows,'combined_rectus_label_split_into_patient_sides':False,'bounded_missing_structure_queries':missing,
            'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False,
            'limits':['Original delivered 256×256×113 CT and labels share their native grid. This does not prove acquired master resolution, phase, HU calibration or complete wall coverage.',
                'Original VTK triangle strips and arrays are unchanged. Alternating strip expansion is analysis only; models are explicitly non-authoritative derived surfaces in source metadata.',
                'Combined rectus label is not split by guessed midline. Missing transversus/sheath/fascial labels cannot be inferred from other named muscles.',
                'Source basis conversion is numerical RAS/LPS correspondence, not independent clinical registration or anatomy approval. Source license research-only/clinical-use qualifications remain separate.']}
        (output/'independent-wall-source-review.json').write_text(json.dumps(result,indent=2)+'\n')
        (output/'original-selected-structure-rows.json').write_text(json.dumps([r for r in structures if r.get('@id') in {s['dataSource'] for i in rows for s in [i['source_label_selector'],i['source_geometry_selector']]} or (r.get('@type')=='Structure' and r.get('annotation',{}).get('name') in [i['source_name'] for i in rows])],indent=2)+'\n')
        (output/'original-atlas-license.md').write_bytes(z.read(prefix+'LICENSE.md'))
    print('Inspected five independent wall models and both full delivered voxel grids.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();review(a.archive,a.output)
