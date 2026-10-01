#!/usr/bin/env python3
"""Package checked source references for the reader without clinical approval."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
import numpy as np


def package(source,output,report):
    output.mkdir(parents=True,exist_ok=True)
    original=json.loads((source/'surface-review.json').read_text());parts={};rows=[]
    names={'gpi':'Globus pallidus internal segment','gpe':'Globus pallidus external segment','put':'Putamen'}
    colors={'gpi':'#a638bf','gpe':'#1c947b','put':'#cc7b23'}
    for entry in original['records']:
        path=source/entry['mesh_file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['mesh_sha256']:raise ValueError('Checked model changed')
        with np.load(path) as mesh:positions=mesh['vertices'].copy();faces=np.asarray(mesh['faces'],dtype='<u4')
        stored=np.asarray(positions,dtype='<f4');error=float(np.max(np.abs(stored.astype(float)-positions)))
        if error>2e-6:raise ValueError('Unexpected coordinate conversion error')
        normals=np.zeros_like(positions);tri=positions[faces];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        for corner in range(3):np.add.at(normals,faces[:,corner],cross)
        lengths=np.linalg.norm(normals,axis=1)
        if np.any(lengths<=0):raise ValueError('Undefined display normals')
        normals=np.asarray(normals/lengths[:,None],dtype='<f4')
        decoded=struct.pack('<4sII',b'BP3D',len(stored),faces.size)+stored.tobytes()+normals.tobytes()+faces.tobytes()
        ident='massp2-'+entry['code']+'-'+entry['side'];name=ident+'.bin.gz';encoded=gzip.compress(decoded,mtime=0);(output/name).write_bytes(encoded)
        n=len(stored);restored=gzip.decompress(encoded)
        restored_positions=np.frombuffer(restored,'<f4',n*3,12).reshape(-1,3)
        restored_faces=np.frombuffer(restored,'<u4',faces.size,12+n*24).reshape(-1,3)
        if not np.array_equal(restored_positions,stored) or not np.array_equal(restored_faces,faces):raise ValueError('Mesh transport changed')
        parts[ident]={'id':ident,'name':('Left' if entry['side']=='l' else 'Right')+' '+names[entry['code']],
                      'file':'/app/anatomy/massp2-subcortex/'+name,'sha256':hashlib.sha256(encoded).hexdigest(),
                      'decoded_sha256':hashlib.sha256(decoded).hexdigest(),'vertices':n,'triangles':len(faces),
                      'bounds':[stored.min(0).tolist(),stored.max(0).tolist()],'source_label':entry['label_id'],
                      'source_surface_sha256':entry['mesh_sha256'],'clinical_fidelity':'unverified','color':colors[entry['code']],
                      'layer':'subcortex','regions':['brain-subcortex']}
        rows.append({'id':ident,'maximum_position_conversion_error_mm':error,'faces_unchanged':True,'vertices':n,'triangles':len(faces),'mesh_sha256':parts[ident]['sha256']})
    low=np.min([p['bounds'][0] for p in parts.values()],axis=0);high=np.max([p['bounds'][1] for p in parts.values()],axis=0)
    notes=['Six source-labelled structures only: bilateral putamen and internal/external pallidal segments. Caudate, thalamus, capsule limbs, gyri, vessels and other brain structures are not supplied by this reference.',
           'Adult population atlas: 97 subjects, ages 18–80. The MRI comparison uses separate 105-subject group templates. These are not individual clinical examinations.',
           'Shared interfaces are derived by tetrahedral interpolation of unchanged source labels. Sampling is 0.5 mm; interpolation does not add measured resolution or establish clinical boundary accuracy.',
           'Original MNI2009b RAS coordinates. This reference is independent of BodyParts3D; their coordinates must not be combined. Fine medullary lamina anatomy, pathological states and clinical accuracy remain unverified.',
           'Attribution: Bazin, Forstmann, Alkemade and Miletic. MASSP 2.0 lifespan atlas v2, CC BY 4.0. Adaptation: joint interfaces, float32 transport and lighting normals; no source voxel labels changed.']
    manifest={'dataset':'MASSP 2.0 · partial adult subcortical reference','source_url':'https://doi.org/10.21942/uva.27291579.v2',
              'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
              'coordinate_system':{'basis':'RAS','units':'millimetres','unit_meters':.001,'display_basis':'native-ras-to-x-left-y-superior-z-anterior','registration':'Original MNI2009b atlas affine; no BodyParts3D registration'},
              'parts':parts,'regions':{'brain-subcortex':{'title':'Putamen and pallidal segments · source atlas','side':'bilateral','parts':[{'id':key,'layer':'subcortex'} for key in parts],
              'layers':[['subcortex','Source subcortical structures']],'source_up_range':[float(low[2]-1),float(high[2]+1)],'focus_bounds':[low.tolist(),high.tolist()]}},
              'viewer_notes':notes,'clinical_approval':False,'runtime_promoted':True,'total_triangles':sum(p['triangles'] for p in parts.values()),
              'status':'Partial source reference; clinical anatomical validation pending','source_manifest_sha256':hashlib.sha256((source/'surface-review.json').read_bytes()).hexdigest()}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (output/'ATTRIBUTION.md').write_text('# MASSP 2.0 source reference\n\nBazin, Forstmann, Alkemade and Miletic. [MASSP 2.0 lifespan atlas v2](https://doi.org/10.21942/uva.27291579.v2), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).\n\nChanges: joint tetrahedral interfaces from unchanged label voxels, float32 position storage, generated lighting normals and gzip transport. Models remain anatomically unapproved; no independent registration to BodyParts3D. Full acquisition, geometric validation and interpolation limits are in docs/brain-massp-source-review.md.\n')
    report.write_text(json.dumps({'parts':rows,'clinical_approval':False,'source_labels_changed':False,'manifest_sha256':hashlib.sha256((output/'manifest.json').read_bytes()).hexdigest()},indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();package(args.source,args.output,args.report)
