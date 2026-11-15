#!/usr/bin/env python3
"""Assess every unresolved cross-surface contact without changing geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def barycentric(point,triangle):
    coordinates=np.linalg.lstsq(np.column_stack([triangle[1]-triangle[0],triangle[2]-triangle[0]]),point-triangle[0],rcond=None)[0]
    return np.array([1-coordinates.sum(),coordinates[0],coordinates[1]])


def assess(root,contacts_path,output):
    manifest=json.loads((root/'surface-review.json').read_text());meshes={}
    for row in manifest['records']:
        path=root/row['mesh_file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=row['mesh_sha256']:raise ValueError('Source mesh changed')
        with np.load(path) as data:meshes[row['code']+'-'+row['side']]=(data['vertices'].copy(),data['faces'].copy())
    contacts=json.loads(contacts_path.read_text());records=[];interior_crossings=[]
    for row in contacts['records']:
        if not row['unexpected_contact_count']:continue
        va,fa=meshes[row['first']];vb,fb=meshes[row['second']]
        opposite=point=segment=interior=0
        for contact in row['unexpected_contacts']:
            first=va[fa[contact['first_face']]];second=vb[fb[contact['second_face']]]
            n1=np.cross(first[1]-first[0],first[2]-first[0]);n2=np.cross(second[1]-second[0],second[2]-second[0])
            n1/=np.linalg.norm(n1);n2/=np.linalg.norm(n2)
            parallel=float(np.linalg.norm(np.cross(n1,n2)))
            distance=float(np.max(np.abs((second-first[0])@n1)))
            if parallel<=1e-12:
                if distance<=1e-9 and n1@n2<0:opposite+=1
                continue
            points=np.array(contact['contact_points_mm']);length=float(np.linalg.norm(points[-1]-points[0]))
            if length<=1e-9:point+=1;continue
            segment+=1
            midpoint=points.mean(0);b1=barycentric(midpoint,first);b2=barycentric(midpoint,second)
            if min(b1.min(),b2.min())>1e-9:
                interior+=1
                interior_crossings.append({'first':row['first'],'second':row['second'],
                                           'first_face':contact['first_face'],'second_face':contact['second_face'],
                                           'contact_points_mm':contact['contact_points_mm'],'line_length_mm':length,
                                           'midpoint_barycentric_first':b1.tolist(),'midpoint_barycentric_second':b2.tolist()})
        records.append({'first':row['first'],'second':row['second'],'initially_unresolved_contacts':row['unexpected_contact_count'],
                        'oppositely_oriented_coplanar_contacts':opposite,'noncoplanar_point_contacts':point,
                        'noncoplanar_line_contacts':segment,'line_midpoint_in_both_triangle_interiors':interior})
    result={'mesh_manifest_sha256':hashlib.sha256((root/'surface-review.json').read_bytes()).hexdigest(),
            'contact_audit_sha256':hashlib.sha256(contacts_path.read_bytes()).hexdigest(),
            'records':records,'interior_crossings':interior_crossings,
            'assembly_status':'held_cross_structure_surface_crossings' if interior_crossings else 'requires_further_interface_review',
            'source_geometry_changed':False,'clinical_approval':False,
            'limits':'Numerical plane/contact dimension and barycentric midpoint assessment, not a volumetric overlap estimate or clinical interface approval. Opposite coplanar contacts and non-interior contacts remain review evidence, not silently removed.'}
    output.write_text(json.dumps(result,indent=2)+'\n')
    print('Interior crossings:',len(interior_crossings))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--meshes',type=Path,required=True);parser.add_argument('--contacts',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assess(args.meshes,args.contacts,args.output)
